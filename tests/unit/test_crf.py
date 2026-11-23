import contextlib
import csv
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import crf
import gate
import init_project

VARIABLES = """# Bảng biến số nghiên cứu (hư cấu, cho kiểm thử)

## 1. Biến phơi nhiễm

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn | Vai trò |
|---|---|---|---|---|---|---|
| MT2 | HbA1c lúc nhập viện (phân nhóm) | HbA1c trong 48 giờ đầu | Thứ tự (ordinal) | < 7% / 7–9% / > 9% (nhóm < 7% tham chiếu) | EMR | Phơi nhiễm |

## 2. Biến kết cục

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn | Vai trò |
|---|---|---|---|---|---|---|
| MT1 | Tái nhập viện 1 năm (mọi nguyên nhân) | Nhập viện lại trong 365 ngày | Nhị giá | Có / Không | HIS | Kết cục chính |

## 3. Biến nhiễu

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn | Vai trò |
|---|---|---|---|---|---|---|
| MT2 | Tuổi | Tuổi khi nhập viện | Liên tục | Năm | EMR | Nhiễu |
| MT2 | Giới | Giới trong hồ sơ | Phân loại nhị giá | Nam / Nữ | EMR | Nhiễu |
|  | Họ tên | Họ tên trong hồ sơ | Văn bản |  | EMR | Đối chiếu |
"""
SAP = """# SAP (hư cấu)

## Analysis register

| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |
|---|---|---|---|---|---|---|
| A0 | MT1 | Đặc điểm chung theo 3 nhóm HbA1c (Bảng 1) | Tất cả | Mô tả | Không | Không |
| A1 | MT2 | Tái nhập viện mọi nguyên nhân trong 1 năm | Như A0 | Hồi quy logistic | {cov} | Không |
"""
DOSSIER = ("# Hồ sơ đạo đức\n\n| Tài liệu | Trạng thái |\n|---|---|\n| crf.md | drafted |\n"
           "| data-dictionary.csv | drafted |\n| consent-form.md | drafted |\n")


