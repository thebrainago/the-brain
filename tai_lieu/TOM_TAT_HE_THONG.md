# QUANTLAB / THE BRAIN — hệ thống đã làm được gì

> Bản tóm tắt cho người đọc ngoài dự án. Chốt ngày 03/09/2026 sau một phiên
> làm việc hơn 10 tiếng trên một mục tiêu cụ thể: *"tối ưu nhịp tăng và đòn
> bẩy trên US500CASH, hướng tới 20-30%/năm"*.

---

## 1. Hệ thống này là gì

Một dây chuyền nghiên cứu định lượng tự động, chạy tại chỗ (Windows + Python +
MetaTrader 5), gồm 5 trụ và một hạt nhân dùng chung:

```
Research SP500/
  lab/nhan/     hạt nhân: dữ liệu, chi phí, mô phỏng, cổng thống kê, ngữ pháp cơ chế
  lab/tru/      5 trụ: seeker (săn nguồn), quantlab (kiểm định),
                nghi (đề xuất), banker (vĩ mô), evolution (tự khám bệnh)
  lab/nao.db    một sổ cái duy nhất: tài liệu, cơ chế, giả thuyết, sổ FDR
  data/         252 bảng giá parquet (ngoài git)
```

**1.021 test tự động**, tất cả đang xanh.

## 2. Quy trình chuẩn: một mục tiêu → ba luồng song song

```
Chủ dự án đưa MỘT mục tiêu (ví dụ: US500CASH, 20-30%/năm)
  │
  ├── LUỒNG 1  SĂN      seeker + muc_tieu.py
  │   Săn theo TÀI SẢN và theo TÊN HỆ THỐNG, qua ~20 nguồn
  │   (MQL5 Code Base, TradingView Pine, GitHub, arXiv, OpenAlex,
  │    Crossref, StackExchange, HackerNews, Reddit, blog RSS…)
  │
  ├── LUỒNG 2  NGOẠI SINH   boc_llm.py + ngoai_sinh.py
  │   Đọc song song → bóc luật thành khai báo DSL → và chuyển
  │   những hệ ĐÃ PASS sang tài sản mới
  │
  └── LUỒNG 3  NỘI SINH     noi_sinh.py
      QUANTLAB tự nghĩ cơ chế bằng cách rò ngược lịch sử của chính mã đó
```

Một lệnh chạy cả dây chuyền: `b day-chuyen US500CASH`

## 3. Nguyên tắc thiết kế cốt lõi

Đây là phần khác biệt nhất so với một bộ backtest thông thường.

**Kiến thức mới chỉ vào hệ qua một NGỮ PHÁP khai báo** (`nhan/ngu_phap.py`).
LLM đọc tài liệu và trả về JSON theo ngữ pháp đó; hệ **không bao giờ `exec`**
mã do LLM sinh. Mọi khai báo phải qua cổng cú pháp + kiểm không-nhìn-trước
trước khi vào kho.

**Chi phí phải ĐO ĐƯỢC.** `cp.do_tin == "KHAI"` thì không bao giờ được PASS.
Spread đọc từ cột `spread` của bar MT5 thật; phí qua đêm quy đổi theo đúng
`swap_mode` của từng sàn.

**Sổ FDR tích luỹ.** Mỗi giả thuyết tiêu một suất; ngưỡng LORD siết dần. Có
`plan_hash` trước khi chạm holdout — đổi kế hoạch sau khi nhìn dữ liệu là một
giả thuyết KHÁC.

**Hiệu chuẩn cổng hai chiều.** Một cổng từ chối TẤT CẢ cho số liệu y hệt một
cổng tốt, nên mỗi cổng đều có bài kiểm "sức mạnh" đi kèm.

**So sánh ở CÙNG MỨC RỦI RO.** Một hệ chọn lọc chỉ ở trong thị trường 17% thời
gian không thể so tổng lãi với mua-giữ ở 100%.

## 4. Kết quả nghiên cứu đáng kể

**Đã bác bỏ (có số liệu):**
- 324 phép thử trước đó + 190 cấu hình cơ chế quét ngày 03/09: **0 cái thắng
  mua-giữ trên holdout** ở cùng mức rủi ro.
- Nội sinh: 3.114 cơ chế sinh từ chính lịch sử US500CASH → 341 vượt mốc trên
  train, **0/12 sống sót holdout**, và khi khớp rủi ro thì **0/11**.
- "Chỉ số êm ả" là bẫy: 3 chỉ số biến động thấp nhất thì **2 cái ÂM sau phí**.
  UK100 mua-giữ **−2,77%/năm** suốt 15 năm.

**Đã tìm được:**
- **Sonic R trên H4 của US500CASH**, TP 5% / SL 1%: 9,13%/năm ở đòn bẩy 1
  (maxDD −19%), **26,01%/năm ở đòn bẩy 3** (maxDD −47,8%). 182 lệnh, PF 1,60.
  Holdout **tốt lên** (Calmar 0,47 → 1,50), lân cận tham số **15/15 ô dương**.
  Chưa qua placebo, chưa đăng ký giả thuyết.
