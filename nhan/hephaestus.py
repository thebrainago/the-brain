# -*- coding: utf-8 -*-
"""hephaestus.py - MODULE DE CO CHE. Nua chu dong cua he.

So do he thong (LUAT SO 0, chu du an duyet 13/09/2026) khai module nay cung
loi goi `b hepha`, va chia lai ranh gioi ba viec:

    SEEKER       chi lo NGUON VAO   - mang ve chi bao, phuong phap, y tuong
    HEPHAESTUS   DE CO CHE          - rai luoi tham so, ghep nut, sinh to hop
    QUANTLAB     TEST               - pheu, quan li lenh, cong

File nay chua bao gio duoc viet. Do la ly do he chi biet may mo cai co san:
`to_hop.py` ket hop co che DA CO, `noi_sinh.py` doc lich su mot ma, `ngoai_sinh`
chuyen he sang tai san khac - **khong ai sinh ra co che MOI**.

## VI SAO DAY LA NUT THAT THAT SU

Chu du an 19/09/2026: *"neu co he thong ra tien thi cha ai up len"*.

Dung, va no keo theo mot he qua ma ca he dang lam nguoc: kho tai lieu cho ta
NGUYEN LIEU, khong cho ta CONG THUC. Gia tri phai den tu viec ta to hop lai -
doi tham so, doi nguong, dat kich hoat cua ho nay vao bo loc cua ho kia.

DO LAI NGAY 19/09/2026 (con so "kho rong 8 chi bao" trong so do la cua 13/09,
da cu - khong dung no nua):

    kho co che              4.049 co che, dung 34/45 toan hang
    con BO TRONG han        15: bollinger · ichimoku · vwap · fibo · moc_ky ·
                            wma · smma · obv · gann_sq9 · goc · duong_xu_huong ·
                            dem_lien_tiep · trang_thai_lat · tuong_quan · phuong_sai

Nen luan diem "kho qua hep" phai phat bieu lai cho dung: kho KHONG hep ve so
luong. Cai no thieu la nhung vung von tu ma **khong ai viet bai**, va - quan
trong hon - nhung TO HOP ma khong truong phai nao viet ra ca.

Do la phep do co y nghia, va no la phep do ma bai `do_moc_hephaestus` chay:

    duc() de ra 573 co che, **573 cai kho chua co** (0 trung)
    bien_the() tu 400 co che trong kho -> 1.069 ban, 1.038 cai kho chua co

Chu du an: *"10 trader chau A co 20 kieu dung Ichimoku"* - bien thien nam o
CACH GHEP va NGUONG, khong o ban than chi bao. 20 kieu dung khong phai 20 lan
boc tai lieu; la 1 chi bao + luoi tham so + to hop, do MAY sinh.

## BA THU BAT BUOC, THIEU MOT LA MAY DE THANH MAY NOI DOI

1. **TIEN DANG KY.** De 10.000 co che roi test la LUONG THIEN neu tra du gia
   FDR (`cong.lord_v2` doi `economic_plan_hash`). De 10.000, chon 5 cai dep,
   bao p < 0,05 la GIAN LAN. Nen `dang_ky_lo` chot van tay ca lo TRUOC khi ai
   cham vao du lieu, va ghi ro lo nay dat bao nhieu suat.
2. **XAC DINH.** Cung dau vao -> cung thu tu, cung `plan_hash`. Khong co RNG o
   day. Han ngach nho phai la TAP CON DAU cua han ngach lon, de xin 20 cai
   hom nay va 100 cai ngay mai khong phai dang ky lai tu dau.
3. **THANG DO.** Toan hang THANG GIA khong bao gio so voi mot hang so tran.
   Du an da tra gia: Sonic R sinh `open < 2` va `ema34_high < 1,5`, ca hai
   kich hoat 100% so bar. Nen `thang_do()` la mot phep BAT BUOC trong may de,
   khong phai mot loi khuyen.

## DE THEO KHUON KINH TE, KHONG THEO TICH DESCARTES

Nhan het von tu voi nhau cho ra hang trieu o vo nghia, va moi o la mot suat
FDR. Nen may de khong duyet tich Descartes - no dien vao KHUON:

    khuon = mot LUAN DIEM ve viec ai tra tien, cong cac O TRONG co kieu

Moi khuon tu mang cau `co_che` cua no - cau ma man hinh duyet doc. Nho vay cau
do noi duoc VI SAO co nguoi tra tien, thay vi liet ke lai tham so (cong
`kiem_khai_bao` doi toi thieu 25 ky tu chinh la doi cai nay).

Va cho "ket hop cac he thong va ly thuyet lai voi nhau" ma chu du an noi nam o
khuon GHEP: mot kich hoat cua ho nay dat trong bo loc cua ho khac - thu khong
tai lieu nao viet san, vi no khong phai cua ai ca.

## LUOI THAM SO CO NGUON GOC

Chu ky trong `CHU_KY` la chu ky nguoi ta THAT SU dung (5 · 9 · 10 · 14 · 20 ·
21 · 34 · 50 · 55 · 89 · 100 · 200 - Fibonacci, Wilder, va cac moc kinh dien).
Nguong trong `NGUONG` cung vay. Day KHONG phai luoi toi uu hoa: viec tim gia
tri tot nhat thuoc `do_on_dinh`/`to_hop`. Day la mien XUAT PHAT co nguon goc,
de moi con so deu tra loi duoc cau "vi sao la 14 ma khong phai 13".
"""
from __future__ import annotations

import hashlib
import json

from nhan import ngu_phap as NP

# --------------------------------------------------------------- THANG DO
#: Bon thang do. Phep so sanh chi co nghia GIUA HAI VE CUNG THANG.
THANG_GIA = "gia"          # muc gia - chi so voi muc gia khac
THANG_CHAN = "chan"        # co chan (0-100, 0-1) - so voi hang so duoc
THANG_CHIEU = "chieu"      # dau (-1/0/+1) - so voi 0
THANG_LICH = "lich"        # gio / thu / thang - so voi so nguyen
THANG_DEM = "dem"          # so lan dem duoc - so voi so nguyen nho
THANG_KL = "khoi_luong"    # so hop dong - don vi rieng, khong phai gia
THANG_GOC = "goc_do"       # goc cua duong khop - don vi rieng
#: Giu lai cho ma cu: truoc 19/09 "dao quanh 0" bi coi la MOT THANG DO. No
#: khong phai - xem `quanh_khong()`.
THANG_QUANH_KHONG = THANG_GIA
THANG_KHAC = "khac"

#: chi bao -> thang do. Cai KHONG co o day bi coi la `khac` va may de khong
#: dung - tha de it con hon de ra dieu kien vo nghia.
_THANG = {
    # muc gia
    "gia": THANG_GIA, "ema": THANG_GIA, "sma": THANG_GIA, "wma": THANG_GIA,
    "smma": THANG_GIA, "vwap": THANG_GIA, "cao_nhat": THANG_GIA,
    "thap_nhat": THANG_GIA, "bollinger": THANG_GIA, "keltner": THANG_GIA,
    "donchian": THANG_GIA, "ichimoku": THANG_GIA, "tb": THANG_GIA,
    "atr": THANG_GIA, "do_lech": THANG_GIA, "bien_do": THANG_GIA,
    "gann_sq9": THANG_GIA, "fibo": THANG_GIA,
    "phuong_sai": THANG_GIA, "tuyet_doi": THANG_GIA,
    # `moc_ky` tra ve MOT MUC GIA (dong cua ky truoc, dinh/day ky truoc). Quen
    # khai o day thi chinh cong thang do cua may de loai sach khuon `moc_neo`,
    # va no loai IM LANG - khuon van chay, chi la khong con gi di ra.
    "moc_ky": THANG_GIA,
    # co chan
    "rsi": THANG_CHAN, "stochastic": THANG_CHAN, "adx": THANG_CHAN,
    "ibs": THANG_CHAN, "phan_vi": THANG_CHAN, "zscore": THANG_CHAN,
    "cci": THANG_CHAN, "doi_pct": THANG_CHAN,
    # dau
    "supertrend": THANG_CHIEU, "heiken": THANG_CHIEU, "mau_nen": THANG_CHIEU,
    "trang_thai_lat": THANG_CHIEU,
    # DAO QUANH KHONG. `macd` la HIEU cua hai duong gia, nen do lon cua no
    # theo thang gia va mot nguong nhu `macd < 0,0034` chi dung cho dung mot
    # tai san o dung mot thoi ky - chinh cai bay `atr14 < 0,003472` da ghi
    # trong `ngu_phap` (kich hoat 1.719 lan o train, 0 lan o holdout). Nhung
    # DAU cua no thi khong thang do gi ca, nen `macd > 0` hoan toan hop le.
    # Vi vay thang nay chi cho so voi DUNG SO 0.
    "macd": THANG_QUANH_KHONG, "doi": THANG_QUANH_KHONG,
    # DO THAT 19/09 tren khung tong hop, chu khong doan theo ten:
    #   duong_xu_huong  -0,35 .. 0,28   <- KHONG phai muc gia, du ten nghe vay
    #   goc            -22,8 .. 21,1
    #   dong_luong      -5,1 .. 4,7
    #   than_nen        -1,4 .. 1,2     <- CO DAU: am la nen giam
    # Ca bon dao quanh 0 va do lon cua chung deo theo don vi gia, nen chi cai
    # DAU la dung duoc. Xep `duong_xu_huong` vao thang gia - loi ban dau cua
    # toi - cho phep so no voi `gia` (~100), mot phep so sanh vo nghia ma cong
    # cu phap khong the bat.
    "duong_xu_huong": THANG_GIA, "goc": THANG_GOC,
    "dong_luong": THANG_GIA, "than_nen": THANG_GIA,
    # tuong_quan nam gon trong [-1, 1] nen so voi hang so la co nghia.
    "tuong_quan": THANG_CHAN,
    # dem duoc
    "dem_lien_tiep": THANG_DEM,
    # lich
    "gio": THANG_LICH, "ngay_trong_tuan": THANG_LICH, "thang": THANG_LICH,
    "ngay_trong_thang": THANG_LICH,
    # KHOI LUONG la DON VI RIENG, khong phai gia. So no voi mot hang so cung
    # vo nghia nhu so gia voi hang so: so hop dong moi bar khac han giua cac ma
    # va truot theo nam. Chi so duoc voi chinh trung binh cua no.
    "khoi_luong": THANG_KL, "obv": THANG_KL,
}

#: `lay` doi thang do cua chinh chi bao do. `bollinger(lay=phan_tram_b)` la mot
#: ty le 0-1 chu khong phai mot muc gia - va do la ban duy nhat cua dai
#: Bollinger so duoc voi mot hang so.
_THANG_THEO_LAY = {
    "phan_tram_b": THANG_CHAN, "do_rong": THANG_CHAN, "chieu": THANG_CHIEU,
    # `fibo` lay=vi_tri la "gia dang o muc thoai lui nao" - mot TY LE tren bien
    # do song, khong phai mot muc gia. `lay` la so (0.618...) thi no LA muc gia
    # va roi ve thang gia qua `_THANG`, dung nhu `donchian` lay=tren.
    "vi_tri": THANG_CHAN, "khoang_cach": THANG_CHAN,
}


#: TOAN TU BOC NGOAI: khong co don vi RIENG, chung KE THUA don vi cua cai
#: chung boc. `tb(cua=khoi_luong)` la khoi luong chu khong phai gia.
#:
#: Thieu bang nay thi `khoi_luong > tb(khoi_luong)` - mot so sanh hoan toan
#: dung dan - bi chinh may de loai vi hai ve "khac thang do", va ca khuon
#: `dong_tien` ra 0 co che TRONG IM LANG (do 19/09/2026).
_BOC_NGOAI = {"tre", "tb", "tuyet_doi", "cao_nhat", "thap_nhat", "tong",
              "tb_cua_cac", "cao_nhat_cua_cac", "thap_nhat_cua_cac"}

#: NGUOC LAI: toan tu CHUAN HOA vut bo don vi cua dau vao va luon tra ve mot
#: so co chan. `phan_vi(cua=atr)` la mot ty le 0-1 chu khong phai mot muc atr -
#: va do chinh la ly do no chuyen duoc sang ma khac.
_CHUAN_HOA = {"phan_vi", "zscore", "doi_pct", "tuong_quan"}

#: DAO QUANH KHONG. Day la mot thuoc tinh KHAC voi don vi, va tach hai thu do
#: ra la cai sua duoc lop loi o tren: `than_nen` CUNG DON VI voi `bien_do`
#: (deu theo gia, nen so duoc voi nhau) nhung rieng no moi so duoc voi 0.
#:
#: Truoc 19/09 toi gop hai thu lam mot ("thang do quanh_khong"), va hau qua la
#: `tuyet_doi(than_nen) > 0,6 x bien_do` - mot dieu kien dung - bi loai vi hai
#: ve bi cham la khac thang do.
_QUANH_KHONG = {"macd", "doi", "dong_luong", "than_nen", "goc",
                "duong_xu_huong"}


