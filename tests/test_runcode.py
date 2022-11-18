import unittest
from pathlib import Path
from textwrap import dedent
import os
import sys

this_dir = Path(__file__).resolve().parent

sys.path.insert(0, this_dir.parent.as_posix())
from runcode import runcode


class Tests(unittest.TestCase):
    def test_assignment(self):

        self.assertEqual(2, runcode("1+1"))

        self.assertEqual(None, runcode("for i in range(10): i"))

        self.assertEqual(
            9,
            runcode(
                dedent(
                    """
                    for i in range(10):
                        i
                    i
                    """
                )
            ),
        )

        self.assertEqual(
            None,
            runcode("while True: break"),
        )

    def test_scoping(self):

        # Exec used class definition scope when globals and locals are specified
        self.assertRaisesRegex(
            NameError,
            "name 'a' is not defined",
            lambda: exec("a=[1];[i for i in a if a]", {}, {}),
        )

        # Runcode does not use class definition scope when namespace (~locals) and
        # readonly_namespace (~globals) are specified
        self.assertEqual([1], runcode("a=[1];[i for i in a if a]"))

        self.assertEqual(
            (None, {"a": 1, "b": 2}),
            (
                runcode("a=1;b=2;", namespace := {}, {"a": 0}),
                namespace,
            ),
        )

        self.assertEqual(
            (None, {"a": 0}),
            (
                runcode("a=1;b=2;", {}, readonly_namespace := {"a": 0}),
                readonly_namespace,
            ),
        )

        self.assertEqual(
            (None, ["mock_module_54f56", "os", "sys"]),
            (
                runcode(
                    dedent(
                        f"""
                        import sys
                        import os
                        sys.path.insert(
                            0,
                            os.path.join({repr(str(Path(__file__).resolve().parent))}, "import_examples")
                        )
                        import mock_module_54f56;
                        """
                    ),
                    namespace := {},
                    {},
                ),
                sorted(namespace),
            ),
        )

        self.assertEqual(
            (None, ["mock_module_54f56"]),
            (
                runcode(
                    dedent(
                        f"""
                        sys.path.insert(
                            0,
                            os.path.join({repr(str(Path(__file__).resolve().parent))}, "import_examples")
                        )
                        import mock_module_54f56;
                        """
                    ),
                    namespace := {},
                    {"os": os, "sys": sys},
                ),
                sorted(namespace),
            ),
        )

        self.assertEqual(
            (None, []),
            (
                runcode(
                    this_dir.parent.joinpath("runcode", "runcode.py").read_text(),
                    namespace := {},
                    {},
                ),
                sorted(namespace),
            ),
        )


if __name__ == "__main__":
    unittest.main()
