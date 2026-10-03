# -*- coding: utf-8 -*-
"""boc_lich_su.py - BOC LOGIC TU LICH SU LENH THAT cua nguoi thang (so do dong 41: "boc tach nguoc tu lich su lenh").

Chu du an 03/10/2026: *"nhung nguoi da co loi san ... AI doi chieu lich su vao lenh voi chart that de doan ra dieu kien
vao lenh"*. Module nay la nua "boc" cua chuoi do (nua "thu" da co: `luoi.py`, `thu_luoi`, `thu_co_che`). Dau vao la DANH
SACH LENH (mo, dong, chieu, lot, gia mo, gia dong) - dung thu ma trang Signals MQL5 / Myfxbook / bao cao tester hien ra;
dau ra la GIA THUYET co so do duoc, KHONG phai ket luan loi nhuan:

  1. CHUAN HOA        lich su (CSV / JSON / bang HTML luu tu trang) -> bang lenh co loai kieu, gio, gia.
  2. GOM RO           lenh cung chieu chong len nhau theo thoi gian = mot ro luoi/DCA; mo lai tai gio dong = ro moi.
  3. SUY THAM SO      `buoc`, `he_so_buoc`, `kieu_lot`/`he_so_lot`, `tran_tang`, `tp` HOAC `chot_tien`, `cho_lui`, `tia_lenh`,
                      `che_do` -> dung ten truong cua `luoi.ThamSo`, chay thang bang `thu_luoi`. Moi tham so kem do tin.
  4. CAN GIO          lich su co gio may chu cua nguoi do, bar cua ta co gio may chu khac: uoc so gio lech bang chinh GIA
                      (gia mo lenh phai nam trong bien do bar chua no) truoc khi so voi chart.
  5. DIEU KIEN VAO    cac lenh MO RO (khong phai mo lai ngay sau TP) so voi bar DOI CHUNG (bar rang, du dieu kien ma khong
                      vao) tren bo dac trung `nc_dac_trung` -> AUC, nguong, dieu kien DSL; `khop_luat` cham luat AI de xuat.
  6. PHAT LAI         tham so suy ra chay qua `luoi.chay` tren bar -> so ro / so lenh / do sau / nhip theo tuan so voi that.

## NHUNG GI MODULE NAY KHONG LAM (doc truoc khi tin bat ky con so nao)

* KHONG do loi nhuan. Moi ket qua o day la MO TA; tien vao so tay chi qua `thu_luoi` / `thu_co_che` tren doan kham pha.
* NGUOI THANG la mau CHON THEO KET QUA: song lau vi da thang tren CUA SO CUA HO. Luat boc tu ho phai duoc thu tren du lieu
  NGOAI cua so do (truoc ngay ho bat dau, hoac tien toi) - `canh_bao` luon nhac. Cua so cua ho nam trong doan niem phong
  thi phat lai KHONG duoc chay (module chi nhan bar tu `DOAN_MO`, xem `nc_thi_nghiem.boc_lich_su`).
* Phan khong nhin thay trong lich su: bo loc chi bao cua lenh DAU, tin tuc, cat lo ngay trong ro. Cai nao engine `luoi.py`
  chua mo phong thi vao `ngoai_engine` thay vi duoc doan cho co.
* Chi so cach gom ro la quy uoc (lenh chong nhau theo thoi gian). EA hedging (mua + ban cung mot ro) khong tach duoc.

Kiem bang du lieu CAI SAN DAP AN: `test_boc_lich_su.py` (EA tick-level viet rieng + `luoi.chay(ghi_lenh=True)`); doi chieu
voi lich su that chi lam duoc khi may nha mang file ve - bo doc HTML o day viet theo cau truc bang chung, chua thay mau that.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pandas as pd

from nhan import luoi as LU
from nhan import nc_dac_trung as DT
from nhan import ngu_phap as NP

#: tang khi thuat toan boc doi (de van tay thi nghiem trong so tay khong tra ket qua cu cua ban cu)
PHIEN_BAN = "1"
HOP_DONG_MAC_DINH = 100_000.0
#: dong sai gio khi coi cac lenh "dong cung luc" / "mo lai ngay": lich su that ghi theo giay
DUNG_SAI_GIAY = 2.0
#: ro bat dau cach ro truoc (cung chieu) toi da bao nhieu giay = "mo lai ngay sau TP"
GAP_NGAY_GIAY = 5.0

_CANH_BAO_NGUOI_THANG = ("NGUOI THANG la mau chon theo ket qua: luat boc duoc chi la GIA THUYET. Thu tren du lieu NGOAI cua so "
                         "song cua ho (truoc ngay ho bat dau) roi moi tien toi xac nhan; cua so cua ho khong duoc la bang chung.")


# ============================================================== 1. CHUAN HOA
def _khong_dau(s) -> str:
    s = str(s).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


_BI_DANH = {
    "mo": {"mo", "gio_mo", "thoi_gian_mo", "open_time", "time_open", "opentime", "open_date", "opened", "entry_time"},
    "dong": {"dong", "gio_dong", "thoi_gian_dong", "close_time", "time_close", "closetime", "close_date", "closed",
             "exit_time"},
    "chieu": {"chieu", "loai", "type", "action", "side", "direction", "buy_sell", "trade_type"},
    "lot": {"lot", "lots", "volume", "vol", "size", "khoi_luong"},
    "gia_mo": {"gia_mo", "open_price", "price_open", "openprice", "entry_price"},
    "gia_dong": {"gia_dong", "close_price", "price_close", "closeprice", "exit_price"},
    "loi": {"loi", "profit", "pnl", "p_l", "net_profit", "loi_nhuan"},
    "sl": {"sl", "s_l", "stop_loss", "stoploss"},
    "tp": {"tp", "t_p", "take_profit", "takeprofit"},
    "ma": {"ma", "symbol", "instrument", "pair", "item"},
}
_HAI_LAN = {"time": ("mo", "dong"), "price": ("gia_mo", "gia_dong"), "gio": ("mo", "dong"), "gia": ("gia_mo", "gia_dong")}


def _ten_cot(cot) -> list[str]:
    """Danh sach ten cot goc -> ten chuan. Ten KHONG nhan ra giu nguyen (khong mat cot)."""
    ra, thu_tu, da = [], {}, set()
    for c in cot:
        if isinstance(c, tuple):
            c = [x for x in c if not str(x).startswith("Unnamed")][-1:] or [""]
            c = c[0]
        n = _khong_dau(c)
        if n in _HAI_LAN:
            k = thu_tu.get(n, 0)
            thu_tu[n] = k + 1
            ten = _HAI_LAN[n][min(k, 1)]
            if k >= 2 or ten in da:
                ra.append(str(c))
                continue
            da.add(ten)
            ra.append(ten)
            continue
        ten = next((k for k, v in _BI_DANH.items() if n in v), None)
        if ten and ten not in da:
            da.add(ten)
            ra.append(ten)
        else:
            ra.append(str(c))
    return ra


def _so(x):
    """'1 234,50' / '1,234.50' / 12.5 -> float. Rong / khong doc duoc -> NaN."""
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).replace("\xa0", "").replace(" ", "").strip()
    if not s or s in ("-", "--", "nan", "None"):
        return float("nan")
    if "," in s and "." in s:
        s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".") if re.fullmatch(r"-?\d*,\d{1,2}", s) else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _gio(serie: pd.Series) -> pd.Series:
    s = serie.astype(str).str.strip().str.replace(r"^(\d{4})\.(\d{2})\.(\d{2})", r"\1-\2-\3", regex=True)
    s = s.where(~serie.isna(), None)
    return pd.to_datetime(s, errors="coerce", format="mixed")


def _chieu(serie: pd.Series) -> pd.Series:
    """buy/sell, mua/ban, long/short -> +1/-1; so: {-1, +1} la +1/-1, {0, 1} la enum MT5 (0 = buy, 1 = sell). Loai khac (balance...) -> NaN.
    Cot so chi gom mot gia tri 1 la MO HO (+1 = mua hay 1 = ban?) -> bao loi, khong doan (doan sai lat nguoc ca lich su)."""
    so = pd.to_numeric(serie, errors="coerce")
    if so.notna().all():
        v = set(so.unique())
        if v <= {-1.0, 1.0} and -1.0 in v:
            return so
        if v <= {0.0, 1.0} and 0.0 in v:
            return so.map({0.0: 1.0, 1.0: -1.0})
        if v <= {1.0}:
            raise ValueError("cot chieu chi gom so 1: khong phan biet +1 = mua hay 1 = ban (enum MT5). Doi thanh buy/sell")
    s = serie.astype(str).str.lower()
    ra = pd.Series(np.nan, index=serie.index)
    ra[s.str.contains(r"^(?:buy|mua|long)\b", regex=True)] = 1.0
    ra[s.str.contains(r"^(?:sell|ban|short)\b", regex=True)] = -1.0
    return ra


def doan_pip(ma: str, gia: float | None = None) -> float:
    """Kich thuoc 1 pip theo ten ma. Chi la doan - truyen `pip=` khi biet chac (vang/chi so/crypto rat khac nhau)."""
    m = str(ma or "").upper()
    if "JPY" in m:
        return 0.01
    if m.startswith(("XAU", "GOLD")):
        return 0.1
    if gia is not None and gia > 50:
        return 0.01
    return 1e-4


def chuan_hoa(lenh, pip: float | None = None, ma: str | None = None) -> pd.DataFrame:
    """Lich su lenh (DataFrame / list dict / duong dan) -> bang chuan: mo, dong, chieu(+1/-1), lot, gia_mo, gia_dong, [loi, sl, tp, ma].

    Giu cot `ma` neu co (lich su nhieu ma phai duoc loc TRUOC: mot ro luoi chi co nghia tren mot ma).
    `attrs`: pip, so_bo (so dong bi bo vi khong phai lenh mua/ban hoac thieu gio mo/gia/lot).
    """
    if isinstance(lenh, (str, Path)):
        lenh = doc_tep(lenh)
    d = pd.DataFrame(lenh).copy()
    d.columns = _ten_cot(list(d.columns))
    thieu = [c for c in ("mo", "chieu", "lot", "gia_mo") if c not in d.columns]
    if thieu:
        raise ValueError("lich su thieu cot %s (co: %s). Can: mo, dong, chieu (buy/sell), lot, gia_mo, gia_dong"
                         % (thieu, list(d.columns)))
    n0 = len(d)
    d["mo"] = _gio(d["mo"])
    d["dong"] = _gio(d["dong"]) if "dong" in d.columns else pd.NaT
    d["chieu"] = _chieu(d["chieu"])
    for c in ("lot", "gia_mo", "gia_dong", "loi", "sl", "tp"):
        d[c] = d[c].map(_so) if c in d.columns else np.nan
    if "ma" not in d.columns:
        d["ma"] = str(ma or "")
    d["ma"] = d["ma"].astype(str).str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
    ok = d["mo"].notna() & d["chieu"].notna() & (d["lot"] > 0) & (d["gia_mo"] > 0)
    d = d[ok].copy()
    d["chieu"] = d["chieu"].astype(int)
    # lenh co gio dong nhung thieu gia dong -> coi nhu chua dong (khong bia gia)
    d.loc[d["gia_dong"].isna() | ~(d["gia_dong"] > 0), "dong"] = pd.NaT
    cot = ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "loi", "sl", "tp", "ma"]
    d = d[cot].sort_values(["mo", "chieu"], kind="stable").reset_index(drop=True)
    d.attrs["so_bo"] = int(n0 - len(d))
    d.attrs["pip"] = float(pip) if pip else doan_pip(d["ma"].mode().iat[0] if len(d) else ma,
                                                      float(d["gia_mo"].median()) if len(d) else None)
    d.attrs["da_chuan_hoa"] = True
    return d


class _BangHTML(HTMLParser):
    """Rut MOI bang <table> thanh list hang (list o). Khong can lxml/bs4 - may nha khong co san."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bang, self._hang, self._o, self._sau = [], None, None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.bang.append([])
        elif tag == "tr" and self.bang:
            self._hang = []
        elif tag in ("td", "th") and self._hang is not None:
            self._o = []
        elif tag in ("script", "style"):
            self._sau += 1

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._o is not None and self._hang is not None:
            self._hang.append(re.sub(r"\s+", " ", "".join(self._o)).strip())
            self._o = None
        elif tag == "tr" and self._hang is not None and self.bang:
            if any(c for c in self._hang):
                self.bang[-1].append(self._hang)
            self._hang = None
        elif tag in ("script", "style"):
            self._sau = max(0, self._sau - 1)

    def handle_data(self, data):
        if self._o is not None and not self._sau:
            self._o.append(data)


