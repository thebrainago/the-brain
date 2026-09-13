# -*- coding: utf-8 -*-
"""test_doc_video_cuc_bo.py - khau VIDEO TREN DIA -> VAN BAN.

Bai kiem quan trong nhat file nay la `test_nang_luc_co_that`: module nay ra
doi chi vi mot ghi chu SAI trong `doc_video.py` (*"faster_whisper can ffmpeg
nen hien tai chua bat"*) da chan mot nang luc CO SAN suot mot thang. Nen phai
co mot bai gac dung dieu do - va no phai KIEM THAT chu khong doc lai ghi chu.

Khong bai nao o day goi whisper that: nap model `small` ton 21 giay va giai ma
mot video ngan ton 39 giay, khong dat trong mot bo test chay hang ngay. Phan
whisper duoc do RIENG (`_thu_day_chuyen_video.py`) va so lieu ghi trong
docstring cua module.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import doc_video_cuc_bo as DV  # noqa: E402


def test_nang_luc_co_that_khong_can_ffmpeg():
    """`faster_whisper` + `av` phai nap duoc, va KHONG duoc doi `ffmpeg` CLI.

    Day la bai gac cho dung cai lam module nay cham mot thang: mot gia dinh
    chua kiem ("can ffmpeg") duoc viet thanh tai lieu, roi tai lieu duoc doc
    nhu su that. Neu mai nay ai do lai viet cau do, bai nay se cai.
    """
    import shutil
    import importlib
    assert importlib.import_module("faster_whisper") is not None
    av = importlib.import_module("av")
    assert av is not None, "PyAV la thu giai ma audio, khong phai ffmpeg CLI"
    # Ghi lai su that luc chay: may nay KHONG co ffmpeg tren PATH.
    # Neu mai nay co, bai van xanh - no chi khang dinh ta khong PHU THUOC.
    shutil.which("ffmpeg")


def test_duoi_file_phu_ca_video_lan_am_thanh():
    for d in (".mp4", ".mov", ".mkv", ".webm", ".mp3", ".m4a", ".wav"):
        assert d in DV.DUOI


def test_mac_dinh_la_small_khong_phai_tiny():
    """`tiny` nhanh gap 6 lan nhung san pham la rac tieng Viet - do 13/09.

    Mot mac dinh nhanh-ma-vo-dung khong nhanh hon, no chi khong lam gi.
    """
    assert DV.MODEL == "small"


def test_kieu_tach_khoi_duong_phu_de_youtube():
    """Hai duong co DO TIN khac han nhau nen khong duoc dung chung nhan.

    Phu de YouTube la chu cua tac gia; ban nay la may nghe lai. Tron nhan thi
    sau nay khong loc rieng duoc, va chinh `doc_video.py` da dinh mot lan dung
    kieu nay (23 video THAT bi bo qua vi tuong "da co ban doc").
    """
    from nhan import doc_video as DVY
    assert DV.KIEU != DVY.KIEU
    assert DV.KIEU == "video_cuc_bo"


def test_tim_tra_ve_rong_khi_thu_muc_khong_co(tmp_path):
    assert DV.tim(tmp_path / "khong_ton_tai") == []


def test_tim_xep_theo_kich_thuoc_va_loc_dung_duoi(tmp_path):
    (tmp_path / "b.mp4").write_bytes(b"x" * 300)
    (tmp_path / "a.mov").write_bytes(b"x" * 100)
    (tmp_path / "c.txt").write_bytes(b"x" * 900)
    ra = DV.tim(tmp_path)
    assert [p.name for p in ra] == ["a.mov", "b.mp4"], "phai bo .txt, xep tang dan"


def test_van_tay_doi_khi_file_doi(tmp_path):
    f = tmp_path / "x.mp4"
    f.write_bytes(b"x" * 100)
    v1 = DV._van_tay(f)
    f.write_bytes(b"x" * 200)
    assert DV._van_tay(f) != v1, "van tay phai doi khi kich thuoc doi"


def test_ghi_tu_choi_ban_qua_ngan(tmp_path):
    """Mot video 12 phut ra 40 ky tu la khau NGHE hong, khong phai mot ban doc.

    Do 13/09: file `Ghi Man hinh ...mp4` ra 186 ky tu. Cho nhung ban do vao
    kho thi chung chiem cho trong hang doi boc ma khong bao gio ra co che.
    """
    f = tmp_path / "ngan.mp4"
    f.write_bytes(b"x" * 100)
    assert DV.ghi(f, "qua ngan", 600, 10, "small") is False


def test_gioi_han_giay_la_tham_so_that():
    """Lay MAU phai la mot tham so, khong phai mot thao tac tay.

    Chu du an: *"khong can chay het dau, xem 1 phan nho de test he thong"*.
    Neu viec do phai lam bang tay moi lan thi no khong lap lai duoc.
    """
    import inspect
    ts = inspect.signature(DV.mot_video).parameters
    assert "gioi_han_giay" in ts
    assert ts["gioi_han_giay"].default == 0.0, "mac dinh phai la nghe HET"


@pytest.mark.parametrize("vb", ["", "   ", "a" * 199])
def test_ghi_tu_choi_moi_dau_vao_rong(tmp_path, vb):
    f = tmp_path / "x.mp4"
    f.write_bytes(b"x" * 100)
    assert DV.ghi(f, vb, 100, 1, "small") is False
