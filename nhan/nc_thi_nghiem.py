# -*- coding: utf-8 -*-
"""nc_thi_nghiem.py - THI NGHIEM cua nha nghien cuu AI: chay he, quet, mo xe, xac nhan, mo niem phong.

Moi ham o day la MOT phep do ma nha nghien cuu (AI) goi qua `nc_cong_cu`. Ham
khong quyet dinh nghien cuu gi - AI quyet dinh. Ham chi lam dung ba viec:

1. **Do bang dung duong cua du an.** Tin hieu qua `ngu_phap` (khong nhin truoc),
   tien qua `mo_phong.chay` hoac `dap_quan_tri.dap` + `vao_lenh.tinh_tien`
   (phi tren GOP, phi qua dem bat doi xung), so voi moc bang
   `vao_lenh.quy_ve_dd` / `vao_lenh.moc_dd20` - **CAGR o cung sut giam 20%**
   so voi max(mua-giu, ban-giu, tien mat). Do la cau hoi tien cua LUAT SO 0,
   khong phai Sharpe.
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
from nhan import (dap_quan_tri as DQT, do_luong as DO, mo_phong as MP,
                  nc_dac_trung as DT, nc_du_lieu as NDL, nc_mo_xe as MX,
                  nc_so_tay as ST, ngu_phap as NP, vao_lenh as VL)

LENH_TOI_THIEU = 10               # duoi nay: CHUA_DO_DUOC o moi doan
LENH_TOI_THIEU_NIEM_PHONG = 20
MO_NIEM_PHONG_TOI_DA = 3          # moi dong gia thuyet
NHIN_XAC_NHAN_CANH_BAO = 6        # nhin doan xac nhan qua so lan nay -> canh bao
DD_MUC_TIEU = 0.20
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


def _moc(ma: str, khung: str, doan: str, seg: pd.DataFrame, cp) -> float:
    khoa = (ma, khung, doan, len(seg))
    if khoa not in _DEM_MOC:
        _DEM_MOC[khoa] = float(VL.moc_dd20(seg, cp, ma=ma, khung=khung))
    return _DEM_MOC[khoa]


def chi_so_he(run: dict) -> dict:
    """Bang so cua mot lan chay: chi so, lenh, TIEN o cung sut giam, theo nam, chi phi."""
    kq, seg, lenh, cp = run["kq"], run["df"], run["lenh"], run["cp"]
    cs = DO.chi_so(kq.loi, seg.index, kq.vi_the)
    so_nam = VL.so_nam_cua(seg)
    tk = MX.thong_ke_lenh(lenh["loi"].to_numpy(float) if len(lenh) else np.zeros(0))
    tk["lenh_moi_nam"] = round(tk.get("so_lenh", 0) / max(so_nam, 1e-9), 1)
    if len(lenh):
        tk["so_bar_giu_trung_vi"] = float(lenh["so_bar"].median())
    phi = np.maximum(np.asarray(kq.loi_tho, float) - np.asarray(kq.loi, float), 0.0)
    q = VL.quy_ve_dd(kq.loi_tho, phi, so_nam, dd_muc_tieu=DD_MUC_TIEU)
    moc = _moc(run["ma"], run["khung"], run["doan"], seg, cp)
    cagr20 = q.get("cagr")
    tien = {"cagr_dd20_pct": round(cagr20 * 100, 2) if cagr20 is not None else None,
            "moc_dd20_pct": round(moc * 100, 2),
            "hon_moc_pct": round((cagr20 - moc) * 100, 2) if cagr20 is not None else None,
            "don_bay_dd20": round(q["L"], 3) if q.get("L") else None,
            "cham_tran_don_bay": bool(q.get("cham_tran_L")), "chay_tai_khoan": bool(q.get("chet")),
            "y_nghia": "CAGR khi don bay dua sut giam ve 20%, tru moc max(mua-giu, ban-giu, "
                       "tien mat) cung quy ve 20% - cau hoi tien cua LUAT SO 0"}
    s = pd.Series(np.asarray(kq.loi, float), index=seg.index)
    nam = s.groupby(pd.DatetimeIndex(seg.index).year).sum()
    theo_nam = {str(int(k)): round(float(np.expm1(v)) * 100, 2) for k, v in nam.items()}
    tong_cp = kq.chi_phi_spread + kq.chi_phi_truot + kq.chi_phi_giu
    return {
        "chi_so": {k: cs.get(k) for k in ("cagr_pct", "sharpe", "calmar", "max_dd_pct", "pf",
                                          "so_nam", "phoi_nhiem")},
        "lenh": tk, "tien": tien, "kinh_te": tang_2_kinh_te(kq),
        "theo_nam_pct": theo_nam,
        "nam_duong": "%d/%d" % (sum(v > 0 for v in theo_nam.values()), len(theo_nam)),
        "chi_phi": {"tong_pct": round(tong_cp * 100, 3),
                    "qua_dem_pct": round(kq.chi_phi_giu * 100, 3),
                    "do_tin": getattr(cp, "do_tin", "?")},
        "canh_bao": list(dict.fromkeys(list(kq.canh_bao or [])[:4])),
    }


def tang_2_kinh_te(kq) -> dict:
    """TANG 2 KINH TE cua `cong.py` (chu du an, 18/09): chan martingale tra hinh va edge mong.

    Dung CHINH ham + nguong cua `cong` (config/nguong.json) de cong cua nha nghien cuu va
    cong chinh thuc khong the noi hai dieu khac nhau. Do 25/09: he yeu HOI_QUY_YEU hon moc
    o DD20 (158 lenh) nhung lai rong chi 2,9x chi phi spread - cong chinh thuc truot, cong
    nha nghien cuu (truoc khi co ham nay) cho DAT.
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
        return {"dat": bool(ok_rr and ok_sp),
                "rr_thuc_te": round(rr, 3) if np.isfinite(rr) else None, "rr_toi_thieu": rr_min,
                "lai_rong_tren_phi_spread": round(lai / sp, 2) if sp > 0 else None,
                "toi_thieu": sp_min,
                "ly_do": ([] if ok_rr else ["rr thuc te %.3f < %.2f (martingale tra hinh)" % (rr, rr_min)])
                + ([] if ok_sp else ["lai rong %.2fx chi phi spread < %.1fx (edge mong so voi phi)"
                                     % (lai / sp, sp_min)])}
    except Exception as e:     # khong tinh duoc -> khong chan, nhung noi ro
        return {"dat": True, "loi": "%s: %s" % (type(e).__name__, str(e)[:120])}


