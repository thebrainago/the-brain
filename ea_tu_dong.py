# -*- coding: utf-8 -*-
"""ea_tu_dong.py - TAI EA THAT -> BIEN DICH -> CHAY STRATEGY TESTER.

VI SAO CO FILE NAY (chu du an chot 01/09/2026).

Do that cung ngay: bo doc ma bang bieu thuc chinh quy (`nhan/doc_ma.py`) rut duoc
**0 co che tren 7 EA MQL5 that su la chien luoc**. Ly do la kien truc chu khong
phai tinh chinh: EA MQL5 hien dai la CHUONG TRINH CO CAU TRUC - quyet dinh vao
lenh nam rai qua nhieu ham, dong vao mot bien `orderType` roi moi toi
`trade.Buy(...)`. Regex khong lan qua duoc. (Pine thi nguoc lai: doc tot, mot
file ra trung binh 4,9 kieu danh.)

Nen voi MQL5, duong nhanh hon va don gian hon la KHONG DOC MA MA CHAY NO. Do la
dung quy trinh cua du an ("MT5 tester TRUOC, Python SAU") va da lam that voi bot
DongDongTV.

RANH GIOI PHAI GIU - va no KHONG phai ly do an ninh nen khong bo theo VPS duoc:

    Tester la BAN THI NGHIEM, khong bao gio la ONG TOA.

Tester tra ve P/L cua MOT bot o MOT cau hinh. No khong sinh ra mot gia thuyet co
`plan_hash`, khong dang ky truoc, khong ton suat FDR va cung khong duoc mien.
Mot con so dep o day la LY DO DE KHAI BAO MOT GIA THUYET roi cho no qua cong
nhu moi gia thuyet khac - khong phai mot ket luan.

BA CAI BAY DA SAP THAT, deu phai kiem lai moi lan doc so:

  1. `Model=1` NOI DOI khi TP hoac SL < ~2x bien do nen M1: +1.161,5% so voi
     -100,7% o tick that. Mac dinh o day la `Model=4` (tick that).
  2. Bao cao .htm tieng Viet goi **Gross Profit** la "Loi nhuan rong"; loi that
     la "**Tong** loi nhuan rong" - sai 13,5 lan.
  3. Tester ap muc swap CUA HOM NAY cho ca lich su, va Exness chi co bar tu
     2022-08 cho 24/25 symbol. Kiem do sau lich su truoc khi so sanh da thi truong.

VA MOT BAY CUA CHINH METAEDITOR, do 01/09: `metaeditor64.exe /compile:<duong dan
TUYET DOI>` tra rc=0 va **khong lam gi ca** - khong .ex5, khong log. Phai dung
duong dan TUONG DOI tinh tu thu muc `MQL5`, kem `cwd` dat o do.

Chay:
    python ea_tu_dong.py --tai 24              # tai + bien dich, khong chay tester
    python ea_tu_dong.py --chay <ten_ea> --symbol US500m --khung H1
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import doc_ma as DM          # noqa: E402
from nhan import ma_nguon as MN        # noqa: E402

REPORTS = LAB / "reports"
KHO_EA = REPORTS / "ea"

#: Thu muc du lieu cua tung terminal + duong toi metaeditor/terminal cua no.
#: May nay co NAM thu muc du lieu MT5 (bai hoc 29/07: phai quet het truoc khi
#: ket luan "khong tim thay").
TERMINAL = {
    "exness": (r"C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal"
               r"\53785E099C927DB68A545C249CDBCE06",
               r"C:\Program Files\MetaTrader 5 EXNESS"),
}


def _duong(ten_terminal: str) -> tuple[Path, Path, Path]:
    dat, cai = TERMINAL[ten_terminal]
    return Path(dat) / "MQL5", Path(cai) / "metaeditor64.exe", Path(cai) / "terminal64.exe"


def ten_sach(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s)[:40].strip("_") or "ea"


def tai_lo(so_bai: int = 24, muc: str = "mt5/experts") -> list[dict]:
    """Tai `so_bai` EA that tu MQL5 Code Base. Chi file .mq5 don, khong .zip."""
    from tru import seeker as S
    S._ghi_con_tro("mql5_code", {"trang": {muc: 1}, "danh_muc_ke": 0})
    ds = [d for d in S.n_mql5_code([]) if muc.split("/")[-1] in d["tieu_de"]]
    ra = []
    for d in ds[:so_bai]:
        try:
            r = MN.tai_ma_nguon({"url": d["url"], "tieu_de": d["tieu_de"]})
        except Exception:
            r = None
        if r and r.get("noi_dung"):
            ra.append({"url": d["url"], "ten": d["tieu_de"], "ma": r["noi_dung"]})
        time.sleep(0.4)
    KHO_EA.mkdir(parents=True, exist_ok=True)
    (KHO_EA / "kho.json").write_text(
        json.dumps(ra, ensure_ascii=False), encoding="utf-8")
    return ra


def bien_dich(ds: list[dict], ten_terminal: str = "exness") -> list[dict]:
    """Ghi .mq5 vao MQL5/Experts/_tu_dong roi bien dich tung file.

    Duong dan phai TUONG DOI tinh tu `MQL5` - duong tuyet doi cho rc=0 va khong
    sinh gi ca (do that 01/09, mat mot luot moi phat hien vi khong co thong bao
    loi nao).
    """
    mql5, me, _ = _duong(ten_terminal)
    thu = mql5 / "Experts" / "_tu_dong"
    thu.mkdir(parents=True, exist_ok=True)
    ra = []
    for x in ds:
        ten = ten_sach(x["ten"].split("]")[-1])
        f = thu / f"{ten}.mq5"
        f.write_text(x["ma"], encoding="utf-8")
        rel = "Experts" + chr(92) + "_tu_dong" + chr(92) + f.name
        p = subprocess.Popen([str(me), f"/compile:{rel}", "/log"], cwd=str(mql5))
        for _ in range(48):
            if f.with_suffix(".ex5").exists():
                break
            time.sleep(0.25)
        else:
            try:
                p.kill()
            except Exception:
                pass
        co = f.with_suffix(".ex5").exists()
        loi = ""
        lg = f.with_suffix(".log")
        if not co and lg.exists():
            t = lg.read_text(encoding="utf-16", errors="ignore")
            d = [l for l in t.splitlines() if "error" in l.lower()]
            loi = (d[0] if d else "")[:160]
        ra.append({**x, "ten_file": ten, "bien_dich": co, "loi": loi,
                   "input": DM.rut_input(x["ma"])})
    return ra


def viet_set(ten: str, khai: dict, ten_terminal: str = "exness") -> str:
    """File .set tu khai bao input cua chinh tac gia (gia tri MAC DINH cua ho).

    Khong doan tham so: doc dung cai ho viet. Quet quanh do la buoc sau, va moi
    diem quet la mot suat FDR nen khong duoc quet bua.
    """
    mql5, _, _ = _duong(ten_terminal)
    thu = mql5 / "Profiles" / "Tester"
    thu.mkdir(parents=True, exist_ok=True)
    dong = [f"{k}={v['gia_tri']:g}" for k, v in khai.items()]
    f = thu / f"{ten}.set"
    f.write_text("\n".join(dong) + "\n", encoding="utf-16")
    return f.name


def viet_ini(ten: str, ea: str, tap_set: str, symbol: str, khung: str,
             tu: str, den: str, model: int = 4, von: int = 10000,
             don_bay: int = 100, ten_terminal: str = "exness") -> Path:
    """`.ini` cho tester.

    `Report=` PHAI la duong TUONG DOI - duong tuyet doi bi lo di khong bao loi
    (bai hoc 27/07), va file ra nam trong thu muc DU LIEU cua terminal.
    `Model=4` la tick that: xem cai bay 1 o dau file.
    """
    mql5, _, _ = _duong(ten_terminal)
    ra = mql5.parent / "_bao_cao"
    ra.mkdir(parents=True, exist_ok=True)
    noi = (f"[Tester]\nExpert=_tu_dong{chr(92)}{ea}\nExpertParameters={tap_set}\n"
           f"Symbol={symbol}\nPeriod={khung}\nModel={model}\nExecutionMode=0\n"
           f"Optimization=0\nFromDate={tu}\nToDate={den}\nForwardMode=0\n"
           f"Deposit={von}\nCurrency=USD\nLeverage=1:{don_bay}\nProfitInPips=0\n"
           f"Report=_bao_cao{chr(92)}{ten}\nReplaceReport=1\nShutdownTerminal=1\n")
    f = REPORTS / "tester_ini"
    f.mkdir(parents=True, exist_ok=True)
    p = f / f"{ten}.ini"
    p.write_text(noi, encoding="utf-16")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tai", type=int, default=0, help="tai va bien dich N EA")
    ap.add_argument("--muc", default="mt5/experts")
    ap.add_argument("--terminal", default="exness")
    a = ap.parse_args()

    if a.tai:
        ds = tai_lo(a.tai, a.muc)
        print(f"tai duoc {len(ds)} file .mq5")
        kq = bien_dich(ds, a.terminal)
        ok = sum(1 for x in kq if x["bien_dich"])
        print(f"bien dich: {ok}/{len(kq)}")
        for x in kq:
            n_in = len(x["input"])
            print(f"  {'OK ' if x['bien_dich'] else 'LOI'} {x['ten_file'][:42]:44} "
                  f"{n_in:3} input  {x['loi'][:60]}")
        (KHO_EA / "bien_dich.json").write_text(
            json.dumps([{k: v for k, v in x.items() if k != "ma"} for x in kq],
                       ensure_ascii=False, indent=1), encoding="utf-8")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
