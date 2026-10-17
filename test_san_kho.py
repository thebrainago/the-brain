# -*- coding: utf-8 -*-
"""San KHO cua Seeker (17/10/2026): cham repo bang CAY FILE, tach link awesome-*, lan theo submodule."""
from pathlib import Path

import pytest

from tru import seeker as SK

EA = Path("/home/user/ea31337/ea31337")


def test_diem_kho_mot_ea_le_khong_phai_kho():
    d = SK.diem_kho(["README.md", "MyEA.mq5", "include/utils.mqh"])
    assert not d["la_kho"] and d["so_file_mql"] == 2


def test_diem_kho_bo_suu_tap_va_quan_tri_lenh():
    dd = ["Stg_%s/Stg_%s.mqh" % (n, n) for n in "ABCDEFGHIJKLMNOPQRST"]
    assert SK.diem_kho(dd)["la_kho"]
    qt = ["src/grid_manager.py", "src/dca_engine.py", "bot/martingale.mq5", "bot/hedge_lock.mq5", "bot/basket_close.mqh"]
    d = SK.diem_kho(qt)
    assert d["la_kho"] and d["so_file_quan_tri"] == 5 and "src/dca_engine.py" in d["vi_du_quan_tri"]
    assert SK.diem_kho(["a.py"], so_submodule=12)["la_kho"]


def test_tach_link_awesome_va_submodule():
    md = ("- [EA31337](https://github.com/EA31337/EA31337) robot\n- [x](https://github.com/topics/mql5)\n"
          "- see https://github.com/freqtrade/freqtrade-strategies.git and https://github.com/EA31337/EA31337)")
    assert SK.tach_link_github(md) == ["EA31337/EA31337", "freqtrade/freqtrade-strategies"]
    gm = '[submodule "strategies"]\n\tpath = src/strategies\n\turl = https://github.com/EA31337/EA31337-strategies.git\n'
    assert SK.tach_submodule(gm) == ["EA31337/EA31337-strategies"]


@pytest.mark.skipif(not (EA / "src" / "strategies").exists(), reason="can ban clone EA31337 (chi co tren may da tai)")
def test_ea31337_that_duoc_nhan_la_kho():
    # repo con EA31337-strategies: 69 submodule chien luoc -> KHO; repo meta: 42 file Stg_Meta_*.mqh
    goc = EA / "src" / "strategies"
    sm = sum(1 for l in (goc / ".gitmodules").read_text().splitlines() if l.strip().startswith("path"))
    assert SK.diem_kho([], so_submodule=sm)["la_kho"] and sm >= 60
    meta = [str(p.relative_to(EA)) for p in (EA / "src" / "strategies-meta").rglob("*.mqh")]
    assert SK.diem_kho(meta)["la_kho"]
