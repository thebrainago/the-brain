# -*- coding: utf-8 -*-
"""_quan_tri_ghep.py - QUAN TRI VI THE DANG BAO NHIEU? Do o TICK, khong o nen.

Chu du an 07/09: *"Trailing luon la cach tot nhat de tang hieu qua cua moi chien
luoc, nhung cac khoang trailing khac nhau la cai can thu. Toi uu tien dua SL ve
entry de bao toan, nhung cai nay co rui ro mat lenh thi ta nen tinh ca viec re
entry hoac nhoi lenh am duong."*

## LOI PHAI SUA TRUOC KHI DO: `Model=2` KHONG DO DUOC QUAN TRI

Ca day chuyen ghep hom nay chay `Model=2` = **"Open prices only"**. Voi logic
vao/ra theo nen dong thi do la lua chon dung va nhanh. Nhung **trailing, dat hue,
tia lenh va lenh stop hai dau song hoan toan o duong di TRONG nen** - Model=2
khong co duong di do, no chi co gia mo. Do quan tri bang Model=2 la do mot thu
khong ton tai.

Du an da sap dung bay ho hang nay mot lan: `Model=1` che ra lai gia **12 lan**
khi TP nho hon 2x bien do nen M1 [[model1-che-ra-lai-gia]]. Nen o day
**`Model=0` (every tick)**, va chap nhan cham hon.

## NAM CAU HOI TACH BACH, MOI CAU MOT LUOT BOOT

Khong quet tich Descartes cua tat ca tham so: tich do la hang trieu pass va
**khong doc duoc** - mot cau hinh may man cua nhanh nay se che mat ket luan cua
nhanh kia. Moi luot deu co dong `moc` (tat het quan tri) lay tu **chinh luot
do** de doi chieu.

    trailing            khoang trailing x nguong bat dau trailing
    dat_hue_va_vao_lai  dua SL ve entry sau k x ATR, x co/khong cho tin hieu tat
    tia_lenh            tia mot nua vi the o k x ATR loi
    nhoi_am_duong       nhoi khi AM (DCA) hay khi DUONG (kim tu thap)
    kieu_ra             0 nhu cu · 1 giu den khi chan kia vao · 2 trailing · 3 ca hai

**Canh bao tu chinh du an ve nhoi lenh:** "nhoi lenh theo chieu + chot khi tong
lai" da do **18/18 cau hinh AM** [[khung-ngan-va-orderflow]]. O day nhoi la mot
tham so de do lai tren nen ghep, khong phai mot gia dinh.

## MOC PHAI GIU NGUYEN NGHIA

Slot 0 (`__mua_giu__`) **khong chiu quan tri** du `InpKieuRa` bang may - mot moc
mua-giu co trailing khong con la mua-giu nua, va moi so sanh se lech theo huong
co loi cho ta.

Chay: python _quan_tri_ghep.py [SYMBOL] [chan_A] [chan_B]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bo_ba as BB                       # noqa: E402
import _dem_ghep as DG                    # noqa: E402
import _ghep_he as GH                     # noqa: E402
import chay_tester_kho as C               # noqa: E402
from nhan import dich_mq5_quan_tri as QT   # noqa: E402

LAB = Path(__file__).resolve().parent
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
A = sys.argv[2] if len(sys.argv) > 2 else "mean_reversion_z5"
B = sys.argv[3] if len(sys.argv) > 3 else "quantora_ma_dashboard_sell"
VON = GH.VON
NAM = DG.NAM
TEN_EA = "GhepQuanTri"
#: SUA 07/09 sau khi DO: quan tri viet o day la quan tri **theo NEN DONG** -
#: `TrailingCham`, `DatHueCham`, `Tia` chi duoc goi khi co nen KHUNG moi. Nen
#: `Model=2` (open prices only) do DUNG no. Canh bao "Model=2 khong do duoc quan
#: tri" chi dung cho quan tri TRONG NEN: SL/TP dat o san, lenh stop hai dau.
#:
#: Va Model=0 khong chay duoc o day vi ly do du lieu chu khong phai nguyen tac:
#: M1 trong may chi co tu 2026-05-28, nen every-tick phai TAI VE nhieu nam M1
#: truoc khi chay - mot luot 10 nam ton 19,5 phut roi tra bang RONG.
#: Muon do trailing TRONG NEN thi phai tai M1 truoc, va do la mot viec rieng.
MODEL = 2
#: CUA SO NGAN HON CUA SO CHUNG - co chu dich. Model=0 phai dung tick tu bar M1
#: nen mot luot 10 nam ton hang chuc phut; ma cau hoi o day la **so sanh trong
#: CUNG mot luot** (moi luot deu co dong `moc` tat het quan tri), khong phai do
#: %/nam dai han. 5 nam du de phan xu, va no giu duoc phan holdout 2021-2026.
DAU, CUOI = "2021.06.01", "2026.07.29"
NAM_QT = (2026 + 7 / 12) - (2021 + 6 / 12)

NL = "\n"
LOT_CO_DINH = ("InpLot0=0||0||0||0||N" + NL + "InpLot1=0.1||0.1||0||0||N" + NL
               + "InpLot2=0.1||0.1||0||0||N" + NL)

SWEEP = [
    ("trailing",
     "InpKieuRa=2||2||0||0||N" + NL
     + "InpTrailATR=0.5||0.5||0.5||4.0||Y" + NL
     + "InpTrailTu=0||0||1.0||2.0||Y" + NL),
    ("dat_hue_va_vao_lai",
     "InpKieuRa=0||0||0||0||N" + NL
     + "InpBE=0||0||0.5||3.0||Y" + NL
     + "InpVaoLai=0||0||1||1||Y" + NL),
    ("tia_lenh",
     "InpKieuRa=0||0||0||0||N" + NL
     + "InpTiaATR=0||0||0.5||3.0||Y" + NL),
    ("nhoi_am_duong",
     "InpKieuRa=0||0||0||0||N" + NL
     + "InpNhoi=0||0||1||2||Y" + NL
     + "InpNhoiATR=1.0||1.0||1.0||3.0||Y" + NL
     + "InpNhoiHeSo=1.0||1.0||0.5||2.0||Y" + NL
     + "InpNhoiMax=2||2||0||0||N" + NL),
    ("kieu_ra",
     "InpKieuRa=0||0||1||3||Y" + NL
     + "InpTrailATR=2.0||2.0||0||0||N" + NL),
]


def sinh(a: dict, b: dict) -> list[dict]:
    ma, dat = QT.sinh_ea_quan_tri([dict(QT.SPEC_MUA_GIU), a, b], TEN_EA,
                                  khung="D1")
    src = C.XM_DATA / "MQL5" / "Experts" / (TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        raise SystemExit("bien dich: " + loi)
    print("EA quan tri: %s" % " | ".join(c["ten"][:30] for c in dat), flush=True)
    return dat


def chay(nc: str, dong_lot: str, dong_qt: str) -> list[dict]:
    (C.XM_DATA / (nc + ".ini")).write_text("""[Tester]
