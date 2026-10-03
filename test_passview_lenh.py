# -*- coding: utf-8 -*-
"""Passview -> TUNG LENH (`passview.deals_thanh_lenh`): kiem bang du lieu CAI SAN DAP AN.

Passview truoc day dung o muc "kieu quan li la gi" (luoi/scalp...). Muon BOC LUAT va LAM LAI thi can bang tung lenh
(gio mo, gio dong, gia, lot). Tren cloud khong co tai khoan that, nen o day:
  (a) engine `luoi.chay(ghi_lenh=True)` sinh lenh -> doi thanh deal VAO/RA kieu MT5 -> ghep lai -> phai ra DUNG lenh cu;
  (b) tu CSV do di qua `boc_lich_su` va tra lai dung buoc luoi da cai (chuoi passview -> boc chay thong);
  (c) cac truong hop MT5 that hay gap (chot tung phan, netting cong don, dao chieu, nap tien, lich su bi cat, phi);
  (d) bo doc MT5 chi goi ham DOC (khong order_send), bang MT5 gia.

CHUA co: lich su MT5 that qua bo ghep (can may nha + mot tai khoan xem that).
"""
from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from nhan import boc_lich_su as BL
from nhan import luoi as LU
from nhan import passview as PV

LAB = Path(__file__).resolve().parent
PIP = 1e-4


# ----------------------------------------------------------------------------- may sinh du lieu
def _chuoi(n: int = 20000, seed: int = 11, sigma: float = 4e-4, theta: float = 0.02, gia0: float = 0.95) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    x = np.empty(n)
    x[0] = gia0
    for i in range(1, n):
        x[i] = x[i - 1] + theta * (gia0 - x[i - 1]) + rng.normal(0, sigma)
    o = np.r_[x[0], x[:-1]]
    hi = np.maximum(o, x) + np.abs(rng.normal(0, 2e-4, n))
    lo = np.minimum(o, x) - np.abs(rng.normal(0, 2e-4, n))
    idx = pd.date_range("2024-01-01", periods=n, freq="15min")
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": x, "spread": 20.0}, index=idx)


