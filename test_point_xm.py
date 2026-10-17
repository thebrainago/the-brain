# -*- coding: utf-8 -*-
"""point_cua phai dung point DA DO cua XM (17/10/2026).

Truoc ngay nay point duoc DOAN theo lop tai san: JP225Cash (point 1,0) bi doan 0,01 nen spread do tu cot `spread`
cua bar bi tinh thap 100 lan, va moi he JP225 "lai" nho phi gia. Doan sai o 214/407 ma XM da do.
"""
import json

from nhan import chi_phi as CP


def test_dung_point_da_do_cua_xm(tmp_path, monkeypatch):
    f = tmp_path / "chi_phi_do.json"
    f.write_text(json.dumps({"_theo_san": {"XM": {"JP225CASH": {"point": 1.0, "san": "XM", "gia_luc_do": 64676.0}}},
                             "USDTRY": {"point": 1e-05, "san": "XM", "gia_luc_do": 40.0},
                             "UK100": {"point": 0.1, "san": "MetaQuotes", "gia_luc_do": 10227.4}}), encoding="utf-8")
    monkeypatch.setattr(CP, "CAU_HINH", f)
    assert CP.point_cua("XM_JP225CASH", 64676.0) == 1.0
    assert CP.point_cua("XM_USDTRY", 40.0) == 1e-05
    # ma khong co tien to XM_: khong biet san -> van doan nhu cu (khong lay nham diem cua MetaQuotes)
    assert CP.point_cua("UK100", 10227.4) == 0.01
    # ma XM chua do -> doan nhu cu
    assert CP.point_cua("XM_EURUSD", 1.1) == 1e-05
