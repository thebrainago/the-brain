# -*- coding: utf-8 -*-
"""Bu lai so tu sinh tu cac file ket qua da co.

Ly do: buoc ghi so dung sai khoa (`ic` thay vi `trung_vi`) nen ca hai tho chet DUNG
LUC GHI - phep do da chay xong, ket qua nam trong reports/ds/*.json, chi la khong vao
duoc bang tong. Day la kieu loi te nhat: duong that bai duoc thu ky, duong thanh cong
thi khong, nen no chi lo ra khi co ket qua tot.
"""
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
GHI_CHEP = HERE / "reports" / "ds"
SO = HERE / "reports" / "BRAIN_TU_SINH.md"
DEM = HERE / "reports" / "BRAIN_dem_phep_thu.json"

DAU = ("# THE BRAIN - tang kham pha tu sinh\n\n"
       "> Ket qua o day KHONG PHAI edge. Tang 1, khong cong nao, khong ton\n"
       "> slot FDR. Cot `phep thu so` la de khi mot khang dinh duoc mang len\n"
       "> tang xac nhan thi con biet no la lan boc tham thu bao nhieu.\n\n"
       "| phep thu so | ten | nhom duong | z trung vi | p theo nhom | khang dinh |\n"
       "|---|---|---|---|---|---|\n")

dong = []
for f in sorted(GHI_CHEP.glob("*.json"), key=lambda x: x.stat().st_mtime):
    if f.name.startswith("_"):
        continue
    d = json.loads(f.read_text(encoding="utf-8"))
    kq = d.get("ket_qua")
    mo_ta = str(d.get("y_tuong", ""))[:150].replace("\n", " ")
    if kq:
        dong.append(f"| {len(dong)+1} | `{d['ten']}` | {kq.get('nhom_duong','?')}/"
                    f"{kq.get('so_nhom','?')} | {kq.get('trung_vi', float('nan')):+.3f} | "
                    f"{kq.get('p_theo_nhom', float('nan')):.4f} | {mo_ta} |")
    else:
        dong.append(f"| {len(dong)+1} | `{d['ten']}` | HONG | - | - | {mo_ta} |")

SO.write_text(DAU + "\n".join(dong) + "\n", encoding="utf-8")
DEM.write_text(json.dumps({"so_phep_thu_tang_1": len(dong),
                           "cap_nhat": datetime.now().isoformat(timespec="seconds")},
                          ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Bu {len(dong)} dong vao {SO.name}. Bo dem tang 1 = {len(dong)}.")
