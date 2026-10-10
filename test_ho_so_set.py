# -*- coding: utf-8 -*-
"""nhan/ho_so_set.py - doi chieu bo .set cua tac gia voi co che do tu LENH THAT (test 10/10/2026).

Module nay dua ra cac phan quyet "tac gia noi X, lenh that cho thay Y", nen test canh giu nam dieu (moi dieu duoc kiem bang du lieu
tu dung hoac bang lan chay THAT tren tep lenh tester that cua VamGe v3.05, 3114 lenh, nam trong git):
  (1) MOI khoa cua .set vao DUNG MOT dong, theo thu tu trong .set; mot bo doi chieu hong KHONG lam mat het va KHONG im lang (vao `loi`);
  (2) KHONG co bang chung thi KHONG BAO GIO ket luan KHOP / MAU_THUAN / BI_CHE: "tham so khong do duoc khong bao gio la tac gia khong dung"
      (TAT chi cho tham so tac gia KHAI TAT);
  (3) cac nguong canh bao (mau thuan >= 40% cua >= 5 tham so da quyet dinh, luoi tick >= 5 giay, thieu bang lenh...) va phep so sanh nhieu bo
      (`so_sanh_bo_set`: bang chung chi khi doi khai bao keo theo doi hanh vi VA moi dong KHOP) dung dinh nghia;
  (4) bao cao Markdown luon ASCII (.set cua tac gia co dau); `main` tra 1 khi co bo hong; `doc_set` khong de lo gia tri nhay cam;
  (5) lan chay that cho ra dung cac con so da ghi (danh dau `cham`, chay MOT lan cho ca module)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

from nhan import ho_so_set as HS

KHOP, MAU_THUAN, TAT = HS.KHOP, HS.MAU_THUAN, HS.TAT
_FIX = Path(__file__).resolve().parent / "reports" / "fixture"


# ---------------------------------------------------------------------------------------------------------------- do dung chung
@pytest.fixture
def gia(monkeypatch):
    """Thay danh sach bo doi chieu THAT bang cac ham do test dat: kiem ham dieu phoi (`doi_chieu`) tach khoi quy tac tung tham so."""
    def dat(*ham, don_vi=None):
        monkeypatch.setattr(HS, "_BO_DO", [(h.__name__.lstrip("_"), h) for h in ham])
        monkeypatch.setattr(HS, "uoc_luong_don_vi", don_vi or (lambda bo: {"he_so": 1.0, "chac": True, "diem": {}, "ly_do": "gia"}))
    return dat


def _bo_cho(kq: dict):
    """Bo doi chieu gia: ghi dong cho tung khoa chuan theo ket qua cho truoc."""
    def _bo(bo):
        for n, k in kq.items():
            bo.ghi(n, k)
    return _bo


def _cb(r, tu):
    return any(tu in w for w in r["canh_bao"])


def _hang(ten, khai, kq=KHOP, do=None, don_vi="pip", do_tin="cao", khoi=""):
    """Mot dong `tham_so` o dang ket qua `doi_chieu` tra ve."""
    return {"ten": ten, "khai": khai, "ket_qua": kq, "do": do, "don_vi": don_vi, "do_tin": do_tin, "khoi": khoi, "ly_do": "", "lop": "x", "nguon_do": ""}


def _doi(ten_bo, *hang, khoi=None):
    return (ten_bo, {"tham_so": list(hang), "khoi": khoi or {}})


# ---------------------------------------------------------------------------------------------------------------- ham nho
def test_j_ra_json_thuan_numpy_thanh_so_nan_inf_thanh_none():
    class _Xau:
        def item(self):
            raise RuntimeError("khong lay duoc")

        def __str__(self):
            return "xau"

    r = HS._j({"a": np.float64(1.5), "b": [np.int64(2), float("nan"), float("inf"), -float("inf")], "c": (1, 2), "d": {3}, "e": True, "f": None,
               "g": "x", 5: np.bool_(True), "h": _Xau(), "i": np.array(7)})
    assert r == {"a": 1.5, "b": [2, None, None, None], "c": [1, 2], "d": [3], "e": True, "f": None, "g": "x", "5": True, "h": "xau", "i": 7}
    assert type(r["b"][0]) is int and r["e"] is True and r["5"] is True
    json.dumps(r, allow_nan=False)                                       # thuan JSON: khong con nan / inf / numpy


@pytest.mark.parametrize("ten,mong", [("InpOrders2Distance1", "orders2distance1"), ("  InpLots ", "lots"), ("InpTP", "tp"), ("Lots", "lots"),
                                       ("Input", "input"), ("Inpa", "inpa"), ("inpLots", "inplots"), ("Inp_x", "_x"), ("Inp1", "1"),
                                       ("InpInp", "inp")])
def test_chuan_bo_tien_to_Inp_chi_khi_theo_sau_la_hoa_so_hoac_gach_duoi(ten, mong):
    assert HS._chuan(ten) == mong


def test_so_chi_nhan_so_huu_han_con_lai_la_none():
    assert [HS._so(v) for v in ("1.5", " 3 ", "-2", "1e3", "0")] == [1.5, 3.0, -2.0, 1000.0, 0.0]
    assert [HS._so(v) for v in ("abc", "", None, "nan", "inf", "-inf", "true")] == [None] * 7
    assert [HS._so_hoc(v) for v in ("1.5", "nan", "x", None)] == [1.5, None, None, None]


def test_bool_chi_nhan_true_false_1_0():
    assert [HS._bool(v) for v in ("true", "TRUE", " 1 ", True)] == [True] * 4
    assert [HS._bool(v) for v in ("false", "0", False)] == [False] * 3
    assert [HS._bool(v) for v in ("2", "yes", "")] == [None] * 3


def test_gio_ra_phut_ke_tu_0h_va_tu_choi_gio_phut_vo_ly():
    assert [HS._gio(v) for v in ("08:30", "8:05", "00:00", "23:59", "08:30:45", " 07:15 ")] == [510, 485, 0, 1439, 510, 435]
    assert [HS._gio(v) for v in ("24:00", "12:60", "0830", "abc", 830)] == [None] * 5


def test_tf_phut_theo_quy_uoc_enum_mt5():
    dung = {"M15": 15, "h1": 60, "PERIOD_H4": 240, 16385: 60, "16408": 1440, "32769": 10080, "49153": 43200, "15": 15, 5: 5, "1": 1, "30": 30}
    assert {k: HS.tf_phut(k) for k in dung} == dung
    for khong in ("0", "31", "15.5", "abc", "", "M45", "16409", "16384", "32768"):
        assert HS.tf_phut(khong) is None, khong                          # 0 = khung cua bieu do: khong biet la bao nhieu phut


def test_cua_so_do_buoc_khong_doi_xung_chap_nhan_buoc_do_lon_hon_khai_nhieu_hon_nho_hon():
    assert [HS._trong_cua_so(p, 10) for p in (9.49, 9.5, 10, 11.0, 11.01)] == [False, True, True, True, False]
    assert [HS._trong_cua_so(p, 100) for p in (96.9, 97.0, 100, 107.0, 107.1)] == [False, True, True, True, False]


def test_dung_sai_la_lon_hon_cua_tuyet_doi_va_ty_le_theo_gia_tri_khai():
    assert HS._dung_sai(100, 0.5, 0.03) == 3.0 and HS._dung_sai(10, 0.5, 0.03) == 0.5 and HS._dung_sai(-100, 0.5, 0.03) == 3.0
    assert HS._gan(103, 100, 0.5, 0.03) and HS._gan(97, 100, 0.5, 0.03) and not HS._gan(103.01, 100, 0.5, 0.03)


def test_gon_so_cho_van_ban():
    assert HS._gon_so(None) == "?"
    assert HS._gon_so(10.0) == "10" and HS._gon_so(15.4) == "15.4" and HS._gon_so(0.5) == "0.5" and HS._gon_so(np.float64(2.0)) == "2"
    assert HS._gon_so(np.int64(3)) == "3" and HS._gon_so(2) == "2"
    assert HS._gon_so(1234.5678) == "1.23e+03" and HS._gon_so(1234.5678, 6) == "1234.57" and HS._gon_so(1e9) == "1e+09"


def test_ty_chia_cho_0_la_0():
    assert HS._ty(1, 2) == 0.5 and HS._ty(5, 0) == 0.0


@pytest.mark.parametrize("n,ty,mong", [(100, 0.9, "cao"), (99, 0.9, "vua"), (100, 0.89, "vua"), (1000, 1.0, "cao"), (30, 0.8, "vua"),
                                       (29, 0.8, "thap"), (30, 0.79, "thap"), (100, 0.79, "thap"), (5, 1.0, "thap")])
def test_do_tin_theo_so_mau_va_ty_le_khop(n, ty, mong):
    assert HS._do_tin_tu_mau(n, ty) == mong
    assert HS._do_tin_tu_mau(100) == "cao"                               # ty_khop mac dinh 1,0


def test_ds_khoi_dem_ten_cat_gon_va_ascii():
    assert HS._ds_khoi(None) == [] and HS._ds_khoi("") == [] and HS._ds_khoi("a") == ["a"] and HS._ds_khoi(("x", "y")) == ["x", "y"]
    d = HS._dem([{"ket_qua": KHOP}, {"ket_qua": KHOP}, {"ket_qua": TAT}])
    assert d["KHOP"] == 2 and d["TAT"] == 1 and d["tong"] == 3 and set(d) == set(HS.KET_QUA) | {"tong"}
    assert HS._ten_ds([{"ten": c} for c in "abcdefgh"]) == "a, b, c, d, e, f (+2)" and HS._ten_ds([{"ten": c} for c in "abcdef"]) == "a, b, c, d, e, f"
    assert HS._ten_ds([]) == "" and HS._ten_ds([{"ten": c} for c in "abc"], toi_da=2) == "a, b (+1)"
    assert HS._cat("a  b\n c", 10) == "a b c" and HS._cat("x" * 20, 10) == "x" * 7 + "..." and HS._cat("x" * 10, 10) == "x" * 10
    assert HS._ascii("Cài đặt Đơn") == "Cai dat Don" and HS._ascii("a—b") == "a?b" and HS._ascii(123) == "123"
    assert HS._o("a|b\n  c") == "a/b c"


def test_khac_khai_so_theo_gia_tri_so_chu_theo_chu_khong_phan_biet_hoa_thuong():
    assert not HS._khac_khai("10", "10.0") and HS._khac_khai("10", "10.5") and not HS._khac_khai("1e-10", "0")
    assert not HS._khac_khai("A", "a") and HS._khac_khai("A", "b") and HS._khac_khai("10", "abc") and not HS._khac_khai(" true ", "True")


def test_la_cong_tac_chi_true_false():
    assert all(HS._la_cong_tac(v) for v in (True, False, "true", " FALSE "))
    assert not any(HS._la_cong_tac(v) for v in ("1", 1, "yes", None, 0))


# ---------------------------------------------------------------------------------------------------------------- _Bo
def test_bo_hai_khoa_cung_ten_chuan_giu_khoa_dau_va_canh_bao():
    bo = HS._Bo({"InpLots": "1", "Lots": "2", "InpTP": "3"}, {})
    assert bo.ten == {"lots": "InpLots", "tp": "InpTP"} and bo.v == {"lots": "1", "tp": "3"}
    assert len(bo.canh_bao) == 1 and "'lots'" in bo.canh_bao[0] and "InpLots va Lots" in bo.canh_bao[0]


def test_bo_doc_gia_tri_set():
    bo = HS._Bo({"InpLots": "0.5", "InpUseX": "true", "InpMode": "abc", "InpZero": "0"}, {})
    assert bo.co("lots") and not bo.co("nope")
    assert bo.so("lots") == 0.5 and bo.so("mode") is None and bo.so("mode", 7) == 7 and bo.so("nope", 3) == 3
    assert bo.so("zero", 5) == 0.0                                       # 0 la gia tri that, khong phai "thieu"
    assert bo.bat("usex") is True and bo.bat("mode") is None and bo.bat("nope") is None


def test_bo_khac_het_chi_tra_khoa_khop_regex_va_chua_co_dong():
    bo = HS._Bo({"InpDist1": "1", "InpDist2": "2", "InpLots": "3"}, {})
    assert sorted(bo.khac_het(r"^dist")) == ["dist1", "dist2"]
    bo.ghi("dist1", TAT)
    assert bo.khac_het(r"^dist") == ["dist2"]


def test_bo_ghi_dong_dau_la_dong_thang_va_chi_ghi_khoa_co_that():
    bo = HS._Bo({"InpLots": "0.01", "InpTP": "10"}, {})
    bo.lop = "lot"
    bo.ghi("khongco", KHOP)                                              # khoa khong co trong .set: bo qua, khong tao dong ma
    assert bo.hang == {}
    bo.ghi("lots", KHOP, khoi="lot_phang", do=0.01, don_vi="lot", do_tin="cao", ly_do="a", nguon="n")
    bo.ghi("lots", MAU_THUAN, ly_do="b")                                 # bo sau KHONG de len dong da co
    assert bo.hang["lots"] == {"ten": "InpLots", "khai": "0.01", "lop": "lot", "khoi": "lot_phang", "ket_qua": "KHOP", "do": 0.01, "don_vi": "lot",
                               "do_tin": "cao", "ly_do": "a", "nguon_do": "n"}
    bo.ghi("lots", TAT, ly_do="c", ghi_de=True)                          # chi ghi_de moi doi duoc
    assert bo.hang["lots"]["ket_qua"] == "TAT" and bo.hang["lots"]["ly_do"] == "c"
    bo.ghi("tp", TAT, lop="khac")
    assert bo.hang["tp"]["lop"] == "khac" and bo.hang["tp"]["do_tin"] == "vua"      # do tin mac dinh = vua


def test_bo_ghi_do_tin_la_thanh_vua_va_ket_qua_la_thi_nem_loi():
    bo = HS._Bo({"InpA": "1"}, {})
    bo.ghi("a", KHOP, do_tin="rat_cao")
    assert bo.hang["a"]["do_tin"] == "vua"
    with pytest.raises(AssertionError):
        HS._Bo({"InpB": "1"}, {}).ghi("b", "TUY_Y")


def test_bo_giai_thich_chi_ghi_khoi_cho_dong_KHOP():
    bo = HS._Bo({"InpA": "1", "InpB": "2", "InpC": "3", "InpD": "4"}, {})
    bo.ghi("a", KHOP, khoi="k1")
    bo.ghi("b", KHOP, khoi=["k1", "k2"])
    bo.ghi("c", MAU_THUAN, khoi="k3")                                    # mau thuan KHONG giai thich duoc khoi nao
    bo.ghi("d", KHOP, khoi="")
    assert bo.giai_thich == {"k1": ["InpA", "InpB"], "k2": ["InpB"]}


def test_bo_ghi_ds_ghi_het_danh_sach_va_bo_qua_khoa_la():
    bo = HS._Bo({"InpA": "1", "InpB": "2"}, {})
    bo.ghi_ds(["a", "b", "zz"], TAT, ly_do="x")
    assert set(bo.hang) == {"a", "b"} and all(h["ket_qua"] == "TAT" and h["ly_do"] == "x" for h in bo.hang.values())


def test_bo_doc_so_do_co_gia_tri_mac_dinh_an_toan():
    hs = {"phep_do": {"p": {"so_lieu": {"a": 1}}}, "khoi": {"k": {"ket_luan": "co", "do_tin": "cao"}}, "tham_so": {"t": {"gia_tri": 5}, "u": {}}}
    bo = HS._Bo({"InpA": "1"}, hs)
    assert bo.sl("p") == {"a": 1} and bo.sl("zz") == {} and bo.phep("zz") == {}
    assert bo.kl("k") == "co" and bo.kl("zz") == "khong_do_duoc" and bo.dt("k") == "cao" and bo.dt("zz") == "thap"
    assert bo.ts("t") == 5 and bo.ts("zz") is None and bo.ts("u") is None
    vo = HS._Bo({"InpA": "1"}, {})
    assert vo.sl("p") == {} and vo.kl("k") == "khong_do_duoc" and vo.dt("k") == "thap" and vo.ts("t") is None


def test_bo_do_hong_vao_loi_kem_ten_loai_loi_va_dong_khong_im_lang():
    bo = HS._Bo({"InpA": "1"}, {})

    def _no(b):
        raise KeyError("thieu_truong")

    def _dai(b):
        raise ValueError("x" * 500)

    HS._chay_bo_do(bo, "no", _no)
    HS._chay_bo_do(bo, "dai", _dai)
    assert re.fullmatch(r"no: KeyError: 'thieu_truong' \(dong \d+\)", bo.loi[0])
    assert re.fullmatch(r"dai: ValueError: x{140} \(dong \d+\)", bo.loi[1])        # thong diep dai bi cat o 140 ky tu


# ---------------------------------------------------------------------------------------------------------------- doc_set
def test_doc_set_van_ban_duong_dan_set_va_set_txt_cho_cung_ket_qua(tmp_path):
    van_ban = "; chu thich\nInpLots=0.01\nInpTP=10||5||1||20||Y\nInpUseDCA=true\n\n"
    a = HS.doc_set(van_ban, "bo_a")
    assert a["khoa"] == {"InpLots": "0.01", "InpTP": "10", "InpUseDCA": "true"} and a["n"] == 3 and a["ten"] == "bo_a"
    assert a["van_ban"] == "InpLots=0.01\nInpTP=10\nInpUseDCA=true\n"           # bo hau to toi uu ||..., sap theo ten khoa
    for ten_tep, ten_mong in (("x.set", "x"), ("y.set.txt", "y"), ("z.txt", "z")):
        p = tmp_path / ten_tep
        p.write_text(van_ban, encoding="utf-8")
        b = HS.doc_set(str(p))
        assert b["khoa"] == a["khoa"] and b["sha"] == a["sha"] and b["ten"] == ten_mong
    assert HS.doc_set(van_ban)["ten"] == "bo_set"                         # khong ten thi dat ten mac dinh
    assert HS.doc_set(b"InpLots=1\nInpTP=2\n")["n"] == 2                  # nhan ca bytes


def test_doc_set_ten_duoc_lam_sach_va_cat_o_40_ky_tu():
    assert HS.doc_set("InpA=1\nInpB=2\n", "a b/c")["ten"] == "a_b_c"
    assert len(HS.doc_set("InpA=1\nInpB=2\n", "x" * 60)["ten"]) == 40


def test_doc_set_xoa_thu_muc_tam_ca_khi_thanh_cong_lan_khi_loi(monkeypatch):
    da_tao = []
    that = HS.tempfile.mkdtemp

    def mkdtemp(*a, **k):
        d = that(*a, **k)
        da_tao.append(d)
        return d

    monkeypatch.setattr(HS.tempfile, "mkdtemp", mkdtemp)
    HS.doc_set("InpLots=1\nInpTP=2\n")
    with pytest.raises(ValueError):
        HS.doc_set("dong khong hop le\n")
    assert len(da_tao) == 2 and not any(Path(d).exists() for d in da_tao)


@pytest.mark.parametrize("van_ban,mong", [
    ("; a\n; b\n", "khong co khoa"),
    ("InpA=1\nInpA=2\n", "lap"),
    ("khong phai cap khoa gia tri\nInpA=1\n", "khong phai Khoa=GiaTri"),
    ("In-valid=1\nInpA=2\n", "khong phai Khoa=GiaTri"),
    ("InpNote=" + "x" * 201 + "\n", "qua dai"),
    ("InpNote=sk-" + "a" * 24 + "\n", "nhay cam"),
])
def test_doc_set_tu_choi_bo_set_hong_hoac_nhay_cam(van_ban, mong):
    with pytest.raises(ValueError, match=mong):
        HS.doc_set(van_ban)


def test_doc_set_khoa_nhay_cam_co_gia_tri_chu_bi_tu_choi_nhung_khong_lo_gia_tri():
    with pytest.raises(ValueError) as e:
        HS.doc_set("InpApiToken=abcdefghijklmnop\nInpLots=1\n")
    assert "InpApiToken" in str(e.value) and "abcdefghijklmnop" not in str(e.value)
    ok = HS.doc_set("InpLicenseOn=true\nInpPasswordLen=8\nInpLots=1\n")        # khoa nhay cam nhung gia tri la so ngan / cong tac: cho qua
    assert ok["khoa"]["InpLicenseOn"] == "true" and ok["khoa"]["InpPasswordLen"] == "8"


def test_doc_set_qua_500_khoa_bi_tu_choi_va_mot_dong_khong_co_xuong_dong_la_duong_dan():
    with pytest.raises(ValueError, match="qua nhieu khoa"):
        HS.doc_set("".join("InpK%d=1\n" % i for i in range(501)))
    assert HS.doc_set("".join("InpK%d=1\n" % i for i in range(500)))["n"] == 500
    with pytest.raises(OSError):
        HS.doc_set("InpLots=1")                                          # khong co xuong dong -> hieu la duong dan tep


# ---------------------------------------------------------------------------------------------------------------- doi_chieu: dieu phoi
def test_moi_khoa_set_dung_mot_dong_theo_thu_tu_va_khoa_khong_ai_xu_ly_bi_ghi_loi(gia):
    def _chi_lots(bo):
        bo.ghi("lots", KHOP, khoi="lot_phang", do_tin="cao")

    gia(_chi_lots)
    r = HS.doi_chieu({}, "InpTP=10\nInpLots=0.01\nInpZ=1\n", ten="t")
    assert [h["ten"] for h in r["tham_so"]] == ["InpTP", "InpLots", "InpZ"]
    assert r["dem"]["tong"] == 3 and r["dem"]["KHOP"] == 1 and r["dem"]["KHONG_PHAN_LOAI"] == 2
    assert sum(r["dem"][k] for k in HS.KET_QUA) == 3
    assert [l.split(":")[0] for l in r["loi"]] == ["khong_dong", "khong_dong"]
    assert "'InpTP'" in r["loi"][0] and "'InpZ'" in r["loi"][1] and "loi module" in r["tham_so"][0]["ly_do"]


def test_hai_khoa_cung_ten_chuan_khoa_sau_khong_duoc_doi_chieu_va_co_canh_bao(gia):
    def _tat_ca(bo):
        for n in list(bo.v):
            bo.ghi(n, TAT)

    gia(_tat_ca)
    r = HS.doi_chieu({}, "InpLots=1\nLots=2\n")
    a, b = r["tham_so"]
    assert a["ket_qua"] == "TAT" and b["ket_qua"] == "KHONG_PHAN_LOAI"
    assert "hai khoa cung ten chuan 'lots'" in b["ly_do"] and "'InpLots'" in b["ly_do"]
    assert r["loi"] == [] and _cb(r, "hai khoa cung ten chuan")


def test_mot_bo_hong_van_thay_duoc_trong_loi_va_cac_bo_khac_van_chay(gia):
    def _hong(bo):
        raise RuntimeError("hong that")

    def _tot(bo):
        bo.ghi("lots", KHOP, khoi="lot_phang", do_tin="cao")

    gia(_hong, _tot)
    r = HS.doi_chieu({}, "InpLots=0.01\n")
    assert r["tham_so"][0]["ket_qua"] == "KHOP"
    assert len(r["loi"]) == 1 and r["loi"][0].startswith("hong: RuntimeError: hong that (dong ")
    assert any(l.startswith("LOI: 1 bo doi chieu hong") for l in r["tom_tat"])
    assert not any(l.startswith("Luu y") for l in r["tom_tat"])         # co loi thi loi chiem cho cua luu y


def test_bo_chay_truoc_ghi_truoc_va_bo_sau_khong_de_len(gia):
    def _a(bo):
        bo.ghi("lots", TAT, ly_do="a")

    def _b(bo):
        bo.ghi("lots", KHOP, ly_do="b")

    gia(_a, _b)
    assert HS.doi_chieu({}, "InpLots=1\n")["tham_so"][0]["ly_do"] == "a"
    gia(_b, _a)
    assert HS.doi_chieu({}, "InpLots=1\n")["tham_so"][0]["ly_do"] == "b"


@pytest.mark.parametrize("xau", [0, -1, -0.5, float("inf"), float("nan")])
def test_he_so_don_vi_phai_la_so_duong_huu_han(xau):
    with pytest.raises(ValueError, match="he_so_don_vi"):
        HS.doi_chieu({}, "InpLots=1\n", he_so_don_vi=xau)


def test_he_so_don_vi_do_nguoi_goi_dat_thi_khong_uoc_luong_lai_va_dua_cho_cac_bo(gia):
    thay = []

    def _xem(bo):
        thay.append(bo.f)
        bo.ghi("lots", TAT)

    def _cam(bo):
        raise AssertionError("khong duoc uoc luong lai")

    gia(_xem, don_vi=_cam)
    r = HS.doi_chieu({}, "InpLots=1\n", he_so_don_vi=10)
    assert r["loi"] == [] and thay == [10.0]
    assert r["don_vi"]["he_so"] == 10.0 and r["don_vi"]["chac"] is True and "nguoi goi dat he so don vi = 10" in r["don_vi"]["ly_do"]


def test_he_so_don_vi_uoc_luong_duoc_dua_cho_cac_bo(gia):
    thay = []

    def _xem(bo):
        thay.append(bo.f)
        bo.ghi("lots", TAT)

    gia(_xem, don_vi=lambda bo: {"he_so": 0.1, "chac": True, "diem": {"0.1": 4}, "ly_do": "uoc luong"})
    r = HS.doi_chieu({}, "InpLots=1\n")
    assert thay == [0.1] and r["don_vi"] == {"he_so": 0.1, "chac": True, "ly_do": "uoc luong", "diem": {"0.1": 4}}


def test_uoc_luong_don_vi_hong_thi_giu_he_so_1_khong_chac_va_ghi_loi(gia):
    def _hong(bo):
        raise RuntimeError("x")

    gia(don_vi=_hong)
    r = HS.doi_chieu({}, "InpLots=1\n")
    assert r["don_vi"]["he_so"] == 1.0 and r["don_vi"]["chac"] is False
    assert r["loi"] and r["loi"][0].startswith("uoc_luong_don_vi: RuntimeError: x") and _cb(r, "khong chac")


def test_bo_set_nhan_ca_dict_khoa_lan_van_ban(gia):
    gia(_bo_cho({"lots": KHOP}))
    r = HS.doi_chieu({}, {"khoa": {"InpLots": 1, "InpTP": 2}, "ten": "goc", "sha": "abc"}, c=object())
    assert r["bo_set"] == {"ten": "goc", "n": 2, "sha": "abc"}
    assert [h["khai"] for h in r["tham_so"]] == ["1", "2"]               # gia tri luon la chuoi
    r2 = HS.doi_chieu({}, {"khoa": {"InpLots": 1}}, ten="khac", c=object())
    assert r2["bo_set"] == {"ten": "khac", "n": 1, "sha": ""}


def test_ket_qua_la_json_thuan_du_khoa_va_giu_ten_sha(gia):
    gia(_bo_cho({"lots": KHOP}))
    r = HS.doi_chieu({"mau": {"tick_s": np.float64(10.0), "so_lenh": np.int64(5), "x": float("nan")}}, "InpLots=1\n", ten="t")
    json.dumps(r, allow_nan=False)
    assert set(r) == {"phien_ban", "bo_set", "mau", "don_vi", "tham_so", "dem", "mau_thuan", "nut_an", "cong_thuc", "khoi", "kiem_lot", "ghi_chu",
                      "canh_bao", "loi", "tom_tat"}
    assert r["phien_ban"] == HS.PHIEN_BAN and r["mau"] == {"tick_s": 10.0, "so_lenh": 5, "x": None}
    assert r["bo_set"] == {"ten": "t", "n": 1, "sha": HS.doc_set("InpLots=1\n", "t")["sha"]}


# ---------------------------------------------------------------------------------------------------------------- doi_chieu: canh bao
@pytest.mark.parametrize("so_khop,so_mau_thuan,co", [(3, 2, True), (6, 4, True), (2, 3, True), (1, 5, True), (4, 1, False), (4, 2, False),
                                                      (2, 2, False), (0, 4, False)])
def test_canh_bao_mau_thuan_tu_40_phan_tram_cua_it_nhat_5_tham_so_da_quyet_dinh(gia, so_khop, so_mau_thuan, co):
    kq = {"p%d" % i: KHOP for i in range(so_khop)}
    kq.update({"q%d" % i: MAU_THUAN for i in range(so_mau_thuan)})
    gia(_bo_cho(kq))
    r = HS.doi_chieu({}, "".join("Inp%s=1\n" % n.upper() for n in kq), c=object())
    assert _cb(r, "MAU THUAN chiem") is co
    if co:
        assert _cb(r, "MAU THUAN chiem %d/%d" % (so_mau_thuan, so_khop + so_mau_thuan))


def test_canh_bao_khong_co_tham_so_nao_khop(gia):
    gia(_bo_cho({"a": TAT}))
    assert _cb(HS.doi_chieu({}, "InpA=1\n", c=object()), "khong co tham so nao KHOP")
    gia(_bo_cho({"a": KHOP}))
    assert not _cb(HS.doi_chieu({}, "InpA=1\n", c=object()), "khong co tham so nao KHOP")


def test_canh_bao_thieu_bang_lenh_chi_khi_c_la_none(gia):
    gia(_bo_cho({"a": KHOP}))
    assert _cb(HS.doi_chieu({}, "InpA=1\n"), "khong co bang lenh")
    assert not _cb(HS.doi_chieu({}, "InpA=1\n", c=object()), "khong co bang lenh")


@pytest.mark.parametrize("tick_s,co", [(None, False), (4.99, False), (5, True), (10.0, True)])
def test_canh_bao_luoi_tick_tu_5_giay_tro_len(gia, tick_s, co):
    gia(_bo_cho({"a": KHOP}))
    hs = {"mau": {"tick_s": tick_s} if tick_s is not None else {}}
    r = HS.doi_chieu(hs, "InpA=1\n", c=object())
    assert _cb(r, "lenh tester dat tren luoi") is co
    if co:
        assert _cb(r, "luoi %s giay" % HS._gon_so(tick_s))


def test_canh_bao_he_so_don_vi_khong_chac(gia):
    gia(_bo_cho({"a": KHOP}), don_vi=lambda bo: {"he_so": 10.0, "chac": False, "diem": {}, "ly_do": "it cap"})
    r = HS.doi_chieu({}, "InpA=1\n", c=object())
    assert _cb(r, "he so don vi khoang cach (10) khong chac: it cap")
    gia(_bo_cho({"a": KHOP}))
    assert not _cb(HS.doi_chieu({}, "InpA=1\n", c=object()), "khong chac")


# ---------------------------------------------------------------------------------------------------------------- doi_chieu: khoi / nut an / tom tat
def test_khoi_co_trong_lenh_that_ma_khong_dong_KHOP_nao_la_nut_an(gia):
    hs = {"khoi": {
        "lot_phang": {"ket_luan": "co", "do_tin": "cao", "ten": "Lot phang", "nhom": "lot", "ly_do": "lot dau 0,01"},
        "co_hedge": {"ket_luan": "co", "do_tin": "vua", "ten": "Doi ung", "nhom": "hedge", "ly_do": "co lenh doi ung"},
        "tp_chuoi": {"ket_luan": "khong", "do_tin": "vua", "ten": "TP chuoi", "nhom": "tp", "ly_do": ""},
        "khoi_mo": {"ket_luan": "khong_do_duoc", "do_tin": "thap", "ten": "Khoi mo"}},
        "tham_so": {"lot_dau": {"khoi": "lot_phang", "gia_tri": 0.01, "don_vi": "lot"}, "khac": {"khoi": "khoi_mo", "gia_tri": 1}}}

    def _bo(bo):
        bo.ghi("lots", KHOP, khoi="lot_phang", do_tin="cao")
        bo.ghi("hedge", TAT, khoi="co_hedge", do_tin="vua")             # .set noi toi khoi nhung KHONG khop
        bo.ghi("tp", TAT, khoi="tp_chuoi")

    gia(_bo)
    r = HS.doi_chieu(hs, "InpLots=0.01\nInpHedge=false\nInpTP=0\n", c=object())
    assert [k["khoi"] for k in r["cong_thuc"]] == ["lot_phang", "co_hedge"]          # chi khoi ket_luan == "co"
    assert [k["co_khop"] for k in r["cong_thuc"]] == [True, False]
    assert [n["khoi"] for n in r["nut_an"]] == ["co_hedge"]
    assert r["nut_an"][0]["tham_so_lien_quan"] == [{"ten": "InpHedge", "khai": "false", "ket_qua": "TAT", "do_tin": "vua"}]
    assert r["cong_thuc"][0]["tham_so_do"] == {"lot_dau": {"gia_tri": 0.01, "don_vi": "lot"}}
    assert r["cong_thuc"][0]["tham_so_set"] == [{"ten": "InpLots", "khai": "0.01", "ket_qua": "KHOP", "do_tin": "cao"}]
    assert set(r["khoi"]) == {"lot_phang", "co_hedge", "tp_chuoi"}      # khoi_mo (khong do duoc, khong dong .set nao) khong vao
    assert r["khoi"]["tp_chuoi"]["ket_luan"] == "khong" and r["khoi"]["lot_phang"]["tham_so_set"][0]["ten"] == "InpLots"
    assert any(l.startswith("NUT AN") and "Doi ung (co_hedge)" in l for l in r["tom_tat"])


def test_dong_noi_toi_nhieu_khoi_giai_thich_tat_ca_cac_khoi_khop(gia):
    hs = {"khoi": {"a": {"ket_luan": "co", "do_tin": "cao"}, "b": {"ket_luan": "co", "do_tin": "cao"}}}

    def _bo(bo):
        bo.ghi("x", KHOP, khoi=["a", "b"])
        bo.ghi("y", KHOP, khoi="a")

    gia(_bo)
    r = HS.doi_chieu(hs, "InpX=1\nInpY=2\n", c=object())
    x, y = r["tham_so"]
    assert x["khoi"] == "a" and x["khoi_phu"] == ["b"] and y["khoi"] == "a" and "khoi_phu" not in y
    assert "_kd" not in x and "_kd" not in y
    assert r["nut_an"] == [] and [k["co_khop"] for k in r["cong_thuc"]] == [True, True]


def test_tom_tat_dong_dau_ghi_so_lenh_san_va_cac_dong_theo_ket_qua(gia):
    hs = {"mau": {"so_lenh": 120, "ma": "EURUSD"}}

    def _bo(bo):
        bo.ghi("lots", KHOP, khoi="lot_phang", do_tin="cao")
        bo.ghi("tp", MAU_THUAN, do_tin="thap", ly_do="tac gia noi 10")
        bo.ghi("x", HS.CHUA_GAP, ly_do="chua toi")

    gia(_bo)
    r = HS.doi_chieu(hs, "InpLots=0.01\nInpTP=10\nInpX=1\n", ten="demo", c=object())
    t = r["tom_tat"]
    assert t[0] == ("Bo .set 'demo' (3 tham so) doi chieu voi 120 lenh that cua EURUSD: KHOP 1, MAU THUAN 1, TAT 0, BI CHE 0, CHUA GAP 1, "
                    "KHONG DO DUOC 0, KHONG RO 0, khac 0.")
    assert t[1] == "Don vi khoang cach: 1 don vi trong .set = 1 pip cua san (da kiem bang nhieu cap so duoc)."
    assert t[2] == "Khop chac (do tin cao): InpLots."
    assert t[3].startswith("MAU THUAN (tac gia noi X, lenh that cho thay Y): InpTP (khai 10, tin cay thap).") and t[3].endswith("Vi du: tac gia noi 10")
    assert t[4] == "CHUA GAP (lich su chua toi dieu kien cua tham so): InpX."
    assert len(t) == 5 and r["canh_bao"] == []


def test_tom_tat_khong_co_khop_chac_thi_noi_ro_va_dong_don_vi_noi_chua_chac(gia):
    gia(_bo_cho({"a": KHOP}), don_vi=lambda bo: {"he_so": 1.0, "chac": False, "diem": {}, "ly_do": ""})
    t = HS.doi_chieu({}, "InpA=1\n", c=object())["tom_tat"]
    assert t[1].endswith("(chua chac: khong du cap khoang cach de so).")


def test_tom_tat_cat_danh_sach_mau_thuan_o_4_nut_an_o_5(gia):
    khoi = {"k%d" % i: {"ket_luan": "co", "do_tin": "cao", "ten": "Khoi %d" % i} for i in range(7)}

    def _bo(bo):
        for n in list(bo.v):
            bo.ghi(n, MAU_THUAN, ly_do="ly do " + n)

    gia(_bo)
    r = HS.doi_chieu({"khoi": khoi}, "".join("InpM%d=%d\n" % (i, i) for i in range(6)), c=object())
    mt = next(l for l in r["tom_tat"] if l.startswith("MAU THUAN"))
    assert "(+2)" in mt and mt.count("tin cay") == 4
    na = next(l for l in r["tom_tat"] if l.startswith("NUT AN"))
    assert na.count("(k") == 5 and len(r["nut_an"]) == 7
    assert len(r["tom_tat"]) <= 8


def test_tom_tat_ghi_ket_qua_kiem_lot_khi_bo_do_lot_dat_bo_kiem_lot(gia):
    def _bo(bo):
        bo.kiem_lot = {"khop": 9, "tong": 10, "ty": 0.9, "cong_thuc": "lot_n = f(n)"}
        bo.ghi("lots", KHOP, do_tin="cao")

    gia(_bo)
    r = HS.doi_chieu({}, "InpLots=1\n", c=object())
    assert "Lot: 9/10 lenh dung cong thuc lot_n = f(n)." in r["tom_tat"] and r["kiem_lot"]["khop"] == 9


def test_tom_tat_khong_loi_thi_dong_cuoi_la_luu_y_dau_tien(gia):
    gia(_bo_cho({"a": TAT}))
    r = HS.doi_chieu({}, "InpA=1\n")
    assert r["tom_tat"][-1].startswith("Luu y: khong co tham so nao KHOP") and r["tom_tat"][2] == "Khong co tham so nao khop o do tin cao."


# ---------------------------------------------------------------------------------------------------------------- doi_chieu: quy tac that, ho so trong
def test_ho_so_trong_khong_bao_gio_phan_quyet_khop_mau_thuan_hay_bi_che():
    """Khong co bang chung thi chi duoc noi 'khong do duoc / chua gap / chua doi chieu / tat (tac gia khai tat)' - khong duoc noi 'tac gia sai'."""
    van_ban = ("InpLots=0.01\nInpTP=10\nInpSL=0\nInpUseDCA=true\nInpMultiplier=2\nInpMagicID=7\nInpEMAPeriod=20\nInpTFSignal=16385\nInpSomethingNew=5\n"
               "InpUseHedging=false\nInpOrders2Hedging=3\nInpUseTrailing=false\nInpUseLottery=false\nInpUseLottery2=1\nInpMinuteDelayAfterClose=60\n"
               "InpDistance0=10\nInpOrders2Distance1=5\nInpDistance1=15\nInpMaxBuyOrders=100\nInpMaxLots=2.3\nInpMaxSpread=6\nInpStartHour=8\n"
               "InpShowTP=false\nInpNewMultiplier=1.5\nInpOrders2NewMultiplier=4\n")
    r = HS.doi_chieu({}, van_ban, ten="trong")
    ten = [l.split("=")[0] for l in van_ban.splitlines()]
    assert r["loi"] == [] and [h["ten"] for h in r["tham_so"]] == ten                # mot dong cho moi khoa, dung thu tu
    d = r["dem"]
    assert d["tong"] == len(ten) and sum(d[k] for k in HS.KET_QUA) == len(ten)
    assert d["KHOP"] == d["MAU_THUAN"] == d["BI_CHE"] == 0 and r["mau_thuan"] == [] and r["cong_thuc"] == [] and r["nut_an"] == []
    tat = {h["ten"] for h in r["tham_so"] if h["ket_qua"] == "TAT"}
    assert tat == {"InpSL", "InpUseHedging", "InpOrders2Hedging", "InpUseTrailing", "InpUseLottery", "InpUseLottery2"}   # chi cai tac gia KHAI TAT / bi cong tat
    kq = {h["ten"]: h["ket_qua"] for h in r["tham_so"]}
    assert kq["InpLots"] == kq["InpTP"] == kq["InpMaxLots"] == "KHONG_DO_DUOC"
    assert kq["InpMagicID"] == kq["InpShowTP"] == "KHONG_LIEN_QUAN" and kq["InpSomethingNew"] == "KHONG_PHAN_LOAI" and kq["InpStartHour"] == "CHUA_DOI_CHIEU"
    assert _cb(r, "khong co tham so nao KHOP") and _cb(r, "khong co bang lenh")


@pytest.mark.parametrize("khai,sau,mong,do", [("true", 5, "KHOP", 5.0), ("true", 1, "MAU_THUAN", None), ("false", 5, "MAU_THUAN", None),
                                              ("false", 1, "TAT", None), ("false", None, "TAT", None), ("true", None, "KHONG_PHAN_LOAI", None)])
def test_bang_quy_tac_UseDCA_theo_do_sau_chuoi_lon_nhat(khai, sau, mong, do):
    hs = {"phep_do": {"chuoi_sau": {"so_lieu": {"do_sau_lon_nhat": sau}}}} if sau is not None else {}
    r = HS.doi_chieu(hs, "InpUseDCA=%s\n" % khai, c=object(), ten="t")
    h = r["tham_so"][0]
    assert r["loi"] == [] and h["ket_qua"] == mong and h["do"] == do
    if mong == "KHOP":
        assert h["don_vi"] == "lenh" and h["do_tin"] == "cao"


def test_doi_chieu_tep_do_ho_so_roi_dua_ca_bang_lenh_vao_doi_chieu(monkeypatch, gia):
    from nhan import ho_so_bot as HB
    thay = {}

    def chuan_bi(deals, **kw):
        thay["chuan_bi"] = (deals, kw)
        return "BANG_LENH"

    def ho_so(c):
        thay["ho_so"] = c
        return {"mau": {"so_lenh": 3}}

    monkeypatch.setattr(HB, "chuan_bi", chuan_bi)
    monkeypatch.setattr(HB, "ho_so", ho_so)
    gia(_bo_cho({"lots": KHOP}))
    r = HS.doi_chieu_tep("duong_dan", "InpLots=1\n", ma="X", pip=0.1, hop_dong=100, von_dau=5000, khung_phut=15, ten="t")
    assert thay["chuan_bi"] == ("duong_dan", {"ma": "X", "pip": 0.1, "hop_dong": 100, "von_dau": 5000, "khung_phut": 15})
    assert thay["ho_so"] == "BANG_LENH"
    assert not _cb(r, "khong co bang lenh")                              # co bang lenh -> kiem tung lenh, khong con canh bao thieu
    assert r["bo_set"]["ten"] == "t" and r["mau"] == {"so_lenh": 3}


# ---------------------------------------------------------------------------------------------------------------- so_sanh_bo_set
def test_so_sanh_bang_chung_khi_doi_khai_bao_keo_theo_doi_hanh_vi_va_moi_dong_khop():
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", do=10.0, do_tin="cao")), _doi("B", _hang("InpTP", "20", do=20.0, do_tin="vua"))])
    assert [e["tham_so"] for e in r["bang_chung"]] == ["InpTP"]
    assert r["khong_quyet_dinh"] == r["khong_tac_dung"] == r["chua_du"] == []
    e = r["bang_chung"][0]
    assert e["do_tin"] == "vua"                                           # muc THAP nhat trong cac dong
    assert [c["bo"] for c in e["cac_bo"]] == ["A", "B"] and e["cac_bo"][1]["khai"] == "20" and e["cac_bo"][1]["do"] == 20.0
    assert "dieu khien hanh vi do" in e["y_nghia"] and r["bo"] == ["A", "B"]
    json.dumps(r, allow_nan=False)


def test_so_sanh_khai_giong_nhau_ma_hanh_vi_khac_la_khong_quyet_dinh():
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", do=10.0)), _doi("B", _hang("InpTP", "10.0", do=20.0))])      # 10 va 10.0 la CUNG khai bao
    assert [e["tham_so"] for e in r["khong_quyet_dinh"]] == ["InpTP"] and r["bang_chung"] == [] and "yeu to khac" in r["khong_quyet_dinh"][0]["y_nghia"]


def test_so_sanh_khai_khac_hanh_vi_y_het_va_co_dong_khong_khop_la_khong_tac_dung():
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", do=10.0)), _doi("B", _hang("InpTP", "20", MAU_THUAN, do=10.0))])
    assert [e["tham_so"] for e in r["khong_tac_dung"]] == ["InpTP"] and r["bang_chung"] == [] and r["chua_du"] == []


@pytest.mark.parametrize("a,b", [
    (_hang("InpTP", "10", do=10.0), _hang("InpTP", "20", do=10.0)),                       # khai khac, hanh vi y het, nhung moi dong deu KHOP
    (_hang("InpTP", "10", do=10.0), _hang("InpTP", "10", do=10.0)),                       # khong doi gi ca
    (_hang("InpTP", "10", do=10.0), _hang("InpTP", "20", MAU_THUAN, do=30.0)),            # ca hai cung doi nhung co dong khong KHOP
])
def test_so_sanh_con_lai_la_chua_du_kem_ly_do(a, b):
    r = HS.so_sanh_bo_set([_doi("A", a), _doi("B", b)])
    assert [e["tham_so"] for e in r["chua_du"]] == ["InpTP"] and "khong dong deu KHOP" in r["chua_du"][0]["vi_sao"]
    assert r["bang_chung"] == r["khong_quyet_dinh"] == r["khong_tac_dung"] == []


def test_so_sanh_dong_chua_co_so_do_cua_chinh_tham_so_la_chua_du_va_noi_ro_ket_qua():
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", TAT)), _doi("B", _hang("InpTP", "20", HS.CHUA_GAP))])
    assert r["chua_du"][0]["vi_sao"] == "co bo chua co so do cua chinh tham so nay (CHUA_GAP, TAT)"
    r2 = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", KHOP, do=1.0)), _doi("B", _hang("InpTP", "20", HS.KHONG_RO, do=9.0))])      # KHONG_RO van so sanh duoc
    assert [e["tham_so"] for e in r2["chua_du"]] == ["InpTP"] and r2["bang_chung"] == []       # nhung khong phai moi dong KHOP -> khong du bang chung
    assert r2["khong_tac_dung"] == [] and "khong dong deu KHOP" in r2["chua_du"][0]["vi_sao"]


@pytest.mark.parametrize("khai_a,khai_b", [("true", "false"), (True, False), (" TRUE ", "False")])
def test_so_sanh_cong_tac_khong_dem_la_bang_chung_vi_so_do_la_dai_luong_phu(khai_a, khai_b):
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpUseX", khai_a, do=5.0)), _doi("B", _hang("InpUseX", khai_b, do=9.0))])
    assert r["chua_du"][0]["vi_sao"].startswith("la cong tac") and r["bang_chung"] == []


@pytest.mark.parametrize("do_b", [None, True, "9"])
def test_so_sanh_thieu_so_do_dang_so_la_chua_du(do_b):
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", do=10.0)), _doi("B", _hang("InpTP", "20", do=do_b))])
    assert r["chua_du"][0]["vi_sao"] == "thieu so do dang so o it nhat mot bo" and r["bang_chung"] == []


def test_so_sanh_tham_so_chi_co_o_mot_bo_bi_bo_qua_ten_chuan_hoa_bo_Inp_va_giu_ten_bo_dau():
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", do=10.0), _hang("InpRieng", "1", do=1.0)), _doi("B", _hang("TP", "20", do=20.0))])
    assert [e["tham_so"] for e in r["bang_chung"]] == ["InpTP"] and r["chua_du"] == []
    assert "1 tham so co o >= 2 bo" in r["tom_tat"][0]


def test_so_sanh_ba_bo_do_tin_la_muc_thap_nhat_va_tham_so_vang_mat_thi_bo_qua():
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", do=10.0, do_tin="cao")), _doi("B", _hang("InpTP", "20", do=20.0, do_tin="thap")),
                           _doi("C", _hang("InpTP", "30", do=30.0, do_tin="cao")), _doi("D")])
    e = r["bang_chung"][0]
    assert e["do_tin"] == "thap" and [c["bo"] for c in e["cac_bo"]] == ["A", "B", "C"]
    assert r["bo"] == ["A", "B", "C", "D"]
    r2 = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", do=10.0)), _doi("B"), _doi("C", _hang("InpTP", "30", do=30.0))])
    assert [c["bo"] for c in r2["bang_chung"][0]["cac_bo"]] == ["A", "C"]


@pytest.mark.parametrize("do_a,do_b,khac", [(100.0, 102.9, False), (100.0, 103.0, False), (100.0, 103.2, True), (0.0, 0.0, False), (0.0, 1e-12, False),
                                            (0.0, 0.5, True), (-100.0, -103.2, True), (-100.0, -102.9, False)])
def test_so_sanh_dung_sai_tuong_doi_3_phan_tram_theo_gia_tri_lon_nhat(do_a, do_b, khac):
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpTP", "10", do=do_a)), _doi("B", _hang("InpTP", "20", do=do_b))])
    assert bool(r["bang_chung"]) is khac and bool(r["chua_du"]) is (not khac)


def test_so_sanh_dung_sai_do_nguoi_goi_dat():
    ds = [_doi("A", _hang("InpTP", "10", do=100.0)), _doi("B", _hang("InpTP", "20", do=120.0))]
    assert len(HS.so_sanh_bo_set(ds)["bang_chung"]) == 1
    assert len(HS.so_sanh_bo_set(ds, dung_sai=0.5)["chua_du"]) == 1      # 20 <= 0,5 x 120: coi la nhu nhau


@pytest.mark.parametrize("don_vi", ["ty le", "ty le mua"])
def test_so_sanh_don_vi_ty_le_dung_sai_tuyet_doi_0_10(don_vi):
    giong = HS.so_sanh_bo_set([_doi("A", _hang("InpP", "1", do=0.50, don_vi=don_vi)), _doi("B", _hang("InpP", "2", do=0.59, don_vi=don_vi))])
    khac = HS.so_sanh_bo_set([_doi("A", _hang("InpP", "1", do=0.50, don_vi=don_vi)), _doi("B", _hang("InpP", "2", do=0.61, don_vi=don_vi))])
    assert giong["bang_chung"] == [] and len(giong["chua_du"]) == 1 and len(khac["bang_chung"]) == 1
    chat = HS.so_sanh_bo_set([_doi("A", _hang("InpP", "1", do=0.50, don_vi=don_vi)), _doi("B", _hang("InpP", "2", do=0.55, don_vi=don_vi))],
                             dung_sai_ty_le=0.02)
    assert len(chat["bang_chung"]) == 1


def test_so_sanh_don_vi_ty_le_chi_ap_dung_khi_moi_dong_deu_la_ty_le():
    r = HS.so_sanh_bo_set([_doi("A", _hang("InpP", "1", do=0.50, don_vi="ty le")), _doi("B", _hang("InpP", "2", do=0.59, don_vi="pip"))])
    assert len(r["bang_chung"]) == 1                                      # 0,09 > 3% x 0,59 -> theo quy tac tuong doi


def test_so_sanh_khoi_doi_chi_khi_mot_bo_co_va_bo_kia_khong():
    ka = {"k1": {"ket_luan": "co", "ten": None, "tham_so_set": [{"ten": "InpA"}]}, "k2": {"ket_luan": "co", "ten": "K2", "tham_so_set": []},
          "k4": {"ket_luan": "khong_do_duoc", "tham_so_set": []}}
    kb = {"k1": {"ket_luan": "khong", "ten": "Khoi 1", "tham_so_set": []}, "k2": {"ket_luan": "co", "ten": "K2", "tham_so_set": []},
          "k3": {"ket_luan": "co"}, "k4": {"ket_luan": "co"}}
    r = HS.so_sanh_bo_set([("A", {"tham_so": [], "khoi": ka}), ("B", {"tham_so": [], "khoi": kb})])
    assert r["khoi_doi"] == [{"khoi": "k1", "ten": "Khoi 1", "co_o": ["A"], "khong_o": ["B"], "tham_so_theo_bo": {"A": [{"ten": "InpA"}], "B": []}}]
    assert r["tom_tat"][0].endswith("1 khoi co che doi giua cac bo.") and r["tom_tat"][-1].startswith("Khoi co o bo nay khong o bo kia: k1 (co o A)")


def test_so_sanh_ten_bo_la_chuoi_va_ket_qua_trong_khong_co_loi():
    r = HS.so_sanh_bo_set([(1, {"tham_so": []}), (2, {})])
    assert r["bo"] == ["1", "2"] and r["tom_tat"] == ["2 bo .set; 0 tham so co o >= 2 bo: bang chung 0, khong quyet dinh 0, khong tac dung 0, chua du 0; "
                                                   "0 khoi co che doi giua cac bo."]
    assert HS.so_sanh_bo_set([])["tom_tat"][0].startswith("0 bo .set; 0 tham so")


def test_so_sanh_tom_tat_liet_ke_toi_da_8_tham_so_moi_loai_va_khong_qua_8_dong():
    a = [_hang("InpP%d" % i, "1", do=10.0) for i in range(10)]
    b = [_hang("InpP%d" % i, "2", do=20.0) for i in range(10)]
    r = HS.so_sanh_bo_set([_doi("A", *a), _doi("B", *b)])
    assert len(r["bang_chung"]) == 10
    dong = next(l for l in r["tom_tat"] if l.startswith("Bang chung"))
    assert dong.count("tin cay") == 8 and "InpP7" in dong and "InpP8" not in dong and len(r["tom_tat"]) <= 8
    assert r["tom_tat"][0] == "2 bo .set; 10 tham so co o >= 2 bo: bang chung 10, khong quyet dinh 0, khong tac dung 0, chua du 0; 0 khoi co che doi giua cac bo."


# ---------------------------------------------------------------------------------------------------------------- bao_cao_md
def _r_md():
    return {"bo_set": {"ten": "bo_Đồng", "n": 2, "sha": "x"}, "tom_tat": ["Dong 1 co dấu: Đặt lệnh"], "canh_bao": ["a | b"],
            "loi": ["lỗi"],
            "mau_thuan": [{"ten": "InpA", "khai": "6|0", "do": 1, "do_tin": "cao", "khoi": "k", "ly_do": "tác giả nói X | thật Y"}],
            "nut_an": [{"khoi": "kn", "ten": "Nút ẩn", "do_tin": "vua", "ly_do": "lý do",
                        "tham_so_lien_quan": [{"ten": "InpB", "khai": "1", "ket_qua": "TAT"}]},
                       {"khoi": "k2", "ten": None, "do_tin": "thap", "ly_do": "", "tham_so_lien_quan": []}],
            "cong_thuc": [{"khoi": "kc", "ten": "Công thức", "do_tin": "cao",
                           "tham_so_do": {"lot": {"gia_tri": 0.01, "don_vi": "lot"}, "txt": {"gia_tri": "abc", "don_vi": ""}},
                           "tham_so_set": [{"ten": "InpL", "khai": "0.01", "ket_qua": "KHOP"}, {"ten": "InpM", "khai": "5", "ket_qua": "TAT"}]}],
            "kiem_lot": {"khop": 9, "tong": 10, "cong_thuc": "f", "n_sau_nhat": 4},
            "tham_so": [{"ten": "InpA", "khai": "6|0", "ket_qua": "MAU_THUAN", "do_tin": "cao", "do": 2.5, "don_vi": "pip", "ly_do": "lý do dài"},
                        {"ten": "InpB", "khai": "1", "ket_qua": "TAT", "do_tin": "vua", "do": None, "don_vi": "", "ly_do": ""}],
            "dem": {"MAU_THUAN": 1, "TAT": 1, "KHOP": 0}}


def test_bao_cao_md_luon_ascii_bo_dau_va_dau_gach_dung_trong_o_bang():
    md = HS.bao_cao_md(_r_md())
    assert md.isascii()
    assert md.splitlines()[0] == "# Doi chieu bo .set 'bo_Dong' voi lenh that"
    assert "- Dong 1 co dau: Dat lenh" in md and "## Luu y\n- a / b" in md and "## Loi (bo doi chieu hong)\n- loi" in md
    assert "| InpA | 6/0 | cao | tac gia noi X / that Y |" in md                    # '|' trong noi dung doi thanh '/', khong vo bang
    assert "- **Nut an** (kn, do tin vua): ly do. Tham so lien quan: InpB=1 (TAT)" in md
    assert "- **k2** (k2, do tin thap): . Tham so lien quan: khong co tham so nao noi toi" in md
    assert "- **Cong thuc** (kc, do tin cao): do duoc [lot=0.01 lot, txt=abc]; .set khop [InpL=0.01]" in md
    assert "Lot: 9/10 lenh dung cong thuc f (chuoi sau nhat 4 lenh)." in md
    assert "| InpA | 6/0 | MAU_THUAN | cao | 2.5 pip | ly do dai |" in md and "| InpB | 1 | TAT | vua |  |  |" in md
    assert md.splitlines()[-1] == "Dem: MAU_THUAN 1, TAT 1"                         # ket qua = 0 (KHOP) khong liet ke
    so_cot = None
    for dong in md.splitlines():                                         # moi hang bang phai co dung so cot cua dong tieu de ngay tren no
        if dong.startswith("| Tham so"):
            so_cot = dong.count("|")
        elif dong.startswith("| Inp"):
            assert dong.count("|") == so_cot, dong
    assert so_cot == 7


def test_bao_cao_md_cat_bang_tham_so_o_toi_da_dong():
    md = HS.bao_cao_md(_r_md(), toi_da_dong=1)
    assert "| InpA | 6/0 | MAU_THUAN" in md and "| InpB | 1 | TAT" not in md


def test_bao_cao_md_ho_so_trong_van_ra_du_muc_va_ghi_khong_co():
    md = HS.bao_cao_md({})
    assert md.splitlines()[0] == "# Doi chieu bo .set '?' voi lenh that"
    assert md.count("(khong co)") == 2 and "## Tung tham so (theo thu tu trong .set)" in md and "Luu y" not in md and "## Loi" not in md


# ---------------------------------------------------------------------------------------------------------------- main
def _r_main(loi=()):
    return {"bo_set": {"ten": "t"}, "tom_tat": ["dong 1", "dong 2"], "loi": list(loi), "mau_thuan": [], "nut_an": [], "cong_thuc": [], "canh_bao": [],
            "dem": {"KHOP": 1},
            "tham_so": [{"ten": "InpLots", "khai": "0.01", "ket_qua": "KHOP", "do_tin": "cao", "ly_do": "lot dung", "do": 0.01, "don_vi": "lot"}]}


def test_main_chuyen_het_doi_so_vao_doi_chieu_tep_in_tom_tat_va_tung_tham_so(monkeypatch, capsys):
    thay = {}

    def gia_tep(deals, bo_set, **kw):
        thay.update(deals=deals, bo_set=bo_set, **kw)
        return _r_main()

    monkeypatch.setattr(HS, "doi_chieu_tep", gia_tep)
    rc = HS.main(["d.csv", "b.set", "--ma", "GOLD.i#", "--pip", "0.1", "--hop-dong", "100", "--von", "10000", "--khung-phut", "5", "--he-so-don-vi", "10"])
    assert rc == 0
    assert thay == {"deals": "d.csv", "bo_set": "b.set", "ma": "GOLD.i#", "pip": 0.1, "hop_dong": 100.0, "von_dau": 10000.0, "khung_phut": 5.0,
                    "he_so_don_vi": 10.0}
    out = capsys.readouterr().out.splitlines()
    assert out[:2] == ["dong 1", "dong 2"] and out[2].startswith("InpLots") and "KHOP" in out[2] and "lot dung" in out[2]
    HS.main(["d.csv", "b.set"])
    assert all(thay[k] is None for k in ("ma", "pip", "hop_dong", "von_dau", "khung_phut", "he_so_don_vi"))


def test_main_gon_chi_in_tom_tat(monkeypatch, capsys):
    monkeypatch.setattr(HS, "doi_chieu_tep", lambda *a, **k: _r_main())
    assert HS.main(["d.csv", "b.set", "--gon"]) == 0
    assert capsys.readouterr().out.splitlines() == ["dong 1", "dong 2"]


def test_main_tra_1_khi_co_bo_doi_chieu_hong(monkeypatch, capsys):
    monkeypatch.setattr(HS, "doi_chieu_tep", lambda *a, **k: _r_main(loi=["bo_x: KeyError: 'k' (dong 3)"]))
    assert HS.main(["d.csv", "b.set", "--gon"]) == 1


def test_main_ghi_json_va_bao_cao_md_ascii(monkeypatch, tmp_path, capsys):
    r = _r_main()
    r["tom_tat"] = ["có dấu"]
    monkeypatch.setattr(HS, "doi_chieu_tep", lambda *a, **k: r)
    j, m = tmp_path / "ra.json", tmp_path / "ra.md"
    assert HS.main(["d.csv", "b.set", "--gon", "--json", str(j), "--md", str(m)]) == 0
    assert json.loads(j.read_text(encoding="utf-8")) == r
    md = m.read_text(encoding="utf-8")
    assert md.isascii() and "- co dau" in md and md.startswith("# Doi chieu bo .set 't' voi lenh that")


# ---------------------------------------------------------------------------------------------------------------- lan chay THAT (cham)
@pytest.fixture(scope="module")
def vamge():
    """CCBSN VamGe v3.05 tren GOLD.i#: 3114 lenh tester that + bo .set cua tac gia (190 tham so). Chay MOT lan cho ca module (~20 giay)."""
    deals, bo_set = _FIX / "tester_vamge10k_kp_deals.csv.gz", _FIX / "ccbsn305_vamge10k.set.txt"
    if not (deals.exists() and bo_set.exists()):
        pytest.skip("thieu reports/fixture/ (VamGe)")
    return HS.doi_chieu_tep(str(deals), str(bo_set), ma="GOLD.i#")


