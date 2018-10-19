#!/usr/bin/env python

import copy
import fnmatch
import math
import numbers

import numpy

import adl.error
import adl.parser
import adl.util
from adl.syntaxtree import *

###################################################### interpretation of the AST

class SymbolTable(object):
    @classmethod
    def root(cls, functions, data):
        fcntable = cls.__new__(cls)
        fcntable.parent = None
        fcntable.symbols = functions
        out = cls(fcntable)
        out.symbols.update(data)
        return out

    def __init__(self, parent):
        self.parent = parent
        self.symbols = {}

    def __getitem__(self, where):
        if where.name in self.symbols:
            return self.symbols[where.name]
        elif self.parent is not None:
            return self.parent[where]
        else:
            raise adl.error.ADLNameError("no symbol named {0} in this scope".format(repr(where.name)), where)

    def __setitem__(self, where, what):
        self.symbols[where.name] = what

    def __contains__(self, where):
        return where.name in self.symbols

    def frozen(self):
        if self.parent is None:
            return self   # don't copy the builtin functions; they don't change
        else:
            out = self.__class__.__new__(self.__class__)
            out.parent = self.parent.frozen()
            out.symbols = dict(self.symbols)
            return out

    def tagfunction(self, where):
        if not hasattr(self, "_functions"):
            self._functions = set()
        self._functions.add(where.name)

    def dropfunctions(self):
        if hasattr(self, "_functions"):
            for n in list(self.symbols):
                if n in self._functions:
                    del self.symbols[n]

def calculate(expression, symboltable):
    if isinstance(expression, Literal):
        return expression.value

    elif isinstance(expression, Identifier):
        return symboltable[expression]

    elif isinstance(expression, Call):
        values = [calculate(x, symboltable) for x in expression.arguments]

        if isinstance(expression.function, Special) and expression.function in Run.special:
            for signature, function in Run.special[expression.function]:
                accept = signature(values, expression)
                try:
                    if accept is True:
                        return function(*values)
                    elif isinstance(accept, Expression):
                        return function(accept, *values)
                except Exception as err:
                    if isinstance(err, adl.error.ADLError):
                        raise
                    else:
                        raise adl.error.ADLRuntimeError("function raised {0}: {1}".format(type(err).__name__, str(err)), expression)

        if isinstance(expression.function, Expression):
            try:
                return calculate(expression.function, symboltable)(*values)
            except Exception as err:
                if isinstance(err, adl.error.ADLError):
                    raise
                else:
                    raise adl.error.ADLRuntimeError("function raised {0}: {1}".format(type(err).__name__, str(err)), expression)
        
    elif isinstance(expression, Inline):
        parameters = [x.name for x in expression.parameters]
        frozen = symboltable.frozen()

        def function(*values):
            if len(parameters) != len(values):
                raise adl.error.ADLTypeError("wrong number of arguments: expecting {0}, encountered {1}".format(len(parameters), len(values)), expression)
            subtable = SymbolTable(frozen)
            for param, val in zip(parameters, values):
                subtable[Identifier(param)] = val
            for stmt in expression.body[:-1]:
                handle(stmt, source, subtable, aggregation)
            return calculate(expression.body[-1], subtable)

        return function

    else:
        raise adl.error.ADLInternalError("cannot calculate a {0}; it is not an expression".format(type(expression).__name__), expression)

