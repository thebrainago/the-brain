# -*- coding: utf-8 -*-
"""hieu_chuan_luoi.py - HIEU CHUAN engine luoi (`luoi.py`) voi MT5 tester: CUNG cua so, CUNG tham so, hai con so canh nhau.

Vi sao co (04/10/2026): moi so lieu luoi cua lab (AUDCAD luoi co tia lenh, +13%/nam...) den tu `luoi.py`, ma engine CHUA tung doi chieu
voi tester o ma nao. Phep do dau tien o may nha (tn5: lot 0,04 cong lot, he so buoc 1,2, tia lenh, AUDCAD M15 kham_pha) cho tester
-3,24%/nam, DD 59,8% (2.828 lenh, 2.680 SELL / 148 BUY, mot ro ket 33.191 gio) so voi engine +33,8%/nam, DD 39% (6.584 lenh). Khong ai
biet CAI GI lech: tia lenh dong o gia tot nhat cua bar, chuoi gia that co xu huong, tick sinh tu M1, hay tien bao gia (CAD) khac tien tai
khoan (USD)? Day la CONG CU DO - khong phai ket luan.

Mot lan goi = mot dong so tay (`hieu_chuan_luoi`, `doan="hieu_chuan"`, `so_phep_thu=0`: KHONG tieu phep thu, khong vao "thi nghiem tot nhat"):
  1. NUA TESTER. `ea_tho.lap_lenh(cua_so_tay=...)` -> tester chay `ea_LuoiDayDu.mq5` (input lay tu `luoi.ThamSo` qua
     `ea_gia_lap.tham_so_ea_tu_luoi`, khong bo sot truong nao) tren cua so tay NAM TRONG doan kham_pha da dong bang -> bao cao -> bang
     lenh (`lenh_tester`). Nua nay CHAM (5-30 phut) nen luu cache rieng (`hieu_chuan_tester`): sua engine roi so lai KHONG chay lai tester.
  2. NUA ENGINE. Chinh `luoi.chay_mang` tren CUNG cua so voi `ghi_lenh=True`; lai tinh luon khoan lo/lai CHUA CHOT luc het cua so (tester
     tu dong dong lenh o cuoi - nhan "end of test"). Lai tung lenh = gia dong - gia mo - spread (dung tung dong cua `_mot_ro`), kiem
     rang cong lai bang tong cua engine; lech thi canh bao va chi so tong, bo bang theo ky.
  3. SO. lai %/nam, maxDD (equity tuong doi), so lenh MO, BUY/SELL, lenh giu lau nhat, do sau luoi, swap + lai theo QUY (thang neu cua so
     < 18 thang) kem KY LECH DAU TIEN. KHOP (DAT) = ca ba trong dung sai; LECH (AM) = lech cho nao, kem canh bao chan doan.

TIEN BAO GIA <> TIEN TAI KHOAN: engine tinh bang dong BAO GIA (AUDCAD -> CAD) con tester tra tien tai khoan (USD). He so quy doi
f = don vi bao gia / 1 don vi tai khoan, uoc luong TU CHINH deal tester: median(chieu*(gia_dong - gia_mo)*lot*hop_dong / loi). Dung hop dong
cua engine nen sai khac hop dong that tu trieu (chi quan trong ty so engine / tester cho cung 1 lenh). Engine chay voi von = von*f va moi
con so lai chia f. Ty gia troi nhe trong nhieu nam (CAD/USD +-10%): sai so nay van con, dang trong `he_so_quy_doi` (p25..p75).

KHONG LAM GI VOI doan xac_nhan / niem_phong: cua so tay chi cho kham_pha va nam trong doan da dong bang (kiem bang `ea_tho.ke_hoach`),
`nhan_ket_qua` cua `ea_tho` tu choi lenh nay - ket qua o day khong the bi ghi nham thanh ket qua cua mot gia thuyet.
Loi ha tang (tester khong ra bao cao, log hong, cua so bao cao lech, du lieu lab thieu) -> `CHUA_DO_DUOC`, KHONG ghi so tay.

Dung (nc): b nc cc hieu_chuan_luoi '{"ma":"AUDCAD","khung":"M15","tu":"2018-01-02","den":"2019-12-31","tham_so":{...}}'
`chi_engine=true`: khong goi tester; co nua tester trong cache thi van so (sau khi sua engine), khong co thi chi in so engine.

KET QUA DAY DU RA TEP: bo chay don o may nha (`qwen/cau_git.chay_don`) chi mang ve 25 dong cuoi cua dau ra + cac bao cao nho (md / json,
<= 40.000 ky tu) moi ra trong `reports/`; mot ket qua hieu chuan dai ~200 dong nen cloud chi doc duoc phan duoi. Moi lan chay vi vay ghi
`reports/hieu_chuan/<ma>_<khung>_<tu>_<den>_<van tay tester>_e<phien ban engine>.json` (day du, <= 38.000 ky tu) va tra duong dan o khoa
`bao_cao` (cuoi dau ra) - day la duong DUY NHAT dua ket qua dai toi cloud qua `b cau`.
"""
from __future__ import annotations

import dataclasses
import json
import math
import re
import time
from datetime import date, datetime

import numpy as np
import pandas as pd

from nhan import bao_cao_mt5 as BC
from nhan import ea_gia_lap as G
from nhan import ea_tho as E
from nhan import lenh_tester as LT
from nhan import luoi as LU
from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN

LOAI_TESTER = "hieu_chuan_tester"
LOAI_SO_SANH = "hieu_chuan_luoi"
DOAN = "hieu_chuan"                    # doan rieng: dem_phep_thu / phep_thu_theo_ma / thi_nghiem_tot_nhat khong bao gio thay no
PHIEN_BAN = "1"                        # doi khi doi CACH DOC tester / cach tinh nua tester -> mat cache nua tester (co y)
EA_MAC_DINH = E.LAB / "ea_LuoiDayDu.mq5"
THU_MUC = E.LAB / "reports" / "hieu_chuan"
TEP_TOI_DA = 38_000                    # bo chay don chi mang ve tep .md/.json <= 40.000 ky tu (qwen/cau_git.TEP_TOI_DA)
MODEL_MAC_DINH = 0                     # Model 0 = moi tick sinh tu M1; Model 1 noi doi khi TP < 2 lan bien do M1 (CLAUDE.md)
NGAY_TOI_THIEU = 14
LENH_TOI_THIEU = 5
CUA_SO_THANG_NGAY = 540                # cua so < 18 thang: so theo thang, khong thi theo quy
#: dung sai (tuong doi, tuyet doi): |engine - tester| <= max(tuong doi * |tester|, tuyet doi)
DUNG_SAI = {"lai": (0.10, 1.0), "dd": (0.25, 2.0), "lenh": (0.15, 3.0)}
KY_LECH = (0.30, 0.25)                 # ky "lech" = chenh > max(30% so lon hon, 0,25 diem phan tram von)


