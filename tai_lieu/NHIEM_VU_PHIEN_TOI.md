# NHIỆM VỤ PHIÊN TỚI — biến THE BRAIN thành bộ não chạy liên tục tới khi ra tiền

> Viết 20/09/2026 cho phiên sau. Chủ dự án mua gói token lớn với **mục đích rõ**:
> *"để bạn dùng hết công suất suy nghĩ + cho máy chạy thử để xem vấn đề và sửa"*.
> Máy chủ dự án bật liên tục **>10 tiếng/ngày**.

## ĐỌC TRƯỚC, KHÔNG ĐƯỢC BỎ

1. `CLAUDE.md` — LUẬT SỐ 0. **Mục tiêu là TIỀN**, không phải chặt chẽ học thuật.
   MDE/FDR/placebo là **nhãn cảnh báo**, không phải cổng chặn; chỉ chặn khi thua
   mua-giữ **ở cùng rủi ro**.
2. `SO_DO_HE_THONG.txt` — sơ đồ thật. Đừng xây lại thứ đã có.
3. `tai_lieu/VAN_HANH_HAI_MAY.md` — **cách vận hành hai máy. Đọc kỹ §3.**
4. `reports/BAO_CAO_CLOUD_20260919.md` — 5 đợt sửa phiên 19-20/09, có số đo.
5. `b kien-truc` trước khi lập kế hoạch · `b ban-do` trước khi xây module mới.

## NGUYÊN TẮC VẬN HÀNH CỦA PHIÊN NÀY

**Máy chủ dự án là nhà máy. Cloud là bộ não. Máy rảnh = lãng phí thật.**

- Trước khi dừng lượt, **hàng đợi `viec/cho/` phải không rỗng**.
- Tự hẹn đánh thức (`send_later`) khớp **thời gian chạy thật** của đơn đã đẩy —
  không hẹn theo con số đẹp.
- Token tiêu vào: **nghĩ, viết bài test, đọc kết quả, quyết định**.
  Không tiêu vào: gõ code mà thợ local gõ được.
- **Bài test là chỗ tiêu token, không phải chỗ tiết kiệm.** Mọi đơn phải có bài
  **dương tính giả** và bài **hiệu chuẩn ngược**. Bằng chứng vì sao: đơn số 2
  phiên 19/09 qua sạch mọi bài test mà vẫn đọc một bộ lọc spread thành
  `trailing_tu = 30`.

## VIỆC 1 — XÂY CẦU NỐI HAI MÁY (chặn mọi thứ khác, làm trước)

Chưa có cầu này thì cả thiết kế trên chỉ là giấy. Bốn mảnh, đã đặc tả ở
`VAN_HANH_HAI_MAY.md` §6:

1. `qwen/cau_git.py` — `git pull`/`push` vào vòng `q`; đọc `viec/cho/`, ghi
   `viec/xong/`.
2. **Hợp đồng kết quả** — JSON mỗi đơn: `trang_thai` (DAT/AM/CHUA_DO_DUOC) +
   bằng chứng + số đo. Cloud quyết định mà không đọc log.
3. **Kênh leo thang** — `can_cloud: true` + câu hỏi.
4. **Chống giẫm chân** — máy là [GHI] với `data/`, `nao.db`, MT5; cloud là
   [GHI] với mã nguồn. Không bên nào đụng vùng bên kia.

**Kiểm nghiệm thật**: đẩy một đơn rỗng (no-op), xác nhận nó đi hết vòng
cloud → git → máy → git → cloud. Chưa đi hết một vòng thì cầu chưa tồn tại.

## VIỆC 2 — CHẠY THẬT, TÌM VẤN ĐỀ, SỬA

Đây là mệnh lệnh chính: *"cho máy chạy thử để xem vấn đề và sửa"*.

Hai thứ phiên 19-20/09 xây xong nhưng **mới chỉ chạy trên chuỗi tổng hợp**:

- **968 cơ chế** của HEPHAESTUS (`b hepha nap 968 --that`)
- **84 cấu hình quản trị** (`b hepha qt 200 --ma AUDCAD --khung H4`)

Và **85 bài test còn đỏ trên cloud** vì thiếu `data/` + `nao.db`. Trên máy chủ
dự án phải chạy lại để biết bài nào **đỏ thật**. Danh sách:
`reports/do_nhanh.txt`.

Đọc kết quả theo đúng ba trạng thái. **CHƯA_ĐO_ĐƯỢC ≠ ÂM** — đây là nhóm lỗi
chiếm trọn đợt 3 phiên trước.

## VIỆC 3 — TRỤ BANKER (chủ dự án duyệt quay lại 20/09/2026)