def _doc_chuoi(duong: Path) -> str:
    b = duong.read_bytes()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):                 # bao cao MT5 xuat HTML la UTF-16
        return b.decode("utf-16", errors="replace")
    for ma in ("utf-8-sig", "cp1252"):
        try:
            return b.decode(ma)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


def doc_bang_html(text: str) -> pd.DataFrame:
    """Bang lenh trong trang HTML luu tu web / bao cao tester: chon bang LENH DA DONG (co ca gio dong + gia dong) nhieu hang nhat.

    Bao cao MT5 co NHIEU bang cung cot Time / Type / Volume / Price: Positions (moi LENH mot dong: gio + gia mo VA dong),
    Orders (lenh dat, co cot State), Deals (moi DEAL mot dong, cot Direction in/out - nhieu hang gap doi). Chon theo so hang se chon
    NHAM Deals va doc moi deal thanh mot lenh. Nen: bang co `dong` + `gia_dong` thang; bang Deals / Orders KHONG bao gio duoc dung
    thay cho Positions (khong ghep duoc vao/ra khi nhieu lenh cung mo - phai xuat muc Positions)."""
    p = _BangHTML()
    p.feed(text)
    tot, la_deal = None, False
    for b in p.bang:
        if len(b) < 3:
            continue
        # dong tieu de = hang dau co chu "time"/"volume"/"symbol"
        for k, h in enumerate(b[:6]):
            goc = [_khong_dau(c) for c in h]
            ten = set(_ten_cot(h))
            if {"mo", "chieu", "lot"} <= ten:
                da_dong = {"dong", "gia_dong"} <= ten
                if not da_dong and ("direction" in goc or "state" in goc):
                    la_deal = True                       # bang Deals / Orders cua MT5: khong dung lam bang lenh
                    break
                rong = max(len(h), 1)
                rows = [r[:rong] + [""] * (rong - len(r)) for r in b[k + 1:] if len(r) >= max(4, rong - 2)]
                diem = (1 if da_dong else 0, len(rows))
                if rows and (tot is None or diem > tot[2]):
                    tot = (h, rows, diem)
                break
    if tot is None:
        if la_deal:
            raise ValueError("HTML chi co bang DEAL / ORDERS (moi deal mot dong), khong co bang lenh da dong. Xuat muc POSITIONS cua "
                             "bao cao MT5 (hoac bao cao MT4: Closed Transactions) roi dua lai.")
        raise ValueError("khong thay bang lenh trong HTML (can dong tieu de co Time / Type / Volume / Price). "
                         "Dua file mau cho phien cloud de viet bo doc dung dinh dang that.")
    return pd.DataFrame(tot[1], columns=tot[0])


def doc_tep(duong) -> pd.DataFrame:
    """Doc tep lich su: .csv/.tsv/.txt (phan cach tu dong nhan), .json (list dict hoac {"lenh": [...]}), .htm/.html."""
    duong = Path(duong)
    if not duong.is_file():
        raise FileNotFoundError("khong co tep lich su: %s" % duong)
    suf = duong.suffix.lower()
    if suf in (".htm", ".html"):
        return doc_bang_html(_doc_chuoi(duong))
    if suf == ".json":
        j = json.loads(_doc_chuoi(duong))
        return pd.DataFrame(j["lenh"] if isinstance(j, dict) else j)
    import io
    return pd.read_csv(io.StringIO(_doc_chuoi(duong)), sep=None, engine="python")


# ============================================================== 2. GOM RO
def phan_ro(lenh: pd.DataFrame, dung_sai_s: float = DUNG_SAI_GIAY) -> pd.DataFrame:
    """Gan `ro` va `tang` cho tung lenh. Cung (ma, chieu): lenh mo TRUOC khi ro dong het thi cung ro; mo SAU khi ro dong het la ro MOI.

    Lich su that ghi theo giay nen "mo lai ngay sau TP" va "them tang cung giay voi TP" co the trung gio. Phan biet bang GIA:
    tang them luon nam SAU tang sau nhat cua ro (theo huong bat loi cua lenh), con lenh mo lai sau TP thi khong.
    Lenh chua dong tinh la dang mo den het du lieu.

    Thu tu khi TRUNG GIAY MO: lenh dong som truoc (tang them cua ro cu dong cung luc voi ro cu, con lenh dau cua ro moi dong sau),
    roi lenh nong truoc - nen ket qua khong phu thuoc thu tu dong trong tep."""
    d = lenh.assign(_sau=-lenh["chieu"].astype(int) * lenh["gia_mo"].astype(float))
    d = d.sort_values(["ma", "chieu", "mo", "dong", "_sau"], kind="stable").drop(columns="_sau").reset_index(drop=True)
    vo_cuc = np.datetime64("2200-01-01T00:00:00")      # xa nhung KHONG sat tran ns (2262-04-11): cong dung sai khong tran so
    mo = d["mo"].to_numpy("datetime64[ns]")
    dong = d["dong"].to_numpy("datetime64[ns]")
    dong = np.where(np.isnat(dong), vo_cuc, dong)
    sai = np.timedelta64(int(dung_sai_s * 1e9), "ns")
    chieu = d["chieu"].to_numpy(int)
    gia = d["gia_mo"].to_numpy(float)
    ma = d["ma"].to_numpy(object)
    ro = np.empty(len(d), np.int64)
    tang = np.empty(len(d), np.int64)
    cur, k, het, sau_nhat, khoa_truoc = -1, 0, None, 0.0, None
    for j in range(len(d)):
        khoa = (ma[j], chieu[j])
        moi_ro = khoa != khoa_truoc or het is None
        if not moi_ro:
            if mo[j] > het + sai:
                moi_ro = True
            elif mo[j] >= het - sai:                     # trung gio: tang them hay mo lai sau TP?
                moi_ro = chieu[j] * gia[j] >= sau_nhat   # tang them thi phai o SAU tang sau nhat
        if moi_ro:
            cur += 1
            k, het, khoa_truoc, sau_nhat = 0, dong[j], khoa, chieu[j] * gia[j]
        else:
            k += 1
            het = max(het, dong[j])
            sau_nhat = min(sau_nhat, chieu[j] * gia[j])
        ro[j], tang[j] = cur, k
    d["ro"], d["tang"] = ro, tang
    return d.sort_values(["mo", "ro", "tang"], kind="stable").reset_index(drop=True)


