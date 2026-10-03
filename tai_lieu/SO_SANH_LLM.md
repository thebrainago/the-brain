# SO SÁNH MODEL RẺ: DeepSeek vs Qwen (chuẩn bị 02/10/2026, chạy 03/10)

> Chủ dự án: *"mai tôi sẽ gọi lại API cho cậu so sánh giữa DeepSeek và Qwen"*. Công cụ đã viết và test bằng nhà cung cấp giả
> (`test_so_sanh_llm.py`, 17 test); **chưa chạy với API thật**. Mã: `nhan/so_sanh_llm.py`, lệnh `b so-sanh`.

## Việc của chủ dự án (3 bước, ~5 phút)

1. **Chạy ở máy nhà** (cc-switch đã giữ khoá nên khoá không rời máy). Kiểm trước, KHÔNG gọi mạng, KHÔNG in khoá:
   `.\b.cmd so-sanh --khai` → mỗi nhà cung cấp hiện `OK` hoặc `THIEU <cái gì>`.
2. Nếu `THIEU`: đặt biến môi trường (hoặc thêm provider vào cc-switch) — **đừng dán khoá vào chat**:
   `SO_SANH_DEEPSEEK_KHOA`, `SO_SANH_QWEN_KHOA`, `SO_SANH_QWEN_URL` (vd DashScope hoặc ai-box), `SO_SANH_QWEN_MO_HINH`;
   giá (USD / 1 triệu token) `SO_SANH_<P>_GIA_VAO` / `_GIA_RA` — **chủ dự án điền, mình không đoán giá**. Qwen3 dạng "thinking" có thể cần
   `SO_SANH_QWEN_THEM={"enable_thinking": false}`.
3. Chạy `.\b.cmd so-sanh` (khoảng 2 × 8 lời gọi mỗi nhà cung cấp, vài chục nghìn token = vài xu). Đọc bảng 12 dòng.
   Thêm `--dai` (task ngữ cảnh dài ~12k token), `--lan 3` (lặp nhiều hơn), `--task a,b` (chạy vài task).

## Công cụ đo gì

Tám task chấm **bằng mã**, mô phỏng đúng việc tầng `tho` / `q` làm (không phải bài thi chung chung):

