# -*- coding: utf-8 -*-
"""chay_tester_z5.py - DUA HE DA PASS RA TICK THAT.

## VI SAO FILE NAY TON TAI

So cai co **2 gia thuyet trang thai PASS** (373 FAIL, 7 cach ly). Ca hai chua
bao gio duoc chay trong MT5 Strategy Tester:

    XM_US100CASH.D1.mean_reversion_z5   plan_hash 55d17325924c27b5  (05/09)
    AUDCAD.H4.rsi_dao_chieu.n14         plan_hash 8ba0abc8b3cdf723  (15/08)

Lan chay tester gan nhat cua ca du an la **01/09** - nam ngay truoc. Trong nam
ngay do The Brain chay thuan Python va ba lan ket luan "nut that la MDE". Nhung
quy tac cua chu du an la **MT5 tester TRUOC, Python SAU**
[[mt5-tester-truoc-python-sau]], va da co tien le tester **lat nguoc** ket luan
Python: EURCAD cho gia lui nang 7,9% -> 12,1%/nam trong khi Python bao "entry vo
dung" [[eurcad-entry-cho-lui]].

## CAI FILE NAY DO, VA CAI NO KHONG DO

DO: so lenh, lai tho moi lenh, va chenh lech giua Python va tick that. Do la
phep doi chieu duy nhat co nghia o buoc nay.

KHONG DO: lai %/nam theo lot. `mo_phong.chay` cua Python tinh tren chuoi loi
suat voi phoi nhiem 0/1 (khong lai kep theo lot), nen so sanh %/nam giua hai ben
la so sanh hai thu khac nhau. Lot o day CO DINH de con so /lenh doc duoc
[[cong-ra-tien-la-cong-thu-hai]].

## BA BAY DA SAP THAT, DEU DA BIT O DAY

- `Report=` duong TUYET DOI bi MT5 lo di khong bao loi -> phai TUONG DOI, va
  file ra nam trong thu muc DU LIEU cua terminal [[mt5-tester-dong-lenh]].
- `terminal64.exe /config:` KHONG chan -> phai poll tien trinh, khong duoc doc
  bao cao ngay.
- MT5 khong cho hai tien trinh dung chung mot thu muc du lieu -> phai dong
  terminal truoc.
- Bao cao .htm tieng Viet goi **Gross Profit** la "Loi nhuan rong"; lai THAT la
  "**Tong** loi nhuan rong". Doc nham lech 13,5 lan.
- `Model=1` noi doi khi TP/SL nho hon bien do nen M1 [[model1-che-ra-lai-gia]].
  He nay KHONG co TP/SL nen bay khong dinh, nhung van chay CA HAI model de
  chung minh dieu do chu khong suy dien.

Chay: python chay_tester_z5.py [--model 1,0] [--tu 2011.09.19] [--den 2026.07.29]
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent

XM_EXE = Path(r"C:\Program Files\XM MT5\terminal64.exe")
XM_DATA = (Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal"
           / "656C351524AFFE300FAFE576FA4C7845")

EA = "MeanRevZ5.ex5"
SYMBOL = "US100Cash"
#: Chay EA tren H1, tin hieu lay tu D1. Xem ghi chu trong MeanRevZ5.mq5: nen D1
#: mo luc 00:00 nam NGOAI phien cua CFD, nen Model=2 tren khung D1 cho 463 lenh
#: "Market closed" va bao cao ghi 0 lenh.
PERIOD = "H1"

#: Lot CO DINH. Xem docstring: bai nay do SO LENH va LAI/LENH, khong do %/nam.
LOT = 0.10
DEPOSIT = 10000
DON_BAY = 500


def viet_ini(ten: str, model: int, tu: str, den: str) -> Path:
    """Ghi .ini vao thu muc DU LIEU. `Report` phai TUONG DOI - xem docstring."""
    noi_dung = f"""[Tester]
