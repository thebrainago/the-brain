# TIẾT KIỆM TOKEN — đo thật rồi mới sửa (02/10/2026)

> Chủ dự án: *"nghiên cứu cách tối ưu hệ thống và dùng token hiệu quả nhất, nếu không sẽ rất tốn"*.
> Số liệu dưới đây đo từ **chính transcript phiên cloud này** (642 gọi API, 3 lần nén ngữ cảnh) bằng `b token` (`nhan/do_token.py`).
> Đơn vị chi phí = 1 token đầu vào thường theo **tỉ lệ giá chuẩn** (đọc cache 0,1 · ghi cache 1 giờ 2 · đầu ra 5): là tỉ lệ, không phải tiền.

## 0. Đọc 1 phút

- **Chi phí = SỐ GỌI API × KÍCH THƯỚC NGỮ CẢNH.** Mỗi lần công cụ chạy xong là một gọi API mới, và mỗi gọi đọc lại *toàn bộ* ngữ cảnh.
  Độ dài từng tin nhắn gần như không quan trọng; số lượt và độ phình của ngữ cảnh mới quan trọng.
- Ngữ cảnh phình chủ yếu vì **chính AI viết ra** (thinking + lệnh + lời), không phải vì tài liệu hay kết quả lệnh.
- Hai thứ tốn bất ngờ: ngữ cảnh chỉ bị nén ở ~967k token (mặc định), và mỗi lần **nghỉ > 1 giờ** thì cả ngữ cảnh bị ghi lại cache (gấp 20 lần một lượt đọc thường).
- Đã sửa đúng các chỗ đó (mục 3). Ước tính tiết kiệm **~1/3 từ cửa sổ nén + thêm nếu hạ effort**, chưa đo lại sau thay đổi (mục 7).

## 1. Số đo thật (phiên cloud, `b token`)

| Chỉ số | Giá trị |
|---|---|
| Chi phí theo thành phần | đọc cache **63,7%** · ghi cache **19,6%** · đầu ra **16,7%** · đầu vào thường 0,0% |
| Thinking trong đầu ra | **59%** (829k / 1,47M token ra) |
| Ngữ cảnh mỗi gọi | trung bình **443k**, trung vị 450k, lớn nhất 781k (cửa sổ nén mặc định ≈ 967k) |
| Độ phình | +3,3–4,4k token mỗi gọi; mỗi cửa sổ 179–210 gọi rồi mới nén |
| Token do AI sinh (đầu ra + "mang theo" trong ngữ cảnh) | **≈ 52%** tổng chi phí (đầu ra 16,7% + mang theo 35,0%) |
| Kết quả công cụ mang theo | 14,9% — nhưng 5 kết quả lớn nhất chỉ ≈ 1,8% |
| Tin người dùng + nhắc nhở hệ thống mang theo | 11,5% |
| Gọi "lạnh" (cache hết hạn, ghi lại > 50% ngữ cảnh) | **9 gọi = 8,9%** tổng; 4 lần nghỉ > 1 giờ (1,8 · 8,1 · 74 · 78,6 giờ) |

## 2. Mô hình chi phí (vì sao các con số trên)

- Một gọi ở vị trí *j* trong cửa sổ: `0,1 × (nền + 3,9k × j)` đọc cache + `5 × đầu ra` + `2 × token mới`. Nền ≈ 90k (hệ thống + CLAUDE.md + bản tóm tắt).
- Token AI viết ra ở gọi *k* bị đọc lại ở *mọi* gọi sau trong cửa sổ: giá thật của nó ≈ `2 + 5 + 0,1 × (số gọi còn lại)` — **gấp 3–5 lần giá đầu ra danh nghĩa**.
- Cache sống **1 giờ** (gói thuê bao; 5 phút nếu đang dùng usage credits). Thức dậy trong hạn: đọc `0,1×C`. Quá hạn: ghi lại `2×C`.
  Ví dụ C = 100k: ấm 10k, lạnh 200k đơn vị. Vì vậy **một lần thức dậy lạnh = 20 lần ấm**.
- Cửa sổ nén *W*: mỗi chu kỳ tốn thêm ≈ `0,1×W + 255k` (đọc cả ngữ cảnh + viết tóm tắt + ghi lại nền). Tối ưu nằm quanh **200–300k**
  (mô hình: 65k → 44k đơn vị / gọi = **−33%**; dưới 150k thì chi phí nén ăn hết lợi).

## 3. Đã làm

