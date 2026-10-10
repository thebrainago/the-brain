# -*- coding: utf-8 -*-
"""Test vong_lap: vong khep kin TIM -> BOC -> KIEM -> GIU -> AP DUNG chi tu `viec/` (git). Dung cay thu muc gia trong thu muc tam.

Cac test duoi day co CHU DICH bat nhung loi ma mot ban viet cau tha se mac (khong chi kiem duong dung):
  - mot don chet / khong do duoc bi dem thanh RUOT hoac QUA;
  - don engine moi chet xoa mat ket luan cua engine cu;
  - mot o chua tung kiem bi coi la da kiem (hoac ngay ca ra don hai lan cho mot o);
  - vong lap cham vao doan NIEM PHONG (khong bao gio duoc phep);
  - co che duoc GIU khi chi thang o 1-2 thi truong;
  - ra don chay lai lan hai lai de them don.
"""
import json
import tempfile
from pathlib import Path

import pytest

from nhan import vong_lap as V

PY = "{py}"


# ------------------------------------------------------------------------------------------- dung cay gia

def _goc():
    d = Path(tempfile.mkdtemp(prefix="vl_test_"))
    for s in ("cho", "xong", "may", "dang"):
        (d / "viec" / s).mkdir(parents=True)
    (d / "so_cai").mkdir()
    return d


def _ghi(p: Path, d: dict):
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def _lenh(cong_cu, arg):
    return [PY, "b.py", "nc", "cc", cong_cu, json.dumps(arg, sort_keys=True)]


def _xong(goc, ma, lenh, dong_cuoi, trang_thai="DAT", ma_thoat=0, giay=10.0, luc="2026-10-08T10:00:00"):
    _ghi(goc / "viec" / "xong" / ("%s.json" % ma),
         {"ma": ma, "trang_thai": trang_thai, "ly_do": "chay xong, ma thoat %s" % ma_thoat, "luc": luc,
          "bang_chung": {"ma_thoat": ma_thoat, "giay": giay, "lenh": lenh, "dong_cuoi": dong_cuoi}})


def _duoi_quet(lop, lai, tong, ts):
    d = {"tham_so_day_du": ts, "trang_thai": "DAT",
         "ly_do": "%s: %d/%d o co lai, tot nhat +20.7%%/nam o tran DD 80%%" % (lop, lai, tong), "tn_id": 7}
    return json.dumps(d, indent=1).splitlines()[-25:]


def _tham_so(che_do="mua", buoc=30, tp=10, tran_tang=12, kieu="phang", cho_lui=0):
    ts = {"che_do": che_do, "lot": 0.01, "kieu_lot": kieu, "buoc": buoc, "he_so_buoc": 1.0, "tp": tp, "tran_tang": tran_tang}
    if cho_lui:
        ts["cho_lui"] = cho_lui
    return ts


def _quet(goc, ma_don, ma, khung="M15", lop="CAO_NGUYEN", ts=None, lai=89, tong=120):
    ts = ts or _tham_so()
    arg = {"ma": ma, "khung": khung, "luoi": {"buoc": [15, 20, 25, 30], "tp": [8, 10, 15], "tran_tang": [7, 9, 12]},
           "co_dinh": {"che_do": ts["che_do"], "lot": 0.01, "kieu_lot": ts["kieu_lot"]}, "von": 10000, "toi_da_o": 120}
    _xong(goc, ma_don, _lenh("quet_luoi", arg), _duoi_quet(lop, lai, tong, ts), giay=900.0)
    return V.id_ung_vien(ma, khung, ts)


def _nhip(goc, ten="nha", kha_nang=("windows", "data", "mt5")):
    _ghi(goc / "viec" / "may" / ("%s.json" % ten), {"may": ten, "kha_nang": list(kha_nang), "luc": "2026-10-09T10:00:00"})


def _doan(goc, cap):
    _ghi(goc / "so_cai" / "doan.json", {"%s|%s" % (m, k): {"t_xac_nhan": "2025-01-01T00:00:00", "t_niem_phong": "2026-07-01T00:00:00"}
                                       for m, k in cap})


def _tra(goc, ma_don, loi_suat=8.0, maxdd=-30.0, calmar=0.3, engine=None, kieu="tom_tat", chet=False, so_lenh=120, trang_thai=None):
    """Gia lap may nha tra ket qua cho don `ma_don` (da ra o viec/cho)."""
    d = json.loads((goc / "viec" / "cho" / ("%s.json" % ma_don)).read_text(encoding="utf-8"))
    if chet:
        _xong(goc, ma_don, d["lenh"], ["Traceback", "FileNotFoundError: khong co du lieu"], trang_thai="CHUA_DO_DUOC", ma_thoat=1, giay=0.5)
        return
    cs = {"loi_suat_nam_pct": loi_suat, "maxdd_pct": maxdd, "calmar": calmar, "lenh_nam": so_lenh / 1.5, "chay": False}
    if kieu == "tom_tat":
        tt = trang_thai or ("DAT" if loi_suat > 0 else "AM")
        tomtat = {"trang_thai": tt, "ly_do": "x", "tien": {"loi_suat_nam_pct": loi_suat, "maxdd_pct": maxdd, "loi_suat_o_tran_pct": loi_suat * 2},
                  "chi_so_luoi": cs, "lenh": {"so_lenh": so_lenh}, "engine": {"phien_ban": engine or 4}, "tn_id": 99}
        tail = ["noi dung khac", "TOM_TAT " + json.dumps(tomtat)]
    else:
        tail = json.dumps({"chi_so_luoi": cs, "engine": {"phien_ban": engine or 3}}, indent=1).splitlines()
    _xong(goc, ma_don, d["lenh"], tail, luc="2026-10-09T12:00:00", giay=4.0)


