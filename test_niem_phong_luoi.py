# -*- coding: utf-8 -*-
"""Niem phong cho he LUOI (`nc_thi_nghiem.niem_phong_luoi`) - 04/10/2026.

Phep thu CUOI cua he luoi / DCA / martingale: MOT lan cho mot khai bao da dong bang, tren 20% cuoi du lieu. Mot niem phong da mo
thi khong mo lai duoc, nen file nay giu nhung dieu KHONG DUOC VO:

  1. LOT chot chi bang du lieu DA MO va chot TRUOC khi cham doan niem phong: cung mot lot du doan niem phong dep hay xau.
  2. Mot khai bao mot lan. `lot` va cach viet so (21 / 21.0) khong phai khai bao moi; moi dong gia thuyet toi da 3 lan.
  3. Ly do KHONG noi gi ve doan niem phong (khai bao sai, khong chot duoc lot, chi phi KHAI) khong duoc tieu luot.
  4. Cong TIEN = tieu chi chu du an: co lai sau phi (ke ca lo treo cuoi doan) + khong stop-out + maxDD < 80% + >= 20 lenh.
  5. Sau stop-out engine van cong don lai va so lenh -> con so do KHONG duoc in ra nhu thanh tich.

Du lieu tong hop tat dinh (`_chuoi`, seed 7): doan niem phong = [4800, 6000) theo ty le 0,8-1,0. Cac "duoi" ben duoi giu nguyen
[0, 4800) tung bit va chi thay doan niem phong - nhu vay moi khac biet cua ket qua la do doan niem phong, khong phai do lot.
"""
from __future__ import annotations

import itertools
import json

import numpy as np
import pytest

from nhan import luoi as LU
from nhan import nc_cong_cu as CC
from nhan import nc_du_lieu as NDL
from nhan import nc_so_cai as SC
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN
from qwen import cau_trang as CT
from test_luoi_quy_cach import TS, _chuoi, _cp

VON = 10000.0
BAR_NP = 4800            # chi so bar dau tien cua doan niem phong tren chuoi 6000 bar


# ------------------------------------------------------------------ MOI TRUONG + GIAN DIEP
@pytest.fixture
def mt(tmp_path, monkeypatch):
    """Moi truong tat dinh. `su_kien` ghi LAI THU TU moi lan nap du lieu / cat doan / do chi phi / chay engine."""
    monkeypatch.setattr(LU, "FILE_QUY_CACH", tmp_path / "luoi_quy_cach.json")
    monkeypatch.setattr(TN, "_DEM_MOC", {})
    st = {"df": _chuoi(), "cp": _cp(do_tin="SAN"), "su_kien": []}
    dem = itertools.count()

    def so_moi():
        monkeypatch.setattr(ST, "DB", tmp_path / ("nc%d.db" % next(dem)))
    st["so_moi"] = so_moi
    so_moi()

    def nap(ma, khung="H4"):
        st["su_kien"].append(("nap", ma, khung))
        return st["df"]

    def chi_phi(ma, d):
        st["su_kien"].append(("chi_phi", len(d)))
        return st["cp"](len(d)) if callable(st["cp"]) else st["cp"]

    cat_goc, chay_goc = NDL.cat_doan, LU.chay_mang

    def cat(df, doan, _giay_phep=False):
        st["su_kien"].append(("cat", doan))
        return cat_goc(df, doan, _giay_phep)

    def chay(dl, ts, von, ghi_lenh=False):
        st["su_kien"].append(("chay", dl.idx[0], dl.idx[-1], ts.lot))
        return chay_goc(dl, ts, von, ghi_lenh)

    monkeypatch.setattr(NDL, "nap", nap)
    monkeypatch.setattr(NDL, "chi_phi", chi_phi)
    monkeypatch.setattr(NDL, "cat_doan", cat)
    monkeypatch.setattr(LU, "chay_mang", chay)
    return st


def _gt(ten="luoi hai chieu AUDCAD", **kw):
    return ST.them_gia_thuyet(ten, "luoi gat loi nho nhieu lan o bien do hep", **kw)


def _np(mt, ts=None, von=VON, ma="AUDCAD", gt=None, **kw):
    return TN.niem_phong_luoi(ma, "M15", dict(TS if ts is None else ts), von, gt_id=gt, **kw)


