# -*- coding: utf-8 -*-
"""pmg_engine.py - MO PHONG RO cua PMG tren bar. Cong G2 cua dac ta.

## Mo hinh duong di trong bar - cho quan trong nhat cua ca file

Bar khong noi gia cham muc nao truoc. Voi luoi day nhieu tang trong mot bar, sai
so cua gia dinh nay **lon hon ca edge** (dac ta muc 5.1). Dac ta doi: chay tren
tick, HOAC chung minh ket qua bat bien voi gia dinh tie-break bi quan nhat.

File nay chon duong thu hai va lam cho no DO DUOC. Moi bar duoc di theo duong hai
chang `O -> X -> Y` voi {X, Y} = {H, L}, va thu tu do la THAM SO:

    tie_break = "bi_quan"   dang co ro : cham cuc tri BAT LOI truoc
                            dang rong  : cham cuc tri GAN HON truoc roi dao lai
                                         cuc tri xa -> ro mo ra sai ben roi bi can
    tie_break = "lac_quan"  nguoc lai o ca hai truong hop

`do_bat_bien()` chay ca hai va do khoang cach. Ket qua CHI duoc doc khi hai ban
khong lat dau - do la phep thay the duy nhat chap nhan duoc cho tick data.

## Ba luat ke toan khong duoc quen

  1. **Khe gia** (muc 8.4): tang luoi nam trong khe khop tai `open` sau khe, KHONG
     tai gia tang; basket stop cung danh gia tai open. Truot do duoc ghi rieng
     thanh `khe_truot_atr*`, khong tron vao DD chung - vi voi ro `AGAINST` khe
     xuyen stop chinh la **che do chet** cua co che.
  2. **Ro chua dong o cuoi mau** (muc 5.4): mark-to-market. Khong co cho nay thi
     MOI cau hinh AGAINST deu dep gia tao.
  3. **Chi phi theo GIO** (muc 5.5): luoi day nhat hay khop dung luc spread gian.
     Dung `MoHinhChiPhi.spread_frac_theo_gio`. Nua spread tra luc VAO (theo gio
     bar vao), nua con lai luc RA (theo gio bar ra).

## Don vi ke toan

Tat ca theo PHAN CUA EQUITY DAU (frac). Tang j co `q_j` don vi; tang 0 co phoi
nhiem `phoi_nhiem_1` (mac dinh 1.0 = 100% equity). Lai cua ro tai gia p:

    lai(p) = phoi * side * sum_j q_j * (p - e_j) / e_j  =  A*p + B

tuyen tinh theo p, nen MOI duong ra (chot tien, tran lo noi cua ro, trailing cua
ro) deu giai nguoc duoc ra mot GIA chinh xac va xu li y het mot muc luoi. Do la
li do engine nay khong phai do lai o hai dau bar roi doan o giua.
"""
from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))
    from nhan import pmg as PMG
else:
    from . import pmg as PMG


def _giua(a: float, b: float, x: float) -> bool:
    return min(a, b) <= x <= max(a, b)


#: Equity (theo phan cua von dau) ma duoi do coi nhu tai khoan da chay.
#: Khong phai 0: san goi margin call tu truoc do, va mot tai khoan con 2% von
#: thi khong con dat noi lot toi thieu cua bat ky cau hinh nao.
NGUONG_CHAY = 0.02

#: Buoc luoi phai rong gap it nhat ngan nay lan BIEN DO MOT NEN cua chuoi dang
#: chay, neu khong thi ca cai luoi nam gon trong mot nen va ket qua la tao tac
#: cua gia dinh duong di, khong phai cua thi truong. Do 14/09 tren random walk
#: khong chi phi: buoc/bien_do = 0,54 cho ra +327% trong khi dap an la ~0.
NGUONG_PHAN_GIAI = 2.0


