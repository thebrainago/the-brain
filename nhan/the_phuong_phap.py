# -*- coding: utf-8 -*-
"""the_phuong_phap.py - THE PHUONG PHAP: mot co che / chien luoc / diem dac sac cua mot con bot, luu thanh khuon TAI DUNG.

Chu du an 05/10/2026: boc co che / chien luoc / diem dac sac cua tung bot, luu thanh phuong phap, thay so de ap cheo sang tai san
va khung khac (tai_lieu/CHUYEN_BOT_SANG_TAI_SAN_KHAC.md muc 7). Mot THE gom: khoi co che + CAC O THAM SO co kieu (lop cua
`dich_tham_so`) + mien + dieu kien dung + nguon + (tuy chon) bang chung.

  * Dinh nghia nam trong git: `kho_phuong_phap/<ma>.json` (module nay doc / ghi / kiem).
  * Hat giong: 52 khoi cua `khoi_co_che` (`gieo_tu_khoi`) va `cong_thuc` do duoc cua `ho_so_set` (`the_tu_cong_thuc`).
  * Bang chung KHONG nam trong the (bang `the_bang_chung` o nc.db, xuat bang `b nc xuat`); the chi giu `bang_chung_ghi_chu` do may sinh.
  * "Thay so vao" (`thay_so`) = doi tung o sang don vi cua thi truong dich bang dung cac phep dich cua `dich_tham_so`.
    KHONG chay engine, KHONG ghi DB, KHONG quyet dinh gi ve tien: the khong phai phat hien, chi la khuon de thu.

    python -m nhan.the_phuong_phap gieo       # ghi kho_phuong_phap/ tu 52 khoi (khong de the da co)
    python -m nhan.the_phuong_phap kiem       # kiem kho (ma loi = 1)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from nhan import dich_tham_so as DTS
from nhan import khoi_co_che as KC

PHIEN_BAN = "1"
LAB = Path(__file__).resolve().parent.parent
KHO = LAB / "kho_phuong_phap"
LOAI = ("VAO", "TANG", "LOT", "THOAT", "BAO_VE", "LOC", "CHI_BAO", "QUAN_LI")
ENGINE_TT = tuple(KC.ENGINE) + ("chua_ro",)
_RX_MA = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_KHOA = ("ma", "loai", "ten", "mo_ta", "tham_so", "can", "xung_dot", "tuong_tac_biet", "vet", "engine", "nguon", "dieu_kien_dung")


# ------------------------------------------------------------------------------------------------------------------ kiem
def kiem_the(the: dict) -> list:
    """Danh sach loi cua mot the (rong = on)."""
    loi = []
    if not isinstance(the, dict):
        return ["the phai la dict"]
    for k in _KHOA:
        if k not in the:
            loi.append("thieu khoa '%s'" % k)
    if loi:
        return loi
    if not isinstance(the["ma"], str) or not _RX_MA.match(the["ma"]):
        loi.append("ma '%s' khong hop le (snake_case ASCII 3-64 ky tu)" % (the["ma"],))
    if the["loai"] not in LOAI:
        loi.append("loai '%s' khong thuoc %s" % (the["loai"], LOAI))
    if not str(the["ten"]).strip() or not str(the["mo_ta"]).strip():
        loi.append("ten / mo_ta rong")
    ten_o = set()
    for i, o in enumerate(the["tham_so"]):
        if not isinstance(o, dict) or not o.get("ten"):
            loi.append("tham_so[%d] thieu ten" % i)
            continue
        if o["ten"] in ten_o:
            loi.append("tham_so trung ten '%s'" % o["ten"])
        ten_o.add(o["ten"])
        lop = o.get("lop")
        if lop not in DTS.LOP + (DTS.CHUA_PHAN_LOP,):
            loi.append("tham_so '%s': lop '%s' la" % (o["ten"], lop))
        m = o.get("mien")
        if m is not None:
            if not (isinstance(m, (list, tuple)) and len(m) == 3 and all(isinstance(x, (int, float)) for x in m)
                    and m[0] <= m[1] and m[2] > 0):
                loi.append("tham_so '%s': mien phai la [min, max, buoc] voi min <= max, buoc > 0" % o["ten"])
    e = the["engine"]
    if not isinstance(e, dict) or e.get("trang_thai") not in ENGINE_TT:
        loi.append("engine.trang_thai khong thuoc %s" % (ENGINE_TT,))
    for k in ("can", "xung_dot", "tuong_tac_biet", "vet", "nguon", "dieu_kien_dung"):
        if not isinstance(the[k], list):
            loi.append("'%s' phai la danh sach" % k)
    return loi


def _duong(ma: str) -> Path:
    if not _RX_MA.match(ma or ""):
        raise ValueError("ma the khong hop le: %r" % (ma,))
    return KHO / (ma + ".json")


def doc(ma: str) -> dict:
    return json.loads(_duong(ma).read_text(encoding="utf-8"))


def ghi(the: dict, ghi_de: bool = False) -> Path:
    loi = kiem_the(the)
    if loi:
        raise ValueError("the hong: " + "; ".join(loi[:5]))
    p = _duong(the["ma"])
    if p.exists() and not ghi_de:
        raise FileExistsError("the '%s' da co (ghi_de=True de thay)" % the["ma"])
    KHO.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(the, ensure_ascii=True, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    return p


def tat_ca() -> list:
    if not KHO.is_dir():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(KHO.glob("*.json"))]


def kiem_kho() -> list:
    loi = []
    for p in sorted(KHO.glob("*.json")) if KHO.is_dir() else []:
        try:
            the = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            loi.append("%s: khong doc duoc (%s)" % (p.name, e))
            continue
        loi += ["%s: %s" % (p.name, x) for x in kiem_the(the)]
        if isinstance(the, dict) and the.get("ma") and p.stem != the["ma"]:
            loi.append("%s: ma '%s' khac ten tep" % (p.name, the["ma"]))
    return loi


# ------------------------------------------------------------------------------------------------------------------ hat giong
def _o_tu_ten(ten: str) -> dict:
    ten = str(ten).strip()
    lop, dv = DTS.lop_khoa_set(ten)
    return {"ten": ten, "lop": lop, "don_vi": dv, "mien": None, "ten_trong_set": None, "ten_trong_engine": None}


def _o(ten, lop, don_vi="", mien=None):
    return {"ten": ten, "lop": lop, "don_vi": don_vi, "mien": mien, "ten_trong_set": None, "ten_trong_engine": None}


#: O CO KIEU viet tay cho cac khoi chinh (cac khoi con lai giu o suy tu TEN, phan nhieu CHUA_PHAN_LOP - dung thua nhan la da co kieu).
#: Mien la [min, max, buoc] de rai luoi; so lieu chi la khoang hop ly de thu, khong phai gia tri cua bot nao.
O_CHUAN = {
    "luoi_gian_cach_deu": [_o("buoc", DTS.KC_BUOC, "pip", [50, 400, 25]), _o("tran_tang", DTS.SO_DEM, "lenh", [4, 20, 2])],
    "luoi_buoc_gian_dan": [_o("buoc", DTS.KC_BUOC, "pip", [50, 400, 25]), _o("he_so_buoc", DTS.HE_SO, "", [1.0, 2.0, 0.25]),
                           _o("tran_tang", DTS.SO_DEM, "lenh", [4, 20, 2])],
    "luoi_buoc_theo_bac": [_o("buoc_bac1", DTS.KC_BUOC, "pip", [50, 400, 25]), _o("buoc_bac_sau", DTS.KC_BUOC, "pip", [50, 800, 50]),
                           _o("so_lenh_moi_bac", DTS.SO_DEM, "lenh", [1, 6, 1])],
    "lot_phang": [_o("lot", DTS.LOT, "lot", [0.01, 0.5, 0.01])],
    "lot_nhan": [_o("lot", DTS.LOT, "lot", [0.01, 0.5, 0.01]), _o("he_so_lot", DTS.HE_SO, "", [1.1, 2.0, 0.1])],
    "lot_cong": [_o("lot", DTS.LOT, "lot", [0.01, 0.5, 0.01]), _o("cong_them", DTS.LOT, "lot", [0.01, 0.2, 0.01])],
    "lot_nhan_theo_bac": [_o("lot", DTS.LOT, "lot", [0.01, 0.5, 0.01]), _o("he_so_lot", DTS.HE_SO, "", [1.1, 2.0, 0.1]),
                          _o("bac_bat_dau_nhan", DTS.SO_DEM, "lenh", [1, 8, 1])],
    "tp_chuoi_tien": [_o("tp_tien", DTS.TIEN, "tien", [5, 200, 5])],
    "tp_chuoi_tu_gia_tb": [_o("tp_tu_gia_tb", DTS.KC_TP, "pip", [10, 200, 10])],
    "tp_tung_lenh": [_o("tp", DTS.KC_TP, "pip", [20, 300, 10])],
    "sl_cung": [_o("sl", DTS.KC_SL, "pip", [100, 2000, 100])],
    "trailing_stop_chuoi": [_o("kich_hoat", DTS.KC_TP, "pip", [10, 100, 10]), _o("buoc_nhich", DTS.KC_TP, "pip", [1, 20, 1])],
    "lenh_doi_ung_sau_n_lenh": [_o("n_kich_hoat", DTS.SO_DEM, "lenh", [3, 12, 1]), _o("ti_le_lot_doi", DTS.HE_SO, "", [0.5, 2.0, 0.25]),
                                _o("tp_doi", DTS.KC_TP, "pip", [10, 100, 10])],
    "cat_lo_theo_tien": [_o("tien_cat_lo", DTS.TIEN, "tien", [50, 2000, 50])],
    "tran_so_lenh": [_o("tran_lenh", DTS.SO_DEM, "lenh", [5, 40, 1])],
    "loc_spread": [_o("spread_toi_da", DTS.PHI, "point", [10, 100, 5])],
    "vao_lai_sau_cho_lui": [_o("cho_lui", DTS.THOI_GIAN, "phut", [0, 120, 5])],
}


def the_tu_khoi(k) -> dict:
    """Mot `khoi_co_che.Khoi` -> the. Cac o co ten la CHUOI MO TA (khong phai ten khoa) van giu nguyen, lop theo ten neu khop."""
    return {"ma": k.ma, "loai": k.nhom if k.nhom in LOAI else "QUAN_LI", "ten": k.ten, "mo_ta": k.mo_ta,
            "tham_so": [dict(o) for o in O_CHUAN[k.ma]] if k.ma in O_CHUAN else [_o_tu_ten(t) for t in k.tham_so], "can": [], "xung_dot": [], "tuong_tac_biet": [],
            "vet": [k.dau_van_tay], "engine": {"trang_thai": k.engine if k.engine in KC.ENGINE else "chua_ro",
                                              "co": list(k.truong_engine), "ghi_chu": k.engine_ghi_chu,
                                              "nhan_c": False, "ea_mq5": False},
            "nguon": [{"loai": "khoi_co_che", "ma": k.ma}], "dieu_kien_dung": ["phan_giai", "lot_toi_thieu"],
            "ap_cheo": k.ap_cheo, "rui_ro": k.rui_ro, "bang_chung_ghi_chu": "chua co (the moi gieo, chua do)"}


def gieo_tu_khoi(ghi_de: bool = False) -> dict:
    """Ghi `kho_phuong_phap/<ma>.json` cho moi khoi chua co the. Tra {da_ghi, bo_qua}."""
    da, bo = [], []
    for k in KC.KHOI_DS:
        try:
            ghi(the_tu_khoi(k), ghi_de=ghi_de)
            da.append(k.ma)
        except FileExistsError:
            bo.append(k.ma)
    return {"da_ghi": da, "bo_qua": bo}


def the_tu_cong_thuc(ct: dict, bot: str = "") -> dict:
    """Mot muc `cong_thuc` cua `ho_so_set` ({khoi, ten, nhom, do_tin, ly_do, cong_thuc?...}) -> cap nhat the cua khoi do bang
    CONG THUC DO DUOC (chuoi) va do tin; tra the moi (chua ghi). Khong co khoi trong kho -> ValueError."""
    ma = ct.get("khoi")
    the = doc(ma)
    the = json.loads(json.dumps(the))
    the.setdefault("cong_thuc_do_duoc", [])
    muc = {"bot": bot, "do_tin": ct.get("do_tin"), "ly_do": str(ct.get("ly_do", ""))[:300],
           "cong_thuc": ct.get("cong_thuc")}
    the["cong_thuc_do_duoc"].append(muc)
    the["nguon"].append({"loai": "ho_so_set", "bot": bot, "khoi": ma})
    return the


# ------------------------------------------------------------------------------------------------------------------ thay so
def he_so_tu_thi_truong(src: DTS.ThiTruong, dst: DTS.ThiTruong, w: float = 0.5, lot: str = "giu") -> DTS.HeSoDich:
    """He so cho `dich_gia_tri` chi tu hai thi truong (khong can luoi). Khong co I4 / I6 (can luoi that): lot GIU nguyen, tam giu."""
    k = DTS.he_so_ty_le(src, dst, w)
    return DTS.HeSoDich(buoc=k, tp=k, sl=k, tam=1.0, lot=1.0, tien_tp=k * dst.pv / src.pv, tien_tam=k * dst.pv / src.pv,
                        phi=dst.C / src.C, pip=src.pip / dst.pip, point=src.point / dst.point,
                        nen_theo_phut=src.khung_phut / dst.khung_phut, phut_theo_nen=dst.khung_phut / src.khung_phut)


def thay_so(the: dict, gia_tri: dict, src: DTS.ThiTruong, dst: DTS.ThiTruong, w: float = 0.5, thoi_gian: str = "dong_ho") -> dict:
    """Doi gia tri tung O cua the (`gia_tri` = {ten_o: so}) sang don vi thi truong dich. Tra {gia_tri_moi, giu, khong_ap_duoc, canh_bao}.
    Duoi 2 A (phan giai) o khoang cach -> khong ap duoc (CHUA_DO_DUOC, khong phai AM). O khong thuoc the -> loi."""
    biet = {o["ten"]: o for o in the["tham_so"]}
    la = [t for t in gia_tri if t not in biet]
    if la:
        raise ValueError("o khong co trong the '%s': %s" % (the["ma"], la))
    hs = he_so_tu_thi_truong(src, dst, w)
    moi, giu, khong, cb = {}, [], [], []
    for ten, v in gia_tri.items():
        o = biet[ten]
        if o["lop"] in (DTS.KC_BUOC, DTS.KC_TP, DTS.KC_SL):
            d_gia = abs(float(v)) * src.pip
            d_dich = d_gia * DTS.he_so_ty_le(src, dst, w)
            d_dich = max(d_dich, DTS.SAN_CHI_PHI * dst.C)
            if d_dich < DTS.NGUONG_PHAN_GIAI * dst.A:
                khong.append({"o": ten, "ly_do": "khoang cach dich < %s A: bar khong phan giai duoc (CHUA_DO_DUOC)" % DTS.NGUONG_PHAN_GIAI})
                continue
        r, quy, ghi_chu = DTS.dich_gia_tri(o["lop"], v, o.get("don_vi") or "", hs, src, dst, thoi_gian, ten)
        if r is None:
            giu.append(ten)
        else:
            moi[ten] = {"tu": v, "den": r, "quy_tac": quy, "ghi_chu": ghi_chu}
    if any(biet[t]["lop"] == DTS.LOT for t in gia_tri):
        cb.append("lot GIU nguyen o buoc nay (I4 can luoi that: dung dich_tham_so.dich_luoi)")
    return {"gia_tri_moi": moi, "giu": giu, "khong_ap_duoc": khong, "canh_bao": cb}


def main(argv: list) -> int:
    if len(argv) < 2 or argv[1] not in ("gieo", "kiem"):
        print(__doc__)
        return 2
    if argv[1] == "gieo":
        r = gieo_tu_khoi()
        print("da ghi %d the, bo qua %d (da co)" % (len(r["da_ghi"]), len(r["bo_qua"])))
    loi = kiem_kho()
    print("kho: %d the, %d loi" % (len(tat_ca()), len(loi)))
    for x in loi[:20]:
        print("  - " + x)
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