def _dem_niem_phong() -> int:
    return int(ST.mot("SELECT COUNT(*) n FROM niem_phong")["n"])


def _tt_gt(gt) -> str:
    return ST.mot("SELECT trang_thai FROM gia_thuyet WHERE id=?", gt)["trang_thai"]


def _da_cham_doan_niem_phong(mt) -> bool:
    return ("cat", "niem_phong") in mt["su_kien"]


# ------------------------------------------------------------------ CAC "DUOI": thay doan niem phong, giu nguyen doan mo
def _x0(df) -> float:
    return float(df["close"].iloc[BAR_NP - 1])


def _ghep(df, x, bien=1e-4):
    """Giu [0, BAR_NP) tung bit; doan niem phong lay duong dong cua x (high / low = +-bien quanh open / close)."""
    d = df.copy()
    x = np.asarray(x, float)
    assert len(x) == len(d) - BAR_NP
    o = np.r_[_x0(df), x[:-1]]
    hi = np.maximum(o, x) + bien
    lo = np.minimum(o, x) - bien
    for c, v in (("open", o), ("high", hi), ("low", lo), ("close", x)):
        d.iloc[BAR_NP:, d.columns.get_loc(c)] = v
    return d


def _duoi_sap(df):
    """Roi deu 6e-4 / bar (~0,72 sau 1200 bar): luoi mo het tang va CHAY tai khoan o bar ~224."""
    rng = np.random.RandomState(99)
    m = len(df) - BAR_NP
    return _ghep(df, _x0(df) + np.cumsum(np.full(m, -6e-4) + rng.normal(0, 4e-4, m)))


def _duoi_troi_xuong(df):
    """Troi xuong cham: lenh chot van duoc chot (loi suat da chot > 0) nhung cuoi doan con lo treo lon."""
    rng = np.random.RandomState(5)
    m = len(df) - BAR_NP
    return _ghep(df, _x0(df) + np.cumsum(np.full(m, -2e-5) + rng.normal(0, 3e-4, m)))


def _duoi_phang(df):
    """Gia dung yen: luoi khong mo duoc lenh nao -> it lenh."""
    return _ghep(df, np.full(len(df) - BAR_NP, _x0(df)), bien=0.0)


def _duoi_chu_v(df, sau):
    """Roi `sau` roi hoi lai dung gia cu: cuoi doan hoa von, nhung DD giua chung lon (luoi MUA gong het tang)."""
    m = len(df) - BAR_NP
    h = m // 2
    x0 = _x0(df)
    x = np.r_[x0 - sau * np.sin(np.linspace(0, np.pi / 2, h)),
              x0 - sau + sau * (1 - np.cos(np.linspace(0, np.pi / 2, m - h)))]
    return _ghep(df, x)


MUA = dict(TS, che_do="mua")


# ------------------------------------------------------------------ 1. DUONG DI DUNG: chot lot truoc, cham doan niem phong sau
def test_dat_chot_lot_tren_du_lieu_mo_truoc_roi_moi_cham_doan_niem_phong(mt):
    gt = _gt()
    r = _np(mt, gt=gt)
    assert r["trang_thai"] == "DAT", r["ly_do"]
    ev, df = mt["su_kien"], mt["df"]
    # thu tu: moi lan chay tren du lieu mo DEU xay ra truoc khi cat doan niem phong; sau do dung MOT lan chay, o dung lot da chot
    i_cat = ev.index(("cat", "niem_phong"))
    chay_truoc = [e for e in ev[:i_cat] if e[0] == "chay"]
    chay_sau = [e for e in ev[i_cat + 1:] if e[0] == "chay"]
    assert chay_truoc and all(e[2] < df.index[BAR_NP] for e in chay_truoc)
    assert len(chay_sau) == 1 and chay_sau[0][1] == df.index[BAR_NP] and chay_sau[0][3] == r["cam_ket"]["lot"]
    assert r["cam_ket"]["so_lan_chay"] == len(chay_truoc)
    assert [e[1] for e in ev if e[0] == "cat"] == ["xac_nhan", "niem_phong"]
    assert r["cua_so"]["mo"] == [str(df.index[0]), str(df.index[BAR_NP - 1])]
    assert r["cua_so"]["niem_phong"] == [str(df.index[BAR_NP]), str(df.index[-1])]
    # ghi so: mot dong niem_phong + mot thi nghiem, gia thuyet len XAC_NHAN
    assert _dem_niem_phong() == 1 and _tt_gt(gt) == "XAC_NHAN"
    tn = ST.mot("SELECT * FROM thi_nghiem WHERE id=?", r["tn_id"])
    assert (tn["loai"], tn["doan"], tn["trang_thai"], tn["gt_id"]) == ("niem_phong_luoi", "niem_phong", "DAT", gt)
    # khai bao day du, khong co `lot`; lot la lot DA CHOT; ghi ro day la mo phong, chua phai phat hien that
    assert "lot" not in r["khai_bao"] and r["khai_bao"]["buoc"] == 15 and r["khai_bao"]["che_do"] == "hai_chieu"
    assert r["cam_ket"]["lot_khai_bao"] is None and 0.01 <= r["cam_ket"]["lot"] <= 40.96
    assert r["tien"]["co_lai"] is True and not r["tien"]["chay_tai_khoan"] and r["tien"]["loi_suat_nam_pct"] > 0
    assert abs(r["tien"]["maxdd_pct"]) < 80.0 and r["lenh"]["so_lenh"] >= 20
    assert "chua phai phat hien" in r["goi_ten_dung"]
    assert any("SAN" in c for c in r["nhan"]["canh_bao"])                       # AUDCAD: phi la san, khong phai do
    assert r["nhan"]["da_qua_xac_nhan"] is False and any("CHUA tung DAT" in c for c in r["nhan"]["canh_bao"])


