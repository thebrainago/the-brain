# -*- coding: utf-8 -*-
"""hang_doi.py - HANG DOI VIEC cua QUANTLAB. Chong nghen, chay song song duoc.

Chu du an 03/09/2026: *"Can phai tang toc cho quantlab hoac tang tinh on dinh
cua no truoc khi tang toc. Xay co che xep hang de tranh nghen va tang toc do
xu li cua quantlab. Uu tien xu li ngoai sinh roi toi noi sinh (hoac lam song
song)."*

VI SAO KHONG DUNG `candidate_queue`. Bang do la **hop dong SEEKER -> QUANTLAB
va CHI-GHI-THEM theo thiet ke**: co trigger chan ca UPDATE lan DELETE, va
`fingerprint UNIQUE` de retry khong sinh ban trung. No la NHAT KY, khong phai
hang doi: khong co cho nao danh dau "da xu ly". Do that 03/09/2026: 555 dong
nam yen tu 21/08, tat ca cung `priority=5`, cung `route=QUANTLAB`, khong ai
tieu thu. Pha tinh chi-ghi-them de nhet trang thai vao la lam hong dau vet
kiem toan cua hop dong do.

Nen day la mot bang RIENG, dat canh no.

BON DIEU FILE NAY PHAI LAM DUNG:

  1. **Idempotent.** `van_tay` UNIQUE. Nap lai cung mot viec khong sinh ban
     trung - bo sinh noi sinh de ra hang nghin viec moi luot, khong the de no
     phinh so.

  2. **LEASE CO HAN, va lease nam trong SQLite chu khong nam tren file.**
     Mot worker chet giua chung phai tu tra viec lai. Bai hoc 24/7 (memory
     `24-7-chet-vi-lease-windows`): lease bang file tren Windows chet vi
     `os.replace` len file dang bi tien trinh khac mo, va no chi hien ra la
     rc=1 khong traceback. SQLite khong co van de do.

  3. **Uu tien NGOAI SINH truoc NOI SINH** (so nho = uu tien cao). Ly do khong
     phai gu: ngoai sinh la thu da co nguoi kiem chung o dau do, con noi sinh
     la to hop may sinh ra hang loat. Khi ngan sach tinh toan co han thi doc
     cai co xac suat tien nghiem cao hon truoc.
     `song_song=True` cho phep tron hai nguon theo han ngach.

  4. **Dem SO LAN THU.** Mot viec hong lap di lap lai phai bi dua ra khoi vong
     chu khong duoc quay mai - do la dang nghen am tham nhat.
"""
from __future__ import annotations

import hashlib
import json
import time

from nhan import so as SO

#: Uu tien mac dinh theo nguon. So NHO = lam truoc.
UU_TIEN = {"ngoai_sinh": 2, "he_da_pass": 1, "seeker": 3, "noi_sinh": 5}

#: Lease het han sau bao lau (giay). Worker chet thi viec tu quay ve CHO.
HAN_LEASE = 900.0

#: Thu qua so lan nay thi coi la HONG HAN.
TOI_DA_THU = 3

_DA_TAO = False

_SCHEMA = """
CREATE TABLE IF NOT EXISTS viec_quantlab(
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  van_tay    TEXT NOT NULL UNIQUE,
  nguon      TEXT NOT NULL,
  uu_tien    INTEGER NOT NULL DEFAULT 5,
  tai_san    TEXT, khung TEXT, template TEXT, tham_so TEXT,
  trang_thai TEXT NOT NULL DEFAULT 'CHO'
             CHECK(trang_thai IN ('CHO','DANG_LAM','XONG','HONG','BO')),
  worker     TEXT, nhan_luc REAL, het_han REAL,
  ket_qua    TEXT, ly_do TEXT, xong_luc TEXT,
  so_lan_thu INTEGER NOT NULL DEFAULT 0,
  tao_luc    TEXT NOT NULL);

CREATE INDEX IF NOT EXISTS ix_viec_lay
  ON viec_quantlab(trang_thai, uu_tien, id);
CREATE INDEX IF NOT EXISTS ix_viec_nguon
  ON viec_quantlab(nguon, trang_thai);
"""


def _bao_dam():
    global _DA_TAO
    if _DA_TAO:
        return
    with SO.ket_noi() as cn:
        cn.executescript(_SCHEMA)
    _DA_TAO = True


def van_tay(nguon: str, tai_san: str, khung: str, template: str,
            tham_so: dict) -> str:
    """Van tay ON DINH cua mot viec. `tham_so` sap khoa de khong phu thu tu."""
    kh = json.dumps(tham_so or {}, sort_keys=True, default=str)
    goc = f"{nguon}|{tai_san}|{khung}|{template}|{kh}"
    return hashlib.sha256(goc.encode("utf-8")).hexdigest()


def nap(cac_viec: list[dict], nguon: str, uu_tien: int | None = None) -> dict:
    """Xep viec vao hang. Tra {'them': n, 'da_co': m}.

    Moi phan tu can: `tai_san`, `khung`, `template`, `tham_so`.
    """
    _bao_dam()
    ut = UU_TIEN.get(nguon, 5) if uu_tien is None else int(uu_tien)
    them = da_co = 0
    luc = SO.bay_gio()
    with SO.ket_noi() as cn:
        for v in cac_viec:
            ts = v.get("tham_so") or {}
            vt = van_tay(nguon, v.get("tai_san", ""), v.get("khung", ""),
                         v.get("template", ""), ts)
            cur = cn.execute(
                "INSERT OR IGNORE INTO viec_quantlab("
                "van_tay,nguon,uu_tien,tai_san,khung,template,tham_so,"
                "trang_thai,tao_luc) VALUES(?,?,?,?,?,?,?,'CHO',?)",
                (vt, nguon, ut, v.get("tai_san"), v.get("khung"),
                 v.get("template"), json.dumps(ts, sort_keys=True, default=str), luc))
            if cur.rowcount == 1:
                them += 1
            else:
                da_co += 1
    return {"nguon": nguon, "them": them, "da_co": da_co, "uu_tien": ut}


