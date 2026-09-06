# -*- coding: utf-8 -*-
"""_z5_theo_nam.py - LAI CO DON HET VAO MOT HAI NAM KHONG?

Bai nay da ha be bot Session V3: 93% lai nam o 2024+, va bang tong 6,5 nam
trong rat dep [[dongdongtv-dca-bot]]. Mot he thang tren ca ky nhung chi lai o
mot hai nam thi khong phai he, la mot lan trung.

Chay ca ban THAT lan cac ban DICH cho tung nam - de moi nam co moc so sanh
rieng, khong phai chi mot con lai/lo tran troi.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _placebo_tester as P     # noqa: E402

P.HE = ["mean_reversion_z5"]
P.DICH = tuple(range(3, 125, 4))          # 31 ban dich -> p san 1/32

MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
NAM = [(str(n), "%d.01.01" % n, "%d.01.01" % (n + 1)) for n in range(2012, 2026)]
NAM.append(("2026", "2026.01.01", "2026.07.29"))

ra = {}
for ten, tu, den in NAM:
    r = P.chay(MA, tu, den)
    if r.get("loi") or not r.get("he"):
        print("  %s: %s" % (ten, r.get("loi", "khong co ket qua")))
        continue
    ra[ten] = r["he"].get("mean_reversion_z5")

Path("reports/Z5_THEO_NAM_%s.json" % MA).write_text(
    json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")

print("\n\n===== %s : mean_reversion_z5 theo NAM =====" % MA)
print("%6s %6s %10s %10s %8s" % ("nam", "lenh", "lai", "dich_tv", "p"))
tong = 0.0
for n, v in ra.items():
    if not v:
        continue
    tong += v["that"]["lai"]
    print("%6s %6d %10.2f %10.2f %8.3f"
          % (n, v["that"]["lenh"], v["that"]["lai"], v["dich_trung_vi"], v["p"]))
duong = [v for v in ra.values() if v and v["that"]["lai"] > 0]
print("\nnam duong: %d/%d | tong lai %.2f" % (len(duong), len(ra), tong))
if tong > 0 and ra:
    tot = sorted((v["that"]["lai"] for v in ra.values() if v), reverse=True)
    print("hai nam tot nhat chiem %.0f%% tong lai" % (100 * sum(tot[:2]) / tong))
