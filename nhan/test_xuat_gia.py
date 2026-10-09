import gzip
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import xuat_gia as X


def _df(n=50):
    i = pd.date_range("2024-01-01", periods=n, freq="15min", tz="Europe/Athens")
    p = 0.9 + np.cumsum(np.random.default_rng(1).normal(0, 1e-4, n))
    return pd.DataFrame({"open": p, "high": p + 1e-4, "low": p - 1e-4, "close": p, "tick_volume": 5, "spread": 3}, index=i)


def _m1(tu="2018-06-30 23:58", den="2019-01-01 00:02", tz=None):
    """Bar M1 lien tuc (khong bo cuoi tuan - chi can de thu bien cua so)."""
    i = pd.date_range(tu, den, freq="1min", tz=tz)
    p = 0.95 + np.cumsum(np.random.default_rng(7).normal(0, 1e-5, len(i)))
    return pd.DataFrame({"open": p, "high": p + 2e-5, "low": p - 2e-5, "close": p, "tick_volume": 7.0, "spread": 12.0}, index=i)


def test_khu_tron():
    d = Path(tempfile.mkdtemp()); sl = Path(tempfile.mkdtemp())
    m = X.ghi(_df(), "AUDCAD", "M15", d, sl)
    assert m["so_bar"] == 50 and (sl / "AUDCAD_M15.csv.gz").exists()   # co ban sao luu ngoai thu muc dich
    r = X.doc("AUDCAD", "M15", d)
    assert len(r) == 50 and abs(r["close"].iloc[0] - _df()["close"].iloc[0]) < 1e-5
    assert r.index.tz is None   # UTC khong mui gio


def test_thieu_ohlc():
    try:
        X.ghi(pd.DataFrame({"x": [1]}, index=pd.date_range("2024", periods=1)), "A", "M15", Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp()))
    except ValueError:
        return
    assert False


# ------------------------------------------------------------------ ngay + ten tep
def test_doc_ngay_nam_ngay_va_moc_cuoi():
    assert X.doc_ngay(None) is None and X.doc_ngay("") is None
    assert X.doc_ngay("2018") == pd.Timestamp("2018-01-01")
    assert X.doc_ngay("2018-07-01") == pd.Timestamp("2018-07-01")
    # moc CUOI la 00:00 ngay SAU (loai tru) -> `den` gom TRON ngay cuoi
    assert X.doc_ngay("2018-12-31", cuoi=True) == pd.Timestamp("2019-01-01")
    assert X.doc_ngay("2018", cuoi=True) == pd.Timestamp("2019-01-01")
    assert X.doc_ngay("2020-02-28", cuoi=True) == pd.Timestamp("2020-02-29")      # nam nhuan


@pytest.mark.parametrize("xau", ["2018-7-1", "18", "2018-13-01", "2018-02-30", "2019-02-29", "2018-07-01T00", "abc", "2018/07/01", "2018-07"])
def test_doc_ngay_tu_choi_dinh_dang_sai_hay_ngay_khong_co(xau):
    with pytest.raises(ValueError):
        X.doc_ngay(xau)
    with pytest.raises(ValueError):
        X.ten_tep("AUDCAD", "M1", xau, None)          # khong roi vao AttributeError


def test_ten_tep():
    assert X.ten_tep("AUDCAD", "M15") == "AUDCAD_M15.csv.gz"
    assert X.ten_tep("AUDCAD", "M15", "2018") == "AUDCAD_M15.csv.gz"                         # cach cu `--tu NAM` giu ten cu
    assert X.ten_tep("AUDCAD", "M1", "2018-07-01") == "AUDCAD_M1_20180701_cuoi.csv.gz"
    assert X.ten_tep("AUDCAD", "M1", "2018-07-01", "2018-12-31") == "AUDCAD_M1_20180701_20181231.csv.gz"
    assert X.ten_tep("AUDCAD", "M1", None, "2018") == "AUDCAD_M1_dau_20181231.csv.gz"
    assert X.ten_tep("AUDCAD", "M1", "2018", "2018") == "AUDCAD_M1_20180101_20181231.csv.gz"


