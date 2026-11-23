# Consent form elements (paraphrased checklist)

Use with the skill `ethics-and-crf`. The elements below are the ones internationally recognised guidance (the
Declaration of Helsinki, the CIOMS international ethical guidelines, ICH-GCP) expects an information sheet and
consent form to cover. They are paraphrased here, never quoted, and give no article or clause numbers: a citation
to any of these documents, or to a national regulation, is added only from a tool lookup recorded in
`ledgers/references.json`. **The author's ethics committee template always wins**: when the author gives one,
follow its order, headings and wording rules and use this list only to spot gaps.

| # | Element | What the participant must be able to understand |
|---|---|---|
| 1 | Purpose | why the study is done; that it is research, not routine care |
| 2 | Procedures | what happens to the participant, how often, what is collected (data, samples), what is experimental |
| 3 | Duration | how long participation lasts; how many contacts or visits |
| 4 | Risks and discomforts | foreseeable risks, including privacy risks in record-only studies |
| 5 | Benefits | to the participant (possibly none) and to others |
| 6 | Alternatives | other care, or not taking part, with no loss of usual care |
| 7 | Confidentiality and data handling | who sees the data, how it is pseudonymised, where and how long it is kept, whether it is shared |
| 8 | Voluntariness and withdrawal | taking part is free; leaving at any time without penalty; what happens to data already collected |
| 9 | Contacts | whom to ask about the study; whom to contact about the participant's rights (the committee) |
| 10 | Compensation and costs | costs, reimbursement, care for study-related harm, where relevant |
| 11 | Future use | storage or re-use of data or samples, if planned, as a separate choice |
| 12 | Signature block | participant (or legal representative), person obtaining consent, date; a witness when the participant cannot read |

Writing rules (warned by `lint_prose.py --profile consent`): plain words, short sentences, every technical term
explained in brackets the first time, active voice that says who does what ("you sign", "the study team keeps"),
the participant addressed directly.

Institution-specific facts are never filled by Claude: committee name and approval number, investigator names and
phone numbers, compensation amounts, insurance, storage periods set by the institution → `[[AUTHOR: …]]`
(`[[TÁC GIẢ: …]]` in Vietnamese).

Record-only (retrospective) studies: a committee may waive individual consent. Whether it does is the committee's
decision, recorded by the author in `decisions.md`; Claude never assumes a waiver.