# ============================================================ 1. DAU VAO
def _ngay(s) -> date:
    if isinstance(s, datetime):
        return s.date()
    if isinstance(s, date):
        return s
    return datetime.strptime(str(s).strip()[:10].replace(".", "-").replace("/", "-"), "%Y-%m-%d").date()


def _ts_ngay(chuoi: str) -> pd.Timestamp:
    return pd.Timestamp(str(chuoi).replace(".", "-"))


def chuan_cua_so(ma: str, khung: str, tu, den, cfg: dict) -> tuple[dict | None, str | None]:
    """Cua so tay -> ({tu, den, ngay} dang MT5 YYYY.MM.DD, None) hoac (None, ly do). PHAI nam trong doan kham_pha da dong bang."""
    try:
        d0, d1 = _ngay(tu), _ngay(den)
    except ValueError as e:
        return None, "ngay khong doc duoc (%s): dung YYYY-MM-DD hoac YYYY.MM.DD" % str(e)[:80]
    ngay = (d1 - d0).days + 1
    if ngay < NGAY_TOI_THIEU:
        return None, "cua so %d ngay < %d ngay: qua ngan de so sanh" % (max(ngay, 0), NGAY_TOI_THIEU)
    kh = E.ke_hoach(ma, khung, "kham_pha", dict(cfg, tick_tu=None))
    if "tu" not in kh:
        return None, kh.get("ly_do") or "chua co doan kham_pha da dong bang"
    k0, k1 = E._ngay_bc(kh["tu"]), E._ngay_bc(kh["den"])
    if d0 < k0 or d1 > k1:
        return None, ("cua so %s .. %s nam NGOAI doan kham_pha da dong bang (%s .. %s): hieu chuan chi chay tren doan kham_pha, "
                      "khong cham xac_nhan / niem_phong" % (d0, d1, kh["tu"], kh["den"]))
    return {"tu": d0.strftime("%Y.%m.%d"), "den": d1.strftime("%Y.%m.%d"), "ngay": ngay,
            "khoa_doan": kh.get("khoa_doan")}, None


def _kiem_dau_vao(khung, model, von, han_giay, tham_so) -> tuple[dict | None, str | None]:
    """-> ({ts: ThamSo, ts_ea: dict, von: float}, None) | (None, ly do)."""
    if str(khung).upper() not in E.KHUNG_HOP_LE:
        return None, "khung '%s' khong hop le (co %s)" % (khung, E.KHUNG_HOP_LE)
    if model not in (0, 1, 4):
        return None, "model phai la 0 (moi tick sinh tu M1), 1 (OHLC 1 phut) hoac 4 (tick that), nhan %r" % (model,)
    try:
        v = float(von)
    except (TypeError, ValueError):
        return None, "von phai la so"
    if not math.isfinite(v) or v < 100 or v != int(v):
        return None, "von phai la SO NGUYEN >= 100 (tester nhan von nguyen; so le se bi cat va hai ben lech von)"
    if han_giay is not None and (not isinstance(han_giay, (int, float)) or han_giay < 60):
        return None, "han_giay phai >= 60 giay"
    if tham_so is not None and not isinstance(tham_so, dict):
        return None, "tham_so phai la object {ten truong luoi.ThamSo: gia tri}"
    ts = dict(tham_so or {})
    ly = TN._loi_tham_so_luoi(ts)
    if ly:
        return None, ly
    try:
        obj = LU.ThamSo(**ts)
        ts_ea = G.tham_so_ea_tu_luoi(obj)
    except (TypeError, ValueError, KeyError) as e:
        return None, "tham_so khong hop le: %s" % str(e)[:200]
    return {"ts": obj, "ts_ea": ts_ea, "von": v}, None


# ============================================================ 2. QUY DOI TIEN
def uoc_he_so_quy_doi(g: pd.DataFrame, hop_dong: float, ghep_fifo_pct: float = 0.0) -> dict | None:
    """He so f = (don vi BAO GIA) / (1 don vi TIEN TAI KHOAN) uoc luong tu deal tester da dong.

    loi_tai_khoan = chieu*(gia_dong - gia_mo)*lot*hop_dong / f. Dung `hop_dong` cua engine: neu hop dong that khac thi f khac cung ty le
    va engine (cung dung hop_dong do) van ra dung lai tai khoan - chi ty so engine/tester moi dung cho viec so sanh.

    CACH 1 (uu tien, 'tong'): tong chieu*lot*(gia_dong - gia_mo)*hop_dong / tong loi. Moi vi the da dong co mat o ca hai ve nen tong nay
    KHONG doi khi ghep nham lenh vao voi lenh ra (mot hoan vi cac lenh cung lot khong doi tong) - quan trong vi cap cheo tien (AUDCAD
    tren tai khoan USD) co hop dong hieu dung troi theo ty gia, khong khop phuong trinh loi -> `lenh_tester` phai ghep FIFO. Can tong
    loi du lon so voi sai so lam tron 0,01 / deal (>= 50 lan) va cung dau voi tong gia.
    CACH 2 ('tung_lenh'): trung vi q/loi tung lenh (|loi| >= 1,0): CHI tin khi it lenh bi ghep FIFO (`ghep_fifo_pct` <= 0,2); cho p25 / p75
    (ty gia troi trong cua so). Tra {trung_vi, p25, p75 (None neu khong tin), so_mau, cach} hoac None."""
    if g is None or len(g) == 0:
        return None
    d = g[g["dong"].notna() & g["gia_dong"].notna() & g["loi"].notna()]
    if d.empty:
        return None
    q = (d["chieu"].astype(float) * (d["gia_dong"].astype(float) - d["gia_mo"].astype(float)) * d["lot"].astype(float)
         * float(hop_dong))
    loi = d["loi"].astype(float)
    n = int(len(d))
    tin_tung_lenh = ghep_fifo_pct <= 0.2
    p25 = p75 = tv_lenh = None
    ok = (loi.abs() >= 1.0) & (q * loi > 0)
    if tin_tung_lenh and int(ok.sum()) >= 20:
        f_i = (q[ok] / loi[ok]).to_numpy(float)
        p25, tv_lenh, p75 = (float(x) for x in np.percentile(f_i, [25, 50, 75]))
    q_tong, l_tong = float(q.sum()), float(loi.sum())
    if n >= 20 and abs(l_tong) >= 50.0 * 0.005 * math.sqrt(n) and q_tong * l_tong > 0:
        return {"trung_vi": round(q_tong / l_tong, 4), "p25": None if p25 is None else round(p25, 4),
                "p75": None if p75 is None else round(p75, 4), "so_mau": n, "cach": "tong"}
    if tv_lenh is not None:
        return {"trung_vi": round(tv_lenh, 4), "p25": round(p25, 4), "p75": round(p75, 4), "so_mau": int(ok.sum()), "cach": "tung_lenh"}
    return None


# ============================================================ 3. THONG KE LENH (dung chung hai nua)
def _nhan_ky(t, theo_thang: bool) -> np.ndarray:
    return np.asarray(pd.DatetimeIndex(t).to_period("M" if theo_thang else "Q").astype(str))


