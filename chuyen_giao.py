# -*- coding: utf-8 -*-
"""chuyen_giao.py - Sao luu + ban giao THE BRAIN (chay cuoi moi phien lam viec).

Lam 2 viec:
  1) Snapshot: copy trang thai quan trong vao  lab/reports/chuyen_giao/YYYY-MM-DD/
     (cai gi lam hom nay thuot ten ngay do -> sau nay tim lai duoc "hom qua lam gi").
  2) Ban giao: doc lab/BAN_GIAO.json (noi dung nguoi dung da viet san) -> gan nhan luc
     moi + ghi truc tiep -> viet lai lab/BAN_GIAO_HOM_NAY.md tom tat de phien sau doc.

Chay:
  python chuyen_giao.py            # ca snap + ban giao
  python chuyen_giao.py --snap      # chi sao luu
  python chuyen_giao.py --bangiao   # chi cap nhat ban giao
Chi dung thu vien chuan (stdio) -> chay duoc bang bat cu python nao (ca C:/Python314).
"""
import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LAB = Path(__file__).parent.resolve()          # .../Research SP500/lab
ROOT = LAB.parent                              # .../Research SP500
SNAP_GOC = LAB / "reports" / "chuyen_giao"
BAN_GIAO = LAB / "BAN_GIAO.json"
HOM_NAY = LAB / "BAN_GIAO_HOM_NAY.md"

# File/duong quang trong nhat, snapshot theo net. (duong goc = ROOT)
DU_LIEU = [
    "lab/BO_NHO.md", "lab/HANDOFF.md", "lab/BAN_GIAO.json", "lab/ke_hoach_mai.md",
    "lab/CAI_THIEN_BRAIN.md", "lab/KHUNG.md", "lab/MULTI_AGENT.md", "lab/README_LAB.md",
    "lab/thu_vien.db", "lab/BAN_GIAO_HOM_NAY.md",
    "nguon_config.json", "CLAUDE.md",
    "reports/brain_24h_queue.json", "reports/brain_24h_state.json",
    "reports/BRAIN_nhip_tim.json", "reports/THE_BRAIN.md", "reports/BRAIN_nhat_ky.md",
    "reports/NGUON_CHAT_LUONG.json",
]

GIOTT = 8 * 1024 * 1024  # bo qua file > 8MB trong lab/reports (vd .htm 49MB) de snap nhanh

# ---------------------------------------------------------------- doc tay
def _doc(path, mac_dinh):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return mac_dinh

def _doc_json(path, mac_dinh):
    try:
        return json.loads(_doc(path, ""))
    except Exception:
        return mac_dinh

# ---------------------------------------------------------------- snapshot
def snap():
    ngay = datetime.now().strftime("%Y-%m-%d")
    dest = SNAP_GOC / ngay
    dest.mkdir(parents=True, exist_ok=True)
    dem = 0
    for rel in DU_LIEU:
        src = ROOT / rel
        if not src.is_file():
            continue
        try:
            d = dest / src.relative_to(ROOT)
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, d)
            dem += 1
        except Exception as e:
            print(f"  [bo qua] {rel}: {e}")

    # lab/reports: copy toan bo .md/.json/.parquet nho hon 8MB
    if (LAB / "reports").exists():
        for f in (LAB / "reports").rglob("*"):
            # bo qua thu muc snapshot (chuyen_giao) + __pycache__ -> tranh de quy vao chinh no
            if "chuyen_giao" in f.parts or "__pycache__" in f.parts:
                continue
            if f.is_file() and f.suffix in (".md", ".json", ".parquet") and f.stat().st_size <= GIOTT:
                try:
                    rel = f.relative_to(LAB)
                    d = dest / "lab" / rel
                    d.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, d)
                    dem += 1
                except Exception:
                    pass
    # code .py doi hom nay -> thu muc code/ (de "hom qua lam gi" tim duoc ngay)
    kho_code = dest / "code"
    kho_code.mkdir(parents=True, exist_ok=True)
    tu_dau_ngay = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for f in list(LAB.glob("*.py")) + list(ROOT.glob("*.py")):
        try:
            if f.stat().st_mtime >= tu_dau_ngay.timestamp():
                shutil.copy2(f, kho_code / f.name)
                dem += 1
        except Exception:
            pass
    print(f"  [snap] {len([p for p in dest.rglob('*') if p.is_file()])} file -> {str(dest.relative_to(ROOT))}")
    return dest

# ---------------------------------------------------------------- ban giao
def _thong_ke_db():
    """So vai trong bang cong_viec (neu co thu_vien.db)."""
    db = LAB / "thu_vien.db"
    if not db.exists():
        return {}
    try:
        con = sqlite3.connect(db)
        r = {}
        for (tt, n) in con.execute("SELECT trang_thai, COUNT(*) FROM cong_viec GROUP BY trang_thai"):
            r[tt] = n
        con.close()
        return r
    except Exception:
        return {}

