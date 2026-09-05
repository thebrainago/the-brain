# -*- coding: utf-8 -*-
"""Xac minh BAN DO CHI PHI LIEN SAN - muc 6 ban giao 04/09 ("chua xac minh").

Bang `SO_CHENH_LECH_CHI_PHI.md` tu ghi dieu kien de no sai:
*"hai symbol khong that su cung phoi nhiem (kiem contract size)"*. Day la buoc
kiem do. Khong can mo terminal: `config/chi_phi_do.json` da luu du gia, point,
contract_size, swap_mode va ten may chu cua tung symbol tung san.

BON PHEP THU, xep theo suc manh:

  1. GIA LECH. Hai symbol cung mot phoi nhiem kinh te thi gia phai gan bang
     nhau. Lech qua 2% la ho KHONG cung phoi nhiem (hoac khac don vi hop dong,
     hoac mot ben la hop dong tuong lai da noi chuoi). Day la phep thu manh
     nhat va re nhat.
  2. SWAP_MODE la ma cong thuc. Mode 9 khong co trong tai lieu API MT5 nhung
     FXCE tra ve - dong quy doi cua no chua tung duoc doi chieu voi sao ke.
     Hai ben khac nhom cong thuc thi hai con so khong so sanh truc tiep duoc.
  3. MAY CHU DEMO. Tra cuu theo ten tho co the lang le lay ban ghi cua
     `MetaQuotes-Demo`. Bieu phi demo khong phai bieu phi that.
  4. CONTRACT SIZE lech nhieu lan -> `%/nam` chi dung neu buoc quy doi da chia
     dung. Danh dau de kiem tay.

KHONG ket luan "sai" khi mot phep thu truot: ket luan la **do tin bi ha**, va
dong do khong duoc dung de chuyen tien truoc khi doi chieu SAO KE THAT.
"""
from __future__ import annotations

import json
import sys
import warnings

sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

from nhan import chi_phi as CP

NGUONG_GIA = 0.02        # gia lech qua 2% = khong cung phoi nhiem
NGUONG_CHENH = 1.0       # chi xet dong chenh >= 1 diem %/nam
MODE_LA = {9}            # swap_mode ngoai chuan API
#: Dau hieu may chu KHONG PHAI tai khoan that. "demo" khong du: Exness dat ten
#: `Exness-MT5Trial14` va no lot qua phep thu o ban dau tien (05/09).
DAU_HIEU_THU = ("demo", "trial", "practice", "test", "contest")


def kiem_mot(b: dict, kho: dict) -> dict:
    ten_san = b["symbol_tung_san"]
    ban = {}
    for san, sym in ten_san.items():
        ban[san] = (kho.get(san) or {}).get(sym.upper())
    thieu = [s for s, v in ban.items() if not v]

    co = {s: v for s, v in ban.items() if v}
    canh: list[str] = []

    gia = {s: v.get("gia_luc_do") for s, v in co.items()}
    lech_gia = None
    if len(gia) >= 2 and all(g for g in gia.values()):
        lo, hi = min(gia.values()), max(gia.values())
        lech_gia = (hi - lo) / lo if lo else None
        if lech_gia is not None and lech_gia > NGUONG_GIA:
            canh.append("GIA LECH %.1f%% (%s)"
                        % (lech_gia * 100,
                           ", ".join("%s %.5g" % kv for kv in gia.items())))

    mode = {s: v.get("swap_mode") for s, v in co.items()}
    if len(set(mode.values())) > 1:
        canh.append("SWAP_MODE khac nhau: %s"
                    % ", ".join("%s=%s" % kv for kv in mode.items()))
    la = [s for s, m in mode.items() if m in MODE_LA]
    if la:
        canh.append("SWAP_MODE ngoai chuan (%s) o: %s"
                    % (",".join(str(MODE_LA)), ",".join(la)))

    demo = [s for s, v in co.items()
            if any(t in str(v.get("nguon", "")).lower() for t in DAU_HIEU_THU)]
    if demo:
        canh.append("BAN GHI TU MAY CHU THU/DEMO: %s"
                    % ", ".join("%s=%s" % (s, co[s].get("nguon")) for s in demo))

    cs = {s: v.get("contract_size") for s, v in co.items()}
    if len(cs) >= 2 and all(cs.values()):
        lo, hi = min(cs.values()), max(cs.values())
        if hi / lo >= 2:
            canh.append("CONTRACT SIZE lech %.0fx: %s"
                        % (hi / lo, ", ".join("%s=%g" % kv for kv in cs.items())))

    if thieu:
        canh.append("KHONG TIM THAY ban ghi: %s" % ",".join(thieu))

    return {"phoi_nhiem": b["phoi_nhiem"], "chenh": b["chenh_diem_pct_nam"],
            "kenh_re": b["kenh_re"], "kenh_dat": b["kenh_dat"],
            "lech_gia_pct": (round(lech_gia * 100, 2) if lech_gia is not None else None),
            "canh_bao": canh, "dat": not canh}


def chay() -> None:
    kho = CP._doc_luu().get("_theo_san", {})
    print("san co ban ghi: %s" % ", ".join("%s(%d sym)" % (s, len(v))
                                           for s, v in kho.items()))
    bang = [b for b in CP.bang_chenh_lech()
            if b["chenh_diem_pct_nam"] >= NGUONG_CHENH and b["tin_cay"] == "CAO"]
    print("dong 'chenh dang ke, do tin CAO' can xac minh: %d\n" % len(bang))

    kq = [kiem_mot(b, kho) for b in bang]
    dat = [k for k in kq if k["dat"]]
    truot = [k for k in kq if not k["dat"]]

    print("=" * 78)
    print("DAT ca 4 phep thu : %d/%d" % (len(dat), len(kq)))
    print("HA DO TIN        : %d/%d" % (len(truot), len(kq)))
    print()
    if truot:
        print("--- HA DO TIN (khong dung de chuyen tien truoc khi doi sao ke) ---")
        for k in sorted(truot, key=lambda z: -z["chenh"])[:25]:
            print("  %-10s chenh %+8.2f  %s -> %s"
                  % (k["phoi_nhiem"], k["chenh"], k["kenh_re"], k["kenh_dat"]))
            for c in k["canh_bao"]:
                print("      ! %s" % c[:100])
    print()
    if dat:
        print("--- CON DUNG sau xac minh (top 20 theo chenh) ---")
        print("  %-12s %10s %10s %10s %10s"
              % ("phoi nhiem", "chenh %/nam", "gia lech%", "re", "dat"))
        for k in sorted(dat, key=lambda z: -z["chenh"])[:20]:
            print("  %-12s %10.2f %10s %10s %10s"
                  % (k["phoi_nhiem"], k["chenh"],
                     ("%.2f" % k["lech_gia_pct"]) if k["lech_gia_pct"] is not None
                     else "-", k["kenh_re"], k["kenh_dat"]))
    json.dump(kq, open("reports/xac_minh_chenh_lech.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nchi tiet -> reports/xac_minh_chenh_lech.json")
    print("Con lai mot buoc KHONG lam duoc o day: doi chieu SAO KE THAT sau mot")
    print("dem giu vi the. So tu `symbol_info` la bang gia niem yet, khong phai")
    print("bang chung ve so tien bi tru.")


if __name__ == "__main__":
    chay()
