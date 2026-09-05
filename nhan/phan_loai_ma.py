# -*- coding: utf-8 -*-
"""phan_loai_ma.py - CHIA KHO MA NGUON THANH BON LAN, TRUOC KHI BOC.

Chu du an 05/09/2026: *"Loc ra chien luoc va tien ich / he thong quan li lenh
=> tich hop vao he thong chinh"*.

## VI SAO CAN, DO DUOC 05/09

Khau boc hom qua bao **70%**. Do lai tren chinh ban tho con luu
(`reports/boc_ma_llm_tho.json` + `config/co_che_dsl.json`): **36 file .mq5 dong
gop 64 co che**, tren 113 file da chay - tuc **32%**, va **9% cua 389 file**.
70% khong phai suat ra co che; no la suat LLM tra ve mot cai gi do.

Mau so that, do bang chinh module nay:

    389 artifact ma
      190  chi_bao     `#property indicator` / `OnCalculate`, khong dat lenh 49%
       82  chien_luoc  dat lenh + co dieu kien vao tinh tu gia                21%
       59  quan_tri    dat lenh nhung khong co dieu kien vao                  15%
       58  tien_ich    khong lenh, khong buffer, khong quan tri               15%

`boc_ma_llm` chi tim `strategy.entry` / `trade.Buy` / `OrderSend`. **190 file chi
bao khong co mot dong nao trong so do** - chung khong dat lenh, chung ve mui ten
vao buffer. Nen chung khong that bai o khau boc: chung chua bao gio duoc dua vao
khau boc, va bi dem nhu file khong ra co che.

Cung the o chieu nguoc lai: `Trade_Manager.mq5`, `ES_Manager.mq5`,
`DailyZoneRecovery.mq5` deu tra "LLM tra ve rong" va bi ghi nhu that bai. Chung
KHONG that bai - chung khong co tin hieu vao de bat dau. Chung la ho 2
(`nhan/quan_tri.py`), va o do chung ra spec dung.

**Mot file khong ra co che vao lenh co the la ba viec khac han nhau:**
bo doc hong · file khong phai chien luoc · file la chien luoc nhung dien dat
kieu khac. Gop ca ba vao mot con so "30% that bai" thi khong sua duoc cai nao.

## KHONG PHAI MOT NHAN, MA HAI CO ROUTING

Mot EA co the vua co tin hieu vao vua co lop quan tri (phan lon EA luoi deu the).
Ep no vao mot nhan la vut mat mot nua. Nen ham nay tra:

    lan       nhan chinh, de BAO CAO va de biet mau so tung duong
    vao_lenh  co gui sang duong 1 (`doc_ma` / `boc_ma_llm`) khong
    quan_tri  co gui sang duong 2 (`quan_tri.boc_kho`) khong

Mot file co the bat CA HAI co. Do la binh thuong, khong phai loi phan loai.

## RANH GIOI

Chi doc van ban bang bieu thuc chinh quy - **khong bao gio chay ma tai ve**
(cung ranh gioi voi `ma_nguon.py`, `doc_ma.py`, `thu_hoi_thanh_phan.py`).
Phan loai theo CAU TRUC ma (ham vao ra, loi goi chi bao, buffer), khong theo
TEN FILE: ten la thu tac gia dat, cau truc la thu trinh bien dich doc.
"""
from __future__ import annotations

import json
import re
from collections import Counter

#: Bon lan. Ten lan la khoa on dinh - bao cao va so deu dung chuoi nay.
CHI_BAO = "chi_bao"
CHIEN_LUOC = "chien_luoc"
QUAN_TRI = "quan_tri"
TIEN_ICH = "tien_ich"

