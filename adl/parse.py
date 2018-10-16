import ply.yacc

import adl.syntaxtree
import adl.tokenize

class ADLParser(object):
    tokens = adl.tokenize.ADLLexer.tokens

    def p_atom_identifier(self, p):
        "atom : IDENTIFIER"
        #                1
        p[0] = adl.syntaxtree.Identifier(p[1])

    def build(self, **kwargs):
        self.parser = ply.yacc.yacc(module=self, **kwargs)

parser = ADLParser()
lexer = adl.tokenize.ADLLexer()

parser.build(write_tables=True, tabmodule="parsertable", errorlog=ply.yacc.NullLogger())
lexer.build()

print(parser.parser.parse("&hello", lexer=lexer.lexer))