| Việc | Vì sao (số đo) |
|---|---|
| `.claude/settings.json`: `autoCompactWindow = 300000` | Ngữ cảnh TB 443k → ~195k (mô hình); áp cho mọi phiên mở repo này (cloud và nhà) |
| `b token`: đo lại bất cứ lúc nào, ở cả hai máy, kèm khuyến nghị theo ngưỡng | Để tối ưu theo số, không theo cảm giác; phiên nhà tự chạy và báo bản tóm tắt ~25 dòng |
| `b nc kiem 30` mặc định in **1 dòng ~700 ký tự** (trước: ~25.000; `-v` để in hết) | Mỗi ký tự in ra vào ngữ cảnh và bị đọc lại ở mọi gọi sau |
| `b cau noi` đến cloud **gộp** lần đánh thức trong 15 phút (`--thuc` để ép, chỉ cho việc CẦN cloud quyết) | Mỗi lần đánh thức = một lượt đọc cả ngữ cảnh cloud (lạnh nếu nghỉ > 1 giờ) |
| `b cau cho` chu kỳ **55 phút** (trước 7.000 giây) và "hết giờ thì chạy lại, không viết gì" — **HỦY 04/10/2026**: máy nhà chạy liên tục, không ngồi chờ (CLAUDE.md) | Hết giờ vẫn trong hạn cache: đọc 0,1× thay vì ghi lại 2× (ấm rẻ hơn lạnh ~4–9 lần) |
| Cầu chì thư: 8 thư / 30 phút / một chiều, quá thì `b cau noi` từ chối | Hai Claude cãi nhau vô hạn là cách đốt token nhanh nhất; chặn bằng mã, không bằng lời dặn |
| Nhãn thư theo vai: cloud → nhà = CHỈ THỊ; nhà → cloud = BÁO CÁO / ĐỀ XUẤT | Chủ dự án đã phân quyền cloud chỉ huy (02/10); bất đồng thì cloud quyết, không ai phải đoán |

## 4. Công tắc của chủ dự án (mình không tự đổi được)

1. **Effort.** Phiên cloud đang chạy `max` (mức đắt nhất). Mặc định của Opus 5.5 / Sonnet 5.5 là `medium`. Gõ `/effort high` (thiết kế, nghiên cứu)
   hoặc `/effort medium` (việc cơ học); để `max` cho bài khó. Không tắt được thinking trên các model này, nên effort là đòn bẩy duy nhất.
2. **Cửa sổ nén cho phiên đang chạy:** `/autocompact 300k` (file `.claude/settings.json` chỉ có hiệu lực từ phiên mới). Biến môi trường cloud:
   `CLAUDE_CODE_AUTO_COMPACT_WINDOW=300000` (thắng mọi cài đặt khác).
3. **Phiên mới sau mỗi mốc lớn:** mọi trạng thái nằm trong git (tài liệu, sổ cái, thư) nên phiên mới chỉ tốn ~90k nền. Phiên cloud mới: gửi thư cho nhà
   *"chạy `b cau dat-session <session_id mới>`"* (id lấy bằng công cụ `get_session`), kẻo nhà đánh thức nhầm phiên cũ (ngữ cảnh lớn, lạnh).
4. **Model:** việc cơ học (chạy lệnh, sửa nhỏ) làm bằng Sonnet; Opus cho thiết kế (khuyến nghị chính thức của Claude Code).

## 5. Giao thức hai phiên

- **Cloud chỉ huy, nhà thực thi** (chủ dự án 02/10/2026). Nhà thấy chỉ thị sai / không làm được → phản đối **đúng một lần** (bằng chứng + đề xuất); cloud trả lời **một lần** và quyết; nhà làm theo.
  Không bên nào cãi lại. Luật an toàn và việc không khứ hồi / đi ra ngoài vẫn hỏi chủ dự án. Hết hạn mức 8 thư/30 phút → tóm tắt 3 dòng cho chủ dự án chốt.
- **Thức dậy là tiền.** Chỉ gửi thư khi có việc (kết quả, câu hỏi, bị chặn); không "ok / cảm ơn"; thư dài ghi vào `reports/<tên>.md`. Chờ bằng lệnh không-LLM hoặc `send_later` một lần đúng lúc — không bao giờ tham dò bằng LLM.
- **Nhà ban đêm / đi vắng:** để runner không-LLM (`b cau chay`, lịch 5 phút) làm việc; phiên Claude Code nhà chỉ `cho` khi chủ dự án đang làm việc với nó.
- **Việc nặng nằm trong mã, không nằm trong LLM:** `b nc tu-lai`, `b nc cc`, `b test` chạy ở máy; phiên chỉ đọc bản tóm tắt gọn rồi quyết bước kế.

## 6. Không đáng tối ưu (đã đo)

CLAUDE.md ≈ 7,4k token (~1,7% chi phí đọc mỗi gọi ở ngữ cảnh hiện tại; khuyến nghị chính thức < 200 dòng, ta 390 dòng nhưng toàn luật đã sập thật — **không cắt**) ·
`b vao` ≈ 1,8k token một lần · `b nc` 62 · `b khoi-phuc` ≈ 840 · thư ≤ 2.000 ký tự · nhắc nhở danh sách việc (71 lần × ~845 token ≈ 1,3%).

## 7. Chưa đo / việc tiếp

- Mức tiết kiệm sau thay đổi: chạy `b token` ở phiên mới sau vài ngày, so với bảng mục 1. (Ước tính −33% từ cửa sổ nén là **mô hình**, không phải số đo; phần hạ effort chỉ là giả định.)
- Phiên nhà chưa có số đo: `b token` ở nhà rồi báo bản tóm tắt.
- Subagent: tài liệu chính thức khuyên dùng cho việc đọc nặng (ngữ cảnh riêng nhỏ, chỉ trả kết luận) và với ngữ cảnh 440k thì rẻ hơn rõ rệt; nhưng quy tắc phiên hiện tại không cho tự sinh subagent — cần chủ dự án đồng ý.
