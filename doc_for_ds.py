import json, time
from pathlib import Path


if __name__ == "__main__":
    # Bo than script vao chot nay: truoc day chi can import module la
    # chay het ca bai quet/ghi bao cao, ke ca khi nguoi goi chi muon
    # dung mot ham trong file.

    DESK = Path(r"C:\Users\SV STORE\Desktop")
    LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
    REP = LAB / "reports"
    f = DESK / "for ds.txt"
    try: txt = f.read_text(encoding="utf-8-sig")
    except Exception: txt = ""
    rec = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "do_dai": len(txt), "dau": txt[:220]}
    REP.mkdir(exist_ok=True)
    with (REP / "for_ds_gdoc.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    (REP / "for_ds_last_read.txt").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    print("OK doc_for_ds", rec["luc"], "len", len(txt))
