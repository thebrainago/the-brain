# -*- coding: utf-8 -*-
"""_bo_ba.py - GHEP BA CHAN, VA KHU TRUNG THEO DUONG VON.

Chu du an 07/09/2026: *"Ghep cac chan duong va am de tao ra co che tot hon."*
`_dem_ghep.py` moi ghep DOI. Bai nay di tiep len BO BA - va lam hai viec ma bang
cap khong lam duoc:

## 1. KHU TRUNG THEO DUONG VON, khong theo ten hay van tay spec

Do 07/09: trong 84 chan duong, ba ten khac nhau cho ket qua **y het** (lai
1.273,43 / DD 4,06%): `martingale_level_1` · `consecutive_down_bars_signal__dao`
· `ob_bearish_rectangle_created__dao`. Mot nhom bon ten khac cung trung o 631,8.
Khau khu trung van tay hien co khong bat duoc vi spec khac nhau tren giay ma
sinh ra **cung mot chuoi lenh**. Phep khu dung la so **duong von tung nen**.

Neu khong khu thi bang bo ba se day nhung "bo ba" that ra la mot he nhan ba lot
- va no se dan dau bang vi cong don lai ma khong cong don sut giam bao nhieu.

## 2. Duyet bo ba KHONG CAN CHAY TESTER

Duong von tung chan da do bang tester roi (`InpGhi=1`). Cong ba chuoi lai o
Python la phep cong dung, vi ba slot giu vi the DOC LAP tren tai khoan hedging
va ky quy khong rang buoc o muc lot nay. Nen 30 chan -> 4.060 bo ba duyet trong
mot nhay, roi chi dua **top vai bo** ra tester de lay %/nam that o luoi lot.

## BAI HOC PHAI GIU

**Tuong quan am khong du - moi chan phai TU NO co ky vong duong**
[[ghep-chan-am-re-hon-chan-manh]]. GER40 co tuong quan am nhat (-0,4429) ma ghep
lai te hon, vi chan thu hai lo -443,64 USD.

Chay: python _bo_ba.py [SYMBOL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _dem_ghep as DG                 # noqa: E402
import _ghep_he as GH                  # noqa: E402
import chay_tester_kho as C            # noqa: E402
from nhan import dich_mq5_ghep as G    # noqa: E402
from nhan import ngu_phap as NP        # noqa: E402

LAB = Path(__file__).resolve().parent
BC = LAB / "reports"
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
VON = GH.VON
NAM = DG.NAM
TOP_CHAN = 30          # 30 chan -> 435 cap + 4.060 bo ba, duyet tuc thi
SO_BO_RA_TESTER = 4


def lay_chan() -> list[dict]:
    d = json.load(open(BC / ("DEM_CHAN_DUONG_%s.json" % MA), encoding="utf-8"))
    kho = {}
    for c in NP.doc_kho():
        c = dict(c, co_che=c.get("co_che") or "MIEN CONG DE DO.")
        kho[c["ten"]] = c
    chan = [kho[t] for t in d["goc"] if t in kho]
    for t in d["dao"]:
        goc = kho.get(t[:-5] if t.endswith("__dao") else t)
        if goc is None:
            continue
        chan.append(dict(goc, ten=t, chieu=-int(goc.get("chieu", 1) or 1),
                         co_che="BAN DAO CHIEU cua %s." % goc["ten"]))
    return chan


def von_tung_chan(chan: list[dict]) -> dict:
    """Chay tung lo 40 slot, tra {ten: chuoi lai luy ke}. Ghi lai de dung sau."""
    f = BC / ("DEM_VON_%s.json" % MA)
    if f.exists():
        d = json.load(open(f, encoding="utf-8"))
        d = d.get("von", d)
        print("dung lai duong von da do: %d chan" % len(d), flush=True)
        return d
    goc, tat = [], {}
    for lo in range((len(chan) + DG.SLOT_MOI_LAN - 1) // DG.SLOT_MOI_LAN):
        phan = chan[lo * DG.SLOT_MOI_LAN:(lo + 1) * DG.SLOT_MOI_LAN]
        print("=== lo %d: %d slot" % (lo, len(phan)), flush=True)
        tg, d = DG.duong_von(phan, lo)
        if not goc and tg:
            goc = tg
        for k, v in d.items():
            if len(v) == len(goc):
                tat[k] = v
    # Luu CA moc thoi gian: khong co no thi khong cat duoc train/holdout de
    # cham cap tren mot doan roi kiem tren doan kia - ma bang xep hang cap tren
    # TOAN cua so la in-sample doi voi chinh phep chon chan.
    f.write_text(json.dumps({"tg": goc, "von": tat}, ensure_ascii=False),
                 encoding="utf-8")
    print("-> reports/DEM_VON_%s.json (%d chan)" % (MA, len(tat)), flush=True)
    return tat


def khu_trung(tat: dict) -> dict:
    """Bo chan co duong von TRUNG voi mot chan da giu (lam tron 2 chu so)."""
    thay, giu, bo = {}, {}, {}
    for t in sorted(tat):
        khoa = tuple(round(x, 2) for x in tat[t])
        if khoa in thay:
            bo.setdefault(thay[khoa], []).append(t)
            continue
        thay[khoa] = t
        giu[t] = tat[t]
    if bo:
        print("\nkhu trung duong von: bo %d chan"
              % sum(len(v) for v in bo.values()), flush=True)
        for k, v in list(bo.items())[:8]:
            print("   %-40s == %s" % (k[:40], ", ".join(x[:34] for x in v[:3])),
                  flush=True)
    print("con %d chan doc lap (tu %d)" % (len(giu), len(tat)), flush=True)
    return giu


def duyet(tat: dict) -> dict:
    ten = sorted(tat)
    lai = {t: tat[t][-1] for t in ten}
    ten = [t for t in ten if lai[t] > 0]
    dd = {t: GH._sut_giam(tat[t]) for t in ten}
    dv = {t: [tat[t][j] - tat[t][j - 1] for j in range(1, len(tat[t]))]
          for t in ten}
    don = sorted(ten, key=lambda t: -(lai[t] / dd[t] if dd[t] > 0 else 0))
    top = don[:TOP_CHAN]

    def cham(bo):
        t = [sum(tat[x][k] for x in bo) for k in range(len(tat[bo[0]]))]
        d = GH._sut_giam(t)
        return (t[-1], d, (t[-1] / d) if d > 0 else 0.0)

    cap, ba = [], []
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            l, d, s = cham([top[i], top[j]])
            cap.append({"bo": [top[i], top[j]], "lai": round(l, 2),
                        "dd": round(d, 3), "loi_tren_dd": round(s, 1),
                        "r": round(GH._tuong_quan(dv[top[i]], dv[top[j]]), 3)})
            for k in range(j + 1, len(top)):
                l, d, s = cham([top[i], top[j], top[k]])
                ba.append({"bo": [top[i], top[j], top[k]], "lai": round(l, 2),
                           "dd": round(d, 3), "loi_tren_dd": round(s, 1)})
    cap.sort(key=lambda x: -x["loi_tren_dd"])
    ba.sort(key=lambda x: -x["loi_tren_dd"])

    print("\n--- 8 he DON tot nhat ---", flush=True)
    for t in don[:8]:
        print("%-46s %9.2f %7.2f%% %8.1f"
              % (t[:46], lai[t], dd[t], lai[t] / dd[t] if dd[t] else 0),
              flush=True)
    print("\n--- 8 CAP tot nhat ---", flush=True)
    for c in cap[:8]:
        print("%-28s + %-28s r%+6.2f %9.2f %6.2f%% %8.1f"
              % (c["bo"][0][:28], c["bo"][1][:28], c["r"], c["lai"], c["dd"],
                 c["loi_tren_dd"]), flush=True)
    print("\n--- 10 BO BA tot nhat ---", flush=True)
    for c in ba[:10]:
        print("%-24s + %-24s + %-24s %9.2f %6.2f%% %8.1f"
              % (c["bo"][0][:24], c["bo"][1][:24], c["bo"][2][:24], c["lai"],
                 c["dd"], c["loi_tren_dd"]), flush=True)
    tot_don = lai[don[0]] / dd[don[0]] if don and dd[don[0]] else 0
    print("\ndon %.1f  |  cap %.1f (x%.2f)  |  bo ba %.1f (x%.2f)"
          % (tot_don, cap[0]["loi_tren_dd"],
             cap[0]["loi_tren_dd"] / tot_don if tot_don else 0,
             ba[0]["loi_tren_dd"],
             ba[0]["loi_tren_dd"] / tot_don if tot_don else 0), flush=True)
    ra = {"so_chan": len(ten), "don": [{"ten": t, "lai": round(lai[t], 2),
                                        "dd": round(dd[t], 3)} for t in don],
          "cap": cap[:60], "bo_ba": ba[:60]}
    DG.ghi("BOBA_%s.json" % MA, ra)
    return ra


def ra_tien(bo_ba: list[dict], chan: list[dict]) -> None:
    """Luoi lot cho top bo ba: 4 slot (mua-giu + ba chan), 11^4 = 14.641 pass."""
    theo_ten = {c["ten"]: c for c in chan}
    ket = []
    for k, b in enumerate(bo_ba[:SO_BO_RA_TESTER]):
        spec = [theo_ten.get(t) for t in b["bo"]]
        if any(s is None for s in spec):
            continue
        print("\n=== bo ba %d: %s" % (k, " + ".join(t[:26] for t in b["bo"])),
              flush=True)
        ma, dat = G.sinh_ea_ghep([dict(G.SPEC_MUA_GIU)] + spec, "BoBaRaTien",
                                 khung="D1", magic=26091100)
        src = C.XM_DATA / "MQL5" / "Experts" / "BoBaRaTien.mq5"
        src.write_text(ma, encoding="utf-8")
        if C.bien_dich(src):
            continue
        nc = "boba%d_%s" % (k, MA)
        (C.XM_DATA / (nc + ".ini")).write_text("""[Tester]
