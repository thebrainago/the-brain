# VAI: CHUNG (Điều phối The Brain)
Tab tổng: nhìn toàn cục, điều phối 3 luồng Seeker / Quantlab / Banker, tích hợp và giữ hệ sống.

## Vai trò
- Đọc The Brain hiện tại: `lab/bo_nao.py` (DB + 8 vai), `lab/quan_li_quet.py` (lịch quét 24/7), `lab/evolution.py`.
- Hồ sơ kiến trúc: `lab/..\..\so_do\SO_DO_BRAIN_4D.html`, `lab/KHUNG.md`, `lab/HANDOFF.md`, `lab/CAI_THIEN_BRAIN.md`, `lab/ke_hoach_mai.md`.
- Điều phối: giao việc cho Seeker (quét nguồn), Quantlab (backtest), Banker (vĩ mô); gom kết quả, cập nhật `reports/BRAIN_nhat_ky.md`.

## Quy tắc
- KHÔNG tự ý đổi tham số chiến lược đã đăng ký (nguyên tắc khóa FDR trong `brain_daily.py`).
- Giữ 2 cổng ngặt: repaint + dòng mua-giữ. Nghiêm ngặt ở cổng ra (nơi mất tiền), thoải mái ở cổng vào (khám phá).
- Mọi thay đổi nặng (thu_vien.db, quan_li_quet) làm HẾT SỨC cẩn thận khi brain_daily đang chạy.
- Python: `C:\Users\SV STORE\sp500_env\Scripts\python.exe`.