def handle(statement, source, symboltable, aggregation):
    if isinstance(statement, Define):
        symboltable[statement.target] = calculate(statement.expression, symboltable)

    elif isinstance(statement, FunctionDefine):
        parameters = [x.name for x in statement.target.arguments]
        frozen = symboltable.frozen()

        def function(*values):
            if len(parameters) != len(values):
                raise TypeError("wrong number of arguments: expecting {0}, encountered {1}".format(len(parameters), len(values)))
            subtable = SymbolTable(frozen)
            for param, val in zip(parameters, values):
                subtable[Identifier(param)] = val
            for stmt in statement.body[:-1]:
                handle(stmt, source, subtable, aggregation)
            return calculate(statement.body[-1], subtable)

        symboltable[statement.target.function] = function
        symboltable.tagfunction(statement.target.function)

    elif isinstance(statement, Collect):
        if statement.weight is None:
            weight = 1
        else:
            weight = calculate(statement.weight, symboltable)
        aggregation[statement.name.value].fill(symboltable, weight)

    elif isinstance(statement, For):
        loopvars = []
        lengths = []
        for loopvar in statement.loopvars:
            loopvars.append((loopvar.target, calculate(loopvar.expression, symboltable)))
            try:
                iter(loopvars[-1][1])
                lengths.append(len(loopvars[-1][1]))
            except TypeError:
                raise adl.errors.ADLTypeError("loop variable {0} must be iterable with a known length".format(repr(loopvar.target.name)), loopvar)

        if not all(x == lengths[0] for x in lengths):
            raise adl.errors.ADLTypeError("loop variables in the same for loop must all have the same length", statement)

        for i in range(lengths[0]):
            subtable = SymbolTable(symboltable)
            for target, value in loopvars:
                subtable[target] = value[i]
            for x in statement.block:
                handle(x, source, subtable, aggregation)

    elif isinstance(statement, Vary):
        for variation in statement.variations:
            subtable = SymbolTable(symboltable)
            subaggregation = aggregation[variation.name.value]
            for x in variation.assignments:
                subtable[x.target] = calculate(x.expression, symboltable)
            for x in statement.block:
                handle(x, source, subtable, subaggregation)

    elif isinstance(statement, Region):
        if statement.predicate is None:
            accept = True
        else:
            accept = calculate(statement.predicate, symboltable)
            if accept is not True and accept is not False:
                raise adl.error.ADLTypeError("predicate returned a non-boolean: {0}".format(accept), statement.predicate)

        if accept:
            aggregation = aggregation[statement.name.value]
            for i in range(len(statement.axes)):
                aggregation = aggregation.which(symboltable)
            symboltable = SymbolTable(symboltable)
            for x in statement.block:
                handle(x, source, symboltable, aggregation)

    elif isinstance(statement, Source):
        if source is None:
            accept = True
        else:
            accept = any(fnmatch.fnmatchcase(source, x.value) for x in statement.names)
            if not statement.inclusive:
                accept = not accept
        if accept:
            for x in statement.block:
                handle(x, source, symboltable, aggregation)

    else:
        raise adl.error.ADLInternalError("cannot handle a {0}; it is not a statement".format(type(statement).__name__), statement)

def initialize(statement, name, aggregation):
    if isinstance(statement, Suite):
        for x in statement.block:
            initialize(x, name, aggregation)

    elif isinstance(statement, Source):
        for x in statement.block:
            initialize(x, name, aggregation)

    elif isinstance(statement, Region):
        adl.util.check_name(statement, aggregation)
        name = name + (statement.name.value,)
        storage = Namespace(name)
        for x in statement.block:
            initialize(x, name, storage)

        for axis in statement.axes[::-1]:
            storage = Binning.binning(name, axis.binning, axis.expression, storage)
        aggregation[statement.name.value] = storage

    elif isinstance(statement, For):
        for x in statement.block:
            initialize(x, name, aggregation)

    elif isinstance(statement, Vary):
        storage = Namespace(name)
        for x in statement.block:
            initialize(x, name, storage)

        for variation in statement.variations:
            adl.util.check_name(variation, aggregation)
            aggregation[variation.name.value] = storage.zeros_like(name + (variation.name.value,))

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
            storage = Fraction(name, statement.expression)
        else:
            raise adl.error.ADLInternalError("{0} is not a collectable statistic".format(type(statement.statistic).__name__), statement.statistic)

        for axis in statement.axes[::-1]:
            storage = Binning.binning(name, axis.binning, axis.expression, storage)

        aggregation[statement.name.value] = storage

    elif isinstance(statement, Statement):
        pass

    else:
        raise adl.error.ADLInternalError("cannot initialize {0}; it is not a statement".format(type(statement).__name__), statement)

###################################################### statistical aggregation

