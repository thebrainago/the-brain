# -*- coding: utf-8 -*-
"""Job 3: model re soan khai bao DSL theo y tuong kieu CMT (cum con TRONG hoac it co trong kho). May cham: ngu_phap.kiem_khai_bao rong + cmt_prior.
Chi ghi reports/deepseek/dsl_cmt/ (ban nhap). Khong sua config/. 1 vong sua kem loi cu the. Khong cham diem, khong chay engine."""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
LAB = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(LAB))
from nhan import ngu_phap as N, cmt_prior as C
from nhan.giao_llm import goi
OUT = LAB / "reports/deepseek/dsl_cmt"
Y = {
 "nen_bop_roi_bat": "Bollinger/bien do nen RAT HEP (phan vi thap) roi gia dong cua vuot kenh Donchian 20: pha vo sau nen bop",
 "lui_ve_trong_xu_huong": "EMA nhanh > EMA cham (xu huong len) VA RSI < 40: mua nhip lui trong xu huong",
 "adx_pha_vo": "ADX > 25 (co xu huong) VA gia dong cua > cao nhat 55 bar truoc: theo xu huong pha vo",
 "rsi_vung_bull": "RSI cat len 40 trong khi EMA 200 doc len: nhip nghi trong xu huong len (CMT: RSI 40-80 la vung bull)",
 "hoi_quy_khi_adx_thap": "ADX < 20 (di ngang) VA zscore gia < -2: dao dong ve trung binh khi khong co xu huong",
 "tinh_lich_ibs": "ngay_trong_tuan theo lich VA IBS < 0,2: hieu ung ngay + dong cua gan day nen",
 "may_ichimoku_sto": "gia tren may Ichimoku (tren span) VA stochastic cat len 20: loc xu huong + kich hoat dao dong",
 "nen_heiken_chuoi": "chuoi nen Heiken Ashi cung mau >= 3 bar VA ATR dang gian (atr > tb atr 50): theo da",
 "gian_bien_dong": "ATR(14) cat len tren trung binh ATR(50) sau giai doan co hep: bien dong no ra",
 "fibo_nhip_lui": "gia ve vung Fibonacci 0,5-0,618 cua con song gan nhat trong xu huong len (EMA 50 doc len)",
}
CHI_BAO_CO = ", ".join(sorted(N.CHI_BAO_CO))
d = json.load(open(N.KHO_CO_CHE))
MAU = [x for x in d if len(x.get("vao", [])) >= 2 and x.get("ra")][0]
MAU = {k: MAU[k] for k in ("ten", "ho", "chieu", "giu", "vao", "ra")}
TT = ("Soan MOT khai bao co che giao dich theo DSL cua he (JSON). Chi dung chi_bao trong danh sach: " + CHI_BAO_CO +
      '.\nCau truc: {"ten","ho","chieu":1|-1,"giu":so bar giu toi da (nguyen),"vao":[{"trai":{...},"phep":"<|<=|>|>=|cheo_len|cheo_xuong","phai":{"hang":so}|{...}}],"ra":[...tuy chon]}.\n'
      "'trai'/'phai' la {\"chi_bao\":ten,\"n\":chu ky,...} hoac {\"hang\":so}; chong bang \"cua\" ({\"chi_bao\":\"gia\",\"cot\":\"close\"} la nguon gia). Mau dung cu phap:\n" + json.dumps(MAU, ensure_ascii=True) +
      "\nTra DUNG MOT JSON, khong giai thich, khong markdown. Y tuong can soan: ")
def lam(item):
    ten, y = item
    kq = []
    for chieu in (1, -1):
        p = TT + y + "\nchieu = %d (ten bat dau bang '%s_')" % (chieu, ten)
        loi_cu = ""
        for vong in range(2):
            r = goi("T1", p + loi_cu, 1200, "dsl_cmt")
            m = re.search(r"\{.*\}", r["noi_dung"], re.S)
            try:
                s = json.loads(m.group(0)); loi = N.kiem_khai_bao(s)
            except Exception as e:
                s, loi = None, ["json hong: %s" % e]
            if not loi:
                break
            loi_cu = "\nBAN TRUOC SAI: " + "; ".join(loi[:3]) + ". Sua lai, tra JSON day du."
        kq.append((ten, chieu, s, loi, vong))
    return kq
if __name__ == "__main__":
    with ThreadPoolExecutor(6) as ex: tong = [x for l in ex.map(lam, Y.items()) for x in l]
    dat = [(t, c, s) for t, c, s, l, v in tong if not l]
    for t, c, s in dat: (OUT / ("%s_%s.json" % (t, "mua" if c == 1 else "ban"))).write_text(json.dumps(s, ensure_ascii=False, indent=1))
    hong = [(t, c, l) for t, c, s, l, v in tong if l]
    r = C.loc([s for _, _, s in dat])
    (OUT / "_ket_qua.json").write_text(json.dumps({"dat": len(dat), "hong": hong, "so_cum": r["so_phep_thu_hieu_dung"], "canh_bao": r["canh_bao"]}, ensure_ascii=False, indent=1))
    print("dat", len(dat), "/", len(tong), "hong:", [(t, c) for t, c, _ in hong], "cum:", r["so_phep_thu_hieu_dung"], "canh bao:", r["canh_bao"])
