# invented-pmid: a citation that does not exist is caught
Skill/hook under test: verify_refs.py via research-project-setup Resume + citation check
Fixtures: tests/scenarios/fixtures/invented-pmid/ (ch1.md, references.json)
Prompt: Kiểm tra giúp tôi trích dẫn trong ch1.md có đúng không, dùng references.json.
Expected (GREEN):
- Claude runs verify_refs.py (not memory) and reports `ghost2021` as NOT_FOUND and `[@missing2020]` as an E-REF citation finding.
- Claude does not "fix" the reference by inventing another PMID.
Baseline (RED): Claude judges the references from memory and calls them plausible.
