# du_lieu/ — dữ liệu bàn giao (the-brain tự suy ra)

Xuất ngày **10/10/2026** từ kho the-brain (commit `8a1151c`) bằng `xuat_du_lieu.py`. Không có giá, không có lệnh thô, không có tên bot / tín hiệu / tác giả; tín hiệu chỉ có **ID** công khai. Danh mục tổng và lý do không đưa phần còn lại: `../05_NGUON_DU_LIEU.md`.
CSV: UTF-8, phân cách dấu phẩy, **dấu chấm** thập phân. Ô trống = không có / không áp dụng (không phải 0).

| Tệp | Dòng | Dùng cho |
|---|---|---|
| `hieu_chuan_125_o.csv` | 125 | P1 (`../04`) |
| `hieu_chuan_tom_tat.json` | – | P1: số đã tính lại |
| `doi_chung_nhieu_tom_tat.json` | – | P4 (`../04`): số để đối chiếu |
| `vung_lai_trong_mau.csv` | 1.055 | P5 (`../04`) |
| `mql5_400_phan_loai.csv` | 400 | bản đồ nguồn |
| `mql5_31_nguoi_thang.csv` | 31 | bước "LẤY lịch sử lệnh" |
| `so_tay_nghien_cuu/` | 1 + 4 + 5 | cách ghi sổ |
| `xuat_du_lieu.py` | – | nguồn gốc (chỉ chạy được ở gốc kho the-brain) |

---

## `hieu_chuan_125_o.csv` — engine nến ↔ MT5 tester (125 ô × 38 cột)

Mỗi dòng = **một cấu hình lưới ("ô")** chạy hai lần trên **cùng một cửa sổ**: (1) MT5 Strategy Tester, Model 0 (tick sinh từ M1) — **đây là đáp án**; (2) engine nến của the-brain (`nhan/luoi.py`, bản v3 "cực trị", đo trước 08/10/2026).

| Nhóm | Cột | Nghĩa |
|---|---|---|
| Cửa sổ | `ma`, `khung`, `tu`, `den`, `ngay` | mã, khung, ngày đầu / cuối (`YYYY.MM.DD`), số ngày |
| | `model` | luôn 0 (cả 125 ô) |
| | `chat_luong_lich_su_pct` | chất lượng lịch sử tester: **100** = sạch (53 ô), **51** = nửa chất lượng (71 ô), **1** = gần như không (1 ô). Chỉ dùng ô 100 làm đáp án |
| | `von`, `don_bay` | 10.000 (tiền tài khoản tester, USD) · đòn bẩy 100 — cả 125 ô |
| Tham số lưới | `che_do` | `mua` / `ban` / `hai_chieu` |
| | `buoc`, `tp` | pip: khoảng cách giữa các tầng · TP tính từ giá trung bình |
| | `tran_tang`, `lot` | số tầng tối đa mỗi rổ · lot ban đầu |
| | `kieu_lot`, `he_so_lot` | `phang` (lot đều) · `nhan` (lot·hệ số^k) · `cong` (lot·(1+hệ số·k)) |
| | `he_so_buoc` | bước giãn dần (1 = đều) |
| | `tia_lenh`, `bien_cap` | **chuỗi `"True"`/`"False"`** (nhớ đổi sang bool) · pip lãi của cặp tia để chốt |
| | `cho_lui`, `chot_tien` | **cả 125 ô đều 0** → bảng không phủ lưới "chờ giá lùi" và "chốt theo tiền" |
| | `tham_so_json` | đủ 17 khoá, nạp thẳng: `ThamSo(**json.loads(...))` |
| Tester | `tester_lai_nam_pct` | lãi %/năm, **gồm cả lãi/lỗ chưa đóng lúc hết cửa sổ**, quy năm bằng `ngay/365,25`, **chưa trừ swap** |
| | `tester_dd_pct`, `tester_pf`, `tester_so_lenh` | DD tối đa (%), profit factor, số lệnh |
| | `tester_swap_tien` | luôn 0 (tester không ghi swap) |
| Engine | `engine_lai_nam_pct` | lãi %/năm đã **trừ swap ước** |
| | `engine_dd_pct`, `engine_so_lenh` | DD (%), số lệnh |
| | `engine_swap_tien`, `engine_swap_nam_pct` | swap ước (tiền; %/năm — âm = tốn tiền) |
| So sánh | `engine_hon_tester` | 1 nếu `engine_lai_nam_pct > tester_lai_nam_pct` |
| | `ty_le_engine_tren_tester` | tỉ số engine/tester, **chỉ có khi tester > 0** (61 ô) |
| | `lech_lai_pp` | engine − tester, **chưa cùng thước** (engine đã trừ swap, tester chưa) |
| | `lech_dd_pp`, `lech_lenh_pct` | chênh DD (điểm), chênh số lệnh (%) |
| | `ket_luan` | `KHOP` (11) / `LECH` (114) theo dung sai chặt của the-brain — **nhãn, đừng học nó; hãy học cột chênh** |

