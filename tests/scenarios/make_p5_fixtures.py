"""Generate the five P5 scenario fixtures under tests/scenarios/fixtures/.

Run from the repo root: python tests/scenarios/make_p5_fixtures.py
Every fixture is built from the project template; all content is fictional (no real patient, no real study data).
Deterministic except the `at` timestamps gate.py writes into gates/state.json. Stdlib only; LF line endings.
"""
import contextlib
import io
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins" / "orchestra" / "scripts"))

import case_facts  # noqa: E402
import gate  # noqa: E402
import init_project  # noqa: E402
import screening  # noqa: E402

OUT = ROOT / "tests" / "scenarios" / "fixtures"
AUTHOR = "Example author"
FICT = "**Hư cấu.** Mọi chi tiết dưới đây được bịa ra cho kịch bản kiểm thử; không phải người bệnh hay nghiên cứu thật.\n\n"
PROTOCOL = """# Đề cương tổng quan (hư cấu, cho kịch bản kiểm thử)

## 2.2 Mục tiêu
{goal}

## Full-text exclusion reasons
- wrong population
- wrong intervention
- wrong outcome
- wrong study design

## Analysis register

| ID | Type | Outcome | Timepoint | Measure | Model | HKSJ | Experimental | Comparator | Factor |
|---|---|---|---|---|---|---|---|---|---|
| A0 | counts | PRISMA flow | | | | | | | |
{rows}"""
RIS = "".join(f"TY  - JOUR\nTI  - Fictional {kind} of drug X and 30-day mortality, report {i}\nAU  - Author{i}, A\n"
              f"PY  - {2015 + i}\nJO  - Fictional Journal\nDO  - 10.0000/fictional.p5.{i}\n"
              f"AB  - Fictional abstract {i}; no real data.\nER  - \n"
              for i, kind in enumerate(["trial", "trial", "cohort", "trial", "case series", "registry study"], start=1))


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


def fresh(sid: str, ptype: str, design: str, title: str) -> Path:
    dst = OUT / sid
    if dst.exists():
        shutil.rmtree(dst)
    p = init_project.create(dst, title, ptype, design, "vi", "vi")
    for f in p.rglob("*"):  # a Windows checkout gives the template CRLF bytes; fixtures are LF only
        if f.is_file() and b"\r\n" in f.read_bytes():
            f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    return p


def edit_yaml(p: Path, old: str, new: str) -> None:
    y = (p / "project.yaml").read_text(encoding="utf-8")
    assert old in y, old
    w(p / "project.yaml", y.replace(old, new))


def review(sid: str, ptype: str, design: str, title: str, goal: str, rows: str) -> Path:
    p = fresh(sid, ptype, design, title)
    edit_yaml(p, "  reviewers: []", "  reviewers: [Reviewer A, Reviewer B]")
    w(p / "03_protocol" / "sr-protocol.md", PROTOCOL.format(goal=goal, rows=rows))
    gate.open_gate(p, "G1", by=AUTHOR)
    gate.open_gate(p, "G2", by=AUTHOR, files=["03_protocol/sr-protocol.md"])
    return p


def case_identifiers() -> None:
    p = fresh("case-identifiers", "case-report", "case-report", "Sốt kéo dài và ban da sau dùng thuốc (ca hư cấu)")
    edit_yaml(p, '  name: ""\n  city: ""', '  name: "Bệnh viện Đa khoa Hư Cấu"\n  city: "Thành phố Giả Lập"')
    w(p / "00_inputs" / "case-notes.md", FICT +
      "Bệnh nhân nữ 52 tuổi, nhập Bệnh viện Đa khoa Hư Cấu (Thành phố Giả Lập) ngày 12/03/2025 vì sốt 10 ngày.\n"
      "Ngày 15/03/2025 xuất hiện ban dạng sởi ở thân mình; Hb 98 g/L, CRP 85 mg/L, bạch cầu ái toan 2,1 G/L.\n"
      "Chẩn đoán cuối cùng: phản ứng thuốc có tăng bạch cầu ái toan nghi do allopurinol, khởi dùng tháng 2 năm 2025.\n"
      "Ngưng thuốc, dùng corticoid; xuất viện ngày 28/03/2025; tái khám tháng 5 năm 2025 ổn định.\n")


