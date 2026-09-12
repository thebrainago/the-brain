# -*- coding: utf-8 -*-
"""Kiem ba toan hang HINH HOC them 12/09/2026: fibo · duong_xu_huong · goc.

## Vi sao chung ra doi

So do he thong co dong: *"Cac dang phuong phap dac biet nhu hinh hoc, gann,..."*.
Gann da co tu 08/09 (`gann_sq9`); hinh hoc thi khong co gi. Do duoc 12/09:

  kho 1.764 co che:  28 nhac "fib" · 9 "retrace" · 4 "angle" · 3 "trendline"
  corpus 150 cau:    nhom tu vung `hinh_hoc` thieu nhieu thu NHI o ca hai tang
                     (16/150 o tang KHAU DOC, 3/150 o tang NGU PHAP)

Tuc day la mot lo thung DEM DUOC, khong phai mot y tuong dep.

## Ba tinh chat phai giu, va ca ba deu de mat

**1. FIBO PHAI DICH MOT BAR.** Neo Fibonacci la mot doan song DA XONG. Neu cua
so dinh/day om ca bar dang xet thi dinh chay theo chinh no: gia khong bao gio
vuot noi muc 0,0 va `vi_tri` bi ep cung trong [0; 1]. Do la kieu nhin truoc kin
nhat - no khong lam ket qua dep len, no lam co che IM LANG. Cung ho benh voi
`donchian` (them cung ngay, cung phai dich mot bar).

**2. KHONG PHU THUOC THANG DO.** Do 12/09: nguong `atr14 < 0,003472` hoc tu
train kich hoat **1.719 lan o train va 0 lan o holdout**. Mot toan hang tra ve
gia tho bien co che thanh co che cua MOT tai san o MOT thoi ky. O day do doc
chia ATR, muc fibo chia bien do song - va bai kiem nhan ca bang gia len 137 lan
de chot lai. Rieng cac nhanh tra ve MUC GIA (`fibo` lay="0.618",
`duong_xu_huong` lay="gia_tri") thi PHAI thay doi dung 137 lan: chung la gia, va
chung chi duoc so voi gia khac - y het `donchian` lay="tren".

**3. CHIEU CUA SONG.** Muc 0,382 cua song tang la muc 0,618 cua song giam. Lay
nham chieu khong nem loi, khong ra NaN - no ra mot muc khac guong, va moi ket
qua sau do van "chay duoc".
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import ngu_phap as NP  # noqa: E402

#: Nhanh tra ve so KHONG THANG DO - nhan bang gia len 137 lan phai y nguyen.
KHONG_THANG_DO = [
    {"chi_bao": "fibo", "n": 20, "lay": "vi_tri"},
    {"chi_bao": "fibo", "n": 20, "lay": "khoang_cach", "muc": 0.618},
    {"chi_bao": "fibo", "n": 20, "lay": "vi_tri", "huong": 1},
    {"chi_bao": "duong_xu_huong", "n": 20, "lay": "doc"},
    {"chi_bao": "duong_xu_huong", "n": 20, "lay": "r2"},
    {"chi_bao": "duong_xu_huong", "n": 20, "lay": "lech"},
    {"chi_bao": "duong_xu_huong", "n": 20, "lay": "doc", "chuan": "nguon"},
    {"chi_bao": "goc", "n": 20, "lay": "do"},
    {"chi_bao": "goc", "n": 20, "lay": "radian"},
]
#: Nhanh tra ve MUC GIA - phai theo gia dung mot he so.
THEO_GIA = [
    {"chi_bao": "fibo", "n": 20, "lay": "0.236"},
    {"chi_bao": "fibo", "n": 20, "lay": "0.382"},
    {"chi_bao": "fibo", "n": 20, "lay": "0.5"},
    {"chi_bao": "fibo", "n": 20, "lay": "0.618"},
    {"chi_bao": "fibo", "n": 20, "lay": "0.786"},
    {"chi_bao": "fibo", "n": 20, "lay": "muc", "muc": 1.618},
    {"chi_bao": "duong_xu_huong", "n": 20, "lay": "gia_tri"},
]
MOI = KHONG_THANG_DO + THEO_GIA


def chuoi(n=800, hat=5, xu_huong=0.0):
    """Khung co hinh dang nen that: co khe gia, co rau hai ben."""
    rng = np.random.default_rng(hat)
    c = 100 + np.cumsum(rng.normal(xu_huong, 0.5, n))
    o = np.r_[c[0], c[:-1]] + rng.normal(0, 0.1, n)
    h = np.maximum(o, c) + np.abs(rng.normal(0, 0.3, n))
    l = np.minimum(o, c) - np.abs(rng.normal(0, 0.3, n))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2018-01-01", periods=n, freq="D"))


def bar(o, h, l, c):
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2020-01-01", periods=len(o), freq="D"))


def lay(df, t):
    return np.asarray(NP.toan_hang(df, t), dtype=float)


class KhongCaiNaoNHIN_TRUOC(unittest.TestCase):

    def test_doi_nua_sau_khong_lam_doi_nua_dau(self):
        df = chuoi()
        d2 = df.copy()
        for k in ("open", "high", "low", "close"):
            v = d2[k].to_numpy(float).copy()
            v[500:] *= 1.6
            d2[k] = v
        for t in MOI:
            a, b = lay(df, t)[:480], lay(d2, t)[:480]
            m = np.isfinite(a) & np.isfinite(b)
            self.assertTrue(m.any(), "%s: khong con gia tri nao de so" % t)
            np.testing.assert_allclose(a[m], b[m], atol=1e-9,
                                       err_msg="%s NHIN TRUOC" % t)

    def test_qua_PHEP_CAT_cua_chinh_he(self):
        """Bo do that cua he (`kiem_khong_nhin_truoc`) chu khong phai mot bo do
        rieng cua file nay: tin hieu tai bar t phai giong het du ta co biet cac
        bar sau t hay khong."""
        df = chuoi(900, hat=11)
        for cb in ("fibo", "duong_xu_huong", "goc"):
            s = lay(df, {"chi_bao": cb, "n": 20})
            nguong = float(np.nanmedian(s))
            spec = {"ten": "hinh_hoc_%s" % cb, "ho": "xu_huong", "chieu": 1,
                    "giu": 1, "ra": [],
                    "vao": [{"trai": {"chi_bao": cb, "n": 20}, "phep": ">",
                             "phai": {"hang": nguong}}],
                    "co_che": "khai bao toi thieu de kiem nhin truoc"}
            ti_le = float(np.mean(np.abs(NP.sinh_tu_spec(spec, df)) > 0))
            self.assertGreater(ti_le, 0.05,
                               "%s kich hoat qua thua, phep cat khong cham toi" % cb)
            ok, mo_ta = NP.kiem_khong_nhin_truoc(spec, df)
            self.assertTrue(ok, "%s: %s" % (cb, mo_ta))

    def test_fibo_PHAI_DICH_MOT_BAR(self):
        """Neu cua so dinh/day om ca bar dang xet thi `vi_tri` bi ep trong
        [0; 1] va moi dieu kien "gia pha qua dinh song" khong bao gio dung."""
        df = chuoi(2000, hat=3)
        vt = lay(df, {"chi_bao": "fibo", "n": 20, "lay": "vi_tri"})
        m = np.isfinite(vt)
        ngoai = float(np.mean((vt[m] < 0) | (vt[m] > 1)))
        self.assertGreater(ngoai, 0.01,
                           "chi %.2f%% bar ra ngoai doan song - cua so chua "
                           "duoc dich mot bar" % (ngoai * 100))

    def test_gia_co_the_o_CA_HAI_PHIA_muc_fibo(self):
        """Chieu nguoc cua bai tren: mot muc ma gia luon nam mot phia la mot
        dieu kien khong mang thong tin."""
        df = chuoi(2000, hat=3)
        muc = lay(df, {"chi_bao": "fibo", "n": 20, "lay": "0.618"})
        c = df["close"].to_numpy(float)
        m = np.isfinite(muc)
        tren = float(np.mean(c[m] > muc[m]))
        self.assertTrue(0.05 < tren < 0.95,
                        "gia nam tren muc 0,618 o %.1f%% bar - muc suy bien"
                        % (tren * 100))


class KhongPhuThuocTHANG_DO(unittest.TestCase):

    HE_SO = 137.0

    def setUp(self):
        self.df = chuoi(700, hat=7)
        self.to = self.df * self.HE_SO

    def test_nhan_bang_gia_137_lan_khong_lam_doi_gi(self):
        for t in KHONG_THANG_DO:
            a, b = lay(self.df, t), lay(self.to, t)
            m = np.isfinite(a) & np.isfinite(b)
            self.assertTrue(m.any(), t)
            # atol noi hon 1e-9 cho `r2`: no la ti so cua hai BINH PHUONG nen
            # sai so float bi nhan doi bac khi gia lon gap 137 lan. Do duoc:
            # lech lon nhat 9,7e-10 tren 20.000 bar.
            np.testing.assert_allclose(
                a[m], b[m], rtol=1e-7, atol=1e-7,
                err_msg="%s phu thuoc THANG DO gia" % t)

    def test_muc_gia_thi_theo_gia_dung_mot_he_so(self):
        """Nhanh tra ve MUC GIA khong duoc "khong doi" - no phai doi DUNG 137
        lan. Mot muc fibo bat bien theo thang do la mot muc sai."""
        for t in THEO_GIA:
            a, b = lay(self.df, t), lay(self.to, t)
            m = np.isfinite(a) & np.isfinite(b)
            self.assertTrue(m.any(), t)
            np.testing.assert_allclose(b[m], a[m] * self.HE_SO, rtol=1e-9,
                                       err_msg="%s khong bien doi theo gia" % t)

    def test_phep_do_nay_BAT_DUOC_thu_phu_thuoc_thang_do(self):
        """Hieu chuan chieu nguoc. Mot bai kiem "khong doi gi" chay tren mot
        phep do mu thi cho so lieu y het mot bai kiem tot."""
        a = lay(self.df, {"chi_bao": "atr", "n": 14})
        b = lay(self.to, {"chi_bao": "atr", "n": 14})
        m = np.isfinite(a) & np.isfinite(b)
        self.assertFalse(np.allclose(a[m], b[m], rtol=1e-7, atol=1e-7),
                         "phep do khong phan biet duoc `atr` (gia tho) voi mot "
                         "toan hang da chuan hoa - no vo dung")


class NguongPhaiCHUYEN_DUOC_SANG_CHE_DO_KHAC(unittest.TestCase):
    """Phep do THAT cua rang buoc "khong phu thuoc thang do".

    Nhan bang gia len 137 lan chi chung minh toan hang khong doc thang do TUYET
    DOI. Cai lam hong co che that la che do BIEN DONG doi: nguong `atr14 <
    0,003472` lay o train kich hoat 1.719 lan o train va 0 lan o holdout, va
    khong ai thay vi co che chi "im lang" chu khong bao loi.

    O day nua sau co bien dong gap 8 lan nua dau. Nguong lay tu nua dau phai
    con kich hoat o nua sau.
    """

    SAN = 0.4                              # giu it nhat 40% so lan kich hoat

    def _khung(self, n, sig, hat):
        r = np.random.default_rng(hat)
        c = 100 + np.cumsum(r.normal(0, sig, n))
        o = np.r_[c[0], c[:-1]] + r.normal(0, sig * 0.2, n)
        h = np.maximum(o, c) + np.abs(r.normal(0, sig * 0.6, n))
        l = np.minimum(o, c) - np.abs(r.normal(0, sig * 0.6, n))
        return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                            index=pd.date_range("2000-01-01", periods=n, freq="D"))

    def _kich_hoat(self, t, q):
        a, b = self._khung(1500, 0.5, 1), self._khung(1500, 4.0, 2)
        xa, xb = lay(a, t), lay(b, t)
        nguong = float(np.nanquantile(xa, q))
        duoi = q < 0.5
        na = int(np.nansum(xa < nguong) if duoi else np.nansum(xa > nguong))
        nb = int(np.nansum(xb < nguong) if duoi else np.nansum(xb > nguong))
        return na, nb

    def test_nguong_nua_dau_van_kich_hoat_o_nua_sau(self):
        for t in ({"chi_bao": "fibo", "n": 20, "lay": "vi_tri"},
                  {"chi_bao": "duong_xu_huong", "n": 20, "lay": "doc"},
                  {"chi_bao": "duong_xu_huong", "n": 20, "lay": "r2"},
                  {"chi_bao": "goc", "n": 20, "lay": "do"}):
            for q in (0.10, 0.90):
                na, nb = self._kich_hoat(t, q)
                self.assertGreater(
                    nb, self.SAN * na,
                    "%s @q%.0f: nua dau %d lan, nua sau chi %d - nguong khong "
                    "chuyen duoc sang che do bien dong khac" % (t, q * 100, na, nb))

    def test_phep_do_nay_BAT_DUOC_toan_hang_phu_thuoc_che_do(self):
        """Hieu chuan chieu nguoc - dung hinh dang loi da do duoc 12/09: `atr`
        tho mat sach o mot dau va no gap 10 lan o dau kia."""
        na_thap, nb_thap = self._kich_hoat({"chi_bao": "atr", "n": 14}, 0.10)
        na_cao, nb_cao = self._kich_hoat({"chi_bao": "atr", "n": 14}, 0.90)
        self.assertGreater(na_thap, 100)
        self.assertEqual(nb_thap, 0, "bo do khong con bat duoc `atr` tho")
        self.assertGreater(nb_cao, 5 * na_cao)


class FiboDungNHU_HINH_VE(unittest.TestCase):
    """Song TANG dung san: 100 -> 120 trong 11 bar roi hoi ve. Bien do = 20."""

    def _song_tang(self):
        c = np.r_[np.linspace(100, 120, 11), np.linspace(118, 110, 5)]
        return bar(c, c, c, c)

    def _song_giam(self):
        c = np.r_[np.linspace(120, 100, 11), np.linspace(102, 110, 5)]
        return bar(c, c, c, c)

    def test_muc_xep_dung_thu_tu_trong_song_tang(self):
        df = self._song_tang()
        muc = [lay(df, {"chi_bao": "fibo", "n": 10, "lay": str(f)})[-1]
               for f in NP.MUC_FIBO]
        self.assertEqual(muc, sorted(muc, reverse=True),
                         "muc thoai lui sau phai nam THAP hon trong song tang")
        dinh = lay(df, {"chi_bao": "donchian", "n": 10, "lay": "tren"})[-1]
        day = lay(df, {"chi_bao": "donchian", "n": 10, "lay": "duoi"})[-1]
        self.assertTrue(day <= min(muc) and max(muc) <= dinh,
                        "muc thoai lui roi ra ngoai doan song")

    def test_muc_0_5_dung_la_trung_diem(self):
        df = self._song_tang()
        giua = lay(df, {"chi_bao": "fibo", "n": 10, "lay": "0.5"})[-1]
        dinh = lay(df, {"chi_bao": "donchian", "n": 10, "lay": "tren"})[-1]
        day = lay(df, {"chi_bao": "donchian", "n": 10, "lay": "duoi"})[-1]
        self.assertAlmostEqual(giua, (dinh + day) / 2.0, places=9)

    def test_muc_MO_RONG_nam_ngoai_doan_song(self):
        df = self._song_tang()
        mr = lay(df, {"chi_bao": "fibo", "n": 10, "lay": "muc", "muc": 1.618})[-1]
        day = lay(df, {"chi_bao": "donchian", "n": 10, "lay": "duoi"})[-1]
        self.assertLess(mr, day, "muc 161,8%% cua song tang phai nam DUOI day")

    def test_vi_tri_do_DO_SAU_thoai_lui(self):
        """0 = dang o dau song, 1 = da hoi het ve goc. Gia cang lui thi so cang
        lon - va do la thu mot co che "mua khi hoi 61,8%%" can hoi."""
        df = self._song_tang()
        vt = lay(df, {"chi_bao": "fibo", "n": 10, "lay": "vi_tri"})
        cuoi = vt[np.isfinite(vt)][-4:]
        self.assertTrue(np.all(np.diff(cuoi) > 0),
                        "gia dang hoi ve ma do sau thoai lui khong tang: %s" % cuoi)
        self.assertGreater(cuoi[-1], 0.5)

    def test_doi_CHIEU_song_thi_muc_LAY_GUONG(self):
        """Muc 0,382 cua song tang la muc 0,618 cua song giam. Day la cho de
        lay nham nhat, va lay nham thi khong co gi nem loi."""
        df = self._song_tang()
        ep_len = lay(df, {"chi_bao": "fibo", "n": 10, "lay": "0.618",
                          "huong": "tang"})[-1]
        ep_xuong = lay(df, {"chi_bao": "fibo", "n": 10, "lay": "0.382",
                            "huong": "giam"})[-1]
        self.assertAlmostEqual(ep_len, ep_xuong, places=9)

    def test_suy_CHIEU_tu_vi_tri_dinh_va_day(self):
        tang = lay(self._song_tang(), {"chi_bao": "fibo", "n": 10,
                                       "lay": "0.618"})[-1]
        ep_tang = lay(self._song_tang(), {"chi_bao": "fibo", "n": 10,
                                          "lay": "0.618", "huong": 1})[-1]
        giam = lay(self._song_giam(), {"chi_bao": "fibo", "n": 10,
                                       "lay": "0.618"})[-1]
        ep_giam = lay(self._song_giam(), {"chi_bao": "fibo", "n": 10,
                                          "lay": "0.618", "huong": -1})[-1]
        self.assertAlmostEqual(tang, ep_tang, places=9,
                               msg="song tang ma suy ra chieu giam")
        self.assertAlmostEqual(giam, ep_giam, places=9,
                               msg="song giam ma suy ra chieu tang")


class DuongXuHuongVaGOC(unittest.TestCase):

    def _mot_atr_moi_bar(self, n=60, d=2.0):
        """Chuoi tang dung MOT ATR moi bar: TR = d o moi bar, do doc = d."""
        c = 100 + np.arange(n) * d
        return bar(c - d, c, c - d, c)

    def test_mot_ATR_moi_bar_dung_bang_45_do(self):
        df = self._mot_atr_moi_bar()
        doc = lay(df, {"chi_bao": "duong_xu_huong", "n": 14, "lay": "doc"})[-1]
        goc = lay(df, {"chi_bao": "goc", "n": 14, "lay": "do"})[-1]
        self.assertAlmostEqual(doc, 1.0, places=9)
        self.assertAlmostEqual(goc, 45.0, places=7)

    def test_r2_bang_1_tren_duong_thang(self):
        df = self._mot_atr_moi_bar()
        r2 = lay(df, {"chi_bao": "duong_xu_huong", "n": 14, "lay": "r2"})[-1]
        self.assertAlmostEqual(r2, 1.0, places=9)

    def test_r2_THAP_tren_chuoi_khong_co_huong(self):
        """Hieu chuan chieu nguoc: neu r2 luon ~1 thi no khong do gi ca."""
        df = chuoi(1200, hat=21)
        r2 = lay(df, {"chi_bao": "duong_xu_huong", "n": 30, "lay": "r2"})
        r2 = r2[np.isfinite(r2)]
        self.assertLess(float(np.median(r2)), 0.6,
                        "chuoi ngau nhien ma do khop trung vi %.2f" % np.median(r2))
        self.assertTrue(np.all((r2 >= -1e-12) & (r2 <= 1 + 1e-12)),
                        "r2 ra ngoai [0; 1]")

    def test_doc_DOI_DAU_theo_chieu_xu_huong(self):
        len_ = lay(chuoi(400, hat=2, xu_huong=0.25),
                   {"chi_bao": "duong_xu_huong", "n": 20})
        xuong = lay(chuoi(400, hat=2, xu_huong=-0.25),
                    {"chi_bao": "duong_xu_huong", "n": 20})
        self.assertGreater(float(np.nanmean(len_[40:])), 0.05)
        self.assertLess(float(np.nanmean(xuong[40:])), -0.05)

    def test_goc_dung_bang_arctan_cua_do_doc(self):
        """Hai toan hang doi chieu nhau: `goc` chi duoc la ban CHAN LAI cua
        `doc`, khong duoc la mot phep tinh khac."""
        df = chuoi(500, hat=13)
        doc = lay(df, {"chi_bao": "duong_xu_huong", "n": 20, "lay": "doc"})
        goc = lay(df, {"chi_bao": "goc", "n": 20, "lay": "do"})
        rad = lay(df, {"chi_bao": "goc", "n": 20, "lay": "radian"})
        m = np.isfinite(doc) & np.isfinite(goc)
        np.testing.assert_allclose(goc[m], np.degrees(np.arctan(doc[m])), atol=1e-9)
        np.testing.assert_allclose(rad[m], np.radians(goc[m]), atol=1e-9)

    def test_goc_CHAN_LAI_cai_duoi_day_cua_do_doc(self):
        """Ly do `goc` ton tai ben canh `doc`: do doc co duoi rat day (mot nen
        khe gia lam no gap hang chuc lan) nen mot nguong hoc tren train de
        thanh nguong khong bao gio cham lai o holdout. Goc bi chan trong
        (-90; 90) nen nguong cua no chuyen duoc."""
        df = chuoi(2000, hat=33)
        doc = lay(df, {"chi_bao": "duong_xu_huong", "n": 20, "lay": "doc"})
        goc = lay(df, {"chi_bao": "goc", "n": 20, "lay": "do"})
        m = np.isfinite(doc) & np.isfinite(goc)
        self.assertTrue(np.all(np.abs(goc[m]) < 90.0))
        duoi_doc = float(np.nanmax(np.abs(doc[m])) / np.nanpercentile(np.abs(doc[m]), 99))
        duoi_goc = float(np.nanmax(np.abs(goc[m])) / np.nanpercentile(np.abs(goc[m]), 99))
        self.assertLess(duoi_goc, duoi_doc,
                        "goc khong lam duoi mong hon do doc (%.2f vs %.2f)"
                        % (duoi_goc, duoi_doc))

    def test_gia_tri_la_DUONG_di_qua_gia(self):
        """Tren mot duong thang thi duong hoi quy trung khit voi gia."""
        df = self._mot_atr_moi_bar()
        gt = lay(df, {"chi_bao": "duong_xu_huong", "n": 14, "lay": "gia_tri"})
        lech = lay(df, {"chi_bao": "duong_xu_huong", "n": 14, "lay": "lech"})
        c = df["close"].to_numpy(float)
        m = np.isfinite(gt)
        np.testing.assert_allclose(gt[m], c[m], atol=1e-9)
        np.testing.assert_allclose(lech[m], 0.0, atol=1e-9)

    def test_chuan_NGUON_dung_cho_chuoi_khong_phai_gia(self):
        """Chia do doc cua `rsi` cho ATR la chia hai don vi khac nhau. `chuan`
        = "nguon" lay chinh buoc di cua chuoi nguon lam thuoc do."""
        df = chuoi(600, hat=17)
        t = {"chi_bao": "duong_xu_huong", "n": 20, "chuan": "nguon",
             "cua": {"chi_bao": "rsi", "n": 14}}
        v = lay(df, t)
        v = v[np.isfinite(v)]
        self.assertGreater(len(v), 400, "chuan='nguon' ra qua nhieu NaN")
        self.assertLess(float(np.nanmax(np.abs(v))), 5.0,
                        "do doc chuan hoa cua rsi ra so vo ly - sai thuoc do")


class MoiNhanhDeuCHAY_DUOC(unittest.TestCase):

    def test_phu_kin_bar_sau_khoi_dong(self):
        df = chuoi(600, hat=4)
        for t in MOI:
            v = lay(df, t)
            self.assertEqual(len(v), len(df), str(t))
            phu = float(np.mean(np.isfinite(v[40:])))
            self.assertGreater(phu, 0.98,
                               "%s chi co %.1f%% bar hop le" % (t, phu * 100))

    def test_ba_ten_moi_deu_nam_trong_CHI_BAO_CO(self):
        """Khai trong ngu phap ma quen khai o `CHI_BAO_CO` thi `thu_hoi_thanh_phan`
        van cham chung la "chua co", va bang "toan hang con thieu" doi them dung
        thu vua lam xong."""
        for cb in ("fibo", "duong_xu_huong", "goc"):
            self.assertIn(cb, NP.CHI_BAO_CO)

    def test_mot_co_che_hinh_hoc_QUA_duoc_cong_khai_bao(self):
        """Goi duoc chua du: co che viet bang toan hang moi con phai qua
        `kiem_khai_bao` thi moi vao duoc kho. Mot toan hang chay duoc ma moi
        khai bao dung no deu bi cong tu choi thi khong hon gi khong co."""
        spec = {"ten": "mua_hoi_618_trong_nhip_tang", "ho": "quay_ve_trung_binh",
                "chieu": 1, "giu": 3, "ra": [],
                "co_che": "Trong mot nhip tang, nguoi lo nhip dau cho gia hoi ve "
                          "vung 61,8% de vao voi rui ro nho hon, nen luc mua don "
                          "lai o do.",
                "vao": [{"trai": {"chi_bao": "fibo", "n": 20, "lay": "vi_tri"},
                         "phep": ">", "phai": {"hang": 0.618}},
                        {"trai": {"chi_bao": "goc", "n": 20},
                         "phep": ">", "phai": {"hang": 5.0}}]}
        self.assertEqual(NP.kiem_khai_bao(spec), [])
        # Nguong goc de o 5 do chu khong 10: do duoc tren chinh chuoi nay, "hoi
        # sau 61,8%" va "duong 20 bar con doc > 10 do" gan nhu KHONG BAO GIO
        # cung xay ra (0,00% so bar) - vi mot nhip hoi sau lam phang chinh
        # duong hoi quy. Day la tinh chat that cua hai toan hang, khong phai
        # loi; ghi ra day de lan sau khong ai chinh nguong ma khong hieu vi sao.
        tin = NP.sinh_tu_spec(spec, chuoi(900, hat=2, xu_huong=0.15))
        self.assertGreater(float(np.mean(np.abs(tin) > 0)), 0.0,
                           "co che hinh hoc khong vao lenh lan nao")

    def test_bi_danh_ve_dung_toan_hang(self):
        df = chuoi(300, hat=6)
        cap = (({"chi_bao": "fib", "n": 20},
                {"chi_bao": "fibo", "n": 20}),
               ({"chi_bao": "fib_618", "n": 20},
                {"chi_bao": "fibo", "n": 20, "lay": "0.618"}),
               ({"chi_bao": "angle", "n": 20},
                {"chi_bao": "goc", "n": 20}),
               ({"chi_bao": "linreg", "n": 20},
                {"chi_bao": "duong_xu_huong", "n": 20, "lay": "gia_tri"}))
        for bi_danh, that in cap:
            a, b = lay(df, bi_danh), lay(df, that)
            m = np.isfinite(a) & np.isfinite(b)
            self.assertTrue(m.any(), str(bi_danh))
            np.testing.assert_allclose(a[m], b[m], atol=1e-12,
                                       err_msg="bi danh %s ve nham cho" % bi_danh)


class KhaiBaoSaiPhaiNEM(unittest.TestCase):

    def setUp(self):
        self.df = chuoi(200, hat=8)

    def test_lay_la_bi_tu_choi(self):
        for cb in ("fibo", "duong_xu_huong", "goc"):
            with self.assertRaises(KeyError, msg=cb):
                NP.toan_hang(self.df, {"chi_bao": cb, "n": 20, "lay": "khong_co"})

    def test_ti_le_fibo_ngoai_khoang_bi_tu_choi(self):
        for muc in (-0.5, 2.5, 300.0):
            with self.assertRaises(KeyError, msg=str(muc)):
                NP.toan_hang(self.df, {"chi_bao": "fibo", "n": 20,
                                       "lay": "muc", "muc": muc})

    def test_huong_la_bi_tu_choi(self):
        with self.assertRaises(KeyError):
            NP.toan_hang(self.df, {"chi_bao": "fibo", "n": 20,
                                   "lay": "0.618", "huong": "cheo"})

    def test_chuan_la_bi_tu_choi(self):
        for cb in ("duong_xu_huong", "goc"):
            with self.assertRaises(KeyError, msg=cb):
                NP.toan_hang(self.df, {"chi_bao": cb, "n": 20, "chuan": "vang"})

    def test_1_618_KHONG_bi_doc_thanh_mot_phay_sau(self):
        """`1.618` la muc mo rong that su (161,8%%). Doi no thanh 1,6%% la doc
        SAI mot khai bao DUNG, va khong mot loi bao nao."""
        self.assertAlmostEqual(NP._ti_le_fibo("1.618"), 1.618, places=9)
        self.assertAlmostEqual(NP._ti_le_fibo("61.8"), 0.618, places=9)
        self.assertAlmostEqual(NP._ti_le_fibo(0.618), 0.618, places=9)
        self.assertIsNone(NP._ti_le_fibo("vi_tri"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
