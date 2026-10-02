# -*- coding: utf-8 -*-
"""HIEU CHUAN HAI CHIEU cua nha nghien cuu tren chuoi CO DAP AN (cham: ~1-2 phut).

Luat du an: *"hieu chuan cong phai HAI CHIEU - mot cong tu choi TAT CA cho so lieu y
het mot cong tot"*. Nen o day do ca hai: edge cai san phai DAT qua niem phong; nhieu va
bay chi phi thi KHONG duoc DAT. Chay day du + ti le bao dong gia: `b nc kiem 30`.
"""
from __future__ import annotations

import pytest

from nhan import nc_so_tay as ST
from nhan import nc_tu_lai as TL


@pytest.mark.cham
def test_tu_lai_hai_chieu_tren_chuoi_co_dap_an(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    r = TL.hieu_chuan(cac_ma=("TONG_HOP_NHIEU_1", "TONG_HOP_HOI_QUY_1", "TONG_HOP_XU_HUONG_1"),
                      so_null=100, ghi_bao_cao=False, in_ra=lambda *_: None)
    theo = {k["ma"]: k for k in r["chi_tiet"]}
    assert theo["TONG_HOP_HOI_QUY_1"]["ket_cuc"] == "DAT", "bo sot edge cai san"
    assert theo["TONG_HOP_NHIEU_1"]["ket_cuc"] != "DAT", "bao dong gia tren nhieu"
    assert theo["TONG_HOP_XU_HUONG_1"]["ket_cuc"] != "DAT", "quen tru chi phi (bay chi phi)"
    assert r["sai"] == 0
    assert all(d["dung"] for d in r["hoc_tu_lenh"]), r["hoc_tu_lenh"]
    assert ST.DB == tmp_path / "nc.db", "hieu chuan phai tra so tay ve cho cu"


# ---------------------------------------------------------------- dau ra gon (khong chay hieu chuan that)
def _gia(sai=0):
    return {"so_kich_ban": 7, "dung": 6, "chua_ket_luan": 1, "sai": sai, "bao_dong_gia": 0, "hoc_tu_lenh_dung": "4/4",
            "chi_tiet": [{"ma": "x" * 400}] * 7, "hoc_tu_lenh": [{"y": "z" * 400}] * 4, "bao_cao": "reports/NC_HIEU_CHUAN.md",
            "bao_dong_gia_tim_quy_luat": {"so_hat": 30, "p_tot_nhat": [0.5] * 30, "ty_le_p_le_0_05": 0.067, "ty_le_p_le_0_10": 0.133},
            "cong_suat": {"so_hat": 8, "do_tim_rong_phat_hien": 3, "co_chu_dich_phat_hien": 8, "co_chu_dich_bao_dong_gia_tren_nhieu": 0,
                          "chi_tiet": {"rong": [True] * 8}},
            "cong_ba_doan": {k: {"so_hat": 10, "khong_edge": {"NHIEU": {"y_tuong": 200, "dat_niem_phong": 1},
                                                              "BETA": {"y_tuong": 200, "dat_niem_phong": 10}},
                                 "co_edge": {"HOI_QUY": {"y_tuong": 10, "dat_niem_phong": 10}}, "chi_tiet": ["q" * 300] * 10}
                             for k in ("H4", "D1")}}


def _chay_main(monkeypatch, argv, sai=0):
    import io
    from contextlib import redirect_stdout
    goi = {}

    def gia(**kw):
        goi.update(kw)
        return _gia(sai)
    monkeypatch.setattr(TL, "hieu_chuan", gia)
    b = io.StringIO()
    with redirect_stdout(b):
        rc = TL.main(argv)
    return rc, b.getvalue(), goi


def test_kiem_in_mot_dong_gon_va_giu_dung_con_so(monkeypatch):
    rc, out, goi = _chay_main(monkeypatch, ["kiem", "30"])
    assert rc == 0 and len(out) < 1500 and out.count("\n") == 1, "dau ra mac dinh phai la MOT dong ~700 ky tu, khong phai ~25.000"
    assert "tim rong 3/8" in out and "co chu dich 8/8" in out and "NHIEU 1/200" in out and "H4" in out and "D1" in out
    assert '"dung": 6' in out and '"sai": 0' in out and '"hoc_tu_lenh_dung": "4/4"' in out and "NC_HIEU_CHUAN.md" in out
    assert goi["so_hat_bao_dong"] == 30 and goi["so_hat_cong_suat"] == 8 and goi["in_ra"] is not print, "khong in tien trinh tung kich ban"


def test_kiem_v_in_het_nhu_cu_va_ma_thoat_theo_sai(monkeypatch):
    rc, out, goi = _chay_main(monkeypatch, ["kiem", "30", "-v"], sai=1)
    assert rc == 1 and "p_tot_nhat" in out and len(out) > 1500 and goi["in_ra"] is print
    rc, out, _ = _chay_main(monkeypatch, ["kiem"], sai=0)
    assert rc == 0 and '"sai": 0' in out
