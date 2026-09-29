# -*- coding: utf-8 -*-
"""Tram may nha: danh sach trang chan lenh la, va vong khu hoi cloud -> tram -> cloud qua git that."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from nhan import tram as TR

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="can git")


@pytest.mark.parametrize("lenh", [
    ["tram", "ping"], ["nc", "kiem"], ["nc", "kiem", "30"], ["nc", "tu-lai", "AUDCAD", "H4"],
    ["nc", "tu-lai", "XAUUSDM", "H1", "--khong-niem-phong"], ["nc", "tho", "--vong", "2"],
    ["nc", "cc", "ho_so_tai_san", '{"ma":"AUDCAD","khung":"H4"}'], ["test"], ["vao"]])
def test_danh_sach_trang_cho_qua(lenh):
    assert TR.kiem_lenh(lenh) is None


@pytest.mark.parametrize("lenh", [
    ["git", "push"], ["nc", "tu-lai", "AUDCAD;del *", "H4"], ["nc", "tu-lai", "AUDCAD", "H4", "x"],
    ["nc", "tu-lai"], ["nc", "cc", "khong_co", "{}"], ["nc", "cc", "ho_so_tai_san", "[1]"],
    ["nc", "kiem", "-1"], ["test", "-k", "x"], [], "nc kiem", ["nc", "tho", "--vong", "999"]])
def test_danh_sach_trang_tu_choi(lenh):
    assert TR.kiem_lenh(lenh) is not None


def _g(d, *a):
    subprocess.run(["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                   check=True, capture_output=True)


@pytest.fixture
def hai_dau(tmp_path, monkeypatch):
    monkeypatch.setattr(TR, "DUNG_TAI_MAY", tmp_path / "TRAM_DUNG")
    goc = tmp_path / "goc.git"
    subprocess.run(["git", "init", "-q", "--bare", str(goc)], check=True)
    cloud = tmp_path / "cloud"
    subprocess.run(["git", "clone", "-q", str(goc), str(cloud)], check=True, capture_output=True)
    (cloud / "README").write_text("x")
    _g(cloud, "add", "README")
    _g(cloud, "commit", "-q", "-m", "goc")
    _g(cloud, "push", "-q", "origin", "HEAD:hop-thu")
    nha = tmp_path / "nha"
    subprocess.run(["git", "clone", "-q", "--branch", "hop-thu", str(goc), str(nha)], check=True,
                   capture_output=True)
    _g(nha, "config", "user.name", "tram")
    _g(nha, "config", "user.email", "tram@t")
    return cloud, {"hop_thu": str(nha), "nhanh": "hop-thu", "tom_tat_re": False}


def _giao_va_day(cloud, *lenh_ds):
    for lenh in lenh_ds:
        TR.giao(list(lenh), "test", goc=cloud)
    _g(cloud, "add", "tram")
    _g(cloud, "commit", "-q", "-m", "giao")
    _g(cloud, "push", "-q", "origin", "HEAD:hop-thu")


def _gia(lenh, han, log):
    log.write_text("OK %s\n" % " ".join(lenh), encoding="utf-8")
    return 0


def test_khu_hoi_cloud_tram_cloud(hai_dau):
    cloud, c = hai_dau
    _giao_va_day(cloud, ["tram", "ping"], ["nc", "kiem", "1"])
    r = TR.chay(chay_lenh=_gia, cau_hinh_=c)
    assert r["trang_thai"] == "XONG" and len(r["da_chay"]) == 2, r
    assert TR.chay(chay_lenh=_gia, cau_hinh_=c)["da_chay"] == [], "viec da chay khong chay lai"
    _g(cloud, "pull", "-q", "origin", "hop-thu")
    kq = {tuple(x["lenh"]): x for x in TR.doc(goc=cloud)}
    assert kq[("tram", "ping")]["trang_thai"] == "XONG" and kq[("tram", "ping")]["python"]
    assert kq[("nc", "kiem", "1")]["duoi_log"] == ["OK nc kiem 1"]


def test_viec_la_bi_tu_choi_va_het_gio_la_HET_GIO(hai_dau):
    cloud, c = hai_dau
    d = cloud / "tram" / "viec"
    d.mkdir(parents=True)
    (d / "20260929-000000-abcd.json").write_text(json.dumps({"id": "20260929-000000-abcd",
                                                             "lenh": ["git", "push"]}))
    TR.giao(["nc", "kiem"], goc=cloud)
    _g(cloud, "add", "tram")
    _g(cloud, "commit", "-q", "-m", "giao")
    _g(cloud, "push", "-q", "origin", "HEAD:hop-thu")

    def _lau(lenh, han, log):
        raise subprocess.TimeoutExpired(lenh, han)
    r = TR.chay(chay_lenh=_lau, cau_hinh_=c)
    tt = sorted(x["trang_thai"] for x in r["da_chay"])
    assert tt == ["HET_GIO", "TU_CHOI"], r


def test_dung_khan_va_khoa(hai_dau, tmp_path):
    cloud, c = hai_dau
    (cloud / "tram").mkdir()
    (cloud / "tram" / "DUNG").write_text("dung")
    _giao_va_day(cloud, ["tram", "ping"])
    assert TR.chay(chay_lenh=_gia, cau_hinh_=c)["trang_thai"] == "DUNG"
    khoa = Path(c["hop_thu"]) / ".git" / "tram_khoa.json"
    khoa.write_text(json.dumps({"den_han": 9e12}))
    assert TR.chay(chay_lenh=_gia, cau_hinh_=c)["trang_thai"] == "DANG_BAN"