def _epoch(ts) -> int:
    return int(pd.Timestamp(ts).value // 10 ** 9)


def _deals_tu_engine(ln: pd.DataFrame, magic: int = 7, ma: str = "AUDCAD") -> list[dict]:
    """Moi lenh engine -> deal VAO (+ deal RA neu da dong), position_id rieng, ticket tang theo gio nhu MT5 that."""
    deals, ticket = [], 1000
    hang = sorted(range(len(ln)), key=lambda i: _epoch(ln["mo"].iat[i]))
    for i in hang:
        r = ln.iloc[i]
        ticket += 1
        mua = int(r["chieu"]) > 0
        deals.append(dict(time=_epoch(r["mo"]), ticket=ticket, position_id=5000 + i, symbol=ma, type=0 if mua else 1,
                          volume=float(r["lot"]), price=float(r["gia_mo"]), profit=0.0, commission=-0.07, swap=0.0,
                          entry=0, magic=magic, reason=3, comment="grid", sl=0.0, tp=0.0))
    ra = []
    for i in range(len(ln)):
        r = ln.iloc[i]
        if pd.isna(r["dong"]):
            continue
        mua = int(r["chieu"]) > 0
        ra.append(dict(time=_epoch(r["dong"]), position_id=5000 + i, symbol=ma, type=1 if mua else 0,
                       volume=float(r["lot"]), price=float(r["gia_dong"]),
                       profit=float((r["gia_dong"] - r["gia_mo"]) * (1 if mua else -1) * r["lot"] * 100000),
                       commission=0.0, swap=-0.01, entry=1, magic=magic, reason=5, comment="tp", sl=0.0, tp=0.0))
    for d in sorted(ra, key=lambda d: d["time"]):
        ticket += 1
        d["ticket"] = ticket
        deals.append(d)
    deals.sort(key=lambda d: (d["time"], d["ticket"]))
    return deals


def _lenh_chuan(lenh: list[dict]) -> pd.DataFrame:
    d = pd.DataFrame(lenh)
    d["mo"] = pd.to_datetime(d["mo"])
    d["dong"] = pd.to_datetime(d["dong"])
    d["chieu"] = np.where(d["chieu"] == "buy", 1, -1)
    return d.sort_values(["mo", "chieu", "gia_mo", "lot"], kind="stable").reset_index(drop=True)


@pytest.fixture(scope="module")
def chay_engine():
    bar = _chuoi()
    kq = LU.chay(bar, LU.ThamSo(buoc=15, tp=10, tran_tang=12), 1e12, None, ghi_lenh=True)
    return bar, kq.lenh


# ----------------------------------------------------------------------------- (a) vong tron engine
def test_vong_tron_engine_ra_dung_lenh_da_cai(chay_engine):
    _bar, ln = chay_engine
    assert len(ln) > 100 and ln["dong"].isna().sum() >= 1          # co ca lenh chua dong
    kq = PV.deals_thanh_lenh(_deals_tu_engine(ln))
    assert kq["khong_phai_lenh"] == 0 and kq["ra_mo_coi"] == 0
    assert kq["chua_dong"] == int(ln["dong"].isna().sum())
    ra = _lenh_chuan(kq["lenh"])
    goc = ln.copy()
    goc["chieu"] = goc["chieu"].astype(int)
    goc = goc.sort_values(["mo", "chieu", "gia_mo", "lot"], kind="stable").reset_index(drop=True)
    assert len(ra) == len(goc)
    assert (ra["mo"].values == goc["mo"].values).all()
    assert ra["dong"].equals(goc["dong"].astype("datetime64[ns]")) or (ra["dong"].fillna(pd.Timestamp(0)).values ==
                                                                        goc["dong"].fillna(pd.Timestamp(0)).values).all()
    assert (ra["chieu"].values == goc["chieu"].values).all()
    assert np.allclose(ra["lot"], goc["lot"]) and np.allclose(ra["gia_mo"], goc["gia_mo"])
    assert np.allclose(ra["gia_dong"].astype(float).fillna(-1), goc["gia_dong"].astype(float).fillna(-1))
    dong = ra[ra["dong"].notna()]
    assert (dong["loi"].astype(float) != 0).all()                    # lai rong da gom phi / swap
    assert set(ra["magic"]) == {7} and set(ra["ma"]) == {"AUDCAD"}


def test_vong_tron_qua_csv_va_boc_ra_dung_buoc_luoi(chay_engine, tmp_path):
    """Chuoi dau-cuoi: deal -> lenh -> CSV -> boc_lich_su (chinh bo boc cua `b nc cc boc_lich_su`) -> tham so luoi da cai."""
    _bar, ln = chay_engine
    kq = PV.deals_thanh_lenh(_deals_tu_engine(ln))
    tep = PV.ghi_lenh_csv(kq["lenh"], "ab12cd34", thu_muc=tmp_path)
    assert [t["ma"] for t in tep] == ["AUDCAD"] and tep[0]["so_lenh"] == len(ln) and tep[0]["magic"] is None
    h = BL.doc_tep(tmp_path / "ab12cd34_AUDCAD.csv")
    ra = BL.boc(h, bar=None, pip=PIP, ma="AUDCAD", spread_pip=0.0)
    assert ra["trang_thai"] == "DAT" and ra["loai"] == "luoi_dca", ra.get("loai")
    assert ra["tham_so"]["buoc"] == pytest.approx(15, rel=0.05)
    assert ra["lich_su"]["so_lenh"] == len(ln)


# ----------------------------------------------------------------------------- (c) truong hop MT5 that
def _d(t, loai, entry, vol, gia, pid=1, profit=0.0, **kw):
    d = dict(time=1_700_000_000 + t, symbol="EURUSD", type=loai, volume=vol, price=gia, profit=profit, entry=entry,
             position_id=pid, commission=0.0, swap=0.0, magic=0, reason=-1, comment="", sl=0.0, tp=0.0)
    d.update(kw)
    return d


def test_chot_tung_phan_thanh_hai_lenh_cung_gia_mo():
    kq = PV.deals_thanh_lenh([
        _d(0, 0, 0, 0.3, 1.10, ticket=1, commission=-3.0),
        _d(60, 1, 1, 0.1, 1.11, profit=10.0, ticket=2),
        _d(120, 1, 1, 0.2, 1.12, profit=40.0, ticket=3, reason=5)])
    a, b = kq["lenh"]
    assert (a["lot"], b["lot"]) == (0.1, 0.2) and a["gia_mo"] == b["gia_mo"] == 1.10
    assert (a["gia_dong"], b["gia_dong"]) == (1.11, 1.12) and kq["chua_dong"] == 0
    # phi VAO (-3) chia theo ty le lot: -1 va -2, nen tong lai rong = tong profit + tong phi
    assert a["loi"] == pytest.approx(10.0 - 1.0) and b["loi"] == pytest.approx(40.0 - 2.0)
    assert b["ly_do_dong"] == "tp"


def test_netting_cong_don_moi_lenh_giu_gia_vao_rieng():
    kq = PV.deals_thanh_lenh([
        _d(0, 0, 0, 0.1, 1.10, ticket=1),
        _d(10, 0, 0, 0.1, 1.09, ticket=2),
        _d(20, 1, 1, 0.2, 1.12, profit=50.0, ticket=3)])
    gia = sorted((x["gia_mo"], x["lot"], x["loi"]) for x in kq["lenh"])
    assert [g[0] for g in gia] == [1.09, 1.10] and all(g[1] == pytest.approx(0.1) for g in gia)
    assert sum(g[2] for g in gia) == pytest.approx(50.0)           # lai deal RA chia theo ty le lot khop


def test_deal_dao_chieu_dong_het_lenh_cu_va_mo_lenh_moi_phan_du():
    kq = PV.deals_thanh_lenh([
        _d(0, 0, 0, 0.1, 1.10, ticket=1),
        _d(30, 1, 2, 0.3, 1.12, profit=20.0, ticket=2),           # dong 0.1 mua, mo 0.2 ban
        _d(90, 0, 1, 0.2, 1.11, profit=20.0, ticket=3)])
    hs = sorted(kq["lenh"], key=lambda x: x["mo"])
    assert [(x["chieu"], round(x["lot"], 6)) for x in hs] == [("buy", 0.1), ("sell", 0.2)]
    assert hs[1]["gia_mo"] == 1.12 and hs[1]["gia_dong"] == 1.11 and hs[0]["gia_dong"] == 1.12
    # loi deal dao chieu chi thuoc phan DONG lenh cu (0.1/0.3 cua 20)
    assert hs[0]["loi"] == pytest.approx(20.0 / 3, rel=1e-6)


def test_bo_nap_rut_va_dem_ra_mo_coi_va_lenh_chua_dong():
    kq = PV.deals_thanh_lenh([
        dict(time=1_699_999_000, symbol="", type=2, volume=0.0, price=0.0, profit=1000.0, entry=0, position_id=0),
        _d(0, 1, 1, 0.5, 1.10, pid=99, profit=5.0, ticket=2),      # RA ma lich su khong co VAO (bi cat)
        _d(10, 0, 0, 0.1, 1.10, pid=7, ticket=3)])                 # van dang mo
    assert kq["khong_phai_lenh"] == 1 and kq["ra_mo_coi"] == 1 and kq["chua_dong"] == 1
    (x,) = kq["lenh"]
    assert x["dong"] is None and x["gia_dong"] is None and x["loi"] is None


def test_lenh_vao_va_ra_cung_giay_van_ghep_dung():
    kq = PV.deals_thanh_lenh([
        _d(5, 1, 1, 0.1, 1.2, pid=3, profit=1.0, ticket=9),         # RA ghi truoc VAO trong mang
        _d(5, 0, 0, 0.1, 1.1, pid=3, ticket=8)])
    (x,) = kq["lenh"]
    assert x["dong"] == x["mo"] and x["gia_mo"] == 1.1 and x["gia_dong"] == 1.2 and kq["ra_mo_coi"] == 0


def test_khong_co_position_id_ghep_theo_ma():
    kq = PV.deals_thanh_lenh([
        _d(0, 0, 0, 0.1, 1.10, pid=0), _d(5, 1, 0, 0.1, 1.30, pid=0),      # mua va ban cung ma: hai lenh KHAC chieu
        _d(60, 1, 1, 0.1, 1.11, pid=0, profit=1.0), _d(70, 0, 1, 0.1, 1.29, pid=0, profit=1.0)])
    d = {x["chieu"]: x for x in kq["lenh"]}
    assert d["buy"]["gia_dong"] == 1.11 and d["sell"]["gia_dong"] == 1.29 and kq["ra_mo_coi"] == 0


def test_ra_bang_lenh_doi_ung_entry3_cung_la_deal_ra():
    kq = PV.deals_thanh_lenh([
        _d(0, 0, 0, 0.1, 1.10, pid=1, ticket=1), _d(0, 1, 0, 0.1, 1.10, pid=2, ticket=2),
        _d(50, 1, 3, 0.1, 1.11, pid=1, profit=1.0, ticket=3), _d(50, 0, 3, 0.1, 1.11, pid=2, profit=-1.0, ticket=4)])
    assert len(kq["lenh"]) == 2 and kq["chua_dong"] == 0 and kq["ra_mo_coi"] == 0


# ----------------------------------------------------------------------------- tep CSV
def _nhieu_lenh(ma, magic, n):
    return [dict(mo="2024-01-01 00:%02d:00" % (i % 60), dong="2024-01-01 01:00:00", chieu="buy", lot=0.1, gia_mo=1.1,
                 gia_dong=1.2, loi=1.0, sl=None, tp=None, ma=ma, magic=magic, position_id=i, ly_do_dong="tp",
                 ghi_chu="x, \"y\"") for i in range(n)]


def test_ghi_lenh_csv_tach_ma_va_magic_va_khong_lo_so_tai_khoan(tmp_path):
    lenh = _nhieu_lenh("EURUSD", 1, 35) + _nhieu_lenh("EURUSD", 2, 40) + _nhieu_lenh("GBPUSD", 0, 31) + \
        _nhieu_lenh("USDJPY", 0, 5)
    ma = PV.ma_tai_khoan(12345678, "XMGlobal-Real 9")
    tep = PV.ghi_lenh_csv(lenh, ma, thu_muc=tmp_path)
    ten = sorted(Path(t["tep"]).name for t in tep)
    assert ten == [ma + "_EURUSD.csv", ma + "_EURUSD_m1.csv", ma + "_EURUSD_m2.csv", ma + "_GBPUSD.csv"]
    assert not any("12345678" in t["tep"] for t in tep) and "USDJPY" not in "".join(ten)    # < toi_thieu lenh: khong ghi
    h = BL.chuan_hoa(tmp_path / (ma + "_EURUSD.csv"))
    assert len(h) == 75 and h.attrs["so_bo"] == 0 and set(h["chieu"]) == {1}


def test_tep_trong_lab_dung_duong_tuong_doi(tmp_path, monkeypatch):
    """`b nc cc boc_lich_su {"tep": ...}` chi nhan tep NAM TRONG lab/: duong dan ghi ra phai tuong doi voi lab/."""
    monkeypatch.setattr(PV, "LAB", tmp_path)
    tep = PV.ghi_lenh_csv(_nhieu_lenh("EURUSD", 0, 31), "aa", thu_muc=tmp_path / "du_lieu_cao" / "lenh")
    assert tep[0]["tep"] == "du_lieu_cao/lenh/aa_EURUSD.csv"


# ----------------------------------------------------------------------------- (d) bo doc MT5 chi DOC
class _MT5Gia:
    """Doi tuong thay module MetaTrader5: ghi lai ham nao duoc goi."""

    def __init__(self):
        self.goi = []

    def account_info(self):
        self.goi.append("account_info")
        return SimpleNamespace(login=1, server="XMGlobal-Real 9", balance=1.0, equity=1.0, profit=0.0, currency="USD",
                               trade_mode=0)

    def history_deals_get(self, tu, den):
        self.goi.append("history_deals_get")
        return [SimpleNamespace(time=10, symbol="EURUSD", type=0, volume=0.1, price=1.1, profit=0.0, entry=0, order=77,
                                position_id=5, magic=3, commission=-0.5, swap=0.0, reason=3, comment="g1", ticket=1,
                                time_msc=10_000),
                SimpleNamespace(time=20, symbol="EURUSD", type=1, volume=0.1, price=1.2, profit=9.0, entry=1, order=88,
                                position_id=5, magic=3, commission=0.0, swap=-0.1, reason=5, comment="tp", ticket=2,
                                time_msc=20_000)]

    def history_orders_get(self, tu, den):
        self.goi.append("history_orders_get")
        return [SimpleNamespace(ticket=77, sl=1.05, tp=1.15), SimpleNamespace(ticket=88, sl=0.0, tp=0.0)]

    def positions_get(self):
        self.goi.append("positions_get")
        return [SimpleNamespace(symbol="EURUSD", volume=0.1, type=0, profit=1.0, magic=3)]


def test_keo_tu_mt5_chi_goi_ham_doc_va_gan_sl_tp_vao_deal_vao():
    mt5 = _MT5Gia()
    kq = PV.keo_tu_mt5(mt5)
    assert set(mt5.goi) <= {"account_info", "history_deals_get", "history_orders_get", "positions_get"}
    vao, ra = kq["deals"]
    assert (vao["sl"], vao["tp"]) == (1.05, 1.15) and (ra["sl"], ra["tp"]) == (0.0, 0.0)
    assert vao["magic"] == 3 and vao["position_id"] == 5 and vao["comment"] == "g1" and ra["reason"] == 5
    (x,) = PV.deals_thanh_lenh(kq["deals"])["lenh"]
    assert x["sl"] == 1.05 and x["tp"] == 1.15 and x["magic"] == 3 and x["loi"] == pytest.approx(9.0 - 0.1 - 0.5)
    assert kq["account"]["loai"] == "DEMO"


def test_ma_nguon_chi_goi_dung_ham_doc_cua_mt5():
    """Moi loi goi `mt5.<ham>(` trong passview.py phai nam trong danh sach DOC. `order_send` khong bao gio duoc xuat hien."""
    src = (LAB / "nhan" / "passview.py").read_text(encoding="utf-8")
    goi = set(re.findall(r"\bmt5\.(\w+)\(", src))
    assert goi <= {"initialize", "shutdown", "last_error", "account_info", "history_deals_get", "history_orders_get",
                   "positions_get"}, goi
    assert "order_send(" not in src and "order_check(" not in src


# ----------------------------------------------------------------------------- kho tai khoan
def test_cap_nhat_va_ma_tai_khoan_khop_voi_link_nguon(tmp_path, monkeypatch):
    from nhan import link_nguon as LN
    monkeypatch.setattr(PV, "KHO", tmp_path / "passview.json")
    assert PV.luu([{"login": 12345678, "mat_khau": "abc123", "server": "XMGlobal-Real 9"}], nguon="t") == 1
    assert PV.cap_nhat(12345678, "XMGlobal-Real 9", trang_thai="DA_DOC", so_lenh=12) is True
    assert PV.cap_nhat(1, "khac") is False
    (t,) = PV.danh_sach()
    assert t["trang_thai"] == "DA_DOC" and t["so_lenh"] == 12 and t["mat_khau"] == "abc123"
    vb = "Investor password: abc123 Login: 12345678 Server: XMGlobal-Real 9"
    (a,) = LN.trich_tu_van_ban(vb)["tai_khoan_xem"]
    assert a["server"] == "XMGlobal-Real 9" and a["ma"] == PV.ma_tai_khoan(12345678, "XMGlobal-Real 9")
    assert not list(tmp_path.glob("*.tmp"))                         # ghi nguyen tu: khong de tep tam


# ----------------------------------------------------------------------------- ten may chu that
@pytest.mark.parametrize("van_ban,ky_vong", [
    ("XMGlobal-Real 31", "XMGlobal-Real 31"),                 # XM (san pho bien nhat o VN): co dau cach truoc so
    ("Exness-Real8", "Exness-Real8"), ("FBS-Real-3", "FBS-Real-3"), ("XMGlobal-MT5 7", "XMGlobal-MT5 7"),
    ("ICMarketsSC-MT5-4", "ICMarketsSC-MT5-4"), ("Exness-MT5Real8", "Exness-MT5Real8"),
    ("HFMarketsGlobal-Live2", "HFMarketsGlobal-Live2"), ("VantageInternational-Live 2", "VantageInternational-Live 2"),
    # tu ke ben KHONG duoc bi nuot vao ten may chu (loi cu: "Exness-Real8 Login")
    ("Server: Exness-Real8 Login: 123456", "Exness-Real8"), ("Server XMGlobal-MT5 7 Login 123", "XMGlobal-MT5 7"),
    ("XMGlobal-MT5 12345678", "XMGlobal-MT5"),                # so tai khoan lien sau KHONG phai so may chu
])
def test_ten_may_chu_that_bat_dung_va_khong_nuot_tu_ke_ben(van_ban, ky_vong):
    assert PV._SERVER.findall(van_ban) == [ky_vong]


@pytest.mark.parametrize("van_ban", ["Controllable Realism", "and Live Trading", "Real 31", "my-real life", "Tickmill-Live"])
def test_tu_thuong_khong_bi_nham_la_may_chu(van_ban):
    assert PV._SERVER.findall(van_ban) == []


def test_bai_mot_dong_login_pass_server_ra_dung_server():
    """Dang dan pho bien nhat: tat ca tren mot dong. Truoc khi sua, server ra 'Exness-Real8 Login' va dang nhap hong am tham."""
    (t,) = PV.boc_tai_khoan("Investor view only - Server: Exness-Real8 Login: 87654321 Password: Xy12ab34")
    assert (t["login"], t["server"], t["mat_khau"]) == (87654321, "Exness-Real8", "Xy12ab34")
