import ply.yacc

import adl.syntaxtree
import adl.tokenizer
import adl.error

class ADLParser(object):
    tokens = adl.tokenizer.ADLLexer.tokens

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

    def require_separator(self, left, right):
        if "\n" not in left.source[left.rightmost().lexspan[1]:right.leftmost().lexspan[0]]:
            raise adl.error.ADLSyntaxError("missing semicolon or newline", left.source, right.leftmost().lineno, right.leftmost().col_offset)

    def p_suite_block(self, p):
        "suite : block"
        #            1
        p[0] = p[1]

    def p_suite_body(self, p):
        "suite : body"
        #           1
        p[0] = p[1]

    def p_vary(self, p):
        "vary : VARY variations OPENCURLY block CLOSECURLY"
        #          1          2         3     4          5
        p[0] = adl.syntaxtree.Vary(p[2], p[4], **self.pos(p, 1))

    def p_variations(self, p):
        "variations : namedassignments"
        #                            1
        p[0] = [p[1]]

    def p_variations_extend(self, p):
        "variations : namedassignments variations"
        #                            1          2
        p[0] = [p[1]] + p[2]

    def p_namedassignments(self, p):
        "namedassignments : string COLON assignment"
        #                        1     2          3
        p[0] = adl.syntaxtree.NamedAssignments(p[1], [p[3]], **self.pos(p, 2))

    def p_namedassignments_extend(self, p):
        "namedassignments : namedassignments assignment"
        #                                  1          2
        self.require_separator(p[1].assignments[-1], p[2])
        p[1].assignments.append(p[2])
        p[0] = p[1]
        
    def p_namedassignments_extend_semi(self, p):
        "namedassignments : namedassignments SEMICOLON assignment"
        #                                  1         2          3
        p[1].assignments.append(p[3])
        p[0] = p[1]

    def p_block_vary(self, p):
        "block : vary"
        #           1
        p[0] = [p[1]]

    def p_block_extend_vary(self, p):
        "block : vary block"
        #           1     2
        p[0] = [p[1]] + p[2]

    def p_block_count(self, p):
        "block : count"
        #            1
        p[0] = [p[1]]

    def p_block_extend_count(self, p):
        "block : count block"
        #            1     2
        self.require_separator(p[1], p[2][0])
        p[0] = [p[1]] + p[2]

    def p_block_extend_count_semi(self, p):
        "block : count SEMICOLON block"
        #            1         2     3
        p[0] = [p[1]] + p[3]

    def p_block_profile(self, p):
        "block : profile"
        #              1
        p[0] = [p[1]]

    def p_block_extend_profile(self, p):
        "block : profile block"
        #              1     2
        self.require_separator(p[1], p[2][0])
        p[0] = [p[1]] + p[2]

    def p_block_extend_profile_semi(self, p):
        "block : profile SEMICOLON block"
        #              1         2     3
        p[0] = [p[1]] + p[3]

    def p_block_extend_assignment(self, p):
        "block : assignment block"
        #                 1     2
        self.require_separator(p[1], p[2][0])
        p[0] = [p[1]] + p[2]

    def p_block_extend_assignment_semi(self, p):
        "block : assignment SEMICOLON block"
        #                 1         2     3
        p[0] = [p[1]] + p[3]

    def p_body_expression(self, p):
        "body : expression"
        #                1
        p[0] = [p[1]]

    def p_body_extend_count(self, p):
        "body : count body"
        #           1    2
        self.require_separator(p[1], p[2][0])
        p[0] = [p[1]] + p[2]

    def p_body_extend_count_semi(self, p):
        "body : count SEMICOLON body"
        #           1         2    3
        p[0] = [p[1]] + p[3]

    def p_body_extend_profile(self, p):
        "body : profile body"
        #             1    2
        self.require_separator(p[1], p[2][0])
        p[0] = [p[1]] + p[2]

    def p_body_extend_profile_semi(self, p):
        "body : profile SEMICOLON body"
        #             1         2    3
        p[0] = [p[1]] + p[3]

    def p_body_extend_assignment(self, p):
        "body : assignment body"
        #                1    2
        self.require_separator(p[1], p[2][0])
        p[0] = [p[1]] + p[2]

    def p_body_extend_assignment_semi(self, p):
        "body : assignment SEMICOLON body"
        #                1         2    3
        p[0] = [p[1]] + p[3]

    def p_count(self, p):
        "count : COUNT string"
        #            1      2
        p[0] = adl.syntaxtree.Count(p[2], [], None, **self.pos(p, 1))

    def p_count_weight(self, p):
        "count : COUNT string WEIGHT expression"
        #            1      2      3          4
        p[0] = adl.syntaxtree.Count(p[2], [], p[4], **self.pos(p, 1))

    def p_count_axis(self, p):
        "count : COUNT string axis"
        #            1      2    3
        p[0] = adl.syntaxtree.Count(p[2], p[3], None, **self.pos(p, 1))

    def p_count_axisweight(self, p):
        "count : COUNT string axisweight"
        #            1      2          3
        axis, weight = p[3]
        p[0] = adl.syntaxtree.Count(p[2], axis, weight, **self.pos(p, 1))

    def p_profile(self, p):
        "profile : PROFILE string expression"
        #                1      2          3
        p[0] = adl.syntaxtree.Profile(p[2], p[3], [], None, **self.pos(p, 1))

    def p_profile_weight(self, p):
        "profile : PROFILE string expression WEIGHT expression"
        #                1      2          3      4          5
        p[0] = adl.syntaxtree.Profile(p[2], p[3], [], p[5], **self.pos(p, 1))

    def p_profile_axis(self, p):
        "profile : PROFILE string expression axis"
        #                1      2          3    4
        p[0] = adl.syntaxtree.Profile(p[2], p[3], p[4], None, **self.pos(p, 1))

    def p_profile_axisweight(self, p):
        "profile : PROFILE string expression axisweight"
        #                1      2          3          4
        axis, weight = p[4]
        p[0] = adl.syntaxtree.Profile(p[2], p[3], axis, weight, **self.pos(p, 1))

    def p_axisweight(self, p):
        "axisweight : axis WEIGHT expression"
        #                1      2          3
        p[0] = p[1], p[3]
        
    def p_axis_single(self, p):
        "axis : call LEFTARROW expression"
        #          1         2          3
        p[0] = [adl.syntaxtree.Axis(p[1], p[3], **self.pos(p, 2))]

    def p_axis_extend(self, p):
        "axis : axis call LEFTARROW expression"
        #          1    2         3          4
        p[0] = p[1] + [adl.syntaxtree.Axis(p[2], p[4], **self.pos(p, 3))]

    def p_assignment(self, p):
        "assignment : IDENTIFIER COLONEQ expression"
        #                      1       2          3
        p[0] = adl.syntaxtree.Assign(adl.syntaxtree.Identifier(p[1], **self.pos(p, 1)), p[3], **self.pos(p, 2))

    def p_assignment_call_expression(self, p):
        "assignment : call COLONEQ expression"
        #                1       2          3
        p[0] = adl.syntaxtree.Assign(p[1], p[3], **self.pos(p, 2))

    def p_assignment_call_body(self, p):
        "assignment : call COLONEQ OPENCURLY body CLOSECURLY"
        #                1       2         3    4          5
        p[0] = adl.syntaxtree.Assign(p[1], p[4], **self.pos(p, 2))

    def p_inline_identifier(self, p):
        "inline : IDENTIFIER RIGHTARROW expression"
        #                  1          2          3
        p[0] = adl.syntaxtree.Inline([adl.syntaxtree.Identifier(p[1], **self.pos(p, 1))], p[3], **self.pos(p, 2))

    def p_inline_identifier_(self, p):
        "inline : OPENPAREN IDENTIFIER CLOSEPAREN RIGHTARROW expression"
        #                 1          2          3          4          5
        p[0] = adl.syntaxtree.Inline([adl.syntaxtree.Identifier(p[2], **self.pos(p, 2))], p[5], **self.pos(p, 4))

    def p_inline_arglist(self, p):
        "inline : OPENPAREN arglist CLOSEPAREN RIGHTARROW expression"
        #                 1       2          3          4          5
        p[0] = adl.syntaxtree.Inline(p[2], p[5], **self.pos(p, 4))

    def p_expression(self, p):
        "expression : andchain"
        #                    1
        p[0] = p[1]

    def p_expression_(self, p):
        "expression : andchain OR andchain"
        #                    1  2        3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Or(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_andchain(self, p):
        "andchain : notchain"
        #                  1
        p[0] = p[1]

    def p_andchain_(self, p):
        "andchain : notchain AND notchain"
        #                  1   2        3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_notchain(self, p):
        "notchain : compare"
        #                 1
        p[0] = p[1]

    def p_notchain_(self, p):
        "notchain : NOT compare"
        #             1       2
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
        pair = [p[1], adl.syntaxtree.Call(adl.syntaxtree.NotEqual(**self.pos(p, 2)), [p[1].arguments[1], p[3]], **self.pos(p, 2))]
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**self.span(pair[0], pair[1])), pair, **self.span(pair[0], pair[1]))

    def p_compare_lesseq(self, p):
        "compare : arith LESSEQ arith"
        #              1      2     3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.LessEq(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_compare_lesseq_chain(self, p):    # optional: for chained x <= y <= z
        "compare : compare LESSEQ arith"
        #                1      2     3
        pair = [p[1], adl.syntaxtree.Call(adl.syntaxtree.LessEq(**self.pos(p, 2)), [p[1].arguments[1], p[3]], **self.pos(p, 2))]
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**self.span(pair[0], pair[1])), pair, **self.span(pair[0], pair[1]))

    def p_compare_less(self, p):
        "compare : arith LESS arith"
        #              1    2     3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Less(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_compare_less_chain(self, p):    # optional: for chained x < y < z
        "compare : compare LESS arith"
        #                1    2     3
        pair = [p[1], adl.syntaxtree.Call(adl.syntaxtree.Less(**self.pos(p, 2)), [p[1].arguments[1], p[3]], **self.pos(p, 2))]
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**self.span(pair[0], pair[1])), pair, **self.span(pair[0], pair[1]))

    def p_compare_greatereq(self, p):
        "compare : arith GREATEREQ arith"
        #              1         2     3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.GreaterEq(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_compare_greatereq_chain(self, p):    # optional: for chained x >= y >= z
        "compare : compare GREATEREQ arith"
        #                1         2     3
        pair = [p[1], adl.syntaxtree.Call(adl.syntaxtree.GreaterEq(**self.pos(p, 2)), [p[1].arguments[1], p[3]], **self.pos(p, 2))]
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.And(**self.span(pair[0], pair[1])), pair, **self.span(pair[0], pair[1]))

    def p_compare_greater(self, p):
        "compare : arith GREATER arith"
        #              1       2     3
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Greater(**self.pos(p, 2)), [p[1], p[3]], **self.pos(p, 2))

    def p_compare_greater_chain(self, p):    # optional: for chained x > y > z
        "compare : compare GREATER arith"
        #                1       2     3
        pair = [p[1], adl.syntaxtree.Call(adl.syntaxtree.Greater(**self.pos(p, 2)), [p[1].arguments[1], p[3]], **self.pos(p, 2))]
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
        "trailer : trailer OPENBRACKET arglist CLOSEBRACKET"
        #                1           2       3            4
        p[0] = adl.syntaxtree.Call(adl.syntaxtree.Subscript(**self.pos(p, 2)), [p[1]] + p[3], **self.pos(p, 2))

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

    def p_atom_literal_string(self, p):
        "atom : string"
        #            1
        p[0] = p[1]

    def p_string_literal_multilinestring(self, p):
        "string : MULTILINESTRING"
        #                       1
        p[0] = adl.syntaxtree.Literal(p[1], **self.pos(p, 1))

    def p_string_literal_string(self, p):
        "string : STRING"
        #              1
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

    def p_arg_expression(self, p):
        "arg : expression"
        #               1
        p[0] = p[1]

    def p_arg_inline(self, p):
        "arg : inline"
        #           1
        p[0] = p[1]

    def p_arglist_single(self, p):
        "arglist : arg"
        #            1
        p[0] = [p[1]]

    def p_arglist_extend(self, p):
        "arglist : arg COMMA arglist"
        #            1     2       3
        p[0] = [p[1]] + p[3]

    def p_arglist_extra_comma(self, p):    # optional: for trailing commas f(x, y,)
        "arglist : arg COMMA"
        #            1     2
        p[0] = [p[1]]

    def p_error(self, p):
        if p is None:
            raise adl.error.ADLError("an ADL source file/string must be an expression or a set of region/vary blocks (either may be preceded by assignments)")
        else:
            raise adl.error.ADLSyntaxError("illegal syntax", p.lexer.lexdata, len(p.lexer.linepos), p.lexpos - p.lexer.linepos[-1])

    def build(self, **kwargs):
        self.parser = ply.yacc.yacc(module=self, **kwargs)

def parse(source):
    parser = ADLParser()
    lexer = adl.tokenizer.ADLLexer()

    parser.build(write_tables=False)  # write_tables=True, tabmodule="parsertable", errorlog=ply.yacc.NullLogger())
    lexer.build()

    return parser.parser.parse(source, lexer=lexer.lexer, tracking=True)
