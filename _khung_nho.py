# -*- coding: utf-8 -*-
"""_khung_nho.py - CHON CHAN TRUC TIEP TREN TUNG KHUNG (khong bung tu D1).

Chu du an 07/09/2026: *"Uh phai thay so chu, thu ca cac khung Minute di, ta phai
thu vai chien luoc de xem sau cung co nen bo khung nho khong."*

`_da_khung.py` bung 36 chan da chon tren D1 sang khung khac va quy doi tham so
chu ky. Ket qua doc duoc mot nua: W1 AM (-1.471, 12/36 chan song), H4 duong
nhung it chan hon D1. **Nhung 36 chan do duoc CHON vi duong tren D1**, nen D1
thang la dieu hien nhien - do la thien lech chon mau, khong phai bang chung.

Bai nay lam dung: chay lai **ca chang A + B** (mo kho 530 co che, roi dao chieu
chan am) **TRUC TIEP tren tung khung**, moi khung mot cua so du lieu THAT cua no.

## HAI CON SO DA DO, QUYET DINH KHUNG NAO DANG QUET

**1. Do sau du lieu THAT (dem bar moi nam, US100Cash):**

    D1   2011 tro di       15 nam
    H4   2016 tro di       10 nam   <- 2011-2015 la bar NGAY deo nhan H4
    H1   2016 tro di       10 nam   <- y het
    M30  2018-04 tro di     8,4 nam
    M15  2022-06 tro di     4,2 nam  <- tron ven trong MOT che do thi truong
    M5   2025-04 tro di     1,4 nam  <- KHONG ket luan duoc gi

Bay da sap: 2012-2015 H4 va D1 co **so bar y het nhau** (312/309/306) - MT5 don
bar NGAY vao yeu cau khung nho khi khong co du lieu, va **khong bao loi gi**.

**2. Chi phi so voi bien do nen (US100Cash, spread do duoc 0,98 bps):**

    khung   bien do nen   |doi| close   spread an mat
    M5          8,2 bps       3,6 bps      12,0%
    M15        13,2 bps       5,5 bps       7,4%
    M30        17,2 bps       7,1 bps       5,7%
    H1         22,4 bps       9,1 bps       4,4%
    H4         51,4 bps      21,2 bps       1,9%
    D1        137,7 bps      57,8 bps       0,7%

Ve nguoc lai phai noi cho cong bang: **phi qua dem con dat hon spread**. Swap
mua -4,61/lot/dem tren hop dong 29.627 USD = **1,56 bps/dem**, gap 1,6 lan
spread. Khung lon tra it spread nhung tra phi von moi dem; khung nho nguoc lai.
Va chan BAN o khung lon **duoc nhan** +0,52/lot/dem = +0,18 bps/dem.

=> Quet **H4 · H1 · M30**. Bo M5 vi DU LIEU (1,4 nam), khong phai vi co che -
hai ly do khac han va phai ghi dung [[ket-luan-am-phai-phan-biet-chua-do]].

## EA CHAY TREN KHUNG NAO

`chay_tester_kho.KHUNG_CHAY` co dinh "H1" vi nen D1 mo luc 00:00 nam NGOAI phien
CFD. Voi khung tin hieu <= H1 thi nen dong TRONG phien, nen chay EA ngay tren
chinh khung do.

Chay: python _khung_nho.py [SYMBOL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _dem_ghep as DG                 # noqa: E402
import _ghep_he as GH                  # noqa: E402
import chay_tester_kho as C            # noqa: E402
from nhan import dich_mq5 as D         # noqa: E402
from nhan import ngu_phap as NP        # noqa: E402

LAB = Path(__file__).resolve().parent
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"

#: (khung tin hieu, khung chay EA, dau cua so, moc cat train/holdout, cuoi).
#: Cua so lay theo DU LIEU THAT cua tung khung, khong lay chung mot cua so -
#: chung cua so thi M30 mat 2,4 nam dau ma khong duoc gi.
KHUNG = [
    ("H4",  "H1",  "2016.06.01", "2021.06.01", "2026.07.29"),
    ("H1",  "H1",  "2016.06.01", "2021.06.01", "2026.07.29"),
    ("M30", "M30", "2018.06.01", "2022.06.01", "2026.07.29"),
]
#: `python _khung_nho.py US100Cash H4` -> chi chay khung do.
if len(sys.argv) > 2:
    KHUNG = [k for k in KHUNG if k[0] == sys.argv[2]]


def kho_mo() -> list[dict]:
    ra = []
    for c in NP.doc_kho():
        if NP.kiem_khai_bao(c):
            c2 = dict(c, co_che="MIEN CONG DE DO - chua co ly do kinh te.")
            if NP.kiem_khai_bao(c2):
                continue
            c = c2
        ra.append(c)
    return ra


def chay_kho(spec: list[dict], khung: str, khung_chay: str, tu: str, den: str,
             nhan: str) -> list[dict]:
    ma, dat = D.sinh_ea(spec, C.TEN_EA, khung=khung)
    src = C.XM_DATA / "MQL5" / "Experts" / (C.TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        print("  bien dich LOI: %s" % loi, flush=True)
        return []
    ten = "%s_%s_%s" % (nhan, khung, MA)
    p = C.XM_DATA / (ten + ".ini")
    p.write_text("""[Tester]
Expert=%s.ex5
Symbol=%s
Period=%s
Model=2
ExecutionMode=0
Optimization=1
OptimizationCriterion=0
FromDate=%s
ToDate=%s
ForwardMode=0
Deposit=%d
Currency=USD
Leverage=1:500
ProfitInPips=0
Report=%s
ReplaceReport=1
ShutdownTerminal=1

