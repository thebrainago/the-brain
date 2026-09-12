# -*- coding: utf-8 -*-
"""HIEU CHUAN HAI CHIEU cho pheu `to_hop` + chang holdout.

## Vi sao file nay bat buoc phai ton tai

Lan chay day du 12/09/2026: **2.841 he qua chang holdout, 0 cai thang moc**.

Mot ket luan am nhu vay chi co gia tri khi bo do DA CHUNG MINH duoc no bat duoc
cai co that. Neu khong, "khong tim thay gi" va "khong co kha nang tim thay gi"
trong y het nhau - va ta se ket luan ve thi truong tu mot bo do bi liet.

Du an da tung sap dung o day: memory `cong-pass-phai-hieu-chuan-hai-chieu` -
nha may null 0% lot va cong tu choi tat ca, hai so trong nhu nhau cho den khi
cam mot tin hieu THAT vao.

Nen file nay cam hai thu vao:
    CHIEU DUONG  chuoi co EDGE CAY SAN  -> pheu PHAI bat duoc, va phai qua holdout
    CHIEU AM     chuoi ngau nhien sach  -> pheu PHAI tra ve khong co gi

Neu chieu duong do: **con so 0/2.841 khong noi len dieu gi ve thi truong**, no
noi ve bo do.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import chi_phi as CP      # noqa: E402
from nhan import vao_lenh as VL     # noqa: E402


def chuoi_co_edge(n=3000, suc: float = 0.6, hat: int = 11,
                  nguong: float = 0.35) -> tuple[pd.DataFrame, np.ndarray]:
    """Chuoi gia co EDGE CAY SAN, va mat na tin hieu di kem.

    Luat cay: khi `ibs` cua bar truoc < `nguong` thi bar nay co drift DUONG
    bang `suc` lan do lech chuan.

    **VA DRIFT DO PHAI DUOC BU LAI O CAC BAR CON LAI.** Day la cho toi lam sai
    o ban dau (12/09/2026): chi cong drift duong vao bar co tin hieu thi ca
    chuoi di len manh, mua-giu an tron cai edge vua cay, va moc dd20 len toi
    **139%/nam**. He chon loc chi o trong thi truong ~35% thoi gian nen thua -
    va bai kiem bao "pheu khong bat duoc edge" trong khi that ra no bat duoc,
    chi la moc con cao hon.

    Bai hoc chung: mot edge cay bang cach CONG DRIFT thi khong phan biet duoc
    voi mot XU HUONG. Muon do kha nang phat hien edge thi chuoi phai trung tinh:
    ky vong khong dieu kien = 0, ky vong CO DIEU KIEN moi khac 0.

    `suc = 0,6` sigma la manh - co y. Muc dich khong phai do nguong phat hien
    nho nhat (viec cua `do_luc`), ma tra loi cau hoi nhi phan: pheu nay CO THE
    bat duoc mot edge khong?
    """
    rng = np.random.default_rng(hat)
    sg = 0.008
    c = np.empty(n)
    o = np.empty(n)
    h = np.empty(n)
    l = np.empty(n)
    c[0] = o[0] = 100.0
    h[0], l[0] = 100.5, 99.5
    ibs_truoc = 0.5
    tin = np.zeros(n)
    # Bu lai de KY VONG KHONG DIEU KIEN = 0: bar co tin hieu duoc +suc*sg, cac
    # bar con lai bi tru sao cho tong bang 0. `nguong` la ti le bar co tin hieu.
    bu = suc * sg * nguong / max(1.0 - nguong, 1e-9)
    for i in range(1, n):
        co_tin = ibs_truoc < nguong
        drift = (suc * sg) if co_tin else (-bu)
        tin[i - 1] = 1.0 if co_tin else 0.0
        r = rng.normal(drift, sg)
        o[i] = c[i - 1]
        c[i] = o[i] * np.exp(r)
        bien = abs(rng.normal(0, sg)) * o[i] + abs(c[i] - o[i]) * 0.3
        h[i] = max(o[i], c[i]) + bien
        l[i] = min(o[i], c[i]) - bien
        ibs_truoc = ((c[i] - l[i]) / (h[i] - l[i])) if h[i] > l[i] else 0.5
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                      index=pd.date_range("2010-01-01", periods=n, freq="D"))
    return df, tin


def chuoi_sach(n=3000, hat: int = 12) -> tuple[pd.DataFrame, np.ndarray]:
    """Chuoi NGAU NHIEN thuan, kem mot mat na tin hieu cung tan suat.

    Chieu am cua phep hieu chuan: tin hieu that su khong biet gi.
    """
    rng = np.random.default_rng(hat)
    sg = 0.008
    c = 100 * np.exp(np.cumsum(rng.normal(0, sg, n)))
    o = np.r_[c[0], c[:-1]]
    bien = np.abs(rng.normal(0, sg, n)) * o
    h = np.maximum(o, c) + bien
    l = np.minimum(o, c) - bien
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                      index=pd.date_range("2010-01-01", periods=n, freq="D"))
    ibs = np.where(h > l, (c - l) / np.maximum(h - l, 1e-12), 0.5)
    tin = np.r_[0.0, (ibs[:-1] < 0.35).astype(float)]
    return df, tin


def _cp_re():
    """Chi phi thap nhung KHAC 0 - de phep hieu chuan khong song nho mien phi."""
    return CP.MoHinhChiPhi(ma="HIEU_CHUAN", spread_frac_chung=2e-5,
                           truot_gia_frac=0.0, phi_nam_mua=0.0,
                           phi_nam_ban=0.0, do_tin="DO")


#: Chan troi cua edge cay san: DUNG MOT BAR. Moi phep do phai dung dung chan
#: troi do - do la chinh dieu ma phep hieu chuan nay chung minh.
GIU = 1


def _dd20(df, tin, cp, luat=None, giu: int = GIU):
    from nhan import dap_quan_tri as DQ
    if luat is None:
        r = VL.dap_cau_truc(df, tin, "thi_truong",
                            tham={"sl_atr": 2.0, "tp_atr": 4.0}, giu_toi_da=giu)
    else:
        r = DQ.dap(df, tin, luat, giu_toi_da=giu)
        r.setdefault("phoi_nhiem_gop", 0.0)
    kq = VL.tinh_tien(df, r, cp)
    q = VL.quy_ve_dd(kq.loi_tho, r["_phi"], VL.so_nam_cua(df))
    dd20 = 0.0 if q["chet"] or q["cagr"] is None else q["cagr"] * 100.0
    return dd20, VL.moc_dd20(df, cp) * 100.0, r


class ChieuDUONG_PheuPhaiBAT_DUOC(unittest.TestCase):
    """Neu bai nay do thi con so '0/2.841 he qua holdout' KHONG noi gi ve thi
    truong - no noi rang bo do khong co kha nang phat hien."""

    def setUp(self):
        self.df, self.tin = chuoi_co_edge()
        self.cp = _cp_re()

    def test_edge_cay_san_duoc_phat_hien_tren_TOAN_CHUOI(self):
        dd20, moc, r = _dd20(self.df, self.tin, self.cp)
        self.assertGreater(r["so_lenh"], 50, "khong du lenh de do")
        self.assertGreater(dd20, moc,
                           "pheu KHONG bat duoc mot edge cay san manh 0,6 sigma "
                           "(dd20 %.2f vs moc %.2f)" % (dd20, moc))

    def test_edge_cay_san_SONG_QUA_HOLDOUT(self):
        from nhan import du_lieu as DL
        tr, ho = DL.hai_nua(self.df, 0.6)
        n_tr = len(tr)
        a, moc_a, _ = _dd20(tr, self.tin[:n_tr], self.cp)
        b, moc_b, _ = _dd20(ho, self.tin[n_tr:], self.cp)
        self.assertGreater(a, moc_a, "nua TRAIN khong thay edge")
        self.assertGreater(b, moc_b, "nua HOLDOUT khong thay edge")
        ty = b / a if a > 0 else 0.0
        self.assertTrue(0.2 <= ty <= 5.0,
                        "hai nua lech qua xa nhau (%.2f) tren mot edge ON DINH "
                        "theo xay dung - tieu chi ti le dang qua chat" % ty)

    def test_giu_SAI_CHAN_TROI_thi_edge_BIEN_MAT(self):
        """Bai kiem ghi lai CHINH cai loi da tim ra 12/09/2026.

        Edge song dung 1 bar. Giu 20 bar thi he LO, du edge co dieu kien van
        nguyen ven. Do la ly do `to_hop` phai dung `spec["giu"]` cua tung co che
        chu khong mot so cung 60."""
        dung, moc, _ = _dd20(self.df, self.tin, self.cp, giu=1)
        sai, _, _ = _dd20(self.df, self.tin, self.cp, giu=20)
        self.assertGreater(dung, moc, "giu DUNG chan troi ma van khong thay edge")
        self.assertGreater(dung, sai,
                           "giu 1 bar (%.2f) phai hon giu 20 bar (%.2f) tren mot "
                           "edge song 1 bar" % (dung, sai))

    def test_quan_tri_khong_giet_mat_edge(self):
        """Moi bo luat quan tri deu phai giu duoc edge - neu mot bo luat lam
        edge that bien mat thi no dang lam hong, khong phai dang quan tri."""
        from nhan import dap_quan_tri as DQ
        moc = None
        song = 0
        for ten, luat in DQ.BO_LUAT.items():
            dd20, moc, r = _dd20(self.df, self.tin, self.cp, luat=luat)
            if r["so_lenh"] >= 50 and dd20 > moc:
                song += 1
        self.assertGreaterEqual(
            song, len(DQ.BO_LUAT) // 2,
            "chi %d/%d bo luat giu duoc mot edge manh - ho quan tri dang an mat "
            "edge chu khong khuech dai no" % (song, len(DQ.BO_LUAT)))


class ChieuAM_PheuKhongDuocBIA_RA(unittest.TestCase):
    def test_chuoi_ngau_nhien_khong_thang_moc(self):
        df, tin = chuoi_sach()
        cp = _cp_re()
        dd20, moc, r = _dd20(df, tin, cp)
        self.assertGreater(r["so_lenh"], 50)
        self.assertLessEqual(
            dd20, max(moc, 0.0) + 3.0,
            "chuoi NGAU NHIEN ma pheu bao thang moc %.2f vs %.2f - bo do dang "
            "bia ra edge" % (dd20, moc))

    def test_nhieu_hat_ngau_nhien_it_khi_qua(self):
        """Chay 8 hat: so lan 'thang moc' tren chuoi sach phai it."""
        qua = 0
        for hat in range(20, 28):
            df, tin = chuoi_sach(n=2000, hat=hat)
            dd20, moc, r = _dd20(df, tin, _cp_re())
            if r["so_lenh"] >= 30 and dd20 > moc:
                qua += 1
        self.assertLessEqual(qua, 3,
                             "%d/8 chuoi ngau nhien 'thang moc' - ti le duong "
                             "tinh qua cao" % qua)


if __name__ == "__main__":
    unittest.main(verbosity=2)
