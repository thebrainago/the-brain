# -*- coding: utf-8 -*-
"""loc_co_che.py - BO LOC TINH, CHAY TRUOC PHEU V0-V3.

Chu du an 05/09/2026: *"Xay dung bo loc va quy trinh kiem dinh sao cho toc do
va hop li nhat"*.

## CHO NAY DUNG O DAU

    kho co che (339 template)
      -> `loc_co_che.loc`      <- FILE NAY. Tinh, ~1 giay cho ca kho.
      -> `sang_loc.chay_pheu`  V0 van tay -> V1 re -> V2 kinh te -> V3 phan chung
      -> `cong.xet`            V4, cho duy nhat tieu suat FDR

Phep do 05/09: mot o pheu D1 ton **0,216 giay**; sinh tin hieu cho CA 339
template tren mot tai san ton **0,4 giay**. Be mat D1 la 339 x 126 tai san =
**42.714 o** = ~2,4 gio mot luong. Nen mot bo loc tinh cat duoc 1/3 so template
tiet kiem gan mot gio may, va no tra tien ngay trong giay dau tien.

## BON CAU HOI, DEU TRA LOI DUOC MA KHONG CAN CHAY BACKTEST

Do 05/09 tren 339 template x XM_US100CASH D1:

    1. SINH DUOC KHONG?          31 template nem ngoai le
    2. CO SUY BIEN KHONG?        45 gan nhu khong bao gio vao lenh
                                  7 gan nhu luon o trong thi truong
                                  8 duoi 10 lan doi vi the
    3. CO TRUNG HANH VI KHONG?   56 template gop lai chi con 11 chuoi tin hieu
    4. (con lai)                248 dung duoc

**Muc 3 la cai dang gia nhat.** Hai muoi template ten khac han nhau - `Breakout
Buy`, `BullBreakout`, `MA_RSI_Buy`, `H1H4_Buy_Signal`, `Breakout_Buy` - sinh ra
**y het mot chuoi tin hieu**. Chung khong phai 20 gia thuyet; chung la MOT, boc
ra tu 20 file khac nhau noi cung mot y. Dem chung nhu 20 phep thu vua dot CPU
vua lam hong moi con so ve "da thu bao nhieu gia thuyet".

Chong trung o day khac chong trung cua `ngu_phap.van_tay_dieu_kien`: cai kia so
KHAI BAO (hai cach viet khac nhau cua cung mot luat van la hai van tay), cai nay
so HANH VI (cung chuoi tin hieu tren cung du lieu = mot co che). Van tay khai bao
van can - no chan trung ngay luc ghi kho; van tay hanh vi bat phan con lai.

## KHONG DUOC KET LUAN TREN MOT TAI SAN

Mot co che im lang tren US100 co the song tren vang. Nen moi phep do o day chay
tren `SO_MA_DO` tai san khac lop nhau, va **chi loai khi suy bien tren TAT CA**.
Trung hanh vi cung vay: chi gop khi trung tren TAT CA tai san do duoc.

Gia cua luat nay la 3 lan 0,4 giay. Gia cua viec khong co no la nem mat mot co
che that vi no khong hop voi mot chi so My - dung ho benh
[[ket-luan-am-phai-phan-biet-chua-do]].

## LOI SINH KHONG PHAI MOT NHOM

31 loi sinh, va chung la BA viec khac han nhau:

    KhungThieuGio      7   co che theo PHIEN chay tren D1. **Khong hong** - sai
                           khung. Phai chuyen sang H1/M15 chu khong phai bo.
    spec HONG         13   `vao: ["khong_dien_dat_duoc"]`, thieu khoa `trai`,
                           toan hang la chuoi thay vi dict. LLM tra ve sai dinh
                           dang va `kiem_khai_bao` da cho qua. Day la RAC trong
                           kho, phai bao ra de don.
    thieu cot          2   spec doi cot `bid` - kho gia khong co.

Gop ca ba thanh "31 template hong" thi khong sua duoc cai nao trong ba.
"""
from __future__ import annotations

import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

#: Tai san do suy bien. Khac LOP nhau co chu dich: mot chi so My, mot hang hoa,
#: mot cap tien. Co che chi bi loai khi im lang tren CA BA.
SO_MA_DO = ("XM_US100CASH", "XAUUSD", "EURUSD")

