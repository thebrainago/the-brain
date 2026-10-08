# -*- coding: utf-8 -*-
"""`quet_luoi` - quet tham so he luoi trong MOT lan goi (03/10/2026).

Chu du an hoi cach tang toc do test. Sau nhan C, nut that con lai la SO LAN GOI: moi lan goi cong cu = mot vong LLM = token;
quet 54 cau hinh bang 54 lan `thu_luoi` ton 54 vong. `quet_luoi` chay CUNG engine, CUNG phep tinh tien (he so lot cham tran
maxDD 80%) nhung trong mot goi. Ky luat phai giu - moi y mot nhom test:

  1. SO KHONG DOI: `chay_mang(chuan_bi(df))` y het `chay(df)`; mot o cua quet y het `danh_gia_luoi` cung tham so; Python va C
     cho cung bang; so luong khong doi bang; mang dung chung chi doc.
  2. KHONG THEM DUONG VAO DOAN KHAC: quet chi doc kham_pha (khong co tham so `doan`), moi o chay la mot phep thu.
  3. HINH DANG la NHAN, o tot nhat la LUA CHON: o chay tai khoan khong bao gio la o co lai; luoi het gio khong doc hinh dang.
  4. DAU VAO SAI bi chan TRUOC khi nap du lieu (khong ton token, khong ghi so tay).
"""
from __future__ import annotations

import inspect
import itertools
import json
import time

import numpy as np
import pytest

from nhan import luoi as LU
from nhan import luoi_nhan as LN
from nhan import nc_cong_cu as CC
from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN
from test_luoi_quy_cach import CASES, _chuoi, _cp, _tom_tat

CD = {"tran_tang": 12}
GRID = {"buoc": [10, 15, 20], "tp": [8, 12]}                                  # 6 o
CD_LON = {"tran_tang": 12, "tp": 10, "kieu_lot": "nhan"}                       # kieu_lot nhan: truc he_so_lot moi co nghia
GRID_LON = {"buoc": [8, 10, 12, 15, 20, 25], "he_so_lot": [1.0, 1.1, 1.3], "che_do": ["mua", "ban", "hai_chieu"]}   # 54 o
#: khoa thay doi giua cac lan chay (dong ho, so luong, nhan C) - khong thuoc ket qua do
_BIEN_DONG = ("giay", "giay_moi_o", "luong", "nhan_c", "canh_bao", "tn_id", "_giay")


@pytest.fixture
def moi_truong(tmp_path, monkeypatch):
    """So tay tam + chuoi tong hop + ghi lai moi lan `cat_doan` (de chung minh quet chi doc kham_pha)."""
    monkeypatch.setattr(LU, "FILE_QUY_CACH", tmp_path / "luoi_quy_cach.json")
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    monkeypatch.setattr(TN, "_DEM_MOC", {})
    monkeypatch.setenv("NC_QUET_LUONG", "2")
    st = {"cp": _cp(do_tin="SAN"), "df": _chuoi(), "doan": [], "tmp": tmp_path}
    goc = NDL.cat_doan

    def cat(df, doan, *a, **k):
        st["doan"].append(doan)
        return goc(df, doan, *a, **k)

    monkeypatch.setattr(NDL, "nap", lambda ma, khung="H4": st["df"])
    monkeypatch.setattr(NDL, "chi_phi", lambda ma, d: st["cp"])
    monkeypatch.setattr(NDL, "cat_doan", cat)
    return st


def _khong_duoc_goi(*a, **k):
    raise AssertionError("dau vao sai phai bi tu choi TRUOC khi nap du lieu")


def _so_tay_moi(st, monkeypatch, ten):
    """So tay rong (de lan chay sau KHONG lay ket qua cu cua lan truoc)."""
    monkeypatch.setattr(ST, "DB", st["tmp"] / ten)


def _doi_chung(r: dict) -> dict:
    return {k: v for k, v in r.items() if k not in _BIEN_DONG}


# ------------------------------------------------------------------ 1. SO KHONG DOI
@pytest.mark.parametrize("ten", sorted(CASES))
def test_chay_mang_chuan_bi_y_het_chay(ten):
    ts, von, kw = CASES[ten]
    df = _chuoi(**kw)
    a = LU.chay(df, LU.ThamSo(**ts), von)
    b = LU.chay_mang(LU.chuan_bi(df), LU.ThamSo(**ts), von)
    assert _tom_tat(a, von) == _tom_tat(b, von)
    assert np.array_equal(a.duong_equity, b.duong_equity)


def test_chay_mang_ghi_lenh_va_quy_cach_khac_audcad_y_het_chay():
    df = _chuoi()
    qc = LU.QuyCach(ma="USDCHF", phi_nam_mua=0.02, phi_nam_ban=-0.01, do_tin="SAN")
    ts = LU.ThamSo(**CASES["mac_dinh"][0])
    a = LU.chay(df, ts, 10000.0, qc, ghi_lenh=True)
    b = LU.chay_mang(LU.chuan_bi(df, qc), ts, 10000.0, ghi_lenh=True)
    assert _tom_tat(a, 10000.0) == _tom_tat(b, 10000.0)
    assert a.lenh is not None and a.lenh.equals(b.lenh)
    # quy cach ngam dinh cua chuan_bi / chay = AUDCAD cu
    assert LU.chuan_bi(df).qc is LU.QC_AUDCAD


def test_dung_lai_mot_bo_mang_nhieu_lan_khong_nhiem_ban():
    """Quet = nhieu `chay_mang` tren CUNG mot `DuLieuChay`: mot lan chay khong duoc de lai dau vet cho lan sau."""
    df = _chuoi()
    dl = LU.chuan_bi(df)
    cac = [CASES[k][0] for k in ("mac_dinh", "tia_lenh", "gian_dan", "cho_lui", "mua_nhan_lot")]
    a = [LU.chay_mang(dl, LU.ThamSo(**ts), 10000.0) for ts in cac]
    b = [LU.chay_mang(dl, LU.ThamSo(**ts), 10000.0) for ts in reversed(cac)][::-1]
    c = [LU.chay(df, LU.ThamSo(**ts), 10000.0) for ts in cac]
    for x, y, z in zip(a, b, c):
        assert _tom_tat(x, 10000.0) == _tom_tat(y, 10000.0) == _tom_tat(z, 10000.0)


