# -*- coding: utf-8 -*-
"""_quay_quan_tri.py - LUAN PHIEN 50 CO CHE QUAN LI LENH VAO CUNG MOT HE NEN.

Chu du an 07/09: *"Da xay duoc cac co che quan li lenh va thu thay no luan phien
vao he thong de xem co che quan li lenh nao hop li nhat cho chien luoc chua."*

Chua - nen bai nay lam. 50 luat (gom MOC tat het quan tri o vi tri 0) x N he nen,
moi he nen mot lan boot.

## CONG RIENG CHO QUAN TRI - khac cong cua tin hieu vao

Quan tri **khong sinh tin hieu**, no bien doi phan phoi ket qua cua mot he da co.
Nen no phai qua bon dieu kien khac:

1. **Moc tat-het-quan-tri nam trong CUNG lan chay** (luat 0). So voi moc cua lan
   boot khac la so hai thu khac nhau.
2. **Cai thien >= 3 HE NEN khac nhau.** Mot luat chi thang tren mot he nen la
   hien tuong cua he do, khong phai mot co che quan tri.
3. **Train/holdout, tham so chon tren train.** Bai hoc 07/09: nhoi lenh dep
   trong mau (x1,89-2,93) nhung cau hinh cua TRAIN ap vao HOLDOUT thi **chay tai
   khoan** (-9.999,70 / DD 100%) [[quan-tri-chi-dat-hue-song-sot]].
4. **Kiem DA KICH HOAT chua** truoc khi ket luan: so lenh phai DOI so voi moc.
   Neu moi luat cho ket qua y het moc thi do la LOI, khong phai ket qua am
   [[ket-luan-am-phai-phan-biet-chua-do]].

## LOT 0,50 CHU KHONG PHAI 0,10

`PositionClosePartial` duoi `SYMBOL_VOLUME_MIN` **that bai im lang**: o lot 0,10
voi min 0,10 thi nua vi the = 0,05 -> moi luat co `tia` deu khong chay va bang so
doc y het "tia khong an thua". Lot 0,50 cho tia du cho.

Chay: python _quay_quan_tri.py [SYMBOL]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bo_ba as BB                       # noqa: E402
import _dem_ghep as DG                    # noqa: E402
import _ghep_he as GH                     # noqa: E402
import chay_tester_kho as C               # noqa: E402
from nhan import dich_mq5 as D            # noqa: E402
from nhan import dich_mq5_qtvt as Q       # noqa: E402
from nhan import quan_tri_dsl as QD       # noqa: E402

MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
DAU, CAT, CUOI = "2016.06.01", "2021.06.01", "2026.07.29"
TEN_EA = "QuayQuanTri"
#: ATR(14) D1 US100Cash ~ 440 diem. Dung de quy pip/diem cua tac gia EA ve ATR.
ATR_DIEM, GIA_DIEM = 440.0, 0.01
LOT = 0.50
#: He nen: chon chan GIU LENH LAU, vi quan tri can CHO de hoat dong
#: [[quan-tri-can-cho-de-hoat-dong]] - tren cap giu 1-3 nen thi moi lop phu deu
#: vo hieu va bang so se noi doi rang "quan tri khong an thua".
HE_NEN = ["vung_discount_rebound", "smc_sell_zone_reversal__dao",
          "fair_value_gap_bullish", "ichimoku_scalper_bullish"]


def sinh_ea(he: dict, luat_ma: str) -> str:
    """EA = mot he nen (tin hieu vao) + khoi quan tri gop, noi bang text.

    Noi bang text chu khong viet mau rieng: mau cua `dich_mq5` la duong da qua
    kiem cua du an, chen vao no thi phan tin hieu vao khong doi mot dong nao.
    """
    ma, _ = D.sinh_ea([he], TEN_EA, khung="D1", them_mua_giu=False)
    ma = ma.replace("CTrade   trade;",
                    "CTrade   trade;\nCTrade   qt_trade;\n" + luat_ma, 1)
    ma = ma.replace("   trade.SetExpertMagicNumber(InpMagic);",
                    "   trade.SetExpertMagicNumber(InpMagic);\n   QT_Khoi();", 1)
    ma = ma.replace("void OnTick()\n  {\n   KhopYDinh();",
                    "void OnTick()\n  {\n   QT_KhopYDinh();\n   KhopYDinh();", 1)
    ma = ma.replace("   int k = InpMaCoChe;",
                    "   QT_MoiNen();\n   int k = InpMaCoChe;", 1)
    return ma


def chay(nc: str, so_luat: int, tu: str, den: str) -> list[dict]:
    (C.XM_DATA / (nc + ".ini")).write_text("""[Tester]
