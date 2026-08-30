import json
p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json"
c = json.loads(open(p, encoding="utf-8-sig").read())
w = c["worker"]
w["SEEKER"] = {"cpu_pct": 15, "song_song": 2, "min_duty_sleep": 2, "task": ["seeker_quy_tac.py"]}
w["QUANT"]  = {"cpu_pct": 60, "song_song": 6, "min_duty_sleep": 2, "task": ["quant_offline.py"]}
w["BANKER"] = {"cpu_pct": 10, "song_song": 1, "min_duty_sleep": 2, "task": ["banker.py"]}
w["EVO"]    = {"cpu_pct": 10, "song_song": 1, "min_duty_sleep": 2, "task": ["evo_giam_sat.py"]}
c["ghi_chu"] = "The Brain 24/7 - TOC DO VUA, cap CPU ~60% (intensive parametre chi khi VPS)."
open(p, "w", encoding="utf-8").write(json.dumps(c, ensure_ascii=False, indent=1))
print("config updated (cap vua)")
