# -*- coding: utf-8 -*-
"""so_lenh.py - SO LENH PAPER: cho mot he DA QUA CONG di tiep, khong dung o nhan.

## Vi sao module nay ton tai

Do 11/09/2026: `grep -rE "paper|live_shadow|kill_switch|decay"` tren toan bo
`nhan/`, `tru/`, `qwen/` tra ve **0 file**. He nay ton tai de ra tien va khong co
MOT DONG NAO cham toi tien. Cong ra tien da cham 35.937 to hop va cho ra dung 1
nguoi song sot - nhung khong co cho nao nhan no.

Kien truc V2 goi day la "mot boundary rieng, chua dat". Dat no o cuoi la sai thu
tu: **no dinh nghia 'xong' nghia la gi**. Khong co no, cong ra tien dang cham mot
thu chua ai nhan.

## May trang thai - khong duoc nhay coc

    PAPER_CANDIDATE -> PAPER -> LIVE_SHADOW -> LIVE_CAP

    PAPER_CANDIDATE  qua cong, chua chay ngay nao
    PAPER            dang ghi lenh tren gia THAT, tien GIA
    LIVE_SHADOW      dat lenh that nhung khoi luong toi thieu, de do TRUOT GIA
    LIVE_CAP         von that, CO TRAN

Khong mot ket qua nao duoc tu dong sang LIVE chi vi co nhan PASS. Chuyen trang
thai len phia truoc **luon** can `nguoi_duyet` - module nay khong tu duyet.

## Hop dong

So la CHI-THEM. Mot lenh da dong khong duoc sua; sua nhan dinh thi ghi dong moi.
Ly do: so lenh la thu duy nhat doi chieu duoc voi backtest, va mot so bi sua thi
phep doi chieu do mat y nghia.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

TRANG_THAI = ("PAPER_CANDIDATE", "PAPER", "LIVE_SHADOW", "LIVE_CAP", "DUNG")
#: Chuyen tiep HOP LE. Luon di mot buoc len; xuong thi di dau cung duoc (dung
#: khan cap phai luon lam duoc).
_LEN = {"PAPER_CANDIDATE": "PAPER", "PAPER": "LIVE_SHADOW",
        "LIVE_SHADOW": "LIVE_CAP"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS he_chay(
  ma         TEXT PRIMARY KEY,
  gt_ma      TEXT,
  tai_san    TEXT,
  khung      TEXT,
  trang_thai TEXT NOT NULL DEFAULT 'PAPER_CANDIDATE',
  von        REAL DEFAULT 0,
  tran_von   REAL DEFAULT 0,
  bat_dau    TEXT,
  doi_luc    TEXT,
  nguoi_duyet TEXT,
  ghi_chu    TEXT
);

CREATE TABLE IF NOT EXISTS lenh_paper(
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  he       TEXT NOT NULL,
  chieu    INTEGER NOT NULL,
  luc_vao  TEXT NOT NULL,
  gia_vao  REAL NOT NULL,
  lot      REAL NOT NULL,
  luc_ra   TEXT,
  gia_ra   REAL,
  phi      REAL DEFAULT 0,
  ly_do_ra TEXT,
  r        REAL,
  ghi_chu  TEXT
);
CREATE INDEX IF NOT EXISTS ix_lenh_he ON lenh_paper(he, id);

CREATE TRIGGER IF NOT EXISTS lenh_paper_khong_xoa
BEFORE DELETE ON lenh_paper BEGIN
  SELECT RAISE(ABORT, 'so lenh la CHI-THEM: mot lenh da ghi khong duoc xoa');
END;
"""


def _khoi_tao() -> None:
    with SO.ket_noi() as cn:
        cn.executescript(_SCHEMA)


def dang_ky_he(ma: str, gt_ma: str, tai_san: str, khung: str,
               ghi_chu: str = "") -> dict:
    """Dua mot he DA QUA CONG vao trang thai PAPER_CANDIDATE."""
    _khoi_tao()
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT INTO he_chay(ma,gt_ma,tai_san,khung,trang_thai,bat_dau,"
            "doi_luc,ghi_chu) VALUES(?,?,?,?,'PAPER_CANDIDATE',?,?,?) "
            "ON CONFLICT(ma) DO NOTHING",
            (ma, gt_ma, tai_san, khung, SO.bay_gio(), SO.bay_gio(), ghi_chu))
    SO.ghi_su_kien("CHAM_TIEN", "dang_ky_he",
                   {"he": ma, "gt_ma": gt_ma, "tai_san": tai_san})
    return he(ma)


def he(ma: str) -> dict | None:
    _khoi_tao()
    r = SO.mot("SELECT * FROM he_chay WHERE ma = ?", ma)
    return dict(r) if r else None