def test_lot_chot_la_lot_lon_nhat_con_thoa_moi_dieu_kien_tren_du_lieu_mo(mt):
    """Do doc lap voi tim kiem cua code: quet tung lot 0,01 bang CHINH engine, khong qua `_lot_cam_ket_luoi`."""
    r = _np(mt, gt=_gt())
    dl = LU.chuan_bi(mt["df"].iloc[:BAR_NP], LU.QC_AUDCAD)
    don_bay_tk = LU.ThamSo(**TS).don_bay

    def kha_thi(lot: float) -> bool:
        kq = LU.chay_mang(dl, LU.ThamSo(**dict(TS, lot=round(lot, 6))), VON)
        e = np.asarray(kq.duong_equity, float)
        return bool(not kq.chay and abs(LU.chi_so(kq, VON)["maxdd_pct"]) < 79.9 and kq.margin * don_bay_tk / VON <= 10.0
                    and kq.lai_rong > 0 and e[-1] > VON)

    lot = r["cam_ket"]["lot"]
    k = round(lot / 0.01)
    assert kha_thi(lot) and not kha_thi(lot + 0.01)                              # lon nhat
    assert all(kha_thi(j * 0.01) for j in range(1, k + 1))                       # va moi lot nho hon deu song duoc
    assert r["cam_ket"]["gioi_han"] == "TRAN_DON_BAY" and k >= 2                 # tran don bay (<= 10) la thu chan lot


def test_lot_chot_chi_phu_thuoc_du_lieu_mo_doan_niem_phong_dep_hay_xau_deu_nhu_nhau(mt):
    base = _chuoi()
    kq = {}
    for ten, df in (("co_ban", base), ("sap", _duoi_sap(base)), ("phang", _duoi_phang(base)),
                    ("troi_xuong", _duoi_troi_xuong(base))):
        mt["so_moi"]()
        mt["df"] = df
        kq[ten] = _np(mt, gt=_gt())
    assert [kq[k]["trang_thai"] for k in kq] == ["DAT", "AM", "CHUA_DO_DUOC", "AM"]
    assert len({kq[k]["cam_ket"]["lot"] for k in kq}) == 1
    assert len({json.dumps(kq[k]["cam_ket"]["tren_du_lieu_mo"], sort_keys=True) for k in kq}) == 1
    assert len({kq[k]["cam_ket"]["so_lan_chay"] for k in kq}) == 1


