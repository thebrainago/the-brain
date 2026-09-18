# -*- coding: utf-8 -*-
"""Sinh so do SVG cho THE BRAIN - danh cho nguoi dung mo truc tiep bang trinh duyet."""
import html
import math
from pathlib import Path

HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# mau sac
# ---------------------------------------------------------------------------
THEMES = {
    "nguon":     dict(head="#1e40af", head_fg="#ffffff", bg="#eff6ff", border="#93c5fd"),
    "khampha":   dict(head="#b45309", head_fg="#ffffff", bg="#fffbeb", border="#fcd34d"),
    "khangdinh": dict(head="#4338ca", head_fg="#ffffff", bg="#eef2ff", border="#a5b4fc"),
    "dangky":    dict(head="#be185d", head_fg="#ffffff", bg="#fdf2f8", border="#f9a8d4"),
    "cong":      dict(head="#166534", head_fg="#ffffff", bg="#f0fdf4", border="#86efac"),
    "ketluan":   dict(head="#991b1b", head_fg="#ffffff", bg="#fef2f2", border="#fca5a5"),
    "rail":      dict(head="#334155", head_fg="#ffffff", bg="#f8fafc", border="#cbd5e1"),
    "dark":      dict(head="#0f172a", head_fg="#e2e8f0", bg="#1e293b", border="#475569"),
    "warn":      dict(head="#92400e", head_fg="#ffffff", bg="#fffbeb", border="#f59e0b"),
}


def esc(s):
    return html.escape(s, quote=False)


