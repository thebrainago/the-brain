# BỘ TIÊU CHÍ MỚI: chỉ hỏi "có ra tiền không" (17/10/2026)

> **Bản chép từ repo `thebrainago/brain2` (repo Grok đang chạy), 17/10/2026.** Các thay đổi trong code (`nhan/cong.py`, `nhan/cham_diem.py`, `nhan/chi_phi.py`, `config/nguong.json`, `mt5tools/do_phi_san.py`) đã được chép sang đây. Riêng sổ cái MT5 13/10 (`reports/mt5_lien_tuc/so_cai.jsonl`), các báo cáo `.htm` (`reports/mt5_v24`, `reports/mt5_v27`), `mt5tools/sinh_viec.py` và `mt5tools/chay_lai_tren_san.py` **chỉ có ở brain2**. Mọi con số MT5 trong tài liệu này lấy từ đó.

> Chủ dự án: *"cái nó cần là giao dịch có lợi nhuận, chứ còn bây giờ cứ loại bỏ các yếu tố may mắn và so sánh với việc mua giữ thì nó không cần thiết, bởi vì chắc chắn là sẽ không thể nào mà chuẩn như thế được."*
>
> Chốt lần 2 (cùng ngày): *"tìm ra một hệ có lãi sau khi trừ đi phí và các mức giãn, chỉ cần mức sụt giảm không quá 80 % và lợi nhuận trên 10 % một năm … bỏ hết những cái đấy đi, chỉ cần đạt được những yếu tố cốt lõi."*

## 0. BA YẾU TỐ CỐT LÕI: tiêu chí duy nhất, đã nằm trong code

1. **Lãi sau phí và các mức giãn** (spread theo giờ, giãn lúc đổi ngày, swap, hoa hồng). Hệ ăn được nhờ "khe giá lúc đổi ngày" là lãi giả, vì lúc đó spread giãn gấp 5–9 lần.
2. **Sụt giảm ≤ 80 %.**
3. **Lãi ≥ 10 %/năm.**

Lot co giãn (anh tự đi lot), nên câu hỏi đúng là: **có mức lot nào cho lãi ≥ 10 %/năm mà sụt giảm ≤ 80 % không?** Điều này tương đương **lãi %/năm ÷ sụt giảm % ≥ 10/80 = 0,125**, ước lượng tuyến tính theo lot. Ví dụ: một hệ lãi 0,5 %/năm với sụt giảm 1 % ở lot 0,01 thì tăng lot lên ×80 sẽ cho ~40 %/năm, sụt giảm 80 %.

| Chỗ | Nay |
|---|---|
| `nhan/cong.py` (`che_do_cong = "loi_nhuan"`) | Chỉ CHẶN 3 điều kiện: (11) khe giá đổi ngày, (14) lãi ròng ≤ 0, (15 mới) `15_lai_10_sut_giam_80`. Phí chỉ khai báo, chuỗi nghiên cứu (chỉ số Yahoo) giờ chỉ là **nhãn**. Ngưỡng nằm ở `config/nguong.json`: `lai_nam_toi_thieu_pct = 10`, `sut_giam_toi_da_pct = 80`. |
| `nhan/cham_diem.py` | `CHAY_DUOC` = lãi ≥ 10 %/năm ở mức lot cho sụt giảm 80 % (`lai_pct_nam_o_dd80`). `CHUA_DAT` = có lãi nhưng quá mỏng, giữ làm mảnh ghép. `BO` = lỗ hoặc cháy. |
| `mt5tools/sinh_viec.py` `tong-ket` | Thêm `cot_loi` cho mỗi cấu hình: lãi %/năm, sụt giảm, hệ số lot, lãi ở DD 80 %, đạt/không. |
| `mt5tools/chay_lai_tren_san.py tong-ket` | Mặc định `--dd-muc-tieu 80`. Thêm `dat_cot_loi` cho từng mảnh và cho cả bộ ghép. |

