# Workflow: case report (CARE; BMJ mode)

1. Gate G1: the case, the teaching point and the consent status confirmed by the author (`gate.py open . G1 …`).
   G2 is not used for case reports.
2. Dossier: `01_case/dossier.md`, de-identified (relative time, age ranges, no names, places, record numbers);
   phi-guard scans it on write.
3. Facts: `01_case/facts.csv` (`id,label,value,unit,day,source`), then
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/case_facts.py" .` → ledger `R-A0-…` (status observed).
4. Literature for the discussion and similar cases with the `literature-search` skill; every case a verified
   record; `01_case/similar-cases.csv` (`ref_id,age_range,sex,presentation,key_finding,treatment,outcome`).
5. `python "${CLAUDE_PLUGIN_ROOT}/scripts/case_lint.py" .` until no block.
6. The author locks G3: `gate.py lock . G3 --by "<name>" --files ledgers/results-ledger.json 01_case/facts.csv 01_case/similar-cases.csv 05_analysis/output/case-facts-log.txt`.
7. Draft with the roles `case-front`, `case-presentation`, `case-discussion` (role briefs first in any subagent prompt).
8. Review rounds (≤ 3) with the five reviewer agents and `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" score . case-report --round N`.
9. `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . case-report`, then
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" . case-report` until 0 blocks.
10. Consent: the author writes `CONSENT: obtained <form, who signed>` in `decisions.md`; without it the final export
    is refused (`case_lint.py . --strict`, G4 and the hook).
11. The author opens G4 (`gate.py open . G4 --by "<name>"`), then
    `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . case-report --final` → `out/case-report.docx`.
12. Disclosure draft and `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" decisions .`.