@pytest.mark.parametrize("che_do", ["py", "auto"])
def test_chay_mang_khong_ghi_len_mang_dung_chung(monkeypatch, che_do):
    """`DuLieuChay` duoc nhieu luong dung chung: engine (Python va C) khong duoc ghi len no. Dat mang o che do CHI DOC - ghi mot
    byte la nem loi - roi chay lai va doi chieu voi ban mang ghi duoc."""
    monkeypatch.setenv("LUOI_NHAN", che_do)
    df = _chuoi()
    dl = LU.chuan_bi(df)
    truoc = [a.copy() for a in (dl.hi, dl.lo, dl.cl, dl.sp, dl.dem)]
    mang = (dl.hi, dl.lo, dl.cl, dl.sp, dl.dem)
    for a in mang:
        a.flags.writeable = False
    for k in ("mac_dinh", "tia_lenh", "gian_dan"):
        ts, von, _ = CASES[k]
        ref = LU.chay(df, LU.ThamSo(**ts), von)
        kq = LU.chay_mang(dl, LU.ThamSo(**ts), von)
        assert _tom_tat(kq, von) == _tom_tat(ref, von)
    assert all(np.array_equal(a, b) for a, b in zip(truoc, mang))


def _mot_o_vs_danh_gia(st, ma):
    """-> [(dong cua quet, ket qua `danh_gia_luoi` cung tham so)] cho vai o dai dien (nhan lot, ban, tia lenh, cho lui)."""
    pre, a = NDL.cat_doan(st["df"], "kham_pha")
    seg = pre.iloc[a:]
    qc, _ = LU.quy_cach_cho(ma, float(np.nanmedian(seg["close"].to_numpy(float))), st["cp"])
    dl = LU.chuan_bi(seg, qc)
    von = 10000.0
    ra = []
    for ts in (dict(CD, buoc=10, tp=8), dict(CD, buoc=15, tp=12, che_do="mua", kieu_lot="nhan", he_so_lot=1.3),
               dict(CD, buoc=12, tp=10, che_do="ban", cho_lui=6.0), dict(CD, buoc=10, tp=15, tia_lenh=True, bien_cap=3.0)):
        d = TN.danh_gia_luoi(ma, "M15", ts, "kham_pha", von=von)
        assert d["trang_thai"] in ("DAT", "AM"), d
        o = {k: v for k, v in ts.items() if k not in CD}
        ra.append((TN._o_luoi(dl, CD, o, von * qc.von_quy_doi, d["tien"]["moc_duoi_tran_pct"]), d))
    return ra


@pytest.mark.parametrize("ma", ["AUDCAD", "USDCHF"])
def test_mot_o_cua_quet_y_het_danh_gia_luoi_cung_tham_so(moi_truong, ma):
    """Cung chuoi, cung quy cach, cung tham so: dong cua quet == `tien` / `lenh` cua `danh_gia_luoi` (tung con so)."""
    for dong, d in _mot_o_vs_danh_gia(moi_truong, ma):
        t, ln = d["tien"], d["lenh"]
        assert dong["so_lenh"] == ln["so_lenh"] and dong["chay"] == ("CHAY TAI KHOAN" in d["ly_do"])
        assert dong["loi_suat_nam_pct"] == t["loi_suat_nam_pct"] and dong["maxdd_pct"] == t["maxdd_pct"]
        assert dong["he_so_lot_tai_tran"] == t["he_so_lot_tai_tran"]
        assert dong["loi_suat_o_tran_pct"] == t["loi_suat_o_tran_pct"] and dong["hon_moc_pct"] == t["hon_moc_pct"]
        assert dong["co_lai"] is t["co_lai"], (dong, t)


def test_quet_von_quy_doi_cho_ma_co_ghi_de_y_het_thu_luoi(moi_truong):
    """Ma co `von_quy_doi` != 1 (cap JPY: von 10.000 USD = 1,5 trieu JPY): quet phai doi von giong `thu_luoi`, neu khong lai % lech
    ca hai bac do lon va khong ai thay (cac ma anh em FX deu co von_quy_doi = 1 nen test o tren khong bat duoc)."""
    LU.FILE_QUY_CACH.write_text(json.dumps({"USDJPY": {"pip": 0.01, "point": 0.001, "von_quy_doi": 150.0, "da_doi_chieu": True}}),
                                encoding="utf-8")
    moi_truong["df"] = _chuoi(k=150 / 0.95)
    r = TN.quet_luoi("USDJPY", "M15", CD, GRID)
    assert r["quy_cach"]["ma"] == "USDJPY" and r["trang_thai"] in ("DAT", "AM"), r.get("ly_do")
    assert r["von"] == 10000.0 and r["o_tot_nhat"] is not None
    d = TN.danh_gia_luoi("USDJPY", "M15", r["tham_so_day_du"], "kham_pha", von=10000.0)
    assert d["quy_cach"]["von_quy_doi"] == 150.0
    assert d["tien"]["loi_suat_nam_pct"] == r["o_tot_nhat"]["loi_suat_nam_pct"]
    assert d["tien"]["loi_suat_o_tran_pct"] == r["o_tot_nhat"]["loi_suat_o_tran_pct"]
    assert d["tien"]["moc_duoi_tran_pct"] == r["moc_duoi_tran_pct"]


def test_o_tot_nhat_cua_quet_chay_lai_bang_thu_luoi_ra_dung_so(moi_truong):
    """Duong di tiep cua quet: `tham_so_day_du` cua o tot nhat dua thang vao `thu_luoi` (cung doan kham_pha) phai ra DUNG con so
    ma bang quet da bao - neu khong, 'o tot nhat' cua quet khong dung duoc o buoc sau."""
    r = TN.quet_luoi("AUDCAD", "M15", CD, GRID)
    assert r["trang_thai"] in ("DAT", "AM") and r["o_tot_nhat"] is not None, r
    tot = r["o_tot_nhat"]
    d = TN.danh_gia_luoi("AUDCAD", "M15", r["tham_so_day_du"], "kham_pha", von=10000.0)
    assert d["tien"]["loi_suat_o_tran_pct"] == tot["loi_suat_o_tran_pct"]
    assert d["tien"]["he_so_lot_tai_tran"] == tot["he_so_lot_tai_tran"] and d["lenh"]["so_lenh"] == tot["so_lenh"]
    assert d["tien"]["hon_moc_pct"] == tot["hon_moc_pct"] and d["tien"]["moc_duoi_tran_pct"] == r["moc_duoi_tran_pct"]


