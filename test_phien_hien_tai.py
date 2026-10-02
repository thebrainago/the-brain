# -*- coding: utf-8 -*-
"""Ban giao phien: AUTO do may, TAY do nguoi - lam moi khong duoc dong vao TAY; muc hong khong lam chet ban giao."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

from nhan import phien_hien_tai as PT
from qwen import cau_git as CG


def git(p, *a):
    return subprocess.run(["git", "-C", str(p), *a], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def kho(tmp_path, monkeypatch):
    g = tmp_path / "kho"
    g.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(g)], check=True)
    git(g, "config", "user.email", "t@t.t")
    git(g, "config", "user.name", "t")
    (g / "a.txt").write_text("x", encoding="utf-8")
    git(g, "add", "-A")
    git(g, "commit", "-q", "-m", "viec that dau tien")
    monkeypatch.setattr(CG, "MAILBOX", g)
    monkeypatch.setattr(CG, "GOC", g)
    monkeypatch.setattr(CG, "CAU_HINH", tmp_path / "config" / "cau.json")      # khong ton tai -> phien cloud
    monkeypatch.setattr(PT, "LAB", g)
    monkeypatch.setattr(PT, "FILE", g / "tai_lieu" / "PHIEN_HIEN_TAI.md")
    return g


def _thu(g, tu, den, chu_de, luc=None, i="20261002-100000-aaaa"):
    d = g / "viec" / "thu"
    d.mkdir(parents=True, exist_ok=True)
    luc = luc or time.strftime("%Y-%m-%dT%H:%M:%S")
    (d / (i + ".json")).write_text(json.dumps({"id": i, "luc": luc, "tu": tu, "den": den, "loai": "nguoi", "chu_de": chu_de,
                                               "tra_loi": None, "noi_dung": "noi dung"}), encoding="utf-8")


class TestAuto:
    def test_co_nhanh_commit_thu_may_don_du_lieu(self, kho):
        _thu(kho, "nha", "cloud", "bao cao dem")
        (kho / "viec" / "may").mkdir(parents=True)
        (kho / "viec" / "may" / "nha.json").write_text(json.dumps({"ten": "nha", "trang_thai": "RANH", "phien_ban_ma": "abc123",
                                                                   "luc": "2026-10-02T23:30:26"}), encoding="utf-8")
        (kho / "viec" / "cho").mkdir()
        (kho / "viec" / "cho" / "x.json").write_text("{}", encoding="utf-8")
        (kho / "viec" / "xong").mkdir()
        (kho / "viec" / "xong" / "y.json").write_text(json.dumps({"trang_thai": "DAT"}), encoding="utf-8")
        (kho / "so_cai").mkdir()
        (kho / "so_cai" / "doan.json").write_text("{}", encoding="utf-8")
        a = PT.auto(kho, bay_gio=time.time())
        assert "Nhanh main @" in a and "viec that dau tien" in a
        assert "phien nay la `cloud`, chua doc 1" in a and "nha->cloud 1" in a and "bao cao dem" in a
        assert "nha RANH ma=abc123" in a and "(gio may)" in a
        assert "Don: cho 1 · dang 0 · xong 1 (DAT 1)" in a
        assert "so_cai/doan.json CO" in a and "Cau hinh: config/cau.json khong co (phien cloud)" in a

    def test_commit_thu_va_ket_qua_may_khong_lam_rac_danh_sach(self, kho):
        for tieu_de in ("thu cloud -> nha: gi do", "may: ket qua 2026-10-02 23:30", "may nha nhan cau-kiem"):
            (kho / "f.txt").write_text(tieu_de, encoding="utf-8")
            git(kho, "add", "-A")
            git(kho, "commit", "-q", "-m", tieu_de)
        a = PT.auto(kho)
        assert "viec that dau tien" in a and "thu cloud -> nha" not in a and "may: ket qua" not in a and "may nha nhan" not in a

    def test_so_voi_origin_va_cay_dang_do(self, kho):
        a = PT.auto(kho)
        assert "chua co origin/main" in a, "chua fetch thi noi that, khong bia +0/-0"
        (kho / "moi.txt").write_text("m", encoding="utf-8")
        assert "1 file sua/chua theo doi" in PT.auto(kho)

    def test_mot_muc_hong_khong_lam_chet_ban_giao(self, kho, monkeypatch):
        def hong(*a, **k):
            raise RuntimeError("giong that")
        monkeypatch.setattr(PT, "_thu", hong)
        a = PT.auto(kho)
        assert "RuntimeError" in a and "Nhanh main @" in a and "Don: cho" in a


class TestGhiGiuTay:
    TAY = "## Quyet dinh\n- dieu quan trong phai con nguyen\n\n## Dang o dau\n- dong thu hai"

    def test_file_moi_dung_mau_tay(self, kho):
        r = PT.ghi(kho)
        van = PT.FILE.read_text("utf-8")
        assert r["co_tay"] and "(chua co)" in van and van.count(PT.A0) == 1 and van.count(PT.T0) == 1

    def test_lam_moi_doi_AUTO_nhung_giu_nguyen_TAY(self, kho):
        PT.FILE.parent.mkdir(parents=True)
        PT.FILE.write_text("%s\n%s\n%s\n" % (PT.T0, self.TAY, PT.T1), encoding="utf-8")
        PT.ghi(kho, bay_gio=1_700_000_000)
        van1 = PT.FILE.read_text("utf-8")
        assert PT.doc_tay(van1) == self.TAY and "viec moi sau lan ghi dau" not in van1
        (kho / "b.txt").write_text("b", encoding="utf-8")
        git(kho, "add", "-A")
        git(kho, "commit", "-q", "-m", "viec moi sau lan ghi dau")
        PT.ghi(kho, bay_gio=1_700_003_600)
        van2 = PT.FILE.read_text("utf-8")
        assert PT.doc_tay(van2) == self.TAY, "TAY KHONG duoc doi"
        assert "viec moi sau lan ghi dau" in van2 and "2023-11-14 22:13" in van1 and "2023-11-14 23:13" in van2
        assert van2.count(PT.A0) == 1 and van2.count(PT.A1) == 1 and van2.count(PT.T0) == 1, "khong nhan doi khoi sau nhieu lan ghi"

    def test_ban_giao_gon_duoi_2k_token_khi_tay_vua_phai(self, kho):
        PT.FILE.parent.mkdir(parents=True)
        PT.FILE.write_text("%s\n%s\n%s\n" % (PT.T0, "dong " * 500, PT.T1), encoding="utf-8")
        assert PT.ghi(kho)["token_uoc"] < 2000


class TestChiMucVaMain:
    def test_chi_muc_xep_theo_co_va_lay_dong_dau(self, kho):
        (kho / "tai_lieu").mkdir()
        (kho / "tai_lieu" / "LON.md").write_text("# Tai lieu lon\n" + "x" * 3200, encoding="utf-8")
        (kho / "NHO.md").write_text("\n\n## Nho thoi\nngan", encoding="utf-8")
        (kho / "tai_lieu" / "VUA.md").write_text("# Vua\n" + "y" * 320, encoding="utf-8")
        ds = PT.chi_muc(kho, top=2)
        assert [x["file"] for x in ds] == ["tai_lieu/LON.md", "tai_lieu/VUA.md"] and ds[0]["dau"] == "Tai lieu lon" and ds[0]["token"] >= 1000

    def test_main_in_ghi_va_chi_muc(self, kho, capsys):
        assert PT.main(["--ghi"]) == 0 and PT.FILE.exists()
        assert "da ghi" in capsys.readouterr().out
        assert PT.main([]) == 0
        out = capsys.readouterr().out
        assert "PHIEN HIEN TAI" in out and PT.A0 in out and PT.T0 in out
        (kho / "NHO.md").write_text("# Muc luc thu\nnoi", encoding="utf-8")
        assert PT.main(["--chi-muc"]) == 0
        assert "NHO.md" in capsys.readouterr().out
