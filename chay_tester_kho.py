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
             deposit: int = 10000, khung: str = "", lot: float = 0.10) -> Path:
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
InpLot={lot:g}||{lot:g}||0||0||N
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
    # BANG DAU HIEU PHAI KHOP VOI CAI MAY THAT SU IN RA.
    #
    # Do 15/09/2026: `--ma AUDCAD` dot mot luot boot terminal roi tra ve
    # "khong thay bang ket qua" tro troi. Log MT5 noi thang, hai dong:
    #     `Tester  cannot select symbol in market watch`
    #     `Tester  symbol AUDCAD not exist`
    # `unknown symbol` o tren khong khop mot ky tu nao voi hai dong do. Mot
    # bang dau hieu khong bat duoc cai chac chan CO thi khong phai bang dau
    # hieu. [[luat-do-phai-thay-duoc-cai-co]]
    ("not exist", "ten ma khong co tren may chu dang dang nhap"),
    ("cannot select symbol", "khong chon duoc ma trong Market Watch"),
    ("no history", "khong co lich su gia"),
]


def _sau_moc(dong: str, moc: float) -> bool:
    """Dong log MT5 co dau thoi gian `HH:MM:SS.mmm` - no co sau `moc` khong.

    File log gom ca ngay nen `mtime` cua file khong noi duoc dong nao la moi.
    """
    import re
    import time as _t
    m = re.search(r"\b(\d{2}):(\d{2}):(\d{2})\.\d{3}\b", dong)
    if not m:
        return False
    g, ph, gy = (int(x) for x in m.groups())
    t = _t.localtime(moc)
    hom_nay = _t.mktime((t.tm_year, t.tm_mon, t.tm_mday, g, ph, gy, 0, 0, -1))
    return hom_nay >= moc - 5


def chan_doan_log(gio_lui: float = 1.0, tu_luc: float | None = None) -> list[str]:
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
    # CHI DOC DONG CUA CHINH LUOT NAY.
    #
    # Do 15/09/2026: mot luot chay DUNG ten ma (`AUDCADmicro`) that bai vi ly do
    # khac, va chan doan in ra `symbol AUDCAD not exist` - dong log cua luot
    # TRUOC do mot tieng, voi ten ma sai. Toi doc va suyt di sua lai thu da dung.
    # Mot bo chan doan tra ve nguyen nhan CU con nguy hiem hon khong chan doan
    # gi: no co ve dang tra loi. `tu_luc` la moc bat dau luot chay.
    ra = []
    gioi_han = float(tu_luc) if tu_luc else _t.time() - gio_lui * 3600
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
                if tu_luc and not _sau_moc(dong, gioi_han):
                    continue
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




def _gop_trung_hanh_vi(kho: list, symbol: str, khung: str) -> tuple:
    """Bo co che sinh ra CHUOI TIN HIEU Y HET nhau. Tra (kho da gop, bi_danh).

    ## Vi sao phai o day

    `nhan/loc_co_che._van_tay_hanh_vi` co tu truoc va no CHAY DUNG - do 15/09
    tren XM_US100CASH H1, `ns_nen_bua_>_q90_giu10` va
    `ns_nen_rau_duoi_>_q90_giu10` cho cung mot bam `013c96e1f1ddb02a`. Nhung
    `chay_tester_kho` doc thang `ngu_phap.doc_kho()` va chi ap `kiem_khai_bao`,
    nen no chua bao gio thay bo loc do.

    Hau qua do duoc cung ngay: mot luot 135 co che `mau_nen`, trong do
    `bua` <-> `rau_duoi` va `sao_bang` <-> `rau_tren` la CUNG MOT THU. Trong
    nen, ba phan `rau duoi / rau tren / than` cong lai bang 1, nen

        bua      = duoi/bien - tren/bien - |than|/bien = 2*(duoi/bien) - 1
        sao_bang = 2*(tren/bien) - 1

    Hai bien doi tuyen tinh TANG, nen sau `phan_vi` chung xep hang y het nhau.
    Do duoc: lech toi da 1,1e-16, Spearman 1,000000.

    Cai dat nhat khong phai luot tester thua ma la **hai co che giong het nhau
    trong nhu hai xac nhan doc lap** - va neu ca hai cung qua cong thi nguoi
    doc se tin gap doi vao mot thu duy nhat.

    Do tren CHINH tai san va khung sap chay, khong phai mot chuoi chuan: hai co
    che co the trung tren ma nay va khac tren ma khac.
    """
    import hashlib
    try:
        import numpy as np
        from nhan import du_lieu as DL
    except Exception:
        return kho, {}
    goc = symbol.replace("micro", "").replace("Cash", "")
    for thu in (goc, symbol):
        try:
            df = DL.nap(thu, khung)
            break
        except Exception:
            df = None
    if df is None or len(df) < 200:
        return kho, {}          # khong do duoc thi CHO CHAY, dung chan mu
    nhom: dict = {}
    ra, bi_danh = [], {}
    for c in kho:
        try:
            a = np.nan_to_num(np.asarray(NP.sinh_tu_spec(c, df), dtype=float))
            vt = hashlib.blake2b(a.tobytes(), digest_size=8).hexdigest()
        except Exception:
            ra.append(c)        # khong do duoc thi giu lai
            continue
        if vt in nhom:
            bi_danh.setdefault(nhom[vt], []).append(str(c.get("ten")))
            continue
        nhom[vt] = str(c.get("ten"))
        ra.append(c)
    return ra, bi_danh

