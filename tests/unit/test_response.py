import contextlib
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import _paths  # noqa: F401
import gate
import init_project
import response
from crolib import drafts

RES = {"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified", "label": "adjusted OR", "value": 1.42,
       "ci": [1.05, 1.91], "n": 749, "kind": "or", "source_file": "05_analysis/output/log.txt", "locator": "line 1",
       "raw": "R-A1-001 value=1.42"}
DRAFTS = {
    "02-introduction.md": "# Introduction\n\nReadmission after a diabetes admission is common (fictional).\n",
    "03-methods.md": "# Methods\n\n## Participants\n\nAdults admitted with type 2 diabetes were included.\n",
    "04-results.md": "# Results\n\nThe adjusted OR was {{R-A1-001.full}}.\n",
    "05-discussion.md": "# Discussion\n\nHigher HbA1c was associated with readmission.\n",
}
COMMENTS = """Editor
1. Please shorten the abstract.

Reviewer 1
1. The exclusion criteria are unclear.
2. Please add a subgroup analysis by sex.

Reviewer #2
The discussion overstates the findings.

Please discuss residual confounding.
"""
CLEAN = """# Response to reviewers

## E1 (editor)
> Please shorten the abstract.

No change because the abstract already meets the journal's limit.

## R1.1
> The exclusion criteria are unclear.

We have clarified the exclusion criteria.
[[CHANGE: 06_writing/manuscript/03-methods.md | "Patients transferred from another hospital were excluded."]]

## R1.2
No change because a subgroup analysis by sex was not planned.

## R2.1
No change because the discussion already reports the adjusted OR of {{R-A1-001}} as an association.

## R2.2
We have added residual confounding to the limitations.
[[CHANGE: 06_writing/manuscript/05-discussion.md | "Residual confounding may remain."]]
"""


def open_g4(p: Path, d: str = "manuscript") -> None:
    files = {f.relative_to(p).as_posix(): gate.sha256(f) for f in drafts.tracked_files(p, d)}
    (p / "reviews" / "audit.json").write_text(json.dumps({"deliverable": d, "deliverables": [d], "at": "t",
                                                          "blocks": 0, "warns": 0, "files": files}), encoding="utf-8")
    gate.open_gate(p, "G4", by="Example author")


