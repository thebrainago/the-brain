# -*- coding: utf-8 -*-
"""doc_dien_dan.py - DOC DIEN DAN / DANH SACH NHIEU TRANG: phan trang co moc 'den trang N', moi nuoc >= 1 dien dan, quet lai 1 tuan / lan.

Chu du an 03/10/2026 (thu nha 37ad / 5ce3): *"moi quoc gia can it nhat mot dien dan trader"*; *"danh sach nhieu trang: doc so trang roi
di tung trang, 3-5 giay / trang, nho 'da toi trang N' de lan sau doc tiep"*; *"quet lai 1 tuan / lan"*; *"cong cu cu ghi cung duong dan
may cu va cong 9222: doi sang trinh duyet AI cong 9224, ho so .browser_thebrain"*.

## Day la buoc TIM (TIM -> LAY lich su lenh -> HIEU luat -> LAM LAI -> THU -> CHINH)

Moi dien dan / danh sach trong `config/dien_dan.json` -> doc tung TRANG DANH SACH bai -> **ung vien** (URL bai + tieu de + diem tu khoa
luoi/DCA/EA/tin hieu) ghi o `du_lieu_cao/dien_dan/<ma>.jsonl` (gitignore). Module nay CHI DOC trang danh sach: khong mo tung bai, khong
dang nhap, khong dang ky, khong tham gia nhom, khong dang gi. Mo bai / lay lich su lenh la buoc sau (`b link`, `b nc cc boc_lich_su`);
nguon moi chi vao day chuyen khi da co DAT o xac_nhan (CLAUDE.md, NGUON_NGUOI_THANG).

## Cach dung

    b dien-dan ke-hoach                          khong mang: dien dan nao, se doc tu trang may, cho den bao gio
    b dien-dan do [--ma a,b]                     tham do 1-2 trang moi dien dan (ke ca dien dan dang tat): co bai khong, co phan trang khong, goi y bat/tat
    b dien-dan quet [--ma a,b] [--toi-da-trang N] [--ep]    doc tiep (mac dinh CHI dien dan `bat: true`); --ep = bo qua cho "1 tuan / lan"
    b dien-dan bao-cao                           khong mang: dung lai bao cao tu trang thai

## Tim trang ke (08/10/2026) - vi sao quet sau 70 nguon chi doc duoc vai trang

Loi cu: bo phan trang chi DEM so ghi tren link "1 2 3 .. 5842" ma khong di theo, va "khong thay link trang ke" bi coi la "het danh sach"
(XONG_PASS, nghi 168 gio) du dien dan con 5842 trang -> don quet bao DAT sau khi doc 1 trang. Nay `tim_trang_tiep(fo, tach, url_hien, n_tiep)` thu lan luot
(`phan_trang: auto`, mac dinh; `mau` = chi `mau_trang`; `khong` = chi doc trang 1) va tra {"url", "cach", "tong_uoc"}:
  1. `rel_next` (`<link rel=next>` / `<a rel=next>`, cung ten mien, khac trang dang doc) ;  2. `mau_trang` khai trong config ;
  3. `neo_so`: link CHINH XAC ghi so `n_tiep` ;  4. `mau_suy_ra`: khi thanh phan trang rut gon (`1 2 3 .. 5842`) khong hien so `n_tiep`, suy URL tu >= 2 link
     so >= 2 cung danh sach, CHI khi cum so doi la ham tuyen tinh NGUYEN cua so tren link (`page-N`; phpBB `start=25*(N-1)`) va `n_tiep <= so lon nhat thanh phan ghi` ;
  5. `chu_tiep`: nut "Next >" / "Trang sau" / chu tuong duong cac ngon ngu khac (xem `_TU_TIEP` va `_MUI_TEN_DON`; chi mui ten DON, cac dau ngoac kep kieu >> bi bo vi nhieu giao dien dung chung cho "TRANG CUOI").
Link phai thuoc CHINH danh sach dang doc: cung ten mien va cung `_goc_danh_sach` (bo vi tri trang `?page=3` `&start=50` `/page-3` `/p3`, ma phien,
tham so sap xep) HOAC cung duong dan voi `<link rel=canonical>` cung ten mien. Vi vay "2 3 .. 120" duoi tung chu de (`/threads/x.1/page-2`) khong bi nham
voi phan trang cua danh sach. Gioi han da biet: thanh phan trang tro sang duong dan KHAC `url` trong config va canonical (dien dan chuyen huong) thi phai sua `url`
hoac khai `mau_trang` - `b dien-dan do` goi y dung cau do (`co_neo_so_khac`).
Khong tim duoc duong sang trang trong khi thanh phan trang bao con trang -> `KHONG_THAY_TRANG_TIEP` (loi CAU HINH, KHONG phai XONG): nghi 24 gio (`GIO_NGHI_LOI_CAU_HINH`),
giu moc `den_trang`, khong tang `so_pass`; hien o bao cao. Ma thoat cua `b dien-dan quet`: 0 = co tien (hoac chi dang cho) ; 3 = ma khong co trong config ;
**5 = khong dien dan nao tien duoc** (tat het / BO_QUA / KHONG_THAY_TRANG_TIEP / bi chan, in `!! DIEN_DAN_KHONG_TIEN: ...`; `qwen/cau_loi.py` nhan dau vet nay la
`can_chan_doan`, nen don khong con ghi DAT gia). Mot phan dien dan hong, phan con lai tien: in `!! N dien dan khong tien duoc: ma(KET_QUA)` va van thoat 0.

## Luat cung (giong b link; repo PUBLIC)

* Khong ne chan, khong gia nguoi. 429 / 403 / captcha / Cloudflare -> DUNG ten mien do (nghi 15 phut x 2^n ... 24 gio) va ghi ma loi; khong
  doi UA / IP, khong thu lai dap, khong giai captcha. Cach lay (`http` / `cdp` / `cdp_render`) chon TRUOC trong config va KHONG doi sang cach
  khac khi bi chan. robots.txt cam -> khong doc. Chuyen huong CHI theo khi cung ten mien goc + https (<= 3 buoc, moi buoc qua nhip); sang ten
  mien khac / ha xuong http / dia chi noi bo -> KHONG toi dich, ghi lai. Phan hoi la tep tai ve / khong phai trang web -> chan, khong luu.
* Nhip: gian cach giua hai yeu cau cung ten mien = max(`nhip_giay` cua config, bang `link_nguon.NHIP_MIEN`, Crawl-delay). Tran: trang / luot /
  dien dan, trang / pass, yeu cau / ngay / ten mien (mql5 thap hon vi bi cam IP sau ~50-150 yeu cau), yeu cau / luot / ten mien.
* Nhieu dien dan duoc doc XEN KE (moi vong mot trang moi dien dan) de thoi gian cho nhip cua ten mien nay trum len thoi gian doc ten mien
  khac: luot ngan hon nhieu so voi doc lan luot (may nha ton dien - chi chay ngan khi duoc goi).
* Trang thai nam CHUNG voi `b link` (`du_lieu_cao/link_nguon_trang_thai.json`, khoa `dd:<ma>`): ten mien bi chan o day thi `b link` cung nghi.
  KHONG chay `b dien-dan` va `b link chay` cung luc (file trang thai chi co mot nguoi ghi).
* Chrome AI = trinh duyet THAT cua chu du an (`mo_trinh_duyet_ai.cmd`, cong 9224, ho so `.browser_thebrain`), doc cham nhu nguoi mo trang.
  Hien man chan thi DUNG. Module KHONG tu mo / dong Chrome, KHONG cham vao ho so Chrome goc, KHONG dung cong 9222.
* Bao cao di xa (`reports/dien_dan_ket_qua.*`) chi co ma dien dan, nuoc, so dem, ma loi, ID tin hieu MQL5 (cong khai). URL + tieu de bai o may nha.

## Da thu that / chua thu that

DA THU (03/10, cloud): Chrome 141 that (headless, cong CDP rieng 19224 - KHONG phai 9224) + dien dan gia HTTPS tu ky tren localhost: phan trang co
Referer, ca ba cach lay, chuyen huong (cung / khac ten mien, ha http, vong lap), tep tai ve, popup, quet tron mot luot + noi lai o tien trinh
moi. Hai thu do that lo ra va da sua:
  1. `ctx.request.get(max_redirects>0)` tu theo ca sang ten mien KHAC -> dat `max_redirects=0`, ta tu theo tung buoc (`cdp`).
  2. `page.route` cua Playwright KHONG duoc goi cho buoc chuyen huong, nen Chrome van cham ten mien khac -> `cdp_render` chan bang lop Fetch cua
     CDP o hai giai doan (Request + Response), chi tren KHUNG CHINH; may chu dich khong nhan gi. Anh / script / CDN / khung con tai nhu thuong.
DA THU (08/10, cloud, `test_doc_dien_dan.py` muc 10): 6 kieu phan trang cua cac phan mem dien dan that (XenForo `/page-N`, vBulletin `&page=N`, phpBB
`&start=25*(N-1)&sid=`, IPB `/page/N/`, mql5 `/pageN`, WordPress) khong co rel=next va khong khai `mau_trang`, moi chu de co them thanh phan trang nho `2 3 120`: doc het
danh sach theo dung thu tu, moi trang MOT lan, khong doan trang vuot thanh phan trang; danh sach `1 2 3 .. 5842` doc 5 trang / luot roi noi tiep o trang 6 trong
tien trinh moi; link chu de khong bi nham voi trang danh sach; `KHONG_THAY_TRANG_TIEP` + ma thoat 5. Cac test nay HONG 42 ca khi chay lai hanh vi cu (kiem dot bien).
CHUA THU THAT: cac dien dan that (cloud khong toi duoc). `mau_bai` / `mau_trang` trong config lay tu lan do 15/09 hoac tri nho (muc `kiem_tra`):
`b dien-dan do` o may nha la lan do that dau tien. Chrome cua chu du an co the khac ban (154): neu id khung doi cach danh so, su kien dau tien
khong khop khung chinh -> DONG (loi `khung_chinh_khong_khop`) chu khong am tham tat bo loc.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

from nhan import link_chay as LCH  # noqa: E402
from nhan import link_nguon as LN  # noqa: E402

CAU_HINH = LAB / "config" / "dien_dan.json"
THU_MUC_UNG_VIEN = LN.THU_MUC_CAO / "dien_dan"                 # bi gitignore: URL + tieu de bai chi nam o may nha
BAO_CAO_JSON = LAB / "reports" / "dien_dan_ket_qua.json"
BAO_CAO_MD = LAB / "reports" / "dien_dan_ket_qua.md"
CDP_CONG = 9224                                                # Chrome AI (mo_trinh_duyet_ai.cmd, ho so .browser_thebrain)
TIEN_TO = "dd:"                                                # khoa trang thai trong TrangThai chung voi `b link`
CACH_LAY = ("http", "cdp", "cdp_render")
PHAN_TRANG = ("auto", "mau", "khong")
LAN_CHUYEN_TOI_DA = 3                                           # chuyen huong cung ten mien + https toi da bao nhieu lan / yeu cau
TIMEOUT_TRANG_MS = 45000                                       # mo tab that: du cho <= 3 buoc chuyen huong (moi buoc co nhip) + tai trang
_MA_CHUYEN_HUONG = (301, 302, 303, 307, 308)
_RX_DOC_DUOC = re.compile(r"^(?:text/[\w.+-]+|application/(?:xhtml\+xml|json|xml|[\w.+-]+\+(?:json|xml)))$", re.I)
GIO_NGHI_LOI_CAU_HINH = 24                                     # sai mau_bai / chuyen huong: dung 24 gio roi do lai, khong tinh tung 5 phut
MAC_DINH = {"toi_da_trang_luot": 10, "toi_da_trang_pass": 200, "tran_ngay_mien": 120, "tran_ngay_theo_mien": {"mql5.com": 60},
            "do_dai_tieu_de": 25, "chu_ky_gio": 168}


# ============================================================== 1. CAU HINH
def nap_cau_hinh(duong=None) -> dict:
    return json.loads(Path(duong or CAU_HINH).read_text(encoding="utf-8-sig"))


def _tham_so(cfg: dict, fo: dict, ten: str):
    """Gia tri theo thu tu: dien dan > `mac_dinh` > goc config > MAC_DINH trong ma."""
    for nguon in (fo, cfg.get("mac_dinh") or {}, cfg):
        if isinstance(nguon, dict) and nguon.get(ten) is not None and ten in nguon:
            return nguon[ten]
    return MAC_DINH[ten]


def _mien(url: str) -> str:
    try:
        return LN.mien_goc(urlsplit(url).hostname or "")
    except ValueError:
        return ""


_RX_URL = re.compile(r"(?:https?|wss?|ftp)://\S+", re.I)


def _khong_url(s) -> str:
    """Bo moi URL khoi mot doan chu: loi cua Playwright / requests kem 'Call log' co URL day du, ma bao cao di xa khong duoc mang URL."""
    return _RX_URL.sub("<url>", str(s))


def _loi_ngan(e: BaseException, n: int = 100) -> str:
    """Ngoai le -> MOT dong `Ten: noi dung`, khong URL, <= n ky tu (an toan de ghi trang thai / bao cao)."""
    dong = (str(e).strip().splitlines() or [""])[0]
    return ("%s: %s" % (type(e).__name__, _khong_url(dong)))[:n]


def _thay_mau_trang(fo: dict, n: int) -> str:
    return str(fo["mau_trang"]).replace("{base}", fo["url"]).replace("{n}", str(n))


_RX_MA = re.compile(r"^[a-z0-9_]{1,40}$")
_RX_NUOC = re.compile(r"^[a-z]{2,3}$")


def kiem_cau_hinh(cfg) -> list[str]:
    """Danh sach loi cau hinh (rong = hop le). Chan tu goc: link rieng, nen tang khong tu dong, URL khong https, mau hong."""
    if not isinstance(cfg, dict) or not isinstance(cfg.get("dien_dan"), list):
        return ["thieu danh sach `dien_dan`"]
    loi, thay = [], set()
    if float(_tham_so(cfg, {}, "chu_ky_gio")) < 24:
        loi.append("`chu_ky_gio` toi thieu 24 gio (chu du an chot 1 tuan / lan = 168)")
    for i, fo in enumerate(cfg["dien_dan"]):
        if not isinstance(fo, dict):
            loi.append("dien_dan[%d]: khong phai doi tuong" % i)
            continue
        ma = str(fo.get("ma", ""))
        n = "dien_dan[%d] %s" % (i, ma or "?")
        if not _RX_MA.match(ma):
            loi.append(n + ": `ma` chi gom chu thuong / so / _ (1-40 ky tu)")
        if ma in thay:
            loi.append(n + ": trung `ma`")
        thay.add(ma)
        if not _RX_NUOC.match(str(fo.get("nuoc", ""))):
            loi.append(n + ": `nuoc` la ma 2-3 chu thuong (vi, ru, ja...)")
        url = str(fo.get("url", ""))
        if not url.startswith("https://"):
            loi.append(n + ": `url` phai bat dau bang https://")
        else:
            pl = LN.phan_loai(url)
            if pl["rieng"] or pl["nen_tang"] in LCH.KHONG_TU_DONG:
                loi.append(n + ": link rieng / nen tang khong tu dong (%s): KHONG dua vao config cong khai" % pl["nen_tang"])
        if fo.get("cach_lay", "http") not in CACH_LAY:
            loi.append(n + ": `cach_lay` phai la %s" % "/".join(CACH_LAY))
        if fo.get("phan_trang", "auto") not in PHAN_TRANG:
            loi.append(n + ": `phan_trang` phai la %s" % "/".join(PHAN_TRANG))
        if not isinstance(fo.get("bat", False), bool):
            loi.append(n + ": `bat` phai la true / false")
        mb = fo.get("mau_bai")
        if mb:
            try:
                if len(mb) > 300:
                    raise re.error("qua dai")
                re.compile(mb)
            except re.error as e:
                loi.append(n + ": `mau_bai` khong hop le (%s)" % e)
        mt = fo.get("mau_trang")
        if mt:
            if "{n}" not in mt:
                loi.append(n + ": `mau_trang` phai co {n}")
            elif url.startswith("https://"):
                u2 = _thay_mau_trang(fo, 2)
                if not u2.startswith("https://") or _mien(u2) != _mien(url):
                    loi.append(n + ": `mau_trang` phai cho URL https cung ten mien voi `url`")
        for ten, lo, hi in (("toi_da_trang_luot", 1, 200), ("toi_da_trang_pass", 1, 2000), ("nhip_giay", 1, 600), ("do_dai_tieu_de", 5, 200),
                            ("chu_ky_gio", 24, 24 * 90)):
            if ten in fo and not (isinstance(fo[ten], (int, float)) and not isinstance(fo[ten], bool) and lo <= fo[ten] <= hi):
                loi.append(n + ": `%s` phai trong %d..%d" % (ten, lo, hi))
    return loi


# ============================================================== 2. PHAN TICH TRANG (ham thuan)
class _Neo(HTMLParser):
    """Gom <a href> (kem chu hien thi), rel=next (the <link> hoac <a>), <base href>, <title>. Khong chay JS, khong tai gi them.
    HTML khong cho long <a>: mot <a> moi (hoac het trang) dong <a> dang mo - nhu trinh duyet - nen the <a> quen dong khong nuot cac link sau."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.neo: list[tuple[str, str]] = []
        self.rel_next, self.base, self.tieu_de, self.canonical = "", "", "", ""
        self._a: list | None = None                             # the <a> dang mo: [href, [manh chu]]
        self._tren_title = False

    def _dong_a(self):
        if self._a is not None:
            href, chu = self._a
            self.neo.append((href, re.sub(r"\s+", " ", "".join(chu)).strip()[:200]))
            self._a = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        la_next = "next" in a.get("rel", "").lower().split()
        if tag == "a":
            self._dong_a()
            self._a = [a.get("href", ""), []]
            if la_next and a.get("href") and not self.rel_next:
                self.rel_next = a["href"]
        elif tag == "link":
            if la_next and a.get("href") and not self.rel_next:
                self.rel_next = a["href"]
            if "canonical" in a.get("rel", "").lower().split() and a.get("href") and not self.canonical:
                self.canonical = a["href"]
        elif tag == "base":
            if a.get("href") and not self.base:
                self.base = a["href"]
        elif tag == "title":
            self._tren_title = True

    def handle_endtag(self, tag):
        if tag == "a":
            self._dong_a()
        elif tag == "title":
            self._tren_title = False

    def handle_data(self, data):
        if self._tren_title and len(self.tieu_de) < 300:
            self.tieu_de += data
        if self._a is not None and sum(len(x) for x in self._a[1]) < 400:
            self._a[1].append(data)

    def close(self):
        super().close()
        self._dong_a()


