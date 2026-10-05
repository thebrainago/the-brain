# -*- coding: utf-8 -*-
"""Job 2: model re DE XUAT o the -> truong luoi.ThamSo (ten_trong_engine). May cham: ten phai la truong that + lop khop. Chi ghi reports/deepseek/anh_xa/."""
import dataclasses, json, sys, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
LAB = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(LAB))
from nhan import luoi as LU, dich_tham_so as D, the_phuong_phap as TP
from nhan.giao_llm import goi
TS = {f.name: D.LOP_THAM_SO_LUOI.get(f.name, "?") for f in dataclasses.fields(LU.ThamSo)}
TT = ("Anh xa o tham so cua the phuong phap sang truong cua luoi.ThamSo (engine). Truong that (ten: lop):\n" +
      "\n".join("%s: %s" % kv for kv in TS.items()) +
      "\nVoi MOI o cua the, tra ten truong khop NGHIA va CUNG lop, hoac null neu khong co truong tuong ung (dung ep).\n"
      'Tra DUNG mot JSON {"ten_o": "truong_hoac_null", ...}, khong giai thich.\n--- THE ---\n')
def lam(ma):
    the = TP.doc(ma)
    o = [{"ten": c["ten"], "lop": c["lop"]} for c in the["tham_so"]]
    r = goi("T1", TT + json.dumps({"ma": ma, "mo_ta": the.get("mo_ta", "")[:300], "o": o}, ensure_ascii=False), 600, "anh_xa")
    t = r["noi_dung"].strip(); m = re.search(r"\{.*\}", t, re.S)
    try: d = json.loads(m.group(0))
    except Exception: return ma, None, r["dong"]
    ok = {k: v for k, v in d.items() if v in TS and any(c["ten"] == k and c["lop"] == TS[v] for c in the["tham_so"])}
    return ma, ok, r["dong"]
if __name__ == "__main__":
    ds = [l.strip() for l in open(LAB / "reports/deepseek/the/_DANH_SACH_VIEC.txt") if l.strip()]
    with ThreadPoolExecutor(6) as ex: kq = list(ex.map(lambda m: lam(m.replace(".json", "")), ds))
    out = {m: ok for m, ok, _ in kq}
    (LAB / "reports/deepseek/anh_xa/ket_qua.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("the:", len(kq), "loi parse:", sum(1 for _, o, _ in kq if o is None), "o khop:", sum(len(o or {}) for _, o, _ in kq), "dong:", round(sum(d for *_, d in kq), 1))
