# -*- coding: utf-8 -*-
"""Test doi_chung_nhieu: thuoc do DOI CHUNG NHIEU cua chang KIEM (vong lap, 10/10/2026).

Cac test duoi day co CHU DICH bat nhung loi lam cho con so 'nhieu cho ra X% qua' SAI MA VAN TRONG BINH THUONG:
  - chuoi gia khong co dap an dung (hoi quy khong hoi quy, 'cung duong gia' nhung bien dong khong nhan dung ti le);
  - cong cho phep engine 3 (`cuc_tri`) bi quen tra lai -> ma that / AI nghien cuu duoc phep dung mo hinh lac quan;
  - o ngau nhien chay bang engine KHAC o tot nhat (so sanh khong cung thuoc do);
  - doan niem_phong bi cat o dau do, hoac so tay nghien cuu THAT (nc.db) bi ghi;
  - chuoi gia ro ri trong bo nho (`_DEM`) sau khi quet xong;
  - gop o thang vao mot ty le (cac mau cung chuoi tuong quan) thay vi gop theo chuoi;
  - khoang tin cay cua mot CHENH (co the am) bi cat o 0;
  - 'KHONG_DO_DUOC' bi dem thanh QUA / RUOT, engine 3 bi so voi engine 4;
  - quy tac doc R1 lech nguong, hoac doc nham khoa giua nguoi san xuat (tong_ket) va nguoi tieu thu (so_voi_nhieu);
  - chay tiep (resume) lam lai chuoi da xong, hoac bo qua chuoi loi;
  - mau (che_do x kieu_lot, luoi) lech khoi cac luot quet THAT cua may nha (hieu chuan do tren mot thu khac san xuat).
"""
import glob
import json
import math
import multiprocessing
import os

import numpy as np
import pandas as pd
import pytest

from nhan import doi_chung_nhieu as D
from nhan import luoi as LU
from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN
from nhan import vong_lap as VL

LAB = D.LAB
OHLC = ("open", "high", "low", "close")


# ------------------------------------------------------------------------------------------ cua nap chuoi tong hop (nc_du_lieu)

@pytest.fixture
def bo_nho(monkeypatch):
    """Bo nho chuoi / chi phi cua nc_du_lieu RIENG cho test (khong lam ban bo nho cua test khac)."""
    monkeypatch.setattr(NDL, "_DEM", {})
    monkeypatch.setattr(NDL, "_DEM_CP", {})
    return NDL


def _df_nho(n=60, cot=("open", "high", "low", "close", "spread")):
    idx = pd.date_range("2020-01-01", periods=n, freq="h")
    d = {c: np.linspace(1.0, 1.1, n) for c in cot}
    if "spread" in d:
        d["spread"] = np.full(n, 15.0)
    return pd.DataFrame(d, index=idx)


@pytest.mark.parametrize("ma", ["EURUSD", "XAUUSD", "US500CASH", "XTONG_HOP_NHIEU_1", ""])
def test_dang_ky_tu_choi_ma_that(bo_nho, ma):
    """Khong ai duoc nhet du lieu gia duoi ten mot symbol that."""
    with pytest.raises(ValueError):
        NDL.dang_ky_tong_hop(ma, "H1", _df_nho())
    assert NDL._DEM == {}


def test_dang_ky_tu_choi_chuoi_hong(bo_nho):
    with pytest.raises(ValueError):
        NDL.dang_ky_tong_hop("TONG_HOP_X_1", "H1", _df_nho(cot=("open", "high", "low", "close")))      # thieu spread
    with pytest.raises(ValueError):
        NDL.dang_ky_tong_hop("TONG_HOP_X_1", "H1", _df_nho().iloc[0:0])                                  # rong
    with pytest.raises(ValueError):
        NDL.dang_ky_tong_hop("TONG_HOP_X_1", "H1", _df_nho().iloc[::-1])                                 # chi so giam dan
    assert NDL._DEM == {}


def test_dang_ky_nap_dung_chuoi_da_dua_vao_khong_sinh_lai(bo_nho):
    """Ten `TONG_HOP_KICH_BAN_LA_7` KHONG sinh lai duoc (kich ban khong co trong KICH_BAN): `nap` chi tra duoc chuoi neu no lay tu bo nho."""
    df = _df_nho()
    NDL.dang_ky_tong_hop("tong_hop_kich_ban_la_7", "h1", df)
    assert NDL.nap("TONG_HOP_KICH_BAN_LA_7", "H1") is df
    cp = NDL.chi_phi("TONG_HOP_KICH_BAN_LA_7", df)
    assert cp.do_tin == "DO" and cp.spread_frac_chung > 0
    NDL.quen_tong_hop("TONG_HOP_KICH_BAN_LA_7")
    assert NDL._DEM == {} and NDL._DEM_CP == {}
    with pytest.raises(KeyError):
        NDL.nap("TONG_HOP_KICH_BAN_LA_7", "H1")


def test_quen_tong_hop_theo_khung_va_khong_dung_ma_khac(bo_nho):
    a, b = _df_nho(), _df_nho(80)
    NDL.dang_ky_tong_hop("TONG_HOP_A_1", "H1", a)
    NDL.dang_ky_tong_hop("TONG_HOP_A_1", "H4", b)
    NDL.dang_ky_tong_hop("TONG_HOP_B_1", "H1", a)
    NDL.chi_phi("TONG_HOP_A_1", a)
    NDL.chi_phi("TONG_HOP_B_1", a)
    NDL.quen_tong_hop("TONG_HOP_A_1", "H1")
    assert set(NDL._DEM) == {("TONG_HOP_A_1", "H4"), ("TONG_HOP_B_1", "H1")}
    NDL.quen_tong_hop("TONG_HOP_A_1")
    assert set(NDL._DEM) == {("TONG_HOP_B_1", "H1")}
    assert all(k[0] == "TONG_HOP_B_1" for k in NDL._DEM_CP)           # mo hinh chi phi cua ma khac con nguyen


# ------------------------------------------------------------------------------------------ hang so + cac chuoi gia

def test_kich_ban_nhat_quan():
    assert set(D.LOAI) == set(D.KICH_BAN)
    assert set(D.DAO_DONG) <= set(D.KICH_BAN) and set(D.HE_SO_BIEN_DONG) <= set(D.KICH_BAN)
    assert {D.LOAI[k] for k in D.DAO_DONG} == {"co_hoi_quy"}
    assert D.LOAI["NHIEU"] == "khong_co" and D.LOAI["BETA"] == "troi"
    assert set(D.MAU_TEN) == {"%s_%s" % (c, k) for c in ("mua", "ban", "hai_chieu") for k in ("phang", "cong", "nhan")}
    assert D.ENGINE_CUA == {"duong_di": 4, "cuc_tri": 3} and D.KHOP_BAR == ("duong_di", "cuc_tri")


def test_hai_engine_khop_voi_engine_that_cua_lab():
    """Neu lab doi engine (PHIEN_BAN_ENGINE 5, doi mac dinh khop_bar) thi 'engine 4' o day het dung: phai hieu chuan lai."""
    assert LU.PHIEN_BAN_ENGINE == D.ENGINE_CUA["duong_di"]
    assert LU.ThamSo().khop_bar == "duong_di"
    assert "cuc_tri" not in LU.MO_HINH_BAR_NGHIEN_CUU and "duong_di" in LU.MO_HINH_BAR_NGHIEN_CUU