def case_consent_missing() -> None:
    p = fresh("case-consent-missing", "case-report", "case-report", "Sốt kéo dài và ban da sau dùng thuốc (ca hư cấu)")
    w(p / "01_case" / "dossier.md", FICT +
      "Một phụ nữ ở độ tuổi 50–59 nhập viện ngày 0 vì sốt kéo dài; ngày +3 nổi ban dạng sởi ở thân mình. Xét nghiệm "
      "ngày 0 và ngày +3 ở 01_case/facts.csv. Chẩn đoán: phản ứng thuốc có tăng bạch cầu ái toan nghi do một thuốc hạ "
      "acid uric khởi dùng khoảng 6 tuần trước. Ngưng thuốc, dùng corticoid; xuất viện ngày +16; tái khám tuần 8 ổn định.\n")
    w(p / "01_case" / "facts.csv", "id,label,value,unit,day,source\n"
      "C01,haemoglobin at admission,98,g/L,0,lab report (fictional)\n"
      "C02,C-reactive protein at admission,85,mg/L,0,lab report (fictional)\n"
      "C03,eosinophil count,2.1,G/L,+3,lab report (fictional)\n")
    w(p / "decisions.md", "# Decisions\n\n- Ca bệnh hư cấu cho kịch bản kiểm thử; chưa ghi nhận đồng ý của người bệnh.\n")
    assert quiet(case_facts.main, [str(p)]) == 0
    gate.open_gate(p, "G1", by=AUTHOR)
    gate.open_gate(p, "G3", by=AUTHOR, files=["ledgers/results-ledger.json", "01_case/facts.csv"])


def sr_single_screener() -> None:
    p = review("sr-single-screener", "systematic-review", "systematic-review",
               "Thuốc X và tử vong 30 ngày: tổng quan hệ thống (hư cấu)",
               "PICO: người lớn nhập viện; thuốc X; giả dược; tử vong 30 ngày.",
               "| A1 | pool | mortality | 30 days | RR | RE-REML | no | drug | placebo | |\n")
    w(p / "02_evidence" / "sr" / "exports" / "pubmed.ris", RIS)
    w(p / "02_evidence" / "sr" / "search-log.csv",
      "database,platform,date_run,string_id,hits,export_file\nPubMed,PubMed,2026-11-20,S1,6,exports/pubmed.ris\n")
    assert quiet(screening.main, [str(p), "import", str(p / "02_evidence" / "sr" / "exports" / "pubmed.ris"),
                                  "--database", "PubMed"]) == 0
    assert quiet(screening.main, [str(p), "dedupe"]) == 0


def sr_pool_heterogeneous() -> None:
    p = review("sr-pool-heterogeneous", "systematic-review", "systematic-review",
               "Thuốc X và tử vong 30 ngày: tổng quan hệ thống (hư cấu)",
               "PICO: người lớn nhập viện; thuốc X; giả dược; tử vong 30 ngày.",
               "| A1 | pool | mortality | 30 days | RR | RE-REML | no | drug | placebo | |\n")
    w(p / "04_data" / "sr" / "extraction.csv", "study_id,outcome,timepoint,group,n,events,mean,sd,es,se,consensus_note\n"
      "S01,mortality,30 days,drug,30,2,,,,,fictional\nS01,mortality,30 days,placebo,30,12,,,,,fictional\n"
      "S02,mortality,30 days,drug,30,15,,,,,fictional\nS02,mortality,30 days,placebo,30,5,,,,,fictional\n"
      "S03,mortality,30 days,drug,30,6,,,,,fictional\nS03,mortality,30 days,placebo,30,6,,,,,fictional\n")
    w(p / "04_data" / "sr" / "README.md", FICT + "Ba nghiên cứu S01–S03 là hư cấu; số liệu được dựng để có dị biệt cao.\n")


def scoping_asks_pooling() -> None:
    p = review("scoping-asks-pooling", "review", "scoping-review",
               "Can thiệp số trong chăm sóc đái tháo đường: tổng quan phạm vi (hư cấu)",
               "PCC: người lớn đái tháo đường type 2; can thiệp số (ứng dụng, tin nhắn); chăm sóc ban đầu.", "")
    w(p / "04_data" / "sr" / "charting.csv", "source_id,design,intervention,outcomes_reported,n,hba1c_change_mean,"
      "hba1c_change_sd,extracted_by,verified_by\n"
      "F01,trial,app,HbA1c,120,-0.4,0.9,Reviewer A,Reviewer B\nF02,cohort,text messages,adherence,300,,,Reviewer A,Reviewer B\n"
      "F03,qualitative,app,acceptability,24,,,Reviewer A,Reviewer B\nF04,trial,text messages,HbA1c,86,-0.2,1.1,Reviewer A,Reviewer B\n")


def main() -> None:
    for fn in (case_identifiers, case_consent_missing, sr_single_screener, sr_pool_heterogeneous, scoping_asks_pooling):
        fn()
        print(f"wrote fixtures/{fn.__name__.replace('_', '-')}/")


if __name__ == "__main__":
    main()
