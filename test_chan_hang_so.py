# -*- coding: utf-8 -*-
"""HAI KIEU HANG SO TRA HINH, VA CHUNG HONG THEO HAI CHIEU NGUOC NHAU.

Do tren kho 06/09/2026, ca hai deu la dau vet cua mot lan boc HONG chu khong
phai co che that:

  1. `close > 0`, `low < 0`, `high >= 0` - **27 ve tren 12 co che**, gan het
     thuoc ho FVG / order block / liquidity sweep. Bo boc nhin thay
     `if(cond) Buffer[i] = low[i] - 10*_Point;` roi dien `hang: 0` vao cho
     nguong ma no khong doc duoc. Gia luon duong, nen ve nay la HANG SO.
  2. `close >= 325.25` - mot muc gia cua MOT tai san tai MOT thoi diem. Dung o
     do, va la hang so `False` o moi noi khac.

Chieu hong khac nhau, va do la ly do phai chan ca hai:

  - Ve LUON SAI thi pheu BAT DUOC (`gan_khong_bao_gio_vao`) - on ao nhung an
    toan.
  - Ve LUON DUNG thi **im lang bien mat**: co che van chay, van co ve co du
    dieu kien, va khong ai biet minh dang kiem dinh mot thu KHAC voi cai ban
    goc noi. Dung ho benh [[ket-luan-am-phai-phan-biet-chua-do]].

Bay rieng cua bai nay: `_hang_so_gia` **da ton tai tu 05/09** va `don_kho` co
goi no - nhung `don_kho` chi bao cao, con `loc()`, cai duy nhat nam tren duong
len be mat, thi khong goi bao gio. Nen bai kiem phai bam vao `loc()`, khong
duoc bam vao ham chan; ham chan xanh khong chung minh duoc gi
[[noi-day-truoc-khi-xay-them]].
"""
import unittest

from nhan import loc_co_che as LCC
from nhan import ngu_phap as NP


def _ve(trai, phep, phai):
    return {"trai": trai, "phep": phep, "phai": phai}


GIA = {"chi_bao": "gia", "cot": "close"}


class GiaSoVoiHangSoAmHoacKhongLaHangSo(unittest.TestCase):

    def test_luon_dung_bi_chan(self):
        self.assertTrue(NP._kiem_hien_nhien(_ve(GIA, ">", {"hang": 0})))

    def test_luon_sai_bi_chan(self):
        self.assertTrue(NP._kiem_hien_nhien(
            _ve({"chi_bao": "gia", "cot": "low"}, "<", {"hang": 0})))

    def test_hang_so_am_cung_bi_chan(self):
        self.assertTrue(NP._kiem_hien_nhien(_ve(GIA, ">", {"hang": -10})))

    def test_nguong_DUONG_khong_bi_ham_nay_dung_toi(self):
        """`close > 322.5` la mot benh KHAC (nguong tuyet doi), va no do
        `loc_co_che._hang_so_gia` chan. Chan hai lan o hai cho voi hai ly do
        khac nhau thi ly do bao ra se sai mot trong hai lan."""
        self.assertEqual(NP._kiem_hien_nhien(_ve(GIA, ">", {"hang": 322.5})), [])

    def test_chi_bao_CO_THE_am_thi_khong_bi_cham(self):
        """`zscore < 0` va `doi_pct > 0` la dieu kien THAT - chung nhan gia tri
        hai dau. Chan bua o day se giet ca ho quay ve trung binh."""
        for cb in ("zscore", "doi_pct", "doi"):
            t = {"chi_bao": cb, "cua": GIA, "n": 20}
            self.assertEqual(NP._kiem_hien_nhien(_ve(t, "<", {"hang": 0})), [],
                             "chan nham '%s < 0'" % cb)

    def test_cong_them_co_che_tu_choi_spec_kieu_nay(self):
        spec = {"ten": "thu", "ho": "pha_vo", "chieu": 1, "giu": 1,
                "co_che": "mot cau du dai de qua duoc cong kiem khai bao.",
                "vao": [_ve({"chi_bao": "gia", "cot": "low"}, "<", {"hang": 0})]}
        self.assertTrue(NP.kiem_khai_bao(spec))