Expert=%s.ex5
Symbol=%s
Period=H1
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
InpMaCoChe=0||0||0||0||N
InpLot=%.2f||%.2f||0||0||N
InpMagic=26091800||26091800||0||0||N
QT_MaLuat=0||0||1||%d||Y
QT_Magic=26091800||26091800||0||0||N
QT_LotGoc=%.2f||%.2f||0||0||N
""" % (TEN_EA, MA, tu, den, GH.VON, nc, LOT, LOT, so_luat - 1, LOT, LOT),
        encoding="utf-16")
    f = C.XM_DATA / (nc + ".xml")
    if f.exists():
        f.unlink()
    GH._chay_terminal(C.XM_DATA / (nc + ".ini"), tran=3600)
    if not f.exists():
        return []
    ra = []
    for d in C.doc_xml(f):
        k = int(C._so(d.get("QT_MaLuat", -1), -1))
        if k < 0:
            continue
        ra.append({"luat": k, "lenh": int(C._so(d.get("Trades"))),
                   "lai": C._so(d.get("Profit")),
                   "dd": C._so(d.get("Equity DD %")),
                   "sharpe": C._so(d.get("Sharpe Ratio"))})
    return ra


def main() -> int:
    kho = {c["ten"]: c for c in BB.lay_chan()}
    ds = [QD.sang_atr(x, ATR_DIEM, GIA_DIEM) for x in QD.doc_kho()]
    luat_ma, luat = Q.sinh_khoi_nhieu(ds, khung="D1", magic=26091800,
                                      lot_goc=LOT)
    print("%d luat quan tri (luat 0 = MOC tat het quan tri)" % len(luat),
          flush=True)

    gop = {}
    for ten in HE_NEN:
        he = kho.get(ten)
        if he is None:
            print("bo qua %s (khong co trong chan duong)" % ten, flush=True)
            continue
        src = C.XM_DATA / "MQL5" / "Experts" / (TEN_EA + ".mq5")
        src.write_text(sinh_ea(he, luat_ma), encoding="utf-8")
        loi = C.bien_dich(src)
        if loi:
            print("%s: bien dich LOI %s" % (ten, loi), flush=True)
            continue
        tr = chay("qq_tr_%s" % MA, len(luat), DAU, CAT)
        ho = chay("qq_ho_%s" % MA, len(luat), CAT, CUOI)
        if not tr or not ho:
            print("%s: khong ra bang" % ten, flush=True)
            continue
        a = {x["luat"]: x for x in tr}
        b = {x["luat"]: x for x in ho}
        moc_tr, moc_ho = a.get(0), b.get(0)
        if not moc_tr or not moc_ho:
            continue
        # Kiem DA KICH HOAT: so lenh phai DOI so voi moc o it nhat vai luat.
        doi = sum(1 for k in a if k and a[k]["lenh"] != moc_tr["lenh"])
        print("\n=== %s\n    moc: %d lenh | lai %.2f | DD %.2f%% | %d/%d luat "
              "lam DOI so lenh" % (ten[:44], moc_tr["lenh"], moc_tr["lai"],
                                   moc_tr["dd"], doi, len(a) - 1), flush=True)
        if doi == 0:
            print("    !! KHONG luat nao kich hoat -> LOI, khong phai ket qua am",
                  flush=True)
            continue

        def diem(x):
            return x["lai"] / x["dd"] if x["dd"] > 0 else 0.0

        m_tr, m_ho = diem(moc_tr), diem(moc_ho)
        hang = []
        for k in sorted(a):
            if k == 0 or k not in b:
                continue
            hang.append({"luat": k, "ten": str(luat[k].get("ten", "?")),
                         "tr": round(diem(a[k]), 1), "ho": round(diem(b[k]), 1),
                         "lenh_tr": a[k]["lenh"]})
        hang.sort(key=lambda x: -x["tr"])
        print("    moc  train %.1f | holdout %.1f" % (m_tr, m_ho), flush=True)
        print("    %-36s %8s %8s %7s" % ("luat (xep theo TRAIN)", "train",
                                         "holdout", "lenh"))
        for x in hang[:6]:
            print("    %-36s %8.1f %8.1f %7d"
                  % (x["ten"][:36], x["tr"], x["ho"], x["lenh_tr"]), flush=True)
        gop[ten] = {"moc_train": round(m_tr, 1), "moc_holdout": round(m_ho, 1),
                    "so_luat_kich_hoat": doi, "hang": hang}
        DG.ghi("QUAY_QUAN_TRI_%s.json" % MA, gop)

    # Cong: luat nao cai thien HOLDOUT tren nhieu he nen
    if len(gop) >= 2:
        dem = {}
        for g in gop.values():
            for x in g["hang"]:
                if x["ho"] > g["moc_holdout"]:
                    dem[x["ten"]] = dem.get(x["ten"], 0) + 1
        print("\n=== LUAT CAI THIEN HOLDOUT tren nhieu he nen (tren %d he) ==="
              % len(gop))
        if not dem:
            print("   khong luat nao cai thien holdout tren he nen nao")
        for t, n in sorted(dem.items(), key=lambda x: -x[1])[:10]:
            print("   %-46s %d/%d he nen" % (t[:46], n, len(gop)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
