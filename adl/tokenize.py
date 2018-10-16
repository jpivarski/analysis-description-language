import ast
import re

import ply.lex

import adl.util

class ADLLexer(object):
    reserved = {}
    tokens = ["MULTILINESTRING", "STRING", "FLOAT_NUMBER", "DEC_NUMBER", "IDENTIFIER",
              "OR", "AND", "NOT",
              "EQEQUAL", "NOTEQUAL",
              "PLUS", "MINUS", "TIMES", "DIV", "POWER",
              "OPENPAREN", "CLOSEPAREN", "DOT", "COMMA",
              "NEWLINE", "WHITESPACE"]

    def t_MULTILINESTRING(self, t):
        r'(\'\'\'[^\\]*(\\.[^\\]*)*\'\'\'|"""[^\\]*(\\.[^\\]*)*""")'
        t.value = ast.literal_eval(t.value)
        return t

    def t_STRING(self, t):
        r'(\'[^\n\'\\]*(\\.[^\n\'\\]*)*\'|"[^\n"\\]*(\\.[^\n"\\]*)*")'
        t.value = ast.literal_eval(t.value)
        return t

    def t_FLOAT_NUMBER(self, t):
        r"((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)"
        t.value = float(t.value)
        return t

    def t_DEC_NUMBER(self, t):
        r"(0+|[1-9][0-9]*)"
        t.value = int(t.value)
        return t

    def t_IDENTIFIER(self, t):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        t.type = self.reserved.get(t.value, "IDENTIFIER")
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
    t_DOT        = r"\."
    t_COMMA      = r","

    def t_COMMENT(self, t):
        r"\#.*"
        pass

    def t_NEWLINE(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)
        t.lexer.linepos = t.lexer.lexpos

    t_ignore = " \t\f\r"

    def t_error(self, t):
        adl.util.complain(SyntaxError, "illegal character", t.lexer.lexpos, t.lexer)

    def build(self, **kwargs):
        self.lexer = ply.lex.lex(module=self, **kwargs)
        self.lexer.linepos = 0
