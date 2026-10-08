# -*- coding: utf-8 -*-
"""Nhan C cua engine luoi (`nhan/luoi_nhan.py` + `nhan/luoi_nhan.c`) - 03/10/2026.

Chu du an hoi cach tang toc do test. `luoi._mot_ro` ~3 us/bar; ban C ~0,02 us/bar (x130) va nha GIL. Cai gia: mot ban sao thu hai cua
logic engine -> co the LECH im lang. Test nay la hang rao:

  1. KHOP: hang tram kich ban ngau nhien (moi tinh nang: nhan/cong lot, gian dan, cho lui, tia lenh, chot tien, tran tang; ca hai
     chieu; cap JPY; chuoi rat ngan; NaN/inf) - lai, treo, thong ke, CHUOI LENH phai trung khit (tung bit tren Linux).
  2. DU PHONG: moi truong hop nhan C khong dam bao -> tra None de Python lo (che do py, mang khong phai float64, tham so ngoai mien,
     np.float32, tran so luy thua, khong co trinh bien dich, tu kiem that bai).
  3. CHONG TROI: quet nguon `_mot_ro`; them truong `ts.xxx` / `qc.xxx` vao engine ma quen nhan C thi test do.
  4. HIEU NANG + DA LUONG: nhanh hon Python it nhat 10 lan; chay song song cho ket qua giong tuan tu.

HAI MO HINH BAR (08/10/2026): `ThamSo.khop_bar` = `cuc_tri` (cu) | `duong_di` (mac dinh moi). Moi test khop Python <-> C chay CA HAI;
`LU.mot_ro_chuan` la ban Python chuan cua mo hinh do (khong qua nhan C). Ngu nghia rieng cua `duong_di` (tay tinh, khong thien vi,
khong phu thuoc do phan giai) o `test_luoi_duong_di.py`.

Khong co trinh bien dich C trong may chay test -> cac test can nhan C duoc BO QUA (khong am tham xanh gia: xem
`test_nhan_san_sang_khi_co_trinh_bien_dich`).
"""
from __future__ import annotations

import dataclasses
import inspect
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import luoi as LU
from nhan import luoi_nhan as LN

LINUX = sys.platform.startswith("linux")
MO_HINH = LU.MO_HINH_BAR                                       # ("cuc_tri", "duong_di")
_CA_BIEN_MO_HINH = [(mh, ca) for mh, bang in (("cuc_tri", LN._CA_BIEN), ("duong_di", LN._CA_BIEN_DUONG)) for ca in bang]


# ------------------------------------------------------------------ TIEN ICH
@pytest.fixture(scope="module")
def nhan():
    if LN.che_do() == "py":
        pytest.skip("LUOI_NHAN=py")
    lib = LN.lay_nhan()
    if lib is None:
        pytest.skip("khong co nhan C: %s" % LN.trang_thai()["ly_do"])
    return lib


@pytest.fixture
def nhan_sach(monkeypatch, tmp_path):
    """Trang thai nap SACH + cache rieng trong tmp (dich that mot lan); tra lai nhu cu sau test."""
    if not LN._ung_vien_trinh_bien():
        pytest.skip("khong co trinh bien dich C")
    LN.lam_lai()
    monkeypatch.setenv("LUOI_NHAN_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("LUOI_NHAN", raising=False)
    yield tmp_path / "cache"
    LN.lam_lai()


def _kich_ban(rng, jpy: bool = False, mo_hinh: str = "duong_di"):
    """Chuoi gia + spread + qua dem + tham so ngau nhien (moi tinh nang bat tat rieng). `mo_hinh` KHONG tieu thu so ngau nhien:
    cung hat giong -> cung kich ban cho ca hai mo hinh."""
    n = int(rng.integers(40, 2500))
    s = 100.0 if jpy else 1.0
    kieu_gia = int(rng.integers(0, 3))
    vol = float(rng.uniform(1, 30)) * 1e-4 * s
    if kieu_gia == 0:
        x = np.cumsum(rng.normal(0, vol, n))
    elif kieu_gia == 1:                                    # hoi quy
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = 0.97 * x[i - 1] + rng.normal(0, vol)
    else:                                                   # xu huong + nhieu
        x = np.cumsum(rng.normal(vol * 0.15, vol, n))
    cl = (144.0 if jpy else 0.9) + x
    op = np.concatenate([[cl[0]], cl[:-1]])
    hi = np.maximum(op, cl) + np.abs(rng.normal(0, vol * 0.6, n))
    lo = np.minimum(op, cl) - np.abs(rng.normal(0, vol * 0.6, n))
    if rng.random() < 0.75:                                 # gia luoi 5 chu so: de va cham dung moc
        d = int(rng.choice([4, 5])) - (2 if jpy else 0)
        cl, hi, lo = np.round(cl, d), np.round(hi, d), np.round(lo, d)
    sp = np.full(n, 0.0001 * s) if rng.random() < 0.3 else np.round(rng.uniform(0.00003, 0.00025, n) * s, 5)
    dem = np.zeros(n)
    if rng.random() < 0.8:
        dem[int(rng.integers(5, 50))::int(rng.integers(20, 120))] = 1.0
        if rng.random() < 0.5:
            dem[int(rng.integers(100, 200))::int(rng.integers(100, 500))] = 3.0
    kw = dict(buoc=float(rng.uniform(3, 80)), tp=float(rng.uniform(2, 80)), tran_tang=int(rng.integers(1, 26)),
              lot=float(rng.choice([0.01, 0.02, 0.03, 0.07, 0.1, 0.5])))
    k = int(rng.integers(0, 3))
    if k == 1:
        kw.update(kieu_lot="nhan", he_so_lot=float(rng.uniform(0.6, 1.8)))
    elif k == 2:
        kw.update(kieu_lot="cong", he_so_lot=float(rng.uniform(0.1, 2.0)))
    if rng.random() < 0.35:
        kw.update(tia_lenh=True, bien_cap=float(rng.uniform(0.5, 10)), cap_moi_bar=int(rng.choice([1, 2, 3, 999])))
    if rng.random() < 0.3:
        kw.update(cho_lui=float(rng.uniform(1, 30)))
    if rng.random() < 0.25:
        kw.update(chot_tien=float(rng.uniform(0.5, 20)))
    if rng.random() < 0.3:
        kw.update(he_so_buoc=float(rng.uniform(0.7, 1.5)), buoc_tran=float(rng.uniform(20, 300)))
    ts = LU.ThamSo(**kw, khop_bar=mo_hinh)
    phi = dict(phi_nam_mua=float(rng.uniform(-0.05, 0.05)), phi_nam_ban=float(rng.uniform(-0.05, 0.05)))
    if jpy:
        qc = LU.QuyCach(ma="USDJPY", pip=1e-2, point=1e-3, **phi)
    elif rng.random() < 0.3:
        qc = LU.QuyCach(**phi)
    else:
        qc = LU.QC_AUDCAD
    return hi, lo, cl, sp, dem, ts, qc


def _py(hi, lo, cl, sp, dem, chieu, ts, qc):
    ev: list = []
    lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc, ev)
    return lai, treo, tk, ev


def _c(hi, lo, cl, sp, dem, chieu, ts, qc):
    ev: list = []
    r = LN.mot_ro(hi, lo, cl, sp, dem, chieu, ts, qc, ev)
    assert r is not None, "nhan C tra None cho %s" % (ts,)
    return r[0], r[1], r[2], ev


def _khop(a, b, ten: str = ""):
    """a = Python (chuan), b = nhan C. Dung sai 1e-9 o moi nen tang; TUNG BIT tren Linux (cung libm, cung co bien dich)."""
    ok, mo_ta = LN.so_sanh_ket_qua(a, b)
    assert ok, "%s: %s" % (ten, mo_ta)
    if LINUX:
        assert np.array_equal(a[0], b[0], equal_nan=True), "%s: lai khong khop tung bit" % ten
        assert np.array_equal(a[1], b[1], equal_nan=True), "%s: treo khong khop tung bit" % ten
        assert set(a[2]) == set(b[2])
        for k in a[2]:
            assert a[2][k] == b[2][k] or (a[2][k] != a[2][k] and b[2][k] != b[2][k]), "%s: %s" % (ten, k)
        assert a[3] == b[3], "%s: chuoi lenh khong khop tung bit" % ten


def _so_ngau_nhien(seed: int, so_ca: int = 8, jpy: bool = False, mo_hinh: str = "duong_di"):
    rng = np.random.default_rng(seed)
    for _ in range(so_ca):
        yield _kich_ban(rng, jpy, mo_hinh)


def _df(n: int = 6000, seed: int = 7, gia0: float = 0.95) -> pd.DataFrame:
    """OHLC + spread (POINT) tong hop hoi quy ve gia0 - cung kieu chuoi voi test_luoi_quy_cach."""
    rng = np.random.RandomState(seed)
    x = np.empty(n)
    x[0] = gia0
    for i in range(1, n):
        x[i] = x[i - 1] + 0.02 * (gia0 - x[i - 1]) + rng.normal(0, 4e-4)
    o = np.r_[x[0], x[:-1]]
    hi = np.maximum(o, x) + np.abs(rng.normal(0, 2e-4, n))
    lo = np.minimum(o, x) - np.abs(rng.normal(0, 2e-4, n))
    sp = np.where(rng.rand(n) < 0.02, 0, rng.randint(12, 40, n)).astype(float)
    idx = pd.date_range("2024-01-01", periods=n, freq="15min")
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": x, "spread": sp}, index=idx)


