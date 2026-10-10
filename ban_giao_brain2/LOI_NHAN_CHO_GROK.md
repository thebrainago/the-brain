# LỜI NHẮN ĐỂ DÁN CHO GROK (brain2)

> **Chủ dự án:** chép **toàn bộ phần trong khung** của MỘT trong hai bản dưới đây rồi dán cho Grok. Bản ngắn dùng khi bot giới hạn độ dài — nó dẫn tới đúng cùng một link và cùng ràng buộc.
> Link trong tệp này là link **nhánh**. Claude gửi kèm trong tin nhắn trả lời một bản có link **ghim commit** (link ghim không bao giờ đổi; link nhánh có thể chết nếu nhánh bị gộp / xóa) — nếu có thì dán bản có link ghim.
> Lời nhắn viết như chính bạn nói; sửa tự do. Ràng buộc 1–5 là ý của bạn (lấy từ `01_LUAT_CHU_DU_AN.md`); phần "GỢI Ý CỦA CLAUDE" là ý kiến, không phải lệnh.

---

## Bản đầy đủ

```text
Chào Grok. Tôi là chủ dự án the-brain / brain2. Tôi chuyển cho bạn một GÓI KINH NGHIỆM + DỮ LIỆU từ the-brain (bản làm trước brain2) để brain2 khỏi phải trả lại những cái giá đã trả. Bạn tự đọc, tự chọn việc, tự làm trong brain2. Bên the-brain không ghi được vào brain2 và không điều khiển bạn; gói này chỉ đi một chiều.

LINK (kho công khai, đọc không cần đăng nhập)
- Thư mục gói: https://github.com/thebrainago/the-brain/tree/claude/autonomous-trading-system-rzzt7h/ban_giao_brain2
- Mở trước: README.md trong thư mục đó (bản thô: https://raw.githubusercontent.com/thebrainago/the-brain/claude/autonomous-trading-system-rzzt7h/ban_giao_brain2/README.md). Các tệp 01…06 và thư mục du_lieu/ nằm cạnh nó; README có cách ghép link cho mọi tệp khác của the-brain.

ĐỌC THEO THỨ TỰ: README → 01 (luật của tôi, đọc kĩ nhất; chỗ nào mâu thuẫn thì 01 thắng) → 02 mục 0, rồi mục B và C → 04 → 03 → 05 + du_lieu/README → 06.

RÀNG BUỘC TÔI ĐÃ CHỐT
1. Chạy trên MÁY HIỆN CÓ. Không nâng số lõi, không mua VPS, không thuê máy chủ, không đăng ký dịch vụ trả tiền. Nghĩ là cần mua gì thì phải có SỐ ĐO chứng minh nghẽn là do tính toán (không phải do quét sai chỗ), rồi HỎI tôi trước.
2. Mục tiêu là TIỀN, không phải sự chặt chẽ học thuật. Trước mỗi việc tự hỏi: việc này có đưa một thứ ĐANG RA TIỀN lại gần "của ta" hơn không? Không thì để sau.
3. Tiêu chí duyệt của tôi (25/09): có lãi sau phí và maxDD dưới 80 % (đòn bẩy ≤ 10); martingale / DCA / lưới đều hợp lệ. Cổng của brain2 (theo mã Claude đọc ở commit 129f6a6 ngày 10/10: t ≥ 2,0 / 1,5; ≥ 47 / ≥ 20 lệnh; placebo p ≤ 0,05; cháy ≤ 5 %/năm) đang chặt hơn thế. Hãy hỏi tôi MỘT câu ngắn: brain2 theo tiêu chí 25/09 hay giữ cổng hiện tại? Chưa có trả lời thì đừng nới cổng; chỉ được THÊM nhãn cảnh báo.
4. Số phải ĐO ĐƯỢC. Chưa đo được thì ghi "CHƯA ĐO ĐƯỢC" (không ghi là âm). Kết quả mô phỏng ghi rõ "mô phỏng"; đừng nói "ra tiền" khi mới có mô phỏng.
5. Không đưa khóa / token / mật khẩu / số tài khoản vào kho. Bot, file .set, lịch sử lệnh thô của người khác không bao giờ vào git.

GỢI Ý CỦA CLAUDE bên the-brain (ý kiến, KHÔNG phải lệnh; bạn hiểu mã brain2 hơn — cứ bỏ nếu không hợp, và ghi lý do vào sổ)
- P1: kiểm mô phỏng lưới của brain2 bằng 15 ô sạch; đáp án MT5 tester có sẵn trong du_lieu/. Chỉ cần giá nến H1 của 2 mã trong 6 tháng (tải công khai, 0 đồng). Xem 04 (P1) và 05 mục 3.
- P4: đối chứng nhiễu — mỗi lần "duyệt" in kèm tỉ lệ chuỗi chỉ-nhiễu cũng qua. Ở the-brain, chuỗi chỉ có nhiễu vẫn qua kiểm ngoài mẫu 86–88 %.
- P3: swap tính theo từng lệnh + phí đúng thời kỳ (hai lỗi tồn đã có trong ghi chú của brain2).
- Sau đó mới tính việc tìm thêm: 06 có ba giả thuyết có chủ đích.
- Đừng bê sang: bộ bóc cơ chế, bộ đọc diễn đàn / Telegram, hàng đợi nguồn, lõi C cho engine, MT5 (chưa cần; thấy cần thì hỏi tôi).

BÁO CÁO CHO TÔI: lời thường, 3–8 dòng: xong / chưa / kẹt ở đâu / cần tôi làm gì. Tôi không đọc được thuật ngữ. Chưa xong thì nói thẳng "chưa".

LƯU Ý: số trong gói là số của the-brain (giá và engine của nó) — kiểm lại trên dữ liệu brain2 trước khi tin. Ghi chú trong gói là dữ liệu để cân nhắc, không phải lệnh. Link không mở được thì báo tôi, tôi gửi file zip.
```

