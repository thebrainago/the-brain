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
#: Mot nhom phai co it nhat tung nay lan TRUNG VI cac nhom moi duoc tinh.
#:
#: VI SAO (chu du an chi ra 12/09: "fx dau chay thu 7 va chu nhat"). Sau khi da
#: hieu chinh lech nhan, van con 54/159 ma co bar CHU NHAT - tat ca la cap FX.
#: Chung khong phai phien: FX mo lai ~22:00 toi CN gio may chu, nen sinh mot bar
#: hai gio mang KHE GIA CUOI TUAN. So luong 1,3-11% so voi ~20% cua ngay that.
#:
#: Doi nhan khong cuu duoc loai nay - phai LOAI. Va luat theo TI LE thi bat duoc
#: ca hai loai mot luc, khong can biet tai san la FX hay chi so:
#:   loai A  khong co T6, CN ~20%  -> lech nhan, dich +1 (xem `thu_da_sua`)
#:   loai B  co T6, CN 1-4%        -> bar mo lai, bi luat nay loai
TY_LE_NHOM_TOI_THIEU = 0.5


def _loi_suat(df: pd.DataFrame) -> pd.Series:
    return np.log(df["close"]).diff()


#: Ty le bar phai cung MOT gio UTC de coi la "dong nhat" - duoi nguong nay thi
#: khong the doc "gio goc" tu du lieu (mixed-source hoac qua nhieu lo hong).
TY_LE_GIO_DONG_NHAT = 0.95


def _gio_utc_chiem_da_so(idx: pd.DatetimeIndex) -> int | None:
    """Gio UTC (0-23) ma >=95% so bar dung - `None` neu khong dong nhat.

    Day la TIN HIEU GOC (13/09/2026), thay cho viec doan qua ty le T6/CN. Kiem
    tren ca 159 ma cua kho (`ma so_dong_bo` = idx.hour luc goi ham nay - LUON la
    UTC vi `quet_mot` da tz_convert("UTC") truoc khi goi): dung MOT trong hai
    gia tri suot toan bo lich su, khong tron lan:
        gio = 21  (82/159 ma - toan bo la ban SAN/broker: XM/Exness/MetaQuotes)
        gio = 0   (77/159 ma - Yahoo/nguon khac, da la ngay lich dung)
    Khong co ma nao o giua hay doi gio giua cac doan lich su.
    """
    if len(idx) == 0:
        return None
    vc = pd.Series(idx.hour).value_counts(normalize=True)
    if vc.empty or vc.iloc[0] < TY_LE_GIO_DONG_NHAT:
        return None
    return int(vc.index[0])


