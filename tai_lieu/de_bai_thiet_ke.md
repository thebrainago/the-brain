# ĐỀ BÀI THIẾT KẾ — công nghiệp hoá vòng nghiên cứu định lượng

Bạn và tôi (Claude) làm cùng một dự án. Bạn đề xuất kiến trúc, tôi phản biện và hoàn
thiện. Đây **không phải** bài đo lường — đừng viết hàm `do()`. Hãy trả về một **bản
thiết kế**.

## Vấn đề cốt lõi

Chủ dự án nói: *"mỗi logic hay chiến lược cần phân tích kỹ, như cái EURCAD của chúng
ta đơn giản cũng mất 2 ngày, làm sao phân tích hết từng đây thứ được, mà như thế chắc
chắn sai sót"*.

Đó là bài toán thật: **phân tích thủ công không mở rộng được**. Một chiến lược lưới DCA
trên EURCAD tốn 2 ngày người mới ra kết luận đáng tin. Chúng tôi có hàng chục ý tưởng
và 28+ thị trường. Cần một dây chuyền chạy được cái quy trình 2-ngày-người đó **một cách
tự động và không mất chất lượng**.

Hệ chạy 24/7 trên VPS cấu hình yếu (mục tiêu: 2 vCPU, 1-2 GB RAM).

## Bốn khâu cần thiết kế

1. **Lấy dữ liệu** — càng nhiều, càng sâu, càng rộng càng tốt.
2. **Chuyển hoá & phân tích** — từ dữ liệu thô + tài liệu ngoài thành giả thuyết đo được.
3. **Mô phỏng** — chạy chiến lược một cách trung thực.
4. **Backtest chuẩn hoá + đối chiếu tài khoản thật.**

## Hiện trạng (đừng thiết kế lại cái đã có)

| Khâu | Đã có | Trạng thái |
|---|---|---|
| Lấy nguồn | `brain_sources.py` (arXiv, GitHub), `brain_nguon_moi.py` (HuggingFace, YouTube, Darwinex, Myfxbook, SEC 13F, IMAP, API Việt Nam) | chạy được; 118 mục |
| Vòng 24/7 | `brain_vong_lap.py` — hàng đợi bền vững, tự hồi phục, nhịp tim, ngân sách giờ | chạy được |
| Sổ khẳng định | `brain_khang_dinh.py` — 11 khẳng định nguyên tử + cổng repaint tổng quát | chạy được |
| Tầng sàng | `brain_co_che.py` — 28 thị trường OHLCV ngày, hoán vị giữ phơi nhiễm, gộp theo 7 nhóm tương quan | chạy được |
| Chi phí thật | `brain_chi_phi.py` — đọc swap/spread thật từng sàn qua MT5 | chạy được |
| Thợ | `ds_tho.py` — chính là kênh bạn đang nói chuyện qua | chạy được |

**Chưa có gì cho khâu 3 và 4.** Đó là lỗ hổng lớn nhất.

## Ràng buộc đã trả giá để biết — vi phạm là hỏng cả kết luận

Đây là những cái bẫy đã sập thật trong dự án này. Thiết kế của bạn phải xử lý được chúng,
nếu không thì dây chuyền sẽ sản xuất ra kết luận sai **hàng loạt** thay vì từng cái một —
đó là rủi ro lớn nhất của việc tự động hoá.

1. **Vào lệnh phải là `open[i+1]`**, không bao giờ `close[i]`.
2. **Phí qua đêm là chi phí quyết định, không phải spread.** Spread CFD chỉ số thật là
   0,6–0,8 bps (từng giả định 9 bps — thận trọng gấp 12 lần và giết oan nhiều chiến lược).
   Phí giữ dài 1,3–6,8%/năm tuỳ sàn. Chênh giữa các sàn 5,5 điểm %/năm — lớn hơn gần như
   mọi edge đã test.
3. **Mọi bảng phải có dòng mua-giữ, CẢ HAI bản: có phí và không phí.** Chỉ số không mua
   được, CFD thì có phí — hai kết luận khác hẳn nhau.
