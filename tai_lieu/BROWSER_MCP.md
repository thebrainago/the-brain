# Browser MCP cho Seeker (cài 18/10/2026, theo yêu cầu chủ dự án)

**Là gì:** [Browser MCP](https://browsermcp.io) = một tiện ích Chrome + một máy chủ MCP (`@browsermcp/mcp`, npm). Agent (Claude Code, Grok…) gửi lệnh duyệt web qua giao thức MCP; lệnh chạy trên **Chrome thật** đang mở, với hồ sơ, cookie và phiên đăng nhập sẵn có. Vân tay trình duyệt là của người thật, nên các trang sau Cloudflare đọc được, trong khi Puppeteer/Playwright headless thì bị chặn.

**Vì sao cần cho Seeker:** những nguồn quý nhất (MQL5 Code Base / Market / Signals, ForexFactory, Myfxbook, diễn đàn EA, nhóm chia sẻ) thường nằm sau Cloudflare hoặc cần đăng nhập. `requests` thì nhận 403; headless thì bị chặn.

## 1. Hai đường đọc trình duyệt thật, dùng chung MỘT hồ sơ

| Đường | Ai dùng | Cách |
|---|---|---|
| `nhan/doc_trinh_duyet.py` (CDP cổng 9224) | **Mã Python** của Seeker, chạy tự động (`seeker_kham_pha_sau.py`, `tru/seeker.py`) | `may_nha/mo_trinh_duyet_ai.cmd` mở Chrome riêng của AI, rồi Python nối vào CDP |
| **Browser MCP** (mới) | **Agent** đọc tay: mở trang, bấm, cuộn, đọc cả bài, tải file đính kèm | Tiện ích Browser MCP trong cùng Chrome đó; agent gọi công cụ `browser_navigate`, `browser_snapshot`, `browser_click`… |

Cả hai đều dùng **trình duyệt riêng của AI** (`may_nha/.browser_thebrain`, git bỏ qua). **Không** cài vào Chrome cá nhân của anh: agent chỉ thấy những phiên mà anh đã đăng nhập vào hồ sơ riêng này (tài khoản demo, mail dự phòng).

## 2. Cài (máy nhà, một lần)

1. Cần Node.js 18 trở lên.
2. Chạy `may_nha\CAI_BROWSER_MCP.cmd`. Script làm hai việc:
   - đăng ký máy chủ MCP cho Claude Code: `claude mcp add browsermcp --scope user -- cmd /c npx -y @browsermcp/mcp@0.1.3` (ghim phiên bản; 0.1.3 là bản mới nhất trên npm);
   - mở Chrome riêng của AI tại trang tiện ích trên Chrome Web Store (id `bjfgambnhccakkhmkepdoekmckoijdlc`). Anh bấm **Add to Chrome** một lần.
3. Mỗi phiên làm việc: trên tab muốn cho agent dùng, bấm biểu tượng Browser MCP → **Connect**. Trong Claude Code, gõ `/mcp` để kiểm tra `browsermcp` báo connected.

## 3. Agent khác (Grok, Qwen, Cursor…)

Cấu hình MCP chuẩn (Windows), đặt vào file cấu hình MCP của công cụ đó:
```json
{"mcpServers": {"browsermcp": {"command": "cmd", "args": ["/c", "npx", "-y", "@browsermcp/mcp@0.1.3"]}}}
```
Mỗi lúc chỉ **một** agent được nối vào tiện ích (một cổng WebSocket), giống luật TESTER = 1.

## 4. Seeker dùng thế nào

1. `python tru/seeker.py san-kho` và các đường Python vẫn chạy như cũ. Đường nào báo `403`, `khong_mo_cdp` hay "Just a moment…" thì ghi URL vào danh sách để agent đọc tay.
2. Agent mở URL đó qua Browser MCP, **đọc cả trang** (cả mã nguồn đính kèm nếu có), rồi ghi tóm tắt: luật vào, luật thoát, cách DCA / hedge / gỡ lệnh, tham số mặc định, URL. Mã của người khác chỉ lưu ở `data/`; repo chỉ giữ tóm tắt và URL.
3. **Luật khi dùng:**
   - Agent **không** gõ mật khẩu, **không** giải CAPTCHA, **không** tạo tài khoản thay anh. Gặp màn hình đăng nhập hay xác minh thì dừng và báo anh.
   - Đọc nhịp như người (vài giây mỗi trang), không quét hàng loạt bằng MCP. Quét số lượng lớn là việc của đường Python.
   - Không bấm mua, không gửi form, không đăng bài.

## 5. Không cài trên cloud

Phiên Claude trên cloud không có Chrome của anh và dùng IP máy chủ, nên Browser MCP chỉ có ích ở **máy nhà**.

**Tham khảo khác:**
- *Stealth Browser MCP* (`vibheksoni/stealth-browser-mcp`, dùng nodriver) tự xưng vượt được nhiều lớp chống bot hơn. Chưa kiểm chứng độc lập; chỉ thử nếu Browser MCP không đủ.
- Nếu không muốn bấm Connect mỗi phiên: `chrome-devtools-mcp` hoặc `@playwright/mcp --cdp-endpoint http://127.0.0.1:9224` nối thẳng vào CDP 9224 có sẵn.
