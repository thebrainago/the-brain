p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\quant_sweep.py"
s = open(p, encoding="utf-8").read()
old = '''def main():
    caps = sorted(p.stem.replace("_M1_mq", "") for p in DATA.glob("*_M1_mq.parquet"))
    workers = 12
    if len(sys.argv) > 1:
        workers = max(2, min(16, int(sys.argv[1])))
    jobs = [(cap, p) for cap in caps for p in PARAMS]
    t0 = time.time()
    kq = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(mo, j): j for j in jobs}
        for fut in as_completed(futs):
            kq.append(fut.result())
    # sap xep: cap, roi lai_nam giam'''
new = '''def cpu():
    try:
        import subprocess as sp
        r = sp.run(["powershell","-NoProfile","-Command",
                    "(Get-CimInstance Win32_Processor|Measure-Object -Property LoadPercentage -Average).Average"],
                   capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 50.0

def gate_wait(target=83):
    for _ in range(12):
        c = cpu()
        if c <= target: return
        time.sleep(3)

def main():
    caps = sorted(p.stem.replace("_M1_mq", "") for p in DATA.glob("*_M1_mq.parquet"))
    workers = 10
    if len(sys.argv) > 1:
        workers = max(2, min(16, int(sys.argv[1])))
    jobs = [(cap, p) for cap in caps for p in PARAMS]
    t0 = time.time()
    kq = []
    # batch de giu CPU theo gate (khong 100%)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for start in range(0, len(jobs), workers):
            batch = jobs[start:start+workers]
            futs = {ex.submit(mo, j): j for j in batch}
            for fut in as_completed(futs):
                kq.append(fut.result())
            gate_wait()
    # sap xep: cap, roi lai_nam giam'''
assert old in s, "quant_sweep main not found"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("quant_sweep gated + batch ok")

import json
c = json.loads(open(r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json", encoding="utf-8-sig").read())
w = c["worker"]
w["QUANT"]   = {"cpu_pct": 90, "song_song": 4, "min_duty_sleep": 1, "task": ["quant_offline.py"]}
w["COMPUTE"] = {"cpu_pct": 90, "song_song": 1, "min_duty_sleep": 1, "task": ["quant_sweep.py", "10"]}
w["SEEKER"]  = {"cpu_pct": 55, "song_song": 3, "min_duty_sleep": 1, "task": ["seeker_quy_tac.py"]}
w["BANKER"]  = {"cpu_pct": 20, "song_song": 1, "min_duty_sleep": 1, "task": ["banker.py"]}
w["EVO"]     = {"cpu_pct": 20, "song_song": 1, "min_duty_sleep": 1, "task": ["evo_giam_sat.py"]}
c["ghi_chu"] = "COMPUTE=quant_sweep(da nhan, gate~83). QUANT scan x4 + SEEKERx3."
open(r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json", "w", encoding="utf-8").write(json.dumps(c, ensure_ascii=False, indent=1))
print("config: COMPUTE added, QUANTx4")
