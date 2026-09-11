# -*- coding: utf-8 -*-
"""_cao_mql5_sau.py - cao SAU vao MQL5 Code Base, nguon DUY NHAT co file chay duoc.

## VI SAO LAN NAY MOI CAO DUOC (08/09/2026)

Truoc hom nay `liet_ke_mql5` tra **0 muc o MOI trang** va doc y het "nguon da
het bai". Do ra HAI loi CHONG len nhau, ca hai deu im lang:

  1. `nhan/dns_vuot.BAN_DO` ep `www.mql5.com` sang IP cung `203.29.60.247` -
     IP do da cu va tra **403**. DNS that (`36.255.76.151`) tra **200**.
     Da sua o `tru/seeker._lay`: thu DNS that TRUOC, ban do chi la duong lui.
  2. Rieng trang DANH SACH (`/en/code/mt5/experts`) bi ngat ket noi trong khi
     trang CHI TIET (`/en/code/71075`) van 200. Cai nay **bat buoc WARP**.
     Voi WARP bat: 40 muc/trang, den trang 12 van con 32 muc.

Bai hoc de lai: `day_chuyen.kiem_mang()` bao `mql5: OK` trong ca hai truong hop
tren. No do TINH THONG MANG, khong do duong ma bo doc that su di.

## VI SAO UU TIEN NGUON NAY

Quy tac cua chu du an: **uu tien nguon CO FILE**. `.mq5`/`.ex5`/`.set` chay
tester duoc ngay; van xuoi thi phai qua ca chang boc roi van co the khong dich
duoc. Kho hien co 389 artifact ma nguon - trang 1 da phu het, nen phai cao SAU.

Chay: python _cao_mql5_sau.py [so_vong] [so_bai_moi_vong]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import ma_nguon as MN     # noqa: E402
from nhan import so as SO           # noqa: E402


def _dem() -> int:
    r = SO.mot("SELECT COUNT(*) n FROM artifact WHERE artifact_type='code'")
    return int(r["n"]) if r else 0


def main() -> int:
    so_vong = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    so_bai = int(sys.argv[2]) if len(sys.argv) > 2 else 40

    t0 = time.time()
    dau = _dem()
    print("=== CAO SAU MQL5 CODE BASE ===")
    print("artifact code truoc: %d\n" % dau, flush=True)

    tong = {"nhin_thay": 0, "tai_duoc": 0, "ghi_moi": 0}
    im = 0
    for v in range(1, so_vong + 1):
        try:
            r = MN.thu_thap(muc_can=("experts", "indicators"), so_bai=so_bai)
        except Exception as e:
            print("  vong %d LOI: %r" % (v, e), flush=True)
            break
        for k in tong:
            tong[k] += int(r.get(k, 0) or 0)
        print("  vong %2d | thay %3s | tai %3s | moi %3s | trang %s"
              % (v, r.get("nhin_thay"), r.get("tai_duoc"), r.get("ghi_moi"),
                 r.get("trang_da_lay")), flush=True)
        # "Het bai" phai la KHONG THAY GI trong nhieu vong lien tiep, khong phai
        # "khong co bai MOI" - trang cu day toan bai da co la chuyen binh thuong.
        im = im + 1 if not r.get("nhin_thay") else 0
        if im >= 3:
            print("  -> 3 vong lien khong thay muc nao, dung", flush=True)
            break

    cuoi = _dem()
    print("\n=== XONG %.0fs ===" % (time.time() - t0))
    print("  thay %(nhin_thay)d | tai %(tai_duoc)d | ghi moi %(ghi_moi)d" % tong)
    print("  artifact code: %d -> %d (+%d)" % (dau, cuoi, cuoi - dau))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
