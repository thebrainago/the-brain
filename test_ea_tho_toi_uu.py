# -*- coding: utf-8 -*-
"""ea_tho_toi_uu: MT5 OPTIMIZE cho EA co file - luoi -> bang pass -> diem on dinh -> xac_nhan DUNG diem do.

Khong co MT5 o day: tester la `MayToiUu`, no DOC CHINH van ban `tep_set_tho` ma code ghi cho tester (cac dong `K=v||tu||buoc||den||Y`),
liet ke luoi, ghi bang SpreadsheetML (moi Row la mot pass) dung bo cuc `chay_tester_kho.doc_xml`. Cai kiem duoc o day la QUYET DINH cua
code (luoi, van ban .set, ky luat dem phep thu, chon diem on dinh, hong ha tang khong phai AM, chay lai khong chay luoi), khong phai
ket qua tester that - bang .xml that dau tien tu may nha phai them vao day (xem tai_lieu/DAO_SAU_10_HE.md muc 3).
"""
from __future__ import annotations

import re
import statistics
import tempfile
from itertools import product
from pathlib import Path

import pytest

from nhan import ea_tho as E
from nhan import ea_tho_toi_uu as TU
from nhan import nc_so_tay as ST
from test_ea_tho import CHI_NUT_BAM, MayGia, dem, ea_cl, moi_truong  # noqa: F401  (fixture duoc dung chung, khong viet lai)
from test_ea_tho_tham_so import _ex5

LUOI = {"InpFast": [8, 2, 16], "InpSlow": [20, 2, 28]}          # 5 x 5 = 25 to hop; mac dinh cua EA (12, 26) nam tren luoi


@pytest.fixture(autouse=True)
def thu_muc_chan_doan(tmp_path, monkeypatch):
    d = tmp_path / "chan_doan"
    monkeypatch.setattr(E, "THU_MUC_CHAN_DOAN", d)
    return d


# ============================================================ TESTER GIA
_CELL = '<Cell><Data ss:Type="%s">%s</Data></Cell>'


def xml_bang(hang: list[dict], cot: list[str] | None = None) -> str:
    """Bang Optimize dang SpreadsheetML cua MT5: Row dau la tieu de, moi Row sau la mot pass."""
    cot = cot or list(hang[0])
    dong = ['<Row>' + "".join(_CELL % ("String", c) for c in cot) + '</Row>']
    for h in hang:
        dong.append('<Row>' + "".join(_CELL % ("Number", h[c]) for c in cot) + '</Row>')
    return ('<?xml version="1.0"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" '
            'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="Tester Optimizator Results"><Table>'
            + "".join(dong) + '</Table></Worksheet></Workbook>')


def doc_luoi(van_ban: str) -> dict:
    """Cac dong `K=v||tu||buoc||den||Y` -> {K: [gia tri...]} (chinh la viec MT5 lam voi khoang optimize)."""
    ra = {}
    for dong in van_ban.splitlines():
        m = re.fullmatch(r"(\w+)=([^|]*)\|\|([^|]*)\|\|([^|]*)\|\|([^|]*)\|\|Y", dong.strip())
        if m:
            tu, buoc, den = float(m.group(3)), float(m.group(4)), float(m.group(5))
            ra[m.group(1)] = [round(tu + i * buoc, 10) for i in range(int((den - tu) / buoc + 1e-9) + 1)]
    return ra


def doc_nen(van_ban: str) -> dict:
    """Moi dong khong thuoc luoi -> {K: v} (gia tri nen)."""
    ra = {}
    for dong in van_ban.splitlines():
        k, _, v = dong.partition("=")
        if k and "||Y" not in dong:
            ra[k] = v.split("||")[0]
    return ra


class MayToiUu(MayGia):
    """Lenh `toi_uu` -> bang pass liet ke tu CHINH van ban .set da ghi; lenh khac (xac_nhan) -> bao cao tong hop nhu MayGia.

    `pass_ = f(gia_tri: dict) -> {lai, dd, lenh}` (dd = % so tien). `sua_bang(hang) -> hang` de lam hong bang cho tung test."""

    def __init__(self, tmp_path, pass_=None, sua_bang=None, ghi_bang=True, **kw):
        super().__init__(tmp_path, **kw)
        self.pass_ = pass_ or (lambda g: {"lai": 1000.0, "dd": 10.0, "lenh": 80})
        self.sua_bang, self.ghi_bang = sua_bang, ghi_bang
        self.set_da_ghi: list[str] = []

    def __call__(self, lenh, ea, cfg):
        if not lenh.get("toi_uu"):
            return super().__call__(lenh, ea, cfg)
        self.lenh.append(lenh)
        if not self.xong:
            return {"xong": False, "loi": "tester chet"}
        van = lenh["viec"]["tep_set_tho"]
        self.set_da_ghi.append(van)
        luoi = doc_luoi(van)
        khoa = sorted(luoi)
        hang = []
        for i, to_hop in enumerate(product(*(luoi[k] for k in khoa))):
            g = dict(zip(khoa, to_hop))
            kq = self.pass_(g)
            hang.append({"Pass": i, "Result": kq["lai"], "Profit": kq["lai"], "Expected Payoff": 1.0, "Profit Factor": 1.5,
                         "Recovery Factor": 1.0, "Sharpe Ratio": 0.5, "Custom": 0, "Equity DD %": kq["dd"], "Trades": kq["lenh"], **g})
        if self.sua_bang:
            hang = self.sua_bang(hang)
        f = self.tmp / ("op%d.xml" % len(self.lenh))
        if self.ghi_bang:
            f.write_text(xml_bang(hang) if hang else "<Workbook/>", encoding="utf-8")
        return {"xong": True, "bao_cao": str(f), "log": "", "giay": 30.0}

    @property
    def lan_toi_uu(self):
        return sum(1 for l in self.lenh if l.get("toi_uu"))


def dat_may(monkeypatch, tmp_path, **kw):
    t = MayToiUu(tmp_path, **kw)
    monkeypatch.setattr(E, "CHAY_TESTER", t)
    return t


def cao_nguyen(g):
    """Mat phang rong: moi to hop deu co lai; (12, 26) hoi cao hon mot chut."""
    t = 1000.0 + 20.0 * (g["InpFast"] - 8) - 10.0 * abs(g["InpSlow"] - 24)
    return {"lai": t, "dd": 15.0, "lenh": 90}


