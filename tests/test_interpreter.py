#!/usr/bin/env python

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
