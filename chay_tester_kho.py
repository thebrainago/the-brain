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

#: `Optimization=1` = QUET DAY DU, khong phai `2` = thuat DI TRUYEN.
#:
#: Loi tim ra 06/09/2026 sau ba luot chay: bang ket qua chi co **116/361 pass**,
#: va `mean_reversion_z5` (chi so 160) KHONG CO trong bang - trong khi luot chay
#: rieng cua no cho 207 lenh. Khong phai co che im lang: thuat di truyen chi lay
#: MOT PHAN khong gian tham so, va voi mot tham so la "ma co che" thi lay mau
#: nhu vay la bo sot co che chu khong phai bo sot cau hinh.
#: Trieu chung de doc nham: "245 co che khong ra pass nao" doc y het "245 co che
#: khong vao lenh" [[ket-luan-am-phai-phan-biet-chua-do]].
#:
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
             deposit: int = 10000, khung: str = "") -> Path:
    p = XM_DATA / f"{ten}.ini"
    # TU DANG NHAP trong chinh `.ini` - xem `bi_mat.khoi_common_ini`.
    # Khong co khoi nay thi tester chet voi "tester not started because the
    # account is not specified", va thong bao do KHONG noi gi ve dang nhap.
    from nhan import bi_mat as _BM
    _chung = _BM.khoi_common_ini("XM")
    p.write_text(_chung + f"""[Tester]
Expert={TEN_EA}.ex5
Symbol={symbol}
Period={khung or KHUNG_CHAY}
Model=2
ExecutionMode=0
Optimization=1
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



#: Cac cau trong log terminal/tester noi rang luot chay HONG VI MOI TRUONG,
#: khong phai vi chien luoc. Moi cau deu dan toi bao cao "0 lenh".
DAU_HIEU_HONG = [
    ("authorization on", "khong dang nhap duoc tai khoan"),
    ("Invalid account", "tai khoan khong hop le"),
    ("not synchronized with", "terminal chua dong bo voi may chu giao dich"),
    ("cannot synchronize history", "khong tai duoc lich su gia cua ma nay"),
    ("unknown symbol", "ten ma khong co tren terminal"),
    ("no history", "khong co lich su gia"),
]


def chan_doan_log(gio_lui: float = 1.0) -> list[str]:
    """Doc log terminal + tester, tra ve nhung cau giai thich vi sao luot chay hong.

    ## Vi sao ham nay ton tai

    MT5 bao "0 lenh" cho MOI kieu hong: khong dang nhap, sai ten ma, thieu lich
    su, EA khong khop. Bao cao tra ve mot bang toan so 0 va **khong mot loi nao**
    noi ly do - nguoi doc se di truy chien luoc trong khi loi nam o moi truong.

    Do 14/09/2026: chay 2 luot x 628 giay, ca 6 co che deu 0 lenh KE CA moc
    mua-giu. Ly do that chi co trong log terminal:
        `'342418441': authorization on XMGlobal-MT5 17 failed (Invalid account)`
        `terminal is not synchronized with the trade server before start`
    """
    import re
    import time as _t
    ra, gioi_han = [], _t.time() - gio_lui * 3600
    for thu_muc in ("logs", "Tester/logs"):
        d = XM_DATA / thu_muc
        if not d.exists():
            continue
        for f in sorted(d.glob("2*.log"))[-2:]:
            try:
                if f.stat().st_mtime < gioi_han:
                    continue
                s = f.read_bytes().decode("utf-16-le", errors="replace")
            except Exception:
                continue
            for dong in s.split(chr(10)):
                for manh, y_nghia in DAU_HIEU_HONG:
                    if manh.lower() in dong.lower():
                        cau = re.sub(r"\s+", " ", dong.strip())[:130]
                        moi = f"{y_nghia}: {cau}"
                        if moi not in ra:
                            ra.append(moi)
                        break
    return ra


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
    """Chay ca kho qua MT5 Strategy Tester.

    KHOA TESTER (11/09/2026): ham nay ghi de cung mot .mq5 / .ini / .xml va may
    chi co MOT terminal64.exe. Truoc day rang buoc do duoc giu bang ky luat con
    nguoi (mot dong trong NHIEM_VU.json). Nay no la mot cai khoa that - vi ky
    luat con nguoi hong IM LANG, nhat la khi ca Claude, qwen va chu du an cung
    ngoi tren mot may.
    """
    from nhan import khoa_tester as KT
    from nhan import ngan_sach as NS
    # MT5 KHONG ket noi duoc toi may chu giao dich qua Cloudflare WARP. Giu
    # WARP TAT suot luot chay, va cam bo cao mql5 lat no giua chung.
    with NS.giu_warp(False, "MT5 tester"), KT.giu(f"chay_tester_kho {symbol} {khung}"):
        return _chay_trong_khoa(symbol, khung, so, loc, tu, den)


def _chay_trong_khoa(symbol: str, khung: str, so: int = 0, loc: str = "",
                     tu: str = "2011.01.01", den: str = "2026.07.29") -> dict:
    # BO CO CHE NAO THI PHAI NOI RO BO CAI NAO VA VI SAO.
    #
    # Truoc 14/09 dong nay chi loc im lang, va nguoi doc chi thay mot con so
    # cuoi ("dich duoc 1"). Do 14/09: **44/3233 co che trong kho khong qua
    # `kiem_khai_bao`** va bi vut moi luot chay ma khong ai biet. Toi da suyt
    # chay tester tren MOT he roi tuong do la ket qua cua ca ba he o lan nhanh -
    # chi phat hien vi tinh co dem lai so co che.
    tat_ca = NP.doc_kho()
    kho, hong = [], []
    for c in tat_ca:
        loi = NP.kiem_khai_bao(c)
        (hong if loi else kho).append((c, loi))
    kho = [c for c, _ in kho]
    if hong:
        import collections as _cl
        dem = _cl.Counter(str(l[0])[:70] for _, l in hong)
        print("  %d/%d co che BI BO vi khai bao hong:" % (len(hong), len(tat_ca)))
        for ly_do, n in dem.most_common(6):
            print("     %4d  %s" % (n, ly_do))
        if loc:
            trung = [c.get("ten", "?") for c, _ in hong
                     if loc in json.dumps(c, ensure_ascii=False)]
            if trung:
                print("     TRONG DO co %d cai KHOP BO LOC '%s': %s"
                      % (len(trung), loc, ", ".join(trung[:6])))
    if loc:
        kho = [c for c in kho if loc in json.dumps(c, ensure_ascii=False)]
    if so:
        kho = kho[:so]
    ma, dat = D.sinh_ea(kho, TEN_EA, khung=khung)
    bo = [c for c in kho if c.get("_khong_dich")]
    print("kho %d -> dich duoc %d, bo %d" % (len(kho), len(dat), len(bo)))
    if bo:
        print("  khong dich duoc: %s"
              % ", ".join(str(c.get("ten", "?")) for c in bo[:8]))

    src = XM_DATA / "MQL5" / "Experts" / f"{TEN_EA}.mq5"
    src.write_text(ma, encoding="utf-8")
    loi = bien_dich(src)
    if loi:
        print("  " + loi)
        return {"loi": loi}
    print("  bien dich xong (%d co che)" % len(dat))

    ten = "kho_%s_%s" % (symbol, khung)
    ini = viet_ini(ten, symbol, len(dat), tu, den, khung=khung)
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

    # TAT CA 0 LENH = HONG MOI TRUONG, khong phai ket qua chien luoc.
    #
    # Dau hieu chac nhat la moc `__mua_giu__` cung 0 lenh: mua roi giu ma khong
    # vao lenh nao thi loi khong nam o chien luoc. Do 14/09/2026: hai luot chay
    # x 628 giay, 6/6 co che deu 0 lenh, va ly do that chi nam trong log
    # terminal chu khong o bao cao:
    #     `'342418441': authorization on XMGlobal-MT5 17 failed (Invalid account)`
    #     `terminal is not synchronized with the trade server before start`
    # Bao cao thi chi la mot bang toan so 0 - doc no nhu ket qua la di truy
    # chien luoc trong khi loi nam o moi truong.
    if ket and all(int(d.get("lenh") or 0) == 0 for d in ket):
        return {"loi": ("TAT CA %d co che deu 0 lenh - hong MOI TRUONG, khong "
                        "phai ket qua chien luoc" % len(ket)),
                "chua_do": True, "giay": giay, "so_pass": len(ket), "ket": ket,
                "chan_doan": chan_doan_log()}

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
        for c in (r.get("chan_doan") or [])[:6]:
            print("   ->", c)
        if r.get("chua_do"):
            print("   => TRANG THAI: CHUA_DO_DUOC, khong phai AM. Sua moi truong")
            print("      roi chay lai; dung doc bang so nhu mot ket luan.")
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