def do_phan_giai(df, cf: "PMG.CauHinh", atr_arr=None) -> dict:
    """Chuoi bar nay co DU MIN de mo phong cau hinh nay khong?

    Day la ban do duoc cua bay 5.1 trong dac ta (*"du lieu bar khong cho biet thu
    tu cham trong bar; voi luoi day nhieu tang trong 1 bar, sai so nay lon hon ca
    edge"*). Dac ta doi tick data cho `h < 0.3 ATR`; cau hoi that khong phai
    "h co nho hon 0,3 ATR khong" ma la **"buoc luoi co lon hon mot nen khong"**,
    va cau do tra loi duoc bang so ngay tren chinh chuoi sap chay.

    Ba trang thai (luat cua du an), khong phai hai:
        DU        - doc duoc so
        CHUA_DO_DUOC - chay xuong khung nho hon, hoac gian h ra; **khong** duoc
                    doc ket qua nhu mot ket luan AM hay DUONG
    """
    hi = np.asarray(df["high"], float)
    lo = np.asarray(df["low"], float)
    if atr_arr is None:
        atr_arr = PMG.atr(hi, lo, np.asarray(df["close"], float), cf.atr_period)
    bien_do = float(np.median(hi - lo))
    a_tv = float(np.nanmedian(atr_arr))
    if not np.isfinite(bien_do) or bien_do <= 0 or not np.isfinite(a_tv):
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "bien do bar hoac ATR khong hop le"}
    buoc = cf.h * a_tv
    tp = cf.tp_dist * a_tv
    ty_buoc = buoc / bien_do
    ty_tp = tp / bien_do
    thieu = []
    if ty_buoc < NGUONG_PHAN_GIAI:
        thieu.append(f"buoc luoi {ty_buoc:.2f}x bien do nen (can >= {NGUONG_PHAN_GIAI:g})")
    if cf.tp_mode == "avg_plus" and ty_tp < NGUONG_PHAN_GIAI:
        thieu.append(f"tp_dist {ty_tp:.2f}x bien do nen (can >= {NGUONG_PHAN_GIAI:g})")
    return {
        "trang_thai": "DU" if not thieu else "CHUA_DO_DUOC",
        "ly_do": "; ".join(thieu),
        "bien_do_nen": bien_do,
        "atr_trung_vi": a_tv,
        "buoc_tren_bien_do": ty_buoc,
        "tp_tren_bien_do": ty_tp,
    }


def atr_khung(df, atr_tf: str, period: int = 14) -> np.ndarray:
    """ATR tinh tren khung LON roi rai xuong tung bar nho, KHONG nhin truoc.

    Dac ta muc 8.3 noi ro: khung thoi gian di vao he chi qua `atr_tf` (thu quy
    doi `h` ra gia tri tuyet doi), con **granularity mo phong luon giu tick/M1
    bat ke scale**. Ham nay la cho thuc hien dieu do: gop len `atr_tf`, tinh ATR,
    roi `ffill` xuong bar nho voi mot buoc `shift` de bar dang chay khong duoc
    dung ATR cua chinh no.
    """
    import pandas as pd
    if atr_tf not in QUY_RESAMPLE:
        raise ValueError(f"atr_tf khong ho tro: {atr_tf} (co: {sorted(QUY_RESAMPLE)})")
    lon = df.resample(QUY_RESAMPLE[atr_tf]).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    if len(lon) < period + 2:
        raise ValueError(f"qua it bar {atr_tf} ({len(lon)}) de tinh ATR({period})")
    a = pd.Series(PMG.atr(lon["high"], lon["low"], lon["close"], period), index=lon.index)
    return a.shift(1).reindex(df.index, method="ffill").to_numpy()


QUY_RESAMPLE = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min",
                "H1": "1h", "H4": "4h", "D1": "1D", "W1": "1W"}


