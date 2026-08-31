# -*- coding: utf-8 -*-
"""hinh_dang_vs_null.py - HINH DANG cua edge co phan biet duoc voi NGAU NHIEN khong?

VI SAO CO FILE NAY (31/08/2026)
  `do_on_dinh.py` (30-31/08) tra loi duoc "cao nguyen hay cai gai" cho MOT cau
  hinh: do vung lan can roi nhin ty le o duong, boi dinh, do doc. Nhung ba con
  so do chua bao gio duoc HIEU CHUAN. Mot chuoi gia hoan toan ngau nhien cung
  sinh ra lan can co 90% o duong neu chinh tai san do di len; va mot luoi tham
  so nao cung co mot o cao nhat, tuc `boi_dinh` luon > 1.

  Cau hoi that la: **hinh dang cua ung vien that co khac hinh dang cua cung
  luoi tham so do chay tren chuoi NULL khong?** Neu khong khac, thi "cao nguyen"
  khong phai bang chung ve co che - no chi la hinh dang cua mot be mat tron.

  Day dung mot bai hoc da ghi: mot cong tu choi tat ca va mot cong khong lam gi
  cho ket qua Y HET nhau neu khong ai do LUC. Cung the, mot thong ke hinh dang
  chi co nghia khi biet no phan bo the nao duoi gia thuyet null.

CACH DO
  Voi moi ung vien (mau + tham so tam + tai san + khung):
    1. Chay CA LUOI LAN CAN tren holdout THAT   -> hinh dang that.
    2. Sinh `--null` chuoi null tu chinh holdout do (block bootstrap va
       permute_time, luan phien), moi chuoi giu nguyen phan phoi HINH DANG BAR
       cua chuoi that (`nha_may_null.bar_tu_chuoi_null`).
    3. Chay Y HET luoi lan can do tren tung chuoi null -> phan bo null cua
       tung thong ke hinh dang.
    4. Bao cao PHAN VI cua gia tri that trong phan bo null. p = ty le chuoi
       null cho gia tri >= gia tri that (mot phia, co +1 hieu chinh).

  Chi phi giao dich lay tu chuoi THAT va dung nguyen cho null: null phai chiu
  dung ma sat do, neu khong thi so sanh la gian lan mot chieu.

HAI DIEU BAT BIEN (giong `do_on_dinh.py` - dung go ra)
  1. **KHONG TIEU SUAT FDR.** Moi loi goi cong deu `ghi_so=False`. Day la phep
     DO DAC tren du lieu da dung. Bo do nay goi cong hang tram nghin lan; de no
     ghi so thi ngan sach kiem dinh cua ca du an bay trong mot dem.
  2. **KHONG CHON THAM SO va KHONG CAP PHAN QUYET.** Dau ra la mot con so ve
     BANG CHUNG HINH DANG, khong phai mot PASS, va khong ghi gi vao bang
     `gia_thuyet`.

Chay:
    python hinh_dang_vs_null.py --qua-123          # ung vien qua cong 1-2-3
    python hinh_dang_vs_null.py --het              # ca 361 gia thuyet
    python hinh_dang_vs_null.py --ma AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55
    python hinh_dang_vs_null.py --qua-123 --null 20 --luong 6 --tiep

`--tiep` doc lai JSON cu va bo qua ung vien da do xong: bo do nay chay hang gio
va phai song sot qua mot lan may ngu.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

RA_JSON = LAB / "reports" / "HINH_DANG_VS_NULL.json"
RA_MD = LAB / "reports" / "HINH_DANG_VS_NULL.md"

SO_NULL = 20          # so chuoi null moi ung vien
TRAN_O = 25           # tran so o cua luoi lan can (that VA moi chuoi null)
PP_NULL = ("block_bootstrap", "permute_time")


# ------------------------------------------------------------------ do dac

def _chuoi_null(hold, so_chuoi: int, hat: int = 4242):
    """SINH LAN LUOT `so_chuoi` khung bar null tu chinh holdout that.

    Luan phien hai phuong phap: block bootstrap giu cum bien dong, permute_time
    pha sach moi tuong quan chuoi. Mot co che that phai vuot ca hai.

    La MOT GENERATOR co chu y: 100 chuoi null cua mot cap H1 la ~300 MB, va sau
    tien trinh cung chay thi may het RAM truoc khi het viec. Moi luc chi mot
    khung bar null ton tai.
    """
    from nhan import mo_phong as MP, nha_may_null as NULL
    r = MP._loi_suat_tien(hold)
    r = np.asarray(r, dtype=float)
    r = r[r != 0]
    if len(r) < 200:
        return
    for i in range(so_chuoi):
        pp = PP_NULL[i % len(PP_NULL)]
        if pp == "block_bootstrap":
            rn = NULL._block_bootstrap(r, hat + i)
        else:
            rng = np.random.default_rng(hat + 10_000 + i)
            rn = r[rng.permutation(len(r))]
        d = NULL.bar_tu_chuoi_null(rn, hold, hat=hat + i)
        if d is not None:
            yield pp, d


def _alpha_mot_o(mau: str, tham_so: dict, df, cp, ma: str, khung: str,
                 che_do: str):
    """Alpha/nam cua MOT o tren MOT khung bar. None neu o do khong chay duoc."""
    from nhan import cong as CONG, mau as MAU, mo_phong as MP
    try:
        th = MAU.sinh(mau, df, tham_so)
        kq = MP.chay(df, th, cp, ma=ma, khung=khung)
        bh = MP.mua_giu(df, cp, ma=ma, khung=khung)
        kt = CONG.xet(df, kq, bh, cp, gt_ma=f"HDNULL.{mau}", ho="hinh_dang_vs_null",
                      da_dang_ky=True, tren_holdout=True, che_do=che_do,
                      chay_placebo=False,      # lan can khong can placebo
                      ghi_so=False)            # <- bat bien 1
        return kt["so_sanh"]["alpha_vs_mua_giu"].get("alpha_nam_pct")
    except Exception:
        return None


def _hinh_dang(luoi: list[dict], alphas: list, tam: dict) -> dict:
    """Ba thong ke hinh dang tu mot luoi da chay. Giong `do_on_dinh`."""
    import do_on_dinh as OD
    cap = [(ts, a) for ts, a in zip(luoi, alphas) if a is not None]
    if not cap:
        return {"do_duoc": False}
    a = np.array([x[1] for x in cap], dtype=float)
    a_tam = next((x[1] for x in cap if x[0] == tam), None)
    trung_vi = float(np.median(a))
    tot_nhat = float(np.max(a))
    mot_buoc = [x[1] for x in cap if OD._khoang_cach(x[0], tam) == 1]
    do_doc = None
    if a_tam and mot_buoc and abs(a_tam) > 1e-9:
        do_doc = float((a_tam - np.median(mot_buoc)) / abs(a_tam) * 100.0)
    return {
        "do_duoc": True, "chay_duoc": len(cap),
        "alpha_tam": a_tam,
        "ty_le_duong": float(np.mean(a > 0)) * 100.0,
        "trung_vi": trung_vi, "o_tot_nhat": tot_nhat,
        "boi_dinh": (tot_nhat / trung_vi) if abs(trung_vi) > 1e-9 else None,
        "do_doc_mot_buoc_pct": do_doc,
        "hinh_dang": OD._dat_ten(float(np.mean(a > 0)), trung_vi, tot_nhat, a_tam),
    }


def _phan_vi(that, ds_null: list, cao_la_tot: bool = True) -> dict | None:
    """p mot phia: ty le chuoi null dat toi hoac hon gia tri that.

    Cong +1 ca tu va mau (hieu chinh Davison-Hinkley): voi 20 chuoi null, p nho
    nhat co the la 1/21 = 0,048 - va do la GIOI HAN DO PHAN GIAI cua bo do nay,
    khong phai mot con so co the lam nho tuy y bang cach nhin ky hon.
    """
    v = [x for x in ds_null if x is not None]
    if that is None or not v:
        return None
    v = np.asarray(v, dtype=float)
    dat = int(np.sum(v >= that)) if cao_la_tot else int(np.sum(v <= that))
    return {"p": round((dat + 1) / (len(v) + 1), 4),
            "so_null": len(v),
            "null_trung_vi": round(float(np.median(v)), 3),
            "null_p95": round(float(np.percentile(v, 95)), 3)}


def do_mot_ung_vien(gt: dict, so_null: int = SO_NULL, tran_o: int = TRAN_O) -> dict:
    """Ham muc GOC de Pool pickle duoc. Mot ung vien = that + `so_null` null."""
    import sys as _s
    _s.path.insert(0, str(LAB))
    import do_on_dinh as OD
    from nhan import ngu_phap as NP
    from tru import quantlab as QL

    NP.nap_vao_mau()
    t0 = time.time()
    ma, mau, khung = gt["ma"], gt["template"], gt["khung"]
    ra = {"ma": ma, "mau": mau, "tai_san": gt["tai_san"], "khung": khung}
    try:
        tam = json.loads(gt["tham_so"] or "{}")
        ra["tam"] = tam
        if not tam:
            ra["do_duoc"] = False
            ra["ly_do"] = "khong co tham so -> khong co lan can de do"
            return ra
        _df, _tr, hold, _c, cp = QL._nap(gt["tai_san"], khung)
        if len(hold) < 300:
            ra["do_duoc"] = False
            ra["ly_do"] = f"holdout {len(hold)} bar"
            return ra
        che_do = QL._che_do(cp)
        luoi = OD.lan_can(tam, toi_da=tran_o)

        that = _hinh_dang(
            luoi, [_alpha_mot_o(mau, ts, hold, cp, gt["tai_san"], khung, che_do)
                   for ts in luoi], tam)
        if not that.get("do_duoc"):
            ra.update({"do_duoc": False, "ly_do": "khong o nao chay duoc tren chuoi that"})
            return ra

        null_ket = []
        for pp, dn in _chuoi_null(hold, so_null):
            h = _hinh_dang(
                luoi, [_alpha_mot_o(mau, ts, dn, cp, gt["tai_san"], khung, che_do)
                       for ts in luoi], tam)
            if h.get("do_duoc"):
                h["pp"] = pp
                null_ket.append(h)

        ra.update({
            "do_duoc": True, "che_do": che_do, "so_o": len(luoi),
            "so_null_chay_duoc": len(null_ket),
            "that": {k: (round(v, 3) if isinstance(v, float) else v)
                     for k, v in that.items()},
            "so_voi_null": {
                "alpha_tam": _phan_vi(that.get("alpha_tam"),
                                      [h.get("alpha_tam") for h in null_ket]),
                "ty_le_duong": _phan_vi(that.get("ty_le_duong"),
                                        [h.get("ty_le_duong") for h in null_ket]),
                "boi_dinh": _phan_vi(that.get("boi_dinh"),
                                     [h.get("boi_dinh") for h in null_ket],
                                     cao_la_tot=False),   # boi dinh THAP moi tot
                "o_tot_nhat": _phan_vi(that.get("o_tot_nhat"),
                                       [h.get("o_tot_nhat") for h in null_ket]),
            },
        })
    except Exception as e:
        ra.update({"do_duoc": False, "ly_do": f"{type(e).__name__}: {str(e)[:140]}"})
    ra["giay"] = round(time.time() - t0, 1)
    return ra


# ------------------------------------------------------------------ chon viec

def _ung_vien(che: str, ma: str | None) -> list[dict]:
    from nhan import so as SO
    if ma:
        g = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", ma)
        if not g:
            raise SystemExit(f"khong co gia thuyet {ma}")
        return [dict(g)]
    gts = [dict(g) for g in SO.nhieu("SELECT * FROM gia_thuyet ORDER BY id")]
    if che == "het":
        return gts
    # qua-123: lay tu ban cham lai gan nhat (khong chay lai cong)
    f = LAB / "reports" / "CHAM_LAI_THE_HE.json"
    if not f.exists():
        raise SystemExit("chua co reports/CHAM_LAI_THE_HE.json - chay `b cham-lai` truoc")
    d = json.loads(f.read_text(encoding="utf-8"))
    ds = d.get("chi_tiet") or d.get("ket_qua") or []
    qua = {r["ma"] for r in ds if r.get("qua_1_2_3")}
    return [g for g in gts if g["ma"] in qua]


def _bao_cao_md(ds: list[dict]) -> str:
    xong = [r for r in ds if r.get("do_duoc")]
    d = ["# Hinh dang co phan biet duoc voi ngau nhien khong?", "",
         "> Cung mot luoi lan can, chay tren holdout THAT va tren chuoi NULL sinh",
         "> tu chinh no. Cot `p` = ty le chuoi null dat toi hoac hon gia tri that",
         "> (co +1 hieu chinh, nen p nho nhat la 1/(so_null+1)). Khong tieu suat",
         "> FDR, khong cap phan quyet.", "",
         f"- do duoc: **{len(xong)}/{len(ds)}** ung vien", ""]
    if xong:
        for ten, khoa in (("alpha o tam", "alpha_tam"),
                          ("ty le o duong", "ty_le_duong"),
                          ("o tot nhat", "o_tot_nhat")):
            ps = [r["so_voi_null"][khoa]["p"] for r in xong
                  if r["so_voi_null"].get(khoa)]
            if ps:
                d.append(f"- **{ten}**: trung vi p = {np.median(ps):.3f} · "
                         f"so ung vien p<=0,05: **{sum(1 for p in ps if p <= 0.05)}"
                         f"/{len(ps)}**")
        d.append("")
    d += ["## Tung ung vien (xep theo p cua alpha o tam)", "",
          "| ung vien | hinh dang that | alpha tam | p(alpha) | p(ty le duong) "
          "| p(boi dinh) | null p95 alpha |", "|---|---|---:|---:|---:|---:|---:|"]

    def _p(r, k):
        x = r["so_voi_null"].get(k)
        return x["p"] if x else None

    for r in sorted(xong, key=lambda x: (_p(x, "alpha_tam") is None,
                                         _p(x, "alpha_tam") or 1.0)):
        n95 = r["so_voi_null"].get("alpha_tam") or {}
        d.append(f"| `{r['ma']}` | {r['that'].get('hinh_dang', '')} | "
                 f"{r['that'].get('alpha_tam')} | {_p(r, 'alpha_tam')} | "
                 f"{_p(r, 'ty_le_duong')} | {_p(r, 'boi_dinh')} | "
                 f"{n95.get('null_p95')} |")
    hong = [r for r in ds if not r.get("do_duoc")]
    if hong:
        d += ["", "## Khong do duoc", ""]
        for r in hong[:40]:
            d.append(f"- `{r['ma']}`: {r.get('ly_do')}")
    return "\n".join(d) + "\n"


def _ghi(ds: list[dict], tham: dict) -> None:
    RA_JSON.write_text(json.dumps({"luc": time.strftime("%Y-%m-%d %H:%M:%S"),
                                   "tham_so_chay": tham, "ket_qua": ds},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    RA_MD.write_text(_bao_cao_md(ds), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ma", help="mot gia thuyet cu the")
    ap.add_argument("--qua-123", action="store_true",
                    help="ung vien qua cong 1-2-3 trong ban cham lai gan nhat")
    ap.add_argument("--het", action="store_true", help="moi gia thuyet trong so cai")
    ap.add_argument("--null", type=int, default=SO_NULL)
    ap.add_argument("--tran-o", type=int, default=TRAN_O)
    ap.add_argument("--luong", type=int, default=6)
    ap.add_argument("--tiep", action="store_true", help="bo qua ung vien da do xong")
    a = ap.parse_args()

    che = "het" if a.het else "qua_123"
    viec = _ung_vien(che, a.ma)
    cu: list[dict] = []
    if a.tiep and RA_JSON.exists():
        try:
            cu = json.loads(RA_JSON.read_text(encoding="utf-8")).get("ket_qua", [])
        except Exception:
            cu = []
        da = {r["ma"] for r in cu}
        viec = [g for g in viec if g["ma"] not in da]

    tham = {"che": che, "so_null": a.null, "tran_o": a.tran_o, "luong": a.luong}
    print(f"[hinh_dang_vs_null] {len(viec)} ung vien · {a.null} null moi ung vien "
          f"· tran {a.tran_o} o · {a.luong} luong", flush=True)
    if not viec:
        _ghi(cu, tham)
        return 0

    ds = list(cu)
    t0 = time.time()
    if a.luong <= 1:
        lap = (do_mot_ung_vien(g, a.null, a.tran_o) for g in viec)
    else:
        from multiprocessing import Pool
        p = Pool(a.luong)
        lap = p.imap_unordered(
            _goi, [(g, a.null, a.tran_o) for g in viec])
    for i, r in enumerate(lap, 1):
        ds.append(r)
        _ghi(ds, tham)          # ghi sau MOI ung vien: bo do nay chay hang gio
        pa = (r.get("so_voi_null") or {}).get("alpha_tam") or {}
        print(f"  [{i}/{len(viec)}] {r['ma']} · {r.get('that', {}).get('hinh_dang', r.get('ly_do', ''))}"
              f" · p={pa.get('p')} · {r.get('giay')}s", flush=True)
    if a.luong > 1:
        p.close(); p.join()
    print(f"[xong] {len(ds)} ung vien · {round(time.time() - t0, 1)}s -> {RA_MD.name}",
          flush=True)
    return 0


def _goi(doi_so):
    return do_mot_ung_vien(*doi_so)


if __name__ == "__main__":
    raise SystemExit(main())
