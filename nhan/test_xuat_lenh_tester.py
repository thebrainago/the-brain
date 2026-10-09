import gzip
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import xuat_lenh_tester as XL

K1, K2, K3 = "fd1c5f89bbeaaaa8", "0123456789abcdef", "aaaaaaaaaaaaaaaa"


def _bang(n=12, dau="2018-07-02 00:15:00", treo_cuoi=False, co_swap=True):
    """Bang lenh dung dinh dang `hieu_chuan_luoi.bang_lenh_tester`: mo, dong, chieu, lot, gia_mo, gia_dong, lai, swap, ly."""
    mo = pd.date_range(dau, periods=n, freq="1h")
    r = np.random.default_rng(3)
    chieu = np.where(np.arange(n) % 2 == 0, 1, -1)
    g0 = 0.9 + np.cumsum(r.normal(0, 1e-3, n))
    g1 = g0 + chieu * 9e-4
    df = pd.DataFrame({"mo": mo, "dong": mo + pd.Timedelta(minutes=45), "chieu": chieu, "lot": 0.04,
                       "gia_mo": g0.round(5), "gia_dong": g1.round(5), "lai": (chieu * (g1 - g0) * 0.04 * 100_000).round(2),
                       "swap": 0.0, "ly": "tp"})
    if not co_swap:
        df = df.drop(columns=["swap"])
    if treo_cuoi and n:
        df.loc[df.index[-1], ["dong", "gia_dong"]] = [pd.NaT, np.nan]
    return df


def _viet(thu_muc: Path, khoa: str, df: pd.DataFrame) -> Path:
    """Ghi nhu `hieu_chuan_luoi._luu_bang_lenh`: pandas, gzip (byte KHONG co dinh)."""
    thu_muc.mkdir(parents=True, exist_ok=True)
    p = thu_muc / ("%s_lenh.csv.gz" % khoa)
    df.to_csv(p, index=False, compression="gzip")
    return p


@pytest.fixture
def nguon(tmp_path):
    n = tmp_path / "reports" / "hieu_chuan"
    _viet(n, K1, _bang(12))
    _viet(n, K2, _bang(8, "2019-03-04 00:00:00", co_swap=False))
    _viet(n, K3, _bang(0))
    return n


# ------------------------------------------------------------------ chuoi chinh
def test_khu_tron_xuat_het_ghi_so_khai_va_giu_nguyen_noi_dung(nguon, tmp_path):
    ra = tmp_path / "ra"
    kq = XL.chay(nguon, ra)
    assert sorted(kq["da_xuat"]) == sorted([K1, K2, K3]) and kq["bo_qua"] == {}
    assert sorted(p.name for p in ra.glob("*.csv.gz")) == sorted("%s_lenh.csv.gz" % k for k in (K1, K2, K3))
    for k in (K1, K2, K3):                                    # van ban CSV khong doi mot chu
        with gzip.open(nguon / ("%s_lenh.csv.gz" % k), "rt") as a, gzip.open(ra / ("%s_lenh.csv.gz" % k), "rt") as b:
            assert a.read() == b.read()
    mf = json.loads((ra / "MANIFEST.json").read_text("utf-8"))
    assert sorted(mf) == sorted([K1, K2, K3])
    m = mf[K1]
    assert m["so_lenh"] == 12 and m["tep"] == "%s_lenh.csv.gz" % K1 and m["byte"] == (ra / m["tep"]).stat().st_size
    assert m["mo_dau"] == "2018-07-02 00:15:00" and m["mo_cuoi"] == "2018-07-02 11:15:00"
    assert m["lai_tong"] == round(float(_bang(12)["lai"].sum()), 4) and m["swap_tong"] == 0.0
    assert len(m["sha256"]) == 16
    assert mf[K2]["so_lenh"] == 8 and mf[K2]["swap_tong"] == 0.0           # bang khong co cot swap van hop le
    assert kq["byte"] == sum(v["byte"] for v in mf.values())
    assert not list(ra.glob("*.tam"))


def test_bang_rong_la_hop_le_vi_tester_co_the_khong_vao_lenh(nguon, tmp_path):
    kq = XL.chay(nguon, tmp_path / "ra")
    m = kq["da_xuat"][K3]
    assert m["so_lenh"] == 0 and m["mo_dau"] is None and m["lai_tong"] == 0.0
    assert len(XL.doc(K3, tmp_path / "ra")) == 0


