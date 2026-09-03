# -*- coding: utf-8 -*-
"""muc_tieu.py - CHIEN DICH THEO MUC TIEU. Day moi la "The Brain + QUANTLAB".

Quy trinh chu du an dat ra 03/09/2026, khi ong chi ra rang phien do da lam
SAI THU TU:

    Chu du an dua MOT muc tieu (vd: "US500CASH, 20-30 %/nam")
      |
      +-- LUONG 1  SEEKER chay HET CONG SUAT san moi he thong / chien luoc
      |            ve DUNG muc tieu do (SP500 noi chung, US500CASH noi rieng)
      |
      +-- LUONG 2  QUANTLAB boc tach - phan tich - backtest - CAN CHINH THAM SO
      |            nhung thu dao ve
      |
      +-- LUONG 3  NOI SINH: tu tim cach test nguoc lich su de ra chien luoc
                   cho chinh ma do, khong doi nguon ngoai

VI SAO CAN FILE NAY. Truoc no, "san theo muc tieu" khong ton tai nhu mot thao
tac. `seeker.mot_luot()` chay theo LICH (`nguon_den_han`) va lay tu khoa theo
DIEM (`tu_khoa_dung`), nen no san cai gi den han chu khong san cai ta dang
can. Do duoc 03/09/2026: kho 152 co che la thu thap CHUNG, va `TU_KHOA_GOC`
gom 15 tu deu chung chung (momentum factor, mean reversion equity...) —
**khong MOT tu nao ve SP500 / US500 / ES futures**. Quet cai kho do roi ket
luan "khong co gi cho SP500" la ket luan sai cho: he chua bao gio di tim.

Ba bat bien:
  1. **Ep tu khoa, khong ep cach cham diem.** Chien dich bom tu khoa vao bang
     `tu_khoa` voi diem cao; cham diem nang suat ve sau van chay nhu cu, nen
     mot tu khoa te se tu tut hang qua cac luot.
  2. **Bo qua LICH cua nguon, khong bo qua BACKOFF loi.** Chien dich la viec
     nguoi ra lenh, duoc uu tien hon chu ky; nhung nguon dang loi lien tuc
     thi van phai nhin.
  3. **Chien dich KHONG cham FDR.** No chi dua tai lieu va co che vao kho.
     Moi phep thu van phai di qua `cong` nhu thuong.
"""
from __future__ import annotations

import time

from nhan import so as SO

#: Tu khoa cho tung ma. Viet ra day chu khong sinh tu dong: mot bo tu khoa la
#: mot GIA THUYET ve noi kien thuc nam, va no phai doc duoc va sua duoc.
TU_KHOA_THEO_MA = {
    "US500CASH": [
        "S&P 500 trading strategy", "SPX trading strategy", "SPY trading strategy",
        "ES futures trading strategy", "emini S&P 500 strategy",
        "S&P 500 mean reversion", "S&P 500 momentum strategy",
        "S&P 500 backtest python", "US500 CFD strategy",
        "SPX overnight session edge", "S&P 500 intraday seasonality",
        "SPY gap fill strategy", "VIX S&P 500 timing signal",
        "S&P 500 turn of month effect", "S&P 500 volatility targeting",
        "index futures intraday strategy", "S&P 500 breadth indicator",
        "SPX options expiration effect", "S&P 500 trend following filter",
        "S&P 500 machine learning prediction",
    ],
    "XM_UK100CASH": [
        "FTSE 100 trading strategy", "UK100 CFD strategy",
        "FTSE 100 mean reversion", "FTSE 100 momentum strategy",
        "FTSE 100 backtest", "UK equity index seasonality",
        "FTSE 100 dividend adjustment CFD", "FTSE 100 overnight edge",
        "London session index strategy", "FTSE 100 gap strategy",
        "UK index futures strategy", "FTSE 100 volatility regime",
        "FTSE 100 vs S&P 500 spread", "UK100 intraday strategy",
        "FTSE 100 trend filter backtest",
    ],
    "XM_JP225CASH": [
        "Nikkei 225 trading strategy", "JP225 CFD strategy",
        "Nikkei 225 mean reversion", "Nikkei 225 momentum",
        "Japan equity index seasonality", "Nikkei overnight session edge",
        "Nikkei 225 futures strategy", "Nikkei 225 backtest",
        "Tokyo session index strategy", "Nikkei gap fill",
    ],
}


