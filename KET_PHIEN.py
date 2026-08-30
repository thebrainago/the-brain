# -*- coding: utf-8 -*-
"""KET PHIEN — mot lenh chot ngay hom nay de mai vao lam ngay duoc.

    b ket "mot cau tom tat phien"
    b ket "..." --khong-commit      chi sinh ban giao, khong dong git

Lam dung sau viec, theo thu tu:
  1. Cat ban `TIEP_TUC_MAI.md` cu sang `nhat_ky/TIEP_TUC_<ngay>.md` (khong mat).
  2. Sinh `TIEP_TUC_MAI.md` moi: phan SO do may tu dien (khong ai chep tay sai
     duoc nua), phan VIEC bung nguyen tu ban cu sang de khong roi viec nao.
  3. `git add -A` + commit ca ngay.
  4. Ghi anh `reports/nhip_song.json` de MAI tinh duoc CHENH LECH.
  5. Them mot dong vao `NHAT_KY.md`.

Vi sao tach so va viec: so thi may dem dung hon nguoi, viec thi nguoc lai.
Ban giao truoc day chep tay ca hai nen so hay lech, con viec thi hay roi.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import nhip_song as NS

LAB = NS.LAB
GOC = NS.GOC
BAN = LAB / "TIEP_TUC_MAI.md"
NHAT_KY = LAB / "NHAT_KY.md"

TEN = {
    "file_test": "file test (lab)", "ham_test": "ham test (lab)",
    "test_ds": "file test (ds/)", "bang_gia": "bang gia .parquet",
    "fdr": "dong so FDR", "fdr_bac_bo": "  trong do bac bo",
    "ung_vien": "ung vien xep hang", "tai_lieu": "ban doc da thu",
    "co_che": "co che trong thu vien", "van_de_mo": "van de con mo",
    "van_de_nang": "  muc NANG", "viec_cho_tong": "viec dang CHO",
    "py_top": "file .py o goc lab",
}


def _muc(van: str, dau: str) -> str:
    """Cat mot muc `## ...` ra khoi ban giao cu, giu nguyen van."""
    m = re.search(rf"^##\s*{dau}.*?(?=^##\s|\Z)", van, re.S | re.M | re.I)
    return m.group(0).rstrip() if m else ""


def main(argv: list) -> int:
    khong_commit = "--khong-commit" in argv
    tom_tat = " ".join(a for a in argv if not a.startswith("--")).strip()
    ngay = time.strftime("%Y-%m-%d")
    gio = time.strftime("%H:%M")

    if not tom_tat:
        print('Thieu tom tat. Dung:  b ket "mot cau ta phien hom nay"')
        return 2

    # --- 1. cat ban cu ------------------------------------------------------
    cu_van = BAN.read_text(encoding="utf-8") if BAN.exists() else ""
    if cu_van:
        m = re.search(r"chot phien\s+([0-9/\-]+)", cu_van)
        nhan = (m.group(1).replace("/", "-") if m else "cu")
        kho = LAB / "nhat_ky"
        kho.mkdir(exist_ok=True)
        (kho / f"TIEP_TUC_{nhan}.md").write_text(cu_van, encoding="utf-8")

    # --- 2. so do duoc ------------------------------------------------------
    moi = NS.doc()
    cu = NS.anh_cu()
    d = NS.chenh(moi, cu)
    ngay_cu = cu.get("ngay", "chua co moc")

    hang = []
    for k, nhan_ in TEN.items():
        v = moi.get(k)
        if v is None:
            continue
        doi = d.get(k)
        hang.append(f"| {nhan_} | {v} | {f'{doi:+d}' if doi else ''} |")
    bang = "\n".join(hang)

    # --- 3. git: hom nay lam gi --------------------------------------------
    if NS.co_git():
        commit = NS.git(["log", "--oneline", f"--since={ngay} 00:00"]) or "(chua commit gi hom nay)"
        doi_file = NS.git(["status", "--short"])
        so_doi = len([l for l in doi_file.splitlines() if l.strip()])
        git_van = (f"- commit hom nay:\n```\n{commit}\n```\n"
                   f"- file dang doi luc chot: **{so_doi}**")
    else:
        git_van = "- **chua co git** — chay `git init` o thu muc goc de co duong lui."

    # --- 4. bung phan VIEC tu ban cu ---------------------------------------
    viec = _muc(cu_van, "Viec tiep theo") or (
        "## Viec tiep theo, theo thu tu\n\n1. (chua dien)")
    quen = _muc(cu_van, "Khong duoc quen")

    van = f"""# TIEP TUC NGAY MAI — chot phien {ngay} {gio}

{tom_tat}

## Trang thai do duoc luc chot
> May tu dien phan nay luc `b ket`. **Dung sua tay** — sua thi mai het so sanh
> duoc. Cot "doi" so voi moc {ngay_cu}.

| chi so | hom nay | doi |
|---|---:|---:|
{bang}

- co DUNG_LAI: **{'CO (he dang nam im)' if moi['dung_lai'] else 'KHONG (he dang chay)'}**
- viec CHO theo loai: {', '.join(f'{a}={b}' for a, b in moi['viec_cho'].items()) or 'khong con'}
{git_van}

## Mot doan doc la hieu ca phien

(dien tay: phien nay tim ra dieu gi, cai gi lat nguoc ket luan cu)

{viec}

{quen}
"""
    BAN.write_text(van, encoding="utf-8")
    NS.luu(moi, ngay)

    # --- 5. nhat ky mot dong ------------------------------------------------
    dong = f"- **{ngay} {gio}** — {tom_tat} (test {moi['ham_test']}, fdr {moi['fdr']}, viec cho {moi['viec_cho_tong']})\n"
    if not NHAT_KY.exists():
        NHAT_KY.write_text("# NHAT KY PHIEN — moi ngay mot dong\n\n", encoding="utf-8")
    with NHAT_KY.open("a", encoding="utf-8") as fh:
        fh.write(dong)

    # --- 6. commit ----------------------------------------------------------
    if NS.co_git() and not khong_commit:
        NS.git(["add", "-A"])
        r = NS.git(["commit", "-m", f"{ngay}: {tom_tat}"])
        print(r[:400] if r else "(khong co gi de commit)")

    print("\n" + "=" * 70)
    print(f"DA CHOT PHIEN {ngay} {gio}")
    print("=" * 70)
    print(f"  ban giao moi : {BAN}")
    print(f"  ban cu cat ve: lab/nhat_ky/")
    print(f"  nhat ky      : {NHAT_KY.name}")
    if d:
        print("  doi so voi moc truoc: " + ", ".join(f"{k} {v:+d}" for k, v in d.items()))
    print("\nCon phai lam tay 2 muc trong TIEP_TUC_MAI.md:")
    print("  - 'Mot doan doc la hieu ca phien'")
    print("  - cap nhat 'Viec tiep theo' (dang bung nguyen tu ban hom qua)")
    print("\nMai vao phien:  b vao")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
