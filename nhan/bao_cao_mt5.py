# -*- coding: utf-8 -*-
"""bao_cao_mt5 - doc bao cao MT5 Strategy Tester (.htm cua MOT lan chay) thanh SO.

VAI TRO: tang ham duy nhat bien file bao cao cua tester thanh dict so, de lan
EA tho (`ea_tho`) cham cong lai + maxDD < 80% bang CODE. Thuan Python, khong cham
MT5 nen test duoc tren Linux.

## Vi sao viet lai thay vi dung `chay_tester_z5.doc_bao_cao`

Ham cu tim CHUOI CON bang regex tren van ban da bo het the HTML va tra CHUOI
("1 234.56 (12.3%)"), khong tra so; thieu mot nhan thi KHONG bao loi ma bo qua
khoa do (nguoi goi doc `dict.get` ra None roi coi nhu 0). Hai bay da cat tay:
  * ban tieng Viet goi Gross Profit la "Loi nhuan rong" va lai THAT la "Tong loi
    nhuan rong" - tim chuoi con "loi nhuan rong" lay nham lech 13,5 lan;
  * mot bao cao do dang (tester chet giua chung) van duoc ghi, voi 0 lenh, PF 0,
    DD 0 - doc y het mot he khong bao gio vao lenh.
Nen o day: khop **nguyen mot O** (khong khop chuoi con), thieu truong BAT BUOC thi
`doc_duoc=False` va liet ke `thieu` (nguoi goi tra CHUA_DO_DUOC, khong bao gio AM),
va moi con so qua `so()` (khoang trang nghin / nbsp / dau phay thap phan / ngoac).

## Chua kiem voi bao cao THAT

Nhan tieng Anh theo tai lieu MT5; nhan tieng Viet CHI lay nhung nhan co trong
`chay_tester_z5.NHAN` (da dung tren may nha 13/09) - khong doan them. Test o day dung
mau tong hop dung bo cuc do. Mau that dau tien tu may nha
phai duoc them vao `test_bao_cao_mt5.py` (muc fixture) truoc khi tin cac nhan con
lai. Nhan la ban ngu khac thi `nhan_them=` bo sung ma khong sua code.
"""
from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path

#: Dau hieu tester KHONG CHAY DUOC (do that 06/09/2026, xem `chay_tester_z5`): bao cao van
#: duoc ghi voi 0 lenh nen phai do log agent, khong the do bao cao.
DAU_HIEU_HONG = ("cannot generate history data", "0 ticks, 0 bars generated",
                 "not enough memory", "no history data")

#: khoa -> (kieu, cac nhan). Kieu: so | tien_pct (so tien + % trong ngoac) | dem_pct | chu.
#: So sanh voi O DA CHUAN HOA (NFC, casefold, bo dau hai cham cuoi, bo khoang trang thua);
#: nhan co chu thich trong ngoac ("Profit Trades (% of total)") khop them bang phan truoc ngoac.
TRUONG = {
    "lai_rong": ("so", ("Total Net Profit", "Tổng lợi nhuận ròng")),
    "lai_tho": ("so", ("Gross Profit", "Lợi nhuận ròng")),
    "lo_tho": ("so", ("Gross Loss", "Lỗ ròng")),
    "pf": ("so", ("Profit Factor", "Hệ số lợi nhuận")),
    "ky_vong": ("so", ("Expected Payoff",)),
    "phuc_hoi": ("so", ("Recovery Factor",)),
    "sharpe": ("so", ("Sharpe Ratio", "Tỷ lệ Sharpe")),
    "so_lenh": ("so", ("Total Trades", "Tổng giao dịch")),
    "so_deal": ("so", ("Total Deals",)),
    "von": ("so", ("Initial Deposit",)),
    "bars": ("so", ("Bars",)),
    "ticks": ("so", ("Ticks",)),
    "chat_luong_pct": ("so", ("History Quality",)),
    "dd_von_toi_da": ("tien_pct", ("Equity Drawdown Maximal", "Sụt giảm vốn sở hữu tối đa")),
    "dd_von_tuong_doi": ("tien_pct", ("Equity Drawdown Relative",)),
    "dd_so_du_toi_da": ("tien_pct", ("Balance Drawdown Maximal",)),
    "dd_so_du_tuong_doi": ("tien_pct", ("Balance Drawdown Relative",)),
    "thang": ("dem_pct", ("Profit Trades", "Giao dịch có lợi nhuận")),
    "thua": ("dem_pct", ("Loss Trades",)),
    "expert": ("chu", ("Expert",)),
    "symbol": ("chu", ("Symbol",)),
    "ky": ("chu", ("Period",)),
}
#: Thieu mot trong cac truong nay -> khong phan quyet duoc, KHONG phai 0. `von` khong bat buoc: nguoi
#: goi biet no tu .ini (Deposit=), nen mot ban ngu chua co mau khong lam hong ca bao cao.
BAT_BUOC = ("lai_rong", "so_lenh")


