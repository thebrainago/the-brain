# -*- coding: utf-8 -*-
"""canary.py - CHIM HOANG MAI. Gac chinh cai engine dang duoc dung.

Ban cu (`canary.py` o goc du an) da chung minh la nhay, nhung KHONG duoc noi
vao `lab/` - do la mot trong nhung phat hien nang nhat cua bao cao 15/08.
File nay gac `nhan/mo_phong.py`, va tru QUANTLAB goi no TRUOC moi lo viec.

Ky vong cua tung ca deu TINH DUOC BANG TAY, doc lap voi engine. Neu mot ca
lech -> engine hong -> DUNG, khong tinh p-value nao.

Hai loi that da tung xay ra (09/08/2026), ca hai chi bi bat vi con so qua dep:
  1. Phi qua dem chi tinh khi DANG MUA -> tang ~2 %/nam alpha gia cho chien
     luoc co chieu ban. Chiem 63% "edge" quan sat duoc.  -> ca `luon ban` bat.
  2. Loi suat ghep lech mot bar -> nhin truoc tron mot bar. Thoi alpha
     +26,8 diem %/nam, t tu -0,74 len +10,05.            -> ca `tre 1 bar` bat.

Va canary PHAI TU CHUNG MINH LA NHAY (`--tu-kiem`): chen lai dung hai loi do
roi kiem xem no co gao len khong. Mot bo canary chua tung bat duoc loi nao thi
khong biet no co tac dung hay khong.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import chi_phi as CP, du_lieu as DL, do_luong as DO, mo_phong as MP
else:
    from . import chi_phi as CP, du_lieu as DL, do_luong as DO, mo_phong as MP

DUNG_SAI = 1e-9
TAP_MAC_DINH = ["EURCAD", "GBPCAD", "AUDNZD", "EURGBP"]
KHUNG = "H1"


def _so_ngay(index) -> np.ndarray:
    ngay = np.zeros(len(index))
    if len(index) > 1:
        ngay[1:] = np.diff(index.to_numpy()).astype("timedelta64[s]").astype(float) / 86400.0
    return ngay


# --------------------------------------------------------------- CAC CANARY
def ca_luon_mua(df, cp, ma):
    """Luon mua 100%. Ky vong tinh tay:
        sum(r) - spread[0] - truot[0] - phi_mua * tong_ngay/365
    Bat: sai sot ke toan chi phi, hoac ghep vi the voi loi suat sai cho."""
    kq = MP.chay(df, np.ones(len(df)), cp, ma=ma, da_dich=True)
    r = MP._loi_suat_tien(df)
    sp = cp.spread_mang(df.index)
    cho = (float(np.sum(r)) - float(sp[0]) - cp.truot_gia_frac
           - cp.phi_nam_mua * float(np.sum(_so_ngay(df.index))) / 365.0)
    thuc = float(np.sum(kq.loi))
    return abs(thuc - cho) < 1e-9, f"thuc {thuc:+.9f} vs tay {cho:+.9f}"


def ca_luon_ban(df, cp, ma):
    """Luon ban 100%. Ky vong tinh tay:
        -sum(r) - spread[0] - truot[0] - phi_BAN * tong_ngay/365
    Bat DUNG loi that #1: phi qua dem chi tinh cho chieu mua."""
    kq = MP.chay(df, -np.ones(len(df)), cp, ma=ma, da_dich=True)
    r = MP._loi_suat_tien(df)
    sp = cp.spread_mang(df.index)
    cho = (-float(np.sum(r)) - float(sp[0]) - cp.truot_gia_frac
           - cp.phi_nam_ban * float(np.sum(_so_ngay(df.index))) / 365.0)
    thuc = float(np.sum(kq.loi))
    return abs(thuc - cho) < 1e-9, f"thuc {thuc:+.9f} vs tay {cho:+.9f}"


def ca_dung_ngoai(df, cp, ma):
    """Khong bao gio vao lenh -> phai bang DUNG 0.
    Bat: chi phi bi ap cho vi the rong."""
    kq = MP.chay(df, np.zeros(len(df)), cp, ma=ma, da_dich=True)
    thuc = float(np.sum(kq.loi))
    return abs(thuc) < DUNG_SAI, f"thuc {thuc:+.12f}, phai bang 0"


