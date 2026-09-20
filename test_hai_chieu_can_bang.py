# -*- coding: utf-8 -*-
"""MAY DE PHAI HOI CA HAI CHIEU (20/09/2026).

`CLAUDE.md` LUAT SO 0: *"'FX' = KIEU GIAO DICH LONG/SHORT, khong phai chi cap
tien"*. Do la mot phat bieu ve SAN CHOI, va no rang buoc truc tiep may de:
mot bo sinh chi biet de ve MUA dang choi tren nua san.

## DO DUOC 20/09/2026 - VAN DE CO THAT, KHONG PHAI GIA DINH

Truoc khi sua, lo duc 714 co che lech **484 long / 230 short**, va **10 trong
23 khuon sinh DUNG MOT CHIEU**:

    thuan_xu_the 84/0 · doi_pct 24/0 · lich_phien 12/0 · fibo 12/0 ·
    nen_bien_dong 12/0 · lich_thang 11/0 · dong_tien 6/0 · hoi_ve_vwap 6/0 ·
    macd 4/0 · nen_manh 4/0

Vi sao do la loi chu khong phai khau vi: tren mot chuoi di len trong mau, mot
may de nghieng ve mua se tim ra "edge" **chi vi so luong phep thu** - va suat
FDR thi bi tieu that. Nguoc lai, tren mot tai san di xuong no se khong thay
gi, trong khi do dung la nua kia cua san choi.

## HAI CACH GUONG - DUNG LAN LA HONG IM LANG

  * Dieu kien **khong co chieu** (lich, nen hep, khoi luong tren trung binh):
    guong bang `_ban_doi_xung` - GIU dieu kien, doi `chieu`.
  * Dieu kien **da co chieu** (`nhanh > cham`, `macd > 0`, `than_nen > 0`):
    phai doi CHINH DIEU KIEN. Neu chi doi nhan thi ban long va ban short kich
    hoat CUNG BAR theo hai huong nguoc nhau -> he khong lam gi ngoai tra phi,
    va bang so cua no trong y het mot he "trung tinh".

Bo bai nay do ca hai.
"""
from __future__ import annotations

import unittest
from collections import Counter

import numpy as np
import pandas as pd

from nhan import hephaestus as HP
from nhan import ngu_phap as NP

LO = HP.duc(han_ngach=9000)


def _df(n: int = 1500, hat: int = 3):
    rng = np.random.default_rng(hat)
    gia = 1.1 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))
    idx = pd.date_range("2019-01-01", periods=n, freq="h")
    return pd.DataFrame({"open": gia, "high": gia * 1.002, "low": gia * 0.998,
                         "close": gia, "volume": rng.uniform(1, 9, n)},
                        index=idx)


class MoiKhuonPhaiHoiCaHaiChieu(unittest.TestCase):
    def test_khong_khuon_nao_chi_sinh_mot_chieu(self):
        lech = []
        for ten, ham in HP.KHUON:
            ds = ham(5)
            c = Counter(d["chieu"] for d in ds)
            a, b = c.get(1, 0), c.get(-1, 0)
            if len(ds) > 1 and (a == 0 or b == 0):
                lech.append("%s: long %d short %d" % (ten, a, b))
        self.assertEqual(lech, [], "khuon chi sinh mot chieu:\n  "
                                   + "\n  ".join(lech))

    def test_ca_lo_duc_can_bang(self):
        c = Counter(d["chieu"] for d in LO)
        a, b = c[1], c[-1]
        self.assertGreater(min(a, b), 0)
        self.assertLessEqual(
            abs(a - b) / max(a, b), 0.10,
            "lo duc lech qua 10%%: long %d / short %d - may de dang choi tren "
            "nua san" % (a, b))

    def test_van_khong_trung_ten_va_khai_bao_van_hop_le(self):
        """Guong hang loat de sinh trung ten hoac spec hong."""
        ten = [d["ten"] for d in LO]
        self.assertEqual(len(ten), len(set(ten)), "co ten trung sau khi guong")
        for d in LO:
            self.assertFalse(NP.kiem_khai_bao(d), d["ten"])