def test_nhan_py_va_nhan_c_cho_cung_bang_o_muc_quet(moi_truong, monkeypatch):
    monkeypatch.setenv("LUOI_NHAN", "auto")
    if LN.lay_nhan() is None:
        pytest.skip("khong co nhan C: %s" % LN.trang_thai()["ly_do"])
    r_c = TN.quet_luoi("AUDCAD", "M15", CD_LON, GRID_LON)
    monkeypatch.setenv("LUOI_NHAN", "py")
    _so_tay_moi(moi_truong, monkeypatch, "py.db")
    r_py = TN.quet_luoi("AUDCAD", "M15", CD_LON, GRID_LON)
    assert r_c["nhan_c"] is True and r_py["nhan_c"] is False
    assert any("nhan C chua san sang" in c for c in r_py["canh_bao"]) and not any("nhan C" in c for c in r_c["canh_bao"])
    assert _doi_chung(r_c) == _doi_chung(r_py)


def test_so_luong_khong_doi_bang_quet(moi_truong, monkeypatch):
    kq = {}
    for n in ("1", "4"):
        monkeypatch.setenv("NC_QUET_LUONG", n)
        _so_tay_moi(moi_truong, monkeypatch, "luong%s.db" % n)
        kq[n] = TN.quet_luoi("AUDCAD", "M15", CD_LON, GRID_LON)
    assert kq["1"]["luong"] == 1 and kq["4"]["luong"] == 4
    assert kq["1"]["so_o"] == kq["4"]["so_o"] == 54
    assert _doi_chung(kq["1"]) == _doi_chung(kq["4"])


@pytest.mark.parametrize("env, mong", [("3", 3), ("0", 1), ("-5", 1)])
def test_luong_theo_bien_moi_truong(monkeypatch, env, mong):
    monkeypatch.setenv("NC_QUET_LUONG", env)
    assert TN._luong_quet_luoi() == mong


def test_luong_mac_dinh_khi_bien_rong_hoac_rac(monkeypatch):
    for v in ("", "nhieu", "2.5"):
        monkeypatch.setenv("NC_QUET_LUONG", v)
        assert 1 <= TN._luong_quet_luoi() <= 6
    monkeypatch.delenv("NC_QUET_LUONG")
    assert 1 <= TN._luong_quet_luoi() <= 6


def test_luong_khong_vuot_so_o(moi_truong, monkeypatch):
    monkeypatch.setenv("NC_QUET_LUONG", "8")
    r = TN.quet_luoi("AUDCAD", "M15", CD, {"buoc": [10, 15, 20]})
    assert r["luong"] == 3 and r["so_o"] == 3


# ------------------------------------------------------------------ 2. KHONG THEM DUONG VAO DOAN KHAC
def test_quet_ghi_mot_dong_kham_pha_va_dem_dung_phep_thu(moi_truong):
    r = TN.quet_luoi("AUDCAD", "M15", CD, GRID, gt_id=None)
    assert r["so_o_tong"] == r["so_o"] == 6
    rows = ST.nhieu("SELECT * FROM thi_nghiem WHERE loai='quet_luoi'")
    assert len(rows) == 1, rows
    w = rows[0]
    assert (w["doan"], w["ma"], w["khung"]) == ("kham_pha", "AUDCAD", "M15")
    assert w["so_phep_thu"] == 6 and w["trang_thai"] == r["trang_thai"]
    assert ST.dem_phep_thu(ma="AUDCAD", khung="M15", doan="kham_pha") == 6
    assert ST.dem_phep_thu(ma="AUDCAD", khung="M15", doan="xac_nhan") == 0
    assert set(moi_truong["doan"]) == {"kham_pha"}, "quet khong duoc cham doan nao ngoai kham_pha"
    # chay lai y het: tra ket qua cu, KHONG ghi them dong va KHONG tinh them phep thu
    r2 = TN.quet_luoi("AUDCAD", "M15", CD, GRID)
    assert str(r["tn_id"]) in r2["tu_so_tay"]
    assert len(ST.nhieu("SELECT id FROM thi_nghiem WHERE loai='quet_luoi'")) == 1
    assert ST.dem_phep_thu(ma="AUDCAD", khung="M15", doan="kham_pha") == 6


def test_quet_khong_vao_bang_thi_nghiem_tot_nhat_cua_so_tay(moi_truong):
    """Quet bi loai co chu y khoi `thi_nghiem_tot_nhat` (chon o tot nhat trong N o = thien lech chon loc); phep do that sau do thi vao."""
    r = TN.quet_luoi("AUDCAD", "M15", CD, GRID)
    assert r["trang_thai"] == "DAT", r["ly_do"]
    assert ST.tom_tat()["thi_nghiem_tot_nhat"] == []
    d = TN.danh_gia_luoi("AUDCAD", "M15", r["tham_so_day_du"], "kham_pha", von=10000.0)
    assert d["trang_thai"] == "DAT"
    tot = ST.tom_tat()["thi_nghiem_tot_nhat"]
    assert [x["loai"] for x in tot] == ["luoi"] and tot[0]["cagr_duoi_tran_pct"] == r["o_tot_nhat"]["loi_suat_o_tran_pct"]


def test_khong_co_duong_nao_dua_quet_sang_xac_nhan_hay_niem_phong(moi_truong):
    assert "doan" not in inspect.signature(TN.quet_luoi).parameters
    with pytest.raises(TypeError):
        TN.quet_luoi("AUDCAD", "M15", CD, GRID, doan="xac_nhan")
    sch = CC.THEO_TEN["quet_luoi"]["schema"]
    assert "doan" not in sch["properties"] and sch["required"] == ["ma", "khung", "luoi"]
    for doan in ("xac_nhan", "niem_phong"):
        r = CC.goi("quet_luoi", {"ma": "AUDCAD", "khung": "M15", "luoi": GRID, "doan": doan})
        assert "khong co trong schema" in r["loi"]
    assert moi_truong["doan"] == [] and ST.nhieu("SELECT id FROM thi_nghiem") == []


