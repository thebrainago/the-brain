# -*- coding: utf-8 -*-
"""kho_co_che.py - DINH DANG CHUNG (the he / co che) + KHO CO CHE TICH LUY (18/10/2026).

Chu du an: ung vien bi loai thi BOC co che dang dung (nguon lenh, bo loc, moc/vung, xu li lenh: DCA, hedge, go, trailing,
chot ro) vao kho tich luy, roi thu ket hop voi nhau. Khong vut manh nao vi no thua khi dung mot minh.

THE HE (ung vien) - dict JSON:
  id, ten, loai (he_hoan_thien | co_che | tien_ich | mo_ta), uu_tien (so nho = lam truoc), nen_tang (BRAIN | MQL5 | MQL4 |
  Python | Pine), nguon {kho, tep, url}, duong_dich (noi_bo | spec_dsl | llm | mt5_truc_tiep | bo_qua), ly_do_duong,
  tin_hieu {kieu: brain|spec, tham{}, khoang{}, specs[]}, quan_tri_goc [nhan ky thuat tu kiem ke], ea_mt5 {file, url},
  nhan [].
CO CHE - dict JSON:
  id, vai_tro (VAI_TRO), ten, mo_ta, tham {}, khoang {}, tu_the (id the he goc), kho, do_duoc {so do tot nhat neu co},
  nhan [] (vd "MÔ PHỎNG", "PHÍ TẠM"), luc.
Kho: SQLite `data/kho_co_che/kho.sqlite` (data/ bi git bo qua). Tom tat cho nguoi doc: `reports/KHO_CO_CHE_TICH_LUY.md`.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
KHO = GOC / "data" / "kho_co_che" / "kho.sqlite"
TOM_TAT = GOC / "reports" / "KHO_CO_CHE_TICH_LUY.md"

VAI_TRO = ("nguon_lenh", "bo_loc", "moc_vung", "quan_li", "go_lenh")
LOAI = ("he_hoan_thien", "co_che", "tien_ich", "mo_ta")
TEN_VAI_TRO = {"nguon_lenh": "nguồn lệnh", "bo_loc": "bộ lọc", "moc_vung": "mốc/vùng", "quan_li": "quản lí",
               "go_lenh": "gỡ lệnh"}
#: nhan ky thuat cua kiem ke Seeker (`tru/seeker.py kiem-ke`) -> vai tro
VAI_TU_NHAN = {"dca": "quan_li", "martingale": "quan_li", "luoi": "quan_li", "trailing": "quan_li", "hoa_von": "quan_li",
               "chot_ro": "quan_li", "dong_mot_phan": "quan_li", "sua_sl_tp": "quan_li", "lenh_cho": "nguon_lenh",
               "hedge": "go_lenh", "go_lenh": "go_lenh", "loc_spread": "bo_loc", "loc_phien": "bo_loc", "loc_tin": "bo_loc"}


def ma_id(*phan) -> str:
    return hashlib.sha1(json.dumps(phan, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


def co_che(vai_tro: str, ten: str, mo_ta: str = "", tham: dict | None = None, khoang: dict | None = None,
           tu_the: str = "", kho: str = "", do_duoc: dict | None = None, nhan: list | None = None) -> dict:
    if vai_tro not in VAI_TRO:
        raise ValueError("vai_tro phai la mot trong %s" % (VAI_TRO,))
    return {"id": ma_id(vai_tro, ten, tham or {}, tu_the), "vai_tro": vai_tro, "ten": ten, "mo_ta": mo_ta,
            "tham": tham or {}, "khoang": khoang or {}, "tu_the": tu_the, "kho": kho, "do_duoc": do_duoc or {},
            "nhan": list(nhan or []), "luc": time.strftime("%Y-%m-%dT%H:%M:%S")}


def kiem_co_che(c: dict) -> list[str]:
    loi = [k for k in ("id", "vai_tro", "ten", "tham") if k not in c]
    if c.get("vai_tro") not in VAI_TRO:
        loi.append("vai_tro sai: %s" % c.get("vai_tro"))
    return loi


def _ket_noi(tep: Path | None = None) -> sqlite3.Connection:
    p = Path(tep or KHO)
    p.parent.mkdir(parents=True, exist_ok=True)
    cn = sqlite3.connect(str(p), timeout=30)
    cn.execute("CREATE TABLE IF NOT EXISTS co_che (id TEXT PRIMARY KEY, vai_tro TEXT, ten TEXT, tu_the TEXT, "
               "json TEXT, so_lan_dung INTEGER DEFAULT 0, cap_nhat TEXT)")
    return cn


def them(ds: list[dict], tep: Path | None = None) -> int:
    """Them / cap nhat co che (khoa = id). -> so co che MOI."""
    cn = _ket_noi(tep)
    moi = 0
    with cn:
        for c in ds:
            loi = kiem_co_che(c)
            if loi:
                raise ValueError("; ".join(loi))
            cu = cn.execute("SELECT json FROM co_che WHERE id=?", (c["id"],)).fetchone()
            if cu:
                d = json.loads(cu[0])
                if c.get("do_duoc"):
                    d["do_duoc"] = c["do_duoc"]
                d["nhan"] = sorted(set(d.get("nhan", [])) | set(c.get("nhan", [])))
                c = d
            else:
                moi += 1
            cn.execute("INSERT OR REPLACE INTO co_che (id, vai_tro, ten, tu_the, json, cap_nhat) VALUES (?,?,?,?,?,?)",
                       (c["id"], c["vai_tro"], c["ten"], c.get("tu_the", ""), json.dumps(c, ensure_ascii=False),
                        time.strftime("%Y-%m-%dT%H:%M:%S")))
    cn.close()
    return moi


def lay(vai_tro: str | None = None, tep: Path | None = None) -> list[dict]:
    cn = _ket_noi(tep)
    q = "SELECT json FROM co_che" + (" WHERE vai_tro=?" if vai_tro else "") + " ORDER BY id"
    ra = [json.loads(r[0]) for r in cn.execute(q, (vai_tro,) if vai_tro else ())]
    cn.close()
    return ra


def ghi_tom_tat(tep: Path | None = None, ra: Path | None = None) -> str:
    ds = lay(tep=tep)
    dong = ["# Kho cơ chế tích luỹ (tự sinh bởi `python ong_dan.py boc`, đừng sửa tay)", "",
            "Kho gốc: `data/kho_co_che/kho.sqlite` (git bỏ qua). Số đo trong kho là MÔ PHỎNG Python, phí là PHÍ TẠM "
            "cho tới khi máy nhà đo xong `reports/phi_san/`.", "",
            "| Vai trò | Số cơ chế |", "|---|---|"]
    for v in VAI_TRO:
        dong.append("| %s | %d |" % (TEN_VAI_TRO[v], sum(1 for c in ds if c["vai_tro"] == v)))
    dong += ["", "Mỗi vai trò liệt kê tối đa 60 cơ chế, cơ chế đã đo đứng trước (lãi cao trước).", "",
             "| Vai trò | Tên | Từ thẻ | Tham số | Đo được (MÔ PHỎNG) |", "|---|---|---|---|---|"]
    chon = []
    for v in VAI_TRO:
        x = [c for c in ds if c["vai_tro"] == v]
        x.sort(key=lambda c: (-(c.get("do_duoc") or {}).get("lai_pct_nam", -1e9), c["ten"]))
        chon += x[:60]
    for c in chon:
        dd = c.get("do_duoc") or {}
        so = ("lãi %.1f%%/năm, sụt %.1f%%" % (dd["lai_pct_nam"], dd["sut_giam_pct"])) if "lai_pct_nam" in dd else "-"
        dong.append("| %s | %s | %s | `%s` | %s |" % (TEN_VAI_TRO[c["vai_tro"]], c["ten"][:60], (c.get("tu_the") or "-")[:40],
                                                    json.dumps(c.get("tham") or {}, ensure_ascii=False)[:80], so))
    s = "\n".join(dong) + "\n"
    p = Path(ra or TOM_TAT)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")
    return s
