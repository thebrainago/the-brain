# -*- coding: utf-8 -*-
"""Test passview - bo tach tai khoan XEM MT5.

Bai test quan trong nhat o day KHONG phai "bat duoc tai khoan that" ma la
"KHONG bat rac". Do 15/09/2026 ban long dau tien tach **902 tai khoan tu kho**,
va **0/902 co server MT5 that**: server regex bat "Controllable Realism" (khop
"Real"), login bat so bai viet mql5 (23673), pass bat "Forgot" (tu "Forgot
password"). Mot lan dang nhap moi tai khoan rac deu dot mot luot boot terminal.

Day la [[luat-do-phai-thay-duoc-cai-co]] theo chieu nguoc: bo do khong duoc bat
cai KHONG phai.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import passview as PV   # noqa: E402


# ------------------------------------------------------- BAT DUOC TAI KHOAN THAT
def test_bat_duoc_passview_that_da_ngon_ngu():
    mau = {
        "Anh": "Copy my signal! Login: 8823451 Investor password: view2024 "
               "Server: XMGlobal-MT5 3",
        "Viet": "Tai khoan xem MT5: 51234567 mat khau xem: abc123 server "
                "ICMarketsSC-Demo05",
        "Nhat": "口座 6712345 投資者パスワード: jp9988 サーバー XMTrading-Real12",
    }
    for ten, m in mau.items():
        r = PV.boc_tai_khoan(m)
        assert r, "khong bat duoc passview %s" % ten
        assert 100000 <= r[0]["login"] <= 999999999
        assert r[0]["mat_khau"] and r[0]["server"]


# ------------------------------------------------------------ KHONG BAT RAC
def test_khong_bat_bai_viet_mql5_thuong():
    """`Controllable Realism` va `and Live Trading` da lam sinh 902 rac."""
    rac = [
        "This MQL5 article 23673 explains Controllable Realism and Live "
        "Trading with 100000 bars of data.",
        "Forgot your password? Reset it here. Real time signals for MT5.",
        "White Reality posted an EA. Backtest over 8823451 ticks, very good.",
        "Download LiveTrader from our site. Works with any MT5 build.",
    ]
    for m in rac:
        assert PV.boc_tai_khoan(m) == [], "bat nham rac: %r" % m[:50]


def test_server_that_khong_dung_mot_minh_Real_hay_Live():
    """`Real`/`Live`/`Demo` la tu tieng Anh thuong - phai co GACH NOI + so."""
    assert PV.boc_tai_khoan(
        "login 8823451 investor pass abc123 on our Real trading account") == []
    # nhung Broker-Real<so> thi la server that
    r = PV.boc_tai_khoan(
        "Login: 8823451 investor password: abc123 Server: Alpari-Real5")
    assert r and r[0]["server"] == "Alpari-Real5"


def test_dau_hieu_XEM_phai_o_GAN_login():
    """Ca bai co chu "view" o dau va mot tai khoan REAL o cuoi - khong ghep."""
    m = ("Great view of the market today. " + "x" * 400 +
         " Login: 8823451 password: abc123 Server: XMGlobal-MT5 3")
    # dau hieu "view" cach login 400 ky tu -> ngoai cua so 300 -> khong bat
    assert PV.boc_tai_khoan(m) == []


def test_login_tron_hoac_lap_bi_loai():
    for n in (100000, 111111, 1000000):
        assert not PV._hop_le_login(n), n
    assert PV._hop_le_login(8823451)


def test_pass_khong_phai_tu_tieng_anh_thuong():
    m = "Login: 8823451 forgot password reset Server: XMGlobal-MT5 3 view"
    r = PV.boc_tai_khoan(m)
    # "forgot"/"reset" bi loai -> khong con ung vien mat khau -> khong bat
    assert r == [] or r[0]["mat_khau"].lower() not in ("forgot", "reset")


# ------------------------------------------------------- AN TOAN + LUU
def test_doc_lich_su_KHONG_bao_gio_goi_order_send():
    """Investor password la CHI DOC. Ma khong duoc chua order_send."""
    s = (LAB / "nhan" / "passview.py").read_text(encoding="utf-8-sig")
    # `order_send(` = mot loi GOI. Docstring nhac ten no de canh bao thi khong sao.
    assert "order_send(" not in s, "passview KHONG duoc goi order_send"
    for ham in ("history_deals_get", "positions_get", "account_info"):
        assert ham in s, "thieu ham doc %s" % ham


def test_luu_khu_trung_va_bo_thieu_mat_khau(tmp_path, monkeypatch):
    monkeypatch.setattr(PV, "KHO", tmp_path / "passview.json")
    n1 = PV.luu([{"login": 8823451, "mat_khau": "a1", "server": "X-MT5 3"}])
    n2 = PV.luu([{"login": 8823451, "mat_khau": "a1", "server": "X-MT5 3"}])
    n3 = PV.luu([{"login": 999888777, "mat_khau": None, "server": "Y-MT5"}])
    assert n1 == 1 and n2 == 0 and n3 == 0, (n1, n2, n3)


def test_gitignore_co_passview():
    """Credential khong duoc vao lich su git."""
    gi = (LAB.parent / ".gitignore").read_text(encoding="utf-8")
    assert "passview" in gi, "config/passview.json phai nam trong .gitignore"


# ------------------------------------------------- PHAN TICH (khong can MT5 that)
def test_phan_tich_doc_duoc_cach_quan_li_tu_deals_gia():
    """Dung `dau_chan.phan_loai` tren mot chuoi deal gia hinh luoi/DCA."""
    import numpy as np
    # Gia lap mot he DCA: mo nhieu lenh khi lo, khoi luong tang dan, roi chot
    # het khi hoa. profit am dan roi mot cu duong lon.
    deals = []
    t = 1_600_000_000
    for i in range(60):
        vol = 0.1 * (1.5 ** (i % 5))
        deals.append({"time": t, "symbol": "AUDCAD", "type": 0, "volume": vol,
                      "price": 0.9, "profit": 0.0, "entry": 0})
        t += 3600
        deals.append({"time": t, "symbol": "AUDCAD", "type": 1, "volume": vol,
                      "price": 0.9, "profit": (5.0 if i % 5 == 4 else -1.0),
                      "entry": 1})
        t += 3600
    kq = {"deals": deals, "account": {"loai": "REAL"}}
    r = PV.phan_tich(kq)
    assert r["kieu"] in ("luoi_dca", "gong_lo", "scalp", "xu_huong", "khong_ro")
    assert r["so_lenh_dong"] == 60
    assert r["symbol_hay_danh"][0][0] == "AUDCAD"
