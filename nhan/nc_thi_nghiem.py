# -*- coding: utf-8 -*-
"""nc_thi_nghiem.py - THI NGHIEM cua nha nghien cuu AI: chay he, quet, mo xe, xac nhan, mo niem phong.

Moi ham o day la MOT phep do ma nha nghien cuu (AI) goi qua `nc_cong_cu`. Ham
khong quyet dinh nghien cuu gi - AI quyet dinh. Ham chi lam dung ba viec:

1. **Do bang dung duong cua du an.** Tin hieu qua `ngu_phap` (khong nhin truoc),
   tien qua `mo_phong.chay` hoac `dap_quan_tri.dap` + `vao_lenh.tinh_tien`
   (phi tren GOP, phi qua dem bat doi xung). Cau hoi tien theo TIEU CHI CHU DU AN
   25/09: *"chi can co lai va maxdd duoi 80% la ok"*, phuong phap nao cung duoc
   (martingale, DCA, luoi...). `tien_duoi_tran` tra CO LAI khong (sau moi phi) va
   muc ra tien TOT NHAT ma maxDD van duoi 80%. Moc max(mua-giu, ban-giu, tien mat)
   o cung tran, tang 2 kinh te, duoi lo: NHAN - tinh va ghi, khong chan.
2. **Giu ky luat du lieu.** Kham pha tren `kham_pha`; `xac_nhan` bi dem so lan
   nhin; `niem_phong` chi mo MOT LAN cho mot khai bao da dong bang, va toi da
   `MO_NIEM_PHONG_TOI_DA` lan cho mot DONG gia thuyet.
3. **Ghi so tay.** Moi phep do thanh mot dong `thi_nghiem` co van tay; cung
   van tay thi tra ket qua cu, khong chay lai va khong tinh them phep thu.

Ba trang thai: DAT / AM / CHUA_DO_DUOC. Khau do hong (it lenh, khai bao sai,
loi engine, chi phi khai bao o niem phong) KHONG BAO GIO la AM.
"""
from __future__ import annotations

import copy
import itertools
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import (cham_diem as CD, dap_quan_tri as DQT, do_luong as DO, mo_phong as MP,
                  nc_dac_trung as DT, nc_du_lieu as NDL, nc_mo_xe as MX,
                  nc_so_tay as ST, ngu_phap as NP, vao_lenh as VL)

LENH_TOI_THIEU = 10               # duoi nay: CHUA_DO_DUOC o moi doan
LENH_TOI_THIEU_NIEM_PHONG = 20
MO_NIEM_PHONG_TOI_DA = 3          # moi dong gia thuyet
NHIN_XAC_NHAN_CANH_BAO = 6        # nhin doan xac nhan qua so lan nay -> canh bao
#: Tieu chi chu du an 25/09: "chi can co lai va maxdd duoi 80% la ok". Tran doc tu MOT
#: nguon (`cham_diem.TRAN_SUT_GIAM`) - cung con so voi `cong.py` dieu kien 15.
DD_TRAN = CD.TRAN_SUT_GIAM / 100.0
#: Tran don bay khi tim muc ra tien tot nhat duoi tran DD (quy uoc `vao_lenh.quy_ve_dd`).
L_TOI_DA = 10.0
O_QUET_TOI_DA = 150

_DEM_MOC: dict = {}


class LoiKhaiBao(ValueError):
    """Khai bao DSL / luat quan tri sai - ket qua la CHUA_DO_DUOC, khong phai AM."""


# ----------------------------------------------------------- CHUAN BI
def chuan_hoa_spec(spec: dict) -> dict:
    """Ban sao spec da kiem cu phap. Nem `LoiKhaiBao` kem ly do cu the."""
    if not isinstance(spec, dict):
        raise LoiKhaiBao("spec phai la mot object DSL")
    s = copy.deepcopy(spec)
    s.setdefault("chieu", 1)
    s.setdefault("giu", 1)
    s.setdefault("ra", [])
    if not s.get("ten"):
        s["ten"] = "nc_" + ST.van_tay(s.get("vao"), s.get("ra"), s.get("chieu"), s.get("giu"))
    s["ten"] = NP.chuan_hoa_ten(s["ten"])
    loi = NP.kiem_khai_bao(s)
    if loi:
        raise LoiKhaiBao("; ".join(loi[:6]))
    return s


def chuan_hoa_quan_tri(qt) -> dict | None:
    if not qt:
        return None
    if not isinstance(qt, dict):
        raise LoiKhaiBao("quan_tri phai la object, vd {\"sl_atr\": 2, \"tp_atr\": 3}")
    xau = [k for k in qt if k not in DQT.NUT]
    if xau:
        raise LoiKhaiBao("nut quan tri khong biet %s (co: %s)" % (xau, ", ".join(DQT.NUT)))
    ra = {}
    for k, v in qt.items():
        try:
            v = float(v)
        except (TypeError, ValueError):
            raise LoiKhaiBao("quan_tri.%s phai la so" % k)
        if not np.isfinite(v) or v <= 0:
            raise LoiKhaiBao("quan_tri.%s phai > 0" % k)
        ra[k] = int(v) if k == "thoat_bar" else v
    return ra


def _bar_moi_ngay(idx: pd.DatetimeIndex) -> float:
    idx = pd.DatetimeIndex(idx)
    so_ngay = max(1, len(np.unique(idx.normalize())))
    return len(idx) / so_ngay


# ------------------------------------------------------------ CHAY HE
def chay_he(ma: str, khung: str, spec: dict, quan_tri: dict | None = None,
            doan: str = "kham_pha", _giay_phep: bool = False) -> dict:
    """Chay MOT he tren MOT doan. -> {df, a, kq, lenh, cp, spec, quan_tri}.

    Tin hieu tinh tren TIEN TO (co lich su cho chi bao), tien chi tinh trong doan.
    Co `quan_tri`: tin hieu VAO la dieu kien `vao` tung bar (vao lai duoc sau khi
    thoat neu dieu kien con dung - dung cach mot EA chay); thoat do luat quan tri,
    tran thoi gian = `giu` cua khai bao (neu khai bao khong co `ra`).
    """
    spec = chuan_hoa_spec(spec)
    qt = chuan_hoa_quan_tri(quan_tri)
    df_full = NDL.nap(ma, khung)
    if doan == "truoc_niem_phong":
        # NOI BO (chi `niem_phong` goi): kham_pha + xac_nhan lien mach, de CHOT don bay tren
        # du lieu da mo truoc khi nhin doan niem phong. Khong co trong `DOAN_MO`.
        pre, _ = NDL.cat_doan(df_full, "xac_nhan")
        a = NDL.chi_so_doan(len(df_full), "kham_pha")[0]
    else:
        pre, a = NDL.cat_doan(df_full, doan, _giay_phep=_giay_phep)
    if len(pre) - a < 50:
        raise LoiKhaiBao("doan %s cua %s/%s chi co %d bar" % (doan, ma, khung, len(pre) - a))
    cp = NDL.chi_phi(ma, pre)
    seg = pre.iloc[a:]
    if qt is None:
        th = NP.sinh_tu_spec(spec, pre)[a:]
        kq = MP.chay(seg, th, cp, ma=str(ma).upper(), khung=str(khung).upper())
        lenh = MX.tach_lenh(seg, kq.vi_the, kq.loi_tho, kq.loi)
    else:
        vao = dict(spec, giu=1, ra=[])
        th = NP.sinh_tu_spec(vao, pre)[a:]
        tran = int(spec.get("giu", 1)) if not spec.get("ra") else 200
        r = DQT.dap(seg, th, qt, giu_toi_da=max(1, tran))
        kq = VL.tinh_tien(seg, r, cp, ma=str(ma).upper(), khung=str(khung).upper())
        lenh = MX.tach_lenh(seg, kq.vi_the, kq.loi_tho, kq.loi, lenh_dap=r["lenh"])
    return {"df": seg, "pre": pre, "a": a, "kq": kq, "lenh": lenh, "cp": cp,
            "spec": spec, "quan_tri": qt, "ma": str(ma).upper(),
            "khung": str(khung).upper(), "doan": doan}


# ------------------------------------------------------ TIEN DUOI TRAN DD
def _chuoi_rong(loi_log, phi) -> np.ndarray:
    """Loi suat SO HOC rong moi bar o don bay 1: e^loi_tho - 1 - phi (quy uoc `quy_ve_dd`)."""
    x = np.expm1(np.asarray(loi_log, float)) - np.asarray(phi, float)
    return np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)


def o_don_bay(x: np.ndarray, so_nam: float, L: float) -> dict:
    """Chay lai chuoi rong `x` o don bay L, gop SO HOC -> CAGR, maxDD, co chay tai khoan."""
    song = 1.0 + float(L) * np.asarray(x, float)
    if np.any(song <= 0.0):
        return {"don_bay": float(L), "cagr": None, "dd": 1.0, "chet": True}
    von = np.cumprod(song)
    return {"don_bay": float(L), "cagr": float(von[-1] ** (1.0 / max(float(so_nam), 1e-9)) - 1.0),
            "dd": VL._sut_giam(von), "chet": False}