def doi_trang_thai(ma: str, moi: str, nguoi_duyet: str = "",
                   tran_von: float = 0.0) -> dict:
    """Doi trang thai. LEN mot buoc va PHAI co nguoi duyet; XUONG thi tu do.

    Khong co `nguoi_duyet` thi tu choi - ke ca khi goi tu code. Day la duong
    duy nhat tien that di qua, va no khong duoc mo bang mot vong lap tu dong.
    """
    _khoi_tao()
    cu = he(ma)
    if not cu:
        return {"nhan": False, "ly_do": [f"chua dang ky he {ma!r}"]}
    if moi not in TRANG_THAI:
        return {"nhan": False, "ly_do": [f"trang thai la {moi!r}, phai thuoc {TRANG_THAI}"]}
    di_len = _LEN.get(cu["trang_thai"]) == moi
    if moi != "DUNG" and not di_len and moi != cu["trang_thai"]:
        # khong cho nhay coc: PAPER_CANDIDATE -> LIVE_CAP la cai bay ro nhat
        thu_tu = list(TRANG_THAI)
        if thu_tu.index(moi) > thu_tu.index(cu["trang_thai"]):
            return {"nhan": False, "ly_do": [
                f"khong duoc nhay coc {cu['trang_thai']} -> {moi}; "
                f"buoc ke tiep hop le la {_LEN.get(cu['trang_thai'])!r}"]}
    if di_len and not nguoi_duyet.strip():
        return {"nhan": False, "ly_do": [
            f"len {moi} PHAI co `nguoi_duyet`. Khong mot ket qua nao duoc tu dong "
            f"giao dich tien that chi vi co nhan PASS."]}
    if moi == "LIVE_CAP" and tran_von <= 0:
        return {"nhan": False, "ly_do": ["LIVE_CAP phai co `tran_von` > 0"]}
    with SO.ket_noi() as cn:
        cn.execute("UPDATE he_chay SET trang_thai=?, doi_luc=?, nguoi_duyet=?, "
                   "tran_von=? WHERE ma=?",
                   (moi, SO.bay_gio(), nguoi_duyet, tran_von or cu["tran_von"], ma))
    SO.ghi_su_kien("CHAM_TIEN", "doi_trang_thai",
                   {"he": ma, "tu": cu["trang_thai"], "sang": moi,
                    "nguoi_duyet": nguoi_duyet, "tran_von": tran_von})
    return {"nhan": True, "ly_do": [], "he": he(ma)}


def vao_lenh(he_ma: str, chieu: int, luc: str, gia: float, lot: float,
             ghi_chu: str = "") -> dict:
    _khoi_tao()
    h = he(he_ma)
    if not h:
        return {"nhan": False, "ly_do": [f"chua dang ky he {he_ma!r}"]}
    if h["trang_thai"] == "PAPER_CANDIDATE":
        return {"nhan": False, "ly_do": [
            "he dang o PAPER_CANDIDATE - phai doi sang PAPER truoc khi ghi lenh"]}
    if h["trang_thai"] == "DUNG":
        return {"nhan": False, "ly_do": ["he da DUNG"]}
    with SO.ket_noi() as cn:
        cur = cn.execute(
            "INSERT INTO lenh_paper(he,chieu,luc_vao,gia_vao,lot,ghi_chu) "
            "VALUES(?,?,?,?,?,?)",
            (he_ma, 1 if chieu > 0 else -1, luc, float(gia), float(lot), ghi_chu))
    return {"nhan": True, "ly_do": [], "id": int(cur.lastrowid)}


def ra_lenh(lenh_id: int, luc: str, gia: float, phi: float = 0.0,
            ly_do: str = "") -> dict:
    _khoi_tao()
    r = SO.mot("SELECT * FROM lenh_paper WHERE id = ?", lenh_id)
    if not r:
        return {"nhan": False, "ly_do": [f"khong co lenh {lenh_id}"]}
    if r["luc_ra"]:
        return {"nhan": False, "ly_do": [
            f"lenh {lenh_id} da dong luc {r['luc_ra']} - so la CHI-THEM, "
            f"khong sua lenh da dong"]}
    lai = (float(gia) - r["gia_vao"]) * r["chieu"] * r["lot"] - float(phi)
    with SO.ket_noi() as cn:
        cn.execute("UPDATE lenh_paper SET luc_ra=?,gia_ra=?,phi=?,ly_do_ra=?,r=? "
                   "WHERE id=?",
                   (luc, float(gia), float(phi), ly_do, lai, lenh_id))
    return {"nhan": True, "ly_do": [], "lai": lai}


def lenh_cua(he_ma: str, con_mo: bool | None = None) -> list[dict]:
    _khoi_tao()
    q = "SELECT * FROM lenh_paper WHERE he = ?"
    if con_mo is True:
        q += " AND luc_ra IS NULL"
    elif con_mo is False:
        q += " AND luc_ra IS NOT NULL"
    return [dict(r) for r in SO.nhieu(q + " ORDER BY id", he_ma)]


def tong_ket(he_ma: str) -> dict:
    d = lenh_cua(he_ma, con_mo=False)
    lai = [x["r"] or 0.0 for x in d]
    von = 0.0
    dinh = 0.0
    sut = 0.0
    for x in lai:
        von += x
        dinh = max(dinh, von)
        sut = min(sut, von - dinh)
    thang = sum(1 for x in lai if x > 0)
    return {"he": he_ma, "so_lenh": len(d), "con_mo": len(lenh_cua(he_ma, True)),
            "tong_lai": round(von, 4), "sut_giam": round(sut, 4),
            "ty_le_thang": round(thang / len(d), 4) if d else None}


if __name__ == "__main__":
    _khoi_tao()
    for r in SO.nhieu("SELECT * FROM he_chay ORDER BY ma"):
        print(json.dumps({**dict(r), **tong_ket(r["ma"])}, ensure_ascii=False))
