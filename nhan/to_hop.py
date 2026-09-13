# -*- coding: utf-8 -*-
"""to_hop.py - TO HOP DA CAP x DA KHUNG x DA QUAN LI x DA THONG SO.

Muc Q6. Chu du an viet trong `SO_DO_HE_THONG.txt`:

    "tat ca moi chien luoc can test da cap/ da khung ... /da phuong phap quan li
     lenh/ da thong so input/ neu co the hay thu ket hop da chi bao da he thong
     ma chung ta tim duoc. Phan nay cang ket thua duoc nhieu tu cac module ben
     tren thi cang tiet kiem thoi gian va nang cao hieu qua"

    "Sau do can co bo tong ket de rut ra chien luoc, neu co co che nao tim ra
     huong di moi lap tuc ghi lai va phan tich ... tim ra huong di nen tranh
     huong khong nen tiep tuc"

Hai cau do la hai nua cua file nay: `chay()` va `tong_ket()`.

## VI SAO KHONG QUET THANG

Khong gian day du la 159 ma x 3 khung x 1.460 co che x 7 cau truc x 8 luat =
**39 trieu o**. O ~40ms moi o do la 18 nam CPU. Nen day la mot PHEU BA CHANG,
khong phai mot vong lap long nhau:

    chang 1  moi (ma, khung, co che) voi cau truc RE NHAT (thi truong, khong
             luat). Day la cau hoi "co gi o day khong" - va no la cau hoi re.
    chang 2  nhung o song sot x 7 cau truc x 8 luat.
    chang 3  dinh cua chang 2 x luoi thong so.

Ti le song sot moi chang do duoc va ghi lai, nen lan sau biet nen tha bao nhieu.

## TIA TRUOC KHI CHAY - DAY LA CHO "KE THUA" CO NGHIA

  - **Bo ma TRUNG CONG CU** bang `ho_so_tuong_quan`: kho co US500CASH va
    XM_US500CASH voi r = 1,000, va 307 cap co r >= 0,7. Chay ca hai la tra tien
    CPU hai lan cho mot cau tra loi.
  - **Bo khung khong du du lieu** cho tung ma. Memory `khung-nho-do-du-lieu`:
    H4 truoc 2016 that ra la bar NGAY duoc don vao, M5 chi co 1,4 nam. Quet mot
    khung khong co du lieu that khong bao loi - no tra ve so.
  - **Bo co che kich hoat qua thua hoac qua day.** Duoi 2% thi khong du lenh de
    ket luan gi; tren 60% thi no khong phai tin hieu ma la mot bo loc che do.

## CAI GI QUYET DINH - TIEN, KHONG PHAI p

Xep hang bang `cagr_dd20` = lai %/nam khi quy ve cung ngan sach sut giam 20%,
so voi moc `max(mua-giu, ban-giu, tien mat)`. Cac chi tieu thong ke di theo
duoi dang NHAN (xem `nhan/cong.py`, che do "nhan" tu 12/09/2026).

Chay:  python -m nhan.to_hop [KHUNG...] [--ma N] [--co-che N] [--tien-trinh N]
Ra:    reports/TO_HOP.json  +  reports/TO_HOP_TONG_KET.md
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

KHUNG_MAC_DINH = ("D1", "H4")
#: Duoi nguong nay thi khong khung nao dung duoc - bar qua it de noi gi.
BAR_TOI_THIEU = 800
#: Hai nua phai CUNG CO. Ngoai khoang nay thi mot nua dang ke chuyen khac han
#: nua kia - du no la "tot hon". `dd20_hold / dd20_train`.
TY_LE_HAI_NUA = (0.33, 3.0)
#: Nguong cho MOT NUA o chang holdout. Thap hon co y: nua ngan hon ca chuoi,
#: giu nguyen 800 thi chang holdout tu loai gan het roi bao "khong he nao song".
BAR_NUA_TOI_THIEU = 300
#: Ti le bar co tin hieu. Ngoai khoang nay thi khong phai "tin hieu".
KICH_HOAT = (0.02, 0.60)
#: Bao nhieu o song sot moi chang.
GIU_CHANG1 = 200
GIU_CHANG2 = 40
#: HAN NGACH: mot ma (chang 1) hay mot he (chang 2) duoc chiem toi da bao nhieu
#: PHAN cua suat giu. Xem `giu_co_han_ngach`.
HAN_NGACH = 0.04
#: Luoi thong so cho chang 3. Nho co y: muc dich la do DO NHAY, khong phai tim
#: so dep nhat - "cao nguyen hay cai gai" (memory `cao-nguyen-hay-cai-gai`).
LUOI_THAM = [
    {"sl_atr": 1.5, "tp_atr": 3.0},
    {"sl_atr": 2.0, "tp_atr": 4.0},
    {"sl_atr": 3.0, "tp_atr": 6.0},
    {"sl_atr": 2.0, "tp_atr": 4.0, "k_dat": 0.25},
    {"sl_atr": 2.0, "tp_atr": 4.0, "k_dat": 1.0},
]


# --------------------------------------------------------------- HAN NGACH GIU
def giu_co_han_ngach(ds: list[dict], n: int, khoa=lambda d: d["ma"],
                     ti_le: float = HAN_NGACH) -> list[dict]:
    """Giu `n` o tot nhat NHUNG khong de mot ma (hay mot he) chiem het.

    ## VI SAO CO HAM NAY

    Chang 1 truoc do la `r1.sort(-cagr_dd20)[:200]` - mot phep sort tren MOT so
    vo huong, khong rang buoc gi ve ma. Hau qua do duoc, hai lan, va ca hai lan
    deu ghi lai trong chinh file nay ma khong sua tan goc:

      * lan chay 12/09 (truoc khi sua bar hong): 200 o song sot -> **2 ma**
        (EURMXN 2.567 cap holdout / GBPTRY 42). 120/120 dong dau bang la EURMXN.
      * ghi chu o chang 4: *"200 o song sot gan nhu chi nam tren TRYJPY, GBPTRY,
        USDARS - ba dong tien sup do"*.

    Hai lan do duoc do hai nguyen nhan khac han nhau (bar hong x10; dong tien
    mat gia mot chieu). Cai CHUNG khong phai nguyen nhan - la phep chon. Bat ky
    ma nao cham diem cao mot cach CO HE THONG deu an tron 200 suat, va chang
    2/3/4 - tuc toan bo phan con lai cua pheu - khong con nhin thay thi truong
    nua. Quet 145 ma roi kiem dinh tren 2 ma la **tra tien cho 145 ma de biet
    ve 2 ma**.

    Sua bar hong chi go duoc mot nguyen nhan. Han ngach go CAI PHEP CHON, nen
    lan sau co nguyen nhan thu ba thi no khong an het bang nua.

    ## KHONG HA MOT NGUONG NAO

    Van giu dung `n` o. Han ngach chi doi o thu 9 cua ma dan dau lay o thu nhat
    cua ma xep sau. Neu it ma qua khong du `n` thi tran tu noi len cho toi khi
    du - nen ham khong bao gio tra ve it hon `min(n, len(ds))`.
    """
    if n <= 0 or not ds:
        return []
    tran = max(1, int(round(n * ti_le)))
    con = list(ds)
    ra: list[dict] = []
    # `dem` song NGOAI vong lap: tran la tran cua CA lan chon, khong phai cua
    # moi luot. De no ben trong thi moi luot lai cho them `tran` o nua cho ma
    # dan dau - han ngach khong con la han ngach.
    dem: dict = {}
    while con and len(ra) < n:
        thua = []
        for d in con:
            k = khoa(d)
            if dem.get(k, 0) < tran and len(ra) < n:
                dem[k] = dem.get(k, 0) + 1
                ra.append(d)
            else:
                thua.append(d)
        if len(thua) == len(con):       # khong nhan them duoc gi -> noi tran
            tran *= 2
        con = thua
    return ra


# ------------------------------------------------------------------ TIA KHONG GIAN
def ma_khong_trung(cac_ma: list[str], khung: str = "D1",
                   nguong: float = 0.97) -> tuple[list[str], dict]:
    """Bo ma la ban sao cua ma khac. -> (danh sach giu, {bi bo: giu thay})

    Dung ket qua da co cua `ho_so_tuong_quan` neu co; khong co thi giu nguyen
    (KHONG tu chay lai - mot module tia khong duoc am tham tieu 40 giay CPU).
    """
    from nhan import ho_so_tuong_quan as TQ
    d = TQ.doc(khung)
    if not d or "cap" not in d:
        return list(cac_ma), {}
    bo: dict[str, str] = {}
    co = set(cac_ma)
    for k, v in d["cap"].items():
        if "|" not in k:
            continue
        a, b = k.split("|", 1)
        if a not in co or b not in co:
            continue
        if v.get("trung") or float(v.get("r", 0)) >= nguong:
            # Giu cai co NHIEU BAR CHUNG hon lam dai dien; hoa thi giu ten ngan
            giu, bot = (a, b) if len(a) <= len(b) else (b, a)
            if giu in bo:          # dai dien cua no cung da bi bo -> lan theo
                giu = bo[giu]
            if bot != giu:
                bo[bot] = giu
    return [m for m in cac_ma if m not in bo], bo


def khung_dung_duoc(ma: str, cac_khung) -> list[str]:
    """Khung nao co du du lieu THAT cho ma nay."""
    from nhan import du_lieu as DL
    ra = []
    for k in cac_khung:
        try:
            df = DL.nap(ma, k)
        except Exception:
            continue
        if len(df) >= BAR_TOI_THIEU:
            ra.append(k)
    return ra


#: VUNG SINH LOI, do tren 1.276 ket qua da cham (13/09/2026):
#:
#:     phoi nhiem     n     CAGR tv   Sharpe tv   ty le PASS
#:     0-10%        127      -0,19      -0,23        3,1%
#:     10-25%       494      -0,42      -0,15        1,2%
#:     25-40%       104      +0,86      +0,20        4,8%   <- tot nhat
#:     40-60%       195      +0,82      +0,15        0,0%
#:     >=60%        356      -1,89      -0,30        0,0%   <- te nhat
#:
#: Hai dieu rut ra, va ca hai deu nguoc voi truc giac dau tien cua toi:
#:
#: 1. **Tran 0,60 CO CO SO** du ghi chu cua no khong neu phep do nao. Nhom
#:    >=60% te nhat tren 356 mau. Noi van la lam hong them.
#: 2. **Pheu dang tieu 39% cong suc vao vung ngheo nhat** (10-25%, ty le
#:    trung 1,2%) va chi 8% vao vung tot nhat (25-40%, ty le trung 4,8%).
#:
#: Nen thu tu duyet KHONG duoc la bang chu cai. `_ty_le_kich_hoat` trong kho
#: du bao phoi nhiem that voi **r = 0,964** (97 cap doi chieu duoc), nen no
#: xep hang truoc duoc.
VUNG_SINH_LOI = (0.25, 0.40)


def co_che_dung_duoc(gioi_han: int = 0) -> list[dict]:
    """Co che co ti le kich hoat nam trong khoang dung duoc.

    Xep theo KHOANG CACH toi vung sinh loi, khong theo ten. Khong loai them
    gi - chi doi thu tu, de khi `gioi_han` cat bot thi cai bi cat la cai it
    hua hen nhat chu khong phai cai co ten van bang Z.
    """
    from nhan import ngu_phap as NP
    giua = sum(VUNG_SINH_LOI) / 2.0
    ds = []
    for s in NP.doc_kho():
        t = s.get("_ty_le_kich_hoat")
        if t is None or not (KICH_HOAT[0] <= float(t) <= KICH_HOAT[1]):
            continue
        ds.append(s)
    ds.sort(key=lambda s: (abs(float(s.get("_ty_le_kich_hoat")) - giua),
                           str(s.get("ten", ""))))
    return ds[:gioi_han] if gioi_han else ds


# ------------------------------------------------------------------- MOT O
def _mot_o(viec):
    """Mot (ma, khung, co che) o chang 1, hoac day du o chang 2/3/4.

    `phan` = "het" | "train" | "hold": chay tren ca chuoi, hay chi mot nua.
    """
    ma, khung, spec, cau_truc, luat, tham = viec[:6]
    phan = viec[6] if len(viec) > 6 else "het"
    try:
        from nhan import dap_quan_tri as DQ
        from nhan import du_lieu as DL
        from nhan import ngu_phap as NP
        from nhan import vao_lenh as VL
        df = DL.nap(ma, khung)
        # CONG CHAT LUONG - doc `dung_duoc` cua `du_lieu.kiem`.
        #
        # Bo do da co tu lau va bao dung, nhung khong noi nao doc no. Hau qua do
        # duoc 12/09/2026: EURMXN co 68 o lech thang x10 ma bo sua cu mu (no neo
        # vao ba cot cung bar, con o day BA cot cung lech) -> loi suat open-to-
        # open co do lech chuan 0,2382 thay vi 0,0072 -> **120/120 dong dau bang
        # pheu deu la EURMXN** voi "CAGR 942%/nam" tren mot ma di ngang 9 nam.
        #
        # Nay `sua_bar_hong` vot duoc ca ba ma hong (EURMXN/GBPZAR/EURNOK), nhung
        # cong nay phai o day de lan sau co ma hong kieu KHAC thi no bi chan chu
        # khong leo len dau bang xep hang.
        try:
            if DL.kiem(df, ma).get("dung_duoc") is False:
                return None
        except Exception:
            pass
        # Nguong bar cua NUA phai thap hon nguong ca chuoi - khong thi chang
        # holdout tu loai gan het va bao "0 he song sot" tu chinh phep loc cua
        # no, chu khong phai tu thi truong. (Do that: 40 he -> 28 o co ket qua
        # -> 0 cap du ca hai dau, chi vi 800 bar ap cho tung nua.)
        toi_thieu = BAR_TOI_THIEU
        if phan in ("train", "hold"):
            df = DL.hai_nua(df, 0.6)[0 if phan == "train" else 1]
            toi_thieu = BAR_NUA_TOI_THIEU
        if len(df) < toi_thieu:
            return None
        th = NP.sinh_tu_spec(spec, df)
        th = np.nan_to_num(np.asarray(th, float).reshape(-1), nan=0.0)
        if int(np.sum(np.abs(th) > 0)) < (30 if phan == "het" else 12):
            return None
        # CHAN TROI GIU LENH PHAI THEO CHINH CO CHE, KHONG PHAI MOT SO CUNG.
        #
        # Do 12/09/2026: 978/1460 co che (67%) khai `giu <= 5 bar`, nhung o day
        # truoc gio chay TAT CA voi `giu_toi_da = 60` - lech 12 lan. Phep hieu
        # chuan hai chieu (`test_hieu_chuan_to_hop`) chung minh hau qua: mot edge
        # CAY SAN manh 0,6 sigma song dung 1 bar, giu 20 bar thi he LO (dd20
        # -2,53) du edge co dieu kien van nguyen ven (+0,00485 vs -0,00227).
        #
        # Nghia la ket qua "0/2.841 he qua holdout" cua lan chay truoc KHONG noi
        # gi ve thi truong - no do sai chan troi cho hai phan ba kho.
        giu = max(int(spec.get("giu") or 1), 1)
        if luat is None:
            bang = VL.so_cau_truc(df, th, ma, khung, cac=[cau_truc],
                                  giu_toi_da=giu, tham=tham)
            if not bang:
                return None
            d = bang[0]
            d["luat"] = "-"
        else:
            bang = DQ.so_luat(df, th, ma, khung,
                              bo_luat={luat: DQ.BO_LUAT[luat]}, giu_toi_da=giu)
            if not bang:
                return None
            d = bang[0]
            d["cau_truc"] = cau_truc
        d["co_che"] = spec.get("ten", "?")
        d["ho"] = spec.get("ho", "?")
        d["tham"] = tham or {}
        d["giu"] = giu
        d["phan"] = phan
        # `so_nam` gan O DAY chu khong o tung engine: co HAI duong ra
        # (`vao_lenh.so_cau_truc` va `dap_quan_tri.so_luat`) va sua mot duong
        # thi duong kia van thieu - dung cai da xay ra 12/09, bang `top` co
        # `luat` nen di duong thu hai va `cham_diem` bo qua ca 120 dong.
        # Thieu no thi `so_lenh_nam` = TONG so lenh, va moi dong vuot nguong
        # 20 lenh/nam mot cach gia.
        d["so_nam"] = round(VL.so_nam_cua(df), 2)
        return d
    except Exception as e:
        return {"ma": ma, "khung": khung, "co_che": spec.get("ten", "?"),
                "loi": "%s: %s" % (type(e).__name__, e)}


def _chay_lo(viecs, sp, in_ra=print, nhan=""):
    t0 = time.time()
    with Pool(sp) as pool:
        kq = pool.map(_mot_o, viecs, chunksize=4)
    tot = [k for k in kq if k and "loi" not in k]
    loi = [k for k in kq if k and "loi" in k]
    in_ra("  %s: %d o -> %d ket qua, %d loi, %.0fs"
          % (nhan, len(viecs), len(tot), len(loi), time.time() - t0))
    if loi:
        in_ra("    loi dau: %s" % loi[0]["loi"][:120])
    return tot


def _in_tap_trung(in_ra, nhan, tat_ca, giu, khoa, ten_khoa):
    """In DO TAP TRUNG cua suat giu. Mot con so, nhung no la con so tra loi
    "pheu dang hoc ve thi truong hay ve mot ma"."""
    if not giu:
        return
    cu = {}
    for d in tat_ca[:len(giu)]:
        cu[khoa(d)] = cu.get(khoa(d), 0) + 1
    dan = max(cu.values()) if cu else 0
    in_ra("  %s giu %d o: %d %s khac nhau (khong han ngach: %d %s, "
          "cai dan dau chiem %d)"
          % (nhan, len(giu), len({khoa(d) for d in giu}), ten_khoa,
             len(cu), ten_khoa, dan))


def chay(cac_khung=KHUNG_MAC_DINH, gh_ma: int = 0, gh_co_che: int = 0,
         sp: int = 10, in_ra=print) -> dict:
    from nhan import ho_so_symbol as HSS
    t0 = time.time()
    hs = HSS.doc()
    if isinstance(hs, dict):
        hs = list(hs.values())
    ma0 = sorted({str(x.get("ma")) for x in hs
                  if isinstance(x, dict) and x.get("ma")})
    ma, bo_trung = ma_khong_trung(ma0, "D1")
    if gh_ma:
        ma = ma[:gh_ma]
    in_ra("ma: %d -> %d (bo %d ban sao)" % (len(ma0), len(ma), len(bo_trung)))

    cap_khung = {m: khung_dung_duoc(m, cac_khung) for m in ma}
    o_mk = [(m, k) for m in ma for k in cap_khung[m]]
    in_ra("cap (ma, khung) co du du lieu: %d" % len(o_mk))

    cc = co_che_dung_duoc(gh_co_che)
    in_ra("co che kich hoat trong [%.0f%%, %.0f%%]: %d"
          % (KICH_HOAT[0] * 100, KICH_HOAT[1] * 100, len(cc)))

    # --- CHANG 1
    v1 = [(m, k, s, "thi_truong", None, None) for m, k in o_mk for s in cc]
    in_ra("\nCHANG 1 - %d o" % len(v1))
    r1 = _chay_lo(v1, sp, in_ra, "chang 1")
    r1.sort(key=lambda d: -d["cagr_dd20"])
    # HAN NGACH THEO MA - xem `giu_co_han_ngach`. Khong ha nguong nao, chi
    # khong cho mot ma an tron suat giu roi bit mat ca chang 2/3/4.
    song1 = giu_co_han_ngach(r1, GIU_CHANG1, lambda d: d["ma"])
    _in_tap_trung(in_ra, "chang 1", r1, song1, lambda d: d["ma"], "ma")

    # --- CHANG 2: cau truc x luat
    from nhan import dap_quan_tri as DQ
    from nhan import vao_lenh as VL
    v2 = []
    for d in song1:
        s = next((x for x in cc if x.get("ten") == d["co_che"]), None)
        if s is None:
            continue
        for ct in VL.CAU_TRUC:
            v2.append((d["ma"], d["khung"], s, ct, None, None))
        for lt in DQ.BO_LUAT:
            v2.append((d["ma"], d["khung"], s, "thi_truong", lt, None))
    in_ra("\nCHANG 2 - %d o (%d song sot x %d cau truc + %d luat)"
          % (len(v2), len(song1), len(VL.CAU_TRUC), len(DQ.BO_LUAT)))
    r2 = _chay_lo(v2, sp, in_ra, "chang 2")
    r2.sort(key=lambda d: -d["cagr_dd20"])
    # O chang 2 moi HE xuat hien 15 lan (7 cau truc + 8 luat), nen khoa la
    # (ma, co che) - neu khoa theo ma khong thi mot he van chiem duoc 15 suat
    # trong 40 mot cach hop le.
    _k2 = (lambda d: (d["ma"], d["co_che"]))
    song2 = giu_co_han_ngach(r2, GIU_CHANG2, _k2)
    _in_tap_trung(in_ra, "chang 2", r2, song2, _k2, "he")

    # --- CHANG 3: luoi thong so tren dinh
    v3 = []
    for d in song2:
        s = next((x for x in cc if x.get("ten") == d["co_che"]), None)
        if s is None or d.get("luat") not in (None, "-"):
            continue
        for tm in LUOI_THAM:
            v3.append((d["ma"], d["khung"], s, d["cau_truc"], None, tm))
    in_ra("\nCHANG 3 - %d o (do do nhay thong so)" % len(v3))
    r3 = _chay_lo(v3, sp, in_ra, "chang 3") if v3 else []

    # --- CHANG 4: HOLDOUT. Chang quyet dinh.
    #
    # Ba chang tren deu CHON tren chinh so ma chung do. Chay Q6 lan dau
    # (12/09/2026) cho thay ket qua: 200 o song sot gan nhu chi nam tren
    # **TRYJPY, GBPTRY, USDARS** - ba dong tien sup do. Do khong phai co che
    # tim ra edge, do la co che bat duoc mot xu huong mot chieu da xay ra.
    # Memory `ibs-la-hien-tuong-cua-mot-thoi-ky` va `phase2-multiasset-result`
    # ("usdars Sharpe 1,75 / placebo 0%") deu la dung hinh dang nay.
    #
    # Nen: CHON tren 60% dau, DO tren 40% sau. O nao doi dau la o do khong co gi.
    # CHANG QUYET DINH PHAI LA CHANG RONG NHAT, KHONG PHAI HEP NHAT.
    #
    # Ban dau toi cho chang 4 an top 40 cua chang 2 - tuc chi 40/2.988 o duoc
    # dua qua phep thu duy nhat co nghia. Do la nguoc: ba chang tren deu la
    # chon loc (re), chang 4 moi la KIEM DINH (cung re: 80 o het 3 giay, nen
    # 5.976 o chi het ~4 phut). Thu tu dung la sang rong roi kiem dinh rong.
    v4 = []
    for d in r2:
        s4 = next((x for x in cc if x.get("ten") == d["co_che"]), None)
        if s4 is None:
            continue
        lt = d.get("luat") if d.get("luat") not in (None, "-") else None
        for ph in ("train", "hold"):
            v4.append((d["ma"], d["khung"], s4, d.get("cau_truc", "thi_truong"),
                       lt, d.get("tham") or None, ph))
    in_ra("")
    in_ra("CHANG 4 - HOLDOUT - %d o (%d he x train/hold)" % (len(v4), len(r2)))
    r4 = _chay_lo(v4, sp, in_ra, "chang 4") if v4 else []
    cap4 = {}
    for d in r4:
        k = (d["ma"], d["khung"], d["co_che"], d.get("cau_truc"), d.get("luat"))
        cap4.setdefault(k, {})[d["phan"]] = d
    song4 = []
    for k, hai in cap4.items():
        if "train" not in hai or "hold" not in hai:
            continue
        tr, ho = hai["train"], hai["hold"]
        song4.append({"ma": k[0], "khung": k[1], "co_che": k[2],
                      "cau_truc": k[3], "luat": k[4],
                      "dd20_train": tr["cagr_dd20"], "dd20_hold": ho["cagr_dd20"],
                      "hon_moc_train": tr["hon_moc"], "hon_moc_hold": ho["hon_moc"],
                      "moc_hold": ho["moc_dd20"], "chan_hold": ho.get("so_chan")
                      or ho.get("so_lenh")})
    # TIEU CHI QUA HOLDOUT - siet sau lan chay dau (12/09/2026).
    #
    # Ban dau chi doi "train duong VA hold thang moc" -> 29/35 qua, mot ti le
    # khong tin duoc. Doc bang thi ro hai lo:
    #   * `moc_hold = 0,00` voi AUDSEK: mua-giu VA ban-giu deu am o nua sau, nen
    #     moc tut ve TIEN MAT. "Thang moc" luc do chi co nghia "duong".
    #   * `dd20_train 1,67 -> dd20_hold 48,86`: gap 30 lan. Do khong phai ben,
    #     do la nua sau tinh co co mot xu huong. Mot he ben thi hai nua GIONG
    #     NHAU, khong phai nua sau to hon.
    # Nen doi ca ba: hai nua deu thang MOC CUA CHINH NO, va hai nua cung co.
    def _ben(x):
        if not (x["hon_moc_train"] and x["hon_moc_hold"]):
            return False
        a, b = x["dd20_train"], x["dd20_hold"]
        if a <= 0 or b <= 0:
            return False
        x["ty_le_hold_tren_train"] = round(b / a, 3)
        return TY_LE_HAI_NUA[0] <= b / a <= TY_LE_HAI_NUA[1]

    for x in song4:
        # Danh dau NGAY TREN DONG, de `tong_ket` khong phai suy lai tieu chi.
        # Hai cho dinh nghia cung mot thu la mam sai lech: vua sua tieu chi o
        # day xong thi bao cao van in con so cu (29 thay vi 19).
        x["qua_holdout"] = _ben(x)
    qua = [x for x in song4 if x["qua_holdout"]]
    in_ra("  giu ca hai dau: %d he - THANG MOC O HOLDOUT: %d"
          % (len(song4), len(qua)))

    ket = {"giay": round(time.time() - t0, 1), "khung": list(cac_khung),
           "so_ma": len(ma), "bo_trung": bo_trung,
           "so_co_che": len(cc),
           "chang": {"1": {"o": len(v1), "ket_qua": len(r1), "giu": len(song1)},
                     "2": {"o": len(v2), "ket_qua": len(r2), "giu": len(song2)},
                     "3": {"o": len(v3), "ket_qua": len(r3)},
                     "4": {"o": len(v4), "cap_du": len(song4),
                           "qua_holdout": len(qua)}},
           "holdout": sorted(song4, key=lambda x: -x["dd20_hold"]),
           "top": sorted(r2 + r3, key=lambda d: -d["cagr_dd20"])[:120],
           "tat_ca_chang2": r2, "chang3": r3}
    tep = LAB / "reports" / "TO_HOP.json"
    tep.parent.mkdir(exist_ok=True)
    tep.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float),
                   encoding="utf-8")
    in_ra("\n-> %s" % tep)
    return ket


# ------------------------------------------------------------------ TONG KET
def _theo_chieu(rows: list[dict], khoa: str) -> list[dict]:
    theo: dict[str, list[float]] = {}
    moc: dict[str, int] = {}
    for r in rows:
        k = str(r.get(khoa, "?"))
        theo.setdefault(k, []).append(float(r["cagr_dd20"]))
        moc[k] = moc.get(k, 0) + (1 if r.get("hon_moc") else 0)
    ra = []
    for k, v in theo.items():
        ra.append({"gia_tri": k, "so_o": len(v),
                   "trung_vi": round(float(np.median(v)), 3),
                   "tot_nhat": round(float(np.max(v)), 3),
                   "ti_le_duong": round(float(np.mean(np.array(v) > 0)), 3),
                   "hon_moc": moc[k]})
    return sorted(ra, key=lambda d: -d["trung_vi"])


def tong_ket(ket: dict | None = None, in_ra=print) -> str:
    """Rut ra HUONG NEN DI va HUONG NEN TRANH tu bang to hop.

    Chu du an: *"tim ra huong di nen tranh huong khong nen tiep tuc"*. Nen o day
    khong chi xep hang cai tot - phan NEN TRANH duoc viet ra ro rang bang nhau,
    vi biet cho nao khong co gi cung tiet kiem CPU y het biet cho nao co.
    """
    if ket is None:
        ket = json.loads((LAB / "reports" / "TO_HOP.json").read_text(
            encoding="utf-8"))
    rows = ket.get("tat_ca_chang2") or ket.get("top") or []
    if not rows:
        in_ra("chua co du lieu to hop")
        return ""
    d = ["# TONG KET TO HOP", "",
         "*%d o chang 2 / %d ma / khung %s / %.0f giay*"
         % (len(rows), ket.get("so_ma", 0), ", ".join(ket.get("khung", [])),
            ket.get("giay", 0)), "",
         "Xep hang bang `cagr_dd20`: lai %/nam khi quy ca hai ve cung ngan sach",
         "sut giam 20%. `hon_moc` = thang **max(mua-giu, ban-giu, tien mat)**.", "",
         "## DOC BANG NAY NHU THE NAO", "",
         "Chang 1 da CHON top %d o theo chinh `cagr_dd20`, roi chang 2 mo rong"
         % GIU_CHANG1,
         "dung nhung o do. Nen con so `hon_moc` o day **bi thoi len boi chinh phep",
         "chon** - no khong phai ti le thanh cong cua mot lan quet mu.",
         "",
         "Cai bang nay tra loi duoc, va chi tra loi duoc, mot cau: *voi nhung o da",
         "co ve co gi, thi doi CAU TRUC hay doi LUAT lam ket qua thay doi ra sao*.",
         "Do la dung cau hoi chu du an dat ra cho module quan li lenh. Muon biet",
         "ti le thanh cong THAT thi phai doc chang 1 (chua chon), hoac chay lai",
         "tren holdout.", ""]
    for khoa, ten in (("khung", "KHUNG"), ("cau_truc", "CAU TRUC VAO LENH"),
                      ("luat", "LUAT QUAN TRI"), ("ho", "HO CO CHE"),
                      ("ma", "TAI SAN")):
        bang = _theo_chieu(rows, khoa)
        if len(bang) < 2:
            continue
        d += ["## Theo %s" % ten, "",
              "| %s | o | dd20 trung vi | tot nhat | ti le duong | hon moc |"
              % ten.lower(), "|---|---:|---:|---:|---:|---:|"]
        for r in bang[:12]:
            d.append("| %s | %d | %.3f | %.3f | %.0f%% | %d |"
                     % (r["gia_tri"], r["so_o"], r["trung_vi"], r["tot_nhat"],
                        r["ti_le_duong"] * 100, r["hon_moc"]))
        tot, te = bang[0], bang[-1]
        d += ["", "**NEN DI**: %s (trung vi %.3f, %d/%d o duong)"
              % (tot["gia_tri"], tot["trung_vi"],
                 int(tot["ti_le_duong"] * tot["so_o"]), tot["so_o"]),
              "", "**NEN TRANH**: %s (trung vi %.3f, chi %d/%d o duong)"
              % (te["gia_tri"], te["trung_vi"],
                 int(te["ti_le_duong"] * te["so_o"]), te["so_o"]), ""]

    ho = ket.get("holdout") or []
    if ho:
        qua = [x for x in ho if x.get("qua_holdout")]
        d += ["## CHANG 4 - HOLDOUT (chang quyet dinh)", "",
              "Chon tren 60% dau, DO tren 40% sau. Ba chang tren deu chon tren",
              "chinh so chung do, nen chi bang nay noi duoc co gi that hay khong.",
              "",
              "**%d/%d he thang moc o holdout.**" % (len(qua), len(ho)), ""]
        if qua:
            d += ["Tieu chi: hai nua deu thang moc CUA CHINH NO, va ti le",
                  "`hold/train` nam trong [%.2f, %.1f] (hai nua cung co)."
                  % TY_LE_HAI_NUA, "",
                  "| ma | khung | co che | cau truc | luat | dd20 train | dd20 HOLD | ti le | moc hold |",
                  "|---|---|---|---|---|---:|---:|---:|---:|"]
            for x in sorted(qua, key=lambda y: -y["dd20_hold"])[:20]:
                d.append("| %s | %s | %s | %s | %s | %.2f | **%.2f** | %.2f | %.2f |"
                         % (x["ma"], x["khung"], str(x["co_che"])[:26],
                            x["cau_truc"], x["luat"] or "-", x["dd20_train"],
                            x["dd20_hold"], x.get("ty_le_hold_tren_train", 0),
                            x["moc_hold"]))
            d.append("")
        else:
            d += ["Khong he nao song sang nua sau. Do la ket qua manh nhat co the",
                  "rut ra tu mot lan quet: khong gian nay khong chua edge ben.", ""]

    hon = [r for r in rows if r.get("hon_moc")]
    d += ["## Cai duy nhat dang theo tiep", "",
          "%d/%d o thang duoc moc. " % (len(hon), len(rows))]
    if hon:
        d += ["", "| ma | khung | co che | cau truc | luat | dd20 | moc |",
              "|---|---|---|---|---|---:|---:|"]
        for r in sorted(hon, key=lambda x: -x["cagr_dd20"])[:20]:
            d.append("| %s | %s | %s | %s | %s | %.3f | %.3f |"
                     % (r["ma"], r["khung"], str(r.get("co_che"))[:28],
                        r.get("cau_truc", "-"), r.get("luat", "-"),
                        r["cagr_dd20"], r.get("moc_dd20", 0)))
    else:
        d += ["", "**Khong o nao thang moc.** Do la mot ket qua, khong phai mot",
              "loi: no noi rang tren khong gian nay, giu tai san con hon giao dich no."]
    vb = "\n".join(d) + "\n"
    tep = LAB / "reports" / "TO_HOP_TONG_KET.md"
    tep.write_text(vb, encoding="utf-8")
    in_ra(vb)
    in_ra("-> %s" % tep)
    return vb


def main(argv: list[str]) -> int:
    kh, gh_ma, gh_cc, sp = [], 0, 0, 10
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--ma":
            gh_ma = int(argv[i + 1]); i += 2
        elif a == "--co-che":
            gh_cc = int(argv[i + 1]); i += 2
        elif a == "--tien-trinh":
            sp = int(argv[i + 1]); i += 2
        elif a == "--tong-ket":
            tong_ket(); return 0
        else:
            kh.append(a); i += 1
    ket = chay(tuple(kh) if kh else KHUNG_MAC_DINH, gh_ma, gh_cc, sp)
    tong_ket(ket)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