def test_nguong_r1_cung_nguong_voi_vong_lap():
    """`doi_chung_nhieu` noi 'cung y nghia voi vong_lap': doi mot ben ma khong doi ben kia la pha phep so sanh."""
    assert D.NHIEU_CHENH_TOI_THIEU == VL.SO_SANH_CHENH_TOI_THIEU


def test_mau_khop_tung_luot_quet_san_xuat_cua_may_nha():
    """Cac luot quet 3.000 o THAT (viec/cho + viec/xong) phai dung la mot trong 9 mau; neu may nha doi luoi thi hieu chuan het dung."""
    kiem = 0
    sai = []
    for thu_muc in ("cho", "xong"):
        for f in glob.glob(str(LAB / "viec" / thu_muc / "*.json")):                  # don san xuat dat ten kieu 220165-AUDCHF-M30-ba-nh6, khong co 'quet-luoi'
            try:
                d = json.loads(open(f, encoding="utf-8").read())
            except (OSError, ValueError):
                continue
            lenh = d.get("lenh") if isinstance(d.get("lenh"), list) else (d.get("bang_chung") or {}).get("lenh")
            if not isinstance(lenh, list) or "quet_luoi" not in lenh:
                continue
            try:
                j = json.loads(lenh[lenh.index("quet_luoi") + 1])
            except (ValueError, IndexError):
                continue
            if j.get("toi_da_o") != 3000:
                continue
            kiem += 1
            if not any(j.get("co_dinh") == c and j.get("luoi") == g for c, g in D.MAU.values()):
                sai.append(os.path.basename(f))
    if kiem == 0:
        pytest.skip("khong co luot quet 3.000 o nao trong viec/")
    assert not sai, "%d/%d luot quet san xuat KHONG khop 9 mau cua doi_chung_nhieu (vd %s): cap nhat MAU roi chay lai hieu chuan" % (
        len(sai), kiem, sai[:3])


def test_sinh_dao_dong_hinh_dang_va_tat_dinh():
    a = D.sinh_dao_dong(3, so_bar=2000, nua_doi=48.0, q=0.6)
    b = D.sinh_dao_dong(3, so_bar=2000, nua_doi=48.0, q=0.6)
    c = D.sinh_dao_dong(4, so_bar=2000, nua_doi=48.0, q=0.6)
    pd.testing.assert_frame_equal(a, b)
    assert not np.allclose(a["close"], c["close"])
    assert len(a) == 2000 and a.index.is_monotonic_increasing
    assert (a["high"] >= a[["open", "close"]].max(axis=1) - 1e-12).all()
    assert (a["low"] <= a[["open", "close"]].min(axis=1) + 1e-12).all()
    assert a["spread"].between(8, 30).all()
    assert a["open"].iloc[0] == pytest.approx(1.0)
    np.testing.assert_allclose(a["open"].iloc[1:].to_numpy(), a["close"].iloc[:-1].to_numpy())      # khong co khe gia giua hai bar
    assert a.attrs["tong_hop"]["nua_doi"] == 48.0 and a.attrs["tong_hop"]["q"] == 0.6


def test_sinh_dao_dong_hat_gieo_theo_ten_kich_ban():
    a = D.sinh_dao_dong(1, 500, 48.0, 0.6, ten="DAO_DONG")
    b = D.sinh_dao_dong(1, 500, 48.0, 0.6, ten="DAO_DONG_KHAC")
    assert not np.allclose(a["close"], b["close"])           # cung tham so, cung hat, khac ten: hai kich ban khong dung chung nhieu


def _vr(kb, k, hats=range(1, 9), so_bar=20000):
    return float(np.mean([D.ty_so_phuong_sai(D.sinh_chuoi(kb, h, so_bar)["close"].to_numpy(), k) for h in hats]))


def test_dao_dong_that_su_hoi_quy_o_chan_dai():
    """Dap an cua phep do: co thanh phan hoi quy THAT. Do bang variance ratio o chan dai (VR48 mot minh khong du nhay voi nua doi 288).
    Do 10/10 (20 chuoi x 20.000 bar): DAO_DONG VR48 0,82 VR288 0,53; DAO_DONG_YEU VR288 0,87; DAO_DONG_RAT_YEU VR288 0,96."""
    vr288, vr48 = _vr("DAO_DONG", 288), _vr("DAO_DONG", 48)
    assert vr288 < 0.8 and vr48 < 0.95 and vr288 < vr48            # ca hai < 1 va hoi quy manh hon o chan dai
    assert _vr("DAO_DONG_YEU", 288) < 0.98                          # yeu hon nhung van nghieng ve hoi quy
    rng = np.random.default_rng(5)
    di_bo = np.exp(np.cumsum(rng.normal(0.0, 0.001, 200000)))
    assert 0.8 < D.ty_so_phuong_sai(di_bo, 288) < 1.2             # thuoc do khong lech: di bo ngau nhien ~ 1


def test_doi_bien_dong_nhan_log_gia_va_giu_thu_tu():
    df = NDL.tong_hop("NHIEU", hat=2, so_bar=1500, khung="H1")
    goc = df.copy()
    x = D.doi_bien_dong(df, 0.65)
    p0 = float(df["open"].iloc[0])
    for c in OHLC:
        np.testing.assert_allclose(np.log(x[c].to_numpy() / p0), 0.65 * np.log(df[c].to_numpy() / p0), atol=1e-9)
    assert (x["high"] >= x[["open", "close"]].max(axis=1)).all() and (x["low"] <= x[["open", "close"]].min(axis=1)).all()
    pd.testing.assert_series_equal(x["spread"], df["spread"])
    pd.testing.assert_frame_equal(df, goc)                          # khong sua chuoi goc
    assert x.attrs["he_so_bien_dong"] == 0.65


def test_sinh_chuoi_moi_kich_ban_va_cap_thap_cao_chung_duong_gia():
    ra = {kb: D.sinh_chuoi(kb, 3, 1500) for kb in D.KICH_BAN}
    for kb, df in ra.items():
        assert len(df) == 1500 and {"open", "high", "low", "close", "spread"} <= set(df.columns), kb
        assert df.index.is_monotonic_increasing and np.isfinite(df[list(OHLC)].to_numpy()).all(), kb
    p0 = float(ra["NHIEU"]["open"].iloc[0])
    for kb, he in (("NHIEU_THAP", 0.65), ("NHIEU_CAO", 1.35)):         # cung duong gia voi NHIEU (ghep cap), chi doi bien dong
        np.testing.assert_allclose(np.log(ra[kb]["close"].to_numpy() / p0), he * np.log(ra["NHIEU"]["close"].to_numpy() / p0), atol=1e-9)
    pd.testing.assert_frame_equal(ra["NHIEU"], NDL.tong_hop("NHIEU", hat=3, so_bar=1500, khung="H1"))
    with pytest.raises(KeyError):
        D.sinh_chuoi("KHONG_CO", 1, 100)
    assert D.ten_chuoi("nhieu", 7) == "TONG_HOP_NHIEU_7" and NDL.la_tong_hop(D.ten_chuoi("DAO_DONG_YEU", 1))


