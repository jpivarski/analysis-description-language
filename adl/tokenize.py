import ast
import re

import ply.lex

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
        return t

    def t_WHITESPACE(self, t):
        r"[ \t\f\r]+"
        return t

    def t_error(self, t):
        message = "Line {0}: illegal character".format(t.lexer.lineno)
        quoted = t.lexer.source.split("\n")[t.lexer.lineno - 1]
        arrow = "-" * (t.lexer.lexpos - t.lexer.linepos + 4) + "^"
        # report the line number, quote the line, and put a cool arrow under it specifying the position
        raise SyntaxError(message + "\n    " + quoted + "\n" + arrow)

    def build(self, **kwargs):
        self.lexer = ply.lex.lex(module=self, **kwargs)
        self.lexer.linepos = 0

# class LexerWithLineNumbers(ply.lex.Lexer):
#     def __iter__(self):
#         self.linepos = 0

#         iterator = super(LexerWithLineNumbers, self).__iter__()
#         while True:
#             token = next(iterator)
#             if not token:
#                 break
#             if token.type == "NEWLINE":
#                 self.linepos = self.lexpos
#             token.col_offset = self.lexpos - self.linepos
#             if token.type != "WHITESPACE" and token.type != "NEWLINE":
#                 yield token
