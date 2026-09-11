# -*- coding: utf-8 -*-
"""_corpus_ngu_phap.py - DO TRAN CUA NGU PHAP bang corpus van xuoi THAT.

Khoi 1 cua KE_HOACH_XAY.md. Cau hoi duy nhat file nay tra loi:

    trong N cau mo ta co che lay tu chinh kho tai lieu, ngu phap noi duoc bao nhieu?

Phai chay TRUOC khi them toan hang moi (lay moc), roi chay lai SAU (do dich chuyen).
Khong co moc thi con so sau vo nghia.

Ba trang thai, khong phai hai:
    NOI_DUOC      doc_hieu ra dieu kien, kiem_khai_bao sach, va phan bo sot < 25% cau
    NOI_MOT_PHAN  ra dieu kien nhung ngu phap NUOT mat phan con lai cua cau
    KHONG_NOI     ra 0 dieu kien

`NOI_MOT_PHAN` la trang thai quan trong nhat: no la cho ngu phap im lang lam mat
ve cua cau ma khong bao gi. Do 11/09 tren mot cau thu: "mua khi RSI 14 duoi 30 VA
gia dong cua tren EMA 200" -> chi ra `rsi < 30`, ve EMA bi bo, khong mot loi nhac.

Dau ra: reports/CORPUS_NGU_PHAP.json
    moc       ty le ba trang thai
    tu_vung   HANG DOI TU VUNG THIEU - tu nao xuat hien nhieu trong cau KHONG_NOI
              duoc ma CHI_BAO_CO khong co. Day la ban do cho mu cua he, do chinh
              dong chay ve ra chu khong phai do Claude doan.

Chay:  python _corpus_ngu_phap.py [so_cau]        (mac dinh 150)
"""
from __future__ import annotations

import json
import random
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import doc_hieu as DH  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

RA = GOC / "reports" / "CORPUS_NGU_PHAP.json"
HAT = 20260911  # co dinh de hai lan chay lay CUNG corpus - neu khong thi khong so sanh duoc

#: Tu khoa bao hieu mot cau DANG mo ta co che (khong phai van tan man).
DAU_HIEU = re.compile(
    r"\b(buy|sell|long|short|enter|entry|exit|close|signal|cross(?:es|ing)?|above|below|"
    r"when|if|break(?:s|out)?|mua|ban|vao lenh|thoat|tin hieu|cat len|cat xuong|vuot|"
    r"duoi|tren|khi)\b",
    re.I,
)

#: Tu vung PHUONG PHAP ma CHI_BAO_CO chua noi duoc. Dung de phan loai hang doi,
#: khong dung de cham diem - cham diem la viec cua `kiem_khai_bao`.
NHOM_TU = {
    "song": r"\b(zigzag|zig-zag|swing (?:high|low|point)|impulse|retrace(?:ment)?|"
            r"pullback|wave|elliott|leg|higher high|lower low|hh|hl|lh|ll|"
            r"song|dinh truoc|day truoc|chan day|chan hoi|buoc song)\b",
    "nen": r"\b(engulf(?:ing)?|pin ?bar|inside bar|outside bar|doji|hammer|"
           r"shooting star|marubozu|harami|morning star|evening star|"
           r"nhan chim|nen bao trum|rau nen|bong nen|nen nhan)\b",
    "hinh_hoc": r"\b(gann|square of nine|sq9|fib(?:onacci)?|golden ratio|"
                r"0\.618|61\.8|trend ?line|channel|pitchfork|angle|"
                r"hinh hoc|duong xu huong|kenh gia|goc)\b",
    "vung": r"\b(support|resistance|supply|demand zone|order ?block|"
            r"fair value gap|fvg|imbalance|liquidity|poc|value area|"
            r"vung cung|vung cau|vung ho tro|vung khang cu|khoang trong)\b",
    "lien_ma": r"\b(correlation|correlated|divergence between|spread between|"
               r"lead(?:s|ing)? (?:the )?(?:market|index)|dxy|risk[- ]o[nf]f|"
               r"tuong quan|dan dat|lien thi truong)\b",
    "khoi_luong": r"\b(volume profile|delta|order flow|footprint|cvd|"
                  r"cum delta|khoi luong theo gia)\b",
}
NHOM_TU = {k: re.compile(v, re.I) for k, v in NHOM_TU.items()}


#: Rac khong phai van xuoi: the HTML, trich dan tap chi, dong code.
RAC = re.compile(r"[<>{}]|\$\.|https?://|\bJournal\b|\bpp\.\b|\bdoi:|^\s*[\[\(]\d")


