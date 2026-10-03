# -*- coding: utf-8 -*-
"""link_chay.py - CHAY THAT cho `link_nguon`: tham do trang, nap thu muc tha_vao, thu hoach tai khoan xem, CLI `b link`.

`link_nguon.py` biet link LA GI va LAY BANG CACH NAO (ham thuan). Module nay la tay chan: goi mang (co nhip, robots.txt, lui khi bi chan),
doc tep chu du an tha vao, keo lich su qua tai khoan XEM (investor password) -> lenh -> CSV de `b nc cc boc_lich_su` bong tach luat.

## Bon duong vao lich su lenh (muc tieu cuoi: lich su lenh -> hieu luat -> lam lai -> thu -> chinh)

  A. `tham_do` / `chay_mau`   link cong khai (MQL5, GitHub...) -> tom tat CAU TRUC trang (tab, bang, diem cuoi XHR). KHONG cao du lieu:
                              muc dich la de phien cloud viet bo doc DUNG dinh dang trang that (cloud khong toi duoc cac trang nay).
                              `--cdp`: dung Chrome chu du an da dang nhap (trang JS / bi chan bot) va bam thu tab lich su de bat XHR.
  B. `nap_thu_muc`            tep chu du an luu tay vao `du_lieu_cao/tha_vao/`: bao cao MT4/MT5 (.htm/.csv), tin nhan Facebook/Zalo/Telegram
                              (.txt, .html luu trang, .json xuat Telegram Desktop), .zip, EA nguon/.set. Lenh -> `du_lieu_cao/lenh/*.csv`.
  C. `nap_van_ban`            tin nhan dan thang: link vao `link_rieng.txt`, tai khoan XEM vao kho passview (gitignore).
  D. `thu_hoach_passview`     dang nhap CHI DOC (investor) bang tai khoan da luu -> history deals -> lenh -> `du_lieu_cao/lenh/*.csv`.

## Hai luat cung (xem `link_nguon.py`)

* Moi thu cao ve nam trong `du_lieu_cao/` (gitignore). Bao cao di xa (`reports/`) CHI co ma bam, nen tang, loai, so dem - khong URL rieng,
  khong ten tep, khong nhan, khong tai khoan, khong mat khau, khong noi dung tin nhan. In ra man hinh cung vay (don co the chay tu xa:
  dau ra tro ve cloud).
* Khong ne chan: UA that, khong cookie, khong doi IP; 429/403/captcha -> ten mien nghi (15 phut x 2^n ... 24 gio); robots.txt cam -> khong cao.
  Hai chieu chuyen huong khac ten mien KHONG duoc di theo: ghi lai dich den (link rut gon) de phan loai o luot sau.

## Chua chay that (noi that)

Moi duong mang / Chrome / MT5 o day chi duoc test bang bo gia (fetch, dong ho, MT5 gia deu tiem duoc). Lan dau chay tren may nha la lan
do that; ket qua dau tien (tom tat cau truc) la dau vao de viet bo doc dung dinh dang - day KHONG phai bo cao lich su hoan chinh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

from nhan import link_nguon as LN  # noqa: E402

UA = "TheBrainLab/1.0 (nghien cuu ca nhan, toc do thap, khong gia nguoi)"
UA_ROBOTS = "TheBrainLab"
TOI_DA_BYTE = 2_000_000
TOI_DA_TEP_BYTE = 60_000_000
THU_MUC_LENH = LN.THU_MUC_CAO / "lenh"
THU_MUC_TOM_TAT = LN.THU_MUC_CAO / "tom_tat"
MANIFEST = LN.THU_MUC_CAO / "tha_vao_manifest.json"
GOI_Y_TELEGRAM = LN.THU_MUC_CAO / "goi_y_telegram.txt"
BAO_CAO_CHAY_JSON = LAB / "reports" / "link_chay_ket_qua.json"
BAO_CAO_CHAY_MD = LAB / "reports" / "link_chay_ket_qua.md"
BAO_CAO_NAP_JSON = LAB / "reports" / "link_nap_ket_qua.json"
BAO_CAO_NAP_MD = LAB / "reports" / "link_nap_ket_qua.md"
BAO_CAO_TK_JSON = LAB / "reports" / "link_tai_khoan_xem.json"
GIOI_HAN_BAO_CAO = 38_000

#: nen tang khong bao gio tu dong cao (xem link_nguon): chu du an dan chu / luu trang
KHONG_TU_DONG = ("noi_bo", "facebook", "zalo", "discord", "whatsapp", "kho_tep")


def _cat(s, n: int = 120) -> str:
    """Chuoi loi / ten bat ky -> ban AN TOAN de in / ghi bao cao: che email va so dai (so tai khoan)."""
    return LN._bo_pii(re.sub(r"[A-Za-z]:\\[^\s]*|/[^\s]*/[^\s]*", "<duong>", str(s)), n)


def _sha(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def _ghi_json_nguyen_tu(duong: Path, d) -> None:
    duong.parent.mkdir(parents=True, exist_ok=True)
    tam = duong.with_name(duong.name + ".tmp")
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tam, duong)


def _co(x) -> int:
    return len(json.dumps(x, ensure_ascii=False))


def _vua_gioi_han(d: dict, khoa_cat: tuple, toi_da: int = GIOI_HAN_BAO_CAO) -> dict:
    """Cat dan `d` cho den khi JSON <= `toi_da` ky tu (tep gui ve cloud <= 40.000): truoc het cat doi cac danh sach (theo thu tu
    `khoa_cat`), con qua lon thi thay khoa lon nhat bang chuoi JSON bi cat. Luon tra ve dict hop le, danh dau `da_cat`."""
    d = dict(d)
    for k in khoa_cat:
        while _co(d) > toi_da and isinstance(d.get(k), list) and d[k]:
            d[k] = d[k][:max(0, len(d[k]) // 2)]
            d["da_cat"] = True
    while _co(d) > toi_da:
        k = max((x for x in d if x != "da_cat"), key=lambda x: _co(d[x]), default=None)
        if k is None:
            break
        s = d[k] if isinstance(d[k], str) else json.dumps(d[k], ensure_ascii=False)
        if len(s) <= 200:
            break
        d[k] = s[:max(100, len(s) // 2)] + "...(cat)"
        d["da_cat"] = True
    return d


def _che_bi_mat(s, *bi_mat) -> str:
    """Thay moi lan xuat hien CHINH XAC cua so tai khoan / mat khau / may chu bang <an> (loi cua MT5 co the lap lai chinh chung)."""
    s = str(s)
    for b in sorted({str(x) for x in bi_mat if x not in (None, "") and len(str(x)) >= 4}, key=len, reverse=True):
        s = re.sub(re.escape(b), "<an>", s, flags=re.I)
    return s


# ============================================================== 1. LAY TRANG (HTTP that + Chrome CDP)
def _mot_buoc_that(url: str, ua: str, timeout: float, toi_da_byte: int):
    """MOT yeu cau GET (khong tu theo chuyen huong, khong cookie) -> (status | None, header[chu thuong], body bytes, loi)."""
    import requests
    h = {"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.5",
         "Accept-Language": "en;q=0.8,vi;q=0.6", "Accept-Encoding": "gzip, deflate"}      # KHONG co `br` (khong co brotli -> rac)
    try:
        r = requests.get(url, headers=h, timeout=timeout, allow_redirects=False, stream=True)
    except requests.RequestException as e:
        return None, {}, b"", "%s: %s" % (type(e).__name__, str(e)[:100])
    try:
        dau = {k.lower(): v for k, v in r.headers.items()}
        buf = bytearray()
        for khuc in r.iter_content(65536):
            buf += khuc
            if len(buf) > toi_da_byte:
                break
        return r.status_code, dau, bytes(buf[:toi_da_byte]), ""
    except requests.RequestException as e:
        return r.status_code, {}, b"", "%s: %s" % (type(e).__name__, str(e)[:100])
    finally:
        r.close()


def _giai_ma_text(body: bytes, dau: dict) -> str:
    m = re.search(r"charset=([\w\-]+)", str(dau.get("content-type", "")), re.I)
    for enc in ([m.group(1)] if m else []) + ["utf-8"]:
        try:
            return body.decode(enc, errors="replace")
        except LookupError:
            continue
    return body.decode("utf-8", errors="replace")


def _url_de_tai(url: str) -> str:
    """URL chuan hoa (bo www + bo /en) chi de SO SANH. MQL5 that: `mql5.com/signals/N` -> 301 -> `www.mql5.com/signals/N` -> 404;
    chi `www.mql5.com/en/signals/N` moi ra 200 (do o may nha 03/10)."""
    p = urlsplit(url)
    if LN.mien_goc(p.hostname or "") != "mql5.com":
        return url
    path = p.path if re.match(r"^/[a-z]{2}(?=/|$)", p.path) else "/en" + p.path
    return urlunsplit((p.scheme, "www.mql5.com", path, p.query, ""))


def lay_http(url: str, ua: str = UA, timeout: float = 20.0, toi_da_byte: int = TOI_DA_BYTE, mot_buoc=None,
             toi_da_chuyen: int = 3, truoc=None):
    """GET don gian -> (status | None, text, loi).

    * Chuyen huong chi duoc theo khi cung ten mien goc VA https; khac ten mien -> dung, `loi = "chuyen huong ra ngoai: <url>"`
      (khong yeu cau toi dich: de nguoi goi phan loai dich roi quyet). Khong bao gio toi dia chi noi bo.
    * `truoc(url)` goi TRUOC moi yeu cau (ke ca moi buoc chuyen huong): cho nhip / dem tran. No co the nem `HetNhip`.
    * `mot_buoc(url, ua, timeout, toi_da_byte)` tiem duoc de test; mac dinh la `requests.get` that."""
    buoc = mot_buoc or _mot_buoc_that
    goc = LN.mien_goc(urlsplit(url).hostname or "")
    u = _url_de_tai(url)
    for _ in range(toi_da_chuyen + 1):
        if truoc:
            truoc(u)
        status, dau, body, loi = buoc(u, ua, timeout, toi_da_byte)
        if status in (301, 302, 303, 307, 308) and dau.get("location"):
            nx = urljoin(u, dau["location"])
            p = urlsplit(nx)
            if p.scheme != "https" or LN.mien_goc(p.hostname or "") != goc or LN.phan_loai(nx)["nen_tang"] == "noi_bo":
                return status, "", "chuyen huong ra ngoai: %s" % nx
            u = nx
            continue
        return status, _giai_ma_text(body, dau), loi
    return None, "", "qua nhieu lan chuyen huong"


_RX_TAB_LICH_SU = re.compile(r"^(?:trading\s+)?(?:history|trade\s*history|orders|deals|closed\s*(?:trades|positions)|lich\s*su.*)$", re.I)


def lay_cdp_that(url: str, truoc=None, port=None, cho_ms: int = 14000, mo_tab: bool = True, toi_da_html: int = TOI_DA_BYTE) -> dict:
    """Mo trang bang Chrome chu du an DA BAT CDP (khong tu mo trinh duyet moi) -> {status, html, xhr, tab_lich_su, loi}.

    `xhr` chi la TEN duong goi mang (khong gia tri, khong than tra ve); `tab_lich_su` = HTML sau khi bam thu tab "History / Trading
    history / Orders..." + cac XHR moi sinh ra: day la cho tim ra diem cuoi that cua bang lenh. CHUA CHAY THAT o cloud (khong co Chrome).
    Mang cua Chrome la mang cua chu du an, nen van di qua `truoc` (nhip / tran ngay) giong HTTP."""
    from nhan import doc_trinh_duyet as DT
    kq = {"status": None, "html": "", "xhr": [], "tab_lich_su": [], "loi": ""}
    url = _url_de_tai(url)                       # cung loi 404 gia nhu HTTP: `mql5.com/signals/N` (khong www, khong /en) -> 404 ca trong Chrome
    cong = port or DT.cdp_dang_chay()
    if not cong:
        kq["loi"] = "khong_mo_cdp"
        return kq
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        kq["loi"] = "khong_co_playwright"
        return kq
    try:
        if truoc:
            truoc(url)
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp("http://127.0.0.1:%d" % cong)
            ctx = b.contexts[0] if b.contexts else b.new_context()
            DT._don_tab(ctx)
            pg = ctx.new_page()
            xhr: list = []

            def _ghi_xhr(rq):
                if rq.resource_type in ("xhr", "fetch") and len(xhr) < 200:
                    xhr.append(rq.url)

            pg.on("request", _ghi_xhr)
            try:
                rp = pg.goto(url, timeout=min(cho_ms + 3000, 40000), wait_until="domcontentloaded")
                kq["status"] = rp.status if rp else None
                try:
                    pg.wait_for_load_state("networkidle", timeout=cho_ms)
                except Exception:
                    pass
                pg.wait_for_timeout(1200)
                kq["html"] = (pg.content() or "")[:toi_da_html]
                kq["xhr"] = list(dict.fromkeys(xhr))
                if mo_tab:
                    n0 = len(xhr)
                    for loc in (pg.get_by_role("tab", name=_RX_TAB_LICH_SU), pg.get_by_role("link", name=_RX_TAB_LICH_SU),
                                pg.get_by_text(_RX_TAB_LICH_SU)):
                        try:
                            if loc.count() == 0:
                                continue
                            loc.first.click(timeout=4000)
                            try:
                                pg.wait_for_load_state("networkidle", timeout=cho_ms)
                            except Exception:
                                pass
                            pg.wait_for_timeout(1500)
                            kq["tab_lich_su"].append({"html": (pg.content() or "")[:toi_da_html],
                                                      "xhr": list(dict.fromkeys(xhr[n0:]))})
                            break
                        except Exception:
                            continue
                    if not kq["tab_lich_su"] and LN.mien_goc(urlsplit(url).hostname or "") == "mql5.com":
                        try:                     # MQL5 doi tab bang phan neo `#!tab=...`, khong chac co chu "History" de bam: dat phan neo roi nap lai
                            n1 = len(xhr)
                            pg.evaluate("location.hash = '#!tab=history'")
                            pg.wait_for_timeout(1500)
                            if len(xhr) == n1:
                                pg.reload(timeout=min(cho_ms + 3000, 40000), wait_until="domcontentloaded")
                            try:
                                pg.wait_for_load_state("networkidle", timeout=cho_ms)
                            except Exception:
                                pass
                            pg.wait_for_timeout(1500)
                            kq["tab_lich_su"].append({"html": (pg.content() or "")[:toi_da_html],
                                                      "xhr": list(dict.fromkeys(xhr[n1:]))})
                        except Exception:
                            pass
            except Exception as e:
                kq["loi"] = "%s: %s" % (type(e).__name__, str(e)[:100])
            finally:
                try:
                    pg.close()
                except Exception:
                    pass
    except LN.HetNhip:
        raise
    except Exception as e:
        kq["loi"] = "%s: %s" % (type(e).__name__, str(e)[:100])
    return kq


# ============================================================== 2. THAM DO MOT TRANG
_RX_TOKEN_DAI = re.compile(r"^[A-Za-z0-9_\-+/=]{28,}$")


def _gia_tri_mau(v, sau: int = 0):
    """Gia tri mau an toan cho tom tat JSON: so / chu ngan giu nguyen (de thay DINH DANG gio, gia), chuoi giong token / email bi che."""
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, (int, float)):
        return v
    s = str(v)
    if LN._RX_EMAIL.search(s):
        return "<email>"
    if _RX_TOKEN_DAI.match(s):
        return "<chuoi_dai_giong_token>"
    return s[:48]


def _tom_tat_json(j, sau: int = 0, toi_da_khoa: int = 40):
    """JSON -> cau truc (kieu + khoa + 1-2 hang mau). Dung khi diem cuoi XHR tra JSON (bang lenh thuong nam o day)."""
    if sau > 4:
        return "<sau>"
    if isinstance(j, dict):
        return {str(k)[:40]: _tom_tat_json(v, sau + 1) for k, v in list(j.items())[:toi_da_khoa]}
    if isinstance(j, list):
        return {"kieu": "list", "so_phan_tu": len(j), "mau": [_tom_tat_json(x, sau + 1) for x in j[:2]]}
    return _gia_tri_mau(j)


def _tom_tat_noi_dung(text: str, url: str) -> dict:
    """Noi dung tra ve (HTML hoac JSON) -> tom tat cau truc."""
    t = str(text or "")
    if t.lstrip()[:1] in ("{", "["):
        try:
            return {"url": LN.rut_diem_cuoi(url), "kieu": "json", "kich_thuoc": len(t), "cau_truc": _tom_tat_json(json.loads(t))}
        except ValueError:
            pass
    d = LN.tom_tat_cau_truc(t, url)
    d["kieu"] = "html"
    ps = LN.phan_bo_symbol(d.get("bang"))
    if ps:
        d["phan_bo_symbol"] = ps
    return d


def _tab_tom_tat(t: dict, url: str) -> dict:
    """Mot tab lich su sau khi bam: chi giu bang + tieu de + xhr (phan con lai da co o trang chinh)."""
    d = LN.tom_tat_cau_truc(t.get("html", ""), url)
    return {"bang": d["bang"], "muc": d["muc"][:8], "diem_cuoi": d["diem_cuoi"][:20],
            "xhr_sau_khi_bam": [LN.rut_diem_cuoi(x) for x in t.get("xhr", [])][:60]}


class Chay:
    """Chay tham do co NHIP + robots.txt + trang thai noi lai. Moi phu thuoc ngoai (mang, Chrome, dong ho) deu tiem duoc de test."""

    def __init__(self, tt=None, nhip=None, lay=None, lay_cdp=None, duong_link=None, thu_muc_tom_tat=None,
                 thu_muc_reports=None, in_ra=print):
        self.tt = tt or LN.TrangThai()
        self.nhip = nhip or LN.Nhip()
        self._lay = lay or lay_http
        self._lay_cdp = lay_cdp or lay_cdp_that
        self.robots = LN.Robots(self._lay_robots, ua=UA_ROBOTS)
        self.duong_link = duong_link
        self.thu_muc_tom_tat = Path(thu_muc_tom_tat) if thu_muc_tom_tat else THU_MUC_TOM_TAT
        self.thu_muc_reports = Path(thu_muc_reports) if thu_muc_reports else LAB / "reports"
        self.in_ra = in_ra
        self._delay: dict = {}

    # ---- nhip: MOI yeu cau (ke ca robots.txt va moi buoc chuyen huong) di qua day
    def _truoc(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        self.nhip.doi(host, self._delay.get(LN.mien_goc(host)))
        self.tt.tinh_yeu_cau(host)

    def _lay_robots(self, url: str):
        return self._lay(url, truoc=self._truoc)

    # ---- danh sach link
    def muc_day_du(self) -> list[dict]:
        """`link_rieng.txt` + dich den da giai ma cua link rut gon (nho trong trang thai) - de luot sau cao ca link dich."""
        muc = LN.doc_link_rieng(self.duong_link)
        thay = {m["ma"] for m in muc}
        for m in list(muc):
            d = self.tt.d["link"].get(m["ma"], {}).get("dich_url")
            if d:
                n = LN.phan_loai(d)
                if n["ma"] not in thay and n["nen_tang"] != "rut_gon":
                    thay.add(n["ma"])
                    muc.append(n)
        return muc

    # ---- mot link
    def tham_do(self, m: dict, cdp: bool | None = None) -> dict:
        """Mot link da phan loai -> ket qua (khong nem loi mang). Ghi trang thai; tom tat cau truc ghi o `_ghi_tom_tat`."""
        ma, url = m["ma"], m["url"]
        host = urlsplit(url).hostname or ""
        dung_cdp = (m["cach_lay"] == "cdp") if cdp is None else bool(cdp)
        khoa = ma if (not dung_cdp or m["cach_lay"] == "cdp") else ma + "~cdp"        # trang thai CDP tach khoi HTTP khi cach chinh la http
        r = {"ma": ma, "khoa": khoa, "nen_tang": m["nen_tang"], "loai": m["loai"], "rieng": bool(m["rieng"]),
             "cach": "cdp" if dung_cdp else "http", "url": url}
        if m["nen_tang"] in KHONG_TU_DONG or m["cach_lay"] in ("thu_cong", "khong_ho_tro", "telethon"):
            return dict(r, ket_qua="BO_QUA", ly_do="khong tu dong duoc (%s): dan chu / luu trang vao du_lieu_cao/tha_vao/" % m["nen_tang"])
        ok, ly = self.tt.thu_duoc(khoa, host)
        if not ok:
            return dict(r, ket_qua="CHO", ly_do=ly)
        try:
            cho, ly = self.robots.cho_phep(url)
            if not cho:
                kq = "LOI_MANG" if ly.startswith("khong doc duoc") else "CHAN_ROBOTS"
                self.tt.ghi(khoa, host, kq, ly_do=ly[:80])
                return dict(r, ket_qua=kq, ly_do=ly)
            self._delay[LN.mien_goc(host)] = self.robots.crawl_delay(url)
            if dung_cdp:
                d = self._lay_cdp(url, truoc=self._truoc)
                status, text, loi = d.get("status"), d.get("html", ""), d.get("loi", "")
                if loi in ("khong_mo_cdp", "khong_co_playwright"):
                    return dict(r, ket_qua="KHONG_CO_CHROME", ly_do="Chrome chua mo o che do CDP (cong 9222/9224) hoac thieu playwright")
            else:
                d = {}
                status, text, loi = self._lay(url, truoc=self._truoc)
        except LN.HetNhip as e:
            return dict(r, ket_qua="CHO", ly_do=str(e))
        if loi.startswith("chuyen huong ra ngoai: "):
            dich = loi.split(": ", 1)[1]
            n = LN.phan_loai(dich)
            self.tt.ghi(khoa, host, "XONG", status=status, dich_url=dich)
            return dict(r, ket_qua="CHUYEN_HUONG", status=status,
                        dich={"ma": n["ma"], "nen_tang": n["nen_tang"], "loai": n["loai"], "rieng": n["rieng"]})
        kq = LN.phan_loai_loi(status, text, loi)
        if kq != "OK":
            self.tt.ghi(khoa, host, kq, status=status, loi=_cat(loi, 80))
            return dict(r, ket_qua=kq, status=status, ly_do=_cat(loi, 80))
        tom = _tom_tat_noi_dung(text, url)
        if dung_cdp:
            tom["xhr"] = [LN.rut_diem_cuoi(x) for x in d.get("xhr", [])][:80]
            tom["tab_lich_su"] = [_tab_tom_tat(t, url) for t in d.get("tab_lich_su", [])][:2]
        duong = self._ghi_tom_tat(m, tom, dung_cdp)
        self.tt.ghi(khoa, host, "OK", status=status, kich_thuoc=len(text), so_bang=len(tom.get("bang", [])))
        return dict(r, ket_qua="OK", status=status, kieu=tom.get("kieu"), so_bang=len(tom.get("bang", [])), so_tab=len(tom.get("tab", [])),
                    so_diem_cuoi=len(tom.get("diem_cuoi", [])) + len(tom.get("xhr", [])), can_js=bool(tom.get("can_js")), tom_tat=duong,
                    symbol_chinh=(tom.get("phan_bo_symbol") or {}).get("symbol_chinh"), phan_bo_symbol=tom.get("phan_bo_symbol"))

    def _ghi_tom_tat(self, m: dict, tom: dict, dung_cdp: bool) -> str:
        """Tom tat cong khai qua HTTP -> `reports/link_tham_do_<ma>.json` (ve cloud). Link rieng hoac Chrome (da dang nhap) -> chi o may nha."""
        tom = dict(tom, ma=m["ma"], nen_tang=m["nen_tang"], loai=m["loai"], cach="cdp" if dung_cdp else "http")
        tom = _vua_gioi_han(tom, ("xhr", "diem_cuoi", "script_nguon", "tab_lich_su", "bang", "muc", "tab"))
        rieng_tu = m["rieng"] or dung_cdp
        goc = self.thu_muc_tom_tat if rieng_tu else self.thu_muc_reports
        duong = goc / (("%s.json" % m["ma"]) if rieng_tu else ("link_tham_do_%s.json" % m["ma"]))
        _ghi_json_nguyen_tu(duong, tom)
        return "local" if rieng_tu else "reports/%s" % duong.name

    # ---- chay mau
    def _chon(self, kh: list[dict], toi_da: int, theo_nen: int, lai: bool, hau_to: str = "") -> list[dict]:
        """Chon MAU: moi (nen_tang, loai) toi da `theo_nen` link TINH CA cai da lam (tham do chi de hoc cau truc, khong cao ao at).
        Link rut gon (`giai_ma`) khong tinh tran: mo moi cai mot lan de biet dich. `hau_to` = hau to khoa trang thai (CDP: `~cdp`)."""
        chon, dem = [], {}
        for e in kh:
            k = (e["nen_tang"], e["loai"])
            if dem.get(k, 0) >= theo_nen and e["cach_lay"] != "giai_ma":
                continue
            dem[k] = dem.get(k, 0) + 1
            if not lai and self.tt.trang_thai(e["ma"] + hau_to) in ("OK", "XONG"):
                continue
            chon.append(e)
            if len(chon) >= toi_da:
                break
        return chon

    def chon_mau(self, muc: list[dict], toi_da: int = 12, theo_nen: int = 2, lai: bool = False, cdp: bool = False) -> list[dict]:
        """Danh sach (da gan `_cdp`) can tham do: luot HTTP truoc; `cdp=True` them luot Chrome cho (a) link chi mo duoc bang Chrome va
        (b) link http co du phong Chrome (de bam thu tab lich su, bat XHR that)."""
        duoc = [m for m in muc if m["nen_tang"] not in KHONG_TU_DONG]
        ra = [dict(e, _cdp=False) for e in self._chon(
            LN.ke_hoach([m for m in duoc if m["cach_lay"] in ("http", "giai_ma")], self.tt), toi_da, theo_nen, lai)]
        if cdp:
            ra += [dict(e, _cdp=True) for e in self._chon(
                LN.ke_hoach([m for m in duoc if m["cach_lay"] == "cdp"], self.tt), toi_da, theo_nen, lai)]
            ra += [dict(e, _cdp=True) for e in self._chon(
                LN.ke_hoach([m for m in duoc if m["cach_lay"] == "http" and m.get("du_phong") == "cdp"], self.tt),
                toi_da, theo_nen, lai, hau_to="~cdp")]
        return ra

    def chay_mau(self, muc: list[dict] | None = None, toi_da: int = 12, theo_nen: int = 2, lai: bool = False, cdp: bool = False) -> list[dict]:
        """Tham do mau (xem `chon_mau`). Bi chan o mot ten mien (429 / 403 / robots) -> bo qua phan con lai cua ten mien do trong luot nay."""
        muc = self.muc_day_du() if muc is None else muc
        ket, da_dung = [], set()
        for e in self.chon_mau(muc, toi_da, theo_nen, lai, cdp):
            mien = LN.mien_goc(urlsplit(e["url"]).hostname or "")
            if mien in da_dung:
                continue
            r = self.tham_do(e, cdp=e["_cdp"])
            ket.append(r)
            if r["ket_qua"] in ("CHAN_TAN_SUAT", "CHAN_CAM", "CHAN_ROBOTS"):
                da_dung.add(mien)
            self.in_ra("  %-15s %-5s %s/%s %s" % (r["ket_qua"], r["cach"], r["nen_tang"], r["loai"], r["ma"]))
        return ket


# ============================================================== 3. BAO CAO CHAY (an toan, bang loi thuong)
def bao_cao_chay(ket: list[dict]) -> dict:
    """Ket qua cac lan tham do -> bao cao AN TOAN: link rieng chi con ma + nen tang + loai (khong URL)."""
    muc = []
    for r in ket:
        e = {k: r[k] for k in ("ma", "nen_tang", "loai", "cach", "ket_qua", "status", "kieu", "so_bang", "so_tab", "so_diem_cuoi",
                               "can_js", "tom_tat", "ly_do", "symbol_chinh") if k in r}
        if r.get("dich"):
            e["dich"] = {k: r["dich"][k] for k in ("ma", "nen_tang", "loai") if k in r["dich"]}
        e["rieng"] = bool(r.get("rieng"))
        if not r.get("rieng") and r.get("url"):
            e["url"] = r["url"]
        muc.append(e)
    tong: dict = {}
    for r in ket:
        tong[r["ket_qua"]] = tong.get(r["ket_qua"], 0) + 1
    return {"so_link": len(ket), "theo_ket_qua": dict(sorted(tong.items(), key=lambda x: -x[1])), "muc": muc}


def bao_cao_chay_van_ban(bc: dict) -> str:
    t = bc["theo_ket_qua"]
    dong = ["THAM DO LINK: %d link" % bc["so_link"]]
    nhan = {"OK": "da lay duoc cau truc trang (tab, bang, diem cuoi) -> cloud doc de viet bo doc lich su dung dinh dang",
            "CHUYEN_HUONG": "link rut gon / chuyen sang ten mien khac: da ghi dich den, luot sau tham do dich",
            "CHAN_CAM": "bi trang chan may tu dong (403 / captcha): ten mien do nghi 24 gio",
            "CHAN_TAN_SUAT": "bi gioi han toc do (429): ten mien nghi 15 phut tro len",
            "CHAN_ROBOTS": "robots.txt cam duong dan: khong cao (ban quyet dinh)",
            "HET_TRANG": "trang khong con (404/410)", "LOI_MAY_CHU": "may chu loi (5xx)", "LOI_MANG": "loi mang / khong doc duoc robots.txt",
            "CHO": "chua toi luot (dang nghi / het tran luot)", "BO_QUA": "khong tu dong duoc (Facebook/Zalo/...): dan chu hoac luu trang",
            "KHONG_CO_CHROME": "Chrome chua mo o che do CDP"}
    for k, n in t.items():
        dong.append("  - %2d x %s: %s" % (n, k, nhan.get(k, "")))
    can = []
    if t.get("CHAN_CAM"):
        can.append("trang chan may tu dong: mo trang do bang Chrome da dang nhap roi chay `b link chay --cdp`, hoac luu trang (Ctrl+S) vao "
                   "du_lieu_cao/tha_vao/ roi `b link thu-muc`")
    if t.get("KHONG_CO_CHROME"):
        can.append("mo Chrome voi --remote-debugging-port=9224 (dang nhap san cac trang can dang nhap)")
    if t.get("BO_QUA"):
        can.append("Facebook / Zalo / Discord / Drive: dan chu tin nhan vao link_rieng.txt hoac luu trang vao du_lieu_cao/tha_vao/")
    if can:
        dong.append("BAN CAN LAM:")
        dong += ["  * " + c for c in can]
    return "\n".join(dong)


def ghi_bao_cao_chay(ket: list[dict], duong_json=None, duong_md=None) -> dict:
    bc = _vua_gioi_han(bao_cao_chay(ket), ("muc",))
    _ghi_json_nguyen_tu(Path(duong_json) if duong_json else BAO_CAO_CHAY_JSON, bc)
    md = Path(duong_md) if duong_md else BAO_CAO_CHAY_MD
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(bao_cao_chay_van_ban(bc)[:GIOI_HAN_BAO_CAO] + "\n", encoding="utf-8")
    return bc


# ============================================================== 4. NAP VAN BAN (tin nhan dan vao)
def nap_van_ban(van_ban: str, duong_link=None, luu_tai_khoan: bool = True, duong_goi_y=None) -> dict:
    """Tin nhan dan vao -> link vao `link_rieng.txt`, tai khoan XEM vao kho passview (bi gitignore), goi y kenh Telegram (cuc bo).

    Ket qua tra ve chi gom SO DEM + ma bam (khong URL, khong ten tep, khong noi dung): an toan de in / ghi vao reports/."""
    vb = str(van_ban or "")
    kq = LN.trich_tu_van_ban(vb, giu_bi_mat=True)
    moi = LN.them_link_rieng(vb, duong=duong_link)
    n_tk_moi = 0
    tho = kq.get("tai_khoan_xem_tho") or []
    if luu_tai_khoan and tho:
        from nhan import passview as PV
        n_tk_moi = PV.luu(tho, nguon="tha_vao")
    goi_y = kq.get("telegram_goi_y") or []
    if goi_y:
        g = Path(duong_goi_y) if duong_goi_y else GOI_Y_TELEGRAM
        co = set(g.read_text(encoding="utf-8").split()) if g.is_file() else set()
        them = [x for x in goi_y if x not in co]
        if them:
            g.parent.mkdir(parents=True, exist_ok=True)
            with g.open("a", encoding="utf-8") as f:
                f.write("\n".join(them) + "\n")
    theo_nen: dict = {}
    for m in kq["link"]:
        theo_nen[m["nen_tang"]] = theo_nen.get(m["nen_tang"], 0) + 1
    return {"so_ky_tu": kq["so_ky_tu"], "link_tong": len(kq["link"]), "link_moi": len(moi),
            "theo_nen_tang": dict(sorted(theo_nen.items(), key=lambda x: -x[1])),
            "mql5_tin_hieu": len(kq["mql5_tin_hieu"]), "telegram_cong_khai": len(kq["telegram_cong_khai"]), "telegram_goi_y": len(goi_y),
            "tai_khoan_xem": {"thay": len(tho), "moi_luu": n_tk_moi},
            "tep_dinh_kem": {a: sum(1 for x in kq["tep"] if x["loai"] == a) for a in sorted({x["loai"] for x in kq["tep"]})},
            "tu_khoa": kq["tu_khoa"]}


class _HtmlThanhChu(HTMLParser):
    """HTML (trang luu tay, xuat Telegram) -> chu + moi href. Bo script/style. Dung de tim link / tai khoan xem trong trang luu."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.o, self._bo = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._bo += 1
        for k, v in attrs:
            if k in ("href", "src", "data-url") and v and v.startswith(("http://", "https://")):
                self.o.append(" %s " % v)
        if tag in ("br", "p", "div", "tr", "li"):
            self.o.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._bo:
            self._bo -= 1

    def handle_data(self, data):
        if not self._bo:
            self.o.append(data)


