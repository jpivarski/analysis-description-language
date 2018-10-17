import fnmatch
import math

import numpy

import adl.error
import adl.parser
import adl.util
from adl.syntaxtree import *
    
class SymbolTable(object):
    @classmethod
    def fromdict(cls, data, parent=None):
        out = SymbolTable(parent)
        for n, x in data.items():
            out[Identifier(n)] = x
        return out

    def __init__(self, parent=None):
        self.parent = None
        self.symbols = {}

    def __getitem__(self, where):
        if where.name in self.symbols:
            return self.symbols[where.name]
        elif self.parent is not None:
            return self.parent[where.name]
        else:
            raise adl.error.ADLNameError("no symbol named {0} in this scope".format(repr(where.name)), where)

    def __setitem__(self, where, what):
        self.symbols[where.name] = what

def calculate(expression, symbols):
    if isinstance(expression, Literal):
        return expression.value

    elif isinstance(expression, Identifier):
        return symbols[expression]

    elif isinstance(expression, Call):
        raise NotImplementedError

    else:
        raise adl.error.ADLInternalError("cannot calculate a {0}; it is not an expression".format(type(expression).__name__), expression)

def handle(statement, symbols, source, aggregation):
    if isinstance(statement, Define):
        raise NotImplementedError

    elif isinstance(statement, FunctionDefine):
        raise NotImplementedError

    elif isinstance(statement, Count):
        raise NotImplementedError

    elif isinstance(statement, Profile):
        raise NotImplementedError

    elif isinstance(statement, Fraction):
        raise NotImplementedError

    elif isinstance(statement, Vary):
        raise NotImplementedError

    elif isinstance(statement, Region):
        raise NotImplementedError

    elif isinstance(statement, Regions):
        raise NotImplementedError

    elif isinstance(statement, Source):
        raise NotImplementedError

    else:
        raise adl.error.ADLInternalError("cannot handle a {0}; it is not a statement".format(type(statement).__name__), statement)

class Storage(object): pass

class Count(Storage):
    def __init__(self):
        self.sumw = 0
        self.sumw2 = 0

    def zeros_like(self):
        return Count()

    def __repr__(self):
        return "{0} +- {1}".format(self.sumw, math.sqrt(self.sumw2))

    def __getitem__(self, where):
        if where == ():
            return self
        else:
            raise IndexError("too many dimensions in index")

    def fill(self, symbols, weight):
        self.sumw += weight
        self.sumw2 += weight**2
        
class Binning(object):
    @staticmethod
    def binning(call, expression, storage):
        if isinstance(call, Call) and call.function.name == "regular":
            adl.util.check_args(call, 3, 3)
            if not isinstance(call.arguments[0], Literal) and adl.util.isint(call.arguments[0].value, 1):
                raise adl.error.ADLTypeError("numbins must be a literal positive integer", call.arguments[0])
            if not isinstance(call.arguments[1], Literal) and adl.util.isnum(call.arguments[1].value):
                raise adl.error.ADLTypeError("low must be a literal number", call.arguments[1])
            if not isinstance(call.arguments[2], Literal) and adl.util.isnum(call.arguments[2].value):
                raise adl.error.ADLTypeError("high must be a literal number", call.arguments[2])
            return RegularBinning(expression, call.arguments[0].value, call.arguments[1].value, call.arguments[2].value, storage)

        elif isinstance(call, Call) and call.function.name == "variable":
            adl.util.check_args(call, 1, None)
            for x in call.arguments:
                if not adl.util.isnum(x.value):
                    raise adl.error.ADLTypeError("edges must be literal numbers", x)
            return VariableBinning([x.value for x in call.arguments], storage)

        else:
            raise ADLTypeError("not a binning", call)

