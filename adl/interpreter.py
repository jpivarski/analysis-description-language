#!/usr/bin/env python

import fnmatch
import math

import numpy

import adl.error
import adl.parser
import adl.util
from adl.syntaxtree import *
            
def calculate(expression, symboltable):
    if isinstance(expression, Literal):
        return expression.value

    elif isinstance(expression, Identifier):
        return symboltable[expression]

    elif isinstance(expression, Call):
        raise NotImplementedError

    else:
        raise adl.error.ADLInternalError("cannot calculate a {0}; it is not an expression".format(type(expression).__name__), expression)

def handle(statement, symboltable, source, aggregation):
    if isinstance(statement, Define):
        symboltable[statement.target] = calculate(statement.expression, symboltable)

    elif isinstance(statement, FunctionDefine):
        raise NotImplementedError

    elif isinstance(statement, Collect):
        if statement.weight is None:
            weight = 1
        else:
            weight = calculate(statement.weight, symboltable)
        aggregation[statement.name.value].fill(symboltable, weight)
        
    elif isinstance(statement, Vary):
        raise NotImplementedError

    elif isinstance(statement, Region):
        raise NotImplementedError

    elif isinstance(statement, Source):
        raise NotImplementedError

    else:
        raise adl.error.ADLInternalError("cannot handle a {0}; it is not a statement".format(type(statement).__name__), statement)

def initialize(statement, name, aggregation):
    if isinstance(statement, Suite):
        for x in statement.statements:
            initialize(x, name, aggregation)

    elif isinstance(statement, Source):
        raise NotImplementedError

    elif isinstance(statement, Region):
        raise NotImplementedError

    elif isinstance(statement, Vary):
        raise NotImplementedError

    elif isinstance(statement, Collect):
        adl.util.check_name(statement, aggregation)
        name = name + (statement.name.value,)

        if isinstance(statement.statistic, CountStatistic):
            storage = Count(name)
        elif isinstance(statement.statistic, SumStatistic):
            storage = Sum(name, statement.expression)
        elif isinstance(statement.statistic, ProfileStatistic):
            storage = Profile(name, statement.expression)
        elif isinstance(statement.statistic, FractionStatistic):
            raise NotImplementedError
        else:
            raise adl.error.ADLInternalError("{0} is not a collectable statistic".format(type(statement.statistic).__name__), statement.statistic)

        for axis in statement.axes[::-1]:
            storage = Binning.binning(name, axis.binning, axis.expression, storage)

        aggregation[statement.name.value] = storage

    elif isinstance(statement, Statement):
        pass

    else:
        raise adl.error.ADLInternalError("cannot initialize {0}; it is not a statement".format(type(statement).__name__), statement)

class SymbolTable(object):
    @classmethod
    def root(cls, functions, data):
        out = SymbolTable()
        out.symbols.update(functions)
        out.symbols.update(data)
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

    def __contains__(self, where):
        return where.name in self.symbols

class Storage(object):
    def __getitem__(self, where):
        if where == ():
            return self
        else:
            raise IndexError("too many dimensions in index")

    def calculate(self, symboltable):
        x = calculate(self.expression, symboltable)
        if not adl.util.isnum(x):
            raise adl.error.ADLTypeError("expression returned a non-number: {0}".format(x), self.expression)
        return x

    def __float__(self):
        return float(self.value())

class Count(Storage):
    def __init__(self, name):
        self.name = name
        self.sumw = 0
        self.sumw2 = 0

    def zeros_like(self, name):
        return Count(name)

    def __repr__(self):
        return "<Count {0}: {1} +- {2}>".format(", ".join(repr(x) for x in self.name), self.value(), self.error())

    def fill(self, symboltable, weight):
        self.sumw += weight
        self.sumw2 += weight**2

    def value(self):
        return self.sumw

    def error2(self):
        return self.sumw2

    def error(self):
        return math.sqrt(self.sumw2)

    def __iter__(self):
        yield self.value()
        yield self.error()

class Sum(Storage):
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression
        self.sumwx = 0.0

    def zeros_like(self, name):
        return Sum(name, self.expression)

    def __repr__(self):
        return "<Sum {0}: {1}>".format(", ".join(repr(x) for x in self.name), self.value())

    def fill(self, symboltable, weight):
        self.sumwx += weight * self.calculate(symboltable)

    def value(self):
        return self.sumwx

    def __iter__(self):
        yield self.value()

