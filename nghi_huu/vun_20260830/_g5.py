p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\evo_giam_sat.py"
s = open(p, encoding="utf-8").read()
old = '''    BAO.write_text("\\n".join(lines), encoding="utf-8")'''
new = '''    # THUC THI: EVO tu xu ly viec nhe - gom report/log >7 ngay vao archive_old
    thuc_thi = []
    try:
        now_t = time.time(); bo = 0
        ard = REP / "archive_old"; ard.mkdir(exist_ok=True)
        for f in list(REP.glob("*.jsonl")) + list(REP.glob("*.json")) + list(REP.glob("*.md")):
            if f.name in ("EVO_BAO_CAO.md", "TOM_TAT_DAILY.md", "tiep_tuc.log"):
                continue
            try:
                if (now_t - f.stat().st_mtime) / 86400 > 7:
                    f.rename(ard / f.name); bo += 1
            except Exception:
                pass
        thuc_thi.append(f"- Da gom {bo} report/log >7 ngay vao reports/archive_old.")
    except Exception as e:
        thuc_thi.append(f"- Loi thuc thi: {str(e)[:80]}")
    lines += ["", "## DA THUC THI"] + thuc_thi
    BAO.write_text("\\n".join(lines), encoding="utf-8")'''
assert old in s, "evo write block not found"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("evo THUC THI added ok")
