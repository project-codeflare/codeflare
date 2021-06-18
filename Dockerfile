#
# Copyright IBM Corporation 2021
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

ARG base_image=rayproject/ray:1.4.0-py38
FROM ${base_image}

USER root
RUN apt-get update && apt-get install -y build-essential

COPY --chown=ray:users setup.py requirements.txt codeflare/
COPY --chown=ray:users codeflare codeflare/codeflare
COPY --chown=ray:users notebooks codeflare/notebooks
COPY --chown=ray:users resources codeflare/resources

RUN apt-get update
RUN apt-get install gcc

RUN pip install jupyterlab

RUN pip install -r ./codeflare/requirements.txt

RUN pip install -e ./codeflare