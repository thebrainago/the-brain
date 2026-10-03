# -*- coding: utf-8 -*-
"""Kiem `nc_thi_nghiem._he_so_lot_tai_tran` ban NHANH (ranh gioi Pareto cua cac cap dinh/day) so voi ban CU.

Ban cu tinh lai sut giam tren ca duong von 80 lan chia doi (139 ms o 190.000 bar - 88% thoi gian mot lan `danh_gia_luoi`
sau khi nhan C lam `luoi.chay` nhanh x89). Ban moi chi giu cac cap khong bi loai. Cau hoi duy nhat o day: KET QUA CO Y
HET khong - nen ban cu duoc chep NGUYEN VAN xuong duoi lam tham phan, so bang `==` (khong dung sai).
"""
import numpy as np
import pytest

from nhan import luoi as LU
from nhan import nc_thi_nghiem as TN
from nhan import vao_lenh as VL


def _cu(equity, von, dd_tran=TN.DD_TRAN, k_toi_da=1000.0):
    """Ban cu, chep nguyen van truoc khi toi uu (03/10/2026). KHONG sua: day la phep do."""
    e = np.asarray(equity, float)
    if len(e) < 2 or not np.all(np.isfinite(e)) or von <= 0:
        return None
    muc = float(dd_tran) - 1e-3

    def dd(k):
        v = von + k * (e - von)
        if np.any(v <= 0):
            return 1.0
        return VL._sut_giam(v)

    if dd(k_toi_da) < muc:
        return k_toi_da
    lo, hi = 0.0, k_toi_da
    for _ in range(80):
        giua = 0.5 * (lo + hi)
        if dd(giua) >= muc:
            hi = giua
        else:
            lo = giua
    return lo if lo > 0 else None


