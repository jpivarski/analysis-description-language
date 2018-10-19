#!/usr/bin/env python

import adl.error

class AST(object):
    def __init__(self, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        self.code = code
        self.lexspan = lexspan
        self.lineno = lineno
        self.col_offset = col_offset
        self.lineno2 = lineno2
        self.col_offset2 = col_offset2

    def children(self):
        return []

    def leftmost(self):
        return self

    def rightmost(self):
        return self
    
    def walk(self, topdown=True):
        yield self

class LeftRight(AST):
    def __init__(self, left, right, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(LeftRight, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.left = left
        self.right = right

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.left), repr(self.right))

    def children(self):
        return [self.left, self.right]

    def leftmost(self):
        return self.left.leftmost()

    def rightmost(self):
        return self.right.rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.left.walk(topdown=topdown):
            yield x
        for x in self.right.walk(topdown=topdown):
            yield x
        if not topdown:
            yield self

class Right(AST):
    def __init__(self, right, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Right, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.right = right

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.right))

    def children(self):
        return [self.right]

    def leftmost(self):
        return self.right.leftmost()

    def rightmost(self):
        return self.right.rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.right.walk(topdown=topdown):
            yield x
        if not topdown:
            yield self

class Special(AST):
    def __repr__(self):
        return "{0}()".format(type(self).__name__)

    def __hash__(self):
        return hash(self.__class__)

    def __eq__(self, other):
        return self.__class__ is other.__class__ or self.__class__ is other

    def __ne__(self, other):
        return not self.__eq__(other)

class Attribute(Special): pass
class Subscript(Special): pass
class Or(Special): pass
class And(Special): pass
class Not(Special): pass
class IsEqual(Special): pass
class NotEqual(Special): pass
class LessEq(Special): pass
class Less(Special): pass
class GreaterEq(Special): pass
class Greater(Special): pass
class Plus(Special): pass
class Minus(Special): pass
class Times(Special): pass
class Div(Special): pass
class Mod(Special): pass
class UnaryPlus(Special): pass
class UnaryMinus(Special): pass
class Power(Special): pass

class Expression(AST): pass
class Statement(AST): pass

class Literal(Expression):
    def __init__(self, value, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Literal, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.value = value

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.value))

class Identifier(Expression):
    def __init__(self, name, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Identifier, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.name = name

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.name))

class Call(Expression):
    @classmethod
    def maybe(cls, function, arguments, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        import adl.interpreter
        out = cls(function, arguments, code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        if ((isinstance(function, Special) and function in adl.interpreter.Run.special) or (isinstance(function, Identifier) and function.name in adl.interpreter.Run.builtins)) and all(isinstance(x, Literal) for x in arguments):
            symboltable = adl.interpreter.SymbolTable.root(adl.interpreter.Run.builtins, {})
            return Literal(adl.interpreter.calculate(out, symboltable), code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        else:
            return out

    def __init__(self, function, arguments, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Call, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.function = function
        self.arguments = arguments

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.function), repr(self.arguments))

    def children(self):
        return [self.function] + self.arguments

    def leftmost(self):
        return self.function.leftmost()

    def rightmost(self):
        if len(self.arguments) > 0:
            return self.arguments[-1].rightmost()
        else:
            return self.function.rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.function.walk(topdown=topdown):
            yield x
        for x in self.arguments:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self

class Inline(AST):
    def __init__(self, parameters, body, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Inline, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.parameters = parameters
        self.body = body

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.parameters), repr(self.body))

    def children(self):
        return self.parameters + self.body

    def leftmost(self):
        return self.parameters[0].leftmost()

    def rightmost(self):
        return self.body[-1].rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.parameters:
            for y in x.walk(topdown=topdown):
                yield y
        for x in self.body:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self

class Define(Statement):
    def __init__(self, target, expression, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Define, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.target = target
        self.expression = expression

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.target), repr(self.expression))

    def children(self):
        return [self.target, self.expression]

    def leftmost(self):
        return self.target.leftmost()

    def rightmost(self):
        return self.expression.rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.target.walk(topdown=topdown):
            yield x
        for x in self.expression.walk(topdown=topdown):
            yield x
        if not topdown:
            yield self

class FunctionDefine(Statement):
    def __init__(self, target, body, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(FunctionDefine, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        if not isinstance(target.function, Identifier):
            raise adl.error.ADLSyntaxError("function name in a function definition must be an identifier", code, lineno, col_offset, lineno2=lineno2, col_offset2=col_offset2)
        if not all(isinstance(x, Identifier) for x in target.arguments):
            raise adl.error.ADLSyntaxError("all parameters in a function definition must be identifiers", code, lineno, col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.target = target
        self.body = body
        
    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.target), repr(self.body))

    def children(self):
        return [self.target] + self.body

    def leftmost(self):
        return self.target.leftmost()

    def rightmost(self):
        return self.body[-1].rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.target.walk(topdown=topdown):
            yield x
        for x in self.body:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self

class Axis(AST):
    def __init__(self, binning, expression, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Axis, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.binning = binning
        self.expression = expression

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.binning), repr(self.expression))

    def children(self):
        return [self.binning, self.expression]

    def leftmost(self):
        return self.binning.leftmost()

    def rightmost(self):
        return self.expression.rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.binning.walk(topdown=topdown):
            yield x
        for x in self.expression.walk(topdown=topdown):
            yield x
        if not topdown:
            yield self