# ------------------------------------------------------------------ cua so
def test_cua_so_gom_tron_ngay_cuoi_va_loai_bar_ngoai():
    d, sl = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    m = X.ghi(_m1("2018-06-30 23:58", "2018-07-04 00:02"), "AUDCAD", "M1", d, sl, tu="2018-07-01", den="2018-07-03")
    r = X.doc("AUDCAD", "M1", d, "2018-07-01", "2018-07-03")
    assert str(r.index[0]) == "2018-07-01 00:00:00"           # 23:58 va 23:59 cua 30/6 bi loai
    assert str(r.index[-1]) == "2018-07-03 23:59:00"          # gom bar cuoi cung cua ngay cuoi; 00:00..00:02 ngay 4 bi loai
    assert len(r) == m["so_bar"] == 3 * 1440
    assert m["tep"] == "AUDCAD_M1_20180701_20180703.csv.gz"
    assert m["yeu_cau_tu"] == "2018-07-01" and m["yeu_cau_den"] == "2018-07-03"
    assert (sl / m["tep"]).exists()                            # sao luu ngoai git


def test_cua_so_khong_con_bar_thi_bao_loi_khong_ghi_tep_rong():
    d = Path(tempfile.mkdtemp())
    with pytest.raises(ValueError, match="khong con bar"):
        X.ghi(_df(), "AUDCAD", "M15", d, Path(tempfile.mkdtemp()), tu="2030-01-01", den="2030-12-31")
    assert not list(d.glob("*.csv.gz"))


def test_nam_cu_van_cat_tu_dau_nam_nhung_giu_ten_cu():
    d = Path(tempfile.mkdtemp())
    m = X.ghi(_m1("2017-12-31 23:58", "2018-01-01 00:02"), "EURCAD", "M1", d, Path(tempfile.mkdtemp()), tu="2018")
    assert m["tep"] == "EURCAD_M1.csv.gz" and "yeu_cau_tu" not in m
    assert m["so_bar"] == 3 and m["tu"].startswith("2018-01-01 00:00")      # 23:58 va 23:59 ngay 31/12/2017 bi cat


def test_index_co_mui_gio_duoc_doi_ve_utc_roi_moi_cat():
    d = Path(tempfile.mkdtemp())
    df = _m1("2018-12-31 20:00", "2019-01-01 03:00", tz="Europe/Athens")           # 18:00 UTC .. 01:00 UTC ngay 1/1
    m = X.ghi(df, "AUDCAD", "M1", d, Path(tempfile.mkdtemp()), tu="2018-12-31", den="2018-12-31")
    r = X.doc("AUDCAD", "M1", d, "2018-12-31", "2018-12-31")
    assert str(r.index[-1]) == "2018-12-31 23:59:00" and m["so_bar"] == len(r)
    assert str(r.index[0]) == "2018-12-31 18:00:00"           # 20:00 Athens (UTC+2) = 18:00 UTC


# ------------------------------------------------------------------ tran dung luong
def test_vuot_tran_thi_khong_ghi_gi_va_khong_dung_den_tep_cu():
    d = Path(tempfile.mkdtemp())
    X.ghi(_df(), "AUDCAD", "M15", d, Path(tempfile.mkdtemp()))
    cu = (d / "AUDCAD_M15.csv.gz").read_bytes()
    with pytest.raises(ValueError, match="vuot tran"):
        X.ghi(_m1("2018-07-01 00:00", "2018-07-01 23:59"), "AUDCAD", "M15", d, Path(tempfile.mkdtemp()), tran_byte=500)
    assert (d / "AUDCAD_M15.csv.gz").read_bytes() == cu        # tep dang co khong bi de
    assert not list(d.glob("*.tam"))                           # khong de tep tam (se bi `git add` nham)