def chay(symbol: str, khung: str, so: int = 0, loc: str = "",
         tu: str = "2011.01.01", den: str = "2026.07.29",
         lot: float = 0.10) -> dict:
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
        return _chay_trong_khoa(symbol, khung, so, loc, tu, den, lot)


def _chay_trong_khoa(symbol: str, khung: str, so: int = 0, loc: str = "",
                     tu: str = "2011.01.01", den: str = "2026.07.29",
                     lot: float = 0.10) -> dict:
    # BO CO CHE NAO THI PHAI NOI RO BO CAI NAO VA VI SAO.
    #
    # Truoc 14/09 dong nay chi loc im lang, va nguoi doc chi thay mot con so
    # cuoi ("dich duoc 1"). Do 14/09: **44/3233 co che trong kho khong qua
    # `kiem_khai_bao`** va bi vut moi luot chay ma khong ai biet. Toi da suyt
    # chay tester tren MOT he roi tuong do la ket qua cua ca ba he o lan nhanh -
    # chi phat hien vi tinh co dem lai so co che.
    # `--loc a,b,c` = HOP cua ba bo loc, khong phai giao. Truoc 14/09 day la mot
    # chuoi duy nhat, nen ba he cua lan nhanh khong the vao CHUNG mot me: hai he
    # dau ten co `_dsl_`, he thu ba (`mat_can_bang_lenh_dong_cua`, ho `phien`)
    # khong chia chuoi con nao voi chung. Ma TESTER=1 la rang buoc VAT LY - moi
    # me thua la mot luot boot terminal doc chiem may.
    # KIEM TEN MA TRUOC KHI DOT MOT LUOT BOOT TERMINAL.
    #
    # Cong nay da co tu 13/09 (`chay_bench_quan_tri.goi_y_ma`, chinh no tim ra
    # `XAUUSD -> GOLD`) nhung chi duoc goi trong chinh file do - duong chay
    # CHINH khong bao gio thay no. Nay ca hai dung chung `nhan/ten_ma.py`.
    from nhan import ten_ma as TM
    for dong in TM.canh_bao(symbol):
        print("  " + dong)

    mau_loc = [x.strip() for x in str(loc or "").split(",") if x.strip()]

    def _khop(c) -> bool:
        if not mau_loc:
            return True
        j = json.dumps(c, ensure_ascii=False)
        return any(m in j for m in mau_loc)

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
        if mau_loc:
            trung = [c.get("ten", "?") for c, _ in hong if _khop(c)]
            if trung:
                print("     TRONG DO co %d cai KHOP BO LOC '%s': %s"
                      % (len(trung), loc, ", ".join(trung[:6])))
    if mau_loc:
        kho = [c for c in kho if _khop(c)]
        if not kho:
            print("  BO LOC '%s' KHONG KHOP CO CHE NAO trong %d cai hop le - "
                  "khong co gi de chay." % (loc, len(tat_ca) - len(hong)))
    if so:
        kho = kho[:so]
    # CO CHE NAO SE RA 0 LENH VI LOI KHAI, NOI TRUOC KHI CHAY.
    #
    # 15/09/2026: 13/60 co che `than_nen` ra dung 0 lenh tren AUDCADmicro H4.
    # Khong phai loi dich (ban Python cung 0 tin hieu), khong phai thi truong:
    # loi khai so `close - open` (DON VI GIA) voi hang so `0.5`, nen no chet
    # sach tren moi cap FX va song tren vang/chi so. Mot dong 0 nhu vay nam
    # canh cac dong that va doc y het mot ket qua am. Xem `nhan/thang_gia.py`.
    from nhan import thang_gia as TG
    for dong in TG.canh_bao_cho_ma([c.get("ten") for c in kho], symbol):
        print("  " + dong)

    kho, bi_danh = _gop_trung_hanh_vi(kho, symbol, khung)
    if bi_danh:
        print("  gop %d co che TRUNG HANH VI (cung mot chuoi tin hieu):"
              % sum(len(v) for v in bi_danh.values()))
        for giu, bo in list(bi_danh.items())[:6]:
            print("     %-40s <- %s" % (giu[:40], ", ".join(x[:34] for x in bo[:3])))

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
    ini = viet_ini(ten, symbol, len(dat), tu, den, khung=khung, lot=lot)
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
        # KHONG TRA VE "khong thay bang ket qua" TRO TROI.
        #
        # Do 15/09/2026: nhanh nay la nhanh DUY NHAT khong goi `chan_doan_log`,
        # trong khi log terminal ghi dung mot dong noi het moi chuyen
        # (`symbol AUDCAD not exist`). Nguoi doc mat 20 phut di truy bo dich
        # MQL5 cho mot loi sai TEN MA.
        return {"loi": "khong thay bang ket qua", "giay": giay, "chua_do": True,
                "chan_doan": chan_doan_log(tu_luc=t0),
                "goi_y_ma": TM.goi_y_ma(symbol)}

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
                "chan_doan": chan_doan_log(tu_luc=t0)}

    ra = {"symbol": symbol, "khung": khung, "so_co_che": len(dat),
          "so_pass": len(ket), "giay": giay, "ghi_chu": hong, "ket": ket,
          "bo_dich": [{"ten": c["ten"], "vi_sao": c["_khong_dich"]} for c in bo]}
    (LAB / "reports" / f"TESTER_KHO_{symbol}_{khung}.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra



#: Ngan sach sut giam de chuan hoa MOI cau hinh ve cung mot muc rui ro.
#: Giong `pmg_engine.NGAN_SACH_DD` - co tinh la mot con so, khong phai hai.
NGAN_SACH_DD_PCT = 20.0


def chuan_hoa_cung_rui_ro(lai_usd: float, dd_pct: float, nam: float,
                          deposit: float = 10000.0,
                          ngan_sach: float = NGAN_SACH_DD_PCT):
    """`lai`/`DD%` cua tester -> **%/nam o cung ngan sach sut giam**.

    ## Vi sao cot nay bat buoc

    Tester chay LOT CO DINH 0,10 tren von 10.000, nen con so `lai` phu thuoc vao
    mot lua chon tuy tien. Do 14/09 tren AUDCADmicro: mot he lai 14,12 USD voi
    sut giam 0,07%, mot he khac lai 8,33 USD voi sut giam 0,10%. Doc cot `lai`
    thi he dau hon 69%; doc o cung rui ro thi no chi hon 19%. Va moc mua-giu co
    sut giam 0,23% - gap ba - nen so thang cot `lai` voi no la mot phep so sai.

    Luat cua chu du an: *chi chan khi thua mua-giu o CUNG RUI RO*. Cot nay la
    cho duy nhat cau hoi do duoc tra loi.

    Lot co dinh -> lai va sut giam CUNG ti le tuyen tinh voi don bay, nen he so
    la `ngan_sach / dd_pct`. Gop bang SO HOC (khong phai log): don bay gop bang
    log cho `(S_T/S_0)^L` va thoi ket qua len hang chuc lan.

    Tra `None` khi khong do duoc: sut giam 0 (chua du lenh de co duong cong) hay
    thua qua nang den muc chay tai khoan - ca hai deu la CHUA_DO_DUOC, khong
    duoc in ra thanh mot con so.
    """
    try:
        dd_pct, nam = float(dd_pct), float(nam)
    except (TypeError, ValueError):
        return None
    if dd_pct <= 0 or nam <= 0:
        return None
    don_bay = ngan_sach / dd_pct
    tong = 1.0 + float(lai_usd) * don_bay / float(deposit)
    if tong <= 0:            # chay tai khoan o muc don bay do
        return None
    return (tong ** (1.0 / nam) - 1.0) * 100.0


def _so_nam(tu: str, den: str) -> float:
    """`2013.02.21` -> so nam duong lich giua hai moc."""
    import datetime as _dt
    try:
        a = _dt.date(*[int(x) for x in str(tu).split(".")])
        b = _dt.date(*[int(x) for x in str(den).split(".")])
    except Exception:
        return 0.0
    return max((b - a).days / 365.25, 0.0)


def main() -> int:
    def lay(c, md):
        return sys.argv[sys.argv.index(c) + 1] if c in sys.argv else md
    symbol = lay("--ma", "US100Cash")
    khung = lay("--khung", "D1")
    so = int(lay("--so", "0"))
    loc = lay("--loc", "")
    lot = float(lay("--lot", "0.10"))
    r = chay(symbol, khung, so, loc, lay("--tu", "2011.01.01"),
             lay("--den", "2026.07.29"), lot=lot)
    if r.get("loi"):
        print("LOI:", r["loi"])
        for c in (r.get("chan_doan") or [])[:6]:
            print("   ->", c)
        if r.get("goi_y_ma"):
            print("   y ban dinh noi ten ma la: %s"
                  % ", ".join(r["goi_y_ma"]))
        if r.get("chua_do"):
            print("   => TRANG THAI: CHUA_DO_DUOC, khong phai AM. Sua moi truong")
            print("      roi chay lai; dung doc bang so nhu mot ket luan.")
        return 1
    tu, den = lay("--tu", "2011.01.01"), lay("--den", "2026.07.29")
    nam = _so_nam(tu, den)
    print("\n%d pass, %ss  %s" % (r["so_pass"], r["giay"], r.get("ghi_chu", "")))
    print("lot %g - von 10.000 USD - %s -> %s (%.2f nam)" % (lot, tu, den, nam))
    print("\n%-42s %6s %9s %6s %7s %7s %11s"
          % ("co che", "lenh", "lai", "PF", "sharpe", "DD%",
             "%%/nam@DD%g" % NGAN_SACH_DD_PCT))
    moc = None
    for d in r["ket"][:25]:
        d["pct_nam_cung_rui_ro"] = chuan_hoa_cung_rui_ro(
            d["lai"], d["dd_pct"], nam)
        if str(d["ten"]).startswith("__mua_giu__"):
            moc = d["pct_nam_cung_rui_ro"]
    for d in r["ket"][:25]:
        v = d.get("pct_nam_cung_rui_ro")
        print("%-42s %6d %9.2f %6.2f %7.2f %7.2f %11s"
              % (str(d["ten"])[:42], d["lenh"], d["lai"], d["pf"],
                 d["sharpe"], d["dd_pct"],
                 "CHUA_DO" if v is None else "%+.2f" % v))
    # Cau hoi tien: hon moc MUA-GIU o CUNG rui ro chua. In thang ra day de khong
    # ai phai tu tinh lai - da mot lan toi so cot `lai` voi moc co sut giam gap ba.
    if moc is not None:
        hon = [d for d in r["ket"]
               if not str(d["ten"]).startswith("__mua_giu__")
               and (d.get("pct_nam_cung_rui_ro") or -9e9) > moc]
        n_co = sum(1 for d in r["ket"]
                   if not str(d["ten"]).startswith("__mua_giu__"))
        print("\nmoc mua-giu o cung rui ro: %+.2f%%/nam  ->  %d/%d co che hon moc"
              % (moc, len(hon), n_co))
    else:
        print("\nmoc mua-giu: CHUA_DO_DUOC o cung rui ro - dung ket luan 'hon moc'")
    # MT5 in `Equity DD %` voi HAI chu so thap phan. Lot 0,10 tren von 10.000 cho
    # DD ~0,03% - tuc MOT chu so y nghia, va cot cuoi dang nhan no len >100 lan.
    # Sai so +-0,005 tren 0,03 la +-17% truyen thang vao ket qua. Phai noi ra.
    tho = [d for d in r["ket"][:25] if 0 < float(d["dd_pct"]) < 0.20]
    if tho:
        print("CANH BAO do phan giai: %d/%d co che co DD%% < 0,20 - cot cuoi dang"
              % (len(tho), len(r["ket"][:25])))
        print("   NGOAI SUY don bay >100 lan tu mot chu so y nghia (sai so ~17%).")
        print("   Chay lai voi `--lot` lon hon de DO o co lenh that.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
