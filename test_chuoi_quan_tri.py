# -*- coding: utf-8 -*-
"""test_chuoi_quan_tri.py - Chuoi quan tri vi the co chay dau-cuoi khong.

So do he thong goi quan tri vi the la *"module quan trong trong toan bo he
thong"*. Ba manh lam viec do (`quan_tri_dsl` · `dich_mq5_qtvt` · `de_quan_tri`)
deu MO COI cho toi 12/09 - ban do sinh tu ma nguon tim ra.

Hai dieu phai chan bang test:

  * **Khau `sang_atr` khong duoc bo qua.** Bo no thi 6/75 khai bao dich duoc;
    goi no thi 49/75. Con so 6 khong phai su that ve kho, no la su that ve mot
    khau bi thieu ([[luat-do-phai-thay-duoc-cai-co]]).
  * **Cong an toan phai con nguyen.** 26 khai bao bi tu choi vi 'nhoi khong
    tran' - do la cong thuc chay tai khoan ([[lottery-mode-session-v3]]: nhan
    lot sau moi lan thua bien +54.354 thanh -1.550 voi DD 94,4%). Mot ban "sua"
    lam chung dich duoc la mot ban LAM HONG.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import pytest                                  # noqa: E402

from nhan import chuoi_quan_tri as CQ          # noqa: E402
from nhan import dich_mq5_qtvt as DQ           # noqa: E402
from nhan import quan_tri_dsl as QD            # noqa: E402


def test_kho_co_khai_bao():
    ds = CQ.kho(in_ra=None)
    assert len(ds) >= 50
    assert all(x.get("ho") == "quan_tri" for x in ds)


def test_sang_atr_la_khau_bat_buoc():
    """Khong quy ATR thi PHAN LON khai bao khong dich duoc - do la khau thieu.

    Phep thu nay giu lai chinh con so da do: 6 khi bo khau, 49 khi co khau.
    Neu ai do bo `sang_atr` khoi chuoi thi test nay do.
    """
    ds = CQ.kho(in_ra=None)
    khong_quy = sum(1 for x in ds if _dich_duoc(x, quy=False))
    co_quy = sum(1 for x in ds if _dich_duoc(x, quy=True))
    assert co_quy > khong_quy * 3, (
        "quy ATR phai mo them nhieu khai bao (do duoc 6 -> 49); "
        "nay %d -> %d" % (khong_quy, co_quy))


def _dich_duoc(spec: dict, quy: bool) -> bool:
    try:
        s = QD.sang_atr(spec, 74.24, 0.1) if quy else spec
        DQ.sinh_khoi(s, khung="D1")
        return True
    except Exception:
        return False


def test_nhoi_khong_tran_van_bi_tu_choi():
    """Cong an toan: nhoi lenh ma khong co tran = cong thuc chay tai khoan."""
    spec = {"ten": "thu", "ho": "quan_tri", "lop": "ro",
            "dau_hieu": ["martingale"],
            "nhoi": {"he_so": 2.0}}
    with pytest.raises(Exception) as e:
        DQ.sinh_khoi(QD.sang_atr(spec, 74.24, 0.1), khung="D1")
    assert "tran" in str(e.value).lower()


def test_dich_het_dem_duoc_va_neu_ly_do():
    k = CQ.dich_het(in_ra=None)
    assert k["tong"] >= 50
    assert len(k["dich_duoc"]) >= 30
    # Moi ly do tu choi phai la mot cau doc duoc, khong phai ma loi tran
    for ly in k["tu_choi"]:
        assert len(ly) > 10 and "Traceback" not in ly


def test_cap_doi_chieu_sinh_HAI_file(tmp_path):
    """Phai sinh CAP - mot ban sua de len ban goc thi het doi chieu duoc."""
    ea = tmp_path / "EAthu.mq5"
    ea.write_text("#property copyright \"x\"\n"
                  "void OnTick()\n{\n   int a=1;\n}\n", encoding="utf-8")
    i = CQ.dich_het(in_ra=None)["dich_duoc"][0]
    k = CQ.cap_doi_chieu(str(ea), i, in_ra=None)
    assert Path(k["goc"]).exists() and Path(k["co_quan_tri"]).exists()
    assert k["goc"] != k["co_quan_tri"]
    assert k["them_dong"] > 20
    # ban GOC phai giu nguyen tung byte
    assert Path(k["goc"]).read_text(encoding="utf-8") == \
        ea.read_text(encoding="utf-8")


def test_chuoi_nam_tren_duong_chay():
    """Ca ba manh phai voi toi duoc tu mot cua vao - do la ly do file nay ra doi."""
    from nhan import ban_do as BD
    toi, _ = BD.voi_toi_duoc()
    for t in ("nhan/chuoi_quan_tri.py", "nhan/quan_tri_dsl.py",
              "nhan/dich_mq5_qtvt.py", "nhan/de_quan_tri.py"):
        assert t in toi, "%s van mo coi" % t


# =========================================================== CONG (1) + (2)
# `sinh_khoi_nhieu` sinh BANG nhieu luat trong MOT EA (dung boi `de_quan_tri.
# chen_tu_spec` va `_de_qt_ea_ngoai.py`). Loi 11/09: goi ham nay voi cac spec
# CHUA quy ve ATR (`_atr0` cu tra 0.0 lang le cho moi dict khac `{'atr': x}`)
# lam ca 14 luat sinh ra GIONG HET nhau (1759 lenh / -108,76 / DD 1,3121), va
# bang do bi doc nham thanh ket luan "AM" thay vi mot loi ky thuat.
ATR_THAT, GIA_DIEM_THAT = 74.24, 0.1   # da do tren US500CASH D1 (dong tren)


def test_sinh_khoi_nhieu_tu_kho_that_KHONG_toan_0():
    """Kho THAT (75 khai bao, loc qua cong), quy ATR that -> bang PHAI KHAC
    NHAU giua cac luat. Day la doi chung voi bang hong ngay 11/09."""
    ds = [c for c in QD.doc_kho() if not QD.kiem_khai_bao(c)][:14]
    assert len(ds) >= 10
    _, luat = DQ.sinh_khoi_nhieu(ds, khung="D1", magic=0,
                                 atr=ATR_THAT, gia_diem=GIA_DIEM_THAT)
    assert len(luat) >= 10
    gia_tri = {ten: [lay(x) for x in luat] for ten, lay, _ in DQ._COT_BANG_NHIEU}
    hang = [tuple(gia_tri[c][i] for c in gia_tri) for i in range(1, len(luat))]
    assert len(set(hang)) > 1, (
        "moi luat cho CUNG mot bo tham so - dung lai dang bug 11/09")
    assert not all(not any(h) for h in hang), "ca bang toan 0"


def test_sinh_khoi_nhieu_thieu_atr_bi_tu_choi():
    """Cong (1): khong duoc doan/mac dinh atr - phai NEM LOI ngay."""
    specs = [{"ten": "a", "dat_hue": {"tu": {"pip": 10}}}]
    with pytest.raises(DQ.KhongDichDuoc):
        DQ.sinh_khoi_nhieu(specs, khung="D1")
    with pytest.raises(DQ.KhongDichDuoc):
        DQ.sinh_khoi_nhieu(specs, khung="D1", atr=0)
    with pytest.raises(DQ.KhongDichDuoc):
        DQ.sinh_khoi_nhieu(specs, khung="D1", atr=-5)


def test_sinh_khoi_nhieu_mot_luat_toan_0_bi_tu_choi():
    """Cong (2): mot luat (khac luat 0 - moc) khong co tham so kich hoat nao
    khac 0 -> tu choi sinh file, bao ro 'CHUA_DO_DUOC: bang luat toan 0'."""
    specs = [{"ten": "rong", "chan": {"so_vi_the_toi_da": 0}},
             {"ten": "co_luat", "dat_hue": {"tu": {"pip": 10}}}]
    with pytest.raises(DQ.KhongDichDuoc) as e:
        DQ.sinh_khoi_nhieu(specs, khung="D1", atr=ATR_THAT, gia_diem=GIA_DIEM_THAT)
    assert "CHUA_DO_DUOC" in str(e.value)
    assert "bang luat toan 0" in str(e.value)


def test_sinh_khoi_nhieu_moi_luat_giong_het_nhau_bi_tu_choi():
    """Cong (2): tat ca luat cho CUNG mot bo tham so sau khi quy ATR - dau
    hieu dien hinh cua loi 11/09 (vd atr/gia_diem dau vao sai)."""
    specs = [{"ten": "x", "dat_hue": {"tu": {"pip": 10}}},
             {"ten": "y", "dat_hue": {"tu": {"pip": 10}}}]
    with pytest.raises(DQ.KhongDichDuoc) as e:
        DQ.sinh_khoi_nhieu(specs, khung="D1", atr=ATR_THAT, gia_diem=GIA_DIEM_THAT)
    assert "CHUA_DO_DUOC" in str(e.value)


def test_dich_nhieu_di_qua_ca_atr_that_va_cong_bang_toan_0():
    """`chuoi_quan_tri.dich_nhieu` la duong CHUOI QUAN TRI de sinh bang N luat -
    phai tu do ATR that (khong nhan tham so tu ben ngoai) roi qua cong (2)."""
    k = CQ.dich_nhieu(so_luat=14, khung="D1", ma="US500CASH", in_ra=None)
    assert k["atr"] > 0
    assert len(k["luat"]) >= 10
    assert "QT_A_DatHue" in k["khoi"]


def test_kiem_bang_luat_bo_qua_cot_mac_dinh_khac_0():
    """`QT_A_TiaTy` (mac dinh 0,5) va `QT_A_NhoiLx` (mac dinh 1,0) KHONG duoc
    tinh la 'luat co cham vi the' - neu tinh ca hai cot nay thi cong khong bao
    gio bat duoc mot luat rong that (moi cot khac deu 0)."""
    gia_tri = {
        "QT_A_DatHue": [0.0, 0.0],
        "QT_A_TiaTy": [0.5, 0.5],
        "QT_A_NhoiLx": [1.0, 1.0],
        "QT_A_TranVT": [0, 0],
    }
    with pytest.raises(DQ.KhongDichDuoc):
        DQ.kiem_bang_luat(gia_tri)


# ------------------------------------------------------- CON SO PHAI KHA DI
#
# Them 13/09/2026. Sua quy doi don vi (pip -> ATR) lam bang luat het toan 0,
# nhung no CHUA du: con so DAU VAO van co the la rac. Do tren 128 gia tri
# khoang cach cua kho that:
#
#   * 4 khai bao co `{"pip": False}` / `{"pip": True}` - mot input kieu BOOL
#     cua EA bi boc nham lam do lon. `float(False)` = 0.0 nen no lang le thanh
#     0 ATR: dung hinh dang cua bo phan im lang ma ca phien 12/09 di truy.
#   * 11/128 gia tri duoi 1 pip, ke ca `0.0` va `0,05 pip`.
#
# Phan vi kho: p10=1, p50=45, p90=500, max=6.000 pip - nen khoang 1..5.000
# khong cat mat phan than cua phan bo.


@pytest.mark.parametrize("gia", [True, False])
def test_bool_trong_truong_khoang_cach_bi_chan(gia):
    loi = QD.kiem_con_so({"ten": "x", "trailing": {"khoang": {"pip": gia}}})
    assert loi, "pip=%r phai bi chan" % gia
    assert "khong phai mot con so" in loi[0]


@pytest.mark.parametrize("gia", [0.0, 0.05, 0.3, 0.99])
def test_khoang_cach_qua_nho_bi_chan(gia):
    assert QD.kiem_con_so({"ten": "x", "trailing": {"khoang": {"pip": gia}}})


@pytest.mark.parametrize("gia", [1.0, 20, 45, 500, 5000])
def test_khoang_cach_binh_thuong_di_qua(gia):
    """Cong phai HIEU CHUAN HAI CHIEU: mot cong tu choi TAT CA cho so lieu y
    het mot cong tot."""
    assert QD.kiem_con_so(
        {"ten": "x", "trailing": {"khoang": {"pip": gia}}}) == []


def test_khong_cham_vao_truong_KHONG_phai_khoang_cach():
    """`tia.ty_le` = 0,5 va `nhoi.lot_x` = 1,0 la TY LE chu khong phai khoang
    cach - chan chung theo nguong pip la sai loai."""
    assert QD.kiem_con_so(
        {"ten": "x", "tia": {"ty_le": 0.5}, "nhoi": {"lot_x": 1.0}}) == []


def test_kho_that_phan_duoc_hai_nhom():
    """Lay thu chac chan CO ra thu truoc khi tin mot con so.

    Cong nay phai chan MOT PHAN kho - chan sach hoac khong chan cai nao deu
    nghia la no khong do gi.
    """
    ds = QD.doc_kho()
    assert len(ds) > 50, "kho quan tri rong - bo do mu"
    chan = sum(1 for d in ds if QD.kiem_con_so(d))
    assert 0 < chan < len(ds), "chan %d/%d - cong khong do gi" % (chan, len(ds))