def mo_phong(df, cf: "PMG.CauHinh", cp=None, atr_arr=None,
             giu_duong_cong: bool = False) -> dict:
    """Chay engine PMG tren `df` (cot open/high/low/close, index thoi gian).

    `cp` = `chi_phi.MoHinhChiPhi` hoac None (khong chi phi - chi de kiem toan
    engine, khong bao gio de ket luan tien).
    """
    if cf.direction == "BOTH":
        # hai ro doc lap, ke toan TACH BACH hoan toan (dac ta muc 1.2)
        a = mo_phong(df, replace(cf, direction="WITH"), cp, atr_arr, giu_duong_cong)
        b = mo_phong(df, replace(cf, direction="AGAINST"), cp, atr_arr, giu_duong_cong)
        return _gop_both(a, b, cf)

    o = np.asarray(df["open"], float)
    hi = np.asarray(df["high"], float)
    lo = np.asarray(df["low"], float)
    cl = np.asarray(df["close"], float)
    n = len(o)
    if n < cf.atr_period + 10:
        return {"loi": "qua it bar", "so_ro": 0, "so_lenh": 0,
                "ma": cf.ma_dinh_danh(), "van_tay": cf.van_tay()}

    if atr_arr is None:
        atr_arr = PMG.atr(hi, lo, cl, cf.atr_period)
    atr_arr = np.asarray(atr_arr, float)
    pg = do_phan_giai(df, cf, atr_arr)

    if cp is not None:
        sp = np.asarray(cp.spread_mang(df.index), float)   # frac, MOT chieu
        truot = float(getattr(cp, "truot_gia_frac", 0.0))
        phi_mua = float(getattr(cp, "phi_nam_mua", 0.0))
        phi_ban = float(getattr(cp, "phi_nam_ban", 0.0))
    else:
        sp = np.zeros(n)
        truot = phi_mua = phi_ban = 0.0

    ngay = np.zeros(n)
    if n > 1:
        ngay[:-1] = (np.diff(df.index.to_numpy()).astype("timedelta64[s]")
                     .astype(float) / 86400.0)

    buc = PMG.bucket_phien(df.index) if cf.phien != PMG.PHIEN_TAT_CA else None
    trong_phien = (buc == cf.phien) if buc is not None else np.ones(n, bool)

    phoi = cf.phoi_nhiem_1
    bi_quan = (cf.tie_break == "bi_quan")
    st = _TrangThai()
    if giu_duong_cong:
        st.duong = np.ones(n)

    # ---------------------------------------------------------- ham noi bo
    def _lai(p: float) -> float:
        return st.A * p + st.B

    def _gia_cho_lai(muc: float):
        return (muc - st.B) / st.A if st.A else None

    def _cac_duong_ra():
        """(gia, loai) cua moi duong ra dang song. Rong khi ro rong."""
        if st.tong_q <= 0:
            return ()
        ra = []
        if cf.tp_mode == "avg_plus":
            ra.append((st.tong_qe / st.tong_q + st.side * cf.tp_dist * st.atr_neo, "tp"))
        elif cf.tp_mode == "anchor_return":
            ra.append((st.neo, "tp"))
        elif cf.tp_mode == "money":
            p = _gia_cho_lai(cf.tp_money * st.eq_luc_mo)
            if p is not None:
                ra.append((p, "tp"))
        elif cf.tp_mode == "trail" and st.dinh_lai > 0:
            p = _gia_cho_lai(st.dinh_lai * (1.0 - cf.trail_giveback))
            if p is not None:
                ra.append((p, "tp_trail"))
        if cf.hard_sl_atr:
            ra.append((st.neo - st.side * cf.hard_sl_atr * st.atr_neo, "sl_cung"))
        if cf.max_basket_dd:
            p = _gia_cho_lai(-cf.max_basket_dd * st.eq_luc_mo)
            if p is not None:
                ra.append((p, "sl_dd"))
        return ra

    def _mo_tang(gia: float, i: int, muc: float | None = None):
        """Them mot tang. `gia` la gia KHOP THAT, `muc` la MUC LUOI ly thuyet.

        Hai cai nay chi khac nhau khi co KHE, va phan biet chung la bat buoc:
        muc luoi ke tiep phai tinh tu MUC, khong tu gia khop. Neu tinh tu gia
        khop thi mot cai khe se keo ca cai luoi troi theo no - do 14/09 tren khe
        dung san 97 -> 80: luoi dang le khop 6 tang (94, 91, 88, 85, 82 deu nam
        trong khe) chi khop duoc 2, vi tang ke tiep bi doi ve 77.
        """
        if muc is None:
            muc = gia
        j = len(st.q)
        qj = _QJ(cf.size_mode, j, cf.size_r)
        st.e.append(gia)
        st.q.append(qj)
        st.tong_q += qj
        st.tong_qe += qj * gia
        st.A += phoi * st.side * qj / gia
        st.B -= phoi * st.side * qj
        st.chi_phi += (0.5 * sp[i] + 0.5 * truot) * qj * phoi
        if j == 0:
            st.bar_mo = i
            # equity co the da am neu tai khoan chay; nguong DD cua ro phai tinh
            # tren mot so DUONG, neu khong `max_basket_dd` doi dau va khong bao gio cham
            st.eq_luc_mo = max(st.equity, 1e-6)
        db = st.tong_q * phoi
        if db > st.dinh_don_bay:
            st.dinh_don_bay = db
        if len(st.q) > st.dinh_so_tang:
            st.dinh_so_tang = len(st.q)
        if len(st.q) >= cf.max_legs:
            st.muc_ke = None
        else:
            if cf.step_mode == "vol_adaptive":
                at = atr_arr[i - 1]
                b = cf.h * (at if not math.isnan(at) and at > 0 else st.atr_neo)
            elif cf.step_mode == "expanding":
                b = cf.h * (cf.step_g ** len(st.q)) * st.atr_neo
            else:
                b = cf.h * st.atr_neo
            st.muc_ke = muc + st.dir_luoi * b

    def _dong_ro(gia: float, i: int, loai: str, gia_le=None):
        lai = _lai(gia)
        st.chi_phi += (0.5 * sp[i] + 0.5 * truot) * st.tong_q * phoi
        st.thuc_hien += lai
        if gia_le is not None and st.atr_neo > 0 and abs(gia - gia_le) > 1e-12:
            st.khe_truot.append(abs(gia - gia_le) / st.atr_neo)
        st.cac_ro.append({"bar_mo": st.bar_mo, "bar_dong": i, "so_tang": len(st.q),
                          "loai": loai, "lai": lai, "don_bay": st.tong_q * phoi,
                          "side": st.side, "giu_bar": i - st.bar_mo})
        st.reset_ro()
        st.cho_toi_bar = i + 1 + (int(cf.rearm_n) if cf.rearm == "cooldown" else 0)

    def _chang(a: float, b: float, i: int) -> None:
        """Di mot chang gia don dieu a -> b, xu li su kien DUNG THU TU GAP."""
        diem = a
        while True:
            if st.tong_q == 0:
                if st.neo is None:
                    return
                buoc = cf.h * st.atr_neo
                ung = []
                for gia, d in ((st.neo + buoc, 1), (st.neo - buoc, -1)):
                    if _giua(diem, b, gia):
                        ung.append((abs(gia - diem), gia, "mo", d))
                if not ung:
                    return
                ung.sort(key=lambda x: x[0])
                _, gia, _, d = ung[0]
                st.dir_luoi = d
                st.side = d if cf.direction == "WITH" else -d
                _mo_tang(gia, i)
                diem = gia
                continue
            ung = []
            if st.muc_ke is not None and _giua(diem, b, st.muc_ke):
                ung.append((abs(st.muc_ke - diem), st.muc_ke, "fill"))
            for gia, loai in _cac_duong_ra():
                if _giua(diem, b, gia):
                    ung.append((abs(gia - diem), gia, loai))
            if not ung:
                return
            ung.sort(key=lambda x: x[0])
            _, gia, loai = ung[0]
            if loai == "fill":
                _mo_tang(gia, i)
                diem = gia
                continue
            _dong_ro(gia, i, loai)
            return           # ro dong giua bar -> khong tai vu trang trong bar nay

    # ------------------------------------------------------------------ VONG
    for i in range(cf.atr_period + 2, n):
        a_tr = atr_arr[i - 1]
        if math.isnan(a_tr) or a_tr <= 0:
            continue
        Oi, Hi, Li, Ci = o[i], hi[i], lo[i], cl[i]

        if st.tong_q > 0:
            # ---- phi qua dem cho tang dang giu
            if ngay[i] > 0:
                st.swap += (st.tong_q * phoi
                            * (phi_mua if st.side > 0 else phi_ban) * ngay[i] / 365.0)
            # ---- ep dong o bien phien (muc 8.2.2)
            if cf.eod_flatten and not trong_phien[i]:
                _dong_ro(Oi, i, "eod")
        if st.tong_q > 0 and st.muc_ke is not None:
            # ---- KHE GIA: tang luoi nam trong khe khop tai OPEN, khong tai gia tang
            while st.muc_ke is not None and (
                    (st.dir_luoi > 0 and Oi >= st.muc_ke)
                    or (st.dir_luoi < 0 and Oi <= st.muc_ke)):
                _mo_tang(Oi, i, muc=st.muc_ke)      # khop tai OPEN, luoi giu nguyen cho
        if st.tong_q > 0:
            # ---- KHE GIA: basket stop danh gia TAI OPEN sau khe
            for gia, loai in _cac_duong_ra():
                loi_neu = (Oi >= gia) if st.side > 0 else (Oi <= gia)
                lo_neu = (Oi <= gia) if st.side > 0 else (Oi >= gia)
                if (loai.startswith("sl") and lo_neu) or \
                   (loai.startswith("tp") and loi_neu):
                    _dong_ro(Oi, i, loai, gia_le=gia)
                    break

        # ---- dat / doi goc luoi khi dang RONG
        if st.tong_q == 0:
            # Ro rong thi equity VAN phai duoc chot lai o bar nay truoc khi bo qua.
            # Bar ma ro vua dong (o khoi khe gia ben tren) roi vao dung nhanh nay;
            # khong cap nhat thi `dd_max` bo sot dung cai day vua tao ra.
            st.equity = 1.0 + st.thuc_hien - st.swap - st.chi_phi
            st.cap_nhat_dd()
            if i < st.cho_toi_bar or not trong_phien[i]:
                st.ghi_duong(i)
                continue
            if cf.rearm == "require_move" and st.neo_cho_move is not None:
                if abs(Oi - st.neo_cho_move) < cf.rearm_n * a_tr:
                    st.ghi_duong(i)
                    continue
                st.neo_cho_move = None
            if st.neo is None:
                st.neo, st.atr_neo, st.bar_mo = Oi, a_tr, i
            elif cf.anchor_mode == "trailing" \
                    and abs(Oi - st.neo) > cf.reanchor_dist * st.atr_neo:
                # goc moi tinh tu Open[i] - khong nhin truoc (muc 5.3)
                st.neo, st.atr_neo, st.bar_mo = Oi, a_tr, i
            elif cf.anchor_mode == "session" and buc is not None and buc[i] != buc[i - 1]:
                st.neo, st.atr_neo, st.bar_mo = Oi, a_tr, i

        # ---- duong di trong bar: BA chang O -> X -> Y -> C
        #
        # Chang cuoi ve C la bat buoc, khong phai lam dep. Bo no di thi moi bar
        # ket thuc o mot CUC TRI, va voi luoi nghich chieu dieu do co nghia: ro
        # mo ra o cuc tri thu nhat LUON duoc tang khong cu dao chieu ve cuc tri
        # thu hai. Do la duong rong da do duoc: random walk khong chi phi ra
        # +327% thay vi ~0. Ket thuc o C lam mat mon qua do.
        if st.tong_q > 0:
            bat_loi = Li if st.side > 0 else Hi
            thuan_loi = Hi if st.side > 0 else Li
            chang = (bat_loi, thuan_loi, Ci) if bi_quan else (thuan_loi, bat_loi, Ci)
        else:
            # dang rong thi khong co chieu nao de goi la "bat loi". Dung quy uoc
            # cua tester MT5 (nen tang: O->L->H, nen giam: O->H->L) lam ban goc,
            # `lac_quan` la ban dao lai - de `do_bat_bien` do duoc do nhay.
            x, y = (Li, Hi) if Ci >= Oi else (Hi, Li)
            chang = (x, y, Ci) if bi_quan else (y, x, Ci)
        diem = Oi
        for dich in chang:
            _chang(diem, dich, i)
            diem = dich

        # ---- mark-to-market cuoi bar
        if st.tong_q > 0:
            l = _lai(Ci)
            if cf.tp_mode == "trail" and l > st.dinh_lai:
                st.dinh_lai = l
            if cf.time_stop_bar and (i - st.bar_mo) >= cf.time_stop_bar:
                _dong_ro(Ci, i, "time")
                l = 0.0
        else:
            l = 0.0
        st.equity = 1.0 + st.thuc_hien + l - st.swap - st.chi_phi
        st.cap_nhat_dd()
        st.ghi_duong(i)
        # CHAY TAI KHOAN. Khong co chot nay thi equity di xuong am va engine van
        # chay tiep - moi so sau do la so cua mot tai khoan khong con ton tai.
        # Ho bot nay dinh dung cho do: `AGAINST` + tang size la duong thang toi no.
        if st.equity <= NGUONG_CHAY:
            st.chay_tai_khoan = True
            st.bar_chay = i
            if st.tong_q > 0:
                _dong_ro(Ci, i, "chay_tai_khoan")
            break

    # ---- ro chua dong o cuoi mau: MARK-TO-MARKET (muc 5.4)
    ro_treo = None
    if st.tong_q > 0:
        lai = _lai(cl[n - 1])
        ro_treo = {"so_tang": len(st.q), "lai_mtm": lai, "don_bay": st.tong_q * phoi,
                   "giu_bar": n - 1 - st.bar_mo}
        st.thuc_hien += lai
        st.chi_phi += (0.5 * sp[n - 1] + 0.5 * truot) * st.tong_q * phoi
        st.cac_ro.append({"bar_mo": st.bar_mo, "bar_dong": n - 1, "so_tang": len(st.q),
                          "loai": "MTM_cuoi_mau", "lai": lai,
                          "don_bay": st.tong_q * phoi, "side": st.side,
                          "giu_bar": n - 1 - st.bar_mo})
    st.equity = 1.0 + st.thuc_hien - st.swap - st.chi_phi
    return _chi_so(cf, st, df, ro_treo, pg)


