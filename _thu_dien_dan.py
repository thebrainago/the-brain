# -*- coding: utf-8 -*-
"""_thu_dien_dan.py - THU THAP tu dien dan giao dich cac nuoc.

## Vi sao co file nay

Chu du an, 15/09/2026: *"o vietnam co dien dan traderviet, vay o hang bao nhieu
nuoc kia cung co nhung dien dan nhu the. Can them vao bo thu thap va tien hanh
thu thap."*

Hai cho hong tim ra khi lam viec nay:

1. **Seeker chi doc tieng Anh.** `GH_NGON_NGU` la ngon ngu LAP TRINH chu khong
   phai ngon ngu nguoi; moi URL mql5 deu ghim `/en/`; nguon phi-Anh duy nhat
   chay theo tu khoa la habr.
2. **Lop cong dong phi-Anh them 30/08 nam trong `NGUON_TRINH_DUYET`** - tuc chi
   chay khi con Chrome CDP dang mo. CDP dang TAT, nen qiita/habr/smart-lab/
   cnblogs/velog gan nhu chua tung chay lan nao. Bay gio do lai thi ca 7 dien
   dan duoi day doc duoc bang `requests` THUAN, khong can CDP.

Nen file nay di duong `requests`, khong phu thuoc CDP.

## Danh sach nay la DO DUOC, khong phai de xuat

Moi muc duoi day da qua `_do_dien_dan_quoc_gia.py`: vao duoc, VA boc ra duoc
link bai that. Do 15/09 (so link tren mot trang hat giong):

    mql5_forum_ru   106     traderviet       89     thaiforexschool  55
    note_fx          50     fxon             28     smartlab          1

Nhung cai KHONG vao duoc tu may nay, ghi lai de khong ai do lai: forexfactory,
babypips, mmgp, gogojungle, pantip, fx168, arabictrader, wallstreet-online,
forex-nawigator, forexforum.com.tr. Kaskus vao duoc nhung la app JS (0 link
trong HTML). traderji.com tra ve trang mac dinh Apache - ten mien khong con
trang web. Chi tiet o `reports/DIEN_DAN_QUOC_GIA.json`.

Chay:  python _thu_dien_dan.py              (thu het)
       python _thu_dien_dan.py --bai 20     (moi dien dan toi da 20 bai)
"""
from __future__ import annotations

import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from tru import seeker as SK   # noqa: E402

#: ten -> cau hinh. `hat_giong` la trang CHUYEN MUC (khong phai trang tim kiem:
#: trang tim kiem cua phan lon dien dan dung JS va tra ve 0 link).
DIEN_DAN = {
    "mql5_forum_ru": {
        "ngon_ngu": "ru", "nuoc": "Nga",
        "hat_giong": ["https://www.mql5.com/ru/forum",
                      "https://www.mql5.com/ru/forum/trading_systems",
                      "https://www.mql5.com/ru/forum/mql5"],
        "loc": r"mql5\.com/ru/forum/\d+",
        "hang": "A", "loai": "dien_dan"},
    "traderviet": {
        "ngon_ngu": "vi", "nuoc": "Viet Nam",
        "hat_giong": ["https://traderviet.com/",
                      "https://traderviet.com/forums/robot-ea-indicator.44/",
                      "https://traderviet.com/forums/kien-thuc-trading-kinh-nghiem-trading.31/"],
        "loc": r"traderviet\.com/t/[^\"'\s<>]+",
        "hang": "B", "loai": "dien_dan"},
    "thaiforexschool": {
        "ngon_ngu": "th", "nuoc": "Thai Lan",
        "hat_giong": ["https://www.thaiforexschool.com/"],
        "loc": r"thaiforexschool\.com/[a-z0-9\-/]{8,}",
        "hang": "B", "loai": "dien_dan"},
    "note_fx": {
        "ngon_ngu": "ja", "nuoc": "Nhat",
        # `FX自動売買` = giao dich FX tu dong · `EA` la tu ban le Nhat dung
        "hat_giong": ["https://note.com/hashtag/FX自動売買",
                      "https://note.com/hashtag/システムトレード"],
        "loc": r"note\.com/[^/\"'\s]+/n/n[0-9a-f]+",
        "hang": "B", "loai": "cong_dong"},
    "fxon": {
        "ngon_ngu": "ja", "nuoc": "Nhat",
        # Cho ban EA lon cua Nhat - moi san pham co trang mo ta co che.
        "hat_giong": ["https://fx-on.com/", "https://fx-on.com/systemtrade/fx"],
        "loc": r"fx-on\.com/(?:\w\w/)?(?:post|systemtrade|review)/[^\"'\s<>]*\d+",
        "hang": "A", "loai": "ma_nguon"},
    "smartlab": {
        "ngon_ngu": "ru", "nuoc": "Nga",
        "hat_giong": ["https://smart-lab.ru/blogs/",
                      "https://smart-lab.ru/blog/algotrading/"],
        "loc": r"smart-lab\.ru/(?:blog|company)/[^\"'\s<>]+/\d+",
        "hang": "B", "loai": "cong_dong"},
}