_BO_QUA_HREF = ("#", "javascript:", "mailto:", "tel:", "data:", "sms:", "whatsapp:", "tg:")
_RX_NEO_TRANG = re.compile(r"page|[?&/]p[=/]|pg[=/]|[?&]start=|[?&]offset=", re.I)


def tach_trang(html: str, url: str) -> dict:
    """HTML -> {tieu_de, neo: [(url tuyet doi, chu)], rel_next, so_trang: [so ghi tren cac neo phan trang], canonical}. Khong nem loi voi HTML hong."""
    p = _Neo()
    try:
        p.feed(html or "")
        p.close()
    except Exception:                                            # HTMLParser hiem khi ne loi: giu phan da gom
        pass
    goc = url
    if p.base:
        try:
            goc = urljoin(url, p.base)
        except ValueError:
            goc = url
    neo, so_trang = [], set()
    for href, chu in p.neo:
        h = (href or "").strip()
        if not h or h.lower().startswith(_BO_QUA_HREF):
            continue
        try:
            tuyet_doi = urljoin(goc, h).split("#", 1)[0]
        except ValueError:
            continue
        if not tuyet_doi.startswith(("http://", "https://")):
            continue
        neo.append((tuyet_doi, chu))
        if re.fullmatch(r"\d{1,5}", chu) and _RX_NEO_TRANG.search(tuyet_doi):
            so_trang.add(int(chu))
    rel_next, canonical = "", ""
    if p.rel_next:
        try:
            rel_next = urljoin(goc, p.rel_next).split("#", 1)[0]
        except ValueError:
            rel_next = ""
    if p.canonical:                                              # dia chi chinh thuc cua trang: dien dan chuyen huong `url` cau hinh sang duong dan khac van nhan ra
        try:
            canonical = urljoin(goc, p.canonical).split("#", 1)[0]
        except ValueError:
            canonical = ""
    return {"tieu_de": re.sub(r"\s+", " ", p.tieu_de).strip()[:160], "neo": neo, "rel_next": rel_next, "so_trang": sorted(so_trang), "canonical": canonical}


_RX_HAU_TO_BAI = re.compile(r"/(?:page[-_]?\d+|latest|unread|last)/?$", re.I)


