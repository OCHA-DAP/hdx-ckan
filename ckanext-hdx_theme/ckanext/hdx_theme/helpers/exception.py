class BaseHdxException(Exception):

    def __init__(self, message, exceptions=None):
        super(Exception, self).__init__(message)

        self.errors = exceptions if exceptions else []
