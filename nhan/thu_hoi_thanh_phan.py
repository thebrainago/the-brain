# -*- coding: utf-8 -*-
"""thu_hoi_thanh_phan.py - GIU LAI PHAN DUNG DUOC CUA MOT HE THONG BI LOAI.

VI SAO CO FILE NAY (chu du an chot 01/09/2026).

Cho toi hom nay, mot he thong khong qua cong thi bien mat khong dau vet: phan
quyet FAIL duoc ghi vao `ket_qua`, con BAN THAN cai he - nhung duong, nhung
nguong, nhung bo loc no dung - thi khong ai giu lai. Nhung mot he thong toi
KHONG co nghia la moi manh cua no deu toi.

Vi du chu du an dua ra, va no la vi du da lam that: **Sonic R**. Ca sau ban
strategy deu khong dung duoc don lap - bon ban khong co cat lo, ban Renko khong
tai lap duoc, cau hinh von tao don bay ~50 lan nen duong von vo nghia. Nhung
`SONIC_R_PHAN_TICH.md` va `sonic_r.py` giu lai duoc phan that su co gia tri:

    dai PAC = EMA34 tren high / low / close · EMA89 lam duong xu huong
    · linreg(89) diem cuoi · TRANG THAI (huong doi) cua histogram MACD
    · Hull MA 377 lam bo loc che do · Donchian 55 dung theo chieu FADE

Sau manh do di vao he nhu THAM SO va BO LOC, doc lap voi viec Sonic R thang hay
thua. Do la viec ma file nay lam tu dong, cho MOI ban doc - ke ca (nhat la) ban
doc cua nhung he da bi loai.

RANH GIOI. Giong `ma_nguon.py`: **khong bao gio chay ma tai ve**. O day chi doc
van ban bang bieu thuc chinh quy va rut ra bo ba (chi bao, tham so, nguon gia).
Khong `exec`, khong bien dich, khong sinh ma moi. Mot thanh phan rut duoc la
UNG VIEN TOAN HANG, khong phai mot quyet dinh.

Va cai thu hai file nay tra loi, quan trong ngang cai thu nhat: **thanh phan nao
ngu phap hien tai KHONG dien dat duoc**. Do la danh sach toan hang can them, do
tu ma nguoi ta that su viet chu khong tu phong doan.
"""
from __future__ import annotations

import json
import re

from nhan import ngu_phap as NP
from nhan import so as SO

#: Nguon gia cua Pine -> cot trong khung du lieu cua ta. `hl2`/`hlc3`/`ohlc4`
#: khong phai mot cot ma la mot phep tinh, nen giu nguyen ten va danh dau la
#: KHONG dien dat truc tiep duoc.
_GIA_PINE = {"close": "close", "open": "open", "high": "high", "low": "low",
             "src": "close", "price": "close", "hl2": "hl2", "hlc3": "hlc3",
             "ohlc4": "ohlc4", "volume": "tick_volume"}

#: MQL5 `ENUM_APPLIED_PRICE`.
_GIA_MQL = {"PRICE_CLOSE": "close", "PRICE_OPEN": "open", "PRICE_HIGH": "high",
            "PRICE_LOW": "low", "PRICE_MEDIAN": "hl2", "PRICE_TYPICAL": "hlc3",
            "PRICE_WEIGHTED": "ohlc4"}

#: MQL5 `ENUM_MA_METHOD` -> ten chi bao cua ta.
_MA_MQL = {"MODE_SMA": "sma", "MODE_EMA": "ema", "MODE_SMMA": "smma",
           "MODE_LWMA": "wma"}