def _dong_thoi_max(mo: np.ndarray, dong: np.ndarray) -> int:
    ev = [(t, 1) for t in mo] + [(t, -1) for t in dong if not np.isnat(t)]
    ev.sort(key=lambda x: (x[0], x[1]))              # dong truoc mo khi bang gio
    cur = best = 0
    for _t, v in ev:
        cur += v
        best = max(best, cur)
    return best


def bang_ro(d: pd.DataFrame, pip: float, hop_dong: float = HOP_DONG_MAC_DINH,
            dung_sai_s: float = DUNG_SAI_GIAY) -> pd.DataFrame:
    """Mot dong / ro: chieu, mo, dong, so_lenh, dong_thoi_max, lot_dau, lot_tong, gia_dau, gia_tb, da_dong ... va, voi ro da dong:

    * `tp_pip`, `tien_cuoi`, `gia_dong_tb`: tinh tren NHOM DONG CUOI (cac lenh dong trong `dung_sai_s` cua lenh dong sau cung):
      voi ro co tia lenh thi cac cap da cat truoc do KHONG tinh vao TP cua ro (engine tinh TP tu gia trung binh cua nhung lenh con lai);
    * `tien_gop`: tien bao gia cua CA ro (gia x lot x hop dong - cung don vi engine luoi, khong phai tien tai khoan);
    * `so_lan_dong`: so dot dong (cach nhau > dung_sai_s), `dong_cung_luc` = ca ro dong mot dot."""
    hang = []
    sai = np.timedelta64(int(dung_sai_s * 1e9), "ns")
    for ro, g in d.groupby("ro", sort=True):
        g = g.sort_values("tang")
        chieu = int(g["chieu"].iat[0])
        lot = g["lot"].to_numpy(float)
        gm = g["gia_mo"].to_numpy(float)
        da_dong = bool(g["dong"].notna().all())
        h = {"ro": int(ro), "ma": g["ma"].iat[0], "chieu": chieu, "mo": g["mo"].min(),
             "dong": g["dong"].max() if da_dong else pd.NaT, "so_lenh": int(len(g)),
             "lot_dau": float(lot[0]), "lot_tong": float(lot.sum()), "gia_dau": float(gm[0]),
             "gia_tb": float((gm * lot).sum() / lot.sum()), "da_dong": da_dong,
             "dong_thoi_max": _dong_thoi_max(g["mo"].to_numpy("datetime64[ns]"), g["dong"].to_numpy("datetime64[ns]"))}
        if da_dong:
            gd = g["gia_dong"].to_numpy(float)
            t = g["dong"].to_numpy("datetime64[ns]")
            cuoi = t >= t.max() - sai
            lc, mc, dc = lot[cuoi], gm[cuoi], gd[cuoi]
            h["so_lenh_cuoi"] = int(cuoi.sum())
            h["gia_dong_tb"] = float((dc * lc).sum() / lc.sum())
            h["tp_pip"] = chieu * (h["gia_dong_tb"] - float((mc * lc).sum() / lc.sum())) / pip
            h["tien_cuoi"] = float((chieu * (dc - mc) * lc).sum() * hop_dong)
            h["tien_gop"] = float((chieu * (gd - gm) * lot).sum() * hop_dong)
            ts = np.sort(t)
            h["so_lan_dong"] = int(1 + (np.diff(ts) > sai).sum()) if len(ts) > 1 else 1
            h["dong_cung_luc"] = h["so_lan_dong"] == 1
        else:
            h.update(gia_dong_tb=np.nan, tp_pip=np.nan, tien_cuoi=np.nan, tien_gop=np.nan, so_lan_dong=0, dong_cung_luc=False,
                     so_lenh_cuoi=0)
        hang.append(h)
    return pd.DataFrame(hang)


# ============================================================== 3. SUY THAM SO
def _cv(x) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2 or abs(x.mean()) < 1e-12:
        return float("inf")
    return float(x.std(ddof=1) / abs(x.mean()))


def _lam_tron(x: float, b: float) -> float:
    return round(x / b) * b


def _do_tin(n: int, tot: float | None = None, vua: float | None = None, val: float | None = None) -> str:
    """cao / vua / thap theo CO MAU truoc, roi theo do sai (val <= tot: cao; <= vua: vua)."""
    if n < 5:
        return "thap"
    if val is None or tot is None:
        return "cao" if n >= 30 else "vua"
    if val <= tot and n >= 15:
        return "cao"
    return "vua" if val <= (vua if vua is not None else 2 * tot) and n >= 8 else "thap"


def _suy_buoc(d: pd.DataFrame, ro: pd.DataFrame, pip: float) -> dict:
    """Khoang cach giua cac tang (pip): buoc, he_so_buoc, buoc_tran. Chi tinh ro `luoi sach` (moi tang cach xa hon theo
    huong BAT LOI cua ro - gia di nguoc chieu lenh)."""
    theo_tang: dict[int, list[float]] = {}
    sach = tong = 0
    for r, g in d.groupby("ro", sort=False):
        if len(g) < 2:
            continue
        tong += 1
        g = g.sort_values("tang")
        chieu = int(g["chieu"].iat[0])
        p = g["gia_mo"].to_numpy(float)
        s = chieu * (p[:-1] - p[1:]) / pip
        if (s > 0).all():
            sach += 1
            for k, v in enumerate(s):
                theo_tang.setdefault(k, []).append(float(v))
    out = {"ty_le_ro_luoi_sach": round(sach / tong, 3) if tong else None, "so_ro_nhieu_tang": tong,
           "buoc": None, "buoc_cv": None, "he_so_buoc": None, "buoc_tran": None, "buoc_theo_tang": {}}
    if not theo_tang:
        out["do_tin"] = "khong_co_du_lieu"
        return out
    trung_vi = {k: float(np.median(v)) for k, v in theo_tang.items() if len(v) >= 3}
    out["buoc_theo_tang"] = {str(k + 1): round(v, 2) for k, v in sorted(trung_vi.items())}
    v0 = theo_tang[0]
    out["buoc"] = round(float(np.median(v0)), 2)
    out["buoc_cv"] = round(_cv(v0), 3)
    out["he_so_buoc"], out["buoc_tran"] = 1.0, None
    ks = sorted(trung_vi)
    if len(ks) >= 3:
        m = [trung_vi[k] for k in ks]
        r = [m[i + 1] / m[i] for i in range(len(m) - 1)]
        tang = [x for x in r if abs(x - 1.0) > 0.06]
        if tang:
            # chi nhung cap truoc cao nguyen: sau khi di ngang (<=6%) la tran buoc
            che = 0
            for i, x in enumerate(r):
                if abs(x - 1.0) <= 0.06 and i > 0 and r[i - 1] > 1.06:
                    che = i
                    break
            dung = r[:che] if che else r
            out["he_so_buoc"] = round(float(np.exp(np.mean(np.log(dung)))), 3)
            if che:
                out["buoc_tran"] = round(m[che], 1)
    out["do_tin"] = _do_tin(len(v0), tot=0.08, vua=0.25, val=out["buoc_cv"])
    return out


def _suy_lot(d: pd.DataFrame) -> dict:
    """kieu_lot (phang|cong|nhan|khong_ro) + he_so_lot. Lot that duoc lam tron theo buoc lot san -> khop DU DOAN DA LAM TRON."""
    theo_tang: dict[int, list[float]] = {}
    for _r, g in d.groupby("ro", sort=False):
        for k, l in zip(g.sort_values("tang")["tang"], g.sort_values("tang")["lot"]):
            theo_tang.setdefault(int(k), []).append(float(l))
    ks = [k for k in sorted(theo_tang) if len(theo_tang[k]) >= 3]
    if not ks or ks[0] != 0:
        return {"kieu_lot": "khong_ro", "he_so_lot": None, "lot": None, "lot_theo_tang": {}, "do_tin": "khong_co_du_lieu"}
    med = {k: float(np.median(theo_tang[k])) for k in ks}
    tat = np.array([max(1, len(theo_tang[k])) for k in ks], float)
    obs = np.array([med[k] for k in ks])
    l0 = med[0]
    tat_ca = np.concatenate([np.asarray(v) for v in theo_tang.values()])
    b = 0.01 if np.allclose(tat_ca / 0.01, np.round(tat_ca / 0.01), atol=1e-6) else 0.001

    def sai(du_doan: np.ndarray) -> float:
        return float(np.sum(tat * np.abs(du_doan - obs) / obs) / tat.sum())

    kk = np.array(ks, float)
    phang = sai(np.full(len(ks), l0))
    cong = min(((sai(np.array([_lam_tron(l0 * (1 + a * k), b) for k in kk])), a) for a in np.arange(0.05, 3.001, 0.01)),
               key=lambda x: x[0])
    nhan = min(((sai(np.array([_lam_tron(l0 * h ** k, b) for k in kk])), h) for h in np.arange(1.05, 3.001, 0.01)),
               key=lambda x: x[0])
    ung = [("phang", phang, 1.0), ("cong", cong[0], round(float(cong[1]), 2)), ("nhan", nhan[0], round(float(nhan[1]), 2))]
    # mo hinh don gian truoc; chi doi sang phuc tap khi tot hon RO (>= 2 diem phan tram sai so)
    ten, sai_so, he = ung[0]
    for t, s, h in ung[1:]:
        if s < sai_so - 0.02:
            ten, sai_so, he = t, s, h
    if sai_so > 0.15:
        ten, he = "khong_ro", None
    return {"kieu_lot": ten, "he_so_lot": he, "lot": round(l0, 4), "sai_so_lot": round(sai_so, 3),
            "lot_theo_tang": {str(k + 1): round(v, 4) for k, v in med.items()},
            "do_tin": ("thap" if len(ks) < 3 else _do_tin(int(tat.sum()), tot=0.03, vua=0.08, val=sai_so))
            if ten != "khong_ro" else "khong_ro"}


