# -*- coding: utf-8 -*-
"""ban_giao_song.py - SO BAN GIAO SONG, ghi lien tuc chu khong doi cuoi phien.

VI SAO CO FILE NAY (31/08/2026, chu du an giao)
  `b ket` sinh ban giao RAT tot - nhung no chi chay khi phien ket thuc TU TE.
  Phien that hay chet giua chung: het han muc token, may ngu, nguoi dong cua so.
  Khi do toan bo "hom nay lam gi, dang do cai gi" nam trong dau agent va mat
  sach; ban giao con lai la ban cua HOM QUA.

  File nay lam mot viec: moi buoc lam xong ghi MOT dong vao `BAN_GIAO_SONG.md`,
  kem trang thai may tu dien. Phien chet luc nao thi ban giao day toi luc do.

BA DIEU NO TU DIEN (khong ai chep tay)
  - moc thoi gian va commit git gan nhat,
  - tien trinh nen dang chay (bo do dai, dieu phoi 24/7),
  - viec dang do: dong cuoi cua moi file .log trong reports/ vua doi trong 2 gio.

Chay:
    python ban_giao_song.py "vua sua xong X, dang cho Y chay"   # ghi mot dong
    python ban_giao_song.py --tu-dong        # chi chup trang thai (dung cho hook)
    python ban_giao_song.py --xem            # in ban giao song hien tai
    python ban_giao_song.py --dong-phien     # gop vao TIEP_TUC_MAI.md roi don
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
GOC = LAB.parent
SO = LAB / "BAN_GIAO_SONG.md"
TRAN_DONG = 400          # giu 400 dong gan nhat, cat phan cu ve nhat_ky


def _git_gan_nhat(n: int = 3) -> list[str]:
    try:
        r = subprocess.run(["git", "log", f"-{n}", "--oneline"], cwd=str(GOC),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="ignore", timeout=15)
        return [x for x in r.stdout.splitlines() if x.strip()]
    except Exception:
        return []


def _tien_trinh_nen() -> list[str]:
    """Tien trinh python dang chay tu thu muc lab - do la 'viec dang do'."""
    ra = []
    try:
        import psutil
        for p in psutil.process_iter(["name", "cmdline", "create_time"]):
            try:
                cl = p.info.get("cmdline") or []
                if not cl or "python" not in (p.info.get("name") or "").lower():
                    continue
                lenh = " ".join(cl)
                if "Research SP500" not in lenh and "lab" not in lenh:
                    continue
                ten = next((c for c in cl if c.endswith(".py")), "?")
                phut = int((time.time() - p.info["create_time"]) / 60)
                ra.append(f"{Path(ten).name} (pid {p.pid}, {phut} phut)")
            except Exception:
                continue
    except Exception:
        return []
    return sorted(set(ra))


def _log_vua_doi(gio: int = 2) -> list[str]:
    """Dong cuoi cua moi .log vua ghi trong `gio` gio - viec dang chay noi gi."""
    ra, moc = [], time.time() - gio * 3600
    for f in sorted((LAB / "reports").glob("*.log")):
        try:
            if f.stat().st_mtime < moc:
                continue
            dong = [x.strip() for x in
                    f.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip()]
            if dong:
                ra.append(f"`{f.name}`: {dong[-1][:150]}")
        except Exception:
            continue
    return ra


def chup() -> str:
    """Mot khoi trang thai may tu dien."""
    d = [f"### {time.strftime('%Y-%m-%d %H:%M:%S')} — chup trang thai", ""]
    tt = _tien_trinh_nen()
    d.append(f"- dang chay: {', '.join(tt) if tt else 'khong co tien trinh nen nao'}")
    for x in _log_vua_doi():
        d.append(f"- {x}")
    g = _git_gan_nhat()
    if g:
        d.append(f"- git: {g[0]}")
    return "\n".join(d) + "\n"


def ghi(dong: str = "", tu_dong: bool = False) -> None:
    """Them mot muc vao so. `dong` la loi cua nguoi/agent; phan may thi tu chup."""
    if not SO.exists():
        SO.write_text(
            "# BAN GIAO SONG\n\n"
            "> Ghi LIEN TUC trong phien, khong doi cuoi phien. Phien chet giua\n"
            "> chung (het token, may ngu) thi day van la ban giao day du toi luc\n"
            "> do. `b ket` doc file nay khi chot phien.\n\n", encoding="utf-8")
    khoi = []
    if dong:
        khoi.append(f"### {time.strftime('%Y-%m-%d %H:%M:%S')} — {dong.strip()}\n")
    if tu_dong or not dong:
        khoi.append(chup())
    van = SO.read_text(encoding="utf-8") + "\n" + "\n".join(khoi)
    d = van.splitlines()
    if len(d) > TRAN_DONG:
        cu = LAB / "nhat_ky" / f"BAN_GIAO_SONG_{time.strftime('%Y%m%d_%H%M')}.md"
        cu.parent.mkdir(exist_ok=True)
        cu.write_text("\n".join(d[:len(d) - TRAN_DONG]), encoding="utf-8")
        d = d[:6] + d[len(d) - TRAN_DONG:]
        van = "\n".join(d)
    SO.write_text(van, encoding="utf-8")


def main(argv: list) -> int:
    if "--xem" in argv:
        print(SO.read_text(encoding="utf-8") if SO.exists() else "(chua co)")
        return 0
    if "--tu-dong" in argv:
        ghi("", tu_dong=True)
        return 0
    dong = " ".join(x for x in argv if not x.startswith("--"))
    ghi(dong, tu_dong=bool(dong))
    print(f"[ban giao song] {SO.name} <- {dong[:70] or 'chup trang thai'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
