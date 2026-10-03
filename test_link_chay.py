# -*- coding: utf-8 -*-
"""link_chay: tham do trang, nap thu muc tha_vao, nap tin nhan, thu hoach tai khoan xem, chia se, CLI.

KHONG goi mang that / Chrome that / MT5 that: fetch, Chrome, dong ho, MT5 deu duoc tiem. Rieng `_mot_buoc_that` (requests.get) duoc thu
voi mot may chu HTTP chay tren 127.0.0.1 de kiem header gui di, tran kich thuoc, khong tu theo chuyen huong.
Dieu quan trong nhat: **bi mat KHONG lot ra bao cao / man hinh** (repo la PUBLIC; dau ra cua don co the quay ve cloud).
"""
from __future__ import annotations

import io
import json
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from nhan import boc_lich_su as BL
from nhan import link_chay as LC
from nhan import link_nguon as LN
from nhan import passview as PV

MAT_KHAU = "Xk93mQ7pLz"
LOGIN = "88776655"
MAY_CHU = "XMGlobal-Real 9"
MOI_NHOM = "https://t.me/+Zq9XkLmN0pQrStUv"
TIN_NHAN = ("Nhom VIP gui: xem lich su bot o day https://www.mql5.com/en/signals/2331122 va %s\n"
            "Login: %s Investor password: %s Server: %s\nfile ReportHistory-%s.html\nBot nay danh grid, DCA rat khoe\n"
            "kenh telegram @sieuloi_bot_vn cung hay") % (MOI_NHOM, LOGIN, MAT_KHAU, MAY_CHU, LOGIN)


class DongHo:
    def __init__(self, t=1_700_000_000.0):
        self.t, self.da_ngu = t, []

    def __call__(self):
        return self.t

    def ngu(self, s):
        self.da_ngu.append(s)
        self.t += s


@pytest.fixture(autouse=True)
def _khong_cham_repo(tmp_path, monkeypatch):
    """Moi duong dan cua repo -> thu muc tam. Bat ky lan ghi nao ra ngoai tmp_path la loi cua test."""
    monkeypatch.setattr(LN, "FILE_LINK_RIENG", (tmp_path / "link_rieng.txt", tmp_path / "config" / "link_rieng.txt"))
    monkeypatch.setattr(LN, "THU_MUC_CAO", tmp_path / "du_lieu_cao")
    monkeypatch.setattr(LN, "THA_VAO", tmp_path / "du_lieu_cao" / "tha_vao")
    monkeypatch.setattr(LN, "TRANG_THAI", tmp_path / "du_lieu_cao" / "trang_thai.json")
    monkeypatch.setattr(LN, "BAO_CAO_JSON", tmp_path / "reports" / "kh.json")
    monkeypatch.setattr(LN, "BAO_CAO_MD", tmp_path / "reports" / "kh.md")
    monkeypatch.setattr(PV, "KHO", tmp_path / "config" / "passview.json")
    monkeypatch.setattr(PV, "LAB", tmp_path)
    monkeypatch.setattr(LC, "LAB", tmp_path)
    monkeypatch.setattr(LC, "THU_MUC_LENH", tmp_path / "du_lieu_cao" / "lenh")
    monkeypatch.setattr(LC, "THU_MUC_TOM_TAT", tmp_path / "du_lieu_cao" / "tom_tat")
    monkeypatch.setattr(LC, "MANIFEST", tmp_path / "du_lieu_cao" / "tha_vao_manifest.json")
    monkeypatch.setattr(LC, "GOI_Y_TELEGRAM", tmp_path / "du_lieu_cao" / "goi_y_telegram.txt")
    for k in ("BAO_CAO_CHAY_JSON", "BAO_CAO_CHAY_MD", "BAO_CAO_NAP_JSON", "BAO_CAO_NAP_MD", "BAO_CAO_TK_JSON"):
        monkeypatch.setattr(LC, k, tmp_path / "reports" / Path(str(getattr(LC, k))).name)


def C(url):
    """URL da chuan hoa nhu he thong gui di (phan_loai bo `www.` va tien to ngon ngu cua mql5)."""
    return LN.phan_loai(url)["url"]


def CR(url):
    """URL robots.txt cua ten mien (da chuan hoa) cua `url`."""
    from urllib.parse import urlsplit
    p = urlsplit(C(url.replace("/robots.txt", "/x")))
    return "%s://%s/robots.txt" % (p.scheme, p.netloc)


class Web:
    """Mang gia: {url: (status, text, loi)}; robots rieng theo ten mien. Ghi thu tu goi; moi yeu cau di qua `truoc` nhu `lay_http` that."""

    def __init__(self, trang=None, robots=None):
        self.trang = {C(k): v for k, v in (trang or {}).items()}
        self.robots = {CR(k): v for k, v in (robots or {}).items()}
        self.goi = []

    def __call__(self, url, truoc=None, **_):
        if truoc:
            truoc(url)
        self.goi.append(url)
        if url.endswith("/robots.txt"):
            return self.robots.get(url, (404, "", ""))
        return self.trang.get(url, (404, "", ""))


def _chay(tmp_path, web=None, tran_luot=60, **kw):
    dh = DongHo()
    return Chay_(tmp_path, dh, web or Web(), tran_luot, **kw), dh


def Chay_(tmp_path, dh, web, tran_luot=60, lay_cdp=None):
    return LC.Chay(tt=LN.TrangThai(tmp_path / "du_lieu_cao" / "tt.json", dong_ho=dh), nhip=LN.Nhip(dong_ho=dh, ngu=dh.ngu, tran_luot=tran_luot),
                   lay=web, lay_cdp=lay_cdp, duong_link=tmp_path / "link_rieng.txt", thu_muc_tom_tat=tmp_path / "du_lieu_cao" / "tom_tat",
                   thu_muc_reports=tmp_path / "reports", in_ra=lambda *_: None)


TRANG_TIN_HIEU = """<html><head><title>Signal 2331122</title></head><body><h1>Super Grid</h1>
<a class="tab" href="#!tab=history">History</a><a role="tab" href="#!tab=stats">Statistics</a>
<table><tr><th>Month</th><th>Growth</th></tr><tr><td>Jan</td><td>5.1%</td></tr><tr><td>Feb</td><td>2.0%</td></tr></table>
<script>fetch("/en/signals/2331122/history?page=1&token=SECRETVALUE")</script></body></html>"""


# ============================================================== 1. lay_http: nhip, chuyen huong, giai ma
def _buoc(chuoi):
    """mot_buoc gia: tra lan luot cac ket qua trong `chuoi`, nho url da goi."""
    goi = []

    def f(url, ua, timeout, toi_da):
        goi.append(url)
        return chuoi[len(goi) - 1]
    return f, goi


