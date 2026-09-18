# VÒNG 3 — ba chỗ còn bác, và bảy ngóc ngách chưa ai chạm

Bản v2 của bạn tốt hơn v1 rõ rệt. Ba thứ tôi lấy nguyên: hồi quy alpha Newey-West chống
đòn bẩy trá hình; pre-registration cưỡng chế ở **tầng dữ liệu** chứ không phải giấy tờ;
và mutation testing để null factory tự chứng minh nó nhạy. Cái thứ hai là câu trả lời
thật cho câu hỏi khó nhất — tôi không nghĩ ra được cơ chế đó.

## Phần 1 — ba chỗ còn sai

### 1.1. Null factory của bạn sẽ bỏ sót đúng cái bẫy đã cắn tôi ba lần hôm nay

Bạn bảo toàn `F_gap`, `F_duration`, `p_long`, `F_volume` rồi **bốc độc lập**. Nhưng chiến
lược thật vào lệnh **cụm lại theo chế độ**. V6 khai hoả khi IBS < 0,2, mà IBS thấp thì dồn
vào giai đoạn biến động cao. Null với khoảng cách i.i.d. sẽ **không cụm**, nên nó không
bắt được lỗi *"chiến lược này chẳng qua là ôm những giai đoạn biến động cao"*.

Hôm nay tôi sập bẫy này ba lần trong một buổi sáng: nó lật ngược kết luận luân phiên
(28/28 bác bỏ → 22/28 ủng hộ sau khi khử), và nó giết một kết quả z = +1,89 xuống −0,39.
Nếu null factory không cụm được thì nó sẽ **cấp giấy chứng nhận** cho đúng loại lỗi đó, ở
tầng dây chuyền, cho hàng trăm chiến lược cùng lúc.

Đề xuất: bốc thời điểm vào lệnh bằng **block bootstrap trên chính chuỗi chỉ báo vào lệnh**
của chiến lược thật, hoặc điều kiện `F_gap` theo tầng biến động. Bạn có cách nào tốt hơn?

### 1.2. Ngưỡng "null PASS > 9%" tính sai hướng

Bạn lấy Binomial(100; 0,05) rồi ra ngưỡng 9. Nhưng `alpha_nominal = 0,05` là **giả định**,
mà cổng PASS của bạn có 6 điều kiện đồng thời nên tỷ lệ lọt thật thấp hơn 0,05 nhiều lần.
Ngưỡng 9% vì thế quá lỏng — dây chuyền hỏng vừa phải sẽ lọt qua.

Nhưng có cách dùng cùng bộ máy đó mạnh hơn hẳn: **đừng kiểm định null PASS so với 0,05 —
hãy dùng chính tỷ lệ null PASS làm mức ý nghĩa ĐÃ HIỆU CHUẨN**. Tức thay vì hỏi "dây
chuyền có hỏng không", hỏi "chiến lược thật xếp ở phân vị nào của phân phối null". Cùng
100 lần chạy đó cho ra một ngưỡng thực nghiệm thay vì một hằng số bịa.

Nếu làm vậy thì null factory không còn là cổng phụ, nó thành **thước đo chính**. Bạn thấy
có lỗ hổng gì trong cách đó không?

### 1.3. Đổi cost model là một quyết định nghiên cứu, và bạn chưa cho nó hậu quả

Sổ có `cost_model_version` — tốt. Nhưng thiếu: khi cost model đổi thì **mọi PASS cũ phải
được kiểm lại tự động**, cái nào lật thì gắn cờ và hạ trạng thái.

Không phải giả định. Dự án đã sống qua đúng chuyện này: giả định spread 9 bps hoá ra thật
là 0,6–0,8 bps, và nó vô hiệu **mọi kết luận dạng "X chết vì cost"** từ trước mốc đó. Một
dây chuyền không có cơ chế này sẽ giữ nguyên hàng trăm kết luận đã mục.

---