def _phan_quyet(bang: dict) -> tuple[str, str]:
    """DAT / AM / CHUA_DO_DUOC cho doan kham_pha / xac_nhan.

    DAT = hon moc o cung DD 20% VA ky vong duong VA qua tang 2 kinh te - dung cac chan
    cua cong niem phong, de ket qua giua duong khong hua hen dieu cong cuoi se bac.
    """
    n = (bang.get("lenh") or {}).get("so_lenh", 0)
    if n < LENH_TOI_THIEU:
        return "CHUA_DO_DUOC", "chi %d lenh < %d" % (n, LENH_TOI_THIEU)
    hm = (bang.get("tien") or {}).get("hon_moc_pct")
    kv = (bang.get("lenh") or {}).get("ky_vong_bps")
    if hm is None:
        return "CHUA_DO_DUOC", "khong quy ve duoc sut giam 20%"
    kt = bang.get("kinh_te") or {"dat": True}
    if hm > 0 and (kv or 0) > 0 and not kt.get("dat", True):
        return "AM", "hon moc %+.2f%%/nam nhung truot TANG 2 KINH TE: %s" % (
            hm, "; ".join(kt.get("ly_do") or []))
    if hm > 0 and (kv or 0) > 0:
        return "DAT", "hon moc %+.2f%%/nam o cung DD, ky vong %+.2f bps/lenh" % (hm, kv)
    return "AM", "hon moc %+.2f%%/nam, ky vong %+.2f bps/lenh" % (hm, kv or 0)


