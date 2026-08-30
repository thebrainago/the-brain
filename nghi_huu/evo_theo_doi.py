# -*- coding: utf-8 -*-
"""evo_theo_doi.py - THE EVO: giam sat hoat dong 3 tru (Seeker/Quantlab/Banker).

Quet dau ra cua 3 tru (report/ket qua) de phat hien van de ton dong / phat sinh,
gom thanh danh sach VAN DE co muc uu tien cao/trung/thap, ghi vao
`lab/reports/EVO_van_de.md`.

Chay 1 luot:
  python evo_theo_doi.py

KHONG sua file khac, khong chay vong lap 24/7, khong tien trinh nen.
"""
import re
import pathlib
from datetime import datetime

LAB = pathlib.Path(__file__).resolve().parent
REPORTS = LAB / "reports"
QUANT = LAB / "quant"
OUT = REPORTS / "EVO_van_de.md"

# Nguon dau ra cua 3 tru (glob). File chua ton tai thi bo qua (ghi "thieu").
NGUON = [
    ("SEEKER",   "reports/SEEKER_*.md"      ),
    ("SEEKER",   "reports/quet.log"         ),
    ("BANKER",   "reports/banker_brief.md"  ),
    ("BANKER",   "reports/BANKER_vn_macro.md"),
    ("QUANTLAB", "quant/KET_QUA*.md"        ),
    ("QUANTLAB", "quant/TAI_LIEU.md"        ),
]

# 2 post Facebook nguoi dung gui lam vi du "nguon y tuong giai phap".
# Khong fetch duoc (tuong dang nhap) -> chi luu lam y tuong.
FB_POSTS = [
    ("https://www.facebook.com/100063765812298/posts/1619897140145798/",
     "FB post 1 (nguoi dung gui)"),
    ("https://www.facebook.com/story.php?story_fbid=1613489464119899&id=100063765812298",
     "FB post 2 (nguoi dung gui)"),
]

# Dau hieu da xu ly -> ha uu tien xuong "thap" (chi can theo doi).
RESOLVED = re.compile(r"đã sửa|đã bỏ|đã fix|đã khôi phục|đã xử lý", re.I)

# Bo quy tac quet: (ten nhom, regex, muc uu tien, goi y giai phap)
RULES = [
    ("Can dua len MT5 / Viet EA",
     re.compile(r"MT5 tick|MT5 that|len MT5|dua.{0,6}MT5|can viet EA|viet EA|EA khung|CODER/MT5", re.I),
     "cao",
     "Viet EA (vai CODER/MT5) dua co che len MT5 tick de xac minh truoc khi tin ket qua."),
    ("Thieu mau / it lenh",
     re.compile(r"thieu mau|khong du mau|mau qua it|it lenh|1.?6 lenh|cuc thap|vo nghia thong ke|khong co y nghia thong ke", re.I),
     "cao",
     "Tang mau: noi tan suat tin hieu hoac xuong khung nho hon; neu van it thi chi coi la goi y, khong tin tuong."),
    ("Loi code / crash",
     re.compile(r"\bloi\b|Traceback|NameError|not defined|Exception|that bai|\berror\b|fail", re.I),
     "cao",
     "Sua loi code / bo sung import thieu, chay lai thanh phan loi."),
    ("Nhin du lieu tuong lai (lookahead bias)",
     re.compile(r"lookahead|nhin du lieu tuong lai|shift\(-26\)|sai, da bo|bias", re.I),
     "cao",
     "Kiem tra bias du lieu: chi dung du lieu qua khu (shift +), chay lai backtest."),
    ("Nguon bi chan / loi fetch",
     re.compile(r"\b403\b|\b429\b|bi chan|bi chan|Bad Request|chat not found|CAN_THEM_BOT|khong fetch|khong lay duoc|khong tai", re.I),
     "trung",
     "Nguon chan (login/server): them proxy, old.reddit, cho noi chan, hoac chuyen nguon thay the."),
    ("Tai san delisted / thay nguon",
     re.compile(r"delisted|da xoa|khong con|thay cho|thay the", re.I),
     "trung",
     "Thay nguon/tai san bi delisted bang tuong duong va ghi ro sai lech."),
    ("Chua test / chua xac minh",
     re.compile(r"chua qua|chua duoc|chua test|chua xac minh|chua tinh chinh|chua walk-forward|chua noi|chua dua", re.I),
     "trung",
     "Dua vao hang doi test MT5 / chay walk-forward + placebo truoc khi tin ket qua."),
    ("Can noi tieu chi / mau lon hon",
     re.compile(r"can noi|noi tieu chi|noi tan suat|noi long|can mau nhieu hon", re.I),
     "trung",
     "Noi tieu chi bo loc de co mau du lon, chay lai backtest roi quyet dinh."),
    ("PF thap / thua buy-hold",
     re.compile(r"PF[ \t]*0|PF[ \t]*1\.0[0-9]|PF thap|PF kem|thua buy.?and.?hold|am lai|thua xa|khong dat PF", re.I),
     "trung",
     "Rasoat lai chi phi + mau that; neu van thap thi loai khoi dien uu tien."),
    ("Loai / tam hoan / khong dang tin",
     re.compile(r"\bloai\b|tam hoan|tam dung|khong dang tin|khong theo duoi", re.I),
     "thap",
     "Loai khoi dien uu tien hoac hoan cho toi khi co bien the / noi tieu chi."),
    ("Viec dang do (stub / dang noi / dang test)",
     re.compile(r"\bstub\b|TODO|dang noi|dang test|dang backtest|dang cho", re.I),
     "thap",
     "Theo doi tien do; hoan thien phan dang do."),
]