def tien_duoi_tran(loi_log, phi, so_nam: float, dd_tran: float = DD_TRAN,
                   L_toi_da: float = L_TOI_DA) -> dict:
    """CO LAI khong, va ra tien TOT NHAT bao nhieu khi maxDD van DUOI tran chu du an.

    Hai cau hoi tach ro (chu du an 25/09: "chi can co lai va maxdd duoi 80% la ok"):

    * **Co lai** khong phu thuoc don bay: tang truong G(L) = sum log(1 + L*x) co
      dG/dL = sum x tai L = 0, nen "co mot muc don bay cho lai" <=> tong loi suat rong
      tung bar > 0. Khi do LUON co mot muc don bay giu maxDD duoi tran.
    * **Ra bao nhieu**: G LOM theo L nen dinh (Kelly) la duy nhat. Dinh nam duoi muc
      don bay cham tran DD -> dung o Kelly (them don bay chi them rui ro VA bot tien);
      dinh nam tren -> dung o tran DD. Khong bao gio bao CAGR o don bay qua Kelly.

    Tran don bay `L_toi_da`. `gioi_han` noi cai gi chan: KELLY / TRAN_DD / TRAN_DON_BAY.
    """
    x = _chuoi_rong(loi_log, phi)
    nam = max(float(so_nam), 1e-9)
    ra = {"co_lai": bool(len(x) and float(np.sum(x)) > 0.0), "don_bay": None, "cagr": None,
          "dd": None, "gioi_han": None, "don_bay_tai_tran_dd": None, "chet": False}
    if not len(x):
        return ra
    muc = float(dd_tran) - 1e-3            # "DUOI 80%": dung o 79,9% chu khong cham 80%
    tren = o_don_bay(x, nam, L_toi_da)
    if not tren["chet"] and tren["dd"] < muc:
        L_tran, gh = float(L_toi_da), "TRAN_DON_BAY"
    else:
        lo, hi = 0.0, float(L_toi_da)       # DD tang theo L -> chia doi
        for _ in range(60):
            giua = 0.5 * (lo + hi)
            r = o_don_bay(x, nam, giua)
            if r["chet"] or r["dd"] >= muc:
                hi = giua
            else:
                lo = giua
        L_tran, gh = lo, "TRAN_DD"
    ra["don_bay_tai_tran_dd"] = L_tran
    if L_tran <= 0.0:
        ra["chet"] = True
        return ra
    if not ra["co_lai"]:
        # khong muc don bay nao cho lai: bao o don bay 1 (hoac thap hon neu 1 da vuot tran)
        r = o_don_bay(x, nam, min(1.0, L_tran))
        ra.update(don_bay=r["don_bay"], cagr=r["cagr"], dd=r["dd"], gioi_han="KHONG_LAI")
        return ra

    def dG(L: float) -> float:              # giam dan theo L
        return float(np.sum(x / (1.0 + L * x)))

    L = L_tran
    if dG(L_tran) < 0.0:
        lo, hi = 0.0, L_tran
        for _ in range(60):
            giua = 0.5 * (lo + hi)
            if dG(giua) > 0.0:
                lo = giua
            else:
                hi = giua
        L, gh = lo, "KELLY"
    r = o_don_bay(x, nam, L)
    ra.update(don_bay=L, cagr=r["cagr"], dd=r["dd"], gioi_han=gh, chet=r["chet"])
    return ra


def _moc(ma: str, khung: str, doan: str, seg: pd.DataFrame, cp) -> float:
    """Moc = max(mua-giu, ban-giu, tien mat 0), moi cai o muc ra tien tot nhat DUOI TRAN DD.

    Cung mot phep voi he (`tien_duoi_tran`) - `so-cuc-dai-phai-so-cung-co-mau`. Ban-giu
    rieng vi phi qua dem bat doi xung. Tu 25/09 moc chi la NHAN: he khong hon moc van DAT
    neu co lai (chu du an), nhung phai goi dung ten - giu tai san co don bay ra tien hon.
    """
    khoa = (ma, khung, doan, len(seg))
    if khoa not in _DEM_MOC:
        nam = VL.so_nam_cua(seg)
        ra = [0.0]
        for v in (1.0, -1.0):
            kq = MP.chay(seg, np.full(len(seg), v), cp, ma=ma, khung=khung,
                         don_bay=1.0, gop="so_hoc")
            phi = np.maximum(np.asarray(kq.loi_tho, float) - np.asarray(kq.loi, float), 0.0)
            t = tien_duoi_tran(kq.loi_tho, phi, nam)
            if t["co_lai"] and t["cagr"] is not None:
                ra.append(t["cagr"])
        _DEM_MOC[khoa] = float(max(ra))
    return _DEM_MOC[khoa]


def _pct(v, k: int = 2):
    return None if v is None else round(float(v) * 100.0, k)


def duoi_lo(tk: dict) -> dict:
    """Lai da DO voi duoi lo chua - NHAN, khong chan (chu du an: phuong phap nao cung duoc).

    He lai nho nhieu lan / lo lon it lan (martingale, DCA, TP hep SL rong) chi lo gia that
    khi gap du lenh thua. Hoa von khi ti le thua = rr/(1+rr); muon THAY duoi can so lenh ma
    o ti le hoa von ky vong co >= 3 lenh thua. Thieu thi ghi so can, de AI chay doan/ma dai hon.
    """
    n = int(tk.get("so_lenh") or 0)
    if not n:
        return {}
    p = tk.get("ty_le_thang")
    k = int(round(n * (1.0 - p))) if p is not None else None
    rr = tk.get("rr")
    if not rr or rr <= 0:
        if k == 0:
            return {"so_lenh_thua": 0,
                    "canh_bao": "chua thay lenh thua nao trong %d lenh - lai CHUA kiem voi duoi lo; "
                                "chay tren doan/ma dai hon truoc khi tin" % n}
        return {"so_lenh_thua": k}
    q = rr / (1.0 + rr)
    can = int(math.ceil(3.0 / q))
    ra = {"rr": rr, "ty_le_thua": round(1.0 - p, 4) if p is not None else None,
          "ty_le_thua_hoa_von": round(q, 4), "so_lenh_thua": k, "so_lenh_can_de_thay_duoi": can}
    if n < can:
        ra["canh_bao"] = ("rr %.3f: mot lenh thua an %.0f lenh thang, hoa von khi thua %.1f%% - can "
                          ">= %d lenh de thay duoi, moi co %d" % (rr, 1.0 / rr, 100.0 * q, can, n))
    return ra


def tach_beta(kq) -> dict:
    """Lai GOP = BETA (phoi nhiem trung binh x troi cua tai san) + CANH THOI DIEM (phan con lai).

    Vi sao: tieu chi chu du an ("chi can co lai") khong chan beta, va nhan "khong hon moc"
    (so CAGR o don bay tot nhat) chi bat duoc ~1/2 so y tuong NGAU NHIEN lot ba doan tren chuoi
    troi nhu chi so (`b nc kiem 30`, muc 5). Phep tach nay tra loi thang: bo he nay di, giu
    tai san voi cung phoi nhiem trung binh thi con lai bao nhieu. NHAN, khong chan.
    """
    v = np.nan_to_num(np.asarray(kq.vi_the, float))
    r = np.nan_to_num(np.asarray(kq.r, float)) if getattr(kq, "r", None) is not None else None
    if r is None or not len(v):
        return {}
    n = min(len(v), len(r))
    gop = float(np.nansum(np.asarray(kq.loi_tho, float)))
    beta = float(np.mean(v[:n]) * np.sum(r[:n]))
    ra = {"lai_gop_pct": round(gop * 100, 3), "phan_beta_pct": round(beta * 100, 3),
          "phan_canh_thoi_diem_pct": round((gop - beta) * 100, 3),
          "phoi_nhiem_tb": round(float(np.mean(v[:n])), 4)}
    if gop > 0:
        ra["ty_le_beta"] = round(beta / gop, 3)
    return ra


