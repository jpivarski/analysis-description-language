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

    def p_expression(self, p):
        "expression : logicalor"
        #                     1
        p[0] = p[1]

    def p_logicalor(self, p):
        "logicalor : logicaland"
        #                     1
        p[0] = p[1]

    def p_logicalor_(self, p):
        "logicalor : logicaland OR logicaland"
        #                     1  2          3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Or(**pos), [p[1], p[3]], **pos)

    def p_logicaland(self, p):
        "logicaland : logicalnot"
        #                      1
        p[0] = p[1]

    def p_logicaland_(self, p):
        "logicaland : logicalnot AND logicalnot"
        #                      1   2          3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**pos), [p[1], p[3]], **pos)

    def p_logicalnot(self, p):
        "logicalnot : compare"
        #                   1
        p[0] = p[1]

    def p_logicalnot_(self, p):
        "logicalnot : NOT compare"
        #               1       2
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Not(**pos), [p[2]], **pos)

    def p_compare(self, p):
        "compare : arith"
        #              1
        p[0] = p[1]

    def p_compare_isequal(self, p):
        "compare : arith EQEQUAL arith"
        #              1       2     3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.IsEqual(**pos), [p[1], p[3]], **pos)

    def p_compare_isequal_chain(self, p):    # optional: for chained x == y == z
        "compare : compare EQEQUAL arith"
        #                1       2     3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**pos), [p[1], adl.syntaxtree.Call(adl.syntaxtree.IsEqual(**pos), [p[1].arguments[1], p[3]], **pos)], **pos)
               
    def p_compare_notequal(self, p):
        "compare : arith NOTEQUAL arith"
        #              1        2     3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.NotEqual(**pos), [p[1], p[3]], **pos)

    def p_compare_notequal_chain(self, p):    # optional: for chained x != y != z
        "compare : compare NOTEQUAL arith"
        #                1        2     3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**pos), [p[1], adl.syntaxtree.Call(adl.syntaxtree.NotEqual(**pos), [p[1].arguments[1], p[3]], **pos)], **pos)

    def p_arith(self, p):
        "arith : term"
        #           1
        p[0] = p[1]

    def p_arith_plus(self, p):
        "arith : term PLUS term"
        #           1    2    3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Plus(**pos), [p[1], p[3]], **pos)

    def p_arith_minus(self, p):
        "arith : term MINUS term"
        #           1     2    3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Minus(**pos), [p[1], p[3]], **pos)

    def p_term(self, p):
        "term : factor"
        #            1
        p[0] = p[1]

    def p_term_factor_times(self, p):
        "term : factor TIMES factor"
        #            1     2      3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Times(**pos), [p[1], p[3]], **pos)

    def p_term_factor_div(self, p):
        "term : factor DIV factor"
        #            1   2      3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Div(**pos), [p[1], p[3]], **pos)

    def p_term_factor_mod(self, p):
        "term : factor MOD factor"
        #            1   2      3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Mod(**pos), [p[1], p[3]], **pos)

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
        "power : trailer"
        #              1
        p[0] = p[1]

    def p_power_trailer(self, p):
        "power : trailer POWER trailer"
        #              1     2       3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Power(**pos), [p[1], p[3]], **pos)

    def p_trailer_atom(self, p):
        "trailer : atom"
        #             1
        p[0] = p[1]

    def p_trailer_attribute(self, p):
        "trailer : trailer DOT IDENTIFIER"
        #                1   2          3
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Attribute(**pos), [p[1], adl.syntaxtree.Identifier(p[3])], **pos)

    def p_trailer_subscript(self, p):
        "trailer : trailer OPENBRACKET trailer CLOSEBRACKET"
        #                1           2       3            4
        pos = self.pos(p)
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Subscript(**pos), [p[1], p[3]], **pos)

    def p_trailer_arglist(self, p):
        "trailer : trailer OPENPAREN arglist CLOSEPAREN"
        #                1         2       3          4
        p[0] = adl.syntaxtree.Call(p[1], p[3], **self.pos(p))

    def p_trailer_arglist_empty(self, p):
        "trailer : trailer OPENPAREN CLOSEPAREN"
        #                1         2          3
        p[0] = adl.syntaxtree.Call(p[1], [], **self.pos(p))

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

    def p_arglist_singleton(self, p):
        "arglist : expression"
        #                   1
        p[0] = [p[1]]

    def p_arglist_extension(self, p):
        "arglist : expression COMMA arglist"
        #                   1     2       3
        p[0] = [p[1]] + p[3]

    def p_arglist_extra_comma(self, p):    # optional: for trailing commas f(x, y,)
        "arglist : expression COMMA"
        #                   1     2
        p[0] = [p[1]]

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