def thong_ke_lenh(b: pd.DataFrame, het: pd.Timestamp, von: float, theo_thang: bool) -> dict:
    """Bang lenh CHUNG (mo, dong [NaT = con mo luc het], chieu, lot, lai = da tru phi, CHUA tinh swap, swap [NaN neu khong biet])
    -> so dem + lai theo ky. Dung CHUNG cho tester va engine nen hai ben dung cung mot dinh nghia."""
    ra = {"so_lenh_mo": int(len(b)), "so_lenh_dong": 0, "lenh_mo_cuoi": 0, "buy": 0, "sell": 0, "giu_lau_nhat_gio": 0.0,
          "giu_lau_nhat_mo": None, "tang_max": 0, "do_sau_tb": 0.0, "do_sau_p90": 0, "lai_chua_swap": 0.0, "swap": None,
          "theo_ky": {}}
    if len(b) == 0:
        return ra
    mo = pd.DatetimeIndex(pd.to_datetime(b["mo"]))
    dong_goc = pd.to_datetime(b["dong"])
    con_mo = dong_goc.isna().to_numpy()
    dong = pd.DatetimeIndex(dong_goc.fillna(pd.Timestamp(het)))
    giu = (dong - mo).total_seconds().to_numpy(float) / 3600.0
    i = int(np.argmax(giu))
    ra.update(so_lenh_dong=int((~con_mo).sum()), lenh_mo_cuoi=int(con_mo.sum()),
              buy=int((b["chieu"].to_numpy() > 0).sum()), sell=int((b["chieu"].to_numpy() < 0).sum()),
              giu_lau_nhat_gio=round(float(giu[i]), 2), giu_lau_nhat_mo=str(mo[i]),
              lai_chua_swap=float(b["lai"].astype(float).sum()))
    sw = b["swap"].astype(float)
    if sw.notna().any():
        ra["swap"] = float(sw.fillna(0.0).sum())
    # do sau: so lenh dang mo dong thoi (lenh dong truoc lenh mo khi cung giay)
    t_ev = np.concatenate([mo.values.astype("datetime64[ns]").astype(np.int64),
                           dong.values.astype("datetime64[ns]").astype(np.int64)])
    d_ev = np.concatenate([np.ones(len(mo), dtype=np.int64), -np.ones(len(dong), dtype=np.int64)])
    o = np.lexsort((d_ev, t_ev))
    cum = np.cumsum(d_ev[o])
    ra["tang_max"] = int(cum.max())
    # do sau THEO THOI GIAN (so lenh dang mo thay doi theo su kien; khong can biet lenh nao dong lenh nao): trung binh + p90.
    # Mot ro ket nhieu nam lam p90 vot cao - bang chung KHONG phu thuoc cach ghep vao/ra.
    t_s = t_ev[o]
    dt = np.diff(t_s).astype(float)
    if dt.sum() > 0:
        sau = cum[:-1].astype(float)
        ra["do_sau_tb"] = round(float((sau * dt).sum() / dt.sum()), 3)
        theo_sau = np.argsort(sau, kind="stable")
        cw = np.cumsum(dt[theo_sau]) / dt.sum()
        ra["do_sau_p90"] = int(sau[theo_sau][int(np.searchsorted(cw, 0.9))])
    ky_ev = _nhan_ky(pd.to_datetime(t_ev[o]), theo_thang)
    tang_ky = pd.Series(cum).groupby(ky_ev).max()
    ky_dong = _nhan_ky(dong, theo_thang)
    g = pd.DataFrame({"ky": ky_dong, "lai": b["lai"].astype(float).to_numpy(), "n": 1}).groupby("ky").agg(
        lai=("lai", "sum"), n=("n", "sum"))
    for ky, r in g.iterrows():
        ra["theo_ky"][str(ky)] = {"lai_pct": round(float(r["lai"]) / von * 100.0, 4), "so_dong": int(r["n"]),
                                  "tang_max": int(tang_ky.get(ky, 0))}
    return ra


def bang_lenh_tester(g: pd.DataFrame) -> pd.DataFrame:
    """`lenh_tester.gop_theo_lenh` -> bang lenh chung. lai = loi + hoa hong (CHUA co swap)."""
    het_gio = g["cm_ra"].astype(str).str.lower().str.contains("end of test")
    return pd.DataFrame({
        "mo": pd.to_datetime(g["mo"]), "dong": pd.to_datetime(g["dong"]), "chieu": g["chieu"].astype(int),
        "lot": g["lot"].astype(float), "gia_mo": g["gia_mo"].astype(float), "gia_dong": g["gia_dong"].astype(float),
        "lai": g["loi"].astype(float).fillna(0.0) + g["hoa_hong"].astype(float).fillna(0.0),
        "swap": g["swap"].astype(float).fillna(0.0),
        "ly": np.where(het_gio, "het_gio", g["ly_do_ra"].astype(str))})


def bang_lenh_engine(kq, dl, f: float, mo_hinh: str) -> tuple[pd.DataFrame, dict]:
    """`KetQuaLuoi.lenh` (ghi_lenh=True) -> (bang lenh chung theo TIEN TAI KHOAN, kiem).

    lai_q = gia - spread: gia = chieu*(gia_ra - gia_mo)*lot*hop (lenh con mo: gia_ra = dong bar cuoi); spread = spread_gia[bar mo]*lot*hop
    (+ spread_gia[bar dong]*lot*hop cho lenh `tia` CHI o mo hinh `cuc_tri`: ban cu tru spread HAI lan o cap tia - hai dong `phi_sp +=`
    cua `_mot_ro` - con EA va tester chi tra MOT lan luc mo; `duong_di` tinh MOT lan nhu EA nen khong co khoan thu hai).
    `mo_hinh` = `ThamSo.khop_bar` cua lan chay (BAT BUOC, khong doan: tach sai mo hinh thi `kiem['khop']` sai o moi cau hinh co tia).
    `kiem` so cong tung lenh voi tong cua engine; khong khop -> `kiem['khop']=False` (engine doi ma ma cach tach nay chua doi theo)."""
    if mo_hinh not in LU.MO_HINH_BAR:
        raise ValueError("bang_lenh_engine: mo_hinh phai la mot trong %s, nhan %r" % (LU.MO_HINH_BAR, mo_hinh))
    cot = ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "lai", "swap", "ly"]
    L = kq.lenh
    if L is None or len(L) == 0:
        return pd.DataFrame(columns=cot), {"khop": True, "lai_treo_q": 0.0, "gross_dong": 0.0, "spread": 0.0}
    hop, idx = dl.qc.hop_dong, dl.idx
    mo = pd.DatetimeIndex(L["mo"])
    dong = pd.to_datetime(L["dong"])
    co = dong.notna().to_numpy()
    p_mo = np.asarray(idx.searchsorted(mo))
    p_dong = np.zeros(len(L), dtype=np.int64)
    if co.any():
        p_dong[co] = np.asarray(idx.searchsorted(pd.DatetimeIndex(dong[co])))
    chieu, lot = L["chieu"].to_numpy(float), L["lot"].to_numpy(float)
    gm, gd = L["gia_mo"].to_numpy(float), L["gia_dong"].to_numpy(float)
    gia_ra = np.where(co, gd, float(dl.cl[-1]))
    gross = chieu * (gia_ra - gm) * lot * hop
    tia = (L["ly_do"].to_numpy() == "tia") & co & (mo_hinh == "cuc_tri")
    sp_mo = dl.sp[p_mo] * lot * hop
    sp_dong = np.where(tia, dl.sp[p_dong] * lot * hop, 0.0)
    lai_q = gross - sp_mo - sp_dong
    gross_dong, spread = float(gross[co].sum()), float((sp_mo + sp_dong).sum())
    khop = (abs(gross_dong - kq.lai_gop) <= 1e-6 * max(1.0, abs(kq.lai_gop))
            and abs(spread - kq.phi_spread) <= 1e-6 * max(1.0, abs(kq.phi_spread)))
    kiem = {"khop": bool(khop), "gross_dong": gross_dong, "lai_gop_engine": float(kq.lai_gop), "spread": spread,
            "phi_spread_engine": float(kq.phi_spread), "lai_treo_q": float(gross[~co].sum())}
    b = pd.DataFrame({"mo": mo, "dong": dong.reset_index(drop=True).where(co), "chieu": L["chieu"].astype(int).to_numpy(),
                      "lot": lot, "gia_mo": gm, "gia_dong": np.where(co, gd, np.nan), "lai": lai_q / f, "swap": np.nan,
                      "ly": np.where(co, L["ly_do"].to_numpy(), "het_gio")})
    return b, kiem


