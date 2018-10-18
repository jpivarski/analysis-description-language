#!/usr/bin/env python

import math
import unittest

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