def _khoa_bai(u: str) -> str:
    """Khoa so sanh mot bai: URL chuan hoa, bo duoi `/page-3`, `/latest`... (cung mot bai, nhieu neo)."""
    k = LN.chuan_hoa_url(u)
    return _RX_HAU_TO_BAI.sub("", k) or k


def trich_bai(fo: dict, tach: dict, url_trang: str, do_dai_toi_thieu: int = 25, toi_da: int = 400) -> list[dict]:
    """Ung vien bai tren mot trang danh sach. Co `mau_bai`: link khop mau. Khong co: link CUNG TEN MIEN co chu >= `do_dai_toi_thieu` ky tu
    (tieu de bai dai, nut dieu huong ngan). Bo chinh trang nay, trang goc va cac neo phan trang."""
    mau = re.compile(fo["mau_bai"], re.I) if fo.get("mau_bai") else None
    goc = _mien(fo["url"])
    ra, thay = [], {_khoa_bai(url_trang), _khoa_bai(fo["url"])}
    for u, chu in tach["neo"]:
        if mau is not None:
            if not mau.search(u):
                continue
        elif _mien(u) != goc or len(chu) < do_dai_toi_thieu:
            continue
        k = _khoa_bai(u)
        if k in thay:
            continue
        thay.add(k)
        ra.append({"url": u, "tieu_de": chu[:160]})
        if len(ra) >= toi_da:
            break
    return ra


# ---- tim trang tiep KHI KHONG co rel=next va khong khai `mau_trang` (08/10/2026)
# Do 08/10: 2 trong 8 don "quet sau" chi doc 1 trang roi bao XONG_PASS du MQL5 ghi 5842 trang - thanh phan trang chi duoc DEM (tong_trang),
# khong bao gio duoc DUNG de di tiep, va "khong thay trang tiep" bi doc nham thanh "het danh sach". Nay: neo so -> mau suy ra -> chu "trang sau".
#: tham so query chi VI TRI trang (gia tri la so): bo khi so sanh "cung mot danh sach"
_THAM_SO_TRANG = frozenset(("page", "p", "pg", "paged", "pagenum", "pageno", "pagina", "seite", "strona", "sayfa", "halaman", "start", "offset",
                            "skip", "pn"))
_THAM_SO_PHIEN = frozenset(("sid", "s", "phpsessid", "sessionid", "session"))        # phpBB / vBulletin gan ma phien vao link phan trang
#: tham so chi cach TRINH BAY danh sach (sap xep, so dong): vBulletin ghi `&order=desc&sort=lastpost&pp=25` vao link trang 2.. nhung khong vao `url` cau hinh
_THAM_SO_TRINH_BAY = frozenset(("order", "sort", "orderby", "sortby", "sk", "sd", "st", "dir", "direction", "pp", "perpage", "per_page", "limit", "daysprune",
                                "ref", "hilit"))
_RX_HAU_TO_TRANG = re.compile(r"/(?:page|pagina|seite|strona|sayfa|halaman|pg|p)[-_/]?\d+/?$", re.I)
#: chu tren neo phan trang: `3`, `Page 3`, `Trang 3` va dang CJK / Cyrillic tuong duong (khong nhan `03`: so dem muc luc, khong phai trang)
_RX_CHU_SO_TRANG = re.compile(
    r"(?:page|pagina|p[aá]gina|trang|seite|strona|sayfa|halaman|страница|стр\.?|ページ|第|หน้า)?\s*(\d{1,5})\s*(?:ページ|页|頁)?", re.I)
_MUI_TEN = (
    r"  »›>→▶⟩〉》")                                                       # ky tu mui ten / khoang trang bi cat khi so voi chu "trang sau"
#: chu cua nut "trang sau" (da ngon ngu): duong CUOI CUNG, sau neo so va mau suy ra; "cuoi" / "last" / ">>" khong bao gio vao day.
_TU_TIEP = frozenset((
    r"next", r"next page", r"siguiente", r"pagina siguiente", r"página siguiente", r"weiter", r"nächste", r"naechste", r"nächste seite", r"suivant", r"suivante",
    r"page suivante", r"avanti", r"successiva", r"prossima", r"próxima", r"proxima", r"seguinte", r"próxima página", r"volgende", r"nästa", r"następna", r"dalej",
    r"далее", r"вперед", r"вперёд", r"следующая", r"следующая страница", r"次へ", r"次のページ", r"下一页", r"下一頁", r"下页", r"下一页 »", r"다음", r"다음 페이지",
    r"selanjutnya", r"berikutnya", r"ถัดไป", r"sonraki", r"ileri", r"tiếp", r"tiếp theo", r"trang sau", r"trang tiếp", r"trang kế", r"अगला", r"التالي", r"التالية"))
_MUI_TEN_DON = frozenset((
    r"›", r">", r"→", r"▶", r"⟩", r"〉"))                                   # mui ten don; dau ngoac kep phai bi bo vi nhieu giao dien dung cho "TRANG CUOI"


def _goc_danh_sach(url: str) -> str:
    """URL -> khoa "cung mot danh sach": bo vi tri trang (`?page=3`, `&start=50`, duoi `/page-3`, `/page/3/`, `/p3`), ma phien va tham so trinh bay.
    Neo "2" cua bai `/threads/x.1/page-2` co khoa KHAC neo "2" cua chinh danh sach `/forums/robot.44/page-2` -> khong bi nham."""
    sp = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(sp.query, keep_blank_values=True)
         if k.lower() not in _THAM_SO_PHIEN and k.lower() not in _THAM_SO_TRINH_BAY and not (k.lower() in _THAM_SO_TRANG and v.isdigit())]
    return LN.chuan_hoa_url(urlunsplit((sp.scheme, sp.netloc, _RX_HAU_TO_TRANG.sub("", sp.path), urlencode(q), "")))


def _so_tren_neo(chu: str) -> int:
    g = _RX_CHU_SO_TRANG.fullmatch((chu or "").strip())
    return int(g.group(1)) if g and not g.group(1).startswith("0") else 0


def _la_chu_tiep(chu: str) -> bool:
    c = re.sub(r"\s+", " ", (chu or "").strip().casefold())
    if not c or len(c) > 24:
        return False
    if c in _MUI_TEN_DON or c in _TU_TIEP:
        return True
    loi = c.strip(_MUI_TEN)
    return bool(loi) and loi in _TU_TIEP


def _goc_chap_nhan(fo: dict, tach: dict, url_hien: str) -> set[str]:
    """Cac `_goc_danh_sach` duoc coi la "chinh danh sach nay": cua URL dang doc, va cua `<link rel=canonical>` neu cung ten mien."""
    ra = {_goc_danh_sach(url_hien)}
    c = tach.get("canonical") or ""
    if c.startswith(("http://", "https://")) and _mien(c) == _mien(fo["url"]):
        ra.add(_goc_danh_sach(c))
    return ra


def _neo_cung_danh_sach(fo: dict, tach: dict, url_hien: str) -> list[tuple[int, str]]:
    """[(so ghi tren neo, URL https)] cac neo danh so TRANG cua CHINH danh sach dang doc: cung ten mien va `_goc_danh_sach` thuoc `_goc_chap_nhan`."""
    goc, mien = _goc_chap_nhan(fo, tach, url_hien), _mien(fo["url"])
    ra, thay = [], set()
    for u, chu in tach["neo"]:
        n = _so_tren_neo(chu)
        if not n or _mien(u) != mien:
            continue
        u = re.sub(r"^http://", "https://", u)
        if (n, u) not in thay and _goc_danh_sach(u) in goc:
            thay.add((n, u))
            ra.append((n, u))
    return ra


def _suy_mau(cac: list[tuple[int, str]], n: int) -> str:
    """>= 2 neo (so, URL) cung danh sach -> URL trang `n` khi neo `n` khong hien (thanh phan trang rut gon `1 2 3 ... 5842`).
    Tach URL thanh [chu, so, chu, so ...]: phan chu phai y het nhau, dung MOT cum so doi, va cum do la ham TUYEN TINH NGUYEN cua so tren neo:
    `page-N` (a=1, b=0), phpBB `start=25*(N-1)` (a=25, b=-25). Moi neo phai nam tren duong thang do, neu khong -> '' (khong doan)."""
    nhom: dict[tuple, list] = {}
    for so, u in cac:
        p = re.split(r"(\d+)", u)
        nhom.setdefault(tuple(p[0::2]), []).append((so, p))
    if not nhom:
        return ""
    khung, mau = max(nhom.items(), key=lambda kv: len({so for so, _ in kv[1]}))
    if len({so for so, _ in mau}) < 2:
        return ""
    cho_doi = [i for i in range(1, len(mau[0][1]), 2) if len({p[i] for _, p in mau}) > 1]
    if len(cho_doi) != 1:
        return ""
    i = cho_doi[0]
    if any(len(p[i]) > 1 and p[i].startswith("0") for _, p in mau):                      # 005, 010: do rong co dinh - khong suy
        return ""
    (s1, p1), (s2, p2) = min(mau, key=lambda x: x[0]), max(mau, key=lambda x: x[0])
    d_so = s2 - s1
    if d_so <= 0 or (int(p2[i]) - int(p1[i])) % d_so:
        return ""
    a = (int(p2[i]) - int(p1[i])) // d_so
    b = int(p1[i]) - a * s1
    if a <= 0 or any(int(p[i]) != a * s + b for s, p in mau):
        return ""
    v = a * n + b
    if v < 0:
        return ""
    ra = list(mau[0][1])
    ra[i] = str(v)
    return "".join(ra)


