#
# Copyright 2021 IBM
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# Authors: Mudhakar Srivatsa <msrivats@us.ibm.com>
#          Raghu Ganti <rganti@us.ibm.com>
#          Carlos Costa <chcost@us.ibm.com>
#
#

"""codeflare.pipelines.Exceptions
The exceptions that pipeline creation and execution throw are defined here.
"""

class BasePipelineException(Exception):
    """
    Base pipeline exception
    """
    pass


class PipelineSaveException(BasePipelineException):
    """
    Exception thrown when a pipeline save fails
    """
    def __init__(self, message):
        self.message = message


class PipelineNodeNotFoundException(BasePipelineException):
    """
    Exception thrown when a node is not found in a pipeline, this can typically happen when pipelines
    are not properly constructed.
    """
    def __init__(self, message):
        self.message = message


class PipelineException(BasePipelineException):
    """
    Generic pipeline exceptions
    """
    def __init__(self, message):
        self.message = message
