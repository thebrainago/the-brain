# -*- coding: utf-8 -*-
"""brain_master.py - Supervisor 24/7 + GOVERNOR CPU.
Spawn nhieu worker song song cho 4 tru (config/tai_nguyen.json).
Governor: do CPU -> tu chinh muc do (cpu_gate.txt) de giu ~80-85%.
Chay: python brain_master.py [--den 23:00] [--target 83]
"""
import argparse, json, os, subprocess, time
from pathlib import Path

LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
PY  = r"C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe"
CFG = LAB / "config" / "tai_nguyen.json"
STOP = LAB / "THORN_STOP"
LOG  = LAB / "reports" / "brain_master.log"
HB   = LAB / "reports" / "brain_heartbeat.txt"
GATE = LAB / "reports" / "cpu_gate.txt"

def ghi(s):
    LOG.parent.mkdir(exist_ok=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + s + "\n")
    except Exception: pass

def cpu_now():
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor|Measure-Object -Property LoadPercentage -Average).Average"],
            capture_output=True, text=True, timeout=15, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        v = float(r.stdout.strip())
        return v if -1 < v <= 100 else 50.0
    except Exception:
        return 50.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--den", default="23:00")
    ap.add_argument("--target", type=int, default=83)
    a = ap.parse_args()
    target = max(50, min(95, a.target))
    try: hh, mm = map(int, a.den.split(":"))
    except Exception: hh, mm = 23, 0
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    ws = cfg["worker"]
    try:
        den = time.mktime(time.strptime(time.strftime("%Y-%m-%d %02d:%02d:00" % (hh, mm)), "%Y-%m-%d %H:%M:%S"))
    except Exception:
        den = time.time() + 8 * 3600
    if den <= time.time(): den = time.time() + 600

    procs = {}
    for ten, v in ws.items():
        for i in range(int(v.get("song_song", 1))):
            env = dict(os.environ); env["BRAIN_PHU"] = str(i); env["BRAIN_TONG"] = str(v.get("song_song", 1))
            procs[(ten, i)] = subprocess.Popen([PY, str(LAB/"tru_worker.py"), "--ten", ten, "--budget", str(v["cpu_pct"])],
                                               cwd=str(LAB), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    g = 1.0
    try: g = max(0.2, min(1.0, float(GATE.read_text().strip() or "1.0")))
    except Exception: pass
    GATE.write_text(str(g))
    ghi("spawn: " + " + ".join(f"{k[0]}x{len([p for p in procs if p[0]==k[0]])}" for k in procs) +
        f" | CPU target {target}% | gate={g:.2f}")

    lan_loi = {k: 0 for k in procs}
    t_last = 0.0
    while True:
        if STOP.exists(): ghi("THORN_STOP - dung."); break
        if time.time() >= den: ghi("het gio - dung."); break
        # governor CPU: moi ~10s
        if time.time() - t_last >= 10:
            t_last = time.time()
            c = cpu_now()
            if c > 0:
                g = max(0.2, min(1.0, g * (target / c)))
                GATE.write_text(f"{g:.2f}")
            ghi(f"cpu={round(c)}% gate={g:.2f}")
        for k, p in list(procs.items()):
            if p.poll() is not None:
                lan_loi[k] += 1
                tar = min(10.0 * lan_loi[k], 60.0)
                ghi(f"{k[0]}#{k[1]} chet - khoi dong lai sau {tar:g}s")
                time.sleep(tar)
                env = dict(os.environ); env["BRAIN_PHU"] = str(k[1]); env["BRAIN_TONG"] = str(ws[k[0]].get("song_song", 1))
                procs[k] = subprocess.Popen([PY, str(LAB/"tru_worker.py"), "--ten", k[0], "--budget", str(ws[k[0]]["cpu_pct"])],
                                            cwd=str(LAB), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            else:
                lan_loi[k] = 0
        HB.parent.mkdir(exist_ok=True)
        HB.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        time.sleep(10)

    for p in procs.values():
        try: p.terminate()
        except Exception: pass
    ghi("da dung supervisor + worker.")

if __name__ == "__main__":
    main()
