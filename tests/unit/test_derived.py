import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import _paths  # noqa: F401
from crolib import derived

BY_ID = {
    "R-A1-001": {"id": "R-A1-001", "kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0041, "n": 1070},
    "R-A0-001": {"id": "R-A0-001", "kind": "percent", "value": 12.54, "count": 134},
}


class TestValueOf(unittest.TestCase):
    def test_parts(self):
        self.assertEqual(derived.value_of(BY_ID, "R-A1-001"), Decimal("1.8412"))
        self.assertEqual(derived.value_of(BY_ID, "R-A1-001.value"), Decimal("1.8412"))
        self.assertEqual(derived.value_of(BY_ID, "R-A1-001.lo"), Decimal("1.214"))
        self.assertEqual(derived.value_of(BY_ID, "R-A1-001.hi"), Decimal("2.786"))
        self.assertEqual(derived.value_of(BY_ID, "R-A1-001.n"), Decimal("1070"))
        self.assertEqual(derived.value_of(BY_ID, "R-A1-001.p"), Decimal("0.0041"))
        self.assertEqual(derived.value_of(BY_ID, "R-A0-001.count"), Decimal("134"))

    def test_unknown_id(self):
        with self.assertRaises(KeyError) as cm:
            derived.value_of(BY_ID, "R-A9-999")
        self.assertIn("R-A9-999", cm.exception.args[0])

    def test_missing_part(self):
        with self.assertRaises(KeyError):
            derived.value_of(BY_ID, "R-A0-001.lo")
        with self.assertRaises(KeyError):
            derived.value_of(BY_ID, "R-A0-001.p")

    def test_unlisted_part(self):
        with self.assertRaises(KeyError) as cm:
            derived.value_of(BY_ID, "R-A1-001.ci")
        self.assertIn(".ci", cm.exception.args[0])


class TestEvaluate(unittest.TestCase):
    def test_formula(self):
        self.assertEqual(derived.evaluate("R-A1-001.hi - R-A1-001.lo", BY_ID), Decimal("1.572"))
        self.assertEqual(derived.evaluate("-(R-A0-001.count + 6) / 2", BY_ID), Decimal("-70"))
        self.assertEqual(derived.evaluate("R-A0-001.count / R-A1-001.n * 100", BY_ID).quantize(Decimal("0.1")),
                         Decimal("12.5"))

    def test_rejects_unsafe(self):
        for bad in ("__import__('os')", "R-A1-001 ** 2", "abs(1)", "x + 1", "[1]", "True", "'a'", "1 if 1 else 2"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                derived.evaluate(bad, BY_ID)

    def test_division_by_zero(self):
        with self.assertRaises(ValueError):
            derived.evaluate("R-A0-001.count / 0", BY_ID)

    def test_syntax_error(self):
        with self.assertRaises(ValueError):
            derived.evaluate("1 +", BY_ID)

    def test_key_errors_propagate(self):
        with self.assertRaises(KeyError):
            derived.evaluate("R-A9-999 + 1", BY_ID)
        with self.assertRaises(KeyError):
            derived.evaluate("R-A1-001.ci + 1", BY_ID)


class TestLedgerById(unittest.TestCase):
    def test_reads_and_missing(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            with self.assertRaises(FileNotFoundError):
                derived.ledger_by_id(p)
            (p / "ledgers").mkdir()
            (p / "ledgers" / "results-ledger.json").write_text(
                json.dumps({"results": list(BY_ID.values())}), encoding="utf-8-sig")
            self.assertEqual(set(derived.ledger_by_id(p)), {"R-A1-001", "R-A0-001"})


if __name__ == "__main__":
    unittest.main()
