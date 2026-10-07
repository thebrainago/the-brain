# -*- coding: utf-8 -*-
"""lenh_tester.py - DOC BANG DEAL / ORDERS cua bao cao MT5 tester va GHEP vao/ra thanh VI THE (lenh) de boc co che bot.

Chu du an 04/10/2026: *"moi bot co chien luoc, cach quan tri, tinh dac sac khac nhau ... boc tach duoc co che de ap dung cheo"*.
Bot nhi phan (.ex5) khong co ma nguon, nen BANG CHUNG DUY NHAT ve hanh vi cua no la cac lenh no dat tren tester. Bao cao
tester cua MT5 chi co hai bang (khong co bang Positions, khong co ma vi the):

  Orders  Open Time | Order | Symbol | Type | Volume (khop / tong) | Price | S/L | T/P | Time | State | Comment
  Deals   Time | Deal | Symbol | Type | Direction (in/out) | Volume | Price | Order | Commission | Swap | Profit | Balance | Comment

`boc_lich_su.doc_bang_html` tu choi ca hai (cho muc Positions) nen can bo doc rieng. Module nay:

  1. DOC        HTML (UTF-16 / UTF-8) HOAC CSV (da luu san tu bao cao) -> bang deal + bang order + Inputs cua EA. Khong dua vao vi tri
                cot ma vao NOI DUNG (gio o o dau, so nguyen o o hai, bang order co "khop / tong"), co mo rong `colspan`, doc tieu de
                tieng Anh va tieng Viet; neu bao cao co cot Position thi dung no (ghep chinh xac).
  2. KIEM       cot Balance phai khop cong don loi + hoa hong + swap tung dong: sai = doc so sai (dau thap phan, nghin) -> canh bao.
  3. GHEP       deal ra -> deal vao cung ma, nguoc chieu, bang PHUONG TRINH LOI: loi = chieu * (gia_ra - gia_vao) * lot * hop_dong
                -> gia vao suy ra -> tim lenh dang mo co gia do. Hop dong (don vi gia -> tien tai khoan) lay theo thu tu: nguoi dung
                truyen vao > uoc luong tu cac lan dong KHONG mo ho (chi mot gia vao dang mo) > TU HIEU CHUAN (thu cac gia tri hop
                dong thuong gap, chon cai ma phuong trinh khop nhieu lenh nhat, phai hon han cai thu hai) > khong co (FIFO co co).
                Khong ghep duoc bang gia thi FIFO va ghi `cach_ghep` ('fifo' = KHONG dang tin cho tung lenh rieng).
                GIOI HAN: cap CHEO tren tai khoan khac tien bao gia (vd AUDCAD tren tai khoan USD) co hop dong hieu dung = 100000 x
                ty gia CADUSD doi theo thoi gian: chi uoc luong duoc tu mau sach (`attrs["lech_hop_dong"]` cho biet do tan), tu hieu
                chuan khong lo ra (luoi gia tri thuong gap) - khi do truyen `hop_dong=` hoac chap nhan 'loi_gan' / 'fifo'.
  4. LENH       bang vi the co `mo, dong, chieu, lot, gia_mo, gia_dong, loi, hoa_hong, swap, sl, tp, ma` - dung ten cot cua
                `boc_lich_su.chuan_hoa` - kem `cm_vao` / `cm_ra` (comment cua EA: bac, "sniper"...), `ly_do_ra` (tp / sl / stopout /
                ea), `kieu_vao` (thi_truong / cho_stop / cho_limit), `gio_dat`.

## NHUNG GI MODULE NAY KHONG LAM

* KHONG do loi nhuan, khong ket luan co che: chi dua deal ve dang lenh. Co che do `ho_so_bot` boc.
* Ghep vao/ra la SUY RA tu gia (bao cao khong co ma vi the): voi nhom lenh dong cung luc, danh tinh tung lenh chi dung khi
  phuong trinh loi phan biet duoc (gia vao khac nhau). `attrs["ghep"]` dem tung cach ghep - doc truoc khi tin thong ke theo lenh.
* Gio la gio MAY CHU cua tester (khong doi mui gio).
* Cac dong KHONG phai lenh (balance / credit / ...) khong vao bang vi the; so tien nam o `attrs["nap_rut"]`.
"""
from __future__ import annotations

import collections
import io
import math
import re
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pandas as pd

from nhan import boc_lich_su as BL

PHIEN_BAN = "1"
#: sai so lam tron cua cot Profit / Balance (MT5 lam tron 0,01)
_DUNG_SAI_TIEN = 0.011

_TG = re.compile(r"^(\d{4})[.\-/](\d{2})[.\-/](\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$")
_NGUYEN = re.compile(r"^\d+$")
#: "0.01 / 0.01" (bang Orders: khoi luong khop / tong)
_KHOI = re.compile(r"^[-+]?[\d\s.,]*\d\s*/\s*[-+]?[\d\s.,]*\d$")
_LA_SO = re.compile(r"^[-+−]?[\d\s.,]*\d$")

# ---------------------------------------------------------------- tu khoa (khong dau, chu thuong, gach duoi)
_LOAI_DEAL = {"buy": "mua", "mua": "mua", "long": "mua", "sell": "ban", "ban": "ban", "short": "ban"}
_KHONG_PHAI_LENH = {"balance", "so_du", "credit", "tin_dung", "deposit", "withdrawal", "correction", "bonus", "charge",
                    "commission", "daily_commission", "monthly_commission", "interest", "tax", "dividend", "fee",
                    "agent", "daily_agent", "monthly_agent", "sales_tax", "so_du_ban_dau", "nap_tien", "rut_tien"}
_HUONG = {"in": "vao", "vao": "vao", "entry": "vao", "out": "ra", "ra": "ra", "exit": "ra",
          "in_out": "vao_ra", "vao_ra": "vao_ra", "out_by": "ra_boi", "ra_boi": "ra_boi", "ra_bang": "ra_boi"}

# ten cot (khong dau) -> vai tro. Thu tu uu tien theo tung bang.
_VAI_TRO_DEAL = {"gio": {"time", "gio", "thoi_gian"}, "deal": {"deal", "giao_dich", "ma_deal"},
                 "ma": {"symbol", "ma", "ky_hieu", "instrument"}, "loai": {"type", "loai"},
                 "huong": {"direction", "huong", "chieu"}, "lot": {"volume", "khoi_luong", "lot"},
                 "gia": {"price", "gia"}, "order": {"order", "lenh", "lenh_dat"},
                 "hoa_hong": {"commission", "hoa_hong", "phi"}, "swap": {"swap", "phi_qua_dem"},
                 "loi": {"profit", "loi_nhuan", "loi"}, "so_du": {"balance", "so_du", "so_du_tai_khoan"},
                 "ghi_chu": {"comment", "ghi_chu", "binh_luan", "chu_thich"},
                 "vi_the": {"position", "vi_the", "id_vi_the", "position_id"}}
_VAI_TRO_ORDER = {"gio_dat": {"open_time", "gio_mo", "thoi_gian_mo", "time_open"}, "order": {"order", "lenh", "lenh_dat"},
                  "ma": {"symbol", "ma", "ky_hieu"}, "loai": {"type", "loai"},
                  "lot": {"volume", "khoi_luong", "lot"}, "gia": {"price", "gia"}, "sl": {"s_l", "sl", "stop_loss", "cat_lo"},
                  "tp": {"t_p", "tp", "take_profit", "chot_loi"}, "gio": {"time", "gio", "thoi_gian"},
                  "trang_thai": {"state", "trang_thai", "status"}, "ghi_chu": {"comment", "ghi_chu", "binh_luan", "chu_thich"}}