class CountStatistic(Special): pass
class SumStatistic(Special): pass
class ProfileStatistic(Special): pass
class FractionStatistic(Special): pass

class Collect(Statement):
    def __init__(self, statistic, name, expression, axes, weight, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Collect, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.statistic = statistic
        self.name = name
        self.expression = expression
        self.axes = axes
        self.weight = weight

    def __repr__(self):
        return "{0}({1}, {2}, {3}, {4}, {5})".format(type(self).__name__, repr(self.statistic), repr(self.name), repr(self.expression), repr(self.axes), repr(self.weight))

    def children(self):
        return [self.statistic, self.name, self.expression] + self.axes + ([self.weight] if self.weight is not None else [])

    def leftmost(self):
        return self.name.leftmost()

    def rightmost(self):
        if self.weight is None and len(self.axes) == 0 and self.expression is None:
            return self.name.rightmost()
        elif self.weight is None and len(self.axes) == 0:
            return self.expression.rightmost()
        elif self.weight is None:
            return self.axes[-1].rightmost()
        else:
            return self.weight.rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.statistic.walk(topdown=topdown):
            yield x
        for x in self.name.walk(topdown=topdown):
            yield x
        if self.expression is not None:
            for x in self.expression.walk(topdown=topdown):
                yield x
        for x in self.axes:
            for y in x.walk(topdown=topdown):
                yield y
        if self.weight is not None:
            for x in self.weight.walk(topdown=topdown):
                yield x
        if not topdown:
            yield self

class For(Statement):
    def __init__(self, loopvars, block, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(For, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.loopvars = loopvars
        self.block = block

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.loopvars), repr(self.block))

    def children(self):
        return self.loopvars + self.block
    
    def leftmost(self):
        return self.loopvars[0].leftmost()

    def rightmost(self):
        return self.block[-1].rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.loopvars:
            for y in x.walk(topdown=topdown):
                yield y
        for x in self.block:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self

class Variation(AST):
    def __init__(self, name, assignments, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Variation, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.name = name
        self.assignments = assignments

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.name), repr(self.assignments))

    def children(self):
        return [self.name] + self.assignments

    def leftmost(self):
        return self.name.leftmost()

    def rightmost(self):
        return self.assignments[-1].rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.name.walk(topdown=topdown):
            yield x
        for x in self.assignments:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self

class Vary(Statement):
    def __init__(self, variations, block, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Vary, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.variations = variations
        self.block = block

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.variations), repr(self.block))

    def children(self):
        return self.variations + self.block
    
    def leftmost(self):
        return self.variations[0].leftmost()

    def rightmost(self):
        return self.block[-1].rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.variations:
            for y in x.walk(topdown=topdown):
                yield y
        for x in self.block:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self

class NamePredicate(AST):
    def __init__(self, name, predicate, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(NamePredicate, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.name = name
        self.predicate = predicate

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.name), repr(self.predicate))

    def children(self):
        return [self.name, self.predicate]

    def leftmost(self):
        return self.name.leftmost()

    def rightmost(self):
        return self.name.rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.name.walk(topdown=topdown):
            yield x
        for x in self.predicate.walk(topdown=topdown):
            yield x
        if not topdown:
            yield self

class Region(Statement):
    def __init__(self, namepredicates, axes, block, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Region, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.namepredicates = namepredicates
        self.axes = axes
        self.block = block

    def __repr__(self):
        return "{0}({1}, {2}, {3})".format(type(self).__name__, repr(self.namepredicates), repr(self.axes), repr(self.block))

    def children(self):
        return self.namepredicates + self.axes + self.block

    def leftmost(self):
        return self.namepredicates[0].leftmost()

    def rightmost(self):
        return self.block[-1].rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.namepredicates:
            for y in x.walk(topdown=topdown):
                yield y
        for x in self.axes:
            for y in x.walk(topdown=topdown):
                yield y
        for x in self.block:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self

class Source(Statement):
    def __init__(self, names, block, inclusive, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Source, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.names = names
        self.block = block
        self.inclusive = inclusive

    def __repr__(self):
        return "{0}({1}, {2}, inclusive={3})".format(type(self).__name__, repr(self.names), repr(self.block), repr(self.inclusive))

    def children(self):
        return self.names + self.block

    def leftmost(self):
        return self.names[0].leftmost()

    def rightmost(self):
        return self.block[-1].rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.names:
            for y in x.walk(topdown=topdown):
                yield y
        for x in self.block:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self

class Suite(AST):
    def __init__(self, block, code=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Suite, self).__init__(code=code, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.block = block

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.block))

    def children(self):
        return list(self.block)

    def leftmost(self):
        return self.block[0].leftmost()

    def rightmost(self):
        return self.block[-1].rightmost()

    def walk(self, topdown=True):
        if topdown:
            yield self
        for x in self.block:
            for y in x.walk(topdown=topdown):
                yield y
        if not topdown:
            yield self
