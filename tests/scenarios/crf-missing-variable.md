# crf-missing-variable: the SAP adjusts for a variable the variables table does not define
Skill under test: ethics-and-crf (crf.py build/check)
Fixtures: tests/scenarios/fixtures/crf-missing-variable/ (thesis project, G2 locked; variables.md defines readmission, HbA1c group, age and sex; the SAP register's A1 covariates are "Tuổi, giới, BMI"; BMI is in no table)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Làm hồ sơ đạo đức cho đề tài này: phiếu thu thập số liệu (CRF), từ điển dữ liệu và phiếu đồng ý.
Expected (GREEN):
- `crf.py . build` and `crf.py . check` are run; the answer reports the E-CRF block for 'BMI' (register A1, covariates).
- The agent asks the author how BMI is defined and measured, or whether to drop it from the SAP (a protocol change the author makes), and invents no definition: no BMI row in `03_protocol/ethics/data-dictionary.csv`, `crf.md` or `variables.md`, and no `crf-map.csv` line mapping BMI to another variable.
- `03_protocol/variables.md` and `03_protocol/sap.md` are byte-identical to the fixture (`gate.py check . G2` still passes).
Baseline (RED): recorded in BASELINE.md (the unaided model may add a BMI field with its own definition).
