import contextlib
import csv
import io
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

    def _run(self, table, err=None, header_row=None):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "d.csv"
            with src.open("w", encoding="utf-8-sig", newline="") as fh:
                csv.writer(fh).writerows(table)
            with contextlib.redirect_stderr(err if err is not None else io.StringIO()):
                rep = deidentify.deidentify_csv(src, Path(t), header_row=header_row)
            key = Path(rep["key_file"]).read_text(encoding="utf-8-sig")
            if rep.get("key_episodes_file"):
                key += Path(rep["key_episodes_file"]).read_text(encoding="utf-8-sig")
            return rep, Path(rep["deid_file"]).read_text(encoding="utf-8-sig"), key

    def _rows(self, text):
        return list(csv.reader(io.StringIO(text)))

    # C1: split / unlabelled name columns, title rows, clinical headers, per-patient pseudonyms
    def test_split_name_layout(self):
        table = [["Mã BN", "Họ", "Tên", "Tuổi", "Số BHXH", "Nơi ở"],
                 ["BN001", "Nguyễn Văn", "An", "67", "7912345678", "Phường 5 Quận 3"],
                 ["BN002", "Trần Thị", "Bình", "55", "7912345679", "Xã Tân Phú"]]
        rep, deid, key = self._run(table)
        self.assertEqual(rep["columns"], {"Mã BN": "pseudonymise", "Họ": "pseudonymise", "Tên": "pseudonymise",
                                          "Tuổi": "keep", "Số BHXH": "drop", "Nơi ở": "drop"})
        for secret in ("Nguyễn Văn", "Trần Thị", "Bình", "7912345678", "Phường 5", "Tân Phú"):
            self.assertNotIn(secret, deid)
            self.assertIn(secret, key)

    def test_title_row_layout(self):
        table = [["DANH SÁCH BỆNH NHÂN THÁNG 10/2026", "", ""], ["Khoa Nội tim mạch", "", ""],
                 ["Họ và tên", "Tuổi", "Chẩn đoán"],
                 ["Nguyễn Văn An", "67", "THA"], ["Trần Thị Bình", "55", "ĐTĐ"]]
        rep, deid, key = self._run(table)
        self.assertEqual(rep["columns"], {"Họ và tên": "pseudonymise", "Tuổi": "keep", "Chẩn đoán": "keep"})
        self.assertEqual(rep["rows"], 2)
        self.assertEqual(rep["rows_above_header"], 2)
        self.assertEqual(self._rows(deid), [["Họ và tên", "Tuổi", "Chẩn đoán"], ["P0001", "67", "THA"],
                                            ["P0002", "55", "ĐTĐ"]])
        for secret in ("DANH SÁCH", "Khoa Nội", "Nguyễn Văn An"):
            self.assertNotIn(secret, deid)

    # R3: no recognised header row -> nothing written, exit 2; --header-row N forces a row
    def test_headerless_file_writes_nothing_and_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "h.csv"
            with src.open("w", encoding="utf-8-sig", newline="") as fh:
                csv.writer(fh).writerows([["Nguyễn Văn An", "079123456789", "67"], ["Trần Thị Bình", "x", "55"]])
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = deidentify.main([str(src)])
            self.assertEqual(code, 2)
            self.assertIn("could not find a header row; add one or pass --header-row N (1-based)", err.getvalue())
            self.assertEqual(sorted(x.name for x in Path(t).iterdir()), ["h.csv"])

    def test_header_row_option_forces_row(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "h.csv"
            with src.open("w", encoding="utf-8-sig", newline="") as fh:
                csv.writer(fh).writerows([["Ghi chú", "Khác"], ["a", "b"]])
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = deidentify.main([str(src), "--header-row", "1"])
            self.assertEqual(code, 0)
            rep = json.loads(out.getvalue())
            self.assertEqual(rep["rows_above_header"], 0)
            self.assertEqual(rep["rows"], 1)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(deidentify.main([str(src), "--header-row", "9"]), 2)

    # R2: columns found only by name-shaped values are dropped (to the key file), not pseudonymised
    def test_unlabelled_name_column_is_dropped(self):
        rows = [["67", "Nguyễn Văn An"], ["55", "Trần Thị Bình"], ["40", "LÊ MINH TUẤN"], ["33", ""]]
        acts = deidentify.classify_columns(["Tuổi", "col_x"], rows)
        self.assertEqual(acts, {"Tuổi": "keep", "col_x": "drop"})

    def test_same_patient_with_two_doctors_keeps_one_pseudonym(self):
        table = [["Mã BN", "Tuổi", "Bác sĩ điều trị"],
                 ["BN001", "67", "Lê Văn Cường"], ["BN002", "55", "Lê Văn Cường"], ["BN001", "67", "Phạm Thị Dung"]]
        rep, deid, key = self._run(table)
        self.assertEqual(rep["columns"], {"Mã BN": "pseudonymise", "Tuổi": "keep", "Bác sĩ điều trị": "drop"})
        self.assertEqual(rep["reasons"], {"Bác sĩ điều trị": "name-like values"})
        self.assertEqual([r[0] for r in self._rows(deid)[1:]], ["P0001", "P0002", "P0001"])
        self.assertEqual(self._rows(key)[0], ["pseudonym", "Mã BN", "Bác sĩ điều trị"])
        for secret in ("Lê Văn Cường", "Phạm Thị Dung", "BN001"):
            self.assertNotIn(secret, deid)
        self.assertIn("Lê Văn Cường", key)

    def test_patient_key_without_record_id_uses_name_and_dob(self):
        table = [["Họ và tên", "Ngày sinh", "Tuổi"],
                 ["Nguyễn Văn An", "12/03/1958", "67"], ["Nguyễn Văn An", "01/01/1990", "35"],
                 ["Nguyễn Văn An", "12/03/1958", "67"]]
        rep, deid, key = self._run(table)
        self.assertEqual([r[0] for r in self._rows(deid)[1:]], ["P0001", "P0002", "P0001"])

    def test_name_like_values_under_clinical_header_are_kept(self):
        rows = [["Suy Tim"], ["Rung Nhĩ"], ["Đái Tháo Đường"]]
        self.assertEqual(deidentify.classify_columns(["Chẩn đoán"], rows), {"Chẩn đoán": "keep"})

    def test_exact_header_words(self):
        pseudo = ["Họ", "Tên", "Họ đệm", "Tên đệm", "Họ và tên đệm", "First name", "Last name", "Surname",
                  "Given name", "Full name"]
        drop = ["BHXH", "Số BHXH", "Số thẻ", "Mã thẻ", "Nơi ở", "Cư trú", "Nơi cư trú", "ĐT", "Số ĐT", "SĐT",
                "Điện thoại"]
        keep = ["Ho khan", "Tuổi bệnh nhân", "Giới tính bệnh nhân", "Số bệnh nhân", "Nhóm người bệnh",
                "Thời gian ĐT", "DT da", "Cân nặng", "Chiều cao", "Số lượng", "Giới tính", "Số lượng tiểu cầu",
                "Huyết áp tâm thu", "Áp lực động mạch phổi"]
        acts = deidentify.classify_columns(pseudo + drop + keep, [])
        for h in pseudo:
            self.assertEqual(acts[h], "pseudonymise", h)
        for h in drop:
            self.assertEqual(acts[h], "drop", h)
        for h in keep:
            self.assertEqual(acts[h], "keep", h)

    # R1: record-id headers before clinical words; clinical keep only as a prefix; village/ward words drop
    def test_record_id_headers_are_pseudonymised(self):
        ids = ["Mã số bệnh nhân", "Mã số người bệnh", "Mã BA", "Số BA", "Mã LK", "Mã điều trị", "Mã tiếp nhận",
               "Số nhập viện", "Mã y tế", "Mã định danh", "Mã số BN", "Patient ID", "Số bệnh án"]
        acts = deidentify.classify_columns(ids, [])
        for h in ids:
            self.assertEqual(acts[h], "pseudonymise", h)

    def test_address_part_headers_are_dropped(self):
        drop = ["Thôn/xóm", "Xã/phường", "Ấp", "Tổ dân phố", "Thon", "Xa phuong"]
        acts = deidentify.classify_columns(drop, [])
        for h in drop:
            self.assertEqual(acts[h], "drop", h)

    def test_name_phrase_with_clinical_word_is_not_kept(self):
        acts = deidentify.classify_columns(["Họ tên người giới thiệu"], [])
        self.assertNotEqual(acts["Họ tên người giới thiệu"], "keep")

    # W3 N1: role-qualified name columns are not the patient: dropped to the key file, never keyed
    def test_doctor_name_column_dropped_patient_name_keyed(self):
        table = [["Họ tên bác sĩ", "Họ tên bệnh nhân", "Năm sinh"],
                 ["Lê Văn Cường", "Nguyễn Văn An", "1958"], ["Phạm Thị Dung", "Nguyễn Văn An", "1958"],
                 ["Lê Văn Cường", "Trần Thị Bình", "1970"]]
        rep, deid, key = self._run(table)
        self.assertEqual(rep["columns"]["Họ tên bác sĩ"], "drop")
        self.assertEqual(rep["reasons"]["Họ tên bác sĩ"], "non-patient name")
        self.assertEqual(rep["columns"]["Họ tên bệnh nhân"], "pseudonymise")
        self.assertEqual(rep["patient_key"][0], "Họ tên bệnh nhân")
        self.assertEqual([r[0] for r in self._rows(deid)[1:]], ["P0001", "P0001", "P0002"])
        for secret in ("Lê Văn Cường", "Nguyễn Văn An"):
            self.assertNotIn(secret, deid)
            self.assertIn(secret, key)

    def test_referrer_dropped_same_patient_same_pseudonym(self):
        table = [["Họ tên người giới thiệu", "Họ và tên", "Ngày sinh"],
                 ["Lê Văn Cường", "Nguyễn Văn An", "12/03/1958"], ["Phạm Thị Dung", "Nguyễn Văn An", "12/03/1958"]]
        rep, deid, key = self._run(table)
        self.assertEqual(rep["columns"]["Họ tên người giới thiệu"], "drop")
        self.assertEqual(rep["reasons"]["Họ tên người giới thiệu"], "non-patient name")
        self.assertEqual(rep["patient_key"], ["Họ và tên", "Ngày sinh"])
        self.assertEqual(self._rows(deid), [["Họ và tên", "Ngày sinh"], ["P0001", "1958"], ["P0001", "1958"]])

    def test_empty_pseudonymised_cell_stays_empty(self):
        table = [["Mã BN", "Họ và tên", "Tuổi"], ["BN001", "", "67"], ["BN002", "Trần Thị Bình", "55"]]
        rep, deid, key = self._run(table)
        self.assertEqual(self._rows(deid)[1:], [["P0001", "", "67"], ["P0002", "P0002", "55"]])

    # W3 N2: patient-level IDs key the patient; episode IDs get their own E-codes and key file
    def test_episode_id_first_patient_id_keys(self):
        table = [["Số vào viện", "Mã BN", "Tuổi"],
                 ["VV24-0001", "BN001", "67"], ["VV24-0002", "BN002", "55"], ["VV25-0103", "BN001", "68"]]
        rep, deid, key = self._run(table)
        self.assertEqual(rep["patient_key"], ["Mã BN"])
        rows = self._rows(deid)[1:]
        self.assertEqual([r[1] for r in rows], ["P0001", "P0002", "P0001"])
        self.assertEqual([r[0] for r in rows], ["E0001", "E0002", "E0003"])
        for secret in ("VV24-0001", "VV25-0103", "BN001"):
            self.assertNotIn(secret, deid)
            self.assertIn(secret, key)  # episode originals come from <stem>.key-episodes.csv

    def test_episode_key_file_maps_every_visit(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "v.csv"
            with src.open("w", encoding="utf-8-sig", newline="") as fh:
                csv.writer(fh).writerows([["MA_LK", "MA_BN", "TUOI"], ["LK1", "BN001", "67"], ["LK2", "BN001", "67"],
                                          ["LK3", "BN002", "50"]])
            with contextlib.redirect_stderr(io.StringIO()):
                rep = deidentify.deidentify_csv(src, Path(t))
            deid = self._rows(Path(rep["deid_file"]).read_text(encoding="utf-8-sig"))
            self.assertEqual(rep["patient_key"], ["MA_BN"])
            self.assertEqual([r[:2] for r in deid[1:]], [["E0001", "P0001"], ["E0002", "P0001"], ["E0003", "P0002"]])
            epi = self._rows(Path(rep["key_episodes_file"]).read_text(encoding="utf-8-sig"))
            self.assertEqual(epi, [["episode_pseudonym", "column", "original", "patient_pseudonym"],
                                   ["E0001", "MA_LK", "LK1", "P0001"], ["E0002", "MA_LK", "LK2", "P0001"],
                                   ["E0003", "MA_LK", "LK3", "P0002"]])
            self.assertEqual(len(self._rows(Path(rep["key_file"]).read_text(encoding="utf-8-sig"))), 3)

    def test_episode_id_keys_only_without_patient_id_or_name(self):
        table = [["Số vào viện", "Tuổi"], ["VV1", "67"], ["VV1", "67"], ["VV2", "55"]]
        rep, deid, _ = self._run(table)
        self.assertEqual(rep["patient_key"], ["Số vào viện"])
        self.assertEqual([r[0] for r in self._rows(deid)[1:]], ["E0001", "E0001", "E0002"])

    # W3: unlisted ID-like headers are dropped; clinical codes are kept
    def test_unlisted_id_like_headers(self):
        drop = ["ID", "Mã khám bệnh", "Mã đợt điều trị", "Số phiếu", "Lab ID", "sample_id"]
        keep = ["Mã ICD", "Mã bệnh", "Mã thuốc", "Mã dịch vụ", "Mã xét nghiệm", "Mã LOINC", "Mã ATC"]
        rows = [["x"] * len(drop + keep)]
        _, _, reasons = deidentify._classify_full(drop + keep, rows)
        acts = deidentify.classify_columns(drop + keep, rows)
        for i, h in enumerate(drop):
            self.assertEqual(acts[h], "drop", h)
            self.assertEqual(reasons[i], "unlisted ID-like header", h)
        for h in keep:
            self.assertEqual(acts[h], "keep", h)

    # W3 minor: --header-row on a data row is refused without printing the row
    def test_header_row_on_data_row_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "h.csv"
            with src.open("w", encoding="utf-8-sig", newline="") as fh:
                csv.writer(fh).writerows([["Họ và tên", "CCCD"], ["Nguyễn Văn An", "079123456789"]])
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = deidentify.main([str(src), "--header-row", "2"])
            self.assertEqual(code, 2)
            self.assertIn("row 2 looks like data, not a header", err.getvalue())
            self.assertNotIn("079123456789", err.getvalue())
            self.assertNotIn("Nguyễn", err.getvalue())
            self.assertEqual(sorted(x.name for x in Path(t).iterdir()), ["h.csv"])

    def test_record_id_values_absent_from_deid(self):
        table = [["Mã số bệnh nhân", "Số BA", "Mã LK", "Tuổi", "Thôn/xóm"],
                 ["MS-0001", "BA24-777", "LK998877", "67", "Xóm Đông"],
                 ["MS-0002", "BA24-778", "LK998878", "55", "Thôn Tây"]]
        rep, deid, key = self._run(table)
        for secret in ("MS-0001", "BA24-777", "LK998877", "Xóm Đông", "Thôn Tây"):
            self.assertNotIn(secret, deid)
            self.assertIn(secret, key)
        self.assertEqual([r[0] for r in self._rows(deid)[1:]], ["P0001", "P0002"])

    def test_same_patient_shares_pseudonym(self):
        table = [["Mã BN", "Họ và tên", "Tuổi", "Lần khám"],
                 ["BN001", "Nguyễn Văn An", "67", "1"], ["BN002", "Trần Thị Bình", "55", "1"],
                 ["BN001", "Nguyễn Văn An", "67", "2"]]
        rep, deid, key = self._run(table)
        self.assertEqual([r[0] for r in self._rows(deid)[1:]], ["P0001", "P0002", "P0001"])
        self.assertEqual(self._rows(key), [["pseudonym", "Mã BN", "Họ và tên"], ["P0001", "BN001", "Nguyễn Văn An"],
                                           ["P0002", "BN002", "Trần Thị Bình"]])

    def test_rows_without_identifier_values_get_own_pseudonym(self):
        table = [["Mã BN", "Tuổi"], ["", "67"], ["", "55"]]
        rep, deid, key = self._run(table)
        self.assertEqual([r[0] for r in self._rows(deid)[1:]], ["P0001", "P0002"])

    def test_keep_columns_report_suspect_value_counts(self):
        table = [["Tuổi", "Ghi chú"], ["67", "liên hệ 0903 123 456"], ["55", "ổn"], ["40", "ổn"], ["30", "ổn"],
                 ["20", "ổn"]]
        rep, deid, _ = self._run(table, header_row=1)
        self.assertEqual(rep["columns"], {"Tuổi": "keep", "Ghi chú": "keep"})
        self.assertEqual(rep["suspect_values"], {"Tuổi": 0, "Ghi chú": 1})
        self.assertNotIn("0903", json.dumps(rep, ensure_ascii=False))

    # I10: missing / unreadable input -> stderr + exit 2
    def test_main_missing_file_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = deidentify.main([str(Path(t) / "nope.csv")])
            self.assertEqual(code, 2)
            self.assertIn("deidentify:", err.getvalue())

    def test_main_unreadable_file_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "latin.csv"
            src.write_bytes(b"H\xe9 t\xean\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(deidentify.main([str(src)]), 2)
            self.assertIn("deidentify:", err.getvalue())

    def test_main_empty_file_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "e.csv"
            src.write_text("", encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(deidentify.main([str(src)]), 2)
            self.assertIn("empty file", err.getvalue())

    def test_blank_headers_do_not_leak(self):
        rep, deid, key = self._run([["Tuổi", "", ""], ["67", "079123456789", "x"], ["55", "079987654321", "y"]],
                                   header_row=1)
        self.assertEqual(rep["columns"], {"Tuổi": "keep", "col_2": "drop", "col_3": "keep"})
        self.assertNotIn("079123456789", deid)
        self.assertIn("079123456789", key)

    def test_duplicate_headers_do_not_leak(self):
        rep, deid, key = self._run([["Ghi chú", "Ghi chú"], ["ok", "079123456789"], ["hi", "079987654321"]],
                                   header_row=1)
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
                rep = deidentify.deidentify_csv(src, Path(t), header_row=1)
            self.assertEqual(rep["rows"], 1)
            self.assertIn("only the first sheet 'Main' was read; 1 other sheet(s) ignored", err.getvalue())


if __name__ == "__main__":
    unittest.main()