def dinh_nhon(g):
    """Mot to hop (16, 28) rat cao nhung ca xom cua no lo; mot vung phang vua phai nam o (10..14, 22..26)."""
    if (g["InpFast"], g["InpSlow"]) == (16, 28):
        return {"lai": 9000.0, "dd": 20.0, "lenh": 90}
    if g["InpFast"] >= 15 and g["InpSlow"] >= 27:
        return {"lai": -800.0, "dd": 30.0, "lenh": 90}        # xom cua dinh nhon: lo
    if 10 <= g["InpFast"] <= 14 and 22 <= g["InpSlow"] <= 26:
        return {"lai": 2500.0, "dd": 20.0, "lenh": 90}         # vung phang
    return {"lai": -300.0, "dd": 25.0, "lenh": 90}


# ============================================================ 1. LUOI
def test_chuan_luoi_day_du_gia_tri_va_den_la_gia_tri_cuoi_that_co():
    lu = TU.chuan_luoi({"InpSlow": [20, 2, 28], "InpFast": {"tu": 8, "buoc": 3, "den": 18}})
    assert list(lu) == ["InpFast", "InpSlow"], "thu tu on dinh theo ten"
    assert lu["InpFast"]["gia_tri"] == [8.0, 11.0, 14.0, 17.0]
    assert lu["InpFast"]["den"] == 17.0, "den 18 khong ton tai: khoang ghi xuong .set phai khop so to hop mong doi"
    assert TU.so_to_hop(lu) == 4 * 5


def test_chuan_luoi_so_thap_phan_khong_troi_tren_buoc_le():
    lu = TU.chuan_luoi({"InpStep": [0.3, 0.1, 0.6], "InpLots": [0.1, 0.1, 0.5]})
    assert lu["InpStep"]["gia_tri"] == [0.3, 0.4, 0.5, 0.6]
    assert lu["InpLots"]["gia_tri"] == [0.1, 0.2, 0.3, 0.4, 0.5]


@pytest.mark.parametrize("luoi,mau", [
    (None, "dict"), ({}, "dict"), ([], "dict"), ("InpFast", "dict"),
    ({"a b": [1, 1, 3]}, "ten input"), ({"x||y": [1, 1, 3]}, "ten input"), ({"1x": [1, 1, 3]}, "ten input"),
    ({"InpFast": [1, 0, 3]}, "buoc"), ({"InpFast": [1, -1, 3]}, "buoc"),
    ({"InpFast": [3, 1, 3]}, "den phai > tu"), ({"InpFast": [3, 1, 2]}, "den phai > tu"),
    ({"InpFast": [1, 5, 2]}, "1 gia tri"),
    ({"InpFast": [1, 1, 100]}, "toi da"),
    ({"InpFast": [True, 1, 3]}, "so huu han"), ({"InpFast": ["1", 1, 3]}, "so huu han"),
    ({"InpFast": [1, 1, float("nan")]}, "so huu han"), ({"InpFast": [1, 1, float("inf")]}, "so huu han"),
    ({"InpFast": [1, 1]}, r"\[tu, buoc, den\]"), ({"InpFast": 5}, r"\[tu, buoc, den\]"),
    ({"A": [1, 1, 2], "B": [1, 1, 2], "C": [1, 1, 2], "D": [1, 1, 2], "E": [1, 1, 2]}, "quet mu"),
])
def test_chuan_luoi_tu_choi_dau_vao_sai(luoi, mau):
    with pytest.raises(ValueError, match=mau):
        TU.chuan_luoi(luoi)


def test_han_giay_tang_theo_so_to_hop_va_co_tran():
    assert TU.han_giay(25) == 1800 + 30 * 25
    assert TU.han_giay(400) == 1800 + 30 * 400 and TU.han_giay(10 ** 6) == TU.HAN_GIAY_TOI_DA == 14400


def test_van_ban_luoi_nen_tren_luoi_giu_nguyen_nen_ngoai_luoi_lay_tu_va_khoa_khac_viet_day_du():
    lu = TU.chuan_luoi({"InpFast": [8, 2, 16], "InpSlow": [20, 2, 28], })
    van = TU.van_ban_luoi({"InpFast": "12", "InpSlow": "21", "InpLots": "0.1", "Mode": "MODE_SMA", "InpTen": "abc"}, lu,
                          so_khoa={"InpFast", "InpSlow", "InpLots"})
    dong = van.splitlines()
    assert "InpFast=12||8||2||16||Y" in dong, "nen 12 nam tren luoi: giu lam gia tri khoi dau"
    assert "InpSlow=20||20||2||28||Y" in dong, "nen 21 lech luoi: MT5 phai bat dau o `tu`"
    assert "InpLots=0.1||0.1||0||0||N" in dong, "khoa so ngoai luoi: dang day du nhu script cu da chay that"
    assert "Mode=MODE_SMA" in dong and "InpTen=abc" in dong, "chuoi / enum: viet tran, khong lam hong gia tri"
    assert van.endswith("\n") and dong == sorted(dong, key=lambda s: s.split("=")[0])


def test_van_ban_luoi_khoa_luoi_khong_co_nen_bat_dau_o_tu():
    lu = TU.chuan_luoi({"InpStep": [30, 10, 70]})
    assert TU.van_ban_luoi({}, lu).splitlines() == ["InpStep=30||30||10||70||Y"]
    assert doc_luoi(TU.van_ban_luoi({}, lu)) == {"InpStep": [30.0, 40.0, 50.0, 60.0, 70.0]}


# ============================================================ 2. BANG PASS
def test_so_trong_o_bang_khong_doan_dau_phay_thap_phan():
    s = TU._so
    assert s("1234.5") == 1234.5 and s("-3.5e2") == -350.0 and s("1 234.50") == 1234.5 and s("1\xa0234.50") == 1234.5
    assert s("1,234.50") == 1234.5 and s("1,234,567") == 1234567.0
    assert s("12,5") is None, "dau phay thap phan khong duoc doan thanh 125"
    assert s("") is None and s("abc") is None and s("nan") is None and s("inf") is None and s("1_000") is None and s(None) is None


