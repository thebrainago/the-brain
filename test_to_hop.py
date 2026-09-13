# -*- coding: utf-8 -*-
"""Kiem `nhan/to_hop.py` - pheu to hop da cap x da khung x da quan li x da thong so.

Module nay nguy hiem theo mot kieu rieng: no chay HANG TRAM NGHIN o roi in ra
mot bang xep hang. Neu phep TIA sai thi khong ai nhin thay - bang van dep, chi
la no da bo mat nua khong gian, hoac da dem hai lan cung mot tai san duoi hai
cai ten. Nen o day kiem PHEP TIA va PHEP GOP, khong kiem "chay duoc".

Va mot dieu nua phai kiem bang test chu khong bang thien chi: bang tong ket
PHAI mang canh bao thien lech chon loc. Chang 1 da chon top N theo chinh
`cagr_dd20` roi chang 2 mo rong dung nhung o do, nen con so "hon moc" o bang
chang 2 bi thoi len boi chinh phep chon. Ai doc ma khong biet dieu do se tuong
he vua tim ra hang chuc he thang moc.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import to_hop as TH  # noqa: E402


class PhepTiaPhaiDUNG(unittest.TestCase):
    def test_bo_ban_sao_nhung_GIU_mot_dai_dien(self):
        cap = {"A|B": {"r": 1.0, "trung": True},
               "B|C": {"r": 0.99, "trung": True}}
        import nhan.ho_so_tuong_quan as TQ
        that = TQ.doc
        TQ.doc = lambda khung="D1": {"cap": cap}
        try:
            giu, bo = TH.ma_khong_trung(["A", "B", "C", "D"], "D1")
        finally:
            TQ.doc = that
        self.assertIn("D", giu, "ma khong lien quan bi bo oan")
        self.assertEqual(len(set(bo) & set(giu)), 0, "vua bo vua giu mot ma")
        # ca ba A/B/C la mot thu -> phai con DUNG mot dai dien
        self.assertEqual(len([m for m in giu if m in ("A", "B", "C")]), 1,
                         "ba ban sao ma giu lai %s" % giu)

    def test_khong_co_ho_so_tuong_quan_thi_GIU_NGUYEN(self):
        """Mot module tia khong duoc tu y chay lai 40 giay CPU, va cung khong
        duoc bo bua khi thieu du lieu."""
        import nhan.ho_so_tuong_quan as TQ
        that = TQ.doc
        TQ.doc = lambda khung="D1": {}
        try:
            giu, bo = TH.ma_khong_trung(["A", "B", "C"], "D1")
        finally:
            TQ.doc = that
        self.assertEqual(giu, ["A", "B", "C"])
        self.assertEqual(bo, {})

    def test_khoang_kich_hoat_hop_le(self):
        lo, hi = TH.KICH_HOAT
        self.assertGreater(lo, 0.0)
        self.assertLess(hi, 1.0)
        self.assertLess(lo, hi)

    def test_co_che_ngoai_khoang_kich_hoat_bi_loai(self):
        import nhan.ngu_phap as NP
        that = NP.doc_kho
        NP.doc_kho = lambda: [
            {"ten": "qua_thua", "_ty_le_kich_hoat": 0.001},
            {"ten": "vua", "_ty_le_kich_hoat": 0.20},
            {"ten": "qua_day", "_ty_le_kich_hoat": 0.95},
            {"ten": "khong_do", "_ty_le_kich_hoat": None},
        ]
        try:
            ten = [s["ten"] for s in TH.co_che_dung_duoc()]
        finally:
            NP.doc_kho = that
        self.assertEqual(ten, ["vua"])


class PhepGOP_PhaiDUNG(unittest.TestCase):
    def _rows(self):
        return [
            {"khung": "D1", "cagr_dd20": 2.0, "hon_moc": True},
            {"khung": "D1", "cagr_dd20": -1.0, "hon_moc": False},
            {"khung": "H4", "cagr_dd20": -3.0, "hon_moc": False},
            {"khung": "H4", "cagr_dd20": -5.0, "hon_moc": False},
        ]

    def test_xep_theo_trung_vi_giam_dan(self):
        b = TH._theo_chieu(self._rows(), "khung")
        self.assertEqual([r["gia_tri"] for r in b], ["D1", "H4"])

    def test_dem_dung_so_o_va_ti_le_duong(self):
        b = {r["gia_tri"]: r for r in TH._theo_chieu(self._rows(), "khung")}
        self.assertEqual(b["D1"]["so_o"], 2)
        self.assertEqual(b["D1"]["hon_moc"], 1)
        self.assertAlmostEqual(b["D1"]["ti_le_duong"], 0.5)
        self.assertEqual(b["H4"]["hon_moc"], 0)
        self.assertAlmostEqual(b["H4"]["ti_le_duong"], 0.0)

    def test_tot_nhat_la_CUC_DAI_khong_phai_trung_vi(self):
        b = {r["gia_tri"]: r for r in TH._theo_chieu(self._rows(), "khung")}
        self.assertAlmostEqual(b["D1"]["tot_nhat"], 2.0)


class TongKetPhaiMANG_CANH_BAO(unittest.TestCase):
    def test_bao_cao_noi_ro_thien_lech_chon_loc(self):
        ket = {"so_ma": 3, "khung": ["D1"], "giay": 1.0,
               "tat_ca_chang2": [
                   {"khung": "D1", "cau_truc": "thi_truong", "luat": "-",
                    "ho": "x", "ma": "A", "cagr_dd20": 1.0, "hon_moc": True,
                    "moc_dd20": 0.0, "co_che": "c1"},
                   {"khung": "D1", "cau_truc": "tt_hedge", "luat": "-",
                    "ho": "x", "ma": "A", "cagr_dd20": -1.0, "hon_moc": False,
                    "moc_dd20": 0.0, "co_che": "c1"}]}
        vb = TH.tong_ket(ket, in_ra=lambda *a, **k: None)
        self.assertIn("DOC BANG NAY NHU THE NAO", vb)
        self.assertIn("bi thoi len boi chinh phep", vb)
        self.assertIn("NEN DI", vb)
        self.assertIn("NEN TRANH", vb)

    def test_khong_o_nao_thang_moc_thi_NOI_THANG(self):
        ket = {"so_ma": 1, "khung": ["D1"], "giay": 1.0,
               "tat_ca_chang2": [
                   {"khung": "D1", "cau_truc": "thi_truong", "luat": "-",
                    "ho": "x", "ma": "A", "cagr_dd20": -1.0, "hon_moc": False,
                    "moc_dd20": 5.0, "co_che": "c1"},
                   {"khung": "H4", "cau_truc": "tt_hedge", "luat": "-",
                    "ho": "x", "ma": "A", "cagr_dd20": -2.0, "hon_moc": False,
                    "moc_dd20": 5.0, "co_che": "c1"}]}
        vb = TH.tong_ket(ket, in_ra=lambda *a, **k: None)
        self.assertIn("Khong o nao thang moc", vb)
        self.assertIn("khong phai mot", vb)


class LuoiThamSoPhaiDO_DO_NHAY(unittest.TestCase):
    def test_luoi_co_cap_lan_can_de_do_cao_nguyen(self):
        """`cao-nguyen-hay-cai-gai`: mot luoi ma moi diem mot goc troi thi khong
        noi duoc edge la cao nguyen hay cai gai."""
        sl = sorted({t.get("sl_atr") for t in TH.LUOI_THAM if "sl_atr" in t})
        self.assertGreaterEqual(len(sl), 3, "luoi khong du diem de do do nhay")

    def test_giu_chang_giam_dan(self):
        self.assertGreater(TH.GIU_CHANG1, TH.GIU_CHANG2,
                           "pheu phai HEP dan, khong thi khong phai pheu")


if __name__ == "__main__":
    unittest.main(verbosity=2)


# --------------------------------------------- THU TU DUYET PHAI THEO PHEP DO
#
# Them 13/09/2026. `co_che_dung_duoc` truoc do xep theo TEN (bang chu cai), nen
# khi `gioi_han` cat bot thi cai bi cat la cai co ten van bang Z - hoan toan
# ngau nhien so voi chat luong.
#
# Do tren 1.276 ket qua da cham:
#     phoi nhiem 10-25%: 494 phep thu (39%), ty le PASS 1,2%, CAGR tv -0,42%
#     phoi nhiem 25-40%: 104 phep thu ( 8%), ty le PASS 4,8%, CAGR tv +0,86%
# Pheu tieu 39% cong suc vao vung ngheo nhat va 8% vao vung tot nhat.
#
# `_ty_le_kich_hoat` trong kho du bao phoi nhiem that voi r = 0,964 (97 cap),
# nen no xep hang truoc duoc.

def test_thu_tu_duyet_uu_tien_vung_sinh_loi():
    from nhan import to_hop as TH
    ds = TH.co_che_dung_duoc()
    assert len(ds) > 200, "kho qua nho de kiem thu tu"
    lo, hi = TH.VUNG_SINH_LOI
    n = min(300, len(ds) // 2)
    dau = sum(1 for s in ds[:n]
              if lo <= float(s["_ty_le_kich_hoat"]) <= hi)
    cuoi = sum(1 for s in ds[-n:]
               if lo <= float(s["_ty_le_kich_hoat"]) <= hi)
    assert dau > cuoi * 3, (
        "%d/%d cai DUYET DAU nam trong vung sinh loi, %d/%d cai CUOI - thu tu "
        "khong uu tien gi" % (dau, n, cuoi, n))


def test_van_giu_DU_co_che_khong_loai_them():
    """Doi thu tu KHONG duoc lam mat co che nao - do la mot cong tra hinh."""
    from nhan import ngu_phap as NP
    from nhan import to_hop as TH
    lo, hi = TH.KICH_HOAT
    du = [s for s in NP.doc_kho()
          if s.get("_ty_le_kich_hoat") is not None
          and lo <= float(s["_ty_le_kich_hoat"]) <= hi]
    assert len(TH.co_che_dung_duoc()) == len(du)


def test_tran_kich_hoat_060_co_co_so():
    """Tran tren KHONG duoc noi: nhom >=60% la nhom TE NHAT (356 mau, CAGR
    tv -1,89%, ty le PASS 0%). Ghi chu goc cua no khong neu phep do nao, nen
    phep do nam o day."""
    from nhan import to_hop as TH
    assert TH.KICH_HOAT[1] <= 0.60
    assert TH.VUNG_SINH_LOI[1] <= TH.KICH_HOAT[1]


# ----------------------------------------------------- HAN NGACH THEO MA
#
# Do that 12/09: chang 1 giu 200 o -> chi 2 ma. Phep chon `sort()[:200]` cho
# phep mot ma an tron suat giu, va khi do thi chang 2/3/4 khong con do thi
# truong nua ma do mot ma.

def _o(ma, diem, co_che="c"):
    return {"ma": ma, "co_che": co_che, "cagr_dd20": diem}


def test_han_ngach_chan_mot_ma_an_tron():
    from nhan import to_hop as TH
    # EURMXN chiem tron 50 diem cao nhat - dung hinh dang do duoc 12/09.
    ds = [_o("EURMXN", 1000 - i) for i in range(50)]
    for j in range(10):
        ds += [_o("MA%d" % j, 10 - j - i * 0.01) for i in range(50)]
    ds.sort(key=lambda d: -d["cagr_dd20"])

    assert len({d["ma"] for d in ds[:20]}) == 1      # khong han ngach: 1 ma

    giu = TH.giu_co_han_ngach(ds, 20, ti_le=0.1)     # tran = 2
    assert len(giu) == 20
    dem = {}
    for d in giu:
        dem[d["ma"]] = dem.get(d["ma"], 0) + 1
    assert max(dem.values()) == 2, dem
    assert len(dem) == 10, dem
    assert dem["EURMXN"] == 2                        # van duoc phan cua no


def test_han_ngach_KHONG_doi_gi_khi_da_da_dang():
    """Hieu chuan chieu nguoc: mot bo loc luon ra tay thi vo dung nhu mot bo
    loc khong bao gio ra tay. Khi khong ma nao vuot tran, ket qua phai GIONG
    HET `sort()[:n]`."""
    from nhan import to_hop as TH
    ds = [_o("MA%02d" % i, 100 - i) for i in range(60)]
    giu = TH.giu_co_han_ngach(ds, 20)
    assert [d["ma"] for d in giu] == [d["ma"] for d in ds[:20]]


def test_han_ngach_van_giu_du_n_khi_it_ma():
    """Chi co 2 ma ma doi 20 o: tran phai tu noi len, khong duoc tra ve 4 o
    roi lam chang sau doi."""
    from nhan import to_hop as TH
    ds = [_o("A", 100 - i) for i in range(30)] + \
         [_o("B", 50 - i) for i in range(30)]
    ds.sort(key=lambda d: -d["cagr_dd20"])
    giu = TH.giu_co_han_ngach(ds, 20)
    assert len(giu) == 20


def test_han_ngach_giu_dung_cai_TOT_NHAT_cua_moi_ma():
    """Khong duoc doi thu tu trong noi bo mot ma: o dau tien cua EURUSD phai
    la o diem cao nhat cua EURUSD."""
    from nhan import to_hop as TH
    ds = [_o("X", 100), _o("X", 99), _o("Y", 98), _o("X", 97), _o("Y", 96)]
    giu = TH.giu_co_han_ngach(ds, 4, ti_le=0.25)   # tran = 1
    diem = {}
    for d in giu:
        diem.setdefault(d["ma"], []).append(d["cagr_dd20"])
    assert diem["X"][0] == 100 and diem["Y"][0] == 98


def test_han_ngach_chang2_khoa_theo_HE_khong_theo_ma():
    """Mot he xuat hien 15 lan o chang 2 (7 cau truc + 8 luat). Khoa theo ma
    thi mot he van chiem tron suat giu mot cach hop le."""
    from nhan import to_hop as TH
    ds = [_o("EURUSD", 100 - i, co_che="he_A") for i in range(15)]
    ds += [_o("EURUSD", 80 - i, co_che="he_B") for i in range(15)]
    ds += [_o("GOLD", 70 - i, co_che="he_C") for i in range(15)]
    ds.sort(key=lambda d: -d["cagr_dd20"])
    k = lambda d: (d["ma"], d["co_che"])       # noqa: E731
    giu = TH.giu_co_han_ngach(ds, 12, k, ti_le=1 / 3.0)   # tran = 4
    assert len({k(d) for d in giu}) == 3
    assert len(giu) == 12


def test_han_ngach_rong_va_n_0():
    from nhan import to_hop as TH
    assert TH.giu_co_han_ngach([], 10) == []
    assert TH.giu_co_han_ngach([_o("A", 1)], 0) == []


# ------------------------------------------- CHI PHI KHAI KHONG DUOC VAO PHEU
#
# `lab/CLAUDE.md`: "Chi phi phai DO DUOC. `cp.do_tin` la KHAI thi khong bao gio
# PASS." Luat co tu lau; `to_hop` chua bao gio doc `do_tin`.
#
# Do 13/09 tren mot luot chang 1 sach: 8 ma dan dau deu KHAI (nen chung
# 90/159). Bo chung di thi top 40 doi tu "cagr_dd20 tv 5,6 / moc 0,0 / vuot moc
# 39/40" thanh "1,7 / 2,2 / 26/40" - so nho hon nhung la so that.

class _Phi:
    def __init__(self, dt):
        self.do_tin = dt


def test_bo_ma_chi_phi_KHAI(monkeypatch):
    from nhan import chi_phi as CP
    from nhan import du_lieu as DL
    from nhan import to_hop as TH
    bang = {"EURGBP": "SAN", "AUDCAD": "SAN", "CHFDKK": "KHAI",
            "EURRUR": "KHAI"}
    monkeypatch.setattr(DL, "nap", lambda m, k: None)
    monkeypatch.setattr(CP, "tu_du_lieu", lambda m, df: _Phi(bang[m]))
    giu, bo = TH.ma_co_chi_phi_do_duoc(list(bang))
    assert sorted(giu) == ["AUDCAD", "EURGBP"]
    assert sorted(bo) == ["CHFDKK", "EURRUR"]
    assert all("KHAI" in v for v in bo.values())


def test_ma_do_chi_phi_that_bai_cung_bi_bo_KHONG_im_lang(monkeypatch):
    """Do chi phi nem loi -> bo, nhung phai co ly do. Bo im lang la cach mot
    con so 'quet 145 ma' tro thanh sai."""
    from nhan import chi_phi as CP
    from nhan import du_lieu as DL
    from nhan import to_hop as TH

    def no(m, df):
        raise ValueError("khong co nguon")
    monkeypatch.setattr(DL, "nap", lambda m, k: None)
    monkeypatch.setattr(CP, "tu_du_lieu", no)
    giu, bo = TH.ma_co_chi_phi_do_duoc(["X"])
    assert giu == [] and "X" in bo and bo["X"]


def test_cong_nay_KHONG_duoc_bo_sach(monkeypatch):
    """Hieu chuan chieu nguoc: tat ca SAN thi khong duoc bo ai. Mot cong tu
    choi tat ca cho so lieu y het mot cong tot."""
    from nhan import chi_phi as CP
    from nhan import du_lieu as DL
    from nhan import to_hop as TH
    monkeypatch.setattr(DL, "nap", lambda m, k: None)
    monkeypatch.setattr(CP, "tu_du_lieu", lambda m, df: _Phi("SAN"))
    giu, bo = TH.ma_co_chi_phi_do_duoc(["A", "B", "C"])
    assert giu == ["A", "B", "C"] and bo == {}


def test_cong_tat_duoc_de_do_lai():
    """`DOI_CHI_PHI_DO_DUOC` phai la mot hang so doc duoc, khong phai mot dieu
    kien chon trong ham - khong thi khong ai do lai duoc anh huong cua no."""
    from nhan import to_hop as TH
    assert isinstance(TH.DOI_CHI_PHI_DO_DUOC, bool)


def test_cli_hieu_tham_so_khung():
    """`--khung D1` truoc day roi xuong nhanh `else` nen CA "--khung" lan "D1"
    thanh ten khung - ban TO_HOP.json cu ghi lai dau vet:
    `"khung": ["--khung", "D1"]`. Chay duoc chi vi khung rac bi bo lang le."""
    import pytest

    from nhan import to_hop as TH
    thay = {}
    goc = TH.chay
    TH.chay = lambda kh, a, b, c: thay.setdefault("kh", kh) or {}
    goc_tk = TH.tong_ket
    TH.tong_ket = lambda *a, **k: None
    try:
        TH.main(["--khung", "D1"])
        assert thay["kh"] == ("D1",)
        with pytest.raises(SystemExit):
            TH.main(["--khhung", "D1"])
    finally:
        TH.chay, TH.tong_ket = goc, goc_tk


def test_chang_chon_KHONG_duoc_cham_nua_holdout():
    """Chang 1/2/3 phai chay tren `train`. Neu chung chay tren "het" thi chang 4
    khong con la holdout: he lot toi do da duoc chon bang chinh du lieu sap dung
    de kiem. Do dem 13/09 khi con lo nay: 592/2.248 = 26% "qua holdout"."""
    import inspect

    from nhan import to_hop as TH
    src = inspect.getsource(TH.chay)
    v1 = [l for l in src.splitlines() if "v1 = [(" in l]
    assert v1 and '"train"' in v1[0], v1
    for l in src.splitlines():
        if "v2.append((" in l or "v3.append((" in l:
            assert '"train"' in l, l
    # chi chang 4 duoc cham ca hai nua
    assert 'for ph in ("train", "hold")' in src


# --------------------------------------------- NHO BANG GIA TRONG BO NHO
#
# `du_lieu.nap` cache ra PARQUET TREN DIA, nen moi o cua pheu doc lai file.
# Do 13/09 tren XM_US100CASH D1: nap 0,798s · sinh tin hieu 0,002s · mo phong
# 0,038s -> tinh toan THAT chi 0,040s/o trong khi chang 1 tra 0,56s/o.
# 14/15 thoi gian la doc lai cung mot bang gia khong he doi.

def test_cache_KHONG_doi_ket_qua():
    """Diem chet cua cache la chia chung mot doi tuong: neu mot khau them cot
    vao bang gia thi khau sau thay bang khac. Chay cung mot o hai lan (lan hai
    an cache) phai ra so Y HET."""
    from nhan import ngu_phap as NP
    from nhan import to_hop as TH
    cc = [s for s in NP.doc_kho()][:40]
    v = [("XM_US100CASH", "D1", s, "thi_truong", None, None) for s in cc]
    TH._NHO_GIA.clear(); TH._NHO_THU_TU.clear()
    a = [TH._mot_o(x) for x in v]           # lan 1: nap that
    b = [TH._mot_o(x) for x in v]           # lan 2: tu cache
    assert TH._NHO_GIA, "cache khong giu gi ca"
    n = 0
    for x, y in zip(a, b):
        if not x or "cagr_dd20" not in x:
            continue
        n += 1
        # so MOI truong so, khong chi vai cot chon san - mot cot bi lech ma
        # khong nam trong danh sach thi phep kiem nay vo dung
        cot = [k for k, v in x.items() if isinstance(v, (int, float))]
        assert cot, x
        assert {c: x[c] for c in cot} == {c: y.get(c) for c in cot}, (x, y)
    assert n >= 10, "khong du o de ket luan (%d)" % n


def test_cache_khong_phinh_vo_han():
    """Mot tien trinh con di qua 72 ma; giu het la om ca kho gia trong RAM."""
    from nhan import to_hop as TH
    TH._NHO_GIA.clear(); TH._NHO_THU_TU.clear()
    for i in range(TH.NHO_TOI_DA + 6):
        TH._NHO_GIA[("M%d" % i, "D1")] = object()
        TH._NHO_THU_TU.append(("M%d" % i, "D1"))
        while len(TH._NHO_THU_TU) > TH.NHO_TOI_DA:
            TH._NHO_GIA.pop(TH._NHO_THU_TU.pop(0), None)
    assert len(TH._NHO_GIA) == TH.NHO_TOI_DA
    TH._NHO_GIA.clear(); TH._NHO_THU_TU.clear()