class Namespace(object):
    def __init__(self, name):
        self.name = name
        self.values = {}

    def __repr__(self):
        return "<Namespace at 0x{0:012x}>".format(id(self))

    def zeros_like(self, name):
        out = Namespace(name)
        out.values.update({n: x.zeros_like(name + (n,)) for n, x in self.values.items()})
        return out

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

    def value(self, indeterminate=0.0):
        return self.sumw

    def error2(self, method="normal", sigmas=1, indeterminate=0.0):
        if method == "normal":
            return sigmas**2 * self.sumw2
        elif method == "poisson":
            raise NotImplementedError
        else:
            raise ValueError("unrecognized method: {0}".format(repr(method)))

    def error(self, method="normal", sigmas=1, indeterminate=0.0):
        return math.sqrt(self.error2(method=method, sigmas=sigmas, indeterminate=indeterminate))

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

    def value(self, indeterminate=0.0):
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

    def value(self, indeterminate=0.0):
        if self.sumw == 0:
            return indeterminate
        else:
            return self.sumwx / self.sumw

    def error2(self, method="normal", sigmas=1, indeterminate=0.0):
        if method == "normal":
            if self.sumw2 == 0:
                return indeterminate
            else:
                effectivecount = self.sumw**2 / self.sumw2
                return sigmas**2 * (self.sumwx2 / self.sumw - self.value()**2) / effectivecount
        else:
            raise ValueError("unrecognized method: {0}".format(repr(method)))

    def error(self, method="normal", sigmas=1, indeterminate=0.0):
        return math.sqrt(self.error2(method=method, sigmas=sigmas, indeterminate=indeterminate))

    def __iter__(self):
        yield self.value()
        yield self.error()

class Fraction(Storage):
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression
        self.numerw = 0.0
        self.denomw = 0.0

    def zeros_like(self, name):
        return Fraction(name, self.expression)

    def __repr__(self):
        return "<Fraction {0}: {1} +- {2}>".format(", ".join(repr(x) for x in self.name), self.value(), self.error())

    def fill(self, symboltable, weight):
        x = calculate(self.expression, symboltable)
        if x is not True and x is not False:
            raise adl.error.ADLTypeError("predicate returned a non-boolean: {0}".format(x), self.expression)
        if x:
            self.numerw += weight
        self.denomw += weight

    def value(self, indeterminate=0.0):
        if self.denomw == 0:
            return indeterminate
        else:
            return self.numerw / self.denomw

    def error2(self, method="normal", sigmas=1, indeterminate=0.0):
        if self.denomw == 0:
            return indeterminate
        p = self.numerw / self.denomw
        if not 0 <= p <= 1:
            return indeterminate

        if method == "normal":
            return sigmas**2 * math.sqrt(p*(1.0 - p) / self.denomw)

        elif method == "clopper-pearson":
            raise NotImplementedError

        elif method == "wilson":
            return (p + 0.5*sigmas**2/self.denomw + sigmas*math.sqrt(p*(1.0 - p)/self.denomw + 0.25*sigmas**2/self.denomw**2)) / (1.0 + sigmas**2/self.denomw)

        elif method == "agresti-coull":
            raise NotImplementedError

        elif method == "feldman-cousins":
            raise NotImplementedError

        elif method == "jeffrey":
            raise NotImplementedError

        elif method == "bayesian-uniform":
            raise NotImplementedError

        else:
            raise ValueError("unrecognized method: {0}".format(repr(method)))

    def error(self, method="normal", sigmas=1, indeterminate=0.0):
        return math.sqrt(self.error2(method=method, sigmas=sigmas, indeterminate=indeterminate))