# ------------------------------------------------------------------ TRANG THAI
def test_nhan_san_sang_khi_co_trinh_bien_dich():
    """Co trinh bien dich ma nhan KHONG san sang = tu kiem hong hoac dich hong: khong duoc im lang chay Python roi bao xanh."""
    if LN.che_do() == "py":
        pytest.skip("LUOI_NHAN=py")
    if not LN._ung_vien_trinh_bien() and not list(LN._thu_muc_cache().glob("luoi_nhan_*")):
        pytest.skip("khong co trinh bien dich va khong co ban dich san")
    tt = LN.trang_thai()
    assert tt["san_sang"], tt["ly_do"]
    assert tt["python"] == sys.version.split()[0]
    assert tt["duong_dan"]


def test_kahan_theo_phien_ban_python():
    """Python >= 3.12 cong BU trong sum() tren float thuan; np.float64 / int thi cong tuan tu. Co nay quyet dinh cach cong cua C."""
    assert LN._kahan(LU.ThamSo(lot=0.01)) is (sys.version_info >= (3, 12))
    assert LN._kahan(LU.ThamSo(lot=np.float64(0.01))) is False
    assert LN._kahan(LU.ThamSo(lot=1)) is False
    assert LN._kahan(LU.ThamSo(lot=0.01, kieu_lot="nhan", he_so_lot=np.float64(1.2))) is False
    assert LN._kahan(LU.ThamSo(lot=0.01, kieu_lot="cong", he_so_lot=2)) is (sys.version_info >= (3, 12))


# ------------------------------------------------------------------ KHOP
@pytest.mark.parametrize("mo_hinh", MO_HINH)
@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5, 6])
def test_khop_tren_kich_ban_ngau_nhien(nhan, seed, mo_hinh):
    tong_lenh = 0
    for k, (hi, lo, cl, sp, dem, ts, qc) in enumerate(_so_ngau_nhien(seed, 8, mo_hinh=mo_hinh)):
        for chieu in (1, -1):
            a = _py(hi, lo, cl, sp, dem, chieu, ts, qc)
            b = _c(hi, lo, cl, sp, dem, chieu, ts, qc)
            _khop(a, b, "%s seed=%d ca=%d chieu=%+d %s" % (mo_hinh, seed, k, chieu, ts))
            tong_lenh += a[2]["so_lenh"]
    assert tong_lenh > 300, "kich ban qua thua - khong du tin cay"


@pytest.mark.parametrize("mo_hinh", MO_HINH)
@pytest.mark.parametrize("seed", [21, 22])
def test_khop_cap_jpy(nhan, seed, mo_hinh):
    """Hang so khac AUDCAD: pip 1e-2, gia ~144, phi qua dem hai chieu khac nhau."""
    for k, (hi, lo, cl, sp, dem, ts, qc) in enumerate(_so_ngau_nhien(seed, 6, jpy=True, mo_hinh=mo_hinh)):
        assert qc.pip == 1e-2
        for chieu in (1, -1):
            _khop(_py(hi, lo, cl, sp, dem, chieu, ts, qc), _c(hi, lo, cl, sp, dem, chieu, ts, qc),
                  "jpy %s seed=%d ca=%d chieu=%+d" % (mo_hinh, seed, k, chieu))


_CO_SO = dict(buoc=18.0, tp=12.0, tran_tang=9, tia_lenh=True, bien_cap=2.5, cap_moi_bar=2, cho_lui=5.0, he_so_buoc=1.1,
              buoc_tran=60.0)


@pytest.mark.parametrize("sua", [
    dict(lot=np.float64(0.02)),
    dict(lot=1),
    dict(lot=0.01, kieu_lot="nhan", he_so_lot=np.float64(1.25)),
    dict(lot=0.01, kieu_lot="nhan", he_so_lot=1),                      # he_so_lot nguyen = 1: luy thua luon 1
    dict(lot=0.01, kieu_lot="cong", he_so_lot=2),                      # he_so_lot nguyen, kieu cong: khong luy thua
    dict(lot=0.01, kieu_lot="cong", he_so_lot=np.float64(0.5)),
    dict(lot=np.float64(0.01), kieu_lot="cong", he_so_lot=1),
    dict(lot=0.01, kieu_lot="nhan", he_so_lot=1.3, he_so_buoc=np.float64(1.15)),
    dict(buoc=np.float64(18.0), tp=np.int64(12), tran_tang=np.int64(7)),
    dict(buoc=18, tp=12, tran_tang=7.0, cap_moi_bar=np.int64(2)),
    dict(he_so_buoc=1),                                                # he_so_buoc nguyen = 1
    dict(chot_tien=2.0, tia_lenh=False),
    dict(chot_tien=np.float64(3.0)),
])
@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_khop_khi_tham_so_la_kieu_so_khac(nhan, sua, mo_hinh):
    """Kieu so cua tham so (int / np.float64 / np.int64) doi cach Python cong `sum()` va luy thua: nhan C phai theo hoac tu choi."""
    hi, lo, cl, sp, dem = LN._kich_ban_tu_kiem()
    ts = LU.ThamSo(**dict(_CO_SO, **sua), khop_bar=mo_hinh)
    for chieu in (1, -1):
        r = LN.mot_ro(hi, lo, cl, sp, dem, chieu, ts, LU.QC_AUDCAD, [])
        if r is None:                      # tu choi cung la dap an dung (Python lo) - nhung phai LA chu y, khong phai loi
            assert not LN.kha_dung(ts, LU.QC_AUDCAD)
            continue
        _khop(_py(hi, lo, cl, sp, dem, chieu, ts, LU.QC_AUDCAD), _c(hi, lo, cl, sp, dem, chieu, ts, LU.QC_AUDCAD),
              "%s %s chieu=%+d" % (mo_hinh, sua, chieu))


@pytest.mark.parametrize("mo_hinh", MO_HINH)
@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_khop_chuoi_rat_ngan(nhan, n, mo_hinh):
    rng = np.random.default_rng(n)
    cl = np.round(0.9 + np.cumsum(rng.normal(0, 3e-3, n)), 5)
    hi, lo = cl + 4e-3, cl - 4e-3
    sp, dem = np.full(n, 1e-4), np.ones(n)
    ts = LU.ThamSo(buoc=5.0, tp=3.0, tran_tang=4, tia_lenh=True, bien_cap=0.5, khop_bar=mo_hinh)
    for chieu in (1, -1):
        _khop(_py(hi, lo, cl, sp, dem, chieu, ts, LU.QC_AUDCAD), _c(hi, lo, cl, sp, dem, chieu, ts, LU.QC_AUDCAD),
              "n=%d chieu=%+d" % (n, chieu))


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_khop_chuoi_phang(nhan, mo_hinh):
    n = 500
    cl = np.full(n, 0.9)
    sp, dem = np.full(n, 1e-4), np.zeros(n)
    ts = LU.ThamSo(buoc=5.0, tp=3.0, tran_tang=4, khop_bar=mo_hinh)
    _khop(_py(cl, cl, cl, sp, dem, 1, ts, LU.QC_AUDCAD), _c(cl, cl, cl, sp, dem, 1, ts, LU.QC_AUDCAD), "phang")


@pytest.mark.parametrize("mo_hinh", MO_HINH)
@pytest.mark.parametrize("hong", ["cl", "hi", "lo", "sp", "dem", "hi_inf", "lo_inf"])
def test_khop_khi_du_lieu_co_nan_hoac_inf(nhan, hong, mo_hinh):
    """`cuc_tri`: cung phep tinh cung thu tu -> NaN/inf lan truyen y het Python; khong co duong 'C bo qua im lang'.
    `duong_di`: du lieu khong huu han bi TU CHOI o ca hai ben (Python ValueError, C bao loi -> wrapper None) - duong di tung buoc
    khong co nghia khi mot dinh la NaN, nen khong co 'lan truyen' de khop."""
    rng = np.random.default_rng(3)
    n = 1500
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.97 * x[i - 1] + rng.normal(0, 0.0012)
    cl = np.round(0.9 + x, 5)
    op = np.r_[cl[0], cl[:-1]]
    hi = np.round(np.maximum(op, cl) + np.abs(rng.normal(0, 0.0006, n)), 5)
    lo = np.round(np.minimum(op, cl) - np.abs(rng.normal(0, 0.0006, n)), 5)
    sp, dem = np.full(n, 1e-4), np.zeros(n)
    dem[96::96] = 1.0
    m = {"cl": cl, "hi": hi, "lo": lo, "sp": sp, "dem": dem}
    if hong.endswith("_inf"):
        k = hong[:2]
        m[k] = m[k].copy()
        m[k][700] = np.inf if k == "hi" else -np.inf
    else:
        m[hong] = m[hong].copy()
        m[hong][300] = np.nan
    ts = LU.ThamSo(buoc=20.0, tp=15.0, tran_tang=8, khop_bar=mo_hinh)
    for chieu in (1, -1):
        if mo_hinh == "duong_di":
            args = (m["hi"], m["lo"], m["cl"], m["sp"], m["dem"], chieu, ts, LU.QC_AUDCAD)
            assert LN.mot_ro(*args, []) is None
            with pytest.raises(ValueError, match="NaN hoac inf"):
                LU.mot_ro_chuan(*args)
            with pytest.raises(ValueError, match="NaN hoac inf"):
                LU._mot_ro_nhanh(*args)                       # C tu choi -> Python lo -> cung loi, khong ket qua im lang
            continue
        _khop(_py(m["hi"], m["lo"], m["cl"], m["sp"], m["dem"], chieu, ts, LU.QC_AUDCAD),
              _c(m["hi"], m["lo"], m["cl"], m["sp"], m["dem"], chieu, ts, LU.QC_AUDCAD), "%s chieu=%+d" % (hong, chieu))


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_khop_tren_lat_cat_khong_lien_tuc(nhan, mo_hinh):
    """Lat cat co buoc (`a[::2]`) khong lien tuc trong bo nho: wrapper phai lam phang, khong doc nham."""
    rng = np.random.default_rng(5)
    hi, lo, cl, sp, dem, ts, qc = _kich_ban(rng, mo_hinh=mo_hinh)
    n2 = 2 * len(cl)

    def gian(a):
        b = np.empty(n2)
        b[::2] = a
        b[1::2] = np.nan
        return b[::2]

    v = [gian(a) for a in (hi, lo, cl, sp, dem)]
    assert not v[0].flags["C_CONTIGUOUS"]
    for chieu in (1, -1):
        _khop(_py(*v, chieu, ts, qc), _c(*v, chieu, ts, qc), "lat cat chieu=%+d" % chieu)
        _khop(_py(hi, lo, cl, sp, dem, chieu, ts, qc), _c(*v, chieu, ts, qc), "lat cat == lien tuc chieu=%+d" % chieu)


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_bo_dem_su_kien_tran_va_chay_lai(nhan, mo_hinh):
    """> 4096 su kien: C bao thieu cho, wrapper chay lai (deterministic) voi bo dem du - ket qua phai y het Python."""
    rng = np.random.default_rng(9)
    n = 30000
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.9 * x[i - 1] + rng.normal(0, 4e-4)
    cl = np.round(0.9 + x, 5)
    op = np.r_[cl[0], cl[:-1]]
    hi = np.round(np.maximum(op, cl) + np.abs(rng.normal(0, 2e-4, n)), 5)
    lo = np.round(np.minimum(op, cl) - np.abs(rng.normal(0, 2e-4, n)), 5)
    sp, dem = np.full(n, 1e-4), np.zeros(n)
    dem[96::96] = 1.0
    ts = LU.ThamSo(buoc=4.0, tp=3.0, tran_tang=6, khop_bar=mo_hinh)
    a = _py(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD)
    assert len(a[3]) > 4096, "kich ban chua du lon de ep bo dem tran (%d su kien)" % len(a[3])
    _khop(a, _c(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD), "tran bo dem")