class RegularBinning(Binning):
    def __init__(self, expression, numbins, low, high, storage):
        self.expression = expression
        self.numbins = int(numbins)
        self.low = float(low)
        self.high = float(high)
        self.values = [storage.zeros_like() for x in range(self.numbins)]
        self.underflow = storage.zeros_like()
        self.overflow = storage.zeros_like()
        self.nanflow = storage.zeros_like()

    def zeros_like(self):
        return RegularBinning(self.expression, self.numbins, self.low, self.high, self.storage)

    @property
    def edges(self):
        return numpy.linspace(self.low, self.high, self.numbins + 1).tolist()

    def __getitem__(self, where):
        if not isinstance(where, tuple):
            where = (where,)
        head, tail = where[0], where[1:]

        if adl.util.isint(head, 0, self.numbins - 1):
            return self.values[head][tail]
        elif head == -adl.util.inf or adl.util.isint(head, None, -1):
            return self.underflow[tail]
        elif head == adl.util.inf or adl.util.isint(head, self.numbins, None):
            return self.overflow[tail]
        else:
            return self.nanflow[tail]

    def fill(self, symbols, weight):
        x = calculate(self.expression, symbols)
        if not adl.util.isnum(x):
            raise adl.error.ADLTypeError("expression returned a non-number: {0}".format(x), self.expression)

        index = self.numbins * (x - self.low) / (self.high - self.low)
        if index < 0:
            self.underflow.fill(symbols, weight)
        elif index >= self.numbins:
            self.overflow.fill(symbols, weight)
        elif adl.util.isnan(index):
            self.nanflow.fill(symbols, weight)
        else:
            self.values[int(math.trunc(index))].fill(symbols, weight)

class VariableBinning(Binning):
    def __init__(self, expression, edges, storage):
        self.expression = expression
        self.edges = [float(x) for x in edges]
        self.values = [storage.copy() for x in range(self.numbins)]
        self.underflow = storage.copy()
        self.overflow = storage.copy()
        self.nanflow = storage.copy()

    def zeros_like(self):
        return VariableBinning(self.expression, self.edges, self.storage)

    @property
    def numbins(self):
        return len(self.edges) - 1

    def __getitem__(self, where):
        if not isinstance(where, tuple):
            where = (where,)
        head, tail = where[0], where[1:]

        if adl.util.isint(head, 0, self.numbins - 1):
            return self.values[head][tail]
        elif head == -adl.util.inf or adl.util.isint(head, None, -1):
            return self.underflow[tail]
        elif head == adl.util.inf or adl.util.isint(head, self.numbins, None):
            return self.overflow[tail]
        else:
            return self.nanflow[tail]

    def fill(self, symbols, weight=1):
        x = calculate(self.expression, symbols)
        if not adl.util.isnum(x):
            raise adl.error.ADLTypeError("expression returned a non-number: {0}".format(x), self.expression)

        if x < self.edges[0]:
            self.underflow.fill(symbols, weight)
        elif x >= self.edges[-1]:
            self.overflow.fill(symbols, weight)
        elif adl.util.isnan(x):
            self.nanflow.fill(symbols, weight)
        else:
            for i in self.numbins:
                if self.edges[i] <= x < self.edges[i + 1]:
                    self.values[i].fill(symbols, weight)
                    break

class Run(object):
    def __init__(self, source):
        if isinstance(source, str):
            self.ast = adl.parser.parse(source)
        else:
            self.ast = adl.parser.parse(source.read())
        self.clear()

    def clear(self):
        pass  # FIXME

    def __iter__(self, source=None, **data):
        if not isinstance(self.ast, BodySuite):
            raise adl.error.ADLTypeError("this ADL source file/string is not an expression")
        for i in range(min(len(x) for x in data.values())):
            yield self(source=source, **{n: x[i] for n, x in data.items()})

    def fill(self, source=None, **data):
        for i in range(min(len(x) for x in data.values())):
            self(source=source, **{n: x[i] for n, x in data.items()})

    def __call__(self, source=None, **data):
        symbols = SymbolTable.fromdict(data)

        if isinstance(self.ast, BodySuite):
            for statement in self.ast.body[:-1]:
                handle(statement, symbols, source, self.aggregation)
            return calculate(self.ast.body[-1], symbols)

        elif isinstance(self.ast, BlockSuite):
            for statement in self.ast.block:
                handle(statement, symbols, source, self.aggregation)

        else:
            raise adl.error.ADLInternalError("cannot execute a {0}; it is not an expression or a set of region/vary blocks".format(type(statement).__name__), statement)