class Binning(object):
    @staticmethod
    def binning(name, call, expression, storage):
        if isinstance(call, Call) and call.function.name == "regular":
            adl.util.check_args(call, 3, 3)
            if not isinstance(call.arguments[0], Literal) or not adl.util.isint(call.arguments[0].value, 1):
                raise adl.error.ADLTypeError("numbins must be a literal positive integer", call.arguments[0])
            if not isinstance(call.arguments[1], Literal) or not adl.util.isnum(call.arguments[1].value):
                raise adl.error.ADLTypeError("low must be a literal number", call.arguments[1])
            if not isinstance(call.arguments[2], Literal) or not adl.util.isnum(call.arguments[2].value):
                raise adl.error.ADLTypeError("high must be a literal number", call.arguments[2])
            return RegularBinning(name, expression, call.arguments[0].value, call.arguments[1].value, call.arguments[2].value, storage)

        elif isinstance(call, Call) and call.function.name == "variable":
            adl.util.check_args(call, 1, None)
            for x in call.arguments:
                if not isinstance(x, Literal) or not adl.util.isnum(x.value):
                    raise adl.error.ADLTypeError("edges must be literal numbers", x)
            return VariableBinning(name, expression, [x.value for x in call.arguments], storage)

        else:
            raise ADLTypeError("not a binning", call)

    def __repr__(self):
        return "<{0} {1} at 0x{2:012x}>".format(type(self).__name__, ", ".join(repr(x) for x in self.name), id(self))

    def fill(self, symboltable, weight):
        self.which(symboltable).fill(symboltable, weight)

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

    def which(self, symboltable):
        x = calculate(self.expression, symboltable)
        if not adl.util.isnum(x):
            raise adl.error.ADLTypeError("expression returned a non-number: {0}".format(x), self.expression)

        index = self.numbins * (x - self.low) / (self.high - self.low)
        if index < 0:
            return self.underflow
        elif index >= self.numbins:
            return self.overflow
        elif adl.util.isnan(index):
            return self.nanflow
        else:
            return self.values[int(math.trunc(index))]

    def plot(self):
        import matplotlib.pyplot

        if isinstance(self.nanflow, Binning):
            raise NotImplementedError

        else:
            binwidth = (self.high - self.low) / self.numbins
            centers = [self.low + (i + 0.5)*binwidth for i in range(self.numbins)]
            heights = [float(self.values[i]) for i in range(self.numbins)]
            fig, ax = matplotlib.pyplot.subplots()
            ax.bar(centers, heights, width=binwidth)
            ax.set_title(", ".join(repr(x) for x in self.name))
            return ax

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

    def which(self, symboltable):
        x = calculate(self.expression, symboltable)
        if not adl.util.isnum(x):
            raise adl.error.ADLTypeError("expression returned a non-number: {0}".format(x), self.expression)

        if x < self.edges[0]:
            return self.underflow
        elif x >= self.edges[-1]:
            return self.overflow
        elif adl.util.isnan(x):
            return self.nanflow
        else:
            for i in range(self.numbins):
                if self.edges[i] <= x < self.edges[i + 1]:
                    return self.values[i]

    def plot(self):
        import matplotlib.pyplot

        if isinstance(self.nanflow, Binning):
            raise NotImplementedError

        else:
            centers = [0.5*(self.edges[i + 1] + self.edges[i]) for i in range(self.numbins)]
            binwidths = [self.edges[i + 1] - self.edges[i] for i in range(self.numbins)]
            heights = [float(self.values[i]) for i in range(self.numbins)]
            fig, ax = matplotlib.pyplot.subplots()
            ax.bar(centers, heights, width=binwidths)
            ax.set_title(", ".join(repr(x) for x in self.name))
            return ax

###################################################### executable ADL document

class Run(object):
    builtins = {}
    special = {Attribute:  [],
               Subscript:  [],
               Or:         [],
               And:        [],
               Not:        [],
               IsEqual:    [],
               NotEqual:   [],
               LessEq:     [],
               Less:       [],
               GreaterEq:  [],
               Greater:    [],
               Plus:       [],
               Minus:      [],
               Times:      [],
               Div:        [],
               Mod:        [],
               UnaryPlus:  [],
               UnaryMinus: [],
               Power:      []}

    def __init__(self, code):
        if isinstance(code, str):
            self.ast = adl.parser.parse(code)
        else:
            self.ast = adl.parser.parse(code.read())
        self.clear()

    def clear(self):
        self.aggregation = Namespace(())
        initialize(self.ast, (), self.aggregation)

    def __iter__(self, source=None, **data):
        functions = {n: x for n, x in data.items() if callable(x)}
        justdata = {n: x for n, x in data.items() if not callable(x)}

        if len(justdata) == 0:
            yield {}

        else:
            try:
                lengths = [len(x) for x in justdata.values()]
                assert all(x == lengths[0] for x in lengths)

            except (TypeError, AssertionError):
                yield self.single(source=source, **data)

            else:
                for i in range(lengths[0]):
                    onedata = {n: x[i] for n, x in justdata.items()}
                    for n, x in functions.items():
                        onedata[n] = x
                    yield self.single(source=source, **onedata)

    def __call__(self, source=None, **data):
        functions = {n: x for n, x in data.items() if callable(x)}
        justdata = {n: x for n, x in data.items() if not callable(x)}

        if len(justdata) == 0:
            return {}

        else:
            try:
                assert all(not isinstance(x, dict) for x in justdata.values())
                lengths = [len(x) for x in justdata.values()]
                assert all(x == lengths[0] for x in lengths)

            except (TypeError, AssertionError):
                return self.single(source=source, **data)

            else:
                out = None
                for i in range(lengths[0]):
                    onedata = {n: x[i] for n, x in justdata.items()}
                    for n, x in functions.items():
                        onedata[n] = x
                    single = self.single(source=source, **onedata)
                    if out is None:
                        out = {n: [x] for n, x in single.items()}
                    else:
                        for n, x in single.items():
                            out[n].append(x)
                return out

    def single(self, source=None, **data):
        symboltable = SymbolTable.root(self.builtins, data)
        for statement in self.ast.block:
            handle(statement, source, symboltable, self.aggregation)
        symboltable.dropfunctions()
        return symboltable.symbols

    def __getitem__(self, where):
        return self.aggregation[where]