def test_doi_phien_ban_engine_thi_so_tay_khong_tai_dung_ket_qua_cu(moi_truong, monkeypatch):
    for ma in ("AUDCAD", "USDCHF"):
        r0 = TN.quet_luoi(ma, "M15", CD, GRID)
        assert "tu_so_tay" in TN.quet_luoi(ma, "M15", CD, GRID)                            # cung phien ban: dung lai
        monkeypatch.setattr(LU, "PHIEN_BAN_ENGINE", LU.PHIEN_BAN_ENGINE + 1)
        r1 = TN.quet_luoi(ma, "M15", CD, GRID)
        assert "tu_so_tay" not in r1, "van tay quet khong gom phien ban engine (%s)" % ma
        assert r1["bang_top"] == r0["bang_top"]                                              # engine that khong doi gi o day
        monkeypatch.setattr(LU, "PHIEN_BAN_ENGINE", LU.PHIEN_BAN_ENGINE - 1)


def test_doi_phi_hoac_tham_so_quet_thi_khong_lay_ket_qua_cu(moi_truong):
    TN.quet_luoi("USDCHF", "M15", CD, GRID)
    moi_truong["cp"] = _cp(pm=0.30, pb=0.30, do_tin="SAN")                  # phi qua dem dat gap 15 lan: quy cach khac -> van tay khac
    assert "tu_so_tay" not in TN.quet_luoi("USDCHF", "M15", CD, GRID)
    for kw in (dict(co_dinh={"tran_tang": 10}, luoi=GRID), dict(co_dinh=CD, luoi={"buoc": [10, 15, 20], "tp": [8, 12, 16]}),
               dict(co_dinh=CD, luoi=GRID, von=5000.0), dict(co_dinh=CD, luoi=GRID, hat=9)):
        assert "tu_so_tay" not in TN.quet_luoi("USDCHF", "M15", **kw), kw
    assert "tu_so_tay" in TN.quet_luoi("USDCHF", "M15", CD, GRID), "cung dau vao va cung phi phai dung lai duoc"


# ------------------------------------------------------------------ 3. LAY MAU, THU TU O, DONG HO
def _ghi_o(monkeypatch):
    """Ghi lai cac o ma `quet_luoi` that su chay (theo thu tu), van chay engine that."""
    chay = []
    goc = TN._o_luoi

    def ghi(dl, cd, o, von_q, moc):
        chay.append(dict(o))
        return goc(dl, cd, o, von_q, moc)

    monkeypatch.setattr(TN, "_o_luoi", ghi)
    return chay


def test_thu_tu_o_nhu_itertools_product(moi_truong, monkeypatch):
    monkeypatch.setenv("NC_QUET_LUONG", "1")
    chay = _ghi_o(monkeypatch)
    luoi = {"buoc": [10, 15, 20], "tp": [8, 12], "he_so_lot": [1.0, 1.2]}
    r = TN.quet_luoi("AUDCAD", "M15", CD, luoi)
    assert chay == [dict(zip(luoi, p)) for p in itertools.product(*luoi.values())]
    assert r["so_o_tong"] == r["so_o"] == 12 and "lay_mau" not in r


def test_lay_mau_theo_hat_xac_dinh_va_dem_dung_so_o(moi_truong, monkeypatch):
    monkeypatch.setenv("NC_QUET_LUONG", "1")
    chay = _ghi_o(monkeypatch)
    luoi = {"buoc": [10, 12, 15, 18, 20, 25], "tp": [6, 8, 10, 12]}                   # 24 o
    tap = {}
    for hat in (3, 3, 4, 5, 6, 7):
        _so_tay_moi(moi_truong, monkeypatch, "h%d_%d.db" % (hat, len(chay)))
        n0 = len(chay)
        r = TN.quet_luoi("AUDCAD", "M15", CD, luoi, toi_da_o=7, hat=hat)
        moi = chay[n0:]
        assert len(moi) == 7 and r["so_o"] == 7 and len({tuple(sorted(o.items())) for o in moi}) == 7
        assert r["lay_mau"] == {"hat": hat, "so_o_tong": 24, "chon": 7} and r["so_o_tong"] == 24
        assert all(o["buoc"] in luoi["buoc"] and o["tp"] in luoi["tp"] for o in moi)
        if hat in tap:
            assert tap[hat] == moi, "cung hat phai ra cung tap o, cung thu tu"
        tap[hat] = moi
        assert ST.nhieu("SELECT so_phep_thu n FROM thi_nghiem WHERE loai='quet_luoi'")[0]["n"] == 7
    assert len({tuple(map(lambda o: tuple(sorted(o.items())), v)) for v in tap.values()}) >= 2, "hat khac nhau phai ra tap khac nhau"


def test_tran_so_o_bi_kep_va_gia_tri_trung_trong_truc_bi_go(moi_truong, monkeypatch):
    dem = []

    def gia(dl, cd, o, von_q, moc):
        dem.append(o)
        return {"tham_so": o, "chay": False, "so_lenh": 50, "co_lai": True, "loi_suat_nam_pct": 1.0, "maxdd_pct": -1.0,
                "he_so_lot_tai_tran": 2.0, "loi_suat_o_tran_pct": 2.0, "hon_moc_pct": 1.0}

    monkeypatch.setattr(TN, "_o_luoi", gia)
    monkeypatch.setenv("NC_QUET_LUONG", "3")
    luoi = {"buoc": list(range(5, 45)), "tp": list(range(5, 45)), "cho_lui": [0.0, 3.0, 6.0]}   # 40 x 40 x 3 = 4.800 o
    r = TN.quet_luoi("AUDCAD", "M15", CD, luoi, toi_da_o=5000)                         # tran cung = 3.000 (nang tu 1.000 o commit 3eee6f3b)
    assert len(dem) == 3000 and r["lay_mau"]["chon"] == 3000 and r["so_o_tong"] == 4800 and r["so_o"] == 3000
    assert ST.nhieu("SELECT so_phep_thu n FROM thi_nghiem WHERE loai='quet_luoi'")[0]["n"] == 3000
    dem.clear()
    r = TN.quet_luoi("AUDCAD", "M15", CD, {"buoc": [10, 10, 15, 15, 20], "tp": [8, 12]}, toi_da_o=0)
    assert r["luoi"]["buoc"] == [10, 15, 20] and r["so_o_tong"] == 6, "gia tri trung phai bi go"
    assert len(dem) == 1 and r["so_o"] == 1, "toi_da_o < 1 phai kep ve 1"