# ------------------------------------------------------------------------------------------- doc lenh

def test_tach_lenh_va_chang_cua():
    cc, arg = V.tach_lenh(_lenh("quet_luoi", {"ma": "AUDCAD", "khung": "M15"}))
    assert cc == "quet_luoi" and arg["ma"] == "AUDCAD"
    assert V.tach_lenh([PY, "b.py", "hepha", "qt"])[0] == "hepha qt"
    assert V.tach_lenh([PY, "-m", "nhan.vong_lap"])[0] == "-m nhan.vong_lap"
    assert V.tach_lenh(None) == ("?", {}) and V.tach_lenh("chuoi khong phai list") == ("?", {})
    # chang theo cong cu
    assert V.chang_cua("quet_luoi", {}, "x") == ("KIEM", "kham")
    assert V.chang_cua("thu_luoi", {"doan": "kham_pha"}, "x") == ("KIEM", "kham")
    assert V.chang_cua("thu_luoi", {"doan": "xac_nhan"}, "x") == ("KIEM", "xac")
    assert V.chang_cua("yeu_cau_seeker", {}, "x")[0] == "TIM" and V.chang_cua("dien-dan quet", {}, "x")[0] == "TIM"
    assert V.chang_cua("ho_so_tai_san", {}, "x")[0] == "BOC"
    assert V.chang_cua("ghi_hieu_biet", {}, "x")[0] == "GIU"
    assert V.chang_cua("hieu_chuan_luoi", {}, "x")[0] == "HA_TANG"          # cong cu la -> ha tang, khong lam sai vong
    # ten don co tien to cua module uu tien hon cong cu
    assert V.chang_cua("quet_luoi", {}, V.TT_CHUYEN + "AUDCHF-M15-ab12cd") == ("AP_DUNG", "chuyen")
    assert V.chang_cua("thu_luoi", {}, V.TT_XAC4 + "abc") == ("KIEM", "xac")


# ------------------------------------------------------------------------------------- ung vien cao nguyen

def test_doc_quet_duoi_cu_va_tom_tat_va_thieu_tham_so():
    goc = _goc()
    ts = _tham_so()
    _quet(goc, "q1", "AUDCAD")
    d = V.doc_xong(goc)[0]
    u = V.doc_quet(d)
    assert u["lop"] == "CAO_NGUYEN" and (u["o_co_lai"], u["o_tong"]) == (89, 120) and u["ma"] == "AUDCAD"
    assert u["tham_so"]["buoc"] == 30 and u["co_che"] == "mua|phang|-" and set(u["luoi"]) == {"buoc", "tp", "tran_tang"}
    # dang moi: TOM_TAT thang
    d2 = json.loads(json.dumps(d))
    d2["bang_chung"]["dong_cuoi"] = ["rac", "TOM_TAT " + json.dumps({"tham_so_day_du": ts, "ly_do": "HON_HOP: 30/120 o co lai, tot nhat +5.0%/nam o tran DD 80%"})]
    u2 = V.doc_quet(d2)
    assert u2["lop"] == "HON_HOP" and (u2["o_co_lai"], u2["o_tong"]) == (30, 120) and u2["id"] == u["id"]
    # duoi bi cat mat tham_so_day_du -> khong ung vien (khong doan tham so)
    d3 = json.loads(json.dumps(d))
    d3["bang_chung"]["dong_cuoi"] = ['"ly_do": "CAO_NGUYEN: 89/120 o co lai, tot nhat +20.7%/nam o tran DD 80%",', '"tn_id": 7']
    assert V.doc_quet(d3) is None
    # khong phai quet_luoi
    d4 = json.loads(json.dumps(d))
    d4["bang_chung"]["lenh"] = _lenh("thu_luoi", {"ma": "AUDCAD", "khung": "M15"})
    assert V.doc_quet(d4) is None


def test_id_khong_phan_biet_10_va_10_0():
    a = V.id_ung_vien("audcad", "m15", {"buoc": 10, "tp": 5.0})
    b = V.id_ung_vien("AUDCAD", "M15", {"tp": 5, "buoc": 10.0})
    assert a == b
    assert a != V.id_ung_vien("AUDCAD", "M15", {"buoc": 11, "tp": 5})
    assert a != V.id_ung_vien("AUDCAD", "M30", {"buoc": 10, "tp": 5})


def test_gom_ung_vien_gop_trung_va_giu_lop_manh_nhat():
    goc = _goc()
    _quet(goc, "q1", "AUDCAD", lop="HON_HOP", lai=30)
    _quet(goc, "q2", "AUDCAD", lop="CAO_NGUYEN", lai=100)       # cung o, quet lai o luot khac, lop manh hon
    _quet(goc, "q3", "AUDCHF")
    uv = V.gom_ung_vien(V.doc_xong(goc))
    assert len(uv) == 2
    a = [u for u in uv if u["ma"] == "AUDCAD"][0]
    assert a["n_quet"] == 2 and a["lop"] == "CAO_NGUYEN" and a["o_co_lai"] == 100 and sorted(a["nguon"]) == ["q1", "q2"]


# ------------------------------------------------------------------------------------- ket qua xac nhan

