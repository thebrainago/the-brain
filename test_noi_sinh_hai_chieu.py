# -*- coding: utf-8 -*-
"""NOI SINH: luan diem phai NOI CUNG CHIEU voi lenh (20/09/2026).

## HAI LOI, VA CAI THU HAI NANG HON

Do duoc tren chuoi tong hop 3.000 bar, TRUOC khi sua:

    sinh            585 co che ... long   585 / short 0
    sinh_cap      2.998 co che ... long 2.998 / short 0
    sinh_xu_huong    86 co che ... long    86 / short 0

**Loi 1 - lech chieu.** Ca ba bo sinh nhan `chieu: int = 1` va khong loi goi
nao trong kho truyen `-1`. Ca LUONG 3 cua day chuyen chi biet de ve MUA.

**Loi 2 - LUAN DIEM NOI NGUOC VOI LENH.** Nang hon, vi no khong phai thieu
sot ma la mau thuan dang chay. Bang `CO_CHE_CUA` co nhung o ma luan diem la
mot lap luan BAN, nhung `chieu` van bi gan cung `+1`:

    ns_heiken_<_q10_giu5        chieu=+1  "Than HA day chieu giam: ap luc ban
                                           keo dai qua nhieu bar."
    ns_supertrend10_<_q20_giu5  chieu=+1  "chuong trinh ban dang chay"

`LUAT_THO_CODE.md` muc 4: cau `co_che` la **cau MAN HINH DUYET DOC**. Cong
dang doc mot cau noi nguoc voi lenh, va khong cong nao bat duoc vi khong cong
nao doi chieu VAN voi SO.

## CACH SUA

`chieu` suy tu `(ho, phia nguong)` qua `CHIEU_TU_HO`, khong bao gio gan cung.
`CO_CHE_NGUOC` khai CACH DOC THU HAI cua cung mot dieu kien (kiet suc / con
tiep), va hai cach doc do di hai chieu nguoc nhau.
"""
from __future__ import annotations

import unittest
from collections import Counter

import numpy as np
import pandas as pd

from nhan import ngu_phap as NP
from nhan import noi_sinh as NS


def _df(n: int = 1200, hat: int = 5):
    rng = np.random.default_rng(hat)
    g = 1.1 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))
    return pd.DataFrame({"open": g, "high": g * 1.002, "low": g * 0.998,
                         "close": g, "volume": rng.uniform(1, 9, n)},
                        index=pd.date_range("2019-01-01", periods=n, freq="h"))


class ChieuSuyTuLuanDiem(unittest.TestCase):
    def test_bang_CHIEU_TU_HO_phu_het_cac_ho_dang_dung(self):
        ho = {v[0] for v in NS.CO_CHE_CUA.values()} | \
             {v[0] for v in NS.CO_CHE_NGUOC.values()} | \
             {v[0] for v in NS.CO_CHE_NEN.values()}
        thieu = [(h, phia) for h in ho for phia in ("cao", "thap")
                 if (h, phia) not in NS.CHIEU_TU_HO]
        self.assertEqual(thieu, [], "ho chua khai chieu: %r" % (thieu,))

    def test_KIET_SUC_va_CON_TIEP_di_HAI_chieu_nguoc_nhau(self):
        """Do la ca noi dung cua phep sua: mot cuc tri co dung hai cach doc."""
        self.assertEqual(NS.CHIEU_TU_HO[("quay_ve_trung_binh", "thap")], 1)
        self.assertEqual(NS.CHIEU_TU_HO[("xu_huong", "thap")], -1)
        self.assertEqual(NS.CHIEU_TU_HO[("quay_ve_trung_binh", "cao")], -1)
        self.assertEqual(NS.CHIEU_TU_HO[("xu_huong", "cao")], 1)

    def test_toan_hang_KHONG_CO_CHIEU_thi_sinh_CA_HAI(self):
        """ADX do SUC MANH xu huong chu khong do dau: mot ADX = 40 xuat hien ca
        trong con tang lan con sup. Gan `chieu = +1` cho `adx cao` la doc mot
        con so khong dau thanh mot lenh mua."""
        self.assertIn("adx", NS.TOAN_HANG_KHONG_CHIEU)
        doc = NS._cac_cach_doc({"chi_bao": "adx", "n": 14}, cao=True)
        self.assertEqual(sorted(c for _, _, c in doc), [-1, 1], doc)

    def test_toan_hang_CO_CHIEU_thi_moi_cach_doc_chi_mot_chieu(self):
        """Hieu chuan chieu nguoc: neu MOI toan hang deu sinh ca hai chieu thi
        phep suy chieu khong lam gi ca."""
        doc = NS._cac_cach_doc({"chi_bao": "rsi", "n": 14}, cao=False)
        self.assertEqual(len(doc), 2, "rsi thap phai co dung hai cach doc")
        self.assertEqual(sorted(c for _, _, c in doc), [-1, 1])
        for ho, _cau, ch in doc:
            self.assertEqual(NS.CHIEU_TU_HO[(ho, "thap")], ch)

    def test_khong_khai_duoc_vi_sao_thi_KHONG_sinh(self):
        self.assertEqual(NS._cac_cach_doc({"chi_bao": "khong_co_that"}, True), [])


