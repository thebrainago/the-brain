# -*- coding: utf-8 -*-
"""ea_LuoiDayDu.mq5 - chay CHINH van ban .mq5 tren SAN GIA (`nhan/ea_gia_lap`), khong phai ban port tay.

Sau lop kiem, tu re den dat. Khong lop nao thay duoc tester MT5 that (cu phap rieng cua MQL5, tick that, spread doi, swap -
`tai_lieu/LAN_EA_THO.md`, 5 diem chua hieu chuan): cai kiem duoc o day la LOGIC file .mq5 co dung y khai bao `luoi.ThamSo` khong.
  1. Bang ten ThamSo <-> input, tham so, bo property (khong can trinh bien dich).
  2. Cu phap: bien dich nghiem (-Wall, input la const), loi tro dung dong .mq5.
  3. KICH BAN TAY: duong gia dung bang tay, so tien tinh tay TRUOC roi moi so voi san gia (khong chep dau ra cua san gia).
  3b. KICH BAN TAY cho BON TINH NANG MOI (08/10/2026: cat lo ca ro theo pip / theo tien, thoat theo gio, nghi, loc gio vao lenh): duong gia dung theo
     TUNG GIAY, tick mo / dong tinh tay (cung so voi `test_luoi_thoat_gio.py`), gom ranh gioi dung giay (>= / >, [tu, den), qua nua dem, 4,1 gio lam tron nua len).
  4. DOI CHIEU NGAU NHIEN voi `luoi.chay` tren CUNG duong gia tick: 12 cau hinh x nhieu duong gia, khop TUNG LENH (chieu, lot,
     gia mo, tick mo / dong) va LAI sau hai khoan da biet (`KetQuaDoiChieu`) - phan lech con lai phai bang 0.
  4b. Nhu 4 cho 8 bo tinh nang moi x 12 cau hinh = 96 o (4 duong gia, gio tick GIAY NGUYEN): them (a) so ro cat lo / thoat gio EA TU DEM = so engine ghi,
     (b) bat bien doc lap tren nhat ky: moi ro mo trong cua so gio, khoang nghi sau cat / thoat >= nghi_gio, ro thoat gio song >= thoat_gio, (c) tinh nang
     CO xay ra (khong phai o rong).
  5. DOT BIEN: sua ma EA co chu dich -> bo so sanh PHAI bao lech (bo so sanh co rang, khong gat dau cho moi thu). 5b: nhu vay cho ma cat lo / thoat gio / nghi / cua so gio /
     kiem dau vao - 40 mau, MOI mau bi mot bai kich ban tay (muc 3b) bat (ranh gioi dung giay ma duong gia ngau nhien it khi cham toi); them mot test do tren 96 duong gia
     ngau nhien rang hai cho `ChamCat` sau tia cap (ma phong ve, 3 dot bien tuong duong) khong bao gio chay.
  6. Do khoang cach mo hinh bar OHLC (engine) <-> tick (EA) - task #48: `cuc_tri` (cu) lac quan +15% .. +55% so voi EA chay tren tick cua CHINH cac bar do;
     `duong_di` (mac dinh) khop < 6% theo nen va KHONG lac quan voi bat ky thu tu cao / thap nao (than trong toi -39% o cau hinh cho lui). Cham, `cham`;
     bang day du: `python test_ea_luoi_day_du.py --bang --paso 1e-6` (`reports/lech_engine_EURCAD.md` muc 2).
"""
from __future__ import annotations

import collections
import dataclasses
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import ea_gia_lap as G
from nhan import ea_tho as EA
from nhan import luoi as L

EA_MQ5 = Path(__file__).with_name("ea_LuoiDayDu.mq5")
EA_CU = Path(__file__).with_name("ea_LuoiThamChieu.mq5")
HOP = 100000.0
can_cxx = pytest.mark.skipif(G.trinh_bien_dich() is None, reason="khong co g++ / clang++ (hoac EA_GIA_LAP_CXX)")

#: 12 cau hinh phu MOI duong di cua EA: lot phang / nhan / cong, buoc co dinh / gian / thu, ro mot chieu / hai chieu, tia lenh,
#: cho lui, chot tien, va cac to hop (tia + chot tien, tia + cho lui, chot tien + cho lui, ca ba). Nguong chot tien KHONG nam tren
#: luoi tien cua lot (xxx003) de hai ben khong tung dong xu o mut nguong: ham tick-bar cua engine va EA lam tron khac nhau o day.
CAU_HINH = {
    "mua_phang": L.ThamSo(buoc=15, tp=6, tran_tang=5, che_do="mua", lot=0.01),
    "ban_cong": L.ThamSo(buoc=18, tp=8, tran_tang=6, che_do="ban", lot=0.04, kieu_lot="cong", he_so_lot=0.25),
    "hai_nhan_buoc": L.ThamSo(buoc=18, tp=7, tran_tang=5, che_do="hai_chieu", lot=0.01, kieu_lot="nhan", he_so_lot=2.0,
                              he_so_buoc=1.5),
    "tn5": L.ThamSo(buoc=21, tp=9, tran_tang=9, che_do="hai_chieu", lot=0.04, kieu_lot="cong", he_so_lot=0.25, he_so_buoc=1.2,
                    tia_lenh=True, bien_cap=5),
    "cho_lui": L.ThamSo(buoc=16, tp=7, tran_tang=6, che_do="hai_chieu", lot=0.02, cho_lui=6),
    "chot_tien": L.ThamSo(buoc=16, tp=7, tran_tang=6, che_do="hai_chieu", lot=0.04, kieu_lot="cong", he_so_lot=0.25,
                          chot_tien=3),
    "chot_tien_cho_lui": L.ThamSo(buoc=14, tp=7, tran_tang=6, che_do="hai_chieu", lot=0.02, chot_tien=2.0003, cho_lui=4),
    "chot_tien_tia": L.ThamSo(buoc=14, tp=7, tran_tang=7, che_do="hai_chieu", lot=0.04, kieu_lot="cong", he_so_lot=0.25,
                              he_so_buoc=1.2, tia_lenh=True, bien_cap=4, chot_tien=1.0003),
    "chot_tien_tia_cho_lui": L.ThamSo(buoc=14, tp=7, tran_tang=7, che_do="hai_chieu", lot=0.04, kieu_lot="cong",
                                      he_so_lot=0.25, he_so_buoc=1.2, tia_lenh=True, bien_cap=4, chot_tien=1.0003, cho_lui=3),
    "tia_cho_lui": L.ThamSo(buoc=20, tp=9, tran_tang=7, che_do="hai_chieu", lot=0.02, kieu_lot="cong", he_so_lot=0.5,
                            tia_lenh=True, bien_cap=3, cho_lui=5),
    "buoc_co": L.ThamSo(buoc=10, tp=5, tran_tang=8, che_do="hai_chieu", lot=0.01, he_so_buoc=2.0, buoc_tran=40),
    "buoc_thu": L.ThamSo(buoc=24, tp=8, tran_tang=6, che_do="mua", lot=0.01, he_so_buoc=0.8),
}
#: Sai so cho phep o TICK (mo / dong) giua engine va EA. Engine mo / dong o MUC LUOI chinh xac (co the le, giua hai tick); EA o tick dau
#: tien vuot muc do. Muc le xuat hien khi buoc gian (21 x 1,2^k pip) hoac TP la trung binh cua cac tang khong deu: ro moi / tang ke tiep
#: tinh tu gia le do co the lech MOT tick. Cau hinh con lai (luoi deu, lot deu) khop DUNG tung tick (do 04/10/2026, 80 duong gia, 0 lech).
TOL_TICK = {ten: 0 for ten in ("mua_phang", "ban_cong", "tn5", "cho_lui", "chot_tien", "chot_tien_cho_lui", "tia_cho_lui")}
CO_TIA = {"tn5", "chot_tien_tia", "chot_tien_tia_cho_lui", "tia_cho_lui"}
CO_CHOT_TIEN = {"chot_tien", "chot_tien_cho_lui", "chot_tien_tia", "chot_tien_tia_cho_lui"}
THU_TU = ("theo_nen", "thap_truoc", "cao_truoc", "xen_ke")


