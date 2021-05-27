class BasePipelineException(Exception):
    pass


class PipelineSaveException(BasePipelineException):
    def __init__(self, message):
        self.message = message


class PipelineNodeNotFoundException(BasePipelineException):
    def __init__(self, message):
        self.message = message


class PipelineException(BasePipelineException):
    def __init__(self, message):
        self.message = message