@pytest.mark.parametrize("mo_hinh", MO_HINH)
@pytest.mark.parametrize("tia", [False, True], ids=["khong_tia", "tia"])
def test_khop_khi_so_tang_vuot_bo_dem_ban_dau(nhan, tia, mo_hinh):
    """tran_tang = 1.000.000 -> C xin bo dem 64 tang roi TU GIAN (realloc). Duong cap phat nay KHONG BAO GIO chay voi tran_tang nho
    (bo dem = tran + 4): do bang gcov 03/10 la dong 67-71 cua luoi_nhan.c chua tung duoc chay. Gia lao 450 muc luoi (> 64, > 256) roi
    dao dong; `tia`: tang dau tien bi pop tien dan -> don mang (memmove) o bo dem da gian."""
    rng = np.random.default_rng(404)
    n = 1800
    x = np.zeros(n)
    x[:450] = -np.arange(450) * 2.2e-4
    x[450:] = x[449] + np.cumsum(rng.normal(0.0, 8e-4, n - 450))
    cl = np.round(5.0 + x, 5)
    op = np.r_[cl[0], cl[:-1]]
    hi = np.round(np.maximum(op, cl) + np.abs(rng.normal(0, 3e-4, n)), 5)
    lo = np.round(np.minimum(op, cl) - np.abs(rng.normal(0, 3e-4, n)), 5)
    sp, dem = np.full(n, 1e-4), np.zeros(n)
    dem[96::96] = 1.0
    kw = dict(buoc=2.0, tp=3.0, tran_tang=1_000_000)
    if tia:
        kw.update(tia_lenh=True, bien_cap=0.2, cap_moi_bar=3)
    ts = LU.ThamSo(**kw, khop_bar=mo_hinh)
    a = _py(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD)
    assert a[2]["tang_max"] > 256, "kich ban khong du sau de ep bo dem gian (tang_max=%d)" % a[2]["tang_max"]
    if tia:
        assert a[2]["so_cap"] > 20, "kich ban khong du tia de ep don mang (so_cap=%d)" % a[2]["so_cap"]
    _khop(a, _c(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD), "bo dem gian %s tia=%s" % (mo_hinh, tia))


@pytest.mark.parametrize("chieu", [1, -1])
@pytest.mark.parametrize("mo_hinh,ca", _CA_BIEN_MO_HINH, ids=lambda x: x if isinstance(x, str) else x[0])
def test_ca_bien_cham_dung_moc_khop_tung_bit(nhan, mo_hinh, ca, chieu):
    """Gia nhi phan (1 + k/1024) de bar cham DUNG moc: khop lenh / cho lui / chot tien / TP / tia. Gia ngau nhien khong bao gio cham
    dung moc nen loi `<` / `<=` o day tung lot qua ca tu kiem lan test ngau nhien (3/9 ban dot bien song sot). Ngu nghia ma Python
    PHAI cho: cham dung moc = KHOP / CHOT / CHAM TP (`<=`, `>=`); tia khi lai cap >= bien."""
    ten, kw, bars, mong = ca
    qc = LN._qc_bien()
    ts = LU.ThamSo(**kw, khop_bar=mo_hinh)
    hi, lo, cl, sp, dem = LN._chuoi_bien(bars, chieu)
    a = _py(hi, lo, cl, sp, dem, chieu, ts, qc)
    assert (a[2]["so_ro"], a[2]["so_lenh"], a[2]["so_cap"]) == mong, "Python doi nghia o moc: %s" % (a[2],)
    b = _c(hi, lo, cl, sp, dem, chieu, ts, qc)
    ok, mo_ta = LN.so_sanh_ket_qua(a, b, 0.0, 0.0)          # chinh xac: khong dung sai (moi phep tinh deu chinh xac trong double)
    assert ok, "%s/%s chieu=%+d: %s" % (mo_hinh, ten, chieu, mo_ta)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and a[3] == b[3]


@pytest.mark.parametrize("ca", LN._CA_BIEN_THAP_PHAN, ids=lambda ca: ca[0])
def test_ca_thap_phan_cham_dung_moc_c_khop_python_tung_bit(nhan, ca):
    """Gia 5 chu so THAT cham DUNG moc (08/10/2026): khop tang / chot TP / mo lai sau cho lui. Moc tinh bang double lech ~1 ulp ve phia KHONG
    cham, nen chi dung sai `EPS_CHAM_PIP` moi cho Python va C ra dung ngu nghia cua EA (`bid <= muc`: cham dung = khop). Gia nhi phan o
    `test_ca_bien_cham_dung_moc_khop_tung_bit` khong bao gio co nhieu nay."""
    ten, chieu, kw, bars, mong = ca
    qc = LN._qc_thap_phan()
    ts = LU.ThamSo(**kw, khop_bar="duong_di")
    hi, lo, cl, sp, dem = LN._chuoi_thap_phan(bars)
    a = _py(hi, lo, cl, sp, dem, chieu, ts, qc)
    assert (a[2]["so_ro"], a[2]["so_lenh"], a[2]["so_cap"]) == mong, "Python khong cham moc nua: %s" % (a[2],)
    b = _c(hi, lo, cl, sp, dem, chieu, ts, qc)
    ok, mo_ta = LN.so_sanh_ket_qua(a, b, 0.0, 0.0)
    assert ok, "%s: %s" % (ten, mo_ta)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and a[3] == b[3]


@pytest.mark.parametrize("ca", LN._CA_BIEN_THAP_PHAN, ids=lambda ca: ca[0])
def test_ca_thap_phan_that_su_co_nhieu_so_hoc_tat_dung_sai_thi_ra_khac(monkeypatch, ca):
    """Moi ca thap phan phai CO RANG: tat dung sai (`EPS_CHAM_PIP = 0`) thi ket qua khac ky vong. Neu mot ca khong con khac (do doi quy cach, doi
    cach tinh moc, hay chuyen sang so chinh xac) thi no thanh ca thuong - khong con bat duoc loi dung sai."""
    ten, chieu, kw, bars, mong = ca
    monkeypatch.setattr(LU, "EPS_CHAM_PIP", 0.0)
    ts = LU.ThamSo(**kw, khop_bar="duong_di")
    hi, lo, cl, sp, dem = LN._chuoi_thap_phan(bars)
    a = _py(hi, lo, cl, sp, dem, chieu, ts, LN._qc_thap_phan())
    assert (a[2]["so_ro"], a[2]["so_lenh"], a[2]["so_cap"]) != mong, "ca '%s' khong con nhay cam voi nhieu so hoc" % ten


