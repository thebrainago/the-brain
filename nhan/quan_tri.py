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
#: Ten input -> nut van cua `mo_phong_v2.mo_phong`.
#:
#: BAN 2 (05/09, sau khi DO pheu): ban 1 chi co 14 mau va 93% file chet o buoc
#: "duoi 2 dau hieu". Ban nay viet tu TU VUNG THAT do duoc tren 5.964 input cua
#: 353 file: trailing(87) · step(70) · multiplier(58) · level(53) · target(45) ·
#: trail(41) · distance(38) · grid(32) · zone(32) · drawdown(28) · martingale(24) ·
#: recovery(22) · partial(20) · breakeven(19) · hedge(17) · equity(15).
#:
#: `mo_phong_v2` CHUA co nut cho `trailing` va `breakeven` - van boc ra va danh
#: dau `_chua_mo_phong` de biet dang bo lo gi, khong im lang bo di.
ANH_XA = {
    # --- khoang cach / buoc luoi ---
    r"grid.?(spacing|step|dist)|gridsize|step.?(pip|point)|distance.?(pip|point|martingale|grid)"
    r"|khoangcach|spacing|pip.?step|point.?step|zone.?(size|width|dist)":
        ("buoc", 1.0, "khoang cach giua cac tang"),
    r"buy.?sell.?dist|khoangcachbuysell|hedge.?dist|entry.?gap":
        ("kc_bs", 1.0, "Buy va Sell mo cach nhau"),
    # --- chot lai ---
    r"^(inp)?take.?profit|(^|_)tp(_|$)|tp.?(pip|point)|takeprofit.?(pip|point)|profit.?pip":
        ("tp", 1.0, "TP tu gia trung binh, pip"),
    r"profit.?target.*(dollar|usd|money|cash)|target.?exit.?all|tpall|close.?all.?profit"
    r"|takeprofittargetusd|basket.?(tp|profit)|total.?profit.?target":
        ("chot_tien", 1.0, "chot ca ro khi lai noi >= X tien"),
    # --- dung lo toan cuc ---
    r"loss.?limit|max.?cutloss|cutloss.?all|stop.?loss.*(money|usd|dollar|all)"
    r"|dunglo|basket.?(sl|loss)|max.?(daily.?)?loss|equity.?stop|drawdown.?(stop|limit|max)":
        ("dung_lo", 1.0, "dong sach khi lo noi >= X tien"),
    # --- thang lot ---
    r"lot.?(multiplier|mult|factor|coef)|(martingale|grid|dca).?(mult|factor)"
    r"|hesonhan|multiplier(?!.*hedge)|lot.?exponent|volume.?mult":
        ("he_so_1", 1.0, "he so nhan lot moi tang"),
    r"(base|start|first|initial).?lot|lot.?(size|batdau|start)|inplotsize|fixed.?lot":
        ("_lot_goc", 1.0, "lot tang dau"),
    # --- tran ---
    r"grid.?levels|max.?(trades|orders|positions|lenh|level|grid)|maxlenh"
    r"|tang.?toi.?da|series.?(max|size)|max.?trades.*series|depth":
        ("tang_toi_da", 1, "tran so tang moi ro"),
    r"max.?lot|lot.?(max|toi.?da|limit)|volume.?limit":
        ("_lot_toi_da", 1.0, "tran tong lot mot ro"),
    # --- tia lenh ---
    r"solenh.?kichhoat|position.?threshold|cat.?hoa|partial.?(close|tp|level)"
    r"|close.?partial|pair.?close|hedge.?pair":
        ("cat_hoa_tu", 1, "chi tia lenh khi ro co >= N lenh"),
    # --- hedge / khoa lo ---
    r"hedge.?(pip|point|dist|level|after|trigger|start)|lock.?(pip|after|level)|khoa.?lo":
        ("hedge_tu", 1.0, "mo lenh nguoc khi ro ket toi N"),
    r"hedge.?(lot.?)?(mult|ratio|factor|size|coef)|lock.?(ratio|lot)|cover.?ratio":
        ("hedge_ty", 1.0, "ty le lot cua lenh hedge"),
    # --- thoat theo thoi gian ---
    r"max.?(cycle|hold|trade).?(hour|time|bar|day)|time.?(exit|limit|stop)"
    r"|close.?after.?(hour|bar|day)|expiry.?(hour|bar)":
        ("thoat_theo_gio", 1.0, "dong ro sau X gio bat ke lai lo"),
    # --- cong bien dong ---
    r"min.?(volatility|vol|atr).?(ratio|filter|thresh)":
        ("vol_min", 1.0, "chi mo ro khi bien dong >= nguong"),
    r"max.?(volatility|vol|atr).?(ratio|filter|thresh)":
        ("vol_max", 1.0, "chi mo ro khi bien dong <= nguong"),
    # --- CHUA MO PHONG DUOC, van boc de biet dang bo lo gi ---
    r"trail(ing)?.?(start|after|trigger|activate)|start.?trail":
        ("trailing_tu", 1.0, "bat trailing sau bao nhieu pip"),
    r"trail(ing)?.?(step|dist|gap|stop|pip|point)":
        ("trailing_buoc", 1.0, "buoc trailing"),
    r"break.?even.?(pip|point|after|trigger|dist)|be.?(trigger|pip)":
        ("breakeven_tu", 1.0, "dua SL ve hoa von sau N pip"),
    r"risk.?(percent|pct)|percent.?risk|risk.?per.?trade":
        ("_risk_pct", 1.0, "CHUA MO PHONG: lot theo % rui ro"),
}