def test_tran_mac_dinh_du_cho_nua_nam_mot_cap_m1_nhung_chan_nhieu_nam():
    d = Path(tempfile.mkdtemp())
    m = X.ghi(_m1("2018-07-01 00:00", "2018-12-31 23:59"), "AUDCAD", "M1", d, Path(tempfile.mkdtemp()))
    assert m["byte"] < X.TRAN_BYTE_MOI_FILE
    assert X.TRAN_BYTE_MOI_FILE <= 12_000_000 and X.TRAN_BYTE_MOI_LENH <= 40_000_000       # repo PUBLIC: khong ai noi long tran lang le


# ------------------------------------------------------------------ gzip co dinh
def test_xuat_lai_ra_dung_cung_byte():
    d1, d2 = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    a = X.ghi(_df(), "AUDCAD", "M15", d1, Path(tempfile.mkdtemp()))
    b = X.ghi(_df(), "AUDCAD", "M15", d2, Path(tempfile.mkdtemp()))
    assert a["sha256"] == b["sha256"]
    assert (d1 / "AUDCAD_M15.csv.gz").read_bytes() == (d2 / "AUDCAD_M15.csv.gz").read_bytes()
    with gzip.open(d1 / "AUDCAD_M15.csv.gz", "rt") as f:
        assert f.readline().strip() == "time,open,high,low,close,tick_volume,spread"


def test_gzip_khong_mang_thoi_gian_hay_ten_tep_cua_luc_ghi(monkeypatch):
    """Cung du lieu o hai LUC va hai TEN khac nhau van ra cung byte: header gzip khong co mtime (4 byte tu offset 4) va khong co co FNAME."""
    import time
    d1, d2 = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    monkeypatch.setattr(time, "time", lambda: 1_700_000_000.0)
    X.ghi(_df(), "AUDCAD", "M15", d1, Path(tempfile.mkdtemp()))
    monkeypatch.setattr(time, "time", lambda: 1_800_000_000.0)
    X.ghi(_df(), "AUDCAD", "M15", d2, Path(tempfile.mkdtemp()))
    r1, r2 = (d1 / "AUDCAD_M15.csv.gz").read_bytes(), (d2 / "AUDCAD_M15.csv.gz").read_bytes()
    assert r1[:2] == b"\x1f\x8b" and r1 == r2
    assert r1[4:8] == b"\x00\x00\x00\x00", "mtime phai bang 0"
    assert not (r1[3] & 0x08), "khong duoc nhung ten tep goc (FNAME)"


# ------------------------------------------------------------------ doc_het
def test_doc_het_ghep_cac_cua_so_bo_trung_va_cat():
    d, sl = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    df = _m1("2018-06-28 00:00", "2018-07-12 12:00")
    X.ghi(df, "AUDCAD", "M1", d, sl, tu="2018-07-01", den="2018-07-07")
    X.ghi(df, "AUDCAD", "M1", d, sl, tu="2018-07-06", den="2018-07-10")                 # chong 2 ngay (6-7/7) voi cua so truoc
    X.ghi(df, "AUDCAD", "M15", d, sl, tu="2018-07-01", den="2018-07-02")                # khung khac: khong duoc lan vao
    X.ghi(df, "EURCAD", "M1", d, sl, tu="2018-07-01", den="2018-07-02")                 # cap khac: khong duoc lan vao
    r = X.doc_het("AUDCAD", "M1", d)
    assert r.index.is_monotonic_increasing and r.index.is_unique
    assert str(r.index[0]) == "2018-07-01 00:00:00" and str(r.index[-1]) == "2018-07-10 23:59:00"
    assert len(r) == 10 * 1440                                  # 1..10/7: hai ngay chong chi tinh MOT lan
    c = X.doc_het("AUDCAD", "M1", d, tu="2018-07-06", den="2018-07-07")
    assert str(c.index[0]) == "2018-07-06 00:00:00" and str(c.index[-1]) == "2018-07-07 23:59:00" and len(c) == 2 * 1440
    # khung M1 khong nuot tep M15 (glob `AUDCAD_M1*` khop ca `AUDCAD_M15_...`): M15 chi co 2 ngay
    assert len(X.doc_het("AUDCAD", "M15", d)) == 2 * 1440