class Profile(Storage):
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression
        self.sumw = 0.0
        self.sumw2 = 0.0
        self.sumwx = 0.0
        self.sumwx2 = 0.0

    def zeros_like(self, name):
        return Profile(name, self.expression)

    def __repr__(self):
        return "<Profile {0}: {1} +- {2}>".format(", ".join(repr(x) for x in self.name), self.value(), self.error())

    def fill(self, symboltable, weight):
        x = self.calculate(symboltable)
        self.sumw += weight
        self.sumw2 += weight**2
        self.sumwx += weight * x
        self.sumwx2 += weight * x**2

    def value(self):
        if self.sumw == 0:
            return 0.0
        else:
            return self.sumwx / self.sumw

    def error2(self):
        if self.sumw2 == 0:
            return 0.0
        else:
            effectivecount = self.sumw**2 / self.sumw2
            return (self.sumwx2 / self.sumw - self.value()**2) / effectivecount

    def error(self):
        return math.sqrt(self.error2())

    def __iter__(self):
        yield self.value()
        yield self.error()

class Binning(object):
    @staticmethod
    def binning(name, call, expression, storage):
        if isinstance(call, Call) and call.function.name == "regular":
            adl.util.check_args(call, 3, 3)
            if not isinstance(call.arguments[0], Literal) and adl.util.isint(call.arguments[0].value, 1):
                raise adl.error.ADLTypeError("numbins must be a literal positive integer", call.arguments[0])
            if not isinstance(call.arguments[1], Literal) and adl.util.isnum(call.arguments[1].value):
                raise adl.error.ADLTypeError("low must be a literal number", call.arguments[1])
            if not isinstance(call.arguments[2], Literal) and adl.util.isnum(call.arguments[2].value):
                raise adl.error.ADLTypeError("high must be a literal number", call.arguments[2])
            return RegularBinning(name, expression, call.arguments[0].value, call.arguments[1].value, call.arguments[2].value, storage)

        elif isinstance(call, Call) and call.function.name == "variable":
            adl.util.check_args(call, 1, None)
            for x in call.arguments:
                if not adl.util.isnum(x.value):
                    raise adl.error.ADLTypeError("edges must be literal numbers", x)
            return VariableBinning(name, expression, [x.value for x in call.arguments], storage)

        else:
            raise ADLTypeError("not a binning", call)

    def __repr__(self):
        return "<{0} {1} at {2:012x}>".format(type(self).__name__, ", ".join(repr(x) for x in self.name), id(self))

class RegularBinning(Binning):
    def __init__(self, name, expression, numbins, low, high, storage):
        self.name = name
        self.expression = expression
        self.numbins = int(numbins)
        self.low = float(low)
        self.high = float(high)
        self.values = [storage.zeros_like(self.name + (i,)) for i, x in enumerate(range(self.numbins))]
        self.underflow = storage.zeros_like(self.name + ("underflow",))
        self.overflow = storage.zeros_like(self.name + ("overflow",))
        self.nanflow = storage.zeros_like(self.name + ("nanflow",))

    def zeros_like(self, name):
        return RegularBinning(name, self.expression, self.numbins, self.low, self.high, self.nanflow)

    @property
    def edges(self):
        return numpy.linspace(self.low, self.high, self.numbins + 1).tolist()

    def __getitem__(self, where):
        if where == ():
            return self
        if not isinstance(where, tuple):
            where = (where,)
        head, tail = where[0], where[1:]

        if adl.util.isint(head, 0, self.numbins - 1):
            return self.values[head][tail]
        elif head == -adl.util.inf or adl.util.isint(head, None, -1):
            return self.underflow[tail]
        elif head == adl.util.inf or adl.util.isint(head, self.numbins, None):
            return self.overflow[tail]
        elif adl.util.isnan(head):
            return self.nanflow[tail]
        elif head == "underflow":
            return self.underflow[tail]
        elif head == "overflow":
            return self.overflow[tail]
        elif head == "nanflow":
            return self.nanflow[tail]
        else:
            raise IndexError("improper index for {0}: {1}".format(type(self).__name__, repr(head)))

    def fill(self, symboltable, weight):
        x = calculate(self.expression, symboltable)
        if not adl.util.isnum(x):
            raise adl.error.ADLTypeError("expression returned a non-number: {0}".format(x), self.expression)

        index = self.numbins * (x - self.low) / (self.high - self.low)
        if index < 0:
            self.underflow.fill(symboltable, weight)
        elif index >= self.numbins:
            self.overflow.fill(symboltable, weight)
        elif adl.util.isnan(index):
            self.nanflow.fill(symboltable, weight)
        else:
            self.values[int(math.trunc(index))].fill(symboltable, weight)