# ============================================================ 4. NUA ENGINE
def nua_engine(ma: str, khung: str, cs: dict, ts: LU.ThamSo, von: float, f: float) -> dict:
    """Chay `luoi.chay_mang` tren cua so `cs` (tien tai khoan `von`, he so quy doi `f`). Loi -> {'loi': ly do} (ha tang)."""
    ma, khung = str(ma).upper(), str(khung).upper()
    chuan = LU.lop_quy_cach(ma) in ("audcad", "tong_hop")          # cung cach chon quy cach voi nc_thi_nghiem.danh_gia_luoi
    qc, ly = LU.quy_cach_cho(ma, None, None)
    if qc is None:
        return {"loi": ly}
    try:
        pre, a = NDL.cat_doan(NDL.nap(ma, khung), "kham_pha")
        if not chuan:
            cp = NDL.chi_phi(ma, pre)
            qc, ly = LU.quy_cach_cho(ma, float(np.nanmedian(pre.iloc[a:]["close"].to_numpy(float))), cp)
            if qc is None:
                return {"loi": ly}
        t0 = _ts_ngay(cs["tu"])
        t1 = _ts_ngay(cs["den"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        seg = pre.loc[t0:t1]
        if len(seg) < 50:
            return {"loi": "du lieu lab chi co %d bar trong cua so %s .. %s" % (len(seg), cs["tu"], cs["den"])}
        if seg.index[0] > t0 + pd.Timedelta(days=7) or seg.index[-1] < t1 - pd.Timedelta(days=7):
            return {"loi": "du lieu lab chi phu %s .. %s, khong phu cua so %s .. %s" % (
                seg.index[0].date(), seg.index[-1].date(), cs["tu"], cs["den"])}
        qc = dataclasses.replace(qc, von_quy_doi=float(f))
        dl = LU.chuan_bi(seg, qc)
        von_q = float(von) * float(f)
        kq = LU.chay_mang(dl, ts, von_q, ghi_lenh=True)
        chi = LU.chi_so(kq, von_q)
        b, kiem = bang_lenh_engine(kq, dl, f, ts.khop_bar)
    except Exception as e:                                   # noqa: BLE001 - mot chuoi ma hong khong duoc lam sap ca hang doi
        return {"loi": "%s: %s" % (type(e).__name__, str(e)[:200])}
    so_nam = cs["ngay"] / 365.25
    lai_tong = (float(kq.lai_rong) + kiem["lai_treo_q"]) / f
    tk = thong_ke_lenh(b, seg.index[-1], von, cs["ngay"] < CUA_SO_THANG_NGAY)
    tk["swap"] = -float(kq.phi_swap) / f
    kiem["lai_tong_khop"] = bool(abs(tk["lai_chua_swap"] + tk["swap"] - lai_tong) <= 1e-6 * max(1.0, abs(lai_tong)))
    # lai_nam_pct gom ca lai/lo CHUA CHOT luc het cua so (tester dong not o cuoi); lai_chot_nam_pct = chi phan da chot, cung
    # dinh nghia voi `luoi.chi_so` -> nhin duoc mot dong "ket qua luoi" cua lab lech bao nhieu so voi so cua tester
    return {"lai_tong": lai_tong, "lai_nam_pct": lai_tong / von / so_nam * 100.0, "dd_pct": abs(float(chi["maxdd_pct"])),
            "lai_chot_nam_pct": float(kq.lai_rong) / f / von / so_nam * 100.0,
            "chay": bool(kq.chay), "phi_spread": float(kq.phi_spread) / f, "lai_treo": kiem["lai_treo_q"] / f,
            "so_bar": int(len(seg)), "tu_bar": str(seg.index[0]), "den_bar": str(seg.index[-1]),
            "qc": {"ma": qc.ma, "pip": qc.pip, "hop_dong": qc.hop_dong, "von_quy_doi": float(f), "khoa": LU.khoa_quy_cach(qc)},
            "thong_ke": tk, "kiem": kiem}


# ============================================================ 5. NUA TESTER
def _dd_tester(bc: dict) -> dict:
    """Ba cach tinh DD cua bao cao; so sanh voi engine dung DD von TUONG DOI (cung kieu: dinh -> day / dinh)."""
    rel = (bc.get("dd_von_tuong_doi") or {}).get("pct")
    mx = (bc.get("dd_von_toi_da") or {}).get("pct")
    sd = (bc.get("dd_so_du_toi_da") or {}).get("pct")
    so_sanh = rel if rel is not None else (mx if mx is not None else bc.get("dd_pct"))
    return {"von_tuong_doi_pct": rel, "von_toi_da_pct": mx, "so_du_pct": sd, "dd_pct_cong": bc.get("dd_pct"),
            "so_sanh_pct": None if so_sanh is None else float(so_sanh)}


def _hong_ha_tang(bc: dict, cs: dict, log: str) -> str | None:
    """Cac kiem tra HA TANG cua `ea_tho.phan_quyet` (khong kiem lai/DD: day khong phai phep thu)."""
    log_hong = BC.dau_hieu_hong(log) if log else ""
    if log_hong:
        return log_hong
    if not bc.get("doc_duoc"):
        return "bao cao khong doc duoc: %s" % (bc.get("loi") or "thieu " + ", ".join(bc.get("thieu", [])))
    if bc.get("ticks") == 0 or bc.get("bars") == 0:
        return "bao cao ghi 0 tick/0 bar - tester khong co du lieu"
    ok, _n = E.kiem_cua_so(bc, cs)
    if ok is False:
        return ("cua so bao cao (%s .. %s) khong nam trong / khong phu du cua so lenh (%s .. %s)"
                % (bc.get("tu"), bc.get("den"), cs["tu"], cs["den"]))
    return None


def _luu_bang_lenh(b: pd.DataFrame, khoa: str) -> str | None:
    """Bang lenh tester ra reports/hieu_chuan/<khoa>_lenh.csv.gz de nguoi / AI mo ra xem; loi ghi -> khong sao (so tay van du)."""
    try:
        THU_MUC.mkdir(parents=True, exist_ok=True)
        p = THU_MUC / ("%s_lenh.csv.gz" % khoa[:16])
        b.to_csv(p, index=False, compression="gzip")
        try:
            return p.relative_to(E.LAB).as_posix()
        except ValueError:
            return str(p)
    except OSError:
        return None


def _luu_bao_cao(ra: dict, khoa: str) -> str | None:
    """Ket qua DAY DU ra `reports/hieu_chuan/<khoa>.json` (<= `TEP_TOI_DA` ky tu; qua dai thi thu gon `theo_ky`). Tra duong dan tuong doi
    so voi lab, hoac None khi khong ghi duoc (loi ghi -> khong sao: so tay + dau ra van du)."""
    try:
        thu = {k: v for k, v in ra.items() if k != "bao_cao"}
        s = json.dumps(thu, ensure_ascii=False, indent=1, default=str)
        if len(s) > TEP_TOI_DA:
            s = json.dumps(thu, ensure_ascii=False, separators=(",", ":"), default=str)
        ky = thu.get("theo_ky")
        while len(s) > TEP_TOI_DA and isinstance(ky, list) and len(ky) > 4:
            ky = ky[::2]                                      # bo bot ky xen ke: giu hinh dang, bo bot do dai
            thu["theo_ky"] = ky
            thu["ghi_chu_theo_ky"] = "da bo bot ky (xen ke) vi tep qua dai; so day du o dong so tay"
            s = json.dumps(thu, ensure_ascii=False, separators=(",", ":"), default=str)
        if len(s) > TEP_TOI_DA:
            return None
        THU_MUC.mkdir(parents=True, exist_ok=True)
        p = THU_MUC / ("%s.json" % re.sub(r"[^0-9A-Za-z_-]", "-", khoa)[:120])
        p.write_text(s, encoding="utf-8")
        try:
            return p.relative_to(E.LAB).as_posix()
        except ValueError:
            return str(p)
    except (OSError, TypeError, ValueError):
        return None


def _khoa_bao_cao(ma: str, khung: str, cs: dict, vt_t: str, khop_bar: str = LU.ThamSo.khop_bar) -> str:
    """Ten bao cao. Mo hinh bar KHAC mac dinh (`cuc_tri`, chi de do lai do lech cu) co duoi rieng: hai mo hinh chay cung o + cung
    nua tester khong duoc de len bao cao cua nhau."""
    khoa = "%s_%s_%s_%s_%s_e%s" % (ma, khung, cs["tu"], cs["den"], vt_t[:8], LU.PHIEN_BAN_ENGINE)
    return khoa if khop_bar == LU.ThamSo.khop_bar else "%s_%s" % (khoa, khop_bar)


def tester_trong_cache(vt_t: str) -> dict | None:
    """Dong so tay cua nua tester cung van tay (EA, cua so, tham so, model, von, don bay) -> {'id','tester'} | None."""
    cu = ST.da_thu(vt_t)
    kq = cu.get("ket_qua") if cu else None
    if isinstance(kq, dict) and isinstance(kq.get("tester"), dict):
        return {"id": cu["id"], "tester": kq["tester"]}
    return None


def nua_tester(lo: dict, d: dict, cfg2: dict, ts: LU.ThamSo, von: float, vt_t: str, vong_id: int | None,
               lam_lai: bool, hop_dong: float) -> dict:
    """Nua tester: cache -> (khong co) chay tester -> bao cao + bang lenh. Tra {'trang_thai':'DAT','tester':{...},'tn_id','tu_cache'}
    hoac CHUA_DO_DUOC (khong ghi so tay)."""
    cs, lenh = lo["lenh"]["cua_so"], lo["lenh"]
    cu = None if lam_lai else tester_trong_cache(vt_t)
    if cu:
        return {"trang_thai": "DAT", "tester": dict(cu["tester"]), "tn_id": cu["id"], "tu_cache": True, "van_tay": vt_t}
    t0 = time.time()
    r = (E.CHAY_TESTER or E._chay_that)(lenh, d, cfg2)
    if not r.get("xong"):
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True,
                "ly_do": "tester khong ra ket qua: %s" % (r.get("loi") or "khong ro")}
    bc = BC.doc_bao_cao(r["bao_cao"], cfg2.get("nhan_them"))
    ly = _hong_ha_tang(bc, cs, r.get("log", ""))
    if ly:
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True, "ly_do": ly}
    ok, _n = E.kiem_cua_so(bc, cs)
    cs_so = dict(cs)
    canh_bao: list[str] = []
    if ok:
        a, b_ = E._ngay_bc(bc.get("tu")), E._ngay_bc(bc.get("den"))
        if a is not None and b_ is not None and (a.strftime("%Y.%m.%d"), b_.strftime("%Y.%m.%d")) != (cs["tu"], cs["den"]):
            cs_so = {"tu": a.strftime("%Y.%m.%d"), "den": b_.strftime("%Y.%m.%d"), "ngay": (b_ - a).days + 1,
                     "khoa_doan": cs.get("khoa_doan")}
            canh_bao.append("bao cao tester chay %s .. %s (lenh xin %s .. %s): so sanh dung cua so cua bao cao"
                            % (cs_so["tu"], cs_so["den"], cs["tu"], cs["den"]))
    try:
        v = LT.vi_the_tu_tep(r["bao_cao"])
    except (ValueError, KeyError, OSError) as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True,
                "ly_do": "bao cao khong co bang Deals doc duoc (%s) - chua so duoc tung lenh" % str(e)[:160]}
    g = LT.gop_theo_lenh(v)
    if len(g) < LENH_TOI_THIEU:
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True,
                "ly_do": "bang Deals chi co %d lenh < %d: khong du de so" % (len(g), LENH_TOI_THIEU)}
    von_bc = float(bc.get("von") or von)
    if abs(von_bc - von) > 0.5:
        canh_bao.append("von bao cao %.0f khac von lenh %.0f: tester khong dung von da dat" % (von_bc, von))
    ghep = v.get("cach_ghep")
    fifo_pct = float((ghep.astype(str) == "fifo").mean()) if ghep is not None and len(ghep) else 0.0
    hs = uoc_he_so_quy_doi(g, hop_dong, fifo_pct)
    b = bang_lenh_tester(g)
    het = pd.to_datetime(b["dong"]).max()
    tk = thong_ke_lenh(b, het if pd.notna(het) else pd.Timestamp(g["mo"].max()), von_bc, cs_so["ngay"] < CUA_SO_THANG_NGAY)
    so_nam = cs_so["ngay"] / 365.25
    lai = float(bc["lai_rong"])
    if abs(tk["lai_chua_swap"] + (tk["swap"] or 0.0) - lai) > max(1.0, 0.002 * abs(lai)):
        canh_bao.append("tong tung lenh (%.2f) khac Total Net Profit cua bao cao (%.2f): ghep vi the co the sai (xem cach_ghep)"
                        % (tk["lai_chua_swap"] + (tk["swap"] or 0.0), lai))
    if fifo_pct > 0.2:
        canh_bao.append("%.0f%% lenh ghep vao/ra bang FIFO (khong khop phuong trinh loi - cap cheo tien thi hop dong hieu dung troi theo "
                        "ty gia): lenh giu lau nhat chi la xap xi; cac so TONG (lai, DD, so lenh, BUY/SELL, do sau theo thoi gian, "
                        "he so quy doi cach 'tong') khong bi anh huong" % (100.0 * fifo_pct))
    t = {"lai_rong": lai, "von": von_bc, "lai_nam_pct": lai / von_bc / so_nam * 100.0,
         "dd": _dd_tester(bc), "pf": bc.get("pf"), "so_lenh_bao_cao": bc.get("so_lenh"),
         "chat_luong_pct": bc.get("chat_luong_pct"), "bars": bc.get("bars"), "ticks": bc.get("ticks"),
         "model": int(lenh["model"]), "tu": bc.get("tu"), "den": bc.get("den"), "cua_so_so_sanh": cs_so,
         "thong_ke": tk, "he_so_quy_doi": hs, "ghep_fifo_pct": round(100.0 * fifo_pct, 1),
         "bang_lenh": _luu_bang_lenh(b, vt_t), "canh_bao": canh_bao,
         "giay": round(float(r.get("giay") or (time.time() - t0)), 1)}
    t["dd_pct_so_sanh"] = t["dd"]["so_sanh_pct"]
    if t["dd_pct_so_sanh"] is None:
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True, "ly_do": "bao cao khong ghi DD von - khong so duoc DD"}
    dau_vao = {"ea_sha": lenh["ea_sha"], "ea": lenh["ea_ten"], "tham_so": lenh["tham_so"], "tham_so_luoi": dataclasses.asdict(ts),
               "cua_so": cs, "model": lenh["model"], "von": lenh["von"], "don_bay": int(ts.don_bay),
               "symbol": lenh["viec"]["symbol"], "phien_ban": PHIEN_BAN}
    ra = {"trang_thai": "DAT", "ghi_chu": "DAT o day = DO DUOC (khong phai dat tieu chi lai): day la nua tester cua phep hieu chuan",
          "ma": lenh["ma"], "khung": lenh["khung"], "tester": t}
    tom = "tester %s %s/%s %s..%s: %+.2f%%/nam DD%.1f%% %d lenh" % (
        lenh["ea_ten"], lenh["ma"], lenh["khung"], cs_so["tu"], cs_so["den"], t["lai_nam_pct"], t["dd_pct_so_sanh"],
        tk["so_lenh_mo"])
    tn = ST.ghi_thi_nghiem(LOAI_TESTER, dau_vao, ra, "DAT", vt_t, lenh["ma"], lenh["khung"], DOAN, gt_id=None,
                           so_phep_thu=0, giay=t["giay"], vong_id=vong_id, tom_tat=tom)
    return {"trang_thai": "DAT", "tester": t, "tn_id": tn, "tu_cache": False, "van_tay": vt_t}


