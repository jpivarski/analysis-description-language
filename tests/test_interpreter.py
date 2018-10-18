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
        assert float(run["stuff"]) == 3.0

    def test_count_weight(self):
        run = adl.interpreter.Run("count 'stuff' weight x")
        run(x=[1, 2, 3])
        assert float(run["stuff"]) == 6.0

    def test_count(self):
        run = adl.interpreter.Run("count 'stuff' by regular(2, 0.0, 4.0) <- x")
        run(x=[1, 2, 3])
        assert float(run["stuff"][0]) == 1
        assert float(run["stuff"][1]) == 2
        assert float(run["stuff"].underflow) == 0
        assert float(run["stuff"].overflow) == 0
        assert float(run["stuff"].nanflow) == 0