def _tra_lease_qua_han(cn, bay: float) -> int:
    """Viec bi worker bo roi -> ve CHO. Day la cai chong NGHEN chinh."""
    cur = cn.execute(
        "UPDATE viec_quantlab SET trang_thai='CHO', worker=NULL, "
        "nhan_luc=NULL, het_han=NULL "
        "WHERE trang_thai='DANG_LAM' AND het_han IS NOT NULL AND het_han < ?",
        (bay,))
    return cur.rowcount


def nhan_viec(worker: str, so_luong: int = 1, nguon: str | None = None,
              han_lease: float = HAN_LEASE) -> list[dict]:
    """Gianh `so_luong` viec MOT CACH NGUYEN TU. Tra danh sach viec da gianh.

    Thu tu: uu_tien tang dan roi id tang dan (FIFO trong cung muc uu tien).
    Viec da thu qua `TOI_DA_THU` lan bi loai khoi vong.
    """
    _bao_dam()
    bay = time.time()
    ra = []
    with SO.ket_noi() as cn:
        cn.execute("BEGIN IMMEDIATE")
        try:
            _tra_lease_qua_han(cn, bay)
            dieu = "trang_thai='CHO' AND so_lan_thu < ?"
            doi = [TOI_DA_THU]
            if nguon:
                dieu += " AND nguon=?"
                doi.append(nguon)
            ids = [r["id"] for r in cn.execute(
                f"SELECT id FROM viec_quantlab WHERE {dieu} "
                f"ORDER BY uu_tien ASC, id ASC LIMIT ?", (*doi, so_luong))]
            if ids:
                dau = ",".join("?" for _ in ids)
                cn.execute(
                    f"UPDATE viec_quantlab SET trang_thai='DANG_LAM', worker=?, "
                    f"nhan_luc=?, het_han=?, so_lan_thu=so_lan_thu+1 "
                    f"WHERE id IN ({dau})",
                    (worker, bay, bay + float(han_lease), *ids))
                for r in cn.execute(
                        f"SELECT * FROM viec_quantlab WHERE id IN ({dau}) "
                        f"ORDER BY uu_tien ASC, id ASC", ids):
                    d = dict(r)
                    try:
                        d["tham_so"] = json.loads(d.get("tham_so") or "{}")
                    except Exception:
                        d["tham_so"] = {}
                    ra.append(d)
            cn.execute("COMMIT")
        except Exception:
            cn.execute("ROLLBACK")
            raise
    return ra


def xong(viec_id: int, ket_qua: dict | None = None) -> None:
    _bao_dam()
    with SO.ket_noi() as cn:
        cn.execute(
            "UPDATE viec_quantlab SET trang_thai='XONG', ket_qua=?, xong_luc=?, "
            "worker=NULL, het_han=NULL WHERE id=?",
            (json.dumps(ket_qua or {}, default=str), SO.bay_gio(), int(viec_id)))


def that_bai(viec_id: int, ly_do: str) -> None:
    """Tra viec ve CHO de thu lai, hoac danh HONG neu da qua so lan."""
    _bao_dam()
    with SO.ket_noi() as cn:
        r = cn.execute("SELECT so_lan_thu FROM viec_quantlab WHERE id=?",
                       (int(viec_id),)).fetchone()
        n = int(r["so_lan_thu"]) if r else TOI_DA_THU
        moi = "HONG" if n >= TOI_DA_THU else "CHO"
        cn.execute(
            "UPDATE viec_quantlab SET trang_thai=?, ly_do=?, worker=NULL, "
            "het_han=NULL, xong_luc=? WHERE id=?",
            (moi, str(ly_do)[:300], SO.bay_gio() if moi == "HONG" else None,
             int(viec_id)))


def trang_thai() -> dict:
    """Do sau hang doi theo nguon x trang thai + so lease qua han dang treo."""
    _bao_dam()
    bay = time.time()
    ra: dict = {"theo_nguon": {}, "tong": {}, "lease_qua_han": 0}
    for r in SO.nhieu("SELECT nguon, trang_thai, COUNT(*) n FROM viec_quantlab "
                      "GROUP BY nguon, trang_thai") or []:
        d = dict(r)
        ra["theo_nguon"].setdefault(d["nguon"], {})[d["trang_thai"]] = d["n"]
        ra["tong"][d["trang_thai"]] = ra["tong"].get(d["trang_thai"], 0) + d["n"]
    q = SO.mot("SELECT COUNT(*) n FROM viec_quantlab WHERE trang_thai='DANG_LAM' "
               "AND het_han IS NOT NULL AND het_han < ?", bay)
    ra["lease_qua_han"] = int(q["n"]) if q else 0
    return ra


def don_lease_treo() -> int:
    """Goi tu supervisor: tra moi lease qua han ve CHO. Tra so viec da tra."""
    _bao_dam()
    with SO.ket_noi() as cn:
        return _tra_lease_qua_han(cn, time.time())
