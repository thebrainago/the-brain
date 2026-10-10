# -*- coding: utf-8 -*-
"""nhan/ho_so_bot.chuan_bi doc THANG export lich su lenh cua MQL5 (WP1, 10/10/2026).

Truoc do `python -m nhan.ho_so_bot <tep>` va `b nc cc ho_so_bot '{"lenh": ...}'` chi hieu bao cao / CSV deal cua tester: export `positions` cua
tin hieu MQL5 (dau `;`, 11 cot, tieu de lap) chet voi `ValueError: CSV deal thieu cot`. Muon boc co che 10 tin hieu winners tu lich su THAT
thi duong dan tep phai di thang duoc (khong qua bo doc rieng). Hai dieu phai giu: (1) tep deal cua tester van di duong cu, (2) tep khong
doc duoc bang CA HAI cach thi thong bao nhac ca hai ly do (khong chi ly do cuoi)."""
from __future__ import annotations

from pathlib import Path

import pytest

from nhan import boc_lich_su as BL
from nhan import ho_so_bot as HB

GOC = Path(__file__).resolve().parent
MQL5 = GOC / "reports" / "fixture" / "mql5_2023752_positions.csv"
DEAL = GOC / "reports" / "fixture" / "tester_cancubo_kp_deals.csv.gz"


@pytest.fixture(scope="module")
def ctx_mql5():
    return HB.chuan_bi(str(MQL5))


def test_export_mql5_di_thang_duoc_va_khop_bo_doc_lich_su(ctx_mql5):
    assert ctx_mql5.ma == "AUDCAD"
    assert len(ctx_mql5.lenh) == len(BL.chuan_hoa(BL.doc_tep(MQL5))) > 2000          # khong rot lenh nao giua hai duong


def test_ho_so_tu_duong_dan_mql5_khong_loi_phep_do():
    hs = HB.ho_so(str(MQL5))                                                          # CHINH duong cua `b nc cc ho_so_bot` va CLI
    tk = hs["tong_ket"]
    assert tk["phep_do_loi"] == {} and tk["khoi_thieu"] == [] and tk["khoi_la"] == []
    assert hs["bao_cao"] and "AUDCAD" in hs["bao_cao"][0]


def test_deal_tester_van_di_duong_cu_khong_bi_nhanh_moi_cuop(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("tep deal tester khong duoc roi sang bo doc export lenh")
    monkeypatch.setattr(HB.BL, "doc_tep", boom)
    c = HB.chuan_bi(str(DEAL))
    assert len(c.lenh) > 100


def test_tep_rac_bao_ca_hai_ly_do(tmp_path):
    f = tmp_path / "rac.csv"
    f.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    with pytest.raises(ValueError) as e:
        HB.chuan_bi(str(f))
    ms = str(e.value)
    assert "CSV deal thieu cot" in ms and "lich su thieu cot" in ms, ms


def test_csv_deal_thieu_cot_giu_ca_hai_ly_do(tmp_path):
    f = tmp_path / "deal_cut.csv"                                                     # giong deal tester nhung cut mat cot (order / profit / balance...)
    f.write_text("time,deal,symbol,type,direction,volume,price\n"
                 "2024.01.02 00:00:01,1,XAUUSD,buy,in,0.01,2000.0\n"
                 "2024.01.02 01:00:01,2,XAUUSD,sell,out,0.01,2001.0\n", encoding="utf-8")
    with pytest.raises(ValueError) as e:                                              # KHONG duoc doc nham thanh danh sach lenh chua dong
        HB.chuan_bi(str(f))
    ms = str(e.value)
    assert "CSV deal thieu cot" in ms and "khong co lenh nao da dong" in ms, ms


def test_tep_khong_ton_tai_van_la_loi_tep_khong_bi_nuot(tmp_path):
    with pytest.raises(FileNotFoundError):
        HB.chuan_bi(str(tmp_path / "khong_co.csv"))


def test_bang_lenh_truyen_thang_khong_di_nhanh_duong_dan(monkeypatch):
    """DataFrame da doc san van chay nhu cu (nhanh duong dan chi danh cho str / Path)."""
    d = BL.doc_tep(MQL5)
    monkeypatch.setattr(HB.LT, "vi_the_tu_tep", lambda *a, **k: (_ for _ in ()).throw(AssertionError("khong duoc goi")))
    monkeypatch.setattr(HB.BL, "doc_tep", lambda *a, **k: (_ for _ in ()).throw(AssertionError("khong duoc goi")))
    assert HB.chuan_bi(d).ma == "AUDCAD"
