# -*- coding: utf-8 -*-
"""link_nguon.py - LINK CHU DU AN DUA -> PHAN LOAI -> KE HOACH CAO LICH SU (module nay KHONG goi mang).

Chu du an 03/10/2026: *"co rat nhieu group co rat nhieu bot giao dich co lai ma ta chua cao duoc du toi co link dan,
can khai thac phan nay sau"* va *"module thao tac web ta chua dung het"*. Day la nua DAU cua day chuyen B (NGUON_NGUOI_THANG):
mot link nguoi dua vao -> biet NO LA GI, LAY BANG CACH NAO, CAN GI TU CHU DU AN, ROI moi cao (o `link_chay.py`).

## Module nay lam gi (toan ham thuan - test duoc o cloud)

  1. `tim_link` / `doc_link_rieng`   link trong doan van bat ky (ke ca tin nhan dan nguyen) + tep `link_rieng.txt`
  2. `phan_loai`                      nen tang (mql5, myfxbook, telegram, facebook...), LOAI trang, RIENG hay CONG KHAI,
                                      cach lay (`http` / `cdp` / `telethon` / `thu_cong`), can gi, `ma` on dinh (sha1 URL chuan hoa)
  3. `trich_tu_van_ban`               tin nhan dan vao -> link, id tin hieu MQL5, ten kenh Telegram, tai khoan XEM (passview),
                                      ten tep dinh kem, dem tu khoa luoi/DCA/martingale (bot song duoc phan lon la he nay)
  4. `ke_hoach` / `bao_cao_*`         thu tu uu tien (nguon co LENH that len dau), buoc bang loi thuong, ban bao cao AN TOAN (khong lo link rieng)
  5. `Nhip` / `Robots` / `phan_loai_loi` / `TrangThai`   cao LICH SU: gian cach theo ten mien, robots.txt, phan loai loi,
                                      lui theo cap so nhan, nho trang thai de noi lai - TUYET DOI khong ne chan (xem duoi)
  6. `tom_tat_cau_truc`               do cau truc mot trang (tieu de, tab, bang, form, diem cuoi XHR) de PHIEN CLOUD viet bo doc that

## Hai luat cung (chu du an: repo nay la PUBLIC)

* **Link rieng KHONG vao git.** Link moi vao nhom (t.me/+..., joinchat, discord.gg, chat.whatsapp.com, zalo.me/g/...), nhom Facebook,
  link kho tep (Drive/Mega), link co token/key trong query, link co user:pass@ -> `rieng = True`. Ban bao cao gui ve cloud chi co `ma`
  + nen tang + loai; URL va nhan tu do khong bao gio ra khoi may nha. Tep `link_rieng.txt`, `du_lieu_cao/` da nam trong `.gitignore`.
* **Khong ne chan, khong gia nguoi.** 429 / 403 / captcha / Cloudflare -> DUNG ten mien do (lui 15 phut x 2^n, toi da 6 gio; chan cam
  nghi 24 gio) va bao chu du an; khong doi UA/IP, khong thu lai dap. robots.txt cam -> khong cao (`CHAN_ROBOTS`), chu du an quyet.
  Facebook / Zalo / Discord / WhatsApp: KHONG tu dong (vi pham dieu khoan, rui ro khoa tai khoan) - chu du an dan chu hoac luu trang.
  Khong bao gio tu tai file thuc thi (.exe/.zip/.ex4...) tu link la.

## Chua lam duoc / chua do that (noi that)

* Moi duong mang chua tung chay that o cloud (cloud khong toi mql5.com, myfxbook, t.me). Phan phan loai / ke hoach / nhip / trang thai /
  tom tat HTML duoc test bang du lieu cai san; bo doc dung dinh dang trang that se viet SAU khi may nha chay `b link tham-do` va gui
  `reports/link_nguon_tham_do_*.json` ve.
* Phan loai nen tang theo mau URL: URL doi cau truc la hong; nen tang la `khac` thi van duoc tham do nhung phai qua chu du an duyet ten mien.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib import robotparser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

#: Noi chu du an dan link - bi gitignore. Dan CA TIN NHAN cung duoc: module tu tim link trong do.
FILE_LINK_RIENG = (LAB / "link_rieng.txt", LAB / "config" / "link_rieng.txt")
THU_MUC_CAO = LAB / "du_lieu_cao"                      # bi gitignore: moi thu cao ve nam day
THA_VAO = THU_MUC_CAO / "tha_vao"                      # chu du an tha tep luu tay (bao cao, .set, tin nhan) vao day
TRANG_THAI = THU_MUC_CAO / "link_nguon_trang_thai.json"
BAO_CAO_JSON = LAB / "reports" / "link_nguon_ke_hoach.json"
BAO_CAO_MD = LAB / "reports" / "link_nguon_ke_hoach.md"

#: Gian cach TOI THIEU (giay) giua hai yeu cau toi CUNG ten mien. Khoa la ten mien goc (hau to khop).
NHIP_MIEN = {
    "mql5.com": 8, "myfxbook.com": 10, "fxblue.com": 8, "tradingview.com": 6, "ctrader.com": 8,
    "darwinex.com": 8, "darwinexzero.com": 8, "github.com": 2, "githubusercontent.com": 2, "t.me": 3,
    "telegram.me": 3, "forexfactory.com": 10, "babypips.com": 8, "reddit.com": 8, "youtube.com": 8, "*": 8,
}
#: Tran yeu cau MOI NGAY cho moi ten mien (mac dinh): ngan khoang cach lan quet qua dai hoi mot ten mien
TRAN_NGAY_MIEN = 400
#: Tran yeu cau MOI LUOT chay cho moi ten mien
TRAN_LUOT_MIEN = 60

#: Ten mien duoc phep `link tham-do` qua DON tu cloud (nen tang cong khai da biet). Ten mien la: chu du an chay tay tren may nha.
TEN_MIEN_CHO_PHEP = (
    "mql5.com", "myfxbook.com", "fxblue.com", "tradingview.com", "ctrader.com", "darwinex.com", "github.com",
    "githubusercontent.com", "t.me", "forexfactory.com", "babypips.com", "reddit.com",
)

_C, _R = False, True                                    # cong khai / rieng

#: Duong dan -> loai trang, theo tung nen tang. Luat dau tien khop thang; khong khop -> `khac`.
_LUAT_DUONG = {
    "mql5": (
        (r"^/signals/\d+", "tin_hieu", _C), (r"^/signals/?$", "danh_sach_tin_hieu", _C),
        (r"^/market/product/\d+", "san_pham_market", _C), (r"^/market", "danh_sach_market", _C),
        (r"^/code/\d+", "ma_nguon", _C), (r"^/code", "danh_sach_ma_nguon", _C),
        (r"^/articles/\d+", "bai_viet", _C), (r"^/blogs/post/\d+", "blog", _C), (r"^/forum", "dien_dan", _C),
        (r"^/users/[^/]+", "nguoi_dung", _C), (r"^/channels/[^/]+", "kenh", _C),
    ),
    "myfxbook": (
        (r"^/members/[^/]+/[^/]+/\d+", "tai_khoan_cong_khai", _C), (r"^/portfolio/[^/]+/\d+", "portfolio", _C),
        (r"^/statements/\d+", "bao_cao", _C), (r"^/(?:forex-autotrade|autotrade)", "autotrade", _C),
        (r"^/(?:community|forex-forum)", "cong_dong", _C), (r"^/systems", "he_thong", _C),
    ),
    "fxblue": (
        (r"^/users/[^/]+", "tai_khoan_cong_khai", _C), (r"^/fxbook/", "tai_khoan_cong_khai", _C),
        (r"^/market", "cho_ea", _C),
    ),
    "darwinex": ((r"^/(?:invest|darwin)/", "darwin", _C),),
    "tradingview": (
        (r"^/script/", "pine_script", _C), (r"^/scripts", "danh_sach_pine", _C), (r"^/chart/", "bieu_do", _C),
        (r"^/(?:u|v|i)/", "nguoi_dung_hoac_y_tuong", _C),
    ),
    "ctrader": ((r"^/algos/", "thuat_toan", _C), (r"^/forum", "dien_dan", _C)),
}
#: (nen_tang, mau host)  - thu tu quan trong (gist truoc github)
_HOST = (
    ("mql5", r"(?:^|\.)mql5\.com$"), ("myfxbook", r"(?:^|\.)myfxbook\.com$"), ("fxblue", r"(?:^|\.)fxblue\.com$"),
    ("darwinex", r"(?:^|\.)darwinex(?:zero)?\.com$"), ("tradingview", r"(?:^|\.)tradingview\.com$"),
    ("ctrader", r"(?:^|\.)ctrader\.com$"), ("github_raw", r"(?:^|\.)(?:raw|gist)\.githubusercontent\.com$"),
    ("github", r"(?:^|\.)github\.com$"), ("telegram", r"^(?:t\.me|telegram\.(?:me|dog))$"),
    ("facebook", r"(?:^|\.)(?:facebook\.com|fb\.com|fb\.me|fb\.watch)$"),
    ("zalo", r"(?:^|\.)(?:zalo\.me|zaloapp\.com|zalo\.vn)$"),
    ("discord", r"(?:^|\.)(?:discord\.gg|discord\.com|discordapp\.com)$"),
    ("whatsapp", r"^(?:chat\.whatsapp\.com|wa\.me|(?:www\.)?whatsapp\.com)$"),
    ("youtube", r"(?:^|\.)(?:youtube\.com|youtu\.be)$"),
    ("dien_dan", r"(?:^|\.)(?:forexfactory\.com|babypips\.com|reddit\.com|redd\.it|trade2win\.com|elitetrader\.com|"
                 r"forexpeacearmy\.com|investing\.com|stocktwits\.com)$"),
    ("copy_trading", r"(?:^|\.)(?:zulutrade\.com|etoro\.com|naga\.com|mqlsignals\.com|ayondo\.com|duplitrade\.com|"
                     r"covesting\.com|tradeo\.com)$"),
    ("kho_tep", r"(?:^|\.)(?:drive\.google\.com|docs\.google\.com|mega\.nz|mega\.co\.nz|dropbox\.com|onedrive\.live\.com|"
                r"1drv\.ms|mediafire\.com|wetransfer\.com|we\.tl|sendspace\.com|4shared\.com|box\.com|sharepoint\.com|"
                r"icloud\.com|pcloud\.com|transfer\.sh)$"),
    ("rut_gon", r"^(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd|cutt\.ly|rb\.gy|shorturl\.at|s\.id|lnkd\.in|"
                r"buff\.ly|rebrand\.ly)$"),
)
_HOST_BIEN_DICH = tuple((n, re.compile(m, re.I)) for n, m in _HOST)
_LUAT_BIEN_DICH = {n: tuple((re.compile(p), l, r) for p, l, r in ds) for n, ds in _LUAT_DUONG.items()}

#: nen_tang -> (cach_lay, du_phong). `http` = GET thuong; `cdp` = Chrome chu du an da dang nhap (JS / dang nhap / chan bot);
#: `telethon` = tai khoan Telegram da dang nhap o may nha; `thu_cong` = chu du an dan chu hoac luu trang; `giai_ma` = mo link rut gon
_CACH_LAY = {
    "mql5": ("http", "cdp"), "myfxbook": ("cdp", "thu_cong"), "fxblue": ("http", "cdp"), "darwinex": ("cdp", "thu_cong"),
    "tradingview": ("http", "cdp"), "ctrader": ("http", "cdp"), "github": ("http", None), "github_raw": ("http", None),
    "telegram": ("telethon", "http"), "facebook": ("thu_cong", None), "zalo": ("thu_cong", None),
    "discord": ("thu_cong", None), "whatsapp": ("thu_cong", None), "youtube": ("khong_ho_tro", "thu_cong"),
    "dien_dan": ("cdp", "thu_cong"), "copy_trading": ("cdp", "thu_cong"), "kho_tep": ("thu_cong", None),
    "rut_gon": ("giai_ma", None), "noi_bo": ("khong_ho_tro", None), "khac": ("http", "cdp"),
}
_CAN = {
    "http": "mang", "cdp": "chrome_cdp_da_dang_nhap", "telethon": "telegram_dang_nhap_o_may_nha",
    "thu_cong": "chu_du_an_dan_chu_hoac_luu_trang", "giai_ma": "mang", "khong_ho_tro": "chua_co_bo_doc",
}
#: khoa query lo credential -> link RIENG. (`code`/`hash` bo di vi qua hay gap o link cong khai)
_KHOA_BI_MAT = {"token", "access_token", "key", "apikey", "api_key", "invite", "invitation", "auth", "password", "passwd",
                "pass", "pwd", "sig", "signature", "session", "sessionid", "sid", "secret", "otp"}
_THAM_SO_RAC = re.compile(r"^(?:utm_.*|fbclid|gclid|igshid|mc_cid|mc_eid|ref|ref_src|source|si|feature|mibextid|rdid|"
                          r"share_url|__cft__.*|__tn__|sfnsn)$", re.I)
#: nen tang chi giu vai tham so query dinh danh (phan con lai la rac theo doi)
_GIU_QUERY = {"facebook.com": {"id", "story_fbid"}, "fb.com": {"id"}, "youtube.com": {"v", "list", "channel"}}
_NHI_PHAN = (".ex4", ".ex5", ".exe", ".zip", ".rar", ".7z", ".msi", ".apk", ".dll", ".bat", ".cmd", ".ps1", ".scr", ".jar",
             ".lnk", ".iso", ".dmg", ".gz", ".tar")
_TEP_VAN_BAN = (".mq4", ".mq5", ".mqh", ".set", ".htm", ".html", ".csv", ".txt", ".json", ".pdf", ".xlsx", ".xls", ".md")

# ============================================================== 1. TIM LINK
_DUOI_BO = ".,;:!?'\"*\u2026\uff0c\u3002\uff01\uff1f\uff1b\uff1a\u3001"
_DONG_NGOAC = {")": "(", "]": "[", "}": "{", ">": "<", "\uff09": "\uff08", "\u3011": "\u3010", "\u300b": "\u300a"}
_RX_LINK = re.compile(
    r"(?i)(?<![\w@./-])((?:https?://|www\.)[^\s<>\"'`\[\]\u3000]+"
    r"|(?:t\.me|telegram\.me|telegram\.dog|discord\.gg|chat\.whatsapp\.com|zalo\.me|youtu\.be|bit\.ly|tinyurl\.com|fb\.me|wa\.me)"
    r"/[^\s<>\"'`\[\]\u3000]+)")
_RX_SCHEME = re.compile(r"(?i)^[a-z][a-z0-9+.\-]*://")


def _cat_duoi(u: str) -> str:
    """Bo dau cau / ngoac dong thua dinh o cuoi link dan trong tin nhan (giu `)` neu link co `(` cung cap)."""
    while u:
        c = u[-1]
        if c in _DUOI_BO:
            u = u[:-1]
        elif c in _DONG_NGOAC and u.count(_DONG_NGOAC[c]) < u.count(c):
            u = u[:-1]
        else:
            break
    return u


def tim_link(van_ban: str) -> list[str]:
    """Moi URL trong doan van (giu thu tu, khu trung). `www.x` va `t.me/x` khong co scheme duoc them `https://`."""
    ra, thay = [], set()
    for m in _RX_LINK.finditer(str(van_ban or "")):
        u = _cat_duoi(m.group(1))
        if len(u) < 8 or u in thay:
            continue
        thay.add(u)
        ra.append(u if _RX_SCHEME.match(u) else "https://" + u)
    return ra


#: Duoi HAI nhan pho bien (co.jp, com.tr...): `gogojungle.co.jp` phai la MOT ten mien rieng, khong gop chung moi trang `.co.jp`
#: vao mot xo nhip / nghi / tran ngay (03/10/2026, khi them dien dan Nhat / Indonesia / Tho Nhi Ky).
_DUOI_HAI_NHAN = frozenset(
    "co.jp ne.jp or.jp co.id or.id com.tr co.uk org.uk com.au co.nz com.br co.kr com.vn co.th com.cn com.sg com.my co.in "
    "com.mx com.ar co.za com.pl com.hk com.tw com.ua com.ph com.eg com.sa com.ru".split())


def mien_goc(host: str) -> str:
    """'www.mql5.com' -> 'mql5.com'. Khop hau to voi khoa NHIP_MIEN; khong co thi lay hai nhan cuoi (ba nhan neu duoi la co.jp, com.tr...)."""
    h = (host or "").lower().strip(".")
    for k in NHIP_MIEN:
        if k != "*" and (h == k or h.endswith("." + k)):
            return k
    p = h.split(".")
    if len(p) >= 3 and ".".join(p[-2:]) in _DUOI_HAI_NHAN:
        return ".".join(p[-3:])
    return ".".join(p[-2:]) if len(p) >= 2 else h


def nhip_cho(mien: str, nhip: dict | None = None) -> float:
    tb = dict(NHIP_MIEN, **(nhip or {}))
    return float(tb.get(mien_goc(mien), tb["*"]))


def chuan_hoa_url(url: str) -> str:
    """URL -> dang chuan de so sanh / lam khoa: https, bo www, bo fragment, bo tham so theo doi, sap query, bo locale cua MQL5
    (`/en/signals/1` va `/vi/signals/1` la mot), t.me/s/ten == t.me/ten. Chi cho ten khong phan biet hoa thuong (ten kenh Telegram)
    thi ha chu; ma moi vao nhom (`t.me/+AbC`) giu nguyen chu hoa."""
    u = str(url or "").strip()
    if not _RX_SCHEME.match(u):
        u = "https://" + u
    p = urlsplit(u)
    host = (p.hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    try:
        port = p.port
    except ValueError:
        port = None
    netloc = host if port in (None, 80, 443) else "%s:%d" % (host, port)
    goc = mien_goc(host)
    path = re.sub(r"/{2,}", "/", p.path or "/")
    if goc == "mql5.com":
        path = re.sub(r"^/[a-z]{2}(?=/|$)", "", path) or "/"
    if host in ("t.me", "telegram.me", "telegram.dog"):
        host = netloc = "t.me"
        path = re.sub(r"^/s/", "/", path)
        seg0 = path.strip("/").split("/", 1)[0]
        if seg0 not in ("joinchat", "c") and not seg0.startswith("+"):
            path = path.lower()
    path = path.rstrip("/") or "/"
    giu = _GIU_QUERY.get(goc)
    q = sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
               if (k in giu if giu is not None else not _THAM_SO_RAC.match(k)))
    return urlunsplit(("https", netloc, path, urlencode(q), ""))


def ma_link(url: str) -> str:
    """Khoa ngan on dinh cua link (dung trong bao cao, trang thai - thay cho URL khi link rieng)."""
    return hashlib.sha1(chuan_hoa_url(url).encode("utf-8")).hexdigest()[:10]


# ============================================================== 2. PHAN LOAI
_RX_TEN_TG = re.compile(r"^[A-Za-z][A-Za-z0-9_]{3,31}$")


def _khop_duong(nen: str, path: str) -> tuple[str, bool]:
    for rx, loai, rieng in _LUAT_BIEN_DICH.get(nen, ()):
        if rx.search(path):
            return loai, rieng
    return "khac", _C


def _telegram(path: str) -> tuple[str, bool]:
    seg = [s for s in path.split("/") if s]
    if not seg:
        return "trang_chu", _C
    a = seg[0]
    if a.startswith("+") or a == "joinchat":
        return "moi_vao_nhom", _R                              # ai co ma nay vao duoc nhom: KHONG dua len git
    if a == "c":
        return "tin_nhan_rieng", _R
    if _RX_TEN_TG.match(a):
        if a.lower().endswith("bot"):
            return "bot", _C
        return ("tin_nhan_cong_khai" if len(seg) >= 2 and seg[1].isdigit() else "kenh_cong_khai"), _C
    return "khac", _C


def _facebook(path: str) -> tuple[str, bool]:
    if path.startswith("/groups/"):
        return "nhom", _R
    if re.match(r"^/(?:share|permalink\.php|photo|story\.php|watch|reel|posts)", path) or "/posts/" in path:
        return "bai_dang", _R                                   # bai dang co the nam trong nhom kin
    return "trang", _C


def _theo_nen_tang(nen: str, path: str) -> tuple[str, bool]:
    if nen == "telegram":
        return _telegram(path)
    if nen == "facebook":
        return _facebook(path)
    if nen == "zalo":
        return ("nhom" if path.startswith("/g/") else "khac"), _R
    if nen == "discord":
        return ("moi_vao_may_chu" if "invite" in path or path.count("/") <= 1 else "kenh"), _R
    if nen == "whatsapp":
        return ("kenh" if path.startswith("/channel/") else "moi_vao_nhom_hoac_so"), (_C if path.startswith("/channel/") else _R)
    if nen == "github":
        seg = [s for s in path.split("/") if s]
        if len(seg) >= 2:
            return "kho_ma", _C
        return ("nguoi_dung" if seg else "trang_chu"), _C
    if nen == "github_raw":
        return "tep_tho", _C
    if nen == "youtube":
        return ("kenh" if re.match(r"^/(?:@|channel/|c/|user/)", path) else "video"), _C
    if nen == "kho_tep":
        return "kho_tep", _R                                    # link chia se Drive/Mega la bi mat theo mac dinh
    if nen == "rut_gon":
        return "chuyen_huong", _C
    if nen in ("dien_dan", "copy_trading"):
        return nen, _C
    return _khop_duong(nen, path)


_RX_ID = {
    "tin_hieu": re.compile(r"^/signals/(\d+)"), "ma_nguon": re.compile(r"^/code/(\d+)"),
    "san_pham_market": re.compile(r"^/market/product/(\d+)"), "bai_viet": re.compile(r"^/articles/(\d+)"),
    "tai_khoan_cong_khai": re.compile(r"/(\d+)(?:/|$)"), "portfolio": re.compile(r"/(\d+)(?:/|$)"),
    "kho_ma": re.compile(r"^/([^/]+/[^/]+)"), "pine_script": re.compile(r"^/script/([^/]+)"),
    "kenh_cong_khai": re.compile(r"^/([^/]+)"), "tin_nhan_cong_khai": re.compile(r"^/([^/]+)"),
}


def _la_noi_bo(host: str) -> bool:
    h = host.strip("[]").lower()
    if h in ("localhost", "") or h.endswith((".local", ".internal", ".lan", ".home")):
        return True
    try:
        ipaddress.ip_address(h)
    except ValueError:
        return False
    return True                                                  # IP tran (cong cong hay noi bo) khong bao gio duoc tham do


def phan_loai(url: str, nhan: str = "") -> dict:
    """Mot link -> {ma, url (chuan hoa), nen_tang, loai, rieng, ly_do_rieng, cach_lay, du_phong, can, id?, tab?, nhan}.

    `rieng` = link nay khong duoc roi may nha (vao git / thu gui di). `cach_lay` la cach lay TOT NHAT; `du_phong` neu cach do
    that bai (khong tu dong chuyen: chi de ke hoach noi). Link toi dia chi noi bo / IP -> `noi_bo`, khong bao gio tham do."""
    goc = str(url or "").strip()
    p0 = urlsplit(goc if _RX_SCHEME.match(goc) else "https://" + goc)
    norm = chuan_hoa_url(goc)
    p = urlsplit(norm)
    host, path = p.hostname or "", p.path
    ly_rieng = ""
    if _la_noi_bo(host):
        nen, loai, rieng = "noi_bo", "dia_chi_noi_bo", _R
        ly_rieng = "dia chi noi bo / IP"
    else:
        nen = next((n for n, rx in _HOST_BIEN_DICH if rx.search(host)), "khac")
        loai, rieng = _theo_nen_tang(nen, path)
        if rieng:
            ly_rieng = "link %s %s la rieng tu" % (nen, loai)
        duoi = path.lower()
        if duoi.endswith(_NHI_PHAN) or (nen == "khac" and duoi.endswith(_TEP_VAN_BAN)):
            loai = "tep_truc_tiep"                               # tep thuc thi / nen khong bao gio tu tai: chu du an tai tay
    if p0.username or p0.password:
        rieng, ly_rieng = _R, "co user:pass trong link"
    khoa = {k.lower() for k, _ in parse_qsl(p0.query)} & _KHOA_BI_MAT
    if khoa:
        rieng, ly_rieng = _R, "tham so bi mat trong link (%s)" % ",".join(sorted(khoa))
    cach, du_phong = _CACH_LAY.get(nen, _CACH_LAY["khac"])
    if loai == "tep_truc_tiep":
        cach, du_phong = "thu_cong", None
    if nen == "telegram" and loai in ("moi_vao_nhom", "tin_nhan_rieng"):
        cach, du_phong = "telethon", None                       # http khong thay nhom kin
    ra = {"ma": hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10], "url": norm, "nen_tang": nen, "loai": loai,
          "rieng": bool(rieng), "ly_do_rieng": ly_rieng, "cach_lay": cach, "du_phong": du_phong,
          "can": [c for c in dict.fromkeys(_CAN[x] for x in (cach, du_phong) if x)], "nhan": str(nhan or "")[:120]}
    rx = _RX_ID.get(loai)
    m = rx.search(path) if rx else None
    if m:
        ra["id"] = m.group(1)
    t = re.search(r"!?tab=(\w+)", p0.fragment or "")
    if t:
        ra["tab"] = t.group(1).lower()
    if path.lower().endswith(_NHI_PHAN):
        ra["nguy_hiem"] = True
    return ra


def loai_tep(ten: str) -> str:
    """Ten tep dinh kem -> loai: bao_cao / ea_nguon / ea_bien_dich / tham_so / nen / anh / khac. (Quyet dinh co tai ve khong nam o `tai_duoc`.)"""
    t = str(ten or "").lower()
    ext = t[t.rfind("."):] if "." in t else ""
    if ext in (".htm", ".html", ".csv", ".xlsx", ".xls", ".pdf") and re.search(
            r"report|statement|history|lich.?su|bao.?cao|trade|deal|order|lenh", t):
        return "bao_cao"
    if ext in (".htm", ".html", ".csv", ".xlsx", ".xls"):
        return "bao_cao_co_the"
    return {".mq4": "ea_nguon", ".mq5": "ea_nguon", ".mqh": "ea_nguon", ".ex4": "ea_bien_dich", ".ex5": "ea_bien_dich",
            ".set": "tham_so", ".zip": "nen", ".rar": "nen", ".7z": "nen", ".png": "anh", ".jpg": "anh",
            ".jpeg": "anh", ".txt": "van_ban", ".json": "du_lieu"}.get(ext, "khac")


def tai_duoc(ten: str, kich_thuoc: int = 0, toi_da: int = 5_000_000) -> tuple[bool, str]:
    """Tep dinh kem nao duoc tai ve may nha. CHI van ban / bao cao / EA nguon + EA bien dich (ex4/ex5 chi LUU, MT5 moi chay).
    Khong tai tep thuc thi / nen / qua lon: tra ly do de bao cao."""
    t = str(ten or "").lower()
    ext = t[t.rfind("."):] if "." in t else ""
    if ext in _NHI_PHAN and ext not in (".ex4", ".ex5"):
        return False, "tep thuc thi/nen (%s): khong tu tai, chu du an tai tay neu tin" % ext
    if kich_thuoc and kich_thuoc > toi_da:
        return False, "qua lon (%d byte)" % kich_thuoc
    if loai_tep(ten) in ("anh", "khac"):
        return False, "loai tep khong can cho nghien cuu"
    return True, ""


# ---------------------------------------------------------------- doc `link_rieng.txt`
def doc_link_rieng(duong=None) -> list[dict]:
    """Tat ca link trong `link_rieng.txt` (hoac `duong`): dan tin nhan nguyen van cung duoc. Khu trung theo `ma`, giu thu tu.
    Dong bat dau bang `#` la ghi chu. Phan chu cung dong voi link thanh `nhan` (chi o may nha, khong vao bao cao gui di)."""
    tep = [Path(duong)] if duong else [d for d in FILE_LINK_RIENG if d.is_file()]
    muc, da = [], set()
    for t in tep:
        try:
            noi_dung = t.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for dong in noi_dung.splitlines():
            if dong.lstrip().startswith("#"):
                continue
            for u in tim_link(dong):
                m = phan_loai(u, nhan=re.sub(r"\s+", " ", dong.replace(u, "").strip(" -:|\t"))[:120])
                if m["ma"] not in da:
                    da.add(m["ma"])
                    muc.append(m)
    return muc


def them_link_rieng(van_ban: str, duong=None) -> list[dict]:
    """Them link trong `van_ban` vao `link_rieng.txt` (bo qua cai da co). Tra danh sach link MOI (da phan loai)."""
    dich = Path(duong) if duong else FILE_LINK_RIENG[0]
    co = {m["ma"] for m in doc_link_rieng(duong)}
    moi = []
    for u in tim_link(van_ban):
        m = phan_loai(u)
        if m["ma"] in co:
            continue
        co.add(m["ma"])
        moi.append(m)
    if moi:
        dich.parent.mkdir(parents=True, exist_ok=True)
        with dich.open("a", encoding="utf-8") as f:
            for m in moi:
                f.write(m["url"] + "\n")
    return moi


# ============================================================== 3. TRICH TU VAN BAN
_TU_KHOA = {
    "luoi": r"\bgrid\w*|\blu[o\u01a1]\u1edb?i\b|\bl\u01b0\u1edbi\b",
    "dca": r"\bdca\b|\baverag\w*|trung\s*b[i\u00ec]nh\s*gi[a\u00e1]|nh[o\u1ed3]i\s*l[e\u1ec7]nh",
    "martingale": r"\bmartingale\b|g[a\u1ea5]p\s*th[e\u1ebf]p",
    "hedge": r"\bhedg\w*|kh[o\u00f3]a\s*l[e\u1ec7]nh|kh\u00f3a\s*l\u1ec7nh",
    "scalp": r"\bscalp\w*",
    "khong_sl": r"\bno\s*(?:sl|stop\s*loss)\b|\bkh[o\u00f4]ng\s*sl\b",
}
_TU_KHOA_BD = {k: re.compile(v, re.I) for k, v in _TU_KHOA.items()}
_RX_TEN_TEP = re.compile(r"(?i)\b([\w\-. ()\[\]]{1,80}\.(?:htm|html|csv|xlsx|xls|pdf|mq4|mq5|mqh|ex4|ex5|set|zip|rar|7z|txt|json))\b")
_RX_SO_LOGIN = re.compile(r"\d{6,}")
_RX_AT = re.compile(r"(?<![\w.])@([A-Za-z][A-Za-z0-9_]{4,31})\b")


def trich_tu_van_ban(van_ban: str, giu_bi_mat: bool = False) -> dict:
    """Tin nhan / bai dan vao -> cac manh dung duoc. KHONG goi mang, KHONG ghi gi.

    `tai_khoan_xem` luon da AN (ma bam + server + co_mat_khau); mat khau that chi tra ve trong `tai_khoan_xem_tho` khi
    `giu_bi_mat=True` (CLI may nha, ngay sau do cat vao `config/passview.json` bi gitignore - xem `passview.luu`)."""
    vb = str(van_ban or "")
    link = [phan_loai(u) for u in tim_link(vb)]
    thay, uniq = set(), []
    for m in link:
        if m["ma"] not in thay:
            thay.add(m["ma"])
            uniq.append(m)
    tg = {m["id"] for m in uniq if m["nen_tang"] == "telegram" and m["loai"] in ("kenh_cong_khai", "tin_nhan_cong_khai")
          and m.get("id")}
    goi_y = sorted({n.lower() for n in _RX_AT.findall(vb)} - tg) if re.search(r"(?i)telegram|\bt\.me\b|\btele\b|\btg\b", vb) else []
    try:
        from nhan import passview as PV
        tho = PV.boc_tai_khoan(vb)
    except Exception:
        tho = []
    kq = {
        "so_ky_tu": len(vb), "link": uniq,
        "mql5_tin_hieu": sorted({int(m["id"]) for m in uniq if m["nen_tang"] == "mql5" and m["loai"] == "tin_hieu" and m.get("id")}),
        "telegram_cong_khai": sorted(tg), "telegram_goi_y": goi_y[:30],
        "tai_khoan_xem": [{"ma": hashlib.sha1(("%s|%s" % (t["login"], t["server"])).encode()).hexdigest()[:8],
                           "server": t["server"], "co_mat_khau": bool(t.get("mat_khau"))} for t in tho],
        "tep": sorted({(loai_tep(n), n.strip()) for n in _RX_TEN_TEP.findall(vb)})[:40],
        "tu_khoa": {k: len(rx.findall(vb)) for k, rx in _TU_KHOA_BD.items() if rx.search(vb)},
    }
    # Ten bao cao MT4/MT5 hay mang LOGIN trong ten (ReportHistory-12345678.html): ban gui di che chuoi so tu 6 chu so tro len
    tep_tho = kq["tep"]
    kq["tep"] = [{"loai": a, "ten": _RX_SO_LOGIN.sub("<so>", b)} for a, b in tep_tho]
    if giu_bi_mat:
        kq["tai_khoan_xem_tho"] = tho
        kq["tep_tho"] = [{"loai": a, "ten": b} for a, b in tep_tho]
    return kq


# ============================================================== 4. KE HOACH
#: uu tien: nguon co TUNG LENH that / ma nguon len dau (muc tieu: lich su lenh -> hieu luat -> lam lai)
_UU_TIEN = {
    ("mql5", "tin_hieu"): 10, ("myfxbook", "tai_khoan_cong_khai"): 10, ("myfxbook", "portfolio"): 12,
    ("myfxbook", "bao_cao"): 10, ("fxblue", "tai_khoan_cong_khai"): 11, ("darwinex", "darwin"): 14,
    ("telegram", "kenh_cong_khai"): 20, ("telegram", "moi_vao_nhom"): 20, ("telegram", "tin_nhan_rieng"): 20,
    ("telegram", "tin_nhan_cong_khai"): 21, ("github", "kho_ma"): 22, ("mql5", "ma_nguon"): 23,
    ("mql5", "san_pham_market"): 24, ("ctrader", "thuat_toan"): 25, ("tradingview", "pine_script"): 26,
    ("rut_gon", "chuyen_huong"): 5,           # 1 yeu cau chuyen huong re nhat, va cho biet dich den that (co the la tai khoan cong khai)
}
_THU_TU_CACH = {"http": 0, "giai_ma": 0, "cdp": 1, "telethon": 2, "thu_cong": 3, "khong_ho_tro": 4}
_TEN_NEN = {"mql5": "MQL5", "myfxbook": "Myfxbook", "fxblue": "FX Blue", "darwinex": "Darwinex", "tradingview": "TradingView",
            "ctrader": "cTrader", "github": "GitHub", "github_raw": "GitHub", "telegram": "Telegram", "facebook": "Facebook",
            "zalo": "Zalo", "discord": "Discord", "whatsapp": "WhatsApp", "youtube": "YouTube", "dien_dan": "dien dan",
            "copy_trading": "copy-trading", "kho_tep": "kho tep (Drive/Mega...)", "rut_gon": "link rut gon",
            "noi_bo": "dia chi noi bo", "khac": "trang khac"}
_NHAN_CACH = {"http": "tu dong duoc ngay (GET lich su, ~vai giay/trang)", "giai_ma": "link rut gon: mo 1 lan de biet dich den",
              "cdp": "can Chrome da dang nhap (cong 9224) - trang JS / bi chan bot",
              "telethon": "can dang nhap Telegram o may nha (ban phai la thanh vien nhom kin)",
              "thu_cong": "KHONG tu dong duoc: ban dan chu / luu trang / tai tep vao du_lieu_cao/tha_vao/",
              "khong_ho_tro": "chua co bo doc"}
_BUOC = {
    "http": ["kiem robots.txt + nhip cho ten mien", "tai trang (GET thuong, 1 yeu cau/ nhip)", "tom tat cau truc trang -> bao cao",
             "neu la tin hieu/tai khoan co lich su: tim bang lenh (tab lich su) -> luu lenh -> boc_lich_su"],
    "cdp": ["noi Chrome (cong 9224) da dang nhap", "mo tab, doc trang + ghi TEN duong XHR (khong ghi gia tri)",
            "tom tat cau truc -> bao cao", "neu co bang lenh: luu lenh -> boc_lich_su"],
    "telethon": ["dang nhap Telegram o may nha (mot lan, ma SMS)", "liet ke nhom da tham gia", "doc tin nhan moi (khong tu vao nhom)",
                 "lay link/EA/tai khoan xem/bao cao dinh kem (tep nho, khong tai thuc thi)"],
    "thu_cong": ["chu du an dan chu tin nhan vao `link_rieng.txt` hoac luu trang/tep vao du_lieu_cao/tha_vao/",
                 "`b link thu-muc` doc: link, tai khoan xem, bao cao lenh"],
    "giai_ma": ["mo link rut gon 1 lan (HEAD), phan loai lai link dich"],
    "khong_ho_tro": ["chua co bo doc cho loai nay - ghi lai, khong lam gi"],
}
_GHI_CHU = {
    ("mql5", "tin_hieu"): "trang tin hieu: lay tab lich su LENH (tung lenh) - cac phien truoc moi lay duong von, chua co lenh",
    ("myfxbook", "tai_khoan_cong_khai"): "lich su giao dich cong khai (bang + xuat CSV neu co); site hay chan bot -> uu tien Chrome da dang nhap",
    ("telegram", "moi_vao_nhom"): "link moi RIENG: khong tu vao nhom. Ban vao nhom bang app Telegram, may nha chi DOC nhom da co trong tai khoan",
    ("facebook", "nhom"): "nhom Facebook: tu dong hoa vi pham dieu khoan va co the khoa tai khoan - ban dan chu / luu trang",
    ("github", "kho_ma"): "tim file .mq5/.set/README: ma nguon EA mo (ban chu y giay phep)",
}


def _uu_tien(m: dict) -> int:
    return _UU_TIEN.get((m["nen_tang"], m["loai"]), 30)


def ke_hoach(muc: list[dict], tt: "TrangThai | None" = None) -> list[dict]:
    """Danh sach link -> ke hoach co thu tu: cach `http` truoc (chay ngay), roi cdp, telegram, thu cong; trong cung cach thi nguon co
    LENH that truoc. Moi muc co `buoc` (loi thuong), `nhip_giay`, `trang_thai` (tu `TrangThai` neu co)."""
    ra = []
    for m in muc:
        host = urlsplit(m["url"]).hostname or ""
        e = dict(m, uu_tien=_uu_tien(m), nhip_giay=nhip_cho(host), buoc=list(_BUOC.get(m["cach_lay"], [])),
                 trang_thai=tt.trang_thai(m["ma"]) if tt else "CHUA_LAM")
        gc = _GHI_CHU.get((m["nen_tang"], m["loai"]))
        if gc:
            e["ghi_chu"] = gc
        ra.append(e)
    ra.sort(key=lambda e: (_THU_TU_CACH.get(e["cach_lay"], 9), e["uu_tien"], e["nen_tang"], e["ma"]))
    return ra


def _dem(kh: list[dict], khoa: str) -> dict:
    d: dict = {}
    for e in kh:
        d[e[khoa]] = d.get(e[khoa], 0) + 1
    return dict(sorted(d.items(), key=lambda x: -x[1]))


def bao_cao_an_toan(kh: list[dict], toi_da_muc: int = 400) -> dict:
    """Ban bao cao DUOC PHEP roi may nha / vao git: link rieng chi con `ma` + nen tang + loai (khong URL, khong nhan)."""
    muc = []
    for e in kh[:toi_da_muc]:
        r = {k: e[k] for k in ("ma", "nen_tang", "loai", "rieng", "cach_lay", "du_phong", "uu_tien", "trang_thai", "nhip_giay")
             if k in e}
        if not e["rieng"]:
            r["url"] = e["url"]
        muc.append(r)
    return {"tong": len(kh), "rieng": sum(1 for e in kh if e["rieng"]), "theo_cach_lay": _dem(kh, "cach_lay"),
            "theo_nen_tang": _dem(kh, "nen_tang"), "theo_trang_thai": _dem(kh, "trang_thai"),
            "bi_cat": max(0, len(kh) - toi_da_muc), "muc": muc}


def bao_cao_van_ban(kh: list[dict]) -> str:
    """Bao cao bang LOI THUONG (khong thuat ngu) cho chu du an: bao nhieu link, cai nao chay duoc ngay, cai nao can gi tu ban."""
    if not kh:
        return ("CHUA CO LINK NAO.\n  Dan link (hoac dan nguyen tin nhan) vao tep `link_rieng.txt` o thu muc lab/ tren may nha, "
                "hoac chay: b link them \"<link>\"\n  Tep nay khong bao gio len GitHub.")
    d = {}
    for e in kh:
        d.setdefault(e["cach_lay"], []).append(e)
    dong = ["LINK CUA CHU DU AN: %d link (%d link RIENG TU - khong bao gio len GitHub)" % (len(kh), sum(1 for e in kh if e["rieng"]))]
    for cach in ("http", "giai_ma", "cdp", "telethon", "thu_cong", "khong_ho_tro"):
        ds = d.get(cach)
        if not ds:
            continue
        nen = ", ".join("%s x%d" % (_TEN_NEN.get(n, n), c) for n, c in _dem(ds, "nen_tang").items())
        dong.append("  - %2d link %s\n      (%s)" % (len(ds), _NHAN_CACH[cach], nen))
    can = []
    if d.get("telethon"):
        can.append("dang nhap Telegram tren may nha mot lan; nhom kin thi tu vao nhom bang app (module khong tu vao)")
    if d.get("cdp"):
        can.append("mo Chrome o che do CDP (cong 9224) va dang nhap san cac trang can dang nhap")
    if d.get("thu_cong"):
        can.append("voi Facebook/Zalo/Discord/kho tep: dan chu tin nhan vao link_rieng.txt hoac bo tep vao du_lieu_cao/tha_vao/")
    if can:
        dong.append("BAN CAN LAM:")
        dong += ["  * " + c for c in can]
    chua = sum(1 for e in kh if e["trang_thai"] == "CHUA_LAM")
    dong.append("TRANG THAI: %d/%d link chua lam. Chay `b link chay` de tham do mau (khong cao hang loat)." % (chua, len(kh)))
    return "\n".join(dong)


def _ghi_gioi_han(duong: Path, noi_dung: str, toi_da: int = 38_000) -> None:
    duong.parent.mkdir(parents=True, exist_ok=True)
    duong.write_text(noi_dung[:toi_da], encoding="utf-8")


def ghi_bao_cao(kh: list[dict], duong_json=None, duong_md=None) -> dict:
    """Ghi `reports/link_nguon_ke_hoach.json` + `.md` (chi ban an toan, <= 38.000 ky tu moi tep de duoc gui ve cloud)."""
    bc = bao_cao_an_toan(kh)
    j = json.dumps(bc, ensure_ascii=False, indent=1)
    while len(j) > 38_000 and bc["muc"]:
        bc["muc"] = bc["muc"][:max(0, len(bc["muc"]) // 2)]
        bc["bi_cat"] = bc["tong"] - len(bc["muc"])
        j = json.dumps(bc, ensure_ascii=False, indent=1)
    _ghi_gioi_han(Path(duong_json) if duong_json else BAO_CAO_JSON, j)
    _ghi_gioi_han(Path(duong_md) if duong_md else BAO_CAO_MD, bao_cao_van_ban(kh) + "\n")
    return bc


# ============================================================== 5. LICH SU (nhip, robots, loi, trang thai)
class HetNhip(RuntimeError):
    """Het tran yeu cau trong luot nay cho mot ten mien: dung ten mien do, de luot sau."""


class Nhip:
    """Gian cach toi thieu giua hai yeu cau toi cung ten mien. Dong ho / ham ngu duoc tiem vao de test khong phai cho that."""

    def __init__(self, dong_ho=time.monotonic, ngu=time.sleep, nhip: dict | None = None, tran_luot: int = TRAN_LUOT_MIEN):
        self._dh, self._ngu = dong_ho, ngu
        self.nhip = dict(NHIP_MIEN, **(nhip or {}))
        self.tran_luot = tran_luot
        self._cuoi: dict[str, float] = {}
        self._dem: dict[str, int] = {}
        self.tong_cho = 0.0

    def doi(self, host: str, toi_thieu: float | None = None) -> float:
        """Cho cho du gian cach roi ghi nhan yeu cau. `toi_thieu` = Crawl-delay cua robots.txt neu lon hon nhip mac dinh."""
        mien = mien_goc(host)
        if self._dem.get(mien, 0) >= self.tran_luot:
            raise HetNhip("het %d yeu cau/luot cho %s" % (self.tran_luot, mien))
        gian = max(float(self.nhip.get(mien, self.nhip["*"])), float(toi_thieu or 0))
        cho = 0.0
        if mien in self._cuoi:
            cho = max(0.0, self._cuoi[mien] + gian - self._dh())
            if cho > 0:
                self._ngu(cho)
        self._cuoi[mien] = self._dh()
        self._dem[mien] = self._dem.get(mien, 0) + 1
        self.tong_cho += cho
        return cho

    def da_goi(self, host: str) -> int:
        return self._dem.get(mien_goc(host), 0)


class Robots:
    """robots.txt theo RFC 9309: 2xx -> theo tep; 4xx -> khong co robots = duoc phep; 5xx / loi mang -> KHONG cao luot nay.
    `lay(url) -> (status | None, text, loi)` duoc tiem vao (that: `link_chay.lay_http`). Bo nho dem theo ten mien, het han sau `ttl`."""

    def __init__(self, lay, ua: str = "TheBrainLab", ttl: float = 6 * 3600, dong_ho=time.time):
        self._lay, self.ua, self.ttl, self._dh = lay, ua, ttl, dong_ho
        self._kho: dict[str, tuple] = {}

    def _nap(self, url: str):
        p = urlsplit(url)
        goc = "%s://%s" % (p.scheme or "https", p.netloc)
        k = self._kho.get(goc)
        if k and k[0] > self._dh():
            return k
        status, text, loi = self._lay(goc + "/robots.txt")
        if status is not None and 200 <= status < 300:
            rp = robotparser.RobotFileParser()
            rp.parse(str(text or "").splitlines())
            k = (self._dh() + self.ttl, rp, "")
        elif status is not None and 400 <= status < 500:
            k = (self._dh() + self.ttl, None, "")
        else:
            k = (self._dh() + 600, None, "khong doc duoc robots.txt (%s): khong cao luot nay" % (status or loi or "loi mang"))
        self._kho[goc] = k
        return k

    def cho_phep(self, url: str) -> tuple[bool, str]:
        _, rp, loi = self._nap(url)
        if loi:
            return False, loi
        if rp is None:
            return True, ""
        if rp.can_fetch(self.ua, url):
            return True, ""
        return False, "robots.txt cam duong dan nay"

    def crawl_delay(self, url: str) -> float | None:
        _, rp, _ = self._nap(url)
        try:
            d = rp.crawl_delay(self.ua) if rp is not None else None
        except Exception:
            d = None
        return float(d) if d else None


_DAU_HIEU_CHAN = ("just a moment", "cf-chl", "cf_chl", "attention required", "captcha", "are you a robot", "verify you are human",
                  "access denied", "unusual traffic", "ddos protection", "checking your browser", "enable javascript and cookies")


def phan_loai_loi(status, text: str = "", loi: str = "") -> str:
    """OK / CHAN_TAN_SUAT (429) / CHAN_CAM (401/403 hoac trang Cloudflare / captcha) / HET_TRANG (404/410) / LOI_MAY_CHU (5xx) / LOI_MANG."""
    if loi or status is None:
        return "LOI_MANG"
    s = int(status)
    if s == 429:
        return "CHAN_TAN_SUAT"
    if s in (401, 403, 451):
        return "CHAN_CAM"
    if s in (404, 410):
        return "HET_TRANG"
    if s >= 500:
        return "LOI_MAY_CHU"
    if 200 <= s < 400:
        dau = str(text or "")[:6000].lower()
        if any(k in dau for k in _DAU_HIEU_CHAN):
            return "CHAN_CAM"                                    # trang 200 nhung la man chan bot
        return "OK"
    return "LOI_MAY_CHU"


def nghi_sau_loi(ket_qua: str, so_loi: int) -> float | None:
    """Giay nghi truoc khi thu lai (None = khong thu lai tu dong). Lui theo cap so nhan, KHONG bao gio tim cach ne."""
    n = max(1, int(so_loi))
    if ket_qua == "CHAN_TAN_SUAT":
        return float(min(6 * 3600, 900 * 2 ** (n - 1)))
    if ket_qua in ("LOI_MAY_CHU", "LOI_MANG"):
        return float(min(2 * 3600, 300 * 2 ** (n - 1)))
    if ket_qua == "CHAN_CAM":
        return 24 * 3600.0
    if ket_qua == "CHAN_ROBOTS":
        return 7 * 24 * 3600.0
    if ket_qua == "HET_TRANG":
        return 30 * 24 * 3600.0
    return 0.0


def _gio_text(t: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(t))


class TrangThai:
    """Trang thai cao NOI LAI duoc: moi link mot muc, moi ten mien mot muc (nghi / dem yeu cau trong ngay). Ghi nguyen tu."""

    def __init__(self, duong=None, dong_ho=time.time):
        self.duong = Path(duong) if duong else TRANG_THAI
        self.dh = dong_ho
        self.d = self._doc()

    def _doc(self) -> dict:
        try:
            d = json.loads(self.duong.read_text(encoding="utf-8"))
            if isinstance(d, dict) and isinstance(d.get("link"), dict) and isinstance(d.get("mien"), dict):
                return d
        except (OSError, ValueError):
            pass
        return {"phien_ban": 1, "link": {}, "mien": {}}

    def luu(self) -> None:
        self.duong.parent.mkdir(parents=True, exist_ok=True)
        tam = self.duong.with_name(self.duong.name + ".tmp")
        tam.write_text(json.dumps(self.d, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tam, self.duong)

    def trang_thai(self, ma: str) -> str:
        return self.d["link"].get(ma, {}).get("ket_qua", "CHUA_LAM")

    def _hom_nay(self) -> str:
        return time.strftime("%Y-%m-%d", time.localtime(self.dh()))

    def so_hom_nay(self, mien: str) -> int:
        m = self.d["mien"].get(mien_goc(mien), {})
        return int(m.get("so_hom_nay", 0)) if m.get("ngay") == self._hom_nay() else 0

    def tinh_yeu_cau(self, mien: str) -> None:
        mien = mien_goc(mien)
        m = self.d["mien"].setdefault(mien, {"so_loi_lien_tiep": 0, "cam_den": 0})
        h = self._hom_nay()
        if m.get("ngay") != h:
            m["ngay"], m["so_hom_nay"] = h, 0
        m["so_hom_nay"] += 1

    def thu_duoc(self, ma: str, host: str, tran_ngay: int = TRAN_NGAY_MIEN) -> tuple[bool, str]:
        """(duoc thu luc nay?, ly do neu khong). Ten mien dang nghi / link dang cho thu lai / het tran ngay -> khong."""
        now, mien = self.dh(), mien_goc(host)
        m = self.d["mien"].get(mien, {})
        if m.get("cam_den", 0) > now:
            return False, "ten mien %s nghi den %s (%s)" % (mien, _gio_text(m["cam_den"]), m.get("ly_do", ""))
        if self.so_hom_nay(mien) >= tran_ngay:
            return False, "het %d yeu cau/ngay cho %s" % (tran_ngay, mien)
        lk = self.d["link"].get(ma, {})
        if lk.get("thu_lai_sau", 0) > now:
            return False, "link cho thu lai den %s (%s)" % (_gio_text(lk["thu_lai_sau"]), lk.get("ket_qua", ""))
        return True, ""

    def ghi(self, ma: str, host: str, ket_qua: str, **them) -> dict:
        """Ghi ket qua mot lan thu. Loi -> dat gio thu lai; chan tan suat / chan cam -> ca TEN MIEN nghi (khong chi link)."""
        now, mien = self.dh(), mien_goc(host)
        lk = self.d["link"].setdefault(ma, {"so_loi": 0})
        m = self.d["mien"].setdefault(mien, {"so_loi_lien_tiep": 0, "cam_den": 0})
        lk.update(them)
        lk["ket_qua"], lk["lan_cuoi"], lk["mien"] = ket_qua, int(now), mien
        if ket_qua in ("OK", "XONG"):
            lk["so_loi"], lk["thu_lai_sau"], m["so_loi_lien_tiep"] = 0, 0, 0
        else:
            lk["so_loi"] = lk.get("so_loi", 0) + 1
            m["so_loi_lien_tiep"] = m.get("so_loi_lien_tiep", 0) + 1
            nghi = nghi_sau_loi(ket_qua, lk["so_loi"])
            lk["thu_lai_sau"] = int(now + nghi) if nghi else 0
            if ket_qua in ("CHAN_TAN_SUAT", "CHAN_CAM") and nghi:
                m["cam_den"], m["ly_do"] = int(now + nghi), ket_qua
        self.luu()
        return lk


# ============================================================== 6. TOM TAT CAU TRUC TRANG (tham do)
_RX_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_RX_SO_DAI = re.compile(r"\d{9,}")
_RX_DIEM_CUOI = re.compile(
    r"""["'`]((?:https?:)?//[A-Za-z0-9.\-]+)?(/(?:api|ajax|json|rest|v\d|data|handler|get|load|signals?|history|statistics|chart|"""
    r"""export|trades?|orders?|deals?)[A-Za-z0-9_\-./{}$]{0,120}(?:\?[A-Za-z0-9_\-=&{}$%.]{0,80})?)["'`]""")
