# -*- coding: utf-8 -*-
"""_da_khung.py - CUNG MOT CHAN, BON KHUNG: W1 / D1 / H4 / H1.

Chu du an 07/09/2026: *"Cau dang dung D1 a, neu he thong tot nhu vay thi co the
them entry tuan va thang hay do xuong h4 h1 va khung nho hon xem. Tat nhien cac
khung thap thi he so de tinh entry can phai nang them."*

Ca hai ve deu dung, va ve thu hai la cho de sai nhat.

## QUY DOI THAM SO KHI DOI KHUNG

`nhan/quy_doi_tham_so.py` quy doi giua TAI SAN theo ATR. Doi KHUNG thi nguyen
tac khac:

  - **Tham so CHU KY (`n` cua sma/ema/rsi/zscore/atr..., va `giu`)** do bang SO
    BAR, nen phai **nhan theo ty le bar**: D1 -> H4 la x6, D1 -> H1 la x24,
    D1 -> W1 la /5. `zscore 5 nen` tren D1 la mot tuan; tren H1 la nam gio -
    hai thu khac han.
  - **Nguong PHI THU NGUYEN (`hang`: z-score -1,0 · RSI 30 · ty le)** giu
    NGUYEN. Nhan chung len la lam hong co che.

Neu bung nguyen tham so D1 xuong H1 thi ra dung mot trong hai ket cuc vo nghia
ma [[quy_doi_tham_so]] da ghi: khong lenh nao, hoac lenh day dac o muc nhieu.

## HAI RANG BUOC CO THAT

- **H1 chi co tu 2016** [[tester-h1-chi-co-tu-2016]] — nen moi khung deu chay
  dung cua so 2016.06..2026.07 de so sanh duoc voi nhau.
- **Spread D1 cao gap 2,7 lan** va **H4 giau nhat** [[quet-phai-mo-DA-KHUNG]] —
  do la tien nghiem noi rang bai nay dang nen chay.

EA chay tren H1 va lay tin hieu tu khung khai bao; rieng khung H1 thi hai cai
trung nhau (khong sao - `KhopYDinh` van giu y dinh cho toi khi phien mo).

Chay: python _da_khung.py [SYMBOL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bo_ba as BB                    # noqa: E402
import _dem_ghep as DG                 # noqa: E402
import _ghep_he as GH                  # noqa: E402
import chay_tester_kho as C            # noqa: E402
from nhan import dich_mq5_ghep as G    # noqa: E402

LAB = Path(__file__).resolve().parent
BC = LAB / "reports"
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"

#: (khung, so bar cua khung do trong MOT bar D1). D1 co ~24 bar H1 tren CFD chi
#: so (bar D1 om ~23 gio), W1 co 5 bar D1.
KHUNG = [("W1", 1 / 5), ("D1", 1.0), ("H4", 6.0), ("H1", 24.0)]
TOP_CHAN = 36


#: GIU LAI LAM MOC, khong dung nua. Do 07/09: ban nay chi nhan chu ky, va tren
#: 26 chan co hang so nguong thi **7 chan bi cam** (tut duoi 25 lenh) khi doi
#: D1 -> H4. Ban day du la `nhan/doi_khung.doi()` - no them buoc khop phan vi va
#: hieu chinh gop, ha so chan bi cam tu 7 xuong 1.
def doi_khung(nut, he_so: float):
    """Nhan MOI truong `n` va `giu` theo he_so; giu nguyen moi `hang`. CU."""
    if isinstance(nut, dict):
        ra = {}
        for k, v in nut.items():
            if k == "n" and isinstance(v, (int, float)):
                ra[k] = max(2, int(round(v * he_so)))
            elif k == "hang":
                ra[k] = v            # nguong phi thu nguyen - KHONG dung vao
            else:
                ra[k] = doi_khung(v, he_so)
        return ra
    if isinstance(nut, list):
        return [doi_khung(x, he_so) for x in nut]
    return nut


def spec_khung(chan: list[dict], he_so: float, khung: str = "",
               ma_kho: str = "") -> list[dict]:
    """Doi ca danh sach sang khung khac.

    Dung `nhan/doi_khung.doi()` (chu ky + khop phan vi + hieu chinh gop) khi co
    du du lieu; thieu du lieu thi roi ve ban chi-nhan-chu-ky va **noi ra** chu
    khong im lang [[ket-luan-am-phai-phan-biet-chua-do]].
    """
    from nhan import doi_khung as DK
    dg = dd = None
    if khung and ma_kho:
        dg = DK.nap_khung(ma_kho, "D1", DG.DAU, DG.CAT if hasattr(DG, "CAT")
                          else "2021.06.01")
        dd = DK.nap_khung(ma_kho, khung, DG.DAU, "2021.06.01")
    ra, roi_ve = [], 0
    for c in chan:
        if dg is not None and dd is not None:
            r = DK.doi(c, ma_kho, "D1", khung, df_goc=dg, df_dich=dd)
            if not r.get("loi"):
                d = dict(r["spec"])
                d["ten"] = c["ten"]
                ra.append(d)
                continue
        roi_ve += 1
        d = doi_khung(c, he_so)
        d["ten"] = c["ten"]
        d["giu"] = max(1, int(round(int(c.get("giu", 1) or 1) * he_so)))
        ra.append(d)
    if roi_ve:
        print("   (%d/%d chan roi ve ban chi-nhan-chu-ky vi thieu du lieu)"
              % (roi_ve, len(chan)), flush=True)
    return ra


def chay_khung(chan: list[dict], khung: str, he_so: float) -> dict:
    spec = spec_khung(chan, he_so, khung, "XM_" + MA.upper())
    goc, tat = [], {}
    for lo in range((len(spec) + DG.SLOT_MOI_LAN - 1) // DG.SLOT_MOI_LAN):
        phan = spec[lo * DG.SLOT_MOI_LAN:(lo + 1) * DG.SLOT_MOI_LAN]
        ten_ea = "Khung%s%d" % (khung, lo)
        ma, dat = G.sinh_ea_ghep([dict(G.SPEC_MUA_GIU)] + phan, ten_ea,
                                 khung=khung, magic=26091200 + lo * 100,
                                 tep="KHUNG_%s_%d_%s.csv" % (khung, lo, MA))
        src = C.XM_DATA / "MQL5" / "Experts" / (ten_ea + ".mq5")
        src.write_text(ma, encoding="utf-8")
        if C.bien_dich(src):
            print("   bien dich hong", flush=True)
            continue
        nc = "khung%s%d_%s" % (khung, lo, MA)
        (C.XM_DATA / "MQL5" / "Profiles" / "Tester").mkdir(parents=True,
                                                           exist_ok=True)
        (C.XM_DATA / "MQL5" / "Profiles" / "Tester" / (nc + ".set")).write_text(
            "".join("InpLot%d=0.10||0.10||0||0||N\n" % i for i in range(len(dat)))
            + "InpMagic=%d||%d||0||0||N\nInpGhi=1||1||0||0||N\n"
            % (26091200 + lo * 100, 26091200 + lo * 100)
            + "InpTep=KHUNG_%s_%d_%s.csv\n" % (khung, lo, MA), encoding="utf-8")
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
""" % (ten_ea, nc, MA, C.KHUNG_CHAY, DG.DAU, DG.CUOI, GH.VON, nc),
            encoding="utf-16")
        f = GH.CHUNG / ("KHUNG_%s_%d_%s.csv" % (khung, lo, MA))
        if f.exists():
            f.unlink()
        GH._chay_terminal(C.XM_DATA / (nc + ".ini"), tran=3600)
        if not f.exists():
            print("   lo %d khong ghi CSV" % lo, flush=True)
            continue
        tg, von, mo, gia = GH.doc_csv(f)
        if not goc:
            goc = tg
        for i in range(1, len(dat)):
            if i < len(von) and len(von[i]) == len(goc):
                tat[dat[i]["ten"]] = von[i]
    return tat