def thang_do(t: dict) -> str:
    """DON VI cua mot toan hang. So sanh hai ve chi co nghia khi CUNG don vi.

    Toan tu boc ngoai ke thua don vi cua cai no boc; toan tu chuan hoa vut don
    vi di va tra ve so co chan. `tuyen_tinh` lay don vi cua cac hang tu khi
    chung dong nhat - mot to hop tuyen tinh cua nhieu muc gia van la muc gia.
    """
    if not isinstance(t, dict):
        return THANG_KHAC
    if "hang" in t:
        return THANG_KHAC
    lay = str(t.get("lay", "")).lower()
    if lay in _THANG_THEO_LAY:
        return _THANG_THEO_LAY[lay]
    cb = str(t.get("chi_bao", "")).lower()
    if cb in _CHUAN_HOA:
        return THANG_CHAN
    if cb in _BOC_NGOAI and isinstance(t.get("cua"), dict):
        return thang_do(t["cua"])
    if cb == "tuyen_tinh":
        tap = {thang_do(x) for x in (t.get("toan_hang") or [])
               if isinstance(x, dict)}
        return tap.pop() if len(tap) == 1 else THANG_KHAC
    return _THANG.get(cb, THANG_KHAC)


def quanh_khong(t: dict) -> bool:
    """Toan hang nay co DAO QUANH 0 khong - tuc dau cua no co nghia khong.

    Tach khoi `thang_do` vi day la thuoc tinh khac: mot toan hang co the cung
    don vi voi mot toan hang khac (nen so duoc voi no) ma van dao quanh 0 (nen
    so duoc voi hang so 0).
    """
    if not isinstance(t, dict) or "hang" in t:
        return False
    cb = str(t.get("chi_bao", "")).lower()
    if cb in _BOC_NGOAI and isinstance(t.get("cua"), dict):
        # `tuyet_doi(than_nen)` KHONG con dao quanh 0 - no la mot DO LON, va
        # do lon thi phai so voi mot do lon khac.
        return False if cb == "tuyet_doi" else quanh_khong(t["cua"])
    return cb in _QUANH_KHONG


# ------------------------------------------------------------------ VON TU
#: Chu ky NGUOI TA THAT SU DUNG - Fibonacci, Wilder, cac moc kinh dien. Khong
#: phai luoi toi uu hoa (do la viec cua `to_hop`/`do_on_dinh`); la mien xuat
#: phat co nguon goc, de moi con so tra loi duoc "vi sao 14 ma khong phai 13".
CHU_KY = (10, 14, 20, 34, 50, 100, 200)
CHU_KY_NGAN = (5, 9, 14, 21)

#: Nguong kinh dien cua tung chi bao co chan.
NGUONG = {
    "rsi": ((20.0, 30.0, 40.0), (60.0, 70.0, 80.0)),
    "stochastic": ((10.0, 20.0), (80.0, 90.0)),
    "cci": ((-200.0, -100.0), (100.0, 200.0)),
    "ibs": ((0.1, 0.2), (0.8, 0.9)),
    "zscore": ((-2.0, -1.5, -1.0), (1.0, 1.5, 2.0)),
    "phan_vi": ((0.05, 0.1, 0.2), (0.8, 0.9, 0.95)),
    "adx": ((15.0, 20.0), (25.0, 30.0)),
}

#: Nhom von tu -> cac toan hang mau. `nhom_cua` tra ve nhom cua mot toan hang,
#: va khuon GHEP dung no de bat hai ve phai thuoc hai nhom KHAC nhau.
NHOM_DO_CANG = "do_cang"
NHOM_MUC_GIA = "muc_gia"
NHOM_XU_THE = "xu_the"
NHOM_BIEN_DONG = "bien_dong"
NHOM_CHIEU = "chieu"
NHOM_LICH = "lich"

_NHOM = {
    "rsi": NHOM_DO_CANG, "stochastic": NHOM_DO_CANG, "cci": NHOM_DO_CANG,
    "ibs": NHOM_DO_CANG, "zscore": NHOM_DO_CANG, "phan_vi": NHOM_DO_CANG,
    "ema": NHOM_MUC_GIA, "sma": NHOM_MUC_GIA, "wma": NHOM_MUC_GIA,
    "smma": NHOM_MUC_GIA, "vwap": NHOM_MUC_GIA, "bollinger": NHOM_MUC_GIA,
    "keltner": NHOM_MUC_GIA, "donchian": NHOM_MUC_GIA,
    "ichimoku": NHOM_MUC_GIA, "cao_nhat": NHOM_MUC_GIA,
    "thap_nhat": NHOM_MUC_GIA, "gia": NHOM_MUC_GIA,
    "adx": NHOM_XU_THE, "dong_luong": NHOM_XU_THE, "macd": NHOM_XU_THE,
    "atr": NHOM_BIEN_DONG, "do_lech": NHOM_BIEN_DONG, "bien_do": NHOM_BIEN_DONG,
    "khoi_luong": "dong_tien", "obv": "dong_tien", "tuong_quan": "dong_tien",
    "than_nen": "hinh_nen", "goc": NHOM_XU_THE, "duong_xu_huong": NHOM_XU_THE,
    "ngay_trong_thang": NHOM_LICH, "thang": NHOM_LICH,
    "supertrend": NHOM_CHIEU, "heiken": NHOM_CHIEU, "mau_nen": NHOM_CHIEU,
    "gio": NHOM_LICH, "ngay_trong_tuan": NHOM_LICH, "thang": NHOM_LICH,
}


def nhom_cua(t: dict) -> str:
    """Nhom von tu cua mot toan hang - de biet mot co che ghep co that su
    ghep hai thu KHAC nhau, hay chi ghep hai bien the cua cung mot thu."""
    if not isinstance(t, dict):
        return THANG_KHAC
    if str(t.get("chi_bao", "")).lower() == "tre" and isinstance(t.get("cua"), dict):
        return nhom_cua(t["cua"])
    return _NHOM.get(str(t.get("chi_bao", "")).lower(), THANG_KHAC)


def _do_cang() -> list[tuple[str, dict, tuple, tuple]]:
    """(ten goi, toan hang, nguong duoi, nguong tren) cho moi do cang."""
    ra = []
    for cb in ("rsi", "stochastic", "cci"):
        for n in CHU_KY_NGAN:
            ra.append((f"{cb}{n}", {"chi_bao": cb, "n": n}, *NGUONG[cb]))
    ra.append(("ibs", {"chi_bao": "ibs"}, *NGUONG["ibs"]))
    for n in CHU_KY_NGAN:
        ra.append((f"zscore{n}",
                   {"chi_bao": "zscore", "n": n,
                    "cua": {"chi_bao": "gia", "cot": "close"}}, *NGUONG["zscore"]))
        ra.append((f"phanvi{n}",
                   {"chi_bao": "phan_vi", "n": n,
                    "cua": {"chi_bao": "gia", "cot": "close"}}, *NGUONG["phan_vi"]))
    for lay, ten in (("phan_tram_b", "bb_b"), ("phan_tram_b", "kc_b")):
        cb = "bollinger" if ten == "bb_b" else "keltner"
        for n in (20, 50):
            ra.append((f"{ten}{n}", {"chi_bao": cb, "n": n, "k": 2.0, "lay": lay},
                       (0.0, 0.1), (0.9, 1.0)))
    return ra


def _muc_gia() -> list[tuple[str, dict]]:
    """Cac MUC GIA de so voi gia dong cua hoac voi nhau."""
    ra = []
    for cb in ("ema", "sma", "wma", "smma"):
        for n in CHU_KY:
            ra.append((f"{cb}{n}", {"chi_bao": cb, "n": n, "cot": "close"}))
    for n in CHU_KY:
        ra.append((f"vwap{n}", {"chi_bao": "vwap", "n": n}))
    for lay, nh in (("tren", "tren"), ("duoi", "duoi")):
        for n in (20, 50):
            ra.append((f"bb{n}_{nh}",
                       {"chi_bao": "bollinger", "n": n, "k": 2.0, "lay": lay}))
            ra.append((f"kc{n}_{nh}",
                       {"chi_bao": "keltner", "n": n, "k": 2.0, "lay": lay}))
            ra.append((f"dc{n}_{nh}", {"chi_bao": "donchian", "n": n, "lay": lay}))
    for lay in ("tenkan", "kijun"):
        ra.append((f"ichi_{lay}", {"chi_bao": "ichimoku", "lay": lay}))
    return ra


def _chieu() -> list[tuple[str, dict]]:
    ra = [("heiken", {"chi_bao": "heiken", "lay": "chieu"})]
    for n in (7, 10, 14):
        ra.append((f"super{n}",
                   {"chi_bao": "supertrend", "n": n, "k": 3.0, "lay": "chieu"}))
    for mau in ("nhan_chim", "bua", "sao_bang", "rau_duoi"):
        ra.append((f"nen_{mau}", {"chi_bao": "mau_nen", "mau": mau}))
    return ra


def _xu_the() -> list[tuple[str, dict, tuple, tuple]]:
    return [(f"adx{n}", {"chi_bao": "adx", "n": n}, *NGUONG["adx"])
            for n in (14, 20)]


GIA = {"chi_bao": "gia", "cot": "close"}


# ------------------------------------------------------------------ KHUON
def _ten(*phan) -> str:
    return NP.chuan_hoa_ten("hp_" + "_".join(str(x) for x in phan if x))


def _spec(ten, ho, chieu, vao, luan, giu) -> dict:
    return {"ten": ten, "ho": ho, "chieu": chieu, "giu": giu,
            "co_che": luan, "vao": vao, "nguon": "hephaestus"}


def _khuon_qua_da_hoi_ve(giu_mac_dinh: int) -> list[dict]:
    """Do cang cham cuc tri -> vao NGUOC. Luan diem: nguoi ban bi ep ban (goi
    ky quy, chan lo, quy phai can bang danh muc) khong chon duoc gia; ai cam
    duoc vi the qua luc do se duoc tra cho phan chenh lech."""
    ra = []
    for ten, t, duoi, tren in _do_cang():
        for v in duoi:
            ra.append(_spec(
                _ten(ten, "duoi", v), "quay_ve_trung_binh", 1,
                [{"trai": t, "phep": "<", "phai": {"hang": v}}],
                "Ben ban bi ep ban o vung qua da nen khong chon duoc gia; ai "
                "cam duoc vi the qua luc do duoc tra cho phan chenh lech.",
                giu_mac_dinh))
        for v in tren:
            ra.append(_spec(
                _ten(ten, "tren", v), "quay_ve_trung_binh", -1,
                [{"trai": t, "phep": ">", "phai": {"hang": v}}],
                "Ben mua duoi o vung qua da nen tra gia cao hon muc can bang; "
                "ban cho ho la ban thanh khoan dung luc no hiem.",
                giu_mac_dinh))
    return ra


def _khuon_pha_vo(giu_mac_dinh: int) -> list[dict]:
    """Gia vuot muc -> vao THUAN. Luan diem: pha mot muc ai cung nhin doi phai
    co dong tien that tiep tuc mua cao hon, va phan dat them do la phi tra cho
    nguoi nhan rui ro pha vo gia."""
    # CAN DUNG BIEN. Ban dau ham nay ghep ca hai chieu vao CUNG mot muc: `gia >
    # bien_tren` cho mua VA `gia < bien_tren` cho ban. Ve thu hai khong phai
    # mot cu thung - gia nam duoi bien tren cua Bollinger o gan nhu moi bar,
    # nen do la mot dieu kien LUON DUNG deo lot mot co che. Pha len phai do voi
    # bien TREN, thung xuong phai do voi bien DUOI.
    ra = []
    for ten, t in _muc_gia():
        if "tren" in ten or "kijun" in ten:
            ra.append(_spec(
                _ten("pha", ten), "pha_vo", 1,
                [{"trai": GIA, "phep": ">", "phai": t}],
                "Pha mot muc ai cung nhin doi phai co dong tien that mua tiep "
                "o gia cao hon; phan dat them do la phi tra cho ben nhan rui ro.",
                giu_mac_dinh))
        if "duoi" in ten or "kijun" in ten:
            ra.append(_spec(
                _ten("thung", ten), "pha_vo", -1,
                [{"trai": GIA, "phep": "<", "phai": t}],
                "Thung muc ai cung nhin doi phai co ben ban that ban tiep o "
                "gia thap hon; phan re them do la phi tra cho ben nhan rui ro.",
                giu_mac_dinh))
    # DONCHIAN VIET TAY, co DO TRE ro rang. `cao_nhat(n)` gom ca nen hien tai
    # nen `high > cao_nhat(n)` luon dung; phai lui mot bar. Day la bay da ghi
    # trong `doc_ma._toan_hang` va no dang gia mot toan hang rieng.
    for n in (20, 55, 100):
        ra.append(_spec(
            _ten("dinh", n), "pha_vo", 1,
            [{"trai": GIA, "phep": ">",
              "phai": {"chi_bao": "tre", "n": 1,
                       "cua": {"chi_bao": "cao_nhat", "n": n,
                               "cua": {"chi_bao": "gia", "cot": "high"}}}}],
            "Vuot dinh n bar da dong doi ben mua chap nhan gia cao nhat ky "
            "gan; ho chi lam the khi buoc phai co hang.",
            giu_mac_dinh))
        ra.append(_spec(
            _ten("day", n), "pha_vo", -1,
            [{"trai": GIA, "phep": "<",
              "phai": {"chi_bao": "tre", "n": 1,
                       "cua": {"chi_bao": "thap_nhat", "n": n,
                               "cua": {"chi_bao": "gia", "cot": "low"}}}}],
            "Thung day n bar da dong doi ben ban chap nhan gia thap nhat ky "
            "gan; ho chi lam the khi buoc phai thoat hang.",
            giu_mac_dinh))
    return ra


