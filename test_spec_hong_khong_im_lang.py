# -*- coding: utf-8 -*-
"""Test: SPEC HONG khong duoc bien mat trong im lang.

## Chuyen da xay ra, 14/09/2026

Toi them 5 spec DSL vao kho voi `ho = "hoi_quy"` - mot ten khong thuoc danh sach
ho hop le. Ket qua:

  - `luu_kho` nhan het, khong mot loi nao.
  - `chay_tester_kho` loc chung ra va in `kho 0 -> dich duoc 1`.
  - Neu khong tinh co dem lai so co che, toi da chay tester tren **mot he** roi
    tuong do la ket qua cua ca **ba he** dang o lan nhanh.

Va do khong phai ca le: do lai thi **44/3233 co che trong kho** dang hong va bi
vut moi luot chay tester, suot nhieu ngay, khong ai biet.

Cung ho loi voi moi thu bat duoc trong ngay: **he im lang khi sai**. Bo test nay
giu cho hai cai mieng vua mo ra khong bi bit lai.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import ngu_phap as NP   # noqa: E402


def spec_tot(ten: str = "thu_tot") -> dict:
    return {
        "ten": ten,
        "ho": "quay_ve_trung_binh",
        "chieu": 1,
        "giu": 1,
        "co_che": ("Ban qua da ngan han thi ap luc mua quay lai, nen vao khi RSI "
                   "xuong duoi 30 va thoat khi no hoi len tren 55."),
        "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<",
                 "phai": {"hang": 30.0}}],
        "ra": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": ">",
                "phai": {"hang": 55.0}}],
    }


# ------------------------------------------------- CONG NGU PHAP CON SONG
def test_spec_tot_qua_duoc_cong():
    """Chieu nguoc: cong tu choi TAT CA thi so lieu y het mot cong tot."""
    assert NP.kiem_khai_bao(spec_tot()) == []


def test_ho_khong_hop_le_bi_tu_choi():
    """Dung cai da sap 14/09: `ho = "hoi_quy"` khong thuoc danh sach ho."""
    xau = {**spec_tot(), "ho": "hoi_quy"}
    loi = NP.kiem_khai_bao(xau)
    assert loi and "ho" in loi[0]


def test_thieu_co_che_bi_tu_choi():
    """37/44 spec hong trong kho la vi thieu truong nay."""
    xau = {k: v for k, v in spec_tot().items() if k != "co_che"}
    assert NP.kiem_khai_bao(xau)


def test_zscore_thieu_ve_cua_thi_KHONG_sinh_duoc():
    """Cai bay thu hai cua 14/09: `zscore` khong noi tinh tren gia nao.

    Cho nay ngu phap NEM LOI (tot) chu khong tra ve mang 0 - nhung ghi lai de
    neu ai do "sua cho no khoi nem" thi test nay do.
    """
    import numpy as np
    import pandas as pd
    df = pd.DataFrame({"open": np.arange(100.0, 200.0),
                       "high": np.arange(100.5, 200.5),
                       "low": np.arange(99.5, 199.5),
                       "close": np.arange(100.0, 200.0)},
                      index=pd.date_range("2020-01-01", periods=100, freq="h"))
    thieu = {**spec_tot(),
             "vao": [{"trai": {"chi_bao": "zscore", "n": 20}, "phep": "<",
                      "phai": {"hang": -2.0}}]}
    with pytest.raises(Exception):
        NP.sinh_tu_spec(thieu, df)


def test_zscore_CO_ve_cua_thi_sinh_duoc():
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(3)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300)))
    df = pd.DataFrame({"open": c, "high": c * 1.001, "low": c * 0.999, "close": c},
                      index=pd.date_range("2020-01-01", periods=300, freq="h"))
    du = {**spec_tot(),
          "vao": [{"trai": {"chi_bao": "zscore",
                            "cua": {"chi_bao": "gia", "cot": "close"}, "n": 20},
                   "phep": "<", "phai": {"hang": -1.0}}],
          "ra": []}
    th = np.asarray(NP.sinh_tu_spec(du, df), float)
    assert len(th) == len(df)
    assert np.sum(np.abs(th) > 0) > 0


# ------------------------------------- LUU_KHO PHAI KEU KHI NHAN SPEC HONG
def test_luu_kho_KEU_khi_co_spec_hong(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(NP, "KHO_CO_CHE", tmp_path / "kho.json")
    monkeypatch.setattr(NP, "_doc_moc_cao", lambda: 0)
    monkeypatch.setattr(NP, "_ghi_moc_cao", lambda n: None)
    ds = [spec_tot("a"), {**spec_tot("b_hong"), "ho": "hoi_quy"}]
    NP.luu_kho(ds, ep=True)
    err = capsys.readouterr().err
    assert "CANH BAO" in err
    assert "b_hong" in err
    assert "1/2" in err


def test_luu_kho_IM_LANG_khi_moi_spec_deu_tot(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(NP, "KHO_CO_CHE", tmp_path / "kho.json")
    monkeypatch.setattr(NP, "_doc_moc_cao", lambda: 0)
    monkeypatch.setattr(NP, "_ghi_moc_cao", lambda n: None)
    NP.luu_kho([spec_tot("a"), spec_tot("b")], ep=True)
    assert "CANH BAO" not in capsys.readouterr().err


def test_luu_kho_VAN_GHI_du_co_spec_hong(tmp_path, monkeypatch):
    """Keu to, nhung KHONG tu choi ghi.

    Kho dang co 44 cai hong tu truoc; tu choi ghi la lam do ca nhung duong ghi
    hop le khac - va do la cach bien mot canh bao thanh mot su co.
    """
    monkeypatch.setattr(NP, "KHO_CO_CHE", tmp_path / "kho.json")
    monkeypatch.setattr(NP, "_doc_moc_cao", lambda: 0)
    monkeypatch.setattr(NP, "_ghi_moc_cao", lambda n: None)
    NP.luu_kho([spec_tot("a"), {**spec_tot("b_hong"), "ho": "hoi_quy"}], ep=True)
    ds = json.loads((tmp_path / "kho.json").read_text(encoding="utf-8"))
    assert len(ds) == 2


# -------------------------------- TESTER PHAI NOI RO NO BO CAI NAO VA VI SAO
def test_chay_tester_kho_co_in_ly_do_bo():
    """Bo quet ma nguon: doan loc phai in ra ly do, khong chi in con so cuoi."""
    s = (LAB / "chay_tester_kho.py").read_text(encoding="utf-8-sig")
    assert "BI BO vi khai bao hong" in s, "tester khong con bao ly do bo co che"
    assert "KHOP BO LOC" in s, "tester khong con bao co che bi bo NAM TRONG bo loc"
    assert "khong dich duoc" in s, "tester khong con liet ke co che khong dich duoc"


# ============ TESTER: "0 lenh" khong duoc tra ve tro troi
def test_tester_co_ham_chan_doan_log():
    """MT5 bao '0 lenh' cho MOI kieu hong. Phai doc log moi biet ly do that."""
    import chay_tester_kho as C
    assert hasattr(C, "chan_doan_log")
    manh = [m for m, _ in C.DAU_HIEU_HONG]
    for can in ("authorization on", "not synchronized with",
                "cannot synchronize history", "unknown symbol"):
        assert can in manh, f"thieu dau hieu '{can}'"


def test_tester_coi_TAT_CA_0_LENH_la_CHUA_DO_DUOC():
    """Ba trang thai chu khong phai hai: moi co che 0 lenh la hong MOI TRUONG.

    Do 14/09: hai luot x 628 giay, 6/6 co che 0 lenh KE CA moc mua-giu, va ly do
    that (`authorization ... Invalid account`) chi nam trong log terminal.
    """
    s = (LAB / "chay_tester_kho.py").read_text(encoding="utf-8-sig")
    assert 'all(int(d.get("lenh") or 0) == 0 for d in ket)' in s
    assert '"chua_do": True' in s
    assert "hong MOI TRUONG" in s


def test_tester_ini_dung_KHUNG_duoc_truyen_vao():
    """`--khung H4` phai vao `.ini`, khong bi hang so `KHUNG_CHAY` de len.

    Do 14/09: truyen `--khung H4` nhung log MT5 ghi `on AUDCAD,H1` - he H4 bi do
    tren H1 ma khong ai biet.
    """
    s = (LAB / "chay_tester_kho.py").read_text(encoding="utf-8-sig")
    assert "Period={khung or KHUNG_CHAY}" in s
    assert "khung=khung" in s, "viet_ini khong nhan `khung` tu nguoi goi"


# ====== BO DICH MQL5 PHAI GIU DUNG DAU CUA `than_nen`
def test_than_nen_dich_sang_mq5_phai_CO_DAU():
    """14/09/2026: `_cb_than_nen` boc `MathAbs` con `ngu_phap` thi khong.

    Hau qua: `mat_can_bang_lenh_dong_cua` co dieu kien `than_nen < 0` (nen
    giam). `MathAbs(...) < 0` khong bao gio dung -> EA chay du 5,4 nam tren
    EURGBPmicro H4, ghi du bao cao, ra **0 lenh**, khong mot dong loi. Ban
    Python cua cung co che ban 98 tin hieu tren cung cua so do.

    56/3189 co che hop le trong kho dung `than_nen` tran - tat ca deu dinh.
    """
    s = (LAB / "nhan" / "dich_mq5.py").read_text(encoding="utf-8-sig")
    i = s.index("def _cb_than_nen")
    than = s[i:i + 1600]
    j = than.index("return self._than")
    assert "MathAbs" not in than[j:j + 200], (
        "than_nen dich sang MQL5 dang MAT DAU - `than_nen < 0` khong bao gio dung")


def test_than_nen_python_la_close_tru_open_co_dau():
    """Chieu nguoc: neu ban Python doi sang tri tuyet doi thi test tren vo nghia."""
    import numpy as np
    import pandas as pd
    df = pd.DataFrame({"open": [10.0, 10.0], "high": [11.0, 11.0],
                       "low": [9.0, 9.0], "close": [9.5, 10.5]},
                      index=pd.date_range("2020-01-01", periods=2, freq="h"))
    v = np.asarray(NP._toan_hang_tinh(df, {"chi_bao": "than_nen"}), float)
    assert v[0] < 0 and v[1] > 0, "than_nen ban Python phai CO DAU"


# ============ TEN MA: cong CO ma khong nam tren duong chay (15/09/2026)
def test_dau_hieu_hong_khop_voi_cai_MT5_that_su_in():
    """Bang dau hieu phai bat duoc HAI dong MT5 that su in khi sai ten ma.

    15/09/2026: `--ma AUDCAD` dot mot luot boot terminal roi tra ve "khong thay
    bang ket qua" tro troi. Log MT5 noi thang:
        `Tester  cannot select symbol in market watch`
        `Tester  symbol AUDCAD not exist`
    `DAU_HIEU_HONG` luc do co `unknown symbol` - khong khop mot ky tu nao voi
    hai dong do. Mot bo do khong thay duoc cai chac chan CO thi khong phai bo do.
    """
    import chay_tester_kho as C
    manh = [m.lower() for m, _ in C.DAU_HIEU_HONG]
    for dong in ("Tester  cannot select symbol in market watch",
                 "Tester  symbol AUDCAD not exist"):
        assert any(m in dong.lower() for m in manh), (
            "khong dau hieu nao bat duoc dong log THAT: %r" % dong)


def test_nhanh_khong_thay_bang_ket_qua_phai_CHAN_DOAN():
    """Nhanh nay tung la nhanh DUY NHAT khong goi `chan_doan_log`."""
    s = (LAB / "chay_tester_kho.py").read_text(encoding="utf-8-sig")
    i = s.index('return {"loi": "khong thay bang ket qua"')
    khoi = s[i:i + 400]
    assert "chan_doan" in khoi, "khong thay bang ket qua ma khong chan doan gi"
    assert "goi_y_ma" in khoi, "khong goi y ten ma gan dung"


def test_tester_kiem_ten_ma_TRUOC_khi_boot_terminal():
    """Cong kiem ten ma phai nam tren duong chay CHINH, khong chi o bench."""
    s = (LAB / "chay_tester_kho.py").read_text(encoding="utf-8-sig")
    i = s.index("def _chay_trong_khoa")
    j = s.index("dong_terminal()", i)
    assert "ten_ma" in s[i:j], (
        "chay_tester_kho khong kiem ten ma truoc khi boot terminal")


def test_ten_ma_cham_theo_MAY_CHU_dang_dung_khong_gop_bases():
    """Kho lich su cua mot tai khoan DA CHET khong duoc tra loi thay may chu song.

    `AUDCAD` chi ton tai duoi `bases/XMGlobal-MT5 17` (tai khoan hong tu 14/09);
    may chu dang dung la `XMGlobal-MT5 10` va chi co `AUDCADmicro`. Ban cu gop
    het `bases/*/history/*` nen tra loi "co" - va luot tester di toi cung roi
    chet.
    """
    from nhan import ten_ma as TM
    d = Path(__import__("tempfile").mkdtemp())
    (d / "config").mkdir()
    (d / "config" / "common.ini").write_text(
        "[Common]\nLogin=1\nServer=MAY CHU SONG\n", encoding="utf-8")
    for sv, ma in (("MAY CHU SONG", ["AUDCADmicro"]), ("MAY CHU CHET", ["AUDCAD"])):
        (d / "bases" / sv / "history" / ma[0]).mkdir(parents=True)
    assert TM.may_chu(d) == "MAY CHU SONG"
    assert TM.ma_co_lich_su(xm_data=d) == ["AUDCADmicro"], (
        "ma_co_lich_su dang gop ca base cua may chu da chet")
    k = TM.kiem_ten("AUDCAD", xm_data=d)
    assert k["trang_thai"] == "NGHI_NGO"
    assert k["o_may_chu_khac"] == ["MAY CHU CHET"]
    assert "AUDCADmicro" in k["goi_y"], "khong goi y duoc duoi `micro`"
    assert TM.canh_bao("AUDCAD", xm_data=d), "khong in canh bao nao"
    assert not TM.canh_bao("AUDCADmicro", xm_data=d), "canh bao oan ma dung"


def test_bench_quan_tri_dung_CHUNG_cong_ten_ma_voi_tester():
    """Hai duong chay khong duoc co hai ban kiem ten ma khac nhau."""
    s = (LAB / "chay_bench_quan_tri.py").read_text(encoding="utf-8-sig")
    i = s.index("def co_lich_su")
    assert "ten_ma" in s[i:i + 1600], (
        "chay_bench_quan_tri van giu ban kiem ten ma rieng")
