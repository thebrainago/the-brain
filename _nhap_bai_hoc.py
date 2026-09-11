# -*- coding: utf-8 -*-
"""_nhap_bai_hoc.py - dua tri thuc dang nam NGOAI repo vao so `bai_hoc`.

Ba nguon, theo thu tu do tin cay:

  1. `~/.claude/.../memory/*.md`  - 130 the Claude da viet qua nhieu phien.
     Day la tai san that cua du an nhung nam trong profile nguoi dung: mat may
     la mat, va `evolution.py` khong bao gio doc duoc.
  2. `AGENTS.md` + `CLAUDE.md` + `lab/CLAUDE.md` - cac muc danh so va cac muc
     "BAY DA SAP THAT". Chung la quy tac chu du an va bay do luong.
  3. `reports/*.json` - ket qua AM da do duoc (lam sau, can schema rieng).

Cong cua `bai_hoc.them` doi `bang_chung` cho hai loai nang nhat, nen the nao
khong co so se bi TU CHOI - do la co y: mot cau "huong X khong an" khong kem
phep do se thanh dieu cam khong ai kiem lai duoc.

Chay:  python _nhap_bai_hoc.py [--that]        (khong co --that thi chi thu)
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import bai_hoc as BH  # noqa: E402

MEM = Path(os.path.expanduser("~")) / ".claude" / "projects" / \
    "C--Users-SV-STORE" / "memory"

#: Dau hieu mot doan CO SO DO - dieu kien de duoc xep vao hai loai nang.
_CO_SO = re.compile(r"\d[\d.,]*\s*(?:%|bps|lenh|nam|ngay|bar|USD|lan|/\d)|"
                    r"\d+\s*/\s*\d+|Sharpe|CAGR|p\s*=|t\s*=", re.I)

_TRANH = re.compile(r"khong an|that bai|da chet|dung thu lai|khong song|"
                    r"khong qua|am tinh|KHONG duoc|dung dung|tranh", re.I)
_BAY = re.compile(r"bay|noi doi|sai|lech|im lang|khong bao loi|nham|hong|"
                  r"KIEM TRUOC|DOC TRUOC", re.I)
_QUY_TAC = re.compile(r"quy tac cua nguoi dung|chu du an|chu he thong", re.I)


def _loai(tieu_de: str, than: str) -> str:
    """Thu tu kiem la co y, va lan dau toi dat SAI.

    Ban dau toi kiem `_BAY` truoc `_TRANH`, ket qua: 147 the vao `bay_do_luong`
    va **0 the** vao `huong_nen_tranh`. Vi mot the "huong X khong an" hau nhu
    luon co chu "sai"/"hong" trong than bai. Ma `huong_nen_tranh` moi la loai tra
    loi cau hoi dat nhat cua so nay - "cai nay da thu chua".

    Nay: TIEU DE quyet dinh truoc (no noi the NAY la ve cai gi), than bai chi
    dung de pha hoa.
    """
    if _QUY_TAC.search(tieu_de) or _QUY_TAC.search(than[:300]):
        return "quy_tac_nguoi_dung"
    if _TRANH.search(tieu_de):
        return "huong_nen_tranh"
    if _BAY.search(tieu_de):
        return "bay_do_luong"
    if _TRANH.search(than[:400]):
        return "huong_nen_tranh"
    if _BAY.search(than[:400]):
        return "bay_do_luong"
    return "huong_dang_mo"


def _tu_memory() -> list[dict]:
    if not MEM.exists():
        print(f"khong thay {MEM} - bo qua nguon memory")
        return []
    ra = []
    for f in sorted(MEM.glob("*.md")):
        if f.name.upper() == "MEMORY.MD":
            continue
        vb = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^description:\s*(.+)$", vb, re.M)
        tieu_de = (m.group(1).strip() if m else f.stem.replace("-", " "))
        than = re.sub(r"^---.*?^---\s*", "", vb, flags=re.S | re.M).strip()
        if len(than) < 20:
            continue
        bc = ""
        for dong in than.splitlines():
            if _CO_SO.search(dong):
                bc = dong.strip()[:400]
                break
        ra.append({"ma": f"mem::{f.stem}", "loai": _loai(tieu_de, than),
                   "tieu_de": tieu_de[:200], "noi_dung": than[:2000],
                   "bang_chung": bc, "nguon": str(f), "ngay": ""})
    return ra


def _tu_hien_phap() -> list[dict]:
    """Cac muc DANH SO trong AGENTS.md / CLAUDE.md - moi muc mot the."""
    ra = []
    for ten in ("../CLAUDE.md", "../AGENTS.md", "CLAUDE.md"):
        f = GOC / ten
        if not f.exists():
            continue
        vb = f.read_text(encoding="utf-8", errors="ignore")
        # "12. **Tieu de.** than..." cho den muc danh so ke tiep
        for m in re.finditer(r"^(\d{1,2})\.\s+\*\*(.+?)\*\*(.*?)(?=^\d{1,2}\.\s+\*\*|\Z)",
                             vb, re.S | re.M):
            so, td, than = m.group(1), m.group(2).strip(), m.group(3).strip()
            if len(than) < 30:
                continue
            bc = ""
            for dong in than.splitlines():
                if _CO_SO.search(dong):
                    bc = dong.strip()[:400]
                    break
            ra.append({"ma": f"hp::{f.name}::{so}", "loai": _loai(td, than),
                       "tieu_de": td[:200], "noi_dung": than[:2000],
                       "bang_chung": bc, "nguon": f.name, "ngay": ""})
    return ra


def chay(that: bool = False) -> dict:
    the = _tu_memory() + _tu_hien_phap()
    dem = Counter()
    tu_choi = []
    for t in the:
        dem[f"nguon::{t['ma'].split('::')[0]}"] += 1
        dem[f"loai::{t['loai']}"] += 1
        if not that:
            continue
        kq = BH.them(**t)
        if kq["nhan"]:
            dem["NHAN"] += 1
        else:
            dem["TU_CHOI"] += 1
            tu_choi.append((t["ma"], kq["ly_do"][0][:90]))
    print(f"the doc duoc: {len(the)}")
    for k, v in sorted(dem.items()):
        print(f"  {k:34s} {v}")
    if tu_choi:
        print(f"\nTU CHOI {len(tu_choi)} - 8 vi du:")
        for ma, ly in tu_choi[:8]:
            print(f"  {ma[:46]:48s} {ly}")
    if that:
        print("\nso hien co:", BH.dem())
    else:
        print("\n(chua ghi - them `--that` de ghi that)")
    return {"doc": len(the), "dem": dict(dem)}


if __name__ == "__main__":
    chay("--that" in sys.argv)