def main() -> int:
    chan = BB.lay_chan()[:TOP_CHAN]
    print("%d chan, %d khung" % (len(chan), len(KHUNG)), flush=True)
    gop = {}
    for khung, hs in KHUNG:
        print("\n########## KHUNG %s (he so chu ky x%.2f)" % (khung, hs),
              flush=True)
        tat = chay_khung(chan, khung, hs)
        if not tat:
            print("   khong do duoc", flush=True)
            continue
        lai = {t: v[-1] for t, v in tat.items()}
        dd = {t: GH._sut_giam(v) for t, v in tat.items()}
        duong = [t for t in tat if lai[t] > 0]
        xh = sorted(duong, key=lambda t: -(lai[t] / dd[t] if dd[t] > 0 else 0))
        gop[khung] = {"so_chan": len(tat), "so_duong": len(duong),
                      "tong_lai": round(sum(lai.values()), 2),
                      "top": [{"ten": t, "lai": round(lai[t], 2),
                               "dd": round(dd[t], 3),
                               "loi_tren_dd": round(lai[t] / dd[t], 1)
                               if dd[t] > 0 else 0} for t in xh[:10]]}
        print("   chan duong %d/%d | tong lai %.2f"
              % (len(duong), len(tat), sum(lai.values())), flush=True)
        for x in gop[khung]["top"][:6]:
            print("   %-44s %9.2f %6.2f%% %8.1f"
                  % (x["ten"][:44], x["lai"], x["dd"], x["loi_tren_dd"]),
                  flush=True)
    DG.ghi("DA_KHUNG_%s.json" % MA, gop)
    print("\n%-6s %8s %10s %12s %10s" % ("khung", "duong", "tong lai",
                                         "chan tot nhat", "loi/DD"))
    for k, v in gop.items():
        t = v["top"][0] if v["top"] else None
        print("%-6s %4d/%-4d %10.2f %12s %10.1f"
              % (k, v["so_duong"], v["so_chan"], v["tong_lai"],
                 (t["ten"][:12] if t else "--"), (t["loi_tren_dd"] if t else 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