class TestResponse(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        p = self.p = init_project.create(self.t / "p", "Fictional cohort", "manuscript", "cohort", "en", "en")
        (p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": [RES]}), encoding="utf-8")
        d = p / "06_writing" / "manuscript"
        d.mkdir(parents=True, exist_ok=True)
        for name, text in DRAFTS.items():
            (d / name).write_text(text, encoding="utf-8", newline="\n")
        self.comments = p / "00_inputs" / "reviews.txt"
        self.comments.parent.mkdir(parents=True, exist_ok=True)
        self.comments.write_text(COMMENTS, encoding="utf-8")
        open_g4(p)

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = response.main([str(self.p), *argv])
        return code, out.getvalue(), err.getvalue()

    def respond(self, text):
        (self.p / response.RESPONSE).write_text(text, encoding="utf-8", newline="\n")

    def edit(self, name, extra):
        f = self.p / "06_writing" / "manuscript" / name
        f.write_text(f.read_text(encoding="utf-8") + extra, encoding="utf-8", newline="\n")

    def made_changes(self):
        self.edit("03-methods.md", "Patients transferred from another hospital were excluded.\n")
        self.edit("05-discussion.md", "\n## Limitations\n\nResidual confounding may remain.\n")

    def blocks(self):
        return [f"{c} {loc}: {m}" for c, lv, loc, m in response.check(self.p) if lv == "block"]

    def test_split_ids_and_text(self):
        items = response.split_comments(COMMENTS)
        self.assertEqual([(i["id"], i["who"]) for i in items],
                         [("E1", "Editor"), ("R1.1", "Reviewer 1"), ("R1.2", "Reviewer 1"), ("R2.1", "Reviewer 2"),
                          ("R2.2", "Reviewer 2")])
        self.assertEqual(items[2]["text"], "Please add a subgroup analysis by sex.")
        self.assertEqual([i["id"] for i in response.split_comments("Reviewer 1:\n- a\n- b\n\nReferee 2\n(1) c\n")],
                         ["R1.1", "R1.2", "R2.1"])
        self.assertEqual(len(response.split_comments("<!-- Fictional: invented for a test. -->\n" + COMMENTS)), 5)

    def test_init_snapshots_and_refuses_twice(self):
        code, out, err = self.cli("init", str(self.comments))
        self.assertEqual(code, 0, out + err)
        data = json.loads((self.p / response.COMMENTS).read_text(encoding="utf-8"))
        self.assertEqual((data["deliverable"], data["approved"], len(data["items"])), ("manuscript", True, 5))
        self.assertEqual(data["source"], "00_inputs/reviews.txt")
        self.assertEqual(set(data["submitted"]), {f"06_writing/manuscript/{n}" for n in DRAFTS})
        for rel, sha in data["submitted"].items():
            self.assertEqual(gate.sha256(self.p / response.SUBMITTED / rel), sha)
        self.assertEqual(self.cli("init", str(self.comments))[0], 1)

    def test_init_needs_the_approved_version(self):
        self.edit("04-results.md", "Edited after approval.\n")
        code, out, _ = self.cli("init", str(self.comments))
        self.assertEqual(code, 1)
        self.assertIn("--unapproved", out)
        self.assertEqual(self.cli("init", str(self.comments), "--unapproved")[0], 0)
        self.assertIs(json.loads((self.p / response.COMMENTS).read_text(encoding="utf-8"))["approved"], False)
        self.assertEqual(response.main([str(self.p), "init"]), 2)

    def test_clean_response_passes_only_after_the_edits(self):
        self.cli("init", str(self.comments))
        self.respond(CLEAN)
        before = self.blocks()
        self.assertEqual(len(before), 2, before)
        self.assertTrue(all("is not in the current" in b for b in before), before)
        self.made_changes()
        self.assertEqual(response.check(self.p), [])
        self.assertEqual(self.cli("check")[0], 0)

    def test_claim_without_locator_and_unchanged_quote_block(self):
        self.cli("init", str(self.comments))
        self.made_changes()
        self.respond(CLEAN.replace(
            'We have clarified the exclusion criteria.\n[[CHANGE: 06_writing/manuscript/03-methods.md | '
            '"Patients transferred from another hospital were excluded."]]',
            "We have revised the Methods to clarify the exclusion criteria.").replace(
            "No change because a subgroup analysis by sex was not planned.",
            'We have clarified the population.\n[[CHANGE: 06_writing/manuscript/03-methods.md | '
            '"Adults admitted with type 2 diabetes were included."]]'))
        b = " | ".join(self.blocks())
        self.assertIn("R1.1: the response says the manuscript was changed but gives no [[CHANGE", b)
        self.assertIn("R1.2: \"Adults admitted with type 2 diabetes were included.\" was already in the submitted", b)

    def test_numbers_masks_new_analysis_unknown_and_missing(self):
        self.cli("init", str(self.comments))
        self.made_changes()
        self.respond(CLEAN.replace(
            "No change because a subgroup analysis by sex was not planned.",
            "NEW-ANALYSIS: subgroup analysis by sex, requested by Reviewer 1").replace(
            "No change because the discussion already reports the adjusted OR of {{R-A1-001}} as an association.",
            "The odds ratio was 1.42 (see lines 120–125 and our reply to R1.2), as {{R-A1-001}} shows; "
            "the CI was 2.5 wide.").split("## R2.2")[0] + "## R9.1\nNo change because this is a test.\n")
        found = response.check(self.p)
        b = " | ".join(f"{c} {m}" for c, lv, _, m in found if lv == "block")
        self.assertIn("E-NUM R2.1: 2.5 is not in the results ledger", b)
        for tok in ("1.42 is", "120 is", "125 is", "1.2 is"):
            self.assertNotIn(tok, b)
        self.assertIn("E-RESP R1.2: NEW-ANALYSIS awaits the author's decision", b)
        self.assertIn("R9.1 is not a comment", b)
        self.assertIn("R2.2 has no response", b)
        warns = [m for c, lv, _, m in found if lv == "warn"]
        self.assertTrue(any(m.startswith("R2.1: no change and no") for m in warns), warns)
        self.assertEqual(self.cli("check")[0], 1)

    def test_check_without_init_is_an_input_error(self):
        with self.assertRaises(response.InputError):
            response.check(self.p)
        self.assertEqual(self.cli("check")[0], 2)

    def test_build_needs_a_clean_check_and_g4_after_the_revision(self):
        self.cli("init", str(self.comments))
        self.respond(CLEAN)
        code, out, _ = self.cli("build")
        self.assertEqual(code, 1)
        self.assertIn("is not in the current", out)
        self.made_changes()
        code, out, _ = self.cli("build")
        self.assertEqual(code, 1)            # the drafts changed: G4 is closed until a fresh audit
        self.assertIn("G4", out)
        open_g4(self.p)
        code, out, err = self.cli("build")
        self.assertEqual(code, 0, out + err)
        with zipfile.ZipFile(self.p / response.LETTER) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        for s in ("Response to the editor and reviewers", "R1.1", "Participants", "Limitations", "1.42",
                  "Patients transferred from another hospital were excluded."):
            self.assertIn(s, xml)
        self.assertNotIn("[[CHANGE", xml)


if __name__ == "__main__":
    unittest.main()
