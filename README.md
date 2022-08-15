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

<p align="center">
<img src="./images/codeflare_square.svg" width="200" height="200">
</p>

<!--
<p align="center">
<img src="./images/pipelines.svg" width="340" height="207">
</p> 
-->

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![Build
Status](https://travis-ci.com/project-codeflare/codeflare.svg?branch=main)](https://travis-ci.com/project-codeflare/codeflare.svg?branch=main) 
[![PyPI](https://badge.fury.io/py/codeflare.svg)](https://badge.fury.io/py/codeflare)
[![Downloads](https://pepy.tech/badge/codeflare)](https://pepy.tech/project/codeflare)
[![Documentation Status](https://readthedocs.org/projects/codeflare/badge/?version=latest)](https://codeflare.readthedocs.io/en/latest/?badge=latest)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue.svg)](https://github.com/project-codeflare/codeflare/issues)

<!-- >> **⚠ UPDATE**  
> CodeFlare is evolving! Check our [updates](https://github.com/project-codeflare/codeflare#pipeline-execution-and-scaling) for CodeFlare Pipelines and related contributions to Ray Workflows under Ray project. -->

# Scale complex AI/ML pipelines anywhere

CodeFlare is a framework to simplify the integration, scaling and acceleration of complex multi-step analytics and machine learning pipelines on the cloud.

Its main features are: 

* **Simplified user experience**:
Interactive and rich command line interface and live dashboards enabling automation to deploy, run and monitor end-to-end pipelines, significantly minimizing the effort and skills needed to scale AI and ML workflows.

* **Pipeline execution and scaling**:
Integrated with Ray Workflows, CodeFlare Pipelines faciltates the definition and parallel execution of pipelines. It unifies pipeline workflows across multiple frameworks while providing nearly optimal scale-out parallelism on pipelined computations.
<!--CodeFlare Pipelines facilities the definition and parallel execution of pipelines. It unifies pipeline workflows across multiple platforms such as [scikit-learn](https://scikit-learn.org/) and [Apache Spark](https://spark.apache.org/), while providing nearly optimal scale-out parallelism on pipelined computations.-->

* **Deploy and integrate anywhere**: 
CodeFlare simplifies deployment and integration by enabling a serverless user experience with the integration with Red Hat OpenShift and IBM Cloud Code Engine and providing adapters and connectors to make it simple to load data and connect to data services.

<p align="center">
<img src="./images/codeflare_arch_diagram.svg" width="880" height="640">
</p>

<!-- ## Release status

This project is under active development. See the [Documentation](https://codeflare.readthedocs.io/en/latest/index.html) for design descriptions and the latest version of the APIs. 
-->

---
## Quick start

### Run on your laptop

### Installing CodeFlare client

See instructions [here](https://github.com/project-codeflare/codeflare-cli) for installing CodeFlare CLI and Dashboard.

<p align="center">
<img src="./images/codeflare_cli.svg" width="150" height="150">
</p>

#### Instaling locally

CodeFlare can be installed from PyPI.

Prerequisites:
* [Python 3.7 or 3.8](https://www.python.org/downloads/)
* [JupyterLab](https://jupyter.org) *(to run examples)*

We recommend installing Python 3.8.6 using
[pyenv](https://github.com/pyenv/pyenv). You can find [here](https://codeflare.readthedocs.io/en/latest/getting_started/setting_python_env.html) recommended steps to set up the Python environment.


Install from PyPI:
```bash
pip3 install --upgrade pip          # CodeFlare requires pip >21.0
pip3 install --upgrade codeflare
```

Alternatively, you can also build locally with:
```shell
git clone https://github.com/project-codeflare/codeflare.git
cd codeflare
pip3 install --upgrade pip
pip3 install .
```

<!--
#### Using Docker

You can try CodeFlare by running the docker image from [Docker Hub](https://hub.docker.com/r/projectcodeflare/codeflare/tags):
- `projectcodeflare/codeflare:latest` has the latest released version installed.

The command below starts the most recent development build in a clean environment:

```bash
docker run --rm -it -p 8888:8888 projectcodeflare/codeflare:latest
```

It should produce an output similar to the one below, where you can then find the URL to run CodeFlare from a Jupyter notebook in your local browser.

```
[I <time_stamp> ServerApp] Jupyter Server <version> is running at:
...
[I <time_stamp> ServerApp]     http://127.0.0.1:8888/lab
```
-->

<!-- #### Using Binder service

You can try out some of CodeFlare features using the My Binder service.

Click on the link below to try CodeFlare, on a sandbox environment, without having to install anything.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/project-codeflare/codeflare.git/develop)
-->

---

## Pipeline execution and scaling

<p align="center">
<img src="./images/pipelines.svg" width="296" height="180">
</p>

> **⚠ UPDATE**  
> As of January 2022, this feature is now built on [Ray Workflows](https://docs.ray.io/en/releases-1.9.0/workflows/concepts.html) with parts of it in [Ray core](https://github.com/ray-project/ray/releases/tag/ray-1.7.0) and the rest in a [DAG contribution repository](https://github.com/ray-project/contrib-workflow-dag). Please follow these links to contribute to CodeFlare Pipelines. 

**CodeFlare Pipelines** reimagined pipelines to provide a more intuitive API for the data scientist to create AI/ML pipelines, data workflows, pre-processing, post-processing tasks, and many more which can scale from a laptop to a cluster seamlessly.

See the API documentation [here](https://codeflare.readthedocs.io/en/latest/codeflare.pipelines.html), and reference use case documentation in the Examples section.

A set of reference examples are provided as executable [notebooks](https://github.com/project-codeflare/codeflare/tree/main/notebooks). 

To run examples, if you haven't done so yet, clone the CodeFlare project with:

```bash
git clone https://github.com/project-codeflare/codeflare.git
```

Example notebooks require JupyterLab, which can be installed with:
```bash
pip3 install --upgrade jupyterlab
```

Use the command below to run locally:
```shell
jupyter-lab codeflare/notebooks/<example_notebook>
```

The step above should automatically open a browser window and connect to a running Jupyter server.

If you are using any one of the recommended cloud based deployments (see below), examples are found in the `codeflare/notebooks` directory in the container image. The examples can be executed directly from the Jupyter environment. 

As a first example of the API usage, see the [sample pipeline](https://github.com/project-codeflare/codeflare/blob/main/notebooks/sample_pipeline.ipynb). 

For an example of how CodeFlare Pipelines can be used to scale out common machine learning problems, see the [grid search](https://github.com/project-codeflare/codeflare/blob/develop/notebooks/Grid%20Search%20Sample.ipynb) example. It shows how hyperparameter optimization for a reference pipeline can be scaled and accelerated with both task and data parallelism.

## Deploy and integrate anywhere

CodeFlare is built on [Red Hat OpenShift Container Platform](https://www.openshift.com) and can be deployed anywhere, from on-prem to cloud, and integrate easily with other cloud-native ecosystems.

See [Running with Red Hat OpenShift](./deploy/redhat_openshift) for detailed instructions on how to run CodeFlare on OpenShift Container Platform.

## Contributing

Join us in making CodeFlare Better! We encourage you to take a look at our [Contributing](CONTRIBUTING.md) page.

## Blog

CodeFlare related blogs are published on our [Medium publication](https://medium.com/codeflare).

## License

CodeFlare is an open-source project with an [Apache 2.0 license](LICENSE).
