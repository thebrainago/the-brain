# -*- coding: utf-8 -*-
"""Boc logic tu lich su lenh (`nhan/boc_lich_su.py`) - KIEM BANG DU LIEU CAI SAN DAP AN.

Tren cloud khong co lich su that nao, nen moi phep do o day dung thu DA BIET DAP AN. Ba may sinh lich su, khong may nao
dung chung dong code voi bo boc:
  (a) `luoi.chay(ghi_lenh=True)` - chinh engine luoi (kem nhieu giay le, nhieu gia: lich su that khong sach nhu engine);
  (b) mot EA luoi viet lai THEO TUNG TICK (port cua `ea_LuoiThamChieu.mq5`, ask/bid that, spread that) - kiem ca quy uoc
      spread: lenh MUA mo o ask, dong o bid;
  (c) mot EA vao lenh theo TIN HIEU (`rsi2 < 10`) sinh theo bar bang vong lap rieng.
Bo boc phai tra lai DUNG tham so / gio lech / luat da cai, phat lai khop so ro, VA khong bia luat khi vao lenh ngau nhien
(hieu chuan null: ty le bao dong gia khop muc danh nghia).

Bang chung chua co: bo doc HTML viet theo cau truc bang chung, chua thay mau that; khong co lich su that nao da qua bo boc.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from nhan import boc_lich_su as BL
from nhan import luoi as LU
from nhan import nc_cong_cu as CC
from nhan import nc_dac_trung as DT
from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN
from nhan import ngu_phap as NP

PIP = 1e-4


@pytest.fixture(autouse=True)
def so_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    yield


# ============================================================== MAY SINH DU LIEU (doc lap voi bo boc)
def _chuoi(n: int = 20000, seed: int = 11, sigma: float = 4e-4, theta: float = 0.02, gia0: float = 0.95,
           spread: float = 20.0) -> pd.DataFrame:
    """M15 hoi quy ve gia0 (co viec cho luoi lam), spread (POINT) hang so."""
    rng = np.random.RandomState(seed)
    x = np.empty(n)
    x[0] = gia0
    for i in range(1, n):
        x[i] = x[i - 1] + theta * (gia0 - x[i - 1]) + rng.normal(0, sigma)
    o = np.r_[x[0], x[:-1]]
    hi = np.maximum(o, x) + np.abs(rng.normal(0, 2e-4, n))
    lo = np.minimum(o, x) - np.abs(rng.normal(0, 2e-4, n))
    idx = pd.date_range("2024-01-01", periods=n, freq="15min")
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": x, "spread": float(spread)}, index=idx)


def _lich_su_tu_engine(ln: pd.DataFrame, seed: int = 0, nhieu_s: int = 40, ma: str = "AUDCAD") -> pd.DataFrame:
    """Bang lenh engine -> 'lich su that': moi moc gio lech MOT so giay ngau nhien (mo lai cung moc voi dong thi van trung
    giay - dung nhu EA that), gia nhieu 0,2 pip, chieu thanh chu buy/sell."""
    rng = np.random.RandomState(seed)
    d = ln.copy()
    tat = pd.unique(pd.concat([d["mo"], d["dong"].dropna()]))
    g = {t: rng.randint(1, nhieu_s) for t in tat}
    d["mo"] = d["mo"] + pd.to_timedelta(d["mo"].map(g), unit="s")
    d["dong"] = d["dong"] + pd.to_timedelta(d["dong"].map(g).fillna(0), unit="s")
    d["gia_mo"] = d["gia_mo"] + rng.normal(0, 0.2e-4, len(d)).round(5)
    d["gia_dong"] = d["gia_dong"] + rng.normal(0, 0.2e-4, len(d)).round(5)
    d["chieu"] = np.where(d["chieu"] > 0, "buy", "sell")
    return d[["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong"]].assign(ma=ma)


def _chay_engine(ts_kw: dict, n: int = 20000, seed: int = 11) -> tuple[pd.DataFrame, pd.DataFrame]:
    bar = _chuoi(n=n, seed=seed)
    kq = LU.chay(bar, LU.ThamSo(**ts_kw), 1e12, None, ghi_lenh=True)
    return bar, _lich_su_tu_engine(kq.lenh)


def _duong_tick(n_bar: int, tpb: int, seed: int, gia0: float = 0.95, hoi_quy_bar: float = 0.02, sd_bar: float = 4e-4):
    rng = np.random.RandomState(seed)
    n = n_bar * tpb
    sd, k = sd_bar / np.sqrt(tpb), hoi_quy_bar / tpb
    x = np.empty(n)
    x[0] = gia0
    z = rng.normal(0, sd, n)
    for i in range(1, n):
        x[i] = x[i - 1] + k * (gia0 - x[i - 1]) + z[i]
    return x


def _bar_tu_tick(bid: np.ndarray, tpb: int, spread_pts: float) -> pd.DataFrame:
    b = bid.reshape(-1, tpb)
    idx = pd.date_range("2024-01-01", periods=b.shape[0], freq="15min")
    return pd.DataFrame({"open": b[:, 0], "high": b.max(1), "low": b.min(1), "close": b[:, -1],
                         "spread": np.full(b.shape[0], float(spread_pts))}, index=idx)


def _ea_tung_tick(bid: np.ndarray, tpb: int, spread: float, step_pips: float, tp_pips: float, max_lv: int, mode: int,
                  lot: float, mult: float, pip: float = PIP, ma: str = "AUDCAD") -> pd.DataFrame:
    """EA luoi viet LAI theo tung tick (logic `ea_LuoiThamChieu.mq5`): moi tick -> kiem TP (phia may chu) -> vao lenh dau /
    them tang khi gia di nguoc >= buoc. MUA mo o ASK, dong o BID; BAN nguoc lai. TP dat tu GIA MO TRUNG BINH (co trong so lot)
    +/- tp pip, tru/cong spread (de TP tinh tren bid/ask dung nhu EA that). Tra DANH SACH LENH (mo, dong, gia) - thu engine luoi
    khong he biet: engine chay theo BAR, EA chay theo TICK."""
    t0 = pd.Timestamp("2024-01-01")
    giay_tick = 900.0 / tpb
    tai = lambda i: t0 + pd.Timedelta(seconds=float(i) * giay_tick)
    dirs = {0: (1,), 1: (-1,), 2: (1, -1)}[mode]
    pos = {1: [], -1: []}                      # [gia_mo, lot, tick_mo]
    tpp = {1: None, -1: None}
    ra = []

    def dat_tp(d):
        b = pos[d]
        tong = sum(l for _, l, _ in b)
        tb = sum(l * g for g, l, _ in b) / tong
        tpp[d] = tb + tp_pips * pip - spread if d > 0 else tb - tp_pips * pip + spread

    for i, b0 in enumerate(bid):
        ask = b0 + spread
        for d in dirs:
            if pos[d] and ((b0 >= tpp[d]) if d > 0 else (ask <= tpp[d])):
                for g, l, im in pos[d]:
                    ra.append(dict(mo=tai(im), dong=tai(i), chieu="buy" if d > 0 else "sell", lot=l, gia_mo=g,
                                   gia_dong=tpp[d], ma=ma))
                pos[d], tpp[d] = [], None
        for d in dirs:
            b = pos[d]
            if not b:
                b.append([ask if d > 0 else b0, lot, i])
                dat_tp(d)
                continue
            if len(b) >= max_lv:
                continue
            cuc = min(g for g, _, _ in b) if d > 0 else max(g for g, _, _ in b)
            nguoc = (cuc - ask) if d > 0 else (b0 - cuc)
            if nguoc >= step_pips * pip - 0.5e-5:
                b.append([ask if d > 0 else b0, lot * mult ** len(b), i])
                dat_tp(d)
    for d in dirs:                            # lenh con mo cuoi du lieu: chua co gio/gia dong
        for g, l, im in pos[d]:
            ra.append(dict(mo=tai(im), dong=pd.NaT, chieu="buy" if d > 0 else "sell", lot=l, gia_mo=g,
                           gia_dong=np.nan, ma=ma))
    return pd.DataFrame(ra).sort_values("mo", kind="stable").reset_index(drop=True)


def _ea_tin_hieu(bar: pd.DataFrame, tin_hieu: np.ndarray, chieu: int = 1, buoc: float = 15, tp: float = 10, tran: int = 8,
                 lot: float = 0.01, seed: int = 0, nhieu_s: int = 40, ma: str = "AUDCAD") -> pd.DataFrame:
    """EA vao theo TIN HIEU, sinh theo bar bang vong lap rieng: MO ro moi (tai gia mo bar i) khi KHONG co ro va
    `tin_hieu[i - 1]` dung (dac trung chi dung bar i - 1 tro ve truoc); them tang khi gia cham moc; TP tu gia TB."""
    rng = np.random.RandomState(seed)
    o, h, l = (bar[k].to_numpy(float) for k in ("open", "high", "low"))
    idx = bar.index
    ra, ro = [], None
    ten = "buy" if chieu > 0 else "sell"
    for i in range(1, len(bar)):
        t_i = idx[i] + pd.Timedelta(seconds=int(rng.randint(1, nhieu_s)))
        if ro is None:
            if tin_hieu[i - 1]:
                ro = [dict(mo=t_i, gia_mo=o[i], lot=lot)]
            continue
        while len(ro) < tran:
            moc = ro[-1]["gia_mo"] - chieu * buoc * PIP
            if (l[i] <= moc) if chieu > 0 else (h[i] >= moc):
                ro.append(dict(mo=t_i, gia_mo=moc, lot=lot))
            else:
                break
        lots = np.array([x["lot"] for x in ro])
        gm = np.array([x["gia_mo"] for x in ro])
        mtp = (lots * gm).sum() / lots.sum() + chieu * tp * PIP
        if (h[i] >= mtp) if chieu > 0 else (l[i] <= mtp):
            ra += [dict(mo=x["mo"], dong=t_i, chieu=ten, lot=x["lot"], gia_mo=x["gia_mo"], gia_dong=mtp, ma=ma) for x in ro]
            ro = None
    ra += [dict(mo=x["mo"], dong=pd.NaT, chieu=ten, lot=x["lot"], gia_mo=x["gia_mo"], gia_dong=np.nan, ma=ma)
           for x in (ro or [])]
    return pd.DataFrame(ra)


def _tin_hieu_rsi2(bar: pd.DataFrame, nguong: float = 10.0) -> np.ndarray:
    dk = DT.dieu_kien("rsi2", "<", nguong)
    return NP._dieu_kien(bar, [dk], mac_dinh=False).fillna(False).to_numpy(bool)


# ============================================================== 1. DOC + CHUAN HOA
def test_chuan_hoa_ten_cot_viet_anh_va_hai_cot_time_price():
    # bang cua MT5 Report: hai cot "Time" va hai cot "Price" cung ten - theo THU TU: mo roi dong
    raw = pd.DataFrame([["2024.01.02 10:00:00", "buy", "0,10", "0.65000", "2024.01.02 10:30:00", "0.65100", "EURUSD"],
                        ["2024.01.02 11:00:00", "sell", "0,20", "0.65200", "2024.01.02 11:10:00", "0.65100", "EURUSD"]],
                       columns=["Time", "Type", "Volume", "Price", "Time", "Price", "Symbol"])
    d = BL.chuan_hoa(raw)
    assert list(d.columns[:6]) == ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong"]
    assert list(d["chieu"]) == [1, -1] and list(d["lot"]) == [0.1, 0.2]
    assert d["gia_mo"].tolist() == [0.65, 0.652] and d["gia_dong"].tolist() == [0.651, 0.651]
    assert d["mo"].iat[0] < d["dong"].iat[0] and d["ma"].iat[0] == "EURUSD"
    vi = pd.DataFrame({"Giờ mở": ["2024-01-02 10:00:00"], "Loại": ["mua"], "Khối lượng": [0.1], "Giá mở": [1.1],
                       "Giờ đóng": ["2024-01-02 11:00:00"], "Giá đóng": [1.101]})
    dv = BL.chuan_hoa(vi, ma="EURUSD")
    assert dv["chieu"].iat[0] == 1 and dv["dong"].iat[0] == pd.Timestamp("2024-01-02 11:00")


def test_chuan_hoa_chieu_so_mo_ho_thi_bao_loi_khong_doan():
    """Cot chieu toan so 1: +1 = mua hay enum MT5 1 = ban? Doan sai la lat nguoc CA lich su -> phai bao loi."""
    mo = pd.date_range("2024-01-01", periods=3, freq="h")
    base = dict(mo=mo, lot=0.1, gia_mo=1.1, gia_dong=1.101, dong=mo + pd.Timedelta(minutes=5))
    with pytest.raises(ValueError, match="chi gom so 1"):
        BL.chuan_hoa(pd.DataFrame(dict(base, chieu=[1, 1, 1])))
    assert BL.chuan_hoa(pd.DataFrame(dict(base, chieu=[0, 1, 0])))["chieu"].tolist() == [1, -1, 1]     # enum MT5
    assert BL.chuan_hoa(pd.DataFrame(dict(base, chieu=[1, -1, 1])))["chieu"].tolist() == [1, -1, 1]
    assert BL.chuan_hoa(pd.DataFrame(dict(base, chieu=["Buy", "SELL", "long"])))["chieu"].tolist() == [1, -1, 1]
    # dong khong phai lenh (balance, deposit) bi bo va DEM
    r = pd.DataFrame(dict(base, chieu=["buy", "balance", "sell"]))
    d = BL.chuan_hoa(r)
    assert len(d) == 2 and d.attrs["so_bo"] == 1


def test_so_dinh_dang_so_kieu_chau_au_va_my():
    assert BL._so("1 234,50") == 1234.5 and BL._so("1,234.50") == 1234.5 and BL._so("1.234,50") == 1234.5
    assert BL._so("0,10") == 0.1 and BL._so(0.25) == 0.25 and BL._so("12,345") == 12345.0
    assert np.isnan(BL._so("")) and np.isnan(BL._so("-")) and np.isnan(BL._so("abc"))


def test_doc_tep_csv_json_html_va_html_utf16(tmp_path):
    hang = [("2024.01.02 10:00:00", "buy", "0.10", "0.65000", "2024.01.02 10:30:00", "0.65100"),
            ("2024.01.02 11:00:00", "sell", "0.10", "0.65200", "2024.01.02 11:10:00", "0.65100"),
            ("2024.01.02 12:00:00", "buy", "0.10", "0.65000", "2024.01.02 12:20:00", "0.65100")]
    cot = ["Open Time", "Type", "Volume", "Open Price", "Close Time", "Close Price"]
    pd.DataFrame(hang, columns=cot).to_csv(tmp_path / "a.csv", index=False)
    (tmp_path / "b.json").write_text(json.dumps({"lenh": [dict(zip(cot, h)) for h in hang]}), encoding="utf-8")
    html = ("<html><body><table><tr><td>Rac</td></tr></table><table><tr>%s</tr>%s</table></body></html>"
            % ("".join("<th>%s</th>" % c for c in cot),
               "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % v for v in h) for h in hang)))
    (tmp_path / "c.html").write_text(html, encoding="utf-8")
    (tmp_path / "d.htm").write_bytes(b"\xff\xfe" + html.encode("utf-16-le"))          # bao cao MT5: UTF-16 co BOM
    chuan = None
    for ten in ("a.csv", "b.json", "c.html", "d.htm"):
        d = BL.chuan_hoa(BL.doc_tep(tmp_path / ten), ma="EURUSD")
        assert len(d) == 3 and d["chieu"].tolist() == [1, -1, 1], ten
        assert d["gia_dong"].tolist() == [0.651] * 3, ten
        chuan = chuan if chuan is not None else d[["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong"]]
        pd.testing.assert_frame_equal(d[["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong"]], chuan, check_dtype=False)
    with pytest.raises(ValueError, match="khong thay bang lenh"):
        BL.doc_bang_html("<table><tr><td>a</td><td>b</td></tr><tr><td>1</td><td>2</td></tr>"
                         "<tr><td>3</td><td>4</td></tr></table>")
    with pytest.raises(FileNotFoundError):
        BL.doc_tep(tmp_path / "khong_co.csv")


# ============================================================== 2. GOM RO
def _lenh_tay(rows):
    """rows = (mo, dong, chieu, gia_mo, lot) voi thoi gian tinh bang GIAY ke tu 2024-01-01."""
    t0 = pd.Timestamp("2024-01-01")
    return pd.DataFrame([dict(mo=t0 + pd.Timedelta(seconds=a), dong=t0 + pd.Timedelta(seconds=b) if b is not None else pd.NaT,
                              chieu=c, gia_mo=g, lot=l, gia_dong=(g if b is not None else np.nan), ma="X")
                         for a, b, c, g, l in rows])


def test_phan_ro_tang_them_cung_giay_voi_tp_phan_biet_bang_gia():
    """Cung giay 100 (giay TP cua ro 0): lenh mua o 0.9990 SAU tang sau nhat 1.0050 -> tang them (dong cung luc ro cu); lenh mua
    o 1.0200 khong o sau -> RO MOI (mo lai ngay sau TP). Ket qua khong duoc phu thuoc thu tu dong trong tep."""
    rows = [(0, 100, 1, 1.0100, 0.01), (50, 100, 1, 1.0050, 0.01), (100, 100, 1, 0.9990, 0.01),    # ro 0 (tang them cung giay TP)
            (100, 300, 1, 1.0200, 0.01)]                                                          # ro 1
    for thu_tu in (rows, rows[::-1]):
        d = BL.phan_ro(_lenh_tay(thu_tu))
        assert d["ro"].nunique() == 2
        gom = {int(r): sorted(g["gia_mo"].round(4).tolist()) for r, g in d.groupby("ro")}
        assert gom == {0: [0.999, 1.005, 1.01], 1: [1.02]}, gom
        assert d.sort_values("tang").groupby("ro")["tang"].max().tolist() == [2, 0]
    # mo SAU khi ro da dong het (xa hon dung sai) -> luon la ro moi
    lenh2 = _lenh_tay([(0, 100, 1, 1.0, 0.01), (110, 200, 1, 0.9, 0.01)])
    assert BL.phan_ro(lenh2)["ro"].nunique() == 2
    # chieu khac nhau khong bao gio chung ro
    lenh3 = _lenh_tay([(0, 100, 1, 1.0, 0.01), (10, 100, -1, 1.0, 0.01)])
    assert BL.phan_ro(lenh3)["ro"].nunique() == 2


# ============================================================== 3. THAM SO TU LICH SU (engine sinh)
#: ten -> (tham so engine, kiem tra tren tham_so suy ra). `tran_tang` suy ra chi la CAN DUOI (khong duoc cam ket bang).
CA_ENGINE = {
    "mac_dinh": (dict(buoc=15, tp=10, tran_tang=12), dict(che_do="hai_chieu", buoc=15.0, tp=10.0, lot=0.01)),
    "mua_nhan_lot": (dict(che_do="mua", kieu_lot="nhan", he_so_lot=1.3, buoc=12, tp=8, tran_tang=10),
                     dict(che_do="mua", buoc=12.0, tp=8.0, kieu_lot="nhan", he_so_lot=1.3)),
    "tia_lenh": (dict(tia_lenh=True, bien_cap=3.0, cap_moi_bar=1, buoc=10, tp=15, tran_tang=15),
                 dict(che_do="hai_chieu", buoc=10.0, tp=15.0, tia_lenh=True)),
    "cho_lui": (dict(cho_lui=8.0, buoc=15, tp=10, tran_tang=12), dict(buoc=15.0, tp=10.0, cho_lui=8.0)),
    "chot_tien_ban": (dict(che_do="ban", chot_tien=3.0, buoc=15, tp=10, tran_tang=12),
                      dict(che_do="ban", buoc=15.0)),
    "gian_dan": (dict(he_so_buoc=1.25, buoc_tran=60.0, buoc=10, tp=10, tran_tang=14),
                 dict(buoc=10.0, he_so_buoc=1.25, tp=10.0)),
}


@pytest.mark.parametrize("ten", list(CA_ENGINE))
def test_tham_so_tu_lich_su_do_engine_sinh(ten):
    ts_kw, ky_vong = CA_ENGINE[ten]
    bar, h = _chay_engine(ts_kw)
    ra = BL.boc(h, bar=None, pip=PIP, ma="AUDCAD", spread_pip=0.0)
    assert ra["trang_thai"] == "DAT" and ra["loai"] == "luoi_dca", ra.get("loai")
    ts = ra["tham_so"]
    for k, v in ky_vong.items():
        if isinstance(v, float):
            assert ts[k] == pytest.approx(v, rel=0.03), (k, ts)
        else:
            assert ts[k] == v, (k, ts)
    # tham so suy ra phai la truong CUA luoi.ThamSo (de dua thang cho thu_luoi) va dung duoc
    LU.ThamSo(**ts)
    assert not LU.tham_so_chua_cai_dat(ts)
    # tran_tang chi la CAN DUOI cua tran that, va do tin noi dung nhu vay khi chi mot ro cham no
    assert ts["tran_tang"] <= ts_kw["tran_tang"]
    # tp_hay_chot_tien: dung loai
    if "chot_tien" in ts_kw:
        assert ts["chot_tien"] == pytest.approx(ts_kw["chot_tien"], rel=0.12) and "tp" not in ts
    if "bien_cap" in ts_kw:
        assert ts["bien_cap"] == pytest.approx(ts_kw["bien_cap"], rel=0.12)
    if ten == "mac_dinh":
        assert ra["tran_tang"]["do_tin"].startswith("thap")
    # cai KHONG co trong lich su (spread / bien tuong tac) thi khong duoc co mat o tham_so
    assert "dung_lo_tong" not in ts and "don_bay" not in ts


def test_lich_su_khong_phai_luoi_thi_khong_bia_tham_so():
    """Mua/ban doc lap, lot ngau nhien, khong tang them: khong co tham so luoi nao."""
    rng = np.random.RandomState(5)
    mo = pd.Timestamp("2024-01-01") + pd.to_timedelta(np.sort(rng.randint(0, 80 * 86400, 300)), unit="s")
    d = pd.DataFrame(dict(mo=mo, dong=mo + pd.to_timedelta(rng.randint(600, 3000, 300), unit="s"),
                          chieu=rng.choice(["buy", "sell"], 300), lot=rng.choice([0.1, 0.2, 0.3], 300),
                          gia_mo=0.65 + rng.normal(0, 0.01, 300), ma="EURUSD"))
    d["gia_dong"] = d["gia_mo"] + rng.normal(0, 0.001, 300)
    ra = BL.boc(d, pip=PIP, spread_pip=0.0)
    assert ra["loai"] in ("don_lenh", "khong_ro_ho_co_che") and ra["tham_so"] == {}
    assert ra["trang_thai"] == "DAT" and ra["lich_su"]["so_lenh"] == 300


def test_ro_dang_mo_den_het_du_lieu_khong_bi_tach_va_khong_tran_so_gio():
    """Ro con mo (chua dong) co >= 2 lenh: dung moc 'dong vo cuc' CAU TRUC KHONG TRAN datetime64[ns] khi cong dung sai - truoc
    03/10 moc 2262-04-11 + 2 giay tran thanh ngay am -> ro dang mo bi tach thanh tung lenh."""
    lenh = _lenh_tay([(0, None, 1, 1.0100, 0.01), (3600, None, 1, 1.0050, 0.01), (7200, None, 1, 1.0000, 0.01)])
    d = BL.phan_ro(lenh)
    assert d["ro"].nunique() == 1 and d["tang"].tolist() == [0, 1, 2]
    bar_idx = pd.date_range("2024-01-01", periods=10, freq="h").to_numpy("datetime64[ns]")
    ro = BL.bang_ro(d, PIP)
    # `rang[j]` = luc bat dau bar j khong co lenh nao dang mo. Ro mo luc 00:00 va KHONG BAO GIO dong: khong con rang tu bar 0.
    # Co lech gio van phai chay (truoc 03/10 `pd.Timestamp.max + lech` nem OverflowError khi co lenh chua dong).
    for lech, ky_vong in ((0.0, [False] * 10), (3 * 3600.0, [True] * 3 + [False] * 7), (-2 * 3600.0, [False] * 10)):
        assert BL._rang_theo_bar(ro, bar_idx, lech, 1).tolist() == ky_vong, lech


def test_gom_ro_dem_dung_tren_lich_su_engine():
    """So ro / so lenh doc lai tu lich su co nhieu giay le = so ro / lenh engine da ghi."""
    bar = _chuoi()
    kq = LU.chay(bar, LU.ThamSo(buoc=15, tp=10, tran_tang=12), 1e12, None, ghi_lenh=True)
    h = _lich_su_tu_engine(kq.lenh)
    ra = BL.phan_tich_lenh(BL.chuan_hoa(h, pip=PIP, ma="AUDCAD"), spread_pip=0.0)
    assert ra["lich_su"]["so_lenh"] == len(kq.lenh)
    assert ra["lich_su"]["so_ro"] == int(kq.lenh["ro"].nunique())
    assert ra["lich_su"]["so_lenh_dang_mo"] == int(kq.lenh["dong"].isna().sum())


# ============================================================== 4. EA TUNG TICK: quy uoc spread, phat lai
@pytest.mark.parametrize("ten,kw", [
    ("hai_chieu", dict(step_pips=15, tp_pips=10, max_lv=12, mode=2, lot=0.01, mult=1.0)),
    ("mua_nhan", dict(step_pips=12, tp_pips=8, max_lv=10, mode=0, lot=0.01, mult=1.3)),
])
def test_ea_tung_tick_tham_so_va_quy_uoc_spread(ten, kw):
    tpb, nb, spread_pts = 100, 1500, 15
    bid = _duong_tick(nb, tpb, seed=3)
    bar = _bar_tu_tick(bid, tpb, spread_pts)
    h = _ea_tung_tick(bid, tpb, spread_pts * 1e-5, **kw)
    ra = BL.boc(h, bar=bar, pip=PIP, ma="AUDCAD", lech_gio=0.0, so_null=20)
    assert ra["loai"] == "luoi_dca"
    ts = ra["tham_so"]
    # spread lay tu cot `spread` cua bar: 15 point = 1,5 pip
    assert ra["spread_pip"] == pytest.approx(1.5)
    # TP do tren lich su = tp - spread (mua mo o ask, dong o bid) -> bo boc cong lai spread de ra dung `tp` cua EA
    assert ra["tp"]["tp_do_duoc"] == pytest.approx(kw["tp_pips"] - 1.5, abs=0.15)
    assert ts["tp"] == pytest.approx(kw["tp_pips"], abs=0.15)
    # buoc: tick nhay 0,4 pip nen khoang cach that = buoc + qua tay < 1 pip
    assert kw["step_pips"] <= ts["buoc"] <= kw["step_pips"] * 1.08
    assert ts["che_do"] == {0: "mua", 2: "hai_chieu"}[kw["mode"]]
    assert ts["lot"] == kw["lot"]
    if kw["mult"] > 1:
        assert ts["kieu_lot"] == "nhan" and ts["he_so_lot"] == pytest.approx(kw["mult"], abs=0.03)
    assert ts["tran_tang"] <= kw["max_lv"]
    # phat lai qua luoi.chay tren bar: cung so ro (khong tien) trong 35% - lich su sinh theo TICK, mo phong theo BAR
    pl = ra["phat_lai"]
    assert pl["trang_thai"] == "DAT" and pl["khop"] in ("tot", "vua"), pl
    assert 0.65 < pl["ro_bat_dau"]["ty_le_mo_phong/that"] < 1.5


def test_khong_truyen_spread_thi_canh_bao_khong_cong_am_tham():
    tpb = 100
    bid = _duong_tick(1500, tpb, seed=3)
    h = _ea_tung_tick(bid, tpb, 15e-5, 15, 10, 12, 2, 0.01, 1.0)
    ra = BL.boc(h, bar=None, pip=PIP, ma="AUDCAD")                 # khong bar, khong spread_pip
    assert ra["tham_so"]["tp"] == pytest.approx(10 - 1.5, abs=0.15)
    assert any("khong biet spread" in x for x in ra["ngoai_engine"])
    ra2 = BL.boc(h, bar=None, pip=PIP, ma="AUDCAD", spread_pip=1.5)
    assert ra2["tham_so"]["tp"] == pytest.approx(10.0, abs=0.15)
    assert not any("khong biet spread" in x for x in ra2["ngoai_engine"])


# ============================================================== 5. PHAT LAI qua engine
@pytest.mark.parametrize("ten", ["mac_dinh", "mua_nhan_lot", "cho_lui"])
def test_phat_lai_khop_khi_lich_su_chinh_la_engine(ten):
    ts_kw, _ = CA_ENGINE[ten]
    bar, h = _chay_engine(ts_kw)
    ra = BL.boc(h, bar=bar, pip=PIP, ma="AUDCAD", lech_gio=0.0, spread_pip=0.0, so_null=20)
    pl = ra["phat_lai"]
    assert pl["trang_thai"] == "DAT" and pl["khop"] == "tot", pl
    assert abs(np.log(pl["ro_bat_dau"]["ty_le_mo_phong/that"])) < 0.08
    assert abs(np.log(pl["lenh"]["ty_le_mo_phong/that"])) < 0.12
    assert pl["tp_pip_trung_vi"]["mo_phong"] == pytest.approx(pl["tp_pip_trung_vi"]["that"], abs=0.5)
    assert pl["tuong_quan_ro_theo_tuan"] > 0.9
    # tham so lech thi phat lai PHAI nhan ra (khong khop 'tot' mot cach vo bo)
    xau = dict(ra["tham_so"], buoc=ra["tham_so"]["buoc"] * 2.0, tp=ra["tham_so"]["tp"] * 3.0)
    ro = BL.bang_ro(BL.phan_ro(BL.chuan_hoa(h, pip=PIP, ma="AUDCAD")), PIP)
    pl2 = BL.phat_lai(bar, xau, ro, None)
    assert pl2["khop"] != "tot", pl2


# ============================================================== 6. GIO LECH MAY CHU
@pytest.mark.parametrize("them_gio", [0, 3, -2, 7])
def test_uoc_lech_gio_khoi_phuc_gio_cai_san(them_gio):
    """Lich su lech `them_gio` gio so voi bar -> phai uoc ra DUNG -them_gio (gio phai CONG THEM) bang chinh gia."""
    bar, h = _chay_engine(CA_ENGINE["mac_dinh"][0])
    h = h.copy()
    h["mo"] = h["mo"] + pd.Timedelta(hours=them_gio)
    h["dong"] = h["dong"] + pd.Timedelta(hours=them_gio)
    d = BL.chuan_hoa(h, pip=PIP, ma="AUDCAD")
    lg = BL.uoc_lech_gio(bar, d, PIP)
    assert lg["lech_gio"] == -float(them_gio), lg
    assert lg["tin_cay"] == "cao" and lg["ty_le_gia_trong_bar"] >= 0.95


def test_uoc_lech_gio_khong_tin_khi_lich_su_khong_phai_cua_chuoi_gia_nay():
    """Lich su cua mot chuoi gia KHAC (hat khac): khong co gio nao khop nhieu -> khong duoc bao 'cao'."""
    bar, _ = _chay_engine(CA_ENGINE["mac_dinh"][0], seed=11)
    _, h_khac = _chay_engine(CA_ENGINE["mac_dinh"][0], seed=99)
    lg = BL.uoc_lech_gio(bar, BL.chuan_hoa(h_khac, pip=PIP, ma="AUDCAD"), PIP)
    assert lg["tin_cay"] != "cao", lg


def test_uoc_lech_gio_chi_dung_lenh_trong_khoang_bar():
    """Lich su dai gap doi bar: lenh ngoai khoang bar khong duoc keo ty le trung xuong (truoc 03/10 ket luan nao cung 'thap')."""
    bar_dai = _chuoi(n=20000, seed=11)
    kq = LU.chay(bar_dai, LU.ThamSo(buoc=15, tp=10, tran_tang=12), 1e12, None, ghi_lenh=True)
    h = BL.chuan_hoa(_lich_su_tu_engine(kq.lenh), pip=PIP, ma="AUDCAD")
    bar_nua = bar_dai.iloc[: len(bar_dai) // 2]                    # bar chi nua dau, lich su ca hai nua
    lg = BL.uoc_lech_gio(bar_nua, h, PIP)
    assert lg["lech_gio"] == 0.0 and lg["tin_cay"] == "cao", lg
    # bar qua ngan / khong lenh nao trong khoang
    assert BL.uoc_lech_gio(bar_dai.iloc[:30], h, PIP)["tin_cay"] == "khong_du_du_lieu"
    xa = h.copy()
    xa["mo"] = xa["mo"] + pd.Timedelta(days=400)
    assert BL.uoc_lech_gio(bar_dai, xa, PIP)["tin_cay"] == "khong_du_du_lieu"


# ============================================================== 7. DIEU KIEN VAO LENH
@pytest.fixture(scope="module")
def lich_su_rsi2():
    """EA luoi mua CHI vao khi rsi2 (bar truoc) < 10 - dap an cai san: dac_trung rsi2, phep <, nguong 10."""
    bar = _chuoi(n=20000, seed=21, sigma=4e-4, theta=0.02)
    sig = _tin_hieu_rsi2(bar, 10.0)
    h = _ea_tin_hieu(bar, sig, chieu=1, buoc=15, tp=10, tran=8, seed=1)
    return bar, sig, h


def test_tim_dieu_kien_vao_khoi_phuc_luat_cai_san(lich_su_rsi2):
    bar, sig, h = lich_su_rsi2
    ra = BL.boc(h, bar=bar, pip=PIP, ma="AUDCAD", lech_gio=0.0, spread_pip=0.0, so_null=100, phat=False)
    dk = ra["dieu_kien_vao"]
    assert dk["trang_thai"] == "DAT" and set(dk["theo_chieu"]) == {"mua"}
    mua = dk["theo_chieu"]["mua"]
    assert mua["so_cho_roi_vao"] >= 100
    t = mua["top"][0]
    assert t["dac_trung"] == "rsi2" and t["phep"] == "<", t
    assert t["nguong"] == pytest.approx(10.0, abs=0.5)                # nguong Youden chinh xac, khong phai luoi 11 muc
    assert t["tpr"] > 0.95 and t["fpr"] < 0.02
    assert t["p_nhom"] < 0.05 and t["auc"] > 0.95
    assert t["mq5_duoc"] in (True, False)
    # dieu_kien DSL dua thang cho thu_co_che duoc: cung bo bar ra cung tin hieu
    kq = NP._dieu_kien(bar, [t["dieu_kien"]], mac_dinh=False).fillna(False).to_numpy(bool)
    assert (kq == sig).mean() > 0.99


def test_khop_luat_do_luat_ai_de_xuat(lich_su_rsi2):
    bar, sig, h = lich_su_rsi2
    ro = BL.bang_ro(BL.phan_ro(BL.chuan_hoa(h, pip=PIP, ma="AUDCAD")), PIP)
    dung = BL.khop_luat(bar, ro, [DT.dieu_kien("rsi2", "<", 10.0)], chieu=1, so_null=200)
    assert dung["trang_thai"] == "DAT" and dung["tpr"] > 0.95 and dung["fpr"] < 0.02 and dung["p_null"] < 0.02
    sai = BL.khop_luat(bar, ro, [DT.dieu_kien("rsi2", ">", 90.0)], chieu=1, so_null=200)
    assert sai["trang_thai"] == "DAT" and sai["tpr"] < 0.05, sai
    # it su kien -> CHUA_DO_DUOC, khong doan
    it = BL.khop_luat(bar, ro[ro["mo"] < ro["mo"].iloc[5]], [DT.dieu_kien("rsi2", "<", 10.0)], chieu=1)
    assert it["trang_thai"] == "CHUA_DO_DUOC"


def test_dich_dac_trung_phai_la_thu_biet_truoc_khi_vao(lich_su_rsi2):
    """`dich = 0` (dac trung cua CHINH bar vao lenh) bi cam; dich 2 van thay rsi2 nhung yeu hon dich 1."""
    bar, _sig, h = lich_su_rsi2
    ro = BL.bang_ro(BL.phan_ro(BL.chuan_hoa(h, pip=PIP, ma="AUDCAD")), PIP)
    with pytest.raises(ValueError, match="dich >= 1"):
        BL.tim_dieu_kien_vao(bar, ro, dich=0)
    d1 = BL.tim_dieu_kien_vao(bar, ro, dich=1, so_null=30)["theo_chieu"]["mua"]["top"][0]
    d3 = BL.tim_dieu_kien_vao(bar, ro, dich=3, so_null=30)["theo_chieu"]["mua"]["top"][0]
    assert d1["auc"] > d3["auc"] + 0.05, (d1, d3)


def test_vao_lenh_ngau_nhien_khong_bi_bia_luat_hieu_chuan_null():
    """HIEU CHUAN: EA vao NGAU NHIEN (khong dieu kien) -> `p_nhom < 0,05` chi duoc xuat hien ~5% so lan (da sua theo viec tim
    tren 25 dac trung). Do 03/10: 120 lich su -> 5,0% (p<0,05), 6,7% (p<0,10), 2,5% (p<0,02). Day la ban rut gon (30 hat)."""
    so_hat, bao = 30, []
    for hat in range(so_hat):
        bar = _chuoi(n=6000, seed=1000 + hat)
        rng = np.random.RandomState(hat)
        sig = rng.rand(len(bar)) < 0.02
        h = _ea_tin_hieu(bar, sig, chieu=1, buoc=15, tp=10, tran=8, seed=hat)
        if len(h) < 60:
            continue
        ra = BL.boc(h, bar=bar, pip=PIP, ma="AUDCAD", lech_gio=0.0, spread_pip=0.0, so_null=100, phat=False)
        mua = ra["dieu_kien_vao"]["theo_chieu"].get("mua", {})
        if mua.get("trang_thai") == "DAT":
            bao.append(min(t["p_nhom"] for t in mua["top"]))
    assert len(bao) >= 20, "can du hat hop le de hieu chuan (%d)" % len(bao)
    ty_le = float(np.mean([p < 0.05 for p in bao]))
    assert ty_le <= 0.20, "ty le bao dong gia %.1f%% >> 5%% danh nghia (n=%d)" % (100 * ty_le, len(bao))


def test_it_su_kien_doc_lap_thi_chua_do_duoc_khong_doan():
    """Lich su chi toan vao lai NGAY sau TP (khong co dieu kien rieng): CHUA_DO_DUOC kem ly do, khong bia."""
    bar, h = _chay_engine(dict(buoc=15, tp=10, tran_tang=12, che_do="mua"))
    ra = BL.boc(h, bar=bar, pip=PIP, ma="AUDCAD", lech_gio=0.0, spread_pip=0.0, so_null=20, phat=False)
    dk = ra["dieu_kien_vao"]
    assert dk["trang_thai"] == "CHUA_DO_DUOC"
    mua = dk["theo_chieu"]["mua"]
    assert mua["vao_lai_ngay_ty_le"] > 0.95 and "doc lap" in mua["ly_do"]


# ============================================================== 8. CONG CU nc + SO TAY
def test_cong_cu_boc_lich_su_co_trong_bo_va_schema_hop_le():
    t = CC.THEO_TEN["boc_lich_su"]
    assert len(t["mo_ta"]) > 40 and t["schema"]["required"] == ["ma"]
    assert {"ma", "khung", "tep", "lenh", "doan", "lech_gio", "so_null", "phat", "gt_id"} <= set(t["schema"]["properties"])
    assert [c["ten"] for c in CC.CONG_CU][-1] == "boc_lich_su"       # them o CUOI: giu thu tu schema (cache prompt)
    assert "niem_phong" in t["mo_ta"] and "GIA THUYET" in t["mo_ta"]


def _lich_su_tong_hop(tmp_path, monkeypatch, ghi_tep=True):
    """Lich su sinh tren CHINH bar kham_pha cua chuoi TONG_HOP (khong co data/ that tren cloud)."""
    ma, khung = "TONG_HOP_HOI_QUY_1", "H1"
    pre, a = NDL.cat_doan(NDL.nap(ma, khung), "kham_pha")
    seg = pre.iloc[a:]
    kq = LU.chay(seg, LU.ThamSo(buoc=60, tp=40, tran_tang=8, che_do="hai_chieu"), 1e12, None, ghi_lenh=True)
    h = _lich_su_tu_engine(kq.lenh, ma=ma)
    monkeypatch.setattr(NDL, "LAB", tmp_path)
    if ghi_tep:
        h.to_csv(tmp_path / "ls.csv", index=False)
    return ma, khung, h


def test_boc_lich_su_qua_cong_cu_ghi_so_tay_va_chi_mo_ta(tmp_path, monkeypatch):
    ma, khung, h = _lich_su_tong_hop(tmp_path, monkeypatch)
    r = CC.goi("boc_lich_su", {"ma": ma, "khung": khung, "tep": "ls.csv", "so_null": 20})
    assert "loi" not in r, r
    assert r["trang_thai"] == "DAT" and r["loai_ket_qua"] == "mo_ta" and r["loai"] == "luoi_dca"
    assert r["tham_so"]["buoc"] == pytest.approx(60.0, rel=0.05) and r["tham_so"]["tp"] == pytest.approx(40.0, rel=0.05)
    assert r["bar"]["so_bar"] > 1000 and r["doan"] == "kham_pha"
    assert r["lech_gio"]["lech_gio"] == 0.0
    assert r["phat_lai"]["khop"] in ("tot", "vua")
    assert not any(k.startswith("_") and k != "_giay" for k in r)    # `_giay` la khoa do thoi gian chung cua moi cong cu
    json.dumps(r, ensure_ascii=False)                                # thuan JSON: khong ro DataFrame / numpy lot ra
    # so tay: ghi dung loai, KHONG tinh la 'DAT co lai' o bang tong ket, phep thu 1 neu da tim dieu kien tren bar
    tn = ST.mot("SELECT * FROM thi_nghiem WHERE id=?", r["tn_id"])
    assert tn["loai"] == "boc_lich_su" and tn["trang_thai"] == "DAT" and tn["tom_tat"].startswith("MO TA")
    assert tn["so_phep_thu"] == (1 if (r.get("dieu_kien_vao") or {}).get("trang_thai") == "DAT" else 0)
    tt = ST.tom_tat(6)
    assert all(z["loai"] != "boc_lich_su" for z in tt["thi_nghiem_tot_nhat"])
    assert all(z["dat"] in (0, None) for z in tt["phep_thu_theo_ma"] if z["ma"] == ma)
    # chay y het -> lay lai tu so tay, khong ghi them
    n0 = ST.mot("SELECT COUNT(*) n FROM thi_nghiem")["n"]
    r2 = CC.goi("boc_lich_su", {"ma": ma, "khung": khung, "tep": "ls.csv", "so_null": 20})
    assert "tu_so_tay" in r2 and ST.mot("SELECT COUNT(*) n FROM thi_nghiem")["n"] == n0


def test_boc_lich_su_tu_choi_tep_ngoai_thu_muc_du_an_va_dau_vao_sai(tmp_path, monkeypatch):
    ma, khung, h = _lich_su_tong_hop(tmp_path, monkeypatch, ghi_tep=False)
    ngoai = tmp_path.parent / "ngoai_lich_su.csv"
    h.to_csv(ngoai, index=False)
    r = TN.boc_lich_su(ma, khung, tep=str(ngoai))
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "trong thu muc du an" in r["ly_do"]
    assert TN.boc_lich_su(ma, khung)["trang_thai"] == "CHUA_DO_DUOC"                       # thieu ca tep lan lenh
    assert TN.boc_lich_su(ma, khung, tep="a.csv", lenh=[{}])["trang_thai"] == "CHUA_DO_DUOC"
    assert "khong doc duoc" in TN.boc_lich_su(ma, khung, tep="khong_co.csv")["ly_do"]
    assert TN.boc_lich_su(ma, khung, lenh=[], doan="niem_phong")["ly_do"] == "doan chi duoc la kham_pha/xac_nhan"
    # lich su cua MA KHAC
    h2 = h.assign(ma="USDCHF")
    r = TN.boc_lich_su(ma, khung, lenh=json.loads(h2.to_json(orient="records", date_format="iso")))
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "khong co lenh cua" in r["ly_do"]
    assert ST.mot("SELECT COUNT(*) n FROM thi_nghiem")["n"] == 0                            # tu choi thi khong ghi so tay


def test_boc_lich_su_khong_dung_bar_niem_phong_lich_su_ngoai_doan_chi_mo_ta(tmp_path, monkeypatch):
    """Lich su roi vao DOAN NIEM PHONG cua chuoi (ma, khung): bar cua doan do khong duoc dung - chi mo ta, bao ro ly do."""
    ma, khung = "TONG_HOP_HOI_QUY_1", "H1"
    df = NDL.nap(ma, khung)
    pre, a = NDL.cat_doan(df, "xac_nhan")
    sau = df.iloc[len(pre):]                                          # CHINH doan niem phong
    assert len(sau) > 500
    kq = LU.chay(sau, LU.ThamSo(buoc=60, tp=40, tran_tang=8), 1e12, None, ghi_lenh=True)
    h = _lich_su_tu_engine(kq.lenh, ma=ma)
    monkeypatch.setattr(NDL, "LAB", tmp_path)
    h.to_csv(tmp_path / "ls.csv", index=False)
    r = TN.boc_lich_su(ma, khung, tep="ls.csv", so_null=20)
    assert r["trang_thai"] == "DAT" and r["bar"] is None
    assert "dieu_kien_vao" not in r and "phat_lai" not in r and "lech_gio" not in r
    assert any("ngoai doan mo" in x and "niem phong" in x for x in r["ghi_chu"]), r["ghi_chu"]
    assert r["tham_so"]["buoc"] == pytest.approx(60.0, rel=0.05)      # mo ta tu CHINH lich su van co
    tn = ST.mot("SELECT so_phep_thu FROM thi_nghiem WHERE id=?", r["tn_id"])
    assert tn["so_phep_thu"] == 0


def test_boc_lich_su_ma_khong_co_du_lieu_van_mo_ta_duoc(tmp_path, monkeypatch):
    ma, khung, h = _lich_su_tong_hop(tmp_path, monkeypatch, ghi_tep=False)
    r = TN.boc_lich_su("KHONGCOMA", "M15", lenh=json.loads(h.assign(ma="KHONGCOMA").to_json(orient="records",
                                                                                           date_format="iso")))
    assert r["trang_thai"] == "DAT" and r["bar"] is None
    assert any("khong nap duoc bar" in x for x in r["ghi_chu"])
    assert r["tham_so"]["buoc"] == pytest.approx(60.0, rel=0.05)
