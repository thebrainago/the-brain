# 05 — DỮ LIỆU: đã bàn giao gì · cố ý KHÔNG đưa gì · lấy phần còn thiếu ở đâu

> Đọc sau `04`. Trả lời bốn câu: (1) trong gói có dữ liệu nào; (2) cái gì cố ý *không* đưa, vì sao; (3) muốn làm P1 (`04`) thì phải tải gì và rẻ nhất ra sao; (4) lấy lịch sử lệnh khi nào, thế nào.
> Đường dẫn dạng `nhan/…`, `tai_lieu/…` là tệp trong kho the-brain; gốc link ở `README.md`.

## 1. Đã bàn giao — thư mục `du_lieu/`

Mô tả từng cột và đoạn mã tự kiểm số: `du_lieu/README.md`. Mọi thứ do the-brain **tự suy ra**: không có giá, không có lệnh thô của ai, không có tên bot / tín hiệu / tác giả (chỉ **ID** công khai của tín hiệu).

| Tệp | Là gì | Cỡ | Dùng cho |
|---|---|---|---|
| `hieu_chuan_125_o.csv` | 125 cấu hình lưới chạy trên engine nến **và** trên MT5 tester: lãi %/năm, DD, số lệnh, swap, chênh | 125 dòng × 38 cột | P1 — đáp án sẵn |
| `hieu_chuan_tom_tat.json` | Số tóm tắt tính lại từ CSV, kèm hai lát cắt theo chất lượng lịch sử (100 % và 51 %) | nhỏ | P1 — kiểm số |
| `doi_chung_nhieu_tom_tat.json` | Đối chứng nhiễu: chuỗi giả **chỉ có nhiễu** (và vài kiểu có đáp án) chạy qua đúng đường ống quét → kiểm ngoài mẫu; 9 kịch bản | ≈ 170 KB | P4 — số để đối chiếu khi brain2 tự dựng |
| `vung_lai_trong_mau.csv` | 1.055 "vùng lãi" từ các lượt quét lưới: 698 cao nguyên + 182 đối chứng (hỗn hợp / cái gai) + 175 ô ngẫu nhiên ghép cặp | 1.055 dòng | P5; **toàn bộ là trong mẫu — 0 dòng đã kiểm ngoài mẫu** |
| `mql5_400_phan_loai.csv` | 400 hồ sơ tín hiệu công khai, phân loại kiểu chiến lược bằng luật khai báo trước (chỉ **ID** + số thống kê) | 400 dòng | bản đồ nguồn |
| `mql5_31_nguoi_thang.csv` | 31 hồ sơ sống ≥ 2 năm, tăng trưởng dương, DD công bố < 80 % (18 là lưới/DCA) | 31 dòng | điểm xuất phát khi tới bước "LẤY lịch sử lệnh" |
| `so_tay_nghien_cuu/*.jsonl` | Sổ tay nghiên cứu (1 câu hỏi, 4 giả thuyết, 5 thí nghiệm), đã lược tên | nhỏ | xem cách ghi sổ có dấu vân tay (`02` E3) |
| `xuat_du_lieu.py` | Mã sinh các tệp trên từ kho the-brain (nguồn gốc từng cột) | – | chỉ để kiểm chứng; **chỉ chạy được ở gốc kho the-brain** |

## 2. Cố ý KHÔNG đưa (và vì sao)

| Không đưa | Vì sao |
|---|---|
| Giá (nến/tick) của sàn XM — thư mục `data/` | Là dữ liệu của sàn, không nằm trong git của the-brain; brain2 đã có Dukascopy/Yahoo. Hai nguồn không khớp từng nến (`02` D9, `04` P1 bước 7) nên chép sang cũng không so trực tiếp được |
| Lịch sử lệnh thô (deals) của tín hiệu / bot người khác | Luật chủ dự án: bot và dữ liệu thô của người khác **không bao giờ vào git**. Chỉ đưa thống kê tự suy ra |
| `.mq5`, `.ex5`, `.mqh`, `.set` của người khác | Như trên; kho the-brain công khai |
| Tên tín hiệu, tên EA, tên tác giả | Chỉ dùng **ID** công khai của tín hiệu |
| `nao.db` cũ và các thư mục mất khi cài lại Windows ở máy nhà | Không còn. Sổ tay trong `so_tay_nghien_cuu/` là phần sót lại và đã lược |
| Báo cáo từng lệnh của tester (hàng nghìn dòng) | Nằm ở máy nhà the-brain; bảng 125 ô đã chứa các cột cần cho P1 |
| Khóa, token, mật khẩu, hồ sơ trình duyệt, số tài khoản (kể cả demo), tên đăng nhập, số tiền cá nhân | Kho công khai; không bao giờ |
| Kho tài liệu đã bóc và hàng chờ nguồn (hàng nghìn tài liệu) | Không đáng bàn giao: phễu 12.078 → 285 → 18 (số trước 02/10) và 3.656 tài liệu tồn kho đã được đo là rác (`02` D6) |
| Dữ liệu cào từ trang cần đăng nhập | Cần phiên đăng nhập của chủ dự án; không đưa ra ngoài |

