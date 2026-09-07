# -*- coding: utf-8 -*-
"""_thu_doi_khung.py - BO DOI KHUNG CO HIEU QUA KHONG? Ba ban, cung mot phep do.

Chu du an: *"Khi nao xay duoc bo chuyen doi timeframe muot va hieu qua thi thoi."*
Ty le kich hoat khop chua chung minh gi - phai cho ra tester.

Ba ban CUNG chan, CUNG cua so, CUNG khung dich:

    A  be nguyen        tham so D1 giu y het
    B  chi nhan chu ky  ban cu (`_da_khung.doi_khung`)
    C  bo doi moi       chu ky + khop phan vi + hieu chinh gop

Doc bang SO CHAN DUONG o CA train lan holdout, khong doc tong lai: tong lai bi
mot chan manh keo [[chieu-quyet-dinh-tuong-quan]].

Chay: python _thu_doi_khung.py [SYMBOL] [KHUNG_DICH]
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bo_ba as BB                    # noqa: E402
import _dem_ghep as DG                 # noqa: E402
import _ghep_he as GH                  # noqa: E402
import chay_tester_kho as C            # noqa: E402
from nhan import dich_mq5 as D         # noqa: E402
from nhan import doi_khung as DK       # noqa: E402

MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
MA_KHO = "XM_" + MA.upper()
DICH = sys.argv[2] if len(sys.argv) > 2 else "H4"
GOC = "D1"
DAU, CAT, CUOI = "2016.06.01", "2021.06.01", "2026.07.29"


def chay(spec, khung, tu, den, nhan):
    ma, dat = D.sinh_ea(spec, C.TEN_EA, khung=khung)
    src = C.XM_DATA / "MQL5" / "Experts" / (C.TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    if C.bien_dich(src):
        return []
    ten = "dk_%s_%s" % (nhan, MA)
    (C.XM_DATA / (ten + ".ini")).write_text("""[Tester]
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
InpMaCoChe=0||0||1||%d||Y
InpLot=0.10||0.10||0||0||N
InpMagic=26091700||26091700||0||0||N
""" % (C.TEN_EA, MA, tu, den, GH.VON, ten, len(dat) - 1), encoding="utf-16")
    f = C.XM_DATA / (ten + ".xml")
    if f.exists():
        f.unlink()
    GH._chay_terminal(C.XM_DATA / (ten + ".ini"), tran=3600)
    if not f.exists():
        return []
    ra = []
    for d in C.doc_xml(f):
        i = int(C._so(d.get("InpMaCoChe", -1), -1))
        if 0 <= i < len(dat):
            ra.append({"ten": dat[i]["ten"], "lenh": int(C._so(d.get("Trades"))),
                       "lai": C._so(d.get("Profit")),
                       "dd": C._so(d.get("Equity DD %"))})
    return ra


def main() -> int:
    chan = BB.lay_chan()
    print("%d chan D1 -> doi sang %s" % (len(chan), DICH), flush=True)
    dg = DK.nap_khung(MA_KHO, GOC, DAU, CAT)
    dd = DK.nap_khung(MA_KHO, DICH, DAU, CAT)
    if dg is None or dd is None:
        print("thieu du lieu")
        return 1
    hs = DK.ti_le_bar(dg, dd)
    print("he so bar do duoc: %.3f (%d -> %d bar tren TRAIN)"
          % (hs, len(dg), len(dd)), flush=True)

    ban = {"A_be_nguyen": [copy.deepcopy(c) for c in chan],
           "B_chi_chu_ky": [DK._doi_chu_ky_spec(c, hs) | {"ten": c["ten"]}
                            for c in chan],
           "C_bo_doi_moi": []}
    n_dat = n_nguong = 0
    for c in chan:
        r = DK.doi(c, MA_KHO, GOC, DICH, DAU, CAT, df_goc=dg, df_dich=dd)
        if r.get("loi"):
            ban["C_bo_doi_moi"].append(DK._doi_chu_ky_spec(c, hs) | {"ten": c["ten"]})
            continue
        ban["C_bo_doi_moi"].append(r["spec"] | {"ten": c["ten"]})
        n_dat += 1 if DK.dat(r) else 0
        n_nguong += 0 if r.get("khong_co_nguong") else 1
    print("bo doi moi: %d/%d co hang so nguong de chinh | %d/%d DAT ty le kich hoat"
          % (n_nguong, len(chan), n_dat, len(chan)), flush=True)

    ket = {}
    for nhan, spec in ban.items():
        tr = chay(spec, DICH, DAU, CAT, nhan + "_tr")
        ho = chay(spec, DICH, CAT, CUOI, nhan + "_ho")
        a = {r["ten"]: r for r in tr if r["lenh"] >= 25}
        b = {r["ten"]: r for r in ho if r["lenh"] >= 25}
        chung = set(a) & set(b)
        duong = [t for t in chung if a[t]["lai"] > 0 and b[t]["lai"] > 0]
        ket[nhan] = {"co_ca_hai": len(chung), "duong": len(duong),
                     "lai_ho": round(sum(b[t]["lai"] for t in duong), 2)}
        print("  %-14s: >=25 lenh ca hai %3d | DUONG ca hai %3d | lai holdout %9.2f"
              % (nhan, len(chung), len(duong), ket[nhan]["lai_ho"]), flush=True)
    DG.ghi("THU_DOI_KHUNG_%s_%s.json" % (MA, DICH),
           {"ma": MA, "goc": GOC, "dich": DICH, "hs": round(hs, 3), "ket": ket})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
