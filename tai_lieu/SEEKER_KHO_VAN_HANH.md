# SEEKER: TÌM KHO EA / CHỈ BÁO / CHIẾN LƯỢC VẬN HÀNH ĐƯỢC (chủ dự án 18/10/2026)

> *"Ngay từ bộ lọc của chúng ta cũng đã bị xa thực tế rồi. Các cậu luôn đi tìm một cách mơ màng, đào ở những nơi không có giá trị thì làm sao thu thập được những thứ có công hiệu. Tôi cần những hệ thống giao dịch, những kho EA và indicator, strategy mà vận hành được. Các cậu phải xem xét từ khoá, ký hiệu, đọc cả file để tìm những kho, nguồn như trên. Lấy của họ về, chúng ta nghiên cứu, biến tấu và kết hợp."*

**Áp cho mọi agent làm Seeker: Claude, Grok, Qwen, DeepSeek.** Tài liệu này thắng mọi danh sách nguồn hay từ khoá cũ.

## 1. Seeker đã đào sai chỗ (đo ngày 18/10/2026)

| Đo | Số |
|---|---|
| Đường tìm trong `tru/seeker.py` là học thuật hoặc thảo luận (arXiv, OpenAlex, Crossref, Semantic Scholar, HackerNews, StackExchange) | **6/13** |
| Nguồn trong `config/nguon_seeker.json` là kho mã (`code` + `ma_nguon`) | **28/303** (còn lại: blog 53, diễn đàn 33, Telegram 22, mạng xã hội 12…) |
| Từ khoá gốc đứng đầu | "momentum factor", "statistical arbitrage", "market microstructure", "deflated sharpe": từ của bài báo, không phải của EA |
| Cơ chế trong kho `config/co_che_dsl.json` **không gom từ đâu cả** (hệ tự sinh, `noi_sinh`) | **1.510/4.049 (37 %)** |
| Một EA gom về bị rút thành… | **đúng 1 luật vào lệnh**; phần xử lí lệnh mất hết |
| Đọc một repo GitHub (`bo_nao._cao_github`) | chỉ **6 file nhỏ nhất**. EA31337 có 111 chiến lược trong repo con, nên chỉ đọc được vỏ |
| Kho cơ chế xử lí lệnh | 75 cái, trong đó **40 cái bị bộ lọc chặn** (DCA không trần, martingale). Đã sửa 17/10 |

## 2. Thứ CẦN tìm, theo thứ tự