4. **`Model=1` của MT5 Strategy Tester chế ra lãi giả** khi TP/SL nhỏ hơn ~2× biên độ nến
   M1: đo được +1.161% ở Model=1 so với −100,7% ở tick thật. Lệch 12 lần.
5. **Tester áp mức swap của HÔM NAY cho cả lịch sử.**
6. **`open = close[t-1]` ở 95-98% ngày trước 2006** trên nhiều chuỗi — quy tắc `open[i+1]`
   thành vô hiệu mà không báo lỗi.
7. **Exness chỉ có bar từ 2022-08** cho 24/25 symbol; tester không báo gì, dấu hiệu duy
   nhất là số lệnh.
8. **Placebo phải hoán vị CHUỖI VỊ THẾ, không phải chuỗi lãi/lỗ** (hoán vị lãi/lỗ luôn ra
   ~50%).
9. **Hoán vị thứ tự lệnh là vô nghĩa với lãi kép tỷ lệ cố định** (tích giao hoán). Muốn đo
   bất định phải lấy mẫu CÓ HOÀN LẠI THEO KHỐI.
10. **PF dưới 0,3 thường là ảo giác của lãi kép trên edge âm** — chạy lại bằng lot cố định
    trước khi kết luận.
11. **Biến động cụm lại giả dạng cấu trúc.** Hôm nay sập ba lần trong một buổi sáng: nó
    lật ngược một kết luận và giết một kết quả z=+1,89 xuống −0,39.
12. **Chi phí cố định quyết định ở quy mô nhỏ**: VPS có thể lớn hơn toàn bộ lãi gộp.
13. **Tinh chỉnh tham số là hợp lệ, miễn là ĐẾM.** Dò 20 tổ hợp thì ghi 20 dòng vào sổ,
    kể cả dòng vứt đi. Hệ hiện có bộ đếm nhưng chưa gắn vào khâu mô phỏng.
14. **Quy tắc của chủ dự án: viết EA chạy MT5 Strategy Tester TRƯỚC, Python SAU.** Tester
    8 phút lật đổ 700 cấu hình Python. Đọc PF/Sharpe trước %/năm.

## Câu hỏi cho bạn

Trả lời **bằng thiết kế cụ thể**, không nói chung chung. Với mỗi khâu: cấu trúc dữ liệu
gì, chạy ra sao trên 2 vCPU, và **cái gì tự động chặn được sai sót** thay vì trông chờ
người soi.

**A. Lấy dữ liệu.** Rộng và sâu hơn hiện tại nghĩa là gì? Nguồn nào đáng thêm và vì sao?
Lưu trữ thế nào để 2 GB RAM vẫn quét được nhiều thị trường × nhiều khung × nhiều năm?

**B. Chuyển hoá.** Từ 118 tài liệu ngoài + dữ liệu giá → giả thuyết đo được. Hôm nay tôi
đưa 25 mục arXiv cho bạn, bạn bỏ qua 25/25 với lý do đúng. Vấn đề là **truy vấn sai** hay
**bề mặt đo của chúng tôi quá hẹp** (chỉ OHLCV ngày, 28 thị trường)? Nếu là cái sau thì
mở rộng bề mặt theo hướng nào cho đáng tiền nhất?

**C. Mô phỏng.** Thiết kế một bộ mô phỏng khai báo được: cùng một khai báo chiến lược
chạy được cả ở Python lẫn sinh ra EA cho MT5 Strategy Tester, để hai bên đối chiếu được.
Xử lý 14 ràng buộc trên ở đâu trong kiến trúc?

**D. Chuẩn hoá số liệu + đối chiếu thật.** Một chiến lược "qua" nghĩa là gì, phát biểu
thành bộ tiêu chí máy kiểm được? Và làm sao đối chiếu tự động kết quả backtest với sao kê
tài khoản thật để bắt lệch sớm?

**E. Cái gì trong thiết kế này bạn thấy RỦI RO NHẤT** — chỗ nào tự động hoá sẽ sản xuất
sai sót hàng loạt? Nói thẳng, đừng nể.

Nếu bạn thấy đề bài này đặt sai ở đâu, cứ nói. Tôi cần phản biện chứ không cần đồng ý.
