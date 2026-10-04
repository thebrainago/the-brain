# -*- coding: utf-8 -*-
"""ea_LuoiDayDu.mq5 - chay CHINH van ban .mq5 tren SAN GIA (`nhan/ea_gia_lap`), khong phai ban port tay.

Sau lop kiem, tu re den dat. Khong lop nao thay duoc tester MT5 that (cu phap rieng cua MQL5, tick that, spread doi, swap -
`tai_lieu/LAN_EA_THO.md`, 5 diem chua hieu chuan): cai kiem duoc o day la LOGIC file .mq5 co dung y khai bao `luoi.ThamSo` khong.
  1. Bang ten ThamSo <-> input, tham so, bo property (khong can trinh bien dich).
  2. Cu phap: bien dich nghiem (-Wall, input la const), loi tro dung dong .mq5.
  3. KICH BAN TAY: duong gia dung bang tay, so tien tinh tay TRUOC roi moi so voi san gia (khong chep dau ra cua san gia).
  4. DOI CHIEU NGAU NHIEN voi `luoi.chay` tren CUNG duong gia tick: 12 cau hinh x nhieu duong gia, khop TUNG LENH (chieu, lot,
     gia mo, tick mo / dong) va LAI sau hai khoan da biet (`KetQuaDoiChieu`) - phan lech con lai phai bang 0.
  5. DOT BIEN: sua ma EA co chu dich -> bo so sanh PHAI bao lech (bo so sanh co rang, khong gat dau cho moi thu).
  6. Do khoang cach mo hinh bar OHLC (engine) <-> tick (EA), `test_engine_lac_quan_...` - dau hieu cho task #48.
"""
from __future__ import annotations

import dataclasses
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


# ============================================================ 4. doi chieu NGAU NHIEN voi engine
SEED_DOI_CHIEU = range(200, 208)


@can_cxx
@pytest.mark.parametrize("ten", list(CAU_HINH))
def test_doi_chieu_voi_engine_tung_lenh_va_lai(exe, ten):
    """Cung duong tick -> EA that va `luoi.chay` (moi tick la mot bar) phai mo / dong CUNG lenh o cung tick, cung lot, cung chieu,
    gia mo trong 2 buoc; lai chenh nhau chi do chenh gia giua hai tick (`lech_con_lai` = 0, tuc khong co khoan chi phi bi tinh khac)."""
    ts = CAU_HINH[ten]
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
def test_doi_chieu_hai_duong_gia_dac_biet(exe):
    """Hai duong gia cuc doan: (a) day xuong lien tuc (khong TP nao) -> tang day, dung o tran; (b) giang bien rat hep quanh mot muc
    -> chi mo, khong tang. Engine va EA van khop lenh va lai."""
    xuong = pd.DataFrame(dict(open=np.round(1.0 - 0.0003 * np.arange(60), 5), high=np.round(1.0001 - 0.0003 * np.arange(60), 5),
                              low=np.round(0.9996 - 0.0003 * np.arange(60), 5), close=np.round(0.9997 - 0.0003 * np.arange(60), 5),
                              spread=20), index=pd.date_range("2024-01-01", periods=60, freq="15min"))
    r = G.doi_chieu(exe, CAU_HINH["mua_phang"], xuong)
    assert r.trang_thai == "khop" and abs(r.lech_con_lai) < 1e-6
    assert r.kq_ea["max_open"] == 5 and len(r.eng) == 5                                # tran_tang = 5, khong TP nao
    hep = pd.DataFrame(dict(open=0.9, high=0.90003, low=0.89997, close=0.9, spread=20),
                       index=pd.date_range("2024-01-01", periods=40, freq="15min"))
    r = G.doi_chieu(exe, CAU_HINH["tn5"], hep)
    assert r.trang_thai == "khop" and len(r.eng) == 2 and r.kq_ea["n_dong"] == 0       # hai ro (mua + ban), moi ro 1 lenh, khong tang 2


# ============================================================ 5. DOT BIEN: bo so sanh phai bao lech
def _lech(exe, ten, seeds=SEED_DOI_CHIEU):
    ts = CAU_HINH[ten]
    out = []
    for sd in seeds:
        r = G.doi_chieu(exe, ts, bars(150, sd), thu_tu=THU_TU[sd % 4], tol_tick=TOL_TICK.get(ten, 1))
        if r.trang_thai != "khop" or abs(r.lech_con_lai) > 1e-6:
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


# ============================================================ 6. khoang cach mo hinh BAR (engine) <-> TICK (EA): task #48
@can_cxx
def test_engine_lac_quan_voi_tia_lenh_khi_chay_tren_bar_ohlc(exe):
    """KHONG phai loi cua EA: engine chay tren bar OHLC dong cap tia / chot tien o gia TOT NHAT cua bar (cao nhat voi lenh mua) va tru
    spread HAI lan cho lenh tia, EA tick dong o gia vua cham nguong. Tren nen M15 gia lap co bien do that (~7 pip), tn5 cua engine cao hon
    EA ~15% (do 04/10/2026: +16,4% / +16,3% / +14,7% theo ba thu tu duong gia), con luoi thuan (mua_phang) chi lech +-5%.
    Test nay GHIM so do: khi sua engine (task #48) no se doi mau - cap nhat khi do, khong xoa."""
    df = [bars_that(seed=s) for s in range(1, 5)]
    def gop(ten, thu):
        e = a = 0.0
        for d in df:
            x = G.do_lech_bar(exe, CAU_HINH[ten], d, thu_tu=thu, paso=1e-5)[0]
            e += x["lai_engine"]
            a += x["lai_ea"]
        return e, a
    e, a = gop("tn5", "theo_nen")
    assert e > a * 1.08 > 0, "tn5: engine %.1f EA %.1f - mo hinh bar KHONG con lac quan hon EA (da sua #48? cap nhat test + tai lieu)" % (e, a)
    e, a = gop("mua_phang", "theo_nen")
    assert a > 0 and abs(e - a) < 0.08 * abs(a) + 5.0, "luoi thuan: engine %.1f EA %.1f" % (e, a)
