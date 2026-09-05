# -*- coding: utf-8 -*-
"""quan_tri_llm.py - ANH XA INPUT -> NUT VAN khi bang REGEX khong doc noi ten.

Chu du an 05/09/2026: *"quan tri vi the ... toi nghi se dung di dung lai va ket
hop duoc voi rat nhieu he thong"*. Va do duoc cung ngay: voi lop luoi, **quan
tri vi the quan trong hon tin hieu vao** - entry co tinh SAI van cho 92-97%/nam.

## VI SAO CAN THEM MOT DUONG

`quan_tri.anh_xa` la mot bang REGEX TREN TEN INPUT. No nhanh (ca kho 389 file
het 1,0 giay), tat dinh, va no doc duoc 53/59 file lan `quan_tri`. Nhung no chi
biet nhung cach dat ten ma nguoi viet bang da nghi ra.

Do 05/09 tren chinh dau ra cua no:

    DailyZoneRecovery.mq5              33 input -> anh xa duoc **1** nut
    SmartTradeAdjustmentPanel.mq5       9 input -> 1
    Quantum_XAUUSD_Silver_Trader.mq5   79 input -> 1
    XProTradePanel.mq5                 25 input -> 1
    BEC_Combined_BE_Trail.mq5          26 input -> 1

10 file roi vao dien nay va bi `quan_tri.loc` gat vi `it_nut_van`. Chung khong
rong - chung dat ten khac. Mot EA goi buoc luoi la `ZoneWidth`, mot EA khac goi
la `KhoangCachNhoi`; khong bang tay nao duoi kip.

## RANH GIOI - GIONG HET HAI DUONG BOC KIA

LLM **khong duoc tao ra nut van moi**. No chi duoc chon MOT ten trong danh sach
`NUT_CHAY_DUOC` co san, hoac tra `null`. Gia tri thi lay tu chinh khai bao
`input` da doc bang regex, **khong lay tu loi mo hinh** - de mot con so bi doc
sai khong bao gio vao duoc cau hinh chay that.

Nen dau ra cua module nay khong the rong hon `mo_phong_v2` biet mo phong, va
khong the mang mot con so ma may chua nhin thay trong ma nguon.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nhan import quan_tri as QT

#: Y nghia tung nut, viet cho NGUOI doc - loi nhac dua nguyen bang nay sang.
#: Khong sinh tu `ANH_XA` vi khoa o do la regex, doc khong ra nghia.
Y_NGHIA_NUT = {
    "buoc": "khoang cach gia giua hai tang luoi (pip hoac diem)",
    "kc_bs": "khoang cach giua lenh Buy va lenh Sell mo cung luc",
    "tp": "chot lai tinh tu GIA TRUNG BINH cua ro, pip",
    "chot_tien": "chot ca ro khi tong lai >= X TIEN",
    "dung_lo": "dong sach khi tong lo >= X TIEN",
    "he_so_1": "he so nhan lot moi tang (martingale / DCA)",
    "tang_toi_da": "so tang toi da duoc mo",
    "cat_hoa_tu": "cat lenh lo nang nhat ghep voi lenh lai (cat hoa) tu tang N",
    "hedge_tu": "mo lenh doi ung (hedge) tu tang thu N",
    "hedge_ty": "ty le lot cua lenh hedge so voi tong lot dang mo",
    "thoat_theo_gio": "dong ca ro sau X GIO bat ke lai lo",
    "vol_min": "chi mo ro moi khi bien dong >= muc nay",
    "vol_max": "chi mo ro moi khi bien dong <= muc nay",
    "trailing_tu": "bat trailing khi lai dat X (pip hoac tien)",
    "trailing_buoc": "buoc keo cua trailing stop",
    "breakeven_tu": "keo dung lo ve hoa von khi lai dat X",
}


#: DON VI ma tung nut van CHAP NHAN. Anh xa dung ten nhung sai don vi thi cau
#: hinh chay ra so, va so do vo nghia.
#:
#: Do 05/09 tren me thu dau tien - ca hai loi deu la loi DON VI, khong phai loi
#: doc hieu:
#:   `InpStrategy1GridStepPct` = 0,34 (PHAN TRAM) bi gan vao `buoc` (pip)
#:   `InpLockProfitPoints`     = 50   (DIEM)      bi gan vao `chot_tien` (TIEN)
#: Ca hai deu "nghe rat hop ly" neu chi doc ten. Du an nay co ca mot ho benh ve
#: don vi ([[don-vi-tai-khoan-khong-cho-them-von]], [[cent-chia-100-von-can]]),
#: nen cong don vi la bat buoc chu khong phai cho chac an.
DON_VI_NUT = {
    "buoc": {"pip", "diem"}, "kc_bs": {"pip", "diem"}, "tp": {"pip", "diem"},
    "trailing_tu": {"pip", "diem"}, "trailing_buoc": {"pip", "diem"},
    "breakeven_tu": {"pip", "diem"},
    "chot_tien": {"tien"}, "dung_lo": {"tien"},
    "he_so_1": {"ty_le"}, "hedge_ty": {"ty_le"},
    "vol_min": {"ty_le"}, "vol_max": {"ty_le"},
    "tang_toi_da": {"so_lan"}, "hedge_tu": {"so_lan"}, "cat_hoa_tu": {"so_lan"},
    "thoat_theo_gio": {"gio"},
}
DON_VI_HOP_LE = sorted({d for v in DON_VI_NUT.values() for d in v} | {"phan_tram"})


def _nhac(ten: str, ins: list[dict], da_co: dict) -> str:
    bang = "\n".join("  %-34s = %-14s (%s)" % (x["ten"][:34], str(x["mac_dinh"])[:14],
                                               x["kieu"])
                     for x in ins[:80])
    nut = "\n".join("  %-16s %s" % (k, v) for k, v in Y_NGHIA_NUT.items())
    dcs = ", ".join("%s <- %s" % (k, v[1]) for k, v in (da_co or {}).items()) or "(chua co)"
    return f"""Day la danh sach tham so `input` cua mot Expert Advisor MQL5 (`{ten}`).