def _lay_cau(so_can: int) -> tuple[list, list]:
    """Rut cau tu bang `noi_dung`, tach lam HAI TANG.

    A  `loai_cau` NHAN  -> he biet day la mot luat. Do o day la do NGU PHAP.
    B  `loai_cau` TU CHOI nhung cau co tu vung phuong phap (song/nen/vung/hinh hoc)
       -> do o day la do KHAU DOC, khong phai ngu phap. Tron hai tang lai thi
       ngu phap bi do oan cho thu ma bo doc lam roi.
    """
    db = sqlite3.connect(GOC / "nao.db")
    dong = db.execute(
        "SELECT url, van_ban FROM noi_dung "
        "WHERE kieu IS NOT 'ma_nguon' AND length(coalesce(van_ban,'')) > 600 "
        "ORDER BY id"
    ).fetchall()
    db.close()

    a, b, thay = [], [], set()
    for url, vb in dong:
        # `_chuan` TRUOC khi tach cau - day la thu `doc_bai` lam. Khong goi no
        # thi bo do chay tren mot van ban KHAC voi van ban duong chay that thay,
        # va moi con so deu khong noi ve he dang chay.
        for _, cau in DH.cac_cau(DH._chuan(vb or "")):
            c = cau.strip()
            if not (40 <= len(c) <= 320) or RAC.search(c):
                continue
            khoa = re.sub(r"\s+", " ", c.lower())[:120]
            if khoa in thay:
                continue
            thay.add(khoa)

            try:
                nhan = DH.loai_cau(c)
            except Exception:
                nhan = None
            if nhan:
                a.append((url or "", c, nhan))
            elif DAU_HIEU.search(c) and any(rx.search(c) for rx in NHOM_TU.values()):
                b.append((url or "", c, None))

    r = random.Random(HAT)
    r.shuffle(a)
    r.shuffle(b)
    return a[:so_can], b[:so_can]


def _do_mot_cau(cau: str) -> tuple[str, list[str], int]:
    """-> (trang_thai, loi_kiem_khai_bao, so_ky_tu_bi_bo_sot)"""
    try:
        ket = DH.dieu_kien_trong_cau(cau)
    except Exception as e:  # bo doc nem loi cung la mot ket qua, khong phai su co
        return "KHONG_NOI", [f"doc_hieu nem loi: {type(e).__name__}"], len(cau)

    dieu_kien, con_lai = (ket if isinstance(ket, (list, tuple)) and len(ket) == 2
                          else (ket, ""))
    if not dieu_kien:
        return "KHONG_NOI", [], len(cau)

    # `co_che` va `ho` la truong BAT BUOC cua kiem_khai_bao. Thieu chung thi
    # MOI cau deu bi bac, va bang doc y het "bo doc hong" - toi da suyt ket luan
    # dung nhu vay luc 19:40 ngay 11/09, trong khi bo doc ra dieu kien cho 12/150.
    spec = {"ten": "thu", "ho": "xu_huong", "chieu": 1, "giu": 1,
            "vao": list(dieu_kien), "ra": [],
            "co_che": "cau do corpus - khong dang ky, chi de kiem cu phap"}
    loi = NP.kiem_khai_bao(spec)
    bo_sot = len((con_lai or "").strip())

    if loi:
        return "KHONG_NOI", loi, bo_sot
    if bo_sot > len(cau) * 0.25:
        return "NOI_MOT_PHAN", [], bo_sot
    return "NOI_DUOC", [], bo_sot


def _do_tang(corpus: list) -> tuple[Counter, Counter, dict, list]:
    dem, tu_vung = Counter(), Counter()
    vi_du: dict[str, list] = {"KHONG_NOI": [], "NOI_MOT_PHAN": []}
    chi_tiet = []
    for url, cau, nhan in corpus:
        tt, loi, bo_sot = _do_mot_cau(cau)
        dem[tt] += 1
        if tt != "NOI_DUOC":
            for nhom, rx in NHOM_TU.items():
                if rx.search(cau):
                    tu_vung[nhom] += 1
            if len(vi_du[tt]) < 10:
                vi_du[tt].append({"cau": cau, "loi": loi[:3], "nguon": url})
        chi_tiet.append({"tt": tt, "bo_sot": bo_sot, "nhan": nhan,
                         "cau": cau[:200], "nguon": url})
    return dem, tu_vung, vi_du, chi_tiet


