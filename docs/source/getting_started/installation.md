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

## Installation

### Run in your laptop

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

#### Using Binder service

You can try out some of CodeFlare features using the My Binder service.

Click on a link below to try CodeFlare, on a sandbox environment, without having to install anything.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/project-codeflare/codeflare.git/main)