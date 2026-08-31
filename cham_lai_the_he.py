# -*- coding: utf-8 -*-
"""cham_lai_the_he.py - CHAM LAI moi gia thuyet da dang ky duoi THE HE CONG hien tai.

VI SAO CO FILE NAY (viec dau tien cua ban giao 30/08/2026):
  Cong doi sang THE HE 5 (cong 1 so o muc RUI RO BANG NHAU) va them cong 11
  (khe gia o moc dao ngay). Moi phan quyet cu deu duoc sinh ra duoi the he 4,
  tuc duoi mot cong da biet la hong. Phai cham lai het truoc khi tin bat ky
  dong FAIL nao trong so cai.

  Luot cham lai 30/08 bo sot **83/361 gia thuyet**: chung dung template do tru
  NGHI sinh ra bang NGU PHAP, nam trong `config/co_che_dsl.json` chu khong
  trong `nhan/mau.py`. Duong cham lai hom do doc thang `MAU.MAU` nen 15 template
  DSL (79 gia thuyet) khong ton tai voi no, va bao la "khong chay duoc". Cach
  sua la mot dong: `NP.nap_vao_mau()` truoc khi cham - dung cai ma
  `quantlab.xac_nhan` van lam.

HAI DIEU BAT BIEN O DAY (dung go ra):

  1. **KHONG TIEU SUAT FDR.** Moi loi goi cong deu `ghi_so=False`. Day la phep
     DO DAC tren so cai da co, khong phai mot vong kiem dinh moi - xem ghi chu
     `do-dac-khong-duoc-chiem-suat-fdr`. Bo do nay ghi ~360 dong/luot; de no vao
     so FDR thi ngan sach cua ca ho bay sach.
  2. **KHONG TU NANG PHAN QUYET.** Gia thuyet nao cham lai ra FAIL thi ghi
     `the_he_cong=5` (da xet lai, verdict khong doi). Gia thuyet nao BAT LEN
     (PASS / CO_CO_CHE / NGHI_NHIN_TRUOC) thi **khong ghi gi vao so** - no can
     mot luot `quantlab.xac_nhan` that, co ghi so va co tra suat FDR. Mot PASS
     do bang `ghi_so=False` khong phai mot PASS.

Chay:
    python cham_lai_the_he.py                 # ca 361
    python cham_lai_the_he.py --chi-dsl       # chi gia thuyet dung template DSL
    python cham_lai_the_he.py --luong 8       # so tien trinh (mac dinh 8)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

RA_JSON = LAB / "reports" / "CHAM_LAI_THE_HE.json"
RA_MD = LAB / "reports" / "CHAM_LAI_THE_HE.md"

#: Giong `quet_be_mat.SO_TIEN_TRINH` - 8 la diem ngot da do that tren pheu D1.
SO_TIEN_TRINH = 8

#: Verdict nghia la "khong cham duoc", khong phai mot phan quyet.
KHONG_CHAM_DUOC = ("KHONG_CHAY_DUOC", "KHONG_DU_HOLDOUT", "LOI")


def _lay_danh_sach(chi_dsl: bool) -> list[dict]:
    from nhan import so as SO
    gts = [dict(g) for g in SO.nhieu("SELECT * FROM gia_thuyet ORDER BY id")]
    if not chi_dsl:
        return gts
    from nhan import mau as MAU
    goc = set(MAU.MAU)          # doc TRUOC khi nap DSL -> chi con mau viet tay
    return [g for g in gts if g["template"] not in goc]


def _cham_mot(gt: dict) -> dict:
    """Cham lai MOT gia thuyet. Ham muc GOC de Pool pickle duoc."""
    import sys as _s
    _s.path.insert(0, str(LAB))
    from nhan import cong as CONG, mau as MAU, mo_phong as MP, ngu_phap as NP
    from tru import quantlab as QL

    NP.nap_vao_mau()            # <- dong bi thieu cua luot 30/08
    ra = {"ma": gt["ma"], "template": gt["template"], "tai_san": gt["tai_san"],
          "khung": gt["khung"], "ho": gt["ho"], "cu": gt["trang_thai"]}
    t0 = time.time()
    try:
        if gt["template"] not in MAU.MAU:
            ra["moi"] = "KHONG_CHAY_DUOC"
            ra["ly_do"] = f"template '{gt['template']}' khong co ca trong mau.py lan DSL"
            return ra
        if str(gt["tai_san"] or "").startswith("RO:"):
            # Gia thuyet GOP khong co file gia rieng: "tai san" cua no la mot RO
            # dung theo pham vi cua ho. Nap thang bang `_nap` chi ra
            # FileNotFoundError - do la 4 dong LOI con lai sau khi noi DSL.
            ra.update(_cham_gop(gt))
            ra["giay"] = round(time.time() - t0, 2)
            return ra
        _df, _tr, holdout, _cptr, cp = QL._nap(gt["tai_san"], gt["khung"])
        if len(holdout) < 300:
            ra["moi"] = "KHONG_DU_HOLDOUT"
            ra["ly_do"] = f"holdout {len(holdout)} bar"
            return ra
        ts = json.loads(gt["tham_so"] or "{}")
        th = MAU.sinh(gt["template"], holdout, ts)
        kq = MP.chay(holdout, th, cp, ma=gt["tai_san"], khung=gt["khung"])
        bh = MP.mua_giu(holdout, cp, ma=gt["tai_san"], khung=gt["khung"])
        che_do = QL._che_do(cp)
        kt = CONG.xet(holdout, kq, bh, cp, gt_ma=gt["ma"],
                      ho=QL._ho_fdr(gt["ho"] or "chung", che_do),
                      da_dang_ky=True, tren_holdout=True, che_do=che_do,
                      ghi_so=False)          # <- bat bien 1
        dk = kt["dieu_kien"]
        al = kt["so_sanh"]["alpha_vs_mua_giu"]
        ra.update({
            "moi": kt["verdict"], "che_do": che_do,
            "dieu_kien": dk,
            "truot": [k for k, v in dk.items() if not v],
            "qua_1_2_3": all(dk.get(k) for k in
                             ("1_loi_hon_mua_giu", "2_sharpe_hon_mua_giu",
                              "3_calmar_hon_mua_giu")),
            "qua_4": bool(dk.get("4_alpha_duong_co_y_nghia")),
            "t_alpha": al.get("t_alpha"), "alpha_nam_pct": al.get("alpha_nam_pct"),
            "sharpe": kt["so_sanh"]["he"].get("sharpe"),
            "ly_do": [str(x)[:160] for x in kt["ly_do"][:3]],
        })
    except Exception as e:
        ra["moi"] = "LOI"
        ra["ly_do"] = f"{type(e).__name__}: {str(e)[:140]}"
    ra["giay"] = round(time.time() - t0, 2)
    return ra


def _cham_gop(gt: dict) -> dict:
    """Cham lai mot gia thuyet GOP qua dung duong cua no (`gop_lop.xet_gop`)."""
    import json as _j
    from nhan import gop_lop as GL
    from tru import quantlab as QL

    kt = GL.xet_gop(gt["template"], ho=gt["ho"], khung=gt["khung"],
                    tham_so=_j.loads(gt["tham_so"] or "{}"),
                    kho=QL._kho_pham_vi(gt["khung"]), gt_ma=gt["ma"],
                    da_dang_ky=True, ghi_so=False)          # <- bat bien 1
    if kt.get("loi") or "so_sanh" not in kt:
        return {"moi": kt.get("verdict") or "KHONG_DU_MAU",
                "ly_do": str(kt.get("ly_do") or kt.get("loi"))[:200]}
    dk = kt["dieu_kien"]
    al = kt["so_sanh"]["alpha_vs_mua_giu"]
    return {
        "moi": kt["verdict"], "che_do": kt.get("che_do"), "duong": "GOP",
        "dieu_kien": dk, "truot": [k for k, v in dk.items() if not v],
        "qua_1_2_3": all(dk.get(k) for k in
                         ("1_loi_hon_mua_giu", "2_sharpe_hon_mua_giu",
                          "3_calmar_hon_mua_giu")),
        "qua_4": bool(dk.get("4_alpha_duong_co_y_nghia")),
        "t_alpha": al.get("t_alpha"), "alpha_nam_pct": al.get("alpha_nam_pct"),
        "sharpe": kt["so_sanh"]["he"].get("sharpe"),
        "cach_biet": kt.get("cach_biet"),
        "ly_do": [str(x)[:160] for x in kt["ly_do"][:3]],
    }


def chay(chi_dsl: bool = False, luong: int = SO_TIEN_TRINH,
         ghi_so_cai: bool = True) -> dict:
    from nhan import cong as CONG
    gts = _lay_danh_sach(chi_dsl)
    print(f"cham lai {len(gts)} gia thuyet, {luong} tien trinh, "
          f"cong the he {CONG.THE_HE_CONG}")
    t0 = time.time()
    ket: list[dict] = []
    if luong <= 1:
        for i, g in enumerate(gts, 1):
            ket.append(_cham_mot(g))
            print(f"  [{i}/{len(gts)}] {ket[-1]['ma'][:52]:52s} "
                  f"{ket[-1]['cu']} -> {ket[-1]['moi']}")
    else:
        with Pool(luong) as p:
            for i, r in enumerate(p.imap_unordered(_cham_mot, gts), 1):
                ket.append(r)
                if i % 20 == 0 or i == len(gts):
                    print(f"  {i}/{len(gts)}  ({time.time() - t0:.0f}s)")

    tt = _tong_ket(ket, time.time() - t0)
    RA_JSON.parent.mkdir(parents=True, exist_ok=True)
    RA_JSON.write_text(json.dumps({"tong_ket": tt, "chi_tiet": ket},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    RA_MD.write_text(_bao_cao_md(tt, ket), encoding="utf-8")

    if ghi_so_cai:
        tt["da_dong_dau"] = _dong_dau_the_he(ket)     # <- bat bien 2
    print(json.dumps(tt, ensure_ascii=False, indent=1))
    print(f"\n-> {RA_MD}")
    return tt


def _tong_ket(ket: list[dict], giay: float) -> dict:
    c = Counter(r["moi"] for r in ket)
    chay_duoc = [r for r in ket if r["moi"] not in KHONG_CHAM_DUOC]
    doi = [r for r in chay_duoc if r["moi"] != r["cu"]]
    return {
        "tong": len(ket), "chay_duoc": len(chay_duoc),
        "khong_chay_duoc": len(ket) - len(chay_duoc),
        "verdict": dict(c),
        "qua_cong_1_2_3": sum(1 for r in chay_duoc if r.get("qua_1_2_3")),
        "qua_them_cong_4": sum(1 for r in chay_duoc
                               if r.get("qua_1_2_3") and r.get("qua_4")),
        "doi_phan_quyet": len(doi),
        "bat_len": [r["ma"] for r in doi if r["moi"] in
                    ("PASS", "CO_CO_CHE", "NGHI_NHIN_TRUOC")],
        "giay": round(giay, 1),
    }


def _dong_dau_the_he(ket: list[dict]) -> int:
    """Ghi `the_he_cong` cho nhung gia thuyet cham lai VAN khong bat len.

    Chi dong dau len cai khong doi. Cai bat len khong duoc dong dau o day - xem
    bat bien 2 o dau file.
    """
    from nhan import cong as CONG, so as SO
    ma = [r["ma"] for r in ket
          if r["moi"] not in KHONG_CHAM_DUOC
          and r["moi"] not in ("PASS", "CO_CO_CHE", "NGHI_NHIN_TRUOC")]
    if not ma:
        return 0
    with SO.ket_noi() as cn:
        cn.executemany("UPDATE gia_thuyet SET the_he_cong=? WHERE ma=?",
                       [(CONG.THE_HE_CONG, m) for m in ma])
    return len(ma)


def _bao_cao_md(tt: dict, ket: list[dict]) -> str:
    d = ["# Cham lai toan bo gia thuyet duoi THE HE CONG hien tai",
         "",
         f"- tong: **{tt['tong']}** · chay duoc **{tt['chay_duoc']}** · "
         f"khong chay duoc **{tt['khong_chay_duoc']}**",
         f"- qua cong 1-2-3: **{tt['qua_cong_1_2_3']}** · qua them cong 4: "
         f"**{tt['qua_them_cong_4']}**",
         f"- doi phan quyet so voi so cai: **{tt['doi_phan_quyet']}**",
         f"- thoi gian: {tt['giay']}s",
         "", "## Verdict", "", "| verdict | so |", "|---|---:|"]
    for k, v in sorted(tt["verdict"].items(), key=lambda x: -x[1]):
        d.append(f"| {k} | {v} |")
    d += ["", "## Truot cong nao (tren so chay duoc)", "", "| cong | truot |",
          "|---|---:|"]
    c: Counter = Counter()
    for r in ket:
        for k in r.get("truot", []):
            c[k] += 1
    for k, v in c.most_common():
        d.append(f"| {k} | {v} |")
    tot = sorted([r for r in ket if r.get("qua_1_2_3")],
                 key=lambda r: -(r.get("t_alpha") or 0))[:25]
    if tot:
        d += ["", "## Qua cong 1-2-3 (xep theo t_alpha)", "",
              "| gia thuyet | cu | moi | t_alpha | alpha %/nam | sharpe |",
              "|---|---|---|---:|---:|---:|"]
        for r in tot:
            d.append(f"| `{r['ma']}` | {r['cu']} | {r['moi']} | "
                     f"{r.get('t_alpha') or 0:.2f} | "
                     f"{r.get('alpha_nam_pct') or 0:.2f} | "
                     f"{r.get('sharpe') or 0:.2f} |")
    xau = [r for r in ket if r["moi"] in KHONG_CHAM_DUOC]
    if xau:
        d += ["", "## Khong cham duoc", "", "| gia thuyet | vi sao |", "|---|---|"]
        for r in xau:
            d.append(f"| `{r['ma']}` | {r.get('ly_do', '')} |")
    return "\n".join(d) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi-dsl", action="store_true",
                    help="chi cham gia thuyet dung template DSL (khong o mau.py)")
    ap.add_argument("--luong", type=int, default=SO_TIEN_TRINH)
    ap.add_argument("--khong-ghi", action="store_true",
                    help="khong dong dau the_he_cong vao so cai")
    a = ap.parse_args()
    chay(chi_dsl=a.chi_dsl, luong=a.luong, ghi_so_cai=not a.khong_ghi)
