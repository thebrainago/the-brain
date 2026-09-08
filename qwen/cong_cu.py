# -*- coding: utf-8 -*-
"""cong_cu.py - Bo cong cu LangChain cho qwen. DANH SACH TRANG, khong co vo shell.

## Nguyen tac: qwen DOC va VIET, khong CHAY va khong CHAM

Khong co cong cu nao o day chay lenh tuy y, xoa file, hay dat trang thai DAT/AM.
Ly do khong phai so qwen pha hoai - la vi mot LLM chay khong nguoi truc nhieu
NGAY ma co quyen tu phong lenh thi sai lam cua no khong con dau vet de truy.

  - phong viec  -> chi tu `NHIEM_VU.json` (bang do nguoi viet)
  - cham ket qua-> `qwen/cong.py` (code tat dinh)
  - qwen        -> doc ket qua, viet nhat ky, DE XUAT viec (vao hang cho, khong chay)

## `hoi_kho` chi cho SELECT

Va cho MOT cau. Chuoi nhieu cau (`;`) bi tu choi - do la duong de mot cau UPDATE
di kem sau mot cau SELECT.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from langchain_core.tools import tool

from . import cau_hinh as CH
from . import cong as CONG

#: dat boi `chay.py` truoc khi goi tac tu
NGU_CANH: dict = {"so_tay": None, "bang": None}

TRAN_KY_TU = 6000


def _cat(s: str, n: int = TRAN_KY_TU) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n] + "\n...(cat con %d ky tu)" % (len(s) - n)


# --------------------------------------------------------------------- doc
@tool
def xem_bang_viec() -> str:
    """Xem toan bo bang viec: viec nao xong, viec nao dang chay, viec nao dang cho gi."""
    st, bg = NGU_CANH["so_tay"], NGU_CANH["bang"]
    if not st or not bg:
        return "chua nap ngu canh"
    return _cat(bg.bang_chu(st))


@tool
def doc_ket_qua(ma_viec: str) -> str:
    """Doc ket qua mot viec da chay: cong cham gi, cac con so, va duoi nhat ky chay.

    ma_viec: ma trong bang viec, vi du "V1_dao_GER40".
    """
    st = NGU_CANH["so_tay"]
    v = (st.d["viec"].get(ma_viec) if st else None)
    if not v:
        return "khong co viec `%s` trong so tay (chua chay bao gio?)" % ma_viec
    log = ""
    p = CH.LOG / ("%s.log" % ma_viec)
    if p.exists():
        from .tien_trinh import duoi_log
        log = duoi_log(p, 3000)
    return _cat(json.dumps({k: v.get(k) for k in
                            ("trang_thai", "lan", "lenh", "ma_thoat", "giay", "cong")},
                           ensure_ascii=False, indent=1) + "\n\n--- duoi log ---\n" + log)


@tool
def doc_file_bao_cao(ten_file: str) -> str:
    """Doc mot file trong lab/reports/ (JSON hoac .md). Chi doc, khong ghi.

    ten_file: ten file, vi du "DEM_CHAN_DUONG_GER40Cash.json".
    """
    ten = Path(ten_file).name          # chan ../ va duong dan tuyet doi
    p = CH.BAO / ten
    if not p.exists():
        gan = sorted(x.name for x in CH.BAO.glob("*%s*" % ten.split(".")[0][:12]))[:12]
        return "khong co reports/%s. File ten gan giong: %s" % (ten, gan or "khong co")
    if p.stat().st_size > 4_000_000:
        return "file %s nang %.1f MB - qua lon de doc thang. Dung hoi_kho hoac xin " \
               "mot ban tom tat." % (ten, p.stat().st_size / 1e6)
    t = p.read_text(encoding="utf-8", errors="replace")
    if ten.endswith(".json"):
        try:
            d = json.loads(t)
            dong = CONG._cac_dong(d)
            if len(dong) > 25:
                giong, ly = CONG.dong_giong_het_nhau(dong)
                return _cat("file co %d dong. Kiem bay so 1: %s (%s)\n\n10 dong dau:\n%s"
                            % (len(dong), "DINH BAY" if giong else "sach", ly,
                               json.dumps(dong[:10], ensure_ascii=False, indent=1)))
        except Exception:
            pass
    return _cat(t)


@tool
def liet_ke_bao_cao(loc: str = "") -> str:
    """Liet ke cac file trong lab/reports/ (moi nhat truoc). `loc` la chuoi con de loc."""
    ds = [p for p in CH.BAO.glob("*") if p.is_file()]
    if loc:
        ds = [p for p in ds if loc.lower() in p.name.lower()]
    ds.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    import time
    return _cat("\n".join(
        "%s  %7.0f KB  %s" % (time.strftime("%m-%d %H:%M", time.localtime(p.stat().st_mtime)),
                              p.stat().st_size / 1024, p.name) for p in ds[:60]))


@tool
def doc_ban_giao() -> str:
    """Doc ban giao gan nhat cua du an (lab/TIEP_TUC_MAI.md) - trang thai va viec dang cho."""
    p = CH.LAB / "TIEP_TUC_MAI.md"
    return _cat(p.read_text(encoding="utf-8", errors="replace") if p.exists()
                else "khong co TIEP_TUC_MAI.md", 9000)


@tool
def hoi_kho(cau_sql: str) -> str:
    """Chay MOT cau SELECT tren so cua du an (nao.db / thu_vien.db). Chi doc.

    Bang hay dung: tai_lieu, noi_dung, chi_so_vh, su_kien, ung_vien.
    Vi du: SELECT COUNT(*) n FROM tai_lieu WHERE COALESCE(da_khai_thac,0)=0
    """
    s = (cau_sql or "").strip().rstrip(";")
    if not re.match(r"(?is)^\s*(select|with)\b", s):
        return "chi nhan SELECT/WITH. Cau nay bi tu choi."
    if ";" in s:
        return "chi nhan MOT cau. Bo dau ; va cac cau sau no."
    ra = []
    for ten in ("nao.db", "thu_vien.db"):
        p = CH.LAB / ten
        if not p.exists():
            continue
        try:
            cn = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
            cn.row_factory = sqlite3.Row
            dong = [dict(r) for r in cn.execute(s).fetchmany(50)]
            cn.close()
            ra.append("### %s\n%s" % (ten, json.dumps(dong, ensure_ascii=False,
                                                      indent=1, default=str)))
        except Exception as e:
            ra.append("### %s -> %s" % (ten, str(e)[:200]))
    return _cat("\n".join(ra) or "khong co so nao mo duoc")


@tool
def tim_trong_ma(tu_khoa: str) -> str:
    """Tim mot chuoi trong ma nguon cua lab (bo qua data/reports/backups). Chi doc."""
    tu = (tu_khoa or "").strip()
    if len(tu) < 3:
        return "tu khoa qua ngan"
    ra = []
    for p in list(CH.LAB.glob("*.py")) + list((CH.LAB / "nhan").glob("*.py")):
        try:
            for i, d in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if tu.lower() in d.lower():
                    ra.append("%s:%d: %s" % (p.name, i, d.strip()[:150]))
                    if len(ra) >= 60:
                        return _cat("\n".join(ra) + "\n...(dung o 60 dong)")
        except Exception:
            pass
    return _cat("\n".join(ra) or "khong thay `%s` trong ma nguon" % tu)


# --------------------------------------------------------------------- viet
@tool
def ghi_nhat_ky(ma_viec: str, van: str) -> str:
    """Ghi mot doan nhat ky cho mot viec. Viet tieng Viet, 2-5 cau, di thang van de.

    Phai noi ro: con so nay sinh ra tu bao nhieu phep thu, va no la AM hay
    CHUA DO DUOC. Khong duoc viet "khong co edge" cho mot khau chua chay duoc.
    """
    st = NGU_CANH["so_tay"]
    if not st:
        return "chua nap ngu canh"
    st.ghi_nhat_ky(ma_viec, (van or "").strip()[:2000])
    return "da ghi nhat ky cho %s" % ma_viec


@tool
def de_xuat_viec(ma: str, ten: str, vi_sao: str, lan: str, lenh: str) -> str:
    """De xuat MOT viec moi vao hang cho. KHONG chay ngay - chu du an duyet moi chay.

    ma:    ma ngan, khong dau, vi du "V1_dao_SPAIN35"
    ten:   mot dong noi viec do lam gi
    vi_sao:vi sao no dang lam - dua tren con so nao
    lan:   TESTER | CPU | LLM | MANG | NHE  (TESTER chi chay duoc 1 viec mot luc)
    lenh:  lenh python, vi du "_dem_ghep.py SPAIN35Cash"
    """
    st = NGU_CANH["so_tay"]
    if not st:
        return "chua nap ngu canh"
    if lan not in ("TESTER", "CPU", "LLM", "MANG", "NHE"):
        return "lan `%s` khong hop le" % lan
    st.de_xuat({"ma": ma, "ten": ten, "vi_sao": vi_sao, "lan": lan,
                "lenh": (lenh or "").split(), "uu_tien": 5, "ngay": 9,
                "cong": {"kieu": "chay_duoc"}})
    return ("da xep `%s` vao hang DE XUAT. No khong tu chay - chu du an xem bang "
            "`q de-xuat` roi duyet." % ma)


BO_CONG_CU = [xem_bang_viec, doc_ket_qua, doc_file_bao_cao, liet_ke_bao_cao,
              doc_ban_giao, hoi_kho, tim_trong_ma, ghi_nhat_ky, de_xuat_viec]