PRIORITY_ORDER = {"cao": 0, "trung": 1, "thap": 2}


def _glob_files(tru, pattern):
    """Tra danh sach file khop glob cua tru. Neu pattern khong co '*' -> file don."""
    base = LAB
    if "/" in pattern:
        base = LAB / pattern.rsplit("/", 1)[0]
        name = pattern.rsplit("/", 1)[1]
    else:
        name = pattern
    if "*" in name:
        return sorted(base.glob(name))
    p = base / name
    return [p] if p.exists() else []


def _snippet(line):
    """Lam sach dong de lam mo ta (bo markdown, cat ngan)."""
    t = re.sub(r"[|*`#>\-]", " ", str(line)).strip()
    t = re.sub(r"\s+", " ", t)
    return t[:140] if t else t


def _scan(tru, path):
    """Quet 1 file, tra danh sach issue {ten, muc, mo_ta, giai_phap}."""
    issues = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # khong doc duoc -> van de gui
        issues.append({
            "ten": "Khong doc duoc file",
            "muc": "cao",
            "mo_ta": f"Khong the doc {path.name}: {exc}",
            "giai_phap": "Kiem tra quyen/encoding cua file dau ra.",
        })
        return issues, f"[LOI] {str(exc)}"
    seen = set()
    for line in text.splitlines():
        for ten, rx, muc, giai_phap in RULES:
            if rx.search(line):
                key = (ten, muc, _snippet(line))
                if key in seen:
                    continue
                seen.add(key)
                it = {"ten": ten, "muc": muc,
                      "mo_ta": _snippet(line), "giai_phap": giai_phap}
                # van de da ghi ro "da sua/da bo" -> khong con can hanh dong gap
                if RESOLVED.search(line) and muc != "thap":
                    it["muc"] = "thap"
                    it["giai_phap"] = giai_phap + " (chi tiet ghi da xu ly — theo doi lai.)"
                issues.append(it)
    return issues, f"quet {len(text.splitlines())} dong -> {len(issues)} van de"


