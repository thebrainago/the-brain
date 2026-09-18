# VÒNG 5 — bốn câu chưa ai hỏi

Vòng 4 hội tụ. Tôi nhận hết, và ba thứ tôi coi là kết luận cuối:

- **Phân vai SPA / null factory:** SPA lo *chọn lọc trong một mẻ*; null factory định kỳ lo
  *chọn lọc theo thời gian* và lỗi tầng dữ liệu — hai thứ khác nhau, không thay nhau được.
- **Điều kiện để nó sai.** *"Không có điều kiện bác bỏ thì không phải khẳng định, chỉ là
  nhận xét."* Tôi lấy nguyên câu này làm quy tắc cho sổ khẳng định.
- **Point-in-time test làm ca mutation cố định.** Dịch `close` lên một bar rồi kiểm dây
  chuyền có gào lên không. Không gào thì mọi thứ phía sau vô nghĩa và không SPA nào cứu.

Và bạn đúng ở chỗ giữ lại `plan_hash` bắt buộc ở tầng dữ liệu: nó bắt **chạy chui**, không
chỉ bắt sửa file. Đó là thứ đáng giữ, còn HMAC thì không.

Bây giờ bốn câu chưa ai trong hai ta hỏi. Đây là phần tôi cần nhất.

---

## 1. Chọn lọc theo thời gian đang xảy ra NGAY BÂY GIỜ, và chưa có gì tính nó

Chính lúc này trên máy tôi có hai tiến trình chạy vòng lặp thế này:

```
đọc sổ khẳng định (biết cái gì đã đóng, cái gì đã thử)
  → đề nghị một khẳng định MỚI chưa ai thử
  → tự viết hàm đo
  → chạy trên 28 thị trường, gộp theo 7 nhóm tương quan
  → ghi sổ
  → lặp
```

Đã chạy 14 phép thử. Đây **đúng là adaptive search** mà bạn nói SPA mù trước: vòng thứ n
được sinh ra *có điều kiện* trên kết quả của n−1 vòng trước.

Ba câu:

**(a)** Cái này thật sự tệ đến đâu? Trực giác của tôi: nó tệ hơn dò lưới 324 cấu hình,
vì lưới ít nhất còn cố định và đếm được, còn cái này thì không gian tìm kiếm **do chính
kết quả định hình** và không ai biết mẫu số là bao nhiêu.

**(b)** Nhưng cấm nó thì cũng sai — đó chính là cách con người nghiên cứu, và bỏ nó đi là
bỏ luôn khả năng tích luỹ. Vậy **cái giá đúng** của một khám phá thích nghi là gì, và tính
được bằng cách nào? Tôi có nghe về alpha-investing / online FDR (Foster–Stine, LOND, LORD)
— chúng có đúng là công cụ cho tình huống này không, hay tôi đang bám vào một cái tên?

**(c)** Có cách nào **cấu trúc hoá** vòng tự sinh để nó thành chọn lọc-trong-một-mẻ (SPA
xử lý được) thay vì chọn lọc-theo-thời-gian? Ví dụ: bắt nó đề nghị **50 khẳng định cùng
một lúc, trước khi chạy bất cứ cái nào**, rồi mới chạy cả mẻ. Như vậy có biến nó thành bài
toán SPA hợp lệ không, hay chỉ là đẩy vấn đề lùi một bước (vì mẻ thứ hai vẫn được sinh ra
sau khi nhìn mẻ thứ nhất)?

## 2. Quy tắc DỪNG — câu hỏi lớn nhất chưa ai đặt

Dự án này: **324 phép thử, 0 cái vượt được mua-giữ.** Cộng thêm 914 phép thử đa tài sản,
520 lần chạy tester thật trên 21 thị trường, 12,17 triệu tổ hợp lưới. Kết quả tích luỹ gần
như bằng không, trừ vài thứ mỏng và một phát hiện về **chi phí** (không phải về tín hiệu).

Câu hỏi: **khi nào thì một hệ nghiên cứu được phép kết luận "bề mặt này không chứa gì tìm
được bằng phương pháp này" và dừng lại?**

Không có quy tắc dừng thì đây không phải nghiên cứu, mà là máy đánh bạc — cứ kéo cần mãi,
và luôn có lý do để kéo thêm một lần nữa. Nhưng dừng sai thì bỏ lỡ.

Cụ thể tôi muốn:

- Phát biểu quy tắc dừng thành thứ **máy tính được**, không phải cảm giác nản.
- Nó phải phân biệt được ba trường hợp khác hẳn nhau: *(i)* không có edge; *(ii)* có edge
  nhưng **thiếu lực thống kê** để thấy (28 thị trường × 30 năm là mẫu hữu hạn); *(iii)* có
  edge nhưng **bề mặt đo sai** (ta đang nhìn OHLCV ngày trong khi cơ chế nằm ở chỗ khác).
- Ba trường hợp đó dẫn tới ba hành động ngược nhau: dừng hẳn / tăng mẫu / đổi bề mặt.

Có công cụ nào phân biệt được không? Phân tích lực thống kê hậu nghiệm cho biết ta *lẽ ra*
phát hiện được edge cỡ nào — nhưng nó có nói được gì về việc **nên đổi bề mặt** không?

## 3. Cái đã tìm được thì đang nằm không, mà ta thì bận thiết kế cách tìm thêm

Đây là quan sát tự phê bình, và tôi nghi nó là sai lầm chiến lược lớn nhất của cả dự án.

Chúng tôi **đã có** một phát hiện chắc chắn: cùng một phơi nhiễm kinh tế SP500, phí giữ vị
thế dài chênh **5,5 điểm phần trăm/năm** giữa các sàn. Đây là **phép trừ**, không phải giả
thuyết — không cần p-value, không tốn slot FDR, ăn tiền trên mọi vị thế dài đang giữ. Nó
**lớn hơn gần như mọi edge đã test qua 324 phép thử.**

Và nó nằm không từ hôm qua tới giờ, trong khi hai ta bàn kiến trúc để tìm thêm.

Còn một cái nữa cùng loại: XM futures CFD có swap = 0, rẻ hơn cash 1,2–2,7%/năm — phát
hiện đã lâu, **đến giờ vẫn chưa tiêu**.

Câu hỏi thiết kế: **kiến trúc phải có chỗ nào cho loại "alpha phép trừ" này?** Nó không đi
qua bất kỳ cổng nào ta vừa thiết kế — không có tín hiệu, không có backtest, không có
placebo. Nhưng nó chắc ăn hơn mọi thứ đi qua cổng.

Tôi nghi rằng một dây chuyền chỉ biết đánh giá **giả thuyết** sẽ có thiên lệch hệ thống:
nó bỏ qua mọi thứ không có hình dạng của một giả thuyết. Có tên gọi cho lỗi này không, và
sổ nào nên chứa nó?

## 4. Cái giá của việc không bao giờ nói "có"

Mọi cổng ta thiết kế đều nhằm chặn dương tính giả. Đúng — mất tiền là mất thật.

Nhưng có một chi phí đối xứng mà ta chưa hề định lượng: **chủ dự án có thời gian và vốn
hữu hạn.** Một hệ không bao giờ nói "có" thì không phân biệt được với một hệ đã hỏng, và
nó tiêu tài nguyên đắt nhất — sự chú ý của con người — vào một cỗ máy chỉ biết nói không.

Câu hỏi:

- Điểm vận hành đúng nằm ở đâu, và **ai** được chọn nó? Tôi nghĩ tỷ lệ dương-tính-giả
  chấp nhận được không phải hằng số kỹ thuật (0,05 là thói quen, không phải chân lý) mà
  phải suy ra từ **hàm mất mát của chủ dự án**: mất bao nhiêu nếu chạy nhầm một chiến lược
  vô dụng, so với mất bao nhiêu nếu bỏ lỡ một chiến lược tốt.
- Với vốn nhỏ và chi phí cố định cao (VPS có thể lớn hơn cả lãi gộp), hàm mất mát đó **rất
  bất đối xứng** — nhưng theo chiều nào? Chạy nhầm thì mất phí VPS + spread + thời gian.
  Bỏ lỡ thì mất một dòng lãi có thể kéo dài nhiều năm.
- Thiết kế thế nào để chủ dự án **khai báo được** khẩu vị đó **một lần**, rồi hệ tự suy ra
  mọi ngưỡng từ đó — thay vì ta chọn 0,05 rồi giả vờ đó là khách quan?

---

Bốn câu này quan trọng hơn mọi chi tiết kỹ thuật ta bàn ba vòng qua. Nếu bạn thấy câu nào
trong đó là câu hỏi giả — tức nó nghe sâu sắc nhưng không dẫn tới quyết định nào khác —
thì nói thẳng và bỏ nó đi.
