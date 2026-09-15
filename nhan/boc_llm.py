# -*- coding: utf-8 -*-
"""boc_llm.py - BOC CO CHE bang LLM, ban NANG SUAT.

Chu du an 03/09/2026: *"neu van de o co che boc thi hay tim cach khac phuc hoac
la xay dung bo doc hoac la goi api deepseek ma toi cho cau ket noi vao de luan"*
va truoc do: *"ty le chuyen doi phai xap xi hoac hon nguon dau vao"*.

DO DUOC HOM NAY, va do la ly do file nay ton tai:
  - 3.489 tai lieu -> 2.543 ban doc -> **4 ban tung duoc boc**. Day chuyen
    tai lieu->co che thuc te khong chay.
  - `doc_ma` chay 452 ban ma nguon trong DUOI 1 GIAY (1 ms/ban) va 444/452
    khong ra gi. Nut that KHONG phai toc do.
  - `seeker.boc_co_che` (ban LLM cu) chay 10 bai het 202 giay va ra **0 co che**.

VI SAO BAN CU RA 0. Loi nhac cua no kem danh sach 170 co che da co, cong cau:
  *"KHONG de xuat lai nhung cai tren, ke ca doi ten hay doi tham so. Mot bien
  the SMA/EMA cat nhau nua la lang phi mot suat ngan sach thong ke. Chi de
  xuat khi tai lieu cho mot co che THAT SU KHAC VE BAN CHAT."*
Voi menh lenh do va mot danh sach 170 ten, mo hinh gan nhu buoc phai im. Bo
loc nam ngay TRONG loi nhac, truoc ca khi co gi de loc.

BAN NAY DOI BA DIEU:
  1. **Lay HET luat doc duoc**, bien the duoc hoan nghenh. Chong trung KHONG
     lam bang menh lenh cho mo hinh ma lam bang `ngu_phap.van_tay_dieu_kien`
     - van tay tinh tren DIEU KIEN, nen doi ten khong qua duoc.
  2. **Chi dua tai lieu CO KHA NANG chua luat.** Bai hoc thuat ta PHUONG PHAP
     chu khong ta LUAT (suat do duoc: arxiv 0,8%, openalex 6%). Loc truoc bang
     tu khoa hanh dong thay vi dot mot luot goi cho mot bai khong co luat nao.
  3. **Goi SONG SONG.** API tra trong ~4 giay; chay tuan tu la tu bo 90% thong
     luong. Han muc chi phi van ton tai nhung la mot con so RIENG cua duong
     nay, khong dung chung voi phanh 40 luot/ngay cua `tri_tue`.

KHONG DOI: moi khai bao ra deu phai qua `kiem_khai_bao` + `kiem_khong_nhin_truoc`
truoc khi vao kho. Kien thuc moi chi vao he qua `ngu_phap.py` - khong `exec` ma
LLM sinh. Do la luat khong duoc pha.
"""
from __future__ import annotations

import concurrent.futures as _cf
import json
import re
import time

from nhan import ngu_phap as NP
from nhan import so as SO
from nhan import tri_tue as TT

#: Tai lieu phai co it nhat `DIEM_TOI_THIEU` dau hieu nay moi dang mot luot goi.
#:
#: BAN DAU CHI CO NHOM VAN XUOI, va do la mot loi do 03/09/2026: bo loc duoc
#: viet cho VAN XUOI roi dem ap len MA NGUON. Do that tren 300 ban doc github
#: (co that `class ThreeBarStrategy`, `strategy/indicators.py`): cham **0-1
#: diem, 0/300 qua nguong**. Code khong viet "buy when RSI crosses above 30";
#: no viet `if rsi < 30:`, `self.buy()`, `strategy.entry(...)`, `OrderSend(...)`.
DAU_HIEU_LUAT = [
    # --- van xuoi ---
    r"\b(buy|long|enter)\s+(when|if|signal|entry)", r"\b(sell|short|exit)\s+(when|if)",
    r"\bcross(es|ing)?\s+(above|below|over|under)\b", r"\bstop[\s-]?loss\b",
    r"\btake[\s-]?profit\b", r"\bif\s+.{0,40}\b(rsi|ema|sma|macd|atr|adx|stoch)",
    r"\b(rsi|stochastic|cci)\s*[<>]\s*\d", r"\bclose\s+(above|below)\b",
    r"\bentry\s+(rule|condition|signal)", r"\bexit\s+(rule|condition|signal)",
    r"\bkhi\s+(gia|rsi|ema|sma)\b", r"\b(vao|thoat)\s+lenh\b",
    # --- TIENG VIET CO DAU ---
    # DO 04/09/2026, va la LAN THU HAI cung mot ho loi. Ngay 03/09 bo loc nay
    # duoc viet cho VAN XUOI roi dem ap len MA NGUON: 0/300 ban github qua
    # nguong. Hom nay lay ve 180 bai Telegram tieng Viet (hai kenh chu du an
    # dua) va **161/180 cham DUNG 0 diem** - trong do co bai phan tich DCA vang
    # tren tai khoan cent, du 10 muc lenh, tuc dac luat.
    #
    # Nguyen nhan y het: moi mau tren deu la tieng Anh hoac cu phap lap trinh.
    # Hai mau tieng Viet duy nhat lai viet KHONG DAU (`khi gia`, `vao lenh`),
    # nen khong khop mot chu nao cua van ban that.
    r"\b(mua|b[áa]n)\s+khi\b",
    r"v[àa]o\s+l[ệe]nh", r"tho[áa]t\s+l[ệe]nh",
    r"c[ắa]t\s+l[ỗo]", r"d[ừu]ng\s+l[ỗo]", r"ch[ốo]t\s+l[ờo]i",
    r"\b(tp|sl)\s*[:=]?\s*\d",
    r"khung\s+(m1|m5|m15|m30|h1|h4|d1|w1)\b",
    r"n[ếe]u\s+.{0,40}\bth[ìi]\b",
    r"(v[ưu][ợo]t|ph[áa]\s+v[ỡo]|c[ắa]t)\s+(l[êe]n|xu[ốo]ng|qua)",
    r"[đd][óo]ng\s+n[ếe]n", r"r[âa]u\s+n[ếe]n",
    r"\b(dca|trailing|martingale)\b", r"l[ướơ]i\s+l[ệe]nh",
    r"kh[ốo]i\s+l[ưư][ợo]ng\s+l[ệe]nh", r"t[ỉi]\s*l[ệe]\s*r\s*:?\s*r",
    # --- MA NGUON: Pine ---
    r"strategy\.(entry|close|exit|order)\s*\(", r"\bta\.(crossover|crossunder)\s*\(",
    r"\bplotshape\s*\(", r"//@version\s*=",
    # --- MA NGUON: MQL4/5 ---
    r"\b(OrderSend|PositionOpen|CTrade|trade\.(Buy|Sell))\s*\(",
    r"\bOnTick\s*\(", r"\biCustom\s*\(",
    r"\b(input|extern)\s+(double|int|bool)\s+\w*(SL|TP|Stop|Take|Period|Lot)",
    # --- MA NGUON: Python (backtrader / QuantConnect / vectorbt) ---
    r"self\.(buy|sell|order_target|close)\s*\(",
    r"\b(SetHoldings|MarketOrder|Liquidate)\s*\(",
    r"class\s+\w*Strateg\w*\s*[\(:]", r"def\s+(next|on_data|OnData|handle_data)\s*\(",
    # --- MA NGUON: THU VIEN QUANT dang pandas/numpy VECTOR ---
    #
    # DO 08/09/2026, va la LAN THU BA cung mot ho loi (03/09 van xuoi -> ma
    # nguon; 04/09 tieng Anh -> tieng Viet co dau). Lan nay: **60/60 ban github
    # chua boc cham DUNG 0 diem**, trong do co `joshyattridge/smart-money-concepts`
    # - 40 KB ma tinh FVG, order block, swing, BOS/CHoCH, tuc DUNG cai ngu phap
    # `nguyen_thuy_vung` dang can [[nguyen-thuy-vung]].
    #
    # Nguyen nhan: moi mau ma nguon o tren deu gia dinh mot EA/strategy co LENH
    # (`strategy.entry`, `OrderSend`, `self.buy`). Mot THU VIEN chi bao khong dat
    # lenh bao gio - no tra ve mot DataFrame. Va no viet dang vector
    # (`breaker[idx] = True`) nen khong co ca so sanh kieu `rsi > 30`.
    #
    # Nguong o day co the noi rong an toan: `DIEM_TOI_THIEU = 1` chi quyet dinh
    # cai gi duoc DUA CHO qwen doc, con cong that la `them_co_che` - no chay
    # spec tren du lieu that va tu choi cai khong chay duoc. Loc chat o day thi
    # mat han mot lop nguon; loc rong thi chi ton them vai loi goi qwen.
    r"\b(order[_\s-]?block|fair[_\s-]?value[_\s-]?gap|break[_\s-]?of[_\s-]?structure)\b",
    r"\b(fvg|bos|choch|ob)\b\s*[=\[(]", r"\bliquidity[_\s-]?(sweep|pool|grab)\b",
    r"\bswing[_\s-]?(high|low|highs_lows)\b", r"\bpremium[_\s-]?discount\b",
    r"def\s+\w*(fvg|order_block|swing|liquidity|structure|retracement|session)\w*\s*\(",
    r"\b(highs?|lows?|closes?|opens?)\s*\[\s*(idx|i|index)\s*\]\s*[<>=]",
    r"\bdf\s*\[\s*[\"'](open|high|low|close|volume)[\"']\s*\]",
    r"\bohlc\s*\[\s*[\"'](open|high|low|close)[\"']\s*\]",
    r"\.rolling\s*\([^)]*\)\s*\.\s*(max|min|mean|std)\s*\(",
    r"\bimport\s+(talib|pandas_ta|vectorbt|backtesting|ccxt|yfinance)\b",
    r"\bfrom\s+(backtesting|vectorbt|pandas_ta|talib)\b",

    # --- chung cho moi ngon ngu ---
    r"\b(rsi|ema|sma|macd|atr|adx|stoch|bollinger)\w*\s*[<>=]{1,2}\s*[\d\w]",
    r"\b(sl|tp|stop_?loss|take_?profit)\s*=\s*[\d\w]",
]

#: Ha tu 2 xuong 1: mot file ma nguon co the chi lo dung MOT dau hieu (vd mot
#: dong `strategy.entry`) ma van chua tron mot chien luoc. Doi HAI dau hieu la
#: mot rao khong co co so, va no da giet 300 ban doc tot.
DIEM_TOI_THIEU = 1

# --- LAN THU BA CUNG MOT HO LOI (15/09/2026) ------------------------------
#
# Hai lan truoc da ghi ngay o tren: bo loc viet cho VAN XUOI ANH thi cham ma
# nguon 0 diem (03/09), roi cham tieng Viet CO DAU 0 diem (04/09). Lan nay:
#
#     cau luat y het nhau, dich sang sau thu tieng, cham bang chinh bo do:
#       Anh 5 · Viet 4 · Viet co dau 4 · **Nga 0 · Nhat 0 · Thai 0**
#
# Va no bat duoc dung luc: sang nay seeker vua duoc noi vao SAU dien dan quoc
# gia (mql5 Nga, note.com Nhat, thaiforexschool...). Neu khong sua thi ta vua
# xay mot day chuyen THU VE ROI VUT DI trong im lang - tai lieu cham 0 diem
# khong bao gio vao khau boc, va bang bao cao chi hien ra la "khong co gi de
# boc". [[luat-do-phai-thay-duoc-cai-co]]
#
# HAI LOP MAU, co chu dich:
#   1. TU KHOA theo tung thu tieng - cach nguoi ban dia that su viet.
#   2. MOT MAU KHONG PHU THUOC NGON NGU: ten chi bao luon viet bang chu Latin
#      ke ca trong bai tieng Nhat/Thai/Nga, nen "chi bao + so + phep so sanh"
#      bat duoc luat o BAT KY thu tieng nao - ke ca thu tieng chua ai liet ke.
DAU_HIEU_LUAT += [
    # --- khong phu thuoc ngon ngu: ten chi bao Latin + so/phep so sanh ---
    r"\b(rsi|ema|sma|wma|macd|atr|adx|cci|stoch|bollinger|ichimoku)\s*"
    r"[\(\[]?\s*\d{1,4}\s*[\)\]]?",
    r"\b(rsi|ema|sma|macd|atr|adx|cci|stoch)\b[^\n]{0,24}[<>≥≤]\s*\d",
    r"\b(tp|sl)\s*[:=]\s*\d",
    # --- Nga ---
    r"поку?па(?:ем|ть|йте)?|покупк[аи]|лонг\b",
    r"продава?(?:ть|ем|йте)?|продаж[аи]|шорт\b",
    r"стоп[\s-]?лосс|тейк[\s-]?профит|стоп[\s-]?приказ",
    r"когда\s+.{0,30}(rsi|ema|sma|macd|цена)",
    r"(выше|ниже|пересека)\w*\s+.{0,20}(ema|sma|rsi|цены?)",
    # --- Nhat ---
    r"買[いうえ]|売[りるれ]|ロング|ショート",
    r"損切り|利確|利食い|逆指値|指値",
    r"(上回|下回|抜け|クロス)",
    # --- Trung ---
    r"买入|做多|卖出|做空|止损|止盈|多单|空单",
    r"(上穿|下穿|突破|回踩)",
    # --- Han ---
    r"매수|매도|손절|익절|돌파",
    # --- Thai ---
    r"ซื้อ|ขาย|ตัดขาดทุน|ทำกำไร|จุดเข้า|จุดออก",
    # --- Tay Ban Nha / Bo Dao Nha ---
    r"\b(comprar|vender)\s+(cuando|quando|si|se)\b",
    r"\b(stop\s+loss|stop\s+de\s+p[ée]rdida|toma\s+de\s+ganancia)\b",
    # --- Duc ---
    r"\b(kaufen|verkaufen)\s+(wenn|falls)\b",
    r"\b(einstieg|ausstieg)s?(regel|signal)\b",
    # --- Tho Nhi Ky / Indonesia / Phap / Y ---
    r"\b(al|sat)[ıi][şs]\s+(sinyali|kural)",
    r"\b(beli|jual)\s+(ketika|jika|saat)\b",
    r"\b(acheter|vendre)\s+(quand|si|lorsque)\b",
    r"\b(comprare|vendere)\s+(quando|se)\b",
]

_RX = [re.compile(p, re.I) for p in DAU_HIEU_LUAT]

HE_THONG = (
    "Ban la bo trich xuat LUAT GIAO DICH. Ban KHONG danh gia chien luoc tot hay "
    "xau, KHONG khuyen nghi. Ban chi doc tai lieu va viet lai cac luat vao dung "
    "mot ngu phap JSON cho truoc. Neu tai lieu khong co luat cu the nao thi tra "
    "mang rong - dung bia."
)


def _diem_luat(vb: str) -> int:
    return sum(1 for rx in _RX if rx.search(vb or ""))


def _la_html_tho(vb: str) -> bool:
    """Ban doc la TRANG HTML CHUA BOC, khong phai van ban.

    Do 05/09/2026 tren 150 ung vien hang dau: **143 cai la trang HTML tho cua
    GitHub** — `<!DOCTYPE html>` + 340.000-630.000 ky tu boilerplate, cua nhung
    repo nhu `RadialMenuKit-swiftUI`, `syntest` (khong lien quan giao dich).
    Chung lot vao vi bo cham dem SO dau hieu luat: mot trang 340k ky tu cham du
    diem hoan toan ngau nhien.

    Do la ly do that cua "3/259 bai ra co che" — khong phai mo hinh doc kem, ma
    la khau THU THAP luu nguyen trang tim kiem thay vi van ban. Doi model khong
    cuu duoc gi o day; goi API tren chung la dot tien.
    """
    dau = (vb or "")[:600].lstrip()
    if "<!doctype html" in dau.lower() or dau.startswith("<html"):
        return True
    # Trang da bi cat dau nhung than van la HTML: dem the tren 2.000 ky tu dau.
    mau = (vb or "")[:2000]
    return mau.count("<") > 40 and mau.count("</") > 20


def ung_vien(gioi_han: int = 200, diem_toi_thieu: int | None = None,
             nguon_uu_tien=("tradingview_pine", "tradingview_scripts", "mql5_code",
                            "mql5_bai_viet", "github", "lean_algo", "blog",
                            "rss_tradingview_blog", "quantconnect")) -> list[dict]:
    """Ban doc CHUA duoc boc, co dau hieu chua luat, uu tien nguon suat cao."""
    # Truoc 04/09 tham so nay hardcode `2` trong khi hang so khai bao
    # `DIEM_TOI_THIEU = 1` (da ha xuong 1 ngay 03/09 vi "doi HAI dau hieu la mot
    # rao khong co co so"). Tuc duong VAN XUOI van chay o nguong CU, chi duong
    # MA NGUON duoc ha - mot lan sua chi ap duoc mot nua.
    nguong = DIEM_TOI_THIEU if diem_toi_thieu is None else diem_toi_thieu

    def _lay(n: int):
        return SO.nhieu(
            "SELECT n.id, n.van_ban, n.so_ky_tu, n.kieu, t.tieu_de, t.nguon, t.url "
            "FROM noi_dung n LEFT JOIN tai_lieu t ON t.id = n.tai_lieu_id "
            "WHERE n.da_boc = 0 AND n.so_ky_tu > 800 AND n.kieu != 'khong_doc_duoc' "
            "ORDER BY CASE WHEN t.nguon IN ({}) "
            "            OR t.nguon LIKE 'telegram%' THEN 0 ELSE 1 END, n.id DESC "
            "LIMIT ?".format(",".join("?" for _ in nguon_uu_tien)),
            *nguon_uu_tien, n) or []

    # LAY THEM CHO DEN KHI DU, dung nhan cung mot he so.
    #
    # He so ×8 dat khi bo loc chi bo vai ban doc. Tu khi `_la_html_tho` chan
    # trang HTML chua boc, no bo **143/150 ban doc dau bang**, nen `ung_vien(20)`
    # quet 160 dong roi tra ve RONG - va mot me boc doc do thanh "khong con gi
    # de boc". Cai bay quen thuoc: mot bo loc dung lam mot phep dem thanh 0.
    def _qua_loc(ds_):
        ra_ = []
        for r in ds_:
            d = dict(r)
            if _la_html_tho(d["van_ban"]):
                continue
            d["_diem"] = _diem_luat(d["van_ban"])
            if d["_diem"] >= nguong:
                d["_mat_do"] = d["_diem"] / max(d["so_ky_tu"], 1) * 1e4
                ra_.append(d)
        return ra_

    ds = _lay(gioi_han * 8)
    ra = _qua_loc(ds)
    # Dieu kien leo thang phai dem so ung vien QUA CA HAI bo loc. Ban dau no
    # dem "khong phai HTML" (71/160) roi dung — trong khi chi **1** cai qua duoc
    # nguong dau hieu luat, nen `ung_vien(20)` van tra ve gan rong.
    for he_so in (32, 128, 512):
        if len(ra) >= gioi_han or len(ds) < gioi_han * (he_so // 4):
            break
        ds = _lay(gioi_han * he_so)
        ra = _qua_loc(ds)

    # XEP THEO MAT DO LUAT, KHONG THEO DO DAI.
    #
    # DO 04/09/2026. Truoc do cau lenh xep `n.so_ky_tu DESC`, va hau qua chi lo
    # ra khi co mot nguon MOI voi hinh dang khac: 180 bai Telegram vua lay ve,
    # 100 bai qua duoc bo loc dau hieu luat, va **khong bai nao tung den luot**
    # - vi bai Telegram dai 2-4 nghin ky tu con mot trang blog hay mot file
    # `.mq5` dai 30-40 nghin, nen o thu tu giam dan theo do dai thi ca lop nguon
    # do nam duoi day mai mai.
    #
    # Do dai KHONG phai mat do luat. Mot bai 2.000 ky tu noi thang "vao khi RSI
    # < 30, cat lo 1%, chot 2%" dac luat hon mot trang 40.000 ky tu ke chuyen.
    # Nen: lay theo THU TU MOI NHAT (bai vua thu hoach la bai chua ai boc), roi
    # xep lai theo SO DAU HIEU LUAT dem duoc, roi moi cat `gioi_han`.
    # MAT DO, khong phai SO DEM, o khoa phu. Mot trang 340.000 ky tu se cham du
    # 5 dau hieu luat hoan toan ngau nhien, va no day het bai ngan ra khoi danh
    # sach du khong mang mot luat nao.
    ra.sort(key=lambda d: (-d["_diem"], -d["_mat_do"]))
    return ra[:gioi_han]


def ung_vien_artifact(gioi_han: int = 300, diem_toi_thieu: int | None = None) -> list[dict]:
    """Ma nguon nam trong bang `artifact` (type `code`) chu khong o `noi_dung`.

    MAT XICH DUT tim ra 03/09/2026: `ma_nguon.thu_thap` tai file `.mq5` THAT
    ve va ghi vao **`artifact`**; con `boc_llm.ung_vien` doc **`noi_dung`**.
    Ket qua: 290 file .mq5 vua cao ve nam ngoai tam voi cua bo boc, va bao cao
    hien ra la "0 co che" trong khi kho vua day len 377 artifact code.

    Danh dau da boc bang mot dong trong `chi_so_vh` (bang `artifact` la
    CHI-GHI-THEM, khong duoc UPDATE).
    """
    da = {str(r["chi_tiet"]) for r in (SO.nhieu(
        "SELECT chi_tiet FROM chi_so_vh WHERE ten='boc_artifact'") or [])}
    rows = SO.nhieu(
        "SELECT id, fingerprint, payload FROM artifact "
        "WHERE artifact_type='code' ORDER BY id DESC LIMIT ?", gioi_han * 3) or []
    nguong = DIEM_TOI_THIEU if diem_toi_thieu is None else diem_toi_thieu
    ra = []
    for r in rows:
        d = dict(r)
        if str(d["id"]) in da:
            continue
        try:
            pl = json.loads(d["payload"])
        except Exception:
            continue
        # Payload LONG mot tang: cot `payload` chua {artifact_type, fingerprint,
        # payload, schema_version}, va ma nguon nam o `payload["payload"]`.
        if isinstance(pl.get("payload"), dict):
            pl = pl["payload"]
        vb = pl.get("content") or pl.get("noi_dung") or ""
        if len(vb) < 800 or _diem_luat(vb) < nguong:
            continue
        ra.append({"id": f"art:{d['id']}", "artifact_id": d["id"],
                   "van_ban": vb, "so_ky_tu": len(vb),
                   "tieu_de": pl.get("title") or pl.get("ten_file") or "",
                   "nguon": "mql5_code",
                   "url": pl.get("source_url") or pl.get("url") or ""})
        if len(ra) >= gioi_han:
            break
    return ra


def _nhac(d: dict) -> str:
    return (
        NP.NP_TOM_TAT if hasattr(NP, "NP_TOM_TAT") else _ngu_phap_tom_tat()
    ) + (
        "\n\nNHIEM VU: doc tai lieu duoi day va viet lai MOI luat vao lenh / thoat "
        "lenh ma no mo ta, theo ngu phap tren.\n"
        "- Lay HET, ke ca bien the gan giong nhau (RSI<30 va RSI<25 la HAI luat).\n"
        "- Moi luat can mot cau `co_che` giai thich VI SAO co nguoi tra tien cho "
        "phoi nhiem do (it nhat 25 ky tu).\n"
        "- `ho` phai thuoc: xu_huong, quay_ve_trung_binh, pha_vo, bien_dong, "
        "dong_tien, phien, lich, vi_mo, khac.\n"
        "- Chi dung toan hang co trong ngu phap. Thieu thi bo luat do va ghi vao "
        "`khong_dien_dat_duoc`.\n"
        "- Neu tai lieu khong co luat cu the nao: tra `co_che` la mang RONG.\n\n"
        'Tra ve DUNG mot JSON: {"co_che": [...], "khong_dien_dat_duoc": "..."}\n\n'
        f"== TAI LIEU: {d.get('tieu_de') or ''} ==\n"
        f"nguon: {d.get('nguon')} | dia chi: {d.get('url')}\n\n"
        f"{(d.get('van_ban') or '')[:40000]}")


def _ngu_phap_tom_tat() -> str:
    from tru import seeker as SK
    return getattr(SK, "NP_TOM_TAT", "")



def chuan_hoa_spec(spec: dict) -> dict:
    """Sua nhung sai lech DINH DANG cua dau ra LLM, truoc khi qua cong ngu phap.

    Do that 03/09/2026 tren lo thu dau tien: 2/4 khai bao bi loai chi vi
    `'giu' phai la so nguyen 1..500` - mo hinh tra `giu` la so thuc, chuoi,
    hoac null. Do la loi DINH DANG, khong phai loi noi dung; de nguyen thi mat
    mot nua san luong ma khong hoc duoc gi.

    Chi sua KIEU va MIEN. KHONG dung vao dieu kien, khong doan gia tri thieu,
    khong bia toan hang. Cong ngu phap van la nguoi phan xu cuoi.
    """
    if not isinstance(spec, dict):
        return spec
    d = dict(spec)

    # giu: so nguyen 1..500
    g = d.get("giu", 1)
    try:
        g = int(float(g))
    except (TypeError, ValueError):
        g = 1
    d["giu"] = min(500, max(1, g))

    # chieu: 1 hoac -1
    c = d.get("chieu", 1)
    try:
        c = int(float(c))
    except (TypeError, ValueError):
        c = 1
    d["chieu"] = -1 if c < 0 else 1

    # ten: bat buoc, chuan hoa ve [a-z0-9_]
    ten = NP.chuan_hoa_ten(str(d.get("ten") or ""))
    if not ten:
        ten = "llm_" + (NP.chuan_hoa_ten(str(d.get("co_che") or ""))[:40] or "khong_ten")
    d["ten"] = ten

    # vao/ra phai la list
    for k in ("vao", "ra"):
        v = d.get(k)
        if v is None:
            d[k] = []
        elif isinstance(v, dict):
            d[k] = [v]
        elif not isinstance(v, list):
            d[k] = []

    # hang phai la so
    def _so_hoa(nut):
        if isinstance(nut, dict):
            if "hang" in nut:
                try:
                    nut["hang"] = float(nut["hang"])
                except (TypeError, ValueError):
                    return False
            if "n" in nut and nut["n"] is not None:
                try:
                    nut["n"] = int(float(nut["n"]))
                except (TypeError, ValueError):
                    nut.pop("n", None)
            for v in nut.values():
                if isinstance(v, (dict, list)) and _so_hoa(v) is False:
                    return False
        elif isinstance(nut, list):
            for v in nut:
                if _so_hoa(v) is False:
                    return False
        return True

    for k in ("vao", "ra"):
        _so_hoa(d[k])
    return d


def _mot_ban(d: dict) -> dict:
    t0 = time.time()
    try:
        kq = TT.hoi_json(_nhac(d), HE_THONG, bo_qua_han_muc=True, dung_cache=False)
    except Exception as e:
        return {"id": d["id"], "loi": f"{type(e).__name__}: {str(e)[:80]}",
                "giay": time.time() - t0}
    # `hoi_json` tra `{"loi": ...}` chu KHONG nem ngoai le khi goi hong, va
    # `.get("json")` tren dict do ra `{}`. Khong tach ra thi mot me het quota /
    # sai model chay rat nhanh va bao "0 co che, 0 tu choi, 0 loi" - doc y het
    # mot ket qua am that. Do 05/09 tren ca ba module boc
    # ([[ket-luan-am-phai-phan-biet-chua-do]]).
    if kq.get("loi") or kq.get("bo_qua"):
        return {"id": d["id"], "url": d.get("url"), "nguon": d.get("nguon"),
                "co_che": [], "chua_do": True,
                "loi": "CHUA DO - %s" % str(kq.get("loi") or kq.get("bo_qua"))[:90],
                "giay": time.time() - t0}
    j = kq.get("json") or {}
    return {"id": d["id"], "url": d.get("url"), "nguon": d.get("nguon"),
            "co_che": j.get("co_che") or [],
            "thieu": j.get("khong_dien_dat_duoc") or "",
            "giay": time.time() - t0}


def boc(gioi_han: int = 50, luong: int = 6, ghi_kho: bool = True,
        df_kiem=None, in_ra=print) -> dict:
    """Boc `gioi_han` ban doc, goi SONG SONG `luong` luot.

    `df_kiem=None` de nguyen thi `them_co_che` **bo qua bai chay thu** — spec
    khong chay duoc van vao kho (do 05/09: 54 spec kieu do da nam san trong kho
    va duoc dem vao con so co che). Nen o day tu nap chuoi kiem chuan.
    """
    from nhan import boc_ma_llm as BM       # noqa: F401  (dung o vong duoi)
    # Het dia thi me boc chay het, ghi khong duoc, va bao "0 co che moi" - dung
    # hinh dang cua mot ket qua am. Chan o dau me.
    from nhan import ngan_sach as _NS
    _NS_giu = _NS.xin("LLM", "boc mot me", cho_giay=120)
    _NS_giu.__enter__()
    if df_kiem is None:
        from nhan import loc_co_che as LCC
        df_kiem = LCC.df_kiem_chuan()
        if df_kiem is None:
            in_ra("  !! khong nap duoc chuoi kiem - se KHONG ghi kho")
            ghi_kho = False
    ds = ung_vien(gioi_han)
    con = gioi_han - len(ds)
    if con > 0:
        them = ung_vien_artifact(con)
        ds += them
        in_ra(f"  + {len(them)} ma nguon tu bang `artifact` (file .mq5 that)")
    in_ra(f"  {len(ds)} ban doc co dau hieu chua luat (tren tong chua boc)")
    if not ds:
        return {"ban": 0, "co_che_moi": 0}

    t0 = time.time()
    ket = []
    with _cf.ThreadPoolExecutor(max_workers=luong) as ex:
        for i, r in enumerate(ex.map(_mot_ban, ds), 1):
            ket.append(r)
            if i % 10 == 0:
                in_ra(f"  ... {i}/{len(ds)}  ({time.time()-t0:.0f}s)")

    _NS_giu.__exit__(None, None, None)
    da_co = {NP.van_tay_dieu_kien(c) for c in NP.doc_kho()}
    moi, tu_choi, loi = 0, 0, 0
    ly_do = {}
    for r in ket:
        if r.get("loi"):
            loi += 1
            continue
        for spec in r["co_che"]:
            if not isinstance(spec, dict):
                continue
            spec = chuan_hoa_spec(spec)
            spec.setdefault("nguon", r.get("url") or r.get("nguon") or "boc_llm")
            # Cung cho dien `co_che` voi hai duong boc ma nguon: cong doi mot
            # cau >= 25 ky tu, va loi nhac chua bao gio xin no. Khong dien thi
            # ca me bi tu choi vi mot ly do DINH DANG (do 05/09: 80/80 o lan
            # chien luoc). Cau tu dien noi ro la CHUA co lap luan kinh te.
            BM._dien_co_che(spec, str(spec.get("nguon") or ""))
            v = NP.kiem_khai_bao(spec)
            if v:
                tu_choi += 1
                ly_do[v[0][:60]] = ly_do.get(v[0][:60], 0) + 1
                continue
            try:
                vt = NP.van_tay_dieu_kien(spec)
            except Exception:
                tu_choi += 1
                continue
            if vt in da_co:
                tu_choi += 1
                ly_do["trung dieu kien"] = ly_do.get("trung dieu kien", 0) + 1
                continue
            if ghi_kho:
                try:
                    kq = NP.them_co_che(spec, df_kiem)
                    if not kq.get("nhan"):
                        tu_choi += 1
                        ly_do[str(kq.get("ly_do"))[:60]] = \
                            ly_do.get(str(kq.get("ly_do"))[:60], 0) + 1
                        continue
                except Exception as e:
                    tu_choi += 1
                    ly_do[f"them_co_che: {type(e).__name__}"] = \
                        ly_do.get(f"them_co_che: {type(e).__name__}", 0) + 1
                    continue
            da_co.add(vt)
            moi += 1

    with SO.ket_noi() as cn:
        for r in ket:
            if r.get("loi"):
                continue
            i = r["id"]
            if isinstance(i, str) and i.startswith("art:"):
                # `artifact` la CHI-GHI-THEM: danh dau o `chi_so_vh`.
                cn.execute("INSERT INTO chi_so_vh(ten,gia_tri,chi_tiet,luc) "
                           "VALUES('boc_artifact',1,?,?)",
                           (i.split(":", 1)[1], SO.bay_gio()))
            else:
                cn.execute("UPDATE noi_dung SET da_boc=1 WHERE id=?", (i,))

    giay = time.time() - t0
    # Ghi so de dem duoc "bao nhieu co che moi HOM NAY". Kho co che
    # (`ngu_phap.doc_kho`) khong co truong thoi gian nao, nen khong co dong nay
    # thi chi tieu ngay khong do duoc muc quan trong nhat cua no.
    SO.ghi_chi_so("boc_co_che_moi", float(moi),
                  {"ban": len(ds), "tu_choi": tu_choi, "loi": loi})
    return {"ban": len(ds), "co_che_moi": moi, "tu_choi": tu_choi, "loi": loi,
            "giay": round(giay, 1), "giay_moi_ban": round(giay / max(len(ds), 1), 1),
            "suat_tren_100_ban": round(moi / max(len(ds), 1) * 100, 1),
            "ly_do_tu_choi": dict(sorted(ly_do.items(), key=lambda x: -x[1])[:8])}
