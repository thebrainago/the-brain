# -*- coding: utf-8 -*-
"""?iet bao cao HTML chi tiet ve SEEKER (nguon, lich quet, pipeline)."""
import sys, io, time, html
from pathlib import Path
LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.path.insert(0, str(LAB))

import quan_li_quet as q   # LICH
import seeker_quy_tac as sk  # NGUON_CATALOG, RULES

def esc(s): return html.escape(str(s))

LUCCI = {2:"2 giờ",4:"4 giờ",6:"6 giờ",8:"8 giờ",12:"12 giờ"}
Nhom = {"hoc_thuat":"Học thuật","cong_dong":"Cộng đồng","hieu_suat":"Hiệu suất thực"}

# --- bang nguon catalog ---
rows_cat = ""
for loai, ten, url, lay, ut in sk.NGUON_CATALOG:
    rows_cat += f"<tr><td>{Nhom.get(loai,loai)}</td><td>{esc(ten)}</td><td class=mono>{esc(url)}</td><td>{esc(lay)}</td><td class=pri>{ut}</td></tr>"

# --- bang lich quet ---
trang_thai = {"reddit":"Playwright ✓","dien_dan":"Playwright ✓","code":"GitHub ✓","darwinex":"API ✓","github":"API ✓","mql5":"API ✓"}
rows_lich = ""
mo_ta = {
 "github":"cào repo trading/chiến lược","mql5":"cào MQL5 Market/Signals → scout",
 "cong_dong":"tìm cộng đồng/trader","wccta":"WCC Alpha (en)","kham_pha":"tự khám phá nguồn mới",
 "telethon":"Telegram tài khoản thật (search+join)","quy":"kênh quỹ Telegram","social":"X/TikTok/FB qua Chrome đã login",
 "youtube":"YouTube kinh nghiệm/chiến lược","telegram":"kênh Telegram công khai","banker":"FRED + COT macro",
 "evolution":"EVO mở rộng keyword bank","reddit":"reddit qua Playwright","darwinex":"1000 DARWIN track record",
 "dien_dan":"diễn đàn (quant, FF, Smart-Lab, Traderviet)","code":"GitHub MQL5/Pine code"}
for ten, it in q.LICH.items():
    tg = f"{it['moi_gio']} giờ" if it['moi_gio'] in LUCCI else f"{it['moi_gio']}h"
    tt = trang_thai.get(ten, "")
    rows_lich += f"<tr><td class=mono>{ten}</td><td>{esc(mo_ta.get(ten,''))}</td><td>{tg}</td><td>{tt}</td></tr>"

# --- 5 rules ---
rules_txt = "".join(f"<li><b>{r.__name__.replace('r_','').replace('_',' ')}</b>: {esc(r.__doc__ or '').strip()}</li>" for r in sk.RULES)