def test_s_so_thanh_chu_khong_co_dau_cham_0_va_khong_ky_hieu_khoa_hoc():
    assert TU._s(8.0) == "8" and TU._s(0.1) == "0.1" and TU._s(0.30000000000000004) == "0.3"
    assert TU._s(1e-7) == "0.0000001" and "e" not in TU._s(1e-9).lower() and TU._s(-2.5) == "-2.5"


def test_doc_bang_xml_va_thieu_cot(tmp_path):
    f = tmp_path / "b.xml"
    f.write_text(xml_bang([{"Pass": 0, "Profit": 5.0, "Equity DD %": 3.0, "Trades": 40, "InpFast": 8}]), encoding="utf-8")
    hang = TU.doc_bang(f)
    assert len(hang) == 1 and hang[0]["Profit"] == "5.0"
    assert TU.thieu_cot(hang, ["InpFast"]) == []
    assert TU.thieu_cot(hang, ["InpFast", "InpSlow"]) == ["InpSlow"]
    assert TU.thieu_cot([], ["InpFast"]) == ["Profit", "Equity DD %", "Trades", "InpFast"], "bang rong: thieu het"
    f2 = tmp_path / "c.xml"
    f2.write_text("<Workbook/>", encoding="utf-8")
    assert TU.doc_bang(f2) == []
    with pytest.raises(OSError):
        TU.doc_bang(tmp_path / "khong_co.xml")


def _hang(lai, dd, n, **inp):
    return {"Profit": str(lai), "Equity DD %": str(dd), "Trades": str(n), "Profit Factor": "1.4", **{k: str(v) for k, v in inp.items()}}


def test_chuan_pass_cagr_dat_va_cac_nguong():
    p = TU.chuan_pass(_hang(1000, 20, 50, InpFast=8), ["InpFast"], 10000.0, 365)
    assert p["gia_tri"] == {"InpFast": 8.0} and p["lai"] == 1000.0 and p["dd_pct"] == 20.0 and p["so_lenh"] == 50 and p["pf"] == 1.4
    assert p["cagr_pct"] == pytest.approx(((1 + 0.1) ** (365.25 / 365) - 1) * 100, abs=0.01) and p["dat"]
    # tung dieu kien cua cong: lai > 0, maxDD < 80, du lenh
    assert not TU.chuan_pass(_hang(-1, 20, 50, InpFast=8), ["InpFast"], 10000.0, 365)["dat"]
    assert not TU.chuan_pass(_hang(0, 20, 50, InpFast=8), ["InpFast"], 10000.0, 365)["dat"]
    assert TU.chuan_pass(_hang(10, 79.99, 50, InpFast=8), ["InpFast"], 10000.0, 365)["dat"]
    assert not TU.chuan_pass(_hang(10, 80, 50, InpFast=8), ["InpFast"], 10000.0, 365)["dat"]
    assert not TU.chuan_pass(_hang(10, 20, 9, InpFast=8), ["InpFast"], 10000.0, 365)["dat"], "duoi 10 lenh: chua du de tin"
    assert TU.chuan_pass(_hang(10, 20, 10, InpFast=8), ["InpFast"], 10000.0, 365)["dat"]
    # lo het von (>= 100%): CAGR = -100, khong vo (1 + x < 0 ** fraction)
    p = TU.chuan_pass(_hang(-12000, 99, 50, InpFast=8), ["InpFast"], 10000.0, 365)
    assert p["cagr_pct"] == -100.0 and not p["dat"]


def test_chuan_pass_o_hong_la_none_khong_phai_so_khong():
    khoa = ["InpFast"]
    assert TU.chuan_pass({**_hang(1, 1, 50, InpFast=8), "Profit": "n/a"}, khoa, 10000.0, 365) is None
    assert TU.chuan_pass({**_hang(1, 1, 50, InpFast=8), "Equity DD %": ""}, khoa, 10000.0, 365) is None
    assert TU.chuan_pass({**_hang(1, 1, 50, InpFast=8), "Trades": "12,5"}, khoa, 10000.0, 365) is None
    assert TU.chuan_pass({k: v for k, v in _hang(1, 1, 50).items()}, khoa, 10000.0, 365) is None, "thieu cot input"
    assert TU.chuan_pass(_hang(1, 1, 50, InpFast="x"), khoa, 10000.0, 365) is None


def _pass(lu, f):
    """Bang pass tu ham f(gia_tri) cho moi o cua luoi (qua chuan_pass nhu code that)."""
    khoa = sorted(lu)
    ra = []
    for to_hop in product(*(lu[k]["gia_tri"] for k in khoa)):
        g = dict(zip(khoa, to_hop))
        kq = f(g)
        ra.append(TU.chuan_pass(_hang(kq["lai"], kq["dd"], kq["lenh"], **g), khoa, 10000.0, 2922))
    return ra


# ============================================================ 3. HINH DANG VA DIEM ON DINH
def test_phan_tich_cao_nguyen_chon_o_trong_vung_khong_phai_mep():
    lu = TU.chuan_luoi(LUOI)
    pt = TU.phan_tich(_pass(lu, cao_nguyen), lu)
    assert pt["so_o"] == 25 and pt["so_dat"] == 25 and pt["hinh_dang"] == "cao_nguyen" and pt["ty_le_dat"] == 1.0
    assert pt["ngoai_luoi"] == 0 and pt["lap"] == 0 and not pt["phang"] and not pt["khong_lenh"]
    assert pt["chon"]["so_hang_xom"] >= 3 and pt["chon"]["ty_le_hang_xom_dat"] == 1.0
    assert pt["chon"]["on_dinh"] <= pt["dinh_tho"]["cagr_pct"], "on dinh khong bao gio cao hon dinh tho"
    assert len(pt["top"]) == TU.TOP and pt["top"][0]["gia_tri"] == pt["chon"]["gia_tri"]


