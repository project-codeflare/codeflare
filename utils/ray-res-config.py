import sys
import os
from typing import Dict
import yaml
import wget
import re
# import regex
from parse import *
from optparse import OptionParser

versions_list=['1.0.0', '1.1.0','1.2.0','1.3.0','1.4.0','1.4.1','1.5.0', '1.6.0', '1.7.0', '1.8.0']

res_modes_list=['relaxed', 'recommended', 'strict', 'custom']

Ray_conf= dict()

FAIL = "91"
STATUS = "33"
WARNING = "93"
OK = "92"
INFO = "94"

##
# Print the string given in parameter with color
#
def print_colored(color, text):
    if color == "FAIL":
        color = FAIL
    elif color == "OK":
        color = OK
    elif color == "WARNING":
        color = WARNING
    elif color == "STATUS":
        color = STATUS
    elif color == "INFO":
        color = INFO
    print("\033[1;" + color + ";40m" + text + "\033[0m")

# print supported ray versions and resiliency modes/profiles
def print_ray_versions_and_modes():
    print("Compatible Ray versions:")
    print(', '.join(versions_list))

    print('''
Available resiliency profiles/modes:
1. strict:      Resilience preferred
2. relaxed:     Performance preferred
3. recommended: Balanced resilience and performance overhead
4. custom:      Define your own preference
    ''')

# Generates .conf files in configs/RAY_VERSION folder in the working directory
def dump_conf(ray_version, res_mode, overwrite, dirname='configs'):
    # dump the default configs in a file to let others edit further
    file_path =  dirname+"/ray-"+ray_version+"-"+res_mode+".conf"
    # check if the file already exist
    if (not os.path.exists(file_path)) or overwrite:
        fd = open(file_path, "w+")
        fd.write("# please edit value_for_this_mode to change any configuration\n")
        yaml.dump(Ray_conf[ray_version],  fd, width=float('inf'))

# Que: is dumping in json format better or YAML?
def read_conf(ray_version, res_mode, dirname='configs/'):
    Ray_conf_new = Ray_conf
    file_path =  dirname+"ray-"+ray_version+"-"+res_mode+".conf"
    fd = open(file_path, 'r')
    fd.readline()
    try:
        Ray_conf_new[ray_version] = yaml.safe_load(fd)
        conf_list = list()
        for conf_name in Ray_conf_new[ray_version].items():
            # print(conf_name[1]['default'], conf_name[1]['value_for_this_mode'])
            if conf_name[1]['default'] != conf_name[1]['value_for_this_mode']:
                cv_dict = {}
                cv_dict[conf_name[0]] = conf_name[1]['value_for_this_mode']
                conf_list.append((conf_name[0],conf_name[1]['value_for_this_mode']))
        # print(conf_list)
        if len(conf_list) == 0:
            print_colored(INFO, 'No change in default configurations!')
        return conf_list
    except yaml.YAMLError as exception:
        print(exception)


def put_conf(ray_version, conf_name, conf_type, conf_default, conf_env, conf_str):
    # Ray_conf[version][conf_name][type/default/env]
    Ray_conf[ray_version][conf_name] = dict()
    Ray_conf[ray_version][conf_name]['type'] = conf_type
    Ray_conf[ray_version][conf_name]['default'] = conf_default
    Ray_conf[ray_version][conf_name]['value_for_this_mode'] = conf_default
    Ray_conf[ray_version][conf_name]['env'] = conf_env
    Ray_conf[ray_version][conf_name]['config_string'] = conf_str

# parse env. variable from config string
def get_env(conf_default):
    conf_env = ""
    if 'getenv' in conf_default:
        _,conf_env,_ = parse('{}etenv("{}"){}', conf_default)
    return conf_env

# get the default value of the configuration
def get_default(conf_default, conf_type):
    if 'env_' in conf_default:
        _, conf_default = parse('{}, {})', conf_default)
    elif '?' in conf_default:
        if_str, true_str, false_str = parse('{} ? {} : {})', conf_default)
        if '!=' in if_str:
            conf_default = false_str
        else:
            conf_default = true_str
    elif 'std::string' in conf_default:
        is_eq, conf_default = parse('{} std::string("{}"))', conf_default)
        # if the condition is != (not equal) then Ray expect the opposite value
        if is_eq[-2:] == "!=":
            if conf_type == "bool":
                conf_default = str(not int(conf_default))
    else:
        print ("Unable to parse string %s" % conf_default)
        sys.exit(-1)

    return conf_default

