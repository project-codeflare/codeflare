
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
Status](https://travis-ci.com/project-codeflare/rayvens.svg?token=hCqvNPDsDawExuyhTBqj&branch=main
)](https://travis-ci.com/project-codeflare/rayvens.svg?token=hCqvNPDsDawExuyhTBqj&branch=main) 
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue.svg)](https://github.ibm.com/project-codeflare/codeflare/issues)

## Scale complex AI/ML pipelines anywhere

CodeFlare is a framework to simplify the integration, scaling and acceleration of complex multi-step analytics and machine learning pipelines on the cloud.

Building on a unified distributed runtime with [Ray](https://github.com/ray-project/ray), CodeFlare enables:

* **Pipeline execution and scaling**:
CodeFlare Pipelines facilities the definition and parallel execution of pipelines. It unifies pipeline workflows across multiple frameworks, while providing nearly optimal scale-out parallelism on pipelined computations.
<!--CodeFlare Pipelines facilities the definition and parallel execution of pipelines. It unifies pipeline workflows across multiple platforms such as [scikit-learn](https://scikit-learn.org/) and [Apache Spark](https://spark.apache.org/), while providing nearly optimal scale-out parallelism on pipelined computations.-->

* **Deploy and integrate anywhere**: 
CodeFlare simplyfies deployment and integration by enabling a serverless user experience with the integration with Red Hat Open Shift and IBM Cloud Code Engine, and integrating adapters and connectors to make it simpler to load data and connect to data services.

<p align="center">
<img src="./images/codeflare_arch_diagram.svg" width="876" height="476">
</p>

## Release status

This project is under active development. Keep an eye on this page for our first public release!

See the [design document](https://docs.google.com/document/d/1t1K8N07TcbBKBgrcI6jf9tPow00cOKE9whnEVxOd4-U/edit) for more information on our design goals.

## Quick start

You can try out some of CodeFlare features using the My Binder service.

Click on a link below to try CodeFlare, on a sandbox environment, without having to install anything.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/project-codeflare/codeflare.git/main)

### Try on your laptop and scale on the cloud

#### Installing

CodeFlare Pipelines Python >3.8 and Ray >1.3.0.

We recommend installing Python 3.8.7 using
[pyenv](https://github.com/pyenv/pyenv).

Clone this repository and install CodeFlare:
```shell
git clone https://github.com/project-codeflare/codeflare.git
pip install --upgrade pip
pip install .
```

### Example notebooks

You can find a selection of examples in [notebooks](./notebooks). As a first example, we recommend the [Sample Pipeline](./notebooks/sample_pipeline.ipynb

**Running locally**

To run the example pipelines, you will need the following requirements:
- Jupyter Jupyter
- Ray
- sklearn
- pandas
- pytest
- numpy
- pickle51
- graphviz

They can be installed with:

If you use pip, you can install it with:
```shell
pip install -r requirements.txt 
```

Run the sample pipeline with:
```shell
jupyter-lab sample_pipeline.ipynb
```

The pipeline will use `ray.init()` to start a local Ray cluster. See [configuring Ray](https://docs.ray.io/en/master/configure.html) to ensure you are able to run a Ray cluster locally.

## Contributing

If you are interested in joining us and make CodeFlare Pipeline better, we encourage you to take a look at our [Contributing](CONTRIBUTING.md) page.