`SO_DO_HE_THONG.txt` dòng 17 đã ghi sẵn: *"BANKER KHÔNG BỎ. Chỉ là phải xây
xong BA MODULE THẬT trước đã, rồi mới quay lại."* Chủ dự án đang nói **quay
lại**. Không phải xây từ trắng: `tru/banker.py` đã có **550 dòng** + 2 bộ test.

### Đặc tả nguyên văn của chủ dự án

> *"banker - là hệ thống phân tích vĩ mô: nó sẽ đi thu thập các báo cáo dữ liệu
> của bofa, cot, bloomberg,… các nguồn claude khuyến nghị + phương pháp luận với
> kiến thức vĩ mô chuẩn như chuyên gia + cfa + phân tích + địa chính trị => kết
> quả là nhìn được dòng tiền và ảnh hưởng của dòng tiền trong trung dài và ngắn
> hạn."*

### Chướng ngại phải nói thẳng trước khi hứa

**BofA và Bloomberg là trả phí / độc quyền.** BofA Global Fund Manager Survey và
dữ liệu Bloomberg Terminal không có API miễn phí; cào chúng vừa vi phạm điều
khoản vừa không bền. **Đừng thiết kế hệ phụ thuộc vào chúng.**

Nhưng câu hỏi thật — *"dòng tiền đang đi đâu"* — có nguồn **miễn phí, chính
thống, point-in-time** phủ được phần lớn:

| Câu hỏi | Nguồn miễn phí |
|---|---|
| Vị thế đầu cơ | **CFTC COT** ✓ đã có trong `banker.py` |
| Lãi suất, đường cong, tín dụng | **FRED / ALFRED** ✓ đã có |
| Vốn xuyên biên giới vào/ra Mỹ | **TIC (US Treasury)** |
| Dòng vốn ngân hàng, credit-gap, REER | **BIS** |
| Cán cân thanh toán | **IMF IFS / WEO** |
| Bảng cân đối NHTW | **ECB SDW · BOJ · Fed H.4.1** |
| Thanh khoản USD ròng | **TGA + RRP** (FRED) |
| Proxy dòng quỹ | **shares outstanding của ETF** (nhà phát hành công bố) |
| Căng thẳng tài chính | **NFCI (Chicago Fed) · OFR FSI** |
| **Địa chính trị ĐỊNH LƯỢNG** | **GPR Index** (Caldara–Iacoviello), miễn phí, hàng tháng |

GPR Index là cách biến "địa chính trị" từ bình luận thành **một chuỗi số có
lịch sử** — tức thành thứ backtest được.

### KIẾN TRÚC ĐỀ XUẤT — và cái bẫy chết người phải chặn

Giữ ba tầng `banker.py` đã có (SỐ LIỆU / CHẾ ĐỘ / HÀM Ý), nhưng phải chốt lại
tầng 3.

**BẪY**: phân tích vĩ mô là **narrative không thể bác bỏ**. Bất kỳ diễn biến nào
cũng giải thích được *sau khi* nó xảy ra. Một BANKER chỉ sinh văn bản sẽ **luôn
trông đúng** và **không bao giờ ra tiền**. Đây là dạng nguy hiểm nhất với LUẬT
SỐ 0, vì nó không hề trông giống một lỗi.

**Ba chốt chặn bắt buộc:**

1. **Mọi luật vĩ mô phải phát biểu được thành ĐIỀU KIỆN point-in-time.**
   Không phát biểu được thì không vào hệ — để trong ghi chú.

2. **Giá trị của luật phải ĐO ĐƯỢC bằng một phép so.** Lấy một hệ ĐÃ PASS, chạy
   holdout **hai lần** — có điều kiện chế độ và không có. Không cải thiện thì
   luật đó là **văn hay, không phải edge**. Phép so này rẻ, chạy trên máy chủ
   dự án.

3. **POINT-IN-TIME LÀ SỐNG CÒN.** Dữ liệu vĩ mô **bị sửa lại**: GDP quý công bố
   lần đầu khác hẳn bản cuối. Backtest bằng bản cuối = **nhìn trước**, và nó im
   lặng. **ALFRED** (FRED vintage) là nguồn duy nhất giải quyết được.
   → **Việc kiểm đầu tiên**: `banker.py` đang lưu **ngày công bố** hay **ngày
   dữ liệu**? Nếu là ngày dữ liệu thì mọi kết luận lịch sử của trụ này hỏng.

4. **FDR.** Mỗi điều kiện chế độ thử trên holdout là **một suất**. Đăng ký
   trước như mọi thứ khác — không có ngoại lệ cho vĩ mô.

