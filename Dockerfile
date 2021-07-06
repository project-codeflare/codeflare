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

ARG base_image=jupyter/minimal-notebook:59c973d16bca
FROM ${base_image}

USER root
RUN chgrp -R 0 /home/jovyan && \
    chmod -R 777 /home/jovyan

# install graphviz
RUN apt-get update && \
    apt-get install -y graphviz

USER $NB_UID

COPY --chown=jovyan:0 setup.py requirements.txt codeflare/
COPY --chown=jovyan:0 codeflare codeflare/codeflare
COPY --chown=jovyan:0 notebooks codeflare/notebooks
COPY --chown=jovyan:0 resources codeflare/resources

ENV JUPYTER_ENABLE_LAB=yes

RUN pip install matplotlib
RUN pip install lale
RUN pip install arff
RUN pip install -r ./codeflare/requirements.txt
RUN pip install -e ./codeflare

CMD start-notebook.sh --NotebookApp.token='' --NotebookApp.password=''