[TesterInputs]
InpMaCoChe=0||0||1||%d||Y
InpLot=0.10||0.10||0||0||N
InpMagic=26091500||26091500||0||0||N
""" % (C.TEN_EA, MA, khung_chay, tu, den, GH.VON, ten, len(dat) - 1),
        encoding="utf-16")
    for h in (".xml", ".htm"):
        f = C.XM_DATA / (ten + h)
        if f.exists():
            f.unlink()
    giay = GH._chay_terminal(p, tran=7200)
    hong = C.kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        print("  %s" % hong, flush=True)
        return []
    f = C.XM_DATA / (ten + ".xml")
    if not f.exists():
        print("  khong thay bang ket qua (%ss)" % giay, flush=True)
        return []
    ket = []
    for d in C.doc_xml(f):
        i = int(C._so(d.get("InpMaCoChe", -1), -1))
        if not (0 <= i < len(dat)):
            continue
        ket.append({"ten": dat[i]["ten"], "lenh": int(C._so(d.get("Trades"))),
                    "lai": C._so(d.get("Profit")),
                    "sharpe": C._so(d.get("Sharpe Ratio")),
                    "dd": C._so(d.get("Equity DD %"))})
    print("  %d pass, %ss" % (len(ket), giay), flush=True)
    return ket


def main() -> int:
    kho = kho_mo()
    print("kho mo: %d co che" % len(kho), flush=True)
    gop = {}
    for khung, khung_chay, tu, cat, den in KHUNG:
        print("\n########## KHUNG %s (EA chay tren %s) %s -> %s"
              % (khung, khung_chay, tu, den), flush=True)
        tr = chay_kho(kho, khung, khung_chay, tu, cat, "kn_train")
        ho = chay_kho(kho, khung, khung_chay, cat, den, "kn_hold")
        if not tr or not ho:
            continue
        a = {r["ten"]: r for r in tr if r["lenh"] >= 25}
        b = {r["ten"]: r for r in ho if r["lenh"] >= 25}
        chung = set(a) & set(b)
        duong = [t for t in chung if a[t]["lai"] > 0 and b[t]["lai"] > 0]
        am = [t for t in chung if a[t]["lai"] < 0 and b[t]["lai"] < 0]
        print("  co >=25 lenh ca hai doan: %d | duong ca hai: %d | am ca hai: %d"
              % (len(chung), len(duong), len(am)), flush=True)

        # Dao chieu chan am, do lai tren CHINH khung nay.
        theo = {c["ten"]: c for c in kho}
        dao = []
        for t in am:
            c = theo.get(t)
            if c is None:
                continue
            dao.append(dict(c, ten=t + "__dao",
                            chieu=-int(c.get("chieu", 1) or 1),
                            co_che="BAN DAO CHIEU cua %s." % t))
        dd = []
        if dao:
            tr2 = chay_kho(dao, khung, khung_chay, tu, cat, "kn_dtrain")
            ho2 = chay_kho(dao, khung, khung_chay, cat, den, "kn_dhold")
            a2 = {r["ten"]: r for r in tr2 if r["lenh"] >= 25}
            b2 = {r["ten"]: r for r in ho2 if r["lenh"] >= 25}
            dd = [t for t in set(a2) & set(b2)
                  if a2[t]["lai"] > 0 and b2[t]["lai"] > 0]
        print("  dao chieu: %d -> duong ca hai doan: %d" % (len(dao), len(dd)),
              flush=True)

        # Xep hang theo lai/sut giam TREN HOLDOUT - con so trong mau khong dung
        # de xep hang duoc [[hinh-dang-phai-hieu-chuan-bang-null]].
        xh = sorted(duong,
                    key=lambda t: -(b[t]["lai"] / b[t]["dd"] if b[t]["dd"] > 0
                                    else 0))
        # Luu DU TEN chu khong chi dem: buoc ghep sau nay can danh sach, va
        # chay lai ca chang A+B chi de lay ten la phi mot lan boot.
        gop[khung] = {"cua_so": [tu, cat, den], "co_ca_hai_doan": len(chung),
                      "duong": len(duong), "am": len(am), "dao_duong": len(dd),
                      "tong_chan_duong": len(duong) + len(dd),
                      "ten_duong": sorted(duong), "ten_dao_duong": sorted(dd),
                      "top": [{"ten": t, "lai_ho": round(b[t]["lai"], 2),
                               "dd_ho": round(b[t]["dd"], 3),
                               "lenh_ho": b[t]["lenh"],
                               "loi_tren_dd": round(b[t]["lai"] / b[t]["dd"], 1)
                               if b[t]["dd"] > 0 else 0} for t in xh[:10]]}
        for x in gop[khung]["top"][:6]:
            print("   %-44s ho %9.2f %6.2f%% %8.1f"
                  % (x["ten"][:44], x["lai_ho"], x["dd_ho"], x["loi_tren_dd"]),
                  flush=True)
        DG.ghi("KHUNG_NHO_%s.json" % MA, gop)

    print("\n%-5s %10s %8s %8s %10s %14s"
          % ("khung", "ca hai doan", "duong", "am", "dao duong", "chan duong"))
    for k, v in gop.items():
        print("%-5s %10d %8d %8d %10d %14d"
              % (k, v["co_ca_hai_doan"], v["duong"], v["am"], v["dao_duong"],
                 v["tong_chan_duong"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