def test_phan_tich_dinh_nhon_bi_keo_xuong_con_vung_phang_duoc_chon():
    lu = TU.chuan_luoi(LUOI)
    pt = TU.phan_tich(_pass(lu, dinh_nhon), lu)
    assert pt["dinh_tho"]["gia_tri"] == {"InpFast": 16.0, "InpSlow": 28.0}, "dinh tho la o nhon"
    assert pt["chon"]["gia_tri"]["InpFast"] in (10.0, 12.0, 14.0) and pt["chon"]["gia_tri"]["InpSlow"] in (22.0, 24.0, 26.0)
    assert pt["chon"]["on_dinh"] == pytest.approx(statistics.median(
        [pt["chon"]["cagr_pct"]] + [h["cagr_pct"] for h in _pass(lu, dinh_nhon)
                                    if h and abs(h["gia_tri"]["InpFast"] - pt["chon"]["gia_tri"]["InpFast"]) <= 2
                                    and abs(h["gia_tri"]["InpSlow"] - pt["chon"]["gia_tri"]["InpSlow"]) <= 2
                                    and h["gia_tri"] != pt["chon"]["gia_tri"]]), abs=0.01)
    assert pt["chenh_dinh_chon_pct"] > 0, "dinh tho cao hon diem duoc chon bao nhieu phai duoc ghi"
    assert pt["hinh_dang"] in ("cai_gai", "lo_cho")
    assert pt["top"][0]["gia_tri"] == pt["chon"]["gia_tri"]


def test_phan_tich_cai_gai_la_mot_o_dat_giua_bien_lo():
    lu = TU.chuan_luoi(LUOI)

    def f(g):
        return {"lai": 4000.0, "dd": 30.0, "lenh": 90} if (g["InpFast"], g["InpSlow"]) == (12, 24) else {"lai": -500.0, "dd": 30.0, "lenh": 90}
    pt = TU.phan_tich(_pass(lu, f), lu)
    assert pt["so_dat"] == 1 and pt["hinh_dang"] == "cai_gai" and pt["chon"]["gia_tri"] == {"InpFast": 12.0, "InpSlow": 24.0}
    assert pt["chon"]["ty_le_hang_xom_dat"] == 0.0 and pt["chon"]["so_hang_xom"] == 8


def test_phan_tich_khong_o_dat_thi_khong_chon():
    lu = TU.chuan_luoi(LUOI)
    pt = TU.phan_tich(_pass(lu, lambda g: {"lai": -100.0, "dd": 30.0, "lenh": 90}), lu)
    assert pt["hinh_dang"] == "khong_co_o_dat" and pt["chon"] is None and pt["dinh_tho"] is None and pt["top"] == []
    assert pt["chenh_dinh_chon_pct"] is None
    # lai duong nhung maxDD >= 80% cung la khong dat
    pt = TU.phan_tich(_pass(lu, lambda g: {"lai": 900.0, "dd": 85.0, "lenh": 90}), lu)
    assert pt["so_dat"] == 0 and pt["chon"] is None


def test_phan_tich_pass_ngoai_luoi_va_trung_lap_duoc_dem_khong_lam_hong_diem_chon():
    lu = TU.chuan_luoi({"InpFast": [8, 2, 16]})
    ps = _pass(lu, lambda g: {"lai": 500.0 + g["InpFast"], "dd": 10.0, "lenh": 90})
    ps.append(TU.chuan_pass(_hang(999, 10, 90, InpFast=9), ["InpFast"], 10000.0, 2922))        # lech buoc
    ps.append(TU.chuan_pass(_hang(999, 10, 90, InpFast=100), ["InpFast"], 10000.0, 2922))      # ngoai khoang
    ps.append(TU.chuan_pass(_hang(777, 10, 90, InpFast=12), ["InpFast"], 10000.0, 2922))       # lap o 12
    pt = TU.phan_tich(ps, lu)
    assert pt["so_o"] == 5 and pt["ngoai_luoi"] == 2 and pt["lap"] == 1
    assert pt["dinh_tho"]["lai"] == 516.0, "o 12 giu pass DAU TIEN, khong bi ban lap de len"


def test_phan_tich_dong_vao_gia_tri_luoi_sach_khong_so_le_tich_luy():
    lu = TU.chuan_luoi({"InpStep": [0.3, 0.1, 0.6]})
    ps = [TU.chuan_pass(_hang(100 * (i + 1), 10, 90, InpStep=x), ["InpStep"], 10000.0, 2922)
          for i, x in enumerate([0.3, 0.30000000001, 0.5, 0.6])]                          # 0,4 vang mat, 0,3 + 0,30000000001 trung
    pt = TU.phan_tich(ps, lu)
    assert pt["so_o"] == 3 and pt["lap"] == 1
    assert pt["chon"]["gia_tri"]["InpStep"] in (0.3, 0.5, 0.6) and all(
        x["gia_tri"]["InpStep"] in (0.3, 0.4, 0.5, 0.6) for x in pt["top"])


def test_phan_tich_bang_phang_va_khong_lenh_la_dau_hieu_hong_moi_truong():
    lu = TU.chuan_luoi(LUOI)
    assert TU.phan_tich(_pass(lu, lambda g: {"lai": 700.0, "dd": 12.0, "lenh": 55}), lu)["phang"]
    pt = TU.phan_tich(_pass(lu, lambda g: {"lai": 0.0, "dd": 0.0, "lenh": 0}), lu)
    assert pt["khong_lenh"] and pt["phang"]
    assert not TU.phan_tich(_pass(lu, cao_nguyen), lu)["phang"]


def test_bang_gon_cot_va_hang():
    lu = TU.chuan_luoi({"InpFast": [8, 2, 12]})
    ps = _pass(lu, lambda g: {"lai": 100.0 * g["InpFast"], "dd": 10.0, "lenh": 90})
    b = TU.bang_gon(ps, ["InpFast"])
    assert b["cot"] == ["InpFast", "lai", "dd_pct", "so_lenh", "dat"] and len(b["hang"]) == 3
    assert b["hang"][0] == [8.0, 800.0, 10.0, 90, 1]


