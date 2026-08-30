# -*- coding: utf-8 -*-
"""quant_sweep.py - QUANTLAB PARAM GRID da nhan (ProcessPoolExecutor).
Grid buoc x tp tren 8 cap M1 local, mo_phong_v2.mo_phong. Chay nhanh da nhan.
Chay: python quant_sweep.py [--workers 12] [--a buoc1..] [--t tp1..]
"""
import json, os, sys, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT = Path(r"C:\Users\SV STORE\Downloads\Research SP500")
DATA = ROOT / "data"
LAB  = ROOT / "lab"
sys.path.insert(0, str(ROOT))

PARAMS = [{"buoc": b, "tp": t} for b in (15, 20, 25, 30) for t in (8, 10, 13, 17)]

def mo(job):
    cap, p = job
    try:
        import mo_phong_v2 as mp
        d = mp.nap(cap)
        r = mp.mo_phong(d, **p)
        return {"cap": cap, "buoc": p["buoc"], "tp": p["tp"],
                "lai_nam": round(r.get("lai_nam", 0), 1),
                "ls": round(r.get("ls", 0), 3),
                "cat_nam": round(r.get("cat_nam", 0), 3),
                "lenh_tuan": round(r.get("lenh_tuan", 0), 1)}
    except Exception as e:
        return {"cap": cap, "buoc": p["buoc"], "tp": p["tp"], "loi": str(e)[:120]}

def cpu():
    try:
        import subprocess as sp
        r = sp.run(["powershell","-NoProfile","-Command",
                    "(Get-CimInstance Win32_Processor|Measure-Object -Property LoadPercentage -Average).Average"],
                   capture_output=True, text=True, timeout=15, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
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
    # sap xep: cap, roi lai_nam giam
    kq.sort(key=lambda x: (x["cap"], -(x.get("lai_nam") or 0)))
    out = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "cap": caps,
           "workers": workers, "jobs": len(jobs), "giay": round(time.time()-t0, 1),
           "ket_qua": kq}
    fp = LAB / "reports" / "quant_sweep.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    # tom tat top cai tien tren tong cap
    best = {}
    for x in kq:
        if x.get("lai_nam") is not None:
            if x["cap"] not in best or x["lai_nam"] > best[x["cap"]]["lai_nam"]:
                best[x["cap"]] = x
    print(f"Sweep xong: {len(jobs)} job / {workers} workers / {round(time.time()-t0,1)}s")
    for cap in caps:
        b = best.get(cap)
        print(f"  {cap:8} best: {b}")
    return 0

if __name__ == "__main__":
    main()
