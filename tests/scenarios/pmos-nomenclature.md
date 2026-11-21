# pmos-nomenclature: renamed condition is searched under old and new names
Skill under test: literature-search (step 0 nomenclature check)
Fixtures: a project created with init_project.py, design rct, title "Lifestyle intervention for reproductive-age women with PCOS in Vietnam" (`python plugins/orchestra/scripts/init_project.py <run-folder> --title "Lifestyle intervention for reproductive-age women with PCOS in Vietnam" --type thesis-masters --design rct --output-lang vi --chat-lang vi`)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Tìm tài liệu cho đề tài này, tập trung vào can thiệp lối sống ở phụ nữ PCOS.
Expected (GREEN):
- The search strategy lists PCOS and PMOS (polyendocrine metabolic ovarian syndrome) and notes MeSH drift.
- The 2026 PLoS Medicine meta-analysis (PMID 42776991) is found by a lookup and enters the ledger verified.
- No PMID appears that was not returned by a tool in the transcript.
Baseline (RED): searches "PCOS" only and misses the 2026 meta-analysis.
