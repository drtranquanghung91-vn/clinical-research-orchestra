orchestra-prep: rob-draft

# Brief: draft risk-of-bias judgements (AI draft until both reviewers confirm)

## Input
The tool for each study from `${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/tools-by-design.md` (RoB 2 for
randomised trials: domains D1–D5; ROBINS-I for non-randomised studies of interventions: D1–D7) and the full texts.

## Output
- One file: `reviews/tmp/rob-draft.csv` with `study_id,outcome,tool,domain,judgement,support,reviewer`; reviewer is
  exactly `AI draft`; support is a quote with its page.
- The two reviewers judge and write `04_data/sr/rob.csv` themselves, naming both of them in `reviewer`;
  `extract_check.py` blocks any row still marked `AI draft`.

## Rules
- Domain judgements follow the tool's signalling questions; the overall judgement follows the tool's algorithm
  (never better than the worst domain), never a summed score.
- Judgements: RoB 2 low / some concerns / high; ROBINS-I low / moderate / serious / critical / no information.