def _QJ(size_mode: str, j: int, r: float) -> float:
    """q cua tang thu j (0 = tang dau). Ban vo huong cua `pmg.trong_so_size`."""
    if size_mode == "flat":
        return 1.0
    if size_mode == "linear":
        return float(j + 1)
    if size_mode == "geometric":
        return float(r ** j)
    if size_mode == "inverse":
        return 1.0 / (j + 1)
    raise ValueError(size_mode)


class _TrangThai:
    """Trang thai engine. Gom lai mot cho de closure khong phai `nonlocal` 20 bien."""

    __slots__ = ("neo", "atr_neo", "side", "dir_luoi", "e", "q", "A", "B", "tong_q",
                 "tong_qe", "muc_ke", "bar_mo", "dinh_lai", "eq_luc_mo", "thuc_hien",
                 "swap", "chi_phi", "equity", "cho_toi_bar", "neo_cho_move", "cac_ro",
                 "khe_truot", "duong", "dinh_don_bay", "dinh_so_tang", "dd_max",
                 "dinh_eq", "chay_tai_khoan", "bar_chay")

    def __init__(self):
        self.neo = None
        self.atr_neo = 0.0
        self.side = 0
        self.dir_luoi = 0
        self.e = []
        self.q = []
        self.A = self.B = self.tong_q = self.tong_qe = 0.0
        self.muc_ke = None
        self.bar_mo = 0
        self.dinh_lai = 0.0
        self.eq_luc_mo = 1.0
        self.thuc_hien = self.swap = self.chi_phi = 0.0
        self.equity = 1.0
        self.cho_toi_bar = 0
        self.neo_cho_move = None
        self.cac_ro = []
        self.khe_truot = []
        self.duong = None
        self.dinh_don_bay = 0.0
        self.dinh_so_tang = 0
        self.dd_max = 0.0
        self.dinh_eq = 1.0
        self.chay_tai_khoan = False
        self.bar_chay = -1

    def reset_ro(self):
        self.e.clear()
        self.q.clear()
        self.A = self.B = self.tong_q = self.tong_qe = 0.0
        self.side = self.dir_luoi = 0
        self.muc_ke = None
        self.dinh_lai = 0.0
        self.neo_cho_move = self.neo
        self.neo = None

    def cap_nhat_dd(self):
        if self.equity > self.dinh_eq:
            self.dinh_eq = self.equity
        dd = (self.dinh_eq - self.equity) / self.dinh_eq if self.dinh_eq > 0 else 0.0
        if dd > self.dd_max:
            self.dd_max = dd

    def ghi_duong(self, i):
        if self.duong is not None:
            self.duong[i] = self.equity