def _suy_tp(ro: pd.DataFrame, co_tia: bool = False) -> dict:
    """`tp` (pip tu gia trung binh nhom con lai) HAY `chot_tien` (tien tren 0,01 lot goc): cai nao it doi theo do sau cua ro la that.

    TP la lenh cho (khop dung gia) -> lay TRUNG VI. `chot_tien` la dieu kien ">=" kiem tra theo thoi gian -> loi that LUON >= nguong
    (qua tay mot nhip gia): lay phan vi 10 lam uoc luong nguong, in kem p50/p90 de thay muc qua tay."""
    ok = ro[ro["da_dong"] & (ro["tp_pip"] > 0)]
    if co_tia:
        # ro co tia lenh co the ket thuc bang cap cuoi (dong dung 2 lenh, loi ~ bien_cap) HOAC bang TP: bo cac ro ket thuc 2 lenh
        # de TP khong tron voi bien cap (ro TP that khi con dung 2 lenh bi bo: chi mat mau, khong sai huong)
        ok = ok[ok["so_lenh_cuoi"] != 2]
    out = {"che_do_tp": "khong_ro", "tp": None, "chot_tien": None, "so_ro_do_tp": int(len(ok))}
    if len(ok) < 8:
        out["do_tin"] = "thap" if len(ok) else "khong_co_du_lieu"
        return out
    nhieu_tang = ok[ok["so_lenh"] >= 2]
    mau = nhieu_tang if len(nhieu_tang) >= 8 else ok
    tien = lambda x: x["tien_cuoi"] * 0.01 / x["lot_dau"]
    cv_pip, cv_tien = _cv(mau["tp_pip"]), _cv(tien(mau))
    out.update(cv_tp_pip=round(cv_pip, 3), cv_chot_tien=round(cv_tien, 3),
               tp_pip_phan_vi={q: round(float(ok["tp_pip"].quantile(q / 100)), 2) for q in (10, 50, 90)},
               chot_tien_phan_vi={q: round(float(tien(ok).quantile(q / 100)), 3) for q in (10, 50, 90)})
    if min(cv_pip, cv_tien) > 0.45:
        out["do_tin"] = "thap"
        return out
    if cv_pip <= cv_tien * 0.9 or (cv_pip <= 0.25 and len(nhieu_tang) < 8):
        out.update(che_do_tp="pip", tp=round(float(ok["tp_pip"].median()), 2), do_tin=_do_tin(len(ok), 0.1, 0.25, cv_pip))
    else:
        out.update(che_do_tp="tien", chot_tien=round(float(tien(ok).quantile(0.10)), 3),
                   do_tin=_do_tin(len(ok), 0.15, 0.35, cv_tien))
    return out


def _suy_cho_lui(ro: pd.DataFrame, pip: float, gia_dong_ro: dict) -> dict:
    """Khoang giua hai ro LIEN TIEP cung (ma, chieu): mo lai ngay (cho_lui = 0) hay cho gia lui N pip roi moi vao."""
    gap, lui = [], []
    for (_m, _c), g in ro.groupby(["ma", "chieu"]):
        g = g.sort_values("mo")
        for a, b in zip(g.index[:-1], g.index[1:]):
            if not bool(g.at[a, "da_dong"]):
                continue
            ga, gb = g.loc[a], g.loc[b]
            gap.append((gb["mo"] - ga["dong"]).total_seconds())
            lui.append(int(ga["chieu"]) * (gia_dong_ro[int(ga["ro"])] - gb["gia_dau"]) / pip)
    out = {"so_cap_ro": len(gap), "vao_lai_ngay_ty_le": None, "cho_lui": None, "gap_giay_trung_vi": None}
    if not gap:
        out["do_tin"] = "khong_co_du_lieu"
        return out
    gap, lui = np.array(gap), np.array(lui)
    ngay = gap <= GAP_NGAY_GIAY
    out["vao_lai_ngay_ty_le"] = round(float(ngay.mean()), 3)
    out["gap_giay_trung_vi"] = round(float(np.median(gap)), 1)
    if ngay.mean() >= 0.8:
        out["cho_lui"] = 0.0
        out["do_tin"] = _do_tin(len(gap))
        return out
    cho = lui[~ngay]
    q1, q2, q3 = np.percentile(cho, [25, 50, 75]) if len(cho) else (0, 0, 0)
    out["lui_pip_phan_vi"] = {"p25": round(float(q1), 2), "p50": round(float(q2), 2), "p75": round(float(q3), 2)}
    if len(cho) >= 8 and q2 > 0 and (q3 - q1) / q2 < 0.6:
        out["cho_lui"] = round(float(q2), 2)
        out["do_tin"] = _do_tin(len(cho), 0.3, 0.6, (q3 - q1) / q2)
    else:
        out["cho_lui"] = None
        out["do_tin"] = "khong_ro"           # cho theo gio / chi bao, khong phai gia lui co dinh: xem dieu_kien_vao
    return out


def _suy_tia(d: pd.DataFrame, ro: pd.DataFrame, pip: float) -> dict:
    """Tia lenh: trong ro >= 3 lenh, moi lan dong DAU TIEN la CAP (lenh cu nhat + lenh moi nhat) trong khi ro van con lenh."""
    thu = ok = 0
    bien = []
    for r in ro.loc[(ro["so_lenh"] >= 3) & ro["da_dong"] & (ro["so_lan_dong"] >= 2), "ro"]:
        g = d[d["ro"] == r].sort_values("tang")
        t1 = g["dong"].min()
        dong1 = g[g["dong"] <= t1 + pd.Timedelta(seconds=DUNG_SAI_GIAY)]
        con_mo = g[g["dong"] > t1 + pd.Timedelta(seconds=DUNG_SAI_GIAY)]
        if con_mo.empty:
            continue
        thu += 1
        da_mo = g[g["mo"] <= t1]
        cap = len(dong1) == 2 and set(dong1["tang"]) == {int(da_mo["tang"].min()), int(da_mo["tang"].max())}
        if cap:
            ok += 1
            ch = int(g["chieu"].iat[0])
            w = (ch * (dong1["gia_dong"] - dong1["gia_mo"]) / pip * dong1["lot"]).sum() / dong1["lot"].sum()
            bien.append(float(w))
    out = {"so_ro_xet": thu, "ty_le_cap": round(ok / thu, 3) if thu else None, "tia_lenh": False, "bien_cap": None}
    if thu >= 5 and ok / thu >= 0.5:
        # `bien_cap` la dieu kien ">=": loi that LUON >= nguong -> phan vi 10 (xem _suy_tp); in kem p50 de thay muc qua tay
        out.update(tia_lenh=True, bien_cap=round(float(np.percentile(bien, 10)), 2),
                   bien_cap_p50=round(float(np.median(bien)), 2))
    out["do_tin"] = "thap" if thu < 5 else _do_tin(thu)
    return out