def _kq_tu(goc, ten, **kw):
    ma = V.id_ung_vien("AUDCAD", "M15", _tham_so())
    _quet(goc, "q", "AUDCAD")
    u = V.gom_ung_vien(V.doc_xong(goc))[0]
    p = V.ra_don_xac_nhan(u, goc)
    _tra(goc, p.stem, **kw)
    return V.doc_xac_nhan(json.loads((goc / "viec" / "xong" / p.name).read_text(encoding="utf-8")))


def test_doc_xac_nhan_tom_tat_dat_va_am():
    r = _kq_tu(_goc(), "a", loi_suat=8.0, calmar=0.3, engine=4)
    assert r["ket_luan"] == "QUA" and r["phien_ban_engine"] == 4 and r["tn_id"] == 99
    assert r["ky_vong_o_tran_pct"] == 16.0                      # uu tien so do that (loi_suat_o_tran_pct), khong phai calmar x 80
    r = _kq_tu(_goc(), "b", loi_suat=-3.0, calmar=-0.1, engine=4)
    assert r["ket_luan"] == "RUOT" and r["ky_vong_o_tran_pct"] is None


def test_doc_xac_nhan_duoi_cu_chi_so_luoi():
    r = _kq_tu(_goc(), "c", loi_suat=6.2, calmar=0.16, kieu="cu")
    assert r["ket_luan"] == "QUA" and r["phien_ban_engine"] == 3 and r["nguon_so"] == "chi_so_luoi"
    assert r["ky_vong_o_tran_pct"] == round(0.16 * V.TRAN_DD, 1)
    assert _kq_tu(_goc(), "d", loi_suat=-1.3, calmar=-0.03, kieu="cu")["ket_luan"] == "RUOT"
    # it lenh -> chua du de ket luan, KHONG phai QUA
    assert _kq_tu(_goc(), "e", loi_suat=9.0, calmar=0.3, kieu="cu", so_lenh=5)["ket_luan"] == "KHONG_DO_DUOC"


def test_don_chet_khong_thanh_qua_hay_ruot():
    r = _kq_tu(_goc(), "f", chet=True)
    assert r["ket_luan"] == "KHONG_DO_DUOC" and "ma thoat 1" in r["ly_do"]
    # khong tim thay so lieu trong duoi -> khong doan
    goc = _goc()
    _quet(goc, "q", "AUDCAD")
    u = V.gom_ung_vien(V.doc_xong(goc))[0]
    p = V.ra_don_xac_nhan(u, goc)
    _xong(goc, p.stem, json.loads(p.read_text(encoding="utf-8"))["lenh"], ["khong co gi huu ich"])
    kq = V.doc_xac_nhan(json.loads((goc / "viec" / "xong" / p.name).read_text(encoding="utf-8")))
    assert kq["ket_luan"] == "KHONG_DO_DUOC"


def test_moi_nhat_uu_tien_ket_luan_roi_engine():
    cu = {"ket_luan": "QUA", "phien_ban_engine": 3, "luc": "2026-10-09T10:00:00"}
    moi_chet = {"ket_luan": "KHONG_DO_DUOC", "phien_ban_engine": 3, "luc": "2026-10-10T10:00:00"}
    assert V.moi_nhat([cu, moi_chet]) is cu                                    # don chet khong xoa ket luan
    moi = {"ket_luan": "RUOT", "phien_ban_engine": 4, "luc": "2026-10-09T09:00:00"}
    assert V.moi_nhat([cu, moi]) is moi                                        # engine moi thay engine cu
    assert V.moi_nhat([]) is None and V.moi_nhat(None) is None


def test_xac_nhan_da_co_nhan_ra_don_tay_va_don_dang_cho():
    goc = _goc()
    _quet(goc, "q", "AUDCAD")
    u = V.gom_ung_vien(V.doc_xong(goc))[0]
    # don TAY (ten khong theo tien to) cung o -> van nhan ra theo id
    arg = {"ma": "AUDCAD", "khung": "M15", "tham_so": u["tham_so"], "doan": "xac_nhan", "von": 10000}
    _ghi(goc / "viec" / "cho" / "tay-1.json", {"ma": "tay-1", "lan": "CPU", "lenh": _lenh("thu_luoi", arg), "can": ["engine4"]})
    da, dc = V.xac_nhan_da_co(V.doc_xong(goc), V.doc_cho(goc), goc)
    assert u["id"] in dc and dc[u["id"]]["ma_don"] == "tay-1" and dc[u["id"]]["can"] == ["engine4"] and not da
    # don thu_luoi KHAM_PHA khong tinh la kiem ngoai mau
    arg2 = dict(arg, doan="kham_pha")
    _xong(goc, "kp", _lenh("thu_luoi", arg2), ["TOM_TAT " + json.dumps({"trang_thai": "DAT", "tien": {"loi_suat_nam_pct": 3}})])
    da, dc = V.xac_nhan_da_co(V.doc_xong(goc), V.doc_cho(goc), goc)
    assert not da


# ------------------------------------------------------------------------------ doi chung va chon dot

def test_ngau_nhien_xac_dinh_nam_tren_luoi_khac_cha():
    goc = _goc()
    _quet(goc, "q", "AUDCAD")
    u = V.gom_ung_vien(V.doc_xong(goc))[0]
    g1, g2 = V.sinh_ngau_nhien(u), V.sinh_ngau_nhien(u)
    assert g1 == g2 and g1["id"] != u["id"] and g1["lop"] == "NGAU_NHIEN" and g1["cha"] == u["id"]
    for k in ("buoc", "tp", "tran_tang"):
        assert g1["tham_so"][k] in u["luoi"][k]
    assert g1["tham_so"]["che_do"] == "mua" and g1["tham_so"]["kieu_lot"] == "phang"      # tham so co dinh giu nguyen
    u2 = dict(u, luoi={})
    assert V.sinh_ngau_nhien(u2) is None


