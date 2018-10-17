import copy
import fnmatch
import math

import numpy

import adl.error
import adl.parser
import adl.util
from adl.syntaxtree import *
    
class Storage(object): pass

class Binning(object):
    @staticmethod
    def binning(call, storage):
        if isinstance(call, Call) and call.function.name == "regular":
            adl.util.check_args(call, 3, 3)
            if not isinstance(call.arguments[0], Literal) and adl.util.isint(call.arguments[0].value, 1):
                raise adl.error.ADLTypeError("numbins must be a literal positive integer", call.arguments[0])
            if not isinstance(call.arguments[1], Literal) and adl.util.isnum(call.arguments[1].value):
                raise adl.error.ADLTypeError("low must be a literal number", call.arguments[1])
            if not isinstance(call.arguments[2], Literal) and adl.util.isnum(call.arguments[2].value):
                raise adl.error.ADLTypeError("high must be a literal number", call.arguments[2])
            return RegularBinning(call.arguments[0].value, call.arguments[1].value, call.arguments[2].value, storage)

        elif isinstance(call, Call) and call.function.name == "variable":
            adl.util.check_args(call, 1, None)
            for x in call.arguments:
                if not adl.util.isnum(x.value):
                    raise adl.error.ADLTypeError("edges must be literal numbers", x)
            return VariableBinning([x.value for x in call.arguments], storage)

        else:
            raise ADLTypeError("not a binning", call)

class RegularBinning(Binning):
    def __init__(self, numbins, low, high, storage):
        self.numbins = int(numbins)
        self.low = float(low)
        self.high = float(high)
        self.values = [copy.deepcopy(storage) for x in range(self.numbins)]
        self.underflow = copy.deepcopy(storage)
        self.overflow = copy.deepcopy(storage)
        self.nanflow = copy.deepcopy(storage)

    @property
    def edges(self):
        return numpy.linspace(self.low, self.high, self.numbins + 1).tolist()

    def __getitem__(self, where):
        if adl.util.isint(where, 0, self.numbins - 1):
            return self.values[where]
        elif where == -adl.util.inf or adl.util.isint(where, None, -1):
            return self.underflow
        elif where == adl.util.inf or adl.util.isint(where, self.numbins, None):
            return self.overflow
        else:
            return self.nanflow

    def fill(self, x, weight=1):
        index = self.numbins * (x - self.low) / (self.high - self.low)
        if index < 0:
            self.underflow += weight
        elif index >= self.numbins:
            self.overflow += weight
        elif adl.util.isnan(index):
            self.nanflow += weight
        else:
            self.values[int(math.trunc(index))] += weight

class VariableBinning(Binning):
    def __init__(self, edges, storage):
        self.edges = [float(x) for x in edges]
        self.values = [copy.deepcopy(storage) for x in range(self.numbins)]
        self.underflow = copy.deepcopy(storage)
        self.overflow = copy.deepcopy(storage)
        self.nanflow = copy.deepcopy(storage)

    @property
    def numbins(self):
        return len(self.edges) - 1

    def __getitem__(self, where):
        if adl.util.isint(where, 0, self.numbins - 1):
            return self.values[where]
        elif where == -adl.util.inf or adl.util.isint(where, None, -1):
            return self.underflow
        elif where == adl.util.inf or adl.util.isint(where, self.numbins, None):
            return self.overflow
        else:
            return self.nanflow

    def fill(self, x, weight=1):
        if x < self.edges[0]:
            self.underflow += weight
        elif x >= self.edges[-1]:
            self.overflow += weight
        elif adl.util.isnan(x):
            self.nanflow += weight
        else:
            for i in self.numbins:
                if self.edges[i] <= x < self.edges[i + 1]:
                    self.values[i] += weight
                    break

class Run(object):
    def __init__(self, source):
        if isinstance(source, str):
            self.ast = adl.parser.parse(source)
        else:
            self.ast = adl.parser.parse(source.read())
        self.clear()

    def clear(self):
        HERE





        
    def __iter__(self, source=None, **data):
        if not isinstance(self.ast, BodySuite):
            raise adl.error.ADLTypeError("this ADL source file/string is not an expression")
        for i in range(min(len(x) for x in data.values())):
            yield self(source=source, **{n: x[i] for n, x in data.items()})

    def fill(self, source=None, **data):
        for i in range(min(len(x) for x in data.values())):
            self(source=source, **{n: x[i] for n, x in data.items()})

    def __call__(self, source=None, **data):
        HERE