## 3. Lấy giá cho P1 — rẻ nhất, công khai

P1 (`04`) chỉ cần giá nến H1 của **hai mã** trong **một cửa sổ sáu tháng**.

| Cần | Chi tiết |
|---|---|
| Mã, khung | AUDCAD và NZDCAD, nến **H1** |
| Cửa sổ | 2019-03-01 → 2019-08-31 (184 ngày, ≈ 3.100 nến H1 mỗi mã; thêm vài ngày lề phía trước nếu mô phỏng cần khởi động) |
| Vì sao đúng 15 ô này | Chỉ các ô H1 có `chat_luong_lich_su_pct == 100` (xem `du_lieu/README.md`); 71 ô còn lại chạy trên lịch sử tester thiếu một nửa nên không dùng làm đáp án |
| Dung lượng | ≈ 6.200 nến tổng cộng — vài trăm KB |
| Giá tiền | 0 đồng (nguồn công khai), một nhân CPU |

Cách làm đỡ rủi ro:
1. **Tải trực tiếp nến của cặp chéo**, đừng tự ghép từ hai cặp USD. High/low của nến không nhân/chia được: `high(AUDCAD)` không bằng `high(AUDUSD) × high(USDCAD)` vì hai cực trị không xảy ra cùng lúc. Ghép sẽ làm sai chính thứ P1 đang đo (thứ tự giá trong nến). Không tải được trực tiếp → ghi **CHƯA ĐO ĐƯỢC**, đừng thế bằng bản ghép.
2. **Dukascopy có thể chậm / trả 429** (brain2 đã ghi lỗi này cho các lần tải dài). Hai mã × sáu tháng là nhỏ; vẫn nên: một yêu cầu một lúc (không song song), nghỉ giữa các ngày, lưu cache từng ngày, gặp 429 thì **dừng và lùi lại** chứ không dồn thử.
3. **Múi giờ.** Nến của tester theo giờ máy chủ sàn (lệch UTC 2–3 giờ theo mùa). Độ lệch là số nguyên giờ nên ranh giới nến H1 thường trùng, chỉ khác nhãn giờ; bộ lọc theo giờ trong ngày (nếu có) phải dịch cho đúng. 15 ô thí điểm **không** dùng lọc giờ (17 khoá tham số của cả 125 ô đều không có khoá giờ).
4. **Spread.** Engine của the-brain đọc spread từng nến từ cột `spread` trong dữ liệu của sàn (thiếu thì mặc định 2 pip). Dữ liệu công khai thường không có spread từng nến → brain2 phải tự đặt: chạy hai mức (ví dụ 1,5 và 2,5 pip — chỉ là gợi ý để biết độ nhạy, không phải số đo) và báo cả hai.
5. **Đổi tiền** (CAD ↔ USD, `f ≈ 1,3`): `04` P1 bước 3.
6. So *hình dạng* và *chênh giữa có tia / không tia*, không so từng con số (`04` P1 bước 7).

## 4. Lấy lịch sử lệnh — chỉ khi tới bước "LẤY → HIỂU"

Chưa cần cho P1 / P4 / P3. Cần khi brain2 muốn *làm lại một hệ có lãi sẵn* (dây chuyền của chủ dự án: TÌM → **LẤY lịch sử lệnh** → HIỂU luật → LÀM LẠI → THỬ → CHỈNH → demo).