def chi_so_he(run: dict) -> dict:
    """Bang so cua mot lan chay: chi so, lenh, TIEN duoi tran DD, theo nam, chi phi, nhan."""
    kq, seg, lenh, cp = run["kq"], run["df"], run["lenh"], run["cp"]
    cs = DO.chi_so(kq.loi, seg.index, kq.vi_the)
    so_nam = VL.so_nam_cua(seg)
    tk = MX.thong_ke_lenh(lenh["loi"].to_numpy(float) if len(lenh) else np.zeros(0))
    tk["lenh_moi_nam"] = round(tk.get("so_lenh", 0) / max(so_nam, 1e-9), 1)
    if len(lenh):
        tk["so_bar_giu_trung_vi"] = float(lenh["so_bar"].median())
    phi = np.maximum(np.asarray(kq.loi_tho, float) - np.asarray(kq.loi, float), 0.0)
    t = tien_duoi_tran(kq.loi_tho, phi, so_nam)
    moc = _moc(run["ma"], run["khung"], run["doan"], seg, cp)
    tien = {"co_lai": t["co_lai"],
            "cagr_duoi_tran_pct": _pct(t["cagr"]),
            "don_bay": round(t["don_bay"], 3) if t["don_bay"] is not None else None,
            "dd_pct": _pct(t["dd"], 1),
            "gioi_han_don_bay": t["gioi_han"],
            "don_bay_tai_tran_dd": (round(t["don_bay_tai_tran_dd"], 3)
                                    if t["don_bay_tai_tran_dd"] is not None else None),
            "moc_duoi_tran_pct": _pct(moc),
            "hon_moc_pct": (round((t["cagr"] - moc) * 100, 2) if t["cagr"] is not None else None),
            "tran_dd_pct": round(DD_TRAN * 100, 1),
            "y_nghia": "CO LAI sau moi phi? va CAGR tot nhat voi maxDD < %.0f%% (don bay <= %g, "
                       "khong qua Kelly) - tieu chi chu du an 25/09. hon_moc chi la NHAN."
                       % (DD_TRAN * 100, L_TOI_DA)}
    s = pd.Series(np.asarray(kq.loi, float), index=seg.index)
    nam = s.groupby(pd.DatetimeIndex(seg.index).year).sum()
    theo_nam = {str(int(k)): round(float(np.expm1(v)) * 100, 2) for k, v in nam.items()}
    tong_cp = kq.chi_phi_spread + kq.chi_phi_truot + kq.chi_phi_giu
    bang = {
        "chi_so": {k: cs.get(k) for k in ("cagr_pct", "sharpe", "calmar", "max_dd_pct", "pf",
                                          "so_nam", "phoi_nhiem")},
        "lenh": tk, "tien": tien, "kinh_te": tang_2_kinh_te(kq), "duoi_lo": duoi_lo(tk),
        "beta": tach_beta(kq),
        "theo_nam_pct": theo_nam,
        "nam_duong": "%d/%d" % (sum(v > 0 for v in theo_nam.values()), len(theo_nam)),
        "chi_phi": {"tong_pct": round(tong_cp * 100, 3),
                    "qua_dem_pct": round(kq.chi_phi_giu * 100, 3),
                    "do_tin": getattr(cp, "do_tin", "?")},
        "canh_bao": list(dict.fromkeys(list(kq.canh_bao or [])[:4])),
    }
    bang["nhan_canh_bao"] = nhan_canh_bao(bang)
    return bang


def tang_2_kinh_te(kq) -> dict:
    """TANG 2 KINH TE cua `cong.py` (18/09) - tu 25/09 chi la NHAN, khong chan.

    Chu du an 25/09: "toi khong quan tam martingale hay dca hay la phuong phap gi". Van
    tinh bang CHINH ham + nguong cua `cong` (config/nguong.json) de hai cong noi cung mot
    con so; `qua=False` nghia la "kieu martingale/DCA" hoac "edge mong so voi phi".
    """
    try:
        from nhan import cong as CONG
        ng = CONG.nguong()
        rr = float(CONG.rr_thuc_te(kq.vi_the, kq.loi))
        lai = float(np.nansum(kq.loi))
        sp = float(abs(kq.chi_phi_spread or 0.0))
        rr_min, sp_min = float(ng["rr_thuc_te_toi_thieu"]), float(ng["edge_tren_spread_toi_thieu"])
        ok_rr = rr >= rr_min
        ok_sp = sp <= 0 or lai >= sp_min * sp
        return {"qua": bool(ok_rr and ok_sp),
                "rr_thuc_te": round(rr, 3) if np.isfinite(rr) else None, "rr_toi_thieu": rr_min,
                "lai_rong_tren_phi_spread": round(lai / sp, 2) if sp > 0 else None,
                "toi_thieu": sp_min,
                "ly_do": ([] if ok_rr else ["rr thuc te %.3f < %.2f (kieu martingale/DCA: lai nho "
                                            "nhieu lan, lo lon it lan)" % (rr, rr_min)])
                + ([] if ok_sp else ["lai rong %.2fx chi phi spread < %.1fx (edge mong so voi phi)"
                                     % (lai / sp, sp_min)])}
    except Exception as e:     # khong tinh duoc -> noi ro
        return {"qua": None, "loi": "%s: %s" % (type(e).__name__, str(e)[:120])}


def nhan_canh_bao(bang: dict) -> list[str]:
    """Moi thu KHONG chan nhung chu du an / AI phai thay truoc khi tin mot con so."""
    t, ra = bang.get("tien") or {}, []
    if t.get("co_lai") and t.get("hon_moc_pct") is not None and t["hon_moc_pct"] <= 0:
        ra.append("KHONG hon moc: mua-giu/ban-giu co don bay cung tran DD ra %s%%/nam - day la "
                  "beta, chua phai he" % t.get("moc_duoi_tran_pct"))
    b = bang.get("beta") or {}
    if t.get("co_lai") and (b.get("ty_le_beta") or 0) >= 0.5:
        ra.append("%.0f%% lai gop la BETA (phoi nhiem TB %+.2f x troi tai san); canh thoi diem chi "
                  "lam ra %+.2f%% - giu tai san voi cung phoi nhiem cung ra phan lon so do"
                  % (100 * min(b["ty_le_beta"], 9.99), b["phoi_nhiem_tb"],
                     b["phan_canh_thoi_diem_pct"]))
    ra += list((bang.get("kinh_te") or {}).get("ly_do") or [])
    if (bang.get("duoi_lo") or {}).get("canh_bao"):
        ra.append(bang["duoi_lo"]["canh_bao"])
    if t.get("co_lai") and t.get("gioi_han_don_bay") == "TRAN_DON_BAY":
        ra.append("cham tran don bay x%g ma DD moi %s%% - so tien bi chan boi tran don bay, "
                  "khong boi rui ro" % (L_TOI_DA, t.get("dd_pct")))
    return ra


def _phan_quyet(bang: dict) -> tuple[str, str]:
    """DAT / AM / CHUA_DO_DUOC cho kham_pha / xac_nhan - TIEU CHI CHU DU AN 25/09.

    DAT = CO LAI sau moi phi (ky vong lenh > 0 va tong loi suat rong > 0). Khi do luon co
    mot muc don bay giu maxDD duoi tran, va `tien` bao muc ra tien tot nhat o do. Phuong
    phap nao cung duoc. Hon moc / tang 2 kinh te / duoi lo: `nhan_canh_bao`, khong chan.
    """
    n = (bang.get("lenh") or {}).get("so_lenh", 0)
    if n < LENH_TOI_THIEU:
        return "CHUA_DO_DUOC", "chi %d lenh < %d" % (n, LENH_TOI_THIEU)
    t = bang.get("tien") or {}
    kv = (bang.get("lenh") or {}).get("ky_vong_bps") or 0.0
    if t.get("cagr_duoi_tran_pct") is None:
        return "CHUA_DO_DUOC", "khong tinh duoc tien duoi tran DD %.0f%%" % (DD_TRAN * 100)
    if t.get("co_lai") and kv > 0:
        return "DAT", ("co lai: %+.2f%%/nam o don bay x%.2f, maxDD %.1f%% < %.0f%%, ky vong "
                       "%+.2f bps/lenh" % (t["cagr_duoi_tran_pct"], t["don_bay"], t["dd_pct"],
                                           DD_TRAN * 100, kv))
    return "AM", ("khong co lai sau phi: ky vong %+.2f bps/lenh, %+.2f%%/nam o don bay x%.2f"
                  % (kv, t["cagr_duoi_tran_pct"], t.get("don_bay") or 0.0))


def _tom_tat(bang: dict, spec: dict, qt) -> str:
    l, t = bang.get("lenh") or {}, bang.get("tien") or {}
    return ("%s%s: %s%%/nam @x%s DD%s%% (moc %s) · %s lenh · kv %s bps · t %s · nam duong %s"
            % (spec.get("ten"), (" +qt" + json.dumps(qt, sort_keys=True)) if qt else "",
               t.get("cagr_duoi_tran_pct"), t.get("don_bay"), t.get("dd_pct"),
               t.get("moc_duoi_tran_pct"), l.get("so_lenh"), l.get("ky_vong_bps"),
               l.get("t_lenh"), bang.get("nam_duong")))