# ------------------------------------------------------------------ 2. MOT LAN: van tay, lot va cach viet so, tran 3 lan
def test_mot_khai_bao_mot_lan_lot_va_cach_viet_so_khong_phai_khai_bao_moi(mt):
    gt = _gt()
    r1 = _np(mt, ts=dict(TS, lot=2.0), gt=gt)
    assert r1["trang_thai"] in ("DAT", "AM") and r1["cam_ket"]["lot_khai_bao"] == 2.0 and "lot" not in r1["khai_bao"]
    assert r1["cam_ket"]["lot"] != 2.0               # lot khai bao khong duoc dung: lot la lot DA CHOT tu du lieu mo
    n_su_kien = len(mt["su_kien"])
    for ts in (dict(TS), dict(TS, lot=0.5), {"buoc": 15.0, "tp": 10.0, "tran_tang": 12.0},
               dict(TS, che_do="hai_chieu", kieu_lot="phang", tia_lenh=False)):    # ghi ro gia tri mac dinh = cung khai bao
        r = _np(mt, ts=ts, gt=gt)
        assert "da_mo_truoc" in r and "XAC NHAN LA HAM Y NGUYEN" in r["da_mo_truoc"], ts
        assert r["trang_thai"] == r1["trang_thai"] and r["cam_ket"]["lot"] == r1["cam_ket"]["lot"]
    assert len(mt["su_kien"]) == n_su_kien           # khong nap, khong cat, khong chay lai
    assert _dem_niem_phong() == 1
    # doi MA, KHUNG, VON hay mot tham so cau truc = khai bao khac
    for kw in (dict(ts=dict(TS, tp=11)), dict(von=20000.0)):
        assert "da_mo_truoc" not in _np(mt, gt=gt, **kw)
    assert _dem_niem_phong() == 3


def test_toi_da_ba_lan_moi_dong_gia_thuyet_lan_thu_tu_khong_cham_doan_niem_phong(mt):
    goc = _gt()
    con = _gt("bien the con", cha=goc)
    r = [_np(mt, gt=goc), _np(mt, ts=dict(TS, tp=9), gt=con), _np(mt, ts=dict(TS, tp=11), gt=con)]
    assert all(x["trang_thai"] in ("DAT", "AM") and "da_mo_truoc" not in x for x in r), [x.get("ly_do") for x in r]
    assert [e for e in mt["su_kien"] if e == ("cat", "niem_phong")] == [("cat", "niem_phong")] * 3
    n_su_kien = len(mt["su_kien"])
    r4 = _np(mt, ts=dict(TS, tp=12), gt=con)
    assert r4["trang_thai"] == "CHUA_DO_DUOC" and "da mo niem phong 3 lan" in r4["ly_do"]
    assert len(mt["su_kien"]) == n_su_kien and _dem_niem_phong() == 3        # chua nap gi, chua cham gi


# ------------------------------------------------------------------ 3. BA TRANG THAI + CONG TIEN
def test_am_chay_tai_khoan_khong_in_loi_suat_gia(mt):
    """Sau stop-out engine van cong don lai da chot va so lenh (chi duong equity bi dua ve 0): khong duoc in thanh tich."""
    mt["df"] = _duoi_sap(_chuoi())
    gt = _gt()
    r = _np(mt, gt=gt)
    assert r["trang_thai"] == "AM" and "CHAY TAI KHOAN" in r["ly_do"], r["ly_do"]
    t, c = r["tien"], r["chi_so_luoi"]
    assert t["chay_tai_khoan"] is True and 0 < t["bar_chay"] < len(mt["df"]) - BAR_NP
    assert t["co_lai"] is False and t["maxdd_pct"] == -100.0
    assert t["loi_suat_nam_pct"] is None and t["loi_suat_ke_ca_lo_treo_pct"] is None
    assert all(c[k] is None for k in TN._SAU_STOP_OUT), c               # moi chi so cong don ca phan SAU khi tai khoan mat
    assert t["phi_tren_lai_gop_pct"] is None and t["lo_treo_dinh_pct_von"] is None and t["don_bay_dinh"] is None
    assert r["lenh"]["gom_lenh_sau_stop_out"] is True and r["lenh"]["lenh_moi_nam"] is None
    assert not any("phi (spread" in x or "KHONG hon moc" in x for x in r["nhan"]["canh_bao"]), r["nhan"]["canh_bao"]
    assert _tt_gt(gt) == "TRUOT_NIEM_PHONG" and _dem_niem_phong() == 1


