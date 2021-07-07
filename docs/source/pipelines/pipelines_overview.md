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

![pipelines](../images/pipelines.svg)

## CodeFlare Pipelines

CodeFlare Pipelines reimagined pipelines to provide a more intuitive API for the data scientist to create AI/ML pipelines, data workflows, pre-processing, post-processing tasks, and many more which can scale from a laptop to a cluster seamlessly.

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

If you are using any one of the recommended cloud based deployments, examples are found in the `codeflare/notebooks` directory in the container image. The examples can be executed directly from the Jupyter environment. 

As a first example of the API usage, see the [sample pipeline](https://github.com/project-codeflare/codeflare/blob/main/notebooks/sample_pipeline.ipynb). 

For an example of how CodeFlare Pipelines can be used to scale out and speed up common machine learning problems, see the [grid search](https://github.com/project-codeflare/codeflare/blob/develop/notebooks/Grid%20Search%20Sample.ipynb) example. It shows how hyperparameter optimization for a reference pipeline can be scaled with both task and data parallelism.