def test_bang_giu_thu_tu_o_du_cac_luong_xong_lech_nhau(moi_truong, monkeypatch):
    """`bang` (va moi thu doc tu no) theo thu tu O, khong theo thu tu luong nao xong truoc: o dau cham nhat."""
    def cham(dl, cd, o, von_q, moc):
        time.sleep(0.02 * (19 - o["buoc"]) / 9)
        return {"tham_so": o, "chay": False, "so_lenh": 0, "co_lai": False, "loi_suat_nam_pct": 0.0, "maxdd_pct": 0.0,
                "he_so_lot_tai_tran": None, "loi_suat_o_tran_pct": None, "hon_moc_pct": None}

    monkeypatch.setattr(TN, "_o_luoi", cham)
    monkeypatch.setenv("NC_QUET_LUONG", "4")
    r = TN.quet_luoi("AUDCAD", "M15", CD, {"buoc": list(range(10, 20))})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r["luong"] == 4
    assert [x["tham_so"]["buoc"] for x in r["bang"]] == list(range(10, 20))


def test_o_het_gio_khong_tinh_phep_thu_va_khong_doc_hinh_dang(moi_truong):
    r = TN.quet_luoi("AUDCAD", "M15", CD, GRID, ngan_giay=-1.0)                         # da qua han ngay tu dau
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "HET GIO" in r["ly_do"]
    assert r["het_gio"] == {"da_chay": 0, "bo_lai": 6, "ngan_giay": -1.0} and r["so_o"] == 0
    assert "hinh_dang" not in r and "bang_top" not in r
    w = ST.nhieu("SELECT * FROM thi_nghiem WHERE loai='quet_luoi'")[0]
    assert w["so_phep_thu"] == 0 and w["trang_thai"] == "CHUA_DO_DUOC"
    # CHUA_DO_DUOC khong vao so tay nhu ket qua da thu: chay lai that, khong lay cai cu
    r2 = TN.quet_luoi("AUDCAD", "M15", CD, GRID)
    assert "tu_so_tay" not in r2 and r2["so_o"] == 6 and r2["trang_thai"] in ("DAT", "AM")


def test_het_gio_giua_chung_chi_tinh_o_da_chay_va_khong_ket_luan_hinh_dang(moi_truong, monkeypatch):
    """Dong ho gia: moi o chay 'ton' 10 giay, ngan 25 giay -> 3 o chay, 3 o bo lai. Phan da chay khong phai mau ngau nhien cua luoi
    (cac o xep theo thu tu truc) nen khong duoc doc hinh dang, du ca 3 o deu co lai."""
    class Dong:
        t = 1000.0

        def time(self):
            return self.t

    dong = Dong()
    goc = TN._o_luoi

    def ton(dl, cd, o, von_q, moc):
        kq = goc(dl, cd, o, von_q, moc)
        dong.t += 10.0
        return kq

    monkeypatch.setattr(TN, "time", dong)
    monkeypatch.setattr(TN, "_o_luoi", ton)
    monkeypatch.setenv("NC_QUET_LUONG", "1")
    r = TN.quet_luoi("AUDCAD", "M15", CD, GRID, ngan_giay=25.0)
    assert r["so_o"] == 3 and r["het_gio"]["bo_lai"] == 3 and r["trang_thai"] == "CHUA_DO_DUOC"
    assert "hinh_dang" not in r and ST.nhieu("SELECT so_phep_thu n FROM thi_nghiem")[0]["n"] == 3


# ------------------------------------------------------------------ 4. HINH DANG LA NHAN; O CHAY KHONG BAO GIO LA O CO LAI
def _dong(ts: dict, lai):
    return {"tham_so": ts, "co_lai": lai is not None, "loi_suat_o_tran_pct": lai}


def test_hinh_dang_cao_nguyen():
    luoi = {"a": [1, 2, 3, 4, 5]}
    bang = [_dong({"a": v}, lai) for v, lai in zip(luoi["a"], (10.0, 12.0, 30.0, 14.0, 9.0))]
    r = TN._doc_hinh_dang_luoi(bang, luoi)
    assert r["hinh_dang"] == "CAO_NGUYEN" and r["ty_le_o_co_lai"] == 1.0 and r["o_tot_nhat"]["tham_so"] == {"a": 3}
    assert r["hang_xom"] == {"so": 2, "ty_le_co_lai": 1.0, "loi_suat_o_tran_tb_pct": 13.0}


def test_hinh_dang_cai_gai_khi_chi_mot_o_co_lai():
    luoi = {"a": [1, 2, 3, 4, 5]}
    bang = [_dong({"a": v}, 40.0 if v == 3 else None) for v in luoi["a"]]
    r = TN._doc_hinh_dang_luoi(bang, luoi)
    assert r["hinh_dang"] == "CAI_GAI" and r["ty_le_o_co_lai"] == 0.2
    assert r["hang_xom"]["so"] == 2 and r["hang_xom"]["ty_le_co_lai"] == 0.0 and r["hang_xom"]["loi_suat_o_tran_tb_pct"] is None


def test_hinh_dang_hon_hop_o_giua_hai_nguong():
    luoi = {"a": [1, 2, 3], "b": [1, 2, 3]}
    co_lai = {(1, 1), (1, 2), (2, 2), (3, 2), (3, 3)}                                   # 5/9 = 0,556
    bang = [_dong({"a": a, "b": b}, 10.0 + a + b if (a, b) in co_lai else None) for a in (1, 2, 3) for b in (1, 2, 3)]
    r = TN._doc_hinh_dang_luoi(bang, luoi)
    assert r["hinh_dang"] == "HON_HOP" and r["o_tot_nhat"]["tham_so"] == {"a": 3, "b": 3}


