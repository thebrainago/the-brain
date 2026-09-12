# -*- coding: utf-8 -*-
"""test_luan_dau_chan.py - 400 ho so signal -> kieu chien luoc.

Dong so do: *"Tu chien luoc co lich su se suy nguoc de tim ra phuong phap
trade"*. `tin_hieu_mql5` + `dau_chan` deu mo coi cho toi 12/09, trong khi
`reports/signal_ho_so.json` (400 ho so da boc) nam canh do tu truoc.

Hai dieu phai chan:

  * **`khong_ro` khong duoc dem vao mau so.** No la THIEU DAC TRUNG de phan,
    khong phai "khong co kieu" ([[ket-luan-am-phai-phan-biet-CHUA-DO]]). 149/400
    ho so roi vao nhom nay - gop chung vao "khong phai DCA" thi moi ty le deu sai.
  * **Moi kieu mot thuoc do.** Voi luoi/DCA thi Sharpe khong noi len dieu gi;
    cau hoi la SONG BAO LAU ([[luoi-dca-cach-kiem-tien]]).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import dau_chan as DC            # noqa: E402
from nhan import luan_dau_chan as LD       # noqa: E402


def test_doc_duoc_ho_so():
    ds = LD.doc_ho_so()
    assert len(ds) >= 100
    assert all(isinstance(x, dict) for x in ds)


def test_phan_loai_ra_du_cac_kieu():
    k = LD.phan_loai_het(in_ra=lambda *a: None)
    dem = k["dem"]
    assert k["so"] >= 100
    # Phai co it nhat hai kieu THAT (khong ke `khong_ro`) - mot bo phan loai
    # do het ve mot ro thi khong phan loai gi ca.
    that = {a: b for a, b in dem.items() if a != "khong_ro"}
    assert len(that) >= 2, "moi ho so roi vao mot kieu: %s" % dem


def test_khong_ro_duoc_noi_ra_rieng():
    """Phai NOI ra rang `khong_ro` la thieu dac trung, khong phai ket qua am."""
    ra = []
    LD.phan_loai_het(in_ra=ra.append)
    vb = "\n".join(ra)
    if "khong_ro" in vb:
        assert "THIEU DAC TRUNG" in vb


def test_phan_loai_luoi_dca_dung_hinh_dang():
    """Hinh dang DCA: nhoi khi lo + lo treo dinh cao + ty le thang cao."""
    d = {"nhoi_khi_lo": 0.9, "bac_tai": 5.0, "lo_treo_dinh": 0.5,
         "cat_sach": 0.1, "giu_phut": 3000.0, "thang_pct": 85.0}
    assert DC.phan_loai(d)[0] == "luoi_dca"


def test_phan_loai_gong_lo_khac_luoi_dca():
    """Giu lo ma KHONG nhoi la `gong_lo` - hai kieu khac nhau, dung tron."""
    d = {"nhoi_khi_lo": 0.0, "bac_tai": 1.0, "lo_treo_dinh": 0.5,
         "cat_sach": 5.0, "giu_phut": 3000.0, "thang_pct": 60.0}
    assert DC.phan_loai(d)[0] == "gong_lo"


def test_thieu_dac_trung_ra_khong_ro_va_NOI_THIEU_GI():
    kieu, ly_do = DC.phan_loai({})
    assert kieu == "khong_ro"
    assert "thieu:" in ly_do, "phai noi ro thieu dac trung nao"


def test_theo_kieu_xep_theo_song_bao_lau():
    """Voi lop DCA, thuoc do la SONG BAO LAU - khong phai Sharpe."""
    ra = []
    k = LD.theo_kieu("luoi_dca", tran=5, in_ra=ra.append)
    assert k["so"] > 0
    vb = "\n".join(ra)
    assert "song" in vb.lower()
    assert "sharpe" not in vb.lower()


def test_ghi_so_va_nam_tren_duong_chay():
    LD.phan_loai_het(in_ra=lambda *a: None)
    assert LD.SO.exists()
    d = json.loads(LD.SO.read_text(encoding="utf-8"))
    assert d.get("dem") and d.get("bang")
    from nhan import ban_do as BD
    toi, _ = BD.voi_toi_duoc()
    for t in ("nhan/luan_dau_chan.py", "nhan/dau_chan.py"):
        assert t in toi, "%s van mo coi" % t