def test_stop_out_duoc_xet_truoc_so_lenh_it_nen_khong_bi_nhan_nham_la_chua_do_duoc(mt, monkeypatch):
    """Dem lenh sau stop-out khong noi gi ve doan niem phong; nhung stop-out thi co: no phai la AM, khong la 'it lenh'."""
    mt["df"] = _duoi_sap(_chuoi())
    chay_goc = LU.chay_mang

    def it_lenh(dl, ts, von, ghi_lenh=False):
        kq = chay_goc(dl, ts, von, ghi_lenh)
        if dl.idx[0] >= mt["df"].index[BAR_NP]:
            kq.so_lenh = 3
        return kq
    monkeypatch.setattr(LU, "chay_mang", it_lenh)
    r = _np(mt, gt=_gt())
    assert r["trang_thai"] == "AM" and "CHAY TAI KHOAN" in r["ly_do"], r["ly_do"]


def test_am_khong_co_lai_khi_tinh_ca_lo_treo_du_lai_da_chot_duong(mt):
    """Luoi khong the thang bang cach khong bao gio dong lenh lo: lo treo cuoi doan tinh vao lai."""
    mt["df"] = _duoi_troi_xuong(_chuoi())
    gt = _gt()
    r = _np(mt, gt=gt)
    assert r["trang_thai"] == "AM" and "KHONG co lai" in r["ly_do"], r["ly_do"]
    t = r["tien"]
    assert t["co_lai"] is False and not t["chay_tai_khoan"] and r["lenh"]["so_lenh"] >= 20
    assert t["loi_suat_nam_pct"] > 0 > t["loi_suat_ke_ca_lo_treo_pct"]          # da chot duong, tinh ca lo treo thi am
    assert not any("KHONG hon moc" in x for x in r["nhan"]["canh_bao"])           # khong co lai thi khong so voi moc
    assert _tt_gt(gt) == "TRUOT_NIEM_PHONG"


def test_duoi_80_du_cao_van_dat_con_tu_80_tro_len_la_am(mt):
    """Tieu chi chu du an 25/09: chi can co lai va maxDD < 80% - khong chat hon, khong long hon."""
    mt["df"] = _duoi_chu_v(_chuoi(), 0.05)
    r = _np(mt, ts=MUA, gt=_gt())
    assert r["trang_thai"] == "DAT", r["ly_do"]
    assert 60.0 < abs(r["tien"]["maxdd_pct"]) < 80.0 and r["tien"]["co_lai"] is True
    assert r["tien"]["don_bay_dinh"] > 10 and any("don bay dinh" in x for x in r["nhan"]["canh_bao"])   # nhan, khong chan
    mt["so_moi"]()
    mt["df"] = _duoi_chu_v(_chuoi(), 0.064)
    gt = _gt()
    r2 = _np(mt, ts=MUA, gt=gt)
    assert r2["trang_thai"] == "AM" and "NHUNG maxDD" in r2["ly_do"], r2["ly_do"]
    assert r2["tien"]["co_lai"] is True and not r2["tien"]["chay_tai_khoan"] and abs(r2["tien"]["maxdd_pct"]) >= 80.0
    assert r2["cam_ket"]["lot"] == r["cam_ket"]["lot"]                            # cung lot: chi doan niem phong khac
    assert _tt_gt(gt) == "TRUOT_NIEM_PHONG"


