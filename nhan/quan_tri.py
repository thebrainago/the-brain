# -*- coding: utf-8 -*-
"""quan_tri.py - BOC CO CHE QUAN TRI VI THE tu ma nguon EA.

Chu du an 05/09/2026: *"Le ra co che hedging cau phai tim ra va boc tach ra
duoc chu, ta thu ca ngan chien luoc ve ma cau chi co dca theo loi thuong co hop
li khong?"*

**Khong hop ly, va day la lo hong CAU TRUC chu khong phai mot lan bo sot.**
Do duoc 05/09:

  - Thu vien co che cua The Brain: **262 co che, 2 cai co dau hieu quan tri vi
    the**. Schema cua spec la `{chieu, co_che, giu, ho, ten, vao, ra, nguon}` -
    **khong co truong nao** cho hedge / thang lot / chot ro / cat hoa.
  - Ho co che: xu_huong 140 · quay_ve_trung_binh 65 · pha_vo 24 · bien_dong 18 ·
    dong_tien 6 · lich 5 · phien 3 · vi_mo 1. **Tat ca deu la ho TIN HIEU VAO.**
  - Kho da thu: 6.658 tai lieu + **389 artifact ma nguon**. Rieng tieu de+tom tat
    da co 61 hedge · 43 luoi · 43 DCA · 34 recovery · 33 martingale · 18 basket.
    **0 cai vao duoc thu vien.**

`nhan/ngu_phap.py` doc file `.mq5`, rut dieu kien vao lenh, roi **nem phan quan
tri vi the di**. Nen moi lan quet 262 co che x 194 ma, he **ve mat cau truc
khong the** tim ra hedging - DSL khong dien dat duoc no.

## MODULE NAY LAM GI

Bo sung **ho co che thu hai**: `quan_tri_vi_the`. No khong sinh tin hieu vao;
no mo ta cach QUAN LY vi the sau khi da vao. Dich chay la `mo_phong_v2.mo_phong`
(da co san trong du an, mo hinh du hedge/cat hoa/chot-dung theo tien).

Bang anh xa ten input -> nut van cua `mo_phong_v2`, dung de "thay so" theo dung
y chu du an: boc `.set`/`input` cua EA that ra thanh mot cau hinh chay duoc.

## BON CO CHE MOI, DO DUOC TU MA THAT (05/09)

  `hedge`        cincinv2.24: `InpEnableHedging` + `InpHedgePips=5` +
                 `InpHedgeLotMultiplier=2.0` - mo lenh NGUOC cach N pip, lot xM.
  `thoat_theo_gio` GridEA: `InpMaxCycleHours=72` - dong ro sau X gio BAT KE lai lo.
                 Day la cach chan duoi HOAN TOAN KHAC voi chan theo tien.
  `cong_bien_dong` GridEA: `InpMinVolatilityRatio`/`InpMaxVolatilityRatio` -
                 chi mo ro moi khi bien dong nam trong dai.
  `nguong_theo_%` cincin/GridEA: chot va dung tinh theo **% so du** chu khong
                 phai $ co dinh -> tu co gian theo tai khoan.
"""
from __future__ import annotations

import json
import re

#: Ten input -> nut van cua `mo_phong_v2.mo_phong`. Khoa la regex tren TEN input
#: (khong phan biet hoa thuong), gia tri la (ten_nut, he_so_quy_doi, ghi_chu).
ANH_XA = {
    r"grid.?spacing|gridstep|distance.?martingale|step.?pip|khoangcach":
        ("buoc", 1.0, "khoang cach giua cac tang (pip hoac point - phai kiem)"),
    r"take.?profit.*(pip)|tp.?pip":
        ("tp", 1.0, "TP tu gia trung binh, pip"),
    r"lot.?multiplier|hesonhan|multiplier.*lot|martingale.?mult":
        ("he_so_1", 1.0, "he so nhan lot moi tang"),
    r"grid.?levels|max.?trades.*series|maxlenh|max.?orders|tang.?toi.?da":
        ("tang_toi_da", 1, "tran so tang moi ro"),
    r"base.?lot|lot.?size|lot.?batdau|inplotsize":
        ("_lot_goc", 1.0, "lot tang dau"),
    r"profit.?target.*(dollar|usd)|target.?exit.?all|tpall.?money|takeprofittargetusd":
        ("chot_tien", 1.0, "chot ca ro khi lai noi >= X tien"),
    r"loss.?limit|max.?cutloss.?all|stoploss.*money|dunglo":
        ("dung_lo", 1.0, "dong sach khi lo noi >= X tien"),
    r"solenh.?kichhoat|position.?threshold|cat.?hoa":
        ("cat_hoa_tu", 1, "chi tia lenh khi ro co >= N lenh"),
    r"hedge.?pip|hedge.?distance":
        ("hedge_tu", 1.0, "mo lenh nguoc khi lo >= N pip"),
    r"hedge.?lot.?multiplier|hedge.?ratio":
        ("hedge_ty", 1.0, "ty le lot cua lenh hedge"),
    r"max.?cycle.?hours|max.?hold.?hours|time.?exit":
        ("thoat_theo_gio", 1.0, "dong ro sau X gio BAT KE lai lo - CO CHE MOI"),
    r"min.?volatility.?ratio":
        ("vol_min", 1.0, "chi mo ro khi bien dong >= nguong - CO CHE MOI"),
    r"max.?volatility.?ratio":
        ("vol_max", 1.0, "chi mo ro khi bien dong <= nguong - CO CHE MOI"),
    r"khoangcachbuysell|buy.?sell.?distance":
        ("kc_bs", 1.0, "Buy va Sell mo cach nhau bao nhieu"),
}

