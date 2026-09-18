# -*- coding: utf-8 -*-
"""Chung minh canary NHAY — chen lai dung hai loi cua phien 09/08 va xem no co bat khong.

Nguyen tac cua DeepSeek: mot bo canary chua tung bat duoc loi nao thi khong biet no co
tac dung hay khong. Phai co tinh lam hong roi kiem.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import brain_co_che as bc
import canary as c
import thu_nhieu_chien_luoc as t


def loi_1_phi_chi_khi_mua(vi_the, r, ngay, phi_nam):
    """LOI THAT #1: phi qua dem chi tinh khi DANG MUA."""
    spread = np.abs(np.diff(np.r_[0.0, vi_the])) * (t.SPREAD_BPS / 1e4)
    dem = np.where(vi_the > 0, phi_nam * ngay / 365.0, 0.0)     # <- loi
    return vi_the * r - spread - dem


def chuan_bi_lui(df):
    """LOI THAT #2: loi suat LUI thay vi tien."""
    o = df["open"].to_numpy()
    r = np.zeros(len(df))
    r[1:] = np.log(o[1:] / o[:-1])                               # <- loi
    ngay = np.r_[0, np.diff(df.index.values).astype("timedelta64[D]").astype(float)]
    return r, ngay


def main():
    tt = bc.nap_tap_sang()
    mau = {k: tt[k] for k in list(tt)[:8]}

    print("=== CHEN LOI #1: phi qua dem chi tinh cho chieu MUA ===")
    goc = c._loi
    c._loi = loi_1_phi_chi_khi_mua
    try:
        bat = 0
        for khoa, df in mau.items():
            ok, mo_ta = c.canary_luon_ban(df)
            if not ok:
                bat += 1
                if bat == 1:
                    print(f"    vi du {khoa}: {mo_ta}")
        print(f"  canary 'luon ban' bat duoc {bat}/{len(mau)} thi truong "
              f"-> {'NHAY' if bat == len(mau) else 'KHONG DU NHAY'}")
    finally:
        c._loi = goc

    print("\n=== CHEN LOI #2: loi suat LUI (nhin truoc mot bar) ===")
    goc2 = c._chuan_bi
    c._chuan_bi = chuan_bi_lui
    try:
        bat = 0
        for khoa, df in mau.items():
            ok, mo_ta = c.canary_tre_mot_bar(df)
            if not ok:
                bat += 1
                if bat == 1:
                    print(f"    vi du {khoa}: {mo_ta}")
        print(f"  canary 'tre 1 bar' bat duoc {bat}/{len(mau)} thi truong "
              f"-> {'NHAY' if bat >= len(mau) * 0.75 else 'KHONG DU NHAY'}")
    finally:
        c._chuan_bi = goc2

    print("\nKet luan: canary nao khong bat duoc loi cua chinh no thi phai viet lai.")


if __name__ == "__main__":
    main()