def _nhieu_ung_vien(goc, thi_truong=("AUDCAD", "AUDCHF", "EURCAD", "GBPAUD"), moi=6):
    n = 0
    for m in thi_truong:
        for i in range(moi):
            _quet(goc, "q%d" % n, m, ts=_tham_so(buoc=15 + 5 * i, tp=8 + i))
            n += 1
    for i in range(4):                                          # luot quet khong phai cao nguyen -> nhom doi chung
        _quet(goc, "d%d" % i, "USDJPY", lop="HON_HOP", lai=20, ts=_tham_so(buoc=50 + i))
    return V.gom_ung_vien(V.doc_xong(goc))


def test_chon_dot_khong_trung_khong_vuot_va_co_doi_chung():
    goc = _goc()
    uv = _nhieu_ung_vien(goc)
    ra = V.chon_dot(uv, set(), 20)
    ids = [x["id"] for x in ra]
    assert len(ids) == len(set(ids)) and len(ra) <= 20
    nhom = {g: sum(1 for x in ra if V.nhom_cua(x) == g) for g in ("cao", "doi", "ngau")}
    assert nhom["cao"] > 0 and nhom["doi"] > 0 and nhom["ngau"] > 0, nhom
    # khong bao gio chon lai o da co don / da co ket qua
    da_co = set(ids[:7])
    ra2 = V.chon_dot(uv, da_co, 20)
    assert not (da_co & {x["id"] for x in ra2})
    # xac dinh: chay lai ra dung dot do
    assert [x["id"] for x in V.chon_dot(uv, set(), 20)] == ids
    # xen ke thi truong: 4 o dau tien cua nhom cao khong dung het vao mot thi truong
    cao = [x for x in ra if V.nhom_cua(x) == "cao"]
    assert len({x["ma"] for x in cao[:4]}) >= 3


def test_ra_don_xac_nhan_hop_le_chi_doan_xac_nhan_va_khong_niem_phong():
    goc = _goc()
    uv = _nhieu_ung_vien(goc, thi_truong=("AUDCAD",), moi=3)
    u = [x for x in uv if x["lop"] == "CAO_NGUYEN"][0]
    p = V.ra_don_xac_nhan(u, goc)
    d = json.loads(p.read_text(encoding="utf-8"))
    assert p.stem == V.TT_XAC + u["id"] and d["lan"] == "CPU" and d["cong"] == {"kieu": "chay_duoc"} and not d.get("can")
    arg = json.loads(d["lenh"][-1])
    assert arg["doan"] == "xac_nhan" and arg["tham_so"] == u["tham_so"] and "niem_phong" not in json.dumps(d["lenh"])
    d4 = json.loads(V.ra_don_xac_nhan(u, goc, engine4=True).read_text(encoding="utf-8"))
    assert d4["ma"] == V.TT_XAC4 + u["id"] and d4["can"] == ["engine4"]


# ------------------------------------------------------------------------------------ co che & GIU

def _ung_vien_gia(i, ma, co_che="mua|phang|-", lop="CAO_NGUYEN"):
    che_do, kieu, lui = co_che.split("|")
    ts = {"che_do": che_do, "kieu_lot": kieu, "buoc": 10 + i, "tp": 5, "tran_tang": 8}
    if lui == "lui":
        ts["cho_lui"] = 2
    return {"id": "u%03d" % i, "ma": ma, "khung": "M15", "tham_so": ts, "von": 10000, "lop": lop, "o_co_lai": 50, "o_tong": 100, "ty_le": 0.5,
            "tran_loi_pct": 10.0, "che_do": che_do, "kieu_lot": kieu, "co_che": V.co_che_khoa(ts), "nguon": [], "luoi": {}, "co_dinh": {}}


def _kq_gia(ket_luan, engine=4, ky_vong=10.0):
    return {"ket_luan": ket_luan, "phien_ban_engine": engine, "ky_vong_o_tran_pct": ky_vong if ket_luan == "QUA" else None,
            "loi_suat_nam_pct": 5.0, "maxdd_pct": -20.0, "tn_id": 3, "calmar": 0.2}


def test_giu_can_nhieu_thi_truong_khong_chi_mot_hai():
    ung_vien, kq = [], {}
    # co che A: qua o 4 thi truong
    for i, m in enumerate(["AUDCAD", "AUDCHF", "EURCAD", "GBPAUD", "AUDCAD", "AUDCHF"]):
        u = _ung_vien_gia(i, m)
        ung_vien.append(u)
        kq[u["id"]] = _kq_gia("QUA" if i < 5 else "RUOT")
    # co che B: qua nhieu (6/6) nhung chi o MOT thi truong
    for i in range(6):
        u = _ung_vien_gia(100 + i, "XAUUSD", co_che="ban|cong|lui")
        ung_vien.append(u)
        kq[u["id"]] = _kq_gia("QUA")
    # co che C: toan RUOT
    for i in range(6):
        u = _ung_vien_gia(200 + i, ["AUDCAD", "EURCAD", "USDCHF"][i % 3], co_che="hai_chieu|nhan|-")
        ung_vien.append(u)
        kq[u["id"]] = _kq_gia("RUOT")
    cm = V.gom_co_che(ung_vien, kq)
    nhan = {m["co_che"]: m["nhan"] for m in cm["co_che"]}
    assert nhan["mua|phang|-"] == "GIU"
    assert nhan["ban|cong|lui"] == "THEO_DOI"                   # qua nhung chi 1 thi truong -> khong giu
    assert nhan["hai_chieu|nhan|-"] == "BO"
    giu = V.danh_sach_giu(ung_vien, kq, cm)
    assert [g["co_che"] for g in giu] == ["mua|phang|-"] and giu[0]["ung_vien"][0]["san_sang_niem_phong"] is True