@pytest.mark.cham
def test_vamge_that_dem_ket_qua_khong_loi_va_moi_khoa_mot_dong(vamge):
    r = vamge
    assert r["loi"] == []
    assert r["dem"] == {"KHOP": 20, "MAU_THUAN": 4, "TAT": 82, "BI_CHE": 1, "CHUA_GAP": 10, "KHONG_DO_DUOC": 59, "KHONG_RO": 7, "CHUA_DOI_CHIEU": 0,
                        "KHONG_PHAN_LOAI": 0, "KHONG_LIEN_QUAN": 7, "tong": 190}
    khoa = HS.doc_set(str(_FIX / "ccbsn305_vamge10k.set.txt"))["khoa"]
    assert [h["ten"] for h in r["tham_so"]] == list(khoa) and len(khoa) == 190                # dung thu tu .set, khong sot khong thua
    assert r["bo_set"] == {"ten": "ccbsn305_vamge10k", "n": 190, "sha": "c74896b6e9cf542c"}
    assert r["mau"]["so_lenh"] == 3114 and r["mau"]["ma"] == "GOLD.i#" and r["mau"]["tick_s"] == 10.0 and r["mau"]["so_chuoi"] == 1198
    assert len(r["canh_bao"]) == 1 and "luoi 10 giay" in r["canh_bao"][0]                  # chi canh bao do chinh xac thoi gian cua tester
    json.dumps(r, allow_nan=False)