Expert=%s.ex5
Symbol=%s
Period=%s
Model=%d
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
%s%sInpMagic=26091300||26091300||0||0||N
InpGhi=0||0||0||0||N
""" % (TEN_EA, MA, C.KHUNG_CHAY, MODEL, DAU, CUOI, VON, nc, dong_lot,
       dong_qt), encoding="utf-16")
    for h in (".xml", ".htm"):
        f = C.XM_DATA / (nc + h)
        if f.exists():
            f.unlink()
    giay = GH._chay_terminal(C.XM_DATA / (nc + ".ini"), tran=7200)
    f = C.XM_DATA / (nc + ".xml")
    if not f.exists():
        print("  khong ra bang (%ss)" % giay, flush=True)
        return []
    ra = []
    for d in C.doc_xml(f):
        lai = C._so(d.get("Profit"))
        if VON + lai <= 0:
            continue
        ra.append({
            "lot": [round(C._so(d.get("InpLot%d" % i, 0)), 2) for i in range(3)],
            "kieu": int(C._so(d.get("InpKieuRa", 0))),
            "trail": round(C._so(d.get("InpTrailATR", 0)), 2),
            "trail_tu": round(C._so(d.get("InpTrailTu", 0)), 2),
            "be": round(C._so(d.get("InpBE", 0)), 2),
            "tia": round(C._so(d.get("InpTiaATR", 0)), 2),
            "vao_lai": int(C._so(d.get("InpVaoLai", 1))),
            "nhoi": int(C._so(d.get("InpNhoi", 0))),
            "nhoi_atr": round(C._so(d.get("InpNhoiATR", 0)), 2),
            "nhoi_he_so": round(C._so(d.get("InpNhoiHeSo", 1)), 2),
            "nhoi_max": int(C._so(d.get("InpNhoiMax", 0))),
            "lenh": int(C._so(d.get("Trades"))), "lai": lai,
            "dd": C._so(d.get("Equity DD %")),
            "sharpe": C._so(d.get("Sharpe Ratio")),
            "pct_nam": (((VON + lai) / VON) ** (1 / NAM_QT) - 1) * 100})
    print("  %d pass, %ss" % (len(ra), giay), flush=True)
    return ra


def _xep(ds):
    for x in ds:
        x["loi_tren_dd"] = round(x["lai"] / x["dd"], 1) if x["dd"] > 0 else 0.0
    return sorted(ds, key=lambda x: -x["loi_tren_dd"])


def _mo_ta(x):
    return ("kieu%d trail%.1f/tu%.1f BE%.2f tia%.2f vaolai%d nhoi%d/%.1f/%.1f/%d"
            % (x["kieu"], x["trail"], x["trail_tu"], x["be"], x["tia"],
               x["vao_lai"], x["nhoi"], x["nhoi_atr"], x["nhoi_he_so"],
               x["nhoi_max"]))


def main() -> int:
    kho = {}
    try:
        kho = {c["ten"]: c for c in BB.lay_chan()}
    except Exception:
        pass
    a, b = kho.get(A), kho.get(B)
    if a is None or b is None:
        from nhan import ngu_phap as NP
        k2 = {c["ten"]: c for c in NP.doc_kho()}
        a = a or k2.get(A)
        b = b or k2.get(B)
    if a is None or b is None:
        print("khong tim thay chan: %s / %s" % (A, B))
        return 1
    sinh(a, b)

    gop, tot = {}, None
    for ten, dong in SWEEP:
        print("\n### %s" % ten, flush=True)
        ds = _xep(chay("qt_%s_%s" % (ten, MA), LOT_CO_DINH, dong))
        if not ds:
            continue
        # `moc` phai lay tu CHINH luot nay: cung mot EA nhung khac lan boot thi
        # con so co the lech, va so hai luot khac nhau la so hai thu khac nhau.
        moc = next((x for x in ds if x["kieu"] == 0 and x["be"] == 0
                    and x["tia"] == 0 and x["nhoi"] == 0), None)
        print("%-54s %6s %10s %8s %8s"
              % ("cau hinh", "lenh", "lai", "sutgiam", "lai/DD"))
        for x in ds[:8]:
            print("%-54s %6d %10.2f %7.2f%% %8.1f"
                  % (_mo_ta(x)[:54], x["lenh"], x["lai"], x["dd"],
                     x["loi_tren_dd"]))
        if moc:
            print("MOC tat het quan tri: %d lenh | lai %.2f | DD %.2f%% | "
                  "lai/DD %.1f" % (moc["lenh"], moc["lai"], moc["dd"],
                                   moc["loi_tren_dd"]))
            print("TOT NHAT: %s -> lai/DD %.1f (x%.2f moc)"
                  % (_mo_ta(ds[0]), ds[0]["loi_tren_dd"],
                     ds[0]["loi_tren_dd"] / moc["loi_tren_dd"]
                     if moc["loi_tren_dd"] else 0))
        gop[ten] = {"moc": moc, "top": ds[:12]}
        if tot is None or ds[0]["loi_tren_dd"] > tot["loi_tren_dd"]:
            tot = ds[0]
        DG.ghi("QUAN_TRI_%s.json" % MA, {"symbol": MA, "chan": [A, B],
                                         "model": MODEL, "sweep": gop})

    if tot is None:
        return 1
    print("\n### RA TIEN voi quan tri tot nhat: %s" % _mo_ta(tot), flush=True)
    b2 = chay("qt_ratien_%s" % MA,
              "InpLot0=0||0||0.2||2.0||Y" + NL
              + "InpLot1=0||0||1.6||16.0||Y" + NL
              + "InpLot2=0||0||1.6||16.0||Y" + NL,
              "InpKieuRa=%d||%d||0||0||N" % (tot["kieu"], tot["kieu"]) + NL
              + "InpTrailATR=%s||%s||0||0||N" % (tot["trail"], tot["trail"]) + NL
              + "InpTrailTu=%s||%s||0||0||N" % (tot["trail_tu"], tot["trail_tu"]) + NL
              + "InpBE=%s||%s||0||0||N" % (tot["be"], tot["be"]) + NL
              + "InpTiaATR=%s||%s||0||0||N" % (tot["tia"], tot["tia"]) + NL
              + "InpVaoLai=%d||%d||0||0||N" % (tot["vao_lai"], tot["vao_lai"]) + NL
              + "InpNhoi=%d||%d||0||0||N" % (tot["nhoi"], tot["nhoi"]) + NL
              + "InpNhoiATR=%s||%s||0||0||N" % (tot["nhoi_atr"], tot["nhoi_atr"]) + NL
              + "InpNhoiHeSo=%s||%s||0||0||N" % (tot["nhoi_he_so"], tot["nhoi_he_so"]) + NL
              + "InpNhoiMax=%d||%d||0||0||N" % (tot["nhoi_max"], tot["nhoi_max"]) + NL)

    def gom(chon):
        g = [x for x in b2 if chon(x["lot"])]
        if not g:
            return None
        x = max(g, key=lambda y: y["pct_nam"])
        return {"lot": x["lot"], "dd": round(x["dd"], 2), "lenh": x["lenh"],
                "pct_nam": round(x["pct_nam"], 2), "sharpe": x["sharpe"]}

    ra = {"symbol": MA, "chan": [A, B], "model": MODEL, "sweep": gop,
          "quan_tri_tot_nhat": tot,
          "ghep": gom(lambda l: l[0] == 0 and l[1] > 0 and l[2] > 0),
          "chi_a": gom(lambda l: l[0] == 0 and l[1] > 0 and l[2] == 0),
          "chi_b": gom(lambda l: l[0] == 0 and l[1] == 0 and l[2] > 0),
          "mua_giu": gom(lambda l: l[0] > 0 and l[1] == 0 and l[2] == 0)}
    for nhan in ("ghep", "chi_a", "chi_b", "mua_giu"):
        x = ra[nhan]
        print("   %-9s %s" % (nhan,
              ("%6.2f%%/nam @ DD %6.2f%%  lot %s  (%d lenh)"
               % (x["pct_nam"], x["dd"],
                  "/".join("%.1f" % v for v in x["lot"]), x["lenh"]))
              if x else "--"))
    DG.ghi("QUAN_TRI_%s.json" % MA, ra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
