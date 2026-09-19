# -*- coding: utf-8 -*-
"""DO MOC: he DE ra duoc bao nhieu, va no dung duoc bao nhieu phan von tu.

Chay duoc TREN CLOUD: khong `nao.db`, khong MT5, khong du lieu gia that.

    python mau_thu/do_moc_hephaestus.py

## CAU HOI BAI NAY DO

Chu du an 19/09/2026: *"He dang kha thu dong trong viec tu duy va tim kiem ra
edge vi no dang chi may mo nhung thu san co"*, va *"neu co he thong ra tien thi
cha ai up len"*.

Dich cua hai cau do la mot phep do: **he dang may mo trong bao nhieu phan cua
cai no co the noi?** Ngu phap tinh duoc 54 toan hang. Kho co che - thu sinh ra
tu viec boc tai lieu - rong dung 8 chi bao, vi do rong cua no phu thuoc vao
"co ai viet bai ve no khong".

## MOC 19/09/2026

    ngu phap NOI DUOC          54 toan hang
    kho (boc tu tai lieu)       8 chi bao        <- truoc
    hephaestus DE RA           29 chi bao        <- sau

Con so thu ba khong phai "da tim ra edge". No la **do rong cua khong gian gia
thuyet** - va do moi la thu module nay chiu trach nhiem. Viec tra loi "cai nao
ra tien" thuoc QUANTLAB, va no can MT5 tester chu khong chay o day.

## DOC CON SO NAY CHO DUNG

De nhieu **khong** tu no la tot. Moi co che de ra an mot suat FDR, nen bai do
in ca `plan_hash` va so phep thu: de 10.000 roi test la luong thien neu tra du
gia; de 10.000 roi chi khai vai cai dep la gian lan.
"""
import sys
from collections import Counter
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from nhan import hephaestus as HP                                # noqa: E402
from nhan import ngu_phap as NP                                  # noqa: E402


def _chi_bao_cua(ds: list) -> Counter:
    dem: Counter = Counter()
    for s in ds:
        t: set = set()
        HP._chi_bao_trong(s.get("vao") or [], t)
        dem.update(t - HP._KHONG_TINH)
    return dem


def do(kho: list | None = None) -> dict:
    ds = HP.duc(han_ngach=100000, kho=kho)
    return {"ds": ds, "lo": HP.dang_ky_lo(ds), "chi_bao": _chi_bao_cua(ds),
            "phu": HP.do_phu(kho if kho is not None else [])}


def main() -> int:
    # Kho rong: tren cloud khong co `nao.db`. Tren may chu du an, bo `kho=None`
    # de doc kho that - luc do con so "da co" moi dung.
    r = do(kho=[])
    ds, lo = r["ds"], r["lo"]

    print("  %-20s %d" % ("khuon", len(HP.KHUON)))
    for k, v in Counter(s["khuon"] for s in ds).most_common():
        print("    %-20s %4d co che" % (k, v))

    print("\n  ngu phap NOI DUOC   : %d toan hang" % r["phu"]["so_noi_duoc"])
    print("  hephaestus DUNG TOI : %d" % len(r["chi_bao"]))
    print("  de ra               : %d co che" % len(ds))
    print("  plan_hash           : %s" % lo["plan_hash"])
    print("  so suat FDR lo nay dat: %d" % lo["so_phep_thu"])

    con = sorted(set(r["phu"]["noi_duoc"]) - set(r["chi_bao"]))
    print("\n  con CHUA de bao gio (%d): %s" % (len(con), ", ".join(con)))

    # Moi co che deu phai qua duoc cong cu phap - neu khong thi con so tren la
    # so rac, khong phai so gia thuyet.
    hong = [s["ten"] for s in ds if NP.kiem_khai_bao(s)]
    print("\n  qua cong cu phap    : %d/%d" % (len(ds) - len(hong), len(ds)))
    if hong:
        print("  HONG: %s" % ", ".join(hong[:5]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