def ca_tre_mot_bar(df, cp, ma):
    """DAU HIEU NHIN TRUOC - dat DUNG BIEN mot bar.

    Tin hieu = huong cua chinh bar vua dong: sign(close[i] - open[i]).
    Day la thong tin hop le tai close[i].
      - Engine dung: vi the do an loi suat open[i+1] -> open[i+2] -> alpha ~ 0.
      - Engine quen dich: no an open[i] -> open[i+1], ma khoang do CHUA
        close[i]-open[i] - tuc chinh cai tin hieu -> alpha khong lo.
    """
    o, c = df["open"].to_numpy(), df["close"].to_numpy()
    th = np.sign(c - o)
    rong = CP.MoHinhChiPhi(ma=ma, spread_frac_chung=0.0, truot_gia_frac=0.0)
    kq = MP.chay(df, th, rong, ma=ma)
    bh = MP.mua_giu(df, rong, ma=ma)
    a, t, _ = DO.alpha_newey_west(kq.loi, bh.loi, df.index)
    ok = (abs(t) < 4) if np.isfinite(t) else True
    return ok, f"alpha {a*100:+.2f}%/nam, t {t:+.2f} (phai |t| < 4)"


def ca_biet_truoc(df, cp, ma):
    """DAU HIEU ENGINE CHET. Tin hieu = dau cua chinh loi suat sap an.
    PHAI ra alpha khong lo. Neu KHONG khong lo thi engine dang khong noi vi the
    voi loi suat - va moi ket luan AM TINH tu no deu vo nghia."""
    r = MP._loi_suat_tien(df)
    th = np.zeros(len(df))
    th[:-1] = np.sign(r[1:])          # engine dich 1 -> v[i] = sign(r[i])
    rong = CP.MoHinhChiPhi(ma=ma, spread_frac_chung=0.0, truot_gia_frac=0.0)
    kq = MP.chay(df, th, rong, ma=ma)
    bh = MP.mua_giu(df, rong, ma=ma)
    a, t, _ = DO.alpha_newey_west(kq.loi, bh.loi, df.index)
    ok = (t > 20) if np.isfinite(t) else False
    return ok, f"alpha {a*100:+.1f}%/nam, t {t:+.1f} (phai t > 20)"


CANARY = {
    "luon mua 100%   = cong thuc tay": ca_luon_mua,
    "luon ban 100%   CO tra phi giu  [bat PHI BAT DOI XUNG]": ca_luon_ban,
    "dung ngoai      = dung 0": ca_dung_ngoai,
    "tre 1 bar       alpha ~ 0       [bat NHIN TRUOC]": ca_tre_mot_bar,
    "biet truoc      alpha KHONG LO  [bat ENGINE CHET]": ca_biet_truoc,
}


# --------------------------------------------------------------------- CHAY
def nap_tap(tap=None, khung=KHUNG, so_bar=12000):
    ds = DL.kho()
    tap = [t for t in (tap or TAP_MAC_DINH) if t in ds]
    ra = {}
    for ma in tap:
        try:
            df = DL.nap(ma, khung)
            if len(df) > so_bar:
                df = df.iloc[-so_bar:]
            if len(df) > 500:
                ra[ma] = df
        except Exception:
            continue
    return ra


