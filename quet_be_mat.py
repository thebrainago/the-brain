# -*- coding: utf-8 -*-
"""Quet TANG KHAM PHA tren toan be mat: moi co che x moi tai san, khung D1.

Chi chay V0-V3. Tang nay KHONG tieu suat FDR (suat chi tieu o V4 confirmation),
nen quet rong o day la mien phi ve ngan sach kiem dinh - cai phai tra la thoi
gian may.

Muc dich: co MOT anh chup ket qua tang kham pha de doi chieu TRUOC va SAU khi
sua bo nap du lieu / bang chi phi (24/08/2026).

Chay: python quet_be_mat.py [ten_file_ra.json] [--khung D1]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import du_lieu as DL      # noqa: E402
from nhan import mau as MAU         # noqa: E402
from nhan import pham_vi as PV      # noqa: E402
from nhan import sang_loc as SL     # noqa: E402

LAB = Path(__file__).resolve().parent


#: So tien trinh mac dinh khi quet be mat.
#:
#: DO THAT 30/08/2026 tren ca 18 co che x 122 tai san D1 (2.196 o):
#:
#:      1 tien trinh   117,8 s   18,6 o/giay
#:      8 tien trinh    31,1 s   70,6 o/giay   (3,8 lan)
#:     16 tien trinh    27,8 s   79,0 o/giay   (4,2 lan)
#:
#: 8 la diem ngot: 16 chi hon 12% ma ton gap doi tien trinh.
#:
#: PHEP DO NAY LAT MOT NIEM TIN CU CUA DU AN. Ghi chu `may-nghet-bang-thong-ram`
#: ket luan "20 luong chay y het 1 luong" va khuyen KHONG bat dau bang nhan
#: luong. Ket luan do do bang mot bai quet MANG LON nen nghet kenh nho; con mot
#: o cua pheu D1 chi ~128 KB, nam gon trong cache CPU va khong cham toi kenh
#: nho. Hai bai do khac tap lam viec, khong mau thuan nhau - nhung ket luan cu
#: KHONG duoc ap cho duong nay.
SO_TIEN_TRINH = 8


def _quet_mot_mau(doi_so):
    """Chay het mot co che tren moi tai san. Ham muc GOC de Pool pickle duoc.

    Tra ve ca BO DEM `bi_loai`/`cho_them`: moi tien trinh con co bo dem RIENG,
    va `quantlab` co doc `SL.lay_bo_dem()` - khong tra ve thi tien trinh cha mat
    sach phan do va khong ai biet.
    """
    ten, khung, cac_ma = doi_so
    import sys as _s
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).resolve().parent))
    from nhan import sang_loc as SL

    SL.xoa_bo_dem()
    try:
        pv = SL.pham_vi_cua(ten)
    except Exception as e:
        pv = {"ket_luan": "LOI", "ly_do": f"{type(e).__name__}: {str(e)[:60]}"}
    o = {}
    for ma in cac_ma:
        try:
            r = SL.chay_pheu(ten, {}, ma, khung, pham_vi=pv, da_chay=None)
        except Exception as e:
            r = {"ket_luan": "LOI", "vong": "?",
                 "ly_do": f"{type(e).__name__}: {str(e)[:60]}", "do": {}}
        o[f"{ten}|{ma}"] = {
            "ket_luan": r.get("ket_luan"), "vong": r.get("vong"),
            "ly_do": str(r.get("ly_do"))[:80],
            "sharpe": (r.get("do") or {}).get("sharpe"),
            "sharpe_mua_giu": (r.get("do") or {}).get("sharpe_mua_giu"),
            "so_lenh": (r.get("do") or {}).get("so_lenh")}
    return {"mau": ten,
            "pham_vi": {"ket_luan": pv.get("ket_luan"),
                        "ly_do": str(pv.get("ly_do"))[:150]},
            "o": o, "bi_loai": SL.lay_bo_dem(), "cho_them": SL.lay_cho_them()}


def quet(khung: str = "D1", cac_mau=None, cac_ma=None,
         so_tien_trinh: int | None = None) -> dict:
    """Quet tang kham pha tren toan be mat.

    `so_tien_trinh=1` chay tuan tu (de go loi, va de doi chieu voi ban cu).
    """
    t0 = time.time()
    cac_mau = list(cac_mau or sorted(MAU.MAU))
    cac_ma = list(cac_ma or PV.kho_du_bar(khung))
    n = so_tien_trinh if so_tien_trinh is not None else SO_TIEN_TRINH
    n = max(1, min(int(n), len(cac_mau)))

    ra = {"khung": khung, "so_mau": len(cac_mau), "so_ma": len(cac_ma),
          "ma": cac_ma, "pham_vi": {}, "o": {}, "tong": {},
          "so_tien_trinh": n, "bi_loai": [], "cho_them": []}

    viec = [(ten, khung, cac_ma) for ten in cac_mau]
    if n <= 1:
        ket = []
        for v in viec:
            r = _quet_mot_mau(v)
            print(f"[{time.strftime('%H:%M:%S')}] {r['mau']:18s} "
                  f"pham_vi={r['pham_vi']['ket_luan']}", flush=True)
            ket.append(r)
    else:
        import multiprocessing as mp
        with mp.Pool(n) as pool:
            ket = []
            for r in pool.imap_unordered(_quet_mot_mau, viec):
                print(f"[{time.strftime('%H:%M:%S')}] {r['mau']:18s} "
                      f"pham_vi={r['pham_vi']['ket_luan']}", flush=True)
                ket.append(r)

    for r in ket:
        ra["pham_vi"][r["mau"]] = r["pham_vi"]
        ra["o"].update(r["o"])
        ra["bi_loai"].extend(r["bi_loai"])
        ra["cho_them"].extend(r["cho_them"])

    dem: dict = {}
    for v in ra["o"].values():
        dem[v["ket_luan"]] = dem.get(v["ket_luan"], 0) + 1
    ra["tong"] = dem
    ra["giay"] = round(time.time() - t0, 1)
    return ra


def main() -> int:
    ten_ra = "reports/QUET_BE_MAT.json"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        ten_ra = sys.argv[1]
    khung = "D1"
    if "--khung" in sys.argv:
        khung = sys.argv[sys.argv.index("--khung") + 1]
    n = None
    if "--tien-trinh" in sys.argv:
        n = int(sys.argv[sys.argv.index("--tien-trinh") + 1])
    ra = quet(khung, so_tien_trinh=n)
    (LAB / ten_ra).write_text(json.dumps(ra, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    print("TONG:", ra["tong"], f"({ra['giay']}s, {ra['so_tien_trinh']} tien trinh)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
