# -*- coding: utf-8 -*-
"""So cai nghien cuu trong git: chi-them, khong mat dau vet, nhap lai dung id - va di cung cau len git."""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from nhan import nc_so_cai as SC, nc_so_tay as ST
from qwen import cau_git as CG


@pytest.fixture
def so_tay(tmp_path, monkeypatch):
    """nc.db tam voi mot it du lieu that: gia thuyet cha/con, thi nghiem, hieu biet, cau hoi, vong, niem phong."""
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    g1 = ST.them_gia_thuyet("hoi quy IBS sau cu giam", vi_sao="co nguoi tra tien", ho="hoi_quy")
    g2 = ST.them_gia_thuyet("loc bien dong", cha=g1)
    vong = ST.bat_dau_vong("tho", "mo-hinh-thu")
    t1 = ST.ghi_thi_nghiem("quet", {"ma": "AUDCAD"}, {"t": 2.1}, "DAT", "vt1", ma="AUDCAD", khung="H4",
                           doan="kham_pha", gt_id=g1, so_phep_thu=7, vong_id=vong)
    ST.them_hieu_biet("IBS thap + bien dong cao -> hoi quy", 0.6, [t1])
    ST.them_cau_hoi("co ben tren moi khung khong?", uu_tien=0.8, nguon="nguoi")
    ST.ket_thuc_vong(vong, tom_tat="xong", so_cong_cu=3)
    with ST.ket_noi() as cn:
        cn.execute("INSERT INTO niem_phong(luc,van_tay,gt_id,ma,khung,spec,ket_qua,trang_thai) VALUES(?,?,?,?,?,?,?,?)",
                   (ST.bay_gio(), "seal-1", g1, "AUDCAD", "H4", "{}", '{"cagr": 3.2}', "DAT"))
    return tmp_path


def _bang(db: Path, bang: str) -> list[dict]:
    cn = sqlite3.connect(str(db))
    cn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in cn.execute("SELECT * FROM %s ORDER BY id" % bang)]
    finally:
        cn.close()


def _dong(f: Path) -> list[dict]:
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_xuat_roi_nhap_vao_so_trong_cho_dung_tung_hang_va_id(so_tay):
    thu = so_tay / "so_cai"
    r = SC.xuat(dich=thu)
    assert r["gia_thuyet"] == 2 and r["thi_nghiem"] == 1 and r["niem_phong"] == 1, r
    moi = so_tay / "nc_moi.db"
    n = SC.nhap(nguon=thu, db=moi)
    assert n["gia_thuyet"] == 2 and n["niem_phong"] == 1
    for b in SC.BANG:
        assert _bang(moi, b) == _bang(so_tay / "nc.db", b), b


def test_chi_them_khong_ghi_lai_hang_nguyen_va_hang_doi_them_dung_mot_dong(so_tay):
    thu = so_tay / "so_cai"
    SC.xuat(dich=thu)
    truoc = {b: len(_dong(thu / ("%s.jsonl" % b))) for b in SC.BANG}
    assert SC.xuat(dich=thu) == {b: 0 for b in SC.BANG}, "xuat lan hai ma khong doi gi van them dong"
    ST.cap_nhat_gia_thuyet(1, trang_thai="TRIEN_VONG")
    r = SC.xuat(dich=thu)
    assert r["gia_thuyet"] == 1 and sum(r.values()) == 1
    sau = {b: len(_dong(thu / ("%s.jsonl" % b))) for b in SC.BANG}
    assert sau["gia_thuyet"] == truoc["gia_thuyet"] + 1, "doi mot hang phai THEM mot dong, khong sua dong cu"
    moi = so_tay / "nc_moi.db"
    SC.nhap(nguon=thu, db=moi)
    assert [x["trang_thai"] for x in _bang(moi, "gia_thuyet")][0] == "TRIEN_VONG", "nhap phai lay ban chup CUOI"


def test_khong_the_xoa_dau_vet_dua_DB_ve_ban_cu_thi_so_cai_VAN_giu_ban_ghi_niem_phong(so_tay):
    """Dung bai toan mat nao.db: khai bao da mo doan niem phong khong duoc quen."""
    thu = so_tay / "so_cai"
    SC.xuat(dich=thu)
    (so_tay / "nc.db").unlink()                       # may cai lai Windows: DB mat sach
    with ST.ket_noi():
        pass                                          # DB moi tinh, RONG
    assert SC.xuat(dich=thu) == {b: 0 for b in SC.BANG}, "xuat tu DB rong khong duoc xoa gi khoi so cai"
    assert SC.tom_tat(thu)["niem_phong"] == 1
    SC.nhap(nguon=thu)                                # khoi phuc tu git
    assert [x["van_tay"] for x in _bang(so_tay / "nc.db", "niem_phong")] == ["seal-1"]


