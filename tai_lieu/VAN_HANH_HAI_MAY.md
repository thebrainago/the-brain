# VẬN HÀNH HAI MÁY — máy anh tính, cloud nghĩ

> Chốt 20/09/2026. Chủ dự án: *"máy tính tôi cho toàn bộ phần tính toán và cloud
> của claude code phụ trách giám sát và suy nghĩ + gọi llm"*. Máy bật liên tục
> **hơn 10 tiếng/ngày**.

## 1. Câu hỏi cơ chế: phiên cloud đọc kết quả máy anh bằng cách nào?

**Phiên cloud KHÔNG có đường mạng nào tới máy anh.** Nó chỉ thấy GitHub. Nên
đường truyền duy nhất là:

```
CLOUD (Claude Code)            GITHUB                 MÁY ANH (q)
  nghĩ, lập kế hoạch    →  viec/cho/*.json   →   git pull (mỗi vòng)
  viết BÀI TEST                                  thợ local viết code
                                                 pytest chấm, lặp đến xanh
                                                 MT5 tester chạy thật
  đọc, quyết định       ←  viec/xong/*.json  ←   git push kết quả
```

**Anh KHÔNG cần mở Claude Code trên máy.** `q` làm được hết phần máy:
`git pull` → nhận đơn → chạy → `git push` kết quả. Mở thêm Claude Code trên máy
chỉ tốn token từ cùng một túi và làm trùng việc cloud đang làm.

Ngoại lệ duy nhất đáng mở Claude Code local: khi cần **sửa thứ không đẩy lên git
được** (đường dẫn Windows, cài đặt MT5, driver). Việc đó hiếm.

### Mắt xích dễ quên: cloud NGỦ giữa các lượt

Tôi không chạy nền. Sau khi đẩy đơn, tôi dừng. Máy anh chạy xong đẩy kết quả lên
nhưng **không ai đánh thức tôi**. Phải tự hẹn:

- `send_later` / `create_trigger` — hẹn giờ đánh thức chính phiên này.
- Nhịp hẹn phải khớp **thời gian chạy thật của đơn**, không phải một con số đẹp.
  Đơn backtest lưới M5 mất ~8 giây; đơn quét 194 symbol mất ~92 giây; đơn MT5
  tester thật mất hàng chục phút. Hẹn 60 giây cho một đơn 40 phút là tự đốt
  lượt.

## 2. Phân vai — ranh giới theo PHÉP ĐO, không theo cảm tính

| Việc | Ai | Vì sao |
|---|---|---|
| Chọn việc tiếp, đọc kết quả, quyết định | **Cloud** | chỗ token đáng tiêu nhất |
| **Viết bài test** (= đặc tả) | **Cloud** | xem §3 |
| Viết code cho xanh test | **Thợ local** | vòng lặp, không đáng giá cao |
| Chạy MT5 tester | **Máy anh** | lằn TESTER = 1 là ràng buộc VẬT LÝ |
| Chấm ĐẠT / ÂM / CHƯA_ĐO_ĐƯỢC | **CODE** (`qwen/cong.py`) | LLM điền `co_che` 48 lần, thẩm định bác 41, ròng cứu 3 |

## 3. Luật không được phá: BÀI TEST LÀ CHỖ TIÊU TOKEN, KHÔNG PHẢI CHỖ TIẾT KIỆM

Bằng chứng từ phiên 19/09: đơn hàng số 2 **qua sạch mọi bài test tôi viết mà vẫn
sai** — nó đọc một bộ lọc spread thành `trailing_tu = 30`, tức bịa ra cơ chế
không có trong EA. Phải thêm 4 bài (3 bài dương-tính-giả + 1 bài hiệu chuẩn
ngược) rồi trả lại thì thợ mới sửa đúng.

Nghĩa là: **chất lượng bài test quyết định toàn bộ hệ hai máy.** Một bài test
lỏng biến thợ rẻ thành máy sinh mã sai được đóng dấu xanh.

Hai dạng bài bắt buộc trong mọi đơn:
- **Dương tính giả** — thứ KHÔNG được nhận. Không có bài này thì "nhận được"
  chỉ nghĩa là "nhận bừa".
- **Hiệu chuẩn ngược** — chứng minh bộ lọc có thật sự từ chối. Một cổng từ chối
  TẤT CẢ cho số liệu y hệt một cổng tốt.

## 4. MT5 trên GitHub Actions: viết rồi, CHƯA CHẠY LẦN NÀO

`actions_list` trả `total_count: 0`. Tôi viết `.github/workflows/mt5-tester.yml`
nhưng **không biết nó chạy được không**. Khâu rủi ro là cài MT5 im lặng rồi
**đăng nhập broker không màn hình** — chỗ hay chết mà không báo lỗi.

Thêm: Windows runner **nhân 2** khi tính quota, mỗi job tốn vài phút cài + tải
lịch sử trước khi chạy được backtest nào.

**Kết luận: Actions KHÔNG phải chỗ chạy backtest hàng loạt.** Chỗ của nó là
*kiểm chứng lại một kết quả trên máy sạch* (chống "chỉ đúng trên máy tôi").
Khối lượng thuộc về máy anh.

Cần 3 secrets (`MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`). Nếu chủ dự án không
muốn để mật khẩu broker lên GitHub thì **bỏ hẳn nhánh này** — thiết kế trên
không phụ thuộc vào nó.

## 5. Ràng buộc chặn hệ, và vì sao token không mua được nó

Ràng buộc là **lằn TESTER = 1**, không phải token. Mua token không mua thêm
throughput backtest. Token mua được: nhiều phiên NGHĨ song song, và giám sát kỹ
hơn.

Nên tiêu chí thiết kế đúng là **tối đa hoá thời gian máy anh chạy có ích**, chứ
không phải tối đa hoá token tiêu. Máy rảnh mà cloud đang nghĩ = lãng phí thật.
Hệ quả thực hành: **luôn giữ hàng đợi `viec/cho/` không rỗng** trước khi tôi
dừng lượt.

## 6. Cái còn THIẾU để chạy được (chưa xây)

1. `qwen/cau_git.py` — `git pull`/`push` vào vòng `q`, đọc `viec/cho/`, ghi
   `viec/xong/`.
2. **Hợp đồng kết quả** — mỗi đơn trả một JSON: `trang_thai` (DAT/AM/
   CHUA_DO_DUOC) + bằng chứng + số đo. Để cloud quyết định mà không đọc log.
3. **Kênh leo thang** — thợ gặp quyết định không tự làm được thì ghi
   `can_cloud: true` kèm câu hỏi; cloud đọc ở vòng sau.
4. **Chống giẫm chân** — `q` và phiên cloud có thể cùng sửa một file. Quy tắc
   phiên trong `CLAUDE.md` (một phiên [GHI], còn lại [DOC]) phải mở rộng cho
   máy: **máy anh là [GHI] với `data/`, `nao.db`, MT5; cloud là [GHI] với mã
   nguồn.** Không bên nào đụng vùng của bên kia.
