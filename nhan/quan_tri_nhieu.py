# -*- coding: utf-8 -*-
"""quan_tri_nhieu.py - QUAN TRI LENH voi NHIEU VI THE cung luc, chay bang Python.

## Lo hong nay va

So do goi quan li lenh la *"module quan trong trong toan bo he thong"*. Nhung
ban chay bang Python (`_quet_quan_tri_python.py`) chi lam duoc **6 tren 11 ho**,
va chinh no ghi ro vi sao:

    "Python chi lam duoc ho MOT VI THE (`dap_quan_tri.dap` mo mot vi the mot
     luc). Nam ho con lai (hedge, luoi_dca, stop_2_dau, tt_stop_doi, thoi_gian)
     can mo phong nhieu vi the - do la viec cua tester."

Ma tester thi: mot `terminal64.exe` la rang buoc VAT LI, va ngay 13/09 no khong
dang nhap duoc nen ca ban do nam cho. Tuc **nam ho quan trong nhat cua module
quan trong nhat dang treo vao mot cu bam chuot.**

File nay go cai treo do. Nam ho con lai chay duoc bang Python, khong can MT5.

## Ba ho nay khac ho mot vi the o cho nao

Khong phai o "nhieu lenh" - ma o cho **rui ro cua ca RO, khong phai cua tung
lenh**. Ho mot vi the hoi "lenh nay lai hay lo"; ho nhieu vi the hoi "ca ro
dang lai hay lo", va dong het mot luot. Do la ly do `luoi_dca` khong dat SL
tung lenh (tran so nhoi + tran so nen moi la luoi an toan cua no), va la ly do
`hedge` thao khoa khi **tong** ve duong chu khong cuu tung chan.

## Thu tu trong mot nen - lay nguyen tu `pmg_engine`

Bar khong noi gia cham muc nao truoc. Dung dung mot mo hinh duong di ba chang
`O -> X -> Y -> C` da dung o `pmg_engine`, va cung mot gia dinh bi quan: cham
cuc tri BAT LOI cho vi the dang co truoc. Luat cua EA duoc danh gia o CUOI NEN
(dung nhu `QuanTri()` cua EA chay moi nen moi), con SL/TP va lenh cho thi khop
TRONG nen.

Chay:  python -m nhan.quan_tri_nhieu --thu
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

#: Nam ho can nhieu vi the. Ten TRUNG voi ban do MT5 (`ea_QuanTriBench.mq5`)
#: de hai ban do doi chieu duoc voi nhau.
HO = ("hedge", "luoi_dca", "stop_2_dau", "tt_stop_doi", "thoi_gian")

#: Luoi an toan chung, giong ban do MT5: SL cung 3 ATR + tran so nen giu.
SL_CUNG = 3.0
GIU_TOI_DA = 120


@dataclass
class ViThe:
    chieu: int          # +1 mua, -1 ban
    gia: float
    lot: float
    bar_vao: int
    sl: float = 0.0     # 0 = khong dat
    tp: float = 0.0


@dataclass
class LenhCho:
    """Lenh cho (stop / limit). `kich_hoat` la gia cham thi khop."""
    chieu: int
    gia: float
    lot: float
    sl_kc: float = 0.0        # khoang cach SL tinh tu gia khop, 0 = khong dat
    huy_khi_khop_cai_kia: bool = False


@dataclass
class TrangThai:
    vi_the: list = field(default_factory=list)
    cho: list = field(default_factory=list)
    so_nhoi: int = 0
    da_hedge: bool = False
    bar_mo: int = -1
    chieu_ro: int = 0
    # Hai bo dem cua RO DANG MO. Khong co chung thi mot chan bi cat le se bien
    # mat khoi so sach: `len(vi_the)` luc dong ro chi con cac chan CON SONG, va
    # `lai_ro(...)` luc do cung chi tinh cac chan con song. Ro dong het bang SL
    # tung chan se ghi "0 lenh, lai 0" - dung cai ro lo nang nhat lai vo hinh.
    ro_lenh: int = 0
    ro_lai_da_chot: float = 0.0


def _atr(h, l, c, n: int = 14) -> np.ndarray:
    h = np.asarray(h, float); l = np.asarray(l, float); c = np.asarray(c, float)
    m = len(h)
    out = np.full(m, np.nan)
    if m <= n:
        return out
    tr = np.empty(m)
    tr[0] = h[0] - l[0]
    pc = c[:-1]
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - pc), np.abs(l[1:] - pc)))
    out[n] = tr[1:n + 1].mean()
    a = 1.0 / n
    for i in range(n + 1, m):
        out[i] = out[i - 1] + a * (tr[i] - out[i - 1])
    return out


def _gia_tb(vi_the: list) -> tuple[float, float, int]:
    """(gia trung binh theo lot, tong lot, chieu). Ro tron chieu -> chieu 0."""
    if not vi_the:
        return 0.0, 0.0, 0
    tong = sum(v.lot for v in vi_the)
    if tong <= 0:
        return 0.0, 0.0, 0
    gtb = sum(v.lot * v.gia for v in vi_the) / tong
    cac_chieu = {v.chieu for v in vi_the}
    return gtb, tong, (cac_chieu.pop() if len(cac_chieu) == 1 else 0)


def lai_ro(vi_the: list, gia: float) -> float:
    """Lai/lo cua CA RO tai `gia`, tinh theo DIEM x lot. Duong = dang lai."""
    return sum(v.chieu * (gia - v.gia) * v.lot for v in vi_the)


def dap_nhieu(df, tin_hieu, ho: str, tham_so: dict | None = None,
              lot: float = 1.0, atr_n: int = 14, sl_cung: float = SL_CUNG,
              giu_toi_da: int = GIU_TOI_DA, nhoi_toi_da: int = 10,
              bi_quan: bool = True, atr_arr=None) -> dict:
    """Chay `tin_hieu` qua mot ho quan tri NHIEU VI THE.

    `tin_hieu[i]` = chieu muon vao, BIET tai close[i] -> vao o open[i+1].
    Tra ve dict co `duong_cong` (lai luy ke theo DIEM) va `lenh` (tung ro).

    Don vi la DIEM x lot, khong phai phan tram - de doi chieu duoc voi bao cao
    cua MT5 tester, va de `_quet_quan_tri_python` quy ve tien theo cach cua no.
    """
    if ho not in HO:
        raise ValueError(f"ho khong biet: {ho} (co: {', '.join(HO)})")
    p = dict(tham_so or {})
    o = np.asarray(df["open"], float)
    hi = np.asarray(df["high"], float)
    lo = np.asarray(df["low"], float)
    cl = np.asarray(df["close"], float)
    n = len(o)
    # `atr_arr` cho phep GHIM ATR. Khong co no thi moi lan doi mot gia tri close
    # la doi ca luoi, va test khong con dap an chinh xac de kiem - chi con kiem
    # duoc "chay khong loi", thu khong phan biet engine dung voi engine sai.
    atr = _atr(hi, lo, cl, atr_n) if atr_arr is None else np.asarray(atr_arr, float)
    th = np.asarray(tin_hieu, float)

    st = TrangThai()
    duong = np.zeros(n)
    thuc_hien = 0.0
    cac_ro: list[dict] = []
    dinh_lot = 0.0
    # Ba mang de DI CHUNG DUONG TINH TIEN voi ho mot vi the (`dap_quan_tri.dap`):
    # `vao_lenh.tinh_tien` doc dung ba cai nay de ap spread / truot gia / phi qua
    # dem. Khong co chung thi nam ho moi phai co mot duong tinh tien RIENG, va
    # hai duong tinh tien thi som muon lech nhau ma khong ai biet.
    loi_tho = np.zeros(n)          # loi suat log x phoi nhiem, theo tung bar
    khoi = np.zeros(n)             # khoi luong GOP khop tai tung bar (cho spread)
    dai = np.zeros(n)              # phoi nhiem chan MUA (cho phi qua dem)
    ngan = np.zeros(n)             # phoi nhiem chan BAN

    def _ghi_tien(v: "ViThe", bar_ra: int, gia_ra: float):
        """Rai lai/lo cua MOT chan ra tung bar theo gia OPEN-TO-OPEN.

        Cung quy uoc voi `dap_quan_tri.dap`: doan dau tu gia VAO toi open ke tiep,
        cac bar giua theo open-to-open, doan cuoi tu open toi gia RA.
        """
        vi = int(v.bar_vao)
        ra = int(min(bar_ra, n - 1))
        khoi[vi] += v.lot
        khoi[ra] += v.lot
        for b in range(vi, ra):
            g0 = v.gia if b == vi else o[b]
            g1 = o[b + 1] if b + 1 < n else o[b]
            loi_tho[b] += v.chieu * v.lot * np.log(max(g1, 1e-12) / max(g0, 1e-12))
        if ra > vi:
            loi_tho[ra] += v.chieu * v.lot * np.log(
                max(gia_ra, 1e-12) / max(o[ra], 1e-12))

    def _dong_het(i: int, gia: float, ly_do: str):
        nonlocal thuc_hien
        con_lai = lai_ro(st.vi_the, gia)
        thuc_hien += con_lai
        for v in st.vi_the:
            _ghi_tien(v, i, gia)
        cac_ro.append({"bar_mo": st.bar_mo, "bar_dong": i,
                       "lai": st.ro_lai_da_chot + con_lai,
                       "so_lenh": st.ro_lenh, "ly_do": ly_do,
                       "chieu": st.chieu_ro,
                       "giu_bar": i - st.bar_mo if st.bar_mo >= 0 else 0})
        st.vi_the.clear()
        st.cho.clear()
        st.so_nhoi = 0
        st.da_hedge = False
        st.chieu_ro = 0
        st.bar_mo = -1
        st.ro_lenh = 0
        st.ro_lai_da_chot = 0.0

    def _mo(chieu: int, gia: float, i: int, l: float, sl_kc: float = 0.0):
        nonlocal dinh_lot
        v = ViThe(chieu=chieu, gia=gia, lot=l, bar_vao=i)
        if sl_kc > 0:
            v.sl = gia - chieu * sl_kc
        st.vi_the.append(v)
        st.ro_lenh += 1
        if st.chieu_ro == 0:
            st.chieu_ro = chieu
        if st.bar_mo < 0:
            st.bar_mo = i
        t = sum(x.lot for x in st.vi_the)
        if t > dinh_lot:
            dinh_lot = t

    # ------------------------------------------------------------- VONG NEN
    for i in range(atr_n + 2, n):
        a = atr[i - 1]
        if not np.isfinite(a) or a <= 0:
            duong[i] = thuc_hien
            continue
        Oi, Hi, Li, Ci = o[i], hi[i], lo[i], cl[i]

        # ---- duong di trong nen: O -> cuc tri BAT LOI -> cuc tri con lai -> C
        if st.vi_the:
            c_ro = st.chieu_ro or 1
            bat_loi = Li if c_ro > 0 else Hi
            thuan = Hi if c_ro > 0 else Li
            chang = (bat_loi, thuan, Ci) if bi_quan else (thuan, bat_loi, Ci)
        else:
            chang = ((Li, Hi, Ci) if Ci >= Oi else (Hi, Li, Ci))

        diem = Oi
        for dich in chang:
            lo_c, hi_c = min(diem, dich), max(diem, dich)

            # --- lenh cho khop (sap theo khoang cach tu diem xuat phat)
            khop = sorted([k for k in st.cho if lo_c <= k.gia <= hi_c],
                          key=lambda k: abs(k.gia - diem))
            for k in khop:
                if k not in st.cho:
                    continue
                st.cho.remove(k)
                if k.huy_khi_khop_cai_kia:
                    st.cho = [x for x in st.cho if not x.huy_khi_khop_cai_kia]
                _mo(k.chieu, k.gia, i, k.lot, k.sl_kc)

            # --- SL / TP cua tung vi the
            for v in list(st.vi_the):
                gia_ra = (v.sl if (v.sl and lo_c <= v.sl <= hi_c)
                          else v.tp if (v.tp and lo_c <= v.tp <= hi_c) else None)
                if gia_ra is None:
                    continue
                x = v.chieu * (gia_ra - v.gia) * v.lot
                thuc_hien += x
                st.ro_lai_da_chot += x      # giu trong so sach cua RO, xem TrangThai
                _ghi_tien(v, i, gia_ra)
                st.vi_the.remove(v)
            if st.bar_mo >= 0 and not st.vi_the and not st.cho:
                _dong_het(i, dich, "sl_tung_lenh")
            diem = dich

        # ---- LUAT CUA HO: danh gia o CUOI NEN, dung nhu `QuanTri()` cua EA
        if st.vi_the:
            _luat_ho(ho, p, st, i, Ci, a, lot, nhoi_toi_da, _mo, _dong_het)
        if st.vi_the and st.bar_mo >= 0 and (i - st.bar_mo) >= giu_toi_da:
            _dong_het(i, Ci, "tran_nen")

        # ---- VAO LENH MOI khi dang rong
        if not st.vi_the and not st.cho and i + 1 < n and abs(th[i]) > 1e-12:
            # CHIEU LAY TU TIN HIEU. Ban dau cho nay bo qua `th[i]` va luon vao
            # MUA - test random walk bat duoc: `luoi_dca` che ra -128 diem tren
            # mot chuoi khong co edge, chi vi no danh mot chieu suot 20.000 nen.
            _vao_ho(ho, p, st, i + 1, o[i + 1], a, lot, sl_cung, _mo,
                    chieu=1 if th[i] > 0 else -1)

        duong[i] = thuc_hien + (lai_ro(st.vi_the, Ci) if st.vi_the else 0.0)
        for v in st.vi_the:
            if v.chieu > 0:
                dai[i] += v.lot
            else:
                ngan[i] += v.lot

    # ---- ro con treo o cuoi mau: MARK-TO-MARKET, khong duoc bo qua
    ro_treo = None
    if st.vi_the:
        con_lai = lai_ro(st.vi_the, cl[n - 1])
        thuc_hien += con_lai
        for v in st.vi_the:
            _ghi_tien(v, n - 1, cl[n - 1])
        # DUNG cong thuc voi `_dong_het`: phai cong ca phan da chot cua ro nay.
        # Ban dau cho nay dung `len(st.vi_the)` va `lai` cua rieng cac chan CON
        # SONG - do 14/09 tren ho `tt_stop_doi`: bao +2,0 trong khi su that la
        # -1,0, vi chan long da bi cat lo -3,0 bien mat khoi so sach.
        ro_treo = {"so_lenh": st.ro_lenh, "lai_mtm": st.ro_lai_da_chot + con_lai,
                   "con_song": len(st.vi_the)}
        cac_ro.append({"bar_mo": st.bar_mo, "bar_dong": n - 1,
                       "lai": st.ro_lai_da_chot + con_lai,
                       "so_lenh": st.ro_lenh, "ly_do": "MTM_cuoi_mau",
                       "chieu": st.chieu_ro,
                       "giu_bar": n - 1 - st.bar_mo if st.bar_mo >= 0 else 0})
    duong[n - 1] = thuc_hien

    dem: dict = {}
    for r in cac_ro:
        dem[r["ly_do"]] = dem.get(r["ly_do"], 0) + 1
    lai_cac_ro = [r["lai"] for r in cac_ro]
    return {
        "ho": ho, "tham_so": p,
        # --- ba mang cho `vao_lenh.tinh_tien` (dung ten voi `dap_quan_tri.dap`)
        "vi_the": dai - ngan,
        "loi_tho": loi_tho,
        "khoi_luong": khoi,
        "dai": dai, "ngan": ngan,
        "bar_trung_vi": (float(np.median([r["giu_bar"] for r in cac_ro]))
                         if cac_ro else 0.0),
        # --- so sach rieng cua ho nhieu vi the
        "duong_cong": duong,
        "lai_tong": thuc_hien,
        "so_ro": len(cac_ro),
        "so_lenh": sum(r["so_lenh"] for r in cac_ro),
        "dinh_lot": dinh_lot,
        "ty_le_thang": (sum(1 for x in lai_cac_ro if x > 0) / len(lai_cac_ro)
                        if lai_cac_ro else 0.0),
        "lai_ro_trung_vi": float(np.median(lai_cac_ro)) if lai_cac_ro else 0.0,
        "lai_ro_xau_nhat": float(min(lai_cac_ro)) if lai_cac_ro else 0.0,
        "giu_bar_trung_vi": (float(np.median([r["giu_bar"] for r in cac_ro]))
                             if cac_ro else 0.0),
        "ly_do": dem,
        "ro_treo_cuoi_mau": ro_treo,
        "ro": cac_ro,
    }


# ------------------------------------------------------------------ VAO LENH
def _vao_ho(ho, p, st, i, gia, a, lot, sl_cung, _mo, chieu: int = 1):
    """Mo vi the dau tien cua mot ro, theo dung cach tung ho vao."""
    kc_sl = max(sl_cung * a, 0.0)
    if ho == "stop_2_dau":
        # Hai lenh cho hai ben, cai nao khop thi huy cai kia. KHONG vao thi truong.
        d = max(p.get("kc_atr", 1.0), 0.01) * a
        st.cho.append(LenhCho(+1, gia + d, lot, kc_sl, huy_khi_khop_cai_kia=True))
        st.cho.append(LenhCho(-1, gia - d, lot, kc_sl, huy_khi_khop_cai_kia=True))
        st.bar_mo = i
        return
    if ho == "luoi_dca":
        # Luoi khong dat SL tung lenh: tran so nhoi + tran so nen la luoi an toan.
        _mo(chieu, gia, i, lot, 0.0)
        return
    _mo(chieu, gia, i, lot, kc_sl)
    if ho == "tt_stop_doi":
        # Vao thi truong + dat ngay mot lenh cho NGUOC chieu o xa `kc_atr`.
        d = max(p.get("kc_atr", 1.0), 0.01) * a
        l2 = lot * max(p.get("he_so_lot", 1.0), 0.1)
        st.cho.append(LenhCho(-chieu, gia - chieu * d, l2, 0.0))


# ---------------------------------------------------------------- LUAT TUNG HO
def _luat_ho(ho, p, st, i, gia, a, lot, nhoi_toi_da, _mo, _dong_het):
    gtb, tong_lot, chieu = _gia_tb(st.vi_the)
    if tong_lot <= 0:
        return

    if ho == "luoi_dca":
        lai_kc = (gia - gtb) * (chieu or st.chieu_ro)
        if lai_kc >= max(p.get("tp_atr", 1.0), 0.01) * a:
            _dong_het(i, gia, "tp_chung")
            return
        nguoc = -lai_kc
        buoc = max(p.get("buoc_atr", 1.0), 0.01) * a
        if nguoc >= buoc * (st.so_nhoi + 1) and st.so_nhoi < nhoi_toi_da - 1:
            _mo(st.chieu_ro, gia, i, lot, 0.0)
            st.so_nhoi += 1
        return

    if ho == "hedge":
        lai = lai_ro(st.vi_the, gia)
        if not st.da_hedge and -lai >= max(p.get("mo_khoa_atr", 1.0), 0.01) * a * tong_lot:
            l2 = lot * max(p.get("he_so_lot", 1.0), 0.1)
            _mo(-st.chieu_ro, gia, i, l2, 0.0)
            st.da_hedge = True
            return
        # Thao khoa khi CA RO ve duong - khong cuu tung chan ma cuu tong.
        if st.da_hedge and lai > 0:
            _dong_het(i, gia, "ro_ve_duong")
        return

    if ho == "thoi_gian":
        if st.bar_mo >= 0 and (i - st.bar_mo) >= int(p.get("so_nen", 20)):
            _dong_het(i, gia, "het_gio")
        return

    if ho in ("stop_2_dau", "tt_stop_doi"):
        # Ca hai ho deu song bang SL/TP cua tung lenh + tran nen; them mot TP
        # chung theo RO neu duoc khai - do la cach `tt_stop_doi` chot khi ca hai
        # chan cung mo (mot chan lai bu chan kia).
        if "tp_ro_atr" in p:
            if lai_ro(st.vi_the, gia) >= p["tp_ro_atr"] * a * tong_lot:
                _dong_het(i, gia, "tp_chung")
        return


# --------------------------------------------------------------------- BO LUAT
def bo_luat() -> dict:
    """Luoi tham so cho nam ho. Ten khoa trung quy uoc cua ban do MT5."""
    ra: dict = {}
    for x in (0.5, 1.0, 2.0):
        for y in (0.5, 1.0, 2.0):
            ra[f"luoi_dca|{x:.1f}|{y:.1f}"] = ("luoi_dca",
                                               {"buoc_atr": x, "tp_atr": y})
        ra[f"hedge|{x:.1f}"] = ("hedge", {"mo_khoa_atr": x, "he_so_lot": 1.0})
        ra[f"stop_2_dau|{x:.1f}"] = ("stop_2_dau", {"kc_atr": x})
        ra[f"tt_stop_doi|{x:.1f}"] = ("tt_stop_doi", {"kc_atr": x, "he_so_lot": 1.0})
    for nen in (10, 20, 40, 80):
        ra[f"thoi_gian|{nen}"] = ("thoi_gian", {"so_nen": nen})
    return ra


def _cli(argv: list) -> int:
    import pandas as pd
    n = 3000
    rng = np.random.default_rng(7)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
    idx = pd.date_range("2020-01-01", periods=n, freq="h")
    o = gia
    c = np.r_[gia[1:], gia[-1]]
    df = pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.001,
                       "low": np.minimum(o, c) * 0.999, "close": c}, index=idx)
    th = np.zeros(n)
    th[::50] = 1.0
    print(f"{'ho':<22}{'so ro':>7}{'so lenh':>9}{'lai':>10}{'dinh lot':>10}  ly do")
    for ten, (ho, p) in bo_luat().items():
        r = dap_nhieu(df, th, ho, p)
        print(f"{ten:<22}{r['so_ro']:>7}{r['so_lenh']:>9}{r['lai_tong']:>10.2f}"
              f"{r['dinh_lot']:>10.1f}  {r['ly_do']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