def test_dinh_don_le_giua_vung_co_lai_van_khong_phai_cao_nguyen():
    """8/10 o co lai nhung o tot nhat co ca hai hang xom lo: day la DINH nhon trong mot vung, khong phai mot vung vung."""
    luoi = {"a": list(range(10))}
    lai = {i: 10.0 for i in range(10)}
    lai[4] = lai[6] = None
    lai[5] = 99.0
    bang = [_dong({"a": i}, lai[i]) for i in range(10)]
    r = TN._doc_hinh_dang_luoi(bang, luoi)
    assert r["ty_le_o_co_lai"] == 0.8 and r["o_tot_nhat"]["tham_so"] == {"a": 5}
    assert r["hang_xom"]["ty_le_co_lai"] == 0.0 and r["hinh_dang"] == "HON_HOP"


def test_khong_o_nao_co_lai():
    luoi = {"a": [1, 2, 3]}
    r = TN._doc_hinh_dang_luoi([_dong({"a": v}, None) for v in luoi["a"]], luoi)
    assert r == {"hinh_dang": "KHONG_CO_LAI", "ty_le_o_co_lai": 0.0, "o_tot_nhat": None, "hang_xom": None}


def test_o_chay_tai_khoan_khong_bao_gio_la_o_co_lai():
    """Chuoi troi xuong, mua chat tang, von nho: tai khoan chay giua chung -> khong duoc xep o co lai, khong co he so lot o tran."""
    ts, von, kw = CASES["chay_giua_chung"]
    dl = LU.chuan_bi(_chuoi(**kw))
    cd = {k: v for k, v in ts.items() if k != "tran_tang"}
    dong = TN._o_luoi(dl, cd, {"tran_tang": 30}, von, 5.0)
    assert dong["chay"] is True and dong["co_lai"] is False
    assert dong["he_so_lot_tai_tran"] is None and dong["loi_suat_o_tran_pct"] is None and dong["hon_moc_pct"] is None
    r = TN._doc_hinh_dang_luoi([dong], {"tran_tang": [30]})
    assert r["hinh_dang"] == "KHONG_CO_LAI" and r["o_tot_nhat"] is None


def test_o_chay_lam_tut_ty_le_co_lai_thay_vi_bi_bo_khoi_mau():
    luoi = {"a": list(range(10))}
    co_lai = [_dong({"a": i}, 10.0 + i) for i in range(5)]
    chay = [{"tham_so": {"a": i}, "co_lai": False, "chay": True, "loi_suat_o_tran_pct": None} for i in range(5, 10)]
    r = TN._doc_hinh_dang_luoi(co_lai + chay, luoi)
    assert r["ty_le_o_co_lai"] == 0.5, "5 o chay tai khoan phai nam trong mau so"
    r = TN._doc_hinh_dang_luoi(co_lai, {"a": list(range(5))})
    assert r["ty_le_o_co_lai"] == 1.0                                                   # ... va neu bo no di thi ty le dep hon gia


def test_engine_nem_loi_thanh_dong_loi_khong_lam_hong_ca_luot_quet(moi_truong, monkeypatch):
    goc = LU.chay_mang
    n = {"i": 0}

    def hong(dl, ts, von, ghi_lenh=False):
        n["i"] += 1
        if n["i"] == 2:
            raise ZeroDivisionError("gia lap")
        return goc(dl, ts, von, ghi_lenh)

    monkeypatch.setattr(LU, "chay_mang", hong)
    monkeypatch.setenv("NC_QUET_LUONG", "1")
    r = TN.quet_luoi("AUDCAD", "M15", CD, GRID)
    assert r["so_o"] == 6 and r["so_o_loi"] == 1 and "ZeroDivisionError" in r["vi_du_loi"]["loi"]
    assert r["so_o_do_duoc"] <= 5 and r["trang_thai"] in ("DAT", "AM")


def test_quet_tren_chuoi_hoi_quy_ra_cao_nguyen_va_tren_chuoi_troi_xuong_khong(moi_truong, monkeypatch):
    """Doi chung hai chieu: cung luoi tham so, chuoi HOI QUY (luoi co viec de lam) -> cao nguyen co lai; chuoi TROI XUONG mot chieu
    voi lenh mua -> khong duoc phep co `DAT` (lai cua luoi mua tren chuoi khong hoi quy la ao: tien o lo treo)."""
    r = TN.quet_luoi("AUDCAD", "M15", CD_LON, GRID_LON)
    assert r["hinh_dang"] == "CAO_NGUYEN" and r["trang_thai"] == "DAT", r["ly_do"]
    assert r["so_o"] == 54 and r["ty_le_o_co_lai"] >= 0.6
    _so_tay_moi(moi_truong, monkeypatch, "troi.db")
    moi_truong["df"] = _chuoi(xu_huong=-4e-5, hoi_quy=0.0)
    r = TN.quet_luoi("AUDCAD", "M15", {"che_do": "mua", "tran_tang": 12, "tp": 10}, {"buoc": [8, 12, 16, 20, 25], "he_so_lot": [1.0, 1.3]},
                     von=1000.0)
    assert r["trang_thai"] != "DAT", (r["trang_thai"], r.get("ly_do"))


