<p align="center">
<img src="./images/pipelines.svg" width="340" height="207">
</p>

[![Build
Status](https://travis.ibm.com/codeflare/ray-pipeline.svg?token=jYGqz8UKPqjxGaHzGAAi&branch=develop)](https://travis.ibm.com/codeflare/ray-pipeline) 
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)

# CodeFlare Pipelines

The `CodeFlare Pipelines` library provides facilities for defining and running parallel pipelines on top of [Ray](https://ray.io). The goal of this project is to unify pipeline workflows across multiple platforms such as [scikit-learn](https://scikit-learn.org/) and [Apache Spark](https://spark.apache.org/), while providing nearly optimal scale-out parallelism on pipelined computations.

## Release status

This project is under active development. Keep an eye on this page for our first public release!

See the [design document](https://docs.google.com/document/d/1t1K8N07TcbBKBgrcI6jf9tPow00cOKE9whnEVxOd4-U/edit) for more information on our design goals.

## Try CodeFlare Pipelines

#### Installing

CodeFlare Pipelines Python >3.8 and Ray >1.3.0.

We recommend installing Python 3.8.7 using
[pyenv](https://github.com/pyenv/pyenv).

Clone this repository and install CodeFlare:
```shell
git clone https://github.ibm.com/codeflare/ray-pipeline.git
pip install --upgrade pip
pip install .
```

### Try a first example

**TODO:** Add instructions for running the notebooks in the `notebooks` directory.

## Contributing

If you are interested in joining us and make CodeFlare Pipeline better, we encourage you to take a look at our [Contributing](CONTRIBUTING.md) page.
