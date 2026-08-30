# -*- coding: utf-8 -*-
"""tru_worker.py - Worker lien tuc 24/7 cho 1 tru.
Chay: python tru_worker.py --ten SEEKER --budget 15
- Chay task cua tru -> sau do ngu theo duty-cycle de giu CPU ~budget%.
- Ghi nhip: reports/worker_<TEN>.txt va su kien reports/worker_log.jsonl
- Nguon du lieu task tu config/tai_nguyen.json (portable).
"""
import argparse, json, subprocess, time
from pathlib import Path

LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
PY  = r"C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe"
CFG = LAB / "config" / "tai_nguyen.json"

def ghi(ten, e):
    p = LAB / "reports" / "worker_log.jsonl"
    p.parent.mkdir(exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "tru": ten, **e}, ensure_ascii=False) + "\n")

def nhip(ten):
    (LAB / "reports" / f"worker_{ten}.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")

def run_task(ten, task):
    head = [x for x in str(task[0]).split("/")]
    script = LAB.joinpath(*head)
    args = [str(x) for x in task[1:]]
    return subprocess.run([PY, str(script)] + args, cwd=str(LAB),
                          stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                          timeout=3600, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).returncode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ten"); ap.add_argument("--budget", type=int, default=15)
    a = ap.parse_args()
    ten = a.ten.upper()
    budget = max(5, min(100, a.budget)) / 100.0
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))["worker"][ten]
    task = cfg["task"]; min_sleep = cfg.get("min_duty_sleep", 5)
    ghi(ten, {"loai": "start", "budget_pct": a.budget})
    lan = -1
    while True:
        lan += 1
        t0 = time.time()
        try:
            rc = run_task(ten, task)
            code = "ok" if rc == 0 else f"rc{rc}"
        except subprocess.TimeoutExpired:
            code = "tko"
        except Exception as e:
            code = "loi:" + str(e)[:60]
        dt = time.time() - t0
        g = 1.0
        try:
            gc = (LAB / "reports" / "cpu_gate.txt").read_text().strip()
            g = max(0.2, min(1.0, float(gc or "1.0")))
        except Exception:
            pass
        b_eff = max(0.05, budget * g)
        nu = max(min_sleep, dt / b_eff - dt)
        nu = min(nu, 3600)
        nhip(ten)
        ghi(ten, {"loai": "task", "lan": lan, "code": code, "giay": round(dt, 1), "ngu": round(nu, 1)})
        time.sleep(nu)

if __name__ == "__main__":
    main()