def _khuon_thuan_xu_the(giu_mac_dinh: int) -> list[dict]:
    """Muc nhanh tren muc cham -> vao THUAN. Luan diem: dong tien lon khong
    vao het mot lan; no chia nho ra nhieu phien, nen huong da hinh thanh con
    keo dai them mot doan do duoc."""
    ra, ds = [], [x for x in _muc_gia() if x[0][:3] in ("ema", "sma", "wma", "smm")]
    for ten_n, t_n in ds:
        for ten_c, t_c in ds:
            if t_n.get("chi_bao") != t_c.get("chi_bao"):
                continue
            if int(t_n.get("n", 0)) >= int(t_c.get("n", 0)):
                continue
            ra.append(_spec(
                _ten("thuan", ten_n, ten_c), "xu_huong", 1,
                [{"trai": t_n, "phep": ">", "phai": t_c}],
                "Dong tien lon khong vao het mot lan ma chia ra nhieu phien, "
                "nen huong da hinh thanh con keo dai them mot doan do duoc.",
                giu_mac_dinh))
    return ra


def _khuon_ghep(giu_mac_dinh: int) -> list[dict]:
    """LAI GHEP QUA HO - cho ma tai lieu khong bao gio viet san.

    Mot kich hoat cua ho nay dat BEN TRONG mot bo loc cua ho khac. Vi du kinh
    dien: mua khi do cang cham day NHUNG chi trong luc gia con tren duong dai
    han. Hai ve do den tu hai truong phai doi lap nhau, nen khong ai viet ca -
    va chinh cho do la cho may co loi the.
    """
    ra = []
    loc_xu_the = [(t_ten, t) for t_ten, t in _muc_gia()
                  if t.get("chi_bao") in ("ema", "sma") and t.get("n") in (100, 200)]
    for ten_c, t_c, duoi, tren in _do_cang():
        for ten_l, t_l in loc_xu_the:
            ra.append(_spec(
                _ten("ghep", ten_c, duoi[0], "tren", ten_l),
                "quay_ve_trung_binh", 1,
                [{"trai": t_c, "phep": "<", "phai": {"hang": duoi[0]}},
                 {"trai": GIA, "phep": ">", "phai": t_l}],
                "Mua lai hoi trong xu huong len: ben ban ngan han bi ep ban, "
                "con ben mua dai han van con o do de do gia.",
                giu_mac_dinh))
            ra.append(_spec(
                _ten("ghep", ten_c, tren[-1], "duoi", ten_l),
                "quay_ve_trung_binh", -1,
                [{"trai": t_c, "phep": ">", "phai": {"hang": tren[-1]}},
                 {"trai": GIA, "phep": "<", "phai": t_l}],
                "Ban lai hoi trong xu huong xuong: ben mua ngan han tra gia "
                "cao, con ben ban dai han van con o do de ep xuong.",
                giu_mac_dinh))
    # LOC THEO SUC XU THE: cung mot pha vo, nhung chi lay luc thi truong that
    # su co huong. ADX thap la thi truong di ngang, noi moi pha vo deu gia.
    for ten_x, t_x, _thap, cao in _xu_the():
        for ten_m, t_m in _muc_gia():
            if "tren" not in ten_m:
                continue
            ra.append(_spec(
                _ten("phaloc", ten_m, ten_x, cao[0]), "pha_vo", 1,
                [{"trai": GIA, "phep": ">", "phai": t_m},
                 {"trai": t_x, "phep": ">", "phai": {"hang": cao[0]}}],
                "Chi nhan pha vo khi thi truong that su co huong: luc di ngang "
                "thi moi cu pha muc deu bi keo nguoc lai ngay trong phien.",
                giu_mac_dinh))
    # XAC NHAN BANG DAU: kich hoat cua ho gia, xac nhan bang mot chi bao CHIEU.
    for ten_ch, t_ch in _chieu():
        for ten_c, t_c, duoi, _tren in _do_cang()[:8]:
            ra.append(_spec(
                _ten("xacnhan", ten_c, duoi[0], ten_ch), "quay_ve_trung_binh", 1,
                [{"trai": t_c, "phep": "<", "phai": {"hang": duoi[0]}},
                 {"trai": t_ch, "phep": ">", "phai": {"hang": 0}}],
                "Cho den khi ap luc ban qua da da dut han moi vao, thay vi bat "
                "dao ngay luc no con dang chay - do la cho mat tien nhieu nhat.",
                giu_mac_dinh))
    return ra


def _khuon_nen_bien_dong(giu_mac_dinh: int) -> list[dict]:
    """Do rong dai co lai -> chuan bi no. Luan diem: bien dong co tu tuong
    quan; giai doan hep bat thuong thuong ket thuc bang mot cu dich manh, va
    do la luc phi quyen chon re so voi bien dong sap toi."""
    ra = []
    for cb, ten in (("bollinger", "bb"), ("keltner", "kc")):
        for n in (20, 50):
            t = {"chi_bao": cb, "n": n, "k": 2.0, "lay": "do_rong"}
            for v in (0.01, 0.02, 0.05):
                ra.append(_spec(
                    _ten("nen", ten, n, v), "bien_dong", 1,
                    [{"trai": t, "phep": "<", "phai": {"hang": v}}],
                    "Bien dong co tu tuong quan: giai doan hep bat thuong "
                    "thuong ket thuc bang mot cu dich manh chu khong tan dan.",
                    giu_mac_dinh))
    return ra


def _khuon_lich(giu_mac_dinh: int) -> list[dict]:
    """Hieu ung LICH. Luan diem: dong tien co lich - quy can bang danh muc
    cuoi thang, phien My mo, ngay dao han. Do la rang buoc VAN HANH cua nguoi
    khac, khong phai mot mau ve ra tu gia."""
    ra = []
    for gio in (0, 2, 7, 8, 13, 14, 20):
        ra.append(_spec(
            _ten("gio", gio), "phien", 1,
            [{"trai": {"chi_bao": "gio"}, "phep": "==", "phai": {"hang": gio}}],
            "Dong tien co lich: phien mo cua va gio chuyen giao la rang buoc "
            "van hanh cua nguoi khac, khong phai mau ve ra tu gia.",
            giu_mac_dinh))
    for thu in (0, 1, 2, 3, 4):
        ra.append(_spec(
            _ten("thu", thu), "lich", 1,
            [{"trai": {"chi_bao": "ngay_trong_tuan"}, "phep": "==",
              "phai": {"hang": thu}}],
            "Quy can bang danh muc va dong tien luong theo lich tuan, nen mot "
            "so ngay mang dong lenh khong do gia sinh ra.",
            giu_mac_dinh))
    return ra


def _khuon_chuoi_lien_tiep(giu_mac_dinh: int) -> list[dict]:
    """N nen giam LIEN TIEP -> mua. Luan diem: mot chuoi dai khong phai tin
    tuc moi moi ngay, ma thuong la MOT lenh lon duoc chia nho ra chay dan.
    Khi no chay xong thi ap luc bien mat dot ngot, khong tan dan."""
    ra = []
    for k in (3, 4, 5, 6):
        ra.append(_spec(
            _ten("chuoi_giam", k), "quay_ve_trung_binh", 1,
            [{"trai": {"chi_bao": "dem_lien_tiep",
                       "khi": {"trai": GIA, "phep": "<",
                               "phai": {"chi_bao": "tre", "n": 1, "cua": GIA}}},
              "phep": ">=", "phai": {"hang": k}}],
            "Chuoi giam dai thuong la MOT lenh lon chia nho chay dan, khong "
            "phai tin xau moi moi ngay; chay xong thi ap luc tat dot ngot.",
            giu_mac_dinh))
        ra.append(_spec(
            _ten("chuoi_tang", k), "quay_ve_trung_binh", -1,
            [{"trai": {"chi_bao": "dem_lien_tiep",
                       "khi": {"trai": GIA, "phep": ">",
                               "phai": {"chi_bao": "tre", "n": 1, "cua": GIA}}},
              "phep": ">=", "phai": {"hang": k}}],
            "Chuoi tang dai thuong la mot lenh mua lon chia nho chay dan; khi "
            "no het thi khong con ai do gia o muc do nua.",
            giu_mac_dinh))
    return ra


def _khuon_doi_pct(giu_mac_dinh: int) -> list[dict]:
    """Bien dong % qua n bar. Luan diem: mot cu dich qua lon trong thoi gian
    qua ngan hiem khi la dinh gia lai that - no la thanh khoan bi rut."""
    ra = []
    t_pct = lambda n: {"chi_bao": "doi_pct", "n": n, "cua": GIA}
    for n in (1, 3, 5, 10):
        for v in (0.02, 0.03, 0.05):
            ra.append(_spec(
                _ten("sut", n, v), "quay_ve_trung_binh", 1,
                [{"trai": t_pct(n), "phep": "<", "phai": {"hang": -v}}],
                "Cu dich qua lon trong thoi gian qua ngan hiem khi la dinh gia "
                "lai that; thuong la thanh khoan bi rut va no quay lai sau do.",
                giu_mac_dinh))
            ra.append(_spec(
                _ten("vot", n, v), "xu_huong", 1,
                [{"trai": t_pct(n), "phep": ">", "phai": {"hang": v}}],
                "Cu bat manh doi dong tien that; ben mua da lo dien thi thuong "
                "con phai mua tiep cho du khoi luong ho can.",
                giu_mac_dinh))
    return ra


def _khuon_moc_neo(giu_mac_dinh: int) -> list[dict]:
    """Gia so voi MOC KY (dong cua ky truoc, dinh/day ky truoc). Luan diem:
    nhung muc nay la moc TINH SO SACH cua nguoi khac - bang gia tham chieu,
    muc chot lai cua quy, gia dong cua de dinh gia NAV. Chung hut gia vi co
    nguoi that buoc phai giao dich quanh do."""
    ra = []
    for ky in ("ngay", "tuan", "thang"):
        for lay, chieu, luan in (
                ("dong_truoc", 1, "Dong cua ky truoc la gia tham chieu tren "
                                  "bang cua nguoi khac, nen co lenh that neo vao do."),
                ("thap_truoc", 1, "Day ky truoc la muc nhieu noi dat chan lo; "
                                  "qua no la cham vung ho buoc phai xu li."),
                ("cao_truoc", -1, "Dinh ky truoc la muc nhieu noi dat chot lai; "
                                  "cham no la cham vung ho buoc phai xu li.")):
            t = {"chi_bao": "moc_ky", "ky": ky, "lay": lay}
            ra.append(_spec(
                _ten("duoi_moc", ky, lay), "quay_ve_trung_binh", chieu,
                [{"trai": GIA, "phep": "<" if chieu == 1 else ">", "phai": t}],
                luan, giu_mac_dinh))
    return ra


def _khuon_hoi_ve_vwap(giu_mac_dinh: int) -> list[dict]:
    """Gia lech khoi VWAP -> ve. Luan diem: VWAP la gia THI HANH trung binh
    cua chinh phien do, tuc la con so ban moi gioi bi cham diem. Lech khoi no
    tao ap luc that len nguoi phai khop lenh."""
    ra = []
    for n in (20, 50, 100):
        t = {"chi_bao": "vwap", "n": n}
        ra.append(_spec(
            _ten("duoi_vwap", n), "quay_ve_trung_binh", 1,
            [{"trai": GIA, "phep": "<", "phai": t}],
            "VWAP la gia thi hanh trung binh ma ban moi gioi bi cham diem; "
            "lech khoi no tao ap luc that len nguoi buoc phai khop lenh.",
            giu_mac_dinh))
        ra.append(_spec(
            _ten("tren_vwap", n), "xu_huong", 1,
            [{"trai": GIA, "phep": ">", "phai": t}],
            "Giu tren gia thi hanh trung binh nghia la ben mua dang chiu tra "
            "cao hon mat bang - dau hieu cua nhu cau that, khong phai nhieu.",
            giu_mac_dinh))
    return ra


def _khuon_macd(giu_mac_dinh: int) -> list[dict]:
    """MACD - CHI dung DAU va phep CAT, khong bao gio dung do lon.

    `macd` la hieu cua hai duong gia nen do lon cua no theo thang gia: mot
    nguong nhu `macd < 0,0034` chi dung cho dung mot tai san o dung mot thoi
    ky. Dau va phep cat thi khong thang do gi ca.
    """
    ra = []
    for nhanh, cham in ((12, 26), (5, 35)):
        goc = {"chi_bao": "macd", "nhanh": nhanh, "cham": cham, "cot": "close"}
        ra.append(_spec(
            _ten("macd", nhanh, cham, "duong"), "xu_huong", 1,
            [{"trai": goc, "phep": ">", "phai": {"hang": 0}}],
            "Trung binh nhanh tren trung binh cham nghia la dong mua moi dang "
            "den nhanh hon mat bang cu - huong da hinh thanh.",
            giu_mac_dinh))
        ra.append(_spec(
            _ten("macd", nhanh, cham, "cat_tin_hieu"), "xu_huong", 1,
            [{"trai": goc, "phep": "cheo_len",
              "phai": dict(goc, lay="tin_hieu")}],
            "Cat len duong tin hieu la luc toc do cua dong mua vuot chinh muc "
            "trung binh gan day cua no - diem gia toc, khong phai diem dat.",
            giu_mac_dinh))
    return ra


