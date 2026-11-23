---
name: ethics-and-crf
description: 'Use when the protocol is locked and the study needs its ethics committee dossier, case report form (CRF), data dictionary or participant information and consent form before data collection. Triggers: "hồ sơ đạo đức", "hội đồng đạo đức", "xin duyệt đạo đức", "phiếu thu thập số liệu", "bệnh án nghiên cứu", "từ điển dữ liệu", "phiếu đồng ý tham gia nghiên cứu", "bản cung cấp thông tin cho người tham gia", "ethics committee submission", "IRB application", "case report form", "CRF", "data dictionary", "informed consent form".'
---

# Ethics and CRF

Builds the CRF and data dictionary from the locked variables table, drafts the consent form and lists the ethics
dossier. Never submits anything and never gives legal advice. Detail:
`${CLAUDE_PLUGIN_ROOT}/references/workflows/ethics-and-crf.md`.

## 1. Gate
Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G2`. Not open: stop, explain in the user's language
that the CRF is built from the locked protocol, and point to `protocol-design`. Never lock a gate yourself.

## 2. CRF and data dictionary
1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/crf.py" . build` writes `03_protocol/ethics/crf.md` and
   `03_protocol/ethics/data-dictionary.csv`.
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/crf.py" . check` until no block. A variable the SAP uses that
   `variables.md` lacks is the author's decision: report the E-CRF block, ask for its definition, type, unit and
   values, and never invent one. Changing `variables.md` after G2 is a protocol change the author makes and
   re-locks. A term the matcher missed that clearly names an existing variable goes in
   `03_protocol/ethics/crf-map.csv` (`term,variable`); show the line to the author.
3. Warns (fields no objective or analysis uses; identifiers without a stated need): ask the author; never delete a
   field silently.

## 3. Consent form
Write `03_protocol/ethics/consent-form.md` from `${CLAUDE_PLUGIN_ROOT}/references/ethics/consent-elements.md` in
`project.yaml → language.output`: every element, plain words, short sentences. The committee's own template, when
the author has one, wins. Institution-specific items (committee, approval number, contacts, amounts) stay
`[[AUTHOR: …]]` (`[[TÁC GIẢ: …]]`); never fill them. A record-only study may get a consent waiver: ask, and let the
author record the committee's decision in `decisions.md`. Then
`python "${CLAUDE_PLUGIN_ROOT}/scripts/lint_prose.py" --profile consent 03_protocol/ethics/consent-form.md`; fix
each warning or tell the author why not.

## 4. Dossier
Write `03_protocol/ethics/dossier.md` from `${CLAUDE_PLUGIN_ROOT}/references/ethics/dossier-template.md`: every
document with its status. Never state a regulation or a committee rule from memory: write it only when the author
or a tool lookup gives it, with the source; otherwise `[[AUTHOR: …]]`.

## 5. Word files
`python "${CLAUDE_PLUGIN_ROOT}/scripts/build_docx.py" 03_protocol/ethics/crf.md out/ethics/crf.docx --project .`,
the same for `consent-form` and `dossier`. No gate beyond G2. Report the paths, the open `[[AUTHOR: …]]` items
and the check results in the user's language.
