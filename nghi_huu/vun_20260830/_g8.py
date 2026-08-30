import json
p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json"
c = json.loads(open(p, encoding="utf-8-sig").read())
w = c["worker"]
w["COMPUTE"] = {"cpu_pct": 88, "song_song": 1, "min_duty_sleep": 2, "task": ["quant_sweep.py", "6"]}
w["QUANT"]   = {"cpu_pct": 88, "song_song": 1, "min_duty_sleep": 2, "task": ["quant_offline.py"]}
w["SEEKER"]  = {"cpu_pct": 55, "song_song": 1, "min_duty_sleep": 2, "task": ["seeker_quy_tac.py"]}
w["BANKER"]  = {"cpu_pct": 20, "song_song": 1, "min_duty_sleep": 2, "task": ["banker.py"]}
w["EVO"]     = {"cpu_pct": 20, "song_song": 1, "min_duty_sleep": 2, "task": ["evo_giam_sat.py"]}
c["ghi_chu"] = "ON DINH: COMPUTE(6 nhan)+QUANTx1+SEEKERx1. Tranh thread/process budget crash."
open(p, "w", encoding="utf-8").write(json.dumps(c, ensure_ascii=False, indent=1))
print("stable config COMPUTE=6 set")