class LocPhaiChanNguongGiaTuyetDoi(unittest.TestCase):
    """Bam vao `loc()` chu khong vao `_hang_so_gia` - xem docstring dau file."""

    def test_ham_chan_nhan_dien_dung(self):
        self.assertEqual(
            LCC._hang_so_gia({"vao": [_ve(GIA, ">=", {"hang": 325.25})]}),
            325.25)
        self.assertIsNone(
            LCC._hang_so_gia({"vao": [_ve({"chi_bao": "rsi", "n": 14}, "<",
                                          {"hang": 30})]}))

    def test_loc_that_su_go_co_che_do_khoi_be_mat(self):
        kho = NP.doc_kho()
        dinh = [c["ten"] for c in kho if LCC._hang_so_gia(c) is not None]
        if not dinh:
            self.skipTest("kho khong con co che nao so gia voi hang so tuyet doi")
        r = LCC.loc(khung="D1", in_ra=lambda *_: None)
        if r.get("chua_do"):
            self.skipTest("khong nap duoc tai san nao de loc")
        for ten in dinh:
            self.assertNotIn(ten, r["dung_duoc"],
                             "'%s' van len be mat du co nguong gia tuyet doi" % ten)
            self.assertEqual(r["bo"].get(ten), "nguong_gia_tuyet_doi")

    def test_ly_do_bo_la_khoa_ON_DINH_khong_kem_con_so(self):
        """Nhet gia tri vao ly do thi moi co che thanh mot nhom rieng trong
        bang dem, va bang doc nhu the moi cai la mot benh khac nhau."""
        r = LCC.loc(khung="D1", in_ra=lambda *_: None)
        if r.get("chua_do"):
            self.skipTest("khong nap duoc tai san nao de loc")
        for v in r["bo"].values():
            self.assertNotIn("(", v, "ly_do '%s' co nhung con so thay doi" % v)


class CongPhaiApChoCA_HANG_DA_VAO_KHO(unittest.TestCase):
    """Mot cong chi ap cho hang MOI thi khong phai cong, ma la thu tuc nhap kho.

    Do 06/09: 169/540 muc trong kho khong qua noi `kiem_khai_bao` - phan lon
    thieu han truong `co_che`. Chung vao qua cua sau (duong LLM ghi thang file
    JSON) va van chay tren be mat, vi `loc()` chua bao gio goi cong.
    """

    def test_spec_thieu_co_che_khong_len_be_mat(self):
        kho = NP.doc_kho()
        thieu = [c["ten"] for c in kho
                 if NP.kiem_khai_bao(c) and LCC._hang_so_gia(c) is None]
        if not thieu:
            self.skipTest("kho da sach - moi muc deu qua duoc kiem_khai_bao")
        r = LCC.loc(khung="D1", in_ra=lambda *_: None)
        if r.get("chua_do"):
            self.skipTest("khong nap duoc tai san nao de loc")
        for ten in thieu:
            self.assertNotIn(ten, r["dung_duoc"])
            self.assertEqual(r["bo"].get(ten), "khong_qua_kiem_khai_bao")

    def test_mau_viet_tay_khong_bi_cong_nay_cham(self):
        """18 mau goc la ham Python, khong co spec trong kho. Doi chung qua
        `kiem_khai_bao` la doi mot thu khong ton tai."""
        r = LCC.loc(khung="D1", in_ra=lambda *_: None)
        if r.get("chua_do"):
            self.skipTest("khong nap duoc tai san nao de loc")
        for ten in ("ibs_bat_day", "momentum_ema", "donchian"):
            self.assertNotEqual(r["bo"].get(ten), "khong_qua_kiem_khai_bao",
                                "'%s' la mau viet tay, khong co spec" % ten)