#: Tu khoa loc TIEU DE. Bai ve quan tri lenh moi dang, khong phai moi bai tren
#: dien dan. Da ngon ngu vi tieu de la tieng ban dia.
TU_KHOA_LOC = [
    # Anh
    "grid", "hedg", "trailing", "martingale", "averaging", "partial", "ea",
    "expert advisor", "robot", "lot", "drawdown",
    # Nga
    "сетк", "сеточ", "хедж", "трейлинг", "мартингейл", "усреднен", "советник",
    "безубыт", "просадк",
    # Nhat
    "グリッド", "両建", "ナンピン", "マーチンゲール", "トレーリング", "自動売買",
    "資金管理", "分割決済",
    # Trung
    "网格", "对冲", "马丁", "补仓", "加仓", "移动止损", "仓位",
    # Viet
    "lưới", "hedge", "nhồi", "gồng", "cắt lỗ", "quản lý vốn", "khối lượng",
    # Thai
    "กริด", "เฮดจ์", "มาติงเกล",
]


def _hop_le(tieu_de: str) -> bool:
    t = str(tieu_de).lower()
    return any(k.lower() in t for k in TU_KHOA_LOC)


def _tieu_de(html: str, url: str) -> str:
    m = re.search(r"<title[^>]*>(.{3,300}?)</title>", html, re.S | re.I)
    if m:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    return url.rsplit("/", 1)[-1]


def lay_link(cfg: dict) -> list[str]:
    """Bot moi trang hat giong ra link BAI."""
    ra: list[str] = []
    for u in cfg["hat_giong"]:
        try:
            t = SK._lay(u, timeout=25)
        except Exception:
            t = None
        if not t:
            continue
        # HREF TUONG DOI: phai noi ve tuyet doi truoc khi khop, neu khong
        # mql5.com ra 1 link tren mot trang co 175.
        tuyet_doi = " ".join(urljoin(u, h) for h in
                             re.findall(r'href="([^"]{2,200})"', t))
        for m in re.findall(cfg["loc"], t) + re.findall(cfg["loc"], tuyet_doi):
            v = m if isinstance(m, str) else m[0]
            if not v.startswith("http"):
                v = "https://" + v
            if v not in ra:
                ra.append(v)
        time.sleep(1.0)     # di cham: khong lam phien dien dan nguoi ta
    return ra


def thu_mot(ten: str, cfg: dict, so_bai: int) -> dict:
    t0 = time.time()
    link = lay_link(cfg)[:so_bai * 3]
    ds, doc = [], 0
    for u in link:
        if len(ds) >= so_bai:
            break
        try:
            html = SK._lay(u, timeout=25)
        except Exception:
            html = None
        doc += 1
        if not html or len(html) < 1500:
            continue
        td = _tieu_de(html, u)
        if not _hop_le(td):
            continue
        van = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html,
                     flags=re.S | re.I)
        van = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", van)).strip()
        ds.append({"tieu_de": td, "url": u, "tom_tat": van[:2000],
                   "hang": cfg["hang"], "loai": cfg["loai"],
                   "tu_khoa": cfg["ngon_ngu"]})
        time.sleep(0.6)
    moi = SK.luu_tai_lieu("dd_" + ten, ds) if ds else 0
    return {"ten": ten, "nuoc": cfg["nuoc"], "ngon_ngu": cfg["ngon_ngu"],
            "link": len(link), "doc": doc, "hop_le": len(ds),
            "moi": int(moi or 0), "giay": round(time.time() - t0, 1)}


def main() -> int:
    so_bai = int(sys.argv[sys.argv.index("--bai") + 1]
                 if "--bai" in sys.argv else 25)
    print("THU THAP tu %d dien dan giao dich, toi da %d bai moi cai\n"
          % (len(DIEN_DAN), so_bai))
    with ThreadPoolExecutor(max_workers=3) as ex:
        ket = list(ex.map(lambda kv: thu_mot(kv[0], kv[1], so_bai),
                          DIEN_DAN.items()))
    ket.sort(key=lambda d: -d["moi"])
    print("%-16s %-10s %-4s %6s %6s %7s %6s %6s"
          % ("dien dan", "nuoc", "ng", "link", "doc", "hop le", "MOI", "giay"))
    print("-" * 70)
    for d in ket:
        print("%-16s %-10s %-4s %6d %6d %7d %6d %6.1f"
              % (d["ten"], d["nuoc"], d["ngon_ngu"], d["link"], d["doc"],
                 d["hop_le"], d["moi"], d["giay"]))
    print("\nTONG %d tai lieu MOI tu %d thu tieng"
          % (sum(d["moi"] for d in ket), len({d["ngon_ngu"] for d in ket})))
    print("buoc sau: `b boc` de boc co che tu chung")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
