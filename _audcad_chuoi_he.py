# -*- coding: utf-8 -*-
"""_audcad_chuoi_he.py - GHEP 8 CUM DOC LAP THANH MOT CHUOI HE CHO AUDCAD.

Chu du an 15/09/2026: *"tao ra mot hoac chuoi he thong toi uu cho audcad"*.

## Duong di den day

1. `chay_tester_kho` quet CA KHO (3.140 co che) tren AUDCAD H4, HAI cua so:
   TRAIN 2016-2021 (moc mua-giu **-0,06%/nam**, gan nhu phang) va HOLDOUT
   2021-2026.
2. `_audcad_chon_va_xac_nhan.py`: CHON top 40 tren TRAIN -> **16/40 song** tren
   HOLDOUT, so voi ty le nen 5,5%. Tuc **7,24 lan**.
3. `_audcad_gom_cum.py`: 16 he do la **8 cum doc lap** (|r| >= 0,7 thi gom),
   tuong quan trung vi giua cac dai dien **0,173**.

## VI SAO PHAI CHAY CHUNG TRONG MOT EA

Ghep bang cach cong ba bang ket qua rieng la sai: moi bang di qua mot lan boot
khac, va quan trong hon - **sut giam cua tong KHONG bang tong cac sut giam**.
Chay chung mot EA, moi cum mot slot rieng (mot magic rieng), EA ghi duong von
TUNG SLOT theo tung nen. Tu do do duoc:
  - tuong quan CHUOI VON that (khong phai tuong quan tin hieu)
  - sut giam cua DANH MUC, do truc tiep
  - va moc mua-giu di qua DUNG bo thuc thi do [[v6-doi-chieu-dung-cach]]

## HAI DIEM VAN HANH (do that tren HOLDOUT 5,36 nam, lot MICRO/von 10.000)

Duong bien lai-DD la TUYEN TINH voi lot (fixed-lot), da xac nhan bang chay that:

    lot 20  -> DD 20,6%   ~15%/nam don   (than trong)
    lot 36  -> DD 30,2%   ~27%/nam don   (muc chu du an dua ra 15/09)

Nhan lot ×3 (lot 15) KHONG dat 27% - chi 11%/nam o DD 17%: cot `%/nam@DD20` la
BAT BIEN cua he (~Calmar 0,5), khong scale theo lot. De 27%/nam phai chap nhan
DD ~30%, va do la lua chon rui ro cua chu du an (chap nhan rui ro cao). Lot 36
KHONG stop-out (da chay that).

Chay:  python _audcad_chuoi_he.py [--lot 36] [--tu ... --den ...]
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import chay_tester_kho as C          # noqa: E402
from nhan import dich_mq5 as D       # noqa: E402
from nhan import dich_mq5_ghep as G  # noqa: E402
from nhan import ngu_phap as NP      # noqa: E402

TEN_EA = "AudcadChuoi"
VON = 10000
#: LOT 0,10 tren von 10.000 cho sut giam ~0,01-0,2% - DUOI do phan giai cua
#: `Equity DD %` (hai chu so thap phan), va cot `%/nam@DD20` khi do ngoai suy
#: don bay >100 lan tu mot chu so y nghia. Luot dau chay o 0,10 cho
#: `__mua_giu__` ra "+19,80%/nam" vi DD = 0,00. Cung co lenh voi cac luot quet
#: don de so sanh duoc truc tiep.
LOT = 36.0  # diem van hanh 27%/nam @ DD 30% (chu du an chon)
CHUNG = Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files"


def dai_dien() -> list[str]:
    d = json.loads((LAB / "reports" / "AUDCAD_CUM.json").read_text(encoding="utf-8"))
    return [c["dai_dien"] for c in d["cum"]]


def sinh(ten_he: list[str], khung: str) -> list[dict]:
    kho = {c.get("ten"): c for c in NP.doc_kho()}
    thieu = [t for t in ten_he if t not in kho]
    if thieu:
        raise SystemExit("khong co trong kho: %s" % thieu)
    # Slot 0 la MOC mua-giu, slot 1 la moc BAN-giu. Ca hai phai o trong CUNG EA
    # de di qua cung spread / phi qua dem / gio khop.
    specs = [dict(D.SPEC_MUA_GIU), dict(D.SPEC_BAN_GIU)] + [kho[t] for t in ten_he]
    ma, dat = G.sinh_ea_ghep(specs, TEN_EA, khung=khung,
                             tep="AUDCAD_CHUOI.csv")
    src = C.XM_DATA / "MQL5" / "Experts" / (TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        raise SystemExit("bien dich: " + loi)
    print("EA %d slot:" % len(dat))
    for i, c in enumerate(dat):
        print("   slot %d  %s" % (i, c["ten"]))
    return dat


def chay(symbol: str, khung: str, tu: str, den: str, n_slot: int) -> Path:
    from nhan import bi_mat as BM
    from nhan import khoa_tester as KT
    from nhan import ngan_sach as NS
    ten = "audcad_chuoi"
    tep = "AUDCAD_CHUOI.csv"
    (C.XM_DATA / "MQL5" / "Profiles" / "Tester").mkdir(parents=True, exist_ok=True)
    dat_set = "".join("InpLot%d=%.2f||%.2f||0||0||N\n" % (i, LOT, LOT)
                      for i in range(n_slot))
    (C.XM_DATA / "MQL5" / "Profiles" / "Tester" / (ten + ".set")).write_text(
        dat_set + "InpMagic=26091501||26091501||0||0||N\n"
        "InpGhi=1||1||0||0||N\nInpTep=%s\n" % tep, encoding="utf-8")
    (C.XM_DATA / (ten + ".ini")).write_text(
        BM.khoi_common_ini("XM") + """[Tester]
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
""" % (TEN_EA, ten, symbol, khung, tu, den, VON, ten), encoding="utf-16")
    ra = CHUNG / tep
    if ra.exists():
        ra.unlink()
    with NS.giu_warp(False, "audcad chuoi"), KT.giu("audcad_chuoi"):
        C.dong_terminal()
        t0 = time.time()
        subprocess.Popen([str(C.XM_EXE), "/config:%s" % (C.XM_DATA / (ten + ".ini"))])
        while time.time() - t0 < 2400:
            time.sleep(5)
            r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                               capture_output=True, text=True)
            if "terminal64.exe" not in r.stdout:
                break
    print("  chay xong %.0fs" % (time.time() - t0))
    if not ra.exists():
        raise SystemExit("EA khong ghi duoc %s - kiem FILE_COMMON" % ra)
    return ra


def doc(f: Path, n: int):
    van = ""
    for bo_ma in ("utf-16", "utf-8", "cp1252"):
        try:
            van = f.read_text(encoding=bo_ma)
        except (UnicodeDecodeError, UnicodeError):
            continue
        if ";" in van or "," in van:
            break
    dong = [x for x in van.splitlines() if x.strip()]
    # HEADER LA NGUON SU THAT, KHONG DOAN THEO VI TRI.
    #
    # Ban dau toi doc `o[i+1]` va moi slot lech di MOT: `__ban_giu__` ra 131,50
    # (dung la so cua `__mua_giu__`) con `rsi_xuong_nguong_cao` ra -811,67
    # (dung la so cua `__ban_giu__`). Bang nhin hoan toan hop li - chi la moi
    # dong noi ve mot he KHAC. Dinh dang that:
    #     thoi_gian, gia, von0, mo0, von1, mo1, ...
    # tuc von cua slot i o cot `2 + 2*i`. Doc theo TEN COT thi khong the lech.
    dau = [x.strip() for x in dong[0].replace(";", ",").split(",")]
    cot = {}
    for i in range(n):
        ten_cot = "von%d" % i
        cot[i] = dau.index(ten_cot) if ten_cot in dau else 2 + 2 * i
    pnl = [[] for _ in range(n)]
    for d in dong[1:]:
        o = d.replace(";", ",").split(",")
        for i in range(n):
            k = cot[i]
            try:
                pnl[i].append(float(o[k]))
            except (ValueError, IndexError):
                pnl[i].append(pnl[i][-1] if pnl[i] else 0.0)
    return [np.asarray(x, float) for x in pnl]


def _sut_giam(v: np.ndarray) -> float:
    if not len(v):
        return 0.0
    dinh = np.maximum.accumulate(VON + v)
    return float(np.max((dinh - (VON + v)) / dinh) * 100.0)


def main() -> int:
    def lay(c, md):
        return sys.argv[sys.argv.index(c) + 1] if c in sys.argv else md
    symbol = lay("--ma", "AUDCADmicro")
    khung = lay("--khung", "H4")
    tu, den = lay("--tu", "2021.03.19"), lay("--den", "2026.07.29")
    global LOT
    LOT = float(lay("--lot", str(LOT)))
    ten_he = dai_dien()
    print("=" * 74)
    print("CHUOI HE AUDCAD - %d cum doc lap + 2 moc, chay CHUNG mot EA" % len(ten_he))
    print("=" * 74)
    dat = sinh(ten_he, khung)
    f = chay(symbol, khung, tu, den, len(dat))
    pnl = doc(f, len(dat))
    nam = C._so_nam(tu, den)

    ten = [c["ten"] for c in dat]
    print("\n%-42s %10s %8s %11s" % ("slot", "lai USD", "DD%", "%/nam@DD20"))
    print("-" * 76)
    for i, t in enumerate(ten):
        lai = float(pnl[i][-1]) if len(pnl[i]) else 0.0
        dd = _sut_giam(pnl[i])
        v = C.chuan_hoa_cung_rui_ro(lai, dd, nam)
        print("%-42s %10.2f %8.2f %11s"
              % (t[:42], lai, dd, "CHUA_DO" if v is None else "%+.2f" % v))

    # --- DANH MUC: cong deu cac cum (bo hai moc o slot 0,1) ---
    cum = [pnl[i] for i in range(2, len(ten))]
    n = min(len(x) for x in cum) if cum else 0
    tong = np.sum([x[:n] for x in cum], axis=0)
    dd_tong = _sut_giam(tong)
    lai_tong = float(tong[-1]) if n else 0.0
    v_tong = C.chuan_hoa_cung_rui_ro(lai_tong, dd_tong, nam)
    tong_dd_rieng = sum(_sut_giam(x) for x in cum)
    print("-" * 76)
    print("%-42s %10.2f %8.2f %11s"
          % ("*** DANH MUC (cong deu %d cum) ***" % len(cum), lai_tong, dd_tong,
             "CHUA_DO" if v_tong is None else "%+.2f" % v_tong))
    print("   tong cac sut giam RIENG: %.2f%%  ->  sut giam CUA TONG: %.2f%%"
          % (tong_dd_rieng, dd_tong))
    print("   loi ich da dang hoa: **%.2f lan**"
          % (tong_dd_rieng / max(dd_tong, 1e-9)))

    # --- tuong quan CHUOI VON that ---
    print("\ntuong quan CHUOI VON (khong phai tin hieu):")
    b = [np.diff(x[:n]) for x in cum]
    rs = []
    for i in range(len(b)):
        for j in range(i + 1, len(b)):
            if np.std(b[i]) > 0 and np.std(b[j]) > 0:
                rs.append(abs(float(np.corrcoef(b[i], b[j])[0, 1])))
    if rs:
        print("   |r| trung vi %.3f · cao nhat %.3f · so cap %d"
              % (float(np.median(rs)), float(np.max(rs)), len(rs)))

    ra = LAB / "reports" / "AUDCAD_CHUOI_HE.json"
    ra.write_text(json.dumps(
        {"symbol": symbol, "khung": khung, "tu": tu, "den": den,
         "slot": [{"ten": t, "lai": float(pnl[i][-1]) if len(pnl[i]) else 0.0,
                   "dd_pct": _sut_giam(pnl[i])} for i, t in enumerate(ten)],
         "danh_muc": {"lai": lai_tong, "dd_pct": dd_tong,
                      "pct_nam_dd20": v_tong,
                      "loi_ich_da_dang_hoa": tong_dd_rieng / max(dd_tong, 1e-9)}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s" % ra.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