**Chênh cùng thước** (cái cần dùng) = `(engine_lai_nam_pct − engine_swap_nam_pct) − tester_lai_nam_pct`.

### Tự kiểm số trong `../03` và `../04` (chạy được ở thư mục này, cần numpy)

```python
import csv, json
import numpy as np

rows = list(csv.DictReader(open("hieu_chuan_125_o.csv", encoding="utf-8")))
f = float
chenh = lambda r: (f(r["engine_lai_nam_pct"]) - f(r["engine_swap_nam_pct"])) - f(r["tester_lai_nam_pct"])
for ten, nhom in (("có tia lệnh", [r for r in rows if r["tia_lenh"] == "True"]),
                  ("không tia lệnh", [r for r in rows if r["tia_lenh"] != "True"])):
    a = np.array([chenh(r) for r in nhom])
    print(ten, len(a), "trung vị %.2f" % np.median(a), "tứ phân vị %.1f … %.1f" % tuple(np.percentile(a, [25, 75])))
# kỳ vọng: có tia 68 ô, +8.69, 2.9 … 30.0 · không tia 57 ô, +0.03, -1.9 … 2.7

sach = [r for r in rows if r["khung"] == "H1" and r["chat_luong_lich_su_pct"] == "100.0"]
print(len(sach), "ô H1 sạch")           # kỳ vọng: 15 (AUDCAD 8 + NZDCAD 7, 2019-03-01 → 2019-08-31)
print(set(json.loads(sach[0]["tham_so_json"])))   # 17 khoá của ThamSo
```

Lưu ý: `lech_lai_pp` trung vị của 68 ô có tia là **+4,38** (chưa cùng thước, engine đã trừ swap), còn chênh cùng thước là **+8,69** — hai số khác nhau vì khác thước, không phải mâu thuẫn. `hieu_chuan_tom_tat.json` tính trên cột `lech_lai_pp` (số +4,38), còn `../03` R1 dùng chênh cùng thước (+8,69).

---

## `hieu_chuan_tom_tat.json`

Số tóm tắt tính lại từ CSV bằng mã trong `xuat_du_lieu.py`. Ba khối: `tat_ca` (125 ô), `chi_lich_su_sach_100pct` (53 ô), `chi_lich_su_51pct` (71 ô); khoá phẳng ở đầu là cho `tat_ca`. Trường `ghi_chu` ghi rõ engine = `nhan/luoi.py` v3 (cực trị), tester = Model 0. Chỉ để đối chiếu nhanh, không cần cho P1.

---

## `doi_chung_nhieu_tom_tat.json` — đối chứng nhiễu (để đối chiếu với bản brain2 tự dựng)

Chạy *chính đường ống thật* của the-brain (quét tối đa 1.000 ô lưới → chọn ô tốt nhất → đánh giá ngoài mẫu → ô ngẫu nhiên cùng lưới làm đối chứng ghép cặp) trên **chuỗi giả có đáp án**: H1, 54.600 nến, ~9 %/năm, GARCH, spread ~15 điểm, chia 60 / 20 / 20.

- `cau_hinh`: `so_bar` 54.600, `toi_da_o` 1.000, `v` 1 · `khung` "H1" · `phien_ban` 1.
- `tom_tat`: 5 câu đọc nhanh (NHIEU@e4, NHIEU@e3, ba mức DAO_DONG).
- `kich_ban`: 9 kịch bản, khoá = `<tên>@e<engine>` (e3 = engine cực trị, e4 = engine đường đi):
  - `NHIEU` — đi bộ ngẫu nhiên có cụm biến động (GARCH), không trôi, không lợi thế: **tham chiếu chính** (100 chuỗi ở e4, 200 ở e3); `NHIEU_THAP` / `NHIEU_CAO` — như `NHIEU` với biến động ×0,65 (≈ 5,9 %/năm) / ×1,35 (≈ 12 %/năm);
  - `BETA` — như `NHIEU` nhưng trôi +6 %/năm (kiểu chỉ số: hệ nghiêng mua "có lãi" nhờ beta); `XU_HUONG` — quán tính bậc 1 hệ số 0,07 (lưới ngược xu hướng bị phá);
  - ba mức hồi quy thật quanh neo trôi: `DAO_DONG_RAT_YEU` (nửa đời 288 nến, 10 % phương sai), `DAO_DONG_YEU` (144 nến, 30 %), `DAO_DONG` (48 nến, 60 %) — tỉ số phương sai VR48 = 0,99 / 0,97 / 0,83.
  Mỗi kịch bản có `so_chuoi`, `vr_tb`, `troi_is_pct_tb` / `troi_oos_pct_tb` (độ trôi trung bình trong / ngoài mẫu), `gop` (tỉ lệ qua + khoảng tin cậy 95 %) và `nhieu` (phân bố từng thước).
