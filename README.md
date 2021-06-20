
<!--
[![Gitter](https://badges.gitter.im/elyra-ai/community.svg)](https://gitter.im/elyra-ai/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
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
[![Documentation Status](https://readthedocs.org/projects/codeflare/badge/?version=latest)](https://codeflare.readthedocs.io/en/latest/?badge=latest)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue.svg)](https://github.com/project-codeflare/codeflare/issues)


# Scale complex AI/ML pipelines anywhere

CodeFlare is a framework to simplify the integration, scaling and acceleration of complex multi-step analytics and machine learning pipelines on the cloud.

Its main features are: 

* **Pipeline execution and scaling**:
CodeFlare Pipelines facilities the definition and parallel execution of pipelines. It unifies pipeline workflows across multiple frameworks, while providing nearly optimal scale-out parallelism on pipelined computations.
<!--CodeFlare Pipelines facilities the definition and parallel execution of pipelines. It unifies pipeline workflows across multiple platforms such as [scikit-learn](https://scikit-learn.org/) and [Apache Spark](https://spark.apache.org/), while providing nearly optimal scale-out parallelism on pipelined computations.-->

* **Deploy and integrate anywhere**: 
CodeFlare simplifies deployment and integration by enabling a serverless user experience with the integration with Red Hat Open Shift and IBM Cloud Code Engine, and integrating adapters and connectors to make it simple to load data and connect to data services.

<p align="center">
<img src="./images/codeflare_arch_diagram.svg" width="876" height="476">
</p>

## Release status

This project is under active development. See the [Documentation](https://codeflare.readthedocs.io/en/latest/index.html) for design descriptions and latest version of the APIs. 

## Quick start

### Run in your laptop

#### Using Docker

You can try CodeFlare by running the docker image from [Docker Hub](https://hub.docker.com/r/projectcodeflare/codeflare/tags):
- `projectcodeflare/codeflare:latest` has the latest released version installed.

The command below starts the most recent development build in a clean environment:

```
docker run -it -p 8888:8888 projectcodeflare/codeflare:latest jupyter-lab --debug
```

It should produce an output similar to the one below, where you can then find the URL to run CodeFlare from a Jupyter notebook in your local browser.

```
    To access the notebook, open this file in a browser:
 ...
    Or copy and paste one of these URLs:
        http://<token>:8888/?token=<token>
     or http://127.0.0.1:8888/?token=<token>
```

Once the notebook is loaded, you can find a selection of examples in `codeflare/notebooks`, which can be executed directly from Jupyter environment. As a first example, we recommend the `sample_pipeline.ipynb` notebook.

#### Using Binder service

You can try out some of CodeFlare features using the My Binder service.

Click on a link below to try CodeFlare, on a sandbox environment, without having to install anything.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/project-codeflare/codeflare.git/master)

#### Instaling locally

CodeFlare can be installed from PyPI.

Prerequisites:
* [Python 3.8+](https://www.python.org/downloads/)
* [Jupyter Lab](https://www.python.org/downloads/) *(to run examples)*

We recommend installing Python 3.8.7 using
[pyenv](https://github.com/pyenv/pyenv).


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

Run the sample pipelines with:
```shell
jupyter-lab notebooks/<example_notabook>
```

The pipeline will use `ray.init()` to start a local Ray cluster. See [configuring Ray](https://docs.ray.io/en/master/configure.html) to ensure you are able to run a Ray cluster locally.

### Scale in the cloud

Unleash the power of pipelines by seamlessly scaling on the cloud. CodeFlare can be deployed with IBM Cloud Code Engine, a fully managed, serverless platform that runs your containerized workloads.

Go to [CodeFlare on IBM Code Engine](./deploy/ibm_cloud_code_engine) for detailed instructions on how to run CodeFlare at scale.


## Contributing

If you are interested in joining us and make CodeFlare better, we encourage you to take a look at our [Contributing](CONTRIBUTING.md) page.