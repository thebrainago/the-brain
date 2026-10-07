# -*- coding: utf-8 -*-
"""Dot HH (05/10): y tuong HANG HOA do Claude mo rong tu kien thuc (mua vu, IBS, lich du lieu, cap hoa kim) -> ds-flash soan DSL -> may cham -> may lat BAN.
Ghi reports/deepseek/dsl_hh/. Moi y tuong ghi kem TAI SAN dich + KHUNG de job may nha. Van la BAN NHAP chua thu tren gia."""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_dsl_cmt as J
from nhan import ngu_phap as N, guong_dsl as G
from nhan.giao_llm import goi
OUT = Path(__file__).resolve().parent / "dsl_hh"; OUT.mkdir(exist_ok=True)
Y = {  # ten: (y tuong, [tai san CFD], khung)
 "khi_mua_dong": ("mua truoc mua dong: thang tu 8 den 10 VA gia dong cua > SMA 50 (nhu cau suoi am + xu huong)", ["XNGUSD"], "D1"),
 "khi_ban_xuan": ("ban khi het mua suoi: thang tu 3 den 4 VA gia dong cua < SMA 50", ["XNGUSD"], "D1"),
 "dau_mua_lai_xe": ("mua trong mua lai xe cao diem: thang tu 4 den 6 VA gia dong cua > EMA 20", ["XTIUSD", "XBRUSD"], "D1"),
 "dau_ibs_hoi_quy": ("IBS < 0,2 VA gia dong cua > SMA 200: mua nhip rut 1 ngay trong xu huong len", ["XTIUSD", "XBRUSD"], "D1"),
 "dau_thu_tu_ton_kho": ("ngay_trong_tuan = 2 (thu Tu; DSL danh so 0 = thu Hai, nen thu Tu la 2; ngay bao cao ton kho EIA) VA RSI 3 < 30: hoi phuc sau nhip giam truoc bao cao", ["XTIUSD"], "D1"),
 "vang_ibs": ("IBS < 0,2 VA gia dong cua > SMA 100: mua nhip rut ngan cua vang trong xu huong", ["XAUUSD", "XAGUSD"], "D1"),
 "vang_mua_vu_cuoi_nam": ("mua dong tien trang suc: thang tu 8 den 9 VA gia dong cua > SMA 50", ["XAUUSD", "XAGUSD"], "D1"),
 "vang_thang_1": ("hieu ung dau nam: ngay_trong_thang <= 10 VA thang = 1 VA gia dong cua > EMA 50", ["XAUUSD"], "D1"),
 "vang_pha_vo_nen": ("nen bien dong: ATR 14 < phan vi 0,2 cua ATR trong 120 bar VA gia dong cua > cao nhat 20 bar truoc", ["XAUUSD", "XAGUSD", "XTIUSD"], "D1"),
 "bac_quay_ve": ("zscore gia 20 < -2 VA ADX 14 < 25: bac quay ve trung binh khi khong xu huong", ["XAGUSD"], "D1"),
 "dong_chu_ky_cong_nghiep": ("EMA 50 > EMA 200 VA RSI 14 cat len tren 50: dong theo chu ky cong nghiep khi xu huong len", ["XCUUSD"], "D1"),
 "ngo_vu_he": ("mua rui ro thoi tiet vu he: thang tu 5 den 6 VA gia dong cua > SMA 30", ["XCNUSD", "CORN"], "D1"),
 "lua_mi_thu_hoach": ("ban ap luc thu hoach: thang tu 6 den 7 VA gia dong cua < SMA 50", ["XWHUSD", "WHEAT"], "D1"),
 "dau_tuong_thang_9": ("mua vao thu: thang tu 8 den 9 VA gia dong cua > EMA 20", ["XSOUSD", "SOYBEAN"], "D1"),
 "ca_phe_dong_luong": ("dong luong 60 ngay duong VA gia dong cua > cao nhat 40 bar truoc: ca phe xu huong dai", ["XKCUSD", "COFFEE"], "D1"),
 "duong_pha_vo": ("gia dong cua > cao nhat 55 bar truoc VA ADX 14 > 20: pha vo kieu Turtle", ["XSBUSD", "SUGAR"], "D1"),
 "tuan_cuoi_thang": ("ngay_trong_thang >= 25 VA IBS < 0,3: dong tien can doi danh muc cuoi thang", ["XTIUSD", "XAUUSD"], "D1"),
 "gio_chot_phien_my": ("gio tu 15 den 17 VA RSI 14 < 35: nhip rut cuoi phien My cua dau", ["XTIUSD"], "H1"),
 "dau_pha_vo_london": ("gio tu 7 den 9 VA gia dong cua > cao nhat 12 bar truoc: pha vo mo phien London", ["XTIUSD", "XAUUSD"], "H1"),
 "vang_hoi_quy_h1": ("zscore gia 24 < -2 VA gio tu 8 den 20: vang quay ve trong gio hoat dong", ["XAUUSD"], "H1"),
}
BAN = {"khi_ban_xuan", "lua_mi_thu_hoach"}      # y tuong goc la BAN: soan thang chieu -1, ten _ban; ban lat la DOI CHUNG (_doi_chung)
def lam(it):
    ten, (y, ts, kh) = it
    hau = "ban" if ten in BAN else "mua"
    p = J.TT + y + "\nchieu = %s (ten = '%s_%s'). CHI soan ban %s." % ("-1" if hau == "ban" else "1", ten, hau, hau.upper())
    loi_cu = ""
    for v in range(3):
        r = goi("T2", p + loi_cu, 1200, "dsl_hh")
        m = re.search(r"\{.*\}", r["noi_dung"], re.S)
        try:
            s = json.loads(m.group(0)); s["ten"] = ten + "_" + hau; s.setdefault("co_che", y)
            s["ho"] = s.get("ho") if s.get("ho") in ("bien_dong", "dong_tien", "lich", "pha_vo", "phien", "quay_ve_trung_binh", "vi_mo", "xu_huong") else ("lich" if "thang" in y or "ngay_trong" in y else "xu_huong")
            loi = N.kiem_khai_bao(s)
        except Exception as e:
            s, loi = None, ["json hong: %s" % e]
        if not loi: break
        loi_cu = "\nBAN TRUOC SAI: " + "; ".join(loi[:3]) + ". Sua lai."
    return ten, s, loi, ts, kh, hau
if __name__ == "__main__":
    with ThreadPoolExecutor(8) as ex: kq = list(ex.map(lam, Y.items()))
    meta = {}; dat = ban = 0
    for ten, s, loi, ts, kh, hau in kq:
        if loi: print("HONG", ten, loi[:1]); continue
        dat += 1; (OUT / ("%s_%s.json" % (ten, hau))).write_text(json.dumps(s, ensure_ascii=False, indent=1)); meta[ten + "_" + hau] = {"tai_san": ts, "khung": kh}
        b = G.guong(s)
        if b and not N.kiem_khai_bao(b): ban += 1; (OUT / ((b["ten"] if hau == "mua" else ten + "_doi_chung") + ".json")).write_text(json.dumps(b, ensure_ascii=False, indent=1)); meta[b["ten"][:-4] if hau == "mua" else ten + "_doi_chung"] = meta[ten + "_" + hau]
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print("dat %d/%d, ban %d" % (dat, len(kq), ban))
