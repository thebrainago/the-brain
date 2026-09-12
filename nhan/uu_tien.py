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

Cai `xu_ly` KHONG lam: khong backtest. Do la viec cua quantlab va cua cong.

## BO SUNG 12/09/2026 - `phan_tich_ngay()`

Chu du an viet "hay **phan tich** va uu tien luong toi gui ngay nhe". Doc lai
thi "ngay" khong chi la doc ngay - la co CAU TRA LOI ngay. Truoc bo sung nay,
sau khi `xu_ly` dang ky xong, ung vien van phai cho mot vong quantlab moi biet
no co gi khong; ma hang doi do tung de 555 dong nam yen 13 ngay.

Nen `phan_tich_ngay()` lam not hai viec:
    1. xep hang doi QUANTLAB o **uu_tien = 0** (thap hon moi nguon may tu quet)
    2. chay LUON mot lan kiem tren nhom tai san dai dien, ket luan bang TIEN

Day la kiem NHANH, khong phai phan quyet: it ma, mot cau truc, khong holdout.
No tra loi "co dang dao sau khong", con "co giao dich duoc khong" van la cong.
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

    # DINH GO SAI MOT DUONG DAN / URL. Phai noi ro, dung im lang coi no la van
    # xuoi: mot URL go thieu chu "h" ma bi doc thanh "bai viet" se tra ve "0 co
    # che" - va chu du an se tuong bai viet do khong co gi, thay vi biet minh go sai.
    t = nguon.strip()
    mot_tu = " " not in t
    if mot_tu and (("/" in t) or ("\\" in t) or t.lower().startswith(("ht", "www."))
                   or Path(t).suffix):
        return {"nhan": False, "ly_do":
                "trong giong mot duong dan/URL nhung khong mo duoc: %r. "
                "Kiem lai chinh ta, hoac dan NOI DUNG vao thay vi duong dan."
                % t[:80]}

    # VAN BAN DAN THANG. Truoc 12/09/2026 cua nay chi nhan URL/file, nen khi chu
    # du an go thang mot y tuong ("mua khi RSI 14 duoi 30, thoat khi tren 55")
    # thi no tra ve "khong nhan ra nguon". Do la dung cai luong nay sinh ra de
    # phuc vu, nen phai nhan - va neu van ban khong co luat nao thi `xu_ly` se
    # bao "0 co che" kem danh sach cum chua hieu, ro hon "khong nhan ra nguon".
    if len(t) >= 12 and not mot_tu:
        return {"nhan": True, "van_ban": t,
                "tieu_de": "chu du an go thang", "cach": "van_ban"}
    return {"nhan": False, "ly_do":
            "khong nhan ra nguon - can URL, duong dan file, hoac mot cau "
            "(tu 12 ky tu tro len va nhieu hon mot tu)"}


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
        if not bai and len(vb) < 120:
            # Guard 120 ky tu cua `doc_bai` la de loc rac trong kho may quet.
            # Thu cua CHU DU AN thi khong phai rac - mot cau luat cung tinh.
            bai = DH.doc_bai(vb, tieu_de, nguon, toi_thieu=0)
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


#: Nhom tai san dai dien de tra loi ngay. It ma nhung du lop (FX chinh, vang,
#: chi so My) - cot de noi "co gi o day khong", khong phai de ket luan.
MA_KIEM = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XM_US500CASH", "XM_US100CASH")
KHUNG_KIEM = ("D1", "H4")


def phan_tich_ngay(kq: dict, xep_hang: bool = True, in_ra=print) -> dict:
    """Xep hang doi o uu tien 0 VA chay kiem nhanh cho cac co che vua nhan.

    `kq` la ket qua cua `xu_ly`. Tra ve chinh `kq`, them khoa `kiem_nhanh`.
    """
    import numpy as np
    ten = [c["ten"] for c in (kq.get("co_che") or []) if c.get("ten")]
    if not ten:
        kq["kiem_nhanh"] = []
        return kq

    if xep_hang:
        try:
            from . import hang_doi as HD
            r = HD.nap([{"tai_san": m, "khung": k, "template": t, "tham_so": {}}
                        for t in ten for m in MA_KIEM for k in KHUNG_KIEM],
                       nguon="chu_du_an", uu_tien=0)
            in_ra("")
            in_ra("XEP HANG DOI uu tien 0: them %d, da co %d"
                  % (r.get("them", 0), r.get("da_co", 0)))
        except Exception as e:
            in_ra("khong xep duoc hang doi: %s: %s" % (type(e).__name__, e))

    from . import du_lieu as DL
    from . import ngu_phap as NP
    from . import vao_lenh as VL
    kho = {x.get("ten"): x for x in NP.doc_kho()}
    bang = []
    for t in ten:
        spec = kho.get(t)
        if spec is None:
            continue
        for ma in MA_KIEM:
            for khung in KHUNG_KIEM:
                try:
                    df = DL.nap(ma, khung)
                except Exception:
                    continue
                if len(df) < 800:
                    continue
                try:
                    th = np.nan_to_num(np.asarray(NP.sinh_tu_spec(spec, df),
                                                  float).reshape(-1), nan=0.0)
                except Exception:
                    continue
                if int(np.sum(np.abs(th) > 0)) < 30:
                    continue
                b = VL.so_cau_truc(df, th, ma, khung, cac=["thi_truong"],
                                   giu_toi_da=60)
                if b:
                    b[0]["co_che"] = t
                    bang.append(b[0])
    bang.sort(key=lambda d: -d["cagr_dd20"])
    kq["kiem_nhanh"] = bang[:60]

    in_ra("")
    if not bang:
        in_ra("KIEM NHANH: khong o nao du lenh de do "
              "(co che qua thua tren nhom dai dien).")
        return kq
    in_ra("KIEM NHANH - %d o - xep bang TIEN o cung sut giam 20%%:" % len(bang))
    in_ra("  %-24s %-14s %-4s %7s %9s %8s"
          % ("CO CHE", "MA", "KH", "CHAN", "DD20%", "MOC%"))
    for d in bang[:10]:
        in_ra("  %-24s %-14s %-4s %7d %9.3f %8.3f%s"
              % (str(d["co_che"])[:24], d["ma"], d["khung"], d["so_chan"],
                 d["cagr_dd20"], d["moc_dd20"],
                 "  <- hon moc" if d["hon_moc"] else ""))
    hon = sum(1 for d in bang if d["hon_moc"])
    in_ra("  => %d/%d o thang moc (max mua-giu / ban-giu / tien mat)."
          % (hon, len(bang)))
    if not hon:
        in_ra("     Chua phai ket an: moi la mot cau truc, khong quan tri, "
              "khong holdout.")
    return kq


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
        print('go: python -m nhan.uu_tien <url hoac duong dan file> [--chi-doc]')
        sys.exit(2)
    _kq = xu_ly(sys.argv[1])
    in_ra(_kq)
    # Mac dinh PHAN TICH LUON. `--chi-doc` de ve hanh vi cu (chi boc, khong do).
    if _kq.get("nhan") and "--chi-doc" not in sys.argv:
        phan_tich_ngay(_kq)