# ---------------------------------------------------------- DANH GIA
def danh_gia(ma: str, khung: str, spec: dict, quan_tri: dict | None = None,
             doan: str = "kham_pha", gt_id: int | None = None,
             vong_id: int | None = None, ghi: bool = True) -> dict:
    """Thu MOT he tren `kham_pha` hoac `xac_nhan`. Cong cu `thu_co_che` / `xac_nhan`."""
    if doan not in NDL.DOAN_MO:
        raise LoiKhaiBao("doan chi duoc la %s (niem phong co cong cu rieng)" % (NDL.DOAN_MO,))
    t0 = time.time()
    try:
        s = chuan_hoa_spec(spec)
        qt = chuan_hoa_quan_tri(quan_tri)
    except LoiKhaiBao as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khai bao sai: %s" % e}
    vt = ST.van_tay("danh_gia", str(ma).upper(), str(khung).upper(), doan,
                    {k: s[k] for k in ("vao", "ra", "chieu", "giu")}, qt)
    cu = ST.da_thu(vt)
    if cu and cu.get("ket_qua"):
        kq = dict(cu["ket_qua"])
        kq["tu_so_tay"] = "thi nghiem %s da chay y het - tra ket qua cu, KHONG tinh them phep thu" % cu["id"]
        kq["tn_id"] = cu["id"]
        return kq
    try:
        run = chay_he(ma, khung, s, qt, doan)
        bang = chi_so_he(run)
    except LoiKhaiBao as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": str(e)}
    except Exception as e:  # engine hong -> khong phai AM
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "loi khi chay: %s: %s" % (type(e).__name__, str(e)[:200])}
    tt, ly_do = _phan_quyet(bang)
    ra = {"trang_thai": tt, "ly_do": ly_do, "ma": run["ma"], "khung": run["khung"], "doan": doan,
          "spec_ten": s["ten"], "quan_tri": qt, **bang}
    if doan == "xac_nhan":
        dong = ST.dong_ho(ST.goc_cua(gt_id)) if gt_id else []
        nhin = ST.mot("SELECT COUNT(*) n FROM thi_nghiem WHERE doan='xac_nhan' AND ma=? AND khung=?"
                      + (" AND gt_id IN (%s)" % ",".join("?" * len(dong)) if dong else ""),
                      run["ma"], run["khung"], *dong).get("n", 0)
        ra["so_lan_nhin_xac_nhan_truoc"] = int(nhin)
        if nhin >= NHIN_XAC_NHAN_CANH_BAO:
            ra["canh_bao"] = ra.get("canh_bao", []) + [
                "doan xac_nhan da bi nhin %d lan cho dong nay - no dang thanh doan kham pha "
                "thu hai; ket qua o day lac quan dan" % nhin]
        kp = ST.da_thu(ST.van_tay("danh_gia", run["ma"], run["khung"], "kham_pha",
                                  {k: s[k] for k in ("vao", "ra", "chieu", "giu")}, qt))
        if kp and kp.get("ket_qua"):
            t_kp = kp["ket_qua"].get("tien") or {}
            ra["so_voi_kham_pha"] = {
                "cagr_kham_pha_pct": t_kp.get("cagr_duoi_tran_pct"),
                "cagr_xac_nhan_pct": ra["tien"]["cagr_duoi_tran_pct"],
                "ky_vong_kham_pha_bps": (kp["ket_qua"].get("lenh") or {}).get("ky_vong_bps"),
                "ky_vong_xac_nhan_bps": ra["lenh"].get("ky_vong_bps")}
    if ghi:
        ra["tn_id"] = ST.ghi_thi_nghiem(
            "xac_nhan" if doan == "xac_nhan" else "thu_co_che",
            {"spec": s, "quan_tri": qt}, ra, tt, vt, run["ma"], run["khung"], doan,
            gt_id=gt_id, so_phep_thu=1, giay=time.time() - t0, vong_id=vong_id,
            tom_tat=_tom_tat(bang, s, qt))
    return ra


# ---------------------------------------------------------------- QUET
def _luoi_tu_dong(spec: dict, toi_da_tham_so: int = 3) -> dict:
    """Luoi mac dinh quanh gia tri hien tai cho <= 3 tham so dau (nguong + chu ky + giu)."""
    ts = NP.tham_so_cua(spec)
    uu = sorted(ts, key=lambda k: (0 if k.endswith("_hang") else 1 if k.endswith("_n") else 2))
    luoi = {}
    for k in uu:
        v = ts[k]
        if isinstance(v, bool):
            continue
        if isinstance(v, int) and not k.endswith("_hang"):
            cac = sorted({max(1, int(round(v * f))) for f in (0.5, 0.75, 1.0, 1.5, 2.0)})
        else:
            d = abs(float(v)) * 0.15 if float(v) != 0 else 0.05
            cac = sorted({MX._lam_tron(float(v) + i * d) for i in (-2, -1, 0, 1, 2)})
        if len(cac) > 1:
            luoi[k] = cac
        if len(luoi) >= toi_da_tham_so:
            break
    return luoi


def quet(ma: str, khung: str, spec: dict, luoi: dict | None = None,
         quan_tri: dict | None = None, doan: str = "kham_pha", gt_id: int | None = None,
         vong_id: int | None = None, toi_da_o: int = O_QUET_TOI_DA, hat: int = 0) -> dict:
    """Quet tham so + doc HINH DANG (cao nguyen hay cai gai). Tinh tung o la mot phep thu."""
    if doan not in NDL.DOAN_MO:
        raise LoiKhaiBao("doan quet chi duoc la kham_pha/xac_nhan")
    t0 = time.time()
    try:
        s = chuan_hoa_spec(spec)
        qt = chuan_hoa_quan_tri(quan_tri)
    except LoiKhaiBao as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khai bao sai: %s" % e}
    ts_goc = NP.tham_so_cua(s)
    luoi = dict(luoi or _luoi_tu_dong(s))
    la = [k for k in luoi if k not in ts_goc and not k.startswith("qt.")]
    if la:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "tham so khong co trong spec: %s. Tham so co: %s" % (la, sorted(ts_goc))}
    if not luoi:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "spec khong co tham so so nao de quet"}
    khoa = list(luoi)
    o_all = list(itertools.product(*[luoi[k] for k in khoa]))
    rng = np.random.default_rng(hat)
    if len(o_all) > toi_da_o:
        chon = sorted(rng.choice(len(o_all), size=toi_da_o, replace=False))
        o_all = [o_all[i] for i in chon]
    vt = ST.van_tay("quet", str(ma).upper(), str(khung).upper(), doan,
                    {k: s[k] for k in ("vao", "ra", "chieu", "giu")}, qt, luoi, toi_da_o, hat)
    cu = ST.da_thu(vt)
    if cu and cu.get("ket_qua"):
        kq = dict(cu["ket_qua"])
        kq["tu_so_tay"] = "quet %s da chay y het - tra ket qua cu" % cu["id"]
        return kq
    bang = []
    for gt in o_all:
        ts = dict(zip(khoa, gt))
        qt2 = dict(qt or {})
        ts_spec = {}
        for k, v in ts.items():
            if k.startswith("qt."):
                qt2[k[3:]] = v
            else:
                ts_spec[k] = v
        try:
            s2 = NP.ap_tham_so(s, ts_spec)
            run = chay_he(ma, khung, s2, qt2 or None, doan)
            b = chi_so_he(run)
            bang.append({"tham_so": ts, "cagr_duoi_tran_pct": b["tien"]["cagr_duoi_tran_pct"],
                         "co_lai": b["tien"]["co_lai"], "don_bay": b["tien"]["don_bay"],
                         "hon_moc_pct": b["tien"]["hon_moc_pct"],
                         "ky_vong_bps": b["lenh"].get("ky_vong_bps"),
                         "so_lenh": b["lenh"].get("so_lenh", 0),
                         "sharpe": b["chi_so"].get("sharpe"), "nam_duong": b["nam_duong"]})
        except Exception as e:
            bang.append({"tham_so": ts, "loi": "%s: %s" % (type(e).__name__, str(e)[:120])})
    do_duoc = [r for r in bang if r.get("cagr_duoi_tran_pct") is not None
               and (r.get("so_lenh") or 0) >= LENH_TOI_THIEU]
    ra: dict = {"luoi": luoi, "so_o": len(bang), "so_o_do_duoc": len(do_duoc)}
    if len(do_duoc) < max(3, len(bang) // 3):
        ra.update(trang_thai="CHUA_DO_DUOC", ly_do="chi %d/%d o do duoc (it lenh hoac loi)"
                  % (len(do_duoc), len(bang)), bang=bang[:10])
        tt = "CHUA_DO_DUOC"
    else:
        cg = np.array([r["cagr_duoi_tran_pct"] for r in do_duoc], float)
        lai = np.array([bool(r.get("co_lai")) and (r.get("ky_vong_bps") or 0) > 0
                        for r in do_duoc], bool)
        tot = max(do_duoc, key=lambda r: r["cagr_duoi_tran_pct"])
        # hang xom cua o tot nhat: khac dung MOT tham so, mot buoc tren luoi
        buoc = {k: {v: i for i, v in enumerate(luoi[k])} for k in khoa}
        vi_tri_tot = {k: buoc[k][tot["tham_so"][k]] for k in khoa}
        xom = [r["cagr_duoi_tran_pct"] for r in do_duoc
               if sum(abs(buoc[k][r["tham_so"][k]] - vi_tri_tot[k]) for k in khoa) == 1]
        ty_lai = float(np.mean(lai))
        xom_tb = float(np.mean(xom)) if xom else None
        tot_lai = bool(tot.get("co_lai")) and (tot.get("ky_vong_bps") or 0) > 0
        if ty_lai >= 0.6 and (xom_tb is None or xom_tb > 0):
            hinh = "CAO_NGUYEN"
        elif tot_lai and ty_lai < 0.3:
            hinh = "CAI_GAI"
        else:
            hinh = "HON_HOP"
        hm = [r["hon_moc_pct"] for r in do_duoc if r.get("hon_moc_pct") is not None]
        ra.update({
            "hinh_dang": hinh, "ty_le_o_co_lai": round(ty_lai, 3),
            "cagr_duoi_tran_trung_vi_pct": round(float(np.median(cg)), 2),
            "ty_le_o_hon_moc_nhan": round(float(np.mean(np.array(hm) > 0)), 3) if hm else None,
            "o_tot_nhat": tot, "hang_xom_tot_nhat_tb_pct": round(xom_tb, 2) if xom_tb is not None else None,
            "bang_top": sorted(do_duoc, key=lambda r: -r["cagr_duoi_tran_pct"])[:8],
            "doc_dung": "Chon theo HINH DANG, khong theo o tot nhat: cuc dai cua %d o tren nhieu "
                        "cung dep. Cao nguyen = nhieu o lan can cung CO LAI." % len(bang)})
        tt = "DAT" if (hinh == "CAO_NGUYEN" and tot_lai) else "AM"
        ra["trang_thai"] = tt
    ra["tn_id"] = ST.ghi_thi_nghiem(
        "quet", {"spec": s, "quan_tri": qt, "luoi": luoi}, ra, tt, vt, str(ma).upper(),
        str(khung).upper(), doan, gt_id=gt_id, so_phep_thu=len(bang), giay=time.time() - t0,
        vong_id=vong_id, tom_tat="quet %d o %s: %s" % (len(bang), s["ten"], ra.get("hinh_dang", tt)))
    return ra


# ---------------------------------------------------------------- MO XE
def mo_xe(ma: str, khung: str, spec: dict, quan_tri: dict | None = None,
          so_null: int = 200, gt_id: int | None = None, vong_id: int | None = None) -> dict:
    """Mo xe lenh cua mot he tren KHAM PHA -> bo loc + luat quan tri de xuat."""
    t0 = time.time()
    try:
        s = chuan_hoa_spec(spec)
        qt = chuan_hoa_quan_tri(quan_tri)
    except LoiKhaiBao as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khai bao sai: %s" % e}
    vt = ST.van_tay("mo_xe", str(ma).upper(), str(khung).upper(),
                    {k: s[k] for k in ("vao", "ra", "chieu", "giu")}, qt, so_null)
    cu = ST.da_thu(vt)
    if cu and cu.get("ket_qua"):
        kq = dict(cu["ket_qua"])
        kq["tu_so_tay"] = "mo xe %s da chay y het" % cu["id"]
        return kq
    try:
        run = chay_he(ma, khung, s, qt, "kham_pha")
    except Exception as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "%s: %s" % (type(e).__name__, str(e)[:200])}
    lenh = run["lenh"]
    X = DT.tinh(run["pre"]).iloc[run["a"]:]
    if len(lenh):
        X_th = X.iloc[lenh["tin_hieu"].to_numpy(int)].reset_index(drop=True)
    else:
        X_th = X.iloc[:0]
    ra = MX.mo_xe_lenh(lenh, X_th, so_null=so_null, hat=int(gt_id or 0))
    for l in ra.get("luat_loc", []):
        if not l.get("dsl") or any(x is None for x in l["dsl"]):
            continue
        s2 = copy.deepcopy(s)
        s2["vao"] = list(s2["vao"]) + l["dsl"]
        s2["ten"] = NP.chuan_hoa_ten((s["ten"] + "_loc_" + ST.van_tay(l["dsl"]))[:60])
        l["spec_de_xuat"] = s2
    ra["ma"], ra["khung"], ra["spec_ten"] = run["ma"], run["khung"], s["ten"]
    ra["doc_dung"] = ("Loc hau kiem tren chinh doan nay luon dep hon that. Chi tin mot bo loc "
                      "khi p_null thap VA spec_de_xuat chay lai tren doan xac_nhan van CO LAI "
                      "(va lai hon he goc).")
    tt = ra.get("trang_thai", "CHUA_DO_DUOC")
    ra["tn_id"] = ST.ghi_thi_nghiem(
        "mo_xe", {"spec": s, "quan_tri": qt, "so_null": so_null}, ra, tt, vt, run["ma"],
        run["khung"], "kham_pha", gt_id=gt_id, so_phep_thu=1, giay=time.time() - t0,
        vong_id=vong_id,
        tom_tat="mo xe %s: %d lenh, loc tot nhat %s" % (
            s["ten"], (ra.get("tong_quan") or {}).get("so_lenh", 0),
            (ra["luat_loc"][0]["dieu_kien"] + " p%.3f" % (ra["luat_loc"][0]["p_null"] or 1))
            if ra.get("luat_loc") else "khong co"))
    return ra