#: Nut MA `mo_phong_v2` chay duoc. Nut bat dau bang `_` la boc duoc nhung chua
#: mo phong - dem rieng de biet do lon cua phan dang bo lo.
NUT_CHAY_DUOC = {"buoc", "kc_bs", "tp", "chot_tien", "dung_lo", "he_so_1",
                 "tang_toi_da", "cat_hoa_tu", "hedge_tu", "hedge_ty",
                 "thoat_theo_gio", "vol_min", "vol_max",
                 # them 05/09 sau khi cai vao `mo_phong_v2`. Truoc do 35/86 file
                 # tien ich bi gat chi vi thieu ba nut nay - khong phai vi rong.
                 "trailing_tu", "trailing_buoc", "breakeven_tu"}

#: Dau hieu de nhan mot file la CO quan tri vi the. BAN 2 - mo rong theo tu
#: vung do duoc, va them tieng Viet (kho co ma nguon cua nguoi Viet).
DAU_HIEU = {
    "hedge": r"hedge|Hedge|khoa.?lo|lock.?(position|profit)|cover.?position",
    "recovery": r"[Rr]ecovery|go.?lenh|zone.?recovery|smart.?recover",
    "martingale": r"[Mm]artingale|nhan.?lot|lot.*\*=|LotMultiplier|lot.?factor",
    "luoi": r"[Gg]rid|GridStep|gridDistance|luoi|zone.?(grid|trade)",
    "tia_lenh": r"PositionClosePartial|[Pp]artial[Cc]lose|CatHoa|cat.?hoa|partial.?(tp|exit)",
    "chot_ro": r"CloseAll|closeAll|Target_Exit|tpAll|basket.?(close|profit)|total.?profit",
    "lenh_cho": r"ORDER_TYPE_(BUY|SELL)_(STOP|LIMIT)",
    "thang_lot": r"[Ll]ot\s*\*=|LotMultiplier|HesoNhan|lot.?\*\s*[A-Za-z_]",
    "trailing": r"[Tt]railing|TrailStop|trail.?(stop|step)",
    "breakeven": r"[Bb]reak.?[Ee]ven|BreakEven|hoa.?von",
    "dca": r"DCA|averaging|average.?down|scale.?in|pyramid|add.?position|nhoi",
    "chan_von": r"[Dd]rawdown|equity.?(stop|guard|protect)|max.?loss|MaxDD",
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
    ins = doc_input(src)
    nut = anh_xa(ins)
    if not nut:
        return None
    chay = {k for k in nut if k in NUT_CHAY_DUOC}
    # Bang chung la NUT ANH XA DUOC, khong phai so tu khoa. Mot file chi co
    # `trailing` co DUNG mot dau hieu nhung neu no khai ca `TrailingStart` lan
    # `TrailingStep` thi no CO trailing that. Nguong cu (>=2 dau hieu) gat het
    # lop nay - ma do lai la lop manh nhat: 23/35 co che giu duoc co
    # `trailing_buoc` (do 05/09).
    if len(dh) < 2 and len(chay) < 2:
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


# ------------------------------------------------------- BUOC LOC CO CHE
#: Chu du an 05/09: *"Co che can phai co buoc loc de chon ra hoac giu lai. Vdu
#: co che quan tri vi the hedge kia toi nghi se dung di dung lai va ket hop
#: duoc voi rat nhieu he thong"*.
#:
#: Nen bo loc o day KHONG hoi "co che nay co lai khong" - do la viec cua
#: `cham_diem`. No hoi: **co che nay co DUNG LAI DUOC khong**. Bon dieu kien:
#:
#:   1. CHAY DUOC   - anh xa duoc >= 2 nut van cua `mo_phong_v2`. Mot cai chi
#:                    boc ra `lot_goc` thi khong mo phong duoc gi.
#:   2. KHONG TRUNG  - da co cai khac cung bo nut van va cung gia tri thi giu
#:                    mot. 389 file EA co rat nhieu ban sao doi ten.
#:   3. CO THAM SO   - it nhat mot nut van la SO (khong phai bool). Co che
#:                    khong co so thi khong "thay so, dieu chinh he so" duoc.
#:   4. GHEP DUOC    - co it nhat mot nut thuoc nhom QUAN TRI (hedge/tia/chot/
#:                    dung), tuc dung duoc CHUNG voi bat ky tin hieu vao nao.
#:                    Day la tieu chi quan trong nhat: no chon ra dung lop
#:                    "dung di dung lai" ma chu du an noi.
NUT_QUAN_TRI = {"hedge_tu", "hedge_ty", "cat_hoa_tu", "chot_tien", "dung_lo",
                "thoat_theo_gio", "vol_min", "vol_max", "kc_bs",
                "trailing_tu", "trailing_buoc", "breakeven_tu"}
NUT_LUOI = {"buoc", "tp", "he_so_1", "tang_toi_da"}


def loc(specs: list[dict], in_ra=print) -> tuple[list[dict], dict]:
    """Loc cac spec quan tri vi the. Tra (giu_lai, thong_ke_vi_sao_loai)."""
    bo = {"it_nut_van": 0, "khong_tham_so": 0, "trung": 0, "khong_ghep_duoc": 0}
    thay = {}
    giu = []
    for s in sorted(specs, key=lambda z: -len(z.get("nut_van") or {})):
        nut = s.get("nut_van") or {}
        if len(nut) < 2:
            bo["it_nut_van"] += 1
            continue
        if not any(isinstance(v, (int, float)) and not isinstance(v, bool)
                   for v in nut.values()):
            bo["khong_tham_so"] += 1
            continue
        khoa = tuple(sorted((k, round(float(v), 6))
                            for k, v in nut.items()
                            if isinstance(v, (int, float))
                            and not isinstance(v, bool)))
        if khoa in thay:
            bo["trung"] += 1
            continue
        if not (set(nut) & NUT_QUAN_TRI):
            bo["khong_ghep_duoc"] += 1
            continue
        thay[khoa] = s["ten"]
        s["ghep_duoc_voi_moi_he"] = True
        s["nut_quan_tri"] = sorted(set(nut) & NUT_QUAN_TRI)
        s["nut_luoi"] = sorted(set(nut) & NUT_LUOI)
        giu.append(s)
    in_ra("giu %d/%d co che | loai: %s"
          % (len(giu), len(specs), ", ".join("%s %d" % kv for kv in bo.items())))
    return giu, bo


def kho_ghep(specs: list[dict]) -> dict:
    """Gom cac GIA TRI THAT cua tung nut van tu moi EA da boc.

    Day la thu de "thay so": thay vi tu bia dai quet, dung dai ma cac EA THAT
    dang chay. Tra {nut: [gia tri da thay, da sap xep, bo trung]}.
    """
    ra: dict[str, list] = {}
    for s in specs:
        for k, v in (s.get("nut_van") or {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                ra.setdefault(k, []).append(float(v))
    return {k: sorted(set(v)) for k, v in sorted(ra.items())}
