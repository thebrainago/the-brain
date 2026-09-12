# -*- coding: utf-8 -*-
"""_audit_tru.py - TRU NAO DA HOAN THIEN, TRU NAO CON LO HONG?

Chu du an 12/09: *"viec chinh la xay cac tru module cho hoan thien"*.

## BAN DAU TOI DO SAI - ghi lai de khong lam lai

Ban dau file nay dung do thi CALL GRAPH tu diem vao `mot_luot()`, va no bao 9 bo
nguon cua SEEKER (`n_arxiv`, `n_openalex`, `n_hackernews`...) la **ma chet**.
SAI. Chung duoc **dang ky** vao `NGUON[ma]["ham"]` roi goi gian tiep bang
`c["ham"](tk)`. AST khong nhin thay dispatch qua so dang ky.

Bai hoc: mot ham duoc THAM CHIEU (dua ten vao mot bang) cung la duoc noi day.
Do "co bi goi khong" bang call graph se bao oan moi kien truc plugin.

## THUOC DUNG CHO "TRU DA HOAN THIEN CHUA"

Khong phai "co ham nao khong ai goi" ma la **tru co dang SINH RA SAN PHAM khong**:

  NHIP TIM   lan cuoi tru chay, va no bao trang thai gi
  SAN LUONG  no de lai gi trong `nao.db` (tai lieu, gia thuyet, ket qua, bai hoc)
  NGUON      bao nhieu nguon BAT ma thu hoach = 0, bao nhieu dang loi lien tuc
  MA CHET    ham cong khai khong duoc GOI lan THAM CHIEU o bat ky dau

Chay:  python _audit_tru.py
Ra:    reports/AUDIT_TRU.json
"""
from __future__ import annotations

import ast
import json
import re
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

TRU = ["seeker", "quantlab", "nghi", "banker", "evolution", "finder"]
RA = LAB / "reports" / "AUDIT_TRU.json"


def _cong_khai(p: Path):
    s = p.read_text(encoding="utf-8", errors="replace")
    try:
        cay = ast.parse(s)
    except SyntaxError:
        return [], s
    return [n.name for n in cay.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and not n.name.startswith("_")], s


def main() -> int:
    from nhan import so as SO

    # ---- ma chet: ten khong xuat hien o BAT KY dau ngoai dong `def` cua chinh no
    nguon = {}
    for p in (list(LAB.glob("*.py")) + list(LAB.glob("nhan/*.py"))
              + list(LAB.glob("tru/*.py")) + list(LAB.glob("qwen/*.py"))):
        try:
            nguon[p] = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ket = {}
    print("=" * 84)
    print("1. MA CHET - ham cong khai khong duoc goi LAN tham chieu o bat ky dau")
    print("=" * 84)
    for ten in TRU:
        p = LAB / "tru" / (ten + ".py")
        if not p.exists():
            continue
        ck, s = _cong_khai(p)
        chet = []
        for f in ck:
            rx = re.compile(rf"\b{re.escape(f)}\b")
            n = 0
            for q, src in nguon.items():
                for dong in src.splitlines():
                    if q == p and re.match(rf"\s*(async\s+)?(def|class)\s+{re.escape(f)}\b", dong):
                        continue          # dong dinh nghia cua chinh no
                    if rx.search(dong):
                        n += 1
            if n == 0:
                chet.append(f)
        ket[ten] = {"so_ham_cong_khai": len(ck), "ma_chet": chet}
        print("  %-11s %3d ham cong khai · %d ma chet%s"
              % (ten, len(ck), len(chet), ("  -> " + ", ".join(chet)) if chet else ""))

    # ---- nhip tim
    print("\n" + "=" * 84)
    print("2. NHIP TIM - tru co dang chay khong")
    print("=" * 84)
    try:
        rows = SO.nhieu("SELECT * FROM nhip ORDER BY tru")
        now = time.time()
        for r in rows:
            luc = r["luc"] if "luc" in r.keys() else None
            gio = ((now - luc) / 3600) if isinstance(luc, (int, float)) and luc else None
            print("  %-12s %-12s %s"
                  % (r["tru"], (r["trang_thai"] if "trang_thai" in r.keys() else "?"),
                     ("%.1f gio truoc" % gio) if gio is not None else str(luc)[:19]))
            ket.setdefault(str(r["tru"]).lower(), {})["nhip_tim_gio_truoc"] = (
                round(gio, 2) if gio is not None else None)
    except Exception as e:
        print("  khong doc duoc bang nhip:", str(e)[:70])

    # ---- nguon: BAT ma khong thu hoach
    print("\n" + "=" * 84)
    print("3. NGUON CUA SEEKER - BAT ma thu hoach = 0, hoac dang loi lien tuc")
    print("=" * 84)
    try:
        ng = SO.nhieu("SELECT * FROM nguon ORDER BY uu_tien, ma")
        bat = [r for r in ng if r["trang_thai"] == "BAT"]
        cam = [r for r in bat if not (r["thu_hoach"] or 0)]
        loi = [r for r in bat if (r["loi_lien_tuc"] or 0) >= 3]
        print("  tong %d nguon · BAT %d · THU HOACH = 0: %d · loi lien tuc >= 3: %d"
              % (len(ng), len(bat), len(cam), len(loi)))
        print("\n  %-24s %8s %7s %7s %s" % ("nguon", "thu hoach", "so lan", "loi", "ghi chu"))
        for r in sorted(bat, key=lambda x: (x["thu_hoach"] or 0))[:22]:
            print("  %-24s %8d %7d %7d %s"
                  % (r["ma"][:24], r["thu_hoach"] or 0, r["so_lan"] or 0,
                     r["loi_lien_tuc"] or 0, str(r["ghi_chu"] or "")[:34]))
        ket["_nguon"] = {"tong": len(ng), "bat": len(bat),
                         "thu_hoach_0": [r["ma"] for r in cam],
                         "loi_lien_tuc": [r["ma"] for r in loi]}
    except Exception as e:
        print("  khong doc duoc bang nguon:", str(e)[:70])

    # ---- san luong trong nao.db
    print("\n" + "=" * 84)
    print("4. SAN LUONG TRONG nao.db")
    print("=" * 84)
    for b in ("tai_lieu", "noi_dung", "artifact", "gia_thuyet", "ket_qua",
              "bai_hoc", "fdr", "nguon"):
        try:
            n = SO.mot("SELECT COUNT(*) c FROM %s" % b)["c"]
            print("  %-12s %8d" % (b, n))
            ket.setdefault("_san_luong", {})[b] = n
        except Exception:
            pass

    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s" % RA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
