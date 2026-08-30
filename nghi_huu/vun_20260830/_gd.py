import io, json
from pathlib import Path
LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
REP = LAB / "reports"
import sys; sys.path.insert(0, str(LAB))
import seeker_quy_tac as S

# 1) RANK_DARWIN.md
top = S.loc_darwinex(30)
ln = ["# RANK DARWIN (track-record that, Darlingex)", "Ngay: 2026-08-14",
      "", "Luoi lo then now: (DD tren -20%, loi duong, du nam, von that >=10000, nha dau tu>=5)",
      "", "| # | DARWIN | Loi% | DD% | Dscore | NDT | von | Diem |",
      "|---|---|---|---|---|---|---|---|"]
for i, d in enumerate(top[:15], 1):
    ln.append(f"| {i} | [{d['darwin']}]({d['url']}) | {round(d.get('returnByPeriod',0),1)} | {round(d.get('drawDownByPeriod',0),1)} | {round(d.get('dscore') or 0,1)} | {d.get('investorsByPeriod') or 0} | {round(d.get('currentInvestment') or 0)} | {d['diem']} |")
ln += ["", "GHI CHU: Darlingex API KHONG cong bo quy tac/chi moi (chi track-record).",
       "=> Chon top de theo doi/copy hoac model 'ban tuong duong' trong Quantlab.",
       "Top 3: VAJJ(+144,DD-15.8) AACU(+119,DD-8.9) XKA(+64,DD-6.1)."]
(REP / "RANK_DARWIN.md").write_text("\n".join(ln), encoding="utf-8")
print("RANK_DARWIN.md wrote, lines=", len(ln))

# 2) patch seeker_quy_tac: thuc_thu + write seek_out.json
p = LAB / "seeker_quy_tac.py"
s = open(p, encoding="utf-8").read()
o = '''        "goi_y_keyword": kw,
    }'''
n = '''        "goi_y_keyword": kw,
        "thuc_thu": {"darwinex": len(top), "web_live": 0},
    }
    try:
        (REPORTS / "seek_out.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    return r'''
assert o in s
s = s.replace(o, n, 1)
open(p, "w", encoding="utf-8").write(s)
print("seeker_quy_tac patched (thuc_thu)")

# 3) patch evo_giam_sat: doc seek_out.json
e = LAB / "evo_giam_sat.py"
t = open(e, encoding="utf-8").read()
o2 = '''    lines += ["", "## Tai nguyen",
              f"- Disk trong: {round(disk,1)} GB",
              f"- MT5 tick-test: {'GO' if disk >= 15 else 'KHOA (disk<15GB)'}"]'''
n2 = '''    lines += ["", "## Tai nguyen",
              f"- Disk trong: {round(disk,1)} GB",
              f"- MT5 tick-test: {'GO' if disk >= 15 else 'KHOA (disk<15GB)'}"]
    tt = "chua co"
    sf = REP / "seek_out.json"
    if sf.exists():
        try:
            ss = json.loads(sf.read_text(encoding="utf-8-sig"))
            th = ss.get("thuc_thu", {})
            tt = f"{ss.get('so_ung_vien_qua_loc', 0)} ung cu; thuc_thu: Darwinex={th.get('darwinex')}, web_live={th.get('web_live')}"
        except Exception:
            pass
    lines += ["", "## Thuc thu SEEKER", f"- {tt}"]'''
assert o2 in t
t = t.replace(o2, n2, 1)
open(e, "w", encoding="utf-8").write(t)
print("evo_giam_sat patched (thuc thu)")
