# -*- coding: utf-8 -*-
"""tinh_cach_chieu.py - TINH CACH TAI SAN -> CHIEU DAT LUOI, BUOC, CHAN TROI.

## Cho nghen that, va vi sao module nay ton tai

Chu du an, 15/09/2026: *"Vi du ve tinh tuong quan va dac tinh tai san cau da
tinh ra chua? Tinh ra roi thi ta ap dung nhu nao. Cau noi toi la he thong khong
can entry thi can co tinh chat cap tien vay thi cau da ap dung duoc chua? Cap co
trend thi danh ve chieu thuan trend, cap sideway ta danh ve giua."*

Kiem lai thi dung: **da DO nhung chua NOI**.

  - `config/ho_so_symbol.json` co 158 ma voi `nhan_tinh_cach`, Hurst, VR, nua doi
  - `reports/PMG_G0.json` co 48 o voi `huong_de_xuat` da qua FDR
  - `grep -rn "ho_so_symbol|nhan_tinh_cach|hurst" nhan/pmg*.py` -> **RONG**

Tuc `pmg_quet.sinh_cau_hinh(..., direction=...)` nhan chieu tu nguoi goi va quet
mu ca hai chieu, trong khi cau tra loi da nam san trong hai file tren suot may
ngay. Module nay la cai cau con thieu.

## Ba cau hoi no tra loi (khong phai mot)

Tinh cach khong chi noi CHIEU. Doc du thi no noi ca ba thu can de dat mot luoi:

  1. **CHIEU**   hoi quy -> `AGAINST` (danh ve giua) · xu huong -> `WITH`
  2. **BUOC**    tu `bien_do_bar_pct`: buoc phai >= 2x bien do nen, neu khong
                 thi bar khong do duoc luoi (`pmg_engine.NGUONG_PHAN_GIAI`)
  3. **CHAN TROI** tu `nua_doi_bar`: hoi quy ma nua doi 934 bar thi giu lenh 20
                 bar la cat truoc khi co che kip chay

## Thu tu bang chung - KHONG duoc dao

`G0` do TREN KHUNG SE GIAO DICH va co kiem soat FDR, nen no thang `ho_so`. Ho so
do tren D1 cho MOI ma; dung no cho M5 la mot gia dinh, va gia dinh do da sai mot
lan roi (H4 va D1 cho ket luan khac nhau - xem ghi chu "Quet phai mo DA KHUNG").

## `TRUNG_TINH` khong phai tung dong xu

Ma khong nghieng ben nao thi tra `CHUA_DO_DUOC`, KHONG tra chieu mac dinh. Duoi
random walk, ky vong cua luoi khong entry la **dung bang -chi phi**; chon bua mot
chieu chi doi cai chac chan lo lay mot cai co ve 50/50.
"""
from __future__ import annotations

import collections
import json
import math
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
KHO_HO_SO = LAB / "config" / "ho_so_symbol.json"
BANG_G0 = LAB / "reports" / "PMG_G0.json"

#: Tinh cach D1 -> chieu luoi. `TRUNG_TINH` co y KHONG nam trong bang.
CHIEU_THEO_TINH_CACH = {"HOI_QUY": "AGAINST", "XU_HUONG": "WITH"}

#: Buoc luoi phai >= bao nhieu lan bien do mot nen. Giong
#: `pmg_engine.NGUONG_PHAN_GIAI` - hep hon nguong nay thi bar khong do duoc luoi
#: va moi con so deu la do mo hinh duong di trong nen che ra.
BOI_BUOC_TOI_THIEU = 2.0

#: Giu lenh toi thieu bao nhieu lan nua doi thi co che moi kip chay. Nua doi la
#: thoi gian de MOT NUA do lech tan di, nen mot nua doi la nguong san.
BOI_CHAN_TROI = 1.0

#: Bang chung G0 phai DA SO RO RANG moi tinh. Duoi muc nay la mau thuan, va mau
#: thuan thi khong phai bang chung.
TY_LE_DA_SO = 0.7


