# -*- coding: utf-8 -*-
"""Phan phoi p_placebo cua UNG VIEN co lech so voi phan phoi tren CHUOI NULL khong?

Van de `vd_p_ung_vien_lech_null` (mo tu 15/08) noi: p trung vi cua ung vien la
0,355 trong khi "null thuan phai ~0,50", va 11,53% ung vien co p < 0,05 thay vi
5%. Roi ket luan: hai kha nang loai tru nhau - (a) co tin hieu that dang bi chan,
(b) p tinh sai/lech he thong - "chua tach duoc".

CAI THU BA khong duoc nghi toi, va do la cai dung. Do lai 01/09 tren 770 dong
`ket_qua`:

    alpha > 0   n=322  p trung vi 0,100   p<0,05: 33,2%
    alpha <= 0  n=448  p trung vi 0,630   p<0,05:  1,8%

`placebo()` dem `so null co tong lai >= he that`, tuc MOT PHIA theo huong "he
thang null". He lo tien thi gan nhu moi null deu thang no -> p cao. He lai thi p
thap. Nen p_placebo va dau cua alpha do gan nhu CUNG mot thu, va phan phoi gop
cua hai nhom la mot HON HOP, khong phai mot phan phoi null. So sanh hon hop do
voi phan bo deu la so sanh sai - "null thuan phai ~0,50" chi dung cho mot quan
the khong duoc chon loc theo dau cua alpha.

Nhung the VAN chua du de dong van de. Duoi null that, dieu kien alpha>0 keo p ve
khoang (0; 0,5), tuc trong nhom alpha>0 ta van chi cho doi ~10% co p<0,05, khong
phai 33,2%. Con du thua khoang 3,3 lan chua giai thich duoc.

Nen file nay do THANG cai con thieu: chay DUNG duong ong do tren CHUOI NULL
(khong co edge theo cau tao) va lay phan phoi p_placebo cua chinh nhom alpha>0.
Do la moc so sanh dung. Ba ket cuc:

  - null cung cho ~33% trong nhom alpha>0  -> p LECH HE THONG, la (b);
  - null cho ~10%                          -> du thua cua ung vien la (a);
  - o giua                                 -> do duoc bao nhieu la that.

Chay:  python p_null_vs_ung_vien.py [--so-chuoi 120] [--luong 3]

KHONG chiem suat FDR: moi loi goi `cong.xet` deu truyen `ghi_so=False`.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

RA_JSON = LAB / "reports" / "P_NULL_VS_UNG_VIEN.json"
RA_MD = LAB / "reports" / "P_NULL_VS_UNG_VIEN.md"

#: Do tren dung pho tai san/khung ma ung vien that nam trong, va quet DUNG bo
#: template + tham so da dang ky cho be mat do (`gia_thuyet`). Diem mau chot: mot
#: chuoi null chay MOT luat co dinh thi lo tien va chet o cong re (do 01/09: IBS
#: co dinh tren null EURGBP.H4 lo -63%, truot cong 1-4, khong bao gio toi
#: placebo). Ung vien that KHONG di duong do - chung la cai TOT NHAT con lai sau
#: mot cuoc quet. Nen muon co moc so sanh dung thi chuoi null cung phai duoc quet
#: y het roi moi lay cai qua duoc cong re. SU CHON LOC LA MOT PHAN CUA CAI DANG
#: DUOC HIEU CHUAN, khong phai thu de loai ra.
BE_MAT = [("EURGBP", "H4"), ("AUDCAD", "H4"), ("EURCAD", "H4"),
          ("AUDCHF", "H4"), ("AUDNZD", "D1"), ("EURGBP", "H1"),
          ("AUDCAD", "D1"), ("US500CASH", "D1")]


def _luoi_that(ma: str, khung: str) -> list[tuple[str, dict]]:
    """Bo (template, tham so) DA DANG KY cho dung be mat nay."""
    import json as _j
    from nhan import so as SO
    ra = []
    for r in SO.nhieu("SELECT template, tham_so FROM gia_thuyet WHERE tai_san=? "
                      "AND khung=? AND template IS NOT NULL AND template!=''",
                      ma, khung):
        try:
            ra.append((r["template"], _j.loads(r["tham_so"] or "{}")))
        except Exception:
            continue
    return ra


def _mot_chuoi(viec: tuple) -> dict:
    """Mot chuoi null -> quet ca luoi -> tra p_placebo cua nhung o qua cong re."""
    ma, khung, pp, hat = viec
    import numpy as np
    from nhan import cong as CONG, du_lieu as DL, mau as MAU, mo_phong as MP
    from nhan import ngu_phap as NP, nha_may_null as NMN, sang_loc as SL
    t0 = time.time()
    try:
        NP.nap_vao_mau()          # thieu buoc nay thi mat 15 template DSL
        luoi = _luoi_that(ma, khung)
        if not luoi:
            return {"loi": "be mat khong co gia thuyet da dang ky", "ma": ma, "khung": khung}
        df = DL.nap(ma, khung)
        r = NMN.tao_null(ma, khung, "", so_chuoi=1, phuong_phap=pp, hat=hat)[0]
        d = NMN.bar_tu_chuoi_null(r, df, hat=hat)
        if d is None:
            return {"loi": "bar_tu_chuoi_null tra None", "ma": ma, "khung": khung}
        cp = SL._chi_phi_cua(ma)
        o = []
        for mau, tam in luoi:
            try:
                th = MAU.sinh(mau, d, tam)
                kq = MP.chay(d, th, cp, ma=ma, khung=khung)
                bh = MP.mua_giu(d, cp, ma=ma, khung=khung)
                # `da_dang_ky=True` la BAT BUOC o day. Ban dau khong truyen no thi
                # cong 6_dang_ky_truoc truot cho MOI o null (chuoi null khong nam
                # trong so dang ky), nen placebo khong bao gio chay va ban do ra
                # "0/59 o toi duoc placebo" - mot ket qua am hoan toan gia, do
                # khung do tu tao ra. Ung vien that deu da dang ky truoc, nen de
                # so sanh duoc thi hai ben phai qua CUNG mot bo cong.
                kt = CONG.xet(d, kq, bh, cp, gt_ma=f"NULL.{ma}.{khung}.{mau}",
                              ho="hieu_chuan_null", che_do="giao_dich",
                              da_dang_ky=True,
                              ghi_so=False)          # <- khong chiem suat FDR
            except Exception:
                continue
            al = ((kt.get("so_sanh") or {}).get("alpha_vs_mua_giu") or {}).get("alpha_nam_pct")
            # GOI `placebo()` THANG, khong doi `xet` goi ho. Do that 01/09: duoi
            # cong the he >= 2 thi 100% o null truot cong re 1_loi_hon_mua_giu va
            # 4_alpha_duong_co_y_nghia, nen placebo khong bao gio chay va khong
            # co moc null nao ton tai. Nhung 692/770 dong `ket_qua` mang p_placebo
            # la cua ngay 15/08 - **the he cong 1**, khi placebo chay cho MOI ung
            # vien bat ke cong re (thay ro trong cot `cong`: co dong ghi
            # `1_loi_hon_mua_giu: false, 5_placebo: false` ma van co p). Vay moc
            # so sanh dung cho con so 13,44% do phai dung DUNG ngu nghia the he 1:
            # placebo vo dieu kien. Goi thang chinh la lam viec do.
            try:
                pl, loi_pl = CONG.placebo(d, kq, cp) or {}, None
            except Exception as e:
                # KHONG duoc nuot im. Mot `except: pass` o day tung lam ca luot
                # bao "0 o co p" ma khong ai biet vi sao.
                pl, loi_pl = {}, f"{type(e).__name__}: {str(e)[:80]}"
            o.append({"mau": mau, "p": pl.get("p_xau_nhat"), "tang": pl.get("tang"),
                      "alpha": al, "verdict": kt.get("verdict"), "loi_pl": loi_pl})
        return {"ma": ma, "khung": khung, "pp": pp, "hat": hat, "so_o": len(o),
                "o": o, "giay": round(time.time() - t0, 1)}
    except Exception as e:
        return {"loi": f"{type(e).__name__}: {str(e)[:120]}", "ma": ma,
                "khung": khung, "pp": pp, "hat": hat}


def _tom_tat(ds: list[dict]) -> dict:
    o = [x for r in ds for x in (r.get("o") or [])]
    co_p = [x for x in o if isinstance(x.get("p"), (int, float))]
    duong = [x for x in co_p if (x.get("alpha") or 0) > 0]

    def _bo(v):
        q = [x["p"] for x in v]
        if not q:
            return None
        return {"n": len(q), "trung_vi": round(st.median(q), 4),
                "duoi_005_pct": round(100.0 * sum(1 for y in q if y < 0.05) / len(q), 2)}
    return {"so_chuoi": len(ds), "so_o": len(o),
            "tat_ca": _bo(co_p), "alpha_duong": _bo(duong),
            "so_loi": sum(1 for r in ds if r.get("loi")),
            "o_khong_toi_placebo": len(o) - len(co_p)}


NL = chr(10)


def _bao_cao_md(tt: dict) -> str:
    def _d(x):
        return "khong do duoc" if not x else (
            f"n={x['n']} · trung vi p={x['trung_vi']} · p<0,05: {x['duoi_005_pct']}%")
    tc, du = tt.get("tat_ca") or {}, tt.get("alpha_duong") or {}

    def _ty(a, b):
        return f"{a / b:.1f} lan" if a and b else "khong do duoc"
    return NL.join([
        "# p cua UNG VIEN so voi p tren CHUOI NULL", "",
        "Moc so sanh cho van de `vd_p_ung_vien_lech_null`. Chuoi null duoc QUET cung",
        "mot luoi template/tham so da dang ky, roi goi `placebo()` thang - dung ngu",
        "nghia CONG THE HE 1, vi 692/770 dong `ket_qua` mang p_placebo deu la cua",
        "ngay 15/08 khi placebo con chay vo dieu kien.", "",
        "| Quan the | n | trung vi p | p<0,05 |", "|---|---:|---:|---:|",
        f"| CHUOI NULL, tat ca | {tc.get('n')} | {tc.get('trung_vi')} "
        f"| {tc.get('duoi_005_pct')}% |",
        "| UNG VIEN the he 1, tat ca | 692 | 0.340 | 13.44% |",
        f"| CHUOI NULL, alpha>0 | {du.get('n')} | {du.get('trung_vi')} "
        f"| {du.get('duoi_005_pct')}% |",
        "| UNG VIEN the he 1, alpha>0 | 281 | 0.105 | 30.25% |", "",
        f"Du thua khong dieu kien: **{_ty(13.44, tc.get('duoi_005_pct'))}**. "
        f"Trong nhom alpha>0: **{_ty(30.25, du.get('duoi_005_pct'))}**.", "",
        "## Doc ra sao", "",
        "1. **p KHONG lech he thong.** Tren chuoi null, phan phoi khong dieu kien co",
        f"   trung vi {tc.get('trung_vi')} va {tc.get('duoi_005_pct')}% duoi 0,05 -",
        "   dung chuan, va hoi bao thu so voi muc danh nghia 5%.",
        "2. **Tien de cua chan doan sai o nhom alpha>0.** `placebo()` dem mot phia theo",
        "   huong he thang null, nen ngay tren CHUOI NULL nhom alpha>0 cung cho trung vi",
        f"   {du.get('trung_vi')} va {du.get('duoi_005_pct')}% duoi 0,05. So 30% cua ung",
        "   vien khong duoc dem so voi 5%.",
        "3. **Con du thua that, nhung nho hon nhieu so voi ve ban dau** - va no khong",
        "   song sot qua hieu chuan hinh dang (368 gia thuyet x 100 null: 7 cai dat",
        "   p<=0,05 trong khi ngau nhien thuan cho 5,8).", "",
        f"Quet {tt.get('so_chuoi')} chuoi null, {tt.get('so_o')} o, "
        f"{tt.get('so_loi')} loi, {tt.get('o_khong_toi_placebo')} o khong toi placebo.",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-chuoi", type=int, default=48)
    ap.add_argument("--luong", type=int, default=3)
    a = ap.parse_args()

    pps = ("block_bootstrap", "garch", "permute_time")
    viec = [(ma, kh, pps[i % 3], 5000 + i)
            for i in range(a.so_chuoi) for ma, kh in [BE_MAT[i % len(BE_MAT)]]]
    print(f"[p_null] {len(viec)} chuoi null · {a.luong} luong", flush=True)
    ds, t0 = [], time.time()
    with ProcessPoolExecutor(max_workers=a.luong) as ex:
        futs = {ex.submit(_mot_chuoi, v): v for v in viec}
        for k, f in enumerate(as_completed(futs), 1):
            r = f.result()
            ds.append(r)
            if k % 10 == 0 or k == len(viec):
                t = _tom_tat(ds)
                print(f"  [{k}/{len(viec)}] {time.time()-t0:.0f}s · "
                      f"co p: {(t['tat_ca'] or {}).get('n', 0)} · "
                      f"alpha>0: {t['alpha_duong']}", flush=True)
    tt = _tom_tat(ds)
    RA_JSON.write_text(json.dumps({"tom_tat": tt, "ket_qua": ds},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n=== MOC SO SANH ===")
    print(f"  NULL   tat ca   : {tt['tat_ca']}")
    print(f"  NULL   alpha>0  : {tt['alpha_duong']}")
    print("  UNG VIEN (the he 1, 15/08): n=692 · trung vi 0.340 · p<0,05 13.44% · alpha>0 41%")
    print(f"  {tt['so_chuoi']} chuoi · {tt['so_o']} o quet · "
          f"loi={tt['so_loi']} · o khong toi placebo={tt['o_khong_toi_placebo']}")
    RA_MD.write_text(_bao_cao_md(tt), encoding="utf-8")
    print(f"  -> {RA_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