def _tom_tat(bang: dict, spec: dict, qt) -> str:
    l, t = bang.get("lenh") or {}, bang.get("tien") or {}
    return ("%s%s: hon moc %s%%/nam · %s lenh · kv %s bps · t %s · nam duong %s"
            % (spec.get("ten"), (" +qt" + json.dumps(qt, sort_keys=True)) if qt else "",
               t.get("hon_moc_pct"), l.get("so_lenh"), l.get("ky_vong_bps"),
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
            hm_kp = ((kp["ket_qua"].get("tien") or {}).get("hon_moc_pct"))
            ra["so_voi_kham_pha"] = {"hon_moc_kham_pha_pct": hm_kp,
                                     "hon_moc_xac_nhan_pct": ra["tien"]["hon_moc_pct"]}
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
            bang.append({"tham_so": ts, "hon_moc_pct": b["tien"]["hon_moc_pct"],
                         "cagr_dd20_pct": b["tien"]["cagr_dd20_pct"],
                         "ky_vong_bps": b["lenh"].get("ky_vong_bps"),
                         "so_lenh": b["lenh"].get("so_lenh", 0),
                         "sharpe": b["chi_so"].get("sharpe"), "nam_duong": b["nam_duong"]})
        except Exception as e:
            bang.append({"tham_so": ts, "loi": "%s: %s" % (type(e).__name__, str(e)[:120])})
    do_duoc = [r for r in bang if r.get("hon_moc_pct") is not None
               and (r.get("so_lenh") or 0) >= LENH_TOI_THIEU]
    ra: dict = {"luoi": luoi, "so_o": len(bang), "so_o_do_duoc": len(do_duoc)}
    if len(do_duoc) < max(3, len(bang) // 3):
        ra.update(trang_thai="CHUA_DO_DUOC", ly_do="chi %d/%d o do duoc (it lenh hoac loi)"
                  % (len(do_duoc), len(bang)), bang=bang[:10])
        tt = "CHUA_DO_DUOC"
    else:
        hm = np.array([r["hon_moc_pct"] for r in do_duoc], float)
        tot = max(do_duoc, key=lambda r: r["hon_moc_pct"])
        # hang xom cua o tot nhat: khac dung MOT tham so, mot buoc tren luoi
        buoc = {k: {v: i for i, v in enumerate(luoi[k])} for k in khoa}
        vi_tri_tot = {k: buoc[k][tot["tham_so"][k]] for k in khoa}
        xom = [r["hon_moc_pct"] for r in do_duoc
               if sum(abs(buoc[k][r["tham_so"][k]] - vi_tri_tot[k]) for k in khoa) == 1]
        ty_duong = float(np.mean(hm > 0))
        xom_tb = float(np.mean(xom)) if xom else None
        if ty_duong >= 0.6 and (xom_tb is None or xom_tb > 0):
            hinh = "CAO_NGUYEN"
        elif tot["hon_moc_pct"] > 0 and ty_duong < 0.3:
            hinh = "CAI_GAI"
        else:
            hinh = "HON_HOP"
        ra.update({
            "hinh_dang": hinh, "ty_le_o_hon_moc": round(ty_duong, 3),
            "hon_moc_trung_vi_pct": round(float(np.median(hm)), 2),
            "o_tot_nhat": tot, "hang_xom_tot_nhat_tb_pct": round(xom_tb, 2) if xom_tb is not None else None,
            "bang_top": sorted(do_duoc, key=lambda r: -r["hon_moc_pct"])[:8],
            "doc_dung": "Chon theo HINH DANG, khong theo o tot nhat: cuc dai cua %d o tren nhieu "
                        "cung dep. Cao nguyen = nhieu o lan can cung tot." % len(bang)})
        tt = "DAT" if (hinh == "CAO_NGUYEN" and tot["hon_moc_pct"] > 0) else "AM"
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
                      "khi p_null thap VA spec_de_xuat chay lai tren doan xac_nhan van hon moc.")
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
        moc = VL.moc_dd20(seg, cp, ma=ma, khung=khung)
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
          "mua_vu_t": mv, "moc_dd20_pct": round(moc * 100, 2) if moc is not None else None,
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

    Cong TIEN (chan): hon moc o cung sut giam 20% va ky vong duong, chi phi do duoc.
    Nhan (khong chan, LUAT SO 0): so phep thu da tieu, Sharpe giam phat, cong that
    `cong.xet` (placebo, alpha) chay voi `ghi_so=False` - khong tieu suat FDR.
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
    n = bang["lenh"].get("so_lenh", 0)
    hm = bang["tien"]["hon_moc_pct"]
    kv = bang["lenh"].get("ky_vong_bps") or 0
    do_tin = getattr(run["cp"], "do_tin", "KHAI")
    if n < LENH_TOI_THIEU_NIEM_PHONG:
        tt, ly = "CHUA_DO_DUOC", "chi %d lenh < %d tren doan niem phong" % (n, LENH_TOI_THIEU_NIEM_PHONG)
    elif do_tin == "KHAI":
        tt, ly = "CHUA_DO_DUOC", "chi phi KHAI (chua do) - khong bao gio DAT (luat chi phi)"
    elif hm is not None and hm > 0 and kv > 0 and not bang["kinh_te"].get("dat", True):
        tt, ly = "AM", "hon moc %+.2f%%/nam nhung truot TANG 2 KINH TE: %s" % (
            hm, "; ".join(bang["kinh_te"].get("ly_do") or []))
    elif hm is not None and hm > 0 and kv > 0:
        tt, ly = "DAT", "hon moc %+.2f%%/nam o cung DD 20%%, %d lenh, ky vong %+.2f bps" % (hm, n, kv)
    else:
        tt, ly = "AM", "hon moc %s%%/nam, ky vong %+.2f bps, %d lenh" % (hm, kv, n)
    pt_dong = ST.dem_phep_thu(gt_id=int(gt_id))
    pt_ma = ST.dem_phep_thu(ma=ma, khung=khung)
    nhan = {"so_phep_thu_dong_gia_thuyet": pt_dong, "so_phep_thu_tren_ma": pt_ma,
            "lan_mo_niem_phong_trong_dong": da_mo + 1,
            "sharpe_giam_phat": _sharpe_giam_phat(run["kq"].loi, max(pt_dong, 1))}
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
          "goi_ten_dung": ("DAT o day = CANH BAC CO KY VONG DUONG DO DUOC tren du lieu chua "
                           "tung dung toi. Buoc tiep: MT5 tester (xuat_mq5) roi demo.")}
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

    Tien o cung sut giam: luoi LOT PHANG co lai lo TUYEN TINH theo lot, nen quy ve DD 20%
    bang ti le 20/|maxDD| la dung cho lai - NHUNG lo treo va margin cung nhan theo, nen
    tra kem `lo_treo_o_dd20_pct_von` de AI thay diem margin call truoc khi nang lot.
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
        ts_canh = ["kieu_lot != phang: lai lo KHONG con tuyen tinh theo lot - quy ve DD20 chi la xap xi"]
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
    k20 = 20.0 / dd if dd > 1e-9 else None
    tien = {"loi_suat_nam_pct": round(float(cs["loi_suat_nam_pct"]), 2), "maxdd_pct": round(-dd, 2),
            "cagr_dd20_pct": round(cs["loi_suat_nam_pct"] * k20, 2) if k20 else None,
            "moc_dd20_pct": round(moc * 100, 2),
            "he_so_lot_dd20": round(k20, 3) if k20 else None,
            "lo_treo_o_dd20_pct_von": round(cs["lo_treo_dinh_pct_von"] * k20, 2) if k20 else None}
    tien["hon_moc_pct"] = (round(tien["cagr_dd20_pct"] - tien["moc_dd20_pct"], 2)
                           if tien["cagr_dd20_pct"] is not None else None)
    lenh = {"so_lenh": int(kq.so_lenh), "so_ro": int(kq.so_ro), "lenh_moi_nam": round(cs["lenh_nam"], 1),
            "tang_max": int(kq.tang_max)}
    if kq.chay:
        tt, ly = "AM", "CHAY TAI KHOAN o bar %s voi von %.0f" % (kq.bar_chay, von)
    elif kq.so_lenh < LENH_TOI_THIEU:
        tt, ly = "CHUA_DO_DUOC", "chi %d lenh" % kq.so_lenh
    elif tien["hon_moc_pct"] is not None and tien["hon_moc_pct"] > 0 and cs["loi_suat_nam_pct"] > 0:
        tt, ly = "DAT", "hon moc %+.2f%%/nam o cung DD 20%% (lot x%.2f)" % (tien["hon_moc_pct"], k20)
    else:
        tt, ly = "AM", "hon moc %s%%/nam, loi suat %.2f%%/nam" % (tien["hon_moc_pct"], cs["loi_suat_nam_pct"])
    ra = {"trang_thai": tt, "ly_do": ly, "ma": ma, "khung": khung, "doan": doan, "tham_so": ts,
          "von": von, "tien": tien, "lenh": lenh,
          "chi_so_luoi": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in cs.items()},
          "canh_bao": ts_canh + (["chuoi TONG_HOP: phi qua dem AUDCAD ap len chuoi gia - chi kiem "
                                  "duong ong"] if NDL.la_tong_hop(ma) else [])}
    ra["tn_id"] = ST.ghi_thi_nghiem("luoi", {"tham_so": ts, "von": von}, ra, tt, vt, ma, khung, doan,
                                    gt_id=gt_id, so_phep_thu=1 if doan == "kham_pha" else 0,
                                    giay=time.time() - t0, vong_id=vong_id,
                                    tom_tat="luoi %s: %s" % (json.dumps(ts, sort_keys=True)[:120], ly))
    return ra


