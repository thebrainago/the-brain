# -*- coding: utf-8 -*-
"""quan_tri_dsl.py - NGON NGU KHAI BAO CHO QUAN TRI VI THE.

Chu du an 07/09/2026: *"FX la cuoc choi quan li vi the, khi quan li vi the tot
thi co the xu li duoc moi van de va loi nhuan rat tot."* Va: *"EA khong gan duoc
sau nay ta van co the de lenh len de quan li von."*

Du an co so ung ho luan diem do: **entry co tinh SAI van cho 92-97%/nam**, va loc
"dung chieu" con TE HON loc dao nguoc [[quan-tri-vi-the-lon-hon-entry]]. Nhung
thu vien co che thi **262 cai toan la tin hieu VAO, 0 cai quan tri**
[[quan-tri-la-ho-co-che-thu-hai]] - DSL cu khong dien dat duoc quan tri.

## MOT NGON NGU, HAI BO PHAT MA

Rang buoc cung: **MT5 Strategy Tester chi chay DUNG MOT EA**. Nen "de lenh len
EA ngoai" chay that duoc (hai EA hai chart) nhung khong backtest duoc kieu do.
Giai phap: cung mot khai bao, hai duong ra -

    nhung      -> chen vao EA sinh tu `dich_mq5` (DE DO trong tester)
    giam sat   -> EA doc lap doc vi the theo magic (DE CHAY THAT tren EA ngoai)

## BA NGUYEN THUY - moi co che quan tri deu rut ve day

    KHI  <trang thai>  THI  <hanh dong>
    TRAILING  = truong hop rieng cua "doi dung lo"
    CHAN      = tran cung, khong dieu kien

`<trang thai>` doc duoc CA vi the don LAN ro (nhieu vi the cung magic):

    vi_the.lai / vi_the.lo        theo atr | r | pct | tien
    vi_the.so_nen                 so nen da giu
    ro.lai / ro.lo                tong ca ro
    ro.so_vi_the                  so vi the dang mo
    ro.cach_gia_tb                khoang cach tu gia trung binh
    gio                           gio trong ngay

`<hanh dong>`:

    dong_het · dong_mot_phan(ty_le) · nhoi(lot_x, chieu) · doi_sl(den)
    hedge(lot_x) · cat_hoa · ngung_vao_moi

## DON VI PHAI KHAI BAO, KHONG DUOC DOAN

Tac gia EA go `InpBreakEvenPips = 10` - **10 PIP**, khong phai 10 ATR. Bung
nguyen sang tai san khac la mot trong hai ket cuc vo nghia
[[quy_doi_tham_so]]. Nen moi con so trong DSL nay deu la mot dict co don vi:

    {"atr": 1.5} · {"pip": 10} · {"diem": 50} · {"pct": 2.0} · {"tien": 100}
    {"r": 1.0}   (boi cua khoang cach dung lo)

`atr` la don vi UU TIEN vi no khong thu nguyen theo tai san lan khung
[[bo-doi-khung-ba-buoc]].

## BA CHOT CHAN (deu tu loi da mac 07/09)

1. **Hanh dong sinh Y DINH, khong dat lenh thang.** Nen khung tin hieu doi luc
   00:00 nam NGOAI phien CFD chi so -> dat thang o do thi lenh tra "Market
   closed" va khong de lai dau vet [[tester-cfd-chi-so-3-bay]].
2. **`dong_mot_phan` phai kiem lot toi thieu.** Nua vi the 0,05 duoi min 0,10
   thi `PositionClosePartial` **that bai im lang** va bang so doc y het "tia
   khong an thua".
3. **He nen giu qua ngan thi quan tri vo hieu** - module phai TU BAO chu khong
   tra ve mot bang so trong nhu that [[quan-tri-can-cho-de-hoat-dong]].
"""
from __future__ import annotations

DON_VI = ("atr", "pip", "diem", "pct", "tien", "r", "nen", "gio")

TRANG_THAI = {
    "vi_the.lai", "vi_the.lo", "vi_the.so_nen",
    "ro.lai", "ro.lo", "ro.so_vi_the", "ro.cach_gia_tb", "ro.tuoi_gio",
    "gio",
}

HANH_DONG = {
    "dong_het", "dong_mot_phan", "nhoi", "doi_sl", "hedge", "cat_hoa",
    "ngung_vao_moi",
}

