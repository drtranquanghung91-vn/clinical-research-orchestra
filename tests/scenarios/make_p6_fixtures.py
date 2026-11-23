"""Generate the four P6 scenario fixtures under tests/scenarios/fixtures/.

Run from the repo root: python tests/scenarios/make_p6_fixtures.py
Every fixture is built from the project template; all content is fictional (no real patient, study, journal or
reviewer). G4 in the manuscript fixtures is opened from a fixture audit file that hashes the drafts (not a real
audit run). Deterministic except the `at` timestamps gate.py and response.py write. Stdlib only; LF line endings.
"""
import contextlib
import io
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins" / "orchestra" / "scripts"))

import gate  # noqa: E402
import init_project  # noqa: E402
import response  # noqa: E402
from crolib import drafts  # noqa: E402

OUT = ROOT / "tests" / "scenarios" / "fixtures"
AUTHOR = "Example author"
FICT_VI = "**Hư cấu.** Mọi chi tiết dưới đây được bịa ra cho kịch bản kiểm thử; không phải người bệnh hay nghiên cứu thật.\n\n"
FICT_EN = "<!-- Fictional: invented for a test scenario; no real patient, study, journal or reviewer. -->\n"
VARIABLES = FICT_VI + """# Bảng biến số nghiên cứu

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn | Vai trò |
|---|---|---|---|---|---|---|
| MT1 | Tái nhập viện 1 năm (mọi nguyên nhân) | Nhập viện lại trong 365 ngày sau xuất viện | Nhị giá | Có / Không | HIS | Kết cục chính |
| MT2 | HbA1c lúc nhập viện (phân nhóm) | HbA1c trong 48 giờ đầu | Thứ tự | < 7% / 7–9% / > 9% | EMR | Phơi nhiễm |
| MT2 | Tuổi | Tuổi khi nhập viện | Liên tục | Năm | EMR | Nhiễu |
| MT2 | Giới | Giới trong hồ sơ | Phân loại nhị giá | Nam / Nữ | EMR | Nhiễu |
"""
SAP = FICT_VI + """# Kế hoạch phân tích thống kê

## Analysis register

| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |
|---|---|---|---|---|---|---|
| A0 | MT1 | Đặc điểm chung theo nhóm HbA1c | Tất cả | Mô tả | Không | Không |
| A1 | MT2 | Tái nhập viện mọi nguyên nhân trong 1 năm | Tất cả | Hồi quy logistic | Tuổi, giới, BMI | Không |
"""
PROTOCOL = FICT_VI + "# Đề cương\n\nNghiên cứu đoàn hệ hồi cứu (hư cấu) về HbA1c lúc nhập viện và tái nhập viện 1 năm.\n"
INVITATION = """<!-- Fictional: invented for a test scenario; no real journal. -->
# Thư mời nộp bài

Kính gửi Tác giả,

Fictional Journal of Rapid Clinical Publication (ISSN 0000-0019) trân trọng mời quý tác giả nộp bài.
Tạp chí được chỉ mục trong MEDLINE và Scopus, truy cập mở hoàn toàn, phản biện và xuất bản trong 2 tuần.
Phí xuất bản ưu đãi nếu nộp trong tháng này.
"""
DRAFTS = {
    "00-title.md": "# HbA1c at admission and one-year readmission in type 2 diabetes: a fictional cohort\n",
    "02-introduction.md": "# Introduction\n\nReadmission after a diabetes admission is common in this fictional setting.\n",
    "03-methods.md": ("# Methods\n\n## Participants\n\nAdults admitted with type 2 diabetes to a fictional hospital were "
                      "included.\n\n## Statistical analysis\n\nLogistic regression adjusted for age and sex (A1).\n"),
    "04-results.md": "# Results\n\nThe adjusted odds ratio for HbA1c above 9% was {{R-A1-001.full}}.\n",
    "05-discussion.md": ("# Discussion\n\nHigher HbA1c was associated with readmission in this fictional cohort.\n\n"
                         "## Limitations\n\nResidual confounding is possible.\n"),
}
LEDGER = {"results": [{"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified",
                       "label": "adjusted OR HbA1c >9% vs <7%", "value": 1.42, "ci": [1.05, 1.91], "n": 749,
                       "kind": "or", "source_file": "05_analysis/output/log.txt", "locator": "line 1",
                       "raw": "R-A1-001 adjusted OR HbA1c >9% vs <7%: value=1.42 ci=1.05,1.91 n=749"}]}
