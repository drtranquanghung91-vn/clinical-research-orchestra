# Phiếu thu thập số liệu (CRF)

<!-- Tạo bởi crf.py từ 03_protocol/variables.md ngày 2026-11-23; sửa variables.md rồi tạo lại. -->

## Biểu mẫu: main

### 1. Biến phơi nhiễm (Exposure)

| Mã | Trường | Loại | Đơn vị | Giá trị cho phép / khoảng | Bắt buộc |
|---|---|---|---|---|---|
| hba1c_luc_nhap_vien | HbA1c lúc nhập viện (phân nhóm) | ordinal |  | < 7% · 7–9% · > 9% | yes |
| hba1c_luc_nhap_vien_2 | HbA1c lúc nhập viện (liên tục) | continuous | % (NGSP) |  | yes |

### 2. Biến kết cục (Outcome)

| Mã | Trường | Loại | Đơn vị | Giá trị cho phép / khoảng | Bắt buộc |
|---|---|---|---|---|---|
| tai_nhap_vien_1_nam | Tái nhập viện 1 năm (mọi nguyên nhân) | binary |  | Có · Không | yes |
| tai_nhap_vien_lien_quan_dtd | Tái nhập viện liên quan ĐTĐ | binary |  | Có · Không | yes |
| thoi_gian_den_lan_tai_nhap_vien | Thời gian đến lần tái nhập viện đầu tiên | time-to-event | Ngày |  | yes |
| tu_vong_trong_1_nam | Tử vong trong 1 năm (trong viện) | binary |  | Có · Không | yes |

### 3. Biến nhiễu đưa vào mô hình chính (Confounder — Mục tiêu 2)

| Mã | Trường | Loại | Đơn vị | Giá trị cho phép / khoảng | Bắt buộc |
|---|---|---|---|---|---|
| tuoi | Tuổi | continuous | Năm |  | yes |
| gioi | Giới | binary |  | Nam · Nữ | yes |
| thoi_gian_mac_dtd | Thời gian mắc ĐTĐ | continuous | Năm |  | yes |
| benh_dong_mac_chinh | Bệnh đồng mắc chính | binary |  | Có · Không | yes |

### 4. Biến không đưa vào mô hình chính (trung gian / chưa rõ vai trò — xem `protocol.md` mục 2.7.2)

| Mã | Trường | Loại | Đơn vị | Giá trị cho phép / khoảng | Bắt buộc |
|---|---|---|---|---|---|
| su_dung_insulin_trong_thoi_gian | Sử dụng insulin trong thời gian nằm viện | binary |  | Có · Không | yes |
| thoi_gian_nam_vien | Thời gian nằm viện (lần nhập viện chỉ số) | continuous | Ngày |  | yes |

### 5. Biến thăm dò, không bắt buộc (phụ thuộc tính khả dụng dữ liệu — xem `protocol.md` mục 2.7.2)

| Mã | Trường | Loại | Đơn vị | Giá trị cho phép / khoảng | Bắt buộc |
|---|---|---|---|---|---|
| ty_so_bach_cau_trung_tinh_lympho | Tỷ số bạch cầu trung tính/lympho (NLR) | continuous | Tỷ số |  | yes |
| chi_so_viem_tong_hop | Chỉ số viêm tổng hợp (SII hoặc SIRI) | continuous | Chỉ số tính toán |  | yes |
| nguy_co_dinh_duong_luc_nhap_vien | Nguy cơ dinh dưỡng lúc nhập viện | categorical |  | Tùy thang đo | yes |

### 6. Biến hành chính / định danh nghiên cứu (không dùng trong phân tích thống kê)

| Mã | Trường | Loại | Đơn vị | Giá trị cho phép / khoảng | Bắt buộc |
|---|---|---|---|---|---|
| ma_so_nghien_cuu | Mã số nghiên cứu | text |  |  | yes |
| ngay_nhap_vien_chi_so | Ngày nhập viện chỉ số | date |  |  | yes |
| ngay_xuat_vien_chi_so | Ngày xuất viện chỉ số | date |  |  | yes |