# ============================================================ 6. SO
def _gan(e: float, t: float, rel: float, ab: float) -> bool:
    return abs(e - t) <= max(rel * abs(t), ab)


def _ky_lech_dau_tien(tk_t: dict, tk_e: dict) -> tuple[list, dict | None]:
    cac = sorted(set(tk_t["theo_ky"]) | set(tk_e["theo_ky"]))
    bang, dau = [], None
    for ky in cac:
        a = tk_t["theo_ky"].get(ky, {})
        b = tk_e["theo_ky"].get(ky, {})
        row = {"ky": ky, "tester_pct": a.get("lai_pct", 0.0), "engine_pct": b.get("lai_pct", 0.0),
               "tester_dong": a.get("so_dong", 0), "engine_dong": b.get("so_dong", 0),
               "tester_tang": a.get("tang_max", 0), "engine_tang": b.get("tang_max", 0)}
        bang.append(row)
        if dau is None and abs(row["engine_pct"] - row["tester_pct"]) > max(
                KY_LECH[0] * max(abs(row["engine_pct"]), abs(row["tester_pct"])), KY_LECH[1]):
            dau = row
    return bang, dau


def _canh_bao_chan_doan(t: dict, e: dict, f_dung: float) -> list[str]:
    ra: list[str] = []
    tk, ek = t["thong_ke"], e["thong_ke"]
    if tk["giu_lau_nhat_gio"] >= 120 and tk["giu_lau_nhat_gio"] >= 3 * max(ek["giu_lau_nhat_gio"], 1.0):
        ra.append("tester co lenh giu %.0f gio (~%.0f ngay, mo %s) con engine toi da %.0f gio: ro ket ben tester ma engine khong thay"
                  % (tk["giu_lau_nhat_gio"], tk["giu_lau_nhat_gio"] / 24.0, str(tk["giu_lau_nhat_mo"])[:10], ek["giu_lau_nhat_gio"]))
    tong_t, tong_e = tk["buy"] + tk["sell"], ek["buy"] + ek["sell"]
    if tong_t >= 20 and tong_e >= 20 and abs(tk["sell"] / tong_t - ek["sell"] / tong_e) > 0.25:
        ra.append("ty le SELL: tester %.0f%% (%d/%d) engine %.0f%% (%d/%d): hai ben khong cung thay mot thi truong"
                  % (100.0 * tk["sell"] / tong_t, tk["sell"], tong_t, 100.0 * ek["sell"] / tong_e, ek["sell"], tong_e))
    if abs(tk["tang_max"] - ek["tang_max"]) >= 3:
        ra.append("do sau luoi lon nhat: tester %d lenh dong thoi, engine %d" % (tk["tang_max"], ek["tang_max"]))
    if t.get("chat_luong_pct") is not None and t["chat_luong_pct"] < 90:
        ra.append("chat luong lich su cua tester chi %.0f%% (Model %s): tick sinh tu M1 / gia dinh - lech co the do mo phong tick, "
                  "khong han la loi engine" % (t["chat_luong_pct"], t.get("model")))
    if abs(f_dung - 1.0) > 0.02:
        ra.append("tien bao gia khac tien tai khoan: he so quy doi %.4f (engine tinh bang tien bao gia, da chia he so nay)" % f_dung)
    if tk["do_sau_p90"] >= ek["do_sau_p90"] + 3 and tk["do_sau_tb"] >= 1.5 * max(ek["do_sau_tb"], 1.0):
        ra.append("tester o do sau cao hon nhieu theo THOI GIAN (trung binh %.1f p90 %d lenh, engine %.1f / %d): ro mo lau khong thoat"
                  " - dung ket qua nay (khong phu thuoc cach ghep vao/ra) de nghi ro ket" % (
                      tk["do_sau_tb"], tk["do_sau_p90"], ek["do_sau_tb"], ek["do_sau_p90"]))
    hs = t.get("he_so_quy_doi")
    if hs and hs.get("p25") is not None and hs.get("p75") is not None and hs["trung_vi"] > 0 \
            and (hs["p75"] - hs["p25"]) / hs["trung_vi"] > 0.05:
        ra.append("he so quy doi troi trong cua so (p25 %.3f .. p75 %.3f): ty gia doi nhieu, sai so tien <= ~%.0f%%"
                  % (hs["p25"], hs["p75"], 100.0 * (hs["p75"] - hs["p25"]) / hs["trung_vi"]))
    if e["chay"]:
        ra.append("engine bao CHAY tai khoan (stop-out) o von nay: moi con so engine sau diem do khong dang tin")
    if tk["so_lenh_mo"] < 30:
        ra.append("chi %d lenh o tester: mau nho, so sanh nhieu ngau nhien" % tk["so_lenh_mo"])
    if not (e["kiem"]["khop"] and e["kiem"].get("lai_tong_khop", True)):
        ra.append("cong lai/phi tung lenh cua engine KHONG khop tong (gop %.4f vs %.4f, spread %.4f vs %.4f): engine da doi ma ma "
                  "cach tach theo lenh chua doi - bang theo ky co the sai" % (
                      e["kiem"]["gross_dong"], e["kiem"]["lai_gop_engine"], e["kiem"]["spread"], e["kiem"]["phi_spread_engine"]))
    if tk["swap"] is not None and ek["swap"] is not None:
        so_nam = max(float(t["cua_so_so_sanh"]["ngay"]), 1.0) / 365.25
        sw_t, sw_e = 100.0 * tk["swap"] / t["von"] / so_nam, 100.0 * ek["swap"] / t["von"] / so_nam
        if not _gan(sw_e, sw_t, *DUNG_SAI["lai"]):
            ra.append("swap: tester %+.2f%%/nam engine %+.2f%%/nam (chenh dang ke: kiem swap_mode / swap 3 ngay cua ma)" % (sw_t, sw_e))
    return ra