# ============================================================ 4. CHAY: toi_uu() VOI TESTER GIA
def test_chay_toi_uu_xac_nhan_diem_on_dinh_dung_mot_lan_va_khong_cham_niem_phong(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path, pass_=dinh_nhon)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    assert r["trang_thai"] == "DAT", r.get("ly_do")
    assert t.lan == 2 and t.lan_toi_uu == 1, "MOT lan Optimize + MOT lan xac_nhan (khong phai 25 lan chay roi)"
    op, xn = t.lenh
    assert op["doan"] == "kham_pha" and xn["doan"] == "xac_nhan" and not any(l["doan"] == "niem_phong" for l in t.lenh)
    assert dem("niem_phong") == 0
    # luoi, gia tri nen va tham so cua lenh Optimize
    assert op["viec"]["toi_uu"] == 1 and op["viec"]["tieu_chi"] == 0 and op["viec"]["han_giay"] == TU.han_giay(25)
    assert doc_luoi(op["viec"]["tep_set_tho"]) == {"InpFast": [8.0, 10.0, 12.0, 14.0, 16.0], "InpSlow": [20.0, 22.0, 24.0, 26.0, 28.0]}
    assert "input" not in op["viec"] and op["tham_so"] == {}
    # diem chon nam trong vung phang, xac_nhan chay DUNG diem do
    chon = r["chon"]["gia_tri"]
    assert chon["InpFast"] in (10.0, 12.0, 14.0) and chon["InpSlow"] in (22.0, 24.0, 26.0)
    assert xn["tham_so"] == {k: v for k, v in chon.items()} and r["xac_nhan"]["gia_tri"] == chon
    assert r["dinh_tho"]["gia_tri"] == {"InpFast": 16.0, "InpSlow": 28.0} and r["chenh_dinh_chon_pct"] > 0
    assert r["so_to_hop"] == 25 and r["so_pass"] == 25 and r["luoi"] == {"InpFast": [8.0, 2.0, 16.0], "InpSlow": [20.0, 2.0, 28.0]}
    assert r["bang"]["cot"] == ["InpFast", "InpSlow", "lai", "dd_pct", "so_lenh", "dat"] and len(r["bang"]["hang"]) == 25
    assert any("TRUOC swap" in c for c in r["canh_bao"])


def test_chay_toi_uu_dem_moi_to_hop_la_mot_phep_thu_va_xac_nhan_khong_dem(ea_cl, tmp_path, monkeypatch):
    dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    gt = r["gt_id"]
    assert ST.dem_phep_thu(gt_id=gt) == 25 and ST.dem_phep_thu(gt_id=gt, doan="xac_nhan") == 1
    row = ST.mot("SELECT * FROM thi_nghiem WHERE id=?", r["tn_id"])
    assert (row["loai"], row["doan"], row["ma"], row["khung"], row["so_phep_thu"], row["gt_id"]) == \
           ("ea_tho_toi_uu", "kham_pha", "EURUSD", "H1", 25, gt)
    assert row["trang_thai"] == "DAT" and "OPTIMIZE" in row["tom_tat"]
    assert dem("thi_nghiem") == 2, "mot dong luoi + mot dong xac_nhan - khong ghi tung pass thanh tung dong"
    assert ST.mot("SELECT trang_thai FROM gia_thuyet WHERE id=?", gt)["trang_thai"] == "TRIEN_VONG"
    assert r["so_phep_thu_dong_gia_thuyet"] == 25
    # cung dong gia thuyet chay luoi khac: cong don, khong dat lai
    dat_may(monkeypatch, tmp_path, pass_=lambda g: {"lai": 500.0 + 10 * g["InpFast"] + g["InpStep"], "dd": 15.0, "lenh": 90})
    r2 = TU.toi_uu(ea_cl, "EURUSD", "H1", {"InpFast": [8, 2, 16], "InpStep": [30, 10, 70]}, gt_id=gt, xac_nhan=False)
    assert r2["so_phep_thu_dong_gia_thuyet"] == 25 + 25 and ST.dem_phep_thu(gt_id=gt) == 50


def test_chay_lai_cung_luoi_lay_tu_so_tay_khong_chay_tester_khong_dem_them(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    r1 = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    assert t.lan == 2
    r2 = TU.toi_uu(ea_cl, "eurusd", "h1", {"InpSlow": [20.0, 2.0, 28.0], "InpFast": {"tu": 8, "buoc": 2, "den": 16}})
    assert t.lan == 2, "luoi (khoa dao thu tu, ma/khung viet thuong, dang dict) cung van tay: khong chay lai gi"
    assert r2["tu_so_tay"] and r2["trang_thai"] == r1["trang_thai"] == "DAT" and r2["chon"] == r1["chon"]
    assert ST.dem_phep_thu(gt_id=r1["gt_id"]) == 25 and dem("thi_nghiem") == 2


def test_dung_giua_chung_giao_lai_chi_lam_tiep_buoc_xac_nhan(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    r1 = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, xac_nhan=False)
    assert r1["trang_thai"] == "DANG_CHO_XAC_NHAN" and r1["xac_nhan"] is None and t.lan == 1
    assert not any(l["doan"] == "xac_nhan" for l in t.lenh) and "chua xac_nhan" in r1["ly_do"]
    r2 = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    assert t.lan == 2 and t.lan_toi_uu == 1, "luoi khong chay lai, chi them mot lan xac_nhan"
    assert r2["trang_thai"] == "DAT" and r2["xac_nhan"]["gia_tri"] == r1["chon"]["gia_tri"] and r2["tu_so_tay"]
    r3 = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    assert t.lan == 2 and r3["trang_thai"] == "DAT", "xac_nhan cung chay y het thi lay tu so tay"
    assert ST.dem_phep_thu(gt_id=r1["gt_id"]) == 25


def test_khong_o_nao_dat_la_AM_ghi_so_tay_va_khong_xac_nhan(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path, pass_=lambda g: {"lai": -400.0 - 10 * g["InpFast"] - g["InpSlow"], "dd": 30.0, "lenh": 90})
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    assert r["trang_thai"] == "AM" and r["chon"] is None and r["xac_nhan"] is None and t.lan == 1
    assert ST.mot("SELECT trang_thai FROM thi_nghiem WHERE id=?", r["tn_id"])["trang_thai"] == "AM"
    assert ST.dem_phep_thu(gt_id=r["gt_id"]) == 25, "25 to hop da NHIN la 25 phep thu du khong cai nao dat"
    assert TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)["trang_thai"] == "AM" and t.lan == 1, "AM cung chay lai y het thi lay tu so tay"


