import unittest
from pathlib import Path
from textwrap import dedent
import sys

this_dir = Path(__file__).resolve().parent
sys.path.insert(0, this_dir.parent.as_posix())

from runcode import reserve_dict
from runcode import runcode

ReserveDict = reserve_dict.ReserveDict


class TestReserveDict(unittest.TestCase):
    def setUp(self) -> None:
        self.d = ReserveDict.fromdicts(
            {"a": 1, "b": 2, "c": 3}, {"c": 999, "d": 4, "e": 5, "f": 6}
        )

    def test_each_constructors(self):
        self.assertEqual(
            dict(**self.d), {"d": 4, "e": 5, "f": 6, "a": 1, "b": 2, "c": 3}
        )

        self.assertEqual(self.d.get("a"), 1)

        self.assertEqual(
            dict.fromkeys(["a", "b"], 2), ReserveDict.fromkeys(["a", "b"], 2)
        )

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
        self.assertEqual(
            self.d, {"d": 4, "e": 5, "f": 6, "a": 999, "b": 2, "c": 3, "g": 999}
        )

    def test_delete(self):
        del self.d["a"]
        self.assertEqual(self.d, {"d": 4, "e": 5, "f": 6, "b": 2, "c": 3})

    def test_iter(self):
        self.assertEqual(list(self.d), ["d", "e", "f", "a", "b", "c"])

    def test_len(self):
        self.assertEqual(len(self.d), 6)

    def test_reverse(self):
        self.assertEqual(list(reversed(self.d)), ["c", "b", "a", "f", "e", "d"])


class TestReserveDictExec(unittest.TestCase):
    def test_annotation(self):
        code = dedent(
            """
            a = object()
            class _:
                def _(self, _=a): pass
            """
        )
        exec(code, {})
        exec(code, ReserveDict())


class TestRunCode(unittest.TestCase):
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

        import os
        import sys

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
            (None, ["Example", "example"]),
            (
                runcode(
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

        """
        self.assertEqual(
            (None, sorted([i for i in dir(reserve_dict) if not i.startswith("_")])),
            (
                runcode(
                    this_dir.parent.joinpath("runcode", "reserve_dict.py").read_text(),
                    namespace := {},
                    {},
                ),
                sorted(namespace),
            ),
        )
        """


if __name__ == "__main__":
    unittest.main()