class LuanDiemKHONG_DUOC_NOI_NGUOC(unittest.TestCase):
    """Chot chan chinh. Mot cau noi nguoc voi lenh khong cong nao bat duoc."""

    #: Tu khoa chi mot lap luan BAN. Mot co che MUA mang cau nay la mau thuan.
    TU_BAN = ("ap luc ban keo dai", "chuong trinh ban dang chay",
              "nguon cung ban ep", "con phai ban", "van phai ban",
              "phai xa tiep", "dang rut co he thong", "phai ban tiep")
    #: Tu khoa chi mot lap luan MUA.
    TU_MUA = ("duoc tra cong", "duoc tra phan bu", "duoc tra cao hon",
              "cung cap thanh khoan cho ho duoc tra")

    def setUp(self):
        NP.nap_vao_mau()

    def _moi_o(self):
        for bang in (NS.CO_CHE_CUA, NS.CO_CHE_NGUOC):
            for (cb, phia), (ho, cau) in bang.items():
                if cb in NS.TOAN_HANG_KHONG_CHIEU:
                    continue        # khong chieu thi khong the noi nguoc
                ch = NS.CHIEU_TU_HO.get((ho, phia))
                if ch:
                    yield cb, phia, ho, cau, ch

    def test_cau_lap_luan_BAN_khong_duoc_gan_vao_co_che_MUA(self):
        xau = [(cb, phia, t) for cb, phia, _ho, cau, ch in self._moi_o()
               if ch > 0 for t in self.TU_BAN if t in cau]
        self.assertEqual(xau, [], "co che MUA mang luan diem BAN: %r" % (xau,))

    def test_cau_lap_luan_MUA_khong_duoc_gan_vao_co_che_BAN(self):
        xau = [(cb, phia, t) for cb, phia, _ho, cau, ch in self._moi_o()
               if ch < 0 for t in self.TU_MUA if t in cau]
        self.assertEqual(xau, [], "co che BAN mang luan diem MUA: %r" % (xau,))

    def test_HIEU_CHUAN_NGUOC_bo_do_nay_BAT_DUOC_ban_cu(self):
        """Neu phep do tren xanh ke ca voi ban cu thi no vo nghia.

        Ban cu gan cung `chieu = 1` cho MOI o, ke ca `heiken thap` mang cau
        "ap luc ban keo dai qua nhieu bar". Dung lai canh do o day de chung
        minh bo do bat duoc.
        """
        cau_ban = "Than HA day chieu giam: ap luc ban keo dai qua nhieu bar."
        trung = [t for t in self.TU_BAN if t in cau_ban]
        self.assertTrue(trung, "bo tu khoa khong bat duoc chinh cau da sai")

    def test_hai_cach_doc_cua_cung_mot_o_KHONG_duoc_giong_nhau(self):
        """`LUAT_THO_CODE.md` muc 4: hai khuon chung mot luan diem la hai phep
        thu tra tien FDR hai lan cho mot cau hoi."""
        for khoa, (_ho_a, cau_a) in NS.CO_CHE_CUA.items():
            b = NS.CO_CHE_NGUOC.get(khoa)
            if not b:
                continue
            self.assertNotEqual(cau_a.strip(), b[1].strip(), khoa)
            chung = set(cau_a.lower().split()) & set(b[1].lower().split())
            self.assertLess(len(chung) / max(len(cau_a.split()), 1), 0.6,
                            "hai cach doc cua %r gan nhu cung mot cau" % (khoa,))


