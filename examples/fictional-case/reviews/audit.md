# Audit: case-report

Date: 2026-11-23T02:11:50 · mode: offline (stored ledger statuses) · blocks: 0 · warns: 5

| Check | Code | Block | Warn |
|---|---|---|---|
| ledgers | E-REF | 0 | 0 |
| citations | E-REF | 0 | 0 |
| results numbers | E-NUM | 0 | 0 |
| analysis declarations | E-STAT | 0 | 0 |
| case report | E-CASE | 0 | 0 |
| screening and extraction | E-SCR | 0 | 0 |
| GRADE wording | E-GRADE | 0 | 0 |
| literature synthesis | E-LIT | 0 | 0 |
| consistency | E-CONS | 0 | 0 |
| prose density | P00 | 0 | 0 |
| guideline checklist | E-RG | 0 | 0 |
| sections and captions | E-FMT | 0 | 0 |
| identifiers | E-PHI | 0 | 0 |
| reviewer reports | E-REV | 0 | 5 |

## Cách sửa / How to fix

- `E-REV`: rerun the reviewer agent on the current drafts.

## Findings

```text
E-REV warn reviews/citation-verifier.md:1: citation-verifier reviewed an earlier version of the case-report drafts (digest differs); rerun it if the content changed
E-REV warn reviews/statistical-reviewer.md:1: statistical-reviewer reviewed an earlier version of the case-report drafts (digest differs); rerun it if the content changed
E-REV warn reviews/reporting-guideline-checker.md:1: reporting-guideline-checker reviewed an earlier version of the case-report drafts (digest differs); rerun it if the content changed
E-REV warn reviews/scientific-editor.md:1: scientific-editor reviewed an earlier version of the case-report drafts (digest differs); rerun it if the content changed
E-REV warn reviews/consistency.md:1: consistency-auditor reviewed an earlier version of the case-report drafts (digest differs); rerun it if the content changed
```

G4: no block; the author may open G4 (`gate.py open . G4 --by "<name>"`).
