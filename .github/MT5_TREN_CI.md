# Chạy MT5 Strategy Tester trên GitHub Actions

## Nó giải quyết cái gì

`CLAUDE.md` ghi ràng buộc cứng nhất của dự án:

> *"Làn TESTER = 1 là ràng buộc VẬT LÝ, không phải lựa chọn. `chay_tester_kho`
> ghi đè cùng một `.mq5` / `.ini` / `.xml` và máy chỉ có một `terminal64.exe`.
> Hai việc tester cùng lúc thì ghi đè kết quả của nhau **và không ai báo lỗi**."*

Đó là ràng buộc vật lý của **một máy**, không phải của bài toán. Mỗi runner
Windows của Actions là một máy riêng với một terminal riêng — `matrix` biến
"1 slot" thành "N slot" mà không phải mua thêm máy nào.

## Cài đặt (làm một lần)

Vào **Settings → Secrets and variables → Actions**, thêm:

| secret | là gì |
|---|---|
| `MT5_LOGIN` | số tài khoản (nên dùng **demo**) |
| `MT5_PASSWORD` | mật khẩu tài khoản |
| `MT5_SERVER` | tên server, vd `XMGlobal-MT5 2` |
| `MT5_SETUP_URL` | *(tuỳ chọn)* link `mt5setup.exe` của sàn. Bỏ trống thì lấy bản MetaQuotes chung. |

Rồi: tab **Actions → MT5 tester → Run workflow**, điền mã / khung / khoảng ngày.

## Ba thứ phải đọc trước khi tin một con số từ đây

**1. Dữ liệu phải từ CHÍNH sàn sẽ giao dịch.** Runner tải lịch sử qua tài khoản
trong secrets. Đổi sàn là đổi spread, đổi swap, đổi cả giờ nến. `CLAUDE.md` đã
ghi bẫy *"tra cứu phí theo tên symbol thô → lặng lẽ lấy phí MetaQuotes-Demo"*.
Dùng bản MetaQuotes chung để "chạy thử cho nhanh" là tự tạo lại đúng cái bẫy đó.

**2. `Model=2` ở đây chỉ để SÀNG LỌC.** `CLAUDE.md`: *"Model=1 của MT5 nói dối
khi TP < 2× biên độ nến M1. Phải chạy Model=0/4."* Kết luận cuối vẫn phải chạy
lại ở Model=0 hoặc 4.

**3. Rỗng không phải âm.** Mã thoát của `terminal64.exe` **không đáng tin** — nó
trả 0 cả khi tester không chạy bar nào. Bước `kiem_ket_qua` đọc chính báo cáo và
trả ba trạng thái:

```
DAT            có báo cáo, có deal
AM             có deal, số không đạt ngưỡng
CHUA_DO_DUOC   không có báo cáo, hoặc báo cáo 0 deal
```

0 deal đọc **y hệt** "cơ chế không bao giờ kích hoạt", nhưng lịch sử không tải
được / sai tên symbol / khung thiếu dữ liệu đều cho đúng con số đó. Cổng trả mã
thoát khác 0 để job đỏ — **một job xanh với bảng số rỗng là thứ nguy hiểm nhất
trong cả đường này**.

## Giới hạn cần biết

- **Runner Windows tốn 2× phút** so với Linux trong quota Actions. Repo private
  thì đây là chi phí thật — chạy `matrix` rộng sẽ ăn quota nhanh.
- **Mỗi job tải lại lịch sử từ đầu** (runner là máy dùng một lần). Với chuỗi dài
  đây là phần chậm nhất. `max-parallel: 4` là trần tự đặt vì lý do đó.
- **EA phải được biên dịch sẵn** (`.ex5`). Mặc định workflow chạy EA mẫu có sẵn
  của MT5 để kiểm đường ống; đổi `--ea` sang EA của dự án sau khi đã commit bản
  `.ex5` hoặc thêm bước biên dịch bằng MetaEditor.
- **Đừng dùng tài khoản thật.** Secrets của Actions an toàn với người ngoài,
  nhưng bất kỳ ai push được vào repo đều chạy được workflow.

## Cách khác, và khi nào nên chọn

| cách | được | mất |
|---|---|---|
| **Actions Windows runner** | song song thật, không phải trông máy | tốn quota, tải lại lịch sử mỗi lần |
| **Self-hosted runner** trên máy anh | lịch sử có sẵn, không tốn quota | vẫn một máy = một slot |
| **VPS Windows** (`setup_vps.ps1` đã có) | chạy 24/7, nhiều terminal nếu đủ RAM | tốn tiền thuê, phải trông |

Nếu mục tiêu là **thông lượng** thì Actions thắng. Nếu là **chạy liên tục** thì
VPS thắng. Hai cái không loại trừ nhau.