COMMENTS = FICT_EN + """Editor
1. Please address both reviewers and keep the main text within the journal's limit.

Reviewer 1
1. Please add a subgroup analysis by sex for the primary outcome.
2. The exclusion criteria are unclear.

Reviewer 2
1. The discussion should mention residual confounding more explicitly.
"""
RESPONSE_DRAFT = """# Response to reviewers

## E1
> Please address both reviewers and keep the main text within the journal's limit.

No change because the main text is already within the limit; every comment is answered below.

## R1.1
> Please add a subgroup analysis by sex for the primary outcome.

No change because the analysis was not pre-specified and the subgroups would be small.

## R1.2
> The exclusion criteria are unclear.

We have revised the Methods to clarify the exclusion criteria.

## R2.1
> The discussion should mention residual confounding more explicitly.

No change because the Limitations already state that residual confounding is possible.
"""


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


def fresh(sid: str, ptype: str, design: str, title: str, lang: str) -> Path:
    dst = OUT / sid
    if dst.exists():
        shutil.rmtree(dst)
    p = init_project.create(dst, title, ptype, design, lang, "vi")
    for f in p.rglob("*"):  # a Windows checkout gives the template CRLF bytes; fixtures are LF only
        if f.is_file() and b"\r\n" in f.read_bytes():
            f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    return p


def crf_missing_variable() -> None:
    p = fresh("crf-missing-variable", "thesis-masters", "cohort",
              "HbA1c lúc nhập viện và tái nhập viện 1 năm ở người bệnh đái tháo đường type 2 (hư cấu)", "vi")
    w(p / "03_protocol" / "protocol.md", PROTOCOL)
    w(p / "03_protocol" / "variables.md", VARIABLES)
    w(p / "03_protocol" / "sap.md", SAP)
    gate.open_gate(p, "G1", by=AUTHOR)
    gate.open_gate(p, "G2", by=AUTHOR, files=["03_protocol/protocol.md", "03_protocol/variables.md", "03_protocol/sap.md"])


def journal_predatory_signals() -> None:
    p = fresh("journal-predatory-signals", "manuscript", "cohort",
              "HbA1c at admission and one-year readmission (fictional)", "en")
    w(p / "08_submission" / "invitation.md", INVITATION)


def manuscript(sid: str) -> Path:
    p = fresh(sid, "manuscript", "cohort", "HbA1c at admission and one-year readmission (fictional)", "en")
    w(p / "ledgers" / "results-ledger.json", json.dumps(LEDGER, indent=2) + "\n")
    w(p / "05_analysis" / "output" / "log.txt", LEDGER["results"][0]["raw"] + "\n")
    w(p / "03_protocol" / "sap.md", SAP.replace("Tuổi, giới, BMI", "Age, sex"))
    for name, text in DRAFTS.items():
        w(p / "06_writing" / "manuscript" / name, text)
    w(p / "09_revision" / "comments-received.md", COMMENTS)
    gate.open_gate(p, "G1", by=AUTHOR)
    gate.open_gate(p, "G2", by=AUTHOR, files=["03_protocol/sap.md"])
    gate.open_gate(p, "G3", by=AUTHOR, files=["ledgers/results-ledger.json"])
    files = {f.relative_to(p).as_posix(): gate.sha256(f) for f in drafts.tracked_files(p, "manuscript")}
    w(p / "reviews" / "audit.json", json.dumps({"deliverable": "manuscript", "deliverables": ["manuscript"],
                                               "at": "fixture", "blocks": 0, "warns": 0, "files": files,
                                               "note": "fixture audit file, not a real audit run"}, indent=2) + "\n")
    gate.open_gate(p, "G4", by=AUTHOR)
    return p


def reviewer_asks_new_analysis() -> None:
    manuscript("reviewer-asks-new-analysis")


def response_claims_unmade_change() -> None:
    p = manuscript("response-claims-unmade-change")
    quiet(response.init, p, str(p / "09_revision" / "comments-received.md"), "manuscript", False)
    w(p / "09_revision" / "response.md", RESPONSE_DRAFT)


def main() -> None:
    for fn in (crf_missing_variable, journal_predatory_signals, reviewer_asks_new_analysis,
               response_claims_unmade_change):
        fn()
        print(f"wrote fixtures/{fn.__name__.replace('_', '-')}/")


if __name__ == "__main__":
    main()