def test_lay_http_theo_chuyen_huong_cung_ten_mien_va_goi_truoc_moi_buoc():
    f, goi = _buoc([(301, {"location": "https://www.mql5.com/en/signals/1"}, b"", ""),
                    (302, {"location": "/ru/signals/1"}, b"", ""),
                    (200, {"content-type": "text/html; charset=windows-1252"}, "caf\xe9".encode("cp1252"), "")])
    truoc = []
    st, text, loi = LC.lay_http("https://mql5.com/signals/1", mot_buoc=f, truoc=truoc.append)
    assert (st, text, loi) == (200, "caf\xe9", "")
    assert goi == ["https://www.mql5.com/en/signals/1", "https://www.mql5.com/en/signals/1", "https://www.mql5.com/ru/signals/1"] == truoc


def test_url_de_tai_mql5_them_www_va_locale_con_ten_mien_khac_giu_nguyen():
    # 03/10 may nha: mql5.com/signals/N -> 301 -> www.mql5.com/signals/N -> 404; chi www.mql5.com/en/signals/N ra 200
    assert LC._url_de_tai("https://mql5.com/signals/2196457") == "https://www.mql5.com/en/signals/2196457"
    assert LC._url_de_tai("https://mql5.com/signals/2196457?source=Site") == "https://www.mql5.com/en/signals/2196457?source=Site"
    assert LC._url_de_tai("https://www.mql5.com/vi/signals/1") == "https://www.mql5.com/vi/signals/1"
    assert LC._url_de_tai("https://www.myfxbook.com/members/a/b/1") == "https://www.myfxbook.com/members/a/b/1"


def test_lay_http_chuyen_huong_ra_ngoai_dung_lai_khong_goi_dich():
    f, goi = _buoc([(301, {"location": "https://www.myfxbook.com/members/a/b/1"}, b"", "")])
    st, text, loi = LC.lay_http("https://bit.ly/abc", mot_buoc=f)
    assert st == 301 and text == "" and loi == "chuyen huong ra ngoai: https://www.myfxbook.com/members/a/b/1"
    assert goi == ["https://bit.ly/abc"]                              # dich KHONG bi goi


@pytest.mark.parametrize("dich", ["http://mql5.com/x", "https://127.0.0.1/x", "https://192.168.1.5/admin", "https://evil.example/x"])
def test_lay_http_khong_theo_ha_cap_http_hay_dia_chi_noi_bo_hay_ten_mien_la(dich):
    f, goi = _buoc([(302, {"location": dich}, b"", ""), (200, {}, b"ok", "")])
    st, text, loi = LC.lay_http("https://mql5.com/x", mot_buoc=f)
    assert loi.startswith("chuyen huong ra ngoai") and len(goi) == 1


def test_lay_http_chuyen_huong_vo_tan_va_loi_mang():
    f, _ = _buoc([(302, {"location": "/a"}, b"", "")] * 10)
    assert LC.lay_http("https://mql5.com/x", mot_buoc=f) == (None, "", "qua nhieu lan chuyen huong")
    f, _ = _buoc([(None, {}, b"", "ConnectionError: x")])
    assert LC.lay_http("https://mql5.com/x", mot_buoc=f) == (None, "", "ConnectionError: x")


class _May(BaseHTTPRequestHandler):
    thay: list = []

    def do_GET(self):
        _May.thay.append({k.lower(): v for k, v in self.headers.items()})
        if self.path == "/chuyen":
            self.send_response(302)
            self.send_header("Location", "https://example.org/dich")
            self.end_headers()
            return
        body = b"x" * 300_000
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_mot_buoc_that_voi_may_chu_cuc_bo_header_tran_va_khong_tu_chuyen_huong(monkeypatch):
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    srv = HTTPServer(("127.0.0.1", 0), _May)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        goc = "http://127.0.0.1:%d" % srv.server_port
        st, dau, body, loi = LC._mot_buoc_that(goc + "/trang", LC.UA, 5, 100_000)
        assert (st, loi) == (200, "") and len(body) == 100_000                       # tran kich thuoc
        h = _May.thay[-1]
        assert h["user-agent"] == LC.UA and "br" not in h["accept-encoding"] and "cookie" not in h and "referer" not in h
        st2, dau2, body2, _ = LC._mot_buoc_that(goc + "/chuyen", LC.UA, 5, 1000)
        assert st2 == 302 and dau2["location"] == "https://example.org/dich" and body2 == b""   # KHONG tu theo
        assert LC._mot_buoc_that("http://127.0.0.1:1/", LC.UA, 2, 100)[0] is None             # cong dong -> loi mang, khong nem
    finally:
        srv.shutdown()


# ============================================================== 2. tham_do mot trang
def _m(url, **kw):
    return LN.phan_loai(url, **kw)


def test_tham_do_ok_ghi_tom_tat_cong_khai_vao_reports_va_dem_robots_vao_nhip(tmp_path):
    url = "https://www.mql5.com/en/signals/2331122"
    web = Web({url: (200, TRANG_TIN_HIEU, "")}, {"https://www.mql5.com/robots.txt": (200, "User-agent: *\nDisallow: /en/admin\n", "")})
    ch, dh = _chay(tmp_path, web)
    r = ch.tham_do(_m(url))
    assert r["ket_qua"] == "OK" and r["so_bang"] == 1 and r["so_tab"] == 2 and r["tom_tat"] == "reports/link_tham_do_%s.json" % r["ma"]
    tom = json.loads((tmp_path / "reports" / ("link_tham_do_%s.json" % r["ma"])).read_text(encoding="utf-8"))
    assert tom["bang"][0]["tieu_de"] == ["Month", "Growth"] and tom["cach"] == "http" and tom["kieu"] == "html"
    assert any("/en/signals/2331122/history" in d and "token=" in d and "SECRETVALUE" not in d for d in tom["diem_cuoi"])   # ten, khong gia tri
    assert web.goi == [CR("https://www.mql5.com/x"), C(url)]
    assert ch.tt.so_hom_nay("mql5.com") == 2 and ch.tt.trang_thai(r["ma"]) == "OK"       # robots.txt cung tinh vao tran ngay
    ch.tham_do(_m("https://www.mql5.com/en/signals/9"))
    assert dh.da_ngu and dh.da_ngu[-1] >= 8 - 1e-6 or sum(dh.da_ngu) >= 8                   # nhip 8 giay giua hai yeu cau cung ten mien


def test_tham_do_link_rieng_chi_ghi_o_may_nha_khong_vao_reports(tmp_path):
    url = "https://www.mql5.com/en/signals/777?token=abc123"
    ch, _ = _chay(tmp_path, Web({url: (200, TRANG_TIN_HIEU, "")}))
    m = _m(url)
    assert m["rieng"]
    r = ch.tham_do(m)
    assert r["ket_qua"] == "OK" and r["tom_tat"] == "local"
    assert (tmp_path / "du_lieu_cao" / "tom_tat" / ("%s.json" % m["ma"])).is_file() and not list((tmp_path / "reports").glob("*"))
    bc = LC.bao_cao_chay([r])
    assert "url" not in bc["muc"][0] and "abc123" not in json.dumps(bc)


