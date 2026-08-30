# -*- coding: utf-8 -*-
"""quet_song_hanh.py - Sweep tham so SONG HANH (multiprocessing) tren 1 cap M1.
Dung toi da luong CPU (may ban: 20 luong). Moi worker nap du lieu 1 lan roi
chay nhieu cau hinh. Ghi tat ca ket qua vao summary.json (file de doc lai,
khong bi mat khi turn bi cat).

Cach dung:
  python quet_song_hanh.py EURCAD out_dir --buoc 15,20,25,30 --tp 10,13,16
"""
import argparse, json, os, sys, time
from pathlib import Path
from multiprocessing import Pool

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data"

_G = {}

def _init(cap):
    import pandas as pd
    import mo_phong_v2 as mp
    full = pd.read_parquet(DATA / f"{cap}_M1_mq.parquet")
    _G["mp"] = mp
    _G["d"] = {"hi": full["high"].to_numpy(), "lo": full["low"].to_numpy(),
               "c": full["close"].to_numpy(),
               "sp": (full["spread"].to_numpy() / 10.0).astype("float32"),
               "thu": full["time"].dt.dayofweek.to_numpy().astype("int8"),
               "nam": (full["time"].max() - full["time"].min()).days / 365.25,
               "pv": mp.PV, "cap": cap, "n": len(full)}

def _chay(cfg):
    mp = _G["mp"]; d = _G["d"]
    t0 = time.time()
    r = mp.mo_phong(d, **cfg["tham_so"])
    r["nhan"] = cfg["nhan"]
    r["tham_so"] = cfg["tham_so"]
    r["giay"] = round(time.time() - t0, 2)
    return r

def _grid(values):
    out = []
    for v in values:
        v = v.strip()
        if v:
            try:
                out.append(float(v))
            except Exception:
                pass
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cap")
    ap.add_argument("out_dir")
    ap.add_argument("--buoc", default="20")
    ap.add_argument("--tp", default="13")
    ap.add_argument("--he-so-buoc", default="1.0")
    ap.add_argument("--dung-lo", default="1000")
    ap.add_argument("--chot-tien", default="1000")
    a = ap.parse_args()
    out_dir = Path(a.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    configs = []
    for buoc in _grid(a.buoc):
        for tp in _grid(a.tp):
            configs.append({"nhan": f"b{buoc:g}_tp{tp:g}",
                            "tham_so": {"buoc": buoc, "tp": tp,
                                        "he_so_buoc": float(a.he_so_buoc),
                                        "dung_lo": float(a.dung_lo),
                                        "chot_tien": float(a.chot_tien)}})
    n = min(os.cpu_count() or 4, len(configs))
    print(f"sweep {a.cap}: {len(configs)} cau hinh / {n} worker (cpu={os.cpu_count()})", flush=True)
    with Pool(n, initializer=_init, initargs=(a.cap,)) as p:
        res = p.map(_chay, configs)
    summary = out_dir / "summary.json"
    summary.write_text(json.dumps(res, ensure_ascii=False, default=str), encoding="utf-8")
    print("XONG", len(res), "->", summary, flush=True)

if __name__ == "__main__":
    main()