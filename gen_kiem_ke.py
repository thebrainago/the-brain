# -*- coding: utf-8 -*-
import io, time, html as H

def esc(s): return H.escape(str(s))

def bang(rows, head):
    r="<table><tr>"+"".join(f"<th>{esc(h)}</th>" for h in head)+"</tr>"
    for row in rows:
        r+="<tr>"+ "".join(f"<td>{c}</td>" for c in row)+"</tr>"
    return r+"</table>"

# SEERER


if __name__ == "__main__":
    # Bo than script vao chot nay: truoc day chi can import module la
    # chay het ca bai quet/ghi bao cao, ke ca khi nguoi goi chi muon
    # dung mot ham trong file.

    seeker_xd = [
     ["quan_li_quet.py + seek_supervisor.py","Scheduler 24/7 chạy 17 source + supervisor tự khởi động lại khi crash","CHẠY"],
     ["nguon_reddit_sim.py","Reddit qua Playwright (chống bot 403) — 280 bài/176 mới","CHẠY"],
     ["nguon_dien_dan.py","Diễn đàn Quant/FF/Smart-Lab qua Playwright — 45–85 bài/nguồn","CHẠY"],
     ["nguon_code.py","GitHub code MQL5/Pine — 19 repo đã lưu","CHẠY"],
     ["telethon_ban.py","Telegram tài khoản thật: search + join group","CHẠY"],
     ["doc_cdp.py","X/TikTok/FB qua Chrome CDP 9222 (phiên đã đăng nhập) — lấy bài X thật","CHẠY"],
     ["tu_follow_join.py + fl_cheo.py","Auto-follow X + follow chéo, chống spam 8/ngày + audit","CHẠY"],
     ["seeker_quy_tac.py","5 cổng lọc + chấm điểm DARWIN → 30 ứng viên","CHẠY"],
     ["loc_chat_luong.py","Phân loại RA_TIEN/DU_BAO/NOISE + kiểm cơ sở (test chuẩn)","CHẠY"],
     ["seeker_deep.py","Deep-research 1 thực thể (Ed Seykota trend rules)","THỬ 1 CASE"],
     ["thu_vien.db","DB: muc/noi_dung/scout/task + trạng thái source","CHẠY"],
    ]
    seeker_h1 = [["Thiếu vòng lặp liên tục","follow/join + fl_cheo chưa nối vào scheduler (đang chạy tay)"],
     ["loc_chat_luong chưa vào pipeline","chỉ test, chưa tự gắn tag chất lượng khi ingest"],
     ["MQL5 Market / Myfxbook / Collective2","chưa cào được (cần login/OCR) — mới có DARWIN"],
     ["Reddit rate-limit","403 → đang đọc JSON đã cache, chưa self-heal"],
     ["Deep-research","mới 1 thực thể, chưa tự lan tỏa qua fl_cheo"]]
    seeker_im = [["Nối loc_chat_luong vào ingest","mỗi bài lưu kèm tag loại + điểm; ưu tiên RA_TIEN"],
     ["Đưa follow/join + fl_cheo vào lịch","1 budget follow/ngày (chống spam), tự discover tài khoản đa nền tảng"],
     ["Thêm MQL5 Market/Myfxbook","dùng CDP đã login + OCR kết quả"],
     ["Theo dõi source-yield","source nào sinh chiến lược thật thì tăng ưu tiên"]]

    # EVO
    evo_xd = [
     ["evo_nguon.py","Đa từ khóa + đa ngôn ngữ (EN/VN/RU/CN/ES); GitHub+X; chấm điểm; bộ lọc nguon_moi.json (24 nguồn)","CHẠY"],
     ["keywords_nguon.py","Ngân hàng keyword 26KB để đào sâu","CHẠY"],
     ["evolution.py + evo_theo_doi.py","Mở rộng keyword + theo dõi nguồn","CHẠY"],
    ]
    evo_h1 = [["X search trong evo_nguon chưa ra kết quả","lần chạy chỉ thấy GitHub, X discovery chưa verify"],
     ["Bộ lọc chưa thành vòng lặp","nguồn mới chưa tự đẩy vào collector để cào"],
     ["Điểm chỉ heuristic","chưa đo thực tế 'nguồn này sinh bao nhiêu chiến lược'"]]
    evo_im = [["Khép vòng lặp","nguồn đạt điểm → tự tạo collector/queue; đo yield → tái chấm điểm"],
     ["Thêm web search backend","Google/Bing để tìm nguồn ngoài GitHub/X"],
     ["Tự tỉa","bỏ nguồn yield thấp để tập trung"]]

    # QUANTLAB
    q_xd = [
     ["auto_kham_pha.py","105 tổ hợp × 5 tài sản, song song 19 nhân, adaptive cores","CHẠY"],
     ["kiem_dinh.py","Đủ mẫu + placebo + era + chống lookahead","CHẠY"],
     ["ket_hop_hoc.py","Kết hợp system: B+D vote EURUSD edge +25.8% (B lẻ +24.2%)","CHẠY"],
     ["4 co_che A/B/C/D + metrics + du_lieu + tin_hieu","Nền tảng backtest D1 10 năm + chi phí spread/swap","CHẠY"],
     ["mt5_chay_ichimoku.py","Port sang MT5 Ichimoku (chỉ stub JSON chưa chạy tick)","DỞ DANG"],
    ]
    q_h1 = [["0 chiến lược qua cổng","chưa có chiến lược nào sống sót → chưa tới MT5/demo"],
     ["Cổng MT5 tick chưa chạy thật","mới stub, chưa xác minh khớp lệnh/trượt giá/swap"],
     ["Walk-forward chưa có","mới era split, chưa có walk-forward tham số"],
     ["Dữ liệu chỉ D1","thiếu H4/H1/tick theo thiết kế V1/V2/V3"],
     ["Ensemble mới test EURUSD","chưa chạy đủ 5 tài sản + chưa kiểm định lại"]]
    q_im = [["Chạy cổng MT5 tick cho B_Ichimoku EURUSD + B+D","thiết kế Gate 3, xác minh edge sau chi phí thật"],
     ["Thêm H4/H1 + walk-forward","V2 theo THIET_KE_QUY_TRINH"],
     ["Test ensemble đủ 5 tài sản","chỉ giữ tổ hợp nào edge>=3/5"],
     ["Kiểm độ nhạy chi phí + tham số","chống overfit"]]

    # BANKER
    b_xd = [
     ["banker.py","FRED + COT → regime neutural, COT E-MINI spec −27k SHORT (đã sửa lỗi closure)","CHẠY"],
     ["dang_ky_alphavantage/twelvedata + lay_du_lieu","Đăng ký + lấy dữ liệu API","CHẠY"],
     ["doc_email.py","Đọc mail (OTP/login)","CHẠY"],
    ]
    b_h1 = [["Mảng HỌC (CFA/Marx) CHƯA chạy","chỉ có kế hoạch BANKER_ke_hoach.md, chưa output thật — lỗ hổng lớn nhất"],
     ["Số liệu VN (DEXVNUS) bị chặn","chưa có phương án thay"],
     ["Macro chưa nối vào giao dịch","regime chưa được Quantlab dùng để gate lệnh"],
     ["Binance/OKX/Bybit live lấy xong chưa dùng","chưa thành tín hiệu quyết định"]]
    b_im = [["Chạy module học","đọc tài liệu → ghi chú + ứng dụng trading làm output"],
     ["Phương án VN fallback","SBV/VND qua nguồn khác khi FRED chặn"],
     ["Banker → regime signal","Quantlab dùng regime để mở/khóa nhóm tài sản"]]

    # cross
    cross = [
     ["Chưa có gate runner cuối-đến-cuối","chiến lược → MT5 → demo chưa tự động"],
     ["Chưa có tài khoản demo","chặn cổng Gate 4"],
     ["Tele bridge chưa bật","thiếu bot_token/api_id/hash/chat_id"],
     ["Vòng học liên tục (Banker) chưa có","chưa tự cập nhật kiến thức"],
    ]

    def phan(ten, mota, xd, h1, im):
        return f"""<h2>{esc(ten)}</h2>
    <p class=mt>{esc(mota)}</p>
    <h3>✔ Đã xây & vận hành</h3>{bang(xd,['File / phần','Vai trò','T.trạng'])}
    <h3>⚠ Lỗ hổng / phản biện</h3><ul>{"".join('<li><b>'+esc(a)+'</b>: '+esc(b)+'</li>' for a,b in h1)}</ul>
    <h3>🛠 Giải pháp cải tiến</h3><ul>{"".join('<li><b>'+esc(a)+'</b>: '+esc(b)+'</li>' for a,b in im)}</ul>"""

    html = f"""<!DOCTYPE html><html lang=vi><head><meta charset=utf-8>
    <title>Kiểm kê + phản biện hệ thống</title><style>
    body{{font-family:Segoe UI,system-ui;background:#0d1117;color:#e6edf3;margin:0;padding:22px;line-height:1.5}}
    h1{{color:#58a6ff;border-bottom:2px solid #30363d;padding-bottom:8px}}
    h2{{color:#79c0ff;margin-top:30px;border-left:4px solid #58a6ff;padding-left:10px}}
    h3{{color:#ffa657;margin:14px 0 6px}}
    p.mt{{color:#8b949e}}
    table{{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0}}
    th,td{{border:1px solid #30363d;padding:5px 8px;text-align:left;vertical-align:top}}
    th{{background:#161b22;color:#79c0ff}}
    tr:nth-child(even) td{{background:#12161c}}
    ul{{margin:4px 0;padding-left:20px}}
    .foot{{color:#8b949e;font-size:12px;margin-top:26px}}
    .big{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px 16px;margin:8px 0}}
    </style></head><body>
    <h1>Kiểm kê thực tế + phản biện hệ thống (The Brain)</h1>
    <p class=foot>Cập nhật {time.strftime('%Y-%m-%d %H:%M')} · Chỉ liệt kê CODE/FILE vận hành được, không lý thuyết.</p>

    <div class=big><b>Tổng quan:</b> ~60 file .py · DB SQLite (thu_vien.db) · dữ liệu Yahoo 5 tài sản · 17 source đang quét · Seeker chạy 24/7 qua supervisor.</div>
    {phan('1. SEEKER — thu thập + lọc', 'Tìm chiến lược/PP/chỉ báo ra tiền; chống bot; lọc chất lượng.', seeker_xd, seeker_h1, seeker_im)}
    {phan('2. EVO — tìm thêm nguồn', 'Đa từ khóa, đa ngôn ngữ, chấm điểm, bổ sung bộ lọc.', evo_xd, evo_h1, evo_im)}
    {phan('3. QUANTLAB — backtest & kiểm định', 'Sàng nhanh + kiểm định nghiêm ngặt + kết hợp system.', q_xd, q_h1, q_im)}
    {phan('4. BANKER — vĩ mô & học', 'FRED/COT regime + học tài liệu.', b_xd, b_h1, b_im)}

    <h2>5. Lỗ hổng chéo (toàn hệ)</h2>
    <ul>{"".join('<li><b>'+esc(a)+'</b>: '+esc(b)+'</li>' for a,b in cross)}</ul>

    <h2>Kết luận & ưu tiên</h2>
    <div class=big>
    <ol>
    <li><b>Cần gấp nhất:</b> chạy cổng <b>MT5 tick</b> cho B_Ichimoku EURUSD + B+D (đang là điểm mù giữa Python và tài khoản thật).</li>
    <li><b>Lấp ngay:</b> chạy module <b>học của BANKER</b> (lỗ hổng lớn nhất — kế hoạch đã có, chưa có output).</li>
    <li><b>Khép vòng lặp:</b> nối follow/join + fl_cheo + loc_chat_luong vào scheduler; EVO feed nguồn mới vào collector.</li>
    <li><b>Cần bạn:</b> config Telegram (bot_token/api_id/hash/chat_id) để bật bridge; đăng nhập LinkedIn đã xong.</li>
    <li><b>VPS:</b> toàn bộ lab/ gói gọn chuyển lên kèm lịch sử chat + supervisor + bridge.</li>
    </ol>
    </div>
    <p class=foot>Báo cáo sinh tự động từ kiểm kê file thực tế trong lab/.</p>
    </body></html>"""
    p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\reports\KIEM_KE_PHAN_BIEN.html"
    io.open(p, "w", encoding="utf-8").write(html)
    print("DA GHI:", p, "|", len(html), "bytes")