#: Duoi nguong nay coi nhu khong bao gio vao lenh. 0,5% so bar tren D1 ~ 20 bar
#: trong 15 nam - khong du de ket luan gi, va pheu se bao `thieu_lenh` o V2 sau
#: khi da ton mot backtest day du.
TY_LE_IT = 0.005
#: Tren nguong nay la MUA-GIU TRA HINH. [[mau-phien-thoai-hoa-tren-D1]]: mot mau
#: thanh hang so 1,0 da tung vao thang hang 2 cua bang xep hang - no khong phai
#: mot he thong, no la mua-giu doi ten.
TY_LE_NHIEU = 0.98
#: Duoi so lan doi vi the nay thi khong co gi de do.
LENH_IT = 10

#: Loi sinh -> nhom. Ba nhom xu ly khac han nhau, xem docstring.
SAI_KHUNG = "sai_khung"
SPEC_HONG = "spec_hong"
THIEU_COT = "thieu_cot"
LOI_KHAC = "loi_khac"


#: Chuoi dung de CHAY THU mot spec truoc khi cho vao kho.
#:
#: Phai la khung co GIO. Do 05/09: 11 co che trong kho la co che theo PHIEN
#: (`mua_qua_dem`, `orb_pha_vo`, `thanh_ly_cuoi_ngay`...) va chung nem
#: `KhungThieuGio` tren D1. Lay D1 lam chuoi kiem thi cong se tu choi dung 11
#: cai do vi mot ly do khong lien quan gi den chat luong cua chung.
MA_KIEM, KHUNG_KIEM = "XM_US100CASH", "H1"


def df_kiem_chuan():
    """Chuoi de `ngu_phap.them_co_che` chay thu. `None` neu khong nap duoc."""
    from nhan import du_lieu as DL
    for ma, khung in ((MA_KIEM, KHUNG_KIEM), ("EURUSD", "H1"), ("EURUSD", "H4")):
        try:
            return DL.hai_nua(DL.nap(ma, khung), 0.6)[0]
        except Exception:
            continue
    return None


def _nhom_loi(e: BaseException) -> str:
    ten = type(e).__name__
    tin = str(e)
    if ten == "KhungThieuGio" or "chi co mot" in tin:
        return SAI_KHUNG
    if "khong co cot" in tin:
        return THIEU_COT
    if (ten in ("TypeError", "KeyError")
            and ("string indices" in tin or "'trai'" in tin
                 or "phai la dict" in tin or "khong_dien_dat_duoc" in tin)):
        return SPEC_HONG
    return LOI_KHAC


#: Duoi muc nay thi hang so co the la mot nguong da chuan hoa (RSI 30, IBS 0,2,
#: zscore -2), tren muc nay thi gan nhu chac chan la MOT MUC GIA cu the.
TRAN_HANG_SO_GIA = 5.0


def _hang_so_gia(spec: dict) -> float | None:
    """Spec co ve nao so GIA voi mot HANG SO TUYET DOI khong? Tra hang so do.

    `close >= 4428.1` khong phai co che - do la mot loi ho gia vang cua mot bai
    viet tai mot thoi diem. No dung o dung mot tai san trong dung mot thang, va
    tren moi tai san khac no la hang so `False`. Do 05/09: 5 spec kieu nay trong
    kho (vang 4428,1 va 4477 · ETH 1950 va 2540 · 1980).

    Chung con lam do bai `test_moi_mau_deu_phan_ung_voi_it_nhat_mot_tham_so`
    theo mot duong vong: tham so cua chung LA muc gia, doi mot chut thi tin hieu
    van rong, nen chung bi dem la "diec".
    """
    for ve in list(spec.get("vao") or []) + list(spec.get("ra") or []):
        if not isinstance(ve, dict):
            continue
        trai, phai = ve.get("trai"), ve.get("phai")
        if (isinstance(trai, dict) and trai.get("chi_bao") == "gia"
                and isinstance(phai, dict) and "hang" in phai):
            try:
                h = float(phai["hang"])
            except (TypeError, ValueError):
                continue
            if abs(h) > TRAN_HANG_SO_GIA:
                return h
    return None