| Task | Đo | Chấm |
|---|---|---|
| `json_ky_luat` | tuân thủ định dạng + tính ngày | JSON sạch (không rào ```) + 2 giá trị đúng |
| `spec_co_che` | viết 5 khai báo cơ chế khác nhau | `ngu_phap.kiem_khai_bao` + `sinh_tu_spec` trên dữ liệu giả; trùng điều kiện vào không tính hai lần |
| `goi_cong_cu` | gọi công cụ kiểu OpenAI (`nc_tho` dùng) | đúng tên + đúng tham số |
| `trich_bang_bao_cao` | đọc bảng, trích số | cấu hình + hold %/năm + DD |
| `tinh_cagr_maxdd` | số học tài chính | tổng lời 50, maxDD 25, CAGR 22,47 (đáp án tính tay) |
| `luat_chan` | hiểu tiêu chí duyệt của chủ dự án | 4 ca (lãi+maxDD<80%, martingale chỉ là nhãn, phí khai ≠ đo) |
| `tom_tat_trung_thuc` | tóm tắt không bịa số | 4 sự kiện then chốt, phạt số lạ, giới hạn từ |
| `tieng_viet_2_cau` | tuân thủ chỉ dẫn tiếng Việt | đúng 2 câu, không markdown, có dấu, có "cache" |

Kết luận: **thắng / hòa / thua từng task** (không chỉ điểm TB) + chọn theo quy tắc: chênh điểm TB ≥ 0,1 → chọn điểm cao; còn lại → chọn rẻ hơn
(nếu đã khai giá). Kết quả đầy đủ: `reports/SO_SANH_LLM_<ngày>.json`.

## Giới hạn (nói thẳng)

- Chín lời gọi × 2 lần là **sàng lọc**: chênh < 0,1 là nhiễu. Muốn chắc hơn thì `--lan 5` hoặc thêm task (sửa `tao_task()` + một hàm chấm + một test).
- Task đo cái lab cần ở tầng rẻ; **không** đo khả năng nghiên cứu / lập trình dài hơi.
- Hai model dùng cùng nhắc và cùng nhiệt độ 0,2 — công bằng cho so sánh, nhưng mỗi model có thể giỏi hơn với nhắc riêng.
- Mạng ra ngoài của container cloud chặn nhiều host: chưa kiểm DeepSeek / Qwen từ cloud. Chạy ở nhà trước.
- Chọn xong: đặt `THO_MO_HINH` / `THO_KHOA_ENV` cho `b nc tho`, hoặc `model` trong `config/qwen.json` cho `q`.

## 03/10 chiều — chọn "Qwen Code + Qwen 3.8" hay "DeepSeek Harness + DeepSeek V4" (chủ dự án tự hỏi ở máy nhà)

Chủ dự án có một nguồn API LLM giá rẻ (tài liệu `https://home.ai-box.vn/docs`), đang nghiêng về Qwen Code gọi Qwen 3.8 hoặc DeepSeek Harness gọi DeepSeek V4 để **giảm token**. Cloud không vào được trang docs (chính sách mạng chặn), rồi chủ dự án rút câu hỏi khỏi cloud: *"thôi không cần tôi sẽ dùng câu hỏi này trên máy nhà"*. Dưới đây là những gì cloud đã biết, để phiên nhà khỏi tìm lại từ đầu:

- **Hệ đang dùng gì:** AI Box đã nối sẵn (`config/qwen.json`: `base_url https://api.ai-box.vn/v1`, `model qwen3.7-flash`, dự phòng `qwen3.6-flash`; khóa đọc cục bộ từ cc-switch, không bao giờ copy vào repo). AI Box chỉ có `/chat/completions` kiểu OpenAI (không có `/v1/responses`). `q`, `b nc tho`, `b tho` gọi **API trực tiếp**, chưa dùng "agent terminal". Đưa Qwen Code / DeepSeek Harness vào là thêm **một lớp mới** (agent tự đọc/sửa file); kết quả của model rẻ vẫn phải qua cổng chấm bằng code (`qwen/cong.py`), không tự chấm.
- **Số liệu công khai (cloud tra 03/10, chưa kiểm ở nhà; KHÔNG trích giá vì các nguồn mâu thuẫn):** Qwen 3.8 công bố 19/07/2026, phát hành chính thức 03/08/2026, có bản 27B dày (Apache-2.0, ngữ cảnh 262.144) và bản MoE 2,4T-A95B. **Qwen Code** là agent terminal mã nguồn mở đã chín (npm `@qwen-code/qwen-code` 0.24.7, 667 bản phát hành từ 07/2025, Node ≥ 22, nối OpenAI / Anthropic / Gemini, chạy không giao diện `qwen -p`, có subagent, MCP). **DeepSeek Harness** (`@deepseek-ai/dsh`, MIT, repo `deepseek-ai/deepseek-harness`) mới ~2 tháng, bản mới nhất `0.2.0-rc.2` là **bản thử** (release candidate). Một so sánh công khai nhỏ (bản flagship Max vs Pro): DeepSeek nhanh hơn / ít gọi công cụ hơn, Qwen mạnh hơn ở SWE-Bench Pro. DeepSeek có cache tiền tố tự động và endpoint tương thích Anthropic `/anthropic`.
- **Cần đọc trong docs AI Box (nhà ra được mạng):** AI Box liệt kê những model nào (đã có Qwen 3.8 / DeepSeek V4 chưa), giá vào/ra mỗi triệu token, chiết khấu cache, endpoint (OpenAI / Anthropic), giới hạn tốc độ, kích thước ngữ cảnh. Thiếu mục nào thì hỏi chủ dự án / nhà cung cấp, đừng đoán.
- **Cách chọn rẻ và có số:** `b so-sanh --khai` (kiểm cấu hình, không gọi mạng) → `b so-sanh` (8 task chấm bằng code) cho hai model; chỉ chạy thật khi chủ dự án đồng ý chi phí. Chọn agent và chọn model là hai việc tách được: Qwen Code nối được endpoint kiểu OpenAI nên về nguyên tắc chạy được model nào AI Box phục vụ (chưa thử) — nếu cần ổn định ngay thì Qwen Code (đã chín), DeepSeek Harness để sau khi ra bản chính thức.
