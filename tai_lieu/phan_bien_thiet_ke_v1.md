# PHẢN BIỆN BẢN THIẾT KẾ v1

Bản của bạn tốt. Tôi giữ nguyên phần lớn kiến trúc và chỉ sửa chỗ sai. Ba thứ tôi lấy
nguyên vẹn vì chúng hơn hẳn cái tôi đang có:

- **Null strategy factory.** Đây là ý hay nhất trong cả bản. Nó là cổng ở tầng **dây
  chuyền**, không phải tầng chiến lược — nếu tỷ lệ chiến lược ngẫu nhiên "PASS" vượt mức
  kỳ vọng thì hỏng cả pipeline, và phải dừng promotion chứ không dừng từng cái. Tôi chưa
  có gì ở tầng đó.
- **Chẩn đoán rủi ro ở phần E.** Bạn chỉ đúng cơ chế: cái bào mòn thống kê không phải số
  attempt đã đếm, mà là **các quyết định nằm ngoài sổ** (chọn giả thuyết nào, chọn đoạn
  dữ liệu nào, chọn bộ lọc nào, chọn cost model nào).
- **Tắt swap trong MT5, cộng chi phí ở Python.** Xử lý đúng ràng buộc 5.
- **Template song ngữ thay vì sinh MQL5 tuỳ ý.** Đúng. Sinh code MQL5 tự động là một
  ổ bug, và conformance test giữa hai backend phải là hạ tầng bắt buộc.

Dưới đây là chỗ sai. Tôi xếp theo mức thiệt hại.

---

## 1. NGHIÊM TRỌNG NHẤT — bộ cổng PASS của bạn sẽ loại đúng thứ duy nhất từng chạy được

Bạn đặt `net_sharpe >= 1.0` và `max_drawdown <= 25%` làm ngưỡng cứng.

Hệ thống tốt nhất dự án từng xác nhận là **V6**, đo trên MT5 thật, danh mục 3 chỉ số Mỹ:

```
CAGR 8,64%  |  Sharpe 0,95  |  maxDD −11,5%  |  Calmar 0,75  |  ~1 lệnh/tuần
```

**Sharpe 0,95 < 1,00 → cổng của bạn loại nó.** Ngưỡng tuyệt đối là số bịa, không neo vào
gì cả. Sharpe 1,0 trên chỉ số cổ phiếu khung ngày là mức gần như không ai đạt sau phí.

Sửa: ngưỡng phải **neo vào mua-giữ của chính tài sản đó trong cùng kỳ**, không phải hằng
số. Cổng đúng là *"vượt mua-giữ sau phí trên nhiều chiều đo"*, không phải *"Sharpe > 1"*.

## 2. Bạn để sót cổng quan trọng nhất của dự án này

Danh sách PASS của bạn ghi:

```
buyhold_gross và buyhold_net có mặt
```

**Chỉ "có mặt"** — tức chỉ cần báo cáo là qua. Nhưng lịch sử dự án: **324 phép thử, 0 cái
vượt được mua-giữ**. Nếu cổng chỉ đòi in ra con số mà không đòi thắng nó, thì dây chuyền
sẽ cho PASS hàng loạt chiến lược thua mua-giữ mà vẫn có bảng đẹp.

Sửa: `net_return_vs_buyhold_net > 0` **và** `net_sharpe > buyhold_net_sharpe` là cổng
CỨNG. Và phải là mua-giữ CFD có phí (mua được thật), đối chiếu thêm với mua-giữ chỉ số
không phí (không mua được nhưng là trần lý thuyết) — hai kết luận khác hẳn nhau.

## 3. Quy tắc TP/SL cùng bar của bạn có thiên lệch hệ thống

Bạn viết: *"nếu SL và TP cùng nằm trong một bar M1, giả định SL chạm trước, trừ khi có
tick chứng minh ngược lại"*.

Nghe thận trọng, nhưng **thận trọng có hệ thống vẫn là số sai**. Nó bóp mọi chiến lược
xuống đều nhau, và sẽ giết những edge mỏng thật — đúng cái loại edge dự án này đang tìm.
Dự án đã chốt quy tắc khác: **dùng open của chính bar đó để đoán** — giá mở gần TP hơn
thì TP chạm trước. Không thiên lệch về bên nào.

Và nhớ bài học đã trả giá: giả định spread 9 bps thay vì 0,7 bps là "thận trọng gấp 12
lần", và nó **giết oan** một loạt chiến lược. Thận trọng sai chỗ đắt ngang cẩu thả.

## 4. `placebo_p <= 0.05` một giá trị là không đủ

Đã đo được: cùng một cơ chế cho placebo 95,8% với hạt ngẫu nhiên 11 và 94,8% với hạt 13.
**Verdict đổi theo hạt.** Một con số p đơn lẻ ở cổng ra là chỗ dễ tự lừa nhất.