def tim_trang_tiep(fo: dict, tach: dict, url_hien: str, n_tiep: int) -> dict:
    """-> {"url": URL trang `n_tiep` hoac '' , "cach": rel_next | mau_trang | neo_so | mau_suy_ra | chu_tiep | '', "tong_uoc": so trang LON NHAT ma
    thanh phan trang cua CHINH danh sach nay ghi (0 = khong thay)}. `phan_trang`: auto = rel=next, roi `mau_trang`, roi (khong khai gi) tu tim tren trang
    (neo so -> mau suy ra tu >= 2 neo -> nut "trang sau"); mau = chi `mau_trang`; khong = chi doc trang 1. Thanh phan trang phai thuoc CHINH danh sach nay
    (cung duong dan sau khi bo vi tri trang / ma phien / tham so sap xep; hoac cung duong dan voi `<link rel=canonical>`): link "2 3 .. 120" duoi tung chu de bi bo.
    rel=next tro sang ten mien khac hoac tro lai chinh no -> bo qua. Thanh phan trang CHI cho phep di toi trang <= so lon nhat no ghi (khong doan trang 4 khi
    thanh phan trang dung o 3). `url == ''` ma `tong_uoc > n_tiep - 1` = dien dan CON trang nhung ta khong co duong sang: KHONG phai "het danh sach"."""
    kieu = fo.get("phan_trang", "auto")
    cac = _neo_cung_danh_sach(fo, tach, url_hien)
    ra = {"url": "", "cach": "", "tong_uoc": max((n for n, _ in cac), default=0)}
    if kieu == "khong":
        return ra
    if kieu == "auto" and tach.get("rel_next"):
        nx = re.sub(r"^http://", "https://", tach["rel_next"])
        if _mien(nx) == _mien(fo["url"]) and LN.chuan_hoa_url(nx) != LN.chuan_hoa_url(url_hien):
            return dict(ra, url=nx, cach="rel_next")
    if fo.get("mau_trang"):
        return dict(ra, url=_thay_mau_trang(fo, n_tiep), cach="mau_trang")
    if kieu != "auto":
        return ra
    theo_so = {}
    for n, u in cac:
        theo_so.setdefault(n, u)
    if n_tiep in theo_so:
        return dict(ra, url=theo_so[n_tiep], cach="neo_so")
    if cac and n_tiep <= ra["tong_uoc"]:
        u = _suy_mau([(n, u) for n, u in cac if n >= 2], n_tiep)
        if u and LN.chuan_hoa_url(u) != LN.chuan_hoa_url(url_hien):
            return dict(ra, url=u, cach="mau_suy_ra")
    goc, mien, hien = _goc_chap_nhan(fo, tach, url_hien), _mien(fo["url"]), LN.chuan_hoa_url(url_hien)
    for u, chu in tach["neo"]:                                                           # cuoi cung: nut "trang sau" cua chinh danh sach nay
        u = re.sub(r"^http://", "https://", u)
        if _la_chu_tiep(chu) and _mien(u) == mien and LN.chuan_hoa_url(u) != hien and _goc_danh_sach(u) in goc:
            return dict(ra, url=u, cach="chu_tiep")
    return ra


def url_trang_tiep(fo: dict, tach: dict, url_hien: str, n_tiep: int) -> str:
    """URL trang `n_tiep` hoac '' (het / khong phan trang / khong tim duoc). Xem `tim_trang_tiep` (ke ca `cach` va tong so trang uoc)."""
    return tim_trang_tiep(fo, tach, url_hien, n_tiep)["url"]


def _van_tay(bai: list[dict], tach: dict) -> str:
    """Dau van tay mot trang = tap URL bai (hoac moi neo neu khong co bai): phat hien phan trang 'khong tien' (trang N+1 y het trang N)."""
    nguon = sorted(_khoa_bai(b["url"]) for b in bai) or sorted(u for u, _ in tach["neo"])[:200]
    return hashlib.sha1("\n".join(nguon).encode("utf-8")).hexdigest()[:10]


#: Diem tieu de = so NHOM tu khoa khop (0-3): luoi/DCA/martingale, EA/robot/bot, tin hieu. CHI de xep thu tu, KHONG loai bai nao.
_NHOM_TU_KHOA = tuple(re.compile(p, re.I) for p in (
    r"grid|martingal|\bdca\b|hedg|averag|recover|gitter|grille|siatka|rejilla|ortalama|l[uư][oơ]i|сетк|мартингейл|усредн"
    r"|グリッド|マーチン|ナンピン|กริด|มาร์ติงเกล|มาติงเกล|网格|马丁|加仓",
    r"\bea\b|expert advisor|robot|\bbot\b|советник|робот|ロボット|自動売買|บอท|机器人|智能交易|روبوت",
    r"signal|t[ií]n hi[eệ]u|сигнал|シグナル|สัญญาณ|sinyal|sinal|se[nñ]al|segnale|signaux|sygna|信号",
))
_RX_TIN_HIEU = re.compile(r"mql5\.com/(?:[a-z]{2}/)?signals/(\d+)", re.I)


def diem_tieu_de(tieu_de: str) -> int:
    return sum(1 for rx in _NHOM_TU_KHOA if rx.search(tieu_de or ""))


def _duoc_theo(nx: str, goc: str) -> bool:
    """Dich chuyen huong / dieu huong cua KHUNG CHINH co duoc phep khong: https + cung ten mien goc + khong phai dia chi noi bo / IP."""
    return urlsplit(nx).scheme == "https" and _mien(nx) == goc and LN.phan_loai(nx)["nen_tang"] != "noi_bo"


def _khong_phai_trang(dau: dict) -> str:
    """Phan hoi cua khung chinh la TAI VE (Content-Disposition: attachment) hoac khong doc duoc nhu trang (exe, zip, pdf, octet-stream, thieu
    Content-Type -> Chrome tu do loai va co the luu tep) -> ly do ngan; '' neu doc duoc. Chrome cua chu du an khong bao gio duoc tu tai tep ve may."""
    if str(dau.get("content-disposition", "")).strip().lower().startswith("attachment"):
        return "tai ve (attachment)"
    ct = str(dau.get("content-type", "")).split(";")[0].strip().lower()
    if not ct:
        return "khong co content-type"
    if not _RX_DOC_DUOC.match(ct):
        return "khong phai trang web (%s)" % ct[:40]
    return ""


# ============================================================== 3. CHROME AI (CDP 9224)
class KhongCoCdp(RuntimeError):
    """Chrome AI chua bat CDP (cong 9224) hoac may chua cai playwright: dien dan can Chrome duoc bo qua, KHONG tinh la loi cua dien dan."""


