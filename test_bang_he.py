# -*- coding: utf-8 -*-
"""test_bang_he.py - BANG SAN PHAM phai doc CA HAI nguon, va khong duoc tron.

Do 13/09/2026: chang 4 cua `to_hop` (holdout) la phep thu duy nhat co nghia
trong ca pheu, va ket qua cua no khong di dau ca - `vong_day_du._cham_tien`
in mot bang roi tra ve dict dem. Bang san pham khong bao gio thay chung.
"""
import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import bang_he as BH   # noqa: E402

MAU = {
    "holdout": [
        {"ma": "GBPTRY", "khung": "D1", "co_che": "x", "cau_truc": "thi_truong",
         "luat": "-", "dd20_train": 164.3, "dd20_hold": 82.9, "moc_hold": 81.0,
         "chan_hold": 60, "ty_le_hold_tren_train": 0.5, "qua_holdout": True},
        {"ma": "EURUSD", "khung": "D1", "co_che": "y", "cau_truc": "thi_truong",
         "luat": "-", "dd20_train": 30.0, "dd20_hold": 25.0, "moc_hold": 5.0,
         "chan_hold": 90, "ty_le_hold_tren_train": 0.83, "qua_holdout": True},
        {"ma": "GOLD", "khung": "D1", "co_che": "z", "dd20_train": 9.0,
         "dd20_hold": 1.0, "moc_hold": 4.0, "qua_holdout": False},
    ]
}


def _tep(tmp_path) -> Path:
    p = tmp_path / "TO_HOP.json"
    p.write_text(json.dumps(MAU), encoding="utf-8")
    return p


def test_chi_lay_dong_QUA_holdout(tmp_path):
    ds = BH.tu_pheu(_tep(tmp_path))
    assert len(ds) == 2
    assert all("GOLD" not in d["he"] for d in ds)


def test_hon_moc_la_hieu_voi_MOC_cua_chinh_nua_kiem(tmp_path):
    """Con so quyet dinh la `dd20_hold - moc_hold`, khong phai `dd20_hold`.
    GBPTRY dd20 82,9 nghe to, nhung moc cua chinh no la 81,0 - hon 1,95."""
    ds = {d["ma"]: d for d in BH.tu_pheu(_tep(tmp_path))}
    assert abs(ds["GBPTRY"]["hon_moc"] - 1.9) < 0.11
    assert abs(ds["EURUSD"]["hon_moc"] - 20.0) < 0.01


def test_xep_theo_HON_MOC_khong_theo_dd20(tmp_path):
    """Xep theo `dd20_hold` thi GBPTRY (82,9) len dau EURUSD (25,0) - trong khi
    GBPTRY chi hon moc 1,95 con EURUSD hon 20,0."""
    ds = BH.tu_pheu(_tep(tmp_path))
    assert ds[0]["ma"] == "EURUSD"


def test_thieu_tep_thi_tra_ve_rong_khong_nem_loi(tmp_path):
    assert BH.tu_pheu(tmp_path / "khong_co.json") == []
    hong = tmp_path / "hong.json"
    hong.write_text("{khong phai json", encoding="utf-8")
    assert BH.tu_pheu(hong) == []


def test_KHONG_ghi_gi_vao_ket_qua(tmp_path):
    """He qua holdout cua pheu la mot phep DO, khong duoc chiem suat FDR
    (memory `do-dac-khong-duoc-chiem-suat-fdr`). Doc no khong duoc dong vao
    bang `ket_qua` mot dong nao."""
    from nhan import so as SO
    truoc = SO.mot("SELECT COUNT(*) n FROM ket_qua")["n"]
    BH.tu_pheu(_tep(tmp_path))
    BH.thu_hoach()
    assert SO.mot("SELECT COUNT(*) n FROM ket_qua")["n"] == truoc


def test_bang_in_ca_HAI_khoi():
    dong = []
    ra = BH.bang(in_ra=dong.append)
    vb = "\n".join(dong)
    assert "HE DA QUA CONG" in vb
    assert "QUA HOLDOUT CUA PHEU" in vb
    assert "chua qua cong that" in vb.lower()
    assert "so_qua_pheu" in ra