def doi_chieu(t: dict, e: dict, f_dung: float) -> dict:
    """Hai nua -> ket luan KHOP / LECH + bang theo ky + canh bao chan doan. Thuan tuy (khong ghi gi)."""
    tl, el = float(t["lai_nam_pct"]), float(e["lai_nam_pct"])
    td, ed = float(t["dd_pct_so_sanh"]), float(e["dd_pct"])
    tn, en = int(t["thong_ke"]["so_lenh_mo"]), int(e["thong_ke"]["so_lenh_mo"])
    khop = {"lai": _gan(el, tl, *DUNG_SAI["lai"]) and not (el * tl < 0 and max(abs(el), abs(tl)) > 0.5),
            "dd": _gan(ed, td, *DUNG_SAI["dd"]), "lenh": _gan(float(en), float(tn), *DUNG_SAI["lenh"])}
    if e["chay"] and td < 90.0:
        khop["dd"] = False
    lech = []
    if not khop["lai"]:
        lech.append("lai (engine %+.2f%%/nam, tester %+.2f%%/nam)" % (el, tl))
    if not khop["dd"]:
        lech.append("maxDD (engine %.1f%%, tester %.1f%%)" % (ed, td))
    if not khop["lenh"]:
        lech.append("so lenh (engine %d, tester %d)" % (en, tn))
    ket = "KHOP" if not lech else "LECH"
    bang, dau = _ky_lech_dau_tien(t["thong_ke"], e["thong_ke"])
    ly = ("KHOP: engine %+.2f%%/nam, tester %+.2f%%/nam; maxDD %.1f%% vs %.1f%%; %d vs %d lenh"
          % (el, tl, ed, td, en, tn)) if ket == "KHOP" else ("LECH o " + "; ".join(lech))
    return {"ket_luan": ket, "ly_do": ly, "khop": khop,
            "lech": {"lai_nam_pp": round(el - tl, 3), "dd_pp": round(ed - td, 3), "lenh": en - tn,
                     "lenh_pct": round(100.0 * (en - tn) / max(tn, 1), 2)},
            "dung_sai": {k: list(v) for k, v in DUNG_SAI.items()}, "theo_ky": bang, "ky_lech_dau_tien": dau,
            "nhan": _canh_bao_chan_doan(t, e, f_dung)}


