# -*- coding: utf-8 -*-
"""chay_backtest.py - Chay backtest Python (mo_phong_v2) TACH NEN, ghi ket qua ra file.
Dung de khong bi timeout khi chay viec nang trong 1 turn.
Cach: python chay_backtest.py <cap> <json_tham_so> <file_ra>
Vidu: python chay_backtest.py EURCAD "{\"buoc\":20,\"tp\":13}" reports/bt_eurcad.json
"""
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pandas as pd
import mo_phong_v2 as mp

def main():
    cap = sys.argv[1] if len(sys.argv) > 1 else "EURCAD"
    tham_so = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    file_ra = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "reports" / f"bt_{cap}.json"
    file_ra.parent.mkdir(exist_ok=True)
    t0 = time.time()
    full = pd.read_parquet(ROOT / "data" / f"{cap}_M1_mq.parquet")
    d = {"hi": full["high"].to_numpy(), "lo": full["low"].to_numpy(),
         "c": full["close"].to_numpy(),
         "sp": (full["spread"].to_numpy() / 10.0).astype("float32"),
         "thu": full["time"].dt.dayofweek.to_numpy().astype("int8"),
         "nam": (full["time"].max() - full["time"].min()).days / 365.25,
         "pv": mp.PV, "cap": cap, "n": len(full)}
    r = mp.mo_phong(d, **tham_so)
    r["cap"] = cap; r["tham_so"] = tham_so
    r["giay"] = round(time.time() - t0, 1)
    r["trang_thai"] = "XONG"
    file_ra.write_text(json.dumps(r, ensure_ascii=False, default=str), encoding="utf-8")
    print("DA XONG", cap, "->", file_ra)

if __name__ == "__main__":
    main()