#: Chi bao Pine: ten -> (ten chuan, so tham so SO dau tien can giu).
#: `ta.` la tien to cua Pine v5; v2-v4 goi tran nen tien to la tuy chon.
_PINE = {
    "ema": ("ema", 1), "sma": ("sma", 1), "wma": ("wma", 1), "rma": ("smma", 1),
    "hma": ("hull", 1), "vwma": ("vwma", 1),
    "rsi": ("rsi", 1), "atr": ("atr", 1), "cci": ("cci", 1), "mfi": ("mfi", 1),
    "stdev": ("do_lech", 1), "variance": ("phuong_sai", 1),
    "highest": ("cao_nhat", 1), "lowest": ("thap_nhat", 1),
    "linreg": ("linreg", 2), "correlation": ("tuong_quan", 1),
    "mom": ("dong_luong", 1), "roc": ("doi_pct", 1), "change": ("doi", 1),
    "macd": ("macd", 3), "bb": ("bollinger", 2), "bbw": ("bollinger_rong", 2),
    "stoch": ("stochastic", 1), "supertrend": ("supertrend", 2),
    "sar": ("sar", 3), "vwap": ("vwap", 0),
    "adx": ("adx", 1), "dmi": ("dmi", 1), "cmo": ("cmo", 1), "tsi": ("tsi", 2),
    "wpr": ("williams_r", 1), "obv": ("obv", 0),
}

#: Chi bao MQL5: ham -> (ten chuan, co tham so `period` dang so hay khong).
_MQL = {
    "iRSI": ("rsi", True), "iATR": ("atr", True), "iCCI": ("cci", True),
    "iMomentum": ("dong_luong", True), "iStdDev": ("do_lech", True),
    "iBands": ("bollinger", True), "iADX": ("adx", True), "iAO": ("ao", False),
    "iMFI": ("mfi", True), "iWPR": ("williams_r", True),
    "iDeMarker": ("demarker", True), "iForce": ("force", True),
    "iOBV": ("obv", False), "iSAR": ("sar", True),
    "iStochastic": ("stochastic", True), "iMACD": ("macd", True),
    "iEnvelopes": ("envelopes", True), "iFractals": ("fractals", False),
    "iIchimoku": ("ichimoku", True),
}

#: Toan hang ngu phap hien co (`nhan/ngu_phap.py::toan_hang`). Cai gi khong nam
#: trong day thi rut ve duoc nhung CHUA dien dat duoc - va do la thong tin can
#: bao chu khong phai ly do de vut.
#: Cap nhat 01/09 sau khi them toan hang. Ba nhom:
#:  - san co tu truoc
#:  - THEM MOI: wma, smma, cci, stochastic, obv, adx, tuong_quan, phuong_sai,
#:    tuyen_tinh - chon theo SO LAN do duoc trong ma that, khong theo cam giac
#:  - GHEP DUOC ma khong can toan hang rieng: `macd` = tuyen_tinh([ema_nhanh,
#:    ema_cham], [1,-1]) · `bollinger` = tuyen_tinh([tb, do_lech], [1, ±k]) ·
#:    `dong_luong` = `doi`. Ba cai nay cong 186 lan xuat hien ma khong ton mot
#:    dong trinh thong dich nao - chung tung bi cham "khong dien dat duoc" chi
#:    vi bang nay chua duoc cap nhat sau khi `tuyen_tinh` ra doi.
#: Nhap TU NGU PHAP, khong chep lai. Ban chep tay truoc day lech ca hai chieu:
#: khai thua macd/bollinger/dong_luong (nen bang "con thieu" giau dung ba toan
#: hang duoc dung nhieu nhat) va khai thieu 6 toan tu co that (nen thanh phan
#: dung chung bi vut). Xem `ngu_phap.CHI_BAO_CO`.
_DIEN_DAT_DUOC = NP.CHI_BAO_CO
_NHAN_COT = NP.CHI_BAO_NHAN_COT

#: Tien to cua ly do "ngu phap KHONG CO toan hang nay". Phan biet voi ly do
#: "co toan hang nhung bien the nay chua nhan duoc" (`atr` tren `hl2` chang
#: han): cai dau doi mot toan hang MOI, cai sau chi doi noi rong cai da co.
#: Tach ra vi hai viec do khac han nhau ve cong suc va ve uu tien.
THIEU_TOAN_HANG = "ngu phap chua co toan hang"

_SO = r"[-+]?\d+(?:\.\d+)?"


#: Gan bien mang gia tri so. Bat ca `n = 34`, `n = input(34)`,
#: `n = input.int(34, ...)`, `n = input(defval=34, ...)`.
#: Tien to KIEU cua mot khai bao C/MQL5 (`input int Chu_ky = 14;`). Khong cho
#: phep tien to nay thi moi input cua EA MQL5 deu vo hinh voi bang bien, va
#: `iMA(NULL,0,InpChuKy,...)` mat chu ky -> chi bao bi bo vi "thieu chu ky".
_KIEU_C = (r"(?:(?:static|const|extern|input|sinput|virtual)[ \t]+)*"
           r"(?:bool|char|uchar|short|ushort|int|uint|long|ulong|float|double"
           r"|datetime|color|string)[ \t]+")

