# -*- coding: utf-8 -*-
"""_dem_ghep.py - DAY CHUYEN TU CHAY: mo kho -> dao chan am -> ghep -> cong ra tien.

Chu du an, 07/09/2026: *"Ta se khoan lay them tu seeker, nhung voi kho da lay ve
toi de nghi cau loc lai 1 luot nua tim nut that de tang co che => tu co che thay
doi de tao thanh cac chan duong, ghep cac chan duong va am de tao ra co che tot
hon. Cho phep maxdd trong khoang 50-60% de toi uu loi nhuan."*

## VI SAO BAI NAY CO LY

Do duoc sang 07/09: ghep `mean_reversion_z5` (mua) voi `quantora_ma_dashboard_sell`
(ban) nang %/nam o CUNG sut giam tu 6,14% len 20,25% tren US100. Va trong 780 cap
cua 40 ung vien, **cap tot nhat (1.011 lai/DD) hon he don tot nhat (542,8) 1,86
lan**. Tuc duong ghep tra nhieu hon duong "tim them mot co che manh".

Nhung cung do duoc: tren GER40 tuong quan AM NHAT (-0,4429) ma ghep lai TE HON,
vi chan thu hai lo -443,64 USD. **Tuong quan am khong du - chan thu hai phai tu
no co ky vong duong.**

## BON CHANG

    A  MO KHO   ca 574 co che, MIEN cong `co_che` (cong do chan vi thieu MOT CAU
                van, khong phan biet duoc tot/xau) -> train + holdout tick that.
    B  DAO CHAN AM   co che AM o CA HAI doan -> sinh ban doi `chieu` -> chay lai.
                **BAY: dao chieu KHONG dao chi phi.** He lo dung bang spread thi
                dao van lo. Nen phai DO bang tester chu khong lat dau con so.
    C  GHEP     moi chan duong ghi duong von rieng (41 slot/lan chay, ~25 giay)
                -> ma tran tuong quan toan cuc -> xep hang cap theo lai/sut giam.
    D  RA TIEN  top cap -> quet luoi lot, muc tieu **sut giam 50-60%** theo yeu
                cau cua chu du an -> so voi mua-giu o CUNG sut giam.

Moi chang ghi JSON rieng, chang sau doc file cua chang truoc - hong chang nao
van con ket qua cua chang do.

Chay: python _dem_ghep.py [SYMBOL]
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _ghep_he as GH                  # noqa: E402
import chay_tester_kho as C            # noqa: E402
from nhan import dich_mq5 as D         # noqa: E402
from nhan import dich_mq5_ghep as G    # noqa: E402
from nhan import ngu_phap as NP        # noqa: E402

LAB = Path(__file__).resolve().parent
BC = LAB / "reports"
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
DAU, CAT, CUOI = "2016.06.01", "2021.06.01", "2026.07.29"
NAM = (2026 + 7 / 12) - (2016 + 6 / 12)
VON = GH.VON
SLOT_MOI_LAN = 40          # 41 slot chay het 24,5 giay - khong can nho hon
DD_MUC = (50.0, 60.0)      # cua so sut giam chu du an cho phep


def ghi(ten: str, d) -> None:
    (BC / ten).write_text(json.dumps(d, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    print("-> reports/%s" % ten, flush=True)


# =============================================================== chang A + B
def chay_kho(spec: list[dict], symbol: str, tu: str, den: str,
             ten_chay: str) -> list[dict]:
    """Nhu `chay_tester_kho.chay` nhung nhan spec TRUC TIEP (khong loc cong)."""
    ma, dat = D.sinh_ea(spec, C.TEN_EA, khung="D1")
    src = C.XM_DATA / "MQL5" / "Experts" / (C.TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        print("  bien dich LOI: %s" % loi, flush=True)
        return []
    ini = C.viet_ini(ten_chay, symbol, len(dat), tu, den)
    for h in (".xml", ".htm"):
        f = C.XM_DATA / (ten_chay + h)
        if f.exists():
            f.unlink()
    giay = GH._chay_terminal(ini, tran=3600)
    hong = C.kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        print("  %s" % hong, flush=True)
        return []
    f = C.XM_DATA / (ten_chay + ".xml")
    if not f.exists():
        print("  khong thay bang ket qua", flush=True)
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


def hai_doan(spec: list[dict], nhan: str) -> dict:
    ra = {}
    for ten, tu, den in (("train", DAU, CAT), ("holdout", CAT, CUOI)):
        print("=== %s %s  %s -> %s" % (nhan, ten, tu, den), flush=True)
        ra[ten] = chay_kho(spec, MA, tu, den, "%s_%s_%s" % (nhan, ten, MA))
    return ra


def loc(ra: dict, dau: int, lenh_min: int = 25) -> list[str]:
    """`dau` = +1 lay cai DUONG ca hai doan, -1 lay cai AM ca hai doan."""
    tr = {r["ten"]: r for r in ra.get("train", []) if r["lenh"] >= lenh_min}
    ho = {r["ten"]: r for r in ra.get("holdout", []) if r["lenh"] >= lenh_min}
    return [t for t in set(tr) & set(ho)
            if tr[t]["lai"] * dau > 0 and ho[t]["lai"] * dau > 0]


def chang_A_B() -> list[dict]:
    kho = []
    for c in NP.doc_kho():
        if NP.kiem_khai_bao(c):
            # Mien DUY NHAT cong `co_che`: no chan vi thieu mot cau van, khong
            # phan biet duoc tot/xau. Cai gi hong THAT (spec loi, dieu kien hien
            # nhien) van bi chan vi vong kiem thu hai duoi day.
            c2 = dict(c, co_che="MIEN CONG DE DO - chua co ly do kinh te.")
            if NP.kiem_khai_bao(c2):
                continue
            c = c2
        kho.append(c)
    print("\n########## CHANG A: mo kho = %d co che\n" % len(kho), flush=True)
    A = hai_doan(kho, "moKho")
    ghi("DEM_A_MO_KHO_%s.json" % MA, A)
    duong = loc(A, +1)
    am = loc(A, -1)
    print("\nchan DUONG ca hai doan : %d" % len(duong), flush=True)
    print("chan AM   ca hai doan : %d" % len(am), flush=True)

    print("\n########## CHANG B: dao chieu %d chan am\n" % len(am), flush=True)
    theo_ten = {c["ten"]: c for c in kho}
    dao = []
    for t in am:
        c = theo_ten.get(t)
        if c is None:
            continue
        d = dict(c)
        d["ten"] = t + "__dao"
        d["chieu"] = -int(c.get("chieu", 1) or 1)
        # Dao chieu KHONG dao chi phi: he lo dung bang spread + phi qua dem thi
        # ban dao van lo. Nen o day chi SINH ban doi, con phan xu la cua tester.
        d["co_che"] = "BAN DAO CHIEU cua %s - chua co ly do kinh te." % t
        dao.append(d)
    B = hai_doan(dao, "dao") if dao else {}
    if B:
        ghi("DEM_B_DAO_%s.json" % MA, B)
    dao_duong = loc(B, +1) if B else []
    print("\ndao chieu -> duong ca hai doan: %d/%d" % (len(dao_duong), len(dao)),
          flush=True)

    chan = [theo_ten[t] for t in duong if t in theo_ten]
    theo_dao = {c["ten"]: c for c in dao}
    chan += [theo_dao[t] for t in dao_duong if t in theo_dao]
    print("\nTONG CHAN DUONG: %d (goc %d + dao %d)"
          % (len(chan), len(duong), len(dao_duong)), flush=True)
    ghi("DEM_CHAN_DUONG_%s.json" % MA,
        {"goc": duong, "dao": dao_duong, "so": len(chan)})
    return chan


# ==================================================================== chang C
def duong_von(spec: list[dict], lo: int) -> tuple[list, dict]:
    """Chay MOT lo slot, tra (moc thoi gian, {ten: chuoi lai luy ke})."""
    ten_ea = "LoGhep%d" % lo
    ma, dat = G.sinh_ea_ghep([dict(G.SPEC_MUA_GIU)] + spec, ten_ea, khung="D1",
                             magic=26090900 + lo * 100,
                             tep="LO%d_%s.csv" % (lo, MA))
    src = C.XM_DATA / "MQL5" / "Experts" / (ten_ea + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        print("  bien dich LOI: %s" % loi, flush=True)
        return [], {}
    nc = "lo%d_%s" % (lo, MA)
    (C.XM_DATA / "MQL5" / "Profiles" / "Tester").mkdir(parents=True, exist_ok=True)
    (C.XM_DATA / "MQL5" / "Profiles" / "Tester" / (nc + ".set")).write_text(
        "".join("InpLot%d=0.10||0.10||0||0||N\n" % i for i in range(len(dat)))
        + "InpMagic=%d||%d||0||0||N\nInpGhi=1||1||0||0||N\n"
        % (26090900 + lo * 100, 26090900 + lo * 100)
        + "InpTep=LO%d_%s.csv\n" % (lo, MA), encoding="utf-8")
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
""" % (ten_ea, nc, MA, C.KHUNG_CHAY, DAU, CUOI, VON, nc), encoding="utf-16")
    f = GH.CHUNG / ("LO%d_%s.csv" % (lo, MA))
    if f.exists():
        f.unlink()
    GH._chay_terminal(C.XM_DATA / (nc + ".ini"), tran=3600)
    if not f.exists():
        print("  lo %d khong ghi duoc CSV" % lo, flush=True)
        return [], {}
    tg, von, mo, gia = GH.doc_csv(f)
    return tg, {dat[i]["ten"]: von[i] for i in range(1, len(dat))
                if i < len(von)}


