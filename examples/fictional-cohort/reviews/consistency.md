STATUS: FINDINGS

`consistency_audit.py .` (run independently): `consistency_audit: 0 block, 0 warn`, exit 0 — confirms the author's own run. Manual cross-check of wording/rounding/dates not caught by the script found one real design-wording drift (see FINDINGS) that a committee member could catch when comparing the slide's "Mục tiêu cụ thể" wording against the methods slide. All numbers checked (ch3-results vs ch3-results.rendered, abstract vs abstract.rendered, poster.json, figures.json) trace to the same locked `R-…` ledger ids and round consistently (e.g. tỷ lệ chung 22,1% everywhere; OR >9% vs <7% hiệu chỉnh 1,42 [0,94–2,15] p=0,097 everywhere; HR Cox >9% 1,35 / 7–9% 1,07 match R-A4-006/R-A4-005; EPV 39 matches R-A1-010; AUC 0,588 matches R-A1-009; n=1070 / n=1043 used with the same meaning in ch3, abstract, poster and F4). Mortality is consistently labelled "tử vong trong viện" (not all-cause) everywhere it appears. Dates (discharge 01/2021–12/2022, follow-up to 31/12/2023) are consistent between question.md, protocol.md, ch3 and the abstract.

FINDINGS
| code | location (file:line) | fix |
|---|---|---|
| X-OBJ | `01_question/question.md:129-131` vs `03_protocol/protocol.md:194-201` | Mục tiêu cụ thể 2 in question.md still lists 6 adjustment factors ("tuổi, giới, thời gian mắc bệnh, bệnh đồng mắc, thời gian nằm viện, sử dụng insulin"), but protocol.md §2.7.2 (confirmed 2026-11-21, see decisions.md "Mediator classification") explicitly removes length-of-stay and insulin use from the adjusted model as likely mediators — and the actual A1 model (SAP §16, ch3 Bảng 3.3, abstract, poster) adjusts only for tuổi, giới, thời gian mắc ĐTĐ, ≥1 bệnh đồng mắc. Follow protocol.md (the later, author-confirmed design decision): replace question.md's clause with "có hiệu chỉnh một số yếu tố nhiễu (tuổi, giới, thời gian mắc bệnh, bệnh đồng mắc); thời gian nằm viện và sử dụng insulin được xử lý là biến trung gian, không hiệu chỉnh trong mô hình chính (xem protocol.md §2.7.2)." If this slide quotes the original "Mục tiêu cụ thể" verbatim, update it before presenting so the Methods slide's 4-variable adjustment set does not contradict the Objectives slide's 6-variable list. |

GAPS
- Could not independently re-derive any `value`/`ci`/`p` from raw data (G3-locked ledger is the only permitted source); checks above are limited to cross-file agreement with the ledger, not re-computation.
- `ch1-literature-review.md` cites only external studies (hu2026, cao2026, li2026, robbins2021, chakraborty2021); it has no own-cohort numbers to cross-check against the ledger, so no rounding/naming check applies there beyond objective wording (already checked above).

CONFLICTS
- None found that I could not resolve against a named source — the one real drift above has a clear authoritative answer (protocol.md over question.md's unupdated clause), so it is listed as a FINDING, not a CONFLICT.