#: HE THONG GIAO DICH PHO THONG — san theo TEN RIENG, khong theo tai san.
#:
#: Vi sao can (chu du an chi ra 03/09/2026): *"sonic r van la cai toi goi y chu
#: chua phai he thong nay tim ra, trong khi sonic r ve muc do pho thong la qua
#: noi tieng trong bao nhieu nam nay roi"*. Do that trong kho 3.489 tai lieu:
#: "sonic" xuat hien **0 lan trong tieu de, 0 lan trong URL**, chi 5 lan trong
#: than bai. Mot he noi tieng ca chuc nam ma SEEKER trang tay - vi khong ai
#: bao no di tim theo TEN.
#:
#: Danh sach nay la mot GIA THUYET ve "nhung cai ai cung biet", va no phai sua
#: duoc bang tay. Cham diem nang suat cua `tu_khoa` se tu ha nhung ten vo bo.
HE_THONG_PHO_THONG = [
    "Sonic R trading system", "SonicR PAC dragon EMA34",
    "Turtle trading rules", "Ichimoku Kinko Hyo strategy",
    "Wyckoff accumulation distribution", "Elliott wave trading rules",
    "ICT inner circle trader model", "smart money concepts order block",
    "fair value gap trading", "supply and demand zone trading",
    "London breakout strategy", "opening range breakout ORB",
    "Bollinger band squeeze breakout", "Keltner channel strategy",
    "SuperTrend ATR strategy", "Heikin Ashi trend strategy",
    "Renko chart trading strategy", "pivot point trading rules",
    "VWAP mean reversion intraday", "three white soldiers candlestick strategy",
    "harmonic pattern Gartley Butterfly", "grid trading martingale system",
    "Donchian channel breakout", "Parabolic SAR trailing system",
    "MACD divergence strategy", "RSI-2 mean reversion Connors",
    "internal bar strength IBS strategy", "gap and go strategy",
    "seasonality turn of month strategy", "pairs trading statistical arbitrage",
]


def _cac_tu_khoa(ma: str, them: list[str] | None = None) -> list[str]:
    tk = list(TU_KHOA_THEO_MA.get(ma.upper(), []))
    for t in (them or []):
        if t not in tk:
            tk.append(t)
    if not tk:
        raise ValueError(
            f"khong co tu khoa cho {ma!r} - khai vao TU_KHOA_THEO_MA hoac "
            f"truyen qua tham so `them_tu_khoa`")
    return tk


def bom_tu_khoa(tu_khoa: list[str], diem: float = 10.0) -> int:
    """Dua tu khoa cua chien dich vao bang `tu_khoa` voi diem cao.

    Diem cao chi anh huong THU TU CHON (`seeker.tu_khoa_dung` sap theo
    `diem + so_ket_qua/(so_lan_dung+1)`). Cham diem nang suat ve sau khong bi
    dong bang: tu khoa te van tu tut hang qua cac luot.
    """
    them = 0
    with SO.ket_noi() as cn:
        for t in tu_khoa:
            cur = cn.execute(
                "INSERT OR IGNORE INTO tu_khoa(tu,linh_vuc,diem,sinh_tu,luc) "
                "VALUES(?,'tai_chinh',?,'muc_tieu',?)", (t, diem, SO.bay_gio()))
            them += cur.rowcount
            cn.execute("UPDATE tu_khoa SET diem=MAX(diem,?) WHERE tu=?", (diem, t))
    return them


class NoiTran:
    """Noi tran truy van cua TAT CA nguon, chi trong pham vi `with`.

    Truoc 03/09/2026 moi nguon hoi cung lam 2-3 tu khoa moi luot va con so do
    viet CUNG trong than tung ham. Voi 126 tu khoa trong bang, mot vong day du
    can ~50 luot. Do that tren TradingView: tu truoc den nay moi hoi 15 tu, va
    mot lan noi tran cho ngay 120 bai moi.

    Dung `with` chu khong sua file cau hinh: mot chien dich duoc quyen hoi
    nhieu, nhung SEEKER chay nen hang ngay thi van phai giu phanh chi phi va
    ton trong quota API cua tung nguon.
    """

    def __init__(self, so: int = 40):
        self.so = int(so)
        self._cu_nguon = None
        self._cu_tv = None

    def __enter__(self):
        from tru import seeker as SK
        self._cu_nguon = dict(SK.SO_TU_KHOA_MOI_NGUON)
        self._cu_tv = SK.TV_SO_TRUY_VAN_MOI_LUOT
        for k in SK.SO_TU_KHOA_MOI_NGUON:
            SK.SO_TU_KHOA_MOI_NGUON[k] = self.so
        SK.TV_SO_TRUY_VAN_MOI_LUOT = self.so
        return self

    def __exit__(self, *a):
        from tru import seeker as SK
        SK.SO_TU_KHOA_MOI_NGUON.clear()
        SK.SO_TU_KHOA_MOI_NGUON.update(self._cu_nguon)
        SK.TV_SO_TRUY_VAN_MOI_LUOT = self._cu_tv
        return False