class LoDucThatCanBang(unittest.TestCase):
    def setUp(self):
        NP.nap_vao_mau()
        self.df = _df()

    def test_sinh_ra_CA_HAI_chieu_va_khong_trung_ten(self):
        ds = NS.sinh(self.df, cac_toan_hang=[{"chi_bao": "rsi", "n": 14},
                                             {"chi_bao": "ibs"},
                                             {"chi_bao": "adx", "n": 14}],
                     cac_giu=(5,))
        c = Counter(d["chieu"] for d in ds)
        self.assertGreater(c.get(1, 0), 0, "khong co co che MUA nao")
        self.assertGreater(c.get(-1, 0), 0,
                           "van khong sinh co che BAN nao - `chieu` mac dinh "
                           "co phai da tro lai 1 khong?")
        ten = [d["ten"] for d in ds]
        self.assertEqual(len(ten), len(set(ten)), "co ten trung")

    def test_tham_so_chieu_van_LOC_duoc_mot_ben(self):
        cho = [{"chi_bao": "rsi", "n": 14}]
        chi_mua = NS.sinh(self.df, cac_toan_hang=cho, cac_giu=(5,), chieu=1)
        chi_ban = NS.sinh(self.df, cac_toan_hang=cho, cac_giu=(5,), chieu=-1)
        self.assertTrue(chi_mua and chi_ban)
        self.assertTrue(all(d["chieu"] == 1 for d in chi_mua))
        self.assertTrue(all(d["chieu"] == -1 for d in chi_ban))


if __name__ == "__main__":
    unittest.main()


