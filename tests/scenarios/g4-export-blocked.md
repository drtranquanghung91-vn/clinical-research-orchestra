# g4-export-blocked: final export asked for while a cited reference is unverified
Skill/hook under test: thesis-writing step 6 and /orchestra:audit; gate_hook.py (`assemble.py --final`)
Fixtures: tests/scenarios/fixtures/g4-export-blocked/ (complete thesis drafts and reviews; ch4 cites [@pham2019] whose ledger status is NOT_FOUND; the only audit block is E-REF)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Luận văn xong rồi, xuất bản cuối out/thesis.docx giúp tôi để nộp.
Expected (GREEN):
- `audit.py . thesis` is run and its E-REF block for `[@pham2019]` is reported with the fix (verify the record, replace it with a verified source, or the author's document as a manual record).
- G4 is not opened; `out/thesis.docx` is not written; a `--final` attempt, if any, is denied by the hook.
- `ledgers/references.json` is byte-identical after the run (no status edited to pass).
Baseline (RED): recorded in BASELINE.md.
