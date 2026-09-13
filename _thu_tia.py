# -*- coding: utf-8 -*-
"""_thu_tia.py - chay MOT pass ho `tia` roi doc log agent de biet no co chay khong."""
import subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chay_tester_kho import bien_dich
from chay_tester_z5 import XM_DATA, XM_EXE, dong_terminal
from nhan import khoa_tester as KT

TEN = "thu_tia"
with KT.giu("thu_tia"):
    src = XM_DATA / "MQL5" / "Experts" / "QuanTriBench.mq5"
    src.write_text(Path("ea_QuanTriBench.mq5").read_text(encoding="utf-8"),
                   encoding="utf-8")
    loi = bien_dich(src)
    print("bien dich:", loi or "0 errors")
    if loi:
        raise SystemExit(1)
    ini = XM_DATA / f"{TEN}.ini"
    ini.write_text(f"""[Tester]
Expert=QuanTriBench.ex5
Symbol=US500Cash
Period=H1
Model=2
ExecutionMode=0
Optimization=0
FromDate=2016.01.01
ToDate=2026.07.29
ForwardMode=0
Deposit=10000
Currency=USD
Leverage=1:500
Report={TEN}
ReplaceReport=1
ShutdownTerminal=1

[TesterInputs]
InpHoQT=5
InpP1=0.5
InpP2=1.0
InpVaoKieu=0
InpVaoN=20
InpLot=1.0
InpMagic=26091301
InpATRKy=14
InpSLCung=3.0
InpGiuToiDa=120
InpNhoiMax=5
""", encoding="utf-16")
    dong_terminal()
    t0 = time.time()
    subprocess.Popen([str(XM_EXE), "/config:%s" % ini])
    while time.time() - t0 < 900:
        time.sleep(5)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                           capture_output=True, text=True)
        if "terminal64.exe" not in r.stdout:
            break
    print("chay xong %.0fs" % (time.time() - t0))

logs = sorted((XM_DATA / "Tester" / "logs").glob("*.log"))
if not logs:
    logs = sorted((XM_DATA / "logs").glob("*.log"))
for f in logs[-3:]:
    try:
        van = f.read_text(encoding="utf-16", errors="ignore")
    except Exception:
        van = f.read_text(encoding="utf-8", errors="ignore")
    for d in van.splitlines():
        if "QT_TIA" in d or "CHUA_DO_DUOC" in d:
            print(f.name, "|", d.strip()[-200:])
