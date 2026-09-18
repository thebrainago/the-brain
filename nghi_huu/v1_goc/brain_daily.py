# -*- coding: utf-8 -*-
"""
brain_daily.py - THE BRAIN chay DINH KY (moi lan mo may / moi ngay)
=====================================================================================
Moi lan chay: cap nhat du lieu -> thu thap nguon moi -> chay cua ai cho to hop CHUA TEST ->
cap nhat bao cao -> ghi nhat ky "co gi moi".

BON CHOT AN TOAN (doc ky - day la thu ngan no thanh co may sinh duong tinh gia):
  1. **KHONG BAO GIO TU TINH CHINH THAM SO.** No chi chay cac chien luoc DA DANG KY voi tham so
     da chot. Muon bo tham so khac = con nguoi phai dang ky tay, va viec do lam TANG tong so
     phep thu -> siet FDR cho tat ca.
  2. **FDR toan cuc tich luy.** Chay cang nhieu ngay, so phep thu cang lon, nguong cang chat.
     He thong tu chong lai chinh viec no chay nhieu. Day la diem khac biet voi moi "bot do chien
     luoc" thong thuong.
  3. **Gioi han thoi gian** (`--max-phut`): khong bao gio an het may.
  4. **Do uu tien THAP**: khong giat may khi dang lam viec khac/choi game.

CLI:
  python brain_daily.py                      # chay day du, gioi han 45 phut
  python brain_daily.py --max-phut 15        # chay ngan
  python brain_daily.py --khong-fetch        # bo qua thu thap nguon, chi chay cua ai
Xuat: reports/BRAIN_nhat_ky.md (co gi moi qua tung lan chay)
"""
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
REPORTS = HERE / "reports"
REPORTS.mkdir(exist_ok=True)
NHAT_KY = REPORTS / "BRAIN_nhat_ky.md"
PY = sys.executable

# Tai san chay cua ai moi lan. Giu NGAN - them tai san = them phep thu = siet FDR cho tat ca,
# nen chi them khi that su co ly do.
TAI_SAN = ["us500cash", "eurusd", "xauusd", "gbpusd", "usdjpy"]
KHUNG = ["d1"]


def ha_uu_tien():
    try:
        import psutil
        psutil.Process(os.getpid()).nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass


def chay(cmd, gioi_han_giay, ten):
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=gioi_han_giay)
        ok = r.returncode == 0
        return ok, f"{ten}: {'OK' if ok else 'LOI'} ({time.time()-t0:.0f}s)", (r.stdout or "")[-2000:]
    except subprocess.TimeoutExpired:
        return False, f"{ten}: HET GIO ({gioi_han_giay}s)", ""
    except Exception as e:
        return False, f"{ten}: LOI {str(e)[:60]}", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-phut", type=int, default=45)
    ap.add_argument("--khong-fetch", action="store_true")
    ap.add_argument("--tai-san", nargs="*", default=TAI_SAN)
    ap.add_argument("--khung", nargs="*", default=KHUNG)
    # LOI DA SUA 28/07: BRAIN.bat goi `--processes 10` nhung o day khong khai bao ->
    # argparse thoat ma 2 NGAY LAP TUC. Tuc file .bat CHUA BAO GIO chay duoc; dong nhat ky
    # duy nhat (27/07) la tu lan goi truc tiep brain_daily.py.
    ap.add_argument("--processes", type=int, default=16, help="so luong song song (80% may)")
    # Thu muc code de nap vao thu vien/ung vien moi ngay (nap_tay/ hoac thu muc khac).
    ap.add_argument("--kho-code", default=None, help="thu muc ma nguon de chay tang nap")
    args = ap.parse_args()

    ha_uu_tien()
    t0 = time.time()
    con = lambda: max(60, args.max_phut * 60 - (time.time() - t0))
    dong = [f"\n## {datetime.now():%Y-%m-%d %H:%M}", ""]
    print(f"=== THE BRAIN - chay dinh ky {datetime.now():%Y-%m-%d %H:%M} ===")

    # 1) cap nhat du lieu (Yahoo: nhanh, sach, KHONG lam phinh cache MT5 nhu bay #8)
    ok, tin, _ = chay([PY, "fetch_yahoo_multi.py", "--force"], min(con(), 600), "cap nhat du lieu Yahoo")
    print("  " + tin); dong.append(f"- {tin}")

    # 2) thu thap nguon moi
    if not args.khong_fetch:
        for lenh, ten in [(["brain_sources.py", "arxiv", "--so", "8"], "nguon arXiv"),
                          (["brain_sources.py", "github", "--so", "12"], "nguon GitHub"),
                          (["brain_sources.py", "nap-tay"], "nguon nap tay")]:
            ok, tin, _ = chay([PY] + lenh, min(con(), 300), ten)
            print("  " + tin); dong.append(f"- {tin}")

    # 2b) TANG NAP: dinh tuyen kho ma nguon -> thu vien / ung vien / chi de hoc.
    #     KHONG tu dang ky gi - chi ra danh sach ung vien can dien `ly_do_kinh_te`.
    kho = args.kho_code or str(HERE / "nap_tay")
    if Path(kho).exists() and any(Path(kho).rglob("*")):
        ok, tin, out = chay([PY, "brain_nap_kho.py", "--tu", kho], min(con(), 300),
                            "tang nap kho code")
        print("  " + tin); dong.append(f"- {tin}")
        for d in out.splitlines():
            if d.strip().startswith(("UNG", "THU", "CHI", "CHO")) or "ham rut duoc" in d:
                dong.append(f"  - `{d.strip()}`")

    # 3) chay cua ai
    ok, tin, out = chay([PY, "the_brain.py", "test", "--symbols"] + args.tai_san
                        + ["--tfs"] + args.khung + ["--placebo-iter", "80",
                                                    "--processes", str(args.processes)],
                        con(), "cua ai The Brain")
    print("  " + tin); dong.append(f"- {tin}")
    for d in out.splitlines():
        if "FDR TOAN CUC" in d or "song sot" in d:
            dong.append(f"  - `{d.strip()}`")
            print("  " + d.strip())

    dong.append("")
    cu = NHAT_KY.read_text(encoding="utf-8") if NHAT_KY.exists() else \
        ("# THE BRAIN - nhat ky chay dinh ky\n\n"
         "> Moi lan chay: cap nhat du lieu -> thu thap nguon -> chay cua ai -> cap nhat bao cao.\n"
         "> KHONG bao gio tu tinh chinh tham so. FDR toan cuc siet dan theo so phep thu tich luy.\n")
    NHAT_KY.write_text(cu + "\n".join(dong), encoding="utf-8")
    print(f"\nXong sau {(time.time()-t0)/60:.1f} phut -> reports/BRAIN_nhat_ky.md")


if __name__ == "__main__":
    main()

