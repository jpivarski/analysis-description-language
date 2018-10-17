import ast
import re

import ply.lex

import adl.error

class ADLLexer(object):
    reserved = {"and": "AND",
                "or": "OR",
                "not": "NOT",
                "count": "COUNT",
                "profile": "PROFILE",
                "weight": "WEIGHT"}

    tokens = ["MULTILINESTRING", "STRING", "FLOAT_NUMBER", "DEC_NUMBER", "IDENTIFIER",
              "COLONEQ", "LEFTARROW", "RIGHTARROW",
              "OR", "AND", "NOT", "COUNT", "PROFILE", "WEIGHT",
              "EQEQUAL", "NOTEQUAL", "LESSEQ", "LESS", "GREATEREQ", "GREATER",
              "PLUS", "MINUS", "TIMES", "DIV", "MOD", "POWER",
              "OPENPAREN", "CLOSEPAREN", "OPENBRACKET", "CLOSEBRACKET", "OPENCURLY", "CLOSECURLY", "DOT", "COMMA",
              "SEMICOLON"]

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

    t_COLONEQ      = r":="
    t_LEFTARROW    = r"<-"
    t_RIGHTARROW   = r"->"
    t_OR           = r"or"
    t_AND          = r"and"
    t_NOT          = r"not"
    t_EQEQUAL      = r"=="
    t_NOTEQUAL     = r"!="
    t_LESSEQ       = r"<="
    t_LESS         = r"<"
    t_GREATEREQ    = r">="
    t_GREATER      = r">"
    t_PLUS         = r"\+"
    t_MINUS        = r"-"
    t_TIMES        = r"\*"
    t_DIV          = r"/"
    t_MOD          = r"%"
    t_POWER        = r"\*\*"
    t_OPENPAREN    = r"\("
    t_CLOSEPAREN   = r"\)"
    t_OPENBRACKET  = r"\["
    t_CLOSEBRACKET = r"\]"
    t_OPENCURLY    = r"\{"
    t_CLOSECURLY   = r"\}"
    t_DOT          = r"\."
    t_COMMA        = r","
    t_SEMICOLON    = r";"

    def t_COMMENT(self, t):
        r"\#.*"
        pass

    def t_NEWLINE(self, t):
        r"\n+"
        t.lexer.linepos.extend([t.lexer.lexpos] * len(t.value))

    t_ignore = " \t\f\r"

    def t_error(self, t):
        raise adl.error.ADLSyntaxError("illegal character", t.lexer.lexdata, len(t.lexer.linepos), t.lexer.lexpos - t.lexer.linepos[-1])

    def build(self, **kwargs):
        self.lexer = ply.lex.lex(module=self, **kwargs)
        self.lexer.linepos = [0]
