# -*- coding: utf-8 -*-
"""_ma_tran_ghep.py - MA TRAN TUONG QUAN CUA CA NHOM UNG VIEN, MOT LAN CHAY.

Phat hien 07/09: ghep `mean_reversion_z5` (mua) voi `quantora_ma_dashboard_sell`
(ban) nang %/nam o CUNG sut giam tu 6,14% len 20,25% tren US100. Khong co che
don le nao trong kho lam duoc dieu do - ke ca mot he manh bang z5.

Nen cau hoi dung tiep theo khong phai "tim them co che manh" ma la **"con cap
nao am nhau nua khong"**. Bai nay tra loi bang MOT lan chay:

  41 slot chay dong thoi trong mot EA, moi slot mot magic, moi slot ghi duong
  von rieng theo tung nen -> ma tran tuong quan 41x41 tu mot lan boot.

## HAI BAI HOC DA DO, DUNG LAM NGUOC

1. **Tuong quan am KHONG DU.** GER40 cho tuong quan am nhat trong bon ma
   (-0,4429) nhung ghep lai TE HON z5 mot minh, vi quantora tren GER40 lo
   -443,64 USD. Chan thu hai phai tu no co ky vong duong. Nen bang xep hang o
   day **loai truoc moi cap co mot chan lo**, roi moi xep theo lai/sut giam.
2. **Do tuong quan tren bar cua CHINH cong cu se giao dich** [[tang2-mt5-result]]
   - tuong quan tren bar Yahoo va bar CFD lech nhau 0,17 vs 0,58.

Chay: python _ma_tran_ghep.py [SYMBOL]
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chay_tester_kho as C            # noqa: E402
import _ghep_he as GH                  # noqa: E402
from _quet_placebo_rong import ds_ung_vien  # noqa: E402
from nhan import dich_mq5_ghep as G    # noqa: E402
from nhan import ngu_phap as NP        # noqa: E402

LAB = Path(__file__).resolve().parent
TEN_EA = "MaTranGhep"
VON = GH.VON


def sinh(ten_he: list[str], khung: str = "D1") -> list[dict]:
    kho = {c["ten"]: c for c in NP.doc_kho()}
    specs = [dict(G.SPEC_MUA_GIU)]
    for t in ten_he:
        c = kho.get(t)
        if c is not None:
            specs.append(c)
    ma, dat = G.sinh_ea_ghep(specs, TEN_EA, khung=khung, magic=26090801,
                             tep="MATRAN.csv")
    src = C.XM_DATA / "MQL5" / "Experts" / (TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        raise SystemExit("bien dich: " + loi)
    print("EA %d slot" % len(dat))
    return dat


def chay(symbol: str, n_slot: int, tu: str, den: str) -> Path:
    ten = "matran_%s" % symbol
    tep = "MATRAN_%s.csv" % symbol
    (C.XM_DATA / "MQL5" / "Profiles" / "Tester").mkdir(parents=True, exist_ok=True)
    (C.XM_DATA / "MQL5" / "Profiles" / "Tester" / (ten + ".set")).write_text(
        "".join("InpLot%d=0.10||0.10||0||0||N\n" % i for i in range(n_slot))
        + "InpMagic=26090801||26090801||0||0||N\nInpGhi=1||1||0||0||N\n"
        + "InpTep=%s\n" % tep, encoding="utf-8")
    (C.XM_DATA / (ten + ".ini")).write_text("""[Tester]
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
""" % (TEN_EA, ten, symbol, C.KHUNG_CHAY, tu, den, VON, ten), encoding="utf-16")
    ra = GH.CHUNG / tep
    if ra.exists():
        ra.unlink()
    print("  chay ...", flush=True)
    giay = GH._chay_terminal(C.XM_DATA / (ten + ".ini"), tran=3600)
    print("  %ss" % giay)
    hong = C.kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        raise SystemExit(hong)
    if not ra.exists():
        raise SystemExit("EA khong ghi duoc %s" % ra)
    return ra


def phan_tich(f: Path, ten_slot: list[str], symbol: str) -> dict:
    tg, von, mo, gia = GH.doc_csv(f)
    n = len(von)
    dv = [[v[j] - v[j - 1] for j in range(1, len(v))] for v in von]
    lai = [v[-1] for v in von]
    dd = [GH._sut_giam(v) for v in von]
    print("\n%d slot, %d nen (%s -> %s)" % (n, len(tg), tg[0], tg[-1]))

    #: Chan LO bi loai TRUOC khi xep hang cap - bai hoc GER40: tuong quan am ma
    #: chan thu hai lo thi ghep chi la mot cach dat tien de giam bien dong.
    duong = [i for i in range(1, n) if lai[i] > 0]
    print("chan co lai duong: %d/%d" % (len(duong), n - 1))

    cap = []
    for x in range(len(duong)):
        for y in range(x + 1, len(duong)):
            i, j = duong[x], duong[y]
            r = GH._tuong_quan(dv[i], dv[j])
            t = [von[i][k] + von[j][k] for k in range(len(von[i]))]
            d = GH._sut_giam(t)
            cap.append({"a": ten_slot[i], "b": ten_slot[j], "r": round(r, 4),
                        "lai": round(t[-1], 2), "dd": round(d, 3),
                        "lai_a": round(lai[i], 2), "lai_b": round(lai[j], 2),
                        "dd_a": round(dd[i], 3), "dd_b": round(dd[j], 3),
                        # Lai tren mot diem sut giam: xep hang o CUNG rui ro,
                        # khong xep theo tong lai [[cong-ra-tien-la-cong-thu-hai]].
                        "loi_tren_dd": round(t[-1] / d, 1) if d > 0 else 0.0})
    cap.sort(key=lambda c: -c["loi_tren_dd"])

    don = sorted(({"ten": ten_slot[i], "lai": round(lai[i], 2),
                   "dd": round(dd[i], 3),
                   "loi_tren_dd": round(lai[i] / dd[i], 1) if dd[i] > 0 else 0.0}
                  for i in range(1, n)),
                 key=lambda d: -d["loi_tren_dd"])

    print("\n--- 12 HE DON tot nhat theo lai/sut giam ---")
    print("%-44s %9s %8s %9s" % ("he", "lai", "sutgiam", "lai/DD"))
    for d in don[:12]:
        print("%-44s %9.2f %7.2f%% %9.1f" % (d["ten"][:44], d["lai"], d["dd"],
                                             d["loi_tren_dd"]))
    print("\n--- 15 CAP tot nhat theo lai/sut giam (ca hai chan deu lai) ---")
    print("%-26s %-26s %7s %9s %8s %9s" % ("chan A", "chan B", "r", "lai",
                                           "sutgiam", "lai/DD"))
    for c in cap[:15]:
        print("%-26s %-26s %+7.3f %9.2f %7.2f%% %9.1f"
              % (c["a"][:26], c["b"][:26], c["r"], c["lai"], c["dd"],
                 c["loi_tren_dd"]))

    tot_don = don[0]["loi_tren_dd"] if don else 0
    print("\nhe don tot nhat: %.1f lai/DD  |  cap tot nhat: %.1f  (gap %.2f lan)"
          % (tot_don, cap[0]["loi_tren_dd"] if cap else 0,
             (cap[0]["loi_tren_dd"] / tot_don) if cap and tot_don else 0))

    ra = {"symbol": symbol, "so_slot": n, "so_nen": len(tg),
          "don": don, "cap": cap[:120]}
    (LAB / "reports" / ("MATRAN_%s.json" % symbol)).write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    print("-> reports/MATRAN_%s.json" % symbol)
    return ra


def main() -> int:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
    tu = sys.argv[2] if len(sys.argv) > 2 else "2016.06.01"
    den = sys.argv[3] if len(sys.argv) > 3 else "2026.07.29"
    he = ds_ung_vien()
    print("%d ung vien qua train+holdout" % len(he))
    dat = sinh(he)
    ten_slot = [c["ten"] for c in dat]
    f = chay(symbol, len(dat), tu, den)
    phan_tich(f, ten_slot, symbol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