def _chuan(s: str) -> str:
    s = unicodedata.normalize("NFC", html.unescape(str(s)))
    s = re.sub(r"\s+", " ", s).strip()
    return s.rstrip(":").strip().casefold()


def _bo_ngoac(s: str) -> str:
    return re.sub(r"\s*\(.*$", "", s).strip()


def _bang_nhan(nhan_them: dict | None = None) -> dict:
    ra: dict = {}
    for khoa, (kieu, nhan) in TRUONG.items():
        for n in nhan:
            ra[_chuan(n)] = (khoa, kieu)
    for khoa, nhan in (nhan_them or {}).items():
        kieu = TRUONG[khoa][0] if khoa in TRUONG else "so"
        for n in ([nhan] if isinstance(nhan, str) else nhan):
            ra[_chuan(n)] = (khoa, kieu)
    return ra


# ------------------------------------------------------------------ DOC FILE
def doc_van_ban(f) -> str:
    """Doc file bao cao theo BOM / dang UTF-16 (MT5 ghi UTF-16 LE co BOM); khong thi UTF-8, cp1252."""
    b = Path(f).read_bytes()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return b.decode("utf-16", errors="ignore")
    if b[:3] == b"\xef\xbb\xbf":
        return b[3:].decode("utf-8", errors="ignore")
    if b and b[:400].count(b"\x00") > len(b[:400]) // 4:        # UTF-16 khong BOM
        return b.decode("utf-16-le", errors="ignore")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252", errors="ignore")


def tach_o(van: str) -> list[str]:
    """Danh sach O khong rong theo thu tu tai lieu (the HTML da bo, entity da giai)."""
    van = re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", " ", van)
    # the o / khoi (mo va dong) la RANH GIOI O; the dong dong (b, i, font, span, a) bo di ma khong cat chu.
    # Chu nam ngoai o (tieu de, div) khong duoc dinh vao o dau tien cua bang.
    van = re.sub(r"(?i)</?(?:td|th|tr|table|tbody|thead|div|p|br|title|head|body|html|h[1-6]|li|ul|ol)\b[^>]*>",
                 "\n", van)
    van = re.sub(r"<[^>]*>", "", van)
    van = html.unescape(van)
    return [re.sub(r"\s+", " ", c).strip() for c in van.split("\n")
            if c.strip()]


# --------------------------------------------------------------------- SO
_SO = re.compile(r"([-+]?)(\d{1,3}(?:[., ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(\s*%)?")


def _thanh_so(chuoi: str) -> float:
    s = chuoi.replace(" ", "")
    if "." in s and "," in s:
        thap_phan = "." if s.rfind(".") > s.rfind(",") else ","
        nghin = "," if thap_phan == "." else "."
        s = s.replace(nghin, "").replace(thap_phan, ".")
    elif "," in s:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    return float(s)


def cac_so(o: str) -> list[tuple[float, bool]]:
    """Moi so trong o -> (gia tri, co dau %). 'So thuc' dung dau tru ASCII va dau tru Unicode."""
    o = re.sub(r"\s+", " ", o.replace(chr(0x2212), "-"))     # dau tru Unicode; nbsp -> khoang trang
    ra = []
    for m in _SO.finditer(o):
        try:
            v = _thanh_so(m.group(2))
        except ValueError:
            continue
        ra.append((-v if m.group(1) == "-" else v, bool(m.group(3))))
    return ra