def parse_ray_config(ray_version, sig_str, is_multiline):
    # print("In parse_ray_config: %s" % sig_str)
    conf_type, conf_name, conf_default = parse("RAY_CONFIG({}, {}, {}", sig_str)

    # replace if default has comment in it
    conf_default = re.sub('(?:/\*(.*?)\*/)', '', conf_default)
    conf_str = ''
    if  is_multiline:
        conf_str = conf_default[:-1]
        conf_env = get_env(conf_default)
        conf_default = get_default(conf_default, conf_type)
    conf_default = conf_default.rstrip(')')
    # print(conf_type, conf_name, conf_default, conf_env)
    # Access values like this: Ray_conf[ray_version][conf_name][type/default/env]
    put_conf(ray_version, conf_name, conf_type, conf_default, conf_env, conf_str)

# for multi-line signatures
def is_balanced_parenthesis(str_list):
    open_para = 0
    close_para = 0
    for line in str_list:
        open_para = open_para + line.count('(')
        close_para = close_para + line.count(')')

    if open_para == close_para:
        return True
    return False

def parse_config_file(config_file, ray_version):
    # initialize conf dict
    Ray_conf[ray_version] = dict()
    print("\nParsing configuration file: %s" % config_file)
    f = open(config_file, 'r')
    '''
    One other way to parse these header files is to write a small C/C++ program
    that define the macro before including the header file and dump into a file
    like following:
    #define RAY_CONFIG(type, name, default_value) \
        std::cout << #type << endl; \
        std::cout << #name << endl; \
        std::cout << #default_value << endl; \
        std::cout << "=====" << endl;
    '''

    # Below is the regex for a single line config signature;
    # Fix it to include multi-line function declarations as well.
    # then we'll not need the whole while loop
    # re.findall(r'^RAY_CONFIG\((.*)\)$',f.read(), flags=re.MULTILINE)

    lines = f.readlines()
    n = len(lines)
    i = 0
    while (i < n):
        line  = lines[i]
        line = line.strip(' ').rstrip('\n')
        # print("Parsing line: %s" % line)
        # FIXME: write a regex that can parse both single and multi-line signature
        if line.startswith("RAY_CONFIG"):
            if line.endswith(','):
                # print("Multi-line signature")
                # normally multi-line signature includes relevant environment
                # variable that we can save if we want to exploit in the future.

                # read till function signature is closed
                j = i + 1
                while (is_balanced_parenthesis(lines[i:j]) is not True):
                    # print (lines[j])
                    j = j + 1
                multiline_fun = ' '.join(map(str.strip,lines[i:j+1]))
                parse_ray_config(ray_version, multiline_fun.rstrip('\n').rstrip(' '), True)
                i = j + 1
                continue
            elif line.endswith(')'):
                parse_ray_config(ray_version, line, False)
            elif line.endswith(');'):
                # this one case is because of ray developer didn't follow the
                # MACRO calling prototype like the rest config calls in Ray 1.5.0
                # RAY_CONFIG(uint32_t, agent_manager_retry_interval_ms, 1000);
                # TODO: generalize it by right striping the line of any ";"
                parse_ray_config(ray_version, line[:-1], False)
            else:
                print("neither ends with , nor with ) ")
                print(line)
                sys.exit()
        i = i + 1

# total config count
def total_config(ray_version):
    print('Total configs in Ray version %s = %d' %(ray_version, len(Ray_conf[ray_version])))

# fetch and parse ray configuration for each resiliency mode/profile
def fetch_configs_from_git(ray_versions, res_modes, overwrite):
    # get configs from file or git for each ray_version
    for ray_version in ray_versions:
        out_dir = "configs/"+ray_version
        # create dir if not present
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        out_filename = "%s/ray-%s-config-def.h" % (out_dir, ray_version)
        # wget it from git if file not present
        if not os.path.exists(out_filename):
            url = 'https://raw.githubusercontent.com/ray-project/ray/ray-%s/src/ray/common/ray_config_def.h' % ray_version
            wget.download(url, out=out_filename)
        parse_config_file(out_filename, ray_version)
        total_config(ray_version)
        for res_mode in res_modes:
            dump_conf(ray_version, res_mode, overwrite, out_dir)
    print_colored(OK, "All conf files saved!\nDONE!")

# generate config json string for system-cm yaml
def get_conf_string(conf_list):
    # join string and escape special chars in the string
    # NOTES: use re.escape and string.translate to escape if needed
    # TODO: check if the format works for all ray versions and ways of cluster deployment
    conf_str = ','.join(['"%s":"%s"' % (x[0],x[1]) for x in conf_list])
    # conf_str = ', '.join(['\\"%s\\":\\"%s\\"' % (x[0],x[1]) for x in conf_list])
    print('New configurations: %s' % conf_str)
    return conf_str