def _khuon_che_do_bien_dong(giu_mac_dinh: int) -> list[dict]:
    """CHE DO BIEN DONG do bang PHAN VI, khong bang gia tri tho.

    Day la cho `ngu_phap` da tra gia mot lan: nguong `atr14 < 0,003472` hoc tu
    train kich hoat **1.719 lan o train va 0 lan o holdout**, vi mot con so
    theo thang gia bien ca co che thanh co che cua MOT tai san o MOT thoi ky.

    `phan_vi(cua=atr)` do dung cau hoi do - "bien dong dang thap so voi CHINH
    no" - nhung tra ve mot ty le 0-1. Nguong tren no chuyen duoc sang ma khac
    va sang thoi ky khac, dung nguyen tac `ngoai_sinh`: giu TY LE KICH HOAT,
    khong giu con so.
    """
    ra = []
    for n_atr in (14, 20):
        for n_xep in (100, 250):
            t = {"chi_bao": "phan_vi", "n": n_xep,
                 "cua": {"chi_bao": "atr", "n": n_atr}}
            for v in (0.1, 0.2):
                ra.append(_spec(
                    _ten("vol_thap", n_atr, n_xep, v), "bien_dong", 1,
                    [{"trai": t, "phep": "<", "phai": {"hang": v}}],
                    "Bien dong co tu tuong quan nen giai doan hep bat thuong "
                    "thuong ket thuc bang mot cu dich manh; do bang phan vi de "
                    "nguong con nghia tren ma khac.",
                    giu_mac_dinh))
            for v in (0.8, 0.9):
                ra.append(_spec(
                    _ten("vol_cao", n_atr, n_xep, v), "bien_dong", -1,
                    [{"trai": t, "phep": ">", "phai": {"hang": v}}],
                    "Bien dong o vung cao cua chinh no thuong keo theo hoan "
                    "lai: phi rui ro da duoc tra qua tay, ai ban no luc do "
                    "duoc tra hau.",
                    giu_mac_dinh))
    return ra


def _khuon_fibo(giu_mac_dinh: int) -> list[dict]:
    """Thoai lui Fibonacci. Luan diem KHONG phai "con so than ki": cac muc nay
    duoc ve san tren man hinh cua rat nhieu nguoi, nen lenh cho va chan lo dong
    lai quanh do. Cai lam no chay la SU DONG THUAN, khong phai ty le."""
    ra = []
    for n in (34, 55, 89):
        for muc in (0.382, 0.5, 0.618):
            ra.append(_spec(
                _ten("fibo_cham", n, muc), "quay_ve_trung_binh", 1,
                [{"trai": GIA, "phep": "cheo_xuong",
                  "phai": {"chi_bao": "fibo", "n": n, "lay": muc}}],
                "Cac muc thoai lui duoc ve san tren man hinh rat nhieu nguoi "
                "nen lenh cho va chan lo dong lai quanh do; su dong thuan lam "
                "no chay, khong phai ban than ty le.",
                giu_mac_dinh))
        ra.append(_spec(
            _ten("fibo_sau", n), "quay_ve_trung_binh", 1,
            [{"trai": {"chi_bao": "fibo", "n": n, "lay": "vi_tri"},
              "phep": ">", "phai": {"hang": 0.786}}],
            "Thoai lui gan het song truoc la vung nhung ai vao muon nhat dang "
            "lo; ho thoat ra thi ap luc ban can kiet nhanh.",
            giu_mac_dinh))
    return ra


def _khuon_dong_tien(giu_mac_dinh: int) -> list[dict]:
    """KHOI LUONG va OBV so voi CHINH TRUNG BINH CUA NO.

    Luan diem: khoi luong la thu duy nhat trong bang gia khong phai y kien - no
    la so nguoi da that su phai giao dich. Mot cu dich kem khoi luong bat
    thuong nghia la co ben buoc phai xong hang, khong phai co ben doi y.

    KHONG so khoi luong voi mot hang so: so hop dong moi bar khac han giua cac
    ma va truot theo nam. So voi trung binh cua chinh no thi ty le do giu duoc
    y nghia khi chuyen ma - dung nguyen tac cua `ngoai_sinh`.
    """
    ra = []
    for cb, ten in (("khoi_luong", "kl"), ("obv", "obv")):
        goc = {"chi_bao": cb}
        for n in (20, 50, 100):
            tb_ = {"chi_bao": "tb", "n": n, "cua": dict(goc)}
            ra.append(_spec(
                _ten(ten, "tren_tb", n), "dong_tien", 1,
                [{"trai": dict(goc), "phep": ">", "phai": tb_}],
                "Khoi luong la thu duy nhat trong bang gia khong phai y kien - "
                "no la so nguoi da that su phai giao dich; vuot muc thuong le "
                "nghia la co ben buoc phai xong hang.",
                giu_mac_dinh))
    return ra


def _khuon_nen_manh(giu_mac_dinh: int) -> list[dict]:
    """THAN NEN so voi BIEN DO cua chinh nen do.

    Luan diem: mot nen than dai nghia la ben thang giu duoc gia toi tan luc
    dong cua - khong ai keo lai duoc. Nen than ngan (rau dai hai dau) nghia la
    ca hai ben deu co mat va khong ben nao thang, tuc thong tin nguoc han.

    Phai do than nen theo BIEN DO cua chinh no, khong theo pip: mot nen 30 pip
    la khong lo tren EURUSD va la nhieu tren XAUUSD.
    """
    ra = []
    do_dai = {"chi_bao": "tuyet_doi", "cua": {"chi_bao": "than_nen"}}
    for k in (0.6, 0.75):
        ra.append(_spec(
            _ten("nen_dac", k), "bien_dong", 1,
            [{"trai": do_dai, "phep": ">",
              "phai": {"chi_bao": "tuyen_tinh",
                       "toan_hang": [{"chi_bao": "bien_do"}], "he_so": [k]}},
             {"trai": {"chi_bao": "than_nen"}, "phep": ">", "phai": {"hang": 0}}],
            "Nen than dai nghia la ben thang giu duoc gia toi tan luc dong cua, "
            "khong ai keo lai duoc - do la dau hieu mot ben het hang de ban.",
            giu_mac_dinh))
    for k in (0.2, 0.3):
        ra.append(_spec(
            _ten("nen_rong", k), "bien_dong", 1,
            [{"trai": do_dai, "phep": "<",
              "phai": {"chi_bao": "tuyen_tinh",
                       "toan_hang": [{"chi_bao": "bien_do"}], "he_so": [k]}}],
            "Than ngan giua bien do rong nghia la ca hai ben deu co mat va "
            "khong ben nao thang - thong tin nguoc han voi mot nen dac.",
            giu_mac_dinh))
    return ra


def _khuon_dau_xu_the(giu_mac_dinh: int) -> list[dict]:
    """GOC · DUONG XU HUONG · DONG LUONG - chi dung DAU, khong dung do lon.

    Ca ba deo theo don vi gia: do 19/09 tren khung tong hop, `goc` chay trong
    -22,8..21,1 va con so do se khac han tren mot ma co gia khac. Nhung DAU cua
    chung thi khong thang do gi ca.
    """
    ra = []
    for cb, ten, luan in (
            ("goc", "goc", "Do doc duong hoi quy duong nghia la ben mua dang "
                           "tra cao dan mot cach co he thong, khong phai mot cu nhay le."),
            ("duong_xu_huong", "dxh", "Gia nam tren duong khop cua chinh no "
                                      "nghia la do lech dang nghieng ve mot phia - mot ben dang phai duoi."),
            ("dong_luong", "dl", "Dong luong duong nghia la muc gia phai tra "
                                 "hom nay cao hon ky truoc; ai con phai mua thi con phai tra them.")):
        for n in (14, 30, 60):
            ra.append(_spec(
                _ten(ten, n, "duong"), "xu_huong", 1,
                [{"trai": {"chi_bao": cb, "n": n, "cot": "close"}, "phep": ">",
                  "phai": {"hang": 0}}], luan, giu_mac_dinh))
            ra.append(_spec(
                _ten(ten, n, "am"), "xu_huong", -1,
                [{"trai": {"chi_bao": cb, "n": n, "cot": "close"}, "phep": "<",
                  "phai": {"hang": 0}}], luan, giu_mac_dinh))
    return ra


def _khuon_lich_thang(giu_mac_dinh: int) -> list[dict]:
    """HIEU UNG DAU/CUOI THANG va MUA VU.

    Luan diem: dong tien huu tri va quy chi so mua theo LICH LUONG, khong theo
    gia. Cuoi thang la luc quy can bang lai danh muc va luc tien luong moi vao
    thi truong - ca hai deu la rang buoc van hanh cua nguoi khac.
    """
    ra = []
    for k in (2, 3, 5):
        ra.append(_spec(
            _ten("dau_thang", k), "lich", 1,
            [{"trai": {"chi_bao": "ngay_trong_thang"}, "phep": "<=",
              "phai": {"hang": k}}],
            "Dong tien huu tri va quy chi so mua theo lich luong chu khong theo "
            "gia; dau thang la luc tien moi vao thi truong.",
            giu_mac_dinh))
        ra.append(_spec(
            _ten("cuoi_thang", 31 - k), "lich", 1,
            [{"trai": {"chi_bao": "ngay_trong_thang"}, "phep": ">=",
              "phai": {"hang": 31 - k}}],
            "Cuoi thang la luc quy can bang lai danh muc - ho phai giao dich "
            "du gia co hop hay khong, va do la rang buoc van hanh.",
            giu_mac_dinh))
    for th in (1, 5, 9, 11, 12):
        ra.append(_spec(
            _ten("thang", th), "lich", 1,
            [{"trai": {"chi_bao": "thang"}, "phep": "==", "phai": {"hang": th}}],
            "Mua vu cua dong tien: nam tai chinh, ky bao cao va lich nghi lam "
            "mot so thang mang dong lenh khac han cac thang con lai.",
            giu_mac_dinh))
    return ra


def _khuon_gia_khoi_luong(giu_mac_dinh: int) -> list[dict]:
    """TUONG QUAN giua GIA va KHOI LUONG - do [-1, 1] nen so hang so duoc.

    Luan diem: gia len kem khoi luong len la co ben that dang gom; gia len ma
    khoi luong tut la het nguoi ban chu khong phai co nguoi mua. Hai tinh
    huong do nhin giong het nhau tren bieu do gia.
    """
    ra = []
    for n in (20, 50):
        t = {"chi_bao": "tuong_quan", "n": n,
             "toan_hang": [{"chi_bao": "gia", "cot": "close"},
                           {"chi_bao": "khoi_luong"}]}
        for v in (0.3, 0.5):
            ra.append(_spec(
                _ten("gia_kl_thuan", n, v), "dong_tien", 1,
                [{"trai": t, "phep": ">", "phai": {"hang": v}}],
                "Gia len kem khoi luong len la co ben that dang gom hang; gia "
                "len ma khoi luong tut chi la het nguoi ban - hai thu nhin "
                "giong het nhau tren bieu do gia.",
                giu_mac_dinh))
        for v in (-0.5, -0.3):
            ra.append(_spec(
                _ten("gia_kl_nghich", n, v), "dong_tien", -1,
                [{"trai": t, "phep": "<", "phai": {"hang": v}}],
                "Gia len trong khi khoi luong can dan la dau hieu ben mua da "
                "het nguoi noi tiep, du duong gia van con dep.",
                giu_mac_dinh))
    return ra


def _khuon_che_do_lat(giu_mac_dinh: int) -> list[dict]:
    """CO CHE DO CO NHO: bat o mot nguong, va chi tat o mot nguong KHAC.

    Luan diem: che do thi truong khong doi tung bar, no doi tung doan - vi cai
    lam no doi la vi the cua nhung nguoi lon, ma ho vao ra trong nhieu phien
    chu khong trong mot nen. Mot bo loc khong nho thi o vung ranh gioi se bat
    tat lien tuc, va moi lan tat la mot lan dong lenh giua doan - dung luc te
    nhat. Mot co co nho thi giu nguyen cho den khi co bang chung NGUOC.

    Khoang giua hai nguong la vung tre. No khong phai tham so trang tri: no
    chinh la phat bieu "bao nhieu bang chung thi du de tin rang che do da doi".

    `trang_thai_lat` tra ve -1 / 0 / +1 nen dung ca hai chieu: `> 0` la dang o
    che do TANG, `< 0` la dang o che do GIAM.
    """
    ra = []
    for n in CHU_KY_NGAN:
        rsi = {"chi_bao": "rsi", "n": n}
        for bat, tat in ((55.0, 45.0), (60.0, 50.0)):
            co = {"chi_bao": "trang_thai_lat",
                  "len": {"trai": rsi, "phep": ">", "phai": {"hang": bat}},
                  "xuong": {"trai": rsi, "phep": "<", "phai": {"hang": tat}}}
            ra.append(_spec(
                _ten("lat_rsi", n, bat, tat, "tang"), "xu_huong", 1,
                [{"trai": co, "phep": ">", "phai": {"hang": 0}}],
                "Che do doi theo doan chu khong theo bar, vi nguoi lon vao ra "
                "trong nhieu phien; giu nguyen huong cho den khi co bang chung "
                "nguoc thi khong bi dong lenh giua doan.",
                giu_mac_dinh))
            ra.append(_spec(
                _ten("lat_rsi", n, bat, tat, "giam"), "xu_huong", -1,
                [{"trai": co, "phep": "<", "phai": {"hang": 0}}],
                "Chieu con lai cua cung mot co: da vao che do giam thi giu ban "
                "cho den khi suc mua lay lai duoc nguong tren, thay vi dao "
                "chieu o moi lan gia nhich len.",
                giu_mac_dinh))
    return ra


