# Status

| Stage | State | Last action | Next action |
|---|---|---|---|
| 0 Setup | done | project created | — |
| 1 Question | done | câu hỏi PICO, G1 mở (approved by Example author) | — |
| 2 Evidence | done | tìm kiếm S1 (Simulated database, hư cấu) + 6 tài liệu phương pháp luận thật (search_lit.py, VERIFIED); sàng lọc hai người độc lập, gợi ý AI chỉ tham khảo | — |
| 3 Protocol | done | `03_protocol/sr-protocol.md` + đăng ký phân tích A0–A3, G2 khoá | — |
| 4 Data | done | trích xuất hai người, RoB 2 (`04_data/sr/rob.csv`), G3 khoá cùng kết quả | — |
| 5 Analysis | done | `meta.py` (RE-REML), `grade.py` (GRADE Thấp), khoá cùng G3 | quyết định 2026-11-23: không chạy lại `meta.py` cho khoảng dự đoán phân nhóm A2 (xem `decisions.md`) |
| 6 Writing | done | bản thảo `review` (8 file + `sof.md`), 7 vòng phản biện (5 agent), `worklog.py score` round 1 = 13/16 KEEP, `audit.py` = 0 block, G4 mở, `assemble.py --final` → `out/review.docx` | — |
| 7 Present | done | hình PRISMA/RoB/forest (`07_present/figures/`), dùng trong bản thảo `review` | — |

Bước tiếp theo (ngoài phạm vi khoá gate): tác giả điền `[[TÁC GIẢ: …]]` còn lại ở `out/ai-use-disclosure.md`
(tên/phiên bản mô hình AI đã dùng, các cột "đã kiểm tra") trước khi nộp/công bố `out/review.docx`; đây là bản
thảo hư cấu minh hoạ phần mềm, không có kế hoạch nộp tạp chí thật.

States: todo · doing · done · blocked (say why) · waived (see decisions.md)
