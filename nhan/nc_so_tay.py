# -*- coding: utf-8 -*-
"""nc_so_tay.py - SO TAY NGHIEN CUU: bo nho dai han cua nha nghien cuu AI (gia thuyet, thi nghiem, hieu biet, cau hoi).

## VI SAO CAN (va vi sao truoc day AI bi tuoc quyen)

`qwen/tac_tu.py` ghi ro ly do he tu chay KHONG cho LLM chon viec: *"da do duoc
rang mot LLM khong bo nho ngoai se lap lai viec cu va chon viec de"*. Phep do
dung - nhung ket luan rut ra sai huong: cai thieu la BO NHO NGOAI, khong phai
quyen quyet dinh. Tuoc quyen thi he khong con ai nghi; cho bo nho thi AI nghi
duoc ma khong lap lai.

So tay nay la bo nho do. Moi chu ky cua nha nghien cuu BAT DAU bang `tom_tat()`
(ho so nghien cuu: da thu gi, cai gi dang co trien vong, hieu biet nao da co
bang chung, cau hoi nao con mo) va KET THUC bang viec ghi hieu biet + cau hoi.

## NAM BANG

    gia_thuyet  cau phat bieu + VI SAO co nguoi tra tien + trang thai + cha/con
    thi_nghiem  MOI lan cong cu chay: dau vao, ket qua, 3 trang thai, SO PHEP THU
    hieu_biet   dieu da hoc duoc, co DO TIN va BANG CHUNG (id thi nghiem)
    cau_hoi     chuong trinh nghien cuu: cau hoi mo, uu tien, ai dat (nguoi/ai)
    vong        moi chu ky tac tu: ai chay, mo hinh, token, tom tat
    niem_phong  moi lan mo doan niem phong - MOT lan cho moi khai bao

## HAI CHOT CHONG TU LUA MINH

1. **Van tay thi nghiem.** Cung cong cu + cung dau vao = cung van tay. Chay lai
   thi TRA KET QUA CU va khong tinh them phep thu. AI khong the "thu lai cho
   may" - va so phep thu that dung la so cau hoi khac nhau da hoi du lieu.
2. **Dem phep thu.** Moi ket qua cuoi (niem phong) mang theo so phep thu da
   tieu tren dong gia thuyet do va tren (ma, khung) do. Mot Sharpe 1,5 sau 3
   phep thu va sau 3.000 phep thu la hai con so khac nhau.

File DB: `nc.db` o goc lab (bo qua boi `.gitignore` `*.db`). Khong dung vao
`nao.db` - so cai chung cua bon tru giu nguyen, va bo test co `conftest` canh
no phinh. Doi duong dan: `NC_DB=<file>` hoac gan `nc_so_tay.DB`.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
DB = Path(os.environ.get("NC_DB") or (LAB / "nc.db"))

TRANG_THAI_GT = ("MO", "DANG_THU", "TRIEN_VONG", "BAC_BO", "XAC_NHAN", "TRUOT_NIEM_PHONG")
TRANG_THAI_TN = ("DAT", "AM", "CHUA_DO_DUOC")

SCHEMA = """
CREATE TABLE IF NOT EXISTS gia_thuyet(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, ma TEXT UNIQUE, cau TEXT,
  vi_sao TEXT, ho TEXT, pham_vi TEXT, cha INTEGER, nguon TEXT,
  uu_tien REAL DEFAULT 0.5, trang_thai TEXT DEFAULT 'MO', ket_luan TEXT,
  cap_nhat TEXT);
CREATE TABLE IF NOT EXISTS thi_nghiem(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, gt_id INTEGER, loai TEXT,
  ma TEXT, khung TEXT, doan TEXT, van_tay TEXT, dau_vao TEXT, ket_qua TEXT,
  trang_thai TEXT, so_phep_thu INTEGER DEFAULT 1, giay REAL, vong_id INTEGER,
  tom_tat TEXT);
CREATE INDEX IF NOT EXISTS ix_tn_vt ON thi_nghiem(van_tay);
CREATE INDEX IF NOT EXISTS ix_tn_gt ON thi_nghiem(gt_id);
CREATE TABLE IF NOT EXISTS hieu_biet(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, cau TEXT, do_tin REAL,
  pham_vi TEXT, bang_chung TEXT, trang_thai TEXT DEFAULT 'HIEU_LUC',
  cap_nhat TEXT);