#: Anh xa nut van cua `quan_tri.boc_kho()` -> (truong DSL, don vi mac dinh).
#: Ten nut van do `quan_tri.ANH_XA` sinh ra tu chinh input cua tac gia EA.
TU_NUT_VAN = {
    "breakeven_tu":   ("dat_hue.tu", "pip"),
    "trailing_tu":    ("trailing.bat_dau", "pip"),
    "trailing_buoc":  ("trailing.khoang", "pip"),
    "buoc":           ("nhoi.khoang", "pip"),
    "dung_lo":        ("chan.lo_toi_da", "pip"),
    "tp":             ("chot.muc", "pip"),
    "he_so_1":        ("nhoi.lot_x", "he_so"),
    "tang_toi_da":    ("chan.so_vi_the_toi_da", "so"),
    "cat_hoa_tu":     ("cat_hoa.tu", "pip"),
    "chot_tien":      ("chot.tien", "tien"),
    "hedge_tu":       ("hedge.tu", "pip"),
    "hedge_ty":       ("hedge.lot_x", "he_so"),
    "thoat_theo_gio": ("chan.tuoi_gio_toi_da", "gio"),
    "vol_min":        ("chan.vol_min", "so"),
    "vol_max":        ("chan.vol_max", "so"),
    "_lot_goc":       ("lot_goc", "so"),
    "_lot_toi_da":    ("chan.lot_toi_da", "so"),
    "_risk_pct":      ("rui_ro_pct", "pct"),
}

#: Dau hieu bóc duoc -> ho quan tri. Dung de biet mot spec thuoc lop DON hay RO.
HO_RO = {"luoi", "martingale", "dca", "hedge", "recovery", "chot_ro"}
HO_DON = {"trailing", "breakeven", "tia_lenh", "chan_von", "thang_lot",
          "lenh_cho"}


def _dat(d: dict, duong: str, gt) -> None:
    nut = d
    phan = duong.split(".")
    for k in phan[:-1]:
        nut = nut.setdefault(k, {})
    nut[phan[-1]] = gt


def tu_boc(spec_boc: dict) -> dict:
    """Doi mot spec cua `quan_tri.boc_kho()` sang DSL quan tri.

    Giu NGUYEN don vi cua tac gia (pip/tien/so) va ghi ro - khong quy doi o day.
    Quy doi sang ATR la viec cua `sang_atr()`, va no can du lieu cua tai san
    dich nen khong lam duoc luc boc.
    """
    ra = {"ten": spec_boc.get("ten"), "ho": "quan_tri",
          "nguon": spec_boc.get("artifact_id"),
          "dau_hieu": list(spec_boc.get("dau_hieu") or []),
          "lop": "ro" if (set(spec_boc.get("dau_hieu") or []) & HO_RO)
                 else "don"}
    thieu = []
    for nut, gt in (spec_boc.get("nut_van") or {}).items():
        anh = TU_NUT_VAN.get(nut)
        if anh is None:
            thieu.append(nut)
            continue
        duong, dv = anh
        _dat(ra, duong, gt if dv in ("so", "he_so") else {dv: gt})
    if thieu:
        ra["_chua_anh_xa"] = thieu
    return ra


def kiem_khai_bao(spec: dict) -> list[str]:
    """Cong vao cua ho quan tri. Tra danh sach ly do; rong = qua.

    Cong nay hoi **"co chay duoc khong"**, KHONG hoi "co lai khong" - do la viec
    cua cham diem [[quy trinh quantlab]].
    """
    loi = []
    if not spec.get("ten"):
        loi.append("thieu 'ten'")
    co = [k for k in ("dat_hue", "trailing", "nhoi", "chot", "cat_hoa", "hedge",
                      "chan", "khi") if spec.get(k)]
    if not co:
        loi.append("khong co luat quan tri nao (dat_hue/trailing/nhoi/chot/"
                   "cat_hoa/hedge/chan/khi)")
    # Nhoi ma khong co tran la cong thuc chay tai khoan - da do 07/09: he so lot
    # 1,5 cho DD 99,98% ngay TRONG mau [[quan-tri-chi-dat-hue-song-sot]].
    nh = spec.get("nhoi") or {}
    if nh:
        chan = spec.get("chan") or {}
        if not chan.get("so_vi_the_toi_da") and not chan.get("lot_toi_da"):
            loi.append("co 'nhoi' ma khong co tran 'chan.so_vi_the_toi_da' hay "
                       "'chan.lot_toi_da' - do la cong thuc chay tai khoan")
        hs = nh.get("lot_x")
        if isinstance(hs, (int, float)) and hs > 1.0:
            loi.append("'nhoi.lot_x' = %s > 1,0 la martingale tren LOT - da do "
                       "DD 99,98%% ngay trong mau" % hs)
    for k in ("dat_hue", "trailing", "cat_hoa", "hedge"):
        v = spec.get(k)
        if isinstance(v, dict):
            for f, x in v.items():
                if isinstance(x, dict) and not (set(x) & set(DON_VI)):
                    loi.append("%s.%s thieu don vi (%s)" % (k, f, "|".join(DON_VI)))
    return loi


