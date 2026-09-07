# -*- coding: utf-8 -*-
"""_ghep_he.py - GHEP HE MUA VOI HE BAN, DO TRONG CUNG MOT EA.

Chu du an, cuoi phien 06/09/2026: *"He thong ban hay day, co chieu ban rat hop
li de can bang cho cac he thong khac. Mai ta se thu ca su ket hop he thong."*

Boi canh: gan nhu MOI he da qua cong cua du an deu chieu MUA. Neu tat ca cung
mua thi danh muc chi la mot cuoc dat cuoc don vao drift di len va sut giam cong
don. `quantora_ma_dashboard_sell` la he DAU TIEN qua cong ma chieu -1.

## HAI CHANG, MOT BO THUC THI

**Chang 1 - HINH DANG.** Mot lan chay don, ca ba slot bat o lot 0,10, EA ghi
duong von CUA TUNG SLOT theo tung nen ra CSV. Tu do do:
  - tuong quan CHUOI VON (khong phai tuong quan tin hieu), tren bar cua CHINH
    cong cu se giao dich [[tang2-mt5-result]] - tuong quan tren bar Yahoo va
    bar CFD lech nhau rat xa (0,17 vs 0,58);
  - phoi nhiem cong don: hai he co bao gio cung mo mot luc khong;
  - sut giam cua tong so voi tong cua hai sut giam rieng.

**Chang 2 - CONG RA TIEN.** Mot luot optimization tren luoi `lot0 x lot1 x
lot2`. Pass co `lot = 0` chinh la "he kia chay mot minh" di qua dung bo thuc
thi do, nen ba duong so sanh (z5 mot minh · quantora mot minh · mua-giu) va
duong ghep deu ra tu MOT lan boot. So o **CUNG SUT GIAM**
[[cong-ra-tien-la-cong-thu-hai]], khong phai o cung bien dong va khong phai chi
vi tong lai cao hon.

## CANH BAO TU CHINH DU AN

[[ghep-v6-va-session-vang]]: ghep hai he tuong quan +0,03 cho Calmar 0,75, la
cau hinh dau tien vuot mua-giu vang. Nhung [[v6-doi-chieu-dung-cach]]: them
chan thu tu lam XAU DI. **Ghep khong tu dong tot** - phai do.

Chay: python _ghep_he.py [SYMBOL] [tu] [den]
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chay_tester_kho as C            # noqa: E402
from nhan import dich_mq5_ghep as G    # noqa: E402
from nhan import ngu_phap as NP        # noqa: E402

LAB = Path(__file__).resolve().parent
TEN_EA = "GhepHe"
CHUNG = Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal" / "Common" / "Files"

VON = 10000
#: Slot 0 la MOC (mua-giu) - phai nam trong CUNG EA de di qua cung spread, cung
#: phi qua dem, cung gio khop [[v6-doi-chieu-dung-cach]].
HE = ["mean_reversion_z5", "quantora_ma_dashboard_sell"]
#: Bien lot theo TUNG SLOT. Luot dau (lot 0..2,0 cho ca ba) cho cau hinh ghep
#: tot nhat nam dung o GOC luoi 2,0/2,0 - tuc luoi dang chan, chua cham tran
#: that. Moc mua-giu thi nguoc lai: lot 2,0 da cho sut giam 99,7%, noi them chi
#: ra them cau hinh chay tai khoan. Nen moi slot mot bien.
LOT_BIEN = [(2.0, 0.1), (4.0, 0.2), (4.0, 0.2)]


# --------------------------------------------------------------------- sinh EA
def sinh(khung: str = "D1") -> list[dict]:
    kho = {c["ten"]: c for c in NP.doc_kho()}
    thieu = [t for t in HE if t not in kho]
    if thieu:
        raise SystemExit("khong co trong kho: %s" % thieu)
    specs = [dict(G.SPEC_MUA_GIU)] + [kho[t] for t in HE]
    ma, dat = G.sinh_ea_ghep(specs, TEN_EA, khung=khung)
    src = C.XM_DATA / "MQL5" / "Experts" / (TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        raise SystemExit("bien dich: " + loi)
    print("EA %d slot: %s" % (len(dat), " | ".join(c["ten"] for c in dat)))
    return dat


def _chay_terminal(ini: Path, tran: int = 2400) -> float:
    C.dong_terminal()
    t0 = time.time()
    subprocess.Popen([str(C.XM_EXE), "/config:%s" % ini])
    while time.time() - t0 < tran:
        time.sleep(6)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                           capture_output=True, text=True)
        if "terminal64.exe" not in r.stdout:
            break
    else:
        C.dong_terminal()
    return round(time.time() - t0, 1)


# ----------------------------------------------------------- chang 1: hinh dang
def chay_duong_von(symbol: str, tu: str, den: str, n_slot: int) -> Path:
    ten = "ghep_von_%s" % symbol
    tep = "GHEP_VON_%s.csv" % symbol
    (C.XM_DATA / "MQL5" / "Profiles" / "Tester").mkdir(parents=True, exist_ok=True)
    dat_set = "".join("InpLot%d=0.10||0.10||0||0||N\n" % i for i in range(n_slot))
    (C.XM_DATA / "MQL5" / "Profiles" / "Tester" / (ten + ".set")).write_text(
        dat_set + "InpMagic=26090701||26090701||0||0||N\n"
        "InpGhi=1||1||0||0||N\n"
        # Tham so KIEU CHUOI trong .set khong co phan `||start||step||stop||`;
        # them vao thi MT5 doc ca chuoi do lam TEN TEP.
        "InpTep=%s\n" % tep, encoding="utf-8")
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

    ra = CHUNG / tep
    if ra.exists():
        ra.unlink()
    giay = _chay_terminal(C.XM_DATA / (ten + ".ini"))
    print("  duong von: %ss" % giay)
    hong = C.kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        raise SystemExit(hong)
    if not ra.exists():
        raise SystemExit("EA khong ghi duoc %s - kiem FILE_COMMON" % ra)
    return ra


def doc_csv(f: Path) -> tuple[list, list[list[float]], list[list[int]], list[float]]:
    van = ""
    for bo_ma in ("utf-16", "utf-8"):
        try:
            van = f.read_text(encoding=bo_ma)
        except (UnicodeDecodeError, UnicodeError):
            continue
        if "thoi_gian" in van:
            break
    dong = [d for d in van.splitlines() if d.strip()]
    dau = dong[0].split(",")
    n = sum(1 for c in dau if c.startswith("von"))
    tg, gia = [], []
    von = [[] for _ in range(n)]
    mo = [[] for _ in range(n)]
    for d in dong[1:]:
        o = d.split(",")
        if len(o) < 2 + 2 * n:
            continue
        tg.append(o[0])
        gia.append(float(o[1]))
        for i in range(n):
            von[i].append(float(o[2 + 2 * i]))
            mo[i].append(int(float(o[3 + 2 * i])))
    return tg, von, mo, gia


def _tuong_quan(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 3:
        return float("nan")
    ma_, mb = sum(a[:n]) / n, sum(b[:n]) / n
    sa = sum((x - ma_) ** 2 for x in a[:n])
    sb = sum((x - mb) ** 2 for x in b[:n])
    if sa <= 0 or sb <= 0:
        return float("nan")
    return sum((a[i] - ma_) * (b[i] - mb) for i in range(n)) / math.sqrt(sa * sb)


def _sut_giam(pnl: list[float]) -> float:
    """Sut giam % tren VON, tinh tren duong von = VON + lai luy ke."""
    dinh, xau = VON + (pnl[0] if pnl else 0.0), 0.0
    for p in pnl:
        v = VON + p
        dinh = max(dinh, v)
        if dinh > 0:
            xau = max(xau, (dinh - v) / dinh)
    return xau * 100


def hinh_dang(f: Path, ten_slot: list[str]) -> dict:
    tg, von, mo, gia = doc_csv(f)
    n = len(von)
    print("\n--- CHANG 1: hinh dang (%d nen, %s -> %s) ---"
          % (len(tg), tg[0] if tg else "?", tg[-1] if tg else "?"))
    dv = [[von[i][j] - von[i][j - 1] for j in range(1, len(von[i]))]
          for i in range(n)]
    ra = {"so_nen": len(tg), "tu": tg[0] if tg else "", "den": tg[-1] if tg else "",
          "slot": ten_slot, "cuoi": [round(v[-1], 2) for v in von],
          "sut_giam": [round(_sut_giam(v), 2) for v in von],
          "phoi_nhiem": [round(sum(m) / max(1, len(m)) * 100, 2) for m in mo]}
    print("%-30s %10s %9s %9s" % ("slot", "lai USD", "sutgiam", "phoinhiem"))
    for i in range(n):
        print("%-30s %10.2f %8.2f%% %8.2f%%"
              % (ten_slot[i][:30], ra["cuoi"][i], ra["sut_giam"][i],
                 ra["phoi_nhiem"][i]))

    # Hai he that (bo slot 0 = moc mua-giu)
    a, b = 1, 2
    ra["tuong_quan"] = round(_tuong_quan(dv[a], dv[b]), 4)
    cung = sum(1 for j in range(len(mo[a])) if mo[a][j] and mo[b][j])
    ra["cung_mo_pct"] = round(cung / max(1, len(mo[a])) * 100, 2)
    ra["cung_mo_neu_a_mo"] = round(cung / max(1, sum(mo[a])) * 100, 2)
    tong = [von[a][j] + von[b][j] for j in range(len(von[a]))]
    ra["tong"] = {"lai": round(tong[-1], 2), "sut_giam": round(_sut_giam(tong), 2)}
    ra["tong_hai_sut_giam"] = round(ra["sut_giam"][a] + ra["sut_giam"][b], 2)
    print("\ntuong quan CHUOI VON (%s vs %s) : %+.4f"
          % (ten_slot[a][:20], ten_slot[b][:20], ra["tuong_quan"]))
    print("cung mo mot luc                  : %.2f%% so nen "
          "(%.2f%% so nen ma %s dang mo)"
          % (ra["cung_mo_pct"], ra["cung_mo_neu_a_mo"], ten_slot[a][:20]))
    print("ghep 1:1  lai %.2f  sut giam %.2f%%   (cong hai sut giam rieng: %.2f%%)"
          % (ra["tong"]["lai"], ra["tong"]["sut_giam"], ra["tong_hai_sut_giam"]))
    return ra


# --------------------------------------------------------- chang 2: cong ra tien
def chay_luoi(symbol: str, tu: str, den: str, n_slot: int) -> Path:
    ten = "ghep_luoi_%s" % symbol
    dong = "".join("InpLot%d=0||0||%s||%s||Y\n"
                   % (i, LOT_BIEN[i][1], LOT_BIEN[i][0])
                   for i in range(n_slot))
    (C.XM_DATA / (ten + ".ini")).write_text("""[Tester]
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
%sInpMagic=26090701||26090701||0||0||N
InpGhi=0||0||0||0||N
""" % (TEN_EA, symbol, C.KHUNG_CHAY, tu, den, VON, ten, dong), encoding="utf-16")
    for h in (".xml", ".htm"):
        f = C.XM_DATA / (ten + h)
        if f.exists():
            f.unlink()
    so = [int(round(LOT_BIEN[i][0] / LOT_BIEN[i][1])) + 1 for i in range(n_slot)]
    tong = 1
    for x in so:
        tong *= x
    print("\n--- CHANG 2: luoi %s = %d pass ---"
          % (" x ".join(str(x) for x in so), tong))
    giay = _chay_terminal(C.XM_DATA / (ten + ".ini"), tran=3600)
    print("  %ss" % giay)
    hong = C.kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        raise SystemExit(hong)
    f = C.XM_DATA / (ten + ".xml")
    if not f.exists():
        raise SystemExit("khong thay bang ket qua %s" % f)
    return f


def _pct_nam(lai: float, nam: float) -> float:
    if nam <= 0 or VON + lai <= 0:
        return float("nan")
    return (((VON + lai) / VON) ** (1 / nam) - 1) * 100


def cong_ra_tien(f: Path, nam: float, ten_slot: list[str]) -> dict:
    n = len(ten_slot)
    hang = []
    for d in C.doc_xml(f):
        lot = [round(C._so(d.get("InpLot%d" % i, -1), -1), 2) for i in range(n)]
        if any(x < 0 for x in lot) or sum(lot) <= 0:
            continue
        lai = C._so(d.get("Profit"))
        hang.append({"lot": lot, "lenh": int(C._so(d.get("Trades"))),
                     "lai": lai, "dd": C._so(d.get("Equity DD %")),
                     "sharpe": C._so(d.get("Sharpe Ratio")),
                     "pct_nam": _pct_nam(lai, nam),
                     "chay": (VON + lai) <= 0})
    print("  %d pass co lenh" % len(hang))

    def duong(chon):
        return sorted([h for h in hang if chon(h["lot"])], key=lambda h: h["dd"])

    mg = duong(lambda l: l[0] > 0 and l[1] == 0 and l[2] == 0)
    a = duong(lambda l: l[0] == 0 and l[1] > 0 and l[2] == 0)
    b = duong(lambda l: l[0] == 0 and l[1] == 0 and l[2] > 0)
    gh = duong(lambda l: l[0] == 0 and l[1] > 0 and l[2] > 0)

    def tot_nhat(ds, dd_muc, bien=1.0):
        gan = [h for h in ds if abs(h["dd"] - dd_muc) <= bien and not h["chay"]]
        return max(gan, key=lambda h: h["pct_nam"]) if gan else None

    bang = {"mua-giu (moc)": mg, ten_slot[1]: a, ten_slot[2]: b, "ghep": gh}
    print("\n--- DINH cua tung duong (bo cau hinh chay tai khoan) ---")
    print("%-28s %13s %8s %7s %9s %8s"
          % ("duong", "lot", "sutgiam", "lenh", "%/nam", "sharpe"))
    for ten, ds in bang.items():
        t = [h for h in ds if not h["chay"]]
        if not t:
            continue
        h = max(t, key=lambda x: x["pct_nam"])
        print("%-28s %13s %7.2f%% %7d %8.2f%% %8.2f"
              % (ten[:28], "/".join("%.1f" % x for x in h["lot"]), h["dd"],
                 h["lenh"], h["pct_nam"], h["sharpe"]))
    #: So o CUNG SUT GIAM: voi moi muc sut giam cua moc mua-giu, tim cau hinh
    #: TOT NHAT cua tung duong o dung muc sut giam do.
    ket = []
    for h_mg in mg:
        if h_mg["chay"]:
            continue
        d = h_mg["dd"]
        r = {"dd_moc": round(d, 2), "lot_mg": h_mg["lot"][0],
             "mua_giu": round(h_mg["pct_nam"], 2)}
        for ten, ds in ((ten_slot[1], a), (ten_slot[2], b), ("ghep", gh)):
            t = tot_nhat(ds, d)
            r[ten] = round(t["pct_nam"], 2) if t else None
            r[ten + "__lot"] = t["lot"] if t else None
        ket.append(r)

    print("\n--- SO O CUNG SUT GIAM (moc = mua-giu trong cung EA) ---")
    print("%8s %10s %10s %10s %10s" % ("sutgiam", "mua-giu", ten_slot[1][:10],
                                       ten_slot[2][:10], "GHEP"))
    for r in ket:
        def v(k):
            x = r.get(k)
            return "%9.2f%%" % x if x is not None else "        --"
        print("%7.1f%% %9.2f%% %s %s %s"
              % (r["dd_moc"], r["mua_giu"], v(ten_slot[1]), v(ten_slot[2]),
                 v("ghep")))
    return {"nam": round(nam, 2), "so_pass": len(hang), "cung_sut_giam": ket,
            "dinh": {k: sorted(v, key=lambda h: -h["pct_nam"])[:5]
                     for k, v in bang.items()}}


def main() -> int:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
    tu = sys.argv[2] if len(sys.argv) > 2 else "2016.06.01"
    den = sys.argv[3] if len(sys.argv) > 3 else "2026.07.29"
    dat = sinh()
    ten_slot = [c["ten"] for c in dat]
    nam = (int(den[:4]) + int(den[5:7]) / 12.0) - (int(tu[:4]) + int(tu[5:7]) / 12.0)

    f = chay_duong_von(symbol, tu, den, len(dat))
    hd = hinh_dang(f, ten_slot)
    x = chay_luoi(symbol, tu, den, len(dat))
    ct = cong_ra_tien(x, nam, ten_slot)

    (LAB / "reports" / ("GHEP_%s.json" % symbol)).write_text(
        json.dumps({"symbol": symbol, "tu": tu, "den": den, "von": VON,
                    "slot": ten_slot, "hinh_dang": hd, "cong_ra_tien": ct},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> reports/GHEP_%s.json" % symbol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