def test_tham_do_robots_cam_khong_goi_trang_va_nghi_bay_ngay(tmp_path):
    url = "https://www.mql5.com/en/signals/5"
    web = Web({url: (200, TRANG_TIN_HIEU, "")}, {"https://www.mql5.com/robots.txt": (200, "User-agent: *\nDisallow: /signals\n", "")})
    ch, dh = _chay(tmp_path, web)
    r = ch.tham_do(_m(url))
    assert r["ket_qua"] == "CHAN_ROBOTS" and C(url) not in web.goi
    assert ch.tt.d["link"][r["ma"]]["thu_lai_sau"] == int(dh.t + 7 * 24 * 3600)


def test_tham_do_khong_doc_duoc_robots_thi_khong_cao_luot_nay(tmp_path):
    url = "https://www.mql5.com/en/signals/5"
    web = Web({url: (200, TRANG_TIN_HIEU, "")}, {"https://www.mql5.com/robots.txt": (503, "", "")})
    ch, _ = _chay(tmp_path, web)
    r = ch.tham_do(_m(url))
    assert r["ket_qua"] == "LOI_MANG" and C(url) not in web.goi


def test_tham_do_429_ca_ten_mien_nghi_link_khac_cung_mien_khong_duoc_goi(tmp_path):
    u1, u2 = "https://www.mql5.com/en/signals/1", "https://www.mql5.com/en/signals/2"
    web = Web({u1: (429, "", ""), u2: (200, TRANG_TIN_HIEU, "")})
    ch, dh = _chay(tmp_path, web)
    assert ch.tham_do(_m(u1))["ket_qua"] == "CHAN_TAN_SUAT"
    r2 = ch.tham_do(_m(u2))
    assert r2["ket_qua"] == "CHO" and "nghi" in r2["ly_do"] and C(u2) not in web.goi
    dh.t += 20 * 60                                                   # qua 15 phut: duoc thu lai, khong con nghi
    assert ch.tham_do(_m(u2))["ket_qua"] == "OK"


def test_tham_do_trang_cloudflare_la_chan_cam_khong_phai_ok(tmp_path):
    u = "https://www.myfxbook.com/members/abc/def/123456"
    ch, _ = _chay(tmp_path, Web({u: (200, "<html><title>Just a moment...</title>cf-chl</html>", "")}))
    r = ch.tham_do(_m(u), cdp=False)
    assert r["ket_qua"] == "CHAN_CAM" and r["ma"] not in {p.stem for p in (tmp_path / "reports").glob("*")}


def test_tham_do_json_tom_tat_khoa_va_che_chuoi_giong_token(tmp_path):
    u = "https://www.mql5.com/en/signals/1/api/history"
    j = {"rows": [{"time": 1700000000123, "symbol": "AUDCAD", "profit": -1.5, "who": "bob@x.com",
                   "sess": "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7"}] * 3, "total": 3}
    ch, _ = _chay(tmp_path, Web({u: (200, json.dumps(j), "")}))
    r = ch.tham_do(_m(u))
    assert r["ket_qua"] == "OK" and r["kieu"] == "json"
    tom = json.loads((tmp_path / "reports" / ("link_tham_do_%s.json" % r["ma"])).read_text(encoding="utf-8"))
    mau = tom["cau_truc"]["rows"]
    assert mau["kieu"] == "list" and mau["so_phan_tu"] == 3 and mau["mau"][0]["time"] == 1700000000123    # giu dinh dang gio (khong che so dai)
    assert mau["mau"][0]["who"] == "<email>" and mau["mau"][0]["sess"] == "<chuoi_dai_giong_token>"


def test_tham_do_link_rut_gon_ghi_dich_den_va_luot_sau_co_ca_link_dich(tmp_path):
    short = "https://bit.ly/3abcXYZ"
    dich = "https://www.myfxbook.com/members/abc/def/123456"
    web = Web({short: (301, "", "chuyen huong ra ngoai: " + dich)})
    ch, _ = _chay(tmp_path, web)
    (tmp_path / "link_rieng.txt").write_text(short + "\n", encoding="utf-8")
    r = ch.tham_do(_m(short))
    assert r["ket_qua"] == "CHUYEN_HUONG" and r["dich"]["nen_tang"] == "myfxbook" and ch.tt.trang_thai(r["ma"]) == "XONG"
    muc = ch.muc_day_du()
    assert {m["nen_tang"] for m in muc} == {"rut_gon", "myfxbook"}
    assert "dich" in json.dumps(LC.bao_cao_chay([r])) and dich not in json.dumps(LC.bao_cao_chay([r]))   # bao cao chi co ma + nen tang


@pytest.mark.parametrize("url", ["https://www.facebook.com/groups/vipforex/", "https://t.me/+AbCdEfGh123456", "https://zalo.me/g/abc",
                                 "https://drive.google.com/file/d/1abc/view", "http://192.168.1.2/x"])
def test_tham_do_khong_tu_dong_voi_nen_tang_khong_cho_phep(tmp_path, url):
    web = Web()
    ch, _ = _chay(tmp_path, web)
    r = ch.tham_do(_m(url))
    assert r["ket_qua"] == "BO_QUA" and web.goi == []


def test_tham_do_het_tran_luot_la_cho_chu_khong_nem(tmp_path):
    web = Web({"https://www.mql5.com/en/signals/%d" % i: (200, TRANG_TIN_HIEU, "") for i in range(5)})
    ch, _ = _chay(tmp_path, web, tran_luot=3)                         # robots (1) + 2 trang
    kq = [ch.tham_do(_m("https://www.mql5.com/en/signals/%d" % i))["ket_qua"] for i in range(5)]
    assert kq[:2] == ["OK", "OK"] and set(kq[2:]) == {"CHO"}


# ============================================================== 3. Chrome (CDP) gia
def _cdp_gia(html=TRANG_TIN_HIEU, xhr=None, tab=None, loi=""):
    goi = []

    def f(url, truoc=None, **_):
        if loi != "khong_mo_cdp" and truoc:
            truoc(url)
        goi.append(url)
        return {"status": 200, "html": html, "xhr": xhr or [], "tab_lich_su": tab or [], "loi": loi}
    f.goi = goi
    return f


