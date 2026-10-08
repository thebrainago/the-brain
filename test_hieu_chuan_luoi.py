# -*- coding: utf-8 -*-
"""hieu_chuan_luoi: engine luoi <-> MT5 tester, CUNG cua so + CUNG tham so, hai con so canh nhau.

Khong co MT5 o day: tester la `MayGia` - nhan LENH THAT cua `ea_tho.lap_lenh` va tra mot BAO CAO MT5 DAY DU (bang Deals / Orders +
bang tom tat, utf-16) dung bo cuc `test_lenh_tester` / `test_bao_cao_mt5`: chinh `luoi.chay` tren bar tong hop, mua khop gia ask (spread
nam TRONG gia), deal 'end of test' cho lenh con mo, swap chia theo lot x thoi gian giu, hop dong hieu dung = hop dong / f (tien bao gia khac
tien tai khoan). Vi MayGia dung chinh engine nen KHOP la dieu phai co: cai duoc kiem o day la DUONG ONG (doc bao cao -> ghep lenh -> uoc
he so quy doi -> so sanh -> so tay -> cache), va cac phep thu am (tester chay tham so KHAC, ha tang hong) phai bi bat. Engine co dung voi
MT5 THAT khong la viec cua may nha (`b nc cc hieu_chuan_luoi`): bao cao that dau tien phai them vao day.
"""
from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import ea_gia_lap as G
from nhan import ea_tho as E
from nhan import hieu_chuan_luoi as HC
from nhan import kien_truc as KT
from nhan import luoi as LU
from nhan import nc_cong_cu as CC
from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from qwen import cau_trang as CT
from test_bao_cao_mt5 import EN, html_mau
from test_lenh_tester import CAU_HINH, HOP_FX, bars_that, dung_giao_dich, ghi_htm, html_bao_cao, vi_the_tu_engine

DF = bars_that(6000)                       # M15 2024-01-01 .. 2024-03-03; kham_pha = 60% dau = 2024.01.01 .. 2024.02.06 (37 ngay)
N = len(DF)
TS_DICT = {"buoc": 15, "tp": 6, "tran_tang": 5, "che_do": "hai_chieu", "lot": 0.01}
TS = LU.ThamSo(**TS_DICT)
CUA_SO = ("2024-01-01", "2024-02-06")
F_THAT = 1.3                               # AUDCAD tren tai khoan USD ~ 1,31..1,33
VON = 10000.0


