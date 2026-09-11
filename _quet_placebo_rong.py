# -*- coding: utf-8 -*-
"""_quet_placebo_rong.py - PLACEBO CHO TAT CA CO CHE QUA TRAIN/HOLDOUT, MOT LUOT.

Do 06/09: mot luot tester ton ~130 giay BOOT va gan nhu 0 giay tinh - 20 nhan
chay song song, 393 pass ton dung bang 1 pass. Nen **them pass la mien phi, them
LAN CHAY moi dat**. Chien luoc dung la nhoi het vao mot lan boot.

`InpDich` la THAM SO TOI UU HOA (khong phai sinh 101 ban ma), nen mot luot quet
duoc `co_che x do_dich`. 40 co che x 26 do dich = 1.040 pass = van mot lan boot.

Truoc bai nay: 40 co che qua train+holdout nhung chi 8 cai duoc thu placebo -
tuc "chi 1 co che song sot" that ra la "1 tren 8 cai kip thu".
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_tester_kho as C     # noqa: E402
from nhan import khoa_tester as KT
from nhan import dich_mq5 as D  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

MA = sys.argv[1].split(",") if len(sys.argv) > 1 else ["US100Cash"]
TU, DEN = "2016.06.01", "2026.07.29"
# 201 gia tri -> p san 1/201 = 0,005. Do 06/09: 1.066 pass ton 22 GIAY (20 nhan
# song song, EA da bien dich, terminal am), tuc ~48 pass/giay. Nen luoi day gap
# 8 lan chi ton ~3 phut/symbol - va p san 0,0385 cua luoi thua la thu duy nhat
# dang chan giua "dat" va "khong ket luan duoc"
# [[hinh-dang-phai-hieu-chuan-bang-null]].
DICH_MAX, DICH_BUOC = 400, 2


def ds_ung_vien():
    d = json.load(open("reports/TESTER_HOLDOUT_US100Cash.json", encoding="utf-8"))
    tr = {r["ten"]: r for r in d["train"] if r["lenh"] >= 25}
    ho = {r["ten"]: r for r in d["holdout"] if r["lenh"] >= 25}
    return [t for t in set(tr) & set(ho)
            if tr[t]["sharpe"] > 0 and ho[t]["sharpe"] > 0]


def viet_ini(ten, symbol, so_cc):
    p = C.XM_DATA / ("%s.ini" % ten)
    p.write_text("""[Tester]
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
Deposit=10000
Currency=USD
Leverage=1:500
ProfitInPips=0
Report=%s
ReplaceReport=1
ShutdownTerminal=1

[TesterInputs]
InpMaCoChe=0||0||1||%d||Y
InpDich=0||0||%d||%d||Y
InpLot=0.10||0.10||0||0||N
InpMagic=26090601||26090601||0||0||N
""" % (C.TEN_EA, symbol, C.KHUNG_CHAY, TU, DEN, ten, so_cc - 1,
       DICH_BUOC, DICH_MAX), encoding="utf-16")
    return p


#: `import` file nay TUNG chay ca luot tester: 07/09 mot dong `from
#: _quet_placebo_rong import ds_ung_vien` da khoi dong lai ban quet va GHI DE
#: `reports/PLACEBO_RONG.json` bon ma bang ban mot ma. Than script phai nam
#: trong guard, khong duoc de o muc module.
if __name__ == "__main__":
    ten_uv = ds_ung_vien()
    kho = {c["ten"]: c for c in NP.doc_kho() if not NP.kiem_khai_bao(c)}
    spec = [kho[t] for t in ten_uv if t in kho]
    print("%d co che qua train+holdout -> dich duoc %d" % (len(ten_uv), len(spec)))

    ma, dat = D.sinh_ea(spec, C.TEN_EA, khung="D1", them_mua_giu=True)
    src = C.XM_DATA / "MQL5" / "Experts" / (C.TEN_EA + ".mq5")
    src.write_text(ma, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        print("LOI:", loi)
        raise SystemExit(1)
    so_dich = len(range(0, DICH_MAX + 1, DICH_BUOC))
    print("  bien dich xong: %d co che x %d do dich = %d pass/symbol"
          % (len(dat), so_dich, len(dat) * so_dich))

    gop = {}
    for symbol in MA:
        ten = "prong_%s" % symbol
        ini = viet_ini(ten, symbol, len(dat))
        for h in (".xml", ".htm"):
            f = C.XM_DATA / (ten + h)
            if f.exists():
                f.unlink()
        C.dong_terminal()
        print("\n=== %s ..." % symbol, flush=True)
        t0 = time.time()
        KT.phong(C.XM_EXE, ini, tran=3600, nhip=10,
                 dong_truoc=C.dong_terminal, viec="quet_placebo_rong %s" % symbol)
        print("  %.0fs" % (time.time() - t0), flush=True)

        o = {}
        for d in C.doc_xml(C.XM_DATA / (ten + ".xml")):
            i = int(C._so(d.get("InpMaCoChe", -1), -1))
            k = int(C._so(d.get("InpDich", -1), -1))
            if 0 <= i < len(dat) and k >= 0:
                o.setdefault(dat[i]["ten"], {})[k] = C._so(d.get("Profit"))
        ket = {}
        for t, v in o.items():
            if 0 not in v or len(v) < 5:
                continue
            that = v[0]
            dich = sorted(x for k, x in v.items() if k > 0)
            hon = sum(1 for x in dich if x >= that)
            ket[t] = {"that": that, "so_dich": len(dich),
                      "trung_vi": dich[len(dich) // 2],
                      "p": round((hon + 1) / (len(dich) + 1), 4)}
        gop[symbol] = ket
        dat_p = sorted((t for t, x in ket.items() if x["p"] <= 0.05),
                       key=lambda t: ket[t]["p"])
        print("  %d co che co ket qua | DAT placebo (p<=0,05): %d"
              % (len(ket), len(dat_p)))
        for t in dat_p[:15]:
            x = ket[t]
            print("    %-42s that %8.2f  dich_tv %8.2f  p=%.4f"
                  % (t[:42], x["that"], x["trung_vi"], x["p"]))

    Path("reports/PLACEBO_RONG.json").write_text(
        json.dumps(gop, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> reports/PLACEBO_RONG.json")
