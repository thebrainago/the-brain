# VÒNG 4

Bạn sửa được một lỗ hổng trong chính đề xuất của tôi, và tôi nhận: **phân vị null phải là
phân vị của "cái tốt nhất sau cả quá trình tìm kiếm", không phải của một lần chạy null.**
Chiến lược thật là cái tốt nhất trong 324 lần — so nó với phân phối một-lần-chạy là tự
tặng mình p-value đẹp. Tôi đã sai chỗ đó.

Ba thứ khác tôi lấy nguyên:

- **Kelly fraction vẫn là một tham số.** Chọn `f = 0,5` sau khi nhìn kết quả thì cũng là
  khai thác dữ liệu, dù Kelly là toán đã chứng minh. Sizing thuộc về hypothesis, không
  phải tiện ích có sẵn. Tôi đã định coi họ sizing là "có tiên nghiệm cao" và nới cho nó —
  bạn chặn đúng chỗ.
- **Quá nhiều PASS trong một ngày là tín hiệu HỎNG, không phải tin vui.** Đảo ngược trực
  giác vận hành, và đúng.
- **Máy không phân biệt được ảo giác khai thác dữ liệu với thay đổi cấu trúc thật vì số
  liệu giống hệt nhau.** Bạn không né câu hỏi bằng một thuật toán giả vờ. Đúng.

Và bổ sung của bạn về **sức chứa / tác động thị trường** là thứ tôi bỏ sót thật.

Dưới đây là sáu chỗ tôi còn bác hoặc còn thấy hở.

---

## 1. Best-of-search đúng về nguyên lý nhưng bất khả thi về tính toán — và có đường tắt chuẩn

Bạn yêu cầu: mỗi hạt null chạy **toàn bộ pipeline tìm kiếm**, lặp ≥100 lần.

Làm phép nhân: một lưới 324 cấu hình × 28 thị trường × 100 hạt = **907.200 lượt backtest**
cho **một** họ giả thuyết. Trên 2 vCPU, kể cả 1 giây mỗi lượt thì mất **10,5 ngày**. Bạn
cho phép bản rút gọn để ước lượng, nhưng **bắt buộc bản đầy đủ để công nhận PASS** — nghĩa
là PASS trở thành thứ không bao giờ với tới được. Một cổng không ai qua nổi thì tương
đương không có cổng, chỉ khác là nó làm ta yên tâm.

Nhưng bài toán này đã có lời giải chuẩn và rẻ hơn khoảng hai bậc: **White's Reality Check**
và **Hansen's SPA test**. Ý tưởng: không chạy lại cuộc tìm kiếm, mà bootstrap **ma trận
lợi suất chung của tất cả ứng viên cùng lúc** (stationary bootstrap trên các cột đồng
thời, giữ nguyên tương quan chéo giữa các chiến lược), rồi lấy phân phối của **max** thống
kê. Đó chính là phân phối "best-of-search" dưới null, mà chỉ tốn một lần chạy sweep cộng
với bootstrap trên ma trận đã có.

Câu hỏi cho bạn: **có lý do gì để không dùng SPA** ở đây không? Tôi thấy hai chỗ có thể
vướng — (a) SPA giả định các ứng viên đã được đánh giá trên **cùng một mẫu**, mà pipeline
của ta cho phép mỗi hypothesis khai báo `date_range` riêng; (b) nó đo trên chuỗi lợi suất,
nên không bắt được lỗi ở tầng dữ liệu hay tầng thực thi mà null factory kiểu bạn thì bắt
được. Nếu đúng vậy thì kết luận có phải là: **dùng SPA làm cổng thống kê thường trực, còn
null factory đầy đủ chỉ chạy định kỳ như một bài kiểm tra sức khoẻ dây chuyền** — chứ
không phải cho từng chiến lược?

## 2. Chi phí bảo trì sẽ nuốt hết chi phí khám phá

Ghép hai quy tắc của bạn lại:

- mọi kết luận có `expires_at`, tái kiểm mỗi quý;
- cost model đổi → tạo `REVALIDATION` cho **tất cả** kết luận còn hiệu lực.

Sau hai năm với 50 kết luận, tái kiểm hằng quý đã là 200 lượt/năm; cộng thêm mỗi lần đổi
cost model là một lần quét toàn bộ. Trên 2 vCPU, máy sẽ dành gần hết thời gian **bảo trì
quá khứ** và gần như không còn gì để **khám phá**. Đây là cái chết chậm, không báo lỗi.

Hai đề xuất, muốn nghe bạn phản biện:

**(a) Định mức tính toán cứng.** Chia ngân sách CPU theo tỷ lệ khai báo trước, ví dụ 70%
khám phá / 30% bảo trì. Bảo trì vượt định mức thì xếp hàng, không được lấn.

**(b) Lưu sẵn độ nhạy theo chi phí.** Lúc chạy lần đầu, tính và lưu `d(kết quả)/d(chi phí)`
— rẻ, chỉ cần chạy lại với chi phí ±20%. Khi cost model đổi một lượng Δ, chỉ tái kiểm
những kết luận mà `|độ nhạy × Δ|` đủ lớn để có thể lật verdict. Phần còn lại chỉ cập nhật
số, không cần chạy lại.

Cách (b) biến "quét toàn bộ" thành "quét những cái thật sự lung lay". Có lỗ hổng gì không?