Expert=BoBaRaTien.ex5
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
InpLot0=0||0||0.2||2.0||Y
InpLot1=0||0||1.6||16.0||Y
InpLot2=0||0||1.6||16.0||Y
InpLot3=0||0||1.6||16.0||Y
InpMagic=26091100||26091100||0||0||N
InpGhi=0||0||0||0||N
""" % (MA, C.KHUNG_CHAY, DG.DAU, DG.CUOI, VON, nc), encoding="utf-16")
        for h in (".xml", ".htm"):
            f = C.XM_DATA / (nc + h)
            if f.exists():
                f.unlink()
        GH._chay_terminal(C.XM_DATA / (nc + ".ini"), tran=3600)
        f = C.XM_DATA / (nc + ".xml")
        if not f.exists():
            print("   khong ra bang", flush=True)
            continue
        hang = []
        for d in C.doc_xml(f):
            lot = [round(C._so(d.get("InpLot%d" % i, -1), -1), 2)
                   for i in range(4)]
            if any(x < 0 for x in lot):
                continue
            l_ = C._so(d.get("Profit"))
            if VON + l_ <= 0:
                continue
            hang.append({"lot": lot, "lenh": int(C._so(d.get("Trades"))),
                         "dd": C._so(d.get("Equity DD %")),
                         "sharpe": C._so(d.get("Sharpe Ratio")),
                         "pct_nam": (((VON + l_) / VON) ** (1 / NAM) - 1) * 100})

        def gom(chon):
            g = [h for h in hang if chon(h["lot"])]
            if not g:
                return None
            h = max(g, key=lambda x: x["pct_nam"])
            return {"lot": h["lot"], "dd": round(h["dd"], 2), "lenh": h["lenh"],
                    "pct_nam": round(h["pct_nam"], 2), "sharpe": h["sharpe"]}

        r = {"bo": b["bo"],
             "ba_chan": gom(lambda l: l[0] == 0 and l[1] > 0 and l[2] > 0
                            and l[3] > 0),
             "mot_chan_tot_nhat": gom(lambda l: l[0] == 0
                                      and sum(1 for x in l[1:] if x > 0) == 1),
             "mua_giu": gom(lambda l: l[0] > 0 and max(l[1:]) == 0)}
        ket.append(r)
        for nhan in ("ba_chan", "mot_chan_tot_nhat", "mua_giu"):
            x = r[nhan]
            print("   %-18s %s" % (nhan,
                  ("%6.2f%%/nam @ DD %5.2f%%  lot %s  (%d lenh)"
                   % (x["pct_nam"], x["dd"],
                      "/".join("%.1f" % v for v in x["lot"]), x["lenh"]))
                  if x else "--"), flush=True)
        DG.ghi("BOBA_RA_TIEN_%s.json" % MA, ket)


def main() -> int:
    chan = lay_chan()
    print("%d chan duong" % len(chan), flush=True)
    tat = khu_trung(von_tung_chan(chan))
    ra = duyet(tat)
    ra_tien(ra["bo_ba"], chan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