#: Dau hieu CAU TRUC. Moi cai la mot cau hoi tra loi duoc bang regex, khong
#: phai mot phong doan. Ten khoa dung trong `bang_dau_hieu` cua ket qua.
DAU_HIEU = {
    # --- khung chuong trinh ---
    "prop_chi_bao":  r"#property\s+indicator",
    "OnCalculate":   r"\bOnCalculate\s*\(",
    "OnTick":        r"\bOnTick\s*\(",
    "OnStart":       r"\bOnStart\s*\(",
    "OnChartEvent":  r"\bOnChartEvent\s*\(",
    "giao_dien":     r"CAppDialog|CDialog\b|ObjectCreate\s*\(",
    # --- co dat lenh khong ---
    "dat_lenh":      r"OrderSend|PositionOpen|\b\w+\.(Buy|Sell)\s*\(|CTrade\b"
                     r"|ExecuteMarketOrder|PlaceLimitOrder",   # .cs = cTrader
    # --- co tin hieu tinh tu du lieu gia khong ---
    "goi_chi_bao":   r"\bi(RSI|MA|ATR|CCI|ADX|Stochastic|MACD|Bands|Momentum"
                     r"|StdDev|Highest|Lowest|AO|WPR|OBV|Alligator|Envelopes"
                     r"|Force|Fractals|Ichimoku|SAR|DeMarker|BullsPower"
                     r"|BearsPower|Volumes|MFI|RVI|TEMA|FrAMA|AMA|VIDyA)\s*\("
                     r"|iCustom\s*\(|CopyBuffer\s*\(|Indicators\.\w+\s*\(",
    "buffer":        r"SetIndexBuffer\s*\(|\w+Buffer\s*\[\s*\w+\s*\]\s*=",
    # --- lop quan tri vi the ---
    "trailing":      r"(?i)trailing|trail_?stop|TrailingStop",
    "breakeven":     r"(?i)break_?even|move_?to_?be\b",
    "thang_lot":     r"(?i)martingale|lot_?multi|multiplier|lot_?factor"
                     r"|volume_?mult|he_?so_?nhan",
    "luoi":          r"(?i)\bgrid\b|grid_?step|grid_?dist|luoi_?buoc",
    "hedge":         r"(?i)\bhedg\w*|doi_?ung|counter_?trade",
    "dong_ro":       r"(?i)close_?all|closeall|basket|dong_?het|CloseAllPositions",
    "chot_phan":     r"(?i)partial_?close|PositionClosePartial|chot_?phan",
    "phuc_hoi":      r"(?i)recovery|zone_?recover|nap_?bu",
    "quan_ly_lenh":  r"(?i)PositionModify|OrderModify|\bModify\s*\(",
}
_RX = {k: re.compile(v) for k, v in DAU_HIEU.items()}

#: Dau hieu thuoc lop QUAN TRI VI THE. Dem >= `TOI_THIEU_QUAN_TRI` cai thi file
#: duoc gui sang duong 2 - ke ca khi no cung co tin hieu vao.
#:
#: Nguong 2 chu khong phai 1: `PositionModify` mot minh co trong hau het EA
#: (dat SL sau khi vao lenh cung goi no) nen 1 dau hieu khong phan biet duoc gi.
NHOM_QUAN_TRI = ("trailing", "breakeven", "thang_lot", "luoi", "hedge",
                 "dong_ro", "chot_phan", "phuc_hoi")
TOI_THIEU_QUAN_TRI = 2


def dau_hieu_cua(src: str) -> dict:
    """Bang dau hieu cau truc cua MOT file. Chi doc, khong chay."""
    return {k: bool(r.search(src)) for k, r in _RX.items()}


def _co_dieu_kien_vao(src: str) -> bool:
    """Vung quanh lenh vao co dieu kien tinh tu DU LIEU GIA khong?

    Dung chinh bo tim vung cua `doc_ma` - de hai module khong bao gio lech nhau
    ve dinh nghia "vung vao lenh".
    """
    try:
        from nhan import doc_ma as DM
    except Exception:
        return False
    vb = DM._chuan_hoa(src)
    L = vb.splitlines(keepends=True)
    dau, p = [], 0
    for l in L:
        dau.append(p)
        p += len(l)
    for m in DM._VAO_LENH.finditer(vb):
        i = max(k for k, x in enumerate(dau) if x <= m.start())
        vung = "".join(L[max(0, i - 25):i + 2])
        if _RX["goi_chi_bao"].search(vung):
            return True
        # so sanh gia voi mot bien: `if(close[1] > g_level)`.
        if re.search(r"if\s*\(.{0,120}\b(close|open|high|low|bid|ask|Close|Open"
                     r"|High|Low|Bid|Ask)\b.{0,40}[<>]", vung):
            return True
    return False


