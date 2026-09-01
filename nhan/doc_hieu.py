# -*- coding: utf-8 -*-
"""doc_hieu.py - DOC VAN XUOI THANH CO CHE KIEM DINH DUOC.

VAN DE NO GIAI (do that tren so cai 23/08/2026):
  Kho co 326 ban doc. Trong do 167 ban `khong_doc_duoc` (0 ky tu), 121 ban
  `ma_nguon` (repo GitHub do nguyen si), 38 ban `khac`. **KHONG MOT BAN NAO
  la mot bai viet mo ta chien luoc bang chu.** Va 18 co che trong
  `config/co_che_dsl.json` deu do tang NGHI tu nghi ra - `nguon` = None ca 18.
  Tuc la: sau ba tuan doc, so co che HOC DUOC TU TAI LIEU van bang 0.

  Duong tu van ban sang co che von co MOT ban: `tru/seeker.boc_co_che()`, goi
  LLM. No dang TAT (`tri_tue.duong = "tat"`, khong co khoa OpenAI) va bi V2 go
  khoi `mot_luot()`. Mot day chuyen 24/7 khong duoc phu thuoc vao mot cai cong
  chi mo khi co nguoi tra tien token.

CACH GIAI:
  Module nay doc van xuoi bang CU PHAP, khong bang mo hinh. No nhan dang mot
  CAU LUAT ("buy when the 2-period RSI closes below 10") va dich thang sang
  `nhan/ngu_phap.py` - dung ngu phap ma tang NGHI dang dung, di qua dung cac
  bai kiem do (cu phap, ty le kich hoat, phep cat nhin truoc), tieu dung dung
  ngan sach FDR. Khong sinh ma, khong `exec`, khong duong tat.

  Han che la CO Y: mot cau khong co CON SO thi khong dung duoc thanh spec.
  "Buy when RSI is oversold" -> tu choi. Doan nguong = bia ra mot con so roi
  kiem dinh chinh no; do la overfit truoc khi backtest bat dau.

HAI CHIEU HIEU CHUAN (bat buoc):
  Bo doc nay phai TU CHOI: cau khong co nguong, cau chi nhac ten chi bao, van
  ban ngoai nganh, quang cao, va cau co "or" (ngu phap chi co VA).
  Va phai NHAN DUOC: cau luat that lay tu bai viet that, ke ca khi viet duoi
  dang bang ("Entry: RSI(2) < 10") hay dang cau ("go long when ...").

TRUNG LAP KHONG PHAI TIN MOI:
  12 bai viet cung ta RSI(2)<10 la MOT co che voi 12 trich dan, khong phai 12
  suat kiem dinh. `van_tay_spec` bam theo CAU TRUC (da chuan hoa), nen ban sao
  gop vao lam BANG CHUNG chu khong an them mot slot FDR.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from html import unescape as _unescape
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import ngu_phap as NP
else:
    from . import ngu_phap as NP


# --------------------------------------------------------------- TU VUNG
#: Hanh dong MO vi the MUA.
HD_MUA = (r"(?:buy(?:s|ing)?|go(?:es|ing)? long|enter(?:s|ing)? (?:a |the )?long"
          r"|open(?:s|ing)? (?:a |the )?long|take (?:a |the )?long"
          r"|long (?:entry|signal|position|setup)|mua vao|vao lenh mua)")
#: Hanh dong MO vi the BAN. Phai kiem TRUOC `HD_RA`: "sell short" co chu "sell".
HD_BAN = (r"(?:sell(?:s|ing)? short|short(?:s|ing)? (?:the |a )?(?:market|stock|index|position)"
          r"|go(?:es|ing)? short|enter(?:s|ing)? (?:a |the )?short"
          r"|open(?:s|ing)? (?:a |the )?short|short (?:entry|signal|position|setup)"
          r"|ban khong|vao lenh ban)")
#: Hanh dong DONG vi the.
HD_RA = (r"(?:sell(?:s|ing)?|exit(?:s|ing)?|close(?:s|ing)? (?:the |our |any )?(?:position|trade|long|short)"
         r"|take profit|liquidat|cover(?:s|ing)? (?:the )?short|thoat lenh|chot loi|dong lenh)")

#: Tu bat dau MENH DE DIEU KIEN.
NEU = r"(?:when(?:ever)?|if|once|as soon as|provided that|so long as|khi|neu)"

#: Nhan dang dang BANG/DAU DONG: "Entry: ...", "Buy rule - ...", "Exit signal:"
NHAN_VAO = re.compile(
    r"(?:^|\n|•|\*|\-\s)\s*(?:long |buy |entry|vao lenh|dieu kien vao)"
    r"[a-z ]{0,14}?(?:rule|signal|condition|criteria|setup)?s?\s*[:\-–]", re.I)
NHAN_RA = re.compile(
    r"(?:^|\n|•|\*|\-\s)\s*(?:exit|sell |close |chot loi|thoat lenh|dieu kien ra)"
    r"[a-z ]{0,14}?(?:rule|signal|condition|criteria)?s?\s*[:\-–]", re.I)

#: So sanh. Thu tu QUAN TRONG: cum dai ("crosses above") phai dung truoc cum
#: ngan ("above"), neu khong "crosses above" bi doc thanh ">".
SO_SANH: tuple[tuple[str, str], ...] = (
    (r"cross(?:es|ed|ing)?\s+(?:back\s+)?(?:above|over|up through)", "cheo_len"),
    (r"cross(?:es|ed|ing)?\s+(?:back\s+)?(?:below|under|down through)", "cheo_xuong"),
    (r"mov(?:es|ed|ing)?\s+above", "cheo_len"),
    (r"mov(?:es|ed|ing)?\s+below", "cheo_xuong"),
    (r"(?:is |are |be )?(?:at or (?:below|under)|no (?:higher|greater) than"
     r"|less than or equal to|<=)", "<="),
    (r"(?:is |are |be )?(?:at or above|no (?:lower|less) than"
     r"|greater than or equal to|>=)", ">="),
    (r"(?:clos(?:es|ed|ing)|fall(?:s|ing)?|drop(?:s|ping)?|dip(?:s|ping)?"
     r"|declin(?:es|ing)|trad(?:es|ing)|settl(?:es|ing))?\s*"
     r"(?:is |are |be |go(?:es)? )?(?:below|under|beneath|less than|lower than"
     r"|smaller than|duoi|nho hon)", "<"),
    (r"(?:clos(?:es|ed|ing)|ris(?:es|ing)|climb(?:s|ing)?|jump(?:s|ing)?"
     r"|trad(?:es|ing)|settl(?:es|ing))?\s*"
     r"(?:is |are |be |go(?:es)? )?(?:above|over|exceed(?:s|ing)?|greater than"
     r"|higher than|larger than|tren|lon hon)", ">"),
    (r"<=", "<="), (r">=", ">="), (r"<", "<"), (r">", ">"),
)
_SO_SANH_RE = [(re.compile(p, re.I), phep) for p, phep in SO_SANH]

_SO = r"[-+]?\d+(?:[.,]\d+)?"


def _tb(n, loai="sma", cot="close"):
    return {"chi_bao": loai, "n": int(n), "cot": cot}


#: Toan hang. Moi muc: (regex, ham dung toan hang, la_gia).
#: `la_gia` = True nghia la toan hang GIA thuan tuy - khi quet ben trai, mot
#: toan hang chi bao bao gio cung duoc uu tien hon gia, vi cau
#: "RSI(2) closes below 10" co chu "closes" nhung ve trai la RSI.
_TOAN_HANG: tuple[tuple[str, object, bool], ...] = (
    # --- chi bao co chu ky ro rang ---
    (r"\b(\d+)[-\s](?:period|day|bar|week|month)s?\s+rsi\b",
     lambda m: {"chi_bao": "rsi", "n": int(m.group(1))}, False),
    (r"\brsi\s*\(?\s*(\d+)\s*\)?(?!\s*\d)",
     lambda m: {"chi_bao": "rsi", "n": int(m.group(1))}, False),
    (r"\b(?:rsi|relative strength index)\b",
     lambda m: {"chi_bao": "rsi", "n": 14, "_mac_dinh": "n"}, False),
    (r"\b(?:ibs|internal bar strength)\b", lambda m: {"chi_bao": "ibs"}, False),
    # z-score CHI khi bai viet noi ro chu ky. Dang tran ("absolute z-score >
    # 1.5" trong bai pairs trading) khong nhan: z-score cua CAI GI, trong bao
    # nhieu bar - doan hai thu do la bia ra mot co che roi kiem dinh chinh no.
    (r"\b(\d+)[-\s](?:day|period|bar)s?\s+z[-\s]?score\b",
     lambda m: {"chi_bao": "zscore", "n": int(m.group(1)),
                "cua": {"chi_bao": "gia", "cot": "close"}}, False),
    (r"\batr\s*\(?\s*(\d+)\s*\)?", lambda m: {"chi_bao": "atr", "n": int(m.group(1))}, False),
    (r"\b(?:atr|average true range)\b",
     lambda m: {"chi_bao": "atr", "n": 14, "_mac_dinh": "n"}, False),
    # --- trung binh dong: nhieu cach viet ---
    (r"\b(\d+)[-\s](?:day|period|bar|week)s?\s+exponential\s+(?:moving average|ma|ema)\b",
     lambda m: _tb(m.group(1), "ema"), False),
    (r"\b(\d+)[-\s](?:day|period|bar|week)s?\s+(?:simple\s+)?(?:moving average|ma|sma)\b",
     lambda m: _tb(m.group(1), "sma"), False),
    (r"\bema\s*\(?\s*(\d+)\s*\)?", lambda m: _tb(m.group(1), "ema"), False),
    (r"\b(?:sma|ma)\s*\(\s*(\d+)\s*\)", lambda m: _tb(m.group(1), "sma"), False),
    (r"\b(\d+)\s*(?:day\s*)?ema\b", lambda m: _tb(m.group(1), "ema"), False),
    (r"\b(\d+)\s*(?:day\s*)?(?:sma|ma)\b", lambda m: _tb(m.group(1), "sma"), False),
    # --- dinh/day N bar (LUI mot bar: dinh cua N bar TRUOC do) ---
    (r"\b(\d+)[-\s](?:day|period|bar|week)s?\s+(?:high|highest high)\b",
     lambda m: {"chi_bao": "cao_nhat", "n": int(m.group(1)),
                "cua": {"chi_bao": "tre", "n": 1,
                        "cua": {"chi_bao": "gia", "cot": "high"}}}, False),
    (r"\b(\d+)[-\s](?:day|period|bar|week)s?\s+(?:low|lowest low)\b",
     lambda m: {"chi_bao": "thap_nhat", "n": int(m.group(1)),
                "cua": {"chi_bao": "tre", "n": 1,
                        "cua": {"chi_bao": "gia", "cot": "low"}}}, False),
    # --- lich / phien ---
    (r"\b(?:hour of (?:the )?day|time of day|session hour)\b",
     lambda m: {"chi_bao": "gio"}, False),
    (r"\bday of (?:the )?month\b", lambda m: {"chi_bao": "ngay_trong_thang"}, False),
    # --- gia ---
    (r"\bprevious (?:day'?s? |bar'?s? )?(?:close|closing price)\b",
     lambda m: {"chi_bao": "tre", "n": 1,
                "cua": {"chi_bao": "gia", "cot": "close"}}, True),
    (r"\bprevious (?:day'?s? |bar'?s? )?low\b",
     lambda m: {"chi_bao": "tre", "n": 1,
                "cua": {"chi_bao": "gia", "cot": "low"}}, True),
    (r"\bprevious (?:day'?s? |bar'?s? )?high\b",
     lambda m: {"chi_bao": "tre", "n": 1,
                "cua": {"chi_bao": "gia", "cot": "high"}}, True),
    (r"\b(?:the )?clos(?:e|es|ed|ing)(?:\s+price)?\b",
     lambda m: {"chi_bao": "gia", "cot": "close"}, True),
    (r"\b(?:the )?open(?:s|ed|ing)?(?:\s+price)?\b",
     lambda m: {"chi_bao": "gia", "cot": "open"}, True),
    (r"\bintraday high\b", lambda m: {"chi_bao": "gia", "cot": "high"}, True),
    (r"\bintraday low\b", lambda m: {"chi_bao": "gia", "cot": "low"}, True),
    (r"\b(?:the )?price\b", lambda m: {"chi_bao": "gia", "cot": "close"}, True),
)
_TOAN_HANG_RE = [(re.compile(p, re.I), f, g) for p, f, g in _TOAN_HANG]

#: Toan hang co GIA TRI CHUAN 0..1 -> "10%" phai doi ra 0,1.
_TY_LE = {"ibs", "phan_vi", "doi_pct"}

BOLL = re.compile(r"\b(?:(\d+)[-\s](?:day|period)\s+)?bollinger\s+band", re.I)
BOLL_DUOI = re.compile(r"\blower\s+(?:bollinger\s+)?band\b", re.I)
BOLL_TREN = re.compile(r"\bupper\s+(?:bollinger\s+)?band\b", re.I)

GIU_RE = re.compile(
    r"\b(?:hold(?:ing)?|stay(?:ing)? (?:in|long)|remain(?:ing)? (?:in|long)"
    r"|exit(?:ing)? after|sell(?:ing)? after|giu)\s+"
    r"(?:for\s+|the\s+(?:next\s+)?)?(\d+)\s*(?:day|bar|week|session|ngay|nen)s?", re.I)
GIU_RE2 = re.compile(r"\b(\d+)[-\s](?:day|bar|session)\s+hold(?:ing)?\s+period\b", re.I)
#: "Holding period: 5 days" - cach viet pho bien khong kem "5-day holding period".
GIU_RE3 = re.compile(r"\bhold(?:ing)?\s+period\s*(?:of|is|:|=)?\s*(\d+)\s*"
                     r"(?:day|bar|week|session|ngay|nen)s?\b", re.I)


# ------------------------------------------------------------------ TIEN XU LY
def _chuan(vb: str) -> str:
    """Bo HTML, gop trang, GIU xuong dong de con nhan duoc dau dong."""
    vb = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", vb or "", flags=re.S | re.I)
    vb = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</tr>", "\n", vb, flags=re.I)
    # Bo THE HTML, khong bo PHEP SO SANH. `<[^>]+>` an "< 5 ... the close >"
    # nguyen mot doan - va do dung la nhung cau dang gia nhat, vi bai viet nao
    # viet luat bang ky hieu deu co "<" va ">". Bay nay da an tron mot cau luat
    # that trong lan chay dau. The that luon bat dau bang chu cai, "/" hoac "!".
    vb = re.sub(r"<\s*/?[a-zA-Z!][^>\n]{0,400}>", " ", vb)
    # GIAI MA THUC THE HTML truoc khi phan tich. Bang thay the tay bo sot
    # `&apos;`, va thuc the do CO DAU CHAM PHAY - ma bo tach menh de lai cat o
    # dau chay phay/cham phay. Ket qua: cau "the 10-bar moving average of
    # Bitcoin&apos;s close sits above the 60-bar moving average" bi cat lam doi
    # va ve trai tu `sma10` thanh `close`. Mot co che SAI da duoc dang ky that
    # ngay 23/08 vi loi nay.
    vb = _unescape(vb).replace("’", "'")
    vb = re.sub(r"[ \t\r\f\v]+", " ", vb)
    return re.sub(r"\n{2,}", "\n", vb)


def cac_cau(vb: str) -> list[tuple[int, str]]:
    """Tach cau, GIU VI TRI ky tu de trich dan doi chieu duoc bang mat."""
    ra, dau = [], 0
    for m in re.finditer(r"[.!?\n;]+(?=\s|$)", vb):
        cau = vb[dau:m.start()].strip()
        if cau:
            ra.append((dau, cau))
        dau = m.end()
    con = vb[dau:].strip()
    if con:
        ra.append((dau, con))
    return ra


# ------------------------------------------------------------- PHAN TICH CAU
#: Cum DANH TU chua buy/sell nhung khong phai hanh dong giao dich. Do 01/09:
#: day la nguon bao dong gia lon nhat cua `loai_cau` - "on both the buy and sell
#: side", "its buyback program", "buyers and sellers", "the sell-side analyst".
_KHONG_PHAI_HANH_DONG = re.compile(
    r"(?:buy|sell)(?:[ -]?(?:side|back|er|ers|out|in)|s(?=[ ]side))"
    r"|buy and sell|buyers?|sellers?", re.I)


def loai_cau(cau: str) -> str | None:
    """'vao_mua' | 'vao_ban' | 'ra' | None.

    Thu tu kiem la co y: BAN truoc RA vi "sell short" chua chu "sell"; VAO
    truoc RA vi "buy" khong duoc doc thanh "dong vi the".
    """
    if NHAN_VAO.search(cau):
        return "vao_mua"
    if NHAN_RA.search(cau):
        return "ra"
    # DANH TU chua chu buy/sell nhung KHONG phai hanh dong. Bo truoc khi do:
    # "on both the buy and sell SIDE", "its BUYBACK program", "the BUYER".
    # Do 01/09: trong 1.289 cau bi cham la luat ma khong dich duoc, phan lon la
    # dang nay - bo doc tu choi chung la DUNG, nhung chung lam con so "cau dang
    # luat" phong len 5.386 va che mat cho hong that su o dau.
    sach = _KHONG_PHAI_HANH_DONG.sub(" ", cau)
    # Mot luat LUON co menh de dieu kien ("buy WHEN rsi < 10") hoac mot phep so
    # sanh. Dong tu tran khong kem dieu kien la van ke chuyen, khong phai luat.
    co_dieu_kien = bool(re.search(NEU, sach, re.I)
                        or re.search(r"(?:<|>|=|crosses|above|below|exceeds)",
                                     sach, re.I))
    if not co_dieu_kien:
        return None
    if re.search(HD_BAN, sach, re.I):
        return "vao_ban"
    if re.search(HD_MUA, sach, re.I):
        return "vao_mua"
    if re.search(HD_RA, sach, re.I):
        return "ra"
    return None


def _vung_dieu_kien(cau: str) -> str:
    """Phan cau SAU tu dieu kien. Khong co tu dieu kien -> lay ca cau (dang bang)."""
    m = re.search(r"\b" + NEU + r"\b", cau, re.I)
    return cau[m.end():] if m else cau


def _quet_toan_hang(doan: str, uu_tien_chi_bao: bool):
    """Tim toan hang trong mot doan. Tra (toan_hang, chu_khop) hoac None."""
    khop = []
    for bt, dung, la_gia in _TOAN_HANG_RE:
        for m in bt.finditer(doan):
            try:
                th = dung(m)
            except Exception:
                continue
            khop.append((m.start(), m.end(), th, la_gia, m.group(0)))
    if not khop:
        return None
    # BO KHOP BI NUOT: "2-period RSI" va "RSI" cung khop, "200-day moving
    # average" va "moving average" cung khop. Neu khong bo, phep chon "lay cai
    # cuoi cung ben trai" se lay CAI NGAN HON (no bat dau muon hon) va cho ra
    # `rsi n=14 mac dinh` tu mot cau da noi ro n=2. Loi nay da xay ra that o
    # lan chay dau tien cua module nay.
    khop = [k for k in khop
            if not any(o is not k and o[0] <= k[0] and o[1] >= k[1]
                       and (o[1] - o[0]) > (k[1] - k[0]) for o in khop)]
    if uu_tien_chi_bao:
        # ben TRAI: lay chi bao cuoi cung; khong co chi bao thi lay gia cuoi cung.
        cb = [k for k in khop if not k[3]]
        chon = max(cb or khop, key=lambda k: k[0])
    else:
        # ben PHAI: lay cai xuat hien SOM nhat; hoa thi chi bao thang gia
        # ("200-day moving average": ca so lan cum chi bao deu bat dau o "200").
        som = min(k[0] for k in khop)
        cung = [k for k in khop if k[0] == som]
        chon = sorted(cung, key=lambda k: (k[3], -(k[1] - k[0])))[0]
    return chon[2], chon[4], chon[0]


def _so_dau_tien(doan: str):
    m = re.search(_SO, doan)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ".")), m.start(), m.end()
    except ValueError:
        return None


#: Cum TRO LAI mot thu vua noi o ve vao. "exit when the closing price falls
#: below the average" - "the average" chinh la duong trung binh cau vao vua goi
#: ten. Khong noi lai duoc thi ve RA mat trang va co che bi doc thanh "giu 1
#: bar", sai han y tac gia.
TRO_LAI = re.compile(r"\bthe (?:moving )?average\b|\bthat (?:level|line)\b"
                     r"|\bthe (?:upper|lower) band\b|\bthe same (?:level|line)\b",
                     re.I)


def _ben_phai(doan: str, trai: dict, thay_the: dict | None = None):
    """Ve phai cua phep so sanh: mot con so, hoac mot toan hang khac."""
    th = _quet_toan_hang(doan, uu_tien_chi_bao=False)
    so = _so_dau_tien(doan)
    if th is None and so is None and thay_the is not None and TRO_LAI.search(doan):
        return dict(thay_the)
    if th is not None and so is not None and th[2] <= so[1]:
        return th[0]
    if so is not None:
        gt, dau, cuoi = so
        if doan[cuoi:cuoi + 2].strip().startswith("%") and (
                str(trai.get("chi_bao")) in _TY_LE):
            gt = gt / 100.0
        return {"hang": gt}
    return th[0] if th is not None else None


def _bollinger(doan: str) -> list[dict]:
    """"closes below the lower Bollinger band" -> zscore(close, n) < -k.

    Ngu phap khong co phep CONG/NHAN nen khong viet duoc `sma - k*sd` truc tiep.
    Nhung `close < sma_n - k*sd_n` TUONG DUONG `zscore_n(close) < -k` - cung mot
    tap bar, khong xap xi. Do la cach dai bang di vao duoc ngu phap nay.
    """
    co_duoi, co_tren = BOLL_DUOI.search(doan), BOLL_TREN.search(doan)
    if not (co_duoi or co_tren):
        return []
    mb = BOLL.search(doan)
    n = int(mb.group(1)) if (mb and mb.group(1)) else 20
    mk = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:standard deviations?|sd|sigma)\b", doan, re.I)
    if not mk:
        mk = re.search(r"bollinger\s*(?:bands?)?\s*\(\s*\d+\s*,\s*(\d+(?:\.\d+)?)\s*\)",
                       doan, re.I)
    k = float(mk.group(1)) if mk else 2.0
    z = {"chi_bao": "zscore", "n": n, "cua": {"chi_bao": "gia", "cot": "close"}}
    if co_duoi:
        return [{"trai": z, "phep": "<", "phai": {"hang": -k}}]
    return [{"trai": z, "phep": ">", "phai": {"hang": k}}]


#: Cau MO TA hai kha nang cung luc thi khong phai mot luat - no la mot cau
#: gioi thieu chi bao. Do that 23/08: "Such a band indicator can be used to
#: trigger long OR short positions when the price crosses the upper OR lower
#: band" da bien thanh mot co che BAN hoan chinh (zscore < -2). Cau do khong
#: noi ai nen lam gi; no ta cai bang.
MO_HO = re.compile(
    r"\blong (?:or|and) short\b|\bshort (?:or|and) long\b|\bbuy (?:or|and) sell\b"
    r"|\bupper (?:or|and) lower\b|\blower (?:or|and) upper\b"
    r"|\beither\b|\bcan be used to\b|\bfor (?:example|illustration)\b"
    # Ngon ngu SACH GIAO KHOA, khong phai luat cua tac gia: "when the RSI falls
    # below 30, it INDICATES that the security is oversold, SUGGESTING a
    # POTENTIAL buying OPPORTUNITY". Cau nay ta cai chi bao, khong ta mot lenh
    # ai do that su dat. Do that 23/08 tren quantifiedstrategies.
    r"|\bsuggest|\bindicat|\bpotential\b|\bopportunit|\btends? to\b"
    r"|\bis considered\b|\bcould be\b|\bwould be\b", re.I)


#: Cau ta CA HAI CHIEU trong cung mot cau. Khac `MO_HO` o cho day khong phai
#: "hoac" ma la "va": "enters LONG when price breaks below the lower band and
#: enters SHORT when price breaks above the upper band". Cau nay dung va day
#: du, va chinh vi the no NGUY HIEM: bo doc lay CHIEU tu menh de sau nhung lay
#: DIEU KIEN tu menh de truoc, ra mot co che nguoc han y tac gia. Da xay ra
#: that 23/08 - `ban_zscore20_close_duoi_am2` bien "mua khi thung day" thanh
#: "ban khi thung day", va no da duoc dang ky truoc khi bi phat hien.
HAI_CHIEU = re.compile(
    r"\blong\b[^.]{0,120}\bshort\b|\bshort\b[^.]{0,120}\blong\b", re.I)

#: Cau DINH NGHIA chi bao, khong phai luat cua ai: no ta ca hai nguong cung
#: luc. "Buy when RSI is oversold (<30), sell when overbought (>70)" la mot muc
#: tu dien viet trong README, va bo doc da rut nham thanh "mua khi RSI > 30".
DINH_NGHIA = re.compile(r"\boversold\b[^.]{0,160}\boverbought\b"
                        r"|\boverbought\b[^.]{0,160}\boversold\b", re.I)


#: Dai tu tro lai mot chi bao da neu O VE TRUOC trong cung cau.
_DAI_TU = re.compile(r"\b(?:it|they|no)\b", re.I)


def _go_dai_tu(cau: str) -> str:
    """Thay dai tu trong menh de dieu kien bang chi bao neu o ve TRUOC.

    "The first example is a 2-day RSI strategy where we buy when **it** crosses
    below 15" — ten va chu ky deu co, nhung `_vung_dieu_kien` cat het phan
    truoc chu "when" nen "2-day RSI" bi vut di va ca cau thanh khong doc duoc.
    Do tren kho ngay 30/08/2026: day la mot trong hai hinh dang luat THAT ma
    bo doc con mu.

    Chi thay khi vung dieu kien KHONG tu co ten chi bao nao — con neu no da co
    thi dai tu dang tro thu khac, va doan bua se sinh ra mot luat khong ai
    phat bieu.
    """
    m = re.search(r"\b" + NEU + r"\b", cau, re.I)
    if not m:
        return cau
    truoc, vung = cau[:m.end()], cau[m.end():]
    dt = _DAI_TU.search(vung)
    if not dt:
        return cau
    for rx, _f, la_gia in _TOAN_HANG_RE:
        if not la_gia and rx.search(vung):
            return cau                     # vung da co chi bao rieng
    tot = None
    for rx, _f, la_gia in _TOAN_HANG_RE:
        if la_gia:
            continue                       # "gia" khong phai tien to dang tro
        for mm in rx.finditer(truoc):
            # Xep theo (ket thuc, do dai): cum GAN dai tu nhat, va khi hai cum
            # ket thuc cung cho thi lay cum DAI hon. Neu xep theo vi tri BAT
            # DAU thi "RSI" tran thang "2-day RSI" (no bat dau muon hon) va
            # chu ky bi mat -> ghi n=14 cho mot bai noi RSI(2). Hai cai do la
            # hai co che khac han: RSI(2)<15 la edge Connors, RSI(14)<15 gan
            # nhu khong bao gio kich hoat.
            if tot is None or (mm.end(), mm.end() - mm.start()) > (
                    tot.end(), tot.end() - tot.start()):
                tot = mm
    if tot is None:
        return cau
    return truoc + vung[:dt.start()] + tot.group(0) + vung[dt.end():]


def dieu_kien_trong_cau(cau: str, thay_the: dict | None = None):
    """Cau -> danh sach dieu kien DSL (VA voi nhau). Tra (dieu_kien, ly_do_bo).

    `thay_the`: toan hang de thay cho cum TRO LAI ("the average") - xem
    `TRO_LAI`. Chi truyen khi doc ve RA cua chinh cau da doc ve VAO.
    """
    cau = _go_dai_tu(cau)
    if MO_HO.search(cau):
        return [], "cau mo ta hai kha nang cung luc - khong xac dinh duoc chieu"
    if DINH_NGHIA.search(cau):
        return [], "cau dinh nghia chi bao (ca oversold lan overbought)"
    if HAI_CHIEU.search(cau):
        return [], "cau ta ca chieu mua lan chieu ban - de lay nham chieu"
    vung = _vung_dieu_kien(cau)
    if re.search(r"\bor\b|\bhoac\b", vung, re.I) and len(re.findall(
            r"\b(?:above|below|under|over|greater|less|cross)\b", vung, re.I)) > 1:
        # Ngu phap chi co VA. Doc mot cau OR thanh VA la doc SAI, khong phai
        # doc thieu - tu choi ca cau.
        return [], "cau co 'or' giua hai so sanh - ngu phap chi co VA"

    dk = _bollinger(vung)
    if dk:
        return dk, ""

    ra: list[dict] = []
    for menh in re.split(r"\band\b|,|;|\bva\b", vung, flags=re.I):
        menh = menh.strip()
        if len(menh) < 3:
            continue
        vt = None
        for bt, phep in _SO_SANH_RE:
            m = bt.search(menh)
            if m and (vt is None or m.start() < vt[0]):
                vt = (m.start(), m.end(), phep)
        if vt is None:
            continue
        trai_doan, phai_doan = menh[:vt[0]], menh[vt[1]:]
        trai = _quet_toan_hang(trai_doan, uu_tien_chi_bao=True)
        if trai is None:
            continue
        phai = _ben_phai(phai_doan, trai[0], thay_the)
        if phai is None:
            continue
        ra.append({"trai": {k: v for k, v in trai[0].items() if not k.startswith("_")},
                   "phep": vt[2],
                   "phai": {k: v for k, v in phai.items() if not k.startswith("_")}})
        if len(ra) >= 4:
            break
    if not ra:
        return [], "khong tach duoc cap (toan hang, so sanh, nguong)"
    return ra, ""


#: Cho NOI cau vao va cau ra khi ca hai nam trong CUNG MOT CAU. Day la cach
#: viet pho bien nhat cua tieng Anh tai chinh: "go long ... when X and to exit
#: ... when Y". Neu khong tach, ve RA bi mat trang va co che thanh "giu 1 bar"
#: - sai han y tac gia. Do that 23/08: bai priceactionlab ta ca vao lan ra
#: trong mot cau, va he chi doc duoc ve vao.
_NOI_RA = re.compile(
    r"[,;]?\s*\b(?:and|then)\s+(?:we\s+)?(?:to\s+)?"
    r"(exit|sell|close (?:the )?(?:position|trade)|cover)\b", re.I)


def tach_vao_ra(cau: str):
    """Mot cau -> (phan VAO, phan RA hoac None).

    Chi tach khi phan duoi CO tu dieu kien rieng cua no; neu khong, "and exit
    the trade" chi la mot menh de ke tiep chu khong phai mot luat ra.
    """
    m = _NOI_RA.search(cau)
    if not m:
        return cau, None
    duoi = cau[m.start():]
    if not re.search(r"\b" + NEU + r"\b", duoi, re.I):
        return cau, None
    return cau[:m.start()], duoi


def _la_gia_tho(t: dict) -> bool:
    """Toan hang la MUC GIA THO (khong chuan hoa) hay khong."""
    if t.get("chi_bao") == "gia":
        return True
    if t.get("chi_bao") in ("tre", "cao_nhat", "thap_nhat", "tb") \
            and isinstance(t.get("cua"), dict):
        return _la_gia_tho(t["cua"])
    return False


def loc_dieu_kien(dk: list[dict]) -> tuple[list[dict], list[str]]:
    """Bo cac dieu kien DUNG CU PHAP nhung VO NGHIA. Tra (con_lai, ly_do_bo).

    Hai dang bi bo, ca hai deu tung lam ban trong cac bo khop truoc day:

    1. **Muc gia tho so voi mot hang so**: "buy when the price is above 100".
       Cau nay dung ngu phap nhung khong CHUYEN duoc sang tai san khac va cung
       khong chuyen duoc sang thoi ky khac cua chinh tai san do - 100 la muc
       gia cua mot ma tai mot nam. No se hoac dung 100% so bar hoac 0%.
    2. **Hai ve giong het nhau**: "close above the close" - san pham cua mot
       cau bi cat sai, khong phai mot luat.
    """
    giu, bo = [], []
    for d in dk:
        trai, phai = d.get("trai") or {}, d.get("phai") or {}
        if _la_gia_tho(trai) and "hang" in phai:
            bo.append("muc gia tho so voi hang so (%g) - khong chuyen duoc sang "
                      "tai san/thoi ky khac" % phai["hang"])
            continue
        if json.dumps(_chuan_hoa_th(trai), sort_keys=True) == \
                json.dumps(_chuan_hoa_th(phai), sort_keys=True):
            bo.append("hai ve giong het nhau")
            continue
        giu.append(d)
    return giu, bo


#: Dau hieu VAN BAN LA MA NGUON chu khong phai van xuoi. Ma nguon co duong
#: doc rieng (`nhan/ma_nguon.py` + `bien_dich_ung_vien` che do ma_nguon) va
#: KHONG duoc di qua day: mot dong `if (x < 30)` bat ky trong mot thu vien bat
#: ky se thanh mot "co che" hoan chinh ma khong ai co y ta mot chien luoc nao.
_DAU_MA = re.compile(r"[;{}]|\bdef \b|\bself\.|\bimport \b|//|==|\breturn\b|=>")


def la_ma_nguon(vb: str, nguong: float = 12.0) -> bool:
    """Mat do dau hieu ma tren 1000 ky tu vuot nguong -> day la ma nguon."""
    if not vb:
        return False
    return len(_DAU_MA.findall(vb)) * 1000.0 / max(len(vb), 1) > nguong


def so_bar_giu(vb: str):
    for bt in (GIU_RE, GIU_RE2, GIU_RE3):
        m = bt.search(vb)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 500:
                return n
    return None


# --------------------------------------------------------------------- HO
_HO_THEO_CHI_BAO = {
    "rsi": "quay_ve_trung_binh", "ibs": "quay_ve_trung_binh",
    "zscore": "quay_ve_trung_binh", "stoch": "quay_ve_trung_binh",
    "atr": "bien_dong",
    "sma": "xu_huong", "ema": "xu_huong",
    "cao_nhat": "pha_vo", "thap_nhat": "pha_vo",
    "gio": "phien", "ngay_trong_thang": "lich", "thang": "lich",
    "ngay_trong_tuan": "lich",
}


def _chi_bao_trong(t: dict) -> list[str]:
    ra = [str(t.get("chi_bao"))] if t.get("chi_bao") else []
    if isinstance(t.get("cua"), dict):
        ra += _chi_bao_trong(t["cua"])
    for x in (t.get("toan_hang") or []):
        if isinstance(x, dict):
            ra += _chi_bao_trong(x)
    return ra


# Chi bao DAO DONG: cung mot chi bao, hai CHIEU la hai co che nguoc nhau.
#   RSI < 30 -> mua  = bat day          -> quay_ve_trung_binh
#   RSI > 70 -> mua  = mua theo da manh -> xu_huong
# Suy ho chi tu TEN chi bao la xep nham mot nua so luat, va ho quyet dinh nhom
# doi chung o phep thu phan chung -> phan quyet thanh vo nghia.
_DAO_DONG = {"rsi", "ibs", "zscore", "stoch"}
# Phep CAT cung mang chieu: "RSI cheo xuong 15" la di vao vung thap.
# Bo sot chung thi luat Connors RSI(2) cheo xuong 15 bi xep ho "khac".
_NHO_HON = {"<", "<=", "duoi", "nho_hon", "cheo_xuong"}
_LON_HON = {">", ">=", "tren", "lon_hon", "cheo_len"}


def _phia_nguong(dk: list[dict], ten: str) -> int | None:
    """Luat bat chi bao o phia THAP (-1) hay phia CAO (+1) cua thang do?

    Tra `None` khi khong doc duoc phia (vd. so sanh hai chi bao voi nhau) —
    khong duoc doan, vi doan sai o day la xep nham ho.
    """
    for d in dk:
        trai, phai = d.get("trai") or {}, d.get("phai") or {}
        phep = str(d.get("phep") or "")
        co_trai = ten in _chi_bao_trong(trai)
        co_phai = ten in _chi_bao_trong(phai)
        if co_trai == co_phai:                 # ca hai ve, hoac khong ve nao
            continue
        # nguong phai la mot HANG SO; chi_bao so voi chi_bao thi khong co "phia"
        kia = phai if co_trai else trai
        if not isinstance(kia, dict) or "hang" not in kia:
            continue
        if phep in _NHO_HON:
            return -1 if co_trai else +1
        if phep in _LON_HON:
            return +1 if co_trai else -1
    return None


def suy_ho(dk: list[dict], chieu: int = 1) -> str:
    cb = []
    for d in dk:
        cb += _chi_bao_trong(d.get("trai") or {}) + _chi_bao_trong(d.get("phai") or {})
    for ten in ("rsi", "ibs", "zscore", "stoch", "cao_nhat", "thap_nhat", "gio",
                "ngay_trong_thang", "sma", "ema", "atr"):
        if ten not in cb:
            continue
        if ten in _DAO_DONG:
            phia = _phia_nguong(dk, ten)
            if phia is None:
                return "khac"              # khong doc duoc phia -> khong xep bua
            # bat NGUOC phia cua vi the = quay ve trung binh
            return ("quay_ve_trung_binh" if phia * int(chieu or 1) < 0
                    else "xu_huong")
        return _HO_THEO_CHI_BAO[ten]
    return "khac"


# ------------------------------------------------------------------- DAT TEN
def _ten_toan_hang(t: dict) -> str:
    if "hang" in t:
        return ("%g" % t["hang"]).replace(".", "p").replace("-", "am")
    cb = str(t.get("chi_bao") or "")
    if cb == "gia":
        return str(t.get("cot", "close"))
    if isinstance(t.get("cua"), dict):
        return f"{cb}{t.get('n', '')}_{_ten_toan_hang(t['cua'])}"
    return f"{cb}{t.get('n', '')}" if t.get("n") else (cb or "th")


_TEN_PHEP = {"<": "duoi", "<=": "duoi", ">": "tren", ">=": "tren",
             "cheo_len": "cheo_len", "cheo_xuong": "cheo_xuong"}


def dat_ten(dk: list[dict], chieu: int) -> str:
    phan = ["mua" if chieu > 0 else "ban"]
    for d in dk[:3]:
        phan.append(f"{_ten_toan_hang(d['trai'])}_{_TEN_PHEP[d['phep']]}_"
                    f"{_ten_toan_hang(d['phai'])}")
    return NP.chuan_hoa_ten("_".join(phan))


# --------------------------------------------------------------- VAN TAY
def _chuan_hoa_th(t: dict) -> dict:
    ra = {}
    for k in sorted(t):
        if k.startswith("_"):
            continue
        v = t[k]
        if isinstance(v, dict):
            ra[k] = _chuan_hoa_th(v)
        elif isinstance(v, float) and float(v).is_integer():
            ra[k] = int(v)
        else:
            ra[k] = v
    return ra


def van_tay_spec(spec: dict) -> str:
    """Bam theo CAU TRUC, khong theo ten. Hai bai viet ta cung mot luat cho
    cung mot van tay -> gop lam bang chung, khong an them suat FDR."""
    loi = {
        "chieu": int(spec.get("chieu", 1) or 1),
        "giu": int(spec.get("giu", 1) or 1),
        "vao": sorted([json.dumps(_chuan_hoa_th(d), sort_keys=True)
                       for d in (spec.get("vao") or [])]),
        "ra": sorted([json.dumps(_chuan_hoa_th(d), sort_keys=True)
                      for d in (spec.get("ra") or [])]),
    }
    return hashlib.sha256(json.dumps(loi, sort_keys=True).encode()).hexdigest()[:16]


# ------------------------------------------------------------------ DOC MOT BAI
#: Mot tai lieu duoc de xuat toi da bay nhieu co che. Bai liet ke "20 chien
#: luoc RSI" khong phai 20 y tuong, no la mot bai tong hop.
TRAN_MOI_TAI_LIEU = 3
#: Cua so ky tu: cau RA phai nam gan cau VAO thi moi la cung mot chien luoc.
GAN_NHAU = 1500


def doc_bai(van_ban: str, tieu_de: str = "", nguon: str = "") -> list[dict]:
    """Van xuoi -> danh sach {spec, bang_chung, ...}. KHONG cham du lieu gia.

    Chi tra ve nhung gi CU PHAP dung duoc. Viec quyet dinh co nhan hay khong
    la cua `nhan/ngu_phap.them_co_che` (ty le kich hoat + phep cat nhin truoc)
    va cuoi cung la cua QUANTLAB.
    """
    vb = _chuan(van_ban)
    if len(vb) < 120 or la_ma_nguon(vb):
        return []
    vao_ds, ra_ds = [], []
    for vt, c in cac_cau(vb):
        if len(c) > 700:
            continue                       # doan dai = doan liet ke, khong phai luat
        phan_vao, phan_ra = tach_vao_ra(c)
        # Phan LOAI tren phan VAO, khong tren ca cau. Cau "We open a long
        # position when ... , and close the position (or open a short position)
        # when ..." co chu "short" o ve RA; phan loai ca cau thi mot chien luoc
        # MUA bi doc thanh chien luoc BAN. Da xay ra that 23/08.
        lo = loai_cau(phan_vao)
        if lo is None:
            continue
        dk, _ly = dieu_kien_trong_cau(phan_vao)
        dk, _bo = loc_dieu_kien(dk)
        if not dk:
            continue
        (ra_ds if lo == "ra" else vao_ds).append(
            {"vi_tri": vt, "cau": phan_vao, "dk": dk,
             "chieu": -1 if lo == "vao_ban" else 1})
        if phan_ra and lo != "ra":
            neo = next((d["phai"] for d in reversed(dk)
                        if d.get("phai", {}).get("chi_bao")), None)
            dk_ra, _ = dieu_kien_trong_cau(phan_ra, thay_the=neo)
            dk_ra, _ = loc_dieu_kien(dk_ra)
            if dk_ra:
                # +1 de cau RA nam SAU cau VAO khi ghep cap ben duoi
                ra_ds.append({"vi_tri": vt + 1, "cau": phan_ra, "dk": dk_ra,
                              "chieu": 1})

    ket: list[dict] = []
    thay: set = set()
    for v in vao_ds:
        if len(ket) >= TRAN_MOI_TAI_LIEU:
            break
        # cau RA gan nhat SAU cau VAO, trong cung mot vung van ban
        r = next((x for x in ra_ds if 0 < x["vi_tri"] - v["vi_tri"] < GAN_NHAU), None)
        giu = so_bar_giu(vb[v["vi_tri"]: v["vi_tri"] + GAN_NHAU]) or 1
        spec = {
            "ten": dat_ten(v["dk"], v["chieu"]),
            "ho": suy_ho(v["dk"], v["chieu"]),
            "chieu": v["chieu"],
            "giu": giu,
            "vao": v["dk"],
            "ra": r["dk"] if r else [],
        }
        vt = van_tay_spec(spec)
        if vt in thay:
            continue
        thay.add(vt)
        trich = " ".join(v["cau"].split())[:400]
        trich_ra = " ".join(r["cau"].split())[:300] if r else ""
        # `co_che` la mot CAU bat buoc. KHONG bia mot cau kinh te - dan nguyen
        # van cau luat cua tai lieu, kem dia chi. Man hinh duyet doc cau nay va
        # phai thay ngay day la LOI KE LAI, chua phai mot lap luan.
        spec["co_che"] = (
            "Luat doc duoc tu tai lieu, CHUA co lap luan kinh te: \"%s\" [nguon: %s]"
            % (trich[:220], (nguon or tieu_de or "khong ro")[:80]))
        ket.append({
            "spec": spec,
            "van_tay": vt,
            "bang_chung": [{"quote": trich, "locator": "char %d" % v["vi_tri"],
                            "note": "cau VAO"}]
                          + ([{"quote": trich_ra, "locator": "char %d" % r["vi_tri"],
                               "note": "cau RA"}] if r else []),
            "tieu_de": tieu_de,
            "nguon": nguon,
            "giu_doc_duoc": giu > 1,
        })
    return ket


def cum_chua_hieu(van_ban: str, toi_da: int = 40) -> list[dict]:
    """Cac cum tu DUNG O VI TRI TOAN HANG ma ngu phap chua co.

    He phai tu noi ra thu no thieu, neu khong thi "0 co che" doc nhu "tai lieu
    khong co gi" trong khi that ra la "ta chua co chi bao do". Danh sach nay la
    danh sach viec cho `nhan/ngu_phap.py`, sinh tu du lieu chu khong tu phong
    doan: chi tinh nhung cau DA co hanh dong, DA co phep so sanh va DA co mot
    con so - tuc da chac chan la mot cau luat - ma ve trai khong doc duoc.
    """
    vb = _chuan(van_ban)
    if len(vb) < 120 or la_ma_nguon(vb):
        return []
    ra = []
    for _vt, cau in cac_cau(vb):
        if len(cau) > 700 or loai_cau(cau) is None:
            continue
        vung = _vung_dieu_kien(tach_vao_ra(cau)[0])
        for menh in re.split(r"\band\b|,|;", vung, flags=re.I):
            m = None
            for bt, _phep in _SO_SANH_RE:
                k = bt.search(menh)
                if k and (m is None or k.start() < m.start()):
                    m = k
            if m is None or not re.search(_SO, menh[m.end():]):
                continue
            if _quet_toan_hang(menh[:m.start()], uu_tien_chi_bao=True) is not None:
                continue
            cum = " ".join(menh[:m.start()].split()[-4:]).strip(" .,:;()")
            if len(cum) > 2:
                ra.append({"cum": cum.lower(), "cau": " ".join(cau.split())[:200]})
            if len(ra) >= toi_da:
                return ra
    return ra


if __name__ == "__main__":
    thu = ("The strategy is simple. Buy when the 2-period RSI closes below 10 "
           "and the close is above the 200-day moving average. "
           "Sell when the close crosses above the 5-day moving average. "
           "We hold for 5 days at most. Backtested on SPY since 1993.")
    for r in doc_bai(thu, "thu", "vi_du"):
        print(json.dumps(r["spec"], ensure_ascii=False, indent=1))
