class AST(object):
    def __init__(self, source=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        self.source = source
        self.lexspan = lexspan
        self.lineno = lineno
        self.col_offset = col_offset
        self.lineno2 = lineno2
        self.col_offset2 = col_offset2

    def leftmost(self):
        return self

    def rightmost(self):
        return self

class LeftRight(AST):
    def __init__(self, left, right, source=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(LeftRight, self).__init__(source=source, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.left = left
        self.right = right

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.left), repr(self.right))

    def leftmost(self):
        return self.left.leftmost()

    def rightmost(self):
        return self.right.rightmost()

class Right(AST):
    def __init__(self, right, source=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Right, self).__init__(source=source, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.right = right

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.right))

    def leftmost(self):
        return self.right.leftmost()

    def rightmost(self):
        return self.right.rightmost()

class Special(AST):
    def __repr__(self):
        return "{0}()".format(type(self).__name__)

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

class Literal(AST):
    def __init__(self, value, source=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Literal, self).__init__(source=source, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.value = value

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.value))

class Identifier(AST):
    def __init__(self, name, source=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Identifier, self).__init__(source=source, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.name = name

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, repr(self.name))

class Call(AST):
    def __init__(self, function, arguments, source=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Call, self).__init__(source=source, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.function = function
        self.arguments = arguments

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.function), repr(self.arguments))

    def leftmost(self):
        return self.function.leftmost()

    def rightmost(self):
        if len(self.arguments) > 0:
            return self.arguments[-1].rightmost()
        else:
            return self.function.rightmost()

class Assign(AST):
    def __init__(self, target, expression, source=None, lexspan=None, lineno=None, col_offset=None, lineno2=None, col_offset2=None):
        super(Assign, self).__init__(source=source, lexspan=lexspan, lineno=lineno, col_offset=col_offset, lineno2=lineno2, col_offset2=col_offset2)
        self.target = target
        self.expression = expression

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, repr(self.target), repr(self.expression))

    def leftmost(self):
        return self.target.leftmost()

    def rightmost(self):
        return self.expression.rightmost()
