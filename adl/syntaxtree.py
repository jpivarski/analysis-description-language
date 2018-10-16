import adl.util

class AST(object):
    def __init__(self, source=None, lineno=None, col_offset=None):
        self.source = source
        self.lineno = lineno
        self.col_offset = col_offset

class LeftRight(AST):
    def __init__(self, left, right, source=None, lineno=None, col_offset=None):
        super(LeftRight, self).__init__(source=source, lineno=lineno, col_offset=col_offset)
        self.left = left
        self.right = right

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.left), repr(self.right))

class Right(AST):
    def __init__(self, right, source=None, lineno=None, col_offset=None):
        super(Right, self).__init__(source=source, lineno=lineno, col_offset=col_offset)
        self.right = right

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.right))

class Logical(AST): pass
class Comparison(AST): pass
class Arithmetic(AST): pass
class Additive(Arithmetic): pass
class Multiplicative(Arithmetic): pass
class UnaryArithmetic(Arithmetic): pass

class Or(Logical, LeftRight): pass
class And(Logical, LeftRight): pass
class Not(Logical, Right): pass
class IsEqual(Comparison, LeftRight): pass
class IsNotEqual(Comparison, LeftRight): pass
class Plus(Additive, LeftRight): pass
class Minus(Additive, LeftRight): pass
class Times(Multiplicative, LeftRight): pass
class Div(Multiplicative, LeftRight): pass
class UnaryPlus(UnaryArithmetic, Right): pass
class UnaryMinus(UnaryArithmetic, Right): pass
class Power(Arithmetic, LeftRight): pass

class Literal(AST):
    def __init__(self, value, source=None, lineno=None, col_offset=None):
        super(Literal, self).__init__(source=source, lineno=lineno, col_offset=col_offset)
        self.value = value

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.value))

class Identifier(AST):
    def __init__(self, name, source=None, lineno=None, col_offset=None):
        super(Identifier, self).__init__(source=source, lineno=lineno, col_offset=col_offset)
        self.name = name

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.name))

class Call(AST):
    def __init__(self, function, arguments, source=None, lineno=None, col_offset=None):
        super(Call, self).__init__(source=source, lineno=lineno, col_offset=col_offset)
        self.function = function
        self.arguments = arguments

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.function), repr(self.arguments))

class Assign(AST):
    def __init__(self, target, expr, source=None, lineno=None, col_offset=None):
        super(Assign, self).__init__(source=source, lineno=lineno, col_offset=col_offset)
        self.target = target
        self.expr = expr