def _khuon_bien_dong_do_lech(giu_mac_dinh: int) -> list[dict]:
    """BIEN DONG theo DO LECH CHUAN, chuan hoa bang `phan_vi`.

    Luan diem: bien dong co tu tuong quan; giai doan hep bat thuong thuong ket
    thuc bang mot cu dich manh, va do la luc phi quyen chon re so voi bien dong
    sap toi.

    ## KHAC GI `che_do_bien_dong` (dung ATR)

    Hai khuon nay nhin giong nhau va co cung cau truc, nen phai noi ro cho
    khac - neu khong chung la mot phep thu duoc tra tien HAI LAN suat FDR.

    `atr` tinh tren BIEN DO THAT: no om ca khoang nhay giua hai nen. `do_lech`
    tinh tren gia DONG CUA: no khong thay khoang nhay nao ca. Hai phep do do
    tach nhau dung o cho quan trong - mot thi truong dung yen trong phien roi
    nhay qua dem co ATR cao va do lech thap.

    Nen day khong phai hai ban cua mot y tuong, ma la hai cau hoi: "bien dong
    co lon khong" va "bien dong TRONG PHIEN co lon khong"."""
    ra = []
    for n_atr in (14, 20):
        for n_xep in (100, 250):
            t = {"chi_bao": "phan_vi", "n": n_xep,
                 "cua": {"chi_bao": "do_lech", "n": n_atr, "cua": GIA}}
            for v in (0.1, 0.2):
                ra.append(_spec(
                    _ten("vol_thap", n_atr, n_xep, v), "bien_dong", 1,
                    [{"trai": t, "phep": "<", "phai": {"hang": v}}],
                    "Bien dong co tu tuong quan nen giai doan hep bat thuong "
                    "thuong ket thuc bang mot cu dich manh; do bang phan_vi de "
                    "nguong con co nghia tren ma khac va thoi ky khac.",
                    giu_mac_dinh))
            for v in (0.8, 0.9):
                ra.append(_spec(
                    _ten("vol_cao", n_atr, n_xep, v), "bien_dong", -1,
                    [{"trai": t, "phep": ">", "phai": {"hang": v}}],
                    "Bien dong o vung cao so voi chinh no thuong keo theo hoan "
                    "lai: phi rui ro da duoc tra qua tay, ai ban no luc do "
                    "duoc tra hau.",
                    giu_mac_dinh))
    return ra


def _khuon_doi_tuyet_doi(giu_mac_dinh: int) -> list[dict]:
    """THAY DOI qua n bar - chi dung DAU, khong dung do lon.

    Do lon cua `doi` theo don vi gia nen mot nguong nhu `doi(5) > 0,005` chi
    dung cho dung mot ma o dung mot thoi ky. Dau thi khong thang do gi ca.

    Luan diem: `doi(n) > 0` la cau hoi "gia hom nay co cao hon n bar truoc
    khong" - phep do THO NHAT cua mot xu huong, va tho la co chu dich. Moi bo
    loc tinh vi hon deu them tham so, ma moi tham so la mot cho de khop vao
    qua khu. Neu mot cap khong tra tien cho phep do tho nhat thi kho tin la no
    tra tien cho mot phien ban da chinh.

    Day cung la cai MOC de doc cac khuon xu huong khac: mot khuon nhieu tham so
    ma khong hon duoc khuon nay thi phan hon do den tu dau?
    """
    ra = []
    for n in (3, 5, 10):
        ra.append(_spec(
            _ten("doi_duong", n), "xu_huong", 1,
            [{"trai": {"chi_bao": "doi", "n": n, "cua": GIA}, "phep": ">",
              "phai": {"hang": 0}}],
            "Phep do tho nhat cua xu huong: gia cao hon n bar truoc. Ai con "
            "phai mua thi con phai tra them, va cho do khong can mot bo loc "
            "nao de nhin thay.",
            giu_mac_dinh))
        ra.append(_spec(
            _ten("doi_am", n), "xu_huong", -1,
            [{"trai": {"chi_bao": "doi", "n": n, "cua": GIA}, "phep": "<",
              "phai": {"hang": 0}}],
            "Chieu con lai cua cung phep do: gia thap hon n bar truoc. Ai con "
            "phai thoat hang thi con phai ban re hon nguoi truoc.",
            giu_mac_dinh))
    return ra


#: THU TU LA THU TU UU TIEN. Khuon dung truoc duoc de truoc, nen mot han ngach
#: nho luon la TAP CON DAU cua han ngach lon - xin 20 hom nay roi 100 ngay mai
#: khong phai dang ky lai tu dau.
KHUON = (
    ("qua_da_hoi_ve", _khuon_qua_da_hoi_ve),
    ("thuan_xu_the", _khuon_thuan_xu_the),
    ("pha_vo", _khuon_pha_vo),
    ("ghep_qua_ho", _khuon_ghep),
    ("nen_bien_dong", _khuon_nen_bien_dong),
    ("che_do_bien_dong", _khuon_che_do_bien_dong),
    ("chuoi_lien_tiep", _khuon_chuoi_lien_tiep),
    ("doi_pct", _khuon_doi_pct),
    ("moc_neo", _khuon_moc_neo),
    ("fibo", _khuon_fibo),
    ("hoi_ve_vwap", _khuon_hoi_ve_vwap),
    ("macd", _khuon_macd),
    ("dong_tien", _khuon_dong_tien),
    ("nen_manh", _khuon_nen_manh),
    ("dau_xu_the", _khuon_dau_xu_the),
    ("gia_khoi_luong", _khuon_gia_khoi_luong),
    ("lich_thang", _khuon_lich_thang),
    ("lich_phien", _khuon_lich),
    ("che_do_lat", _khuon_che_do_lat),
    ("bien_dong_do_lech", _khuon_bien_dong_do_lech),
    ("doi_tuyet_doi", _khuon_doi_tuyet_doi),
)


# ------------------------------------------------------------------- MAY DE
def nguong_dat_duoc(d: dict) -> bool:
    """Nguong nay co BAO GIO cham toi duoc khong - tra loi duoc ma khong can
    du lieu.

    `phan_vi(n)` la thu hang trong cua so n bar, nen no chi nhan duoc n gia tri
    roi rac: voi n = 5 thi gia tri nho nhat la 1/5 = 0,20. Dieu kien
    `phan_vi(5) < 0,05` **khong bao gio dung**, tren moi tai san, o moi thoi ky.

    Do 19/09/2026 tren lo dau tien: 6 co che dang nay lot qua `kiem_khai_bao`
    (cu phap hoan toan hop le) roi kich hoat 0,0% - nhung KHONG mot cong nao
    goi ten duoc van de, vi "kich hoat 0%" trong y het mot co che qua hiem.
    Moi cai nhu vay an mot suat FDR de doi lay mot cau tra loi da biet truoc.

    Cung ho voi `_kiem_hien_nhien` cua ngu phap: bat cai LUON SAI bang mot phep
    so thay vi bang mot luot backtest.
    """
    trai, phai = d.get("trai") or {}, d.get("phai") or {}
    if "hang" not in phai:
        return True
    if str(trai.get("chi_bao", "")).lower() != "phan_vi":
        return True
    try:
        n = int(trai.get("n") or 0)
        v = float(phai["hang"])
    except (TypeError, ValueError):
        return True
    if n < 2:
        return True
    buoc = 1.0 / n
    phep = d.get("phep", ">")
    if phep in ("<", "<="):
        return v >= buoc          # duoi buoc dau tien = khong bao gio dung
    if phep in (">", ">="):
        return v <= 1.0 - buoc
    return True


def _hop_thang(d: dict) -> bool:
    """Mot ve co so sanh duoc khong. Day la phep BAT BUOC - xem docstring."""
    trai, phai = d.get("trai"), d.get("phai")
    tt = thang_do(trai)
    if "hang" in (phai or {}):
        if quanh_khong(trai):
            # Chi DAU moi khong thang do. Mot nguong KHAC 0 tren mot toan hang
            # theo don vi gia la nguong cua MOT tai san o MOT thoi ky - dung
            # cai bay `atr14 < 0,003472` (train 1.719 lan, holdout 0 lan).
            return float(phai["hang"]) == 0.0
        # So voi HANG SO chi co nghia khi ve trai co chan, co dau, dem duoc,
        # hoac la lich.
        return tt in (THANG_CHAN, THANG_CHIEU, THANG_LICH, THANG_DEM)
    return tt == thang_do(phai) and tt != THANG_KHAC


def duc(han_ngach: int = 500, kho: list | None = None,
        khuon: str | None = None, giu: int = 5) -> list[dict]:
    """DE CO CHE. Tra danh sach spec DA qua cong cu phap, KHONG trung nhau.

    `kho` la cac co che DA CO - de trung cai da co la tra tien FDR hai lan cho
    mot cau tra loi, nen chung bi loai theo VAN TAY (`van_tay_dieu_kien`) chu
    khong theo ten: hai co che cung noi dung du khac ten van la mot.

    Xac dinh hoan toan: khong RNG, thu tu theo `KHUON`.
    """
    da_co = {NP.van_tay_dieu_kien(s) for s in (kho or [])}
    ra, thay, ten_da_co = [], set(), set()
    for ten_khuon, ham in KHUON:
        if khuon and ten_khuon != khuon:
            continue
        for s in ham(giu):
            if len(ra) >= han_ngach:
                return ra
            if not all(_hop_thang(d) and nguong_dat_duoc(d) for d in s["vao"]):
                continue
            if NP.kiem_khai_bao(s):
                continue               # khong bao gio de ra spec hong
            vt = NP.van_tay_dieu_kien(s)
            if vt in da_co or vt in thay:
                continue
            # TRUNG TEN GIUA HAI KHUON: DOI TEN, khong duoc bo.
            #
            # Ban cu bo cai den sau, va no bo TRONG IM LANG. Do 19/09/2026:
            # khuon `bien_dong_do_lech` dung cung nhan tham so voi
            # `che_do_bien_dong` (`vol_thap_14_100_0_1`...) nen ca **16** co
            # che cua no bien mat khoi lo day du - khuon chay rieng thi ra 16,
            # chay chung thi ra 0, va khong co mot dong nao bao.
            #
            # Hai co che KHAC VAN TAY la hai phep thu khac nhau; trung ten chi
            # la trung nhan. Bo mot phep thu vi nhan cua no da co nguoi dung la
            # mat mot cau hoi ma khong ai biet da mat.
            if s["ten"] in ten_da_co:
                s["ten"] = NP.chuan_hoa_ten("%s_%s" % (s["ten"], ten_khuon))
                if s["ten"] in ten_da_co:
                    continue           # van trung sau khi doi -> that su la ban sao
            ten_da_co.add(s["ten"])
            thay.add(vt)
            s["khuon"] = ten_khuon
            ra.append(s)
    return ra


def dang_ky_lo(specs: list[dict]) -> dict:
    """TIEN DANG KY mot lo truoc khi ai cham vao du lieu.

    `plan_hash` bam tren VAN TAY NOI DUNG da sap xep, khong tren ten: doi ten
    ca lo khong duoc lam no thanh mot lo khac. `so_phep_thu` la so suat FDR lo
    nay dat - `cong.lord_v2` can dung con so do de tinh cho dung.

    De nhieu la luong thien neu tra du gia. De nhieu roi chi khai vai cai dep
    la gian lan. Ham nay ton tai de cai gia luon duoc khai truoc.
    """
    vt = sorted(NP.van_tay_dieu_kien(s) for s in specs)
    h = hashlib.sha256("\n".join(vt).encode("utf-8")).hexdigest()[:32]
    return {"plan_hash": h, "so_phep_thu": len(vt), "van_tay": vt,
            "ten": [s.get("ten") for s in specs],
            "khuon": sorted({s.get("khuon", "") for s in specs} - {""})}


# ---------------------------------- RAI LUOI QUANH MOT CO CHE DA CO
#: Ba diem quanh gia tri tac gia chon, theo TY LE. Ba chu khong nhieu hon: moi
#: diem them la mot suat FDR, va muc dich o day khong phai tim gia tri tot nhat
#: (viec cua `do_on_dinh`/`to_hop`) ma la biet HINH DANG quanh diem tac gia
#: chon - cao nguyen hay cai gai.
_TY_LE_CHU_KY = (0.5, 2.0)