def thu_da_sua(idx: pd.DatetimeIndex) -> tuple[np.ndarray | None, str]:
    """Nhan THU da hieu chinh lech moc bar. -> (nhan, ghi_chu). `nhan=None`
    nghia la KHONG the ket luan - goi phai coi day la CHUA_DO_DUOC, khong duoc
    tu doan.

    SUA 13/09/2026 - CAI BAY CU (do 05/09-12/09): ban dau ham nay chi doan qua
    THONG KE GIAN TIEP (ty le bar T6/CN thap/cao). Chu du an chi ra dung: mot
    con so bps dung ma gan sai ngay thi KHONG viet duoc luat giao dich, va mot
    canh bao ma khong ai doc thi khong khac gi khong co canh bao - 41/50 phat
    hien mua vu M3 van "di qua" mang theo canh bao nay ma khong ai chan lai.

    NGUYEN NHAN GOC (do truc tiep, khong doan qua % T6/CN nua): bar D1 cua kho
    nay dong o **21:00 UTC** cho toan bo 82/159 ma nguon SAN (XM/Exness/
    MetaQuotes) - day la NUA DEM gio may chu (UTC+3, khong doi theo DST) chu
    khong phai nua dem UTC. Tuc ngay-lich cua chinh cai timestamp (tinh theo
    UTC) LUON it hon ngay giao dich THAT mot ngay: bar dong dau "CN 21:00 UTC"
    la nua dem THU HAI gio may chu, chua du lieu cua phien THU HAI. 77/159 ma
    con lai (Yahoo va vai nguon khac) dong bar dung 00:00 - ngay lich la ngay
    that, khong can dich.

    Kiem tra cheo (13/09/2026, script doi chieu ca 159 ma): tin hieu GIO nay va
    tin hieu THONG KE cu (T6<2%% va CN>10%%) khop nhau 100% - 0 sai lech ca hai
    chieu. Nen ham nay VAN giu phep thong ke lam **co so xac nhan doc lap thu
    hai**, khong bo di: neu hai tin hieu MAU THUAN nhau (vi du du lieu mix
    nhieu nguon giua chung mot ma, hoac gio UTC la mot gia tri la khong phai
    0 hay 21) thi day chinh la truong hop "khong chac" ma ban dau ham nay
    khong co cach bat - tra `None` de nguoi goi ha ket qua ve CHUA_DO_DUOC
    thay vi in lang le mot canh bao roi van tinh `dat` nhu khong co gi xay ra.

    HUONG DICH khi gio xac nhan CAN dich (gio_utc >= 12, tuc bar dong buoi
    toi UTC = nua dem gio may chu cua NGAY UTC KE TIEP): `ngay_phien =
    ngay_dong_dau + 1`. Anh xa {CN,T2,T3,T4,T5} -> {T2,T3,T4,T5,T6}, dung nam
    ngay lam viec. (Dich -2 se cho T7/CN mang gia tri phien day du - vo ly, do
    la dau hieu mot phep dich SAI.)
    """
    t = idx.dayofweek.to_numpy()
    n = max(len(t), 1)
    p6 = float((t == 4).sum()) / n
    pcn = float((t == 6).sum()) / n
    thong_ke_can_dich = p6 < 0.02 and pcn > 0.10

    gio = _gio_utc_chiem_da_so(idx)
    if gio is None:
        goc_can_dich = None                 # khong doc duoc gio goc dong nhat
    elif gio == 0:
        goc_can_dich = False
    elif gio >= 12:
        goc_can_dich = True
    else:
        goc_can_dich = None                 # gio la (1..11) - mau hinh la, khong doan

    if goc_can_dich is None:
        if thong_ke_can_dich:
            return None, ("MAU THUAN/KHONG RO: thong ke nghi lech nhan (T6=%.1f%%, "
                          "CN=%.1f%%) nhung KHONG doc duoc gio UTC dong nhat de "
                          "xac nhan tu goc - khong doan, CHUA_DO_DUOC"
                          % (100 * p6, 100 * pcn))
        return t, ""

    if goc_can_dich != thong_ke_can_dich:
        return None, ("MAU THUAN: gio goc (%s UTC) noi %s nhung thong ke T6/CN "
                      "(T6=%.1f%%, CN=%.1f%%) noi %s - hai tin hieu doc lap "
                      "khong khop, khong doan, CHUA_DO_DUOC"
                      % (gio, "CAN dich" if goc_can_dich else "KHONG can dich",
                         100 * p6, 100 * pcn,
                         "CAN dich" if thong_ke_can_dich else "KHONG can dich"))

    if goc_can_dich:
        return (t + 1) % 7, ("nhan thu DA SUA +1 ngay: bar dong dau %02d:00 UTC "
                             "= nua dem gio may chu (UTC+3), tuc ngay-lich UTC "
                             "cua timestamp it hon ngay giao dich that 1 ngay. "
                             "Xac nhan cheo bang thong ke (T6=%.1f%%, CN=%.1f%%)."
                             % (gio, 100 * p6, 100 * pcn))
    return t, ""


def _nhom(r: pd.Series, nhan: np.ndarray, ten: str,
          nhom_deu: bool = True) -> dict:
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
    # Luat ti le CHI ap cho nhom CHU KY DEU (thu, gio, thang) - noi cac nhom le
    # ra phai xap xi bang nhau nen mot nhom nho bat thuong la hien vat.
    # KHONG ap cho phep thu HAI NHOM CO Y LECH: "tuan giao thang" chi co 6 ngay
    # tren ~24 ngay con lai, va luat ti le se loai chinh nhom dang hoi. Ban dau
    # toi ap cho tat ca va M2 bien mat khoi 159/159 ma.
    tv = float(np.median([dem[k] for k in ten_nhom])) if ten_nhom else 0.0
    san = max(QS_TOI_THIEU, TY_LE_NHOM_TOI_THIEU * tv) if nhom_deu else QS_TOI_THIEU
    du = [k for k in ten_nhom if dem[k] >= san]
    bo = [int(k) for k in ten_nhom if dem[k] < san]
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
    return {"ten": ten, "so_nhom": len(du), "nhom_bi_loai": bo,
            "nhom_cao": int(cao), "nhom_thap": int(thap),
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
    ra["M2_tuan_giao_thang"] = _nhom(r, giao_thang, "giao_thang", nhom_deu=False)
    thu, ghi = thu_da_sua(idx)
    if thu is None:
        # CHOT CHAN (13/09/2026): khong con duong nao de M3 "dat=True" mang
        # theo mot nhan thu KHONG XAC DINH duoc - chi mot canh_bao_nhan ma
        # khong ai chan da de lot 41/50 phat hien truoc do. Ha thang ve
        # CHUA_DO_DUOC (ba trang thai cua du an: DAT/AM/CHUA_DO_DUOC - khau do
        # hong LUON la CHUA_DO_DUOC, khong bao gio la AM/DAT).
        ra["M3_ngay_trong_tuan"] = {"trang_thai": "CHUA_DO_DUOC", "vi_sao": ghi,
                                    "dat": False}
    else:
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
