import sys, json, pathlib
from nhan import pmg_quet as Q
ra = {}
for ma in sys.argv[1:]:
    r = Q.quet(ma, "M5", "H1", "ALL")
    Q.in_ket_qua(r, 10)
    ra[ma] = {k: v for k, v in r.items() if k != "ket_qua"}
    ra[ma]["ket_qua"] = [{a: b for a, b in x.items() if a != "duong_cong"}
                         for x in r.get("ket_qua", [])]
pathlib.Path("reports/PMG_QUET.json").write_text(
    json.dumps(ra, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("\n-> reports/PMG_QUET.json")
