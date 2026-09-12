# -*- coding: utf-8 -*-
"""gop_wal.py - GOP `nao.db-wal` VAO DB. Cai phanh cho mot kieu day dia lang le.

## Cai da xay ra 12/09/2026

O C con **177 MB tren 120 GB**, va hau qua khong hien ra nhu mot loi dia. No
hien ra nhu ba viec bao "xong":

    boc 684 file chi bao   -> 0 co che moi
    xao_ma_llm      221s   -> XONG rc=0, kho 2.554 khong doi
    xao_hoc_thuat   222s   -> XONG rc=0, kho 2.554 khong doi

Loi that (`sqlite3.OperationalError: database or disk is full`) nam sau ba lop:
ham boc bat Exception roi tra ve rong · hang doi cham theo MA THOAT nen thay
rc=0 · va khong ai nhin dung cho.

Cho do la **`nao.db-wal` = 1,4 GB**, dung bang chinh `nao.db`. WAL chi duoc gop
vao db khi mot checkpoint chay tron. Tien trinh bi giet giua chung - qua han,
Ctrl-C, pool worker bi don - thi WAL o lai, va lan ghi sau noi tiep vao do. No
lon len lang le cho toi khi dia day.

Sau khi gop: 1,4 GB ve 0, dia 177 MB -> 8,8 GB.

## BUSY LA TRANG THAI BINH THUONG, KHONG PHAI LOI

`PRAGMA wal_checkpoint(TRUNCATE)` tra `(1, -1, -1)` khi con ket noi khac dang
mo - khong gop duoc gi. Do la ly do ham nay bao ro BUSY thay vi im lang tra ve
"xong": mot lenh don dep bao "xong" ma khong don gi la thu nguy hiem hon khong
co lenh don dep.

Chay:  python -m nhan.gop_wal          gop WAL cua nao.db
       python -m nhan.gop_wal --het    gop moi *.db trong lab
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))


def _mb(p: Path) -> float:
    try:
        return p.stat().st_size / (1024 ** 2)
    except Exception:
        return 0.0


def gop_mot(db: Path, in_ra=print) -> dict:
    """Gop WAL cua mot db. Tra {truoc_mb, sau_mb, busy}."""
    wal = db.with_name(db.name + "-wal")
    truoc = _mb(wal)
    if not db.exists():
        return {"bo": "khong co %s" % db.name}
    try:
        cn = sqlite3.connect(str(db), timeout=120)
        r = cn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        cn.close()
    except Exception as e:
        in_ra("  %s: LOI %s" % (db.name, e))
        return {"db": db.name, "loi": str(e)[:120]}
    busy = bool(r and r[0] == 1)
    sau = _mb(wal)
    if busy:
        in_ra("  %s: BUSY - con ket noi khac dang mo, KHONG gop duoc."
              % db.name)
        in_ra("      Dung tien trinh dang ghi roi chay lai "
              "(`python -m nhan.don_mo_coi --don`).")
    else:
        in_ra("  %s: WAL %.0f MB -> %.0f MB" % (db.name, truoc, sau))
    return {"db": db.name, "truoc_mb": round(truoc), "sau_mb": round(sau),
            "busy": busy, "giai_phong_mb": round(max(truoc - sau, 0))}


def gop_het(in_ra=print) -> dict:
    ra = [gop_mot(p, in_ra=in_ra) for p in sorted(LAB.glob("*.db"))]
    tong = sum(x.get("giai_phong_mb", 0) for x in ra)
    in_ra("")
    in_ra("giai phong %d MB tu %d co so du lieu" % (tong, len(ra)))
    return {"db": ra, "giai_phong_mb": tong}


def main(argv: list[str]) -> int:
    if "--het" in argv:
        gop_het()
    else:
        gop_mot(LAB / "nao.db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
