# -*- coding: utf-8 -*-
"""ngoai_sinh.py - LUONG NGOAI SINH. Ke thua tu ben ngoai, roi CHINH cho tai san moi.

Chu du an dinh nghia 03/09/2026:

  *"Noi sinh la y tuong, phuong phap ro nguoc cua quantlab nghi ra. Con NGOAI
  SINH la toan bo he thong giao dich ma seeker dao ve + cac he thong giao dich
  DA PASS se duoc tinh chinh lai cho he thong va tai san moi."*

Vay ngoai sinh co HAI nguon, khong phai mot:
  A. kho co che SEEKER dao ve (`ngu_phap.doc_kho`)
  B. **cac gia thuyet DA PASS / dang cach ly trong so cai** — chuyen sang tai
     san moi. Day la phan truoc nay khong ton tai: mot he PASS tren AUDCAD.H4
     nam yen trong so, khong ai mang no sang thu tren US500CASH.

CHUYEN THAM SO SANG TAI SAN MOI: GIU TY LE KICH HOAT, KHONG GIU CON SO.

`quy_doi_tham_so.quy_doi` chi doi duoc tham so CO THU NGUYEN GIA (SL 50 diem
tren vang khac 50 diem tren EURUSD). Nhung tham so cua mot template thuong la
nguong dao dong va cua so nhin lai: `rsi_dao_chieu(n=14, vao=30, ra_=55)`.
`30` khong co thu nguyen gia nen khong nhan ty le ATR duoc.

Cai KHONG doi khi sang tai san khac la **do HIEM cua su kien**. Tren AUDCAD.H4
thi `RSI(14) < 30` co the la 4,2% so bar; tren US500CASH.H4 cung nguong 30 do
co the chi la 1,1% - qua hiem de co thong ke - hoac 9% - qua thuong de con la
mot dieu kien. Nen phep chuyen dung la:

    do ty le kich hoat tren tai san GOC  ->  tim cau hinh tren tai san DICH
    cho ty le kich hoat gan nhat

Cach nay khong can biet tham so nao mang y nghia gi, nen no chay duoc cho CA
template viet tay lan khai bao DSL - va do la ly do no duoc chon thay vi mot
bang anh xa theo tung template.

BA CHOT CHAN:
  1. **Do ty le kich hoat tren TRAIN cua ca hai ben.** Do tren ca chuoi la
     nhin truoc.
  2. **Chuyen KHONG phai la mot PASS moi.** He chuyen sang la mot GIA THUYET
     MOI tren tai san moi, phai di lai tu dau qua `cong`. Mot PASS tren AUDCAD
     khong mua duoc suat nao tren US500CASH.
  3. **Khong dang ky, khong cham FDR o day.** File nay chi de xuat ung vien.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhan import du_lieu as DU
from nhan import mau as MAU
from nhan import ngu_phap as NP
from nhan import so as SO

#: Trang thai duoc coi la "da qua duoc cai gi do" va dang de ke thua.
TRANG_THAI_KE_THUA = ("PASS", "QUARANTINED_V2")


def he_da_pass(trang_thai=TRANG_THAI_KE_THUA) -> list[dict]:
    """Cac gia thuyet trong so cai dang o trang thai dang ke thua."""
    dau = ",".join("?" for _ in trang_thai)
    rows = SO.nhieu(
        f"SELECT ma, template, tham_so, tai_san, khung, ho, trang_thai, ghi_chu "
        f"FROM gia_thuyet WHERE trang_thai IN ({dau}) ORDER BY trang_thai", *trang_thai)
    ra = []
    for r in rows or []:
        d = dict(r)
        try:
            d["tham_so"] = __import__("json").loads(d.get("tham_so") or "{}")
        except Exception:
            d["tham_so"] = {}
        ra.append(d)
    return ra


#: Ly do cuoi cung khien `ty_le_kich_hoat` tra `None`. Doc ngay sau loi goi.
#: Khong phai trang thai toan cuc "dung": chi de `chuyen`/`ung_vien` phan biet
#: duoc HAI nguyen nhan rat khac nhau ma khong doi chu ky ham cong khai.
_LY_DO_CUOI: str | None = None


def ty_le_kich_hoat(ma: str, khung: str, template: str, tham_so: dict,
                    chi_train: bool = True) -> float | None:
    """Ty le bar co phoi nhiem khac 0. None = khong chay duoc tren tai san nay.

    ## HAI NGUYEN NHAN KHAC HAN NHAU (tach 20/09/2026)

    Ban cu co hai `except Exception: return None` gop lai lam mot dau ra:

      * **THIEU DU LIEU** (`DU.nap` nem) - may nay khong co `data/<ma>`. Day la
        `CHUA_DO_DUOC`: khong noi duoc gi ve co che ca.
      * **CO CHE KHONG CHAY DUOC** (`MAU.sinh` nem) - vd co che theo GIO tren
        khung khong co gio. Day la ket luan THAT ve cap (co che, tai san).

    Vi sao phai tach: `ung_vien()` bo im lang moi ung vien tra `None`. Tren
    mot may thieu `data/`, MOI he da PASS deu roi vao nhanh thu nhat va bao
    cao in ra `tu_he_da_pass: 0` - doc y het "khong he nao ke thua duoc",
    dung hinh dang bay `CHUA_DO_DUOC` bi doc thanh `AM` cua LUAT SO 0.
    """
    global _LY_DO_CUOI
    _LY_DO_CUOI = None
    try:
        df = DU.nap(ma, khung)
    except Exception as e:
        _LY_DO_CUOI = f"CHUA_DO_DUOC: khong nap duoc {ma} {khung} ({type(e).__name__}: {e})"
        return None
    if chi_train:
        df = DU.hai_nua(df, 0.6)[0]
    try:
        th = MAU.sinh(template, df, tham_so)
    except Exception as e:
        _LY_DO_CUOI = f"co che '{template}' khong chay duoc tren {ma} {khung} ({type(e).__name__})"
        return None
    return float(np.mean(np.abs(np.nan_to_num(np.asarray(th, float))) > 0))


def _lan_can(tham_so: dict, rong: float = 0.6, buoc: int = 3) -> list[dict]:
    """Luoi quanh `tham_so`, rong hon `do_on_dinh.lan_can` vi day la CHUYEN
    sang tai san khac chu khong phai do do on dinh quanh mot tam."""
    ten = sorted(k for k, v in tham_so.items()
                 if isinstance(v, (int, float)) and not isinstance(v, bool))
    if not ten:
        return [dict(tham_so)]
    truc = []
    for k in ten:
        v = tham_so[k]
        if isinstance(v, int):
            b = max(1, int(round(abs(v) * rong / buoc)))
            truc.append(sorted({v + i * b for i in range(-buoc, buoc + 1)
                                if v + i * b > 0}))
        else:
            b = abs(v) * rong / buoc
            truc.append(sorted({round(v + i * b, 6) for i in range(-buoc, buoc + 1)}))
    ra, tong = [], 1
    for t in truc:
        tong *= len(t)
    if tong > 400:                      # giu chi phi hop ly
        truc = [t[::2] if len(t) > 3 else t for t in truc]
    import itertools
    for bo in itertools.product(*truc):
        ra.append({**tham_so, **dict(zip(ten, bo))})
    return ra


def chuyen(gt: dict, ma_dich: str, khung_dich: str,
           dung_sai: float = 0.25) -> dict | None:
    """Chuyen mot he da PASS sang tai san moi, GIU ty le kich hoat.

    Tra None khi template khong chay duoc tren tai san dich (vd co che theo
    phien tren khung khong co gio) hoac khong do duoc ty le goc.
    """
    tpl, ts = gt.get("template"), gt.get("tham_so") or {}
    if not tpl or tpl not in MAU.MAU:
        return None
    goc = ty_le_kich_hoat(gt["tai_san"], gt["khung"], tpl, ts)
    if goc is None:
        # Ghi ly do vao chinh ket qua thay vi tra `None` tron: goi y thu hai
        # cua LUAT SO 0 la khong bao gio de mot phep KHONG DO DUOC im lang.
        return {"tu": gt.get("ma"), "template": tpl, "ho": gt.get("ho"),
                "tai_san_goc": gt.get("tai_san"), "khung_goc": gt.get("khung"),
                "tai_san_dich": ma_dich, "khung_dich": khung_dich,
                "dat": False, "chua_do_duoc": True,
                "ly_do": _LY_DO_CUOI or "khong do duoc ty le kich hoat goc"}
    if goc <= 0:
        return None

    thang = ty_le_kich_hoat(ma_dich, khung_dich, tpl, ts)
    tot, tot_ts, tot_ty = None, None, None
    for ung in _lan_can(ts):
        ty = ty_le_kich_hoat(ma_dich, khung_dich, tpl, ung)
        if ty is None or ty <= 0:
            continue
        # so sanh tren thang LOG: 2% so voi 4% lech bang 4% so voi 8%
        lech = abs(np.log(ty / goc))
        if tot is None or lech < tot:
            tot, tot_ts, tot_ty = lech, ung, ty
    if tot_ts is None:
        return None
    return {
        "tu": gt["ma"], "template": tpl, "ho": gt.get("ho"),
        "trang_thai_goc": gt.get("trang_thai"),
        "tai_san_goc": gt["tai_san"], "khung_goc": gt["khung"],
        "tham_so_goc": ts, "ty_le_goc": round(goc, 5),
        "tai_san_dich": ma_dich, "khung_dich": khung_dich,
        "tham_so_moi": tot_ts, "ty_le_moi": round(tot_ty, 5),
        "ty_le_neu_giu_nguyen_so": (round(thang, 5) if thang is not None else None),
        "lech_log": round(float(tot), 4),
        "dat": bool(tot <= np.log(1 + dung_sai)),
    }


def ung_vien(ma_dich: str, khung_dich: str, gom_kho: bool = True) -> dict:
    """Toan bo ung vien NGOAI SINH cho mot tai san: kho SEEKER + he da PASS.

    Tra dict co hai phan de nguoi doc thay ro chung den tu dau - hai nguon nay
    co do tin cay rat khac nhau va khong duoc tron lam mot.
    """
    NP.nap_vao_mau()
    ke_thua, chua_do = [], []
    for gt in he_da_pass():
        r = chuyen(gt, ma_dich, khung_dich)
        if not r:
            continue
        (chua_do if r.get("chua_do_duoc") else ke_thua).append(r)
    kho = []
    if gom_kho:
        kho = [{"ten": c.get("ten"), "ho": c.get("ho"), "nguon": c.get("nguon")}
               for c in NP.doc_kho()]
    return {"tai_san": ma_dich, "khung": khung_dich,
            "tu_kho_seeker": len(kho), "tu_he_da_pass": len(ke_thua),
            # `tu_he_da_pass: 0` chi doc duoc la "khong he nao ke thua duoc"
            # KHI `chua_do_duoc: 0`. Thieu `data/` thi moi he roi vao day.
            "chua_do_duoc": len(chua_do), "khong_do_duoc": chua_do,
            "kho": kho, "ke_thua": ke_thua}
