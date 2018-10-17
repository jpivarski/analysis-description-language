import numbers

import numpy

import adl.error

inf = float("inf")
nan = float("nan")

def isint(x, min=None, max=None):
    if not isinstance(x, (numbers.Integral, numpy.integer)):
        return False
    if min is not None and x < min:
        return False
    if max is not None and x > max:
        return False
    return True

def isnum(x, min=None, max=None):
    if not isinstance(x, (numbers.Real, numpy.integer, numpy.floating)):
        return False
    if min is not None and x < min:
        return False
    if max is not None and x > max:
        return False
    return True

def isnan(x):
    return numpy.isnan(x)

def check_args(call, min=0, max=None):
    if len(arguments) < min:
        raise adl.error.ADLTypeError("too few arguments: at least {0} required".format(min), call)
    if max is not None and len(arguments) > max:
        raise adl.error.ADLTypeError("too many arguments: no more than {0} allowed".format(max), call)

def check_params(call):
    if len(call.arguments) < 1:
        raise adl.error.ADLTypeError("cannot define a function with zero arguments (define a value instead)", call)
    if any(not isinstance(x, Identifier) for x in call.arguments):
        raise adl.error.ADLTypeError("cannot define function: parameters must be simple identifiers")

def check_name(node, namespace):
    if node.name in namespace:
        raise adl.error.ADLNameError("name {0} is already defined in this scope".format(repr(node.name)), node)