def gen_system_conf(conf_list, verbose):
    if verbose:
        print("Version 1.4.0 specific configs")
    conf_string = get_conf_string(conf_list)
    # FIXME: this should not be hardcoded and can be made a dict in python to be
    # loaded as yaml instead of a string
    sys_conf = """
    apiVersion: v1
    data:
        system_config: '{%s}'
    kind: ConfigMap
    metadata:
        name: system-config-json
    """ % (conf_string)
    return yaml.load(sys_conf, yaml.Loader)

# print next steps on how to use generated system-cm.yaml
# TODO: generalize next steps for different deploy stratagies
def print_next_steps():
    print('------------')
    print_colored(INFO, 'NEXT STEPS:')
    print('''
1. Apply system-cm.yaml to your namespace. For openshift:
`oc apply -f system-cm.yaml`

2. Add SYSTEM_CONFIG enviornment variable to Ray's head node container that maps
   to system config map's name in your cluster yaml (See an example below):
    ...
    containers:
      env:
        - name: SYSTEM_CONFIG
          valueFrom:
          configMapKeyRef:
            name: system-config-json
            key: system_config
        ...
    ...

3. Specify SYSTEM_CONFIG env. var to head node's `ray start` command as following:
    ray start --head --system-config='$(SYSTEM_CONFIG)' ...

4. Deploy Ray cluster
''')

#
# TODO:
# 1. finalize the configurations for each mode
# 2. pass verbose to all functions to have all prints included in verbose
#
def generate_system_config_map(ray_version, res_mode, path, verbose):
    ## version specific configurations
    Ray_configs= read_conf(ray_version, res_mode)
    sys_config_yaml = gen_system_conf(Ray_configs, verbose)
    fd = open(path + '/system_cm.yaml', 'w+')
    yaml.dump(sys_config_yaml, fd, allow_unicode=True)
    print_colored(OK, "File saved! DONE!")
    print_next_steps()


# Tool options
def main(argv):
    parser = OptionParser(usage="ray-res-config.py --ray-version <arg> --resiliency-mode <arg>")
    parser.add_option("-r","--ray-version", action="store", type="string",
                      default="1.4.0", dest="ray_version",
                      help="Ray version for the deployment (required). \
                            e.g. 1.4.0 (default), 1.4.1")
    parser.add_option("-m","--resiliency-mode", action="store", type="string",
                      default="recommended", dest="res_mode",
                      help="Fault-tolerance model for the deployment (required).\
                          e.g. strict, recommended (default), relaxed")
    parser.add_option("-p","--path", action="store", type="string",
                      default=".", dest="path",
                      help="Path to save final system config map yaml.\
                           Otherwise, saves in $PWD (default)")
    parser.add_option("-n","--name", action="store", type="string",
                      default="system-config-json", dest="name",
                      help="Name of the system config map.\
                           default=system-config-json")

    parser.add_option("-f","--fetch-all", action="store_true", dest='fetch_all',
                      help="Fetch configs for all from git. \
                        Use -o to overwrite existing .conf files")
    parser.add_option("-o","--overwrite", action="store_true", dest="overwrite",
                      help="Use with -f or --fetch-all to overwrite existing .conf files")
    parser.add_option("-l","--list", action="store_true", dest='lists',
                      help="List compatible versions and resiliency modes")
    parser.add_option("--verbose", action="store_true",
                      help="Enable verbose execution mode")
    parser.add_option("--version", action="store_true",
                      help="Print version of the FT model")
    (opts, args) = parser.parse_args()

    # Que.: do we need this?
    if opts.version:
        print("CodeFlare Resiliency Tool v1.0")
        sys.exit(0)

    # fetch and parse all supported ray versions
    if opts.fetch_all:
        fetch_configs_from_git(versions_list, res_modes_list, opts.overwrite)
        sys.exit(0)

    # print list of supported ray versions and resiliency profiles
    if opts.lists:
        print_ray_versions_and_modes()
        sys.exit(0)

    # validate ray version; print list of supported versions if input is invalid
    if opts.ray_version not in versions_list:
        print_colored(FAIL, "Ray version %s not supported!" % opts.ray_version)
        print_ray_versions_and_modes()
        sys.exit(1)

    # validate resiliency profile/mode input (case insensitive)
    # print list of supported versions and modes if input is unsupported
    if opts.res_mode.lower() not in res_modes_list:
        print_colored(FAIL, "Resiliency profile %s not supported!" % opts.res_mode)
        print_ray_versions_and_modes()
        sys.exit(1)

    # generate system configMap yaml file
    generate_system_config_map(opts.ray_version, opts.res_mode, opts.path, opts.verbose)

if __name__ == "__main__":
    main(sys.argv[1:])