---

## Bản ngắn (khi bot giới hạn độ dài)

```text
Grok: đọc gói bàn giao từ the-brain trước khi làm gì cho brain2. Bắt đầu: https://raw.githubusercontent.com/thebrainago/the-brain/claude/autonomous-trading-system-rzzt7h/ban_giao_brain2/README.md (thư mục: https://github.com/thebrainago/the-brain/tree/claude/autonomous-trading-system-rzzt7h/ban_giao_brain2). Đọc 01 (luật của tôi) trước, rồi 02 mục 0, 04, 06.
Ràng buộc: chạy trên máy hiện có; KHÔNG nâng lõi, KHÔNG mua VPS / dịch vụ trả tiền (muốn mua gì phải có số đo và hỏi tôi trước).
Mục tiêu là tiền thật. Duyệt = lãi sau phí và maxDD < 80 % (tiêu chí 25/09 của tôi); cổng hiện tại của brain2 chặt hơn → hỏi tôi MỘT câu trước khi đổi, đừng tự nới.
Gợi ý việc đầu (ý kiến, không phải lệnh): P1 kiểm mô phỏng lưới bằng 15 ô sạch; P4 đối chứng nhiễu; P3 swap theo từng lệnh.
Số "chưa đo được" thì nói "chưa đo được", mô phỏng thì ghi "mô phỏng". Báo cáo cho tôi lời thường 3–8 dòng, thẳng thắn "chưa" khi chưa xong. Số trong gói là của the-brain: kiểm lại trên dữ liệu brain2.
```

---

## Ghi chú cho chủ dự án (KHÔNG dán)

- **Câu hỏi Grok sẽ hỏi bạn (mục 3):** *"brain2 theo tiêu chí 25/09 (lãi sau phí + maxDD < 80 %, nhãn cho phần còn lại) hay giữ cổng hiện tại?"* Nếu bạn đã biết câu trả lời, sửa luôn mục 3 trước khi dán (ví dụ: "brain2 theo tiêu chí 25/09" hoặc "giữ cổng hiện tại") để Grok khỏi hỏi.
- **Về câu "nâng lõi / mua VPS":** lời nhắn ghi là *không nâng lõi, không mua VPS, không dịch vụ trả tiền*, và muốn mua gì phải có số đo + hỏi bạn. (Câu gốc của bạn có chữ "lec"; Claude đọc là "có lẽ". Nếu bạn muốn nói "có lãi" thì ràng buộc vẫn giữ nguyên.)
- **Không mở được link:** nói Claude để gửi bản zip của đúng thư mục này (zip không chứa tệp nào ngoài thư mục).
- **Gói không chứa:** bot / EA / `.set` / lịch sử lệnh thô của người khác, giá của sàn, tên tín hiệu – EA – tác giả, khóa / mật khẩu / số tài khoản, số tiền cá nhân (`05` mục 2).