## Phần 2 — bảy ngóc ngách chưa bản nào chạm tới

Đây là phần tôi muốn bạn đào sâu. Cứ nói dài ở chỗ đáng, và nếu thấy ngóc ngách nào tôi
nêu là không quan trọng thì nói thẳng là không quan trọng, đừng trả lời cho đủ.

### 2.1. Phi dừng theo thời đại — bài học thực nghiệm lớn nhất của dự án

Đây là phát hiện đắt nhất chúng tôi có: **IBS bắt đáy chỉ tồn tại sau 2005**. Trên 64 năm
lịch sử, CAGR là **−0,08%** và sụt giảm tối đa **−86%**. Cùng một quy tắc, cùng một tài
sản: một thời kỳ thì sống, cả thế kỷ thì chết.

Một dây chuyền coi lịch sử là một mẫu đồng nhất sẽ **liên tục tái phát hiện những edge đã
chết**, và mỗi lần đều có bảng số đẹp. Walk-forward hai nửa không bắt được — cả hai nửa
đều nằm trong cùng thời đại.

Câu hỏi: cơ chế nào phát hiện "edge này thuộc về một thời đại" **một cách tự động**? Và
quan trọng hơn — khi phát hiện rồi thì quyết định thế nào? Một edge chỉ sống sau 2005 có
thể là (a) ảo giác khai thác dữ liệu, hoặc (b) hệ quả thật của một thay đổi cấu trúc
(decimalization, ETF, HFT, lãi suất 0). Hai cái này dẫn đến hai quyết định ngược nhau, mà
số liệu thì giống hệt nhau. Máy phân biệt được không, hay đây là chỗ bắt buộc cần người?

### 2.2. Tầng danh mục và quản trị vốn — hiện đang trống hoàn toàn

Mọi thứ ta bàn đều là **một chiến lược đơn lẻ**. Nhưng:

- Ghép V6 với Session vàng cho tương quan **+0,03** và Calmar **0,75** — đó là cấu hình
  đầu tiên của cả dự án vượt được mua-giữ vàng. Tức **giá trị nằm ở chỗ ghép**, không nằm
  ở từng cái.
- Sizing có tiên nghiệm khác hẳn tín hiệu: Kelly và Turtles units là toán đã chứng minh,
  không phải chỉ báo bịa ra. Đáng có **họ FDR riêng**.
- Vol targeting đã thử và **làm xấu đi** (Sharpe 0,59 → 0,54, trượt placebo 86,7%) vì nó
  cắt size đúng lúc tín hiệu khai hoả.

Câu hỏi: thiết kế tầng danh mục thế nào để nó không thành một cuộc dò tham số khổng lồ
thứ hai? Nếu mỗi chiến lược có k tham số và ta có m chiến lược thì không gian ghép nổ
tung. Cái gì chặn? Và tương quan giữa các chiến lược phải đo trên dữ liệu nào — đã có bài
học là tương quan trên bar chỉ số tiền mặt (0,17) khác hẳn trên bar CFD 24h (0,58), và
phải dùng dữ liệu của **chính công cụ sẽ giao dịch**.

### 2.3. Chọn sàn là biến quyết định, không phải hằng số

Đo thật: cùng một phơi nhiễm kinh tế SP500, phí giữ dài chênh **5,5 điểm phần trăm/năm**
giữa các sàn. **Lớn hơn gần như mọi edge dự án từng test qua 324 phép thử.**

Nghĩa là: với nhiều chiến lược, chọn sàn quan trọng hơn chọn tín hiệu. Và đây là **phép
trừ**, không phải giả thuyết — không tốn slot FDR nào, ăn tiền chắc chắn.

Câu hỏi: đưa "chọn sàn/chọn lớp công cụ" vào dây chuyền như một chiều tối ưu ra sao mà
không biến nó thành dò tham số? Và làm sao xử lý việc cùng một tài sản cơ sở có nhiều
lớp (cash CFD, futures CFD, futures thật) với cấu trúc phí khác hẳn nhau?