def phan_loai_mot(src: str, ten: str = "") -> dict:
    """Mot file -> {lan, vao_lenh, quan_tri, bang_dau_hieu, vi_sao}."""
    d = dau_hieu_cua(src)
    so_qt = sum(1 for k in NHOM_QUAN_TRI if d[k])
    co_qt = so_qt >= TOI_THIEU_QUAN_TRI
    la_chi_bao = (d["prop_chi_bao"] or (d["OnCalculate"] and not d["dat_lenh"]))

    if la_chi_bao:
        # Chi bao DINH NGHIA tin hieu (buffer + mui ten) nhung khong dat lenh.
        # No thuoc duong 1, chi la doc bang bo doc khac.
        return {"ten": ten, "lan": CHI_BAO, "vao_lenh": True, "quan_tri": False,
                "so_dau_hieu_quan_tri": so_qt, "bang_dau_hieu": d,
                "vi_sao": "khai bao indicator/OnCalculate, khong dat lenh"}

    if d["dat_lenh"]:
        co_vao = d["goi_chi_bao"] and _co_dieu_kien_vao(src)
        if co_vao:
            return {"ten": ten, "lan": CHIEN_LUOC, "vao_lenh": True,
                    "quan_tri": co_qt, "so_dau_hieu_quan_tri": so_qt,
                    "bang_dau_hieu": d,
                    "vi_sao": "dat lenh + dieu kien vao tinh tu gia"}
        if co_qt:
            return {"ten": ten, "lan": QUAN_TRI, "vao_lenh": False,
                    "quan_tri": True, "so_dau_hieu_quan_tri": so_qt,
                    "bang_dau_hieu": d,
                    "vi_sao": "dat lenh nhung khong co dieu kien vao; %d dau "
                              "hieu quan tri vi the" % so_qt}
        return {"ten": ten, "lan": CHIEN_LUOC, "vao_lenh": True,
                "quan_tri": False, "so_dau_hieu_quan_tri": so_qt,
                "bang_dau_hieu": d,
                "vi_sao": "dat lenh, chua thay dieu kien - van thu duong 1"}

    if co_qt:
        return {"ten": ten, "lan": QUAN_TRI, "vao_lenh": False, "quan_tri": True,
                "so_dau_hieu_quan_tri": so_qt, "bang_dau_hieu": d,
                "vi_sao": "khong dat lenh nhung %d dau hieu quan tri" % so_qt}

    return {"ten": ten, "lan": TIEN_ICH, "vao_lenh": False, "quan_tri": False,
            "so_dau_hieu_quan_tri": so_qt, "bang_dau_hieu": d,
            "vi_sao": "khong dat lenh, khong buffer chi bao, khong quan tri"}


def _doc_kho_ma() -> list[dict]:
    """Doc artifact `code` tu so. Tra [{id, ten, src}]."""
    from nhan import so as SO
    ra = []
    for x in SO.nhieu("SELECT id,payload FROM artifact WHERE artifact_type='code'"):
        try:
            p = json.loads(x["payload"])
        except Exception:
            continue
        con = p.get("payload") or p
        src = con.get("content") or ""
        if not isinstance(src, str) or len(src) < 200:
            continue
        ra.append({"id": x["id"], "src": src,
                   "ten": str(con.get("path") or con.get("ten") or x["id"])})
    return ra


def quet(in_ra=print) -> dict:
    """Phan loai CA KHO. Tra {ds, dem, duong}."""
    ds = []
    for d in _doc_kho_ma():
        z = phan_loai_mot(d["src"], d["ten"])
        z["id"] = d["id"]
        z["so_ky_tu"] = len(d["src"])
        ds.append(z)
    dem = Counter(z["lan"] for z in ds)
    duong = {"vao_lenh": sum(1 for z in ds if z["vao_lenh"]),
             "quan_tri": sum(1 for z in ds if z["quan_tri"]),
             "ca_hai": sum(1 for z in ds if z["vao_lenh"] and z["quan_tri"]),
             "khong_duong": sum(1 for z in ds
                                if not z["vao_lenh"] and not z["quan_tri"])}
    in_ra("PHAN LOAI %d file ma" % len(ds))
    for k, v in dem.most_common():
        in_ra("  %-12s %4d  %4.0f%%" % (k, v, 100 * v / max(len(ds), 1)))
    in_ra("  --- duong ra ---")
    for k, v in duong.items():
        in_ra("  %-12s %4d" % (k, v))
    return {"ds": ds, "dem": dict(dem), "duong": duong}


