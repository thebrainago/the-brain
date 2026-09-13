# -*- coding: utf-8 -*-
"""test_ngan_sach.py - CUA VAO tai nguyen phai TU CHOI duoc, khong chi cho qua.

Moi bai o day ung voi mot cach he da chet ngay 13/09/2026:

    dia day            -> ghi khong tron ven -> kho co che bi xoa HAI lan
    34 tien trinh sot  -> `ENOMEM: uv_spawn`, bo test chet 4 lan
    cao mql5 0,3s/luot -> chan ca IP, 29 URL tot bi loai vinh vien
    whisper+pytest+MT5 -> ba viec nang cung luc, hai cai chet

Nen cai phai gac khong phai "ham co chay khong" ma **"no co TU CHOI dung luc
khong"**. Mot cua vao khong bao gio tu choi doc y het khong co cua vao.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import ngan_sach as NS  # noqa: E402


def test_moi_con_so_suc_chua_deu_duong():
    for lop, tran in NS.SUC_CHUA.items():
        assert tran >= 1, "%s co tran %s" % (lop, tran)
    assert NS.SUC_CHUA["TESTER"] == 1, "MOT terminal64 la rang buoc VAT LY"
    assert NS.SUC_CHUA["BANG_THONG"] == 1, (
        "bai mang lon: 1 luong 8,9 GB/s vs 20 luong 9,4 - song song hoa an 6%")


def test_nhip_host_rieng_tung_host():
    """mql5 va CDN cua github khong the chung mot nhip."""
    assert NS.NHIP_HOST["www.mql5.com"] >= 5.0
    assert NS.NHIP_HOST["api.github.com"] >= 60.0   # 60 luot/GIO
    assert NS.NHIP_HOST["raw.githubusercontent.com"] < NS.NHIP_HOST["www.mql5.com"]
    assert "_mac_dinh" in NS.NHIP_HOST, "host la gi cung phai co nhip"


def test_cho_nhip_that_su_cho(tmp_path, monkeypatch):
    """Va no phai ghi xuong DIA - hai tien trinh chia nhau mot nhip."""
    monkeypatch.setattr(NS, "SO_NHIP", tmp_path / "nhip.json")
    monkeypatch.setitem(NS.NHIP_HOST, "thu.local", 1.5)
    NS.cho_nhip("thu.local")
    t0 = time.time()
    NS.cho_nhip("thu.local")
    cho = time.time() - t0
    assert 1.0 < cho < 3.0, "cho %.2fs, phai ~1,5s" % cho
    assert (tmp_path / "nhip.json").exists(), "nhip phai nam tren DIA"


def test_het_dia_thi_TU_CHOI(monkeypatch):
    from nhan import dia as D
    monkeypatch.setattr(D, "NGUONG_GB", D.con_gb() + 1000)
    with pytest.raises(D.DiaDay):
        with NS.xin("LLM", "thu"):
            pass


def test_thieu_RAM_thi_TU_CHOI(monkeypatch):
    monkeypatch.setattr(NS, "may", lambda: {"ram_trong_gb": 0.5, "cpu": 10,
                                            "python": 3, "dia_gb": 99})
    with pytest.raises(NS.HetCho):
        with NS.xin("CPU_NANG", "thu", ram_gb=8.0):
            pass


def test_qua_nhieu_tien_trinh_thi_TU_CHOI(monkeypatch):
    monkeypatch.setattr(NS, "may", lambda: {"ram_trong_gb": 99, "cpu": 10,
                                            "python": 999, "dia_gb": 99})
    monkeypatch.setattr(NS, "don_mo_coi", lambda **k: 0)
    with pytest.raises(NS.HetCho):
        with NS.xin("LLM", "thu"):
            pass


def test_lop_day_thi_TU_CHOI(monkeypatch, tmp_path):
    """TESTER co DUNG mot cho - xin cai thu hai phai truot."""
    monkeypatch.setattr(NS, "_KHOA", tmp_path / "khoa")
    monkeypatch.setattr(NS, "may", lambda: {"ram_trong_gb": 99, "cpu": 10,
                                            "python": 3, "dia_gb": 99})
    # Cung tien trinh thi the trung ten, nen gia lap "tien trinh khac" bang
    # mot the mang pid 4 (System cua Windows - luon song).
    gia = tmp_path / "khoa" / "TESTER" / ("%d.the" % 4)
    with NS.xin("TESTER", "viec mot"):
        assert NS._dang_giu("TESTER") == 1
        gia.write_text("gia")
        with pytest.raises(NS.HetCho):
            with NS.xin("TESTER", "viec hai"):
                pass
    gia.unlink()
    assert NS._dang_giu("TESTER") == 0, "the phai duoc tra lai khi xong"


def test_the_cua_tien_trinh_da_chet_duoc_THU_HOI(monkeypatch, tmp_path):
    """Khong co buoc thu hoi thi mot lan Ctrl-C khoa vinh vien mot lop."""
    monkeypatch.setattr(NS, "_KHOA", tmp_path / "khoa")
    thu = tmp_path / "khoa" / "TESTER"
    thu.mkdir(parents=True)
    (thu / "999999.the").write_text("tien trinh da chet")
    assert NS._dang_giu("TESTER") == 0
    assert not (thu / "999999.the").exists()


def test_bang_khong_no():
    r = NS.bang(in_ra=lambda *a: None)
    assert set(r) >= {"may", "lop"}
    assert r["may"]["ram_trong_gb"] > 0


def test_don_mo_coi_khong_giet_tien_trinh_co_cha():
    """Chi giet MO COI. Giet nham mot tien trinh dang lam viec that thi te
    hon de no song."""
    import psutil
    truoc = sum(1 for p in psutil.process_iter(["name"])
                if (p.info.get("name") or "").lower() == "python.exe")
    NS.don_mo_coi(qua_gio=999999, in_ra=lambda *a: None)   # khong cai nao du gia
    sau = sum(1 for p in psutil.process_iter(["name"])
              if (p.info.get("name") or "").lower() == "python.exe")
    assert sau >= truoc - 1
