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
