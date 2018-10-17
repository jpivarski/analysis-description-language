import ply.yacc

import adl.syntaxtree
import adl.tokenize
import adl.error

class ADLParser(object):
    tokens = adl.tokenize.ADLLexer.tokens

    def pos(self, p, n):
        lo, hi = p.lexspan(n)
        lolineno = hilineno = len(p.lexer.linepos)
        while p.lexer.linepos[lolineno - 1] > lo:
            lolineno -= 1
        while p.lexer.linepos[hilineno - 1] > hi:
            hilineno -= 1
        return {"source": p.lexer.lexdata,
                "lexspan": p.lexspan(n),
                "lineno": lolineno,
                "col_offset": lo - p.lexer.linepos[lolineno - 1],
                "lineno2": hilineno,
                "col_offset2": hi - p.lexer.linepos[hilineno - 1]}

    def span(self, p1, p2):
        p1 = p1.leftmost()
        p2 = p2.rightmost()
        return {"source": p1.source,
                "lexspan": (p1.lexspan[0], p2.lexspan[1]),
                "lineno": p1.lineno,
                "col_offset": p1.col_offset,
                "lineno2": p2.lineno,
                "col_offset2": p2.col_offset}

    def p_body_expression(self, p):
        "body : expression"
        #                1
        p[0] = [p[1]]

    def p_body_assignment_single(self, p):
        "body : assignment"
        #                1
        p[0] = [p[1]]

    def p_body_assignment_extend(self, p):
        "body : assignment body"
        #                1    2
        if "\n" in p[1].source[p[1].rightmost().lexspan[1]:p[2][0].leftmost().lexspan[0]]:
            p[0] = [p[1]] + p[2]
        else:
            raise adl.error.ADLSyntaxError("missing semicolon or newline", p[1].source, p[2][0].leftmost().lineno, p[2][0].leftmost().col_offset)

    def p_body_assignment_extend_semi(self, p):
        "body : assignment SEMICOLON body"
        #                1         2    3
        p[0] = [p[1]] + p[3]

    def p_assignment(self, p):
        "assignment : IDENTIFIER COLONEQ expression"
        #                      1       2          3
        p[0] = adl.syntaxtree.Assign(p[1], p[3], **self.pos(p, 2))

    def p_assignment_call_expression(self, p):
        "assignment : call COLONEQ expression"
        #                1       2          3
        p[0] = adl.syntaxtree.Assign(p[1], p[3], **self.pos(p, 2))

    def p_assignment_call_body(self, p):
        "assignment : call COLONEQ OPENCURLY body CLOSECURLY"
        #                1       2         3    4          5
        p[0] = adl.syntaxtree.Assign(p[1], p[4], **self.pos(p, 2))

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
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Or(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_logicaland(self, p):
        "logicaland : logicalnot"
        #                      1
        p[0] = p[1]

    def p_logicaland_(self, p):
        "logicaland : logicalnot AND logicalnot"
        #                      1   2          3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_logicalnot(self, p):
        "logicalnot : compare"
        #                   1
        p[0] = p[1]

    def p_logicalnot_(self, p):
        "logicalnot : NOT compare"
        #               1       2
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Not(**self.pos(p, 1)), [p[2]], **self.pos(p, 1))

    def p_compare(self, p):
        "compare : arith"
        #              1
        p[0] = p[1]

    def p_compare_isequal(self, p):
        "compare : arith EQEQUAL arith"
        #              1       2     3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.IsEqual(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_compare_isequal_chain(self, p):    # optional: for chained x == y == z
        "compare : compare EQEQUAL arith"
        #                1       2     3
        pair = [p[1], adl.syntaxtree.Call(adl.syntaxtree.IsEqual(**self.pos(p, 2)), [p[1].arguments[1], p[3]], **self.pos(p, 2))]
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**self.span(pair[0], pair[1])), pair, **self.span(pair[0], pair[1]))
               
    def p_compare_notequal(self, p):
        "compare : arith NOTEQUAL arith"
        #              1        2     3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.NotEqual(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_compare_notequal_chain(self, p):    # optional: for chained x != y != z
        "compare : compare NOTEQUAL arith"
        #                1        2     3
        pair = [p[1], adl.syntaxtree.Call(adl.syntaxtree.NotEqual(**self.pos(p, 2)), [p[1].arguments[1], p[3]], **self.pos(pos, 2))]
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**self.span(pair[0], pair[1])), pair, **self.span(pair[0], pair[1]))

    def p_arith(self, p):
        "arith : term"
        #           1
        p[0] = p[1]

    def p_arith_plus(self, p):
        "arith : term PLUS term"
        #           1    2    3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Plus(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_arith_minus(self, p):
        "arith : term MINUS term"
        #           1     2    3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Minus(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_term(self, p):
        "term : factor"
        #            1
        p[0] = p[1]

    def p_term_factor_times(self, p):
        "term : factor TIMES factor"
        #            1     2      3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Times(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_term_factor_div(self, p):
        "term : factor DIV factor"
        #            1   2      3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Div(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_term_factor_mod(self, p):
        "term : factor MOD factor"
        #            1   2      3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Mod(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p2, ))

    def p_factor(self, p):
        "factor : power"
        #             1
        p[0] = p[1]

    def p_factor_unaryplus(self, p):
        "factor : PLUS power"
        #            1     2
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.UnaryPlus(**self.pos(p, 1)), [p[2]])

    def p_factor_unaryminus(self, p):
        "factor : MINUS power"
        #             1     2
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.UnaryMinus(**self.pos(p, 1)), [p[2]])

    def p_power(self, p):
        "power : trailer"
        #              1
        p[0] = p[1]

    def p_power_trailer(self, p):
        "power : trailer POWER trailer"
        #              1     2       3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Power(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_trailer_atom(self, p):
        "trailer : atom"
        #             1
        p[0] = p[1]

    def p_trailer_attribute(self, p):
        "trailer : trailer DOT IDENTIFIER"
        #                1   2          3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Attribute(**self.pos(p, 2)), [p[1], adl.syntaxtree.Identifier(p[3])], **self.pos(p, 2))

    def p_trailer_subscript(self, p):
        "trailer : trailer OPENBRACKET trailer CLOSEBRACKET"
        #                1           2       3            4
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Subscript(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_trailer_call(self, p):
        "trailer : call"
        #             1
        p[0] = p[1]

    def p_call_arglist(self, p):
        "call : trailer OPENPAREN arglist CLOSEPAREN"
        #             1         2       3          4
        p[0] = adl.syntaxtree.Call(p[1], p[3], **self.pos(p, 2))

    def p_call_arglist_empty(self, p):
        "call : trailer OPENPAREN CLOSEPAREN"
        #             1         2          3
        p[0] = adl.syntaxtree.Call(p[1], [], **self.pos(p, 2))

    def p_atom_parens(self, p):
        "atom : OPENPAREN atom CLOSEPAREN"
        #               1    2          3
        p[0] = p[2]

    def p_atom_literal_multilinestring(self, p):
        "atom : MULTILINESTRING"
        #                     1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p, 1))

    def p_atom_literal_string(self, p):
        "atom : STRING"
        #            1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p, 1))

    def p_atom_literal_floatnumber(self, p):
        "atom : FLOAT_NUMBER"
        #                  1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p, 1))

    def p_atom_literal_decnumber(self, p):
        "atom : DEC_NUMBER"
        #                1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p, 1))

    def p_atom_identifier(self, p):
        "atom : IDENTIFIER"
        #                1
        p[0] = adl.syntaxtree.Identifier(p[1], **self.pos(p, 1))

    def p_arglist_single(self, p):
        "arglist : expression"
        #                   1
        p[0] = [p[1]]

    def p_arglist_extend(self, p):
        "arglist : expression COMMA arglist"
        #                   1     2       3
        p[0] = [p[1]] + p[3]

    def p_arglist_extra_comma(self, p):    # optional: for trailing commas f(x, y,)
        "arglist : expression COMMA"
        #                   1     2
        p[0] = [p[1]]

    def p_error(self, p):
        raise adl.error.ADLSyntaxError("illegal syntax", p.lexer.lexdata, len(p.lexer.linepos), p.lexpos - p.lexer.linepos[-1])

    def build(self, **kwargs):
        self.parser = ply.yacc.yacc(module=self, **kwargs)

def parse(source):
    parser = ADLParser()
    lexer = adl.tokenize.ADLLexer()

    parser.build(write_tables=False)  # write_tables=True, tabmodule="parsertable", errorlog=ply.yacc.NullLogger())
    lexer.build()

    return parser.parser.parse(source, lexer=lexer.lexer, tracking=True)
