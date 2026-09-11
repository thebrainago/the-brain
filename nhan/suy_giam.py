# -*- coding: utf-8 -*-
"""suy_giam.py - HE DANG CHAY CO CON GIONG CAI DA KIEM DINH KHONG.

## Van de

Mot he qua cong roi chay that se **khong bao gio** giong het backtest. Cau hoi
khong phai "co lech khong" ma la "lech den muc nao thi phai dung lai".

Khong co module nay thi chi co hai cach hanh xu, va ca hai deu sai:
  - tin mai cho den khi chay tai khoan
  - dung ngay lan thua thu ba, tuc vut mot he tot vi mot chuoi binh thuong

## Cach do

Lay ky vong va do lech tung lenh TU BACKTEST lam gia thuyet goc, roi hoi: chuoi
lenh THAT dang thay co con nam trong phan phoi do khong.

    t = (tb_that - tb_backtest) / (do_lech_backtest / sqrt(n))

`t < -2` (mot phia) la moc canh bao. **KHONG** phai moc dung: voi n nho thi
khong the phan biet "edge chet" voi "xui". Nen module tra ve CA `n` va `n_can` -
so lenh toi thieu de noi duoc dieu gi.

Day chinh la bai hoc `do_luc`/MDE cua du an, ap vao chieu nguoc: truoc khi tuyen
bo mot he DA CHET, phai co du luc de thay cai chet do.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO, so_lenh as SL
else:
    from . import so as SO
    from . import so_lenh as SL

#: Nguong canh bao mot phia. -2 tuong ung ~2,3% neu gia thuyet goc dung.
NGUONG_T = -2.0


def _tk(x: list[float]) -> tuple[float, float]:
    n = len(x)
    if n == 0:
        return 0.0, 0.0
    tb = sum(x) / n
    if n < 2:
        return tb, 0.0
    return tb, math.sqrt(sum((v - tb) ** 2 for v in x) / (n - 1))


def n_can(tb_bt: float, sd_bt: float, hut: float = 0.5) -> int | None:
    """Bao nhieu lenh moi du de THAY mot cu hut `hut` phan cua ky vong?

    Khong co con so nay thi moi ket luan "he da chet" deu la doan. Cung cong
    thuc MDE ma du an dung cho chieu phat hien edge.
    """
    if sd_bt <= 0 or tb_bt == 0:
        return None
    d = abs(tb_bt) * hut
    return max(1, int(math.ceil((2.0 * sd_bt / d) ** 2)))


def do(he: str, tb_bt: float, sd_bt: float, hut: float = 0.5) -> dict:
    """So chuoi lenh THAT cua `he` voi ky vong tu backtest.

    `tb_bt`, `sd_bt`: trung binh va do lech MOI LENH do tu backtest - phai la
    so DO DUOC, khong phai uoc luong. Truyen sai o day thi moi ket luan sau deu
    sai, nen ham khong tu doan chung.
    """
    lai = [x["r"] for x in SL.lenh_cua(he, con_mo=False) if x["r"] is not None]
    n = len(lai)
    tb_that, sd_that = _tk(lai)
    can = n_can(tb_bt, sd_bt, hut)

    t = None
    if n >= 2 and sd_bt > 0:
        t = (tb_that - tb_bt) / (sd_bt / math.sqrt(n))

    if n < 2:
        trang = "CHUA_DO_DUOC"
        mo_ta = f"moi {n} lenh da dong - chua noi duoc gi"
    elif can is not None and n < can:
        trang = "CHUA_DO_DUOC"
        mo_ta = (f"{n} lenh, can >= {can} de thay duoc cu hut {hut:.0%} ky vong. "
                 f"t = {t:.2f} nhung CHUA du luc de ket luan.")
    elif t is not None and t < NGUONG_T:
        trang = "SUY_GIAM"
        mo_ta = (f"t = {t:.2f} < {NGUONG_T} tren {n} lenh: "
                 f"that {tb_that:.4g}/lenh so voi backtest {tb_bt:.4g}")
    else:
        trang = "BINH_THUONG"
        mo_ta = (f"t = {t:.2f} tren {n} lenh - con trong phan phoi cua backtest"
                 if t is not None else f"{n} lenh")

    return {"he": he, "trang_thai": trang, "mo_ta": mo_ta, "n": n, "n_can": can,
            "t": None if t is None else round(t, 4),
            "tb_that": round(tb_that, 6), "sd_that": round(sd_that, 6),
            "tb_backtest": tb_bt, "sd_backtest": sd_bt}


def quet(bang: dict[str, tuple[float, float]]) -> dict:
    """Quet nhieu he. `bang`: he -> (tb_backtest, sd_backtest)."""
    ra = [do(he, tb, sd) for he, (tb, sd) in bang.items()]
    xau = [x for x in ra if x["trang_thai"] == "SUY_GIAM"]
    return {"so_he": len(ra), "so_suy_giam": len(xau), "chi_tiet": ra}


if __name__ == "__main__":
    print(json.dumps(
        {r["ma"]: do(r["ma"], 0.0, 1.0)
         for r in SO.nhieu("SELECT ma FROM he_chay WHERE trang_thai <> 'DUNG'")},
        ensure_ascii=False, indent=1))