def chay_het(tap=None, im_lang=False) -> tuple[bool, dict]:
    mau = nap_tap(tap)
    if not mau:
        return False, {"loi": "khong nap duoc tai san nao de kiem canary"}
    bao = {"tai_san": list(mau), "ket_qua": {}, "hong": []}
    if not im_lang:
        print(f"Chay {len(CANARY)} canary tren {len(mau)} tai san ({KHUNG})\n")
    for ten, ham in CANARY.items():
        dat, chi_tiet = [], []
        for ma, df in mau.items():
            cp = CP.tu_du_lieu(ma, df)
            try:
                ok, mo_ta = ham(df, cp, ma)
            except Exception as e:
                ok, mo_ta = False, f"LOI {type(e).__name__}: {str(e)[:70]}"
            dat.append(bool(ok))
            if not ok:
                chi_tiet.append(f"{ma}: {mo_ta}")
        n_ok = sum(dat)
        bao["ket_qua"][ten] = {"dat": n_ok, "tong": len(dat), "chi_tiet": chi_tiet[:3]}
        if not im_lang:
            print(f"  [{'OK  ' if n_ok == len(dat) else 'HONG'}] {ten:<56} {n_ok}/{len(dat)}")
            for c in chi_tiet[:2]:
                print(f"         {c}")
        if n_ok < len(dat):
            bao["hong"].append(ten)
    lanh = not bao["hong"]
    if not im_lang:
        print()
        if lanh:
            print("Tat ca canary dat. Engine dung duoc.")
        else:
            print("=" * 70)
            print("ENGINE HONG - KHONG DUOC TIN BAT KY KET QUA NAO CHO TOI KHI SUA:")
            for h in bao["hong"]:
                print("  -", h)
            print("=" * 70)
    return lanh, bao


# ------------------------------------------------- CANARY TU CHUNG MINH LA NHAY
def tu_kiem() -> tuple[bool, dict]:
    """MUTATION AUDIT (THIET_KE muc 12): chen lai dung hai loi that roi kiem
    xem canary co gao len khong. KHONG gao = day bay khong hoat dong."""
    mau = nap_tap()
    if not mau:
        return False, {"loi": "khong co du lieu"}
    ra = {"ca": {}}

    goc_phi = CP.MoHinhChiPhi.phi_giu_mang
    goc_chay = MP.chay

    # ---- LOI 1: phi qua dem chi tinh cho chieu MUA -------------------------
    def phi_thien_vi(self, index, huong, lai_suat_nam=None):
        return goc_phi(self, index, np.clip(huong, 0, 1), lai_suat_nam)

    CP.MoHinhChiPhi.phi_giu_mang = phi_thien_vi
    bat = 0
    for ma, df in mau.items():
        cp = CP.tu_du_lieu(ma, df)
        ok, _ = ca_luon_ban(df, cp, ma)
        bat += (not ok)
    CP.MoHinhChiPhi.phi_giu_mang = goc_phi
    ra["ca"]["phi qua dem chi tinh chieu mua"] = {"bat": bat, "tong": len(mau)}

    # ---- LOI 2: engine QUEN dich mot bar ----------------------------------
    def chay_quen_dich(df, tin_hieu, cp, lai_suat_nam=None, ma="", khung="", da_dich=False):
        return goc_chay(df, tin_hieu, cp, lai_suat_nam, ma, khung, da_dich=True)

    MP.chay = chay_quen_dich
    bat2 = 0
    for ma, df in mau.items():
        cp = CP.tu_du_lieu(ma, df)
        ok, _ = ca_tre_mot_bar(df, cp, ma)
        bat2 += (not ok)
    MP.chay = goc_chay
    ra["ca"]["engine quen dich mot bar"] = {"bat": bat2, "tong": len(mau)}

    nhay = all(v["bat"] == v["tong"] for v in ra["ca"].values())
    ra["nhay"] = nhay
    print("\n=== MUTATION AUDIT: canary co that su nhay khong? ===")
    for ten, v in ra["ca"].items():
        dau = "OK  " if v["bat"] == v["tong"] else "TRUOT"
        print(f"  [{dau}] chen loi '{ten}' -> canary bat {v['bat']}/{v['tong']}")
    print("  =>", "canary NHAY, dung duoc lam cong." if nhay
          else "canary KHONG nhay - day bay khong hoat dong, PHAI SUA.")
    return nhay, ra


if __name__ == "__main__":
    lanh, _ = chay_het()
    ma_ra = 0 if lanh else 1
    if "--tu-kiem" in sys.argv:
        nhay, _ = tu_kiem()
        ma_ra = ma_ra or (0 if nhay else 2)
    sys.exit(ma_ra)
