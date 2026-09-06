# -*- coding: utf-8 -*-
"""chay_tester_kho.py - DUA CA KHO CO CHE RA MT5 TESTER.

Chu du an 06/09/2026: *"Python test rat hay sai, nen no dung de test tho cho
nhanh thoi."* Nen tester phai la trong tai, khong phai mot lan chay tay cho mot
co che.

## CACH LAM CHO NHANH

Do 06/09: mot luot tester ton **138 giay**, trong do bai test that chi **0,5
giay** - con lai la boot terminal + dong bo lich su. Chay tung co che mot thi
360 co che = 14 gio.

`dich_mq5.sinh_ea` gop tat ca vao MOT EA co `switch(InpMaCoChe)`, roi chay
**Optimization** tren dung tham so do. MT5 boot mot lan, dong bo lich su mot
lan, roi chay N pass. [[mt5-tester-dong-lenh]]: "optimization 20 pass = gia 1
pass".

## DOC KET QUA O DAU

Optimization ghi ra file **.xml** (khong phai .htm cua single run). Cot quan
trong: `Result`, `Profit`, `Trades`, `Profit Factor`, `Sharpe Ratio`,
`Equity DD %`. Moi dong la mot gia tri `InpMaCoChe`.

## KHONG DUOC TIN CON SO KHI TESTER CHUA CHAY DUOC

Ba cach hong da sap that, ca ba deu ghi bao cao binh thuong voi 0 lenh:
Model=1 het dia · nen khung tin hieu mo NGOAI phien · EA hanh dong dung luc
dong cua. `chay_tester_z5.kiem_log_agent` phan biet ba muc, va dung lai o day.

Chay:
    python chay_tester_kho.py --khung D1 --ma XM_US100CASH --so 60
    python chay_tester_kho.py --khung D1 --ma DE40 --loc vung
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chay_tester_z5 import (XM_DATA, XM_EXE, dong_terminal,   # noqa: E402
                            kiem_log_agent)
from nhan import dich_mq5 as D                                # noqa: E402
from nhan import ngu_phap as NP                               # noqa: E402

LAB = Path(__file__).resolve().parent
TEN_EA = "KhoCoChe"

#: Chay EA tren H1 con tin hieu lay tu khung khai bao. Nen khung tin hieu mo
#: luc 00:00 nam NGOAI phien cua CFD chi so; EA giu Y DINH roi khop o nen H1 dau
#: tien co the giao dich (xem MAU_EA.KhopYDinh).
KHUNG_CHAY = "H1"


MET_EDITOR = r"C:\Program Files\XM MT5\MetaEditor64.exe"


def bien_dich(duong: Path) -> str:
    """Tra chuoi loi, rong = dat.

    MetaEditor tra **exit code 1 ke ca khi bien dich thanh cong**, va no ghi
    log SAU khi thoat - nen phan xu bang exit code hoac doc log ngay lap tuc
    deu sai. O day phan xu bang hai thu do duoc: log co dong "Result: 0 errors"
    va file `.ex5` co MOI HON ban truoc khong. Thieu ve thu hai thi mot lan
    bien dich hong se lang le chay lai ban `.ex5` CU - va ta se doc ket qua cua
    mot EA khac voi cai minh vua sinh.
    """
    log = duong.with_suffix(".compile.log")
    ex5 = duong.with_suffix(".ex5")
    cu = ex5.stat().st_mtime if ex5.exists() else 0
    if log.exists():
        log.unlink()
    # KHONG dung `capture_output`: MetaEditor sinh mot tien trinh con roi thoat,
    # nen `subprocess.run` tra ve TRUOC khi bien dich xong. Do 06/09: goi tu
    # Python ra "khong co log", goi cung lenh do tu PowerShell `-Wait` thi ra
    # "0 errors" - khac biet la ai doi ai. Nen o day doi bang DAU HIEU: file
    # `.ex5` co dau thoi gian moi hon ban truoc.
    # DUONG TUONG DOI + `cwd`. Duong TUYET DOI co khoang trang (`...\SV STORE\
    # AppData\...`) thi MetaEditor khong bien dich va cung khong bao gi - dung
    # ho benh voi `Report=` tuyet doi bi tester lo di [[mt5-tester-dong-lenh]].
    subprocess.Popen([MET_EDITOR, "/compile:%s" % duong.name,
                      "/log:%s" % log.name],
                     cwd=str(duong.parent),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(120):
        time.sleep(1)
        if ex5.exists() and ex5.stat().st_mtime > cu and log.exists():
            time.sleep(1)
            break

    van = ""
    if log.exists():
        van = log.read_text(encoding="utf-16", errors="ignore")
        if "Result" not in van:
            van = log.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"Result: (\d+) errors", van)
    if m and int(m.group(1)) > 0:
        loi = [x for x in van.splitlines() if ": error" in x][:5]
        return "bien dich LOI: " + " | ".join(loi)
    if not ex5.exists():
        return "khong ra .ex5 | log: " + " ".join(van.split())[-200:]
    if ex5.stat().st_mtime <= cu:
        return "file .ex5 KHONG duoc ghi lai - ban cu con nam do"
    return ""


def viet_ini(ten: str, symbol: str, so_co_che: int, tu: str, den: str,
             deposit: int = 10000) -> Path:
    p = XM_DATA / f"{ten}.ini"
    p.write_text(f"""[Tester]
