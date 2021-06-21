# CodeFlare on OpenShift Container Platform (OCP)

A few installation deployment targets are provided below.

- [Ray Cluster Using Operator on Openshift](#Openshift-Ray-Cluster-Operator)
- [Ray Cluster on Openshift](#Openshift-Cluster)
- [Ray Cluster on Openshift for Jupyter](#Jupyter)

## Openshift Ray Cluster Operator

Deploying the [Ray Operator](https://docs.ray.io/en/master/cluster/kubernetes.html?highlight=operator#the-ray-kubernetes-operator)

## Openshift Cluster

### Dispatch Ray Cluster on Openshift

#### Pre-req
- Access to openshift cluster
- Python 3.8+ 

We recommend installing Python 3.8.7 using
[pyenv](https://github.com/pyenv/pyenv).

#### Setup


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
    
       ```
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
    ray submit python/ray/autoscaler/kubernetes/example-full.yaml x.py 
    Loaded cached provider configuration
    If you experience issues with the cloud provider, try re-running the command with --no-config-cache.
    2021-02-09 08:50:51,028	INFO command_runner.py:171 -- NodeUpdater: ray-head-ql46b: Running kubectl -n ray exec -it ray-head-ql46b -- bash --login -c -i 'true && source ~/.bashrc && export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && (python ~/x.py)'
    2021-02-09 05:52:10,538	INFO worker.py:655 -- Connecting to existing Ray cluster at address: 172.30.236.163:6379
    [0, 1, 4, 9]
    ```

### Jupyter

Jupyter setup demo [Reference repository](https://github.com/erikerlandson/ray-odh-demo)

### Running examples

Once in a Jupyer envrionment, refer to [notebooks](../../notebooks) for example pipeline. Documentation for reference use cases can be found in [Examples](https://codeflare.readthedocs.io/en/latest/).