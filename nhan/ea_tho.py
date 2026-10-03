# -*- coding: utf-8 -*-
"""ea_tho - LAN EA THO: EA cong khai (MQL5 Code Base / Market / Myfxbook...) chay THANG tren MT5 tester,
cham bang tieu chi chu du an, tren doan du lieu DONG BANG, ghi so tay nghien cuu.

## Vi sao co lan nay (03/10/2026 - ra soat kien truc)

Chu du an: *"tren mql5 va myfxbook co nhieu link cong khai da co hieu qua, ta dua vao nhung chien luoc do
boc tach logic => tao thanh chien luoc => backtest roi tinh chinh"*. So do `hethong.txt` dong 38/55/60:
"dung truc tiep file EA", "backtest cac file co san truoc", "moi thu phai test tren phan mem trade".

Duong chinh cua nc lai di NGUOC: co che -> DSL -> engine Python -> niem phong -> xuat .mq5 ra tester CUOI CUNG.
Do that 03/10 tren 12 EA that cua MQL5 Code Base (`reports/ea/kho.json`): bo boc bang regex ra 5 co che tu
12 EA, vi (a) 5/12 KHONG phai chien luoc (cong cu: replay, dong ro, dong ho, giam sat spread, bang tay),
(b) cac EA that giu logic CO TRANG THAI (khoang gia dau phien, co theo ngay, dem vi the, lenh cho) ma DSL
vao-theo-dong-bar khong dien duoc. Lan EA da duoc xay tu 01/09 (`ea_tu_dong.py`: tai -> bien dich -> .set/.ini
-> tester Model=4) nhung mo coi: khong biet EA nao la chien luoc, khong biet chay tren ma/khung nao (mot lan
chay cu dat EA co phieu AAPL len EURUSD), khong doc bao cao thanh so, khong co doan/niem phong.

Module nay ra QUYET DINH bang code thuan (khong cham MT5 nen test duoc tren Linux):
  * `phan_loai`    EA co phai chien luoc khong (do ham nao goi duoc tu OnTick), ho, phu thuoc ngoai
  * `chon_ma_khung` ma/khung de thu (bang chung tu tieu de, input, chuoi trong ma; thieu thi mac dinh co ghi ro)
  * `de_xuat_tham_so` luoi nho quanh MAC DINH cua tac gia (moi diem la mot phep thu duoc dem)
  * `ke_hoach`     cua so ngay cua kham_pha / xac_nhan / niem_phong tu `so_cai/doan.json` + 1 ngay cach ly
  * `lap_lenh` / `nhan_ket_qua`   lenh tester + cong: CO LAI sau phi VA maxDD < 80% (`cham_diem.TRAN_SUT_GIAM`)
  * `chay` `quet` `tinh`   bo ba cong cu (`nc_cong_cu`): chay mot, quet kho, tinh chinh quanh mac dinh

Chay tester that CHI o may nha (`_chay_that`, qua `slot_tester` + `ea_tu_dong`); o day no la mot ham thay duoc
(`CHAY_TESTER`) de test bang bao cao tong hop.

## Ky luat (giong `nc_thi_nghiem`, khong noi long vi chay bang EA)

  * kham_pha / xac_nhan: ket qua cung van tay tra lai tu so tay, khong tinh them phep thu.
  * niem_phong: MOT lan cho mot bo (EA, ma, khung, tham so, von, model); toi da 3 lan / dong gia thuyet;
    can gia thuyet; can mot xac_nhan DAT dung bo tham so do (CAM KET don bay = chinh bo tham so, gom lot);
    >= 20 lenh; chi phi phai DO (Model=4 va chat luong lich su >= 90%); cua so trong bao cao phai TRUNG cua so
    cua lenh. Hong ha tang (khong doc duoc bao cao, tester chet) KHONG tieu mot lan mo; doc duoc ma it lenh thi CO.
  * DAT = co lai sau phi VA maxDD < 80%: "canh bac co ky vong duong do duoc", chua phai chan ly.

## CHUA kiem voi may that (phai hieu chuan o nha truoc khi tin DAT)

  1. tester co tinh/dong lenh con MO luc het cua so khong (lai dong vs equity) - `da_hieu_chuan_lenh_mo`;
  2. nhan bao cao tieng Viet ngoai 8 nhan da biet (xem `bao_cao_mt5`), nhan `Period` / `History Quality`;
  3. do sau tick that cua XM demo (`tick_tu`) - cua so nao duoc chay Model=4;
  4. `_chay_that` (slot + bien dich + log agent) chua chay lan nao.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from nhan import bao_cao_mt5 as BC
from nhan import cham_diem as CD
from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN

LAB = Path(__file__).resolve().parent.parent
KHO_JSON = LAB / "reports" / "ea" / "kho.json"
NGAY_TOI_THIEU = 30                       # cua so ngan hon: it lenh, noi suy vo nghia
DD_TRAN = float(CD.TRAN_SUT_GIAM)         # % - MOT nguon cho moi cong
PF_NGHI_NHIN_TRUOC = 4.0
KHUNG_HOP_LE = ("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1")
MA_MAC_DINH = ("EURUSD", "XAUUSD")        # khi EA khong cho bang chung gi ve tai san

#: Cau hinh mac dinh; `config/ea_tho.json` (neu co) de len. Khong ghim duong dan nao o day.
MAC_DINH = {
    "model": 4,                           # tick that: chi phi DO duoc (xem chay_tester_z5, bay Model=1)
    "von": 10000,
    "don_bay": 100,
    "han_giay": 1800,
    "chat_luong_toi_thieu_pct": 90.0,
    "tick_tu": None,                      # "YYYY-MM-DD": ngay som nhat co tick that tren tester
    "hau_to_symbol": "",                  # vd "m": ten san = ma nghien cuu + hau to
    "ban_do_symbol": {},                  # ma nghien cuu -> ten san: {"XM_US500CASH": "US500Cash"} (thang hau to)
    "da_hieu_chuan_lenh_mo": False,
    "nhan_them": {},                      # nhan bao cao ban ngu chua co mau: {"so_lenh": "..."}
    "tu_nap": True,                       # chua co doan dong bang thi nap du lieu de dong bang
}

#: Ham de thay khi test / o may khong co MT5: f(lenh, ea, cfg) -> {xong, bao_cao, log, giay, loi}
CHAY_TESTER = None


def cau_hinh() -> dict:
    cfg = dict(MAC_DINH)
    f = Path(os.environ.get("EA_THO_CFG") or (LAB / "config" / "ea_tho.json"))
    try:
        cu = json.loads(f.read_text(encoding="utf-8-sig"))
        if isinstance(cu, dict):
            cfg.update({k: v for k, v in cu.items() if k in MAC_DINH})
    except (OSError, ValueError):
        pass
    return cfg


# ============================================================ 1. PHAN TICH MA NGUON
_LEX = re.compile(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|//[^\n]*|/\*.*?\*/', re.S)
_VAO = re.compile(r"\bOrderSend(?:Async)?\s*\(|\.\s*(?:Buy|Sell|BuyStop|SellStop|BuyLimit|SellLimit|"
                  r"PositionOpen|OrderOpen)\s*\(")
_DINH_NGHIA = re.compile(r"\b([A-Za-z_]\w*)\s*\(((?:[^;{}()]|\([^;{}()]*\))*)\)\s*(?:const\s*)?\{")
_GOI = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_TU_KHOA = frozenset(("if", "for", "while", "switch", "catch", "return", "else", "sizeof", "do", "case"))
GOC_TU_DONG = ("OnInit", "OnTick", "OnTimer", "OnTrade", "OnTradeTransaction", "OnBookEvent", "OnStart")
GOC_GIAO_DIEN = ("OnChartEvent",)


def sach(ma_nguon: str) -> str:
    """Bo chu thich; noi dung chuoi/ky tu -> '""'. De 'Buy(' trong loi chu thich khong bi dem la lenh."""
    return _LEX.sub(lambda m: '""' if m.group(0)[0] in "\"'" else " ", ma_nguon or "")


def _than(code: str, i_mo: int) -> str:
    d = 0
    for j in range(i_mo, len(code)):
        c = code[j]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return code[i_mo + 1:j]
    return code[i_mo + 1:]


def cac_ham(code: str) -> dict:
    """ten ham -> than (cung ten thi gop: OnTick toan cuc + phuong thuc OnTick cua lop)."""
    ham: dict = {}
    for m in _DINH_NGHIA.finditer(code):
        if m.group(1) in _TU_KHOA:
            continue
        ham[m.group(1)] = ham.get(m.group(1), "") + "\n" + _than(code, m.end() - 1)
    return ham


def phan_tich_vao_lenh(code: str) -> dict:
    """Lenh VAO nam o ham nao, ham do co goi duoc tu OnTick/OnTimer/... (tu dong) hay chi tu OnChartEvent (nut)."""
    ham = cac_ham(code)
    co_vao = {n for n, b in ham.items() if _VAO.search(b)}
    goi = {n: {c for c in set(_GOI.findall(b)) if c in ham and c != n} for n, b in ham.items()}

    def _tu(goc) -> set:
        thay, hang = set(), [g for g in goc if g in ham]
        while hang:
            n = hang.pop()
            if n not in thay:
                thay.add(n)
                hang.extend(goi.get(n, ()))
        return thay

    return {"so_ham": len(ham), "ham_co_vao": sorted(co_vao),
            "vao_tu_dong": bool(co_vao & _tu(GOC_TU_DONG)),
            "vao_chi_qua_nut": bool(co_vao & _tu(GOC_GIAO_DIEN)) and not (co_vao & _tu(GOC_TU_DONG)),
            "co_vao_ngoai_ham": bool(_VAO.search(code)) and not co_vao}


def can_tep(ma_nguon: str, code: str) -> dict:
    """Tep/dich vu ngoai ma EA can: thieu thi bien dich hong hoac tester khong vao lenh."""
    return {
        "include_cuc_bo": re.findall(r'^[ \t]*#include[ \t]+"([^"]+)"', ma_nguon, re.M),
        "icustom": sorted(set(re.findall(r'\biCustom\s*\([^;"]*"([^"]+)"', ma_nguon))),
        "tester_indicator": re.findall(r'#property[ \t]+tester_indicator[ \t]+"([^"]+)"', ma_nguon),
        "resource": re.findall(r'^[ \t]*#resource[ \t]+"([^"]+)"', ma_nguon, re.M),
        "dll": re.findall(r'^[ \t]*#import[ \t]+"([^"]+\.dll)"', ma_nguon, re.M | re.I),
        "web_hoac_socket": bool(re.search(r"\b(WebRequest|SocketCreate|SocketConnect)\s*\(", code)),
        "onnx": bool(re.search(r"\bOnnx\w*\s*\(", code)),
    }


_HO_TU_KHOA = {
    "luoi_hoi_phuc": ("martingale", "recovery", "grid", "average", "hedge", "basket", "multiplier",
                      "lotmult", "dca"),
    "phien_pha_vo": ("openingrange", "opening_range", "orb", "sessionstart", "session_start",
                     "rangestart", "breakout"),
}
_CHI_BAO = re.compile(r"\bi(MA|RSI|MACD|Bands|ATR|Stochastic|CCI|ADX|Ichimoku|SAR|Momentum|WPR|"
                      r"Envelopes|AMA|DEMA|TEMA|Custom)\s*\(")


def ho_goi_y(code: str) -> dict:
    """Ho goi y theo TEN dinh danh (>= 2 tu khoa khac nhau). Chi la nhan de AI doc, khong cong."""
    dinh_danh = set(re.findall(r"[A-Za-z_]\w*", code.lower()))
    ra: dict = {}
    for ho, tk in _HO_TU_KHOA.items():
        n = sum(1 for k in tk if any(k in t for t in dinh_danh))
        if n >= 2:
            ra[ho] = n
    chi_bao = sorted(set(_CHI_BAO.findall(code)))
    if chi_bao:
        ra["chi_bao_chuan"] = chi_bao
    return ra


_INPUT_SO = re.compile(r"\b(?:extern|input|sinput)[ \t]+(int|uint|long|ulong|short|ushort|char|uchar|"
                       r"double|float)[ \t]+([A-Za-z_]\w*)[ \t]*=[ \t]*([-+]?\d+(?:\.\d+)?)[ \t]*;")


def input_so(ma_nguon: str) -> list[dict]:
    """Input SO kem KIEU (int/double): .set can ghi dung kieu, `doc_ma.rut_input` khong giu kieu.
    Doc tren ma da bo chu thich (dong input bi comment khong tinh)."""
    ra = []
    for kieu, ten, gt in _INPUT_SO.findall(sach(ma_nguon)):
        thap_phan = kieu in ("double", "float")
        ra.append({"ten": ten, "kieu": "double" if thap_phan else "int",
                   "mac_dinh": float(gt) if thap_phan else int(float(gt))})
    return ra


def phan_loai(ma_nguon: str, tieu_de: str = "", mo_ta: str = "") -> dict:
    """EA co phai CHIEN LUOC (tu vao lenh) khong. Do 12 EA that: 5 la cong cu, khong co lenh vao tu dong."""
    code = sach(ma_nguon)
    v = phan_tich_vao_lenh(code)
    ly_do: list[str] = []
    if v["vao_tu_dong"]:
        loai = "CHIEN_LUOC"
        ly_do.append("co lenh vao goi duoc tu OnTick/OnTimer/OnTrade: %s" % ", ".join(v["ham_co_vao"][:4]))
    elif v["co_vao_ngoai_ham"] or (v["so_ham"] == 0 and _VAO.search(code)):
        loai = "KHONG_RO"
        ly_do.append("co lenh vao nhung bo phan tich ham khong dinh vi duoc - doc tay")
    elif v["ham_co_vao"]:
        loai = "TIEN_ICH"
        ly_do.append("lenh vao chi nam trong ham khong goi tu OnTick/OnTimer (nut bam / su kien giao dien): %s"
                     % ", ".join(v["ham_co_vao"][:4]))
    else:
        loai = "TIEN_ICH"
        ly_do.append("khong co lenh vao (OrderSend / CTrade.Buy|Sell...) - dong lenh, bang dieu khien hoac do dac")
    tep = can_tep(ma_nguon, code)
    if tep["web_hoac_socket"]:
        ly_do.append("co WebRequest/Socket: tester chan - EA co the khong vao lenh trong tester")
    for k in ("include_cuc_bo", "icustom", "tester_indicator", "resource", "dll"):
        if tep[k]:
            ly_do.append("can %s: %s" % (k, ", ".join(tep[k][:4])))
    ra = {"loai": loai, "ly_do": ly_do, "vao": v, "can_tep": tep, "ho": ho_goi_y(code),
          "input_so": input_so(ma_nguon), "dai_ky_tu": len(ma_nguon or "")}
    ra["khung_goi_y"] = khung_goi_y(ma_nguon, tieu_de, mo_ta)
    return ra


# ============================================================ 2. MA / KHUNG
_TIEN = frozenset("USD EUR GBP JPY AUD CAD CHF NZD SEK NOK DKK PLN CZK HUF ZAR MXN TRY SGD HKD CNH".split())
_BIEU_DANH = (
    ("xauusd", "XAUUSD"), ("gold", "XAUUSD"), ("xau", "XAUUSD"), ("xagusd", "XAGUSD"), ("silver", "XAGUSD"),
    ("us100", "US100"), ("nas100", "US100"), ("nasdaq", "US100"), ("ustec", "US100"),
    ("us30", "US30"), ("djia", "US30"), ("dow jones", "US30"),
    ("us500", "US500"), ("sp500", "US500"), ("spx500", "US500"), ("s&p 500", "US500"),
    ("de40", "DE40"), ("ger40", "DE40"), ("dax", "DE40"),
    ("btcusd", "BTCUSD"), ("bitcoin", "BTCUSD"), ("usoil", "USOIL"), ("wti", "USOIL"), ("crude", "USOIL"),
)


def _ma_trong_van_ban(van: str) -> list[tuple[str, str]]:
    """[(ma chuan, bang chung)] theo thu tu xuat hien trong van ban."""
    thay: list[tuple[int, str, str]] = []
    thap = van.lower()
    for cum, ma in _BIEU_DANH:
        m = re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(cum), thap)
        if m:
            thay.append((m.start(), ma, cum))
    for m in re.finditer(r"(?<![A-Za-z])([A-Za-z]{3})([A-Za-z]{3})(?![A-Za-z])", van):
        a, b = m.group(1).upper(), m.group(2).upper()
        if a in _TIEN and b in _TIEN and a != b:
            thay.append((m.start(), a + b, m.group(0)))
    thay.sort()
    return [(ma, bc) for _, ma, bc in thay]


_CFD_TIEU_DE = re.compile(r"(?<![A-Za-z0-9])([A-Z]{1,5})\s+(?:cfd|stock|share|equity)s?(?![A-Za-z])", re.I)


def _co_phieu_trong_tieu_de(van: str) -> list[tuple[str, str]]:
    """'AAPL cfd - ORB strategy' -> [('AAPL', 'AAPL cfd')]. Chi nhan khi chu HOA hoan toan (tranh 'Gold cfd')."""
    ra = []
    for m in _CFD_TIEU_DE.finditer(van or ""):
        if m.group(1).isupper() and m.group(1) not in _TIEN and len(m.group(1)) >= 2:
            ra.append((m.group(1), m.group(0)))
    return ra


def khung_goi_y(ma_nguon: str, tieu_de: str = "", mo_ta: str = "") -> str | None:
    m = re.search(r"\binput\s+ENUM_TIMEFRAMES\s+\w+\s*=\s*PERIOD_([A-Z]+\d*)\s*;", sach(ma_nguon))
    if m and m.group(1) in KHUNG_HOP_LE:
        return m.group(1)
    m = re.search(r"(?<![A-Za-z0-9])(M1|M5|M15|M30|H1|H4|D1)(?![A-Za-z0-9])", "%s %s" % (tieu_de, mo_ta))
    return m.group(1) if m else None


def goi_y_ma(ma_nguon: str, tieu_de: str = "", mo_ta: str = "") -> list[dict]:
    """Ma/khung tai san EA nham toi, kem BANG CHUNG (nguon + tu khoa). Khong co bang chung -> danh sach rong."""
    ra: list[dict] = []
    thay: set = set()

    def them(ma, nguon, bc):
        if ma not in thay:
            thay.add(ma)
            ra.append({"ma": ma, "nguon": nguon, "bang_chung": bc})
    m = re.search(r'\binput\s+string\s+\w*(?:symbol|pair|instrument)\w*\s*=\s*"([^"]+)"', ma_nguon, re.I)
    if m:
        for ma, bc in _ma_trong_van_ban(m.group(1)) or [(m.group(1).upper(), m.group(1))]:
            them(ma, "input", bc)
    for nguon, van in (("tieu_de", tieu_de), ("mo_ta", mo_ta)):
        for ma, bc in _ma_trong_van_ban(van or "") + _co_phieu_trong_tieu_de(van):
            them(ma, nguon, bc)
    chuoi = " ".join(re.findall(r'"([A-Za-z0-9._& ]{3,16})"', ma_nguon))
    for ma, bc in _ma_trong_van_ban(chuoi):
        them(ma, "ma_nguon", bc)
    return ra


def khop_ma(goi_y: str, co_san: list[str]) -> str | None:
    """Ma trong danh sach co san khop `goi_y` (XAUUSD -> XAUUSDM, US100 -> US100CASH); chon ten NGAN nhat."""
    g = goi_y.upper()
    for tuong_ung in (lambda t: t == g, lambda t: t.startswith(g), lambda t: g in t):
        ung = [x for x in co_san if tuong_ung(x.upper())]
        if ung:
            return min(ung, key=len)
    return None


def ma_co_san() -> list[str] | None:
    """Ma co du lieu that tren may nay (de khong dat EA co phieu len EURUSD); None = khong biet (vd cloud)."""
    try:
        ds = [x["ma"] for x in NDL.danh_sach(gom_tong_hop=False) if x.get("ma")]
    except Exception:
        return None
    return ds or None


def symbol_san(ma: str, cfg: dict) -> str:
    return (cfg.get("ban_do_symbol") or {}).get(ma) or (ma + str(cfg.get("hau_to_symbol") or ""))


def chon_ma_khung(pl: dict, ma_nguon: str, tieu_de: str = "", mo_ta: str = "",
                  co_san: list[str] | None = None, toi_da: int = 3) -> dict:
    """-> {'ung_vien': [{ma, khung, nguon, bang_chung}], 'thieu_du_lieu': [...], 'mac_dinh': bool}.

    Khong co bang chung gi -> MA_MAC_DINH va ghi ro `mac_dinh=True` (lan chay do la doan, khong phai hieu EA)."""
    khung = pl.get("khung_goi_y") or "H1"
    goi = goi_y_ma(ma_nguon, tieu_de, mo_ta)
    mac_dinh = not goi
    if mac_dinh:
        goi = [{"ma": m, "nguon": "mac_dinh", "bang_chung": "EA khong cho bang chung ve tai san"}
               for m in MA_MAC_DINH]
    ung_vien, thieu = [], []
    for g in goi:
        ma = g["ma"]
        if co_san is not None:
            ma = khop_ma(ma, co_san)
            if ma is None:
                thieu.append(g["ma"])
                continue
        ung_vien.append({"ma": ma, "khung": khung, "nguon": g["nguon"], "bang_chung": g["bang_chung"]})
    return {"ung_vien": ung_vien[:toi_da], "thieu_du_lieu": thieu, "mac_dinh": mac_dinh,
            "khung_tu_dau": "ma/tieu de" if pl.get("khung_goi_y") else "mac dinh H1"}


# ============================================================ 3. THAM SO
_KHONG_TINH_CHINH = re.compile(r"magic|slippage|deviation|comment|lot|volume|risk|spread|balance|seed|digits|"
                               r"hour|minute|time|day|month|year|date|id$", re.I)
_UU_TIEN = ((re.compile(r"period|length|lookback|bars|fast|slow|signal|smooth", re.I), 3),
            (re.compile(r"step|distance|range|threshold|width|atr|mult|factor|gap", re.I), 3),
            (re.compile(r"tp|takeprofit|take_profit|profit|sl|stoploss|stop_loss|stop|trail", re.I), 2))


def de_xuat_tham_so(inputs: list[dict], so_bien: int = 3, he_so=(0.7, 1.4), toi_da: int = 7) -> list[dict]:
    """Luoi NHO quanh MAC DINH cua tac gia: [mac dinh] + moi input noi bat x he_so, MOT bien mot lan.

    Khong dong cham lot/rui ro/gio/magic: lot la DON BAY (chot rieng), gio la co che (thay doi la co che khac).
    Moi diem la mot phep thu se duoc dem; AI co the bo qua va tu dua `tham_so`."""
    xep = []
    for i in inputs:
        if i["mac_dinh"] == 0 or _KHONG_TINH_CHINH.search(i["ten"]):
            continue
        d = max((w for r, w in _UU_TIEN if r.search(i["ten"])), default=0)
        if d:
            xep.append((-d, i["ten"], i))
    xep.sort(key=lambda x: (x[0], x[1]))
    ra = [{"ten": "mac_dinh", "tham_so": {}}]
    for _, _, i in xep[:so_bien]:
        for h in he_so:
            v = i["mac_dinh"] * h
            v = max(1, int(round(v))) if i["kieu"] == "int" else round(v, 6)
            if v != i["mac_dinh"] and len(ra) < toi_da:
                ra.append({"ten": "%s=%g" % (i["ten"], v), "tham_so": {i["ten"]: v}})
    return ra


def _so_chuan(v):
    return round(float(v), 10) if isinstance(v, (int, float)) and not isinstance(v, bool) else v


def _chuan_ts(ts: dict | None) -> dict:
    return {str(k): _so_chuan(v) for k, v in sorted((ts or {}).items())}


# ============================================================ 4. CUA SO THEO DOAN DONG BANG
def _ngay(chuoi) -> date:
    return datetime.fromisoformat(str(chuoi).strip()[:19]).date()


def cua_so(k: dict, doan: str, ngay_cach: int = 1) -> tuple[date, date]:
    """Cua so ngay [a, b] cua mot doan. NGAY RANH GIOI khong thuoc doan nao (cach ly `ngay_cach` ngay moi phia):
    bar cuoi cua doan truoc va bar dau cua doan sau khong bao gio cung nam trong mot lan chay tester."""
    t = [_ngay(k[x]) for x in ("t_dau", "t_xac_nhan", "t_niem_phong", "t_cuoi")]
    c = timedelta(days=ngay_cach)
    return {"kham_pha": (t[0], t[1] - c), "xac_nhan": (t[1] + c, t[2] - c),
            "niem_phong": (t[2] + c, t[3])}[doan]


def doan_dong_bang(ma: str, khung: str, tu_nap: bool = True) -> dict | None:
    key = "%s|%s" % (ma.upper(), khung.upper())
    k = NDL._doc_doan().get(key)
    if k is None and tu_nap:
        try:
            NDL.nap(ma, khung)                  # lan dau: dong bang + ghi vao so cai
        except Exception:
            return None
        k = NDL._doc_doan().get(key)
    return k


def ke_hoach(ma: str, khung: str, doan: str, cfg: dict | None = None, ngay_cach: int = 1) -> dict:
    """Cua so ngay cho mot doan, hoac `ha_tang=True` + ly do (chua dong bang / doan qua ngan / ngoai tick that)."""
    if doan not in NDL.DOAN:
        raise ValueError("doan phai la %s" % (tuple(NDL.DOAN),))
    cfg = cfg or cau_hinh()
    k, dung = None, None
    for kh in dict.fromkeys([khung.upper(), "H1", "H4", "D1"]):
        k = doan_dong_bang(ma, kh, cfg.get("tu_nap", True))
        if k:
            dung = kh
            break
    if not k:
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True,
                "ly_do": "chua co doan dong bang cho %s (H1/H4/D1/%s) - can du lieu o may nha (b khoi-phuc)"
                         % (ma.upper(), khung.upper())}
    a, b = cua_so(k, doan, ngay_cach)
    if cfg.get("tick_tu"):
        a = max(a, _ngay(cfg["tick_tu"]))
    if (b - a).days + 1 < NGAY_TOI_THIEU:
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True,
                "ly_do": "cua so %s cua %s|%s chi con %d ngay < %d (doan qua ngan%s)"
                         % (doan, ma.upper(), dung, max((b - a).days + 1, 0), NGAY_TOI_THIEU,
                            " hoac nam ngoai tick that" if cfg.get("tick_tu") else "")}
    return {"khoa_doan": "%s|%s" % (ma.upper(), dung), "tu": a.strftime("%Y.%m.%d"),
            "den": b.strftime("%Y.%m.%d"), "ngay": (b - a).days + 1}


# ============================================================ 5. DOC EA
def ten_sach(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s)[:40].strip("_") or "ea"


def sha_ma(ma: str) -> str:
    return hashlib.sha1((ma or "").replace("\r\n", "\n").encode("utf-8")).hexdigest()[:16]


def doc_ea(ea: str) -> dict:
    """`ea`: duong .mq5 | 'kho:<so thu tu>' | 'kho:<tu trong tieu de>' (reports/ea/kho.json)."""
    ea = str(ea).strip()
    if ea.lower().startswith("kho:"):
        ds = json.loads(KHO_JSON.read_text(encoding="utf-8-sig"))
        tim = ea[4:].strip()
        if tim.isdigit():
            if not 0 <= int(tim) < len(ds):
                raise KeyError("kho co %d EA, khong co so %s" % (len(ds), tim))
            d = ds[int(tim)]
        else:
            ung = [x for x in ds if tim.lower() in str(x.get("ten", "")).lower()]
            if len(ung) != 1:
                raise KeyError("kho:%s khop %d EA (can dung 1): %s"
                               % (tim, len(ung), [x.get("ten") for x in ung][:5]))
            d = ung[0]
        ma, tieu_de, url = d.get("ma", ""), str(d.get("ten", "")), d.get("url", "")
    else:
        p = Path(ea)
        if not p.exists():
            raise KeyError("khong thay file EA: %s" % ea)
        ma, tieu_de, url = BC.doc_van_ban(p), p.stem, ""
    sha = sha_ma(ma)
    ten = ten_sach(tieu_de.split("]")[-1])[:30].strip("_") + "_" + sha[:6]
    return {"ten": ten, "tieu_de": tieu_de, "ma": ma, "url": url, "sha": sha}


def kham(ea: str, tieu_de: str = "", mo_ta: str = "", co_san: list[str] | None = None) -> dict:
    """Phan loai + ma/khung de thu + luoi tham so de xuat + cua so tung doan (neu da dong bang)."""
    co_san = co_san if co_san is not None else ma_co_san()
    d = doc_ea(ea)
    td = tieu_de or d["tieu_de"]
    pl = phan_loai(d["ma"], td, mo_ta)
    ra = {"ea": d["ten"], "sha": d["sha"], "tieu_de": d["tieu_de"], "url": d["url"], "phan_loai": pl}
    if pl["loai"] != "CHIEN_LUOC":
        ra["ket_luan"] = "KHONG chay tester: %s" % pl["loai"]
        return ra
    mk = chon_ma_khung(pl, d["ma"], td, mo_ta, co_san)
    ra["ma_khung"] = mk
    ra["de_xuat_tham_so"] = de_xuat_tham_so(pl["input_so"])
    cfg = cau_hinh()
    ra["cua_so"] = {"%s|%s" % (u["ma"], u["khung"]): {dn: ke_hoach(u["ma"], u["khung"], dn, cfg)
                                                      for dn in NDL.DOAN} for u in mk["ung_vien"][:1]}
    return ra


# ============================================================ 6. CONG
def van_tay_chay(ea_sha: str, ma: str, khung: str, ts: dict | None, doan: str, cs: dict,
                 model: int, von: float) -> str:
    return ST.van_tay("ea_tho_chay", ea_sha, ma.upper(), khung.upper(), _chuan_ts(ts), doan,
                      cs["tu"], cs["den"], int(model), _so_chuan(von))


def chi_phi_do_duoc(bc: dict, model: int, cfg: dict) -> tuple[bool, str]:
    q = bc.get("chat_luong_pct")
    if int(model) != 4:
        return False, "Model=%s khong phai tick that: spread/truot gia la gia dinh" % model
    if q is None:
        return False, "bao cao khong cho chat luong lich su (nhan chua co) - khong xac nhan duoc tick that"
    if q < float(cfg["chat_luong_toi_thieu_pct"]):
        return False, "chat luong lich su %.0f%% < %.0f%%: mot phan tick la sinh ra" % (
            q, cfg["chat_luong_toi_thieu_pct"])
    return True, "tick that, chat luong %.0f%%" % q


def _ngay_bc(chuoi: str) -> date | None:
    try:
        return datetime.strptime(str(chuoi).strip(), "%Y.%m.%d").date()
    except ValueError:
        return None


def kiem_cua_so(bc: dict, cs: dict) -> tuple[bool | None, int]:
    """(cua so bao cao NAM TRONG cua so lenh va phu >= 80% | None neu bao cao khong ghi ngay, so ngay bao cao).

    Chi can NAM TRONG (khong doi trung tung ngay): tester co the cat ngay cuoi thieu du lieu. Vuot RA NGOAI doan
    dong bang moi la ro ri - bao cao bar cua doan khac."""
    tu, den = _ngay_bc(bc.get("tu")), _ngay_bc(bc.get("den"))
    if tu is None or den is None:
        return None, int(cs["ngay"])
    a, b = _ngay_bc(cs["tu"]), _ngay_bc(cs["den"])
    ngay = (den - tu).days + 1
    return (a <= tu <= den <= b and ngay >= 0.8 * cs["ngay"]), ngay


def phan_quyet(bc: dict, doan: str, lenh: dict, cfg: dict, log_hong: str = "") -> tuple[str, str, dict]:
    """-> (trang_thai, ly_do, chi_so). `chi_so['ha_tang']=True`: hong ha tang, KHONG ghi so (khong tieu phep thu,
    khong tieu mot lan mo niem phong, khong lo so vi ket qua tra ve khong kem so nao)."""
    so: dict = {"ha_tang": False}

    def hong(ly: str):
        so["ha_tang"] = True
        return "CHUA_DO_DUOC", ly, so
    if log_hong:
        return hong(log_hong)
    if not bc.get("doc_duoc"):
        return hong("bao cao khong doc duoc: %s" % (bc.get("loi") or "thieu " + ", ".join(bc.get("thieu", []))))
    if bc.get("ticks") == 0 or bc.get("bars") == 0:
        return hong("bao cao ghi 0 tick/0 bar - tester khong co du lieu")
    cs = lenh["cua_so"]
    cua_so_ok, ngay = kiem_cua_so(bc, cs)
    if cua_so_ok is False:
        return hong("cua so bao cao (%s .. %s) khong nam trong / khong phu du cua so lenh (%s .. %s): tester khong "
                    "chay dung doan da dong bang" % (bc.get("tu"), bc.get("den"), cs["tu"], cs["den"]))
    if cua_so_ok is None and doan == "niem_phong":
        return hong("niem_phong can xac minh duoc cua so tu bao cao nhung bao cao khong ghi ngay (nhan Period "
                    "chua nhan ra - dat cfg.nhan_them)")
    do_tin, ly_tin = chi_phi_do_duoc(bc, lenh["model"], cfg)
    if doan == "niem_phong" and not do_tin:
        return hong("chi phi KHONG do duoc (%s): doan niem phong khong the DAT, nen khong tinh ket qua o day - "
                    "sua du lieu/nhan roi chay lai (chua tieu lan mo)" % ly_tin)
    von = float(bc.get("von") or lenh["von"])
    lai, dd, n = float(bc["lai_rong"]), float(bc["dd_pct"]), int(bc["so_lenh"])
    cagr = ((1.0 + lai / von) ** (365.25 / ngay) - 1.0) * 100.0 if von > 0 and 1.0 + lai / von > 0 else -100.0
    so.update(lai=round(lai, 2), von=von, cagr_pct=round(cagr, 2), dd_pct=round(dd, 2), so_lenh=n,
              pf=bc.get("pf"), ky_vong_lenh=bc.get("ky_vong"), chat_luong_pct=bc.get("chat_luong_pct"),
              do_tin_chi_phi="DO" if do_tin else "KHAI", ngay=int(ngay), cua_so_khop=cua_so_ok)
    toi_thieu = TN.LENH_TOI_THIEU_NIEM_PHONG if doan == "niem_phong" else TN.LENH_TOI_THIEU
    if n < toi_thieu:
        return "CHUA_DO_DUOC", "chi %d lenh < %d tren doan %s" % (n, toi_thieu, doan), so
    if lai <= 0:
        return "AM", "KHONG co lai sau phi: %+.2f tren von %.0f (%+.2f%%/nam), %d lenh" % (lai, von, cagr, n), so
    if dd >= DD_TRAN:
        return "AM", ("co lai (%+.2f%%/nam, %d lenh) NHUNG maxDD %.1f%% >= %.0f%% o bo tham so/lot nay"
                      % (cagr, n, dd, DD_TRAN)), so
    return "DAT", "co lai sau phi: %+.2f%%/nam, maxDD %.1f%% < %.0f%%, %d lenh, %s" % (
        cagr, dd, DD_TRAN, n, ly_tin), so


def nhan_canh_bao(so: dict, bc: dict, cfg: dict, lenh: dict) -> list[str]:
    ra = []
    pf = so.get("pf")
    if pf and pf > PF_NGHI_NHIN_TRUOC:
        ra.append("PF %.1f > %.0f: nghi khop duong cong / nhin truoc - xem lai tren doan khac" % (pf, PF_NGHI_NHIN_TRUOC))
    if so.get("so_lenh", 0) < 30:
        ra.append("chi %d lenh: mau nho, ket qua nhieu ngau nhien" % so.get("so_lenh", 0))
    if so.get("dd_pct") is not None and 50 <= so["dd_pct"] < DD_TRAN:
        ra.append("maxDD %.0f%% gan tran %.0f%%" % (so["dd_pct"], DD_TRAN))
    if so.get("do_tin_chi_phi") == "KHAI":
        ra.append("chi phi KHAI: tester khong chay tick that / chat luong thap - khong the DAT o niem phong")
    if not cfg.get("da_hieu_chuan_lenh_mo"):
        ra.append("CHUA hieu chuan: lenh con MO luc het cua so co duoc tinh/dong khong (lai dong vs equity)")
    if bc.get("lenh_mo_cuoi"):
        ra.append("co lenh mo cuoi ky")
    return ra


def _dong_gia_thuyet(gt_id: int) -> list[int]:
    return ST.dong_ho(ST.goc_cua(int(gt_id)))


def _chan_niem_phong(lenh: dict, cfg: dict) -> str | None:
    """Ly do KHONG duoc mo niem phong, hoac None. Goi ca luc lap lenh va luc nhan ket qua (trang thai co the doi)."""
    if int(lenh["model"]) != 4:
        return ("niem_phong chi chay Model=4 (tick that): Model=%s thi spread/truot gia la gia dinh va ket qua "
                "khong bao gio DAT - khong dang tieu mot lan mo" % lenh["model"])
    gt_id = lenh.get("gt_id")
    if gt_id is None:
        return "niem_phong can gt_id: moi lan mo phai gan voi mot gia thuyet da ghi"
    if not ST.mot("SELECT id FROM gia_thuyet WHERE id=?", int(gt_id)):
        return "khong co gia thuyet id=%s" % gt_id
    dong = _dong_gia_thuyet(gt_id)
    da_mo = int(ST.mot("SELECT COUNT(*) n FROM niem_phong WHERE gt_id IN (%s)" % ",".join("?" * len(dong)),
                       *dong).get("n") or 0)
    if da_mo >= TN.MO_NIEM_PHONG_TOI_DA:
        return ("dong gia thuyet nay da mo niem phong %d lan (tran %d). Mo them la bien doan niem phong "
                "thanh doan chon." % (da_mo, TN.MO_NIEM_PHONG_TOI_DA))
    xn = ke_hoach(lenh["ma"], lenh["khung"], "xac_nhan", cfg)
    if "tu" not in xn:
        return "khong tinh duoc cua so xac_nhan de kiem cam ket: %s" % xn.get("ly_do")
    vt_xn = van_tay_chay(lenh["ea_sha"], lenh["ma"], lenh["khung"], lenh["tham_so"], "xac_nhan", xn,
                         lenh["model"], lenh["von"])
    r = ST.mot("SELECT trang_thai FROM thi_nghiem WHERE van_tay=? ORDER BY id DESC LIMIT 1", vt_xn)
    if r.get("trang_thai") != "DAT":
        return ("chua co xac_nhan DAT cho CHINH bo (EA, ma, khung, tham so, von, model) nay (%s). Cam ket don "
                "bay = bo tham so da qua xac_nhan; chon bo tham so tren seal la nhin truoc."
                % (r.get("trang_thai") or "chua chay"))
    return None


def lap_lenh(ea: dict, ma: str, khung: str, doan: str, tham_so: dict | None = None,
             gt_id: int | None = None, cfg: dict | None = None) -> dict:
    """Lenh chay tester cho mot doan, hoac ly do KHONG chay. Tra `trang_thai='SAN_SANG'` + `lenh`.

    kham_pha / xac_nhan: da co ket qua cung van tay -> tra lai tu so tay (khong chay, khong dem them)."""
    cfg = cfg or cau_hinh()
    ma, khung, doan = str(ma).upper(), str(khung).upper(), str(doan)
    if khung not in KHUNG_HOP_LE:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "khung '%s' khong hop le (co %s)" % (khung, KHUNG_HOP_LE)}
    if doan not in NDL.DOAN:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "doan phai la %s" % (tuple(NDL.DOAN),)}
    kh = ke_hoach(ma, khung, doan, cfg)
    if "tu" not in kh:
        return kh
    ts = _chuan_ts(tham_so)
    vt = van_tay_chay(ea["sha"], ma, khung, ts, doan, kh, cfg["model"], cfg["von"])
    lenh = {"van_tay": vt, "doan": doan, "ma": ma, "khung": khung, "gt_id": gt_id, "ea_ten": ea["ten"],
            "ea_sha": ea["sha"], "tham_so": ts, "cua_so": kh, "model": int(cfg["model"]),
            "von": cfg["von"],
            "viec": {"terminal": "", "ea": ea["ten"], "nhan": "ea_" + vt[:10],
                     "symbol": symbol_san(ma, cfg), "khung": khung, "tu": kh["tu"],
                     "den": kh["den"], "model": int(cfg["model"]), "von": int(cfg["von"]),
                     "don_bay": int(cfg["don_bay"]), "han_giay": int(cfg["han_giay"]),
                     "input": {k: {"gia_tri": v} for k, v in ts.items() if isinstance(v, (int, float))}}}
    if doan == "niem_phong":
        cu = ST.mot("SELECT * FROM niem_phong WHERE van_tay=?", vt)
        if cu:
            kq = json.loads(cu["ket_qua"] or "{}")
            kq["da_mo_truoc"] = "bo nay da mo niem phong luc %s - XAC NHAN LA HAM Y NGUYEN, khong mo lai" % cu["luc"]
            return kq
        ly = _chan_niem_phong(lenh, cfg)
        if ly:
            return {"trang_thai": "CHUA_DO_DUOC", "ly_do": ly}
    else:
        cu = ST.da_thu(vt)
        if cu and cu.get("ket_qua"):
            kq = dict(cu["ket_qua"])
            kq["tu_so_tay"] = "thi nghiem %s da chay y het - tra ket qua cu, KHONG tinh them phep thu" % cu["id"]
            kq["tn_id"] = cu["id"]
            return kq
    return {"trang_thai": "SAN_SANG", "lenh": lenh}


def nhan_ket_qua(lenh: dict, bao_cao, log: str = "", vong_id: int | None = None, giay: float = 0.0) -> dict:
    """Bao cao tester + lenh -> ket luan DAT/AM/CHUA_DO_DUOC, ghi so tay (va bang niem_phong neu la seal)."""
    cfg = cau_hinh()
    doan, vt, ma, khung = lenh["doan"], lenh["van_tay"], lenh["ma"], lenh["khung"]
    kh = ke_hoach(ma, khung, doan, cfg)
    if "tu" not in kh or (kh["tu"], kh["den"]) != (lenh["cua_so"]["tu"], lenh["cua_so"]["den"]):
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True,
                "ly_do": "lenh khong khop cua so dong bang hien tai (%s)" % (kh.get("ly_do") or "doan da doi")}
    if vt != van_tay_chay(lenh["ea_sha"], ma, khung, lenh["tham_so"], doan, kh, lenh["model"], lenh["von"]):
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True, "ly_do": "van tay lenh khong khop noi dung lenh"}
    if doan == "niem_phong":
        cu = ST.mot("SELECT * FROM niem_phong WHERE van_tay=?", vt)
        if cu:
            kq = json.loads(cu["ket_qua"] or "{}")
            kq["da_mo_truoc"] = "bo nay da mo niem phong luc %s - khong mo lai" % cu["luc"]
            return kq
        ly = _chan_niem_phong(lenh, cfg)
        if ly:
            return {"trang_thai": "CHUA_DO_DUOC", "ly_do": ly}
    else:
        cu = ST.da_thu(vt)
        if cu and cu.get("ket_qua"):
            kq = dict(cu["ket_qua"])
            kq["tu_so_tay"] = "thi nghiem %s da ghi - khong tinh them phep thu" % cu["id"]
            return kq
    bc = bao_cao if isinstance(bao_cao, dict) else BC.doc_bao_cao(bao_cao, cfg.get("nhan_them"))
    tt, ly, so = phan_quyet(bc, doan, lenh, cfg, BC.dau_hieu_hong(log) if log else "")
    if so.get("ha_tang"):
        return {"trang_thai": tt, "ly_do": ly, "ha_tang": True,
                "ghi_chu": "hong ha tang: KHONG ghi so tay, khong tieu phep thu / mot lan mo niem phong"}
    nhan = {"canh_bao": nhan_canh_bao(so, bc, cfg, lenh)}
    if lenh.get("gt_id") is not None:
        nhan["so_phep_thu_dong_gia_thuyet"] = ST.dem_phep_thu(gt_id=int(lenh["gt_id"]), doan=doan) + 1
        if doan == "xac_nhan":
            dong = _dong_gia_thuyet(lenh["gt_id"])
            nhin = int(ST.mot("SELECT COUNT(*) n FROM thi_nghiem WHERE doan='xac_nhan' AND gt_id IN (%s)"
                              % ",".join("?" * len(dong)), *dong).get("n") or 0)
            if nhin >= TN.NHIN_XAC_NHAN_CANH_BAO:
                nhan["canh_bao"].append("doan xac_nhan da bi nhin %d lan cho dong nay - no dang thanh doan "
                                        "kham pha thu hai; ket qua o day lac quan dan" % nhin)
    ra = {"trang_thai": tt, "ly_do": ly, "ma": ma, "khung": khung, "doan": doan, "ea": lenh["ea_ten"],
          "ea_sha": lenh["ea_sha"], "tham_so": lenh["tham_so"], "cua_so": lenh["cua_so"], "chi_so": so,
          "nhan": nhan}
    dau_vao = {"ea_sha": lenh["ea_sha"], "ea": lenh["ea_ten"], "tham_so": lenh["tham_so"],
               "cua_so": lenh["cua_so"], "model": lenh["model"], "von": lenh["von"]}
    tom_tat = "%s %s/%s %s: %s%%/nam DD%s%% · %s lenh -> %s" % (
        lenh["ea_ten"], ma, khung, doan, so.get("cagr_pct"), so.get("dd_pct"), so.get("so_lenh"), tt)
    if doan == "niem_phong":
        ra["goi_ten_dung"] = ("DAT o day = CO LAI VA maxDD < %.0f%% tren MT5 tester, doan chua tung dung toi, "
                              "cung bo tham so da qua xac_nhan - canh bac co ky vong duong do duoc, chua phai "
                              "chan ly. Buoc tiep: demo." % DD_TRAN)
        with ST.ket_noi() as cn:
            cn.execute("INSERT INTO niem_phong(luc,van_tay,gt_id,ma,khung,spec,ket_qua,trang_thai) "
                       "VALUES(?,?,?,?,?,?,?,?)",
                       (ST.bay_gio(), vt, int(lenh["gt_id"]), ma, khung, ST._json(dau_vao), ST._json(ra), tt))
        ST.cap_nhat_gia_thuyet(int(lenh["gt_id"]),
                               trang_thai="XAC_NHAN" if tt == "DAT" else ("TRUOT_NIEM_PHONG" if tt == "AM" else None),
                               ket_luan="niem phong EA %s/%s: %s" % (ma, khung, ly))
        tom_tat = "NIEM PHONG " + tom_tat
    ra["tn_id"] = ST.ghi_thi_nghiem("ea_tho_" + doan, dau_vao, ra, tt, vt, ma, khung, doan,
                                    gt_id=lenh.get("gt_id"), so_phep_thu=1, giay=giay, vong_id=vong_id,
                                    tom_tat=tom_tat)
    return ra


# ============================================================ 7. CHAY / QUET / TINH
def _chay_that(lenh: dict, ea: dict, cfg: dict) -> dict:
    """CHI may nha (Windows + MT5): xin slot -> bien dich -> tester -> tra duong bao cao + log agent.

    CHUA TUNG CHAY. Dung lai `ea_tu_dong` (bien_dich, chay_mot) va `slot_tester.cap`. `ea_tu_dong.TERMINAL`
    ghim GUID may cu nen o day dang ky slot vua xin nhu mot terminal tam."""
    if os.name != "nt":
        return {"xong": False, "loi": "chay tester can may nha (Windows + MT5), may nay la %s" % os.name}
    import ea_tu_dong as EA
    from nhan import slot_tester as SL
    with SL.cap("ea_tho:" + lenh["van_tay"]) as slot:
        khoa = "slot:" + slot.ten
        EA.TERMINAL[khoa] = (slot.du_lieu, slot.exe.parent, "")
        ds = EA.bien_dich([{"url": ea.get("url", ""), "ten": ea["ten"], "ma": ea["ma"]}], khoa, cho_giay=90.0)
        if not ds or not ds[0]["bien_dich"]:
            return {"xong": False, "loi": "bien dich hong: %s" % (ds[0]["loi"] if ds else "khong co ket qua")}
        viec = dict(lenh["viec"], terminal=khoa, ea=ds[0]["ten_file"])
        kq = EA.chay_mot(viec)
        log = ""
        try:
            goc = Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Tester"
            fs = sorted(goc.glob("*/Agent-*/logs/*.log"), key=lambda p: p.stat().st_mtime)
            if fs:
                log = BC.doc_van_ban(fs[-1])
        except OSError:
            pass
        return {"xong": bool(kq.get("xong")), "bao_cao": kq.get("bao_cao", ""), "log": log,
                "giay": kq.get("giay", 0.0), "loi": kq.get("bo_qua") or ("" if kq.get("xong") else
                                                                         "tester khong ra bao cao")}


def chay(ea: str, ma: str, khung: str, doan: str = "kham_pha", tham_so: dict | None = None,
         gt_id: int | None = None, vong_id: int | None = None) -> dict:
    """MOT lan chay: lap lenh -> tester -> cong -> so tay."""
    d = doc_ea(ea)
    cfg = cau_hinh()
    lo = lap_lenh(d, ma, khung, doan, tham_so, gt_id, cfg)
    if lo.get("trang_thai") != "SAN_SANG":
        return lo
    t0 = time.time()
    r = (CHAY_TESTER or _chay_that)(lo["lenh"], d, cfg)
    if not r.get("xong"):
        return {"trang_thai": "CHUA_DO_DUOC", "ha_tang": True,
                "ly_do": "tester khong ra ket qua: %s" % (r.get("loi") or "khong ro")}
    return nhan_ket_qua(lo["lenh"], r["bao_cao"], r.get("log", ""), vong_id, giay=time.time() - t0)


def gia_thuyet_ea(d: dict, ma: str, khung: str, pl: dict | None = None) -> int:
    """Gia thuyet cho mot (EA, ma, khung): idempotent theo ma gia thuyet."""
    return ST.them_gia_thuyet(
        "EA cong khai '%s' co lai sau phi va maxDD < %.0f%% tren %s %s (MT5 tester, doan dong bang)"
        % (d["tieu_de"][:60], DD_TRAN, ma, khung),
        "EA da duoc phat hanh/ban cong khai nen co the da qua mat nguoi dung that; co che chua viet ra - "
        "tien tu tester, khong tu mo hinh cua lab", ho="ea_tho", pham_vi={"ea_sha": d["sha"], "ma": ma, "khung": khung,
                                                                       "ho": (pl or {}).get("ho")},
        nguon="ea_tho", ma="gt_ea_%s_%s_%s" % (d["sha"][:10], ma, khung))


def _gon(r: dict) -> dict:
    so = r.get("chi_so") or {}
    return {"trang_thai": r.get("trang_thai"), "ly_do": (r.get("ly_do") or "")[:140],
            "cagr_pct": so.get("cagr_pct"), "dd_pct": so.get("dd_pct"), "so_lenh": so.get("so_lenh"),
            "tn_id": r.get("tn_id"), "tu_so_tay": bool(r.get("tu_so_tay"))}


def quet(eas: list[str] | str, doan: str = "kham_pha", toi_da_lan: int = 6, co_san: list[str] | None = None,
         vong_id: int | None = None) -> dict:
    """Quet nhieu EA. Buoc 1 (thuan, khong ton ngan sach): phan loai het, bo cong cu, doi chieu ma voi `co_san`.
    Buoc 2: chay chien luoc o ma/khung nham toi (toi da 2 ung vien moi EA) cho den het `toi_da_lan` lan chay THAT
    (ket qua da co trong so tay tra ve tu so tay, khong tinh). Phan con lai nam o `con_lai`: goi lai la di tiep."""
    co_san = co_san if co_san is not None else ma_co_san()
    if isinstance(eas, str):
        eas = [eas]
    ds = []
    for e in eas:
        if str(e).strip().lower() == "kho:*":
            ds += ["kho:%d" % i for i in range(len(json.loads(KHO_JSON.read_text(encoding="utf-8-sig"))))]
        else:
            ds.append(e)
    eas = ds
    bo_qua, ke = [], []
    for e in eas:
        try:
            d = doc_ea(e)
        except (KeyError, OSError, ValueError) as x:
            bo_qua.append({"ea": e, "loai": "KHONG_DOC_DUOC", "ly_do": "doc EA loi: %s" % x})
            continue
        pl = phan_loai(d["ma"], d["tieu_de"])
        if pl["loai"] != "CHIEN_LUOC":
            bo_qua.append({"ea": d["ten"], "loai": pl["loai"], "ly_do": pl["ly_do"][0]})
            continue
        mk = chon_ma_khung(pl, d["ma"], d["tieu_de"], "", co_san, toi_da=2)
        for ma in mk["thieu_du_lieu"]:
            bo_qua.append({"ea": d["ten"], "loai": "THIEU_DU_LIEU",
                           "ly_do": "EA nham toi %s nhung may nay khong co ma do - khong thay bang ma khac" % ma})
        ke += [(e, d, pl, mk, u) for u in mk["ung_vien"]]
    bang, con_lai, lan = [], [], 0
    for e, d, pl, mk, u in ke:
        if lan >= toi_da_lan:
            con_lai.append({"ea": d["ten"], "ma": u["ma"], "khung": u["khung"]})
            continue
        gt = gia_thuyet_ea(d, u["ma"], u["khung"], pl)
        r = chay(e, u["ma"], u["khung"], doan, None, gt, vong_id)
        if not r.get("tu_so_tay") and not r.get("ha_tang") and r.get("trang_thai") != "CHUA_DO_DUOC":
            lan += 1
        elif not r.get("tu_so_tay") and r.get("tn_id"):
            lan += 1                                # CHUA_DO_DUOC co ghi so (it lenh) cung la mot phep thu
        if r.get("tn_id"):
            ST.cap_nhat_gia_thuyet(gt, trang_thai="DANG_THU")
        bang.append({"ea": d["ten"], "ma": u["ma"], "khung": u["khung"], "gt_id": gt,
                     "mac_dinh_ma": mk["mac_dinh"], **_gon(r)})
    return {"bang": bang, "bo_qua": bo_qua, "con_lai": con_lai, "so_lan_chay": lan,
            "het_ngan_sach": bool(con_lai)}


def tinh(ea: str, ma: str, khung: str, gt_id: int | None = None, so_bien: int = 3, toi_da_lan: int = 7,
         xac_nhan: bool = True, vong_id: int | None = None) -> dict:
    """Tinh chinh quanh MAC DINH tren kham_pha, chon bo DAT tot nhat (CAGR), xac_nhan DUNG BO DO mot lan.

    Moi diem la mot phep thu duoc dem theo dong gia thuyet. KHONG bao gio cham niem_phong: do la buoc rieng."""
    d = doc_ea(ea)
    pl = phan_loai(d["ma"], d["tieu_de"])
    if pl["loai"] != "CHIEN_LUOC":
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "EA khong phai chien luoc (%s)" % pl["loai"]}
    gt = gt_id if gt_id is not None else gia_thuyet_ea(d, ma.upper(), khung.upper(), pl)
    bang, tot = [], None
    for c in de_xuat_tham_so(pl["input_so"], so_bien, toi_da=toi_da_lan):
        r = chay(ea, ma, khung, "kham_pha", c["tham_so"], gt, vong_id)
        g = {"ten": c["ten"], "tham_so": c["tham_so"], **_gon(r)}
        bang.append(g)
        if r.get("trang_thai") == "DAT" and (tot is None or g["cagr_pct"] > tot["cagr_pct"]):
            tot = g
    ra = {"gt_id": gt, "bang": bang, "tot_nhat": tot, "xac_nhan": None}
    if tot is None:
        ra["trang_thai"] = "AM" if any(b["trang_thai"] == "AM" for b in bang) else "CHUA_DO_DUOC"
        ra["ly_do"] = "khong bo tham so nao DAT tren kham_pha"
        return ra
    if xac_nhan:
        r = chay(ea, ma, khung, "xac_nhan", tot["tham_so"], gt, vong_id)
        ra["xac_nhan"] = {"tham_so": tot["tham_so"], **_gon(r)}
        ra["trang_thai"] = r.get("trang_thai")
        ra["ly_do"] = "bo tot nhat tren kham_pha (%s) -> xac_nhan: %s" % (tot["ten"], r.get("ly_do"))
    else:
        ra["trang_thai"], ra["ly_do"] = "DANG_CHO_XAC_NHAN", "bo tot nhat: %s" % tot["ten"]
    ST.cap_nhat_gia_thuyet(gt, trang_thai="TRIEN_VONG" if ra["trang_thai"] == "DAT" else "DANG_THU")
    return ra