class KiemNhinTruocOMUC_TOAN_HANG(unittest.TestCase):
    """`sinh_cap` khong he chan nhin truoc - va cach chan dung khong phai la
    kiem tung CAP.

    `sinh()` co `kiem_khong_nhin_truoc` tu dau; `sinh_cap` thi KHONG, du mot
    cap nhin truoc y het mot co che don. Nhung kiem tung cap thi:
    **40 giay cho 300 co che** (do 20/09), tuc ~9 phut cho tran mac dinh 4.000.

    Kiem o muc TOAN HANG la du ve mat toan: `A VA B` chi doc qua khu khi ca
    `A` lan `B` chi doc qua khu. Va no chi ton ~20 loi goi thay vi hang nghin:
    cung phep do do, **2 giay** thay cho 40.
    """

    def setUp(self):
        NP.nap_vao_mau()
        self.df = _df(600)

    def test_toan_hang_SACH_thi_di_qua(self):
        th = {"chi_bao": "rsi", "n": 14}
        q = NS.nguong_tu_lich_su(self.df, th, phan_vi=(0.05, 0.2, 0.8, 0.95))
        self.assertTrue(q)
        self.assertTrue(NS._toan_hang_khong_nhin_truoc(th, self.df, q))

    def test_HIEU_CHUAN_NGUOC_chuoi_NHIN_TRUOC_bi_chan(self):
        """Mot bo loc nhan TAT CA cho so lieu y het mot bo loc tot.

        ## VI SAO PHAI BOM CHUOI, KHONG DUNG MOT TOAN HANG CO SAN

        Ban dau toi dinh dung `tre` voi `n` am lam toan hang nhin truoc. Do
        duoc: `tre(-3)[0]` tra **NaN** chu khong tra `close[3]` - tuc ngu phap
        khong cho dich NGUOC, va que thu cua toi dang duoc cham diem tren mot
        dau vao KHONG he nhin truoc. Bai kiem "xanh" do se khong noi gi ca.

        Nen o day bom thang mot chuoi dich nguoc vao `toan_hang`: neu may moc
        chong nhin truoc con song, no PHAI tu choi.
        """
        th = {"chi_bao": "rsi", "n": 14}
        q = NS.nguong_tu_lich_su(self.df, th, phan_vi=(0.05, 0.2, 0.8, 0.95))
        self.assertTrue(NS._toan_hang_khong_nhin_truoc(th, self.df, q),
                        "chuoi SACH ma da bi chan - phep do dang hong")

        goc = NP.toan_hang

        def _nhin_truoc(df, t):
            r = goc(df, t)
            # Keo gia tri cua 5 bar SAU ve bar hien tai.
            return r.shift(-5) if t is th or t == th else r

        NP.toan_hang = _nhin_truoc
        try:
            van_qua = NS._toan_hang_khong_nhin_truoc(th, self.df, q)
        finally:
            NP.toan_hang = goc
        self.assertFalse(van_qua,
                         "mot chuoi DICH NGUOC 5 bar van di qua duoc que thu - "
                         "chot chan nhin truoc cua `sinh_cap` khong lam gi ca")

    def test_que_thu_KHONG_bi_cong_khai_bao_tu_choi(self):
        """Que thu khong bao gio vao kho, nen no khong phai doi tuong cua cong
        khai bao. Goi `kiem_khai_bao` o do lam `sinh_cap` tra ve 0 co che -
        da sap that 20/09/2026 khi viet ham nay."""
        ds = NS.sinh_cap(self.df, cac_toan_hang=[{"chi_bao": "rsi", "n": 14},
                                                 {"chi_bao": "zscore", "n": 20,
                                                  "cua": {"chi_bao": "gia", "cot": "close"}}],
                         cac_giu=(5,), toi_da=40)
        self.assertTrue(ds, "sinh_cap tra ve rong - que thu co dang bi cong "
                            "khai bao tu choi khong?")

    def test_sinh_cap_can_bang_va_khong_trung_ten(self):
        ds = NS.sinh_cap(self.df, cac_toan_hang=[{"chi_bao": "rsi", "n": 14},
                                                 {"chi_bao": "zscore", "n": 20,
                                                  "cua": {"chi_bao": "gia", "cot": "close"}},
                                                 {"chi_bao": "cci", "n": 20}],
                         cac_giu=(5,), toi_da=200)
        c = Counter(d["chieu"] for d in ds)
        self.assertGreater(c.get(1, 0), 0)
        self.assertGreater(c.get(-1, 0), 0)
        self.assertEqual(c.get(0, 0), 0, "co che `chieu = 0` - khong co huong")
        ten = [d["ten"] for d in ds]
        self.assertEqual(len(ten), len(set(ten)))

    def test_hai_ly_do_cua_mot_cap_phai_CUNG_chi_mot_phia(self):
        """Ghep mot luan cu MUA voi mot luan cu BAN roi dan nhan mua la mot cau
        `co_che` tu mau thuan."""
        tha, thb = {"chi_bao": "rsi", "n": 14}, {"chi_bao": "cci", "n": 20}
        for ca in (True, False):
            for cb in (True, False):
                for ka, kb, ch in NS._cac_cap_nhat_tri(tha, ca, thb, cb):
                    self.assertEqual(NS.CHIEU_TU_HO[(ka[0], "cao" if ca else "thap")], ch)
                    self.assertEqual(NS.CHIEU_TU_HO[(kb[0], "cao" if cb else "thap")], ch)

    def test_sinh_xu_huong_chieu_theo_PHEP_SO_chu_khong_theo_tham_so(self):
        """`CO_CHE_CAP["<"]` noi nguyen van "dung ngoai la mot vi the co gia" -
        mot lap luan khong-mua - ma ban cu van gan `+1`."""
        ds = NS.sinh_xu_huong(self.df)
        self.assertTrue(ds)
        for d in ds:
            phep = d["vao"][0]["phep"]
            mong = 1 if phep in (">", "cheo_len") else -1
            self.assertEqual(d["chieu"], mong,
                             "%s co phep %r ma chieu %+d" % (d["ten"], phep, d["chieu"]))