CREATE TABLE IF NOT EXISTS cau_hoi(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, cau TEXT, vi_sao TEXT,
  uu_tien REAL DEFAULT 0.5, nguon TEXT DEFAULT 'ai', trang_thai TEXT DEFAULT 'MO',
  gt_id INTEGER, tra_loi TEXT, cap_nhat TEXT);
CREATE TABLE IF NOT EXISTS vong(
  id INTEGER PRIMARY KEY AUTOINCREMENT, bat_dau TEXT, ket_thuc TEXT, tac_tu TEXT,
  mo_hinh TEXT, tom_tat TEXT, so_cong_cu INTEGER DEFAULT 0,
  token_vao INTEGER DEFAULT 0, token_ra INTEGER DEFAULT 0, usd REAL DEFAULT 0,
  trang_thai TEXT DEFAULT 'DANG');
CREATE TABLE IF NOT EXISTS niem_phong(
  id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT, van_tay TEXT UNIQUE,
  gt_id INTEGER, ma TEXT, khung TEXT, spec TEXT, ket_qua TEXT, trang_thai TEXT);
"""


def bay_gio() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def ket_noi():
    DB.parent.mkdir(parents=True, exist_ok=True)
    cn = sqlite3.connect(str(DB), timeout=30.0)
    cn.row_factory = sqlite3.Row
    try:
        cn.execute("PRAGMA journal_mode=WAL")
        cn.executescript(SCHEMA)
        yield cn
        cn.commit()
    finally:
        cn.close()


def _dict(r) -> dict:
    return {k: r[k] for k in r.keys()} if r is not None else {}


def nhieu(sql: str, *ts) -> list[dict]:
    with ket_noi() as cn:
        return [_dict(r) for r in cn.execute(sql, ts).fetchall()]


def mot(sql: str, *ts) -> dict:
    with ket_noi() as cn:
        return _dict(cn.execute(sql, ts).fetchone())


def _json(x) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, default=str)


def van_tay(*phan) -> str:
    """Van tay chuan tac: JSON sort_keys cua moi phan -> sha1 16 ky tu."""
    return hashlib.sha1(_json(list(phan)).encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------- GIA THUYET
def them_gia_thuyet(cau: str, vi_sao: str = "", ho: str = "", pham_vi=None,
                    cha: int | None = None, nguon: str = "ai", uu_tien: float = 0.5,
                    ma: str | None = None) -> int:
    """Ghi mot gia thuyet. `ma` trung -> tra id cu (khong ghi de)."""
    ma = ma or ("gt_" + van_tay(cau, ho, pham_vi))
    cu = mot("SELECT id FROM gia_thuyet WHERE ma=?", ma)
    if cu:
        return int(cu["id"])
    with ket_noi() as cn:
        c = cn.execute(
            "INSERT INTO gia_thuyet(luc,ma,cau,vi_sao,ho,pham_vi,cha,nguon,uu_tien,"
            "trang_thai,cap_nhat) VALUES(?,?,?,?,?,?,?,?,?,'MO',?)",
            (bay_gio(), ma, cau, vi_sao, ho, _json(pham_vi or {}), cha, nguon,
             float(uu_tien), bay_gio()))
        return int(c.lastrowid)


def cap_nhat_gia_thuyet(gt_id: int, trang_thai: str | None = None,
                        ket_luan: str | None = None, uu_tien: float | None = None) -> dict:
    if trang_thai and trang_thai not in TRANG_THAI_GT:
        raise ValueError("trang_thai phai thuoc %s" % (TRANG_THAI_GT,))
    gt = mot("SELECT * FROM gia_thuyet WHERE id=?", int(gt_id))
    if not gt:
        raise KeyError("khong co gia thuyet id=%s" % gt_id)
    with ket_noi() as cn:
        cn.execute("UPDATE gia_thuyet SET trang_thai=COALESCE(?,trang_thai), "
                   "ket_luan=COALESCE(?,ket_luan), uu_tien=COALESCE(?,uu_tien), "
                   "cap_nhat=? WHERE id=?",
                   (trang_thai, ket_luan, uu_tien, bay_gio(), int(gt_id)))
    return mot("SELECT * FROM gia_thuyet WHERE id=?", int(gt_id))


def dong_ho(gt_id: int) -> list[int]:
    """Id cua gia thuyet va MOI hau due (con, chau...) - de dem phep thu theo dong."""
    ra, mo = [], [int(gt_id)]
    while mo:
        x = mo.pop()
        if x in ra:
            continue
        ra.append(x)
        mo += [int(r["id"]) for r in nhieu("SELECT id FROM gia_thuyet WHERE cha=?", x)]
    return ra


def goc_cua(gt_id: int) -> int:
    x, da = int(gt_id), set()
    while x not in da:
        da.add(x)
        r = mot("SELECT cha FROM gia_thuyet WHERE id=?", x)
        if not r or r.get("cha") is None:
            return x
        x = int(r["cha"])
    return x


# --------------------------------------------------------------- THI NGHIEM
def da_thu(van_tay_tn: str) -> dict:
    """Ket qua cua lan chay truoc cung van tay (rong neu chua)."""
    r = mot("SELECT * FROM thi_nghiem WHERE van_tay=? AND trang_thai!='CHUA_DO_DUOC' "
            "ORDER BY id DESC LIMIT 1", van_tay_tn)
    if r and r.get("ket_qua"):
        try:
            r["ket_qua"] = json.loads(r["ket_qua"])
        except Exception:
            pass
    return r


def ghi_thi_nghiem(loai: str, dau_vao: dict, ket_qua: dict, trang_thai: str,
                   van_tay_tn: str, ma: str = "", khung: str = "", doan: str = "",
                   gt_id: int | None = None, so_phep_thu: int = 1, giay: float = 0.0,
                   vong_id: int | None = None, tom_tat: str = "") -> int:
    if trang_thai not in TRANG_THAI_TN:
        raise ValueError("trang_thai thi nghiem phai thuoc %s" % (TRANG_THAI_TN,))
    with ket_noi() as cn:
        c = cn.execute(
            "INSERT INTO thi_nghiem(luc,gt_id,loai,ma,khung,doan,van_tay,dau_vao,ket_qua,"
            "trang_thai,so_phep_thu,giay,vong_id,tom_tat) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (bay_gio(), gt_id, loai, ma, khung, doan, van_tay_tn, _json(dau_vao),
             _json(ket_qua), trang_thai, int(so_phep_thu), float(giay), vong_id,
             tom_tat[:600]))
        return int(c.lastrowid)


def dem_phep_thu(gt_id: int | None = None, ma: str | None = None,
                 khung: str | None = None, doan: str = "kham_pha") -> int:
    """So phep thu da tieu - theo DONG gia thuyet (goc + hau due) hoac theo (ma, khung)."""
    if gt_id is not None:
        ids = dong_ho(goc_cua(int(gt_id)))
        cho = ",".join("?" * len(ids))
        r = mot("SELECT COALESCE(SUM(so_phep_thu),0) n FROM thi_nghiem WHERE doan=? "
                "AND gt_id IN (%s)" % cho, doan, *ids)
        return int(r.get("n") or 0)
    r = mot("SELECT COALESCE(SUM(so_phep_thu),0) n FROM thi_nghiem WHERE doan=? "
            "AND ma=? AND khung=?", doan, str(ma or "").upper(), str(khung or "").upper())
    return int(r.get("n") or 0)


# ------------------------------------------------------------ HIEU BIET
def them_hieu_biet(cau: str, do_tin: float, bang_chung: list[int] | None = None,
                   pham_vi=None) -> int:
    """Mot dieu da hoc duoc. `bang_chung` = id thi nghiem - khong co thi do tin <= 0,3."""
    bc = [int(x) for x in (bang_chung or [])]
    ton_tai = {int(r["id"]) for r in nhieu(
        "SELECT id FROM thi_nghiem WHERE id IN (%s)" % ",".join("?" * len(bc)), *bc)} if bc else set()
    thieu = [x for x in bc if x not in ton_tai]
    if thieu:
        raise KeyError("bang chung tro toi thi nghiem khong ton tai: %s" % thieu)
    dt = max(0.0, min(1.0, float(do_tin)))
    if not bc:
        dt = min(dt, 0.3)
    with ket_noi() as cn:
        c = cn.execute("INSERT INTO hieu_biet(luc,cau,do_tin,pham_vi,bang_chung,cap_nhat) "
                       "VALUES(?,?,?,?,?,?)",
                       (bay_gio(), cau, dt, _json(pham_vi or {}), _json(bc), bay_gio()))
        return int(c.lastrowid)


def bac_hieu_biet(hb_id: int, ly_do: str, bang_chung: list[int] | None = None) -> None:
    with ket_noi() as cn:
        cn.execute("UPDATE hieu_biet SET trang_thai='BI_BAC', cap_nhat=?, "
                   "cau = cau || ' [BI BAC: ' || ? || ' | tn ' || ? || ']' WHERE id=?",
                   (bay_gio(), ly_do[:300], _json(bang_chung or []), int(hb_id)))


# --------------------------------------------------------------- CAU HOI
def them_cau_hoi(cau: str, vi_sao: str = "", uu_tien: float = 0.5, nguon: str = "ai",
                 gt_id: int | None = None) -> int:
    cu = mot("SELECT id FROM cau_hoi WHERE cau=? AND trang_thai IN ('MO','DANG')", cau)
    if cu:
        return int(cu["id"])
    with ket_noi() as cn:
        c = cn.execute("INSERT INTO cau_hoi(luc,cau,vi_sao,uu_tien,nguon,gt_id,cap_nhat) "
                       "VALUES(?,?,?,?,?,?,?)",
                       (bay_gio(), cau, vi_sao, float(uu_tien), nguon, gt_id, bay_gio()))
        return int(c.lastrowid)


def dong_cau_hoi(ch_id: int, tra_loi: str, trang_thai: str = "XONG") -> None:
    if trang_thai not in ("XONG", "BO", "DANG", "MO"):
        raise ValueError("trang_thai cau hoi: MO/DANG/XONG/BO")
    with ket_noi() as cn:
        cn.execute("UPDATE cau_hoi SET trang_thai=?, tra_loi=?, cap_nhat=? WHERE id=?",
                   (trang_thai, tra_loi[:1500], bay_gio(), int(ch_id)))


# ------------------------------------------------------------------ VONG
def bat_dau_vong(tac_tu: str, mo_hinh: str = "") -> int:
    with ket_noi() as cn:
        c = cn.execute("INSERT INTO vong(bat_dau,tac_tu,mo_hinh) VALUES(?,?,?)",
                       (bay_gio(), tac_tu, mo_hinh))
        return int(c.lastrowid)


def ket_thuc_vong(vong_id: int, tom_tat: str = "", so_cong_cu: int = 0,
                  token_vao: int = 0, token_ra: int = 0, usd: float = 0.0,
                  trang_thai: str = "XONG") -> None:
    with ket_noi() as cn:
        cn.execute("UPDATE vong SET ket_thuc=?, tom_tat=?, so_cong_cu=?, token_vao=?, "
                   "token_ra=?, usd=?, trang_thai=? WHERE id=?",
                   (bay_gio(), tom_tat[:4000], int(so_cong_cu), int(token_vao),
                    int(token_ra), float(usd), trang_thai, int(vong_id)))


def usd_hom_nay() -> float:
    r = mot("SELECT COALESCE(SUM(usd),0) u FROM vong WHERE bat_dau LIKE ?",
            time.strftime("%Y-%m-%d") + "%")
    return float(r.get("u") or 0.0)


# --------------------------------------------------------------- TOM TAT
def tom_tat(so_dong: int = 12) -> dict:
    """HO SO NGHIEN CUU cho dau moi chu ky: gon, du de khong lap lai viec cu."""
    dem = {b: int(mot("SELECT COUNT(*) n FROM %s" % b).get("n") or 0)
           for b in ("gia_thuyet", "thi_nghiem", "hieu_biet", "cau_hoi", "vong")}
    tong_phep_thu = int(mot("SELECT COALESCE(SUM(so_phep_thu),0) n FROM thi_nghiem "
                            "WHERE doan='kham_pha'").get("n") or 0)
    theo_tt = {r["trang_thai"]: r["n"] for r in nhieu(
        "SELECT trang_thai, COUNT(*) n FROM gia_thuyet GROUP BY trang_thai")}
    gt_mo = nhieu("SELECT id, cau, ho, trang_thai, uu_tien, pham_vi, ket_luan FROM gia_thuyet "
                  "WHERE trang_thai IN ('MO','DANG_THU','TRIEN_VONG') "
                  "ORDER BY (trang_thai='TRIEN_VONG') DESC, uu_tien DESC, id DESC LIMIT ?",
                  so_dong)
    gt_xong = nhieu("SELECT id, cau, trang_thai, ket_luan FROM gia_thuyet "
                    "WHERE trang_thai IN ('XAC_NHAN','BAC_BO','TRUOT_NIEM_PHONG') "
                    "ORDER BY id DESC LIMIT ?", so_dong)
    hb = nhieu("SELECT id, cau, do_tin, bang_chung FROM hieu_biet WHERE trang_thai='HIEU_LUC' "
               "ORDER BY do_tin DESC, id DESC LIMIT ?", so_dong)
    ch = nhieu("SELECT id, cau, vi_sao, uu_tien, nguon FROM cau_hoi WHERE trang_thai IN ('MO','DANG') "
               "ORDER BY (nguon='nguoi') DESC, uu_tien DESC, id ASC LIMIT ?", so_dong)
    # Thi nghiem tot nhat theo TIEN duoi tran DD chu du an (tren kham_pha / xac_nhan)
    tot = []
    for r in nhieu("SELECT id, gt_id, loai, ma, khung, doan, tom_tat, ket_qua FROM thi_nghiem "
                   "WHERE loai IN ('thu_co_che','xac_nhan') AND trang_thai='DAT' "
                   "ORDER BY id DESC LIMIT 400"):
        try:
            kq = json.loads(r["ket_qua"] or "{}")
        except Exception:
            kq = {}
        tn_ = kq.get("tien") or {}
        cg = tn_.get("cagr_duoi_tran_pct")
        if cg is None:
            continue
        tot.append({"tn": r["id"], "gt": r["gt_id"], "loai": r["loai"], "ma": r["ma"],
                    "khung": r["khung"], "doan": r["doan"], "cagr_duoi_tran_pct": cg,
                    "don_bay": tn_.get("don_bay"), "dd_pct": tn_.get("dd_pct"),
                    "hon_moc_pct": tn_.get("hon_moc_pct"),
                    "so_lenh": (kq.get("lenh") or {}).get("so_lenh"),
                    "tom_tat": r["tom_tat"]})
    tot.sort(key=lambda z: -(z["cagr_duoi_tran_pct"] or -1e9))
    gan = nhieu("SELECT id, loai, ma, khung, doan, trang_thai, tom_tat FROM thi_nghiem "
                "ORDER BY id DESC LIMIT ?", so_dong)
    theo_ma = nhieu("SELECT ma, khung, COUNT(*) so_tn, COALESCE(SUM(so_phep_thu),0) phep_thu, "
                    "SUM(trang_thai='DAT') dat FROM thi_nghiem WHERE doan='kham_pha' AND ma!='' "
                    "GROUP BY ma, khung ORDER BY phep_thu DESC LIMIT 20")
    np_ = nhieu("SELECT id, luc, gt_id, ma, khung, trang_thai FROM niem_phong ORDER BY id DESC LIMIT ?",
                so_dong)
    vg = nhieu("SELECT id, bat_dau, tac_tu, mo_hinh, so_cong_cu, usd, tom_tat FROM vong "
               "ORDER BY id DESC LIMIT 3")
    return {"dem": dem, "tong_phep_thu_kham_pha": tong_phep_thu,
            "gia_thuyet_theo_trang_thai": theo_tt,
            "gia_thuyet_dang_mo": gt_mo, "gia_thuyet_da_ket": gt_xong,
            "hieu_biet": hb, "cau_hoi_mo": ch, "thi_nghiem_tot_nhat": tot[:so_dong],
            "thi_nghiem_gan_day": gan, "phep_thu_theo_ma": theo_ma,
            "niem_phong": np_, "vong_gan_day": vg, "usd_hom_nay": round(usd_hom_nay(), 3)}


def tom_tat_md(so_dong: int = 12) -> str:
    """Ban Markdown cua `tom_tat` - cho nguoi doc va cho dau loi nhac cua tac tu."""
    t = tom_tat(so_dong)
    d = t["dem"]
    L = ["# SO TAY NGHIEN CUU", "",
         "%d gia thuyet · %d thi nghiem (%d phep thu tren kham_pha) · %d hieu biet · "
         "%d cau hoi · %d vong · chi hom nay $%.2f"
         % (d["gia_thuyet"], d["thi_nghiem"], t["tong_phep_thu_kham_pha"], d["hieu_biet"],
            d["cau_hoi"], d["vong"], t["usd_hom_nay"]), ""]
    if t["cau_hoi_mo"]:
        L += ["## Cau hoi dang mo (nguoi dat xep truoc)"]
        L += ["- [#%d %s u%.2f] %s%s" % (c["id"], c["nguon"], c["uu_tien"] or 0, c["cau"],
                                          (" — " + c["vi_sao"]) if c.get("vi_sao") else "")
              for c in t["cau_hoi_mo"]]
        L.append("")
    if t["gia_thuyet_dang_mo"]:
        L += ["## Gia thuyet dang song"]
        L += ["- [gt %d %s] %s%s" % (g["id"], g["trang_thai"], g["cau"],
                                     (" — " + g["ket_luan"]) if g.get("ket_luan") else "")
              for g in t["gia_thuyet_dang_mo"]]
        L.append("")
    if t["thi_nghiem_tot_nhat"]:
        L += ["## Thi nghiem tot nhat (co lai, tien tot nhat voi maxDD < 80%)"]
        L += ["- tn %d gt %s %s %s/%s [%s]: %+.2f%%/nam @x%s DD %s%% (hon moc %s), %s lenh — %s"
              % (x["tn"], x["gt"], x["loai"], x["ma"], x["khung"], x["doan"],
                 x["cagr_duoi_tran_pct"], x.get("don_bay"), x.get("dd_pct"), x.get("hon_moc_pct"),
                 x["so_lenh"], x["tom_tat"] or "") for x in t["thi_nghiem_tot_nhat"]]
        L.append("")
    if t["hieu_biet"]:
        L += ["## Hieu biet da co bang chung"]
        L += ["- [hb %d tin %.2f] %s (tn %s)" % (h["id"], h["do_tin"] or 0, h["cau"], h["bang_chung"])
              for h in t["hieu_biet"]]
        L.append("")
    if t["gia_thuyet_da_ket"]:
        L += ["## Gia thuyet da ket (dung dao lai)"]
        L += ["- [gt %d %s] %s — %s" % (g["id"], g["trang_thai"], g["cau"], g.get("ket_luan") or "")
              for g in t["gia_thuyet_da_ket"]]
        L.append("")
    if t["phep_thu_theo_ma"]:
        L += ["## Phep thu da tieu theo (ma, khung) tren kham_pha"]
        L += ["- %s/%s: %d thi nghiem, %d phep thu, %d DAT" % (r["ma"], r["khung"], r["so_tn"],
                                                               r["phep_thu"], r["dat"] or 0)
              for r in t["phep_thu_theo_ma"]]
        L.append("")
    if t["niem_phong"]:
        L += ["## Da mo niem phong"]
        L += ["- [np %d] gt %s %s/%s -> %s" % (x["id"], x["gt_id"], x["ma"], x["khung"], x["trang_thai"])
              for x in t["niem_phong"]]
        L.append("")
    if t["thi_nghiem_gan_day"]:
        L += ["## Thi nghiem gan day"]
        L += ["- tn %d %s %s/%s [%s] %s — %s" % (x["id"], x["loai"], x["ma"], x["khung"], x["doan"],
                                                 x["trang_thai"], x["tom_tat"] or "")
              for x in t["thi_nghiem_gan_day"]]
        L.append("")
    if t["vong_gan_day"]:
        L += ["## Chu ky gan day"]
        L += ["- vong %d %s %s (%s, %s cong cu, $%.2f): %s"
              % (v["id"], v["bat_dau"], v["tac_tu"], v["mo_hinh"] or "-", v["so_cong_cu"],
                 v["usd"] or 0, (v["tom_tat"] or "")[:400]) for v in t["vong_gan_day"]]
    return "\n".join(L)


if __name__ == "__main__":
    print(tom_tat_md())
