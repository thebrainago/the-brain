# -*- coding: utf-8 -*-
"""Test: bay chi bao them vao bo dich MQL5 ngay 15/09/2026.

## Vi sao dot nhien phai them

Do 15/09: **563/3216 co che hop le trong kho khong ra noi MT5 tester** vi bo
dich thieu chi bao. `lab/CLAUDE.md` noi tester la trong tai - nen mot co che
khong dich duoc la vo hinh voi thu duy nhat tinh tien, va no vo hinh trong im
lang: bang ket qua chi ngan di, khong ai bao gi.

Sau khi bu: 226. Go duoc 337 co che.

## Bo test nay giu gi

Khong giu "ma sinh ra co dep khong". Giu ba thu de hong nhat, ma neu hong thi
KHONG AI THAY:

  1. **Dich MOT BAR cua `donchian`.** Kenh phai tinh tren n bar TRUOC. Quen
     `s+1` thi `gia >= donchian_tren` LUON DUNG o moi dinh moi, va no hien ra
     thanh mot he "bat dinh" rat dep - nhin truoc kin nhat trong ho nay.
  2. **Cai gi lech quy uoc thi TU CHOI, khong dich gan dung.** `macd` lay
     duong tin hieu, `cci` tren `ohlc4`, `keltner` cua bieu thuc long: ba cho
     nay deu co mot ham MT5 "gan giong". Dich gan dung sinh ra mot EA KHAC voi
     khai bao - van chay, van ra so, va con so do noi ve mot co che khong ai
     viet.
  3. **Gioi han danh sach phai KHOP ban Python.** `tb_cua_cac` cat o 24,
     `tuyen_tinh` cat o 12. Lech gioi han thi hai ben chi lech tren nhung cay
     dai, tuc lech trong im lang.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import dich_mq5 as D   # noqa: E402


def _ma(t: dict) -> str:
    """Ma MQL5 sinh ra cho mot toan hang."""
    b = D.BoDich()
    b.toan_hang(t)
    kb, kt = b.khai_bao_chi_bao()
    return "\n".join(b.ham) + "\n" + kb + "\n" + kt


# ------------------------------------------------------------- DONCHIAN
def test_donchian_DICH_MOT_BAR():
    """Thieu `s+1` = nhin truoc. Day la bai kiem quan trong nhat tep nay."""
    m = _ma({"chi_bao": "donchian", "n": 20, "lay": "tren"})
    assert "iHighest" in m
    assert "s+1" in m, ("donchian khong dich bar - `gia >= kenh tren` se LUON "
                        "dung o moi dinh moi")


@pytest.mark.parametrize("lay", ["tren", "duoi", "giua", "do_rong", "vi_tri"])
def test_donchian_dich_duoc_moi_bien_the_ngu_phap_noi_duoc(lay):
    """Ngu phap noi duoc 5 bien the; thieu cai nao la cai do vo hinh voi tester."""
    assert _ma({"chi_bao": "donchian", "n": 20, "lay": lay}).strip()


def test_donchian_lay_la_khong_biet_thi_NEM_chu_khong_doan():
    with pytest.raises(D.KhongDichDuoc):
        _ma({"chi_bao": "donchian", "n": 20, "lay": "khong_co_kieu_nay"})


# ------------------------------------------------------------- KELTNER
@pytest.mark.parametrize("lay", ["giua", "tren", "duoi", "do_rong", "phan_tram_b"])
def test_keltner_dich_duoc_moi_bien_the(lay):
    m = _ma({"chi_bao": "keltner", "n": 20, "k": 2.0, "lay": lay})
    assert "iATR" in m and "MODE_EMA" in m


def test_keltner_cua_bieu_thuc_long_thi_TU_CHOI():
    """`iMA` chi lay duoc tu GIA. Dich `cua` thanh close la doi khai bao."""
    with pytest.raises(D.KhongDichDuoc):
        _ma({"chi_bao": "keltner", "n": 20,
             "cua": {"chi_bao": "rsi", "n": 14}, "lay": "tren"})


# ------------------------------------------------------------------ CCI
def test_cci_mac_dinh_la_typical_price():
    assert "PRICE_TYPICAL" in _ma({"chi_bao": "cci", "n": 20})


def test_cci_tren_close_dung_PRICE_CLOSE():
    assert "PRICE_CLOSE" in _ma({"chi_bao": "cci", "n": 20, "cot": "close"})


def test_cci_tren_ohlc4_thi_TU_CHOI():
    """`PRICE_WEIGHTED` cua MT5 la (h+l+2c)/4, KHONG phai (o+h+l+c)/4.

    Hai cong thuc khac nhau ma cung mot cai ten "gia trong so" - dung cai bay
    de dich gan dung nhat trong ca tep nay.
    """
    with pytest.raises(D.KhongDichDuoc):
        _ma({"chi_bao": "cci", "n": 20, "cot": "ohlc4"})


# ------------------------------------------------------------------ ADX
@pytest.mark.parametrize("lay,buf", [("adx", 0), ("di_duong", 1), ("di_am", 2)])
def test_adx_doc_dung_buffer(lay, buf):
    """ADX co ba duong. Truoc 15/09 bo dich chi doc duoc buffer 0."""
    m = _ma({"chi_bao": "adx", "n": 14, "lay": lay})
    assert "iADX" in m
    assert ", %d, s)" % buf in m, "doc nham duong cua ADX"


def test_ham_doc_buffer_bat_ky_co_ton_tai():
    """`ChiB` la cai mo khoa moi chi bao NHIEU DUONG ve sau."""
    ma, _ = D.sinh_ea([{
        "ten": "thu_adx", "ho": "xu_huong", "chieu": 1, "giu": 1,
        "co_che": "Chi de kiem duong dich, khong dang ky vao he.",
        "vao": [{"trai": {"chi_bao": "adx", "n": 14, "lay": "di_duong"},
                 "phep": ">", "phai": {"hang": 25.0}}], "ra": []}],
        ten="ThuEA", khung="H4")
    assert "double ChiB(" in ma
    assert "CopyBuffer(h, buf" in ma


# --------------------------------------------------------------- MACD
def test_macd_duong_chinh_la_HIEU_HAI_EMA():
    m = _ma({"chi_bao": "macd", "nhanh": 12, "cham": 26})
    assert m.count("MODE_EMA") == 2, "macd phai dung dung hai duong EMA"


def test_macd_duong_TIN_HIEU_thi_TU_CHOI():
    """Duong tin hieu la EMA CUA CHINH duong MACD - `iMA` khong lay duoc.

    `iMACD` co san mot duong tin hieu, nhung quy uoc cua no khong chac trung
    voi `MAU_MOD.ema` cua ta. Lay bua = mot EA khac voi khai bao.
    """
    for lay in ("tin_hieu", "hieu"):
        with pytest.raises(D.KhongDichDuoc):
            _ma({"chi_bao": "macd", "lay": lay})


# --------------------------------------------------- STOCHASTIC / DONG LUONG
def test_stochastic_KHONG_dich_bar():
    """Khac `donchian`: ban Python o day khong `.shift(1)`.

    Hai chi bao cung ho nhung mot cai dich bar con cai kia thi khong. Chep quy
    uoc tu cai nay sang cai kia la mot cach lam lech im lang.
    """
    m = _ma({"chi_bao": "stochastic", "n": 14})
    assert "MODE_HIGH, 14, s)" in m and "MODE_LOW, 14, s)" in m
    assert "s+1" not in m


def test_stochastic_khong_dung_iStochastic():
    """`iStochastic` con co `slowing`; hai ben chi trung khi slowing = 1."""
    assert "iStochastic" not in _ma({"chi_bao": "stochastic", "n": 14})


def test_dong_luong_la_hieu_voi_chinh_no_n_bar_truoc():
    m = _ma({"chi_bao": "dong_luong", "n": 10})
    assert "s+10" in m and "-" in m


# ------------------------------------------------------------ NHOM GOP
def test_tb_cua_cac_la_trung_binh_that_khong_phai_mot_duong_xap_xi():
    """GMMA = mean(EMA3..EMA15). Mot DAI bo qua khi cac duong phan ky."""
    m = _ma({"chi_bao": "tb_cua_cac",
             "toan_hang": [{"chi_bao": "ema", "n": n} for n in (3, 5, 7)]})
    assert "/ 3.0" in m


def test_cao_nhat_va_thap_nhat_cua_cac():
    a = _ma({"chi_bao": "cao_nhat_cua_cac",
             "toan_hang": [{"chi_bao": "ema", "n": 3}, {"chi_bao": "ema", "n": 5}]})
    b = _ma({"chi_bao": "thap_nhat_cua_cac",
             "toan_hang": [{"chi_bao": "ema", "n": 3}, {"chi_bao": "ema", "n": 5}]})
    assert "MathMax" in a and "MathMin" in b


def test_nhom_GOP_cat_o_24_giong_ban_Python():
    """Ban Python cat `ds[:24]`. Lech gioi han = lech tren dung cac cay dai."""
    m = _ma({"chi_bao": "tong_cua_cac",
             "toan_hang": [{"chi_bao": "ema", "n": n} for n in range(2, 40)]})
    assert m.count("F") > 0
    than = [h for h in m.split("double ") if "return(F1(s)" in h]
    assert than, "khong thay ham gop"
    assert than[0].count("(s)") == 24, "nhom GOP khong cat o 24 nhu ban Python"


def test_tuyen_tinh_cat_o_12_giong_ban_Python():
    b = D.BoDich()
    b.toan_hang({"chi_bao": "tuyen_tinh",
                 "toan_hang": [{"chi_bao": "ema", "n": n} for n in range(2, 30)],
                 "he_so": [1.0] * 28})
    assert b.ham[-1].count(") * F") == 12, "tuyen_tinh khong cat o 12"


def test_tuyen_tinh_he_so_lech_do_dai_thi_NEM():
    with pytest.raises(D.KhongDichDuoc):
        _ma({"chi_bao": "tuyen_tinh",
             "toan_hang": [{"chi_bao": "atr", "n": 14}], "he_so": [1.0, 2.0]})


# ------------------------------------------------- DO PHU CUA BO DICH
def test_do_phu_bo_dich_khong_duoc_TUT_XUONG():
    """Cai chan neo: bo dich da phu 2.991/3.217 co che. Khong duoc lui.

    Con so nay la ket qua cua mot buoi bu chi bao; mot lan "don dep" vo y lam
    no tut lai se khong bao loi gi - chi lam bang ket qua tester ngan di.
    """
    from nhan import ngu_phap as NP
    kho = [c for c in NP.doc_kho() if not NP.kiem_khai_bao(c)]
    if len(kho) < 2000:
        pytest.skip("kho qua nho - khong phai may co du lieu that")
    _, dat = D.sinh_ea(kho, "DoPhu", khung="H4")
    ty = len(dat) / len(kho)
    assert ty >= 0.88, ("bo dich chi con phu %.1f%% kho (truoc do 93%%) - co "
                        "che khong dich duoc la vo hinh voi tester" % (100 * ty))


# ================ MAU NEN (them 15/09/2026) - 135 co che ket ngoai tester
@pytest.mark.parametrize("mau", ["nen_dac", "rau_tren", "rau_duoi", "doji",
                                 "bua", "sao_bang", "trong", "ngoai",
                                 "nhan_chim", "ba_nen"])
def test_dich_duoc_MOI_mau_nen_ngu_phap_noi_duoc(mau):
    """135 co che dung `mau_nen`, va truoc 15/09 khong cai nao ra noi tester.

    Mot dong nguyen trong so do cua chu du an (*"Cac dang nen khac nhau"*) chua
    bao gio duoc trong tai cham.
    """
    m = _ma({"chi_bao": "mau_nen", "mau": mau})
    assert "iOpen" in m and "iHigh" in m


def test_mau_nen_KHONG_chia_cho_khong():
    """Bar khong bien do (`h == l`) phai tra 0, khong phai chia cho khong."""
    for mau in ("nen_dac", "doji", "bua", "ba_nen"):
        m = _ma({"chi_bao": "mau_nen", "mau": mau})
        assert "<= 0.0) return(0.0)" in m, mau


def test_mau_nen_la_khong_biet_thi_NEM():
    with pytest.raises(D.KhongDichDuoc):
        _ma({"chi_bao": "mau_nen", "mau": "khong_co_mau_nay"})


def test_BUA_va_RAU_DUOI_la_CUNG_MOT_THU():
    """Trong mot nen, `duoi/bien + tren/bien + |than|/bien` == 1, nen

        bua = duoi/bien - tren/bien - |than|/bien = 2*(duoi/bien) - 1

    tuc mot bien doi TUYEN TINH TANG cua `rau_duoi`. Sau `phan_vi` chung xep
    hang y het nhau. Do 15/09 tren AUDCAD H4: lech toi da 1,1e-16, Spearman
    1,000000, va tester cho DUNG cung so lenh / cung lai.

    Giu bai kiem nay de khong ai doc hai ket qua do nhu HAI XAC NHAN DOC LAP.
    """
    import numpy as np
    import pandas as pd
    from nhan import ngu_phap as NP
    r = np.random.default_rng(0)
    n = 500
    c = 100 + np.cumsum(r.normal(0, 1, n))
    o = c + r.normal(0, 0.5, n)
    h = np.maximum(o, c) + np.abs(r.normal(0, 0.5, n))
    l = np.minimum(o, c) - np.abs(r.normal(0, 0.5, n))
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                      index=pd.date_range("2020-01-01", periods=n, freq="h"))
    bua = np.asarray(NP.toan_hang(df, {"chi_bao": "mau_nen", "mau": "bua"}), float)
    rd = np.asarray(NP.toan_hang(df, {"chi_bao": "mau_nen", "mau": "rau_duoi"}), float)
    ok = np.isfinite(bua) & np.isfinite(rd)
    assert np.nanmax(np.abs(bua[ok] - (2 * rd[ok] - 1))) < 1e-12
    sb = np.asarray(NP.toan_hang(df, {"chi_bao": "mau_nen", "mau": "sao_bang"}), float)
    rt = np.asarray(NP.toan_hang(df, {"chi_bao": "mau_nen", "mau": "rau_tren"}), float)
    ok2 = np.isfinite(sb) & np.isfinite(rt)
    assert np.nanmax(np.abs(sb[ok2] - (2 * rt[ok2] - 1))) < 1e-12


def test_tester_GOP_co_che_trung_hanh_vi_truoc_khi_chay():
    """`loc_co_che._van_tay_hanh_vi` CO tu truoc va chay dung - nhung
    `chay_tester_kho` doc thang kho nen chua bao gio thay no.

    Do 15/09 tren AUDCAD H4: **616/3.236 co che (19,0%) sinh ra chuoi tin hieu
    Y HET mot co che khac**. Cai dat khong phai luot tester thua ma la hai co
    che giong het nhau trong nhu hai xac nhan doc lap.
    """
    import chay_tester_kho as C
    assert hasattr(C, "_gop_trung_hanh_vi")
    s = (LAB / "chay_tester_kho.py").read_text(encoding="utf-8-sig")
    i = s.index("def _chay_trong_khoa")
    j = s.index("ma, dat = D.sinh_ea(", i)
    assert "_gop_trung_hanh_vi" in s[i:j], (
        "gop trung hanh vi khong nam TRUOC luc sinh EA")


def test_gop_trung_hanh_vi_KHONG_do_duoc_thi_CHO_CHAY():
    """Khong nap duoc du lieu thi tra nguyen kho - dung chan mu."""
    import chay_tester_kho as C
    kho = [{"ten": "a"}, {"ten": "b"}]
    moi, bd = C._gop_trung_hanh_vi(kho, "MA_KHONG_CO_THAT_XYZ", "H4")
    assert len(moi) == 2 and bd == {}
