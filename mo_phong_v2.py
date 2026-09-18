# -*- coding: utf-8 -*-
"""
mo_phong_v2.py - Bo mo phong luoi DCA v2, gom co che tu CAC HE THONG NGOAI
===========================================================================
Nguon y tuong (nguoi dung nhac dung: phan lon core den tu he thong ngoai):
  - Ultima (do nguoc 537 ro)          : luoi buoc co dinh, lot phang, TP tu gia TB
  - DCA Am Duong (clip tac gia)       : loc Supertrend + loc KHOANG CACH gia-ST
  - US500_Hedge_DCA_EA.mq5 (may user) : mo CA HAI chieu, chot BEN THANG, DCA BEN THUA
  - T91 Bigmouse / T95 HedgingCover   : he so nhan THEO NHOM (2,0 cho 4 lenh dau roi
                                        1,6), CAT HOA kich hoat theo SO LENH,
                                        Target_Exit_All / Max_CutLoss_All theo TIEN,
                                        Buy va Sell mo CACH NHAU mot khoang
  - nguoi dung                        : chot doi xung tung phan, chap nhan DD de giam von

================== LUAT DAY DU (khong de mac dinh ngam) ==================
MO RO   : khi ro rong -> mo Buy tai gia + kc_bs/2, Sell tai gia - kc_bs/2.
          kc_bs = 0 nghia la mo cung gia.
NAP THEM: gia di nguoc >= buoc * he_so_buoc^(i-1) so voi lenh sau nhat -> them lenh.
LOT     : lenh thu i (0-indexed):
            i < nhom_dau : LOT * he_so_1^i
            i >= nhom_dau: LOT * he_so_1^(nhom_dau-1) * he_so_2^(i-nhom_dau+1)
          he_so_1 = he_so_2 = 1 -> lot phang.
CAT HOA : chi bat khi ro co >= cat_hoa_tu lenh. Khi bat: ghep lenh moi nhat voi
          lenh dau tien, dong ca cap khi tong >= bien_cap pip. Toi da cap_moi_nen
          cap moi nen.
CHOT    : (a) TP theo pip tu gia trung binh, HOAC
          (b) chot_tien: dong ca ro khi lai noi >= X USD  (Target_Exit_All)
DUNG LO : lo noi ca hai ro >= dung_lo -> dong sach (Max_CutLoss_All)
TRAN    : tang_toi_da lenh moi ro, lot_toi_da tong lot
MA SAT  : spread THAT tung nen · swap x3 thu Tu · truot gia cho lenh thi truong
"""
from pathlib import Path

import numpy as np
import pandas as pd

KHO = Path(__file__).parent / "data"
PV = 0.0714
PIP = 0.0001
LOT = 0.01
SWAP_NGAY = 0.0474


def nap(cap="EURCAD", pv=None):
    m = pd.read_parquet(KHO / f"{cap}_M1_mq.parquet")
    return {
        "hi": m["high"].to_numpy(), "lo": m["low"].to_numpy(),
        "c": m["close"].to_numpy(),
        "sp": (m["spread"].to_numpy() / 10.0).astype(np.float32),
        "thu": m["time"].dt.dayofweek.to_numpy().astype(np.int8),
        "nam": (m["time"].max() - m["time"].min()).days / 365.25,
        "pv": PV if pv is None else pv, "cap": cap,
        "n": len(m),
    }


def _lot_tang(i, he_so_1, nhom_dau, he_so_2, lot_sau_l1=None):
    """lot_sau_l1: neu dat, L1 giu LOT (lenh tham do) con MOI tang tu L2 tro di
    dung LOT * lot_sau_l1 — PHANG voi nhau, khong luy tien. Day la y 'L1 la lenh
    tham do': L1 vao mu (167 luat entry deu vo dung) nen de nho; tu L2 moi co
    thong tin (gia da lech mot buoc) nen moi cam ket von."""
    if lot_sau_l1 is not None:
        return LOT if i == 0 else LOT * lot_sau_l1
    if i < nhom_dau:
        return LOT * he_so_1 ** i
    return LOT * he_so_1 ** (nhom_dau - 1) * he_so_2 ** (i - nhom_dau + 1)