# ------------------------------------------------------------------ 5. DAU VAO SAI -> chan TRUOC khi nap du lieu
@pytest.mark.parametrize("kw, tu_khoa", [
    (dict(luoi={}), "thieu `luoi`"),
    (dict(luoi=None), "thieu `luoi`"),
    (dict(luoi={"khong_co": [1, 2]}), "khong biet"),
    (dict(luoi={"buoc": [10, 15]}, co_dinh={"khong_co": 1}), "khong biet"),
    (dict(luoi={"buoc": [10, 15]}, co_dinh={"buoc": 10}), "ca `co_dinh` lan `luoi`"),
    (dict(luoi={"dung_lo_tong": [0.0, 200.0]}), "CHUA cai dat"),
    (dict(luoi={"buoc": [10, 15]}, co_dinh={"dung_lo_tong": 500.0}), "CHUA cai dat"),
    (dict(luoi={"buoc": []}), "khong rong"),
    (dict(luoi={"buoc": 10}), "danh sach gia tri don"),
    (dict(luoi={"buoc": [[1, 2], [3]]}), "danh sach gia tri don"),
    (dict(luoi={"buoc": [{"a": 1}]}), "danh sach gia tri don"),
    (dict(luoi={k: [1, 2] for k in ("buoc", "tp", "tran_tang", "lot", "he_so_lot", "buoc_tran", "cho_lui")}), "toi da 6 truc"),
    (dict(luoi={"buoc": list(range(1, 42))}), "> 40"),
])
def test_dau_vao_sai_bi_tu_choi_truoc_khi_nap_du_lieu(moi_truong, monkeypatch, kw, tu_khoa):
    monkeypatch.setattr(NDL, "nap", _khong_duoc_goi)
    r = TN.quet_luoi("USDCHF", "M15", **kw)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and tu_khoa in r["ly_do"], r
    assert ST.nhieu("SELECT id FROM thi_nghiem") == [], "dau vao sai khong duoc ghi so tay (khong phai phep thu)"


def test_ma_chua_ho_tro_hoac_chua_doi_chieu_van_tu_choi(moi_truong, monkeypatch):
    monkeypatch.setattr(NDL, "nap", _khong_duoc_goi)
    for ma, tk in (("USDJPY", "doi chieu"), ("XAUUSD", "doi chieu"), ("US500Cash", "chua ho tro")):
        r = TN.quet_luoi(ma, "M15", CD, GRID)
        assert r["trang_thai"] == "CHUA_DO_DUOC" and tk in r["ly_do"], (ma, r)


def test_it_o_do_duoc_thi_chua_do_duoc_kem_bang(moi_truong):
    r = TN.quet_luoi("AUDCAD", "M15", CD, {"buoc": [10, 15]})                           # 2 o: chua du de doc hinh dang
    assert r["trang_thai"] == "CHUA_DO_DUOC" and [x["tham_so"] for x in r["bang"]] == [{"buoc": 10}, {"buoc": 15}]
    assert "hinh_dang" not in r
    assert r["so_o"] == 2 and "can >= 3 o" in r["ly_do"]


def test_canh_bao_kieu_lot_khac_phang_va_chi_phi_khai(moi_truong):
    r = TN.quet_luoi("AUDCAD", "M15", dict(CD, kieu_lot="nhan"), {"buoc": [10, 15, 20, 25]})
    assert any("kieu_lot != phang" in c for c in r["canh_bao"])
    r = TN.quet_luoi("AUDCAD", "M15", CD, {"buoc": [10, 15, 20, 25], "kieu_lot": ["phang", "nhan"], "he_so_lot": [1.2]})
    assert any("kieu_lot != phang" in c for c in r["canh_bao"]), "kieu_lot nam o mot truc cung phai canh bao"
    r = TN.quet_luoi("AUDCAD", "M15", CD, {"buoc": [10, 15, 20, 25]})
    assert not any("kieu_lot" in c for c in r["canh_bao"])
    moi_truong["cp"] = _cp(do_tin="KHAI")
    r = TN.quet_luoi("USDCHF", "M15", CD, GRID)
    assert any("KHAI" in c for c in r["canh_bao"]) and any("tester" in c or "doi chieu" in c for c in r["canh_bao"])
    assert r["chi_phi_do_tin"] == "KHAI" and r["trang_thai"] in ("DAT", "AM")


# ------------------------------------------------------------------ 6. CONG CU (kenh AI)
def test_dang_ky_cuoi_bo_cong_cu_de_giu_cache_prompt():
    ten = [c["ten"] for c in CC.CONG_CU]
    assert ten.count("quet_luoi") == 1 and ten.index("quet_luoi") > ten.index("boc_lich_su")
    s = [t for t in CC.schema_api() if t["name"] == "quet_luoi"][0]
    assert "luoi" in s["input_schema"]["properties"] and len(s["description"]) > 200
    assert "LUA CHON" in s["description"], "mo ta phai noi o tot nhat la lua chon, chua phai phep do"


def test_goi_qua_cong_cu_ra_ket_qua_va_ghi_so(moi_truong):
    r = CC.goi("quet_luoi", {"ma": "AUDCAD", "khung": "M15", "luoi": GRID, "co_dinh": CD, "hat": 1, "toi_da_o": 100})
    assert r["trang_thai"] in ("DAT", "AM") and "tn_id" in r and "_giay" in r, r
    assert "thieu tham so" in CC.goi("quet_luoi", {"ma": "AUDCAD", "khung": "M15"})["loi"]
    r2 = CC.goi("quet_luoi", {"ma": "AUDCAD", "khung": "M15", "luoi": GRID, "co_dinh": CD, "hat": 1, "toi_da_o": 100})
    assert "tu_so_tay" in r2


def test_chuoi_tong_hop_chay_duoc_va_co_canh_bao_ong_dan():
    """Duong that, khong gia lap nap du lieu: chuoi TONG_HOP (dung cho kiem duong ong) qua ca `nap`, `cat_doan`, `chi_phi`."""
    dv = {"ma": "TONG_HOP_NHIEU_1", "khung": "H1", "luoi": {"buoc": [30, 40, 50], "tp": [20, 30]},
          "co_dinh": {"tran_tang": 8, "che_do": "hai_chieu"}}
    r = CC.goi("quet_luoi", dv)
    assert r["trang_thai"] in ("DAT", "AM", "CHUA_DO_DUOC"), r
    assert r["so_o"] == 6 and any("TONG_HOP" in c for c in r["canh_bao"])
    if r["trang_thai"] != "CHUA_DO_DUOC":                       # CHUA_DO_DUOC khong vao so tay nhu ket qua da thu
        assert "tu_so_tay" in CC.goi("quet_luoi", dv)