def _gop_both(a: dict, b: dict, cf) -> dict:
    """Gop hai ro doc lap cua DIRECTION=BOTH. Ke toan tach bach, chi cong so."""
    if a.get("loi") or b.get("loi"):
        return a if a.get("loi") else b
    r = dict(a)
    for k in ("so_ro", "so_lenh", "lai_tong", "swap_tich", "chi_phi_tich",
              "dinh_don_bay", "ro_moi_nam"):
        r[k] = a[k] + b[k]
    r["equity_cuoi"] = 1.0 + r["lai_tong"]
    r["dd_max"] = max(a["dd_max"], b["dd_max"])
    r["chay_tai_khoan"] = bool(a["chay_tai_khoan"] or b["chay_tai_khoan"])
    r["trang_thai"] = ("CHUA_DO_DUOC" if "CHUA_DO_DUOC" in (a["trang_thai"], b["trang_thai"])
                       else "DU")
    r["von_toi_thieu"] = r["dd_max"] * 1.5
    r["ma"] = cf.ma_dinh_danh()
    r["van_tay"] = cf.van_tay()
    r["ghi_chu"] = ("BOTH: dd_max la CHAN DUOI (max cua hai chan), khong phai do "
                    "tren chuoi equity gop - hai chan hedge nhau nen DD that nho hon")
    return r


