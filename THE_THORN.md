# THE THORN — Watchdog giữ 3 trụ THE BRAIN sống & tự hồi phục

> **DA NGHI HUU 16/09/2026 — DOC MUC NAY TRUOC.**
>
> `the_thorn.py` khong con o `lab/`, no nam trong `nghi_huu/the_thorn.py`, va
> **khong tac vu Windows nao dang chay no** (`schtasks /query` khong co
> `BrainThorn_keeper`). Ngoai ra no ghim cung duong Python
> `AppData\Local\Python\pythoncore-3.14-64` — duong do khong con ton tai tren
> may (nay la `C:\Python314`), nen chay thang cung gay ngay.
>
> Viec cua no da chuyen sang **`dieu_phoi.py`** (supervisor 24/7, co watchdog +
> restart + nhip tim). Bat bang `b chay`, dung bang `b dung`.
>
> Tai lieu nay giu lai vi **sau quy tac R1-R6 van dung** va `dieu_phoi` nen
> duoc doi chieu voi chung. Dung doc phan "Van hanh" ben duoi nhu huong dan
> con hieu luc — do la ban cua the_thorn da nghi.


> Bộ quy tắc (rules) cho phần chạy 24/7. Khi hệ thống KHÔNG hoạt động hoặc KHÔNG
> có tác vụ, THE THORN chủ động KÍCH HOẠT LẠI **1 lần** để phòng trường hợp mất
> kết nối / mất mạng thoáng qua — rồi mới coi là lỗi thật.

## 6 QUY TẮC CỨNG

| # | Quy tắc | Hành vi cụ thể |
|---|---------|----------------|
| R1 | Mỗi trụ 1 tiến trình độc lập | SEEKER, QUANT, BANKER chạy song song, mỗi trụ tự log |
| R2 | **Kích hoạt lại 1 lần** | Trụ LOI / không có đầu ra / kẹt → tự restart LẠI 1 lần ngay (guard mất mạng thoáng) |
| R3 | Hết nhuồng | Nếu lần retry (R2) vẫn lỗi → ghi thống kê lỗi + cooldown rồi lên lịch lại; không boom vô hạn |
| R4 | Trụ "dạng im" | Không có output mới quá hạn (SEK 150s / QUANT 480s / BANK 300s) → coi kẹt, giết + retry 1 lần |
| R5 | Evolution định kỳ | Chạy `evolution.py` mỗi 30 phút để quan sát lỗi + tự tối ưu keyword/đề xuất |
| R6 | Dừng đúng giờ | Dừng lúc 23:00 hôm nay, hoặc khi có file `THORN_STOP`, hoặc Ctrl-C |

## Vận hành
- Chạy: `python the_thorn.py` (tới 23:00) · `python the_thorn.py --phut 40` (40 phút)
- Theo dõi: `reports/thorn_heartbeat.txt` (nhịp tim), `reports/thorn_log.jsonl` (sự kiện),
  `reports/thorn_stats.json` (thống kê ok/lỗi/revive), `tru_<ten>.log` (log từng trụ).
- Muốn dừng sớm: tạo file `THORN_STOP` trong thư mục `lab/`.

## Bản ghi sự kiện (`thorn_log.jsonl`)
Mỗi dòng 1 JSON: `{luc, tru, loai(ok/loi-mang/loi-code/kem-may/start/EVOLUTION), rc, retry}`.
Phân biệt **loi-mang** (mất kết nối — đáng retry) vs **loi-code** (lỗi logic — cần sửa).
