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

    def p_factor(self, p):
        "factor : power"
        #             1
        p[0] = p[1]

    def p_factor_unaryplus(self, p):
        "factor : PLUS power"
        #            1     2
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.UnaryPlus(**pos), [p[2]])

    def p_factor_unaryminus(self, p):
        "factor : MINUS power"
        #             1     2
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.UnaryMinus(**pos), [p[2]])

    def p_power(self, p):
        "power : trailed"
        #              1
        p[0] = p[1]

    def p_power_trailed(self, p):
        "power : trailed POWER trailed"
        #              1     2       3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Power(**pos), [p[1], p[3]], **pos)

    def p_trailed_1(self, p):
        "trailed : atom"
        #             1
        p[0] = p[1]

    def p_trailed_2(self, p):
        "trailed : attribute"
        #                  1
        p[0] = p[1]

    def p_trailed_3(self, p):
        "trailed : subscript"
        #                  1
        p[0] = p[1]

    def p_trailed_4(self, p):
        "trailed : call"
        #             1
        p[0] = p[1]

    def p_attribute(self, p):
        "attribute : trailed DOT IDENTIFIER"
        #                  1   2          3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Attribute(**pos), [p[1], adl.syntaxtree.Identifier(p[3])], **pos)

    def p_subscript(self, p):
        "subscript : trailed OPENBRACKET trailed CLOSEBRACKET"
        #                  1           2          3            4
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Subscript(**pos), [p[1], p[3]], **pos)

    def p_call_arglist(self, p):
        "call : trailed OPENPAREN arglist CLOSEPAREN"
        #             1         2       3          4
        p[0] = adl.syntaxtree.Call(p[1], p[3], **self.pos(p))

    def p_call_empty(self, p):
        "call : trailed OPENPAREN CLOSEPAREN"
        #             1         2          3
        p[0] = adl.syntaxtree.Call(p[1], [], **self.pos(p))

    def p_arglist_singleton(self, p):
        "arglist : atom"
        #             1
        p[0] = [p[1]]

    def p_arglist_extension(self, p):
        "arglist : atom COMMA arglist"
        #             1     2       3
        p[0] = [p[1]] + p[3]

    # def p_arglist_3(self, p):
    #     "arglist : atom COMMA"   # optional: allows trailing commas in f(x, y,)
    #     #             1     2
    #     p[0] = [p[1]]

    def p_atom_parens(self, p):
        "atom : OPENPAREN atom CLOSEPAREN"
        #               1    2          3
        p[0] = p[2]

    def p_atom_literal_multilinestring(self, p):
        "atom : MULTILINESTRING"
        #                     1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p))

    def p_atom_literal_string(self, p):
        "atom : STRING"
        #            1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p))

    def p_atom_literal_floatnumber(self, p):
        "atom : FLOAT_NUMBER"
        #                  1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p))

    def p_atom_literal_decnumber(self, p):
        "atom : DEC_NUMBER"
        #                1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p))

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

    parser.build(write_tables=False)  # write_tables=True, tabmodule="parsertable", errorlog=ply.yacc.NullLogger())
    lexer.build()

    return parser.parser.parse(source, lexer=lexer.lexer)