def html_thanh_chu(html: str, toi_da: int = 3_000_000) -> str:
    p = _HtmlThanhChu()
    try:
        p.feed(str(html)[:toi_da])
        p.close()
    except Exception:
        pass
    return "".join(p.o)


_KHOA_CHU_JSON = {"text", "href", "file_name", "caption", "url", "title", "description", "body", "message", "content"}


def json_thanh_chu(j, toi_da: int = 3_000_000) -> str:
    """JSON bat ky (xuat Telegram Desktop `result.json`, du lieu luu tay) -> chu: gom gia tri chuoi cua cac khoa van ban, di xuong long."""
    ra, n = [], [0]

    def di(x, sau=0):
        if n[0] > toi_da or sau > 12:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, str) and str(k).lower() in _KHOA_CHU_JSON:
                    ra.append(v)
                    n[0] += len(v)
                elif isinstance(v, (dict, list)):
                    di(v, sau + 1)
        elif isinstance(x, list):
            for v in x:
                if isinstance(v, str):
                    ra.append(v)
                    n[0] += len(v)
                else:
                    di(v, sau + 1)

    di(j)
    return "\n".join(ra)[:toi_da]


# ============================================================== 5. NAP THU MUC `tha_vao` (bao cao, tin nhan, EA)
def _iso(t):
    import pandas as pd
    return None if t is None or pd.isna(t) else t.strftime("%Y-%m-%d %H:%M:%S")