def test_ty_so_phuong_sai_dung_cong_thuc():
    a = 0.01
    xen_ke = np.exp(np.cumsum([a, -a] * 500))                # moi cap bar triet tieu nhau: VR(2) = 0 chinh xac
    assert D.ty_so_phuong_sai(xen_ke, 2) == pytest.approx(0.0, abs=1e-12)
    rng = np.random.default_rng(11)
    r = np.zeros(50000)
    e = rng.normal(0.0, 0.001, 50000)
    for t in range(1, 50000):
        r[t] = 0.5 * r[t - 1] + e[t]                         # quan tinh duong -> VR > 1
    assert D.ty_so_phuong_sai(np.exp(np.cumsum(r)), 12) > 1.5
    iid = np.exp(np.cumsum(rng.normal(0.0, 0.001, 60000)))
    assert abs(D.ty_so_phuong_sai(iid, 12) - 1.0) < 0.08


# ------------------------------------------------------------------------------------------ mat nap + thuoc do gia (khong cham engine that)

class _TNGia:
    """Thay `nc_thi_nghiem`: ghi lai moi loi goi, tra ket qua da dan."""
    LENH_TOI_THIEU = 10

    def __init__(self, quet=None, danh_gia=None, o_luoi=None):
        self.quet, self.danh_gia, self.o_luoi = quet, danh_gia, o_luoi
        self.goi_quet, self.goi_dg, self.goi_o = [], [], []

    def quet_luoi(self, ma, khung, co_dinh, luoi, von, toi_da_o=0):
        self.goi_quet.append({"ma": ma, "khung": khung, "co_dinh": dict(co_dinh), "luoi": luoi, "von": von, "toi_da_o": toi_da_o})
        return self.quet(co_dinh, luoi) if callable(self.quet) else self.quet

    def danh_gia_luoi(self, ma, khung, ts, doan, von):
        self.goi_dg.append((ma, khung, dict(ts), doan, von))
        return self.danh_gia(ts) if callable(self.danh_gia) else self.danh_gia

    def _o_luoi(self, dl, co_dinh, o, von_q, moc):
        self.goi_o.append((dl, dict(co_dinh), dict(o), von_q, moc))
        return self.o_luoi(dl, o, moc)


def _dg(trang_thai="DAT", ln=4.0, dd=-12.0, o_tran=9.0, hon_moc=2.0, so_lenh=40, ly_do=None):
    return {"trang_thai": trang_thai, "ly_do": ly_do, "lenh": {"so_lenh": so_lenh},
            "tien": {"loi_suat_nam_pct": ln, "maxdd_pct": dd, "loi_suat_o_tran_pct": o_tran, "hon_moc_pct": hon_moc}}


def test_kl_chi_dat_la_qua_am_la_ruot_con_lai_khong_do_duoc():
    assert D._kl("DAT") == "QUA" and D._kl("AM") == "RUOT"
    for x in ("CHUA_DO_DUOC", "LOI", None, "dat", ""):
        assert D._kl(x) == "KHONG_DO_DUOC"


def test_xn_dung_doan_xac_nhan_va_anh_xa_truong():
    tn = _TNGia(danh_gia=_dg())
    r = D._xn(tn, "TONG_HOP_NHIEU_1", "H1", {"buoc": 20})
    assert tn.goi_dg == [("TONG_HOP_NHIEU_1", "H1", {"buoc": 20}, "xac_nhan", D.VON)]          # KHONG BAO GIO doan khac
    assert r == {"kl": "QUA", "ln": 4.0, "dd": -12.0, "o_tran": 9.0, "hon_moc": 2.0, "so_lenh": 40, "chay": False}
    tn2 = _TNGia(danh_gia=_dg("AM", ln=-30.0, ly_do="CHAY TAI KHOAN o ngay 12"))
    r2 = D._xn(tn2, "M", "H1", {})
    assert r2["kl"] == "RUOT" and r2["chay"] is True and "ly_do" not in r2
    tn3 = _TNGia(danh_gia={"trang_thai": "CHUA_DO_DUOC", "ly_do": "x" * 300})
    r3 = D._xn(tn3, "M", "H1", {})
    assert r3["kl"] == "KHONG_DO_DUOC" and len(r3["ly_do"]) == 100 and r3["ln"] is None and r3["chay"] is False


def _o(co_lai=True, so_lenh=50, ln=5.0, chay=False, hon_moc=None, loi=None):
    if loi:
        return {"tham_so": {}, "loi": loi}
    return {"co_lai": co_lai, "so_lenh": so_lenh, "loi_suat_nam_pct": ln, "chay": chay, "hon_moc_pct": hon_moc}


def _cd1(trong, ngoai, so_o=5, luoi=None):
    """`_chan_doan` voi luoi 1 o: mot o duy nhat nen moi lan boc ra cung ket qua, dem duoc chinh xac."""
    tn = _TNGia(o_luoi=lambda dl, o, moc: trong if moc == 0.0 else ngoai)
    return D._chan_doan(tn, luoi or {"buoc": [10]}, {"che_do": "mua"}, "IS", "OOS", 100.0, 3.5, so_o, 1), tn


def test_chan_doan_phan_loai_tung_nhanh():
    b, tn = _cd1(_o(True, 50), _o(True, 50, ln=5.0, hon_moc=2.0))
    assert b["bang"]["lai"] == [5, 0, 0, 5] and b["loi"] == 0 and b["so_o"] == 5
    assert all(g[0] == "IS" if g[4] == 0.0 else g[0] == "OOS" for g in tn.goi_o)                  # trong mau: moc 0, ngoai mau: moc cua doan
    assert sorted({g[4] for g in tn.goi_o}) == [0.0, 3.5] and all(g[3] == 100.0 for g in tn.goi_o)
    assert _cd1(_o(True), _o(True, ln=5.0, hon_moc=-1.0))[0]["bang"]["lai"] == [5, 0, 0, 0]       # qua nhung khong hon moc
    assert _cd1(_o(True), _o(True, ln=5.0, hon_moc=None))[0]["bang"]["lai"] == [5, 0, 0, 0]
    assert _cd1(_o(True), _o(True, ln=5.0, chay=True))[0]["bang"]["lai"] == [0, 5, 0, 0]           # chay tai khoan thang lai: van RUOT
    assert _cd1(_o(False), _o(True, ln=0.0))[0]["bang"]["khong_lai"] == [0, 5, 0, 0]               # lai == 0 khong phai QUA (nghiem ngat > 0)
    assert _cd1(_o(False), _o(True, ln=-1.0))[0]["bang"]["khong_lai"] == [0, 5, 0, 0]
    assert _cd1(_o(False), _o(True, so_lenh=3, ln=9.0))[0]["bang"]["khong_lai"] == [0, 0, 5, 0]    # it lenh: khong do duoc du lai


def test_chan_doan_trong_mau_it_lenh_va_o_loi():
    b, _ = _cd1(_o(True, so_lenh=4), _o(True, ln=5.0))
    assert b["bang"]["khong_do_duoc"] == [5, 0, 0, 0] and b["bang"]["lai"] == [0, 0, 0, 0]        # trong mau < LENH_TOI_THIEU: khong tinh la lai
    b, _ = _cd1(_o(loi="ValueError: x"), _o(True))
    assert b["loi"] == 5 and sum(sum(v) for v in b["bang"].values()) == 0
    b, _ = _cd1(_o(True), _o(loi="ValueError: y"))
    assert b["loi"] == 5 and sum(sum(v) for v in b["bang"].values()) == 0


