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
            with Path(rep["deid_file"]).open(encoding="utf-8-sig", newline="") as fh:
                out = list(csv.reader(fh))
            self.assertEqual(out[0], ["Họ và tên", "Ngày sinh", "Mã BN", "Tuổi", "HbA1c"])
            self.assertEqual(out[1], ["P0001", "1958", "P0001", "67", "7.2"])
            deid_text = Path(rep["deid_file"]).read_text(encoding="utf-8-sig")
            key = Path(rep["key_file"]).read_text(encoding="utf-8-sig")
            for secret in ("Nguyễn Văn An", "079123456789", "079123456780"):
                self.assertNotIn(secret, deid_text)
                self.assertIn(secret, key)
            with Path(rep["key_file"]).open(encoding="utf-8-sig", newline="") as fh:
                self.assertEqual(next(csv.reader(fh)), ["pseudonym", "Họ và tên", "CCCD", "Mã BN", "col_x"])
            self.assertEqual(rep["rows"], 2)
            self.assertNotIn("Nguyễn", json.dumps(rep, ensure_ascii=False))

    def _run(self, table):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "d.csv"
            with src.open("w", encoding="utf-8-sig", newline="") as fh:
                csv.writer(fh).writerows(table)
            rep = deidentify.deidentify_csv(src, Path(t))
            return (rep, Path(rep["deid_file"]).read_text(encoding="utf-8-sig"),
                    Path(rep["key_file"]).read_text(encoding="utf-8-sig"))

    def test_blank_headers_do_not_leak(self):
        rep, deid, key = self._run([["Tuổi", "", ""], ["67", "079123456789", "x"], ["55", "079987654321", "y"]])
        self.assertEqual(rep["columns"], {"Tuổi": "keep", "col_2": "drop", "col_3": "keep"})
        self.assertNotIn("079123456789", deid)
        self.assertIn("079123456789", key)

    def test_duplicate_headers_do_not_leak(self):
        rep, deid, key = self._run([["Ghi chú", "Ghi chú"], ["ok", "079123456789"], ["hi", "079987654321"]])
        self.assertEqual(rep["columns"], {"Ghi chú": "keep", "Ghi chú_2": "drop"})
        self.assertNotIn("079123456789", deid)
        self.assertIn("079123456789", key)

    def test_more_header_words(self):
        pseudo = ["Tên người bệnh", "Bệnh nhân", "Mã người bệnh", "Mã hồ sơ", "Số vào viện"]
        drop = ["E-mail", "Số ĐT", "Liên hệ", "Nơi sinh", "Quê quán"]
        keep = ["HbA1c", "Tuổi", "Chẩn đoán"]
        acts = deidentify.classify_columns(pseudo + drop + keep, [])
        for h in pseudo:
            self.assertEqual(acts[h], "pseudonymise", h)
        for h in drop:
            self.assertEqual(acts[h], "drop", h)
        for h in keep:
            self.assertEqual(acts[h], "keep", h)

    def test_value_scan_phone_and_email(self):
        rows = [["0912345678", "a@b.vn"], ["0987654321", "c@d.com"]]
        acts = deidentify.classify_columns(["col_y", "col_z"], rows)
        self.assertEqual(acts, {"col_y": "drop", "col_z": "drop"})

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "e.csv"
            src.write_text("", encoding="utf-8")
            with self.assertRaises(SystemExit) as cm:
                deidentify.deidentify_csv(src, Path(t))
            self.assertEqual(str(cm.exception), "deidentify: empty file")

    def test_xlsx_first_sheet_only_warns(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl not installed")
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "w.xlsx"
            wb = openpyxl.Workbook()
            wb.active.title = "Main"
            wb.active.append(["Tuổi"])
            wb.active.append([67])
            wb.create_sheet("Other")
            wb.save(src)
            wb.close()
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rep = deidentify.deidentify_csv(src, Path(t))
            self.assertEqual(rep["rows"], 1)
            self.assertIn("only the first sheet 'Main' was read; 1 other sheet(s) ignored", err.getvalue())


if __name__ == "__main__":
    unittest.main()