BAO_CAO = f"""<!DOCTYPE html><html lang=vi><head><meta charset=utf-8>
<title>Seeker — Báo cáo nguồn • lịch quét • pipeline</title>
<style>
 body{{font-family:Segoe UI,system-ui,sans-serif;background:#0d1117;color:#e6edf3;margin:0;padding:24px;line-height:1.5}}
 h1{{color:#58a6ff;border-bottom:2px solid #30363d;padding-bottom:8px}}
 h2{{color:#79c0ff;margin-top:34px}}
 .mono{{font-family:Consolas,monospace;font-size:12.5px}}
 table{{border-collapse:collapse;width:100%;margin:10px 0;font-size:13.5px}}
 th,td{{border:1px solid #30363d;padding:6px 9px;text-align:left;vertical-align:top}}
 th{{background:#161b22;color:#79c0ff}}
 tr:nth-child(even) td{{background:#12161c}}
 .pri{{text-align:center;font-weight:700;color:#ffa657}}
 .badge{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11.5px;font-weight:700}}
 .b-on{{background:#238636;color:#fff}} .b-wait{{background:#9e6a03;color:#fff}}
 .card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px 18px;margin:12px 0}}
 .step{{background:#0d1117;border:1px dashed #30363d;border-radius:6px;padding:10px 14px;margin:8px 0}}
 .k{{color:#3fb950;font-weight:700}} .tt{{color:#ffa657}} .x{{color:#f85149}}
 ul{{margin:6px 0;padding-left:20px}}
 .foot{{color:#8b949e;font-size:12px;margin-top:28px}}
</style></head><body>
<h1>SEEKER — Báo cáo hệ thống</h1>
<p class=foot>Cập nhật: {time.strftime('%Y-%m-%d %H:%M')}</p>

<h2>1. Tổng quan quy trình (pipeline)</h2>
<div class=card>
 <div class=step><b>① Thu thập</b> — lịch quét 24/7 ({len(q.LICH)} nguồn) cào nguồn từng giờ → lưu bảng <span class=mono>muc</span> + nội dung <span class=mono>noi_dung</span>.</div>
 <div class=step><b>② Sinh task scout</b> — mỗi mục mới tạo task <span class=mono>scout</span> (huong=seeker) cho bộ não xử lý.</div>
 <div class=step><b>③ Evolution (EVO)</b> — trích keyword/khái niệm/ten mới từ nội dung → bổ sung vào keyword bank (self-growing).</div>
 <div class=step><b>④ Seeker — lọc theo quy tắc</b> — áp 5 cổng ngặt + chấm điểm → danh sách ứng viên có cấu trúc (JSON).</div>
 <div class=step><b>⑤ Deep-research</b> — với 1 tên/quỹ đã biết: tìm tài liệu đa ngôn ngữ → cào → rút chiến lược có cấu trúc.</div>
 <div class=step><b>⑥ EVO gộp 3 trụ</b> — Seeker + Quantlab + Banker chạy <span class=k>SÔNG SONG</span> → 1 state + 1 báo cáo.</div>
 <div class=step><b>⑦ Backtest nhanh</b> — Python D1, chống lookahead (shift+1), chi phí spread/swap, so buy&amp;hold, placebo + era, <span class=tt>adaptive cores</span>.</div>
 <div class=step><b>⑧ Cổng ra nghiêm ngặt</b> — cấu hình sống sót mới lên <span class=mono>MT5 tick</span> xác nhận (không tin Python đơn thuần).</div>
</div>

<h2>2. Nguồn (catalog)</h2>
<p>Ưu tiên: <span class=tt>5</span> = cao nhất (track record thật), <span class=tt>3</span> = tham khảo.</p>
<table><tr><th>Nhóm</th><th>Nguồn</th><th>URL</th><th>Lấy gì</th><th>Ưu tiên</th></tr>
{rows_cat}</table>

<h2>3. Lịch quét (tần suất từng nguồn)</h2>
<table><tr><th>Collector</th><th>Mô tả</th><th>Tần suất</th><th>Trạng thái</th></tr>
{rows_lich}</table>
<p class=foot>Chạy liên tục bởi <span class=mono>quan_li_quet.py</span> dưới supervisor tự khởi động lại khi crash. Playwright ✓ = đã có đường cào qua trình duyệt thật.</p>

<h2>4. 5 cổng lọc (Seeker rules)</h2>
<ul>{rules_txt}
<li><b>chấm điểm</b>: lãi + dscore + số nhà đầu tư + quy mô vốn − phạt drawdown sâu → xếp hạng.</li>
</ul>

<h2>5. Kiểm định & hiệu năng</h2>
<div class=card>
 <ul>
  <li><span class=k>Chống lookahead</span>: mọi tín hiệu <span class=mono>shift(1)</span> (quyết định ở t, lãi từ t+1).</li>
  <li><span class=k>Chi phí thực</span>: spread round-trip + swap/đêm theo từng tài sản.</li>
  <li><span class=k>So buy&amp;hold</span>: lãi chiến lược ≥ mốc buy&amp;hold cùng kỳ mới tính.</li>
  <li><span class=k>Đủ mẫu</span>: cần ≥ 30 lệnh (1–6 lệnh là vô nghĩa thống kê).</li>
  <li><span class=k>Placebo</span>: so với phân phối lãi ngẫu nhiên (shuffle) → p &lt; 0.05.</li>
  <li><span class=k>Era split</span>: edge phải dương ở cả 2 mien thời gian (out-of-sample).</li>
  <li><span class=k>Adaptive cores</span>: backtest song song theo <span class=mono>cpu_count−1</span> (máy này 19; VPS 4 luồng → 3).</li>
  <li><span class=tt>Cảnh báo</span>: hầu hết naive signal KHÔNG qua hết cổng — đúng kỳ vọng, chống overfit.</li>
 </ul>
</div>

<p class=foot>Báo cáo sinh tự động từ code (quan_li_quet.py + seeker_quy_tac.py). Xem thêm: BO_NHO.md, BAN_GIAO.json, reports/quet.log.</p>
</body></html>"""

out = LAB / "reports" / "BAO_CAO_SEEKER.html"
out.write_text(BAO_CAO, encoding="utf-8")
print("DA GHI:", out, "|", out.stat().st_size, "bytes")