def test_cai_gai_van_duoc_xac_nhan_nhung_canh_bao_ro(ea_cl, tmp_path, monkeypatch):
    def f(g):
        return {"lai": 4000.0, "dd": 30.0, "lenh": 90} if (g["InpFast"], g["InpSlow"]) == (12, 24) else {"lai": -500.0, "dd": 30.0, "lenh": 90}
    t = dat_may(monkeypatch, tmp_path, pass_=f)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    assert r["tong_quan"]["hinh_dang"] == "cai_gai" and r["tong_quan"]["so_dat"] == 1
    assert r["xac_nhan"]["gia_tri"] == {"InpFast": 12.0, "InpSlow": 24.0} and t.lan == 2, "van xac nhan (cong chi la nhan canh bao)"
    assert any("CAI GAI" in c for c in r["canh_bao"]) and any("it hon mot nua" in c for c in r["canh_bao"])


def test_xac_nhan_am_thi_ket_qua_cuoi_la_AM_du_luoi_dep(ea_cl, tmp_path, monkeypatch):
    """Luoi dep tren kham_pha nhung xac_nhan lo: dung la dieu can bat (chon dinh tren du lieu da nhin)."""
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen,
                kq=lambda lenh: {"lai": -800.0, "tho": 400.0, "lo": -1200.0, "lenh": 60} if lenh["doan"] == "xac_nhan" else {})
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    assert r["trang_thai"] == "AM" and r["xac_nhan"]["trang_thai"] == "AM" and t.lan == 2
    assert ST.mot("SELECT trang_thai FROM gia_thuyet WHERE id=?", r["gt_id"])["trang_thai"] == "DANG_THU"


# ---------------------------------------------------------------- hong ha tang khong phai AM
def _kiem_khong_ghi_gi(r, ly=None):
    assert r["trang_thai"] == "CHUA_DO_DUOC", r
    if ly:
        assert ly in r["ly_do"], r["ly_do"]
    assert dem("thi_nghiem") == 0 and dem("gia_thuyet") == 0, "hong ha tang: khong ghi so tay, khong tao gia thuyet"


def test_tester_chet_khong_phai_AM_va_khong_ghi_so_tay(ea_cl, tmp_path, monkeypatch):
    dat_may(monkeypatch, tmp_path, xong=False)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    _kiem_khong_ghi_gi(r, "tester chet")
    assert r["ha_tang"]


def test_tester_bao_xong_nhung_khong_co_file_bang_pass_la_ha_tang(ea_cl, tmp_path, monkeypatch, thu_muc_chan_doan):
    dat_may(monkeypatch, tmp_path, ghi_bang=False)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    _kiem_khong_ghi_gi(r, "khong doc duoc bang pass")
    assert "bang goc giu o" not in r["ly_do"] and not list(thu_muc_chan_doan.glob("*")), "khong co gi de giu"


def test_bang_rong_va_bang_thieu_cot_giu_ban_goc_de_doc_lai(ea_cl, tmp_path, monkeypatch, thu_muc_chan_doan):
    dat_may(monkeypatch, tmp_path, sua_bang=lambda h: [])
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    _kiem_khong_ghi_gi(r, "bang rong")
    assert "reports/chan_doan_tester/" in r["ly_do"] and list(thu_muc_chan_doan.glob("toi_uu_*.xml"))
    # cot input mang ten khac ten bien (vd nhan hien thi) -> noi ro cot nao thieu
    dat_may(monkeypatch, tmp_path, sua_bang=lambda h: [{("Fast period" if k == "InpFast" else k): v for k, v in x.items()} for x in h])
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    _kiem_khong_ghi_gi(r, "thieu cot InpFast")
    assert "Fast period" in r["ly_do"], "liet ke cot CO de nguoi doc thay ten that"


def test_chi_mot_pass_nghia_la_mt5_chay_mot_lan_khong_doc_khoang(ea_cl, tmp_path, monkeypatch):
    dat_may(monkeypatch, tmp_path, sua_bang=lambda h: h[:1])
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    _kiem_khong_ghi_gi(r, "1/25 pass")
    assert "MOT lan" in r["ly_do"]


def test_doc_duoc_duoi_90_phan_tram_pass_la_hong_con_du_90_thi_chap_nhan(ea_cl, tmp_path, monkeypatch):
    dat_may(monkeypatch, tmp_path, pass_=cao_nguyen, sua_bang=lambda h: h[:22])               # 22/25 = 88%
    _kiem_khong_ghi_gi(TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI), "22/25")
    dat_may(monkeypatch, tmp_path, pass_=cao_nguyen, sua_bang=lambda h: h[:23])               # 23/25 = 92%
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, xac_nhan=False)
    assert r["so_pass"] == 23 and r["trang_thai"] == "DANG_CHO_XAC_NHAN"


def test_o_so_hong_khong_bi_dem_la_pass_dat(ea_cl, tmp_path, monkeypatch):
    def hong(h):
        h[0]["Profit"] = "n/a"
        h[1]["Trades"] = "12,5"
        return h
    dat_may(monkeypatch, tmp_path, pass_=cao_nguyen, sua_bang=hong)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, xac_nhan=False)
    assert r["so_pass"] == 23 and r["tong_quan"]["so_o"] == 23, "2 pass hong bi bo, khong thanh 0"


def test_tat_ca_pass_deu_khong_lenh_la_hong_moi_truong_khong_phai_chien_luoc_te(ea_cl, tmp_path, monkeypatch):
    dat_may(monkeypatch, tmp_path, pass_=lambda g: {"lai": 0.0, "dd": 0.0, "lenh": 0})
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    _kiem_khong_ghi_gi(r, "TAT CA 25 pass deu 0 lenh")


def test_input_khong_tac_dong_len_ea_moi_pass_y_het_la_ha_tang(ea_cl, tmp_path, monkeypatch):
    dat_may(monkeypatch, tmp_path, pass_=lambda g: {"lai": 850.0, "dd": 12.0, "lenh": 77})
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    _kiem_khong_ghi_gi(r, "CUNG lai va so lenh")


def test_gt_id_khong_co_trong_so_tay_bi_chan_truoc_tester(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    for gt in (999, "abc"):
        r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, gt_id=gt)
        assert r["trang_thai"] == "CHUA_DO_DUOC" and "khong co gia thuyet" in r["ly_do"], r
    assert t.lan == 0 and dem("thi_nghiem") == 0 and dem("gia_thuyet") == 0


