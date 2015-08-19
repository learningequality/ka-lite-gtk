from __future__ import print_function
from __future__ import unicode_literals

class ValidationError(Exception):

    def __init__(self, err_msg, *args, **kwargs):
        self.err_msg = err_msg
        super(ValidationError, self).__init__(err_msg, *args, **kwargs)