def _van_tay_hanh_vi(th) -> str:
    a = np.nan_to_num(np.asarray(th, dtype=float))
    return hashlib.blake2b(a.tobytes(), digest_size=8).hexdigest()


def _do_mot_ma(ten_mau_ds, df) -> dict:
    """Sinh tin hieu cho moi template tren MOT tai san.

    Tra {ten: {"vt", "ty_le", "so_lenh"}} hoac {"loi": nhom}.
    """
    from nhan import mau as MAU
    ra = {}
    for ten in ten_mau_ds:
        try:
            th = MAU.sinh(ten, df, {})
        except BaseException as e:                      # noqa: BLE001
            ra[ten] = {"loi": _nhom_loi(e), "tin": "%s: %s"
                       % (type(e).__name__, str(e)[:70])}
            continue
        a = np.asarray(th, dtype=float)
        s = a[~np.isnan(a)]
        if s.size == 0:
            ra[ten] = {"loi": SPEC_HONG, "tin": "chuoi tin hieu rong"}
            continue
        trong = (np.abs(s) > 0).astype(int)
        ra[ten] = {"vt": _van_tay_hanh_vi(a),
                   "ty_le": float(trong.mean()),
                   "so_lenh": int(np.sum(np.abs(np.diff(trong)) > 0))}
    return ra


