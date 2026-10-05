# -*- coding: utf-8 -*-
"""so_sanh_model.py - chay CUNG 35 the voi nhieu model (1 lan, tat suy luan), ghi reports/deepseek/so_sanh/<model>/, KHONG dung vao the/.
    python3 reports/deepseek/so_sanh_model.py <model> [...]      (bang gia: tai_lieu/BANG_GIA_AIBOX.md)"""
import json, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_dien_the as C

OUT = C.LAB / "reports" / "deepseek" / "so_sanh"


def mot(args):
    model, ma = args
    goc = C.TP.doc(ma)
    nd = C.TIEN_TO + json.dumps(goc, ensure_ascii=True)
    g = C.goi(model, nd, 1500)
    if "loi" in g:
        time.sleep(3); g = C.goi(model, nd, 1500)
    r = {"ma": ma, "model": model, **{k: v for k, v in g.items() if k != "text"}, "dat": False, "loi": []}
    if "loi" in g:
        r["loi"] = [g["loi"]]; return r
    ban = C.tach_json(g["text"])
    if ban is None:
        r["loi"] = ["khong ra JSON"]; return r
    r["loi"] = C.KT.cham(ban); r["dat"] = not r["loi"]
    d = OUT / model.replace("/", "_"); d.mkdir(parents=True, exist_ok=True)
    (d / (ma + ".json")).write_text(json.dumps(ban, ensure_ascii=True, indent=1) + "\n", encoding="utf-8")
    return r


if __name__ == "__main__":
    ds = (C.DIR / "_DANH_SACH_VIEC.txt").read_text().split()
    for m in sys.argv[1:]:
        t = time.time()
        with ThreadPoolExecutor(6) as ex:
            rs = list(ex.map(mot, [(m, x) for x in ds]))
        OUT.mkdir(parents=True, exist_ok=True)
        with (OUT / "_nhat_ky.jsonl").open("a") as f:
            for r in rs: f.write(json.dumps(r, ensure_ascii=True) + "\n")
        print(m, "dat %d/%d" % (sum(r["dat"] for r in rs), len(rs)), "%.0fs" % (time.time() - t), flush=True)
