# -*- coding: utf-8 -*-
"""
chay_lien_tuc.py - Chay noi tiep cac giai doan con lai cua phien, khong de trong
================================================================================
Strategy Tester khong cho 2 tien trinh dung chung thu muc du lieu, nen cac buoc
dung tester PHAI noi tiep. Cac buoc thuan CPU (quet gio 20 luong) cung de noi tiep
luon vi neu chay chen vao thi 20 agent tester bi tranh nhan.

Thu tu co chu y: buoc nao can MT5 API (tai bar) chay TRUOC khi tester chiem terminal.

Chay: python chay_lien_tuc.py
      python chay_lien_tuc.py --tu 3      (chay lai tu buoc 3)
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

GOC = Path(__file__).parent
NHAT_KY = GOC / "reports" / "nhat_ky_chay.txt"

BUOC = [
    ("1. hieu chuan quy uoc tc_StopDistance + tai bar H1 vang",
     [sys.executable, "vang_quet_gio.py", "--hieu-chuan"]),
    ("2. tester: luoi risk% va lot co dinh tren von 200/300/20.000",
     [sys.executable, "vang_von_nho.py", "--chay"]),
    ("3. doc luoi von nho",
     [sys.executable, "vang_von_nho.py", "--doc"]),
    ("4. placebo: quet ca 24 gio dat lenh (20 luong)",
     [sys.executable, "vang_quet_gio.py", "--quet"]),
    ("5. do he so quy doi khoang cach DCA cho BTC",
     [sys.executable, "dca_vang_btc.py", "--do-buoc"]),
    ("6. tester: DCA Am Duong tren vang + BTC, von 20.000",
     [sys.executable, "dca_vang_btc.py", "--chay", "--von", "20000"]),
    ("7. tester: DCA Am Duong tren vang + BTC, von 300",
     [sys.executable, "dca_vang_btc.py", "--chay", "--von", "300"]),
    ("8. doc ket qua DCA",
     [sys.executable, "dca_vang_btc.py", "--doc"]),
    ("9. tester: vang tung nam tren von 200/300 (bao cao .htm)",
     [sys.executable, "vang_von_nho.py", "--chay", "--nam"]),
]


def ghi(s):
    print(s, flush=True)
    with NHAT_KY.open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def main(tu):
    NHAT_KY.parent.mkdir(parents=True, exist_ok=True)
    ghi(f"\n===== bat dau {time.strftime('%Y-%m-%d %H:%M:%S')} =====")
    for i, (ten, lenh) in enumerate(BUOC, 1):
        if i < tu:
            continue
        ghi(f"\n----- BUOC {ten} -----")
        t0 = time.time()
        r = subprocess.run(lenh, cwd=GOC, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        ghi(r.stdout.rstrip())
        if r.returncode != 0:
            ghi(f"  !! ma loi {r.returncode}")
            ghi((r.stderr or "").strip()[-3000:])
            # khong dung ca chuoi: cac buoc sau doc lap voi nhau
        ghi(f"  ({time.time()-t0:.0f}s)")
    ghi(f"\n===== xong {time.strftime('%Y-%m-%d %H:%M:%S')} =====")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tu", type=int, default=1)
    main(ap.parse_args().tu)