#: Nguong thi dich theo DO RONG CUA THANG, khong theo ty le. `rsi < 30` nhan
#: doi thanh `rsi < 60` la doi han y nghia co che (tu "qua ban" thanh "duoi
#: trung binh"), trong khi `rsi < 25` va `rsi < 35` van la cung mot y tuong o
#: hai do chat khac nhau - do moi la cai ta muon do.
_BUOC_NGUONG = {
    "rsi": 5.0, "stochastic": 5.0, "adx": 5.0, "cci": 50.0,
    "zscore": 0.5, "ibs": 0.05, "phan_vi": 0.05, "doi_pct": 0.01,
}


def _buoc_cua(t: dict) -> float | None:
    cb = str((t or {}).get("chi_bao", "")).lower()
    if str((t or {}).get("lay", "")).lower() in ("phan_tram_b", "do_rong"):
        return 0.05
    return _BUOC_NGUONG.get(cb)


def bien_the(spec: dict, han_ngach: int = 24, so_buoc: int = 2) -> list[dict]:
    """Mot co che -> cac BAN THAY SO cua chinh no. Khong tra lai ban goc.

    Chu du an: *"10 trader chau A co 20 kieu dung Ichimoku"* - bien thien nam o
    NGUONG va CACH GHEP chu khong o ban than chi bao. 20 kieu dung khong phai
    20 lan boc tai lieu; la mot chi bao cong mot luoi tham so, do may sinh.

    DOI TUNG THAM SO MOT, khong duyet tich Descartes. Hai ly do:
      * mot co che 4 tham so x 5 diem la 625 o, tuc 625 suat FDR cho mot y
        tuong - khong con la do hinh dang nua ma la dao mo nhieu.
      * doi mot truc moi tra loi duoc "truc nao nhay" - thu can de biet co che
        dung tren cao nguyen hay tren cai gai.

    NGUONG va CHU KY dich theo hai cach khac nhau, co chu dich: chu ky theo TY
    LE (x0,5 · x2), nguong theo DO RONG CUA THANG (`rsi` +-5 chu khong phai
    x2 - `rsi < 60` khong con la co che qua ban nua).
    """
    goc_vt = NP.van_tay_dieu_kien(spec)
    ts = NP.tham_so_cua(spec)
    ra, thay = [], {goc_vt}
    for khoa in sorted(ts):
        if khoa == "giu":
            continue
        gt = ts[khoa]
        if not isinstance(gt, (int, float)) or isinstance(gt, bool):
            continue
        moc = _diem_quanh(spec, khoa, float(gt), so_buoc)
        for v in moc:
            moi = NP.ap_tham_so(spec, {khoa: v})
            moi = dict(moi, ten=NP.chuan_hoa_ten(
                "%s_%s%s" % (spec.get("ten", "he"), khoa.replace("vao0_", ""),
                             _so_ten(v))),
                nguon="hephaestus:bien_the")
            if not all(_hop_thang(d) and nguong_dat_duoc(d) for d in moi["vao"]):
                continue
            if NP.kiem_khai_bao(moi):
                continue
            vt = NP.van_tay_dieu_kien(moi)
            if vt in thay:
                continue
            thay.add(vt)
            ra.append(moi)
            if len(ra) >= han_ngach:
                return ra
    return ra


def _so_ten(v: float) -> str:
    return ("%g" % v).replace(".", "_").replace("-", "am")


def _diem_quanh(spec: dict, khoa: str, gt: float, so_buoc: int) -> list[float]:
    """Cac gia tri thu quanh `gt`. Chu ky theo ty le, nguong theo buoc thang."""
    if khoa.endswith("_n"):
        ra = [int(round(gt * r)) for r in _TY_LE_CHU_KY]
        return [float(x) for x in ra if x >= 2 and x != int(gt)]
    t = _toan_hang_cua_khoa(spec, khoa)
    buoc = _buoc_cua(t)
    if buoc is None:
        return []               # khong biet thang cua nguong -> khong doan
    ra = []
    for k in range(1, so_buoc + 1):
        ra += [gt - k * buoc, gt + k * buoc]
    return [round(x, 6) for x in ra]


def _toan_hang_cua_khoa(spec: dict, khoa: str) -> dict:
    """`vao0_phai_hang` -> toan hang VE TRAI cua dieu kien 0 (ve mang thang do).

    Nguong nam o ve phai nhung THANG DO cua no do ve trai quyet dinh: `< 30`
    la 30 diem RSI hay 30 don vi gia la tuy ve trai la gi.
    """
    for phan in ("vao", "ra"):
        if not khoa.startswith(phan):
            continue
        con = khoa[len(phan):].lstrip("_")
        so = ""
        while con and con[0].isdigit():
            so, con = so + con[0], con[1:]
        ds = spec.get(phan) or []
        try:
            d = ds[int(so)]
        except (ValueError, IndexError):
            return {}
        return d.get("trai") or {}
    return {}


def ghep(a: dict, b: dict, giu: int | None = None) -> dict | None:
    """Ghep HAI co che thanh mot: vao lenh khi CA HAI cung dung.

    Chu du an: *"ket hop cac he thong va ly thuyet lai voi nhau"*. Dat mot kich
    hoat canh mot bo loc cho ra thu khong ban goc nao co - va do la cho may co
    loi the, vi khong tai lieu nao viet san mot co che thuoc hai truong phai.

    Tra `None` khi ghep khong co nghia:
      * NGUOC CHIEU - mua va ban cung luc khong phai mot co che, la mau thuan.
      * TRUNG NHAU - ghep mot co che voi chinh no chi lam ten dai ra.
    """
    if not a or not b:
        return None
    if int(a.get("chieu", 1)) != int(b.get("chieu", 1)):
        return None
    va, vb = a.get("vao") or [], b.get("vao") or []
    if not va or not vb:
        return None
    kh_a = {NP.van_tay_dieu_kien({"vao": [d]}) for d in va}
    kh_b = {NP.van_tay_dieu_kien({"vao": [d]}) for d in vb}
    if kh_b <= kh_a or kh_a <= kh_b:
        return None                       # mot cai da chua cai kia
    moi = {
        "ten": NP.chuan_hoa_ten("hp_va_%s_%s" % (a.get("ten", "a"),
                                                 b.get("ten", "b")))[:60],
        "ho": a.get("ho") or b.get("ho"),
        "chieu": int(a.get("chieu", 1)),
        "giu": int(giu or a.get("giu", 1)),
        "co_che": ("Ghep hai luan diem doc lap: %s VA %s. Phoi nhiem chi mo khi "
                   "ca hai cung dung, tuc doi hai ly do khac nhau cung chi ve "
                   "mot phia." % (str(a.get("co_che", ""))[:70].rstrip(". "),
                                  str(b.get("co_che", ""))[:70].rstrip(". "))),
        "vao": list(va) + [d for d in vb
                           if NP.van_tay_dieu_kien({"vao": [d]}) not in kh_a],
        "nguon": "hephaestus:ghep",
    }
    return None if NP.kiem_khai_bao(moi) else moi


def ghep_lo(specs: list[dict], han_ngach: int = 200) -> list[dict]:
    """Ghep doi mot cach XAC DINH tren mot danh sach co che.

    Duyet theo thu tu da cho, khong ngau nhien, de mot lo ghep co the tien dang
    ky y nhu mot lo duc.
    """
    ra, thay = [], set()
    for i, a in enumerate(specs):
        for b in specs[i + 1:]:
            s = ghep(a, b)
            if s is None:
                continue
            vt = NP.van_tay_dieu_kien(s)
            if vt in thay:
                continue
            thay.add(vt)
            ra.append(s)
            if len(ra) >= han_ngach:
                return ra
    return ra


# ----------------------------------------------------- NOI VAO KHO CO CHE
def nap(specs: list[dict], that: bool = False, df_kiem=None) -> dict:
    """De ra roi NAP vao kho. CHAY KHO o mac dinh - phai bao ro moi ghi.

    ## VI SAO MAC DINH LA CHAY KHO

    Ngay 19/09/2026, de "xem thu no chay khong", toi goi `them_co_che` mot lan
    tu dong lenh. No GHI THAT vao `config/co_che_dsl.json` ngay lap tuc - kho
    san xuat, thu ma ca he doc. Khong co gi hoi lai, khong co gi canh bao.

    Kho co che la du lieu san xuat va no da tung tut 2.975 -> 21 co che trong
    mot buoi sang vi nhung chuyen nho hon the (xem `ngu_phap.doc_kho`). Mot
    lenh go nham khong duoc phep sua no. Nen: `that=False` thi ham nay do het
    moi thu va bao cao, nhung khong cham vao kho.

    ## LUON TIEN DANG KY, KE CA KHI CHAY KHO

    Lo da sinh ra la da ton tai. Neu khong dang ky no, lan sau chay lai dung lo
    do se trong nhu mot lo MOI va FDR dem hai lan cho mot lan thu. `plan_hash`
    tra ve o day chinh la `economic_plan_hash` ma `cong.lord_v2` doi.

    ## `do_kich_hoat` PHAN BIET HAI THU KHAC NHAU

    `DA_DO`        co chuoi kiem, ty le kich hoat da duoc do that.
    `CHUA_DO_DUOC` khong nap duoc chuoi nao (vi du tren cloud, khong co `data/`)
                   nen phep do do KHONG CHAY. Bao "dat" luc do la noi doi: chua
                   ai do gi ca. Day la cung mot luat voi `CHUA_DO_DUOC` vs `AM`
                   ma du an dung o moi cho khac.
    """
    lo = dang_ky_lo(specs)
    kho = NP.doc_kho(cho_rong_khi_hong=True)
    da_co = {NP.van_tay_dieu_kien(s) for s in kho}

    co_chuoi = bool(NP._chuoi_do_them()) or df_kiem is not None
    ra = {**lo, "da_ghi": bool(that), "nhan": 0, "trung": 0, "tu_choi": 0,
          "ly_do": {}, "do_kich_hoat": "DA_DO" if co_chuoi else "CHUA_DO_DUOC"}

    for s in specs:
        if NP.van_tay_dieu_kien(s) in da_co:
            ra["trung"] += 1
            continue
        if not that:
            # Chay kho: kiem duoc gi thi kiem, nhung KHONG goi `them_co_che`
            # vi ham do ghi. Phep do ty le kich hoat nam trong do, nen ban chay
            # kho khong thay the duoc ban that - va `do_kich_hoat` noi ro dieu do.
            loi = NP.kiem_khai_bao(s)
            if loi:
                ra["tu_choi"] += 1
                ra["ly_do"][loi[0][:60]] = ra["ly_do"].get(loi[0][:60], 0) + 1
            else:
                ra["nhan"] += 1
            continue
        kq = NP.them_co_che(dict(s), df_kiem=df_kiem)
        if kq.get("nhan"):
            ra["nhan"] += 1
            da_co.add(NP.van_tay_dieu_kien(s))
        else:
            ra["tu_choi"] += 1
            for x in (kq.get("ly_do") or [])[:1]:
                ra["ly_do"][str(x)[:60]] = ra["ly_do"].get(str(x)[:60], 0) + 1
    return ra


# ------------------------------------------- NUA HAI: DAY NGUOC VE SEEKER
def _chi_bao_trong(t, ra: set) -> None:
    if isinstance(t, dict):
        cb = t.get("chi_bao")
        if isinstance(cb, str):
            ra.add(cb.lower())
        for v in t.values():
            _chi_bao_trong(v, ra)
    elif isinstance(t, list):
        for v in t:
            _chi_bao_trong(v, ra)


#: Chi bao KHONG tinh vao do phu: chung la toan tu bao ngoai hoac nguon gia
#: tran, co mat trong gan nhu moi co che nen dem chung lam nhoe bang.
_KHONG_TINH = {"gia", "tre", "tuyen_tinh", "tb_cua_cac", "cao_nhat_cua_cac",
               "thap_nhat_cua_cac", "tong_cua_cac", "tuyet_doi", "tong"}


def do_phu(kho: list[dict] | None = None) -> dict:
    """Ngu phap NOI DUOC gi, va kho DANG DUNG gi. Chenh lech la viec cua Seeker.

    Day la phep do tra loi dung cau chu du an hoi: he dang may mo trong bao
    nhieu phan cua cai no co the noi. Do 19/09: 54 toan hang noi duoc, 8 dang
    duoc dung.
    """
    if kho is None:
        kho = NP.doc_kho(cho_rong_khi_hong=True)
    dem: dict[str, int] = {}
    for s in kho:
        t: set = set()
        for nhom in ("vao", "ra"):
            _chi_bao_trong(s.get(nhom) or [], t)
        for cb in t - _KHONG_TINH:
            dem[cb] = dem.get(cb, 0) + 1
    noi_duoc = {c for c in NP.CHI_BAO_CO} - _KHONG_TINH
    return {"noi_duoc": sorted(noi_duoc), "dang_dung": dem,
            "bo_trong": sorted(noi_duoc - set(dem)),
            "so_noi_duoc": len(noi_duoc), "so_dang_dung": len(dem)}


