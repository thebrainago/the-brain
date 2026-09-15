# -*- coding: utf-8 -*-
"""FXBLUE + ETORO — hai nguon "chay sach ma rong" suot 7 luot.

Chan doan 12/09/2026. Ca hai nam trong `NGUON_TRINH_DUYET` (chi doc duoc khi
con Chrome CDP dang mo) va so cai ghi chung la lanh manh: so_lan 4 va 3,
so_loi 0, loi_lien_tuc 0 — nhung **thu_hoach 0**. Do lai bang tay:

    fxblue  /marketdata/systemlist                     -> **404**
    etoro   /strategy-investing/copy-open-book-...      -> **404**
    www.fxblue.com/                                     -> 200, 525.989 ky tu
    www.etoro.com/                                      -> 200, 181.219 ky tu

Mot trang 404 khong nem ngoai le: `_duyet_tai_lieu` chi tra danh sach rong va
vong quet van ghi `lan_cuoi` nhu mot luot thanh cong. Nen "nguon im lang" o day
KHONG phai loi mang, cung khong phai loi bo boc anchor — la **hai dia chi seed
da chet**, va cai gia phai tra la mot bo dem thu_hoach dung yen ma khong ai doc.

Bo test nay khoa ba thu, va ca ba deu tung sai that trong dung phien do:

  1. Hai nguon KHONG duoc quay lai duong CDP. Chung doc duoc bang `requests`,
     con CDP thi thuong TAT — de o do la tu buoc minh doi mot dieu kien khong
     can thiet.
  2. Bo loc xep hang cua eToro khong duoc go. Bang tho co 3.636.551 tai khoan
     va dan dau la rac thong ke (`DiegoButron`, Gain 6.923.152%, 0 nguoi copy).
  3. Tieu de cua fxblue phai lay CA duong dan. Ban dau ham chi lay doan cuoi,
     va 25/103 muc thanh cung mot tieu de "metaTrader4"/"metaTrader5".

Khong goi mang: moi bai deu thay `_lay` va con tro bang ban gia.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import toan_van as TV   # noqa: E402
from tru import seeker as S       # noqa: E402


def _sitemap(*duong: str) -> str:
    """Sitemap gia dung khuon that cua fxblue (co <lastmod>)."""
    muc = "".join(
        f"<url><loc>https://www.fxblue.com{d}</loc>"
        f"<lastmod>2026-09-12T10:45:47.040Z</lastmod></url>" for d in duong)
    return '<?xml version="1.0" encoding="UTF-8"?><urlset>' + muc + "</urlset>"


class _ThayLay:
    """Thay `seeker._lay` bang mot ban gia tra chuoi dinh san."""

    def __init__(self, tra):
        self.tra, self.goi = tra, []

    def __enter__(self):
        self.cu = S._lay

        def gia(url, timeout=25):
            self.goi.append(url)
            return self.tra(url) if callable(self.tra) else self.tra

        S._lay = gia
        return self

    def __exit__(self, *a):
        S._lay = self.cu


class _ThayConTro:
    """Con tro trong RAM — khong dung vao `nao.db` khi chay test."""

    def __init__(self, bd=None):
        self.d = dict(bd or {})

    def __enter__(self):
        self.cu_doc, self.cu_ghi = S._con_tro, S._ghi_con_tro
        S._con_tro = lambda ma: dict(self.d)
        S._ghi_con_tro = lambda ma, d: self.d.update(d)
        return self

    def __exit__(self, *a):
        S._con_tro, S._ghi_con_tro = self.cu_doc, self.cu_ghi


class HaiNguonKhongDuocQuayLaiDuongCDP(unittest.TestCase):
    """Chung doc duoc bang `requests`; CDP la mot dieu kien thua."""

    def test_dang_ky_o_NGUON_chu_khong_phai_NGUON_TRINH_DUYET(self):
        for ma in ("fxblue", "etoro"):
            self.assertIn(ma, S.NGUON, f"'{ma}' bien mat khoi bo nguon")
            self.assertNotIn(
                ma, S.NGUON_TRINH_DUYET,
                f"'{ma}' quay lai duong CDP - no doc duoc bang requests, "
                "con CDP thi thuong TAT (cdp_dang_chay() tra None khi do)")

    def test_moi_nguon_deu_co_ham_boc_that(self):
        self.assertIs(S.NGUON["fxblue"]["ham"], S.n_fxblue)
        self.assertIs(S.NGUON["etoro"]["ham"], S.n_etoro)

    def test_fxblue_khong_con_bi_ep_qua_trinh_duyet_khi_doc_toan_van(self):
        """`/tools-for-download/.../user-guide/metaTrader4` do duoc 33.223 ky
        tu chu bang `requests` - khong co gi de doi Chrome ca."""
        self.assertFalse(TV.can_trinh_duyet("https://www.fxblue.com/live"),
                         "fxblue van bi liet vao mien bat buoc qua trinh duyet")

    def test_khong_con_dem_vao_LAN_QUA_TRINH_DUYET(self):
        """`vuon_nguon` chia ngan sach gio giua hai lan theo SUAT do duoc.

        Ke chung vao lan "qua trinh duyet" thi suat cua hai nguon nay duoc cong
        cho mot duong chay ma chung khong con di - phep do sai o dung cho no
        quyet dinh tien.
        """
        from nhan import vuon_nguon as VN
        for ma in ("fxblue", "etoro"):
            self.assertEqual(VN._lan_cua(ma), "hoc_thuat",
                             f"'{ma}' van nam trong lan xa_hoi/trinh duyet")
        self.assertEqual(VN._lan_cua("reddit_td"), "xa_hoi",
                         "sua nham: nguon that su can trinh duyet cung bi doi lan")


class BocFxblueTuSitemap(unittest.TestCase):

    def test_boc_ra_muc_co_DU_URL_VA_TIEU_DE(self):
        with _ThayLay(_sitemap("/tools-for-download/fx-blue-trading-simulator",
                               "/news/tastyfx/what-is-leverage-in-forex2")):
            ra = S.n_fxblue([])
        self.assertEqual(len(ra), 2, f"boc ra {len(ra)} muc thay vi 2")
        for m in ra:
            self.assertTrue(m["url"].startswith("https://www.fxblue.com/"))
            self.assertGreater(len(m["tieu_de"]), 10, f"tieu de rong: {m}")

    def test_TIEU_DE_LAY_CA_DUONG_DAN_khong_chi_doan_cuoi(self):
        """25/103 muc tung trung tieu de vi chi lay `rsplit('/')[-1]`.

        18 trang huong dan co doan cuoi la `metaTrader4` va 7 trang la
        `metaTrader5`; tat ca deu thanh "[fxblue] metaTrader4".
        """
        with _ThayLay(_sitemap(
                "/tools-for-download/fx-blue-trading-simulator/user-guide/metaTrader4",
                "/tools-for-download/fx-blue-account-monitor/user-guide/metaTrader4")):
            ra = S.n_fxblue([])
        tt = [m["tieu_de"] for m in ra]
        self.assertEqual(len(set(tt)), 2, f"hai trang khac nhau cung tieu de: {tt}")
        self.assertIn("trading simulator", tt[0])
        self.assertIn("account monitor", tt[1])

    def test_BO_100_trang_widget_theo_tung_ma(self):
        """50 `chart/<MA>` + 50 `technical-analysis/<MA>` la cung mot khung
        trang, chi khac ma - nhat ca thi hang doi doc bi chung chiem."""
        with _ThayLay(_sitemap("/market-data/tools/chart/EURUSD",
                               "/market-data/tools/technical-analysis/XAUUSD",
                               "/market-data/tools/chart/SP500",
                               "/market-data/tools/sentiment")):
            ra = S.n_fxblue([])
        self.assertEqual([m["url"] for m in ra],
                         ["https://www.fxblue.com/market-data/tools/sentiment"],
                         "trang widget theo ma van lot vao kho")

    def test_BO_trang_tai_khoan_phap_ly_quang_cao(self):
        with _ThayLay(_sitemap("/login", "/register", "/about/privacy",
                               "/prop-firms/ftmo", "/news/scorecm/trade-bonus",
                               "/news/tastyfx/what-is-a-stop-order")):
            ra = S.n_fxblue([])
        self.assertEqual(len(ra), 1, f"loc sot: {[m['url'] for m in ra]}")
        self.assertIn("/news/tastyfx/", ra[0]["url"])

    def test_HANG_bam_theo_luong_chu_DO_DUOC(self):
        """Huong dan cong cu 33.223 ky tu va bai tastyfx 4.351 ky tu -> hang B
        (duoc `doc_toan_van` keo toan van). Trang cong cu chung 3.552 ky tu va
        phan lon la mo ta giao dien -> hang C."""
        with _ThayLay(_sitemap("/tools-for-download/fx-blue-tick-charts",
                               "/news/tastyfx/what-is-a-limit-order",
                               "/market-data/tools/sentiment")):
            hang = {m["url"].rsplit("/", 1)[-1]: m["hang"] for m in S.n_fxblue([])}
        self.assertEqual(hang["fx-blue-tick-charts"], "B")
        self.assertEqual(hang["what-is-a-limit-order"], "B")
        self.assertEqual(hang["sentiment"], "C")

    def test_sitemap_khong_lay_duoc_thi_tra_RONG_chu_khong_vo(self):
        with _ThayLay(None):
            self.assertEqual(S.n_fxblue([]), [])


def _rankings(tong: int, *ten: str) -> str:
    muc = [{"UserName": t, "Gain": 120.0, "AnnualizedReturn": 31.6,
            "PeakToValley": -35.45, "RiskScore": 5, "Copiers": 1135,
            "Trades": 498, "WinRatio": 48.19, "ProfitableMonthsPct": 69.2,
            "Exposure": 88.0, "LongPosPct": 90.6, "ActiveWeeks": 52,
            "WeeksSinceRegistration": 293, "Country": "Germany"} for t in ten]
    return json.dumps({"Status": "OK", "TotalRows": tong, "Items": muc})


class BocEtoroTuAPIXepHang(unittest.TestCase):

    def test_boc_ra_muc_co_DU_URL_VA_TIEU_DE_KEM_SO(self):
        with _ThayLay(_rankings(477, "MrMagoon")), _ThayConTro():
            ra = S.n_etoro([])
        self.assertEqual(len(ra), 1)
        m = ra[0]
        self.assertEqual(m["url"], "https://www.etoro.com/people/MrMagoon")
        self.assertIn("MrMagoon", m["tieu_de"])
        self.assertIn("-35.45", m["tieu_de"], "tieu de khong mang sut giam")
        self.assertIn("sut giam dinh-day", m["tom_tat"])

    def test_tom_tat_mang_DU_SO_vi_trang_ca_nhan_khong_doc_lai_duoc(self):
        """`/people/<ten>` la vo SPA (0 ky tu chu) nen ban ghi phai TU DU."""
        with _ThayLay(_rankings(477, "MrMagoon")), _ThayConTro():
            tom = S.n_etoro([])[0]["tom_tat"]
        for khoa in ("lai/nam %", "diem rui ro", "so lenh", "thang %",
                     "nguoi copy"):
            self.assertIn(khoa, tom, f"tom tat thieu '{khoa}'")

    def test_de_HANG_C_de_khong_nhoi_dia_chi_chet_vao_hang_doi_doc(self):
        """`doc_toan_van` chi keo hang A/B. Hang B o day = 50 dia chi SPA bi
        danh dau 'khong doc duoc' moi luot."""
        with _ThayLay(_rankings(477, "a1", "a2")), _ThayConTro():
            ra = S.n_etoro([])
        self.assertEqual({m["hang"] for m in ra}, {"C"})

    def test_BO_LOC_XEP_HANG_khong_duoc_go(self):
        """Khong loc thi dan dau bang la `DiegoButron`, Gain 6.923.152%,
        tai khoan 6 thang, 0 nguoi copy - hieu ung von be, khong phai thanh
        tich. Loc lai con 477 nguoi tren 3.636.551 tai khoan."""
        for khoa in ("copiersmin", "tradesmin", "weekssinceregistrationmin",
                     "istestaccount"):
            self.assertIn(khoa, S.ETORO_LOC, f"bo loc mat '{khoa}'")
        self.assertGreaterEqual(int(S.ETORO_LOC["copiersmin"]), 1)
        self.assertGreaterEqual(int(S.ETORO_LOC["weekssinceregistrationmin"]), 52,
                                "duoi mot nam thi chua goi la track record")

    def test_bo_loc_DUOC_GHIM_VAO_URL_goi_di(self):
        with _ThayLay(_rankings(477, "a1")) as t, _ThayConTro():
            S.n_etoro([])
        u = t.goi[0]
        for khoa, gt in S.ETORO_LOC.items():
            self.assertIn(f"{khoa}={gt}", u, f"'{khoa}' khai ma khong gui di")

    def test_CON_TRO_DI_TIEP_khong_doc_lai_trang_1_mai(self):
        """Bai hoc cua `_con_tro`: `n_mql5_code` tung dung o 35 tai lieu vi moi
        luot doc dung trang 1."""
        with _ThayLay(_rankings(477, "a1")) as t, _ThayConTro() as ct:
            S.n_etoro([])
            self.assertIn("page=1", t.goi[0])
            self.assertEqual(ct.d["trang"], 2)
            S.n_etoro([])
            self.assertIn("page=2", t.goi[1])

    def test_HET_TRANG_thi_quay_ve_dau_va_tang_vong(self):
        with _ThayLay(_rankings(80, "a1")), _ThayConTro({"trang": 2}) as ct:
            S.n_etoro([])
        self.assertEqual(ct.d["trang"], 1, "khong quay ve trang 1 khi het bien")
        self.assertEqual(ct.d["vong"], 1)

    def test_JSON_hong_thi_tra_RONG_chu_khong_vo(self):
        with _ThayLay("<html>khong phai json</html>"), _ThayConTro():
            self.assertEqual(S.n_etoro([]), [])


if __name__ == "__main__":
    unittest.main()


# ===== DIEM NANG SUAT PHAI DEM DUOC CAI GI DO (15/09/2026)
def test_diem_nang_suat_KHONG_duoc_xep_theo_nghich_dao_so_tai_lieu():
    """Do 15/09: tu so lay tu `gia_thuyet` noi `t.url = g.nguon` - ma cot do
    chua `'kham_pha'` chu khong phai URL, nen phep noi khop **4/387 dong**.

    Khi tu so luon = 0, ham tro thanh `1 / (so tai lieu + 2)`, tuc XEP HANG
    NGUON THEO NGHICH DAO SO TAI LIEU: nguon doc cang it cang duoc uu tien.
    Top 10 luc do la facebook va cac blog rss it bai; `mql5_code` - nguon tot
    nhat he thong (66,6 co che/100 tai lieu) - khong co mat.

    Bai kiem nay dung mot nguon NANG SUAT CAO va mot nguon NANG SUAT 0 co cung
    co mau, roi doi nguon nang suat cao phai duoc xep tren.
    """
    import types
    from tru import seeker as S
    doc = {"tot": 100, "te": 100}
    cc = {"tot": 60, "te": 0}
    cu_doc, cu_cc = S.SO.nhieu, S._co_che_theo_nguon
    S.SO.nhieu = lambda *a, **k: [{"ng": k_, "n": v} for k_, v in doc.items()]
    S._co_che_theo_nguon = lambda: cc
    try:
        d = S._diem_nang_suat()
    finally:
        S.SO.nhieu, S._co_che_theo_nguon = cu_doc, cu_cc
    assert d["tot"] > d["te"] * 5, (
        "nguon 60 co che/100 bai khong duoc xep tren nguon 0 co che/100 bai: %s"
        % d)


def test_co_che_theo_nguon_noi_duoc_ve_tai_lieu():
    """Neu phep noi hong thi moi nguon deu ra 0 va khong ai bao loi.

    Day chinh la cach loi cu song sot: mot tu so luon bang 0 nhin y het mot tu
    so dung khi moi nguon deu chua co gi.
    """
    from tru import seeker as S
    d = S._co_che_theo_nguon()
    assert isinstance(d, dict)
    if not d:
        import pytest
        pytest.skip("may khong co kho co che that")
    assert sum(d.values()) > 50, (
        "chi noi duoc %d co che ve nguon - phep noi dang hong" % sum(d.values()))
    assert max(d.values()) > 20, "khong nguon nao co qua 20 co che - dang nghi"


def test_prior_phai_la_SUAT_THAT_chu_khong_phai_mot_nua():
    """Nguon TOT NHAT khong duoc vinh vien thua mot nguon CHUA AI THU.

    Do 15/09/2026, sau khi da sua tu so: hang doi doc toan van VAN la 60/60
    `semantic` - mot nguon hoc thuat chua tung duoc doc mot bai nao.

    Ly do nam o PRIOR: Laplace (k+1)/(n+2) tin truoc rang "cu 2 bai doc thi 1
    ra co che" (50%). Nhung suat THAT cua ca he chi 0,304 va nguon tot nhat
    (`mql5_code`) chay o 0,459 - nen voi prior 0,5, ngay ca no cung luon thua
    mot nguon chua thu, va hang doi doc bi nguon moi chiem mai mai.
    """
    from tru import seeker as S
    # mot nguon TOT (46 co che / 100 bai) va mot nguon TE (0/100)
    doc = {"tot": 100, "te": 100}
    d = S._cham_theo_prior_that(doc, {"tot": 46, "te": 0})
    assert d["tot"] > d["chua_ai_thu"], (
        "nguon tot nhat (46/100) van thua nguon chua thu (%.4f vs %.4f)"
        % (d["tot"], d["chua_ai_thu"]))
    # nhung nguon chua thu VAN phai tren nguon da chung minh la te
    assert d["chua_ai_thu"] > d["te"], "nguon moi khong con duoc tham do"


def test_nguon_chua_thu_lay_SUAT_TOAN_HE_khong_phai_hang_so():
    from tru import seeker as S
    d = S._cham_theo_prior_that({"a": 200}, {"a": 20})
    assert abs(d.mac_dinh - 0.10) < 1e-9, d.mac_dinh
    assert d["ten_la_hoac"] == d.mac_dinh, "khong dung __missing__"


def test_cho_goi_dung___missing___chu_khong_get_voi_hang_so():
    """`.get(ng, 0.5)` bo qua `__missing__` - sua mot dau thi hong dau kia."""
    from pathlib import Path as _P
    s = (_P(__file__).resolve().parent / "tru" / "seeker.py").read_text(
        encoding="utf-8-sig")
    assert 'diem_ns.get(' not in s, (
        "van con `.get()` voi hang so mac dinh - `__missing__` se bi bo qua")
    assert "-diem_ns[t[" in s
