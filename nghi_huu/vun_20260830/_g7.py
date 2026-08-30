import json
p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json"
c = json.loads(open(p, encoding="utf-8-sig").read())
w = c["worker"]
w["COMPUTE"] = {"cpu_pct": 95, "song_song": 1, "min_duty_sleep": 1, "task": ["quant_sweep.py", "10"]}
w["QUANT"]   = {"cpu_pct": 90, "song_song": 2, "min_duty_sleep": 1, "task": ["quant_offline.py"]}
w["SEEKER"]  = {"cpu_pct": 55, "song_song": 1, "min_duty_sleep": 1, "task": ["seeker_quy_tac.py"]}
w["BANKER"]  = {"cpu_pct": 20, "song_song": 1, "min_duty_sleep": 1, "task": ["banker.py"]}
w["EVO"]     = {"cpu_pct": 20, "song_song": 1, "min_duty_sleep": 1, "task": ["evo_giam_sat.py"]}
c["gioi_han"] = "tru ban: COMPUTE(10 nhan) + QUANTx2 scan + SEEKERx1. Giam tai tranh OOM."
open(p, "w", encoding="utf-8").write(json.dumps(c, ensure_ascii=False, indent=1))
print("sustainable config set")
