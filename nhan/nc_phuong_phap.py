# -*- coding: utf-8 -*-
"""nc_phuong_phap.py - cong cu nc cho THE PHUONG PHAP (`nhan/the_phuong_phap.py`): luu_the, chuyen_bot, ke_hoach_do, quet_o, thu_chuyen.

Tat ca chi DICH + LAP KE HOACH: khong chay engine, khong tester, khong ghi nc.db, khong tieu phep thu. Ket qua do tien (DAT / AM) chi den
tu `nhan/cham_diem` + tester sau khi ke hoach duoc dong bang. `thu_chuyen` o day chi tra ke hoach (CHUA_CHAY), khong phai ket luan.
Thi truong ('nguon' / 'dich') la dict {ma, khung_phut, A, C, pip, pv, von} (A, C theo don vi GIA; xem `dich_tham_so.ThiTruong`).
"""
from __future__ import annotations

from nhan import dich_tham_so as DTS
from nhan import the_phuong_phap as TP

_TT = ("ma", "khung_phut", "A", "C", "pip", "pv", "von")


def _thi_truong(d, nhan: str) -> DTS.ThiTruong:
    if not isinstance(d, dict):
        raise ValueError("'%s' phai la dict thi truong" % nhan)
    thieu = [k for k in _TT if k not in d]
    if thieu:
        raise ValueError("'%s' thieu %s" % (nhan, thieu))
    tt = DTS.ThiTruong(ma=str(d["ma"]), khung_phut=float(d["khung_phut"]), A=float(d["A"]), C=float(d["C"]), pip=float(d["pip"]),
                       pv=float(d["pv"]), von=float(d["von"]), do_tin_chi_phi=str(d.get("do_tin_chi_phi", "KHAI")),
                       lot_toi_thieu=float(d.get("lot_toi_thieu", 0.01)), lot_buoc=float(d.get("lot_buoc", 0.01)))
    loi = DTS.kiem_thi_truong(tt, nhan)
    if loi:
        raise ValueError("; ".join(str(x) for x in loi[:3]))
    return tt


def _bao(f):
    def g(vong_id=None, **kw):
        try:
            return f(**kw)
        except (ValueError, FileNotFoundError, FileExistsError, KeyError) as e:
            return {"trang_thai": "CHUA_DO_DUOC", "loi": str(e)}
    return g


def _luu_the(the=None, ghi_de=False, **_):
    p = TP.ghi(the, ghi_de=bool(ghi_de))
    return {"trang_thai": "DAT", "tep": str(p.relative_to(TP.LAB)), "tom_tat": "da luu the '%s' (%s)" % (the["ma"], the["loai"])}


def _chuyen_bot(the_ma=None, gia_tri=None, nguon=None, dich=None, w=0.5, **_):
    the = TP.doc(the_ma)
    r = TP.thay_so(the, gia_tri or {}, _thi_truong(nguon, "nguon"), _thi_truong(dich, "dich"), float(w))
    r["trang_thai"] = "DAT" if r["gia_tri_moi"] and not r["khong_ap_duoc"] else ("CHUA_DO_DUOC" if r["khong_ap_duoc"] else "DAT")
    r["tom_tat"] = "%d o doi, %d giu, %d khong ap duoc" % (len(r["gia_tri_moi"]), len(r["giu"]), len(r["khong_ap_duoc"]))
    return r


def _ke_hoach_do(the_ma=None, gia_tri=None, nguon=None, dich_ds=None, w=0.5, **_):
    the = TP.doc(the_ma)
    src = _thi_truong(nguon, "nguon")
    if not isinstance(dich_ds, list) or not dich_ds:
        raise ValueError("dich_ds phai la danh sach thi truong dich")
    hang = []
    for d in dich_ds[:50]:
        r = TP.thay_so(the, gia_tri or {}, src, _thi_truong(d, "dich"), float(w))
        hang.append({"dich": d.get("ma"), "khung_phut": d.get("khung_phut"),
                     "do_duoc": not r["khong_ap_duoc"], "gia_tri_moi": r["gia_tri_moi"], "khong_ap_duoc": r["khong_ap_duoc"]})
    return {"trang_thai": "CHUA_CHAY", "the": the_ma, "ke_hoach": hang,
            "tom_tat": "%d / %d cho dich do duoc (khong chay gi; dong bang ke hoach truoc khi cham du lieu)" % (
                sum(h["do_duoc"] for h in hang), len(hang))}


