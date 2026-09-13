# -*- coding: utf-8 -*-
"""test_go_html.py - KHAU GO HTML, khau con thieu giua THU THAP va BOC.

Vi sao khau nay can test rieng: lo hong no vá KHONG hien ra nhu mot loi. No
hien ra nhu *"boc 300 ban -> 8 ung vien"*, tuc doc y het "kho da can co che".
Ban giao 12/09 dieu do thanh mot bai toan THONG LUONG (goi LLM nhieu luong
hon) va do la chan doan sai.

Nen test o day khong chi hoi "go duoc khong" ma hoi ba cau khac:
  - bo do co THAY duoc HTML that khong (lay thu that ra thu, dung tu che chuoi)
  - hai file co dong y voi nhau ve "cai gi la HTML tho" khong
  - go xong thi phan tram ung vien qua pheu co TANG khong
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import go_html as GH  # noqa: E402


TRANG_GITHUB = """<!DOCTYPE html>
<html lang="en"><head><title>x</title>
<script>var a = 1;</script><style>body{color:red}</style></head>
<body><nav>Sign in Sign up Explore</nav>
<article class="markdown-body">
<h1>Turtle Trading System</h1>
<p>Buy when price closes above the 20-day high. Stop loss at 2 ATR.
Take profit is managed by a trailing stop of 3 ATR from the highest close.</p>
</article>
<footer>copyright github</footer></body></html>"""


def test_thay_duoc_html_that():
    """Bo do phai THAY duoc cai CO truoc khi ai tin mot danh sach rong.

    Lab da ba lan ket luan "khong tim thay" bang mot bo do mu. Nen test nay
    khong tu che chuoi: no lay HTML dung hinh dang cua trang github that
    (doctype + nav + markdown-body + footer).
    """
    assert GH.la_html_tho(TRANG_GITHUB) is True
    assert GH.la_html_tho("import pandas as pd\nif rsi < 30: self.buy()") is False


def test_hai_file_dong_y_ve_dinh_nghia():
    """`go_html.la_html_tho` va `boc_llm._la_html_tho` phai trung nhau.

    Neu lech, phan chenh lech la tap ban doc ma bo loc CHAN nhung bo go KHONG
    GO - va no nam ket mai mai ma khong ai dem duoc.
    """
    from nhan import boc_llm as BL
    mau = [TRANG_GITHUB,
           "<div>" * 30 + "</div>" * 30 + "x" * 900,
           "def next(self):\n    if self.rsi < 30:\n        self.buy()\n" * 40,
           "Vao lenh khi gia cat len EMA200, cat lo 1%, chot loi 2%." * 30]
    for vb in mau:
        assert GH.la_html_tho(vb) == BL._la_html_tho(vb), vb[:60]


def test_go_giu_lai_noi_dung_luat():
    """Go xong thi phan LUAT phai con, phan dieu huong phai mat."""
    ra = GH.go(TRANG_GITHUB)
    assert "Turtle Trading System" in ra
    assert "trailing stop" in ra
    assert "Sign in" not in ra          # nav bi bo
    assert "copyright github" not in ra  # footer bi bo
    assert "var a = 1" not in ra         # script bi bo
    assert "<" not in ra


def test_go_lam_tang_ty_le_qua_pheu():
    """Day la ly do khau nay ton tai - phai co mot test noi dung dieu do.

    Truoc khi go, trang tren bi `boc_llm` chan tu vong ngoai nen khong bao gio
    duoc cham diem. Sau khi go, no cham duoc dau hieu luat ("buy when ...
    closes above", "stop loss", "take profit", "trailing").
    """
    from nhan import boc_llm as BL
    assert BL._la_html_tho(TRANG_GITHUB) is True     # bi chan
    ra = GH.go(TRANG_GITHUB)
    assert BL._la_html_tho(ra) is False              # het bi chan
    assert BL._diem_luat(ra) >= 2                    # va co luat that


def test_go_khong_no_voi_dau_vao_rac():
    """Bo go chay tren ca kho nen no gap moi hinh dang dau vao.

    Ban dau bai nay chi GOI `GH.go(...)` ma khong khang dinh gi - va hien phap
    cua lab (`test_hien_phap.KhongTestRong`) bat dung no ngay trong ngay viet
    ra. Mot bai tu bao PASSED ma khong kiem gi thi te hon khong co bai, vi no
    lam bang so xanh dep len ma khong gac cai nao.
    """
    for vb in ("", None, "khong phai html", "<html>", "<<<<>>>>"):
        assert isinstance(GH.go(vb or ""), str)
    assert GH.go("") == ""              # rong vao thi rong ra, khong bia
    assert "RSI" in GH.go("Vao lenh khi RSI duoi 30")   # van xuoi di qua nguyen
    # THE that thi khong duoc sot; con `<<<<>>>>` thi bs4 coi la VAN BAN chu
    # khong phai the, va giu nguyen no moi dung - do khong phai HTML.
    assert "<p>" not in GH.go("<div><p>Cat lo 1%</p></div>")
    assert GH.go("<<<<>>>>") == "<<<<>>>>"


def test_hau_to_khong_go_hai_lan():
    """Ban da go mang hau to trong `kieu`, nen `ung_vien` khong lay lai no.

    Khong co chot nay thi moi vong lai go lai tu dau tren cung mot tap - dung
    cai bay hang doi bi rac chiem ma lab da gap voi 406 URL chet.
    """
    assert GH.HAU_TO and GH.HAU_TO.startswith("_")
    ds = GH.ung_vien(50)
    for d in ds:
        assert not (d.get("kieu") or "").endswith(GH.HAU_TO)


@pytest.mark.parametrize("n", [1, 5])
def test_ung_vien_khong_vuot_gioi_han(n):
    assert len(GH.ung_vien(n)) <= n