# ---------------------------------------------------------- QUY LUAT
def tim_quy_luat(ma: str, khung: str, chan_troi=(1, 3, 5, 10), so_null: int = 200,
                 chon_dac_trung: list | None = None, gt_id: int | None = None,
                 vong_id: int | None = None) -> dict:
    """Tim quy luat tren KHAM PHA cua (ma, khung) - khong can he goc nao."""
    t0 = time.time()
    ma, khung = str(ma).upper(), str(khung).upper()
    ct = tuple(sorted({int(h) for h in chan_troi if 1 <= int(h) <= 100}))
    if not ct:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "chan_troi rong"}
    vt = ST.van_tay("tim_quy_luat", ma, khung, ct, so_null, sorted(chon_dac_trung or []))
    cu = ST.da_thu(vt)
    if cu and cu.get("ket_qua"):
        kq = dict(cu["ket_qua"])
        kq["tu_so_tay"] = "tim quy luat %s da chay y het" % cu["id"]
        return kq
    try:
        df_full = NDL.nap(ma, khung)
        pre, a = NDL.cat_doan(df_full, "kham_pha")
        X = DT.tinh(pre, chon=chon_dac_trung)
        cp = NDL.chi_phi(ma, pre)
    except Exception as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "%s: %s" % (type(e).__name__, str(e)[:200])}
    ra = MX.tim_quy_luat(pre, X, cp, bat_dau=a, chan_troi=ct, so_null=so_null,
                         hat=int(gt_id or 0), bar_moi_ngay=_bar_moi_ngay(pre.index))
    ra["ma"], ra["khung"] = ma, khung
    ra["doc_dung"] = ("p_null da tinh ca viec do tim tren moi dac trung/nguong/chan troi. Luat "
                      "p_null > 0,1 thi nhieu trang cung de ra. Moi luat DAT phai chay lai bang "
                      "thu_co_che (co chi phi day du) roi xac_nhan.")
    tt = ra.get("trang_thai", "CHUA_DO_DUOC")
    tot = ra["luat"][0] if ra.get("luat") else None
    ra["tn_id"] = ST.ghi_thi_nghiem(
        "tim_quy_luat", {"chan_troi": ct, "so_null": so_null, "chon": chon_dac_trung}, ra, tt,
        vt, ma, khung, "kham_pha", gt_id=gt_id, so_phep_thu=1, giay=time.time() - t0,
        vong_id=vong_id,
        tom_tat="quy luat %s/%s: %s" % (ma, khung, ("%s chieu %+d h%d rong %.1fbps p%.3f" % (
            tot["dieu_kien"], tot["chieu"], tot["giu"], tot["tb_rong_bps"], tot["p_null"] or 1))
            if tot else "khong co"))
    return ra


# ----------------------------------------------------------- HO SO TAI SAN
def ho_so(ma: str, khung: str, vong_id: int | None = None) -> dict:
    """Tinh cach cua (ma, khung) tren KHAM PHA: hoi quy hay xu huong, mua vu, chi phi, moc."""
    ma, khung = str(ma).upper(), str(khung).upper()
    vt = ST.van_tay("ho_so", ma, khung)
    cu = ST.da_thu(vt)
    if cu and cu.get("ket_qua"):
        return dict(cu["ket_qua"], tu_so_tay=True)
    t0 = time.time()
    try:
        df_full = NDL.nap(ma, khung)
        pre, a = NDL.cat_doan(df_full, "kham_pha")
        cp = NDL.chi_phi(ma, pre)
    except Exception as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "%s: %s" % (type(e).__name__, str(e)[:200])}
    seg = pre.iloc[a:]
    lo = np.log(seg["open"].to_numpy(float))
    r = np.diff(lo)
    n = len(r)
    sd = float(np.std(r, ddof=1))
    tq = {str(k): round(float(pd.Series(r).autocorr(k)), 4) for k in (1, 2, 3, 5)}
    vr = {}
    for q in (2, 5, 10, 20):
        if n > 5 * q:
            rq = lo[q:] - lo[:-q]
            v = float(np.var(rq, ddof=1) / (q * sd * sd))
            z = (v - 1.0) / math.sqrt(2.0 * (2 * q - 1) * (q - 1) / (3.0 * q * n))
            vr[str(q)] = {"vr": round(v, 3), "z": round(z, 2)}
    bmn = _bar_moi_ngay(seg.index)
    sp_bps = float(np.mean(cp.spread_mang(seg.index))) * 1e4
    bd_bps = float(np.median((seg["high"] - seg["low"]) / seg["open"])) * 1e4
    tq_abs = round(float(pd.Series(np.abs(r)).autocorr(1)), 3)
    mv = {}
    s = pd.Series(r, index=seg.index[:-1])
    for ten, k in (("thu", s.index.dayofweek), ("thang", s.index.month)):
        g = s.groupby(k)
        t = (g.mean() / (sd / np.sqrt(g.count()))).round(2)
        mv[ten] = {str(int(i)): float(v) for i, v in t.items()}
    if bmn > 1.5:
        g = s.groupby(s.index.hour)
        mv["gio"] = {str(int(i)): float(v) for i, v in (g.mean() / (sd / np.sqrt(g.count()))).round(2).items()}
    try:
        moc = _moc(ma, khung, "kham_pha", seg, cp)
        mg = MP.mua_giu(seg, cp)
        mg_cs = DO.chi_so(mg.loi, seg.index)
    except Exception:
        moc, mg_cs = None, {}
    goi_y = []
    v5 = (vr.get("5") or {}).get("vr")
    if v5 is not None and v5 < 0.92 and (vr.get("5") or {}).get("z", 0) < -2:
        goi_y.append("VR(5) < 1 co y nghia -> HOI QUY ngan han: thu ho quay_ve_trung_binh, "
                     "vao nguoc cu soc, giu 1-5 bar")
    if v5 is not None and v5 > 1.08 and (vr.get("5") or {}).get("z", 0) > 2:
        goi_y.append("VR(5) > 1 co y nghia -> QUAN TINH: thu ho xu_huong / pha_vo")
    if tq_abs > 0.1:
        goi_y.append("bien dong co CUM (tq|r| %.2f) -> dieu kien che do bien dong (atr_pv) "
                     "co the tach duoc lenh tot/xau" % tq_abs)
    if sp_bps > 0.25 * bd_bps:
        goi_y.append("chi phi %.1f bps = %.0f%% bien do mot bar: khung nay qua dat cho luot song "
                     "ngan, uu tien giu lau hon hoac khung lon hon" % (sp_bps, 100 * sp_bps / bd_bps))
    ra = {"trang_thai": "DAT", "ma": ma, "khung": khung, "so_bar_kham_pha": int(len(seg)),
          "tu": str(seg.index[0])[:10], "den": str(seg.index[-1])[:10],
          "bar_moi_ngay": round(bmn, 2), "sd_bar_bps": round(sd * 1e4, 2),
          "bien_do_bar_trung_vi_bps": round(bd_bps, 2), "spread_mot_chieu_bps": round(sp_bps, 2),
          "chi_phi_do_tin": getattr(cp, "do_tin", "?"),
          "phi_qua_dem_nam": {"mua": cp.phi_nam_mua, "ban": cp.phi_nam_ban},
          "tu_tuong_quan": tq, "ti_so_phuong_sai": vr, "tu_tuong_quan_bien_do": tq_abs,
          "mua_vu_t": mv, "moc_duoi_tran_pct": round(moc * 100, 2) if moc is not None else None,
          "mua_giu": {k: mg_cs.get(k) for k in ("cagr_pct", "sharpe", "max_dd_pct")},
          "goi_y_huong": goi_y, "la_tong_hop": NDL.la_tong_hop(ma)}
    ST.ghi_thi_nghiem("ho_so", {"ma": ma, "khung": khung}, ra, "DAT", vt, ma, khung, "kham_pha",
                      so_phep_thu=0, giay=time.time() - t0, vong_id=vong_id,
                      tom_tat="ho so %s/%s: VR5 %s, tq1 %s" % (ma, khung, v5, tq.get("1")))
    return ra


