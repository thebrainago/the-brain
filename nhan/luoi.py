# -*- coding: utf-8 -*-
"""luoi.py - MO PHONG LUOI/DCA CO TRACH NHIEM, dung duoc lai cho moi cap.

Chu du an 05/09/2026: *"Neu la audcad thi gio cau tim he thong, tinh chinh thong
so cho ra cai tot nhat di. Day chinh la cai toi muon ve quantlab => phat hien ra
tiem nang => backtest thi nghiem ra thong so => he thong"*.

Tiem nang den tu `luan_nguoc`: 13/19 tai khoan DCA song >= 2 nam tren bang xep
hang mql5 danh AUDCAD (nen 28%, p = 0,00035).

## VI SAO KHONG DUNG LAI `ultima_luoi_backtest.py`

Ban do co luat DAY DU va dung, nhung hai cho khong dung duoc:
  1. No chay tren **D1**. Bo nho du an: *"D1 thoi loi suat 11,7 lan"* - luoi bat
     tang theo duong di TRONG bar, ma bar D1 giau het duong di do.
  2. No uoc von = dinh lo treo cua hai ro cong lai, roi lay lai/von lam loi
     suat. Do la mot con SO, khong phai mot duong von: khong co margin call,
     khong co sut giam theo thoi gian, khong biet bao gio chay tai khoan.

## LUAT MO PHONG - khai bao TRUOC khi chay, khong doi giua chung

  1. Khung M15/M5/M1, gia OHLC. Trong MOT bar xu ly **BAT LOI TRUOC**: them
     tang truoc, xet TP sau. Neu mot bar cham ca hai thi coi nhu bi them tang
     truoc roi moi chot - gia dinh THAN TRONG.
  2. `che_do`: `mua` (chi ro mua), `ban`, hoac `hai_chieu` (hai ro doc lap).
  3. **Lot PHANG** moi tang. KHONG nhan lot. Martingale da bi kho du an bac bo:
     Lottery Mode x1,3 bien +54.354 thanh -1.550 voi DD 94,4%.
  4. Them mot tang khi gia di nguoc `buoc` pip so voi tang GAN NHAT.
  5. Dong CA RO khi gia cham gia trung binh +/- `tp` pip.
  6. `tran_tang`: cham tran thi NGUNG them tang (van giu, van cho TP). Day la
     tham so quan trong nhat cua lop nay - no la thu duy nhat chan duoi.
  7. **Khong cat lo**, nhung CO stop-out: equity <= `muc_stopout` x margin thi
     dong het va ghi CHAY. Do la cach tai khoan that chet, phai mo phong.
  8. Chi phi: spread THAT tung bar (cot `spread` cua M5/M15 AUDCAD co that -
     `do_tin=SAN`) tru moi lan mo; phi qua dem theo SO DEM x SO VI THE x CHIEU.
     AUDCAD bat doi xung manh: giu MUA -0,263%/nam (ta DUOC tra), giu BAN
     +3,853%/nam. Bo qua cho nay la thoi lai cua luoi hai chieu.
  9. Lai KHONG tai dau tu (lot phang) -> loi suat tinh tren VON, va von la
     tham so, khong phai ket qua.

## DON VI

Tinh het bang **dong tien BAO GIA** (CAD voi AUDCAD). Loi suat la ty so nen
khong phu thuoc quy doi - tranh han cai bay "doi dong tien tai khoan".
1 pip = 0,0001. Voi 0,01 lot: 1 pip = 0,01 x 100.000 x 0,0001 = 1,0 don vi bao gia.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

PIP = 1e-4
HOP_DONG = 100_000.0


@dataclass
class ThamSo:
    buoc: float = 60.0          # pip, khoang cach giua cac tang
    tp: float = 40.0            # pip, TP tinh tu gia trung binh
    tran_tang: int = 20         # toi da bao nhieu tang moi ro
    che_do: str = "hai_chieu"   # mua | ban | hai_chieu
    lot: float = 0.01
    muc_stopout: float = 0.5    # equity <= 0,5 x margin -> chay
    don_bay: float = 100.0
    #: Sau khi mot ro chot TP, KHONG mo lai L1 ngay tai do ma cho gia LUI
    #: `cho_lui` pip nguoc chieu roi moi vao. 0 = mo lai ngay (ban goc).
    #: Bo nho `eurcad-entry-cho-lui`: tren tester MT5 THAT, luat nay nang
    #: EURCAD tu 7,9% len 12,1%/nam VA giam sut giam - va no lat nguoc ket
    #: luan cua ban Python truoc do rang "entry vo dung".
    cho_lui: float = 0.0
    #: TANG LOT THEO TANG - chu du an cho phep 05/09: *"Cho phep tang lot, cho
    #: phep dca. Chi can tinh sao ra con so rui ro vua phai van duoc"*.
    #: `phang` = lot deu (ban goc, an toan nhat).
    #: `nhan`  = lot_i = lot * he_so^(i-1)      (nhan luy thua - martingale)
    #: `cong`  = lot_i = lot * (1 + he_so*(i-1)) (tang tuyen tinh - hien hon)
    #: Kho du an da bac bo martingale MOT LAN roi: Lottery Mode x1,3 tren LOT
    #: bien +54.354 thanh -1.550 voi DD 94,4%. Nhung do la martingale sau khi
    #: THUA MOT LENH, khac han tang lot theo TANG LUOI (o day gia da di nguoc
    #: that va tang moi co gia tot hon). Hai thu khac nhau nen phai do lai,
    #: khong duoc suy tu ket qua kia.
    kieu_lot: str = "phang"
    he_so_lot: float = 1.0


@dataclass
class KetQuaLuoi:
    lai_rong: float = 0.0
    lai_gop: float = 0.0
    phi_spread: float = 0.0
    phi_swap: float = 0.0
    so_ro: int = 0
    so_lenh: int = 0
    tang_max: int = 0
    lo_treo_dinh: float = 0.0        # don vi bao gia
    chay: bool = False
    bar_chay: int | None = None
    so_nam: float = 0.0
    duong_equity: np.ndarray | None = field(default=None, repr=False)


def _mot_ro(hi, lo, cl, spread_gia, dem, chieu: int, ts: ThamSo):
    """Mo phong MOT ro. Tra (lai_cong_don_theo_bar, lo_treo_theo_bar, thong ke).

    `lai_cong_don_theo_bar` la lai DA CHOT tich luy (rong phi) den tung bar.
    `lo_treo_theo_bar` la lo chua chot cua cac tang dang mo tai bar do.
    Tach hai cai nay ra vi equity = von + lai_chot - lo_treo, va chi co cach
    do moi kiem duoc margin call.
    """
    n = len(cl)
    gia_pip = ts.lot * HOP_DONG * PIP          # gia tri 1 pip cua 1 tang
    b = ts.buoc * PIP
    t = ts.tp * PIP
    # phi qua dem: ty le/nam tren notional, theo chieu
    ty_le = -0.00263 if chieu > 0 else 0.03853
    notional_1 = ts.lot * HOP_DONG             # tinh bang dong CO SO
    def _lot(k: int) -> float:
        """Lot cua tang thu k (0-based)."""
        if ts.kieu_lot == "nhan":
            return ts.lot * (ts.he_so_lot ** k)
        if ts.kieu_lot == "cong":
            return ts.lot * (1.0 + ts.he_so_lot * k)
        return ts.lot

    vao = [cl[0]]
    cho = 0.0          # != 0: dang CHO gia lui toi muc nay moi mo L1
    lai = 0.0
    phi_sp = 0.0
    phi_sw = 0.0
    so_ro = so_lenh = 0
    tang_max = 1
    lai_arr = np.empty(n)
    treo_arr = np.empty(n)
    # phi mo lenh dau
    phi_sp += spread_gia[0] * ts.lot * HOP_DONG
    so_lenh += 1
    tong_lot = ts.lot
    for i in range(1, n):
        # ---- 0. dang CHO gia lui de mo L1 ----
        if cho:
            if (lo[i] <= cho) if chieu > 0 else (hi[i] >= cho):
                vao = [cho]
                so_lenh += 1
                phi_sp += spread_gia[i] * _lot(0) * HOP_DONG
                cho = 0.0
            else:
                lai_arr[i] = lai - phi_sp - phi_sw
                treo_arr[i] = 0.0
                continue
        # ---- 1. BAT LOI TRUOC: them tang ----
        if len(vao) < ts.tran_tang:
            moc = vao[-1] - chieu * b
            while (lo[i] <= moc if chieu > 0 else hi[i] >= moc):
                phi_sp += spread_gia[i] * _lot(len(vao)) * HOP_DONG
                vao.append(moc)
                so_lenh += 1
                if len(vao) >= ts.tran_tang:
                    break
                moc = moc - chieu * b
        if not vao:
            lai_arr[i] = lai - phi_sp - phi_sw
            treo_arr[i] = 0.0
            continue
        if len(vao) > tang_max:
            tang_max = len(vao)
        # ---- 2. phi qua dem cho cac tang dang mo ----
        tong_lot = sum(_lot(k) for k in range(len(vao)))
        if dem[i]:
            phi_sw += tong_lot * HOP_DONG * ty_le * dem[i] / 365.0 * cl[i]
        # ---- 3. lo treo sau nhat trong bar ----
        xau = lo[i] if chieu > 0 else hi[i]
        treo = 0.0
        for k, v in enumerate(vao):
            d = chieu * (v - xau)
            if d > 0:
                treo += d * _lot(k)
        treo_arr[i] = treo * HOP_DONG
        # ---- 4. TP tu gia trung binh ----
        # gia trung binh CO TRONG SO LOT - do la ca co che cua DCA: tang sau
        # lot to hon keo gia trung binh ve gan gia hien tai nhanh hon.
        tb = sum(_lot(k) * v for k, v in enumerate(vao)) / tong_lot
        mtp = tb + chieu * t
        if (hi[i] >= mtp) if chieu > 0 else (lo[i] <= mtp):
            lai += tong_lot * HOP_DONG * t
            so_ro += 1
            treo_arr[i] = 0.0
            if ts.cho_lui > 0:
                # khong mo lai ngay: dat moc cho gia lui `cho_lui` pip
                cho = mtp - chieu * ts.cho_lui * PIP
                vao = []
            else:
                vao = [mtp]
                so_lenh += 1
                phi_sp += spread_gia[i] * _lot(0) * HOP_DONG
        lai_arr[i] = lai - phi_sp - phi_sw
    lai_arr[0] = -phi_sp
    treo_arr[0] = 0.0
    return lai_arr, treo_arr, {
        "lai_gop": lai, "phi_spread": phi_sp, "phi_swap": phi_sw,
        "so_ro": so_ro, "so_lenh": so_lenh, "tang_max": tang_max,
        "con_mo": len(vao)}


def chay(df, ts: ThamSo, von: float) -> KetQuaLuoi:
    """Mo phong day du tren mot khung du lieu. `von` bang dong BAO GIA."""
    hi = df["high"].to_numpy(float)
    lo = df["low"].to_numpy(float)
    cl = df["close"].to_numpy(float)
    if "spread" in df.columns:
        # cot spread la POINT; AUDCAD point = 1e-5
        sp = df["spread"].to_numpy(float) * 1e-5
        sp = np.where(sp > 0, sp, np.nanmedian(sp[sp > 0]) if (sp > 0).any() else 2e-4)
    else:
        sp = np.full(len(df), 2e-4)
    idx = df.index
    dem = np.zeros(len(df))
    dem[1:] = np.diff(idx.values).astype("timedelta64[s]").astype(float) / 86400.0

    chieus = {"mua": (1,), "ban": (-1,), "hai_chieu": (1, -1)}[ts.che_do]
    lais, treos, tks = [], [], []
    for c in chieus:
        a, b, k = _mot_ro(hi, lo, cl, sp, dem, c, ts)
        lais.append(a)
        treos.append(b)
        tks.append(k)
    lai = np.sum(lais, axis=0)
    treo = np.sum(treos, axis=0)

    equity = von + lai - treo
    # margin: so tang dang mo x notional / don bay. Xap xi bang tang_max de
    # khong phai luu so tang tung bar - THAN TRONG vi margin bi uoc CAO.
    def _lot_k(k):
        if ts.kieu_lot == "nhan":
            return ts.lot * (ts.he_so_lot ** k)
        if ts.kieu_lot == "cong":
            return ts.lot * (1.0 + ts.he_so_lot * k)
        return ts.lot
    lot_tong = sum(sum(_lot_k(j) for j in range(k["tang_max"])) for k in tks)
    margin = lot_tong * HOP_DONG * float(np.mean(cl)) / ts.don_bay
    chay_o = np.flatnonzero(equity <= ts.muc_stopout * margin)
    bar_chay = int(chay_o[0]) if len(chay_o) else None
    if bar_chay is not None:
        equity = equity.copy()
        equity[bar_chay:] = 0.0

    so_nam = max((idx[-1] - idx[0]).days / 365.25, 1e-9)
    return KetQuaLuoi(
        lai_rong=float(lai[-1]),
        lai_gop=sum(k["lai_gop"] for k in tks),
        phi_spread=sum(k["phi_spread"] for k in tks),
        phi_swap=sum(k["phi_swap"] for k in tks),
        so_ro=sum(k["so_ro"] for k in tks),
        so_lenh=sum(k["so_lenh"] for k in tks),
        tang_max=max(k["tang_max"] for k in tks),
        lo_treo_dinh=float(np.max(treo)),
        chay=bar_chay is not None, bar_chay=bar_chay,
        so_nam=so_nam, duong_equity=equity)


def chi_so(kq: KetQuaLuoi, von: float) -> dict:
    """Chi so doc duoc tu duong von. CAGR tren VON, khong tai dau tu."""
    e = kq.duong_equity
    dinh = np.maximum.accumulate(e)
    dd = float(np.min(np.where(dinh > 0, e / np.maximum(dinh, 1e-9) - 1.0, -1.0)))
    lai_nam = kq.lai_rong / kq.so_nam
    return {
        "loi_suat_nam_pct": lai_nam / von * 100.0,
        "maxdd_pct": dd * 100.0,
        "lo_treo_dinh_pct_von": kq.lo_treo_dinh / von * 100.0,
        "ro_nam": kq.so_ro / kq.so_nam,
        "lenh_nam": kq.so_lenh / kq.so_nam,
        "tang_max": kq.tang_max,
        "chay": kq.chay,
        "phi_tren_lai_gop_pct": (
            (kq.phi_spread + kq.phi_swap) / kq.lai_gop * 100.0
            if kq.lai_gop > 0 else float("nan")),
        "calmar": (lai_nam / von) / abs(dd) if dd < 0 else float("inf"),
    }
