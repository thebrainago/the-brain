# -*- coding: utf-8 -*-
"""test_ban_do.py - Ban do sinh tu ma nguon co doc DUNG do thi goi khong.

Bo do nay tung mu HAI lan trong chinh phien viet no:
  1) bo qua cua vao `.cmd`/`.bat`  -> bao ca goi `qwen/` la MO COI
  2) bo qua `from . import X`      -> bao them 11 module nua la MO COI
Ca hai deu la AM TINH GIA, va mot ban do bao nham khien nguoi doc xoa thu
dang chay. Nen moi khau dinh vao do thi goi deu phai co test.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import ban_do as BD          # noqa: E402


def _khoa_cua(p: Path) -> str:
    return str(p.relative_to(BD.LAB)).replace("\\", "/")


def test_do_thi_co_moi_file():
    canh = BD.do_thi()
    fs = {_khoa_cua(p) for p in BD._cac_file()}
    assert set(canh) == fs


def test_bat_duoc_import_thang():
    """`from nhan import X as Y` - dang pho bien nhat trong lab."""
    canh = BD.do_thi()
    # vong_day_du.py goi `from nhan import to_hop as TH` trong `_to_hop`
    assert "nhan/to_hop.py" in canh["nhan/vong_day_du.py"]


def test_bat_duoc_import_tuong_doi():
    """`from . import X` trong goi qwen. Bo qua khau nay -> ca goi MO COI."""
    canh = BD.do_thi()
    assert "qwen/cong.py" in canh["qwen/chay.py"]
    assert "qwen/bang_viec.py" in canh["qwen/chay.py"]


def test_cua_vao_cmd_duoc_tinh():
    """`q.cmd` chay `-m qwen.chay` - khong doc .cmd thi qwen bao MO COI."""
    cua = BD._tu_cmd()
    assert "qwen/chay.py" in cua


def test_qwen_khong_phai_mo_coi():
    """Phep thu HOI QUY cho ca hai lan mu o tren."""
    toi, _ = BD.voi_toi_duoc()
    for t in ("qwen/chay.py", "qwen/cong.py", "qwen/bang_viec.py",
              "qwen/dieu_toc.py", "qwen/tien_trinh.py"):
        assert t in toi, "%s bi bao mo coi nhung `q` dang chay no" % t


def test_cac_module_hom_nay_da_noi_day():
    """Nhung gi xay 12/09 phai voi toi duoc tu mot cua vao."""
    toi, _ = BD.voi_toi_duoc()
    for t in ("nhan/to_hop.py", "nhan/suy_nguoc.py", "nhan/vao_lenh.py",
              "nhan/vong_day_du.py", "nhan/don_mo_coi.py", "nhan/evo.py",
              "nhan/cham_diem.py"):
        assert t in toi, "%s chua noi vao duong chay nao" % t


def test_script_chay_tay_khong_tinh_la_mo_coi():
    """`_*.py` mo coi la DUNG ban chat - khong duoc tron voi module."""
    vb = BD.sinh(in_ra=None)
    phan = vb.split("## Script chay tay")
    assert len(phan) == 2
    tren = phan[0]
    assert "_mo_xe_z5" not in tren and "_ghep_h4" not in tren


def test_ban_do_co_ba_tru():
    vb = BD.sinh(in_ra=None)
    for t in ("SEEKER", "QUANTLAB", "EVO"):
        assert t in vb


def test_sinh_khong_ghi_de_khi_chi_doc():
    """`sinh()` la ham THUAN - khong duoc dong vao dia."""
    p = BD.LAB / "BAN_DO.md"
    truoc = p.stat().st_mtime if p.exists() else None
    BD.sinh(in_ra=None)
    assert (p.stat().st_mtime if p.exists() else None) == truoc


def test_bat_duoc_duong_ghep_tu_chuoi():
    """`b.py` ghep `LAB / "nhan" / "X.py"` - chuoi trong ma chi con `"X.py"`.

    Lan mu THU BA cua bo do (sau `.cmd` va `from . import`): moi lenh `b` goi
    mot module trong `nhan/` deu bi bao MO COI. Luat L16.
    """
    canh = BD.do_thi()
    assert "nhan/doc_lenh_tester.py" in canh["b.py"]
    assert "nhan/dieu_khien_xa.py" not in canh["b.py"]   # file do o GOC lab


# ===== BAN DO RUNG CANH THI BAO MO COI NHAM (15/09/2026)
def test_import_NHIEU_DONG_khong_duoc_rung_canh(tmp_path):
    r"""Mau cu `[\w, ]` khong co xuong dong, nen mot import nhieu dong chi bat
    duoc DONG DAU.

    `tru/quantlab.py` co `quant_plan` o dong THU BA cua mot import ba dong, nen
    ban do bao `nhan/quant_plan.py` MO COI suot nhieu ngay - trong khi tru
    QUANTLAB goi no moi luot. CLAUDE.md canh bao dung dieu nay: *"mot ban do
    bao nham con te hon ban do cu: no khien nguoi doc xoa thu dang chay"*.
    """
    from nhan import ban_do as BD
    canh = BD.do_thi()
    assert "nhan/quant_plan.py" in canh.get("tru/quantlab.py", set()), (
        "canh tru/quantlab -> quant_plan bi rung: import nhieu dong chua doc het")


def test_import_TRONG_CHUOI_van_duoc_tinh_la_canh():
    """`b.py` goi nhieu module bang `python -c "from nhan import X as Y; ..."`.

    Do la canh THAT. Toi da co mot lan thay ca khoi bang `ast` va ngay lap tuc
    co BON mo coi MOI (`chi_tieu`, `telegram`, `kham_pha_nguon`,
    `nguon_tinix`) - deu la module `b.py` dang goi hang ngay.
    """
    from nhan import ban_do as BD
    canh = BD.do_thi()
    for m in ("chi_tieu", "telegram", "kham_pha_nguon", "nguon_tinix"):
        assert "nhan/%s.py" % m in canh.get("b.py", set()), (
            "mat canh b.py -> %s (import nam trong chuoi)" % m)


def test_CHU_THICH_khong_duoc_tinh_la_canh():
    """Ban do khong duoc tu ve them canh cho chinh no.

    Quet van ban THO thi mot dong chu thich nhac toi `from nhan import X` cung
    thanh canh - va luc do moi con so mo coi trong ban do deu bot dang tin.
    """
    from nhan import ban_do as BD
    import ast as _ast
    from pathlib import Path as _P
    lab = _P(__file__).resolve().parent
    van = (lab / "nhan" / "ban_do.py").read_text(encoding="utf-8")
    assert "from nhan import chi_tieu" in van, (
        "bai kiem nay can mot vi du import trong chu thich cua ban_do.py")
    canh = BD.do_thi()
    assert "nhan/chi_tieu.py" not in canh.get("nhan/ban_do.py", set()), (
        "chu thich cua ban_do dang tu tao ra mot canh MA")


def test_KHONG_CON_MO_COI(tmp_path):
    """Chan neo: 15/09/2026 dua so mo coi ve 0 va so module tren duong chay
    tu 172 len 191. Mot module moi khong duoc ra doi ma khong co cua vao.
    """
    from nhan import ban_do as BD
    d = BD.sinh()
    mo_coi = d.get("mo_coi") if isinstance(d, dict) else None
    if mo_coi is None:
        import pytest
        pytest.skip("ban_do.sinh() khong tra ve khoa `mo_coi`")
    assert not mo_coi, "co %d module MO COI: %s" % (len(mo_coi), list(mo_coi)[:6])
