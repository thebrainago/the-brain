# -*- coding: utf-8 -*-
"""cong_ra_tien.py - CONG THU HAI. Hoi "co ra tien khong", khong hoi "co that khong".

Chu du an 05/09/2026: *"thay doi quan diem ve viec phai chap nhan he thong dca,
chap nhan DD cao hon. Con neu cu tim he single shot ma dat duoc cac tieu chi thi
cac to chuc tai chinh ho da lam truoc roi"*.

## RANH GIOI VOI `vao_lenh.moc_dd20` (ghi 12/09/2026 - DOC TRUOC KHI SUA)

Hai ham cung tim don bay bang CHIA DOI de khop mot muc sut giam, va chung
KHONG trung nhau:

    `cong_ra_tien.mua_giu_khop_dd`  chi MUA-GIU (`np.ones`). La mot phan cua
                                    CONG - di kem nguong MUC_CAGR/TRAN_DD/
                                    MIN_LENH/MIN_NAM va luoi DON_BAY.
    `vao_lenh.moc_dd20`             `max(mua-giu, BAN-GIU, tien mat)`. La MOC
                                    cua PHEU `to_hop`, khong co nguong nao.

Voi he long/short thi lay mot minh mua-giu lam moc la SAI (sua 11/09): ban-giu
khong phai anh guong cua mua-giu vi phi qua dem bat doi xung. Nen trong pheu
dung `moc_dd20`; o cong thi `mua_giu_khop_dd` du vi cong con hoi them nhieu thu.
**Dung hop nhat hai ham** - chung phuc vu hai cau hoi khac nhau.

DAY LA CONG THU HAI, KHONG PHAI CONG CU NOI LONG. Hai cong hoi hai cau khac
nhau va khong duoc tron:

    `nhan/cong.py`      "co phai mot phat hien that khong?"  -> placebo, FDR,
                        alpha co y nghia, thang mua-giu o cung BIEN DONG.
    `cong_ra_tien.py`   "co ra tien tren tai khoan CUA TA khong?" -> lai, sut
                        giam trong nguong ta chiu duoc, va song du lau de thu.

Mot he qua cong nay ma truot cong kia thi phai goi dung ten: **mot canh bac co
ky vong duong do duoc tren holdout, chua phai mot phat hien**. Ghi ro trong
ket qua bang `da_qua_cong_that`.

## Lap luan cua chu du an dung o dau, va sai o dau

DUNG: to chuc tai chinh bi hai rang buoc ma tai khoan ca nhan khong bi -
**suc chua** (khong trien khai duoc chien luoc chi om vai chuc nghin dollar) va
**nguong sut giam** (-60% la ket thuc mot quy vi nguoi ta rut von, nhung khong
ket thuc mot tai khoan ca nhan da biet truoc). Goc con lai la giao cua hai dieu
do. Do la mot luan diem that va no doi cach cham diem.

PHAI CAN THAN: *"chap nhan DD cao"* tu no KHONG phai edge. Tran loi suat
`0,5 * Sharpe^2` van rang buoc. Chap nhan DD cao chi cho phep dung DON BAY cao
hon tren cung mot edge - va **mua-giu cung duoc dung don bay do**. Neu bo phep
so voi mua-giu thi cai con lai chi la beta co don bay, va ta se "phat hien" ra
no mai mai.

## Nen phep so voi mua-giu duoc DOI, khong bo

Cong cu so o cung BIEN DONG (`cong.py`, he so khop rui ro k). Cong nay so o
**cung SUT GIAM TOI DA** - vi sut giam moi la thu chu du an khai la chiu duoc,
khong phai bien dong. Va hai phep so cho ket qua khac han nhau: mua-giu NASDAQ
o L=2 cho 2,08%/nam voi DD -97,6%, tuc **o muc DD 60% thi mua-giu co don bay
la mot doi thu yeu han** so voi khi so theo bien dong.

Do chinh la khe cua so mo ra khi chap nhan DD cao. No that, va no do duoc.

## 25/09/2026: CHU DU AN CHOT TIEU CHI DUYET - so voi mua-giu xuong NHAN

Nguyen van: *"toi khong quan tam martingale hay dca hay la phuong phap gi. Toi
trade don bay toi chap nhan rui ro, chi can co lai va maxdd duoi 80% la ok"*.

Nen: `1_lai` = CAGR > 0 (`MUC_CAGR` = 0; 20%/nam con la muc TIEU cua
`cham_diem`, khong phai nguong duyet), `2_sut_giam` = maxDD DUOI `TRAN_DD` =
`cham_diem.TRAN_SUT_GIAM` (80%). Tieu chi 3 KHONG bi xoa: van tinh va tra trong
`nhan` voi ten `3_hon_mua_giu_cung_DD`, chi khong con chan. Canh bao ben duoi
van dung - bo chan thi "beta co don bay" qua duoc cong nay - nen bang nao doc
ket qua cong nay PHAI hien nhan do (`bang_he` hien "KHONG hon mua-giu").

## Sau tieu chi, khai bao TRUOC (ban 05/09 - xem muc 25/09 o tren)

  1. `lai`        CAGR >= `MUC_CAGR` sau chi phi that, o don bay duoc chon.
  2. `sut_giam`   maxDD <= `TRAN_DD`. Nguong nay la KHAI BAO CUA CHU DU AN,
                  khong phai do tu du lieu.
  3. `hon_mua_giu_cung_DD`  CAGR > CAGR cua mua-giu duoc don bay len DUNG muc
                  sut giam cua he. Day la tieu chi khong duoc bo.
  4. `du_lenh`    so lenh >= `MIN_LENH`. Chan "mua-giu doi ten" - mot he 1
                  lenh/15 nam khong phai he thong (quy tac cua chu du an).
  5. `khong_chay` khong bar nao lam von ve 0 trong ky.
  6. `song_du`    so nam du lieu >= `MIN_NAM`. Voi lop DCA/gong lo, day la
                  tieu chi NANG nhat: mot lop song bang cach hiem khi thua thi
                  doan chua co cu thua khong noi gi.

KHONG co o cong nay, va co y: Sharpe, Calmar, placebo, FDR. Chung thuoc cong
that. Mot he DCA co Sharpe cao tren doan chua sap la chuyen binh thuong, nen
Sharpe o day chi gay hieu nham.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhan import bien_don_bay as B
from nhan import cham_diem as CD
from nhan import chi_phi as CP
from nhan import mo_phong as MP

#: Nguong DUYET lai: 25/09 chu du an chot "chi can co lai" -> CAGR > 0. (Muc tieu
#: 20%/nam dat 04/09 van la `cham_diem.MUC_LAI` - muc tieu, khong phai cong.)
MUC_CAGR = 0.0
#: Tran sut giam chu du an khai la chiu duoc: 60% (04/09) -> 70% (05/09) -> 80%
#: (25/09). Doc tu MOT nguon `cham_diem.TRAN_SUT_GIAM`, khong go lai o day.
TRAN_DD = CD.TRAN_SUT_GIAM / 100.0
#: Duoi muc nay thi khong phai he thong, la mua-giu doi ten.
MIN_LENH = 20
#: Duoi muc nay thi khong ket luan duoc gi ve lop chiu lo treo.
MIN_NAM = 8.0
#: Cac muc don bay thu. Khong toi uu - chi lay muc THAP NHAT dat muc tieu.
DON_BAY = (1.0, 1.5, 2.0, 3.0, 4.0, 5.0)


def _dd(von: np.ndarray) -> float:
    dinh = np.maximum.accumulate(np.maximum(von, 1e-300))
    return float((von / dinh - 1.0).min())


#: Luoi don bay de dung BANG mua-giu mot lan cho moi tai san. Quet rong cham
#: hang nghin ung vien tren cung mot ma, ma bang nay chi phu thuoc (ma, khung,
#: cua so) - tinh lai cho tung ung vien la lang phi 20 lan.
LUOI_BH = (0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0,
           3.5, 4.0, 5.0, 6.0, 8.0, 10.0, 14.0, 20.0)


def bang_mua_giu(df: pd.DataFrame, cp, ma: str = "", khung: str = "D1") -> list[dict]:
    """(don_bay, cagr, maxdd) cua mua-giu tren luoi `LUOI_BH`. Tinh MOT lan/ma."""
    ra = []
    for L in LUOI_BH:
        kq = MP.chay(df, np.ones(len(df)), cp, ma=ma, khung=khung,
                     don_bay=float(L), gop="so_hoc")
        c = B._chi_so(kq)
        ra.append({"don_bay": float(L), "cagr": c["cagr"], "maxdd": c["maxdd"],
                   "sharpe": c["sharpe"], "chay": c["chay"]})
    return ra


def tra_khop_dd(bang: list[dict], dd_muc_tieu: float) -> dict:
    """Mua-giu o dung muc sut giam `dd_muc_tieu`, noi suy tren bang.

    |maxDD| tang don dieu theo don bay nen noi suy tuyen tinh giua hai moc ke
    nhau la du. Neu muc DD cua he SAU HON ca moc cao nhat thi lay moc cao nhat
    (khong ngoai suy - ngoai suy o day se bia ra mot doi thu manh gia).
    """
    d = abs(dd_muc_tieu)
    hop_le = [b for b in bang if not b["chay"]]
    if not hop_le:
        return {"don_bay": None, "cagr": -1.0, "maxdd": None, "ngoai_bang": True}
    hop_le.sort(key=lambda b: abs(b["maxdd"]))
    if d <= abs(hop_le[0]["maxdd"]):
        return {**hop_le[0], "ngoai_bang": True}
    if d >= abs(hop_le[-1]["maxdd"]):
        return {**hop_le[-1], "ngoai_bang": True}
    for a, b in zip(hop_le, hop_le[1:]):
        da, db = abs(a["maxdd"]), abs(b["maxdd"])
        if da <= d <= db:
            w = 0.0 if db == da else (d - da) / (db - da)
            return {"don_bay": a["don_bay"] + w * (b["don_bay"] - a["don_bay"]),
                    "cagr": a["cagr"] + w * (b["cagr"] - a["cagr"]),
                    "maxdd": -d, "sharpe": a["sharpe"] + w * (b["sharpe"] - a["sharpe"]),
                    "ngoai_bang": False}
    return {**hop_le[-1], "ngoai_bang": True}


def mua_giu_khop_dd(df: pd.DataFrame, cp, dd_muc_tieu: float, ma: str = "",
                    khung: str = "D1") -> dict:
    """Mua-giu duoc don bay len DUNG muc sut giam `dd_muc_tieu`. Tra chi so cua no.

    Vi sao phai tim don bay chu khong lay L=1: chu du an chap nhan DD cao, nen
    doi thu that su khong phai mua-giu tran ma la **mua-giu co don bay den cung
    muc DD do**. Khong lam buoc nay thi moi he DD cao deu "thang mua-giu" mot
    cach tam thuong.

    Tim bang chia doi tren L, vi |maxDD| tang don dieu theo don bay.
    """
    def thu(L: float) -> dict:
        kq = MP.chay(df, np.ones(len(df)), cp, ma=ma, khung=khung,
                     don_bay=float(L), gop="so_hoc")
        return B._chi_so(kq)

    lo, hi = 1.0, 20.0
    c_lo = thu(lo)
    if abs(c_lo["maxdd"]) >= abs(dd_muc_tieu):
        # mua-giu tran da sau hon muc DD cua he -> ha don bay xuong duoi 1
        lo, hi = 0.05, 1.0
        c = thu(lo)
        if abs(c["maxdd"]) >= abs(dd_muc_tieu):
            c["don_bay"] = lo
            return c
    for _ in range(22):
        gi = (lo + hi) / 2.0
        c = thu(gi)
        if c["chay"] or abs(c["maxdd"]) > abs(dd_muc_tieu):
            hi = gi
        else:
            lo = gi
    c = thu(lo)
    c["don_bay"] = lo
    return c


def xet(df: pd.DataFrame, vi_the, cp, ma: str = "", khung: str = "D1",
        muc_cagr: float = MUC_CAGR, tran_dd: float = TRAN_DD,
        min_lenh: int = MIN_LENH, min_nam: float = MIN_NAM,
        don_bay=DON_BAY, bang_bh: list[dict] | None = None) -> dict:
    """Xet mot he qua CONG RA TIEN. Tra ve day du ly do, khong chi PASS/FAIL.

    Chon don bay THAP NHAT dat `muc_cagr` ma van trong `tran_dd`. Khong toi uu
    don bay theo ket qua - lay thap nhat la de khong bien buoc chon don bay
    thanh mot vong quet tham so len holdout.
    """
    vi_the = np.asarray(vi_the, float)
    so_nam = max((df.index[-1] - df.index[0]).days / 365.25, 1e-9)

    hang = []
    for L in don_bay:
        kq = MP.chay(df, vi_the, cp, ma=ma, khung=khung, don_bay=float(L),
                     gop="so_hoc")
        c = B._chi_so(kq)
        c["don_bay"] = float(L)
        c["so_lenh"] = int(kq.so_lenh)
        hang.append(c)

    dat = [h for h in hang
           if h["cagr"] > 0 and h["cagr"] >= muc_cagr and abs(h["maxdd"]) < tran_dd
           and not h["chay"]]
    chon = min(dat, key=lambda h: h["don_bay"]) if dat else \
        max(hang, key=lambda h: h["cagr"])

    bh = (tra_khop_dd(bang_bh, chon["maxdd"]) if bang_bh
          else mua_giu_khop_dd(df, cp, chon["maxdd"], ma=ma, khung=khung))

    dk = {
        "1_lai": chon["cagr"] > 0 and chon["cagr"] >= muc_cagr,
        "2_sut_giam": abs(chon["maxdd"]) < tran_dd,
        "4_du_lenh": chon["so_lenh"] >= min_lenh,
        "5_khong_chay": not chon["chay"],
        "6_song_du": so_nam >= min_nam,
    }
    # 25/09: NHAN, khong chan (xem docstring dau file).
    nhan = {"3_hon_mua_giu_cung_DD": chon["cagr"] > bh["cagr"]}
    truot = [k for k, v in dk.items() if not v]
    return {
        "verdict": "RA_TIEN" if not truot else "KHONG",
        "truot": truot,
        "nhan": nhan,
        "he": {k: chon.get(k) for k in
               ("don_bay", "cagr", "maxdd", "calmar", "sharpe", "so_lenh",
                "phoi_nhiem", "chay")},
        "mua_giu_cung_dd": {k: bh.get(k) for k in
                            ("don_bay", "cagr", "maxdd", "sharpe")},
        "cach_biet_cagr": (chon["cagr"] - bh["cagr"]),
        "so_nam": so_nam,
        "hang_don_bay": [{k: h[k] for k in ("don_bay", "cagr", "maxdd", "chay")}
                         for h in hang],
        # Cong nay KHONG tra loi cau hoi "co that khong". Bat cu ket qua
        # RA_TIEN nao muon thanh ket luan van phai qua `nhan/cong.py`.
        "da_qua_cong_that": False,
        "nguong": {"muc_cagr": muc_cagr, "tran_dd": tran_dd,
                   "min_lenh": min_lenh, "min_nam": min_nam},
    }
