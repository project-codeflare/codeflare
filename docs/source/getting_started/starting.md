<!--
{% comment %}
Copyright 2021 IBM

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
{% endcomment %}
-->

# Running

## CodeFlare on IBM Cloud Code Engine

IBM Cloud Code Engine is a fully managed, serverless platform that runs your containerized workloads, including web apps, microservices, event-driven functions, and batch jobs with run-to-completion characteristics. 

CodeFlare can use IBM Cloud Code Engine to seamlessly scale pipelines on a serverless backend.

The following steps describe how to deploy the examples in [notebooks](https://github.com/project-codeflare/codeflare/tree/develop/notebooks) on a serverless backend with Code Engine (they expand the steps to run Ray on Code Engine [here](https://www.ibm.com/cloud/blog/ray-on-ibm-cloud-code-engine))

### Install pre-requisities

Install the pre-requisites for Code Engine and Ray:

1. Get ready with IBM Code Engine:

- [Set up your Code Engine CLI](https://cloud.ibm.com/docs/codeengine?topic=codeengine-install-cli)
- [optional] [Create your first Code Engine Project using the CLI](https://cloud.ibm.com/docs/codeengine?topic=codeengine-manage-project)

2. [Set up the Kubernetes CLI](https://kubernetes.io/docs/tasks/tools/install-kubectl/)

3. Install Kubernetes:

```shell
pip install kubernetes
```

### Step 1 - Define your Ray Cluster on Code Engine

If not already done in the previous step, create a Code Engine project:

```shell
ibmcloud ce project create -n <your project name>
```

Select the Code Engine project and switch the `kubectl` context to the project:

```shell
ibmcloud ce project select -n <your project name> -k
```

Extract the Kubernetes namespace assigned to your project. The namespace can be found in the `NAME` column in the output of the command:

```shell
kubectl get namespace
````

Export the namespace:

```shell
export NAMESPACE=<namespace from above>
```

A reference Ray cluster definition can be customized for your namespace with the following commands:
```shell
cd ./deploy/ibm_cloud_code_engine/
sed "s/NAMESPACE/$NAMESPACE/" ./example-cluster.yaml.template > ./example-cluster.yaml
```

This reference deployment file will create a Ray cluster with following characteristics:

- a cluster named example-cluster with up to 10 workers using the Kubernetes provider pointing to your Code Engine project
- A head node type with 1 vCPU and 2GB of memory using the CodeFlare image `codeflare:latest`
- A worker node type with 1 vCPU and 2GB memory using the ray image `codeflare:latest`
- The default startup commands to start Ray within the container and listen to the proper ports
- The autoscaler upscale speed is set to 2 for quick upscaling in this short and simple demo

### Step 2 - Start Ray cluster

You can now start the Ray cluster by running:

```shell 
ray up example-cluster.yaml
```

This command will create the Ray head node as Kubernetes Pod in your Code Engine project. When you create the Ray cluster for the first time, it can take few minutes until the Ray image is downloaded from the container registry. 

### Step 3 - Run sample Pipeline with Jupyter

A Jupyter server will be automatically running on the head node. To access the server from your local machine, execute the command:

```shell
kubectl -n $NAMESPACE port-forward <ray-cluster-name> 8888:8888
```

You can now access the Jupyter server by pointing your browser to the following url:

```shell
http://127.0.0.1:8888/lab
```

Once in the the Jupyer envrionment, examples are found in the `codeflare/notebooks` directory in the container image. Documentation for reference use cases can be found in [Examples](https://codeflare.readthedocs.io/en/latest/).

To execute any of the notebooks with the Ray cluster running on Code Engine, edit the `ray.init()` line with the following parameters:

```python
ray.init(address='auto', _redis_password='5241590000000000')
```

This change will allow pipelines to be auto-scaled on the underlying Ray cluster running on Code Engine (up to 10 workers with the reference deployment). The number of workers and scaling parameters can be adjusted in the `yaml` file.

## CodeFlare on OpenShift Container Platform (OCP)

A few installation deployment targets are provided below:

- [Ray Cluster Using Operator on Openshift](#Openshift-Ray-Cluster-Operator)
- [Ray Cluster on Openshift](#Openshift-Cluster)
- [Ray Cluster on Openshift for Jupyter](#Jupyter)

### Openshift Ray Cluster Operator

Deploying the [Ray Operator](https://docs.ray.io/en/master/cluster/kubernetes.html?highlight=operator#the-ray-kubernetes-operator)

### Openshift Cluster

#### Dispatch Ray Cluster on Openshift

Pre-req
- Access to openshift cluster
- Python 3.7 or 3.8.

We recommend installing Python 3.8.7 using
[pyenv](https://github.com/pyenv/pyenv).

Setup

1. Install CodeFlare

Install from PyPI:
```bash
pip3 install --upgrade codeflare
```

Alternatively, you can also build locally with:
```shell
git clone https://github.com/project-codeflare/codeflare.git
pip3 install --upgrade pip
pip3 install .
pip3 install -r requirements.txt 
```

2. Create Cluster (https://docs.ray.io/en/master/cluster/cloud.html#kubernetes)

   Assuming openshift cluster access from pre-reqs.

   a) Create namespace
      ```shell
       $ oc create namespace codefalre
       namespace/codeflare created
       $
      ```

   b) Bring up Ray cluster  

    ```
      $ ray up ray/python/ray/autoscaler/kubernetes/example-full.yaml
        Cluster: default

        Checking Kubernetes environment settings
        2021-02-09 06:40:09,612	INFO config.py:169 -- KubernetesNodeProvider: using existing namespace 'ray'
        2021-02-09 06:40:09,671	INFO config.py:202 -- KubernetesNodeProvider: autoscaler_service_account 'autoscaler' not found, attempting to create it
        2021-02-09 06:40:09,738	INFO config.py:204 -- KubernetesNodeProvider: successfully created autoscaler_service_account 'autoscaler'
        2021-02-09 06:40:10,196	INFO config.py:228 -- KubernetesNodeProvider: autoscaler_role 'autoscaler' not found, attempting to create it
        2021-02-09 06:40:10,265	INFO config.py:230 -- KubernetesNodeProvider: successfully created autoscaler_role 'autoscaler'
        2021-02-09 06:40:10,573	INFO config.py:261 -- KubernetesNodeProvider: autoscaler_role_binding 'autoscaler' not found, attempting to create it
        2021-02-09 06:40:10,646	INFO config.py:263 -- KubernetesNodeProvider: successfully created autoscaler_role_binding 'autoscaler'
        2021-02-09 06:40:10,704	INFO config.py:294 -- KubernetesNodeProvider: service 'ray-head' not found, attempting to create it
        2021-02-09 06:40:10,788	INFO config.py:296 -- KubernetesNodeProvider: successfully created service 'ray-head'
        2021-02-09 06:40:11,098	INFO config.py:294 -- KubernetesNodeProvider: service 'ray-workers' not found, attempting to create it
        2021-02-09 06:40:11,185	INFO config.py:296 -- KubernetesNodeProvider: successfully created service 'ray-workers'
        No head node found. Launching a new cluster. Confirm [y/N]: y

        Acquiring an up-to-date head node
        2021-02-09 06:40:14,396	INFO node_provider.py:113 -- KubernetesNodeProvider: calling create_namespaced_pod (count=1).
          Launched a new head node
          Fetching the new head node

        <1/1> Setting up head node
          Prepared bootstrap config
          New status: waiting-for-ssh
          [1/7] Waiting for SSH to become available
            Running `uptime` as a test.
        2021-02-09 06:40:15,296	INFO command_runner.py:171 -- NodeUpdater: ray-head-ql46b: Running kubectl -n ray exec -it ray-head-ql46b -- bash --login -c -i 'true && source ~/.bashrc && export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && (uptime)'
        error: unable to upgrade connection: container not found ("ray-node")
            SSH still not available (Exit Status 1): kubectl -n ray exec -it ray-head-ql46b -- bash --login -c -i 'true && source ~/.bashrc && export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && (uptime)', retrying in 5 seconds.
        2021-02-09 06:40:22,197	INFO command_runner.py:171 -- NodeUpdater: ray-head-ql46b: Running kubectl -n ray exec -it ray-head-ql46b -- bash --login -c -i 'true && source ~/.bashrc && export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && (uptime)'

        03:41:41 up 81 days, 14:25,  0 users,  load average: 1.42, 0.87, 0.63
            Success.
          Updating cluster configuration. [hash=16487b5e0285fc46d5f1fd6da0370b2f489a6e5f]
          New status: syncing-files
          [2/7] Processing file mounts
        2021-02-09 06:41:42,330	INFO command_runner.py:171 -- NodeUpdater: ray-head-ql46b: Running kubectl -n ray exec -it ray-head-ql46b -- bash --login -c -i 'true && source ~/.bashrc && export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && (mkdir -p ~)'
          [3/7] No worker file mounts to sync
          New status: setting-up
          [4/7] No initialization commands to run.
          [5/7] Initalizing command runner
          [6/7] No setup commands to run.
          [7/7] Starting the Ray runtime
        2021-02-09 06:42:10,643	INFO command_runner.py:171 -- NodeUpdater: ray-head-ql46b: Running kubectl -n ray exec -it ray-head-ql46b -- bash --login -c -i 'true && source ~/.bashrc && export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && (export RAY_OVERRIDE_RESOURCES='"'"'{"CPU":1,"GPU":0}'"'"';ray stop)'
        Did not find any active Ray processes.
        2021-02-09 06:42:13,845	INFO command_runner.py:171 -- NodeUpdater: ray-head-ql46b: Running kubectl -n ray exec -it ray-head-ql46b -- bash --login -c -i 'true && source ~/.bashrc && export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && (export RAY_OVERRIDE_RESOURCES='"'"'{"CPU":1,"GPU":0}'"'"';ulimit -n 65536; ray start --head --num-cpus=$MY_CPU_REQUEST --port=6379 --object-manager-port=8076 --autoscaling-config=~/ray_bootstrap_config.yaml --dashboard-host 0.0.0.0)'
        Local node IP: 172.30.236.163
        2021-02-09 03:42:17,373	INFO services.py:1195 -- View the Ray dashboard at http://172.30.236.163:8265

        --------------------
        Ray runtime started.
        --------------------

        Next steps
          To connect to this Ray runtime from another node, run
            ray start --address='172.30.236.163:6379' --redis-password='5241590000000000'

          Alternatively, use the following Python code:
            import ray
            ray.init(address='auto', _redis_password='5241590000000000')

          If connection fails, check your firewall settings and network configuration.

          To terminate the Ray runtime, run
            ray stop
          New status: up-to-date

        Useful commands
          Monitor autoscaling with
            ray exec /Users/darroyo/git_workspaces/github.com/ray-project/ray/python/ray/autoscaler/kubernetes/example-full.yaml 'tail -n 100 -f /tmp/ray/session_latest/logs/monitor*'
          Connect to a terminal on the cluster head:
            ray attach /Users/darroyo/git_workspaces/github.com/ray-project/ray/python/ray/autoscaler/kubernetes/example-full.yaml
          Get a remote shell to the cluster manually:
            kubectl -n ray exec -it ray-head-ql46b -- bash  
      ```

3. Verify  
   a) Check for head node
    
    ```
    $ oc get pods
    NAME             READY   STATUS    RESTARTS   AGE
    ray-head-ql46b   1/1     Running   0          118m
    $
    ```
   b) Run example test
    
    ```
    ray submit ray/python/ray/autoscaler/kubernetes/example-full.yaml x.py 
    Loaded cached provider configuration
    If you experience issues with the cloud provider, try re-running the command with --no-config-cache.
    2021-02-09 08:50:51,028	INFO command_runner.py:171 -- NodeUpdater: ray-head-ql46b: Running kubectl -n ray exec -it ray-head-ql46b -- bash --login -c -i 'true && source ~/.bashrc && export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && (python ~/x.py)'
    2021-02-09 05:52:10,538	INFO worker.py:655 -- Connecting to existing Ray cluster at address: 172.30.236.163:6379
    [0, 1, 4, 9]
    ```

### Jupyter

Jupyter setup demo [Reference repository](https://github.com/erikerlandson/ray-odh-demo)

### Running examples

Once in a Jupyer envrionment, refer to [notebooks](https://github.com/project-codeflare/codeflare/tree/develop/notebooks) for example pipelines. Documentation for reference use cases can be found in [Examples](https://codeflare.readthedocs.io/en/latest/).