def test_cdp_tom_tat_o_may_nha_xhr_chi_co_ten_va_tab_lich_su(tmp_path):
    u = "https://www.myfxbook.com/members/abc/def/123456"
    tab = [{"html": "<table><tr><th>Open Date</th><th>Symbol</th><th>Action</th><th>Lots</th></tr><tr><td>1</td><td>EURUSD</td><td>Buy</td>"
                    "<td>0.1</td></tr></table>", "xhr": ["https://www.myfxbook.com/api/get-history.json?id=123456&session=ABCSECRET"]}]
    cdp = _cdp_gia(xhr=["https://www.myfxbook.com/api/get-stats.json?id=1"], tab=tab)
    ch, _ = _chay(tmp_path, Web(), lay_cdp=cdp)
    r = ch.tham_do(_m(u))                                             # myfxbook: cach_lay = cdp
    assert r["cach"] == "cdp" and r["ket_qua"] == "OK" and r["tom_tat"] == "local"
    tom = json.loads((tmp_path / "du_lieu_cao" / "tom_tat" / ("%s.json" % r["ma"])).read_text(encoding="utf-8"))
    assert tom["tab_lich_su"][0]["bang"][0]["tieu_de"][:2] == ["Open Date", "Symbol"]
    xs = json.dumps(tom["xhr"] + tom["tab_lich_su"][0]["xhr_sau_khi_bam"])
    assert "get-history.json" in xs and "session=" in xs and "ABCSECRET" not in xs and "123456" not in xs   # ten tham so, khong gia tri
    assert not list((tmp_path / "reports").glob("*"))                                                      # khong tu gui di


def test_cdp_khong_co_chrome_khong_ghi_trang_thai_va_khong_tinh_la_loi(tmp_path):
    ch, _ = _chay(tmp_path, Web(), lay_cdp=_cdp_gia(loi="khong_mo_cdp"))
    m = _m("https://www.myfxbook.com/members/abc/def/123456")
    r = ch.tham_do(m)
    assert r["ket_qua"] == "KHONG_CO_CHROME" and ch.tt.trang_thai(m["ma"]) == "CHUA_LAM" and ch.tt.d["link"] == {}


def test_cdp_voi_link_http_dung_khoa_rieng_khong_de_len_trang_thai_http(tmp_path):
    u = "https://www.mql5.com/en/signals/2331122"
    web = Web({u: (200, TRANG_TIN_HIEU, "")})
    ch, _ = _chay(tmp_path, web, lay_cdp=_cdp_gia())
    m = _m(u)
    assert m["cach_lay"] == "http" and m["du_phong"] == "cdp"
    assert ch.tham_do(m, cdp=False)["ket_qua"] == "OK"
    assert ch.tham_do(m, cdp=True)["ket_qua"] == "OK"
    assert ch.tt.trang_thai(m["ma"]) == "OK" and ch.tt.trang_thai(m["ma"] + "~cdp") == "OK"


def test_lay_cdp_that_bao_khong_mo_cdp_khi_khong_co_chrome(monkeypatch):
    from nhan import doc_trinh_duyet as DT
    monkeypatch.setattr(DT, "cdp_dang_chay", lambda *a, **k: None)
    r = LC.lay_cdp_that("https://www.myfxbook.com/x")
    assert r["loi"] == "khong_mo_cdp" and r["html"] == "" and r["xhr"] == []


# ============================================================== 4. chon mau
def _nhieu_link(n_tin_hieu=6, n_ma_nguon=3):
    lk = ["https://www.mql5.com/en/signals/%d" % (1000 + i) for i in range(n_tin_hieu)]
    lk += ["https://www.mql5.com/en/code/%d" % (50 + i) for i in range(n_ma_nguon)]
    lk += ["https://www.facebook.com/groups/abc", "https://t.me/+AbCdEfGh1234", "https://www.myfxbook.com/members/a/b/1",
           "https://www.myfxbook.com/members/c/d/2"]
    return [_m(u) for u in lk]


def test_chon_mau_moi_loai_toi_da_hai_va_tinh_ca_cai_da_lam(tmp_path):
    ch, _ = _chay(tmp_path)
    muc = _nhieu_link()
    chon = ch.chon_mau(muc, toi_da=50)
    dem = {}
    for e in chon:
        dem[(e["nen_tang"], e["loai"])] = dem.get((e["nen_tang"], e["loai"]), 0) + 1
    assert dem == {("mql5", "tin_hieu"): 2, ("mql5", "ma_nguon"): 2} and not any(e["_cdp"] for e in chon)   # facebook/telegram/myfxbook: khong
    ch.tt.ghi(chon[0]["ma"], "www.mql5.com", "OK")                    # mot tin hieu da xong -> con dung mot suat cho tin hieu
    chon2 = ch.chon_mau(muc, toi_da=50)
    assert sum(1 for e in chon2 if e["loai"] == "tin_hieu") == 1
    assert sum(1 for e in ch.chon_mau(muc, toi_da=50, lai=True) if e["loai"] == "tin_hieu") == 2


def test_chon_mau_cdp_them_myfxbook_va_luot_chrome_cho_link_http_co_du_phong(tmp_path):
    ch, _ = _chay(tmp_path)
    chon = ch.chon_mau(_nhieu_link(), toi_da=50, cdp=True)
    cdp = [e for e in chon if e["_cdp"]]
    assert {e["nen_tang"] for e in cdp} == {"myfxbook", "mql5"} and not any(e["nen_tang"] in ("facebook", "telegram") for e in chon)
    assert sum(1 for e in cdp if e["nen_tang"] == "myfxbook") == 2


def test_chon_mau_toi_da_va_link_rut_gon_khong_bi_tran_loai(tmp_path):
    ch, _ = _chay(tmp_path)
    ngan = [_m("https://bit.ly/a%d" % i) for i in range(5)] + _nhieu_link()
    chon = ch.chon_mau(ngan, toi_da=6)
    assert len(chon) == 6 and sum(1 for e in chon if e["nen_tang"] == "rut_gon") == 5


def test_chay_mau_dung_ten_mien_bi_chan_nhung_van_lam_ten_mien_khac(tmp_path):
    muc = [_m("https://www.mql5.com/en/signals/1000"), _m("https://www.mql5.com/en/signals/1001"), _m("https://www.mql5.com/en/code/50"),
           _m("https://github.com/a/b")]
    thu_tu = [e["url"] for e in _chay(tmp_path)[0].chon_mau(muc)]
    mql5 = [u for u in thu_tu if "mql5.com" in u]
    assert len(mql5) == 3
    trang = {u: (200, TRANG_TIN_HIEU, "") for u in thu_tu}
    trang[mql5[0]] = (403, "", "")                                      # link mql5 DAU TIEN bi chan -> ca ten mien nghi trong luot nay
    web = Web(trang)
    ch, _ = _chay(tmp_path, web)
    ket = ch.chay_mau(muc)
    assert [r["ket_qua"] for r in ket if r["nen_tang"] == "mql5"] == ["CHAN_CAM"]
    assert any(r["nen_tang"] == "github" and r["ket_qua"] == "OK" for r in ket)
    assert not any(u in web.goi for u in mql5[1:])
    bc = LC.ghi_bao_cao_chay(ket)
    van_ban = (tmp_path / "reports" / "link_chay_ket_qua.md").read_text(encoding="utf-8")
    assert bc["theo_ket_qua"] == {"CHAN_CAM": 1, "OK": 1} and "Chrome" in van_ban and "tha_vao" in van_ban


# ============================================================== 5. nap tin nhan dan vao: BI MAT KHONG LOT RA
def test_nap_van_ban_luu_link_va_tai_khoan_xem_nhung_ket_qua_khong_chua_bi_mat(tmp_path):
    bc = LC.nap_van_ban(TIN_NHAN, duong_link=tmp_path / "link_rieng.txt")
    ra = json.dumps(bc, ensure_ascii=False)
    for bi_mat in (MAT_KHAU, LOGIN, MAY_CHU, "Zq9XkLmN0pQrStUv", "sieuloi_bot_vn", "2331122"):
        assert bi_mat not in ra
    assert bc["link_tong"] == 2 and bc["link_moi"] == 2 and bc["mql5_tin_hieu"] == 1 and bc["tai_khoan_xem"] == {"thay": 1, "moi_luu": 1}
    assert bc["telegram_goi_y"] == 1 and bc["tu_khoa"]["luoi"] >= 1 and bc["tu_khoa"]["dca"] >= 1
    assert MOI_NHOM in (tmp_path / "link_rieng.txt").read_text(encoding="utf-8")
    kho = json.loads(PV.KHO.read_text(encoding="utf-8"))["tai_khoan"]
    assert len(kho) == 1 and kho[0]["mat_khau"] == MAT_KHAU and str(kho[0]["login"]) == LOGIN
    assert "sieuloi_bot_vn" in LC.GOI_Y_TELEGRAM.read_text(encoding="utf-8")
    again = LC.nap_van_ban(TIN_NHAN, duong_link=tmp_path / "link_rieng.txt")
    assert again["link_moi"] == 0 and again["tai_khoan_xem"]["moi_luu"] == 0                      # nap lai khong nhan doi


def test_html_thanh_chu_lay_href_va_bo_script_json_thanh_chu_lay_khoa_van_ban():
    h = ('<html><script>var u="https://evil.example/zzz";</script><p>xem <a href="https://www.mql5.com/en/signals/42">link...</a></p>'
         '<style>.a{}</style><div>Login 88776655</div></html>')
    c = LC.html_thanh_chu(h)
    assert "https://www.mql5.com/en/signals/42" in c and "evil.example" not in c and "88776655" in c
    j = {"name": "Nhom", "id": 5, "messages": [{"from": "A", "date": "2024", "text": ["xem ", {"type": "link", "text": "https://t.me/abc_def_ghi"},
                                                                                       {"type": "text_link", "text": "x", "href": "https://github.com/a/b"}],
                                                "file_name": "ReportHistory-1.html"}, {"text": "chao"}]}
    t = LC.json_thanh_chu(j)
    assert "https://t.me/abc_def_ghi" in t and "https://github.com/a/b" in t and "chao" in t and "ReportHistory-1.html" in t and "Nhom" not in t


# ============================================================== 6. nap thu muc tha_vao
def _tbl(hang):
    return "<table>" + "".join("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>" for r in hang) + "</table>"


def _vi_the(n=40, ma="AUDCAD"):
    """n vi the dong: (mo, dong, chieu, lot, gia_mo, gia_dong, loi). Chieu luan phien, moi vi the 1 gio."""
    ra = []
    for i in range(n):
        ngay = 1 + i // 20
        gio = 8 + (i % 20) // 2
        ph = 0 if i % 2 == 0 else 30
        ra.append(("2024.02.%02d %02d:%02d:00" % (ngay, gio, ph), "2024.02.%02d %02d:%02d:00" % (ngay, gio + 1, ph),
                   "buy" if i % 2 == 0 else "sell", "0.10", "%.5f" % (0.88 + i * 1e-4), "%.5f" % (0.881 + i * 1e-4), "%.2f" % (1 + i % 3)))
    return ra


def _html_mt5(n=40, ma="AUDCAD"):
    pos = [["Time", "Position", "Symbol", "Type", "Volume", "Price", "S / L", "T / P", "Time", "Price", "Commission", "Swap", "Profit"]]
    deals = [["Time", "Deal", "Symbol", "Type", "Direction", "Volume", "Price", "Order", "Commission", "Fee", "Swap", "Profit", "Balance"]]
    for i, (mo, dong, ch, lot, g1, g2, loi) in enumerate(_vi_the(n, ma)):
        pos.append([mo, str(1000 + i), ma.lower(), ch, lot, g1, "", "", dong, g2, "-0.7", "0", loi])
        deals.append([mo, str(5000 + 2 * i), ma.lower(), ch, "in", lot, g1, "1", "-0.7", "0", "0", "0", "10000"])
        deals.append([dong, str(5001 + 2 * i), ma.lower(), "sell" if ch == "buy" else "buy", "out", lot, g2, "2", "0", "0", "0", loi, "10001"])
    return "<html><body>%s%s</body></html>" % (_tbl(pos), _tbl(deals))


def _html_mt4(n=40, ma="AUDCAD"):
    hdr = ["Ticket", "Open Time", "Type", "Size", "Item", "Price", "S / L", "T / P", "Close Time", "Price", "Commission", "Taxes", "Swap", "Profit"]
    rows = [hdr] + [[str(i), mo, ch, lot, ma.lower(), g1, "0.0", "0.0", dong, g2, "0", "0", "0", loi]
                    for i, (mo, dong, ch, lot, g1, g2, loi) in enumerate(_vi_the(n, ma))]
    rows.append(["", "", "balance", "", "", "", "", "", "", "", "", "", "", "10000"])
    return "<html><body>%s%s%s</body></html>" % (_tbl([["Closed Transactions:"]]), _tbl(rows), _tbl([["Open Trades:"]]))


def _csv_bao_cao(n=35, ma="EURUSD"):
    d = ["Time,Type,Volume,Symbol,Price,Close Time,Close Price,Profit"]
    for mo, dong, ch, lot, g1, g2, loi in _vi_the(n):
        d.append("%s,%s,%s,%s,%s,%s,%s,%s" % (mo, ch, lot, ma, g1, dong, g2, loi))
    return "\n".join(d)


def _tha(tmp_path, ten, noi_dung):
    d = LN.THA_VAO
    d.mkdir(parents=True, exist_ok=True)
    (d / ten).write_bytes(noi_dung if isinstance(noi_dung, bytes) else noi_dung.encode("utf-8"))


def _nap(tmp_path, **kw):
    return LC.nap_thu_muc(duong_link=tmp_path / "link_rieng.txt", **kw)


