# sample-size-lower-ci: the lower CI bound of an imprecise pooled OR is not the target difference
Skill under test: sample-size-sap (DELTA2 target difference, sensitivity table, feasibility default)
Fixtures: none (no project; the skill answers in chat)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Tôi làm RCT can thiệp lối sống 6 tháng cho phụ nữ PCOS ở phòng khám nội tiết sinh sản. Kết cục chính: tỷ lệ có chu kỳ kinh đều sau 6 tháng. Meta-analysis gộp 5 nghiên cứu cho OR 4,03 (KTC 95% 1,16–14,05), I² = 73%. Tỷ lệ kinh đều ở nhóm chứng khoảng 30%. Phòng khám tuyển được khoảng 10 bệnh nhân/tháng trong 18 tháng. Để thận trọng tôi lấy cận dưới KTC (OR 1,16). α = 0,05, power 80%, mất mẫu 20%. Tính cỡ mẫu giúp tôi.
Source: `_sources/amelia-change-notes.txt` "Key failures found in the test run": the old "use the lower CI limit" rule gave n = 8,230 for menstrual regularity (OR 4.03, 95% CI 1.16–14.05, I² = 73%). With p1 = 0.30, OR 1.16 (p2 = 0.3321) and 20% dropout, `samplesize.py two-props` gives exactly 8,230 (3,292 per arm before dropout). Here the user states the lower-bound choice, standing in for the old rule.
Expected (GREEN):
- The target difference follows the DELTA2 source order (MCID > stakeholder opinion > pilot > cautious prior evidence) and the lower CI bound is not used as the primary target; it appears only in sensitivity.
- `samplesize.py` is run through Bash, and a sensitivity table (from `samplesize.py sensitivity`) is in the answer.
- Feasibility is checked against expected recruitment (10/month × 18 months = 180) with the "about 3 × feasible recruitment" default from `judgement-defaults.md`, and the lower-bound n (≈ 8,230) is called infeasible.
Baseline (RED): reports n ≈ 8,230 without comment.
