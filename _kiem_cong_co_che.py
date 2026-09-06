# -*- coding: utf-8 -*-
"""_kiem_cong_co_che.py - CONG `co_che` DANG CHAN 166 CO CHE. NO CHAN NHAM AI?

Cau hoi cua chu du an 06/09: bo vai phan xu cua LLM thi co LOC KEM DI khong?

Cach tra loi dung khong phai bang ly le ma bang phep do: **cho chinh 166 co che
dang bi chan ra tester**, cung bo thuc thi, cung cua so, cung moc mua-giu. Neu
trong do co cai qua duoc thi cong dang cat vao thit; neu khong thi cong dang
lam dung viec cua no.

Bai nay CHAY NGUOC bo loc: lay dung nhung muc `kiem_khai_bao` tu choi.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_tester_kho as C     # noqa: E402
from nhan import dich_mq5 as D  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
TU, DEN = "2016.06.01", "2026.07.29"

kho = NP.doc_kho()
bi_chan = [c for c in kho if NP.kiem_khai_bao(c)]
print("kho %d -> bi cong chan %d" % (len(kho), len(bi_chan)))
import collections
ly = collections.Counter(NP.kiem_khai_bao(c)[0][:44] for c in bi_chan)
for a, b in ly.most_common(5):
    print("  %3d  %s" % (b, a))

# Bo dich doi `co_che` >= 25 ky tu de qua `kiem_khai_bao` cua chinh no; chen
# mot cau NHAN cho ro rang day la ban DUOC MIEN cong, khong phai ban da qua.
tam = [dict(c, co_che="MIEN CONG DE DO - ban nay chua co ly do kinh te.")
       for c in bi_chan]
tam = [c for c in tam if not NP.kiem_khai_bao(c)]
print("  trong do dich thu duoc (chi thieu `co_che`): %d" % len(tam))

ma, dat = D.sinh_ea(tam, C.TEN_EA, khung="D1", them_mua_giu=True)
src = C.XM_DATA / "MQL5" / "Experts" / (C.TEN_EA + ".mq5")
src.write_text(ma, encoding="utf-8")
loi = C.bien_dich(src)
if loi:
    print("LOI:", loi)
    raise SystemExit(1)
print("  bien dich xong: %d ban" % len(dat))

ten = "bichan_%s" % MA
ini = C.viet_ini(ten, MA, len(dat), TU, DEN)
for h in (".xml", ".htm"):
    f = C.XM_DATA / (ten + h)
    if f.exists():
        f.unlink()
C.dong_terminal()
t0 = time.time()
subprocess.Popen([str(C.XM_EXE), "/config:%s" % ini])
while time.time() - t0 < 2400:
    time.sleep(8)
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                       capture_output=True, text=True)
    if "terminal64.exe" not in r.stdout:
        break

ket = []
for d in C.doc_xml(C.XM_DATA / (ten + ".xml")):
    i = int(C._so(d.get("InpMaCoChe", -1), -1))
    if 0 <= i < len(dat):
        ket.append({"ten": dat[i]["ten"], "lenh": int(C._so(d.get("Trades"))),
                    "lai": C._so(d.get("Profit")),
                    "sharpe": C._so(d.get("Sharpe Ratio")),
                    "dd": C._so(d.get("Equity DD %"))})
mg = next((x for x in ket if x["ten"] == "__mua_giu__"), None)
he = [x for x in ket if x["ten"] != "__mua_giu__"]
he.sort(key=lambda x: -x["sharpe"])
print("\n%d ban co ket qua. Mua-giu: %s" % (len(ket), mg))
print("\n%-42s %5s %9s %7s %7s" % ("co che BI CHAN", "lenh", "lai", "sharpe", "DD%"))
for x in he[:15]:
    print("%-42s %5d %9.2f %7.2f %7.2f"
          % (x["ten"][:42], x["lenh"], x["lai"], x["sharpe"], x["dd"]))
tot = [x for x in he if x["lenh"] >= 25 and x["sharpe"] >= 0.8]
print("\nco >=25 lenh VA sharpe >=0,8: %d/%d" % (len(tot), len(he)))
Path("reports/BI_CHAN_%s.json" % MA).write_text(
    json.dumps({"mua_giu": mg, "ket": he}, ensure_ascii=False, indent=1),
    encoding="utf-8")
