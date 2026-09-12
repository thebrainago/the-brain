# -*- coding: utf-8 -*-
"""ho_so_mua_vu.py - TINH MUA VU va ENTRY-TIME cua mot tai san.

Muc Q2 cua `KE_HOACH_HOAN_THIEN.md`. Chu du an yeu cau trong `SO_DO_HE_THONG.txt`:

    "tinh mua vu (khong/ co/co thi cu the nhu nao)"
    "Nghien cuu cac dang entry time cua cac loai tai san nhu thoi diem mua ban
     co xac suat cao trong nam"

Chu y cach hoi: **"khong / co / co thi cu the nhu nao"** - tuc cau tra loi duoc
phep la KHONG. File nay phai tra loi duoc "khong co mua vu" chu khong phai luon
luon tim ra mot thang dep nhat.

## HAI CAI BAY, CA HAI DA SAP TRONG CHINH DU AN NAY

**(1) DIEM MUA VU IN-SAMPLE.** `AGENTS.md` muc 6: bang `MONTHLY_SCORE` gan cung
duoc rut ra tu chinh giai doan backtest -> IC bi thoi GAP DOI (+0,057 -> +0,029),
keo Sharpe he thong tu 0,76 xuong 0,59. Nen o day moi diem mua vu deu tinh bang
**CUA SO MO RONG**: diem cua nam N chi dung du lieu den het nam N-1.

**(2) 12 THANG LA 12 PHEP THU.** Tren 25 nam, moi thang chi co 25 quan sat. Lay
thang tot nhat trong 12 roi bao p-value cua rieng no la sai - do la cuc tri cua
12 lan rut. Nen null o day la **HOAN VI NHAN THANG**: giu nguyen chuoi loi suat,
xao tron nhan thang, roi hoi "chenh lech thang tot nhat - thang te nhat" co lon
hon dam khong. Cach do tu dong hieu chinh cho viec chon cuc tri.

## BON CAU HOI

    M1  THANG TRONG NAM     co thang nao khac han khong?
    M2  TUAN GIAO THANG     ngay cuoi/dau thang co khac phan con lai khong?
    M3  NGAY TRONG TUAN     thu nao khac han khong?
    M4  GIO TRONG NGAY      (chi khung co gio) gio nao khac han khong?

Chay:  python -m nhan.ho_so_mua_vu [MA] [KHUNG]
       python -m nhan.ho_so_mua_vu quet D1 10
Ra:    reports/HO_SO_MUA_VU.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

KHO = LAB / "reports" / "HO_SO_MUA_VU.json"

SO_XAO = 2000
HAT = 20260912
#: Duoi so quan sat nay cho mot nhom thi khong ket luan gi ve nhom do.
QS_TOI_THIEU = 12


def _loi_suat(df: pd.DataFrame) -> pd.Series:
    return np.log(df["close"]).diff()


def thu_da_sua(idx: pd.DatetimeIndex) -> tuple[np.ndarray, str]:
    """Nhan THU da hieu chinh lech moc bar. -> (nhan, ghi_chu)

    CAI BAY DA SAP O DAY (do 12/09/2026). Bar D1 cua nhieu cap FX **khong co bar
    THU SAU**, trong khi "CHU NHAT" lai chiem du ~20% so bar voi bien do binh
    thuong:

        EURUSD D1   T2 20,1% · T3 20,1% · T4 20,0% · T5 20,1% · CN 19,7% · T6 0%

    Tuc bar duoc dong dau o gio may chu (UTC+2/+3) nen phien THU SAU roi sang
    nhan CHU NHAT. Doc thang `dayofweek` thi "chu nhat la thu tot nhat" - 23/43
    ma trong lan quet dau bao vay, va do la mot HIEN VAT NHAN, khong phai hieu
    ung lich.

    Phan biet voi bar CHU NHAT THAT: chi so CFD co bar CN that, nhung no la mot
    phien MO LAI ngan - chi 4,2%% so bar va bien do 0,227%% so voi 1,3%% cua ngay
    thuong (XM_US500CASH). Nen dau hieu la SO LUONG, khong phai ten.

    HUONG DICH: tuan FX chay CN 22:00 -> T6 22:00 UTC. Bar dong dau CHU NHAT
    chua phien THU HAI; bar dong dau THU NAM chua phien THU SAU. Tuc
    **ngay_phien = ngay_dong_dau + 1**. Anh xa {CN,T2,T3,T4,T5} -> {T2,T3,T4,T5,T6},
    dung nam ngay lam viec.

    (Ban dau toi dich -2 va no cho ra T7/CN co phien day du - vo ly, vi thu bay
    va chu nhat khong co phien. Dau hieu de nhan ra mot phep dich SAI: sau khi
    dich van con ngay cuoi tuan mang gia tri binh thuong.)

    Luat: neu thu 6 gan nhu khong co (<2%%) ma CN co nhieu (>10%%) thi dich +1.
    """
    t = idx.dayofweek.to_numpy()
    n = max(len(t), 1)
    p6 = float((t == 4).sum()) / n
    pcn = float((t == 6).sum()) / n
    if p6 < 0.02 and pcn > 0.10:
        return (t + 1) % 7, ("nhan thu lech mot ngay (khong co T6, CN chiem "
                             "%.1f%%) - bar dong dau la ngay TRUOC phien, da +1"
                             % (100 * pcn))
    return t, ""


def _nhom(r: pd.Series, nhan: np.ndarray, ten: str) -> dict:
    """Chenh lech nhom cao nhat - thap nhat, so voi HOAN VI NHAN.

    Hoan vi NHAN (khong hoan vi loi suat) giu nguyen moi tinh chat cua chuoi -
    cum bien dong, duoi beo - va chi pha lien he giua NHAN va LOI SUAT. Do la
    dung dieu can kiem.
    """
    ok = np.isfinite(r.to_numpy()) & (nhan >= 0)
    x, g = r.to_numpy()[ok], nhan[ok]
    if len(x) < 200:
        return {"loi": "chi %d quan sat" % len(x)}
    ten_nhom = sorted(set(g.tolist()))
    dem = {k: int((g == k).sum()) for k in ten_nhom}
    du = [k for k in ten_nhom if dem[k] >= QS_TOI_THIEU]
    if len(du) < 2:
        return {"loi": "chi %d nhom du quan sat" % len(du)}

    def _chenh(gg):
        tb = np.array([x[gg == k].mean() for k in du])
        return float(tb.max() - tb.min()), du[int(tb.argmax())], du[int(tb.argmin())]

    that, cao, thap = _chenh(g)
    rng = np.random.default_rng(HAT)
    null = np.array([_chenh(rng.permutation(g))[0] for _ in range(SO_XAO)])
    p = float((np.sum(null >= that) + 1) / (SO_XAO + 1))
    tb = {int(k): round(float(x[g == k].mean()) * 1e4, 2) for k in du}  # bps/bar
    return {"ten": ten, "so_nhom": len(du), "nhom_cao": int(cao), "nhom_thap": int(thap),
            "chenh_bps": round(that * 1e4, 2),
            "null_trung_vi_bps": round(float(np.median(null)) * 1e4, 2),
            "p": round(p, 4), "dat": bool(p <= 0.05),
            "trung_binh_bps": tb, "so_quan_sat": {int(k): dem[k] for k in du}}


def _diem_pit(r: pd.Series, nhan: np.ndarray, toi_thieu_nam: int = 5) -> dict:
    """DIEM MUA VU POINT-IN-TIME: diem cua moc t chi dung du lieu TRUOC t.

    Do IC (tuong quan hang) giua diem PIT va loi suat thuc te. Day la con so
    duy nhat noi duoc "mua vu co dung duoc khong", khac han bang trung binh
    toan mau o tren - bang do chi noi "trong qua khu thang nao dep".
    """
    x = r.to_numpy()
    idx = pd.DatetimeIndex(r.index)
    nam = idx.year.to_numpy()
    ok = np.isfinite(x) & (nhan >= 0)
    nam_dau = int(np.min(nam[ok])) + toi_thieu_nam
    diem, thuc = [], []
    tong = {}
    dem = {}
    for i in range(len(x)):
        if not ok[i]:
            continue
        k = int(nhan[i])
        if nam[i] >= nam_dau and dem.get(k, 0) >= 3:
            diem.append(tong[k] / dem[k])
            thuc.append(x[i])
        tong[k] = tong.get(k, 0.0) + x[i]     # CAP NHAT SAU khi dung - PIT
        dem[k] = dem.get(k, 0) + 1
    if len(diem) < 300:
        return {"loi": "chi %d quan sat PIT" % len(diem)}
    a = pd.Series(diem).rank()
    b = pd.Series(thuc).rank()
    ic = float(a.corr(b))
    rng = np.random.default_rng(HAT + 1)
    null = np.array([float(a.corr(pd.Series(rng.permutation(b.to_numpy()))))
                     for _ in range(min(SO_XAO, 400))])
    p = float((np.sum(np.abs(null) >= abs(ic)) + 1) / (len(null) + 1))
    return {"ic_pit": round(ic, 5), "so_quan_sat": len(diem),
            "p": round(p, 4), "dat": bool(p <= 0.05 and ic > 0)}


def quet_mot(ma: str, khung: str = "D1") -> dict:
    from nhan import du_lieu as DL
    t0 = time.time()
    df = DL.nap(ma, khung)
    r = _loi_suat(df)
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)

    ngay_trong_thang = idx.day.to_numpy()
    so_ngay = idx.days_in_month.to_numpy()
    # TUAN GIAO THANG: 3 ngay cuoi thang + 3 ngay dau thang = nhom 1, con lai 0
    giao_thang = np.where((ngay_trong_thang <= 3) | (ngay_trong_thang > so_ngay - 3),
                          1, 0)

    ra = {"ma": ma, "khung": khung, "so_bar": len(df),
          "tu": str(df.index[0].date()), "den": str(df.index[-1].date()),
          "so_nam": round((df.index[-1] - df.index[0]).days / 365.25, 2)}
    ra["M1_thang_trong_nam"] = _nhom(r, idx.month.to_numpy(), "thang")
    ra["M2_tuan_giao_thang"] = _nhom(r, giao_thang, "giao_thang")
    thu, ghi = thu_da_sua(idx)
    ra["M3_ngay_trong_tuan"] = _nhom(r, thu, "thu")
    if ghi:
        ra["M3_ngay_trong_tuan"]["canh_bao_nhan"] = ghi
    if len(set(idx.hour)) > 1:
        ra["M4_gio_trong_ngay"] = _nhom(r, idx.hour.to_numpy(), "gio")
    ra["diem_thang_PIT"] = _diem_pit(r, idx.month.to_numpy())

    dat = [k for k, v in ra.items()
           if isinstance(v, dict) and v.get("dat")]
    ra["cau_tra_loi"] = ("KHONG co mua vu do duoc" if not dat
                         else "CO: " + ", ".join(dat))
    ra["giay"] = round(time.time() - t0, 2)
    return ra


def _mot(args):
    ma, khung = args
    try:
        return quet_mot(ma, khung)
    except Exception as e:
        return {"ma": ma, "khung": khung,
                "loi": "%s: %s" % (type(e).__name__, str(e)[:70])}


def quet(cac_ma=None, khung: str = "D1", so_tien_trinh: int = 10, in_ra=print) -> dict:
    from concurrent.futures import ProcessPoolExecutor
    if cac_ma is None:
        from nhan import ho_so_symbol as HSS
        hs = HSS.doc()
        if isinstance(hs, dict):
            hs = list(hs.values())
        cac_ma = sorted({str(x.get("ma")) for x in hs
                         if isinstance(x, dict) and x.get("ma")})
    t0 = time.time()
    ra = {}
    with ProcessPoolExecutor(max_workers=so_tien_trinh) as ex:
        for i, r in enumerate(ex.map(_mot, ((m, khung) for m in cac_ma),
                                     chunksize=2), 1):
            ra["%s|%s" % (r["ma"], r["khung"])] = r
            if in_ra and i % 25 == 0:
                in_ra("  ... %d/%d (%.0fs)" % (i, len(cac_ma), time.time() - t0))
    KHO.parent.mkdir(exist_ok=True)
    KHO.write_text(json.dumps(ra, ensure_ascii=False, indent=1, default=float),
                   encoding="utf-8")
    if in_ra:
        ok = [v for v in ra.values() if "loi" not in v]
        from collections import Counter
        dem = Counter()
        for v in ok:
            for k in ("M1_thang_trong_nam", "M2_tuan_giao_thang",
                      "M3_ngay_trong_tuan", "M4_gio_trong_ngay", "diem_thang_PIT"):
                if isinstance(v.get(k), dict) and v[k].get("dat"):
                    dem[k] += 1
        in_ra("\ndo duoc %d/%d ma trong %.0fs" % (len(ok), len(ra), time.time() - t0))
        in_ra("%-24s %8s %8s" % ("cau hoi", "dat", "ty le"))
        in_ra("-" * 44)
        for k in ("M1_thang_trong_nam", "M2_tuan_giao_thang", "M3_ngay_trong_tuan",
                  "M4_gio_trong_ngay", "diem_thang_PIT"):
            co = sum(1 for v in ok if isinstance(v.get(k), dict) and "loi" not in v[k])
            if co:
                in_ra("%-24s %8d %7.1f%%" % (k, dem[k], 100 * dem[k] / co))
        khong = sum(1 for v in ok if v.get("cau_tra_loi", "").startswith("KHONG"))
        in_ra("\nma KHONG co mua vu do duoc: %d/%d = %.1f%%"
              % (khong, len(ok), 100 * khong / max(len(ok), 1)))
        in_ra("-> %s" % KHO)
    return ra


def doc() -> dict:
    try:
        return json.loads(KHO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "quet":
        quet(khung=argv[1] if len(argv) > 1 else "D1",
             so_tien_trinh=int(argv[2]) if len(argv) > 2 else 10)
        return 0
    ma = argv[0] if argv else "XM_US500CASH"
    khung = argv[1] if len(argv) > 1 else "D1"
    print(json.dumps(quet_mot(ma, khung), ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