def _doc_brain_24h():
    """Doc nhip tim + hang doi cua brain_24h (ngoai lab)."""
    nhip = _doc_json(ROOT / "reports" / "BRAIN_nhip_tim.json", {})
    q = _doc_json(ROOT / "reports" / "brain_24h_queue.json", [])
    dem = {}
    for v in q:
        dem[v.get("trang_thai", "?")] = dem.get(v.get("trang_thai", "?"), 0) + 1
    loi = [v.get("id") for v in q if "LOI" in str(v.get("ket_qua", "")) or "CO_LOI" in str(v.get("ket_qua", ""))]
    return {
        "nhip_tim": nhip.get("luc"), "trang_thai": nhip.get("trang_thai"),
        "hang_doi": dem, "viec_loi": loi,
    }

def ban_giao(dest):
    # giu nguyen phan nguoi dung viet, chi gan nhan + them phan live
    bg = _doc_json(BAN_GIAO, {"du_an": "The Brain"})
    luc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bg["ban_giao_luc"] = luc

    _24h = _doc_brain_24h()
    db_tk = _thong_ke_db()

    # phan live: chi them, khong xoa gi
    live = {
        "luc": luc,
        "snapshot": str(str(dest.relative_to(ROOT))) if dest else "",
        "brain_24h": _24h,
        "bo_nao_cong_viec": db_tk,
    }
    bg["live"] = live
    BAN_GIAO.write_text(json.dumps(bg, ensure_ascii=False, indent=2), encoding="utf-8")

    # ban giao doc cho nguoi/agent đo cuoi phien
    de_xuat = bg.get("state", {}).get("de_xuat_giao_dich", [])
    dx = ""
    if isinstance(de_xuat, list) and de_xuat:
        top = de_xuat[0]
        dx = "- " + "; ".join(f"{k}={top.get(k)}" for k in
                              ("co_che", "symbol", "khung", "lai_pct", "pf", "trang_thai") if k in top)
    lines = [
        "# BAN GIAO HOM NAY - THE BRAIN",
        "",
        "> Sinh tu dong boi `lab/chuyen_giao.py` cuoi phien. Doc file nay + `lab/BAN_GIAO.json`",
        "> de nam ngay trang thai, khong can doi lai lich su. (" + luc + ")",
        "",
        "## 1. Snapshot luu o dau",
        "- `lab/reports/chuyen_giao/" + (str(dest.relative_to(ROOT)) if dest else "?") + "/`",
        "- Code .py doi hom nay nam trong `.../code/`",
        "",
        "## 2. Trang thai thuc te (live)",
        "- Brain 24/7: nhip tim `" + str(live["brain_24h"].get("nhip_tim")) + "` ("
          + str(live["brain_24h"].get("trang_thai")) + ") | hang doi "
          + json.dumps(live["brain_24h"].get("hang_doi"), ensure_ascii=False),
    ]
    nl = live["brain_24h"].get("viec_loi", [])
    if nl:
        lines.append("  - Viec dang lo~i: " + ", ".join(nl))
    lines += [
        "- bo_nao `cong_viec`: " + json.dumps(live["bo_nao_cong_viec"], ensure_ascii=False),
        "",
        "## 3. Viec tiep theo (tu BAN_GIAO.json)",
    ]
    vt = bg.get("viec_tiep", [])
    lines += (["- [ ] " + v for v in vt] if isinstance(vt, list) and vt else ["- (trong BAN_GIAO.json)"])
    if dx:
        lines += ["", "## 4. De xuat giao dich dang du", dx]
    lines += [
        "",
        "## 5. Doc tiep (theo thu tu)",
        "- `lab/BAN_GIAO.json`, `lab/BO_NHO.md`, `lab/HANDOFF.md`, `CLAUDE.md`, `README_LAB.md`",
    ]
    HOM_NAY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  [bangiao] da cap nhat {BAN_GIAO.name} + viet {HOM_NAY.name}")
    return HOM_NAY

def main():
    ap = argparse.ArgumentParser(description="Sao luu + ban giao THE BRAIN")
    ap.add_argument("--snap", action="store_true", help="chi chup snapshot")
    ap.add_argument("--bangiao", action="store_true", help="chi cap nhat ban giao")
    a = ap.parse_args()
    lam_snap = a.snap or not a.bangiao
    lam_bi = a.bangiao or not a.snap
    dest = None
    if lam_snap:
        dest = snap()
    if lam_bi:
        ban_giao(dest)
    print("  Xong. Nguoi lam tiep: doc lab/BAN_GIAO_HOM_NAY.md + lab/BAN_GIAO.json")

if __name__ == "__main__":
    main()