**Kết quả áp ngay:** danh sách hệ đạt nằm trong **`DANH_SACH_HE_DAT.md`**.

Các mục 1–6 dưới đây là bản thứ nhất cùng ngày, còn đúng cho phần GIỮ/BỎ/THÊM. Riêng điều kiện (7) "phí đo được" nay **chỉ là nhãn**.

Tài liệu này là bản chốt cho mục 1 của `RA_SOAT_TOAN_BO.md`. Các thay đổi dưới đây **đã nằm trong code** và có hiệu lực ngay, không còn là đề xuất.

## 1. Đã sửa trong code

| Chỗ | Trước | Nay |
|---|---|---|
| `nhan/cong.py`, `config/nguong.json` | `che_do_cong = "nhan"`. Trượt **một** trong ~14 điều kiện là FAIL, gồm: thắng mua-giữ, Sharpe, Calmar, alpha có ý nghĩa, placebo, FDR, ≥ 30 lệnh, rr ≥ 0,2, lãi ≥ 3× spread | `che_do_cong = "loi_nhuan"`. **Chỉ 3 điều kiện chặn**: (7) phí đo được (không phải khai báo), (11) không ăn khe đảo ngày, tức không nhìn trước, (14 mới) **lãi ròng sau phí > 0**. Các điều kiện còn lại thành **nhãn** đính kèm. Chế độ cũ `chan`/`nhan` vẫn còn, đổi lại bằng config. |
| `nhan/cong.py`: lỗi ẩn | Điều kiện 12/13 thêm ngày 18/09 nhưng chưa được xếp loại chặn hay nhãn, nên ở chế độ `nhan` (chế độ mặc định cũ) **mỗi lần gọi `cong.xet` đều ném `KeyError`** | Đã xếp loại cả 12, 13, 14. Placebo/FDR giờ chỉ bị bỏ qua khi trượt điều kiện **chặn**, không phải khi chỉ trượt nhãn. |
| `nhan/cham_diem.py` | `CHAY_DUOC` đòi lãi ≥ 20 %/năm ở lot cố định, sụt giảm ≤ 60 %, ≥ 20 lệnh/năm. Hệ lãi nhỏ bị xếp `MONG` | `CHAY_DUOC` = **có lãi và không cháy tài khoản**. Ba ngưỡng cũ thành nhãn trong `ly_do`, vì lot co giãn được nên "20 %/năm ở lot 0,01" không mang nghĩa gì. |
| `mt5tools/sinh_viec.py` | IS phải đạt PF ≥ 1,25 và ≥ 30 lệnh; OOS phải đạt PF ≥ 1,15 và ≥ 15 lệnh. Hệ D1 chỉ 4–8 lệnh/năm nên **không bao giờ được chạy OOS** | IS: PF ≥ 1,0, ≥ 10 lệnh, net > 0. OOS: PF ≥ 1,0, ≥ 5 lệnh. "Near-miss" giờ là vùng sát hoà vốn (PF 0,9–1,0). |

**Tác động đo được trên sổ cái MT5 (630 lần chạy, 13/10):** số cấu hình đạt IS tăng từ 252 lên **343**. Trong đó **92 cấu hình mới được xếp chạy OOS**: MRZ AUDCAD 42, MRZ GBPUSD 20, MRZ AUDUSD 13, RSI US500 9, và vài cấu hình khác. Lần chạy `chay_lien_tuc.py` kế tiếp trên máy nhà sẽ tự lấy các việc này trước.