class Doc:
    """Sinh SVG don gian: box, chu, mui ten."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = []
        self.p.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="Segoe UI, Arial, sans-serif">'
        )
        self.p.append(
            '<defs>'
            '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/></marker>'
            '<marker id="arD" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8"/></marker>'
            '</defs>'
        )

    def _w(self, s, size):
        """Uoc luong be rong chu."""
        n_vn = sum(1 for c in s if ord(c) > 0x2E)
        n = len(s)
        return (0.50 * n + 0.16 * n_vn) * size

    def wrap(self, s, size, max_px):
        words = s.split(" ")
        lines, cur = [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if self._w(t, size) <= max_px:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def rect(self, x, y, w, h, fill, stroke, rx=10, sw=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def txt(self, x, y, s, size, fill, anchor="middle", weight="normal", italic=False):
        it = " font-style='italic'" if italic else ""
        self.p.append(
            f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{it}>{esc(s)}</text>'
        )

    def txt_wrap(self, x, y, s, size, fill, anchor, weight, max_px, lh, italic=False):
        for i, line in enumerate(self.wrap(s, size, max_px)):
            self.txt(x, y + i * lh, line, size, fill, anchor, weight, italic)
        return len(self.wrap(s, size, max_px))

    def box(self, x, y, w, title, items, theme, title_size=15, align="middle",
            title_icon="", max_px=None, body_size=13, lh=20):
        """items: list (kind, text) - kind: body/bold/small/tiny/sep"""
        t = THEMES[theme]
        head = 34 if title else 0
        pad = 12
        inner = (w - 2 * pad) if max_px is None else max_px
        # tinh chieu cao
        heights = {"body": lh, "bold": lh, "small": lh - 3, "tiny": lh - 5}
        n_lines = 0
        for kind, s in items:
            if kind == "sep":
                n_lines += 1
            else:
                n_lines += len(self.wrap(s, body_size if kind in ("body", "bold") else (lh - 3 if kind == "small" else lh - 5), inner))
        h = 12 + head + n_lines * (lh - 3) + 8
        # than
        self.rect(x, y + head, w, h - head, t["bg"], t["border"], rx=10, sw=1.3)
        if title:
            self.rect(x, y, w, head, t["head"], t["head"], rx=10, sw=0)
            self.rect(x, y + head - 4, w, 4, t["head"], t["head"], rx=0, sw=0)
            self.txt(x + w / 2, y + head / 2 + 5, (title_icon + " " + title).strip(),
                     title_size, t["head_fg"], "middle", "bold")
        # noi dung
        yy = y + head + 10
        for kind, s in items:
            if kind == "sep":
                self.rect(x + pad, yy + 2, w - 2 * pad, 1.2, "#cbd5e1", "#cbd5e1", rx=0, sw=0)
                yy += 8
                continue
            size = body_size if kind in ("body", "bold") else (lh - 3 if kind == "small" else lh - 5)
            fill = "#0f172a" if kind in ("body", "bold") else "#475569"
            weight = "bold" if kind in ("bold",) else "normal"
            if align == "middle":
                nl = self.txt_wrap(x + w / 2, yy + size, s, size, fill, "middle", weight, inner, lh - 3)
            else:
                nl = self.txt_wrap(x + pad, yy + size, s, size, fill, "start", weight, inner, lh - 3)
            yy += nl * (lh - 3) + 3
        return x, y, w, h

    def arrow(self, x1, y1, x2, y2, color="#475569", dashed=False, sw=2.2, label=None, lx=0, ly=0):
        d = f' stroke-dasharray="8,5"' if dashed else ""
        mk = "url(#arD)" if dashed else "url(#ar)"
        self.p.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{sw}"{d} marker-end="{mk}"/>'
        )
        if label:
            self.txt(x2 + lx, y2 + ly, label, 11.5, "#64748b", "start", "normal")

    def save(self, name):
        self.p.append("</svg>")
        (HERE / name).write_text("\n".join(self.p), encoding="utf-8")
        print("da ghi", name, f"({self.w}x{self.h})")


# ===========================================================================
# SO DO 1: TONG QUAN DAY CHUYEN
# ===========================================================================
def so_do_tong_quan():
    d = Doc(1240, 1680)
    # tieu de
    d.txt(620, 44, "THE BRAIN — SƠ ĐỒ QUY TRÌNH DÂY CHUYỀN NGHIÊN CỨU", 30, "#0f172a", "middle", "bold")
    d.txt(620, 74, "Chốt 09/08/2026 sau 5 vòng phản biện Claude × DeepSeek · chạy 24/7 trên VPS 2 vCPU/1–2 GB",
          15, "#475569", "middle")
    # chu giai
    legend = [("nguon", "Tầng 0 · Nguồn"), ("khampha", "Tầng 1 · Khám phá"), ("khangdinh", "Tầng 2 · Sổ khẳng định"),
              ("dangky", "Tầng 3 · Sổ đăng ký"), ("cong", "Tầng 4 · Cổng xác nhận"), ("ketluan", "Tầng 5 · Kết luận")]
    lx = 120
    for theme, lab in legend:
        t = THEMES[theme]
        d.rect(lx, 96, 18, 18, t["bg"], t["head"], rx=4)
        d.txt(lx + 24, 109, lab, 12, "#334155", "start")
        lx += d._w(lab, 12) + 24 + 34

    # --- cot giua: day chuyen ---
    cx, cw = 620, 500
    x0 = cx - cw / 2

    b = d.box(x0, 150, cw, "TẦNG 0 — NGUỒN: THU THẬP TỰ ĐỘNG", [
        ("bold", "DỮ LIỆU: Yahoo Finance 31 thị trường (chỉ số · FX · hàng hóa) · MT5"),
        ("bold", "Ý TƯỞNG: arXiv · GitHub (freqtrade…) · YouTube phụ đề · IMAP · track record · nạp tay"),
        ("bold", "CÔNG NGHỆ: HuggingFace models/datasets/papers · GitHub trending → BRAIN_cong_nghe (101)"),
        ("small", "Kho: THƯ VIỆN (23 hàm/công thức) · dữ liệu cập nhật 08:21 mỗi sáng"),
    ], "nguon", body_size=13)
    _, b0y, _, b0h = b
    y1 = b0y + b0h

    b = d.box(x0, y1 + 28, cw, "TẦNG 1 — KHÁM PHÁ · TẬP SÀNG (KHÔNG PHẢI EDGE)", [
        ("bold", "28 thị trường → 7 nhóm tương quan (châu Âu · châu Á · châu Mỹ · kim loại · năng lượng · nông sản · FX)"),
        ("body", "DeepSeek thợ viết ĐÚNG 1 hàm do(); Claude giám sát · brain_co_che.py: 3 hạt, p theo nhóm, trung vị"),
        ("body", "Chặn lỗi thợ: nhìn trước · thiếu null · gọi mạng/xoá file · cum kết quả"),
        ("small", "Kết quả: BRAIN_TU_SINH (51 phép thử) · BRAIN_CO_CHE · BRAIN_sang — không tốn slot FDR"),
    ], "khampha", body_size=13)
    _, b1y, _, b1h = b
    y2 = b1y + b1h

    b = d.box(x0, y2 + 28, cw, "TẦNG 2 — SỔ KHẲNG ĐỊNH (brain_khang_dinh.py)", [
        ("body", "Khẳng định nguyên tử KD_* — 11 sổ: 1 CHƯA_TEST · 3 ĐANG_SÀNG · 7 ĐÃ_ĐÓNG_SỔ"),
        ("body", "“Không có điều kiện bác bỏ → không phải khẳng định, chỉ là nhận xét”"),
        ("small", "Tra sổ TRƯỚC khi test: biến thể là số vô nghĩa — khẳng định nguyên tử mới là thứ trả tiền"),
    ], "khangdinh", body_size=13)
    _, b2y, _, b2h = b
    y3 = b2y + b2h

    b = d.box(x0, y3 + 28, cw, "TẦNG 3 — SỔ ĐĂNG KÝ (324 giả thuyết)", [
        ("bold", "CHỈ NGƯỜI ký mới vào sổ — máy 24/7 không bao giờ tự thêm"),
        ("body", "Ngân sách FDR toàn cục q = 10% · siết dần theo số phép thử tích lũy"),
        ("small", "plan_hash bắt buộc ở tầng dữ liệu · pre-registration · sổ chỉ-thêm, chống chạy chui"),
    ], "dangky", body_size=13)
    _, b3y, _, b3h = b
    y4 = b3y + b3h

    b = d.box(x0, y4 + 28, cw, "TẦNG 4 — CỔNG XÁC NHẬN (tập xác nhận chưa từng nhìn)", [
        ("bold", "sp500 · dowjones · nasdaq · russell2000 · us500cash · us500m"),
        ("body", "PASS = 6 điều kiện đồng thời: 1) net > buyhold  2) sharpe > buyhold  3) calmar > buyhold"),
        ("body", "4) alpha Newey-West p ≤ ngưỡng  5) placebo p xấu nhất (≥5 hạt)  6) pre_registered = true"),
        ("small", "Siết thêm khi exposure > 95%: p ≤ 0,01 + ≥1 giai đoạn con dương · SPA cho chọn-trong-mẻ · Null factory cho chọn-theo-thời-gian"),
        ("small", "Mốc = buyhold CFD · cost model ĐỐI XỨNG 2 vế (Vòng 6: phí bất đối xứng = 63% “edge” giả)"),
    ], "cong", body_size=13)
    _, b4y, _, b4h = b
    y5 = b4y + b4h

    b = d.box(x0, y5 + 28, cw, "TẦNG 5 — KẾT LUẬN", [
        ("bold", "SONG SÓT (PASS): hạn 3/6/12 tháng (hạng C/B/A) · tái kiểm quý bằng lịch Lan-DeMets — không cộng FDR"),
        ("body", "EXPLORATORY: kho chờ người duyệt · âm tính: CLOSED_UNLESS_TRIGGERED kèm điều kiện để sai"),
        ("small", "Hiện tại: 0 song sót / 324 phép thử — âm tính hợp lệ, không được tinh chỉnh tham số"),
    ], "ketluan", body_size=13)
    _, b5y, _, b5h = b
    y6 = b5y + b5h

    # --- cot trai: van hanh 24/7 ---
    lx0, lw = 20, 340
    d.txt(lx0 + 8, 140, "VẬN HÀNH 24/7", 16, "#0f172a", "start", "bold")
    d.rect(lx0, 148, lw, 2, "#94a3b8", "#94a3b8", rx=1, sw=0)

    l1 = d.box(lx0, 165, lw, "NHỊP TIM & HÀNG ĐỢI", [
        ("small", "BRAIN_nhip_tim.json mỗi 5 giây · trạng thái nghỉ/đang chạy"),
        ("small", "Hàng đợi BRAIN_hang_doi: 14 chờ · 11 xong"),
    ], "rail", align="start", body_size=12, lh=18)
    _, l1y, _, l1h = l1

    l2 = d.box(lx0, l1y + l1h + 14, lw, "CHẠY HẰNG NGÀY", [
        ("small", "cập nhật dữ liệu → thu thập nguồn → chạy cửa ải → cập nhật báo cáo"),
        ("bold", "KHÔNG bao giờ tự tinh chỉnh tham số"),
    ], "rail", align="start", body_size=12, lh=18)
    _, l2y, _, l2h = l2

    l3 = d.box(lx0, l2y + l2h + 14, lw, "THỢ DEEPSEEK — TỰ SINH (ds_tho.py)", [
        ("small", "DeepSeek viết ĐÚNG 1 hàm do(); Claude giám sát, soi từng lỗi"),
        ("small", "quét an toàn: nhìn trước · thiếu null · gọi mạng/xoá file · cum kết quả"),
    ], "rail", align="start", body_size=12, lh=18)
    _, l3y, _, l3h = l3

    l4 = d.box(lx0, l3y + l3h + 14, lw, "ĐẾM PHÉP THỬ & FDR", [
        ("small", "+51 phép thử khám phá hôm nay (BRAIN_dem_phep_thu)"),
        ("small", "FDR toàn cục siết dần theo số phép thử tích lũy"),
    ], "rail", align="start", body_size=12, lh=18)
    _, l4y, _, l4h = l4

    l5 = d.box(lx0, l4y + l4h + 14, lw, "BÁO CÁO TỰ ĐỘNG", [
        ("small", "THE_BRAIN.md · BRAIN_BAO_CAO.md · BRAIN_nhat_ky.md"),
        ("small", "Báo cáo tuần: “N dòng bị sửa hồi tố” — chỉ dismiss sau khi xem"),
    ], "rail", align="start", body_size=12, lh=18)
    _, l5y, _, l5h = l5

    l6 = d.box(lx0, l5y + l5h + 14, lw, "QUY TẮC DỪNG", [
        ("small", "0,0017 × V > C → TIẾP TỤC · ngược lại DỪNG"),
        ("small", "3 chẩn đoán: không edge (dừng hẳn) · thiếu lực (tăng mẫu) · nhìn sai chỗ (đổi bề mặt)"),
        ("small", "Dừng theo BỀ MẶT tìm kiếm, không phải “thị trường không có edge”"),
    ], "rail", align="start", body_size=12, lh=18)
    _, l6y, _, l6h = l6

    l7 = d.box(lx0, l6y + l6h + 14, lw, "3 CON SỐ → MỌI NGƯỠNG", [
        ("small", "1) Edge tốt sau chi phí đáng bao nhiêu/năm?"),
        ("small", "2) Chiến lược vô dụng lọt qua gây thiệt hại bao nhiêu/năm?"),
        ("small", "3) Xác suất ý tưởng ngẫu nhiên là tốt?"),
        ("small", "Tuition budget: thăm dò = tiền học phí, đánh giá bằng cập nhật niềm tin"),
    ], "rail", align="start", body_size=12, lh=18)
    _, l7y, _, l7h = l7

    l8 = d.box(lx0, l7y + l7h + 14, lw, "NGƯỜI DUYỆT — GIỮ NGƯỜI TRONG VÒNG LẶP", [
        ("small", "Chỉ trình thứ đã qua cổng + có cơ chế · màn hình 60 giây: cơ chế · net vs mua-giữ · alpha t · placebo p · đồ thị vốn"),
        ("small", "Không phản hồi = PENDING · không bao giờ tự động duyệt · gom cụm cùng cơ chế"),
    ], "rail", align="start", body_size=12, lh=18)
    _, l8y, _, l8h = l8

    # --- cot phai: suc khoe day chuyen ---
    rx0, rw = 880, 340
    d.txt(rx0 + 8, 140, "SỨC KHOẺ DÂY CHUYỀN", 16, "#0f172a", "start", "bold")
    d.rect(rx0, 148, rw, 2, "#94a3b8", "#94a3b8", rx=1, sw=0)

    r1 = d.box(rx0, 165, rw, "CANARY — ĐÃ CHỨNG MINH NHẠY (canary.py)", [
        ("small", "5 con: luôn mua = đúng buyhold · luôn bán · đứng ngoài = 0 · trễ 1 bar (alpha ≈ 0) · biết trước (t > 20)"),
        ("small", "Tự kiểm độ nhạy: bắt 8/8 sau khi sửa · t > 5 trên tập sàng = nghi nhìn trước"),
    ], "rail", align="start", body_size=12, lh=18)
    _, r1y, _, r1h = r1

    r2 = d.box(rx0, r1y + r1h + 14, rw, "MUTATION AUDIT HẰNG THÁNG", [
        ("small", "Point-in-time test = ca cố định: dịch close lên 1 bar → dây chuyền phải gào"),
        ("small", "Chèn lỗi: đảo dấu phí · spread âm · cost bất đối xứng giữa 2 vế"),
    ], "rail", align="start", body_size=12, lh=18)
    _, r2y, _, r2h = r2

    r3 = d.box(rx0, r2y + r2h + 14, rw, "HIỆU CHUẨN", [
        ("small", "Placebo FDR phải đúng target (5%) · sai số ngoài mẫu z ~ N(0,1)"),
        ("small", "Quá nhiều PASS/ngày = tín hiệu HỎNG, không phải tin vui"),
    ], "rail", align="start", body_size=12, lh=18)
    _, r3y, _, r3h = r3

    r4 = d.box(rx0, r3y + r3h + 14, rw, "HẠN DÙNG BẤT ĐỐI XỨNG", [
        ("small", "PASS (tuyên bố về tiền): hết hạn 3/6/12 tháng theo hậu quả"),
        ("small", "Âm tính (tuyên bố về vắng mặt): CLOSED_UNLESS_TRIGGERED — điều kiện sai viết theo LỚP SỰ KIỆN, không theo ngày"),
        ("small", "Trigger xuất hiện → REOPENED_EXPLORATORY, đi lại từ đầu"),
    ], "rail", align="start", body_size=12, lh=18)
    _, r4y, _, r4h = r4

    r5 = d.box(rx0, r4y + r4h + 14, rw, "MÔ PHỎNG SONG NGỮ + DANH MỤC", [
        ("small", "1 khai báo template+tham số (YAML) → 2 backend: Python + MQL5 EA · conformance test bắt buộc"),
        ("small", "MT5 chỉ every-tick/real ticks · tắt swap trong tester, Python cộng cost_model"),
        ("small", "Danh mục: cấm optimizer · equal weight/inverse-vol/ERC đăng ký trước · Kelly vẫn là tham số"),
    ], "rail", align="start", body_size=12, lh=18)
    _, r5y, _, r5h = r5

    r6 = d.box(rx0, r5y + r5h + 14, rw, "LIVE & ĐỐI CHIẾU + SỨC CHỨA", [
        ("small", "magic = mã chiến lược · comment = attempt_id · khớp symbol+side+attempt_id+volume"),
        ("small", "CUSUM trên residual → WARN (dừng mở lệnh) → CRITICAL (halt)"),
        ("small", "Scale-aware validation: lệnh lớn tự đẩy giá → CAPACITY_CONSTRAINED"),
    ], "rail", align="start", body_size=12, lh=18)
    _, r6y, _, r6h = r6

    # --- mui ten cot giua ---
    d.arrow(cx, b0y + b0h, cx, y1, label="hằng ngày + nạp tay")
    d.arrow(cx, b1y + b1h, cx, y2, label="phép thử đo được →")
    d.arrow(cx, b2y + b2h, cx, y3, label="người ký →")
    d.arrow(cx, b3y + b3h, cx, y4, label="chạy cổng xác nhận")
    d.arrow(cx, b4y + b4h, cx, y5)

    # mui ten lien ket ngang
    d.arrow(lx0 + lw, l3y + l3h / 2, x0, b1y + 40, dashed=True, color="#94a3b8")
    d.txt(x0 - 6, b1y + 28, "thợ sinh phép thử mới", 11.5, "#64748b", "end")
    d.arrow(lx0 + lw, l4y + l4h / 2, x0, b3y + 40, dashed=True, color="#94a3b8")
    d.txt(x0 - 6, b3y + 28, "FDR siết dần", 11.5, "#64748b", "end")
    d.arrow(b5x := x0 + cw, b5y + 60, rx0, r1y + r1h / 2, dashed=True, color="#94a3b8")
    d.txt(b5x + 6, b5y + 50, "kết luận → báo cáo & canary giám sát", 11.5, "#64748b", "start")

    # --- banner ket qua ---
    by = r6y + r6h + 40 if r6y + r6h > l8y + l8h else l8y + l8h + 40
    d.box(x0 - 240, by, cw + 480, "KẾT QUẢ NGÀY 09/08/2026", [
        ("bold", "+51 phép thử khám phá tự sinh · 2 lỗi engine THẬT bị bắt nhờ canary:"),
        ("body", "phí qua đêm bất đối xứng (~2%/năm alpha giả, 63% “edge” Volatility System) · lệch 1 bar (+26,8%/năm, t trung vị −0,74 → +10,05)"),
        ("body", "Phát hiện chi phí: giữ SP500 dài chênh 5,5%/năm giữa các sàn · XM futures CFD swap = 0 (rẻ hơn cash 1,2–2,7%/năm) → alpha phép trừ ưu tiên cao"),
        ("small", "Vòng 6 chốt: mốc = cách RẺ NHẤT có cùng phơi nhiễm theo từng lớp tài sản · cổng máy kiểm được tính đối xứng chi phí 2 vế"),
    ], "dark", body_size=13)
    d.save("so_do_tong_quan.svg")


# ===========================================================================
# SO DO 2: VONG LAP TU SINH 24/7
# ===========================================================================
def so_do_vong_lap():
    d = Doc(1150, 1080)
    d.txt(575, 40, "VÒNG LẶP TỰ SINH 24/7 — THỢ DEEPSEEK × CLAUDE GIÁM SÁT", 24, "#0f172a", "middle", "bold")
    d.txt(575, 68, "Mỗi vòng = 1 lần bốc thăm khẳng định mới · kết quả ghi sổ, không tự duyệt · KHÔNG phải edge cho tới khi qua cổng",
          13.5, "#475569", "middle")

    cx, cw = 575, 430
    x0 = cx - cw / 2

    b1 = d.box(x0, 100, cw, "SỔ KHẲNG ĐỊNH KD_* (brain_khang_dinh.py)", [
        ("body", "11 khẳng định nguyên tử: 1 CHƯA_TEST · 3 ĐANG_SÀNG · 7 ĐÃ_ĐÓNG_SỔ"),
        ("small", "“Không có điều kiện bác bỏ → không phải khẳng định”"),
    ], "khangdinh")
    _, y1, _, h1 = b1

    b2 = d.box(x0, y1 + h1 + 30, cw, "ĐỀ XUẤT KHẲNG ĐỊNH MỚI (DeepSeek)", [
        ("body", "Đọc sổ → đề nghị câu chưa ai trả lời, kèm cách đo"),
        ("small", "Có điều kiện trên kết quả các vòng trước → adaptive search, phải trả giá online FDR"),
    ], "khampha")
    _, y2, _, h2 = b2

    b3 = d.box(x0, y2 + h2 + 30, cw, "VIẾT ĐÚNG 1 HÀM do(khoa, df, rng)", [
        ("body", "Thợ không chọn dữ liệu, không chọn ngưỡng, không viết kết luận"),
        ("small", "→ thợ vụng KHÔNG thể tự che edge giả"),
    ], "khampha")
    _, y3, _, h3 = b3

    b4 = d.box(x0, y3 + h3 + 30, cw, "QUÉT AN TOÀN + CLAUDE SOI", [
        ("body", "Nhìn trước (close[i] thay open[i+1]) · thiếu null · gọi mạng / xoá file · cum kết quả"),
        ("bold", "HỎNG → cho sửa ≤ 4 vòng, hết giờ thì bỏ · OK → chạy"),
    ], "warn")
    _, y4, _, h4 = b4
    # nhanh sua
    sx, sw_, sy, sh_ = x0 - 330, 250, y4 + 30, 80
    d.box(sx, sy, sw_, "SỬA CODE (tối đa 4 vòng)", [
        ("small", "hết giờ 900s hoặc vẫn hỏng → LOẠI"),
    ], "rail", align="start", body_size=12, lh=17)
    d.arrow(x0, y4 + h4 - 10, sx + sw_, sy + sh_ / 2, label="lỗi", lx=-40, ly=-8)
    d.arrow(sx + sw_ / 2, sy, x0, y4 + h4 / 2, dashed=True, color="#94a3b8")
    d.txt(x0 - 8, y4 + h4 / 2 - 8, "sửa lại → quét lại", 11.5, "#64748b", "end")

    b5 = d.box(x0, y4 + h4 + 30, cw, "brain_co_che.py — CHẠY ĐÚNG BỘ KỶ LUẬT", [
        ("body", "28 thị trường × 7 nhóm tương quan × 3 hạt ngẫu nhiên"),
        ("body", "p theo NHÓM (28 dòng không phải 28 phép thử độc lập) · trung vị · p hạt xấu nhất"),
    ], "khampha")
    _, y5, _, h5 = b5

    b6 = d.box(x0, y5 + h5 + 30, cw, "GHI SỔ KHÁM PHÁ", [
        ("body", "BRAIN_TU_SINH.md (phép thử #1…51) · BRAIN_CO_CHE.md · BRAIN_sang.parquet"),
        ("small", "Kèm đề xuất tiếp theo vào BRAIN_DE_XUAT_DS — CHƯA AI DUYỆT"),
    ], "rail")
    _, y6, _, h6 = b6

    b7 = d.box(x0, y6 + h6 + 30, cw, "NGƯỜI CHỌN → brain_khang_dinh.py", [
        ("body", "Con người đọc đề xuất, chọn cái đáng test → khẳng định mới, đăng ký, tốn FDR"),
        ("bold", "Không phản hồi = PENDING · không bao giờ tự động duyệt"),
    ], "dangky")
    _, y7, _, h7 = b7

    d.arrow(cx, y1 + h1, cx, y2)
    d.arrow(cx, y2 + h2, cx, y3)
    d.arrow(cx, y3 + h3, cx, y4)
    d.arrow(cx, y4 + h4, cx, y5, label="sạch →")
    d.arrow(cx, y5 + h5, cx, y6)
    d.arrow(cx, y6 + h6, cx, y7)

    # vong lap phan hoi
    d.arrow(x0 - 40, y7 + h7 / 2, x0 - 40, y1 + h1 / 2, dashed=True, color="#94a3b8")
    d.txt(x0 - 46, (y7 + h7 / 2 + y1 + h1 / 2) / 2, "khẳng định mới quay về sổ → vòng sau có điều kiện trên vòng trước", 11.5, "#64748b", "end")

    # ghi chu phai
    nx = x0 + cw + 30
    d.box(nx, y2, 300, "TẠI SAO TẦNG NÀY AN TOÀN", [
        ("body", "Tầng 1: không cổng nào, không tốn slot FDR — muốn thành edge phải:"),
        ("body", "người ký + lập hồ sơ + pre-registration + chạy TẬP XÁC NHẬN"),
        ("small", "Ngưỡng t > 5 trên tập sàng = nghi nhìn trước, chứng minh ngược mới thôi"),
    ], "rail", align="start", body_size=12, lh=18)
    d.box(nx, y5 + 10, 300, "RỦI RO CHÍNH: CHỌN LỌC THEO THỜI GIAN", [
        ("body", "Vòng n sinh ra có điều kiện trên vòng n−1 → SPA mù trước kiểu chọn lọc này"),
        ("body", "Hướng xử lý: online FDR (LORD/LOND…) · hoặc đề xuất CẢ MẺ trước khi chạy"),
    ], "warn", align="start", body_size=12, lh=18)
    d.box(nx, y7 - 20, 300, "CHẠY SONG SONG NHIỀU THỢ", [
        ("small", "ds_tho.py --tho <id> · toàn văn hội thoại lưu reports/ds/ để Claude soi lại"),
        ("small", "Log: _tusinh_tho0/1.log · hàng đợi: BRAIN_hang_doi.parquet"),
    ], "rail", align="start", body_size=12, lh=18)

    d.save("so_do_vong_lap.svg")


# ===========================================================================
# SO DO 3: CONG PASS
# ===========================================================================
def so_do_cong_pass():
    d = Doc(1150, 1150)
    d.txt(575, 40, "CỔNG XÁC NHẬN — 6 ĐIỀU KIỆN PASS (Tầng 4)", 24, "#0f172a", "middle", "bold")
    d.txt(575, 68, "Một kết luận chỉ được gọi EDGE khi qua đủ cửa này trên TẬP XÁC NHẬN — chưa từng nhìn lúc sàng",
          13.5, "#475569", "middle")

    cx, cw = 380, 460
    x0 = cx - cw / 2
    px = x0 + cw + 70   # cot phuong an loai

    b1 = d.box(x0, 100, cw, "GIẢ THUYẾT ĐÃ SÀNG, CÓ CƠ CHẾ", [
        ("small", "chưa đăng ký · chưa tốn slot FDR nào"),
    ], "khampha")
    _, y1, _, h1 = b1

    b2 = d.box(x0, y1 + h1 + 30, cw, "ĐÃ ĐĂNG KÝ TRƯỚC + plan_hash? (quyết định)", [
        ("body", "plan_hash bắt buộc ở tầng dữ liệu → bắt chạy chui, không chỉ bắt sửa file"),
        ("bold", "KHÔNG → tối đa EXPLORATORY, không bao giờ PASS"),
    ], "dangky")
    _, y2, _, h2 = b2
    e1 = d.box(px, y2 + 6, 300, "EXPLORATORY", [
        ("small", "kho chờ — không cần người nhìn, không phải edge"),
    ], "rail", align="start", body_size=12, lh=17)
    d.arrow(x0 + cw, y2 + 40, px, y2 + 40, label="chưa ký", lx=-46, ly=-8)

    b3 = d.box(x0, y2 + h2 + 30, cw, "CHẠY TRÊN TẬP XÁC NHẬN", [
        ("body", "sp500 · dowjones · nasdaq · russell2000 · us500cash · us500m"),
        ("small", "6 thị trường này chưa bao giờ bị nhìn lúc sàng"),
    ], "cong")
    _, y3, _, h3 = b3

    b4 = d.box(x0, y3 + h3 + 30, cw, "COST MODEL ĐỐI XỨNG 2 VẾ? (quyết định)", [
        ("body", "Chiến lược và mốc phải dùng CÙNG hàm chi phí trên cùng chuỗi phơi nhiễm"),
        ("body", "Mốc = cách RẺ NHẤT có cùng phơi nhiễm theo lớp tài sản (ETF ~0,1%/năm cho chỉ số)"),
        ("bold", "KHÔNG → TỪ CHỐI — bài học Vòng 6 (63% “edge” giả)"),
    ], "warn")
    _, y4, _, h4 = b4
    e2 = d.box(px, y4 + 10, 300, "TỪ CHỐI", [
        ("small", "lỗi mô hình chi phí, không phải tín hiệu"),
    ], "ketluan", align="start", body_size=12, lh=17)
    d.arrow(x0 + cw, y4 + 50, px, y4 + 50, label="mất đối xứng", lx=-70, ly=-8)

    b5 = d.box(x0, y4 + h4 + 30, cw, "6 ĐIỀU KIỆN PASS — ĐỒNG THỜI", [
        ("bold", "1. net_return > buyhold_net_return"),
        ("bold", "2. net_sharpe > buyhold_net_sharpe   (không phải do liều cao hơn)"),
        ("bold", "3. net_calmar > buyhold_net_calmar   (không phải do ôm sụt giảm)"),
        ("bold", "4. alpha_vs_buyhold > 0, p ≤ ngưỡng (Newey-West — chặn đòn bẩy trá hình)"),
        ("bold", "5. placebo_p ≤ ngưỡng — p XẤU NHẤT trong ≥ 5 hạt null"),
        ("bold", "6. pre_registered = true"),
    ], "cong")
    _, y5, _, h5 = b5
    d.box(px, y5 + 10, 300, "SIẾT THÊM KHI EXPOSURE > 95%", [
        ("small", "alpha & placebo p ≤ 0,01 + ≥1 giai đoạn con dương"),
        ("small", "Lý do: cơ chế VIX IC +0,106 nhưng placebo 10,2% — gần như là mua-giữ"),
    ], "rail", align="start", body_size=12, lh=17)

    b6 = d.box(x0, y5 + h5 + 30, cw, "PLACEBO + WALK-FORWARD + THỜI ĐẠI", [
        ("body", "Null factory: block bootstrap theo chính chuỗi vào lệnh (phải CỤM như thật)"),
        ("body", "Walk-forward 2 nửa · REGIME_LOCKED: mốc cấu trúc đăng ký trước (1971, 1987, 2000, 2008…)"),
        ("small", "Edge chỉ sống sau một mốc → cần cơ chế kinh tế + dữ liệu ngoài mẫu sau phát hiện"),
    ], "cong")
    _, y6, _, h6 = b6

    b7 = d.box(x0, y6 + h6 + 30, cw, "FDR TOÀN CỤC q = 10%", [
        ("body", "Ngưỡng tính trên TOÀN BỘ 324 phép thử tích lũy, không phải riêng lần chạy"),
        ("small", "Thêm giả thuyết = tự động siết ngưỡng cho tất cả"),
    ], "dangky")
    _, y7, _, h7 = b7

    b8 = d.box(x0, y7 + h7 + 30, cw, "SONG SÓT — KẾT LUẬN ĐƯỢC KÝ", [
        ("body", "Hạn dùng 3/6/12 tháng (hạng C/B/A) · tái kiểm quý bằng lịch Lan-DeMets"),
        ("body", "Không cộng FDR cho bảo trì · hết hạn = quay lại từ đầu"),
        ("small", "Hiện tại: 0 song sót / 324 — quá nhiều PASS/ngày là tín hiệu HỎNG dây chuyền"),
    ], "ketluan")
    _, y8, _, h8 = b8

    d.arrow(cx, y1 + h1, cx, y2)
    d.arrow(cx, y2 + h2, cx, y3, label="đã ký →")
    d.arrow(cx, y3 + h3, cx, y4)
    d.arrow(cx, y4 + h4, cx, y5, label="đối xứng →")
    d.arrow(cx, y5 + h5, cx, y6, label="đủ 6 điều kiện")
    d.arrow(cx, y6 + h6, cx, y7)
    d.arrow(cx, y7 + h7, cx, y8)

    d.save("so_do_cong_pass.svg")


if __name__ == "__main__":
    so_do_tong_quan()
    so_do_vong_lap()
    so_do_cong_pass()
