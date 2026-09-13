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
    kho_truoc = _dau_kho()
    yield
    # `SO.DB` phai duoc tra ve cho cu - neu mot bai quen tra thi phep dem sau
    # se doc nham so tam va bao "khong phinh" trong khi khong biet gi ca.
    if Path(SO.DB) != Path(db_that):
        SO.DB = db_that
    sau = _dem()
    phinh = {b: sau[b] - truoc[b] for b in BANG_CANH
             if truoc[b] >= 0 and sau[b] > truoc[b]}
    # Canh CA PHIEN cho kho co che - duong duy nhat con lai duoi xdist.
    kho_sau = _dau_kho()
    if kho_truoc and kho_sau and kho_truoc != kho_sau:
        print("\n" + "=" * 70)
        print("BO TEST DA LAM DOI KHO CO CHE THAT: %s -> %s byte"
              % (kho_truoc[0], kho_sau[0]))
        print("Chay lai MOT tien trinh (`b test1`) de biet bai nao.")
        print("=" * 70)
        request.session.exitstatus = 1

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


# ---------------------------------------------------------------- KHO CO CHE
#
# Them 13/09/2026, sau khi kho co che bi ghi de **2.975 -> 21, hai lan trong
# mot buoi**. Mot trong hai nguyen nhan la mot BAI TEST:
# `test_chan_hang_so.test_nap_vao_mau_tu_choi_spec_khong_qua_cong` doc kho
# THAT, them mot spec hong, roi tra lai trong `finally`. Ba cach hong:
#
#   * chay 6 nhan song song -> hai nhan doc-sua-ghi cung mot file;
#   * `doc_kho()` hong mot lan (dia day) -> `goc = []` -> `finally` ghi de
#     ca kho bang rong;
#   * tien trinh bi giet -> `finally` khong chay -> spec rac o lai trong kho
#     san xuat, va no lam do mot bai kiem KHAC trong cung file.
#
# `canh_so_cai_that` o tren canh `nao.db` nhung khong canh file kho. Day la
# dung lo hong ma no duoc sinh ra de bit, chi o mot file khac - nen bit not.
#
# Canh theo TUNG BAI chu khong theo ca phien: biet "bo test co lam doi kho
# khong" thi khong sua duoc gi, phai biet BAI NAO.
_KHO_DAU = {}


def _dau_kho():
    """Dau van tay re tien cua file kho: (kich thuoc, thoi diem sua)."""
    try:
        from nhan import ngu_phap as NP
        f = Path(NP.KHO_CO_CHE)
        if not f.exists():
            return None
        t = f.stat()
        return (t.st_size, t.st_mtime_ns)
    except Exception:
        return None


def _co_xdist(request) -> bool:
    """Dang chay nhieu nhan song song khong.

    Canh THEO TUNG BAI khong dung duoc duoi xdist: nhan A dang chay mot bai
    vo can trong khi nhan B ghi kho mot cach hop le -> bai cua A bao do. Do
    la mot cong bao NHAM, va mot cong bao nham thi som muon se bi tat di -
    tuc te hon ca khong co cong.
    #
    # Do that 13/09: them canh nay roi chay `-n 6`, hai bai khong lien quan
    # bao do (`test_mau_viet_tay_khong_bi_cong_nay_cham`) va xdist tu no nem
    # INTERNALERROR.
    """
    return hasattr(request.config, "workerinput")


@pytest.fixture(autouse=True)
def canh_kho_co_che(request):
    if _co_xdist(request):
        yield
        return
    truoc = _dau_kho()
    yield
    sau = _dau_kho()
    if truoc is None or sau is None or truoc == sau:
        return
    pytest.fail(
        "bai test nay DA SUA kho co che THAT (%s -> %s byte). Bai test khong "
        "duoc sua du lieu san xuat: tro `NP.KHO_CO_CHE` (va `NP.MOC_CAO`) sang "
        "thu muc tam - xem `test_chan_hang_so."
        "test_nap_vao_mau_tu_choi_spec_khong_qua_cong` lam mau."
        % (truoc[0], sau[0]), pytrace=False)
