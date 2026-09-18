# VÒNG 6 — một lỗi thật vừa xảy ra, và nó lộ ra lỗ hổng trong bộ cổng ta đã chốt

Hôm nay tôi kiểm một chiến lược thật lấy từ `freqtrade-strategies` (GPL-3.0):
**Volatility System** của Wilder — `ATR2 = ATR(14)×2`; long khi `close − close[-1] > ATR2[-1]`;
short khi ngược lại; đảo chiều liên tục, luôn ở trong thị trường, không cắt lỗ.

Chạy trên 28 thị trường tập sàng với đầy đủ kỷ luật của ta. Kết quả đầu tiên:

> **24/28 thị trường vượt mua-giữ, 7/7 nhóm, p = 0,0156**

Sau 324 phép thử với **0 cái** vượt mua-giữ, con số này xuất hiện. Tôi không tin và đi tìm
lỗi. Tìm ra, và **lỗi là của tôi**:

Tôi cho hệ trả phí qua đêm **chỉ khi đang mua**, còn mua-giữ trả phí **mọi ngày**. Hệ nằm
ở chiều bán khoảng nửa thời gian, nên nó thắng một phần chỉ vì **trả ít phí hơn**.

Tách ra bằng bốn biến thể:

| biến thể | thị trường | nhóm | trung vị hiệu Sharpe | p |
|---|---|---|---|---|
| A. như ban đầu (phí bất đối xứng) | 24/28 | 7/7 | +0,323 | **0,0156** |
| B. hệ trả phí **cả hai chiều** | 23/28 | 6/7 | +0,120 | 0,125 |
| C. bỏ phí qua đêm cả hai bên (tín hiệu thuần) | 23/28 | 6/7 | +0,119 | 0,125 |
| D. hệ trả phí hai chiều vs **mua chỉ số KHÔNG phí** | 11/28 | 4/7 | **−0,077** | 1,000 |

**63% của "edge" là lỗi mô hình chi phí.** B ≈ C xác nhận phần còn lại đúng là tín hiệu.
Nhưng dòng D giết nó: so với việc mua chỉ số/ETF thật (~0,1%/năm chứ không phải 4%/năm
của CFD), chiến lược **thua**.

---

## Lỗ hổng trong bộ cổng ta đã chốt

Ở vòng 2 bạn viết `net_return > buyhold_net_return` với `buyhold_net` = **mua-giữ CFD sau
phí**. Tôi đã tán thành. Nhưng vụ hôm nay cho thấy định nghĩa đó **thiên vị một cách hệ
thống** cho mọi chiến lược có chiều bán:

- Mua-giữ CFD phải trả phí giữ **100% thời gian**.
- Một chiến lược ở chiều bán 50% thời gian chỉ trả **~50%** phí đó.
- Chênh lệch ấy khoảng **2%/năm** với chỉ số — **lớn hơn hầu hết edge ta từng đo**.

Tức bất kỳ chiến lược nào biết đứng ngoài hoặc bán khống đều được **tặng miễn phí ~2%/năm
alpha giả** khi so với mua-giữ CFD. Bộ cổng của ta sẽ cấp PASS cho những thứ đó.

Hai sửa tôi đề xuất:

**(1) Mốc phải là CÁCH RẺ NHẤT có được cùng phơi nhiễm, không phải cùng công cụ.**
Với chỉ số cổ phiếu, đó là ETF ~0,1%/năm, không phải CFD 4%/năm. Với FX giao ngay thì
không có cách rẻ hơn nên CFD là đúng. Với vàng có thể là ETF vàng. Nghĩa là bảng mốc phải
khai báo **theo từng lớp tài sản**, không dùng một con số chung.

**(2) Ghi rõ mô hình chi phí áp cho CẢ HAI VẾ và bắt chúng đối xứng.** Đây phải là một
cổng máy kiểm được, không phải sự cẩn thận của người viết code: nếu chiến lược và mốc
không dùng cùng một hàm chi phí trên cùng một chuỗi phơi nhiễm thì kết quả bị từ chối.

---

## Câu hỏi cho bạn

**A.** Sửa (1) có kéo theo hệ quả gì tôi chưa thấy? Cụ thể: nếu mốc là ETF nhưng ta giao
dịch bằng CFD, thì ta đang so một thứ **không giao dịch được bằng công cụ đang dùng** với
một thứ giao dịch được. Trước đây dự án đã chốt là phải báo **cả hai** mốc. Nhưng cái nào
làm **cổng cứng**? Tôi nghiêng về: mốc cứng là cái rẻ nhất **mà chủ dự án thật sự tiếp cận
được** — với người ở Việt Nam thì ETF Mỹ có thể không mua được dễ, nên CFD lại là đúng.
Vậy cổng phụ thuộc vào **người dùng ở đâu**. Điều đó có làm hỏng tính khách quan không,
hay đó chính là cách nó phải thế?

**B.** Còn dạng "alpha giả do bất đối xứng chi phí" nào khác cùng loại mà ta chưa chặn?
Tôi nghĩ ra hai cái nữa và muốn bạn thêm:
- Chiến lược **đứng ngoài thị trường** phần lớn thời gian: nó không trả phí giữ, và nếu
  ta không tính lãi tiền mặt cho mốc thì lại thiên vị tiếp — nhưng lần này thiên vị theo
  chiều **ngược lại**.
- Chiến lược giao dịch **ít lệnh**: nó trả ít spread, nên mọi so sánh với chiến lược nhiều
  lệnh đều méo nếu spread bị ước lượng sai.

**C.** Volatility System còn +0,12 Sharpe trên mua-giữ CFD (6/7 nhóm, p = 0,125) sau khi
sửa. Chưa đạt ngưỡng nhóm, nhưng cũng không phải số không. Theo bộ cổng ta đã thiết kế,
thứ này đi về đâu — `EXPLORATORY` rồi thôi, hay có đường nào để nó được kiểm tiếp mà không
phá kỷ luật? Nhớ là nó **không** được đăng ký trước.

**D.** Quan trọng nhất: **quy trình nào bắt được lỗi này TỰ ĐỘNG?** Hôm nay tôi bắt được
vì con số 24/28 quá đẹp so với lịch sử 324-phép-thử-0-thắng của dự án, nên tôi đi tìm lỗi.
Đó là trực giác của người, không phải cổng của máy. Nếu kết quả chỉ là 16/28 thì tôi đã
không nghi ngờ và lỗi sẽ lọt.

Bạn từng đề xuất **mutation audit** — cố tình chèn lỗi rồi xem dây chuyền có gào lên không.
Lỗi hôm nay có dạng gì để đưa vào bộ ca mutation? Tôi nghĩ là: *"chèn một bất đối xứng chi
phí giữa chiến lược và mốc, rồi kiểm xem có bị bắt không"*. Nhưng chèn thế nào cho tổng
quát, chứ không phải chỉ bắt đúng một lỗi tôi vừa mắc?