def bang_suat(in_ra=print) -> dict:
    """SUAT BOC THEO TUNG LAN - de "70%" khong bao gio con mo ho nua.

    Moi lan co MOT dich va MOT mau so. Tron chung lai la cach mot lan 90% va
    mot lan chua chay bao giay nao gop thanh mot con so khong sua duoc gi.

    `None` co nghia CHUA DO, khong co nghia 0. Phan biet nay la bat buoc:
    [[ket-luan-am-phai-phan-biet-chua-do]].
    """
    import json as _json
    from pathlib import Path as _P

    r = quet(in_ra=lambda *a: None)
    lan = {z["ten"]: z["lan"] for z in r["ds"]}
    dem = r["dem"]

    # --- lan chien_luoc: doc ban tho cua `boc_ma_llm` ---
    ra_cl = da_cl = None
    p = _P(__file__).resolve().parent.parent / "reports" / "boc_ma_llm_tho.json"
    if p.exists():
        tho = _json.loads(p.read_text(encoding="utf-8"))
        cl = [k for k in tho if lan.get(k["ten"]) == CHIEN_LUOC]
        da_cl, ra_cl = len(cl), sum(1 for k in cl if k.get("co_che"))

    # --- lan quan_tri: bo boc la tat dinh, chay lai duoc ngay ---
    from nhan import quan_tri as QT
    specs = QT.boc_kho(in_ra=lambda *a: None)
    ten_qt = {s["ten"] for s in specs}
    n_qt = dem.get(QUAN_TRI, 0)
    ra_qt = sum(1 for t, v in lan.items() if v == QUAN_TRI and t in ten_qt)

    # --- lan chi_bao: khoanh vung tat dinh, DICH thi can LLM ---
    from nhan import doc_chi_bao as DC
    n_cb = dem.get(CHI_BAO, 0)
    khoanh = len(DC._ds_chi_bao())
    p2 = _P(__file__).resolve().parent.parent / "reports" / "doc_chi_bao_tho.json"
    ra_cb = None
    if p2.exists():
        tho2 = _json.loads(p2.read_text(encoding="utf-8"))
        if not all(k.get("chua_do") for k in tho2):
            ra_cb = sum(1 for k in tho2 if k.get("co_che"))

    bang = [
        ("chi_bao", n_cb, khoanh, ra_cb, "doc_chi_bao -> LLM"),
        ("chien_luoc", dem.get(CHIEN_LUOC, 0), da_cl, ra_cl, "boc_ma_llm"),
        ("quan_tri", n_qt, n_qt, ra_qt, "quan_tri.boc_kho (tat dinh)"),
        ("tien_ich", dem.get(TIEN_ICH, 0), 0, 0, "bo CO CHU DICH"),
    ]
    in_ra("SUAT BOC THEO LAN  (None = CHUA DO, khong phai 0)")
    in_ra("  %-11s %5s %7s %7s %6s  %s"
          % ("lan", "file", "da thu", "ra", "suat", "duong"))
    for ten, n, thu, ra, duong in bang:
        s = "-" if (ra is None or not thu) else "%.0f%%" % (100 * ra / thu)
        in_ra("  %-11s %5d %7s %7s %6s  %s"
              % (ten, n, "-" if thu is None else thu,
                 "CHUA DO" if ra is None else ra, s, duong))
    return {"bang": bang, "dem": dem}


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    sys.stdout.reconfigure(encoding="utf-8")
    if "--suat" in sys.argv:
        bang_suat()
        raise SystemExit(0)
    r = quet()
    out = Path(__file__).resolve().parent.parent / "reports" / "phan_loai_ma.json"
    out.write_text(json.dumps(
        [{k: v for k, v in z.items() if k != "bang_dau_hieu"} for z in r["ds"]],
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("-> %s" % out)