- **Điểm xuất phát:** 31 ID trong `du_lieu/mql5_31_nguoi_thang.csv` (18 là lưới/DCA). Cột `ma_chinh_da_sua` là mã chính **sau khi sửa**: nhãn mã đời đầu sai 19/31 (`02` D5), nên đừng tin nhãn mã lấy từ HTML thô; đọc bảng *Distribution* có cấu trúc của trang tín hiệu. Hệ quả: nhóm 31 người thắng **không** phải "gần hết là lưới/DCA trên AUDCAD và anh em" — sau khi sửa chỉ 3/31 có mã chính là AUDCAD.
- **Lịch sử lệnh của MQL5 cần phiên đăng nhập** của chủ dự án (`02` D3–D4): dùng export chính thức `…/signals/<id>/export/positions` (CSV phân cách `;`, ngày mới nhất bị ẩn). Đây là **việc cần chủ dự án** (đăng nhập hoặc cấp phiên); đừng tự đăng ký tài khoản, tự tham gia nhóm / diễn đàn (`01` §9).
- **Nhịp:** 3–5 giây / yêu cầu; MQL5 chặn IP sau khoảng 50–150 yêu cầu. Gặp 403 / 429 / Cloudflare thì **dừng**, ghi mã lỗi và trang đã tới, lần sau làm tiếp từ đó (`02` D2, D4).
- **Nguồn thứ hai (chỉ khi sau này có MT5):** chạy nguyên gói của tác giả trên tester rồi lấy lịch sử lệnh của chính lần chạy đó (`02` D10, G). Chỉ giữ **thống kê tự suy ra**, không bao giờ commit bot.
- **Giữ lại gì:** thẻ cơ chế theo ID (công thức lot, bước, thoát…) và số thống kê. Không giữ lệnh thô, không giữ tên.

## 5. Công khai hay riêng tư

- Kho the-brain **công khai** (chủ dự án chọn 02/10/2026) → gói này đọc được không cần đăng nhập; **vì vậy** nó chỉ chứa số tự suy ra và ID.
- Brain2 công khai hay riêng tư thì phía the-brain không biết. Trước khi đẩy bất cứ thứ gì lên brain2: kiểm. Nếu brain2 là kho công khai thì áp đúng luật ở mục 2 (không bot, không lệnh thô, không tên, không khóa).
- Gói đã được quét bằng từ khóa trước khi đẩy (khóa / token / mật khẩu, địa chỉ thư, đường dẫn máy, số tài khoản, tên bot và tác giả đã biết). Không phép quét nào hoàn hảo: nếu bạn thấy một thông tin nhạy cảm, báo chủ dự án để gỡ.

## 6. Độ tươi và giới hạn của dữ liệu

- **Xuất ngày 10/10/2026** từ kho the-brain, commit `8a1151c`. Sổ tay có thể **cũ hơn** sổ tay thật ở máy nhà (máy nhà là nơi duy nhất ghi sổ cái).
- `vung_lai_trong_mau.csv`: cột `xac_nhan_ngoai_mau` **trống ở cả 1.055 dòng** = chưa dòng nào được kiểm ngoài mẫu. `ty_le_o_lai` là tỉ lệ trong mẫu; đừng đọc thành xác suất có lãi thật.
- `hieu_chuan_125_o.csv`: cột engine là **bản v3 (cực trị)**, chưa đo lại bản v4 (đường đi); chất lượng lịch sử tester không đều (53 ô sạch, 71 ô nửa chất lượng, 1 ô gần như không); toàn bộ `cho_lui = 0` và `chot_tien = 0` nên bảng **không** phủ lưới "chờ giá lùi" và "chốt tiền". Số `ket_luan` (KHOP / LECH) là nhãn dung sai chặt của the-brain, đừng học nhãn — học cột chênh.
- `mql5_400_phan_loai.csv`: nhãn `kieu` do luật thô khai báo trước; danh sách chỉ có tài khoản **còn sống** (thiên lệch sống sót) nên đọc là "kiểu này tồn tại và đo được", **không phải** "kiểu này ra tiền".
- Các con số phễu (12.078 → 285 → 18) là số **trước 02/10** lấy từ hồ sơ cũ, vì `nao.db` đã mất; chỉ dùng làm mốc xu hướng.
