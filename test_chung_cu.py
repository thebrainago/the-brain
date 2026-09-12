# -*- coding: utf-8 -*-
"""test_chung_cu.py - Hang doi phai cham theo CHUNG CU, khong theo ma thoat.

## Cai da xay ra 12/09/2026 (toi)

O C con 177 MB. Hai viec chay het thoi gian roi bao XONG:

    xao_ma_llm     221s  rc=0  ->  kho co che 2.554 khong doi mot dong
    xao_hoc_thuat  222s  rc=0  ->  y het

Loi that (`database or disk is full`) bi nuot qua ba lop: ham boc bat Exception
roi tra ve rong · hang doi cham theo `rc == 0` · khong ai nhin `nao.db-wal`
(1,4 GB, bang dung `nao.db`).

443 giay chay de sinh ra so 0 - va so 0 do doc duoc y het mot ket luan that
("kho nay khong con gi de boc").
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import day_viec as DV                      # noqa: E402


def test_khong_khai_chung_cu_thi_van_qua():
    """Viec khong khai `bang_chung` giu nguyen hanh vi cu - khong pha gi."""
    dat, ly = DV._kiem_chung_cu({}, time.time())
    assert dat and "khong khai" in ly


def test_tep_khong_doi_thi_TRUOT(tmp_path, monkeypatch):
    p = tmp_path / "ra.json"
    p.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(DV, "LAB", tmp_path)
    time.sleep(0.02)
    t0 = time.time()                        # viec "bat dau" SAU khi tep duoc ghi
    dat, ly = DV._kiem_chung_cu({"tep_moi_hon": "ra.json"}, t0)
    assert dat is False and "KHONG doi" in ly


def test_tep_duoc_ghi_lai_thi_DAT(tmp_path, monkeypatch):
    monkeypatch.setattr(DV, "LAB", tmp_path)
    t0 = time.time()
    time.sleep(0.02)
    (tmp_path / "ra.json").write_text("{}", encoding="utf-8")
    dat, ly = DV._kiem_chung_cu({"tep_moi_hon": "ra.json"}, t0)
    assert dat is True


def test_thieu_tep_thi_TRUOT(tmp_path, monkeypatch):
    monkeypatch.setattr(DV, "LAB", tmp_path)
    dat, ly = DV._kiem_chung_cu({"tep_moi_hon": "khong_co.json"}, time.time())
    assert dat is False and "khong co" in ly


def test_kho_khong_tang_thi_TRUOT(monkeypatch):
    """Dung hinh dang cua `xao_ma_llm`: chay 221 giay, kho khong doi."""
    import nhan.ngu_phap as NP
    monkeypatch.setattr(NP, "doc_kho", lambda: [{}] * 2554)
    dat, ly = DV._kiem_chung_cu({"kho_tang": True, "_kho_truoc": 2554},
                                time.time())
    assert dat is False and "khong sinh ra co che nao" in ly


def test_kho_tang_thi_DAT(monkeypatch):
    import nhan.ngu_phap as NP
    monkeypatch.setattr(NP, "doc_kho", lambda: [{}] * 2600)
    dat, ly = DV._kiem_chung_cu({"kho_tang": True, "_kho_truoc": 2554},
                                time.time())
    assert dat is True and "+46" in ly


def test_trang_thai_rieng_khong_phai_loi():
    """`khong_chung_cu` phai TACH khoi `loi` - hai chuyen khac nhau.

    `loi` = lenh nem ra ma thoat khac 0. `khong_chung_cu` = lenh chay tron ma
    khong sinh ra gi. Gop chung lai thi mat thong tin can de sua.
    """
    import inspect
    ma = inspect.getsource(DV.chay_mot)
    assert "khong_chung_cu" in ma
    assert '"xong" if rc == 0' in ma       # duong cu van con cho viec khong khai


def test_dia_day_thi_dung_hang_doi():
    import inspect
    assert "NGUONG_DIA_GB" in inspect.getsource(DV.chay_het)