#: Chi bao -> tu khoa di san. Ten DSL khong phai tu nguoi ta viet tren mang.
TU_KHOA = {
    "ichimoku": ["ichimoku kinko hyo", "tenkan kijun cross", "kumo breakout"],
    "keltner": ["keltner channel strategy", "keltner squeeze"],
    "vwap": ["vwap reversion", "anchored vwap", "vwap bands"],
    "supertrend": ["supertrend strategy", "supertrend atr trailing"],
    "heiken": ["heiken ashi strategy", "heikin ashi smoothed"],
    "mau_nen": ["candlestick pattern backtest", "engulfing pattern edge"],
    "donchian": ["donchian channel turtle", "donchian breakout"],
    "bollinger": ["bollinger band squeeze", "percent b mean reversion"],
    "fibo": ["fibonacci retracement backtest", "fib extension target"],
    "gann_sq9": ["gann square of nine", "gann angles trading"],
    "obv": ["on balance volume divergence"],
    "macd": ["macd histogram divergence", "macd zero cross"],
    "cci": ["cci extreme reversal", "commodity channel index strategy"],
    "stochastic": ["stochastic oscillator strategy", "stochastic divergence"],
    "moc_ky": ["monthly open level", "previous day close magnet"],
    "tuong_quan": ["pair correlation trading", "correlation filter"],
    "duong_xu_huong": ["trendline break backtest"],
    "goc": ["slope filter trading", "regression angle"],
    "phan_vi": ["percentile rank strategy"],
    "dem_lien_tiep": ["consecutive down days", "n day streak reversal"],
    "trang_thai_lat": ["regime switch filter"],
    "gann": ["gann fan"],
}


def tu_vung(kho: list[dict] | None = None, so_huong: int = 10) -> list[dict]:
    """Huong tim kiem DAY NGUOC ve SEEKER, uu tien cho TRONG.

    So do: *"Seeker khong tu nghi ra 'di tim Ichimoku'; Hephaestus bao no di."*

    Uu tien cho trong chu khong phai cho da day, vi them mot bai nua ve RSI
    khong lam kho rong ra mot ly nao. Chi bao khong co tu khoa thi bo qua -
    day nguoc mot cai ten DSL ma khong ai tren mang goi the la sai viec Seeker.
    """
    r = do_phu(kho)
    ra = []
    for cb in r["bo_trong"]:
        tk = TU_KHOA.get(cb)
        if not tk:
            continue
        ra.append({"chi_bao": cb, "tu_khoa": list(tk), "vi_sao":
                   "ngu phap tinh duoc `%s` nhung kho khong co co che nao dung"
                   % cb})
        if len(ra) >= so_huong:
            break
    return ra


# =========================================================================
# NUA BA: DE CAU HINH QUAN TRI LENH
# =========================================================================
# Hai nua tren de ra TIN HIEU VAO. Bang chung cua chinh du an noi do la nua IT
# GIA TRI HON:
#
#   * 18/09 tren AUDCAD: cung mot bo tham so luoi, chi bat/tat `tia_lenh` thi
#     holdout di tu +0,66%/nam len +13,26%/nam, sut giam tu -15,6% xuong -3,5%.
#     Tia lenh la TOAN BO khac biet.
#   * Cung phien do, 668 co che ENTRY qua MT5 tester that: **0** co che vua du
#     2 lenh/tuan vua Sharpe duong.
#   * `quan_tri.py`: *"entry co tinh SAI van cho 92-97%/nam"* voi lop luoi.
#
# Nen phan nay de ra CAU HINH cho `mo_phong_v2.mo_phong` - mot ho co che khong
# can tin hieu vao nao ca.

#: Buoc luoi (pip) - thua so 2 giua cac muc de luoi phu rong ma it o.
BUOC_LUOI = (15.0, 30.0, 60.0, 120.0)
#: TP tinh tu gia trung binh cua ro (pip).
TP_LUOI = (20.0, 40.0, 80.0)


def _cf(ten, khuon, nut, luan) -> dict:
    return {"ten": NP.chuan_hoa_ten("qt_" + ten), "khuon": khuon,
            "nut": dict(nut), "co_che": luan}


def van_tay_quan_tri(cf: dict) -> str:
    """Van tay theo NUT VAN, bo qua ten - hai cau hinh cung nut la mot."""
    return json.dumps(cf.get("nut") or {}, sort_keys=True, default=str)


def _qt_tran(_):
    """Luoi tran: chi buoc va TP. Luan diem: gia di qua mot muc nhieu lan hon
    so lan no di qua muc do MOT lan, nen ai dat lenh hai chieu quanh mot vung
    se duoc tra cho viec om chenh lech tam thoi."""
    ra = []
    for b in BUOC_LUOI:
        for tp in TP_LUOI:
            ra.append(_cf("tran_b%g_tp%g" % (b, tp), "luoi_tran",
                          {"buoc": b, "tp": tp},
                          "Gia di qua mot vung nhieu lan hon so lan no roi han "
                          "khoi do; ai om chenh lech tam thoi duoc tra cho viec "
                          "do, va tien do la phi thanh khoan."))
    return ra


def _qt_cat_hoa(_):
    """+ CAT HOA. Luan diem: ghep lenh moi nhat voi cu nhat rui dong ca cap
    hien thuc hoa phan hoi ve ma khong phai cho ca ro ve diem hoa von - tuc
    lay tien ve som hon nhieu, va giam dung cai chan lon nhat cua ro."""
    ra = []
    for b in (30.0, 60.0):
        for tu in (2, 3, 4):
            for bien in (0.0, 4.0):
                ra.append(_cf("cathoa_b%g_n%d_c%g" % (b, tu, bien),
                              "luoi_cat_hoa",
                              {"buoc": b, "tp": 60.0, "cat_hoa_tu": tu,
                               "bien_cap": bien},
                              "Ghep lenh moi nhat voi cu nhat roi dong ca cap "
                              "hien thuc hoa phan hoi ve ma khong phai cho ca "
                              "ro ve hoa von - tien ve som hon nhieu."))
    return ra


def _qt_tia(_):
    """+ TIA MOT PHAN. Luan diem: cat bot khi lai da co thi phan con lai chay
    bang von da thu hoi, tuc rui ro con lai la rui ro cua tien lai.

    CAT HOA PHAI TAT. Do 19/09: voi `cat_hoa_tu=2` (mac dinh) thi `tia` kich
    hoat 0 lan tren 60.000 bar - cat hoa dong cac cap truoc khi lai ca ro kip
    cham nguong. De ra mot cau hinh "co tia" ma de cat hoa bat la de ra mot
    cau hinh KHONG tia, va bang so se bao "tia vo dung".
    """
    ra = []
    for b in (30.0, 60.0):
        for tu in (2.0, 5.0):
            for ty in (0.3, 0.5):
                ra.append(_cf("tia_b%g_t%g_ty%g" % (b, tu, ty), "luoi_tia",
                              {"buoc": b, "tp": 60.0, "cat_hoa_tu": 999,
                               "tia_tu": tu, "tia_ty": ty},
                              "Cat bot khi lai da co thi phan con lai chay bang "
                              "von da thu hoi - rui ro con lai la rui ro cua "
                              "tien lai, khong phai cua von goc."))
    return ra


def _qt_chot_lui(_):
    """+ NHA LAI MOT PHAN DINH LAI. Luan diem: mot ro dang lai la mot ro da
    dung; giu no mo them chi de an not phan duoi cua bien dong la doi mot rui
    ro lon lay mot phan thuong nho."""
    ra = []
    for b in (30.0, 60.0):
        for tu in (2.0, 5.0, 10.0):
            for ty in (0.7, 0.85):
                ra.append(_cf("chotlui_b%g_t%g_ty%g" % (b, tu, ty),
                              "luoi_chot_lui",
                              {"buoc": b, "tp": 120.0, "chot_lui_tu": tu,
                               "chot_lui_ty": ty},
                              "Mot ro dang lai la mot ro da dung; giu no mo "
                              "them de an not phan duoi cua bien dong la doi "
                              "rui ro lon lay phan thuong nho."))
    return ra


def _qt_hedge(_):
    """+ KHOA LO. Luan diem: khi ro da ket, cai giet tai khoan khong phai huong
    gia ma la TOC DO no di tiep. Mot vi the nguoc dong bang lo do lai, doi lay
    thoi gian de ro chinh cho gia hoi."""
    ra = []
    for b in (30.0, 60.0):
        for tu in (4, 6, 8):
            for ty in (0.5, 1.0):
                ra.append(_cf("hedge_b%g_n%d_ty%g" % (b, tu, ty), "luoi_hedge",
                              {"buoc": b, "tp": 60.0, "hedge_tu": tu,
                               "hedge_ty": ty, "hedge_go": 10.0},
                              "Khi ro da ket, cai giet tai khoan khong phai "
                              "huong gia ma la toc do no di tiep; mot vi the "
                              "nguoc mua lai thoi gian cho ro chinh."))
    return ra


def _qt_thoat_gio(_):
    """+ DONG RO THEO THOI GIAN. Luan diem: mot ro ket ba ngay tren cap neo ve
    trung binh khong phai tin hieu can them tang - la tin hieu CHE DO da doi,
    va gia dinh neo ve trung binh khong con hieu luc."""
    ra = []
    for b in (30.0, 60.0):
        for bar in (48, 120, 240):
            ra.append(_cf("thoatgio_b%g_%dbar" % (b, bar), "luoi_thoat_gio",
                          {"buoc": b, "tp": 60.0, "thoat_sau_bar": bar},
                          "Mot ro ket nhieu ngay tren cap neo ve trung binh la "
                          "tin hieu che do da doi, khong phai tin hieu can nap "
                          "them tang - gia dinh ban dau het hieu luc."))
    return ra


def _qt_chan_von(_):
    """+ TRAN TANG va DUNG LO. Luan diem: luoi khong chet vi sai huong, no
    chet vi HET VON truoc khi gia hoi. Tran tang la thu duy nhat chan duoi."""
    ra = []
    for b in (30.0, 60.0):
        for tran in (5, 8, 12):
            ra.append(_cf("chanvon_b%g_tran%d" % (b, tran), "luoi_chan_von",
                          {"buoc": b, "tp": 60.0, "tang_toi_da": tran},
                          "Luoi khong chet vi sai huong, no chet vi het von "
                          "truoc khi gia hoi; tran tang la thu duy nhat chan "
                          "duoi mot cach chac chan."))
    return ra


def _qt_trailing(_):
    """+ TRAILING tren gia trung binh cua ro."""
    ra = []
    for b in (30.0, 60.0):
        for tu in (20.0, 40.0):
            for buoc_t in (10.0, 20.0):
                ra.append(_cf("trail_b%g_t%g_s%g" % (b, tu, buoc_t),
                              "luoi_trailing",
                              {"buoc": b, "tp": 200.0, "trailing_tu": tu,
                               "trailing_buoc": buoc_t},
                              "Keo moc dong theo gia tot nhat ro da cham: doi "
                              "mot phan lai da co lay kha nang an het mot cu "
                              "dich dai, thay vi chot cung o mot muc."))
    return ra


def _qt_bat_doi_xung(_):
    """+ LUOI BAT DOI XUNG theo EMA. Luan diem: phi qua dem khong doi xung -
    tren AUDCAD giu MUA duoc tra -0,263%/nam con giu BAN mat +3,853%/nam. Mot
    cai luoi doi xung hoan hao dang tra tien cho mot ben ma khong biet."""
    ra = []
    for b in (30.0, 60.0):
        for n in (50, 200):
            for nguoc in (False, True):
                ra.append(_cf("lech_b%g_ema%d%s" % (b, n, "_nguoc" if nguoc else ""),
                              "luoi_bat_doi_xung",
                              {"buoc": b, "tp": 60.0, "lech_ema": n,
                               "entry_nguoc": nguoc},
                              "Phi qua dem khong doi xung giua hai chieu, nen "
                              "mot cai luoi doi xung hoan hao dang tra tien cho "
                              "mot ben ma khong biet minh dang tra."))
    return ra


#: THU TU LA THU TU UU TIEN - xem `duc`. Ho `tia` va `chot_lui` xep ngay sau
#: luoi tran vi chung la hai ho DA CHUNG MINH GIA TRI BANG SO tren AUDCAD.
KHUON_QT = (
    ("luoi_tran", _qt_tran),
    ("luoi_tia", _qt_tia),
    ("luoi_chot_lui", _qt_chot_lui),
    ("luoi_cat_hoa", _qt_cat_hoa),
    ("luoi_chan_von", _qt_chan_von),
    ("luoi_hedge", _qt_hedge),
    ("luoi_thoat_gio", _qt_thoat_gio),
    ("luoi_trailing", _qt_trailing),
    ("luoi_bat_doi_xung", _qt_bat_doi_xung),
)


def duc_quan_tri(han_ngach: int = 200, khuon: str | None = None) -> list[dict]:
    """DE CAU HINH QUAN TRI LENH. Xac dinh, khong trung, khong RNG."""
    ra, thay = [], set()
    for ten_khuon, ham in KHUON_QT:
        if khuon and ten_khuon != khuon:
            continue
        for cf in ham(None):
            if len(ra) >= han_ngach:
                return ra
            vt = van_tay_quan_tri(cf)
            if vt in thay:
                continue
            thay.add(vt)
            ra.append(cf)
    return ra


