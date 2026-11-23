import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import lint_prose

SCRIPT = ORCH_SCRIPTS / "lint_prose.py"

VI_SLOP = ("Mô hình này không chỉ giảm tải cho bác sĩ mà còn cải thiện kết quả điều trị.\n"
           "Nó không chỉ nhanh mà còn chính xác. Quy trình đóng vai trò quan trọng trong thực hành.")
HEDGED = ("Kết quả có thể gợi ý rằng nhóm can thiệp có xu hướng hồi phục nhanh hơn. "
          "Mẫu được thu thập từ hồ sơ và các biến được ghi nhận bởi hai người. "
          "These findings may suggest a modest association, which was assessed by two reviewers.")
CLEAN = ("Chúng tôi thu thập hồ sơ của 120 bệnh nhân điều trị tại khoa nội trong năm 2025 và ghi nhận "
         "tuổi, giới và thời gian nằm viện cho từng trường hợp.\n\n"
         "Nhóm can thiệp có thời gian nằm viện ngắn hơn nhóm chứng ở mức nhỏ.")


def run_cli(*args, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True,
                          env=env, timeout=60)


class TestFindHits(unittest.TestCase):
    def test_vi_slop_codes_and_lines(self):
        hits = lint_prose.find_hits(VI_SLOP, "vi")
        codes = [c for _, c, _ in hits]
        self.assertEqual(codes.count("P01"), 2)
        self.assertEqual(codes.count("P02"), 1)
        lines = {c: [ln for ln, cc, _ in hits if cc == c] for c in ("P01", "P02")}
        self.assertEqual(lines["P01"], [1, 2])
        self.assertEqual(lines["P02"], [2])

    def test_en_patterns(self):
        text = "This not only reduces cost but also improves care. It plays a pivotal role. We delve into the landscape."
        codes = {c for _, c, _ in lint_prose.find_hits(text, "en")}
        self.assertTrue({"P01", "P02", "P12"} <= codes)

    def test_hedges_and_passive_not_counted(self):
        self.assertEqual(lint_prose.find_hits(HEDGED, "auto"), [])

    def test_robust_statistical_is_exempt(self):
        self.assertEqual(lint_prose.find_hits("We used robust standard errors clustered by ward.", "en"), [])
        self.assertTrue(lint_prose.find_hits("This is a robust and seamless solution.", "en"))

    def test_dashes(self):
        text = "A — B — C — D. Range 5–10 mg is fine."
        self.assertIn("P07", [c for _, c, _ in lint_prose.find_hits(text, "en")])
        self.assertNotIn("P07", [c for _, c, _ in lint_prose.find_hits("Dose 5–10 mg — twice daily.", "en")])

    def test_openers(self):
        text = "Kết quả khác biệt.\n\nTóm lại, mô hình hiệu quả. Đáng chú ý, nhóm A cao hơn."
        codes = [c for _, c, _ in lint_prose.find_hits(text, "vi")]
        self.assertIn("P06", codes)
        self.assertIn("P10", codes)

    def test_vague_attribution_needs_citation(self):
        self.assertTrue(lint_prose.find_hits("Studies show that the drug works.", "en"))
        self.assertEqual(lint_prose.find_hits("Studies show that the drug works [@lee2020].", "en"), [])

    def test_skipped_blocks(self):
        text = ("# Không chỉ A mà còn B\n\n| không chỉ A mà còn B |\n\n<!-- không chỉ A mà còn B -->\n\n"
                "Giá trị {{R-A1-001.full}} được ghi nhận.")
        self.assertEqual(lint_prose.find_hits(text, "vi"), [])

    def test_bold_label(self):
        hits = lint_prose.find_hits("Chúng tôi thấy **Điểm mấu chốt:** nhóm A tốt hơn.", "vi")
        self.assertIn("P15", [c for _, c, _ in hits])
        self.assertEqual(lint_prose.find_hits("**Background:** We studied 100 patients.", "en"), [])


