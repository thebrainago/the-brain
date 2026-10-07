# -*- coding: utf-8 -*-
"""cmt_prior.py - tri thuc nen kieu giao trinh CMT (phan tich ky thuat) dung de LOC thi nghiem thua va XEP UU TIEN gia thuyet.

CMT (Chartered Market Technician) day ba y ma lab dung duoc: (1) cac chi bao CUNG HO do cung mot thong tin (RSI/Stoch/CCI deu la dong luong
dao dong) -> hai gia thuyet chi khac ho-trong-ho la MOT thi nghiem, tham so cua no di vao luoi (HEPHAESTUS), khong ton mot phep thu moi;
(2) "xac nhan" chi co nghia khi bang chung DOC LAP (khac ho) - chong hai chi bao cung ho khong xac nhan gi; (3) che do thi truong quyet dinh ho
nao dang thu truoc: hoi quy (Hurst < 0,5) -> dao dong / bang; quan tinh -> theo xu huong / pha vo.
KHONG PHAI CONG CHAN: day la NHAN + THU TU, khong tu choi gia thuyet (tieu chi duyet chi la co lai sau phi + maxDD < 80%).
Chi doc ten chi bao trong khai bao DSL (`ngu_phap`), khong chay engine, khong ghi so cai."""
from __future__ import annotations

from collections import OrderedDict

HO = {
    "XU_HUONG": {"sma", "ema", "wma", "smma", "macd", "supertrend", "ichimoku", "tuyen_tinh", "duong_xu_huong", "goc", "tb"},
    "SUC_MANH_XU_HUONG": {"adx"},
    "DAO_DONG": {"rsi", "stochastic", "cci", "dong_luong", "doi", "doi_pct", "zscore", "ibs", "do_lech"},
    "BIEN_DONG": {"atr", "bollinger", "keltner", "bien_do", "phuong_sai"},
    "PHA_VO": {"donchian", "cao_nhat", "thap_nhat", "cao_nhat_cua_cac", "thap_nhat_cua_cac"},
    "KHOI_LUONG": {"obv", "vwap", "khoi_luong"},
    "HINH_HOC": {"fibo", "gann_sq9", "moc_ky"},
    "NEN": {"mau_nen", "heiken", "than_nen"},
    "LICH": {"gio", "ngay_trong_tuan", "ngay_trong_thang", "thang"},
    "TUONG_QUAN": {"tuong_quan", "phan_vi"},
}
NEN_TANG = {"gia", "tre", "tong", "tuyet_doi", "tong_cua_cac", "tb_cua_cac", "trang_thai_lat", "dem_lien_tiep"}   # khong mang thong tin ho
TEN_HO = {c: h for h, cs in HO.items() for c in cs}
# che do -> ho thu truoc (CMT: dao dong dung o thi truong di ngang, theo xu huong o thi truong co xu huong)
UU_TIEN = {"hoi_quy": {"DAO_DONG": 2, "BIEN_DONG": 2, "LICH": 1, "HINH_HOC": 1},
           "quan_tinh": {"XU_HUONG": 2, "PHA_VO": 2, "SUC_MANH_XU_HUONG": 1, "BIEN_DONG": 1}}


def ho_cua(chi_bao: str) -> str | None:
    return TEN_HO.get(chi_bao)


def chi_bao_trong(x) -> list[str]:
    """Moi gia tri khoa 'chi_bao' (de quy, giu thu tu, khong lap)."""
    ra: list[str] = []

    def di(v):
        if isinstance(v, dict):
            c = v.get("chi_bao")
            if isinstance(c, str) and c not in ra:
                ra.append(c)
            for w in v.values():
                di(w)
        elif isinstance(v, (list, tuple)):
            for w in v:
                di(w)
    di(x)
    return ra


def chu_ky(spec) -> dict:
    cb = [c for c in chi_bao_trong(spec) if c not in NEN_TANG]
    ho = sorted({TEN_HO[c] for c in cb if c in TEN_HO})
    la = sorted(c for c in cb if c not in TEN_HO)
    return {"chi_bao": cb, "ho": ho, "la": la}


def canh_bao(spec, co_khoi_luong_that: bool = False) -> list[str]:
    cs = chu_ky(spec)
    ra = []
    if "KHOI_LUONG" in cs["ho"] and not co_khoi_luong_that:
        ra.append("KHOI_LUONG tren CFD/FX la tick volume (khong phai khoi luong san): bang chung yeu, de thu cuoi")
    vao = spec.get("vao") if isinstance(spec, dict) else None
    if isinstance(vao, list) and len(vao) >= 2:
        hos = [tuple(chu_ky(d)["ho"]) for d in vao]
        if len(set(hos)) == 1 and hos[0]:
            ra.append("xac_nhan_khong_doc_lap: moi dieu kien vao cung ho %s - CMT: chong cung ho khong xac nhan them" % "+".join(hos[0]))
    if not cs["ho"]:
        ra.append("khong_co_chi_bao_ho: (gia / lich tran) - khong the xep ho")
    return ra


def diem_uu_tien(spec, tinh_cach: str | None = None) -> int:
    u = UU_TIEN.get(tinh_cach or "", {})
    return sum(u.get(h, 0) for h in chu_ky(spec)["ho"])


def loc(cac_spec, tinh_cach: str | None = None, co_khoi_luong_that: bool = False) -> dict:
    """Gom spec cung CHU KY HO thanh cum; moi cum giu 1 dai dien (diem uu tien cao nhat, roi dau tien); phan con lai = GOP (tham so -> luoi).
    `so_phep_thu_hieu_dung` = so cum: dung lam so phep thu khi tinh FDR / ngan sach, thay cho so spec."""
    cum: "OrderedDict[tuple, list[int]]" = OrderedDict()
    for i, s in enumerate(cac_spec):
        cum.setdefault((tuple(chu_ky(s)["ho"]), (s.get("chieu", s.get("huong")) if isinstance(s, dict) else None)), []).append(i)
    ds = []
    for (ho, huong), idx in cum.items():
        dai_dien = max(idx, key=lambda i: (diem_uu_tien(cac_spec[i], tinh_cach), -i))
        ds.append({"ho": list(ho), "huong": huong, "dai_dien": dai_dien, "gop": [i for i in idx if i != dai_dien],
                   "uu_tien": diem_uu_tien(cac_spec[dai_dien], tinh_cach)})
    ds.sort(key=lambda c: (-c["uu_tien"], c["dai_dien"]))
    return {"so_spec": len(cac_spec), "so_phep_thu_hieu_dung": len(ds), "tinh_cach": tinh_cach, "cum": ds,
            "canh_bao": {i: w for i, w in ((i, canh_bao(s, co_khoi_luong_that)) for i, s in enumerate(cac_spec)) if w},
            "ghi_chu": "NHAN + THU TU, khong phai cong chan; GOP = cung ho, doi tham so trong luoi."}