class VariableBinning(Binning):
    def __init__(self, name, expression, edges, storage):
        self.name = name
        self.expression = expression
        self.edges = [float(x) for x in edges]
        self.values = [storage.zeros_like(self.name + (i,)) for i, x in enumerate(range(self.numbins))]
        self.underflow = storage.zeros_like(self.name + ("underflow",))
        self.overflow = storage.zeros_like(self.name + ("overflow",))
        self.nanflow = storage.zeros_like(self.name + ("nanflow",))

    def zeros_like(self, name):
        return VariableBinning(name, self.expression, self.edges, self.nanflow)

    @property
    def numbins(self):
        return len(self.edges) - 1

    def __getitem__(self, where):
        if where == ():
            return self
        if not isinstance(where, tuple):
            where = (where,)
        head, tail = where[0], where[1:]

        if adl.util.isint(head, 0, self.numbins - 1):
            return self.values[head][tail]
        elif head == -adl.util.inf or adl.util.isint(head, None, -1):
            return self.underflow[tail]
        elif head == adl.util.inf or adl.util.isint(head, self.numbins, None):
            return self.overflow[tail]
        elif adl.util.isnan(head):
            return self.nanflow[tail]
        elif head == "underflow":
            return self.underflow[tail]
        elif head == "overflow":
            return self.overflow[tail]
        elif head == "nanflow":
            return self.nanflow[tail]
        else:
            raise IndexError("improper index for {0}: {1}".format(type(self).__name__, repr(head)))

    def fill(self, symboltable, weight=1):
        x = calculate(self.expression, symboltable)
        if not adl.util.isnum(x):
            raise adl.error.ADLTypeError("expression returned a non-number: {0}".format(x), self.expression)

        if x < self.edges[0]:
            self.underflow.fill(symboltable, weight)
        elif x >= self.edges[-1]:
            self.overflow.fill(symboltable, weight)
        elif adl.util.isnan(x):
            self.nanflow.fill(symboltable, weight)
        else:
            for i in range(self.numbins):
                if self.edges[i] <= x < self.edges[i + 1]:
                    self.values[i].fill(symboltable, weight)
                    break

class Namespace(object):
    def __init__(self):
        self.values = {}

    def __getitem__(self, where):
        if where == ():
            return self
        if not isinstance(where, tuple):
            where = (where,)
        head, tail = where[0], where[1:]
        return self.values[head][tail]

    def __setitem__(self, where, what):
        self.values[where] = what

    def __contains__(self, where):
        return where in self.values

class Run(object):
    builtins = {}

    def __init__(self, code):
        if isinstance(code, str):
            self.ast = adl.parser.parse(code)
        else:
            self.ast = adl.parser.parse(code.read())
        self.clear()

    def clear(self):
        self.aggregation = Namespace()
        initialize(self.ast, (), self.aggregation)

    def __iter__(self, source=None, **data):
        if not isinstance(self.ast.statements[-1], Expression):
            raise adl.error.ADLTypeError("this ADL file/string ends with a {0}, not an expression; cannot iterate".format(type(self.ast).__name__))
        for i in range(min(len(x) for x in data.values())):
            yield self(source=source, **{n: x[i] for n, x in data.items()})

    def __call__(self, source=None, **data):
        if len(data) == 0:
            return {}

        try:
            lengths = [len(x) for x in data.values()]
            assert all(x == lengths[0] for x in lengths)
        except (TypeError, AssertionError):
            return self.single(source=source, **data)
        
        out = None
        for i in range(lengths[0]):
            single = self.single(source=source, **{n: x[i] for n, x in data.items()})
            if out is None:
                out = {n: [x] for n, x in single.items()}
            else:
                for n, x in single.items():
                    out[n].append(x)
        return out

    def single(self, source=None, **data):
        symboltable = SymbolTable.root(self.builtins, data)
        for statement in self.ast.statements:
            handle(statement, symboltable, source, self.aggregation)
        return symboltable.symbols

    def __getitem__(self, where):
        return self.aggregation[where]
