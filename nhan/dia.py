# -*- coding: utf-8 -*-
"""dia.py - CONG DIA DAY. Khong phai mot bao cao, mot CONG.

## VI SAO CAN THEM CAI NAY KHI EVO DA DO DIA

`evo.py` da do `dia.con_trong` va bao XAU khi duoi 5 GB tu truoc. No van khong
cuu duoc gi ngay 13/09/2026, vi do la mot BAO CAO ma nguoi phai doc:

    09:45  `b vao` -> EVO: TOT 22 · XAU 0 · dia 8,6 GB      (that, luc do)
    10:2x  dia tut ve 233 MB
           pytest 6 nhan chet voi `paging file too small`
           kho co che bi ghi de 2.975 -> 21, HAI LAN
           khong mot dong log nao noi "het dia"

Ban giao hom truoc da ghi dung cai bay nay bang chu: *"Dia day khong hien ra
nhu loi dia. No hien ra nhu 'boc 684 file -> 0 co che' va 'viec XONG rc=0 ma
kho khong doi'. Kiem `b don-dia` + `b evo` TRUOC khi tin bat ky ket qua rong
nao."* Mot canh bao duoc viet ra, doc ky, va van sap lai - do la dau hieu no
phai thanh mot CONG chu khong phai mot dong chu.

## CONG NAY DAT O DAU

Truoc moi thao tac GHI LON hoac TON DIA:
    `ngu_phap.luu_kho`   ghi kho co che (chinh cho da mat du lieu)
    `boc_llm.boc`        moi me boc ghi hang tram dong vao nao.db
    `go_html.go_kho`     ghi de hang nghin ban doc

KHONG dat o duong DOC. Het dia thi doc van dung; chan doc chi lam he chet som
hon ma khong cuu duoc gi.
"""
from __future__ import annotations

import shutil
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent

#: Duoi muc nay thi TU CHOI ghi. 2 GB khong phai con so tron chon bua: mot
#: luot `to_hop` voi pool 10 tien trinh an vai GB file tam (do 12/09: dia tut
#: ve 177 MB roi nhay lai 6,4 GB khi dung tien trinh), va `nao.db` mot minh da
#: 1,5 GB nen mot lan VACUUM can dung tung do cho nua.
NGUONG_GB = 2.0

#: Rieng ghi kho co che thi de nguong thap hon - file chi 2,4 MB, va TU CHOI
#: ghi kho co the lam mat cong mot me boc. Nhung 0,3 GB thi van phai chan, vi
#: duoi muc do `tam.replace()` co the that bai giua chung.
NGUONG_KHO_GB = 0.3


class DiaDay(RuntimeError):
    """Het cho ghi. Day la `CHUA_DO_DUOC`, khong bao gio la `AM`."""


def con_gb(duong: Path | str = LAB) -> float:
    try:
        return shutil.disk_usage(str(duong)).free / (1024 ** 3)
    except Exception:
        return float("inf")      # khong do duoc thi dung chan mu


def du_cho(can_gb: float = NGUONG_GB, viec: str = "",
           duong: Path | str = LAB) -> float:
    """Tra so GB con trong, NEM `DiaDay` neu duoi nguong."""
    gb = con_gb(duong)
    if gb < can_gb:
        raise DiaDay(
            "con %.2f GB trong (can >= %.1f GB)%s. Dung ghi - het dia KHONG "
            "hien ra nhu loi dia, no hien ra nhu 'ket qua rong' va 'kho bi xoa'. "
            "Don: `b don-dia`, xoa `Tester/logs` + `Tester/cache` cua MT5, "
            "cache trinh duyet, `npm-cache`, `pip/cache`."
            % (gb, can_gb, (" truoc khi " + viec) if viec else ""))
    return gb


if __name__ == "__main__":
    print("con trong: %.2f GB  (nguong ghi %.1f GB)" % (con_gb(), NGUONG_GB))
