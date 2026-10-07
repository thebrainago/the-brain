# -*- coding: utf-8 -*-
"""Job 3b: dot 2 y tuong CMT. Model re CHI soan ban MUA; ban BAN do nhan/guong_dsl.guong (may lat, khong de LLM lat). Ghi reports/deepseek/dsl_cmt/."""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_dsl_cmt as J
from nhan import ngu_phap as N, cmt_prior as C, guong_dsl as G
from nhan.giao_llm import goi
Y = {
 "sto_cheo_trong_xu_huong": "stochastic cat len tren 20 (cheo_len) VA SMA 50 > SMA 200: tin hieu dao dong chi nhan khi xu huong cung chieu",
 "cci_qua_ban_roi_len": "CCI cat len tren -100 VA ADX > 20: thoat vung qua ban khi co xu huong",
 "donchian_pha_loc_atr": "gia dong cua > cao nhat 20 bar truoc VA ATR(14) > trung binh ATR 50: pha vo kem bien dong no",
 "keltner_quay_ve_adx_thap": "gia dong cua < duong Keltner duoi VA ADX < 20: quay ve trung binh khi khong co xu huong",
 "supertrend_dao_chieu": "gia dong cua cat len tren Supertrend: dao chieu xu huong",
 "ichimoku_tenkan_kijun": "Tenkan cat len tren Kijun VA gia tren may Ichimoku",
 "ba_nen_giam_ibs": "dem_lien_tiep >= 3 bar giam VA IBS < 0,2: quay ve sau chuoi giam ngan",
 "bien_dong_thap_pha_vo": "phan vi ATR < 0,2 trong 100 bar roi gia dong cua > cao nhat 10 bar: nen bop phat nho",
 "dau_thang_xu_huong": "ngay_trong_thang <= 3 VA gia > EMA 50: dong tien dau thang theo xu huong",
 "gio_london_pha_vo": "gio tu 7 den 10 VA gia dong cua > cao nhat 12 bar: pha vo phien London",
 "vwap_quay_ve": "gia dong cua < VWAP - 2 ATR hoac zscore gia < -2 trong khi ADX < 25: quay ve VWAP",
 "bollinger_ep_bop_xu_huong": "bollinger duoi (hoac %B < 0,05) VA EMA 100 doc len: mua nhip rut sau trong xu huong len",
}
def lam(item):
    ten, y = item
    p = J.TT + y + "\nchieu = 1 (ten = '%s_mua'). CHI soan ban MUA." % ten
    loi_cu = ""
    for vong in range(2):
        r = goi("T1", p + loi_cu, 1200, "dsl_cmt2")
        m = re.search(r"\{.*\}", r["noi_dung"], re.S)
        try:
            s = json.loads(m.group(0)); loi = N.kiem_khai_bao(s)
        except Exception as e:
            s, loi = None, ["json hong: %s" % e]
        if not loi:
            break
        loi_cu = "\nBAN TRUOC SAI: " + "; ".join(loi[:3]) + ". Sua lai."
    return ten, s, loi
if __name__ == "__main__":
    with ThreadPoolExecutor(6) as ex: kq = list(ex.map(lam, Y.items()))
    cu = [json.load(open(f)) for f in sorted(J.OUT.glob("*_mua.json"))]
    dat = [s for _, s, l in kq if not l]
    for t, s, l in kq:
        if not l: (J.OUT / ("%s_mua.json" % t)).write_text(json.dumps(s, ensure_ascii=False, indent=1))
    tat_ca = cu + dat
    ban, khong = [], []
    for s in tat_ca:
        b = G.guong(s)
        if b and not N.kiem_khai_bao(b): ban.append(b); (J.OUT / (b["ten"] + ".json")).write_text(json.dumps(b, ensure_ascii=False, indent=1))
        else: khong.append(s.get("ten"))
    r = C.loc(tat_ca + ban)
    print("dot2 dat %d/%d hong %s | tong mua %d, ban (may lat) %d, khong lat duoc %s | cum %d" % (len(dat), len(kq), [t for t, s, l in kq if l], len(tat_ca), len(ban), khong, r["so_phep_thu_hieu_dung"]))
