import ast
import re

import ply.lex

reserved = {}
tokens = ["MULTILINESTRING", "STRING", "FLOAT_NUMBER", "DEC_NUMBER", "IDENTIFIER",
          "OR", "AND", "NOT", "EQEQUAL", "NOTEQUAL", "PLUS", "MINUS", "TIMES", "DIV", "POWER", "OPENPAREN", "CLOSEPAREN",
          "NEWLINE", "WHITESPACE"]

def t_MULTILINESTRING(t):
    r'(\'\'\'[^\\]*(\\.[^\\]*)*\'\'\'|"""[^\\]*(\\.[^\\]*)*""")'
    t.value = ast.literal_eval(t.value)
    return t

def t_STRING(t):
    r'(\'[^\n\'\\]*(\\.[^\n\'\\]*)*\'|"[^\n"\\]*(\\.[^\n"\\]*)*")'
    t.value = ast.literal_eval(t.value)
    return t

def t_FLOAT_NUMBER(t):
    r"((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)"
    t.value = float(t.value)
    return t

def t_DEC_NUMBER(t):
    r"(0+|[1-9][0-9]*)"
    t.value = int(t.value)
    return t

def t_IDENTIFIER(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "IDENTIFIER")
    t.value = t.value
    return t

t_OR         = r"or"
t_AND        = r"and"
t_NOT        = r"not"
t_EQEQUAL    = r"=="
t_NOTEQUAL   = r"!="
t_PLUS       = r"\+"
t_MINUS      = r"-"
t_TIMES      = r"\*"
t_DIV        = r"/"
t_POWER      = r"\*\*"
t_OPENPAREN  = r"\("
t_CLOSEPAREN = r"\)"

def t_COMMENT(t):
    r"\#.*"
    pass

def t_NEWLINE(t):
    r"\n+"
    t.lexer.lineno += len(t.value)
    return t

def t_WHITESPACE(t):
    r"[ \t\f\r]+"
    return t

def t_error(t):
    message = "Line {0}: illegal character".format(t.lexer.lineno)
    quoted = t.lexer.source.split("\n")[t.lexer.lineno - 1]
    arrow = "-" * (t.lexer.lexpos - t.lexer.linepos + 4) + "^"
    raise SyntaxError(message + "\n    " + quoted + "\n" + arrow)

def tokenize(source):
    lexer = ply.lex.lex()
    lexer.source = source
    lexer.input(source)

    lexer.linepos = 0
    for token in lexer:
        if not token:
            break
        if token.type == "NEWLINE":
            lexer.linepos = lexer.lexpos

        token.col_offset = lexer.lexpos - lexer.linepos
        if token.type == "WHITESPACE":
            pass
        else:
            yield token