def _duong(kieu, n, rng):
    if kieu == "di_len":
        return 10000 + np.cumsum(rng.normal(3, 40, n))
    if kieu == "bien_dong_lon":
        return 10000 + np.cumsum(rng.normal(-1, 80, n))          # co the xuong am
    if kieu == "chi_tang":
        return 10000 + np.cumsum(np.abs(rng.normal(2, 1, n)))     # sut giam 0
    if kieu == "phang":
        return np.full(n, 10000.0)
    if kieu == "nguyen_nhieu_hoa":
        return np.round(10000 + np.cumsum(rng.normal(0, 20, n)))  # nhieu gia tri BANG nhau
    if kieu == "bac_thang":
        buoc = rng.integers(0, 2, n) * rng.normal(0, 60, n)
        return 10000 + np.cumsum(buoc)                              # co doan phang dai
    if kieu == "chay_tai_khoan":
        e = 10000 + np.cumsum(rng.normal(-4, 60, n))
        e[n // 2:] = 0.0                                             # nhu luoi.chay khi bi stop-out
        return e
    if kieu == "chi_giam":
        return 10000 - np.cumsum(np.abs(rng.normal(0.5, 0.2, n)))
    raise AssertionError(kieu)


KIEU = ["di_len", "bien_dong_lon", "chi_tang", "phang", "nguyen_nhieu_hoa", "bac_thang", "chay_tai_khoan", "chi_giam"]


@pytest.mark.parametrize("kieu", KIEU)
@pytest.mark.parametrize("n", [2, 3, 7, 60, 1500, 20000])
def test_ban_nhanh_ra_y_het_ban_cu(kieu, n):
    for seed in range(6):
        e = _duong(kieu, n, np.random.default_rng(1000 * seed + n))
        for von in (10000.0, 1.0, 12345.678):
            moi, cu = TN._he_so_lot_tai_tran(e, von), _cu(e, von)
            assert moi == cu, "kieu=%s n=%d seed=%d von=%s: moi=%r cu=%r" % (kieu, n, seed, von, moi, cu)


@pytest.mark.parametrize("dd_tran,k_max", [(0.5, 1000.0), (0.8, 5.0), (0.999, 1000.0), (0.05, 50.0), (0.8, 1.0)])
def test_ban_nhanh_ra_y_het_voi_tran_va_k_toi_da_khac(dd_tran, k_max):
    for seed in range(8):
        rng = np.random.default_rng(seed)
        e = _duong(KIEU[seed % len(KIEU)], 3000, rng)
        assert TN._he_so_lot_tai_tran(e, 10000.0, dd_tran, k_max) == _cu(e, 10000.0, dd_tran, k_max)


def test_dau_vao_khong_tinh_duoc_van_tra_none_nhu_cu():
    ok = np.array([100.0, 90.0, 95.0])
    assert TN._he_so_lot_tai_tran(np.array([100.0]), 100.0) is None            # < 2 diem
    assert TN._he_so_lot_tai_tran(np.array([]), 100.0) is None
    assert TN._he_so_lot_tai_tran(np.array([100.0, np.nan, 90.0]), 100.0) is None
    assert TN._he_so_lot_tai_tran(np.array([100.0, np.inf, 90.0]), 100.0) is None
    assert TN._he_so_lot_tai_tran(ok, 0.0) is None and TN._he_so_lot_tai_tran(ok, -5.0) is None


def _che_do_cua_k(e, von, k, k_max=1000.0):
    """Kiem k la hop le va xep vao MOT trong ba che do: bi tran k, DD cham tran truoc, hay tai khoan chet truoc."""
    muc = TN.DD_TRAN - 1e-3
    v = von + k * (e - von)
    assert v.min() > 0 and VL._sut_giam(v) < muc, "k tim duoc phai la he so SONG va chua cham tran DD"
    if k == k_max:
        return "tran_k"
    v2 = von + k * (1 + 1e-6) * (e - von)           # nhich k len mot chut: phai vuot bien
    if v2.min() <= 0:
        return "chet"
    assert VL._sut_giam(v2) >= muc, "k khong phai bien: nhich len van song va chua cham tran"
    return "tran_dd"


def test_he_so_tim_duoc_la_BIEN_tren_duong_von_day_du():
    """Phep kiem ngoai, dung CHINH `vao_lenh._sut_giam` tren ca duong von (khong qua ranh gioi). Co ba che do that va test phai
    thay du ca ba, neu khong no chi kiem mot nhanh: (1) DD cham tran 80% truoc, (2) day cua duong von (vd bar dau) lam tai
    khoan chet truoc, (3) duong von qua em nen k len toi tran k_toi_da."""
    dem = {"tran_dd": 0, "chet": 0, "tran_k": 0}
    # (troi, bien dong, so diem, gia tri ep cho diem dau hoac None): diem dau ep thap = day nam o DAU duong von, tai khoan
    # chet truoc khi DD kip cham tran - dung hinh dang cua loi bar-0 cu cua luoi.py (equity[0] = von - TONG spread)
    gia_dinh = [(3, 40, 4000, None), (-1, 80, 3000, None), (2, 50, 6000, None), (0.5, 5, 3000, None),
                (0.5, 5, 3000, 9200.0)]
    for h, (troi, bd, n, dau) in enumerate(gia_dinh):
        rng = np.random.default_rng(3 + h)
        for _ in range(15):
            e = 10000 + np.cumsum(rng.normal(troi, bd, n))
            if dau is not None:
                e[0] = dau
            k = TN._he_so_lot_tai_tran(e, 10000.0)
            if k is None:
                continue
            dem[_che_do_cua_k(e, 10000.0, k)] += 1
    assert all(v > 0 for v in dem.values()), "can du ba che do de phep kiem co y nghia: %s" % dem


# ---------------------------------------------------------------- RANH GIOI: du va gon
def _cap_cuc_dai_vet_can(e, von, k):
    v = von + k * (e - von)
    best = 0.0
    for i in range(len(v)):
        for j in range(i, len(v)):
            best = max(best, 1.0 - v[j] / max(v[i], 1e-12))
    return best


def test_ranh_gioi_du_cho_sut_giam_cuc_dai_voi_moi_k():
    """DU: voi moi k > 0, max tren ranh gioi = max tren MOI cap (i <= j) (vet can O(n^2) tren duong von nho)."""
    rng = np.random.default_rng(11)
    for kieu in KIEU:
        for _ in range(4):
            e = _duong(kieu, 40, rng)
            a, b = TN._cap_sut_giam_ung_vien(e)
            for k in (0.01, 0.3, 1.0, 2.5, 17.0):
                v = 10000.0 + k * (e - 10000.0)
                if np.any(v <= 0):
                    continue
                va, vb = 10000.0 + k * (a - 10000.0), 10000.0 + k * (b - 10000.0)
                assert float(np.max(1.0 - vb / np.maximum(va, 1e-12))) == _cap_cuc_dai_vet_can(e, 10000.0, k)


def test_ranh_gioi_gon_khong_cap_nao_bi_cap_khac_chi_phoi():
    """GON: khong cap nao co dinh <= va day >= cua mot cap khac (neu co thi thua mot cap vo ich)."""
    rng = np.random.default_rng(12)
    for kieu in KIEU:
        e = _duong(kieu, 5000, rng)
        a, b = TN._cap_sut_giam_ung_vien(e)
        assert len(a) == len(b) >= 1
        for s in range(len(a)):
            for t in range(len(a)):
                if s != t:
                    assert not (a[s] >= a[t] and b[s] <= b[t]), "cap %d bi cap %d chi phoi" % (t, s)
        # moi cap that su la (dinh, day sau dinh): day khong cao hon dinh
        assert np.all(b <= a)


def test_ranh_gioi_nho_hon_nhieu_so_voi_so_diem():
    e = 10000 + np.cumsum(np.random.default_rng(1).normal(2, 40, 190_000))
    a, _ = TN._cap_sut_giam_ung_vien(e)
    assert 1 <= len(a) < 0.05 * len(e), len(a)   # < 5% so diem (do: ~1,4%): day moi la ly do toc do tang


def test_ranh_gioi_loai_khoi_hoa_dinh_nhung_day_cao_hon():
    """Ca xac dinh: hai khoi co CUNG dinh 10 nhung day 5 va 6 -> khoi day 6 la hang thua (dinh khong cao hon, day khong thap
    hon). Ca ngau nhien hiem khi sinh dung dinh bang nhau, nen khong co ca nay thi doi `>` thanh `>=` khong ai hay."""
    e = np.array([10.0, 5.0, 10.0, 6.0, 8.0])
    a, b = TN._cap_sut_giam_ung_vien(e)
    assert a.tolist() == [10.0] and b.tolist() == [5.0], (a.tolist(), b.tolist())
    # va ca co hai khoi KHONG thua nhau: day cao hon nhung dinh cao hon han
    a2, b2 = TN._cap_sut_giam_ung_vien(np.array([10.0, 5.0, 20.0, 6.0, 8.0]))
    assert a2.tolist() == [10.0, 20.0] and b2.tolist() == [5.0, 6.0]


# ---------------------------------------------------------------- HE QUA CUA LOI BAR 0 CUA LUOI (sua 03/10/2026)
def _chuoi_hoi_quy(n=6000, seed=7, gia0=0.95):
    import pandas as pd
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


@pytest.mark.parametrize("kw", [dict(buoc=15, tp=10, tran_tang=12), dict(buoc=8, tp=5, tran_tang=12),
                                dict(buoc=10, tp=6, tran_tang=10, che_do="hai_chieu")])
def test_he_so_lot_khong_bi_chan_boi_tong_spread_cua_chuoi(kw):
    """Ban cu cua `luoi.chay` gan equity[0] = von - TONG spread -> tai khoan 'chet' o bar 0 khi k = von / tong spread, nen k bang
    DUNG von / phi_spread o moi cau hinh (do 03/10/2026: 71,51 / 19,33 / 8,41) va cau hinh GIAO DICH NHIEU bi phat theo so lenh
    chu khong theo rui ro. Sau khi sua, k do SUT GIAM (hoac tran k_toi_da) quyet dinh."""
    von = 10000.0
    kq = LU.chay(_chuoi_hoi_quy(), LU.ThamSo(**kw), von, LU.QC_AUDCAD)
    e = np.asarray(kq.duong_equity, float)
    assert int(np.argmin(e)) != 0, "diem thap nhat khong duoc la bar 0"
    k = TN._he_so_lot_tai_tran(e, von)
    assert k is not None and k > 3 * von / kq.phi_spread, (k, von / kq.phi_spread)
    assert _che_do_cua_k(e, von, k) in ("tran_dd", "tran_k")      # khong phai 'chet' (tai khoan chet o day bar dau)