#: Dau hieu de nhan mot file la CO quan tri vi the (khong phai chi tin hieu).
DAU_HIEU = {
    "hedge": r"\bhedge|Hedge",
    "recovery": r"[Rr]ecovery",
    "martingale": r"[Mm]artingale",
    "luoi": r"[Gg]rid[SsPpLl]|GridStep|gridDistance",
    "tia_lenh": r"PositionClosePartial|[Pp]artialClose|CatHoa",
    "chot_ro": r"CloseAll|closeAll|Target_Exit|tpAll",
    "lenh_cho": r"ORDER_TYPE_(BUY|SELL)_(STOP|LIMIT)",
    "thang_lot": r"[Ll]ot\s*\*=|LotMultiplier|HesoNhan",
}

_RX_INPUT = re.compile(
    r"^\s*(?:input|sinput|extern)\s+(\w+)\s+(\w+)\s*=\s*([^;/]+)", re.M)


def doc_input(src: str) -> list[dict]:
    """Moi khai bao `input` trong ma nguon MQL -> {kieu, ten, mac_dinh}."""
    ra = []
    for kieu, ten, gt in _RX_INPUT.findall(src or ""):
        ra.append({"kieu": kieu, "ten": ten, "mac_dinh": gt.strip().strip('"')})
    return ra


def dau_hieu_cua(src: str) -> list[str]:
    """Co che quan tri vi the nao xuat hien trong ma nguon."""
    return [k for k, pat in DAU_HIEU.items() if re.search(pat, src or "")]


def anh_xa(ins: list[dict]) -> dict:
    """input -> nut van cua `mo_phong_v2`. Tra {nut: (gia_tri, ten_input_goc)}."""
    ra = {}
    for x in ins:
        for pat, (nut, he_so, _gc) in ANH_XA.items():
            if re.search(pat, x["ten"], re.I):
                v = x["mac_dinh"]
                try:
                    v = float(v)
                except ValueError:
                    if v.lower() in ("true", "false"):
                        v = v.lower() == "true"
                    else:
                        continue
                if nut not in ra:          # input dau tien khop thi giu
                    ra[nut] = (v * he_so if isinstance(v, float) else v, x["ten"])
                break
    return ra


def boc_mot(src: str, ten: str = "") -> dict | None:
    """Mot file ma nguon -> mot spec `quan_tri_vi_the`, hoac None neu khong co.

    Nguong: phai co it nhat HAI dau hieu. Mot dau hieu don le (vi du chi
    `CloseAll`) co o gan nhu moi EA va khong noi len gi.
    """
    dh = dau_hieu_cua(src)
    if len(dh) < 2:
        return None
    ins = doc_input(src)
    nut = anh_xa(ins)
    if not nut:
        return None
    return {
        "ten": ten, "ho": "quan_tri_vi_the",
        "dau_hieu": dh, "so_input": len(ins),
        "nut_van": {k: v[0] for k, v in nut.items()},
        "input_goc": {k: v[1] for k, v in nut.items()},
    }


def boc_kho(gioi_han: int = 0, in_ra=print) -> list[dict]:
    """Quet toan bo artifact `code` trong so, tra ve cac spec quan tri vi the."""
    from nhan import so as SO
    r = SO.nhieu("SELECT id,payload FROM artifact WHERE artifact_type='code'")
    ra = []
    for x in r:
        try:
            p = json.loads(x["payload"])
        except Exception:
            continue
        con = p.get("payload") or p
        src = con.get("content") or ""
        if not isinstance(src, str) or len(src) < 200:
            continue
        ten = con.get("ten") or con.get("path") or ("artifact#%s" % x["id"])
        s = boc_mot(src, ten=str(ten))
        if s:
            s["artifact_id"] = x["id"]
            ra.append(s)
        if gioi_han and len(ra) >= gioi_han:
            break
    in_ra("boc duoc %d co che quan tri vi the tu %d artifact ma" % (len(ra), len(r)))
    return ra
