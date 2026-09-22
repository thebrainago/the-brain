# -*- coding: utf-8 -*-
"""CAU NOI HAI MAY: git la duong truyen duy nhat (20/09/2026).

Chu du an: *"vấn đề là làm sao để phiên chat này đọc được kết quả chạy trên máy
tính tôi"*. Cau tra loi: qua git, va `qwen/cau_git.py` la cai cau do.

## VI SAO BO BAI NAY PHAI DUNG REPO THAT

May chu du an TAT luc viet bo nay. Mot bai kiem gia lap bang mock se chung
minh duoc dung mot dieu: cac ham goi nhau dung thu tu. No khong noi gi ve viec
`git` co that su cho don di qua khong - ma do moi la cau hoi.

Nen moi bai o day dung **mot repo bare + hai ban clone that**, chay `git` that.
Mot vong day du:

    CLOUD ghi don -> push -> MAY pull -> thay don -> ghi ket qua -> push
    -> CLOUD pull -> doc duoc ket qua

Chua di het vong do thi cau chua ton tai.

## MODULE NAY TU CHAY `git` TREN MAY NGUOI KHAC

Nen ba bai an toan o `AnToan` quan trong ngang bai vong doi:
khong `add -A`, khong vut viec local, khong `push --force`.
"""
from __future__ import annotations

import json
import subprocess
import time
import tempfile
import unittest
from pathlib import Path

from qwen import cau_git as CG


def _git(goc, *doi):
    r = subprocess.run(["git", *doi], cwd=str(goc), capture_output=True, text=True)
    assert r.returncode == 0, "git %s: %s" % (" ".join(doi), r.stderr)
    return r.stdout.strip()


