# -*- coding: utf-8 -*-
"""DO MOC: boc duoc bao nhieu NUT QUAN TRI LENH tu bo mau .mq5.

Bai chi em cua `do_moc.py`, nhung do HO CO CHE THU HAI. Chay duoc TREN CLOUD:
khong dung `nao.db`, khong dung MT5, khong dung du lieu gia.

    python mau_thu/do_moc_quan_tri.py

## VI SAO CAN BAI DO RIENG CHO HO NAY

Do cua chinh du an, ghi trong `nhan/quan_tri.py`: thu vien co **262 co che,
tat ca deu la tin hieu VAO**. Va do ngay 18/09 tren AUDCAD: cung mot bo tham
so luoi, chi bat/tat `tia_lenh` thi holdout di tu **+0,66%/nam len
+13,26%/nam**, sut giam tu **-15,6% xuong -3,5%**.

Tuc ho co che dang TRONG lai chinh la ho ra tien nhat da do duoc. Khong co bai
do rieng thi khong biet no dang day len hay dung im.

## HAI BO BOC, DO CANH NHAU

  `quan_tri.boc_mot`      doc TEN INPUT cua tac gia
  `quan_tri_than.boc_than` doc THAN HAM - ma that su chay

Moc 19/09/2026 tren 10 file mau:

    theo ten input : 5 file ra nut ·  5 nut · **0** file >= 2 nut
    theo than ham  : 8 file ra nut · 26 nut · **5** file >= 2 nut

Con so dang de y la cot cuoi. `quan_tri.loc` gat moi co che duoi 2 nut chay
duoc, nen truoc bai nay ca bo mau ra **khong co che quan tri nao dung duoc** -
du ba file trong do co han mot bo chot lenh hoan chinh viet thang trong ma.
"""
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from nhan import quan_tri as QT                                  # noqa: E402
from nhan import quan_tri_than as QTT                            # noqa: E402

MAU = LAB / "mau_thu"


def do() -> dict:
    dong, thieu = [], {}
    for p in sorted(MAU.glob("*.mq5")):
        src = p.read_text(encoding="utf-8", errors="ignore")
        s = QT.boc_mot(src, ten=p.name)
        cu = sorted((s or {}).get("nut_van", {}).keys())
        r = QTT.boc_than(src)
        moi = r["nut_van"]
        for x in r["thieu"]:
            thieu[x] = thieu.get(x, 0) + 1
        dong.append((p.name, cu, moi))
    return {"dong": dong, "thieu": thieu}


def _dem(ds, chi_chay_duoc=False):
    """(so file ra nut, so nut, so file ra >= 2 nut)."""
    if chi_chay_duoc:
        ds = [[k for k in x if not k.startswith("_")] for x in ds]
    return (sum(1 for x in ds if x), sum(len(x) for x in ds),
            sum(1 for x in ds if len(x) >= 2))


def main() -> int:
    r = do()
    print("  %-40s %-14s %s" % ("file", "ten input", "than ham"))
    for ten, cu, moi in r["dong"]:
        print("  %-40s %-14s %s" % (
            ten[:40], ",".join(cu) or "-",
            ", ".join("%s=%g" % (k, v) for k, v in sorted(moi.items())) or "-"))

    cu_ds = [x[1] for x in r["dong"]]
    moi_ds = [list(x[2]) for x in r["dong"]]
    print("\n  file mau : %d" % len(r["dong"]))
    for nhan, ds in (("theo TEN INPUT", cu_ds), ("theo THAN HAM ", moi_ds)):
        f, n, hai = _dem(ds)
        fc, nc, haic = _dem(ds, chi_chay_duoc=True)
        print("  %s : %d file ra nut · %d nut · %d file >= 2 nut"
              % (nhan, f, n, hai))
        print("  %s   trong do `mo_phong_v2` chay duoc: %d nut · %d file >= 2 nut"
              % (" " * len(nhan), nc, haic))
    if r["thieu"]:
        print("\n  DOC DUOC CO CHE nhung KHONG doc duoc so (khong phai 'khong co'):")
        for k, n in sorted(r["thieu"].items(), key=lambda x: -x[1])[:6]:
            print("   %2dx  %s" % (n, k))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
