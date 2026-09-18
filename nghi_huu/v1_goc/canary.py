# -*- coding: utf-8 -*-
"""
canary.py — CHIM HOANG MAI TRONG MO THAN
=====================================================================================
Chay MOI LAN sua engine backtest. Cac chien luoc o day tam thuong den muc ket qua
TINH DUOC BANG TAY. Neu mot cai lech, engine hong — dung ngay, dung tinh p-value nao.

Vi sao can: trong phien 09/08/2026 engine mac HAI loi nghiem trong, va ca hai chi bi
bat vi CON SO QUA DEP, tuc bang truc giac cua nguoi:
  1. Phi qua dem chi tinh khi DANG MUA -> chien luoc co chieu ban duoc tang ~2%/nam
     alpha gia. Chiem 63% cua "edge" quan sat duoc.
  2. Loi suat LUI ghep voi dich mot bar -> do tre bang KHONG, nhin truoc tron mot bar.
     Thoi alpha len +26,8 diem phan tram/nam, t tu -0,74 thanh +10,05.

Neu ket qua chi la 16/28 thay vi 24/28 thi ca hai loi da lot. Truc giac khong phai cong.

  python canary.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import brain_co_che as bc
import thu_nhieu_chien_luoc as t

DUNG_SAI = 1e-9


def _chuan_bi(df):
    o = df["open"].to_numpy()
    r = np.zeros(len(df))
    r[:-1] = np.log(o[1:] / o[:-1])          # loi suat TIEN: open[i] -> open[i+1]
    ngay = np.r_[0, np.diff(df.index.values).astype("timedelta64[D]").astype(float)]
    return r, ngay


def _loi(vi_the, r, ngay, phi_nam):
    spread = np.abs(np.diff(np.r_[0.0, vi_the])) * (t.SPREAD_BPS / 1e4)
    dem = np.abs(vi_the) * phi_nam * ngay / 365.0
    return vi_the * r - spread - dem


# ---------------------------------------------------------------------------
# CAC CANARY
# ---------------------------------------------------------------------------

def canary_luon_mua(df):
    """Luon mua 100% -> PHAI bang dung mua-giu CFD, sai so 1e-9.
    Bat: sai sot trong ke toan chi phi hoac trong cach ghep vi the voi loi suat."""
    r, ngay = _chuan_bi(df)
    v = np.ones(len(df))
    he = np.nansum(_loi(v, r, ngay, t.PHI_CFD))
    mg = np.nansum(_loi(np.ones(len(df)), r, ngay, t.PHI_CFD))
    return abs(he - mg) < DUNG_SAI, f"he {he:+.6f} vs mua-giu {mg:+.6f}"


def canary_luon_ban(df):
    """Luon ban 100% -> PHAI bang -(loi suat tho) tru phi giu, KHONG duoc mien phi.
    Bat: dung loi cua phien 09/08 — phi qua dem chi tinh cho chieu mua."""
    r, ngay = _chuan_bi(df)
    v = -np.ones(len(df))
    he = np.nansum(_loi(v, r, ngay, t.PHI_CFD))
    cho = -np.nansum(r) - t.PHI_CFD * np.nansum(ngay) / 365.0 - t.SPREAD_BPS / 1e4
    return abs(he - cho) < 1e-6, f"he {he:+.6f} vs cho doi {cho:+.6f}"


def canary_dung_ngoai(df):
    """Khong bao gio vao lenh -> PHAI bang dung 0 (chua tinh lai tien mat).
    Bat: chi phi bi ap cho vi the rong."""
    r, ngay = _chuan_bi(df)
    he = np.nansum(_loi(np.zeros(len(df)), r, ngay, t.PHI_CFD))
    return abs(he) < DUNG_SAI, f"he {he:+.9f}, phai bang 0"


def canary_tre_mot_bar(df):
    """DAU HIEU NHIN TRUOC — dat DUNG BIEN mot bar.

    Ban dau toi viet canary nay bang dau cua loi suat open-open bar truoc. No TRUOT:
    tu no da co san hai bar tre nen lech mot bar cua engine khong cham toi. Mutation
    test bat duoc (0/8) — day la ly do phai kiem chinh cai kiem.

    Ban dung: tin hieu = HUONG CUA CHINH BAR VUA DONG, `sign(close[i-1] - open[i-1])`.
    Day la thong tin hoan toan hop le tai close[i-1].
      - Engine dung : vi the do an loi suat open[i] -> open[i+1]  -> alpha ~ 0.
      - Engine lech mot bar: no an open[i-1] -> open[i], ma khoang do CHUA
        close[i-1]-open[i-1] — tuc chinh cai tin hieu — -> alpha khong lo.
    Do la khac biet toi thieu du de bat, va no bat dung mot bar."""
    r, ngay = _chuan_bi(df)
    o, c = df["open"].to_numpy(), df["close"].to_numpy()
    huong = np.sign(c - o)                    # biet o close cua chinh bar do
    v = np.r_[0.0, huong[:-1]]                # ap cho bar ke tiep
    he = _loi(v, r, ngay, 0.0)
    mg = _loi(np.ones(len(df)), r, ngay, 0.0)
    a, tt = t.alpha_newey_west(he, mg)
    return (abs(tt) < 4 if np.isfinite(tt) else True), f"alpha {a*100:+.2f}%/nam, t {tt:+.2f}"


def canary_biet_truoc(df):
    """DAU HIEU ENGINE CHET. Tin hieu = dau cua chinh loi suat sap an (biet truoc hoan
    toan). PHAI ra alpha KHONG LO. Neu KHONG khong lo thi engine dang khong noi vi the
    voi loi suat dung cach — moi ket qua am tinh deu vo nghia."""
    r, ngay = _chuan_bi(df)
    v = np.sign(r)
    he = _loi(v, r, ngay, 0.0)
    mg = _loi(np.ones(len(df)), r, ngay, 0.0)
    a, tt = t.alpha_newey_west(he, mg)
    return (tt > 20 if np.isfinite(tt) else False), f"alpha {a*100:+.1f}%/nam, t {tt:+.1f}"


CANARY = {
    "luon mua 100%  = mua-giu": canary_luon_mua,
    "luon ban 100%  co tra phi": canary_luon_ban,
    "dung ngoai     = dung 0": canary_dung_ngoai,
    "tre 1 bar      alpha ~ 0  [bat NHIN TRUOC]": canary_tre_mot_bar,
    "biet truoc     alpha KHONG LO  [bat ENGINE CHET]": canary_biet_truoc,
}


def main():
    tt = bc.nap_tap_sang()
    mau = {k: tt[k] for k in list(tt)[:8]}          # 8 thi truong la du de bat loi
    print(f"Chay {len(CANARY)} canary tren {len(mau)} thi truong\n")

    hong = []
    for ten, ham in CANARY.items():
        dat, chi_tiet = [], []
        for khoa, df in mau.items():
            try:
                ok, mo_ta = ham(df)
            except Exception as e:
                ok, mo_ta = False, f"LOI {str(e)[:60]}"
            dat.append(ok)
            if not ok:
                chi_tiet.append(f"{khoa}: {mo_ta}")
        n_ok = sum(dat)
        dau = "OK  " if n_ok == len(dat) else "HONG"
        print(f"  [{dau}] {ten:<46} {n_ok}/{len(dat)}")
        for c in chi_tiet[:3]:
            print(f"           {c}")
        if n_ok < len(dat):
            hong.append(ten)

    print()
    if hong:
        print("=" * 68)
        print("ENGINE HONG — KHONG DUOC TIN BAT KY KET QUA NAO CHO TOI KHI SUA:")
        for h in hong:
            print(f"  - {h}")
        print("=" * 68)
        return 1
    print("Tat ca canary dat. Engine dung duoc.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