def test_nhap_tu_choi_de_len_so_dang_co_tru_khi_ghi_de(so_tay):
    thu = so_tay / "so_cai"
    SC.xuat(dich=thu)
    with pytest.raises(SC.LoiSoCai) as e:
        SC.nhap(nguon=thu)                            # nc.db dang co du lieu
    assert "KHONG rong" in str(e.value)
    assert SC.nhap(nguon=thu, ghi_de=True)["gia_thuyet"] == 2     # hieu chuan nguoc: co chu y thi duoc


def test_dong_cut_do_do_may_sap_giua_luc_ghi_bi_bo_qua_chu_khong_hong_ca_file(so_tay):
    thu = so_tay / "so_cai"
    SC.xuat(dich=thu)
    f = thu / "gia_thuyet.jsonl"
    f.write_text(f.read_text(encoding="utf-8") + '{"h": "abc", "r": {"id": 99, "cau": "cut do', encoding="utf-8")
    moi = so_tay / "nc_moi.db"
    assert SC.nhap(nguon=thu, db=moi)["gia_thuyet"] == 2


def test_chua_co_so_cai_thi_noi_ro(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    with pytest.raises(SC.LoiSoCai):
        SC.nhap(nguon=tmp_path / "khong_co")
    assert SC.xuat(db=tmp_path / "khong_co.db", dich=tmp_path / "x") == {b: 0 for b in SC.BANG}


# ---------------------------------------------------------------- di cung cau len git
def _git(p, *a):
    return subprocess.run(["git", "-C", str(p), *a], capture_output=True, text=True, check=True).stdout.strip()


def _hai_dau_cau(tmp_path):
    bare = tmp_path / "t.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    hop, cloud = tmp_path / "hop", tmp_path / "cloud"
    for p in (hop, cloud):
        subprocess.run(["git", "clone", "-q", str(bare), str(p)], check=True, capture_output=True)
        _git(p, "config", "user.email", "t@t.t")
        _git(p, "config", "user.name", "t")
    (cloud / "README.md").write_text("x", encoding="utf-8")
    _git(cloud, "add", "-A")
    _git(cloud, "commit", "-m", "dau")
    _git(cloud, "push", "origin", "HEAD:main")
    _git(hop, "pull", "-q", "origin", "main")
    return bare, hop, cloud


def test_dong_bo_day_so_cai_len_git_khi_may_bat_ghi_so_cai(so_tay, tmp_path, monkeypatch):
    _, hop, cloud = _hai_dau_cau(tmp_path)
    monkeypatch.setattr(CG, "CAU_HINH", tmp_path / "cau.json")
    # BAT: may nay ghi so cai
    (tmp_path / "cau.json").write_text(json.dumps({"ghi_so_cai": True}), encoding="utf-8")
    r = CG.dong_bo("main", ep=True, goc=hop, rieng=True)
    assert r["trang_thai"] == "DAT" and r["day"]["da_day"] is True, r
    _git(cloud, "pull", "-q", "origin", "main")
    assert (cloud / "so_cai" / "nc" / "niem_phong.jsonl").exists()
    # cloud NHAP ban sao de doc: "hieu duoc viec"
    ban_sao = tmp_path / "nc_cloud.db"
    assert SC.nhap(nguon=cloud / "so_cai" / "nc", db=ban_sao)["gia_thuyet"] == 2
    assert [x["van_tay"] for x in _bang(ban_sao, "niem_phong")] == ["seal-1"]


def test_HIEU_CHUAN_NGUOC_may_KHONG_bat_ghi_so_cai_thi_khong_day_gi(so_tay, tmp_path, monkeypatch):
    """Cloud cung co nc.db (ephemeral) - no khong duoc dung id voi may nha."""
    _, hop, cloud = _hai_dau_cau(tmp_path)
    monkeypatch.setattr(CG, "CAU_HINH", tmp_path / "cau.json")          # khong co file -> mac dinh ghi_so_cai False
    CG.dong_bo("main", ep=True, goc=hop, rieng=True)
    _git(cloud, "pull", "-q", "origin", "main")
    assert not (cloud / "so_cai").exists()
