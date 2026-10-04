# -*- coding: utf-8 -*-
"""nhan/ho_so_bot.py - ho so co che cua bot do tu lich su lenh.

CLOUD KHONG CO BAO CAO TESTER THAT cua bot that (tep that nam o may nha, khong vao git). Nen bai test dung BO MO PHONG BOT theo
TUNG TICK viet rieng o day (khong dung chung mot dong ma voi bo do) va DAP AN BIET TRUOC:
  * moi bot mo phong duoc khai bao bang `Cfg` (lot nhan / lot theo bac / buoc theo bac / TP chuoi / TP tien / doi ung / tia / lenh
    cho / gio cam...), chay tren duong gia vang gia lap, ghi thanh bao cao tester gia (deal + order) roi doc lai bang
    `lenh_tester` - cung duong di cua bao cao that;
  * bo do phai tim lai dung THAM SO da cai (so lenh kich hoat doi ung, he so lot, buoc tung bac, moc doi bac...) VA phai tra
    `khong_ro` / `khong_do_duoc` o cho du lieu khong cho phep - khong doan;
  * doi chung am: bot KHONG co khoi do thi bo do khong duoc bao `co`;
  * mat the (mutation): pha tung quy tac cua bo do -> it nhat mot bai test phai do.
Dieu khong kiem duoc o day: dinh dang va thoi gian THAT cua tep may nha. Khi co mau that (`reports/fixture/tester_*`) them test do.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import ho_so_bot as H
from nhan import khoi_co_che as KC
from nhan import lenh_tester as LT
from test_lenh_tester import csv_deals, csv_orders, dung_giao_dich

HOP_VANG = 100.0
PIP = 0.1                # 1 pip vang = 0,1 gia = 10 point
BUOC_LOT = 0.01
BD = "2018.01.02 00:00:00"


# =============================================================== BO MO PHONG BOT (viet rieng, khong dung chung ma voi bo do)
@dataclass(frozen=True)
class Cfg:
    chieu: str = "hai"                  # hai | mua
    lot0: float = 0.01
    lot_mode: str = "phang"             # phang | cong | nhan | fibo
    lot_plus: float = 0.01
    lot_m: float = 1.2
    lot_bac: tuple = ()                 # ((tu_lenh, he_so), ...): he so cua lenh thu k >= tu_lenh
    lam_tron: str = "chuoi"             # chuoi: lot_k = tron(lot_{k-1} * m) | tich: lot_k = tron(lot0 * tich m)
    lot_max: float = 99.0               # tran lot MOT lenh
    tong_lot_max: float = 1e9           # tran tong lot cua chuoi
    lot_theo_von: float = 0.0           # >0: lot dau = so_du / lot_theo_von * 0,01 (USD cho moi 0,01 lot)
    buoc_mode: str = "deu"              # deu | gian_dan | bac
    buoc: float = 15.0                  # pip
    buoc_g: float = 1.1
    buoc_tran: float = 1e9
    buoc_bac: tuple = ()                # ((tu_lenh, pip), ...)
    tp_mode: str = "tb"                 # tb | tien | lenh
    tp: float = 8.0                     # pip (tb: tu gia trung binh chuoi; lenh: tu gia mo lenh)
    tp_tien: float = 5.0
    tp_bac: tuple = ()                  # ((tu_lenh_dang_mo, tp_pip), ...) doi TP theo do sau (chi tb)
    max_lenh: int = 40
    doi_ung: tuple | None = None        # (n_kich_hoat, lot): chuoi chinh co >= n lenh thi mo MOT lenh nguoc chieu, dong khi chuoi dong
    tia: tuple | None = None            # (n, F, L, usd): chuoi >= n lenh -> dong F lenh dau + L lenh cuoi khi lai nhom >= usd
    all_sniper: tuple | None = None     # (n, usd): chuoi >= n lenh va tong lai >= usd -> dong TAT CA
    gio_cam: frozenset = frozenset()    # gio (gio may chu) khong mo lenh moi
    vao_lai_cho_pip: float = 0.0        # sau khi chuoi dong, cho gia lui them X pip moi vao lai
    cho_nen: int = 0                    # phut: moi nen chi them toi da 1 lenh / chieu
    sl_pip: float = 0.0                 # cat lo cung moi lenh
    cm: str = ""                        # tien to comment lenh


def _tron(x: float, buoc: float = BUOC_LOT) -> float:
    return round(round(x / buoc) * buoc, 2)


def duong_gia(n: int, seed: int = 1, dt: int = 5, gia0: float = 1800.0, bien: tuple = (0.8, 4.0, 15.0),
              tau: tuple = (60, 800, 8000), nhieu_pt: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
    """Tick vang: (giay tu moc, bid theo point nguyen). Tong ba qua trinh hoi quy (OU) o ba thang thoi gian (bien do gia tri USD,
    tau theo tick) + nhieu moi tick: do sau chuoi lien tuc tu nong den sau, khong chi hai cuc."""
    from scipy.signal import lfilter
    r = np.random.RandomState(seed)
    x = np.zeros(n)
    for amp, ta in zip(bien, tau):
        phi = np.exp(-1.0 / ta)
        e = r.normal(0.0, amp * np.sqrt(1.0 - phi * phi), n)
        e[0] = r.normal(0.0, amp)
        x += lfilter([1.0], [1.0, -phi], e)
    x = gia0 + x + r.normal(0.0, nhieu_pt / 100.0, n)
    bid = np.round(x * 100.0).astype(np.int64)
    t = np.cumsum(r.randint(max(1, dt - 2), dt + 3, size=n)).astype(np.int64)
    return t, bid


def _he_so(cfg: Cfg, k: int) -> float:
    m = cfg.lot_m
    for tu, h in cfg.lot_bac:
        if k >= tu:
            m = h
    return m


def _lot_k(cfg: Cfg, k: int, lot_truoc: float, lot0: float) -> float:
    """Lot cua lenh thu k (k=1 la lenh dau)."""
    if k == 1:
        lot = lot0
    elif cfg.lot_mode == "phang":
        lot = lot0
    elif cfg.lot_mode == "cong":
        lot = lot0 + (k - 1) * cfg.lot_plus
    elif cfg.lot_mode == "nhan":
        if cfg.lam_tron == "chuoi":
            lot = lot_truoc * _he_so(cfg, k)
        else:
            tich = 1.0
            for j in range(2, k + 1):
                tich *= _he_so(cfg, j)
            lot = lot0 * tich
    elif cfg.lot_mode == "fibo":
        a, b = 1, 1
        for _ in range(k - 1):
            a, b = b, a + b
        lot = lot0 * a
    else:
        raise ValueError(cfg.lot_mode)
    return min(_tron(lot), cfg.lot_max)


def _buoc_k(cfg: Cfg, k: int) -> float:
    """Buoc (pip) truoc khi mo lenh thu k (k >= 2)."""
    if cfg.buoc_mode == "deu":
        return cfg.buoc
    if cfg.buoc_mode == "gian_dan":
        return min(cfg.buoc * cfg.buoc_g ** (k - 2), cfg.buoc_tran)
    b = cfg.buoc
    for tu, p in cfg.buoc_bac:
        if k >= tu:
            b = p
    return b


def mo_phong(cfg: Cfg, n: int = 150_000, seed: int = 1, spread: int = 20, von: float = 10000.0, dt: int = 5,
             gia: tuple | None = None, **kw_gia) -> list[dict]:
    """Chay bot `cfg` tren duong gia gia lap -> danh sach VI THE (dap an) theo dinh dang `dung_giao_dich`."""
    t_s, bid = gia if gia is not None else duong_gia(n, seed, dt, **kw_gia)
    t0 = pd.Timestamp(BD)
    vt: list[dict] = []
    huong = (1, -1) if cfg.chieu == "hai" else (1,)
    st = {d: dict(op=[], hedge=None, last_close=None, dong_tick=-1, last_lot=0.0, bar=None) for d in (1, -1)}
    so_du = von
    for i in range(len(t_s)):
        ts = int(t_s[i])
        gio_t = t0 + pd.Timedelta(seconds=ts)
        b = int(bid[i]) / 100.0
        a = (int(bid[i]) + spread) / 100.0
        hh = (ts // 3600) % 24
        for d in huong:
            S = st[d]
            op = S["op"]
            px_ra = b if d > 0 else a                       # gia dong lenh cua chuoi nay
            px_vao = a if d > 0 else b
            # ---------------- thoat
            if op:
                n_op = len(op)
                dong_het = False
                if cfg.sl_pip:
                    for j in list(op):
                        sl_gia = vt[j]["sl"]
                        if d * (px_ra - sl_gia) <= 0:
                            vt[j]["dong"].append((gio_t, vt[j]["lot"], sl_gia, "[sl %.2f]" % sl_gia))
                            so_du += round(d * (sl_gia - vt[j]["gia_mo"]) * vt[j]["lot"] * HOP_VANG, 2)
                            op.remove(j)
                    n_op = len(op)
                if op and cfg.all_sniper and n_op >= cfg.all_sniper[0]:
                    lai = sum(d * (px_ra - vt[j]["gia_mo"]) * vt[j]["lot"] * HOP_VANG for j in op)
                    if lai >= cfg.all_sniper[1]:
                        dong_het = True
                if op and cfg.tp_mode == "tb" and not dong_het:
                    lot_t = sum(vt[j]["lot"] for j in op)
                    tb = sum(vt[j]["lot"] * vt[j]["gia_mo"] for j in op) / lot_t
                    tp_h = cfg.tp
                    for tu, p in cfg.tp_bac:
                        if n_op >= tu:
                            tp_h = p
                    if d * (px_ra - (tb + d * tp_h * PIP)) >= 0:
                        dong_het = True
                elif op and cfg.tp_mode == "tien" and not dong_het:
                    lai = sum(d * (px_ra - vt[j]["gia_mo"]) * vt[j]["lot"] * HOP_VANG for j in op)
                    if lai >= cfg.tp_tien:
                        dong_het = True
                elif op and cfg.tp_mode == "lenh":
                    for j in list(op):
                        tp_gia = vt[j]["tp"]
                        if d * (px_ra - tp_gia) >= 0:
                            vt[j]["dong"].append((gio_t, vt[j]["lot"], tp_gia, "[tp %.2f]" % tp_gia))
                            so_du += round(d * (tp_gia - vt[j]["gia_mo"]) * vt[j]["lot"] * HOP_VANG, 2)
                            op.remove(j)
                            S["dong_tick"] = i
                            S["last_close"] = tp_gia
                if op and cfg.tia and not dong_het and len(op) >= cfg.tia[0]:
                    n_tia, f, l, usd = cfg.tia
                    if f + l < len(op):
                        sub = op[:f] + op[len(op) - l:] if l else op[:f]
                        lai = sum(d * (px_ra - vt[j]["gia_mo"]) * vt[j]["lot"] * HOP_VANG for j in sub)
                        if lai >= usd:
                            for j in sub:
                                vt[j]["dong"].append((gio_t, vt[j]["lot"], px_ra, ""))
                                so_du += round(d * (px_ra - vt[j]["gia_mo"]) * vt[j]["lot"] * HOP_VANG, 2)
                                op.remove(j)
                            S["dong_tick"] = i
                            S["last_close"] = px_ra
                if dong_het and op:
                    for j in list(op):
                        vt[j]["dong"].append((gio_t, vt[j]["lot"], px_ra, ""))
                        so_du += round(d * (px_ra - vt[j]["gia_mo"]) * vt[j]["lot"] * HOP_VANG, 2)
                    op.clear()
                    S["dong_tick"] = i
                    S["last_close"] = px_ra
            # lenh doi ung dong khi chuoi chinh het
            if S["hedge"] is not None and not op:
                j = S["hedge"]
                px_h = a if -d > 0 else b
                px_h_ra = b if -d > 0 else a
                _ = px_h
                vt[j]["dong"].append((gio_t, vt[j]["lot"], px_h_ra, ""))
                so_du += round(-d * (px_h_ra - vt[j]["gia_mo"]) * vt[j]["lot"] * HOP_VANG, 2)
                S["hedge"] = None
            # ---------------- vao
            if hh in cfg.gio_cam or S["dong_tick"] == i:
                continue
            if not op:
                if cfg.vao_lai_cho_pip and S["last_close"] is not None:
                    if d * (S["last_close"] - px_vao) < cfg.vao_lai_cho_pip * PIP:
                        continue
                lot0 = cfg.lot0
                if cfg.lot_theo_von:
                    lot0 = max(BUOC_LOT, _tron(so_du / cfg.lot_theo_von * BUOC_LOT))
                lot = _lot_k(cfg, 1, 0.0, lot0)
                k = 1
            else:
                k = len(op) + 1
                if k > cfg.max_lenh:
                    continue
                if d * (vt[op[-1]]["gia_mo"] - px_vao) < _buoc_k(cfg, k) * PIP:
                    continue
                if cfg.cho_nen:
                    bar = ts // (cfg.cho_nen * 60)
                    if S["bar"] == bar:
                        continue
                lot0 = vt[op[0]]["lot"]
                lot = _lot_k(cfg, k, vt[op[-1]]["lot"], lot0)
                if sum(vt[j]["lot"] for j in op) + lot > cfg.tong_lot_max + 1e-9:
                    continue
                S["bar"] = ts // (cfg.cho_nen * 60) if cfg.cho_nen else None
            p = dict(ma="XAUUSD", chieu=d, lot=lot, gia_mo=px_vao, mo=gio_t, cm_vao="%s%d" % (cfg.cm, k) if cfg.cm else "", dong=[],
                     kieu="", dat=gio_t)
            if cfg.tp_mode == "lenh":
                p["tp"] = round(px_vao + d * cfg.tp * PIP, 2)
            if cfg.sl_pip:
                p["sl"] = round(px_vao - d * cfg.sl_pip * PIP, 2)
            vt.append(p)
            op.append(len(vt) - 1)
            if cfg.doi_ung and S["hedge"] is None and len(op) >= cfg.doi_ung[0]:
                px_h = a if -d > 0 else b                   # lenh nguoc chieu: mo o gia phia nguoc lai
                h = dict(ma="XAUUSD", chieu=-d, lot=cfg.doi_ung[1], gia_mo=px_h, mo=gio_t, cm_vao="", dong=[], kieu="", dat=gio_t)
                vt.append(h)
                S["hedge"] = len(vt) - 1
    return vt


def luu_bao_cao(vt: list[dict], thu_muc: Path, von: float = 10000.0, hoa_hong_lot: float = 0.0, co_orders: bool = True,
                ten: str = "bc") -> pd.DataFrame:
    """Vi the dap an -> bao cao gia (CSV deals [+ orders]) -> bang vi the doc lai bang `lenh_tester` (duong di cua bao cao that)."""
    deals, orders = dung_giao_dich(vt, von=von, hop_dong=HOP_VANG, digits=2, bd=BD, hoa_hong_lot=hoa_hong_lot)
    f = csv_deals(deals, thu_muc / (ten + "_deals.csv"), digits=2)
    o = csv_orders(orders, thu_muc / (ten + "_orders.csv"), digits=2) if co_orders else None
    return LT.vi_the_tu_tep(f, orders_csv=o, hop_dong=HOP_VANG)


# @@FIN_MO_PHONG@@