1. **KHO**: repo hoặc tổ chức gom nhiều EA, chiến lược, chỉ báo một chỗ (như EA31337: 69 chiến lược và 42 meta trong một khung).
2. **EA và bot xử lí lệnh**: lưới, DCA, martingale, hedge, gỡ lệnh, chốt rổ, trailing, đóng một phần (như passivbot "auto unstuck", hummingbot DCA/grid executor).
3. **Chỉ báo có mã** (MQL4/5, Pine, Python, C#) và **chiến lược có mã**, chạy được.
4. Chỉ sau đó mới đến bài viết, video, diễn đàn, và **chỉ khi có luật cụ thể hoặc link tới mã**. Bài báo học thuật thì để cuối.

## 3. Nhận ra thứ "vận hành được" bằng KÝ HIỆU, đọc CẢ FILE

`tru/seeker.py → dau_hieu_van_hanh(van_ban, ten_file)` đọc toàn bộ nội dung file (kể cả MQL lưu UTF-16) và phân loại:

| Nền tảng | EA / bot (tự đặt lệnh) | Lớp chiến lược | Chỉ báo |
|---|---|---|---|
| MT4/MT5 `.mq4/.mq5/.mqh` | `OnTick(`, `int start()`, `OrderSend(`, `CTrade`, `trade.Buy(` | `SignalOpen(`, `: public Strategy`, `CExpertSignal`, `LongCondition(` | `#property indicator_`, `SetIndexBuffer(`, `OnCalculate(` |
| TradingView `.pine` / `//@version=` | `strategy(`, `strategy.entry(` | | `indicator(` / `study(`, `plot(` |
| Python | `IStrategy` (freqtrade), `populate_entry_trend`, `bt.Strategy`, `should_long` (jesse), `ScriptStrategyBase` / `ControllerBase` (hummingbot), `create_order(` | | hàm `rsi/ema/atr…` |
| cTrader `.cs` | `: Robot`, `ExecuteMarketOrder(` | | `: Indicator` |

Kĩ thuật xử lí lệnh nhận ra bằng từ trong mã: trailing · break-even · grid · DCA (`adjust_trade_position`, `average down`…) · martingale (`LotExponent`, `lot multiplier`) · hedge · recovery/unstuck · basket/close all · partial close · sửa SL/TP · lệnh chờ · lọc phiên / spread / tin.

**Từ khoá tìm kho** (GitHub topic và tên): `mql5`, `mql4`, `expert-advisor`, `metatrader5`, `grid-trading`, `dca`, `martingale`, `hedging`, `trading-bot`, `freqtrade-strategies`, `pinescript`, cùng các cụm "multi strategy expert advisor", "grid ea source code", "basket close recovery ea", "ctrader cbot source"… Tên file gợi ý kho: `Stg_*`, `strategies/`, `Strategy*.py`, `*_EA.mq5`, nhiều `.mq5` hoặc `.pine` trong một repo, hoặc nhiều repo con.

## 4. Quy trình: TÌM → LẤY VỀ → ĐỌC CẢ FILE → NGHIÊN CỨU, BIẾN TẤU, KẾT HỢP

```
python tru/seeker.py san-kho [--tai 5]     # tìm theo chủ đề + từ khoá + awesome-* + repo con, chấm theo cây file -> reports/SAN_KHO.json
python tru/seeker.py tai-kho owner/repo    # lấy về data/cau_kho/<owner>__<repo> (clone, kèm repo con) + kiểm kê
python tru/seeker.py kiem-ke <thư mục>     # đọc CẢ TỪNG FILE -> reports/KHO_<tên>.json: EA / chiến lược / chỉ báo, nền tảng, kĩ thuật xử lí lệnh
```
Rồi agent **đọc tay** các file EA và xử lí lệnh (như `reports/SEEKER_EA31337.md`) và ghi lại: luật vào, luật thoát, cách DCA / hedge / gỡ, tham số mặc định, lỗi. Sau đó mới đưa vào kho cơ chế (`config/co_che_dsl.json`, `config/quan_tri_dsl.json`). **Không rút cả EA còn một luật vào lệnh.**

**Luật giữ nguyên:**
- Mã của người khác chỉ nằm ở `data/` (git bỏ qua). Repo chỉ giữ tóm tắt và URL.
- Không chạy mã tải về khi chưa đọc.
- Không vượt Cloudflare hay đăng nhập thay chủ dự án.
- Đặt `GITHUB_TOKEN` trong biến môi trường máy nhà nếu có; không lưu vào git.

## 5. Kho đã biết

| Kho | Trạng thái |
|---|---|
| EA31337 (+ strategies, strategies-meta, classes) | **ĐÃ ĐỌC** 17/10 → `reports/SEEKER_EA31337.md`, `reports/KHO_EA31337.json` |
| enarjord/passivbot | chưa đọc. Ưu tiên 1: lưới DCA + **gỡ lệnh kẹt (auto unstuck)** |
| hummingbot/hummingbot | chưa đọc. DCA / grid executor, Grid Strike |
| freqtrade/freqtrade-strategies, iterativv/NostalgiaForInfinity, danh sách awesomefreqtrade | chưa đọc. Hàng trăm chiến lược, DCA qua `adjust_trade_position` |
| MQL5 Code Base (đang có `n_mql5_code`) | đang gom. Phải đọc **cả file**, giữ phần xử lí lệnh |