def test_lenh_con_treo_cuoi_ky_khong_bi_coi_la_hong(tmp_path):
    n = tmp_path / "n"
    _viet(n, K1, _bang(6, treo_cuoi=True))
    assert XL.chay(n, tmp_path / "ra")["da_xuat"][K1]["so_lenh"] == 6


def test_gzip_co_dinh_khong_mtime_khong_ten(nguon, tmp_path, monkeypatch):
    monkeypatch.setattr(time, "time", lambda: 1_700_000_000.0)
    XL.chay(nguon, tmp_path / "a")
    monkeypatch.setattr(time, "time", lambda: 1_800_000_000.0)
    XL.chay(nguon, tmp_path / "b")
    for k in (K1, K2):
        ten = "%s_lenh.csv.gz" % k
        x, y = (tmp_path / "a" / ten).read_bytes(), (tmp_path / "b" / ten).read_bytes()
        assert x == y and x[:2] == b"\x1f\x8b"
        assert x[4:8] == b"\x00\x00\x00\x00" and not (x[3] & 0x08)


def test_doc_lai_ra_thoi_gian(nguon, tmp_path):
    XL.chay(nguon, tmp_path / "ra")
    d = XL.doc(K1 + "ffff", tmp_path / "ra")                  # chi lay 16 ky tu dau cua khoa
    assert len(d) == 12 and str(d["mo"].dtype).startswith("datetime64") and str(d["dong"].dtype).startswith("datetime64")


# ------------------------------------------------------------------ file hong / la
def test_file_hong_thieu_cot_hay_thoi_gian_sai_bi_bo_qua_co_ly_do_con_lai_van_xuat(nguon, tmp_path):
    (nguon / "1111111111111111_lenh.csv.gz").write_bytes(b"day khong phai gzip")
    _viet(nguon, "2222222222222222", _bang(5).drop(columns=["gia_mo"]))
    x = _bang(5); x["mo"] = x["mo"].astype(str); x.loc[2, "mo"] = "khong phai ngay"
    _viet(nguon, "3333333333333333", x)
    y = _bang(5); y["lai"] = y["lai"].astype(object); y.loc[1, "lai"] = "abc"
    _viet(nguon, "4444444444444444", y)
    z = _bang(5); z["gia_dong"] = z["gia_dong"].astype(object); z.loc[3, "gia_dong"] = "xyz"
    _viet(nguon, "5555555555555555", z)
    (nguon / "6666666666666666_lenh.csv.gz").write_bytes(gzip.compress(b""))
    kq = XL.chay(nguon, tmp_path / "ra")
    assert sorted(kq["da_xuat"]) == sorted([K1, K2, K3])
    assert sorted(kq["bo_qua"]) == ["%s_lenh.csv.gz" % k for k in ("1111111111111111", "2222222222222222", "3333333333333333",
                                                                   "4444444444444444", "5555555555555555", "6666666666666666")]
    assert "gia_mo" in kq["bo_qua"]["2222222222222222_lenh.csv.gz"]                        # ly do noi ro thieu cot nao
    assert "mo" in kq["bo_qua"]["3333333333333333_lenh.csv.gz"]
    assert "lai" in kq["bo_qua"]["4444444444444444_lenh.csv.gz"]
    assert "gia_dong" in kq["bo_qua"]["5555555555555555_lenh.csv.gz"]
    assert not (tmp_path / "ra" / "1111111111111111_lenh.csv.gz").exists()
    assert sorted(json.loads((tmp_path / "ra" / "MANIFEST.json").read_text("utf-8"))) == sorted([K1, K2, K3])


@pytest.mark.parametrize("cot", ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "lai"])
def test_thieu_bat_ky_cot_bat_buoc_nao_cung_bi_bo_qua(tmp_path, cot):
    n = tmp_path / "n"
    _viet(n, K1, _bang(5))
    _viet(n, K2, _bang(5).drop(columns=[cot]))
    kq = XL.chay(n, tmp_path / "ra")
    assert list(kq["da_xuat"]) == [K1] and cot in kq["bo_qua"]["%s_lenh.csv.gz" % K2]