def san(ma: str, ngan_sach_giay: int = 900, them_tu_khoa: list[str] | None = None,
        moi_nguon_toi_da: int = 0, toan_luc: int = 0, in_ra=print) -> dict:
    """LUONG 1 - SEEKER het cong suat theo mot muc tieu.

    Khac `seeker.mot_luot`: bo qua LICH cua nguon (chien dich uu tien hon chu
    ky) nhung VAN nhin backoff loi, va ep dung bo tu khoa cua muc tieu thay vi
    lay 6 tu theo diem.
    """
    from tru import seeker as SK

    t0 = time.time()
    tk = _cac_tu_khoa(ma, them_tu_khoa)
    bom_tu_khoa(tk)
    SK.dang_ky_nguon()
    tran = NoiTran(toan_luc) if toan_luc else None
    if tran:
        tran.__enter__()
        in_ra(f"  [toan luc] tran truy van moi nguon nang len {toan_luc}")

    # Nguon dang loi lien tuc thi van phai nhin (bat bien 2).
    hong = {r["ma"] for r in (SO.nhieu(
        "SELECT ma FROM nguon WHERE loi_lien_tuc >= 5") or [])}

    ten_nguon = [n for n in SK.NGUON if n not in hong]
    ten_nguon.sort(key=lambda n: SK.NGUON[n]["uu_tien"])
    if moi_nguon_toi_da:
        ten_nguon = ten_nguon[:moi_nguon_toi_da]

    chi_tiet, tong_moi = [], 0
    for i, ma_nguon in enumerate(ten_nguon):
        con = ngan_sach_giay - (time.time() - t0)
        if con <= 10:
            in_ra(f"  [het ngan sach] dung truoc {ma_nguon}")
            break
        # Xoay danh sach tu khoa cho tung nguon: nhieu nguon chi lay 2-3 tu dau
        # (`tu_khoa[:3]`), nen neu khong xoay thi 17/20 tu khong bao gio duoc hoi.
        k = len(tk)
        d = (i * 3) % k
        xoay = tk[d:] + tk[:d]
        try:
            ds = SK.NGUON[ma_nguon]["ham"](xoay)
            moi = SK.luu_tai_lieu(ma_nguon, ds)
            tong_moi += moi
            SO.chay("UPDATE nguon SET lan_cuoi=?, so_lan=so_lan+1, loi_lien_tuc=0, "
                    "thu_hoach=thu_hoach+? WHERE ma=?", time.time(), moi, ma_nguon)
            chi_tiet.append({"nguon": ma_nguon, "lay_ve": len(ds), "moi": moi})
            in_ra(f"  {ma_nguon:<18} lay ve {len(ds):>4}  moi {moi:>4}  "
                  f"({time.time() - t0:.0f}s)")
        except Exception as e:
            SO.chay("UPDATE nguon SET lan_cuoi=?, so_loi=so_loi+1, "
                    "loi_lien_tuc=loi_lien_tuc+1, ghi_chu=? WHERE ma=?",
                    time.time(), f"{type(e).__name__}: {str(e)[:100]}", ma_nguon)
            chi_tiet.append({"nguon": ma_nguon,
                             "loi": f"{type(e).__name__}: {str(e)[:60]}"})
            in_ra(f"  {ma_nguon:<18} LOI {type(e).__name__}: {str(e)[:56]}")

    # Cham diem nang suat cho chinh bo tu khoa nay.
    with SO.ket_noi() as cn:
        for t in tk:
            cn.execute("UPDATE tu_khoa SET so_lan_dung=so_lan_dung+1, "
                       "so_ket_qua=so_ket_qua+? WHERE tu=?",
                       (tong_moi // max(len(tk), 1), t))

    if tran:
        tran.__exit__()
    return {"ma": ma, "tu_khoa": len(tk), "nguon_chay": len(chi_tiet),
            "tai_lieu_moi": tong_moi, "giay": round(time.time() - t0, 1),
            "toan_luc": toan_luc,
            "chi_tiet": chi_tiet, "nguon_bo_qua_vi_loi": sorted(hong)}


def san_he_pho_thong(ngan_sach_giay: int = 1200, in_ra=print) -> dict:
    """San theo TEN HE THONG, khong theo tai san.

    Bo sung cho `san(ma)`: mot he noi tieng nhu Sonic R khong xuat hien duoi tu
    khoa "S&P 500 trading strategy" — phai goi dung ten no. Do that: 3.489 tai
    lieu trong kho co 0 tieu de nhac "sonic".
    """
    from tru import seeker as SK

    t0 = time.time()
    bom_tu_khoa(HE_THONG_PHO_THONG, diem=9.0)
    SK.dang_ky_nguon()
    hong = {r["ma"] for r in (SO.nhieu(
        "SELECT ma FROM nguon WHERE loi_lien_tuc >= 5") or [])}
    ten_nguon = [n for n in SK.NGUON if n not in hong]
    ten_nguon.sort(key=lambda n: SK.NGUON[n]["uu_tien"])

    tk = list(HE_THONG_PHO_THONG)
    chi_tiet, tong_moi = [], 0
    for i, ma_nguon in enumerate(ten_nguon):
        if ngan_sach_giay - (time.time() - t0) <= 10:
            in_ra(f"  [het ngan sach] dung truoc {ma_nguon}")
            break
        d = (i * 3) % len(tk)
        try:
            ds = SK.NGUON[ma_nguon]["ham"](tk[d:] + tk[:d])
            moi = SK.luu_tai_lieu(ma_nguon, ds)
            tong_moi += moi
            SO.chay("UPDATE nguon SET lan_cuoi=?, so_lan=so_lan+1, loi_lien_tuc=0, "
                    "thu_hoach=thu_hoach+? WHERE ma=?", time.time(), moi, ma_nguon)
            chi_tiet.append({"nguon": ma_nguon, "lay_ve": len(ds), "moi": moi})
            in_ra(f"  {ma_nguon:<18} lay ve {len(ds):>4}  moi {moi:>4}  "
                  f"({time.time() - t0:.0f}s)")
        except Exception as e:
            SO.chay("UPDATE nguon SET lan_cuoi=?, so_loi=so_loi+1, "
                    "loi_lien_tuc=loi_lien_tuc+1, ghi_chu=? WHERE ma=?",
                    time.time(), f"{type(e).__name__}: {str(e)[:100]}", ma_nguon)
            in_ra(f"  {ma_nguon:<18} LOI {type(e).__name__}: {str(e)[:56]}")
    return {"tu_khoa": len(tk), "nguon_chay": len(chi_tiet),
            "tai_lieu_moi": tong_moi, "giay": round(time.time() - t0, 1),
            "chi_tiet": chi_tiet}


def boc(gioi_han_doc: int = 40, gioi_han_co_che: int = 25,
        ngan_sach_giay: int = 600, in_ra=print) -> dict:
    """LUONG 2 (nua dau) - doc toan van nhung gi vua dao ve, roi boc ra co che.

    Nua sau cua luong 2 (backtest + can chinh tham so) la viec cua QUANTLAB va
    da co san: `tru.quantlab` + `do_on_dinh` + `nhan.bien_don_bay`.
    """
    from tru import seeker as SK
    t0 = time.time()
    doc = SK.doc_toan_van(gioi_han=gioi_han_doc,
                          ngan_sach_giay=int(ngan_sach_giay * 0.6))
    in_ra(f"  doc toan van: {doc}")
    co_che = SK.boc_co_che(gioi_han=gioi_han_co_che)
    in_ra(f"  boc co che  : {co_che}")
    return {"doc": doc, "co_che": co_che, "giay": round(time.time() - t0, 1)}


def chien_dich(ma: str, ngan_sach_san: int = 900, ngan_sach_boc: int = 600,
               in_ra=print) -> dict:
    """Luong 1 + nua dau luong 2, mot lenh."""
    from nhan import ngu_phap as NP
    truoc = len(NP.doc_kho())
    in_ra(f"=== CHIEN DICH: {ma} ===")
    in_ra(f"kho co che truoc: {truoc}")
    in_ra("-- LUONG 1: SEEKER san theo muc tieu --")
    s = san(ma, ngan_sach_giay=ngan_sach_san, in_ra=in_ra)
    in_ra(f"   -> {s['tai_lieu_moi']} tai lieu moi tu {s['nguon_chay']} nguon "
          f"({s['giay']}s)")
    in_ra("-- LUONG 2a: doc toan van + boc co che --")
    b = boc(ngan_sach_giay=ngan_sach_boc, in_ra=in_ra)
    sau = len(NP.doc_kho())
    in_ra(f"kho co che sau: {sau}  (+{sau - truoc})")
    return {"san": s, "boc": b, "co_che_truoc": truoc, "co_che_sau": sau,
            "co_che_them": sau - truoc}