def _chi_so(cf, st, df, ro_treo, pg) -> dict:
    equity = st.equity
    lai_tong = equity - 1.0
    so_ro = len(st.cac_ro)
    nam = max((df.index[-1] - df.index[0]).days / 365.25, 1e-9)
    lai_ro = [r["lai"] for r in st.cac_ro]
    kt = st.khe_truot
    out = {
        "ma": cf.ma_dinh_danh(),
        "van_tay": cf.van_tay(),
        "o": list(cf.o()),
        "so_ro": so_ro,
        "so_lenh": sum(r["so_tang"] for r in st.cac_ro),
        "ro_moi_nam": so_ro / nam,
        "lai_tong": lai_tong,
        "equity_cuoi": equity,
        "cagr": (equity ** (1.0 / nam) - 1.0) if equity > 0 else -1.0,
        "dd_max": st.dd_max,
        "ty_le_thang_ro": (sum(1 for x in lai_ro if x > 0) / so_ro) if so_ro else 0.0,
        "lai_ro_trung_vi": float(np.median(lai_ro)) if lai_ro else 0.0,
        "lai_ro_tb": float(np.mean(lai_ro)) if lai_ro else 0.0,
        "lai_ro_xau_nhat": float(min(lai_ro)) if lai_ro else 0.0,
        "giu_bar_trung_vi": (float(np.median([r["giu_bar"] for r in st.cac_ro]))
                             if st.cac_ro else 0.0),
        "dinh_don_bay": st.dinh_don_bay,
        "dinh_so_tang": st.dinh_so_tang,
        "swap_tich": st.swap,
        "chi_phi_tich": st.chi_phi,
        # dac ta muc 8.3: > 30% thi cau hinh nay la mot cuoc LAI SUAT, khong phai co che
        "swap_tren_lai": (abs(st.swap) / abs(lai_tong)) if lai_tong else float("inf"),
        "khe_truot_atr_tb": float(np.mean(kt)) if kt else 0.0,
        "khe_truot_atr_p95": float(np.percentile(kt, 95)) if kt else 0.0,
        "khe_truot_so_lan": len(kt),
        "ro_treo_cuoi_mau": ro_treo,
        # muc 3.3: von toi thieu de khong margin call o kich ban xau nhat x1.5
        "von_toi_thieu": st.dd_max * 1.5,
        "so_nam": nam,
        "ly_do_dong": _dem_loai(st.cac_ro),
        "chay_tai_khoan": st.chay_tai_khoan,
        "bar_chay": st.bar_chay,
        # ba trang thai, khong phai hai. `CHUA_DO_DUOC` thi moi con so o tren la
        # tao tac cua gia dinh duong di trong bar - khong duoc doc la AM hay DUONG.
        "trang_thai": pg["trang_thai"],
        "phan_giai": pg,
    }
    if st.duong is not None:
        out["duong_cong"] = st.duong
    return out