def test_hut_eps_phai_lon_hon_dung_sai_va_bat_dung_sai_qua_lon(monkeypatch):
    """Ca `*_hut_eps` dung cach moc `_HUT` pip: voi dung sai that thi KHONG cham (da kiem o test khop tung bit); phai LON hon dung sai, va neu
    dung sai bi nang len qua khoang hut thi ket qua doi - tuc cac ca nay bat duoc loi 'dung sai qua rong'."""
    assert 2 * LU.EPS_CHAM_PIP < LN._HUT, "khoang hut cua ca `*_hut_eps` phai lon gap doi dung sai - doi `_HUT` cung luc doi EPS_CHAM_PIP"
    hut = [ca for ca in LN._CA_BIEN_DUONG if ca[0].endswith("_hut_eps")]
    assert len(hut) == 3, [ca[0] for ca in hut]
    qc = LN._qc_bien()
    for ten, kw, bars, mong in hut:
        for chieu in (1, -1):
            hi, lo, cl, sp, dem = LN._chuoi_bien(bars, chieu)
            ts = LU.ThamSo(**kw, khop_bar="duong_di")
            a = _py(hi, lo, cl, sp, dem, chieu, ts, qc)
            assert (a[2]["so_ro"], a[2]["so_lenh"], a[2]["so_cap"]) == mong, (ten, chieu, a[2])
            monkeypatch.setattr(LU, "EPS_CHAM_PIP", 4 * LN._HUT)
            b = _py(hi, lo, cl, sp, dem, chieu, ts, qc)
            assert (b[2]["so_ro"], b[2]["so_lenh"], b[2]["so_cap"]) != mong, "ca '%s' chieu %+d khong bat duoc dung sai qua rong" % (ten, chieu)
            monkeypatch.setattr(LU, "EPS_CHAM_PIP", 1e-6)


def test_dung_sai_cham_moc_c_bang_python():
    """`#define EPS_CHAM_PIP` o .c phai bang `luoi.EPS_CHAM_PIP`: lech nhau thi hai ben khop lenh khac nhau o cac o cham dung moc."""
    nguon = LN.NGUON_C.read_text(encoding="utf-8")
    m = re.findall(r"^#define\s+EPS_CHAM_PIP\s+([0-9.eE+-]+)\s*(?:/\*.*)?$", nguon, re.M)
    assert len(m) == 1 and float(m[0]) == LU.EPS_CHAM_PIP, (m, LU.EPS_CHAM_PIP)


def test_dau_ban_kiem_doi_khi_bang_ca_doi(monkeypatch):
    """Marker 'da kiem' mang van tay cua CA bo kiem: them / sua ca bien thi nhan da cache phai kiem lai, khong duoc tin marker cu."""
    d0 = LN._dau_ban_kiem()
    assert LN._dau_ban_kiem() == d0 and len(d0) == 8
    with monkeypatch.context() as m:
        m.setattr(LN, "_CA_BIEN_THAP_PHAN", LN._CA_BIEN_THAP_PHAN[:-1])
        assert LN._dau_ban_kiem() != d0
    with monkeypatch.context() as m:
        m.setattr(LN, "_HUT", LN._HUT * 2)
        assert LN._dau_ban_kiem() != d0
    with monkeypatch.context() as m:
        m.setattr(LN, "_CA_TU_KIEM", LN._CA_TU_KIEM[:-1])
        assert LN._dau_ban_kiem() != d0
    assert LN._dau_ban_kiem() == d0


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_bar_0_la_spread_lenh_dau_o_ca_python_va_nhan_c(nhan, mo_hinh):
    """`lai_arr[0]` = -(spread[0] * ts.lot * hop): chi phi DA TRA luc bar 0 (sua 03/10/2026). Truoc do ca hai ban gan
    `-tong spread ca chuoi` -> diem dau gia, xem test_luoi_quy_cach muc 9. Tung bit, hai chieu, ca cap JPY."""
    so_ca = so_nhieu_lenh = 0
    for jpy in (False, True):
        for seed in (1, 2, 3):
            for hi, lo, cl, sp, dem, ts, qc in _so_ngau_nhien(seed, 6, jpy, mo_hinh):
                for chieu in (1, -1):
                    mong = -(sp[0] * ts.lot * qc.hop_dong)
                    a, b = _py(hi, lo, cl, sp, dem, chieu, ts, qc), _c(hi, lo, cl, sp, dem, chieu, ts, qc)
                    assert a[0][0] == mong and b[0][0] == mong, (a[0][0], b[0][0], mong)
                    assert a[1][0] == 0.0 and b[1][0] == 0.0
                    so_ca += 1
                    if a[2]["so_lenh"] > 1:
                        so_nhieu_lenh += 1
                        assert a[0][0] > -a[2]["phi_spread"]                 # khong con la tong ca chuoi
    assert so_ca >= 30 and so_nhieu_lenh >= so_ca // 2, (so_ca, so_nhieu_lenh)


def test_ham_c_tu_choi_dau_vao_ngoai_mien(nhan):
    """n = 0 hoac chieu = 0: wrapper khong bao gio gui, nhung ham C van phai tu choi (ma loi) chu khong doc bo nho bay."""
    p = LN._dong_goi(LU.ThamSo(), LU.QC_AUDCAD, 1)
    a5 = np.ones(5)
    for ghi in (False, True):
        assert LN._goi(nhan, a5, a5, a5, a5, a5, 0, p, ghi) is None
    e = np.empty(0)
    assert LN._goi(nhan, e, e, e, e, e, 1, p, False) is None
    # gia tri mo hinh la (khong phai 0 / 1): C khong doan ma tu choi - hai ben khong the lech nhau ve mo hinh
    k = LN._TEN_P.index("mo_hinh")
    for ghi in (False, True):
        assert LN._goi(nhan, a5, a5, a5, a5, a5, 1, p, ghi) is not None           # doi chung: 5 bar phang chay duoc
        for mh in (-1.0, 0.5, 2.0, 3.0, float("nan"), float("inf")):
            q = p.copy()
            q[k] = mh
            assert LN._goi(nhan, a5, a5, a5, a5, a5, 1, q, ghi) is None, mh


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_luy_thua_buoc_tran_so_de_python_bao_loi(nhan, mo_hinh):
    """Nhu `test_luy_thua_tran_so...` nhung cho `he_so_buoc ** k` (buoc_k): C tra NaN -> loi -> Python nem dung OverflowError. buoc_tran
    = 1 pip cat buoc o 1 pip nen 2000 muc chi can 0,2 gia, ma `1,7 ** 1400` van tran (Python tinh luy thua TRUOC khi cat)."""
    n = 4
    cl = np.array([1.0, 1.0, 1.0, 1.0])
    lo = np.array([1.0, 0.7, 0.7, 0.7])
    hi = cl.copy()
    sp, dem = np.full(n, 1e-4), np.zeros(n)
    ts = LU.ThamSo(buoc=1.0, tp=5.0, tran_tang=2000, he_so_buoc=1.7, buoc_tran=1.0, khop_bar=mo_hinh)
    assert LN.kha_dung(ts, LU.QC_AUDCAD)
    assert LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, []) is None
    with pytest.raises(OverflowError):
        LU.mot_ro_chuan(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD)
    with pytest.raises(OverflowError):
        LU._mot_ro_nhanh(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD)


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_moc_cho_lui_dung_bang_0_python_bao_loi_va_c_nhuong(nhan, mo_hinh):
    """`cho == 0.0` vua la moc gia hop le vua la co 'khong cho' (ca Python `if cho:` lan C `cho != 0.0`): neu moc cho lui rot dung vao 0
    thi ro rong va khong ai cho -> Python IndexError. C KHONG tu doan: tra loi -> Python nem dung loi do. (Gia that khong bao gio ~ 0;
    day la loi ngu nghia co san cua engine, ghi nhan chu khong sua.)"""
    p = 2.0 ** -10
    qc = LN._qc_bien()
    goc = 5 * p
    cl = np.array([goc, goc + 5 * p, goc + 5 * p])
    hi, lo = cl.copy(), cl.copy()
    lo[1] = goc
    sp, dem = np.zeros(3), np.zeros(3)
    ts = LU.ThamSo(buoc=40.0, tp=5.0, tran_tang=4, lot=1.0, cho_lui=10.0, khop_bar=mo_hinh)   # TP o 10 pip, cho lui 10 pip -> moc cho = 0,0 dung
    assert LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, qc, []) is None
    with pytest.raises(IndexError):
        LU.mot_ro_chuan(hi, lo, cl, sp, dem, 1, ts, qc)
    with pytest.raises(IndexError):
        LU._mot_ro_nhanh(hi, lo, cl, sp, dem, 1, ts, qc)


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_ghi_lenh_khong_doi_so(nhan, mo_hinh):
    """Bat/tat ghi lenh chi them dong ghi, khong doi mot con so (nhu ban Python)."""
    hi, lo, cl, sp, dem = LN._kich_ban_tu_kiem()
    ts = LU.ThamSo(buoc=15.0, tp=10.0, tran_tang=9, tia_lenh=True, bien_cap=3.0, cap_moi_bar=1, khop_bar=mo_hinh)
    r0 = LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, None)
    ev: list = []
    r1 = LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, ev)
    assert ev and np.array_equal(r0[0], r1[0]) and np.array_equal(r0[1], r1[1]) and r0[2] == r1[2]


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_khong_ghi_de_mang_dau_vao(nhan, mo_hinh):
    hi, lo, cl, sp, dem = LN._kich_ban_tu_kiem()
    goc = [a.copy() for a in (hi, lo, cl, sp, dem)]
    LN.mot_ro(hi, lo, cl, sp, dem, 1, LU.ThamSo(buoc=15.0, tp=10.0, tran_tang=9, khop_bar=mo_hinh), LU.QC_AUDCAD, [])
    for a, b in zip((hi, lo, cl, sp, dem), goc):
        assert np.array_equal(a, b)


