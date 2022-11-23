import unittest
from pathlib import Path
from textwrap import dedent
import sys

this_dir = Path(__file__).resolve().parent
sys.path.insert(0, this_dir.parent.as_posix())

from neval import flagged_dict
from neval import neval

FlaggedDict = flagged_dict.FlaggedDict


class TestFlaggedDict(unittest.TestCase):
    def setUp(self) -> None:
        self.d = FlaggedDict(
            {"d": 4, "e": 5, "f": 6, "a": 1, "b": 2, "c": 3},
            __flags__={"a": None, "b": None, "c": None},
        )

    def test_each_constructors(self):
        self.assertEqual(dict(**self.d), {"d": 4, "e": 5, "f": 6, "a": 1, "b": 2, "c": 3})

        self.assertEqual(self.d.get("a"), 1)

        self.assertEqual(dict.fromkeys(["a", "b"], 2), FlaggedDict.fromkeys(["a", "b"], 2))

    def test_pops(self):
        self.assertEqual(self.d.pop("c"), 3)

    def test_popitem(self):
        self.assertEqual(self.d.popitem(), ("c", 3))
        self.assertEqual(self.d.popitem(), ("b", 2))
        self.assertEqual(self.d.popitem(), ("a", 1))
        self.assertEqual(self.d.popitem(), ("f", 6))

    def test_clear(self):
        self.d.clear()
        self.assertEqual(self.d, {})

    def test_copy(self):
        d = self.d.copy()
        self.assertEqual(d, self.d)

        d.pop("c")
        self.assertNotEqual(d, self.d)

    def test_items_keys_values(self):
        # items
        self.assertEqual(
            list(self.d.items()),
            [("d", 4), ("e", 5), ("f", 6), ("a", 1), ("b", 2), ("c", 3)],
        )

        self.assertEqual(len(self.d.items()), 6)

        self.assertEqual(list({**self.d}.items()), list(self.d.items()))

        self.assertEqual({**self.d}.items(), self.d.items())

        # test contains
        self.assertTrue(("a", 1) in dict(**self.d).items())
        self.assertTrue(("a", 1) in self.d.items())

        # keys
        self.assertEqual(list(self.d.keys()), ["d", "e", "f", "a", "b", "c"])

        self.assertEqual(len(self.d), 6)

        self.assertEqual(list({**self.d}.keys()), list(self.d.keys()))

        self.assertEqual({**self.d}.keys(), self.d.keys())

        self.assertIn("a", self.d.keys())

        # values
        self.assertEqual(list(self.d.values()), [4, 5, 6, 1, 2, 3])

        self.assertEqual(len(self.d.values()), 6)

        self.assertEqual(list({**self.d}.values()), list(self.d.values()))

        # self.assertEqual({**self.d}.values(), self.d.values())

        self.assertTrue(6 in self.d.values())

    def test_set_default(self):
        self.assertEqual(self.d.setdefault("a", 999), 1)
        self.assertEqual(self.d.setdefault("g", 999), 999)

    def test_update(self):
        self.d.update({"a": 999, "g": 999})
        self.assertEqual(self.d, {"d": 4, "e": 5, "f": 6, "a": 999, "b": 2, "c": 3, "g": 999})

    def test_delete(self):
        del self.d["a"]
        self.assertEqual(self.d, {"d": 4, "e": 5, "f": 6, "b": 2, "c": 3})

    def test_iter(self):
        self.assertEqual(list(self.d), ["d", "e", "f", "a", "b", "c"])

    def test_len(self):
        self.assertEqual(len(self.d), 6)

    def test_reverse(self):
        self.assertEqual(list(reversed(self.d)), ["c", "b", "a", "f", "e", "d"])


class TestFlaggedDictExec(unittest.TestCase):
    def test_annotation(self):
        code = dedent(
            """
            a = object()
            class _:
                def _(self, _=a): pass
            """
        )
        exec(code, {})
        exec(code, FlaggedDict())