class TestWordCount(unittest.TestCase):
    def test_placeholder_one_word_and_headings_excluded(self):
        text = "# Title heading here\n\nOR {{R-A1-001}} was found <!-- hidden words here -->.\n"
        self.assertEqual(lint_prose.word_count(text), 4)

    def test_structured_abstract(self):
        text = "# Abstract\n\n**Background:** Diabetes is common.\n\n**Methods:** We reviewed 100 charts.\n"
        self.assertEqual(lint_prose.word_count(text), 3 + 4)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_block_and_exit_1(self):
        p = self.write("slop.md", VI_SLOP)
        r = run_cli(p)
        out = r.stdout.decode("utf-8")
        self.assertEqual(r.returncode, 1, out)
        self.assertIn("P00 block", out)
        self.assertIn("P01 warn", out)
        self.assertIn("lint_prose:", out)

    def test_clean_exit_0(self):
        p = self.write("clean.md", CLEAN)
        r = run_cli(p)
        self.assertEqual(r.returncode, 0, r.stdout.decode("utf-8"))
        self.assertNotIn("block", r.stdout.decode("utf-8"))

    def test_json(self):
        p = self.write("slop.md", VI_SLOP)
        r = run_cli(p, "--json")
        data = json.loads(r.stdout.decode("utf-8"))
        self.assertTrue(any(f["code"] == "P01" for f in data["findings"]))

    def test_count_words(self):
        p = self.write("abs.md", "# H\n\n**Background:** one two\n\nx {{R-A1-001}} <!-- c c c -->\n")
        r = run_cli("--count-words", p)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.decode("utf-8").strip(), "words: 4")

    def test_missing_file_exit_2(self):
        r = run_cli(self.dir / "nope.md")
        self.assertEqual(r.returncode, 2)

    def test_cp1252_console_does_not_crash(self):
        p = self.write("vi.md", VI_SLOP)
        r = run_cli(p, env_extra={"PYTHONIOENCODING": "cp1252"})
        self.assertEqual(r.returncode, 1)
        self.assertNotIn(b"Traceback", r.stderr)

    def test_slides_html(self):
        topic = self.write("a.html", "<html><body><section class='slide'><h2>Results</h2><p>x</p></section></body></html>")
        r = run_cli("--slides", topic)
        self.assertIn("S17 warn", r.stdout.decode("utf-8"))
        self.assertEqual(r.returncode, 0)
        claim = self.write("b.html", "<html><body><section class='slide'><h2>HbA1c &gt; 9% was associated "
                           "with more readmissions</h2><p>Details.</p></section></body></html>")
        r = run_cli("--slides", claim)
        self.assertNotIn("S17", r.stdout.decode("utf-8"))

    def test_slides_html_notes_excluded_and_s20_s21(self):
        html = ("<html><body><section class='slide'><h2>Drug X lowers readmissions</h2>"
                "<p>This chart shows the rates. The drug dramatically improves survival.</p>"
                "<aside class='notes'>This chart shows nothing; cures everything</aside></section></body></html>")
        p = self.write("c.html", html)
        out = run_cli("--slides", p).stdout.decode("utf-8")
        self.assertIn("S20 warn", out)
        self.assertIn("S21 warn", out)
        self.assertEqual(out.count("S20 warn"), 1)
        self.assertNotIn("cures", out)

    def test_nfd_input_matches(self):
        import unicodedata
        nfd = unicodedata.normalize("NFD", VI_SLOP)
        codes = [c for _, c, _ in lint_prose.find_hits(nfd, "vi")]
        self.assertEqual(codes.count("P01"), 2)
        self.assertEqual(codes.count("P02"), 1)
        self.assertEqual(lint_prose.word_count(nfd), lint_prose.word_count(VI_SLOP))
        p = self.write("nfd.md", nfd)
        self.assertEqual(run_cli(p).returncode, 1)

    def test_slides_plain_section_body_linted(self):
        p = self.write("e.html", "<html><body><section><h2>Methods</h2><p>This chart shows a drug that "
                       "cures all.</p><aside class='notes'>cures notes</aside></section></body></html>")
        out = run_cli("--slides", p).stdout.decode("utf-8")
        self.assertIn("S17 warn", out)
        self.assertIn("S20 warn", out)
        self.assertIn("S21 warn", out)

    def test_slides_heading_only_deck_body_linted(self):
        p = self.write("f.html", "<html><body><h2>Drug X lowers readmissions</h2><p>As shown above.</p>"
                       "<h2>Methods</h2><p>Text.</p></body></html>")
        out = run_cli("--slides", p).stdout.decode("utf-8")
        self.assertIn("S20 warn f.html:1", out.replace(str(self.dir) + os.sep, ""))
        self.assertIn("S17 warn", out)

    def test_slides_h1_deck_title_exempt_and_hype(self):
        p = self.write("g.html", "<html><body><section class='slide'><h1>Deck title</h1></section>"
                       "<section class='slide'><h2>Drug X lowers readmissions</h2>"
                       "<p>A revolutionary, groundbreaking and game-changing result.</p></section></body></html>")
        out = run_cli("--slides", p).stdout.decode("utf-8")
        self.assertNotIn("S17", out)
        self.assertIn("S21 warn", out)

    def test_slides_pptx_groups_and_tables(self):
        try:
            from pptx import Presentation
            from pptx.util import Inches
        except ImportError:
            self.skipTest("python-pptx not installed")
        prs = Presentation()
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.shapes.title.text = "Drug X lowers readmissions"
        grp = s.shapes.add_group_shape()
        tb = grp.shapes.add_textbox(Inches(1), Inches(1), Inches(3), Inches(1))
        tb.text_frame.text = "This chart shows the rates."
        tbl = s.shapes.add_table(1, 1, Inches(1), Inches(3), Inches(3), Inches(1)).table
        tbl.cell(0, 0).text = "The drug cures everything"
        p = self.dir / "h.pptx"
        prs.save(str(p))
        out = run_cli("--slides", p).stdout.decode("utf-8")
        self.assertIn("S20 warn", out)
        self.assertIn("S21 warn", out)

    def test_slides_pptx(self):
        try:
            from pptx import Presentation
        except ImportError:
            self.skipTest("python-pptx not installed")
        prs = Presentation()
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.shapes.title.text = "Methods"
        s.notes_slide.notes_text_frame.text = "This chart shows"
        p = self.dir / "d.pptx"
        prs.save(str(p))
        out = run_cli("--slides", p).stdout.decode("utf-8")
        self.assertIn("S17 warn", out)
        self.assertNotIn("S20", out)


