*** This is a first draft of README and we'll soon update it with more and clear text ***

## Introduction
This python script is an entry point where users can specify resiliency mode and Ray version.
It then generates a system config-map (system-cm.yaml) YAML file.
The system config-map contains all relevant ray's system-level configurations for the ray cluster.

## Background and Motivation
Resiliency in Ray is limited, and it can be improved by tuning system-level configurations.
Moreover, configurations can also be tuned to improve the performance of a ray workload.
However, ray has a large set of configuration options available, and the count is increasing with each release.
For example, Ray version 1.5.0 has 113 configuration options available. It is inconvenient for users to learn and tune each configuration manually. Therefore, we need a tool where users can easily configure the ray cluster.

## Example usage
```
python3 Usage: ray-res-config.py --ray-version <arg> --resiliency-mode <arg>
```
Use `--help` option for all available options.

## Tool features/options


## TODOs
- [x] Fetch Ray configs for 1.x.x versions from Github if not available locally and save locally
- [x] Parse configs and dump configs in file to be edited later according to the res
- [x] If any config value is different than default value then add that config to the --system-config parameter
- [x] Dump config in a yaml file named system-cm.yaml
- [ ] Change hardcoded string to dynamic to dump in system-cm.yaml
- [ ] Update format of system config string that works correctly
- [ ] Segregate internal and external options
- [ ] Spread code in multiple files
- [ ] Extend to more Ray versions
- [ ] Add Try-catch and checks to improve robustness
- [ ] Add code to also dump Ray operator and cluster yamls
- [ ] Give a sample cluster Yaml to user to let user edit cluster specific configurations, e.g., cpu, num of workers
- [ ] Add an example usage of the script
- [ ] Test custom Ray build instead of Ray's official images