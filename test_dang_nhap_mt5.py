# -*- coding: utf-8 -*-
"""Test cho `nhan/dang_nhap_mt5.py` — module TU DANG NHAP MT5.

Module nay khong test duoc bang cach goi that: no can mot `terminal64.exe` va
mot tai khoan song. Nhung phan de sai nhat cua no KHONG nam o cho goi MT5 - nam
o ba cho thuan logic duoi day, va ca ba deu test duoc khong can MT5:

  1. **Nhan dang san** (`_dung_san`). Cai bay da do duoc 13/09: `mt5.initialize
     (path=X)` KHONG bao dam ban dang noi voi ban cai X - neu da co mot terminal
     chay thi API gan vao CAI DO. Neu `_dung_san` nhan nham thi ca cai chan do
     tro nen vo dung, va he se doc so cua mot san khac ma khong bao gi.
  2. **Duong GIET terminal.** `TESTER = 1` la rang buoc VAT LI: hai viec tester
     cung luc ghi de ket qua cua nhau va **khong ai bao loi**. Duong giet phai
     di qua `khoa_tester`, khong duoc goi thang lenh cua he dieu hanh.
  3. **Doc/ghi kho tai khoan** khong duoc lam mat mat khau cua san khac.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from nhan import dang_nhap_mt5 as DN

LAB = Path(__file__).resolve().parent


# ------------------------------------------------------------- NHAN DANG SAN
@pytest.mark.parametrize("san,cong_ty,server", [
    ("XM", "XM Global Limited", "XMGlobal-MT5 17"),
    ("Exness", "Exness Technologies Ltd", "Exness-MT5Real37"),
])
def test_dung_san_nhan_ra_ban_cua_chinh_no(san, cong_ty, server):
    assert DN._dung_san(san, cong_ty, server) is True


def test_dung_san_TU_CHOI_terminal_cua_san_khac():
    """Cai bay 13/09: hoi XM nhung API gan vao terminal Exness dang chay."""
    assert DN._dung_san("XM", "Exness Technologies Ltd", "Exness-MT5Real37") is False
    assert DN._dung_san("Exness", "XM Global Limited", "XMGlobal-MT5 17") is False


def test_dung_san_khong_nhan_bua_khi_thong_tin_rong():
    """Thong tin rong = KHONG biet dang noi voi ai. Khong duoc coi la dung san."""
    assert DN._dung_san("XM", "", "") is False
    assert DN._dung_san("XM", None, None) is False


def test_moi_san_khai_bao_deu_co_dau_hieu_nhan_dang():
    """San co trong `EXE` ma khong co trong `DAU_HIEU_SAN` thi roi ve so khop TEN -
    de nhan nham. Chan tu day chu dung doi luc chay that."""
    thieu = sorted(set(DN.EXE) - set(DN.DAU_HIEU_SAN))
    assert thieu == [], f"san thieu dau hieu nhan dang: {thieu}"


# ------------------------------------------------------- DUONG GIET TERMINAL
def test_khong_goi_thang_lenh_giet_cua_he_dieu_hanh():
    """Chieu nguoc cua `khoa_tester`: con mot duong tat thi cai khoa vo nghia.

    `test_khoa_tester.py` quet toan kho; test nay ghim rieng cho file nay vi no
    la file da tung vi pham (sua 14/09/2026).
    """
    s = (LAB / "nhan" / "dang_nhap_mt5.py").read_text(encoding="utf-8-sig")
    # Ghep mau tu manh: viet nguyen chuoi ra day thi CHINH FILE NAY se bi bo quet
    # cua `test_khoa_tester` bat - no glob ca thu muc lab. (Da sap dung vay.)
    mau = re.compile("task" + "kill" + r".{0,40}" + "terminal" + "64", re.I)
    assert not mau.search(s)
    assert "khoa_tester" in s, "duong giet phai di qua khoa_tester"


def test_duong_giet_nem_loi_khi_tien_trinh_khac_dang_chay_tester(tmp_path, monkeypatch):
    """Giet trong khi nguoi khac dang chay tester = pha ket qua cua ho trong im lang."""
    from nhan import khoa_tester as KT
    monkeypatch.setattr(KT, "KHOA", tmp_path / "khoa.json")
    import time
    # `luc` phai la moc THOI GIAN THAT: `dang_giu` tu thu hoi khoa mo coi khi
    # qua `HAN_GIAY`, nen mot khoa de `luc=0` se bi coi la het han va xoa di.
    KT.KHOA.write_text(json.dumps(
        {"pid": 999_999, "viec": "luot tester cua nguoi khac",
         "luc": time.time(), "luc_doc": "2026-09-14 00:00:00"}), encoding="utf-8")
    monkeypatch.setattr(KT, "_con_song", lambda pid: True)
    with pytest.raises(KT.TesterDangBan):
        KT.dong_terminal("thu giet tu dang_nhap_mt5")


# --------------------------------------------------------------- KHO TAI KHOAN
def test_luu_khong_lam_mat_tai_khoan_cua_san_khac(tmp_path, monkeypatch):
    monkeypatch.setattr(DN, "KHO", tmp_path / "tai_khoan.json")
    DN.luu("XM", 111, "mk_xm", ["XMGlobal-MT5 17"])
    DN.luu("Exness", 222, "mk_ex", ["Exness-MT5Real37"])
    assert DN.khoa("XM")["login"] == 111
    assert DN.khoa("Exness")["login"] == 222


def test_khoa_san_chua_luu_tra_ve_rong_chu_khong_nem(tmp_path, monkeypatch):
    monkeypatch.setattr(DN, "KHO", tmp_path / "tai_khoan.json")
    assert DN.khoa("SAN_KHONG_CO") == {}
