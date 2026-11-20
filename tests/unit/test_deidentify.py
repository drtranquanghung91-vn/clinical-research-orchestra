import csv
import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import deidentify

ROWS = [["Họ và tên", "Ngày sinh", "CCCD", "Mã BN", "Tuổi", "HbA1c", "col_x"],
        ["Nguyễn Văn An", "12/03/1958", "079123456789", "BN001", "67", "7.2", "079123456780"],
        ["Trần Thị Bình", "01/01/1970", "079987654321", "BN002", "55", "6.8", "079123456781"]]


class TestDeidentify(unittest.TestCase):
    def test_classify_columns(self):
        acts = deidentify.classify_columns(ROWS[0], ROWS[1:])
        self.assertEqual(acts["Họ và tên"], "pseudonymise")
        self.assertEqual(acts["Ngày sinh"], "year-only")
        self.assertEqual(acts["CCCD"], "drop")
        self.assertEqual(acts["Mã BN"], "pseudonymise")
        self.assertEqual(acts["Tuổi"], "keep")
        self.assertEqual(acts["HbA1c"], "keep")
        self.assertEqual(acts["col_x"], "drop")

    def test_deidentify_csv_outputs(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "data.csv"
            with src.open("w", encoding="utf-8-sig", newline="") as fh:
                csv.writer(fh).writerows(ROWS)
            rep = deidentify.deidentify_csv(src, Path(t))
            out = list(csv.reader(Path(rep["deid_file"]).open(encoding="utf-8-sig")))
            self.assertEqual(out[0], ["Họ và tên", "Ngày sinh", "Mã BN", "Tuổi", "HbA1c"])
            self.assertEqual(out[1], ["P0001", "1958", "P0001", "67", "7.2"])
            self.assertNotIn("Nguyễn Văn An", Path(rep["deid_file"]).read_text(encoding="utf-8-sig"))
            key = Path(rep["key_file"]).read_text(encoding="utf-8-sig")
            self.assertIn("Nguyễn Văn An", key)
            self.assertEqual(rep["rows"], 2)
            self.assertNotIn("Nguyễn", json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
