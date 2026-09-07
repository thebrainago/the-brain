# -*- coding: utf-8 -*-
"""_ghep_h4.py - AP QUY TRINH GHEP LEN H4, BANG CHAN CUA CHINH H4.

Vi sao H4 chu khong phai khung khac (ca ba deu la so do duoc 07/09):

  1. **Quy trinh ghep da chung minh song NGOAI MAU tren D1**: 39/45 cap dau bang
     train van hon chinh he don do o holdout, trong khi bang he don la nhieu
     (822,7 -> 40,7) [[ghep-song-o-holdout-he-don-thi-khong]].
  2. **H4 co chan don manh hon D1** (lai/DD 735,1 vs 542,8) va con **61 chan
     duong** khi quet truc tiep - du de ghep.
  3. **H1 tro xuong thi ti le song duoi 7%**: chan duong D1 84 -> H4 61 -> H1 29
     -> M30 16, giam don dieu theo dung ti le spread/bien do nen
     [[khung-nho-do-du-lieu-quyet-dinh]].

## KHONG BUNG CHAN CUA D1 SANG

Chan o day lay tu `KHUNG_NHO_<MA>.json` - la chan **duoc chon tren chinh H4**
(duong o ca train lan holdout cua H4), khong phai chan D1 quy doi chu ky sang.
Do 07/09: be 36 chan D1 sang H1 thi tong lai **-4.739**. Doi khung phai chon lai
tu dau, hoac giu TY LE KICH HOAT chu khong giu con so (CLAUDE.md muc "DOI KHUNG
= DOI TAI SAN").

## BA CHANG, GIONG HET DUONG D1

    A  duong von tung chan (41 slot/lan chay, `InpGhi=1`)
    B  khu trung theo DUONG VON roi xep hang cap - **cham tren TRAIN, doc o
       HOLDOUT**, vi bang cham tren toan cua so la in-sample doi voi phep chon
       chan
    C  cong ra tien: luoi lot cho top cap, so voi mua-giu o CUNG sut giam

Chay: python _ghep_h4.py [SYMBOL]
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
KHUNG, KHUNG_CHAY = "H4", "H1"
DAU, CAT, CUOI = "2016.06.01", "2021.06.01", "2026.07.29"
NAM = (2026 + 7 / 12) - (2016 + 6 / 12)
VON = GH.VON
TOP = 30


def lay_chan() -> list[dict]:
    d = json.load(open(BC / ("KHUNG_NHO_%s.json" % MA), encoding="utf-8"))
    if KHUNG not in d or "ten_duong" not in d[KHUNG]:
        raise SystemExit("chua co ten chan H4 - chay `_khung_nho.py %s H4`" % MA)
    k = d[KHUNG]
    kho = {}
    for c in NP.doc_kho():
        kho[c["ten"]] = dict(c, co_che=c.get("co_che") or "MIEN CONG DE DO.")
    chan = [kho[t] for t in k["ten_duong"] if t in kho]
    for t in k["ten_dao_duong"]:
        g = kho.get(t[:-5] if t.endswith("__dao") else t)
        if g is None:
            continue
        chan.append(dict(g, ten=t, chieu=-int(g.get("chieu", 1) or 1),
                         co_che="BAN DAO CHIEU cua %s." % g["ten"]))
    return chan


def duong_von(chan: list[dict]) -> tuple[list, dict]:
    goc, tat = [], {}
    for lo in range((len(chan) + DG.SLOT_MOI_LAN - 1) // DG.SLOT_MOI_LAN):
        phan = chan[lo * DG.SLOT_MOI_LAN:(lo + 1) * DG.SLOT_MOI_LAN]
        ten_ea = "GhepH4_%d" % lo
        tep = "H4VON%d_%s.csv" % (lo, MA)
        ma, dat = G.sinh_ea_ghep([dict(G.SPEC_MUA_GIU)] + phan, ten_ea,
                                 khung=KHUNG, magic=26091600 + lo * 100, tep=tep)
        src = C.XM_DATA / "MQL5" / "Experts" / (ten_ea + ".mq5")
        src.write_text(ma, encoding="utf-8")
        if C.bien_dich(src):
            print("  lo %d: bien dich hong" % lo, flush=True)
            continue
        nc = "h4von%d_%s" % (lo, MA)
        (C.XM_DATA / "MQL5" / "Profiles" / "Tester").mkdir(parents=True,
                                                           exist_ok=True)
        (C.XM_DATA / "MQL5" / "Profiles" / "Tester" / (nc + ".set")).write_text(
            "".join("InpLot%d=0.10||0.10||0||0||N\n" % i for i in range(len(dat)))
            + "InpMagic=%d||%d||0||0||N\nInpGhi=1||1||0||0||N\n"
            % (26091600 + lo * 100, 26091600 + lo * 100)
            + "InpTep=%s\n" % tep, encoding="utf-8")
        (C.XM_DATA / (nc + ".ini")).write_text("""[Tester]