class PhienCdp:
    """MOT ket noi toi Chrome AI cho ca luot quet (mo mot lan, khong noi lai moi trang). Khong mo / dong Chrome, khong dong tab cua tien trinh khac."""

    def __init__(self, cong: int | None = None, cho_ms: int = 14000):
        self.cong, self.cho_ms = cong, cho_ms
        self._pw = self._ctx = None

    def __enter__(self):
        from nhan import doc_trinh_duyet as DT
        cong = self.cong or DT.cdp_dang_chay((CDP_CONG,))
        if not cong:
            raise KhongCoCdp("khong_mo_cdp: bat Chrome AI (mo_trinh_duyet_ai.cmd, cong %d)" % CDP_CONG)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise KhongCoCdp("khong_co_playwright") from None
        self._pw = sync_playwright().start()
        try:
            b = self._pw.chromium.connect_over_cdp("http://127.0.0.1:%d" % cong)
            self._ctx = b.contexts[0] if b.contexts else b.new_context()
            DT._don_tab(self._ctx)
        except Exception as e:
            self.__exit__(None, None, None)
            raise KhongCoCdp("khong_noi_duoc_cdp: %s" % LCH._cat("%s: %s" % (type(e).__name__, e), 100)) from None
        return self

    def __exit__(self, *_):
        try:
            if self._pw is not None:
                self._pw.stop()                                 # chi ngat ket noi cua ta; Chrome cua chu du an van chay
        except Exception:
            pass
        self._pw = self._ctx = None
        return False

    def lay(self, url: str, referer: str = "", render: bool = False, truoc=None):
        """-> (status | None, text, loi) giong `link_chay.lay_http`. render=False: GET qua cookie cua Chrome AI (Referer = trang truoc, khong chay JS,
        mang cua Playwright chu khong phai ngan xep mang cua tab); render=True: mo tab that, cho JS chay xong roi doc DOM (mang that cua Chrome).
        `truoc(url)` goi TRUOC moi yeu cau (nhip + dem tran; co the nem `HetNhip`).
        Chuyen huong chi duoc theo khi cung ten mien goc VA https; ra ten mien khac -> KHONG toi dich, `loi = "chuyen huong ra ngoai: <url>"`.
        (Do that 03/10 voi Chrome 141: `max_redirects>0` de Playwright tu theo ca sang ten mien khac, nen o day dat 0 va tu theo tung buoc;
        o che do render thi Chrome tu theo nen chan bang Fetch (CDP), xem `_lay_render`.)"""
        url = LCH._url_de_tai(url)
        if render:
            return self._lay_render(url, truoc)
        goc = _mien(url)
        kw = {"headers": {"Referer": referer}} if referer else {}
        cur = url
        for _ in range(LAN_CHUYEN_TOI_DA + 1):
            if truoc:
                truoc(cur)
            try:
                r = self._ctx.request.get(cur, timeout=30000, max_redirects=0, **kw)
            except TypeError:                                    # Playwright < 1.26: khong chan duoc chuyen huong -> khong chay con hon chay lieu
                return None, "", "playwright_qua_cu: can Playwright >= 1.26 (max_redirects)"
            except Exception as e:
                return None, "", _loi_ngan(e)
            try:
                status = r.status
                dau = {str(k).lower(): v for k, v in (r.headers or {}).items()}
                if status in (301, 302, 303, 307, 308) and dau.get("location"):
                    nx = urljoin(cur, dau["location"])
                    if not _duoc_theo(nx, goc):
                        return status, "", "chuyen huong ra ngoai: %s" % nx
                    cur = nx
                    continue
                return status, LCH._giai_ma_text(r.body()[:LCH.TOI_DA_BYTE], dau), ""
            except Exception as e:
                return None, "", _loi_ngan(e)
            finally:
                try:
                    r.dispose()
                except Exception:
                    pass
        return None, "", "qua nhieu lan chuyen huong"

    def _lay_render(self, url: str, truoc=None):
        """Mo tab that, cho JS chay, doc DOM. Chrome TU theo chuyen huong, nen phai chan truoc khi no di: lop Fetch cua CDP, tren KHUNG CHINH,
        o CA HAI giai doan - YEU CAU (JS tu `location.href = ...`) va PHAN HOI 3xx (doc Location, yeu cau toi dich chua duoc gui).
        Do that 03/10 (Chromium 141 + Playwright 1.63): `page.route` KHONG duoc goi cho buoc chuyen huong - ke ca `route.fetch(max_redirects=0)` +
        `route.fulfill` - nen yeu cau van toi ten mien khac; Fetch (Response) thi chan duoc, may chu dich khong nhan gi.
        Chi chan DIEU HUONG khung chinh: anh / script / CDN / khung con (quang cao) van tai nhu trinh duyet binh thuong."""
        pg = cdp = None
        goc = _mien(url)
        ts = {"ra_ngoai": "", "ma_chan": None, "nhieu": False, "khong_trang": "", "het_nhip": None, "loi": "", "hop": 0, "da_tinh": True, "thay_dau": False}
        khung = {"id": None}

        def _dung(rid):
            """Chan yeu cau: dich KHONG nhan gi. Ly do da nam trong `ts` (nguoi goi ghi truoc)."""
            try:
                cdp.send("Fetch.failRequest", {"requestId": rid, "errorReason": "BlockedByClient"})
            except Exception:
                pass

        def _xu_ly(ev):
            rid = ev.get("requestId")
            try:
                rq = ev["request"]
                dau_tien, ts["thay_dau"] = not ts["thay_dau"], True
                if ev.get("frameId") != khung["id"]:
                    if dau_tien:                                                       # su kien DAU phai la cua khung chinh; khong khop = khong dam tin bo loc
                        ts["loi"] = "khung_chinh_khong_khop: Chrome doi cach danh so khung, bo loc chuyen huong khong dung duoc"
                        return _dung(rid)
                    cdp.send("Fetch.continueRequest", {"requestId": rid})              # khung con (quang cao, nhung): de trinh duyet lam binh thuong
                    return
                ma = ev.get("responseStatusCode")
                if ma is None and not ev.get("responseErrorReason"):                  # --- giai doan YEU CAU
                    if not _duoc_theo(rq["url"], goc):
                        ts["ra_ngoai"] = ts["ra_ngoai"] or rq["url"]
                        return _dung(rid)
                    if ts["da_tinh"]:                                                  # trang dau / buoc chuyen huong: da qua nhip roi
                        ts["da_tinh"] = False
                    elif truoc:
                        truoc(rq["url"])                                               # JS tu mo them mot trang cung ten mien: van nhip + dem tran
                    cdp.send("Fetch.continueRequest", {"requestId": rid})
                    return
                if ma is None:                                                        # --- phan hoi bi loi mang: de trinh duyet bao loi
                    cdp.send("Fetch.continueRequest", {"requestId": rid})
                    return
                dau = {str(h.get("name", "")).lower(): str(h.get("value", "")) for h in ev.get("responseHeaders") or []}
                if ma in _MA_CHUYEN_HUONG and dau.get("location"):                   # --- giai doan PHAN HOI, 3xx: quyet truoc khi trinh duyet di tiep
                    nx = urljoin(rq["url"], dau["location"])
                    ts["ma_chan"] = ma
                    if not _duoc_theo(nx, goc):
                        ts["ra_ngoai"] = ts["ra_ngoai"] or nx
                        return _dung(rid)
                    ts["hop"] += 1
                    if ts["hop"] > LAN_CHUYEN_TOI_DA:
                        ts["nhieu"] = True
                        return _dung(rid)
                    if truoc:
                        truoc(nx)
                    ts["da_tinh"] = True
                    ts["ma_chan"] = None
                    cdp.send("Fetch.continueRequest", {"requestId": rid})
                    return
                ly_khong = _khong_phai_trang(dau)
                if ly_khong:
                    ts["khong_trang"], ts["ma_chan"] = ly_khong, ma
                    return _dung(rid)
                cdp.send("Fetch.continueRequest", {"requestId": rid})
            except Exception as e:                                                    # loi trong bo loc -> DONG (chan), khong de yeu cau treo hay di lung tung
                if isinstance(e, LN.HetNhip):
                    ts["het_nhip"] = e
                else:
                    ts["loi"] = ts["loi"] or _loi_ngan(e)
                _dung(rid)

        if truoc:
            truoc(url)                                          # NGOAI try: het nhip / het tran phai len cho bo quet dung, khong bi nuot thanh chuoi loi
        try:
            pg = self._ctx.new_page()
            cdp = self._ctx.new_cdp_session(pg)
            khung["id"] = cdp.send("Page.getFrameTree")["frameTree"]["frame"]["id"]
            cdp.on("Fetch.requestPaused", _xu_ly)
            cdp.send("Fetch.enable", {"patterns": [{"urlPattern": "*", "resourceType": "Document", "requestStage": g} for g in ("Request", "Response")]})
            rp = pg.goto(url, timeout=TIMEOUT_TRANG_MS, wait_until="domcontentloaded")
            try:
                pg.wait_for_load_state("networkidle", timeout=self.cho_ms)
            except Exception:
                pass
            pg.wait_for_timeout(1200)
            return self._ket_qua_render(ts, rp.status if rp else None, goc, pg, None)
        except Exception as e:
            return self._ket_qua_render(ts, None, goc, pg, e)
        finally:
            for doi_tuong, ham in ((cdp, "detach"), (pg, "close")):
                try:
                    if doi_tuong is not None:
                        getattr(doi_tuong, ham)()
                except Exception:
                    pass

    @staticmethod
    def _ket_qua_render(ts: dict, status, goc: str, pg, loi):
        """Gom ket qua mot lan mo tab: uu tien ly do DO TA CHAN (het nhip > ra ngoai > qua nhieu buoc > khong phai trang) hon loi cua trinh duyet."""
        if ts["het_nhip"] is not None:
            raise ts["het_nhip"]
        if ts["ra_ngoai"]:
            return ts["ma_chan"] or status, "", "chuyen huong ra ngoai: %s" % ts["ra_ngoai"]
        if ts["nhieu"]:
            return None, "", "qua nhieu lan chuyen huong"
        if ts["khong_trang"]:
            return ts["ma_chan"] or status, "", ts["khong_trang"]
        if ts["loi"]:
            return None, "", ts["loi"]
        if loi is not None:
            return None, "", _loi_ngan(loi)
        try:
            cuoi = pg.url
            if _mien(cuoi) != goc or not cuoi.startswith("https://"):             # luoi an toan thu hai: trang cuoi khong cung ten mien
                return status, "", "chuyen huong ra ngoai: %s" % cuoi
            return status, (pg.content() or "")[:LCH.TOI_DA_BYTE], ""
        except Exception as e:
            return None, "", _loi_ngan(e)


# ============================================================== 4. KHO UNG VIEN (may nha, gitignore)
class _Kho:
    """Ung vien cua MOT dien dan: tep JSONL, chi THEM URL moi (khong ghi de, khong xoa)."""

    def __init__(self, duong):
        self.duong = Path(duong)
        self._ds: list[dict] | None = None
        self._thay: set[str] = set()

    def doc_het(self) -> list[dict]:
        if self._ds is None:
            self._ds = []
            try:
                for dong in self.duong.read_text(encoding="utf-8").splitlines():
                    try:
                        m = json.loads(dong)
                        self._thay.add(m["k"])
                        self._ds.append(m)
                    except (ValueError, KeyError, TypeError):
                        continue
            except OSError:
                pass
        return self._ds

    def tong(self) -> int:
        return len(self.doc_het())

    def them(self, bai: list[dict], trang: int, luc: int) -> int:
        self.doc_het()
        moi = []
        for b in bai:
            k = _khoa_bai(b["url"])
            if k in self._thay:
                continue
            self._thay.add(k)
            moi.append({"k": k, "url": b["url"], "tieu_de": b["tieu_de"], "diem": diem_tieu_de(b["tieu_de"]), "trang": trang, "luc": luc})
        if moi:
            self.duong.parent.mkdir(parents=True, exist_ok=True)
            with self.duong.open("a", encoding="utf-8") as f:
                for m in moi:
                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
            self._ds.extend(moi)
        return len(moi)


# ============================================================== 5. QUET
class _Dien:
    """Tien trinh MOT dien dan trong MOT luot quet."""

    def __init__(self, cfg: dict, fo: dict, toi_da_trang: int | None = None):
        self.fo, self.ma, self.khoa = fo, fo["ma"], TIEN_TO + fo["ma"]
        self.cach = fo.get("cach_lay", "http")
        self.host = urlsplit(fo["url"]).hostname or ""
        self.mien = LN.mien_goc(self.host)
        self.toi_da_luot = int(toi_da_trang or _tham_so(cfg, fo, "toi_da_trang_luot"))
        self.toi_da_pass = int(_tham_so(cfg, fo, "toi_da_trang_pass"))
        self.chu_ky = float(_tham_so(cfg, fo, "chu_ky_gio"))
        self.do_dai = int(_tham_so(cfg, fo, "do_dai_tieu_de"))
        self.url, self.n, self.referer = fo["url"], 1, ""         # trang dau mo nhu mo tu thanh dia chi (khong Referer); sau do = trang truoc
        self.van_tay: list[str] = []
        self.tong_trang = self.trang_cuoi = self.da_lam = self.bai_moi = 0
        self.status = None
        self.xong, self.ket_qua, self.ly_do = False, "", ""