**Ước tính trên sổ chấm lại 361 hệ** (`reports/CHAM_LAI_THE_HE.json`, mô phỏng Python, phí XM): cổng cũ cho **1 PASS / 361**. Theo cổng mới, khoảng **113 / 361** sẽ là ứng viên: qua (7) và (11), Sharpe sau phí > 0. Phần lớn là hồi quy trên cặp chéo FX: EURCAD 17, GBPCAD 15, AUDCAD 14, NZDCAD 14, EURGBP 13. Nhiều nhất ở khung H4 (59), rồi H1 (32), D1 (22); có cả IBS US500. Đây chỉ là ước tính, vì sổ cũ không lưu lãi ròng mà dùng Sharpe > 0 thay cho nó. Số thật cần chạy lại `cham_lai_the_he.py` trên máy có `data/`.

## 2. GIỮ: những thứ làm con số thành tiền thật

1. **Phí thật của sàn anh đánh**: spread theo giờ, độ giãn lúc đổi ngày, swap, hoa hồng. Phí chỉ khai báo (`cp.do_tin = KHAI`) thì không bao giờ qua.
2. **Không nhìn trước, không ăn khe đảo ngày.** Hệ dùng dữ liệu tương lai thì lãi trên giấy không bao giờ thành tiền.
3. **Lãi ròng sau phí > 0**, và cuối cùng phải **khớp MT5**. Mô phỏng Python chỉ dùng để lọc trước: 93,9 % số lần cùng dấu với MT5, nhưng thường lạc quan hơn.
4. **Tài khoản không cháy** (`nguy_co_chay` trong `cham_diem`). Đây là rủi ro tiền, không phải tiêu chí học thuật.
5. Canary dữ liệu và `NGUONG_PHAN_GIAI` của PMG: hai thứ này báo **dữ liệu hỏng / không đo được**, không phải báo hệ thua. Kết quả là `CHƯA_ĐO_ĐƯỢC`, không phải `ÂM`.

## 3. BỎ khỏi phán quyết: vẫn tính và ghi, nhưng chỉ làm nhãn

| Tiêu chí | Vì sao bỏ |
|---|---|
| Holm cộng dồn, p-value, alpha có ý nghĩa, placebo, FDR, MDE | Đây là câu hỏi "có phải may mắn không". Anh không cần câu trả lời đó. Trên sổ cái MT5 13/10, 247/251 cấu hình lãi cả hai giai đoạn vẫn bị ghi "0 qua" chỉ vì Holm. |
| Thắng mua-giữ (điều kiện 1–3) | Trader CFD không ôm mua-giữ (swap ~5,8 %/năm). Một mảnh lãi ít hơn mua-giữ vẫn là tiền khi đem ghép. |
| Đủ lệnh (≥ 30 lệnh, ≥ 20 lệnh/năm, ≥ 2 lệnh/tuần) | Ghép nhiều mảnh ít lệnh thì tổng sẽ đủ lệnh. Ít lệnh chỉ được gắn nhãn "mảnh ghép". |
| `rr_thuc_te ≥ 0,2` | Tiêu chí này loại đúng cách anh đánh: TP nhỏ, DCA, gồng lệnh. Nay chỉ là nhãn "đuôi rủi ro, cần quản lí vốn". |
| Lãi ≥ 3× spread | Đã thay bằng lãi ròng **sau** phí > 0, cộng thêm con số "chịu được giãn thêm bao nhiêu giá" (mục 4). |
| Dương cả hai nửa | Hệ ăn theo xu hướng hay theo chế độ thị trường là hợp lệ. Gắn nhãn chế độ, không loại. |
| Lãi ≥ 20 %/năm ở lot cố định | Lot co giãn được. Con số đúng là %/năm ở mức sụt giảm anh chọn (mục 4). |

Luật vòng lặp của Grok (`tai_lieu/VONG_LAP.md`, mục "Luật cứng") đã sửa theo cùng hướng.

## 4. THÊM: thứ trader cần mà hệ chưa từng đo

