# CodeFlare on IBM Cloud Code Engine

IBM Cloud Code Engine is a fully managed, serverless platform that runs your containerized workloads, including web apps, microservices, event-driven functions and batch jobs with run-to-completion characteristics. 

CodeFlare Pipelines can use IBM Cloud Code Engine to seamlessly scale pipeline on a serverless backend.

The following steps describe how to deploy the examples in [notebooks](./notebooks) on a serverless backend with Code Engine (they expand the steps to run Ray on Code Engine [here](https://www.ibm.com/cloud/blog/ray-on-ibm-cloud-code-engine))

## Install pre-requisities

Install the pre-requisites for Code Engine and Ray

1. Get ready with IBM Code Engine:

- [Set up your Code Engine CLI](https://cloud.ibm.com/docs/codeengine?topic=codeengine-install-cli)
- [Create your first Code Engine Project using the CLI](https://cloud.ibm.com/docs/codeengine?topic=codeengine-manage-project)

2. [Set up the Kubernetes CLI](https://kubernetes.io/docs/tasks/tools/install-kubectl/)

3. Install Kubernetes (assuming Ray and Python dependcies have been installed with the steps [here](../../README.md).

```shell
pip install kubernetes
```

## Step 1 - Define your Ray Cluster on Code Engine

If not already done, create a project in Code Engine:

```shell
ibmcloud ce project create -n <your project name>
```

Select the Code Engine project and switch the `kubectl` context to the project:

```shell
ibmcloud ce project select -n <your project name>  -k
```

Extract the Kubernetes namespace assigned to your project. The namespace can be found in the NAME column in theoutput of the command:

```shell
kubectl get namespace
````

Export the namespace:

```shell
export NAMESPACE=<namespace from above>
```

Update With the following command you can download a basic Ray cluster definition and customize it for your namespace:
```shell
sed "s/NAMESPACE/$NAMESPACE/" > ./example-cluster.yaml
```

This reference deployment file will create a Ray cluster with following characteristics:

- a cluster named example-cluster with up to 10 workers using the Kubernetes provider pointing to your Code Engine project
- A head node type with 1 vCPU and 2GiB memory using the CodeFlare image codeflare:nightly
- A worker node type with 1 vCPU and 2GiB memory using the ray image codeflare:nightly
- The default startup commands to start Ray within the container and listen to the proper ports
- The autoscaler upscale speed is set to 2 for quick upscaling in this short and simple demo

## Step 2 - Start Ray cluster

You can start now the Ray cluster by running
``` 
ray up example-cluster.yaml
```

This command will create the Ray head node as Kubernetes Pod in your Code Engine project. When you create the Ray cluster for the first time, it can take up to three minutes until the Ray image is downloaded from the Ray repository. 

## Step 3 - Run sample Pipeline with Jupyter

Edit the sample notebook to connect to a running Ray cluster with the command:
```
ray.init(address='auto', _redis_password='5241590000000000')
```

```
ray exec example-cluster.yaml 'jupyter notebook --port=8899 <add file here>'
```

To foward access to the Jupyter notebook, do:
```
kubectl -n $NAMESPACE port-forward <ray-cluster-name>  8899:8899
```

Set up access to Jupyter notebook:
< how to obtain the token >


To access Ray dashboard, do:


In your browser, go to:


