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

    # --- chi bao NGU PHAP DA CO ma bang nay chua bao gio sinh ra (them 11/09) ---
    #
    # Do 11/09 bang `_corpus_ngu_phap.py`: 12/43 toan hang chua duoc dung MOT
    # LAN NAO trong 689 co che cua kho - bollinger, cci, dem_lien_tiep,
    # dong_luong, gann_sq9, obv, phuong_sai, smma, tong, trang_thai_lat,
    # tuong_quan, wma. Doi chieu thi CA 12 deu vang mat khoi bang nay.
    #
    # Tuc khong phai he "khong thich" chung, cung khong phai thi truong khong
    # co: khong co gi NOI RA chung. Ngu phap noi duoc mot dai rong hon hai lan
    # cai ma bo doc biet hoi. Day la cung ho loi voi `ma_nguon.thu_thap khong
    # phan trang` va `closure DSL nuot tham so` - bo phan im lang khong lam
    # viec, doc y het "khong co gi o do".
    #
    # `tuong_quan`, `trang_thai_lat`, `dem_lien_tiep` KHONG them o day: chung
    # nhan mot DANH SACH toan hang hoac mot dieu kien con, khong doc duoc bang
    # mot mau ve trai. Chung can duong doc rieng - ghi vao hang doi, dung im.
    (r"\bmacd\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
     lambda m: {"chi_bao": "macd", "nhanh": int(m.group(1)),
                "cham": int(m.group(2)), "tin_hieu": int(m.group(3))}, False),
    (r"\bmacd\s+histogram\b",
     lambda m: {"chi_bao": "macd", "lay": "hieu", "_mac_dinh": "chu_ky"}, False),
    (r"\bmacd\s+signal(?:\s+line)?\b",
     lambda m: {"chi_bao": "macd", "lay": "tin_hieu", "_mac_dinh": "chu_ky"}, False),
    (r"\bmacd(?:\s+line)?\b",
     lambda m: {"chi_bao": "macd", "_mac_dinh": "chu_ky"}, False),

    (r"\b(\d+)[-\s](?:period|day|bar|week)s?\s+adx\b",
     lambda m: {"chi_bao": "adx", "n": int(m.group(1))}, False),
    (r"\badx\s*\(\s*(\d+)\s*\)",
     lambda m: {"chi_bao": "adx", "n": int(m.group(1))}, False),
    (r"\b(?:adx|average directional (?:index|movement index))\b",
     lambda m: {"chi_bao": "adx", "n": 14, "_mac_dinh": "n"}, False),

    (r"\b(\d+)[-\s](?:period|day|bar|week)s?\s+cci\b",
     lambda m: {"chi_bao": "cci", "n": int(m.group(1))}, False),
    (r"\bcci\s*\(\s*(\d+)\s*\)",
     lambda m: {"chi_bao": "cci", "n": int(m.group(1))}, False),
    (r"\b(?:cci|commodity channel index)\b",
     lambda m: {"chi_bao": "cci", "n": 20, "_mac_dinh": "n"}, False),

    # "the highest high OF THE LAST 20 bars" - cung y nghia voi "20-bar high" o
    # tren nhung dao thu tu chu ky va ten. Do 11/09: day la cach viet cua cau
    # pha vo pho bien nhat ("buys when price exceeds the highest high of the
    # last n bars"), va mau "20-bar high" khong bat duoc no.
    (r"\b(?:highest high|high(?:est)?)\s+(?:price\s+)?of\s+the\s+"
     r"(?:last|past|previous|prior)\s+(\d+)\s*(?:bar|day|period|week)s?\b",
     lambda m: {"chi_bao": "cao_nhat", "n": int(m.group(1)),
                "cua": {"chi_bao": "tre", "n": 1,
                        "cua": {"chi_bao": "gia", "cot": "high"}}}, False),
    (r"\b(?:lowest low|low(?:est)?)\s+(?:price\s+)?of\s+the\s+"
     r"(?:last|past|previous|prior)\s+(\d+)\s*(?:bar|day|period|week)s?\b",
     lambda m: {"chi_bao": "thap_nhat", "n": int(m.group(1)),
                "cua": {"chi_bao": "tre", "n": 1,
                        "cua": {"chi_bao": "gia", "cot": "low"}}}, False),

    (r"\b(\d+)[-\s](?:period|day|bar)s?\s+stochastics?\b",
     lambda m: {"chi_bao": "stochastic", "n": int(m.group(1))}, False),
    (r"\bstoch(?:astic)?\s*\(\s*(\d+)\s*(?:,[^)]*)?\)",
     lambda m: {"chi_bao": "stochastic", "n": int(m.group(1))}, False),
    # %D la trung binh 3 phien cua %K - ngu phap noi duoc bang `tb` co `cua`.
    # Khong co muc nay thi cau pho bien nhat cua ho stochastic ("a bullish
    # crossover occurs when %K rises above %D") rot ngay o ve PHAI.
    (r"%\s?d\b",
     lambda m: {"chi_bao": "tb", "n": 3,
                "cua": {"chi_bao": "stochastic", "n": 14, "_mac_dinh": "n"}}, False),
    # `%k` phai la mau RIENG: `\b` truoc `%` khong bao gio khop, vi `%` la ky tu
    # khong-phai-chu nen khong co ranh gioi tu o do. Viet chung voi `stochastic`
    # trong mot nhom `\b(?:...)` la tat lang le nhanh `%k`.
    (r"%\s?k\b", lambda m: {"chi_bao": "stochastic", "n": 14, "_mac_dinh": "n"}, False),
    (r"\b(?:stochastics?|stochastic oscillator)\b",
     lambda m: {"chi_bao": "stochastic", "n": 14, "_mac_dinh": "n"}, False),

    (r"\b(?:obv|on[- ]balance volume)\b", lambda m: {"chi_bao": "obv"}, False),

    (r"\b(\d+)[-\s](?:period|day|bar|week)s?\s+weighted\s+(?:moving average|ma|wma)\b",
     lambda m: _tb(m.group(1), "wma"), False),
    (r"\bwma\s*\(\s*(\d+)\s*\)", lambda m: _tb(m.group(1), "wma"), False),
    (r"\b(?:smma|rma)\s*\(\s*(\d+)\s*\)", lambda m: _tb(m.group(1), "smma"), False),
    (r"\b(\d+)[-\s](?:period|day|bar)s?\s+(?:smma|rma"
     r"|wilder'?s?\s+(?:smooth(?:ed|ing)?|moving average))\b",
     lambda m: _tb(m.group(1), "smma"), False),

    (r"\b(\d+)[-\s](?:period|day|bar|week)s?\s+momentum\b",
     lambda m: {"chi_bao": "dong_luong", "n": int(m.group(1))}, False),
    (r"\bmom(?:entum)?\s*\(\s*(\d+)\s*\)",
     lambda m: {"chi_bao": "dong_luong", "n": int(m.group(1))}, False),

    (r"\b(\d+)[-\s](?:period|day|bar)s?\s+variance\b",
     lambda m: {"chi_bao": "phuong_sai", "n": int(m.group(1))}, False),
    (r"\b(\d+)[-\s](?:period|day|bar)s?\s+percentile\b",
     lambda m: {"chi_bao": "phan_vi", "n": int(m.group(1))}, False),

    # Khong dat `\brange\b` tran: "a range of strategies" khong phai bien do.
    (r"\b(?:daily|bar|candle|intraday|true)\s+range\b",
     lambda m: {"chi_bao": "bien_do"}, False),
    (r"\b(?:candle|candlestick|bar)\s+body\b",
     lambda m: {"chi_bao": "than_nen"}, False),
    (r"\b(?:trading |tick )?volume\b", lambda m: {"chi_bao": "khoi_luong"}, False),

    (r"\bday of (?:the )?week\b", lambda m: {"chi_bao": "ngay_trong_tuan"}, False),
    (r"\b(?:calendar month|month of (?:the )?year)\b",
     lambda m: {"chi_bao": "thang"}, False),
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
    # GIAI MA CHUOI THOAT `\uXXXX` TRUOC KHI BO THE HTML. Do 11/09: 1.679/4.198
    # ban van xuoi (40,0%) chua `<` thay vi `<` - chung di qua API tra JSON
    # roi duoc luu nguyen van. Bo the HTML chay SAU se khong nhan ra chung, nen
    # ca doan `</p>\n<p dir=\"auto\">` o lai trong cau va
    # bo tach menh de doc no thanh van. Phai lam truoc, khong lam sau.
    if vb and "\\u00" in vb:
        vb = re.sub(r"\\u([0-9a-fA-F]{4})",
                    lambda m: chr(int(m.group(1), 16)), vb)
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
    r"\b(?:buy|sell)(?:[ -]?(?:side|back|er|ers|out|in)\b|s\b(?=[ ]side))"
    r"|\bbuy and sell\b|\bbuyers?\b|\bsellers?\b", re.I)


def loai_cau(cau: str, chat: bool = True) -> str | None:
    """'vao_mua' | 'vao_ban' | 'ra' | None.

    Thu tu kiem la co y: BAN truoc RA vi "sell short" chua chu "sell"; VAO
    truoc RA vi "buy" khong duoc doc thanh "dong vi the".

    `chat=True` (mac dinh, cho duong BOC) doi them: cau phai co it nhat MOT
    toan hang doc duoc. `chat=False` (cho `cum_chua_hieu`) bo dieu do - vi
    hang doi tu vung TON TAI de tim dung nhung cau co toan hang CHUA doc duoc,
    siet chung o day thi lam mu chinh cai la khoa mo cho buoc sau.
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
    #
    # SIET 11/09: truoc day chi can CO tu dieu kien ("if"/"when") LA DU. Do duoc
    # tren 150 cau corpus: ca 150 cau `loai_cau` nhan la luat deu ra 0 dieu kien,
    # va ly do `dieu_kien_trong_cau` tra ve la "khong tach duoc cap". Nhin vao
    # cau thi ro - chung la van ke chuyen co chu "if":
    #     "So if you are still bullish, how about buying a stock at an oversold
    #      (rsi) or at a support level"
    #     "And if it's a bearish price movement, you go for a sell"
    # Do phu cao, do chinh xac gan bang 0. Mot bo phan loai nhu vay lam hai viec
    # cung luc: nhoi hang doi boc bang rac, va thoi phong con so "cau dang luat"
    # nen cho hong that su bi che.
    #
    # Mot LUAT phai co du ba thanh phan: hanh dong · phep so sanh · NGUONG.
    # Thieu nguong thi khong co gi de kiem dinh - "buy when RSI is oversold"
    # khong dich duoc thanh mot phep thu, du no la mot cau tieng Anh dung.
    # Day cung la nguong `cum_chua_hieu` vao dung dung (no doi `_SO` sau phep
    # so sanh), nen hai ham gio noi cung mot thu.
    m_ss = None
    for bt, _phep in _SO_SANH_RE:
        k = bt.search(sach)
        if k and (m_ss is None or k.start() < m_ss.start()):
            m_ss = k
    if m_ss is None:
        return None
    # NGUONG la mot CON SO hoac mot TOAN HANG KHAC. Doi con so khong thoi la
    # sai: "the close falls below the lower Bollinger band" la mot luat day du
    # va khong co chu so nao - phep siet dau tien cua toi 11/09 da loai no, va
    # bai test `test_dai_bollinger_thanh_zscore` bat duoc ngay.
    # Dai Bollinger KHONG nam trong `_TOAN_HANG` - no co duong doc rieng
    # (`_bollinger`). Quen no o day thi cau Bollinger bi loai ngay tu cua.
    phai = sach[m_ss.end():]
    if (not re.search(_SO, phai)
            and _quet_toan_hang(phai, uu_tien_chi_bao=False) is None
            and not (BOLL.search(phai) or BOLL_DUOI.search(phai)
                     or BOLL_TREN.search(phai))):
        return None
    # Phai co it nhat MOT toan hang doc duoc trong cau. Khong co chot nay thi
    # van hoc thuat ("if φn → φ in L2F, then, up to a subsequence"), danh sach
    # tinh nang ("Has multiple overlapping exit systems: fixed SL/TP, ...") va
    # tro chuyen Reddit ("So if selling into the panic is key, when do you
    # sell") deu lot vao, vi chung co du mot tu so sanh va mot con so o dau do.
    # Do 11/09: chung la phan lon cua 108 cau "khong tach duoc cap".
    if chat and _quet_toan_hang(sach, uu_tien_chi_bao=True) is None \
            and not (BOLL.search(sach) or BOLL_DUOI.search(sach)
                     or BOLL_TREN.search(sach)):
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


#: Doan ve TRAI cua mot menh de da LUOC CHU NGU. Chi nhung tu noi/dai tu rong
#: moi duoc phep o day.
#:
#: Chot dau tien cua toi 11/09 la "doan trai ngan hon 25 ky tu" - va no SAI ngay
#: tren vi du dau tien co that: "RSI(14) is below 30 and the Ichimoku cloud is
#: above 55" co doan trai "the Ichimoku cloud " (19 ky tu) nen duoc thua ke, va
#: bo doc sinh ra `rsi > 55`. Tuc no ghi vao he MOT CO CHE KHAC HAN dieu tac gia
#: viet, khong mot loi canh bao. Do dai khong phan biet duoc "luoc chu ngu" voi
#: "chu ngu la mot thu ta chua doc duoc" - chi TU VUNG moi phan biet duoc.
#:
#: Ve trai khong doc duoc ma khong rong thi phai vao `bo_sot`, khong duoc thua ke.
_LUOC_CHU_NGU = re.compile(
    r"[\s,]*(?:(?:and|then|also|it|they|which|that|subsequently|later|again"
    r"|conversely|otherwise|va|roi|sau do)\b[\s,]*)*", re.I)


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

    # `bo_sot` GIU LAI cac menh de CO phep so sanh ma khong doc ra dieu kien.
    #
    # Truoc 11/09 ham nay chi tra ve mot LY DO khi ra tay trang, va khong noi gi
    # khi no doc duoc mot nua. Do la mat mat im lang: cau
    #     "buy when RSI(14) < 30 and the close is above the 200-day MA"
    # ra dung `rsi < 30`, ve MA bi bo, khong mot dong nhac - va co che dang ky
    # vao he la mot co che KHAC voi y tac gia. Khong do duoc thi khong sua duoc:
    # `_corpus_ngu_phap.py` khong bao gio dem duoc trang thai NOI_MOT_PHAN.
    ra: list[dict] = []
    bo_sot: list[str] = []
    menh_truoc = ""
    for menh in re.split(r"\band\b|,|;|\bva\b", vung, flags=re.I):
        menh = menh.strip()
        if len(menh) < 3:
            continue
        truoc, menh_truoc = menh_truoc, menh
        vt = None
        for bt, phep in _SO_SANH_RE:
            m = bt.search(menh)
            if m and (vt is None or m.start() < vt[0]):
                vt = (m.start(), m.end(), phep)
        if vt is None:
            continue
        trai_doan, phai_doan = menh[:vt[0]], menh[vt[1]:]
        trai = _quet_toan_hang(trai_doan, uu_tien_chi_bao=True)
        if trai is None and truoc and _LUOC_CHU_NGU.fullmatch(trai_doan):
            # Menh de truoc co the KHONG phai mot dieu kien ma chi la nua dau
            # cua cung mot menh de: "if the price rises and exceeds the previous
            # High" - "the price rises" khong co phep so sanh nen khong sinh
            # dieu kien nao, nhung chu ngu nam o do. Quet VAN BAN cua no.
            trai = _quet_toan_hang(truoc, uu_tien_chi_bao=True)
        if trai is None and ra and _LUOC_CHU_NGU.fullmatch(trai_doan):
            # CHUNG CHU NGU. Tieng Anh tai chinh hay luoc chu ngu o menh de sau:
            #   "if the price rises and exceeds the previous High"
            #   "price breaks above the 50 MA and below the 200 MA"
            # Cat o chu "and" roi doi menh de sau tu co chu ngu rieng la doc
            # SAI van pham - ve trai cua no da duoc noi o menh de truoc.
            # Chi thua ke khi doan trai NGAN (<=25 ky tu): du de om "and then",
            # "and also", nhung khong du de om mot chu ngu khac han nhu
            # "Given ORCL's known sustained downtrend" - thua ke nham vao do se
            # gan dieu kien cho sai thuc the.
            trai = (dict(ra[-1]["trai"]), "<thua ke>", 0)
        if trai is None:
            bo_sot.append(menh)
            continue
        phai = _ben_phai(phai_doan, trai[0], thay_the)
        if phai is None:
            bo_sot.append(menh)
            continue
        ra.append({"trai": {k: v for k, v in trai[0].items() if not k.startswith("_")},
                   "phep": vt[2],
                   "phai": {k: v for k, v in phai.items() if not k.startswith("_")}})
        if len(ra) >= 4:
            break
    if not ra:
        return [], "khong tach duoc cap (toan hang, so sanh, nguong)"
    if bo_sot:
        # Dang `bo_sot: ...` de goi BIET day la van ban chua doc duoc, khac han
        # cac ly do o tren (chung la cau bi TU CHOI ca cau).
        return ra, "bo_sot: " + " | ".join(m[:120] for m in bo_sot[:3])
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
#: Chi bao -> HO. Moi chi bao bo doc co the sinh ra PHAI co mat o day.
#:
#: Do 11/09/2026 sau khi them 15 toan hang vao bo doc: ly do TU CHOI lon nhat cua
#: `them_co_che` la `ho 'khac' khong thuoc [...]` - **29 tren 58 lan tu choi**, va
#: trong 19 co che moi duoc nhan KHONG co lay mot cci/adx/macd nao. Doi chieu thi
#: bang nay chi biet 11 chi bao, khong co MOT cai nao trong 15 cai vua them.
#:
#: Tuc ban va bo doc bi HUY LANG LE o tang duoi: doc ra duoc, roi bi vut vi khong
#: xep duoc ho. Cung ho loi voi "bo doc khong sinh ra toan hang ngu phap da co" -
#: mot mat xich im lang lam vo hieu mat xich truoc no. Sua mot cho thi phai di
#: het duong.
#:
#: `stochastic` la ten bo doc THAT SU sinh ra; `stoch` la ten cu. Giu ca hai.
_HO_THEO_CHI_BAO = {
    "rsi": "quay_ve_trung_binh", "ibs": "quay_ve_trung_binh",
    "zscore": "quay_ve_trung_binh", "stoch": "quay_ve_trung_binh",
    "stochastic": "quay_ve_trung_binh", "cci": "quay_ve_trung_binh",
    "phan_vi": "quay_ve_trung_binh",
    "atr": "bien_dong", "phuong_sai": "bien_dong", "do_lech": "bien_dong",
    "bien_do": "bien_dong", "than_nen": "bien_dong",
    "sma": "xu_huong", "ema": "xu_huong", "wma": "xu_huong", "smma": "xu_huong",
    "macd": "xu_huong", "dong_luong": "xu_huong", "adx": "xu_huong",
    "obv": "dong_tien", "khoi_luong": "dong_tien",
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
# DAO DONG = chi bao co THANG DO co dinh, nen "bat o phia thap" doc duoc thanh
# quay-ve-trung-binh va "bat o phia cao" thanh xu-huong. `adx` va `macd` KHONG
# o day du chung cung la so: ADX cao = xu huong MANH (khong noi chieu), MACD
# khong co bien - xep chung theo phia nguong se cho ra ho sai.
_DAO_DONG = {"rsi", "ibs", "zscore", "stoch", "stochastic", "cci", "phan_vi"}

#: THU TU XET trong `suy_ho`. Mot cau co nhieu chi bao ("RSI(2) closes below 10"
#: co ca `rsi` lan `gia`), nen chi bao DAC TRUNG phai duoc hoi truoc chi bao nen.
#:
#: Truoc 11/09 day la mot tuple VIET CUNG ben trong `suy_ho`, tach roi khoi
#: `_HO_THEO_CHI_BAO`. Hai nguon su that cho cung mot dieu: toi them 15 chi bao
#: vao bang ho, chay lai, va van ra "khac" - vi vong lap khong he doc bang do.
#: Nay mot nguon, va co bai kiem chan hai ben lech nhau.
_UU_TIEN_HO: tuple[str, ...] = (
    # dao dong / phan vi truoc: chung noi ro luat dang bat phia nao
    "rsi", "ibs", "zscore", "stochastic", "stoch", "cci", "phan_vi",
    # pha vo
    "cao_nhat", "thap_nhat",
    # lich / phien
    "gio", "ngay_trong_tuan", "ngay_trong_thang", "thang",
    # dong tien
    "obv", "khoi_luong",
    # xu huong
    "macd", "adx", "dong_luong", "sma", "ema", "wma", "smma",
    # bien dong (sau cung: `bien_do`/`than_nen` hay di kem chi bao khac)
    "atr", "phuong_sai", "do_lech", "bien_do", "than_nen",
)
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
    for ten in _UU_TIEN_HO:
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
        # `chat=False`: hang doi tu vung phai thay duoc cau co toan hang
        # CHUA doc duoc - do dung la thu no di tim.
        if len(cau) > 700 or loai_cau(cau, chat=False) is None:
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