###################################################### library for the interpreter

def typerequire(*types):
    def out(values, expression):
        if len(expression.arguments) != len(types):
            raise adl.error.ADLTypeError("expected {0} arguments, found {1}".format(len(types), len(expression.arguments)))
        for val, arg, tpe in zip(values, expression.arguments, types):
            if tpe is bool and val is not True and val is not False:
                raise adl.error.ADLTypeError("value is not a boolean: {0}".format(repr(val), arg), expression)
            elif tpe is float and not isinstance(val, (numbers.Real, numpy.integer, numpy.floating)):
                raise adl.error.ADLTypeError("value is not a number: {0}".format(repr(val), arg), expression)
            elif tpe is int and not isinstance(val, (numbers.Integral, numpy.integer)):
                raise adl.error.ADLTypeError("value is not an integer: {0}".format(repr(val), arg), expression)
        return True
    return out

def typetest(*types):
    def out(values, expression):
        if len(expression.arguments) != len(types):
            return False
        for val, arg, tpe in zip(values, expression.arguments, types):
            if tpe is bool and value is not True and value is not False:
                return False
            elif tpe is float and not isinstance(x, (numbers.Real, numpy.integer, numpy.floating)):
                return False
            elif tpe is int and not isinstance(x, (numbers.Integral, numpy.integer)):
                return False
        return True
    return out

def has(data, name):
    if hasattr(data, name):
        return True
    try:
        return name in data
    except TypeError:
        return False

def get(data, name):
    try:
        return getattr(data, name)
    except AttributeError:
        return data[name]

###################################################### lists

def islist(values, expression):
    if len(values) == 0:
        return False
    try:
        iter(values[0]), len(values[0])
    except TypeError:
        return False
    else:
        if isinstance(values[0], dict):
            return False
        else:
            return expression

def listfunctions(expression, data, name):
    if name == "map":
        return lambda inline: [inline(x) for x in data]

    elif name == "filter":
        return lambda inline: [x for x in data if inline(x)]

    elif name == "flatten":
        return lambda: [item for sublist in data for item in sublist]

    elif name == "cross":
        return lambda other: [x + (y,) if isinstance(x, tuple) else (x, y) for x in data for y in other]

    elif name == "pairs":
        return lambda: [(data[i], data[j]) for i in range(len(data)) for j in range(i, len(data))]

    elif name == "distincts":
        return lambda: [(data[i], data[j]) for i in range(len(data)) for j in range(i + 1, len(data))]

    elif name == "min":
        if len(data) == 0:
            return lambda: float("inf")
        else:
            return lambda: min(data)

    elif name == "max":
        if len(data) == 0:
            return lambda: float("-inf")
        else:
            return lambda: max(data)

    elif name == "minby":
        if len(data) == 0:
            return lambda f: []
        else:
            return lambda f: [min(data, key=f)]

    elif name == "maxby":
        if len(data) == 0:
            return lambda f: []
        else:
            return lambda f: [max(data, key=f)]

    else:
        raise adl.error.ADLTypeError("lists do not have a method named {0}".format(repr(name)), expression)

Run.special[Attribute].append((islist, listfunctions))

###################################################### Lorentz vectors

def is_pxpypz(values, expression):
    if len(values) == 0:
        return False
    elif not has(values[0], "px") or not has(values[0], "py") or not has(values[0], "pz") or not (has(values[0], "energy") or has(values[0], "mass")):
        return False
    else:
        return expression

def is_ptetaphi(values, expression):
    if len(values) == 0:
        return False
    elif not has(values[0], "pt") or not has(values[0], "eta") or not has(values[0], "phi") or not (has(values[0], "energy") or has(values[0], "mass")):
        return False
    else:
        return expression

