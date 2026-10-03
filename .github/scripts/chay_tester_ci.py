# -*- coding: utf-8 -*-
"""Chay MT5 Strategy Tester tren runner Windows cua GitHub Actions.

Ban RUT GON cua `chay_tester_kho.py` cho moi truong CI: khong co `nao.db`,
khong co kho co che, khong ghi vao so. No chi lam mot viec - chay mot luot
tester va de lai bao cao de buoc sau kiem.

## VI SAO TACH RA THAY VI GOI `chay_tester_kho`

`chay_tester_kho` ghi vao `nao.db`, doc kho co che, va giu KHOA TESTER cua may
chu du an. Tren runner khong co thu nao trong so do, va quan trong hon: khoa
tester o day la VO NGHIA va co hai - moi runner la mot may rieng voi mot
terminal rieng, nen khoa chi lam cac job cho nhau vo co.

## CHO DE SAI NHAT: TAI LICH SU

Terminal vua cai xong khong co bar nao. Tester tu tai khi chay, nhung neu tai
that bai (mang, san tu choi, sai server) thi no van chay - tren mot chuoi
RONG - va tra ve mot bao cao 0 deal. Bao cao do doc y het "co che khong bao
gio kich hoat".

Nen buoc `kiem_ket_qua_ci.py` doi bao cao phai co it nhat mot deal, va khong
co thi goi ten dung: `CHUA_DO_DUOC`.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

RA = Path("ci_out")


def viet_ini(dich: Path, ten: str, ma: str, khung: str, tu: str, den: str,
             ea: str) -> Path:
    """File `.ini` cho tester, gom ca khoi `[Common]` de terminal TU dang nhap.

    Khong co khoi `[Common]` thi tester chet voi *"tester not started because
    the account is not specified"* - mot thong bao khong noi gi ve dang nhap.
    Bay nay da ghi trong `nhan/bi_mat.khoi_common_ini`.
    """
    p = dich / f"{ten}.ini"
    p.write_text(
        "[Common]\n"
        f"Login={os.environ['MT5_LOGIN']}\n"
        f"Password={os.environ['MT5_PASSWORD']}\n"
        f"Server={os.environ['MT5_SERVER']}\n"
        "ProxyEnable=0\n"
        "CertInstall=0\n"
        "NewsEnable=0\n\n"
        "[Tester]\n"
        f"Expert={ea}\n"
        f"Symbol={ma}\n"
        f"Period={khung}\n"
        # Model=2 (gia mo nen) la MUC SANG LOC. `CLAUDE.md`: *"Model=1 cua MT5
        # noi doi khi TP < 2x bien do nen M1. Phai chay Model=0/4."* Ket luan
        # cuoi phai chay lai o Model=0 hoac 4, khong duoc dung con so tu day.
        "Model=2\n"
        "ExecutionMode=0\n"
        "Optimization=0\n"
        f"FromDate={tu}\n"
        f"ToDate={den}\n"
        "ForwardMode=0\n"
        "Deposit=10000\n"
        "Currency=USD\n"
        "Leverage=1:500\n"
        "ProfitInPips=0\n"
        f"Report={ten}\n"
        "ReplaceReport=1\n"
        "ShutdownTerminal=1\n",
        encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--terminal", required=True)
    ap.add_argument("--ma", required=True)
    ap.add_argument("--khung", required=True)
    ap.add_argument("--tu", required=True)
    ap.add_argument("--den", required=True)
    ap.add_argument("--ea", default="Examples\\MACD\\MACD Sample.ex5",
                    help="EA co san cua MT5; doi sang EA cua du an khi da bien dich")
    a = ap.parse_args()

    for k in ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"):
        if not os.environ.get(k):
            print(f"CHUA_DO_DUOC: thieu bien moi truong {k}")
            return 1

    RA.mkdir(exist_ok=True)
    term = Path(a.terminal)
    ten = f"{a.ma}_{a.khung}"
    ini = viet_ini(RA, ten, a.ma, a.khung, a.tu, a.den, a.ea)

    print(f"chay tester: {a.ma} {a.khung} {a.tu}..{a.den}")
    r = subprocess.run([str(term), f"/config:{ini.resolve()}"],
                       capture_output=True, text=True, timeout=5400)
    print("ma thoat:", r.returncode)
    if r.stdout:
        print(r.stdout[-3000:])
    if r.stderr:
        print(r.stderr[-3000:], file=sys.stderr)

    # Terminal copy bao cao vao thu muc cua no, khong vao cwd. Gom lai de
    # buoc sau (va `upload-artifact`) nhin thay.
    for goc in (term.parent, term.parent / "Tester", Path.cwd()):
        for mau in ("*.htm", "*.html", "*.xml", "*.log"):
            for f in goc.glob(mau):
                try:
                    (RA / f.name).write_bytes(f.read_bytes())
                except OSError:
                    pass

    # Ma thoat cua terminal KHONG dang tin: no tra 0 ca khi tester khong chay
    # gi. Phan quyet nam o `kiem_ket_qua_ci.py`, doc chinh bao cao.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
