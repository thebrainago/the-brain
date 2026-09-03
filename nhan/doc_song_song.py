# -*- coding: utf-8 -*-
"""doc_song_song.py - DOC TOAN VAN song song, uu tien nguon co SUAT CAO.

Do 03/09/2026: sau khi va duong boc (0 -> 18,9 co che/100 ban), nut that dich
sang chang DOC. `seeker.doc_toan_van` tai URL TUAN TU: 28 ban / 245 giay =
8,75 s/ban, va con **1.175 tai lieu chua co ban doc** -> 2,9 gio.

Va no con thoai hoa: vong 1 doc duoc 28/that bai 2, vong 3 con **1/26**. Vi
no lay theo thu tu bang chu khong theo NGUON, nen di vao mot me `crossref` /
`openalex` (DOI, phan lon co tuong phi) la ca vong hong.

Trong 1.175 tai lieu do:
   tradingview_pine 285 | mql5_code 174 | crossref 139 | openalex 117
   stackexchange 99 | hackernews 84 | cnblogs_trung 72 | github 54
**459 dau tien la kho MA NGUON** - dung hai nguon cho suat cao nhat, va chung
la trang ma chu khong phai paywall hoc thuat.

File nay doi hai dieu:
  1. **Uu tien theo nguon**, xep theo suat co che DO DUOC chu khong theo lich.
  2. **Tai song song**, vi cho mang la cho khong, khong phai tinh toan.

Khong doi: van di qua `seeker` de ghi `noi_dung`/`artifact` dung mot cho, va
van ton trong `khong_doc_duoc` de khong tai lai vo han.
"""
from __future__ import annotations

import concurrent.futures as _cf
import time

from nhan import so as SO

#: Xep theo suat co che DO DUOC (03/09/2026), khong theo cam giac.
#: tradingview/mql5 = trang ma; crossref/openalex = DOI, phan lon co tuong phi.
UU_TIEN_NGUON = [
    "tradingview_pine", "tradingview_scripts", "mql5_code", "mql5_bai_viet",
    "rss_mql5_articles", "github", "lean_algo", "quantconnect",
    "rss_tradingview_blog", "blog", "reddit_td", "stackexchange",
    "hackernews", "cnblogs_trung", "velog_han", "qiita_nhat", "habr_nga",
    "youtube", "x", "tiktok",
]
#: Cuoi hang, khong phai bo han: phan lon co tuong phi nhung van co bai mo.
CUOI_HANG = ["crossref", "openalex", "arxiv"]


def _thu_tu(nguon: str) -> int:
    if nguon in UU_TIEN_NGUON:
        return UU_TIEN_NGUON.index(nguon)
    if nguon in CUOI_HANG:
        return 900 + CUOI_HANG.index(nguon)
    return 500


def chua_doc(gioi_han: int = 400, chi_nguon: list[str] | None = None) -> list[dict]:
    """Tai lieu chua co ban doc, xep theo uu tien nguon."""
    ds = SO.nhieu(
        "SELECT t.id, t.url, t.tieu_de, t.nguon FROM tai_lieu t "
        "LEFT JOIN noi_dung n ON n.tai_lieu_id = t.id "
        "WHERE n.id IS NULL AND t.url IS NOT NULL AND t.url != ''") or []
    ra = [dict(r) for r in ds]
    if chi_nguon:
        ra = [r for r in ra if r.get("nguon") in chi_nguon]
    ra.sort(key=lambda r: (_thu_tu(r.get("nguon") or ""), -(r["id"] or 0)))
    return ra[:gioi_han]


#: Phan loai ban doc de `boc_llm.ung_vien` loc dung. Giu don gian va bao thu:
#: doan sai sang `ma_nguon` chi lam mot bai vao hang doi som hon; doan sai
#: sang `khac` thi bai do bi bo qua han.
_DAU_MA = ("//@version", "study(", "indicator(", "strategy(", "#property",
           "OnTick(", "def ", "import ", "class ", "function ", "public ")


def _loai(vb: str) -> str:
    v = (vb or "")[:4000]
    return "ma_nguon" if any(d in v for d in _DAU_MA) else "bai_bao"


def _mot(t: dict) -> dict:
    from tru import seeker as SK
    t0 = time.time()
    try:
        vb = SK._lay(t["url"], timeout=25)
    except Exception as e:
        return {"id": t["id"], "loi": f"{type(e).__name__}: {str(e)[:60]}",
                "giay": time.time() - t0}
    if not vb or len(vb) < 400:
        return {"id": t["id"], "loi": "rong hoac qua ngan",
                "giay": time.time() - t0}
    return {"id": t["id"], "url": t["url"], "nguon": t.get("nguon"),
            "van_ban": vb, "giay": time.time() - t0}


def doc(gioi_han: int = 300, luong: int = 12, chi_nguon=None,
        in_ra=print) -> dict:
    """Tai song song roi ghi `noi_dung`. Tra thong ke."""
    from tru import seeker as SK

    ds = chua_doc(gioi_han, chi_nguon)
    if not ds:
        return {"tai_lieu": 0, "doc_duoc": 0}
    in_ra(f"  {len(ds)} tai lieu chua doc (uu tien nguon ma nguon)")

    t0 = time.time()
    ok, hong = 0, 0
    theo_nguon: dict[str, int] = {}
    with _cf.ThreadPoolExecutor(max_workers=luong) as ex:
        for i, r in enumerate(ex.map(_mot, ds), 1):
            if r.get("loi"):
                hong += 1
                # Ghi `khong_doc_duoc` de vong sau khong tai lai vo han. Than
                # ban ghi chinh LY DO - `_ghi_ban_doc` dung `len(van_ban)` lam
                # `so_ky_tu`, va `boc_llm.ung_vien` loc bang cot do.
                try:
                    SK._ghi_ban_doc(r.get("url") or "",
                                    f"[khong doc duoc] {r['loi']}",
                                    kieu="khong_doc_duoc")
                except Exception:
                    pass
            else:
                try:
                    SK._ghi_ban_doc(r["url"], r["van_ban"], kieu=_loai(r["van_ban"]))
                    ok += 1
                    theo_nguon[r.get("nguon") or "?"] = \
                        theo_nguon.get(r.get("nguon") or "?", 0) + 1
                except Exception:
                    hong += 1
            if i % 50 == 0:
                in_ra(f"  ... {i}/{len(ds)}  doc duoc {ok}  ({time.time()-t0:.0f}s)")

    giay = time.time() - t0
    return {"tai_lieu": len(ds), "doc_duoc": ok, "hong": hong,
            "giay": round(giay, 1),
            "giay_moi_ban": round(giay / max(len(ds), 1), 2),
            "theo_nguon": dict(sorted(theo_nguon.items(), key=lambda x: -x[1])[:8])}