def test_khong_do_duoc_khong_tinh_la_ruot_va_engine_cu_chua_san_sang_niem_phong():
    ung_vien = [_ung_vien_gia(i, m) for i, m in enumerate(["AUDCAD", "AUDCHF", "EURCAD", "GBPAUD", "NZDCAD", "USDCAD", "EURGBP"])]
    kq = {u["id"]: _kq_gia("QUA", engine=3) for u in ung_vien[:5]}
    kq.update({u["id"]: _kq_gia("KHONG_DO_DUOC") for u in ung_vien[5:]})
    cm = V.gom_co_che(ung_vien, kq)
    m = cm["co_che"][0]
    assert (m["qua"], m["ruot"], m["khong_do_duoc"]) == (5, 0, 2) and m["ty_le_qua"] == 1.0      # khong do duoc KHONG keo ty le xuong
    giu = V.danh_sach_giu(ung_vien, kq, cm)
    assert giu and not any(u["san_sang_niem_phong"] for u in giu[0]["ung_vien"])    # engine 3: chi la nhan, chua san sang


def test_so_voi_nen_hon_hay_ngang():
    ung_vien, kq = [], {}
    for i, m in enumerate(["AUDCAD", "AUDCHF", "EURCAD", "GBPAUD", "NZDCAD", "USDCAD"]):
        u = _ung_vien_gia(i, m)
        ung_vien.append(u)
        kq[u["id"]] = _kq_gia("QUA")
    for i in range(12):                                         # nhom ngau nhien cung 100% qua -> co che khong hon nen
        u = dict(_ung_vien_gia(300 + i, "AUDCAD"), lop="NGAU_NHIEN", cha="x")
        ung_vien.append(u)
        kq[u["id"]] = _kq_gia("QUA")
    assert V.gom_co_che(ung_vien, kq)["co_che"][0]["so_voi_nen"] == "NGANG_NEN"
    for u in ung_vien[6:]:
        kq[u["id"]] = _kq_gia("RUOT")
    cm = V.gom_co_che(ung_vien, kq)
    assert cm["nen_so_sanh"] == "ngau" and cm["co_che"][0]["so_voi_nen"] == "HON_NEN"


# ------------------------------------------------------------------------------------------- ap dung

def test_ke_hoach_ap_dung_chi_vao_cho_trong_va_luoi_hep():
    ts = _tham_so(buoc=20, tp=10, tran_tang=8, cho_lui=2)
    giu = [{"co_che": "mua|phang|lui", "ty_le_qua": 0.8, "thi_truong_qua": ["AUDCAD"], "so_voi_nen": "CHUA_BIET",
            "ung_vien": [{"id": "x1", "ma": "AUDCAD", "khung": "M15", "tham_so": ts, "von": 10000}]}]
    co_du_lieu = {("AUDCAD", "M15"), ("AUDCHF", "M15"), ("AUDNZD", "M15"), ("NZDCAD", "M15"), ("AUDCAD", "M30"), ("XAUUSD", "M15"), ("AUDCAD", "H1")}
    da_quet = {("AUDCHF", "M15", "mua")}
    kh = V.ke_hoach_ap_dung(giu, co_du_lieu, da_quet)
    dich = {s["den"] for s in kh}
    assert "AUDCHF M15" not in dich                              # da quet roi
    assert dich == {"AUDNZD M15", "NZDCAD M15", "AUDCAD M30"}    # H1 khong ke M15; XAUUSD khong chung dong tien
    arg = json.loads(kh[0]["lenh"][-1])
    assert arg["luoi"]["buoc"] == [15, 20, 26.6] or len(arg["luoi"]["buoc"]) == 3
    assert len(arg["luoi"]["cho_lui"]) == 3 and "tp" in arg["luoi"] and arg["co_dinh"]["che_do"] == "mua"
    assert arg["toi_da_o"] == 81
    assert len(V.ke_hoach_ap_dung(giu, co_du_lieu, set(), toi_da=2)) == 2
    assert V.khung_ke("M15") == ["M5", "M30"] and V.khung_ke("D1") == ["H4"] and V.khung_ke("M3") == []
    assert "AUDCHF" in V.thi_truong_ke("AUDCAD", {"AUDCHF", "XAUUSD", "EURGBP"}) and "EURGBP" not in V.thi_truong_ke("AUDCAD", {"EURGBP"})


