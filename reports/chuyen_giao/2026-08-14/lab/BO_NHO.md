# BỘ NHỚ DỰ ÁN — THE BRAIN (quyết định cố định của người dùng)

> File này lưu các quyết định/ưu tiên cố định mà người dùng đã chốt, để mọi phiên làm việc
> sau đều tuân theo. Cập nhật: 2026-08-12.

## 1. CHẾ ĐỘ TỰ ĐỘNG (AUTONOMOUS)
- **"Cứ đề xuất gì tôi duyệt luôn chạy luôn"** — người dùng mặc định duyệt mọi đề xuất hợp lệ.
- Nghĩa là: khi CHUNG đề xuất bước tiếp (test, build EA, thêm nguồn, thêm dữ liệu...),
  **tiến hành chạy luôn**, không chờ xác nhận từng bước, trừ khi có rủi ro phá huỷ dữ liệu / tiền thật.
- Vẫn giữ nguyên tắc an toàn: **không giao dịch tiền thật**, chỉ demo; không sửa file ngoài phạm vi vai.

## 2. TÀI KHOẢN DEMO MT5
- **Tài khoản demo MT5 đã có sẵn** trên máy (dùng cho việc chạy EA + xác minh chiến lược).
- MT5 chính: `C:\Program Files\MetaTrader 5\` (data `D0E8209F77C8CF37AD8BF550E51FF075`).
- Các broker khác đã cài terminal: FXCE, Ultima Markets, Exness, XM.
- MT5 Strategy Tester đã có hạ tầng sẵn: `mt5_worker.py` (chạy `terminal64.exe /config:*.ini`).

## 3. VIỆC ĐANG LÀM / ĐỀ XUẤT ĐÃ DUYỆT
- [x] Dựng + backtest Ichimoku cross (Quantlab) — `quant/`.
- [ ] Đưa Ichimoku EURUSD lên **MT5 Strategy Tester** (tick thật) — EA + run.
- [ ] **Tự động tạo tài khoản demo sàn khác** (giả lập thao tác người dùng) — dang làm.
- [ ] Test MT5 thật Daily Zone gold TP=50 (ưu tiên 1 còn nợ).

## 4. NGUYÊN TẮC BẤT BIẾN
1. Rigorous ở cổng ra (nơi mất tiền), thoải mái ở cổng vào (khám phá).
2. Backtest phải có **chi phí thật** (spread+swap) và **so với buy&hold**; MT5 tick là bước cuối.
3. Không tự tinh chỉnh tham số đã đăng ký (khoá FDR).
4. Không chạy vòng lặp 24/7 từ sub-agent; không để tiến trình nền.
5. Trả lời tiếng Việt.

## 6. LOGIC "LÀM NGAY" (EVO chot 2026-08-12)
- Khi co y tuong / de xuat moi: LAM NGAY, khong cho duyet tung buoc.
- Viec nho (< vai phut): chay ngay roi bao ket qua.
- Viec lon: khoi dong phan lam duoc ngay, ghi phan cho vao BAN_GIAO.json.
- Van giu: khong tien that, khong vong lap 24/7 tu sub-agent, khong pha du lieu.