# ------------------------------------------------------------------ QUA ENGINE THAT (LU.chay)
@pytest.mark.parametrize("sua", [
    dict(),
    dict(che_do="mua", kieu_lot="nhan", he_so_lot=1.3, buoc=12.0, tp=8.0, tran_tang=10),
    dict(tia_lenh=True, bien_cap=3.0, cap_moi_bar=1, buoc=10.0, tp=15.0, tran_tang=15),
    dict(cho_lui=8.0, buoc=15.0, tp=10.0, tran_tang=12),
    dict(che_do="ban", chot_tien=3.0, buoc=15.0, tp=10.0, tran_tang=12),
    dict(he_so_buoc=1.25, buoc_tran=60.0, buoc=10.0, tp=10.0, tran_tang=14),
])
@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_chay_cho_ket_qua_y_het_che_do_py(nhan, monkeypatch, sua, mo_hinh):
    df = _df()
    ts = LU.ThamSo(**dict(dict(buoc=15.0, tp=10.0, tran_tang=12), **sua), khop_bar=mo_hinh)
    monkeypatch.setenv("LUOI_NHAN", "py")
    kp = LU.chay(df, ts, 10000.0, ghi_lenh=True)
    monkeypatch.setenv("LUOI_NHAN", "auto")
    kc = LU.chay(df, ts, 10000.0, ghi_lenh=True)
    for ten in ("lai_rong", "lai_gop", "phi_spread", "phi_swap", "lo_treo_dinh"):
        x, y = getattr(kp, ten), getattr(kc, ten)
        assert x == y if LINUX else x == pytest.approx(y, rel=1e-9, abs=1e-9), ten
    for ten in ("so_ro", "so_lenh", "tang_max", "chay", "bar_chay"):
        assert getattr(kp, ten) == getattr(kc, ten), ten
    if LINUX:
        assert np.array_equal(kp.duong_equity, kc.duong_equity)
    else:
        assert np.allclose(kp.duong_equity, kc.duong_equity, rtol=1e-9, atol=1e-9)
    pd.testing.assert_frame_equal(kp.lenh, kc.lenh, check_exact=LINUX)
    assert len(kc.lenh) > 50


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_chay_that_su_dung_nhan_c(nhan, monkeypatch, mo_hinh):
    """Dispatcher noi dung day: neu dau vao `chay` doi kieu (list, float32...) ma khong ai hay, nhan C bi bo qua im lang."""
    dem = {"c": 0, "py": 0}
    goc = LN.mot_ro

    def dem_mot_ro(*a, **k):
        r = goc(*a, **k)
        dem["py" if r is None else "c"] += 1
        return r

    monkeypatch.setattr(LN, "mot_ro", dem_mot_ro)
    LU.chay(_df(1500), LU.ThamSo(buoc=15.0, tp=10.0, tran_tang=8, khop_bar=mo_hinh), 10000.0)
    assert dem == {"c": 2, "py": 0}, dem


# ------------------------------------------------------------------ DU PHONG
def test_che_do_py_khong_dung_nhan_c(monkeypatch):
    monkeypatch.setenv("LUOI_NHAN", "py")
    hi, lo, cl, sp, dem = LN._kich_ban_tu_kiem()
    assert LN.lay_nhan() is None
    assert LN.mot_ro(hi, lo, cl, sp, dem, 1, LU.ThamSo(), LU.QC_AUDCAD, []) is None


def test_che_do_la_thi_ve_auto(monkeypatch):
    monkeypatch.setenv("LUOI_NHAN", "linh_tinh")
    assert LN.che_do() == "auto"
    monkeypatch.setenv("LUOI_NHAN", " PY ")
    assert LN.che_do() == "py"


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_dau_vao_khong_phai_ndarray_float64_de_python_lo(nhan, mo_hinh):
    hi, lo, cl, sp, dem = LN._kich_ban_tu_kiem()
    ts = LU.ThamSo(buoc=20.0, tp=15.0, tran_tang=8, khop_bar=mo_hinh)
    chuan = LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, [])
    assert chuan is not None
    # list float thuan: `sum()` cua Python >= 3.12 cong bu - khong the khop bit -> phai de Python lo
    assert LN.mot_ro(hi.tolist(), lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, []) is None
    # sai dtype
    assert LN.mot_ro(hi.astype(np.float32), lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, []) is None
    assert LN.mot_ro(hi, lo, cl, sp, dem.astype(np.int64), 1, ts, LU.QC_AUDCAD, []) is None
    # sai chieu mang / do dai
    assert LN.mot_ro(hi.reshape(-1, 1), lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, []) is None
    assert LN.mot_ro(hi[:-1], lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, []) is None
    e = np.array([], dtype=float)
    assert LN.mot_ro(e, e, e, e, e, 1, ts, LU.QC_AUDCAD, []) is None
    # chieu la
    assert LN.mot_ro(hi, lo, cl, sp, dem, 0, ts, LU.QC_AUDCAD, []) is None
    assert LN.mot_ro(hi, lo, cl, sp, dem, 2, ts, LU.QC_AUDCAD, []) is None


@pytest.mark.parametrize("sua", [
    dict(buoc=0.0), dict(buoc=-5.0), dict(lot=0.0), dict(lot=-0.01), dict(tran_tang=0), dict(tran_tang=2_000_000),
    dict(buoc=float("nan")), dict(tp=float("inf")), dict(cho_lui=-1.0), dict(buoc_tran=-1.0),
    dict(he_so_lot=-1.0, kieu_lot="cong"), dict(he_so_buoc=0.0), dict(he_so_buoc=-1.2),
    dict(he_so_buoc=2), dict(kieu_lot="nhan", he_so_lot=2),                       # luy thua so nguyen: Python chinh xac, C pow()
    dict(lot=np.float32(0.01)), dict(buoc=np.float32(20.0)), dict(kieu_lot="nhan", he_so_lot=np.float32(1.2)),
    dict(lot=True), dict(lot="0.01"), dict(lot=None),
])
@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_tham_so_ngoai_mien_de_python_lo(nhan, sua, mo_hinh):
    hi, lo, cl, sp, dem = LN._kich_ban_tu_kiem()
    ts = LU.ThamSo(**dict(dict(buoc=20.0, tp=15.0, tran_tang=8), **sua), khop_bar=mo_hinh)
    assert not LN.kha_dung(ts, LU.QC_AUDCAD)
    assert LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, []) is None


@pytest.mark.parametrize("sua", [dict(pip=0.0), dict(pip=-1e-4), dict(hop_dong=0.0), dict(hop_dong=float("nan")),
                                 dict(phi_nam_mua=float("inf")), dict(phi_nam_ban=float("nan"))])
@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_quy_cach_ngoai_mien_de_python_lo(nhan, sua, mo_hinh):
    hi, lo, cl, sp, dem = LN._kich_ban_tu_kiem()
    qc = LU.QuyCach(**sua)
    assert LN.mot_ro(hi, lo, cl, sp, dem, 1, LU.ThamSo(buoc=20.0, tp=15.0, tran_tang=8, khop_bar=mo_hinh), qc, []) is None


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_luy_thua_tran_so_de_python_bao_loi(nhan, mo_hinh):
    """`he ** k` tran so: Python (float) nem OverflowError. C khong tu doan: bao loi -> wrapper None -> `_mot_ro_nhanh` chay Python
    va Python nem dung loi do (khong phai ket qua inf lang le)."""
    n = 4
    cl = np.array([1.0, 1.0, 1.0, 1.0])
    lo = np.array([1.0, 0.2, 0.2, 0.2])           # bar 1 tut 8000 pip: mo lien tuc den tran tang
    hi = cl.copy()
    sp, dem = np.full(n, 1e-4), np.zeros(n)
    ts = LU.ThamSo(buoc=1.0, tp=5.0, tran_tang=1200, kieu_lot="nhan", he_so_lot=2.0, khop_bar=mo_hinh)
    assert LN.kha_dung(ts, LU.QC_AUDCAD)
    assert LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD, []) is None
    with pytest.raises(OverflowError):
        LU.mot_ro_chuan(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD)
    with pytest.raises(OverflowError):
        LU._mot_ro_nhanh(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD)


def test_c_che_do_bat_buoc_bao_loi_khi_khong_co_nhan(nhan_sach, monkeypatch):
    monkeypatch.setattr(LN, "_ung_vien_trinh_bien", lambda: [])
    monkeypatch.setenv("LUOI_NHAN", "auto")
    assert LN.lay_nhan() is None
    tt = LN.trang_thai()
    assert tt["san_sang"] is False and "khong co trinh bien dich" in tt["ly_do"]
    # engine van chay (Python) va cho dung ket qua
    kq = LU.chay(_df(800), LU.ThamSo(buoc=15.0, tp=10.0, tran_tang=8), 10000.0)
    assert kq.so_lenh > 0
    monkeypatch.setenv("LUOI_NHAN", "c")
    with pytest.raises(RuntimeError, match="LUOI_NHAN=c"):
        LN.lay_nhan()


def test_tu_kiem_that_bai_thi_bo_nhan_va_xoa_ban_dich(nhan_sach, monkeypatch):
    """Nhan lech Python -> khong duoc dung, khong de lai file de lan sau nap nham."""
    monkeypatch.setattr(LN, "_tu_kiem", lambda lib: (False, "gia lap: khong khop"))
    ds = LN._ung_vien_trinh_bien()[:1]
    monkeypatch.setattr(LN, "_ung_vien_trinh_bien", lambda: ds)
    assert LN.lay_nhan() is None
    tt = LN.trang_thai()
    assert tt["san_sang"] is False and "TU KIEM KHONG KHOP" in tt["ly_do"], tt["ly_do"]
    if sys.platform != "win32":                              # Windows khoa .dll dang nap: khong xoa duoc, nhung khong co marker thi lan sau tu kiem lai
        assert not list(nhan_sach.glob("luoi_nhan_*%s" % LN._duoi_thu_vien())), "ban dich lech van con trong cache"
    assert not list(nhan_sach.glob("*.ok_*")), "marker 'da kiem' khong duoc ghi khi tu kiem that bai"
    hi, lo, cl, sp, dem = LN._kich_ban_tu_kiem()
    assert LN.mot_ro(hi, lo, cl, sp, dem, 1, LU.ThamSo(), LU.QC_AUDCAD, []) is None