def _doc(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def ho_so(ma: str) -> dict | None:
    """Ho so D1 cua mot ma, hoac `None`.

    Chap nhan ca ten tren terminal (`AUDCADmicro`) lan ten trong kho (`AUDCAD`).
    Hai ten nay khac nhau, va da mat mot luot tester 628 giay vi cho do.
    """
    d = _doc(KHO_HO_SO)
    if not d:
        return None
    hs = d.get("ho_so") or {}
    if isinstance(hs, list):
        hs = {x.get("ma"): x for x in hs if isinstance(x, dict)}
    if not isinstance(hs, dict):
        return None
    ma_u = str(ma).upper()
    if ma_u in hs:
        return hs[ma_u]
    for k in hs:
        ku = str(k).upper()
        if ma_u.startswith(ku) or ku.startswith(ma_u):
            return hs[k]
    return None


def _o_g0(ma: str) -> list[dict]:
    """Cac o G0 cua mot ma. Rong khi chua quet ma do - do la CHUA_DO_DUOC."""
    d = _doc(BANG_G0) or {}
    o = d.get("o")
    if not isinstance(o, list):
        for v in d.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                o = v
                break
    if not isinstance(o, list):
        return []
    ma_u = str(ma).upper()
    ra = []
    for x in o:
        if not isinstance(x, dict):
            continue
        k = str(x.get("ma", "")).upper()
        if k and (k == ma_u or ma_u.startswith(k) or k.startswith(ma_u)):
            ra.append(x)
    return ra


def chieu_luoi(ma: str) -> dict:
    """Chieu nen dat luoi cho `ma`, kem BANG CHUNG va DO TIN.

    Tra ve dict:
      `chieu`      "AGAINST" | "WITH" | None
      `trang_thai` "DAT" | "CHUA_DO_DUOC"
      `do_tin`     "G0" (do tren khung giao dich, co FDR) | "HO_SO" (suy tu D1)
      `vi_sao`     mot cau doc duoc, khong phai mot con so tran
    """
    o = _o_g0(ma)
    qua = [x for x in o if x.get("qua_fdr")]
    if qua:
        dem = collections.Counter(x.get("huong_de_xuat") for x in qua)
        chieu, n = dem.most_common(1)[0]
        khung = qua[0].get("khung", "?")
        if n >= TY_LE_DA_SO * len(qua):
            return {"chieu": chieu, "trang_thai": "DAT", "do_tin": "G0",
                    "so_o_qua": len(qua), "so_o": len(o), "khung_do": khung,
                    "vi_sao": ("G0 tren %s: %d/%d o qua FDR, %d o trong so do chi "
                               "%s" % (khung, len(qua), len(o), n, chieu))}
        return {"chieu": None, "trang_thai": "CHUA_DO_DUOC", "do_tin": "G0",
                "so_o_qua": len(qua), "so_o": len(o), "khung_do": khung,
                "vi_sao": "G0 mau thuan giua cac chan troi: %s" % dict(dem)}

    hs = ho_so(ma)
    if not hs:
        return {"chieu": None, "trang_thai": "CHUA_DO_DUOC", "do_tin": None,
                "vi_sao": "khong co o G0 nao qua FDR va khong co ho so cho ma nay"}
    nhan = str(hs.get("nhan_tinh_cach") or "")
    chieu = CHIEU_THEO_TINH_CACH.get(nhan)
    if not chieu:
        return {"chieu": None, "trang_thai": "CHUA_DO_DUOC", "do_tin": "HO_SO",
                "nhan_tinh_cach": nhan,
                "vi_sao": ("tinh cach '%s' khong nghieng ben nao - chon bua mot "
                           "chieu chi doi -chi phi chac chan lay mot cai co ve "
                           "50/50" % (nhan or "khong ro"))}
    return {"chieu": chieu, "trang_thai": "DAT", "do_tin": "HO_SO",
            "nhan_tinh_cach": nhan, "hurst": hs.get("hurst"),
            "khung_do": "D1",
            "vi_sao": ("ho so D1: %s (Hurst %.3f, VR2 %.3f, ac1 %+.4f) -> %s. "
                       "CHUA do tren khung se giao dich."
                       % (nhan, float(hs.get("hurst") or 0),
                          float(hs.get("vr2") or 0), float(hs.get("ac1") or 0),
                          chieu))}


def buoc_toi_thieu_pct(ma: str) -> dict:
    """Buoc luoi nho nhat con DO DUOC tren bar, theo % gia."""
    hs = ho_so(ma)
    if not hs:
        return {"buoc_pct": None, "trang_thai": "CHUA_DO_DUOC",
                "vi_sao": "khong co ho so cho ma nay"}
    bd = hs.get("bien_do_bar_pct")
    try:
        bd = float(bd)
    except (TypeError, ValueError):
        bd = 0.0
    if bd <= 0:
        return {"buoc_pct": None, "trang_thai": "CHUA_DO_DUOC",
                "vi_sao": "ho so khong co `bien_do_bar_pct` dung duoc"}
    return {"buoc_pct": bd * BOI_BUOC_TOI_THIEU, "trang_thai": "DAT",
            "bien_do_bar_pct": bd, "khung_do": "D1",
            "vi_sao": ("buoc phai >= %.1fx bien do nen (%.3f%%) = %.3f%%; hep hon "
                       "thi bar khong do duoc luoi va moi so deu do mo hinh duong "
                       "di che ra" % (BOI_BUOC_TOI_THIEU, bd,
                                      bd * BOI_BUOC_TOI_THIEU))}


def chan_troi_giu_bar(ma: str) -> dict:
    """So bar toi thieu phai giu lenh de co che hoi quy kip chay."""
    hs = ho_so(ma)
    if not hs:
        return {"giu_bar": None, "trang_thai": "CHUA_DO_DUOC",
                "vi_sao": "khong co ho so cho ma nay"}
    try:
        nd = float(hs.get("nua_doi_bar"))
    except (TypeError, ValueError):
        nd = float("inf")
    if math.isnan(nd) or math.isinf(nd) or nd <= 0:
        return {"giu_bar": None, "trang_thai": "CHUA_DO_DUOC",
                "nua_doi_bar": None,
                "vi_sao": ("nua doi vo cuc - chuoi khong the hien hoi quy do "
                           "duoc, nen khong suy ra duoc chan troi giu lenh")}
    return {"giu_bar": nd * BOI_CHAN_TROI, "trang_thai": "DAT",
            "nua_doi_bar": nd, "khung_do": "D1",
            "vi_sao": ("nua doi %.0f bar D1; giu ngan hon %.0f bar la cat truoc "
                       "khi co che kip chay" % (nd, nd * BOI_CHAN_TROI))}


def don_thuoc(ma: str) -> dict:
    """Ca ba cau tra loi cho mot ma - goi truoc khi dat bat ky luoi nao."""
    return {"ma": ma, "chieu": chieu_luoi(ma),
            "buoc": buoc_toi_thieu_pct(ma), "chan_troi": chan_troi_giu_bar(ma)}


def in_don_thuoc(ma: str) -> None:
    d = don_thuoc(ma)
    print("== %s ==" % ma)
    for ten, k, khoa_gt in (("CHIEU", "chieu", "chieu"),
                            ("BUOC %", "buoc", "buoc_pct"),
                            ("GIU bar", "chan_troi", "giu_bar")):
        r = d[k]
        gt = r.get(khoa_gt)
        gt = ("%.3f" % gt) if isinstance(gt, float) else (gt or "-")
        print("  %-9s %-9s [%-13s] %s"
              % (ten, gt, r["trang_thai"], r.get("vi_sao", "")[:88]))