def mass2energy(data):
    out = copy.copy(data)
    mass = get(out, "mass")
    if has(out, "px") and has(out, "py") and has(out, "pz"):
        px = get(out, "px")
        py = get(out, "py")
        pz = get(out, "pz")
    elif has(out, "pt") and has(out, "eta") and has(out, "phi"):
        pt = get(out, "pt")
        eta = get(out, "eta")
        phi = get(out, "phi")
        px = pt * math.cos(phi)
        py = pt * math.sin(phi)
        pz = pt * math.sinh(eta)
    else:
        assert False
    energy = math.sqrt(px**2 + py**2 + pz**2 + mass**2*(1 if mass >= 0 else -1))
    try:
        out.energy = energy
    except:
        out["energy"] = energy
    return out

def cylindrical2cartesian(data):
    out = copy.copy(data)
    pt = get(out, "pt")
    eta = get(out, "eta")
    phi = get(out, "phi")
    px = pt * math.cos(phi)
    py = pt * math.sin(phi)
    pz = pt * math.sinh(eta)
    try:
        out.px = px
        out.py = py
        out.pz = pz
    except:
        out["px"] = px
        out["py"] = py
        out["pz"] = pz
    return out

def cartesian2cylindrical(data):
    out = copy.copy(data)
    px = get(out, "px")
    py = get(out, "py")
    pz = get(out, "pz")
    theta = math.atan2(math.sqrt(px**2 + py**2), pz)
    pt = math.sqrt(px**2 + py**2)
    eta = -math.log((1.0 - math.cos(theta)) / (1.0 + math.cos(theta)))/2.0
    phi = math.atan2(py, px)
    try:
        out.pt = pt
        out.eta = eta
        out.phi = phi
    except:
        out["pt"] = pt
        out["eta"] = eta
        out["phi"] = phi
    return out

def pxpy2phi(data):
    out = copy.copy(data)
    px = get(out, "px")
    py = get(out, "py")
    phi = math.atan2(py, px)
    try:
        out.phi = phi
    except:
        out["phi"] = phi
    return out

def ensure_pxpypzE(data, expression):
    if has(data, "px") and has(data, "py") and has(data, "pz") and has(data, "energy"):
        return data
    elif has(data, "px") and has(data, "py") and has(data, "pz") and has(data, "mass"):
        return mass2energy(data)
    elif has(data, "pt") and has(data, "eta") and has(data, "phi") and has(data, "energy"):
        return cylindrical2cartesian(data)
    elif has(data, "pt") and has(data, "eta") and has(data, "phi") and has(data, "energy"):
        return mass2energy(cylindrical2cartesian(data))
    else:
        raise adl.error.ADLTypeError("value is not a Lorentz vector: {0}".format(data), expression)

def ensure_ptetaphi(data, expression):
    if has(data, "px") and has(data, "py") and has(data, "pz"):
        return cartesian2cylindrical(data)
    elif has(data, "pt") and has(data, "eta") and has(data, "phi"):
        return data
    else:
        raise adl.error.ADLTypeError("value is not a Lorentz vector: {0}".format(data), expression)

def ensure_phi(data, expression):
    if has(data, "px") and has(data, "py"):
        return pxpy2phi(data)
    elif has(data, "phi"):
        return data
    else:
        raise adl.error.ADLTypeError("value is not a Lorentz vector: {0}".format(data), expression)

def pxpypz_members(expression, data, name):
    px = get(data, "px")
    py = get(data, "py")
    pz = get(data, "pz")

    def energy():
        if has(data, "energy"):
            return get(data, "energy")
        else:
            return mass2energy(data)

    def phi():
        return math.atan2(py, px)

    def eta():
        return -math.log((1.0 - math.cos(theta())) / (1.0 + math.cos(theta())))/2.0

    def mt():
        mt2 = energy()**2 - pz**2
        if mt2 >= 0:
            return math.sqrt(mt2)
        else:
            return -math.sqrt(mt2)

    def theta():
        return math.atan2(math.sqrt(px**2 + py**2), pz)

    def beta():
        return math.sqrt(px**2 + py**2 + pz**2) / energy()

    def gamma():
        b = beta()
        if -1 < b < 1:
            return (1.0 - b**2)**(-0.5)
        else:
            return float("inf")

    def dot(other):
        other = ensure_pxpypzE(other, expression.arguments[1])
        return energy()*get(other, "energy") - px*get(other, "px") - py*get(other, "py") - pz*get(other, "pz")

    def delta_phi(other):
        other = ensure_phi(other, expression.arguments[1])
        return (phi() - get(other, "phi") + math.pi) % (2*math.pi) - math.pi

    def delta_r(other):
        other = ensure_ptetaphi(other, expression.arguments[1])
        return math.sqrt(delta_phi(other)**2 + (eta() - get(other, "eta"))**2)

    if   name == "px":        return px
    elif name == "py":        return py
    elif name == "pz":        return pz
    elif name == "energy":    return energy()
    elif name == "eta":       return eta()
    elif name == "phi":       return phi()
    elif name == "mass":      return get(data, "mass") if has(data, "mass") else math.sqrt(energy()**2 - px**2 - py**2 - pz**2)
    elif name == "p":         return math.sqrt(px**2 + py**2 + pz**2)
    elif name == "pt":        return math.sqrt(px**2 + py**2)
    elif name == "Et":        return energy() * math.sqrt(px**2 + py**2) / math.sqrt(px**2 + py**2 + pz**2)
    elif name == "mt":        return mt()
    elif name == "theta":     return theta()
    elif name == "rapidity":  return math.log((energy() + pz) / (energy() - pz)) / 2.0
    elif name == "beta":      return beta()
    elif name == "gamma":     return gamma()
    elif name == "dot":       return dot
    elif name == "delta_phi": return delta_phi
    elif name == "delta_r":   return delta_r
    else:
        raise adl.error.ADLTypeError("Lorentz vectors do not have a member named {0}".format(repr(name)), expression)

