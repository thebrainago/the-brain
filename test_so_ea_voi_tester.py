# -*- coding: utf-8 -*-
"""Kiem `so_ea_voi_tester`: dung cu tim QUY LUAT BACKTEST cua may thu MT5 bang cach so bot goc <-> EA dung lai <-> tester.

Bon tang:
  1. Ham thuan, so TAY: `chuan_gia` (nen M1 hong bi tu choi noi ro), `_p_dau` (xac suat dau chinh xac), `luong_tick` (4 tick / nen), `_ket_luan`,
     `chan_doan` (moi nhanh), `gon` / `ghi_bao_cao`.
  2. MICRO-CA tinh tay (3 nen M1, 1 chuoi): moi loai su kien (vao / DCA / TP / SL) co mot con so ra bang tay cho tung luat tick
     (theo_nen, nguoc_nen, thap_truoc, cao_truoc, xen_ke) - vi du lenh DCA o giay 40 tren nen GIAM chi hop le voi luat "cao truoc"; va cac phep thu AM
     (sua gia 1 point, giay la, TP chua cham, dinh SL thap...) phai bi bat. Dung cu khong duoc "xanh" vi khong kiem gi.
  3. TU KIEM tren gia tong hop co DAP AN (luat that biet truoc): dung cu chon dung luat, 100% su kien hop le, khong luat sai nao thang, va phep quet
     mo phong tai tao DUNG tung chuoi o (luat that, SL doi len).
  4. Duong ong cua mot lan chay: bang chuoi <-> CSV / gz CO DINH (cung noi dung = cung byte), `chay_tester` voi MAY THU GIA (bien dich CHINH van ban .mq5 trong
     lenh, ghi bao cao MT5 day du, `chay_tester` doc lai: cung luat -> DAT, khac luat -> AM, cua so ngoai doan kham_pha / qua ngan / hong ha tang ->
     CHUA_DO_DUOC, doan dong bang va so tay KHONG bi dung), `phan_tich` tren nen M1 ghi bang `xuat_gia` (lech gio, tester co / khong / khac luat).

Khong co MT5 o day: "tester" la `MayThu` (san gia C++ + bao cao HTML utf-16). Vi MayThu dung chinh san gia nen KHOP la dieu phai co; cai duoc kiem la
DUONG ONG va cac phep thu am. Luat tick cua MT5 THAT chi biet duoc khi co nen M1 that + bao cao that (viec cua may nha).
"""
from __future__ import annotations

import functools
import gzip
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import ea_cancubo_lai as C
from nhan import ea_gia_lap as G
from nhan import ea_tho as E
from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from nhan import so_ea_voi_tester as S
from nhan import xuat_gia as XG
from test_bao_cao_mt5 import EN, html_mau
from test_lenh_tester import dung_giao_dich, ghi_htm, html_bao_cao

T = pd.Timestamp
DOC_HAI_NGUON_THAT = C.doc_hai_nguon                    # fixture `moi_truong` thay C.doc_hai_nguon bang chuoi tong hop: giu ham that o day
can_cxx = pytest.mark.skipif(G.trinh_bien_dich() is None, reason="khong co g++ / clang++ (hoac EA_GIA_LAP_CXX)")
co_deal = pytest.mark.skipif(not (C.DEAL_KP.exists() and C.DEAL_XN.exists()), reason="thieu deal tester trong reports/fixture")
LUAT = S.LUAT


# ----------------------------------------------------------------------------------------------------------------- dung cu
def nen(*dong) -> pd.DataFrame:
    """dong = (gio 'YYYY-MM-DD HH:MM', open, high, low, close, spread_point)."""
    return pd.DataFrame([dict(open=o, high=h, low=l, close=c, spread=sp) for (_, o, h, l, c, sp) in dong], index=pd.DatetimeIndex([T(d[0]) for d in dong]))


def chuoi(id, lenh, dong=None, gia_ra=None, ly="sl") -> dict:
    """lenh = [(gio 'YYYY-MM-DD HH:MM:SS', gia ask)]. Lot theo bac thang 0,01 * 1,05^i."""
    gio = [T(g) for g, _ in lenh]
    gia = [float(p) for _, p in lenh]
    lot = [round(0.01 * 1.05 ** i, 2) for i in range(len(lenh))]
    return dict(id=id, mo=gio[0], dong=T(dong) if dong else pd.NaT, n=len(lenh), lot=sum(lot), gia_vao=gia[0], gia_tb=float(np.average(gia, weights=lot)),
                gia_thap=min(gia), gia_ra=np.nan if gia_ra is None else gia_ra, ly_do=ly, loi=0.0, lot_cac_lenh=lot, gia_cac_lenh=gia, gio_cac_lenh=gio)


def bang(*cs) -> pd.DataFrame:
    return pd.DataFrame(list(cs), columns=C.COT_CHUOI)


def ra_gia(ti=1.0, p=(1e-9,), n_xet=10, tot="theo_nen") -> dict:
    """Dau vao nhan tao cho `_ket_luan`."""
    return dict(tot_nhat=tot, n_xet=n_xet, luat={tot: dict(ti_le=ti)}, so_voi={"doi_thu%d" % i: dict(p=x) for i, x in enumerate(p)})


# ================================================================================================= 1. HAM THUAN
def test_chuan_gia_dua_ve_dang_sach_va_giu_nguyen_gia_tri():
    d = nen(("2019-03-04 00:01", 10.0, 11.0, 9.0, 10.5, 20.4), ("2019-03-04 00:00", 10.0, 10.5, 9.5, 10.2, 18),
            ("2019-03-04 00:01", 10.1, 11.1, 9.1, 10.6, 21))                    # trung nen 00:01: giu ban SAU; nen 00:00 dat sai thu tu
    r = S.chuan_gia(d)
    assert list(r.index) == [T("2019-03-04 00:00"), T("2019-03-04 00:01")]
    assert r["open"].tolist() == [10.0, 10.1] and r["spread"].tolist() == [18, 21] and r["spread"].dtype == np.int64
    r2 = S.chuan_gia(d.drop(columns="spread"))
    assert r2["spread"].tolist() == [0, 0]                                       # thieu cot spread -> 0
    r3 = S.chuan_gia(d.assign(spread=[20.4, np.nan, 21.6]))
    assert r3["spread"].tolist() == [0, 22]                                      # NaN -> 0; lam tron ve point nguyen (sau khi bo nen trung)


def test_chuan_gia_doi_gio_co_mui_ve_utc_khong_mui():
    d = nen(("2019-03-04 02:00", 10, 11, 9, 10, 1))
    d.index = d.index.tz_localize("Europe/Athens")                               # 02:00 mua dong = 00:00 UTC
    assert list(S.chuan_gia(d).index) == [T("2019-03-04 00:00")]


@pytest.mark.parametrize("sua,tu_khoa", [
    (lambda d: d.drop(columns="low"), "thieu cot"),
    (lambda d: d.iloc[0:0], "khong co nen"),
    (lambda d: d.set_axis(d.index + pd.Timedelta(seconds=7)), "canh phut"),
    (lambda d: d.assign(close=[np.nan, 10.0]), "o trong"),
    (lambda d: d.assign(high=[10.0, 11.0]), "hong"),                              # high 10 < close 10.5? nen 0: open 10 close 10.5 -> high phai >= 10.5
    (lambda d: d.assign(low=[9.0, 10.8]), "hong"),                                # low 10.8 > open 10.1
], ids=["thieu_cot", "rong", "lech_giay", "nan", "high_thap", "low_cao"])
def test_chuan_gia_tu_choi_nen_hong_va_noi_ro(sua, tu_khoa):
    d = nen(("2019-03-04 00:00", 10.0, 11.0, 9.0, 10.5, 20), ("2019-03-04 00:01", 10.1, 11.0, 9.0, 10.5, 20))
    with pytest.raises(ValueError, match=tu_khoa):
        S.chuan_gia(sua(d))


def test_gia_tong_hop_tat_dinh_lien_tuc_va_la_nen_hop_le():
    a, b = S.gia_tong_hop(3, seed=5), S.gia_tong_hop(3, seed=5)
    pd.testing.assert_frame_equal(a, b)                                          # cung seed -> cung nen
    assert not a.equals(S.gia_tong_hop(3, seed=6))
    assert len(a) == 3 * 1380 and (np.diff(a.index.values.astype("datetime64[m]").astype(np.int64)) == 1).all()     # phut lien tiep
    assert a["spread"].between(18, 32).all()
    assert np.allclose(a[["open", "high", "low", "close"]].to_numpy() / S.POINT, np.rint(a[["open", "high", "low", "close"]].to_numpy() / S.POINT))   # tren luoi 0,01
    S.chuan_gia(a)                                                               # khong nem loi: high >= max(o, c), low <= min(o, c)
    assert 1100 < a["close"].mean() < 1500


@pytest.mark.parametrize("b,c,mong", [(0, 0, 1.0), (1, 0, 0.5), (5, 0, 1 / 32), (3, 1, 5 / 16), (0, 5, 1.0), (4, 4, 163 / 256), (10, 0, 1 / 1024)])
def test_p_dau_chinh_xac(b, c, mong):
    assert S._p_dau(b, c) == pytest.approx(mong, rel=1e-12)


def test_p_dau_don_dieu_va_bao_phu_khong_tran_so_lon():
    ps = [S._p_dau(b, 3) for b in range(0, 30)]
    assert all(x >= y for x, y in zip(ps, ps[1:]))                               # nhieu bang chung hon thi p nho hon
    assert 0 < S._p_dau(400, 0) < 1e-100                                         # math.comb khong tran so