def test_dich_vao_cache_rieng_roi_lan_hai_dung_cache(nhan_sach):
    assert LN.lay_nhan() is not None, LN.trang_thai()["ly_do"]
    tt = LN.trang_thai()
    assert tt["san_sang"] and tt["giay_dich"] > 0 and tt["giay_tu_kiem"] > 0
    so = list(nhan_sach.glob("luoi_nhan_*%s" % LN._duoi_thu_vien()))
    ok = list(nhan_sach.glob("luoi_nhan_*.ok_%s_%s" % (LN._dau_py(), LN._dau_ban_kiem())))
    assert len(so) == 1 and len(ok) == 1
    assert not list(nhan_sach.glob("ln_*")), "thu muc dich tam phai duoc don"
    LN.lam_lai()                                            # tien trinh moi: phai nap tu cache, KHONG dich lai
    assert LN.lay_nhan() is not None
    tt2 = LN.trang_thai()
    assert tt2["giay_dich"] == 0.0 and tt2["giay_tu_kiem"] == 0.0 and "da kiem truoc do" in tt2["ly_do"], tt2


def test_khoa_cache_doi_theo_noi_dung_nguon(tmp_path, monkeypatch):
    k0 = LN._khoa_dich("gcc")
    assert LN._khoa_dich("gcc") == k0 and LN._khoa_dich("msvc") != k0
    bien = tmp_path / "luoi_nhan.c"
    bien.write_bytes(LN.NGUON_C.read_bytes() + b"\n/* doi */\n")
    monkeypatch.setattr(LN, "NGUON_C", bien)
    assert LN._khoa_dich("gcc") != k0


# ------------------------------------------------------------------ CHONG TROI
def _truong_doc(*ham):
    nguon = "\n".join(inspect.getsource(h) for h in ham)
    return set(re.findall(r"\bts\.(\w+)", nguon)), set(re.findall(r"\bqc\.(\w+)", nguon))


def test_moi_truong_ts_va_qc_ma_engine_doc_deu_co_trong_nhan_c():
    """Ham engine doc `ts.<a>` / `qc.<b>` nao thi nhan C phai biet cai do (moi mo hinh bar, ca dieu kien mien cua `duong_di` va cho chon
    mo hinh). Them truong vao engine ma quen C = C tinh THIEU im lang."""
    ts_ct, qc_ct = _truong_doc(LU._mot_ro)
    ts_dd, qc_dd = _truong_doc(LU._mot_ro_duong, LU.mien_duong_di)
    ts_chon, qc_chon = _truong_doc(LU.kiem_khop_bar, LU.mot_ro_chuan)
    assert ts_chon == {"khop_bar"} and not qc_chon, "cho chon mo hinh doc truong la: %s %s" % (ts_chon, qc_chon)
    for ten, ts_doc, qc_doc in (("cuc_tri", ts_ct, qc_ct), ("duong_di", ts_dd, qc_dd)):
        assert ts_doc <= set(LN.TRUONG_TS), "nhan C thieu (%s): %s" % (ten, sorted(ts_doc - set(LN.TRUONG_TS)))
        assert qc_doc <= set(LN.TRUONG_QC), "nhan C thieu (%s): %s" % (ten, sorted(qc_doc - set(LN.TRUONG_QC)))
    assert ts_ct | ts_dd | ts_chon == set(LN.TRUONG_TS) and qc_ct | qc_dd == set(LN.TRUONG_QC), "TRUONG_* khai thua so voi engine"


def test_moi_truong_thamso_phai_duoc_phan_loai():
    """Truong moi cua ThamSo phai thuoc MOT trong: nhan C doc / chi `chay` doc / chua cai dat. Khong de truong lo lung."""
    chi_chay = {"che_do", "muc_stopout", "don_bay"}
    da_biet = set(LN.TRUONG_TS) | chi_chay | set(LU.CHUA_CAI_DAT)
    ten = {f.name for f in dataclasses.fields(LU.ThamSo)}
    assert ten <= da_biet, "ThamSo co truong chua phan loai (nhan C / chay / chua cai dat): %s" % sorted(ten - da_biet)


def test_so_tham_so_va_thu_tu_khop_abi(nhan):
    """Thu tu enum P_* trong .c phai TRUNG thu tu `_TEN_P` trong .py (doi mot ben ma quen ben kia = tham so lech cho)."""
    assert nhan.luoi_nhan_so_tham_so() == len(LN._TEN_P)
    assert nhan.luoi_nhan_phien_ban() == LN.PHIEN_BAN
    nguon = LN.NGUON_C.read_text(encoding="utf-8")
    kv = re.search(r"enum\s*\{\s*(P_LOT[^}]*)\}", nguon, re.S).group(1)
    ten_c = [t.strip().split("=")[0].strip() for t in kv.split(",") if t.strip()]
    assert ten_c[-1] == "P_SO"
    assert [t[2:].lower() for t in ten_c[:-1]] == list(LN._TEN_P)


def test_tran_so_vong_c_bang_python():
    """Hai ben cung ngan sach vong chot / tia trong mot doan (`TOI_DA_VONG` o .c, `luoi.TOI_DA_VONG_DOAN` o .py): lech nhau thi tham so
    suy bien se chay duoc o ben nay va bao loi o ben kia."""
    nguon = LN.NGUON_C.read_text(encoding="utf-8")
    m = re.findall(r"^#define\s+TOI_DA_VONG\s+(\d+)\s*$", nguon, re.M)
    assert len(m) == 1 and int(m[0]) == LU.TOI_DA_VONG_DOAN, (m, LU.TOI_DA_VONG_DOAN)


def test_kien_truc_da_xep_lop():
    from nhan import kien_truc as KT
    assert any("luoi_nhan" in nhom[1] for nhom in KT.LOP.values()), "luoi_nhan chua duoc xep lop trong nhan/kien_truc.LOP"


