# 06 — GỢI Ý VIỆC TIẾP (ý kiến của Claude — KHÔNG phải lệnh của chủ dự án)

> Mọi thứ ở đây là **khuyến nghị**. Quyền quyết là của chủ dự án và của brain2 (brain2 hiểu mã của mình hơn Claude: Claude chỉ đọc nó ở chế độ chỉ-đọc, commit `129f6a6` ngày 10/10/2026, và nó có thể đã đổi).
> Lệnh thật của chủ dự án ở `01`. Chỗ nào gợi ý này xung đột với `01`, `01` thắng.
> Mỗi gợi ý ghi: **tốn gì · xong khi nào · dừng khi nào**.

## 0. Một câu để chọn việc

Câu của chủ dự án: *"việc này đưa một thứ ĐANG RA TIỀN lại gần 'của ta' hơn không?"*. Ba việc đầu bên dưới **không tự tạo ra hệ nào ra tiền**; chúng làm cho con số "ra tiền" của brain2 **đáng tin** — rẻ nhất và đổi nhiều nhất cách đọc mọi kết quả về sau. Có chúng rồi thì tiêu máy vào việc tìm thêm mới có nghĩa.

## 1. Việc đầu (theo thứ tự)

| # | Việc | Tốn | Xong khi | Dừng nếu |
|---|---|---|---|---|
| 0 | Hỏi chủ dự án MỘT câu về cổng duyệt (`01` §3) | một tin nhắn | có câu trả lời | – |
| 1 | **P1** — kiểm mô phỏng lưới H1 của brain2 bằng 15 ô sạch (`04` P1) | 0 đồng · 1 nhân CPU · vài giờ công | có bảng "chênh có tia / không tia" kèm *khoảng* giữa ≥ 3 thứ tự giá trong nến | không tải được nến trực tiếp của cặp chéo → ghi CHƯA ĐO ĐƯỢC, đừng ghép từ cặp USD (`05` mục 3) |
| 2 | **P4** — đối chứng nhiễu ở cấp đường ống (`04` P4) | 0 đồng · ≈ 100–150 dòng · vài phút / nhân | mỗi lần "duyệt" in kèm *tỉ lệ chuỗi chỉ-nhiễu cũng qua* | – |
| 3 | **P3** — swap theo từng lệnh + phí đúng thời kỳ (`04` P3; hai lỗi tồn đã có trong ghi chú của brain2) | ≈ 80–150 dòng | lãi sau swap khớp công thức trong `04` P3 | – |

Gợi ý P1 trước P4 vì P1 trả lời "mô phỏng lưới của mình lệch thực tế bao nhiêu", P4 trả lời "cổng của mình để lọt nhiễu bao nhiêu". Cả hai đều rẻ; nếu chỉ làm được một thì làm P1 khi brain2 sắp tin một con số lãi lưới, làm P4 khi brain2 sắp mở rộng quét.

## 2. Sau đó: hướng ra tiền (ba giả thuyết có chủ đích — KHÔNG phải kết luận)

Bài học đo được (`02` C3, `03` R13): quét rộng ≈ 3.000 điều kiện chỉ thấy cạnh yếu ở 3/8 chuỗi có đáp án; một giả thuyết có chủ đích thấy 8/8. Nên đi từ giả thuyết có *lý do*, kèm chuỗi đối chứng. Ba ví dụ lấy từ sổ tay (`du_lieu/so_tay_nghien_cuu/gia_thuyet.jsonl`):

- **G-a — quản lí lệnh quyết định, entry không.** Cùng luật lưới, đổi entry (vào ngay / theo xu hướng / hồi quy / ngẫu nhiên cùng tần suất) → lãi sau phí không khác nhau nhiều trên tài sản hồi quy. Kèm: tỉ lệ "ô có lãi trong mẫu" trên random walk để biết *nền* (sổ tay: giả thuyết 2).
- **G-b — chọn tài sản.** Luật lưới có lãi trên tài sản hồi quy (cặp chéo FX, vàng) nhưng không trên tài sản xu hướng (chỉ số). Nguồn gợi ý: phép đo PMG ngày 14/09 (cặp chéo FX và vàng hồi quy ở mọi thang đo, chỉ số gần như không) — là *nguồn gợi ý*, chưa phải bằng chứng (sổ tay: giả thuyết 3).
- **G-c — làm lại một hệ có lãi sẵn.** Lấy một ID trong 31 người thắng, bóc luật từ lịch sử lệnh (`04` P6), chạy lại trên giá của brain2 và **cũng** chạy trên giai đoạn *trước* khi hệ đó bắt đầu (kiểm "cơ chế hay chỉ gặp may") (sổ tay: giả thuyết 1 và 4).

Việc nào cũng: **đóng băng kế hoạch trước** (hash), kiểm ngoài mẫu **một lần** trên đoạn khoá theo ngày (`02` C6), ghi sổ, gắn nhãn "mô phỏng" cho tới khi có demo.

## 3. Về máy, nhân CPU, VPS (ràng buộc ở `01` §7)

- Ở the-brain, **84 % giờ máy là quét trong mẫu** và **0/698 vùng lãi từng được kiểm ngoài mẫu** (`03` R12). Đọc của Claude: phần lãng phí là **nhắm sai chỗ** (nhiều vùng lãi trong mẫu mà không ai kiểm), không phải thiếu nhân. Thêm nhân / VPS vào đúng chỗ đó chỉ sinh thêm "vùng lãi trong mẫu" nhanh hơn.
- Trước khi đề nghị mua gì: đo xem nghẽn ở **tính toán** (một ô tốn bao nhiêu giây, thật sự cần bao nhiêu ô) hay ở **kế hoạch** (quét thừa). Đo bằng đồng hồ, không đoán. Ước lượng tuyến tính của Claude: ≈ 1 giây / ô trên ≈ 116.000 nến H1 → 1.000 ô ≈ 17 phút một nhân — **chưa đo trên brain2**.
- Nhân C (`04` P2): có sẵn, nhưng chỉ nên nhắc tới khi *đo thấy* tốc độ là nghẽn.
- MT5 tester chỉ có **một khe** (ràng buộc vật lý, `02` F3): đó là giới hạn về *thời gian*, không giải bằng thêm nhân. Brain2 chưa chạy MT5: bảng 125 ô (P1) là thứ thay tạm.
- Muốn một phiên MT5 thật để hiệu chuẩn H1 (`04` P7): **hỏi chủ dự án**, kèm số đo vì sao P1 chưa đủ.

## 4. Đừng làm (tóm tắt — đầy đủ ở `04`)

Đừng bê bộ bóc cơ chế, bộ đọc diễn đàn / Telegram, kênh `b cau` / `viec/`, hàng đợi tài liệu tồn, hay luật "máy bật là chạy hết công suất" sang brain2. Đừng nới cổng chặn khi chưa hỏi chủ dự án. Đừng gọi một kết quả mô phỏng là "ra tiền".

## 5. Điều Claude CHƯA biết về brain2

- Brain2 hiện có gì ngoài commit `129f6a6`; brain2 công khai hay riêng tư; brain2 chạy trên máy nào.
- Brain2 có sẵn nguồn giá H1 tốt cho cặp chéo AUDCAD / NZDCAD trong cửa sổ 2019 hay không (P1 cần nó).
- Chủ dự án muốn brain2 duyệt theo tiêu chí 25/09 hay giữ cổng hiện tại (câu hỏi #0).

Nếu một gợi ý ở trên không hợp thực tế của brain2, **bỏ nó** — và ghi lý do vào sổ tay để lần sau không bị gợi lại.
