# SLOT TESTER — cách thêm làn tester thứ hai

*Viết 16/09/2026, gói G2-A. Đọc cùng `b slot` và `nhan/slot_tester.py`.*

## Vì sao cần

`ngan_sach.TESTER = 1` lâu nay được gọi là "ràng buộc **vật lý**". Đo lại
16/09 bằng `b ho-so` mục 11.7: máy có **6 bản cài MT5** và **8 thư mục dữ liệu
terminal** riêng. Ràng buộc nằm ở **mã nguồn**, không ở máy.

Tester là **nút thắt số 1** của cả hệ: mọi kết luận cuối cùng đều phải đi qua
nó, và 10 nhân / 20 luồng CPU không giúp được gì ở khâu đó.

## Trạng thái hiện tại (đo 16/09)

Chỉ **một** thư mục dữ liệu có lịch sử giá thật:

| Thư mục | Bản cài | Mã có lịch sử | Dung lượng |
|---|---|---|---|
| `BB16F565…` | XM Global MT5 | **32** | 2,42 GB |
| `53785E09…` | MetaTrader 5 EXNESS | 14 | 0,06 GB |
| `D0E8209F…` | MetaTrader 5 | 4 | 0,10 GB |
| `1A842330…` | FXCE MT5 | 4 | 0,04 GB |
| `43A9BD89…` | Ultima Markets MT5 | 4 | 0,04 GB |
| `656C3515…` | XM MT5 | **0** | 0 |

Năm thư mục còn lại **không dùng làm slot được**, và lý do không phải dung
lượng: **khác broker là khác symbol, khác spread, khác dữ liệu lịch sử**. Hai
slot khác broker cho hai kết quả không so được với nhau — mà tệ hơn, chúng vẫn
in ra một bảng số trông như so được.

**Slot 2 phải là bản sao portable của chính XM Global MT5.**

## Các bước tay (cần chủ dự án — có bước đăng nhập)

1. **Sao thư mục cài đặt**
   ```
   xcopy "C:\Program Files\XM Global MT5" "C:\MT5_slot2" /E /I /H
   ```
   Không dùng bản cài của broker khác.

2. **Bật chế độ portable** — chạy `C:\MT5_slot2\terminal64.exe /portable`.
   Ở chế độ này MT5 giữ dữ liệu **ngay trong thư mục cài**
   (`C:\MT5_slot2\MQL5`, `C:\MT5_slot2\bases`) thay vì trong `AppData`, nên
   hai slot không đụng nhau.

3. **Đăng nhập** đúng tài khoản XM đang dùng cho tester (tài khoản đọc/demo,
   không cần tài khoản tiền thật).

4. **Tải lịch sử giá** cho những mã sẽ chạy: mở biểu đồ từng mã, kéo về quá
   khứ, hoặc dùng Symbols → chọn mã → Download. Slot 2 phải có **cùng số
   bar/năm** với slot 1, nếu không thì hai slot trả hai kết quả khác nhau vì
   dữ liệu khác nhau chứ không phải vì cơ chế khác nhau.

5. **Khai vào `config/slot_tester.json`**
   ```json
   {"slots": [
     {"ten": "mac_dinh", "exe": "C:\\Program Files\\XM Global MT5\\terminal64.exe",
      "du_lieu": "C:\\Users\\SV STORE\\AppData\\Roaming\\MetaQuotes\\Terminal\\BB16F565FAAA6B23A20C26C49416FF05",
      "hau_to": ""},
     {"ten": "s2", "exe": "C:\\MT5_slot2\\terminal64.exe",
      "du_lieu": "C:\\MT5_slot2", "hau_to": "_s2"}
   ]}
   ```
   `hau_to` làm tên file đầu ra tách nhau (`KhoCoChe_s2.mq5`, `..._s2.xml`).

6. **`b slot`** — kiểm khai báo, phát hiện trùng thư mục.

7. **`b slot kiem`** — kiểm điều kiện nâng trần.

## Hai phép thử BẮT BUỘC trước khi nâng trần

Chưa có cả hai thì `nen_nang_tran()` từ chối, và `ngan_sach.TESTER` giữ nguyên 1.

**a. Cùng cấu hình, hai slot → kết quả Y HỆT.** Chạy một cấu hình đã biết kết
quả trên slot 1, rồi trên slot 2. Lệch một lệnh cũng là hỏng — nghĩa là dữ
liệu hai slot khác nhau.

**b. Hai cấu hình khác nhau chạy CÙNG LÚC → mỗi kết quả khớp với lần chạy
riêng lẻ.** Đây là phép thử bắt ghi đè. Ghi đè là kiểu hỏng **không báo lỗi**:
bảng số đọc y hệt một kết quả thật.

Ghi kết quả vào `reports/slot_kiem_chung.json`:
```json
{"giong_nhau": true, "song_song_khop": true,
 "ghi_chu": "chạy ngày … trên cấu hình …, số lệnh … / …"}
```

Nếu (a) hoặc (b) sai: **giữ TESTER = 1**, ghi nguyên nhân, không nâng.

## Còn nợ trong mã nguồn

`nhan/slot_tester.py` gỡ được hai trong bốn chỗ ghim cứng: đường dẫn exe
(qua `BRAIN_MT5`/`BRAIN_MT5_DATA`) và khoá theo slot.

**Chưa gỡ:** `chay_tester_kho.py` vẫn ghi đè cùng một
`MQL5/Experts/<TEN_EA>.mq5`, cùng một `.ini`, cùng một `.xml`. Với hai slot có
thư mục dữ liệu **riêng** thì không đụng nhau, nhưng nếu ai khai hai slot dùng
chung thư mục thì hỏng ngay — `trung_thu_muc()` chặn đúng trường hợp đó.

Bước tiếp: cho `chay_tester_kho` nhận `slot` để đặt tên file đầu ra qua
`slot.ten_ea()` và `slot.tep()`.

## Số slot nên đặt

Đừng lấy số nhân CPU. MT5 tester tự chia nhiều agent cho mỗi lần tối ưu, nên
hai slot có thể đã dùng hết máy. **Bắt đầu 2**, đo thời gian / CPU / RAM ở 1
slot và 2 slot, rồi mới tính tăng.
