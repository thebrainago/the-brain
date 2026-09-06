# -*- coding: utf-8 -*-
"""_z5_don_bay.py - %/NAM THAT O DON BAY THAT.

Moi con so cua phien 06/09 chay o **lot 0,10 co dinh tren von 10.000** - don bay
~0,03x. Nen "+1.341 USD" la mot bang chung ve HUONG, khong phai mot muc loi
suat. Bai nay quet lot de ra du sau con so cua `nhan/cham_diem.py`:

    lai %/nam tren VON PHAI BO RA · sut giam · von can · hoi von thang ·
    so lenh/nam · nguy co chay

Quet CA `__mua_giu__` cung mot luoi lot, trong cung mot EA - de moc so sanh o
moi muc don bay deu la moc DI QUA CUNG BO THUC THI.

## HAI CHO DE SAI, DEU DA GHI TRONG BO NHO

- **Khong gop bang log khi don bay != 1** [[don-bay-gop-log-sai]]: `(S_T/S_0)^L`
  bo mat luc can bien dong va bo mat kha nang chay tai khoan. O day khong phai
  gop gi ca - tester chay lot that va tra ve duong von that, ke ca luc no chay.
- **Tran loi suat la Sharpe** [[tran-lai-suat-la-sharpe]]: CAGR toi da o moi
  don bay la `0,5*S^2`. Neu bang do ra %/nam vuot han tran do thi co cho sai.

`min_lot` cua US100Cash la **0,1** - khong xuong duoc thap hon.

Chay: python _z5_don_bay.py [SYMBOL] [tu] [den]
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chay_tester_kho as C     # noqa: E402
from nhan import dich_mq5 as D  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

LAB = Path(__file__).resolve().parent
HE = "mean_reversion_z5"
VON = 10000
LOT = [round(0.1 * i, 1) for i in range(1, 31)]      # 0,1 .. 3,0


def viet_ini(ten, symbol, tu, den):
    p = C.XM_DATA / ("%s.ini" % ten)
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
InpMaCoChe=0||0||1||1||Y
InpLot=0.1||0.1||0.1||3.0||Y
InpMagic=26090601||26090601||0||0||N
""" % (C.TEN_EA, symbol, C.KHUNG_CHAY, tu, den, VON, ten), encoding="utf-16")
    return p


def chay(symbol: str, tu: str, den: str) -> dict:
    kho = {c["ten"]: c for c in NP.doc_kho() if not NP.kiem_khai_bao(c)}
    if HE not in kho:
        return {"loi": "khong co %s trong kho" % HE}
    ma, dat = D.sinh_ea([kho[HE]], C.TEN_EA, khung="D1", them_mua_giu=True)
    src = C.XM_DATA / "MQL5" / "Experts" / (C.TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        return {"loi": loi}
    print("EA: %s" % " + ".join(c["ten"] for c in dat))

    ten = "donbay_%s" % symbol
    ini = viet_ini(ten, symbol, tu, den)
    for h in (".xml", ".htm"):
        f = C.XM_DATA / (ten + h)
        if f.exists():
            f.unlink()
    C.dong_terminal()
    print("  quet %d lot x %d co che ..." % (len(LOT), len(dat)), flush=True)
    t0 = time.time()
    subprocess.Popen([str(C.XM_EXE), "/config:%s" % ini])
    while time.time() - t0 < 2400:
        time.sleep(8)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                           capture_output=True, text=True)
        if "terminal64.exe" not in r.stdout:
            break

    hong = C.kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        return {"loi": hong}
    f = C.XM_DATA / (ten + ".xml")
    if not f.exists():
        return {"loi": "khong thay bang ket qua"}

    nam = (int(den[:4]) + int(den[5:7]) / 12.0) - (int(tu[:4]) + int(tu[5:7]) / 12.0)
    bang = {c["ten"]: {} for c in dat}
    for d in C.doc_xml(f):
        i = int(C._so(d.get("InpMaCoChe", -1), -1))
        lot = round(C._so(d.get("InpLot", 0)), 2)
        if not (0 <= i < len(dat)) or lot <= 0:
            continue
        lai = C._so(d.get("Profit"))
        dd = C._so(d.get("Equity DD %"))
        bang[dat[i]["ten"]][lot] = {
            "lai": lai, "dd_pct": dd, "lenh": int(C._so(d.get("Trades"))),
            "sharpe": C._so(d.get("Sharpe Ratio")),
            # Loi suat tren VON, gop theo nam that. Khong gop bang log.
            # Von cuoi <= 0 la CHAY TAI KHOAN. Luy thua phan so cua so am cho
            # ra SO PHUC trong Python - mot con so "loi suat" khong ai doc duoc
            # thay vi mot canh bao. Phai bao dung ten.
            "chay": (VON + lai) <= 0,
            "pct_nam": ((((VON + lai) / VON) ** (1 / nam) - 1) * 100
                        if nam > 0 and (VON + lai) > 0 else float("nan")),
            "lenh_nam": int(C._so(d.get("Trades")) / nam) if nam > 0 else 0}

    ra = {"symbol": symbol, "tu": tu, "den": den, "nam": round(nam, 2),
          "von": VON, "bang": bang}
    # Khoa dict la SO THUC -> `json.dumps` nem. Doi sang chuoi khi ghi.
    (LAB / "reports" / ("DON_BAY_%s.json" % symbol)).write_text(
        json.dumps({**ra, "bang": {k: {str(l): x for l, x in v.items()}
                                   for k, v in bang.items()}},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    he = bang.get(HE, {})
    mg = bang.get("__mua_giu__", {})
    print("\n%s  %s -> %s  (%.2f nam, von %d USD)"
          % (symbol, tu, den, nam, VON))
    print("\n%5s %6s %9s %8s %8s %7s   | %s"
          % ("lot", "lenh", "lai USD", "%/nam", "sutgiam", "sharpe", "mua-giu cung lot"))
    for lot in sorted(he):
        v = he[lot]
        m = mg.get(lot)
        moc = ("CHAY TAI KHOAN" if m and m.get("chay") else
               ("%8.2f%% / DD %5.2f%%" % (m["pct_nam"], m["dd_pct"])) if m else "  --")
        print("%5.1f %6d %9.2f %7.2f%% %7.2f%% %7.2f   | %s"
              % (lot, v["lenh"], v["lai"], v["pct_nam"], v["dd_pct"],
                 v["sharpe"], moc))

    # So o CUNG SUT GIAM: voi moi muc DD cua mua-giu, tim lot cua he cho DD do.
    print("\n--- so o CUNG SUT GIAM ---")
    for lot_mg in sorted(mg):
        d_mg = mg[lot_mg]
        gan = min((abs(he[l]["dd_pct"] - d_mg["dd_pct"]), l) for l in he) if he else None
        if not gan or gan[0] > 1.0:
            continue
        l = gan[1]
        print("  mua-giu lot %.1f: DD %5.2f%% -> %6.2f%%/nam   |  he lot %.1f: "
              "DD %5.2f%% -> %6.2f%%/nam  (%+.2f diem)"
              % (lot_mg, d_mg["dd_pct"], d_mg["pct_nam"], l, he[l]["dd_pct"],
                 he[l]["pct_nam"], he[l]["pct_nam"] - d_mg["pct_nam"]))
    return ra


def main() -> int:
    ma = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
    tu = sys.argv[2] if len(sys.argv) > 2 else "2016.06.01"
    den = sys.argv[3] if len(sys.argv) > 3 else "2026.07.29"
    r = chay(ma, tu, den)
    if r.get("loi"):
        print("LOI:", r["loi"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
