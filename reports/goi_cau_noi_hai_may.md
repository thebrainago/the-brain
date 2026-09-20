# GÓI: CẦU NỐI HAI MÁY (20/09/2026 đêm)

Chủ dự án: *"vấn đề là làm sao để phiên chat này đọc được kết quả chạy trên máy
tính tôi"*. Máy chủ dự án **TẮT** trong lúc làm gói này — nên mọi thứ ở đây phải
xác minh được mà không cần nó.

## ĐÃ LÀM

| Mảnh | File | Trạng thái |
|---|---|---|
| Đồng bộ git hai chiều | `qwen/cau_git.py` | **đã kiểm bằng repo thật** |
| Hợp đồng kết quả (3 trạng thái) | `cau_git.ghi_ket_qua` / `doc_ket_qua` | đã kiểm |
| Kênh leo thang `can_cloud` | `cau_git.cho_cloud` | đã kiểm |
| Chạy đơn + khoá lằn TESTER | `cau_git.chay_don` | đã kiểm |
| Móc vào vòng `q` | `qwen/chay.py` | **kiểm bằng AST, chưa chạy thật** |
| CLI hai bên | `b cau` · `q cau` | `b cau` đã chạy; `q cau` chưa |

## BẰNG CHỨNG: 35 bài, dùng REPO GIT THẬT

Một bài kiểm bằng mock chỉ chứng minh các hàm gọi nhau đúng thứ tự — nó không
nói gì về việc `git` có thật sự cho đơn đi qua không, mà đó mới là câu hỏi. Nên
mỗi bài dùng **một repo bare + hai bản clone thật**, chạy `git` thật.

Vòng đầy đủ đã chạy được: `CLOUD ghi đơn → push → MÁY pull → thấy đơn → ghi kết
quả → push → CLOUD pull → đọc được`.

Kèm **bài hiệu chuẩn ngược**: nếu máy ghi kết quả mà KHÔNG đồng bộ thì cloud
phải vẫn thấy `CHUA_DO_DUOC`. Không có bài này thì bài trên có thể xanh chỉ vì
hai bên dùng chung hệ thống file.

## LỖI THẬT BẮT ĐƯỢC TRONG CHÍNH GÓI NÀY

`_git` cũ luôn `.strip()` cả stdout. `git status --porcelain` in mỗi dòng dạng
`XY<cách>ĐƯỜNG`, nên một file **bị sửa** ra ` M README.md` có dấu cách dẫn đầu —
và `.strip()` trên CẢ chuỗi chỉ ăn dấu cách của **dòng đầu**. Kết quả: dòng đầu
bị cắt lệch một ký tự (`README.md` → `EADME.md`), các dòng sau thì đúng.

Không ném lỗi, không sai rõ ràng — chỉ đọc ra một đường dẫn LỆCH, rồi `dong_bo`
quyết định sai xem có được kéo không. Đã chuyển sang `--porcelain -z` (NUL, không
trích dẫn) và xử lý bản ghi kép của `R` (đổi tên).

**A/B**: 3 bài đỏ trên bản cũ, 35/35 xanh trên bản mới.

## BA LUẬT AN TOÀN — đây là module TỰ CHẠY `git` TRÊN MÁY NGƯỜI KHÁC

1. **Không bao giờ `git add -A`.** Chỉ thêm đúng `DUOC_DAY` = `viec/xong`,
   `viec/hoi`, `viec/dang`, `reports`. `config/` **không** có trong danh sách —
   quy tắc phiên cấm phiên [DOC] sửa `config/*.json`, và máy chạy `q` đúng là
   một phiên như vậy đối với mã nguồn.
   *Đã kiểm*: file lạ + `config/qwen.json` bẩn → không cái nào lên remote.
2. **Không bao giờ vứt việc local.** Không `stash`, không `reset --hard`, không
   `push --force`. `merge --ff-only` **thất bại có chủ đích** khi hai nhánh rẽ:
   một merge tự động lúc 3 giờ sáng, không ai nhìn, trên cây có việc dở dang là
   cách nhanh nhất để mất việc mà không ai biết.
   *Đã kiểm*: nhánh rẽ → `CHUA_DO_DUOC`, `HEAD` local không đổi.
3. **Đồng bộ hỏng không bao giờ là `AM`.** Mất mạng, xung đột, remote từ chối →
   `CHUA_DO_DUOC`, và **không ném ra vòng `q`** — một lỗi mạng không được phép
   giết một đợt chạy nhiều ngày.

## CHẤM ĐIỂM: MÃ THOÁT != 0 KHÔNG MẶC NHIÊN LÀ `AM`

`qwen/DOC_TRUOC.md` chốt điều này. Nhưng **`pytest` là ngoại lệ có thật**:

| mã thoát | ý nghĩa | chấm |
|---|---|---|
| 0 | mọi bài xanh | `DAT` |
| 1 | bài chạy được, có bài đỏ | **`AM`** — kết quả ĐO ĐƯỢC |
| ≥2 | lỗi thu gom / dừng giữa chừng | `CHUA_DO_DUOC` |

Gộp 1 với ≥2 thì **một lỗi cú pháp trong file test đọc ra thành "cơ chế không ra
tiền"**. Đơn không khai `cong.kieu` → `CHUA_DO_DUOC`, kể cả khi mã thoát 0: mặc
định phải là "chưa nói được gì", không phải "đạt".

## KHOÁ LẰN TESTER

`_lay_khoa` dùng `open(k, "x")` — kiểm-và-đặt **nguyên tử** ở mức hệ điều hành.
`if not exists: create` thì hai tiến trình vào cùng lúc đều thấy "chưa có" và
đều tạo. Khoá cũ hơn 6 giờ coi như tiến trình giữ nó đã chết, nếu không thì một
lần tắt máy làm kẹt lằn TESTER **vĩnh viễn** mà bảng việc vẫn trông bình thường.

`chay_mot_don_dang_cho` **nhảy qua** đơn TESTER khi lằn bận thay vì dừng cả hàng
đợi — nếu không một đơn tester dài sẽ chặn hết các đơn NHẸ phía sau.

## RỦI RO CÒN LẠI / VIỆC CHƯA LÀM

- **Móc vào `qwen/chay.py` chưa chạy thật.** `chay.py` kéo `langchain_core`,
  chỉ có trên máy chủ dự án; trên cloud nó ném `ModuleNotFoundError`. Tôi kiểm
  bằng **AST** (vòng lặp có gọi `dong_bo_git` + `chay_don_cloud` không · đồng bộ
  có chạy TRƯỚC `nap_lai_bang` không · đơn có vào luồng nền không). AST trả lời
  đúng câu cần hỏi trên MỌI máy, nhưng **không** thay được một lần chạy thật.
- **Việc đầu tiên khi máy bật**: `q cau` rồi `q mot-vong`, xác nhận một đơn
  no-op đi hết vòng. Chưa đi hết vòng thì cầu chưa tồn tại.
- Chưa có cơ chế cloud **trả lời** một câu `can_cloud` (mới có chiều máy→cloud).
- `viec/dang/` đã tạo nhưng chưa dùng — `chay_don` hiện dựa vào `viec/xong/` để
  chống chạy trùng.
