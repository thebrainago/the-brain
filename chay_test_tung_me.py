# -*- coding: utf-8 -*-
"""chay_test_tung_me.py - chay CA bo test bang NHIEU tien trinh pytest ngan.

## VI SAO CAN FILE NAY

Ngay 13/09/2026 bo test khong chay het duoc mot lan nao, 4 luot lien:

    -n 6   chet o 92%   khong ban tom tat
    -n 6   chet o 94%   `[gw4] node down: Not properly terminated`
    -n 6   chet o 94%   khong ban tom tat
    -n 3   chet o 56%   khong ban tom tat

Trong khi chay TUNG NHOM 8-16 file thi xanh binh thuong (124/125, 32/32,
167/167). Nguyen nhan la bo nho: mot tien trinh pytest song suot ~1.060 bai
tich luy du lieu cua moi bai (parquet da nap, ket noi SQLite, MAU.MAU...) va
may nay nghet paging - `paging file too small` da xuat hien that.

**Va do khong phai mot phien phuc.** Mot bo test khong bao gio chay het la mot
bo test khong ai doc ket qua - dung nhu ban giao 12/09 ghi *"bo test chot phien
chay den 94% thi bi cat, thay 2 chu F nhung chua kip biet la bai nao"*. Hai
chu F do nam do mot ngay khong ai truy duoc.

## CACH LAM

Chia file test thanh cac me `so_file` file, moi me MOT tien trinh pytest
RIENG. Tien trinh chet thi chi mat me do, va ta BIET me nao - cac me khac van
chay. Khong me nao song du lau de tich du bo nho ma chet.

Danh doi: cham hon mot chut (moi me boot lai pytest ~2 giay). Doi lai la mot
con so tong KET THUC duoc.

Chay:
    python chay_test_tung_me.py              ca bo, me 12 file, 3 nhan
    python chay_test_tung_me.py --me 8       me nho hon neu van chet
    python chay_test_tung_me.py --nhan 1     mot nhan (khi nghi song song sai)
    python chay_test_tung_me.py --tu-khoa qt chi file co tu khoa trong ten
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
PY = sys.executable

_RX = re.compile(
    r"(?:(\d+) failed)?,?\s*(?:(\d+) passed)?,?\s*(?:(\d+) skipped)?"
    r"(?:,\s*(\d+) error)?")


def _doc_tom_tat(van: str) -> dict:
    """Lay dong tong ket cuoi cua pytest. Khong co = me chet giua chung."""
    for d in reversed(van.strip().splitlines()):
        # Chi nhan dong TOM TAT that. Khong co `d.startswith` thi dong
        # `INTERNALERROR> File "...xdist/dsession.py", line 266, in
        # worker_errordown` cung khop ("error" + " in ") va me chet bi bao
        # nham la me chay xong - dung cai bay "khau do hong doc y het ket qua".
        if d.startswith(("INTERNALERROR", "E ", "  File", "Traceback")):
            continue
        if ("passed" in d or "failed" in d or "error" in d) and " in " in d:
            m = _RX.search(d)
            if m and (m.group(1) or m.group(2) or m.group(4)):
                return {"do": int(m.group(1) or 0), "xanh": int(m.group(2) or 0),
                        "bo_qua": int(m.group(3) or 0),
                        "loi": int(m.group(4) or 0), "dong": d.strip()}
    return {}


def chay(so_file: int = 12, nhan: int = 3, tu_khoa: str = "",
         han_giay: int = 1800) -> dict:
    ds = sorted(p.name for p in LAB.glob("test_*.py"))
    if tu_khoa:
        ds = [f for f in ds if tu_khoa in f]
    me = [ds[i:i + so_file] for i in range(0, len(ds), so_file)]
    print("%d file test -> %d me x %d file, %d nhan moi me"
          % (len(ds), len(me), so_file, nhan), flush=True)

    t0 = time.time()
    tong = {"xanh": 0, "do": 0, "bo_qua": 0, "loi": 0}
    me_chet, bai_do = [], []
    for i, nhom in enumerate(me, 1):
        lenh = [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                "--no-header", "-rf"]
        if nhan > 1:
            lenh += ["-n", str(nhan), "--dist", "loadfile"]
        lenh += nhom
        # LOI KHONG DUOC CHAN HANG. Ban dau `subprocess.run(timeout=1800)` de
        # `TimeoutExpired` bay ra ngoai -> mot me qua gio lam SAP ca luot va
        # mat luon ket qua cua 7 me da chay xong. Day dung la luat 3 cua
        # `day_viec.py` ("hang doi tuan tu ma dung o loi dau tien thi vo dung
        # hon"), chi la toi khong ap no cho chinh bo chay test.
        try:
            r = subprocess.run(lenh, cwd=str(LAB), capture_output=True,
                               text=True, errors="replace", timeout=han_giay)
            van = (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired as e:
            van = ""
            me_chet.append({"me": i, "file": nhom,
                            "duoi": "QUA GIO %ds" % han_giay})
            print("  me %2d/%d  QUA GIO %ds (%s...)"
                  % (i, len(me), han_giay, nhom[0]), flush=True)
            continue
        tt = _doc_tom_tat(van)
        if not tt:
            # Me chet giua chung. Day la thong tin, khong phai mot ket qua am:
            # ta BIET me nao va chay lai rieng duoc.
            me_chet.append({"me": i, "file": nhom, "duoi": van.strip()[-300:]})
            print("  me %2d/%d  CHET  (%s)" % (i, len(me), nhom[0]), flush=True)
            continue
        for k in ("xanh", "do", "bo_qua", "loi"):
            tong[k] += tt[k]
        do_me = [d[len("FAILED "):].strip() for d in van.splitlines()
                 if d.startswith("FAILED ")]
        bai_do += do_me
        print("  me %2d/%d  %s" % (i, len(me), tt["dong"]), flush=True)
        # In NGAY ten bai do, dung doi cuoi luot: neu luot bi cat (may treo,
        # Ctrl-C) thi danh sach cuoi khong bao gio duoc in ra. Ban giao 12/09
        # mat dung hai chu `F` theo kieu do.
        for b in do_me:
            print("        DO  " + b, flush=True)

    ra = dict(tong, so_me=len(me), me_chet=me_chet, bai_do=sorted(set(bai_do)),
              giay=round(time.time() - t0, 1))
    (LAB / "reports" / "TEST_TUNG_ME.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra


def main() -> int:
    def lay(c, md):
        return sys.argv[sys.argv.index(c) + 1] if c in sys.argv else md
    r = chay(int(lay("--me", "12")), int(lay("--nhan", "3")),
             lay("--tu-khoa", ""), int(lay("--han", "1800")))
    print("\n=== TONG: %d xanh · %d DO · %d bo qua · %d loi · %.0fs ==="
          % (r["xanh"], r["do"], r["bo_qua"], r["loi"], r["giay"]))
    for b in r["bai_do"]:
        print("   DO  " + b)
    for m in r["me_chet"]:
        print("   ME CHET %d: %s" % (m["me"], " ".join(m["file"])))
    return 1 if (r["do"] or r["loi"] or r["me_chet"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
