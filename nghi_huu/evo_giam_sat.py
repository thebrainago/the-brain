# -*- coding: utf-8 -*-
"""evo_giam_sat.py - EVO: giam sat he thong, phat hien van de, DE XUAT giai phap.
Doc worker_log -> viet reports/EVO_BAO_CAO.md. EVO worker chay file nay.
"""
import json, ctypes, time
from pathlib import Path

LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
REP = LAB / "reports"
BAO = REP / "EVO_BAO_CAO.md"
TRU = ["SEEKER", "QUANT", "BANKER", "EVO", "COMPUTE"]

def tail_json(p, n=400):
    out = []
    try:
        for ln in p.read_text(encoding="utf-8-sig").splitlines()[-n:]:
            try: out.append(json.loads(ln))
            except Exception: pass
    except Exception: pass
    return out

def disk_gb():
    try:
        f = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW("C:/", None, None, ctypes.byref(f))
        return f.value / (1024**3)
    except Exception:
        return 99.0

def main():
    evs = tail_json(REP / "worker_log.jsonl")
    st = {}
    for e in evs:
        if e.get("loai") == "task":
            st[e.get("tru")] = e
    lines = ["# EVO_BAO_CAO " + time.strftime("%Y-%m-%d %H:%M:%S"), "",
             "## Trang thai 4 tru", "| tru | lan | code | giay | ngu |", "|---|---|---|---|---|"]
    van_de = []
    for t in TRU:
        e = st.get(t)
        if not e:
            van_de.append(f"{t}: KHONG co du lieu task - kiem tra worker")
            e = {}
        elif e.get("code") != "ok":
            van_de.append(f"{t}: task khong ok ({e.get('code')})")
        lines.append(f"| {t} | {e.get('lan','-')} | {e.get('code','-')} | {e.get('giay','-')} | {e.get('ngu','-')} |")
    disk = disk_gb()
    lines += ["", "## Tai nguyen",
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
    lines += ["", "## Thuc thu SEEKER", f"- {tt}"]
    ung_cu = []
    for f in REP.glob("quantlab_ichimoku_*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8-sig"))
            for r in d.get("ket_qua", []):
                for row in r.get("rows", []):
                    if row and row.get("pval") and row.get("trades", 0) >= 20 and row.get("points", 0) > 0 and row.get("pval") < 0.05:
                        ung_cu.append(f"{d.get('cap')} {r.get('khung')} hold{row.get('hold')} p={row.get('pval')}")
        except Exception: pass
    lines += ["", "## Ung cu vien (qua placebo)",
              *(ung_cu if ung_cu else ["Chua co - tiep tuc param grid + them khung/cap"])]
    lines += ["", "## De xuat & giai phap (EVO)",
              "- [CPU] Neu CPU<50% -> chay param-grid da nhan (quant_sweep) thay vi chi tang duty.",
              "- [HUONG] Quet them M15/H1 cho 8 cap; ung cu -> len MT5 tick-test.",
              "- [NGUON] Seeker bo sung nguon de co y tuong moi cho Quantlab.",
              "- [ONHIEM] Kiem tra disk truoc vu MT5."]
    lines += ["", "## Van de dang theo doi"] + (van_de if van_de else ["- Khong phat hien van de nao"])
    # THUC THI: EVO tu xu ly viec nhe - gom report/log >7 ngay vao archive_old
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
    BAO.write_text("\n".join(lines), encoding="utf-8")
    print("EVO_BAO_CAO ghi xong:", BAO.name, flush=True)
    return 0

if __name__ == "__main__":
    main()