def test_chan_doan_tat_dinh_theo_hat_va_tong_o_khop():
    luoi = {"buoc": [1, 2, 3, 4, 5, 6, 7, 8], "tp": [10, 20, 30]}
    def o_luoi(dl, o, moc):
        return _o(co_lai=o["buoc"] % 2 == 0, ln=float(o["tp"] - 15), so_lenh=50, hon_moc=1.0)
    ket = []
    for hat in (1, 1, 2):
        tn = _TNGia(o_luoi=o_luoi)
        ket.append(D._chan_doan(tn, luoi, {}, "IS", "OOS", 1.0, 0.0, 60, hat))
    assert ket[0] == ket[1] and ket[0]["bang"] != ket[2]["bang"]
    for k in ket:
        assert sum(k["bang"][h][j] for h in k["bang"] for j in range(3)) + k["loi"] == k["so_o"] == 60
        assert all(k["bang"][h][3] <= k["bang"][h][0] for h in k["bang"])


def _quet_gia(hinh="CAO_NGUYEN", tot=True, ly_do=None):
    def f(co_dinh, luoi):
        if hinh is None:
            return {"hinh_dang": None, "ly_do": ly_do or "x"}
        ts = dict(co_dinh, **{k: v[0] for k, v in luoi.items()})
        return {"hinh_dang": hinh, "so_o": 40, "so_o_do_duoc": 40, "so_o_chay_tai_khoan": 1, "ty_le_o_co_lai": 0.8,
                "hang_xom": {"ty_le_co_lai": 0.7},
                "o_tot_nhat": {"loi_suat_o_tran_pct": 12.0, "loi_suat_nam_pct": 9.0} if tot else None,
                "tham_so_day_du": ts if tot else None}
    return f


_NGU_CANH = {"dl_is": "IS", "dl_oos": "OOS", "von_q": 100.0, "moc_oos": 3.5}


def _tn_mau(**kw):
    return _TNGia(quet=_quet_gia(**kw), danh_gia=_dg(), o_luoi=lambda dl, o, moc: _o(True))


def test_chay_mau_engine4_khong_them_khop_bar_va_khong_sua_mau():
    tn = _tn_mau()
    goc = json.dumps(D.MAU["mua_phang"], sort_keys=True)
    r = D._chay_mau(tn, VL, "TONG_HOP_NHIEU_1", "H1", "mua_phang", "duong_di", 77, 8, _NGU_CANH, 1)
    q = tn.goi_quet[0]
    assert "khop_bar" not in q["co_dinh"] and q["toi_da_o"] == 77 and q["von"] == D.VON and q["khung"] == "H1"
    assert q["luoi"] == D.MAU["mua_phang"][1] and q["luoi"] is not D.MAU["mua_phang"][1]
    assert json.dumps(D.MAU["mua_phang"], sort_keys=True) == goc
    assert r["hinh"] == "CAO_NGUYEN" and r["xn_tot"]["kl"] == "QUA" and r["xn_ngau"]["kl"] == "QUA"
    assert set(r["tot"]["tham_so"]) == set(D.MAU["mua_phang"][1]) and r["chan_doan"]["so_o"] == 8
    (_, _, ts_tot, doan1, _), (_, _, ts_ngau, doan2, _) = tn.goi_dg
    assert doan1 == doan2 == "xac_nhan" and ts_tot != ts_ngau                    # o ngau KHAC o tot nhat, cung luoi
    assert set(ts_ngau) == set(ts_tot) and ts_ngau["che_do"] == ts_tot["che_do"] == "mua"


def test_chay_mau_engine3_tat_ca_o_deu_cuc_tri_va_mau_goc_khong_nhiem():
    tn = _tn_mau()
    r = D._chay_mau(tn, VL, "TONG_HOP_NHIEU_1", "H1", "ban_nhan", "cuc_tri", 50, 6, _NGU_CANH, 1)
    assert tn.goi_quet[0]["co_dinh"]["khop_bar"] == "cuc_tri"
    assert {g[2]["khop_bar"] for g in tn.goi_dg} == {"cuc_tri"} and len(tn.goi_dg) == 2          # o tot nhat VA o ngau cung engine 3
    assert {g[1]["khop_bar"] for g in tn.goi_o} == {"cuc_tri"} and len(tn.goi_o) == 12            # 6 o chan doan x (trong mau + ngoai mau)
    assert "khop_bar" not in D.MAU["ban_nhan"][0]                                                  # mau dung chung khong bi nhiem khop_bar
    assert r["hinh"] == "CAO_NGUYEN"


def test_chay_mau_khong_hinh_dang_hoac_khong_o_tot_nhat():
    tn = _tn_mau(hinh=None, ly_do="y" * 400)
    r = D._chay_mau(tn, VL, "M", "H1", "mua_phang", "duong_di", 10, 4, _NGU_CANH, 1)
    assert r["hinh"] == "CHUA_DO_DUOC" and len(r["ly_do"]) == 140
    assert "xn_tot" not in r and "chan_doan" not in r and tn.goi_dg == [] and tn.goi_o == []
    tn = _tn_mau(hinh="KHONG_CO_LAI", tot=False)
    r = D._chay_mau(tn, VL, "M", "H1", "ban_phang", "duong_di", 10, 4, _NGU_CANH, 1)
    assert r["hinh"] == "KHONG_CO_LAI" and "xn_tot" not in r and "xn_ngau" not in r and "chan_doan" in r and tn.goi_dg == []


# ------------------------------------------------------------------------------------------ MOT chuoi that, qua duong ong that (nho)

@pytest.fixture
def co_lap(tmp_path, monkeypatch):
    """So tay / bo nho / quy cach RIENG; ghi lai moi doan bi cat + mo hinh bar cua moi o duoc chay."""
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    monkeypatch.setattr(TN, "_DEM_MOC", {})
    monkeypatch.setattr(LU, "FILE_QUY_CACH", tmp_path / "luoi_quy_cach.json")
    monkeypatch.setattr(NDL, "_DEM", {})
    monkeypatch.setattr(NDL, "_DEM_CP", {})
    monkeypatch.setenv("NC_QUET_LUONG", "1")
    st = {"doan": [], "khop_bar": set(), "guard_khi_quet": [], "tmp": tmp_path}
    cat_goc, chay_goc, quet_goc = NDL.cat_doan, LU.chay_mang, TN.quet_luoi

    def cat(df, doan, _giay_phep=False):
        st["doan"].append((doan, bool(_giay_phep)))
        return cat_goc(df, doan, _giay_phep)

    def chay(dl, ts, von, ghi_lenh=False):
        st["khop_bar"].add(ts.khop_bar)
        return chay_goc(dl, ts, von, ghi_lenh)

    def quet(*a, **k):
        st["guard_khi_quet"].append(TN._loi_mo_hinh_bar("cuc_tri") is None)          # cong dang MO luc quet?
        return quet_goc(*a, **k)

    monkeypatch.setattr(NDL, "cat_doan", cat)
    monkeypatch.setattr(LU, "chay_mang", chay)
    monkeypatch.setattr(TN, "quet_luoi", quet)
    return st