# ------------------------------------------------------------------ KIEM CHINH BO KIEM
# Do bang DOT BIEN (03/10): doi tung toan tu so sanh trong luoi_nhan.c (40 ban) roi xem bo tu kiem + test co phat hien khong. Truoc khi
# vá, 17/40 song sot: nhieu ban tuong duong (chieu > 0 -> >= 0 ...), nhung CO ba loi that - so sanh DUNG moc (gia nhi phan o
# `_CA_BIEN`), duong gian bo dem (tran_tang lon) va duong cong Kahan (chi chay tren Python >= 3.12 = may nha Python 3.14).
# Bang nay giu cac ban dot bien QUAN TRONG lam hang rao: ai doi luoi_nhan.c ma lam tu kiem mu di thi test do.
# (doan goc, doan dot bien, can Python >= 3.12)
_DOT_BIEN = {
    "khop_cham_moc": ("while (chieu > 0 ? (lo[i] <= moc) : (hi[i] >= moc)) {",
                      "while (chieu > 0 ? (lo[i] < moc) : (hi[i] > moc)) {", False, "cuc_tri"),
    "cho_lui_cham_moc": ("int cham0 = chieu > 0 ? (lo[i] <= cho) : (hi[i] >= cho);",
                         "int cham0 = chieu > 0 ? (lo[i] < cho) : (hi[i] > cho);", False, "cuc_tri"),
    "chot_tien_bang": ("cham = lai_noi >= nguong;", "cham = lai_noi > nguong;", False, "cuc_tri"),
    "tp_cham_moc": ("cham = chieu > 0 ? (hi[i] >= mtp) : (lo[i] <= mtp);",
                    "cham = chieu > 0 ? (hi[i] > mtp) : (lo[i] < mtp);", False, "cuc_tri"),
    "tia_bang_bien": ("if (lai_cap < bien_cap * pip * (pd->l + pc->l) * hop) break;",
                      "if (lai_cap <= bien_cap * pip * (pd->l + pc->l) * hop) break;", False, "cuc_tri"),
    "tia_so_cap_moi_bar": ("while (v.n >= 2 && da < cap_moi_bar) {", "while (v.n >= 2 && da <= cap_moi_bar) {", False, "cuc_tri"),
    "he_so_buoc_lech_tang": ("double b0 = buoc_k(buoc, he_buoc, buoc_tran, so_tang - 1);",
                             "double b0 = buoc_k(buoc, he_buoc, buoc_tran, so_tang);", False, "cuc_tri"),
    "qua_dem_365": ("/ 365.0 * cl[i];", "/ 360.0 * cl[i];", False, "cuc_tri"),
    "bar0_loi_cu": ("lai_arr[0] = -phi_sp_bar0; ", "lai_arr[0] = -phi_sp;       ", False, "cuc_tri"),
    "bar0_quen_spread_lenh_dau": ("const double phi_sp_bar0 = phi_sp;", "const double phi_sp_bar0 = 0.0;   ", False, "cuc_tri"),
    "kahan_vuot_bien": ("for (int64_t k = 1; k < n; k++) {", "for (int64_t k = 1; k <= n; k++) {", True, "cuc_tri"),
    "kahan_bo_bu": ("if (c != 0.0 && isfinite(c)) f += c;", "if (c != 0.0 && isfinite(c)) f += 0.0;", True, "cuc_tri"),
    # --- mo hinh `duong_di` (08/10/2026): moi dong la mot phep so sanh / cong thuc cua d_lui, d_len, d_treo_tai hoac vong nen
    'dd_lui_gap_khop_o_moc': ('double gg = (s * (moc - a) <= 0) ? moc : a;      /* nhay gia vuot moc: khop o gia dau doan */',
                             'double gg = moc;      /* nhay gia vuot moc: khop o gia dau doan */', False, "duong_di"),
    'dd_lui_chuoi_tu_moc': ('moc = gg - s * b1 * D->pip;',
                           'moc = moc - s * b1 * D->pip;', False, "duong_di"),
    'dd_lui_cham_moc_bo_dung_sai': ('while (s * (moc - b) >= -D->eps) {',
                                   'while (s * (moc - b) >= 0) {', False, "duong_di"),
    'dd_lui_cham_moc_sai_dau_dung_sai': ('while (s * (moc - b) >= -D->eps) {',
                                        'while (s * (moc - b) >= D->eps) {', False, "duong_di"),
    'dd_lui_cham_moc_dung_sai_lon': ('while (s * (moc - b) >= -D->eps) {',
                                    'while (s * (moc - b) >= -1000.0 * D->eps) {', False, "duong_di"),
    'dd_lui_tran_truoc': ('if ((double)D->v.n < D->tran) {',
                         'if ((double)D->v.n <= D->tran) {', False, "duong_di"),
    'dd_lui_tran_sau': ('if ((double)D->v.n >= D->tran) break;',
                       'if ((double)D->v.n > D->tran) break;', False, "duong_di"),
    'dd_cho_cham_moc_bo_dung_sai': ('if (s * (D->cho - b) < -D->eps) return 0;',
                                   'if (s * (D->cho - b) < 0) return 0;', False, "duong_di"),
    'dd_cho_cham_moc_sai_dau_dung_sai': ('if (s * (D->cho - b) < -D->eps) return 0;',
                                        'if (s * (D->cho - b) < D->eps) return 0;', False, "duong_di"),
    'dd_cho_cham_moc_dung_sai_lon': ('if (s * (D->cho - b) < -D->eps) return 0;',
                                    'if (s * (D->cho - b) < -1000.0 * D->eps) return 0;', False, "duong_di"),
    'dd_cho_gap': ('double gg = (s * (D->cho - a) <= 0) ? D->cho : a;',
                  'double gg = D->cho;', False, "duong_di"),
    'dd_len_cham_nguong_bo_dung_sai': ('if (s * (g_ev - b) > D->eps) break;',
                                      'if (s * (g_ev - b) > 0) break;', False, "duong_di"),
    'dd_len_cham_nguong_sai_dau_dung_sai': ('if (s * (g_ev - b) > D->eps) break;',
                                           'if (s * (g_ev - b) > -D->eps) break;', False, "duong_di"),
    'dd_len_cham_nguong_dung_sai_lon': ('if (s * (g_ev - b) > D->eps) break;',
                                       'if (s * (g_ev - b) > 1000.0 * D->eps) break;', False, "duong_di"),
    'dd_eps_bang_0': ('D.eps = EPS_CHAM_PIP * D.pip;',
                     'D.eps = 0.0;', False, "duong_di"),
    'dd_eps_quen_nhan_pip': ('D.eps = EPS_CHAM_PIP * D.pip;',
                            'D.eps = EPS_CHAM_PIP;', False, "duong_di"),
    'dd_eps_gap_10': ('D.eps = EPS_CHAM_PIP * D.pip;',
                     'D.eps = 10.0 * EPS_CHAM_PIP * D.pip;', False, "duong_di"),
    'dd_len_tia_truoc_tp': ('la_tia = (s * ps <= s * mtp);',
                           'la_tia = (s * ps < s * mtp);', False, "duong_di"),
    'dd_len_nhay_gia': ('double e = (s * (g_ev - p) >= 0) ? g_ev : p;',
                       'double e = g_ev;', False, "duong_di"),
    'dd_len_cap_moi_bar': ('(double)D->da_bar < D->cap_moi_bar',
                          '(double)D->da_bar <= D->cap_moi_bar', False, "duong_di"),
    'dd_len_dau_bien_cap': ('+ s * D->bien_cap * D->pip;',
                           '- s * D->bien_cap * D->pip;', False, "duong_di"),
    'dd_len_tia_lai_lech_lot': ('D->lai += (s * (e - pc->g) * pc->l + s * (e - pd->g) * pd->l) * D->hop;',
                               'D->lai += (s * (e - pc->g) * pd->l + s * (e - pd->g) * pc->l) * D->hop;', False, "duong_di"),
    'dd_len_chot_tien_bang_0': ('if (D->chot_tien > 0) mtp',
                               'if (D->chot_tien >= 0) mtp', False, "duong_di"),
    'dd_nguong_tien_theo_lot': ('D.nguong_tien = D.chot_tien * (D.lot / 0.01);',
                               'D.nguong_tien = D.chot_tien;', False, "duong_di"),
    'dd_cho_lui_huong': ('D->cho = e - s * D->cho_lui * D->pip;',
                        'D->cho = e + s * D->cho_lui * D->pip;', False, "duong_di"),
    'dd_cho_lui_dieu_kien': ('if (D->cho_lui > 0) {',
                            'if (D->cho_lui >= 0) {', False, "duong_di"),
    'dd_treo_max': ('if (f > treo_bar) treo_bar = f;',
                   'if (f < treo_bar) treo_bar = f;', False, "duong_di"),
    'dd_treo_lai_tru_lo': ('if (d > 0) acc += d * va[k].l;',
                          'acc += d * va[k].l;', False, "duong_di"),
    'dd_swap_dieu_kien': ('if (D.v.n > 0 && dem[i] != 0.0) {',
                         'if (D.v.n > 1 && dem[i] != 0.0) {', False, "duong_di"),
    'dd_swap_365': ('/ 365.0 * cl_i;',
                   '/ 360.0 * cl_i;', False, "duong_di"),
    'dd_bar0_spread': ('D.phi_sp += spread[0] * D.lot * D.hop;',
                      'D.phi_sp += 0.0;', False, "duong_di"),
    'dd_bar0_lai': ('lai_arr[0] = -phi_sp_bar0;\n    treo_arr[0] = 0.0;\n    stats[S_LAI_GOP] = D.lai;',
                   'lai_arr[0] = -D.phi_sp;\n    treo_arr[0] = 0.0;\n    stats[S_LAI_GOP] = D.lai;', False, "duong_di"),
    'dd_spread_theo_lot_tang': ('D->phi_sp += D->sp[i] * lk * D->hop;',
                               'D->phi_sp += D->sp[i] * D->lot * D->hop;', False, "duong_di"),
    'dd_o_khong_kep': ('        if (o < lo_i) o = lo_i;\n        if (o > hi_i) o = hi_i;\n',
                      '', False, "duong_di"),
    'dd_doji_la_do': ('if (cl_i >= o) { pts[0] = lo_i; pts[1] = hi_i; }',
                     'if (cl_i > o) { pts[0] = lo_i; pts[1] = hi_i; }', False, "duong_di"),
    'dd_mau_nen_dao': ('if (cl_i >= o) { pts[0] = lo_i; pts[1] = hi_i; }',
                      'if (cl_i <= o) { pts[0] = lo_i; pts[1] = hi_i; }', False, "duong_di"),
    'dd_bo_nhay_gia_dau_nen': ('if ((rc = d_lui(&D, i, o, o)) != 0) goto xong;       /* nhay gia luc mo nen */',
                              'rc = 0;', False, "duong_di"),
    'dd_treo_bo_gia_mo': ('double treo_bar = d_treo_tai(&D, o);',
                         'double treo_bar = 0.0;', False, "duong_di"),
    'dd_tia_chap_1_lenh': ('if (D->tia && D->v.n >= 2 &&',
                          'if (D->tia && D->v.n >= 1 &&', False, "duong_di"),
    'dd_tang_max_bo': ('if (D->v.n > D->tang_max) D->tang_max = D->v.n;',
                      ';', False, "duong_di"),
    'dd_so_tang_khong_ve_1_khi_chot': ('for (int64_t k = 0; k < D->v.n; k++) ghi_dong(&D->g, i, e, va[k].id, 0);\n            D->so_tang = 1;',
                                      'for (int64_t k = 0; k < D->v.n; k++) ghi_dong(&D->g, i, e, va[k].id, 0);', False, "duong_di"),
    'dd_tia_het_ro_khong_mo_lai': ('            if (D->v.n == 0) {                               /* tia het ca ro -> mo lai mot lenh moi, ladder ve 0 */\n                D->so_tang = 1;\n                if ((rc = d_mo_lenh(D, i, e, 0, 1)) != 0) return rc;\n            }',
                                  '            if (D->v.n == 0) {\n                D->so_tang = 1;\n            }', False, "duong_di"),
    'dd_tp_tien_chia_hop': ('mtp = tb + s * D->nguong_tien / (D->hop * tong);',
                           'mtp = tb + s * D->nguong_tien / tong;', False, "duong_di"),
    'dd_tb_khong_trong_so': ('double tb = sw / tong;',
                            'double tb = sw / (double)D->v.n;', False, "duong_di"),
    'dd_tia_trung_binh_sai': ('ps = (pc->g * pc->l + pd->g * pd->l) / (pc->l + pd->l) + s * D->bien_cap * D->pip;',
                             'ps = (pc->g + pd->g) / 2.0 + s * D->bien_cap * D->pip;', False, "duong_di"),
}


