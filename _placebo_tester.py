# -*- coding: utf-8 -*-
"""_placebo_tester.py - PLACEBO CHO HAI HE SONG SOT, CHAY TREN TICK THAT.

Sau phien 06/09 con dung HAI co che qua ca hai cong (train+holdout duong, VA
thang mua-giu o cung sut giam):

    mean_reversion_z5                  train +0,15  holdout +1,43
    pine_ichimoku_cloud_..._ema144     train +0,10  holdout +1,25

Ca hai co cung mot hinh dang dang ngo: **train gan 0, holdout manh**. Do la hinh
dang cua mot GIAI DOAN, khong nhat thiet la cua mot co che. Viec tiep theo dung
la HA BE chung, khong phai mo rong.

## PLACEBO KIEU GI

Khong hoan vi lai/lo: phep do giu nguyen phan phoi nen luon ra ~50% va se "ket
luan" rang moi he deu truot [[v6-doi-chieu-dung-cach]] - loi da mac 29/07.

O day dich CHUOI TIN HIEU di K nen: dieu kien duoc danh gia tai `s+K` thay vi
`s`. Giu nguyen ty le kich hoat, do dai cum, tu tuong quan - pha dung mot thu
dang tra loi: su khop thoi diem voi loi suat phia sau. Va no khong dung vao
phan phoi loi suat mot ly nao.

Ban that + N ban dich chay TRONG CUNG MOT EA, CUNG mot luot optimization, cung
chi phi va cung bo thuc thi. Neu ban that khong noi han len khoi dam dich thi
con so cua no la mot cuc tri cua giai doan.

Chay: python _placebo_tester.py [SYMBOL] [tu] [den]
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chay_tester_kho as C     # noqa: E402
from nhan import dich_mq5 as D  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

LAB = Path(__file__).resolve().parent

HE = ["mean_reversion_z5", "pine_ichimoku_cloud_close_duoi_ema144_close"]

#: Do dich (so nen). Chon so NGUYEN TO va rai deu de khong cong huong voi chu ky
#: nao cua chinh co che (5, 14, 20, 144, 200 la cac chu ky dang co mat).
#: 100 do dich -> p san = 1/101 = 0,0099. Voi 20 ban thi p nho nhat co the dat
#: la 1/21 = 0,0476 - dung bang nguong, tuc bo do het luc ngay tai cho quan
#: trong nhat [[hinh-dang-phai-hieu-chuan-bang-null]].
DICH = tuple(range(3, 405, 4))


def chay(symbol: str, tu: str, den: str) -> dict:
    kho = {c["ten"]: c for c in NP.doc_kho() if not NP.kiem_khai_bao(c)}
    goc = []
    for t in HE:
        c = kho.get(t) or next((v for k, v in kho.items() if k.startswith(t[:40])),
                               None)
        if c is None:
            print("KHONG TIM THAY co che '%s' trong kho" % t)
            continue
        goc.append(c)
    if not goc:
        return {"loi": "khong co co che nao de chay"}

    spec = []
    for c in goc:
        spec.append(dict(c, _dich=0, ten=c["ten"] + "@that"))
        for k in DICH:
            spec.append(dict(c, _dich=k, ten="%s@dich%d" % (c["ten"], k)))

    ma, dat = D.sinh_ea(spec, C.TEN_EA, khung="D1", them_mua_giu=True)
    src = C.XM_DATA / "MQL5" / "Experts" / (C.TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        return {"loi": loi}
    print("%d ban (%d that + %d dich), bien dich xong"
          % (len(dat), len(goc), len(dat) - len(goc) - 1))

    ten = "placebo_%s" % symbol
    ini = C.viet_ini(ten, symbol, len(dat), tu, den)
    for h in (".xml", ".htm"):
        f = C.XM_DATA / (ten + h)
        if f.exists():
            f.unlink()
    C.dong_terminal()
    t0 = time.time()
    subprocess.Popen([str(C.XM_EXE), "/config:%s" % ini])
    while time.time() - t0 < 1800:
        time.sleep(8)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                           capture_output=True, text=True)
        if "terminal64.exe" not in r.stdout:
            break

    hong = C.kiem_log_agent()
    if hong.startswith("TESTER KHONG CHAY DUOC"):
        return {"loi": hong}
    f = C.XM_DATA / (ten + ".xml")
    if not f.exists():
        return {"loi": "khong thay bang ket qua"}

    ket = {}
    for d in C.doc_xml(f):
        i = int(C._so(d.get("InpMaCoChe", -1), -1))
        if 0 <= i < len(dat):
            ket[dat[i]["ten"]] = {
                "lenh": int(C._so(d.get("Trades"))),
                "lai": C._so(d.get("Profit")),
                "sharpe": C._so(d.get("Sharpe Ratio")),
                "dd_pct": C._so(d.get("Equity DD %"))}

    ra = {"symbol": symbol, "tu": tu, "den": den, "ket": ket, "he": {}}
    print("\n%s  %s -> %s   (%d ban co ket qua)"
          % (symbol, tu, den, len(ket)))
    for c in goc:
        that = ket.get(c["ten"] + "@that")
        dich = [ket["%s@dich%d" % (c["ten"], k)] for k in DICH
                if "%s@dich%d" % (c["ten"], k) in ket]
        if not that or not dich:
            print("  %-40s THIEU BAN DE SO SANH" % c["ten"][:40])
            continue
        lai = sorted(x["lai"] for x in dich)
        hon = sum(1 for x in lai if x >= that["lai"])
        p = (hon + 1) / (len(lai) + 1)      # p nho nhat = 1/(K+1)
        ra["he"][c["ten"]] = {
            "that": that, "so_dich": len(lai),
            "dich_trung_vi": lai[len(lai) // 2], "dich_tot_nhat": lai[-1],
            "so_dich_hon_that": hon, "p": round(p, 4)}
        print("\n  %s" % c["ten"])
        print("    THAT       : %4d lenh  lai %8.2f  sharpe %5.2f  DD %.2f%%"
              % (that["lenh"], that["lai"], that["sharpe"], that["dd_pct"]))
        print("    %d ban DICH : lai trung vi %8.2f  tot nhat %8.2f"
              % (len(lai), lai[len(lai) // 2], lai[-1]))
        print("    so ban dich >= ban that: %d/%d   ->  p = %.4f"
              % (hon, len(lai), p))
        print("    %s" % ("DAT (ban that noi len khoi dam dich)" if p <= 0.05
                          else "KHONG DAT - con so cua ban that nam trong dam"))

    (LAB / "reports" / ("PLACEBO_%s.json" % symbol)).write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra


def main() -> int:
    ma = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
    tu = sys.argv[2] if len(sys.argv) > 2 else "2020.05.01"
    den = sys.argv[3] if len(sys.argv) > 3 else "2026.07.29"
    r = chay(ma, tu, den)
    if r.get("loi"):
        print("LOI:", r["loi"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
