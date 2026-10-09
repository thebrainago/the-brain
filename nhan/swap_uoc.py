# -*- coding: utf-8 -*-
"""swap_uoc.py - UOC phi qua dem (swap) cho mot bang lenh cua MT5 tester (09/10/2026).

VI SAO CO. Tren 286 hang hieu chuan va 3 bao cao tester that, cot Swap cua tester LUON bang 0 (khong phai it: tuyet doi 0), trong khi
tai khoan that tra / nhan swap moi dem. Hai he qua do duoc: (1) engine `luoi.py` (co tru swap) lech tester ~3 diem %/nam o rieng khoan
nay; (2) mot con so tester "DAT" cao hon so tien that vai diem %/nam - 22 / 61 o tester-duong thanh <= 0 sau swap. Phan quyet DAT / AM
cua `ea_tho` vi vay doc tren thuoc do "TRUOC swap": cong lai-sau-phi bo sot dung khoan phi ma luoi / DCA tra nhieu nhat (giu lenh lau).

CACH UOC (khong can tester chay lai; chi can bang lenh cua chinh tester + ty le/nam cua ma):

    swap_lenh = - ty_le(chieu) x so_dem x lot x K x gia / 365          (am = ton tien, cung dau voi cot Swap cua MT5)

  ty_le  %/nam tren notional THEO CHIEU, duong = TRA (cung dau `luoi.QuyCach.phi_nam_mua/ban`). AUDCAD / TONG_HOP: hang so `luoi.QC_AUDCAD`
         (XM); ma khac: `chi_phi.phi_cua` (do tren san that, uu tien XM) - KHONG co thi KHONG uoc (khong doan).
  so_dem so lan NUA DEM (00:00 gio may chu) ma vi the di qua; thu Tu tinh 3 (FX, `SYMBOL_SWAP_ROLLOVER3DAYS`); thu Bay / Chu nhat 0, nen
         7 ngay lich = 7 dem. Ma khong phai FX: tinh LIEN TUC theo ngay lich (chua biet ngay x3 cua tung san), ghi ro trong `che_do`.
  K      tien tai khoan tren MOT don vi gia tren MOT lot, uoc tu chinh P&L tester: tong(loi) / tong(chieu x lot x (gia_dong - gia_mo)).
         Gom luon hop dong va ty gia bao gia -> tai khoan (AUDCAD tren tai khoan USD: ~ 100000 x 0,73), nen khong can bang ty gia.

TACH HAI NUA de luu duoc va tinh lai duoc: `phoi_bay` (KHONG phu thuoc ty le: A_mua / A_ban = tong lot x K x gia x so_dem / 365, don vi
"tien tai khoan nam") roi `ap_ty_le` (swap = -(mua x A_mua + ban x A_ban)). Bang lenh tester nam o may nha (khong vao git), con A_mua /
A_ban thi nho: luu vao ket qua thi cloud doi ty le (XM khac san do) ma khong can bang lenh.

QUY TAC KHONG TINH HAI LAN: tester CO ghi swap khac 0 -> dung so DO, khong cong them uoc. Uoc khong lam duoc (thieu ty le, khong uoc duoc K,
khong doc duoc bang lenh) -> `nguon = "khong_uoc_duoc"` + ly do; noi goi quyet: o doan niem_phong thi KHONG cho DAT.
CHUA gom: swap lam sau them maxDD (tester khong co duong von sau swap) - canh bao, khong sua so.

CLI (may nha):
  python -m nhan.swap_uoc BANG_LENH.csv.gz --ma AUDCAD [--k K] [--mua x --ban y]
  python -m nhan.swap_uoc --quet reports/hieu_chuan [--ra tep.json]   gom A_mua / A_ban cua moi hang hieu chuan da luu (cho cloud doc);
                                                                      --ra: tep tong + cac phan `<ten>_pNN.json` (<= 36.000 ky tu / tep: bo chay chi mang theo 40.000)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
CHE_DO_ROLLOVER = "rollover"
CHE_DO_LIEN_TUC = "lien_tuc"
THU_TU = 2                          # thu Tu (thu Hai = 0): dem x3 cua FX
NGAY_NAM = 365.0
K_LENH_TOI_THIEU = 20               # it hon: khong uoc duoc K
K_SAI_SO_LAM_TRON = 0.005           # tien tai khoan lam tron 0,01 / deal -> sai so moi deal <= 0,005
_NS_NGAY = 86_400_000_000_000
_TIEN_NHO = 1e-12
# Bo chay may nha chi MANG THEO cho cloud toi da 40.000 ky tu / tep va 300.000 / don (`cau_git.tep_moi`): tep qua lon bi cat giua chung (JSON hong).
# Nen ket qua quet duoc CHIA PHAN, moi phan <= PHAN_TOI_DA ky tu, tong hang <= TONG_TOI_DA (con thua thi dem va noi ro, khong im lang).
PHAN_TOI_DA = 36_000
TONG_TOI_DA = 270_000
COT_GOM = ("ma", "khung", "tu", "den", "von", "k_tien", "A_mua", "A_ban", "so_lenh", "swap_tester_do",
           "lai_tester", "lai_engine", "swap_engine", "ty_mua", "ty_ban")


# ============================================================ 1. DEM SO DEM
def _ns(t) -> np.ndarray:
    """Thoi gian -> int64 nano giay (bo mui gio: tester va lab dung gio may chu). NaT -> so nguyen nho nhat: noi goi phai tu loai NaT."""
    idx = pd.DatetimeIndex(pd.to_datetime(t))
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    return idx.values.astype("datetime64[ns]").astype(np.int64)


def trong_so_dem(thu_cua_ngay: int, triple: int | None = THU_TU) -> float:
    """Trong so cua nua dem CUOI mot ngay co thu `thu_cua_ngay` (thu Hai = 0): Tu = 3 (hoac `triple`), thu Bay / Chu nhat = 0, con lai 1."""
    if thu_cua_ngay >= 5:
        return 0.0
    if triple is not None and thu_cua_ngay == triple:
        return 3.0
    return 1.0


def so_dem(mo, dong, triple: int | None = THU_TU, che_do: str = CHE_DO_ROLLOVER) -> np.ndarray:
    """So dem tinh swap (da nhan trong so) cua tung vi the mo luc `mo`, dong luc `dong` (cung do dai, khong NaT).

    rollover : dem cac nua dem 00:00 NAM TRONG (mo, dong) - mo dung luc nua dem thi chua qua no, dong dung luc nua dem thi chua giu qua no.
    lien_tuc : (dong - mo) tinh bang ngay (giong `luoi.chuan_bi.dem`): dung cho ma chua biet ngay dem x3.
    dong <= mo -> 0."""
    a, b = _ns(mo), _ns(dong)
    if a.shape != b.shape:
        raise ValueError("so_dem: mo va dong phai cung do dai (%s vs %s)" % (a.shape, b.shape))
    if che_do == CHE_DO_LIEN_TUC:
        return np.clip((b - a) / float(_NS_NGAY), 0.0, None)
    if che_do != CHE_DO_ROLLOVER:
        raise ValueError("so_dem: che_do phai la %r hoac %r, nhan %r" % (CHE_DO_ROLLOVER, CHE_DO_LIEN_TUC, che_do))
    if a.size == 0:
        return np.zeros(0)
    d0, d1 = a // _NS_NGAY, b // _NS_NGAY
    cuoi = np.maximum(np.where(b % _NS_NGAY > 0, d1, d1 - 1), d0)       # nua dem dau ngay d1 chi tinh khi dong SAU 00:00:00 cua ngay do
    lo, hi = int(d0.min()), int(cuoi.max())
    ngay = np.arange(lo, hi + 1, dtype=np.int64)
    thu = (ngay - 1 + 3) % 7                                            # thu cua ngay TRUOC nua dem j (1970-01-01 la thu Nam = 3)
    w = np.where(thu >= 5, 0.0, 1.0)
    if triple is not None:
        w = np.where(thu == triple, 3.0, w)
    cum = np.cumsum(w)
    return cum[cuoi - lo] - cum[d0 - lo]


def cach_dem_cho(ma: str) -> tuple[str, int | None]:
    """(che_do, triple) theo LOP ma: FX (cap tien 6 chu) = rollover + thu Tu x3; con lai = lien tuc (chua biet ngay x3 cua san)."""
    try:
        from nhan import luoi as LU
        lop = LU.lop_quy_cach(ma)
    except Exception:                                      # noqa: BLE001 - khong phan lop duoc -> cach an toan
        lop = "khong_ho_tro"
    if lop in ("audcad", "tong_hop", "fx_chuan", "fx_jpy"):
        return CHE_DO_ROLLOVER, THU_TU
    return CHE_DO_LIEN_TUC, None


# ============================================================ 2. TY LE THEO MA
def ty_le_cho(ma: str) -> dict | None:
    """{'mua', 'ban', 'nguon', 'tin_cay'} (ty le/nam tren notional, duong = TRA) hoac None khi chua do duoc ma nay. KHONG doan."""
    try:
        from nhan import luoi as LU
        lop = LU.lop_quy_cach(ma)
        if lop in ("audcad", "tong_hop"):
            q = LU.QC_AUDCAD
            return {"mua": float(q.phi_nam_mua), "ban": float(q.phi_nam_ban), "nguon": "luoi.QC_AUDCAD (XM)", "tin_cay": "SAN"}
        from nhan import chi_phi as CP
        r = CP.phi_cua(ma)
    except Exception:                                      # noqa: BLE001 - thieu thu vien chi phi: khong co ty le, khong phai loi
        return None
    if not r or r.get("phi_nam_mua") is None or r.get("phi_nam_ban") is None:
        return None
    mua, ban = float(r["phi_nam_mua"]), float(r["phi_nam_ban"])
    if not (math.isfinite(mua) and math.isfinite(ban)):
        return None
    return {"mua": mua, "ban": ban, "nguon": "%s %s" % (r.get("san_lay", "?"), r.get("symbol_lay", ma)),
            "tin_cay": str(r.get("tin_cay") or "?")}


# ============================================================ 3. K = TIEN TAI KHOAN / (DON VI GIA x LOT)
def uoc_k_tien(b: pd.DataFrame, cot_loi: str | None = None) -> dict | None:
    """K uoc tu P&L cua chinh bang lenh (cot `chieu`, `lot`, `gia_mo`, `gia_dong`, `dong` + cot loi: `loi` uu tien, khong co thi `lai`).

    'tong' : tong(loi) / tong(chieu x lot x (gia_dong - gia_mo)). Moi vi the dong co mat o ca hai ve nen tong KHONG doi khi ghep nham lenh
             vao / ra (cap cheo tien: hop dong hieu dung troi theo ty gia). Can >= 20 lenh dong, tong loi >= 50 x sai so lam tron, cung dau.
    'tung_lenh' : trung vi loi / (chieu x lot x dgia) tren cac lenh |loi| >= 1,0 (khi tong qua nho) - can >= 20 lenh.
    Tra {k, so_mau, cach} hoac None (dung doan: khong uoc duoc thi noi goi bao khong uoc duoc)."""
    if b is None or len(b) == 0:
        return None
    cot = cot_loi or ("loi" if "loi" in b.columns else "lai")
    if cot not in b.columns or "gia_dong" not in b.columns:
        return None
    d = b[b["dong"].notna() & b["gia_dong"].notna() & b[cot].notna()]
    n = int(len(d))
    if n < K_LENH_TOI_THIEU:
        return None
    q = d["chieu"].astype(float) * (d["gia_dong"].astype(float) - d["gia_mo"].astype(float)) * d["lot"].astype(float)
    loi = d[cot].astype(float)
    q_tong, l_tong = float(q.sum()), float(loi.sum())
    if abs(l_tong) >= 50.0 * K_SAI_SO_LAM_TRON * math.sqrt(n) and q_tong * l_tong > 0 and abs(q_tong) > _TIEN_NHO:
        return {"k": l_tong / q_tong, "so_mau": n, "cach": "tong"}
    ok = (loi.abs() >= 1.0) & (q * loi > 0) & (q.abs() > _TIEN_NHO)
    if int(ok.sum()) >= K_LENH_TOI_THIEU:
        return {"k": float(np.median((loi[ok] / q[ok]).to_numpy(float))), "so_mau": int(ok.sum()), "cach": "tung_lenh"}
    return None


# ============================================================ 4. PHOI BAY (khong phu thuoc ty le) -> SWAP
def phoi_bay(b: pd.DataFrame, k_tien: float, het=None, ma: str | None = None, triple: int | None = THU_TU,
             che_do: str | None = None) -> dict:
    """'Tien-nam' ma bang lenh chiu phi qua dem, TACH THEO CHIEU: A = tong(lot x K x gia x so_dem / 365) (don vi: tien tai khoan x nam).

    swap = -(ty_le_mua x A_mua + ty_le_ban x A_ban). `b`: cot mo, dong (NaT = con mo luc het), chieu (+1 mua / -1 ban), lot, gia_mo, gia_dong.
    `het`: gio het cua so (lenh con mo dong tai day); khong cho thi lay gio dong muon nhat. `ma` chon cach dem theo lop ma neu khong cho
    `che_do` / `triple`. Gia tinh notional = trung binh gia mo va gia dong (lenh con mo: gia mo)."""
    if che_do is None:
        che_do, triple = cach_dem_cho(ma or "")
    k = float(k_tien)
    if not (math.isfinite(k) and k > 0):
        raise ValueError("phoi_bay: k_tien phai la so duong huu han, nhan %r" % (k_tien,))
    ra = {"che_do": che_do, "triple": triple, "k_tien": k, "so_lenh": int(len(b)), "so_lenh_tu_1_dem": 0, "A_mua": 0.0, "A_ban": 0.0,
          "dem_lot_mua": 0.0, "dem_lot_ban": 0.0}
    if len(b) == 0:
        return ra
    b = b[pd.to_datetime(b["mo"]).notna()]
    ra["so_lenh"] = int(len(b))
    if len(b) == 0:
        return ra
    mo = pd.to_datetime(b["mo"])
    dong = pd.to_datetime(b["dong"])
    if het is not None:
        cuoi = pd.Timestamp(het)
    else:
        cuoi = dong.max() if dong.notna().any() else mo.max()
    dong = dong.fillna(cuoi)
    n_dem = so_dem(mo, dong, triple, che_do)
    gm = b["gia_mo"].astype(float).to_numpy()
    gd = b["gia_dong"].astype(float).to_numpy() if "gia_dong" in b.columns else np.full(len(b), np.nan)
    gia = np.where(np.isfinite(gd), (gm + np.where(np.isfinite(gd), gd, gm)) / 2.0, gm)
    lot = b["lot"].astype(float).to_numpy()
    mua = b["chieu"].astype(float).to_numpy() > 0
    tien = n_dem * lot * k * gia / NGAY_NAM
    ra.update(so_lenh_tu_1_dem=int((n_dem >= 1.0).sum()), A_mua=float(tien[mua].sum()), A_ban=float(tien[~mua].sum()),
              dem_lot_mua=float((n_dem * lot)[mua].sum()), dem_lot_ban=float((n_dem * lot)[~mua].sum()))
    return ra


def ap_ty_le(phoi: dict | None, ty_le: dict | None, swap_do: float | None = None) -> dict:
    """Ket luan cuoi cung cho MOT bang lenh: {'nguon': 'do' | 'uoc' | 'khong_uoc_duoc', 'swap': tien (am = ton) | None, ...}.

    `swap_do` = tong swap tester GHI (None = khong ghi). Khac 0 -> 'do' (khong cong uoc them: tranh tinh hai lan).
    Khong co phoi bay / ty le -> 'khong_uoc_duoc' kem `ly`."""
    if swap_do is not None and math.isfinite(float(swap_do)) and abs(float(swap_do)) > 0.0:
        return {"nguon": "do", "swap": float(swap_do), "ly": "tester co ghi swap khac 0: dung so do, khong cong uoc them"}
    if not phoi:
        return {"nguon": "khong_uoc_duoc", "swap": None, "ly": "khong co phoi bay (khong uoc duoc K tu P&L tester hoac khong doc duoc bang lenh)"}
    if not ty_le:
        return {"nguon": "khong_uoc_duoc", "swap": None, "ly": "khong co ty le swap/nam do duoc cho ma nay (khong doan)", "phoi_bay": phoi}
    mua, ban = float(ty_le["mua"]), float(ty_le["ban"])
    swap = -(mua * float(phoi["A_mua"]) + ban * float(phoi["A_ban"]))
    return {"nguon": "uoc", "swap": swap, "ty_le": {"mua": mua, "ban": ban, "nguon": ty_le.get("nguon"), "tin_cay": ty_le.get("tin_cay")},
            "phoi_bay": phoi, "ly": "tester khong ghi swap (cot Swap = 0): uoc tu bang lenh"}


def uoc_cho_bang(b: pd.DataFrame, ma: str, k_tien: float | None = None, ty_le: dict | None = None, het=None,
                 cot_loi: str | None = None, bang_k: pd.DataFrame | None = None) -> dict:
    """Mot buoc: bang lenh tester -> ket luan swap. `swap_do` lay tu cot `swap` cua chinh bang (tong, NaN = 0); co deal swap khac 0 -> 'do'.

    `bang_k`: bang rieng de uoc K (vd bang gop theo lenh co cot `loi` THUAN, chua tru hoa hong); mac dinh dung chinh `b`."""
    sw = b["swap"].astype(float).fillna(0.0) if (b is not None and len(b) and "swap" in b.columns) else None
    swap_do = float(sw.sum()) if sw is not None else None
    if sw is not None and bool((sw.abs() > 0).any()):
        return ap_ty_le(None, None, swap_do)
    k_nguon, kinfo = "cho", None
    if k_tien is None:
        kinfo = uoc_k_tien(bang_k if bang_k is not None else b, cot_loi)
        if kinfo is None:
            return {"nguon": "khong_uoc_duoc", "swap": None,
                    "ly": "khong uoc duoc K (tien tai khoan / don vi gia / lot) tu P&L tester: can >= %d lenh dong va tong loi du lon" % K_LENH_TOI_THIEU}
        k_tien, k_nguon = kinfo["k"], kinfo["cach"]
    phoi = phoi_bay(b, k_tien, het, ma)
    phoi["k_cach"] = k_nguon
    return ap_ty_le(phoi, ty_le if ty_le is not None else ty_le_cho(ma), swap_do)


def doi_k(phoi: dict | None, k_moi: float) -> dict | None:
    """Doi K cua mot phoi bay (A_mua, A_ban ty le thuan voi K; so dem va lot khong doi): dung khi he so quy doi tien duoc dat lai."""
    if not phoi:
        return phoi
    k0, k1 = float(phoi["k_tien"]), float(k_moi)
    if not (math.isfinite(k0) and k0 > 0 and math.isfinite(k1) and k1 > 0):
        raise ValueError("doi_k: K cu va K moi phai la so duong huu han, nhan %r -> %r" % (k0, k1))
    h = k1 / k0
    return {**phoi, "k_tien": k1, "A_mua": float(phoi["A_mua"]) * h, "A_ban": float(phoi["A_ban"]) * h}


def doi_ty_le(kq: dict, mua: float, ban: float) -> float | None:
    """Swap neu doi ty le (vd XM khac san do): dung lai `phoi_bay` da luu trong ket qua `uoc`. None khi khong co phoi bay."""
    p = (kq or {}).get("phoi_bay")
    if not p:
        return None
    return -(float(mua) * float(p["A_mua"]) + float(ban) * float(p["A_ban"]))


def uoc_tu_bao_cao(duong, ma: str, het=None, ty_le: dict | None = None) -> dict | None:
    """Bao cao tester (.htm / CSV deal) -> ket luan swap (xem `uoc_cho_bang`), kem `bang_doc_duoc`.

    None  = khong co tep de doc (`duong` rong / khong phai tep / da la dict): noi goi giu cach cu, KHONG co gi de thu.
    `bang_doc_duoc=False` = tep co nhung khong doc ra bang Deals co lenh (bao cao tong hop): khong uoc duoc, KHONG phai loi uoc.
    `bang_doc_duoc=True`  = da co bang lenh; `nguon='khong_uoc_duoc'` luc nay la that bai THAT (thieu ty le / khong uoc duoc K)."""
    if not duong or isinstance(duong, dict):
        return None
    p = Path(str(duong))
    if not p.is_file():
        return None
    try:
        from nhan import lenh_tester as LT
        g = LT.gop_theo_lenh(LT.vi_the_tu_tep(p))
    except Exception as e:                                 # noqa: BLE001 - bao cao tong hop / dinh dang la: khong co bang de uoc
        return {"nguon": "khong_uoc_duoc", "swap": None, "bang_doc_duoc": False,
                "ly": "khong doc ra bang Deals cua bao cao (%s: %s)" % (type(e).__name__, str(e)[:100])}
    if g is None or len(g) == 0:
        return {"nguon": "khong_uoc_duoc", "swap": None, "bang_doc_duoc": False, "ly": "bang Deals cua bao cao khong co lenh nao"}
    kq = uoc_cho_bang(g, ma, het=het, ty_le=ty_le)
    kq["bang_doc_duoc"] = True
    return kq


# ============================================================ 5. CLI
def _doc_bang(duong: Path) -> pd.DataFrame:
    b = pd.read_csv(duong)
    for c in ("mo", "dong"):
        if c in b.columns:
            b[c] = pd.to_datetime(b[c])
    return b


def quet_hieu_chuan(thu_muc: Path, ra: Path | None = None) -> dict:
    """Gom A_mua / A_ban cua moi hang hieu chuan da luu (`<khoa>.json` + `*_lenh.csv.gz`): ban nho (~vai KB) de dua cho cloud."""
    out: dict = {"thu_muc": str(thu_muc), "cac_hang": {}, "bo_qua": {}}
    for p in sorted(Path(thu_muc).glob("*.json")):
        if p.name.startswith("swap_"):
            continue
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            out["bo_qua"][p.name] = "khong doc duoc: %s" % str(e)[:80]
            continue
        t = r.get("tester") if isinstance(r, dict) else None
        if not isinstance(t, dict) or not t.get("bang_lenh") or not r.get("engine"):
            out["bo_qua"][p.name] = "khong phai ket qua hieu chuan day du"
            continue
        bl = Path(t["bang_lenh"])
        bl = bl if bl.is_absolute() else LAB / bl
        if not bl.exists():
            out["bo_qua"][p.name] = "mat bang lenh %s" % bl.name
            continue
        try:
            b = _doc_bang(bl)
            hs = (r.get("he_so_quy_doi") or {}).get("dung")
            hop = ((r.get("engine") or {}).get("qc") or {}).get("hop_dong")
            k = float(hop) / float(hs) if hs and hop else None
            ma = str(r.get("ma") or "")
            cs = r.get("cua_so") or {}
            het = pd.Timestamp(str(cs.get("den", "")).replace(".", "-")) + pd.Timedelta(days=1) if cs.get("den") else None
            kinfo = None if k else uoc_k_tien(b)
            k_dung = k or (kinfo or {}).get("k")
            if not k_dung:
                out["bo_qua"][p.name] = "khong uoc duoc K"
                continue
            ph = phoi_bay(b, k_dung, het, ma)
            sw_do = float(b["swap"].astype(float).fillna(0.0).sum()) if "swap" in b.columns else None
            out["cac_hang"][p.stem] = {"ma": ma, "khung": r.get("khung"), "cua_so": [cs.get("tu"), cs.get("den"), cs.get("ngay")],
                                       "von": r.get("von"), "phoi_bay": {k2: (round(v, 6) if isinstance(v, float) else v) for k2, v in ph.items()},
                                       "swap_tester_do": sw_do, "lai_tester_pct_nam": (r.get("tester") or {}).get("lai_nam_pct"),
                                       "lai_engine_pct_nam": (r.get("engine") or {}).get("lai_nam_pct"),
                                       "swap_engine": ((r.get("engine") or {}).get("thong_ke") or {}).get("swap"),
                                       "ty_le_engine": [((r.get("engine") or {}).get("qc") or {}).get(x) for x in ("phi_nam_mua", "phi_nam_ban")]}
        except (OSError, ValueError, KeyError, TypeError) as e:
            out["bo_qua"][p.name] = "loi: %s" % str(e)[:100]
    out["so_hang"], out["so_bo_qua"] = len(out["cac_hang"]), len(out["bo_qua"])
    if ra is not None:
        out["tep_ra"] = ghi_gom(out, Path(ra))
    return out


def _dai(x) -> int:
    return len(json.dumps(x, ensure_ascii=False, separators=(",", ":")))


def _hang_gon(h: dict) -> list:
    """Mot hang quet -> danh sach gon theo `COT_GOM` (khong lap ten khoa): ~170 ky tu / hang thay vi ~400."""
    ph, cs, ty = h.get("phoi_bay") or {}, h.get("cua_so") or [None, None, None], h.get("ty_le_engine") or [None, None]
    return [h.get("ma"), h.get("khung"), cs[0], cs[1], h.get("von"), ph.get("k_tien"), ph.get("A_mua"), ph.get("A_ban"), ph.get("so_lenh"),
            h.get("swap_tester_do"), h.get("lai_tester_pct_nam"), h.get("lai_engine_pct_nam"), h.get("swap_engine"), ty[0], ty[1]]


def ghi_gom(out: dict, ra: Path) -> list[str]:
    """Ghi ket qua `quet_hieu_chuan` thanh tep tong `ra` (so hang, ly do bo qua theo nhom, danh sach phan) va cac phan `<ra>_pNN.json`
    (`{"cot": COT_GOM, "hang": {khoa: [gia tri theo cot]}}`), moi phan <= PHAN_TOI_DA ky tu. Tong hang vuot TONG_TOI_DA thi cac hang cuoi
    KHONG ghi, nhung `so_hang_khong_vua` noi ro (doi `--quet` ra thu muc nho hon / chay lai). Tra danh sach ten tep da ghi (tep tong truoc)."""
    ra = Path(ra)
    ra.parent.mkdir(parents=True, exist_ok=True)
    khung_rong = _dai({"cot": list(COT_GOM), "hang": {}})
    phan: list[dict] = []
    hien: dict = {}
    dai_hien = khung_rong
    tong = 0
    khong_vua = 0
    for khoa, h in out["cac_hang"].items():
        gon = _hang_gon(h)
        n = _dai([khoa, gon]) + 2                      # "khoa":[...], + dau phay
        if khung_rong + n > PHAN_TOI_DA or tong + n > TONG_TOI_DA:
            khong_vua += 1
            continue
        if dai_hien + n > PHAN_TOI_DA:
            phan.append(hien)
            hien, dai_hien = {}, khung_rong
        hien[khoa] = gon
        dai_hien += n
        tong += n
    if hien:
        phan.append(hien)
    ten_phan = []
    for i, hang in enumerate(phan, 1):
        t = ra.with_name("%s_p%02d%s" % (ra.stem, i, ra.suffix or ".json"))
        t.write_text(json.dumps({"cot": list(COT_GOM), "hang": hang}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        ten_phan.append(t.name)
    nhom: dict = {}
    for ly in out["bo_qua"].values():
        k = " ".join(str(ly).split()[:3])
        nhom[k] = nhom.get(k, 0) + 1
    man = {"thu_muc": out["thu_muc"], "so_hang": out["so_hang"], "so_bo_qua": out["so_bo_qua"], "bo_qua_theo_ly_do": nhom,
           "bo_qua": dict(list(out["bo_qua"].items())[:40]), "cot": list(COT_GOM), "phan": ten_phan,
           "so_hang_khong_vua": khong_vua, "don_vi": "A_mua / A_ban = tien tai khoan x nam; lai % / nam; swap_* = tien tai khoan",
           "cach_dung": "swap uoc = -(ty_mua * A_mua + ty_ban * A_ban) (ty le %/nam tren notional, duong = tra); sau swap %/nam = lai_tester + swap / von / nam"}
    ra.write_text(json.dumps(man, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return [ra.name] + ten_phan


def giai_gom(man: dict, phan: dict) -> dict:
    """Doc nguoc (ben cloud): `man` = tep tong da `json.loads`, `phan` = {ten tep: noi dung da json.loads hoac chuoi JSON} -> {khoa: {cot: gia tri}}.
    Thieu mot phan duoc liet ke trong `man["phan"]` -> ValueError (khong im lang tra ban thieu)."""
    cot = list(man.get("cot") or COT_GOM)
    ra: dict = {}
    for ten in man.get("phan") or []:
        if ten not in phan:
            raise ValueError("thieu phan %s (tep tong liet ke %d phan)" % (ten, len(man.get("phan") or [])))
        d = phan[ten]
        d = json.loads(d) if isinstance(d, (str, bytes)) else d
        for khoa, v in (d.get("hang") or {}).items():
            ra[khoa] = dict(zip(cot, v))
    return ra


def main_cli(a: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if a is None else a)
    if not a:
        print(__doc__)
        return 2

    def lay(ten: str, mac_dinh=None):
        return a[a.index(ten) + 1] if ten in a and a.index(ten) + 1 < len(a) else mac_dinh
    if "--quet" in a:
        r = quet_hieu_chuan(Path(lay("--quet")), Path(lay("--ra")) if lay("--ra") else None)
        print("swap_uoc quet: %d hang, bo qua %d, tep ra %s" % (r["so_hang"], r["so_bo_qua"], ", ".join(r.get("tep_ra") or ["(khong ghi)"])))
        return 0 if r["so_hang"] else 1
    duong = Path(a[0])
    ma = str(lay("--ma", ""))
    b = _doc_bang(duong)
    ty = {"mua": float(lay("--mua")), "ban": float(lay("--ban")), "nguon": "dong lenh"} if lay("--mua") and lay("--ban") else None
    kq = uoc_cho_bang(b, ma, float(lay("--k")) if lay("--k") else None, ty)
    print(json.dumps(kq, ensure_ascii=False, indent=1, default=str))
    return 0 if kq["nguon"] != "khong_uoc_duoc" else 1


if __name__ == "__main__":
    sys.exit(main_cli())
