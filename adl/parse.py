import ply.yacc

import adl.syntaxtree
import adl.tokenize
import adl.util

class ADLParser(object):
    tokens = adl.tokenize.ADLLexer.tokens

    def pos(self, p):
        return {"source": p.lexer.lexdata,
                "lineno": p.lexer.lineno,
                "col_offset": p.lexer.lexpos - p.lexer.linepos}

    def p_atom_identifier(self, p):
        "atom : IDENTIFIER"
        #                1
        p[0] = adl.syntaxtree.Identifier(p[1], **self.pos(p))

    def p_error(self, p):
        adl.util.complain(SyntaxError, "illegal syntax", p.lexer.lexdata, p.lexer.lineno, p.lexpos - p.lexer.linepos)

    def build(self, **kwargs):
        self.parser = ply.yacc.yacc(module=self, **kwargs)

def parse(source):
    parser = ADLParser()
    lexer = adl.tokenize.ADLLexer()

    parser.build(write_tables=True, tabmodule="parsertable", errorlog=ply.yacc.NullLogger())
    lexer.build()

    return parser.parser.parse(source, lexer=lexer.lexer)