CONSENT = ("# Phiếu đồng ý (hư cấu)\n\n"
           "Bạn sẽ được chia ngẫu nhiên hoá vào một trong hai nhóm và nhóm còn lại sẽ dùng giả dược (thuốc không có "
           "hoạt chất) trong suốt thời gian nghiên cứu kéo dài mười hai tháng tại bệnh viện cùng với các lần tái khám "
           "định kỳ mỗi tháng một lần.\n\n"
           "Phiếu này phải được ký trước khi tham gia.\n\n"
           "Nghiên cứu là mù đôi (cả bạn và bác sĩ đều không biết bạn ở nhóm nào).\n")


class TestConsentProfile(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.f = self.d / "consent-form.md"
        self.f.write_text(CONSENT, encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.d, ignore_errors=True)

    def test_codes_and_warn_only(self):
        res = lint_prose.lint_consent(str(self.f))
        codes = [(x["code"], x["line"]) for x in res["findings"]]
        self.assertIn(("CF01", 3), codes)
        self.assertIn(("CF02", 3), codes)
        self.assertIn(("CF03", 5), codes)
        self.assertTrue(all(x["level"] == "warn" for x in res["findings"]))
        msgs = " ".join(x["message"] for x in res["findings"])
        self.assertIn("ngẫu nhiên hoá", msgs)
        self.assertNotIn("giả dược", msgs)      # explained in the parenthesis right after it
        self.assertNotIn("mù đôi", msgs)

    def _cf02(self, text):
        self.f.write_text(text + "\n", encoding="utf-8")
        return [x["message"] for x in lint_prose.lint_consent(str(self.f))["findings"] if x["code"] == "CF02"]

    def test_jargon_accepts_both_hoa_spellings_and_nfd(self):
        import unicodedata
        for word in ("mã hóa", "mã hoá", "ngẫu nhiên hóa", "ngẫu nhiên hoá"):
            self.assertEqual(len(self._cf02(f"Dữ liệu được {word} khi lưu.")), 1, word)
        nfd = unicodedata.normalize("NFD", "Dữ liệu được mã hóa khi lưu.")
        self.assertEqual(len(self._cf02(nfd)), 1)

    def test_cli_exit_0_and_profiles(self):
        r = run_cli("--profile", "consent", self.f)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout.decode("utf-8")
        self.assertIn("CF03 warn", out)
        self.assertIn("consent profile", out)
        self.assertNotIn("CF0", run_cli(self.f).stdout.decode("utf-8"))
        self.assertEqual(run_cli("--profile", "consent", "--slides", self.f).returncode, 2)

    def test_english_sentence_limit(self):
        self.f.write_text("At each visit you answer a few short questions about your health and your treatment "
                          "during the study, which lasts one year.\n", encoding="utf-8")
        self.assertEqual([x["code"] for x in lint_prose.lint_consent(str(self.f))["findings"]], [])
        self.f.write_text(" ".join(["word"] * 26) + ".\n", encoding="utf-8")
        self.assertEqual([x["code"] for x in lint_prose.lint_consent(str(self.f))["findings"]], ["CF01"])


if __name__ == "__main__":
    unittest.main()