def _quet_o(the_ma=None, o=None, **_):
    the = TP.doc(the_ma)
    ob = next((x for x in the["tham_so"] if x["ten"] == o), None)
    if ob is None:
        raise ValueError("o '%s' khong co trong the '%s'" % (o, the_ma))
    m = ob.get("mien")
    if not m:
        raise ValueError("o '%s' chua co mien [min,max,buoc] - dien mien truoc (luu_the)" % o)
    lo, hi, st = m
    luoi, x, n = [], lo, 0
    while x <= hi + 1e-12 and n < 500:
        luoi.append(round(x, 10))
        n += 1
        x = lo + n * st
    return {"trang_thai": "CHUA_CHAY", "o": o, "lop": ob["lop"], "luoi": luoi, "tom_tat": "%d diem luoi cho o '%s'" % (len(luoi), o)}


def _thu_chuyen(**kw):
    r = _ke_hoach_do(**kw)
    r["tom_tat"] = "KE HOACH thu chuyen (CHUA CHAY, can tester + chi phi do duoc): " + r["tom_tat"]
    return r


_NGUON = {"type": "object", "description": "thi truong {ma, khung_phut, A, C, pip, pv, von} (A, C don vi gia)"}
_MA = {"type": "string", "description": "ma the trong kho_phuong_phap/"}
_GT = {"type": "object", "description": "{ten_o: gia tri o thi truong nguon}"}

def _cmt_loc(khai_bao=None, tinh_cach=None, kho=False, **_):
    from nhan import cmt_prior as C
    if kho:
        import json
        from nhan import ngu_phap as N
        khai_bao = json.load(open(N.KHO_CO_CHE, encoding="utf-8"))
    if not isinstance(khai_bao, list) or not khai_bao:
        raise ValueError("can `khai_bao` (danh sach khai bao DSL) hoac kho=true")
    r = C.loc(khai_bao, tinh_cach)
    r["cum"] = r["cum"][:40]
    r["canh_bao"] = {"so_spec_co_canh_bao": len(r["canh_bao"])}
    return r

CONG_CU = [
    ("luu_the", "Luu (kiem + ghi) mot THE PHUONG PHAP vao kho_phuong_phap/. Khong an phep thu.",
     {"the": {"type": "object", "description": "the theo dang muc 7.2 CHUYEN_BOT_SANG_TAI_SAN_KHAC.md"},
      "ghi_de": {"type": "boolean"}}, ["the"], _bao(_luu_the)),
    ("chuyen_bot", "Thay so: doi gia tri cac O cua mot the tu thi truong nguon sang dich (khong chay engine).",
     {"the_ma": _MA, "gia_tri": _GT, "nguon": _NGUON, "dich": _NGUON, "w": {"type": "number", "description": "pha tron A/C 0..1"}},
     ["the_ma", "gia_tri", "nguon", "dich"], _bao(_chuyen_bot)),
    ("ke_hoach_do", "Lap ke hoach do: mot the x nhieu thi truong dich, cho nao do duoc (khong chay).",
     {"the_ma": _MA, "gia_tri": _GT, "nguon": _NGUON, "dich_ds": {"type": "array", "items": {"type": "object"}}, "w": {"type": "number"}},
     ["the_ma", "gia_tri", "nguon", "dich_ds"], _bao(_ke_hoach_do)),
    ("quet_o", "Rai luoi gia tri cua MOT o tham so trong mien cua the (chi liet ke luoi, khong chay).",
     {"the_ma": _MA, "o": {"type": "string"}}, ["the_ma", "o"], _bao(_quet_o)),
    ("thu_chuyen", "Ke hoach thu chuyen mot the sang cac thi truong dich (CHUA_CHAY; ket luan can tester + cham_diem).",
     {"the_ma": _MA, "gia_tri": _GT, "nguon": _NGUON, "dich_ds": {"type": "array", "items": {"type": "object"}}, "w": {"type": "number"}},
     ["the_ma", "gia_tri", "nguon", "dich_ds"], _bao(_thu_chuyen)),
    ("cmt_loc", "Gom khai bao DSL cung HO chi bao (kieu CMT) thanh cum: so phep thu HIEU DUNG + dai dien + thu tu theo che do (tinh_cach hoi_quy|quan_tinh). NHAN + THU TU, khong chan, khong chay engine.",
     {"khai_bao": {"type": "array", "items": {"type": "object"}}, "tinh_cach": {"type": "string"}, "kho": {"type": "boolean", "description": "true = dung config/co_che_dsl.json"}}, [], _bao(_cmt_loc)),
]