def ptetaphi_members(expression, data, name):
    pt = get(data, "pt")
    eta = get(data, "eta")
    phi = get(data, "phi")

    def energy():
        if has(data, "energy"):
            return get(data, "energy")
        else:
            return mass2energy(data)

    def mt():
        mt2 = energy() - (pt * math.sinh(eta))**2
        if mt2 >= 0:
            return math.sqrt(mt2)
        else:
            return -math.sqrt(mt2)

    def rapidity():
        E = energy()
        pz = pt * math.sinh(eta)
        return math.log((E + pz) / (E - pz)) / 2.0

    def beta():
        return pt * math.cosh(eta) / energy()   # FIXME: not checked

    def gamma():
        b = beta()
        if -1 < b < 1:
            return (1.0 - b**2)**(-0.5)
        else:
            return float("inf")

    def dot(other):
        self = ensure_pxpypzE(data, expression.arguments[0])
        other = ensure_pxpypzE(other, expression.arguments[1])
        return get(self, "energy")*get(other, "energy") - get(self, "px")*get(other, "px") - get(self, "py")*get(other, "py") - get(self, "pz")*get(other, "pz")

    def delta_phi(other):
        other = ensure_phi(other, expression.arguments[1])
        return (phi - get(other, "phi") + math.pi) % (2*math.pi) - math.pi

    def delta_r(other):
        other = ensure_ptetaphi(other, expression.arguments[1])
        return math.sqrt(delta_phi(other)**2 + (eta - get(other, "eta"))**2)

    if   name == "px":        return pt * math.cos(phi)
    elif name == "py":        return pt * math.sin(phi)
    elif name == "pz":        return pt * math.sinh(eta)
    elif name == "energy":    return energy()
    elif name == "eta":       return eta
    elif name == "phi":       return phi
    elif name == "mass":      return get(data, "mass") if has(data, "mass") else math.sqrt(energy()**2 - px**2 - py**2 - pz**2)
    elif name == "p":         return pt * math.cosh(eta)              # FIXME: not checked
    elif name == "pt":        return pt
    elif name == "Et":        return energy() / math.cosh(eta)        # FIXME: not checked
    elif name == "mt":        return mt()
    elif name == "theta":     return math.atan2(1.0, math.sinh(eta))  # FIXME: not checked
    elif name == "rapidity":  return rapidity()
    elif name == "beta":      return beta()
    elif name == "gamma":     return gamma()
    elif name == "dot":       return dot
    elif name == "delta_phi": return delta_phi
    elif name == "delta_r":   return delta_r
    else:
        raise adl.error.ADLTypeError("Lorentz vectors do not have a member named {0}".format(repr(name)), expression)

Run.special[Attribute].append((is_pxpypz, pxpypz_members))
Run.special[Attribute].append((is_ptetaphi, ptetaphi_members))

###################################################### syntactical functions

def dodot(obj, attr):
    try:
        return obj[attr]
    except:
        return getattr(obj, attr)