_GAN = re.compile(
    rf"^[ \t]*(?:{_KIEU_C})?([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*"
    r"(?:input(?:\.[a-z]+)?[ \t]*\(\s*(?:defval\s*=\s*)?)?"
    r"([-+]?\d+(?:\.\d+)?)", re.M)


def _bang_bien(vb: str) -> list[tuple[int, str, float]]:
    """Danh sach (vi tri, ten, gia tri) theo THU TU XUAT HIEN.

    Phai theo vi tri chu khong phai mot tu dien phang: mot file tai ve thuong la
    NHIEU script noi duoi nhau, va cung mot ten mang gia tri khac nhau o moi
    ban. Trong `pineturtle.txt` cua Sonic R, `PeriodLookBack` la 34 o ban nay va
    55 o ban khac. Phang hoa thi mot trong hai so bien mat.
    """
    return [(m.start(), m.group(1), float(m.group(2))) for m in _GAN.finditer(vb)]


def _giai_bien(x: str, vi_tri: int, bang: list) -> float | None:
    """Gia tri cua mot doi so: so tho, hoac lan gan GAN NHAT TRUOC `vi_tri`."""
    x = x.strip()
    if re.fullmatch(_SO, x):
        return float(x)
    # `input(6)` VIET THANG trong doi so, khong qua mot bien trung gian:
    # `ema(DX, input(6))`. Khong bat thi chu ky mat va ca chi bao rot.
    m_in = re.fullmatch(rf"input(?:\.[a-z]+)?\s*\(\s*(?:defval\s*=\s*)?({_SO})[^)]*\)", x)
    if m_in:
        return float(m_in.group(1))
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", x):
        return None
    gt = None
    for pos, ten, v in bang:
        if pos >= vi_tri:
            break
        if ten == x:
            gt = v
    return gt


def _so_dau(doi_so: list[str], k: int, vi_tri: int = 0,
            bang: list | None = None) -> list[float]:
    """`k` gia tri so dau tien, GIAI CA BIEN chu khong chi lay so tho.

    Truoc khi co buoc giai bien, ham nay tra `[]` cho gan het Sonic R: ma that
    viet `ema(high, HiLoLen)` chu khong viet `ema(high, 34)`, nen dung cac con
    so dang gia tri nhat (34 / 89 / 55 / 377) deu rot mat.
    """
    ra: list[float] = []
    for x in doi_so:
        v = _giai_bien(x, vi_tri, bang or [])
        if v is None:
            continue
        # Gia tri DAU TIEN luon la CHU KY, va chu ky < 1 la vo nghia. Khong chan
        # thi `iMA(sym, tf, period, shift, ...)` voi `period` la bien khong giai
        # duoc se lay nham `shift = 0` va sinh ra nhung dong `ema [0.0]` trong
        # kho - trong nhu mot tham so that. Cac vi tri sau thi 0 hop le (vi du
        # doi so `offset` cua `linreg`).
        if not ra and v < 1:
            continue
        ra.append(v)
        if len(ra) >= k:
            break
    return ra


def _tach_doi_so(s: str) -> list[str]:
    """Tach theo dau phay o MUC NGOAI CUNG (khong cat trong ngoac long nhau)."""
    ra, sau, muc = [], 0, 0
    for i, c in enumerate(s):
        if c in "([":
            muc += 1
        elif c in ")]":
            muc -= 1
        elif c == "," and muc == 0:
            ra.append(s[sau:i])
            sau = i + 1
    ra.append(s[sau:])
    return ra


def _khoi_ngoac(vb: str, mo: int) -> str:
    """Noi dung trong cap ngoac bat dau tai `mo` (la vi tri cua '(')."""
    muc, i = 0, mo
    while i < len(vb):
        if vb[i] == "(":
            muc += 1
        elif vb[i] == ")":
            muc -= 1
            if muc == 0:
                return vb[mo + 1:i]
        i += 1
    return ""