def mo_phong(d, buoc=20.0, tp=13.0, he_so_buoc=1.0, buoc_tran=400.0,
             he_so_1=1.0, nhom_dau=4, he_so_2=1.0,
             cat_hoa_tu=2, bien_cap=0.0, cap_moi_nen=999,
             chot_tien=None, dung_lo=1000.0,
             tang_toi_da=200, lot_toi_da=15.0, kc_bs=0.0, truot=0.3,
             cho_phep=None, tp_nhanh=None, kia_ket_tu=6,
             hedge_tu=None, hedge_ty=1.0, hedge_go=0.0,
             cho_lui=0.0, cho_toi_da=0, nghi_sau_chot=0, lech_ema=None, lot_sau_l1=None,
             entry_nguoc=False,
             thoat_sau_bar=0, vol_min=None, vol_max=None, vol_ngan=20, vol_dai=200,
             trailing_tu=None, trailing_buoc=10.0, breakeven_tu=None,
             tra_duong_von=False):
    """cho_lui/cho_toi_da : thay vi vao L1 tai gia thi truong, dat lenh CHO cach
                            gia hien tai `cho_lui` pip ve phia co loi, cho toi da
                            `cho_toi_da` nen; het han thi vao thi truong.
                            cho_toi_da = 0 nghia la cho vo han (chi vao khi khop).
       nghi_sau_chot       : so nen phai nghi sau khi mot ro dong moi duoc mo lai.
       lech_ema            : neu dat, chi mo ro MUA khi gia duoi EMA(lech_ema),
                            chi mo ro BAN khi gia tren EMA -> luoi bat doi xung."""
    """tp_nhanh/kia_ket_tu: y tuong tu US500_Hedge_DCA_EA — khi ro BEN KIA da ket
    (>= kia_ket_tu lenh) thi ro ben nay chot SOM o tp_nhanh pip thay vi cho tp,
    de lay tien ve nuoi ben dang ket. Khong bat chuoc nguyen: EA goc dong han ben
    thang roi nhoi lot x2 vao ben thua; o day chi ha muc chot."""
    hi, lo, c, sp, thu = d["hi"], d["lo"], d["c"], d["sp"], d["thu"]
    PV = d.get("pv", 0.0714)
    n = d["n"]
    swap_phut = SWAP_NGAY / 1440.0

    gia = {1: [], -1: []}
    lot = {1: [], -1: []}
    tlot = {1: 0.0, -1: 0.0}
    tgl = {1: 0.0, -1: 0.0}
    cuoi = {1: 0.0, -1: 0.0}

    # KHOA LO (hedge lock): mo vi the NGUOC chieu de dong bang lo cua ro dang ket.
    # khoa[ch] = (lot khoa, gia mo khoa). Go khi gia hoi hedge_go pip.
    khoa = {1: None, -1: None}
    #: bar mo ro hien tai - de dong ro theo THOI GIAN (GridEA: InpMaxCycleHours=72).
    #: Day la cach chan duoi HOAN TOAN KHAC chan theo tien: khong hoi "lo bao
    #: nhieu" ma hoi "ket bao lau roi". Mot ro ket 3 ngay tren cap neo-ve-trung-
    #: binh la tin hieu che do da doi, khong phai tin hieu can them tang.
    mo_luc = {1: 0, -1: 0}
    #: gia TOT NHAT ro da cham ke tu khi mo - de dat moc trailing.
    dinh_ro = {1: None, -1: None}
    so_thoat_gio = so_trailing = so_hoa_von = 0
    cho_dat = {1: None, -1: None}
    mo_lai_tu = {1: 0, -1: 0}
    ema_gia = None
    if lech_ema is not None:
        ema_gia = pd.Series(c).ewm(span=lech_ema, adjust=False).mean().to_numpy()
    # CONG BIEN DONG (GridEA: InpMin/MaxVolatilityRatio) - chi mo ro MOI khi
    # bien dong ngan han nam trong dai so voi bien dong dai han. Luoi chet trong
    # che do bien dong cao; cong nay khong cuu ro dang mo, no chi ngung MO THEM.
    ty_vol = None
    if vol_min is not None or vol_max is not None:
        bd = pd.Series(hi - lo)
        ty_vol = (bd.rolling(vol_ngan).mean()
                  / bd.rolling(vol_dai).mean().replace(0, np.nan)).to_numpy()
    so_khoa = 0
    lai = 0.0
    dem_ro = so_cap = so_cat = 0
    tang_max = 0
    lot_max = 0.0
    lich_vt = np.zeros(n, dtype=np.float32)
    con_lai = []

    for i in range(1, n):
        lo_tong = 0.0
        for ch in (1, -1):
            g, l = gia[ch], lot[ch]
            if not g:
                if cho_phep is not None and not cho_phep[i]:
                    continue
                if i < mo_lai_tu[ch]:            # dang nghi sau khi chot
                    continue
                if ty_vol is not None:
                    v = ty_vol[i]
                    if not np.isfinite(v):
                        continue
                    if vol_min is not None and v < vol_min:
                        continue
                    if vol_max is not None and v > vol_max:
                        continue
                # `entry_nguoc=True`: DAO NGUOC bo loc entry - mo ro MUA khi gia
                # TREN EMA (dung luc te nhat cho mot ro mua). Dung de tra loi cau
                # hoi cua chu du an 05/09: *"quan li vi the tot thi entry sai van
                # co loi"*. Neu ket qua voi entry DAO NGUOC van duong thi entry
                # that su khong phai thu quyet dinh o lop nay.
                _dau = -1.0 if entry_nguoc else 1.0
                if lech_ema is not None and _dau * ch * (ema_gia[i] - c[i]) <= 0:
                    continue                      # luoi bat doi xung
                if cho_lui > 0:
                    # dat lenh CHO cach gia hien tai cho_lui pip ve phia co loi
                    if cho_dat[ch] is None:
                        cho_dat[ch] = (c[i] - ch * cho_lui * PIP, i)
                    muc_cho, t_dat = cho_dat[ch]
                    khop = lo[i] <= muc_cho if ch > 0 else hi[i] >= muc_cho
                    het_han = cho_toi_da > 0 and (i - t_dat) >= cho_toi_da
                    if khop:
                        p0 = muc_cho
                        lai -= sp[i] * PV        # lenh cho -> khong truot
                        cho_dat[ch] = None
                    elif het_han:
                        p0 = c[i] + ch * truot * PIP
                        lai -= (sp[i] + truot) * PV
                        cho_dat[ch] = None
                    else:
                        continue
                else:
                    p0 = c[i] + ch * (kc_bs / 2.0 + truot) * PIP
                    lai -= (sp[i] + truot) * PV
                g.append(p0)
                l.append(LOT)
                tlot[ch] = LOT
                tgl[ch] = p0 * LOT
                cuoi[ch] = p0
                mo_luc[ch] = i
                dinh_ro[ch] = p0
                continue
            # --- nap them tang ---
            kc = min(buoc * he_so_buoc ** (len(g) - 1), buoc_tran)
            moc = cuoi[ch] - ch * kc * PIP
            while (lo[i] <= moc if ch > 0 else hi[i] >= moc):
                if len(g) >= tang_toi_da or tlot[ch] >= lot_toi_da:
                    break
                lt = _lot_tang(len(g), he_so_1, nhom_dau, he_so_2, lot_sau_l1)
                g.append(moc)
                l.append(lt)
                tlot[ch] += lt
                tgl[ch] += moc * lt
                cuoi[ch] = moc
                lai -= sp[i] * PV * (lt / LOT)
                kc = min(buoc * he_so_buoc ** (len(g) - 1), buoc_tran)
                moc -= ch * kc * PIP
            if len(g) > tang_max:
                tang_max = len(g)
            if tlot[ch] > lot_max:
                lot_max = tlot[ch]
            lai -= (tlot[ch] / LOT) * swap_phut * (3.0 if thu[i] == 2 else 1.0)
            tb = tgl[ch] / tlot[ch]
            xau = lo[i] if ch > 0 else hi[i]
            lo_ro = ch * (xau - tb) / PIP * (tlot[ch] / LOT) * PV
            # --- KHOA LO: mo vi the nguoc chieu khi ro da ket ---
            if hedge_tu is not None:
                if khoa[ch] is None and len(g) >= hedge_tu:
                    lk = tlot[ch] * hedge_ty
                    khoa[ch] = (lk, c[i] - ch * truot * PIP)
                    lai -= (sp[i] + truot) * PV * (lk / LOT)
                    so_khoa += 1
                elif khoa[ch] is not None:
                    lk, gk = khoa[ch]
                    # khoa lai/lo NGUOC chieu ro
                    lai_khoa = -ch * (c[i] - gk) / PIP * (lk / LOT) * PV
                    lo_ro += lai_khoa
                    # go khoa khi ro da hoi (khoa dang lo hedge_go pip)
                    if -ch * (c[i] - gk) / PIP <= -hedge_go:
                        lai += lai_khoa - truot * PV * (lk / LOT)
                        khoa[ch] = None
            lo_tong += min(lo_ro, 0.0)
            # --- CAT HOA: chi bat khi ro du lon (Bigmouse: Solenh_KichhoatCatHoa) ---
            if len(g) >= max(2, cat_hoa_tu):
                tot = hi[i] if ch > 0 else lo[i]
                da = 0
                while len(g) >= 2 and da < cap_moi_nen:
                    a = ch * (tot - g[-1]) / PIP * (l[-1] / LOT)
                    b = ch * (tot - g[0]) / PIP * (l[0] / LOT)
                    if (a + b) < bien_cap:
                        break
                    lai += (a + b) * PV
                    so_cap += 1
                    da += 1
                    tlot[ch] -= l[-1] + l[0]
                    tgl[ch] -= g[-1] * l[-1] + g[0] * l[0]
                    del g[-1], l[-1]
                    del g[0], l[0]
                    if g:
                        cuoi[ch] = g[-1]
                if da:
                    con_lai.append(len(g))
                if not g:
                    dem_ro += 1
                    tlot[ch] = tgl[ch] = 0.0
                    mo_lai_tu[ch] = i + nghi_sau_chot
                    continue
                tb = tgl[ch] / tlot[ch]
            # --- TRAILING / BREAKEVEN: tinh tren GIA TRUNG BINH cua ro ---
            if trailing_tu is not None or breakeven_tu is not None:
                # MOC tinh tu dinh DEN BAR TRUOC. Cap nhat dinh bang gia tot
                # nhat cua CHINH bar nay roi kiem moc trong cung bar la NHIN
                # TRUOC: no gia dinh dinh den truoc day. Do 05/09 khi mac loi
                # do: AUDCAD ra 6.557%/nam voi von can 41 USD - so gia.
                if dinh_ro[ch] is None:
                    dinh_ro[ch] = c[i]
                lai_dinh = ch * (dinh_ro[ch] - tb) / PIP
                moc_dong = None
                if trailing_tu is not None and lai_dinh >= trailing_tu:
                    moc_dong = dinh_ro[ch] - ch * trailing_buoc * PIP
                elif breakeven_tu is not None and lai_dinh >= breakeven_tu:
                    moc_dong = tb
                if moc_dong is not None:
                    xau_bar = lo[i] if ch > 0 else hi[i]
                    if (xau_bar <= moc_dong) if ch > 0 else (xau_bar >= moc_dong):
                        lai += ch * (moc_dong - tb) / PIP * (tlot[ch] / LOT) * PV
                        lai -= (sp[i] + truot) * PV * (tlot[ch] / LOT)
                        if khoa[ch] is not None:
                            lk, gk = khoa[ch]
                            lai += -ch * (c[i] - gk) / PIP * (lk / LOT) * PV
                            khoa[ch] = None
                        g.clear()
                        l.clear()
                        tlot[ch] = tgl[ch] = 0.0
                        dinh_ro[ch] = None
                        dem_ro += 1
                        if trailing_tu is not None and lai_dinh >= trailing_tu:
                            so_trailing += 1
                        else:
                            so_hoa_von += 1
                        mo_lai_tu[ch] = i + nghi_sau_chot
                        continue
                # ro van mo -> gio moi cap nhat dinh bang bar nay, de bar SAU
                # dung no lam moc.
                tot_bar = hi[i] if ch > 0 else lo[i]
                dinh_ro[ch] = (max(dinh_ro[ch], tot_bar) if ch > 0
                               else min(dinh_ro[ch], tot_bar))
            # --- THOAT THEO THOI GIAN: dong ro sau X bar BAT KE lai lo ---
            if thoat_sau_bar and (i - mo_luc[ch]) >= thoat_sau_bar:
                lai += ch * (c[i] - tb) / PIP * (tlot[ch] / LOT) * PV
                lai -= (sp[i] + truot) * PV * (tlot[ch] / LOT)
                if khoa[ch] is not None:
                    lk, gk = khoa[ch]
                    lai += -ch * (c[i] - gk) / PIP * (lk / LOT) * PV
                    lai -= truot * PV * (lk / LOT)
                    khoa[ch] = None
                g.clear(); l.clear()
                tlot[ch] = tgl[ch] = 0.0
                dem_ro += 1
                so_thoat_gio += 1
                mo_lai_tu[ch] = i + nghi_sau_chot
                continue
            # --- CHOT: theo TIEN hoac theo PIP ---
            tot = hi[i] if ch > 0 else lo[i]
            if chot_tien is not None:
                if ch * (tot - tb) / PIP * (tlot[ch] / LOT) * PV >= chot_tien:
                    lai += chot_tien
                    g.clear(); l.clear()
                    tlot[ch] = tgl[ch] = 0.0
                    dem_ro += 1
                    continue
            # ben kia ket -> ha muc chot cua ben nay de lay tien ve
            tp_ap = tp
            if tp_nhanh is not None and len(gia[-ch]) >= kia_ket_tu:
                tp_ap = tp_nhanh
            # ro dong -> go khoa neu con
            if khoa[ch] is not None and False:
                pass
            muc = tb + ch * tp_ap * PIP
            if (hi[i] >= muc if ch > 0 else lo[i] <= muc):
                lai += ch * (muc - tb) / PIP * (tlot[ch] / LOT) * PV
                g.clear(); l.clear()
                tlot[ch] = tgl[ch] = 0.0
                dem_ro += 1
                mo_lai_tu[ch] = i + nghi_sau_chot
        # --- DUNG LO toan bo ---
        if -lo_tong >= dung_lo:
            lai += lo_tong - (tlot[1] + tlot[-1]) / LOT * truot * PV
            so_cat += 1
            for ch in (1, -1):
                gia[ch].clear(); lot[ch].clear()
                tlot[ch] = tgl[ch] = 0.0
            lo_tong = -dung_lo
        lich_vt[i] = lai + lo_tong

    so_nam = d["nam"]
    sut = np.maximum.accumulate(lich_vt) - lich_vt
    dd = float(sut.max())
    duoi = sut > 1e-9
    dai = cur = 0
    for v in duoi:
        cur = cur + 1 if v else 0
        if cur > dai:
            dai = cur
    cl = np.array(con_lai) if con_lai else np.array([0])
    return {
        "lai_nam": lai / so_nam, "von": dd,
        "ls": lai / so_nam / dd * 100 if dd > 0 else np.nan,
        "ro_nam": dem_ro / so_nam, "cap_nam": so_cap / so_nam,
        "thoat_gio_nam": so_thoat_gio / so_nam,
        "trailing_nam": so_trailing / so_nam,
        "hoa_von_nam": so_hoa_von / so_nam,
        "cat_nam": so_cat / so_nam, "tang_max": tang_max, "lot_max": lot_max,
        "khoa_nam": so_khoa / so_nam,
        "lenh_tuan": (so_cap * 2 + dem_ro) / so_nam / 52,
        "hoi_von_ngay": dai / 1440.0,
        "pct_duoi_dinh": float(duoi.mean() * 100),
        "giua_tv": float(np.median(cl)),
        **({"duong_von": lich_vt} if tra_duong_von else {}),
    }
