# -*- coding: utf-8 -*-
"""_truy_chang_4_5.py - VI SAO 1.035/1.418 CO CHE CHUA BAO GIO THANH GIA THUYET?

Viec H1a cua `KE_HOACH_HOAN_THIEN.md`. Day la chang HEP NHAT cua ca day chuyen:

    co che 1.418  ->  gia thuyet 383  (27,0%)

Ba kha nang, va PHAI phan biet bang so chu khong duoc doan - vi ba cai can ba
cach sua hoan toan khac nhau:

  (i)   TRUOT `kiem_khai_bao`   -> loi cu phap trong chinh khai bao
  (ii)  KHONG SINH DUOC tin hieu -> goi duoc nhung tra chuoi rong/hang so
  (iii) CHUA AI GOI              -> khai bao lanh lan, chi la khong ai dua vao cong

Neu phan lon la (iii) thi sua la CHAY, khong phai VIET. Neu phan lon la (i) thi
phai sua bo boc. Doan nham o day la dot ca ngay.

Chay:  python _truy_chang_4_5.py [so_luong]
Ra:    reports/TRUY_CHANG_4_5.json
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402

from nhan import du_lieu as DL  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402
from nhan import so as SO  # noqa: E402

RA = LAB / "reports" / "TRUY_CHANG_4_5.json"
MA, KHUNG = "XM_US500CASH", "D1"


def main(argv: list[str]) -> int:
    gh = int(argv[0]) if argv else 0
    kho = NP.doc_kho()

    # Ten nao DA co mat trong bang gia_thuyet? `gt_ma` co dang
    # "<MA>.<KHUNG>.<ten_co_che>.<bien_the>" nen so bang CHUOI CON.
    gt = [r["ma"] if "ma" in r.keys() else "" for r in SO.nhieu("SELECT * FROM gia_thuyet")]
    gt_txt = "\n".join(str(x) for x in gt)
    da_dang_ky = set()
    for s in kho:
        t = str(s.get("ten") or "")
        if t and t in gt_txt:
            da_dang_ky.add(t)

    chua = [s for s in kho if str(s.get("ten") or "") not in da_dang_ky]
    print("kho %d co che · da co mat trong gia_thuyet: %d · CHUA: %d"
          % (len(kho), len(da_dang_ky), len(chua)))
    if gh:
        chua = chua[:gh]

    df = DL.nap(MA, KHUNG)
    print("nen do tin hieu: %s %s · %d bar" % (MA, KHUNG, len(df)))

    dem = Counter()
    vi_du = {}
    chi_tiet = []
    t0 = time.time()
    for i, s in enumerate(chua, 1):
        ten = str(s.get("ten") or "?")
        loi = NP.kiem_khai_bao(s)
        if loi:
            ly_do = "i_truot_kiem_khai_bao"
            ghi = loi[0][:120]
        else:
            try:
                v = np.asarray(NP.sinh_tu_spec(s, df), float)
                kh = float(np.mean(np.abs(v) > 0))
                if kh <= 0.0:
                    ly_do, ghi = "ii_khong_kich_hoat", "ty le kich hoat = 0"
                elif kh >= 0.999:
                    ly_do, ghi = "ii_kich_hoat_hang_so", "kich hoat 100% - la mua-giu doi ten"
                else:
                    ly_do, ghi = "iii_chua_ai_goi", "kich hoat %.1f%% - khai bao LANH LAN" % (kh * 100)
            except Exception as e:
                ly_do, ghi = "ii_nem_loi", "%s: %s" % (type(e).__name__, str(e)[:90])
        dem[ly_do] += 1
        vi_du.setdefault(ly_do, []).append({"ten": ten, "ghi": ghi})
        chi_tiet.append({"ten": ten, "ly_do": ly_do, "ghi": ghi,
                         "ho": s.get("ho"), "chieu": s.get("chieu")})
        if i % 200 == 0:
            print("  ... %d/%d (%.0fs)" % (i, len(chua), time.time() - t0), flush=True)

    tong = sum(dem.values())
    print("\n%-26s %7s %7s" % ("ly do", "so", "ty le"))
    print("-" * 44)
    for k, n in dem.most_common():
        print("%-26s %7d %6.1f%%" % (k, n, 100 * n / max(tong, 1)))

    print("\nVI DU moi loai:")
    for k in dem:
        print("  --- %s" % k)
        for x in vi_du[k][:3]:
            print("      %-42s %s" % (x["ten"][:42], x["ghi"][:70]))

    lanh = dem.get("iii_chua_ai_goi", 0)
    print("\n>>> KHAI BAO LANH LAN, chi thieu NGUOI GOI: %d / %d = %.1f%%"
          % (lanh, tong, 100 * lanh / max(tong, 1)))
    print("    Neu con so nay lon thi H1 la viec CHAY, khong phai viec VIET.")

    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(
        {"kho": len(kho), "da_dang_ky": len(da_dang_ky), "chua": tong,
         "nen": "%s.%s" % (MA, KHUNG), "dem": dict(dem),
         "ty_le_lanh_lan": round(lanh / max(tong, 1), 4),
         "vi_du": {k: v[:8] for k, v in vi_du.items()},
         "chi_tiet": chi_tiet},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s  (%.0fs)" % (RA, time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