- **Đọc nhanh:** chuỗi *chỉ có nhiễu* vẫn cho ô tốt nhất "qua" ngoài mẫu **86 %** (engine 4, 100 chuỗi) / **88 %** (engine 3, 200 chuỗi), ô chọn bừa **84 % / 85 %**; "qua *và* hơn mua-giữ" 57 % / 55 %. Cổng nhị phân "lãi sau phí ngoài mẫu" **bão hòa** với lưới.
- **Nhãn:** MÔ PHỎNG trên chuỗi giả; chưa thử trên chuỗi thật. Mã gốc `nhan/doi_chung_nhieu.py` đã **đóng băng** — đừng chép nguyên (1.015 dòng); `../04` P4 có công thức ≈ 100–150 dòng.

---

## `vung_lai_trong_mau.csv` — 1.055 vùng lãi (TOÀN BỘ trong mẫu)

Mỗi dòng = ô tốt nhất của **một lượt quét lưới** trên một (mã, khung) ở đoạn khám phá, kèm hình dạng vùng quanh nó.

| Cột | Nghĩa |
|---|---|
| `id` | khoá 10 ký tự của (mã, khung, tham số) |
| `nhom` | `cao` (698: ô tốt nhất của lượt quét xếp CAO_NGUYÊN) · `doi` (182: lượt quét không phải cao nguyên) · `ngau` (175: ô ngẫu nhiên ghép cặp cùng lượt quét, làm đối chứng) |
| `lop` | `CAO_NGUYEN` (≥ 60 % ô có lãi **và** hàng xóm của ô tốt nhất cũng lãi) · `HON_HOP` (115) · `CAI_GAI` (67: ô đẹp lẻ loi, < 30 % ô có lãi) · `NGAU_NHIEN` (175) |
| `ma`, `khung` | thị trường, khung |
| `co_che` | khoá cơ chế `kiểu vào|kiểu lot|lui?` (vd `mua|cong|-`) |
| `o_lai`, `o_quet`, `ty_le_o_lai` | số ô có lãi · tổng số ô của lượt quét · tỉ lệ (trống ở nhóm `ngau`) |
| `n_quet` | số lượt quét trùng (mã, khung, tham số) được gộp |
| `che_do`, `kieu_lot`, `buoc`, `tp`, `tran_tang`, `he_so_lot`, `cho_lui`, `lot` | các tham số chính của ô |
| `xac_nhan_ngoai_mau` | **trống ở cả 1.055 dòng** = chưa dòng nào được kiểm ngoài mẫu |
| `tham_so_json` | tham số đầy đủ |

Đọc đúng: `ty_le_o_lai` là **tỉ lệ trong mẫu** — nó cho biết vùng lãi *rộng* hay *hẹp*, **không** nói vùng đó có lãi thật. Trên chuỗi chỉ-nhiễu cổng này vẫn "qua" 84–88 % (xem `doi_chung_nhieu_tom_tat.json`).

---

## `mql5_400_phan_loai.csv` — 400 hồ sơ tín hiệu công khai (chỉ ID + số thống kê)

Phân loại bằng luật khai báo trước (`nhan/dau_chan.py`), xét theo thứ tự, dừng ở luật đầu khớp: `luoi_dca` (nhồi khi lỗ > 0,30 hoặc bậc tải ≥ 2, **và** lỗ treo đỉnh ≥ 0,10, **và** thắng ≥ 60 %) → `gong_lo` (cắt sạch > 1,2 và lỗ treo ≥ 0,10) → `scalp` (giữ ≤ 120 phút, cắt sạch ≤ 1,0) → `xu_huong` (giữ ≥ 1.440 phút, cắt sạch ≤ 1,0) → `khong_ro`. Phân bố: `khong_ro` 149 · `luoi_dca` 142 · `scalp` 47 · `gong_lo` 31 · `xu_huong` 31.