class TestRunCode(unittest.TestCase):
    def test_assignment(self):

        self.assertEqual(2, neval("1+1"))

        self.assertEqual(None, neval("for i in range(10): i"))

        self.assertEqual(
            9,
            neval(
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
            neval("while True: break"),
        )

    def test_return(self):
        self.assertEqual(
            # Do we want to return None or the function `f`?
            None,
            neval("def f(): pass"),
        )

        self.assertTrue(callable(neval("lambda:None")))

        # unfortunately the `with` statement is the last statement and not the `1` expression
        self.assertEqual(
            None,
            neval(
                dedent(
                    """
                    class w:
                        def __enter__(self): pass
                        def __exit__(self, *args): pass
                            
                    with w():
                        1
                    """
                )
            ),
        )

        self.assertEqual(None, neval(""))

    def test_scoping(self):

        # Exec used class definition scope when globals and locals are specified
        self.assertRaisesRegex(
            NameError,
            "name 'a' is not defined",
            lambda: exec("a=[1];[i for i in a if a]", {}, {}),
        )

        # Runcode does not use class definition scope when namespace (~locals) and
        # namespace_readonly (~globals) are specified
        self.assertEqual([1], neval("a=[1];[i for i in a if a]"))

        self.assertEqual(
            (None, {"a": 1, "b": 2}),
            (
                neval("a=1;b=2;", namespace := {}, {"a": 0}),
                namespace,
            ),
        )

        self.assertEqual(
            (None, {"a": 0}),
            (
                neval("a=1;b=2;", {}, namespace_readonly := {"a": 0}),
                namespace_readonly,
            ),
        )

        self.assertEqual(
            (None, ["mock_module_54f56", "os", "sys"]),
            (
                neval(
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

        import os
        import sys

        self.assertEqual(
            (None, ["mock_module_54f56"]),
            (
                neval(
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
            (None, ["Example", "example"]),
            (
                neval(
                    dedent(
                        f"""
                        Example = object()
                        def example(a=Example):
                            pass
                        """
                    ),
                    namespace := {},
                    {},
                ),
                sorted(namespace),
            ),
        )

        self.assertEqual(
            (None, sorted([i for i in dir(flagged_dict) if not i.startswith("_")])),
            (
                neval(
                    this_dir.parent.joinpath("neval", "flagged_dict.py").read_text(),
                    namespace := {},
                ),
                sorted(namespace),
            ),
        )

        # Do we want this to be true or not? For now it's False
        self.assertEqual(
            False,
            neval(
                dedent(
                    """
                        name_main = False
                        if __name__ == "__main__":
                            name_main = True
                        name_main
                        """
                ),
                namespace := {},
            ),
        )

        # Assign-and-return via walrus operator
        self.assertEqual(
            (1, {"a": 1}),
            (neval("(a := 1)", namespace := {}), namespace),
        )

    def test_errors(self):
        code = dedent(
            """\
            a
            b
            c
            d d d
            e"""
        )
        #   File "<neval-2b43d9fb0bb36723ba251724e7078a6a33f6fefd>", line 1
        #     a = 1 b = 2
        #           ^
        # SyntaxError: invalid syntax
        # ----> 1 a = 1 b = 2
        #

        self.assertRaisesRegex(
            SyntaxError,
            "invalid syntax",
            lambda: neval(code),
        )

        # test if python running this test is > 3.11
        if sys.version_info >= (3, 11):
            #
            err = None
            try:
                neval(code)
            except SyntaxError as e:
                err = e

            self.assertEqual(
                err.msg,
                "invalid syntax",
            )
            self.assertEqual(
                err.__notes__,
                [
                    dedent(
                        """\
                              1 a
                              2 b
                              3 c
                        ----> 4 d d d
                              5 e"""
                    )
                ],
            )

        self.assertRaisesRegex(
            ZeroDivisionError,
            "division by zero",
            lambda: neval("1/0"),
        )

        self.assertRaisesRegex(
            ZeroDivisionError,
            "division by zero",
            lambda: neval("1/0", {}, {}, False),
        )


if __name__ == "__main__":
    unittest.main()