# ----------------------------------------------------------- NIEM PHONG
def _sharpe_giam_phat(loi: np.ndarray, so_phep_thu: int) -> dict:
    """Deflated Sharpe (Bailey & Lopez de Prado) - NHAN, khong chan (LUAT SO 0)."""
    from scipy import stats
    y = np.asarray(loi, float)
    y = y[np.isfinite(y)]
    T = len(y)
    if T < 30 or np.std(y) == 0:
        return {"dsr": None, "ly_do": "khong du bar"}
    sr = float(np.mean(y) / np.std(y, ddof=1))
    g3 = float(stats.skew(y))
    g4 = float(stats.kurtosis(y, fisher=False))
    N = max(int(so_phep_thu), 1)
    em = 0.5772156649
    if N > 1:
        sr0 = math.sqrt(1.0 / (T - 1)) * ((1 - em) * stats.norm.ppf(1 - 1.0 / N)
                                          + em * stats.norm.ppf(1 - 1.0 / (N * math.e)))
    else:
        sr0 = 0.0
    mau = max(1e-12, 1 - g3 * sr + (g4 - 1) / 4.0 * sr * sr)
    dsr = float(stats.norm.cdf((sr - sr0) * math.sqrt(T - 1) / math.sqrt(mau)))
    return {"dsr": round(dsr, 4), "sharpe_bar": round(sr, 5), "sharpe_nguong_nhieu_bar": round(sr0, 5),
            "so_phep_thu": N,
            "doc": "xac suat Sharpe that > 0 sau khi tru cuc dai cua %d phep thu; < 0,95 = "
                   "co the chi la cuc dai ngau nhien (NHAN, khong chan)" % N}


def niem_phong(ma: str, khung: str, spec: dict, quan_tri: dict | None = None,
               gt_id: int | None = None, vong_id: int | None = None,
               cong_that: bool = True) -> dict:
    """MO NIEM PHONG: phep thu CUOI, mot lan cho mot khai bao da dong bang.

    Cong TIEN (chan) = tieu chi chu du an 25/09 tren du lieu CHUA TUNG DUNG TOI:
      * CO LAI sau moi phi (ky vong lenh > 0), chi phi DO DUOC, >= 20 lenh;
      * maxDD DUOI 80% o DON BAY CAM KET - don bay chot tren du lieu da mo (kham pha +
        xac nhan) TRUOC khi nhin doan nay. Chon don bay tren chinh doan niem phong la
        nhin truoc: con so luc do luon dep va khong ai trade duoc no.
    Nhan (khong chan): hon moc, tang 2 kinh te, duoi lo, so phep thu da tieu, Sharpe
    giam phat, cong that `cong.xet` (placebo, alpha) voi `ghi_so=False`.
    """
    if gt_id is None:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "niem_phong can gt_id: moi lan mo phai gan voi mot gia thuyet da ghi"}
    if not ST.mot("SELECT id FROM gia_thuyet WHERE id=?", int(gt_id)):
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khong co gia thuyet id=%s" % gt_id}
    try:
        s = chuan_hoa_spec(spec)
        qt = chuan_hoa_quan_tri(quan_tri)
    except LoiKhaiBao as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khai bao sai: %s" % e}
    ma, khung = str(ma).upper(), str(khung).upper()
    vt = ST.van_tay("niem_phong", ma, khung, {k: s[k] for k in ("vao", "ra", "chieu", "giu")}, qt)
    cu = ST.mot("SELECT * FROM niem_phong WHERE van_tay=?", vt)
    if cu:
        kq = json.loads(cu["ket_qua"] or "{}")
        kq["da_mo_truoc"] = "khai bao nay da mo niem phong luc %s - XAC NHAN LA HAM Y NGUYEN, " \
                            "khong mo lai" % cu["luc"]
        return kq
    dong = ST.dong_ho(ST.goc_cua(int(gt_id)))
    da_mo = int(ST.mot("SELECT COUNT(*) n FROM niem_phong WHERE gt_id IN (%s)"
                       % ",".join("?" * len(dong)), *dong).get("n") or 0)
    if da_mo >= MO_NIEM_PHONG_TOI_DA:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "dong gia thuyet nay da mo niem phong %d lan (tran %d). Mo them la bien "
                         "doan niem phong thanh doan chon." % (da_mo, MO_NIEM_PHONG_TOI_DA)}
    t0 = time.time()
    try:
        run = chay_he(ma, khung, s, qt, "niem_phong", _giay_phep=True)
        bang = chi_so_he(run)
    except Exception as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "loi khi chay: %s: %s" % (type(e).__name__, str(e)[:200])}
    # Don bay CAM KET: muc ra tien tot nhat duoi tran tren du lieu DA MO (truoc doan nay).
    cam_ket = {"don_bay": None, "nguon": "kham_pha+xac_nhan"}
    try:
        run_mo = chay_he(ma, khung, s, qt, "truoc_niem_phong")
        k_mo = run_mo["kq"]
        t_mo = tien_duoi_tran(k_mo.loi_tho, np.maximum(np.asarray(k_mo.loi_tho, float)
                                                       - np.asarray(k_mo.loi, float), 0.0),
                              VL.so_nam_cua(run_mo["df"]))
        if t_mo["co_lai"] and t_mo["don_bay"]:
            cam_ket.update(don_bay=float(t_mo["don_bay"]), cagr_truoc_pct=_pct(t_mo["cagr"]),
                           dd_truoc_pct=_pct(t_mo["dd"], 1), gioi_han=t_mo["gioi_han"])
        else:
            cam_ket.update(don_bay=1.0, ghi_chu="du lieu mo KHONG co lai -> don bay 1")
    except Exception as e:
        cam_ket.update(don_bay=1.0, ghi_chu="khong chay duoc du lieu mo (%s) -> don bay 1"
                       % type(e).__name__)
    kq_np = run["kq"]
    x_np = _chuoi_rong(kq_np.loi_tho, np.maximum(np.asarray(kq_np.loi_tho, float)
                                                 - np.asarray(kq_np.loi, float), 0.0))
    o_ck = o_don_bay(x_np, VL.so_nam_cua(run["df"]), cam_ket["don_bay"])
    bang["tien"]["o_don_bay_cam_ket"] = {
        "don_bay": round(cam_ket["don_bay"], 3), "cagr_pct": _pct(o_ck["cagr"]),
        "dd_pct": _pct(o_ck["dd"], 1), "chay_tai_khoan": o_ck["chet"], **{
            k: v for k, v in cam_ket.items() if k != "don_bay"}}
    n = bang["lenh"].get("so_lenh", 0)
    kv = bang["lenh"].get("ky_vong_bps") or 0
    co_lai = bool(bang["tien"].get("co_lai")) and kv > 0
    do_tin = getattr(run["cp"], "do_tin", "KHAI")
    L_ck, dd_ck = cam_ket["don_bay"], o_ck["dd"]
    if n < LENH_TOI_THIEU_NIEM_PHONG:
        tt, ly = "CHUA_DO_DUOC", "chi %d lenh < %d tren doan niem phong" % (n, LENH_TOI_THIEU_NIEM_PHONG)
    elif do_tin == "KHAI":
        tt, ly = "CHUA_DO_DUOC", "chi phi KHAI (chua do) - khong bao gio DAT (luat chi phi)"
    elif not co_lai:
        tt, ly = "AM", "KHONG co lai sau phi tren doan niem phong: ky vong %+.2f bps, %d lenh" % (kv, n)
    elif o_ck["chet"] or dd_ck is None or dd_ck >= DD_TRAN:
        tt, ly = "AM", ("co lai (ky vong %+.2f bps, %d lenh) NHUNG o don bay cam ket x%.2f maxDD "
                        "%s >= %.0f%% - don bay chot tren du lieu mo qua cao cho doan nay (doan nay "
                        "chiu duoc toi x%s)" % (kv, n, L_ck, "CHAY TAI KHOAN" if o_ck["chet"]
                                                else "%.1f%%" % (dd_ck * 100), DD_TRAN * 100,
                                                bang["tien"].get("don_bay_tai_tran_dd")))
    else:
        tt, ly = "DAT", ("co lai tren doan niem phong: %+.2f%%/nam o don bay cam ket x%.2f, maxDD "
                         "%.1f%% < %.0f%%, %d lenh, ky vong %+.2f bps"
                         % ((o_ck["cagr"] or 0) * 100, L_ck, dd_ck * 100, DD_TRAN * 100, n, kv))
    pt_dong = ST.dem_phep_thu(gt_id=int(gt_id))
    pt_ma = ST.dem_phep_thu(ma=ma, khung=khung)
    nhan = {"so_phep_thu_dong_gia_thuyet": pt_dong, "so_phep_thu_tren_ma": pt_ma,
            "lan_mo_niem_phong_trong_dong": da_mo + 1,
            "sharpe_giam_phat": _sharpe_giam_phat(run["kq"].loi, max(pt_dong, 1)),
            "canh_bao": bang.get("nhan_canh_bao") or []}
    try:
        ok, why = NP.kiem_khong_nhin_truoc(s, run["pre"])
        nhan["phep_cat_nhin_truoc"] = why
        if not ok:
            tt, ly = "CHUA_DO_DUOC", "phep cat bat NHIN TRUOC: %s" % why
    except Exception as e:
        nhan["phep_cat_nhin_truoc"] = "loi: %s" % str(e)[:120]
    if cong_that and tt != "CHUA_DO_DUOC":
        try:
            from nhan import cong as CONG
            bh = MP.mua_giu(run["df"], run["cp"])
            # da_dang_ky=True: khai bao da DONG BANG va van tay truoc khi mo doan nay -
            # dung nghia dang ky truoc, nen placebo duoc chay (lam NHAN). tren_holdout=
            # False + ghi_so=False: khong dung vao chuoi FDR cua so cai chung.
            cx = CONG.xet(run["df"], run["kq"], bh, run["cp"], gt_ma="nc:%s" % s["ten"],
                          ho=s.get("ho", "chung"), da_dang_ky=True, tren_holdout=False,
                          ghi_so=False)
            nhan["cong_that"] = {"verdict": cx.get("verdict"),
                                 "ly_do": (cx.get("ly_do") or [])[:5],
                                 "nhan": cx.get("nhan_canh_bao") or cx.get("nhan")}
        except Exception as e:
            nhan["cong_that"] = {"loi": "%s: %s" % (type(e).__name__, str(e)[:160])}
    ra = {"trang_thai": tt, "ly_do": ly, "ma": ma, "khung": khung, "doan": "niem_phong",
          "spec": s, "quan_tri": qt, **bang, "nhan": nhan, "la_tong_hop": NDL.la_tong_hop(ma),
          "goi_ten_dung": ("DAT o day = CO LAI VA maxDD < %.0f%% o don bay chot truoc, tren du "
                           "lieu chua tung dung toi - canh bac co ky vong duong do duoc, chua "
                           "phai chan ly. Buoc tiep: MT5 tester (xuat_mq5) roi demo." % (DD_TRAN * 100))}
    with ST.ket_noi() as cn:
        cn.execute("INSERT INTO niem_phong(luc,van_tay,gt_id,ma,khung,spec,ket_qua,trang_thai) "
                   "VALUES(?,?,?,?,?,?,?,?)",
                   (ST.bay_gio(), vt, int(gt_id), ma, khung, ST._json({"spec": s, "quan_tri": qt}),
                    ST._json(ra), tt))
    ra["tn_id"] = ST.ghi_thi_nghiem("niem_phong", {"spec": s, "quan_tri": qt}, ra, tt, vt, ma, khung,
                                    "niem_phong", gt_id=int(gt_id), so_phep_thu=1,
                                    giay=time.time() - t0, vong_id=vong_id,
                                    tom_tat="NIEM PHONG " + _tom_tat(bang, s, qt) + " -> " + tt)
    ST.cap_nhat_gia_thuyet(int(gt_id), trang_thai="XAC_NHAN" if tt == "DAT" else
                           ("TRUOT_NIEM_PHONG" if tt == "AM" else None),
                           ket_luan="niem phong %s/%s: %s" % (ma, khung, ly))
    return ra


