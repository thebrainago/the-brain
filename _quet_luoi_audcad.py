# -*- coding: utf-8 -*-
"""Quet luoi DCA hai chieu tren AUDCAD H4, spacing lay tu PHAN VI DO DUOC.

Do 18/09 tren 20.902 bar H4: gia lui truoc khi ve lai muc vao —
p90 0,325% (~29 pip) · p99 0,711% (~64 pip) · p99,9 2,054% (~185 pip) ·
max 13,202% (~1.188 pip, ket 1.527 bar).

Nen buoc luoi quet quanh 20-65 pip, va he_so_buoc >1 de ladder song duoc
qua cai duoi do. Tach NUA DAU / NUA SAU: cau hinh nao chi song o nua dau
la overfit.
"""
import sys, json, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import du_lieu as DL, luoi as L

VON = 10_000.0

def do_mot(df, **kw):
    ts = L.ThamSo(**kw)
    kq = L.chay(df, ts, VON)
    return L.chi_so(kq, VON)

def main():
    df = DL.nap("AUDCAD", khung="H4")
    n = len(df)
    nua = n // 2
    train, hold = df.iloc[:nua], df.iloc[nua:]
    print("H4: %d bar | train %d | holdout %d" % (n, len(train), len(hold)))

    luoi_ts = []
    for buoc, hs, tp, tia in itertools.product(
            (20.0, 30.0, 45.0, 65.0), (1.0, 1.3, 1.5), (30.0, 45.0, 60.0), (False, True)):
        luoi_ts.append(dict(buoc=buoc, he_so_buoc=hs, tp=tp, tia_lenh=tia,
                            bien_cap=4.0, cap_moi_bar=1 if tia else 999,
                            che_do="hai_chieu", tran_tang=12, lot=0.01,
                            buoc_tran=400.0))
    print("quet %d cau hinh...\n" % len(luoi_ts))

    ra = []
    for i, kw in enumerate(luoi_ts):
        try:
            a = do_mot(train, **kw)
            b = do_mot(hold, **kw)
        except Exception as e:
            print("  loi %s: %s" % (kw, str(e)[:60])); continue
        ra.append({"ts": kw, "train": a, "hold": b})
        if (i + 1) % 12 == 0:
            print("  ...%d/%d" % (i + 1, len(luoi_ts)))

    song = [x for x in ra if not x["train"]["chay"] and not x["hold"]["chay"]]
    print("\n%d/%d cau hinh KHONG chay tai khoan o ca hai nua" % (len(song), len(ra)))
    song.sort(key=lambda x: -min(x["train"]["calmar"], x["hold"]["calmar"]))
    print("\n%-38s %9s %8s %9s %8s %7s" % ("cau hinh", "train%/nam", "trainDD", "hold%/nam", "holdDD", "tang"))
    for x in song[:14]:
        t, h, k = x["train"], x["hold"], x["ts"]
        print("%-38s %9.2f %8.1f %9.2f %8.1f %7d"
              % ("buoc%g hs%g tp%g %s" % (k["buoc"], k["he_so_buoc"], k["tp"],
                                          "tia" if k["tia_lenh"] else "---"),
                 t["loi_suat_nam_pct"], t["maxdd_pct"],
                 h["loi_suat_nam_pct"], h["maxdd_pct"], max(t["tang_max"], h["tang_max"])))
    Path("reports").mkdir(exist_ok=True)
    json.dump(ra, open("reports/LUOI_AUDCAD_H4_18092026.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print("\nda ghi reports/LUOI_AUDCAD_H4_18092026.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