def rut_pine(vb: str) -> list[dict]:
    """Bo ba (chi bao, tham so, nguon gia) rut tu Pine Script."""
    ra = []
    bang = _bang_bien(vb)
    mau = "|".join(map(re.escape, sorted(_PINE, key=len, reverse=True)))
    for m in re.finditer(rf"(?:\bta\.)?\b({mau})\s*\(", vb):
        chuan, so_ts = _PINE[m.group(1)]
        trong = _khoi_ngoac(vb, m.end() - 1)
        ds = _tach_doi_so(trong) if trong.strip() else []
        cot = None
        for x in ds:
            k = x.strip().lower()
            if k in _GIA_PINE:
                cot = _GIA_PINE[k]
                break
        ra.append({"chi_bao": chuan,
                   "tham_so": _so_dau(ds, so_ts, m.start(), bang) if so_ts else [],
                   "cot": cot, "ngon_ngu": "pine",
                   "trich": (m.group(0) + trong + ")")[:120]})
    return ra


def rut_mql(vb: str) -> list[dict]:
    """Bo ba rut tu MQL4/5. `iMA` tach rieng vi phuong phap nam trong doi so."""
    ra = []
    bang = _bang_bien(vb)
    for m in re.finditer(r"\biMA\s*\(", vb):
        trong = _khoi_ngoac(vb, m.end() - 1)
        ds = [x.strip() for x in _tach_doi_so(trong)]
        pp = next((_MA_MQL[x] for x in ds if x in _MA_MQL), "ma")
        cot = next((_GIA_MQL[x] for x in ds if x in _GIA_MQL), None)
        ra.append({"chi_bao": pp, "tham_so": _so_dau(ds, 1, m.start(), bang), "cot": cot,
                   "ngon_ngu": "mql", "trich": (m.group(0) + trong + ")")[:120]})
    mau = "|".join(map(re.escape, sorted(_MQL, key=len, reverse=True)))
    for m in re.finditer(rf"\b({mau})\s*\(", vb):
        chuan, co_period = _MQL[m.group(1)]
        trong = _khoi_ngoac(vb, m.end() - 1)
        ds = [x.strip() for x in _tach_doi_so(trong)]
        cot = next((_GIA_MQL[x] for x in ds if x in _GIA_MQL), None)
        ra.append({"chi_bao": chuan,
                   "tham_so": _so_dau(ds, 3, m.start(), bang) if co_period else [],
                   "cot": cot, "ngon_ngu": "mql",
                   "trich": (m.group(0) + trong + ")")[:120]})
    return ra



#: Phuong ngu PYTHON/pandas. Day la kho LON NHAT trong thu vien (do 01/09: 234
#: ban doc python so voi 43 pine va 21 mql), va no viet truc tiep hon MQL nhieu:
#: `df["close"].rolling(20).mean()` khong mo ho gi.
_PY_ROLL = re.compile(
    r"\.rolling\(\s*(?:window\s*=\s*)?(\d+)[^)]*\)\s*\.\s*(mean|max|min|std|sum)\s*\(")
_PY_EWM = re.compile(r"\.ewm\(\s*span\s*=\s*(\d+)[^)]*\)\s*\.\s*mean\s*\(")
_PY_HAM = {
    "rsi": ("rsi", 1), "RSI": ("rsi", 1), "atr": ("atr", 1), "ATR": ("atr", 1),
    "sma": ("sma", 1), "SMA": ("sma", 1), "ema": ("ema", 1), "EMA": ("ema", 1),
    "wma": ("wma", 1), "WMA": ("wma", 1), "stdev": ("do_lech", 1),
    "MACD": ("macd", 3), "macd": ("macd", 3), "ADX": ("adx", 1),
    "CCI": ("cci", 1), "MOM": ("dong_luong", 1), "OBV": ("obv", 0),
    "BBANDS": ("bollinger", 2), "bbands": ("bollinger", 2),
}
_PY_CUA = {"mean": "sma", "max": "cao_nhat", "min": "thap_nhat",
           "std": "do_lech", "sum": "tong"}
#: Cot gia trong pandas: `df["close"]`, `df.close`, `data['Close']`.
_PY_COT = re.compile(r"""(?:\[\s*['"](\w+)['"]\s*\]|\.(\w+))\s*$""")