Nhiem vu: anh xa MOI input sang MOT nut van cua bo mo phong quan tri vi the.

NUT VAN CO SAN (chi duoc chon trong danh sach nay, khong duoc tao ten moi):
{nut}

DA ANH XA DUOC bang bang ten (dung lam vi du, dung lap lai): {dcs}

INPUT CUA EA:
{bang}

QUY TAC:
- Mot input chi duoc anh xa khi ban CHAC no dieu khien dung viec do. Khong chac
  thi tra `null` - mot anh xa sai lam sai ca cau hinh chay that.
- BO QUA: magic number, slippage, ten/mau doi tuong, bat/tat log, gio giao dich,
  chon symbol, kich thuoc chu, mau sac.
- Moi nut chi duoc gan NHIEU NHAT mot input.
- KHONG doc gia tri; he tu lay gia tri tu khai bao. Ban chi noi input NAO ung
  voi nut NAO.
- **PHAI khai DON VI** cua input, mot trong: {", ".join(DON_VI_HOP_LE)}.
  Doc ky HAU TO cua ten: `...Pct`/`...Percent` la phan_tram, `...Points`/
  `...Pips` la diem/pip, `...Money`/`...USD`/`...Dollar` la tien,
  `...Hours` la gio, `...Multiplier`/`...Factor` la ty_le,
  `...Count`/`...Level`/`...Step` (so tang) la so_lan.
  He se TU CHOI anh xa neu don vi khong khop nut - vi du mot input tinh bang
  DIEM khong the la `chot_tien` (nut do tinh bang TIEN), va mot input
  PHAN TRAM khong the la `buoc` (nut do tinh bang pip).