_RX_GOI_MANG = re.compile(
    r"""(?:fetch|\$\.(?:get|post|getJSON|ajax)|axios\.(?:get|post)|\.open)\(\s*(?:\{[^}]*?url\s*:\s*)?["'`]([^"'`\s]{1,200})["'`]""")


def _bo_pii(s: str, toi_da: int = 60) -> str:
    s = _RX_EMAIL.sub("<email>", str(s))
    return _RX_SO_DAI.sub("<so_dai>", re.sub(r"\s+", " ", s).strip())[:toi_da]


def rut_diem_cuoi(url: str) -> str:
    """URL goi mang -> duong dan + TEN tham so (khong gia tri: gia tri co the la token / ma phien)."""
    u = str(url or "").strip()
    try:
        p = urlsplit(u)
    except ValueError:
        return _bo_pii(u, 120)
    q = "&".join("%s=" % k for k, _ in parse_qsl(p.query, keep_blank_values=True))
    dich = ("%s://%s" % (p.scheme, p.netloc) if p.netloc else "") + p.path
    return _bo_pii(dich + ("?" + q if q else ""), 160)


class _Tham(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tieu_de, self.muc, self.tab, self.bang, self.form = "", [], [], [], []
        self.script_nguon, self.script_json, self.diem_cuoi, self.meta, self.link_ra = [], [], [], {}, []
        self._buf = None
        self._loai_buf = ""
        self._bang_dang, self._hang, self._form_dang = [], None, None
        self._a = None
        self._script = None
        self.so_the = 0

    def _bat(self, loai):
        self._buf, self._loai_buf = [], loai

    def _ket(self) -> str:
        t = _bo_pii("".join(self._buf or []), 80)
        self._buf, self._loai_buf = None, ""
        return t

    def handle_starttag(self, tag, attrs):
        self.so_the += 1
        a = {k: (v or "") for k, v in attrs}
        if tag == "title":
            self._bat("title")
        elif tag in ("h1", "h2", "h3"):
            self._bat(tag)
        elif tag == "a":
            href = a.get("href", "")
            cl = " ".join((a.get("class", ""), a.get("role", ""), a.get("id", ""))).lower()
            la_tab = "tab" in cl or "tab=" in href or "#!" in href or a.get("role") == "tab"
            self._a = (href, la_tab)
            if la_tab and self._buf is None:
                self._bat("tab")
            if href.startswith(("http://", "https://")):
                self.link_ra.append(href)
        elif tag == "table":
            self.bang.append({"tieu_de": None, "mau": [], "so_hang": 0})
            self._bang_dang.append(self.bang[-1])
        elif tag == "tr" and self._bang_dang:
            self._hang = {"o": [], "co_th": False}
        elif tag in ("td", "th") and self._hang is not None:
            if tag == "th":
                self._hang["co_th"] = True
            self._bat("o")
        elif tag == "form":
            self._form_dang = {"duong": rut_diem_cuoi(a.get("action", "")), "cach": (a.get("method") or "get").lower(), "o": []}
            self.form.append(self._form_dang)
        elif tag in ("input", "select", "textarea", "button") and self._form_dang is not None:
            ten = a.get("name") or a.get("id")
            if ten and len(self._form_dang["o"]) < 40:
                self._form_dang["o"].append({"ten": _bo_pii(ten, 40), "loai": (a.get("type") or ("text" if tag == "input" else tag)).lower()})
        elif tag == "script":
            if a.get("src"):
                self.script_nguon.append(rut_diem_cuoi(a["src"]))
            self._script = {"json": "json" in a.get("type", "").lower() or a.get("id", "") == "__NEXT_DATA__",
                            "id": _bo_pii(a.get("id", ""), 40), "dem": [], "tong": 0}
        elif tag == "meta":
            k = (a.get("property") or a.get("name") or "").lower()
            if k in ("og:title", "og:type", "generator", "robots", "description", "og:site_name"):
                self.meta[k] = _bo_pii(a.get("content", ""), 160)
        for k in ("data-url", "data-src", "data-href", "data-endpoint", "data-ajax"):
            if a.get(k, "").startswith(("/", "http")) and len(self.diem_cuoi) < 80:
                self.diem_cuoi.append(rut_diem_cuoi(a[k]))

    def handle_endtag(self, tag):
        if tag == "title" and self._loai_buf == "title":
            self.tieu_de = self._ket()
        elif tag in ("h1", "h2", "h3") and self._loai_buf == tag:
            t = self._ket()
            if t and len(self.muc) < 60:
                self.muc.append((tag, t))
        elif tag == "a":
            if self._loai_buf == "tab" and self._a:
                t = self._ket()
                if len(self.tab) < 40:
                    self.tab.append({"chu": t, "den": rut_diem_cuoi(self._a[0]) if self._a[0] else ""})
            self._a = None
        elif tag in ("td", "th") and self._loai_buf == "o" and self._hang is not None:
            self._hang["o"].append(self._ket())
        elif tag == "tr" and self._hang is not None and self._bang_dang:
            b = self._bang_dang[-1]
            h = self._hang
            if any(h["o"]):
                if h["co_th"] and b["tieu_de"] is None:
                    b["tieu_de"] = h["o"][:14]                    # hang tieu de khong tinh vao so hang du lieu
                else:
                    b["so_hang"] += 1
                    if len(b["mau"]) < (10 if str((b["tieu_de"] or [""])[0]).strip().lower() == "symbol" else 2):
                        b["mau"].append(h["o"][:14])       # bang Symbol (Distribution cua MQL5): lay toi 10 hang de thay du phan bo
            self._hang = None
        elif tag == "table" and self._bang_dang:
            self._bang_dang.pop()
        elif tag == "form":
            self._form_dang = None
        elif tag == "script" and self._script is not None:
            s = self._script
            noi = "".join(s["dem"])
            if s["json"] and noi.strip():
                try:
                    j = json.loads(noi)
                    khoa = sorted(j.keys())[:30] if isinstance(j, dict) else ["<list %d>" % len(j)]
                    self.script_json.append({"id": s["id"], "khoa": [_bo_pii(k, 40) for k in khoa], "kich_thuoc": len(noi)})
                except ValueError:
                    pass
            elif noi:
                for m in _RX_GOI_MANG.findall(noi) + [h + p for h, p in _RX_DIEM_CUOI.findall(noi)]:
                    if len(self.diem_cuoi) < 80:
                        self.diem_cuoi.append(rut_diem_cuoi(m))
            self._script = None

    def handle_data(self, data):
        if self._buf is not None:
            self._buf.append(data)
        if self._script is not None and self._script["tong"] < 200_000:
            self._script["dem"].append(data)
            self._script["tong"] += len(data)


def tom_tat_cau_truc(html: str, url: str = "", toi_da: int = 40_000) -> dict:
    """HTML -> {tieu_de, muc, tab, bang (tieu de cot + 2 hang mau), form (ten o, KHONG gia tri), script, json_nhung, diem_cuoi, link_ra, meta}.

    Dung cho `link tham-do`: phien cloud khong toi duoc trang that, nen may nha tom tat cau truc (<= 40KB, khong cookie, khong gia tri o
    nhap / token / ma phien, email va so dai bi che) va gui ve de viet bo doc DUNG dinh dang trang. Muc dich: tim tab LICH SU LENH
    nam o dau (ban co cung cap bang that khong, hay tai bang bang XHR nao)."""
    html = str(html or "")
    p = _Tham()
    loi = ""
    try:
        p.feed(html)
        p.close()
    except Exception as e:                                       # HTML hong khong duoc lam sap tham do
        loi = "%s: %s" % (type(e).__name__, str(e)[:100])
    ra_nen: dict = {}
    for h in p.link_ra:
        m = phan_loai(h)
        if not m["rieng"]:
            ra_nen[m["nen_tang"]] = ra_nen.get(m["nen_tang"], 0) + 1
    kq = {
        "url": rut_diem_cuoi(url) if url else "", "kich_thuoc_html": len(html), "so_the": p.so_the, "tieu_de": p.tieu_de,
        "meta": p.meta, "muc": [{"cap": c, "chu": t} for c, t in p.muc], "tab": p.tab,
        "bang": [{"so_hang": b["so_hang"], "tieu_de": b["tieu_de"], "mau": b["mau"]} for b in p.bang if b["so_hang"]][:12],
        "form": p.form[:6],
        "script_nguon": list(dict.fromkeys(p.script_nguon))[:25], "json_nhung": p.script_json[:8],
        "diem_cuoi": list(dict.fromkeys(p.diem_cuoi))[:40], "link_ra_theo_nen_tang": dict(sorted(ra_nen.items(), key=lambda x: -x[1])),
        "can_js": bool(re.search(r"(?i)enable javascript|noscript", html[:20000])) and p.so_the < 80, "loi_doc": loi, "da_cat": False,
    }
    for khoa, gioi in (("diem_cuoi", 8), ("script_nguon", 5), ("bang", 4), ("muc", 15), ("tab", 10), ("form", 2), ("json_nhung", 2)):
        while len(json.dumps(kq, ensure_ascii=False)) > toi_da and len(kq[khoa]) > gioi:
            kq[khoa].pop()
            kq["da_cat"] = True
    return kq


# ---------------------------------------------------------------- PHAN BO SYMBOL (bang Distribution cua trang tin hieu MQL5)
_HAU_TO_SO = {"K": 1e3, "M": 1e6, "B": 1e9}


def _so_ngan(s):
    """'1549' -> 1549.0 · '9.8K' -> 9800.0 · '1,549' -> 1549.0 · rong / chu -> None (trang tieng Anh: dau cham la thap phan)."""
    t = str(s or "").replace("\xa0", "").replace(" ", "").strip()
    m = re.fullmatch(r"([+-]?\d[\d,]*(?:\.\d+)?)([KMB]?)", t, re.I)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "")) * _HAU_TO_SO.get(m.group(2).upper(), 1.0)
    except ValueError:
        return None