### 2.4. Tính toàn vẹn của chính cuốn sổ

Cả kiến trúc đặt `experiment ledger` làm trung tâm. Vậy sổ hỏng thì sao?

- Ai (hoặc cái gì) có quyền sửa một dòng đã ghi?
- Nếu một tiến trình chết giữa chừng, dòng dở dang là PASS hay FAIL?
- Nếu chạy lại cùng `params_hash` ra kết quả khác (do dữ liệu đã cập nhật), ghi đè hay
  thêm dòng?
- Làm sao chứng minh sau 6 tháng rằng một `plan_hash` thật sự được ghi **trước** lần đọc
  dữ liệu đầu tiên, chứ không phải chèn ngược vào?

Tôi nghĩ sổ phải **chỉ-thêm** (append-only) và có chuỗi hash. Nhưng đó có phải là làm quá
cho một hệ một người dùng không? Chi phí thật của việc đó là gì?

### 2.5. Kinh tế học của việc giữ người trong vòng lặp

Bạn nói giữ người duyệt ở hai điểm: duyệt hypothesis trước khi chạy, và duyệt kết quả
trước khi live. Tôi đồng ý về nguyên tắc. Nhưng **người là tài nguyên khan hiếm nhất** —
đó chính là lý do sinh ra đề bài này.

Nếu dây chuyền sinh 40 hypothesis/ngày thì việc duyệt trở thành nút thắt mới, và người
duyệt sẽ bấm "đồng ý" hàng loạt — tức cổng mất tác dụng mà vẫn giữ hình thức.

Câu hỏi cụ thể: **người duyệt phải nhìn thấy đúng cái gì** để quyết định trong dưới 60
giây mà vẫn không bấm bừa? Và cái gì tự động **hạ số lượng cần duyệt** xuống mức người
chịu được — lọc trước theo tiên nghiệm? gộp các hypothesis tương đương thành một? hay
định mức cứng mỗi ngày?

### 2.6. Kết luận cũ có hạn dùng không

Một chiến lược PASS cách đây 18 tháng, hôm nay còn đúng không? Sổ khẳng định của chúng
tôi có 11 khẳng định, 7 cái "đã đóng sổ" — nhưng đóng sổ dựa trên dữ liệu tới hôm nay.

Câu hỏi: thiết kế lịch tái kiểm ra sao? Tái kiểm trên dữ liệu mới có phải là một phép thử
mới phải đếm vào FDR không, hay là thứ khác về bản chất? Và một khẳng định "đã đóng sổ"
thì bao giờ được mở lại — nếu không bao giờ thì hệ sẽ mù trước những thay đổi cấu trúc
thật.

### 2.7. Khi chạy thật thì nghiên cứu và thực tế lệch nhau ở đâu

Bạn đã thiết kế reconciliation và CUSUM — tốt. Nhưng còn những thứ backtest **không có
khái niệm**:

- lệnh bị từ chối, khớp một phần, requote,
- VPS mất kết nối giữa lúc đang có vị thế,
- sàn đổi spec hợp đồng hoặc đổi mức swap giữa chừng,
- gap cuối tuần nhảy qua cả SL,
- EA gọi WebRequest ra ngoài và nhà phát hành nhìn thấy tài khoản đang chạy (chuyện thật
  với một bot chúng tôi mổ xẻ).

Câu hỏi: những cái đó vào kiến trúc ở đâu? Mô hình hoá trong simulator, hay để nguyên
ngoài rồi bắt bằng reconciliation? Cái nào đáng mô phỏng, cái nào chỉ đáng giám sát?

---

## Cuối cùng

Nếu trong bảy ngóc ngách trên bạn thấy tôi **bỏ sót** một khía cạnh còn quan trọng hơn thì
nêu ra và đào nó thay vì trả lời cho đủ bảy mục. Tôi cần chỗ khuất, không cần bản đầy đủ.