# ---------------------------------------------------------------- LUOI
def danh_gia_luoi(ma: str, khung: str, tham_so: dict | None = None, doan: str = "kham_pha",
                  von: float = 10000.0, gt_id: int | None = None,
                  vong_id: int | None = None) -> dict:
    """He LUOI (khong can tin hieu vao) qua `nhan/luoi.py` - ho quan tri lenh ra tien nhat lab.

    Ket qua tot nhat cua lab (AUDCAD luoi hai chieu CO TIA LENH, holdout +13,26%/nam
    DD -3,5%) den tu engine nay. Cong cu nay cho nha nghien cuu di tiep mach do trong
    so tay, voi ky luat doan nhu moi he khac.

    GIOI HAN THAT, khong giau: `luoi._mot_ro` GHIM phi qua dem AUDCAD (mua -0,263%/nam,
    ban +3,853%/nam) va coi point = 1e-5. Ma khac -> CHUA_DO_DUOC cho toi khi luoi.py
    nhan mo hinh chi phi. Chuoi TONG_HOP chi de kiem duong ong.

    Tieu chi chu du an 25/09 ("chi can co lai va maxdd duoi 80%", martingale/DCA/luoi deu
    duoc): DAT = co lai sau phi va khong chay tai khoan o lot dang thu. Lai lo cua luoi
    TUYEN TINH theo lot (moi lot nhan cung he so), nen duong von o he so lot k la
    von + k*(equity - von) - he so lot cham tran 80% tim CHINH XAC bang chia doi tren duong
    equity (co lo treo), khong nhan tuyen tinh DD. Tra kem `lo_treo_o_tran_pct_von`.
    """
    from dataclasses import fields as _fields
    from nhan import luoi as LU
    if doan not in NDL.DOAN_MO:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "doan chi duoc la kham_pha/xac_nhan"}
    ma, khung = str(ma).upper(), str(khung).upper()
    if not (NDL.la_tong_hop(ma) or "AUDCAD" in ma):
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "luoi.py dang GHIM phi qua dem + point cua AUDCAD; %s can mo hinh chi phi "
                         "rieng truoc (viec 8.2 trong tai_lieu/NHA_NGHIEN_CUU.md)" % ma}
    ts = dict(tham_so or {})
    hop = {f.name for f in _fields(LU.ThamSo)}
    la = [k for k in ts if k not in hop]
    if la:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "tham so luoi khong biet %s (co: %s)"
                % (la, ", ".join(sorted(hop)))}
    if ts.get("kieu_lot", "phang") != "phang":
        ts_canh = ["kieu_lot != phang: lam tron lot nho lam lai lo lech khoi tuyen tinh - he so "
                   "lot o tran chi la xap xi"]
    else:
        ts_canh = []
    vt = ST.van_tay("luoi", ma, khung, doan, ts, von)
    cu = ST.da_thu(vt)
    if cu and cu.get("ket_qua"):
        return dict(cu["ket_qua"], tu_so_tay="luoi %s da chay y het" % cu["id"])
    t0 = time.time()
    try:
        pre, a = NDL.cat_doan(NDL.nap(ma, khung), doan)
        seg = pre.iloc[a:]
        kq = LU.chay(seg, LU.ThamSo(**ts), float(von))
        cs = LU.chi_so(kq, float(von))
        moc = _moc(ma, khung, doan, seg, NDL.chi_phi(ma, pre))
    except Exception as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "%s: %s" % (type(e).__name__, str(e)[:200])}
    dd = abs(float(cs["maxdd_pct"]))
    k_tran = None if kq.chay else _he_so_lot_tai_tran(np.asarray(kq.duong_equity, float), float(von))
    ln = float(cs["loi_suat_nam_pct"])
    tien = {"co_lai": bool(ln > 0 and not kq.chay), "loi_suat_nam_pct": round(ln, 2),
            "maxdd_pct": round(-dd, 2),
            "he_so_lot_tai_tran": round(k_tran, 3) if k_tran else None,
            "loi_suat_o_tran_pct": round(ln * k_tran, 2) if k_tran else None,
            "lo_treo_o_tran_pct_von": (round(cs["lo_treo_dinh_pct_von"] * k_tran, 2)
                                       if k_tran else None),
            "moc_duoi_tran_pct": round(moc * 100, 2), "tran_dd_pct": round(DD_TRAN * 100, 1)}
    tien["hon_moc_pct"] = (round(tien["loi_suat_o_tran_pct"] - tien["moc_duoi_tran_pct"], 2)
                           if tien["loi_suat_o_tran_pct"] is not None else None)
    lenh = {"so_lenh": int(kq.so_lenh), "so_ro": int(kq.so_ro), "lenh_moi_nam": round(cs["lenh_nam"], 1),
            "tang_max": int(kq.tang_max)}
    nhan = []
    if dd >= DD_TRAN * 100:
        nhan.append("o lot dang thu maxDD %.1f%% >= %.0f%%: giam lot x%s" % (
            dd, DD_TRAN * 100, round(k_tran, 3) if k_tran else "?"))
    if tien["co_lai"] and tien["hon_moc_pct"] is not None and tien["hon_moc_pct"] <= 0:
        nhan.append("KHONG hon moc (%s%%/nam o cung tran DD) - beta, chua phai he"
                    % tien["moc_duoi_tran_pct"])
    if kq.chay:
        tt, ly = "AM", ("CHAY TAI KHOAN o bar %s voi von %.0f o lot dang thu - giam lot/tang von "
                        "roi thu lai (lai lo tuyen tinh theo lot)" % (kq.bar_chay, von))
    elif kq.so_lenh < LENH_TOI_THIEU:
        tt, ly = "CHUA_DO_DUOC", "chi %d lenh" % kq.so_lenh
    elif ln > 0:
        tt, ly = "DAT", ("co lai %+.2f%%/nam, maxDD %.1f%% o lot dang thu; o tran DD %.0f%%: lot x%s "
                         "-> %s%%/nam" % (ln, dd, DD_TRAN * 100, tien["he_so_lot_tai_tran"],
                                          tien["loi_suat_o_tran_pct"]))
    else:
        tt, ly = "AM", "khong co lai sau phi: %.2f%%/nam, maxDD %.1f%%" % (ln, dd)
    ra = {"trang_thai": tt, "ly_do": ly, "ma": ma, "khung": khung, "doan": doan, "tham_so": ts,
          "von": von, "tien": tien, "lenh": lenh,
          "chi_so_luoi": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in cs.items()},
          "nhan_canh_bao": nhan,
          "canh_bao": ts_canh + (["chuoi TONG_HOP: phi qua dem AUDCAD ap len chuoi gia - chi kiem "
                                  "duong ong"] if NDL.la_tong_hop(ma) else [])}
    ra["tn_id"] = ST.ghi_thi_nghiem("luoi", {"tham_so": ts, "von": von}, ra, tt, vt, ma, khung, doan,
                                    gt_id=gt_id, so_phep_thu=1 if doan == "kham_pha" else 0,
                                    giay=time.time() - t0, vong_id=vong_id,
                                    tom_tat="luoi %s: %s" % (json.dumps(ts, sort_keys=True)[:120], ly))
    return ra