class CONG_PHAI_NAM_O_CUA(unittest.TestCase):
    """`loc()` khong phai cua duy nhat vao `MAU.MAU`.

    Sua 06/09 lan mot dat cong o `loc_co_che.loc`. Nhung `do_on_dinh`,
    `hinh_dang_vs_null`, `cham_lai_the_he`, `ngoai_sinh`, `p_null_vs_ung_vien`
    deu goi thang `nap_vao_mau` roi doc `MAU.MAU` - nen mot co che khong co
    truong `co_che` van duoc cham lai diem, van duoc do lan can "cao nguyen hay
    cai gai", van duoc dem trong nha may null. Chan o hai cho voi hai danh sach
    thi som muon se lech nhau; cong phai nam o CUA.
    """

    def test_nap_vao_mau_tu_choi_spec_khong_qua_cong(self):
        """CHAY TREN KHO TAM, khong bao gio tren kho THAT.

        Ban truoc cua bai kiem nay lam dung nhu vay: `goc = NP.doc_kho()` ->
        `NP.luu_kho(goc + [hong])` -> `finally: NP.luu_kho(goc)` tren kho
        SAN XUAT. No la mot trong hai nguyen nhan lam kho tut 2.975 -> 21 ngay
        13/09/2026:

          * chay 6 nhan song song thi hai nhan cung doc-sua-ghi mot file;
          * neu mot lan `doc_kho()` hong (dia day -> `paging file too small`),
            `goc` thanh `[]` va `finally` GHI DE ca kho bang danh sach rong;
          * va ke ca khi khong hong, mot lan `finally` khong chay (tien trinh
            bi giet) de lai `thu_khong_co_co_che` nam trong kho that - dung cai
            lam bai kiem `test_khong_con_khai_bao_truot_chi_vi_co_che` do.

        Bai kiem khong duoc sua du lieu san xuat. Do la luat, khong phai gu.
        """
        import json
        import tempfile
        from pathlib import Path as _P
        from nhan import mau as MAU
        MAU.MAU.pop("thu_khong_co_co_che", None)
        goc = NP.doc_kho()
        hong = {"ten": "thu_khong_co_co_che", "ho": "pha_vo", "chieu": 1,
                "giu": 1, "vao": [_ve(GIA, ">", {"chi_bao": "gia",
                                                 "cot": "open"})]}
        kho_that, moc_that = NP.KHO_CO_CHE, NP.MOC_CAO
        with tempfile.TemporaryDirectory() as tm:
            f = _P(tm) / "co_che_dsl.json"
            f.write_text(json.dumps(goc + [hong], ensure_ascii=False),
                         encoding="utf-8")
            NP.KHO_CO_CHE, NP.MOC_CAO = f, f.with_suffix(".moc_cao")
            try:
                NP.nap_vao_mau()
                self.assertNotIn("thu_khong_co_co_che", MAU.MAU,
                                 "spec thieu 'co_che' van vao duoc MAU.MAU")
                self.assertIn("thu_khong_co_co_che", NP.BI_TU_CHOI_KHI_NAP)
            finally:
                NP.KHO_CO_CHE, NP.MOC_CAO = kho_that, moc_that
                MAU.MAU.pop("thu_khong_co_co_che", None)

    def test_ban_ghi_tu_choi_khong_bi_vut_di(self):
        """Mot muc bi tu choi im lang thi khong ai biet kho vua nho di, va con
        so '540 co che' van duoc doc nhu 540 phep thu."""
        NP.nap_vao_mau()
        self.assertIsInstance(NP.BI_TU_CHOI_KHI_NAP, dict)
        kho = NP.doc_kho()
        dung = sum(1 for c in kho if NP.kiem_khai_bao(c))
        self.assertEqual(len(NP.BI_TU_CHOI_KHI_NAP), dung,
                         "so muc bi tu choi khong khop so muc truot cong")

    def test_kiem_cong_False_chi_de_DO_DAC(self):
        from nhan import mau as MAU
        MAU.MAU.clear()
        import importlib
        importlib.reload(MAU)
        n_co_cong = NP.nap_vao_mau()
        MAU.MAU.clear()
        importlib.reload(MAU)
        n_khong_cong = NP.nap_vao_mau(kiem_cong=False)
        self.assertGreater(n_khong_cong, n_co_cong,
                           "tat cong ma so nap khong tang -> cong khong lam gi")


class KHO_KHONG_DUOC_CHUA_HANG_CHET(unittest.TestCase):
    """Mot khai bao truot `kiem_khai_bao` thi KHONG BAO GIO vao duoc cong.

    Do 12/09/2026: 166/1.418 co che trong kho truot cong cua CHINH NO, va 122
    trong so do truot chi vi **thieu truong `co_che`** - mot lo metadata, khong
    phai loi logic. Chung nam trong kho nhu hang chet tu truoc 05/09 (luc
    `boc_ma_llm._dien_co_che` ra doi), va khong bai kiem nao gac.

    Bai kiem nay chia hai loai va gac tung loai khac nhau:

      METADATA (chi thieu/hong `co_che`)  -> phai bang 0. Dien bu duoc bang may
                                             (`_va_co_che_thieu.py`), khong co
                                             ly do de ton tai.
      NOI DUNG (dieu kien hang dung, hai  -> duoc phep ton tai nhung KHONG DUOC
                ve giong het, thieu `vao`)   TANG. Do la loi cua khau BOC; chan
                                             tran de no khong am tham phinh.
    """

    #: Tran hang loi NOI DUNG, chot theo so do duoc 12/09/2026. Ha duoc thi ha,
    #: nhung khong duoc nang ma khong co ly do ghi kem.
    TRAN_LOI_NOI_DUNG = 44

    def _phan_loai(self):
        from nhan import ngu_phap as NP
        meta, noi_dung = [], []
        for s in NP.doc_kho():
            loi = NP.kiem_khai_bao(s)
            if not loi:
                continue
            (meta if all("co_che" in x for x in loi) else noi_dung).append(
                (s.get("ten"), loi))
        return meta, noi_dung

    def test_khong_con_khai_bao_truot_chi_vi_co_che(self):
        meta, _ = self._phan_loai()
        self.assertEqual(
            [t for t, _ in meta][:20], [],
            "%d khai bao truot cong CHI vi thieu `co_che` - chay "
            "`python _va_co_che_thieu.py --that`" % len(meta))

    def test_loi_noi_dung_khong_duoc_tang(self):
        _, nd = self._phan_loai()
        self.assertLessEqual(
            len(nd), self.TRAN_LOI_NOI_DUNG,
            "hang loi NOI DUNG tang tu %d len %d - khau BOC dang sinh them "
            "dieu kien vo nghia (hang dung, hai ve giong het, thieu `vao`). "
            "Vi du: %s" % (self.TRAN_LOI_NOI_DUNG, len(nd),
                           [t for t, _ in nd[:3]]))


if __name__ == "__main__":
    unittest.main()