def _so_hoac_none(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if x != x else x


def lenh_tu_bang(d) -> list[dict]:
    """Bang chuan hoa cua `boc_lich_su.chuan_hoa` -> list dict hop voi `passview.ghi_lenh_csv` (gio dang chuoi ISO, NaN -> None)."""
    ra = []
    for r in d.itertuples(index=False):
        ra.append({"mo": _iso(r.mo), "dong": _iso(r.dong), "chieu": int(r.chieu), "lot": float(r.lot), "gia_mo": float(r.gia_mo),
                   "gia_dong": _so_hoac_none(r.gia_dong), "loi": _so_hoac_none(r.loi), "sl": _so_hoac_none(r.sl), "tp": _so_hoac_none(r.tp),
                   "ma": str(r.ma) or "X", "magic": None, "position_id": None, "ly_do_dong": None, "ghi_chu": None})
    return ra


def nap_bao_cao(duong: Path, ma_nguon: str, thu_muc_lenh=None, toi_thieu: int = 30) -> dict:
    """Mot tep bao cao lich su (.csv/.htm/.html/.json) -> `du_lieu_cao/lenh/<ma_nguon>_<MA>.csv`. Tra {ket_qua, so_lenh, ma: {MA: so_lenh}, tep_lenh}."""
    from nhan import boc_lich_su as BL
    from nhan import passview as PV
    try:
        d = BL.chuan_hoa(BL.doc_tep(duong))
    except Exception as e:                                           # tep khong phai bao cao lenh / sai dinh dang: noi that, khong doan
        return {"ket_qua": "KHONG_DOC_DUOC", "ly_do": _cat("%s: %s" % (type(e).__name__, e), 160), "so_lenh": 0}
    if d.empty:
        return {"ket_qua": "KHONG_CO_LENH", "so_lenh": 0}
    tep = PV.ghi_lenh_csv(lenh_tu_bang(d), ma_nguon, thu_muc=thu_muc_lenh, toi_thieu=toi_thieu)
    theo_ma = {str(m): int(n) for m, n in d["ma"].value_counts().items()}
    ra = {"ket_qua": "DA_NAP" if tep else "QUA_IT_LENH", "so_lenh": int(len(d)), "so_dong": int(d["dong"].notna().sum()),
          "ma": dict(list(theo_ma.items())[:12]), "tep_lenh": [t["tep"] for t in tep]}
    if not tep:
        ra["ly_do"] = "moi ma duoi %d lenh: chua du de bong tach luat" % toi_thieu
    return ra


def _doc_manifest(duong=None) -> dict:
    try:
        d = json.loads(Path(duong or MANIFEST).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _xu_ly_tep(duong: Path, noi_dung: bytes | None, thu_muc_lenh, duong_link, duong_goi_y, toi_thieu, luu_tai_khoan) -> dict:
    """Xu ly MOT tep theo loai. `noi_dung` (cho tep trong .zip) -> ghi ra thu muc tam co ten phang truoc khi doc."""
    suf = duong.suffix.lower()
    loai = LN.loai_tep(duong.name)
    tho = noi_dung if noi_dung is not None else duong.read_bytes()
    sha = _sha(tho)
    r = {"sha": sha, "loai": loai, "dinh_dang": suf}
    if suf in (".ex4", ".ex5"):
        return dict(r, ket_qua="EA_BIEN_DICH", ly_do="chi ghi nhan: MT5 moi chay duoc, khong thuc thi tu day")
    if suf in (".mq4", ".mq5", ".mqh", ".set"):
        return dict(r, ket_qua="EA_NGUON" if suf != ".set" else "THAM_SO", kich_thuoc=len(tho))
    if suf in (".xlsx", ".xls", ".pdf"):
        return dict(r, ket_qua="CAN_CHUYEN_SANG_CSV", ly_do="chua doc duoc %s: mo trong Excel/MT5 roi luu ra .csv hoac .htm" % suf)
    if suf in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        return dict(r, ket_qua="BO_QUA", ly_do="anh")
    if suf not in (".txt", ".md", ".csv", ".tsv", ".htm", ".html", ".json"):
        return dict(r, ket_qua="BO_QUA", ly_do="loai tep khong can cho nghien cuu")
    import tempfile
    with tempfile.TemporaryDirectory() as tam:
        if noi_dung is not None:
            nguon = Path(tam) / ("x" + suf)
            nguon.write_bytes(noi_dung)
        else:
            nguon = duong
        if suf in (".csv", ".tsv", ".htm", ".html", ".json"):
            kq = nap_bao_cao(nguon, sha[:8], thu_muc_lenh, toi_thieu)
            if kq["ket_qua"] in ("DA_NAP", "QUA_IT_LENH", "KHONG_CO_LENH"):
                return dict(r, **kq)
            bao_cao_loi = kq
        else:
            bao_cao_loi = None
        # khong phai bao cao lenh -> coi la chu (tin nhan / trang luu / xuat Telegram)
        van_ban = tho.decode("utf-8-sig", errors="replace")
        if suf in (".htm", ".html"):
            van_ban = html_thanh_chu(van_ban)
        elif suf == ".json":
            try:
                van_ban = json_thanh_chu(json.loads(van_ban))
            except ValueError:
                pass
    n = nap_van_ban(van_ban, duong_link=duong_link, luu_tai_khoan=luu_tai_khoan, duong_goi_y=duong_goi_y)
    ra = dict(r, ket_qua="DA_NAP_CHU", **{k: n[k] for k in ("so_ky_tu", "link_tong", "link_moi", "mql5_tin_hieu", "telegram_goi_y")},
              tai_khoan_xem=n["tai_khoan_xem"], tu_khoa=n["tu_khoa"])
    if bao_cao_loi and bao_cao_loi["ket_qua"] == "KHONG_DOC_DUOC" and suf in (".csv", ".tsv", ".htm", ".html"):
        ra["ghi_chu"] = "khong phai bang lenh (%s)" % bao_cao_loi.get("ly_do", "")[:100]
    return ra


def _tep_trong_zip(duong: Path, toi_da_muc: int = 100, toi_da_byte: int = 20_000_000, toi_da_tong: int = 100_000_000):
    """Doc cac tep van ban / bao cao / EA nguon TRONG .zip bang bo nho (khong giai nen ra duong dan: chong zip-slip / zip-bomb)."""
    ra, tong = [], 0
    with zipfile.ZipFile(duong) as z:
        for zi in z.infolist()[:toi_da_muc]:
            if zi.is_dir() or zi.file_size > toi_da_byte or tong + zi.file_size > toi_da_tong:
                continue
            ten = os.path.basename(zi.filename.replace("\\", "/"))
            if not ten or ten.startswith("."):
                continue
            ok, _ = LN.tai_duoc(ten, zi.file_size)
            if not ok:
                continue
            tong += zi.file_size
            ra.append((ten, z.read(zi)))
    return ra


def nap_thu_muc(thu_muc=None, manifest=None, duong_link=None, duong_goi_y=None, thu_muc_lenh=None, toi_thieu: int = 30,
                luu_tai_khoan: bool = True, in_ra=None) -> dict:
    """Nap moi tep trong `du_lieu_cao/tha_vao/` (de quy). Tep da nap (cung noi dung) thi bo qua; tep doi noi dung thi nap lai.

    Tra bao cao AN TOAN: moi tep chi hien `<ma bam 8 ky tu>.<duoi>` + ket qua + so dem (ten tep co the la ten nhom / so tai khoan)."""
    goc = Path(thu_muc) if thu_muc else LN.THA_VAO
    goc.mkdir(parents=True, exist_ok=True)
    man_duong = Path(manifest) if manifest else MANIFEST
    man = _doc_manifest(man_duong)
    ket = []
    for duong in sorted(goc.rglob("*")):
        if not duong.is_file() or duong.name.startswith((".", "~$")):
            continue
        rel = duong.relative_to(goc).as_posix()
        try:
            kich = duong.stat().st_size
            if kich > TOI_DA_TEP_BYTE:
                ket.append({"tep": "?", "ket_qua": "QUA_LON", "ly_do": "tep > %d MB" % (TOI_DA_TEP_BYTE // 1_000_000)})
                continue
            sha = _sha(duong.read_bytes())
        except OSError as e:
            ket.append({"tep": "?", "ket_qua": "LOI_DOC", "ly_do": _cat(e, 80)})
            continue
        ten_an = "%s%s" % (sha[:8], duong.suffix.lower())
        if man.get(rel, {}).get("sha") == sha:
            ket.append({"tep": ten_an, "ket_qua": "DA_NAP_TRUOC_DO"})
            continue
        try:
            if duong.suffix.lower() == ".zip":
                con = []
                for ten, nd in _tep_trong_zip(duong):
                    c = _xu_ly_tep(Path(ten), nd, thu_muc_lenh, duong_link, duong_goi_y, toi_thieu, luu_tai_khoan)
                    con.append({"tep": "%s%s" % (c["sha"][:8], Path(ten).suffix.lower()), **{k: v for k, v in c.items() if k != "sha"}})
                dem: dict = {}
                for c in con:
                    dem[c["ket_qua"]] = dem.get(c["ket_qua"], 0) + 1
                r = {"tep": ten_an, "ket_qua": "ZIP", "so_tep_ben_trong": len(con), "theo_ket_qua": dem, "ben_trong": con[:40]}
            else:
                c = _xu_ly_tep(duong, None, thu_muc_lenh, duong_link, duong_goi_y, toi_thieu, luu_tai_khoan)
                r = {"tep": ten_an, **{k: v for k, v in c.items() if k != "sha"}}
        except zipfile.BadZipFile:
            r = {"tep": ten_an, "ket_qua": "ZIP_HONG"}
        except Exception as e:                                       # mot tep hong khong duoc lam sap ca thu muc
            r = {"tep": ten_an, "ket_qua": "LOI_XU_LY", "ly_do": _cat("%s: %s" % (type(e).__name__, e), 120)}
        man[rel] = {"sha": sha, "ket_qua": r["ket_qua"], "lan_cuoi": int(time.time())}
        ket.append(r)
        if in_ra:
            in_ra("  %-20s %s" % (r["ket_qua"], r["tep"]))
    _ghi_json_nguyen_tu(man_duong, man)
    dem_kq: dict = {}
    for r in ket:
        dem_kq[r["ket_qua"]] = dem_kq.get(r["ket_qua"], 0) + 1
    so_lenh = sum(r.get("so_lenh", 0) for r in ket) + sum(c.get("so_lenh", 0) for r in ket for c in r.get("ben_trong", []))
    return {"thu_muc": "du_lieu_cao/tha_vao", "so_tep": len(ket), "theo_ket_qua": dict(sorted(dem_kq.items(), key=lambda x: -x[1])),
            "so_lenh_nap": int(so_lenh), "tep": ket}


def bao_cao_nap_van_ban(bc: dict) -> str:
    t = bc["theo_ket_qua"]
    dong = ["NAP THU MUC tha_vao: %d tep" % bc["so_tep"]]
    if not bc["so_tep"]:
        return ("THU MUC tha_vao TRONG. Tha vao du_lieu_cao/tha_vao/: bao cao MT4/MT5 (.htm/.csv), tin nhan luu (.txt / .html luu trang / "
                "result.json cua Telegram Desktop), .zip, EA nguon (.mq5) / .set.")
    nhan = {"DA_NAP": "bao cao lenh da doc -> du_lieu_cao/lenh/*.csv (san sang `b nc cc boc_lich_su`)",
            "DA_NAP_CHU": "tin nhan / trang luu: da lay link, tai khoan xem, ten tep dinh kem",
            "QUA_IT_LENH": "bao cao co lenh nhung moi ma < 30 lenh: chua du de bong tach luat",
            "KHONG_DOC_DUOC": "khong doc duoc bang lenh (sai dinh dang?)", "CAN_CHUYEN_SANG_CSV": "Excel/PDF: luu ra .csv hoac .htm roi tha lai",
            "EA_NGUON": "ma EA (.mq4/.mq5/.mqh): da ghi nhan", "THAM_SO": ".set: da ghi nhan", "EA_BIEN_DICH": ".ex4/.ex5: chi ghi nhan",
            "ZIP": "tep nen: da doc ben trong bang bo nho", "DA_NAP_TRUOC_DO": "da nap luot truoc (khong doi)", "BO_QUA": "bo qua"}
    for k, n in t.items():
        dong.append("  - %2d x %s: %s" % (n, k, nhan.get(k, "")))
    if bc["so_lenh_nap"]:
        dong.append("TONG: %d lenh da doc. Buoc ke: cloud chay `b nc cc boc_lich_su` tren tung tep CSV." % bc["so_lenh_nap"])
    return "\n".join(dong)


def ghi_bao_cao_nap(bc: dict, duong_json=None, duong_md=None) -> dict:
    bc = _vua_gioi_han(bc, ("tep",))
    _ghi_json_nguyen_tu(Path(duong_json) if duong_json else BAO_CAO_NAP_JSON, bc)
    md = Path(duong_md) if duong_md else BAO_CAO_NAP_MD
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(bao_cao_nap_van_ban(bc)[:GIOI_HAN_BAO_CAO] + "\n", encoding="utf-8")
    return bc


# ============================================================== 6. THU HOACH PASSVIEW (tai khoan XEM -> lenh)
def _can_thu_tk(t: dict, bay_gio: float, nghi_giay: float = 24 * 3600, toi_da_loi: int = 3) -> bool:
    if t.get("trang_thai", "CHUA_THU") == "CHUA_THU":
        return True
    if t.get("trang_thai") == "KHONG_DOC":
        return int(t.get("so_loi", 0)) < toi_da_loi and bay_gio - float(t.get("lan_cuoi", 0)) >= nghi_giay
    return False


def thu_hoach_passview(toi_da: int = 3, doc=None, thu_muc_lenh=None, dong_ho=time.time, ngu=time.sleep, cach_giay: float = 15.0,
                       toi_thieu: int = 30) -> dict:
    """Moi tai khoan XEM chua thu: dang nhap CHI DOC -> deals -> lenh -> `du_lieu_cao/lenh/<ma_tk>_<MA>.csv`. Ghi ket qua vao kho passview.

    `doc(login, mat_khau, server)` tiem duoc (that: `passview.doc_lich_su`, can MT5 + giu khoa tester). Bao cao khong chua so tai khoan /
    mat khau / may chu: chi ma bam 8 ky tu. Toi da `toi_da` tai khoan / lan, cach nhau `cach_giay` (khong dap may chu moi)."""
    from nhan import passview as PV
    doc = doc or PV.doc_lich_su
    bay_gio = dong_ho()
    cho = [t for t in PV.danh_sach() if _can_thu_tk(t, bay_gio)]
    ket, lenh_tong = [], 0
    for i, t in enumerate(cho[:max(0, toi_da)]):
        if i:
            ngu(cach_giay)
        ma = PV.ma_tai_khoan(t["login"], t["server"])
        try:
            kq = doc(int(t["login"]), t["mat_khau"], t["server"])
        except Exception as e:
            ly = _cat(_che_bi_mat(e, t["login"], t["mat_khau"], t["server"]), 100)
            PV.cap_nhat(t["login"], t["server"], trang_thai="KHONG_DOC", loi=ly, lan_cuoi=int(bay_gio),
                        so_loi=int(t.get("so_loi", 0)) + 1)
            ket.append({"tk": ma, "ket_qua": "KHONG_DOC", "ly_do": ly})
            continue
        r = PV.deals_thanh_lenh(kq.get("deals") or [])
        tep = PV.ghi_lenh_csv(r["lenh"], ma, thu_muc=thu_muc_lenh, toi_thieu=toi_thieu)
        loai = (kq.get("account") or {}).get("loai")
        PV.cap_nhat(t["login"], t["server"], trang_thai="DA_DOC", so_lenh=len(r["lenh"]), lan_cuoi=int(bay_gio), loi="", so_loi=0,
                    loai=str(loai or ""))
        lenh_tong += len(r["lenh"])
        ket.append({"tk": ma, "ket_qua": "DA_DOC", "loai": loai, "so_deal": len(kq.get("deals") or []), "so_lenh": len(r["lenh"]),
                    "chua_dong": int(r.get("chua_dong") or 0), "tep": [x["tep"] for x in tep],
                    "ma": {x["ma"]: x["so_lenh"] for x in tep if x.get("magic") is None}})
    return {"tong_trong_kho": len(PV.danh_sach()), "den_luot": len(cho), "da_thu": len(ket),
            "doc_duoc": sum(1 for k in ket if k["ket_qua"] == "DA_DOC"), "khong_doc": sum(1 for k in ket if k["ket_qua"] == "KHONG_DOC"),
            "lenh_tong": lenh_tong, "tk": ket}


# ============================================================== 8. KIEM LAI NHAN SYMBOL CUA HO SO MQL5 SONG LAU
def ho_so_symbol(ch: "Chay", ho_so=None, song_toi_thieu: int = 730, toi_da: int = 40) -> dict:
    """Kiem lai NHAN symbol cua cac ho so MQL5 song lau (`reports/signal_ho_so.json`) bang bang Distribution THAT cua trang.

    Nhan cu do `_quet_signal_mql5._RX_SYM` gan (dem chu hoa 6 ky tu trong CA trang) sai o con 2196457: vang 1549 lenh bi gan USDCHF
    (2 lenh). Chi tham do cong khai (HTTP, co nhip + robots), moi trang MOT lan, dung khi ten mien chan / het luot. Tom tat tung trang
    nam o `du_lieu_cao/` (khong vao git); ket qua gon -> `reports/nguoi_thang_symbol.json`."""
    if ho_so is None:
        ho_so = json.loads((LAB / "reports" / "signal_ho_so.json").read_text(encoding="utf-8"))
    chon = sorted((h for h in ho_so if h.get("id") and (h.get("song_ngay") or 0) >= song_toi_thieu),
                  key=lambda h: -(h.get("song_ngay") or 0))[:toi_da]
    goc = ch.thu_muc_reports
    ch.thu_muc_reports = THU_MUC_TOM_TAT / "ho_so_symbol"
    muc, dung = [], ""
    try:
        for h in chon:
            r = ch.tham_do(LN.phan_loai("https://www.mql5.com/en/signals/%d" % int(h["id"])))
            ps = r.get("phan_bo_symbol") or {}
            cu = list(h.get("symbol") or [])
            muc.append({"id": int(h["id"]), "song_ngay": round(float(h.get("song_ngay") or 0)), "nhan_cu": cu, "ket_qua": r["ket_qua"],
                        "symbol_chinh": ps.get("symbol_chinh"), "ty_le_lenh": ps.get("ty_le_lenh"), "day_du": ps.get("day_du"),
                        "symbol": [{k: x[k] for k in ("tho", "chuan", "lenh") if k in x} for x in (ps.get("symbol") or [])[:6]],
                        "nhan_cu_dung": (bool(cu) and ps.get("symbol_chinh") == cu[0]) if ps else None})
            if r["ket_qua"] in ("CHAN_TAN_SUAT", "CHAN_CAM", "CHAN_ROBOTS", "CHO"):
                dung = r["ket_qua"]
                break
    finally:
        ch.thu_muc_reports = goc
    dem: dict = {}
    for x in muc:
        if x["symbol_chinh"]:
            dem[x["symbol_chinh"]] = dem.get(x["symbol_chinh"], 0) + 1
    return {"da_thu": len(muc), "tong_song_lau": len(chon), "doc_duoc": sum(1 for x in muc if x["symbol_chinh"]),
            "nhan_cu_sai": sum(1 for x in muc if x["nhan_cu_dung"] is False), "dung_vi": dung,
            "dem_symbol_chinh": dict(sorted(dem.items(), key=lambda kv: -kv[1])), "muc": muc}


# ============================================================== 7. CHIA SE TOM TAT (link cong khai da tham do bang Chrome)
def chia_se(ma: str, thu_muc_tom_tat=None, thu_muc_reports=None, tt=None, duong_link=None) -> tuple[bool, str]:
    """Copy tom tat CUC BO cua mot link CONG KHAI (da tham do bang Chrome) sang `reports/link_tham_do_<ma>.json` de cloud doc.
    Tu choi link rieng. Chay lai bo loc: khong URL day du, khong gia tri o nhap (da co o `tom_tat_cau_truc`)."""
    if not re.fullmatch(r"[0-9a-f]{10}", str(ma)):
        return False, "ma phai la 10 ky tu hex (xem `b link ke-hoach`)"
    nguon = (Path(thu_muc_tom_tat) if thu_muc_tom_tat else THU_MUC_TOM_TAT) / ("%s.json" % ma)
    if not nguon.is_file():
        return False, "chua co tom tat cuc bo cho ma nay (chay `b link tham-do ... --cdp` truoc)"
    muc = {m["ma"]: m for m in LN.doc_link_rieng(duong_link)}
    tt = tt or LN.TrangThai()
    dich = tt.d["link"]
    lien_quan = muc.get(ma)
    if lien_quan is None:                                           # co the la dich cua link rut gon
        for k, v in dich.items():
            if v.get("dich_url") and LN.phan_loai(v["dich_url"])["ma"] == ma:
                lien_quan = LN.phan_loai(v["dich_url"])
                break
    if lien_quan is None:
        return False, "ma nay khong nam trong link_rieng.txt: khong chia se"
    if lien_quan["rieng"]:
        return False, "link RIENG TU: khong bao gio gui di"
    d = json.loads(nguon.read_text(encoding="utf-8"))
    d = _vua_gioi_han(d, ("xhr", "diem_cuoi", "script_nguon", "tab_lich_su", "bang", "muc", "tab"))
    dich_duong = (Path(thu_muc_reports) if thu_muc_reports else LAB / "reports") / ("link_tham_do_%s.json" % ma)
    _ghi_json_nguyen_tu(dich_duong, d)
    return True, "reports/%s" % dich_duong.name


# ============================================================== 8. CLI `b link`
def _in_ke_hoach(ch: Chay) -> list[dict]:
    muc = ch.muc_day_du()
    kh = LN.ke_hoach(muc, ch.tt)
    LN.ghi_bao_cao(kh)
    print(LN.bao_cao_van_ban(kh))
    cho = [p for p in LN.THA_VAO.rglob("*") if p.is_file()] if LN.THA_VAO.is_dir() else []
    print("THU MUC tha_vao: %d tep dang cho (chay `b link thu-muc` de nap)" % len(cho))
    return kh


def _doc_van_ban_tu(nguon: str) -> str:
    if nguon in ("-", ""):
        return sys.stdin.read()
    return Path(nguon).read_text(encoding="utf-8-sig", errors="replace")


def main(argv=None) -> int:
    """`b link <lenh>`: xem `--help`. Dau ra chi gom so dem / ma bam (khong URL rieng, khong ten tep)."""
    ap = argparse.ArgumentParser(prog="b link", description="Link chu du an -> tham do / nap tep / lich su lenh (xem nhan/link_nguon.py)")
    sp = ap.add_subparsers(dest="lenh")
    sp.add_parser("ke-hoach", help="doc link_rieng.txt + phan loai + ke hoach (khong goi mang)")
    p = sp.add_parser("them", help="them link / dan tin nhan vao link_rieng.txt (+ tai khoan xem)")
    p.add_argument("van_ban", nargs="+")
    p = sp.add_parser("nap-van-ban", help="nap tin nhan tu tep (hoac - = stdin)")
    p.add_argument("nguon", nargs="?", default="-")
    p = sp.add_parser("chay", help="tham do MAU (khong cao hang loat)")
    p.add_argument("--toi-da", type=int, default=12)
    p.add_argument("--theo-nen", type=int, default=2)
    p.add_argument("--lai", action="store_true")
    p.add_argument("--cdp", action="store_true", help="them link can Chrome da dang nhap")
    p = sp.add_parser("tham-do", help="tham do MOT link (tu tren mang: chi ten mien da duyet)")
    p.add_argument("url")
    p.add_argument("--cdp", action="store_true")
    p = sp.add_parser("thu-muc", help="nap du_lieu_cao/tha_vao/")
    p.add_argument("--toi-thieu", type=int, default=30)
    p = sp.add_parser("tai-khoan-xem", help="thu hoach lich su bang tai khoan xem da luu (can MT5 o may nha)")
    p.add_argument("--toi-da", type=int, default=3)
    sp.add_parser("bao-cao", help="in lai bao cao lan gan nhat")
    p = sp.add_parser("ho-so-symbol", help="kiem lai nhan symbol cua ho so MQL5 song lau bang bang Distribution that -> reports/nguoi_thang_symbol.json")
    p.add_argument("--song", type=int, default=730)
    p.add_argument("--toi-da", type=int, default=40)
    p = sp.add_parser("chia-se", help="gui tom tat cuc bo cua link CONG KHAI vao reports/")
    p.add_argument("ma")
    a = ap.parse_args(argv)
    ch = Chay(in_ra=print)
    if a.lenh in (None, "ke-hoach"):
        _in_ke_hoach(ch)
        return 0
    if a.lenh == "them":
        bc = nap_van_ban(" ".join(a.van_ban))
        print(json.dumps(bc, ensure_ascii=False, indent=1))
        return 0
    if a.lenh == "nap-van-ban":
        bc = nap_van_ban(_doc_van_ban_tu(a.nguon))
        print(json.dumps(bc, ensure_ascii=False, indent=1))
        return 0
    if a.lenh == "chay":
        kh = ch.muc_day_du()
        if not kh:
            print(LN.bao_cao_van_ban([]))
            return 0
        ket = ch.chay_mau(kh, toi_da=a.toi_da, theo_nen=a.theo_nen, lai=a.lai, cdp=a.cdp)
        bc = ghi_bao_cao_chay(ket)
        print(bao_cao_chay_van_ban(bc))
        return 0
    if a.lenh == "tham-do":
        ok, ly = LN.cho_tham_do(a.url) if not a.cdp else (True, "")
        if not ok:
            print("TU CHOI: %s" % ly)
            return 2
        r = ch.tham_do(LN.phan_loai(a.url), cdp=a.cdp or None)
        bc = ghi_bao_cao_chay([r], BAO_CAO_CHAY_JSON.with_name("link_tham_do_ket_qua.json"), BAO_CAO_CHAY_MD.with_name("link_tham_do_ket_qua.md"))
        print(bao_cao_chay_van_ban(bc))
        return 0 if r["ket_qua"] in ("OK", "CHUYEN_HUONG") else 1
    if a.lenh == "thu-muc":
        bc = ghi_bao_cao_nap(nap_thu_muc(toi_thieu=a.toi_thieu, in_ra=print))
        print(bao_cao_nap_van_ban(bc))
        return 0
    if a.lenh == "tai-khoan-xem":
        bc = thu_hoach_passview(toi_da=a.toi_da)
        _ghi_json_nguyen_tu(BAO_CAO_TK_JSON, bc)
        print("TAI KHOAN XEM: %d trong kho, %d den luot, da thu %d: doc duoc %d, khong doc duoc %d, %d lenh -> du_lieu_cao/lenh/"
              % (bc["tong_trong_kho"], bc["den_luot"], bc["da_thu"], bc["doc_duoc"], bc["khong_doc"], bc["lenh_tong"]))
        return 0
    if a.lenh == "bao-cao":
        for f in (LN.BAO_CAO_MD, BAO_CAO_CHAY_MD, BAO_CAO_NAP_MD):
            if f.is_file():
                print(f.read_text(encoding="utf-8").rstrip() + "\n")
        return 0
    if a.lenh == "ho-so-symbol":
        bc = ho_so_symbol(ch, song_toi_thieu=a.song, toi_da=a.toi_da)
        _ghi_json_nguyen_tu(LAB / "reports" / "nguoi_thang_symbol.json", bc)
        print("HO SO SYMBOL: da thu %d/%d, doc duoc %d, gan sai tu truoc %d%s; symbol chinh that: %s"
              % (bc["da_thu"], bc["tong_song_lau"], bc["doc_duoc"], bc["nhan_cu_sai"], (" (dung vi %s)" % bc["dung_vi"]) if bc["dung_vi"] else "",
                 ", ".join("%s %d" % kv for kv in bc["dem_symbol_chinh"].items()) or "chua co"))
        return 0 if bc["doc_duoc"] else 1
    if a.lenh == "chia-se":
        ok, ly = chia_se(a.ma)
        print(("DA CHIA SE: " if ok else "KHONG CHIA SE: ") + ly)
        return 0 if ok else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