def loc(cac_mau=None, khung: str = "D1", cac_ma=None, in_ra=print) -> dict:
    """Loc tinh CA KHO. Tra {dung_duoc, bo, chuyen_khung, hong, bi_danh}.

    `dung_duoc` la danh sach template dang dua len be mat. `bi_danh` la
    {ten_giu: [ten bi gop]} - de sau nay truy nguoc mot ket qua ve moi nguon da
    noi ra no.
    """
    from nhan import du_lieu as DL
    from nhan import mau as MAU
    from nhan import ngu_phap as NP

    # [[nap-vao-mau-truoc-khi-doc-mau]] - doc thang `MAU.MAU` truoc buoc nay thi
    # chi thay 18 template viet tay, mat sach 321 co che boc tu kho.
    NP.nap_vao_mau()
    ten_ds = list(cac_mau or sorted(MAU.MAU))

    # --- CHAN O MUC KHAI BAO, TRUOC KHI CHAM DU LIEU ---
    #
    # Lo hong tim ra 06/09/2026. `_hang_so_gia` co tu 05/09 va `don_kho` co goi
    # no, nhung `don_kho` **chi bao cao, khong ghi** - con `loc()`, cai duy nhat
    # dung tren duong len be mat, thi khong goi bao gio. Ket qua:
    # `aapl_call_breakout_above_322_50` (`close >= 325.25`) van len be mat sau
    # ca mot ngay ke ten no trong ban giao. Mot chan doan dung ma khong noi vao
    # duong chay thi khong khac gi chua chan doan [[noi-day-truoc-khi-xay-them]].
    #
    # Chan o day re hon chan bang du lieu: khong o backtest nao, va ly do tu
    # choi mang DUNG TEN ("nguong gia tuyet doi") thay vi "suy bien tren moi
    # tai san" - cau sau doc nhu mot phat hien ve thi truong.
    kho_theo_ten = {c.get("ten"): c for c in NP.doc_kho()}
    tong_ban_dau = len(ten_ds)
    bo_khai_bao, chi_tiet_gia, chi_tiet_kb = {}, [], []
    for ten in list(ten_ds):
        spec = kho_theo_ten.get(ten)
        if spec is None:
            continue                                   # mau viet tay: khong co spec
        h = _hang_so_gia(spec)
        if h is not None:
            # Ly do phai la MOT khoa on dinh: nhet con so vao day thi moi co
            # che thanh mot nhom rieng trong bang dem, va bang doc nhu the moi
            # cai la mot benh khac nhau.
            bo_khai_bao[ten] = "nguong_gia_tuyet_doi"
            chi_tiet_gia.append((ten, h))
            ten_ds.remove(ten)
            continue
        # CONG CUA CHINH HE, AP CHO CA HANG DA VAO KHO.
        #
        # Do 06/09: **169/540 muc trong kho khong qua noi `kiem_khai_bao`** -
        # phan lon thieu han truong `co_che`, cau noi ai la ben doi ung. Chung
        # vao qua cua sau (duong LLM ghi thang file JSON), va vi `loc()` chua
        # bao gio goi cong nen ca 169 van chay tren be mat nhu moi co che khac.
        #
        # Mot cong chi ap cho hang MOI thi khong phai cong, ma la mot thu tuc
        # nhap kho. `_dien_co_che.py` da hoi LLM lay ly do cho cai nao co ly
        # do that; cai nao LLM tra "CHUA_BIET_LY_DO" thi dung ra o day - do la
        # danh sach cho BO, khong phai danh sach cho dien not.
        loi_kb = NP.kiem_khai_bao(spec)
        if loi_kb:
            bo_khai_bao[ten] = "khong_qua_kiem_khai_bao"
            chi_tiet_kb.append((ten, loi_kb[0]))
            ten_ds.remove(ten)

    cac_ma = list(cac_ma or SO_MA_DO)
    do, da_do = {}, []
    for ma in cac_ma:
        try:
            df = DL.hai_nua(DL.nap(ma, khung), 0.6)[0]
        except Exception as e:
            in_ra("  bo qua %s: %s" % (ma, str(e)[:60]))
            continue
        do[ma] = _do_mot_ma(ten_ds, df)
        da_do.append(ma)
    if not da_do:
        # Khong do duoc gi thi KHONG duoc tra ve "khong cai nao dung duoc".
        return {"dung_duoc": ten_ds, "bo": {}, "chuyen_khung": [], "hong": [],
                "bi_danh": {}, "chua_do": True,
                "vi_sao": "khong nap duoc tai san nao trong %s" % (cac_ma,)}

    bo, hong, chuyen, dung = dict(bo_khai_bao), [], [], []
    for ten in ten_ds:
        cac = [do[m].get(ten, {}) for m in da_do]
        loi = [c.get("loi") for c in cac if c.get("loi")]
        if len(loi) == len(cac):                       # hong/sai khung o MOI ma
            nh = Counter(loi).most_common(1)[0][0]
            muc = {"ten": ten, "nhom": nh,
                   "tin": next(c.get("tin", "") for c in cac if c.get("loi"))}
            (chuyen if nh == SAI_KHUNG else hong).append(muc)
            continue
        song = [c for c in cac if not c.get("loi")]
        # Chi loai khi suy bien tren TAT CA tai san do duoc.
        if all(c["ty_le"] < TY_LE_IT for c in song):
            bo[ten] = "gan_khong_bao_gio_vao"
        elif all(c["ty_le"] > TY_LE_NHIEU for c in song):
            bo[ten] = "mua_giu_tra_hinh"
        elif all(c["so_lenh"] < LENH_IT for c in song):
            bo[ten] = "duoi_%d_lan_doi_vi_the" % LENH_IT
        else:
            dung.append(ten)

    # --- gop TRUNG HANH VI: cung van tay tren MOI tai san do duoc ---
    nhom = defaultdict(list)
    for ten in dung:
        khoa = tuple(do[m].get(ten, {}).get("vt") for m in da_do)
        if any(v is None for v in khoa):
            khoa = ("rieng", ten)                      # thieu phep do -> khong gop
        nhom[khoa].append(ten)
    giu, bi_danh = [], {}
    for ds in nhom.values():
        # Giu ten NGAN NHAT: ten do thuong la ten do `doc_ma` sinh theo luat
        # (`ma_close_tren_sma200`), con ten dai la ten tac gia dat trong file.
        ds = sorted(ds, key=lambda t: (len(t), t))
        giu.append(ds[0])
        if len(ds) > 1:
            bi_danh[ds[0]] = ds[1:]

    in_ra("LOC TINH %d template tren %d tai san (%s)"
          % (tong_ban_dau, len(da_do), ", ".join(da_do)))
    in_ra("  spec hong        : %d" % len(hong))
    in_ra("  sai khung        : %d  (co che phien, phai chay khung noi ngay)"
          % len(chuyen))
    for k, v in Counter(bo.values()).most_common():
        in_ra("  %-17s: %d" % (k[:17], v))
    for ten, h in chi_tiet_gia:
        in_ra("      %-40s nguong %.2f" % (str(ten)[:40], h))
    if chi_tiet_kb:
        for ly, n in Counter(v for _, v in chi_tiet_kb).most_common(4):
            in_ra("      %-40s x%d" % (ly[:40], n))
    in_ra("  trung hanh vi    : %d template gop vao %d"
          % (sum(len(v) for v in bi_danh.values()), len(bi_danh)))
    in_ra("  --> len be mat   : %d/%d  (cat %.0f%%)"
          % (len(giu), tong_ban_dau,
             100 * (1 - len(giu) / max(tong_ban_dau, 1))))
    return {"dung_duoc": sorted(giu), "bo": bo, "chuyen_khung": chuyen,
            "hong": hong, "bi_danh": bi_danh, "chua_do": False,
            "da_do_tren": da_do}