def _chi_binh_phuong_deu(dem: np.ndarray) -> tuple[float, float]:
    """Chi-binh-phuong so voi phan phoi deu; p qua xap xi Wilson-Hilferty (khong can scipy)."""
    n = dem.sum()
    if n <= 0:
        return 0.0, 1.0
    e = n / len(dem)
    x2 = float(((dem - e) ** 2 / e).sum())
    k = len(dem) - 1
    z = ((x2 / k) ** (1 / 3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    return x2, 0.5 * math.erfc(z / math.sqrt(2))


def _lich(ro: pd.DataFrame) -> dict:
    """Gio / thu BAT DAU ro (theo gio MAY CHU cua nguoi do - chua doi sang gio bar cua ta)."""
    out = {}
    if ro.empty:
        return out
    gio = ro["mo"].dt.hour.to_numpy()
    dem = np.bincount(gio, minlength=24).astype(float)
    x2, p = _chi_binh_phuong_deu(dem)
    exp = dem.sum() / 24.0
    out["gio_bat_dau"] = {"dem": {str(i): int(v) for i, v in enumerate(dem)}, "p_deu": round(p, 4),
                          "gio_khong_vao": [int(i) for i in range(24) if dem[i] <= 0.15 * exp] if p < 0.01 else [],
                          "gio_dong_nhat": [int(i) for i in np.argsort(-dem)[:3]]}
    thu = ro["mo"].dt.dayofweek.to_numpy()
    dt = np.bincount(thu, minlength=7).astype(float)
    out["thu_bat_dau"] = {"dem": {str(i): int(v) for i, v in enumerate(dt)}}
    # EA kiem tra moi NEN MOI vao dung giay dau nen: ty le ro mo trong 10 giay dau cua phut chia het k (ngau nhien ~ 10/(60k))
    dau = {}
    for k in (5, 15, 60):
        ty = float(((ro["mo"].dt.second < 10) & (ro["mo"].dt.minute % k == 0)).mean())
        dau[str(k)] = round(ty, 3)
    out["vao_dau_nen_ty_le"] = dau
    best = max(dau, key=dau.get)
    out["vao_dau_nen"] = ("khung %s phut (%.0f%% ro mo trong 10 giay dau nen; ngau nhien ~%.1f%%) - EA kiem tra khi nen dong, "
                          "dac trung phai dich >= 1 nen" % (best, 100 * dau[best], 100 * 10 / (60 * int(best)))
                          if dau[best] >= 0.3 else None)
    return out


def _tp_kieu_don(d: pd.DataFrame, pip: float) -> dict:
    """He KHONG phai luoi: nhin tung lenh - giu bao lau, thang bao nhieu, cat lo / chot loi co dinh khong."""
    dd = d[d["dong"].notna()]
    out = {"so_lenh_da_dong": int(len(dd))}
    if len(dd) < 5:
        return out
    giu = (dd["dong"] - dd["mo"]).dt.total_seconds() / 60.0
    pips = dd["chieu"] * (dd["gia_dong"] - dd["gia_mo"]) / pip
    thang = pips > 0
    out.update(giu_phut_phan_vi={q: round(float(giu.quantile(q / 100)), 1) for q in (10, 50, 90)},
               ty_le_thang=round(float(thang.mean()), 3),
               pip_thang_tb=round(float(pips[thang].mean()), 2) if thang.any() else None,
               pip_thua_tb=round(float(pips[~thang].mean()), 2) if (~thang).any() else None)
    for c, ten in (("sl", "sl_pip"), ("tp", "tp_pip")):
        x = (dd["gia_mo"] - dd[c]).abs() / pip
        x = x[dd[c].notna() & (dd[c] > 0)]
        if len(x) >= 5:
            out[ten] = {"trung_vi": round(float(x.median()), 2), "cv": round(_cv(x), 3), "n": int(len(x))}
    return out


def phan_tich_lenh(lenh: pd.DataFrame, hop_dong: float = HOP_DONG_MAC_DINH, spread_pip: float | None = None) -> dict:
    """Moi thu rut duoc tu CHINH danh sach lenh (khong can bar): ro, tham so luoi suy ra, do tin, mo ta he don lenh.

    `tham_so` chi gom truong ma `luoi.ThamSo` doc DUOC (de dua thang cho `thu_luoi`); nhung hanh vi engine chua mo phong
    nam o `ngoai_engine` kem ly do. Gia tri khong suy duoc thi KHONG co mat trong `tham_so` (khong bia mac dinh).

    `spread_pip`: spread trung vi (pip) luc vao lenh. Lich su that mo lenh MUA o gia ask va dong o bid (BAN nguoc lai) nen TP do tren
    lich su = TP tu gia trung binh - spread; engine tinh spread RIENG nen `tham_so["tp"]` = TP do duoc + spread_pip (khong truyen: giu
    nguyen TP do duoc va ghi canh bao)."""
    pip = float(lenh.attrs.get("pip") or doan_pip(None))
    if len(lenh) < 2:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "lich su co %d lenh" % len(lenh)}
    ma_list = sorted(set(lenh["ma"]))
    d = phan_ro(lenh)
    ro = bang_ro(d, pip, hop_dong)
    gia_dong_ro = dict(zip(ro["ro"], ro["gia_dong_tb"]))
    n_ro = len(ro)
    nhieu = ro[ro["so_lenh"] >= 2]
    ty_nhieu = len(nhieu) / n_ro if n_ro else 0.0
    mua = int((ro["chieu"] > 0).sum())
    ban = n_ro - mua
    che_do = "hai_chieu" if min(mua, ban) / max(n_ro, 1) > 0.2 else ("mua" if mua >= ban else "ban")
    buoc = _suy_buoc(d, ro, pip)
    lot = _suy_lot(d)
    tia = _suy_tia(d, ro, pip)
    tp = _suy_tp(ro, co_tia=tia["tia_lenh"])
    cho_lui = _suy_cho_lui(ro, pip, gia_dong_ro)
    dong = ro[ro["da_dong"]]
    lo = dong[dong["tp_pip"] < 0]
    dong_le = dong[(~dong["dong_cung_luc"]) & (~tia["tia_lenh"])]
    ra = {"trang_thai": "DAT", "ma": ma_list, "pip": pip, "hop_dong": hop_dong, "spread_pip": spread_pip,
          "lich_su": {"so_lenh": int(len(d)), "so_ro": n_ro, "so_ro_nhieu_tang": int(len(nhieu)),
                      "tu": str(d["mo"].min())[:19], "den": str((d["dong"].max() if d["dong"].notna().any() else d["mo"].max()))[:19],
                      "so_lenh_dang_mo": int(d["dong"].isna().sum()), "so_dong_bo": int(lenh.attrs.get("so_bo", 0))},
          "buoc": buoc, "lot": lot, "tp": tp, "cho_lui": cho_lui, "tia": tia,
          "tran_tang": {"toi_da_thay": int(ro["dong_thoi_max"].max()),
                        "so_ro_cham": int((ro["dong_thoi_max"] == ro["dong_thoi_max"].max()).sum()),
                        "do_tin": "cao" if (ro["dong_thoi_max"] == ro["dong_thoi_max"].max()).sum() >= 2 else "thap (chi la can duoi)"},
          "ro_lo": {"ty_le": round(len(lo) / len(dong), 4) if len(dong) else None, "so": int(len(lo)),
                    "tp_pip_tb": round(float(lo["tp_pip"].mean()), 2) if len(lo) else None},
          "ro_dong_le_ty_le": round(len(dong_le) / len(dong), 3) if len(dong) else None,
          "che_do": {"gia_tri": che_do, "ro_mua": mua, "ro_ban": ban},
          "lich": _lich(ro)}
    # luoi/DCA = nhieu ro co tang them va cac tang xep thanh THANG (moi tang o SAU tang truoc theo huong bat loi).
    # Lenh doc lap chong len nhau chi xep thang ngau nhien (~0,5^(so tang - 1)) nen nguong 0,75 + >= 20 ro tach duoc.
    ra["loai"] = ("luoi_dca" if (len(nhieu) >= 20 and (buoc.get("ty_le_ro_luoi_sach") or 0) >= 0.75)
                  else "don_lenh" if ty_nhieu < 0.15 else "khong_ro_ho_co_che")
    if ra["loai"] != "luoi_dca":
        ra["don_lenh"] = _tp_kieu_don(d, pip)
    # ---- tham so cho engine (chi gia tri co mat)
    ts = {"che_do": che_do}
    if lot.get("lot"):
        ts["lot"] = lot["lot"]
    if buoc.get("buoc"):
        ts["buoc"] = buoc["buoc"]
        if buoc.get("he_so_buoc") not in (None, 1.0):
            ts["he_so_buoc"] = buoc["he_so_buoc"]
            if buoc.get("buoc_tran"):
                ts["buoc_tran"] = buoc["buoc_tran"]
    ts["tran_tang"] = int(ro["dong_thoi_max"].max())
    if lot["kieu_lot"] in ("cong", "nhan"):
        ts["kieu_lot"], ts["he_so_lot"] = lot["kieu_lot"], lot["he_so_lot"]
    if tp["che_do_tp"] == "pip":
        ts["tp"] = round(tp["tp"] + (spread_pip or 0.0), 2)
        tp["tp_do_duoc"], tp["cong_spread_pip"] = tp["tp"], round(float(spread_pip or 0.0), 2)
    elif tp["che_do_tp"] == "tien":
        ts["chot_tien"] = tp["chot_tien"]
    if cho_lui.get("cho_lui"):
        ts["cho_lui"] = cho_lui["cho_lui"]
    if tia["tia_lenh"]:
        ts["tia_lenh"], ts["bien_cap"] = True, tia["bien_cap"]
    ra["tham_so"] = ts if ra["loai"] == "luoi_dca" else {}
    # ---- cai engine KHONG mo phong duoc (de AI khong tin ket qua phat lai hon muc cho phep)
    ngoai = []
    if ra["ro_lo"]["ty_le"] and ra["ro_lo"]["ty_le"] > 0.02:
        ngoai.append("co ro dong LO (%.1f%% so ro): engine luoi.py chua mo phong cat lo ro (dung_lo_tong chua cai dat) - "
                     "phat lai se THIEU phan thua do" % (100 * ra["ro_lo"]["ty_le"]))
    if ra["ro_dong_le_ty_le"] and ra["ro_dong_le_ty_le"] > 0.1:
        ngoai.append("%.0f%% ro dong LE TE (khong cung luc, khong phai cap tia lenh): trailing / cat tung lenh?"
                     % (100 * ra["ro_dong_le_ty_le"]))
    if buoc.get("buoc_cv") is not None and buoc["buoc_cv"] > 0.35:
        ngoai.append("buoc giua cac tang bien thien manh (CV %.2f): co ve buoc DONG theo ATR/bien dong, engine chi co buoc "
                     "co dinh + gian dan" % buoc["buoc_cv"])
    if lot["kieu_lot"] == "khong_ro" and lot.get("lot_theo_tang"):
        ngoai.append("lot theo tang khong theo cong/nhan: dung lot_theo_tang tren de dung bang tay")
    if cho_lui.get("do_tin") == "khong_ro":
        ngoai.append("khoang cach giua cac ro khong phai gia lui co dinh: cho theo gio / chi bao - xem dieu_kien_vao")
    if len(ma_list) > 1:
        ngoai.append("lich su co %d ma (%s): ro chi gom trong tung ma, nhung tham so suy ra la GOP - loc theo ma truoc"
                     % (len(ma_list), ", ".join(ma_list[:5])))
    if tp["che_do_tp"] == "pip" and spread_pip is None:
        ngoai.append("khong biet spread luc vao lenh: TP o tham_so la TP DO DUOC tren lich su (da tru spread neu gia lich su la ask/bid "
                     "that); truyen spread_pip (hoac dua bar co cot spread) de cong lai cho dung quy uoc engine")
    ra["ngoai_engine"] = ngoai
    ra["canh_bao"] = [_CANH_BAO_NGUOI_THANG] + (
        ["chi %d ro dong: cac tham so suy ra rat thieu mau" % len(dong)] if len(dong) < 30 else [])
    ra["_ro"], ra["_lenh"] = ro, d          # cho cac buoc sau; bo di truoc khi tra ra ngoai (xem `boc`)
    return ra


# ============================================================== 4. CAN GIO VOI CHART
def uoc_lech_gio(bar: pd.DataFrame, lenh: pd.DataFrame, pip: float, toi_da_gio: int = 14, buoc_phut: int = 30,
                 dung_sai_pip: float = 2.0, toi_da_lenh: int = 3000) -> dict:
    """Gio lich su cong them bao nhieu gio thi gia MO LENH nam trong bien do bar chua no nhieu nhat.

    Chong lech gio may chu giua hai san (GMT+2/+3...) bang CHINH gia: neu gio dung thi ~100% gia mo nam trong [low, high] cua bar
    (tru dung_sai_pip cho spread / chenh giua hai nguon gia); gio sai thi gia da di xa. Nen dung bar M15 tro xuong: bar lon thi
    gio sai van 'trung' vi bien do rong. `tin_cay` = cach biet so voi ung vien tot nhi KHAC (khong ke lan can cung 1 gio)."""
    if bar is None or len(bar) < 50:
        return {"lech_gio": None, "tin_cay": "khong_du_du_lieu", "ly_do": "bar qua ngan"}
    idx = bar.index.to_numpy("datetime64[ns]")
    hi = bar["high"].to_numpy(float)
    lo = bar["low"].to_numpy(float)
    bar_s = float(np.median(np.diff(idx).astype("timedelta64[s]").astype(float)))
    # chi lenh NAM TRONG khoang bar ke ca sau khi doi toi da `toi_da_gio` gio: lenh ngoai khoang se bi tinh la 'khong trung bar'
    # o MOI ung vien nen keo ty le tuyet doi xuong va ket luan nao cung 'tin cay thap'
    bien = np.timedelta64(int(toi_da_gio * 3600), "s")
    t_mo = lenh["mo"].to_numpy("datetime64[ns]")
    lenh = lenh[(t_mo >= idx[0] + bien) & (t_mo <= idx[-1] - bien)]
    if len(lenh) < 20:
        return {"lech_gio": None, "tin_cay": "khong_du_du_lieu",
                "ly_do": "chi %d lenh nam trong khoang bar (can >= 20, bo bien %d gio hai dau)" % (len(lenh), toi_da_gio)}
    mau = lenh if len(lenh) <= toi_da_lenh else lenh.sample(toi_da_lenh, random_state=0)
    t0 = mau["mo"].to_numpy("datetime64[ns]")
    gia = mau["gia_mo"].to_numpy(float)
    tol = dung_sai_pip * pip
    kq = {}
    for phut in range(-toi_da_gio * 60, toi_da_gio * 60 + 1, buoc_phut):
        t = t0 + np.timedelta64(phut * 60, "s")
        j = np.searchsorted(idx, t, side="right") - 1
        ok_j = (j >= 0) & (j < len(idx)) & (t < idx[np.clip(j, 0, len(idx) - 1)] + np.timedelta64(int(bar_s * 2), "s"))
        jj = np.clip(j, 0, len(idx) - 1)
        trong = (gia >= lo[jj] - tol) & (gia <= hi[jj] + tol) & ok_j
        kq[phut] = float(trong.mean())
    tot = max(kq, key=kq.get)
    khac = [v for p, v in kq.items() if abs(p - tot) >= 60]
    nhi = max(khac) if khac else 0.0
    cach = kq[tot] - nhi
    return {"lech_gio": tot / 60.0, "ty_le_gia_trong_bar": round(kq[tot], 3), "ty_le_tot_nhi_khac": round(nhi, 3),
            "tin_cay": "cao" if (kq[tot] >= 0.85 and cach >= 0.25) else ("vua" if (kq[tot] >= 0.7 and cach >= 0.12) else "thap"),
            "so_lenh_dung": int(len(mau)), "bar_giay": bar_s}


# ============================================================== 5. DIEU KIEN VAO LENH
def _vi_tri_bar(idx: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Chi so bar chua thoi diem t (bar bat dau <= t); -1 neu truoc bar dau, SAU bar cuoi hoac roi vao lo hong du lieu
    (> 2 chu ky bar ke tu bar gan nhat) - mot lenh sau het du lieu khong duoc dinh vao bar cuoi."""
    j = np.searchsorted(idx, t, side="right") - 1
    if len(idx) < 2:
        return j
    bar_ns = int(np.median(np.diff(idx).astype("timedelta64[s]").astype(np.int64))) * 2 * 10**9
    jj = np.clip(j, 0, len(idx) - 1)
    qua_xa = (t - idx[jj]).astype("timedelta64[ns]").astype(np.int64) >= bar_ns
    return np.where(qua_xa | (j < 0), -1, j)


def _su_kien_vao(ro: pd.DataFrame, bar_idx: np.ndarray, lech_s: float) -> pd.DataFrame:
    """Moi RO la mot su kien vao lenh tai bar `j`. `loai`: `vao_lai_ngay` (ro truoc cung chieu vua dong <= GAP_NGAY_GIAY) hay
    `cho_roi_vao` (dau tien, hoac sau mot khoang rang) - chi loai sau moi co dieu kien vao DOC LAP voi ro truoc."""
    r = ro.sort_values(["ma", "chieu", "mo"]).copy()
    prev_dong = r.groupby(["ma", "chieu"])["dong"].shift(1)
    gap = (r["mo"] - prev_dong).dt.total_seconds()
    r["loai"] = np.where(gap <= GAP_NGAY_GIAY, "vao_lai_ngay", "cho_roi_vao")
    r["j"] = _vi_tri_bar(bar_idx, (r["mo"] + pd.to_timedelta(lech_s, unit="s")).to_numpy("datetime64[ns]"))
    return r.sort_values("mo").reset_index(drop=True)


def _rang_theo_bar(ro: pd.DataFrame, bar_idx: np.ndarray, lech_s: float, chieu: int | None) -> np.ndarray:
    """`rang[j]` = True neu LUC BAT DAU bar j khong co lenh nao (cung chieu neu chieu != None) dang mo."""
    r = ro if chieu is None else ro[ro["chieu"] == chieu]
    mo = (r["mo"] + pd.to_timedelta(lech_s, unit="s")).to_numpy("datetime64[ns]")
    dong = np.where(r["dong"].isna(), np.datetime64("2200-01-01T00:00:00"),             # chua dong = mo den het du lieu
                    (r["dong"] + pd.to_timedelta(lech_s, unit="s")).to_numpy("datetime64[ns]"))
    so_mo = np.searchsorted(np.sort(mo), bar_idx, side="right")
    so_dong = np.searchsorted(np.sort(dong), bar_idx, side="right")
    return (so_mo - so_dong) <= 0


def _hang_cho_cot(X: pd.DataFrame) -> np.ndarray:
    return X.rank(method="average").to_numpy(float)


def _auc_va_nguong(x_pos: np.ndarray, x_ctl: np.ndarray) -> tuple[float, str, float, float, float]:
    """(auc, phep, nguong, tpr, fpr): nguong toi da hoa Youden J tren MOI diem cat that (trong mau - uoc luong lac quan);
    nguong dat o GIUA hai gia tri ke nhau nen luat `< nguong` dung dung cho tap duong tinh."""
    n_p, n_c = len(x_pos), len(x_ctl)
    tat = np.concatenate([x_pos, x_ctl])
    la_duong = np.r_[np.ones(n_p, bool), np.zeros(n_c, bool)]
    hang = pd.Series(tat).rank(method="average").to_numpy()
    auc = (hang[:n_p].sum() - n_p * (n_p + 1) / 2.0) / (n_p * n_c)
    phep = ">" if auc >= 0.5 else "<"
    thu_tu = np.argsort(tat if phep == "<" else -tat, kind="stable")
    v = (tat if phep == "<" else -tat)[thu_tu]
    duong_tich = np.cumsum(la_duong[thu_tu])
    ctl_tich = np.cumsum(~la_duong[thu_tu])
    # chi cat o CHO gia tri doi (cac diem trung gia tri di cung nhau)
    cat = np.flatnonzero(np.r_[v[1:] > v[:-1], False])
    if len(cat) == 0:
        return float(auc), phep, float(np.median(tat)), 0.0, 0.0
    tpr, fpr = duong_tich[cat] / n_p, ctl_tich[cat] / n_c
    k = int(np.argmax(tpr - fpr))
    i = cat[k]
    ng = 0.5 * (v[i] + v[i + 1])
    ng = ng if phep == "<" else -ng
    return float(auc), phep, float(ng), float(tpr[k]), float(fpr[k])


def _chuan_bi_tim(bar: pd.DataFrame, ro: pd.DataFrame, chieu: int | None, dich: int, lech_s: float,
                  chon: list[str] | None) -> dict:
    """Gom: tap bar ung vien E (bar rang, du lich su dac trung), nhan duong (co vao trong bar), bang dac trung dich `dich` bar."""
    idx = bar.index.to_numpy("datetime64[ns]")
    sk = _su_kien_vao(ro if chieu is None else ro[ro["chieu"] == chieu], idx, lech_s)
    sk = sk[(sk["j"] >= dich) & (sk["j"] < len(idx))]
    X = DT.tinh(bar, chon=chon)
    Xd = X.shift(dich)                                   # dac trung duoc BIET luc bar j mo = bar j - dich
    rang = _rang_theo_bar(ro, idx, lech_s, chieu)
    j_dau, j_cuoi = (int(sk["j"].min()), int(sk["j"].max())) if len(sk) else (0, -1)
    cua_so = np.zeros(len(idx), bool)
    cua_so[max(j_dau - 1, 0): j_cuoi + 1] = True
    return {"idx": idx, "su_kien": sk, "X": Xd, "rang": rang, "cua_so": cua_so}


def _tim_bang_dich_chuyen(rk: np.ndarray, pos: np.ndarray, so_null: int, rng: np.random.RandomState,
                          dich_toi_thieu: int = 50) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """AUC quan sat + AUC cua `so_null` lan DICH VONG vi tri cac su kien trong chuoi bar ung vien (giu cum thoi gian cua su kien
    va tu tuong quan cua dac trung) -> p tung dac trung va p da sua theo viec tim tren NHIEU dac trung (max |AUC - 0,5|)."""
    n = rk.shape[0]
    n_p = len(pos)
    n_c = n - n_p
    chuan = n_p * (n_p + 1) / 2.0
    auc = (rk[pos].sum(0) - chuan) / (n_p * n_c)
    lech = np.abs(auc - 0.5)
    ngau = np.empty((so_null, rk.shape[1]))
    lo_s, hi_s = min(dich_toi_thieu, n // 4), max(n - dich_toi_thieu, n - n // 4)
    for s in range(so_null):
        k = rng.randint(lo_s, max(lo_s + 1, hi_s))
        ngau[s] = np.abs((rk[(pos + k) % n].sum(0) - chuan) / (n_p * n_c) - 0.5)
    p_rieng = (1 + (ngau >= lech[None, :] - 1e-12).sum(0)) / (1.0 + so_null)
    max_ngau = ngau.max(axis=1)
    p_nhom = (1 + (max_ngau[:, None] >= lech[None, :] - 1e-12).sum(0)) / (1.0 + so_null)
    return auc, p_rieng, p_nhom


def tim_dieu_kien_vao(bar: pd.DataFrame, ro: pd.DataFrame, dich: int = 1, lech_gio: float = 0.0, so_null: int = 200,
                      toi_thieu_su_kien: int = 30, chon: list[str] | None = None, seed: int = 0) -> dict:
    """So bar luc nguoi do VAO lenh (khong tinh mo lai ngay sau TP) voi bar rang ma ho KHONG vao, tren bo dac trung ngu phap.

    Dac trung cua bar j chi lay tu bar `j - dich` tro ve truoc (dich >= 1: khong nhin truoc). Tra tung dac trung: auc, huong,
    nguong (toi da hoa Youden J trong mau), tpr/fpr, p_null (dich vong - xem `_tim_bang_dich_chuyen`), p_nhom (da tinh viec
    tim tren moi dac trung), dieu_kien DSL. Su kien it (< toi_thieu_su_kien) thi CHUA_DO_DUOC, khong doan."""
    if dich < 1:
        raise ValueError("dich >= 1: dac trung phai la thu BIET truoc khi lenh mo (khong nhin truoc)")
    lech_s = lech_gio * 3600.0
    out = {"dich": dich, "lech_gio": lech_gio, "theo_chieu": {}}
    rng = np.random.RandomState(seed)
    dem_chieu = ro["chieu"].value_counts()
    for chieu, ten in ((1, "mua"), (-1, "ban")):
        if dem_chieu.get(chieu, 0) < toi_thieu_su_kien:
            continue
        cb = _chuan_bi_tim(bar, ro, chieu, dich, lech_s, chon)
        sk = cb["su_kien"]
        cho = sk[sk["loai"] == "cho_roi_vao"]
        mac = {"so_ro": int(len(sk)), "so_cho_roi_vao": int(len(cho)),
               "vao_lai_ngay_ty_le": round(1 - len(cho) / max(len(sk), 1), 3)}
        if len(cho) < toi_thieu_su_kien:
            mac.update(trang_thai="CHUA_DO_DUOC",
                       ly_do=("chi %d lan vao doc lap (con lai la mo lai ngay sau TP): lenh vao hau nhu khong co dieu kien "
                              "rieng" % len(cho)))
            out["theo_chieu"][ten] = mac
            continue
        E = np.flatnonzero(cb["rang"] & cb["cua_so"])
        X = cb["X"].iloc[E]
        X = X.loc[:, X.isna().mean() < 0.2]
        ok = ~X.isna().any(axis=1).to_numpy()
        E, X = E[ok], X.loc[ok]
        pos_j = set(int(j) for j in cho["j"])
        la_pos = np.array([int(j) in pos_j for j in E])
        if la_pos.sum() < toi_thieu_su_kien or (~la_pos).sum() < 100 or X.shape[1] == 0:
            mac.update(trang_thai="CHUA_DO_DUOC",
                       ly_do="chi %d su kien vao nam trong bar rang co du dac trung (can >= %d)" % (int(la_pos.sum()), toi_thieu_su_kien))
            out["theo_chieu"][ten] = mac
            continue
        rk = _hang_cho_cot(X)
        pos = np.flatnonzero(la_pos)
        auc, p_r, p_n = _tim_bang_dich_chuyen(rk, pos, so_null, rng)
        ten_dt = list(X.columns)
        xs = X.to_numpy(float)
        top = []
        for f in np.argsort(-np.abs(auc - 0.5))[:8]:
            a, phep, ng, tpr, fpr = _auc_va_nguong(xs[la_pos, f], xs[~la_pos, f])
            top.append({"dac_trung": ten_dt[f], "auc": round(max(float(auc[f]), 1.0 - float(auc[f])), 4), "phep": phep,
                        "nguong": round(ng, 4),
                        "tpr": round(tpr, 3), "fpr": round(fpr, 3), "p_null": round(float(p_r[f]), 4),
                        "p_nhom": round(float(p_n[f]), 4), "mq5_duoc": DT.dich_duoc_mq5(ten_dt[f]),
                        "dieu_kien": DT.dieu_kien(ten_dt[f], phep, ng)})
        mac.update(trang_thai="DAT", so_bar_ung_vien=int(len(E)), ty_le_vao_khi_rang=round(float(la_pos.mean()), 4),
                   so_dac_trung=len(ten_dt), top=top,
                   doc_dung=("auc theo HUONG cua phep (>= 0,5; 0,5 = khong phan biet); p_nhom da tinh viec tim tren %d dac trung "
                             "(dich vong %d lan). nguong / tpr / fpr "
                             "la TRONG MAU (lac quan). Day la MO TA hanh vi nguoi do - thu bang thu_co_che tren doan KHAC cua ho."
                             % (len(ten_dt), so_null)))
        out["theo_chieu"][ten] = mac
    out["trang_thai"] = "DAT" if any(v.get("trang_thai") == "DAT" for v in out["theo_chieu"].values()) else "CHUA_DO_DUOC"
    if out["trang_thai"] != "DAT":
        out["ly_do"] = "khong chieu nao du su kien vao DOC LAP de so voi bar doi chung: %s" % json.dumps(
            {k: v.get("ly_do") for k, v in out["theo_chieu"].items()}, ensure_ascii=False)
    return out


def khop_luat(bar: pd.DataFrame, ro: pd.DataFrame, luat: list[dict], chieu: int, dich: int = 1, lech_gio: float = 0.0,
              so_null: int = 300, seed: int = 0) -> dict:
    """Cham mot LUAT DSL (list dieu kien `{trai, phep, phai}`) do AI de xuat bang chinh so lenh that: luat dung nhu mot bo phan loai
    'bar nay nguoi do co vao khong'. Tra tpr (ty le lan vao ma luat dung), fpr (ty le bar rang ma luat dung), lift, p_null (dich vong)."""
    cb = _chuan_bi_tim(bar, ro, chieu, dich, lech_gio * 3600.0, ["rsi2"])        # chi lay lich su vi tri, dac trung that lay ben duoi
    sk = cb["su_kien"]
    cho = sk[sk["loai"] == "cho_roi_vao"]
    E = np.flatnonzero(cb["rang"] & cb["cua_so"])
    if len(cho) < 20 or len(E) < 100:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "chi %d su kien vao doc lap / %d bar rang" % (len(cho), len(E))}
    R = NP._dieu_kien(bar, list(luat), mac_dinh=False).shift(dich).fillna(False).to_numpy(bool)
    la_pos = np.isin(E, cho["j"].to_numpy())
    r = R[E]
    tpr, fpr = float(r[la_pos].mean()), float(r[~la_pos].mean())
    co_luat = float(r.mean())
    lift = tpr / co_luat if co_luat > 0 else float("nan")
    # null dich vong: thong ke = tpr - fpr
    rng = np.random.RandomState(seed)
    pos = np.flatnonzero(la_pos)
    n = len(E)
    rv = r.astype(float)
    tong_r = rv.sum()
    stat = tpr - fpr
    ngau = []
    for _ in range(so_null):
        k = rng.randint(max(50, n // 8), max(51, n - max(50, n // 8)))
        ps = (pos + k) % n
        a = rv[ps].sum()
        ngau.append(a / len(pos) - (tong_r - a) / (n - len(pos)))
    p = (1 + sum(abs(x) >= abs(stat) - 1e-12 for x in ngau)) / (1.0 + so_null)
    return {"trang_thai": "DAT", "tpr": round(tpr, 3), "fpr": round(fpr, 3), "lift": round(lift, 3), "p_null": round(p, 4),
            "so_su_kien": int(la_pos.sum()), "so_bar_ung_vien": int(n),
            "ty_le_bar_luat_dung": round(co_luat, 4),
            "doc_dung": "luat do AI de xuat (1 phep thu): p_null la dich vong 1 luat, khong sua theo so luat da thu ngoai ham nay."}


# ============================================================== 6. PHAT LAI
def phat_lai(bar: pd.DataFrame, tham_so: dict, ro_that: pd.DataFrame, qc=None, hop_dong: float = HOP_DONG_MAC_DINH,
             spread_pip: float = 0.0) -> dict:
    """Chay `tham_so` qua `luoi.chay(ghi_lenh=True)` tren `bar`, qua CUNG duong ong gom ro nhu lich su that, roi so voi ro THAT
    trong cung khoang thoi gian.

    So SO DEM (ro bat dau, lenh, do sau, TP) - KHONG so tien, KHONG so tung moc gio: ro luoi di theo duong gia nen lech mot bar o dau
    keo lech ca chuoi sau do (hon do, khong phai loi). Ro dau tien cua mo phong la ro nhan tao (luoi.chay mo luc bar dau)."""
    if bar is None or len(bar) < 100:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "bar qua ngan"}
    t0, t1 = bar.index[0], bar.index[-1]
    that = ro_that[(ro_that["mo"] >= t0) & (ro_that["mo"] <= t1)]
    if len(that) < 10:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "chi %d ro that nam trong khoang bar (%s .. %s)" % (len(that), t0, t1)}
    ts = LU.ThamSo(**tham_so)
    qc = qc or LU.QC_AUDCAD
    kq = LU.chay(bar, ts, 1e12, qc, ghi_lenh=True)
    ln = kq.lenh
    sim = chuan_hoa(ln[["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong"]]
                    .assign(ma="SIM", chieu=np.where(ln["chieu"] > 0, "buy", "sell")), pip=qc.pip)
    sim_ro = bang_ro(phan_ro(sim), qc.pip, hop_dong)
    so_nam = max((t1 - t0).days / 365.25, 1e-9)
    tuan = lambda r: r.set_index("mo").resample("W").size()
    tuan_that = tuan(that)
    tuan_sim = tuan(sim_ro).reindex(tuan_that.index, fill_value=0)
    tq = (float(np.corrcoef(tuan_that.to_numpy(float), tuan_sim.to_numpy(float))[0, 1])
          if len(tuan_that) >= 8 and tuan_that.std() > 0 and tuan_sim.std() > 0 else None)
    ty = lambda a, b: round(float(a) / float(b), 3) if b else None
    th_dong, sm_dong = that[that["da_dong"]], sim_ro[sim_ro["da_dong"]]
    ra = ty(len(sim_ro), len(that))
    out = {"trang_thai": "DAT", "so_nam": round(so_nam, 2), "tham_so_chay": tham_so,
           "ro_bat_dau": {"that": int(len(that)), "mo_phong": int(len(sim_ro)), "ty_le_mo_phong/that": ra},
           "lenh": {"that": int(that["so_lenh"].sum()), "mo_phong": int(len(ln)),
                    "ty_le_mo_phong/that": ty(len(ln), that["so_lenh"].sum())},
           "do_sau": {"that_tb": round(float(that["so_lenh"].mean()), 2), "mo_phong_tb": round(float(sim_ro["so_lenh"].mean()), 2),
                      "that_max": int(that["so_lenh"].max()), "mo_phong_max": int(sim_ro["so_lenh"].max())},
           "tp_pip_trung_vi": {"that": round(float(th_dong["tp_pip"].median()) + spread_pip, 2) if len(th_dong) else None,
                               "mo_phong": round(float(sm_dong["tp_pip"].median()), 2) if len(sm_dong) else None},
           "tuong_quan_ro_theo_tuan": round(tq, 3) if tq is not None else None,
           "chay_tai_khoan_mo_phong": bool(kq.chay)}
    lech = abs(math.log(ra)) if ra else None
    out["khop"] = ("tot" if lech is not None and lech < 0.15 else "vua" if lech is not None and lech < 0.35 else "lech")
    out["doc_dung"] = ("so DEM, khong so tien; lech < 15% ve so ro la khop tot. Tham so dung nhung bar thieu tick thi so ro that "
                       "NHIEU HON mo phong (bar lam mat vong lap trong bar): xem `ro_bat_dau`.")
    return out


# ============================================================== NHAC TOAN BO
def boc(lenh, bar: pd.DataFrame | None = None, pip: float | None = None, ma: str | None = None,
        hop_dong: float = HOP_DONG_MAC_DINH, lech_gio: float | None = None, dich: int = 1, so_null: int = 200,
        qc=None, phat: bool = True, spread_pip: float | None = None) -> dict:
    """Ca duong ong: chuan hoa -> gom ro -> suy tham so -> (co bar) can gio, tim dieu kien vao, phat lai. Bo cac truong `_`.
    `spread_pip` mac dinh = trung vi cot `spread` (POINT) cua bar doi pip (point = qc.point, khong co qc thi pip / 10)."""
    # bang da chuan hoa (co the chi gom lenh MUA: cot chieu toan +1 mo ho voi enum MT5) thi khong chuan hoa lai
    d = lenh if (isinstance(lenh, pd.DataFrame) and lenh.attrs.get("da_chuan_hoa")) else chuan_hoa(lenh, pip=pip, ma=ma)
    if spread_pip is None and bar is not None and "spread" in bar.columns:
        point = qc.point if qc is not None else d.attrs["pip"] / 10.0
        sp = float(pd.to_numeric(bar["spread"], errors="coerce").median())
        spread_pip = round(sp * point / d.attrs["pip"], 3) if math.isfinite(sp) else None
    ra = phan_tich_lenh(d, hop_dong, spread_pip)
    if ra.get("trang_thai") != "DAT":
        return ra
    ro, dl = ra.pop("_ro"), ra.pop("_lenh")
    p = ra["pip"]
    if bar is None:
        ra["buoc_ke_tiep"] = ["co bar cua ma nay (b nc cc boc_lich_su kem ma + khung) de can gio, tim dieu kien vao va phat lai"]
    else:
        lg = uoc_lech_gio(bar, d, p) if lech_gio is None else {"lech_gio": float(lech_gio), "tin_cay": "nguoi_dung_dat"}
        ra["lech_gio"] = lg
        g = lg.get("lech_gio")
        if g is None or lg.get("tin_cay") == "thap":
            ra["canh_bao"].append("chua can duoc gio lich su voi bar (tin cay thap): dieu kien vao & phat lai co the SAI. Dat lech_gio "
                                  "neu biet gio may chu cua ho.")
        ra["dieu_kien_vao"] = tim_dieu_kien_vao(bar, ro, dich=dich, lech_gio=g or 0.0, so_null=so_null)
        if phat and ra.get("tham_so"):
            ro_bar = ro.copy()
            ro_bar["mo"] = ro_bar["mo"] + pd.to_timedelta((g or 0.0) * 3600.0, unit="s")
            ra["phat_lai"] = phat_lai(bar, ra["tham_so"], ro_bar, qc, hop_dong, spread_pip or 0.0)
    ra["buoc_ke_tiep"] = ra.get("buoc_ke_tiep") or []
    if ra.get("tham_so"):
        ra["buoc_ke_tiep"].append("thu_luoi tham_so=%s tren doan kham_pha NGOAI cua so song cua nguoi do"
                                  % json.dumps(ra["tham_so"], ensure_ascii=False, sort_keys=True))
    return ra


def goi_cho_json(x):
    """DataFrame / numpy -> kieu JSON thuan (de ghi so tay)."""
    if isinstance(x, dict):
        return {str(k): goi_cho_json(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, (list, tuple)):
        return [goi_cho_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if (isinstance(x, float) and not math.isfinite(x)) else float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (pd.Timestamp,)):
        return str(x)
    return x