Tra ve DUNG mot JSON:
{{"anh_xa": {{"TenInput": {{"nut": "ten_nut", "don_vi": "pip"}},
             "TenInputKhac": null}}}}"""


def anh_xa_mot(src: str, ten: str = "", model: str = "") -> dict:
    """Mot file -> {nut: (gia_tri, ten_input)} do LLM anh xa THEM.

    Gia tri lay tu chinh khai bao `input` (regex), khong lay tu loi mo hinh.
    """
    from nhan import tri_tue as TT
    ins = QT.doc_input(src)
    if not ins:
        return {}
    da_co = QT.anh_xa(ins)
    r = TT.hoi_json(_nhac(ten, ins, da_co), bo_qua_han_muc=True,
                    dung_cache=False, model=model)
    if isinstance(r, dict) and (r.get("loi") or r.get("bo_qua")):
        return {"_chua_do": str(r.get("loi") or r.get("bo_qua"))[:90]}
    j = (r or {}).get("json") or r or {}
    ax = j.get("anh_xa") or {}
    if not isinstance(ax, dict):
        return {}

    theo_ten = {x["ten"]: x for x in ins}
    ra, bo_don_vi = {}, []
    for ten_in, muc in ax.items():
        if isinstance(muc, dict):
            nut, don_vi = muc.get("nut"), str(muc.get("don_vi") or "").lower()
        else:
            nut, don_vi = muc, ""
        if not nut or nut not in QT.NUT_CHAY_DUOC:
            continue                      # khong duoc tao nut moi
        # CONG DON VI. Khong khai don vi thi van cho qua (ban cu khong hoi), con
        # khai SAI don vi thi tu choi - do la truong hop nguy hiem hon, vi no
        # nghe hop ly va van chay ra so.
        hop = DON_VI_NUT.get(nut)
        if don_vi and hop and don_vi not in hop:
            bo_don_vi.append("%s -> %s (don vi %s, can %s)"
                             % (ten_in[:26], nut, don_vi, "/".join(sorted(hop))))
            continue
        x = theo_ten.get(ten_in)
        if x is None:
            continue                      # khong duoc bia ten input
        v = str(x["mac_dinh"])
        try:
            v = float(v)
        except ValueError:
            if v.lower() in ("true", "false"):
                v = v.lower() == "true"
            else:
                continue
        if nut in ra:
            continue                      # moi nut nhieu nhat mot input
        ra[nut] = (v, x["ten"])
    if bo_don_vi:
        ra["_bo_vi_don_vi"] = bo_don_vi
    return ra


def bo_sung(toi_thieu: int = 2, gioi_han: int = 0, in_ra=print) -> dict:
    """Chay LLM cho cac file lan `quan_tri` bi bang ten doc duoi `toi_thieu` nut.

    Tra {spec moi, so file da them nut}. KHONG ghi vao dau - nguoi goi quyet
    dinh dung lam gi (dap len he nen bang `_thu_quan_tri.py`).
    """
    import concurrent.futures as cf

    from nhan import phan_loai_ma as PL

    ds = []
    for d in PL._doc_kho_ma():
        z = PL.phan_loai_mot(d["src"], d["ten"])
        if not z["quan_tri"] and z["lan"] != PL.QUAN_TRI:
            continue
        ins = QT.doc_input(d["src"])
        if len(QT.anh_xa(ins)) >= toi_thieu:
            continue                      # bang ten da du, khong ton mot luot goi
        if not ins:
            continue
        ds.append(d)
        if gioi_han and len(ds) >= gioi_han:
            break
    in_ra("LLM anh xa bo sung cho %d file (bang ten doc duoc < %d nut)"
          % (len(ds), toi_thieu))
    if not ds:
        return {"so_file": 0, "them": 0, "spec": []}

    def _mot(d):
        try:
            return d["ten"], anh_xa_mot(d["src"], d["ten"])
        except Exception as e:
            return d["ten"], {"_loi": "%s: %s" % (type(e).__name__, str(e)[:60])}

    ket = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        ket = list(ex.map(_mot, ds))

    chua_do = sum(1 for _, r in ket if r.get("_chua_do"))
    if chua_do == len(ket):
        in_ra("  !! CA ME KHONG GOI DUOC: %s"
              % next(r["_chua_do"] for _, r in ket if r.get("_chua_do")))
        return {"so_file": len(ds), "chua_do": chua_do, "them": None, "spec": []}

    theo_ten = {d["ten"]: d for d in ds}
    spec, them = [], 0
    for ten, r in ket:
        nut = {k: v for k, v in r.items() if not k.startswith("_")}
        if len(nut) < toi_thieu:
            continue
        d = theo_ten[ten]
        s = QT.boc_mot(d["src"], ten=ten) or {
            "ten": ten, "ho": "quan_tri_vi_the", "dau_hieu": QT.dau_hieu_cua(d["src"]),
            "so_input": len(QT.doc_input(d["src"])), "nut_van": {}, "input_goc": {}}
        s["nut_van"] = dict(s.get("nut_van") or {},
                            **{k: v[0] for k, v in nut.items()})
        s["input_goc"] = dict(s.get("input_goc") or {},
                              **{k: v[1] for k, v in nut.items()})
        s["_llu_bo_sung"] = sorted(nut)
        spec.append(s)
        them += 1
    in_ra("  %d/%d file duoc bo sung du >= %d nut (chua do: %d)"
          % (them, len(ds), toi_thieu, chua_do))
    return {"so_file": len(ds), "them": them, "chua_do": chua_do, "spec": spec}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    n = 0
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)
    r = bo_sung(gioi_han=n)
    p = Path(__file__).resolve().parent.parent / "reports" / "quan_tri_llm.json"
    p.write_text(json.dumps(r.get("spec") or [], ensure_ascii=False, indent=1),
                 encoding="utf-8")
    print("-> %s" % p)
