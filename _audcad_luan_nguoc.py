# -*- coding: utf-8 -*-
"""_audcad_luan_nguoc.py - 114 ho so signal AUDCAD -> CONG THUC cua he song sot.

Chu du an 15/09/2026: *"Lung suc khap moi noi tren the gioi nay system hieu qua
voi audcad. Hay tim moi nguon tai lieu, truy nguoc moi lich su cua nhung he
thong giao dich audcad."*

## Cai nay do duoc gi ma backtest khong do duoc

Nguoi ban tin hieu giau duoc LUAT nhung khong giau duoc DUONG VON, MUC TAI va
THOI GIAN SONG. 114 ho so AUDCAD la 114 lan mot nguoi that dem tien that ra thu
mot y tuong tren dung cap nay - va ta doc duoc ket cuc.

## HAI CAI BAY PHAI NOI TRUOC MOI CON SO

1. **SONG SOT.** Day la nhung signal CON DUOC LIET KE. Cai chet va bi go khoi
   san khong co trong mau. Nen moi ty le "song duoc bao nhieu %" o day deu la
   CHAN TREN, va khoang cach toi su that khong do duoc tu chinh mau nay.
2. **`song_ngay` KHONG phai tuoi tho** - no la tuoi DEN HOM DO. Mot signal 60
   ngay co the dang khoe. Nen so sanh phai lam trong cung mot bac tuoi, hoac
   dung no lam BIEN PHAN NHOM chu khong lam ket qua.

Chay:  python _audcad_luan_nguoc.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

#: Nguong "song lau" - 2 nam. Cung moc ma [[luan-nguoc-400-signal-audcad]] dung.
SONG_LAU_NGAY = 730

#: Truong so de so sanh hai nhom.
TRUONG = ("so_lenh", "giu_phut", "thang_pct", "pf", "sharpe", "tai_dinh_pct",
          "dd_pct", "tang_truong_pct", "nhoi_khi_lo", "bac_tai", "tai_deu",
          "cat_sach", "lech_trai", "tai_trung_vi_pct")


def _so(h, k):
    v = h.get(k)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


def _pv(ds, k, q=50):
    v = [x for x in (_so(h, k) for h in ds) if x is not None]
    return float(np.percentile(v, q)) if v else float("nan")


def nap() -> list:
    d = json.loads((LAB / "reports" / "signal_ho_so.json").read_text(encoding="utf-8"))
    ds = d if isinstance(d, list) else (d.get("ho_so") or list(d.values()))
    return [h for h in ds if isinstance(h, dict)]


def loc_audcad(ds: list) -> list:
    return [h for h in ds if "AUDCAD" in str(h.get("symbol") or "")]


def _mann_whitney(a: list, b: list) -> float | None:
    """p-value hai duoi, xap xi chuan. Mau nho thi dung tin con so nay.

    Dung phep thu THEO HANG chu khong theo trung binh: cac truong o day (tang
    truong %, so lenh) co duoi rat day, va mot ho so ngoai le se keo trung binh
    di bat cu dau.
    """
    from math import sqrt
    a = [x for x in a if x is not None]
    b = [x for x in b if x is not None]
    n1, n2 = len(a), len(b)
    if n1 < 5 or n2 < 5:
        return None
    tat = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    hang, i = {}, 0
    while i < len(tat):
        j = i
        while j + 1 < len(tat) and tat[j + 1][0] == tat[i][0]:
            j += 1
        tb = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            hang[k] = tb
        i = j + 1
    r1 = sum(hang[k] for k in range(len(tat)) if tat[k][1] == 0)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    sd = sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    if sd <= 0:
        return None
    z = (u1 - mu) / sd
    try:
        from statistics import NormalDist
        return 2 * (1 - NormalDist().cdf(abs(z)))
    except Exception:
        return None


def main() -> int:
    tat = nap()
    au = loc_audcad(tat)
    khac = [h for h in tat if h not in au]
    print("=" * 74)
    print("114 HO SO SIGNAL AUDCAD - LUAN NGUOC CONG THUC")
    print("=" * 74)
    print("AUDCAD %d / %d ho so (%.1f%%)" % (len(au), len(tat),
                                             100 * len(au) / max(len(tat), 1)))

    lau = [h for h in au if (_so(h, "song_ngay") or 0) >= SONG_LAU_NGAY]
    tre = [h for h in au if (_so(h, "song_ngay") or 0) < SONG_LAU_NGAY]
    print("  song >= %d ngay: **%d**   |  tre hon: %d"
          % (SONG_LAU_NGAY, len(lau), len(tre)))
    print()
    print("CANH BAO SONG SOT: day la signal CON DUOC LIET KE. Cai chet va bi go")
    print("khoi san khong co trong mau, nen moi ty le o day la CHAN TREN.")
    print()

    print("%-20s %12s %12s %10s" % ("truong", "song LAU", "tre hon", "p (hang)"))
    print("-" * 60)
    dat = []
    for k in TRUONG:
        a = [_so(h, k) for h in lau]
        b = [_so(h, k) for h in tre]
        p = _mann_whitney(a, b)
        tag = ""
        if p is not None and p < 0.05:
            tag = "  <-"
            dat.append((k, _pv(lau, k), _pv(tre, k), p))
        print("%-20s %12.4g %12.4g %10s%s"
              % (k, _pv(lau, k), _pv(tre, k),
                 "-" if p is None else "%.4f" % p, tag))

    print()
    print("-" * 74)
    if not dat:
        print("KHONG truong nao tach duoc hai nhom o p<0,05.")
        print("Doc dung: mau nay KHONG noi duoc cai gi lam mot he AUDCAD song")
        print("lau. Do la mot ket qua, khong phai mot that bai cua phep do.")
    else:
        print("CONG THUC DOC DUOC (%d truong tach duoc, p<0,05):" % len(dat))
        for k, a, b, p in sorted(dat, key=lambda x: x[3]):
            print("   %-20s song lau %10.4g  vs  tre %10.4g   (p=%.4f)"
                  % (k, a, b, p))
        print()
        print("   %d truong x 1 phep thu moi truong = hieu chinh Bonferroni:"
              % len(TRUONG))
        for k, a, b, p in sorted(dat, key=lambda x: x[3]):
            print("      %-20s p x %d = %.4f   %s"
                  % (k, len(TRUONG), p * len(TRUONG),
                     "VAN DAT" if p * len(TRUONG) < 0.05 else "khong con dat"))

    # --- AUDCAD co KHAC cac tai san khac khong ---
    print()
    print("-" * 74)
    print("AUDCAD co KHAC phan con lai khong (cung phep thu):")
    for k in ("nhoi_khi_lo", "giu_phut", "thang_pct", "pf", "song_ngay",
              "dd_pct", "bac_tai"):
        p = _mann_whitney([_so(h, k) for h in au], [_so(h, k) for h in khac])
        print("   %-14s AUDCAD %10.4g  vs  khac %10.4g   p=%s%s"
              % (k, _pv(au, k), _pv(khac, k),
                 "-" if p is None else "%.4f" % p,
                 "  <-" if p is not None and p < 0.05 else ""))

    ra = LAB / "reports" / "AUDCAD_LUAN_NGUOC.json"
    ra.write_text(json.dumps(
        {"so_ho_so": len(au), "song_lau": len(lau), "tre": len(tre),
         "truong_tach_duoc": [{"truong": k, "song_lau": a, "tre": b, "p": p}
                              for k, a, b, p in dat]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s" % ra.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