class GuongPhaiDOI_DIEU_KIEN_chu_khong_DOI_NHAN(unittest.TestCase):
    """Chot chan quan trong nhat cua ca goi.

    Guong mot dieu kien DA CO CHIEU (`nhanh > cham`) bang cach giu nguyen
    dieu kien va chi lat `chieu` la loi te nhat co the mac o day: hai co che
    se **kich hoat cung bar theo hai huong nguoc nhau**. Khong cu phap nao
    sai, khong cong nao keu.

    ## PHAI DO TREN `giu = 1`, KHONG DO TREN CHUOI VI THE

    Ban dau toi do `sinh_tu_spec` nguyen ban va thay 103 cap "trung" - trong
    do co ca `hp_thuan_ema10_ema14` vs `hp_thuan_ban_ema10_ema14`, hai dieu
    kien khong the cung dung. Nguyen nhan: `sinh_tu_spec` tra chuoi VI THE,
    ma `giu` giu vi the them nhieu bar sau kich hoat, nen hai lenh no o hai
    thoi diem khac nhau van chong nhau tren chuoi. Do la hanh vi dung cua
    `giu`, khong phai mau thuan.

    Ep `giu = 1` thi chuoi vi the tro ve dung cac bar KICH HOAT: cung hai co
    che do, trung **0** bar. Bai kiem phai do cai no dinh do.
    """

    def setUp(self):
        self.df = _df()
        self.theo_ten = {d["ten"]: d for d in LO}

    def _cap(self):
        """(ban goc long, ban guong short) - tim ca `_ban` cuoi ten VA giua ten.

        Hai dang ten cung ton tai (`hp_vot_ban` va `hp_thuan_ban_ema10_ema14`)
        nen chi bat mot dang thi bo sot gan het. Ban dau toi chi bat hau to va
        bai kiem duyet DUNG 0 cap co dieu kien khac nhau - xanh vi rong.
        """
        ra = []
        for ten, d in self.theo_ten.items():
            if d["chieu"] != -1:
                continue
            for goc_ten in (ten[:-4] if ten.endswith("_ban") else None,
                            ten.replace("_ban_", "_", 1)):
                g = self.theo_ten.get(goc_ten) if goc_ten else None
                if g is not None and g["chieu"] == 1:
                    ra.append((g, d))
                    break
        return ra

    def test_co_du_cap_de_bai_nay_co_nghia(self):
        """Hieu chuan chieu nguoc: bai duoi xanh vi DUNG hay vi RONG?"""
        cap = self._cap()
        self.assertGreaterEqual(len(cap), 100, "qua it cap de ket luan")
        khac = [1 for a, b in cap if a["vao"] != b["vao"]]
        self.assertGreaterEqual(
            len(khac), 100,
            "hau nhu khong cap nao doi DIEU KIEN - hoac `_ban_doi_xung` dang "
            "bi dung cho ca khuon co chieu, hoac phep ghep cap dang bo sot")

    def test_cap_doi_DIEU_KIEN_thi_khong_the_kich_hoat_cung_bar(self):
        n = 0
        for goc, guong in self._cap():
            if goc["vao"] == guong["vao"]:
                continue                    # dang doi xung may moc
            n += 1
            a = np.asarray(NP.sinh_tu_spec(dict(goc, giu=1), self.df), float)
            b = np.asarray(NP.sinh_tu_spec(dict(guong, giu=1), self.df), float)
            ca_hai = int(np.sum((np.abs(a) > 0) & (np.abs(b) > 0)))
            self.assertEqual(
                ca_hai, 0,
                "%s va %s kich hoat CUNG %d bar theo hai huong nguoc nhau - "
                "guong sai kieu: phai doi dieu kien chu khong lat nhan"
                % (goc["ten"], guong["ten"], ca_hai))
        self.assertGreater(n, 100)

    def test_cap_DOI_XUNG_MAY_MOC_giu_nguyen_dieu_kien(self):
        """`_ban_doi_xung` chi duoc dung cho dieu kien KHONG co chieu, va khi
        dung thi phai giu y nguyen dieu kien: hai co che la hai GIA THUYET
        canh tranh ve cung mot cua so ("thu Hai la ngay mua hay ngay ban"),
        duoc thu RIENG chu khong bao gio ghep lam mot."""
        n = 0
        for goc, guong in self._cap():
            if goc["vao"] != guong["vao"]:
                continue
            n += 1
            self.assertEqual(goc["chieu"], -guong["chieu"])
        self.assertGreater(n, 0, "khong cap doi xung nao - `_ban_doi_xung` da "
                                 "bi go?")


class GhepKHONG_DUOC_TRON_HAI_CHIEU(unittest.TestCase):
    """Guong chi an toan chung nao `ghep` con tu choi ghep nguoc chieu.

    Mot co che va ban guong cua no la hai GIA THUYET, khong phai hai ve cua
    mot he. Neu `ghep` tron chung lam mot thi he do mua va ban cung luc - mot
    he tra phi de dung yen, va bang so cua no trong y het mot he trung tinh.
    Nhan doi so ban BAN lam rui ro nay lon hon han truoc, nen phai chot lai.
    """

    def test_ghep_tu_choi_hai_co_che_nguoc_chieu(self):
        theo = {d["ten"]: d for d in LO}
        a = theo["hp_thuan_ema10_ema14"]
        b = theo["hp_thuan_ban_ema10_ema20"]
        self.assertEqual(a["chieu"], -b["chieu"])
        self.assertIsNone(HP.ghep(a, b), "ghep tron hai chieu nguoc nhau")

    def test_ghep_VAN_lam_viec_khi_cung_chieu(self):
        """Hieu chuan chieu nguoc: mot `ghep` tu choi TAT CA cung xanh o bai
        tren ma khong lam duoc gi."""
        theo = {d["ten"]: d for d in LO}
        r = HP.ghep(theo["hp_thuan_ema10_ema14"], theo["hp_thuan_ema20_ema50"])
        self.assertIsNotNone(r, "ghep cung chieu ma van tu choi")
        self.assertEqual(r["chieu"], 1)

    def test_khong_lo_ghep_nao_tron_hai_chieu(self):
        g = HP.ghep_lo(LO[:120], han_ngach=300)
        self.assertTrue(g)
        for d in g:
            self.assertIn(d["chieu"], (1, -1), d["ten"])


if __name__ == "__main__":
    unittest.main()
