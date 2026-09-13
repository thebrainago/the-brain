# -*- coding: utf-8 -*-
"""test_kho_khong_teo.py - KHO CO CHE khong duoc bien mat.

## Chuyen da xay ra HAI lan

**11/09/2026**: kho tut 1.149 -> 3 co che vi ba tien trinh boc chay doc-sua-ghi
khong khoa. Sua bang `voi_khoa()` + chot hao hut 20%.

**13/09/2026**: kho tut **2.741 -> 130** va chot 20% KHONG chan duoc. Duong di:

    doc_kho() gap loi doc -> `except Exception: return []`
    them_co_che: ds = [] -> append -> luu_kho([1 spec])
    luu_kho: `cu = len(doc_kho())` cung = 0
             chot viet la `if not ep and cu and moi < cu*0.8`
             -> `cu == 0` nen menh de TAT
    ghi de 2.741 co che bang 1

Hai lan, hai nguyen nhan khac nhau, cung mot hau qua. Nen test o day khong test
"chot co chay khong" ma test DUNG BA DUONG DI da tung lam mat du lieu.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import ngu_phap as NP  # noqa: E402


@pytest.fixture
def kho_gia(tmp_path, monkeypatch):
    """Kho rieng trong tmp - KHONG dung vao kho that.

    Chinh mot bo test tung ghi de len kho that; day la ly do fixture nay bat
    buoc chu khong tuy chon.
    """
    f = tmp_path / "co_che_dsl.json"
    ds = [{"ten": "c%d" % i, "ho": "thu",
           "vao": [{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
                    "phai": {"so": i}}]} for i in range(100)]
    f.write_text(json.dumps(ds), encoding="utf-8")
    monkeypatch.setattr(NP, "KHO_CO_CHE", f)
    monkeypatch.setattr(NP, "MOC_CAO", f.with_suffix(".moc_cao"))
    return f, ds


def test_doc_hong_KHONG_duoc_tra_kho_rong(kho_gia):
    """Duong di cua su co 13/09. Day la test quan trong nhat file nay."""
    f, _ = kho_gia
    f.write_text("{ cai nay khong phai JSON", encoding="utf-8")
    with pytest.raises(NP.KhoDocHong):
        NP.doc_kho()


def test_file_khong_co_thi_moi_la_kho_rong(kho_gia):
    """Phan biet 'khong co file' voi 'co file ma doc khong ra'."""
    f, _ = kho_gia
    f.unlink()
    assert NP.doc_kho() == []


def test_doc_hong_thi_khong_ghi_de_duoc(kho_gia):
    """Chot cuoi: ke ca khi ai do bat duoc loi doc, lan ghi van phai bi chan."""
    f, ds = kho_gia
    NP.luu_kho(ds)                      # dat moc cao = 100
    f.write_text("] hong [", encoding="utf-8")
    with pytest.raises((NP.KhoDocHong, NP.KhoBiTeoLai)):
        NP.luu_kho([ds[0]])


def test_chot_hao_hut_mot_lan(kho_gia):
    _, ds = kho_gia
    NP.luu_kho(ds)
    with pytest.raises(NP.KhoBiTeoLai):
        NP.luu_kho(ds[:50])             # mat 50% > 20%
    assert len(NP.doc_kho()) == 100     # kho khong doi


def test_chot_bat_duoc_BAO_MON_DAN(kho_gia):
    """Chot chi so voi LAN TRUOC thi bao mon 19% moi lan khong bao gio bi chan.

    2.741 -> 130 chi can 15 buoc nhu the. Moc cao nhat la thu chan duoc.
    """
    _, ds = kho_gia
    NP.luu_kho(ds)
    n = 100
    for _ in range(10):
        n = int(n * 0.85)               # moi lan mat 15% < nguong 20%
        try:
            NP.luu_kho(ds[:n])
        except NP.KhoBiTeoLai:
            break
    else:
        pytest.fail("bao mon dan di qua duoc het 10 buoc - chot khong co tac dung")
    assert len(NP.doc_kho()) >= 80


def test_ep_van_ghi_duoc_nho_that(kho_gia):
    """Don kho THAT phai lam duoc - chot khong duoc chan ca viec dung."""
    _, ds = kho_gia
    NP.luu_kho(ds)
    NP.luu_kho(ds[:5], ep=True)
    assert len(NP.doc_kho()) == 5


def test_co_ban_lui_sau_moi_lan_ghi(kho_gia):
    """Khoa va chot deu co the bi vuot; mot ban sao thi khong."""
    f, ds = kho_gia
    NP.luu_kho(ds)
    NP.luu_kho(ds[:5], ep=True)
    lui = f.with_suffix(".json.lui")
    assert lui.exists()
    assert len(json.loads(lui.read_text(encoding="utf-8"))) == 100


def test_kho_that_khong_rong():
    """Cham vao kho THAT, chi doc: no phai co hang nghin co che.

    Luat cua du an: truoc khi tin mot danh sach rong, lay mot thu chac chan CO
    ra thu. Day la cai chot do o muc kho.
    """
    assert len(NP.doc_kho()) > 1000