def test_ra_don_ap_dung_khong_ghi_de_don_cu():
    goc = _goc()
    giu = [{"co_che": "mua|phang|-", "ty_le_qua": 0.9, "thi_truong_qua": ["AUDCAD", "AUDCHF", "EURCAD"], "so_voi_nen": "HON_NEN",
            "ung_vien": [{"id": "x1", "ma": "AUDCAD", "khung": "M15", "tham_so": _tham_so(), "von": 10000, "tn_id": 5, "san_sang_niem_phong": True}]}]
    specs = V.ke_hoach_nho_lai(giu)
    assert {s["loai"] for s in specs} == {"seeker", "ghi"}
    p = V.ra_don_ap_dung(specs[0], goc)
    assert p is not None and p.exists()
    assert V.ra_don_ap_dung(specs[0], goc) is None               # lan hai: da co don cung ten
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["lan"] == "NHE" and d["cong"]["kieu"] == "chay_duoc"


# --------------------------------------------------------------------------------------- bang diem

def test_bang_diem_tach_don_chay_duoc_voi_don_cho_ma_moi():
    goc = _goc()
    _nhip(goc)
    _quet(goc, "q1", "AUDCAD")
    _xong(goc, "tim1", [PY, "b.py", "dien-dan", "quet"], ["futures  en  XONG_PASS +12 bai", "smart-lab  ru  CHAN_403"])
    _ghi(goc / "viec" / "cho" / "cho-1.json", {"ma": "cho-1", "lan": "CPU", "lenh": _lenh("quet_luoi", {"ma": "AUDCAD", "khung": "M5"}), "uu_tien": 5})
    _ghi(goc / "viec" / "cho" / "cho-2.json", {"ma": "cho-2", "lan": "CPU", "lenh": _lenh("thu_luoi", {"ma": "AUDCAD", "khung": "M5", "doan": "xac_nhan"}),
                                               "uu_tien": 5, "can": ["engine4"]})
    bd = V.bang_diem(goc)
    t = bd["tong"]
    assert (t["cho_tong"], t["cho_chay_duoc"], t["cho_bi_chan"]) == (2, 1, 1) and t["thieu_ma"] == {"engine4": 1}
    assert bd["chang"]["KIEM"]["so_don"] == 1 and bd["chang"]["TIM"]["so_don"] == 1
    assert bd["chang"]["KIEM"]["phu"]["kham"]["so_don"] == 1 and "xac" not in bd["chang"]["KIEM"]["phu"]
    assert bd["san_luong"]["tim"]["nguon_ok"] == 1 and bd["san_luong"]["tim"]["bai_moi"] == 12 and bd["san_luong"]["tim"]["nguon_chan"] == 1
    assert bd["san_luong"]["lop_quet"] == {"CAO_NGUYEN": 1}
    assert bd["ung_vien"]["cao_nguyen"] == 1 and bd["ung_vien"]["cao_chua_ra_don"] == 1
    assert any("chua tung duoc kiem" in s for s in bd["diem_nghen"])
    assert bd["khuyen_nghi"] and "vong_lap --giao" in bd["khuyen_nghi"][0]
    tong_ty_le = sum(x["ty_le_gio"] for x in bd["chang"].values())
    assert abs(tong_ty_le - 1.0) < 0.01


def test_may_nha_khong_co_viec_duoc_bao_dung():
    goc = _goc()
    _nhip(goc)
    _ghi(goc / "viec" / "cho" / "a.json", {"ma": "a", "lan": "CPU", "lenh": _lenh("quet_luoi", {"ma": "X", "khung": "M5"}), "can": ["engine4"]})
    bd = V.bang_diem(goc)
    assert any("KHONG CO VIEC" in s for s in bd["diem_nghen"])
    assert any("Can chu du an" in s for s in V.tom_tat_cho_chu(bd))
    # co mot don chay duoc thi khong bao dong
    _ghi(goc / "viec" / "cho" / "b.json", {"ma": "b", "lan": "CPU", "lenh": _lenh("quet_luoi", {"ma": "X", "khung": "M5"})})
    assert not any("KHONG CO VIEC" in s for s in V.bang_diem(goc)["diem_nghen"])


# --------------------------------------------------------------------------- vong khep tu dau den cuoi

def _quet_nhieu_thi_truong(goc):
    """4 thi truong x 6 o cao nguyen (cung co che) + 4 o doi chung + du lieu khai bao cho thi truong lan can."""
    _nhip(goc)
    _nhieu_ung_vien(goc)
    _doan(goc, [(m, "M15") for m in ("AUDCAD", "AUDCHF", "EURCAD", "GBPAUD", "NZDCAD", "AUDNZD", "USDJPY")] + [("AUDCAD", "M30"), ("AUDCAD", "M5")])


def test_chay_ra_don_roi_khong_ra_lai_va_khong_cham_niem_phong():
    goc = _goc()
    _quet_nhieu_thi_truong(goc)
    bd = V.chay(goc, giao=12)
    dm = bd["don_moi"]
    assert len(dm["xac_nhan"]) == 12 and not dm["loi"]
    assert bd["ung_vien"]["cao_dang_cho"] > 0
    for p in (goc / "viec" / "cho").glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        assert "niem_phong" not in " ".join(d["lenh"]), p.name
        assert json.loads(d["lenh"][-1])["doan"] == "xac_nhan"
    # chay lai: dot moi khong lap lai don cu
    ten_cu = {p.stem for p in (goc / "viec" / "cho").glob("*.json")}
    dm2 = V.chay(goc, giao=12)["don_moi"]
    assert not (set(dm2["xac_nhan"]) & ten_cu) and len(dm2["xac_nhan"]) == 12
    # bao cao + so cai
    assert (goc / "reports" / "VONG_LAP.md").exists() and (goc / "reports" / "vong_lap" / "ung_vien.json").exists()
    uv = json.loads((goc / "reports" / "vong_lap" / "ung_vien.json").read_text(encoding="utf-8"))
    assert {u["nhom"] for u in uv} >= {"cao", "doi"}