def test_nap_thu_muc_bao_cao_mt5_chon_positions_ghi_csv_va_doc_lai_dung(tmp_path):
    _tha(tmp_path, "ReportHistory-%s.html" % LOGIN, _html_mt5(40))
    bc = _nap(tmp_path)
    r = bc["tep"][0]
    assert r["ket_qua"] == "DA_NAP" and r["so_lenh"] == 40 and r["so_dong"] == 40 and r["ma"] == {"AUDCAD": 40}
    csv = tmp_path / r["tep_lenh"][0]
    assert csv.is_file() and csv.parent == tmp_path / "du_lieu_cao" / "lenh"
    d = BL.chuan_hoa(csv)
    assert len(d) == 40 and d["dong"].notna().all() and (d["gia_dong"] > d["gia_mo"]).all() and d["chieu"].iloc[:2].tolist() == [1, -1]
    assert bc["so_lenh_nap"] == 40


def test_nap_thu_muc_bao_cao_mt4_va_csv(tmp_path):
    _tha(tmp_path, "statement.htm", _html_mt4(33))
    _tha(tmp_path, "history.csv", _csv_bao_cao(35))
    bc = _nap(tmp_path)
    kq = {t["so_lenh"]: t for t in bc["tep"]}
    assert set(kq) == {33, 35} and all(t["ket_qua"] == "DA_NAP" for t in bc["tep"])
    assert kq[33]["ma"] == {"AUDCAD": 33} and kq[35]["ma"] == {"EURUSD": 35}


def test_nap_thu_muc_bao_cao_it_lenh_khong_ghi_csv_va_noi_ly_do(tmp_path):
    _tha(tmp_path, "ReportHistory-1.html", _html_mt5(12))
    r = _nap(tmp_path)["tep"][0]
    assert r["ket_qua"] == "QUA_IT_LENH" and r["so_lenh"] == 12 and not r.get("tep_lenh") and "30" in r["ly_do"]
    assert not (tmp_path / "du_lieu_cao" / "lenh").exists() or not list((tmp_path / "du_lieu_cao" / "lenh").glob("*.csv"))


def test_nap_thu_muc_tin_nhan_trang_luu_va_xuat_telegram(tmp_path):
    _tha(tmp_path, "tin nhan vip.txt", TIN_NHAN)
    _tha(tmp_path, "trang luu.html", '<html><a href="https://www.mql5.com/en/signals/42424">x</a> <script>var a="https://evil.example";</script></html>')
    j = {"messages": [{"text": ["bot lai khung ", {"type": "text_link", "text": "xem", "href": "https://www.myfxbook.com/members/q/w/9"}]}]}
    _tha(tmp_path, "result.json", json.dumps(j))
    bc = _nap(tmp_path)
    assert {t["ket_qua"] for t in bc["tep"]} == {"DA_NAP_CHU"}
    lk = (tmp_path / "link_rieng.txt").read_text(encoding="utf-8")
    assert "signals/42424" in lk and "myfxbook.com/members/q/w/9" in lk and MOI_NHOM in lk and "evil.example" not in lk
    assert len(json.loads(PV.KHO.read_text(encoding="utf-8"))["tai_khoan"]) == 1


def test_nap_thu_muc_ea_excel_pdf_anh_la_ghi_nhan_khong_thuc_thi(tmp_path):
    _tha(tmp_path, "Grid.ex5", b"MZ\x90\x00binary")
    _tha(tmp_path, "Grid.mq5", "// ea\ninput double Lot=0.1;")
    _tha(tmp_path, "preset.set", "Lot=0.1")
    _tha(tmp_path, "sao_ke.xlsx", b"PK\x03\x04xlsx")
    _tha(tmp_path, "a.png", b"\x89PNG")
    kq = {t["tep"].split(".")[-1]: t["ket_qua"] for t in _nap(tmp_path)["tep"]}
    assert kq == {"ex5": "EA_BIEN_DICH", "mq5": "EA_NGUON", "set": "THAM_SO", "xlsx": "CAN_CHUYEN_SANG_CSV", "png": "BO_QUA"}