def _dem_loai(cac_ro) -> dict:
    d = {}
    for r in cac_ro:
        d[r["loai"]] = d.get(r["loai"], 0) + 1
    return d


# --------------------------------------------------- BAT BIEN VOI TIE-BREAK
def do_bat_bien(df, cf: "PMG.CauHinh", cp=None, atr_arr=None) -> dict:
    """Chay ca hai gia dinh thu tu cham trong bar va do khoang cach (muc 5.1).

    Dac ta cho phep dung bar THAY CHO tick chi khi chung minh duoc ket qua bat
    bien voi gia dinh bi quan nhat. Day la phep chung minh do - va no tra ve
    `dung_duoc=False` khi hai ban LAT DAU, nghia la moi so cua cau hinh do deu
    la tao tac cua gia dinh, khong phai cua thi truong.

    ## DOC `lai_than_trong`, DUNG DOC `lai_bi_quan`

    Ten `bi_quan` mo ta GIA DINH VE THU TU KHOP (cham cuc tri bat loi cho vi the
    hien co truoc), khong mo ta ket qua. Va chieu cua no **dao nguoc theo
    `direction`**:

      - `WITH`  : cham cuc tri bat loi truoc = ro breakout bi can truoc khi kip
                  nhoi them -> dung la ban te hon.
      - `AGAINST`: cham cuc tri bat loi truoc = **khop sau hon, nhieu tang hon o
                  gia tot hon**, roi cu hoi ve moi an TP -> ban nay LAI HON.

    Do 14/09/2026 tren cau hinh AUDCAD duy nhat song sot: `bi_quan` cho **+2,753%**
    con `lac_quan` cho **+0,199%** - chenh 14 lan, va ban mang ten "bi quan" lai la
    ban DEP hon. Doc nham cho no thi mot he bang khong thanh mot he co ve dung duoc.

    Nen luon doc `lai_than_trong = min(hai ban)`. `ban_than_trong` noi ban nao.
    """
    a = mo_phong(df, replace(cf, tie_break="bi_quan"), cp, atr_arr)
    b = mo_phong(df, replace(cf, tie_break="lac_quan"), cp, atr_arr)
    if a.get("loi") or b.get("loi"):
        return {"dung_duoc": False, "ly_do": a.get("loi") or b.get("loi")}
    la, lb = a["lai_tong"], b["lai_tong"]
    lat_dau = (la > 0) != (lb > 0)
    than_trong = "bi_quan" if la <= lb else "lac_quan"
    return {
        "dung_duoc": not lat_dau,
        "lat_dau": lat_dau,
        "lai_bi_quan": la,
        "lai_lac_quan": lb,
        # DOC CON SO NAY, KHONG DOC `lai_bi_quan`. Xem docstring - ban co ten
        # "bi quan" khong phai lúc nào cũng la ban cho ket qua te hon.
        "lai_than_trong": min(la, lb),
        "ban_than_trong": than_trong,
        "khoang_cach": abs(la - lb),
        "ty_le_bi_quan": (la / lb) if lb else float("nan"),
        "bi_quan": a,
        "lac_quan": b,
    }
