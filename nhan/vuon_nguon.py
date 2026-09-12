# -*- coding: utf-8 -*-
"""vuon_nguon.py - VUON NGUON: do suat, chia ngan sach, tu tim nguon moi.

BA VIEC, MOT CHO, vi ca ba dung chung mot con so:

  1. **DO SUAT** - moi nguon sinh ra bao nhieu UNG VIEN tren 100 bai. Do la
     thuoc do duy nhat co nghia. "Thu ve 864 bai" khong noi gi ca: 864 bai
     tin hieu Telegram cho 0 ung vien, con 260 bai blog cho 39.
  2. **CHIA NGAN SACH GIUA HAI LAN** theo suat do duoc, khong theo cam tinh:
       - lan `hoc_thuat`: feed/API - bai viet co luat, tap chi, ma nguon;
       - lan `xa_hoi`: dien dan/social qua trinh duyet.
     Chia theo suat NHUNG co san tham do: lan nao cung duoc it nhat `SAN_THAM_DO`
     phan ngan sach, neu khong thi mot lan bi doi 0 vinh vien va khong bao gio
     co co hoi chung minh nguoc lai.
  3. **TU TIM NGUON MOI** - kho tu noi ra nguon tiep theo: bai viet tot dan
     sang blog khac. Quet lien ket ra ngoai trong chinh cac bai da thu, dem
     ten mien, do thu duong feed, cai nao tra feed that thi cho vao dien THU.

VONG DOI MOT NGUON: `THU` (tham do) -> `BAT` (dat suat) hoac `TAT` (het han
tham do ma khong sinh duoc ung vien nao). Khong nguon nao vao thang `BAT`, va
khong nguon nao bi xoa - tat roi van giu lai ly do, de lan sau khong co ai
them lai chinh no.

CAI KHONG LAM: module nay khong doc noi dung, khong sinh co che, khong xep viec
backtest. No chi tra loi "dao o dau" va "dao bao lau".
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

LAB = Path(__file__).resolve().parent.parent
KHO_NGUON_MOI = LAB / "config" / "nguon_tu_tim.json"

#: Hai lan dau vao. `ma` cua nguon duoc xep lan theo tien to / danh sach nay.
LAN = {
    "hoc_thuat": {
        "mo_ta": "feed bai viet, tap chi, ma nguon - noi nguoi ta viet LUAT",
        "tien_to": ("rss_", "trang_"),
        "ten": {"arxiv", "github", "openalex", "stackexchange", "hackernews",
                "semantic", "lean_algo", "mql5_code", "blog", "quantconnect",
                "crossref", "mql5_ma_nguon"},
    },
    "xa_hoi": {
        "mo_ta": "dien dan va mang xa hoi qua trinh duyet - noi nguoi ta KE",
        "tien_to": ("browser_",),
        # `fxblue` va `etoro` RUT khoi lan nay 12/09/2026: tu hom do ca hai doc
        # bang `requests` (sitemap XML va API JSON), khong qua trinh duyet nua
        # - xem `seeker.n_fxblue` / `n_etoro`. De chung o day thi suat cua
        # chung duoc cong vao lan "qua trinh duyet", tuc ngan sach gio chia
        # theo mot phep do KHONG dung duong chay that. `_lan_cua` mac dinh tra
        # "hoc_thuat" nen bo ten ra la du.
        "ten": {"reddit_td", "x", "tiktok", "facebook", "youtube", "telegram",
                "mql5_signals", "myfxbook", "collective2",
                "zulutrade", "darwinex"},
    },
}

#: Phan ngan sach toi thieu cho MOI lan, du suat do duoc bang 0.
#:
#: Khong co san nay thi he thanh mot vong lap tu khang dinh: lan nao dang thang
#: duoc them gio, nen no cang thang, nen no lai duoc them gio. San tham do la
#: gia phai tra de biet minh co dang sai khong.
SAN_THAM_DO = 0.15
#: Va tran, de mot lan dang thang khong nuot sach.
TRAN_MOT_LAN = 0.75

#: Hang so lam min cua suat (Laplace). Mot nguon moi co 0 bai khong duoc coi la
#: suat 0 - no chua duoc thu. Cong nay cho no khoi diem bang mot nguon trung binh.
MIN_A = 1.0
MIN_B = 20.0

#: Bao nhieu BAI thi het han tham do. Duoi nguong nay chua ket luan duoc gi.
HAN_THAM_DO_BAI = 40


# ------------------------------------------------------------------ DO SUAT
def _lan_cua(ma: str) -> str:
    for ten_lan, c in LAN.items():
        if ma in c["ten"] or any(ma.startswith(t) for t in c["tien_to"]):
            return ten_lan
    return "hoc_thuat"


def thong_ke_nguon() -> dict[str, dict]:
    """{ma_nguon: {bai, ky_tu, ung_vien, suat, lan}} - do tren SO CAI.

    `ung_vien` dem theo `nguon_url` cua ung vien anh xa nguoc ve `tai_lieu.url`.
    Do la duong duy nhat noi mot ung vien voi noi no sinh ra.
    """
    ra: dict[str, dict] = {}
    for r in SO.nhieu(
            "SELECT t.nguon ma, COUNT(nd.id) bai, "
            "COALESCE(SUM(nd.so_ky_tu),0) ky_tu "
            "FROM tai_lieu t JOIN noi_dung nd ON nd.tai_lieu_id=t.id "
            "WHERE nd.so_ky_tu > 0 GROUP BY t.nguon"):
        ra[r["ma"]] = {"bai": int(r["bai"]), "ky_tu": int(r["ky_tu"]),
                       "ung_vien": 0, "co_che": 0}

    # url -> nguon, de anh xa nguoc ung vien
    url2nguon = {r["url"]: r["nguon"] for r in SO.nhieu(
        "SELECT url, nguon FROM tai_lieu WHERE url IS NOT NULL AND url<>''")}
    for r in SO.nhieu("SELECT payload FROM artifact WHERE artifact_type='candidate'"):
        try:
            p = json.loads(r["payload"]).get("payload") or {}
            md = p.get("metadata") or {}
        except Exception:
            continue
        ma = url2nguon.get(str(md.get("nguon_url") or ""))
        if not ma or ma not in ra:
            continue
        ra[ma]["ung_vien"] += 1
        if md.get("dsl"):
            ra[ma]["co_che"] += 1

    for ma, d in ra.items():
        d["lan"] = _lan_cua(ma)
        d["suat"] = round(100.0 * (d["ung_vien"] + MIN_A) / (d["bai"] + MIN_B), 2)
        d["suat_tho"] = round(100.0 * d["ung_vien"] / d["bai"], 2) if d["bai"] else 0.0
    return ra


def suat_lan() -> dict[str, dict]:
    """Gop suat theo lan. Tra {lan: {bai, ung_vien, suat, nguon}}."""
    tk = thong_ke_nguon()
    ra = {ten: {"bai": 0, "ky_tu": 0, "ung_vien": 0, "co_che": 0, "nguon": 0}
          for ten in LAN}
    for ma, d in tk.items():
        o = ra[d["lan"]]
        o["bai"] += d["bai"]
        o["ky_tu"] += d["ky_tu"]
        o["ung_vien"] += d["ung_vien"]
        o["co_che"] += d["co_che"]
        o["nguon"] += 1
    for o in ra.values():
        o["suat"] = round(100.0 * (o["ung_vien"] + MIN_A) / (o["bai"] + MIN_B), 2)
        o["suat_tho"] = round(100.0 * o["ung_vien"] / o["bai"], 2) if o["bai"] else 0.0
    return ra


def chia_ngan_sach(tong_giay: float) -> dict[str, float]:
    """Chia ngan sach THU THAP cho hai lan theo suat do duoc.

    Co san tham do va tran, nen khong lan nao bi khoa vinh vien va khong lan
    nao nuot sach. Tra so GIAY cho tung lan.
    """
    s = suat_lan()
    tho = {ten: max(s[ten]["suat"], 0.01) for ten in LAN}
    tong = sum(tho.values())
    phan = {ten: tho[ten] / tong for ten in LAN}

    # DO DAY, khong phai "ap tran roi chuan hoa lai". Chuan hoa SAU khi ap tran
    # se DAY NGUOC lan vua bi cat len tren tran: ap tran 0,75 cho lan A va san
    # 0,15 cho lan B ra tong 0,90, chia lai cho 0,90 thi A tro lai 0,833.
    # Bo test bat duoc that: lan hoc_thuat nhan 484/600 giay = 80,7% trong khi
    # tran khai bao la 75%.
    #
    # Cach dung: KHOA lan da cham san/tran o dung gia tri do, roi chia PHAN CON
    # LAI cho nhung lan chua khoa - lap toi khi khong con ai vuot.
    n = max(len(phan), 1)
    san, tran = min(SAN_THAM_DO, 1.0 / n), max(TRAN_MOT_LAN, 1.0 / n)
    for _ in range(n + 1):
        khoa = {t: (san if v < san else tran)
                for t, v in phan.items() if v < san or v > tran}
        if not khoa:
            break
        con = 1.0 - sum(khoa.values())
        tu_do = {t: v for t, v in phan.items() if t not in khoa}
        tong_td = sum(tu_do.values())
        moi = dict(khoa)
        for t, v in tu_do.items():
            moi[t] = (con * v / tong_td) if tong_td > 0 else con / max(len(tu_do), 1)
        if moi == phan:
            break
        phan = moi

    # DON PHAN DU. Khi MOI lan deu cham san hoac tran trong cung mot vong thi
    # khong con lan tu do nao de nhan phan con lai, va tong tut xuong duoi 1:
    # o bien "suat 99 vs 0" ta duoc 0,75 + 0,15 = 0,90, tuc mat 10% ngan sach.
    # Phan du di ve nhung lan CON CHO (chua cham tran), chia theo khoang trong.
    con = 1.0 - sum(phan.values())
    if abs(con) > 1e-9:
        cho = ({t: tran - v for t, v in phan.items() if tran - v > 1e-9} if con > 0
               else {t: v - san for t, v in phan.items() if v - san > 1e-9})
        tong_cho = sum(cho.values())
        if tong_cho > 1e-12:
            for t, k in cho.items():
                phan[t] += con * k / tong_cho
    return {ten: round(tong_giay * phan[ten], 1) for ten in phan}


# ---------------------------------------------------------- KHO NGUON TU TIM
def doc_kho() -> dict:
    try:
        d = json.loads(KHO_NGUON_MOI.read_text(encoding="utf-8-sig"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def luu_kho(d: dict) -> None:
    KHO_NGUON_MOI.parent.mkdir(parents=True, exist_ok=True)
    tmp = KHO_NGUON_MOI.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(KHO_NGUON_MOI)


# --------------------------------------------------------- TIM NGUON MOI
#: Ten mien KHONG bao gio la nguon kien thuc: ha tang, mang xa hoi, ban hang.
#: Khong phai danh sach cam vi ly do dao duc - chi la nhung cho khong co bai
#: viet co luat, va moi lan do thu chung deu ton mot lan goi mang.
BO_QUA_MIEN = re.compile(
    r"(?:^|\.)(?:google|gstatic|googleapis|facebook|twitter|x|instagram|linkedin"
    r"|youtube|youtu|tiktok|pinterest|reddit|amazon|amzn|paypal|stripe|gravatar"
    r"|wordpress|w3|schema|creativecommons|doubleclick|cloudflare|jsdelivr"
    r"|bootstrapcdn|fontawesome|wikipedia|wikimedia|archive|github|gitlab"
    r"|apple|microsoft|mozilla|adobe|bit|goo|t|buff|feedburner|substackcdn)\."
    , re.I)

#: Nhan con cua HA TANG ANH/FILE, khong phai noi ai viet bai. Do that 23/08:
#: 8/20 ten mien dan nhieu nhat la CDN (`substack-post-media.s3.amazonaws.com`
#: 28 lan, `blogger.googleusercontent.com` 13, `i0.wp.com` 10) - do thu feed
#: tren chung la ton mang cho mot cau tra loi da biet truoc.
NHAN_HA_TANG = {"s3", "cdn", "cdn1", "cdn2", "img", "imgs", "image", "images",
                "static", "assets", "media", "preview", "files", "uploads",
                "i0", "i1", "i2", "scanner-backend", "api", "cdn-cgi"}
DUOI_HA_TANG = (".amazonaws.com", ".googleusercontent.com", ".wpenginepowered.com",
                ".wp.com", ".cloudfront.net", ".akamaized.net", ".redd.it",
                ".substackcdn.com", ".gstatic.com")


def _la_ha_tang(mien: str) -> bool:
    if re.fullmatch(r"[\d.]+", mien) or mien.startswith("127."):
        return True
    if any(mien.endswith(d) for d in DUOI_HA_TANG):
        return True
    return bool(set(mien.split(".")) & NHAN_HA_TANG)


#: Duong feed pho bien. Thu tu theo xac suat trung, do that tren 27 feed dang co.
DUONG_FEED = ("/feed/", "/feed", "/rss.xml", "/index.xml", "/atom.xml",
              "/feed.xml", "/rss/", "/blog/feed/")

#: Bao nhieu tu khoa nganh KHAC NHAU thi tinh la nguon giao dich. Dem so LAN
#: thi hong: `doi.org/index.xml` lot voi diem 3 chi vi mot chu "market" lap ba
#: lan. Dem so tu KHAC NHAU moi phan biet duoc mot bai giao dich voi mot trang
#: tinh co nhac tu do.
NGUONG_NGANH = 6

#: Tu khoa trong tieu de/noi dung feed cho thay day la nguon GIAO DICH.
#: Mot blog nau an cung co feed hop le - hop le khong co nghia la lien quan.
DAU_HIEU_NGANH = re.compile(
    r"\b(?:trading|trader|quant|backtest|strategy|strategies|portfolio|alpha"
    r"|momentum|volatility|hedge|futures|equities|forex|systematic|market"
    r"|sharpe|drawdown|indicator|algorithmic)\b", re.I)


#: Ngon ngu cua cac cong dong quant lon ngoai tieng Anh.
#:
#: Chu du an chot 30/08: "tim da ngon ngu de tan dung toi da cac cong dong".
#: Kho hien tai gan nhu chi tieng Anh - do 30/08 tren 1.194 ban doc. Nhung ba
#: cong dong quant lon nhat ngoai tieng Anh (Trung, Nga, Nhat) co truyen thong
#: chia se ma nguon rat manh, va ho KHONG viet bang tieng Anh.
#:
#: Dung de: (1) sinh truy van cho cac nguon `kieu=tu_khoa`, (2) cham diem mot
#: mien ung vien - mot trang tieng Trung ve luong hoa van la nguon tot.
TU_KHOA_NGON_NGU = {
    "trung": ["量化交易", "量化投资 策略", "回测 框架", "因子挖掘", "高频交易 策略"],
    "nga":   ["алгоритмический трейдинг", "квантовые стратегии", "бэктест стратегии"],
    "nhat":  ["システムトレード 戦略", "アルゴリズム取引", "バックテスト 手法"],
    "tay_ban_nha": ["trading algoritmico estrategia", "backtesting cuantitativo"],
    "bo_dao_nha": ["trading quantitativo estrategia", "backtest algoritmico"],
    "han":   ["퀀트 투자 전략", "알고리즘 트레이딩 백테스트"],
    "duc":   ["algorithmischer handel strategie", "quantitative handelsstrategie"],
}

#: Mien cua cac cong dong do — de `mien_ung_vien` khong loai chung vi "la".
MIEN_CONG_DONG_NGOAI = (
    "zhihu.com", "csdn.net", "jianshu.com", "juejin.cn", "cnblogs.com",
    "uqer.io", "joinquant.com", "ricequant.com", "myquant.cn",
    "habr.com", "smart-lab.ru",
    "qiita.com", "note.com",
    "velog.io", "tistory.com",
)


def tu_khoa_da_ngon_ngu(so_moi_thu: int = 1) -> list[str]:
    """Lay tu khoa o NHIEU ngon ngu, moi thu tieng vai cum.

    Tra ve danh sach phang de nguoi goi ghep vao truy van tim kiem. Khong dich
    may: cac cum nay do nguoi viet, vi mot ban dich may cua "mean reversion"
    thuong khong phai cum ma cong dong do THUC SU dung.
    """
    ra = []
    for cac in TU_KHOA_NGON_NGU.values():
        ra.extend(cac[:max(1, so_moi_thu)])
    return ra


def mien_ung_vien(gioi_han: int = 60, it_nhat: int = 2) -> list[tuple[str, int]]:
    """Ten mien duoc CAC BAI DA THU dan sang, xep theo so lan dan.

    Day la cach kho tu noi ra nguon tiep theo: mot blog quant tot dan sang cac
    blog quant khac. Khong can danh sach do ai viet tay.
    """
    da_co = _mien_da_biet()
    dem: dict[str, int] = {}
    # DOC TAT CA CAC KIEU, khong chi `bai_bao`.
    #
    # Do that 30/08/2026: loc `kieu='bai_bao'` bo qua **207 ban ma_nguon (8,3
    # trieu ky tu)** va **434 ban `khac` (3 trieu)** - tuc hon mot nua kho.
    # Mot vong san 6 luot chi tim ra 33 mien va **0 mien dat**.
    # Mo ra tat ca cac kieu: **241 ung vien**, dan dau la openreview.net,
    # proceedings.mlr.press, jmlr.org, papers.nips.cc, nber.org - toan nguon
    # hoc thuat hang dau. Kho ma va trang forum trich dan rat nhieu nguon;
    # bo chung di la bo dung cho giau nhat.
    for r in SO.nhieu(
            "SELECT van_ban FROM noi_dung WHERE so_ky_tu>800 "
            "ORDER BY id DESC LIMIT 900"):
        thay = set()
        for u in re.findall(r'https?://([a-z0-9.\-]+)', r["van_ban"] or "", re.I):
            mien = u.lower().lstrip("www.")
            if mien in thay or BO_QUA_MIEN.search(mien) or _la_ha_tang(mien):
                continue
            if khoa_nha_xuat_ban(mien) in da_co:
                continue
            if mien.count(".") > 3 or len(mien) < 6:
                continue
            thay.add(mien)
        for m in thay:
            dem[m] = dem.get(m, 0) + 1
    return sorted([(m, n) for m, n in dem.items() if n >= it_nhat],
                  key=lambda x: -x[1])[:gioi_han]


#: Duoi hai cap pho bien, de `research.hangukquant.com` va
#: `hangukquant.substack.com` duoc nhan ra la CUNG mot nha xuat ban.
_DUOI_KEP = ("co.uk", "com.au", "co.jp", "com.br", "com.vn", "org.uk", "ac.uk")


def ten_goc(mien: str) -> str:
    """Ten mien DANG KY DUOC cua mot netloc. `a.b.example.com` -> `example.com`.

    Khong co no thi `research.hangukquant.com` duoc coi la nguon moi trong khi
    kho da co `hangukquant.substack.com` - cung mot nguoi viet, hai suat ngan
    sach. Da xay ra that o lan chay dau."""
    m = (mien or "").lower().strip().lstrip("www.")
    phan = m.split(".")
    if len(phan) <= 2:
        return m
    if ".".join(phan[-2:]) in _DUOI_KEP and len(phan) >= 3:
        return ".".join(phan[-3:])
    return ".".join(phan[-2:])


#: Nen tang CHO THUE cho: nguoi viet la SUBDOMAIN, khong phai ten mien goc.
#: `hangukquant.substack.com` ma quy ve `substack.com` thi ca Substack thanh
#: mot nguon duy nhat, va `research.hangukquant.com` (cung nguoi viet) lot qua
#: nhu mot nguon moi - da xay ra that o lan chay dau.
NEN_TANG_CHO_THUE = {"substack.com", "blogspot.com", "wordpress.com",
                     "github.io", "medium.com", "ghost.io", "netlify.app",
                     "tumblr.com", "typepad.com", "svbtle.com"}


def khoa_nha_xuat_ban(mien: str) -> str:
    """Ai VIET, khong phai ho o dau. Dung cho ca dat ten lan chong trung.

    `hangukquant.substack.com` -> `hangukquant`
    `research.hangukquant.com` -> `hangukquant`   (cung nguoi, khong them suat)
    `financial-hacker.com`     -> `financial-hacker`
    """
    m = (mien or "").lower().strip().lstrip("www.")
    goc = ten_goc(m)
    if goc in NEN_TANG_CHO_THUE:
        phan = [x for x in m.split(".") if x]
        con = phan[:-len(goc.split("."))]
        if con:
            return con[-1]
    return goc.split(".")[0]


def _mien_da_biet() -> set[str]:
    from nhan import nguon_bai_viet as NBV
    ra = set()
    for c in list(NBV.FEEDS.values()):
        ra.add(khoa_nha_xuat_ban(urlparse(c["url"]).netloc))
    for c in NBV.TRANG.values():
        ra.add(khoa_nha_xuat_ban(urlparse(c["seed"][0]).netloc))
    for ma, c in doc_kho().items():
        if not isinstance(c, dict) or not c.get("url"):
            continue
        ra.add(khoa_nha_xuat_ban(urlparse(c["url"]).netloc))
    ra |= {khoa_nha_xuat_ban(m) for m in NBV.FEED_HONG} | set(NBV.FEED_HONG)
    ra |= {khoa_nha_xuat_ban(m) for m in NBV.FEEDS}
    # Nha xuat ban / cong tra cuu: co feed nhung khong phai noi ai viet luat.
    ra |= {"doi", "springer", "wiley", "tandfonline", "researchgate", "ssrn",
           "sciencedirect", "jstor", "elsevier", "mql5", "zorro-project"}
    return ra


def do_thu_feed(mien: str, cho_giay: float = 12.0,
                duong: tuple = ()) -> dict | None:
    """Thu cac duong feed pho bien tren mot ten mien. Tra ho so neu dat.

    DAT nghia la: XML doc duoc, >= 3 muc, VA co dau hieu nganh trong tieu de
    hoac noi dung. Mot feed hop le ve ky thuat nhung noi ve chuyen khac thi
    khong phai nguon - no chi lam day hang doi.
    """
    from nhan import nguon_bai_viet as NBV
    for d in (duong or DUONG_FEED):
        for so_do in ("https://", "https://www."):
            url = so_do + mien.lstrip("www.") + d
            xml = NBV._lay(url, timeout=int(cho_giay))
            if not xml or "<" not in xml:
                continue
            muc = NBV.doc_feed(xml)
            if len(muc) < 3:
                continue
            chu = " ".join((m["tieu_de"] + " " + (m["van_ban"] or "")[:1500])
                           for m in muc[:8])
            diem = len(DAU_HIEU_NGANH.findall(chu))
            if diem < 3:
                return {"url": url, "so_muc": len(muc), "diem_nganh": diem,
                        "dat": False, "ly_do": "feed hop le nhung khong phai nganh"}
            day_du = sum(1 for m in muc if m.get("day_du"))
            return {"url": url, "so_muc": len(muc), "diem_nganh": diem,
                    "toan_van": day_du >= max(1, len(muc) // 3), "dat": True}
    return None


#: THU MUC BLOG cong khai. Day la nhien lieu tot hon lien ket trong bai:
#: quantocracy la mot trang TONG HOP, va trang cua no liet ke **108 blog quant**
#: duoi dang `?blog=<slug>`. Do la mot danh sach do NGUOI trong nganh duy tri -
#: dung loai nguon ta can, va no tu cap nhat.
#:
#: Lien ket bai cua no di qua `redirect.php` va duong do tra 200 rong (khong
#: theo duoc), nen ta chi lay TEN, roi doan ten mien tu ten.
THU_MUC_BLOG = {
    "quantocracy": {
        "url": "https://quantocracy.com/?blog=robot-wealth",
        "mau": r"\?blog=([a-z0-9][a-z0-9\-]{2,40})",
    },
}

#: Toi da bao nhieu ten mien DOAN cho moi ten blog. Doan cang nhieu cang ton
#: mang cho mot cau tra loi cang loang.
DOAN_MOI_TEN = 3
#: Voi ten mien DOAN thi chi thu hai duong feed pho bien nhat (do tren 27 feed
#: dang co: `/feed/` va `/rss.xml` phu gan het).
DUONG_FEED_NGAN = ("/feed/", "/rss.xml")


def slug_thu_muc(ma: str = "quantocracy") -> list[str]:
    """Ten cac blog ma mot thu muc cong khai dang theo doi."""
    from nhan import nguon_bai_viet as NBV
    c = THU_MUC_BLOG.get(ma)
    if not c:
        return []
    html = NBV._lay(c["url"], timeout=25)
    if not html:
        return []
    bo = {"about", "contact", "faqs", "privacy", "terms", "feed"}
    return sorted({s for s in re.findall(c["mau"], html, re.I) if s not in bo})


def mien_doan_tu_slug(slug: str) -> list[str]:
    """`alpha-architect` -> alphaarchitect.com, alpha-architect.com, ...substack.com

    Doan, khong phai tra cuu - nen moi cai doan deu phai qua dung bai kiem feed
    nhu moi nguon khac. Doan sai thi chet o do, khong vao kho.
    """
    lien = slug.replace("-", "")
    ra = [f"{lien}.com", f"{slug}.com", f"{lien}.substack.com"]
    return list(dict.fromkeys(ra))[:DOAN_MOI_TEN]


def _tu_thu_muc(kho: dict, bao: dict, t0: float, so_ten: int,
                ngan_sach_giay: float) -> None:
    """Lay ten tu thu muc, doan ten mien, do thu feed. Ghi nho ten DA THU."""
    da_thu = set(kho.get("_da_thu_ten", {}).get("ds", []))
    da_co = _mien_da_biet()
    try:
        ds = slug_thu_muc()
    except Exception as e:
        bao["thu_muc_loi"] = f"{type(e).__name__}: {str(e)[:80]}"
        return
    bao["thu_muc_co"] = len(ds)
    dem = 0
    for slug in ds:
        if dem >= so_ten or time.time() - t0 > ngan_sach_giay:
            break
        if slug in da_thu or re.sub(r"[^a-z0-9]+", "", slug) in \
                {re.sub(r"[^a-z0-9]+", "", x) for x in da_co}:
            continue
        dem += 1
        da_thu.add(slug)
        for mien in mien_doan_tu_slug(slug):
            if khoa_nha_xuat_ban(mien) in da_co:
                break
            try:
                ho_so = do_thu_feed(mien, duong=DUONG_FEED_NGAN)
            except Exception:
                ho_so = None
            if not ho_so or not ho_so.get("dat"):
                continue
            ma = re.sub(r"[^a-z0-9]+", "_", khoa_nha_xuat_ban(mien))[:28]
            while ma in kho:
                ma += "_x"
            kho[ma] = {
                "url": ho_so["url"], "ten": mien, "hang": "C", "loai": "blog",
                "toan_van": bool(ho_so.get("toan_van")), "trang_thai": "THU",
                "phat_hien_luc": SO.bay_gio(), "tu_thu_muc": "quantocracy",
                "diem_nganh": ho_so["diem_nganh"],
                "ghi_chu": f"tu thu muc quantocracy ('{slug}'), "
                           f"{ho_so['so_muc']} muc, diem nganh {ho_so['diem_nganh']}",
            }
            bao["them"].append(ma)
            da_co.add(khoa_nha_xuat_ban(mien))
            break
    bao["ten_da_thu"] = dem
    kho["_da_thu_ten"] = {"ds": sorted(da_thu)}


def mot_luot_tim(so_mien: int = 8, ngan_sach_giay: float = 90.0,
                 so_ten_thu_muc: int = 6) -> dict:
    """Do thu vai ten mien moi, ghi cai nao dat vao dien THU."""
    t0 = time.time()
    kho = doc_kho()
    bao = {"da_thu": 0, "them": [], "khong_dat": [], "khong_co_feed": 0}
    for mien, lan_dan in mien_ung_vien():
        if bao["da_thu"] >= so_mien or time.time() - t0 > ngan_sach_giay:
            break
        bao["da_thu"] += 1
        try:
            ho_so = do_thu_feed(mien)
        except Exception:
            ho_so = None
        if not ho_so:
            bao["khong_co_feed"] += 1
            continue
        if not ho_so.get("dat"):
            bao["khong_dat"].append({mien: ho_so.get("ly_do")})
            continue
        ma = re.sub(r"[^a-z0-9]+", "_", khoa_nha_xuat_ban(mien))[:28]
        while ma in kho:
            ma += "_x"
        kho[ma] = {
            "url": ho_so["url"], "ten": mien, "hang": "C",
            "loai": "blog", "toan_van": bool(ho_so.get("toan_van")),
            "trang_thai": "THU", "phat_hien_luc": SO.bay_gio(),
            "duoc_dan": lan_dan, "diem_nganh": ho_so["diem_nganh"],
            "ghi_chu": f"tu tim: {lan_dan} bai da thu dan sang, "
                       f"{ho_so['so_muc']} muc, diem nganh {ho_so['diem_nganh']}",
        }
        bao["them"].append(ma)
    # NGUON THU HAI: thu muc blog cong khai. Lien ket trong bai chi tim duoc
    # nhung noi ma kho HIEN CO dan sang - no khong bao gio ra khoi vong tron
    # ban dau. Thu muc thi ra duoc.
    if time.time() - t0 < ngan_sach_giay:
        _tu_thu_muc(kho, bao, t0, so_ten_thu_muc, ngan_sach_giay)

    if bao["them"] or kho.get("_da_thu_ten"):
        luu_kho(kho)
    if bao["them"]:
        SO.ghi_chi_so("vuon_nguon_them_moi", len(bao["them"]), bao)
    return bao


# ------------------------------------------------------------- THANG / GIANG
def soat_lai() -> dict:
    """Nguon dien THU da du bai -> thang `BAT` neu co ung vien, khong thi `TAT`.

    Day la cho mot nguon te CHET. Neu khong co buoc nay thi moi nguon tu tim
    duoc deu song mai va ngan sach thu thap loang dan ra vo han.
    """
    kho = doc_kho()
    if not kho:
        return {"khong_co_nguon_thu": True}
    tk = thong_ke_nguon()
    ra = {"thang": [], "giang": [], "cho_them": []}
    for ma, c in kho.items():
        if not isinstance(c, dict) or c.get("trang_thai") != "THU":
            continue
        d = tk.get("rss_" + ma) or {}
        bai = int(d.get("bai") or 0)
        if bai < HAN_THAM_DO_BAI:
            ra["cho_them"].append({ma: f"{bai}/{HAN_THAM_DO_BAI} bai"})
            continue
        if int(d.get("ung_vien") or 0) > 0:
            c["trang_thai"] = "BAT"
            c["ghi_chu"] = f"thang sau {bai} bai, {d['ung_vien']} ung vien"
            ra["thang"].append(ma)
        else:
            c["trang_thai"] = "TAT"
            c["ghi_chu"] = f"tat sau {bai} bai, 0 ung vien"
            ra["giang"].append(ma)
    if ra["thang"] or ra["giang"]:
        luu_kho(kho)
        SO.ghi_chi_so("vuon_nguon_soat_lai", len(ra["thang"]) - len(ra["giang"]), ra)
    return ra


def feed_dang_bat() -> dict[str, dict]:
    """Nguon tu tim dang duoc phep goi (THU hoac BAT) - dang giong `FEEDS`."""
    return {ma: {"url": c["url"], "hang": c.get("hang", "C"),
                 "toan_van": bool(c.get("toan_van")), "loai": c.get("loai", "blog"),
                 "ghi_chu": c.get("ghi_chu", ""), "tu_tim": True}
            for ma, c in doc_kho().items()
            if isinstance(c, dict) and c.get("url")
            and c.get("trang_thai") in ("THU", "BAT")}


if __name__ == "__main__":
    import pprint
    print("== SUAT THEO LAN ==")
    pprint.pprint(suat_lan())
    print("== CHIA NGAN SACH 600 giay ==")
    pprint.pprint(chia_ngan_sach(600))
    print("== TEN MIEN UNG VIEN ==")
    pprint.pprint(mien_ung_vien(gioi_han=20)[:20])