def test_nap_thu_muc_zip_doc_bang_bo_nho_khong_ghi_ra_ngoai_va_bo_tep_nguy_hiem(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("nhom/ReportHistory-1.csv", _csv_bao_cao(40))
        z.writestr("../../evil.txt", "https://www.mql5.com/en/signals/31337")
        z.writestr("setup.exe", b"MZ")
        z.writestr("EA.ex5", b"MZ")
        z.writestr("ghi chu.txt", "link https://github.com/foo/bar")
    _tha(tmp_path, "goi.zip", buf.getvalue())
    _tha(tmp_path, "hong.zip", b"khong phai zip")
    bc = _nap(tmp_path)
    z = next(t for t in bc["tep"] if t["ket_qua"] == "ZIP")
    kq = sorted(c["ket_qua"] for c in z["ben_trong"])
    assert kq == ["DA_NAP", "DA_NAP_CHU", "DA_NAP_CHU", "EA_BIEN_DICH"] and any(t["ket_qua"] == "ZIP_HONG" for t in bc["tep"])
    assert not (tmp_path.parent / "evil.txt").exists() and not (tmp_path / "evil.txt").exists()
    assert "setup.exe" not in json.dumps(bc) and bc["so_lenh_nap"] == 40


def test_nap_thu_muc_manifest_bo_qua_tep_cu_va_nap_lai_khi_doi_noi_dung(tmp_path):
    _tha(tmp_path, "a.txt", "https://github.com/a/b")
    assert _nap(tmp_path)["tep"][0]["ket_qua"] == "DA_NAP_CHU"
    assert _nap(tmp_path)["tep"][0]["ket_qua"] == "DA_NAP_TRUOC_DO"
    _tha(tmp_path, "a.txt", "https://github.com/a/b va https://github.com/c/d")
    r = _nap(tmp_path)["tep"][0]
    assert r["ket_qua"] == "DA_NAP_CHU" and r["link_moi"] == 1


def test_nap_thu_muc_bao_cao_khong_lo_ten_tep_login_hay_mat_khau(tmp_path):
    _tha(tmp_path, "Nhom VIP John Smith - ReportHistory-%s.html" % LOGIN, _html_mt5(40))
    _tha(tmp_path, "tin nhan John.txt", TIN_NHAN)
    bc = LC.ghi_bao_cao_nap(_nap(tmp_path))
    mo_ta = json.dumps(bc, ensure_ascii=False) + (tmp_path / "reports" / "link_nap_ket_qua.md").read_text(encoding="utf-8") + \
        (tmp_path / "reports" / "link_nap_ket_qua.json").read_text(encoding="utf-8")
    for bi_mat in ("John", "Smith", LOGIN, MAT_KHAU, MAY_CHU, "Zq9XkLmN", "sieuloi"):
        assert bi_mat not in mo_ta
    assert all(p.stat().st_size < 40_000 for p in (tmp_path / "reports").glob("*"))


def test_nap_thu_muc_tep_hong_khong_lam_sap_ca_thu_muc(tmp_path):
    _tha(tmp_path, "x.html", "<html><table><tr><td>Time</td><td>Type</td><td>Volume</td><td>Price</td></tr>")   # bang cut
    _tha(tmp_path, "y.json", "{khong phai json")
    _tha(tmp_path, "tot.txt", "https://github.com/a/b")
    kq = sorted(t["ket_qua"] for t in _nap(tmp_path)["tep"])
    assert "DA_NAP_CHU" in kq and len(kq) == 3 and "LOI_XU_LY" not in kq


def test_nap_thu_muc_thu_muc_chua_co_thi_tao_va_bao_trong(tmp_path):
    bc = _nap(tmp_path)
    assert bc["so_tep"] == 0 and LN.THA_VAO.is_dir() and "TRONG" in LC.bao_cao_nap_van_ban(bc)


# ============================================================== 7. thu hoach tai khoan XEM
def _deals(n=40, ma="AUDCAD", t0=1_700_000_000):
    ra = []
    for i in range(n):
        t = t0 + i * 7200
        loai = 0 if i % 2 == 0 else 1
        ra.append(dict(time=t, symbol=ma, type=loai, volume=0.1, price=0.88 + i * 1e-4, profit=0.0, entry=0, position_id=100 + i,
                       commission=-0.7, swap=0.0, magic=7, reason=3, comment="", sl=0.0, tp=0.0, ticket=2 * i + 1))
        ra.append(dict(time=t + 3600, symbol=ma, type=1 - loai, volume=0.1, price=0.881 + i * 1e-4, profit=1.5, entry=1, position_id=100 + i,
                       commission=0.0, swap=0.0, magic=7, reason=5, comment="", sl=0.0, tp=0.0, ticket=2 * i + 2))
    return ra


def _luu_tk(login=LOGIN, server=MAY_CHU, mat_khau=MAT_KHAU):
    return PV.luu([{"login": login, "server": server, "mat_khau": mat_khau}], nguon="tha_vao")


def test_thu_hoach_doc_duoc_ghi_csv_cap_nhat_kho_va_bao_cao_khong_lo_tai_khoan(tmp_path):
    _luu_tk()
    goi = []

    def doc(login, mat_khau, server):
        goi.append((login, mat_khau, server))
        return {"account": {"login": login, "server": server, "loai": "DEMO"}, "deals": _deals(40), "positions": []}

    dh = DongHo()
    kq = LC.thu_hoach_passview(doc=doc, dong_ho=dh, ngu=dh.ngu)
    assert goi == [(int(LOGIN), MAT_KHAU, MAY_CHU)]
    assert kq["doc_duoc"] == 1 and kq["khong_doc"] == 0 and kq["lenh_tong"] == 40 and kq["tk"][0]["loai"] == "DEMO"
    csv = tmp_path / kq["tk"][0]["tep"][0]
    assert csv.is_file() and len(BL.chuan_hoa(csv)) == 40
    ra = json.dumps(kq)
    for bi_mat in (MAT_KHAU, LOGIN, MAY_CHU):
        assert bi_mat not in ra and bi_mat not in str(csv)
    t = PV.danh_sach()[0]
    assert t["trang_thai"] == "DA_DOC" and t["so_lenh"] == 40
    assert LC.thu_hoach_passview(doc=doc, dong_ho=dh, ngu=dh.ngu)["den_luot"] == 0 and len(goi) == 1    # da doc: khong doc lai


def test_thu_hoach_loi_dang_nhap_thu_lai_sau_24_gio_va_bo_cuoc_sau_3_lan(tmp_path):
    _luu_tk()
    lan = []

    def doc(login, mat_khau, server):
        lan.append(1)
        raise PV.KhongDoc("initialize that bai: (-6, 'Terminal: Authorization failed') login %s" % login)

    dh = DongHo()
    kq = LC.thu_hoach_passview(doc=doc, dong_ho=dh, ngu=dh.ngu)
    assert kq["khong_doc"] == 1 and LOGIN not in json.dumps(kq) and PV.danh_sach()[0]["trang_thai"] == "KHONG_DOC"
    assert LOGIN not in PV.danh_sach()[0]["loi"]
    assert LC.thu_hoach_passview(doc=doc, dong_ho=dh, ngu=dh.ngu)["den_luot"] == 0               # chua du 24 gio
    for _ in range(4):
        dh.t += 25 * 3600
        LC.thu_hoach_passview(doc=doc, dong_ho=dh, ngu=dh.ngu)
    assert len(lan) == 3 and PV.danh_sach()[0]["so_loi"] == 3                                      # 3 lan roi thoi


def test_thu_hoach_toi_da_va_cach_giay_giua_cac_tai_khoan(tmp_path):
    for i in range(4):
        _luu_tk(login=str(10000000 + i))
    dh = DongHo()
    kq = LC.thu_hoach_passview(toi_da=3, doc=lambda l, p, s: {"account": {"loai": "DEMO"}, "deals": [], "positions": []}, dong_ho=dh, ngu=dh.ngu,
                               cach_giay=15)
    assert kq["da_thu"] == 3 and kq["den_luot"] == 4 and dh.da_ngu == [15, 15]


def test_thu_hoach_chi_dung_ham_doc_cua_passview():
    """`thu_hoach_passview` khong tu goi bat ky ham MT5 nao: chi `doc` duoc tiem (that: passview.doc_lich_su - da bi test khoa chi-doc)."""
    nguon = Path(LC.__file__).read_text(encoding="utf-8")
    assert "order_send" not in nguon and "order_check" not in nguon and "MetaTrader5" not in nguon


# ============================================================== 8. chia se, bao cao
def test_chia_se_chi_cho_link_cong_khai_da_co_tom_tat_cuc_bo(tmp_path):
    pub = "https://www.myfxbook.com/members/abc/def/123456"
    rieng = "https://www.mql5.com/en/signals/9?token=SECRET99"
    (tmp_path / "link_rieng.txt").write_text(pub + "\n" + rieng + "\n", encoding="utf-8")
    ch, _ = _chay(tmp_path, Web({rieng: (200, TRANG_TIN_HIEU, "")}), lay_cdp=_cdp_gia())
    r = ch.tham_do(_m(pub))
    assert r["tom_tat"] == "local"
    kw = dict(thu_muc_tom_tat=tmp_path / "du_lieu_cao" / "tom_tat", thu_muc_reports=tmp_path / "reports", tt=ch.tt, duong_link=tmp_path / "link_rieng.txt")
    ok, ly = LC.chia_se(r["ma"], **kw)
    assert ok and (tmp_path / "reports" / ("link_tham_do_%s.json" % r["ma"])).is_file()
    mr = _m(rieng)
    ch.tham_do(mr)                                                    # co tom tat cuc bo nhung la link RIENG
    ok2, ly2 = LC.chia_se(mr["ma"], **kw)
    assert not ok2 and "RIENG" in ly2 and not (tmp_path / "reports" / ("link_tham_do_%s.json" % mr["ma"])).exists()
    assert LC.chia_se("zzzz", **kw)[0] is False and LC.chia_se("0123456789", **kw)[0] is False
    assert LC.chia_se("../../etc/pw", **kw)[0] is False


def test_vua_gioi_han_cat_danh_sach_cho_vua_40k_va_van_la_json_hop_le():
    d = {"xhr": ["https://x.example/api/%d?a=&b=" % i + "z" * 100 for i in range(2000)], "bang": [{"a": 1}] * 5, "cau_truc": {"k": "v" * 60000}}
    ra = LC._vua_gioi_han(d, ("xhr", "bang"))
    s = json.dumps(ra)
    assert len(s) < 40_000 and ra["da_cat"] and isinstance(json.loads(s)["cau_truc"], (dict, str))


# ============================================================== 9. CLI + vien rang buoc
def _cli(argv, capsys):
    rc = LC.main(argv)
    return rc, capsys.readouterr().out


def test_cli_ke_hoach_them_thu_muc_va_bao_cao_khong_in_bi_mat(tmp_path, capsys):
    rc, out = _cli(["ke-hoach"], capsys)
    assert rc == 0 and "CHUA CO LINK" in out
    rc, out = _cli(["them", TIN_NHAN], capsys)
    assert rc == 0 and MAT_KHAU not in out and LOGIN not in out and "Zq9Xk" not in out
    rc, out = _cli(["ke-hoach"], capsys)
    assert "2 link" in out and "RIENG" in out and MOI_NHOM not in out and "tha_vao" in out
    _tha(tmp_path, "r.html", _html_mt5(40))
    rc, out = _cli(["thu-muc"], capsys)
    assert rc == 0 and "DA_NAP" in out and "40 lenh" in out
    rc, out = _cli(["bao-cao"], capsys)
    assert rc == 0 and "NAP THU MUC" in out and "LINK CUA CHU DU AN" in out


def test_cli_tham_do_tu_choi_ten_mien_chua_duyet_va_link_rieng(tmp_path, capsys):
    for url in ("https://evil.example/x", "http://www.mql5.com/x", "https://www.mql5.com/en/signals/1?token=abc", "https://127.0.0.1/x"):
        rc, out = _cli(["tham-do", url], capsys)
        assert rc == 2 and out.startswith("TU CHOI")


def test_cli_chia_se_ma_sai_dinh_dang(tmp_path, capsys):
    rc, out = _cli(["chia-se", "abc"], capsys)
    assert rc == 1 and "KHONG CHIA SE" in out


def test_ma_nguon_chi_chua_ascii_va_khong_in_url_rieng_ra_man_hinh():
    nguon = Path(LC.__file__).read_text(encoding="utf-8")
    assert nguon.isascii()
    # moi lenh print trong CLI chi in so dem / van ban tu ham bao cao, khong in `url` hay `nhan` cua link
    for dong in nguon.splitlines():
        if "print(" in dong and "in_ra" not in dong:
            assert 'url"' not in dong and "nhan" not in dong.replace("nhan import", "")


# =============================================================== NOI VAO HE THONG: b link + DANH SACH TRANG
def test_c_link_nam_trong_bang_LENH_va_goi_duoc_CLI(tmp_path, capsys):
    import b as B
    assert B.LENH["link"] is B.c_link
    assert B.c_link(["bao-cao"]) == 0                                 # khong goi mang, khong can may that


class TestDanhSachTrangLink:
    from qwen import cau_trang as CT                                    # noqa: E402  (chi dung trong lop nay)

    @pytest.mark.parametrize("lenh", [
        ["{py}", "b.py", "link", "ke-hoach"],
        ["{py}", "b.py", "link", "chay"],
        ["{py}", "b.py", "link", "chay", "--toi-da", "12", "--theo-nen", "2", "--lai"],
        ["{py}", "b.py", "link", "tham-do", "https://mql5.com/signals/2331122"],
        ["{py}", "b.py", "link", "tham-do", "https://www.myfxbook.com/members/abc/def/123456"],
        ["{py}", "b.py", "link", "thu-muc"],
        ["{py}", "b.py", "link", "thu-muc", "--toi-thieu", "30"],
        ["{py}", "b.py", "link", "bao-cao"],
        ["{py}", "b.py", "link", "chia-se", "0123456789"],
    ])
    def test_cho_qua(self, lenh):
        assert self.CT.kiem_lenh(lenh) is None, self.CT.kiem_lenh(lenh)

    @pytest.mark.parametrize("lenh", [
        ["{py}", "b.py", "link"],                                           # phai goi ro lenh con
        ["{py}", "b.py", "link", "them", "https://mql5.com/signals/1"],     # ghi vao link_rieng.txt: chi chu du an
        ["{py}", "b.py", "link", "nap-van-ban", "-"],
        ["{py}", "b.py", "link", "tai-khoan-xem"],                          # dung mat khau investor da luu
        ["{py}", "b.py", "link", "telegram-quet"],                          # dung phien Telegram cua chu du an
        ["{py}", "b.py", "link", "chay", "--cdp"],                          # Chrome da dang nhap
        ["{py}", "b.py", "link", "tham-do", "https://mql5.com/signals/1", "--cdp"],
        ["{py}", "b.py", "link", "chay", "--toi-da", "41"],
        ["{py}", "b.py", "link", "chay", "--toi-da", "0"],
        ["{py}", "b.py", "link", "chay", "--toi-da"],
        ["{py}", "b.py", "link", "chay", "--toi-da", "5; rm -rf /"],
        ["{py}", "b.py", "link", "chay", "--lai", "--lai"],
        ["{py}", "b.py", "link", "tham-do"],                                # thieu URL
        ["{py}", "b.py", "link", "tham-do", "http://mql5.com/signals/1"],   # khong https
        ["{py}", "b.py", "link", "tham-do", "https://evil.example/x"],      # ten mien chua duyet
        ["{py}", "b.py", "link", "tham-do", "https://127.0.0.1/x"],
        ["{py}", "b.py", "link", "tham-do", "https://facebook.com/groups/abc"],
        ["{py}", "b.py", "link", "tham-do", "https://mql5.com/signals/1?token=abc"],
        ["{py}", "b.py", "link", "chia-se", "xyz"],
        ["{py}", "b.py", "link", "chia-se", "0123456789", "extra"],
        ["{py}", "b.py", "link", "bao-cao", "--ghi"],
    ])
    def test_tu_choi(self, lenh):
        assert self.CT.kiem_lenh(lenh) is not None
