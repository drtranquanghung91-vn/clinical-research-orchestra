"""Generate the four P4 scenario fixtures under tests/scenarios/fixtures/.

Run from the repo root: python tests/scenarios/make_p4_fixtures.py
Every fixture starts from the fictional cohort example (its G3 lock stays valid on the copied bytes).
Deterministic except the `at` timestamps worklog.py writes into reviews/worklog.json (revise-revert).
Stdlib only; all files are written with LF line endings.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins" / "orchestra" / "scripts"))

import worklog  # noqa: E402
from crolib import drafts, reviews  # noqa: E402

EX = ROOT / "examples" / "fictional-cohort"
OUT = ROOT / "tests" / "scenarios" / "fixtures"
BASE = ("project.yaml", "STATUS.md", "decisions.md", "gates/state.json", "ledgers/claims.json", "ledgers/outline.json",
        "ledgers/references.json", "ledgers/results-ledger.json", "01_question/question.md",
        "02_evidence/evidence-table.md", "03_protocol/protocol.md", "03_protocol/sap.md", "03_protocol/sample-size.md",
        "03_protocol/variables.md", "04_data/cohort.deid.csv", "05_analysis/analysis.py", "05_analysis/crostats.py",
        "05_analysis/output/results.json", "06_writing/thesis/ch1-literature-review.md",
        "06_writing/thesis/ch3-results.md")
STROBE_IDS = ["1a", "1b", "2", "3", "4", "5", "6a", "6b", "7", "8", "9", "10", "11", "12a", "12b", "12c", "12d", "12e",
              "13a", "13b", "13c", "14a", "14b", "14c", "15", "16a", "16b", "16c", "17", "18", "19", "20", "21", "22"]

SIM = "**Dữ liệu mô phỏng.** Nội dung này thuộc dự án ví dụ, không phải số liệu bệnh nhân thật.\n\n"
CH2 = ("# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n" + SIM +
       "## 2.1 Thiết kế nghiên cứu\n\nNghiên cứu đoàn hệ hồi cứu trên người bệnh đái tháo đường type 2 xuất viện tại "
       "Bệnh viện Mô phỏng, theo dõi một năm sau xuất viện.\n\n"
       "## 2.2 Đối tượng nghiên cứu\n\nNgười bệnh đủ tuổi trưởng thành có HbA1c ghi nhận lúc nhập viện, xuất viện còn sống; "
       "loại trừ hồ sơ thiếu ngày nhập viện.\n\n"
       "## 2.3 Biến số và phân tích\n\nPhơi nhiễm là nhóm HbA1c lúc nhập viện; kết cục là tái nhập viện mọi nguyên nhân "
       "trong một năm. Phân tích theo kế hoạch trong 03_protocol/sap.md.\n")
DATVANDE = ("# ĐẶT VẤN ĐỀ\n\n" + SIM + "Đái tháo đường type 2 là bệnh mạn tính thường gặp ở người bệnh nằm viện. "
            "HbA1c lúc nhập viện phản ánh mức kiểm soát đường huyết trước đó [@robbins2021]. Đề tài xem xét mối liên quan "
            "giữa HbA1c lúc nhập viện và tái nhập viện trong một năm tại một bệnh viện mô phỏng.\n")
KETLUAN = ("# KẾT LUẬN\n\n" + SIM + "Trong đoàn hệ mô phỏng này, chưa chứng minh được mối liên quan giữa nhóm HbA1c "
           "lúc nhập viện và tái nhập viện trong một năm. <!-- results: R-A1-004 -->\n")
KIENNGHI = ("# KIẾN NGHỊ\n\n" + SIM + "Cần nghiên cứu tiến cứu với cỡ mẫu lớn hơn, nhiều trung tâm, để ước lượng chính xác "
            "hơn mối liên quan này.\n")
LIMITS = ("## 4.3 Hạn chế\n\nThiết kế hồi cứu có thể có sai lệch chọn; dữ liệu hồ sơ có thể có sai lệch thông tin; "
          "còn yếu tố nhiễu chưa đo lường; kết quả từ một bệnh viện mô phỏng nên khó khái quát hoá.\n")
CH4_PHAM = ("# CHƯƠNG 4. BÀN LUẬN\n\n" + SIM +
            "## 4.1 Kết quả chính\n\nTỷ số chênh hiệu chỉnh của tái nhập viện ở nhóm HbA1c >9% so với nhóm <7% là "
            "{{R-A1-004.value}} (KTC 95%: {{R-A1-004.ci}}); khoảng tin cậy chứa giá trị 1 nên chưa chứng minh được mối liên quan.\n\n"
            "## 4.2 So sánh với nghiên cứu khác\n\nHướng ước lượng tương tự báo cáo trước đó [@robbins2021] và một báo cáo "
            "khác trong cùng bối cảnh [@pham2019].\n\n" + LIMITS)
CH4_R1 = CH4_PHAM.replace(" và một báo cáo khác trong cùng bối cảnh [@pham2019]", "")
CH4_R2 = CH4_R1.replace("chưa chứng minh được mối liên quan.",
                        "chưa chứng minh được mối liên quan. HbA1c cao có thể làm tăng nguy cơ tái nhập viện ở người bệnh nam.")
REQUEST = "phân tích dưới nhóm theo giới tính (nam/nữ) cho mục tiêu 2 — chưa có trong SAP"


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def base(sid: str) -> Path:
    dst = OUT / sid
    if dst.exists():
        shutil.rmtree(dst)
    for rel in BASE:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        data = (EX / rel).read_bytes().replace(b"\r\n", b"\n")  # the example is committed with CRLF; fixtures are LF only
        (dst / rel).write_bytes(data)
    state = json.loads((dst / "gates" / "state.json").read_text(encoding="utf-8"))
    for rel in state.get("G3", {}).get("files", {}):  # the lock hashes follow the LF bytes
        state["G3"]["files"][rel] = hashlib.sha256((dst / rel).read_bytes()).hexdigest()
    w(dst / "gates" / "state.json", json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return dst


def thesis_drafts(dst: Path, ch4: str) -> None:
    d = dst / "06_writing" / "thesis"
    ch3 = d / "ch3-results.md"  # the example's pending figure slot would be an E-FMT block; G3 does not lock ch3
    text = "".join(ln for ln in ch3.read_text(encoding="utf-8").splitlines(keepends=True)
                   if not ln.startswith("[Biểu đồ 3.1:"))
    w(ch3, text.replace("\n\n\n", "\n\n"))
    w(d / "00-dat-van-de.md", DATVANDE)
    w(d / "ch2-methods.md", CH2)
    w(d / "ch4-discussion.md", ch4)
    w(d / "05-ket-luan.md", KETLUAN)
    w(d / "06-kien-nghi.md", KIENNGHI)


def write_reports(dst: Path, scores: dict, request: str | None = None) -> None:
    dg = drafts.digest(dst, "thesis")
    for agent, (rel, crits) in reviews.REVIEWERS.items():
        block = {"deliverable": "thesis", **{c: scores[c] for c in crits}}
        req = f"NEW-ANALYSIS: {request}\n" if request and agent == "statistical-reviewer" else ""
        w(dst / rel, f"STATUS: PASS\nFINDINGS\n| code | location | fix |\n{req}drafts-digest: thesis {dg}\n"
                     f"```scores\n{json.dumps(block)}\n```\n")
    items = {i: {"status": "na", "reason": "fixture"} for i in STROBE_IDS}
    w(dst / "reviews" / "guideline-checklist.json",
      json.dumps({"guideline": "STROBE", "deliverable": "thesis", "items": items}, ensure_ascii=False, indent=2) + "\n")


def thesis_g3_closed() -> None:
    dst = base("thesis-g3-closed")
    state = json.loads((dst / "gates" / "state.json").read_text(encoding="utf-8"))
    state.pop("G3")
    w(dst / "gates" / "state.json", json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def discussion_overclaim() -> None:
    dst = base("discussion-overclaim")
    w(dst / "06_writing" / "thesis" / "ch2-methods.md", CH2)


def g4_export_blocked() -> None:
    dst = base("g4-export-blocked")
    thesis_drafts(dst, CH4_PHAM)
    refs = json.loads((dst / "ledgers" / "references.json").read_text(encoding="utf-8"))
    refs["references"].append({"id": "pham2019", "title": "Fictional record for the g4-export-blocked scenario",
                               "authors": ["Pham X"], "journal": "Fictional J", "year": 2019,
                               "doi": "10.0000/fictional.2019.001",
                               "verified_by": "verify_refs.py 2026-11-21 NOT_FOUND"})
    w(dst / "ledgers" / "references.json", json.dumps(refs, ensure_ascii=False, indent=2) + "\n")
    write_reports(dst, dict.fromkeys(reviews.CRITERIA, 2))


def revise_revert() -> None:
    dst = base("revise-revert")
    thesis_drafts(dst, CH4_R1)
    r1 = dict.fromkeys(reviews.CRITERIA, 2)
    r1["claim_scope"] = 1
    write_reports(dst, r1)
    entry = worklog.score(dst, "thesis", 1)
    assert entry["total"] == 15 and entry["decision"] == "KEEP", entry
    w(dst / "06_writing" / "thesis" / "ch4-discussion.md", CH4_R2)
    r2 = dict(r1, statistics=1, claim_scope=0, limitations=1)
    write_reports(dst, r2, REQUEST)


def main() -> None:
    thesis_g3_closed()
    discussion_overclaim()
    g4_export_blocked()
    revise_revert()
    n = sum(1 for sid in ("thesis-g3-closed", "discussion-overclaim", "g4-export-blocked", "revise-revert")
            for p in (OUT / sid).rglob("*") if p.is_file())
    print(f"wrote 4 fixtures, {n} files")


if __name__ == "__main__":
    main()