def test_che_do_thua_roi_min_tim_dinh_va_re_hon_quet_day(moi_truong, monkeypatch):
    """Tang 1 quet thua (chi so chan + cuoi), tang 2 don quanh top: dinh o chi so le van duoc tim, chi phi << quet day."""
    dem = []
    dinh = (7, 11)                                                  # le, le: KHONG nam o tang 1

    def gia(dl, cd, o, von_q, moc):
        dem.append(o)
        x, y = o["buoc"], o["tp"]
        diem = 100 - abs(x - dinh[0]) - abs(y - dinh[1])
        return {"tham_so": o, "chay": False, "so_lenh": 50, "co_lai": diem > 0, "loi_suat_nam_pct": float(diem),
                "maxdd_pct": -1.0, "he_so_lot_tai_tran": 1.0, "loi_suat_o_tran_pct": float(diem), "hon_moc_pct": 1.0}

    monkeypatch.setattr(TN, "_o_luoi", gia)
    monkeypatch.setenv("NC_QUET_LUONG", "1")
    luoi = {"buoc": list(range(1, 21)), "tp": list(range(1, 21))}   # 400 o
    r = TN.quet_luoi("AUDCAD", "M15", CD, luoi, toi_da_o=3000, che_do="thua_roi_min")
    assert r["che_do"]["ten"] == "thua_roi_min" and r["che_do"]["so_o_day_du"] == 400
    assert len(dem) == r["so_o"] < 400 // 2
    assert r["o_tot_nhat"]["tham_so"] == {"buoc": 7, "tp": 11}
    assert len({tuple(sorted(o.items())) for o in dem}) == len(dem), "khong o nao chay hai lan"
    assert TN.quet_luoi("AUDCAD", "M15", CD, luoi, che_do="la")["trang_thai"] == "CHUA_DO_DUOC"


# ------------------------------------------------------------------ TRAN DON BAY CUA XEP HANG (08/10/2026)
class _KQ:
    def __init__(self, margin):
        self.margin = margin


def test_he_so_lot_hop_le_chan_boi_don_bay_khi_don_bay_chan_truoc():
    """k cham tran maxDD = 400 nhung lot dang thu da la don bay 0,5 -> k toi da theo don bay = 10 / 0,5 = 20 < 400."""
    k, gh, d1 = TN._he_so_lot_hop_le(_KQ(margin=50.0), don_bay_tk=100.0, von=10000.0, k_dd=400.0)    # 50 x 100 / 10000 = 0,5
    assert gh == "TRAN_DON_BAY" and d1 == 0.5 and abs(k - 20.0) < 1e-9


def test_he_so_lot_hop_le_giu_nguyen_khi_maxdd_chan_truoc():
    k, gh, d1 = TN._he_so_lot_hop_le(_KQ(margin=50.0), 100.0, 10000.0, 12.0)       # 12 x 0,5 = don bay 6 <= 10: maxDD chan truoc
    assert (k, gh, d1) == (12.0, "TRAN_DD", 0.5)


def test_he_so_lot_hop_le_khong_tinh_duoc_thi_none():
    assert TN._he_so_lot_hop_le(_KQ(10.0), 100.0, 10000.0, None) == (None, None, None)
    assert TN._he_so_lot_hop_le(_KQ(10.0), 100.0, 10000.0, 0.0) == (None, None, None)


def test_loi_suat_o_tran_khong_bao_gio_vuot_tran_don_bay(moi_truong):
    """Tren cac o that cua `danh_gia_luoi`: loi suat o tran <= ban cu (chi tran maxDD), va neu tran don bay chan thi
    don bay dinh sau khi nhan lot dung bang 10 (khong vuot)."""
    for _dong, d in _mot_o_vs_danh_gia(moi_truong, "AUDCAD"):
        t = d["tien"]
        if t["he_so_lot_tai_tran"] is None:
            continue
        assert t["loi_suat_o_tran_pct"] <= t["loi_suat_chi_tran_dd_pct"] + 1e-6
        assert t["don_bay_dinh_o_lot_thu"] * t["he_so_lot_tai_tran"] <= TN.L_TOI_DA + 0.05, t          # +0,05: sai so lam tron hai con so da in
        if t["gioi_han_lot"] == "TRAN_DON_BAY":
            assert abs(t["don_bay_dinh_o_lot_thu"] * t["he_so_lot_tai_tran"] - TN.L_TOI_DA) < 0.05, t


def test_ket_qua_so_tay_cu_khuyet_tran_don_bay_duoc_tinh_lai_va_khong_dem_them_phep_thu(moi_truong):
    ts = dict(CD, buoc=10, tp=8)
    d1 = TN.danh_gia_luoi("AUDCAD", "M15", ts, "kham_pha", von=10000.0)
    assert "tu_so_tay" not in d1 and d1["tien"]["gioi_han_lot"] in ("TRAN_DD", "TRAN_DON_BAY"), d1
    d1b = TN.danh_gia_luoi("AUDCAD", "M15", ts, "kham_pha", von=10000.0)                    # y het -> lay lai tu so tay
    assert d1b.get("tu_so_tay") and d1b["tien"] == d1["tien"]
    so_truoc = ST.nhieu("SELECT COALESCE(SUM(so_phep_thu),0) n FROM thi_nghiem WHERE loai='luoi'")[0]["n"]
    # gia lap ban ghi TRUOC 08/10/2026: tien khong co cac truong tran don bay
    cu = dict(d1)
    cu["tien"] = {k: v for k, v in d1["tien"].items() if k not in ("gioi_han_lot", "don_bay_dinh_o_lot_thu", "loi_suat_chi_tran_dd_pct")}
    cu.pop("tn_id", None)
    with ST.ket_noi() as cn:
        cn.execute("UPDATE thi_nghiem SET ket_qua=? WHERE id=?", (json.dumps(cu), d1["tn_id"]))
    d2 = TN.danh_gia_luoi("AUDCAD", "M15", ts, "kham_pha", von=10000.0)
    assert "tu_so_tay" not in d2 and d2["tien"] == d1["tien"], "ban ghi cu khuyet truong -> phai tinh lai ra dung so moi"
    so_sau = ST.nhieu("SELECT COALESCE(SUM(so_phep_thu),0) n FROM thi_nghiem WHERE loai='luoi'")[0]["n"]
    assert so_sau == so_truoc, "tinh lai cung phep thu khong duoc dem them phep thu"