def build_report():
    all_issues = []   # dong bang van de
    source_note = []  # trang thai tung file nguon
    for tru, pattern in NGUON:
        files = _glob_files(tru, pattern)
        if not files:
            source_note.append(f"- `{pattern}`: KHONG CO file (chua co dau ra tru {tru})")
            continue
        for path in files:
            issues, note = _scan(tru, path)
            source_note.append(f"- `{path.relative_to(LAB)}`: {note}")
            for it in issues:
                it["nguon"] = tru
                it["file"] = str(path.relative_to(LAB))
                all_issues.append(it)

    all_issues.sort(key=lambda x: PRIORITY_ORDER.get(x["muc"], 9))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# EVO — BÁO CÁO GIÁM SÁT 3 TRỤ (VẤN ĐỀ / ĐỀ XUẤT)")
    lines.append("")
    lines.append(f"> Thời điểm quét: **{now}** (Asia/Saigon) · Module: `lab/evo_theo_doi.py`")
    lines.append("> Quét thủ công 1 lượt, KHÔNG phải vòng lặp 24/7.")
    lines.append("")

    lines.append("## 1. TRẠNG THÁI NGUỒN ĐẦU VÀO")
    lines.append("")
    lines.extend(source_note)
    lines.append("")

    dem = {"cao": 0, "trung": 0, "thap": 0}
    for it in all_issues:
        dem[it["muc"]] = dem.get(it["muc"], 0) + 1

    lines.append("## 2. BẢNG VẤN ĐỀ PHÁT HIỆN")
    lines.append("")
    lines.append(f"Tổng: **{len(all_issues)}** vấn đề (cao={dem['cao']}, trung={dem['trung']}, thấp={dem['thap']}).")
    lines.append("")
    lines.append("| # | Ưu tiên | Nhóm vấn đề | Mô tả ghi nhận | Nguồn | File | Gợi ý giải pháp |")
    lines.append("|---|---------|-------------|----------------|-------|------|------------------|")
    for i, it in enumerate(all_issues, 1):
        muc = it["muc"].upper()
        mo = it["mo_ta"].replace("|", "\\|")
        giai = it["giai_phap"].replace("|", "\\|")
        lines.append(f"| {i} | {muc} | {it['ten']} | {mo} | {it['nguon']} | `{it['file']}` | {giai} |")
    lines.append("")

    # tom tat hanh dong: gom theo nhom + cac file lien quan (khong lap trung)
    grouped = {}
    for it in all_issues:
        key = (it["muc"], it["ten"])
        grouped.setdefault(key, set()).add(it["file"])
    lines.append("## 3. TÓM TẮT HÀNH ĐỘNG")
    lines.append("")
    for muc in ("cao", "trung", "thap"):
        n = dem.get(muc, 0)
        if not n:
            continue
        items = [f"{ten} ({', '.join(sorted(files))})"
                 for (m, ten), files in grouped.items() if m == muc]
        lines.append(f"- **Ưu tiên {muc.upper()} ({n} vấn đề):** " + "; ".join(items))
        lines.append("")

    lines.append("## 4. NGUỒN Ý TƯỞNG GIẢI PHÁP (Facebook — người dùng gửi làm ví dụ)")
    lines.append("")
    lines.append("> 2 post này **không fetch được** (tường đăng nhập), chỉ lưu link làm **ý tưởng** "
                 "để EVO/CHUNG tham khảo khi đề xuất giải pháp — cần theo dõi/gợi ý người dùng dán nội dung.")
    lines.append("")
    for url, label in FB_POSTS:
        lines.append(f"- **{label}**: <{url}>")
    lines.append("")
    lines.append("---")
    lines.append("_File này do EVO tự tạo mỗi lượt quét; không sửa các file khác trong lab._")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    return all_issues, dem


def main():
    all_issues, dem = build_report()
    print(f"EVO: quet xong -> {len(all_issues)} van de (cao={dem['cao']}, trung={dem['trung']}, thap={dem['thap']})")
    print(f"Da ghi: {OUT}")
    for it in all_issues:
        print(f"  [{it['muc'].upper()}] {it['ten']} | {it['file']}")


if __name__ == "__main__":
    main()

