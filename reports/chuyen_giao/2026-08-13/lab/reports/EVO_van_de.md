# EVO — BÁO CÁO GIÁM SÁT 3 TRỤ (VẤN ĐỀ / ĐỀ XUẤT)

> Thời điểm quét: **2026-08-12 19:48:23** (Asia/Saigon) · Module: `lab/evo_theo_doi.py`
> Quét thủ công 1 lượt, KHÔNG phải vòng lặp 24/7.

## 1. TRẠNG THÁI NGUỒN ĐẦU VÀO

- `reports\SEEKER_backtest_pha.md`: quet 49 dong -> 3 van de
- `reports\SEEKER_nguon_chat_luong.md`: quet 100 dong -> 6 van de
- `reports\quet.log`: quet 30 dong -> 5 van de
- `reports\banker_brief.md`: quet 25 dong -> 0 van de
- `reports\BANKER_vn_macro.md`: quet 28 dong -> 0 van de
- `quant\KET_QUA.md`: quet 103 dong -> 9 van de
- `quant\KET_QUA_ichimoku_cross.md`: quet 43 dong -> 2 van de
- `quant\TAI_LIEU.md`: quet 35 dong -> 1 van de

## 2. BẢNG VẤN ĐỀ PHÁT HIỆN

Tổng: **26** vấn đề (cao=12, trung=13, thấp=1).

| # | Ưu tiên | Nhóm vấn đề | Mô tả ghi nhận | Nguồn | File | Gợi ý giải pháp |
|---|---------|-------------|----------------|-------|------|------------------|
| 1 | CAO | Can dua len MT5 / Viet EA | Nguyên tắc dự án (THE_BRAIN): Python sàng lọc nhanh TRƯỚC → MT5 tick CUỐI. Không tin backtest Python trước khi qua MT5 tick. | SEEKER | `reports\SEEKER_backtest_pha.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 2 | CAO | Can dua len MT5 / Viet EA | Pipeline 3 lớp: Python scan → MT5 tick → (tùy chọn) forward demo thật . Mỗi lớp có ngưỡng riêng. | SEEKER | `reports\SEEKER_backtest_pha.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 3 | CAO | Can dua len MT5 / Viet EA | Sớm xác minh cơ chế vàng "Daily Zone Gold TP=50" qua MT5 tick (theo CAI_THIEN_BRAIN.md ) bằng EA phù hợp. | SEEKER | `reports\SEEKER_backtest_pha.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 4 | CAO | Loi code / crash | 2026 08 11 22:02:14 [LOI] kham_pha: name 'concurrent' is not defined :: Traceback (most recent call last): | SEEKER | `reports\quet.log` | Sua loi code / bo sung import thieu, chay lai thanh phan loi. |
| 5 | CAO | Loi code / crash | NameError: name 'concurrent' is not defined. Did you forget to import 'concurrent'? | SEEKER | `reports\quet.log` | Sua loi code / bo sung import thieu, chay lai thanh phan loi. |
| 6 | CAO | Can dua len MT5 / Viet EA | Đây là sàng lọc Python , chưa qua MT5 tick. Kết quả KHÔNG phải lời hứa lợi nhuận. | QUANTLAB | `quant\KET_QUA.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 7 | CAO | Can dua len MT5 / Viet EA | Nhận xét: logic "retest + engulfing" có vẻ bắt sóng tốt hơn khi có biến động mạnh (vàng) , nhưng mẫu EURUSD quá ít. Cần xác minh MT5 tick tr | QUANTLAB | `quant\KET_QUA.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 8 | CAO | Can dua len MT5 / Viet EA | 1. Python sàng lọc sơ, chưa qua MT5 tick. Dữ liệu D1 của Yahoo không phải tick MT5; không mô phỏng trượt giá theo thời điểm thực, độ khớp lệ | QUANTLAB | `quant\KET_QUA.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 9 | CAO | Can dua len MT5 / Viet EA | Đưa B_Chikou_DI trên EURUSD (case duy nhất vượt buy&hold) lên MT5 tick để xác minh. | QUANTLAB | `quant\KET_QUA.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 10 | CAO | Can dua len MT5 / Viet EA | Đây là sàng lọc Python cấp 1 , chưa qua MT5 tick. Khung intraday (phút/giờ) phải test bằng MT5 Strategy Tester. | QUANTLAB | `quant\KET_QUA_ichimoku_cross.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 11 | CAO | Nhin du lieu tuong lai (lookahead bias) | Cơ chế: Tenkan (9) cắt Kijun (26) — golden cross → LONG, death cross → SHORT, vào lệnh ở giá close của nến xác nhận (không lookahead). | QUANTLAB | `quant\KET_QUA_ichimoku_cross.md` | Kiem tra bias du lieu: chi dung du lieu qua khu (shift +), chay lai backtest. |
| 12 | CAO | Can dua len MT5 / Viet EA | Dữ liệu 1 phút → cần MT5 tick (khớp kế hoạch đưa chiến lược lên MT5 tester). | QUANTLAB | `quant\TAI_LIEU.md` | Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua. |
| 13 | TRUNG | Nguon bi chan / loi fetch | Collective2 https://www.collective2.com/ Thư viện chiến lược, return, drawdown, track record api/login 1 Request thuần trả 403 (Cloudflare). | SEEKER | `reports\SEEKER_nguon_chat_luong.md` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 14 | TRUNG | Nguon bi chan / loi fetch | SG CTA Index https://www.sgindex.com/ Chỉ số CTA/Trend, return theo tháng public 1 Request thuần trả 403 (Cloudflare). Nên lấy bản dữ liệu E | SEEKER | `reports\SEEKER_nguon_chat_luong.md` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 15 | TRUNG | Nguon bi chan / loi fetch | NilssonHedge https://nilssonhedge.com/ CTA ranking, quỹ top public 2 Request thuần trả 403. | SEEKER | `reports\SEEKER_nguon_chat_luong.md` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 16 | TRUNG | Nguon bi chan / loi fetch | Collective2 https://www.collective2.com/ ❌ 403 (Cloudflare) Cần login/session trình duyệt. | SEEKER | `reports\SEEKER_nguon_chat_luong.md` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 17 | TRUNG | Nguon bi chan / loi fetch | SG Index https://www.sgindex.com/ ❌ 403 Chặn; lấy dữ liệu chỉ số từ file Excel/PDF công khai. | SEEKER | `reports\SEEKER_nguon_chat_luong.md` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 18 | TRUNG | Nguon bi chan / loi fetch | NilssonHedge https://nilssonhedge.com/ ❌ 403 Chặn request thuần. | SEEKER | `reports\SEEKER_nguon_chat_luong.md` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 19 | TRUNG | Nguon bi chan / loi fetch | CAN_THEM_BOT: forexsignals (Bad Request: chat not found) | SEEKER | `reports\quet.log` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 20 | TRUNG | Nguon bi chan / loi fetch | CAN_THEM_BOT: tradingp (38.3s) | SEEKER | `reports\quet.log` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 21 | TRUNG | Nguon bi chan / loi fetch | 2026 08 12 18:29:44 [OK] reddit: reddit: doc 0, them 0 new: bi chan (403/429) (2.1s) | SEEKER | `reports\quet.log` | Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the. |
| 22 | TRUNG | Tai san delisted / thay nguon | Tài sản: S&P 500 ( ^GSPC ), Vàng ( GC=F — futures, thay cho XAUUSD=X đã delisted trên Yahoo ), EUR/USD ( EURUSD=X ). | QUANTLAB | `quant\KET_QUA.md` | Thay nguon/tai san bi delisted bang tuong duong va ghi ro sai lech. |
| 23 | TRUNG | PF thap / thua buy-hold | SP500: PF 1.33, Sharpe 0.54 — lãi 32.8%, thua xa buy&hold. | QUANTLAB | `quant\KET_QUA.md` | Rasoat lai chi phi + mau that; neu van thap thi loai khoi dien uu tien. |
| 24 | TRUNG | PF thap / thua buy-hold | SP500: thua buy&hold (PF 1.02, Sharpe 0.06, DD 39.7%). | QUANTLAB | `quant\KET_QUA.md` | Rasoat lai chi phi + mau that; neu van thap thi loai khoi dien uu tien. |
| 25 | TRUNG | Tai san delisted / thay nguon | 2. Vàng dùng futures GC=F , không phải XAUUSD spot (đã delisted trên Yahoo). Nến contang/backwardation của futures có thể lệch nhẹ so với sp | QUANTLAB | `quant\KET_QUA.md` | Thay nguon/tai san bi delisted bang tuong duong va ghi ro sai lech. |
| 26 | THAP | Nhin du lieu tuong lai (lookahead bias) | ⚠️ Đã sửa lỗi lookahead bias trong bản ngày 12/08: bản đầu dùng shift( 26) (nhìn dữ liệu tương lai) cho Sharpe 1.37 trên SP500 — sai, đã bỏ  | QUANTLAB | `quant\KET_QUA.md` | Kiem tra bias du lieu: chi dung du lieu qua khu (shift +), chay lai backtest. (chi tiet ghi da xu ly — theo doi lai.) |