| Cột | Nghĩa |
|---|---|
| `id`, `kieu`, `ly_do_phan_loai` | ID công khai · nhãn · các số dẫn tới nhãn |
| `song_ngay` | số ngày tín hiệu đã sống |
| `song_2_nam_tang_duong_dd_duoi_80` | 1 nếu sống ≥ 2 năm, tăng trưởng dương và DD công bố < 80 % (**31 dòng = 31 "người thắng"**) |
| `so_lenh`, `lenh_moi_tuan`, `giu_phut`, `thang_pct`, `pf`, `sharpe` | lấy thẳng từ trang tín hiệu: số lệnh, lệnh / tuần, giữ trung bình (phút), % lệnh thắng, profit factor, Sharpe |
| `tai_dinh_pct` | "Max deposit load" trên trang |
| `dd_cong_bo_pct`, `tang_truong_pct` | DD và tăng trưởng công bố |
| `nhoi_khi_lo` | Spearman(mức tải, độ sâu lỗ treo): dương mạnh = **càng lỗ càng nhồi thêm** |
| `bac_tai` | số bước tăng tải rời rạc trong một đoạn giữ vị thế (trung vị); ≥ 2 = có nhồi lệnh |
| `lo_treo_dinh` | max (số dư − vốn)/số dư |
| `cat_sach` | trung vị \|MAE\|/MFE theo ngày; > 1 = để lỗ chạy hơn lãi |
| `tai_deu`, `tai_trung_vi_pct` | độ lệch chuẩn / trung bình của tải khi có vị thế (thấp = đều) · trung vị tải (%) |
| `lech_trai` | độ lệch (skewness) lợi suất theo lệnh; âm = nhiều lãi nhỏ, hiếm khi lỗ lớn |
| `so_diem_tai` | số điểm của đường tải có vị thế |

**Thiên lệch sống sót là toàn phần**: bảng chỉ có tài khoản CÒN SỐNG, nên đọc là "kiểu này tồn tại và đo được", **không** phải "kiểu này ra tiền" (`nhan/dau_chan.py`).

---

## `mql5_31_nguoi_thang.csv` — 31 hồ sơ sống ≥ 2 năm, tăng trưởng dương, DD công bố < 80 %

Cột: `id`, `kieu` (18 `luoi_dca` · 11 `khong_ro` · 1 `gong_lo` · 1 `xu_huong`), `song_ngay`, `dd_cong_bo_pct`, `tang_truong_pct`, `so_lenh`, `ma_chinh_da_sua` (mã giao dịch nhiều nhất **sau khi sửa** nhãn từ bảng Distribution), `ty_le_lenh_ma_chinh`, `6_ma_dau_(ma:so_lenh)`, `nhan_symbol_cu_dung` (**0 = nhãn mã đời đầu sai (19 dòng)**, 1 = đúng (12 dòng)), `ly_do_phan_loai`.
Sau khi sửa, mã chính phổ biến nhất là XAUUSD (8), EURUSD (5), rồi USDJPY / BTCUSD / AUDCAD (3 mỗi mã) — **không** phải "gần hết AUDCAD" (`../02` D5).

---

## `so_tay_nghien_cuu/*.jsonl`

Mỗi dòng JSON `{"h": <dấu vân tay>, "r": <bản ghi>}`. `cau_hoi.jsonl` (1 câu hỏi mở, ưu tiên 0,95, do chủ dự án đặt), `gia_thuyet.jsonl` (4 giả thuyết, cả 4 còn **MỞ**), `thi_nghiem.jsonl` (5 thí nghiệm trên AUDCAD M15: 2 bóc lịch sử, 1 quét lưới 70 ô, 1 chạy lưới ở đoạn khám phá, 1 xác nhận ở đoạn xác nhận). Tên EA / tên tín hiệu đã lược; chỉ còn ID.
Ba điều cần thấy ở đây: dấu vân tay mỗi bản ghi; trạng thái **MỞ / ĐẠT** thay vì "đúng / sai"; thí nghiệm gắn với giả thuyết (`gt_id`) và đoạn dữ liệu (`doan`).

## `xuat_du_lieu.py`

Mã sinh các tệp trên từ kho the-brain (đọc `reports/…`, `viec/xong/*.json`, `so_cai/nc/*.jsonl`). **Chỉ chạy được ở gốc kho the-brain** (các tệp nguồn không nằm trong gói). Có sẵn phép kiểm "không có tên cấm": đặt biến môi trường `CAM_TEN="tên1,tên2"` để nhờ nó dừng nếu thấy tên đó trong đầu ra.