def test_doc_het_bo_qua_tep_la_va_khung_khac_ngoai_khoang():
    """Tep la (`AUDCAD_M1_ghi_chu`, `AUDCAD_M1x`) khop glob `AUDCAD_M1*` nhung KHONG phai tep xuat -> khong duoc lan vao; M15 khong lan vao M1
    (dung khoang thoi gian khac M1 de neu lan vao thi so bar doi, khong bi dedup che)."""
    d, sl = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    X.ghi(_m1("2018-07-01 00:00", "2018-07-02 23:59"), "AUDCAD", "M1", d, sl, tu="2018-07-01", den="2018-07-02")
    X.ghi(_m1("2018-08-01 00:00", "2018-08-02 23:59"), "AUDCAD", "M15", d, sl, tu="2018-08-01", den="2018-08-02")     # khoang KHAC, khung khac
    for la in ("AUDCAD_M1_ghi_chu.csv.gz", "AUDCAD_M1x.csv.gz", "AUDCAD_M1_20180901.csv.gz", "AUDCAD_M1_20180901_20180902.csv.gz.bak"):
        X._ghi_gz(d / la, "time,open,high,low,close\n2018-09-01 00:00:00,9,9,9,9\n")
    r = X.doc_het("AUDCAD", "M1", d)
    assert len(r) == 2 * 1440 and str(r.index[-1]) == "2018-07-02 23:59:00"
    assert len(X.doc_het("AUDCAD", "M15", d)) == 2 * 1440


def test_doc_het_khi_hai_cua_so_chong_nhau_thi_giu_ban_cua_so_sau():
    d, sl = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    a = _m1("2018-07-01 00:00", "2018-07-10 23:59")
    b = a.copy()
    b[["open", "high", "low", "close"]] = b[["open", "high", "low", "close"]] + 0.5                 # cung thoi diem, GIA KHAC
    X.ghi(a, "AUDCAD", "M1", d, sl, tu="2018-07-01", den="2018-07-07")
    X.ghi(b, "AUDCAD", "M1", d, sl, tu="2018-07-06", den="2018-07-10")                              # ten sap SAU -> la ban moi
    r = X.doc_het("AUDCAD", "M1", d)
    t = pd.Timestamp("2018-07-06 12:00")
    assert abs(r.loc[t, "close"] - b.loc[t, "close"]) < 1e-5 and abs(r.loc[t, "close"] - a.loc[t, "close"]) > 0.4
    t0 = pd.Timestamp("2018-07-02 12:00")
    assert abs(r.loc[t0, "close"] - a.loc[t0, "close"]) < 1e-5                                     # ngoai khoang chong: giu ban cua a


def test_doc_het_khong_co_tep_thi_bao_loi_ro():
    with pytest.raises(FileNotFoundError):
        X.doc_het("AUDCAD", "M1", Path(tempfile.mkdtemp()))


# ------------------------------------------------------------------ noi ghi mac dinh = hop thu
def test_noi_ghi_mac_dinh_la_hop_thu_cua_bo_chay(monkeypatch, tmp_path):
    from qwen import cau_git as CG
    monkeypatch.setattr(CG, "MAILBOX", tmp_path / "hop_thu_p7")
    assert X.thu_muc_mac_dinh() == tmp_path / "hop_thu_p7" / "du_lieu_gia"
    # `ghi` khong truyen thu_muc -> vao dung do
    m = X.ghi(_df(), "AUDCAD", "M15", None, tmp_path / "sl")
    assert (tmp_path / "hop_thu_p7" / "du_lieu_gia" / m["tep"]).exists()


def test_khong_co_hop_thu_rieng_thi_la_lab(monkeypatch):
    from qwen import cau_git as CG
    monkeypatch.setattr(CG, "MAILBOX", CG.GOC)               # che do in-place
    assert X.thu_muc_mac_dinh() == X.MAC_DINH


