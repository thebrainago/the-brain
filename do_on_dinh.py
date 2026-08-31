# -*- coding: utf-8 -*-
"""do_on_dinh.py - CAO NGUYEN hay CAI GAI? Do HINH DANG cua mot edge.

VI SAO CO FILE NAY
  Cau hoi cua chu du an (31/08/2026): "chay di chay lai mot chien luoc nhieu
  lan de xem dieu chinh co tao ra dieu gi khac nhau khong".

  Cau hoi do co HAI phien ban nguoc nhau:

  * **Phien ban hong** - chay nhieu cau hinh roi GIU CAI TOT NHAT. Do la
    curve-fitting, la dieu CLAUDE.md cam thang ("tuyet doi khong dung MT5
    optimization chon tham so"), va moi luot con an mot suat FDR.
  * **Phien ban dung** - chay ca VUNG LAN CAN roi hoi ve HINH DANG. Khong chon
    gi ca. Mot co che that co bien do sai so: doi tham so mot buoc thi ket qua
    xau di mot chut chu khong sup. Mot cai gai thi chi dung mot o la duong, va
    do la van may cua mot lan boc tham.

  File nay lam phien ban thu hai. Dau ra la DO ON DINH, khong phai tham so tot
  nhat - va no khong bao gio duoc phep cap PASS cho ai.

BA CON SO NO TRA VE
  `ty_le_duong`    bao nhieu % o trong lan can co alpha > 0.
  `boi_dinh`       o tot nhat / trung vi lan can. Cang lon cang giong cai gai.
                   Mot cao nguyen thuc su co boi_dinh gan 1.
  `do_doc`         di MOT buoc khoi tam thi mat bao nhieu % alpha (trung vi).

  Doc CHUNG ba con so. `ty_le_duong` cao mot minh khong du: mot suon doc deu
  duong van co the la drift cua chinh tai san doi lot.

HAI DIEU BAT BIEN (dung go ra)
  1. **KHONG TIEU SUAT FDR.** Moi loi goi cong deu `ghi_so=False`. Day la phep
     DO DAC tren du lieu da dung, khong phai mot vong kiem dinh moi.
  2. **KHONG CHON THAM SO.** Ham nay khong tra ve "cau hinh tot nhat" va khong
     ghi gi vao bang `gia_thuyet`. Neu ban thay minh muon lay o tot nhat ra
     dung, thi ban dang lam dung cai bay ma file nay sinh ra de tranh.

Chay:
    python do_on_dinh.py --ma AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55
    python do_on_dinh.py --mau rsi_dao_chieu --tai-san AUDCAD --khung H4
    python do_on_dinh.py --het-ung-vien          # moi gia thuyet dang PASS/CO_CO_CHE
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

RA_JSON = LAB / "reports" / "DO_ON_DINH.json"
RA_MD = LAB / "reports" / "DO_ON_DINH.md"

#: Buoc quanh tam cho tham so SO NGUYEN va tham so TY LE.
#: Lan can phai du rong de thay suon doc, du hep de con la CUNG MOT co che.
#: +-30% la muc mot nguoi van goi la "cung mot cau hinh, chinh mot chut".
BIEN_DO = 0.30
SO_BUOC = 2          # moi chieu: -2, -1, 0, +1, +2 -> 5 diem


def _lan_can_mot_tham_so(ten: str, gia_tri):
    """Sinh cac gia tri lan can quanh mot tham so. Giu nguyen KIEU."""
    if isinstance(gia_tri, bool):
        return [gia_tri]                       # bool khong co "lan can"
    if isinstance(gia_tri, int):
        b = max(1, int(round(abs(gia_tri) * BIEN_DO / SO_BUOC)))
        ds = [gia_tri + k * b for k in range(-SO_BUOC, SO_BUOC + 1)]
        return sorted({x for x in ds if x > 0})
    if isinstance(gia_tri, float):
        b = abs(gia_tri) * BIEN_DO / SO_BUOC
        return sorted({round(gia_tri + k * b, 6) for k in range(-SO_BUOC, SO_BUOC + 1)})
    return [gia_tri]


def lan_can(tham_so: dict, toi_da: int = 81) -> list[dict]:
    """Luoi lan can quanh `tham_so`. Tam LUON nam trong ket qua.

    `toi_da` la tran an toan: ba tham so x 5 diem = 125 o, va moi o la mot
    backtest. Vuot tran thi rut so buoc, roi neu van vuot thi DONG BANG han
    mot truc ve gia tri tam - khong bao gio cat bua danh sach. Ly do: `do_doc`
    va `boi_dinh` deu tinh tren gia dinh lan can CAN DOI quanh tam; mot danh
    sach bi cat mot phia lam ca hai con so do noi doi ma khong bao loi.
    Truc bi dong bang la truc KHONG duoc do - `so_o` trong bao cao cho thay.
    """
    ten = sorted(tham_so)
    truc = [_lan_can_mot_tham_so(k, tham_so[k]) for k in ten]

    def _so_o():
        return int(np.prod([len(x) for x in truc]))

    # Chang 1: rut moi truc ve 3 diem (van con hai phia quanh tam).
    while _so_o() > toi_da and any(len(x) > 3 for x in truc):
        i = max(range(len(truc)), key=lambda k: len(truc[k]))
        giua = (truc[i].index(tham_so[ten[i]]) if tham_so[ten[i]] in truc[i]
                else len(truc[i]) // 2)
        truc[i] = [truc[i][max(0, giua - 1)], truc[i][giua],
                   truc[i][min(len(truc[i]) - 1, giua + 1)]]
    # Chang 2: van vuot tran -> DONG BANG han mot truc ve dung gia tri tam.
    # Tha khong do mot chieu con hon do lech mot phia: `do_doc` va `boi_dinh`
    # deu tinh tren gia dinh lan can can doi quanh tam.
    i = 0
    while _so_o() > toi_da and i < len(truc):
        if len(truc[i]) > 1:
            truc[i] = [tham_so[ten[i]]]
        i += 1
    ra = [dict(zip(ten, bo)) for bo in product(*truc)]
    if tham_so not in ra:
        ra.insert(0, dict(tham_so))
    return ra


def _khoang_cach(a: dict, tam: dict) -> int:
    """So THAM SO khac tam. Day la 'may buoc' theo nghia cua `do_doc`."""
    return sum(1 for k in tam if a.get(k) != tam[k])


def do_mot_o(mau: str, tham_so: dict, tai_san: str, khung: str) -> dict:
    """Mot o cua lan can. Tra alpha/nam va t_alpha, KHONG tra phan quyet."""
    from nhan import cong as CONG, mau as MAU, mo_phong as MP, ngu_phap as NP
    from tru import quantlab as QL
    NP.nap_vao_mau()
    try:
        _df, _tr, holdout, _c, cp = QL._nap(tai_san, khung)
        th = MAU.sinh(mau, holdout, tham_so)
        kq = MP.chay(holdout, th, cp, ma=tai_san, khung=khung)
        bh = MP.mua_giu(holdout, cp, ma=tai_san, khung=khung)
        che_do = QL._che_do(cp)
        kt = CONG.xet(holdout, kq, bh, cp, gt_ma=f"ONDINH.{mau}", ho="do_on_dinh",
                      da_dang_ky=True, tren_holdout=True, che_do=che_do,
                      chay_placebo=False,       # lan can khong can placebo
                      ghi_so=False)             # <- bat bien 1
        al = kt["so_sanh"]["alpha_vs_mua_giu"]
        return {"tham_so": tham_so, "alpha": al.get("alpha_nam_pct"),
                "t": al.get("t_alpha"), "sharpe": kt["so_sanh"]["he"].get("sharpe"),
                "so_lenh": kt["so_sanh"]["he"].get("so_lenh")}
    except Exception as e:
        return {"tham_so": tham_so, "alpha": None, "t": None,
                "loi": f"{type(e).__name__}: {str(e)[:90]}"}


def do_hinh_dang(mau: str, tam: dict, tai_san: str, khung: str,
                 luong: int = 6) -> dict:
    """Chay ca lan can quanh `tam` roi tra HINH DANG."""
    from multiprocessing import Pool
    o = lan_can(tam)
    t0 = time.time()
    doi_so = [(mau, ts, tai_san, khung) for ts in o]
    if luong <= 1:
        ket = [do_mot_o(*x) for x in doi_so]
    else:
        with Pool(luong) as p:
            ket = p.starmap(do_mot_o, doi_so)

    chay = [r for r in ket if r.get("alpha") is not None]
    if not chay:
        return {"mau": mau, "tai_san": tai_san, "khung": khung, "tam": tam,
                "do_duoc": False, "ly_do": "khong o nao chay duoc",
                "so_o": len(o), "giay": round(time.time() - t0, 1)}

    a = np.array([r["alpha"] for r in chay], dtype=float)
    r_tam = next((r for r in chay if r["tham_so"] == tam), None)
    trung_vi = float(np.median(a))
    tot_nhat = float(np.max(a))

    # `do_doc`: di dung MOT tham so khoi tam thi mat bao nhieu % alpha.
    mot_buoc = [r["alpha"] for r in chay if _khoang_cach(r["tham_so"], tam) == 1]
    a_tam = r_tam["alpha"] if r_tam else None
    do_doc = None
    if a_tam and mot_buoc and abs(a_tam) > 1e-9:
        do_doc = round(float((a_tam - np.median(mot_buoc)) / abs(a_tam) * 100.0), 1)

    return {
        "mau": mau, "tai_san": tai_san, "khung": khung, "tam": tam,
        "do_duoc": True,
        "so_o": len(o), "chay_duoc": len(chay),
        "alpha_tam": a_tam,
        "ty_le_duong": round(float(np.mean(a > 0)) * 100.0, 1),
        "trung_vi_lan_can": round(trung_vi, 3),
        "o_tot_nhat": round(tot_nhat, 3),
        "boi_dinh": round(tot_nhat / trung_vi, 2) if abs(trung_vi) > 1e-9 else None,
        "do_doc_mot_buoc_pct": do_doc,
        "tam_co_phai_dinh": bool(r_tam and abs(a_tam - tot_nhat) < 1e-9),
        "hinh_dang": _dat_ten(float(np.mean(a > 0)), trung_vi, tot_nhat, a_tam),
        "giay": round(time.time() - t0, 1),
        "o": sorted(chay, key=lambda r: -(r["alpha"] or -1e9)),
    }


def _dat_ten(ty_le_duong: float, trung_vi: float, tot_nhat: float,
             a_tam) -> str:
    """Dat ten hinh dang. Day la MO TA, khong phai phan quyet.

    Nguong chon theo y nghia chu khong theo toi uu: mot cao nguyen phai co da
    so o duong VA dinh khong noi len han so voi phan con lai.
    """
    if a_tam is None:
        return "khong_do_duoc"
    if ty_le_duong < 0.5:
        return "CAI GAI - da so lan can AM"
    if abs(trung_vi) < 1e-9:
        return "khong_ket_luan_duoc"
    boi = tot_nhat / trung_vi
    if boi > 3.0:
        return "CAI GAI - dinh cao gap %.1f lan trung vi lan can" % boi
    if ty_le_duong >= 0.8 and boi <= 2.0:
        return "CAO NGUYEN - %.0f%% lan can duong, dinh chi gap %.1f lan" % (
            ty_le_duong * 100, boi)
    return "SUON DOC - %.0f%% duong, dinh gap %.1f lan" % (ty_le_duong * 100, boi)


def _tach_ma(ma: str):
    """`AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` -> tra ve tu SO CAI.

    Khong tach chuoi bang tay: ten mau va tham so deu co dau cham/gach duoi,
    va so cai da co san cot rieng cho tung phan.
    """
    from nhan import so as SO
    gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", ma)
    if not gt:
        raise SystemExit(f"khong co gia thuyet {ma} trong so cai")
    return (gt["template"], json.loads(gt["tham_so"] or "{}"),
            gt["tai_san"], gt["khung"])


def _bao_cao_md(ds: list[dict]) -> str:
    d = ["# Cao nguyen hay cai gai — hinh dang cua edge", "",
         "> Do VUNG LAN CAN quanh mot cau hinh roi hoi ve HINH DANG. **Khong chon",
         "> tham so** va khong tieu suat FDR (`ghi_so=False`). Mot co che that co",
         "> bien do sai so; mot cai gai thi chi dung mot o la duong.", ""]
    for r in ds:
        d.append(f"## `{r['mau']}` tren {r['tai_san']}.{r['khung']}")
        d.append("")
        if not r.get("do_duoc"):
            d += [f"- KHONG DO DUOC: {r.get('ly_do')}", ""]
            continue
        d += [f"- **{r['hinh_dang']}**",
              f"- tam: `{json.dumps(r['tam'], ensure_ascii=False)}` -> "
              f"alpha **{r['alpha_tam']}%/nam**",
              f"- lan can: {r['chay_duoc']}/{r['so_o']} o chay duoc · "
              f"**{r['ty_le_duong']}% duong** · trung vi {r['trung_vi_lan_can']}% · "
              f"o tot nhat {r['o_tot_nhat']}%",
              f"- boi dinh: **{r['boi_dinh']}x** · do doc mot buoc: "
              f"**{r['do_doc_mot_buoc_pct']}%** · tam co phai dinh: "
              f"{'CO' if r['tam_co_phai_dinh'] else 'khong'}",
              f"- {r['giay']}s", "",
              "| tham so | alpha %/nam | t | sharpe |", "|---|---:|---:|---:|"]
        for o in r["o"][:15]:
            d.append(f"| `{json.dumps(o['tham_so'], ensure_ascii=False)}` | "
                     f"{o['alpha']:.3f} | {(o['t'] or 0):.2f} | "
                     f"{(o['sharpe'] or 0):.2f} |")
        d.append("")
    return "\n".join(d) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ma", help="ma gia thuyet trong so cai")
    ap.add_argument("--mau")
    ap.add_argument("--tai-san")
    ap.add_argument("--khung", default="D1")
    ap.add_argument("--tham-so", default="{}", help="JSON tam cua lan can")
    ap.add_argument("--het-ung-vien", action="store_true",
                    help="moi gia thuyet dang PASS / CO_CO_CHE trong so cai")
    ap.add_argument("--luong", type=int, default=6)
    a = ap.parse_args()

    viec = []
    if a.het_ung_vien:
        from nhan import so as SO
        for g in SO.nhieu("SELECT ma FROM gia_thuyet WHERE trang_thai IN "
                          "('PASS','CO_CO_CHE') ORDER BY id"):
            viec.append(_tach_ma(g["ma"]))
    elif a.ma:
        viec.append(_tach_ma(a.ma))
    elif a.mau and a.tai_san:
        viec.append((a.mau, json.loads(a.tham_so), a.tai_san, a.khung))
    else:
        ap.error("can --ma, hoac --mau + --tai-san, hoac --het-ung-vien")

    ds = []
    for mau, ts, tai_san, khung in viec:
        print(f"do lan can quanh {mau} {ts} tren {tai_san}.{khung} ...")
        r = do_hinh_dang(mau, ts, tai_san, khung, luong=a.luong)
        ds.append(r)
        print("  ->", r.get("hinh_dang") or r.get("ly_do"), f"({r['giay']}s)")

    RA_JSON.parent.mkdir(parents=True, exist_ok=True)
    RA_JSON.write_text(json.dumps(ds, ensure_ascii=False, indent=1, default=str),
                       encoding="utf-8")
    RA_MD.write_text(_bao_cao_md(ds), encoding="utf-8")
    print(f"\n-> {RA_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
