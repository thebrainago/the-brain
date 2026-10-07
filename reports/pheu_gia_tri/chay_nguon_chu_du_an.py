# -*- coding: utf-8 -*-
"""Chay chan_doan tren cac nguon chu du an gui 06/10/2026 (van ban chep tu anh chup)."""
import json, sys
sys.path.insert(0, "/home/user/the-brain")
from da_agent import llm
from nhan import pheu_gia_tri as P

NGUON = {
 "eod_reversal": ("deep_market_insight/baltussen_da_soebhag", """End-of-Day Reversal (Baltussen, Da, Soebhag), co phieu My 1993-2019. Mua co phieu giam sau nhat trong ngay, ban co phieu tang manh nhat cuoi ngay.
ROD3 = ON + FH + M (loi suat tu dong cua hom qua den truoc 30 phut cuoi). Nhom ROD3 thap (losers) bat tang 30 phut cuoi (LH), nhom cao (winners) giam. Mua 10% losers (dong gop 85% loi nhuan), ban khong 10% winners (15%), dong het tai ATC khong giu qua dem.
Loi nhuan 17,3%/nam, t-stat > 10. Rao can: khop lenh thi truong an loi do spread va phi ban khong cuoi phien. Kiem soat bang hoi quy Fama-MacBeth voi size, volume, illiquidity overnight, volatility, realized volatility, mispricing. Hieu ung cross-sectional ro ret (-5.97 bps pha cross), time-series nho (2.79 bps).
Ly do: (1) tam ly ca nhan mua duoi sang, bat day chieu; (2) phe ban khong rut lui vi rui ro qua dem, giam nhip do short de tranh gap-up. Tiep dien cuoi phien do market maker gamma hedging va ETF don bay tai can bang den het phien. Nhieu nghien cuu truoc cho S&P 500 co momentum cuoi ngay."""),
 "dca_vang": ("tiktok/zilloo_quyen", """Bot DCA mot chieu XAUUSD M5. Chi vao mot chieu (sell hoac buy), phai xac dinh xu huong truoc khi bat bot, bot khong tu chuyen buy sang sell. Lien tuc DCA duong (them lenh khi gia chay dung chieu: BUY 2 lot nhieu tang loi nhuan tang dan +94, +332, +534 ... +2893 USD).
DCA am toi da -20% thi dung DCA. Am 30% dong bot hoac am toi da theo so tien khi cham nguong de bao dam khong keo tai khoan ve 0. TP ky vong +30% tai khoan hoac tuy chinh thap/cao hon hoac dong toan bo khi thi truong xau hoac du target. Co duong MA vang va xanh tren chart. Khong co so lieu lich su, chi anh chup mot lenh dang lai."""),
}
def goi(he, nguoi):
    r = llm.goi("manh", he, nguoi, max_tokens=2500, nhan="pheu_gia_tri")
    return r["noi_dung"] if isinstance(r, dict) and "noi_dung" in r else str(r)
out = {}
for k, (ng, vb) in NGUON.items():
    kq = P.chan_doan(vb, ng, goi, k, da_thu=P.so_da_thu())
    out[k] = kq
    print(k, "vong", kq["so_vong"], "loi", kq["loi"][:2], "diem", kq.get("diem"))
json.dump(out, open("/home/user/the-brain/reports/pheu_gia_tri/lan1_kq.json", "w"), ensure_ascii=False, indent=1)
