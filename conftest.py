# -*- coding: utf-8 -*-
"""Canh cho SO CAI THAT trong luc chay bo test.

VI SAO CO FILE NAY (01/09/2026). `test_cham_lai_holdout.py` goi `SO.ghi_ket_qua`
ma khong tro `SO.DB` sang so tam, va no da bom **60 dong `test_cham_lai_*` vao
`nao.db` that** trong mot buoi chieu - moi lan `b test` them ~10 dong. Khong ai
thay, vi mot bo test qua het thi khong ai di dem lai so dong.

Nam file test khac deu tu tro `SO.DB` sang thu muc tam trong `setUp`. Tuc luat
DA CO, no chi khong nam o cho nao bat buoc phai di qua - dung hinh dang loi cua
`cham_lai_holdout` ma chinh file kia dang di bat: mot luat chi song neu no nam
o cho HEP NHAT.

Canh nay khong tro `SO.DB` ho ai ca (lam vay se pha cac bai co chu y doc so
that). No chi dem so dong TRUOC va SAU ca phien va bao neu so cai phinh ra -
mot lan nua, do dac chu khong ap dat.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

#: Bang ma mot bo test khong bao gio duoc lam phinh.
BANG_CANH = ("ket_qua", "fdr", "gia_thuyet", "khang_dinh")


def _dem() -> dict:
    from nhan import so as SO
    ra = {}
    for b in BANG_CANH:
        try:
            ra[b] = int(SO.mot(f"SELECT COUNT(*) n FROM {b}")["n"])
        except Exception:
            ra[b] = -1
    return ra


@pytest.fixture(scope="session", autouse=True)
def canh_so_cai_that(request):
    from nhan import so as SO
    db_that = SO.DB
    if not Path(db_that).exists():
        yield
        return
    truoc = _dem()
    yield
    # `SO.DB` phai duoc tra ve cho cu - neu mot bai quen tra thi phep dem sau
    # se doc nham so tam va bao "khong phinh" trong khi khong biet gi ca.
    if Path(SO.DB) != Path(db_that):
        SO.DB = db_that
    sau = _dem()
    phinh = {b: sau[b] - truoc[b] for b in BANG_CANH
             if truoc[b] >= 0 and sau[b] > truoc[b]}
    if phinh:
        request.session.exitstatus = 1
        print("\n" + "=" * 70)
        print("BO TEST DA LAM PHINH SO CAI THAT:", db_that)
        for b, n in phinh.items():
            print(f"   {b}: +{n} dong")
        print("Bai test nao ghi vao so phai tro SO.DB sang thu muc tam trong")
        print("setUp (xem `SoTam` trong test_ghi_so_fdr.py).")
        print("=" * 70)
        pytest.fail(f"so cai that phinh them {phinh} trong luc chay test",
                    pytrace=False)