def _cot_python(truoc: str) -> str | None:
    """Doan cot gia tu doan van ban NGAY TRUOC loi goi."""
    m = _PY_COT.search(truoc.strip())
    if not m:
        return None
    ten = (m.group(1) or m.group(2) or "").lower()
    return ten if ten in ("open", "high", "low", "close", "volume") else None


def rut_python(vb: str) -> list[dict]:
    """Bo ba rut tu ma Python/pandas (pandas-ta, talib, rolling/ewm)."""
    ra = []
    bang = _bang_bien(vb)
    for m in _PY_ROLL.finditer(vb):
        n, phep = int(m.group(1)), m.group(2)
        cb = _PY_CUA.get(phep)
        if not cb:
            continue
        ra.append({"chi_bao": cb, "tham_so": [float(n)],
                   "cot": _cot_python(vb[max(0, m.start() - 60):m.start()]),
                   "ngon_ngu": "python", "trich": m.group(0)[:120]})
    for m in _PY_EWM.finditer(vb):
        ra.append({"chi_bao": "ema", "tham_so": [float(m.group(1))],
                   "cot": _cot_python(vb[max(0, m.start() - 60):m.start()]),
                   "ngon_ngu": "python", "trich": m.group(0)[:120]})
    mau = "|".join(map(re.escape, sorted(_PY_HAM, key=len, reverse=True)))
    for m in re.finditer(rf"(?:ta|talib)?\.?({mau})\s*\(", vb):
        chuan, so_ts = _PY_HAM[m.group(1)]
        trong = _khoi_ngoac(vb, m.end() - 1)
        ds = _tach_doi_so(trong) if trong.strip() else []
        cot = None
        for x in ds:
            c = _cot_python(x)
            if c:
                cot = "tick_volume" if c == "volume" else c
                break
        ra.append({"chi_bao": chuan,
                   "tham_so": _so_dau(ds, so_ts, m.start(), bang) if so_ts else [],
                   "cot": cot, "ngon_ngu": "python",
                   "trich": (m.group(0) + trong + ")")[:120]})
    return ra


def dien_dat_duoc(tp: dict) -> tuple[bool, str]:
    """Thanh phan nay ngu phap hien tai co viet ra duoc khong, va thieu gi."""
    cb = tp.get("chi_bao")
    if cb not in _DIEN_DAT_DUOC:
        return False, f"{THIEU_TOAN_HANG} '{cb}'"
    cot = tp.get("cot")
    if cot in NP.COT_TONG_HOP and cb not in _NHAN_COT:
        return False, f"'{cb}' chua nhan duoc nguon gia tong hop '{cot}'"
    if cot and cot != "close" and cb not in _NHAN_COT:
        return False, f"'{cb}' trong ngu phap luon tinh tren close, khong nhan cot"
    return True, ""


def rut(vb: str, ngon_ngu: str = "tu_doan") -> list[dict]:
    """Rut thanh phan tu mot ban doc. Gop trung theo (chi bao, tham so, cot)."""
    if not vb:
        return []
    la_pine = ("//@version" in vb or "strategy(" in vb or "indicator(" in vb
               or "study(" in vb)
    la_mql = ("OnTick" in vb or "#property" in vb or "iMA(" in vb)
    la_py = ("import pandas" in vb or "import numpy" in vb or ".rolling(" in vb
             or "talib" in vb or "pandas_ta" in vb or "def " in vb)
    if ngon_ngu == "pine" or (ngon_ngu == "tu_doan" and la_pine and not la_mql):
        tho = rut_pine(vb)
    elif ngon_ngu == "mql" or (ngon_ngu == "tu_doan" and la_mql and not la_pine):
        tho = rut_mql(vb)
    elif ngon_ngu == "python" or (ngon_ngu == "tu_doan" and la_py):
        tho = rut_python(vb)
    else:
        tho = rut_pine(vb) + rut_mql(vb) + rut_python(vb)
    gop: dict = {}
    for t in tho:
        khoa = (t["chi_bao"], tuple(t["tham_so"]), t.get("cot"))
        g = gop.setdefault(khoa, dict(t, so_lan=0))
        g["so_lan"] += 1
    ra = []
    for t in gop.values():
        ok, thieu = dien_dat_duoc(t)
        ra.append(dict(t, dien_dat_duoc=ok, con_thieu=thieu))
    return sorted(ra, key=lambda x: (-x["so_lan"], x["chi_bao"]))