def test_may_khong_co_mt5_la_ha_tang_chu_khong_phai_am(ea_cl):
    """Khong cai tester gia (E.CHAY_TESTER = None): tren Linux `_chay_that` tra loi ro rang, khong nem, khong ghi so tay."""
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI)
    _kiem_khong_ghi_gi(r, "tester khong ra bang pass")
    assert r["ha_tang"]


def test_loi_nhap_lieu_khong_goi_tester(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path)
    for kw, mau in [
        (dict(luoi={}), "dict"),
        (dict(luoi={"InpFast": [8, 2, 10]}), "can 4..400"),                                         # 2 to hop < 4
        (dict(luoi={"InpFast": [1, 1, 59], "InpSlow": [1, 1, 8]}), "can 4..400"),                    # 59*8 = 472 > 400
        (dict(luoi={"KhongPhaiInput": [1, 1, 5]}), "KHONG phai input cua EA"),
        (dict(luoi={"InpFast": [1.5, 1, 5.5]}), "nguyen"),                                          # input int nhan so le
        (dict(luoi={"InpFast": [8, 2, 16]}, tham_so={"InpFast": 9}), "vua trong tham_so vua trong luoi"),
        (dict(luoi={"InpFast": [8, 2, 16], "InpSlow": [20, 2, 28]}, tham_so={"InpMagic": 1.5}), "nguyen"),
        (dict(luoi=LUOI, khung="H9"), "khung 'H9'"),
    ]:
        args = dict(ea=ea_cl, ma="EURUSD", khung="H1") | kw
        r = TU.toi_uu(**args)
        assert r["trang_thai"] == "CHUA_DO_DUOC" and re.search(mau, r["ly_do"]), (kw, r)
    assert t.lan == 0 and dem("thi_nghiem") == 0 and dem("gia_thuyet") == 0
    r = TU.toi_uu("/khong/co/file.mq5", "EURUSD", "H1", LUOI)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and t.lan == 0


def test_ea_khong_phai_chien_luoc_va_ma_khong_co_doan_dong_bang_bi_chan_truoc_tester(tmp_path, monkeypatch, ea_cl):
    t = dat_may(monkeypatch, tmp_path)
    nut = tmp_path / "Nut.mq5"
    nut.write_text(CHI_NUT_BAM, encoding="utf-8")
    r = TU.toi_uu(str(nut), "EURUSD", "H1", LUOI)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "khong phai chien luoc" in r["ly_do"]
    r = TU.toi_uu(ea_cl, "GBPJPY", "H1", LUOI)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r.get("ha_tang") and t.lan == 0


def test_tham_so_nen_di_vao_van_ban_set_va_xuong_xac_nhan(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", {"InpFast": [8, 2, 16], "InpSlow": [20, 2, 28]}, tham_so={"InpLots": 0.2, "InpStep": 40})
    assert r["trang_thai"] == "DAT"
    assert doc_nen(t.set_da_ghi[0]) == {"InpLots": "0.2", "InpStep": "40"}
    dong = t.set_da_ghi[0].splitlines()
    assert "InpLots=0.2||0.2||0||0||N" in dong and "InpStep=40||40||0||0||N" in dong
    xn = t.lenh[-1]
    assert xn["doan"] == "xac_nhan" and xn["tham_so"]["InpLots"] == 0.2 and xn["tham_so"]["InpStep"] == 40.0
    assert set(xn["tham_so"]) == {"InpLots", "InpStep", "InpFast", "InpSlow"}


def test_tham_so_nen_sai_ten_bi_tu_choi_truoc_khi_ton_gio_tester(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, tham_so={"InpLotz": 0.2})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "InpLotz" in r["ly_do"] and "InpLots" in r["ly_do"] and t.lan == 0


# ---------------------------------------------------------------- bo_set cua tac gia (EA nhi phan hoac co ma)
def _set(tmp_path, ten="Tac_Gia", **khoa):
    f = tmp_path / (ten + ".set")
    f.write_text("; saved by author\n" + "".join("%s=%s\n" % (k, v) for k, v in khoa.items()), encoding="utf-8")
    return str(f)


def test_bo_set_lam_gia_tri_nen_va_xac_nhan_chay_set_da_doi_dung_input_da_chon(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    tam = tmp_path / "tam"
    tam.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(tam))                      # .set tam nam duoi tmp_path de kiem duoc la da xoa
    da_doc: list[str] = []
    doc_set_goc = E.doc_set

    def doc_set_ghi_lai(duong):
        da_doc.append(str(duong))
        return doc_set_goc(duong)
    monkeypatch.setattr(E, "doc_set", doc_set_ghi_lai)
    bs = _set(tmp_path, InpFast=12, InpSlow=26, InpLots="0.1", InpMagic=777)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, bo_set=bs)
    assert r["trang_thai"] == "DAT" and r["bo_set"]["ten"] == "Tac_Gia"
    assert "InpFast=12||8||2||16||Y" in t.set_da_ghi[0].splitlines() and "InpSlow=26||20||2||28||Y" in t.set_da_ghi[0].splitlines()
    assert "InpLots=0.1||0.1||0||0||N" in t.set_da_ghi[0].splitlines() and "InpMagic=777||777||0||0||N" in t.set_da_ghi[0].splitlines()
    xn = t.lenh[-1]
    assert xn["doan"] == "xac_nhan" and xn["bo_set"]["so_khoa"] == 4 and xn["tham_so"].get("@bo_set")
    van = xn["bo_set"]["van_ban"].splitlines()
    chon = r["chon"]["gia_tri"]
    assert "InpFast=%d" % chon["InpFast"] in van and "InpSlow=%d" % chon["InpSlow"] in van and "InpLots=0.1" in van and "InpMagic=777" in van
    assert not [l for l in van if "||" in l], ".set xac nhan khong con khoang optimize"
    tam_set = [x for x in da_doc if x.endswith("_toi_uu.set")]
    assert len(tam_set) == 1 and Path(tam_set[0]).parent.parent == tam, "xac nhan doc dung .set tam do code ghi"
    assert not Path(tam_set[0]).exists() and not any(tam.iterdir()), ".set tam (cua nguoi la) phai bi xoa, ke ca thu muc tam"