def _gon_engine(e: dict) -> dict:
    """Nua engine dua len ket qua: bo `kiem` dai dong, giu so can doc."""
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in e.items() if k not in ("kiem",)} | {
        "kiem_tung_lenh_khop": e["kiem"]["khop"]}


# ============================================================ 7. MOT LAN HIEU CHUAN
def hieu_chuan(ma: str, khung: str, tu, den, tham_so: dict | None = None, model: int = MODEL_MAC_DINH,
               von: float = 10000.0, ea: str | None = None, chi_engine: bool = False, von_quy_doi: float | None = None,
               han_giay: int | None = None, lam_lai_tester: bool = False, vong_id: int | None = None) -> dict:
    """Mot phep so engine <-> tester (xem docstring module). KHOP -> DAT, LECH -> AM, ha tang hong -> CHUA_DO_DUOC (khong ghi)."""
    t_dau = time.time()
    ma, khung = str(ma).upper(), str(khung).upper()
    dv, ly = _kiem_dau_vao(khung, model, von, han_giay, tham_so)
    if dv is None:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": ly}
    ts, ts_ea, von = dv["ts"], dv["ts_ea"], dv["von"]
    if von_quy_doi is not None and (not isinstance(von_quy_doi, (int, float)) or not (0.05 <= float(von_quy_doi) <= 20.0)):
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "von_quy_doi phai trong [0,05 .. 20] (don vi bao gia / 1 don vi tai khoan)"}
    cfg = E.cau_hinh()
    cfg2 = dict(cfg, model=int(model), von=int(von), don_bay=int(ts.don_bay), tick_tu=None)
    if han_giay:
        cfg2["han_giay"] = int(han_giay)
    cs, ly = chuan_cua_so(ma, khung, tu, den, cfg2)
    if cs is None:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": ly}
    try:
        d = E.doc_ea(str(ea or EA_MAC_DINH))
    except (KeyError, ValueError, OSError) as e:
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True, "ly_do": "khong doc duoc EA: %s" % str(e)[:200]}
    lo = E.lap_lenh(d, ma, khung, "kham_pha", ts_ea, None, cfg2, None, cua_so_tay=cs)
    if lo.get("trang_thai") != "SAN_SANG":
        return lo
    lenh = lo["lenh"]
    vt_t = ST.van_tay("hieu_chuan_tester", lenh["van_tay"], lenh["viec"]["symbol"], int(ts.don_bay), PHIEN_BAN)
    qc0, ly_qc = LU.quy_cach_cho(ma, None, None)
    if qc0 is None:                       # engine khong ho tro ma nay: dung TRUOC khi ton 5-30 phut tester
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": ly_qc}
    cache = None if lam_lai_tester else tester_trong_cache(vt_t)
    f0 = float(von_quy_doi) if von_quy_doi else float(qc0.von_quy_doi)
    # engine chay trong giay: chay thu NGAY de du lieu lab / quy cach thieu thi biet truoc, khong phai doi tester xong moi bao loi
    e0 = nua_engine(ma, khung, cs, ts, von, f0)
    if "loi" in e0:
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True, "ly_do": "engine khong chay duoc: %s" % e0["loi"]}
    if chi_engine and cache is None:
        r0 = {"trang_thai": "CHUA_DO_DUOC", "ma": ma, "khung": khung, "cua_so": cs, "tham_so": dataclasses.asdict(ts),
              "engine": _gon_engine(e0),
              "ly_do": "chua co nua tester trong so tay cho dung cua so + tham so + model + von nay: chi in so engine "
                       "(khong ghi so tay). Chay lai khong co chi_engine de goi tester (hoac cho don tester xong)",
              "nhan": ["he so quy doi dung: %.4f (%s)" % (f0, "do nguoi goi dat" if von_quy_doi else "mac dinh cua quy cach")]}
        bc0 = _luu_bao_cao(r0, _khoa_bao_cao(ma, khung, cs, vt_t, ts.khop_bar))
        if bc0:
            r0["bao_cao"] = bc0
        return r0
    th = nua_tester(lo, d, cfg2, ts, von, vt_t, vong_id, lam_lai_tester, qc0.hop_dong)
    if th.get("trang_thai") != "DAT":
        return th
    t = th["tester"]
    cs_so = t["cua_so_so_sanh"]
    hs = t.get("he_so_quy_doi")
    if von_quy_doi:
        f_dung, nguon_f = float(von_quy_doi), "do nguoi goi dat"
    elif hs:
        f_dung, nguon_f = float(hs["trung_vi"]), "uoc luong tu %d deal tester" % hs["so_mau"]
    else:
        f_dung, nguon_f = float(qc0.von_quy_doi), "MAC DINH cua quy cach (khong uoc luong duoc tu deal)"
    if (cs_so["tu"], cs_so["den"]) == (cs["tu"], cs["den"]) and abs(f_dung - f0) < 1e-12:
        e = e0
    else:
        e = nua_engine(ma, khung, cs_so, ts, von, f_dung)
        if "loi" in e:
            return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True, "tn_tester_id": th["tn_id"],
                    "ly_do": "engine khong chay duoc: %s" % e["loi"]}
    so = doi_chieu(t, e, f_dung)
    if hs and von_quy_doi and abs(float(von_quy_doi) / hs["trung_vi"] - 1.0) > 0.03:
        so["nhan"].append("von_quy_doi dat %.4f khac uoc luong tu deal tester %.4f (%.1f%%)" % (
            float(von_quy_doi), hs["trung_vi"], 100.0 * (float(von_quy_doi) / hs["trung_vi"] - 1.0)))
    if not hs and not von_quy_doi:
        so["nhan"].append("khong uoc luong duoc he so quy doi tien tu deal tester (can >= 20 lenh |loi| >= 1): dung %.4f %s"
                          % (f_dung, nguon_f))
    tt = "DAT" if so["ket_luan"] == "KHOP" else "AM"
    ra = {"trang_thai": tt, "ket_luan": so["ket_luan"], "ly_do": so["ly_do"], "ma": ma, "khung": khung, "cua_so": cs_so,
          "model": int(model), "von": von, "don_bay": int(ts.don_bay), "tham_so": dataclasses.asdict(ts),
          "he_so_quy_doi": {"dung": round(f_dung, 4), "nguon": nguon_f, "uoc_tu_deal": hs},
          "tester": {k: t[k] for k in ("lai_rong", "lai_nam_pct", "dd", "pf", "chat_luong_pct", "model", "giay", "thong_ke", "bang_lenh",
                                 "ghep_fifo_pct")},
          "engine": _gon_engine(e), "phien_ban_engine": LU.PHIEN_BAN_ENGINE, "tn_tester_id": th["tn_id"],
          "tester_tu_cache": bool(th["tu_cache"])}
    ra.update({k: so[k] for k in ("khop", "lech", "dung_sai", "theo_ky", "ky_lech_dau_tien", "nhan")})
    ra["nhan"] = list(t.get("canh_bao", [])) + ra["nhan"]
    vt_so = ST.van_tay("hieu_chuan_luoi", vt_t, LU.PHIEN_BAN_ENGINE, ts.khop_bar, round(f_dung, 4), e["qc"]["khoa"], DUNG_SAI, KY_LECH,
                       PHIEN_BAN)
    khoa_so = [round(e["lai_nam_pct"], 2), round(t["lai_nam_pct"], 2), round(e["dd_pct"], 2), round(t["dd_pct_so_sanh"], 2),
               int(e["thong_ke"]["so_lenh_mo"]), int(t["thong_ke"]["so_lenh_mo"])]
    ra["so_khoa"] = khoa_so
    cu_so = ST.da_thu(vt_so)
    if cu_so and isinstance(cu_so.get("ket_qua"), dict) and cu_so["ket_qua"].get("so_khoa") == khoa_so:
        ra["tn_id"], ra["tu_so_tay"] = cu_so["id"], "da ghi dong so tay %s (cung so)" % cu_so["id"]
        bc1 = _luu_bao_cao(ra, _khoa_bao_cao(ma, khung, cs_so, vt_t, ts.khop_bar))
        if bc1:
            ra["bao_cao"] = bc1
        return ra
    dau_vao = {"ma": ma, "khung": khung, "cua_so": cs_so, "model": int(model), "von": von, "don_bay": int(ts.don_bay),
               "tham_so": dataclasses.asdict(ts), "ea_sha": lenh["ea_sha"], "he_so_quy_doi": round(f_dung, 4),
               "phien_ban_engine": LU.PHIEN_BAN_ENGINE, "tn_tester_id": th["tn_id"]}
    tom = "%s %s/%s %s..%s: engine %+.2f%%/nam DD%.1f%% %d lenh | tester %+.2f%%/nam DD%.1f%% %d lenh -> %s" % (
        lenh["ea_ten"], ma, khung, cs_so["tu"], cs_so["den"], e["lai_nam_pct"], e["dd_pct"], e["thong_ke"]["so_lenh_mo"],
        t["lai_nam_pct"], t["dd_pct_so_sanh"], t["thong_ke"]["so_lenh_mo"], so["ket_luan"])
    ra["tn_id"] = ST.ghi_thi_nghiem(LOAI_SO_SANH, dau_vao, ra, tt, vt_so, ma, khung, DOAN, gt_id=None, so_phep_thu=0,
                                    giay=time.time() - t_dau, vong_id=vong_id, tom_tat=tom)
    bc2 = _luu_bao_cao(ra, _khoa_bao_cao(ma, khung, cs_so, vt_t, ts.khop_bar))
    if bc2:
        ra["bao_cao"] = bc2
    return ra
