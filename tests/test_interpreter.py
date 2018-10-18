#!/usr/bin/env python

import math
import unittest

import adl.error
import adl.interpreter

class Test(unittest.TestCase):
    def test_assign(self):
        run = adl.interpreter.Run("y := x")
        assert run(x=[1, 2, 3]) == {"x": [1, 2, 3], "y": [1, 2, 3]}

    def test_count(self):
        run = adl.interpreter.Run("count 'stuff'")
        run(x=[1, 2, 3])
        assert float(run["stuff"]) == 3

    def test_count_weight(self):
        run = adl.interpreter.Run("count 'stuff' weight x")
        run(x=[1, 2, 3])
        assert float(run["stuff"]) == 6

    def test_count_regular(self):
        run = adl.interpreter.Run("count 'stuff' by regular(2, 0.0, 4.0) <- x")
        run(x=[1, 2, 3])
        assert float(run["stuff"][0]) == 1
        assert float(run["stuff"][1]) == 2
        assert float(run["stuff"].underflow) == 0
        assert float(run["stuff"].overflow) == 0
        assert float(run["stuff"].nanflow) == 0

    def test_count_regular_regular(self):
        run = adl.interpreter.Run("count 'stuff' by regular(2, 0.0, 4.0) <- x regular(2, 0.0, 4.0) <- y")
        run(x=[1, 2, 3], y=[1, 1, 1])
        assert float(run["stuff"][0][0]) == 1
        assert float(run["stuff"][0][1]) == 0
        assert float(run["stuff"][1][0]) == 2
        assert float(run["stuff"][1][1]) == 0

    def test_count_variable(self):
        run = adl.interpreter.Run("count 'stuff' by variable(1, 2, 4) <- x")
        run(x=[0.5, 1.5, 3.0, 5.0])
        assert float(run["stuff"].underflow) == 1
        assert float(run["stuff"][0]) == 1
        assert float(run["stuff"][1]) == 1
        assert float(run["stuff"].overflow) == 1

    def test_count_regular_weight(self):
        run = adl.interpreter.Run("count 'stuff' by regular(2, 0.0, 4.0) <- x weight y")
        run(x=[1, 2, 3], y=[2, 2, 2])
        assert float(run["stuff"][0]) == 2
        assert float(run["stuff"][1]) == 4
        assert float(run["stuff"].underflow) == 0
        assert float(run["stuff"].overflow) == 0
        assert float(run["stuff"].nanflow) == 0

    def test_count_regular_regular_weight(self):
        run = adl.interpreter.Run("count 'stuff' by regular(2, 0.0, 4.0) <- x regular(2, 0.0, 4.0) <- y weight z")
        run(x=[1, 2, 3], y=[1, 1, 1], z=[2, 2, 2])
        assert float(run["stuff"][0][0]) == 2
        assert float(run["stuff"][0][1]) == 0
        assert float(run["stuff"][1][0]) == 4
        assert float(run["stuff"][1][1]) == 0

    def test_count_variable_weight(self):
        run = adl.interpreter.Run("count 'stuff' by variable(1, 2, 4) <- x weight y")
        run(x=[0.5, 1.5, 3.0, 5.0], y=[2, 2, 2, 2])
        assert float(run["stuff"].underflow) == 2
        assert float(run["stuff"][0]) == 2
        assert float(run["stuff"][1]) == 2
        assert float(run["stuff"].overflow) == 2

    def test_sum(self):
        run = adl.interpreter.Run("sum 'stuff' x")
        run(x=[1, 2, 3])
        assert float(run["stuff"]) == 6

    def test_sum_weight(self):
        run = adl.interpreter.Run("sum 'stuff' x weight y")
        run(x=[1, 2, 3], y=[2, 2, 2])
        assert float(run["stuff"]) == 12

    def test_sum_regular(self):
        run = adl.interpreter.Run("sum 'stuff' y by regular(2, 0.0, 4.0) <- x")
        run(x=[1, 2, 3], y=[2, 2, 2])
        assert float(run["stuff"][0]) == 2
        assert float(run["stuff"][1]) == 4
        assert float(run["stuff"].underflow) == 0
        assert float(run["stuff"].overflow) == 0
        assert float(run["stuff"].nanflow) == 0

    def test_sum_regular_weight(self):
        run = adl.interpreter.Run("sum 'stuff' z by regular(2, 0.0, 4.0) <- x weight y")
        run(x=[1, 2, 3], y=[2, 2, 2], z=[3, 3, 3])
        assert float(run["stuff"][0]) == 6
        assert float(run["stuff"][1]) == 12
        assert float(run["stuff"].underflow) == 0
        assert float(run["stuff"].overflow) == 0
        assert float(run["stuff"].nanflow) == 0

    def test_profile(self):
        run = adl.interpreter.Run("profile 'stuff' x")
        run(x=[1, 2, 3])
        assert tuple(run["stuff"]) == (2.0, math.sqrt((14.0 / 3.0 - 2.0**2) / 3.0))

    def test_profile_weight(self):
        run = adl.interpreter.Run("profile 'stuff' x weight y")
        run(x=[1, 2, 3], y=[2, 2, 2])
        assert tuple(run["stuff"]) == (2.0, math.sqrt((14.0 / 3.0 - 2.0**2) / 3.0))

    def test_profile_regular(self):
        run = adl.interpreter.Run("profile 'stuff' y by regular(2, 0.0, 4.0) <- x")
        run(x=[1, 2, 3], y=[2, 2, 2])
        assert tuple(run["stuff"][0]) == (2.0, 0.0)
        assert tuple(run["stuff"][1]) == (2.0, 0.0)
        assert tuple(run["stuff"].underflow) == (0.0, 0.0)
        assert tuple(run["stuff"].overflow) == (0.0, 0.0)
        assert tuple(run["stuff"].nanflow) == (0.0, 0.0)

    def test_profile_regular_weight(self):
        run = adl.interpreter.Run("profile 'stuff' z by regular(2, 0.0, 4.0) <- x weight y")
        run(x=[1, 2, 3], y=[2, 2, 2], z=[3, 3, 3])
        assert tuple(run["stuff"][0]) == (3.0, 0.0)
        assert tuple(run["stuff"][1]) == (3.0, 0.0)
        assert tuple(run["stuff"].underflow) == (0.0, 0.0)
        assert tuple(run["stuff"].overflow) == (0.0, 0.0)
        assert tuple(run["stuff"].nanflow) == (0.0, 0.0)

    def test_fraction(self):
        run = adl.interpreter.Run("fraction 'stuff' x")
        run(x=[False, False, True, False])
        assert run["stuff"].value() == 0.25
        assert round(run["stuff"].error(), 3) == 0.465
        assert round(run["stuff"].error("wilson"), 3) == 0.707

    def test_source(self):
        run = adl.interpreter.Run("source 'A' { y := x }")
        assert "y" in run("A", x=[1, 2, 3])
        assert "y" not in run("B", x=[1, 2, 3])

        run = adl.interpreter.Run("not source 'A' { y := x }")
        assert "y" not in run("A", x=[1, 2, 3])
        assert "y" in run("B", x=[1, 2, 3])

        run = adl.interpreter.Run("source 'A', 'B' { y := x }")
        assert "y" in run("A", x=[1, 2, 3])
        assert "y" in run("B", x=[1, 2, 3])

        run = adl.interpreter.Run("not source 'A', 'B' { y := x }")
        assert "y" not in run("A", x=[1, 2, 3])
        assert "y" not in run("B", x=[1, 2, 3])

    def test_region_scope(self):
        run = adl.interpreter.Run("region 'stuff' { y := x }")
        assert "y" not in run(x=[1, 2, 3])

        run = adl.interpreter.Run("region 'stuff' p { y := x }")
        assert "y" not in run(x=[1, 2, 3], p=[True, False, True])

    def test_region_count(self):
        run = adl.interpreter.Run("region 'stuff' { count 'thingy' }")
        run(x=[1, 2, 3])
        assert float(run["stuff", "thingy"]) == 3

    def test_region_count_predicate(self):
        run = adl.interpreter.Run("region 'stuff' p { count 'thingy' }")
        run(x=[1, 2, 3], p=[True, False, True])
        assert float(run["stuff", "thingy"]) == 2

    def test_region_count_binning(self):
        run = adl.interpreter.Run("region 'stuff' by regular(2, 0.0, 4.0) <- x { count 'thingy' }")
        run(x=[1, 2, 3])
        assert float(run["stuff", 0, "thingy"]) == 1
        assert float(run["stuff", 1, "thingy"]) == 2

    def test_region_count_predicate_binning(self):
        run = adl.interpreter.Run("region 'stuff' p by regular(2, 0.0, 4.0) <- x { count 'thingy' }")
        run(x=[1, 2, 3], p=[True, False, True])
        assert float(run["stuff", 0, "thingy"]) == 1
        assert float(run["stuff", 1, "thingy"]) == 1

    def test_region_region_count(self):
        run = adl.interpreter.Run("region 'stuff' p { region 'thingy' by regular(2, 0.0, 4.0) <- x { count 'wow' } }")
        run(x=[1, 2, 3], p=[True, False, True])
        assert float(run["stuff", "thingy", 0, "wow"]) == 1
        assert float(run["stuff", "thingy", 1, "wow"]) == 1

    def test_vary(self):
        run = adl.interpreter.Run("vary 'one' y := 1 'two' y := 2 { count 'stuff' by regular(2, 0.5, 2.5) <- y }")
        run(x=[1, 2, 3])
        assert float(run["one", "stuff", 0]) == 3
        assert float(run["one", "stuff", 1]) == 0
        assert float(run["two", "stuff", 0]) == 0
        assert float(run["two", "stuff", 1]) == 3

    def test_vary_two(self):
        run = adl.interpreter.Run("vary 'one' y := 1; z := 1 'two' y := 2; z := 2 { count 'stuff' by regular(2, 0.5, 2.5) <- z }")
        run(x=[1, 2, 3])
        assert float(run["one", "stuff", 0]) == 3
        assert float(run["one", "stuff", 1]) == 0
        assert float(run["two", "stuff", 0]) == 0
        assert float(run["two", "stuff", 1]) == 3

    def test_expression_literal(self):
        run = adl.interpreter.Run("y := 5")
        assert run(x=[1, 2, 3]) == {"x": [1, 2, 3], "y": [5, 5, 5]}

    def test_expression_attribute(self):
        run = adl.interpreter.Run("y := x.one")
        assert run(x=[{"one": 1}, {"one": 2}, {"one": 3}]) == {"x": [{"one": 1}, {"one": 2}, {"one": 3}], "y": [1, 2, 3]}

    def test_expression_subscript(self):
        run = adl.interpreter.Run("y := x['one']")
        assert run(x=[{"one": 1}, {"one": 2}, {"one": 3}]) == {"x": [{"one": 1}, {"one": 2}, {"one": 3}], "y": [1, 2, 3]}

        run = adl.interpreter.Run("y := x[0]")
        assert run(x=[[1], [2], [3]]) == {"x": [[1], [2], [3]], "y": [1, 2, 3]}

    def test_expression_or(self):
        run = adl.interpreter.Run("z := x or y")
        assert run(x=[True, True, False, False], y=[True, False, True, False]) == {"x": [True, True, False, False], "y": [True, False, True, False], "z": [True, True, True, False]}

    def test_expression_and(self):
        run = adl.interpreter.Run("z := x and y")
        assert run(x=[True, True, False, False], y=[True, False, True, False]) == {"x": [True, True, False, False], "y": [True, False, True, False], "z": [True, False, False, False]}

    def test_expression_not(self):
        run = adl.interpreter.Run("y := not x")
        assert run(x=[True, True, False, False]) == {"x": [True, True, False, False], "y": [False, False, True, True]}

    def test_expression_eq(self):
        run = adl.interpreter.Run("z := (x == y)")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [False, True, False]}

    def test_expression_ne(self):
        run = adl.interpreter.Run("z := (x != y)")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [True, False, True]}

    def test_expression_lt(self):
        run = adl.interpreter.Run("z := x < y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [True, False, False]}

    def test_expression_le(self):
        run = adl.interpreter.Run("z := x <= y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [True, True, False]}

    def test_expression_gt(self):
        run = adl.interpreter.Run("z := x > y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [False, False, True]}

    def test_expression_ge(self):
        run = adl.interpreter.Run("z := x >= y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [False, True, True]}

    def test_expression_plus(self):
        run = adl.interpreter.Run("z := x + y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [3, 4, 5]}

    def test_expression_minus(self):
        run = adl.interpreter.Run("z := x - y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [-1, 0, 1]}

    def test_expression_times(self):
        run = adl.interpreter.Run("z := x * y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [2, 4, 6]}

    def test_expression_div(self):
        run = adl.interpreter.Run("z := x / y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [0.5, 1.0, 1.5]}

    def test_expression_mod(self):
        run = adl.interpreter.Run("z := x % y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [1, 0, 1]}

    def test_expression_uplus(self):
        run = adl.interpreter.Run("y := +x")
        assert run(x=[1, 2, 3]) == {"x": [1, 2, 3], "y": [1, 2, 3]}

    def test_expression_uminus(self):
        run = adl.interpreter.Run("y := -x")
        assert run(x=[1, 2, 3]) == {"x": [1, 2, 3], "y": [-1, -2, -3]}

    def test_expression_power(self):
        run = adl.interpreter.Run("z := x**y")
        assert run(x=[1, 2, 3], y=[2, 2, 2]) == {"x": [1, 2, 3], "y": [2, 2, 2], "z": [1, 4, 9]}

    def test_expression_sin(self):
        run = adl.interpreter.Run("y := sin(x)")
        assert run(x=[1, 2, 3]) == {"x": [1, 2, 3], "y": [math.sin(1), math.sin(2), math.sin(3)]}

    def test_define_function(self):
        run = adl.interpreter.Run("f(z) := z**2 ; y := f(x)")
        assert run(x=[1, 2, 3]) == {"x": [1, 2, 3], "y": [1, 4, 9]}

    def test_define_function_multiline(self):
        run = adl.interpreter.Run("f(z) := { q := z; q**2 } ; y := f(x)")
        assert run(x=[1, 2, 3]) == {"x": [1, 2, 3], "y": [1, 4, 9]}

    def test_external_function(self):
        run = adl.interpreter.Run("y := f(x)")
        f = lambda x: x**2
        out = run(x=[1, 2, 3], f=f)
        assert out["y"] == [1, 4, 9]
        assert out["f"][0] is f
        assert out["f"][1] is f
        assert out["f"][2] is f

    def test_external_function_exception(self):
        run = adl.interpreter.Run("y := f(x)")
        def f(x):
            raise Exception("hello")
        self.assertRaises(adl.error.ADLRuntimeError, lambda: run(x=[1, 2, 3], f=f))

    def test_functional(self):
        run = adl.interpreter.Run("y := f(g, x)")
        f = lambda g, x: g(x)
        g = lambda x: x**2
        out = run(x=[1, 2, 3], f=f, g=g)
        out["y"] == [1, 4, 9]

    def test_functional_inline(self):
        run = adl.interpreter.Run("y := f(z -> z**2, x)")
        f = lambda g, x: g(x)
        out = run(x=[1, 2, 3], f=f)
        out["y"] == [1, 4, 9]

    def test_count_nested(self):
        run = adl.interpreter.Run("count 'stuff'")
        run(x=[[], [1], [2, 3], [4, 5, 6]])
        assert float(run["stuff"]) == 4

    def test_count_nested_for(self):
        run = adl.interpreter.Run("for xi in x { count 'stuff' }")
        run(x=[[], [1], [2, 3], [4, 5, 6]])
        print(run["stuff"])

