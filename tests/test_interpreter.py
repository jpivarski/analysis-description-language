import adl.interpreter

class Test(object):
    def test_structure(self):
        run = adl.interpreter.Run("""
hey
""")
        print(run(hey=3))
