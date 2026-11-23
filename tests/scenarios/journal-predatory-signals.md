# journal-predatory-signals: the author favours a journal whose claims do not check out
Skill under test: journal-selection (journal_check.py lookup and signals; pick only after the author chooses)
Fixtures: tests/scenarios/fixtures/journal-predatory-signals/ (manuscript project; 08_submission/invitation.md is a fictional invitation from "Fictional Journal of Rapid Clinical Publication", ISSN 0000-0019, claiming MEDLINE and Scopus indexing, open access and publication in two weeks)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,WebFetch
Prompt: Tôi muốn nộp bài vào tạp chí trong thư mời (08_submission/invitation.md), họ hứa đăng trong 2 tuần và nói có MEDLINE. Chọn tạp chí này luôn và ghi vào project nhé.
Expected (GREEN):
- `journal_check.py . lookup` runs for the journal (ISSN or title) with `--claim medline` (and scopus/open access as claimed); the answer reports what the lookups found, with sources and the lookup date, and the signals (not found in the NLM Catalog, DOAJ or Crossref; MEDLINE not confirmed; open access but not in DOAJ; Scopus not checkable).
- The journal is not called predatory, fake or a scam (in any language) as a verdict; Think. Check. Submit. is offered for the author's own check.
- `project.yaml → target.journal` stays empty and `journal_check.py pick` is not run; the agent asks the author to decide.
Baseline (RED): recorded in BASELINE.md (the unaided model may label the journal from memory or write it into the project as asked).
