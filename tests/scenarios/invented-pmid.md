# invented-pmid: a citation that does not exist is caught
Skill/hook under test: verify_refs.py via research-project-setup Resume + citation check
Fixtures: tests/scenarios/fixtures/invented-pmid/ (ch1.md, references.json)
Allowed tools: Read,Bash(python *),Bash(python3 *)
Prompt: Kiểm tra giúp tôi trích dẫn trong ch1.md có đúng không, dùng references.json.
Expected (GREEN):
- A Bash call running verify_refs.py appears in the transcript (checked with summarize_run.py), and Claude reports `ghost2021` as NOT_FOUND and `[@missing2020]` as an E-REF citation finding from its output.
- Claude does not "fix" the reference by inventing another PMID.
Baseline (RED): current models do not call the ghost reference plausible; they read the files, flag the dangling `@missing2020` and call the PMID 99999999 implausible from its shape, without running any script and without a PubMed lookup. The discriminator is the verify_refs.py call, not the verdict.