@pytest.mark.skipif(not LINUX, reason="so BANG tung bit chi chac chan tren Linux (libm cua pow)")
@pytest.mark.parametrize("ten", sorted(_DOT_BIEN))
def test_dot_bien_bi_tu_kiem_hoac_khop_chinh_xac_bat(nhan_sach, monkeypatch, tmp_path, ten):
    """Ban dot bien cua luoi_nhan.c PHAI bi bat: boi tu kiem (nhan bi bo) hoac boi so sanh chinh xac tren kich ban ngau nhien. Neu
    mot ban lot qua ca hai, bo kiem dang mu o cho do - them ca vao `_CA_BIEN` truoc khi sua tiep."""
    goc, moi, can_312, mo_hinh = _DOT_BIEN[ten]
    if can_312 and sys.version_info < (3, 12):
        pytest.skip("duong cong Kahan chi chay tren Python >= 3.12")
    nguon = LN.NGUON_C.read_text(encoding="utf-8")
    assert nguon.count(goc) == 1, "doan '%s' khong con DUY NHAT trong luoi_nhan.c: cap nhat _DOT_BIEN" % goc
    bien = tmp_path / "luoi_nhan.c"
    bien.write_text(nguon.replace(goc, moi), encoding="utf-8")
    monkeypatch.setattr(LN, "NGUON_C", bien)
    if LN.lay_nhan() is None:                                # tu kiem da chan
        assert "TU KIEM KHONG KHOP" in LN.trang_thai()["ly_do"], LN.trang_thai()["ly_do"]
        return
    for seed in (1, 2, 3, 4):
        for hi, lo, cl, sp, dem, ts, qc in _so_ngau_nhien(seed, 8, mo_hinh=mo_hinh):
            for chieu in (1, -1):
                r = LN.mot_ro(hi, lo, cl, sp, dem, chieu, ts, qc, [])
                if r is None:
                    return
                a = _py(hi, lo, cl, sp, dem, chieu, ts, qc)
                if not LN.so_sanh_ket_qua(a, _c(hi, lo, cl, sp, dem, chieu, ts, qc), 0.0, 0.0)[0]:
                    return                                   # so sanh chinh xac bat duoc
    pytest.fail("ban dot bien '%s' LOT qua ca tu kiem lan so sanh chinh xac" % ten)


def _moi_truong_asan():
    """(lenh dich, duong dan libasan) de dich nhan voi ASan + UBSan va nap vao Python KHONG-ASan bang LD_PRELOAD; None neu may khong co."""
    if not sys.platform.startswith("linux"):
        return None
    for cc in ("gcc", "cc"):
        p = shutil.which(cc)
        if not p:
            continue
        try:
            r = subprocess.run([p, "-print-file-name=libasan.so"], capture_output=True, text=True, timeout=30)
        except Exception:
            continue
        so = r.stdout.strip()
        if r.returncode == 0 and os.path.isabs(so) and os.path.exists(so):
            return p, so
    return None


_CHAY_ASAN = r"""
import sys
import pytest
from nhan import luoi_nhan as LN
ok = LN.lay_nhan() is not None and LN.trang_thai()["trinh_bien"] == "env"
print("ASAN_TRANG_THAI", ok, LN.trang_thai()["ly_do"], flush=True)
if not ok:
    sys.exit(3)
# -s: KHONG de pytest bat stderr - ASan ghi bao cao roi _exit(86), pytest chua kip in thi bao cao mat
sys.exit(pytest.main(["-q", "-x", "-s", "-p", "no:cacheprovider", "test_luoi_nhan.py", "-k", sys.argv[1]]))
"""
# test_luoi_nhan chay lai CHINH NO duoi ASan: bo cac test de quy / dich lai / do toc do (ASan lam cham C vai lan)
_LOAI_TRU_ASAN = "not asan and not dot_bien and not nhanh_hon and not dich_vao_cache and not tu_kiem_that_bai"


def test_nhan_c_sach_duoi_asan_va_ubsan(tmp_path):
    """Chay lai toan bo test nhan C voi nhan dich bang AddressSanitizer + UndefinedBehaviorSanitizer: tran bo dem, doc/ghi qua bien,
    so nguyen tran, chia 0... Dot bien bang 03/10: `head + n >= cap` doi thanh `>` ghi lo 1 phan tu ra khoi bo dem ma KHONG test nao
    thay (heap nho khong sap) - chi ASan thay. Can gcc + libasan (Linux); khong co thi bo qua."""
    if os.environ.get("LUOI_NHAN_DANG_ASAN"):
        pytest.skip("dang chay ben trong ban ASan")
    if LN.che_do() == "py":
        pytest.skip("LUOI_NHAN=py")
    mt = _moi_truong_asan()
    if mt is None:
        pytest.skip("khong co gcc + libasan")
    cc, libasan = mt
    env = dict(os.environ)
    env.update(LUOI_NHAN_CC="%s -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -g" % cc,
               LUOI_NHAN_CACHE=str(tmp_path / "cache_asan"), LUOI_NHAN_DANG_ASAN="1", LUOI_NHAN="auto",
               LD_PRELOAD=libasan, ASAN_OPTIONS="detect_leaks=0:exitcode=86", UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
    r = subprocess.run([sys.executable, "-c", _CHAY_ASAN, _LOAI_TRU_ASAN], cwd=str(Path(__file__).resolve().parent), env=env,
                       capture_output=True, text=True, timeout=600)
    ra = (r.stdout or "") + "\n" + (r.stderr or "")
    # CHI bo qua khi chua toi luc nhan nap xong (loi moi truong). Nhan da nap ma tien trinh chet / test hong = THAT BAI, khong bao gio skip:
    # ASan thoat voi ma 86, tin hieu (am) cung la hong that.
    if "AddressSanitizer" in ra or "runtime error" in ra or r.returncode == 86 or r.returncode < 0:
        i = max(ra.find("ERROR: AddressSanitizer"), ra.find("runtime error"))      # dau bao cao, khong phai duoi stack Python
        pytest.fail("nhan C hong duoi ASan/UBSan (ma %s):\n%s" % (r.returncode, ra[max(0, i - 300): i + 2500] if i >= 0 else ra[-3000:]))
    m = re.search(r"ASAN_TRANG_THAI (True|False) (.*)", ra)
    if m is None:
        pytest.skip("khong khoi dong duoc tien trinh ASan (moi truong): " + ra[-600:])
    if m.group(1) == "False":
        if "TU KIEM KHONG KHOP" in m.group(2):
            pytest.fail("nhan dich voi ASan KHONG khop Python: " + m.group(2))
        pytest.skip("khong dich / nap duoc nhan ASan (moi truong): " + m.group(2)[:600])
    assert r.returncode == 0, "test nhan C that bai duoi ASan (ma %s):\n%s" % (r.returncode, ra[-4000:])


# ------------------------------------------------------------------ HIEU NANG + DA LUONG
@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_nhan_c_nhanh_hon_python_it_nhat_10_lan(nhan, mo_hinh):
    """Do that nho (20.000 bar). Do tren may that cho ~130 lan; 10 lan la san de khong flaky tren may cham/dang tai."""
    rng = np.random.default_rng(7)
    n = 20_000
    cl = np.round(np.cumsum(rng.normal(0.0, 0.0004, n)) * 0.2 + 0.9, 5)
    hi = np.round(cl + np.abs(rng.normal(0.0, 0.0003, n)), 5)
    lo = np.round(cl - np.abs(rng.normal(0.0, 0.0003, n)), 5)
    sp, dem = np.full(n, 0.0001), np.zeros(n)
    dem[96::96] = 1.0
    ts = LU.ThamSo(buoc=30.0, tp=25.0, tran_tang=12, khop_bar=mo_hinh)
    t0 = time.perf_counter()
    LU.mot_ro_chuan(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD)
    t_py = time.perf_counter() - t0
    t_c = min(_gio(lambda: LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, LU.QC_AUDCAD)) for _ in range(5))
    assert t_py / t_c >= 10, "nhan C chi nhanh hon %.1f lan (py %.1f ms, c %.2f ms)" % (t_py / t_c, t_py * 1e3, t_c * 1e3)


def _gio(f) -> float:
    t0 = time.perf_counter()
    f()
    return time.perf_counter() - t0


@pytest.mark.parametrize("mo_hinh", MO_HINH)
def test_da_luong_cho_ket_qua_giong_tuan_tu(nhan, mo_hinh):
    """ctypes nha GIL va nhan C khong co trang thai chung: quet song song cho dung tung to hop (co ghi lenh)."""
    rng = np.random.default_rng(31)
    hi, lo, cl, sp, dem, _, qc = _kich_ban(rng, mo_hinh=mo_hinh)
    to_hop = [LU.ThamSo(buoc=3.0 + 4 * k, tp=2.0 + 3 * (k % 5), tran_tang=3 + k % 9, tia_lenh=(k % 3 == 0), bien_cap=2.0,
                        cap_moi_bar=1 + k % 3, cho_lui=float(k % 4) * 3.0, kieu_lot="nhan" if k % 4 == 1 else "phang",
                        he_so_lot=1.2, khop_bar=mo_hinh) for k in range(24)]

    def chay(ts):
        ev: list = []
        r = LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, qc, ev)
        return r[0].copy(), r[1].copy(), r[2], ev

    tuan_tu = [chay(ts) for ts in to_hop]
    with ThreadPoolExecutor(8) as ex:
        song_song = list(ex.map(chay, to_hop * 2))
    for k, b in enumerate(song_song):
        a = tuan_tu[k % len(to_hop)]
        assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and a[2] == b[2] and a[3] == b[3], k