def _he_so_lot_tai_tran(equity: np.ndarray, von: float, dd_tran: float = DD_TRAN,
                        k_toi_da: float = 1000.0) -> float | None:
    """He so lot k de maxDD cua duong von + k*(equity - von) cham (duoi) tran. None = khong tinh duoc.

    DD tang theo k (moi cap dinh/day: k*d/(von + k*P) tang theo k), nen chia doi dung.
    """
    e = np.asarray(equity, float)
    if len(e) < 2 or not np.all(np.isfinite(e)) or von <= 0:
        return None
    muc = float(dd_tran) - 1e-3

    def dd(k: float) -> float:
        v = von + k * (e - von)
        if np.any(v <= 0):
            return 1.0
        return VL._sut_giam(v)

    if dd(k_toi_da) < muc:
        return k_toi_da
    lo, hi = 0.0, k_toi_da
    for _ in range(80):
        giua = 0.5 * (lo + hi)
        if dd(giua) >= muc:
            hi = giua
        else:
            lo = giua
    return lo if lo > 0 else None


# ------------------------------------------------------------ DANH MUC
def ghep_danh_muc(chan: list[dict], doan: str = "kham_pha", vong_id: int | None = None) -> dict:
    """Ghep nhieu he (chan) cung RUI RO (nghich dao bien dong) -> tuong quan + tien cua ca ro.

    So bang CUNG mot phep voi tung he: muc ra tien tot nhat voi maxDD duoi tran chu du an.
    """
    if doan not in NDL.DOAN_MO:
        raise LoiKhaiBao("danh muc chi tren kham_pha/xac_nhan")
    if not chan or len(chan) < 2:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "can it nhat 2 chan"}
    chuoi, ten, tho = {}, [], {}
    for i, c in enumerate(chan[:8]):
        try:
            run = chay_he(c["ma"], c["khung"], c["spec"], c.get("quan_tri"), doan)
        except Exception as e:
            return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "chan %d: %s" % (i, str(e)[:160])}
        k = "%d:%s/%s:%s" % (i, run["ma"], run["khung"], run["spec"]["ten"][:24])
        idx = pd.DatetimeIndex(run["df"].index).normalize()
        chuoi[k] = pd.Series(np.asarray(run["kq"].loi, float), index=idx).groupby(level=0).sum()
        tho[k] = pd.Series(np.asarray(run["kq"].loi_tho, float), index=idx).groupby(level=0).sum()
        ten.append(k)
    R = pd.DataFrame(chuoi).fillna(0.0)
    RT = pd.DataFrame(tho).fillna(0.0)
    sd = R.std().replace(0, np.nan)
    w = (1.0 / sd) / (1.0 / sd).sum()
    p = (R * w).sum(axis=1)
    pt = (RT * w).sum(axis=1)
    so_nam = max((R.index[-1] - R.index[0]).days / 365.25, 1e-9)
    q = tien_duoi_tran(pt.to_numpy(), np.maximum(pt.to_numpy() - p.to_numpy(), 0), so_nam)
    tung = {}
    for k in ten:
        qk = tien_duoi_tran(RT[k].to_numpy(), np.maximum(RT[k].to_numpy() - R[k].to_numpy(), 0),
                            so_nam)
        tung[k] = _pct(qk["cagr"]) if qk["co_lai"] else None
    tq = R.corr().round(3)
    tot_don = max([v for v in tung.values() if v is not None] or [0.0])
    cagr = _pct(q["cagr"]) if q["co_lai"] else None
    tt = "DAT" if cagr is not None and cagr > tot_don else "AM"
    ra = {"trang_thai": tt, "doan": doan, "trong_so": {k: round(float(v), 3) for k, v in w.items()},
          "cagr_duoi_tran_danh_muc_pct": cagr, "don_bay_danh_muc": (round(q["don_bay"], 3)
                                                                   if q["don_bay"] else None),
          "cagr_duoi_tran_tung_chan_pct": tung,
          "tuong_quan_ngay": {k: tq[k].to_dict() for k in tq.columns},
          "doc": "DAT = ro danh muc CO LAI va ra tien hon chan tot nhat, cung tran maxDD %.0f%% - "
                 "tuong quan thap dang lam viec. Tuong quan > 0,5 thi ghep chi la nhan doi rui "
                 "ro." % (DD_TRAN * 100)}
    vt = ST.van_tay("danh_muc", doan, [(c["ma"], c["khung"], c["spec"].get("vao"), c.get("quan_tri"))
                                       for c in chan[:8]])
    ra["tn_id"] = ST.ghi_thi_nghiem("danh_muc", {"chan": chan[:8]}, ra, tt, vt, "", "", doan,
                                    so_phep_thu=1, vong_id=vong_id,
                                    tom_tat="danh muc %d chan: %s%% vs chan tot nhat %s%%"
                                            % (len(ten), cagr, tot_don))
    return ra


if __name__ == "__main__":
    import tempfile
    ST.DB = Path(tempfile.mkdtemp()) / "nc.db"
    spec = {"ten": "mua_sau_3_bar_giam", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 5,
            "co_che": "Ban thao sau ba bar giam lien tiep tao gia re tam thoi; nguoi mua "
                      "cung cap thanh khoan duoc tra bang cu hoi.",
            "vao": [{"trai": {"chi_bao": "doi_pct", "cua": {"chi_bao": "gia", "cot": "close"}, "n": 3},
                     "phep": "<", "phai": {"hang": -0.006}}]}
    for ma in ("TONG_HOP_LOC_1", "TONG_HOP_NHIEU_1"):
        t0 = time.time()
        r = danh_gia(ma, "H4", spec)
        print(ma, r["trang_thai"], r["ly_do"], "%.1fs" % (time.time() - t0))
        t0 = time.time()
        m = mo_xe(ma, "H4", spec, so_null=100)
        print("  mo xe", m["trang_thai"], "%.1fs" % (time.time() - t0), m.get("null"))
        for l in m.get("luat_loc", [])[:3]:
            print("    ", l["dieu_kien"], "giu", l["giu_lai"], "t", l["t_goc"], "->", l["t_sau_loc"],
                  "p", l["p_null"])
        if m.get("luat_loc"):
            v = danh_gia(ma, "H4", m["luat_loc"][0]["spec_de_xuat"], doan="xac_nhan")
            g = danh_gia(ma, "H4", spec, doan="xac_nhan")
            print("  xac nhan: goc", g["tien"]["cagr_duoi_tran_pct"], g["lenh"].get("ky_vong_bps"),
                  "| loc", v["tien"]["cagr_duoi_tran_pct"], v["lenh"].get("ky_vong_bps"),
                  v["trang_thai"])
