# -*- coding: utf-8 -*-
"""_so_voi_mua_giu.py - SO O CUNG SUT GIAM, TREN CUNG MOT BO THUC THI.

Quy tac cua du an: mot he chi la phat hien khi no thang MUA-GIU o **cung muc
sut giam**, khong phai cung bien dong va khong phai so lai suat tho
[[cong-ra-tien-la-cong-thu-hai]].

Moc mua-giu o day nam TRONG CHINH EA sinh ra (`dich_mq5.SPEC_MUA_GIU`), nen no
di qua dung mot bo thuc thi: cung spread, cung phi qua dem, cung gio khop, cung
lot. Mot con so mua-giu lay tu chuoi gia la mot moc KHAC.

Quy ve cung sut giam: lai va sut giam deu TUYEN TINH theo lot khi khong cham
ky quy (lot 0,10 tren von 10.000 la don bay ~0,03x - rat xa muc do). Nen nhan
lai cua he voi `DD_muagiu / DD_he` la phep quy dung, khong phai xap xi.

Chay: python _so_voi_mua_giu.py [SYMBOL] [tu] [den]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_tester_kho as C     # noqa: E402

MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
TU = sys.argv[2] if len(sys.argv) > 2 else "2020.05.01"
DEN = sys.argv[3] if len(sys.argv) > 3 else "2026.07.29"

r = C.chay(MA, "D1", tu=TU, den=DEN)
if r.get("loi"):
    print("LOI:", r["loi"])
    raise SystemExit(1)

ket = {x["ten"]: x for x in r["ket"]}
mg = ket.get("__mua_giu__")
if not mg:
    print("KHONG CO moc mua-giu trong bang - khong ket luan gi duoc.")
    raise SystemExit(1)

print("\n%s  %s -> %s" % (MA, TU, DEN))
print("MUA-GIU: %d lenh | lai %.2f | DD %.2f%% | sharpe %.2f"
      % (mg["lenh"], mg["lai"], mg["dd_pct"], mg["sharpe"]))

bang = []
for t, x in ket.items():
    if t == "__mua_giu__" or x["lenh"] < 25 or x["dd_pct"] <= 0:
        continue
    he_so = mg["dd_pct"] / x["dd_pct"]        # quy ve CUNG sut giam
    bang.append({**x, "he_so": he_so, "lai_quy": x["lai"] * he_so,
                 "hon_mua_giu": x["lai"] * he_so - mg["lai"]})
bang.sort(key=lambda x: -x["hon_mua_giu"])

print("\n%-40s %5s %8s %6s %6s %10s %10s"
      % ("co che", "lenh", "lai", "DD%", "x", "lai@cungDD", "hon MG"))
for b in bang[:20]:
    print("%-40s %5d %8.2f %6.2f %6.1f %10.2f %10.2f"
          % (b["ten"][:40], b["lenh"], b["lai"], b["dd_pct"], b["he_so"],
             b["lai_quy"], b["hon_mua_giu"]))
thang = [b for b in bang if b["hon_mua_giu"] > 0]
print("\nTHANG mua-giu o cung sut giam: %d/%d" % (len(thang), len(bang)))

Path("reports/SO_MUA_GIU_%s.json" % MA).write_text(
    json.dumps({"mua_giu": mg, "bang": bang, "tu": TU, "den": DEN},
               ensure_ascii=False, indent=1), encoding="utf-8")
