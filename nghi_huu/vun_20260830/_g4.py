import json
p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json"
c = json.loads(open(p, encoding="utf-8-sig").read())
w = c["worker"]
w["COMPUTE"] = {"cpu_pct": 95, "song_song": 1, "min_duty_sleep": 1, "task": ["quant_sweep.py", "13"]}
w["SEEKER"]  = {"cpu_pct": 55, "song_song": 2, "min_duty_sleep": 1, "task": ["seeker_quy_tac.py"]}
w["QUANT"]   = {"cpu_pct": 90, "song_song": 4, "min_duty_sleep": 1, "task": ["quant_offline.py"]}
open(p, "w", encoding="utf-8").write(json.dumps(c, ensure_ascii=False, indent=1))
print("config: COMPUTE=13 cores, SEEKER=2")