@pytest.mark.cham
def test_vamge_that_cong_thuc_lot_khop_ca_3114_lenh_va_don_vi_1_chac(vamge):
    kl = vamge["kiem_lot"]
    assert kl["khop"] == kl["tong"] == 3114 and kl["ty"] == 1.0 and kl["n_sau_nhat"] == 25 and kl["lech_mau"] == [] and kl["doi_he_so"] is True
    assert kl["cong_thuc"] == "lot_n = lam_tron(0.01 x M(n)^(n-1), 0.01)"
    assert vamge["don_vi"]["he_so"] == 1.0 and vamge["don_vi"]["chac"] is True


@pytest.mark.cham
def test_vamge_that_cac_tham_so_khop_va_do_tin(vamge):
    mong = [("InpLots", "cao"), ("InpTP", "cao"), ("InpUseDCA", "cao"), ("InpMultiplier", "cao"), ("InpUseChangeMultiplier", "cao"),
            ("InpOrders2NewMultiplier", "cao"), ("InpNewMultiplier", "cao"), ("InpOrders2NewMultiplier2", "thap"), ("InpNewMultiplier2", "thap"),
            ("InpDistance0", "cao"), ("InpTPDCA", "cao"), ("InpOrders2Distance1", "cao"), ("InpDistance1", "cao"), ("InpDistance2", "cao"),
            ("InpDistance3", "thap"), ("InpUseHedging", "vua"), ("InpOrders2Hedging", "vua"), ("InpUseLotsDCA2Hedging", "vua"),
            ("InpInitialSLTrailing", "thap"), ("InpTFSignal", "cao")]
    assert [(h["ten"], h["do_tin"]) for h in vamge["tham_so"] if h["ket_qua"] == "KHOP"] == mong
    cao = {h["ten"]: h for h in vamge["tham_so"]}
    assert cao["InpTP"]["do"] == 10.1 and cao["InpTP"]["don_vi"] == "pip" and cao["InpUseDCA"]["do"] == 25.0 and cao["InpUseDCA"]["don_vi"] == "lenh"