def _hinh_dang_kho() -> dict:
    """Toan hang nao THUC SU duoc dung trong 689 co che da co.

    Day la phep do dang tin nhat trong file nay: khong phu thuoc bo doc, khong
    phu thuoc cach chon corpus. No do HINH DANG DA THANH HINH cua ngu phap.
    """
    dung = Counter()
    ho = Counter()

    def di(nut):
        if isinstance(nut, dict):
            if "chi_bao" in nut:
                dung[str(nut["chi_bao"])] += 1
            for v in nut.values():
                di(v)
        elif isinstance(nut, list):
            for v in nut:
                di(v)

    try:
        kho = NP.doc_kho()
    except Exception as e:
        return {"loi": f"doc_kho nem loi: {e}"}
    for spec in kho:
        ho[str(spec.get("ho", "?"))] += 1
        di(spec.get("vao", []))
        di(spec.get("ra", []))

    chua_dung = sorted(set(map(str, NP.CHI_BAO_CO)) - set(dung))
    return {
        "so_co_che": len(kho),
        "theo_ho": ho.most_common(),
        "toan_hang_duoc_dung": dung.most_common(),
        "toan_hang_CHUA_AI_DUNG": chua_dung,
    }


def chay(so_can: int = 150) -> dict:
    tang_a, tang_b = _lay_cau(so_can)
    if len(tang_a) < 30:
        print(f"CHUA_DO_DUOC: chi rut duoc {len(tang_a)} cau o tang A. "
              f"Kiem `doc_hieu.loai_cau` truoc khi tin so nay.")

    dem_a, tu_a, vd_a, ct_a = _do_tang(tang_a)
    dem_b, tu_b, vd_b, ct_b = _do_tang(tang_b)
    tong_a = sum(dem_a.values()) or 1

    ket = {
        "luc": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hat": HAT,
        "toan_hang_hien_co": len(NP.CHI_BAO_CO),
        "tang_A_do_NGU_PHAP": {
            "so_cau": tong_a,
            "moc": {k: round(dem_a[k] / tong_a, 4)
                    for k in ("NOI_DUOC", "NOI_MOT_PHAN", "KHONG_NOI")},
            "dem": dict(dem_a),
            "tu_vung_thieu": tu_a.most_common(),
            "vi_du": vd_a,
        },
        "tang_B_do_KHAU_DOC": {
            "so_cau": sum(dem_b.values()),
            "ghi_chu": "Cau co tu vung phuong phap ma `loai_cau` TU CHOI. "
                       "Truot o day la loi KHAU DOC, khong phai ngu phap.",
            "tu_vung_thieu": tu_b.most_common(),
            "vi_du": vd_b,
        },
        "tang_C_hinh_dang_kho": _hinh_dang_kho(),
        "chi_tiet_A": ct_a,
        "chi_tiet_B": ct_b[:80],
    }
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"toan hang hien co: {len(NP.CHI_BAO_CO)}")
    print(f"\nTANG A - do NGU PHAP ({tong_a} cau `loai_cau` nhan la luat)")
    for k in ("NOI_DUOC", "NOI_MOT_PHAN", "KHONG_NOI"):
        print(f"  {k:14s} {dem_a[k]:4d}  {dem_a[k]/tong_a:6.1%}")
    print(f"\nTANG B - do KHAU DOC ({sum(dem_b.values())} cau co tu vung phuong phap "
          f"ma `loai_cau` tu choi)")
    for nhom, n in tu_b.most_common():
        print(f"  {nhom:12s} {n}")
    if tu_a:
        print("\nhang doi tu vung thieu (tang A):")
        for nhom, n in tu_a.most_common():
            print(f"  {nhom:12s} {n}")
    c = ket["tang_C_hinh_dang_kho"]
    if "loi" not in c:
        print(f"\nTANG C - hinh dang THAT cua {c['so_co_che']} co che trong kho")
        print("  ho:        " + " · ".join(f"{k} {v}" for k, v in c["theo_ho"][:8]))
        print("  toan hang: " + " · ".join(f"{k} {v}" for k, v in
                                           c["toan_hang_duoc_dung"][:10]))
        print(f"  CHUA AI DUNG ({len(c['toan_hang_CHUA_AI_DUNG'])}): "
              + ", ".join(c["toan_hang_CHUA_AI_DUNG"]))
    print(f"\n-> {RA}")
    return ket


if __name__ == "__main__":
    chay(int(sys.argv[1]) if len(sys.argv) > 1 else 150)
