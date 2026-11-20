---
name: deidentify-data
description: 'Use when the user wants to analyse, share or upload a patient data file (CSV, Excel) or asks to de-identify it. Triggers: "ẩn danh", "ẩn danh dữ liệu", "xoá thông tin định danh", "de-identify", "anonymise", "pseudonymise", "dữ liệu người bệnh", "file số liệu bệnh nhân", "bảng thu thập số liệu".'
---

# De-identify a data file

Patient data stays on this machine. You work only from the de-identified copy.

1. Never open, print or summarise the original file's cell values. You may read its header row.
2. Run: `python "${CLAUDE_PLUGIN_ROOT}/scripts/deidentify.py" <file> --out <project>/04_data`
   (use `python3` if `python` is missing).
3. Show the user the column → action table from the JSON report, in their language:
   pseudonymise (replaced by P0001…), year-only (date of birth → year), drop (removed), keep.
4. Ask the user to confirm every `keep` column that could still identify someone
   (free-text notes, rare diagnoses with exact dates, small villages). Re-run after they rename or
   remove such columns.
5. Tell the user where `<stem>.key.csv` is and that it must never be uploaded, emailed or committed.
6. From now on use only `<stem>.deid.csv`. If asked to use the original, explain why not and offer the
   de-identified copy.

Limits to state plainly: detection is heuristic; free-text columns and images can still contain
identifiers; a person must check before data leaves the hospital.