Expert={TEN_EA}.ex5
Symbol={symbol}
Period={KHUNG_CHAY}
Model=2
ExecutionMode=0
Optimization=2
OptimizationCriterion=0
FromDate={tu}
ToDate={den}
ForwardMode=0
Deposit={deposit}
Currency=USD
Leverage=1:500
ProfitInPips=0
Report={ten}
ReplaceReport=1
ShutdownTerminal=1

[TesterInputs]
InpMaCoChe=0||0||1||{so_co_che - 1}||Y
InpLot=0.10||0.10||0||0||N
InpMagic=26090601||26090601||0||0||N
""", encoding="utf-16")
    return p


def doc_xml(f: Path) -> list[dict]:
    """Bang toi uu hoa cua MT5 la SpreadsheetML - moi Row la mot pass."""
    # Bang toi uu hoa co the la UTF-8 KHONG BOM; `read_text(utf-16)` khi do NEM
    # `UnicodeDecodeError` chu khong tra chuoi rac, nen phai bat chu khong the
    # dua vao `errors="ignore"`.
    van = ""
    for bo_ma in ("utf-16", "utf-8", "cp1252"):
        try:
            van = f.read_text(encoding=bo_ma, errors="ignore")
        except (UnicodeDecodeError, UnicodeError):
            continue
        if "<Row" in van or "<tr" in van.lower():
            break
    hang = re.findall(r"<Row[^>]*>(.*?)</Row>", van, re.S)
    if not hang:
        return []
    def _o(h):
        return [re.sub(r"<[^>]+>", "", c).strip()
                for c in re.findall(r"<Cell[^>]*>(.*?)</Cell>", h, re.S)]
    dau = _o(hang[0])
    ra = []
    for h in hang[1:]:
        c = _o(h)
        if len(c) < 3:
            continue
        ra.append({k: v for k, v in zip(dau, c)})
    return ra


def _so(x, mac_dinh=0.0):
    try:
        return float(str(x).replace(" ", "").replace(",", ""))
    except Exception:
        return mac_dinh


def chay(symbol: str, khung: str, so: int = 0, loc: str = "",
         tu: str = "2011.01.01", den: str = "2026.07.29") -> dict:
    kho = [c for c in NP.doc_kho() if not NP.kiem_khai_bao(c)]
    if loc:
        kho = [c for c in kho if loc in json.dumps(c, ensure_ascii=False)]
    if so:
        kho = kho[:so]
    ma, dat = D.sinh_ea(kho, TEN_EA, khung=khung)
    bo = [c for c in kho if c.get("_khong_dich")]
    print("kho %d -> dich duoc %d, bo %d" % (len(kho), len(dat), len(bo)))

    src = XM_DATA / "MQL5" / "Experts" / f"{TEN_EA}.mq5"
    src.write_text(ma, encoding="utf-8")
    loi = bien_dich(src)
    if loi:
        print("  " + loi)
        return {"loi": loi}
    print("  bien dich xong (%d co che)" % len(dat))

    ten = "kho_%s_%s" % (symbol, khung)
    ini = viet_ini(ten, symbol, len(dat), tu, den)
    for hs in (".xml", ".htm"):
        f = XM_DATA / (ten + hs)
        if f.exists():
            f.unlink()

    dong_terminal()
    print("  chay optimization %d pass ..." % len(dat), flush=True)
    t0 = time.time()
    subprocess.Popen([str(XM_EXE), "/config:%s" % ini])
    while time.time() - t0 < 3600:
        time.sleep(10)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                           capture_output=True, text=True)
        if "terminal64.exe" not in r.stdout:
            break
    else:
        dong_terminal()
        return {"loi": "qua 3600s"}
    giay = round(time.time() - t0, 1)

    hong = kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        return {"loi": hong, "giay": giay, "chua_do": True}

    f = next((XM_DATA / (ten + h) for h in (".xml", ".htm")
              if (XM_DATA / (ten + h)).exists()), None)
    if f is None:
        return {"loi": "khong thay bang ket qua", "giay": giay, "chua_do": True}

    dong = doc_xml(f)
    ket = []
    for d in dong:
        i = int(_so(d.get("InpMaCoChe", d.get("Pass", -1)), -1))
        if not (0 <= i < len(dat)):
            continue
        ket.append({
            "ten": dat[i].get("ten"), "ma_co_che": i,
            "lenh": int(_so(d.get("Trades"))),
            "lai": _so(d.get("Profit")),
            "pf": _so(d.get("Profit Factor")),
            "sharpe": _so(d.get("Sharpe Ratio")),
            "dd_pct": _so(d.get("Equity DD %")),
            "ky_vong": _so(d.get("Expected Payoff")),
            "ho": dat[i].get("ho"), "co_che": str(dat[i].get("co_che"))[:110]})
    ket.sort(key=lambda x: -x["sharpe"])
    ra = {"symbol": symbol, "khung": khung, "so_co_che": len(dat),
          "so_pass": len(ket), "giay": giay, "ghi_chu": hong, "ket": ket,
          "bo_dich": [{"ten": c["ten"], "vi_sao": c["_khong_dich"]} for c in bo]}
    (LAB / "reports" / f"TESTER_KHO_{symbol}_{khung}.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra


def main() -> int:
    def lay(c, md):
        return sys.argv[sys.argv.index(c) + 1] if c in sys.argv else md
    symbol = lay("--ma", "US100Cash")
    khung = lay("--khung", "D1")
    so = int(lay("--so", "0"))
    loc = lay("--loc", "")
    r = chay(symbol, khung, so, loc, lay("--tu", "2011.01.01"),
             lay("--den", "2026.07.29"))
    if r.get("loi"):
        print("LOI:", r["loi"])
        return 1
    print("\n%d pass, %ss  %s" % (r["so_pass"], r["giay"], r.get("ghi_chu", "")))
    print("\n%-42s %6s %9s %6s %7s %7s" % ("co che", "lenh", "lai", "PF",
                                           "sharpe", "DD%"))
    for d in r["ket"][:25]:
        print("%-42s %6d %9.2f %6.2f %7.2f %7.2f"
              % (str(d["ten"])[:42], d["lenh"], d["lai"], d["pf"],
                 d["sharpe"], d["dd_pct"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