def test_khong_doc_duoc_cau_noi_thi_lui_ve_lab(monkeypatch):
    import qwen
    monkeypatch.setitem(sys.modules, "qwen.cau_git", None)    # `from qwen import cau_git` -> ImportError
    monkeypatch.delattr(qwen, "cau_git", raising=False)
    assert X.thu_muc_mac_dinh() == X.MAC_DINH


def test_duong_xuat_that_den_dung_noi_runner_git_add(monkeypatch, tmp_path):
    """Chuoi that: mac dinh ghi vao `<hop thu>/du_lieu_gia` VA thu muc do nam trong `DUOC_DAY` -> `git add` co nuot duoc."""
    from qwen import cau_git as CG
    assert "du_lieu_gia" in CG.DUOC_DAY
    monkeypatch.setattr(CG, "MAILBOX", tmp_path / "hop")
    from nhan import du_lieu
    monkeypatch.setattr(du_lieu, "nap", lambda ma, khung, **kw: _m1("2018-07-01 00:00", "2018-07-03 23:59"))
    monkeypatch.setattr(X, "GOC", tmp_path / "lab")           # `../sao_luu_gia` rot vao tmp, khong dung vao may that
    X.chay(["AUDCAD"], "M1", None, "2018-07-01", "2018-07-02")
    assert (tmp_path / "hop" / "du_lieu_gia" / "AUDCAD_M1_20180701_20180702.csv.gz").exists()
    assert (tmp_path / "hop" / "du_lieu_gia" / "MANIFEST.json").exists()


# ------------------------------------------------------------------ chay() va CLI
@pytest.fixture
def lo_gia(monkeypatch, tmp_path):
    """`du_lieu.nap` gia: tra bar M1 lien tuc, KHONG nhan tu/den (ham that so sanh sai khi index co mui gio)."""
    from nhan import du_lieu
    goi = []

    def nap(ma, khung, **kw):
        goi.append((ma, khung, kw))
        return _m1("2018-06-30 00:00", "2018-07-05 23:59", tz="Europe/Athens" if ma == "TZ" else None)
    monkeypatch.setattr(du_lieu, "nap", nap)
    monkeypatch.setattr(X, "GOC", tmp_path / "lab")
    return goi, tmp_path / "ra"


def test_chay_ghi_tung_cap_va_gop_manifest(lo_gia):
    goi, ra = lo_gia
    X.chay(["AUDCAD", "EURCAD"], "M1", ra, "2018-07-01", "2018-07-03")
    X.chay(["AUDCAD"], "M15", ra, "2018")                      # cach cu: khong cua so
    X.chay(["NZDCAD"], "M1", ra, "2018-07-01", "2018-07-03")
    mf = json.loads((ra / "MANIFEST.json").read_text("utf-8"))
    assert sorted(mf) == ["AUDCAD_M15", "AUDCAD_M1_20180701_20180703", "EURCAD_M1_20180701_20180703", "NZDCAD_M1_20180701_20180703"]
    assert mf["AUDCAD_M1_20180701_20180703"]["so_bar"] == 3 * 1440
    assert mf["AUDCAD_M15"]["tep"] == "AUDCAD_M15.csv.gz"
    assert all("tu" not in kw and "den" not in kw for _, _, kw in goi)       # cat o `ghi`, khong qua `nap`
    assert not list(ra.glob("*.tam"))


def test_chay_xu_ly_index_co_mui_gio(lo_gia):
    _, ra = lo_gia
    X.chay(["TZ"], "M1", ra, "2018-07-01", "2018-07-01")
    r = X.doc("TZ", "M1", ra, "2018-07-01", "2018-07-01")
    assert len(r) == 1440 and str(r.index[0]) == "2018-07-01 00:00:00"


def test_chay_sai_ngay_thi_dung_truoc_khi_nap_bat_ky_ma_nao(lo_gia):
    goi, ra = lo_gia
    with pytest.raises(ValueError):
        X.chay(["AUDCAD"], "M1", ra, "2018-07-1", "2018-12-31")
    assert goi == [] and not ra.exists()