class TestCrf(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "Fictional cohort", "thesis-masters", "cohort", "vi", "vi")
        self.write("03_protocol/variables.md", VARIABLES)
        self.write("03_protocol/sap.md", SAP.format(cov="Tuổi, giới (xem mục 8)"))

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def write(self, rel, text):
        path = self.p / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def lock_g2(self, files=("03_protocol/variables.md", "03_protocol/sap.md")):
        gate.open_gate(self.p, "G2", by="Example author", files=list(files))

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = crf.main([str(self.p), *argv])
        return code, out.getvalue(), err.getvalue()

    def dictionary(self):
        with open(self.p / crf.DICT, encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def test_build_needs_g2(self):
        code, out, _ = self.cli("build")
        self.assertEqual(code, 1)
        self.assertIn("G2", out)
        self.assertFalse((self.p / crf.CRF).exists())

    def test_build_writes_crf_and_dictionary(self):
        self.lock_g2()
        code, out, err = self.cli("build")
        self.assertEqual(code, 0, out + err)
        raw = (self.p / crf.DICT).read_bytes()
        self.assertNotIn(b"\r\n", raw)
        self.assertEqual(raw.decode("utf-8").splitlines()[0], "variable,label,type,unit,values,range,source_form,required")
        rows = {r["variable"]: r for r in self.dictionary()}
        self.assertEqual(set(rows), {"hba1c_luc_nhap_vien", "tai_nhap_vien_1_nam", "tuoi", "gioi", "ho_ten"})
        self.assertEqual((rows["tuoi"]["type"], rows["tuoi"]["unit"]), ("continuous", "Năm"))
        self.assertEqual((rows["gioi"]["type"], rows["gioi"]["values"]), ("binary", "Nam|Nữ"))
        self.assertEqual(rows["hba1c_luc_nhap_vien"]["type"], "ordinal")
        self.assertEqual(len(rows["hba1c_luc_nhap_vien"]["values"].split("|")), 3)
        self.assertEqual(rows["ho_ten"]["type"], "text")
        self.assertTrue(all(r["source_form"] == "main" and r["required"] == "yes" for r in rows.values()))
        text = (self.p / crf.CRF).read_text(encoding="utf-8")
        self.assertIn("## Biểu mẫu: main", text)
        self.assertIn("### 2. Biến kết cục", text)
        self.assertIn("| tai_nhap_vien_1_nam |", text)

    def test_clean_check_warns_identifier_and_minimisation(self):
        self.lock_g2()
        self.cli("build")
        self.write(crf.DOSSIER, DOSSIER)
        found = crf.check(self.p)
        self.assertFalse([f for f in found if f[0] == "block"], found)
        warns = " ".join(m for lv, _, m in found if lv == "warn")
        self.assertIn("ho_ten: a direct identifier", warns)
        self.assertIn("ho_ten: no objective", warns)
        self.assertNotIn("tuoi:", warns)
        self.assertEqual(self.cli("check")[0], 0)

    def test_register_variable_missing_blocks(self):
        self.write("03_protocol/sap.md", SAP.format(cov="Tuổi, giới, BMI"))
        self.lock_g2()
        self.cli("build")
        code, out, _ = self.cli("check")
        self.assertEqual(code, 1)
        self.assertIn("E-CRF block 03_protocol/sap.md:", out)
        self.assertIn("A1 (covariates) uses 'BMI', which matches no CRF variable", out)

    def test_crf_map_must_name_a_dictionary_variable(self):
        self.write("03_protocol/sap.md", SAP.format(cov="Tuổi, giới, BMI"))
        self.lock_g2()
        self.cli("build")
        self.write(crf.MAP, "term,variable\nBMI,bmi\n")
        self.assertIn("not in the data dictionary", " ".join(m for lv, _, m in crf.check(self.p) if lv == "block"))
        self.write(crf.MAP, "term,variable\nBMI,tuoi\n")
        self.assertFalse([f for f in crf.check(self.p) if f[0] == "block"])

    def test_dictionary_and_crf_problems_block(self):
        self.lock_g2()
        self.cli("build")
        rows = self.dictionary()
        rows[0]["type"] = ""
        rows[1]["values"] = ""
        rows.append(dict(rows[2], variable="extra_field"))
        with open(self.p / crf.DICT, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=crf.FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        msgs = [m for lv, _, m in crf.check(self.p) if lv == "block"]
        self.assertTrue(any(m.endswith(": no type") for m in msgs), msgs)
        self.assertTrue(any("without a value list" in m for m in msgs), msgs)
        self.assertTrue(any("extra_field is in the data dictionary but not in the CRF" in m for m in msgs), msgs)

    def test_missing_outputs_block_and_errors(self):
        self.assertEqual(len([f for f in crf.check(self.p) if f[0] == "block"]), 2)
        self.assertEqual(crf.main([str(self.t / "none"), "check"]), 2)
        (self.p / "03_protocol" / "variables.md").unlink()
        self.lock_g2(files=("03_protocol/sap.md",))
        self.assertEqual(self.cli("build")[0], 2)

    def test_english_headers_and_dossier_warn(self):
        self.write("03_protocol/variables.md", "| Variable | Definition | Type | Values / unit | Role | Objective |\n"
                   "|---|---|---|---|---|---|\n| Smoking status | self-report | Categorical | never / former / current "
                   "| Confounder | O2 |\n| Weight | scale | Continuous | kg | Descriptive | O1 |\n")
        self.write("03_protocol/sap.md", SAP.format(cov="Smoking status"))
        self.lock_g2()
        self.cli("build")
        rows = {r["variable"]: r for r in self.dictionary()}
        self.assertEqual(rows["smoking_status"]["values"], "never|former|current")
        self.assertEqual(rows["weight"]["unit"], "kg")
        warns = [m for lv, _, m in crf.check(self.p) if lv == "warn"]
        self.assertIn("no dossier.md listing the ethics documents and their status", warns)

    def test_fold_and_type_order(self):
        self.assertEqual(crf.fold("  Đái Tháo   Đường "), "dai thao duong")
        vs = crf.parse_variables("| Biến | Loại |\n|---|---|\n| A | Thứ tự (ordinal)/phân loại |\n| B | Phân loại nhị giá |\n"
                                 "| C | Thời gian-đến-sự kiện |\n| D | ? |\n")
        self.assertEqual([v["type"] for v in vs], ["ordinal", "binary", "time-to-event", ""])
        self.assertEqual([v["variable"] for v in crf.parse_variables("| Code | Biến | Loại |\n|---|---|---|\n"
                                                                     "| x1 | A | Liên tục |\n| x1 | B | Liên tục |\n")],
                         ["x1", "x1_2"])


if __name__ == "__main__":
    unittest.main()