## 3. TÓM TẮT HÀNH ĐỘNG

- **Ưu tiên CAO (12 vấn đề):** Can dua len MT5 / Viet EA (quant\KET_QUA.md, quant\KET_QUA_ichimoku_cross.md, quant\TAI_LIEU.md, reports\SEEKER_backtest_pha.md); Loi code / crash (reports\quet.log); Nhin du lieu tuong lai (lookahead bias) (quant\KET_QUA_ichimoku_cross.md)

- **Ưu tiên TRUNG (13 vấn đề):** Nguon bi chan / loi fetch (reports\SEEKER_nguon_chat_luong.md, reports\quet.log); Tai san delisted / thay nguon (quant\KET_QUA.md); PF thap / thua buy-hold (quant\KET_QUA.md)

- **Ưu tiên THAP (1 vấn đề):** Nhin du lieu tuong lai (lookahead bias) (quant\KET_QUA.md)

## 4. NGUỒN Ý TƯỞNG GIẢI PHÁP (Facebook — người dùng gửi làm ví dụ)

> 2 post này **không fetch được** (tường đăng nhập), chỉ lưu link làm **ý tưởng** để EVO/CHUNG tham khảo khi đề xuất giải pháp — cần theo dõi/gợi ý người dùng dán nội dung.

- **FB post 1 (nguoi dung gui)**: <https://www.facebook.com/100063765812298/posts/1619897140145798/>
- **FB post 2 (nguoi dung gui)**: <https://www.facebook.com/story.php?story_fbid=1613489464119899&id=100063765812298>

---
_File này do EVO tự tạo mỗi lượt quét; không sửa các file khác trong lab._