# ------------------------------------------------------------ DANH MUC
def ghep_danh_muc(chan: list[dict], doan: str = "kham_pha", vong_id: int | None = None) -> dict:
    """Ghep nhieu he (chan) cung RUI RO (nghich dao bien dong) -> tuong quan + tien cua ca ro."""
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
    q = VL.quy_ve_dd(pt.to_numpy(), np.maximum(pt.to_numpy() - p.to_numpy(), 0), so_nam, DD_MUC_TIEU)
    tung = {}
    for k in ten:
        qk = VL.quy_ve_dd(RT[k].to_numpy(), np.maximum(RT[k].to_numpy() - R[k].to_numpy(), 0),
                          so_nam, DD_MUC_TIEU)
        tung[k] = round(qk["cagr"] * 100, 2) if qk.get("cagr") is not None else None
    tq = R.corr().round(3)
    tot_don = max([v for v in tung.values() if v is not None] or [0.0])
    cagr = round(q["cagr"] * 100, 2) if q.get("cagr") is not None else None
    tt = "DAT" if cagr is not None and cagr > tot_don else "AM"
    ra = {"trang_thai": tt, "doan": doan, "trong_so": {k: round(float(v), 3) for k, v in w.items()},
          "cagr_dd20_danh_muc_pct": cagr, "cagr_dd20_tung_chan_pct": tung,
          "tuong_quan_ngay": {k: tq[k].to_dict() for k in tq.columns},
          "doc": "DAT = ro danh muc o cung sut giam 20% lai hon chan tot nhat - tuong quan thap "
                 "dang lam viec. Tuong quan > 0,5 thi ghep chi la nhan doi rui ro."}
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
            print("  xac nhan: goc", g["tien"]["hon_moc_pct"], g["lenh"].get("ky_vong_bps"),
                  "| loc", v["tien"]["hon_moc_pct"], v["lenh"].get("ky_vong_bps"), v["trang_thai"])