@pytest.mark.cham
def test_vamge_that_mau_thuan_va_nut_an(vamge):
    assert [(m["ten"], m["khai"], m["do_tin"], m["khoi"]) for m in vamge["mau_thuan"]] == [
        ("InpMinuteDelayAfterClose", "60", "cao", "loc_gio_giao_dich"), ("InpPlus", "0.01", "vua", "lot_cong"),
        ("InpDistanceMulti", "1.2", "thap", "luoi_buoc_gian_dan"), ("InpMinuteDelayNewDay", "120", "vua", "loc_gio_giao_dich")]
    assert [n["khoi"] for n in vamge["nut_an"]] == ["luoi_theo_nen_moi"]
    assert [(k["khoi"], k["co_khop"]) for k in vamge["cong_thuc"]] == [("luoi_buoc_theo_bac", True), ("luoi_theo_nen_moi", False),
                                                                       ("lenh_doi_ung_sau_n_lenh", True), ("lot_nhan_theo_bac", True),
                                                                       ("tp_chuoi_tu_gia_tb", True)]
    # 4 mau thuan / 24 tham so da quyet dinh = 17% < 40%: bo .set dung la bo da chay -> khong co canh bao 'sai bo .set'
    assert not _cb(vamge, "MAU THUAN chiem")