def _trang_thai_nc_db_that():
    p = LAB / "nc.db"
    return (p.exists(), p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else (False, 0, 0)


NHO = dict(toi_da_o=24, so_o_cd=8, so_bar=12000)


def _bo_thoi_gian(r):
    r = json.loads(json.dumps(r))
    for k in ("giay", "giay_sinh_chuoi"):
        r.pop(k, None)
    for m in r["mau"].values():
        m.pop("giay_quet", None)
    return r


@pytest.mark.cham
def test_chay_chuoi_engine4_ban_ghi_day_du_khong_cham_niem_phong_khong_ro_ri(co_lap):
    that_truoc = _trang_thai_nc_db_that()
    r = D.chay_chuoi("NHIEU", 1, "duong_di", **NHO)
    assert r["engine"] == 4 and r["khop_bar"] == "duong_di" and r["ma"] == "TONG_HOP_NHIEU_1" and r["v"] == D.PHIEN_BAN
    assert set(r["mau"]) == set(D.MAU_TEN) and set(r["vr"]) == {str(k) for k in D.CHAN_VR}
    assert all(isinstance(r[k], float) for k in ("troi_is_pct", "troi_oos_pct", "moc_oos_pct"))
    assert {d for d, _ in co_lap["doan"]} == {"kham_pha", "xac_nhan"} and not any(g for _, g in co_lap["doan"])       # KHONG BAO GIO niem_phong
    assert co_lap["khop_bar"] == {"duong_di"}                                                                           # moi o chay engine 4
    assert co_lap["guard_khi_quet"] and not any(co_lap["guard_khi_quet"])                                                # cong KHONG mo o engine 4
    assert not [k for k in NDL._DEM if k[0].startswith("TONG_HOP_NHIEU_1")] and not NDL._DEM_CP                        # chuoi da bi quen
    assert _trang_thai_nc_db_that() == that_truoc and (co_lap["tmp"] / "nc.db").exists()                                # so tay THAT nguyen, so tam co ghi
    for ten, m in r["mau"].items():
        assert m["hinh"] in ("CAO_NGUYEN", "CAI_GAI", "HON_HOP", "KHONG_CO_LAI", "CHUA_DO_DUOC"), ten
        if "xn_tot" in m:
            assert m["xn_tot"]["kl"] in ("QUA", "RUOT", "KHONG_DO_DUOC") and set(m["tot"]["tham_so"]) == set(D.MAU[ten][1])
        if "chan_doan" in m:
            cd = m["chan_doan"]
            assert sum(cd["bang"][h][j] for h in cd["bang"] for j in range(3)) + cd["loi"] == cd["so_o"] == NHO["so_o_cd"]
    assert any("xn_tot" in m for m in r["mau"].values())                      # it nhat mot mau co o tot nhat de kiem (neu khong, test vo nghia)
    json.dumps(r)                                                              # ban ghi ghi duoc ra jsonl


@pytest.mark.cham
def test_chay_chuoi_engine3_mo_cong_chi_luc_chay_roi_dong_lai(co_lap):
    goc = TN._loi_mo_hinh_bar
    assert goc("cuc_tri") is not None                                           # truoc: duong nghien cuu TU CHOI cuc_tri
    r = D.chay_chuoi("NHIEU", 1, "cuc_tri", mau_ten=("mua_phang", "hai_chieu_cong"), **NHO)
    assert r["engine"] == 3 and r["khop_bar"] == "cuc_tri" and set(r["mau"]) == {"mua_phang", "hai_chieu_cong"}
    assert co_lap["khop_bar"] == {"cuc_tri"}                                    # CA o tot nhat, o ngau, o chan doan deu engine 3
    assert co_lap["guard_khi_quet"] and all(co_lap["guard_khi_quet"])           # cong mo trong luc quet
    assert TN._loi_mo_hinh_bar is goc and goc("cuc_tri") is not None            # sau: dong lai
    assert not NDL._DEM and not NDL._DEM_CP


@pytest.mark.cham
def test_chay_chuoi_tai_lap_duoc_cung_hat_cung_ket_qua(co_lap, monkeypatch):
    a = _bo_thoi_gian(D.chay_chuoi("NHIEU", 2, "duong_di", mau_ten=("mua_phang", "ban_cong"), **NHO))
    monkeypatch.setattr(ST, "DB", co_lap["tmp"] / "nc_khac.db")                 # so tay khac: khong an cache
    monkeypatch.setattr(TN, "_DEM_MOC", {})
    b = _bo_thoi_gian(D.chay_chuoi("NHIEU", 2, "duong_di", mau_ten=("mua_phang", "ban_cong"), **NHO))
    assert a == b


def test_chay_chuoi_loi_van_tra_cong_va_quen_chuoi(co_lap):
    goc = TN._loi_mo_hinh_bar
    with pytest.raises(KeyError):
        D.chay_chuoi("NHIEU", 3, "cuc_tri", mau_ten=("khong_co_mau_nay",), toi_da_o=10, so_o_cd=2, so_bar=3000)
    assert TN._loi_mo_hinh_bar is goc and goc("cuc_tri") is not None
    assert not NDL._DEM and not NDL._DEM_CP


def test_chay_chuoi_tu_choi_khop_bar_la_truoc_khi_sinh_gi(co_lap):
    with pytest.raises(ValueError):
        D.chay_chuoi("NHIEU", 1, "ngau_nhien", toi_da_o=10, so_o_cd=2, so_bar=3000)
    assert co_lap["doan"] == [] and not NDL._DEM


# ------------------------------------------------------------------------------------------ tong ket (nguoi san xuat)

def _muc(hinh="CAO_NGUYEN", tot="QUA", ngau=None, hon_moc=None, o_tran=5.0, ty_le=0.7, cd=None):
    m = {"hinh": hinh, "so_o": 100, "so_o_do_duoc": 100, "ty_le_o_co_lai": ty_le}
    if hinh == "CHUA_DO_DUOC":
        return m
    if tot is not None:
        m["tot"] = {"tham_so": {}, "o_tran_trong_mau": 12.0, "ln_trong_mau": 9.0}
        m["xn_tot"] = {"kl": tot, "ln": 3.0, "dd": -10.0, "o_tran": o_tran, "hon_moc": hon_moc, "so_lenh": 40, "chay": False}
    if ngau is not None:
        m["xn_ngau"] = {"kl": ngau, "ln": 1.0, "dd": -10.0, "o_tran": 1.0, "hon_moc": None, "so_lenh": 40, "chay": False}
    if cd:
        m["chan_doan"] = cd
    return m


def _dong(mau, kb="NHIEU", hat=1, khop_bar="duong_di", so_bar=D.SO_BAR, toi_da_o=D.TOI_DA_O, troi_oos=1.0, v=D.PHIEN_BAN):
    return {"v": v, "kb": kb, "hat": hat, "khop_bar": khop_bar, "engine": D.ENGINE_CUA[khop_bar], "ma": D.ten_chuoi(kb, hat),
            "so_bar": so_bar, "toi_da_o": toi_da_o, "troi_is_pct": 1.0, "troi_oos_pct": troi_oos, "moc_oos_pct": 2.0,
            "vr": {str(k): 1.0 for k in D.CHAN_VR}, "mau": mau, "giay": 1.0}


def test_tb_ci_chenh_am_khong_bi_cat_o_0():
    ci = D._tb_ci([-0.20, -0.30, -0.25, -0.22], (-1.0, 1.0))
    assert ci["tb"] < 0 and ci["ci95"][0] < ci["ci95"][1] < 0                  # khoang tin cay cua chenh am phai nam o phia am
    assert D._tb_ci([0.1, 0.9]) ["ci95"][0] >= 0.0 and D._tb_ci([0.1, 0.9])["ci95"][1] <= 1.0
    assert D._tb_ci([])["tb"] is None and D._tb_ci([0.5])["ci95"] is None and D._tb_ci([0.5])["n_chuoi"] == 1


def test_gop_theo_chuoi_khong_gop_o_thang():
    """Chuoi A: 3 mau deu QUA; chuoi B: 1 mau RUOT. Gop theo chuoi = (1 + 0)/2; gop o thang se ra 3/4."""
    dong = [_dong({"mua_phang": _muc(), "mua_cong": _muc(), "ban_phang": _muc()}, hat=1),
            _dong({"mua_phang": _muc(tot="RUOT")}, hat=2)]
    tk = D.tong_ket(dong)
    g = tk["kich_ban"]["NHIEU@e4"]["gop"]["qua_o_tot_nhat"]
    assert g["tb"] == 0.5 and g["n_chuoi"] == 2


def test_tong_ket_con_so_gop_tren_vi_du_tay():
    dong = [
        _dong({"mua_phang": _muc(hon_moc=1.0, ngau="RUOT"), "mua_cong": _muc(hon_moc=-1.0, ngau="QUA"), "ban_phang": _muc(ngau="QUA")},
              hat=1, troi_oos=5.0),
        _dong({"mua_phang": _muc(tot="RUOT", ngau="RUOT")}, hat=2, troi_oos=-3.0),
        _dong({"mua_phang": _muc(hinh="CAI_GAI", tot="KHONG_DO_DUOC"), "mua_cong": _muc(hinh="CHUA_DO_DUOC")}, hat=3, troi_oos=0.0),
    ]
    tk = D.tong_ket(dong)
    k = tk["kich_ban"]["NHIEU@e4"]
    g = k["gop"]
    assert k["so_chuoi"] == 3 and k["engine"] == 4 and k["loai"] == "khong_co"
    assert g["qua_o_tot_nhat"]["tb"] == 0.5 and g["qua_o_tot_nhat"]["n_chuoi"] == 2                 # chuoi 3 toan KHONG_DO_DUOC: khong dong gop
    assert g["qua_cao_nguyen"]["tb"] == 0.5
    assert g["qua_hon_moc_o_tot_nhat"]["tb"] == pytest.approx((1 / 3 + 0.0) / 2, abs=1e-4)          # QUA nhung hon_moc <= 0 / None khong tinh
    assert g["qua_o_ngau"]["tb"] == pytest.approx((2 / 3 + 0.0) / 2, abs=1e-4) and g["qua_o_ngau"]["n_chuoi"] == 2
    assert g["ty_le_cao_nguyen"]["tb"] == pytest.approx(2 / 3, abs=1e-4) and g["ty_le_cao_nguyen"]["n_chuoi"] == 3      # CHUA_DO_DUOC bi bo
    assert k["troi_oos_pct_tb"] == pytest.approx((5.0 - 3.0 + 0.0) / 3, abs=0.01)
    m = k["mau"]["mua_phang"]
    assert (m["cao"]["n"], m["cao"]["qua"], m["cao"]["ty_le"]) == (2, 1, 0.5)
    assert (m["doi"]["n"], m["doi"]["khong_do_duoc"]) == (0, 1)                                       # CAI_GAI KHONG_DO_DUOC: khong la RUOT
    assert (m["ngau_cua_cao"]["n"], m["ngau_cua_cao"]["qua"]) == (2, 0) and m["n_chuoi"] == 3 and m["n_do_duoc"] == 3
    assert m["cao_theo_huong_ngoai_mau"]["oos_tang"]["n"] == 1 and m["cao_theo_huong_ngoai_mau"]["oos_giam"]["n"] == 1
    cn = m["so_sanh"]["cao_vs_ngau"]
    assert cn["cap"] == 2 and cn["cao_qua_ngau_ruot"] == 1 and cn["ca_hai_ruot"] == 1 and cn["ket_luan"] == "CHUA_DU"
    assert m["so_sanh"]["cao_vs_doi"]["ket_luan"] == "CHUA_DU"


def test_tong_ket_tach_engine_tach_cau_hinh_va_bo_chuoi_loi():
    cao = lambda: {"mua_phang": _muc()}
    dong = [_dong(cao(), hat=1), _dong(cao(), hat=2), _dong(cao(), hat=1, khop_bar="cuc_tri"),
            _dong(cao(), hat=3, so_bar=9999),                                  # cau hinh khac so voi da so
            {"v": D.PHIEN_BAN, "kb": "NHIEU", "hat": 9, "khop_bar": "duong_di", "loi": "RuntimeError: x", "mau": {}}]
    tk = D.tong_ket(dong)
    assert set(tk["kich_ban"]) == {"NHIEU@e3", "NHIEU@e4"}
    assert tk["kich_ban"]["NHIEU@e4"]["so_chuoi"] == 2 and tk["kich_ban"]["NHIEU@e3"]["so_chuoi"] == 1
    assert tk["kich_ban"]["NHIEU@e3"]["engine"] == 3 and tk["kich_ban"]["NHIEU@e3"]["khop_bar"] == "cuc_tri"
    assert tk["so_chuoi_hong"] == 1 and tk["so_chuoi_khac_cau_hinh"] == 1
    assert tk["cau_hinh"] == {"v": D.PHIEN_BAN, "so_bar": D.SO_BAR, "toi_da_o": D.TOI_DA_O}
    assert D.tong_ket([]) == {"phien_ban": D.PHIEN_BAN, "khung": D.KHUNG, "cau_hinh": None, "so_chuoi_hong": 0,
                              "so_chuoi_khac_cau_hinh": 0, "kich_ban": {}, "tom_tat": []}


def test_chan_doan_gop_theo_chuoi_va_chenh_am():
    def cd(lai, khong_lai):
        return {"bang": {"lai": lai, "khong_lai": khong_lai, "khong_do_duoc": [0, 0, 0, 0]}, "loi": 0,
                "so_o": sum(lai[:3]) + sum(khong_lai[:3])}
    muc = [_muc(cd=cd([6, 4, 0, 3], [3, 7, 0, 1])), _muc(cd=cd([2, 8, 0, 0], [2, 8, 0, 0])),
           _muc(cd=cd([1, 1, 0, 0], [1, 1, 0, 0]))]                            # chuoi 3: < 5 o moi nhom, < 10 o: bo
    r = D._chan_doan_gop(muc)
    assert r["qua_moi_o"]["n_chuoi"] == 2 and r["qua_moi_o"]["tb"] == pytest.approx((9 / 20 + 4 / 20) / 2, abs=1e-4)
    assert r["qua_hon_moc_moi_o"]["tb"] == pytest.approx((4 / 20 + 0.0) / 2, abs=1e-4)
    assert r["qua_neu_co_lai_trong_mau"]["tb"] == pytest.approx((0.6 + 0.2) / 2, abs=1e-4)
    assert r["qua_neu_khong_lai_trong_mau"]["tb"] == pytest.approx((0.3 + 0.2) / 2, abs=1e-4)
    assert r["chenh_co_lai_tru_khong_lai"]["tb"] == pytest.approx((0.3 + 0.0) / 2, abs=1e-4)
    assert D._chan_doan_gop([_muc(), _muc(hinh="KHONG_CO_LAI", tot=None)]) is None
    am = D._chan_doan_gop([_muc(cd=cd([1, 9, 0, 0], [6, 4, 0, 0])), _muc(cd=cd([0, 10, 0, 0], [5, 5, 0, 0])),
                           _muc(cd=cd([2, 8, 0, 0], [7, 3, 0, 0]))])           # 'co lai' trong mau KEM hon 'khong lai': chenh am
    ci = am["chenh_co_lai_tru_khong_lai"]
    assert ci["tb"] < 0 and ci["ci95"][1] < 0


def test_tom_tat_loi_thuong_la_ascii_va_chi_ve_nhieu_va_hoi_quy():
    dong = [_dong({"mua_phang": _muc(hon_moc=1.0), "ban_phang": _muc(tot="RUOT")}, kb="NHIEU", hat=h) for h in (1, 2)]
    dong += [_dong({"mua_phang": _muc()}, kb="DAO_DONG", hat=1), _dong({"mua_phang": _muc()}, kb="BETA", hat=1)]
    ts = D.tong_ket(dong)["tom_tat"]
    assert len(ts) == 2 and ts[0].startswith("NHIEU@e4 (2 chuoi gia chi co nhieu, engine 4)") and "DAO_DONG@e4" in ts[1]
    assert all(s.isascii() for s in ts) and "50%" in ts[0]


# ------------------------------------------------------------------------------------------ quy tac doc R1 (nguoi tieu thu)

def _tham_chieu(qua_tren_40, engine=4, hon_moc_qua=None):
    """40 chuoi NHIEU, moi chuoi mot mau 'mua_phang' CAO_NGUYEN, `qua_tren_40` chuoi QUA -> tham chieu that do `tong_ket` sinh."""
    hm = qua_tren_40 if hon_moc_qua is None else hon_moc_qua
    dong = [_dong({"mua_phang": _muc(tot="QUA" if i < qua_tren_40 else "RUOT", hon_moc=1.0 if i < hm else -1.0)},
                  hat=i + 1, khop_bar="duong_di" if engine == 4 else "cuc_tri") for i in range(40)]
    return D.tong_ket(dong)


def test_r1_dung_khoa_cua_nguoi_san_xuat_gop_va_theo_mau():
    tc = _tham_chieu(20)
    for mau in (None, "mua_phang"):
        r = D.so_voi_nhieu(45, 50, tc, 4, mau=mau)
        assert r["ket_luan"] == "VUOT_NHIEU" and r["engine"] == 4 and r["nhieu"] == 0.5 and r["n_chuoi_nhieu"] == 40, mau
        assert r["thuc"] == 0.9 and r["khoang_thuc"] == VL.khoang_wilson(45, 50) and r["khoang_nhieu"][0] < 0.5 < r["khoang_nhieu"][1]
        assert D.so_voi_nhieu(25, 50, tc, 4, mau=mau)["ket_luan"] == "NGANG_NHIEU"
        assert D.so_voi_nhieu(5, 50, tc, 4, mau=mau)["ket_luan"] == "DUOI_NHIEU"
    assert D.so_voi_nhieu(45, 50, tc, 4, mau="ban_phang")["ket_luan"] == "CHUA_DU"                  # mau chua co trong tham chieu


def test_r1_phai_tach_hai_dieu_kien_khoang_tin_cay_va_chenh_toi_thieu():
    tc = _tham_chieu(20)
    # 36/50 = 72%: chenh 22 diem >= 10 nhung can duoi Wilson (~0,58) con nam trong khoang cua nhieu (~0,34-0,66) -> KHONG duoc 'vuot'
    r = D.so_voi_nhieu(36, 50, tc, 4)
    assert r["ket_luan"] == "NGANG_NHIEU" and r["thuc"] - r["nhieu"] >= D.NHIEU_CHENH_TOI_THIEU and r["khoang_thuc"][0] < r["khoang_nhieu"][1]
    # khoang tin cay roi nhau nhung chenh chi 8 diem (< 10): van NGANG
    hep = {"kich_ban": {"NHIEU@e4": {"gop": {"qua_cao_nguyen": {"tb": 0.5, "ci95": [0.49, 0.51], "n_chuoi": 5000}}}}}
    r = D.so_voi_nhieu(580, 1000, hep, 4)
    assert r["khoang_thuc"][0] > 0.51 and r["ket_luan"] == "NGANG_NHIEU"
    assert D.so_voi_nhieu(610, 1000, hep, 4)["ket_luan"] == "VUOT_NHIEU"                           # chenh 11 diem: qua ngay
    assert D.so_voi_nhieu(390, 1000, hep, 4)["ket_luan"] == "DUOI_NHIEU"


def test_r1_chua_du_khi_it_ket_qua_that_khi_thieu_tham_chieu_hoac_sai_engine():
    tc = _tham_chieu(20)
    assert D.so_voi_nhieu(19, 19, tc, 4)["ket_luan"] == "CHUA_DU" and D.so_voi_nhieu(20, 20, tc, 4)["ket_luan"] != "CHUA_DU"
    assert D.so_voi_nhieu(45, 50, None, 4)["ket_luan"] == "CHUA_DU"
    assert D.so_voi_nhieu(45, 50, {}, 4)["ket_luan"] == "CHUA_DU"
    r = D.so_voi_nhieu(45, 50, tc, 3)                                    # tham chieu chi co engine 4: KHONG so engine 3 voi engine 4
    assert r["ket_luan"] == "CHUA_DU" and "engine 3" in r["ly_do"]
    tc3 = _tham_chieu(20, engine=3)
    assert D.so_voi_nhieu(45, 50, tc3, 3)["ket_luan"] == "VUOT_NHIEU" and D.so_voi_nhieu(45, 50, tc3, 4)["ket_luan"] == "CHUA_DU"
    mot = D.tong_ket([_dong({"mua_phang": _muc()}, hat=1)])                # 1 chuoi: chua co khoang tin cay
    assert D.so_voi_nhieu(45, 50, mot, 4)["ket_luan"] == "CHUA_DU"


def test_r1_bao_hoa_khi_nhieu_da_qua_gan_het_va_doi_sang_hon_moc():
    tc = _tham_chieu(38, hon_moc_qua=10)                                  # nhieu qua 95%, nhung chi 25% qua VA hon mua-giu/ban-giu
    r = D.so_voi_nhieu(48, 50, tc, 4)
    assert r["ket_luan"] == "BAO_HOA" and r["nhieu"] == 0.95 and "hon" in r["ly_do"]
    r2 = D.so_voi_nhieu(48, 50, tc, 4, hon_moc=True)
    assert r2["ket_luan"] == "VUOT_NHIEU" and r2["tieu_chi"] == "qua_hon_moc" and r2["nhieu"] == 0.25
    # dung 90% van la bao hoa (>=), 89% thi khong
    assert D.so_voi_nhieu(30, 50, _tham_chieu(36), 4)["ket_luan"] == "BAO_HOA"
    assert D.so_voi_nhieu(30, 50, _tham_chieu(35), 4)["ket_luan"] != "BAO_HOA"


# ------------------------------------------------------------------------------------------ doc / ghi tep, chay tiep, CLI

def test_doc_tham_chieu_thieu_hong_hay_dung(tmp_path):
    assert D.doc_tham_chieu(tmp_path / "khong_co.json") is None
    (tmp_path / "hong.json").write_text("{khong phai json", encoding="utf-8")
    assert D.doc_tham_chieu(tmp_path / "hong.json") is None
    (tmp_path / "rong.json").write_text(json.dumps({"kich_ban": {}}), encoding="utf-8")
    assert D.doc_tham_chieu(tmp_path / "rong.json") is None
    tk = _tham_chieu(20)
    (tmp_path / "tot.json").write_text(json.dumps(tk), encoding="utf-8")
    assert D.doc_tham_chieu(tmp_path / "tot.json")["kich_ban"].keys() == tk["kich_ban"].keys()


def test_doc_dong_bo_dong_hong_va_da_xong_chi_tinh_chuoi_tron_ven(tmp_path):
    ok = _dong({"mua_phang": _muc()}, hat=1)
    loi = {"v": D.PHIEN_BAN, "kb": "NHIEU", "hat": 2, "khop_bar": "duong_di", "so_bar": D.SO_BAR, "toi_da_o": D.TOI_DA_O, "loi": "x", "mau": {}}
    rong = _dong({}, hat=3)
    p = tmp_path / "x.jsonl"
    p.write_text("\n".join([json.dumps(ok), "", json.dumps(loi), json.dumps(rong), '{"kb": "NHIEU", "hat": 4, "mau": {"a"']), encoding="utf-8")
    dong = D.doc_dong(p)
    assert len(dong) == 3 and D.doc_dong(tmp_path / "khong_co.jsonl") == []                        # dong cuoi bi cat do bi ngat: bo qua
    xong = D.da_xong(dong)
    assert xong == {("NHIEU", 1, "duong_di", D.SO_BAR, D.TOI_DA_O, D.PHIEN_BAN)}                   # chuoi loi / chuoi khong co mau: se duoc chay lai


def test_chay_tiep_khong_lam_lai_chuoi_da_xong_va_khong_mo_pool(tmp_path, monkeypatch):
    tep = tmp_path / "r.jsonl"
    tep.write_text("\n".join(json.dumps(_dong({"mua_phang": _muc()}, hat=h, so_bar=500, toi_da_o=7)) for h in (1, 2)) + "\n", encoding="utf-8")

    def cam(*a, **k):
        raise AssertionError("khong duoc mo pool khi khong con viec")
    monkeypatch.setattr(multiprocessing, "get_context", cam)
    ra = D.chay(("NHIEU",), 2, 1, ("mua_phang",), ("duong_di",), 2, 7, 4, 500, tep=tep, im=True)
    assert [r["hat"] for r in ra] == [1, 2] and len(tep.read_text(encoding="utf-8").splitlines()) == 2


def _thu_muc_tam_cua_chay():
    import tempfile
    return {p for p in os.listdir(tempfile.gettempdir()) if p.startswith("doi_chung_nhieu_")}


@pytest.mark.cham
def test_chay_that_pool_ghi_tung_dong_resume_va_khong_cham_so_tay_that(tmp_path):
    that_truoc = _trang_thai_nc_db_that()
    truoc = _thu_muc_tam_cua_chay()
    tep = tmp_path / "r.jsonl"
    ra = D.chay(("NHIEU",), 2, 1, ("mua_phang",), ("duong_di",), 2, 16, 4, 9000, tep=tep, im=True)
    assert sorted(r["hat"] for r in ra) == [1, 2] and all(not r.get("loi") for r in ra), [r.get("loi") for r in ra]
    assert len(tep.read_text(encoding="utf-8").splitlines()) == 2
    ra2 = D.chay(("NHIEU",), 3, 1, ("mua_phang",), ("duong_di",), 1, 16, 4, 9000, tep=tep, im=True)      # xin 3 chuoi: chi hat 3 la moi
    assert sorted(r["hat"] for r in ra2) == [1, 2, 3] and len(tep.read_text(encoding="utf-8").splitlines()) == 3
    assert _trang_thai_nc_db_that() == that_truoc
    assert _thu_muc_tam_cua_chay() == truoc                                          # pool don dep thu muc tam cua no


def test_kiem_do_trung_thuc_khong_ghi_tep_chinh_va_so_1000_voi_3000(monkeypatch):
    goi = []

    def chay_gia(kich_ban, so_chuoi, hat_tu, mau_ten, khop_bar, luong, toi_da_o, so_o_cd, **kw):
        goi.append((tuple(kich_ban), so_chuoi, hat_tu, tuple(mau_ten), tuple(khop_bar), toi_da_o, kw))
        return [_dong({"mua_phang": _muc(), "ban_phang": _muc(tot="RUOT")}, hat=hat_tu + i, toi_da_o=toi_da_o) for i in range(so_chuoi)]
    monkeypatch.setattr(D, "chay", chay_gia)
    ra = D.kiem_do_trung_thuc(so_chuoi=3, mau_ten=("mua_phang", "ban_phang"), luong=2, hat_tu=9001)
    assert [g[5] for g in goi] == [1000, 3000] and all(g[2] == 9001 and g[4] == ("duong_di",) for g in goi)
    assert all(g[6] == {"im": True} for g in goi)                                    # khong truyen `tep`: khong dong vao tep ket qua chinh
    assert set(ra) == {"mua_phang", "ban_phang"} and set(ra["mua_phang"]) == {"1000", "3000"}
    assert ra["mua_phang"]["1000"]["cao"]["n"] == 3 and ra["ban_phang"]["3000"]["cao"]["qua"] == 0


def test_main_tu_choi_ten_la_va_tong_ket_tu_tep(tmp_path, capsys):
    assert D.main(["--kich-ban", "KHONG_CO", "--ra", str(tmp_path / "x")]) == 2
    assert "khong biet" in capsys.readouterr().err
    assert D.main(["--khop-bar", "ngau_nhien", "--ra", str(tmp_path / "x")]) == 2
    assert D.main(["--mau", "mua_phang,khong_co", "--ra", str(tmp_path / "x")]) == 2
    (tmp_path / "x.jsonl").write_text("\n".join(json.dumps(_dong({"mua_phang": _muc(), "ban_phang": _muc(tot="RUOT")}, hat=h)) for h in (1, 2, 3)) + "\n",
                                      encoding="utf-8")
    assert D.main(["--tong-ket", "--ra", str(tmp_path / "x")]) == 0
    out = capsys.readouterr().out
    assert "NHIEU@e4" in out and out.isascii()
    tk = json.loads((tmp_path / "x.json").read_text(encoding="utf-8"))
    assert tk["kich_ban"]["NHIEU@e4"]["so_chuoi"] == 3
    assert D.main(["--tong-ket", "--json", "--ra", str(tmp_path / "x")]) == 0
    assert json.loads(capsys.readouterr().out)["kich_ban"]["NHIEU@e4"]["gop"]["qua_o_tot_nhat"]["tb"] == 0.5


def test_module_chi_ascii():
    for p in (LAB / "nhan" / "doi_chung_nhieu.py", LAB / "nhan" / "test_doi_chung_nhieu.py"):
        loi = [i + 1 for i, d in enumerate(p.read_text(encoding="utf-8").splitlines()) if not d.isascii()]
        assert not loi, "%s co ky tu ngoai ASCII o dong %s" % (p.name, loi[:5])
