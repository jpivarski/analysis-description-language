import adl.interpreter

class Test(object):
    def test_structure(self):
        run = adl.interpreter.Run("""
source "MC" {
  region "signal" 60 < mass < 120 {
    count "total"
  }

  region "background" not 60 < mass < 120 {
    count "total"
  }
}
""")
