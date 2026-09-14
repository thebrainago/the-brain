# -*- coding: utf-8 -*-
"""pmg.py - POSITION MANAGEMENT GRID ENGINE. Ho quan li lenh KHONG CO TIN HIEU VAO.

## Vi sao module nay ton tai

Chu du an giao dac ta `PMG v0.2 (14/09/2026)` qua LUONG UU TIEN, va noi ro no
thuoc **module quan li lenh**. Doc cung hai cho khac:

  - `SO_DO_HE_THONG.txt`: *"viec su dung ky thuat quan li lenh tot con hon viec
    co 1 entry tot"*
  - ban giao 13/09 muc 4.B'.2: *"co nhung kieu danh chi dung quan li lenh loi
    dung su di chuyen cua gia de chot rat nhanh 1 lenh"* -> bench cu SAI KHUNG
    vi no gan quan tri len mot engine vao co dinh roi hoi "them quan tri thi doi
    gi". PMG la **ho khong can tin hieu vao** ma ban giao doi.

## Mot cau phai thuoc truoc khi doc so nao cua file nay

Engine khong co entry signal. Duoi gia thuyet random walk ky vong cua no bang
dung `-chi phi`. Nen moi con so duong deu phai tra loi duoc: *bat doi xung that
o dung timescale cua buoc luoi nam o dau?* Do la viec cua `pmg_g0.py` (cong G0),
va G0 co **quyen phu quyet** ca ho chien luoc tren mot (tai san x scale).

## Bon thu file nay lam, khong lam thu thu nam

    1. KHONG GIAN THAM SO  `CauHinh` - 7 khoi cua dac ta, ma dinh danh + van tay
    2. TOAN HOC            `d_be` (khoang cach hoan von) - dong kin, co test
    3. CONG G1             `kiem_g1` - loai cau hinh VO NGHIEM truoc khi ton CPU
    4. ENGINE              `mo_phong` - mo phong ro tren bar, hai kieu tie-break

Khong lam: khong cham MT5 (TESTER=1 la rang buoc vat li), khong tu quet lon
(viec cua `pmg_quet.py`), khong tu ket luan PASS (viec cua `cong.py`).

## Ba cai bay cua rieng ho bot nay - xu li o dau

  - **Thu tu cham trong bar**: bar khong noi gia cham muc nao truoc. Engine chay
    duoc CA HAI kieu (`bi_quan` / `lac_quan`); `do_bat_bien` do khoang cach giua
    hai ket qua. Ket qua chi duoc tin khi hai kieu khong lat dau -> day la cach
    thay the cho tick data ma dac ta doi (muc 5.1).
  - **Khe gia**: tang luoi nam trong khe khop tai **open sau khe**, khong tai gia
    tang. Basket stop cung danh gia tai open sau khe (muc 8.4).
  - **Ro chua dong o cuoi mau**: mark-to-market, khong bo qua. Khong co cho nay
    thi MOI cau hinh `AGAINST` deu dep gia tao (muc 5.4).

Chay:  python -m nhan.pmg --dbe
       python -m nhan.pmg --thu US500CASH
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

RA = LAB / "reports"

# ---------------------------------------------------------------- MIEN GIA TRI
#: Moi mien duoi day lay NGUYEN VAN tu dac ta v0.2. Doi mien la doi gia thuyet,
#: nen phai sua o day chu khong rai rac trong ma - va moi lan sua phai ghi vao
#: prereg cua o, vi so phep thu deu dem o cong G5.
MIEN = {
    "anchor_mode":   ("static", "trailing", "session"),
    "direction":     ("WITH", "AGAINST", "BOTH"),
    "step_mode":     ("fixed", "expanding", "vol_adaptive"),
    "size_mode":     ("flat", "linear", "geometric", "inverse"),
    "tp_mode":       ("avg_plus", "money", "trail", "anchor_return"),
    "rearm":         ("immediate", "cooldown", "require_move"),
    "tie_break":     ("bi_quan", "lac_quan"),
}
MIEN_SO = {
    "h":              (0.1, 3.0),      # x ATR  - dac ta muc 1.3
    "reanchor_dist":  (0.25, 2.0),
    "step_g":         (1.0, 1.6),
    "size_r":         (1.2, 2.0),
    "tp_dist":        (0.1, 2.0),
    "trail_giveback": (0.10, 0.60),
    "max_legs":       (3, 40),
    "max_basket_dd":  (0.005, 0.08),   # phan cua equity
    "hard_sl_atr":    (2.0, 15.0),
}

#: Bucket phien theo GIO SAN (MT5 server = Europe/Helsinki, tu no da co DST).
#: Dac ta cam dinh nghia phien bang offset UTC co dinh; dung gio san la cach
#: dung DST duy nhat ma khong phai tu quy doi lay.
PHIEN = {
    "ROLLOVER":     (0, 0),
    "ASIA_QUIET":   (1, 8),
    "LONDON_OPEN":  (9, 11),
    "LONDON_MID":   (12, 15),
    "NY_OPEN":      (16, 17),
    "NY_MID":       (18, 21),
    "NY_CLOSE":     (22, 23),
}
PHIEN_TAT_CA = "ALL"
CAC_PHIEN = tuple(PHIEN) + ("WEEKEND_EDGE",)


def bucket_phien(index) -> np.ndarray:
    """Mang ten bucket cho tung bar. WEEKEND_EDGE de len tren cac bucket gio."""
    gio = np.asarray(index.hour)
    thu = np.asarray(index.dayofweek)          # 0 = thu Hai
    ten = np.full(len(gio), "LONDON_MID", dtype=object)
    for b, (a, z) in PHIEN.items():
        ten[(gio >= a) & (gio <= z)] = b
    ria = ((thu == 4) & (gio >= 22)) | ((thu == 0) & (gio <= 2))
    ten[ria] = "WEEKEND_EDGE"
    return ten


# ------------------------------------------------------------------- CAU HINH
@dataclass(frozen=True)
class CauHinh:
    """Mot diem trong khong gian 7 chieu cua dac ta. Bat bien de hash duoc."""
    ma: str
    phien: str = PHIEN_TAT_CA
    atr_tf: str = "H1"
    atr_period: int = 14
    # 1.1 ANCHOR
    anchor_mode: str = "static"
    reanchor_dist: float = 1.0
    # 1.2 DIRECTION
    direction: str = "AGAINST"
    # 1.3 STEP
    h: float = 0.5
    step_mode: str = "fixed"
    step_g: float = 1.0
    # 1.4 SIZE
    size_mode: str = "flat"
    size_r: float = 2.0
    # 1.5 BASKET EXIT
    tp_mode: str = "avg_plus"
    tp_dist: float = 0.5
    tp_money: float = 0.01           # chi dung khi tp_mode = money (frac equity)
    trail_giveback: float = 0.30
    # 1.6 BASKET STOP - khong duoc bo trong (dac ta muc 1.6)
    max_legs: int = 10
    max_basket_dd: float = 0.03      # frac equity, 0 = tat
    time_stop_bar: int = 240         # 0 = tat
    hard_sl_atr: float = 6.0         # 0 = tat
    # 1.7 RE-ARM
    rearm: str = "immediate"
    rearm_n: float = 0               # so bar cooldown, hoac x ATR neu require_move
    # ngoai 7 khoi
    eod_flatten: bool = False        # ep dong ro o bien phien (muc 8.2.2)
    phoi_nhiem_1: float = 1.0        # phoi nhiem cua tang 0 theo equity dau
    tie_break: str = "bi_quan"

    # -------------------------------------------------------------- dinh danh
    def ma_dinh_danh(self) -> str:
        """Dac ta muc 8.7, CO SUA: them cac tham so SO ma ban goc bo sot.

        Ban nguyen van cua dac ta la:

            PMG-{asset}-{session}-{atr_tf}-h{h}-{direction}-{step_mode}
                -{size_mode}-tp{tp_mode}-st{stop_mode}

        Chuoi do **khong phan biet duoc `tp_dist`** (cung nhu `size_r`, `step_g`).
        Tuc hai cau hinh khac han nhau - vi du `tp_dist = 0,5` va `tp_dist = 2,0`
        tren cung mot luoi - cho ra y het mot ma. Va dac ta lai noi (§8.7): *"Hash
        rut gon tu chuoi nay lam khoa dedupe. Bat buoc, neu khong QuantLab se chay
        trung hang nghin lan"*. Dung ma nay lam khoa dedupe thi ta khong chay trung
        - ta **danh roi im lang** moi bien the `tp_dist` tru mot cai.

        Lo hong nay tu no lo ra: ngay 14/09 toi dung ma nay de dung lai cau hinh
        duy nhat song sot cua AUDCAD, dung nham `tp_dist`, va ra mot ket qua khac
        han (-0,169%/nam thay vi +0,20%/nam).

        Nen o day them `tp_dist`, va them `size_r` / `step_g` khi chung co nghia.
        Khoa dedupe THAT van la `van_tay()` - hash cua TOAN BO dataclass, khong
        phai chuoi nay; chuoi nay de NGUOI doc.
        """
        sm = self.size_mode + (f"{self.size_r:g}" if self.size_mode == "geometric" else "")
        st = self.step_mode + (f"{self.step_g:g}" if self.step_mode == "expanding" else "")
        tp = self.tp_mode + (f"{self.tp_money:g}" if self.tp_mode == "money"
                             else f"{self.trail_giveback:g}" if self.tp_mode == "trail"
                             else f"{self.tp_dist:g}")
        return (f"PMG-{self.ma}-{self.phien}-{self.atr_tf}-h{self.h:g}"
                f"-{self.direction}-{st}-{sm}-tp{tp}-st{self.che_do_stop()}")

    def che_do_stop(self) -> str:
        p = []
        if self.max_basket_dd:
            p.append(f"dd{self.max_basket_dd:g}")
        if self.time_stop_bar:
            p.append(f"t{self.time_stop_bar:g}")
        if self.hard_sl_atr:
            p.append(f"sl{self.hard_sl_atr:g}")
        p.append(f"n{self.max_legs}")
        return ".".join(p)

    def van_tay(self) -> str:
        s = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)
        return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

    def o(self) -> tuple:
        """`O` nghien cuu theo dac ta muc 8: (tai san, phien, scale)."""
        return (self.ma, self.phien, self.atr_tf)


# --------------------------------------------------------- 3.1 TOAN HOC D_BE
def trong_so_size(size_mode: str, n: int, r: float = 2.0) -> np.ndarray:
    """q cua tung tang; chi so j = 0 tai tang GAN GOC LUOI nhat (lenh dau tien)."""
    j = np.arange(n, dtype=float)
    if size_mode == "flat":
        return np.ones(n)
    if size_mode == "linear":
        return j + 1.0
    if size_mode == "geometric":
        return r ** j
    if size_mode == "inverse":
        return 1.0 / (j + 1.0)
    raise ValueError(f"size_mode la gi: {size_mode}")


def khoang_cach_tang(n: int, h: float, step_mode: str = "fixed",
                     g: float = 1.0) -> np.ndarray:
    """Khoang cach tu goc luoi toi tung tang. d[0] = h (tang dau cach goc 1 buoc)."""
    j = np.arange(n, dtype=float)
    if step_mode == "expanding" and g != 1.0:
        # h_k = h * g^k la khoang cach giua tang k va k+1 -> cong don
        return h * (g ** (j + 1.0) - 1.0) / (g - 1.0)
    return h * (j + 1.0)


def d_be(size_mode: str, n: int, h: float = 1.0, r: float = 2.0,
         step_mode: str = "fixed", g: float = 1.0) -> float:
    """Khoang cach tu LENH CUOI CUNG toi gia von binh quan (dac ta muc 3.1).

        D_BE = sum(k * q_k) / sum(q_k) * h     , k = 0 tai lenh MOI NHAT

    Day la bien quyet dinh song chet cua mot cau hinh: o che do `anchor_return`,
    neu quang duong ve goc luoi khong vuot D_BE + chi phi thi ro **khong bao gio**
    co duong thoat duong, va khong can ton mot giay backtest nao de biet dieu do.

    Ket qua dong da doi chieu voi dac ta (test_pmg.py giu cac moc nay):
        geometric r=2, n -> lon :  D_BE -> h     (1 bac, khong phu thuoc n)
        linear n=8              :  D_BE = 2.333 h
        flat   n                :  D_BE = (n-1) h / 2
        inverse                 :  tang theo n
    """
    if n <= 1:
        return 0.0
    q = trong_so_size(size_mode, n, r)
    d = khoang_cach_tang(n, h, step_mode, g)
    k = d[-1] - d                      # quang duong tu tang j toi tang cuoi
    return float((k * q).sum() / q.sum())


# ------------------------------------------------------------------- CONG G1
def kiem_g1(cf: CauHinh, spread_frac: float = 0.0, truot_frac: float = 0.0,
            atr_frac: float = 0.01) -> dict:
    """Loai cau hinh VO NGHIEM truoc khi ton mot giay backtest (dac ta G1).

    `atr_frac` = ATR chia gia (ATR duoi dang PHAN CUA GIA) - vi moi khoang cach
    trong cau hinh deu theo boi so ATR, con chi phi theo phan cua gia.

    DAC TA NOI MOT DIEU KIEN, THUC TE NO TACH LAM HAI. Phai noi ro cho nguoi doc
    sau, vi cho nay de ap nham roi loai sach cau hinh tot:

      - `anchor_return` / `trail`: gia phai di HET quang duong tu lenh cuoi ve
        diem thoat, nen dieu kien la `quang_duong_thoat > D_BE + chi phi`. Day
        dung la cau trong dac ta.
      - `avg_plus`: diem thoat DUOC DINH NGHIA tu gia von binh quan, nen lai moi
        don vi luon bang dung `tp_dist` bat ke D_BE bao nhieu. Rang buoc that la
        `tp_dist > chi phi mot vong`. Ap cau cua dac ta vao day se loai nham moi
        cau hinh DCA sau tang - dung cai ma M2 dang chay that.

    Va mot luat khong nhan nhuong: **cau hinh khong co BASKET STOP THAT thi loai
    ngay** - `max_legs` mot minh KHONG phai stop, no chi la tran phoi nhiem.
    """
    ly_do = []
    for k, mien in MIEN.items():
        v = getattr(cf, k, None)
        if v is not None and v not in mien:
            ly_do.append(f"{k}={v!r} ngoai mien {mien}")
    for k, (lo, hi) in MIEN_SO.items():
        v = getattr(cf, k, None)
        if v is None or v == 0:
            continue
        if not (lo <= v <= hi):
            ly_do.append(f"{k}={v:g} ngoai mien [{lo:g}, {hi:g}]")

    # muc 1.6: phai co it nhat MOT stop that
    if not (cf.max_basket_dd or cf.time_stop_bar or cf.hard_sl_atr):
        ly_do.append("KHONG CO BASKET STOP (max_legs khong phai stop) - dac ta muc 1.6")

    # `anchor_return` chi co nghia voi luoi NGHICH chieu. Voi `WITH` cac tang nam
    # PHIA SAU goc luoi theo huong vi the, nen "gia quay ve goc" la mot khoan LO
    # chac chan, khong phai mot TP. Dac ta khong noi, nhung hai o nay ghep lai
    # cho ra mot cau hinh khong bao gio lai duoc - loai o G1 chu dung de no an CPU.
    if cf.tp_mode == "anchor_return" and cf.direction == "WITH":
        ly_do.append("tp=anchor_return + direction=WITH: gia ve goc luoi la LO, khong phai TP")

    # muc 3.1 + 3.2: co duong thoat duong khong
    chi_phi_don_vi = spread_frac + truot_frac          # mot vong / mot don vi
    chi_phi_atr = chi_phi_don_vi / atr_frac if atr_frac > 0 else float("inf")
    dbe = d_be(cf.size_mode, cf.max_legs, cf.h, cf.size_r, cf.step_mode, cf.step_g)
    if cf.tp_mode in ("anchor_return", "trail"):
        quang_duong = (khoang_cach_tang(cf.max_legs, cf.h, cf.step_mode, cf.step_g)[-1]
                       if cf.tp_mode == "anchor_return" else cf.tp_dist)
        if quang_duong <= dbe + chi_phi_atr:
            ly_do.append(f"vo nghiem: quang duong thoat {quang_duong:.3f} ATR <= "
                         f"D_BE {dbe:.3f} + chi phi {chi_phi_atr:.3f} ATR")
    else:
        if cf.tp_dist <= chi_phi_atr:
            ly_do.append(f"vo nghiem: tp_dist {cf.tp_dist:.3f} ATR <= chi phi mot vong "
                         f"{chi_phi_atr:.3f} ATR")

    q = trong_so_size(cf.size_mode, cf.max_legs, cf.size_r)
    return {
        "kha_thi": not ly_do,
        "ly_do": ly_do,
        "d_be_atr": dbe,
        "chi_phi_atr": chi_phi_atr,
        "don_bay_dinh": float(q.sum()) * cf.phoi_nhiem_1,
        "ma": cf.ma_dinh_danh(),
        "van_tay": cf.van_tay(),
    }


# --------------------------------------------------------------------- ATR
def atr(high, low, close, period: int = 14) -> np.ndarray:
    """ATR Wilder. Tra ve mang cung do dai, `period` phan tu dau la NaN."""
    h = np.asarray(high, float)
    l = np.asarray(low, float)
    c = np.asarray(close, float)
    n = len(h)
    out = np.full(n, np.nan)
    if n <= period:
        return out
    tr = np.empty(n)
    tr[0] = h[0] - l[0]
    pc = c[:-1]
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - pc), np.abs(l[1:] - pc)))
    out[period] = tr[1:period + 1].mean()
    a = 1.0 / period
    for i in range(period + 1, n):
        out[i] = out[i - 1] + a * (tr[i] - out[i - 1])
    return out
