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

# CodeFlare on IBM Cloud Code Engine

IBM Cloud Code Engine is a fully managed, serverless platform that runs your containerized workloads, including web apps, microservices, event-driven functions, and batch jobs with run-to-completion characteristics. 

CodeFlare can use IBM Cloud Code Engine to seamlessly scale pipelines on a serverless backend.

The following steps describe how to deploy the examples in [notebooks](https://github.com/project-codeflare/codeflare/tree/develop/notebooks) on a serverless backend with Code Engine (they expand the steps to run Ray on Code Engine [here](https://www.ibm.com/cloud/blog/ray-on-ibm-cloud-code-engine))

## Install pre-requisities

Install the pre-requisites for Code Engine and Ray:

1. Get ready with IBM Code Engine:

- [Set up your Code Engine CLI](https://cloud.ibm.com/docs/codeengine?topic=codeengine-install-cli)
- [optional] [Create your first Code Engine Project using the CLI](https://cloud.ibm.com/docs/codeengine?topic=codeengine-manage-project)

2. [Set up the Kubernetes CLI](https://kubernetes.io/docs/tasks/tools/install-kubectl/)

3. Install Kubernetes:

```shell
pip install kubernetes
```

## Step 1 - Define your Ray Cluster on Code Engine

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

## Step 2 - Start Ray cluster

You can now start the Ray cluster by running:

```shell 
ray up example-cluster.yaml
```

This command will create the Ray head node as Kubernetes Pod in your Code Engine project. When you create the Ray cluster for the first time, it can take few minutes until the Ray image is downloaded from the container registry. 

## Step 3 - Run sample Pipeline with Jupyter

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

