# -*- coding: utf-8 -*-
"""Dot 3 (05/10): LAP CHO TRONG theo he thong. Liet ke moi cap HO CMT (khac ho) chua co trong kho + ban nhap, nho ds-flash soan 3 bien the
ban MUA moi cap (chi bao khac nhau trong cung ho), may cham cu phap, may lat BAN, `cmt_prior.loc` bao cum moi. Ghi reports/deepseek/dsl_cmt/."""
import json, re, sys, itertools
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_dsl_cmt as J
from nhan import ngu_phap as N, cmt_prior as C, guong_dsl as G
from nhan.giao_llm import goi

HO_DUNG = ["XU_HUONG", "SUC_MANH_XU_HUONG", "DAO_DONG", "BIEN_DONG", "PHA_VO", "LICH", "NEN"]
def ho_cua_spec(s):
    return {C.HO.get(k) for k in C.chi_bao_trong(s)} - {None}
def hien_co():
    kho = [json.load(open(f)) for f in sorted(Path("kho_phuong_phap").glob("*.json"))] if Path("kho_phuong_phap").exists() else []
    nhap = [json.load(open(f)) for f in sorted(J.OUT.glob("*.json"))]
    return {frozenset(ho_cua_spec(s)) for s in nhap}
def _ho_dsl(a, b):
    """ho cua DSL (danh sach co dinh cua ngu_phap) suy bang may tu cap ho CMT - khong de LLM doan."""
    for ho_cmt, ho in (("PHA_VO", "pha_vo"), ("LICH", "lich"), ("BIEN_DONG", "bien_dong"), ("DAO_DONG", "quay_ve_trung_binh")):
        if ho_cmt in (a, b): return ho
    return "xu_huong"
def lam(item):
    ten, ho_a, ho_b, bien_the = item
    ga = sorted({k for k, v in C.HO.items() if v == ho_a}); gb = sorted({k for k, v in C.HO.items() if v == ho_b})
    y = ("Y TUONG: ket hop mot chi bao ho %s (chon trong %s) voi mot chi bao ho %s (chon trong %s) thanh dieu kien VAO MUA hop ly theo "
         "phan tich ky thuat (bien the %d: chon chi bao / tham so KHAC cac bien the khac). DUNG hai dieu kien vao: mot tu moi ho, KHONG them dieu kien ho thu ba." % (ho_a, ga[:8], ho_b, gb[:8], bien_the))
    p = J.TT + y + "\nchieu = 1 (ten = '%s_mua'). CHI soan ban MUA." % ten
    loi_cu = ""
    for vong in range(3):
        r = goi("T2", p + loi_cu, 1200, "dsl_cmt3")
        m = re.search(r"\{.*\}", r["noi_dung"], re.S)
        try:
            s = json.loads(m.group(0)); s["ten"] = ten + "_mua"; s.setdefault("co_che", "CMT %s + %s (nhap, may dien)" % (ho_a, ho_b)); s["ho"] = _ho_dsl(ho_a, ho_b); loi = N.kiem_khai_bao(s)
        except Exception as e:
            s, loi = None, ["json hong: %s" % e]
        if not loi:
            got = {C.ho_cua(k) for k in C.chi_bao_trong(s)} - {None}
            if got != {ho_a, ho_b}:       # may cham trung thanh voi y tuong: DUNG hai ho, khong them ho thu ba
                loi = ["ho hien co %s nhung phai DUNG hai ho %s va %s (khong them chi bao ho khac, vd chi bao khoi luong / dao dong thua)" % (sorted(got), ho_a, ho_b)]
        if not loi:
            break
        loi_cu = "\nBAN TRUOC SAI: " + "; ".join(loi[:3]) + ". Sua lai."
    return ten, s, loi
if __name__ == "__main__":
    co = hien_co()
    viec = []
    for a, b in itertools.combinations(HO_DUNG, 2):
        if frozenset({a, b}) in co or (J.OUT / ("c3_%s_%s_1_mua.json" % (a.lower()[:6], b.lower()[:6]))).exists(): continue
        for k in (1, 2, 3):
            viec.append(("c3_%s_%s_%d" % (a.lower()[:6], b.lower()[:6], k), a, b, k))
    print("cap ho moi:", len(viec) // 3, "viec", len(viec))
    with ThreadPoolExecutor(8) as ex: kq = list(ex.map(lam, viec))
    dat = 0; ban = 0
    for t, s, l in kq:
        if l: continue
        dat += 1; (J.OUT / (t + "_mua.json")).write_text(json.dumps(s, ensure_ascii=False, indent=1))
        b = G.guong(s)
        if b and not N.kiem_khai_bao(b): ban += 1; (J.OUT / (b["ten"] + ".json")).write_text(json.dumps(b, ensure_ascii=False, indent=1))
    print("dat %d/%d, ban (may lat) %d; hong %s" % (dat, len(kq), ban, [(t, l[:1]) for t, s, l in kq if l][:6]))