Sửa: chạy tối thiểu 5 hạt, lấy **p xấu nhất**. Và ghi cả 5 vào sổ, không chỉ ghi cái đại
diện.

## 5. Bạn quay lại FDR toàn cục — dự án đã bỏ cách đó vì sai chuẩn

`attempt_count` để hiệu chỉnh là đúng hướng, nhưng nếu cộng dồn toàn cục vĩnh viễn thì ý
tưởng thứ 400 bị phạt vì 40 ý tưởng tồi hồi tháng 3. Chuẩn đã chốt: **FDR theo HỌ × theo
QUÝ**, ngân sách nạp lại mỗi quý, chia họ theo mức tiên nghiệm (có tiền nghiệm / cơ chế /
quản trị vốn / tự đào).

Và quan trọng: **tầng khám phá KHÔNG tốn slot nào**. Chỉ tầng xác nhận mới tính tiền.
Nếu bạn tính attempt của tầng 1 vào mẫu số của tầng 2 thì hệ sẽ không bao giờ nói "có",
và một hệ không bao giờ nói "có" thì không phân biệt được với hệ đã hỏng.

## 6. Cổng demo 20-30 lệnh không dùng được cho chiến lược tần suất thấp

V6 chạy ~1 lệnh/tuần. 20-30 lệnh = **5 đến 7 tháng** demo trước khi được vào live. Cổng
viết theo SỐ LỆNH sẽ chặn vĩnh viễn đúng loại chiến lược ít lệnh mà dự án này đang có.

Sửa: cổng theo **sức mạnh thống kê**, không theo số lệnh — cần bao nhiêu lệnh để phân
biệt được kỳ vọng quan sát với 0 ở mức tin cậy đặt trước, tính từ chính phương sai của
backtest. Chiến lược biên độ lớn cần ít lệnh, biên độ mỏng cần nhiều. Và nói thẳng con số
tháng cho người quyết định.

---

## Hai chỗ tôi hạ ưu tiên (không sai, nhưng chưa đến lúc)

- **DuckDB + partition parquet.** Toàn bộ tập sàng hiện tại là **9,1 MB**, tiến trình
  nặng nhất 120 MB. Dựng DuckDB bây giờ là giải bài toán chưa tồn tại. Lấy **bố cục thư
  mục** của bạn ngay (rẻ, và đổi sau thì đau), nhưng hoãn DuckDB tới khi M1 thật sự nằm
  trên đĩa (~2-3 GB).
- **Tick history.** Đắt và chậm. Chỉ cần cho chiến lược có TP/SL nhỏ hơn ~2× biên độ nến
  M1. Đó là một **điều kiện kích hoạt**, không phải hạng mục làm trước.

---

## Câu hỏi vòng 2

Trả lời gọn, chỉ những gì đổi so với v1:

**A.** Viết lại bộ cổng PASS với ngưỡng **neo vào mua-giữ** thay cho hằng số tuyệt đối.
Cụ thể: chiến lược phải hơn mua-giữ ở những chiều nào, hơn bao nhiêu thì đủ, và làm sao
tránh việc chỉ hơn nhờ phơi nhiễm cao hơn (đòn bẩy trá hình — cơ chế VIX từng có IC
+0,106 dương ở cả 5 giai đoạn con nhưng placebo 10,2% vì size trung bình 98-99%, tức nó
gần như chính là mua-giữ).

**B.** Null strategy factory: thiết kế cụ thể. Sinh chiến lược ngẫu nhiên **như thế nào**
để chúng có cùng cấu trúc với chiến lược thật (cùng tần suất vào lệnh, cùng phân bố thời
gian giữ, cùng phơi nhiễm) mà không có tín hiệu? Ngưỡng "tỷ lệ null PASS vượt mức kỳ
vọng" tính ra sao? Và khi vượt thì chẩn đoán chỗ hỏng bằng cách nào?

**C.** Pre-registration là cổng bạn cho là quan trọng nhất. Nhưng dây chuyền tự sinh giả
thuyết thì "đăng ký trước" thành hình thức — máy tự viết kế hoạch rồi tự chạy ngay sau
đó. Cái gì làm cho nó **không** thành hình thức?

**D.** Với ràng buộc 2 vCPU: xếp thứ tự thực hiện 7 module mới của bạn. Cái nào làm trước
để sớm chặn được sai sót hàng loạt nhất? Tôi nghĩ là `brain_validator.py` + null factory
đi trước cả simulator — vì không có cổng thì simulator chỉ sản xuất số nhanh hơn. Bạn
thấy sao, và nếu không đồng ý thì vì sao?
