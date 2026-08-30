# PHIẾU ĐIỀN CẤU HÌNH NGUỒN — THE BRAIN

> **Cách dùng:** mở file này (Notepad), điền thẳng vào chỗ `...` mỗi ô. Xong báo tôi
> để **lưu + nối vào code** rồi **chuyển lên VPS** cho dễ.
> **Nguyên tắc:** chỉ điền API/URL **công khai**; passview chỉ khi **chủ tự nguyện công khai**.
> Cột "độ ưu tiên" ghi theo bậc 1–5 (NGUON.md).

============================================================
## 1. API / TÀI KHOẢN NỀN TẢNG (bậc 2 — nơi thấy hiệu quả thật)
============================================================
| Khoản                     | Hướng dẫn                                                                 | Điền vào đây (...) |
|---------------------------|---------------------------------------------------------------------------|--------------------|
| DEEPSEEK_API_KEY          | tạo key tại platform.deepseek.com ("Create new API key")                  | ... |
| Darwinex API (client id)  | Darwinex → API dashboard → tạo app → copy Client ID                        | ... |
| Darwinex API (secret)     | như trên                                                                    | ... |
| Collective2              | C2 → Settings → API (nếu có) hoặc trang public                            | ... |
| eToro                    | trang public, không cần key (theo dõi Popular Investor)                    | (link nếu cần) |
| FX Blue                  | fxblue.com → Tools → API key (nếu có)                                     | ... |
| Myfxbook                | myfxbook.com → Settings → API token (nếu có)                              | ... |
| MQL5 Signals/Market      | không cần key — scrape trang (1 mình lo)                                  | — |
| FTMO/TopStep/Apex leaderboard | không cần key — scrape leaderboard (1 mình lo)                      | — |
| QuantConnect/Kaggle/Numerai | không cần cho đọc kết quả; cần key nếu muốn chạy (gửi sau)            | ... |

============================================================
## 2. NGUỒN CẦN ĐĂNG NHẬP (Playwright — bạn đăng nhập 1 lần, tôi đọc lịch sử)
============================================================
> Cách: tôi mở cửa sổ Playwright → bạn gõ tài khoản/mật khẩu + captcha/2FA 1 lần →
> tôi lưu phiên (cookie) → từ đó đọc tự động. Tôi KHÔNG tự đăng nhập tài khoản người khác.
| Nền tảng (tên trang) | Đăng nhập bằng gì (email/phone) | Điền vào đây |
|----------------------|----------------------------------|--------------|
| (ví dụ) eToro        | email + mật khẩu của BẠN         | ... |
| ...                  | ...                              | ... |

============================================================
## 3. PASSVIEW / TÀI KHOẢN IMPORT (chỉ khi chủ TỰ NGUYỆN công khai)
============================================================
| Số tài khoản | Investor password | Nền tảng (MT4/MT5/ctrader) | Ghi chú (ai, vì sao tin) |
|--------------|-------------------|----------------------------|--------------------------|
| ...          | ...               | ...                        | ... |

============================================================
## 4. NGUỒN DÁN TAY (FB / TikTok / trang đóng — bậc 5, không ưu tiên)
============================================================
| Link                        | Nội dung (paste tham số/chiến lược) | Ưu tiên (1-5) |
|-----------------------------|---------------------------------------|---------------|
| ...                         | ...                                   | ... |

============================================================
## 5. NGƯỜI GIỎI / QUỸ MUỐN MÔ PHỎNG (bậc 1)
============================================================
| Tên          | Loại (quỹ/trader/academic) | Nguồn tài liệu (sách/paper/link) | Ghi chú |
|--------------|----------------------------|----------------------------------|---------|
| ...          | ...                        | ...                              | ... |

============================================================
## 6. CẤU HÌNH VPS (để chạy 24/7)
============================================================
| Khoản                          | Điền vào đây |
|--------------------------------|--------------|
| IP / user / mật khẩu VPS       | ... |
| Thư mục chung (Google Drive/copy) | C:\...\lab_chung |
| Lịch chạy (giờ VPS)            | ... |
| Có MT5 + dữ liệu M1 chưa?      | có / chưa |