class KhongQuyDoiDuoc(Exception):
    """`atr` <= 0 (khong do duoc tren du lieu that). Loi 12/09: ban cu `return
    nut if atr <= 0 else ...` IM LANG tra ve pip/diem CHUA quy doi - roi dich_mq5_qtvt
    doc nham dict do la "khong co", ghi 0.0, va ca bang luat sinh ra GIONG HET
    nhau (14/15 luat = 1759 lenh/-108,76/1,3121). Tu 12/09: atr<=0 phai NEM LOI
    ngay tai day, khong duoc de no troi xuong tang duoi roi bien mat thanh so 0."""


def sang_atr(spec: dict, atr: float, gia_diem: float = 0.01) -> dict:
    """Quy MOI so do khoang cach ve boi cua ATR, dung du lieu tai san dich.

    `atr` do tren KHUNG se chay. `gia_diem` = `SYMBOL_POINT` (1 pip = 10 diem
    voi ma 5 chu so; voi chi so thi tac gia thuong go 'pip' ma y la DIEM - nen
    ham nay nhan `gia_diem` chu khong doan).
    """
    if not (isinstance(atr, (int, float)) and atr > 0):
        raise KhongQuyDoiDuoc(
            "atr=%r khong do duoc/khong hop le - can do tren du lieu THAT cua "
            "symbol+khung se chay (vd nhan/du_lieu.nap), khong duoc mac dinh 0"
            % (atr,))
    import copy
    ra = copy.deepcopy(spec)

    def _di(nut):
        if isinstance(nut, dict):
            if set(nut) & {"pip", "diem"} and len(nut) == 1:
                k, v = next(iter(nut.items()))
                gia = v * gia_diem * (10 if k == "pip" else 1)
                return {"atr": round(gia / atr, 4)}
            return {k: _di(v) for k, v in nut.items()}
        if isinstance(nut, list):
            return [_di(x) for x in nut]
        return nut

    for k in list(ra):
        if k not in ("ten", "ho", "nguon", "dau_hieu", "lop", "_chua_anh_xa"):
            ra[k] = _di(ra[k])
    ra["_da_quy_atr"] = True
    return ra


# ============================================================== KHO QUAN TRI
import json as _json
from pathlib import Path as _Path

KHO = _Path(__file__).resolve().parent.parent / "config" / "quan_tri_dsl.json"


def doc_kho() -> list[dict]:
    """Doc kho co che QUAN TRI. Tach hoan toan khoi kho tin hieu vao.

    Hai kho phai tach vi chung tra loi hai cau khac nhau va di qua hai cong
    khac nhau: kho tin hieu hoi "vao luc nao", kho nay hoi "vao roi thi lam gi".
    """
    if not KHO.exists():
        return []
    try:
        return _json.loads(KHO.read_text(encoding="utf-8"))
    except Exception:
        return []


def luu_kho(ds: list[dict]) -> None:
    KHO.parent.mkdir(parents=True, exist_ok=True)
    KHO.write_text(_json.dumps(ds, ensure_ascii=False, indent=1),
                   encoding="utf-8")


def van_tay(spec: dict) -> str:
    """Van tay theo LUAT, khong theo ten - de khu trung khi nap tu nhieu nguon."""
    import hashlib
    goc = {k: v for k, v in sorted(spec.items())
           if k in ("dat_hue", "trailing", "nhoi", "chot", "cat_hoa", "hedge",
                    "chan", "lop")}
    return hashlib.md5(_json.dumps(goc, sort_keys=True,
                                   ensure_ascii=False).encode()).hexdigest()[:12]


def nap_tu_boc(in_ra=print) -> dict:
    """Boc 75 co che quan tri tu ma nguon EA -> DSL -> kho. Tra bang dem.

    KHONG loai cai bi cong chan: chung van chay duoc neu nguoi dung THEM TRAN
    (`chan.so_vi_the_toi_da`), va do la mot tham so chu khong phai mot phan
    quyet. Danh dau `_bi_chan` de biet cai nao can nguoi nhin.
    """
    from . import quan_tri as _QT
    tho = _QT.boc_kho(in_ra=lambda *a, **k: None)
    cu = {van_tay(x): x for x in doc_kho()}
    them = trung = 0
    for s in tho:
        d = tu_boc(s)
        loi = kiem_khai_bao(d)
        d["_bi_chan"] = loi or []
        vt = van_tay(d)
        if vt in cu:
            trung += 1
            continue
        cu[vt] = d
        them += 1
    ds = list(cu.values())
    luu_kho(ds)
    qua = sum(1 for x in ds if not x.get("_bi_chan"))
    in_ra("kho quan tri: %d co che (them %d, trung %d) | qua cong %d | bi chan %d"
          % (len(ds), them, trung, qua, len(ds) - qua))
    return {"tong": len(ds), "them": them, "trung": trung, "qua": qua}