class NenHaiMay(unittest.TestCase):
    """Dung mot repo bare + hai clone: `cloud` va `may`."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        goc = Path(self.tmp.name)
        self.bare = goc / "trung_tam.git"
        subprocess.run(["git", "init", "--bare", "-b", "main", str(self.bare)],
                       check=True, capture_output=True)
        self.cloud, self.may = goc / "cloud", goc / "may"
        for p in (self.cloud, self.may):
            subprocess.run(["git", "clone", str(self.bare), str(p)],
                           check=True, capture_output=True)
            _git(p, "config", "user.email", "t@t.t")
            _git(p, "config", "user.name", "t")
        # Mot commit dau de hai ban co chung goc.
        CG.bao_dam_thu_muc(goc=self.cloud)
        (self.cloud / "README.md").write_text("x", encoding="utf-8")
        _git(self.cloud, "add", "-A")
        _git(self.cloud, "commit", "-m", "dau")
        _git(self.cloud, "push", "origin", "HEAD:main")
        _git(self.may, "fetch", "origin", "main")
        _git(self.may, "merge", "--ff-only", "FETCH_HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def _ra_don(self, ma="don-thu", **kw):
        """CLOUD ra mot don va day len."""
        CG.bao_dam_thu_muc(goc=self.cloud)
        d = {"ma": ma, "loai": "lenh", "muc_tieu": "thu vong", **kw}
        (self.cloud / "viec" / "cho" / ("%s.json" % ma)).write_text(
            json.dumps(d, ensure_ascii=False), encoding="utf-8")
        _git(self.cloud, "add", "-A")
        _git(self.cloud, "commit", "-m", "cloud: don %s" % ma)
        _git(self.cloud, "push", "origin", "HEAD:main")
        return d


class VongDayDu(NenHaiMay):
    def test_don_di_het_vong_cloud_may_cloud(self):
        self._ra_don("don-a")

        # --- ben MAY ---
        r = CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        self.assertEqual(r["trang_thai"], "DAT", r)
        self.assertTrue(r["keo"]["da_keo"], r)

        cho = CG.don_dang_cho(goc=self.may)
        self.assertEqual([d["ma"] for d in cho], ["don-a"],
                         "may khong nhan duoc don sau khi dong bo")

        CG.ghi_ket_qua("don-a", "DAT", "chay xong",
                       bang_chung={"ma_thoat": 0}, so_do={"lai_pct_nam": 13.26},
                       goc=self.may)
        r2 = CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        self.assertEqual(r2["trang_thai"], "DAT", r2)
        self.assertTrue(r2["day"]["da_day"], r2)

        # --- ben CLOUD ---
        # TRUOC khi keo, cloud phai thay CHUA_DO_DUOC chu khong phai AM.
        truoc = CG.doc_ket_qua("don-a", goc=self.cloud)
        self.assertEqual(truoc["trang_thai"], "CHUA_DO_DUOC", truoc)

        r3 = CG.dong_bo(nhanh="main", ep=True, goc=self.cloud)
        self.assertEqual(r3["trang_thai"], "DAT", r3)
        sau = CG.doc_ket_qua("don-a", goc=self.cloud)
        self.assertEqual(sau["trang_thai"], "DAT", sau)
        self.assertEqual(sau["so_do"]["lai_pct_nam"], 13.26)
        self.assertIn("may", sau, "ket qua khong ghi may nao chay")

    def test_HIEU_CHUAN_NGUOC_may_khong_day_thi_cloud_KHONG_thay(self):
        """Neu bai tren xanh ke ca khi cau hong thi no vo nghia.

        Cho may ghi ket qua nhung KHONG dong bo: cloud phai van thay
        CHUA_DO_DUOC. Bai nay chung minh bai tren dang do duong truyen that
        chu khong do he thong file dung chung.
        """
        self._ra_don("don-b")
        CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        CG.ghi_ket_qua("don-b", "DAT", "chay xong", goc=self.may)
        CG.dong_bo(nhanh="main", ep=True, goc=self.cloud)
        kq = CG.doc_ket_qua("don-b", goc=self.cloud)
        self.assertEqual(kq["trang_thai"], "CHUA_DO_DUOC", kq)

    def test_leo_thang_can_cloud_di_nguoc_ve(self):
        self._ra_don("don-c")
        CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        CG.ghi_ket_qua("don-c", "CHUA_DO_DUOC", "thieu du lieu",
                       can_cloud=True, cau_hoi="Dung khung H4 hay H1?",
                       goc=self.may)
        CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        CG.dong_bo(nhanh="main", ep=True, goc=self.cloud)
        hoi = CG.cho_cloud(goc=self.cloud)
        self.assertEqual([h["ma"] for h in hoi], ["don-c"], hoi)
        self.assertIn("H4", hoi[0]["cau_hoi"])

    def test_don_da_co_ket_qua_thi_KHONG_lam_lai(self):
        """Slot TESTER la thu hiem nhat trong he - khong duoc dot lai."""
        self._ra_don("don-d")
        CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        self.assertEqual(len(CG.don_dang_cho(goc=self.may)), 1)
        CG.ghi_ket_qua("don-d", "AM", "khong vuot nguong", goc=self.may)
        self.assertEqual(CG.don_dang_cho(goc=self.may), [],
                         "don da co ket qua ma van nam trong hang cho")


class AnToan(NenHaiMay):
    """Ba luat an toan cua mot module TU CHAY `git` tren may nguoi khac."""

    def test_KHONG_day_file_ngoai_danh_sach_trang(self):
        """`git add -A` tu dong se cuon ca viec dang lam cua chu du an len.

        Do la ly do `_day` chi `add` tung duong trong `DUOC_DAY`.
        """
        (self.may / "dang_viet_do.py").write_text("# chua xong", encoding="utf-8")
        (self.may / "config").mkdir(exist_ok=True)
        (self.may / "config" / "qwen.json").write_text("{}", encoding="utf-8")
        CG.ghi_ket_qua("don-e", "DAT", "x", goc=self.may)
        r = CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        self.assertEqual(r["trang_thai"], "DAT", r)

        _git(self.cloud, "fetch", "origin", "main")
        cay = _git(self.cloud, "ls-tree", "-r", "--name-only", "FETCH_HEAD")
        self.assertIn("viec/xong/don-e.json", cay)
        self.assertNotIn("dang_viet_do.py", cay,
                         "da day mot file NGOAI danh sach trang len remote")
        self.assertNotIn("config/qwen.json", cay,
                         "da day config/ len - quy tac phien cam dieu nay")

    def test_viec_nguoi_do_dang_thi_KHONG_keo_de_khoi_vut(self):
        """Khong `stash`, khong `reset --hard`. Do dang thi bao va di tiep."""
        (self.may / "README.md").write_text("nguoi dang sua", encoding="utf-8")
        r = CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        self.assertFalse(r["keo"]["da_keo"], r)
        self.assertIn("README.md", r["viec_nguoi_do_dang"])
        self.assertEqual((self.may / "README.md").read_text(encoding="utf-8"),
                         "nguoi dang sua", "da vut mat viec local")

    def test_nhanh_da_RE_thi_CHUA_DO_DUOC_chu_khong_merge_tu_dong(self):
        """`--ff-only` that bai co chu dich: mot merge tu dong luc 3 gio sang,
        khong ai nhin, tren cay co viec do dang la cach nhanh nhat de mat viec."""
        # cloud di truoc mot commit
        (self.cloud / "a.txt").write_text("1", encoding="utf-8")
        _git(self.cloud, "add", "-A"); _git(self.cloud, "commit", "-m", "cloud")
        _git(self.cloud, "push", "origin", "HEAD:main")
        # may cung di mot commit KHAC -> hai nhanh re
        (self.may / "b.txt").write_text("2", encoding="utf-8")
        _git(self.may, "add", "-A"); _git(self.may, "commit", "-m", "may")
        truoc = _git(self.may, "rev-parse", "HEAD")

        r = CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC", r)
        self.assertIn("re", r["ly_do"].lower())
        self.assertEqual(_git(self.may, "rev-parse", "HEAD"), truoc,
                         "lich su local bi doi khi hai nhanh re")

    def test_doc_dung_DUONG_DAN_du_o_dong_dau_hay_ten_co_dau_cach(self):
        """Khoa lai loi da sap khi viet bo bai nay (20/09/2026).

        `_git` cu luon `.strip()` ca stdout. `git status --porcelain` in
        `XY<cach>DUONG`, nen mot file BI SUA ra ` M README.md` co dau cach dan
        dau - va `.strip()` tren ca chuoi chi an dau cach cua **dong dau**.
        Ket qua: dong dau bi cat lech mot ky tu (`README.md` -> `EADME.md`),
        cac dong sau thi dung. Khong nem loi, khong sai ro rang - chi doc ra
        mot duong dan LECH, roi `dong_bo` quyet dinh sai xem co duoc keo khong.

        Bai nay do ba hinh dang cung luc: file SUA (co cach dan dau, nam dong
        dau), file MOI (`??`), va ten CO DAU CACH (ban `--porcelain` thuong se
        trich dan thanh `"a b.txt"`).
        """
        (self.may / "README.md").write_text("sua", encoding="utf-8")   # ' M '
        (self.may / "moi tinh.txt").write_text("x", encoding="utf-8")  # '?? ' + cach
        (self.may / "moi2.txt").write_text("x", encoding="utf-8")
        d = CG.co_viec_chua_commit(goc=self.may)
        self.assertIn("README.md", d, d)
        self.assertIn("moi tinh.txt", d, d)
        self.assertIn("moi2.txt", d, d)
        for x in d:
            self.assertFalse(x.startswith(('"', " ")), "duong dan chua go sach: %r" % x)
            self.assertTrue((self.may / x).exists(), "duong dan khong ton tai: %r" % x)

    def test_doi_ten_khong_bi_doc_thanh_hai_muc(self):
        """`R` an THEM mot ban ghi la ten cu - khong nhay qua thi ten cu bi
        doc thanh mot muc do dang rieng, va `dong_bo` se tu chan chinh no."""
        _git(self.may, "mv", "README.md", "DOC_TOI.md")
        d = CG.co_viec_chua_commit(goc=self.may)
        self.assertIn("DOC_TOI.md", d, d)
        for x in d:
            self.assertTrue((self.may / x).exists(),
                            "doc ra mot duong khong ton tai (ten cu?): %r" % x)

    def test_mat_mang_la_CHUA_DO_DUOC_chu_khong_nem_ra_vong_q(self):
        """Mot loi mang khong duoc phep giet mot dot chay nhieu ngay."""
        _git(self.may, "remote", "set-url", "origin",
             str(Path(self.tmp.name) / "khong_ton_tai.git"))
        r = CG.dong_bo(nhanh="main", ep=True, goc=self.may)
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC", r)
        self.assertTrue(r["ly_do"])


class BaTrangThai(unittest.TestCase):
    """LUAT SO 0 o cho nay: THIEU ket qua KHAC ket qua AM."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.goc = Path(self.tmp.name)
        CG.bao_dam_thu_muc(goc=self.goc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_chua_co_file_la_CHUA_DO_DUOC(self):
        self.assertEqual(CG.doc_ket_qua("x", goc=self.goc)["trang_thai"],
                         "CHUA_DO_DUOC")

    def test_json_hong_la_CHUA_DO_DUOC_chu_khong_nem(self):
        (self.goc / "viec" / "xong" / "y.json").write_text(
            '{"ma": "y", "trang', encoding="utf-8")
        self.assertEqual(CG.doc_ket_qua("y", goc=self.goc)["trang_thai"],
                         "CHUA_DO_DUOC")

    def test_trang_thai_LA_bi_ha_xuong_CHUA_DO_DUOC_chu_khong_di_tiep(self):
        """Mot chu la (`OK`, `PASS`, `true`) khong duoc lot qua thanh DAT."""
        for la in ("OK", "PASS", "true", "", None, 1):
            (self.goc / "viec" / "xong" / "z.json").write_text(
                json.dumps({"ma": "z", "trang_thai": la}), encoding="utf-8")
            d = CG.doc_ket_qua("z", goc=self.goc)
            self.assertEqual(d["trang_thai"], "CHUA_DO_DUOC", la)
            self.assertIn("goc", d, "mat ban goc khi ha xuong CHUA_DO_DUOC")

    def test_ghi_trang_thai_LA_thi_NEM_chu_khong_lang_le_ghi(self):
        for la in ("OK", "PASS", "dat", ""):
            with self.assertRaises(ValueError, msg=la):
                CG.ghi_ket_qua("w", la, goc=self.goc)

    def test_HIEU_CHUAN_NGUOC_ba_chu_dung_thi_van_di_qua(self):
        """Mot cong tu choi TAT CA cho so lieu y het mot cong tot."""
        for t in CG.TRANG_THAI:
            CG.ghi_ket_qua("v", t, goc=self.goc)
            self.assertEqual(CG.doc_ket_qua("v", goc=self.goc)["trang_thai"], t)

    def test_ghi_NGUYEN_TU_khong_de_lai_file_viet_do_dang(self):
        """`q` bi Ctrl-C giua chung khong duoc lam mat mot ket qua that."""
        CG.ghi_ket_qua("u", "DAT", "x" * 5000, goc=self.goc)
        tam = list((self.goc / "viec" / "xong").glob("*.tam"))
        self.assertEqual(tam, [], "con sot file tam")
        self.assertEqual(CG.doc_ket_qua("u", goc=self.goc)["trang_thai"], "DAT")

    def test_tom_tat_dem_rieng_trang_thai_la(self):
        CG.ghi_ket_qua("a", "DAT", goc=self.goc)
        CG.ghi_ket_qua("b", "AM", goc=self.goc)
        CG.ghi_ket_qua("c", "CHUA_DO_DUOC", goc=self.goc)
        (self.goc / "viec" / "xong" / "d.json").write_text(
            json.dumps({"ma": "d", "trang_thai": "OK"}), encoding="utf-8")
        t = CG.tom_tat(goc=self.goc)
        self.assertEqual((t["DAT"], t["AM"], t["CHUA_DO_DUOC"]), (1, 1, 1), t)
        self.assertEqual(t["trang_thai_la"], 1, t)


if __name__ == "__main__":
    unittest.main()


class RaDon(unittest.TestCase):
    """Ben CLOUD ra don. Cho de nhat lam hong ca he bang mot chu go sai."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.goc = Path(self.tmp.name)
        CG.bao_dam_thu_muc(goc=self.goc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_lan_SAI_thi_nem_chu_khong_lang_le_ghi(self):
        """`lan` quyet dinh may co chay trung slot TESTER khong. Mot chu go sai
        khong lo ra o dau ca cho toi luc hai viec tester ghi de ket qua cua
        nhau - va CLAUDE.md ghi ro luc do KHONG AI BAO LOI."""
        for la in ("tester", "Tester", "CPU ", "", "GPU"):
            with self.assertRaises(ValueError, msg=la):
                CG.ra_don("x", "y", lan=la, goc=self.goc)

    def test_HIEU_CHUAN_NGUOC_nam_lan_hop_le_deu_di_qua(self):
        for l in CG.LAN:
            p = CG.ra_don("don-%s" % l.lower(), "thu", lan=l, goc=self.goc)
            self.assertTrue(p.exists())

    def test_file_test_nam_trong_duoc_sua_thi_NEM(self):
        """Bai test la DAC TA. Cho no vao `duoc_sua` la cho pha dac ta de lam
        xanh bang so."""
        with self.assertRaises(ValueError):
            CG.ra_don("z", "y", file_test="test_a.py",
                      duoc_sua=["nhan/a.py", "test_a.py"], goc=self.goc)

    def test_ma_co_dau_gach_thi_NEM(self):
        """`ma` di thang vao ten file - `../` se ghi ra ngoai thu muc viec."""
        for la in ("", "a/b", "..\\c", "../x"):
            with self.assertRaises(ValueError, msg=la):
                CG.ra_don(la, "y", goc=self.goc)

    def test_don_ra_roi_thi_doc_lai_duoc_va_xep_theo_uu_tien(self):
        CG.ra_don("sau", "b", uu_tien=9, goc=self.goc)
        CG.ra_don("truoc", "a", uu_tien=1, goc=self.goc)
        self.assertEqual([d["ma"] for d in CG.don_dang_cho(goc=self.goc)],
                         ["truoc", "sau"])


class ChamDon(unittest.TestCase):
    """CHAM bang CODE, va ma thoat != 0 KHONG mac nhien la AM.

    `qwen/DOC_TRUOC.md`: *"Ma thoat != 0 ... deu la CHUA_DO_DUOC, khong bao
    gio la AM."* Nhung `pytest` la ngoai le co that: ma thoat **1** nghia la
    bai chay duoc va co bai do - mot ket qua DO DUOC. Gop hai cai lam mot thi
    mot loi cu phap trong file test doc ra thanh "co che khong ra tien".
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.goc = Path(self.tmp.name)
        CG.bao_dam_thu_muc(goc=self.goc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pytest_thoat_1_la_AM_con_2_tro_len_la_CHUA_DO_DUOC(self):
        self.assertEqual(CG._cham("pytest", 0, False)[0], "DAT")
        self.assertEqual(CG._cham("pytest", 1, False)[0], "AM")
        for m in (2, 3, 4, 5):
            self.assertEqual(CG._cham("pytest", m, False)[0], "CHUA_DO_DUOC", m)

    def test_chay_duoc_thi_moi_ma_thoat_khac_0_deu_CHUA_DO_DUOC(self):
        self.assertEqual(CG._cham("chay_duoc", 0, False)[0], "DAT")
        for m in (1, 2, -9, 127):
            self.assertEqual(CG._cham("chay_duoc", m, False)[0], "CHUA_DO_DUOC", m)

    def test_khong_khai_kieu_thi_CHUA_DO_DUOC_ke_ca_khi_ma_thoat_0(self):
        """Mac dinh phai la 'chua noi duoc gi', khong phai 'dat'."""
        self.assertEqual(CG._cham("", 0, False)[0], "CHUA_DO_DUOC")
        self.assertEqual(CG._cham("la_hoac", 0, False)[0], "CHUA_DO_DUOC")

    def test_qua_gio_la_CHUA_DO_DUOC_du_kieu_nao(self):
        for k in ("pytest", "chay_duoc", ""):
            self.assertEqual(CG._cham(k, 0, True)[0], "CHUA_DO_DUOC", k)

    def test_chay_THAT_mot_don_va_ghi_ket_qua(self):
        CG.ra_don("ok", "in ra", lenh=["python3", "-c", "print('xin chao')"],
                  cong="chay_duoc", goc=self.goc)
        d = CG.don_dang_cho(goc=self.goc)[0]
        d["cong"] = {"kieu": "chay_duoc"}
        r = CG.chay_don(d, goc=self.goc)
        self.assertEqual(r["trang_thai"], "DAT", r)
        self.assertIn("xin chao", "\n".join(r["bang_chung"]["dong_cuoi"]))
        self.assertEqual(CG.doc_ket_qua("ok", goc=self.goc)["trang_thai"], "DAT")

    def test_lenh_hong_KHONG_lam_q_nem_ma_thanh_ket_qua_tren_dia(self):
        CG.ra_don("hong", "chay thu", lenh=["khong_co_lenh_nay_xyz"],
                  cong="chay_duoc", goc=self.goc)
        d = CG.don_dang_cho(goc=self.goc)[0]
        d["cong"] = {"kieu": "chay_duoc"}
        r = CG.chay_don(d, goc=self.goc)
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC", r)
        self.assertTrue((self.goc / "viec" / "xong" / "hong.json").exists(),
                        "loi khong duoc ghi xuong dia - cloud se khong bao gio biet")

    def test_don_KHONG_CO_LENH_la_CHUA_DO_DUOC_chu_khong_im(self):
        CG.ra_don("rong", "khong lam gi", goc=self.goc)
        r = CG.chay_don(CG.don_dang_cho(goc=self.goc)[0], goc=self.goc)
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC", r)

    def test_khoa_TESTER_chan_don_thu_hai(self):
        """Mot `terminal64.exe` la rang buoc VAT LY. Hai viec tester cung luc
        ghi de ket qua cua nhau VA KHONG AI BAO LOI."""
        CG.ra_don("t1", "tester", lenh=["python3", "-c", "pass"], lan="TESTER",
                  uu_tien=1, cong="chay_duoc", goc=self.goc)
        CG.ra_don("t2", "tester", lenh=["python3", "-c", "pass"], lan="TESTER",
                  uu_tien=2, cong="chay_duoc", goc=self.goc)
        self.assertTrue(CG._lay_khoa(self.goc / "viec"))
        r = CG.chay_don(CG.don_dang_cho(goc=self.goc)[0], goc=self.goc)
        self.assertTrue(r.get("hoan"), r)
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC", r)
        # va `chay_mot_don_dang_cho` phai NHAY QUA chu khong dung ca hang doi
        CG.ra_don("nhe", "viec nhe", lenh=["python3", "-c", "pass"], lan="NHE",
                  uu_tien=9, cong="chay_duoc", goc=self.goc)
        r2 = CG.chay_mot_don_dang_cho(goc=self.goc)
        self.assertEqual(r2["ma"], "nhe",
                         "don TESTER dang ban lai chan ca cac don NHE phia sau")

    def test_khoa_CU_duoc_coi_la_da_chet(self):
        """Mot lan tat may giua chung khong duoc lam ket lan TESTER vinh vien."""
        k = self.goc / "viec" / ".khoa_tester"
        k.write_text("999999", encoding="utf-8")
        import os as _os
        cu = time.time() - CG.KHOA_CU_GIAY - 60
        _os.utime(k, (cu, cu))
        self.assertTrue(CG._lay_khoa(self.goc / "viec"),
                        "khoa cu van chan - mot lan tat may lam ket lan TESTER")

    def test_khoa_duoc_TRA_LAI_sau_khi_don_chay_xong(self):
        CG.ra_don("t", "x", lenh=["python3", "-c", "pass"], lan="TESTER",
                  cong="chay_duoc", goc=self.goc)
        d = CG.don_dang_cho(goc=self.goc)[0]; d["cong"] = {"kieu": "chay_duoc"}
        CG.chay_don(d, goc=self.goc)
        self.assertFalse((self.goc / "viec" / ".khoa_tester").exists(),
                         "khoa khong duoc tra lai - lan TESTER ket tu vong sau")


class MocVaoVongQ(unittest.TestCase):
    """Cau chi co nghia khi vong `q` THAT SU goi no.

    ## VI SAO KIEM BANG AST CHU KHONG IMPORT

    `qwen/chay.py` keo `qwen/cong_cu.py` -> `langchain_core`, thu vien chi co
    tren may chu du an. Tren cloud no nem `ModuleNotFoundError`, nen mot bai
    kiem kieu `import chay` se luon do o day va luon xanh o kia - tuc khong
    kiem duoc gi ca.

    Doc AST thi khong can import: no tra loi dung cau can hoi - "vong lap co
    goi cau khong" - tren MOI may.
    """

    def setUp(self):
        import ast
        self.cay = ast.parse(Path("qwen/chay.py").read_text(encoding="utf-8"))
        self.ast = ast

    def _lop(self):
        for n in self.ast.walk(self.cay):
            if isinstance(n, self.ast.ClassDef) and n.name == "DieuPhoi":
                return n
        self.fail("khong tim thay lop DieuPhoi")

    def _goi_trong(self, ten_ham):
        for n in self._lop().body:
            if isinstance(n, self.ast.FunctionDef) and n.name == ten_ham:
                return {x.func.attr for x in self.ast.walk(n)
                        if isinstance(x, self.ast.Call)
                        and isinstance(x.func, self.ast.Attribute)}
        self.fail("DieuPhoi khong co ham %s" % ten_ham)

    def test_mot_vong_goi_CA_dong_bo_lan_chay_don(self):
        g = self._goi_trong("mot_vong")
        self.assertIn("dong_bo_git", g, "vong lap khong keo don ve bao gio")
        self.assertIn("chay_don_cloud", g, "keo don ve roi khong ai chay")

    def test_dong_bo_dung_TRUOC_nap_lai_bang(self):
        """`dong_bo` co the keo ve mot `NHIEM_VU.json` moi; `nap_lai_bang`
        ngay sau se nhat duoc no trong CUNG mot vong. Dao thu tu thi don moi
        phai cho them mot vong."""
        for n in self._lop().body:
            if isinstance(n, self.ast.FunctionDef) and n.name == "mot_vong":
                ten = [x.func.attr for x in self.ast.walk(n)
                       if isinstance(x, self.ast.Call)
                       and isinstance(x.func, self.ast.Attribute)]
                self.assertLess(ten.index("dong_bo_git"), ten.index("nap_lai_bang"),
                                "dong bo phai chay TRUOC khi nap lai bang")
                return

    def test_chay_don_dung_LUONG_NEN_chu_khong_chan_vong_lap(self):
        """Mot don `han_phut = 60` goi thang trong `mot_vong` thi suot ngan ay
        phut khong ai thu hoach va khong ai phong viec - CPU ve 0 voi bang
        viec day."""
        self.assertIn("submit", self._goi_trong("chay_don_cloud"),
                      "chay_don_cloud khong dua vao luong nen")


class TheTrongLenh(unittest.TestCase):
    """Don viet tren CLOUD (Linux) phai chay duoc tren MAY (Windows)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.goc = Path(self.tmp.name)
        CG.bao_dam_thu_muc(goc=self.goc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_py_doi_thanh_python_dang_chay(self):
        """May chu du an khong co `python3`, va CLAUDE.md chot Python o do la
        MOT duong dan cu the. Mot don viet cung `python3` se hong tren may voi
        mot ly do khong lien quan gi den noi dung don."""
        import sys
        self.assertEqual(CG._thay_the(["{py}", "-c", "pass"])[0], sys.executable)

    def test_chay_that_bang_the_py(self):
        CG.ra_don("t", "x", lenh=["{py}", "-c", "print('ok')"],
                  cong="chay_duoc", goc=self.goc)
        d = CG.don_dang_cho(goc=self.goc)[0]; d["cong"] = {"kieu": "chay_duoc"}
        r = CG.chay_don(d, goc=self.goc)
        self.assertEqual(r["trang_thai"], "DAT", r)
        self.assertIn("ok", "\n".join(r["bang_chung"]["dong_cuoi"]))

    def test_khong_co_the_thi_giu_nguyen(self):
        self.assertEqual(CG._thay_the(["a", "b"]), ["a", "b"])
        self.assertIsNone(CG._thay_the(None))


class DonPhaiKHAI_CONG(unittest.TestCase):
    """Loi toi tu mac ngay lo don dau tien (20/09/2026).

    Ra sau don khong kem `cong`. `_cham` cham don khong khai kieu la
    `CHUA_DO_DUOC` - dung theo luat, nhung nghia la ca sau don se ve
    `CHUA_DO_DUOC` **bat ke chung chay the nao**. Mot dem may chay het cong
    suat de lay ve sau dong "khong cham duoc".

    Cai bay o day: khong co gi HONG ca. Don hop le, may chay that, ket qua ghi
    that - chi la khong con so nao doc duoc. Nen phai chan luc RA DON.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.goc = Path(self.tmp.name)
        CG.bao_dam_thu_muc(goc=self.goc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_don_co_lenh_ma_khong_khai_cong_thi_NEM(self):
        with self.assertRaises(ValueError) as e:
            CG.ra_don("x", "y", lenh=["{py}", "-c", "pass"], goc=self.goc)
        self.assertIn("CHUA_DO_DUOC", str(e.exception))

    def test_kieu_cong_LA_thi_NEM(self):
        for la in ("pytest3", "chay", "PYTEST", "", {}, {"kieu": "x"}):
            with self.assertRaises(ValueError, msg=la):
                CG.ra_don("x", "y", lenh=["a"], cong=la, goc=self.goc)

    def test_HIEU_CHUAN_NGUOC_kieu_dung_thi_di_qua_va_ghi_vao_don(self):
        import json as _j
        for k in CG.KIEU_CONG:
            p = CG.ra_don("d-%s" % k, "y", lenh=["a"], cong=k, goc=self.goc)
            self.assertEqual(_j.loads(p.read_text(encoding="utf-8"))["cong"],
                             {"kieu": k})

    def test_don_KHONG_co_lenh_van_ra_duoc_khong_can_cong(self):
        """Don thuan tuy la ghi chu / cau hoi cho nguoi thi khong can cong."""
        CG.ra_don("ghi-chu", "doc giup toi X", goc=self.goc)
        self.assertEqual(len(CG.don_dang_cho(goc=self.goc)), 1)

    def test_MOI_don_dang_nam_trong_hang_doi_THAT_deu_cham_duoc(self):
        """Chot chan tren hang doi that trong repo, khong phai fixture.

        Mot don da day len ma khong cham duoc thi khong ai biet cho toi khi
        may chay xong no.
        """
        for d in CG.don_dang_cho():
            if not d.get("lenh"):
                continue
            kieu = (d.get("cong") or {}).get("kieu")
            self.assertIn(kieu, CG.KIEU_CONG,
                          "don '%s' trong viec/cho/ co lenh ma cong.kieu=%r"
                          % (d["ma"], kieu))


class TuKiem(unittest.TestCase):
    """`b cau tu-kiem` - tach buoc de vo nhat ra khoi long vong `q`.

    Cau noi duoc viet va kiem HOAN TOAN tren cloud, tren repo git gia lap.
    Buoc dau tren may that la buoc de vo nhat, va neu no vo BEN TRONG `q` thi
    trieu chung se lan voi muoi thu khac dang chay.
    """

    def test_tu_kiem_chay_het_va_bao_du_cac_khau(self):
        ra = CG.tu_kiem(in_ra=lambda *a, **k: None)
        self.assertIn(ra["trang_thai"], CG.TRANG_THAI)
        ten = {b["buoc"] for b in ra["buoc"]}
        for phai_co in ("git chay duoc", "the {py} chay duoc",
                        "ra don -> chay -> ghi -> doc lai",
                        "khoa lan TESTER chan duoc nguoi thu hai"):
            self.assertIn(phai_co, ten)

    def test_tu_kiem_KHONG_cham_remote_va_KHONG_ghi_vao_viec_that(self):
        """Tu kiem phai an toan de go bat cu luc nao - ke ca giua mot dot chay."""
        truoc = {p.name for p in (CG.VIEC / "xong").glob("*.json")}
        CG.tu_kiem(in_ra=lambda *a, **k: None)
        sau = {p.name for p in (CG.VIEC / "xong").glob("*.json")}
        self.assertEqual(truoc, sau, "tu kiem da ghi vao viec/xong that")

    def test_HIEU_CHUAN_NGUOC_the_py_hong_thi_tu_kiem_BAO_HONG(self):
        """Neu tu kiem bao DAT du moi thu hong thi no vo dung."""
        goc = CG._thay_the
        CG._thay_the = lambda lenh: ["khong_co_lenh_nay_xyz"] if lenh else None
        try:
            ra = CG.tu_kiem(in_ra=lambda *a, **k: None)
        finally:
            CG._thay_the = goc
        self.assertEqual(ra["trang_thai"], "CHUA_DO_DUOC")
        self.assertTrue(ra["hong"])