def bars(n: int = 150, seed: int = 1, rng_max: int = 8, spread_pts: int = 20) -> pd.DataFrame:
    """Bar M15 gia lap tren luoi 1e-5, ve gia quanh 0,90 (rieng test: khong lay du lieu that); bien do bar toi da `rng_max` pip."""
    r = np.random.RandomState(seed)
    o, h, l, c = [], [], [], []
    p = 90000
    for _ in range(n):
        o_ = p
        c_ = o_ + int(round(r.normal(-0.02 * (p - 90000), 25)))
        hi = max(o_, c_) + int(abs(r.normal(0, 15)))
        lo = min(o_, c_) - int(abs(r.normal(0, 15)))
        if hi - lo > rng_max * 10:
            ex = (hi - lo) - rng_max * 10
            hi = max(hi - (ex // 2 + ex % 2), max(o_, c_))
            lo = min(lo + ex // 2, min(o_, c_))
        o.append(o_ * 1e-5), h.append(hi * 1e-5), l.append(lo * 1e-5), c.append(c_ * 1e-5)
        p = c_
    return pd.DataFrame(dict(open=o, high=h, low=l, close=c, spread=spread_pts),
                        index=pd.date_range("2024-01-01", periods=n, freq="15min"))


def bars_that(n: int = 1500, seed: int = 1, spread_pts: int = 20) -> pd.DataFrame:
    """Giong `bars` nhung bien do nen nhu M15 that cua cap FX (trung binh ~7 pip, toi da 25): do lech mo hinh bar o day moi co nghia."""
    r = np.random.RandomState(seed)
    o, h, l, c = [], [], [], []
    p = 90000
    for _ in range(n):
        o_ = p
        c_ = o_ + int(round(r.normal(-0.01 * (p - 90000), 45)))
        hi = max(o_, c_) + int(abs(r.normal(0, 25)))
        lo = min(o_, c_) - int(abs(r.normal(0, 25)))
        if hi - lo > 250:
            ex = (hi - lo) - 250
            hi = max(hi - (ex // 2 + ex % 2), max(o_, c_))
            lo = min(lo + ex // 2, min(o_, c_))
        o.append(o_ * 1e-5), h.append(hi * 1e-5), l.append(lo * 1e-5), c.append(c_ * 1e-5)
        p = c_
    return pd.DataFrame(dict(open=o, high=h, low=l, close=c, spread=spread_pts),
                        index=pd.date_range("2024-01-01", periods=n, freq="15min"))


def tk_tay(diem, spread: float = 0.0, paso: float = 1e-5, giay: float = 1.0) -> dict:
    """Duong gia dung TAY: danh sach moc BID noi lien tiep bang buoc `paso` (tick dau = moc dau). `spread` la GIA (0,0002 = 2 pip)."""
    pts = [int(round(diem[0] / paso))]
    for a, b in zip(diem[:-1], diem[1:]):
        a, b = int(round(a / paso)), int(round(b / paso))
        if b != a:
            pts += list(a + np.sign(b - a) * np.arange(1, abs(b - a) + 1))
    bid = np.array(pts) * paso
    t = 1.7e9 + np.arange(len(bid)) * giay
    return dict(bid=bid, spread=np.full(len(bid), float(spread)), time=t, bar=np.floor(t / 900.0) * 900.0,
                bar_idx=np.zeros(len(bid), np.int64))


@pytest.fixture(scope="module")
def exe(tmp_path_factory):
    if G.trinh_bien_dich() is None:
        pytest.skip("khong co trinh bien dich C++")
    return G.bien_dich(EA_MQ5, thu_muc=tmp_path_factory.mktemp("ea_gia_lap_exe"))


def chay_tay(exe, diem, spread: float, ts: dict, von: float = 10000.0) -> dict:
    r = G.chay(exe, tk_tay(diem, spread), von, dict(InpPipSize=1e-4, **ts), digits=5)
    assert r["ok"], (r["loi"], r["log"][-3:])
    return r


#: 00:00:00 UTC cua mot ngay (19675 x 86400): tick dau cua `tk_chuoi(..., t0=NGAY0)` o 0h, giay trong ngay = chi so tick x `giay`.
NGAY0 = 1699920000.0


def tk_chuoi(bid, giay: float = 1.0, t0: float = 1.7e9, spread: float = 0.0) -> dict:
    """Duong gia cho TUNG TICK (khong noi bang buoc paso): `bid[k]` la BID cua tick k luc `t0 + k * giay` giay. Dung de dat gia nhay / dung yen dung vao mot
    giay cho truoc (tick 'dung yen' van la mot tick) - `tk_tay` chi sinh tick khi gia doi."""
    bid = np.round(np.asarray(bid, float), 5)
    t = t0 + np.arange(len(bid)) * giay
    return dict(bid=bid, spread=np.full(len(bid), float(spread)), time=t, bar=np.floor(t / 900.0) * 900.0,
                bar_idx=np.zeros(len(bid), np.int64))


def chay_tk(exe, tk: dict, ts: dict, von: float = 10000.0) -> dict:
    r = G.chay(exe, tk, von, dict(InpPipSize=1e-4, **ts), digits=5)
    assert r["ok"], (r["loi"], r["log"][-3:])
    return r


def bang(r: dict) -> pd.DataFrame:
    return r["lenh"].sort_values("ticket").reset_index(drop=True)


# ============================================================ 1. bang ten, tham so (khong can trinh bien dich)
def test_bang_ten_phu_het_truong_thamso():
    """Truong moi them vao `luoi.ThamSo` ma EA chua co input -> test nay do: bo phan ton tai nhung khong nam tren duong chay."""
    truong = {f.name for f in dataclasses.fields(L.ThamSo)}
    chua = truong - set(G.BANG_TEN) - set(G.KHONG_CO_TRONG_EA)
    assert not chua, "ThamSo co truong ma EA chua anh xa: %s (them input vao ea_LuoiDayDu.mq5 + BANG_TEN)" % sorted(chua)
    thua = (set(G.BANG_TEN) | set(G.KHONG_CO_TRONG_EA)) - truong
    assert not thua, "BANG_TEN / KHONG_CO_TRONG_EA nhac truong khong con trong ThamSo: %s" % sorted(thua)
    assert not set(G.BANG_TEN) & set(G.KHONG_CO_TRONG_EA)


def test_bang_ten_tro_dung_input_cua_ea():
    ma = EA_MQ5.read_text(encoding="utf-8")
    khai = EA.input_khai_bao(ma)
    for truong, ten in G.BANG_TEN.items():
        assert ten in khai, "BANG_TEN[%s] = %s khong phai input cua ea_LuoiDayDu.mq5" % (truong, ten)
    # moi input cua EA hoac co truong tuong ung, hoac la thu cua tai khoan / san (ma so, do truot, kich thuoc pip)
    mo_coi = set(khai) - set(G.BANG_TEN.values()) - {"InpMagic", "InpDeviation", "InpPipSize"}
    assert not mo_coi, "input khong co truong ThamSo tuong ung: %s" % sorted(mo_coi)
    assert len(set(G.BANG_TEN.values())) == len(G.BANG_TEN)       # khong hai truong dung chung mot input


def test_mac_dinh_ea_khop_mac_dinh_thamso():
    """Nguoi chay EA khong dien gi phai nhan dung he thong ma `luoi.ThamSo()` mac dinh mo ta (khong tia, khong cho lui, khong chot tien)."""
    mac_dinh = {d["ten"]: d["mac_dinh"] for d in EA.input_so(EA_MQ5.read_text(encoding="utf-8"))}
    for ten, v in G.tham_so_ea_tu_luoi(L.ThamSo()).items():
        if ten == "InpLotKind":
            continue          # EA mac dinh 'nhan' (giu bo tham so cu); ThamSo 'phang' - GIONG nhau khi he so lot = 1
        assert mac_dinh[ten] == v, "mac dinh %s: EA %r, ThamSo %r" % (ten, mac_dinh[ten], v)
    assert mac_dinh["InpLotKind"] == 1 and mac_dinh["InpLotMult"] == 1.0 and mac_dinh["InpPipSize"] == 0.0


def test_input_cua_ea_cu_van_dung_duoc():
    """`ea_LuoiThamChieu.mq5` la EA hieu chuan toi thieu (lan `_chay_that` dau); bo tham so cu phai chay y nguyen tren EA moi."""
    cu = {d["ten"]: d for d in EA.input_so(EA_CU.read_text(encoding="utf-8"))}
    moi = {d["ten"]: d for d in EA.input_so(EA_MQ5.read_text(encoding="utf-8"))}
    for ten, d in cu.items():
        assert ten in moi, "EA moi thieu input cu %s" % ten
        assert moi[ten]["kieu"] == d["kieu"], ten
        if ten != "InpMagic":                          # magic khac nhau CO CHU DICH (hai EA cung ma khong dam lenh nhau)
            assert moi[ten]["mac_dinh"] == d["mac_dinh"], "mac dinh cua %s doi: %s -> %s" % (ten, d["mac_dinh"], moi[ten]["mac_dinh"])
    assert moi["InpMagic"]["mac_dinh"] != cu["InpMagic"]["mac_dinh"]
    ma = EA_MQ5.read_text(encoding="utf-8")
    assert EA.kiem_tham_so({ten: d["mac_dinh"] for ten, d in cu.items()}, ma) is None


def test_tham_so_ea_tu_luoi_tn5():
    ts = CAU_HINH["tn5"]
    ps = G.tham_so_ea_tu_luoi(ts)
    assert ps == {"InpLot": 0.04, "InpStepPips": 21, "InpTpPips": 9, "InpMaxLevels": 9, "InpMode": 2, "InpLotMult": 0.25,
                  "InpLotKind": 2, "InpStepMult": 1.2, "InpStepCap": ts.buoc_tran, "InpSpark": 1, "InpSparkPips": 5,
                  "InpSparkPerBar": ts.cap_moi_bar, "InpWaitBack": ts.cho_lui, "InpTakeMoney": ts.chot_tien}
    # bo tham so ma cloud dua cho may nha qua `ea_tho_chay` phai la bo MA tester chap nhan
    assert EA.kiem_tham_so(ps, EA_MQ5.read_text(encoding="utf-8")) is None
    for che_do, so in (("mua", 0), ("ban", 1), ("hai_chieu", 2)):
        assert G.tham_so_ea_tu_luoi(dataclasses.replace(ts, che_do=che_do))["InpMode"] == so
    for kieu, so in (("phang", 0), ("nhan", 1), ("cong", 2)):
        assert G.tham_so_ea_tu_luoi(dataclasses.replace(ts, kieu_lot=kieu))["InpLotKind"] == so
    assert G.tham_so_ea_tu_luoi(dataclasses.replace(ts, tia_lenh=False))["InpSpark"] == 0


def test_tham_so_ea_tu_luoi_tu_choi_truong_la_va_dung_lo_tong():
    with pytest.raises(ValueError, match="chua co input"):
        G.tham_so_ea_tu_luoi({"lot": 0.01, "truong_la_moi": 1})
    with pytest.raises(ValueError, match="dung_lo_tong"):
        G.tham_so_ea_tu_luoi(dataclasses.replace(CAU_HINH["tn5"], dung_lo_tong=5.0))
    assert "InpLot" in G.tham_so_ea_tu_luoi(dataclasses.replace(CAU_HINH["tn5"], dung_lo_tong=0.0))   # 0 = tat: duoc phep


def test_kiem_tham_so_bat_ten_sai_va_so_le():
    ma = EA_MQ5.read_text(encoding="utf-8")
    assert "InpStepPip" in (EA.kiem_tham_so({"InpStepPip": 21}, ma) or "")             # thieu chu 's': MT5 se IM LANG bo qua
    assert EA.kiem_tham_so({"InpMode": 1.5}, ma)                                       # input int nhan so nguyen
    assert EA.kiem_tham_so({"InpSpark": 1, "InpSparkPips": 5}, ma) is None


def test_bo_property_giu_so_dong_va_chan_include_la():
    ma = '#property copyright "x"\n#include <Trade/Trade.mqh>\ninput int A = 1;\n   #  property version "1"\nvoid OnTick() {}\n'
    ra = G.bo_property(ma)
    assert ra.count("\n") == ma.count("\n")                                           # giu so dong de loi bien dich tro dung dong
    assert "#property" not in ra and "#include" not in ra and "input int A = 1;" in ra
    with pytest.raises(ValueError, match="include"):
        G.bo_property("#include <Math/Stat/Normal.mqh>\n")
    that = EA_MQ5.read_text(encoding="utf-8")
    assert G.bo_property(that).count("\n") == that.count("\n")


def test_tick_tu_bar_thu_tu_va_buoc():
    df = pd.DataFrame(dict(open=[1.0000], high=[1.0003], low=[0.9997], close=[1.0001], spread=[20]),
                      index=pd.date_range("2024-01-01", periods=1, freq="15min"))
    for thu, thap_truoc in (("thap_truoc", True), ("cao_truoc", False), ("theo_nen", True), ("xen_ke", True)):
        b = G.tick_tu_bar(df, thu)["bid"]
        assert b[0] == pytest.approx(1.0000) and b[-1] == pytest.approx(1.0001)
        assert b.min() == pytest.approx(0.9997) and b.max() == pytest.approx(1.0003)
        assert bool(np.argmin(b) < np.argmax(b)) is thap_truoc
        assert np.allclose(np.abs(np.diff(b)), 1e-5)                                  # moi tick dung MOT buoc gia
    nho = G.tick_tu_bar(df, "thap_truoc", paso=1e-6)
    assert np.allclose(np.abs(np.diff(nho["bid"])), 1e-6) and len(nho["bid"]) == 10 * (len(G.tick_tu_bar(df)["bid"]) - 1) + 1
    assert np.allclose(nho["spread"], 20 * 1e-5)
    with pytest.raises(ValueError, match="paso"):
        G.tick_tu_bar(df, paso=3e-6)
    giam = df.assign(open=1.0001, close=0.9999)                                       # nen giam: theo_nen = cao truoc
    b = G.tick_tu_bar(giam, "theo_nen")["bid"]
    assert np.argmax(b) < np.argmin(b)


def test_barra_tu_tick_moi_tick_la_mot_bar():
    tk = tk_tay([1.0, 1.0003, 1.0001], 0.0002)
    bt = G.barra_tu_tick(tk, nhieu=1e-9)
    assert len(bt) == len(tk["bid"]) and bt.index.is_monotonic_increasing and bt.index.is_unique
    assert np.allclose(bt.open, tk["bid"]) and np.allclose(bt.close, tk["bid"])
    assert np.allclose(bt.high - bt.low, 2e-9, atol=1e-12)
    assert np.allclose(bt.spread, 20.0)                                               # spread theo POINT (0,0002 / 1e-5)


def _cap(chieu=1, lot=0.01, gia_mo=1.0, i_mo=0, i_dong=-1, ly_do="tp", vol=None, bid_mo=None, tick_mo=None, tick_dong=None, ea_ly_do=None):
    e = pd.DataFrame(dict(chieu=[chieu], lot=[lot], gia_mo=[gia_mo], i_mo=[i_mo], i_dong=[i_dong], ly_do=[ly_do], tang=[0]))
    a = pd.DataFrame(dict(chieu=[chieu], vol=[lot if vol is None else vol], bid_mo=[gia_mo if bid_mo is None else bid_mo],
                          tick_mo=[i_mo if tick_mo is None else tick_mo],
                          tick_dong=[i_dong if tick_dong is None else tick_dong],
                          ly_do=[("tp" if i_dong >= 0 else "open") if ea_ly_do is None else ea_ly_do]))
    return e, a


def test_so_lenh_phan_loai_tung_loai_lech():
    paso = 1e-6
    assert G.so_lenh(*_cap(i_dong=50), paso)[1] == "khop"
    assert G.so_lenh(*_cap(i_dong=50, tick_dong=51), paso)[1] == "khop"                # lech 1 tick: cho phep
    assert G.so_lenh(*_cap(i_dong=50, tick_dong=52), paso)[1] == "lech_dong"
    assert G.so_lenh(*_cap(i_dong=50, ea_ly_do="open"), paso)[1] == "lech_dong"        # engine dong, EA chua
    assert G.so_lenh(*_cap(i_dong=-1, ea_ly_do="tp", tick_dong=9), paso)[1] == "lech_dong"
    assert G.so_lenh(*_cap(i_mo=10, tick_mo=12, i_dong=50, tick_dong=50), paso)[1] == "lech_tick_mo"
    assert G.so_lenh(*_cap(gia_mo=1.0, bid_mo=1.0 + 3 * paso, i_dong=50), paso)[1] == "lech_gia"
    assert G.so_lenh(*_cap(gia_mo=1.0, bid_mo=1.0 + 2 * paso, i_dong=50), paso)[1] == "khop"
    assert G.so_lenh(*_cap(lot=0.02, vol=0.01, i_dong=50), paso)[1] == "lech_chieu_lot"
    e, a = _cap(i_dong=50)
    a2 = a.assign(chieu=-1)
    assert G.so_lenh(e, a2, paso)[1] == "lech_chieu_lot"
    assert G.so_lenh(e, pd.concat([a, a], ignore_index=True), paso)[1] == "lech_so_lenh"
    k, tt, ct = G.so_lenh(e, e.iloc[0:0].assign(vol=0.0, bid_mo=0.0, tick_mo=0, tick_dong=0), paso)
    assert tt == "lech_so_lenh" and k == 0 and "1 lenh" in ct


# ============================================================ 2. trinh bien dich + cu phap
@can_cxx
def test_cu_phap_nghiem_ngat():
    """`chi_cu_phap=True` bien `input` thanh const (MQL5 cam gan gia tri cho input) + -Wall: khong loi, tra None."""
    assert G.bien_dich(EA_MQ5, chi_cu_phap=True) is None


@can_cxx
def test_ea_gan_gia_tri_cho_input_bi_bat(tmp_path):
    ma = EA_MQ5.read_text(encoding="utf-8").replace("g_trade.SetExpertMagicNumber(InpMagic);",
                                                    "InpLot = 0.02;\n   g_trade.SetExpertMagicNumber(InpMagic);", 1)
    assert "InpLot = 0.02;" in ma
    p = tmp_path / "ea_xau.mq5"
    p.write_text(ma, encoding="utf-8")
    with pytest.raises(G.LoiBienDich) as e:
        G.bien_dich(p, chi_cu_phap=True, thu_muc=tmp_path / "b")
    assert "InpLot" in e.value.args[0]


@can_cxx
def test_loi_cu_phap_tro_dung_dong(tmp_path):
    """Dong trong van ban EA sau `bo_property` = dong trong file .mq5 that (bo_property thay dong bo bang dong trong)."""
    dong = EA_MQ5.read_text(encoding="utf-8").splitlines()
    m = next(i for i, d in enumerate(dong) if d.startswith("void OnDeinit"))
    dong.insert(m, "Dong_Hong_O_Day;")
    p = tmp_path / "ea_hong.mq5"
    p.write_text("\n".join(dong) + "\n", encoding="utf-8")
    with pytest.raises(G.LoiBienDich) as e:
        G.bien_dich(p, chi_cu_phap=True, thu_muc=tmp_path / "b")
    assert ("ea_pp.inc:%d:" % (m + 1)) in e.value.args[0] and "Dong_Hong_O_Day" in e.value.args[0]


# ============================================================ 3. kich ban tay (so tinh TRUOC bang tay)
@can_cxx
def test_tay_mua_hai_tang_roi_tp(exe):
    """L1 mua BID 1,0000 (ASK 1,0002). Gia xuong 10 pip -> L2 BID 0,9990 (ASK 0,9992). TP BID = (1,0000 + 0,9990)/2 + 5 pip = 1,0000.
    Gia len 1,0000 -> dong ca hai: L1 -0,2 (1,0000 - 1,0002), L2 +0,8 (1,0000 - 0,9992). Tong +0,6. Dong xong mo lai L1 ngay."""
    r = chay_tay(exe, [1.0, 0.999, 1.0], 0.0002,
                 dict(InpLot=0.01, InpStepPips=10, InpTpPips=5, InpMaxLevels=5, InpMode=0, InpLotKind=0))
    lai = ((1.0000 - 1.0002) + (1.0000 - 0.9992)) * 0.01 * HOP
    assert lai == pytest.approx(0.6)
    k = r["kq"]
    assert k["balance"] == pytest.approx(10000.0 + lai, abs=1e-6)
    assert (k["n_mo"], k["n_dong"], k["n_tp"], k["n_ea"], k["con_mo"]) == (3, 2, 2, 0, 1)
    assert k["spread_con_mo"] == pytest.approx(0.0002 * 0.01 * HOP)                   # lenh mo lai o tick cuoi chua tra het spread
    t = bang(r)
    assert list(t.open) == pytest.approx([1.0002, 0.9992, 1.0002])
    assert list(t.tick_mo) == [0, 100, 200] and list(t.ly_do) == ["tp", "tp", "open"]
    assert t.tick_dong[0] == 200 and t.tick_dong[1] == 200 and list(t.close[:2]) == pytest.approx([1.0, 1.0])


@can_cxx
def test_tay_ban_la_guong_cua_mua(exe):
    """BAN khop o BID, dong o ASK. L1 ban BID 1,0000, L2 ban BID 1,0010; TP BID = 1,0005 - 5 pip = 1,0000 (TP may chu = TP + spread,
    dong khi ASK cham). L1 = 1,0000 - 1,0002 = -0,0002; L2 = 1,0010 - 1,0002 = +0,0008 -> +0,6."""
    r = chay_tay(exe, [1.0, 1.001, 1.0], 0.0002,
                 dict(InpLot=0.01, InpStepPips=10, InpTpPips=5, InpMaxLevels=5, InpMode=1, InpLotKind=0))
    lai = ((1.0000 - 1.0002) + (1.0010 - 1.0002)) * 0.01 * HOP
    k = r["kq"]
    assert k["balance"] == pytest.approx(10000.0 + lai, abs=1e-6) and lai == pytest.approx(0.6)
    assert (k["n_mo"], k["n_dong"], k["n_tp"], k["con_mo"]) == (3, 2, 2, 1)
    t = bang(r)
    assert set(t.type) == {1} and list(t.open) == pytest.approx([1.0, 1.001, 1.0])      # BAN mo o BID
    assert k["spread_con_mo"] == pytest.approx(0.0002 * 0.01 * HOP)                   # engine tru spread luc MO ca lenh ban


@can_cxx
def test_tay_lot_nhan_tp_lam_tron_theo_digits(exe):
    """L1 0,01 @1,0000; L2 0,02 @0,9990 (he 2). BID TB co trong so lot = (0,01*1,0000 + 0,02*0,9990)/0,03 = 0,999333.. ; TP = +5 pip =
    0,999833.. -> chuan hoa 5 chu so = 0,99983 (MT5 bat buoc TP chia het point). Dong khi BID = 0,99983: -0,17 + 1,66 = +1,49."""
    r = chay_tay(exe, [1.0, 0.999, 1.0], 0.0,
                 dict(InpLot=0.01, InpStepPips=10, InpTpPips=5, InpMaxLevels=5, InpMode=0, InpLotKind=1, InpLotMult=2.0))
    tp = round((0.01 * 1.0 + 0.02 * 0.999) / 0.03 + 0.0005, 5)
    assert tp == pytest.approx(0.99983)
    lai = (tp - 1.0) * 0.01 * HOP + (tp - 0.999) * 0.02 * HOP
    assert lai == pytest.approx(1.49)
    k, t = r["kq"], bang(r)
    assert k["balance"] == pytest.approx(10000.0 + lai, abs=1e-6)
    assert list(t.vol[:2]) == [0.01, 0.02] and list(t.close[:2]) == pytest.approx([tp, tp])
    assert t.tick_dong[0] == 183 and t.tick_dong[1] == 183                              # 0,9990 (tick 100) -> 0,99983: 83 tick
    assert k["lot_con_mo"] == pytest.approx(0.01)


@can_cxx
def test_tay_tia_lenh_dong_cap_dau_cuoi(exe):
    """Mua phang, TP rat xa. L1 @1,0000, L2 @0,9990, L3 @0,9980. Tia: cap (L1 dau, L3 cuoi). Lai cap theo BID khi gia = b:
    (b - 1,0000)*0,01 + (b - 0,9980)*0,01 >= 4 pip * 0,02 lot -> b >= 0,9994 (tick 340). Cap lai +0,8 truoc spread.
    Spread 2 pip: moi lenh MUA da tra 0,2 -> hai lenh dong ghi so du +0,8 - 0,4 = +0,4. L2 (tang giua) van mo, k van 3."""
    r = chay_tay(exe, [1.0, 0.998, 0.9994], 0.0002,
                 dict(InpLot=0.01, InpStepPips=10, InpTpPips=100, InpMaxLevels=5, InpMode=0, InpLotKind=0, InpSpark=1,
                      InpSparkPips=4))
    k, t = r["kq"], bang(r)
    cap = ((0.9994 - 1.0000) + (0.9994 - 0.9980)) * 0.01 * HOP
    assert cap == pytest.approx(0.8)
    assert k["balance"] == pytest.approx(10000.0 + cap - 2 * 0.0002 * 0.01 * HOP, abs=1e-6)
    assert (k["n_mo"], k["n_dong"], k["n_ea"], k["n_tp"], k["con_mo"]) == (3, 2, 2, 0, 1)
    assert list(t.ly_do) == ["ea", "open", "ea"] and list(t.tick_dong.dropna()) == [340, 340]
    assert k["spread_con_mo"] == pytest.approx(0.2)


@can_cxx
def test_tay_chot_tien_dong_ca_ro_khi_lai_noi_du(exe):
    """Mua phang 0,01, chot_tien = 0,855 (tien bao gia tren 0,01 lot), TP pip bi bo qua. L1 @1,0000, L2 @0,9990. Lai noi theo BID tai b:
    ((b - 1,0000) + (b - 0,9990)) * 1000. EA cho dung sai NUA POINT tren tong lot (0,01 tien o day): dong khi lai noi >= 0,845.
    b = 0,99992 -> 0,84 (chua), b = 0,99993 -> 0,86: dong o tick 193, so du +0,86."""
    cau_hinh = dict(InpLot=0.01, InpStepPips=10, InpTpPips=5, InpMaxLevels=5, InpMode=0, InpLotKind=0)
    r = chay_tay(exe, [1.0, 0.999, 1.0], 0.0, dict(cau_hinh, InpTakeMoney=0.855))
    k, t = r["kq"], bang(r)
    b = 0.99993
    lai = ((b - 1.0) + (b - 0.999)) * 0.01 * HOP
    assert lai == pytest.approx(0.86)
    assert k["balance"] == pytest.approx(10000.0 + lai, abs=1e-6)
    assert (k["n_mo"], k["n_dong"], k["n_ea"], k["n_tp"], k["con_mo"]) == (3, 2, 2, 0, 1)
    assert list(t.tick_dong.dropna()) == [193, 193] and t.tick_mo[2] == 193           # mo lai ngay o tick dong
    assert float(t.open[2]) == pytest.approx(b)
    # dung sai nua point: nguong 0,85 DUNG BANG diem hoa (0,84 + 0,01) -> dong som mot tick (b = 0,99992, lai 0,84)
    r2 = chay_tay(exe, [1.0, 0.999, 1.0], 0.0, dict(cau_hinh, InpTakeMoney=0.85))
    assert list(bang(r2).tick_dong.dropna()) == [192, 192]
    assert r2["kq"]["balance"] == pytest.approx(10000.0 + ((0.99992 - 1.0) + (0.99992 - 0.999)) * 0.01 * HOP, abs=1e-6)   # +0,84
    # nguong 0,875 -> dong khi lai noi >= 0,865: tick 194 (b = 0,99994, lai 0,88)
    r3 = chay_tay(exe, [1.0, 0.999, 1.0], 0.0, dict(cau_hinh, InpTakeMoney=0.875))
    assert list(bang(r3).tick_dong.dropna()) == [194, 194]


@can_cxx
def test_tay_cho_lui_khong_mo_lai_ngay(exe):
    """cho_lui = 3 pip: sau khi dong o BID 1,0000 (tick 200) KHONG mo lai; gia len 1,0010 roi xuong, L1 moi mo khi BID <= 1,0000 - 3 pip
    = 0,9997. Tick 430 (0,9997). Gia chi xuong 0,9990 (lui 7 pip < buoc 10 pip tinh tu 0,9997) nen khong co tang 2."""
    r = chay_tay(exe, [1.0, 0.999, 1.0, 1.001, 0.9997, 0.999], 0.0,
                 dict(InpLot=0.01, InpStepPips=10, InpTpPips=5, InpMaxLevels=5, InpMode=0, InpLotKind=0, InpWaitBack=3))
    k, t = r["kq"], bang(r)
    assert (k["n_mo"], k["n_dong"], k["con_mo"]) == (3, 2, 1)
    assert list(t.tick_mo) == [0, 100, 430] and float(t.open[2]) == pytest.approx(0.9997)
    assert k["balance"] == pytest.approx(10000.0 + (1.0 - 0.999) * 0.01 * HOP, abs=1e-6)


@can_cxx
def test_tay_buoc_gian_co_tran_va_tran_tang(exe):
    """buoc 10, he 2, tran buoc 25 pip, toi da 4 tang. Tang 2 sau 10 pip (0,9990); tang 3 sau min(20, 25) = 20 pip (0,9970); tang 4 sau
    min(40, 25) = 25 pip (0,99450). Gia xuong 0,9900 nhung tang 5 bi chan boi InpMaxLevels = 4."""
    r = chay_tay(exe, [1.0, 0.99], 0.0,
                 dict(InpLot=0.01, InpStepPips=10, InpTpPips=500, InpMaxLevels=4, InpMode=0, InpLotKind=0, InpStepMult=2.0,
                      InpStepCap=25))
    t = bang(r)
    bid = [float(c[3:]) for c in t.comment]
    assert bid == pytest.approx([1.0, 0.999, 0.997, 0.9945])
    assert r["kq"]["n_mo"] == 4 and r["kq"]["max_open"] == 4


@can_cxx
def test_tay_lot_cong_va_lam_tron_den_buoc_lot(exe):
    """Lot cong 0,04 * (1 + 0,25 k): 0,04 / 0,05 / 0,06 / 0,07. Lot nhan 0,01 * 1,5^k = 0,01 / 0,015 / 0,0225 / 0,03375 lam tron TOI GAN
    NHAT theo buoc lot 0,01 (nua buoc tro len): 0,01 / 0,02 / 0,02 / 0,03."""
    base = dict(InpStepPips=10, InpTpPips=500, InpMaxLevels=4, InpMode=0)
    r = chay_tay(exe, [1.0, 0.996], 0.0, dict(base, InpLot=0.04, InpLotKind=2, InpLotMult=0.25))
    assert list(bang(r).vol) == pytest.approx([0.04, 0.05, 0.06, 0.07])
    r = chay_tay(exe, [1.0, 0.996], 0.0, dict(base, InpLot=0.01, InpLotKind=1, InpLotMult=1.5))
    assert list(bang(r).vol) == pytest.approx([0.01, 0.02, 0.02, 0.03])


@can_cxx
def test_tay_hai_chieu_hai_ro_doc_lap_hedging(exe):
    """Tai khoan hedging: o tick 0 mo CA mua LAN ban (hai ro). Gia len 5 pip: ro mua dong TP (+5 pip * 0,01 lot) va mo lai; ro ban
    (BID mo 1,0000 -> dong o ASK 1,0005 = -5 pip) con mo. Hai ro khong lam huy nhau."""
    r = chay_tay(exe, [1.0, 1.0005], 0.0,
                 dict(InpLot=0.01, InpStepPips=10, InpTpPips=5, InpMaxLevels=5, InpMode=2, InpLotKind=0))
    t = bang(r)
    assert list(t.type[:2]) == [0, 1] and list(t.tick_mo[:2]) == [0, 0]
    assert t.ly_do[0] == "tp" and t.close[0] == pytest.approx(1.0005) and t.ly_do[1] == "open"
    assert r["kq"]["balance"] == pytest.approx(10000.0 + 0.0005 * 0.01 * HOP, abs=1e-6)


@can_cxx
def test_khoi_dong_tu_choi_tham_so_sai_va_tai_khoan_netting(exe):
    tk = tk_tay([1.0, 0.999], 0.0002)
    for ts in (dict(InpMode=7), dict(InpMaxLevels=0), dict(InpLotKind=3), dict(InpTpPips=0.0), dict(InpLot=0.0),
               dict(InpSpark=1, InpSparkPips=0.0)):
        r = G.chay(exe, tk, 10000.0, dict(InpPipSize=1e-4, **ts), digits=5)
        assert not r["ok"] and r["kq"]["init_ok"] == 0.0 and r["kq"].get("n_mo", 0) == 0, ts
    assert G.chay(exe, tk, 10000.0, dict(InpPipSize=1e-4, InpTpPips=0.0, InpTakeMoney=2.0), digits=5)["ok"]  # chot tien thay TP: hop le
    r = G.chay(exe, tk, 10000.0, dict(InpPipSize=1e-4), netting=True, digits=5)
    assert not r["ok"] and any("HEDGING" in d for d in r["log"])                      # netting gop cac tang: EA tu choi chay


# ============================================================ 3b. kich ban tay CHO TINH NANG MOI (08/10/2026)
#: Gio quy ra GIAY NGUYEN va so voi gio TICK (TimeCurrent) nen nhung bai nay dung duong gia theo TUNG GIAY (`tk_chuoi` / `tk_tay`, 1 tick = 1 giay hoac 36 giay) va doc
#: `tick_mo` / `tick_dong`. So tinh TAY truoc, roi moi so voi san gia; cung so voi `test_luoi_thoat_gio.py` (engine) o nhung cho co the (cat 22 pip = c1, lot nhan = c7,
#: hai nguong = c3), tien o day = tien engine / 100 (0,01 lot thay cho 1,0 lot). Tick o buoc 1/10 pip (`paso` 1e-5 voi pip 1e-4): 100 tick = 10 pip.
LUOI_TAY = dict(InpLot=0.01, InpStepPips=10, InpTpPips=100, InpMaxLevels=4, InpMode=0, InpLotKind=0)


def _dem_ea(log) -> tuple[int, int]:
    """(so ro cat lo, so ro thoat gio) ma EA TU DEM va in o OnDeinit (`g_so_cat`, `g_so_gio`)."""
    for dong in reversed(log):
        m = re.search(r"so ro cat lo=(\d+), so ro thoat gio=(\d+)", dong)
        if m:
            return int(m.group(1)), int(m.group(2))
    raise AssertionError("EA khong in dong thong ke o OnDeinit: %r" % (log[-3:],))


@can_cxx
def test_tay_cat_lo_pip_cat_ca_ro_o_trung_binh_tru_khoang_cat_roi_mo_lai_ngay(exe):
    """Mua phang 0,01, buoc 10 pip, toi da 4 tang, cat_lo_pip = 22; gia 1,0000 -> 0,9960. Tang o 0,9990 / 0,9980 / 0,9970 (tick 100 / 200 / 300): moc cat sau tang 1 / 2 / 3
    la 0,9978 / 0,99730 / 0,9968, moi cai nam SAU moc them tang ke tiep -> them tang truoc. Du 4 tang trung binh 0,9985, moc cat = 0,9985 - 22 pip = 0,9963 (tick 370, BID
    cham dung moc: dung sai nua point). Dong ca 4 lenh o 0,9963: (-37 - 27 - 17 - 7 pip) x 0,01 lot = -8,8; mo lai NGAY o tick 370 (khong cho lui, khong nghi)."""
    r = chay_tk(exe, tk_tay([1.0, 0.996], 0.0), dict(LUOI_TAY, InpCutPips=22.0))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [0, 100, 200, 300, 370] and list(t.tick_dong.dropna()) == [370] * 4
    assert list(t.ly_do) == ["ea"] * 4 + ["open"]
    assert list(t.close[:4]) == pytest.approx([0.9963] * 4) and float(t.open[4]) == pytest.approx(0.9963)
    assert k["balance"] == pytest.approx(10000.0 - 8.8, abs=1e-6)
    assert (k["n_mo"], k["n_dong"], k["n_ea"], k["n_tp"], k["con_mo"]) == (5, 4, 4, 0, 1)
    assert _dem_ea(r["log"]) == (1, 0)


@can_cxx
def test_tay_cat_lo_tien_dung_trung_binh_co_trong_so_theo_lot(exe):
    """Lot NHAN doi (0,01 / 0,02), cat_lo_tien = 3,0 (tien bao gia tren 0,01 lot; lot tang 1 = 0,01 -> nguong 3,0). 1 lot: khoang cat 3,0 / (100.000 x 0,01) = 30 pip, them tang
    o 0,9990 truoc. 0,03 lot: trung binh co trong so (0,01 x 1,0000 + 0,02 x 0,9990) / 0,03 = 0,999333 (trung binh ngay thang 0,9995 la SAI), khoang cat 3,0 / (100.000 x 0,03)
    = 10 pip -> moc cat 0,998333, truoc moc them tang 0,9980 -> CAT o BID 0,99833 (tick 167; ben tick 0,99834 chua toi): lo (0,99833 - 1,0)x0,01 + (0,99833 - 0,9990)x0,02 =
    -1,67 - 1,34 = -3,01 (xap xi nguong 3,0). Ro moi 0,01 lot mo ngay o 0,99833."""
    r = chay_tk(exe, tk_tay([1.0, 0.9983], 0.0), dict(LUOI_TAY, InpMaxLevels=5, InpLotKind=1, InpLotMult=2.0, InpCutMoney=3.0))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [0, 100, 167] and list(t.tick_dong.dropna()) == [167, 167] and list(t.vol) == pytest.approx([0.01, 0.02, 0.01])
    assert list(t.close[:2]) == pytest.approx([0.99833] * 2) and float(t.open[2]) == pytest.approx(0.99833)
    assert k["balance"] == pytest.approx(10000.0 - 3.01, abs=1e-6)
    assert _dem_ea(r["log"]) == (1, 0)


@can_cxx
def test_tay_cat_lo_tien_nhan_theo_lot_goc_cua_ea(exe):
    """Nguong cat TIEN tinh cho lot goc 0,01 va NHAN voi InpLot / 0,01 (EA 0,02 lot: nguong gap doi). InpLot = 0,02, cat_lo_tien = 3,0, lot phang, buoc 10 pip: tang 2 o 0,9990 (tick 100).
    Hai tang 0,04 lot: trung binh 0,9995, khoang cat 3,0 x 2 / (100.000 x 0,04) = 15 pip -> moc 0,9980 = ngay moc them tang 3 -> cat truoc (tick 200): lo (-20 - 10 pip) x 0,02 lot
    = -6,0 (= 3,0 x 2). EA quen nhan lot goc cat o moc 0,99875 (khoang 7,5 pip) o tick ~125; ro moi mo lai o tick 200."""
    r = chay_tk(exe, tk_tay([1.0, 0.9975], 0.0), dict(LUOI_TAY, InpLot=0.02, InpMaxLevels=5, InpCutMoney=3.0))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [0, 100, 200] and list(t.tick_dong.dropna()) == [200, 200] and list(t.vol) == pytest.approx([0.02] * 3)
    assert list(t.close[:2]) == pytest.approx([0.998] * 2) and k["balance"] == pytest.approx(10000.0 - 6.0, abs=1e-6) and _dem_ea(r["log"]) == (1, 0)


@can_cxx
def test_tay_cat_lo_dung_sai_nua_point_khi_moc_tinh_lech_mot_ulp(exe):
    """cat_lo_tien = 25,7, 1 tang 0,01 lot (InpMaxLevels = 1, khong them tang): khoang cat 25,7 / (100.000 x 0,01) = 0,0257 -> moc = 1 - 0,0257 = 0,9742999999999999 (double), THAP hon
    luoi gia 0,9743 dung mot ulp. Tick 2570 co BID = 0,97430 (luoi gia): nho dung sai nua point EA CAT ngay o tick 2570 (lo -25,7); ban khong dung sai thay 0,97430 > moc nen cat tre mot tick."""
    r = chay_tk(exe, tk_tay([1.0, 0.9740], 0.0), dict(LUOI_TAY, InpMaxLevels=1, InpCutMoney=25.7))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [0, 2570] and t.tick_dong[0] == 2570 and float(t.close[0]) == pytest.approx(0.9743)
    assert k["balance"] == pytest.approx(10000.0 - 25.7, abs=1e-6) and _dem_ea(r["log"]) == (1, 0)


@can_cxx
def test_tay_hai_nguong_cat_nguong_nao_gan_trung_binh_hon_thang(exe):
    """cat_lo_pip = 12 VA cat_lo_tien = 2,0 (20 pip / tong lot tinh theo 0,01): 0,01 lot -> min(12, 20) = 12 pip (theo pip), 0,02 lot -> min(12, 10) = 10 pip (theo tien). Ro 1:
    tang 2 o 0,9990 (tick 100), trung binh 0,9995, moc cat 0,9985 (tick 150): lo -1,5 - 0,5 = -2,0 = DUNG nguong tien; mo lai o 0,9985. Ro 2: tang 2 o 0,9975 (tick 250), cat o
    0,9970 (tick 300, lo -2,0). Ro 3 mo 0,9970, tang 2 o 0,9960 (tick 400); moc cat 0,9955 chua toi (gia chi xuong 0,9957): 6 lenh, 4 dong, so du 10000 - 4,0."""
    r = chay_tk(exe, tk_tay([1.0, 0.9957], 0.0),
                dict(LUOI_TAY, InpMaxLevels=5, InpCutPips=12.0, InpCutMoney=2.0))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [0, 100, 150, 250, 300, 400] and list(t.tick_dong.dropna()) == [150, 150, 300, 300]
    assert list(t.close[:4]) == pytest.approx([0.9985, 0.9985, 0.9970, 0.9970])
    assert k["balance"] == pytest.approx(10000.0 - 4.0, abs=1e-6)
    assert (k["n_mo"], k["n_dong"], k["con_mo"]) == (6, 4, 2) and _dem_ea(r["log"]) == (2, 0)


@can_cxx
def test_tay_thoat_gio_dong_ro_o_tick_du_tuoi_dung_giay_roi_mo_lai(exe):
    """thoat_gio = 2 gio; moi tick 36 giay (100 tick / gio); gia dao dong 1,00000 / 1,00001 (khong cham TP 100 pip, khong them tang). Ro mo o tick 0, tuoi 7200 giay o tick 200
    (dung `>=`: tick 199 moi 7164 giay): dong o tick 200 (gia = gia mo, lai 0) va mo ro MOI ngay o tick 200 (dong ho chay lai) - chuoi dai 300 tick nen khong den lan thoat thu hai."""
    bid = np.where(np.arange(300) % 2 == 0, 1.0, 1.00001)
    r = chay_tk(exe, tk_chuoi(bid, giay=36.0), dict(LUOI_TAY, InpExitHours=2.0))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [0, 200] and t.tick_dong[0] == 200 and list(t.ly_do) == ["ea", "open"]
    assert k["balance"] == pytest.approx(10000.0) and _dem_ea(r["log"]) == (0, 1)


@can_cxx
def test_tay_thoat_gio_le_4_1_gio_lam_tron_nua_len_den_giay(exe):
    """thoat_gio = 4,1 gio = 4,1 x 3600 = 14759,999999999998 (double) -> lam tron NUA LEN 14760 giay. Tick 1 giay: tick 14759 (tuoi 14759 giay) CHUA thoat, tick 14760 thoat.
    (Cat cut ve 14759 giay -> thoat o tick 14759: sai mot giay, va engine / tester lam tron nua len.)"""
    bid = np.where(np.arange(15000) % 2 == 0, 1.0, 1.00001)
    r = chay_tk(exe, tk_chuoi(bid, giay=1.0), dict(LUOI_TAY, InpExitHours=4.1))
    t = bang(r)
    assert list(t.tick_mo) == [0, 14760] and t.tick_dong[0] == 14760 and _dem_ea(r["log"]) == (0, 1)


@can_cxx
def test_tay_nghi_het_dung_giay_moi_mo_ro_moi(exe):
    """Cat 22 pip nhu bai dau (tick 370, 0,9963) + nghi_gio = 0,5 = 1800 giay (tick 1 giay): ro moi chi duoc mo khi gio tick >= 370 + 1800 -> tick 2170 (tick 2169 con nghi:
    `<`, khong phai `<=`). Trong luc nghi gia dao dong 0,99630 / 0,99631 (khong lenh nao); lenh moi mo o BID cua tick 2170 = 0,9963 (tick chan sau 370)."""
    diem = [1.0, 0.9963] + [0.9963, 0.99631] * 1500
    r = chay_tk(exe, tk_tay(diem, 0.0), dict(LUOI_TAY, InpCutPips=22.0, InpRestHours=0.5))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [0, 100, 200, 300, 2170] and float(t.open[4]) == pytest.approx(0.9963)
    assert list(t.tick_dong.dropna()) == [370] * 4 and k["balance"] == pytest.approx(10000.0 - 8.8, abs=1e-6)
    assert _dem_ea(r["log"]) == (1, 0)


@can_cxx
def test_tay_nghi_bat_dau_ca_sau_thoat_gio_khong_chi_sau_cat(exe):
    """thoat_gio = 2 gio + nghi_gio = 0,5 gio, tick 36 giay (100 tick / gio), gia dao dong 1,00000 / 1,00001. Ro dong o tick 200 (thoat gio, tuoi 7200 giay) roi NGHI 1800 giay = 50 tick:
    ro MOI chi mo o tick 250 (tick 249 con nghi). EA 'chi nghi sau cat lo' se mo lai o tick 200; chuoi 400 tick nen khong den lan thoat thu hai (tick 250 + 200)."""
    bid = np.where(np.arange(400) % 2 == 0, 1.0, 1.00001)
    r = chay_tk(exe, tk_chuoi(bid, giay=36.0), dict(LUOI_TAY, InpExitHours=2.0, InpRestHours=0.5))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [0, 250] and t.tick_dong[0] == 200 and list(t.ly_do) == ["ea", "open"]
    assert k["balance"] == pytest.approx(10000.0) and _dem_ea(r["log"]) == (0, 1)


@can_cxx
def test_tay_cat_va_thoat_gio_mo_lai_ngay_ke_ca_khi_co_cho_lui(exe):
    """Cho lui (InpWaitBack) chi ap dung sau TP / chot tien. Ro dong boi CAT LO hay THOAT GIO: mo lai NGAY o chinh tick dong, khong cho gia lui (engine: `cho_lui` bo qua sau cat / thoat
    gio). Cho lui 150 pip (> TP 100 pip + khoang cat): EA quen ha co 'ro dang song' se dat muc cho = TP cu - 150 pip, thap hon gia luc cat -> khong bao gio mo lai.
    (a) cat 22 pip nhu bai dau: ro moi o tick 370; (b) thoat gio 2 gio (tick 36 giay): ro moi o tick 200."""
    r = chay_tk(exe, tk_tay([1.0, 0.996], 0.0), dict(LUOI_TAY, InpCutPips=22.0, InpWaitBack=150.0))
    t = bang(r)
    assert list(t.tick_mo) == [0, 100, 200, 300, 370] and list(t.tick_dong.dropna()) == [370] * 4 and _dem_ea(r["log"]) == (1, 0)
    bid = np.where(np.arange(300) % 2 == 0, 1.0, 1.00001)
    r = chay_tk(exe, tk_chuoi(bid, giay=36.0), dict(LUOI_TAY, InpExitHours=2.0, InpWaitBack=150.0))
    t = bang(r)
    assert list(t.tick_mo) == [0, 200] and t.tick_dong[0] == 200 and _dem_ea(r["log"]) == (0, 1)


@can_cxx
def test_tay_cho_lui_toi_muc_ngoai_cua_so_gio_giu_muc_cho_den_khi_cua_so_mo(exe):
    """Cua so [1 gio; 2 gio) = tick [100; 200) (36 giay / tick tu 0h), TP 1 pip, cho lui 5 pip. Lenh dau o tick 100 (1,0000); gia len 1,0001 o tick 190 (TRONG cua so): TP dong, muc cho
    = 1,0001 - 5 pip = 0,9996. Gia ve 0,9996 o tick 210 (02:06, NGOAI cua so): KHONG vao, GIU muc cho (EA bo kiem cua so o nhanh cho lui se vao o tick 210). Cua so mo lai ngay hom sau
    luc 01:00 = tick 2500 (86400 + 3600 giay): vao ngay o tick 2500 voi BID luc do (0,9996)."""
    bid = np.full(2600, 1.0)
    bid[190:210] = 1.0001
    bid[210:] = 0.9996
    r = chay_tk(exe, tk_chuoi(bid, giay=36.0, t0=NGAY0), dict(LUOI_TAY, InpTpPips=1, InpWaitBack=5.0, InpHourFrom=1.0, InpHourTo=2.0))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [100, 2500] and t.tick_dong[0] == 190 and list(t.ly_do) == ["tp", "open"]
    assert float(t.open[1]) == pytest.approx(0.9996) and k["balance"] == pytest.approx(10000.1, abs=1e-6)


def _bac_thang(n: int, nhay: dict) -> np.ndarray:
    """Chuoi BID 1,0000 dung yen, MOI diem `k` trong `nhay` cong them `nhay[k]` vao BID tu tick k tro di."""
    bid = np.full(n, 1.0)
    for k, d in nhay.items():
        bid[k:] += d
    return bid


@can_cxx
def test_tay_cua_so_gio_chi_chan_mo_ro_moi_o_hai_dau_nua_khoang(exe):
    """Cua so [0,5 gio; 1,0 gio) = [1800; 3600) giay trong ngay; tick 1 giay tu 0h; TP 1 pip; gia dao dong 1,00000 / 1,00001. Truoc tick 1800 KHONG lenh nao (ngoai cua so); tick 1800
    (= tu) mo ro: lenh dau o tick 1800 (dung `>=`). Gia len 1,0001 DUNG tai tick 3600 (= den): TP dong lenh (+1 pip = +0,1) nhung KHONG mo lai (`<`, khong phai `<=`) - ro rong
    cho toi het chuoi. Cung chuoi voi TP o tick 3599 (con trong cua so): mo lai NGAY o tick 3599."""
    ts = dict(LUOI_TAY, InpTpPips=1, InpHourFrom=0.5, InpHourTo=1.0)
    dao = np.where(np.arange(3700) % 2 == 0, 1.0, 1.00001)
    bid = dao.copy()
    bid[3591:] = 1.0 + (np.arange(3591, 3700) - 3590) * 1e-5            # 3599 -> 1,00009 ; 3600 -> 1,00010 (= TP)
    bid[3601:] = 1.0001
    r = chay_tk(exe, tk_chuoi(bid, t0=NGAY0), ts)
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [1800] and list(t.tick_dong.dropna()) == [3600] and list(t.ly_do) == ["tp"]
    assert k["balance"] == pytest.approx(10000.1, abs=1e-6) and (k["n_mo"], k["n_dong"], k["con_mo"]) == (1, 1, 0)
    bid = dao.copy()
    bid[3590:] = 1.0 + (np.arange(3590, 3700) - 3589) * 1e-5            # 3598 -> 1,00009 ; 3599 -> 1,00010 (= TP)
    bid[3600:] = 1.0001
    r = chay_tk(exe, tk_chuoi(bid, t0=NGAY0), ts)
    t = bang(r)
    assert list(t.tick_mo) == [1800, 3599] and t.tick_dong[0] == 3599 and list(t.ly_do) == ["tp", "open"] and float(t.open[1]) == pytest.approx(1.0001)


@can_cxx
def test_tay_cua_so_gio_qua_nua_dem_hai_nhanh_va_ranh_gioi(exe):
    """Cua so [23 gio; 1 gio) qua nua dem, tick 1 giay tu 22:59:00 (sec 82740), TP 1 pip, gia nhay +1 pip (1,0000 -> 1,0001 -> ...) tai tick 30 / 1000 / 3700 / 6300 / 7260 / 7300.
    Tick 30 (22:59:30, NGOAI cua so): khong lenh nao. Tick 60 = 23:00:00 (= tu) mo lenh dau (dung `>=` o nhanh `sec >= tu`). Tick 1000 (23:16:40) TP + mo lai. Tick 3700 = 00:00:40
    (SAU nua dem) TP + mo lai (nhanh `sec < den`). Tick 6300 (00:44:00) TP + mo lai. Tick 7260 = 01:00:00 (= den): TP dong nhung KHONG mo lai. Tick 7300: khong lenh nao.
    4 lenh, moi lenh +1 pip = +0,1 -> 10000,4."""
    bid = _bac_thang(7400, {30: 1e-4, 1000: 1e-4, 3700: 1e-4, 6300: 1e-4, 7260: 1e-4, 7300: 1e-4})
    r = chay_tk(exe, tk_chuoi(bid, t0=NGAY0 + 82740), dict(LUOI_TAY, InpTpPips=1, InpHourFrom=23.0, InpHourTo=1.0))
    t, k = bang(r), r["kq"]
    assert list(t.tick_mo) == [60, 1000, 3700, 6300] and list(t.tick_dong) == [1000, 3700, 6300, 7260] and set(t.ly_do) == {"tp"}
    assert list(t.open) == pytest.approx([1.0001, 1.0002, 1.0003, 1.0004])
    assert k["balance"] == pytest.approx(10000.4, abs=1e-6) and (k["n_mo"], k["n_dong"], k["con_mo"]) == (4, 4, 0)


@can_cxx
def test_tay_gio_le_4_1_lam_tron_nua_len_cho_ca_nghi_tu_va_den(exe):
    """4,1 gio = 4,1 x 3600 = 14759,999999999998 (double) -> 14760 giay NGUYEN (lam tron nua len) o CA BA cho EA doi gio ra giay - khong chi o thoat gio:
    (a) NGHI 4,1 gio sau cat 22 pip o tick 370: ro moi o tick 370 + 14760 = 15130 (cat cut -> 15129).
    (b) cua so [4,1 gio; 6 gio): lenh dau o tick 14760 (cat cut -> 14759).
    (c) cua so [3 gio; 4,1 gio): lenh mo o tick 10800 (= 3 gio), TP o tick 14759 con TRONG cua so (14759 < 14760) -> mo lai ngay o tick 14759 (cat cut -> khong mo lai)."""
    diem = [1.0, 0.9963] + [0.9963, 0.99631] * 8000
    r = chay_tk(exe, tk_tay(diem, 0.0), dict(LUOI_TAY, InpCutPips=22.0, InpRestHours=4.1))
    assert list(bang(r).tick_mo) == [0, 100, 200, 300, 15130] and float(bang(r).open[4]) == pytest.approx(0.9963)
    dao = np.where(np.arange(15200) % 2 == 0, 1.0, 1.00001)
    r = chay_tk(exe, tk_chuoi(dao, t0=NGAY0), dict(LUOI_TAY, InpHourFrom=4.1, InpHourTo=6.0))
    assert list(bang(r).tick_mo) == [14760]
    bid = dao.copy()
    bid[14759:] = 1.0001                                                # TP 1 pip tu 1,0000 (lenh mo o tick chan 10800)
    r = chay_tk(exe, tk_chuoi(bid, t0=NGAY0), dict(LUOI_TAY, InpTpPips=1, InpHourFrom=3.0, InpHourTo=4.1))
    t = bang(r)
    assert list(t.tick_mo) == [10800, 14759] and t.tick_dong[0] == 14759 and list(t.ly_do) == ["tp", "open"]


#: (tham so luoi.ThamSo, input EA, gia tri SAI): hai ben phai tu choi y het nhau (`luoi.mien_duong_di` la MOT nguon cho Python lan nhan C; EA phai theo).
MIEN_TINH_NANG_SAI = [("cat_lo_pip", "InpCutPips", -0.5), ("cat_lo_tien", "InpCutMoney", -0.5), ("thoat_gio", "InpExitHours", -1.0),
                      ("thoat_gio", "InpExitHours", 1e6 + 1), ("nghi_gio", "InpRestHours", -1.0), ("nghi_gio", "InpRestHours", 1e6 + 1),
                      ("gio_vao_tu", "InpHourFrom", -0.1), ("gio_vao_tu", "InpHourFrom", 24.5),
                      ("gio_vao_den", "InpHourTo", -0.1), ("gio_vao_den", "InpHourTo", 24.5)]
#: ... va nhung gia tri BIEN hop le (khong duoc tu choi nham): 1.000.000 gio la tran, [0, 24] gom ca hai dau.
MIEN_TINH_NANG_DUNG = [dict(thoat_gio=1e6), dict(nghi_gio=1e6), dict(gio_vao_tu=0.0, gio_vao_den=24.0), dict(gio_vao_tu=24.0, gio_vao_den=24.0),
                       dict(gio_vao_tu=24.0, gio_vao_den=0.0), dict(cat_lo_pip=1e-9, cat_lo_tien=1e-9)]


@can_cxx
def test_khoi_dong_mien_tinh_nang_moi_khop_python(exe):
    """Cat lo / thoat gio / nghi / cua so gio: gia tri sai -> EA TU CHOI khoi dong, dung luc `luoi.mien_duong_di` tu choi; gia tri bien hop le -> ca hai chap nhan."""
    qc = L.QuyCach()
    tk = tk_tay([1.0, 0.999], 0.0002)
    for ten_ts, ten_in, v in MIEN_TINH_NANG_SAI:
        assert L.mien_duong_di(dataclasses.replace(CAU_HINH["mua_phang"], **{ten_ts: v}), qc), "Python chap nhan %s=%r" % (ten_ts, v)
        r = G.chay(exe, tk, 10000.0, {"InpPipSize": 1e-4, ten_in: v}, digits=5)
        assert not r["ok"] and r["kq"]["init_ok"] == 0.0 and r["kq"].get("n_mo", 0) == 0, "EA chap nhan %s=%r" % (ten_in, v)
    for cap in MIEN_TINH_NANG_DUNG:
        assert L.mien_duong_di(dataclasses.replace(CAU_HINH["mua_phang"], **cap), qc) == "", cap
        r = G.chay(exe, tk, 10000.0, dict({"InpPipSize": 1e-4}, **{G.BANG_TEN[k]: v for k, v in cap.items()}), digits=5)
        assert r["ok"], "EA tu choi nham %r: %s" % (cap, r["log"][-2:])


# ============================================================ 4. doi chieu NGAU NHIEN voi engine
SEED_DOI_CHIEU = range(200, 208)


@can_cxx
@pytest.mark.parametrize("mo_hinh", L.MO_HINH_BAR)
@pytest.mark.parametrize("ten", list(CAU_HINH))
def test_doi_chieu_voi_engine_tung_lenh_va_lai(exe, ten, mo_hinh):
    """Cung duong tick -> EA that va `luoi.chay` (moi tick la mot bar) phai mo / dong CUNG lenh o cung tick, cung lot, cung chieu,
    gia mo trong 2 buoc; lai chenh nhau chi do chenh gia giua hai tick (`lech_con_lai` = 0, tuc khong co khoan chi phi bi tinh khac).

    CA HAI mo hinh bar: tren bar suy bien (moi tick mot bar) `duong_di` phai tai lap EA tung lenh mot - day la phep kiem logic mo hinh moi
    voi mot cai cai dat doc lap (ma MQL5). Spread o lenh tia: `cuc_tri` tru hai lan (`phi_tia_kep`), `duong_di` mot lan nhu EA."""
    ts = dataclasses.replace(CAU_HINH[ten], khop_bar=mo_hinh)
    so_lenh = n_tia = n_ea = n_tp = 0
    for sd in SEED_DOI_CHIEU:
        r = G.doi_chieu(exe, ts, bars(150, sd), thu_tu=THU_TU[sd % 4], tol_tick=TOL_TICK.get(ten, 1))
        assert r.trang_thai == "khop", "%s seed %d (%s): %s" % (ten, sd, THU_TU[sd % 4], r.chi_tiet)
        assert abs(r.lech_con_lai) < 1e-6, "%s seed %d: lech lai %.6f, giai thich duoc %.6f" % (ten, sd, r.lech_lai, r.lech_explicada)
        assert r.kq_ea["init_ok"] == 1.0
        so_lenh += len(r.eng)
        n_tia += int((r.eng.ly_do == "tia").sum())
        n_tp += int((r.eng.ly_do == "tp").sum())
        n_ea += int((r.ea.ly_do == "ea").sum())
    assert so_lenh >= 25, "%s chi co %d lenh tren %d duong gia - bai kiem rong" % (ten, so_lenh, len(SEED_DOI_CHIEU))
    if ten in CO_TIA:
        assert n_tia >= 5, "%s: engine chi tia %d lenh - khong kiem duoc duong tia" % (ten, n_tia)
        assert n_ea >= n_tia
    if ten in CO_CHOT_TIEN:
        assert n_tp >= 5 and n_ea >= 10, "%s: duong chot tien khong chay (chot %d, EA tu dong %d)" % (ten, n_tp, n_ea)
    if ten not in CO_TIA | CO_CHOT_TIEN:
        assert n_ea == 0 and n_tia == 0 and n_tp > 10        # chi dong bang TP may chu


@can_cxx
@pytest.mark.parametrize("mo_hinh", L.MO_HINH_BAR)
def test_doi_chieu_hai_duong_gia_dac_biet(exe, mo_hinh):
    """Hai duong gia cuc doan: (a) day xuong lien tuc (khong TP nao) -> tang day, dung o tran; (b) giang bien rat hep quanh mot muc
    -> chi mo, khong tang. Engine va EA van khop lenh va lai."""
    xuong = pd.DataFrame(dict(open=np.round(1.0 - 0.0003 * np.arange(60), 5), high=np.round(1.0001 - 0.0003 * np.arange(60), 5),
                              low=np.round(0.9996 - 0.0003 * np.arange(60), 5), close=np.round(0.9997 - 0.0003 * np.arange(60), 5),
                              spread=20), index=pd.date_range("2024-01-01", periods=60, freq="15min"))
    r = G.doi_chieu(exe, dataclasses.replace(CAU_HINH["mua_phang"], khop_bar=mo_hinh), xuong)
    assert r.trang_thai == "khop" and abs(r.lech_con_lai) < 1e-6
    assert r.kq_ea["max_open"] == 5 and len(r.eng) == 5                                # tran_tang = 5, khong TP nao
    hep = pd.DataFrame(dict(open=0.9, high=0.90003, low=0.89997, close=0.9, spread=20),
                       index=pd.date_range("2024-01-01", periods=40, freq="15min"))
    r = G.doi_chieu(exe, dataclasses.replace(CAU_HINH["tn5"], khop_bar=mo_hinh), hep)
    assert r.trang_thai == "khop" and len(r.eng) == 2 and r.kq_ea["n_dong"] == 0       # hai ro (mua + ban), moi ro 1 lenh, khong tang 2


# ============================================================ 4b. doi chieu NGAU NHIEN cho TINH NANG MOI (08/10/2026)
#: 8 bo tinh nang x 12 cau hinh x 4 duong gia. Gio tick GIAY NGUYEN (`giay_tick=True`) de EA (TimeCurrent) va engine (cot thoi gian) thay CUNG gio tung tick; thu tu cao /
#: thap trong nen xoay theo seed. Cac bo: cat theo pip / theo tien / ca hai, thoat theo gio, nghi sau cat, cua so gio thuong / qua nua dem, tat ca cung luc.
TINH_NANG_MOI = {
    "cat_pip": dict(cat_lo_pip=12.0),
    "cat_tien": dict(cat_lo_tien=4.0),
    "cat_hai_nguong": dict(cat_lo_pip=25.0, cat_lo_tien=3.0),
    "thoat_gio": dict(thoat_gio=1.5),
    "cat_nghi": dict(cat_lo_pip=12.0, nghi_gio=0.75),
    "loc_gio": dict(gio_vao_tu=3.0, gio_vao_den=9.0),
    "loc_gio_qua_dem": dict(gio_vao_tu=22.0, gio_vao_den=4.0),
    "tat_ca": dict(cat_lo_pip=14.0, thoat_gio=2.0, nghi_gio=0.5, gio_vao_tu=1.0, gio_vao_den=20.0),
}
SEED_TINH_NANG = range(200, 204)
#: Tinh nang phai CO xay ra trong tung o, khong thi o do khong kiem gi (do 08/10/2026: muc thap nhat tren 12 cau hinh x 4 duong gia la 2 .. 77, chon nguong <= muc do).
#: `ro_cat` / `ro_gio` = so ro bi cat / thoat; `ro` = so ro co lenh dau; `nghi` = so cap (ro dong boi cat / thoat, ro ke tiep cung chieu); `ro_ngoai_neu_khong_loc` =
#: so ro SE mo ngoai cua so neu bo loc (cung duong gia): bo loc phai co viec de lam.
TOI_THIEU = {
    "cat_pip": dict(ro_cat=5), "cat_tien": dict(ro_cat=2), "cat_hai_nguong": dict(ro_cat=2), "thoat_gio": dict(ro_gio=20),
    "cat_nghi": dict(ro_cat=5, nghi=5), "loc_gio": dict(ro=5, ro_ngoai_neu_khong_loc=3), "loc_gio_qua_dem": dict(ro=5, ro_ngoai_neu_khong_loc=3),
    "tat_ca": dict(ro_gio=20, nghi=10, ro_ngoai_neu_khong_loc=3),
}


def _giay_ngay(t: pd.Series) -> np.ndarray:
    """Giay trong ngay [0, 86400) cua cot thoi gian nhat ky engine, lam tron XUONG giay (engine danh them micro-giay cho tick cung giay)."""
    return (t.dt.floor("s") - t.dt.floor("D")).dt.total_seconds().to_numpy()


def _trong_cua_so(sec: np.ndarray, tu: float, den: float) -> np.ndarray:
    """[tu, den) giay trong ngay; tu > den = qua nua dem; tu == den = khong loc."""
    if tu == den:
        return np.ones(len(sec), bool)
    return (sec >= tu) & (sec < den) if tu < den else (sec >= tu) | (sec < den)


def _bat_bien_tinh_nang(e: pd.DataFrame, thoat_s: float, nghi_s: float, tu_s: float, den_s: float) -> collections.Counter:
    """Bat bien DOC LAP voi so sanh EA <-> engine, chi doc nhat ky engine (da khop EA tung lenh), viet tu y nghia khai bao: (a) ro nao cung MO LENH DAU trong cua so gio;
    (b) ro dong boi THOAT GIO song >= thoat_gio; (c) cat / thoat dong CA ro cung mot giay; (d) ro ke tiep CUNG CHIEU mo sau cat / thoat >= nghi_gio. Tra dem cho `TOI_THIEU`."""
    dem = collections.Counter()
    w = e.assign(mo_s=e.mo.dt.floor("s"), dong_s=e.dong.dt.floor("s"))
    goc = w.groupby("ro").agg(mo=("mo_s", "min"), chieu=("chieu", "first"))
    dem["ro"] = len(goc)
    ngoai = ~_trong_cua_so(_giay_ngay(goc.mo), tu_s, den_s)
    assert not ngoai.any(), "ro mo NGOAI cua so gio [%g, %g): %s" % (tu_s, den_s, goc[ngoai].head(3).to_dict("index"))
    kt = w[w.ly_do.isin(["cat", "gio"])]
    assert (kt.groupby("ro").dong_s.nunique() <= 1).all(), "cat / thoat khong dong ca ro cung mot giay"
    gio = w[w.ly_do == "gio"]
    dem["ro_cat"] = w[w.ly_do == "cat"].ro.nunique()
    dem["ro_gio"] = gio.ro.nunique()
    if len(gio):
        tuoi = (gio.dong_s - goc.mo.reindex(gio.ro).to_numpy()).dt.total_seconds()
        assert (tuoi >= thoat_s).all(), "ro thoat gio khi chua du tuoi %g giay: %s" % (thoat_s, tuoi[tuoi < thoat_s].head(3).to_dict())
    if nghi_s > 0:
        dong_kt = kt.groupby("ro").dong_s.max()
        for _, g in goc.groupby("chieu"):
            ros = g.sort_index().index.to_list()
            for a, b in zip(ros[:-1], ros[1:]):
                if a in dong_kt.index:
                    dem["nghi"] += 1
                    khoang = (g.mo[b] - dong_kt[a]).total_seconds()
                    assert khoang >= nghi_s, "ro %d mo lai sau %g giay < nghi %g giay (ro %d cat / thoat luc %s)" % (b, khoang, nghi_s, a, dong_kt[a])
    return dem


def _ro_ngoai_neu_khong_loc(ts, df: pd.DataFrame, thu_tu: str, tu_s: float, den_s: float) -> int:
    """So ro se mo NGOAI cua so neu BO loc gio (cung duong gia, cung cau hinh con lai): cho thay bo loc co viec that, khong chi cua so rong bao quanh cac lenh."""
    qc = L.QuyCach(phi_nam_mua=0.0, phi_nam_ban=0.0)
    tk = G.tick_tu_bar(df, thu_tu, point=qc.point, paso=1e-6, giay_nguyen=True)
    kq = L.chay(G.barra_tu_tick(tk, point=qc.point), dataclasses.replace(ts, gio_vao_tu=0.0, gio_vao_den=0.0), 10000.0, qc=qc, ghi_lenh=True)
    goc = kq.lenh.assign(mo_s=kq.lenh.mo.dt.floor("s")).groupby("ro").mo_s.min()
    return int((~_trong_cua_so(_giay_ngay(goc), tu_s, den_s)).sum())


@can_cxx
@pytest.mark.parametrize("tn", list(TINH_NANG_MOI))
@pytest.mark.parametrize("ten", list(CAU_HINH))
def test_doi_chieu_tinh_nang_moi_voi_engine(exe, ten, tn):
    """12 cau hinh x 8 bo tinh nang moi x 4 duong gia: EA that khop `luoi.chay` TUNG LENH (chieu, lot, gia mo, tick mo / dong) va lai; so ro cat lo / thoat gio ma EA
    TU DEM (in o OnDeinit) bang so engine ghi; cac bat bien doc lap (`_bat_bien_tinh_nang`) dung tren nhat ky; va tinh nang CO xay ra (`TOI_THIEU`)."""
    ts = dataclasses.replace(CAU_HINH[ten], **TINH_NANG_MOI[tn])
    thoat_s, nghi_s, tu_s, den_s = L.cau_hinh_gio(ts)
    dem = collections.Counter()
    for sd in SEED_TINH_NANG:
        thu_tu, df = THU_TU[sd % 4], bars(150, sd)
        r = G.doi_chieu(exe, ts, df, thu_tu=thu_tu, giay_tick=True, tol_tick=TOL_TICK.get(ten, 1))
        assert r.trang_thai == "khop", "%s + %s seed %d (%s): %s" % (ten, tn, sd, thu_tu, r.chi_tiet)
        assert abs(r.lech_con_lai) < 1e-6, "%s + %s seed %d: lech lai %.6f, giai thich duoc %.6f" % (ten, tn, sd, r.lech_lai, r.lech_explicada)
        assert r.kq_ea["init_ok"] == 1.0
        d = _bat_bien_tinh_nang(r.eng, thoat_s, nghi_s, tu_s, den_s)
        assert _dem_ea(r.log_ea) == (d["ro_cat"], d["ro_gio"]), "%s + %s seed %d: EA tu dem %s, engine ghi %s" % (
            ten, tn, sd, _dem_ea(r.log_ea), (d["ro_cat"], d["ro_gio"]))
        dem.update(d)
        if tu_s != den_s:
            dem["ro_ngoai_neu_khong_loc"] += _ro_ngoai_neu_khong_loc(ts, df, thu_tu, tu_s, den_s)
    for khoa, toi_thieu in TOI_THIEU[tn].items():
        assert dem[khoa] >= toi_thieu, "%s + %s: %s = %d < %d tren %d duong gia - tinh nang khong xay ra du, bai kiem rong" % (
            ten, tn, khoa, dem[khoa], toi_thieu, len(SEED_TINH_NANG))


# ============================================================ 5. DOT BIEN: bo so sanh phai bao lech
def _lech(exe, ten, seeds=SEED_DOI_CHIEU, tn=None):
    """Cac duong gia (seed) ma EA `exe` KHAC engine o cau hinh `ten` (+ bo tinh nang moi `tn` neu co; khi do gio tick giay nguyen)."""
    ts = CAU_HINH[ten] if tn is None else dataclasses.replace(CAU_HINH[ten], **TINH_NANG_MOI[tn])
    out = []
    for sd in seeds:
        r = G.doi_chieu(exe, ts, bars(150, sd), thu_tu=THU_TU[sd % 4], tol_tick=TOL_TICK.get(ten, 1), giay_tick=tn is not None)
        if r.trang_thai != "khop" or abs(r.lech_con_lai) > 1e-6 or _dem_ea(r.log_ea) != (r.eng[r.eng.ly_do == "cat"].ro.nunique(),
                                                                                         r.eng[r.eng.ly_do == "gio"].ro.nunique()):
            out.append((sd, r.trang_thai))
    return out


DOT_BIEN = [
    ("tp_xa_hon", "tb + InpTpPips * g_pip : tb - InpTpPips * g_pip", "tb + (InpTpPips + 2.0) * g_pip : tb - (InpTpPips + 2.0) * g_pip",
     "mua_phang"),
    ("nguong_tia_cao_hon", "InpSparkPips * g_pip * lot_cap", "(InpSparkPips + 2.0) * g_pip * lot_cap", "tn5"),
    ("cho_lui_nguoc_huong", "g_cho[i] = g_tp_bid[i] - chieu * InpWaitBack * g_pip;", "g_cho[i] = g_tp_bid[i] + chieu * InpWaitBack * g_pip;",
     "cho_lui"),
    ("chot_tien_khong_nhan_lot", "InpTakeMoney * (InpLot / 0.01)", "InpTakeMoney", "chot_tien"),
    ("buoc_gian_lech_mot_tang", "BuocTang(g_tang[i] - 1) * g_pip", "BuocTang(g_tang[i]) * g_pip", "hai_nhan_buoc"),
    ("lot_cong_lech_mot_tang", "InpLot * (1.0 + InpLotMult * k)", "InpLot * (1.0 + InpLotMult * (k + 1))", "ban_cong"),
    ("tia_bo_qua_lenh_dau", "+ chieu * (bid - r.bid_dau) * r.lot_dau;", "+ 0.0;", "tn5"),
    ("tia_het_ro_mo_lai_cham_mot_tick", "g_cho[i] = 0.0;\n            MoRoMoi(loai);\n            return;",
     "g_cho[i] = 0.0;\n            return;", "tia_cho_lui"),
]


@can_cxx
@pytest.mark.parametrize("ten_dot,cu,moi,cau_hinh", DOT_BIEN, ids=[d[0] for d in DOT_BIEN])
def test_dot_bien_bo_so_sanh_bao_lech(tmp_path, ten_dot, cu, moi, cau_hinh):
    """Sua DUNG MOT cho trong ma EA (nguong tia, huong cho lui, he so lot...) roi chay lai bai doi chieu: it nhat mot duong gia
    phai ra khac engine. Neu mau dot bien khong con trong ma -> sua test (EA da doi chu)."""
    ma = EA_MQ5.read_text(encoding="utf-8")
    assert ma.count(cu) >= 1, "mau '%s' khong con trong ea_LuoiDayDu.mq5 - cap nhat DOT_BIEN" % cu
    p = tmp_path / "ea_dot_bien.mq5"
    p.write_text(ma.replace(cu, moi, 1), encoding="utf-8")
    exe_xau = G.bien_dich(p, thu_muc=tmp_path / "b")
    bao = _lech(exe_xau, cau_hinh)
    assert bao, "dot bien %s khong bi bat tren cau hinh %s (bo so sanh qua long)" % (ten_dot, cau_hinh)


@can_cxx
def test_dot_bien_khong_doi_gi_van_khop(tmp_path, exe):
    """Doi chung cho bai dot bien: ma KHONG sua (chi them mot dong chu thich) bien dich lai van khop - bao lech o tren la do cai sua."""
    ma = EA_MQ5.read_text(encoding="utf-8") + "\n// dong chu thich them\n"
    p = tmp_path / "ea_nguyen.mq5"
    p.write_text(ma, encoding="utf-8")
    exe2 = G.bien_dich(p, thu_muc=tmp_path / "b")
    assert exe2 != exe and _lech(exe2, "tn5") == []


# ============================================================ 5b. dot bien cho TINH NANG MOI: cat lo / thoat gio / nghi / cua so gio (08/10/2026)
#: Sua DUNG MOT cho trong `ea_LuoiDayDu.mq5`, bien dich lai, chay mot bai nhan dang: bai PHAI bao loi (AssertionError). 43 mau da duoc quet het truoc khi chot bang nay: 40 mau chet boi
#: bai tay duoi day, 3 song sot la TUONG DUONG (hai cho `ChamCat` sau tia cap khong bao gio dung - `test_cat_lo_ngay_sau_tia_cap_khong_bao_gio_xay_ra`). Nhom: cat lo (MocCat / ChamCat /
#: dem), thoat gio, nghi, cua so gio (hai dau nua khoang + qua nua dem + lam tron giay), kiem dau vao. Them mot co che moi vao EA -> them mau vao day.
_TAY = {
    "cat_pip": test_tay_cat_lo_pip_cat_ca_ro_o_trung_binh_tru_khoang_cat_roi_mo_lai_ngay,
    "cat_tien": test_tay_cat_lo_tien_dung_trung_binh_co_trong_so_theo_lot,
    "cat_tien_lot_goc": test_tay_cat_lo_tien_nhan_theo_lot_goc_cua_ea,
    "dung_sai": test_tay_cat_lo_dung_sai_nua_point_khi_moc_tinh_lech_mot_ulp,
    "hai_nguong": test_tay_hai_nguong_cat_nguong_nao_gan_trung_binh_hon_thang,
    "thoat_gio": test_tay_thoat_gio_dong_ro_o_tick_du_tuoi_dung_giay_roi_mo_lai,
    "thoat_le": test_tay_thoat_gio_le_4_1_gio_lam_tron_nua_len_den_giay,
    "nghi": test_tay_nghi_het_dung_giay_moi_mo_ro_moi,
    "nghi_sau_thoat": test_tay_nghi_bat_dau_ca_sau_thoat_gio_khong_chi_sau_cat,
    "cho_lui_sau_cat": test_tay_cat_va_thoat_gio_mo_lai_ngay_ke_ca_khi_co_cho_lui,
    "cho_lui_cua_so": test_tay_cho_lui_toi_muc_ngoai_cua_so_gio_giu_muc_cho_den_khi_cua_so_mo,
    "cua_so": test_tay_cua_so_gio_chi_chan_mo_ro_moi_o_hai_dau_nua_khoang,
    "qua_dem": test_tay_cua_so_gio_qua_nua_dem_hai_nhanh_va_ranh_gioi,
    "gio_le": test_tay_gio_le_4_1_lam_tron_nua_len_cho_ca_nghi_tu_va_den,
    "mien": test_khoi_dong_mien_tinh_nang_moi_khop_python,
    "ban_la_guong": test_tay_ban_la_guong_cua_mua,
}
DOT_BIEN_TN = [
    ("kc_pip_cong_1", "kc = InpCutPips * g_pip;", "kc = (InpCutPips + 1.0) * g_pip;", "cat_pip"),
    ("cat_tien_khong_nhan_lot", "const double k2 = InpCutMoney * (InpLot / 0.01) / (hd * r.lot);", "const double k2 = InpCutMoney / (hd * r.lot);", "cat_tien_lot_goc"),
    ("kc_lay_xa_hon", "if(k2 < kc)", "if(k2 > kc)", "hai_nguong"),
    ("moc_cat_sai_phia", "return tb - chieu * kc;", "return tb + chieu * kc;", "cat_pip"),
    ("tb_la_gia_tang_cuoi", "const double tb = r.sum_lg / r.lot;\n   double kc", "const double tb = r.bid_cuoi;\n   double kc", "cat_pip"),
    ("cat_khong_dung_sai", "return (chieu > 0.0) ? (bid <= moc + 0.5 * _Point) : (bid >= moc - 0.5 * _Point);", "return (chieu > 0.0) ? (bid <= moc) : (bid >= moc);", "dung_sai"),
    ("cat_can_ca_hai_nguong", "if((InpCutPips <= 0.0 && InpCutMoney <= 0.0) ||", "if((InpCutPips <= 0.0 || InpCutMoney <= 0.0) ||", "cat_pip"),
    ("cat_khong_nhan_tien_theo_tong_lot", "InpCutMoney * (InpLot / 0.01) / (hd * r.lot)", "InpCutMoney * (InpLot / 0.01) / (hd * 0.01)", "cat_tien"),
    ("thoat_gio_lon_hon_han", "(double)(TimeCurrent() - g_t_mo[i]) >= g_exit_s", "(double)(TimeCurrent() - g_t_mo[i]) > g_exit_s", "thoat_gio"),
    ("t_mo_khong_cap_nhat", "g_t_mo[i] = TimeCurrent();\n   SRo r;", "g_t_mo[i] = g_t_mo[i];\n   SRo r;", "thoat_gio"),
    ("thoat_gio_khong_mo_lai_ngay", "if(DongRoVaNghi(loai, 3))\n         MoRoMoi(loai);", "DongRoVaNghi(loai, 3);", "thoat_gio"),
    ("thoat_gio_khong_tinh_khi_tat", "if(g_exit_s > 0.0 &&", "if(g_exit_s >= 0.0 &&", "ban_la_guong"),
    ("cat_khong_mo_lai_ngay", "   if(ChamCat(r, bid, chieu))\n     {\n      if(DongRoVaNghi(loai, 2))\n         MoRoMoi(loai);", "   if(ChamCat(r, bid, chieu))\n     {\n      DongRoVaNghi(loai, 2);", "cat_pip"),
    ("dem_cat_thanh_gio", "if(kieu == 2)", "if(kieu == 3)", "cat_pip"),
    ("nghi_nua", "g_nghi_den[i] = (datetime)((double)TimeCurrent() + g_rest_s);", "g_nghi_den[i] = (datetime)((double)TimeCurrent() + g_rest_s * 0.5);", "nghi"),
    ("nghi_bien_bao_gom", "if(g_nghi_den[i] != 0 && t < g_nghi_den[i])", "if(g_nghi_den[i] != 0 && t <= g_nghi_den[i])", "nghi"),
    ("nghi_khong_chan_ro_rong", "   else if(!CoTheMoRo(i))                         // ro rong khong cho lui: chi vao khi het nghi va trong cua so gio\n      return false;", "", "nghi"),
    ("nghi_khong_chan_cho_lui", "      if(!CoTheMoRo(i))                           // toi muc cho nhung dang nghi / ngoai cua so gio: giu muc cho, chua vao\n         return false;\n", "", "cho_lui_cua_so"),
    ("dong_ro_khong_ha_co", "   g_co[i] = false;\n   g_tang[i] = 0;\n   g_cho[i] = 0.0;\n   if(kieu == 2)", "   g_tang[i] = 0;\n   g_cho[i] = 0.0;\n   if(kieu == 2)", "cho_lui_sau_cat"),
    ("nghi_chi_sau_cat", "   if(g_rest_s > 0.0)\n      g_nghi_den[i]", "   if(g_rest_s > 0.0 && kieu == 2)\n      g_nghi_den[i]", "nghi_sau_thoat"),
    ("cua_so_bo_bien_duoi", "return (sec >= g_from_s && sec < g_to_s);", "return (sec > g_from_s && sec < g_to_s);", "cua_so"),
    ("cua_so_gom_bien_tren", "return (sec >= g_from_s && sec < g_to_s);", "return (sec >= g_from_s && sec <= g_to_s);", "cua_so"),
    ("cua_so_qua_dem_and", "return (sec >= g_from_s || sec < g_to_s);", "return (sec >= g_from_s && sec < g_to_s);", "qua_dem"),
    ("cua_so_qua_dem_bo_bien_duoi", "return (sec >= g_from_s || sec < g_to_s);", "return (sec > g_from_s || sec < g_to_s);", "qua_dem"),
    ("cua_so_qua_dem_gom_bien_tren", "return (sec >= g_from_s || sec < g_to_s);", "return (sec >= g_from_s || sec <= g_to_s);", "qua_dem"),
    ("cua_so_bo_qua_dem", "if(g_from_s != g_to_s)\n     {\n      const double td", "if(g_from_s < g_to_s)\n     {\n      const double td", "qua_dem"),
    ("giay_ngay_lech_1s", "const double sec = td - 86400.0 * MathFloor(td / 86400.0);", "const double sec = td - 86400.0 * MathFloor(td / 86400.0) - 1.0;", "cua_so"),
    ("thoat_khong_lam_tron", "g_exit_s = MathFloor(InpExitHours * 3600.0 + 0.5);", "g_exit_s = MathFloor(InpExitHours * 3600.0);", "thoat_le"),
    ("nghi_khong_lam_tron", "g_rest_s = MathFloor(InpRestHours * 3600.0 + 0.5);", "g_rest_s = MathFloor(InpRestHours * 3600.0);", "gio_le"),
    ("tu_khong_lam_tron", "g_from_s = MathFloor(InpHourFrom * 3600.0 + 0.5);", "g_from_s = MathFloor(InpHourFrom * 3600.0);", "gio_le"),
    ("den_khong_lam_tron", "g_to_s   = MathFloor(InpHourTo * 3600.0 + 0.5);", "g_to_s   = MathFloor(InpHourTo * 3600.0);", "gio_le"),
    ("lenh_dau_bo_qua_cua_so", "   else if(!CoTheMoRo(i))", "   else if(false)", "cua_so"),
    ("bo_kiem_cat_pip_am", "if(InpCutPips < 0.0 || InpCutMoney < 0.0 ||", "if(InpCutMoney < 0.0 ||", "mien"),
    ("bo_kiem_cat_tien_am", "if(InpCutPips < 0.0 || InpCutMoney < 0.0 ||", "if(InpCutPips < 0.0 ||", "mien"),
    ("bo_kiem_thoat_gio_tran", "InpExitHours > 1.0e6 ||", "", "mien"),
    ("bo_kiem_nghi_tran", "InpRestHours > 1.0e6 ||", "", "mien"),
    ("kiem_gio_tu_24_5", "InpHourFrom > 24.0", "InpHourFrom > 25.0", "mien"),
    ("kiem_gio_den_am", "InpHourTo < 0.0 ||", "", "mien"),
    ("kiem_gio_tu_chat_hon", "InpHourFrom > 24.0", "InpHourFrom >= 24.0", "mien"),
    ("kiem_nghi_tran_chat_hon", "InpRestHours > 1.0e6", "InpRestHours >= 1.0e6", "mien"),
]


@can_cxx
@pytest.mark.parametrize("ten_dot,cu,moi,bai", DOT_BIEN_TN, ids=[d[0] for d in DOT_BIEN_TN])
def test_dot_bien_tinh_nang_moi_bi_bai_tay_bat(tmp_path, ten_dot, cu, moi, bai):
    """Moi dot bien ma EA (cat lo, thoat gio, nghi, cua so gio, kiem dau vao) phai lam rot DUNG bai tay da ghi (AssertionError). Mau khong con xuat hien dung MOT lan -> EA da doi chu,
    cap nhat DOT_BIEN_TN (khong bo mau)."""
    ma = EA_MQ5.read_text(encoding="utf-8")
    assert ma.count(cu) == 1, "mau '%s' khong con dung mot lan trong ea_LuoiDayDu.mq5 - cap nhat DOT_BIEN_TN" % ten_dot
    p = tmp_path / "ea_dot_bien.mq5"
    p.write_text(ma.replace(cu, moi, 1), encoding="utf-8")
    exe_dot = G.bien_dich(p, thu_muc=tmp_path / "b")
    with pytest.raises(AssertionError):
        _TAY[bai](exe_dot)


#: Hai cho `ChamCat` SAU tia cap trong `XuLy` (trong vong tia va ngay sau vong) la ma phong ve: bo hai lenh dau / cuoi khong bao gio doi ro con lai thanh ro bi cat ngay o gia tia
#: (bo de trong `luoi._mot_ro_duong`: moc cat moi A' - K' < q_cuoi < gia tia, vi A' < A truoc khi mo tang cuoi va K' >= K). Test dung EA CO DAT BIEN BAO (in `LDD_DEAD_TIA_*` thay vi cat)
#: va chay nhieu duong gia ngau nhien voi cat lo pip / tien / ca hai: bien bao phai KHONG BAO GIO in. Doi chung: cung ma nhung dieu kien luon dung -> bien bao PHAI in (khong thi
#: test mu). Ba dot bien xoa/sua hai cho nay song sot vi tuong duong; neu sau nay buoc luoi (ATR, buoc dong) hoac lenh tia (TP theo lenh) lam bo de sai, test nay do truoc.
_CHO_CAT_TIA = (
    ("         if(ChamCat(r, bid, chieu))               // bo hai lenh dau / cuoi doi trung binh: ro con lai da vuot moc cat -> thoat vong tia\n            break;\n",
     "         if(r.n > 0)\n            Print(\"LDD_TIA_KIEM_VONG\");\n         if(%s)\n           {\n            Print(\"LDD_DEAD_TIA_VONG\");\n            break;\n           }\n"),
    ("         if(ChamCat(r, bid, chieu))\n           {\n            if(DongRoVaNghi(loai, 2))\n               MoRoMoi(loai);\n            return;\n           }\n         DatTP(loai, r);",
     "         Print(\"LDD_TIA_KIEM_SAU\");\n         if(%s)\n           {\n            Print(\"LDD_DEAD_TIA_SAU\");\n            if(DongRoVaNghi(loai, 2))\n               MoRoMoi(loai);\n            return;\n           }\n         DatTP(loai, r);"),
)
CAT_DO_TIA = (dict(cat_lo_pip=30.0), dict(cat_lo_pip=45.0, cat_lo_tien=10.0), dict(cat_lo_tien=8.0))     # cat du chat de ro co >= 3 tang van bi cat, du long de con tia


def _exe_bien_bao_tia(tmp_path, dieu_kien: str, ten: str):
    ma = EA_MQ5.read_text(encoding="utf-8")
    for cu, moi in _CHO_CAT_TIA:
        assert ma.count(cu) == 1, "cho ChamCat sau tia khong con trong ea_LuoiDayDu.mq5 - cap nhat _CHO_CAT_TIA"
        ma = ma.replace(cu, moi % dieu_kien, 1)
    p = tmp_path / ("ea_%s.mq5" % ten)
    p.write_text(ma, encoding="utf-8")
    return G.bien_dich(p, thu_muc=tmp_path / ("b_" + ten))


def _chay_do_tia(exe, ten: str, cat: dict, sd: int):
    ts = dataclasses.replace(CAU_HINH[ten], **cat)
    return G.doi_chieu(exe, ts, bars(300, sd, rng_max=(8, 14, 20)[sd % 3]), thu_tu=THU_TU[sd % 4], tol_tick=TOL_TICK.get(ten, 1), giay_tick=False)


@can_cxx
@pytest.mark.cham
def test_cat_lo_ngay_sau_tia_cap_khong_bao_gio_xay_ra(tmp_path):
    """Doi chung truoc (dieu kien `true`: `LDD_DEAD_TIA_VONG` / `_SAU` PHAI in, neu khong dong in khong vao log va test mu), roi 96 duong gia (4 cau hinh tia x 3 kieu cat x 8 hat):
    moi lan tia cap de lai ro khong rong (`LDD_TIA_KIEM_SAU`) EA kiem cat lai - khong lan nao ra ket qua 'cat' (`LDD_DEAD_TIA_*` khong bao gio in). Do 08/10 tren 1440 duong: ~750 lan kiem, 0 lan cat."""
    ctrl = _exe_bien_bao_tia(tmp_path, "true", "doi_chung")
    log = "\n".join(_chay_do_tia(ctrl, "chot_tien_tia", dict(cat_lo_pip=80.0), 300).log_ea)
    assert "LDD_DEAD_TIA_VONG" in log and "LDD_DEAD_TIA_SAU" in log, "doi chung: bien bao khong in du khi dieu kien luon dung (hai cho khong chay toi, hoac dong in khong vao log)"
    exe_do = _exe_bien_bao_tia(tmp_path, "ChamCat(r, bid, chieu)", "do")
    n_kiem = 0
    for ten in sorted(CO_TIA):
        for cat in CAT_DO_TIA:
            for sd in range(300, 308):
                r = _chay_do_tia(exe_do, ten, cat, sd)
                assert r.trang_thai == "khop", (ten, cat, sd, r.trang_thai)
                log = "\n".join(r.log_ea)
                assert "LDD_DEAD_TIA" not in log, "cat lo ngay sau tia cap da XAY RA (%s, %s, hat %d): bo de 'khong bao gio' sai - engine can kiem cat sau tia" % (ten, cat, sd)
                n_kiem += log.count("LDD_TIA_KIEM_SAU")
    assert n_kiem >= 30, "qua it lan tia de lai ro khong rong de ket luan (%d)" % n_kiem


# ============================================================ 6. khoang cach mo hinh BAR (engine) <-> TICK (EA): task #48
#: Bar M15 gia lap co bien do that (~7 pip), 4 chuoi x 1500 bar. EA chay tren tick sinh tu CHINH cac bar do (`G.do_lech_bar`), engine chay tren bar.
#: `PASO_DO` = 1e-6 (= 0,1 point): voi 1e-5 moi tick bi ep ve luoi point, them vai % nhieu luong tu o cau hinh tia / chot tien. Bang day du:
#: `python test_ea_luoi_day_du.py --bang --paso 1e-6` (hoac `reports/lech_engine_EURCAD.md` muc 2). Moi ca chay ~1,7 giay -> danh dau `cham`.
PASO_DO = 1e-6
_BAR_THAT = [bars_that(seed=sd) for sd in range(1, 5)]
#: Cau hinh cua test 'khop theo nen' (moi cau hinh 4 chuoi x 1 thu tu ~7 giay). Bo `ban_cong` / `hai_nhan_buoc` / `buoc_thu`: cuc_tri va duong_di cho
#: CUNG so o do (bang trong bao cao) nen khong phan biet duoc hai mo hinh; van co mat o test 'moi thu tu duong gia' ben duoi.
_CH_KHOP_THEO_NEN = ["tn5", "mua_phang", "chot_tien", "chot_tien_tia", "cho_lui", "tia_cho_lui", "chot_tien_cho_lui", "chot_tien_tia_cho_lui", "buoc_co"]
_THU_TU_KHAC = tuple(t for t in THU_TU if t != "theo_nen")


def lai_engine_va_ea(exe, ten, mo_hinh, thu_tu=("theo_nen",), hat=range(4), paso=PASO_DO):
    """-> {thu_tu: (lai engine, lai EA)} cong qua cac chuoi bar `_BAR_THAT[i] for i in hat` (don vi bao gia, tru phi lenh con mo)."""
    ts = dataclasses.replace(CAU_HINH[ten], khop_bar=mo_hinh)
    tong = {tt: [0.0, 0.0] for tt in thu_tu}
    for i in hat:
        for x in G.do_lech_bar(exe, ts, _BAR_THAT[i], thu_tu=thu_tu, paso=paso):
            tong[x["thu_tu"]][0] += x["lai_engine"]
            tong[x["thu_tu"]][1] += x["lai_ea"]
    return {tt: (v[0], v[1]) for tt, v in tong.items()}


@can_cxx
@pytest.mark.cham
@pytest.mark.parametrize("ten,tran_lech", [("tn5", 1.08), ("chot_tien", 1.20), ("chot_tien_tia", 1.20), ("cho_lui", 1.20)])
def test_cuc_tri_van_lac_quan_so_voi_ea_tick(exe, ten, tran_lech):
    """BANG CHUNG cua chan doan 08/10/2026 (khong phai loi EA): mo hinh bar CU `cuc_tri` dong cap tia / chot tien o gia TOT NHAT cua bar va
    luon xu ly bat loi truoc, nen cao hon EA chay tren tick cua CHINH cac bar do: tn5 +15%, chot_tien +37%, chot_tien_tia +37%, cho_lui
    +26% (do 08/10, paso 1e-6, thu tu duong gia 'theo_nen' = cung gia dinh mau nen voi `duong_di`; chot_tien_tia_cho_lui toi +55%).
    Giu lai de khong ai quen vi sao `duong_di` ra doi."""
    e, a = lai_engine_va_ea(exe, ten, "cuc_tri")["theo_nen"]
    assert a > 0 and e > a * tran_lech, "%s: cuc_tri %.1f, EA %.1f - mo hinh cu KHONG con lac quan nhu da do" % (ten, e, a)


@can_cxx
@pytest.mark.cham
@pytest.mark.parametrize("ten", _CH_KHOP_THEO_NEN)
def test_duong_di_khop_ea_tick_cung_thu_tu_duong_gia(exe, ten):
    """`duong_di` (mac dinh) tren bar so voi EA chay tren tick sinh tu CHINH cac bar do theo CUNG thu tu duong gia (nen xanh: thap -> cao,
    nen do: cao -> thap): lai lech < 6% o moi cau hinh (do 08/10/2026, paso 1e-6, 4 chuoi: +3,1% mua_phang, +0,2% tn5, -0,1% chot_tien,
    +2,1% chot_tien_tia, -3,0% cho_lui, -3,0% tia_cho_lui, -4,5% chot_tien_cho_lui, -2,3% chot_tien_tia_cho_lui, -3,9% buoc_co), trong khi
    `cuc_tri` lech +15% .. +55% (test tren). Phan con lai la do KHONG BIET thu tu cao / thap that trong nen, khong phai sai so mo hinh - xem
    `reports/lech_engine_EURCAD.md`. Cong 2,0 (don vi bao gia) cho cau hinh lai nho."""
    e, a = lai_engine_va_ea(exe, ten, "duong_di")["theo_nen"]
    assert a > 0 and abs(e - a) < 0.06 * a + 2.0, "%s: duong_di %.1f, EA %.1f (%+.1f%%)" % (ten, e, a, 100.0 * (e - a) / a)


@can_cxx
@pytest.mark.cham
@pytest.mark.parametrize("ten", list(CAU_HINH))
def test_duong_di_khong_lac_quan_voi_bat_ky_thu_tu_cao_thap_trong_nen(exe, ten):
    """Tinh chat QUAN TRONG NHAT cua mo hinh cong bang: voi MOI thu tu duong gia (thap truoc / cao truoc / xen ke) engine khong duoc cao hon EA tick
    qua 6% - cai da thoi phong ket qua luoi 15-55% truoc 08/10 la su LAC QUAN, con than trong thi chi mat co hoi. Do (08/10, paso 1e-6, chuoi 1): lech cao
    nhat +3,3% (chot_tien_tia); cac cau hinh 'cho lui / buoc gian' than trong hon EA tren nhieu thu tu (cho_lui -39,5%, tia_cho_lui -26%, buoc_co
    -14%, ban_cong -4%: lech THAT khi thu tu cao / thap la bat dinh - bang day du trong bao cao). Chan duoi -45% chi de bat loi engine bo lenh bua bai."""
    r = lai_engine_va_ea(exe, ten, "duong_di", thu_tu=_THU_TU_KHAC, hat=[0])
    for tt, (e, a) in r.items():
        assert a > 0, "%s/%s: EA khong lai (%.1f) - chuoi thu khong con y nghia" % (ten, tt, a)
        assert e - a < 0.06 * a + 2.0, "%s/%s: engine LAC QUAN %.1f so voi EA %.1f (%+.1f%%)" % (ten, tt, e, a, 100.0 * (e - a) / a)
        assert e - a > -0.45 * a - 2.0, "%s/%s: engine qua than trong %.1f so voi EA %.1f (%+.1f%%)" % (ten, tt, e, a, 100.0 * (e - a) / a)


# ============================================================ bang day du: python test_ea_luoi_day_du.py --bang --paso 1e-6
def _o_bang(r: dict) -> str:
    return " / ".join("%+.1f" % (100.0 * (r[tt][0] - r[tt][1]) / abs(r[tt][1]) if r[tt][1] else float("nan")) for tt in THU_TU)


def in_bang(paso: float, hat: list[int], cau_hinh: list[str], mo_hinh: list[str]) -> list[str]:
    """Bang markdown 'lai engine lech bao nhieu % so voi lai EA tick' (am = engine than trong hon EA), moi mo hinh bar mot cot, 4 thu tu duong gia
    trong nen: theo nen / thap truoc / cao truoc / xen ke. Cot dau = lai cua EA (theo nen) cong qua cac chuoi, don vi bao gia."""
    import tempfile
    exe = G.bien_dich(EA_MQ5, thu_muc=Path(tempfile.mkdtemp(prefix="ea_gia_lap_exe_")))
    dong = ["| cau hinh | EA lai (theo nen) | " + " | ".join("`%s`: theo nen / thap truoc / cao truoc / xen ke" % m for m in mo_hinh) + " |",
            "|---|---:|" + "---|" * len(mo_hinh)]
    print("\n".join(dong), flush=True)
    for ten in cau_hinh:
        kq = {m: lai_engine_va_ea(exe, ten, m, thu_tu=THU_TU, hat=hat, paso=paso) for m in mo_hinh}
        a0 = kq[mo_hinh[0]]["theo_nen"][1]
        dong.append("| %s | %+.0f | " % (ten, a0) + " | ".join(_o_bang(kq[m]) for m in mo_hinh) + " |")
        print(dong[-1], flush=True)
    return dong


if __name__ == "__main__":
    import argparse
    import shutil
    import sys
    ap = argparse.ArgumentParser(description="In bang lech engine <-> EA tick (muc 6): lai engine so voi lai EA, 4 thu tu duong gia trong nen")
    ap.add_argument("--bang", action="store_true", help="bat buoc: in bang (khong chay pytest)")
    ap.add_argument("--paso", type=float, default=PASO_DO, help="buoc tick, don vi GIA (uoc nguyen cua point 1e-5; mac dinh %g)" % PASO_DO)
    ap.add_argument("--hat", default="1,2,3,4", help="cac chuoi bar (seed) cua `bars_that`, cach nhau bang phay (mac dinh 1,2,3,4 = bang trong bao cao)")
    ap.add_argument("--cau-hinh", default="", help="cac cau hinh cua CAU_HINH cach nhau bang phay (mac dinh: tat ca)")
    ap.add_argument("--mo-hinh", default=",".join(L.MO_HINH_BAR), help="mo hinh bar (mac dinh %s)" % ",".join(L.MO_HINH_BAR))
    a = ap.parse_args()
    if not a.bang:
        ap.error("chay pytest de chay test; them --bang de in bang")
    if G.trinh_bien_dich() is None:
        sys.exit("khong co g++ / clang++ (hoac EA_GIA_LAP_CXX)")
    seeds = [int(x) for x in a.hat.split(",") if x.strip()]
    if not seeds or any(not 1 <= x <= len(_BAR_THAT) for x in seeds):
        sys.exit("--hat chi nhan 1..%d" % len(_BAR_THAT))
    ten_ch = [x for x in a.cau_hinh.split(",") if x.strip()] or list(CAU_HINH)
    sai = [x for x in ten_ch if x not in CAU_HINH]
    mh = [x for x in a.mo_hinh.split(",") if x.strip()]
    sai_mh = [x for x in mh if x not in L.MO_HINH_BAR]
    if sai or sai_mh or not mh:
        sys.exit("khong co cau hinh %s / mo hinh %s (cau hinh: %s; mo hinh: %s)" % (sai or "-", sai_mh or "-", ",".join(CAU_HINH), ",".join(L.MO_HINH_BAR)))
    in_bang(a.paso, [x - 1 for x in seeds], ten_ch, mh)