def test_vong_khep_giu_roi_ap_dung_roi_im_khi_khong_doi():
    goc = _goc()
    _quet_nhieu_thi_truong(goc)
    tong_ung_vien = len(V.gom_ung_vien(V.doc_xong(goc)))
    # ra het don kiem (rong), may nha tra ket qua: o cao nguyen deu QUA, o doi chung deu RUOT
    V.chay(goc, giao=200, toi_da_engine4=0)
    cho = sorted((goc / "viec" / "cho").glob("vl-xn-*.json"))
    assert len(cho) >= tong_ung_vien
    for p in cho:
        d = json.loads(p.read_text(encoding="utf-8"))
        arg = json.loads(d["lenh"][-1])
        la_doi = arg["ma"] == "USDJPY"
        _tra(goc, p.stem, loi_suat=-2.0 if la_doi else 7.0, calmar=-0.05 if la_doi else 0.25, engine=3, kieu="cu")
    bd = V.chay(goc, giao=0)
    assert bd["ung_vien"]["cao_co_ket_qua"] >= 24 and bd["ung_vien"]["cao_dang_cho"] == 0
    assert len(bd["giu"]) == 1 and bd["giu"][0]["co_che"] == "mua|phang|-" and len(bd["giu"][0]["thi_truong_qua"]) == 4
    assert bd["co_che"]["nhom"]["doi"]["ruot"] == 4 and bd["co_che"]["nhom"]["cao"]["ruot"] == 0
    assert all(not u["san_sang_niem_phong"] for u in bd["giu"][0]["ung_vien"])      # engine 3
    # lan giao ke tiep: engine moi kiem lai o da QUA (gated) + ap dung (chuyen thi truong + SEEKER + ghi so tay)
    bd = V.chay(goc, giao=50, toi_da_engine4=10)
    dm = bd["don_moi"]
    assert 0 < len(dm["engine4"]) <= 10
    assert all((json.loads((goc / "viec" / "cho" / ("%s.json" % t)).read_text(encoding="utf-8")).get("can") == ["engine4"]) for t in dm["engine4"])
    ten = " ".join(dm["ap_dung"])
    assert V.TT_CHUYEN in ten and V.TT_SEEKER in ten
    chuyen = [t for t in dm["ap_dung"] if t.startswith(V.TT_CHUYEN)]
    assert chuyen and len(chuyen) <= 24
    for t in chuyen:
        d = json.loads((goc / "viec" / "cho" / ("%s.json" % t)).read_text(encoding="utf-8"))
        a = json.loads(d["lenh"][-1])
        assert (a["ma"], a["khung"]) in V.co_du_lieu_cua(goc) and a["toi_da_o"] == 81
    # idempotent: ngay sau do khong ra them don nao (tru dot moi cua nhom kiem neu con ung vien chua kiem)
    dm3 = V.chay(goc, giao=0, toi_da_engine4=10)["don_moi"]
    assert dm3 == {"xac_nhan": [], "engine4": [], "ap_dung": [], "loi": []}
    dm4 = V.chay(goc, giao=50, toi_da_engine4=10)["don_moi"]
    assert not dm4["engine4"] and not dm4["ap_dung"]


def test_ket_qua_engine_moi_thay_the_va_co_the_lam_mat_giu():
    goc = _goc()
    _quet_nhieu_thi_truong(goc)
    V.chay(goc, giao=200, toi_da_engine4=0)
    for p in sorted((goc / "viec" / "cho").glob("vl-xn-*.json")):
        arg = json.loads(json.loads(p.read_text(encoding="utf-8"))["lenh"][-1])
        _tra(goc, p.stem, loi_suat=-2.0 if arg["ma"] == "USDJPY" else 7.0, calmar=0.25, engine=3, kieu="cu")
    assert len(V.chay(goc, giao=0)["giu"]) == 1
    # engine moi (that hon) cho TAT CA o cao nguyen RUOT -> co che khong con duoc giu
    V.chay(goc, giao=0, toi_da_engine4=100)
    bd = V.chay(goc, giao=50, toi_da_engine4=100)
    for t in V.doc_cho(goc):
        if t["ma"].startswith(V.TT_XAC4):
            _tra(goc, t["ma"], loi_suat=-1.0, calmar=-0.02, engine=4)
    assert V.chay(goc, giao=0)["giu"] == []


# ------------------------------------------------------------------------------------ bao cao & CLI

def test_so_jsonl_chi_them_dong_khi_so_dem_doi_va_md_la_ascii():
    goc = _goc()
    _quet_nhieu_thi_truong(goc)
    V.chay(goc, giao=0)
    V.chay(goc, giao=0)
    so = goc / "reports" / "vong_lap" / "so.jsonl"
    assert len(so.read_text(encoding="utf-8").splitlines()) == 1
    V.chay(goc, giao=5)
    assert len(so.read_text(encoding="utf-8").splitlines()) == 2
    V.chay(goc, giao=0, ghi=False)                               # ghi=False khong dung vao dia
    assert len(so.read_text(encoding="utf-8").splitlines()) == 2
    txt = (goc / "reports" / "VONG_LAP.md").read_text(encoding="utf-8")
    txt.encode("ascii")                                          # quy uoc repo: tieng Viet khong dau
    assert "Tom tat" in txt and "Thoi gian may theo chang" in txt


