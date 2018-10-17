class ADLError(Exception): pass

class ADLSourceError(ADLError):
    def __init__(self, message, source, lineno, col_offset, lineno2=None, col_offset2=None):
        if lineno2 is None or col_offset2 is None:
            message = "Line {0}: {1}".format(lineno, message)
            quoted = source.split("\n")[lineno - 1]
            arrow = "-" * (col_offset + 4) + "^"
            super(ADLSourceError, self).__init__(message + "\n    " + quoted + "\n" + arrow)

        elif lineno == lineno2:
            message = "Line {0}: {1}".format(lineno, message)
            quoted = source.split("\n")[lineno - 1]
            arrow = "-" * (col_offset + 4) + "^" * (col_offset2 - col_offset)
            super(ADLSourceError, self).__init__(message + "\n    " + quoted + "\n" + arrow)

        else:
            message = "Lines {0}-{1}: {2}".format(lineno, lineno2, message)
            quoted = "\n    ".join(source.split("\n")[lineno - 1 : lineno2])
            super(ADLSourceError, self).__init__(message + "\n    " + quoted)

class ADLNodeError(ADLSourceError):
    def __init__(self, message, node=None, wide=False):
        if node is None or node.source is None:
            ADLError.__init__(self, message)
        elif not wide:
            ADLSourceError.__init__(self, message, node.source, node.lineno, node.col_offset)
        else:
            ADLSourceError.__init__(self, message, node.source, node.lineno, node.col_offset, node.lineno2, node.col_offset2)

class ADLSyntaxError(ADLSourceError): pass
class ADLTypeError(ADLNodeError): pass
class ADLNameError(ADLNodeError): pass
class ADLInternalError(ADLNodeError): pass