@pytest.mark.cham
def test_vamge_that_tom_tat_bao_cao_ascii_va_so_sanh_voi_chinh_no_khong_chung_minh_gi(vamge):
    t = vamge["tom_tat"]
    assert t[0].startswith("Bo .set 'ccbsn305_vamge10k' (190 tham so) doi chieu voi 3114 lenh that cua GOLD.i#: KHOP 20, MAU THUAN 4, TAT 82")
    assert t[3] == "Lot: 3114/3114 lenh dung cong thuc lot_n = lam_tron(0.01 x M(n)^(n-1), 0.01)." and len(t) <= 8
    md = HS.bao_cao_md(vamge)
    assert md.isascii() and len(md.splitlines()) > 190
    r = HS.so_sanh_bo_set([("A", vamge), ("B", vamge)])
    assert r["bang_chung"] == r["khong_quyet_dinh"] == r["khong_tac_dung"] == [] and r["khoi_doi"] == []         # cung bo, cung hanh vi: khong chung minh gi
    assert len(r["chua_du"]) == 190


@pytest.mark.cham
def test_vamge_that_doi_mot_tham_so_thi_so_sanh_thay_bang_chung(vamge):
    import copy
    b = copy.deepcopy(vamge)
    for h in b["tham_so"]:
        if h["ten"] == "InpTP":
            h["khai"], h["do"] = "20.0", 20.1
    r = HS.so_sanh_bo_set([("goc", vamge), ("doi_TP", b)])
    assert [e["tham_so"] for e in r["bang_chung"]] == ["InpTP"] and r["bang_chung"][0]["do_tin"] == "cao"
    assert r["khong_quyet_dinh"] == r["khong_tac_dung"] == [] and len(r["chua_du"]) == 189
