# -*- coding: utf-8 -*-
"""uu_tien.py - CUA MOT BUOC cho chu du an: mot link/file -> co che, ngay trong phien.

## Vi sao

`hethong.txt`, muc "Quantlab luong uu tien":
    *"Khi toi tim duoc 1 bai viet, 1 phuong phap, gia thuyet nao do hay phan
    tich va uu tien luong toi gui ngay nhe"*

Do 11/09/2026: khong co cua nao. `nap_tay/` co 5 repo da tai san, nhung khong co
duong "gui mot link -> nhan ket qua". Thu chu du an gui phai di vao cung hang doi
voi 10.000 tai lieu may tu quet - tuc la co the vai ngay sau moi toi luot, va
den luc do thi cau hoi da nguoi.

## Ham nay lam gi

    1. nhan URL hoac duong dan file
    2. lay toan van (trang web / .md / .txt / .pdf / video YouTube)
    3. chay `doc_hieu.doc_bai` -> co che
    4. dang ky cai doc duoc qua `ngu_phap.them_co_che` (cong van la cong cu)
    5. hoi `bai_hoc.tra` xem huong nay da tung di chua
    6. tra ve MOT ban tom tat doc duoc ngay

Cai KHONG lam: khong backtest, khong ket luan tot/xau. Do la viec cua quantlab
va cua cong. Cua nay chi rut ngan duong TU LINK DEN UNG VIEN.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

KIEU = "uu_tien"


def _lay_van_ban(nguon: str) -> dict:
    """-> {nhan, van_ban, tieu_de, cach, ly_do}"""
    p = Path(nguon)
    if p.exists() and p.is_file():
        if p.suffix.lower() == ".pdf":
            try:
                import pymupdf
                with pymupdf.open(p) as d:
                    vb = "\n".join(t.get_text() for t in d)
            except Exception as e:
                return {"nhan": False, "ly_do": f"doc PDF hong: {type(e).__name__}"}
        else:
            vb = p.read_text(encoding="utf-8", errors="ignore")
        return {"nhan": True, "van_ban": vb, "tieu_de": p.name, "cach": "file"}

    if re.search(r"youtube\.com/watch|youtu\.be/", nguon):
        from . import doc_video as DV
        kq = DV.phu_de(nguon)
        if not kq["nhan"]:
            return {"nhan": False, "ly_do": f"video: {kq['ly_do']}"}
        return {"nhan": True, "van_ban": kq["van_ban"],
                "tieu_de": kq.get("tieu_de") or nguon, "cach": "video_phu_de"}

    if nguon.startswith(("http://", "https://")):
        # DUNG LAI ha tang da co, theo dung thu tu `toan_van` da hieu chuan:
        # arxiv / github co duong rieng, roi HTML, roi TRINH DUYET cho trang
        # chan bot. Ban dau toi viet mot duong lui `requests` tho - va no lam
        # quantifiedstrategies.com tra ve dung 124 ky tu "Bot Verification",
        # tuc bao "khong co co che nao" cho mot bai co day co che.
        from . import toan_van as TV
        for ten, ham in (("arxiv", TV.tu_arxiv), ("github", TV.tu_github),
                         ("html", TV.tu_html)):
            try:
                kq = ham(nguon)
            except Exception:
                kq = None
            vb = (kq or {}).get("van_ban") or (kq or {}).get("noi_dung") or ""
            if vb and len(vb) > 400:
                return {"nhan": True, "van_ban": vb,
                        "tieu_de": (kq or {}).get("tieu_de") or nguon, "cach": ten}
        try:
            kq = TV.tu_trinh_duyet(nguon)
        except Exception as e:
            return {"nhan": False,
                    "ly_do": f"trinh duyet hong: {type(e).__name__}: {str(e)[:90]}"}
        vb = (kq or {}).get("van_ban") or (kq or {}).get("noi_dung") or ""
        if vb and len(vb) > 400:
            return {"nhan": True, "van_ban": vb,
                    "tieu_de": (kq or {}).get("tieu_de") or nguon,
                    "cach": "trinh_duyet"}
        return {"nhan": False, "ly_do": (
            f"lay duoc {len(vb)} ky tu - qua ngan de doc. Trang co the dang chan "
            f"bot; thu `b mang` (bat WARP) hoac mo CDP cho `doc_trinh_duyet`.")}

    return {"nhan": False, "ly_do": "khong nhan ra nguon - can URL hoac duong dan file"}


def xu_ly(nguon: str, ghi_kho: bool = True) -> dict:
    from . import doc_hieu as DH
    from . import ngu_phap as NP

    lay = _lay_van_ban(nguon)
    if not lay["nhan"]:
        return {"nhan": False, "ly_do": [lay["ly_do"]], "nguon": nguon}
    vb, tieu_de = lay["van_ban"], lay.get("tieu_de") or nguon

    if ghi_kho:
        vt = SO.van_tay(KIEU, nguon, vb[:4000])
        if not SO.mot("SELECT id FROM noi_dung WHERE van_tay = ?", vt):
            with SO.ket_noi() as cn:
                cn.execute(
                    "INSERT INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
                    "so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc) "
                    "VALUES(NULL,?,?,?,?,?,?,?,?,0)",
                    (vt, nguon, KIEU, lay["cach"], len(vb), len(vb), vb,
                     SO.bay_gio()))

    try:
        bai = DH.doc_bai(vb, tieu_de, nguon)
    except Exception as e:
        return {"nhan": False, "ly_do": [f"doc_hieu nem loi: {type(e).__name__}: {e}"],
                "nguon": nguon, "so_ky_tu": len(vb)}

    co_che, tu_choi = [], []
    for r in bai:
        spec = dict(r["spec"], nguon=nguon)
        try:
            kq = NP.them_co_che(spec) if ghi_kho else {"nhan": None, "ly_do": []}
        except Exception as e:
            kq = {"nhan": False, "ly_do": [f"{type(e).__name__}: {e}"]}
        m = {"ten": spec.get("ten"), "ho": spec.get("ho"),
             "chieu": spec.get("chieu"), "vao": spec.get("vao"),
             "nhan": kq.get("nhan")}
        (co_che if kq.get("nhan") is not False else tu_choi).append(
            m if kq.get("nhan") is not False else {**m, "ly_do": kq["ly_do"][:1]})

    # he da tung di huong nay chua
    da_thu = []
    try:
        from . import bai_hoc as BH
        goi = " ".join([tieu_de] + [str(c.get("ho")) for c in co_che])
        da_thu = [{"loai": t["loai"], "tieu_de": t["tieu_de"][:110],
                   "bang_chung": (t["bang_chung"] or "")[:160]}
                  for t in BH.tra(goi, so_the=3)]
    except Exception:
        pass

    # cum ngu phap CHUA noi duoc - de biet vi sao mot bai "khong ra gi"
    chua_hieu = []
    try:
        chua_hieu = [x["cum"] for x in DH.cum_chua_hieu(vb, toi_da=8)]
    except Exception:
        pass

    return {"nhan": True, "ly_do": [], "nguon": nguon, "tieu_de": tieu_de,
            "cach": lay["cach"], "so_ky_tu": len(vb),
            "co_che": co_che, "tu_choi": tu_choi,
            "cum_chua_hieu": chua_hieu, "bai_hoc_lien_quan": da_thu}


def in_ra(kq: dict) -> None:
    if not kq["nhan"]:
        print("KHONG XU LY DUOC:", "; ".join(kq["ly_do"]))
        return
    print(f"{kq['tieu_de'][:90]}")
    print(f"  nguon: {kq['nguon'][:90]}")
    print(f"  doc bang: {kq['cach']} · {kq['so_ky_tu']:,} ky tu".replace(",", "."))
    print(f"\nCO CHE DOC DUOC: {len(kq['co_che'])}")
    for c in kq["co_che"]:
        print(f"  [{c['ho']}] {c['ten']}  (nhan: {c['nhan']})")
        for d in (c.get("vao") or [])[:3]:
            print(f"      {d}")
    if kq["tu_choi"]:
        print(f"\nCONG TU CHOI: {len(kq['tu_choi'])}")
        for c in kq["tu_choi"][:5]:
            print(f"  {c['ten']}: {(c.get('ly_do') or [''])[0][:100]}")
    if kq["cum_chua_hieu"]:
        print("\nNGU PHAP CHUA NOI DUOC (hang doi tu vung):")
        print("  " + " · ".join(kq["cum_chua_hieu"]))
    if kq["bai_hoc_lien_quan"]:
        print("\nHE DA TUNG DI HUONG NAY:")
        for t in kq["bai_hoc_lien_quan"]:
            print(f"  [{t['loai']}] {t['tieu_de']}")
            if t["bang_chung"]:
                print(f"      {t['bang_chung']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('go: python -m nhan.uu_tien <url hoac duong dan file>')
        sys.exit(2)
    in_ra(xu_ly(sys.argv[1]))
