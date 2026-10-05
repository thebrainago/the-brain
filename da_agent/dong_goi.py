# -*- coding: utf-8 -*-
"""Dong goi da_agent thanh du an RIENG: python3 da_agent/dong_goi.py -> xuat/da_agent_du_an.zip (+ thu muc xuat/da_agent_du_an/).
Chua: ma, ke hoach mau, giao thuc, bai hoc, skill Claude, README, .gitignore. KHONG chua khoa hay so chi."""
import shutil, zipfile
from pathlib import Path

G = Path(__file__).resolve().parent.parent
D = G / "xuat" / "da_agent_du_an"
shutil.rmtree(D, ignore_errors=True)
shutil.copytree(G / "da_agent", D / "da_agent", ignore=shutil.ignore_patterns("__pycache__", "dong_goi.py"))
(D / ".claude" / "skills" / "da-agent").mkdir(parents=True)
shutil.copy2(G / ".claude/skills/da-agent/SKILL.md", D / ".claude/skills/da-agent/SKILL.md")
(D / "reports/da_agent").mkdir(parents=True)
shutil.copy2(G / "reports/da_agent/BAI_HOC.md", D / "reports/da_agent/BAI_HOC.md")
shutil.copy2(G / "da_agent/README.md", D / "README.md")
(D / ".gitignore").write_text("__pycache__/\nreports/da_agent/*_20*/\n.env\n", "utf-8")
z = G / "xuat" / "da_agent_du_an.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
    for p in D.rglob("*"):
        if p.is_file():
            f.write(p, p.relative_to(D))
print("xong", z, z.stat().st_size, "byte")