def don_kho(that: bool = False, in_ra=print) -> dict:
    """Chuyen cac spec KHONG CHAY DUOC ra khu cach ly.

    Khong XOA: chung duoc ghi sang `config/co_che_dsl_hong.json` kem ly do. Mot
    spec hong van la bang chung ve cho ngu phap con thieu (`khong_dien_dat_duoc`,
    cot `bid`/`ask` chua co) - vut di la mat luon danh sach viec phai lam.

    Mac dinh CHI BAO CAO. `that=True` moi ghi.
    """
    import json as _json
    from pathlib import Path as _P

    from nhan import ngu_phap as NP

    df = df_kiem_chuan()
    if df is None:
        in_ra("khong nap duoc chuoi kiem - khong don gi ca")
        return {"chua_do": True}

    kho = NP.doc_kho()
    giu, hong = [], []
    for c in kho:
        # Ho `khac` khong khai duoc pham vi -> khong co co so doi hoi phep thu
        # phan chung cho no (`nhan/pham_vi.py`). `doc_ma` da bo tu 01/09; duong
        # LLM chua ap luat nen 61 cai lot vao me 05/09.
        from nhan import pham_vi as _PV
        if str(c.get("ho") or "").strip() not in _PV.PHAM_VI:
            hong.append(dict(c, _ly_do_hong="ho '%s' chua khai pham vi"
                             % str(c.get("ho"))[:20]))
            continue
        h = _hang_so_gia(c)
        if h is not None:
            hong.append(dict(c, _ly_do_hong="so GIA voi hang so tuyet doi %.2f"
                             % h))
            continue
        try:
            NP.sinh_tu_spec(c, df)
            giu.append(c)
        except BaseException as e:                      # noqa: BLE001
            hong.append(dict(c, _ly_do_hong="%s: %s"
                             % (type(e).__name__, str(e)[:120])))
    in_ra("kho %d co che: chay duoc %d, hong %d" % (len(kho), len(giu), len(hong)))
    for x in hong[:8]:
        in_ra("   %-40s %s" % (str(x.get("ten"))[:40], x["_ly_do_hong"][:60]))
    if that and hong:
        goc = _P(__file__).resolve().parent.parent / "config"
        p = goc / "co_che_dsl_hong.json"
        cu = _json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
        p.write_text(_json.dumps(cu + hong, ensure_ascii=False, indent=1),
                     encoding="utf-8")
        NP.luu_kho(giu)
        in_ra("  -> da chuyen %d sang %s; kho con %d" % (len(hong), p.name, len(giu)))
    return {"tong": len(kho), "chay_duoc": len(giu), "hong": len(hong),
            "da_ghi": bool(that and hong)}


if __name__ == "__main__":
    import json
    sys.stdout.reconfigure(encoding="utf-8")
    khung = "D1"
    if "--khung" in sys.argv:
        khung = sys.argv[sys.argv.index("--khung") + 1]
    if "--don" in sys.argv:
        don_kho(that="--that" in sys.argv)
        raise SystemExit(0)
    r = loc(khung=khung)
    p = Path(__file__).resolve().parent.parent / "reports" / ("loc_co_che_%s.json" % khung)
    p.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("-> %s" % p)
