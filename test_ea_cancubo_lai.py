# -*- coding: utf-8 -*-
"""Kiem `ea_cancubo_lai`: bot "Can Cu Bu Sieng Nang" tren vang, dung lai tu deal tester that.

Ba tang:
  1. Ham thuan (khong can trinh bien dich): gom chuoi tu bang vi the, gio vao, kiem co che tren chuoi tu che, so hai bang chuoi, duong gia toi thieu.
  2. KICH BAN TINH TAY tren EA `ea_CanCuBoLai.mq5` chay tren san gia C++ (can g++/clang++): moi quy tac co mot con so ra bang tay
     (TP 100 pip, bac thang SL 15 + 2k, DCA dung 100 pip tinh tu lenh SAU CUNG, lot 0,01 * 1,05^(n-1) lam tron, TP chuoi 200 pip,
     trung binh theo lot, lam tron NUA CENT LEN, bo cua vao khi chuoi dang mo...). Bien the `CCBL_MAU` (file mau EA) dung cho thu dot bien.
  3. Vong kin tren 2.244 chuoi THAT cua hai lan chay tester (reports/fixture): EA tai tao dung tung chuoi.

Kiem DOT BIEN (09/10/2026, `CCBL_MAU` + 94 dot bien van ban cua `EA_MAU`): 89 bi bat, 5 TUONG DUONG theo cau tao (doi ma ma KHONG doi
hanh vi quan sat duoc, nen khong the bat - khong phai lo hong cua bo test):
  vao.khop_le          `G_VAO[i] == nen` -> `<=`: vong while ngay tren da bo moi gio vao < nen, nen G_VAO[i] >= nen luon dung
  tick.khong_gan_nen   bo `g_nen = nen`: XuLyVao chay lai o MOI tick nhung da lap lai vo hai (g_ivao da vuot gio vao cua nen do) - chi cham hon
  tick.khong_ra_khi_0  bo `if(g_n == 0) return`: khi khong co lenh, khong co vi the nao de DongBo sua va g_cuoi = 0 nen DCA khong the kich hoat
  dca.nho_hon          `ask <= moc - 100 pip + 1e-9` -> `<`: ask va moc deu la so nguyen diem, 1e-9 < 1 diem nen hai phep so sanh trung nhau
  sl.bat_dau_lon_hon   `loi + 1e-9 >= 30 pip` -> `>`: cung ly do, dung tai ngay 30,0 pip ca hai deu cho bac thang SL dau
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import ea_cancubo_lai as C
from nhan import ea_gia_lap as G

T = pd.Timestamp
can_cxx = pytest.mark.skipif(G.trinh_bien_dich() is None, reason="khong co g++ / clang++ (hoac EA_GIA_LAP_CXX)")
co_deal = pytest.mark.skipif(not (C.DEAL_KP.exists() and C.DEAL_XN.exists()), reason="thieu deal tester trong reports/fixture")
T0 = 1_700_000_000 - (1_700_000_000 % 3600)      # gio tron
VAO_CHUNG = sorted({T0 + 3600 * j + d for j in range(40) for d in (0, 420)})   # 2 gio vao moi gio: +0 va +420 giay (phut 7: ngoai luoi M5)


def _mau():
    """Mau EA: mac dinh `C.EA_MAU`; harness dot bien dat CCBL_MAU = duong dan file mau da bi sua."""
    f = os.environ.get("CCBL_MAU")
    return Path(f).read_text(encoding="utf-8") if f else None


# ----------------------------------------------------------------------------------------------------------------- dung cu
def vt(mo, dong, lot=0.01, gia_mo=2000.0, gia_dong=2001.0, ly="sl", loi=None, dv=0):
    """Mot dong bang vi the cung dang `lenh_tester.vi_the_tu_tep` (chi cac cot chuoi dung)."""
    return dict(mo=T(mo), dong=T(dong) if dong else pd.NaT, lot=lot, gia_mo=gia_mo, gia_dong=gia_dong,
                loi=(gia_dong - gia_mo) * lot * 100 if loi is None else loi, ly_do_ra=ly, deal_vao=dv)


def bang(*dong):
    d = pd.DataFrame(list(dong))
    d["deal_vao"] = range(len(d))
    return d


# ----------------------------------------------------------------------------------------------------------------- 1. ham thuan
def test_chuoi_tu_vi_the_tach_va_gop():
    v = bang(
        vt("2020-01-01 10:00:00", "2020-01-01 12:00:00", 0.01, 2000.0, 2001.5),                                   # chuoi 0, 1 lenh
        vt("2020-01-02 10:00:00", "2020-01-03 12:00:40", 0.01, 2000.0, 1999.0, loi=-1.0),                         # chuoi 1: lenh dau
        vt("2020-01-02 15:10:40", "2020-01-03 12:00:40", 0.01, 1990.0, 1999.0),                                   # ... DCA, chong len nhau
        vt("2020-01-04 09:00:00", "2020-01-04 09:10:20", 0.02, 1990.0, 1992.0))                                   # chuoi 2
    ch = C.chuoi_tu_vi_the(v)
    assert list(ch["n"]) == [1, 2, 1]
    assert list(ch["id"]) == [0, 1, 2]
    assert ch["lot"].tolist() == pytest.approx([0.01, 0.02, 0.02])
    assert ch["gia_vao"].tolist() == [2000.0, 2000.0, 1990.0]
    assert ch["gia_tb"].iloc[1] == pytest.approx(1995.0)                    # trung binh co trong so lot cua 2000 va 1990
    assert ch["gia_thap"].iloc[1] == 1990.0
    assert ch["gia_ra"].iloc[1] == pytest.approx(1999.0)
    assert ch["dong"].iloc[1] == T("2020-01-03 12:00:40")
    assert ch["gia_cac_lenh"].iloc[1] == [2000.0, 1990.0] and ch["lot_cac_lenh"].iloc[1] == [0.01, 0.01]
    assert ch["loi"].iloc[1] == pytest.approx(-1.0 + 9.0)


def test_chuoi_trung_trong_so_lot_va_gia_ra():
    v = bang(vt("2020-01-01 10:00:00", "2020-01-01 11:00:00", 0.01, 2000.0, 2010.0),
             vt("2020-01-01 10:30:40", "2020-01-01 11:00:00", 0.03, 1900.0, 2010.0))
    c = C.chuoi_tu_vi_the(v).iloc[0]
    assert c["gia_tb"] == pytest.approx((2000 * 0.01 + 1900 * 0.03) / 0.04)
    assert c["gia_ra"] == pytest.approx(2010.0) and c["lot"] == pytest.approx(0.04)


def test_chuoi_lenh_mo_cung_giay_voi_lan_dong_cuoi_van_la_mot_chuoi():
    v = bang(vt("2020-01-01 10:00:00", "2020-01-01 11:00:00"), vt("2020-01-01 11:00:00", "2020-01-01 12:00:00"),
             vt("2020-01-01 12:00:01", "2020-01-01 13:00:00"))
    assert list(C.chuoi_tu_vi_the(v)["n"]) == [2, 1]


def test_chuoi_lenh_con_mo_cuoi_cua_so_la_het_gio():
    v = bang(vt("2020-01-01 10:00:00", "2020-01-01 11:00:00"), vt("2020-01-01 12:00:00", None, gia_dong=np.nan, ly="open", loi=np.nan))
    ch = C.chuoi_tu_vi_the(v)
    assert list(ch["ly_do"]) == ["sl", "het_gio"]
    assert pd.isna(ch["dong"].iloc[1]) and pd.isna(ch["gia_ra"].iloc[1])


def test_chuoi_con_mo_nhieu_lenh_cuoi_cua_so_van_la_MOT_chuoi():
    """Truoc 09/10/2026 moc 'mo mai' la nam 9999 -> tran int64 ns (thanh 1815) nen chuoi dang DCA chua dong bi cat thanh nhieu chuoi n=1."""
    v = bang(vt("2020-01-01 10:00:00", "2020-01-01 11:00:00"),
             vt("2020-01-01 12:00:00", None, gia_dong=np.nan, ly="open", loi=np.nan),
             vt("2020-01-02 03:00:00", None, gia_mo=1990.0, gia_dong=np.nan, ly="open", loi=np.nan),
             vt("2020-02-03 03:00:00", None, gia_mo=1980.0, gia_dong=np.nan, ly="open", loi=np.nan))
    ch = C.chuoi_tu_vi_the(v)
    assert list(ch["n"]) == [1, 3] and list(ch["ly_do"]) == ["sl", "het_gio"]
    assert ch["gia_cac_lenh"].iloc[1] == [2000.0, 1990.0, 1980.0]


def test_chuoi_bang_rong():
    ch = C.chuoi_tu_vi_the(pd.DataFrame())
    assert len(ch) == 0 and list(ch.columns) == C.COT_CHUOI


def test_chuoi_ly_do_la_cua_lan_dong_cuoi():
    v = bang(vt("2020-01-01 10:00:00", "2020-01-01 11:00:00", ly="tp"), vt("2020-01-01 10:20:00", "2020-01-01 11:00:20", ly="sl"))
    assert C.chuoi_tu_vi_the(v)["ly_do"].iloc[0] == "sl"


def test_thoi_diem_vao_cat_phut_va_sap_xep():
    v = bang(vt("2020-01-01 10:07:00", "2020-01-01 11:00:00"), vt("2020-01-01 10:07:40", "2020-01-01 11:00:00", gia_mo=1990.0),
             vt("2020-01-02 09:01:30", "2020-01-02 10:00:00"))
    ch = C.chuoi_tu_vi_the(v)
    assert C.thoi_diem_vao(ch) == [int(T("2020-01-01 10:07:00").value // 10 ** 9), int(T("2020-01-02 09:01:00").value // 10 ** 9)]


def _chuoi_gia(n=1, lots=None, gias=None, vao="2020-01-01 10:00:00", ra="2020-01-01 12:00:40", ly="sl", gia_ra=2001.5, loi=1.5):
    lots = lots or C._lot_du_kien(n, C.THAM_SO_GOC)
    gias = gias or [2000.0 - 10.0 * i for i in range(n)]
    tb = sum(a * b for a, b in zip(lots, gias)) / sum(lots)
    return dict(id=0, mo=T(vao), dong=T(ra), n=n, lot=sum(lots), gia_vao=gias[0], gia_tb=tb, gia_thap=min(gias), gia_ra=gia_ra, ly_do=ly,
                loi=loi, lot_cac_lenh=lots, gia_cac_lenh=gias, gio_cac_lenh=[T(vao)] * n)


def _kiem(*chuoi):
    d = pd.DataFrame(list(chuoi))
    return C.kiem_co_che(d)


def test_kiem_co_che_chuoi_dung_khong_vi_pham():
    c1 = _chuoi_gia(1, gia_ra=2000.0 + 1.5)                                        # SL +15 pip
    c2 = _chuoi_gia(2, gias=[2000.0, 1990.0], gia_ra=1995.0 + 1.9)                 # SL +19 pip (15 + 2 * 2)
    c3 = _chuoi_gia(1, gia_ra=2010.0, ly="tp")                                     # TP 100 pip
    c4 = _chuoi_gia(2, gias=[2000.0, 1990.0], gia_ra=1995.0 + 20.0, ly="tp")       # TP 200 pip
    k = _kiem(c1, c2, c3, c4)
    assert (k["lot_sai"], k["dca_duoi_buoc"], k["sl_ngoai_luoi"], k["sl_duoi_khoi"], k["sl_vuot_tp"], k["tp_lech"]) == (0, 0, 0, 0, 0, 0)
    assert k["dca_n"] == 2 and k["dca_min_pip"] == pytest.approx(100.0) and k["sl_n"] == 2 and k["tp_n"] == 2
    assert k["tp_theo_do_sau"] == {1: 1, 2: 1}


@pytest.mark.parametrize("sua,truong", [
    (dict(lots=[0.01, 0.02], gias=[2000.0, 1990.0], n=2, gia_ra=1996.9), "lot_sai"),                  # lot thu hai phai 0,01
    (dict(gias=[2000.0, 1990.5], n=2, gia_ra=1995.25 + 1.5), "dca_duoi_buoc"),                        # DCA o -95 pip
    (dict(gia_ra=2001.6), "sl_ngoai_luoi"),                                                           # 16 pip khong thuoc 15 + 2k
    (dict(gia_ra=1999.0), "sl_duoi_khoi"),                                                            # thoat SL o -10 pip: duoi 15
    (dict(gia_ra=2010.5), "sl_vuot_tp"),                                                              # thoat SL o +105 pip khi TP = 100
    (dict(gia_ra=2009.0, ly="tp"), "tp_lech"),                                                        # TP o 90 pip
])
def test_kiem_co_che_bat_tung_vi_pham(sua, truong):
    k = _kiem(_chuoi_gia(**sua))
    assert k[truong] >= 1, k


def test_kiem_co_che_lo_va_do_sau():
    k = _kiem(_chuoi_gia(loi=-3.0), _chuoi_gia(1, loi=2.0, vao="2020-01-02 10:00:00", ra="2020-01-02 11:00:00"))
    assert k["lo"] == 1 and k["loi_min"] == -3.0 and k["do_sau_max"] == 1


def test_duong_tu_chuoi_sl_dinh_giua_bac_thang_va_chuoi_khong_dung_lai_bi_bo():
    sl = _chuoi_gia(1, vao="2020-01-01 10:00:00", ra="2020-01-01 12:00:40", gia_ra=2001.9)         # +19 pip
    tp = _chuoi_gia(1, vao="2020-01-02 10:00:00", ra="2020-01-02 10:20:20", gia_ra=2010.0, ly="tp")
    ea = _chuoi_gia(1, vao="2020-01-03 10:00:00", ra="2020-01-03 10:20:00", ly="ea")
    d = pd.DataFrame([sl, tp, ea])
    d["id"] = [0, 1, 2]
    tk, bo = C.duong_tu_chuoi(d)
    assert bo == [2]
    assert list(tk["loai"]) == ["vao", "dinh", "sl", "vao", "tp"]
    gia = dict(zip(tk["loai"], tk["bid"]))
    assert tk["bid"][1] == pytest.approx(2000.0 + (19 + 15.5) * 0.1)             # dinh = bac + 15,5 pip: trong [bac + 15, bac + 17)
    assert tk["bid"][2] == pytest.approx(2001.9 - 0.5)                           # tick cuoi duoi muc SL 5 pip
    assert tk["bid"][4] == pytest.approx(2010.0 + 0.5)                           # tick cuoi tren muc TP 5 pip
    assert tk["time"][1] == tk["time"][2] - 1 and (np.diff(tk["time"]) >= 0).all()
    assert tk["spread"].tolist() == [0.0] * 5 and (tk["bar"] % 60 == 0).all()


def test_duong_tu_chuoi_tu_choi_id_trung_va_chuoi_chong_nhau():
    a = _chuoi_gia(1, vao="2020-01-01 10:00:00", ra="2020-01-01 12:00:40")
    b = _chuoi_gia(1, vao="2020-01-01 11:00:00", ra="2020-01-01 13:00:40")
    with pytest.raises(ValueError, match="duy nhat"):
        C.duong_tu_chuoi(pd.DataFrame([a, b]))
    d = pd.DataFrame([a, b])
    d["id"] = [0, 1]
    with pytest.raises(ValueError, match="chong len nhau"):
        C.duong_tu_chuoi(d)


def test_viet_ea_mang_vao_dinh_dang_va_kiem_tra_dau_vao(tmp_path):
    p = C.viet_ea([T0, T0 + 60, T0 + 120], tmp_path / "ea.mq5", mau=_mau())
    ma = p.read_text(encoding="utf-8")
    assert "long     G_VAO[]" in ma and "%d,%d,%d" % (T0, T0 + 60, T0 + 120) in ma.replace("\n", "").replace(" ", "")
    assert "__VAO__" not in ma
    with pytest.raises(ValueError, match="tang dan"):
        C.viet_ea([5, 5], tmp_path / "x.mq5")
    with pytest.raises(ValueError, match="tang dan"):
        C.viet_ea([6, 5], tmp_path / "x.mq5")
    with pytest.raises(ValueError, match="__VAO__"):
        C.viet_ea([1], tmp_path / "x.mq5", mau="void OnTick(){}")
    m = C.viet_ea([], tmp_path / "rong.mq5").read_text(encoding="utf-8")
    assert "G_VAO[] =\n  {\n   0\n  };" in m


def _hai(*chuoi):
    d = pd.DataFrame(list(chuoi))
    d["id"] = range(len(d))
    return d


def test_so_chuoi_khop_va_tung_loai_lech():
    a = _chuoi_gia(2, gias=[2000.0, 1990.0], gia_ra=1996.9, loi=3.8)
    assert C.so_chuoi(_hai(a), _hai(dict(a)))["khop"] == 1
    cases = {
        "so_lenh": dict(n=1, lot_cac_lenh=[0.01], gia_cac_lenh=[2000.0]),
        "lot": dict(lot_cac_lenh=[0.01, 0.02]),
        "gia_vao": dict(gia_cac_lenh=[2000.0, 1989.9]),
        "gio_ra": dict(dong=T("2020-01-01 12:00:50")),
        "ly_do": dict(ly_do="tp"),
        "gia_ra": dict(gia_ra=1996.92),
        "loi": dict(loi=3.9),
    }
    for truong, sua in cases.items():
        b = dict(a)
        b.update(sua)
        kq = C.so_chuoi(_hai(a), _hai(b))
        assert kq["khop"] == 0 and kq["dem_lech"][truong] == 1, (truong, kq)
        assert kq["chi_tiet"][0]["lech"]


def test_so_chuoi_chuoi_thieu_hai_ben_va_dung_sai():
    a = _chuoi_gia(1)
    b = dict(a, mo=T("2020-01-05 10:00:00"), dong=T("2020-01-05 11:00:00"))
    kq = C.so_chuoi(_hai(a), _hai(b))
    assert kq["chung"] == 0 and len(kq["chi_goc"]) == 1 and len(kq["chi_lai"]) == 1
    nhe = dict(a, gia_ra=a["gia_ra"] + 0.005, dong=a["dong"] + pd.Timedelta(seconds=1), loi=a["loi"] + 0.01)
    assert C.so_chuoi(_hai(a), _hai(nhe))["khop"] == 1                        # trong dung sai lam tron
    # chuoi cung phut mo -> cung khoa, ky tu giay khac van khop
    sau = dict(a, mo=a["mo"] + pd.Timedelta(seconds=30))
    assert C.so_chuoi(_hai(a), _hai(sau))["chung"] == 1


# ----------------------------------------------------------------------------------------------------------------- 2. kich ban tinh tay
@pytest.fixture(scope="module")
def exe(tmp_path_factory):
    if G.trinh_bien_dich() is None:
        pytest.skip("khong co trinh bien dich C++")
    d = tmp_path_factory.mktemp("ccbl")
    mq5 = C.viet_ea(VAO_CHUNG, d / "ea_CanCuBoLai.mq5", mau=_mau())
    e = G.bien_dich(mq5, thu_muc=d / "bin")
    assert e is not None
    return e


def chay(exe, ticks, gio=0, spread=0.0, lot=C.LOT_VANG, **ts):
    """`ticks` = [(giay so voi gio vao thu `gio`, bid)]. Tra (res, bang lenh, thoi gian tick)."""
    base = T0 + 3600 * gio
    t = np.array([base + s for s, _ in ticks], float)
    tk = dict(bid=np.array([b for _, b in ticks], float), spread=np.full(len(ticks), float(spread)), time=t, bar=np.floor(t / 60) * 60,
              bar_idx=np.arange(len(ticks)))
    res = G.chay(exe, tk, 100000.0, tham_so=ts or None, digits=2, hop_dong=C.HOP_DONG, lot=lot)
    assert res["ok"], res
    assert res["kq"]["gia_lech"] == 0, "EA dat SL/TP chua NormalizeDouble %d lan (MT5 that co the tu choi 'Invalid stops')" % res["kq"]["gia_lech"]
    d = res["lenh"]
    if len(d):
        d = d.sort_values(["tick_mo", "ticket"], kind="stable").reset_index(drop=True)      # san ghi theo thu tu DONG; test doc theo thu tu MO
    return res, d, (t - base)


def dong_cuoi(lenh):
    return lenh.iloc[-1]


def tong_ket(res):
    """(so gio vao bi bo vi chuoi dang mo, so gio vao nam truoc cua so) tu dong tong ket OnDeinit - kiem CA HAI so, khong chi mot."""
    m = [re.search(r"bo qua (\d+) gio vao vi chuoi dang mo; (\d+) gio vao nam truoc cua so", x) for x in res["log"]]
    m = [x for x in m if x]
    assert len(m) == 1, res["log"]
    return int(m[0].group(1)), int(m[0].group(2))


def test_tp_mot_lenh_100_pip_khop_dung_muc(exe):
    r, d, t = chay(exe, [(0, 2000.00), (20, 2005.00), (40, 2010.49), (59, 2011.00)])
    assert r["kq"]["n_mo"] == 1 and r["kq"]["n_tp"] == 1 and r["kq"]["n_sl"] == 0
    x = d.iloc[0]
    assert (x["vol"], x["open"], x["close"], x["ly_do"], x["comment"]) == (0.01, 2000.0, 2010.0, "tp", "CCBL|1")
    assert t[int(x["tick_dong"])] == 40 and r["kq"]["balance"] - 100000.0 == pytest.approx(10.0)


def test_tp_chua_cham_thi_khong_thoat(exe):
    r, d, _ = chay(exe, [(0, 2000.00), (20, 2005.00), (40, 2009.99)])          # chi tang: khong ha xuong cham SL truot
    assert r["kq"]["n_dong"] == 0 and r["kq"]["con_mo"] == 1
    r, d, _ = chay(exe, [(0, 2000.00), (20, 2009.99), (40, 2005.00)])          # chua cham TP nhung ve cham SL truot (95 pip -> SL +83)
    assert r["kq"]["n_sl"] == 1 and d.iloc[0]["close"] == 2008.30


def test_vao_lenh_mua_o_ask_va_tp_theo_bid(exe):
    # bid 1999,70 + spread 0,30 -> MUA khop o ASK 2000,00 ; TP = 2010,00 chi cham khi BID cham (ask da 2010,29 o tick 2 ma chua thoat)
    r, d, t = chay(exe, [(0, 1999.70), (20, 2009.99), (40, 2010.00)], spread=0.30)
    x = d.iloc[0]
    assert x["open"] == pytest.approx(2000.00)
    assert r["kq"]["n_tp"] == 1 and x["close"] == pytest.approx(2010.00) and t[int(x["tick_dong"])] == 40


def test_sl_truot_do_loi_theo_bid_chu_khong_theo_ask(exe):
    # vao o ask 2000,30. Loi tinh tren BID: bid 2003,29 -> 29,9 pip (< 30, chua co SL) ; bid 2003,30 -> 30,0 pip -> SL = 2000,30 + 15 pip = 2001,80
    r, d, _ = chay(exe, [(0, 2000.00), (20, 2003.29), (40, 2000.00)], spread=0.30)
    assert r["kq"]["n_dong"] == 0 and r["kq"]["con_mo"] == 1
    r, d, t = chay(exe, [(0, 2000.00), (20, 2003.30), (40, 2001.81)], spread=0.30)
    assert r["kq"]["n_dong"] == 0
    r, d, t = chay(exe, [(0, 2000.00), (20, 2003.30), (40, 2001.80)], spread=0.30)
    assert r["kq"]["n_sl"] == 1 and d.iloc[0]["close"] == pytest.approx(2001.80)


def test_sl_bac_thang_15_cong_2k_pip(exe):
    # loi dinh 33,5 pip -> k = 1 -> SL = tb + 17 pip = 2001,70 ; gia ve 2001,65 -> thoat DUNG o 2001,70
    r, d, t = chay(exe, [(0, 2000.00), (20, 2003.35), (40, 2001.65)])
    x = d.iloc[0]
    assert (x["ly_do"], x["close"]) == ("sl", 2001.70) and r["kq"]["n_sl"] == 1
    assert t[int(x["tick_dong"])] == 40 and r["kq"]["balance"] - 100000.0 == pytest.approx(1.70)


@pytest.mark.parametrize("dinh,muc_sl_pip", [(2003.00, 15), (2003.19, 15), (2003.20, 17), (2003.39, 17), (2003.40, 19), (2003.59, 19),
                                             (2003.60, 21), (2005.00, 35), (2008.00, 65)])
def test_sl_bac_thang_tung_nac(exe, dinh, muc_sl_pip):
    # loi dinh P pip (>= 30) -> SL = tb + 15 + 2 * floor((P - 30) / 2) pip ; gia ve sat tren SL 1 tick -> khong thoat ; ve DUNG SL -> thoat o SL
    gia_sl = round(2000.0 + muc_sl_pip / 10.0, 2)
    r, d, _ = chay(exe, [(0, 2000.00), (20, dinh), (40, round(gia_sl + 0.01, 2))])
    assert r["kq"]["n_dong"] == 0, "thoat som: SL cao hon bac thang %d pip" % muc_sl_pip
    r, d, _ = chay(exe, [(0, 2000.00), (20, dinh), (40, gia_sl)])
    assert r["kq"]["n_sl"] == 1 and d.iloc[0]["close"] == gia_sl


def test_sl_chua_bat_duoi_30_pip(exe):
    r, d, _ = chay(exe, [(0, 2000.00), (20, 2002.99), (40, 1999.00), (59, 1995.00)])
    assert r["kq"]["n_sl"] == 0 and r["kq"]["n_mo"] == 1 and r["kq"]["con_mo"] == 1


def test_sl_chi_doi_len_mac_dinh_va_bam_theo_khi_tat_ratchet(exe):
    ticks = [(0, 2000.00), (20, 2004.00), (40, 2003.60), (59, 2002.30)]
    r, d, _ = chay(exe, ticks)                                                # ratchet: SL giu o 2002,50 (dinh 40 pip)
    assert r["kq"]["n_sl"] == 1 and d.iloc[0]["close"] == 2002.50
    r, d, _ = chay(exe, ticks, InpTrailRatchet=0)                             # bam theo: SL ha xuong 2002,10 -> 2002,30 chua cham
    assert r["kq"]["n_sl"] == 0 and r["kq"]["con_mo"] == 1


def test_dca_dung_100_pip_tu_lenh_truoc_va_tp_200_pip(exe):
    r, d, t = chay(exe, [(0, 2000.00), (20, 1990.00), (40, 2015.49)])
    assert r["kq"]["n_mo"] == 2 and r["kq"]["n_tp"] == 2
    assert d["open"].tolist() == [2000.0, 1990.0] and d["vol"].tolist() == [0.01, 0.01] and d["comment"].tolist() == ["CCBL|1", "CCBL|2"]
    assert d["close"].tolist() == [2015.0, 2015.0]                           # tb = 1995 -> TP = tb + 200 pip
    assert r["kq"]["balance"] - 100000.0 == pytest.approx(40.0)


def test_dca_khong_som_hon_100_pip(exe):
    r, d, _ = chay(exe, [(0, 2000.00), (20, 1990.01)])
    assert r["kq"]["n_mo"] == 1
    r, d, _ = chay(exe, [(0, 2000.00), (20, 1990.01), (40, 1990.00)])
    assert r["kq"]["n_mo"] == 2 and d.iloc[1]["open"] == 1990.0


def test_dca_so_voi_ask_chu_khong_bid(exe):
    r, d, _ = chay(exe, [(0, 1999.70), (20, 1989.71)], spread=0.30)           # ask 1990,01 -> chua
    assert r["kq"]["n_mo"] == 1
    r, d, _ = chay(exe, [(0, 1999.70), (20, 1989.70)], spread=0.30)           # ask 1990,00 -> DCA, khop o ask
    assert r["kq"]["n_mo"] == 2 and d.iloc[1]["open"] == pytest.approx(1990.0)


def test_dca_moc_la_gia_mo_lenh_sau_cung(exe):
    # lenh 2 mo o 1985,00 (khop o gia tick, vuot moc 1990 them 50 pip) -> moc tiep = 1985 - 10 = 1975,00.
    # KHONG phai luoi cua lenh dau (1980,00) va KHONG phai gia tb - 10 (1992,5 - 10 = 1982,5).
    cac = [(0, 2000.00), (10, 1985.00), (20, 1982.40), (25, 1980.00), (30, 1975.01)]
    r, d, _ = chay(exe, cac)
    assert r["kq"]["n_mo"] == 2 and d["open"].tolist() == [2000.0, 1985.0]
    r, d, _ = chay(exe, cac + [(40, 1975.00)])
    assert r["kq"]["n_mo"] == 3 and d["open"].tolist() == [2000.0, 1985.0, 1975.0]


def test_chuan_lot_theo_buoc_va_gioi_han_cua_ma(exe):
    # mac dinh InpLot 0,01 -> ma co lot nho nhat 0,05 : keo len 0,05 ; InpLot 0,5 -> chan o lot lon nhat 0,10 ; 0,08 -> lam tron NUA LEN theo buoc 0,05 = 0,10 ; 0,07 -> 0,05
    for in_lot, mong in ((0.01, 0.05), (0.5, 0.10), (0.08, 0.10), (0.07, 0.05)):
        r, d, _ = chay(exe, [(0, 2000.00)], lot=(0.05, 0.10, 0.05), InpLot=in_lot)
        assert r["kq"]["n_mo"] == 1 and d.iloc[0]["vol"] == pytest.approx(mong), (in_lot, d["vol"].tolist())


def test_lot_tang_1_05_mu_n_tru_1_lam_tron_hai_so(exe):
    ticks = [(20 * i, round(2000.0 - 10.0 * i, 2)) for i in range(20)]
    r, d, _ = chay(exe, ticks)
    assert r["kq"]["n_mo"] == 20
    lot = d["vol"].tolist()
    assert lot == C._lot_du_kien(20, C.THAM_SO_GOC)
    assert lot[:9] == [0.01] * 9 and lot[9:19] == [0.02] * 10 and lot[19] == 0.03
    assert d["comment"].tolist() == ["CCBL|%d" % (i + 1) for i in range(20)]


def test_tp_chuoi_theo_gia_tb_co_trong_so_lot(exe):
    # 10 lenh: chin lenh 0,01 o 2000 ... 1920 va lenh thu 10 (0,02) o 1910 ; tb = 21460 / 11 = 1950,909 ; TP = tb + 20 = 1970,909 -> 1970,91
    ticks = [(20 * i, round(2000.0 - 10.0 * i, 2)) for i in range(10)] + [(200, 1971.00)]
    r, d, _ = chay(exe, ticks)
    assert r["kq"]["n_mo"] == 10 and r["kq"]["n_tp"] == 10
    assert set(d["close"]) == {1970.91} and d["vol"].tolist()[-1] == 0.02
    assert r["kq"]["balance"] - 100000.0 == pytest.approx(220.01)


def test_lam_tron_nua_cent_len_tp(exe):
    # 1320,02 va 1309,83 -> tb = 1314,925 ; TP = 1334,925 -> 1334,93 (so thuc 1334.9249999 se ra 1334,92: lech 1 cent o 21 chuoi that)
    ticks = [(0, 1320.02), (20, 1309.83), (40, 1334.92), (59, 1334.93)]
    r, d, t = chay(exe, ticks)
    assert r["kq"]["n_tp"] == 2 and set(d["close"]) == {1334.93} and t[int(d.iloc[0]["tick_dong"])] == 59
    assert r["kq"]["balance"] - 100000.0 == pytest.approx(40.01)


def test_lam_tron_nua_cent_len_tp_mep_so_thuc(exe):
    # tb = (1300,00 + 1260,43) / 2 = 1280,215 -> TP = 1300,215 -> NUA LEN 1300,22. Tinh bang so thuc ra 1300,21: 130021,5 * 0.01 * 100 =
    # 130021.49999999999 -> round -> 130021. (Mep nay chi xuat hien o vai vung gia; vung 1950-2040 USD khong co mep nao.)
    ticks = [(0, 1300.00), (20, 1260.43), (40, 1300.21), (59, 1300.22)]
    r, d, t = chay(exe, ticks)
    assert r["kq"]["n_mo"] == 2 and r["kq"]["n_tp"] == 2 and r["kq"]["con_mo"] == 0
    assert set(d["close"]) == {1300.22} and t[int(d.iloc[0]["tick_dong"])] == 59
    assert r["kq"]["balance"] - 100000.0 == pytest.approx(40.01)


@pytest.mark.parametrize("diem", [100004, 120010, 150010, 180010, 200009, 220020])
def test_muc_tp_va_sl_luon_nam_tren_luoi_chu_so(exe, diem):
    # `k * 0.01` khong luon bang `k / 100` (13% so nguyen k, vd. 100004 * 0.01 = 1000.0400000000001): EA khong NormalizeDouble thi MT5 that
    # co the bao 'Invalid stops'. Cac `diem` duoi day deu la k nhu vay.
    # lenh don o (diem - 1000) diem, TP = +100 pip = `diem`; chay() da khang dinh gia_lech == 0 -> test nay ep EA dat TP DUNG tai nhung gia do
    gia_mo = (diem - 1000) / 100.0
    r, d, _ = chay(exe, [(0, gia_mo), (20, diem / 100.0)])
    assert r["kq"]["n_tp"] == 1 and d.iloc[0]["close"] == diem / 100.0


def test_lam_tron_nua_cent_len_sl_chuoi_that_2018_01_03(exe):
    # chuoi that 2018-01-03: 0,01 @1320,02 + 0,01 @1309,83, thoat SL o 1318,23 loi +6,61 (tb = 1314,925 ; bac 33 pip -> 1318,225 -> .23)
    r, d, _ = chay(exe, [(0, 1320.02), (20, 1309.83), (40, 1319.82), (59, 1318.24)])
    assert r["kq"]["n_dong"] == 0 and r["kq"]["con_mo"] == 2
    r, d, _ = chay(exe, [(0, 1320.02), (20, 1309.83), (40, 1319.82), (59, 1318.23)])
    assert r["kq"]["n_sl"] == 2 and set(d["close"]) == {1318.23}
    assert r["kq"]["balance"] - 100000.0 == pytest.approx(6.61)


def test_cua_vao_bi_bo_khi_chuoi_dang_mo(exe):
    r, d, _ = chay(exe, [(0, 2000.00), (300, 2000.50), (420, 2000.50), (430, 2000.40)])
    assert r["kq"]["n_mo"] == 1
    assert any("bo qua gio vao" in x for x in r["log"])
    assert tong_ket(r) == (1, 0)                                                  # cua +0 da mo lenh (khong tinh la 'truoc cua so'), cua +420 bi bo


def test_cua_vao_thu_hai_mo_chuoi_moi_khi_chuoi_cu_da_dong(exe):
    r, d, _ = chay(exe, [(0, 2000.00), (20, 2010.50), (420, 2000.00)])
    assert r["kq"]["n_mo"] == 2 and r["kq"]["n_tp"] == 1 and r["kq"]["con_mo"] == 1
    assert tong_ket(r) == (0, 0)                                                  # cua da DUNG khong bi dem lai o nen sau ('truoc cua so') - chong lap cua


def test_cua_vao_truoc_cua_so_bi_bo_im_lang_va_dem(exe):
    r, d, _ = chay(exe, [(0, 2000.00)], gio=5)
    assert r["kq"]["n_mo"] == 1 and tong_ket(r) == (0, 10)                                       # 5 gio * 2 cua vao moi gio


def test_cua_vao_mo_o_tick_dau_tien_cua_phut_ke_ca_khi_khong_phai_giay_0(exe):
    r, d, t = chay(exe, [(30, 2000.00)])
    assert r["kq"]["n_mo"] == 1 and t[int(d.iloc[0]["tick_mo"])] == 30


def test_cua_vao_phut_le_ngoai_luoi_m5_van_mo(exe):
    r, d, t = chay(exe, [(420, 2000.00)])                                      # phut 7 cua gio: nen M1 mo luc +420 (khong phai boi cua 5 phut)
    assert r["kq"]["n_mo"] == 1 and t[int(d.iloc[0]["tick_mo"])] == 420
    assert tong_ket(r) == (0, 1)                                               # cua +0 da qua


def test_cua_vao_cuoi_cung_cua_mang_van_duoc_xu_ly(exe):
    # gio thu 39, +420 giay = phan tu CUOI (thu 80) cua G_VAO: truoc day ArraySize - 1 bo roi no im lang
    r, d, t = chay(exe, [(420, 2000.00)], gio=39)
    assert r["kq"]["n_mo"] == 1 and t[int(d.iloc[0]["tick_mo"])] == 420
    assert tong_ket(r) == (0, 79)


def test_cua_vao_ngay_sau_cua_cuoi_khong_mo_gi(exe):
    r, d, _ = chay(exe, [(420, 2000.00), (3600 + 0, 2000.00), (3600 + 420, 2000.00)], gio=39)      # het mang -> cac nen sau khong co cua
    assert r["kq"]["n_mo"] == 1
    assert tong_ket(r) == (0, 79)


def test_dca_hai_lenh_cung_giay_moc_la_lenh_mo_sau_nhat(exe):
    # hai lenh mo trong CUNG mot giay (gio POSITION_TIME bang nhau) : moc DCA tiep theo van la gia lenh sau (1990 -> 1980), khong phai lenh dau
    r, d, _ = chay(exe, [(0, 2000.00), (0.4, 1990.00), (0.8, 1985.00)])
    assert r["kq"]["n_mo"] == 2 and d["open"].tolist() == [2000.0, 1990.0]
    r, d, _ = chay(exe, [(0, 2000.00), (0.4, 1990.00), (0.8, 1980.00)])
    assert r["kq"]["n_mo"] == 3


def test_khong_co_gio_vao_thi_khong_vao_lenh(exe):
    r, d, _ = chay(exe, [(120, 2000.00), (180, 1980.00)])                     # phut +2, +3: khong nam trong mang gio vao
    assert r["kq"]["n_mo"] == 0


def test_chi_mo_mot_lan_moi_gio_vao(exe):
    r, d, _ = chay(exe, [(0, 2000.00), (10, 2000.10), (20, 2000.00), (50, 2000.20)])
    assert r["kq"]["n_mo"] == 1


def test_gioi_han_so_lenh(exe):
    r, d, _ = chay(exe, [(0, 2000.00), (20, 1990.00), (40, 1980.00)], InpMaxOrders=2)
    assert r["kq"]["n_mo"] == 2
    r, d, _ = chay(exe, [(0, 2000.00), (20, 1990.00), (40, 1980.00)])
    assert r["kq"]["n_mo"] == 3


def test_tham_so_buoc_dca_va_tp_doi_duoc(exe):
    r, d, _ = chay(exe, [(0, 2000.00), (20, 1995.00)], InpStepPips=50.0)
    assert r["kq"]["n_mo"] == 2
    r, d, _ = chay(exe, [(0, 2000.00), (20, 2005.00)], InpTpPips=50.0)
    assert r["kq"]["n_tp"] == 1 and d.iloc[0]["close"] == 2005.0
    r, d, _ = chay(exe, [(0, 2000.00), (20, 1990.00), (40, 2008.00)], InpTpDcaPips=130.0)
    assert r["kq"]["n_tp"] == 2 and set(d["close"]) == {2008.0}              # tb 1995 + 13


def test_che_do_vao_chua_co_bi_tu_choi(exe):
    t = np.array([float(T0)])
    tk = dict(bid=np.array([2000.0]), spread=np.array([0.0]), time=t, bar=t, bar_idx=np.array([0]))
    res = G.chay(exe, tk, 100000.0, tham_so={"InpEntryMode": 1}, digits=2, hop_dong=C.HOP_DONG, lot=C.LOT_VANG)
    assert not res["ok"] and res["ma_thoat"] == 3 and res["kq"].get("init_ok") == 0.0


def test_chuoi_thuc_hien_dung_voi_trinh_bien_dich_cu_phap(tmp_path):
    if G.trinh_bien_dich() is None:
        pytest.skip("khong co trinh bien dich C++")
    p = C.viet_ea(VAO_CHUNG, tmp_path / "ea.mq5", mau=_mau())
    assert G.bien_dich(p, chi_cu_phap=True, thu_muc=tmp_path / "cp") is None          # input thanh const: EA khong tu gan input


# ----------------------------------------------------------------------------------------------------------------- 3. vong kin tren chuoi that
@co_deal
def test_co_che_khop_tung_chuoi_that_cua_hai_lan_chay_tester():
    ch = C.doc_hai_nguon()
    assert len(ch) > 2000 and ch["id"].is_unique
    for ten, g in ch.groupby("nguon"):
        k = C.kiem_co_che(g)
        assert (k["lot_sai"], k["dca_duoi_buoc"], k["sl_ngoai_luoi"], k["sl_duoi_khoi"], k["sl_vuot_tp"], k["tp_lech"]) == (0,) * 6, (ten, k)
        assert k["dca_min_pip"] == pytest.approx(100.0) and k["sl_du_max_pip"] <= 0.0501 and k["sl_n"] > 800 and k["tp_n"] > 30


@co_deal
@can_cxx
def test_vong_kin_ea_tai_tao_dung_moi_chuoi_that():
    ch = C.doc_hai_nguon()
    kq = C.vong_kin(ch, mau=_mau())
    assert kq["n_goc"] == kq["n_lai"] == kq["chung"] == kq["khop"] == 2244, kq
    assert kq["n_bo"] == 2 and kq["ea_bo_qua"] == 0 and sum(kq["dem_lech"].values()) == 0
    assert kq["ea_n_mo"] == int(ch[ch["ly_do"].isin(["sl", "tp"])]["n"].sum())


@co_deal
@can_cxx
def test_vong_kin_bat_duoc_chuoi_sai_co_y():
    ch = C.doc_hai_nguon()
    sai = ch.copy()
    idx = np.flatnonzero(((sai["ly_do"] == "sl") & (sai["n"] == 1)).to_numpy())[5:8]
    sai.loc[sai.index[idx], "gia_ra"] += 0.2             # dinh duong gia len mot bac thang (2 pip) -> EA khoa SL cao hon -> thoat o muc khac
    tk, bo = C.duong_tu_chuoi(sai)
    res = C.chay_ea(tk, C.thoi_diem_vao(ch), mau=_mau())
    lai = C.chuoi_tu_vi_the(C.vi_the_tu_ket_qua(res, tk))
    kq = C.so_chuoi(ch[~ch["id"].isin(bo)], lai)
    assert kq["khop"] == kq["chung"] - 3 and kq["dem_lech"]["gia_ra"] == 3, kq


@co_deal
def test_gio_vao_hai_nguon_khong_trung_va_tang_dan():
    ch = C.doc_hai_nguon()
    v = C.thoi_diem_vao(ch)
    assert len(v) == len(set(v)) and v == sorted(v) and 2200 < len(v) < 2300
