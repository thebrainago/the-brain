p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\tru_worker.py"
s = open(p, encoding="utf-8").read()
o = '''        dt = time.time() - t0
        # duty-cycle: tong chu ky = dt/budget -> ngu = dt/budget - dt
        nu = max(min_sleep, dt / max(0.01, budget) - dt)
        nu = min(nu, 3600)'''
n = '''        dt = time.time() - t0
        g = 1.0
        try:
            gc = (LAB / "reports" / "cpu_gate.txt").read_text().strip()
            g = max(0.2, min(1.0, float(gc or "1.0")))
        except Exception:
            pass
        b_eff = max(0.05, budget * g)
        nu = max(min_sleep, dt / b_eff - dt)
        nu = min(nu, 3600)'''
assert o in s, "tru_worker sleep block not found"
s = s.replace(o, n, 1)
open(p, "w", encoding="utf-8").write(s)
print("tru_worker governor patched ok")

import json
c = json.loads(open(r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json", encoding="utf-8-sig").read())
w = c["worker"]
w["SEEKER"] = {"cpu_pct": 55, "song_song": 3, "min_duty_sleep": 1, "task": ["seeker_quy_tac.py"]}
w["QUANT"]  = {"cpu_pct": 90, "song_song": 12, "min_duty_sleep": 1, "task": ["quant_offline.py"]}
w["BANKER"] = {"cpu_pct": 20, "song_song": 1, "min_duty_sleep": 1, "task": ["banker.py"]}
w["EVO"]    = {"cpu_pct": 20, "song_song": 1, "min_duty_sleep": 1, "task": ["evo_giam_sat.py"]}
c["ghi_chu"] = "Toc do CAO, governor tu can CPU ~83%. Tong worker = 12 QUANT + 3 SEEKER + 1 BANKER + 1 EVO."
open(r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json", "w", encoding="utf-8").write(json.dumps(c, ensure_ascii=False, indent=1))
print("config updated: QUANTx12, SEEKERx3")