Expert=%s.ex5
ExpertParameters=%s.set
Symbol=%s
Period=%s
Model=2
ExecutionMode=0
Optimization=0
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
""" % (ten_ea, nc, MA, KHUNG_CHAY, DAU, CUOI, VON, nc), encoding="utf-16")
        f = GH.CHUNG / tep
        if f.exists():
            f.unlink()
        print("  lo %d: %d slot ..." % (lo, len(dat)), flush=True)
        GH._chay_terminal(C.XM_DATA / (nc + ".ini"), tran=3600)
        if not f.exists():
            print("  lo %d khong ghi CSV" % lo, flush=True)
            continue
        tg, von, mo, gia = GH.doc_csv(f)
        if not goc:
            goc = tg
        for i in range(1, len(dat)):
            if i < len(von) and len(von[i]) == len(goc):
                tat[dat[i]["ten"]] = von[i]
    return goc, tat


def main() -> int:
    chan = lay_chan()
    print("H4: %d chan duong (chon TREN H4)" % len(chan), flush=True)
    tg, tat = duong_von(chan)
    if len(tat) < 2:
        print("khong do duoc duong von")
        return 1
    i = next((k for k, x in enumerate(tg) if x[:10] >= CAT), len(tg) // 2)
    print("%d nen | cat %s: train %s..%s | holdout %s..%s"
          % (len(tg), CAT, tg[0][:10], tg[i - 1][:10], tg[i][:10], tg[-1][:10]))

    def doan(a, b):
        return {t: [v[j] - v[a] for j in range(a, b)] for t, v in tat.items()}

    tr, ho = doan(0, i), doan(i, len(tg))
    # Khu trung theo duong von TREN TRAIN: hai chan cung chuoi lenh thi ghep chi
    # la nhan doi lot, va no se dan dau bang mot cach gia.
    thay, giu = {}, []
    for t in sorted(tr):
        k = tuple(round(x, 2) for x in tr[t])
        if k in thay:
            continue
        thay[k] = t
        giu.append(t)
    duong = [t for t in giu if tr[t][-1] > 0]
    dd_tr = {t: GH._sut_giam(tr[t]) for t in duong}
    don = sorted((t for t in duong if dd_tr[t] > 0),
                 key=lambda t: -tr[t][-1] / dd_tr[t])[:TOP]
    print("khu trung %d -> %d | duong tren TRAIN %d | lay top %d"
          % (len(tat), len(giu), len(duong), len(don)))

    def cham(d, bo):
        t = [sum(d[x][k] for x in bo) for k in range(len(d[bo[0]]))]
        dd = GH._sut_giam(t)
        return (t[-1] / dd) if dd > 0 else 0.0

    cap = []
    for a in range(len(don)):
        for b in range(a + 1, len(don)):
            cap.append({"bo": [don[a], don[b]], "tr": round(cham(tr, [don[a], don[b]]), 1)})
    cap.sort(key=lambda c: -c["tr"])
    for c in cap:
        c["ho"] = round(cham(ho, c["bo"]), 1)
    moc_ho = cham(ho, [don[0]])
    n = 15
    giu_hang = sum(1 for c in cap[:n] if c["ho"] > moc_ho)
    tv = sorted(c["ho"] for c in cap[:n])[n // 2]

    print("\n--- 12 CAP dau bang TRAIN, doc ket qua o HOLDOUT (H4) ---")
    print("%-30s %-30s %9s %9s" % ("chan A", "chan B", "train", "holdout"))
    for c in cap[:12]:
        print("%-30s %-30s %9.1f %9.1f"
              % (c["bo"][0][:30], c["bo"][1][:30], c["tr"], c["ho"]))
    print("\nhe don dau bang TRAIN: %s" % don[0][:46])
    print("   train %.1f -> holdout %.1f" % (tr[don[0]][-1] / dd_tr[don[0]], moc_ho))
    print("cap dau bang TRAIN   : train %.1f -> holdout %.1f"
          % (cap[0]["tr"], cap[0]["ho"]))
    print("\n%d/%d cap dau bang train VAN hon he don do o holdout | "
          "trung vi holdout: %.1f" % (giu_hang, n, tv))
    DG.ghi("GHEP_H4_%s.json" % MA,
           {"symbol": MA, "khung": KHUNG, "so_chan": len(tat),
            "sau_khu_trung": len(giu), "don_train_dau_bang": don[0],
            "don_holdout": round(moc_ho, 1), "cap_giu_hang": giu_hang,
            "trung_vi_holdout": tv, "cap": cap[:60]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
