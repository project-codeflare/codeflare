"""codeflare.pipelines.Exceptions
The exceptions that pipeline creation and execution throw are defined here.
"""
# Authors: Mudhakar Srivatsa <msrivats@us.ibm.com>
#           Raghu Ganti <rganti@us.ibm.com>
#           Carlos Costa <chcost@us.ibm.com>
#
# License: Apache v2.0


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