def test_chua_do_duoc_it_lenh_van_tieu_luot_niem_phong(mt):
    """Da cham doan niem phong thi het luot, du ket qua khong du lenh de ket luan; gia thuyet khong doi trang thai."""
    mt["df"] = _duoi_phang(_chuoi())
    gt = _gt()
    r = _np(mt, gt=gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "lenh <" in r["ly_do"], r["ly_do"]
    assert _dem_niem_phong() == 1 and _tt_gt(gt) == "MO"
    r2 = _np(mt, gt=gt)
    assert "da_mo_truoc" in r2 and r2["trang_thai"] == "CHUA_DO_DUOC"


# ------------------------------------------------------------------ 4. KHONG TIEU LUOT khi ly do khong noi gi ve doan niem phong
@pytest.mark.parametrize("ts,von,hong", [
    (dict(che_do="mua", buoc=10, tp=40, tran_tang=30), 1000.0, "STOPOUT"),
    (dict(TS), VON, "MAT_LAI"),
])
def test_khong_chot_duoc_lot_thi_khong_tieu_luot_va_khai_bao_con_nguyen(mt, ts, von, hong):
    mt["df"] = _chuoi(xu_huong=-4e-5, hoi_quy=0.0)                                # troi xuong lien tuc: du lieu mo da thua
    gt = _gt()
    r = _np(mt, ts=ts, von=von, gt=gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "(%s)" % hong in r["ly_do"] and "CHUA bi dung toi" in r["ly_do"], r["ly_do"]
    assert r["cam_ket"]["chot"] is False and r["cam_ket"]["thu"]["lot"] == 0.01
    assert not _da_cham_doan_niem_phong(mt) and _dem_niem_phong() == 0 and _tt_gt(gt) == "MO"
    assert "da_mo_truoc" not in _np(mt, ts=ts, von=von, gt=gt)                    # khai bao con nguyen: thu lai duoc
    mt["df"] = _chuoi()                                                            # co du lieu tot hon -> chot duoc, mo duoc
    r2 = _np(mt, ts=dict(TS), gt=gt)
    assert r2["trang_thai"] in ("DAT", "AM") or hong == "STOPOUT"


def test_mat_lai_o_lot_nho_nhat_in_ca_loi_suat_chot_lan_lo_treo(mt):
    mt["df"] = _chuoi(xu_huong=-4e-5, hoi_quy=0.0)
    ly = _np(mt, gt=_gt())["ly_do"]
    assert "MAT_LAI" in ly and "loi suat chot +" in ly and "ke ca lo treo -" in ly, ly      # chot > 0 nhung treo < 0


def test_du_lieu_mo_qua_ngan_khong_tieu_luot(mt):
    mt["df"] = _chuoi(n=60)
    gt = _gt()
    r = _np(mt, gt=gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "bar" in r["ly_do"]
    assert not _da_cham_doan_niem_phong(mt) and _dem_niem_phong() == 0


@pytest.mark.parametrize("ts,von,ky_tu", [
    ({"khong_co_tham_so": 1}, VON, "khong biet"),
    ({"dung_lo_tong": 5.0}, VON, "CHUA cai dat"),
    (dict(TS, khop_bar="cuc_tri"), VON, "khop_bar"),         # mo hinh bar lac quan: khong niem phong bang no
    (dict(TS, khop_bar=None), VON, "khop_bar"),
    (dict(TS, buoc=0), VON, "buoc phai > 0"),
    (dict(TS, tp=-1.0), VON, "tp phai > 0"),
    (dict(TS, don_bay=0), VON, "don_bay phai > 0"),
    (dict(TS, tran_tang=2.5), VON, "tran_tang"),
    (dict(TS, tran_tang=0), VON, "tran_tang"),
    (dict(TS, che_do="len"), VON, "che_do"),
    (dict(TS, kieu_lot="mu"), VON, "kieu_lot"),
    (dict(TS, tia_lenh="true"), VON, "tia_lenh"),
    (dict(TS, buoc="15"), VON, "so huu han"),               # "15" va 15 khong duoc thanh hai khai bao
    (dict(TS, buoc=True), VON, "so huu han"),
    (dict(TS, tp=float("nan")), VON, "so huu han"),
    (dict(TS, he_so_lot=float("inf")), VON, "so huu han"),
    (dict(TS), 0.0, "von phai la so huu han"),
    (dict(TS), -5.0, "von phai la so huu han"),
    (dict(TS), float("nan"), "von phai la so huu han"),
    (dict(TS), "abc", "khai bao sai"),
])
def test_khai_bao_sai_bi_tu_choi_truoc_khi_cham_du_lieu(mt, ts, von, ky_tu):
    gt = _gt()
    r = _np(mt, ts=ts, von=von, gt=gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and ky_tu in r["ly_do"], r["ly_do"]
    assert mt["su_kien"] == [] and _dem_niem_phong() == 0 and _tt_gt(gt) == "MO"


def test_thieu_hoac_sai_gia_thuyet_bi_tu_choi_truoc_khi_cham_du_lieu(mt):
    assert "gt_id" in _np(mt, gt=None)["ly_do"]
    assert "khong co gia thuyet" in _np(mt, gt=9999)["ly_do"]
    assert mt["su_kien"] == [] and _dem_niem_phong() == 0


@pytest.mark.parametrize("ma,tu_khoa", [("USDJPY", "doi chieu"), ("XAUUSD", "doi chieu"), ("US500Cash", "chua ho tro")])
def test_ma_chua_ho_tro_hoac_chua_doi_chieu_bi_tu_choi_truoc_khi_cham_du_lieu(mt, ma, tu_khoa):
    r = _np(mt, ma=ma, gt=_gt())
    assert r["trang_thai"] == "CHUA_DO_DUOC" and tu_khoa in r["ly_do"], r["ly_do"]
    assert mt["su_kien"] == [] and _dem_niem_phong() == 0


def test_chi_phi_khai_khong_bao_gio_dat_va_khong_tieu_luot(mt):
    """KHAI = chi phi chua do: ca o du lieu mo lan o doan niem phong, `niem_phong` chua bi dung toi; do duoc roi thi mo duoc."""
    gt = _gt()
    mt["cp"] = _cp(do_tin="KHAI")
    r = _np(mt, ma="USDCHF", gt=gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "KHAI" in r["ly_do"] and "chua bi dung toi" in r["ly_do"], r["ly_do"]
    assert not _da_cham_doan_niem_phong(mt) and _dem_niem_phong() == 0
    # du lieu mo do duoc, doan niem phong thi KHAI: cat roi nhung CHUA chay va CHUA ghi
    mt["cp"] = lambda n: _cp(do_tin="SAN") if n <= BAR_NP else _cp(do_tin="KHAI")
    r = _np(mt, ma="USDCHF", gt=gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "KHAI" in r["ly_do"] and "doan niem phong" in r["ly_do"], r["ly_do"]
    assert not [e for e in mt["su_kien"] if e[0] == "chay" and e[1] >= mt["df"].index[BAR_NP]]
    assert _dem_niem_phong() == 0 and _tt_gt(gt) == "MO"
    mt["cp"] = _cp(do_tin="SAN")
    r = _np(mt, ma="USDCHF", gt=gt)
    assert "da_mo_truoc" not in r and r["trang_thai"] in ("DAT", "AM", "CHUA_DO_DUOC")
    assert r["chi_phi_do_tin"] == "SAN" and any("tester" in c for c in r["canh_bao"])


# ------------------------------------------------------------------ 5. NHAN (khong chan)
def test_nhan_da_qua_xac_nhan_chi_khi_dung_khai_bao_va_dung_von(mt):
    gt = _gt()
    assert TN.danh_gia_luoi("AUDCAD", "M15", dict(TS), "xac_nhan", von=VON, gt_id=gt)["trang_thai"] == "DAT"
    r = _np(mt, gt=gt)
    assert r["nhan"]["da_qua_xac_nhan"] is True and not any("CHUA tung DAT" in c for c in r["nhan"]["canh_bao"])
    r2 = _np(mt, von=20000.0, gt=gt)                                              # von khac = khai bao khac, chua tung DAT
    assert r2["nhan"]["da_qua_xac_nhan"] is False
    r3 = _np(mt, ts=dict(TS, tp=11), gt=gt, ghi_chu="chong len doi song con tin hieu goc: chi la LAM LAI")
    assert r3["nhan"]["da_qua_xac_nhan"] is False
    assert any("ghi chu nguoi goi: chong len doi song" in c for c in r3["nhan"]["canh_bao"])
    # ghi chu di cung ket luan cua gia thuyet: trang thai XAC_NHAN khong duoc doc nhu bang chung doc lap
    assert "ghi chu: chong len doi song con tin hieu goc" in ST.mot("SELECT ket_luan FROM gia_thuyet WHERE id=?", gt)["ket_luan"]


def test_khai_bao_chuan_hoa_khong_chua_lot_va_khong_phan_biet_cach_viet_so():
    a = TN._khai_bao_luoi({"buoc": 15, "tp": 10.0, "tran_tang": 12, "lot": 3.0})
    b = TN._khai_bao_luoi({"buoc": 15.0, "tp": 10, "tran_tang": 12.0})
    assert a == b and "lot" not in a
    assert TN._khai_bao_luoi({}) != a and set(TN._khai_bao_luoi({})) == set(a)   # mac dinh dien day du, cung bo khoa


# ------------------------------------------------------------------ 6. LOT CAM KET: tran don bay, tran lot
def test_tran_don_bay_chan_lot_va_bo_tran_thi_lot_cao_hon_nhieu(mt, monkeypatch):
    dl = LU.chuan_bi(mt["df"].iloc[:BAR_NP], LU.QC_AUDCAD)
    co = TN._lot_cam_ket_luoi(dl, dict(TS), VON)
    assert co["chot"] and co["gioi_han"] == "TRAN_DON_BAY" and co["tren_du_lieu_mo"]["don_bay_dinh"] <= TN.L_TOI_DA
    monkeypatch.setattr(TN, "L_TOI_DA", 1e9)
    khong = TN._lot_cam_ket_luoi(dl, dict(TS), VON)
    assert khong["chot"] and khong["lot"] > 5 * co["lot"] and khong["gioi_han"] == "STOPOUT"
    assert khong["tren_du_lieu_mo"]["don_bay_dinh"] > 100            # thu ma tran don bay (10) dang chan


def test_tran_lot_khi_khong_dieu_kien_nao_hong_truoc(mt, monkeypatch):
    monkeypatch.setattr(TN, "BUOC_LOT_TOI_DA", 4)
    ck = TN._lot_cam_ket_luoi(LU.chuan_bi(mt["df"].iloc[:BAR_NP], LU.QC_AUDCAD), dict(TS), VON)
    assert ck["chot"] and ck["gioi_han"] == "TRAN_LOT" and ck["lot"] == 0.04 and ck["so_buoc"] == 4


# ------------------------------------------------------------------ 7. CONG CU nc, DANH SACH TRANG, SO CAI
def test_cong_cu_nc_niem_phong_luoi_dang_ky_dung_schema_va_chay_qua_goi(mt):
    assert "niem_phong_luoi" in CC.THEO_TEN
    sch = CC.THEO_TEN["niem_phong_luoi"]["schema"]
    assert set(sch["required"]) == {"ma", "khung", "tham_so", "gt_id"} and "lot" not in sch["properties"]
    gt = _gt()
    assert "thieu tham so" in CC.goi("niem_phong_luoi", {"ma": "AUDCAD", "khung": "M15", "tham_so": dict(TS)})["loi"]
    assert "khong co trong schema" in CC.goi("niem_phong_luoi", {"ma": "AUDCAD", "khung": "M15", "tham_so": dict(TS),
                                                                 "gt_id": gt, "cong_that": False})["loi"]
    assert mt["su_kien"] == [] and _dem_niem_phong() == 0
    r = CC.goi("niem_phong_luoi", {"ma": "audcad", "khung": "m15", "tham_so": dict(TS), "gt_id": gt, "von": 10000,
                                   "ghi_chu": "thu qua cong cu"})
    assert r["trang_thai"] == "DAT" and r["ma"] == "AUDCAD" and r["khung"] == "M15" and r["von"] == VON
    assert any("thu qua cong cu" in c for c in r["nhan"]["canh_bao"])
    r2 = CC.goi("niem_phong_luoi", {"ma": "AUDCAD", "khung": "M15", "tham_so": dict(TS), "gt_id": gt})
    assert "da_mo_truoc" in r2


def test_may_nha_chay_duoc_don_niem_phong_luoi_qua_danh_sach_trang():
    lenh = ["{py}", "b.py", "nc", "cc", "niem_phong_luoi",
            json.dumps({"ma": "AUDCAD", "khung": "M15", "tham_so": dict(TS), "von": 10000, "gt_id": 4}, separators=(",", ":"))]
    assert CT.kiem_lenh(lenh) is None, CT.kiem_lenh(lenh)
    assert CT.kiem_lenh(lenh[:5] + ["[1]"]) is not None                           # JSON phai la object


def test_dau_niem_phong_luoi_di_qua_so_cai_nen_cai_lai_may_van_con(mt, tmp_path):
    """So cai nghien cuu nam trong git: sau khi cai lai, mot khai bao da niem phong KHONG mo lai duoc."""
    gt = _gt()
    r1 = _np(mt, gt=gt)
    thu = tmp_path / "so_cai"
    assert SC.xuat(dich=thu)["niem_phong"] == 1
    mt["so_moi"]()
    SC.nhap(nguon=thu, db=ST.DB)
    n_su_kien = len(mt["su_kien"])
    r2 = _np(mt, gt=gt)
    assert "da_mo_truoc" in r2 and r2["trang_thai"] == r1["trang_thai"] and r2["cam_ket"]["lot"] == r1["cam_ket"]["lot"]
    assert len(mt["su_kien"]) == n_su_kien and _dem_niem_phong() == 1             # khong cham lai doan niem phong
