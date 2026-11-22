import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ROOT
import init_project
import worklog
from crolib import drafts, reviews

CH3 = "# CHƯƠNG 3. KẾT QUẢ\n\nMô tả mẫu nghiên cứu theo nhóm.\n"
CH4 = "# CHƯƠNG 4. BÀN LUẬN\n\nKết quả gợi ý có liên quan giữa hai biến trong mẫu nghiên cứu.\n"
ASSUME = ("# Câu hỏi\n\n**Giả định / Assumptions** (dự án mô phỏng;\ntác giả xác nhận):\n"
          "- HbA1c được ghi nhận thường quy\n  trong hồ sơ.\n- HIS ghi ngày nhập viện.\n\nĐoạn khác.\n")


def checklist(p: Path, absent: int = 0) -> None:
    items = {f"x{i}": ({"status": "absent"} if i < absent else {"status": "na", "reason": "t"}) for i in range(6)}
    (p / "reviews" / "guideline-checklist.json").write_text(json.dumps(
        {"guideline": "TEST-GL", "deliverable": "thesis", "items": items}), encoding="utf-8")


def reports(p: Path, deliverable="thesis", digest=None, request=None, **s) -> None:
    digest = digest or drafts.digest(p, deliverable)
    vals = dict.fromkeys(reviews.CRITERIA, 2)
    vals.update(s)
    for agent, (rel, crits) in reviews.REVIEWERS.items():
        block = {"deliverable": deliverable, **{c: vals[c] for c in crits}}
        req = f"NEW-ANALYSIS: {request}\n" if request and agent == "statistical-reviewer" else ""
        (p / rel).write_text(f"STATUS: FINDINGS\nFINDINGS\n| code | location | fix |\n{req}"
                             f"drafts-digest: {deliverable} {digest}\n```scores\n{json.dumps(block)}\n```\n", encoding="utf-8")

BOX = ("# Tính cỡ mẫu\n\n> **Assumptions / Giả định.** Theo yêu cầu của tác giả, tham số không có\n"
       "> nguồn thì ghi GIẢ ĐỊNH và làm luôn.\n> Đây là giả định rủi ro nhất.\n\n## 1. Tóm tắt\n")
BOX_BULLETS = "> **Giả định / Assumptions**:\n> - Tỷ lệ nền 20%.\n>   theo ngoại suy.\n> - OR 1,5.\n\nHết.\n"