def van_tay(tp: dict) -> str:
    return SO.van_tay("tp", tp.get("chi_bao", ""),
                      json.dumps(tp.get("tham_so") or [], sort_keys=True),
                      str(tp.get("cot") or ""))


def thu_hoi(tieu_de: str, van_ban: str, url: str = "", nguon: str = "",
            ly_do_loai: str = "", ngon_ngu: str = "tu_doan") -> dict:
    """Rut thanh phan va GHI LAI, ke ca khi ca he da bi loai.

    `ly_do_loai` co gia tri rieng: no noi thanh phan nay den tu mot he KHONG qua
    duoc cong. Dung de sau nay tra loi duoc "duong nay ta lay ve tu dau" -
    giong het cach `sonic_r.py` giu lai EMA34/EMA89 tu mot bo strategy ma ban
    than no khong dung duoc.
    """
    ds = rut(van_ban, ngon_ngu)
    with SO.ket_noi() as cn:
        # Dem bang SO DONG TRUOC/SAU, khong bang `cur.rowcount`: mot upsert cham
        # nhanh UPDATE van tra rowcount=1 trong SQLite, nen dem theo rowcount thi
        # lan thu hai tren cung mot van ban se bao "10 thanh phan moi".
        truoc = cn.execute("SELECT COUNT(*) n FROM thanh_phan").fetchone()["n"]
        for t in ds:
            cn.execute(
                "INSERT INTO thanh_phan(van_tay,chi_bao,tham_so,cot,ngon_ngu,"
                "dien_dat_duoc,con_thieu,trich,nguon,url,tieu_de,ly_do_loai,"
                "so_lan,luc) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(van_tay) DO UPDATE SET so_lan=so_lan+excluded.so_lan",
                (van_tay(t), t["chi_bao"],
                 json.dumps(t["tham_so"], ensure_ascii=False), t.get("cot") or "",
                 t.get("ngon_ngu") or "", int(t["dien_dat_duoc"]), t["con_thieu"],
                 t["trich"], nguon, url, (tieu_de or "")[:300],
                 (ly_do_loai or "")[:300], t["so_lan"], SO.bay_gio()))
        moi = cn.execute("SELECT COUNT(*) n FROM thanh_phan").fetchone()["n"] - truoc
    return {"rut_duoc": len(ds), "moi": moi,
            "dien_dat_duoc": sum(1 for t in ds if t["dien_dat_duoc"]),
            "chua_dien_dat_duoc": sorted(
                {t["con_thieu"] for t in ds if not t["dien_dat_duoc"]})}


def kho(chi_dien_dat_duoc: bool | None = None, toi_da: int = 200) -> list[dict]:
    sql = "SELECT * FROM thanh_phan"
    args: tuple = ()
    if chi_dien_dat_duoc is not None:
        sql += " WHERE dien_dat_duoc=?"
        args = (int(chi_dien_dat_duoc),)
    return SO.nhieu(sql + " ORDER BY so_lan DESC, id DESC LIMIT ?", *args, toi_da)


def toan_hang_con_thieu(toi_da: int = 30) -> list[dict]:
    """Danh sach toan hang can them, xep theo SO LAN nguoi ta that su dung.

    Cham lai `dien_dat_duoc` theo NGU PHAP HIEN TAI thay vi tin co `dien_dat_duoc`
    da luu. Co do la anh chup luc THU HOACH: mot toan hang them vao ngu phap hom
    sau van bi bang nay doi them lan nua. Do that 01/09: bang van doi them `wma`,
    `smma`, `cci` trong khi ca ba da co tu buoi sang cung ngay.
    """
    tho = SO.nhieu("SELECT chi_bao, cot, so_lan FROM thanh_phan")
    gom: dict[str, dict] = {}
    for r in tho:
        ok, thieu = dien_dat_duoc(r)
        if ok:
            continue
        g = gom.setdefault(r["chi_bao"], {
            "chi_bao": r["chi_bao"], "so_bien_the": 0, "tong_lan": 0,
            "con_thieu": thieu})
        g["so_bien_the"] += 1
        g["tong_lan"] += int(r["so_lan"] or 0)
    return sorted(gom.values(), key=lambda x: -x["tong_lan"])[:toi_da]
