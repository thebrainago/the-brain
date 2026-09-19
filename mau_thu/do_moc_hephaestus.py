# -*- coding: utf-8 -*-
"""DO MOC: he DE ra duoc bao nhieu, va no dung duoc bao nhieu phan von tu.

Chay duoc TREN CLOUD: khong `nao.db`, khong MT5, khong du lieu gia that.

    python mau_thu/do_moc_hephaestus.py

## CAU HOI BAI NAY DO

Chu du an 19/09/2026: *"He dang kha thu dong trong viec tu duy va tim kiem ra
edge vi no dang chi may mo nhung thu san co"*, va *"neu co he thong ra tien thi
cha ai up len"*.

Dich cua hai cau do la mot phep do: **he dang may mo trong bao nhieu phan cua
cai no co the noi, va no co de ra duoc thu chua ai co khong?**

## MOC 19/09/2026

    kho co che              4.049 co che, dung 34/45 toan hang
    con bo trong han        15 toan hang (ichimoku · vwap · fibo · bollinger ·
                            moc_ky · wma · smma · obv · gann_sq9 · goc ·
                            duong_xu_huong · dem_lien_tiep · trang_thai_lat ·
                            tuong_quan · phuong_sai)

    duc()        de 573 co che - **573 cai kho CHUA CO** (0 trung)
    bien_the()   tu 400 co che kho -> 1.069 ban, 1.038 cai kho chua co

Con so "kho rong 8 chi bao" trong so do la cua 13/09 va da cu; bai nay do lai
moi lan chay nen no khong the cu theo cach do.

Nhung con so tren KHONG phai "da tim ra edge". Chung la **do rong cua khong
gian gia thuyet** - thu duy nhat module nay chiu trach nhiem. Tra loi "cai nao
ra tien" la viec cua QUANTLAB va no can MT5 tester, khong chay o day.

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
    # Doc kho THAT khi doc duoc. Do voi kho rong thi con so "de ra" trong dep
    # hon that, vi khong ai tru di phan da co.
    kho = NP.doc_kho(cho_rong_khi_hong=True)
    r = do(kho=kho)
    print("  kho hien co         : %d co che, dung %d toan hang"
          % (len(kho), r["phu"]["so_dang_dung"]))
    ds, lo = r["ds"], r["lo"]

    print("  %-20s %d" % ("khuon", len(HP.KHUON)))
    for k, v in Counter(s["khuon"] for s in ds).most_common():
        print("    %-20s %4d co che" % (k, v))

    print("\n  ngu phap NOI DUOC   : %d toan hang" % r["phu"]["so_noi_duoc"])
    print("  hephaestus DUNG TOI : %d" % len(r["chi_bao"]))
    print("  de ra               : %d co che (KHO CHUA CO - da tru phan trung)"
          % len(ds))
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