def so(o: str) -> float | None:
    """So dau tien trong o ('10 000.00' -> 10000.0; '1 234.56 (12.3%)' -> 1234.56); None neu khong co."""
    xs = cac_so(o)
    return xs[0][0] if xs else None


def _gia_tri(o: str, kieu: str):
    if kieu == "chu":
        return o
    xs = cac_so(o)
    if not xs:
        return None
    if kieu == "so":
        return xs[0][0]
    pct = next((v for v, p in xs if p), None)
    sl = next((v for v, p in xs if not p), None)
    if kieu == "dem_pct":
        return {"so": sl, "pct": pct}
    return {"tien": sl, "pct": pct}              # tien_pct


# ----------------------------------------------------------------- PHAN TICH
def phan_tich(van: str, nhan_them: dict | None = None) -> dict:
    """Bao cao -> dict so. Truong thieu KHONG co trong dict; `thieu` liet ke truong BAT BUOC con thieu.

    Ra: lai_rong, so_lenh, von, pf, ky_vong, ... , `dd_pct` (= phan tram DD von LON NHAT trong cac cach
    tinh co mat, de thua con hon de lot), `khung` / `tu` / `den` tach tu o Period, `doc_duoc`, `thieu`.
    """
    bang = _bang_nhan(nhan_them)
    o = tach_o(van)
    chuan = [_chuan(x) for x in o]
    ra: dict = {}
    for i, c in enumerate(chuan):
        k = bang.get(c) or bang.get(_bo_ngoac(c))
        if not k or k[0] in ra or i + 1 >= len(o):
            continue
        j = i + 1
        if chuan[j] in bang or _bo_ngoac(chuan[j]) in bang:      # o ke tiep la mot nhan: truong nay trong
            continue
        v = _gia_tri(o[j], k[1])
        if v is not None:
            ra[k[0]] = v
    ky = ra.pop("ky", None)
    if isinstance(ky, str):
        m = re.search(r"\b(M\d+|H\d+|D1|W1|MN1)\b\s*\(\s*(\d{4}\.\d{2}\.\d{2})\s*-\s*(\d{4}\.\d{2}\.\d{2})", ky)
        if m:
            ra["khung"], ra["tu"], ra["den"] = m.group(1), m.group(2), m.group(3)
        else:
            ra["ky_tho"] = ky
    dd = [v["pct"] for k, v in ra.items()
          if k.startswith("dd_von_") and isinstance(v, dict) and v.get("pct") is not None]
    if dd:
        ra["dd_pct"] = max(dd)
    thieu = [k for k in BAT_BUOC if k not in ra]
    if "dd_pct" not in ra:
        thieu.append("dd_von")
    ra["thieu"] = thieu
    ra["doc_duoc"] = not thieu
    return ra


def doc_bao_cao(f, nhan_them: dict | None = None) -> dict:
    """Doc file bao cao. Khong co file / khong doc duoc -> `doc_duoc=False` va `loi`, khong nem."""
    try:
        van = doc_van_ban(f)
    except OSError as e:
        return {"doc_duoc": False, "thieu": list(BAT_BUOC), "loi": "khong doc duoc %s: %s" % (f, e)}
    ra = phan_tich(van, nhan_them)
    ra["file"] = str(f)
    return ra


# ---------------------------------------------------------------------- LOG
def phan_log_luot_cuoi(van_log: str) -> str:
    """Cat log agent tu lan 'MetaTester 5 started' CUOI: agent ghi noi tiep theo ngay nen loi cua luot
    truoc lam moi luot sau bi bao hong oan."""
    i = van_log.rfind("MetaTester 5 started")
    return van_log[i:] if i > 0 else van_log


def dau_hieu_hong(van_log: str) -> str:
    """Chuoi ly do neu log cho thay tester KHONG chay duoc; rong neu khong thay dau hieu."""
    van = phan_log_luot_cuoi(van_log or "").lower()
    for d in DAU_HIEU_HONG:
        if d in van:
            return "TESTER KHONG CHAY DUOC: " + d
    return ""
