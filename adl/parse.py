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

    def p_expression_1(self, p):
        "expression : atom"
        #                1
        p[0] = p[1]

    def p_expression_2(self, p):
        "expression : attribute"
        #                     1
        p[0] = p[1]

    def p_expression_3(self, p):
        "expression : subscript"
        #                     1
        p[0] = p[1]

    def p_expression_4(self, p):
        "expression : call"
        #                1
        p[0] = p[1]

    def p_attribute(self, p):
        "attribute : expression DOT IDENTIFIER"
        #               1   2          3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Attribute(**pos), [p[1], adl.syntaxtree.Identifier(p[3])], **pos)

    def p_subscript(self, p):
        "subscript : expression OPENBRACKET expression CLOSEBRACKET"
        #                     1           2          3            4
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Subscript(**pos), [p[1], p[3]], **pos)

    def p_call_1(self, p):
        "call : expression OPENPAREN arglist CLOSEPAREN"
        #                1         2       3          4
        p[0] = adl.syntaxtree.Call(p[1], p[3], **self.pos(p))

    def p_call_2(self, p):
        "call : expression OPENPAREN CLOSEPAREN"
        #                1         2          3
        p[0] = adl.syntaxtree.Call(p[1], [], **self.pos(p))

    def p_arglist_1(self, p):
        "arglist : atom"
        #             1
        p[0] = [p[1]]

    # this one lets you have a trailing COMMA in argument lists
    def p_arglist_2(self, p):
        "arglist : atom COMMA"
        #             1     2
        p[0] = [p[1]]

    def p_arglist_3(self, p):
        "arglist : atom COMMA arglist"
        #             1     2       3
        p[0] = [p[1]] + p[3]

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
