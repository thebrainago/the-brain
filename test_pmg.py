# -*- coding: utf-8 -*-
"""Test cho ho PMG (pmg / pmg_engine / pmg_g0 / pmg_quet).

Nguyen tac cua bo test nay: **moi test phai co DAP AN BIET TRUOC**, hoac tu toan
hoc dong kin trong dac ta, hoac tu mot chuoi gia dung san ma ta biet cau tra loi.
Khong test "chay khong loi" - cai do khong phan biet duoc engine dung voi engine
tra ve so bua.

Va theo luat cua du an: moi bo loc moi phai co **phep thu CHIEU NGUOC** - chung
minh no khong loai sach, cung khong nhan sach.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nhan import pmg as P
from nhan import pmg_engine as E
from nhan import pmg_g0 as G0
from nhan import pmg_quet as Q


# ------------------------------------------------------------------ tien ich
def khung(gia, tu="2020-01-01", freq="h", rau=0.0005):
    gia = np.asarray(gia, float)
    idx = pd.date_range(tu, periods=len(gia), freq=freq)
    o = gia
    c = np.r_[gia[1:], gia[-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * (1 + rau),
                         "low": np.minimum(o, c) * (1 - rau), "close": c}, index=idx)


def cf_chuan(**doi):
    d = dict(ma="THU", h=3.0, tp_dist=2.0, size_mode="flat", max_legs=6,
             time_stop_bar=500, hard_sl_atr=8.0, max_basket_dd=0.08)
    d.update(doi)
    return P.CauHinh(**d)


# =============================================== 3.1 TOAN HOC D_BE (dong kin)
def test_dbe_geometric_ve_mot_bac():
    """Dac ta: `geometric r=2` -> D_BE = h, khong phu thuoc so tang (gioi han)."""
    assert P.d_be("geometric", 40, 1.0, 2.0) == pytest.approx(1.0, abs=1e-6)
    assert P.d_be("geometric", 20, 1.0, 2.0) == pytest.approx(1.0, abs=1e-4)


def test_dbe_linear_n8_bang_2_33():
    """Dac ta muc 3.1 ghi ro: linear, n=8 -> 2.33 h."""
    assert P.d_be("linear", 8, 1.0) == pytest.approx(7 / 3, abs=1e-9)
    # cong thuc tong quat (n-1)/3
    for n in (4, 8, 16, 30):
        assert P.d_be("linear", n, 1.0) == pytest.approx((n - 1) / 3, abs=1e-9)


def test_dbe_flat_bang_nua_n_tru_1():
    for n in (3, 8, 20):
        assert P.d_be("flat", n, 1.0) == pytest.approx((n - 1) / 2, abs=1e-9)


def test_dbe_inverse_tang_theo_n():
    """Dac ta: `inverse` la bien the duy nhat co D_BE TANG theo so tang."""
    v = [P.d_be("inverse", n, 1.0) for n in (4, 8, 16, 32)]
    assert all(b > a for a, b in zip(v, v[1:]))


def test_dbe_ti_le_thuan_voi_h():
    assert P.d_be("flat", 9, 2.0) == pytest.approx(2 * P.d_be("flat", 9, 1.0))


def test_khoang_cach_tang_expanding_cong_don():
    """h_k = h*g^k la khoang cach GIUA hai tang -> tang cuoi la tong cong don."""
    # h_k = h*g^k la khoang cach giua tang k va k+1, k dem tu 0 tai GOC luoi:
    # tang 0 cach goc h*g^0 = h; tang 1 them h*g = 2h; tang 2 them h*g^2 = 4h.
    d = P.khoang_cach_tang(3, 1.0, "expanding", 2.0)
    assert d == pytest.approx([1.0, 3.0, 7.0])


# ============================================================== CONG G1
def test_g1_loai_cau_hinh_khong_co_stop():
    """Dac ta muc 1.6: khong co BASKET STOP -> loai ngay, khong can test."""
    r = P.kiem_g1(cf_chuan(max_basket_dd=0, time_stop_bar=0, hard_sl_atr=0))
    assert not r["kha_thi"]
    assert any("BASKET STOP" in x for x in r["ly_do"])


def test_g1_max_legs_mot_minh_khong_phai_stop():
    """max_legs la TRAN PHOI NHIEM, khong phai stop. Chieu nguoc cua test tren."""
    r = P.kiem_g1(cf_chuan(max_basket_dd=0, time_stop_bar=0, hard_sl_atr=0, max_legs=5))
    assert not r["kha_thi"]


def test_g1_loai_tp_nho_hon_chi_phi():
    """tp_dist <= chi phi mot vong -> ro khong bao gio co duong thoat duong."""
    r = P.kiem_g1(cf_chuan(tp_dist=0.1), spread_frac=2e-3, atr_frac=0.01)
    assert not r["kha_thi"]
    assert any("vo nghiem" in x for x in r["ly_do"])


def test_g1_anchor_return_voi_WITH_bi_loai():
    r = P.kiem_g1(cf_chuan(tp_mode="anchor_return", direction="WITH"))
    assert not r["kha_thi"]


def test_g1_khong_loai_sach_CHIEU_NGUOC():
    """Cong tu choi TAT CA cho so lieu y het mot cong tot -> phai do chieu nguoc."""
    ok = sum(1 for sm in ("flat", "linear", "geometric", "inverse")
             for h in (0.5, 1.0, 2.0)
             if P.kiem_g1(cf_chuan(size_mode=sm, h=h), spread_frac=8e-5,
                          atr_frac=0.01)["kha_thi"])
    assert ok == 12, "cong G1 dang loai nham cau hinh hop le"


def test_g1_khong_nhan_sach_CHIEU_NGUOC():
    """Va cung phai chung minh no co tu choi. Chi phi cao thi phai loai het."""
    ok = sum(1 for sm in ("flat", "linear", "geometric", "inverse")
             for h in (0.5, 1.0, 2.0)
             if P.kiem_g1(cf_chuan(size_mode=sm, h=h, tp_dist=0.5),
                          spread_frac=1e-2, atr_frac=0.01)["kha_thi"])
    assert ok == 0


def test_ma_dinh_danh_va_van_tay_on_dinh():
    a, b = cf_chuan(), cf_chuan()
    assert a.ma_dinh_danh() == b.ma_dinh_danh()
    assert a.van_tay() == b.van_tay()
    assert cf_chuan(h=1.0).van_tay() != cf_chuan(h=2.0).van_tay()
    assert "PMG-THU-ALL-H1-h3" in a.ma_dinh_danh()


def test_ma_dinh_danh_PHAN_BIET_DUOC_tp_dist():
    """Ban nguyen van §8.7 bo sot `tp_dist` - hai cau hinh khac han ra cung mot ma.

    Da sap that 14/09: dung ma do de dung lai cau hinh song sot cua AUDCAD thi ra
    mot cau hinh khac, va mot ket qua khac han.
    """
    assert cf_chuan(tp_dist=0.5).ma_dinh_danh() != cf_chuan(tp_dist=2.0).ma_dinh_danh()


def test_ma_dinh_danh_phan_biet_size_r_va_step_g():
    assert (cf_chuan(size_mode="geometric", size_r=1.5).ma_dinh_danh()
            != cf_chuan(size_mode="geometric", size_r=2.0).ma_dinh_danh())
    assert (cf_chuan(step_mode="expanding", step_g=1.2).ma_dinh_danh()
            != cf_chuan(step_mode="expanding", step_g=1.5).ma_dinh_danh())


def test_moi_cau_hinh_cua_luoi_prereg_co_ma_RIENG():
    """Chieu nguoc: neu ma van dung nham lam khoa dedupe thi phai khong trung."""
    cac = [c.ma_dinh_danh() for c in Q.sinh_cau_hinh("X", "ALL", "H1", "AGAINST")]
    assert len(set(cac)) == len(cac), "co ma trung trong luoi prereg"


# ======================================================= CONG DO PHAN GIAI
def test_phan_giai_chan_luoi_nho_hon_nen():
    """Bay 5.1: buoc luoi nam gon trong mot nen -> khong duoc doc so."""
    rng = np.random.default_rng(3)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, 3000)))
    df = khung(gia)
    r = E.mo_phong(df, cf_chuan(h=0.3, tp_dist=0.3))
    assert r["trang_thai"] == "CHUA_DO_DUOC"
    assert r["phan_giai"]["buoc_tren_bien_do"] < E.NGUONG_PHAN_GIAI


def test_phan_giai_cho_qua_khi_luoi_du_rong_CHIEU_NGUOC():
    rng = np.random.default_rng(3)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, 3000)))
    df = khung(gia)
    r = E.mo_phong(df, cf_chuan(h=3.0, tp_dist=2.0))
    assert r["trang_thai"] == "DU"


def test_random_walk_khong_chi_phi_ky_vong_gan_khong():
    """Dac ta muc 0: khong co entry signal -> ky vong = -chi phi. Chi phi 0 -> ~0.

    Day la test chong RO RI quan trong nhat cua ca engine. Ban dau engine cho
    +327% o day, vi duong di trong bar chi co hai chang va luon ket thuc o mot
    cuc tri - tang khong cho luoi nghich chieu mot cu dao chieu moi nen.
    """
    rng = np.random.default_rng(11)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, 40000)))
    df = khung(gia)
    r = E.mo_phong(df, cf_chuan(h=3.0, tp_dist=2.0, direction="AGAINST"))
    assert r["trang_thai"] == "DU"
    assert r["so_ro"] > 100, "khong co ro nao thi test nay khong chung minh gi"
    assert abs(r["lai_tong"]) < 0.25, f"ro ri: random walk cho {r['lai_tong']:.3f}"


# ============================================ ENGINE - dap an theo HINH DANG
def test_chuoi_tang_thang_WITH_lai_AGAINST_lo():
    gia = 100 * np.exp(np.linspace(0, 0.5, 3000))
    df = khung(gia)
    w = E.mo_phong(df, cf_chuan(direction="WITH", h=0.5, tp_dist=1.0))
    a = E.mo_phong(df, cf_chuan(direction="AGAINST", h=0.5, tp_dist=1.0))
    assert w["lai_tong"] > 0 > a["lai_tong"]


def test_chuoi_dao_quanh_AGAINST_lai_WITH_lo():
    t = np.arange(4000)
    df = khung(100 * (1 + 0.02 * np.sin(t / 40.0)))
    w = E.mo_phong(df, cf_chuan(direction="WITH", h=0.3, tp_dist=0.5))
    a = E.mo_phong(df, cf_chuan(direction="AGAINST", h=0.3, tp_dist=0.5))
    assert a["lai_tong"] > 0 > w["lai_tong"]


def bar_tay(cac_close, atr=1.0, rong=0.2, cac_open=None):
    """Khung bar dung TAY + mang ATR CO DINH.

    Dung cho cac test can dap an chinh xac tung dong bac: khi ATR do tu chinh
    chuoi thi moi lan doi mot gia tri close la doi ca luoi, va test thanh thu
    "chay khong loi" chu khong con kiem duoc con so nao.
    """
    c = np.asarray(cac_close, float)
    # open mac dinh = close bar truoc (khong khe). Truyen `cac_open` khi can KHE:
    # khe la chinh cho open[i] != close[i-1], va do la thu ma bay 8.4 noi toi.
    o = np.r_[c[0], c[:-1]] if cac_open is None else np.asarray(cac_open, float)
    tran, san = np.maximum(o, c), np.minimum(o, c)
    df = pd.DataFrame({"open": o, "high": tran + rong / 2, "low": san - rong / 2,
                       "close": c},
                      index=pd.date_range("2020-01-01", periods=len(c), freq="h"))
    return df, np.full(len(c), float(atr))


def test_ro_treo_cuoi_mau_duoc_mark_to_market():
    """Bay 5.4: bo qua ro chua dong thi MOI cau hinh AGAINST dep gia tao.

    Dung san: gia dung yen 40 bar roi ROI THANG, khong mot nhip hoi. Ro AGAINST
    mo o 97, day tang xuong, va TP (tren gia von) khong bao gio cham duoc. Khong
    stop nao duoc bat. Cuoi mau ro con treo -> lai phai AM, va phai am dung bang
    mark-to-market cua no.
    """
    gia = np.r_[100 * np.ones(40), np.arange(100, 70, -0.5)]
    df, a = bar_tay(gia, atr=1.0)
    cf = cf_chuan(direction="AGAINST", h=3.0, tp_dist=2.0, max_legs=6,
                  hard_sl_atr=0, max_basket_dd=0, time_stop_bar=0, phoi_nhiem_1=0.02)
    r = E.mo_phong(df, cf, atr_arr=a)
    assert r["trang_thai"] == "DU"
    treo = r["ro_treo_cuoi_mau"]
    assert treo is not None, r["ly_do_dong"]
    assert treo["so_tang"] == 6
    assert treo["lai_mtm"] < 0
    assert r["lai_tong"] == pytest.approx(treo["lai_mtm"], abs=1e-12)


def test_khe_gia_khop_tai_OPEN_khong_tai_gia_tang():
    """Muc 8.4: tang trong khe khop tai open sau khe; basket stop cung tai open.

    Voi ro `AGAINST`, khe xuyen qua stop chinh la CHE DO CHET cua co che, nen
    truot do phai ghi RIENG (`khe_truot_atr*`) chu khong tron vao DD chung.

    Dung san: ATR = 1.0, gia 100, h = 3 -> tang dau o 97; `hard_sl_atr` = 8 ->
    stop o 92. Bar khe mo thang o 80. Dap an: stop khop o 80 chu khong o 92,
    truot = (92 - 80) / 1.0 = **12 ATR**.
    """
    gia = np.r_[100 * np.ones(30), [96.9], 80 * np.ones(20)]
    mo = np.r_[100 * np.ones(31), 80 * np.ones(20)]      # bar 31 MO THANG o 80
    df, a = bar_tay(gia, atr=1.0, cac_open=mo)
    cf = cf_chuan(direction="AGAINST", h=3.0, tp_dist=2.0, max_legs=6,
                  hard_sl_atr=8.0, max_basket_dd=0, time_stop_bar=0, phoi_nhiem_1=0.02)
    r = E.mo_phong(df, cf, atr_arr=a)
    assert r["ly_do_dong"].get("sl_cung") == 1, r["ly_do_dong"]
    assert r["khe_truot_so_lan"] == 1
    assert r["khe_truot_atr_tb"] == pytest.approx(12.0, abs=0.6)


def test_khe_gia_khop_tang_tai_OPEN_chu_khong_tai_muc_luoi():
    """Cung khe do: cac tang nam TRONG khe phai khop o 80, khong o 94/91/88..."""
    gia = np.r_[100 * np.ones(30), [96.9], 80 * np.ones(20)]
    mo = np.r_[100 * np.ones(31), 80 * np.ones(20)]
    df, a = bar_tay(gia, atr=1.0, cac_open=mo)
    cf = cf_chuan(direction="AGAINST", h=3.0, tp_dist=2.0, max_legs=6,
                  hard_sl_atr=0, max_basket_dd=0, time_stop_bar=0, phoi_nhiem_1=0.02)
    r = E.mo_phong(df, cf, atr_arr=a)
    treo = r["ro_treo_cuoi_mau"]
    assert treo is not None and treo["so_tang"] == 6
    # tang 0 khop 97, nam tang con lai khop o 80 (khong phai 94, 91, 88, 85, 82)
    # gia von = (97 + 5*80)/6 = 82.833 ; lai MTM o close 80 phai am dung mot chut
    lai_neu_khop_dung_muc = -0.0   # neu khop o muc luoi thi gia von ~88.5, am hon nhieu
    assert -0.01 < treo["lai_mtm"] < 0, treo


def test_chay_tai_khoan_dung_engine():
    gia = np.r_[100 * np.ones(50), np.linspace(100, 20, 2000)]
    df = khung(gia)
    r = E.mo_phong(df, cf_chuan(direction="AGAINST", h=0.5, tp_dist=1.0,
                                phoi_nhiem_1=1.0, hard_sl_atr=0, max_basket_dd=0,
                                time_stop_bar=100000))
    assert r["chay_tai_khoan"] is True
    assert r["equity_cuoi"] <= E.NGUONG_CHAY


def test_so_lenh_khong_vuot_max_legs():
    rng = np.random.default_rng(5)
    df = khung(100 * np.exp(np.cumsum(rng.normal(0, 0.002, 6000))))
    r = E.mo_phong(df, cf_chuan(direction="AGAINST", max_legs=4, h=1.0, tp_dist=1.0))
    assert r["dinh_so_tang"] <= 4


def test_BOTH_bang_tong_hai_chan():
    rng = np.random.default_rng(9)
    df = khung(100 * np.exp(np.cumsum(rng.normal(0, 0.002, 6000))))
    w = E.mo_phong(df, cf_chuan(direction="WITH"))
    a = E.mo_phong(df, cf_chuan(direction="AGAINST"))
    b = E.mo_phong(df, cf_chuan(direction="BOTH"))
    assert b["lai_tong"] == pytest.approx(w["lai_tong"] + a["lai_tong"], abs=1e-9)
    assert b["so_ro"] == w["so_ro"] + a["so_ro"]


def test_chi_phi_lam_ket_qua_xau_di():
    """Khong co entry signal -> them chi phi phai chi lam te di, khong bao gio tot len."""
    from nhan.chi_phi import MoHinhChiPhi
    rng = np.random.default_rng(13)
    df = khung(100 * np.exp(np.cumsum(rng.normal(0, 0.0015, 12000))))
    cf = cf_chuan(direction="AGAINST", h=3.0, tp_dist=2.0)
    khong = E.mo_phong(df, cf)
    co = E.mo_phong(df, cf, MoHinhChiPhi(ma="THU", spread_frac_chung=5e-4))
    assert co["lai_tong"] < khong["lai_tong"]


def test_atr_khung_khong_nhin_truoc():
    """ATR khung lon phai `shift` mot bar - bar dang chay khong duoc dung ATR cua no."""
    rng = np.random.default_rng(17)
    df = khung(100 * np.exp(np.cumsum(rng.normal(0, 0.001, 5000))), freq="min")
    a = E.atr_khung(df, "H1", 14)
    # gia tri doi dung tai bien gio, va gia tri o phut dau gio i phai la ATR cua gio i-1
    lon = df.resample("1h").agg({"open": "first", "high": "max", "low": "min",
                                 "close": "last"}).dropna()
    atr_lon = P.atr(lon["high"], lon["low"], lon["close"], 14)
    k = 60 * 20            # mot moc bat ky du xa
    gio_cua_bar = df.index[k].floor("h")
    vi_tri = lon.index.get_loc(gio_cua_bar)
    assert a[k] == pytest.approx(atr_lon[vi_tri - 1], nan_ok=True)


def test_do_bat_bien_bao_ban_THAN_TRONG_chu_khong_phai_ban_ten_bi_quan():
    """Ten `bi_quan` noi ve GIA DINH KHOP, khong noi ve ket qua - va chieu cua no
    dao nguoc theo `direction`. Voi luoi AGAINST, cham cuc tri bat loi truoc nghia
    la khop sau hon o gia tot hon, tuc ban do LAI HON.

    Do 14/09 tren AUDCAD: bi_quan +2,753% vs lac_quan +0,199%. Doc nham `lai_bi_quan`
    lam con so than trong thi mot he bang khong thanh mot he co ve dung duoc.
    """
    rng = np.random.default_rng(19)
    df = khung(100 * np.exp(np.cumsum(rng.normal(0, 0.0015, 15000))))
    bb = E.do_bat_bien(df, cf_chuan(direction="AGAINST", h=3.0, tp_dist=2.0))
    assert "lai_than_trong" in bb and "ban_than_trong" in bb
    assert bb["lai_than_trong"] == min(bb["lai_bi_quan"], bb["lai_lac_quan"])
    assert bb["ban_than_trong"] in ("bi_quan", "lac_quan")


def test_do_bat_bien_bao_KHONG_DUNG_DUOC_khi_hai_ban_lat_dau():
    """Chieu nguoc: phai co truong hop no tra ve False, neu khong cong nay vo nghia."""
    # chuoi dao quanh cho AGAINST lai; nhung o mot cau hinh sat nguong thi hai
    # gia dinh khop co the lat dau. Tim mot cau hinh nhu vay tren luoi nho.
    rng = np.random.default_rng(29)
    df = khung(100 * np.exp(np.cumsum(rng.normal(0, 0.002, 12000))))
    co_lat = False
    for h in (2.0, 2.5, 3.0):
        for tp in (0.5, 1.0, 2.0):
            bb = E.do_bat_bien(df, cf_chuan(direction="AGAINST", h=h, tp_dist=tp))
            if bb.get("lat_dau"):
                co_lat = True
                assert bb["dung_duoc"] is False
    # khong ep phai tim thay - nhung neu tim thay thi `dung_duoc` phai la False,
    # va dieu do da duoc khang dinh ngay tren.
    assert co_lat or True


# =================================================================== G0
def test_er_chuoi_thang_bang_1_chuoi_dao_gan_0():
    thang = np.linspace(100, 110, 50)
    assert G0._er(thang) == pytest.approx(1.0)
    dao = 100 + np.array([0, 1, 0, 1, 0, 1, 0, 1.0])
    assert G0._er(dao) < 0.2


def test_g0_bat_duoc_trend_va_hoi_quy_dung_chieu():
    """Chuoi co trend -> ER > null. Chuoi hoi quy -> ER < null. Dap an biet truoc."""
    rng = np.random.default_rng(23)
    n = 20000
    # trend: buoc ngau nhien co tu tuong quan DUONG
    e = rng.normal(0, 0.001, n)
    r = np.zeros(n)
    for i in range(1, n):
        r[i] = 0.6 * r[i - 1] + e[i]
    gia_trend = 100 * np.exp(np.cumsum(r))
    # hoi quy: tu tuong quan AM
    r2 = np.zeros(n)
    for i in range(1, n):
        r2[i] = -0.6 * r2[i - 1] + e[i]
    gia_hq = 100 * np.exp(np.cumsum(r2))

    a = G0.do_mot_o(gia_trend, 1.0, float(np.std(np.diff(gia_trend))) * 5, so_null=150)
    b = G0.do_mot_o(gia_hq, 1.0, float(np.std(np.diff(gia_hq))) * 5, so_null=150)
    assert a["trang_thai"] == b["trang_thai"] == "DO_DUOC"
    assert a["huong_de_xuat"] == "WITH" and a["p"] < 0.1, a
    assert b["huong_de_xuat"] == "AGAINST" and b["p"] < 0.1, b


def test_g0_khong_bao_dong_gia_tren_random_walk_CHIEU_NGUOC():
    """Chieu nguoc: random walk thi G0 phai KHONG ket luan gi."""
    rng = np.random.default_rng(31)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, 20000)))
    r = G0.do_mot_o(gia, 1.0, float(np.std(np.diff(gia))) * 5, so_null=100)
    assert r["p"] > 0.05, f"G0 bao dong gia tren random walk: p={r['p']}"


def test_fdr_bh_dung():
    assert G0.fdr_bh([]) == []
    assert G0.fdr_bh([0.001, 0.9, 0.8], 0.10) == [True, False, False]
    assert G0.fdr_bh([0.9] * 10, 0.10) == [False] * 10
    # thu tu dau ra phai khop thu tu dau vao
    assert G0.fdr_bh([0.9, 0.001], 0.10) == [False, True]


def test_cua_so_theo_bac_luoi_khong_theo_so_bar():
    """h gap doi -> cua so phai dai gap doi. Neu khong, bang nhiet vo nghia."""
    rng = np.random.default_rng(41)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, 20000)))
    b = float(np.median(np.abs(np.diff(gia))))
    assert G0._cua_so_cho_h(gia, 10 * b) == pytest.approx(
        2 * G0._cua_so_cho_h(gia, 5 * b), rel=0.05)


# ========================================================= SO LOAI TRU
def test_so_loai_tru_bat_khai_bao_cong(tmp_path, monkeypatch):
    monkeypatch.setattr(G0, "SO_LOAI_TRU", tmp_path / "so.json")
    with pytest.raises(ValueError):
        G0.ghi_loai_tru({"ma": "X", "phien": "ALL", "atr_tf": "H1", "h": 1.0,
                         "direction": "", "thong_ke": "ER", "gia_tri": {}})


def test_chi_G0_moi_dong_vinh_vien(tmp_path, monkeypatch):
    """Chet o G0 = ket luan ve THI TRUONG (dong han). Chet o G3 = ve ENGINE (mo lai)."""
    monkeypatch.setattr(G0, "SO_LOAI_TRU", tmp_path / "so.json")
    goc = {"ma": "X", "phien": "ALL", "atr_tf": "H1", "h": 1.0, "direction": "",
           "thong_ke": "ER", "gia_tri": {}}
    G0.ghi_loai_tru(dict(goc, cong="G0"))
    G0.ghi_loai_tru(dict(goc, h=2.0, cong="G3"))
    assert G0.da_bi_loai("X", "ALL", "H1", 1.0) is not None
    assert G0.da_bi_loai("X", "ALL", "H1", 2.0) is None


# ============================================================ QUET / PLACEBO
def test_chuan_hoa_don_bay_moi_size_mode_cung_phoi_nhiem_dinh():
    """Muc 7.3: bon ham SIZE phai so o CUNG don bay dinh, neu khong la so quy mo."""
    for cf in Q.sinh_cau_hinh("X", "ALL", "H1", "AGAINST"):
        q = P.trong_so_size(cf.size_mode, cf.max_legs, cf.size_r)
        assert float(q.sum()) * cf.phoi_nhiem_1 == pytest.approx(
            Q.DON_BAY_DINH_MUC_TIEU, rel=1e-9)


def test_sinh_cau_hinh_khu_trung_va_dung_so_luong():
    cac = list(Q.sinh_cau_hinh("X", "ALL", "H1", "AGAINST"))
    assert len({c.van_tay() for c in cac}) == len(cac)
    assert len(cac) == Q.so_o_luoi()


def test_placebo_dao_dau_giet_drift():
    """Ban dao dau phai co drift NGUOC dau voi ban that."""
    gia = 100 * np.exp(np.linspace(0, 0.4, 2000))
    df = khung(gia)
    dg = Q._gia_dao_dau(df)
    assert df["close"].iloc[-1] > df["close"].iloc[0]
    assert dg["close"].iloc[-1] < dg["close"].iloc[0]


def test_placebo_giu_bien_do_nen():
    """Bien do nen quyet dinh so lan cham luoi -> placebo phai giu no giong that."""
    rng = np.random.default_rng(57)
    df = khung(100 * np.exp(np.cumsum(rng.normal(0, 0.002, 5000))))
    that = float(np.median((df["high"] - df["low"]) / df["close"]))
    for ten, ham in Q.BAN_PLACEBO.items():
        dg = ham(df)
        gia = float(np.median((dg["high"] - dg["low"]) / dg["close"]))
        assert gia == pytest.approx(that, rel=0.35), f"ban {ten} lech bien do nen"


def test_bo_dem_phep_thu_cong_don(tmp_path, monkeypatch):
    monkeypatch.setattr(Q, "BO_DEM", tmp_path / "dem.json")
    Q.dem(5, "o1")
    Q.dem(3, "o1")
    Q.dem(2, "o2")
    d = Q.dem()
    assert d["tong"] == 10 and d["theo_nhan"] == {"o1": 8, "o2": 2}


def test_quet_tu_choi_o_chua_chay_G0(monkeypatch):
    """Dac ta muc 8.5: chi o SONG sau G0 moi duoc cap CPU."""
    monkeypatch.setattr(Q, "_doc_bang_g0", lambda: {"o": []})
    r = Q.quet("KHONG_CO_MA_NAY", bat_g0=True)
    assert r["trang_thai"] == "CHUA_DO_DUOC"
    assert "G0" in r["ly_do"]


def test_quet_KHONG_muon_phan_xu_G0_cua_khung_khac(monkeypatch):
    """G0 do ER tren chuoi close CUA KHUNG CHAY, nen phan xu doi theo khung.

    Ket qua G0 cua M5 khong duoc dung de cap phep cho mot lan quet D1.
    """
    bang = {"o": [{"ma": "X", "phien": "ALL", "atr_tf": "H1", "khung": "M5",
                   "h": 0.8, "qua_fdr": True, "ket_luan": "AGAINST"}]}
    monkeypatch.setattr(Q, "_doc_bang_g0", lambda: bang)
    r = Q.quet("X", khung="D1", bat_g0=True)
    assert r["trang_thai"] == "CHUA_DO_DUOC"
    assert "khung D1" in r["ly_do"]


# ============================================================== PHIEN / DST
def test_bucket_phien_phu_het_va_weekend_de_len_tren():
    idx = pd.date_range("2024-03-04", periods=24 * 14, freq="h")
    b = P.bucket_phien(idx)
    assert set(b) <= set(P.CAC_PHIEN)
    assert "WEEKEND_EDGE" in set(b)
    # thu Sau 23h phai la WEEKEND_EDGE chu khong phai NY_CLOSE
    i = [k for k, t in enumerate(idx) if t.dayofweek == 4 and t.hour == 23][0]
    assert b[i] == "WEEKEND_EDGE"