| Cần | Đo bằng | Trạng thái |
|---|---|---|
| Phí trên **đúng tài khoản anh** (Exness cent, XM micro): spread p50/p90/p99 theo giờ, giãn đổi ngày (×), spread đầu tuần, **khoảng trống cuối tuần** (gồng không SL), swap **ra tiền mỗi đêm ở lot nhỏ nhất**, ngày ×3, tiền mỗi 1 giá, tiền của TP 5 giá, spread chiếm bao nhiêu % TP, margin lot nhỏ nhất, **margin khi hedge**, mức stop-out, tài khoản hedging hay netting, `stops_level` (đặt TP sát giá được không) | `mt5tools/do_phi_san.py` (`may_nha/DO_PHI_SAN.cmd`) | Script đã viết và có test. **Cần máy nhà chạy.** |
| **Hoa hồng thật, swap đã trả, cách anh xử lí lệnh** (số lần nhồi, giờ giữ lệnh, tỉ lệ đóng lãi, đóng bằng TP hay bằng tay, lỗ lớn nhất) | `do_phi_san.py` đọc **lịch sử lệnh** của chính tài khoản → `lenh_cua_anh.csv`, `lich_su_tom_tat.csv` | Như trên |
| **Lãi trên phí sàn anh**: chạy lại đúng các cấu hình MT5 đã lãi, trên terminal đăng nhập tài khoản anh | `mt5tools/chay_lai_tren_san.py chay` (không quét tham số mới: 28 lần chạy mỗi sàn = 15 cặp EA × mã, mỗi cặp tối đa 2 cấu hình, 2016 → 10/2026) | Script đã viết và có test. **Cần máy nhà chạy.** |
| **%/năm ở mức sụt giảm anh chọn** (hệ số lot) | `chay_lai_tren_san.py tong-ket --dd-muc-tieu 20` | Đã có. Đây là ước lượng **thô**: tăng lot tuyến tính, đường vốn tính theo lệnh đã đóng. |
| **Spread/trượt giá chịu được thêm mỗi lệnh** (đơn vị giá) trước khi mảnh hết lãi | `tong-ket` → `chiu_them_gia_moi_lenh` | Đã có |
| **Đóng góp khi ghép**: bỏ mảnh này ra thì bộ ghép mất bao nhiêu lãi và sụt giảm đổi ra sao | `tong-ket` → `dong_gop` | Đã có |
| Sụt giảm **thả nổi** (lệnh đang kẹt) | Từng mảnh: MT5 đã đo (`Equity Drawdown Maximal`). **Bộ ghép: CHƯA ĐO**, vì cộng đường vốn đóng lệnh làm sụt giảm thấp hơn thực tế | Ghi rõ trong `tong_ket.json` |
| Giãn lúc có tin (NFP/CPI) | API Python của MT5 không có lịch kinh tế | **CHƯA ĐO**. Tạm xem p99 theo giờ. |
| **Demo là phán xử cuối**: EA chạy demo cent lot nhỏ 4–8 tuần, so với tester | Bước 4 của `RA_SOAT_TOAN_BO.md` | Chờ anh |

## 5. Không đổi, kèm lí do (sửa một chỗ trong bản rà soát)

- **`quan_tri.loc`**: bản rà soát `RA_SOAT_TOAN_BO.md` đề xuất đổi bộ lọc này. Đọc lại code thì thấy nó **chỉ phân loại họ 2 (quản trị vị thế)**: spec không có nút quản trị thuộc họ 1 (tín hiệu vào). Nó không loại hệ có lãi nào, nên **giữ nguyên**.
- **`TRAN_SPREAD_BPS = 8`** (`ho_so_symbol`): giữ nguyên. Đây là câu hỏi tiền, vì cặp phí cao giết mọi lưới. Khi có `reports/phi_san/` thì đổi sang phí đo trên sàn anh.

## 6. Máy nhà cần chạy

Xem `tai_lieu/HANG_CHO_MAY_NHA.md` mục **"PHÍ + CHẠY LẠI TRÊN TÀI KHOẢN CỦA ANH"** (#37–#40).