def chang_C(chan: list[dict]) -> list[dict]:
    print("\n########## CHANG C: ma tran tuong quan %d chan\n" % len(chan),
          flush=True)
    goc, tat = [], {}
    for lo in range((len(chan) + SLOT_MOI_LAN - 1) // SLOT_MOI_LAN):
        phan = chan[lo * SLOT_MOI_LAN:(lo + 1) * SLOT_MOI_LAN]
        print("=== lo %d: %d slot" % (lo, len(phan)), flush=True)
        tg, d = duong_von(phan, lo)
        if not goc and tg:
            goc = tg
        # Cac lo chay CUNG symbol / cung cua so / cung chi phi nen moc nen trung
        # nhau; chi giu chuoi du do dai de khong so lech nen.
        for k, v in d.items():
            if len(v) == len(goc):
                tat[k] = v
    print("\nghep duoc %d chuoi von" % len(tat), flush=True)
    if len(tat) < 2:
        return []
    ten = sorted(tat)
    dv = {t: [tat[t][j] - tat[t][j - 1] for j in range(1, len(tat[t]))]
          for t in ten}
    lai = {t: tat[t][-1] for t in ten}
    dd = {t: GH._sut_giam(tat[t]) for t in ten}
    cap = []
    for x in range(len(ten)):
        for y in range(x + 1, len(ten)):
            a, b = ten[x], ten[y]
            if lai[a] <= 0 or lai[b] <= 0:
                continue        # bai hoc GER40: chan lo thi ghep khong cuu duoc
            t = [tat[a][k] + tat[b][k] for k in range(len(tat[a]))]
            d = GH._sut_giam(t)
            if d <= 0:
                continue
            cap.append({"a": a, "b": b,
                        "r": round(GH._tuong_quan(dv[a], dv[b]), 4),
                        "lai": round(t[-1], 2), "dd": round(d, 3),
                        "loi_tren_dd": round(t[-1] / d, 1)})
    cap.sort(key=lambda c: -c["loi_tren_dd"])
    don = sorted(({"ten": t, "lai": round(lai[t], 2), "dd": round(dd[t], 3),
                   "loi_tren_dd": round(lai[t] / dd[t], 1) if dd[t] > 0 else 0}
                  for t in ten if lai[t] > 0),
                 key=lambda d: -d["loi_tren_dd"])
    ghi("DEM_C_MATRAN_%s.json" % MA,
        {"so_chan": len(ten), "don": don, "cap": cap[:200]})
    print("\n--- 10 he DON tot nhat ---", flush=True)
    for d in don[:10]:
        print("%-46s %9.2f %7.2f%% %8.1f"
              % (d["ten"][:46], d["lai"], d["dd"], d["loi_tren_dd"]), flush=True)
    print("\n--- 15 CAP tot nhat ---", flush=True)
    for c in cap[:15]:
        print("%-30s %-30s %+7.3f %9.2f %7.2f%% %8.1f"
              % (c["a"][:30], c["b"][:30], c["r"], c["lai"], c["dd"],
                 c["loi_tren_dd"]), flush=True)
    return cap


# ==================================================================== chang D
def chang_D(cap: list[dict], chan: list[dict], so_cap: int = 6) -> None:
    print("\n########## CHANG D: cong ra tien o sut giam %.0f-%.0f%%\n"
          % DD_MUC, flush=True)
    theo_ten = {c["ten"]: c for c in chan}
    ket = []
    for k, c in enumerate(cap[:so_cap]):
        a, b = theo_ten.get(c["a"]), theo_ten.get(c["b"])
        if a is None or b is None:
            continue
        print("=== cap %d: %s + %s" % (k, c["a"][:34], c["b"][:34]), flush=True)
        ma, dat = G.sinh_ea_ghep([dict(G.SPEC_MUA_GIU), a, b], "CapRaTien",
                                 khung="D1", magic=26091000)
        src = C.XM_DATA / "MQL5" / "Experts" / "CapRaTien.mq5"
        src.write_text(ma, encoding="utf-8")
        if C.bien_dich(src):
            continue
        nc = "captien%d_%s" % (k, MA)
        (C.XM_DATA / (nc + ".ini")).write_text("""[Tester]
Expert=CapRaTien.ex5
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
InpLot0=0||0||0.1||2.0||Y
InpLot1=0||0||0.8||16.0||Y
InpLot2=0||0||0.8||16.0||Y
InpMagic=26091000||26091000||0||0||N
InpGhi=0||0||0||0||N
""" % (MA, C.KHUNG_CHAY, DAU, CUOI, VON, nc), encoding="utf-16")
        for h in (".xml", ".htm"):
            f = C.XM_DATA / (nc + h)
            if f.exists():
                f.unlink()
        GH._chay_terminal(C.XM_DATA / (nc + ".ini"), tran=3600)
        f = C.XM_DATA / (nc + ".xml")
        if not f.exists():
            print("  khong ra bang", flush=True)
            continue
        hang = []
        for d in C.doc_xml(f):
            lot = [round(C._so(d.get("InpLot%d" % i, -1), -1), 2)
                   for i in range(3)]
            if any(x < 0 for x in lot):
                continue
            l_ = C._so(d.get("Profit"))
            if VON + l_ <= 0:
                continue        # chay tai khoan: luy thua phan so cua so am
            hang.append({"lot": lot, "lenh": int(C._so(d.get("Trades"))),
                         "lai": l_, "dd": C._so(d.get("Equity DD %")),
                         "sharpe": C._so(d.get("Sharpe Ratio")),
                         "pct_nam": (((VON + l_) / VON) ** (1 / NAM) - 1) * 100})

        # Do 07/09 tren cap 0: dai sut giam 50-60% cua chu du an **KHONG** mua
        # them duoc loi nhuan - dinh cua duong ghep nam o DD ~19-20% (30,45%/nam)
        # con o DD 51% chi con 16,59%. Vi qua diem can bang, muon day sut giam
        # len cao thi luoi buoc phai lech han ve mot chan (0,8/8,0), va chan lech
        # thi kem. Nen o day bao CA DUONG BIEN chu khong chi mot dai: dinh · muc
        # 20% · dai 50-60% neu voi toi.
        def gom(loc_lot):
            g = [h for h in hang if loc_lot(h["lot"])]
            if not g:
                return None
            def o(dd_lo, dd_hi):
                x = [h for h in g if dd_lo <= h["dd"] <= dd_hi]
                return max(x, key=lambda h: h["pct_nam"]) if x else None
            def gon(h):
                return ({"lot": h["lot"], "dd": round(h["dd"], 2),
                         "lenh": h["lenh"], "pct_nam": round(h["pct_nam"], 2),
                         "sharpe": h["sharpe"]} if h else None)
            return {"dinh": gon(max(g, key=lambda h: h["pct_nam"])),
                    "dd20": gon(o(17.5, 22.5)),
                    "dd_chu_du_an": gon(o(DD_MUC[0], DD_MUC[1])),
                    "dd_max_do_duoc": round(max(h["dd"] for h in g), 2)}

        r = {"a": c["a"], "b": c["b"], "r": c["r"],
             "ghep": gom(lambda l: l[0] == 0 and l[1] > 0 and l[2] > 0),
             "chi_a": gom(lambda l: l[0] == 0 and l[1] > 0 and l[2] == 0),
             "chi_b": gom(lambda l: l[0] == 0 and l[1] == 0 and l[2] > 0),
             "mua_giu": gom(lambda l: l[0] > 0 and l[1] == 0 and l[2] == 0)}
        ket.append(r)

        def s(x):
            return ("%6.2f%%/nam @ DD %5.2f%%  lot %s"
                    % (x["pct_nam"], x["dd"],
                       "/".join("%.1f" % v for v in x["lot"]))) if x else "  --"
        for nhan in ("ghep", "chi_a", "chi_b", "mua_giu"):
            g = r[nhan]
            if not g:
                print("   %-8s --" % nhan, flush=True)
                continue
            print("   %-8s dinh %s | DD20 %s | %.0f-%.0f%% %s"
                  % (nhan, s(g["dinh"]), s(g["dd20"]), DD_MUC[0], DD_MUC[1],
                     s(g["dd_chu_du_an"])), flush=True)
        ghi("DEM_D_RA_TIEN_%s.json" % MA, ket)


def main() -> int:
    t0 = time.time()
    chan = chang_A_B()
    if len(chan) < 2:
        print("khong du chan duong de ghep", flush=True)
        return 1
    cap = chang_C(chan)
    if cap:
        chang_D(cap, chan)
    print("\nXONG sau %.1f phut" % ((time.time() - t0) / 60), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
