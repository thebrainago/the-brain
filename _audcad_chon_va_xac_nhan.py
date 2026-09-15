# -*- coding: utf-8 -*-
"""_audcad_chon_va_xac_nhan.py - CHON tren nua dau, XAC NHAN tren nua sau.

Chu du an 15/09/2026: *"tao ra mot hoac chuoi he thong toi uu cho audcad"*.

## VI SAO PHAI THEO THU TU NAY

Quet toan kho tren HOLDOUT roi lay dinh bang la **cuc dai trong 3.140 phep
thu** - va bai hoc [[so-cuc-dai-phai-so-cung-co-mau]] noi ro no thoi p sai toi
mot bac. Thu tu dung la: CHON tren nua dau (2016-2021), roi XEM cai da chon
lam duoc gi tren nua sau (2021-2026) ma khong duoc chon lai.

Cai tinh duoc tu do la mot con so that: trong N cai chon tren TRAIN, bao nhieu
cai con hon moc tren HOLDOUT - va so do so voi TY LE NEN cua ca kho.

## MOT MAY MAN CUA CUA SO NAY

Moc mua-giu tren TRAIN la **-0,06%/nam** - gan nhu phang. Tuc 2016-2021 AUDCAD
khong troi, nen mot he thang moc o day khong the la "drift doi lot edge".
Tren HOLDOUT moc la +1,13%/nam (cap tang), nen o do moc cao hon va kho hon.

Chay:  python _audcad_chon_va_xac_nhan.py [--top 40]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

TRAIN = ("reports/TESTER_AUDCAD_H4_TRAIN.json", "2016.01.01", "2021.03.19")
HOLD = ("reports/TESTER_AUDCAD_H4_HOLDOUT.json", "2021.03.19", "2026.07.29")

#: So lenh toi thieu de mot ket qua co nghia. Bai hoc: "ung vien UK100 tot nhat
#: chi co 32 lenh" - mot Sharpe dep tren 12 lenh khong noi len gi.
LENH_TOI_THIEU = 30


def doc(duong: str, tu: str, den: str) -> tuple[dict, float]:
    import chay_tester_kho as C
    r = json.loads((LAB / duong).read_text(encoding="utf-8"))
    nam = C._so_nam(tu, den)
    d = {}
    for x in r["ket"]:
        v = C.chuan_hoa_cung_rui_ro(x["lai"], x["dd_pct"], nam)
        if v is not None:
            d[x["ten"]] = {"pct": v, "lenh": int(x["lenh"]),
                           "sharpe": float(x["sharpe"]), "pf": float(x["pf"]),
                           "dd": float(x["dd_pct"])}
    moc = max(d.get("__mua_giu__", {}).get("pct", -9e9),
              d.get("__ban_giu__", {}).get("pct", -9e9))
    return d, moc


def main() -> int:
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 40
    a, moc_a = doc(*TRAIN)
    b, moc_b = doc(*HOLD)
    chung = {k for k in a if k in b and not k.startswith("__")}
    print("=" * 74)
    print("AUDCAD H4 - CHON TREN NUA DAU, XAC NHAN TREN NUA SAU")
    print("=" * 74)
    print("co che do duoc tren CA HAI cua so: %d" % len(chung))
    print("moc TRAIN  (2016-2021): %+.2f%%/nam   <- gan nhu PHANG, khong troi"
          % moc_a)
    print("moc HOLDOUT(2021-2026): %+.2f%%/nam" % moc_b)
    print()

    # TY LE NEN: bao nhieu % ca kho hon moc tren HOLDOUT, khong chon gi ca.
    du_lenh = {k for k in chung if b[k]["lenh"] >= LENH_TOI_THIEU}
    nen = [k for k in du_lenh if b[k]["pct"] > moc_b]
    p_nen = len(nen) / max(len(du_lenh), 1)
    print("TY LE NEN (khong chon gi): %d/%d = **%.1f%%** co che hon moc tren"
          " HOLDOUT" % (len(nen), len(du_lenh), 100 * p_nen))
    print("   (chi tinh co che co >= %d lenh tren HOLDOUT)" % LENH_TOI_THIEU)
    print()

    # CHON tren TRAIN: hon moc + du lenh, xep theo %/nam.
    ung = [k for k in du_lenh
           if a[k]["pct"] > moc_a and a[k]["lenh"] >= LENH_TOI_THIEU]
    ung.sort(key=lambda k: -a[k]["pct"])
    chon = ung[:top]
    song = [k for k in chon if b[k]["pct"] > moc_b]
    print("CHON tren TRAIN: %d co che hon moc & du lenh; lay top %d"
          % (len(ung), len(chon)))
    print("XAC NHAN tren HOLDOUT: **%d/%d song** = %.1f%%   (nen %.1f%%)"
          % (len(song), len(chon), 100 * len(song) / max(len(chon), 1),
             100 * p_nen))
    boi = (len(song) / max(len(chon), 1)) / max(p_nen, 1e-9)
    print("   -> **%.2f lan** ty le nen" % boi)
    print()
    print("%-42s %9s %9s %6s %6s" % ("co che", "TRAIN", "HOLDOUT", "lenh", "DD%"))
    print("-" * 78)
    for k in sorted(chon, key=lambda x: -b[x]["pct"])[:25]:
        print("%-42s %+8.2f %+9.2f %6d %6.2f%s"
              % (k[:42], a[k]["pct"], b[k]["pct"], b[k]["lenh"], b[k]["dd"],
                 "  <- song" if b[k]["pct"] > moc_b else ""))

    ra = LAB / "reports" / "AUDCAD_CHON_XAC_NHAN.json"
    ra.write_text(json.dumps(
        {"moc_train": moc_a, "moc_holdout": moc_b, "ty_le_nen": p_nen,
         "so_chon": len(chon), "so_song": len(song), "boi_so_nen": boi,
         "song": [{"ten": k, "train": a[k], "holdout": b[k]} for k in song]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s" % ra.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