def test_cli_in_khong_di_kem_giao(capsys):
    goc = _goc()
    _quet_nhieu_thi_truong(goc)
    with pytest.raises(SystemExit):
        V.main(["--in", "--giao", "5", "--goc", str(goc)])
    assert V.main(["--in", "--goc", str(goc)]) == 0
    assert not (goc / "reports").exists()
    out = capsys.readouterr().out
    assert "Vung lai tim duoc" in out
    assert V.main(["--giao", "3", "--goc", str(goc)]) == 0
    assert len(list((goc / "viec" / "cho").glob("vl-xn-*.json"))) == 3


# ----------------------------------------------------- dong TOM_TAT (nc_cong_cu) <-> bo doc cua vong lap

def _kq_thu_luoi(ts, trang_thai="DAT", loi=7.5, engine=4):
    return {"trang_thai": trang_thai, "ly_do": "co lai %+.2f%%/nam" % loi, "ma": "AUDCAD", "khung": "M15", "doan": "xac_nhan", "tham_so": ts,
            "von": 10000, "tn_id": 321,
            "tien": {"co_lai": True, "loi_suat_nam_pct": loi, "maxdd_pct": -41.2, "he_so_lot_tai_tran": 1.9, "loi_suat_o_tran_pct": loi * 1.9,
                     "hon_moc_pct": float("nan"), "gioi_han_lot": "TRAN_DD", "lo_treo_o_tran_pct_von": 3.0},
            "lenh": {"so_lenh": 140, "so_ro": 3, "lenh_moi_nam": 90.1, "tang_max": 6},
            "chi_so_luoi": {"calmar": 0.18, "loi_suat_nam_pct": loi, "maxdd_pct": -41.2, "lenh_nam": 90.1, "chay": False, "rac": [1] * 100},
            "engine": {"phien_ban": engine, "ghi_chu": "x" * 500}, "quy_cach": {"rat_dai": "y" * 2000}}


def test_tom_tat_dong_la_mot_dong_gon_va_vong_lap_doc_lai_duoc():
    from nhan import nc_cong_cu as NC
    kq = _kq_thu_luoi(_tham_so())
    dong = NC.tom_tat_dong(kq, "thu_luoi")
    assert dong.startswith("TOM_TAT {") and "\n" not in dong and len(dong) < 1500
    assert "NaN" not in dong and "quy_cach" not in dong and "rac" not in dong        # khong ro rac, khong NaN (json chuan)
    d = {"ma": "x", "trang_thai": "DAT", "bang_chung": {"ma_thoat": 0, "dong_cuoi": ["...", "}", dong]}}
    r = V.doc_xac_nhan(d)
    assert r["ket_luan"] == "QUA" and r["phien_ban_engine"] == 4 and r["tn_id"] == 321 and r["so_lenh"] == 140
    assert r["ky_vong_o_tran_pct"] == round(7.5 * 1.9, 1) and r["nguon_so"] == "TOM_TAT"
    am = V.doc_xac_nhan({"ma": "x", "bang_chung": {"dong_cuoi": [NC.tom_tat_dong(_kq_thu_luoi(_tham_so(), "AM", -2.0), "thu_luoi")]}})
    assert am["ket_luan"] == "RUOT"
    # cong cu khac / thieu trang_thai: khong in gi
    assert NC.tom_tat_dong(kq, "xem_so_tay") is None and NC.tom_tat_dong({"loi": "hong"}, "thu_luoi") is None and NC.tom_tat_dong(None, "thu_luoi") is None


def test_tom_tat_quet_luoi_giu_tham_so_day_du_ke_ca_khi_duoi_bi_cat():
    from nhan import nc_cong_cu as NC
    ts = _tham_so(buoc=22, tp=9)
    kq = {"trang_thai": "DAT", "ly_do": "CAO_NGUYEN: 89/120 o co lai, tot nhat +20.7%/nam o tran DD 80%", "ma": "AUDCAD", "khung": "M15",
          "tham_so_day_du": ts, "tn_id": 5, "doc_dung": "dai " * 100}
    dong = NC.tom_tat_dong(kq, "quet_luoi")
    d = {"ma": "q", "bang_chung": {"ma_thoat": 0, "giay": 10, "dong_cuoi": ["dong rac cuoi"] * 20 + [dong],
                                   "lenh": _lenh("quet_luoi", {"ma": "AUDCAD", "khung": "M15", "luoi": {"buoc": [20, 22]}, "co_dinh": {"che_do": "mua"}})}}
    u = V.doc_quet(d)
    assert u and u["lop"] == "CAO_NGUYEN" and (u["o_co_lai"], u["o_tong"]) == (89, 120) and u["tham_so"]["buoc"] == 22
    assert u["id"] == V.id_ung_vien("AUDCAD", "M15", ts)


def test_main_in_tom_tat_o_dong_cuoi_cung(capsys, monkeypatch):
    from nhan import nc_cong_cu as NC
    monkeypatch.setattr(NC, "goi", lambda ten, dv, vong_id=None: _kq_thu_luoi(_tham_so()))
    assert NC.main(["thu_luoi", "{}"]) == 0
    dong = capsys.readouterr().out.rstrip("\n").splitlines()
    assert dong[-1].startswith("TOM_TAT ") and dong[-2].strip() == "}"
    monkeypatch.setattr(NC, "goi", lambda ten, dv, vong_id=None: {"x": 1})
    NC.main(["xem_gi_do", "{}"])
    assert "TOM_TAT" not in capsys.readouterr().out