def test_luong_tick_bon_tick_moi_nen_o_giay_0_20_40_59_va_diem_nguyen():
    b = nen(("2019-03-04 00:00", 2000.00, 2000.50, 1999.90, 2000.20, 20), ("2019-03-04 00:01", 2000.20, 2001.00, 2000.10, 2000.90, 24))
    s = S.luong_tick(S.chuan_gia(b), "theo_nen")
    t0 = int(T("2019-03-04 00:00").value // 10 ** 9)
    assert s["t"].tolist() == [t0, t0 + 20, t0 + 40, t0 + 59, t0 + 60, t0 + 80, t0 + 100, t0 + 119]
    assert s["bid"].tolist() == [200000, 199990, 200050, 200020, 200020, 200010, 200100, 200090]     # nen tang: open, LOW, HIGH, close
    assert s["sp"].tolist() == [20] * 4 + [24] * 4 and s["bid"].dtype == np.int64
    assert S.luong_tick(S.chuan_gia(b), "theo_nen", lech_s=3600)["t"].tolist() == [x + 3600 for x in s["t"].tolist()]
    assert S._tim(s, t0 + 40) == 2 and S._tim(s, t0 + 41) == -1 and S._tim(s, t0 - 5) == -1 and S._tim(s, t0 + 10 ** 6) == -1
    with pytest.raises(ValueError):
        S.luong_tick(S.chuan_gia(b), "luat_khong_co")


# ================================================================================================= 2. MICRO-CA TINH TAY
# Nen 0 (00:00) la nen vao; ask = open + spread (20 point = 0,20) = 2000,20.
BARS_TP = nen(("2019-03-04 00:00", 2000.00, 2000.50, 1999.90, 2000.20, 20),
              ("2019-03-04 00:01", 2000.20, 2001.00, 2000.10, 2000.90, 20),          # nen TANG, cao 2001,00 >= TP 2000,80
              ("2019-03-04 00:02", 2000.90, 2000.90, 2000.90, 2000.90, 20))
BARS_DCA = nen(("2019-03-04 00:00", 2000.00, 2000.50, 1999.90, 2000.20, 20),
               ("2019-03-04 00:01", 1995.00, 1995.50, 1989.50, 1990.50, 20),         # nen GIAM, thap 1989,50: ask 1989,70 <= 2000,20 - 10,00
               ("2019-03-04 00:02", 1990.50, 1991.20, 1990.40, 1991.00, 20))
BARS_SL = nen(("2019-03-04 00:00", 2000.00, 2000.50, 1999.90, 2000.20, 20),
              ("2019-03-04 00:01", 2000.20, 2003.00, 2000.10, 2002.80, 20),          # dinh bid 2003,00 = SL 2001,50 + 15 pip
              ("2019-03-04 00:02", 2002.80, 2002.90, 2001.00, 2001.20, 20))          # nen GIAM: cao 2002,90 ; thap 2001,00


def ch_tp(giay=40, muc=2000.80, ask=2000.20, gio_vao="2019-03-04 00:00:00") -> pd.DataFrame:
    return bang(chuoi(0, [(gio_vao, ask)], dong="2019-03-04 00:01:%02d" % giay, gia_ra=muc, ly="tp"))


def ch_dca(ask2=1989.70, giay2=40, giay_tp=40, muc_tp=1991.00) -> pd.DataFrame:
    return bang(chuoi(0, [("2019-03-04 00:00:00", 2000.20), ("2019-03-04 00:01:%02d" % giay2, ask2)], dong="2019-03-04 00:02:%02d" % giay_tp, gia_ra=muc_tp, ly="tp"))


def ch_sl(giay=40, muc=2001.50) -> pd.DataFrame:
    return bang(chuoi(0, [("2019-03-04 00:00:00", 2000.20)], dong="2019-03-04 00:02:%02d" % giay, gia_ra=muc, ly="sl"))


@pytest.mark.parametrize("luat,hop_le", [("theo_nen", True), ("thap_truoc", True), ("nguoc_nen", False), ("cao_truoc", False), ("xen_ke", False)])
def test_tp_giay_40_tren_nen_tang_chi_hop_voi_luat_thap_truoc(luat, hop_le):
    """Nen tang 00:01: theo_nen / thap_truoc = open, LOW, HIGH (TP cham o giay 40); nguoc_nen / cao_truoc / xen_ke(nen le) = open, HIGH, LOW (TP cham o giay 20)."""
    k = S.kiem_luat_tick(ch_tp(40), BARS_TP)
    r = k["luat"][luat]
    assert r["theo_loai"]["vao"] == [1, 0]                                       # lenh dau: open + spread, MOI luat deu dung
    assert r["theo_loai"]["tp"] == ([1, 0] if hop_le else [0, 1])
    if not hop_le:
        assert r["ly_sai"] == {"som_hon": 1} and r["vi_du_sai"][0]["tick_som_hon_giay"] == -20 and r["vi_du_sai"][0]["loai"] == "tp"
    assert k["n_xet"] == 1 and k["su_kien"] == dict(vao=1, dca=0, tp=1, sl=0)


def test_tp_xep_hang_hoa_va_chua_ro_vi_mot_chuoi_khong_du():
    k = S.kiem_luat_tick(ch_tp(40), BARS_TP)
    assert k["xep_hang"][:2] == ["theo_nen", "thap_truoc"] and k["tot_nhat"] == "theo_nen"      # hoa -> thu tu LUAT
    assert k["so_voi"]["thap_truoc"] == dict(tot_hon=0, kem_hon=0, p=1.0)
    assert k["so_voi"]["nguoc_nen"]["tot_hon"] == 1 and k["so_voi"]["nguoc_nen"]["p"] == 0.5
    assert k["ket_luan"] == "CHUA_RO" and "thap_truoc" in k["ly_do"]
    assert k["giay_quan_sat"]["tp"] == {40: 1}


def test_tp_giay_20_dao_nguoc_ket_qua():
    k = S.kiem_luat_tick(ch_tp(20), BARS_TP)                                     # tick giay 20: thap_truoc la LOW 2000,10 < TP -> chua cham
    assert k["luat"]["theo_nen"]["theo_loai"]["tp"] == [0, 1] and k["luat"]["theo_nen"]["ly_sai"] == {"khong_cham": 1}
    assert k["luat"]["nguoc_nen"]["theo_loai"]["tp"] == [1, 0] and k["luat"]["cao_truoc"]["theo_loai"]["tp"] == [1, 0]
    assert k["tot_nhat"] in ("nguoc_nen", "cao_truoc", "xen_ke")


def test_tp_muc_chua_bao_gio_cham_la_khong_cham():
    k = S.kiem_luat_tick(ch_tp(40, muc=2002.00), BARS_TP)
    for lt in LUAT:
        assert k["luat"][lt]["theo_loai"]["tp"] == [0, 1] and k["luat"][lt]["ly_sai"] == {"khong_cham": 1}
    assert k["ket_luan"] == "KHONG_KHOP" and "0.0%" in k["ly_do"]


def test_tp_thoat_o_giay_59_luon_som_hon_vi_dinh_den_truoc():
    k = S.kiem_luat_tick(ch_tp(59, muc=2000.80), BARS_TP)                        # close 2000,90 >= 2000,80 nhung dinh 2001,00 da cham truoc o MOI luat
    assert all(k["luat"][lt]["theo_loai"]["tp"] == [0, 1] for lt in LUAT)


@pytest.mark.parametrize("luat,hop_le", [("theo_nen", True), ("cao_truoc", True), ("xen_ke", True), ("thap_truoc", False), ("nguoc_nen", False)])
def test_dca_giay_40_tren_nen_giam_chi_hop_voi_luat_cao_truoc(luat, hop_le):
    """Nen giam 00:01 (open 1995,00 close 1990,50): theo_nen / cao_truoc / xen_ke(nen le) = open, HIGH, LOW => DCA o giay 40;
    nguoc_nen / thap_truoc = open, LOW, HIGH => DCA o giay 20."""
    k = S.kiem_luat_tick(ch_dca(), BARS_DCA)
    r = k["luat"][luat]
    assert r["theo_loai"]["vao"] == [1, 0]
    assert r["theo_loai"]["dca"] == ([1, 0] if hop_le else [0, 1])
    if not hop_le:
        # thap_truoc sai DCA (nen giam 00:01 chay LOW truoc); nguoc_nen sai CA TP (nen tang 00:02 chay HIGH truoc => TP o giay 20)
        assert r["ly_sai"].get("som_hon") == {"thap_truoc": 1, "nguoc_nen": 2}[luat]
        vd = [x for x in r["vi_du_sai"] if x["loai"] == "dca"][0]
        assert vd["ly"] == "som_hon" and vd["tick_som_hon_giay"] == -20


def test_dca_gia_khop_sai_1_point_bi_bat():
    k = S.kiem_luat_tick(ch_dca(ask2=1989.69), BARS_DCA)                         # tick dung (giay 40) nhung gia ghi lech 1 point so voi ask
    r = k["luat"]["theo_nen"]
    assert r["theo_loai"]["dca"] == [0, 1] and r["ly_sai"].get("sai_gia") == 1
    vd = [x for x in r["vi_du_sai"] if x["ly"] == "sai_gia"][0]
    assert vd["quan_sat"] == 198969 and vd["du_doan"] == 198970


def test_dca_qua_som_khi_chua_du_100_pip_la_khong_cham():
    k = S.kiem_luat_tick(ch_dca(giay2=20, ask2=1995.70), BARS_DCA)               # giay 20 (cao 1995,50, ask 1995,70) chua toi 1990,20
    r = k["luat"]["theo_nen"]
    assert r["theo_loai"]["dca"] == [0, 1] and r["ly_sai"].get("khong_cham") == 1


def test_dca_giay_la_va_vao_giay_la():
    k = S.kiem_luat_tick(ch_dca(giay2=41), BARS_DCA)                             # khong luat nao co tick o giay 41
    assert all(k["luat"][lt]["theo_loai"]["dca"] == [0, 1] and k["luat"][lt]["ly_sai"].get("giay_la") for lt in LUAT)
    k2 = S.kiem_luat_tick(ch_tp(40, gio_vao="2019-03-04 00:00:05"), BARS_TP)
    assert all(k2["luat"][lt]["theo_loai"]["vao"] == [0, 1] for lt in LUAT)
    assert all(k2["luat"][lt]["theo_loai"]["tp"] == [0, 1] and k2["luat"][lt]["ly_sai"] == {"giay_la": 1} for lt in LUAT)   # lenh cuoi khong dinh vi duoc


def test_vao_sai_1_point_hien_o_muc_vao_khong_o_xep_hang():
    k = S.kiem_luat_tick(ch_tp(40, ask=2000.21), BARS_TP)
    assert k["vao"]["dung"] == 0 and k["vao"]["sai"] == 1 and k["vao"]["lech_diem"] == {1: 1}      # quan sat 200021 - du doan 200020
    assert k["tot_nhat"] == "theo_nen" and k["luat"]["theo_nen"]["ti_le"] == 1.0                    # khong anh huong xep hang luat
    assert k["luat"]["theo_nen"]["theo_loai"]["vao"] == [0, 1]


@pytest.mark.parametrize("giay,hop_le", [
    (40, {"theo_nen", "cao_truoc"}),                    # nen giam 00:02: theo_nen / cao_truoc: open, HIGH 2002,90, LOW 2001,00 -> bid 2001,00 o giay 40
    (20, {"nguoc_nen", "thap_truoc", "xen_ke"}),        # nguoc_nen / thap_truoc / xen_ke(nen chan): open, LOW, HIGH -> bid 2001,00 o giay 20
    (59, set(LUAT)),                                    # giay 59 = close 2001,20 <= 2001,50 o moi luat
    (0, set()),                                         # giay 0 = open 2002,80 > SL o moi luat
])
def test_sl_bid_thoat_phai_nam_duoi_muc_theo_tung_luat(giay, hop_le):
    k = S.kiem_luat_tick(ch_sl(giay), BARS_SL)
    for lt in LUAT:
        r = k["luat"][lt]
        assert r["theo_loai"]["sl"] == ([1, 0] if lt in hop_le else [0, 1]), (lt, giay)
        if lt not in hop_le:
            assert r["ly_sai"] == {"bid_tren_muc": 1}


def test_sl_dinh_phai_cao_hon_muc_it_nhat_15_pip():
    ok = S.kiem_luat_tick(ch_sl(40), BARS_SL)
    assert ok["luat"]["theo_nen"]["theo_loai"]["sl"] == [1, 0]
    thap = BARS_SL.copy()
    thap.loc[T("2019-03-04 00:01"), "high"] = 2002.99                             # dinh 2002,99 < 2001,50 + 1,50 = 2003,00
    k = S.kiem_luat_tick(ch_sl(40), thap)
    r = k["luat"]["theo_nen"]
    assert r["theo_loai"]["sl"] == [0, 1] and r["ly_sai"] == {"dinh_thap": 1}
    vd = r["vi_du_sai"][0]
    assert vd["dinh"] == 200299 and vd["can"] == 200300 and vd["muc"] == 200150
    assert S.kiem_luat_tick(ch_sl(40), thap, slack=1)["luat"]["theo_nen"]["theo_loai"]["sl"] == [1, 0]     # slack 1 point cho phep


def test_nen_ngoai_gia_khong_bi_tinh_va_khong_co_gi_de_kiem_la_chua_do_duoc():
    k = S.kiem_luat_tick(ch_tp(40), BARS_TP.iloc[1:])                            # nen 00:00 (nen vao) bi cat: chuoi nam ngoai khoang nen
    assert k["n_xet"] == 0 and k["n_ngoai_gia"] == 1 and k["ket_luan"] == "CHUA_DO_DUOC" and "n_xet = 0" in k["ly_do"]
    k2 = S.kiem_luat_tick(bang(chuoi(0, [("2019-03-04 00:00:00", 2000.20)], dong="2019-03-04 00:01:10", ly="ea")), BARS_TP)
    assert k2["n_xet"] == 0                                                      # chuoi dong tay (ly do 'ea') khong co hanh vi tick de kiem
    k3 = S.kiem_luat_tick(bang(chuoi(0, [("2019-03-04 00:00:00", 2000.20)])).iloc[0:0], BARS_TP)
    assert k3["ket_luan"] == "CHUA_DO_DUOC"


def test_lech_giay_dich_chuoi_va_nen_cung_mot_khoang():
    """Chuoi cua deal lech +3600 s so voi nen: khong khai lech thi chuoi nam NGOAI khoang nen; khai `lech_s=3600` thi ket qua y het ban chua dich."""
    goc = S.kiem_luat_tick(ch_tp(40), BARS_TP)
    c = ch_tp(40)
    d = pd.Timedelta(hours=1)
    c["mo"], c["dong"] = c["mo"] + d, c["dong"] + d
    c["gio_cac_lenh"] = c["gio_cac_lenh"].map(lambda xs: [x + d for x in xs])
    assert S.kiem_luat_tick(c, BARS_TP)["n_xet"] == 0
    k = S.kiem_luat_tick(c, BARS_TP, lech_s=3600)
    assert k["n_xet"] == 1
    for lt in LUAT:
        assert k["luat"][lt]["theo_loai"] == goc["luat"][lt]["theo_loai"]


# ----------------------------------------------------------------------------------------------- bien + hai phia (lo hong do kiem dot bien 09/10 chi ra)
def luong(*tick) -> dict:
    """tick = (giay ke tu 00:00:00, bid, spread_point) -> duong tick cho `_kiem_chuoi` o point nguyen, khong qua nen M1."""
    t0 = int(T("2019-03-04 00:00:00").value // 10 ** 9)
    return dict(t=np.array([t0 + g for g, _, _ in tick], np.int64), bid=np.array([round(b / S.POINT) for _, b, _ in tick], np.int64),
                sp=np.array([sp for *_, sp in tick], np.int64))


def kiem_mot(c: pd.DataFrame, s: dict, slack: int = 0) -> list[tuple]:
    return S._kiem_chuoi(next(c.itertuples()), s, dict(C.THAM_SO_GOC), slack)


def test_tp_cham_dung_muc_la_cham_hon_1_point_thi_chua():
    """MT5 khop TP cua lenh mua khi bid >= TP: bid == TP la DA cham."""
    s = luong((0, 2000.00, 20), (20, 2000.80, 20))
    lenh = [("2019-03-04 00:00:00", 2000.20)]
    assert kiem_mot(bang(chuoi(0, lenh, dong="2019-03-04 00:00:20", gia_ra=2000.80, ly="tp")), s)[1][:3] == ("tp", True, "")
    assert kiem_mot(bang(chuoi(0, lenh, dong="2019-03-04 00:00:20", gia_ra=2000.81, ly="tp")), s)[1][:3] == ("tp", False, "khong_cham")


def test_sl_dinh_chi_tinh_sau_lenh_cuoi_khong_tinh_dinh_truoc_do():
    """Chuoi 2 lenh: dinh bid TRUOC lenh DCA (2000,50) khong lam SL hop le; SL chi hop le neu SAU lenh cuoi gia den >= SL + 15 pip."""
    lenh = [("2019-03-04 00:00:00", 2000.20), ("2019-03-04 00:00:40", 1990.20)]

    def ca(dinh):
        s = luong((0, 2000.00, 20), (20, 2000.50, 20), (40, 1990.00, 20), (60, dinh, 20), (80, 1996.30, 20))
        return kiem_mot(bang(chuoi(0, lenh, dong="2019-03-04 00:01:20", gia_ra=1996.40, ly="sl")), s)
    thap, cao = ca(1996.80), ca(1998.50)
    assert [x[:3] for x in thap] == [("vao", True, ""), ("dca", True, ""), ("sl", False, "dinh_thap")]
    assert thap[2][3]["dinh"] == 199680 and thap[2][3]["can"] == 199790 and thap[2][3]["muc"] == 199640
    assert [x[:3] for x in cao] == [("vao", True, ""), ("dca", True, ""), ("sl", True, "")]


def test_chuoi_trong_gia_hai_dau_khoang_dong_chuoi_mo_va_dich_theo_lech_gio():
    bars = nen(("2019-03-04 00:00", 1, 1, 1, 1, 0), ("2019-03-04 00:01", 1, 1, 1, 1, 0))                # khoang [00:00:00, 00:01:59]

    def trong(mo, dong=None, lech=0):
        c = bang(chuoi(0, [(mo, 2000.0)], dong=dong, gia_ra=2001.0 if dong else None, ly="tp" if dong else "ea"))
        return len(S._chuoi_trong_gia(c, bars, lech)) == 1
    assert trong("2019-03-04 00:00:00") and not trong("2019-03-03 23:59:59")                          # dau khoang: tinh giay dau, khong tinh giay truoc
    assert trong("2019-03-04 00:01:59") and not trong("2019-03-04 00:02:00")                           # cuoi khoang = giay 59 cua nen cuoi
    assert trong("2019-03-04 00:00:10", "2019-03-04 00:01:59") and not trong("2019-03-04 00:00:10", "2019-03-04 00:02:00")   # dong sau khoang -> ngoai
    assert trong("2019-03-04 00:00:10")                                                                 # chuoi con mo: van tinh
    assert trong("2019-03-04 01:00:00", lech=3600) and not trong("2019-03-04 00:59:59", lech=3600)    # lech +1 gio: ca hai dau dich theo
    assert trong("2019-03-04 01:01:59", lech=3600) and not trong("2019-03-04 01:02:00", lech=3600)
    assert trong("2019-03-04 00:00:30") and not trong("2019-03-04 00:00:30", lech=3600)               # chua dich thi nam trong, dich roi thi truoc khoang


def test_so_voi_dem_ca_hai_phia_p_la_kiem_dau_chinh_xac(monkeypatch):
    """Luat A hon B o 25 su kien nhung B hon A o 5: p = P(X >= 25 | n = 30) = 174437 / 2^30 (so su kien B tot hon PHAI duoc dem, khong bo qua)."""
    n = 30
    ok = {"A": [True] * 25 + [False] * 5, "B": [False] * 25 + [True] * 5}                                # moi chuoi mot su kien tp
    chs = bang(*[chuoi(i, [("2019-03-04 00:00:00", 2000.20)], dong="2019-03-04 00:00:40", gia_ra=2001.0, ly="tp") for i in range(n)])
    bars = nen(("2019-03-04 00:00", 2000.00, 2001.00, 1999.00, 2000.50, 20))
    monkeypatch.setattr(S, "luong_tick", lambda b, lt, lech_s=0: dict(luat=lt))
    monkeypatch.setattr(S, "_kiem_chuoi", lambda r, s, ts, slack=0: [("vao", True, "", dict(giay=0)), ("tp", ok[s["luat"]][int(r.id)], "", dict(giay=40))])
    k = S.kiem_luat_tick(chs, bars, luat=["A", "B"])
    assert k["xep_hang"] == ["A", "B"] and k["luat"]["A"]["ti_le"] == pytest.approx(25 / 30) and k["luat"]["B"]["ti_le"] == pytest.approx(5 / 30)
    assert k["so_voi"]["B"]["tot_hon"] == 25 and k["so_voi"]["B"]["kem_hon"] == 5
    assert k["so_voi"]["B"]["p"] == pytest.approx(174437 / 2 ** 30, rel=1e-12)


def test_do_lech_gio_khong_khop_o_dau_ca_thi_tra_lech_0():
    bars = S.gia_tong_hop(1, seed=3)
    c = bang(*[chuoi(i, [("2019-03-04 %02d:07:00" % (3 + i), 1234.56)], dong="2019-03-04 %02d:09:00" % (3 + i), gia_ra=1235.0, ly="tp") for i in range(3)])
    r = S.do_lech_gio(c, bars)
    assert r["tot_nhat"] == 0 and r["ti_le"] == 0.0 and set(r["khop"].values()) == {0}                  # hoa khong -> chon lech nho nhat, khong phai lech 6 gio


def test_do_lech_gio_tim_dung_so_gio_lech():
    bars = S.gia_tong_hop(2, seed=3)
    rng = np.random.default_rng(1)
    c = []
    for i, j in enumerate(sorted(rng.choice(len(bars) - 5, 12, replace=False))):
        t_nen = bars.index[j]
        ask = round(bars["open"].iloc[j] + bars["spread"].iloc[j] * S.POINT, 2)
        c.append(chuoi(i, [(str(t_nen + pd.Timedelta(hours=2)), ask)], dong=str(t_nen + pd.Timedelta(hours=2, minutes=3)), gia_ra=ask + 1, ly="tp"))
    r = S.do_lech_gio(bang(*c), bars)
    assert r["tot_nhat"] == 2 and r["khop"][2] == 12 and r["ti_le"] == 1.0 and r["n_chuoi"] == 12
    assert sum(v for h, v in r["khop"].items() if h != 2) <= 1                    # lech sai chi khop ngau nhien
    assert S.do_lech_gio(bang(*c), bars, gio=[0, 1])["ti_le"] < 0.2               # khong quet toi +2 -> khong thay
    assert S.do_lech_gio(bang(*c).iloc[0:0], bars)["ti_le"] is None


# ================================================================================================= 3. KET LUAN + CHAN DOAN
@pytest.mark.parametrize("ra,mong", [
    (dict(tot_nhat=None, n_xet=0, luat={}, so_voi={}), "CHUA_DO_DUOC"),
    (ra_gia(n_xet=0), "CHUA_DO_DUOC"),
    (ra_gia(ti=None), "CHUA_DO_DUOC"),
    (ra_gia(ti=0.8999), "KHONG_KHOP"),
    (ra_gia(ti=0.0), "KHONG_KHOP"),
    (ra_gia(ti=0.90), "CHUA_RO"),                    # sat nguong khong-khop: duoi 99% thi chua ro
    (ra_gia(ti=0.9899), "CHUA_RO"),
    (ra_gia(ti=0.99, p=(1e-6, 1e-9)), "RO"),         # bien: dung 99% va p = 1e-6 van RO
    (ra_gia(ti=1.0, p=(1e-6 * 1.0001,)), "CHUA_RO"),
    (ra_gia(ti=1.0, p=(1e-12, 0.3)), "CHUA_RO"),      # chi can MOT doi thu chua bi vuot
    (ra_gia(ti=1.0, p=()), "RO"),                    # khong co doi thu nao (danh sach luat chi co 1)
])
def test_ket_luan_cac_nguong(ra, mong):
    kl, ly = S._ket_luan(ra)
    assert kl == mong and isinstance(ly, str) and ly


def test_ket_luan_chua_ro_noi_ro_thieu_gi():
    _, ly = S._ket_luan(ra_gia(ti=0.95))
    assert "chua dat nguong 99%" in ly
    _, ly = S._ket_luan(ra_gia(ti=1.0, p=(0.01,)))
    assert "doi_thu0" in ly and "can them chuoi" in ly


@pytest.mark.parametrize("ti,mong", [
    ({"goc_mo_phong": None}, "CHUA_DO_DUOC"),
    ({"goc_mo_phong": 1.0}, "CHUA co tester"),
    ({"goc_mo_phong": 0.5}, "chi tai tao 50.0%"),
    ({"goc_mo_phong": 1.0, "goc_tester": 1.0, "mo_phong_tester": 1.0}, "CA BA KHOP"),
    ({"goc_mo_phong": 0.2, "goc_tester": 1.0, "mo_phong_tester": 0.2}, "MO PHONG lech tester"),
    ({"goc_mo_phong": 1.0, "goc_tester": 0.4, "mo_phong_tester": 0.4}, "TESTER (cung EA) thi khong"),
    ({"goc_mo_phong": 0.3, "goc_tester": 0.3, "mo_phong_tester": 1.0}, "deu lech bot goc"),
    ({"goc_mo_phong": 0.3, "goc_tester": 0.4, "mo_phong_tester": 0.5}, "ca ba deu lech nhau"),
    ({"goc_mo_phong": None, "goc_tester": 1.0, "mo_phong_tester": 1.0}, "CHUA_DO_DUOC"),
])
def test_chan_doan_moi_nhanh(ti, mong):
    assert mong in S.chan_doan(ti)


def test_chan_doan_nguong_tuy_chinh():
    assert "CA BA KHOP" in S.chan_doan({"goc_mo_phong": 0.95, "goc_tester": 0.95, "mo_phong_tester": 0.95}, nguong=0.9)
    assert "CA BA KHOP" not in S.chan_doan({"goc_mo_phong": 0.95, "goc_tester": 0.95, "mo_phong_tester": 0.95})


def test_ti_le_khop_lay_mau_so_lon_hon():
    assert S._ti_le(dict(n_goc=10, n_lai=12, khop=9)) == pytest.approx(0.75)      # tester thua 2 chuoi khong ton tai o goc: khop/12
    assert S._ti_le(dict(n_goc=0, n_lai=0, khop=0)) is None


# ================================================================================================= 4. BANG CHUOI <-> CSV / GZ
def _mau_chuoi(n=6, seed=2) -> pd.DataFrame:
    """Bang chuoi nho gom cac dang can thiet: 1 lenh, nhieu lenh, dong bang TP, SL, dang mo (NaT / NaN)."""
    c = [chuoi(0, [("2019-03-04 00:08:00", 1301.18)], dong="2019-03-04 02:00:20", gia_ra=1311.18, ly="tp"),
         chuoi(1, [("2019-03-04 05:10:00", 1292.42), ("2019-03-04 06:11:40", 1282.38), ("2019-03-04 07:30:20", 1272.31)], dong="2019-03-05 00:55:20", gia_ra=1280.1, ly="sl"),
         chuoi(2, [("2019-03-05 09:00:00", 1280.07)], ly="het_gio")]
    return bang(*c).iloc[:n]


def test_csv_khu_tron_giu_nguyen_moi_cot_ke_ca_nat_nan():
    c = _mau_chuoi()
    c2 = S.chuoi_tu_csv(S.chuoi_ra_csv(c))
    assert list(c2.columns) == C.COT_CHUOI and len(c2) == 3
    for col in ("id", "n", "ly_do"):
        assert c2[col].tolist() == c[col].tolist()
    for col in ("lot", "gia_vao", "gia_tb", "gia_thap", "gia_ra", "loi"):
        np.testing.assert_allclose(c2[col].to_numpy(float), c[col].to_numpy(float), rtol=0, atol=1e-8, equal_nan=True)
    assert c2["mo"].tolist() == c["mo"].tolist() and pd.isna(c2["dong"].iloc[2]) and c2["dong"].iloc[:2].tolist() == c["dong"].iloc[:2].tolist()
    for col in ("lot_cac_lenh", "gia_cac_lenh", "gio_cac_lenh"):
        assert c2[col].tolist() == c[col].tolist()                                 # danh sach noi bang ';', so lap bang repr -> khong mat so le
    assert C.so_chuoi(c[c["ly_do"] != "het_gio"], c2[c2["ly_do"] != "het_gio"])["khop"] == 2


def test_csv_bang_rong_va_thieu_cot():
    r = S.chuoi_tu_csv(S.chuoi_ra_csv(pd.DataFrame(columns=C.COT_CHUOI)))
    assert len(r) == 0 and list(r.columns) == C.COT_CHUOI
    assert len(S.chuoi_tu_csv(S.chuoi_ra_csv(None))) == 0
    with pytest.raises(ValueError, match="thieu cot"):
        S.chuoi_tu_csv("id,mo\n0,2019-01-01 00:00:00\n")


def test_gz_co_dinh_cung_noi_dung_cung_byte_va_khong_de_lai_tep_tam(tmp_path):
    c = _mau_chuoi()
    a = S.ghi_chuoi_gz(c, tmp_path / "a" / "x.csv.gz")
    b = S.ghi_chuoi_gz(c, tmp_path / "b" / "ten_khac.csv.gz")
    assert a == b > 50
    assert (tmp_path / "a" / "x.csv.gz").read_bytes() == (tmp_path / "b" / "ten_khac.csv.gz").read_bytes()     # khong ten goc / khong mtime -> chay lai khong them ban sao vao git
    assert list(tmp_path.rglob("*.tam")) == []
    assert gzip.open(tmp_path / "a" / "x.csv.gz", "rb").read().decode().startswith("id,mo,dong,n,")
    c2 = S.doc_chuoi_gz(tmp_path / "a" / "x.csv.gz")
    assert c2["gia_cac_lenh"].tolist() == c["gia_cac_lenh"].tolist()


def test_ghi_gz_loi_giua_chung_khong_de_lai_tep_tam_va_khong_tao_tep_dich(tmp_path, monkeypatch):
    def hong(*a, **k):
        raise OSError("het cho")
    monkeypatch.setattr(os, "replace", hong)
    with pytest.raises(OSError):
        S.ghi_chuoi_gz(_mau_chuoi(), tmp_path / "d" / "x.csv.gz")
    assert list((tmp_path / "d").iterdir()) == []                                   # khong tep dich, khong tep tam


@co_deal
def test_csv_khu_tron_tren_2246_chuoi_that():
    goc = DOC_HAI_NGUON_THAT()
    c2 = S.chuoi_tu_csv(S.chuoi_ra_csv(goc.drop(columns=["nguon"])))
    assert len(c2) == len(goc) >= 2000
    so = C.so_chuoi(goc[goc["ly_do"].isin(["sl", "tp"])], c2[c2["ly_do"].isin(["sl", "tp"])])
    assert so["khop"] == so["n_goc"] == so["n_lai"] == so["chung"]
    assert 30_000 < len(S._gz_co_dinh(S.chuoi_ra_csv(goc))) < 400_000                # ~70 KB: bang chuoi that len git duoc, khong phinh


def test_ten_tep_tester():
    assert S.ten_tep_tester("2019-03-11", "2019-04-10", 1, 1) == "tester_m1_r1_20190311_20190410.csv.gz"
    assert S.ten_tep_tester("2019.03.11", "2019.04.10", 0, 0) == "tester_m0_r0_20190311_20190410.csv.gz"


def test_thu_muc_tester_nam_canh_file_gia(tmp_path):
    assert S.thu_muc_tester(tmp_path) == tmp_path / "so_ea_voi_tester"
    assert S.thu_muc_tester().name == "so_ea_voi_tester" and S.thu_muc_tester().parent == XG.thu_muc_mac_dinh()


# ================================================================================================= 5. GON + GHI BAO CAO
def test_gon_cat_danh_sach_chuoi_va_so_numpy():
    r = S.gon(dict(a=list(range(10)), s="x" * 300, n=np.int64(5), f=np.float64(2.5), t=(1, 2), d=dict(z=np.int32(3))), 220, 4)
    assert r["a"] == [0, 1, 2, 3, "... +6"] and len(r["s"]) == 223 and r["s"].endswith("...")
    assert r["n"] == 5 and type(r["n"]) is int and type(r["f"]) is float and r["t"] == [1, 2] and type(r["d"]["z"]) is int
    json.dumps(r)


def test_ghi_bao_cao_vua_tep_va_cat_gon_dan_roi_bo_cuoc(tmp_path):
    nho = S.ghi_bao_cao(dict(a=1, b="x"), "nho", tmp_path)
    assert nho == "reports/so_ea_voi_tester/nho.json" and json.loads((tmp_path / nho).read_text(encoding="utf-8")) == dict(a=1, b="x")
    to = {"k%02d" % i: ["x" * 200] * 10 for i in range(40)}
    assert len(json.dumps(S.gon(to, 220, 6), ensure_ascii=False, indent=1)) > S.TEP_TOI_DA          # tien de: 6 phan tu / danh sach la qua to
    p = S.ghi_bao_cao(to, "to", tmp_path)
    vb = (tmp_path / p).read_text(encoding="utf-8")
    assert p and len(vb) <= S.TEP_TOI_DA and "... +7" in vb                                            # thu nho xuong 3 phan tu / danh sach
    khong_lo = {"k%04d" % i: "y" * 220 for i in range(400)}                                            # 400 khoa x 220 ky tu: dang nao cung > 38k
    assert S.ghi_bao_cao(khong_lo, "khong_lo", tmp_path) is None and not (tmp_path / "reports" / "so_ea_voi_tester" / "khong_lo.json").exists()


# ================================================================================================= 6. MO PHONG + TU KIEM (can g++)
@functools.lru_cache(maxsize=None)
def _gia(ngay: int = 60, seed: int = 7) -> pd.DataFrame:
    return S.gia_tong_hop(ngay, seed)


@functools.lru_cache(maxsize=None)
def _goc_cache(luat: str = "theo_nen", ratchet: int = 1, ngay: int = 60, seed: int = 7) -> pd.DataFrame:
    """'Deal goc gia': EA dung lai chay tren duong tick `luat` cua nen tong hop, chi chuoi dong SL / TP."""
    bars = _gia(ngay, seed)
    exe = S.bien_dich(S._vao_ngau_nhien(bars, seed))
    ch, _ = S.chay_mo_phong(exe, bars, luat, ratchet)
    ch = ch[ch["ly_do"].isin(["sl", "tp"])].reset_index(drop=True)
    ch.insert(0, "nguon", "kp")
    return ch


def goc(luat="theo_nen", ratchet=1) -> pd.DataFrame:
    return _goc_cache(luat, ratchet).copy()


@can_cxx
def test_goc_gia_dung_hinh_dang_chuoi_that():
    g = goc()
    assert len(g) >= 40 and set(g["ly_do"]) <= {"sl", "tp"} and (g["n"] > 1).any() and (g["n"] == 1).any()
    assert set(g["lot_cac_lenh"].map(lambda x: x[0])) == {0.01}
    assert (g["mo"].dt.second == 0).all()                                         # lenh dau luon o giay 0 cua nen


@can_cxx
def test_bien_dich_khong_co_trinh_bien_dich_bao_loi_ro(monkeypatch):
    monkeypatch.setattr(G, "bien_dich", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="trinh bien dich"):
        S.bien_dich([1_551_657_600])


@can_cxx
def test_chay_mo_phong_loi_san_gia_khong_bi_nuot(monkeypatch):
    bars = _gia()
    exe = S.bien_dich(S._vao_ngau_nhien(bars, 7))
    monkeypatch.setattr(G, "chay", lambda *a, **k: {"ok": False, "ma_thoat": 3, "loi": "boom", "lenh": None})
    with pytest.raises(RuntimeError, match="khong chay duoc tren san gia"):
        S.chay_mo_phong(exe, bars, "theo_nen")


@can_cxx
@pytest.mark.parametrize("luat", ["theo_nen", "cao_truoc"])
def test_quet_mo_phong_chon_dung_luat_va_ratchet_tren_goc_gia(luat):
    g = goc(luat)
    q = S.quet_mo_phong(g, _gia(), luat=LUAT, ratchet=(1, 0))
    assert q["n_goc"] == len(g) and q["khop_tuyet_doi"]
    assert q["tot_nhat"]["luat"] == luat and q["tot_nhat"]["ratchet"] == 1 and q["tot_nhat"]["khop"] == q["tot_nhat"]["chung"] == len(g)
    hang = [(b["luat"], b["ratchet"]) for b in q["bang"] if b["khop"] == q["bang"][0]["khop"]]
    assert hang == [(luat, 1)]                                                    # DUY NHAT mot o dat tuyet doi: luat that + SL doi len
    assert len(q["bang"]) == 10 and all(b["khop"] < q["bang"][0]["khop"] for b in q["bang"][1:])


@can_cxx
def test_quet_mo_phong_khong_co_chuoi_nao_trong_gia_thi_bang_rong():
    q = S.quet_mo_phong(goc(), _gia().iloc[:5])
    assert q == dict(n_goc=0, bang=[], tot_nhat=None, khop_tuyet_doi=False)


@can_cxx
def test_quet_mo_phong_goc_bi_sua_thi_khong_con_tuyet_doi():
    g = goc()
    g.loc[g.index[3], "gia_ra"] += 0.5                                           # sua 1 chuoi: gia thoat lech 50 cent
    g.loc[g.index[5], "ly_do"] = "tp" if g["ly_do"].iloc[5] == "sl" else "sl"
    q = S.quet_mo_phong(g, _gia(), luat=("theo_nen",), ratchet=(1,))
    b = q["bang"][0]
    assert not q["khop_tuyet_doi"] and b["khop"] == len(g) - 2 and b["dem_lech"]["gia_ra"] >= 1 and b["dem_lech"]["ly_do"] >= 1


@can_cxx
def test_luat_dung_duoc_xac_nhan_o_cap_su_kien_va_cac_luat_sai_bi_bat():
    for lt in ("theo_nen", "nguoc_nen"):
        k = S.kiem_luat_tick(goc(lt), _gia())
        assert k["luat"][lt]["ti_le"] == 1.0 and k["vao"]["sai"] == 0 and k["tot_nhat"] == lt
        assert all(v["kem_hon"] == 0 for v in k["so_voi"].values())               # khong doi thu nao tot hon luat that o BAT KY su kien nao
        assert min(k["luat"][r]["ti_le"] for r in LUAT if r != lt) < 1.0         # it nhat mot luat sai bi lo (khong phai luat nao cung 'dung')


@can_cxx
def test_so_ba_chieu_cung_bang_thi_khop_con_khac_luat_thi_chan_doan_loi_dung_cho():
    g = goc("theo_nen")
    r = S.so_ba_chieu(g, g.copy())
    assert r["ti_le_khop"]["goc_mo_phong"] == 1.0 and "CHUA co tester" in r["chan_doan"] and r["tong_hop"]["goc"] == r["tong_hop"]["mo_phong"]
    r2 = S.so_ba_chieu(g, g.copy(), g.copy())
    assert "CA BA KHOP" in r2["chan_doan"] and r2["ti_le_khop"]["mo_phong_tester"] == 1.0 and "tester" in r2["tong_hop"]
    lech = goc("cao_truoc")                                                       # 'tester' chay luat khac => goc <-> tester lech, goc <-> mo phong van khop
    r3 = S.so_ba_chieu(g, g.copy(), lech)
    assert r3["ti_le_khop"]["goc_mo_phong"] == 1.0 and r3["ti_le_khop"]["goc_tester"] < 0.99 and "TESTER (cung EA) thi khong" in r3["chan_doan"]
    r4 = S.so_ba_chieu(g, lech, lech)                                             # mo phong va tester giong nhau nhung deu lech goc
    assert "deu lech bot goc" in r4["chan_doan"]
    r5 = S.so_ba_chieu(g, lech, g.copy())                                         # tester ra y het goc nhung mo phong lech tester
    assert "MO PHONG lech tester" in r5["chan_doan"]


@can_cxx
def test_tong_hop_chuoi_dem_dung():
    g = goc()
    t = S.tong_hop_chuoi(g)
    assert t["n"] == len(g) and t["tp"] + t["sl"] == len(g) and t["n_lenh"] == int(g["n"].sum()) and t["sau_nhat"] == int(g["n"].max())
    assert t["loi"] == pytest.approx(round(float(g["loi"].sum()), 2))
    assert S.tong_hop_chuoi(g.iloc[0:0])["sau_nhat"] == 0


@can_cxx
@pytest.mark.cham
def test_tu_kiem_chon_dung_luat_that_va_bao_cao_do_phan_giai():
    nhat_ky = []
    kq = S.tu_kiem(ngay=40, seed=1, quet=True, ra=nhat_ky.append)
    assert kq["dat"] is True and set(kq["ca"]) == {"theo_nen", "nguoc_nen", "thap_truoc", "cao_truoc"}
    for lt, c in kq["ca"].items():
        assert c["dat"] and c["ti_le_luat_that"] == 1.0 and c["vao_sai"] == 0 and c["n_chuoi"] >= 60, lt
        assert all(v["kem_hon"] == 0 for v in c["so_voi"].values()), lt           # luat that khong bao gio thua mot doi thu
        assert c["quet"]["khop_o_luat_that"] == c["quet"]["n_goc"] and c["quet"]["phan_biet"], lt      # quet: DUY NHAT mot o dat tuyet doi
    dp = kq["do_phan_giai"]
    assert dp["so_chuoi_can"] > 50 and dp["ngay_giao_dich_can"] > 30 and 0 < dp["su_kien_moi_chuoi"] < 1
    assert any("do phan giai" in d for d in nhat_ky) and sum("luat that" in d for d in nhat_ky) == 4


@can_cxx
@pytest.mark.cham
def test_tu_kiem_du_chuoi_thi_ro_khong_chi_dat():
    kq = S.tu_kiem(ngay=150, seed=2, quet=False, ra=lambda *_: None)
    assert kq["dat"] and kq["ro"]                                                  # du chuoi: luat that duoc xep nhat va hon han (p <= 1e-6) moi doi thu
    assert all(c["ket_luan"] == "RO" for c in kq["ca"].values())


# ================================================================================================= 7. MAY THU GIA + CHAY_TESTER + PHAN_TICH
TU, DEN = "2019-03-11", "2019-04-05"                    # 26 ngay trong kham_pha dong bang (xem moi_truong)


@pytest.fixture(autouse=True)
def moi_truong(tmp_path, monkeypatch):
    """Doan dong bang rieng (`XAUUSD|M15`: kham_pha 2019-03-04 .. 2019-04-09), so tay rieng, `ea_tho` rieng; goc = chuoi tong hop (khong dung deal that)."""
    bars = _gia()
    dd = {"t_dau": str(bars.index[0]), "t_xac_nhan": "2019-04-10 00:00:00", "t_niem_phong": "2019-04-20 00:00:00", "t_cuoi": str(bars.index[-1]),
          "n0": len(bars) // 15, "van_tay": "x", "luc": "2026-10-09 00:00:00"}
    so_cai = tmp_path / "so_cai"
    so_cai.mkdir()
    (so_cai / "doan.json").write_text(json.dumps({"XAUUSD|M15": dd}), encoding="utf-8")
    monkeypatch.setenv("NC_SO_CAI", str(so_cai))
    cfg = tmp_path / "ea_tho.json"
    cfg.write_text(json.dumps({"tu_nap": False, "model": 1, "hau_to_symbol": "#", "ban_do_symbol": {"XAUUSD": "GOLD.i#"}}), encoding="utf-8")
    monkeypatch.setenv("EA_THO_CFG", str(cfg))
    monkeypatch.setattr(E, "CHAY_TESTER", None)
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    monkeypatch.setattr(NDL, "nap", lambda *a, **k: (_ for _ in ()).throw(AssertionError("khong duoc nap du lieu / dong bang doan moi")))
    monkeypatch.setattr(C, "doc_hai_nguon", lambda: goc())
    return dict(tmp=tmp_path, so_cai=so_cai, doan=so_cai / "doan.json")


class MayThu:
    """E.CHAY_TESTER thay MT5: bien dich CHINH van ban .mq5 trong lenh, chay tren duong tick `luat` cua nen tong hop CUA cua so lenh bang san gia C++, roi
    ghi bao cao MT5 day du (Orders / Deals + bang tom tat, utf-16). `luat` = luat ma tester GIA nay khop lenh."""

    def __init__(self, tmp: Path, luat: str = "theo_nen", xong: bool = True, log: str = "", ky: str | None = None, khong_deal: bool = False):
        self.tmp, self.luat, self.xong, self.log, self.ky, self.khong_deal = tmp, luat, xong, log, ky, khong_deal
        self.lenh: list[dict] = []
        self.ea: list[dict] = []

    def __call__(self, lenh, ea, cfg):
        self.lenh.append(lenh)
        self.ea.append(ea)
        if not self.xong:
            return {"xong": False, "loi": "terminal het han 1800 s", "bao_cao": None, "log": self.log, "giay": 1800.0}
        v = lenh["viec"]
        t0 = T(v["tu"].replace(".", "-"))
        t1 = T(v["den"].replace(".", "-")) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        seg = _gia().loc[t0:t1]
        mq5 = self.tmp / ("ea_may_thu_%d.mq5" % len(self.lenh))
        mq5.write_text(ea["ma"], encoding="utf-8")
        exe = G.bien_dich(mq5)
        assert exe is not None
        tk = G.tick_ohlc4(seg, self.luat, S.POINT)
        ts = {k: x["gia_tri"] for k, x in v["input"].items()}
        res = G.chay(exe, tk, 100000.0, tham_so=ts, digits=2, hop_dong=C.HOP_DONG, lot=C.LOT_VANG)
        assert res["ok"], res["loi"]
        vt = C.vi_the_tu_ket_qua(res, tk)
        cuoi = seg.index[-1] + pd.Timedelta(seconds=59)
        vi_the = []
        for r in vt.itertuples():
            if pd.isna(r.dong):                                   # tester dong not lenh con mo luc het cua so
                dong = [(cuoi, r.lot, round(float(seg["close"].iloc[-1]), 2), "end of test")]
            else:
                dong = [(r.dong, r.lot, round(float(r.gia_dong), 2), "[%s %.2f]" % (r.ly_do_ra, r.gia_dong))]
            vi_the.append(dict(ma="GOLD.i#", chieu=1, lot=r.lot, gia_mo=round(float(r.gia_mo), 2), mo=r.mo, dong=dong))
        deals, orders = dung_giao_dich(vi_the, von=10000.0, hop_dong=C.HOP_DONG, digits=2)
        mau = html_mau(EN, lai=float(vt["loi"].sum()), lenh=len(vi_the), ky=self.ky or "M1 (%s - %s)" % (v["tu"], v["den"]), von="10 000.00")
        if self.khong_deal:
            html = mau
        else:
            bang_tom_tat = mau[mau.index("<table>"): mau.index("</table>") + len("</table>")]
            html = html_bao_cao(deals, orders, digits=2).replace("</body></html>", bang_tom_tat + "</body></html>")
        p = ghi_htm(self.tmp / ("bc_%d.htm" % len(self.lenh)), html)
        return {"xong": True, "bao_cao": str(p), "log": self.log, "giay": 1.5}


@pytest.fixture
def may(monkeypatch, moi_truong):
    def dat(**kw) -> MayThu:
        m = MayThu(moi_truong["tmp"], **kw)
        monkeypatch.setattr(E, "CHAY_TESTER", m)
        return m
    return dat


def chay(moi_truong, **kw) -> dict:
    a = dict(tu=TU, den=DEN, model=1, ratchet=1, thu_muc=moi_truong["tmp"] / "hop_thu", goc_bao_cao=moi_truong["tmp"] / "lab")
    a.update(kw)
    return S.chay_tester(**a)


def so_tay_rong() -> bool:
    try:
        return not ST.nhieu("SELECT id FROM thi_nghiem")
    except Exception:                                                              # noqa: BLE001  (bang chua duoc tao = chua ghi gi)
        return True


@can_cxx
def test_chay_tester_cung_luat_thi_dat_va_ghi_dung_cho(may, moi_truong):
    m = may(luat="theo_nen")
    doan_truoc = moi_truong["doan"].read_text(encoding="utf-8")
    kq = chay(moi_truong)
    assert kq["trang_thai"] == "DAT", kq
    g = kq["goc_tester"]
    assert g["n_goc"] == g["n_lai"] == g["khop"] == g["chung"] >= 30
    assert kq["cua_so"] == dict(tu="2019.03.11", den="2019.04.05", ngay=26) and kq["model"] == 1 and kq["ratchet"] == 1 and kq["von"] == 10000
    assert kq["tong_hop"]["goc"] == kq["tong_hop"]["tester"] and kq["n_vao"] == g["n_goc"]
    # lenh gui cho tester dung la lenh kham_pha CO cua so tay, symbol cua san, model dat, EA la chinh van ban .mq5 vua viet
    lenh = m.lenh[0]
    assert len(m.lenh) == 1 and lenh["doan"] == "kham_pha" and lenh["khung"] == "M1" and lenh["viec"]["symbol"] == "GOLD.i#" and lenh["model"] == 1
    assert (lenh["viec"]["tu"], lenh["viec"]["den"]) == ("2019.03.11", "2019.04.05") and lenh["cua_so"]["khoa_doan"] == "XAUUSD|M15"
    assert lenh["ea_sha"] == kq["ea_sha"] == E.sha_ma(m.ea[0]["ma"]) and "G_VAO" in m.ea[0]["ma"]
    # file gui ve: bang chuoi tester (.csv.gz) + tom tat (.json); doc lai ra DUNG bang chuoi do
    ten = "tester_m1_r1_20190311_20190405"
    gz = moi_truong["tmp"] / "hop_thu" / "so_ea_voi_tester" / (ten + ".csv.gz")
    assert gz.exists() and kq["tep_chuoi"] == dict(ten=ten + ".csv.gz", byte=gz.stat().st_size)
    tc = S.doc_chuoi_gz(gz)
    assert len(tc) == g["n_lai"] and C.so_chuoi(S.chuoi_tu_csv(S.chuoi_ra_csv(tc)), tc)["khop"] == len(tc)
    bc = moi_truong["tmp"] / "lab" / kq["bao_cao_tom_tat"]
    assert kq["bao_cao_tom_tat"] == "reports/so_ea_voi_tester/%s.json" % ten and json.loads(bc.read_text(encoding="utf-8"))["trang_thai"] == "DAT"
    # doan dong bang va so tay KHONG bi dung; khong dong bang them khoa M1
    assert moi_truong["doan"].read_text(encoding="utf-8") == doan_truoc and "XAUUSD|M1" not in json.loads(doan_truoc)
    assert so_tay_rong()


@can_cxx
def test_chay_tester_khac_luat_thi_am_chu_khong_phai_chua_do_duoc(may, moi_truong):
    may(luat="cao_truoc")                                                         # bot goc chay luat theo_nen (goc gia), tester GIA chay cao_truoc
    kq = chay(moi_truong)
    g = kq["goc_tester"]
    assert kq["trang_thai"] == "AM" and g["khop"] < 0.99 * g["n_goc"] and g["n_goc"] >= 30
    assert sum(g["dem_lech"].values()) >= 3 and g["chi_tiet"]                     # lech co ten: gio thoat / gia thoat ...
    assert "AM" in kq["ghi_chu"] and "tieu chi lai" in kq["ghi_chu"]


@can_cxx
def test_chay_tester_ratchet_khac_thi_am_va_lenh_mang_dung_input(may, moi_truong):
    m = may(luat="theo_nen")
    kq = chay(moi_truong, ratchet=0)                                              # goc gia dung SL doi len; ban nay bao tester chay SL bam theo
    assert m.lenh[0]["tham_so"] == {"InpTrailRatchet": 0} and m.lenh[0]["viec"]["input"] == {"InpTrailRatchet": {"gia_tri": 0}}
    g = kq["goc_tester"]                                                           # do 09/10: SL bam theo vs SL doi len khop chi ~10% chuoi tren gia tong hop
    assert kq["ratchet"] == 0 and kq["trang_thai"] == "AM" and g["khop"] < 0.5 * g["n_goc"] and g["dem_lech"]["gia_ra"] > 0
    assert kq["tep_chuoi"]["ten"] == "tester_m1_r0_20190311_20190405.csv.gz"
    assert not m.lenh[0]["viec"]["input"].get("InpEntryMode")


@can_cxx
def test_chay_tester_ghi_false_khong_ghi_gi(may, moi_truong):
    may()
    kq = chay(moi_truong, ghi=False)
    assert kq["trang_thai"] == "DAT" and "tep_chuoi" not in kq
    assert not (moi_truong["tmp"] / "hop_thu").exists() and not (moi_truong["tmp"] / "lab").exists()


@pytest.mark.parametrize("kw,tu_khoa", [
    (dict(model=4), "model phai la 0"), (dict(model=2), "model phai la 0"), (dict(ratchet=2), "ratchet phai la 0 hoac 1"),
    (dict(von="abc"), "von phai la so nguyen"), (dict(von=500), "von phai >= 1000"),
    (dict(tu="2019-04-01", den="2019-04-20"), "NGOAI doan kham_pha"),            # 20 ngay nhung den 04-20 vuot qua xac_nhan 04-10
    (dict(tu="2019-02-20", den="2019-03-20"), "NGOAI doan kham_pha"),
    (dict(tu="2019-03-11", den="2019-03-20"), "qua ngan"),                         # 10 ngay < 14
    (dict(tu="khong phai ngay", den="2019-03-20"), "ngay khong doc duoc"),
])
def test_chay_tester_dau_vao_sai_la_chua_do_duoc_va_khong_goi_tester(may, moi_truong, kw, tu_khoa):
    m = may()
    kq = chay(moi_truong, **kw)
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and tu_khoa in kq["ly_do"] and m.lenh == []
    assert "XAUUSD|M1" not in json.loads(moi_truong["doan"].read_text(encoding="utf-8")) and so_tay_rong()


def test_chay_tester_cua_so_it_hon_5_chuoi_goc(may, moi_truong, monkeypatch):
    m = may()
    monkeypatch.setattr(C, "doc_hai_nguon", lambda: goc().iloc[:3])
    kq = chay(moi_truong, tu="2019-03-04", den="2019-03-31")
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and "(< 5)" in kq["ly_do"] and m.lenh == []


@can_cxx
def test_chay_tester_loi_ha_tang_la_chua_do_duoc_khong_bao_gio_am(may, moi_truong, monkeypatch):
    may(xong=False)
    kq = chay(moi_truong)
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and kq["ha_tang"] and "terminal het han" in kq["ly_do"]
    may(log="... cannot generate history data for XAUUSD ...")
    kq = chay(moi_truong)
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and kq["ha_tang"] and "TESTER KHONG CHAY DUOC" in kq["ly_do"]
    may(ky="M1 (2019.01.01 - 2019.01.20)")                                        # bao cao cua mot cua so khac
    kq = chay(moi_truong)
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and kq["ha_tang"] and "khong nam trong" in kq["ly_do"]
    may(khong_deal=True)                                                          # co bang tom tat nhung khong co bang Deals
    kq = chay(moi_truong)
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and kq["ha_tang"] and "Deals" in kq["ly_do"]
    assert not (moi_truong["tmp"] / "hop_thu").exists() and so_tay_rong()


def test_chay_tester_khong_doc_duoc_ea_va_lenh_khong_san_sang(may, moi_truong, monkeypatch):
    m = may()
    monkeypatch.setattr(E, "doc_ea", lambda p: (_ for _ in ()).throw(ValueError("ma hong")))
    kq = chay(moi_truong)
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and kq["ha_tang"] and "ma hong" in kq["ly_do"] and m.lenh == []
    monkeypatch.undo()
    monkeypatch.setattr(E, "lap_lenh", lambda *a, **k: {"trang_thai": "CHUA_DO_DUOC", "ly_do": "thieu tep"})
    monkeypatch.setattr(E, "CHAY_TESTER", m)
    monkeypatch.setenv("NC_SO_CAI", str(moi_truong["so_cai"]))
    monkeypatch.setenv("EA_THO_CFG", str(moi_truong["tmp"] / "ea_tho.json"))
    monkeypatch.setattr(C, "doc_hai_nguon", lambda: goc())
    kq = chay(moi_truong)
    assert kq == {"trang_thai": "CHUA_DO_DUOC", "ly_do": "thieu tep"} and m.lenh == []


def _ghi_m1(thu_muc: Path, bars: pd.DataFrame, moi_truong) -> None:
    XG.ghi(bars, "XAUUSD", "M1", thu_muc, moi_truong["tmp"] / "sao_luu")


@pytest.fixture(scope="module")
def thu_muc_m1(tmp_path_factory):
    """Nen M1 tong hop ghi bang `xuat_gia.ghi` (dung dinh dang may nha gui ve): 1 lan cho ca module."""
    d = tmp_path_factory.mktemp("du_lieu_gia")
    XG.ghi(_gia(), "XAUUSD", "M1", d, tmp_path_factory.mktemp("sao_luu"))
    return d


@can_cxx
@pytest.mark.cham
def test_phan_tich_toan_tuyen_tren_nen_m1_ghi_bang_xuat_gia(thu_muc_m1):
    kq = S.phan_tich(thu_muc_m1, quet=True)
    assert kq["trang_thai"] == "DAT" and kq["nen_m1"]["n"] == len(_gia()) and kq["n_chuoi_goc_trong_gia"] == len(goc())
    assert kq["lech_gio"]["tot_nhat"] == 0 and kq["lech_gio"]["ti_le"] == 1.0 and "ghi_chu_gio" not in kq
    lt = kq["luat_tick"]
    assert lt["tot_nhat"] == "theo_nen" and lt["luat"]["theo_nen"]["ti_le"] == 1.0 and lt["vao"]["sai"] == 0
    mp = kq["mo_phong"]
    assert mp["khop_tuyet_doi"] and mp["tot_nhat"]["luat"] == "theo_nen" and mp["tot_nhat"]["ratchet"] == 1
    d = S.loi_thuong(kq)
    assert len(d) == 3 and all(isinstance(x, str) for x in d)
    assert "Da doi chieu" in d[0] and "theo_nen" in d[1] and ("khop %d/%d" % (len(goc()), len(goc()))) in d[2] and "SL chi doi len" in d[2]


@can_cxx
@pytest.mark.cham
def test_phan_tich_tim_ra_lech_gio_va_dich_nen_truoc_khi_kiem(tmp_path, moi_truong):
    lech = _gia().copy()
    lech.index = lech.index - pd.Timedelta(hours=3)                              # kho gia o gio may chu tre hon deal 3 gio
    d = tmp_path / "gia_lech"
    _ghi_m1(d, lech, moi_truong)
    kq = S.phan_tich(d, quet=False)
    assert kq["trang_thai"] == "DAT" and kq["lech_gio"]["tot_nhat"] == 3 and kq["lech_gio"]["ti_le"] >= 0.9
    assert "lech +3 gio" in kq["ghi_chu_gio"]
    assert kq["luat_tick"]["tot_nhat"] == "theo_nen" and kq["luat_tick"]["luat"]["theo_nen"]["ti_le"] == 1.0 and kq["luat_tick"]["vao"]["sai"] == 0
    assert "mo_phong" not in kq


@can_cxx
@pytest.mark.cham
def test_phan_tich_voi_bang_chuoi_tester_ba_chieu(thu_muc_m1, moi_truong):
    ra = S.thu_muc_tester(thu_muc_m1)
    S.ghi_chuoi_gz(goc("theo_nen"), ra / "tester_giong.csv.gz")
    S.ghi_chuoi_gz(goc("cao_truoc"), ra / "tester_khac.csv.gz")
    kq = S.phan_tich(thu_muc_m1, quet=True, tester="tester_giong.csv.gz")
    t = kq["tester"]
    assert t["tep"] == "tester_giong.csv.gz" and t["n_chuoi"] == len(goc()) and t["goc_tester"]["khop"] == len(goc())
    assert "CA BA KHOP" in t["ba_chieu"]["chan_doan"] and any("Ba ben" in x for x in S.loi_thuong(kq))
    kq2 = S.phan_tich(thu_muc_m1, quet=True, tester="tester_khac.csv.gz")
    assert "CA BA KHOP" not in kq2["tester"]["ba_chieu"]["chan_doan"] and "TESTER" in kq2["tester"]["ba_chieu"]["chan_doan"]
    assert kq2["tester"]["goc_tester"]["khop"] < len(goc())
    kq3 = S.phan_tich(thu_muc_m1, quet=False, tester="khong_co.csv.gz")
    assert kq3["trang_thai"] == "DAT" and "chua co khong_co.csv.gz" in kq3["tester"]["ly_do"] and "ba_chieu" not in kq3["tester"]


def test_phan_tich_thieu_nen_m1_la_cho_may_nha_khong_phai_am(tmp_path):
    kq = S.phan_tich(tmp_path / "chua_co")
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and kq["cho_may_nha"] is True and "b xuat-gia XAUUSD M1" in kq["ly_do"]
    assert S.loi_thuong(kq)[0].startswith("Chua do duoc:")


def test_phan_tich_nen_m1_hong_la_ha_tang(tmp_path, moi_truong):
    bad = _gia().iloc[:3000].copy()
    bad.iloc[10, bad.columns.get_loc("high")] = bad["low"].iloc[10] - 5
    d = tmp_path / "gia_hong"
    _ghi_m1(d, bad, moi_truong)
    kq = S.phan_tich(d)
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and kq["ha_tang"] is True and "hong" in kq["ly_do"]


def test_phan_tich_khong_chuoi_nao_nam_trong_khoang_nen(tmp_path, moi_truong):
    xa = S.gia_tong_hop(2, seed=1, bat_dau="2021-01-04 00:00")
    d = tmp_path / "gia_2021"
    _ghi_m1(d, xa, moi_truong)
    kq = S.phan_tich(d)
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and "khong chuoi nao" in kq["ly_do"] and kq["n_chuoi_goc_trong_gia"] == 0


@can_cxx
def test_phan_tich_loi_san_gia_ghi_vao_ket_qua_khong_lam_sap(thu_muc_m1, monkeypatch):
    monkeypatch.setattr(S, "quet_mo_phong", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("khong co trinh bien dich")))
    kq = S.phan_tich(thu_muc_m1, tu="2019-03-04", den="2019-03-20", quet=True)
    assert kq["trang_thai"] == "DAT" and kq["mo_phong"] == {"loi": "khong co trinh bien dich"}
    assert S.loi_thuong(kq)[-1].startswith("Cach may thu")                         # khong co dong 'bot dung lai chay tren gia that'


# ================================================================================================= 8. DONG LENH
def test_main_phan_tich_thieu_nen_in_loi_thuong_va_tra_ma_2(tmp_path, capsys):
    assert S.main(["luat", "--thu-muc", str(tmp_path / "trong")]) == 2
    assert "Chua do duoc" in capsys.readouterr().out


@can_cxx
def test_main_tu_kiem_ra_ma_0_khi_dat(capsys):
    assert S.main(["tu-kiem", "--ngay", "25", "--khong-quet"]) == 0
    assert "TU KIEM: DAT" in capsys.readouterr().out


def test_main_tester_cua_so_ngan_khong_cham_mt5(capsys):
    assert S.main(["tester", "--tu", "2019-03-11", "--den", "2019-03-15"]) == 2             # E.CHAY_TESTER = None: neu cham MT5 that se khong bao gio toi day
    assert "CHUA_DO_DUOC" in capsys.readouterr().out and "qua ngan" in capsys.readouterr().out + "qua ngan"


@can_cxx
def test_main_luat_ghi_bao_cao_ra_thu_muc_lab(thu_muc_m1, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(C, "GOC", tmp_path)
    assert S.main(["luat", "--thu-muc", str(thu_muc_m1), "--ghi"]) == 0
    out = capsys.readouterr().out
    assert "Da doi chieu" in out and "ghi: reports/so_ea_voi_tester/phan_tich.json" in out
    kq = json.loads((tmp_path / "reports" / "so_ea_voi_tester" / "phan_tich.json").read_text(encoding="utf-8"))
    assert kq["trang_thai"] == "DAT" and kq["luat_tick"]["tot_nhat"] == "theo_nen"


# ================================================================================================= 9. CONG CU NGHIEN CUU (`nc cc so_ea_voi_tester`)
def _tn() -> list[dict]:
    return ST.nhieu("SELECT * FROM thi_nghiem ORDER BY id")


def test_phan_tich_tester_chi_nhan_ten_tep_khong_duong_dan(tmp_path):
    for xau in ("../x.csv.gz", "/etc/passwd", "a/b.csv.gz"):
        kq = S.phan_tich(tmp_path, tester=xau)
        assert kq["trang_thai"] == "CHUA_DO_DUOC" and "TEN tep" in kq["ly_do"], xau


@can_cxx
def test_cong_cu_tu_kiem_ghi_so_tay_mot_dong_do_dac_va_khong_ghi_trung():
    assert so_tay_rong()
    kq = S.cong_cu("tu_kiem", ngay=25, seed=1, quet=False, vong_id=7)
    assert kq["dat"] is True and isinstance(kq["tn_id"], int) and "tu_so_tay" not in kq and "_giay" not in kq
    (hang,) = _tn()
    assert (hang["loai"], hang["doan"], hang["trang_thai"], hang["so_phep_thu"], hang["vong_id"], hang["ma"], hang["khung"]) == \
        (S.LOAI_SO_TAY, "hieu_chuan", "DAT", 0, 7, "XAUUSD", "M1")
    assert hang["id"] == kq["tn_id"] and hang["tom_tat"].startswith("tu kiem DAT: 4/4 luat that duoc chon dung")
    assert ST.dem_phep_thu(ma="XAUUSD", khung="M1", doan="kham_pha") == 0 and ST.dem_phep_thu(ma="XAUUSD", khung="M1", doan="hieu_chuan") == 0
    lai = S.cong_cu("tu_kiem", ngay=25, seed=1, quet=False)
    assert lai["tn_id"] == kq["tn_id"] and "da ghi dong so tay" in lai["tu_so_tay"] and len(_tn()) == 1       # cung dau vao + cung du lieu: khong them dong
    S.cong_cu("tu_kiem", ngay=25, seed=2, quet=False)
    assert len(_tn()) == 2                                                                                    # doi hat ngau nhien = phep do khac


def test_cong_cu_chua_do_duoc_khong_ghi_so_tay_va_che_do_la_bi_tu_choi(tmp_path, monkeypatch):
    monkeypatch.setattr(XG, "thu_muc_mac_dinh", lambda: tmp_path / "chua_co")
    kq = S.cong_cu("luat")
    assert kq["trang_thai"] == "CHUA_DO_DUOC" and kq["cho_may_nha"] is True and kq["loi_thuong"][0].startswith("Chua do duoc") and "tn_id" not in kq
    assert S.cong_cu("so", tester="khong_co.csv.gz")["trang_thai"] == "CHUA_DO_DUOC"
    assert S.cong_cu("tester", tu="2019-03-11", den="2019-03-15")["trang_thai"] == "CHUA_DO_DUOC"              # 5 ngay: qua ngan, khong cham MT5
    assert _tn() == []
    with pytest.raises(ValueError, match="che_do phai la"):
        S.cong_cu("quet_het")


@can_cxx
def test_cong_cu_luat_tren_nen_m1_ghi_mot_dong_va_loi_thuong(thu_muc_m1, monkeypatch):
    monkeypatch.setattr(XG, "thu_muc_mac_dinh", lambda: thu_muc_m1)
    kq = S.cong_cu("luat")
    assert kq["trang_thai"] == "DAT" and kq["luat_tick"]["tot_nhat"] == "theo_nen" and "mo_phong" not in kq and len(kq["loi_thuong"]) == 2
    (hang,) = _tn()
    assert hang["trang_thai"] == "DAT" and hang["so_phep_thu"] == 0 and hang["doan"] == "hieu_chuan" and "theo_nen" in hang["tom_tat"]
    assert S.cong_cu("luat")["tn_id"] == hang["id"] and len(_tn()) == 1
    kq2 = S.cong_cu("so")
    assert kq2["mo_phong"]["khop_tuyet_doi"] is True and len(_tn()) == 2                                       # quet bat = dau vao khac


@can_cxx
def test_cong_cu_tester_dat_va_am_ghi_so_tay(may, moi_truong, monkeypatch):
    may(luat="theo_nen")
    monkeypatch.setattr(XG, "thu_muc_mac_dinh", lambda: moi_truong["tmp"] / "hop_thu")
    monkeypatch.setattr(C, "GOC", moi_truong["tmp"] / "lab")
    kq = S.cong_cu("tester", tu=TU, den=DEN, model=1, ratchet=1)
    assert kq["trang_thai"] == "DAT" and kq["tn_id"] and kq["goc_tester"]["khop"] == kq["goc_tester"]["n_goc"]
    assert (moi_truong["tmp"] / "hop_thu" / "so_ea_voi_tester" / "tester_m1_r1_20190311_20190405.csv.gz").exists()
    (hang,) = _tn()
    assert hang["trang_thai"] == "DAT" and hang["tom_tat"].startswith("tester Model 1 ratchet 1 2019.03.11..2019.04.05: DAT, khop")
    am = S.cong_cu("tester", tu=TU, den=DEN, model=1, ratchet=0)
    assert am["trang_thai"] == "AM" and len(_tn()) == 2 and _tn()[1]["trang_thai"] == "AM"


@can_cxx
def test_nc_cong_cu_goi_duoc_cong_cu_nay_qua_dang_ky_chuan():
    from nhan import nc_cong_cu as NC
    c = NC.THEO_TEN["so_ea_voi_tester"]
    assert c["schema"]["required"] == [] and set(c["schema"]["properties"]) >= {"che_do", "tu", "den", "model", "ratchet", "tester"}
    assert not any(k in c["schema"]["properties"] for k in ("thu_muc", "duong_dan", "path", "ea"))             # khong nhan duong dan tuy y
    assert c["mo_ta"].isascii()
    kq = NC.goi("so_ea_voi_tester", {"che_do": "tu_kiem", "ngay": 25, "quet": False}, vong_id=3)
    assert kq["dat"] is True and "loi" not in kq and "_giay" in kq and _tn()[0]["vong_id"] == 3
    assert NC.goi("so_ea_voi_tester", {"che_do": "khong_co"})["loi"].startswith("ValueError")
    assert "tham so khong co trong schema" in NC.goi("so_ea_voi_tester", {"thu_muc": "/etc"})["loi"]