def test_van_ban_khong_phai_utf8_bi_bo_qua_khong_lam_chet_ca_lo(tmp_path):
    n = tmp_path / "n"
    _viet(n, K1, _bang(5))
    (n / ("%s_lenh.csv.gz" % K2)).write_bytes(gzip.compress(b"mo,dong,chieu\n\xff\xfe\x80,1,2\n"))
    kq = XL.chay(n, tmp_path / "ra")
    assert list(kq["da_xuat"]) == [K1] and "UnicodeDecodeError" in kq["bo_qua"]["%s_lenh.csv.gz" % K2]


def test_gzip_hong_giua_than_bi_bo_qua_khong_lam_chet_ca_lo(tmp_path):
    n = tmp_path / "n"
    _viet(n, K1, _bang(5))
    (n / ("%s_lenh.csv.gz" % K2)).write_bytes(b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff" + b"\xff" * 12)       # dau gzip dung, than deflate rac
    ct = gzip.compress(_bang(40).to_csv(index=False).encode())
    (n / ("%s_lenh.csv.gz" % K3)).write_bytes(ct[: len(ct) // 2])                                      # bi cat ngang
    kq = XL.chay(n, tmp_path / "ra")
    assert list(kq["da_xuat"]) == [K1] and sorted(kq["bo_qua"]) == ["%s_lenh.csv.gz" % K2, "%s_lenh.csv.gz" % K3]
    assert "error" in kq["bo_qua"]["%s_lenh.csv.gz" % K2].lower()


def test_swap_tong_va_sha_tinh_dung_tren_du_lieu_va_tep_ghi(tmp_path):
    import hashlib
    n = tmp_path / "n"
    b = _bang(6)
    b["swap"] = [-0.5, -0.25, 0.0, 1.5, np.nan, -2.0]                      # tester that ghi 0, nhung cot nay van phai cong dung
    _viet(n, K1, b)
    kq = XL.chay(n, tmp_path / "ra")
    m = kq["da_xuat"][K1]
    assert m["swap_tong"] == -1.25                                          # NaN tinh 0
    f = tmp_path / "ra" / m["tep"]
    assert m["sha256"] == hashlib.sha256(f.read_bytes()).hexdigest()[:16] and m["byte"] == f.stat().st_size


def test_ten_khong_dung_dinh_dang_khong_phai_bang_lenh(nguon, tmp_path):
    for ten in ("abc_lenh.csv.gz", "FD1C5F89BBEAAAA8_lenh.csv.gz", "fd1c5f89bbeaaaa_lenh.csv.gz",          # khoa sai do dai / chu hoa
                "fd1c5f89bbeaaaa81_lenh.csv.gz", "fd1c5f89bbeaaaa8_lenh.csv", "fd1c5f89bbeaaaa8_lenh.csv.gz.bak",
                "x_fd1c5f89bbeaaaa8_lenh.csv.gz", "swap_gom.json"):
        (nguon / ten).write_bytes(gzip.compress(b"mo,dong\n"))
    kq = XL.chay(nguon, tmp_path / "ra")
    assert sorted(kq["da_xuat"]) == sorted([K1, K2, K3]) and kq["bo_qua"] == {}


def test_khong_co_bang_nao_thi_bao_loi_ro_khong_thanh_cong_rong(tmp_path):
    with pytest.raises(FileNotFoundError, match="khong co bang lenh"):
        XL.chay(tmp_path / "khong_ton_tai", tmp_path / "ra")
    (tmp_path / "trong").mkdir()
    with pytest.raises(FileNotFoundError):
        XL.chay(tmp_path / "trong", tmp_path / "ra")
    assert not (tmp_path / "ra").exists()


def test_co_file_nhung_khong_file_nao_dung_thi_bao_loi_kem_ly_do(tmp_path):
    n = tmp_path / "n"
    n.mkdir()
    (n / ("%s_lenh.csv.gz" % K1)).write_bytes(b"rac")
    with pytest.raises(ValueError, match="khong file nao dung") as e:
        XL.chay(n, tmp_path / "ra")
    assert K1 in str(e.value)
    assert not (tmp_path / "ra").exists()


# ------------------------------------------------------------------ tran dung luong (repo PUBLIC)
def test_vuot_tran_moi_file_bo_qua_file_do_con_lai_van_xuat(tmp_path):
    n = tmp_path / "n"
    _viet(n, K1, _bang(400))
    _viet(n, K2, _bang(3))
    nho = XL.chay(n, tmp_path / "do")["da_xuat"][K2]["byte"]
    kq = XL.chay(n, tmp_path / "ra", tran_file=nho + 50)
    assert sorted(kq["da_xuat"]) == [K2] and "vuot tran" in kq["bo_qua"]["%s_lenh.csv.gz" % K1]
    assert [p.name for p in (tmp_path / "ra").glob("*.csv.gz")] == ["%s_lenh.csv.gz" % K2]


def test_vuot_tran_moi_lenh_thi_khong_ghi_gi(nguon, tmp_path):
    with pytest.raises(ValueError, match="vuot tran"):
        XL.chay(nguon, tmp_path / "ra", tran_lenh=300)
    assert not (tmp_path / "ra").exists()                     # tat ca hoac khong: chua tao ca thu muc
    xong = XL.chay(nguon, tmp_path / "ra2")["byte"]
    XL.chay(nguon, tmp_path / "ra3", tran_lenh=xong)          # dung bang tran thi qua
    with pytest.raises(ValueError, match="vuot tran"):
        XL.chay(nguon, tmp_path / "ra4", tran_lenh=xong - 1)
    assert not (tmp_path / "ra4").exists()


def test_tran_mac_dinh_rong_rai_cho_125_o_nhung_chan_file_lac_loai():
    assert XL.TRAN_BYTE_MOI_FILE <= 3_000_000 and XL.TRAN_BYTE_MOI_LENH <= 12_000_000          # repo PUBLIC: khong ai noi long tran lang le
    mot = len(XL._gz_co_dinh(_bang(500).to_csv(index=False)))
    assert 125 * mot < XL.TRAN_BYTE_MOI_LENH and mot < XL.TRAN_BYTE_MOI_FILE                    # 125 o x 500 lenh van lot


# ------------------------------------------------------------------ ghi an toan
def test_xuat_lai_cung_noi_dung_thi_khong_ghi_de_tep(nguon, tmp_path):
    ra = tmp_path / "ra"
    XL.chay(nguon, ra)
    cu = {p.name: p.stat().st_mtime_ns for p in ra.glob("*.csv.gz")}
    time.sleep(0.02)
    XL.chay(nguon, ra)
    assert {p.name: p.stat().st_mtime_ns for p in ra.glob("*.csv.gz")} == cu
    # noi dung doi (hieu chuan chay lai) -> ghi de
    _viet(nguon, K1, _bang(13))
    XL.chay(nguon, ra)
    assert XL.doc(K1, ra).shape[0] == 13
    assert json.loads((ra / "MANIFEST.json").read_text("utf-8"))[K1]["so_lenh"] == 13


def test_manifest_gop_va_giu_dong_cua_lan_xuat_truoc(nguon, tmp_path):
    ra = tmp_path / "ra"
    XL.chay(nguon, ra)
    n2 = tmp_path / "n2"
    _viet(n2, "bbbbbbbbbbbbbbbb", _bang(4))
    XL.chay(n2, ra)
    assert sorted(json.loads((ra / "MANIFEST.json").read_text("utf-8"))) == sorted([K1, K2, K3, "bbbbbbbbbbbbbbbb"])


def test_loi_giua_chung_khong_de_tep_tam(nguon, tmp_path, monkeypatch):
    ra = tmp_path / "ra"
    that = os.replace
    dem = {"n": 0}

    def hong(a, b):
        dem["n"] += 1
        if dem["n"] == 2:
            raise OSError("het cho")
        return that(a, b)
    monkeypatch.setattr(os, "replace", hong)
    with pytest.raises(OSError):
        XL.chay(nguon, ra)
    assert not list(ra.glob("*.tam"))                         # `.tam` se bi `git add` nham neu o lai (da them vao .gitignore, nhung khong de lai)


# ------------------------------------------------------------------ noi ghi + dong lenh
def test_noi_ghi_mac_dinh_la_mau_tester_trong_hop_thu(monkeypatch, tmp_path):
    from qwen import cau_git as CG
    monkeypatch.setattr(CG, "MAILBOX", tmp_path / "hop")
    assert XL.thu_muc_mac_dinh() == tmp_path / "hop" / "du_lieu_gia" / "mau_tester"
    assert "du_lieu_gia" in CG.DUOC_DAY                      # bo chay `git add` duong nay


def test_nguon_mac_dinh_la_reports_hieu_chuan_cua_lab():
    assert XL.THU_NGUON == XL.GOC / "reports" / "hieu_chuan"


def test_cli(nguon, tmp_path, capsys):
    ra = tmp_path / "ra"
    XL.main_cli(["--nguon", str(nguon), "--thu-muc", str(ra)])
    out = capsys.readouterr().out
    assert "xuat 3 bang lenh tester (20 lenh" in out and str(ra) in out
    (nguon / "1111111111111111_lenh.csv.gz").write_bytes(b"rac")
    XL.main_cli(["--thu-muc", str(ra), "--nguon", str(nguon)])
    out = capsys.readouterr().out
    assert "bo qua 1" in out and "1111111111111111_lenh.csv.gz" in out
    for hong in (["--la"], ["--nguon"], ["--thu-muc"], ["--nguon", str(nguon), "--them"]):
        with pytest.raises(SystemExit):
            XL.main_cli(hong)


def test_cli_khong_co_nguon_hay_dich_la_dung_noi_mac_dinh(monkeypatch, tmp_path, capsys):
    from qwen import cau_git as CG
    monkeypatch.setattr(CG, "MAILBOX", tmp_path / "hop")
    monkeypatch.setattr(XL, "THU_NGUON", tmp_path / "lab" / "reports" / "hieu_chuan")
    _viet(tmp_path / "lab" / "reports" / "hieu_chuan", K1, _bang(3))
    XL.main_cli([])
    assert (tmp_path / "hop" / "du_lieu_gia" / "mau_tester" / ("%s_lenh.csv.gz" % K1)).exists()
    assert "mau_tester" in capsys.readouterr().out


# ------------------------------------------------------------------ khop voi bo ghi THAT cua hieu_chuan_luoi
def test_doc_duoc_bang_do_chinh_hieu_chuan_luoi_ghi_ra(tmp_path, monkeypatch):
    """Dung `hieu_chuan_luoi.bang_lenh_tester` + `_luu_bang_lenh` (bo ghi that), roi xuat - tranh hai ben lech dinh dang."""
    from nhan import hieu_chuan_luoi as HC
    monkeypatch.setattr(HC, "THU_MUC", tmp_path / "lab" / "reports" / "hieu_chuan")
    n = 7
    mo = pd.date_range("2019-03-04 01:00", periods=n, freq="30min")
    g = pd.DataFrame({"mo": mo, "dong": mo + pd.Timedelta(minutes=20), "chieu": [1, -1, 1, -1, 1, -1, 1], "lot": 0.05,
                      "gia_mo": 0.9 + np.arange(n) * 1e-4, "gia_dong": 0.9 + np.arange(n) * 1e-4 + 5e-4,
                      "loi": np.arange(n) * 1.5 - 2.0, "hoa_hong": -0.4, "swap": 0.0,
                      "cm_ra": ["tp"] * 6 + ["end of test"], "ly_do_ra": ["tp"] * 6 + ["so"]})
    b = HC.bang_lenh_tester(g)
    khoa_dai = "%s%s" % (K1, "e" * 48)
    dd = HC._luu_bang_lenh(b, khoa_dai)
    assert dd and dd.endswith("%s_lenh.csv.gz" % K1)
    kq = XL.chay(tmp_path / "lab" / "reports" / "hieu_chuan", tmp_path / "ra")
    assert list(kq["da_xuat"]) == [K1] and kq["da_xuat"][K1]["so_lenh"] == n
    d = XL.doc(K1, tmp_path / "ra")
    assert list(d.columns) == ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "lai", "swap", "ly"]
    assert d["ly"].iloc[-1] == "het_gio" and abs(d["lai"].sum() - float(b["lai"].sum())) < 1e-6