- **Bộ lọc xu hướng là BẢO HIỂM chứ không phải alpha**: trên 98 năm SP500,
  `close > SMA200` hơn mua-giữ **+19,5 điểm%/năm trong 1929-1932**, +16,3 trong
  2000-2002, +21,9 trong 2008-2009 — nhưng **thua** trong mọi giai đoạn bò.
  Cộng dồn 99 năm: +1,33 điểm%/năm, và nó **nâng Sharpe 0,284 → 0,461**, tức
  nâng trần đòn bẩy từ ~4% lên ~10,6%/năm.
- **Đẳng thức trần**: `CAGR tối đa ở BẤT KỲ đòn bẩy nào = 0,5 × Sharpe²`.
  Đòn bẩy không nâng trần, nó chỉ trượt dọc đường cong. Muốn 25%/năm cần
  Sharpe ≥ 0,71 (Kelly toàn phần) hoặc ≥ 0,82 (nửa Kelly).

## 5. Điều học được lớn nhất

Trong 10 tiếng của một phiên, hệ thống lộ ra **15 lỗi**, và **tất cả cùng một
họ bệnh: một thất bại được báo cáo như một kết quả bình thường.**

| lỗi | biểu hiện | hậu quả đo được |
|---|---|---|
| `don_bay` gộp bằng log | CAGR "bình thường" | phóng đại **31.700 lần** ở L=3 |
| closure DSL nuốt tham số (`**_`) | báo "CAO NGUYÊN 100% dương" | 152/170 mẫu chưa từng đổi tham số |
| cơ chế theo giờ trên khung ngày | thành hằng số 1,0 | vào **hạng 2** bảng xếp hạng, tên là cơ chế phiên |
| lời nhắc bóc kèm "đừng đề xuất biến thể" | "0 cơ chế" | LLM im lặng, suất **0/100 bản** |
| bộ lọc luật viết cho văn xuôi | "không có tài liệu phù hợp" | 300 file mã bị chấm **0 điểm** |
| `Accept-Encoding: br` không giải nén được | **HTTP 200** | 82.347 ký tự → 21.245 ký tự **rác** |
| DNS bị đầu độc | 3 triệu chứng khác nhau | bị đoán thành 3 nguyên nhân riêng |
| tải hỏng bị dịch thành "hết trang" | "nguồn đã cạn" | con trỏ MQL5 bị cắt vĩnh viễn ở trang 3 |
| `thu_thap` không phân trang | "tải 60 file" | 4 vòng tải lại đúng 60 file cũ |
| lớp "duyệt như người" | 403 | chính nó bị chặn; `requests` trần thì 4/4 = 200 |

**Nguyên tắc rút ra:** khi một bộ phận báo con số bình thường mà sản lượng
bằng 0, đừng tin con số — hãy đo từng chặng. Và mọi cổng chặn đều phải có bài
kiểm ngược: *nếu nó không bao giờ nói "không" thì nó cũng chẳng nói "có".*

## 6. Năng lực hạ tầng (đo được ngày 03/09)

| chặng | trước | sau |
|---|---|---|
| săn theo mục tiêu | không tồn tại | 229 tài liệu / 101 giây |
| đọc toàn văn | 8,75 s/bản (tuần tự) | **0,31 s/bản** (song song, 28×) |
| bóc cơ chế | **0** cơ chế / 10 bài | **19-37 cơ chế / 100 bản** |
| backtest | — | 0,72 ms cho 4.027 bar |
| MQL5 Code Base | bị chặn hoàn toàn | **358 file `.mq5` tải về, 290 mới** |

Kho hiện tại: **6.226 tài liệu**, **377 file mã nguồn thật**, **191 cơ chế**
chạy được, **252 bảng giá**.

## 7. Việc còn dở, nói thẳng

- **Tỷ lệ chuyển đổi tài liệu → cơ chế mới đạt ~3%**, mục tiêu chủ dự án đặt
  ra là ≥100%. Nút thắt hiện tại là hạn mức API của bộ bóc, không còn là tốc
  độ hay nguồn.
- 281 file `.mq5` vừa cào về **chưa được bóc** (mắt xích `artifact → bộ bóc`
  vừa nối xong lúc chốt phiên).
- Sonic R chưa chạy placebo, chưa qua cổng FDR, chưa lên MT5 Strategy Tester.
- Một ẩn số chưa chốt: sàn có trả điều chỉnh cổ tức riêng không — đáng
  1,87%/năm × đòn bẩy.

---

*Sinh từ phiên làm việc 03/09/2026. Toàn bộ số liệu trong tài liệu này đều đo
được và tái lập được từ mã nguồn trong kho.*