# ================================================================= HA TANG TEST: moi truong + MAY GIA
@pytest.fixture(autouse=True)
def moi_truong(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    dd = {"t_dau": str(DF.index[0]), "t_xac_nhan": str(DF.index[int(0.6 * N)]), "t_niem_phong": str(DF.index[int(0.8 * N)]),
          "t_cuoi": str(DF.index[-1]), "n0": N, "van_tay": "x", "luc": "2026-10-04 00:00:00"}
    so_cai = tmp_path / "so_cai"
    so_cai.mkdir()
    (so_cai / "doan.json").write_text(json.dumps({"AUDCAD|M15": dd, "US500|M15": dd}), encoding="utf-8")
    monkeypatch.setenv("NC_SO_CAI", str(so_cai))
    cfg = tmp_path / "ea_tho.json"
    cfg.write_text(json.dumps({"tu_nap": False}), encoding="utf-8")
    monkeypatch.setenv("EA_THO_CFG", str(cfg))
    monkeypatch.setattr(E, "CHAY_TESTER", None)
    monkeypatch.setattr(HC, "THU_MUC", tmp_path / "hc")
    df = DF.copy()
    df.attrs["doan_dong_bang"] = dict(dd)
    monkeypatch.setattr(NDL, "nap", lambda ma, khung="H4": df)
    return {"dd": dd, "tmp": tmp_path, "df": df}


_HTML: dict = {}


def _bao_cao_html(ts_dict: dict, f: float, swap: bool, dong_cuoi: bool, tu: str, den: str, ky: str | None,
                  chat_luong: int | None, khong_deal: bool) -> str:
    """Bao cao tester (HTML day du) cho mot cua so; nho theo tham so vi chay engine 0,5 giay moi lan."""
    khoa = (tuple(sorted(ts_dict.items())), f, swap, dong_cuoi, tu, den, ky, chat_luong, khong_deal)
    if khoa in _HTML:
        return _HTML[khoa]
    ts = LU.ThamSo(**ts_dict)
    t0 = pd.Timestamp(tu.replace(".", "-"))
    t1 = pd.Timestamp(den.replace(".", "-")) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    seg = DF.loc[t0:t1]
    vt = vi_the_tu_engine(ts, seg)
    if dong_cuoi:                          # tester dong not lenh con mo luc het cua so: deal comment 'end of test'
        for p in vt:
            if not p["dong"]:
                p["dong"] = [(seg.index[-1] + pd.Timedelta(seconds=30), p["lot"], round(float(seg["close"].iloc[-1]), 5), "end of test")]
    sp = float(seg["spread"].iloc[0]) * 1e-5
    for p in vt:                           # spread nam TRONG gia (mua khop ask, dong lenh ban o ask) - khong hoa hong rieng
        if p["chieu"] > 0:
            p["gia_mo"] = round(p["gia_mo"] + sp, 5)
        elif p["dong"]:
            g = p["dong"][0]
            p["dong"] = [(g[0], g[1], round(g[2] + sp, 5), g[3])]
    deals, orders = dung_giao_dich(vt, von=VON, hop_dong=HOP_FX / f, hoa_hong_lot=0.0)
    kq = LU.chay(seg, ts, VON * f, ghi_lenh=False)
    if swap:                               # swap cua engine chia theo lot x thoi gian giu, lam tron cent, phan du vao deal lon nhat
        can = []
        for p in vt:
            for j, (t_ra, lot, _g, _c) in enumerate(p["dong"]):
                can.append((p["deal_ra"][j], lot * max((pd.Timestamp(t_ra) - pd.Timestamp(p["mo"])).total_seconds(), 1.0)))
        tong = -float(kq.phi_swap) / f
        tong_can = sum(w for _, w in can)
        phan, da = {}, 0.0
        for did, w in can:
            phan[did] = round(tong * w / tong_can, 2)
            da += phan[did]
        du = round(tong - da, 2)
        if du:
            lon = max(can, key=lambda x: x[1])[0]
            phan[lon] = round(phan[lon] + du, 2)
        so_du = VON
        for d in deals:
            if d["loai"] == "balance":
                continue
            d["swap"] = phan.get(d["deal"], 0.0)
            so_du = round(so_du + (d["loi"] or 0) + (d["hoa_hong"] or 0) + d["swap"], 2)
            d["so_du"] = so_du
    lai = deals[-1]["so_du"] - VON
    dd = abs(LU.chi_so(kq, VON * f)["maxdd_pct"])
    mau = html_mau(EN, lai=lai, lenh=len(vt), dd="%.2f (%.2f%%)" % (dd * VON / 100, dd),
                   ky=ky or "M15 (%s - %s)" % (tu, den), von="{:,.2f}".format(VON).replace(",", " "))
    mau = mau.replace("<b>21.00% (2 100.00)</b>", "<b>%.2f%% (%.2f)</b>" % (dd, dd * VON / 100))
    if chat_luong is not None:
        mau = mau.replace("<b>100%</b>", "<b>%d%%</b>" % chat_luong)
    if khong_deal:
        html = mau
    else:
        bang = mau[mau.index("<table>"): mau.index("</table>") + len("</table>")]
        html = html_bao_cao(deals, orders).replace("</body></html>", bang + "</body></html>")
    _HTML[khoa] = html
    return html


class MayGia:
    """E.CHAY_TESTER thay MT5: ghi bao cao MT5 DAY DU cho cua so cua lenh. `ts` = ThamSo ma tester gia THUC SU chay (khac lenh -> phep am)."""

    def __init__(self, tmp: Path, ts: dict | None = None, f: float = F_THAT, swap: bool = True, dong_cuoi: bool = True,
                 xong: bool = True, log: str = "", ky: str | None = None, chat_luong: int | None = None, khong_deal: bool = False):
        self.tmp, self.ts, self.f, self.swap, self.dong_cuoi = tmp, dict(ts or TS_DICT), f, swap, dong_cuoi
        self.xong, self.log, self.ky, self.chat_luong, self.khong_deal = xong, log, ky, chat_luong, khong_deal
        self.lenh: list[dict] = []

    @property
    def lan(self) -> int:
        return len(self.lenh)

    def __call__(self, lenh, ea, cfg):
        self.lenh.append(lenh)
        if not self.xong:
            return {"xong": False, "loi": "terminal het han 1800 s", "bao_cao": None, "log": self.log, "giay": 1800.0}
        v = lenh["viec"]
        html = _bao_cao_html(self.ts, self.f, self.swap, self.dong_cuoi, v["tu"], v["den"], self.ky, self.chat_luong, self.khong_deal)
        p = ghi_htm(self.tmp / ("bc_%d.htm" % len(self.lenh)), html)
        return {"xong": True, "bao_cao": str(p), "log": self.log, "giay": 1.5}


@pytest.fixture
def may(monkeypatch, moi_truong):
    def dat(**kw) -> MayGia:
        m = MayGia(moi_truong["tmp"], **kw)
        monkeypatch.setattr(E, "CHAY_TESTER", m)
        return m
    return dat


def chay(**kw) -> dict:
    a = dict(ma="AUDCAD", khung="M15", tu=CUA_SO[0], den=CUA_SO[1], tham_so=dict(TS_DICT), model=0, von=10000)
    a.update(kw)
    return HC.hieu_chuan(**a)


def dong_so_tay() -> list[dict]:
    return ST.nhieu("SELECT id, loai, doan, so_phep_thu, trang_thai, ma, khung FROM thi_nghiem ORDER BY id")


def _cfg() -> dict:
    return dict(E.cau_hinh(), tick_tu=None)


# ================================================================= A. CUA SO + DAU VAO (khong ton tester)
def test_cua_so_trong_doan_kham_pha_duoc_chap_nhan_ca_hai_mep():
    cs, ly = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-10", "2024-01-31", _cfg())
    assert ly is None and cs["tu"] == "2024.01.10" and cs["den"] == "2024.01.31" and cs["ngay"] == 22
    kh = E.ke_hoach("AUDCAD", "M15", "kham_pha", _cfg())
    assert (kh["tu"], kh["den"]) == ("2024.01.01", "2024.02.06")      # cua so dong bang = 37 ngay
    cs, ly = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-01", "2024-02-06", _cfg())
    assert ly is None and cs["ngay"] == 37 and cs["khoa_doan"] == kh["khoa_doan"]


@pytest.mark.parametrize("tu,den", [("2023-12-31", "2024-01-20"), ("2024-01-20", "2024-02-07"), ("2023-06-01", "2024-03-01"),
                                    ("2024-02-07", "2024-03-02")])
def test_cua_so_lot_ra_ngoai_doan_kham_pha_bi_tu_choi(tu, den):
    cs, ly = HC.chuan_cua_so("AUDCAD", "M15", tu, den, _cfg())
    assert cs is None and "NGOAI doan kham_pha" in ly and "xac_nhan" in ly      # khong cham xac_nhan / niem_phong


def test_cua_so_qua_ngan_14_ngay():
    cs, ly = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-10", "2024-01-22", _cfg())          # 13 ngay
    assert cs is None and "13 ngay" in ly
    cs, ly = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-10", "2024-01-23", _cfg())          # 14 ngay
    assert ly is None and cs["ngay"] == 14
    cs, ly = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-30", "2024-01-10", _cfg())          # den < tu
    assert cs is None and "ngay" in ly


@pytest.mark.parametrize("tu", ["2024.01.05", "2024/01/05", "2024-01-05", "2024-01-05 13:30:00", " 2024-01-05 "])
def test_doc_ngay_cac_dang(tu):
    assert HC._ngay(tu).isoformat() == "2024-01-05"


def test_doc_ngay_kieu_date_va_datetime_va_rac():
    from datetime import date, datetime
    assert HC._ngay(date(2024, 1, 5)).isoformat() == "2024-01-05"
    assert HC._ngay(datetime(2024, 1, 5, 23, 59)).isoformat() == "2024-01-05"
    cs, ly = HC.chuan_cua_so("AUDCAD", "M15", "2024-13-45", "2024-02-06", _cfg())
    assert cs is None and "khong doc duoc" in ly
    cs, ly = HC.chuan_cua_so("AUDCAD", "M15", "hom qua", "2024-02-06", _cfg())
    assert cs is None and "khong doc duoc" in ly


def test_cua_so_ma_chua_dong_bang_thi_khong_tu_dong_bang():
    cs, ly = HC.chuan_cua_so("EURUSD", "M15", "2024-01-10", "2024-01-31", _cfg())
    assert cs is None and ly


@pytest.mark.parametrize("sai,ly_co", [
    (dict(von=10000.5), "SO NGUYEN"), (dict(von=50), "SO NGUYEN"), (dict(von="abc"), "von"), (dict(von=float("nan")), "SO NGUYEN"),
    (dict(model=2), "model"), (dict(model=3), "model"), (dict(khung="M7"), "khung"),
    (dict(tham_so={"khong_co_truong_nay": 1}), "khong_co_truong_nay"), (dict(tham_so={"dung_lo_tong": 5}), "dung_lo_tong"),
    (dict(tham_so="buoc=15"), "object"), (dict(han_giay=30), "han_giay"), (dict(han_giay="nhanh"), "han_giay"),
    (dict(von_quy_doi=0.01), "von_quy_doi"), (dict(von_quy_doi=25), "von_quy_doi"), (dict(von_quy_doi="1,3"), "von_quy_doi"),
    (dict(tham_so={"buoc": "mot"}), "SO huu han"),
])
def test_dau_vao_sai_bi_chan_truoc_khi_ton_tester(may, sai, ly_co):
    m = may()
    r = chay(**sai)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and ly_co in r["ly_do"], r
    assert m.lan == 0 and dong_so_tay() == []


def test_ma_engine_khong_ho_tro_dung_truoc_tester(may):
    m = may()
    r = chay(ma="US500")
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "chua ho tro cho luoi" in r["ly_do"], r
    assert m.lan == 0 and dong_so_tay() == []


def test_du_lieu_lab_thieu_dung_truoc_tester(may, moi_truong, monkeypatch):
    m = may()
    ngan = DF.iloc[:1000].copy()
    ngan.attrs["doan_dong_bang"] = dict(moi_truong["dd"])
    monkeypatch.setattr(NDL, "nap", lambda ma, khung="H4": ngan)
    r = chay()
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r.get("ha_tang") and "du lieu lab" in r["ly_do"], r
    assert m.lan == 0 and dong_so_tay() == []


# ================================================================= B. CHAY TRON VONG (may gia tra bao cao MT5 day du)
def test_khop_ghi_dung_hai_dong_so_tay_va_khong_an_phep_thu(may):
    m = may()
    r = chay()
    assert r["trang_thai"] == "DAT" and r["ket_luan"] == "KHOP", r["ly_do"]
    assert m.lan == 1 and r["tester_tu_cache"] is False and all(r["khop"].values())
    t, e = r["tester"], r["engine"]
    assert t["thong_ke"]["so_lenh_mo"] == e["thong_ke"]["so_lenh_mo"] > 100
    assert abs(t["lai_nam_pct"] - e["lai_nam_pct"]) < 0.1
    assert abs(t["dd"]["so_sanh_pct"] - e["dd_pct"]) < 0.05
    assert abs(r["he_so_quy_doi"]["dung"] - F_THAT) / F_THAT < 0.03 and "uoc luong tu" in r["he_so_quy_doi"]["nguon"]
    rows = dong_so_tay()
    assert [(x["loai"], x["trang_thai"], x["doan"], x["so_phep_thu"]) for x in rows] == [
        (HC.LOAI_TESTER, "DAT", "hieu_chuan", 0), (HC.LOAI_SO_SANH, "DAT", "hieu_chuan", 0)]
    assert r["tn_tester_id"] == rows[0]["id"] and r["tn_id"] == rows[1]["id"]
    # khong tieu phep thu, khong len bang "thi nghiem tot nhat", khong vao dem theo ma
    assert ST.dem_phep_thu() == 0 and ST.dem_phep_thu(doan="hieu_chuan") == 0
    tt = ST.tom_tat()
    assert tt["tong_phep_thu_kham_pha"] == 0 and not tt["thi_nghiem_tot_nhat"] and not tt["phep_thu_theo_ma"]


def test_lenh_gui_tester_dung_cua_so_model_von_va_input_ea(may):
    m = may()
    chay()
    l = m.lenh[0]
    assert l["doan"] == "kham_pha" and l["gt_id"] is None and l["ea_ten"].startswith("ea_LuoiDayDu")
    assert l["cua_so"]["tu"] == "2024.01.01" and l["cua_so"]["den"] == "2024.02.06" and l["cua_so"]["ngay"] == 37
    v = l["viec"]
    assert (v["tu"], v["den"], v["model"], v["von"], v["symbol"], v["khung"], v["don_bay"]) == (
        "2024.01.01", "2024.02.06", 0, 10000, "AUDCAD", "M15", 100)
    ea_in = G.tham_so_ea_tu_luoi(TS)
    assert ea_in[G.BANG_TEN["buoc"]] == 15 and ea_in[G.BANG_TEN["tp"]] == 6
    for k, x in ea_in.items():                       # moi input cua ThamSo di THANG vao lenh tester (khong bi doi / bo)
        assert float(v["input"][k]["gia_tri"]) == float(x), k


def test_lan_hai_cung_dau_vao_dung_cache_tester_khong_goi_lai_khong_ghi_them(may):
    m = may()
    r1 = chay()
    r2 = chay()
    assert m.lan == 1, "nua tester da nho: khong ton them 5-30 phut tester"
    assert r2["tester_tu_cache"] is True and r2["tn_tester_id"] == r1["tn_tester_id"]
    assert (r2["trang_thai"], r2["so_khoa"]) == (r1["trang_thai"], r1["so_khoa"])
    assert r2["tn_id"] == r1["tn_id"] and "tu_so_tay" in r2
    assert len(dong_so_tay()) == 2


def test_lam_lai_tester_ep_goi_lai_nhung_dong_so_sanh_cung_so_khong_ghi_trung(may):
    m = may()
    r1 = chay()
    r2 = chay(lam_lai_tester=True)
    assert m.lan == 2 and r2["tester_tu_cache"] is False
    assert r2["so_khoa"] == r1["so_khoa"] and r2["tn_id"] == r1["tn_id"] and "tu_so_tay" in r2
    assert [x["loai"] for x in dong_so_tay()] == [HC.LOAI_TESTER, HC.LOAI_SO_SANH, HC.LOAI_TESTER]
    r3 = chay()                                       # lan sau doc dong tester MOI NHAT
    assert r3["tester_tu_cache"] is True and m.lan == 2


@pytest.mark.parametrize("ts_that,o_dau", [
    ({"buoc": 15, "tp": 6, "tran_tang": 2, "che_do": "hai_chieu", "lot": 0.01}, "so lenh"),
    ({"buoc": 8, "tp": 3, "tran_tang": 5, "che_do": "hai_chieu", "lot": 0.01}, "so lenh"),
    ({"buoc": 30, "tp": 12, "tran_tang": 5, "che_do": "hai_chieu", "lot": 0.01}, "lai"),
    ({"buoc": 15, "tp": 6, "tran_tang": 5, "che_do": "hai_chieu", "lot": 0.01, "he_so_buoc": 1.5}, "lai"),
])
def test_tester_chay_tham_so_khac_voi_engine_la_LECH_va_ghi_AM(may, ts_that, o_dau):
    m = may(ts=ts_that)
    r = chay()
    assert r["trang_thai"] == "AM" and r["ket_luan"] == "LECH" and o_dau in r["ly_do"], r["ly_do"]
    assert not all(r["khop"].values()) and m.lan == 1
    assert [(x["loai"], x["trang_thai"], x["so_phep_thu"]) for x in dong_so_tay()] == [(HC.LOAI_TESTER, "DAT", 0), (HC.LOAI_SO_SANH, "AM", 0)]
    assert ST.dem_phep_thu() == 0


def test_lech_co_bang_theo_ky_va_ky_lech_dau_tien(may):
    may(ts={"buoc": 30, "tp": 12, "tran_tang": 5, "che_do": "hai_chieu", "lot": 0.01})
    r = chay()
    assert r["theo_ky"] and {"ky", "tester_pct", "engine_pct", "tester_dong", "engine_dong"} <= set(r["theo_ky"][0])
    d = r["ky_lech_dau_tien"]
    assert d and d["ky"] in {x["ky"] for x in r["theo_ky"]} and abs(d["tester_pct"] - d["engine_pct"]) > 0.25
    assert r["lech"]["lai_nam_pp"] < -1.0 and r["lech"]["lenh"] == r["engine"]["thong_ke"]["so_lenh_mo"] - r["tester"]["thong_ke"]["so_lenh_mo"]


@pytest.mark.parametrize("kw,ly_co", [
    (dict(xong=False), "tester khong ra ket qua"),
    (dict(log="MetaTester 5 started\r\nAUDCAD,M15: cannot generate history data\r\n"), "history"),
    (dict(khong_deal=True), "Deals"),
    (dict(ky="M15 (2023.12.01 - 2024.02.06)"), "khong nam trong"),
    (dict(ky="M15 (2024.01.01 - 2024.01.20)"), "khong nam trong"),
])
def test_ha_tang_hong_la_CHUA_DO_DUOC_khong_ghi_so_tay_va_lan_sau_chay_lai(may, monkeypatch, kw, ly_co):
    m = may(**kw)
    r = chay()
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r.get("ha_tang") is True and ly_co in r["ly_do"], r
    assert dong_so_tay() == [] and ST.dem_phep_thu() == 0
    m2 = may()                                        # may chay lai binh thuong -> tester KHONG bi cache ban hong
    r2 = chay()
    assert r2["trang_thai"] == "DAT" and m2.lan == 1 and r2["tester_tu_cache"] is False


def test_bao_cao_ngan_hon_mot_ngay_van_so_dung_cua_so_cua_bao_cao(may):
    may(ky="M15 (2024.01.01 - 2024.02.05)")           # tester cat 1 ngay cuoi thieu du lieu (>= 80% cua cua so, nam trong)
    r = chay()
    assert r["trang_thai"] in ("DAT", "AM")
    assert (r["cua_so"]["tu"], r["cua_so"]["den"]) == ("2024.01.01", "2024.02.05") and r["cua_so"]["ngay"] == 36
    assert any("bao cao tester chay 2024.01.01 .. 2024.02.05 (lenh xin 2024.01.01 .. 2024.02.06)" in x for x in r["nhan"])
    assert r["engine"]["den_bar"] < "2024-02-06"


def test_chat_luong_thap_la_canh_bao_khong_phai_loi_ha_tang(may):
    may(chat_luong=45)
    r = chay()
    assert r["trang_thai"] in ("DAT", "AM") and r["tester"]["chat_luong_pct"] == 45
    assert any("chat luong lich su cua tester chi 45%" in x for x in r["nhan"])


def test_canh_bao_cap_cheo_tien_he_so_quy_doi_va_ghep_fifo(may):
    may()
    r = chay()
    assert any("tien bao gia khac tien tai khoan" in x for x in r["nhan"])
    assert r["tester"]["ghep_fifo_pct"] > 50 and any("ghep vao/ra bang FIFO" in x for x in r["nhan"])
    # tester tra tien tai khoan (USD) con engine tinh tien bao gia (CAD): so TONG van khop vi engine da chia he so quy doi
    assert r["trang_thai"] == "DAT"


def test_von_quy_doi_do_nguoi_goi_dat_va_canh_bao_khi_lech_uoc_luong(may):
    may()
    r = chay(von_quy_doi=1.0)                         # sai: that su 1,3
    assert r["he_so_quy_doi"]["dung"] == 1.0 and r["he_so_quy_doi"]["nguon"] == "do nguoi goi dat"
    assert any("von_quy_doi dat 1.0000 khac uoc luong tu deal tester" in x for x in r["nhan"])
    r2 = chay(von_quy_doi=F_THAT)
    assert r2["he_so_quy_doi"]["dung"] == F_THAT
    assert not any("von_quy_doi dat" in x for x in r2["nhan"])


def test_chi_engine_chua_co_tester_tra_so_engine_va_khong_ghi_gi(may):
    m = may()
    r = chay(chi_engine=True)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r["engine"]["thong_ke"]["so_lenh_mo"] > 100 and "ha_tang" not in r
    assert any("he so quy doi dung" in x for x in r["nhan"]) and "chi in so engine" in r["ly_do"]
    assert m.lan == 0 and dong_so_tay() == []


def test_chi_engine_sau_khi_co_cache_so_sanh_day_du_khong_goi_tester(may):
    m = may()
    r1 = chay()
    r2 = chay(chi_engine=True)
    assert m.lan == 1 and r2["tester_tu_cache"] is True and (r2["trang_thai"], r2["so_khoa"]) == (r1["trang_thai"], r1["so_khoa"])


def test_tester_khong_ghi_doi_chieu_lenh_ra_ngoai_phep_thu_thuong(may, moi_truong):
    """Lenh hieu chuan mang cua so TAY: `nhan_ket_qua` (duong ghi ket qua nghien cuu) phai tu choi, khong the thanh phep thu."""
    m = may()
    chay()
    l = m.lenh[0]
    kh = E.ke_hoach("AUDCAD", "M15", "kham_pha", _cfg())
    # cua so nho hon cua so dong bang -> nhan_ket_qua phat hien lenh khong khop ke_hoach hien tai
    nho, ly = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-10", "2024-01-31", _cfg())
    assert ly is None and (nho["tu"], nho["den"]) != (kh["tu"], kh["den"])
    d = E.doc_ea(str(HC.EA_MAC_DINH))
    lo = E.lap_lenh(d, "AUDCAD", "M15", "kham_pha", G.tham_so_ea_tu_luoi(TS), None, _cfg(), None, cua_so_tay=nho)
    assert lo["trang_thai"] == "SAN_SANG"
    r = E.nhan_ket_qua(lo["lenh"], str(moi_truong["tmp"] / "bc_1.htm"))
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r.get("ha_tang") and "khong khop cua so dong bang" in r["ly_do"]
    assert ST.dem_phep_thu() == 0 and not [x for x in dong_so_tay() if x["loai"] not in (HC.LOAI_TESTER, HC.LOAI_SO_SANH)]


# ================================================================= C. DON VI: so sanh, chan doan, thong ke, he so quy doi
def _tk(**kw) -> dict:
    d = {"so_lenh_mo": 100, "so_lenh_dong": 100, "lenh_mo_cuoi": 0, "buy": 50, "sell": 50, "giu_lau_nhat_gio": 10.0,
         "giu_lau_nhat_mo": "2024-01-02 00:00:00", "tang_max": 5, "do_sau_tb": 2.0, "do_sau_p90": 4, "lai_chua_swap": 0.0,
         "swap": None, "theo_ky": {}}
    d.update(kw)
    return d


def _t(**kw) -> dict:
    tk = kw.pop("thong_ke", None) or _tk()
    d = {"lai_nam_pct": 10.0, "dd_pct_so_sanh": 20.0, "thong_ke": tk, "chat_luong_pct": 99.0, "model": 0, "he_so_quy_doi": None,
         "cua_so_so_sanh": {"tu": "2024.01.01", "den": "2024.12.31", "ngay": 366}, "von": 10000.0}
    d.update(kw)
    return d


def _e(**kw) -> dict:
    tk = kw.pop("thong_ke", None) or _tk()
    d = {"lai_nam_pct": 10.0, "dd_pct": 20.0, "chay": False, "thong_ke": tk,
         "kiem": {"khop": True, "lai_tong_khop": True, "gross_dong": 1.0, "lai_gop_engine": 1.0, "spread": 0.1, "phi_spread_engine": 0.1}}
    d.update(kw)
    return d


def test_doi_chieu_hai_ben_y_het_la_KHOP_va_khong_canh_bao():
    r = HC.doi_chieu(_t(), _e(), 1.0)
    assert r["ket_luan"] == "KHOP" and r["ly_do"].startswith("KHOP") and all(r["khop"].values()) and r["nhan"] == []
    assert r["lech"] == {"lai_nam_pp": 0.0, "dd_pp": 0.0, "lenh": 0, "lenh_pct": 0.0}
    assert r["dung_sai"]["lai"] == list(HC.DUNG_SAI["lai"]) and r["ky_lech_dau_tien"] is None


@pytest.mark.parametrize("tester,engine,khop", [
    (10.0, 10.99, True), (10.0, 11.05, False),            # |lech| <= max(10% so tester, 1,0 diem %/nam)
    (50.0, 54.9, True), (50.0, 55.2, False),
    (-3.0, -3.9, True), (-3.0, -4.1, False),
    (0.0, 0.9, True), (0.0, 1.1, False),
    (-0.45, 0.54, False),                                 # SAI DAU (am <-> duong) khi mot ben > 0,5%/nam: khong cho qua du trong nguong
    (-0.4, 0.4, True),                                    # sai dau nhung deu be hon 0,5%/nam: la nhieu
])
def test_doi_chieu_dung_sai_lai(tester, engine, khop):
    r = HC.doi_chieu(_t(lai_nam_pct=tester), _e(lai_nam_pct=engine), 1.0)
    assert r["khop"]["lai"] is khop and (r["ket_luan"] == "KHOP") is khop
    if not khop:
        assert r["ly_do"].startswith("LECH o lai")


@pytest.mark.parametrize("tester,engine,khop", [
    (40.0, 49.9, True), (40.0, 50.2, False), (1.0, 2.9, True), (1.0, 3.1, False), (80.0, 99.0, True), (80.0, 100.5, False),
])
def test_doi_chieu_dung_sai_maxdd(tester, engine, khop):
    r = HC.doi_chieu(_t(dd_pct_so_sanh=tester), _e(dd_pct=engine), 1.0)
    assert r["khop"]["dd"] is khop and r["lech"]["dd_pp"] == round(engine - tester, 3)


@pytest.mark.parametrize("tn,en,khop", [
    (100, 115, True), (100, 116, False), (100, 85, True), (100, 84, False), (10, 13, True), (10, 14, False), (10, 7, True), (10, 6, False),
])
def test_doi_chieu_dung_sai_so_lenh(tn, en, khop):
    r = HC.doi_chieu(_t(thong_ke=_tk(so_lenh_mo=tn)), _e(thong_ke=_tk(so_lenh_mo=en)), 1.0)
    assert r["khop"]["lenh"] is khop and r["lech"]["lenh"] == en - tn and r["lech"]["lenh_pct"] == round(100.0 * (en - tn) / tn, 2)


def test_doi_chieu_nhieu_cho_lech_ghi_het_va_chi_can_mot_cho_lech_la_LECH():
    r = HC.doi_chieu(_t(lai_nam_pct=10.0, dd_pct_so_sanh=20.0), _e(lai_nam_pct=30.0, dd_pct=45.0, thong_ke=_tk(so_lenh_mo=300)), 1.0)
    assert r["ket_luan"] == "LECH" and not any(r["khop"].values())
    assert r["ly_do"].startswith("LECH o lai") and "maxDD" in r["ly_do"] and "so lenh" in r["ly_do"]
    r = HC.doi_chieu(_t(), _e(dd_pct=45.0), 1.0)
    assert r["ket_luan"] == "LECH" and r["khop"] == {"lai": True, "dd": False, "lenh": True}


def test_engine_chay_tai_khoan_ma_tester_khong_thi_maxdd_la_LECH():
    r = HC.doi_chieu(_t(dd_pct_so_sanh=60.0), _e(dd_pct=60.0, chay=True), 1.0)
    assert r["khop"]["dd"] is False and any("CHAY tai khoan" in x for x in r["nhan"])
    r = HC.doi_chieu(_t(dd_pct_so_sanh=95.0), _e(dd_pct=96.0, chay=True), 1.0)        # tester cung sat stop-out: khop duoc
    assert r["khop"]["dd"] is True


def _ky(**kv) -> dict:
    return {k: {"lai_pct": v, "so_dong": 10, "tang_max": 3} for k, v in kv.items()}


def test_ky_lech_dau_tien_la_ky_som_nhat_lech_qua_nguong_va_ky_mot_ben_tinh_la_0():
    t = _tk(theo_ky=_ky(**{"2024-01": 1.0, "2024-02": 2.0, "2024-03": 1.0}))
    e = _tk(theo_ky=_ky(**{"2024-01": 1.1, "2024-02": 3.0}))
    bang, dau = HC._ky_lech_dau_tien(t, e)
    assert [x["ky"] for x in bang] == ["2024-01", "2024-02", "2024-03"]
    assert dau["ky"] == "2024-02" and (dau["tester_pct"], dau["engine_pct"]) == (2.0, 3.0)
    assert bang[2]["engine_pct"] == 0.0 and bang[2]["engine_dong"] == 0
    bang, dau = HC._ky_lech_dau_tien(_tk(theo_ky=_ky(a=0.10, b=5.0)), _tk(theo_ky=_ky(a=0.30, b=5.2)))   # 0,2 < 0,25 diem: nhieu
    assert dau is None


# ---- canh bao chan doan: moi canh bao co phep thu duong VA phep thu am
def _nhan(t=None, e=None, f=1.0) -> list[str]:
    return HC._canh_bao_chan_doan(t or _t(), e or _e(), f)


def test_canh_bao_nen_sach_khong_co_gi():
    assert _nhan() == []


def test_canh_bao_ro_ket_ben_tester():
    assert any("ro ket ben tester" in x for x in _nhan(_t(thong_ke=_tk(giu_lau_nhat_gio=500.0)), _e(thong_ke=_tk(giu_lau_nhat_gio=20.0))))
    assert not _nhan(_t(thong_ke=_tk(giu_lau_nhat_gio=100.0)), _e(thong_ke=_tk(giu_lau_nhat_gio=5.0)))        # < 120 gio
    assert not _nhan(_t(thong_ke=_tk(giu_lau_nhat_gio=500.0)), _e(thong_ke=_tk(giu_lau_nhat_gio=200.0)))      # engine cung giu lau


def test_canh_bao_ty_le_sell_lech():
    assert any("ty le SELL" in x for x in _nhan(_t(thong_ke=_tk(buy=10, sell=90)), _e(thong_ke=_tk(buy=50, sell=50))))
    assert not _nhan(_t(thong_ke=_tk(buy=30, sell=70)), _e(thong_ke=_tk(buy=50, sell=50)))                    # 20 diem < 25
    assert not _nhan(_t(thong_ke=_tk(buy=1, sell=9, so_lenh_mo=100)), _e(thong_ke=_tk(buy=5, sell=5)))       # < 20 lenh: mau nho


def test_canh_bao_do_sau_luoi_lon_nhat():
    assert any("do sau luoi lon nhat" in x for x in _nhan(_t(thong_ke=_tk(tang_max=11)), _e(thong_ke=_tk(tang_max=8))))
    assert not _nhan(_t(thong_ke=_tk(tang_max=10)), _e(thong_ke=_tk(tang_max=8)))


def test_canh_bao_chat_luong_lich_su():
    assert any("chat luong lich su cua tester chi 45%" in x for x in _nhan(_t(chat_luong_pct=45.0)))
    assert not _nhan(_t(chat_luong_pct=90.0)) and not _nhan(_t(chat_luong_pct=None))


def test_canh_bao_he_so_quy_doi_va_he_so_troi():
    assert any("he so quy doi 1.3000" in x for x in _nhan(f=1.3))
    assert not _nhan(f=1.01)
    hs = {"trung_vi": 1.3, "p25": 1.2, "p75": 1.4, "so_mau": 80, "cach": "tong"}                                 # troi 15%
    assert any("troi trong cua so" in x for x in _nhan(_t(he_so_quy_doi=hs)))
    assert not _nhan(_t(he_so_quy_doi=dict(hs, p25=1.29, p75=1.31)))
    assert not _nhan(_t(he_so_quy_doi=dict(hs, p25=None, p75=None)))                                              # ghep FIFO: p25/p75 khong tin


def test_canh_bao_do_sau_theo_thoi_gian_bang_chung_ro_ket_khong_phu_thuoc_cach_ghep():
    t = _t(thong_ke=_tk(do_sau_tb=4.0, do_sau_p90=10))
    e = _e(thong_ke=_tk(do_sau_tb=1.5, do_sau_p90=5))
    assert any("do sau cao hon nhieu theo THOI GIAN" in x for x in _nhan(t, e))
    assert not _nhan(_t(thong_ke=_tk(do_sau_tb=2.0, do_sau_p90=10)), e)                                           # tb chua >= 1,5 lan
    assert not _nhan(_t(thong_ke=_tk(do_sau_tb=4.0, do_sau_p90=7)), e)                                            # p90 chua cao hon >= 3


def test_canh_bao_engine_chay_mau_nho_va_cong_tung_lenh_khong_khop():
    assert any("CHAY tai khoan" in x for x in _nhan(e=_e(chay=True)))
    assert any("chi 12 lenh o tester" in x for x in _nhan(_t(thong_ke=_tk(so_lenh_mo=12))))
    assert not any("chi" in x and "lenh o tester" in x for x in _nhan(_t(thong_ke=_tk(so_lenh_mo=30))))
    kiem = {"khop": False, "gross_dong": 5.0, "lai_gop_engine": 6.0, "spread": 1.0, "phi_spread_engine": 1.0}
    assert any("KHONG khop tong" in x for x in _nhan(e=_e(kiem=kiem)))
    assert any("KHONG khop tong" in x for x in _nhan(e=_e(kiem=dict(kiem, khop=True, lai_tong_khop=False))))


def test_canh_bao_swap_tinh_theo_phan_tram_nam_khong_theo_tien():
    """Swap so bang %/nam cua von (khong phai so tuyet doi): 1 nam, von 10000: -200 (= -2%/nam) vs -50 (= -0,5%/nam) la lech."""
    t = _t(thong_ke=_tk(swap=-200.0), cua_so_so_sanh={"tu": "2024.01.01", "den": "2024.12.31", "ngay": 366})
    assert any("swap: tester -2.00%/nam engine -0.50%/nam" in x for x in _nhan(t, _e(thong_ke=_tk(swap=-50.0))))
    assert not _nhan(t, _e(thong_ke=_tk(swap=-150.0)))                                    # chenh 0,5 diem < 1,0
    ngan = _t(thong_ke=_tk(swap=-5.0), cua_so_so_sanh={"tu": "2024.01.01", "den": "2024.02.06", "ngay": 37})
    assert not _nhan(ngan, _e(thong_ke=_tk(swap=-1.0)))                                   # 37 ngay: -0,5%/nam vs -0,1%/nam: nhieu
    assert not _nhan(_t(thong_ke=_tk(swap=None)), _e(thong_ke=_tk(swap=-50.0)))           # tester khong ghi swap: khong ket luan


# ---- thong_ke_lenh: ba lenh tinh tay
def _bang3() -> pd.DataFrame:
    return pd.DataFrame({
        "mo": pd.to_datetime(["2024-01-01 00:00", "2024-01-01 06:00", "2024-01-03 00:00"]),
        "dong": pd.to_datetime(["2024-01-02 00:00", "2024-01-04 00:00", None]),
        "chieu": [1, -1, 1], "lot": [0.01, 0.01, 0.02], "gia_mo": [1.0, 1.0, 1.0], "gia_dong": [1.0, 1.0, np.nan],
        "lai": [10.0, -4.0, 2.5], "swap": [-0.5, -0.25, np.nan], "ly": ["tp", "tp", "het_gio"]})


def test_thong_ke_lenh_ba_lenh_tinh_tay():
    k = HC.thong_ke_lenh(_bang3(), pd.Timestamp("2024-01-05"), 1000.0, True)
    assert (k["so_lenh_mo"], k["so_lenh_dong"], k["lenh_mo_cuoi"], k["buy"], k["sell"]) == (3, 2, 1, 2, 1)
    assert k["giu_lau_nhat_gio"] == 66.0 and k["giu_lau_nhat_mo"] == "2024-01-01 06:00:00"      # lenh 2: 1/1 06:00 -> 1/4 00:00
    assert k["lai_chua_swap"] == 8.5 and k["swap"] == -0.75                                    # NaN swap tinh 0
    assert k["tang_max"] == 2
    # do sau theo thoi gian: 1 lenh x 6h, 2 x 18h, 1 x 24h, 2 x 24h, 1 x 24h (het 96h) -> tb 138/96, p90 = 2
    assert k["do_sau_tb"] == pytest.approx(138.0 / 96.0, abs=1e-3) and k["do_sau_p90"] == 2
    assert list(k["theo_ky"]) == ["2024-01"] and k["theo_ky"]["2024-01"] == {"lai_pct": 0.85, "so_dong": 3, "tang_max": 2}
    q = HC.thong_ke_lenh(_bang3(), pd.Timestamp("2024-01-05"), 1000.0, False)
    assert list(q["theo_ky"]) == ["2024Q1"]


def test_thong_ke_lenh_rong_va_swap_khong_biet():
    r = HC.thong_ke_lenh(pd.DataFrame(columns=["mo", "dong", "chieu", "lot", "lai", "swap"]), pd.Timestamp("2024-01-05"), 1000.0, True)
    assert r["so_lenh_mo"] == 0 and r["theo_ky"] == {} and r["swap"] is None and r["tang_max"] == 0
    b = _bang3()
    b["swap"] = np.nan
    assert HC.thong_ke_lenh(b, pd.Timestamp("2024-01-05"), 1000.0, True)["swap"] is None       # engine khong biet swap tung lenh


def test_thong_ke_lenh_hai_lenh_cung_giay_dong_truoc_mo():
    """Lenh dong dung luc lenh khac mo: khong tinh la dang mo CA HAI (do sau khong bi thoi phong)."""
    b = pd.DataFrame({"mo": pd.to_datetime(["2024-01-01 00:00", "2024-01-01 12:00"]),
                      "dong": pd.to_datetime(["2024-01-01 12:00", "2024-01-02 00:00"]), "chieu": [1, 1], "lot": [0.01, 0.01],
                      "lai": [1.0, 1.0], "swap": [0.0, 0.0]})
    assert HC.thong_ke_lenh(b, pd.Timestamp("2024-01-02"), 1000.0, True)["tang_max"] == 1


# ---- uoc he so quy doi: tong va tung lenh
def _gia_lap(n: int, f: float, seed: int = 3, hop: float = HOP_FX) -> pd.DataFrame:
    """n lenh da dong, loi = chieu*(gd-gm)*lot*hop/f lam tron cent; lenh co ky vong duong (tong loi du lon de uoc 'tong' tin duoc)."""
    r = np.random.default_rng(seed)
    gm = 0.9 + r.normal(0, 0.002, n)
    ch = r.choice([1, -1], n)
    gd = gm + ch * r.normal(0.0004, 0.0012, n)
    lot = r.choice([0.01, 0.02, 0.04], n)
    loi = np.round(ch * (gd - gm) * lot * hop / f, 2)
    t0 = pd.Timestamp("2024-01-01")
    return pd.DataFrame({"mo": t0 + pd.to_timedelta(np.arange(n), unit="h"), "dong": t0 + pd.to_timedelta(np.arange(n) + 1, unit="h"),
                         "chieu": ch, "lot": lot, "gia_mo": gm, "gia_dong": gd, "loi": loi})


def test_uoc_he_so_tim_lai_dap_an_da_cai():
    g = _gia_lap(200, 1.3)
    r = HC.uoc_he_so_quy_doi(g, HOP_FX)
    assert r["cach"] == "tong" and r["so_mau"] == 200 and r["trung_vi"] == pytest.approx(1.3, rel=0.01)
    assert r["p25"] is not None and r["p25"] < r["trung_vi"] < r["p75"]
    assert r["p75"] - r["p25"] < 0.05 * 1.3                                  # moi lenh cung mot he so: p25..p75 hep


def test_uoc_he_so_khong_phu_thuoc_cach_ghep_vao_ra():
    """Hoan vi `loi` giua cac lenh (ghep nham) khong doi tong -> cach 'tong' van dung; cach tung lenh bi tat khi FIFO nhieu."""
    g = _gia_lap(200, 1.3)
    xao = g.copy()
    xao["loi"] = np.random.default_rng(9).permutation(g["loi"].to_numpy())
    r = HC.uoc_he_so_quy_doi(xao, HOP_FX, ghep_fifo_pct=0.9)
    assert r["cach"] == "tong" and r["trung_vi"] == pytest.approx(1.3, rel=0.01) and r["p25"] is None and r["p75"] is None


def test_uoc_he_so_it_mau_hoac_sai_dau_la_none_khong_doan():
    assert HC.uoc_he_so_quy_doi(_gia_lap(15, 1.3), HOP_FX) is None            # < 20 lenh
    sai = _gia_lap(200, 1.3)
    sai["loi"] = -sai["loi"]                                                     # tien that nguoc dau tien tinh: khong doan he so am
    assert HC.uoc_he_so_quy_doi(sai, HOP_FX) is None
    assert HC.uoc_he_so_quy_doi(pd.DataFrame(columns=["dong", "gia_dong", "loi", "chieu", "gia_mo", "lot"]), HOP_FX) is None
    assert HC.uoc_he_so_quy_doi(None, HOP_FX) is None


def test_uoc_he_so_bo_qua_lenh_chua_dong():
    g = _gia_lap(60, 1.3)
    g.loc[:9, "dong"] = pd.NaT
    g.loc[:9, "gia_dong"] = np.nan
    g.loc[:9, "loi"] = np.nan
    r = HC.uoc_he_so_quy_doi(g, HOP_FX)
    assert r["so_mau"] == 50 and r["trung_vi"] == pytest.approx(1.3, rel=0.02)


def test_uoc_he_so_tong_loi_qua_nho_thi_roi_ve_cach_tung_lenh():
    g = _gia_lap(200, 1.3)
    g.loc[g.index[-1], "loi"] += -g["loi"].sum()                                # tong loi ~ 0: cach 'tong' khong tin
    r = HC.uoc_he_so_quy_doi(g, HOP_FX)
    assert r is not None and r["cach"] == "tung_lenh" and r["trung_vi"] == pytest.approx(1.3, rel=0.02)
    assert HC.uoc_he_so_quy_doi(g, HOP_FX, ghep_fifo_pct=0.9) is None


# ---- ha tang + DD cua bao cao
def test_hong_ha_tang_tung_ly_do():
    cs = {"tu": "2024.01.01", "den": "2024.02.06", "ngay": 37}
    ok = {"doc_duoc": True, "ticks": 100, "bars": 100, "tu": "2024.01.01", "den": "2024.02.06"}
    assert HC._hong_ha_tang(ok, cs, "") is None
    assert "TESTER KHONG CHAY DUOC" in HC._hong_ha_tang(ok, cs, "MetaTester 5 started\r\nnot enough memory\r\n")
    assert "khong doc duoc" in HC._hong_ha_tang(dict(ok, doc_duoc=False, loi="hong"), cs, "")
    assert "0 tick/0 bar" in HC._hong_ha_tang(dict(ok, ticks=0), cs, "")
    assert "khong nam trong" in HC._hong_ha_tang(dict(ok, tu="2023.12.15"), cs, "")
    assert HC._hong_ha_tang(dict(ok, tu=None, den=None), cs, "") is None        # bao cao khong ghi ngay: bo qua kiem cua so


def test_dd_tester_uu_tien_von_tuong_doi_roi_von_toi_da_roi_cong():
    bc = {"dd_von_tuong_doi": {"pct": 12.0}, "dd_von_toi_da": {"pct": 15.0}, "dd_so_du_toi_da": {"pct": 9.0}, "dd_pct": 20.0}
    assert HC._dd_tester(bc)["so_sanh_pct"] == 12.0
    assert HC._dd_tester(dict(bc, dd_von_tuong_doi=None))["so_sanh_pct"] == 15.0
    assert HC._dd_tester(dict(bc, dd_von_tuong_doi=None, dd_von_toi_da=None))["so_sanh_pct"] == 20.0
    d = HC._dd_tester({"dd_pct": None})
    assert d["so_sanh_pct"] is None and d["so_du_pct"] is None


# ---- engine: cong tung lenh phai khop tong, cho ca bon kieu luoi (bao ve khi luoi.py doi cach tinh phi)
@pytest.mark.parametrize("mo_hinh", LU.MO_HINH_BAR)
@pytest.mark.parametrize("ten", sorted(CAU_HINH))
def test_engine_tach_theo_lenh_khop_tong_cho_moi_kieu_luoi(ten, mo_hinh):
    """Hai mo hinh bar co CACH TINH SPREAD KHAC NHAU o lenh tia (`cuc_tri` tru hai lan, `duong_di` mot lan): tach theo lenh phai khop
    tong CA HAI - truoc 08/10/2026 chi co mot, nen doi mo hinh mac dinh la tn5 (co tia) mat khop."""
    cs = {"tu": "2024.01.01", "den": "2024.02.06", "ngay": 37}
    ts = dataclasses.replace(CAU_HINH[ten], khop_bar=mo_hinh)
    e = HC.nua_engine("AUDCAD", "M15", cs, ts, VON, F_THAT)
    assert "loi" not in e, e
    assert e["kiem"]["khop"] and e["kiem"]["lai_tong_khop"], (ten, e["kiem"])
    k = e["thong_ke"]
    assert k["so_lenh_mo"] > 20 and k["so_lenh_dong"] + k["lenh_mo_cuoi"] == k["so_lenh_mo"]
    so_nam = 37 / 365.25
    assert e["lai_nam_pct"] == pytest.approx(e["lai_tong"] / VON / so_nam * 100.0)
    assert e["lai_tong"] == pytest.approx(k["lai_chua_swap"] + k["swap"])           # lai gom ca lai/lo treo cuoi cua so
    assert e["lai_tong"] - e["lai_chot_nam_pct"] / 100.0 * VON * so_nam == pytest.approx(e["lai_treo"], abs=1e-6)
    assert e["qc"]["von_quy_doi"] == F_THAT and e["so_bar"] > 3000


@pytest.mark.parametrize("mo_hinh", LU.MO_HINH_BAR)
def test_tach_spread_tia_phai_dung_mo_hinh_va_bi_bat_khi_sai(mo_hinh):
    """Cach tach spread o lenh tia theo mo hinh: dung mo hinh -> khop; DOI mo hinh (cuc_tri <-> duong_di) tren cung mot lan chay co tia
    -> `kiem['khop']` phai False. Neu khong, phep so cong tung lenh vo nghia voi lenh tia (khong bat duoc tach sai)."""
    ts = dataclasses.replace(CAU_HINH["tn5"], khop_bar=mo_hinh)
    dl = LU.chuan_bi(bars_that(), LU.QC_AUDCAD)
    kq = LU.chay_mang(dl, ts, 10000.0, ghi_lenh=True)
    assert int((kq.lenh["ly_do"] == "tia").sum()) >= 10, "can nhieu lenh tia de phep thu co nghia"
    _b, dung = HC.bang_lenh_engine(kq, dl, 1.0, mo_hinh)
    assert dung["khop"], dung
    khac = [m for m in LU.MO_HINH_BAR if m != mo_hinh][0]
    _b, sai = HC.bang_lenh_engine(kq, dl, 1.0, khac)
    assert not sai["khop"], sai
    with pytest.raises(ValueError, match="mo_hinh"):
        HC.bang_lenh_engine(kq, dl, 1.0, "tick")


def test_engine_cua_so_ngoai_du_lieu_la_loi_ha_tang_khong_phai_lai_bang_0():
    ra = HC.nua_engine("AUDCAD", "M15", {"tu": "2025.01.01", "den": "2025.02.01", "ngay": 32}, TS, VON, F_THAT)
    assert list(ra) == ["loi"] and "du lieu lab chi co 0 bar" in ra["loi"]
    ra = HC.nua_engine("AUDCAD", "M15", {"tu": "2024.01.20", "den": "2024.03.01", "ngay": 42}, TS, VON, F_THAT)
    assert "loi" in ra and "khong phu cua so" in ra["loi"]                         # kham_pha dung 2024.02.06: thieu hon 7 ngay duoi
    assert "loi" in HC.nua_engine("US500", "M15", {"tu": "2024.01.10", "den": "2024.01.31", "ngay": 22}, TS, VON, F_THAT)


# ================================================================= D. lap_lenh(cua_so_tay) + cong cu nc + ve sinh
def _ea() -> dict:
    return E.doc_ea(str(HC.EA_MAC_DINH))


def _lap(doan: str = "kham_pha", **kw) -> dict:
    return E.lap_lenh(_ea(), "AUDCAD", "M15", doan, G.tham_so_ea_tu_luoi(TS), None, _cfg(), None, **kw)


def test_lap_lenh_cua_so_tay_dung_cua_so_va_van_tay_doi_theo_cua_so():
    a, _ = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-10", "2024-01-31", _cfg())
    b, _ = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-10", "2024-02-01", _cfg())
    la, lb, ld = _lap(cua_so_tay=a), _lap(cua_so_tay=b), _lap()
    assert la["trang_thai"] == lb["trang_thai"] == ld["trang_thai"] == "SAN_SANG"
    assert la["lenh"]["cua_so"] == a and (la["lenh"]["viec"]["tu"], la["lenh"]["viec"]["den"]) == ("2024.01.10", "2024.01.31")
    assert len({la["lenh"]["van_tay"], lb["lenh"]["van_tay"], ld["lenh"]["van_tay"]}) == 3
    assert (ld["lenh"]["viec"]["tu"], ld["lenh"]["viec"]["den"]) == ("2024.01.01", "2024.02.06")      # khong tay: cua so dong bang


@pytest.mark.parametrize("doan", ["xac_nhan", "niem_phong"])
def test_lap_lenh_cua_so_tay_bi_tu_choi_voi_doan_khong_phai_kham_pha(doan):
    cs, _ = HC.chuan_cua_so("AUDCAD", "M15", "2024-01-10", "2024-01-31", _cfg())
    r = _lap(doan, cua_so_tay=cs)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "cua so tay chi cho doan kham_pha" in r["ly_do"] and "lenh" not in r
    assert ST.nhieu("SELECT id FROM niem_phong") == []


def test_lap_lenh_cua_so_tay_khong_doc_cache_ket_qua_nghien_cuu():
    """Phep thu thuong cung van tay -> tra ket qua cu (khong chay lai); hieu chuan co cua so tay PHAI chay that, va khong lam mat cache cua phep thu."""
    kh = E.ke_hoach("AUDCAD", "M15", "kham_pha", _cfg())
    cfg, d = _cfg(), _ea()
    vt = E.van_tay_chay(d["sha"], "AUDCAD", "M15", G.tham_so_ea_tu_luoi(TS), "kham_pha", kh, cfg["model"], cfg["von"])
    ST.ghi_thi_nghiem("ea_tho_chay", {"x": 1}, {"trang_thai": "DAT", "lai": 1.0}, "DAT", vt, "AUDCAD", "M15", "kham_pha",
                      gt_id=None, so_phep_thu=1, tom_tat="dong mau")
    r = _lap()
    assert r.get("tu_so_tay") and "lenh" not in r                                 # duong thuong: tra lai tu so tay
    r2 = _lap(cua_so_tay=dict(kh))
    assert r2["trang_thai"] == "SAN_SANG" and r2["lenh"]["van_tay"] == vt           # cung cua so: van phai chay that
    assert len(ST.nhieu("SELECT id FROM thi_nghiem")) == 1                          # chi con dong mau: lap lenh khong ghi gi them


# ---- cong cu nc: dang ky, goi, loi dau vao, danh sach trang cua may nha
def test_cong_cu_nc_hieu_chuan_luoi_dang_ky_voi_schema_dung():
    c = CC.THEO_TEN["hieu_chuan_luoi"]
    assert c["schema"]["required"] == ["ma", "khung", "tu", "den"]
    assert {"ma", "khung", "tu", "den", "tham_so", "model", "von", "ea", "chi_engine", "von_quy_doi", "han_giay",
            "lam_lai_tester"} == set(c["schema"]["properties"])
    assert c["mo_ta"].isascii() and "KHOP" in c["mo_ta"] and "hieu_chuan" in c["mo_ta"]
    assert len({x["ten"] for x in CC.CONG_CU}) == len(CC.CONG_CU)                     # khong trung ten


def test_cong_cu_nc_goi_chay_dung_nhu_goi_thang_va_dung_so_tay(may):
    m = may()
    r = CC.goi("hieu_chuan_luoi", {"ma": "AUDCAD", "khung": "M15", "tu": CUA_SO[0], "den": CUA_SO[1], "tham_so": dict(TS_DICT),
                                    "model": 0, "von": 10000})
    assert r["trang_thai"] == "DAT" and r["ket_luan"] == "KHOP" and m.lan == 1 and "_giay" in r
    assert [x["loai"] for x in dong_so_tay()] == [HC.LOAI_TESTER, HC.LOAI_SO_SANH] and ST.dem_phep_thu() == 0


def test_cong_cu_nc_goi_voi_vong_id_gan_dong_so_tay_vao_vong(may):
    may()
    r = CC.goi("hieu_chuan_luoi", {"ma": "AUDCAD", "khung": "M15", "tu": CUA_SO[0], "den": CUA_SO[1], "tham_so": dict(TS_DICT),
                                    "model": 0, "von": 10000}, vong_id=77)
    assert r["trang_thai"] == "DAT"
    assert {x["vong_id"] for x in ST.nhieu("SELECT vong_id FROM thi_nghiem")} == {77}


def test_cong_cu_nc_loi_dau_vao_tra_loi_khong_nem_ngoai_le(may):
    m = may()
    base = {"ma": "AUDCAD", "khung": "M15", "tu": CUA_SO[0], "den": CUA_SO[1]}
    assert "thieu tham so bat buoc" in CC.goi("hieu_chuan_luoi", {"ma": "AUDCAD"})["loi"]
    assert "khong co trong schema" in CC.goi("hieu_chuan_luoi", dict(base, so_lan_thu=5))["loi"]
    r = CC.goi("hieu_chuan_luoi", dict(base, tu="2023-01-01"))
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "NGOAI doan kham_pha" in r["ly_do"]
    r = CC.goi("hieu_chuan_luoi", dict(base, tham_so={"buoc": 15, "dung_lo_tong": 3}))
    assert r["trang_thai"] == "CHUA_DO_DUOC"
    assert m.lan == 0 and dong_so_tay() == []


def test_cli_nc_cc_in_json_va_may_nha_duoc_xep_hang(may, capsys):
    may()
    dv = {"ma": "AUDCAD", "khung": "M15", "tu": CUA_SO[0], "den": CUA_SO[1], "tham_so": dict(TS_DICT), "model": 0, "von": 10000}
    tho = json.dumps(dv)
    assert CT.kiem_lenh(["{py}", "b.py", "nc", "cc", "hieu_chuan_luoi", tho]) is None, "may nha phai chay duoc don nay"
    assert CT.kiem_lenh(["{py}", "b.py", "nc", "cc", "khong_co_cong_cu_nay", tho]) is not None
    assert CC.main(["hieu_chuan_luoi", tho]) == 0
    ra = json.loads(capsys.readouterr().out)
    assert ra["trang_thai"] == "DAT" and ra["ket_luan"] == "KHOP"
    assert CC.main(["hieu_chuan_luoi", "{khong phai json"]) == 2


def test_hieu_chuan_luoi_nam_trong_tang_nha_nghien_cuu():
    assert any("hieu_chuan_luoi" in mods for _mo_ta, mods in KT.LOP.values())


# ---- ve sinh file moi: ASCII, khong ten mo hinh, khong file nhi phan / khoa
def _ten_cam() -> re.Pattern:
    return re.compile("|".join(("cla" + "ude", "son" + "net", "op" + "us", "hai" + "ku", "fa" + "ble")), re.I)


def test_file_moi_chi_co_ascii_va_khong_ten_mo_hinh():
    for p in (Path(HC.__file__), Path(__file__)):
        van = p.read_text(encoding="utf-8")
        assert van.isascii(), (p.name, [c for c in van if ord(c) > 127][:5])
        m = _ten_cam().search(van.replace("CLAUDE.md", ""))                          # ten FILE huong dan cua du an khong phai ten mo hinh
        assert m is None, (p.name, m and van[max(0, m.start() - 30): m.end() + 30])
    mo_ta = CC.THEO_TEN["hieu_chuan_luoi"]["mo_ta"]
    assert mo_ta.isascii() and _ten_cam().search(mo_ta) is None


def test_bang_lenh_tester_luu_ra_thu_muc_hieu_chuan_khong_vao_git_khong_co_khoa(may, moi_truong):
    may()
    r = chay()
    p = Path(r["tester"]["bang_lenh"])
    assert p.exists() and p.name.endswith("_lenh.csv.gz") and p.parent == moi_truong["tmp"] / "hc"
    b = pd.read_csv(p)
    assert {"mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "lai", "swap", "ly"} <= set(b.columns) and len(b) == r["tester"]["thong_ke"]["so_lenh_mo"]


def test_tick_tu_cua_may_nha_khong_cat_cua_so_hieu_chuan(may, moi_truong, monkeypatch):
    """May nha dat `tick_tu` (chi co tick that tu 2024): phep thu thuong bi cat, nhung Model 0 sinh tick tu M1 nen hieu chuan khong bi cat."""
    cfg = moi_truong["tmp"] / "ea_tho_tick.json"
    cfg.write_text(json.dumps({"tu_nap": False, "tick_tu": "2024-02-01"}), encoding="utf-8")
    monkeypatch.setenv("EA_THO_CFG", str(cfg))
    assert "tu" not in E.ke_hoach("AUDCAD", "M15", "kham_pha", E.cau_hinh())            # phep thu thuong: con < 30 ngay -> khong chay
    m = may()
    r = chay()
    assert r["trang_thai"] == "DAT" and m.lenh[0]["viec"]["tu"] == "2024.01.01" and m.lenh[0]["viec"]["den"] == "2024.02.06"