### CHỨC NĂNG TÔI ĐỀ XUẤT THÊM (chủ dự án mời đề xuất)

**BANKER nên trả lời "TÀI SẢN NÀO ĐÁNG QUÉT", không chỉ "lúc nào đáng vào".**

Hiện SEEKER/QUANTLAB quét gần như mù — chọn ứng viên theo chi phí và Hurst.
Nếu BANKER nói được *"quý này dòng tiền đang rời EM về USD"* thì nó **thu hẹp
không gian tìm kiếm**, mà thu hẹp không gian tìm kiếm là **tiết kiệm suất FDR
trực tiếp** — một đóng góp **đo đếm được**, không phải narrative.

Điều này khớp đúng dòng đã có sẵn trong `banker.py`:
> *"BANKER không được tạo tín hiệu giao dịch. Nó cung cấp LỚP BỐI CẢNH."*

Nên chốt vai: **BANKER = BỘ LỌC KHÔNG GIAN TÌM KIẾM + LỚP ĐIỀU KIỆN CHẾ ĐỘ.
Không phải bộ sinh tín hiệu.**

Phép đo thành công của cả trụ, phát biểu một câu:
> Với cùng ngân sách FDR, hệ CÓ BANKER tìm được nhiều cấu hình `CHAY_DUOC` hơn
> hệ KHÔNG BANKER — đo trên holdout, point-in-time.

Không vượt được phép so đó thì BANKER là chi phí, dù báo cáo có hay đến đâu.

## VIỆC 4 — GHI SỔ

- Cuối mỗi gói: `reports/goi_<ten>.md` — đã làm gì · bằng chứng · số trước/sau ·
  rủi ro còn lại · **việc chưa làm**.
- Chủ dự án cần cập nhật `Desktop/hethong.txt` (bản gốc của sơ đồ) về việc
  BANKER quay lại phạm vi. Cloud chỉ sửa được bản chép `SO_DO_HE_THONG.txt`.

## ĐIỀU KHÔNG ĐƯỢC LÀM

- **Không dừng ở mức mô tả.** Chủ dự án: *"tôi muốn claude phải làm được hệ
  thống đó và có thể nâng cấp phát triển hơn cả mô tả của tôi"*.
- **Không báo CHẠY_ĐƯỢC cho thứ chưa qua cổng thật.** Gọi đúng tên: *canh bạc
  có kỳ vọng dương đo được*.
- **Không để một phép CHƯA_ĐO_ĐƯỢC đi ra im lặng.** Cả đợt 3 phiên trước là
  nhóm lỗi này.
- **Không sửa bài test cho xanh.** Bài test là đặc tả.

---

# ĐÃ LÀM TRONG ĐÊM 20→21/09 (cập nhật cuối đêm)

Máy chủ dự án **TẮT** cả đêm, nên mọi thứ dưới đây là phần không cần máy.

| Việc | Trạng thái |
|---|---|
| **VIỆC 1 — cầu nối hai máy** | **XONG phần code**, 43 bài trên repo git thật. Chưa chạy vòng thật vì máy tắt. |
| Hàng đợi cho máy | **7 đơn** trong `viec/cho/` |
| **VIỆC 3 — BANKER point-in-time** | **XONG**: lời khai point-in-time là SAI, đã thêm chiều `ngay_biet` |
| BANKER — phép so edge/chi phí | **XONG**: `so_co_che_do` + `chuoi_che_do` |
| NỘI SINH lệch chiều + luận điểm nói ngược | **XONG**: 3.669 long/0 short → cân; và `sinh()` nhanh 300× |
| Cổng chặn cứng **hỏng thì mở** (2 cổng) | **XONG** |

## VIỆC ĐẦU TIÊN KHI MÁY BẬT

```
q cau            xem cầu nối + 7 đơn đang chờ
q mot-vong       chạy một vòng, xác nhận đơn `cau-kiem` đi hết vòng
```

**Chưa đi hết một vòng thì cầu chưa tồn tại.** Mọi thứ khác chờ sau đó.

## CÒN NGUYÊN, CHƯA ĐỘNG TỚI

- **VIỆC 2** (chạy thật 968 cơ chế + 84 cấu hình quản trị) — cần máy.
- Độ trễ công bố của BANKER mới là **ƯỚC TÍNH**; nguồn ngày thật là **ALFRED**,
  và cloud **không nối được** (proxy trả 403 CONNECT cho fred/alfred/cftc).
- `_luu_seri` chưa ghi vào `vi_mo_ban` — bảng có, đường ghi chưa nối.
- Chưa có phép so "cùng ngân sách FDR, có BANKER vs không BANKER".