_VI_TRI_DEAL = ["gio", "deal", "ma", "loai", "huong", "lot", "gia", "order", "hoa_hong", "swap", "loi", "so_du", "ghi_chu"]
_VI_TRI_ORDER = ["gio_dat", "order", "ma", "loai", "lot", "gia", "sl", "tp", "gio", "trang_thai", "ghi_chu"]


def _khong_dau(s) -> str:
    return BL._khong_dau(s)


# ============================================================== 1. DOC
class _Bang(HTMLParser):
    """Moi <tr> thanh mot hang cac o, MO RONG colspan (o gop thanh nhieu o: gia tri o dau, '' o sau) de vi tri cot khong lech.
    Khong can lxml / bs4. Chiu the thieu </td> / </tr> (dong lai hang / o truoc khi mo cai moi)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hang: list[list[str]] = []
        self._h: list[str] | None = None
        self._o: list[str] | None = None
        self._cs = 1
        self._an = 0

    def _dong_o(self):
        if self._o is not None and self._h is not None:
            self._h.append(re.sub(r"\s+", " ", "".join(self._o)).strip())
            self._h.extend([""] * (self._cs - 1))
        self._o, self._cs = None, 1

    def _dong_hang(self):
        self._dong_o()
        if self._h is not None and any(self._h):
            self.hang.append(self._h)
        self._h = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._dong_hang()
            self._h = []
        elif tag in ("td", "th") and self._h is not None:
            self._dong_o()
            self._o = []
            for k, v in attrs:
                if k == "colspan":
                    try:
                        self._cs = max(1, min(int(str(v).strip("\"' ")), 40))
                    except ValueError:
                        pass
        elif tag in ("script", "style"):
            self._an += 1
        elif tag == "br" and self._o is not None:
            self._o.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self._dong_o()
        elif tag == "tr":
            self._dong_hang()
        elif tag in ("script", "style"):
            self._an = max(0, self._an - 1)

    def handle_data(self, data):
        if self._o is not None and not self._an:
            self._o.append(data)

    def close(self):
        super().close()
        self._dong_hang()


def _so(s, thap_phan: str = ".") -> float:
    """'10 000.00' / '-1 234.5' / '0,01' (thap_phan=',') -> float; rong / khong doc duoc -> NaN."""
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return float("nan")
    if isinstance(s, (int, float, np.integer, np.floating)):
        return float(s)
    t = str(s).replace("\xa0", " ").replace(" ", " ").replace("−", "-").strip()
    t = t.replace(" ", "")
    if not t or t in ("-", "--"):
        return float("nan")
    t = t.replace(".", "").replace(",", ".") if thap_phan == "," else t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        return float("nan")


def _doan_thap_phan(mau: list[str]) -> str:
    """Dau thap phan cua bao cao ('.' hay ','): dem o co dang so.XX / so,XX. Mac dinh '.' (MT5: 10 000.00)."""
    cham = sum(1 for c in mau if re.search(r"\d\.\d{1,8}$", c.strip()))
    phay = sum(1 for c in mau if re.search(r"\d,\d{1,8}$", c.strip()) and "." not in c)
    return "," if phay > cham else "."


def _la_gio(c: str) -> bool:
    return bool(_TG.match(c.strip()))


def _chuan_gio(c) -> str | None:
    m = _TG.match(str(c).strip())
    if not m:
        return None
    y, mo, d, h, mi, s = m.groups()
    return "%s-%s-%s %s:%s:%s" % (y, mo, d, h, mi, s or "00")


def _phan_loai_hang(c: list[str]) -> str | None:
    """'deal' / 'order' / None. Dua vao NOI DUNG: o dau la gio, o hai la so nguyen; Orders co 'khop / tong' o o thu nam."""
    if len(c) < 10 or not _la_gio(c[0]) or not _NGUYEN.match(c[1].strip()):
        return None
    if len(c) > 4 and _KHOI.match(c[4].strip()):
        return "order"
    return "deal" if len(c) >= 12 else None


def _anh_xa_tieu_de(h: list[str], vai_tro: dict) -> dict | None:
    """Hang tieu de -> {vai_tro: chi_so_cot}. None neu khong du vai tro bat buoc (gio, loai, lot, gia)."""
    ra: dict = {}
    for i, t in enumerate(h):
        n = _khong_dau(t)
        if not n:
            continue
        for vt, tap in vai_tro.items():
            if n in tap and vt not in ra:
                ra[vt] = i
                break
    return ra if {"gio", "loai", "lot", "gia"} <= set(ra) else None


def _tieu_de_truoc(hang: list[list[str]], i0: int) -> list[str] | None:
    """Hang tieu de ngay truoc hang du lieu dau tien: hang gan nhat khong co gio, >= 8 o co chu."""
    for j in range(i0 - 1, max(-1, i0 - 6), -1):
        h = hang[j]
        if not any(_la_gio(c) for c in h) and sum(1 for c in h if re.search(r"[^\W\d_]", c)) >= 7:
            return h
    return None


def _truong(c: list[str], vt: dict, ten: str, mac_dinh: str = "") -> str:
    i = vt.get(ten)
    return c[i] if i is not None and i < len(c) else mac_dinh


def _ghi_chu(c: list[str], i: int | None) -> str:
    """Comment: o cuoi cung (co the bi chia nho boi colspan) - ghep cac o tu vi tri comment tro di."""
    if i is None or i >= len(c):
        return ""
    return " ".join(x for x in c[i:] if x).strip()


def _doc_inputs(hang: list[list[str]], i_dau: int) -> dict:
    """Inputs cua EA ghi trong phan dau bao cao: cac o co dang `Ten=GiaTri`. Chi lay truoc bang Orders / Deals dau tien."""
    ra: dict = {}
    for c in hang[:i_dau]:
        for o in c:
            m = re.fullmatch(r"([A-Za-z_]\w{0,63})\s*=\s*(.*)", o.strip())
            if m and m.group(1) not in ra:
                ra[m.group(1)] = m.group(2).strip()
    return ra


def doc_html(van: str, bang_loai: dict | None = None) -> dict:
    """HTML bao cao tester -> {"deals": DataFrame, "orders": DataFrame, "inputs": dict, "canh_bao": [...]}.

    NEM ValueError neu khong thay dong deal nao (dua file mau cho phien cloud) hoac gap tu loai deal la (khong co trong
    `_LOAI_DEAL` / `bang_loai`: doan sai lat nguoc ca lich su)."""
    p = _Bang()
    p.feed(van)
    p.close()
    hang = p.hang
    loai = [_phan_loai_hang(c) for c in hang]
    if "deal" not in loai:
        raise ValueError("khong thay dong DEAL nao (o dau = gio, o hai = so deal, >= 12 o). Dua file mau cho phien cloud de "
                         "chinh bo doc dung dinh dang that.")
    i_deal = loai.index("deal")
    i_ord = loai.index("order") if "order" in loai else None
    vt_d = {k: i for i, k in enumerate(_VI_TRI_DEAL)}
    vt_o = {k: i for i, k in enumerate(_VI_TRI_ORDER)}
    canh_bao: list[str] = []
    th = _tieu_de_truoc(hang, i_deal)
    mx = _anh_xa_tieu_de(th, _VAI_TRO_DEAL) if th else None
    if mx and "vi_the" in mx:
        vt_d = mx            # bao cao co cot Position: dung thu tu that
    elif mx and mx != {k: i for i, k in enumerate(_VI_TRI_DEAL) if k in mx} and {"huong", "order", "loi", "so_du"} <= set(mx):
        vt_d = mx
        canh_bao.append("thu tu cot Deals khac mau: dung theo tieu de")
    if i_ord is not None:
        th2 = _tieu_de_truoc(hang, i_ord)
        mo = _anh_xa_tieu_de(th2, _VAI_TRO_ORDER) if th2 else None
        if mo and mo != {k: i for i, k in enumerate(_VI_TRI_ORDER) if k in mo} and {"order", "sl", "tp", "trang_thai"} <= set(mo):
            vt_o = mo
            canh_bao.append("thu tu cot Orders khac mau: dung theo tieu de")
    deals_raw = [c for c, k in zip(hang, loai) if k == "deal"]
    orders_raw = [c for c, k in zip(hang, loai) if k == "order"]
    tp = _doan_thap_phan([_truong(c, vt_d, "gia") for c in deals_raw[:400]] +
                         [_truong(c, vt_d, "loi") for c in deals_raw[:400]])
    deals = _bang_deal(deals_raw, vt_d, tp, bang_loai)
    orders = _bang_order(orders_raw, vt_o, tp) if orders_raw else _bang_order([], vt_o, tp)
    return {"deals": deals, "orders": orders, "inputs": _doc_inputs(hang, i_deal if i_ord is None else min(i_deal, i_ord)),
            "canh_bao": canh_bao, "thap_phan": tp}


def _so_chu_so_le(cac_gia, thap_phan: str) -> int:
    """So chu so thap phan lon nhat trong cac chuoi gia GOC (truoc khi doi sang so): '1 306.10' -> 2."""
    d = 0
    for c in cac_gia:
        t = str(c).replace("\xa0", "").replace("\u202f", "").replace(" ", "")
        if thap_phan in t and re.fullmatch(r"[-+]?[\d.,]*\d", t):
            d = max(d, len(t.rsplit(thap_phan, 1)[1]))
    return d


def _bang_deal(raw: list[list[str]], vt: dict, tp: str, bang_loai: dict | None = None) -> pd.DataFrame:
    hang = []
    digits: dict = {}
    for c in raw:
        hang.append({
            "gio": _chuan_gio(_truong(c, vt, "gio")), "deal": int(_truong(c, vt, "deal") or 0),
            "ma": _truong(c, vt, "ma").strip(), "loai_goc": _truong(c, vt, "loai").strip(),
            "huong_goc": _truong(c, vt, "huong").strip(), "lot": _so(_truong(c, vt, "lot"), tp),
            "gia": _so(_truong(c, vt, "gia"), tp),
            "order": int(_so(_truong(c, vt, "order"), tp)) if _NGUYEN.match(_truong(c, vt, "order").strip() or "x") else 0,
            "hoa_hong": _so(_truong(c, vt, "hoa_hong"), tp), "swap": _so(_truong(c, vt, "swap"), tp),
            "loi": _so(_truong(c, vt, "loi"), tp), "so_du": _so(_truong(c, vt, "so_du"), tp),
            "ghi_chu": _ghi_chu(c, vt.get("ghi_chu")),
            "vi_the": _truong(c, vt, "vi_the").strip() if "vi_the" in vt else ""})
        ma = hang[-1]["ma"]
        if ma:
            digits[ma] = max(digits.get(ma, 0), _so_chu_so_le([_truong(c, vt, "gia")], tp))
    d = _hoan_thien_deal(pd.DataFrame(hang), bang_loai)
    d.attrs["digits"] = digits
    return d


def _bang_order(raw: list[list[str]], vt: dict, tp: str) -> pd.DataFrame:
    cot = ["gio_dat", "order", "ma", "loai_goc", "lot_khop", "lot", "gia", "sl", "tp", "gio", "trang_thai", "ghi_chu"]
    hang = []
    for c in raw:
        khoi = _truong(c, vt, "lot")
        a, _, b = khoi.partition("/")
        gia = _truong(c, vt, "gia").split("/")[0]
        hang.append({"gio_dat": _chuan_gio(_truong(c, vt, "gio_dat")), "order": int(_truong(c, vt, "order") or 0),
                     "ma": _truong(c, vt, "ma").strip(), "loai_goc": _truong(c, vt, "loai").strip(),
                     "lot_khop": _so(a, tp), "lot": _so(b if b else a, tp), "gia": _so(gia, tp),
                     "sl": _so(_truong(c, vt, "sl"), tp), "tp": _so(_truong(c, vt, "tp"), tp),
                     "gio": _chuan_gio(_truong(c, vt, "gio")), "trang_thai": _truong(c, vt, "trang_thai").strip(),
                     "ghi_chu": _ghi_chu(c, vt.get("ghi_chu"))})
    d = pd.DataFrame(hang, columns=cot)
    return _hoan_thien_order(d)


def _loai_lenh(w: str) -> tuple[int, str]:
    """'buy' / 'sell limit' / 'mua stop' / 'ban gioi han' -> (chieu +1/-1, kieu). Khong nhan ra -> (0, 'khac')."""
    n = _khong_dau(w)
    ch = 1 if n.startswith(("buy", "mua", "long")) else -1 if n.startswith(("sell", "ban", "short")) else 0
    gh = "limit" in n or "gioi_han" in n
    dg = "stop" in n or n.endswith("_dung") or "_dung_" in n
    if gh and dg:
        kieu = "cho_stop_limit"
    elif gh:
        kieu = "cho_limit"
    elif dg:
        kieu = "cho_stop"
    else:
        kieu = "thi_truong" if ch else "khac"
    return ch, kieu


def _hoan_thien_order(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty:
        d = d.assign(chieu=pd.Series(dtype=int), kieu=pd.Series(dtype=str))
    else:
        lk = d["loai_goc"].map(_loai_lenh)
        d["chieu"] = [x[0] for x in lk]
        d["kieu"] = [x[1] for x in lk]
    d["gio_dat"] = pd.to_datetime(d["gio_dat"], errors="coerce")
    d["gio"] = pd.to_datetime(d["gio"], errors="coerce")
    for c in ("sl", "tp"):
        d[c] = d[c].where(d[c] > 0)               # 0.00 = khong dat
    return d.reset_index(drop=True)


def _hoan_thien_deal(d: pd.DataFrame, bang_loai: dict | None = None) -> pd.DataFrame:
    """Chuan hoa loai / huong, sap xep theo (gio, deal). Tu choi tu LA (khong doan: doan sai lat nguoc ca lich su)."""
    bl = {_khong_dau(k): v for k, v in (bang_loai or {}).items()}
    loai, la = [], set()
    for w in d["loai_goc"]:
        n = _khong_dau(w)
        if n in bl:
            loai.append(bl[n])
        elif n in _LOAI_DEAL:
            loai.append(_LOAI_DEAL[n])
        elif n in _KHONG_PHAI_LENH or not n:
            loai.append("so_du")
        else:
            loai.append("la")
            la.add(str(w)[:20])
    if la:
        raise ValueError("loai deal la (khong dich duoc sang mua / ban): %s. Truyen bang_loai={'<tu>': 'mua'|'ban'|'so_du'} "
                         "hoac them vao _LOAI_DEAL." % sorted(la)[:6])
    d["loai"] = loai
    la_lenh = d["loai"].isin(("mua", "ban"))
    # huong: tu dien truoc; tu la -> deal DAU TIEN cua mot ma la VAO, tu khac con lai (neu chi con mot tu) la RA
    tu = [t for t in d.loc[la_lenh, "huong_goc"].tolist()]
    huong_map: dict = {}
    for w in dict.fromkeys(tu):
        n = _khong_dau(w)
        if n in _HUONG:
            huong_map[w] = _HUONG[n]
    chua = [w for w in dict.fromkeys(tu) if w not in huong_map]
    if chua:
        dau = tu[0] if tu else ""
        if dau in chua:
            huong_map[dau] = "vao"
            chua.remove(dau)
        if len(chua) == 1 and "ra" not in huong_map.values():
            huong_map[chua[0]] = "ra"
        elif chua:
            for w in chua:
                huong_map[w] = "khac"
    d["huong"] = d["huong_goc"].map(lambda w: huong_map.get(w, "") if w else "")
    # deal lenh KHONG co huong (bao cao khong co cot nay?) -> khong doan
    d["gio"] = pd.to_datetime(d["gio"], errors="coerce")
    d = d.sort_values(["gio", "deal"], kind="stable").reset_index(drop=True)
    return d


# ---------------------------------------------------------------- CSV (da luu san tu bao cao)
_CSV_DEAL = {"time": "gio", "gio": "gio", "deal": "deal", "symbol": "ma", "ma": "ma", "type": "loai_goc", "loai": "loai_goc",
             "direction": "huong_goc", "huong": "huong_goc", "volume": "lot", "lot": "lot", "price": "gia", "gia": "gia",
             "order": "order", "commission": "hoa_hong", "hoa_hong": "hoa_hong", "swap": "swap", "profit": "loi",
             "loi": "loi", "balance": "so_du", "so_du": "so_du", "comment": "ghi_chu", "ghi_chu": "ghi_chu",
             "position": "vi_the", "vi_the": "vi_the"}
_CSV_ORDER = {"open_time": "gio_dat", "gio_dat": "gio_dat", "order": "order", "symbol": "ma", "ma": "ma", "type": "loai_goc",
              "loai": "loai_goc", "volume": "lot", "lot": "lot", "price": "gia", "gia": "gia", "s_l": "sl", "sl": "sl",
              "t_p": "tp", "tp": "tp", "time": "gio", "gio": "gio", "state": "trang_thai", "trang_thai": "trang_thai",
              "comment": "ghi_chu", "ghi_chu": "ghi_chu"}


def _doc_csv_thanh_df(duong) -> pd.DataFrame:
    p = Path(duong)
    if not p.is_file():
        raise FileNotFoundError("khong co tep: %s" % p)
    return pd.read_csv(p, sep=None, engine="python", dtype=str, keep_default_na=False, compression="infer")


def doc_deals_csv(duong, bang_loai: dict | None = None) -> pd.DataFrame:
    """CSV deal luu tu bao cao (cot goc: time, deal, symbol, type, direction, volume, price, order, commission, swap, profit,
    balance, comment - khong phan biet hoa thuong). Cung dau ra voi `doc_html()['deals']`."""
    r = _doc_csv_thanh_df(duong)
    ten = {}
    for c in r.columns:
        k = _CSV_DEAL.get(_khong_dau(c))
        if k and k not in ten.values():
            ten[c] = k
    r = r.rename(columns=ten)
    thieu = [k for k in ("gio", "deal", "ma", "loai_goc", "huong_goc", "lot", "gia", "order", "loi", "so_du") if k not in r.columns]
    if thieu:
        raise ValueError("CSV deal thieu cot %s (co: %s)" % (thieu, list(r.columns)))
    tp = _doan_thap_phan(r["gia"].tolist()[:400] + r["loi"].tolist()[:400])
    for c in ("hoa_hong", "swap", "ghi_chu", "vi_the"):
        if c not in r.columns:
            r[c] = ""
    out = pd.DataFrame({
        "gio": r["gio"].map(_chuan_gio), "deal": pd.to_numeric(r["deal"], errors="coerce").fillna(0).astype(int),
        "ma": r["ma"].str.strip(), "loai_goc": r["loai_goc"].str.strip(), "huong_goc": r["huong_goc"].str.strip(),
        "lot": r["lot"].map(lambda x: _so(x, tp)), "gia": r["gia"].map(lambda x: _so(x, tp)),
        "order": r["order"].map(lambda x: _so(x, tp)).fillna(0).astype(int),
        "hoa_hong": r["hoa_hong"].map(lambda x: _so(x, tp)), "swap": r["swap"].map(lambda x: _so(x, tp)),
        "loi": r["loi"].map(lambda x: _so(x, tp)), "so_du": r["so_du"].map(lambda x: _so(x, tp)),
        "ghi_chu": r["ghi_chu"].astype(str).str.strip(), "vi_the": r["vi_the"].astype(str).str.strip()})
    if out["gio"].isna().all():
        raise ValueError("CSV deal: cot time khong doc duoc (can dang 2018.01.02 01:00:00)")
    digits: dict = {}
    for m, g in zip(r["ma"].tolist(), r["gia"].tolist()):
        if m.strip():
            digits[m.strip()] = max(digits.get(m.strip(), 0), _so_chu_so_le([g], tp))
    d = _hoan_thien_deal(out, bang_loai)
    d.attrs["digits"] = digits
    return d


def doc_orders_csv(duong) -> pd.DataFrame:
    """CSV order (cot goc Open Time, Order, Symbol, Type, Volume 'khop / tong', Price, S / L, T / P, Time, State, Comment)."""
    r = _doc_csv_thanh_df(duong)
    ten = {}
    for c in r.columns:
        k = _CSV_ORDER.get(_khong_dau(c))
        if k and k not in ten.values():
            ten[c] = k
    r = r.rename(columns=ten)
    thieu = [k for k in ("gio_dat", "order", "loai_goc", "lot", "gia") if k not in r.columns]
    if thieu:
        raise ValueError("CSV order thieu cot %s (co: %s)" % (thieu, list(r.columns)))
    for c in ("sl", "tp", "gio", "trang_thai", "ghi_chu", "ma"):
        if c not in r.columns:
            r[c] = ""
    tp = _doan_thap_phan(r["gia"].tolist()[:400])
    raw = []
    for _, x in r.iterrows():
        raw.append([x["gio_dat"], str(x["order"]), x["ma"], x["loai_goc"], x["lot"], x["gia"], x["sl"], x["tp"], x["gio"],
                    x["trang_thai"], x["ghi_chu"]])
    return _bang_order(raw, {k: i for i, k in enumerate(_VI_TRI_ORDER)}, tp)


def doc_tep(duong, bang_loai: dict | None = None) -> dict:
    """.htm / .html (UTF-16 / UTF-8) hoac .csv / .csv.gz (deal) -> {"deals", "orders", "inputs", "canh_bao", ...}.
    Cac tep order mau di rieng: `doc_orders_csv`."""
    p = Path(duong)
    suf = "".join(p.suffixes).lower()
    if suf.endswith((".htm", ".html")):
        van = BL._doc_chuoi(p)
        r = doc_html(van, bang_loai)
        try:
            from nhan import bao_cao_mt5 as BC
            r["tom_tat_mt5"] = {k: v for k, v in BC.phan_tich(van).items() if k not in ("van_ban",)}
        except Exception as e:                                   # noqa: BLE001 - tom tat chi la phu, khong chan viec doc deal
            r["tom_tat_mt5"] = {"loi": str(e)[:120]}
        return r
    if suf.endswith((".csv", ".tsv", ".txt", ".csv.gz")):
        return {"deals": doc_deals_csv(p, bang_loai), "orders": pd.DataFrame(), "inputs": {}, "canh_bao": [], "thap_phan": "."}
    raise ValueError("dinh dang tep khong ho tro: %s (can .htm / .html / .csv)" % p.name)


# ============================================================== 2. KIEM
def kiem_so_du(deals: pd.DataFrame) -> dict:
    """Cot Balance phai bang so du truoc + loi + hoa hong + swap cua dong do (sai so 0,011). Sai nhieu = doc so sai.

    Tra {"so_dong", "sai", "ty_le_sai", "dong_sai_dau": [deal...]} - 'khong_kiem_duoc' neu thieu cot."""
    d = deals
    if d.empty or not d["so_du"].notna().any():
        return {"so_dong": 0, "sai": 0, "ty_le_sai": None, "khong_kiem_duoc": True}
    hh = d["hoa_hong"].fillna(0.0).to_numpy(float)
    sw = d["swap"].fillna(0.0).to_numpy(float)
    lo = d["loi"].fillna(0.0).to_numpy(float)
    bal = d["so_du"].to_numpy(float)
    chenh = np.diff(bal) - (lo + hh + sw)[1:]
    ok = np.isfinite(chenh)
    sai = ok & (np.abs(chenh) > _DUNG_SAI_TIEN + 1e-9)
    return {"so_dong": int(ok.sum()), "sai": int(sai.sum()),
            "ty_le_sai": round(float(sai.sum() / max(1, ok.sum())), 4),
            "dong_sai_dau": [int(x) for x in d["deal"].to_numpy()[1:][sai][:5]]}




# ============================================================== 3. GHEP
def _so_thap_phan(gia: pd.Series, toi_thieu: int = 2) -> int:
    """So chu so thap phan cua gia (nho nhat d >= toi_thieu sao cho moi gia tron den d chu so). San 2: mot mau chi toan gia
    nguyen (1300.0, 1290.0 ...) khong duoc phep lam 'tick' = 1.0 (dung sai phuong trinh loi se nuot ca cac lenh ke nhau)."""
    v = gia.dropna().to_numpy(float)[:5000]
    for d in range(toi_thieu, 9):
        if np.allclose(np.round(v, d), v, atol=1e-9, rtol=0):
            return d
    return 8


class _Kho:
    """Cac lenh DANG MO cua mot (ma, chieu): theo thu tu mo (FIFO, xoa luoi) va theo khoa gia (tick nguyen)."""

    def __init__(self, tick: float):
        self.tick = tick
        self.rec: dict[int, dict] = {}
        self.thu_tu: collections.deque = collections.deque()
        self.theo_gia: dict[int, list[int]] = {}

    def khoa(self, gia: float) -> int:
        return int(round(gia / self.tick))

    def them(self, r: dict):
        self.rec[r["id"]] = r
        self.thu_tu.append(r["id"])
        self.theo_gia.setdefault(self.khoa(r["gia"]), []).append(r["id"])

    def bo(self, rid: int):
        r = self.rec.pop(rid, None)
        if r is not None:
            k = self.khoa(r["gia"])
            q = self.theo_gia.get(k)
            if q is not None:
                if rid in q:
                    q.remove(rid)
                if not q:
                    del self.theo_gia[k]

    def cu_nhat(self, du_lot: float = 0.0) -> dict | None:
        """Lenh mo som nhat con >= du_lot; khong co thi lenh som nhat."""
        while self.thu_tu and self.thu_tu[0] not in self.rec:
            self.thu_tu.popleft()
        if not self.thu_tu:
            return None
        if du_lot > 0:
            for i in self.thu_tu:
                r = self.rec.get(i)
                if r is not None and r["lot_con"] >= du_lot - 1e-9:
                    return r
        return self.rec[self.thu_tu[0]]

    def quanh_gia(self, gia: float, tol: float, du_lot: float = 0.0) -> list[dict]:
        """Cac lenh dang mo co gia trong [gia - tol, gia + tol] va con >= du_lot, theo thu tu mo. Dung chi muc khoa gia khi dai khoa
        ngan hon so lenh dang mo, khong thi quet het (tick rat nho so voi dung sai khong duoc lam mat ket qua)."""
        k0, k1 = self.khoa(gia - tol), self.khoa(gia + tol)
        if k1 - k0 + 1 > len(self.rec):
            cung = list(self.rec.values())
        else:
            cung = [self.rec[i] for k in range(k0, k1 + 1) for i in self.theo_gia.get(k, ()) if i in self.rec]
        ra = [r for r in cung if abs(r["gia"] - gia) <= tol + 1e-9 and r["lot_con"] >= du_lot - 1e-9]
        ra.sort(key=lambda r: r["stt"])
        return ra

    def tong_lot(self) -> float:
        return float(sum(r["lot_con"] for r in self.rec.values()))

    def __len__(self):
        return len(self.rec)


def _kieu_deal(d: pd.DataFrame) -> pd.DataFrame:
    """Chi giu deal mua / ban, kiem tra moi deal co huong. Thieu huong -> ValueError (khong doan vao hay ra)."""
    ds = d[d["loai"].isin(("mua", "ban"))]
    thieu = ds[~ds["huong"].isin(("vao", "ra", "vao_ra", "ra_boi"))]
    if len(thieu):
        raise ValueError("%d deal mua/ban khong co huong vao/ra hop le (vd deal %s, tu '%s')"
                         % (len(thieu), int(thieu["deal"].iat[0]), thieu["huong_goc"].iat[0]))
    return ds


_LOI_TOI_THIEU = 0.2        # |loi| nho hon: sai so lam tron 0,01 chiem > 2,5% mot mau -> bo
_LOI_CHINH_XAC = 2.0        # |loi| tu day: sai so lam tron <= 0,25% -> dung de do do tan (`lech`)


def _mau_hop_dong(deals: pd.DataFrame) -> dict[str, list[tuple[float, float, float]]]:
    """Cac mau hop dong (don vi gia -> tien tai khoan) tung ma, lay tu cac lan dong KHONG MO HO: [(hop_dong_mau, loi, dg*lot)].

    Mot deal RA phia chieu s (s = chieu cua lenh bi dong = -chieu deal) co loi = s * (gia_ra - gia_vao) * lot * hop_dong.
    Chi lay mau khi luc do MOI lenh dang mo phia s deu cung MOT gia vao (nen gia vao la CHAC CHAN du dong lenh nao) va phia do
    khong bi 'nhiem' ('nhiem' = mot lan dong truoc do khong biet dong lenh nao, den khi phia s ve 0). |loi| >= 0,2 de sai so lam
    tron 0,01 khong lam lech mot mau qua 2,5% (uoc luong chung dung ti so tong nen sai so lam tron triet tieu)."""
    mau: dict[str, list[tuple[float, float, float]]] = {}
    kho: dict[tuple, list[list[float]]] = {}
    nhiem: dict[tuple, bool] = {}
    for r in _kieu_deal(deals).itertuples(index=False):
        c = 1 if r.loai == "mua" else -1
        if r.huong == "vao":
            kho.setdefault((r.ma, c), []).append([r.gia, r.lot])
            continue
        s = -c
        ds = kho.get((r.ma, s), [])
        if not ds:
            continue
        gia_vao = {round(g, 9) for g, _ in ds}
        if len(gia_vao) == 1 and not nhiem.get((r.ma, s)):
            dg = s * (r.gia - ds[0][0])
            if np.isfinite(r.loi) and abs(r.loi) >= _LOI_TOI_THIEU and abs(dg) > 0 and r.lot <= sum(l for _, l in ds) + 1e-9:
                hd = r.loi / (dg * r.lot)
                if hd > 0:
                    mau.setdefault(r.ma, []).append((hd, float(r.loi), float(dg * r.lot)))
        else:
            nhiem[(r.ma, s)] = True
        con = r.lot                                   # tru FIFO (xap xi: chi dung de biet bao gio phia nay ve 0)
        while con > 1e-9 and ds:
            t = min(ds[0][1], con)
            ds[0][1] -= t
            con -= t
            if ds[0][1] <= 1e-9:
                ds.pop(0)
        if not ds:
            nhiem[(r.ma, s)] = False
    return mau


def uoc_hop_dong(deals: pd.DataFrame, chi_tiet: bool = False) -> dict:
    """Hop dong tung ma = TI SO TONG (tong loi / tong dg*lot) cua cac mau sach sau khi bo mau lech > 20% khoi trung vi
    (>= 3 mau con lai; thieu mau -> ma khong co trong ket qua).

    chi_tiet=True -> {ma: {"hop_dong", "n", "lech"}}; `lech` = (p90 - p10) / hop_dong (tu cac mau |loi| >= 2 neu du 3 mau, khong thi
    tu tat ca): gan 0 voi cap co tien bao gia = tien tai khoan (XAUUSD tren tai khoan USD), lon (vai %) voi cap cheo vi ty gia
    quy doi doi theo thoi gian - khi do phuong trinh loi chi gan dung."""
    ra: dict = {}
    for m, v in _mau_hop_dong(deals).items():
        if len(v) < 3:
            continue
        hd_i = np.array([x[0] for x in v])
        loi = np.array([x[1] for x in v])
        dgl = np.array([x[2] for x in v])
        md = float(np.median(hd_i))
        giu = np.abs(hd_i - md) <= 0.2 * md
        if giu.sum() < 3 or dgl[giu].sum() == 0:
            continue
        hd = float(loi[giu].sum() / dgl[giu].sum())
        if not hd > 0:
            continue
        if chi_tiet:
            chinh = hd_i[giu & (np.abs(loi) >= _LOI_CHINH_XAC)]
            mau_lech = chinh if len(chinh) >= 3 else hd_i[giu]
            p10, p90 = np.percentile(mau_lech, [10, 90])
            ra[m] = {"hop_dong": hd, "n": int(giu.sum()), "lech": float((p90 - p10) / hd)}
        else:
            ra[m] = hd
    return ra


#: gia tri hop dong (don vi gia -> tien tai khoan) thuong gap: CFD chi so / dau / vang / bac / FX / ...
_HOP_DONG_UNG_VIEN = (1.0, 2.0, 5.0, 10.0, 20.0, 25.0, 50.0, 100.0, 200.0, 250.0, 500.0, 1000.0, 2000.0, 2500.0, 5000.0, 10000.0,
                      20000.0, 50000.0, 100000.0, 200000.0, 1000000.0)
_TU_HIEU_CHUAN_TOI_DA = 2500       # so dong deal dau dung de tu hieu chuan (du de thay mot cai nhat dinh, khong chay het file lon)


def hieu_chuan_hop_dong(deals: pd.DataFrame, ma: str) -> dict | None:
    """TU HIEU CHUAN hop dong cua mot ma khi khong du mau sach (`uoc_hop_dong`): ghep thu voi tung gia tri thuong gap, cai nao
    lam phuong trinh loi KHOP nhieu lenh nhat (so lenh 'loi' / 'loi_gan' tren tong khop + fifo) la hop dong dung - vi hop dong sai
    cho gia vao suy ra khong trung gia lenh nao dang mo, con hop dong dung thi khop gan het. Chi nhan khi >= 10 phep ghep co kiem
    chung, ti le khop >= 0,7 va hon cai thu hai >= 0,2 (hai gia tri gan nhau khong lam lan). Tra {"hop_dong", "lech", "n", "diem"}
    hoac None. Gia tri cuoi duoc tinh lai tu cac cap da khop (ti so tong) nen khong bi gioi han vao luoi gia tri thuong gap
    khi ty le chi lech vai %."""
    sub = deals[deals["ma"].isin((ma, ""))].head(_TU_HIEU_CHUAN_TOI_DA)
    sub.attrs = dict(deals.attrs)
    ket = []
    for cs in _HOP_DONG_UNG_VIEN:
        v = ghep_vi_the(sub, None, {ma: cs}, uoc=False)
        g = v.attrs["ghep"]
        ok, hong = g.get("loi", 0) + g.get("loi_gan", 0), g.get("fifo", 0)
        ket.append((ok / (ok + hong) if ok + hong else 0.0, ok + hong, cs, v))
    ket.sort(key=lambda x: (-x[0], -x[1]))
    diem, n, cs, v = ket[0]
    if n < 10 or diem < 0.7 or diem - ket[1][0] < 0.2:
        return None
    k = v[(v["cach_ghep"] == "loi") & v["dong"].notna()]
    dg = k["chieu"] * (k["gia_dong"] - k["gia_mo"]) * k["lot"]
    ok = (dg.abs() > 0) & (k["loi"].abs() >= _LOI_TOI_THIEU) & ((k["loi"] / dg) > 0)
    k, dg = k[ok], dg[ok]
    hd_i = (k["loi"] / dg).to_numpy(float)
    if len(hd_i) < 3:
        return {"hop_dong": cs, "lech": 0.0, "n": int(n), "diem": round(float(diem), 3)}
    md = float(np.median(hd_i))
    giu = np.abs(hd_i - md) <= 0.2 * md
    if giu.sum() < 3:
        return {"hop_dong": cs, "lech": 0.0, "n": int(n), "diem": round(float(diem), 3)}
    hd = float(k["loi"].to_numpy(float)[giu].sum() / dg.to_numpy(float)[giu].sum())
    chinh = hd_i[giu & (np.abs(k["loi"].to_numpy(float)) >= _LOI_CHINH_XAC)]
    p10, p90 = np.percentile(chinh if len(chinh) >= 3 else hd_i[giu], [10, 90])
    return {"hop_dong": hd, "lech": float((p90 - p10) / hd), "n": int(n), "diem": round(float(diem), 3)}


_LY_DO_RA = re.compile(r"^\[?\s*(sl|tp)\b[\s:]*[-+]?\d", re.I)
_STOP_OUT = re.compile(r"(?i)\bso\s*:|stop[\s_-]*out")


def ly_do_ra(cm: str) -> str:
    """Comment cua deal RA -> 'tp' / 'sl' / 'stopout' / 'ea'. MT5 tu them '[sl 1300.00]' / '[tp 1310.90]' khi may chu dong lenh
    (SL / TP dat san); 'so: 20.00% / 100.00' khi stop-out. Comment khac = EA tu dong lenh ('ea')."""
    c = (cm or "").strip()
    m = _LY_DO_RA.match(c)
    if m:
        return m.group(1).lower()
    if _STOP_OUT.search(c):
        return "stopout"
    return "ea"


_COT_VI_THE = ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "loi", "hoa_hong", "swap", "sl", "tp", "ma",
               "cm_vao", "cm_ra", "ly_do_ra", "kieu_vao", "gio_dat", "deal_vao", "deal_ra", "order_vao", "order_ra",
               "lot_vao", "cach_ghep"]


def _tra_order(orders: pd.DataFrame | None) -> dict:
    if orders is None or len(orders) == 0:
        return {}
    return {int(r.order): r for r in orders.itertuples(index=False)}


def ghep_vi_the(deals: pd.DataFrame, orders: pd.DataFrame | None = None, hop_dong: dict | float | None = None,
                uoc: bool = True) -> pd.DataFrame:
    """Bang deal (+ bang order) -> bang VI THE: moi dong la mot lan DONG (hoac phan dong) cua mot lenh. `lot` = phan do, `lot_vao` =
    lot luc mo; lenh dong tung phan cho nhieu dong cung `deal_vao`. Lenh chua dong den het du lieu: dong = NaT, gia_dong = NaN.

    Ghep (`cach_ghep`): 'ma_vi_the' (bao cao co cot Position - chinh xac), 'don' (phia do chi con mot lenh), 'loi' (phuong trinh loi
    chi ra DUNG mot lenh / cac lenh cung gia), 'cung_gia' (moi lenh dang mo cung mot gia vao: chon lenh nao cung ra cung loi, lay
    lenh mo som nhat), 'loi_gan' (nhieu gia gan nhau, lay gan nhat), 'fifo' (khong khop phuong trinh - KHONG dang tin cho tung
    lenh rieng). `hop_dong`: so (cho moi ma) hoac dict {ma: hop_dong}; thieu thi uoc luong (`uoc_hop_dong`).

    Gio, lot, gia, ly do dong, comment la du lieu DOC THANG tu bao cao; chi viec 'deal ra nay dong lenh vao nao' la suy ra.
    `uoc=False`: chi dung `hop_dong` truyen vao (khong uoc luong / tu hieu chuan) - dung noi bo cho phep tu hieu chuan."""
    ds = _kieu_deal(deals)
    tra = _tra_order(orders)
    hd: dict[str, float] = {}
    nguon_hd: dict[str, str] = {}
    if isinstance(hop_dong, dict):
        hd.update(hop_dong)
    elif hop_dong:
        hd.update({m: float(hop_dong) for m in set(ds["ma"])})
    nguon_hd.update({m: "truyen_vao" for m in hd})
    lech: dict[str, float] = {}
    if uoc:
        for m, v in uoc_hop_dong(deals, chi_tiet=True).items():
            if m not in hd:
                hd[m] = v["hop_dong"]
                nguon_hd[m] = "mau_sach"
            lech[m] = v["lech"] if np.isfinite(v["lech"]) else 0.0
        for m in sorted(set(ds["ma"]) - set(hd)):
            hc = hieu_chuan_hop_dong(deals, m)
            if hc:
                hd[m], lech[m], nguon_hd[m] = hc["hop_dong"], hc["lech"], "tu_hieu_chuan"
    goc = deals.attrs.get("digits") or {}                # so chu so thap phan IN trong bao cao (chuoi goc), neu doc tu tep
    tick = {m: 10.0 ** -(goc[m] if m in goc else _so_thap_phan(g["gia"])) for m, g in ds.groupby("ma")}
    kho: dict[tuple, _Kho] = {}
    hang: list[dict] = []
    dem = collections.Counter()
    mo_coi = 0
    co_ma = (ds["vi_the"] != "").any() if "vi_the" in ds.columns else False
    stt = 0
    theo_ma: dict[str, dict] = {}                     # chi cho che do ma vi the

    def _hang(rec, part, rr, loi, hh, sw, cach):
        o = tra.get(rec["order"])
        cm_ra = str(rr.ghi_chu or "")
        hang.append({
            "mo": rec["gio"], "dong": rr.gio, "chieu": rec["chieu"], "lot": part, "gia_mo": rec["gia"], "gia_dong": rr.gia,
            "loi": loi, "hoa_hong": hh, "swap": sw,
            "sl": float(o.sl) if o is not None and pd.notna(o.sl) else np.nan,
            "tp": float(o.tp) if o is not None and pd.notna(o.tp) else np.nan, "ma": rec["ma"],
            "cm_vao": rec["cm"], "cm_ra": cm_ra, "ly_do_ra": ly_do_ra(cm_ra),
            "kieu_vao": o.kieu if o is not None else "", "gio_dat": o.gio_dat if o is not None else pd.NaT,
            "deal_vao": rec["id"], "deal_ra": int(rr.deal), "order_vao": rec["order"], "order_ra": int(rr.order),
            "lot_vao": rec["lot0"], "cach_ghep": cach})
        dem[cach] += 1

    for r in ds.itertuples(index=False):
        c = 1 if r.loai == "mua" else -1
        k_vao = (r.ma, c)
        if r.huong in ("ra", "ra_boi", "vao_ra"):
            s = -c
            kk = kho.setdefault((r.ma, s), _Kho(tick[r.ma]))
            lot_ra = r.lot
            phan_vao = 0.0
            if r.huong == "vao_ra":                                  # dao chieu: phan dau dong lenh cu, phan du mo lenh moi
                co = kk.tong_lot()
                phan_vao = max(0.0, r.lot - co)
                lot_ra = min(r.lot, co)
            con = lot_ra
            hh_ra_tong = 0.0 if pd.isna(r.hoa_hong) else float(r.hoa_hong)
            loi_tong = 0.0 if pd.isna(r.loi) else float(r.loi)
            sw_tong = 0.0 if pd.isna(r.swap) else float(r.swap)
            while con > 1e-9:
                rec, cach = None, "fifo"
                if co_ma and r.vi_the:
                    rec = theo_ma.get(r.vi_the)
                    cach = "ma_vi_the"
                    if rec is not None and rec["id"] not in kk.rec:
                        rec = None
                if rec is None and len(kk) == 1:
                    rec, cach = kk.cu_nhat(), "don"
                if rec is None and len(kk):
                    cs = hd.get(r.ma)
                    part_thu = min(con, kk.cu_nhat(con)["lot_con"])
                    if cs and np.isfinite(r.loi) and part_thu > 0:
                        # chia loi theo ti le lot neu mot deal dong nhieu lenh (hiem)
                        loi_phan = loi_tong * part_thu / max(lot_ra, 1e-12)
                        gia_vao = r.gia - s * loi_phan / (part_thu * cs)
                        tol = (_DUNG_SAI_TIEN + (0.002 + lech.get(r.ma, 0.0)) * abs(loi_phan)) / (part_thu * cs) + tick[r.ma]
                        ung = kk.quanh_gia(gia_vao, tol, part_thu)
                        if ung:
                            gan = min(ung, key=lambda x: (abs(x["gia"] - gia_vao), x["stt"]))
                            trung = [x for x in ung if abs(x["gia"] - gan["gia"]) < 1e-9]
                            rec = trung[0]
                            cach = "loi" if len(ung) == len(trung) else "loi_gan"
                if rec is None and len(kk):
                    gia_dang_mo = {kk.khoa(x["gia"]) for x in kk.rec.values()}
                    if len(gia_dang_mo) == 1:                        # moi lenh dang mo cung MOT gia vao: chon lenh nao cung ra cung loi
                        rec, cach = kk.cu_nhat(con), "cung_gia"
                if rec is None:
                    rec = kk.cu_nhat(con)
                    cach = "fifo"
                if rec is None:                                      # lenh ra ma khong co lenh nao dang mo
                    mo_coi += 1
                    break
                part = min(rec["lot_con"], con)
                ty = part / max(lot_ra, 1e-12)
                hh = rec["hh_vao"] * part / rec["lot0"] + hh_ra_tong * ty
                _hang(rec, part, r, loi_tong * ty, hh, sw_tong * ty, cach)
                rec["lot_con"] -= part
                con -= part
                if rec["lot_con"] <= 1e-9:
                    kk.bo(rec["id"])
                    theo_ma.pop(str(rec.get("ma_vt", "")), None)
            if phan_vao > 1e-9:                                      # phan mo moi cua deal dao chieu
                stt += 1
                kho.setdefault((r.ma, c), _Kho(tick[r.ma])).them(
                    {"id": int(r.deal), "stt": stt, "gio": r.gio, "gia": r.gia, "lot0": phan_vao, "lot_con": phan_vao,
                     "hh_vao": 0.0, "order": int(r.order), "cm": str(r.ghi_chu or ""), "ma": r.ma, "chieu": c,
                     "ma_vt": r.vi_the})
        else:                                                         # vao
            stt += 1
            rec = {"id": int(r.deal), "stt": stt, "gio": r.gio, "gia": r.gia, "lot0": r.lot, "lot_con": r.lot,
                   "hh_vao": 0.0 if pd.isna(r.hoa_hong) else float(r.hoa_hong), "order": int(r.order),
                   "cm": str(r.ghi_chu or ""), "ma": r.ma, "chieu": c, "ma_vt": r.vi_the}
            kho.setdefault(k_vao, _Kho(tick[r.ma])).them(rec)
            if co_ma and r.vi_the:
                theo_ma[r.vi_the] = rec
    # lenh con mo den het du lieu
    for (m, ch), kk in kho.items():
        for rec in kk.rec.values():
            o = tra.get(rec["order"])
            hang.append({"mo": rec["gio"], "dong": pd.NaT, "chieu": ch, "lot": rec["lot_con"], "gia_mo": rec["gia"],
                         "gia_dong": np.nan, "loi": np.nan, "hoa_hong": rec["hh_vao"] * rec["lot_con"] / rec["lot0"], "swap": np.nan,
                         "sl": float(o.sl) if o is not None and pd.notna(o.sl) else np.nan,
                         "tp": float(o.tp) if o is not None and pd.notna(o.tp) else np.nan, "ma": m,
                         "cm_vao": rec["cm"], "cm_ra": "", "ly_do_ra": "", "kieu_vao": o.kieu if o is not None else "",
                         "gio_dat": o.gio_dat if o is not None else pd.NaT, "deal_vao": rec["id"], "deal_ra": 0,
                         "order_vao": rec["order"], "order_ra": 0, "lot_vao": rec["lot0"], "cach_ghep": "chua_dong"})
            dem["chua_dong"] += 1
    v = pd.DataFrame(hang, columns=_COT_VI_THE)
    v = v.sort_values(["mo", "deal_vao", "deal_ra"], kind="stable").reset_index(drop=True)
    v["mo"] = pd.to_datetime(v["mo"])
    v["dong"] = pd.to_datetime(v["dong"])
    v["chieu"] = v["chieu"].astype(int)
    non = deals[~deals["loai"].isin(("mua", "ban"))]
    nap_rut = [[str(t)[:19], float(x)] for t, x in zip(non["gio"], non["loi"]) if pd.notna(x) and x != 0]
    v.attrs.update({"ghep": dict(dem), "mo_coi": int(mo_coi), "hop_dong": hd, "nap_rut": nap_rut, "so_deal": int(len(deals)),
                    "kiem_so_du": kiem_so_du(deals), "da_chuan_hoa": False, "tick": tick, "lech_hop_dong": lech,
                    "hop_dong_nguon": nguon_hd})
    if len(nap_rut) and nap_rut[0][1] > 0:
        v.attrs["von_dau"] = nap_rut[0][1]
    mas = sorted(set(v["ma"]))
    v.attrs["pip"] = BL.doan_pip(mas[0] if mas else "", float(v["gia_mo"].median()) if len(v) else None)
    return v


def gop_theo_lenh(v: pd.DataFrame) -> pd.DataFrame:
    """Gop cac dong dong-tung-phan cung `deal_vao` thanh MOT dong / lenh (lot cong, gia dong binh quan theo lot, dong = lan cuoi,
    loi / hoa hong / swap cong). Dung cho phan tich theo tang (buoc, lot); phan tich THOAT dung bang goc."""
    if v.empty:
        return v
    g = v.groupby("deal_vao", sort=False)
    dong_het = g["dong"].apply(lambda s: s.notna().all())
    ra = g.agg(mo=("mo", "first"), chieu=("chieu", "first"), lot=("lot", "sum"), gia_mo=("gia_mo", "first"), ma=("ma", "first"),
               cm_vao=("cm_vao", "first"), kieu_vao=("kieu_vao", "first"), gio_dat=("gio_dat", "first"),
               sl=("sl", "first"), tp=("tp", "first"), lot_vao=("lot_vao", "first"), order_vao=("order_vao", "first"),
               so_lan_dong=("deal_ra", lambda s: int((s > 0).sum())), loi=("loi", lambda s: float(s.sum(min_count=1))),
               hoa_hong=("hoa_hong", "sum"), swap=("swap", lambda s: float(s.sum(min_count=1))),
               dong=("dong", "max"), cm_ra=("cm_ra", "last"), ly_do_ra=("ly_do_ra", "last"))
    w = v.assign(_gw=v["gia_dong"] * v["lot"]).groupby("deal_vao", sort=False)
    ra["gia_dong"] = (w["_gw"].sum(min_count=1) / g["lot"].sum()).where(dong_het)
    ra["dong"] = ra["dong"].where(dong_het)
    ra = ra.reset_index()
    ra["dong"] = pd.to_datetime(ra["dong"])
    ra = ra.sort_values(["mo", "deal_vao"], kind="stable").reset_index(drop=True)
    ra.attrs.update(v.attrs)
    return ra


def lenh_cho_boc(v: pd.DataFrame) -> pd.DataFrame:
    """Bang vi the -> bang lenh CHUAN cua `boc_lich_su` (cot mo, dong, chieu, lot, gia_mo, gia_dong, loi, hoa_hong, swap, sl, tp, ma;
    `attrs`: pip, so_bo, nap_rut), moi LENH mot dong (gop dong tung phan). Dua thang vao `boc_lich_su.phan_tich_lenh`."""
    g = gop_theo_lenh(v)
    cot = ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "loi", "hoa_hong", "swap", "sl", "tp", "ma"]
    c = BL.chuan_hoa(g[cot], pip=v.attrs.get("pip"))
    c.attrs["nap_rut"] = v.attrs.get("nap_rut", [])
    return c


# ============================================================== 4. MOT CUA
def vi_the_tu_tep(duong, orders_csv=None, hop_dong=None, bang_loai: dict | None = None) -> pd.DataFrame:
    """Tep bao cao (.htm) hoac CSV deal (+ tuy chon CSV order mau) -> bang vi the, kem `attrs`: inputs, canh_bao, kiem_so_du."""
    r = doc_tep(duong, bang_loai)
    orders = r.get("orders")
    if orders_csv:
        orders = doc_orders_csv(orders_csv)
    v = ghep_vi_the(r["deals"], orders, hop_dong)
    v.attrs["inputs"] = r.get("inputs", {})
    v.attrs["canh_bao"] = list(r.get("canh_bao", []))
    v.attrs["tom_tat_mt5"] = r.get("tom_tat_mt5")
    return v