class TestWorklog(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "T", "thesis-masters", "cohort", "vi", "vi")
        d = self.p / "06_writing" / "thesis"
        d.mkdir(parents=True, exist_ok=True)
        (d / "ch3-results.md").write_text(CH3, encoding="utf-8")
        (d / "ch4-discussion.md").write_text(CH4, encoding="utf-8")
        checklist(self.p)

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = worklog.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def score(self, n, **s):
        reports(self.p, **s)
        return worklog.score(self.p, "thesis", n)

    def test_digest_covers_drafts_only(self):
        code, out, _ = self.cli("digest", str(self.p), "thesis")
        self.assertEqual(code, 0)
        self.assertRegex(out.strip(), r"^drafts-digest: thesis [0-9a-f]{64}$")
        before = drafts.digest(self.p, "thesis")
        (self.p / "06_writing/thesis/ch3-results.rendered.md").write_text("x", encoding="utf-8")
        self.assertEqual(drafts.digest(self.p, "thesis"), before)
        (self.p / "06_writing/thesis/ch4-discussion.md").write_text(CH4 + "\nThêm.\n", encoding="utf-8")
        self.assertNotEqual(drafts.digest(self.p, "thesis"), before)
        self.assertEqual(self.cli("digest", str(self.p), "manuscript")[0], 2)

    def test_round_one_keeps_and_snapshots(self):
        reports(self.p, structure=1)
        code, out, err = self.cli("score", str(self.p), "thesis", "--round", "1")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip().splitlines()[-1], "KEEP")
        e = json.loads((self.p / "reviews/worklog.json").read_text(encoding="utf-8"))["rounds"][0]
        self.assertEqual((e["round"], e["kept"], e["max"]), (1, True, 16))
        self.assertEqual(e["total"], sum(e["scores"].values()))
        self.assertEqual(list(e["scores"]), list(reviews.CRITERIA))
        snap = self.p / "reviews/rounds/thesis/r1"
        self.assertEqual((snap / "ch4-discussion.md").read_bytes(),
                         (self.p / "06_writing/thesis/ch4-discussion.md").read_bytes())
        self.assertTrue((snap / "reviews" / "consistency.md").is_file())
        self.assertTrue((snap / "reviews" / "guideline-checklist.json").is_file())

    def test_decision_rules(self):
        self.assertEqual(self.score(1, structure=1, claim_scope=1)["decision"], "KEEP")
        self.assertEqual(self.score(2, structure=2, claim_scope=1)["decision"], "KEEP")
        self.assertEqual(self.score(3, structure=2, claim_scope=2)["decision"], "STOP")    # round 3

    def test_lower_reverts(self):
        self.score(1, structure=1)
        self.assertEqual(self.score(2, structure=1, claim_scope=0)["decision"], "REVERT")
        reports(self.p)
        with self.assertRaises(worklog.UsageError):
            worklog.score(self.p, "thesis", 3)                                             # loop has stopped

    def test_equal_with_loss_reverts_equal_without_stops(self):
        self.score(1, structure=1)
        self.assertEqual(self.score(2, structure=2, claim_scope=1)["decision"], "REVERT")
        shutil.rmtree(self.p / "reviews" / "rounds")
        (self.p / "reviews" / "worklog.json").unlink()
        self.score(1, structure=1)
        self.assertEqual(self.score(2, structure=1)["decision"], "STOP")

    def test_scripted_criteria_win(self):
        checklist(self.p, absent=4)
        e = self.score(1, guideline=2)
        self.assertEqual(e["scores"]["guideline"], 0)
        self.assertTrue(any("script measured 0" in n for n in e["notes"]))
        checklist(self.p, absent=2)
        shutil.rmtree(self.p / "reviews" / "rounds")
        (self.p / "reviews" / "worklog.json").unlink()
        self.assertEqual(self.score(1)["scores"]["guideline"], 1)

    def test_prose_score_zero_on_p00(self):
        dense = ROOT / "tests" / "scenarios" / "fixtures" / "vi-dense-prose" / "06_writing" / "thesis" / "ch4-discussion.md"
        shutil.copyfile(dense, self.p / "06_writing" / "thesis" / "ch4-discussion.md")
        self.assertEqual(worklog.prose_score(self.p, "thesis")[0], 0)

    def test_refusals_exit_2(self):
        self.assertEqual(self.cli("score", str(self.p), "thesis", "--round", "1")[0], 2)    # no reports
        reports(self.p, digest="0" * 64)
        code, _, err = self.cli("score", str(self.p), "thesis", "--round", "1")
        self.assertEqual(code, 2)
        self.assertIn("does not match", err)
        reports(self.p)
        self.assertEqual(self.cli("score", str(self.p), "thesis", "--round", "2")[0], 2)
        (self.p / "reviews" / "scientific-editor.md").write_text("STATUS: PASS\n", encoding="utf-8")
        self.assertEqual(self.cli("score", str(self.p), "thesis", "--round", "1")[0], 2)
        self.assertFalse((self.p / "reviews" / "worklog.json").exists())

    def test_revert_restores_exactly(self):
        self.score(1, structure=1)
        d = self.p / "06_writing" / "thesis"
        (d / "ch4-discussion.md").write_text(CH4 + "\nĐoạn mới của vòng hai.\n", encoding="utf-8")
        (d / "ch9-extra.md").write_text("# Thêm\n", encoding="utf-8")
        self.assertEqual(self.score(2, structure=1, claim_scope=0)["decision"], "REVERT")
        code, out, _ = self.cli("revert", str(self.p), "thesis")
        self.assertEqual(code, 0)
        self.assertEqual((d / "ch4-discussion.md").read_text(encoding="utf-8"), CH4)
        self.assertFalse((d / "ch9-extra.md").exists())
        self.assertTrue((self.p / "reviews/rounds/thesis/r2/ch9-extra.md").is_file())
        ev = json.loads((self.p / "reviews/worklog.json").read_text(encoding="utf-8"))["events"][-1]
        self.assertEqual((ev["event"], ev["to_round"], ev["removed"]), ("revert", 1, ["ch9-extra.md"]))

    def test_none_request_recorded_by_an_older_version_is_not_listed(self):
        self.score(1, request="phân tích dưới nhóm theo giới tính")
        log = worklog.load_log(self.p)
        log["rounds"][0]["requests"].append({"agent": "scientific-editor", "text": "none — wording fixes only"})
        text = worklog.decisions_text(self.p, log)
        self.assertIn("phân tích dưới nhóm theo giới tính", text)
        self.assertNotIn("wording fixes only", text)

    def test_requests_assumptions_waivers_to_author_decisions(self):
        (self.p / "01_question").mkdir(exist_ok=True)
        (self.p / "01_question" / "question.md").write_text(ASSUME, encoding="utf-8")
        with (self.p / "decisions.md").open("a", encoding="utf-8") as fh:
            fh.write("\n- WAIVE G4: báo cáo nội bộ, 2026-11-22\n")
        e = self.score(1, request="phân tích dưới nhóm theo giới tính cho mục tiêu 2")
        self.assertEqual(e["requests"], [{"agent": "statistical-reviewer",
                                          "text": "phân tích dưới nhóm theo giới tính cho mục tiêu 2"}])
        code, out, _ = self.cli("decisions", str(self.p))
        self.assertEqual(code, 0, out)
        text = (self.p / "out" / "author-decisions.md").read_text(encoding="utf-8")
        self.assertIn("phân tích dưới nhóm theo giới tính", text)
        self.assertIn("HbA1c được ghi nhận thường quy trong hồ sơ.", text)
        self.assertIn("01_question/question.md:5", text)
        self.assertIn("WAIVE G4: báo cáo nội bộ, 2026-11-22", text)
        self.assertEqual(self.cli("decisions", str(self.p))[0], 0)
        (self.p / "out" / "author-decisions.md").write_text(text + "\nQuyết định: không làm.\n", encoding="utf-8")
        self.assertEqual(self.cli("decisions", str(self.p))[0], 1)
        self.assertIn("không làm", (self.p / "out" / "author-decisions.md").read_text(encoding="utf-8"))
        self.assertTrue((self.p / "reviews" / "tmp" / "author-decisions.new.md").is_file())

    def test_ordered_and_required(self):
        files, missing, req = drafts.ordered(self.p, "thesis")
        self.assertEqual([f.name for f in files], ["ch3-results.md", "ch4-discussion.md"])
        self.assertIn("00-dat-van-de.md", missing)
        self.assertEqual(req, ["ch2-methods.md", "05-ket-luan.md"])
        (self.p / "06_writing/thesis/order.txt").write_text("# order\nch4-discussion.md\nch3-results.md\n", encoding="utf-8")
        self.assertEqual([f.name for f in drafts.ordered(self.p, "thesis")[0]], ["ch4-discussion.md", "ch3-results.md"])
        self.assertTrue(drafts.results_bearing("06_writing/thesis/ch4-discussion.md"))
        self.assertFalse(drafts.results_bearing("06_writing/thesis/ch2-methods.md"))
        self.assertTrue(drafts.is_literature("06_writing/thesis/ch1-literature-review.md"))

    def test_assumptions_blockquote_and_both_heading_orders(self):
        (self.p / "03_protocol").mkdir(exist_ok=True)
        (self.p / "03_protocol" / "sample-size.md").write_text(BOX, encoding="utf-8")
        (self.p / "03_protocol" / "sap.md").write_text(BOX_BULLETS, encoding="utf-8")
        found = worklog.assumptions(self.p)
        box = [t for loc, t in found if loc.startswith("03_protocol/sample-size.md")]
        self.assertEqual(len(box), 1)
        self.assertIn("tham số không có nguồn thì ghi GIẢ ĐỊNH", box[0])
        self.assertIn("giả định rủi ro nhất", box[0])
        sap = [t for loc, t in found if loc.startswith("03_protocol/sap.md")]
        self.assertEqual(sap, ["Tỷ lệ nền 20%. theo ngoại suy.", "OR 1,5."])

    def test_checklist_for_another_deliverable_refused(self):
        with self.assertRaises(worklog.UsageError) as cm:
            worklog.guideline_score(self.p, "manuscript")    # the legacy file is the thesis's: ignored
        self.assertIn("reviews/guideline-checklist-manuscript.json not found", str(cm.exception))
        self.assertEqual(worklog.guideline_score(self.p, "thesis")[0], 2)

    def test_per_deliverable_checklists_scored_and_snapshotted_apart(self):
        (self.p / "reviews" / "guideline-checklist.json").unlink()
        for d, absent in (("thesis", 0), ("manuscript", 5)):
            items = {f"x{i}": ({"status": "absent"} if i < absent else {"status": "na", "reason": "t"})
                     for i in range(6)}
            (self.p / "reviews" / f"guideline-checklist-{d}.json").write_text(json.dumps(
                {"guideline": "TEST-GL", "deliverable": d, "items": items}), encoding="utf-8")
        self.assertEqual(worklog.guideline_score(self.p, "thesis")[0], 2)
        self.assertEqual(worklog.guideline_score(self.p, "manuscript")[0], 0)
        reports(self.p)
        worklog.score(self.p, "thesis", 1)
        snap = self.p / "reviews/rounds/thesis/r1/reviews/guideline-checklist.json"
        self.assertEqual(snap.read_bytes(), (self.p / "reviews" / "guideline-checklist-thesis.json").read_bytes())

    def test_bad_log_shape_exit_2(self):
        log = self.p / "reviews" / "worklog.json"
        for bad in ('{"rounds": [1]}', '{"rounds": [{"round": "1", "deliverable": "thesis"}]}',
                    '{"rounds": [{"round": 1, "deliverable": "essay"}]}', '{"rounds": [], "events": {}}'):
            log.write_text(bad, encoding="utf-8")
            reports(self.p)
            self.assertEqual(self.cli("score", str(self.p), "thesis", "--round", "1")[0], 2, bad)
            self.assertEqual(self.cli("revert", str(self.p), "thesis")[0], 2, bad)
            self.assertEqual(self.cli("decisions", str(self.p))[0], 2, bad)

    def test_revert_validates_log_before_touching_files(self):
        self.score(1, structure=1)
        d = self.p / "06_writing" / "thesis"
        (d / "ch4-discussion.md").write_text("changed\n", encoding="utf-8")
        (self.p / "reviews" / "worklog.json").write_text('{"rounds": "x"}', encoding="utf-8")
        self.assertEqual(self.cli("revert", str(self.p), "thesis")[0], 2)
        self.assertEqual((d / "ch4-discussion.md").read_text(encoding="utf-8"), "changed\n")

    def test_log_written_atomically(self):
        self.score(1)
        self.assertEqual([p.name for p in (self.p / "reviews").glob("worklog.json*")], ["worklog.json"])

    def test_scores_must_be_plain_ints(self):
        for bad in (1.0, True, "2", 3):
            reports(self.p, structure=bad)
            code, _, err = self.cli("score", str(self.p), "thesis", "--round", "1")
            self.assertEqual(code, 2, bad)
            self.assertIn("must be 0, 1 or 2", err)
        self.assertFalse((self.p / "reviews" / "worklog.json").exists())

    def test_malformed_and_duplicate_scores_blocks(self):
        reports(self.p)
        rep = self.p / "reviews" / "scientific-editor.md"
        good = rep.read_text(encoding="utf-8")
        rep.write_text(good.replace("```scores\n", "```scores\n{oops", 1), encoding="utf-8")
        code, _, err = self.cli("score", str(self.p), "thesis", "--round", "1")
        self.assertEqual(code, 2)
        self.assertIn("malformed", err)
        rep.write_text(good + good[good.index("```scores"):], encoding="utf-8")
        code, _, err = self.cli("score", str(self.p), "thesis", "--round", "1")
        self.assertEqual(code, 2)
        self.assertIn("more than one", err)
        self.assertFalse((self.p / "reviews" / "worklog.json").exists())

    def test_revert_to_a_reverted_round_refused(self):
        self.score(1, structure=1)
        self.assertEqual(self.score(2, structure=1, claim_scope=0)["decision"], "REVERT")
        code, _, err = self.cli("revert", str(self.p), "thesis", "--to", "2")
        self.assertEqual(code, 2)
        self.assertIn("reverted", err)