def test_bo_set_va_tham_so_loai_tru_nhau_va_set_hong_bi_chan_truoc_tester(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path)
    bs = _set(tmp_path, InpFast=12, InpSlow=26)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, bo_set=bs, tham_so={"InpLots": 0.2})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "loai tru" in r["ly_do"]
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, bo_set=str(tmp_path / "khong_co.set"))
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "khong doc duoc .set" in r["ly_do"]
    assert t.lan == 0 and dem("thi_nghiem") == 0 and dem("gia_thuyet") == 0


def test_ea_co_ma_nguon_set_thieu_input_cua_ea_thi_cot_do_bat_dau_o_tu(ea_cl, tmp_path, monkeypatch):
    """InpSlow la input khai trong ma EA nhung .set cua tac gia khong co: khong chan, MT5 bat dau o `tu` cua luoi."""
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    r = TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, bo_set=_set(tmp_path, "Thieu", InpFast=12), xac_nhan=False)
    assert r["trang_thai"] == "DANG_CHO_XAC_NHAN", r.get("ly_do")
    dong = t.set_da_ghi[0].splitlines()
    assert "InpFast=12||8||2||16||Y" in dong and "InpSlow=20||20||2||28||Y" in dong


def test_ea_nhi_phan_can_bo_set_va_khoa_luoi_phai_co_trong_set(tmp_path, monkeypatch):
    ex5 = _ex5(tmp_path, "Hop_Den.ex5")
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    r = TU.toi_uu(ex5, "EURUSD", "H1", LUOI)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "nhi phan" in r["ly_do"] and "bo_set" in r["ly_do"]
    r = TU.toi_uu(ex5, "EURUSD", "H1", LUOI, bo_set=_set(tmp_path, InpFast=12))                      # thieu InpSlow trong .set
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "InpSlow" in r["ly_do"]
    assert t.lan == 0 and dem("thi_nghiem") == 0 and dem("gia_thuyet") == 0


def test_ea_nhi_phan_chay_nguyen_set_cua_tac_gia_chi_doi_khoa_trong_luoi(tmp_path, monkeypatch):
    ex5 = _ex5(tmp_path, "Hop_Den.ex5")
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    bs = _set(tmp_path, InpFast=12, InpSlow=26, Comment="my bot", InpUseMM="true")
    r = TU.toi_uu(ex5, "EURUSD", "H1", LUOI, bo_set=bs)
    assert r["trang_thai"] == "DAT", r.get("ly_do")
    op = t.lenh[0]
    assert op["nhi_phan"]["sha"] and "Comment=my bot" in op["viec"]["tep_set_tho"], "chuoi / bool cua tac gia di nguyen, khong 'sua'"
    assert "InpUseMM=true" in op["viec"]["tep_set_tho"].splitlines()
    assert t.lenh[-1]["nhi_phan"]["sha"] == op["nhi_phan"]["sha"]


# ---------------------------------------------------------------- van tay phan biet cac luoi / nen / cua so
def test_van_tay_phan_biet_luoi_nen_va_bo_set_khac_nhau(ea_cl, tmp_path, monkeypatch):
    t = dat_may(monkeypatch, tmp_path, pass_=cao_nguyen)
    TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, xac_nhan=False)
    TU.toi_uu(ea_cl, "EURUSD", "H1", {"InpFast": [8, 2, 16], "InpSlow": [20, 2, 30]}, xac_nhan=False)               # luoi khac
    TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, tham_so={"InpLots": 0.2}, xac_nhan=False)                                # nen khac
    TU.toi_uu(ea_cl, "EURUSD", "H1", LUOI, bo_set=_set(tmp_path, InpFast=12, InpSlow=26), xac_nhan=False)           # bo_set
    TU.toi_uu(ea_cl, "XAUUSD", "H1", LUOI, xac_nhan=False)                                                          # ma khac
    assert t.lan_toi_uu == 5 and dem("thi_nghiem", "loai='ea_tho_toi_uu'") == 5


# ============================================================ 5. DANG KY CONG CU + CHANG CUA VONG LAP
def test_dang_ky_cong_cu_va_chang_cua_vong_lap():
    from nhan import nc_cong_cu as CC
    from nhan import vong_lap as VL
    ten = [c["ten"] for c in CC.CONG_CU]
    assert "ea_tho_toi_uu" in ten
    api = {t["name"]: t for t in CC.schema_api()}
    d = api["ea_tho_toi_uu"]
    assert len(d["description"]) > 200 and set(d["input_schema"]["required"]) == {"ea", "ma", "khung", "luoi"}
    assert VL.chang_cua("ea_tho_toi_uu", {}, "") == ("KIEM", "kham")


def test_cong_cu_goi_duoc_bang_nc_cong_cu_va_khong_tra_bang_pass_day_du(ea_cl, tmp_path, monkeypatch):
    from nhan import nc_cong_cu as CC
    dat_may(monkeypatch, tmp_path, pass_=dinh_nhon)
    r = CC.goi("ea_tho_toi_uu", {"ea": ea_cl, "ma": "EURUSD", "khung": "H1", "luoi": LUOI})
    assert "loi" not in r and r["trang_thai"] == "DAT" and r["so_to_hop"] == 25 and r["xac_nhan"]["gia_tri"] == r["chon"]["gia_tri"]
    assert "bang" not in r, "bang 25 dong nam o so tay (tn_id), khong lap lai trong moi cau tra loi cua cong cu"
    row = ST.mot("SELECT ket_qua FROM thi_nghiem WHERE id=?", r["tn_id"])
    assert '"bang"' in row["ket_qua"], "...nhung so tay GIU bang day du de so voi mo phong sau nay"
    r = CC.goi("ea_tho_toi_uu", {"ea": ea_cl, "ma": "EURUSD", "khung": "H1"})
    assert "thieu tham so bat buoc" in r["loi"]
    r = CC.goi("ea_tho_toi_uu", {"ea": ea_cl, "ma": "EURUSD", "khung": "H1", "luoi": {"InpFast": [1, 0, 5]}})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "buoc" in r["ly_do"], r