Expert=MeanRevZ5.ex5
ExpertParameters={ten}.set
Symbol={SYMBOL}
Period={PERIOD}
Model={model}
ExecutionMode=0
Optimization=0
FromDate={tu}
ToDate={den}
ForwardMode=0
Deposit={DEPOSIT}
Currency=USD
Leverage=1:{DON_BAY}
ProfitInPips=0
Report={ten}
ReplaceReport=1
ShutdownTerminal=1
"""
    p = XM_DATA / f"{ten}.ini"
    p.write_text(noi_dung, encoding="utf-16")
    return p


def viet_set(ten: str, n: int = 5, nguong: float = -1.0) -> None:
    (XM_DATA / "MQL5" / "Profiles" / "Tester").mkdir(parents=True, exist_ok=True)
    (XM_DATA / "MQL5" / "Profiles" / "Tester" / f"{ten}.set").write_text(
        "InpN=%d||5||1||10||N\n"
        "InpNguongVao=%s||-1.0||0.0||0.0||N\n"
        "InpNguongRa=%s||-1.0||0.0||0.0||N\n"
        "InpGiuToiDa=500||500||1||1000||N\n"
        "InpLot=%s||0.1||0.0||0.0||N\n"
        "InpMagic=20260906||20260906||0||0||N\n"
        % (n, nguong, nguong, LOT), encoding="utf-8")


def dong_terminal() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "terminal64.exe"],
                   capture_output=True)
    time.sleep(2)


def chay_mot(ten: str, model: int, tu: str, den: str, tran_giay: int = 900) -> dict:
    viet_set(ten)
    ini = viet_ini(ten, model, tu, den)
    bao_cao = XM_DATA / f"{ten}.htm"
    for f in (bao_cao, XM_DATA / f"{ten}.html"):
        if f.exists():
            f.unlink()

    dong_terminal()
    print(f"  chay Model={model} ...", flush=True)
    t0 = time.time()
    subprocess.Popen([str(XM_EXE), f"/config:{ini}"])
    # `/config:` KHONG chan - phai poll. Xem docstring.
    while time.time() - t0 < tran_giay:
        time.sleep(5)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                           capture_output=True, text=True)
        if "terminal64.exe" not in r.stdout:
            break
    else:
        dong_terminal()
        return {"ten": ten, "model": model, "loi": "qua %ds" % tran_giay}
    giay = round(time.time() - t0, 1)

    hong = kiem_log_agent()
    f = next((x for x in (bao_cao, XM_DATA / f"{ten}.html") if x.exists()), None)
    if f is None:
        return {"ten": ten, "model": model, "giay": giay,
                "chua_do": True, "loi": hong or "khong thay bao cao"}
    r = {**doc_bao_cao(f), "ten": ten, "model": model, "giay": giay}
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        # KHONG DUOC bao "0 lenh" khi tester chua chay duoc. Xem `kiem_log_agent`.
        r["chua_do"] = True
        r["loi"] = hong
    elif hong:
        r["ghi_chu"] = hong
    return r


#: Thu muc log cua AGENT - khac log cua Tester, va chi o day moi co ly do that.
LOG_AGENT = (Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Tester"
             / "656C351524AFFE300FAFE576FA4C7845"
             / "Agent-127.0.0.1-3000" / "logs")

#: Dau hieu tester KHONG CHAY DUOC - phai phan biet voi "chay duoc, 0 lenh".
#:
#: Do that 06/09/2026: Model=1 tren 15 nam D1 phai SINH tick M1, ngon 20.480 MB
#: cache roi chet voi "cannot generate history data, check disk space" (dia con
#: 12 GB). Bao cao .htm van duoc ghi, va no ghi **0 lenh, PF 0.00, DD 0.00** -
#: doc y het mot he khong bao gio vao lenh. Neu tin con so do thi ket luan se la
#: "he da PASS khong giao dich tren tick that", tuc nguoc hoan toan su that.
#: [[ket-luan-am-phai-phan-biet-chua-do]]
DAU_HIEU_HONG = ("cannot generate history data", "0 ticks, 0 bars generated",
                 "not enough memory", "no history data")


def kiem_log_agent() -> str:
    """Tra chuoi ly do neu tester KHONG CHAY DUOC; rong neu chay that."""
    try:
        fs = sorted(LOG_AGENT.glob("*.log"), key=lambda p: p.stat().st_mtime)
        if not fs:
            return ""
        van = fs[-1].read_text(encoding="utf-16", errors="ignore")
        if "Tester" not in van:
            van = fs[-1].read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    # CHI DOC PHAN CUA LUOT NAY. Agent ghi noi tiep vao cung mot file theo NGAY,
    # nen mot loi cua luot truoc se lam moi luot sau bi bao hong - va ta se di
    # sua mot thu khong hong. Cat tu lan "MetaTester 5 started" cuoi cung.
    i = van.rfind("MetaTester 5 started")
    if i > 0:
        van = van[i:]
    for d in DAU_HIEU_HONG:
        if d in van:
            return "TESTER KHONG CHAY DUOC: " + d
    # "Market closed" o day KHONG phai lenh bi mat. EA giu Y DINH roi thu lai o
    # moi nen H1 cho toi khi phien mo, nen mot y dinh co the that bai vai lan
    # truoc khi khop. Con so duoi la SO LAN THU, khong phai so lenh mat - goi
    # dung ten, neu khong lan sau se co nguoi di sua mot thu khong hong.
    tt = van.count("failed market buy") + van.count("failed market sell")
    if tt:
        return "ghi chu: %d lan thu lai truoc gio mo phien (khong mat lenh)" % tt
    return ""


#: Nhan trong bao cao .htm. Ban tieng Viet goi Gross Profit la "Loi nhuan rong"
#: va lai THAT la "Tong loi nhuan rong" - doc nham lech 13,5 lan.
NHAN = {
    "lai_rong": ("Total Net Profit", "Tổng lợi nhuận ròng"),
    "lai_tho": ("Gross Profit", "Lợi nhuận ròng"),
    "lo_tho": ("Gross Loss", "Lỗ ròng"),
    "so_lenh": ("Total Trades", "Tổng giao dịch"),
    "pf": ("Profit Factor", "Hệ số lợi nhuận"),
    "dd_pct": ("Equity Drawdown Maximal", "Sụt giảm vốn sở hữu tối đa"),
    "thang_pct": ("Profit Trades", "Giao dịch có lợi nhuận"),
    "sharpe": ("Sharpe Ratio", "Tỷ lệ Sharpe"),
}


def doc_bao_cao(f: Path) -> dict:
    tho = f.read_text(encoding="utf-16", errors="ignore")
    if "<" not in tho[:400]:
        tho = f.read_text(encoding="utf-8", errors="ignore")
    van = re.sub(r"<[^>]+>", "\t", tho)
    van = van.replace("&nbsp;", " ")
    ra: dict = {}
    for khoa, nhan in NHAN.items():
        for t in nhan:
            m = re.search(re.escape(t) + r"\s*:?\s*\t+\s*([\-\d\s,\.%\(\)]+)", van)
            if m:
                ra[khoa] = m.group(1).strip()[:40]
                break
    return ra


def main() -> int:
    # Model=2 "Open prices only" la mac dinh, va voi EA nay no khong phai xap xi
    # ma la NGU NGHIA DUNG: EA chi hanh dong khi co nen moi, doc chi so o shift 1,
    # khong co TP/SL nen khong co gi xay ra trong long nen. Model=1/0 phai SINH
    # tick M1 cho 15 nam va da chet vi het dia (xem DAU_HIEU_HONG).
    models = [2]
    if "--model" in sys.argv:
        models = [int(x) for x in sys.argv[sys.argv.index("--model") + 1].split(",")]
    tu = "2011.09.19"
    den = "2026.07.29"
    if "--tu" in sys.argv:
        tu = sys.argv[sys.argv.index("--tu") + 1]
    if "--den" in sys.argv:
        den = sys.argv[sys.argv.index("--den") + 1]

    if not (XM_DATA / "MQL5" / "Experts" / EA).exists():
        print("THIEU %s - bien dich truoc" % EA)
        return 1

    print("MeanRevZ5 tren %s %s, %s -> %s, lot %.2f, von %d"
          % (SYMBOL, PERIOD, tu, den, LOT, DEPOSIT))
    ket = []
    for m in models:
        r = chay_mot("z5_M%d" % m, m, tu, den)
        ket.append(r)
        print("   ", {k: v for k, v in r.items() if k != "ten"})

    import json
    (LAB / "reports" / "TESTER_Z5.json").write_text(
        json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> reports/TESTER_Z5.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
