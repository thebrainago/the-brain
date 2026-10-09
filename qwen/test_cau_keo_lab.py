# -*- coding: utf-8 -*-
"""Test keo_lab: MA NGUON cua lab phai toi may thuc thi (08/10/2026) - bang repo git THAT (bare + cloud + lab + hop thu).

Vi sao bo test nay dung git that: loi can bat la loi cua DUONG TRUYEN (fetch / merge --ff-only / cay lam viec dang do), khong phai
loi logic. Mock se chung minh cac ham goi nhau dung thu tu va khong noi gi ve viec git co tu choi hay khong.

Mot lan do 08/10: lab o `44b3b23d` (+sua), cloud di truoc 150+ commit, moi ban sua cua cloud nam tren git ma may khong thay.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from qwen import cau_git as CG                                    # noqa: E402
from qwen import cau_may as CM                                    # noqa: E402

NHANH = "claude/test"


def g(p, *a, ok=True):
    r = subprocess.run(["git", *a], cwd=str(p), capture_output=True, text=True)
    if ok:
        assert r.returncode == 0, "git %s: %s" % (" ".join(a), r.stderr)
    return r.stdout.strip()


def ghi(p, rel, nd):
    f = Path(p) / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(nd, encoding="utf-8")


def commit(p, msg="c"):
    g(p, "add", "-A")
    g(p, "commit", "-q", "-m", msg)
    g(p, "push", "-q", "origin", "HEAD:%s" % NHANH)


@pytest.fixture
def nen(tmp_path):
    bare = tmp_path / "t.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", NHANH, str(bare)], check=True, capture_output=True)
    cloud, lab = tmp_path / "cloud", tmp_path / "lab"
    for p in (cloud, lab):
        subprocess.run(["git", "clone", "-q", str(bare), str(p)], check=True, capture_output=True)
        g(p, "config", "user.email", "t@t.t")
        g(p, "config", "user.name", "t")
        g(p, "checkout", "-q", "-B", NHANH) if p == cloud else None
    ghi(cloud, "qwen/ma.py", "V = 1\n")
    ghi(cloud, "nhan/x.py", "X = 1\n")
    ghi(cloud, "b.py", "print('b')\n")
    ghi(cloud, "tai_lieu/a.md", "a\n")
    commit(cloud, "dau")
    g(lab, "fetch", "-q", "origin", NHANH)
    g(lab, "checkout", "-q", "-B", NHANH, "FETCH_HEAD")
    g(lab, "branch", "-q", "--set-upstream-to=origin/%s" % NHANH, NHANH, ok=False)
    return type("Nen", (), {"cloud": cloud, "lab": lab, "bare": bare, "tmp": tmp_path})


def keo(nen, **kw):
    return CG.keo_lab(NHANH, nen.lab, ep=kw.pop("ep", True), **kw)


class TestKeoLab:
    def test_lab_sach_keo_ma_moi_va_bao_doi_ma(self, nen):
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud, "sua qwen")
        r = keo(nen)
        assert r["trang_thai"] == "DAT" and r["da_keo"] is True, r
        assert r["doi_ma"] is True and r["so_commit"] == 1
        assert (nen.lab / "qwen" / "ma.py").read_text("utf-8") == "V = 2\n"

    def test_chi_doi_tai_lieu_thi_khong_bao_doi_ma(self, nen):
        ghi(nen.cloud, "tai_lieu/a.md", "b\n")
        commit(nen.cloud)
        r = keo(nen)
        assert r["trang_thai"] == "DAT" and r["da_keo"] is True and r["doi_ma"] is False, r

    def test_da_moi_nhat_khong_lam_gi(self, nen):
        r = keo(nen)
        assert r["trang_thai"] == "DAT" and r["da_keo"] is False, r
        assert CG.tom_tat_keo_lab(r) == "kip"

    def test_lab_di_truoc_remote_van_la_kip_va_khong_mat_commit(self, nen):
        ghi(nen.lab, "rieng.txt", "x\n")
        g(nen.lab, "add", "-A")
        g(nen.lab, "commit", "-q", "-m", "viec chu du an")
        truoc = g(nen.lab, "rev-parse", "HEAD")
        r = keo(nen)
        assert r["trang_thai"] == "DAT" and r["da_keo"] is False, r
        assert g(nen.lab, "rev-parse", "HEAD") == truoc

    def test_nhip_dung_chung_qua_tep_trong_git_cua_lab(self, nen):
        keo(nen)                                         # lan dau that su fetch
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud)
        r = keo(nen, ep=False, nghi_giay=300)            # chua toi nhip: khong dong den mang
        assert r.get("bo_qua_nhip") is True
        assert (nen.lab / "qwen" / "ma.py").read_text("utf-8") == "V = 1\n"
        r = keo(nen, ep=False, nghi_giay=0)              # qua nhip: keo that
        assert r["da_keo"] is True
        assert (nen.lab / "qwen" / "ma.py").read_text("utf-8") == "V = 2\n"

    def test_file_dang_sua_do_dang_ma_commit_moi_cung_dong_vao_thi_KHONG_MAT_VIEC_va_noi_ro_file(self, nen):
        ghi(nen.lab, "qwen/ma.py", "V = 99  # ban va cua may nha\n")
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud)
        truoc = g(nen.lab, "rev-parse", "HEAD")
        r = keo(nen)
        assert r["trang_thai"] == "CHUA_DO_DUOC", r
        assert "qwen/ma.py" in r["ly_do"], r["ly_do"]
        assert g(nen.lab, "rev-parse", "HEAD") == truoc
        assert (nen.lab / "qwen" / "ma.py").read_text("utf-8") == "V = 99  # ban va cua may nha\n"
        assert g(nen.lab, "stash", "list") == ""                       # khong bao gio stash
        assert CG.tom_tat_keo_lab(r).startswith("tre: ")

    def test_file_dang_sua_khong_dung_vao_commit_moi_thi_van_keo_va_giu_ban_va(self, nen):
        ghi(nen.lab, "nhan/x.py", "X = 7  # ban va\n")
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud)
        r = keo(nen)
        assert r["trang_thai"] == "DAT" and r["da_keo"] is True and r["doi_ma"] is True, r
        assert (nen.lab / "nhan" / "x.py").read_text("utf-8") == "X = 7  # ban va\n"
        assert (nen.lab / "qwen" / "ma.py").read_text("utf-8") == "V = 2\n"

    def test_file_chua_theo_doi_trung_ten_voi_file_moi_thi_khong_de(self, nen):
        ghi(nen.lab, "qwen/moi.py", "RIENG = 1\n")
        ghi(nen.cloud, "qwen/moi.py", "CLOUD = 1\n")
        commit(nen.cloud)
        r = keo(nen)
        assert r["trang_thai"] == "CHUA_DO_DUOC", r
        assert (nen.lab / "qwen" / "moi.py").read_text("utf-8") == "RIENG = 1\n"

    def test_re_nhanh_lab_co_commit_chua_day_len_thi_noi_ro_khong_tu_rebase(self, nen):
        ghi(nen.lab, "rieng.txt", "x\n")
        g(nen.lab, "add", "-A")
        g(nen.lab, "commit", "-q", "-m", "viec chu du an")
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud)
        truoc = g(nen.lab, "rev-parse", "HEAD")
        r = keo(nen)
        assert r["trang_thai"] == "CHUA_DO_DUOC" and "re nhanh" in r["ly_do"], r
        assert r["lab_truoc"] == 1 and r["lab_sau"] == 1
        assert g(nen.lab, "rev-parse", "HEAD") == truoc

    def test_nhan_ngan_khong_chua_so_de_nhip_tim_khong_nhay_moi_lan_cloud_day(self, nen):
        ghi(nen.lab, "rieng.txt", "x\n")
        g(nen.lab, "add", "-A")
        g(nen.lab, "commit", "-q", "-m", "viec chu du an")
        nhan = []
        for i in range(3):
            ghi(nen.cloud, "tai_lieu/a.md", "v%d\n" % i)
            commit(nen.cloud)
            nhan.append(CG.tom_tat_keo_lab(keo(nen)))
        assert len(set(nhan)) == 1, nhan

    def test_lab_o_nhanh_khac_thi_bo_qua_va_khong_doi_nhanh(self, nen):
        g(nen.lab, "checkout", "-q", "-b", "viec-rieng")
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud)
        r = keo(nen)
        assert r["trang_thai"] == "BO_QUA" and "viec-rieng" in r["ly_do"], r
        assert g(nen.lab, "rev-parse", "--abbrev-ref", "HEAD") == "viec-rieng"
        assert CG.tom_tat_keo_lab(r).startswith("bo_qua: ")

    def test_lab_o_head_roi_thi_bo_qua(self, nen):
        g(nen.lab, "checkout", "-q", "--detach")
        assert keo(nen)["trang_thai"] == "BO_QUA"

    @pytest.mark.parametrize("dau", ["rebase-merge", "MERGE_HEAD", "CHERRY_PICK_HEAD"])
    def test_lab_dang_do_rebase_hay_merge_thi_khong_dung_vao(self, nen, dau):
        d = nen.lab / ".git" / dau
        d.mkdir() if dau == "rebase-merge" else d.write_text("x", encoding="utf-8")
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud)
        r = keo(nen)
        assert r["trang_thai"] == "BO_QUA" and dau in r["ly_do"], r
        assert (nen.lab / "qwen" / "ma.py").read_text("utf-8") == "V = 1\n"

    def test_khong_phai_kho_git_thi_bo_qua_khong_nem(self, tmp_path):
        r = CG.keo_lab(NHANH, tmp_path / "khong_co", ep=True)
        assert r["trang_thai"] == "BO_QUA"

    def test_mang_hong_la_chua_do_duoc_khong_nem(self, nen):
        g(nen.lab, "remote", "set-url", "origin", str(nen.tmp / "khong_ton_tai.git"))
        r = keo(nen)
        assert r["trang_thai"] == "CHUA_DO_DUOC" and "fetch hong" in r["ly_do"], r

    def test_khoa_moi_cua_bo_chay_khac_thi_khong_fetch_chong_len_nhau(self, nen):
        gd = nen.lab / ".git"
        (gd / "cau_keo_lab.khoa").write_text("123", encoding="utf-8")
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud)
        r = keo(nen)
        assert r.get("may_khac_dang_keo") is True
        assert (nen.lab / "qwen" / "ma.py").read_text("utf-8") == "V = 1\n"

    def test_khoa_cu_cua_tien_trinh_chet_thi_go_va_keo(self, nen):
        k = nen.lab / ".git" / "cau_keo_lab.khoa"
        k.write_text("123", encoding="utf-8")
        cu = time.time() - CG.KHOA_KEO_LAB_CU_GIAY - 60
        os.utime(str(k), (cu, cu))
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud)
        r = keo(nen)
        assert r["trang_thai"] == "DAT" and r["da_keo"] is True, r
        assert not k.exists()                                         # tra khoa sau khi xong

    def test_khoa_duoc_tra_ca_khi_keo_hong(self, nen):
        g(nen.lab, "remote", "set-url", "origin", str(nen.tmp / "khong_ton_tai.git"))
        keo(nen)
        assert not (nen.lab / ".git" / "cau_keo_lab.khoa").exists()


class TestChuKyMa:
    def test_doi_khi_doi_qwen_nhan_hay_b_py_khong_doi_khi_doi_tai_lieu(self, nen):
        a = CG.chu_ky_ma_bo_chay(nen.lab)
        ghi(nen.cloud, "tai_lieu/a.md", "doi\n")
        commit(nen.cloud)
        keo(nen)
        assert CG.chu_ky_ma_bo_chay(nen.lab) == a
        for rel in ("qwen/ma.py", "nhan/x.py", "b.py"):
            truoc = CG.chu_ky_ma_bo_chay(nen.lab)
            ghi(nen.cloud, rel, "doi %s\n" % rel)
            commit(nen.cloud)
            keo(nen)
            assert CG.chu_ky_ma_bo_chay(nen.lab) != truoc, rel

    def test_file_dang_sua_chua_commit_khong_tinh(self, nen):
        a = CG.chu_ky_ma_bo_chay(nen.lab)
        ghi(nen.lab, "qwen/ma.py", "V = 5\n")
        assert CG.chu_ky_ma_bo_chay(nen.lab) == a

    def test_khong_phai_git_thi_tra_chuoi_on_dinh(self, tmp_path):
        assert CG.chu_ky_ma_bo_chay(tmp_path) == "-/-/-"


class TestNhanPhienBanNhipTim:
    """Lab tu keo ma => HEAD cua lab nhay theo MOI commit tren nhanh, ke ca nhip tim / ket qua cua ~22 bo chay (dong `viec/`).
    Nhip tim ma ghi HEAD se doi o moi lan keo -> commit nhip tim -> HEAD lai nhay: vong lap commit vo tan."""

    def test_commit_chi_dong_viec_khong_doi_nhan_nhung_HEAD_thi_doi(self, nen):
        a, head = CG.phien_ban_ma_nguon(nen.lab), CG.phien_ban_ma(nen.lab)
        ghi(nen.cloud, "viec/may/x.json", "{}\n")
        commit(nen.cloud, "nhip tim cua bo chay khac")
        keo(nen)
        assert CG.phien_ban_ma(nen.lab) != head                      # HEAD that (dung cho bang chung tung don) co nhay
        assert CG.phien_ban_ma_nguon(nen.lab) == a                   # nhan nhip tim thi KHONG

    def test_doi_ma_hay_tai_lieu_thi_nhan_doi(self, nen):
        a = CG.phien_ban_ma_nguon(nen.lab)
        ghi(nen.cloud, "tai_lieu/a.md", "doi\n")
        commit(nen.cloud, "tai lieu")
        keo(nen)
        b = CG.phien_ban_ma_nguon(nen.lab)
        assert b != a
        ghi(nen.cloud, "qwen/ma.py", "V = 3\n")
        commit(nen.cloud, "ma")
        keo(nen)
        assert CG.phien_ban_ma_nguon(nen.lab) not in (a, b)

    def test_file_theo_doi_dang_sua_thi_co_dau_sua(self, nen):
        ghi(nen.lab, "qwen/ma.py", "V = 5\n")
        assert CG.phien_ban_ma_nguon(nen.lab).endswith("+sua")

    def test_khong_phai_git_thi_khong_nem(self, tmp_path):
        assert isinstance(CG.phien_ban_ma_nguon(tmp_path), str)


class TestCauHinhMoiTruong:
    def _sach(self, monkeypatch, tmp_path):
        monkeypatch.setattr(CG, "CAU_HINH", tmp_path / "khong_co.json")
        for k in ("CAU_TEN", "CAU_KHA_NANG", "CAU_CHI_LAN", "CAU_HOP_THU", "CAU_NHANH"):
            monkeypatch.delenv(k, raising=False)

    def test_mac_dinh_khong_co_chi_lan(self, monkeypatch, tmp_path):
        self._sach(monkeypatch, tmp_path)
        assert CG.cau_hinh()["chi_lan"] == []

    def test_moi_bo_chay_khai_ten_kha_nang_lan_qua_moi_truong(self, monkeypatch, tmp_path):
        self._sach(monkeypatch, tmp_path)
        monkeypatch.setenv("CAU_TEN", "nha-m2")
        monkeypatch.setenv("CAU_KHA_NANG", "windows, mt5,data")
        monkeypatch.setenv("CAU_CHI_LAN", "tester")
        c = CG.cau_hinh()
        assert (c["ten"], c["kha_nang"], c["chi_lan"]) == ("nha-m2", ["windows", "mt5", "data"], ["TESTER"])

    def test_ten_nguy_hiem_bi_lam_sach(self, monkeypatch, tmp_path):
        self._sach(monkeypatch, tmp_path)
        monkeypatch.setenv("CAU_TEN", "../../etc/x y")
        t = CG.cau_hinh()["ten"]
        assert "/" not in t and " " not in t and ".." not in t.replace("..", "", 0) or t.strip("_.-") == t

    def test_moi_truong_rong_thi_giu_cau_hinh_file(self, monkeypatch, tmp_path):
        self._sach(monkeypatch, tmp_path)
        f = tmp_path / "cau.json"
        f.write_text(json.dumps({"ten": "tu-file", "kha_nang": ["linux"]}), encoding="utf-8")
        monkeypatch.setattr(CG, "CAU_HINH", f)
        monkeypatch.setenv("CAU_TEN", "")
        monkeypatch.setenv("CAU_KHA_NANG", "")
        c = CG.cau_hinh()
        assert (c["ten"], c["kha_nang"]) == ("tu-file", ["linux"])


def _don(hop, ma, lan, uu_tien=5):
    (hop / "viec" / "cho").mkdir(parents=True, exist_ok=True)
    (hop / "viec" / "cho" / ("%s.json" % ma)).write_text(json.dumps(
        {"ma": ma, "muc_tieu": "t", "lan": lan, "uu_tien": uu_tien, "han_phut": 5,
         "lenh": ["{py}", "-c", "print(1)"], "cong": {"kieu": "chay_duoc"}}), encoding="utf-8")


class TestChiLan:
    def test_bo_chay_chi_lan_tester_bo_qua_don_cpu(self, tmp_path):
        hop = tmp_path / "hop"
        CG.bao_dam_thu_muc(goc=hop)
        _don(hop, "a-cpu", "CPU", 1)
        _don(hop, "b-nhe", "NHE", 2)
        assert CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, may="m1", kha_nang=["mt5"],
                                        chi_lan=["TESTER"]) is None

    def test_bo_chay_khong_gioi_han_lan_van_nhan_don_cpu(self, tmp_path):
        hop = tmp_path / "hop"
        CG.bao_dam_thu_muc(goc=hop)
        _don(hop, "a-cpu", "CPU", 1)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, may="p1", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "a-cpu"

    def test_chi_lan_tester_van_nhan_don_tester(self, tmp_path):
        hop = tmp_path / "hop"
        CG.bao_dam_thu_muc(goc=hop)
        _don(hop, "a-cpu", "CPU", 1)
        _don(hop, "t-test", "TESTER", 9)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, may="m1", kha_nang=["mt5"], chi_lan=["TESTER"])
        assert r and r["ma"] == "t-test"


class TestTagMa:
    """Nhan kha nang suy ra tu MA dang chay: don can ma moi khong bi bo chay cu nhan nham (08/10/2026, lab nha tre ~270 commit)."""

    @staticmethod
    def _lab(tmp_path, ten, engine=None, trang_ke=False, swap=None, gia=None, lenh=None):
        lab = tmp_path / ten
        if engine is not None:
            ghi(lab, "nhan/luoi.py", "# luoi\nPHIEN_BAN_ENGINE = %d\n" % engine)
        if trang_ke:
            ghi(lab, "nhan/doc_dien_dan.py", "def tim_trang_tiep(fo, tach, url, n):\n    return {}\n")
        if swap is not None:                           # swap=True: bo uoc swap day du; chuoi: noi dung tuy y
            ghi(lab, "nhan/swap_uoc.py", "def uoc_tu_bao_cao(duong, ma, het=None, ty_le=None):\n    return None\n" if swap is True else swap)
        if gia is not None:                            # gia=True: bo xuat gia ghi vao hop thu; chuoi: noi dung tuy y
            ghi(lab, "nhan/xuat_gia.py", "def thu_muc_mac_dinh():\n    return None\n" if gia is True else gia)
        if lenh is not None:                           # lenh=True: bo xuat bang lenh tester day du; chuoi: noi dung tuy y
            ghi(lab, "nhan/xuat_lenh_tester.py", "def kiem_bang(van_ban):\n    return {}\n" if lenh is True else lenh)
        lab.mkdir(parents=True, exist_ok=True)
        return lab

    def test_nhan_suy_ra_tu_ma(self, tmp_path):
        lab = self._lab(tmp_path, "moi", engine=4, trang_ke=True)
        assert CG.tag_ma(lab) == ["ma-0810", "engine1", "engine2", "engine3", "engine4", "dien-dan-v2"]

    def test_ma_cu_khong_co_nhan_tinh_nang(self, tmp_path):
        assert CG.tag_ma(self._lab(tmp_path, "cu")) == ["ma-0810"]
        assert CG.tag_ma(self._lab(tmp_path, "cu3", engine=3)) == ["ma-0810", "engine1", "engine2", "engine3"]

    def test_nhan_swap_v1_chi_khi_ma_co_bo_uoc_swap_day_du(self, tmp_path):
        assert CG.tag_ma(self._lab(tmp_path, "co", engine=4, swap=True)) == \
            ["ma-0810", "engine1", "engine2", "engine3", "engine4", "swap-v1"]
        assert "swap-v1" not in CG.tag_ma(self._lab(tmp_path, "khong", engine=4))
        # tep co ten dung nhung chua co ham chinh (ban nhap / ban cu): khong khai nhan
        assert "swap-v1" not in CG.tag_ma(self._lab(tmp_path, "nua", swap="def ty_le_cho(ma):\n    return None\n"))
        assert CG.tag_ma(self._lab(tmp_path, "tat_ca", engine=4, trang_ke=True, swap=True))[-2:] == ["dien-dan-v2", "swap-v1"]

    def test_nhan_gia_v2_chi_khi_xuat_gia_biet_ghi_vao_hop_thu(self, tmp_path):
        assert CG.tag_ma(self._lab(tmp_path, "co", engine=4, gia=True))[-1] == "gia-v2"
        assert "gia-v2" not in CG.tag_ma(self._lab(tmp_path, "khong", engine=4))
        # `xuat_gia.py` ban cu (ghi vao lab, file khong bao gio len git): khong khai nhan
        assert "gia-v2" not in CG.tag_ma(self._lab(tmp_path, "cu", gia="def ghi(df, ma, khung):\n    return {}\n"))
        assert CG.tag_ma(self._lab(tmp_path, "tat_ca", engine=4, trang_ke=True, swap=True, gia=True))[-3:] == \
            ["dien-dan-v2", "swap-v1", "gia-v2"]

    def test_ma_that_cua_repo_khai_gia_v2(self):
        assert "gia-v2" in CG.tag_ma(CG.GOC)

    def test_nhan_lenh_v1_chi_khi_ma_co_bo_xuat_bang_lenh_tester(self, tmp_path):
        assert CG.tag_ma(self._lab(tmp_path, "co", engine=4, lenh=True))[-1] == "lenh-v1"
        assert "lenh-v1" not in CG.tag_ma(self._lab(tmp_path, "khong", engine=4, gia=True))
        # tep co ten dung nhung chua co ham kiem bang (ban nhap): khong khai nhan
        assert "lenh-v1" not in CG.tag_ma(self._lab(tmp_path, "nhap", lenh="def chay():\n    return {}\n"))
        assert CG.tag_ma(self._lab(tmp_path, "tat_ca", engine=4, trang_ke=True, swap=True, gia=True, lenh=True))[-4:] == \
            ["dien-dan-v2", "swap-v1", "gia-v2", "lenh-v1"]

    def test_ma_that_cua_repo_khai_lenh_v1(self):
        assert "lenh-v1" in CG.tag_ma(CG.GOC)

    def test_don_lenh_v1_cho_bo_chay_ma_cu_va_chay_o_bo_chay_ma_moi(self, tmp_path):
        hop = tmp_path / "hop"
        CG.bao_dam_thu_muc(goc=hop)
        _don(hop, "a-xuat-lenh", "NHE", 1)
        f = hop / "viec" / "cho" / "a-xuat-lenh.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        d["can"] = ["lenh-v1"]
        f.write_text(json.dumps(d), encoding="utf-8")
        _don(hop, "z-thuong", "NHE", 9)
        cu = self._lab(tmp_path, "cu", engine=4, swap=True, gia=True)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, lab=cu, may="p1", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "z-thuong"             # ma chua co xuat_lenh_tester: don CHO, khong chay ra 'khong biet lenh'
        assert not (hop / "viec" / "xong" / "a-xuat-lenh.json").exists()
        moi = self._lab(tmp_path, "moi", engine=4, swap=True, gia=True, lenh=True)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, lab=moi, may="p2", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "a-xuat-lenh"

    def test_don_gia_v2_cho_bo_chay_ma_cu_va_chay_o_bo_chay_ma_moi(self, tmp_path):
        hop = tmp_path / "hop"
        CG.bao_dam_thu_muc(goc=hop)
        _don(hop, "a-xuat-gia", "NHE", 1)
        f = hop / "viec" / "cho" / "a-xuat-gia.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        d["can"] = ["gia-v2"]
        f.write_text(json.dumps(d), encoding="utf-8")
        _don(hop, "z-thuong", "NHE", 9)
        cu = self._lab(tmp_path, "cu", engine=4, swap=True)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, lab=cu, may="p1", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "z-thuong"             # ma chua ghi vao hop thu: don xuat gia CHO, khong chay roi mat file
        assert not (hop / "viec" / "xong" / "a-xuat-gia.json").exists()
        moi = self._lab(tmp_path, "moi", engine=4, swap=True, gia=True)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, lab=moi, may="p2", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "a-xuat-gia"

    def test_don_swap_v1_cho_bo_chay_ma_cu_va_chay_o_bo_chay_ma_moi(self, tmp_path):
        hop = tmp_path / "hop"
        CG.bao_dam_thu_muc(goc=hop)
        _don(hop, "a-quet-swap", "NHE", 1)
        f = hop / "viec" / "cho" / "a-quet-swap.json"
        d = json.loads(f.read_text(encoding="utf-8"))
        d["can"] = ["swap-v1"]
        f.write_text(json.dumps(d), encoding="utf-8")
        _don(hop, "z-thuong", "NHE", 9)
        cu = self._lab(tmp_path, "cu", engine=4)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, lab=cu, may="p1", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "z-thuong"             # ma chua co swap_uoc: don quet swap CHO, khong bi dot thanh loi
        assert not (hop / "viec" / "xong" / "a-quet-swap.json").exists()
        moi = self._lab(tmp_path, "moi", engine=4, swap=True)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, lab=moi, may="p2", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "a-quet-swap"

    def test_don_can_engine4_cho_bo_chay_ma_cu_va_chay_o_bo_chay_ma_moi(self, tmp_path):
        hop = tmp_path / "hop"
        CG.bao_dam_thu_muc(goc=hop)
        _don(hop, "a-can-engine4", "CPU", 1)
        d = json.loads((hop / "viec" / "cho" / "a-can-engine4.json").read_text(encoding="utf-8"))
        d["can"] = ["engine4"]
        (hop / "viec" / "cho" / "a-can-engine4.json").write_text(json.dumps(d), encoding="utf-8")
        _don(hop, "z-thuong", "CPU", 9)
        cu = self._lab(tmp_path, "cu", engine=3)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, lab=cu, may="p1", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "z-thuong"            # ma cu: don can engine4 CHO, khong bi dot, don thuong van chay
        assert not (hop / "viec" / "xong" / "a-can-engine4.json").exists()
        moi = self._lab(tmp_path, "moi", engine=4)
        r = CG.chay_mot_don_dang_cho(goc=hop, kiem_trang=False, lab=moi, may="p2", kha_nang=["windows"], chi_lan=[])
        assert r and r["ma"] == "a-can-engine4"       # ma moi: don do chay


class TestTienTrinhMoi:
    def _gia_lap(self, tmp_path, monkeypatch, ma_b):
        lab = tmp_path / "lab_gia"
        lab.mkdir()
        (lab / "b.py").write_text(ma_b, encoding="utf-8")
        monkeypatch.setattr(CM, "GOC", lab)
        monkeypatch.setattr(CG, "GOC", lab)
        monkeypatch.setattr(CG, "CAU_HINH", tmp_path / "khong_co.json")
        for k in ("CAU_NHANH", "CAU_HOP_THU"):
            monkeypatch.delenv(k, raising=False)
        return lab

    def test_luot_con_tra_ket_qua_qua_tep_tam_va_biet_la_luot_con(self, tmp_path, monkeypatch):
        self._gia_lap(tmp_path, monkeypatch, (
            "import json, os, sys\n"
            "open(os.environ['CAU_KET_QUA_LUOT'], 'w').write(json.dumps({'trang_thai': 'XONG', 'argv': sys.argv[1:],\n"
            "    'luot_con': os.environ.get('CAU_LUOT_CON')}))\n"))
        r = CM.luot_tien_trinh_moi()
        assert r == {"trang_thai": "XONG", "argv": ["cau", "chay"], "luot_con": "1"}

    def test_luot_con_chet_khong_ra_ket_qua_thi_la_LOI_CON_chu_khong_phai_xong(self, tmp_path, monkeypatch):
        self._gia_lap(tmp_path, monkeypatch, "import sys\nsys.exit(3)\n")
        r = CM.luot_tien_trinh_moi()
        assert r["trang_thai"] == "LOI_CON" and r["ma_thoat"] == 3

    def test_ma_moi_hong_cu_phap_thi_giam_sat_van_song(self, tmp_path, monkeypatch):
        self._gia_lap(tmp_path, monkeypatch, "def (:\n")
        assert CM.luot_tien_trinh_moi()["trang_thai"] == "LOI_CON"

    def test_giam_sat_keo_ma_lab_truoc_khi_sinh_luot_con(self, tmp_path, monkeypatch):
        self._gia_lap(tmp_path, monkeypatch, "import sys\nsys.exit(0)\n")
        goi = []
        monkeypatch.setattr(CG, "cau_hinh", lambda: {"nhanh": "nh"})
        monkeypatch.setattr(CG, "keo_lab", lambda nhanh, lab=None, nghi_giay=None, ep=False: goi.append((nhanh, nghi_giay)) or {})
        CM.luot_tien_trinh_moi()
        CM.luot_tien_trinh_moi(sau_loi=True)
        assert goi == [("nh", None), ("nh", 60.0)]


def _chay_gia(d, goc=None, kiem_trang=True, lab=None):
    """Thay `chay_don`: ghi ket qua vao `viec/xong/` NHU THAT - don xong khong con 'dang cho'. Mock tra ve ma khong ghi
    gi thi don van o hang doi va bi nhan lai o vong sau (lan chay thu hai chi bi chan neu hai phieu nhan viec trung giay)."""
    CG.ghi_ket_qua(d["ma"], "DAT", goc=goc)
    return {"ma": d["ma"], "trang_thai": "DAT"}


class TestChayMotLuotMaLab:
    def _ha_tang(self, nen, monkeypatch):
        hop = nen.tmp / "hop"
        subprocess.run(["git", "clone", "-q", str(nen.bare), str(hop)], check=True, capture_output=True)
        g(hop, "config", "user.email", "t@t.t")
        g(hop, "config", "user.name", "t")
        g(hop, "checkout", "-q", "-B", NHANH, "origin/%s" % NHANH)
        CG.bao_dam_thu_muc(goc=hop)
        monkeypatch.setattr(CG, "GOC", nen.lab)
        monkeypatch.setattr(CM, "GOC", nen.lab)
        monkeypatch.setattr(CG, "CAU_HINH", nen.tmp / "khong_co.json")
        monkeypatch.setattr(CG, "NGU_GIAY", (0, 0, 0))
        monkeypatch.setattr(CM, "_mau_may", lambda: ("XANH", ""))
        monkeypatch.setattr(CM, "_MA_NAP", None)
        return hop, {"ten": "may-a", "hop_thu": str(hop), "nhanh": NHANH, "kha_nang": ["windows"],
                     "session_cloud": "", "bao_cloud": False, "nhip_bao_phut": 30, "tom_tat_re": False, "chi_lan": []}

    def test_ma_moi_ve_giua_luot_thi_dung_nhan_don_va_bao_nap_lai(self, nen, monkeypatch):
        hop, c = self._ha_tang(nen, monkeypatch)
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud, "sua ma")
        _don(nen.cloud, "a", "CPU")
        commit(nen.cloud, "don")
        r = CM.chay_mot_luot(c)
        assert r["trang_thai"] == "XONG" and r["nap_lai_ma"] is True and r["da_chay"] == [], r
        assert (nen.lab / "qwen" / "ma.py").read_text("utf-8") == "V = 2\n"           # ma lab DA toi
        d = json.loads((hop / "viec" / "may" / "may-a.json").read_text("utf-8"))
        assert d["lab_keo"] == "kip"

    def test_o_tien_trinh_moi_ma_khong_doi_thi_chay_don_binh_thuong(self, nen, monkeypatch):
        hop, c = self._ha_tang(nen, monkeypatch)
        _don(nen.cloud, "a", "CPU")
        commit(nen.cloud, "don")
        monkeypatch.setattr(CG, "chay_don", _chay_gia)
        r = CM.chay_mot_luot(c)
        assert r["trang_thai"] == "XONG" and r["nap_lai_ma"] is False
        assert [x["ma"] for x in r["da_chay"]] == ["a"], r

    def test_che_do_trong_tien_trinh_khong_the_nap_lai_nen_cu_chay_tiep(self, nen, monkeypatch):
        hop, c = self._ha_tang(nen, monkeypatch)
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud, "sua ma")
        _don(nen.cloud, "a", "CPU")
        commit(nen.cloud, "don")
        monkeypatch.setattr(CG, "chay_don", _chay_gia)
        r = CM.chay_mot_luot(c, dung_khi_doi_ma=False)
        assert r["nap_lai_ma"] is False and [x["ma"] for x in r["da_chay"]] == ["a"], r

    def test_nhip_tim_khong_ghi_lai_khi_lab_chi_keo_ve_commit_cua_viec(self, nen, monkeypatch):
        hop, c = self._ha_tang(nen, monkeypatch)
        assert CM.nhip_tim(hop, c, "RANH", lab_keo="kip") is True            # lan dau: ghi
        ghi(nen.cloud, "viec/may/bo-chay-khac.json", "{}\n")
        commit(nen.cloud, "nhip tim cua bo chay khac")
        keo(nen)                                                              # lab keo commit do ve: HEAD nhay
        assert CM.nhip_tim(hop, c, "RANH", lab_keo="kip") is False           # nhung nhip tim KHONG ghi lai
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud, "sua ma")
        keo(nen)
        assert CM.nhip_tim(hop, c, "RANH", lab_keo="kip") is True            # doi MA that thi ghi

    def test_lab_bi_chan_boi_file_dang_sua_thi_nhip_tim_noi_ro_va_van_chay_don(self, nen, monkeypatch):
        hop, c = self._ha_tang(nen, monkeypatch)
        ghi(nen.lab, "qwen/ma.py", "V = 99\n")
        ghi(nen.cloud, "qwen/ma.py", "V = 2\n")
        commit(nen.cloud, "sua ma")
        _don(nen.cloud, "a", "CPU")
        commit(nen.cloud, "don")
        monkeypatch.setattr(CG, "chay_don", _chay_gia)
        r = CM.chay_mot_luot(c)
        assert [x["ma"] for x in r["da_chay"]] == ["a"], r
        d = json.loads((hop / "viec" / "may" / "may-a.json").read_text("utf-8"))
        assert d["lab_keo"].startswith("tre: ") and "qwen/ma.py" in d["lab_keo"], d
        assert "ma lab: tre" in CM.bang_may(hop)


class TestTuoiNhip:
    def test_gio_dia_phuong_doi_ve_utc(self):
        from datetime import datetime, timezone
        bay = datetime(2026, 10, 8, 16, 47, tzinfo=timezone.utc).timestamp()
        assert round(CG.tuoi_nhip_phut({"luc": "2026-10-08T23:26:06"}, bay)) == 21                  # nhip cu: mac dinh +7
        assert round(CG.tuoi_nhip_phut({"luc": "2026-10-08T23:26:06", "mui_gio_phut": 420}, bay)) == 21
        assert round(CG.tuoi_nhip_phut({"luc": "2026-10-08T16:30:00", "mui_gio_phut": 0}, bay)) == 17
        assert CG.tuoi_nhip_phut({"luc": "khong phai gio"}, bay) is None
        assert CG.tuoi_nhip_phut({}, bay) is None

    def test_mui_gio_phut_may_la_so_nguyen_trong_khoang_hop_le(self):
        m = CG.mui_gio_phut_may()
        assert isinstance(m, int)
        assert -12 * 60 <= m <= 14 * 60