def kiem_phan_giai(cf: dict, df) -> dict:
    """Chuoi bar co DU MIN de mo phong cau hinh nay khong? BA trang thai.

    Day la luat `pmg_engine.NGUONG_PHAN_GIAI`, ap cho luoi tinh bang PIP thay
    vi bang ATR. Buoc luoi phai rong >= 2 lan BIEN DO MOT NEN, khong thi ca cai
    luoi nam gon trong mot nen va ket qua la tao tac cua gia dinh duong di
    trong bar chu khong phai cua thi truong. Do 14/09 tren random walk khong
    chi phi: buoc/bien_do = 0,54 cho ra **+720%** trong khi dap an la ~0.

    Tra `CHUA_DO_DUOC`, **khong bao gio** tra `AM`: ham nay noi ve DO MIN cua
    du lieu, khong noi ve co che.
    """
    import numpy as _np
    hi = _np.asarray(df["high"], float)
    lo = _np.asarray(df["low"], float)
    bien_do = float(_np.median(hi - lo)) / PIP_QT
    nut = cf.get("nut") or {}
    buoc = float(nut.get("buoc", 0.0) or 0.0)
    tp = float(nut.get("tp", 0.0) or 0.0)
    if not _np.isfinite(bien_do) or bien_do <= 0:
        return {"trang_thai": "CHUA_DO_DUOC",
                "ly_do": "bien do bar khong hop le", "buoc_tren_bien_do": 0.0}
    ty_buoc, ty_tp = buoc / bien_do, tp / bien_do
    thieu = []
    # MOI NUT LA MOT KHOANG CACH GIA deu phai qua nguong, khong chi `buoc` va
    # `tp`. Do 19/09/2026: ban dau ham nay chi kiem hai nut do, va cac cau hinh
    # `trailing` di lot het - `trailing_buoc = 10 pip` tren chuoi co bien do nen
    # 14,4 pip cho ra **12.805%/nam tren random walk** voi sut giam 4,67. Do la
    # dung chu ky cua loi "AUDCAD 6.557%/nam voi von 41 USD".
    #
    # Va lai chay theo dung mot duong don dieu voi do min: trailing_buoc
    # 5 -> +1.267/nam · 10 -> +1.197 · 20 -> +820 · 30 -> +519 · 60 -> +34 ·
    # 120 (8,3x nen) -> **-12**, tuc dap an dung (= -chi phi) chi hien ra khi
    # buoc trailing rong hon nen may lan. Khong phai mot cau hinh tot o do phan
    # giai cao; la mot phep do khong hop le.
    for k, nhan in (("trailing_buoc", "buoc trailing"),
                    ("trailing_tu", "nguong bat trailing"),
                    ("breakeven_tu", "nguong hoa von"),
                    ("kc_bs", "khoang cach buy-sell"),
                    ("cho_lui", "do lui lenh cho"),
                    ("hedge_go", "nguong go khoa"),
                    ("tp_nhanh", "tp nhanh"),
                    ("bien_cap", "bien cap cat hoa")):
        v = nut.get(k)
        if v is None or float(v) <= 0.0:
            continue                    # khong dat = khong dung, khong phai loi
        ty = float(v) / bien_do
        if ty < NGUONG_PHAN_GIAI_QT:
            thieu.append("%s %.2fx bien do nen (can >= %g)"
                         % (nhan, ty, NGUONG_PHAN_GIAI_QT))
    if ty_buoc < NGUONG_PHAN_GIAI_QT:
        thieu.append("buoc luoi %.2fx bien do nen (can >= %g)"
                     % (ty_buoc, NGUONG_PHAN_GIAI_QT))
    if ty_tp < NGUONG_PHAN_GIAI_QT:
        thieu.append("tp %.2fx bien do nen (can >= %g)"
                     % (ty_tp, NGUONG_PHAN_GIAI_QT))
    return {"trang_thai": "DU" if not thieu else "CHUA_DO_DUOC",
            "ly_do": "; ".join(thieu), "bien_do_nen_pip": bien_do,
            "buoc_tren_bien_do": ty_buoc, "tp_tren_bien_do": ty_tp}


#: Nut do bang TIEN, khong bang pip: `chot_lui_tu`, `tia_tu`, `dung_lo`,
#: `chot_tien`. Quy chung ve khoang cach gia can biet LOT cua ro tai thoi diem
#: do, ma lot thi doi theo so tang - nen khong co mot con so kiem duoc truoc
#: khi chay. Chung KHONG duoc kiem o day, va do la mot lo hong da biet:
#: `chot_lui_ty = 0,9` tren mot ro lai mong van la mot khoang cach duoi nen.
#: Cach chan that la do LAI DINH quy ra pip trong chinh vong mo phong.
NUT_THEO_TIEN = ("chot_lui_tu", "tia_tu", "dung_lo", "chot_tien")


#: Cung nguong voi `pmg_engine.NGUONG_PHAN_GIAI` - mot con so, mot cho.
NGUONG_PHAN_GIAI_QT = 2.0
PIP_QT = 1e-4


def chay_lo(cfs: list[dict], df, so_nam: float | None = None) -> dict:
    """Chay ca lo qua `mo_phong_v2` roi cham diem bang `cham_diem`.

    Cau hinh khong du PHAN GIAI bi cham `CHUA_DO_DUOC` va **khong duoc chay**:
    chay roi bao AM mot cau hinh ma bar khong do noi la bia ra mot ket luan.
    """
    import numpy as _np

    import mo_phong_v2 as MP
    from nhan import cham_diem as CD

    n = len(df)
    nam = float(so_nam if so_nam is not None else n / (24.0 * 252.0))
    hi = _np.asarray(df["high"], float)
    lo_ = _np.asarray(df["low"], float)
    d = {"hi": hi, "lo": lo_, "c": _np.asarray(df["close"], float),
         "sp": _np.full(n, 1.0), "thu": _np.ones(n, dtype=int),
         "n": n, "pv": 0.0714, "nam": nam}

    dong = []
    for cf in cfs:
        pg = kiem_phan_giai(cf, df)
        if pg["trang_thai"] != "DU":
            dong.append({"ten": cf["ten"], "khuon": cf.get("khuon", ""),
                         "phan_giai": pg,
                         "diem": {"muc": "CHUA_DO_DUOC", "ly_do": [pg["ly_do"]],
                                  "lai_pct_nam": None}})
            continue
        try:
            r = MP.mo_phong(d, **cf["nut"])
        except Exception as e:
            dong.append({"ten": cf["ten"], "khuon": cf.get("khuon", ""),
                         "phan_giai": pg,
                         "diem": {"muc": "CHUA_DO_DUOC",
                                  "ly_do": ["chay loi: %s" % type(e).__name__],
                                  "lai_pct_nam": None}})
            continue
        von = max(float(r.get("von") or 0.0) * CD.BO_DEM_SUT_GIAM, 1e-9)
        dong.append({"ten": cf["ten"], "khuon": cf.get("khuon", ""),
                     "phan_giai": pg, "ket_qua": r,
                     "diem": CD.tu_ket_qua_luoi(r, von_can=von, so_nam=nam,
                                                ten=cf["ten"])})
    vt = sorted(van_tay_quan_tri(c) for c in cfs)
    h = hashlib.sha256("\n".join(vt).encode("utf-8")).hexdigest()[:32]
    return {"dong": dong, "plan_hash": h, "so_phep_thu": len(vt),
            "so_nam": nam}


def chuoi_null(df, hat: int = 0):
    """Mot ban KHONG CON EDGE cua chuoi gia, GIU NGUYEN ket cau bar.

    Hoan vi loi suat bar-sang-bar cua `close`, roi dung lai high/low bang dung
    cac do lech (high - close) va (close - low) cua chinh bar do, mang theo
    trong cung mot hoan vi. Nho vay:

      * BIEN DO NEN giu nguyen phan phoi - dieu kien song con, vi phep kiem
        phan giai va moi tao tac trong-bar deu phu thuoc vao no;
      * TU TUONG QUAN bi pha - va do la thu ma mot cai luoi song bang.

    Vi sao khong dung random walk chuan: bien do nen cua no khong giong bien do
    that, nen ty le lot do duoc tren no khong noi gi ve cong dang chay tren du
    lieu that.

    Day KHONG phai placebo cua mot co che (cai do la ngau nhien hoa BUOC va
    HUONG). Day la hieu chuan CONG: mot cong tu choi tat ca cho so lieu y het
    mot cong tot, nen phai do ca hai chieu.
    """
    import numpy as _np
    import pandas as _pd
    c = _np.asarray(df["close"], float)
    hi = _np.asarray(df["high"], float)
    lo = _np.asarray(df["low"], float)
    r = _np.diff(_np.log(c))
    tren, duoi = hi - c, c - lo
    rng = _np.random.default_rng(hat)
    thu_tu = rng.permutation(len(r))
    c2 = _np.empty(len(c))
    c2[0] = c[0]
    c2[1:] = c[0] * _np.exp(_np.cumsum(r[thu_tu]))
    t2 = _np.r_[tren[0], tren[1:][thu_tu]]
    d2 = _np.r_[duoi[0], duoi[1:][thu_tu]]
    op2 = _np.r_[c2[0], c2[:-1]]
    return _pd.DataFrame(
        {"open": op2, "high": c2 + _np.abs(t2), "low": c2 - _np.abs(d2),
         "close": c2,
         "tick_volume": _np.asarray(df.get("tick_volume", 1.0), float)},
        index=df.index)


def hieu_chuan(cfs: list[dict], df, so_lan: int = 5) -> dict:
    """Lo nay lot qua cong bao nhieu lan tren chuoi DA BI PHA EDGE.

    Luat cua du an: *"Hieu chuan cong phai HAI CHIEU"* - mot cong tu choi TAT
    CA cho so lieu y het mot cong tot. Ham nay do chieu con lai: cai gi lot qua
    khi dang le khong duoc phep lot.

    `ty_le_lot` cao nghia la moi ket qua cua lo nay dang bi nghi ngo, KHONG
    phai la lo nay tot. Do 19/09 dung cach nay ma tim ra `cat_hoa` gat bien do
    trong nen: ty le lot 42% tren nhieu, va sau khi sua con 2,9%.
    """
    from collections import Counter
    dem: Counter = Counter()
    lot: Counter = Counter()
    for k in range(so_lan):
        r = chay_lo(cfs, chuoi_null(df, hat=k))
        for d in r["dong"]:
            dem[d["diem"]["muc"]] += 1
            if d["diem"]["muc"] == "CHAY_DUOC":
                lot[d["ten"]] += 1
    tong = max(sum(dem.values()), 1)
    return {"muc": dict(dem), "so_lan": so_lan,
            "ty_le_lot": dem["CHAY_DUOC"] / tong,
            "lot_nhieu_lan": lot.most_common(10)}


def danh_gia_vs_null(cfs: list[dict], df, so_null: int = 20) -> dict:
    """Ket qua THAT so voi PHAN BO NULL cua chinh cau hinh do.

    ## VI SAO KHONG DUOC PHAN QUYET TREN MOT DUONG

    Do 19/09/2026: chay `hieu_chuan` tren chuoi DA BI PHA EDGE, ty le cau hinh
    duoc cham `CHAY_DUOC` van la **50%**. Khong phai vi cong hong, ma vi mot
    cai luoi co hinh dang tra thuong **trung vi DUONG, ky vong AM**: phan lon
    duong mau cho lai nho deu, mot thieu so cho lo rat sau. Nen tren MOT duong,
    xac suat no "trong nhu co lai" von da gan mot nua - ke ca khi khong co edge
    nao.

    Tuc `cham_diem` cham mot luot chay don le thi **ve mat cau truc** khong
    phan biet duoc luoi co edge voi luoi khong co. No do "duong nay co lai
    khong", trong khi cau hoi that la "co lai hon MUC NGAU NHIEN khong".

    ## CACH DO

    Chay cau hinh tren `so_null` ban hoan vi (xem `chuoi_null`) roi hoi: ket
    qua THAT nam o phan vi nao cua phan bo do. `vuot_null = 0,95` nghia la no
    hon 95% cac lan chay tren chuoi khong con edge.

    Day van CHUA phai mot p-value dung nghia (cac ban null khong doc lap hoan
    toan voi nhau), nen doc no nhu mot THU HANG, va van phai qua `cong.lord_v2`
    voi `plan_hash` truoc khi goi la phat hien.
    """
    import numpy as _np
    that = {d["ten"]: d for d in chay_lo(cfs, df)["dong"]}
    gom: dict = {t: [] for t in that}
    for k in range(so_null):
        for d in chay_lo(cfs, chuoi_null(df, hat=k))["dong"]:
            r = d.get("ket_qua")
            gom[d["ten"]].append(None if r is None else float(r.get("lai_nam", 0.0)))

    dong = []
    for ten, d in that.items():
        r = d.get("ket_qua")
        ds = [x for x in gom.get(ten, []) if x is not None]
        if r is None or len(ds) < max(5, so_null // 2):
            # Khong du ban null de xep hang -> KHONG ket luan. Bia mot thu hang
            # o day la bia ca phan quyet.
            dong.append({**d, "vuot_null": None,
                         "ghi_chu": "CHUA_DO_DUOC: khong du ban null"})
            continue
        lai = float(r.get("lai_nam", 0.0))
        dong.append({**d, "vuot_null": float(_np.mean([lai > x for x in ds])),
                     "null_trung_vi": float(_np.median(ds))})
    dong.sort(key=lambda x: (x.get("vuot_null") is None, -(x.get("vuot_null") or 0)))
    return {"dong": dong, "so_null": so_null,
            "plan_hash": chay_lo(cfs, df)["plan_hash"], "so_phep_thu": len(cfs)}
