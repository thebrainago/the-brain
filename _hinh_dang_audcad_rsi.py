# -*- coding: utf-8 -*-
"""Quet lan can tham so cua PASS DUY NHAT cua du an.

`AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` la gia thuyet duy nhat dat trang
thai PASS trong so cai (367 FAIL / 7 QUARANTINED / 1 PASS). Chua ai quet lan
can tham so cua no - cau hoi "cao nguyen hay cai gai" chua duoc hoi cho chinh
cai quan trong nhat.

Chay ca tren tai san GOC (AUDCAD.H4) lan tren tai san DICH sau khi chuyen
bang `ngoai_sinh.chuyen` (giu ty le kich hoat).
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

import do_on_dinh as OD                 # noqa: E402
from nhan import ngoai_sinh as NGS      # noqa: E402
from nhan import ngu_phap as NP         # noqa: E402


def bao(ten, tam, tai_san, khung):
    print(f"\n=== {ten} @ {tai_san}.{khung} ===", flush=True)
    print(f"    tam: {tam}", flush=True)
    r = OD.do_hinh_dang(ten, tam, tai_san, khung, luong=1)
    if not r.get("do_duoc"):
        print(f"    KHONG DO DUOC: {r.get('ly_do')} "
              f"(so_o={r.get('so_o')}, chay={r.get('chay_duoc')})", flush=True)
        return
    print(f"    HINH DANG: {r['hinh_dang']}", flush=True)
    print(f"    so o {r['so_o']} / chay {r['chay_duoc']} / KHAC NHAU "
          f"{r.get('so_o_khac_nhau')}", flush=True)
    print(f"    alpha tam {r['alpha_tam']}% | trung vi lan can "
          f"{r['trung_vi_lan_can']}% | tot nhat {r['o_tot_nhat']}%", flush=True)
    print(f"    o duong {r['ty_le_duong']}% | boi dinh {r['boi_dinh']} | "
          f"do doc mot buoc {r['do_doc_mot_buoc_pct']}%", flush=True)
    print(f"    tam la dinh: {r['tam_co_phai_dinh']}  ({r['giay']}s)", flush=True)
    print("    -- 8 o tot nhat --", flush=True)
    for o in r["o"][:8]:
        print(f"       {str(o['tham_so']):<40} alpha {o['alpha']:>7}%  "
              f"t {o['t']}  lenh {o.get('so_lenh')}", flush=True)
    print("    -- 5 o TE nhat --", flush=True)
    for o in r["o"][-5:]:
        print(f"       {str(o['tham_so']):<40} alpha {o['alpha']:>7}%  "
              f"t {o['t']}  lenh {o.get('so_lenh')}", flush=True)


def main():
    NP.nap_vao_mau()
    TAM = {"n": 14, "vao": 30, "ra_": 55}

    # 1. tren chinh tai san da PASS
    bao("rsi_dao_chieu", TAM, "AUDCAD", "H4")

    # 2. chuyen sang US500CASH (giu ty le kich hoat) roi quet lan can o do
    gt = next((g for g in NGS.he_da_pass()
               if g["ma"].startswith("AUDCAD.H4.rsi_dao_chieu")), None)
    if gt:
        for dich, khung in (("US500CASH", "H4"), ("XM_UK100CASH", "H4")):
            r = NGS.chuyen(gt, dich, khung)
            if not r:
                print(f"\n=== khong chuyen duoc sang {dich}.{khung} ===", flush=True)
                continue
            print(f"\n### CHUYEN sang {dich}.{khung}: {r['tham_so_goc']} -> "
                  f"{r['tham_so_moi']} (ty le {r['ty_le_goc']*100:.2f}% -> "
                  f"{r['ty_le_moi']*100:.2f}%)", flush=True)
            bao("rsi_dao_chieu", r["tham_so_moi"], dich, khung)


if __name__ == "__main__":
    main()