Run.special[Attribute] .append((lambda values, expression: True,             dodot))
Run.special[Subscript] .append((lambda values, expression: len(values) == 2, lambda x, i: x[i]))
Run.special[Subscript] .append((lambda values, expression: True,             lambda x, *args: x[args]))
Run.special[Or]        .append((typerequire(bool, bool),                     lambda x, y: x or y))
Run.special[And]       .append((typerequire(bool, bool),                     lambda x, y: x and y))
Run.special[Not]       .append((typerequire(bool),                           lambda x: not x))
Run.special[IsEqual]   .append((lambda values, expression: True,             lambda x, y: x == y))
Run.special[NotEqual]  .append((lambda values, expression: True,             lambda x, y: x != y))
Run.special[LessEq]    .append((typerequire(float, float),                   lambda x, y: x <= y))
Run.special[Less]      .append((typerequire(float, float),                   lambda x, y: x < y))
Run.special[GreaterEq] .append((typerequire(float, float),                   lambda x, y: x >= y))
Run.special[Greater]   .append((typerequire(float, float),                   lambda x, y: x > y))
Run.special[Plus]      .append((typerequire(float, float),                   lambda x, y: x + y))
Run.special[Minus]     .append((typerequire(float, float),                   lambda x, y: x - y))
Run.special[Times]     .append((typerequire(float, float),                   lambda x, y: x * y))
Run.special[Div]       .append((typerequire(float, float),                   lambda x, y: float(x) / float(y)))
Run.special[Mod]       .append((typerequire(float, float),                   lambda x, y: x % y))
Run.special[UnaryPlus] .append((typerequire(float),                          lambda x: +x))
Run.special[UnaryMinus].append((typerequire(float),                          lambda x: -x))
Run.special[Power]     .append((typerequire(float, float),                   lambda x, y: x**y))

###################################################### builtin mathematical functions

# constants (just pi; `e` is too easily confused with user-defined variables, and it's `exp(1)`)
Run.builtins["pi"] = math.pi

# basic math
Run.builtins["sqrt"] = math.sqrt
Run.builtins["exp"] = math.exp
Run.builtins["exp2"] = lambda x: float(numpy.exp2(float(x)))
Run.builtins["log"] = math.log
Run.builtins["log2"] = math.log2
Run.builtins["log10"] = math.log10
Run.builtins["sin"] = math.sin
Run.builtins["cos"] = math.cos
Run.builtins["tan"] = math.tan
Run.builtins["arcsin"] = math.asin
Run.builtins["arccos"] = math.acos
Run.builtins["arctan"] = math.atan
Run.builtins["arctan2"] = math.atan2
Run.builtins["hypot"] = math.hypot
Run.builtins["rad2deg"] = lambda x: x * 180.0 / math.pi
Run.builtins["deg2rad"] = lambda x: x * math.pi / 180.0
Run.builtins["sinh"] = math.sinh
Run.builtins["cosh"] = math.cosh
Run.builtins["tanh"] = math.tanh
Run.builtins["arcsinh"] = math.asinh
Run.builtins["arccosh"] = math.acosh
Run.builtins["arctanh"] = math.atanh

# special functions
Run.builtins["erf"] = math.erf
Run.builtins["erfc"] = math.erfc
Run.builtins["factorial"] = math.factorial
Run.builtins["gamma"] = math.gamma
Run.builtins["lgamma"] = math.lgamma

# rounding and discontinuous
Run.builtins["abs"] = abs
Run.builtins["round"] = round
Run.builtins["floor"] = math.floor
Run.builtins["ceil"] = math.ceil
Run.builtins["sign"] = lambda x: -1 if x < 0 else 1 if x > 0 else 0
Run.builtins["heaviside"] = lambda x, middle=0.5: 0 if x < 0 else 1 if x > 0 else middle

# fast calculations of common combinations
Run.builtins["expm1"] = math.expm1
Run.builtins["log1p"] = math.log1p
Run.builtins["ldexp"] = math.ldexp
Run.builtins["logaddexp"] = lambda x, y: float(numpy.logaddexp(x, y))
Run.builtins["logaddexp2"] = lambda x, y: float(numpy.logaddexp2(x, y))

# number type
Run.builtins["isfinite"] = math.isfinite
Run.builtins["isinf"] = math.isinf
Run.builtins["isnan"] = math.isnan

# bit-level detail
Run.builtins["nextafter"] = lambda x: float(numpy.nextafter(x, numpy.inf))
Run.builtins["nextbefore"] = lambda x: float(numpy.nextafter(x, -numpy.inf))
Run.builtins["nexttoward"] = lambda x, y: float(numpy.nextafter(x, y))
