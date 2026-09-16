# -*- coding: utf-8 -*-
"""Test G2-A: khoa theo slot, va cai PHANH khong cho nang tran bua.

Cai dang so nhat o day khong phai bug - la viec nang `TESTER` len khi chua
kiem chung. Hai luot tester ghi de nhau **khong bao loi**: bang so doc y het
mot ket qua that. Nen nua so bai duoi day la test cua cai PHANH.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import pytest  # noqa: E402

from nhan import khoa_tester as KT  # noqa: E402
from nhan import slot_tester as ST  # noqa: E402


def test_khoa_mac_dinh_giu_nguyen_ten_file_cu():
    """Nang cap khong duoc bo roi khoa dang giu cua tien trinh khac."""
    assert KT._tep(None).name == "khoa_tester.json"
    assert KT._tep("s2").name == "khoa_tester_s2.json"


def test_hai_slot_khoa_doc_lap(tmp_path, monkeypatch):
    monkeypatch.setattr(KT, "LAB", tmp_path)
    monkeypatch.setattr(KT, "KHOA", tmp_path / "config" / "khoa_tester.json")
    (tmp_path / "config").mkdir()
    assert KT.thu_lay("viec 1", None)["duoc"]
    # Cung tien trinh nen lay lai duoc; diem chinh la HAI FILE khac nhau.
    assert KT.thu_lay("viec 2", "s2")["duoc"]
    assert (tmp_path / "config" / "khoa_tester.json").exists()
    assert (tmp_path / "config" / "khoa_tester_s2.json").exists()
    KT.tra(None)
    assert not (tmp_path / "config" / "khoa_tester.json").exists()
    assert (tmp_path / "config" / "khoa_tester_s2.json").exists(), \
        "tra khoa slot nay khong duoc xoa khoa slot kia"
    KT.tra("s2")


def _slots(tmp_path, n=2, chung=False):
    ds = []
    for i in range(n):
        d = tmp_path / ("data" if chung else "data%d" % i)
        (d / "bases" / "b" / "history" / "X").mkdir(parents=True, exist_ok=True)
        exe = tmp_path / ("t%d.exe" % i)
        exe.write_text("x")
        ds.append(ST.Slot("s%d" % i, str(exe), str(d),
                          hau_to="" if chung else "_s%d" % i))
    return ds


def test_bat_slot_dung_chung_thu_muc(tmp_path):
    """Hai slot chung thu muc + chung hau to = ghi de nhau, khong bao loi."""
    assert ST.trung_thu_muc(_slots(tmp_path, 2, chung=True))
    assert not ST.trung_thu_muc(_slots(tmp_path, 2, chung=False))


def test_khong_nang_tran_khi_chi_co_mot_slot(monkeypatch, tmp_path):
    monkeypatch.setattr(ST, "doc", lambda: _slots(tmp_path, 1))
    duoc, ly_do = ST.nen_nang_tran()
    assert not duoc and "1 slot" in ly_do


def test_khong_nang_tran_khi_chua_co_bang_chung(monkeypatch, tmp_path):
    """Du hai slot sach: chua kiem chung thi van GIU 1."""
    monkeypatch.setattr(ST, "doc", lambda: _slots(tmp_path, 2))
    monkeypatch.setattr(ST, "LAB", tmp_path)
    duoc, ly_do = ST.nen_nang_tran()
    assert not duoc and "kiem chung" in ly_do


def test_khong_nang_tran_khi_kiem_chung_TRUOT(monkeypatch, tmp_path):
    monkeypatch.setattr(ST, "doc", lambda: _slots(tmp_path, 2))
    monkeypatch.setattr(ST, "LAB", tmp_path)
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "slot_kiem_chung.json").write_text(json.dumps(
        {"giong_nhau": True, "song_song_khop": False,
         "ghi_chu": "chay song song lech 3 lenh"}), encoding="utf-8")
    duoc, ly_do = ST.nen_nang_tran()
    assert not duoc and "CHUA DAT" in ly_do


def test_nang_tran_chi_khi_du_CA_BA_dieu_kien(monkeypatch, tmp_path):
    monkeypatch.setattr(ST, "doc", lambda: _slots(tmp_path, 2))
    monkeypatch.setattr(ST, "LAB", tmp_path)
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "slot_kiem_chung.json").write_text(json.dumps(
        {"giong_nhau": True, "song_song_khop": True, "ghi_chu": "ok"}),
        encoding="utf-8")
    duoc, _ = ST.nen_nang_tran()
    assert duoc


def test_slot_thieu_lich_su_gia_thi_khong_san_sang(tmp_path):
    exe = tmp_path / "t.exe"
    exe.write_text("x")
    d = tmp_path / "trong"
    d.mkdir()
    ok, ly_do = ST.Slot("s", str(exe), str(d)).san_sang()
    assert not ok and "lich su" in ly_do


def test_cap_dat_bien_moi_truong_cho_tien_trinh_con(monkeypatch, tmp_path):
    import os
    monkeypatch.setattr(ST, "doc", lambda: _slots(tmp_path, 1))
    monkeypatch.setattr(KT, "LAB", tmp_path)
    monkeypatch.setattr(KT, "KHOA", tmp_path / "config" / "khoa_tester.json")
    (tmp_path / "config").mkdir(exist_ok=True)
    with ST.cap("thu") as s:
        assert os.environ["BRAIN_MT5"] == str(s.exe)
        assert os.environ["BRAIN_MT5_DATA"] == str(s.du_lieu)
    assert "BRAIN_MT5" not in os.environ or os.environ.get("BRAIN_MT5") != str(s.exe)
