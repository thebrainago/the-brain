# -*- coding: utf-8 -*-
"""CAT HOA DANG GAT BIEN DO TRONG NEN (tim ra 19/09/2026).

## PHEP DO QUYET DINH

Cung MOT duong gia (chuoi `close` y het nhau), chi khac o cho nen co bien do
hay khong:

    nen CO bien do (hi > lo)        lai +234/nam,  **0/12** lan am
    nen KHONG bien do (hi = lo = c) lai -208/nam,  **12/12** lan am

Dap an dung tren random walk co chi phi la AM. Toan bo phan "lai" den tu bien
do trong nen.

## CO CHE

Trong CUNG mot bar, bo mo phong:
  1. nap them tang khi `lo[i] <= moc` - tuc o day BAT LOI cua bar;
  2. roi `cat_hoa` dong cap voi `tot = hi[i]` - tuc o day CO LOI cua bar.

Mua o day ban o dinh trong cung mot nen. Bar khong noi thu tu cham, nen khong
co gi bao dam duong di cho phep ca hai.

## KHAC VOI TP - va day la cho de lan

TP dung `hi[i]` thi DUNG: TP la lenh CHO dat san o mot muc biet truoc, bar cham
muc do nghia la lenh khop that. Con muc ghep cua `cat_hoa` DOI theo ro (no phu
thuoc gia trung binh va so tang hien tai), nen lay dinh bar la gia dinh bat
duoc dung tick cao nhat.

## HE QUA PHAI NOI RO

`cat_hoa_tu=2` la MAC DINH, nen moi ket qua `mo_phong_v2` chay voi mac dinh
deu chua phan nay. Do la ho co che chu du an quan tam nhat (tia lenh).
"""
from __future__ import annotations

import unittest

import numpy as np

import mo_phong_v2 as MP


def _khung(seed: int, rong: bool, n: int = 12000, bd: float = 0.0008) -> dict:
    """Hai ban CUNG mot chuoi `close`, chi khac bien do trong nen."""
    rng = np.random.default_rng(seed)
    c = 1.0 * np.exp(np.cumsum(rng.normal(0, bd, n)))
    op = np.r_[c[0], c[:-1]]
    if rong:
        hi = np.maximum(c, op) * (1 + bd / 2)
        lo = np.minimum(c, op) * (1 - bd / 2)
    else:
        hi, lo = c.copy(), c.copy()
    return {"hi": hi, "lo": lo, "c": c, "sp": np.full(n, 1.0),
            "thu": np.ones(n, dtype=int), "n": n, "pv": 0.0714,
            "nam": n / (24 * 252.0)}


_KW = dict(buoc=30.0, tp=60.0, cat_hoa_tu=2)


class CatHoaKhongDuocGatBienDoNen(unittest.TestCase):

    def _lai(self, rong: bool, **kw) -> float:
        k = dict(_KW)
        k.update(kw)
        return float(np.mean([MP.mo_phong(_khung(100 + s, rong), **k)["lai_nam"]
                              for s in range(6)]))

    def test_MAC_DINH_khong_con_song_nho_bien_do_nen(self):
        """Chenh lech giua hai ban phai NHO. Con lon nghia la ket qua dang do
        bien do nen chu khong do co che."""
        co = self._lai(True)
        khong = self._lai(False)
        self.assertLess(abs(co - khong), abs(khong) * 0.6 + 50.0,
                        "lai doi qua nhieu khi bo bien do nen: %.1f vs %.1f"
                        % (co, khong))

    def test_MAC_DINH_van_AM_tren_random_walk(self):
        """Random walk co chi phi -> ky vong dung bang -chi phi."""
        self.assertLess(self._lai(True), 0.0)

    def test_ban_TOT_NHAT_van_dung_duoc_de_doi_chieu(self):
        """Khong xoa hanh vi cu: phai giu duoc de do BE cua chenh lech tren
        du lieu that. Xoa di thi khong ai biet cac ket qua cu lech bao nhieu."""
        cu = self._lai(True, cat_hoa_gia="tot_nhat")
        moi = self._lai(True)
        self.assertGreater(cu, moi, "ban 'tot_nhat' phai lac quan hon ban mac dinh")

    def test_ten_ban_la_bi_TU_CHOI(self):
        with self.assertRaises(ValueError):
            MP.mo_phong(_khung(1, True), cat_hoa_gia="khong_he_co", **_KW)


class TP_VAN_DUOC_DUNG_DINH_BAR(unittest.TestCase):
    """Hieu chuan chieu nguoc: khong duoc "sua" luon ca cho dang dung.

    TP la lenh CHO dat san o mot muc biet truoc; bar cham muc do nghia la lenh
    khop that. Neu ban va luon cho nay thi moi ket qua TP se bi lui mot bar va
    bang so se AM hon thuc te.
    """

    def test_TP_van_khop_trong_bar_cham_muc(self):
        d = _khung(7, True)
        r = MP.mo_phong(d, buoc=30.0, tp=20.0, cat_hoa_tu=999)
        self.assertGreater(r["ro_nam"], 0, "khong ro nao dong - TP khong khop")