class Quet:
    """Doc dien dan co NHIP + robots.txt + trang thai noi lai. Moi phu thuoc ngoai (mang, Chrome, dong ho) tiem duoc de test."""

    def __init__(self, cfg=None, tt=None, nhip=None, lay=None, mo_cdp=None, thu_muc_ung_vien=None, thu_muc_reports=None, in_ra=print):
        self.cfg = cfg if cfg is not None else nap_cau_hinh()
        loi = kiem_cau_hinh(self.cfg)
        if loi:
            raise ValueError("config/dien_dan.json sai: " + "; ".join(loi[:5]))
        self.tt = tt or LN.TrangThai()
        self.nhip = nhip or LN.Nhip()
        self._lay = lay or LCH.lay_http
        self._mo_cdp = mo_cdp or PhienCdp
        self.robots = LN.Robots(self._lay_robots, ua=LCH.UA_ROBOTS)
        self.thu_muc_ung_vien = Path(thu_muc_ung_vien) if thu_muc_ung_vien else THU_MUC_UNG_VIEN
        self.thu_muc_reports = Path(thu_muc_reports) if thu_muc_reports else LAB / "reports"
        self.in_ra = in_ra
        self._delay: dict = {}
        self._nhip_cau_hinh: dict = {}                           # nhip_giay lon nhat theo ten mien (khong bao gio nhanh hon bang LN)
        for fo in self.cfg["dien_dan"]:
            if fo.get("nhip_giay"):
                m = _mien(fo["url"])
                self._nhip_cau_hinh[m] = max(self._nhip_cau_hinh.get(m, 0), float(fo["nhip_giay"]))
        self._kho: dict[str, _Kho] = {}
        self._st = None
        self._phien_cdp = None
        self._loi_cdp = ""

    # ---- nhip: MOI yeu cau (ke ca robots.txt va moi buoc chuyen huong) di qua day
    def _truoc(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        m = LN.mien_goc(host)
        self.nhip.doi(host, max(self._delay.get(m) or 0, self._nhip_cau_hinh.get(m, 0)) or None)
        self.tt.tinh_yeu_cau(host)

    def _lay_robots(self, url: str):
        return self._lay(url, truoc=self._truoc)

    def _tran_ngay(self, mien: str) -> int:
        md = self.cfg.get("mac_dinh") or {}
        return int((md.get("tran_ngay_theo_mien") or MAC_DINH["tran_ngay_theo_mien"]).get(mien)
                   or md.get("tran_ngay_mien") or MAC_DINH["tran_ngay_mien"])

    def _phien(self):
        if self._phien_cdp is None:
            if self._loi_cdp:
                raise KhongCoCdp(self._loi_cdp)
            try:
                self._phien_cdp = self._st.enter_context(self._mo_cdp())
            except KhongCoCdp as e:
                self._loi_cdp = str(e)
                raise
        return self._phien_cdp

    def _kho_cua(self, fo: dict) -> _Kho:
        if fo["ma"] not in self._kho:
            self._kho[fo["ma"]] = _Kho(self.thu_muc_ung_vien / ("%s.jsonl" % fo["ma"]))
        return self._kho[fo["ma"]]

    def _tt_muc(self, fo: dict, hau_to: str = "") -> dict:
        return self.tt.d["link"].get(TIEN_TO + fo["ma"] + hau_to, {})

    # ---- chon dien dan
    def _chon(self, ma_list, chi_bat: bool) -> tuple[list[dict], list[str]]:
        tat_ca = self.cfg["dien_dan"]
        muon = [m.strip() for m in (ma_list or []) if m.strip()]
        if not muon:
            return [fo for fo in tat_ca if fo.get("bat") or not chi_bat], []
        theo_ma = {fo["ma"]: fo for fo in tat_ca}
        return [theo_ma[m] for m in dict.fromkeys(muon) if m in theo_ma], [m for m in dict.fromkeys(muon) if m not in theo_ma]

    # ---- mot lan lay trang (dung chung cho quet va do)
    def _lay_mot(self, d: _Dien, url: str, het_trang_ok: bool = False):
        """-> (ket_qua, status, text, ly_do). ket_qua: OK | CHO | HET_NHIP | KHONG_CO_CHROME | CHUYEN_HUONG | CHAN_ROBOTS | CHAN_TAN_SUAT |
        CHAN_CAM | HET_TRANG | LOI_MAY_CHU | LOI_MANG. Loi that duoc ghi vao trang thai (nghi / lui nhip) o day; `HET_TRANG` khi
        `het_trang_ok` (trang N+1 cua mot danh sach da het) KHONG phai loi."""
        ok, ly = self.tt.thu_duoc(d.khoa, d.host, self._tran_ngay(d.mien))
        if not ok:
            return "CHO", None, "", ly
        try:
            phien = self._phien() if d.cach != "http" else None  # khong co Chrome thi khong cham mang (ke ca robots.txt)
            cho, ly = self.robots.cho_phep(url)
            if not cho:
                kq = "LOI_MANG" if ly.startswith("khong doc duoc") else "CHAN_ROBOTS"
                self._ghi(d, kq, ly_do=ly[:80])
                return kq, None, "", ly
            self._delay[d.mien] = self.robots.crawl_delay(url)
            if phien is None:
                status, text, loi = self._lay(url, truoc=self._truoc)
            else:
                status, text, loi = phien.lay(url, referer=d.referer, render=(d.cach == "cdp_render"), truoc=self._truoc)
        except LN.HetNhip as e:
            return "HET_NHIP", None, "", str(e)
        except KhongCoCdp as e:
            return "KHONG_CO_CHROME", None, "", str(e)
        if loi.startswith("chuyen huong ra ngoai: "):
            self._ghi(d, "CHUYEN_HUONG", status=status, den_han=int(self.tt.dh() + GIO_NGHI_LOI_CAU_HINH * 3600))
            return "CHUYEN_HUONG", status, "", "dien dan chuyen sang ten mien khac: sua `url` trong config (khong tu theo)"
        kq = LN.phan_loai_loi(status, text, loi)
        if kq == "HET_TRANG" and het_trang_ok:
            return kq, status, "", "HTTP %s" % status
        if kq != "OK":
            ly = LCH._cat(_khong_url(loi), 80) or ("HTTP %s" % status)
            self._ghi(d, kq, status=status, loi=ly)
            return kq, status, "", ly
        return "OK", status, text, ""

    def _ghi(self, d: _Dien, ket_qua: str, **them) -> None:
        """Ghi trang thai MOT dien dan; luon kem `url_goc` de biet moc / nghi cu con ap dung khong khi chu du an doi `url` trong config."""
        self.tt.ghi(d.khoa, d.host, ket_qua, url_goc=d.fo["url"], **them)

    @staticmethod
    def _dung(d: _Dien, ket_qua: str, ly: str) -> None:
        d.xong, d.ket_qua, d.ly_do = True, ket_qua, ly

    # ---- vao luot: cong tuan, noi tiep moc
    def _vao_luot(self, fo: dict, toi_da_trang, ep: bool) -> _Dien:
        d = _Dien(self.cfg, fo, toi_da_trang)
        if not fo.get("bat"):
            self._dung(d, "BO_QUA", "dang tat (`bat: false`); chay `b dien-dan do --ma %s` truoc khi bat" % d.ma)
            return d
        m = self._tt_muc(fo)
        if m and m.get("url_goc") not in (None, fo["url"]):      # chu du an doi `url`: moc, nghi va dem loi cu khong con ap dung
            m.update(den_trang=0, url_tiep="", den_han=0, thu_lai_sau=0, so_loi=0, dau_van_tay=[], trang_cuoi=0, tong_trang=0,
                     url_goc=fo["url"])
        d.trang_cuoi, d.tong_trang = int(m.get("trang_cuoi", 0)), int(m.get("tong_trang", 0))
        if not ep and int(m.get("den_han", 0)) > self.tt.dh():
            gio = LN._gio_text(m["den_han"])
            if m.get("ket_qua") == "XONG":
                self._dung(d, "CHO_TUAN", "da xong luot quet, mo lai luc %s (hoac --ep)" % gio)
            else:                                                # KHONG_CO_BAI / CHUYEN_HUONG: sai cau hinh, nghi 24 gio
                self._dung(d, "CHO_TUAN", "dang nghi den %s vi %s (sua config roi chay --ep)" % (gio, m.get("ket_qua", "loi")))
            return d
        ut, dt = str(m.get("url_tiep") or ""), int(m.get("den_trang", 0))
        if dt > 0 and ut.startswith("https://") and m.get("url_goc") == fo["url"] and _mien(ut) == d.mien:
            d.url, d.n, d.van_tay = ut, dt + 1, [str(x) for x in (m.get("dau_van_tay") or [])][-3:]
        return d

    def _het_pass(self, d: _Dien, ly: str, trang_cuoi: int, status) -> None:
        so_pass = int(self._tt_muc(d.fo).get("so_pass", 0)) + 1
        self._ghi(d, "XONG", status=status, den_trang=0, url_tiep="", tong_trang=d.tong_trang,
                  dau_van_tay=[], tien_do="XONG_PASS", trang_cuoi=trang_cuoi, so_pass=so_pass, ly_do=ly[:80],
                  den_han=int(self.tt.dh() + d.chu_ky * 3600), bai_tong=self._kho_cua(d.fo).tong())
        d.trang_cuoi = trang_cuoi
        self._dung(d, "XONG_PASS", ly)

    def _khong_thay_tiep(self, d: _Dien, tong: int, status) -> None:
        """Trang `d.n` doc xong (bai da ghi) nhung thanh phan trang ghi toi `tong` trang va ta khong tim duoc link trang ke. Day la LOI CAU HINH, khong phai
        'XONG': nghi 24 gio (khong dap lai), khong xoa moc 'da toi trang N' (so lan XONG_PASS khong tang), noi ro de chu du an / phien cloud sua `mau_trang`."""
        ly = "trang %d/%d nhung khong tim thay link trang %d (khai `mau_trang` cho dien dan nay, hoac `phan_trang: khong`)" % (d.n, tong, d.n + 1)
        self._ghi(d, "KHONG_THAY_TRANG_TIEP", status=status, den_trang=0, url_tiep="", tong_trang=d.tong_trang, dau_van_tay=[], tien_do="KHONG_THAY_TRANG_TIEP",
                  trang_cuoi=d.n, bai_tong=self._kho_cua(d.fo).tong(), ly_do=ly[:90], den_han=int(self.tt.dh() + GIO_NGHI_LOI_CAU_HINH * 3600))
        self._dung(d, "KHONG_THAY_TRANG_TIEP", ly)

    def _mot_trang(self, d: _Dien) -> None:
        if d.da_lam >= d.toi_da_luot:
            self._dung(d, "DANG_DO", "het %d trang / luot: lan sau doc tiep tu trang %d" % (d.toi_da_luot, d.n))
            return
        kq, status, text, ly = self._lay_mot(d, d.url, het_trang_ok=d.n > 1)
        d.status = status
        if kq == "HET_TRANG":
            if d.n > 1:
                self._het_pass(d, "het trang (HTTP %s o trang %d)" % (status, d.n), d.n - 1, status)
            else:                                                # trang 1 cung 404 / 410: URL sai hoac dien dan da dong (`_lay_mot` da ghi nghi 30 ngay)
                self._dung(d, "HET_TRANG", "trang 1 tra HTTP %s: sai `url`? nghi 30 ngay, sua config thi doc lai ngay" % status)
            return
        if kq == "HET_NHIP":
            self._dung(d, "DANG_DO", ly)
            return
        if kq != "OK":
            self._dung(d, kq, ly)
            return
        t = tach_trang(text, d.url)
        bai = trich_bai(d.fo, t, d.url, d.do_dai)
        vt = _van_tay(bai, t)
        if d.n > 1 and (not bai or vt in d.van_tay):
            self._het_pass(d, "trang trong" if not bai else "trang lap (phan trang khong tien)", d.n - 1, status)
            return
        if not bai:                                              # trang 1 khong co bai: sai mau_bai hoac trang can JS
            self._ghi(d, "KHONG_CO_BAI", status=status, kich_thuoc=len(text), den_han=int(self.tt.dh() + GIO_NGHI_LOI_CAU_HINH * 3600))
            self._dung(d, "KHONG_CO_BAI", "trang 1 khong co bai nao khop (sai mau_bai? trang can JS -> thu cdp_render?)")
            return
        d.bai_moi += self._kho_cua(d.fo).them(bai, d.n, int(self.tt.dh()))
        d.da_lam += 1
        d.trang_cuoi = d.n
        d.van_tay = (d.van_tay + [vt])[-3:]
        tm = tim_trang_tiep(d.fo, t, d.url, d.n + 1)
        tiep = tm["url"]
        d.tong_trang = max(d.tong_trang, d.n, tm["tong_uoc"])     # KHONG dung `so_trang`: link "2 3 .. 120" duoi tung chu de khong phai thanh phan trang cua danh sach
        ket = ""
        if not tiep:
            if tm["tong_uoc"] > d.n and d.fo.get("phan_trang", "auto") != "khong":   # thanh phan trang bao CON trang ma ta khong co duong sang: KHONG phai het
                self._khong_thay_tiep(d, tm["tong_uoc"], status)
                return
            ket = "het trang (khong thay trang tiep)"
        elif d.n >= d.toi_da_pass:
            ket = "cham tran %d trang / pass" % d.toi_da_pass
        elif LN.chuan_hoa_url(tiep) == LN.chuan_hoa_url(d.url):
            ket = "trang tiep tro lai chinh no"
        if ket:
            self._het_pass(d, ket, d.n, status)
            return
        self._ghi(d, "OK", status=status, den_trang=d.n, url_tiep=tiep, tong_trang=d.tong_trang, dau_van_tay=d.van_tay, tien_do="DANG_DO",
                  trang_cuoi=d.n, bai_tong=self._kho_cua(d.fo).tong(),
                  den_han=0)                                     # pass dang do: `den_han` cua pass truoc (--ep giua tuan) khong duoc chan luot sau
        d.referer, d.url, d.n = d.url, tiep, d.n + 1

    # ---- quet
    def chay(self, ma_list=None, toi_da_trang: int | None = None, ep: bool = False) -> dict:
        """Doc tiep cac dien dan (mac dinh chi cai `bat`; `ma_list` goi ten thi doc ca cai tat -> BO_QUA). XEN KE moi vong mot trang moi dien dan."""
        cac, khong_thay = self._chon(ma_list, chi_bat=True)
        ds = [self._vao_luot(fo, toi_da_trang, ep) for fo in cac]
        with contextlib.ExitStack() as st:
            self._st = st
            hoat = [d for d in ds if not d.xong]
            while hoat:
                for d in list(hoat):
                    self._mot_trang(d)
                    if d.xong:
                        hoat.remove(d)
        self._st, self._phien_cdp = None, None
        bc = self._bao_cao("quet", {d.ma: d for d in ds}, khong_thay)
        self.ghi_bao_cao(bc)
        return bc

    # ---- tham do
    def do(self, ma_list=None) -> dict:
        """Tham do 1 trang (+ trang 2 neu co cach phan trang) cua MOI dien dan dang chon (ke ca dien dan tat). Khong ghi moc, khong bat / tat gi."""
        cac, khong_thay = self._chon(ma_list, chi_bat=False)
        ket = {}
        with contextlib.ExitStack() as st:
            self._st = st
            for fo in cac:
                ket[fo["ma"]] = self._do_mot(fo)
        self._st, self._phien_cdp = None, None
        bc = {"luc": LN._gio_text(self.tt.dh()), "lenh": "do", "khong_thay": khong_thay, "dien_dan": [ket[fo["ma"]] for fo in cac]}
        LCH._ghi_json_nguyen_tu(self.thu_muc_reports / "dien_dan_do.json", LCH._vua_gioi_han(bc, ("dien_dan",)))
        return bc

    def _do_mot(self, fo: dict) -> dict:
        d = _Dien(self.cfg, fo, 1)
        d.khoa = TIEN_TO + fo["ma"] + "~do"                      # trang thai tham do tach khoi trang thai quet (khong lam sai moc)
        r = {"ma": d.ma, "nuoc": fo["nuoc"], "bat": bool(fo.get("bat")), "cach": d.cach}
        kq, status, text, ly = self._lay_mot(d, d.url)
        r.update(ket_qua=kq, status=status)
        if kq != "OK":
            r.update(ly_do=LCH._cat(ly, 90), goi_y=_goi_y(r))
            return r
        t = tach_trang(text, d.url)
        bai = trich_bai(fo, t, d.url, d.do_dai)
        tm = tim_trang_tiep(fo, t, d.url, 2)
        r.update(kich_thuoc=len(text), so_link=len(t["neo"]), so_bai=len(bai), rel_next=bool(t["rel_next"]),
                 tong_trang_uoc=tm["tong_uoc"], co_neo_so_khac=bool(t["so_trang"]) and not tm["tong_uoc"], mau_trang=bool(fo.get("mau_trang")),
                 cach_trang_tiep=tm["cach"])
        url2 = tm["url"]
        if url2 and bai:
            d.referer = d.url
            kq2, _, text2, _ = self._lay_mot(d, url2, het_trang_ok=True)
            if kq2 == "OK":
                t2 = tach_trang(text2, url2)
                bai2 = trich_bai(fo, t2, url2, d.do_dai)
                r["trang2"] = {"ket_qua": "OK", "so_bai": len(bai2), "khac_trang_1": bool(bai2) and _van_tay(bai2, t2) != _van_tay(bai, t)}
            else:
                r["trang2"] = {"ket_qua": kq2}
        self._ghi(d, "OK", status=status, so_bai=len(bai), do_luc=int(self.tt.dh()))
        r["goi_y"] = _goi_y(r)
        return r

    # ---- ke hoach (khong mang)
    def ke_hoach(self) -> list[dict]:
        ra, now = [], self.tt.dh()
        for fo in self.cfg["dien_dan"]:
            d = _Dien(self.cfg, fo)
            m = self._tt_muc(fo)
            r = {"ma": d.ma, "nuoc": fo["nuoc"], "cach": d.cach, "bat": bool(fo.get("bat")), "ket_qua": m.get("ket_qua", "CHUA_LAM"),
                 "den_trang": int(m.get("trang_cuoi", 0)), "tong_trang": int(m.get("tong_trang", 0)), "so_pass": int(m.get("so_pass", 0))}
            ok, ly = self.tt.thu_duoc(d.khoa, d.host, self._tran_ngay(d.mien))
            if not fo.get("bat"):
                r["buoc_tiep"] = "tat"
            elif int(m.get("den_han", 0)) > now:
                loi = m.get("ket_qua") not in (None, "OK", "XONG")
                r["buoc_tiep"] = ("cho den %s vi %s (sua config roi --ep)" % (LN._gio_text(m["den_han"]), m["ket_qua"])) if loi \
                    else "cho den %s (1 tuan / lan)" % LN._gio_text(m["den_han"])
            elif not ok:
                r["buoc_tiep"] = "cho: %s" % ly
            elif int(m.get("den_trang", 0)) > 0 and m.get("url_goc") == fo["url"] and m.get("url_tiep"):
                r["buoc_tiep"] = "doc tiep trang %d" % (int(m["den_trang"]) + 1)
            else:
                r["buoc_tiep"] = "doc tu trang 1"
            ra.append(r)
        return ra

    # ---- bao cao
    def _ban_ghi(self, fo: dict) -> dict:
        m = self._tt_muc(fo)
        return {"ma": fo["ma"], "nuoc": fo["nuoc"], "bat": bool(fo.get("bat")), "cach": fo.get("cach_lay", "http"),
                "ket_qua": m.get("ket_qua", "CHUA_LAM"), "tien_do": m.get("tien_do", "CHUA_LAM"), "status": m.get("status"),
                "den_trang": int(m.get("trang_cuoi", 0)), "tong_trang": int(m.get("tong_trang", 0)), "so_pass": int(m.get("so_pass", 0)),
                "bai_tong": int(m.get("bai_tong", 0)), "lan_cuoi": int(m.get("lan_cuoi", 0)), "den_han": int(m.get("den_han", 0))}

    def _id_tin_hieu(self, toi_da: int = 300) -> list[int]:
        ra: list[int] = []
        for fo in self.cfg["dien_dan"]:
            for m in reversed(self._kho_cua(fo).doc_het()):
                g = _RX_TIN_HIEU.search(m.get("url", ""))
                if g and int(g.group(1)) not in ra:
                    ra.append(int(g.group(1)))
                    if len(ra) >= toi_da:
                        return ra
        return ra

    def _bao_cao(self, lenh: str, luot: dict, khong_thay=()) -> dict:
        ban = []
        for fo in self.cfg["dien_dan"]:
            b = self._ban_ghi(fo)
            d = luot.get(fo["ma"])
            if d is not None:
                b.update(ket_qua_luot=d.ket_qua, ly_do=LCH._cat(d.ly_do, 90), trang_luot=d.da_lam, bai_moi=d.bai_moi)
            ban.append(b)
        nuoc: dict = {}
        for b in ban:
            n = nuoc.setdefault(b["nuoc"], {"dien_dan": 0, "bat": 0, "doc_duoc": 0})
            n["dien_dan"] += 1
            n["bat"] += 1 if b["bat"] else 0
            n["doc_duoc"] += 1 if (b["ket_qua"] in ("OK", "XONG") and b["lan_cuoi"]) else 0
        tom_tat: dict = {}
        for d in luot.values():
            tom_tat[d.ket_qua] = tom_tat.get(d.ket_qua, 0) + 1
        return {"luc": LN._gio_text(self.tt.dh()), "lenh": lenh, "tong_dien_dan": len(ban), "dang_bat": sum(1 for b in ban if b["bat"]),
                "tom_tat_luot": tom_tat, "khong_thay_ma": list(khong_thay), "nuoc": nuoc,
                "nuoc_chua_doc_duoc": sorted(k for k, v in nuoc.items() if not v["doc_duoc"]),
                "chua_co_ung_vien": list(self.cfg.get("nuoc_chua_co_ung_vien") or []),
                "tin_hieu_mql5": self._id_tin_hieu(), "dien_dan": ban}

    def bao_cao(self) -> dict:
        """Dung lai bao cao tu trang thai (khong mang)."""
        bc = self._bao_cao("bao-cao", {})
        self.ghi_bao_cao(bc)
        return bc

    def ghi_bao_cao(self, bc: dict) -> dict:
        bc = LCH._vua_gioi_han(bc, ("tin_hieu_mql5", "dien_dan"))
        LCH._ghi_json_nguyen_tu(self.thu_muc_reports / BAO_CAO_JSON.name, bc)
        LN._ghi_gioi_han(self.thu_muc_reports / BAO_CAO_MD.name, bao_cao_van_ban(bc) + "\n")
        return bc


def _goi_y(r: dict) -> str:
    """Goi y bang loi thuong cho ket qua tham do (chu du an / phien cloud doc de quyet bat hay tat)."""
    kq = r.get("ket_qua")
    if kq == "KHONG_CO_CHROME":
        return "can Chrome AI (mo_trinh_duyet_ai.cmd, cong %d): bat len roi do lai" % CDP_CONG
    if kq in ("CHAN_CAM", "CHAN_TAN_SUAT", "CHAN_ROBOTS"):
        return "bi chan (%s): giu tat. Chi thu bang Chrome AI (cach_lay=cdp) MOT lan; bi chan nua thi bo, khong ne" % kq
    if kq == "CHO":
        return "dang nghi / het tran ngay: do lai sau"
    if kq == "CHUYEN_HUONG":
        return "dien dan da chuyen ten mien: sua `url` trong config roi do lai"
    if kq != "OK":
        return "loi %s: do lai sau; neu lap lai thi bo" % kq
    if r.get("so_bai", 0) < 3:
        return "it bai (%d): sai mau_bai hoac trang can JS -> thu cach_lay=cdp_render; chua nen bat" % r.get("so_bai", 0)
    t2 = r.get("trang2")
    if not t2:
        if r.get("tong_trang_uoc", 0) > 1:
            return ("trang bao co %d trang nhung KHONG tim thay link trang 2 (se bao KHONG_THAY_TRANG_TIEP, khong phai het): "
                    "them mau_trang, hoac dat phan_trang=khong" % r["tong_trang_uoc"])
        if r.get("co_neo_so_khac"):
            return ("doc duoc trang 1 (%d bai); co link danh so trang nhung khong cung duong dan voi `url` (dien dan chuyen huong? dat `url` la dia chi cuoi cung; "
                    "link duoi tung chu de thi bo qua): them mau_trang hoac dat phan_trang=khong" % r["so_bai"])
        return "doc duoc trang 1 (%d bai) nhung chua thay cach sang trang: them mau_trang hoac dat phan_trang=khong" % r["so_bai"]
    if t2.get("ket_qua") == "OK":
        if t2.get("khac_trang_1"):
            return "dung duoc: dat bat=true (%d bai o trang 1, co phan trang, cach sang trang: %s)" % (r["so_bai"], r.get("cach_trang_tiep") or "?")
        return "trang 2 giong trang 1 hoac khong co bai: mau_trang sai -> sua hoac dat phan_trang=khong (chi doc trang 1)"
    if t2.get("ket_qua") == "HET_TRANG":
        return "trang 2 khong ton tai (404): dien dan chi co 1 trang hoac mau_trang sai - xem lai truoc khi bat"
    return "trang 1 doc duoc (%d bai) nhung trang 2 chua do duoc (%s): do lai truoc khi bat" % (r["so_bai"], t2.get("ket_qua"))


def bao_cao_van_ban(bc: dict) -> str:
    dong = ["# Dien dan / danh sach nhieu trang - %s (%s)" % (bc.get("luc", ""), bc.get("lenh", "")),
            "", "%d dien dan trong config, %d dang bat." % (bc.get("tong_dien_dan", 0), bc.get("dang_bat", 0))]
    if bc.get("tom_tat_luot"):
        dong.append("Luot nay: " + ", ".join("%s %d" % (k, v) for k, v in sorted(bc["tom_tat_luot"].items())) + ".")
    ok = sorted(k for k, v in (bc.get("nuoc") or {}).items() if v["doc_duoc"])
    dong.append("Nuoc DA doc duoc it nhat mot dien dan: %s." % (", ".join(ok) or "chua co"))
    thieu = bc.get("nuoc_chua_doc_duoc") or []
    dong.append("Nuoc co dien dan trong config nhung CHUA doc duoc: %s." % (", ".join(thieu) or "khong"))
    dong.append("Nuoc chua co ung vien nao (can tim): %s." % (", ".join(bc.get("chua_co_ung_vien") or []) or "khong"))
    if bc.get("tin_hieu_mql5"):
        dong.append("ID tin hieu MQL5 moi tim thay: %d (xem JSON)." % len(bc["tin_hieu_mql5"]))
    dong += ["", "| ma | nuoc | cach | bat | ket qua | den trang | bai |", "|---|---|---|---|---|---|---|"]
    for b in bc.get("dien_dan", []):
        tong = ("/%d" % b["tong_trang"]) if b.get("tong_trang") else ""
        dong.append("| %s | %s | %s | %s | %s | %s%s | %s |" % (
            b["ma"], b["nuoc"], b["cach"], "x" if b["bat"] else "", b.get("ket_qua_luot") or b.get("ket_qua", ""),
            b.get("den_trang", 0), tong, b.get("bai_tong", 0)))
    return "\n".join(dong)


# ============================================================== 6. CLI (b dien-dan ...)
def _in_ke_hoach(kh: list[dict], in_ra=print) -> None:
    bat = sum(1 for r in kh if r["bat"])
    in_ra("dien dan: %d trong config, %d dang bat" % (len(kh), bat))
    for r in kh:
        if r["bat"] or r["den_trang"]:
            tien = ("trang %d%s" % (r["den_trang"], ("/%d" % r["tong_trang"]) if r["tong_trang"] else "")) if r["den_trang"] else "chua doc"
            in_ra("  %-20s %-3s %-10s %-11s %s -> %s" % (r["ma"], r["nuoc"], r["cach"], r["ket_qua"], tien, r["buoc_tiep"]))
    tat = [r["ma"] for r in kh if not r["bat"]]
    if tat:
        in_ra("  dang tat (%d): %s" % (len(tat), ", ".join(tat)))


#: ket qua luot can NGUOI / cloud sua cau hinh: dien dan van khong doc sau duoc nen doc xong trang 1 cung KHONG tinh la tien
_KQ_CAU_HINH = frozenset(("KHONG_THAY_TRANG_TIEP", "KHONG_CO_BAI", "CHUYEN_HUONG", "HET_TRANG", "BO_QUA", "KHONG_CO_CHROME"))
#: ket qua luot do bi chan / loi mang (tam thoi): trang da doc truoc khi bi chan van tinh la tien
_KQ_CHAN = frozenset(("CHAN_ROBOTS", "CHAN_TAN_SUAT", "CHAN_CAM", "LOI_MANG", "LOI_MAY_CHU"))
_KQ_KHONG_TIEN = _KQ_CAU_HINH | _KQ_CHAN


def _luot_khong_tien(bc: dict) -> str:
    """'' neu luot quet co tien; nguoc lai MOT dong ly do. Co tien = it nhat mot dien dan xong mot pass, hoac doc >= 1 trang ma khong roi vao loi cau hinh;
    hoac cac dien dan chi dang CHO (CHO_TUAN, CHO, DANG_DO 0 trang) - binh thuong, KHONG phai loi. Don quet ma thoat 0 trong khi moi dien dan deu
    loi / bi tat / khong di tiep duoc la don 'DAT' gia (do 08/10/2026: 6/8 don quet-sau bao DAT du dien dan dang tat o may nha; 2/8 chi doc 1 trang roi 'XONG')."""
    ban = [b for b in bc.get("dien_dan", []) if "ket_qua_luot" in b]
    if not ban:
        return "khong dien dan nao duoc chon (tat het? xem `b dien-dan ke-hoach`)"
    if any(b["ket_qua_luot"] == "XONG_PASS" or (b.get("trang_luot", 0) > 0 and b["ket_qua_luot"] not in _KQ_CAU_HINH) for b in ban):
        return ""
    if not any(b["ket_qua_luot"] in _KQ_KHONG_TIEN for b in ban):
        return ""
    dem: dict[str, int] = {}
    for b in ban:
        dem[b["ket_qua_luot"]] = dem.get(b["ket_qua_luot"], 0) + 1
    return "khong dien dan nao doc tiep duoc: " + ", ".join("%s %d" % kv for kv in sorted(dem.items()))


def main(argv=None, tao_quet=None) -> int:
    ap = argparse.ArgumentParser(prog="b dien-dan", description="Doc dien dan / danh sach nhieu trang (chi doc; nho 'den trang N'; 1 tuan / lan)")
    ap.add_argument("lenh", choices=("ke-hoach", "do", "quet", "bao-cao"))
    ap.add_argument("--ma", default="", help="ma dien dan trong config/dien_dan.json (nhieu ma cach nhau bang phay)")
    ap.add_argument("--toi-da-trang", type=int, default=0, help="so trang toi da MOI dien dan trong luot nay (mac dinh theo config)")
    ap.add_argument("--ep", action="store_true", help="bo qua cho 1 tuan / lan (van ton trong nghi sau loi, robots.txt, nhip, tran ngay)")
    a = ap.parse_args(argv)
    try:
        q = (tao_quet or Quet)()
    except (ValueError, OSError) as e:
        print("!! %s" % LCH._cat(e, 400))
        return 2
    ma = [m for m in a.ma.split(",") if m.strip()]
    if a.lenh == "ke-hoach":
        _in_ke_hoach(q.ke_hoach())
        return 0
    if a.lenh == "bao-cao":
        bc = q.bao_cao()
        print("bao cao: %d dien dan, %d bat, nuoc da doc duoc: %s -> reports/%s" % (
            bc["tong_dien_dan"], bc["dang_bat"], ",".join(k for k, v in bc["nuoc"].items() if v["doc_duoc"]) or "chua co", BAO_CAO_MD.name))
        return 0
    if a.lenh == "do":
        bc = q.do(ma)
        for r in bc["dien_dan"]:
            print("  %-20s %-3s %-10s %-14s bai=%s  %s" % (r["ma"], r["nuoc"], r["cach"], r["ket_qua"], r.get("so_bai", "-"), r["goi_y"]))
    else:
        bc = q.chay(ma, toi_da_trang=a.toi_da_trang or None, ep=a.ep)
        for b in bc["dien_dan"]:
            if "ket_qua_luot" in b:
                tong = ("/%d" % b["tong_trang"]) if b["tong_trang"] else ""
                print("  %-20s %-3s %-16s %d trang luot nay, den trang %d%s, +%d bai%s" % (
                    b["ma"], b["nuoc"], b["ket_qua_luot"], b["trang_luot"], b["den_trang"], tong, b["bai_moi"],
                    ("  (" + b["ly_do"] + ")") if b.get("ly_do") and b["ket_qua_luot"] not in ("DANG_DO", "XONG_PASS") else ""))
        xau = ["%s(%s)" % (b["ma"], b["ket_qua_luot"]) for b in bc["dien_dan"] if b.get("ket_qua_luot") in _KQ_KHONG_TIEN]
        if xau:
            print("!! %d dien dan khong tien duoc: %s" % (len(xau), ", ".join(xau)))
        print("-> reports/%s (URL + tieu de bai nam o du_lieu_cao/dien_dan/, khong len git)" % BAO_CAO_MD.name)
    if bc.get("khong_thay_ma"):
        print("!! khong co ma dien dan: %s" % ", ".join(bc["khong_thay_ma"]))
        return 3
    if a.lenh == "quet":
        ly = _luot_khong_tien(bc)
        if ly:
            print("!! DIEN_DAN_KHONG_TIEN: %s" % ly)
            return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