def test_chay_vuot_tran_moi_lenh(lo_gia, monkeypatch):
    _, ra = lo_gia
    monkeypatch.setattr(X, "TRAN_BYTE_MOI_LENH", 5_000)
    with pytest.raises(ValueError, match="vuot tran"):
        X.chay(["AUDCAD", "EURCAD", "NZDCAD"], "M1", ra, "2018-07-01", "2018-07-03")
    # dung o cap dau vuot tran; tep da ghi van co dong khai (khong mo coi), cac cap sau KHONG duoc ghi
    assert sorted(json.loads((ra / "MANIFEST.json").read_text("utf-8"))) == ["AUDCAD_M1_20180701_20180703"]
    assert [p.name for p in ra.glob("*.csv.gz")] == ["AUDCAD_M1_20180701_20180703.csv.gz"]


def test_sao_luu_mac_dinh_nam_ngoai_lab_theo_ngay(monkeypatch, tmp_path):
    from datetime import date
    monkeypatch.setattr(X, "GOC", tmp_path / "lab")
    d = tmp_path / "ra"
    m = X.ghi(_df(), "AUDCAD", "M15", d)                     # khong truyen sao_luu
    bk = tmp_path / "sao_luu_gia" / date.today().isoformat() / m["tep"]
    assert bk.exists() and bk.read_bytes() == (d / m["tep"]).read_bytes()


def test_chay_ghi_lai_bar_da_sua_vao_manifest(lo_gia, monkeypatch):
    from nhan import du_lieu
    _, ra = lo_gia
    monkeypatch.setattr(du_lieu, "_DA_SUA", {("AUDCAD", "M1"): {"so_bar": 3, "ngay": pd.Timestamp("2018-07-02")}}, raising=False)
    X.chay(["AUDCAD", "EURCAD"], "M1", ra, "2018-07-01", "2018-07-02")
    mf = json.loads((ra / "MANIFEST.json").read_text("utf-8"))
    assert mf["AUDCAD_M1_20180701_20180702"]["da_sua_bar"] == {"so_bar": 3, "ngay": "2018-07-02 00:00:00"}
    assert "da_sua_bar" not in mf["EURCAD_M1_20180701_20180702"]


def test_tran_moi_lenh_la_tong_cong_don_khong_phai_tung_cap(lo_gia, monkeypatch):
    _, ra = lo_gia
    mot = X.ghi(_m1("2018-06-30 00:00", "2018-07-05 23:59"), "AUDCAD", "M1", ra.parent / "do", ra.parent / "sl", "2018-07-01", "2018-07-03")["byte"]
    monkeypatch.setattr(X, "TRAN_BYTE_MOI_LENH", int(mot * 1.5))      # tung cap < tran, hai cap > tran
    with pytest.raises(ValueError, match="vuot tran"):
        X.chay(["AUDCAD", "EURCAD", "NZDCAD"], "M1", ra, "2018-07-01", "2018-07-03")
    assert sorted(json.loads((ra / "MANIFEST.json").read_text("utf-8"))) == ["AUDCAD_M1_20180701_20180703", "EURCAD_M1_20180701_20180703"]
    assert not (ra / "NZDCAD_M1_20180701_20180703.csv.gz").exists()


def test_cli_doc_dung_co_va_doi_so(lo_gia):
    _, ra = lo_gia
    X.main_cli(["AUDCAD,EURCAD", "M1", "--thu-muc", str(ra), "--tu", "2018-07-01", "--den", "2018-07-02"])
    assert sorted(p.name for p in ra.glob("*.csv.gz")) == ["AUDCAD_M1_20180701_20180702.csv.gz", "EURCAD_M1_20180701_20180702.csv.gz"]
    X.main_cli(["--den", "2018-07-02", "--tu", "2018-07-02", "NZDCAD", "M5", "--thu-muc", str(ra)])   # co dung truoc doi so
    assert (ra / "NZDCAD_M5_20180702_20180702.csv.gz").exists()
    X.main_cli(["AUDCAD", "--thu-muc", str(ra), "--tu", "2018"])                                        # khung mac dinh M15, cach cu
    assert (ra / "AUDCAD_M15.csv.gz").exists()
