# HỎI: có đường hợp lệ nào để tự động lấy chiến lược từ MQL5 CodeBase không?

Bối cảnh: tôi đang cần một dòng chảy tự động các chiến lược để dây chuyền nghiên cứu có
cái mà bóc tách. Hôm nay tôi lấy được `geraked/metatrader5` từ GitHub (giấy phép MIT, 590
sao, 11 EA) — hợp lệ và sạch. Nhưng GitHub chỉ có một phần nhỏ; kho lớn nhất là **MQL5
CodeBase** trên mql5.com.

Trước đây dự án đã thử và **gặp 403**, nên tôi ghi vào tài liệu là "điều khoản cấm, dùng
thư mục `nap_tay/`". Chủ dự án nghi rằng tôi kết luận vội và có thể có đường hợp lệ tôi
chưa nghĩ tới. Tôi đồng ý là có thể. Nên hỏi bạn nghiêm túc.

**Tôi không hỏi cách vượt rào.** Không hỏi cách đổi User-Agent, xoay IP, giả trình duyệt,
hay né rate limit. Nếu điều khoản của họ cấm thì tôi tôn trọng. Tôi hỏi là: **có kênh
CHÍNH THỨC hoặc HỢP LỆ nào mà tôi chưa biết không?**

Cụ thể xin bạn trả lời từng cái:

1. **MetaEditor có sẵn trình duyệt CodeBase** ngay trong phần mềm — đó là client chính
   thức của chính nhà cung cấp. Tải qua đường đó có khác về mặt điều khoản so với gọi HTTP
   không? Và có tự động hoá được không (dòng lệnh, script MQL5, hay thư mục cache mà
   MetaEditor lưu lại sau khi tải)?

2. **MQL5.com có RSS/feed công khai nào** cho CodeBase hoặc Articles không? Feed công khai
   thường là kênh nhà cung cấp *cố ý* mở cho máy đọc.

3. **Điều khoản thật sự nói gì?** Tôi đang suy từ một mã lỗi 403 chứ chưa đọc kỹ. 403 có
   thể chỉ là chặn User-Agent thiếu, không nhất thiết là cấm về mặt pháp lý. Phân biệt hai
   thứ đó giúp tôi: cấm về điều khoản thì dừng hẳn; chỉ là rào kỹ thuật với nội dung công
   khai thì phải xem lại.

4. **Nguồn thay thế cùng loại nội dung, giấy phép rõ ràng.** Ngoài GitHub, còn kho nào
   chứa EA/indicator mã nguồn mở đủ nhiều để nuôi một dây chuyền? Tôi biết có
   `EA31337`, `EarnForex`. Còn gì nữa? Và với Pine Script thì sao?

5. **Tác giả tự đăng lại.** Nhiều tác giả CodeBase cũng đẩy code của họ lên GitHub. Có
   cách nào lập bản đồ *"bài CodeBase X ⇄ repo GitHub Y"* một cách hệ thống không, để lấy
   từ nơi có giấy phép rõ ràng?

6. **Câu quan trọng nhất — có đáng không?** Sổ khẳng định của dự án này vừa loại **9 trên
   11** EA của kho GitHub kia trong một phút, vì chúng rút hết về hai họ đã đóng sổ (xu
   hướng-momentum và mốc giá) sau 12,17 triệu tổ hợp. Nếu CodeBase cũng có phân bố tương
   tự — mà tôi đoán là còn nghiêng hơn về hai họ đó — thì cào thêm 5.000 script sẽ cho
   thêm bao nhiêu khẳng định MỚI?

   Nhắc lại một con số của chính dự án: nạp thêm ứng viên làm **siết ngưỡng cho tất cả**
   những ý tưởng đã có (40 phép thử → t≈2,73; 306 phép thử → t≈3,48). Vậy nếu tỷ lệ khẳng
   định mới trên mỗi script là rất thấp, việc cào rộng có thể là **âm giá trị**.

   Bạn nghĩ điểm cân bằng nằm ở đâu? Và có cách nào **lọc trước khi tải** — ví dụ chỉ lấy
   những script mà mô tả cho thấy nó KHÔNG rút về hai họ đã đóng?

Trả lời thẳng. Nếu câu trả lời là "không có đường hợp lệ nào và cũng không đáng" thì cứ
nói vậy — đó cũng là một kết luận dùng được.