def chuan_symbol(tho) -> str:
    """Ten symbol cua san -> ten chung: 'GOLD#' / 'XAUUSDm' -> XAUUSD · 'EURUSD.pro' / 'EURUSD_i' / 'EURUSDm' -> EURUSD · 'US30m' -> US30.

    Cat hau to cua san (moi thu tu ky tu khong phai chu-so dau tien, va chu thuong theo sau phan chu hoa); GOLD* / SILVER* doi ra
    XAUUSD / XAGUSD. KHONG doan ten la: khong nhan ra thi tra lai ten da cat hau to, chu hoa."""
    s = re.split(r"[^A-Za-z0-9]", str(tho or "").strip(), maxsplit=1)[0]
    m = re.fullmatch(r"([A-Z0-9]{3,})([a-z]{1,5})", s)
    if m:
        s = m.group(1)
    u = s.upper()
    if u.startswith(("GOLD", "XAUUSD")):
        return "XAUUSD"
    if u.startswith(("SILVER", "XAGUSD")):
        return "XAGUSD"
    return u


def phan_bo_symbol(bang):
    """Cac bang 'Distribution' cua trang tin hieu MQL5 (Symbol | so lenh ; Symbol | USD ; Symbol | pip) -> symbol chinh THAT, hoac None.

    VI SAO: bo gan nhan cu (`_quet_signal_mql5._RX_SYM`) dem moi chu hoa 6 ky tu trong CA TRANG, nen bo sot `GOLD#` / `XAUUSDm` va gan
    nham `USDCHF` (2 lenh) cho con vang 1549 lenh (2196457, may nha do 03/10). Cac gia tri So (lenh / USD / pip) lay o COT 2 cua moi hang
    (cot tieu de bi de trong tren trang that); khong doan y nghia cot USD (lai rong hay gop) - chi ghi la `usd`."""
    theo: dict = {}
    for b in bang or []:
        tieu = [str(c).strip() for c in (b.get("tieu_de") or [])]
        if not tieu or tieu[0].lower() != "symbol":
            continue
        chu = " ".join(tieu).lower()
        khoa = "lenh" if "deals" in chu else "pip" if "pips" in chu else "usd" if "usd" in chu else None
        if khoa and khoa not in theo:
            theo[khoa] = b
    if "lenh" not in theo:
        return None
    hang = []
    for r in theo["lenh"].get("mau") or []:
        tho = str(r[0]).strip() if r else ""
        so = _so_ngan(r[1]) if len(r) > 1 else None
        if tho and so is not None:
            hang.append({"tho": tho, "chuan": chuan_symbol(tho), "lenh": int(so)})
    if not hang:
        return None
    for khoa in ("usd", "pip"):
        if khoa in theo:
            gt = {str(r[0]).strip(): _so_ngan(r[1]) for r in theo[khoa].get("mau") or [] if len(r) > 1}
            for h in hang:
                if gt.get(h["tho"]) is not None:
                    h[khoa] = gt[h["tho"]]
    gop: dict = {}
    for h in hang:
        gop[h["chuan"]] = gop.get(h["chuan"], 0) + h["lenh"]
    tong = sum(gop.values())
    chinh = max(gop, key=gop.get)
    return {"symbol_chinh": chinh, "ty_le_lenh": round(gop[chinh] / tong, 3) if tong else None,
            "day_du": len(hang) >= int(theo["lenh"].get("so_hang") or len(hang)), "symbol": hang}


def cho_tham_do(url: str) -> tuple[bool, str]:
    """Co duoc `link tham-do <url>` qua DON tu cloud khong: https + ten mien trong TEN_MIEN_CHO_PHEP + khong rieng + khong IP / cong la."""
    u = str(url or "").strip()
    if not u.lower().startswith("https://"):
        return False, "chi nhan https://"
    try:
        p = urlsplit(u)
        port = p.port
    except ValueError:
        return False, "url hong"
    if p.username or p.password or port not in (None, 443):
        return False, "url co user:pass hoac cong la"
    m = phan_loai(u)
    if m["rieng"] or m["nen_tang"] in ("noi_bo", "kho_tep", "facebook", "zalo", "discord", "whatsapp"):
        return False, "link rieng / khong tu dong duoc (%s)" % m["nen_tang"]
    goc = mien_goc(p.hostname or "")
    if goc not in TEN_MIEN_CHO_PHEP:
        return False, "ten mien %s chua duoc duyet cho tham do tu xa (chay tay tren may nha)" % goc
    return True, ""