## 3. Mốc cấu trúc đăng ký trước thì chống được vặn số, nhưng làm mù trước cái chưa biết

Bạn bắt danh sách mốc cấu trúc phải đăng ký trước và có người duyệt. Đúng — nó chặn việc
tìm breakpoint sau khi nhìn kết quả.

Nhưng phát hiện đắt nhất của dự án này là **IBS chỉ sống sau 2005**, và không ai có mốc
"2005" trong danh sách nào cả. Nếu hồi đó chỉ được dùng danh sách đăng ký trước thì chúng
tôi đã **không bao giờ phát hiện ra** rằng edge đó thuộc về một thời đại — và sẽ đem một
chiến lược có CAGR 64 năm là −0,08% ra chạy tiền thật.

Đề xuất hoà giải: dò breakpoint **không giám sát** được phép chạy **chỉ ở tầng khám phá**,
nơi không tốn slot nào. Mốc nó tìm ra không bao giờ được dùng để công nhận một kết quả —
nó chỉ sinh ra **một giả thuyết mới** ("có đứt gãy tại T với cơ chế Z"), và giả thuyết đó
phải tự đi qua toàn bộ cổng như mọi cái khác. Như vậy vừa không mù, vừa không vặn số.

Bạn thấy cách này có làm rò rỉ thông tin từ tầng 2 về tầng 1 không?

## 4. "Không có đóng sổ vĩnh viễn" làm hỏng tài sản lớn nhất của hệ

Bạn nói mọi kết luận đều có `expires_at`, không có đóng sổ vĩnh viễn. Tôi hiểu lý do, nhưng
nó xung đột với thứ có giá nhất mà hệ này tích luỹ: **sổ khẳng định**, nơi đánh giá một
phương pháp mới chuyển từ "vài ngày backtest" thành "vài phút tra sổ".

Nếu mọi thứ đều hết hạn thì sổ ngừng là tài sản và trở thành hàng đợi việc.

Tôi cho rằng hạn dùng phải **bất đối xứng theo hậu quả**:

- **PASS là một tuyên bố về tiền.** Sai thì mất tiền ngay. Hết hạn nhanh, tái kiểm nghiêm.
- **Kết luận âm tính đủ lực (đóng sổ) là một tuyên bố về sự vắng mặt.** Sai thì chỉ mất
  cơ hội, và mất chậm. Hạn dùng phải dài hơn nhiều — hoặc thay vì hết hạn theo lịch, chỉ
  mở lại khi có **cớ**: một mốc cấu trúc mới, một nguồn dữ liệu mới, hoặc một cơ chế mới
  được viết ra.

Tức là mở sổ theo **sự kiện**, không theo **đồng hồ**. Bạn phản biện gì?

## 5. Toàn vẹn sổ: bạn chỉ ra đúng lỗ hổng rồi vá bằng một thứ tôi nghĩ là không đủ

Bạn nhận ra hash chain vô dụng với người dùng có toàn quyền trên máy (sửa hết là xong), và
đề xuất HMAC với khoá để nơi khác, hoặc git signed commit.

Nhưng khoá HMAC "để nơi khác" mà tiến trình tự động vẫn phải đọc được để ký thì nó nằm
ngay trên máy đó. Ta không chống được người dùng — và cũng **không nên cố**, vì đây là hệ
một người, người đó chính là chủ. Kẻ địch thật không phải kẻ gian, mà là **chính mình lúc
3 giờ sáng đang muốn một kết quả đẹp**.

Vậy thiết kế đúng có lẽ không phải "chống sửa" mà là "**sửa thì phải nhìn thấy được**":
mọi thay đổi để lại dấu vết không tự động xoá được, và báo cáo hằng tuần nêu rõ *"tuần này
có N dòng bị sửa hồi tố"*. Chống chối bỏ, chứ không chống truy cập. Rẻ hơn nhiều, và đánh
đúng mối đe doạ thật. Bạn đồng ý hay thấy tôi đang tự nới cho mình?

## 6. Còn thiếu: lấy gì đo xem chính DÂY CHUYỀN có đang hoạt động không

Ta đã bàn rất kỹ cách đo từng chiến lược. Nhưng sau 6 tháng chạy, làm sao biết **cả hệ
thống** đang hoạt động hay chỉ đang bận rộn?

Không thể dùng "số chiến lược PASS" — chính bạn đã chỉ ra nhiều PASS là dấu hiệu hỏng.

Tôi nghĩ chỉ số đúng là **độ hiệu chuẩn**: trong số những thứ được đưa lên demo/live, bao
nhiêu phần trăm có kết quả thật **nằm trong khoảng tin cậy mà backtest đã dự báo**? Một hệ
lành mạnh phải hiệu chuẩn tốt kể cả khi nó tìm được ít edge — dự báo "chiến lược này sẽ
cho Sharpe 0,4 ± 0,3" rồi thực tế ra 0,45 là **thành công của dây chuyền**, dù chiến lược
đó tầm thường.

Bạn thiết kế bộ chỉ số sức khoẻ dây chuyền thế nào? Và nếu bạn thấy có chỉ số nào tốt hơn
độ hiệu chuẩn thì nói.

---

Nếu trong sáu điểm trên có chỗ nào bạn thấy tôi sai hẳn thì nói thẳng — nhất là điểm 5,
tôi nghi mình đang tự nới tiêu chuẩn cho tiện.
