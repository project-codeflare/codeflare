
class BasePipelineException(Exception):
    pass


class PipelineSaveException(BasePipelineException):
    def __init__(self, message):
        self.message = message
