import subprocess, time, sqlite3, sys
from pathlib import Path
lab = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sp = lab / "seeker_theo_doi.py"
SOURCES = ["Rational Reminder", "Quantified Strategies", "Real Vision", "Quantpedia"]
log = lab / "reports" / "theo_doi_scan.log"
tot = 0
lines = ["[" + time.strftime("%Y-%m-%d %H:%M:%S") + "] THEO DOI scan"]
for s in SOURCES:
    try:
        r = subprocess.run([sys.executable, str(sp), "--quet", s],
                           capture_output=True, text=True, timeout=70, cwd=str(lab))
        out = (r.stdout or "") + (r.stderr or "")
        hit = [l for l in out.splitlines() if "bai moi" in l.lower() or "+" in l]
        lines.append("  " + s + " -> " + (hit[-1] if hit else out.strip()[-80:]))
    except Exception as e:
        lines.append("  " + s + " ERR " + str(e)[:60])
try:
    db = lab / "thu_vien.db"
    con = sqlite3.connect(str(db))
    tot = con.execute("select count(*) from bai_theo_doi").fetchone()[0]
    con.close()
except Exception as e:
    tot = -1
lines.append("TONG bai_theo_doi=" + str(tot))
log.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
