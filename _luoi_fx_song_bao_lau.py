# -*- coding: utf-8 -*-
"""LUOI FX: khong hoi 'co SL khong', hoi 'song bao lau va rut kip khong'.

Chu du an 04/09: *"toi khong ngai viec dca khong cat"*. Dung - kho cua chinh du
an ghi EURCAD luoi **35%/nam backtest that**. Cau hoi dung cho lop he nay la
ba cai: song bao lau, kiem duoc bao nhieu trong thoi gian do, va lich rut tien
co dua tay ve bo truoc khi duoi den khong.
"""
import sys, json, warnings
sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")
import numpy as np
from nhan import tin_hieu_mql5 as TH

SID = 2359404
rr = TH.rui_ro_json(SID)
print(f"signal #{SID}: {len(rr)} ngay co du lieu rui ro")
loi = np.array([x["loi"] for x in rr], dtype=float)
mae = np.array([x["mae"] for x in rr], dtype=float)
mfe = np.array([x["mfe"] for x in rr], dtype=float)
ngay = len(loi)
print(f"loi/ngay: TB {loi.mean():+.3f}%  do lech {loi.std():.3f}%  "
      f"am {int((loi < 0).sum())}/{ngay} ngay")
print(f"MAE: TB {mae[mae < 0].mean():.2f}%  sau nhat {mae.min():.2f}%")
print(f"MFE: TB {mfe[mfe > 0].mean():.2f}%")
print()

# 1) SONG BAO LAU. Uoc bang cach lay mau CO HOAN LAI THEO KHOI (giu cum bien
#    dong), dem bao nhieu duong chay cham -100% trong N nam.
rng = np.random.default_rng(20260904)
KHOI, LAN, NAM = 10, 4000, 5
b_ngay = 252
ket = []
for _ in range(LAN):
    can = NAM * b_ngay
    chuoi = []
    while len(chuoi) < can:
        i = rng.integers(0, max(len(loi) - KHOI, 1))
        chuoi.extend(loi[i:i + KHOI])
    r = np.array(chuoi[:can]) / 100.0
    tk, chet = 1.0, None
    for j, x in enumerate(r):
        tk *= (1.0 + x)
        if tk <= 0.02:          # con 2% von = coi nhu chay
            chet = j
            break
    ket.append((chet, tk))
chet = [k[0] for k in ket if k[0] is not None]
song = [k[1] for k in ket if k[0] is None]
print(f"=== MO PHONG {LAN} duong chay, {NAM} nam, lay mau khoi {KHOI} ngay ===")
print(f"  chay tai khoan : {len(chet)}/{LAN} = {len(chet)/LAN:.1%}")
if chet:
    print(f"  neu chay thi chay sau trung vi {np.median(chet)/b_ngay:.2f} nam")
if song:
    s = np.array(song)
    print(f"  neu song: von cuoi trung vi x{np.median(s):.2f}  "
          f"(bach phan vi 10 x{np.percentile(s,10):.2f}, 90 x{np.percentile(s,90):.2f})")
print()

# 2) RUT TIEN: bao lau thi hoan von goc?
print("=== LICH RUT: bao lau hoa von goc ===")
for chu_ky_ngay, ty_le in ((21, 0.5), (63, 0.5), (63, 1.0), (126, 1.0)):
    hoa = []
    for _ in range(1500):
        can = NAM * b_ngay
        chuoi = []
        while len(chuoi) < can:
            i = rng.integers(0, max(len(loi) - KHOI, 1))
            chuoi.extend(loi[i:i + KHOI])
        r = np.array(chuoi[:can]) / 100.0
        tk, tui, t_hoa = 1.0, 0.0, None
        for j, x in enumerate(r):
            tk *= (1.0 + x)
            if tk <= 0.02:
                break
            if j and j % chu_ky_ngay == 0 and tk > 1.0:
                lay = (tk - 1.0) * ty_le
                tk -= lay
                tui += lay
                if tui >= 1.0 and t_hoa is None:
                    t_hoa = j
        hoa.append(t_hoa)
    co = [h for h in hoa if h is not None]
    print(f"  rut {ty_le:.0%} lai moi {chu_ky_ngay:>3} ngay: "
          f"hoan von goc {len(co)/len(hoa):>5.1%} duong chay"
          + (f", trung vi {np.median(co)/b_ngay:.2f} nam" if co else ""))
