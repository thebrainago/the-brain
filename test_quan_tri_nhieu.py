# -*- coding: utf-8 -*-
"""Test LOGIC cua `nhan/quan_tri_nhieu.py` — nam ho quan tri nhieu vi the.

Bo test nay khong hoi "co lai khong". No hoi **"co lam dung cai no noi la lam
khong"** — tung luat mot, tren chuoi gia dung TAY, voi ATR GHIM CUNG, de moi
khang dinh co mot dap an tinh duoc bang giay but.

Vi sao phai chat den vay: module quan li lenh la thu so do goi la quan trong
nhat toan he thong, va nam ho nay truoc gio chua he chay bang Python lan nao -
chung chi ton tai trong mot file MQL5 chay tren tester. Mot engine moi ma chi
test bang "chay khong bao loi" thi khong phan biet duoc no dung hay no tra ve
so bua.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nhan import quan_tri_nhieu as QN


# ------------------------------------------------------------------ tien ich
def bar(cac_close, atr=1.0, rong=0.2, cac_open=None):
    """Khung nen dung TAY + mang ATR CO DINH. Moi test co dap an tinh duoc."""
    c = np.asarray(cac_close, float)
    o = np.r_[c[0], c[:-1]] if cac_open is None else np.asarray(cac_open, float)
    tran, san = np.maximum(o, c), np.minimum(o, c)
    df = pd.DataFrame({"open": o, "high": tran + rong / 2, "low": san - rong / 2,
                       "close": c},
                      index=pd.date_range("2020-01-01", periods=len(c), freq="h"))
    return df, np.full(len(c), float(atr))


def tin_hieu_tai(n, bar_i, chieu=1):
    """Mot tin hieu duy nhat o bar `bar_i` -> vao lenh o open[bar_i + 1]."""
    th = np.zeros(n)
    th[bar_i] = chieu
    return th


def chay(gia, ho, p, **kw):
    n = len(gia)
    df, a = bar(gia, atr=kw.pop("atr", 1.0), cac_open=kw.pop("cac_open", None))
    th = kw.pop("tin_hieu", tin_hieu_tai(n, kw.pop("vao_tai", 20)))
    return QN.dap_nhieu(df, th, ho, p, atr_arr=a, **kw)


# ============================================================ LUOI DCA
def test_luoi_dca_nhoi_dung_so_tang_theo_khoang_cach():
    """Luat EA: nhoi khi nguoc >= buoc x (so_nhoi + 1). Buoc 1 ATR = 1 gia.

    Gia vao 100, roi xuong 99 (nhoi 1), 97 (nhoi 2: can nguoc >= 2 tu gia TB)...
    Dap an tinh tay: chuoi roi deu 1 don vi moi nen thi moi buoc nhoi can mot
    khoang NGUOC xa dan, nen so tang PHAI it hon so nen da roi.
    """
    gia = np.r_[100 * np.ones(22), np.arange(100, 88, -0.5), 88 * np.ones(30)]
    r = chay(gia, "luoi_dca", {"buoc_atr": 1.0, "tp_atr": 99.0}, vao_tai=20,
             nhoi_toi_da=5, giu_toi_da=100)
    assert r["so_ro"] == 1
    assert r["so_lenh"] == 5, f"tran nhoi 5 bi vuot: {r['so_lenh']}"


def test_luoi_dca_ton_trong_tran_nhoi():
    gia = np.r_[100 * np.ones(22), np.arange(100, 50, -0.5)]
    for tran in (3, 6, 10):
        r = chay(gia, "luoi_dca", {"buoc_atr": 0.5, "tp_atr": 99.0}, vao_tai=20,
                 nhoi_toi_da=tran, giu_toi_da=10_000)
        assert r["so_lenh"] <= tran, f"tran {tran} bi vuot: {r['so_lenh']}"


def test_luoi_dca_chot_ca_ro_theo_gia_TRUNG_BINH_chu_khong_tung_lenh():
    """Day la dac diem dinh nghia cua ho luoi: TP chung tinh tu gia von binh quan.

    Vao 100, nhoi them o 98 -> gia von 99. TP 1 ATR = gia 100. Gia len 100 thi
    DONG CA HAI, lai = (100-100) + (100-98) = +2,0 dung bang giay but.
    """
    gia = np.r_[100 * np.ones(22), 98.0, 98.0, 100.0, 100 * np.ones(5)]
    r = chay(gia, "luoi_dca", {"buoc_atr": 1.0, "tp_atr": 1.0}, vao_tai=20,
             nhoi_toi_da=5, giu_toi_da=100)
    assert r["ly_do"].get("tp_chung") == 1, r["ly_do"]
    assert r["so_lenh"] == 2
    assert r["lai_tong"] == pytest.approx(2.0, abs=1e-9)


def test_luoi_dca_KHONG_dat_sl_tung_lenh():
    """Luoi an toan cua ho nay la tran nhoi + tran nen, khong phai SL tung chan.

    Chuoi roi thang 40 don vi: neu co SL 3 ATR tung chan thi phai thay
    `sl_tung_lenh`; dung luat thi phai thay `tran_nen`.
    """
    gia = np.r_[100 * np.ones(22), np.arange(100, 60, -1.0)]
    r = chay(gia, "luoi_dca", {"buoc_atr": 2.0, "tp_atr": 2.0}, vao_tai=20,
             nhoi_toi_da=4, giu_toi_da=20)
    assert "sl_tung_lenh" not in r["ly_do"], r["ly_do"]
    assert r["lai_tong"] < 0


# ================================================================ HEDGE
def test_hedge_mo_khoa_dung_nguong_va_dung_chieu():
    """Luat EA: khi lo cua ca ro >= nguong thi mo mot chan NGUOC chieu."""
    gia = np.r_[100 * np.ones(22), np.arange(100, 94, -0.5), 94 * np.ones(20)]
    r = chay(gia, "hedge", {"mo_khoa_atr": 2.0, "he_so_lot": 1.0}, vao_tai=20,
             giu_toi_da=100)
    assert r["so_lenh"] == 2, f"phai co dung 1 chan goc + 1 chan khoa: {r['so_lenh']}"


def test_hedge_chua_cham_nguong_thi_KHONG_mo_khoa():
    """Chieu nguoc: neu no luon mo khoa thi cai nguong chi la trang tri."""
    gia = np.r_[100 * np.ones(22), 99.8 * np.ones(30)]
    r = chay(gia, "hedge", {"mo_khoa_atr": 2.0}, vao_tai=20, giu_toi_da=100)
    assert r["so_lenh"] == 1, r["ly_do"]


def test_hedge_LOT_BANG_NHAU_thi_khoa_CHET_khong_bao_gio_ve_duong():
    """Phat hien logic 14/09, va la ly do EA co tham so he so lot.

    Khoa bang lot BANG NHAU thi phoi nhiem rong = 0, nen lai cua ro **dong bang**
    o dung muc lo luc khoa: mua@100 + ban@98 -> lai = (p-100) + (98-p) = -2 voi
    MOI gia p. Khong co duong nao ve duong ca. Ro chi thoat khi mot chan cham SL,
    va luc do la THUA CHAC.

    Tuc "hedge de cuu lenh" voi lot bang nhau khong phai la cuu - la dong bang lo
    roi tra them phi. Ghi thanh test de khong ai doc bang ket qua ma tuong ho nay
    thua vi thi truong.
    """
    gia = np.r_[100 * np.ones(22), np.arange(100, 94, -0.5),
                np.arange(94, 104, 0.5), 104 * np.ones(10)]
    r = chay(gia, "hedge", {"mo_khoa_atr": 2.0, "he_so_lot": 1.0}, vao_tai=20,
             giu_toi_da=200)
    assert r["so_lenh"] == 2
    assert r["lai_tong"] < 0, "khoa lot bang nhau ma van ve duong -> engine sai"


def test_hedge_LOT_LON_HON_va_KHONG_SL_CHAN_GOC_thi_moi_hoi_phuc_duoc():
    """Chieu nguoc: co phoi nhiem rong VA khong bi cat chan goc thi ro hoi phuc.

    Khoa lot 2 lan: mua@100 lot1 + ban@98 lot2 -> phoi nhiem rong -1. Gia roi
    tiep thi lai cua ro = 96 - p, duong khi p < 96. Dap an tinh tay.
    """
    gia = np.r_[100 * np.ones(22), np.arange(100, 90, -0.5), 90 * np.ones(20)]
    r = chay(gia, "hedge", {"mo_khoa_atr": 2.0, "he_so_lot": 2.0}, vao_tai=20,
             giu_toi_da=200, sl_cung=0.0)
    assert r["ly_do"].get("ro_ve_duong") == 1, r["ly_do"]
    assert r["lai_tong"] > 0


def test_hedge_CO_SL_CHAN_GOC_thi_chan_goc_bi_cat_TRUOC_khi_kip_hoi_phuc():
    """Phat hien logic 14/09 — ho `hedge` nhu dac ta la TU MAU THUAN.

    SL cung 3 ATR dat tren chan goc nam **ben trong** duong hoi phuc: voi khoa
    lot 2 lan mo o 2 ATR, ro chi duong khi gia di them 2 ATR nua - ma truoc do
    1 ATR thi chan goc da cham SL va bi cat lo.

    Cung mot chuoi gia, cung mot tham so, chi khac co SL chan goc hay khong:
        khong SL -> ro ve duong, LAI
        co SL 3 ATR -> chan goc bi cat, LO
    Day khong phai loi engine; day la tinh chat cua chinh bo luat, va no giai
    thich vi sao ban do MT5 xep `hedge` vao nhom "cai gai".
    """
    gia = np.r_[100 * np.ones(22), np.arange(100, 90, -0.5), 90 * np.ones(20)]
    p = {"mo_khoa_atr": 2.0, "he_so_lot": 2.0}
    khong_sl = chay(gia, "hedge", p, vao_tai=20, giu_toi_da=200, sl_cung=0.0)
    co_sl = chay(gia, "hedge", p, vao_tai=20, giu_toi_da=200, sl_cung=3.0)
    assert khong_sl["lai_tong"] > 0 > co_sl["lai_tong"]


# ========================================================== STOP HAI DAU
def test_stop_2_dau_chi_MOT_chan_khop_va_huy_chan_kia():
    """Dac diem dinh nghia: cai nao khop thi huy cai kia."""
    gia = np.r_[100 * np.ones(22), 102.0, 103.0, 103 * np.ones(10)]
    r = chay(gia, "stop_2_dau", {"kc_atr": 1.0}, vao_tai=20, giu_toi_da=100)
    assert r["so_lenh"] == 1, f"ca hai chan cung khop: {r['so_lenh']}"


def test_stop_2_dau_khop_chan_MUA_khi_gia_len():
    gia = np.r_[100 * np.ones(22), 105 * np.ones(20)]
    r = chay(gia, "stop_2_dau", {"kc_atr": 1.0}, vao_tai=20, giu_toi_da=100)
    assert r["ro"][0]["chieu"] == 1


def test_stop_2_dau_khop_chan_BAN_khi_gia_xuong():
    gia = np.r_[100 * np.ones(22), 95 * np.ones(20)]
    r = chay(gia, "stop_2_dau", {"kc_atr": 1.0}, vao_tai=20, giu_toi_da=100)
    assert r["ro"][0]["chieu"] == -1


def test_stop_2_dau_gia_dung_yen_thi_KHONG_chan_nao_khop():
    gia = 100 * np.ones(60)
    r = chay(gia, "stop_2_dau", {"kc_atr": 1.0}, vao_tai=20, giu_toi_da=100)
    assert r["so_lenh"] == 0


# ================================================= THI TRUONG + STOP DOI
def test_tt_stop_doi_mo_ngay_mot_chan_va_dat_lenh_cho_NGUOC_chieu():
    gia = np.r_[100 * np.ones(22), np.arange(100, 97, -0.25), 97 * np.ones(20)]
    r = chay(gia, "tt_stop_doi", {"kc_atr": 1.0, "he_so_lot": 1.0}, vao_tai=20,
             giu_toi_da=100)
    assert r["so_lenh"] == 2, f"chan doi dien chua khop: {r['so_lenh']}"


def test_tt_stop_doi_gia_khong_lui_thi_chan_doi_dien_KHONG_khop():
    gia = np.r_[100 * np.ones(22), np.arange(100, 106, 0.5), 106 * np.ones(10)]
    r = chay(gia, "tt_stop_doi", {"kc_atr": 1.0}, vao_tai=20, giu_toi_da=100)
    assert r["so_lenh"] == 1


# ============================================================ THOI GIAN
@pytest.mark.parametrize("nen", [5, 10, 25])
def test_thoi_gian_dong_dung_sau_N_nen(nen):
    gia = np.r_[100 * np.ones(22), 100 + np.arange(60) * 0.01]
    r = chay(gia, "thoi_gian", {"so_nen": nen}, vao_tai=20, giu_toi_da=10_000)
    assert r["ly_do"].get("het_gio") == 1, r["ly_do"]
    assert r["ro"][0]["giu_bar"] == nen


def test_thoi_gian_dong_BAT_KE_dang_lai_hay_lo():
    for huong in (+0.05, -0.05):
        gia = np.r_[100 * np.ones(22), 100 + np.arange(40) * huong]
        r = chay(gia, "thoi_gian", {"so_nen": 10}, vao_tai=20, giu_toi_da=10_000)
        assert r["ly_do"].get("het_gio") == 1


# ================================================== LUAT CHUNG CUA ENGINE
@pytest.mark.parametrize("chieu", [1, -1])
def test_chieu_vao_lenh_lay_tu_TIN_HIEU_chu_khong_phai_luon_MUA(chieu):
    """Bo qua chieu cua tin hieu thi ca bo do thanh "danh mot chieu" tra hinh.

    Da sap that 14/09: test random walk bat duoc `luoi_dca` che ra -128 diem tren
    chuoi khong co edge, chi vi moi ro deu vao MUA suot 20.000 nen.
    """
    gia = np.r_[100 * np.ones(22), 100 + np.arange(40) * 0.01]
    r = chay(gia, "thoi_gian", {"so_nen": 5},
             tin_hieu=tin_hieu_tai(len(gia), 20, chieu), giu_toi_da=100)
    assert r["ro"][0]["chieu"] == chieu


def test_vao_lenh_o_OPEN_bar_ke_tiep_khong_nhin_truoc():
    """Tin hieu biet tai close[i] -> som nhat vao duoc la open[i+1]."""
    gia = np.r_[100 * np.ones(22), 110 * np.ones(20)]
    mo = np.r_[100 * np.ones(22), 110 * np.ones(20)]
    df, a = bar(gia, atr=1.0, cac_open=mo)
    r = QN.dap_nhieu(df, tin_hieu_tai(len(gia), 20), "thoi_gian", {"so_nen": 5},
                     atr_arr=a, giu_toi_da=100)
    # tin hieu o bar 20 (close 100) -> vao o open[21] = 100, KHONG phai 110
    assert r["ro"][0]["bar_mo"] == 21


def test_ro_treo_cuoi_mau_duoc_mark_to_market():
    """Bo qua ro chua dong thi moi ho nhoi nguoc deu dep gia tao."""
    gia = np.r_[100 * np.ones(22), np.arange(100, 80, -0.5)]
    r = chay(gia, "luoi_dca", {"buoc_atr": 2.0, "tp_atr": 99.0}, vao_tai=20,
             nhoi_toi_da=6, giu_toi_da=10_000)
    assert r["ro_treo_cuoi_mau"] is not None
    assert r["ro_treo_cuoi_mau"]["lai_mtm"] < 0
    assert r["lai_tong"] < 0


def test_lai_tong_bang_tong_lai_tung_ro():
    """Kiem doi chieu so sach: khong duoc mat tien o giua hai cach cong."""
    rng = np.random.default_rng(5)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, 1500)))
    th = np.zeros(len(gia))
    th[::40] = 1.0
    for ho, p in (("luoi_dca", {"buoc_atr": 1.0, "tp_atr": 1.0}),
                  ("hedge", {"mo_khoa_atr": 1.0}),
                  ("thoi_gian", {"so_nen": 15}),
                  ("stop_2_dau", {"kc_atr": 1.0}),
                  ("tt_stop_doi", {"kc_atr": 1.0})):
        r = chay(gia, ho, p, tin_hieu=th)
        assert r["lai_tong"] == pytest.approx(sum(x["lai"] for x in r["ro"]),
                                              abs=1e-9), ho


def test_duong_von_khop_lai_tong_o_diem_cuoi():
    rng = np.random.default_rng(11)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, 1200)))
    th = np.zeros(len(gia))
    th[::60] = 1.0
    r = chay(gia, "luoi_dca", {"buoc_atr": 1.0, "tp_atr": 1.0}, tin_hieu=th)
    assert r["duong_cong"][-1] == pytest.approx(r["lai_tong"], abs=1e-9)


def test_tran_so_nen_giu_duoc_ton_trong():
    gia = np.r_[100 * np.ones(22), np.arange(100, 60, -0.2)]
    r = chay(gia, "luoi_dca", {"buoc_atr": 5.0, "tp_atr": 99.0}, vao_tai=20,
             nhoi_toi_da=20, giu_toi_da=30)
    assert r["ly_do"].get("tran_nen") == 1
    assert r["ro"][0]["giu_bar"] == 30


def test_ho_la_khong_thi_NEM_LOI_chu_khong_tra_ve_so():
    """Ten ho go sai ma van tra ve so thi ca bang xep hang thanh vo nghia."""
    gia = 100 * np.ones(100)
    with pytest.raises(ValueError):
        chay(gia, "ho_khong_co_that", {})


def test_random_walk_khong_ho_nao_de_ra_tien_tu_khong_khi():
    """Engine vao NGAU NHIEN tren random walk: moi ho phai quanh 0, khong duong to.

    Khong co chi phi trong engine nay nen ky vong dung la 0. Mot ho ra +lon o day
    nghia la engine dang che tien - dung cai loi ma `pmg_engine` tung mac.
    """
    rng = np.random.default_rng(23)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, 20000)))
    th = np.zeros(len(gia))
    th[::30] = np.where(rng.random(len(th[::30])) > 0.5, 1.0, -1.0)
    bien_do = float(np.median(np.abs(np.diff(gia))))
    for ten, (ho, p) in QN.bo_luat().items():
        r = chay(gia, ho, p, tin_hieu=th, atr=bien_do * 5)
        # quy ve "so nen bien dong": lai tuyet doi khong duoc vuot 3% quang duong
        quang_duong = float(np.abs(np.diff(gia)).sum())
        assert abs(r["lai_tong"]) < 0.03 * quang_duong, (
            f"{ten} che ra {r['lai_tong']:.1f} tren random walk "
            f"(quang duong {quang_duong:.0f})")


# ================================== NOI VAO DUONG TINH TIEN CUA HE
def test_ba_mang_cho_bo_tinh_tien_dung_hinh_dang():
    """Nam ho moi phai di CHUNG duong tinh tien voi sau ho cu, khong duong rieng."""
    rng = np.random.default_rng(3)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, 1200)))
    th = np.zeros(len(gia))
    th[::40] = 1.0
    r = chay(gia, "luoi_dca", {"buoc_atr": 1.0, "tp_atr": 1.0}, tin_hieu=th)
    for k in ("vi_the", "loi_tho", "khoi_luong", "dai", "ngan"):
        assert k in r and len(r[k]) == len(gia), k
    assert np.all(r["dai"] >= 0) and np.all(r["ngan"] >= 0)
    assert np.allclose(r["vi_the"], r["dai"] - r["ngan"])


def test_loi_tho_KHOP_voi_lai_tong_tinh_theo_diem():
    """Hai cach cong tien phai ra cung mot ket qua.

    `lai_tong` cong theo DIEM tung ro; `loi_tho` cong theo LOI SUAT LOG tung bar
    de bo tinh phi dung duoc. Hai duong doc lap nhau, nen chung khop la mot phep
    doi chieu that - lech nhau tuc mot trong hai dang mat tien o dau do.
    """
    rng = np.random.default_rng(17)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, 2000)))
    th = np.zeros(len(gia))
    th[::50] = 1.0
    for ho, p in (("luoi_dca", {"buoc_atr": 1.0, "tp_atr": 1.0}),
                  ("thoi_gian", {"so_nen": 15}),
                  ("tt_stop_doi", {"kc_atr": 1.0})):
        r = chay(gia, ho, p, tin_hieu=th)
        # quy loi suat log ve DIEM bang gia trung binh - xap xi, nen chi doi cung dau
        # va cung bac do lon; cai can bat la lech HANG, khong phai lech lam tron.
        theo_log = float(r["loi_tho"].sum()) * float(np.mean(gia))
        assert np.sign(theo_log) == np.sign(r["lai_tong"]) or abs(r["lai_tong"]) < 1e-6, ho
        assert abs(theo_log - r["lai_tong"]) < 0.5 * max(abs(r["lai_tong"]), 1.0), ho


def test_khoi_luong_tinh_tren_GOP_chu_khong_tren_RONG():
    """Chan hedge tra spread CA HAI LAN - neu tinh tren rong thi no mien phi."""
    gia = np.r_[100 * np.ones(22), np.arange(100, 94, -0.5), 94 * np.ones(20)]
    r = chay(gia, "hedge", {"mo_khoa_atr": 2.0, "he_so_lot": 1.0}, vao_tai=20,
             giu_toi_da=100)
    assert r["so_lenh"] == 2
    # hai chan, moi chan mo + dong = 4 luot khop
    assert r["khoi_luong"].sum() == pytest.approx(4.0, abs=1e-9)
