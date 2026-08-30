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


def quet(khung: str = "D1", cac_mau=None, cac_ma=None) -> dict:
    t0 = time.time()
    cac_mau = list(cac_mau or sorted(MAU.MAU))
    cac_ma = list(cac_ma or PV.kho_du_bar(khung))
    ra = {"khung": khung, "so_mau": len(cac_mau), "so_ma": len(cac_ma),
          "ma": cac_ma, "pham_vi": {}, "o": {}, "tong": {}}

    for ten in cac_mau:
        try:
            pv = SL.pham_vi_cua(ten)
        except Exception as e:
            pv = {"ket_luan": "LOI", "ly_do": f"{type(e).__name__}: {str(e)[:60]}"}
        ra["pham_vi"][ten] = {"ket_luan": pv.get("ket_luan"),
                              "ly_do": str(pv.get("ly_do"))[:150]}
        print(f"[{time.strftime('%H:%M:%S')}] {ten:18s} pham_vi={pv.get('ket_luan')}",
              flush=True)
        for ma in cac_ma:
            SL.xoa_bo_dem()
            try:
                r = SL.chay_pheu(ten, {}, ma, khung, pham_vi=pv, da_chay=None)
            except Exception as e:
                r = {"ket_luan": "LOI", "vong": "?",
                     "ly_do": f"{type(e).__name__}: {str(e)[:60]}", "do": {}}
            ra["o"][f"{ten}|{ma}"] = {
                "ket_luan": r.get("ket_luan"), "vong": r.get("vong"),
                "ly_do": str(r.get("ly_do"))[:80],
                "sharpe": (r.get("do") or {}).get("sharpe"),
                "sharpe_mua_giu": (r.get("do") or {}).get("sharpe_mua_giu"),
                "so_lenh": (r.get("do") or {}).get("so_lenh")}
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
    ra = quet(khung)
    (LAB / ten_ra).write_text(json.dumps(ra, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    print("TONG:", ra["tong"], f"({ra['giay']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
