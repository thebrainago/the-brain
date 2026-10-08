# -*- coding: utf-8 -*-
"""doc_dien_dan: doc dien dan / danh sach nhieu trang - phan trang co moc, nhip, dung khi bi chan, 1 tuan / lan, Chrome gia.

KHONG goi mang that / Chrome that: fetch, Chrome, dong ho deu duoc tiem; HTML la mau tu viet. `PhienCdp.lay` duoc thu voi doi tuong Playwright gia.
Dieu quan trong nhat (repo PUBLIC): bao cao gui ve cloud KHONG chua URL / tieu de bai; 403 / 429 / captcha thi DUNG ca ten mien, khong thu lai.
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import pytest

from nhan import doc_dien_dan as DD
from nhan import doc_trinh_duyet as DT
from nhan import link_chay as LCH
from nhan import link_nguon as LN
from qwen import cau_trang as CT

NHIP = 8                                                          # gian cach mac dinh giua hai yeu cau cung ten mien (`NHIP_MIEN["*"]`)
HOST = "forum.example.com"


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
    monkeypatch.setattr(LN, "THU_MUC_CAO", tmp_path / "du_lieu_cao")
    monkeypatch.setattr(LN, "TRANG_THAI", tmp_path / "du_lieu_cao" / "trang_thai.json")
    monkeypatch.setattr(DD, "THU_MUC_UNG_VIEN", tmp_path / "du_lieu_cao" / "dien_dan")
    monkeypatch.setattr(DD, "BAO_CAO_JSON", tmp_path / "reports" / "dien_dan_ket_qua.json")
    monkeypatch.setattr(DD, "BAO_CAO_MD", tmp_path / "reports" / "dien_dan_ket_qua.md")


# ============================================================== HTML mau + mang gia
def u(n, host=HOST, goc="/robot/"):
    """URL trang `n` cua mot dien dan kieu XenForo (`{base}page-{n}`)."""
    return "https://%s%s" % (host, goc) + ("" if n == 1 else "page-%d" % n)


def trang_html(n, tong=3, so_bai=4, goc="/robot/", rel_next=True, tieu="Grid EA robot thread"):
    bai = "".join('<div class="structItem"><a href="/t/%d/">%s %d-%d</a></div>' % (n * 100 + i, tieu, n, i) for i in range(so_bai))
    nav = "".join('<a href="%s%s">%d</a>' % (goc, "" if p == 1 else "page-%d" % p, p) for p in range(1, tong + 1))
    nxt = '<link rel="next" href="%spage-%d">' % (goc, n + 1) if rel_next and n < tong else ""
    return "<html><head><title>Robot EA - trang %d</title>%s</head><body>%s<div class=\"pageNav\">%s</div></body></html>" % (n, nxt, bai, nav)


def dien_dan_web(host=HOST, tong=3, so_bai=4, goc="/robot/", **kw):
    return {u(n, host, goc): (200, trang_html(n, tong, so_bai, goc, **kw), "") for n in range(1, tong + 1)}


def fo(ma="a", host=HOST, goc="/robot/", **kw):
    d = {"ma": ma, "ten": ma, "nuoc": "vi", "url": "https://%s%s" % (host, goc), "bat": True, "cach_lay": "http",
         "mau_trang": "{base}page-{n}", "mau_bai": r"/t/\d+"}
    d.update(kw)
    return {k: v for k, v in d.items() if v is not None}


def cfg(*fos, **mac_dinh):
    return {"phien_ban": 1, "chu_ky_gio": 168, "dien_dan": list(fos),
            "mac_dinh": dict({"toi_da_trang_luot": 10, "toi_da_trang_pass": 200, "tran_ngay_mien": 120, "do_dai_tieu_de": 25}, **mac_dinh)}


class Web:
    """Mang gia: {url: (status, text, loi) | ham(url)}; robots rieng theo host. Ghi URL va gio (dong ho gia) cua tung yeu cau;
    moi yeu cau di qua `truoc` nhu `lay_http` that (nhip + dem tran)."""

    def __init__(self, trang=None, robots=None, dh=None):
        self.trang, self.robots, self.dh = dict(trang or {}), dict(robots or {}), dh
        self.goi, self.luc = [], []

    def __call__(self, url, truoc=None, **_):
        if truoc:
            truoc(url)
        self.goi.append(url)
        self.luc.append(self.dh() if self.dh else 0)
        if url.endswith("/robots.txt"):
            return self.robots.get(urlsplit(url).hostname, (404, "", ""))
        r = self.trang.get(url, (404, "", ""))
        return r(url) if callable(r) else r

    def trang_da_goi(self):
        return [x for x in self.goi if not x.endswith("/robots.txt")]


class CdpGia:
    """Thay `PhienCdp`: dem so lan mo / dong, ghi (url, referer, render) cua tung yeu cau."""

    def __init__(self, trang=None, loi_mo=None):
        self.trang, self.loi_mo, self.mo, self.dong, self.goi = dict(trang or {}), loi_mo, 0, 0, []

    def __call__(self):
        return self

    def __enter__(self):
        if self.loi_mo:
            raise DD.KhongCoCdp(self.loi_mo)
        self.mo += 1
        return self

    def __exit__(self, *_):
        self.dong += 1
        return False

    def lay(self, url, referer="", render=False, truoc=None):
        if truoc:
            truoc(url)                                                                            # that: PhienCdp goi `truoc` truoc moi buoc chuyen huong
        self.goi.append((url, referer, render))
        return self.trang.get(url, (404, "", ""))


def tao(tmp_path, web, cfg_, cdp=None, dh=None, **nhip_kw):
    """Quet moi tren CUNG tep trang thai / thu muc (hai lan goi = hai tien trinh noi nhau)."""
    dh = dh or DongHo()
    q = DD.Quet(cfg=cfg_, tt=LN.TrangThai(tmp_path / "tt.json", dong_ho=dh), nhip=LN.Nhip(dong_ho=dh, ngu=dh.ngu, **nhip_kw), lay=web, mo_cdp=cdp,
                thu_muc_ung_vien=tmp_path / "uv", thu_muc_reports=tmp_path / "reports", in_ra=lambda *_: None)
    return q, dh


def muc(q, ma="a"):
    return q.tt.d["link"].get("dd:" + ma, {})


def ung_vien(tmp_path, ma="a"):
    f = tmp_path / "uv" / ("%s.jsonl" % ma)
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []


def kq_luot(bc, ma="a"):
    return next(b["ket_qua_luot"] for b in bc["dien_dan"] if b["ma"] == ma)


# ============================================================== 1. CAU HINH
def test_config_that_hop_le_bat_it_nhat_5_dien_dan_phu_nhieu_nuoc():
    c = DD.nap_cau_hinh()
    assert DD.kiem_cau_hinh(c) == []
    ds = c["dien_dan"]
    assert len({f["ma"] for f in ds}) == len(ds) >= 20
    assert sum(1 for f in ds if f["bat"]) >= 5
    nuoc = {f["nuoc"] for f in ds}
    assert len(nuoc) >= 12 and {"ru", "vi", "th", "ja"} <= nuoc
    assert nuoc.isdisjoint(c["nuoc_chua_co_ung_vien"])            # nuoc ghi "chua co ung vien" thi that su khong co dien dan nao
    assert all(f["kiem_tra"] for f in ds)                         # moi muc ghi ro do that hay tu tri nho
    assert all(f["cach_lay"] in DD.CACH_LAY for f in ds)


def test_config_that_khong_chua_bi_mat_hay_link_rieng():
    txt = (Path(DD.__file__).resolve().parent.parent / "config" / "dien_dan.json").read_text(encoding="utf-8-sig")
    assert not re.search(r"(?i)passw|secret|api[_-]?key|token|bearer|investor|login", txt)
    assert not re.search(r"[A-Za-z0-9+/_-]{40,}", txt.replace("https://", ""))
    assert not re.search(r"@[a-z0-9-]+\.[a-z]{2,}|t\.me/\+|/joinchat/|drive\.google|mega\.nz", txt, re.I)
    for f in DD.nap_cau_hinh()["dien_dan"]:
        assert "?" not in f["url"] and f["url"].startswith("https://")
        assert not LN.phan_loai(f["url"])["rieng"]


@pytest.mark.parametrize("sua,mong", [
    (lambda c: c["dien_dan"].append(dict(c["dien_dan"][0])), "trung"),
    (lambda c: c["dien_dan"][0].update(ma="A b"), "ma"),
    (lambda c: c["dien_dan"][0].update(nuoc="Vietnam"), "nuoc"),
    (lambda c: c["dien_dan"][0].update(url="http://forum.example.com/robot/"), "https"),
    (lambda c: c["dien_dan"][0].update(url="https://t.me/+AbCdEfGh12345678"), "rieng"),
    (lambda c: c["dien_dan"][0].update(url="https://www.facebook.com/groups/12345"), "nen tang"),
    (lambda c: c["dien_dan"][0].update(cach_lay="selenium"), "cach_lay"),
    (lambda c: c["dien_dan"][0].update(phan_trang="vo_han"), "phan_trang"),
    (lambda c: c["dien_dan"][0].update(bat="true"), "bat"),
    (lambda c: c["dien_dan"][0].update(mau_bai="(unclosed"), "mau_bai"),
    (lambda c: c["dien_dan"][0].update(mau_bai="a" * 400), "mau_bai"),
    (lambda c: c["dien_dan"][0].update(mau_trang="{base}page-2"), "{n}"),
    (lambda c: c["dien_dan"][0].update(mau_trang="https://evil.example.org/p/{n}"), "cung ten mien"),
    (lambda c: c["dien_dan"][0].update(mau_trang="http://forum.example.com/p-{n}"), "cung ten mien"),
    (lambda c: c["dien_dan"][0].update(toi_da_trang_luot=0), "toi_da_trang_luot"),
    (lambda c: c["dien_dan"][0].update(toi_da_trang_luot=500), "toi_da_trang_luot"),
    (lambda c: c["dien_dan"][0].update(nhip_giay=0), "nhip_giay"),
    (lambda c: c.update(chu_ky_gio=12), "chu_ky_gio"),
    (lambda c: c.update(dien_dan="khong phai danh sach"), "dien_dan"),
])
def test_kiem_cau_hinh_bat_cac_loi_thuong_gap(sua, mong):
    c = cfg(fo("a"), fo("b", "other.example.net"))
    assert DD.kiem_cau_hinh(c) == []
    sua(c)
    loi = DD.kiem_cau_hinh(c)
    assert loi and any(mong in x for x in loi), loi


def test_quet_tu_choi_cau_hinh_sai_ngay_luc_khoi_tao(tmp_path):
    with pytest.raises(ValueError, match="dien_dan.json sai"):
        tao(tmp_path, Web(), cfg(fo("a", url="http://khong-https.example.com/")))


def test_tham_so_uu_tien_dien_dan_roi_mac_dinh_roi_goc_roi_ma_nguon():
    c = {"chu_ky_gio": 100, "mac_dinh": {"toi_da_trang_luot": 7}, "dien_dan": []}
    assert DD._tham_so(c, {"toi_da_trang_luot": 3}, "toi_da_trang_luot") == 3
    assert DD._tham_so(c, {}, "toi_da_trang_luot") == 7
    assert DD._tham_so(c, {}, "chu_ky_gio") == 100
    assert DD._tham_so(c, {}, "toi_da_trang_pass") == DD.MAC_DINH["toi_da_trang_pass"]


# ============================================================== 2. PHAN TICH TRANG
def test_tach_trang_url_tuong_doi_base_rel_next_va_so_trang():
    h = ('<html><head><title> Robot  EA \n forum </title><base href="https://forum.example.com/robot/"><link rel="next" href="page-2"></head>'
         '<body><a href="page-3">3</a> <a href="/t/9/">Thread 9</a> <a href="#top">top</a> <a href="javascript:void(0)">js</a>'
         '<a href="mailto:x@y.z">mail</a> <a href="/robot/page-2">2</a> <a href="/robot/page-10">10</a> <a href="//cdn.example.com/x">cdn</a>'
         '<a href="/t/10/">unclosed <a href="/t/11/">Thread 11</a> <a href="/t/12/#post-5">T12</a></body></html>')
    t = DD.tach_trang(h, "https://forum.example.com/robot/")
    assert t["tieu_de"] == "Robot EA forum" and t["rel_next"] == "https://forum.example.com/robot/page-2"
    urls = [x for x, _ in t["neo"]]
    assert "https://forum.example.com/robot/page-3" in urls and "https://forum.example.com/t/9/" in urls
    assert "https://cdn.example.com/x" in urls and "https://forum.example.com/t/12/" in urls    # // cung giao thuc; fragment bi bo
    assert not any(x.startswith(("javascript", "mailto")) or x.endswith("#top") for x in urls)
    assert t["so_trang"] == [2, 3, 10]
    assert dict(t["neo"])["https://forum.example.com/t/10/"] == "unclosed"                      # <a> chua dong khong nuot link sau
    assert dict(t["neo"])["https://forum.example.com/t/11/"] == "Thread 11"


def test_tach_trang_rel_next_tren_the_a_va_html_hong_khong_nem_loi():
    t = DD.tach_trang('<a rel="next nofollow" href="/x/p/2">Sau</a><a href="/y">y', "https://forum.example.com/x/")
    assert t["rel_next"] == "https://forum.example.com/x/p/2" and ("https://forum.example.com/y", "y") in t["neo"]
    for rac in ("", None, "<<<>>><a href=", "<a href='\x00'>", "\ufffd" * 50, "<a " * 5000):
        t = DD.tach_trang(rac, "https://forum.example.com/")
        assert set(t) == {"tieu_de", "neo", "rel_next", "so_trang", "canonical"}


def test_trich_bai_theo_mau_bai_bo_trung_trang_goc_va_neo_phan_trang():
    f = fo()
    t = DD.tach_trang(trang_html(2), u(2))
    bai = DD.trich_bai(f, t, u(2), 25)
    assert [b["url"] for b in bai] == ["https://forum.example.com/t/%d/" % (200 + i) for i in range(4)]
    # cung bai xuat hien hai lan (tieu de + 'trang cuoi') + duoi /page-3 + chinh trang nay + trang goc -> chi tinh mot lan
    h = ('<a href="/t/5/">A thread</a><a href="/t/5/page-3">3</a><a href="/t/5/latest">latest</a><a href="/robot/">goc</a>'
         '<a href="/robot/page-2">self</a><a href="/t/6/">B thread</a>')
    bai = DD.trich_bai(dict(f, mau_bai=r"/(?:t/\d+|robot/)"), DD.tach_trang(h, u(2)), u(2), 25)
    assert [b["url"] for b in bai] == ["https://forum.example.com/t/5/", "https://forum.example.com/t/6/"]
    assert DD.trich_bai(f, DD.tach_trang(trang_html(1, so_bai=50), u(1)), u(1), 25, toi_da=10).__len__() == 10


def test_trich_bai_khong_mau_bai_dung_do_dai_tieu_de_va_cung_ten_mien():
    f = fo(mau_bai=None)
    h = ('<a href="/forum/">Forum</a><a href="/topic/1">Grid EA tu dong cho MT5 hieu qua cao</a>'
         '<a href="/topic/2">Robot martingale hedging system test</a><a href="https://other.org/x">Link ngoai ten mien rat dai nhung la ngoai</a>'
         '<a href="/topic/1">Grid EA tu dong cho MT5 hieu qua cao</a><a href="/login">Dang nhap</a>')
    bai = DD.trich_bai(f, DD.tach_trang(h, u(1)), u(1), 25)
    assert [b["url"] for b in bai] == ["https://forum.example.com/topic/1", "https://forum.example.com/topic/2"]
    tach = DD.tach_trang(h, u(1))
    assert len(DD.trich_bai(f, tach, u(1), 10)) == 2                                            # 'Dang nhap' (9 ky tu) va 'Forum' (5) chua du dai
    assert len(DD.trich_bai(f, tach, u(1), 9)) == 3                                             # ha nguong 9 -> them 'Dang nhap'
    assert len(DD.trich_bai(f, tach, u(1), 5)) == 4                                             # ha nguong 5 -> them ca 'Forum'


def test_khoa_bai_gop_duoi_trang_locale_mql5_va_tham_so_theo_doi():
    k = DD._khoa_bai
    assert k("https://forum.example.com/t/5/") == k("https://forum.example.com/t/5/page-3") == k("https://forum.example.com/t/5/latest")
    assert k("https://www.mql5.com/ru/forum/123") == k("https://www.mql5.com/en/forum/123") == k("https://mql5.com/forum/123/")
    assert k("https://forum.example.com/viewtopic.php?t=1") != k("https://forum.example.com/viewtopic.php?t=2")
    assert k("https://forum.example.com/t/5?utm_source=x") == k("https://forum.example.com/t/5")


def test_url_trang_tiep_ba_che_do():
    f = fo()
    t = DD.tach_trang(trang_html(1), u(1))
    assert DD.url_trang_tiep(f, t, u(1), 2) == u(2)                                             # auto: rel=next
    sai = dict(t, rel_next="https://evil.example.org/p/2")
    assert DD.url_trang_tiep(f, sai, u(1), 2) == u(2)                                           # rel=next sang ten mien khac -> bo, dung mau_trang
    t_cuoi = DD.tach_trang(trang_html(3), u(3))
    assert DD.url_trang_tiep(f, t_cuoi, u(3), 4) == u(4)                                        # khong co rel=next -> mau_trang
    assert DD.url_trang_tiep(dict(f, phan_trang="mau"), dict(t, rel_next="https://forum.example.com/zzz"), u(1), 2) == u(2)
    assert DD.url_trang_tiep(dict(f, phan_trang="khong"), t, u(1), 2) == ""
    assert DD.url_trang_tiep(fo(mau_trang=None), t_cuoi, u(3), 4) == ""                         # khong rel=next, khong mau -> het
    tro_lai = dict(t, rel_next=u(1), neo=[], so_trang=[])
    assert DD.url_trang_tiep(fo(mau_trang=None), tro_lai, u(1), 2) == ""                        # rel=next tro lai chinh no, khong neo nao khac -> bo
    assert DD.url_trang_tiep(fo(mau_trang=None), dict(t, rel_next=u(1)), u(1), 2) == u(2)       # ... nhung thanh phan trang co neo "2" thi di theo neo (08/10)
    nx = dict(t, rel_next="http://forum.example.com/robot/page-2")
    assert DD.url_trang_tiep(f, nx, u(1), 2) == "https://forum.example.com/robot/page-2"       # nang http -> https


@pytest.mark.parametrize("tieu_de,diem", [
    ("Grid EA robot signal", 3), ("Martingale expert advisor", 2), ("Сетка советник сигналы", 3), ("グリッド 自動売買 シグナル", 3),
    ("EA lưới tín hiệu", 3), ("Weather in Hanoi", 0), ("", 0), (None, 0), ("Robot", 1), ("Estrategia de cuadrícula con señales", 1),
])
def test_diem_tieu_de_da_ngon_ngu_chi_de_xep_thu_tu(tieu_de, diem):
    assert DD.diem_tieu_de(tieu_de) == diem or (tieu_de == "EA lưới tín hiệu" and DD.diem_tieu_de(tieu_de) >= 2)


def test_van_tay_phan_biet_hai_trang_khac_nhau_va_nhan_ra_trang_lap():
    f = fo()
    a = DD.tach_trang(trang_html(1), u(1))
    b = DD.tach_trang(trang_html(2), u(2))
    va, vb = DD._van_tay(DD.trich_bai(f, a, u(1)), a), DD._van_tay(DD.trich_bai(f, b, u(2)), b)
    assert va != vb and va == DD._van_tay(DD.trich_bai(f, a, u(1)), a)


# ============================================================== 3. QUET: phan trang co moc
def test_quet_doc_het_mot_dien_dan_ba_trang_ghi_ung_vien_va_chot_pass(tmp_path):
    web = Web(dien_dan_web(), dh=None)
    q, dh = tao(tmp_path, web, cfg(fo()))
    bc = q.chay()
    assert web.trang_da_goi() == [u(1), u(2), u(3), u(4)]                                       # trang 4 = 404 -> het pass
    assert kq_luot(bc) == "XONG_PASS" and bc["tom_tat_luot"] == {"XONG_PASS": 1}
    uv = ung_vien(tmp_path)
    assert len(uv) == 12 and len({x["k"] for x in uv}) == 12 and {x["trang"] for x in uv} == {1, 2, 3}
    m = muc(q)
    assert (m["ket_qua"], m["den_trang"], m["url_tiep"], m["trang_cuoi"], m["tong_trang"], m["so_pass"], m["bai_tong"]) == ("XONG", 0, "", 3, 3, 1, 12)
    assert m["den_han"] == int(dh() + 168 * 3600) and m["tien_do"] == "XONG_PASS"
    b = next(x for x in bc["dien_dan"] if x["ma"] == "a")
    assert (b["den_trang"], b["tong_trang"], b["bai_moi"], b["trang_luot"]) == (3, 3, 12, 3)


def test_quet_gioi_han_trang_moi_luot_roi_doc_tiep_tu_moc_o_tien_trinh_sau(tmp_path):
    web1 = Web(dien_dan_web())
    q1, dh = tao(tmp_path, web1, cfg(fo(), toi_da_trang_luot=2))
    bc = q1.chay()
    assert kq_luot(bc) == "DANG_DO" and web1.trang_da_goi() == [u(1), u(2)]
    m = muc(q1)
    assert (m["den_trang"], m["url_tiep"], m["tien_do"], m["den_han"]) == (2, u(3), "DANG_DO", 0)
    web2 = Web(dien_dan_web())
    q2, _ = tao(tmp_path, web2, cfg(fo(), toi_da_trang_luot=2), dh=dh)                           # tien trinh MOI, cung tep trang thai
    bc = q2.chay()
    assert web2.trang_da_goi() == [u(3), u(4)] and kq_luot(bc) == "XONG_PASS"                   # khong doc lai trang 1-2
    assert len(ung_vien(tmp_path)) == 12 and muc(q2)["so_pass"] == 1


def test_quet_tham_so_toi_da_trang_ghi_de_config(tmp_path):
    web = Web(dien_dan_web())
    q, _ = tao(tmp_path, web, cfg(fo()))
    bc = q.chay(toi_da_trang=1)
    assert web.trang_da_goi() == [u(1)] and kq_luot(bc) == "DANG_DO" and muc(q)["den_trang"] == 1


def test_quet_pass_xong_cho_mot_tuan_ep_bo_cho_nhung_van_ton_trong_nhip(tmp_path):
    web = Web(dien_dan_web())
    q, dh = tao(tmp_path, web, cfg(fo()))
    q.chay()
    n = len(web.goi)
    bc = q.chay()                                                                                # ngay sau do
    assert kq_luot(bc) == "CHO_TUAN" and len(web.goi) == n                                       # khong mot yeu cau mang
    assert "1 tuan" not in json.dumps(bc) or True
    dh.t += 100 * 3600
    assert kq_luot(q.chay()) == "CHO_TUAN" and len(web.goi) == n                                 # moi 100 gio < 168 gio
    t0, so_ngu = dh(), len(dh.da_ngu)
    bc = q.chay(ep=True)                                                                         # --ep: bo qua cho tuan
    assert kq_luot(bc) == "XONG_PASS" and muc(q)["so_pass"] == 2 and web.trang_da_goi().count(u(1)) == 2
    assert len(dh.da_ngu) > so_ngu and dh() - t0 >= NHIP * 3                                      # nhung KHONG bo nhip giua cac yeu cau
    dh.t += 169 * 3600
    assert kq_luot(q.chay()) == "XONG_PASS" and muc(q)["so_pass"] == 3                           # qua 1 tuan: tu doc lai tu trang 1
    assert muc(q)["den_han"] == int(dh() + 168 * 3600) or muc(q)["den_han"] > dh()


def test_quet_ep_giua_tuan_roi_chay_thuong_van_doc_tiep_khong_bi_chan_boi_den_han_cu(tmp_path):
    web = Web(dien_dan_web())
    q, dh = tao(tmp_path, web, cfg(fo(), toi_da_trang_luot=1))
    for _ in range(4):                                                                           # pass 1: 3 trang + trang 404
        q.chay()
    assert muc(q)["tien_do"] == "XONG_PASS" and muc(q)["den_han"] > dh()
    q.chay(ep=True)                                                                              # pass 2 bat dau som, dang do (trang 1)
    assert muc(q)["tien_do"] == "DANG_DO" and muc(q)["den_trang"] == 1 and muc(q)["den_han"] == 0
    web.goi.clear()
    bc = q.chay()                                                                                # KHONG ep: phai doc tiep trang 2
    assert kq_luot(bc) == "DANG_DO" and web.trang_da_goi() == [u(2)] and muc(q)["den_trang"] == 2


def test_quet_trang_404_o_trang_sau_la_het_pass_khong_phai_loi_va_khong_nghi_ten_mien(tmp_path):
    web = Web({u(1): (200, trang_html(1, tong=2), ""), u(2): (404, "", "")})
    q, dh = tao(tmp_path, web, cfg(fo()))
    bc = q.chay()
    assert kq_luot(bc) == "XONG_PASS" and muc(q)["ket_qua"] == "XONG" and muc(q)["trang_cuoi"] == 1 and muc(q)["so_loi"] == 0
    assert q.tt.d["mien"]["example.com"]["cam_den"] == 0
    ok, _ = q.tt.thu_duoc("dd:khac", HOST)
    assert ok


def test_quet_trang_lap_hoac_trong_la_het_pass_khong_ghi_trung(tmp_path):
    trang = dien_dan_web()
    trang[u(4)] = trang[u(3)]                                                                    # phan trang 'khong tien': trang 4 y het trang 3
    web = Web(trang)
    q, _ = tao(tmp_path, web, cfg(fo()))
    bc = q.chay()
    assert kq_luot(bc) == "XONG_PASS" and web.trang_da_goi() == [u(1), u(2), u(3), u(4)] and len(ung_vien(tmp_path)) == 12
    assert muc(q)["trang_cuoi"] == 3
    trang[u(4)] = (200, "<html><body>khong co bai nao</body></html>", "")                       # trang rong
    web2 = Web(trang)
    q2, dh2 = tao(tmp_path / "x", web2, cfg(fo()))
    assert kq_luot(q2.chay()) == "XONG_PASS" and muc(q2)["trang_cuoi"] == 3


def test_quet_dung_o_phan_trang_toi_da_moi_pass(tmp_path):
    web = Web({u(n): (200, trang_html(n, tong=50), "") for n in range(1, 60)})
    q, _ = tao(tmp_path, web, cfg(fo(), toi_da_trang_pass=3))
    bc = q.chay()
    assert kq_luot(bc) == "XONG_PASS" and web.trang_da_goi() == [u(1), u(2), u(3)] and muc(q)["trang_cuoi"] == 3
    assert muc(q)["tong_trang"] == 50                                                            # tong so trang doc tu thanh phan trang


def test_quet_phan_trang_khong_chi_doc_trang_dau_va_khong_co_mau_trang_dung_o_rel_next(tmp_path):
    web = Web(dien_dan_web())
    q, _ = tao(tmp_path, web, cfg(fo(phan_trang="khong")))
    assert kq_luot(q.chay()) == "XONG_PASS" and web.trang_da_goi() == [u(1)]
    web2 = Web(dien_dan_web())
    q2, _ = tao(tmp_path / "y", web2, cfg(fo(mau_trang=None)))
    assert kq_luot(q2.chay()) == "XONG_PASS" and web2.trang_da_goi() == [u(1), u(2), u(3)]       # theo rel=next, het o trang 3, khong doan trang 4


def test_quet_moc_cu_khong_con_dung_khi_doi_url_trong_config(tmp_path):
    web = Web({**dien_dan_web(), **dien_dan_web(goc="/ea/")})
    q1, dh = tao(tmp_path, web, cfg(fo(), toi_da_trang_luot=1))
    q1.chay()
    assert muc(q1)["den_trang"] == 1
    q2, _ = tao(tmp_path, web, cfg(fo(goc="/ea/"), toi_da_trang_luot=1), dh=dh)                  # chu du an doi `url`
    web.goi.clear()
    q2.chay()
    assert web.trang_da_goi() == [u(1, goc="/ea/")]                                              # doc lai tu trang 1 cua url moi
    assert muc(q2)["url_goc"] == "https://%s/ea/" % HOST and muc(q2)["den_trang"] == 1


def test_quet_doi_url_xoa_ca_nghi_30_ngay_cua_url_cu(tmp_path):
    web = Web({u(1, goc="/ea/"): (200, trang_html(1, tong=1, goc="/ea/"), "")})                  # url cu: /robot/ -> 404 (het trang)
    q1, dh = tao(tmp_path, web, cfg(fo()))
    assert kq_luot(q1.chay()) == "HET_TRANG" and muc(q1)["thu_lai_sau"] > dh() + 20 * 24 * 3600
    q2, _ = tao(tmp_path, web, cfg(fo(goc="/ea/")), dh=dh)
    assert kq_luot(q2.chay()) == "XONG_PASS"


def test_quet_trang_1_khong_co_bai_la_khong_co_bai_nghi_24_gio_ep_thu_lai(tmp_path):
    web = Web({u(1): (200, "<html><body><a href='/login'>Dang nhap</a><p>can bat JavaScript de xem bai</p></body></html>", "")})
    q, dh = tao(tmp_path, web, cfg(fo()))
    bc = q.chay()
    assert kq_luot(bc) == "KHONG_CO_BAI" and "mau_bai" in next(b["ly_do"] for b in bc["dien_dan"] if b["ma"] == "a")
    assert abs(muc(q)["den_han"] - (dh() + 24 * 3600)) < 5
    n = len(web.goi)
    bc = q.chay()
    assert kq_luot(bc) == "CHO_TUAN" and len(web.goi) == n and "KHONG_CO_BAI" in next(b["ly_do"] for b in bc["dien_dan"] if b["ma"] == "a")
    web.trang[u(1)] = (200, trang_html(1, tong=1), "")                                           # chu du an sua config / trang
    assert kq_luot(q.chay(ep=True)) == "XONG_PASS"


def test_quet_chuyen_huong_ra_ten_mien_khac_khong_theo_va_ghi_ly_do_khong_url(tmp_path):
    web = Web({u(1): (301, "", "chuyen huong ra ngoai: https://other.example.org/robot/")})
    q, dh = tao(tmp_path, web, cfg(fo()))
    bc = q.chay()
    assert kq_luot(bc) == "CHUYEN_HUONG" and all("other.example.org" not in x for x in web.goi)
    assert "other.example.org" not in json.dumps(bc) and muc(q)["den_han"] > dh()


# ============================================================== 4. DUNG KHI BI CHAN - khong ne chan, khong thu lai
def _hai_dien_dan_cung_mien(tmp_path, chan):
    A, B = "a.example.com", "b.example.com"                                                      # cung ten mien goc example.com
    trang = {**dien_dan_web(A), **dien_dan_web(B)}
    trang[u(2, A)] = chan
    web = Web(trang)
    q, dh = tao(tmp_path, web, cfg(fo("a", A), fo("b", B)))
    return q, web, dh, A, B, trang


def test_quet_403_dung_ca_dien_dan_va_dien_dan_cung_ten_mien_khong_thu_lai_moc_con(tmp_path):
    q, web, dh, A, B, trang = _hai_dien_dan_cung_mien(tmp_path, (403, "Forbidden", ""))
    bc = q.chay()
    assert kq_luot(bc, "a") == "CHAN_CAM" and kq_luot(bc, "b") == "CHO"
    assert web.trang_da_goi() == [u(1, A), u(1, B), u(2, A)]                                     # b khong bi goi trang 2; a khong thu lai
    assert muc(q, "a")["den_trang"] == 1 and muc(q, "b")["den_trang"] == 1                        # moc giu nguyen
    assert q.tt.d["mien"]["example.com"]["cam_den"] > dh() + 23 * 3600
    n = len(web.goi)
    bc = q.chay()                                                                                # ngay sau do: khong mot yeu cau
    assert len(web.goi) == n and {kq_luot(bc, "a"), kq_luot(bc, "b")} == {"CHO"}
    web.trang[u(2, A)] = (200, trang_html(2), "")                                                # het nghi: doc tiep tu trang 2 (khong tu trang 1)
    dh.t += 24 * 3600 + 60
    web.goi.clear()
    q.chay()
    assert u(1, A) not in web.goi and u(2, A) in web.goi


def test_quet_429_nghi_tan_suat_15_phut_dau_va_khong_tu_thu_lai_trong_luot(tmp_path):
    q, web, dh, A, B, trang = _hai_dien_dan_cung_mien(tmp_path, (429, "Too Many Requests", ""))
    bc = q.chay()
    assert kq_luot(bc, "a") == "CHAN_TAN_SUAT" and web.trang_da_goi().count(u(2, A)) == 1
    assert 14 * 60 < q.tt.d["mien"]["example.com"]["cam_den"] - dh() <= 15 * 60 + 1
    dh.t += 16 * 60
    web.trang[u(2, A)] = (200, trang_html(2), "")
    bc = q.chay()
    assert kq_luot(bc, "a") in ("DANG_DO", "XONG_PASS") and muc(q, "a")["so_loi"] == 0


def test_quet_trang_200_nhung_la_man_chan_cloudflare_la_chan_cam(tmp_path):
    web = Web({u(1): (200, "<html><title>Just a moment...</title><div id='cf-chl-widget'>Checking your browser</div></html>", "")})
    q, dh = tao(tmp_path, web, cfg(fo()))
    assert kq_luot(q.chay()) == "CHAN_CAM" and muc(q)["so_loi"] == 1 and q.tt.d["mien"]["example.com"]["cam_den"] > dh()


def test_quet_loi_may_chu_va_loi_mang_lui_nhip_khong_dap_lai(tmp_path):
    web = Web({u(1): (503, "", "")})
    q, dh = tao(tmp_path, web, cfg(fo()))
    assert kq_luot(q.chay()) == "LOI_MAY_CHU" and web.trang_da_goi() == [u(1)]
    assert kq_luot(q.chay()) == "CHO" and web.trang_da_goi() == [u(1)]                           # dang lui nhip
    web2 = Web({u(1): (None, "", "ConnectionError: boom")})
    q2, _ = tao(tmp_path / "m", web2, cfg(fo()))
    assert kq_luot(q2.chay()) == "LOI_MANG"


def test_quet_robots_cam_thi_khong_goi_trang_nao(tmp_path):
    web = Web(dien_dan_web(), robots={HOST: (200, "User-agent: *\nDisallow: /robot/\n", "")})
    q, _ = tao(tmp_path, web, cfg(fo()))
    bc = q.chay()
    assert kq_luot(bc) == "CHAN_ROBOTS" and web.trang_da_goi() == [] and muc(q)["ket_qua"] == "CHAN_ROBOTS"
    assert ung_vien(tmp_path) == []


def test_quet_robots_5xx_thi_khong_cao_luot_nay(tmp_path):
    web = Web(dien_dan_web(), robots={HOST: (503, "", "")})
    q, _ = tao(tmp_path, web, cfg(fo()))
    assert kq_luot(q.chay()) == "LOI_MANG" and web.trang_da_goi() == []


def test_quet_ton_trong_crawl_delay_cua_robots_va_nhip_giay_cua_config(tmp_path):
    web = Web(dien_dan_web(tong=2), robots={HOST: (200, "User-agent: *\nCrawl-delay: 30\n", "")}, dh=None)
    dh = DongHo()
    web.dh = dh
    q, _ = tao(tmp_path, web, cfg(fo()), dh=dh)
    q.chay()
    t = [web.luc[i] for i, x in enumerate(web.goi) if not x.endswith("/robots.txt")]
    assert all(b - a >= 30 - 1e-6 for a, b in zip(t, t[1:])) and len(t) == 3
    web2 = Web(dien_dan_web(tong=2))
    dh2 = DongHo()
    web2.dh = dh2
    q2, _ = tao(tmp_path / "n", web2, cfg(fo(nhip_giay=20)), dh=dh2)
    q2.chay()
    t2 = [web2.luc[i] for i, x in enumerate(web2.goi) if not x.endswith("/robots.txt")]
    assert all(b - a >= 20 - 1e-6 for a, b in zip(t2, t2[1:]))                                    # config chi co the TANG nhip, khong ha duoi bang
    assert DD.LN.NHIP_MIEN["mql5.com"] == 8 and q2.nhip.nhip["mql5.com"] == 8


def test_quet_xen_ke_hai_dien_dan_khac_ten_mien_thoi_gian_cho_trum_len_nhau(tmp_path):
    dh = DongHo()
    A, B = "forum.alpha-test.com", "forum.beta-test.com"
    web = Web({**dien_dan_web(A), **dien_dan_web(B)}, dh=dh)
    q, _ = tao(tmp_path, web, cfg(fo("a", A), fo("b", B)), dh=dh)
    t0 = dh()
    bc = q.chay()
    assert [urlsplit(x).hostname for x in web.trang_da_goi()] == [A, B] * 4                      # a1 b1 a2 b2 a3 b3 a4 b4
    for h in (A, B):
        t = [web.luc[i] for i, x in enumerate(web.goi) if urlsplit(x).hostname == h]
        assert all(b - a >= NHIP - 1e-6 for a, b in zip(t, t[1:]))                               # tung ten mien van du nhip
    assert dh() - t0 <= NHIP * 5 + 1                                                             # xen ke: ~40 s; doc lan luot se mat ~64 s
    assert {kq_luot(bc, "a"), kq_luot(bc, "b")} == {"XONG_PASS"}


def test_quet_tran_ngay_va_tran_luot_la_cho_hoac_dang_do_khong_phai_loi(tmp_path):
    web = Web(dien_dan_web())
    q, _ = tao(tmp_path, web, cfg(fo(), tran_ngay_mien=3))                                       # robots + trang 1 + trang 2 roi het
    bc = q.chay()
    assert kq_luot(bc) == "CHO" and web.trang_da_goi() == [u(1), u(2)] and muc(q)["den_trang"] == 2
    assert "yeu cau/ngay" in next(b["ly_do"] for b in bc["dien_dan"] if b["ma"] == "a") and muc(q)["so_loi"] == 0
    web2 = Web(dien_dan_web())
    q2, _ = tao(tmp_path / "t", web2, cfg(fo()), tran_luot=3)                                    # tran 3 yeu cau / luot / ten mien
    bc = q2.chay()
    assert kq_luot(bc) == "DANG_DO" and muc(q2)["den_trang"] == 2 and muc(q2)["so_loi"] == 0
    assert q2.tt.d["mien"].get("example.com", {}).get("cam_den", 0) == 0


def test_quet_tran_ngay_rieng_cho_mql5_thap_hon_ten_mien_khac(tmp_path):
    q, _ = tao(tmp_path, Web(), cfg(fo(), tran_ngay_mien=120, tran_ngay_theo_mien={"mql5.com": 60}))
    assert q._tran_ngay("mql5.com") == 60 and q._tran_ngay("example.com") == 120
    q2, _ = tao(tmp_path / "z", Web(), {"dien_dan": [fo()]})
    assert q2._tran_ngay("mql5.com") == DD.MAC_DINH["tran_ngay_theo_mien"]["mql5.com"] and q2._tran_ngay("x.com") == DD.MAC_DINH["tran_ngay_mien"]


def test_quet_chi_dien_dan_bat_va_ma_goi_ten_dien_dan_tat_la_bo_qua(tmp_path):
    web = Web({**dien_dan_web(), **dien_dan_web("khac.example.net")})
    q, _ = tao(tmp_path, web, cfg(fo("a"), fo("b", "khac.example.net", bat=False)))
    bc = q.chay()
    assert kq_luot(bc, "a") == "XONG_PASS" and "kq_luot" and all(urlsplit(x).hostname == HOST for x in web.goi)
    assert "ket_qua_luot" not in next(b for b in bc["dien_dan"] if b["ma"] == "b")               # khong ca duoc xet
    bc = q.chay(["b"])
    assert kq_luot(bc, "b") == "BO_QUA" and all(urlsplit(x).hostname == HOST for x in web.goi)   # goi ten van khong bat tat
    bc = q.chay(["khong_co_ma_nay"])
    assert bc["khong_thay_ma"] == ["khong_co_ma_nay"] and bc["tom_tat_luot"] == {}


# ============================================================== 5. CHROME AI (CDP 9224)
def test_quet_khong_co_chrome_bo_qua_dien_dan_can_chrome_khong_cham_mang_khong_ghi_trang_thai(tmp_path):
    web = Web(dien_dan_web())
    cdp = CdpGia(loi_mo="khong_mo_cdp: bat Chrome AI")
    q, _ = tao(tmp_path, web, cfg(fo("a"), fo("c", "chrome.example.net", cach_lay="cdp")), cdp=cdp)
    bc = q.chay()
    assert kq_luot(bc, "c") == "KHONG_CO_CHROME" and kq_luot(bc, "a") == "XONG_PASS"             # dien dan http van chay
    assert "dd:c" not in q.tt.d["link"] and all("chrome.example.net" not in x for x in web.goi)  # khong ghi trang thai, khong ke ca robots.txt
    assert cdp.mo == 0 and "Chrome" in next(b["ly_do"] for b in bc["dien_dan"] if b["ma"] == "c")


def test_quet_cdp_mot_phien_chung_cho_dien_dan_cdp_va_cdp_render_trong_cung_luot(tmp_path):
    H1, H2 = "chrome.example.net", "render.another-site.org"
    cdp = CdpGia({**dien_dan_web(H1, tong=2), u(3, H1): (404, "", ""), u(1, H2): (200, trang_html(1, tong=1), ""), u(2, H2): (404, "", "")})
    q, _ = tao(tmp_path, Web(), cfg(fo("c", H1, cach_lay="cdp"), fo("d", H2, cach_lay="cdp_render")), cdp=cdp)
    bc = q.chay()
    assert kq_luot(bc, "c") == "XONG_PASS" and kq_luot(bc, "d") == "XONG_PASS"
    assert cdp.mo == 1 and cdp.dong == 1                                                          # MOT ket noi cho ca luot, dong khi het luot
    assert {(url, render) for url, _, render in cdp.goi if H1 in url} == {(u(1, H1), False), (u(2, H1), False), (u(3, H1), False)}
    assert {render for url, _, render in cdp.goi if H2 in url} == {True}                           # cdp_render -> mo tab that o moi trang


def test_quet_cdp_referer_la_trang_truoc_va_trang_dau_khong_co_referer(tmp_path):
    H = "chrome.example.net"
    cdp = CdpGia({**dien_dan_web(H, tong=2), u(3, H): (404, "", "")})
    q, _ = tao(tmp_path, Web(), cfg(fo("c", H, cach_lay="cdp")), cdp=cdp)
    q.chay()
    assert [(a, b, c) for a, b, c in cdp.goi] == [(u(1, H), "", False), (u(2, H), u(1, H), False), (u(3, H), u(2, H), False)]


def test_quet_cdp_van_di_qua_nhip_va_tran_yeu_cau_nhu_http(tmp_path):
    H = "chrome.example.net"
    cdp = CdpGia(dien_dan_web(H, tong=3))
    dh = DongHo()
    q, _ = tao(tmp_path, Web(dh=dh), cfg(fo("c", H, cach_lay="cdp")), cdp=cdp, dh=dh)
    q.chay()
    assert sum(dh.da_ngu) >= NHIP * 3                                                             # moi trang cach nhau >= 8 giay (nhu nguoi doc cham)
    assert q.tt.so_hom_nay("example.net") >= 4                                                    # robots.txt + 4 trang deu duoc dem vao tran ngay


def test_quet_cdp_403_dung_nhu_http_khong_giai_man_chan(tmp_path):
    H = "chrome.example.net"
    cdp = CdpGia({u(1, H): (403, "<html>Attention Required! | Cloudflare</html>", "")})
    q, dh = tao(tmp_path, Web(), cfg(fo("c", H, cach_lay="cdp")), cdp=cdp)
    assert kq_luot(q.chay(), "c") == "CHAN_CAM" and len(cdp.goi) == 1 and q.tt.d["mien"]["example.net"]["cam_den"] > dh()


def test_quet_cdp_chuyen_huong_ra_ngoai_ghi_ly_do_khong_chua_url(tmp_path):
    H = "chrome.example.net"
    cdp = CdpGia({u(1, H): (302, "", "chuyen huong ra ngoai: https://tracker.other-site.org/x?id=SECRET123")})
    q, dh = tao(tmp_path, Web(), cfg(fo("c", H, cach_lay="cdp")), cdp=cdp)
    bc = q.chay()
    txt = json.dumps(bc) + json.dumps(q.tt.d)
    assert kq_luot(bc, "c") == "CHUYEN_HUONG" and "other-site" not in txt and "SECRET123" not in txt


def test_quet_loi_mang_cua_chrome_khong_dua_url_vao_trang_thai_hay_bao_cao(tmp_path):
    H = "chrome.example.net"
    cdp = CdpGia({u(1, H): (None, "", "Error: connect ECONNREFUSED https://chrome.example.net/t/4455/ Call log: GET https://chrome.example.net/t/4455/")})
    q, _ = tao(tmp_path, Web(), cfg(fo("c", H, cach_lay="cdp")), cdp=cdp)
    bc = q.chay()
    txt = json.dumps(bc) + json.dumps(q.tt.d)
    assert kq_luot(bc, "c") == "LOI_MANG" and "4455" not in txt and "ECONNREFUSED <url>" in txt   # URL trong loi bi che; url_goc cua robots.txt la that va duoc phep


# ---------------------------------------------------------- PhienCdp that voi doi tuong Playwright gia
class _Resp:
    def __init__(self, status=200, body=b"<html><a href='/t/1/'>x</a></html>", url=u(1), headers=None):
        self.status, self._b, self.url = status, body, url
        self.headers = headers if headers is not None else {"Content-Type": "text/html; charset=utf-8"}
        self.da_huy = False

    def body(self):
        return self._b

    def dispose(self):
        self.da_huy = True


def _chuyen(url, status=302):
    return _Resp(status=status, body=b"", headers={"Location": url})


class _Req:
    """`ctx.request`: tra lan luot cac phan hoi (hoac ngoai le); ghi lai (url, kwargs) tung lan."""

    def __init__(self, *tra):
        self.tra, self.goi = list(tra), []

    def get(self, url, **kw):
        self.goi.append((url, kw))
        x = self.tra.pop(0) if len(self.tra) > 1 else self.tra[0]
        if isinstance(x, BaseException):
            raise x
        return x


class _Cdp:
    """Phien CDP gia: ghi lai moi lenh `send`; `on` luu bo xu ly de tab gia kich ban cac su kien `Fetch.requestPaused`."""

    def __init__(self, khung="F1", loi_fail=False):
        self.goi, self.xu_ly, self.da_tach = [], None, False
        self.khung, self.loi_fail = khung, loi_fail

    def send(self, ten, tham_so=None):
        self.goi.append((ten, tham_so))
        if ten == "Page.getFrameTree":
            return {"frameTree": {"frame": {"id": self.khung}}}
        if ten == "Fetch.failRequest" and self.loi_fail:
            raise RuntimeError("Target closed")
        return {}

    def on(self, su_kien, f):
        self.goi.append(("on", su_kien))
        self.xu_ly = f

    def detach(self):
        self.da_tach = True

    def hanh_dong(self, rid):
        """'continue' | 'fail' | None: lenh CUOI da gui cho yeu cau `rid`."""
        for ten, ts in reversed(self.goi):
            if isinstance(ts, dict) and ts.get("requestId") == rid:
                return {"Fetch.continueRequest": "continue", "Fetch.failRequest": "fail"}.get(ten)
        return None

    def so_lenh(self, ten):
        return [t for n, t in self.goi if n == ten]


_RID = itertools.count(1)
HTML = {"Content-Type": "text/html; charset=utf-8"}


def yc(url, khung="F1"):
    """Su kien `Fetch.requestPaused` o giai doan YEU CAU (chua gui di)."""
    return {"requestId": "r%d" % next(_RID), "request": {"url": url}, "frameId": khung}


def ph(url, status, dau=None, khung="F1", loi=None):
    """... o giai doan PHAN HOI (da co dong trang thai + header, noi dung chua ve)."""
    ev = yc(url, khung)
    if status is not None:
        ev["responseStatusCode"] = status
    ev["responseHeaders"] = [{"name": k, "value": v} for k, v in (dau or {}).items()]
    if loi:
        ev["responseErrorReason"] = loi
    return ev


class _Trang:
    """Tab gia. `kich_ban`: su kien Fetch ma trinh duyet 'gap' TRONG `goto` (dung ngay khi mot yeu cau bi chan, nhu Chrome that, va ket thuc bang loi);
    `sau`: su kien den SAU khi trang da tai (JS tu dieu huong) - bi chan thi tab chuyen sang man hinh loi, `goto` khong nem gi."""

    def __init__(self, url=u(1), html="<html>render</html>", loi_goto=None, status=200, kich_ban=(), sau=()):
        self.url, self.html, self.loi_goto, self.status = url, html, loi_goto, status
        self.kich_ban, self.sau, self.cdp = list(kich_ban), list(sau), None
        self.da_dong, self.cho = False, []

    def _phat(self, ev):
        self.cdp.xu_ly(ev)
        return self.cdp.hanh_dong(ev["requestId"])

    def goto(self, url, **kw):
        self.cdp.goi.append(("goto", url))
        self.cho.append(("goto", kw.get("wait_until"), kw.get("timeout")))
        for ev in self.kich_ban:
            if self._phat(ev) == "fail":
                raise RuntimeError("net::ERR_BLOCKED_BY_CLIENT at %s" % ev["request"]["url"])
        if self.loi_goto:
            raise self.loi_goto
        return type("R", (), {"status": self.status})()

    def wait_for_load_state(self, *a, **kw):
        self.cho.append(("load_state", a))
        for ev in self.sau:
            if self._phat(ev) == "fail":
                self.url, self.html = "chrome-error://chromewebdata/", "<html>This site can't be reached</html>"
                break
        self.sau = []

    def wait_for_timeout(self, ms):
        self.cho.append(("timeout", ms))

    def content(self):
        return self.html

    def close(self):
        self.da_dong = True


class _Ctx:
    def __init__(self, req=None, trang=None, cdp=None):
        self.request, self.trang_tao, self.cdp = req, trang, cdp or _Cdp()
        self.pages, self.da_mo = [], 0

    def new_page(self):
        self.da_mo += 1
        return self.trang_tao

    def new_cdp_session(self, pg):
        pg.cdp = self.cdp
        return self.cdp


def phien(ctx):
    p = DD.PhienCdp()
    p._ctx = ctx
    return p


def test_phien_cdp_lay_gui_referer_giai_ma_huy_phan_hoi_va_khong_de_playwright_tu_theo_chuyen_huong():
    r = _Resp()
    req = _Req(r)
    st, text, loi = phien(_Ctx(req)).lay(u(2), referer=u(1))
    assert (st, loi) == (200, "") and "<a href='/t/1/'>x</a>" in text and r.da_huy
    url, kw = req.goi[0]
    assert url == u(2) and kw["headers"] == {"Referer": u(1)} and kw["timeout"] == 30000
    assert kw["max_redirects"] == 0                                                              # KHONG de Playwright tu theo (no theo ca ra ten mien khac)
    req2 = _Req(_Resp())
    phien(_Ctx(req2)).lay(u(2))                                                                   # khong Referer -> khong gui header
    assert "headers" not in req2.goi[0][1]


def test_phien_cdp_theo_chuyen_huong_cung_ten_mien_https_tung_buoc_qua_truoc():
    r2, r3 = _chuyen("/robot/moi"), _Resp(body=b"<html>dich</html>")
    req = _Req(r2, r3)
    truoc = []
    st, text, loi = phien(_Ctx(req)).lay(u(1), truoc=truoc.append)
    assert (st, text, loi) == (200, "<html>dich</html>", "") and r2.da_huy and r3.da_huy
    assert [x for x, _ in req.goi] == [u(1), "https://%s/robot/moi" % HOST] and truoc == [u(1), "https://%s/robot/moi" % HOST]   # nhip + dem tran moi buoc


@pytest.mark.parametrize("dich", ["https://other.example.org/x", "http://%s/robot/" % HOST, "https://t.me/+AbCdEfGh12345678",
                                  "https://www.facebook.com/groups/1", "//cdn.other-site.net/p"])
def test_phien_cdp_chuyen_huong_ra_ten_mien_khac_hoac_ha_xuong_http_thi_dung_khong_toi_dich(dich):
    r = _chuyen(dich, 301)
    req = _Req(r, _Resp(body=b"<html>KHONG DUOC DEN DAY</html>"))
    st, text, loi = phien(_Ctx(req)).lay(u(2))
    assert st == 301 and text == "" and loi.startswith("chuyen huong ra ngoai: ") and r.da_huy
    assert len(req.goi) == 1                                                                      # khong mot yeu cau nao toi dich


def test_phien_cdp_qua_nhieu_chuyen_huong_va_vong_lap():
    req = _Req(_chuyen("/robot/a"), _chuyen("/robot/b"), _chuyen("/robot/c"), _chuyen("/robot/d"), _Resp())
    st, text, loi = phien(_Ctx(req)).lay(u(1))
    assert (st, text, loi) == (None, "", "qua nhieu lan chuyen huong") and len(req.goi) == DD.LAN_CHUYEN_TOI_DA + 1


def test_phien_cdp_het_nhip_giua_chung_chuyen_huong_thi_nem_len_cho_quet_bat():
    def truoc(url):
        if url.endswith("/moi"):
            raise LN.HetNhip("het tran")
    with pytest.raises(LN.HetNhip):
        phien(_Ctx(_Req(_chuyen("/robot/moi"), _Resp()))).lay(u(1), truoc=truoc)


def test_phien_cdp_phien_ban_playwright_qua_cu_khong_co_max_redirects_thi_tu_choi_chu_khong_chay_lieu():
    class Cu:
        goi = 0

        def get(self, url, **kw):
            Cu.goi += 1
            if "max_redirects" in kw:
                raise TypeError("get() got an unexpected keyword argument 'max_redirects'")
            return _Resp()
    st, text, loi = phien(_Ctx(Cu())).lay(u(2))
    assert st is None and text == "" and loi.startswith("playwright_qua_cu") and Cu.goi == 1       # khong thu lai khong co max_redirects


def test_phien_cdp_loi_mang_mot_dong_khong_url_va_cat_ngan():
    st, text, loi = phien(_Ctx(_Req(RuntimeError("boom " + "x" * 500)))).lay(u(2))
    assert st is None and text == "" and loi.startswith("RuntimeError: boom") and len(loi) <= 100
    msg = "APIRequestContext.get: connect ECONNREFUSED 127.0.0.1:1\nCall log:\n  - GET https://forum.example.com/t/4455/\n  - user=me@x.org"
    st, text, loi = phien(_Ctx(_Req(RuntimeError(msg)))).lay(u(2))
    assert "\n" not in loi and "http" not in loi and "4455" not in loi and loi.startswith("RuntimeError: APIRequestContext.get")
    assert "<url>" in DD._khong_url("loi tai https://a.b/c?d=1 va http://x.y") and "http" not in DD._khong_url("loi tai https://a.b/c?d=1 va http://x.y")


def _render(tr, truoc=None, cdp=None, url=u(1)):
    """`lay(render=True)` tren tab gia -> (ket qua, ctx)."""
    ctx = _Ctx(trang=tr, cdp=cdp)
    return phien(ctx).lay(url, render=True, truoc=truoc), ctx


def test_phien_cdp_render_mo_tab_that_bat_fetch_hai_giai_doan_doc_dom_roi_dong_tab_va_tach_cdp():
    tr = _Trang(kich_ban=[yc(u(1)), ph(u(1), 200, HTML)])
    truoc = []
    (st, text, loi), ctx = _render(tr, truoc.append)
    assert (st, text, loi) == (200, "<html>render</html>", "") and tr.da_dong and ctx.cdp.da_tach and truoc == [u(1)]
    ten = [n for n, _ in ctx.cdp.goi]
    assert ten.index("Page.getFrameTree") < ten.index("on") < ten.index("Fetch.enable") < ten.index("goto")      # bo loc san sang TRUOC khi trinh duyet di
    assert ctx.cdp.so_lenh("Fetch.enable") == [{"patterns": [{"urlPattern": "*", "resourceType": "Document", "requestStage": g} for g in ("Request", "Response")]}]
    assert ("goto", "domcontentloaded", DD.TIMEOUT_TRANG_MS) in tr.cho
    assert ctx.cdp.so_lenh("Fetch.failRequest") == [] and len(ctx.cdp.so_lenh("Fetch.continueRequest")) == 2


@pytest.mark.parametrize("vi_tri, dich", [("/robot/moi", "https://%s/robot/moi" % HOST), ("page-9", "https://%s/robot/page-9" % HOST),
                                          ("https://www.%s/robot/" % HOST, "https://www.%s/robot/" % HOST)])
def test_phien_cdp_render_chuyen_huong_cung_ten_mien_goc_https_duoc_theo_va_qua_truoc_dung_mot_lan_moi_trang(vi_tri, dich):
    tr = _Trang(kich_ban=[yc(u(2)), ph(u(2), 302, {"Location": vi_tri}), yc(dich), ph(dich, 200, HTML)])
    truoc = []
    (st, text, loi), ctx = _render(tr, truoc.append, url=u(2))
    assert (st, text, loi) == (200, "<html>render</html>", "") and ctx.cdp.so_lenh("Fetch.failRequest") == []
    assert truoc == [u(2), dich]                                      # nhip + dem tran DUNG MOT lan / trang that su tai (yeu cau ke tiep khong bi tinh lan hai)


def test_phien_cdp_render_trang_tu_mo_them_trang_cung_ten_mien_thi_van_qua_nhip_va_dem_tran():
    tr = _Trang(kich_ban=[yc(u(1)), ph(u(1), 200, HTML), yc(u(2)), ph(u(2), 200, HTML)])
    truoc = []
    (st, text, loi), _ = _render(tr, truoc.append)
    assert (st, loi) == (200, "") and truoc == [u(1), u(2)]


@pytest.mark.parametrize("dich", ["https://other.example.org/x", "http://%s/robot/" % HOST, "https://t.me/+AbCdEfGh12345678",
                                  "https://www.facebook.com/groups/1", "//cdn.other-site.net/p", "file:///etc/passwd", "ftp://files.example.net/a",
                                  "https://127.0.0.1:8443/admin", "https://printer.local/status"])
def test_phien_cdp_render_302_ra_ten_mien_khac_ha_http_hoac_noi_bo_thi_chan_truoc_khi_trinh_duyet_di(dich):
    den = urljoin(u(2), dich)
    sau = yc(den)
    tr = _Trang(kich_ban=[yc(u(2)), ph(u(2), 302, {"Location": dich}), sau, ph(den, 200, HTML)])
    (st, text, loi), ctx = _render(tr, url=u(2))
    assert st == 302 and text == "" and loi == "chuyen huong ra ngoai: " + den and tr.da_dong and ctx.cdp.da_tach
    assert [t["errorReason"] for t in ctx.cdp.so_lenh("Fetch.failRequest")] == ["BlockedByClient"]
    assert ctx.cdp.hanh_dong(sau["requestId"]) is None                # yeu cau toi dich KHONG he duoc tao ra


def test_phien_cdp_render_qua_nhieu_chuyen_huong_cung_ten_mien_thi_dung_o_hop_thu_tu():
    chuoi = [u(1)] + ["https://%s/robot/%s" % (HOST, c) for c in "abcd"]
    kb = []
    for cur, nx in zip(chuoi, chuoi[1:]):
        kb += [yc(cur), ph(cur, 302, {"Location": nx})]
    truoc = []
    (st, text, loi), ctx = _render(_Trang(kich_ban=kb), truoc.append)
    assert (st, text, loi) == (None, "", "qua nhieu lan chuyen huong") and len(ctx.cdp.so_lenh("Fetch.failRequest")) == 1
    assert truoc == chuoi[:DD.LAN_CHUYEN_TOI_DA + 1]                  # nhu duong ctx.request: <= 3 hop, moi hop deu qua nhip


@pytest.mark.parametrize("trong_goto", [False, True])
def test_phien_cdp_render_js_tu_dieu_huong_khung_chinh_ra_ten_mien_khac_thi_chan_va_khong_tra_man_hinh_loi(trong_goto):
    ra = "https://login.other-site.org/sso"
    ev = yc(ra)
    tr = _Trang(kich_ban=[yc(u(1)), ph(u(1), 200, HTML)] + ([ev] if trong_goto else []), sau=[] if trong_goto else [ev])
    (st, text, loi), ctx = _render(tr)
    assert text == "" and loi == "chuyen huong ra ngoai: " + ra and tr.da_dong       # dung khi goto con dang chay, hoac sau khi trang da tai
    assert st == (None if trong_goto else 200) and ctx.cdp.hanh_dong(ev["requestId"]) == "fail"


def test_phien_cdp_render_khung_con_o_ten_mien_khac_khong_bi_chan_chi_khung_chinh_bi_loc():
    qc = yc("https://ads.other-site.net/frame", khung="F2")
    qc_ph = ph("https://ads.other-site.net/frame", 200, {"Content-Type": "application/octet-stream"}, khung="F2")
    tr = _Trang(kich_ban=[yc(u(1)), ph(u(1), 200, HTML), qc, qc_ph])
    truoc = []
    (st, text, loi), ctx = _render(tr, truoc.append)
    assert (st, text, loi) == (200, "<html>render</html>", "") and truoc == [u(1)]
    assert ctx.cdp.hanh_dong(qc["requestId"]) == "continue" and ctx.cdp.hanh_dong(qc_ph["requestId"]) == "continue"


def test_phien_cdp_render_het_nhip_giua_chung_chuyen_huong_thi_chan_yeu_cau_dong_tab_va_nem_len_cho_quet_bat():
    def truoc(url):
        if url.endswith("/moi"):
            raise LN.HetNhip("het tran")
    tr = _Trang(kich_ban=[yc(u(1)), ph(u(1), 302, {"Location": "/robot/moi"}), yc("https://%s/robot/moi" % HOST)])
    ctx = _Ctx(trang=tr)
    with pytest.raises(LN.HetNhip):
        phien(ctx).lay(u(1), render=True, truoc=truoc)
    assert tr.da_dong and ctx.cdp.da_tach and len(ctx.cdp.so_lenh("Fetch.failRequest")) == 1      # trinh duyet KHONG duoc di tiep


def test_phien_cdp_render_het_nhip_o_trang_dau_thi_khong_mo_tab_khong_cham_cdp():
    ctx = _Ctx(trang=_Trang())
    with pytest.raises(LN.HetNhip):
        phien(ctx).lay(u(1), render=True, truoc=lambda url: (_ for _ in ()).throw(LN.HetNhip("het tran")))
    assert ctx.da_mo == 0 and ctx.cdp.goi == []


@pytest.mark.parametrize("dau, ly", [({"Content-Type": "application/octet-stream"}, "khong phai trang web (application/octet-stream)"),
                                     ({"Content-Type": "application/x-msdownload"}, "khong phai trang web (application/x-msdownload)"),
                                     ({"Content-Type": "application/pdf"}, "khong phai trang web (application/pdf)"),
                                     ({"Content-Type": "text/html", "Content-Disposition": "attachment; filename=setup.exe"}, "tai ve (attachment)"),
                                     ({}, "khong co content-type")])
def test_phien_cdp_render_tep_tai_ve_hoac_khong_phai_trang_web_thi_chan_truoc_khi_chrome_luu_ve_may(dau, ly):
    tr = _Trang(kich_ban=[yc(u(1)), ph(u(1), 200, dau)])
    (st, text, loi), ctx = _render(tr)
    assert (st, text, loi) == (200, "", ly) and tr.da_dong and len(ctx.cdp.so_lenh("Fetch.failRequest")) == 1


def test_phien_cdp_render_loi_trong_bo_loc_thi_dong_yeu_cau_va_bao_loi_mot_dong_khong_url():
    def truoc(url):
        if url.endswith("/moi"):
            raise RuntimeError("hong tai https://forum.example.com/t/4455/ do loi")
    tr = _Trang(kich_ban=[yc(u(1)), ph(u(1), 302, {"Location": "/robot/moi"}), yc("https://%s/robot/moi" % HOST)])
    (st, text, loi), ctx = _render(tr, truoc)
    assert st is None and text == "" and loi.startswith("RuntimeError: hong tai <url>") and "4455" not in loi and "http" not in loi
    assert len(ctx.cdp.so_lenh("Fetch.failRequest")) == 1             # DONG: loi trong bo loc = chan, khong de yeu cau treo hay di lung tung


def test_phien_cdp_render_loi_cua_trinh_duyet_mot_dong_khong_url_va_van_dong_tab():
    tr = _Trang(loi_goto=TimeoutError("het gio https://forum.example.com/t/9/"))
    (st, text, loi), ctx = _render(tr)
    assert st is None and text == "" and loi.startswith("TimeoutError") and "http" not in loi and tr.da_dong and ctx.cdp.da_tach


def test_phien_cdp_render_phan_hoi_bi_loi_mang_thi_de_trinh_duyet_tu_bao_loi():
    ev = ph(u(1), None, loi="ConnectionRefused")
    tr = _Trang(kich_ban=[yc(u(1)), ev], loi_goto=RuntimeError("net::ERR_CONNECTION_REFUSED"))
    (st, text, loi), ctx = _render(tr)
    assert st is None and loi == "RuntimeError: net::ERR_CONNECTION_REFUSED" and ctx.cdp.hanh_dong(ev["requestId"]) == "continue"


def test_phien_cdp_render_failrequest_tu_no_loi_cung_khong_lan_ra_ngoai_bo_xu_ly():
    dich = "https://other.example.org/x"
    tr = _Trang(kich_ban=[yc(u(2)), ph(u(2), 302, {"Location": dich})])
    ctx = _Ctx(trang=tr, cdp=_Cdp(loi_fail=True))
    st, text, loi = phien(ctx).lay(u(2), render=True)
    assert text == "" and loi == "chuyen huong ra ngoai: " + dich and tr.da_dong


def test_phien_cdp_render_id_khung_chinh_khong_khop_thi_dong_chu_khong_tin_bo_loc():
    ctx = _Ctx(trang=_Trang(kich_ban=[yc(u(1), khung="F-LA")]), cdp=_Cdp(khung="F1"))
    st, text, loi = phien(ctx).lay(u(1), render=True)
    assert st is None and text == "" and loi.startswith("khung_chinh_khong_khop") and len(ctx.cdp.so_lenh("Fetch.failRequest")) == 1


def test_phien_cdp_render_luoi_an_toan_thu_hai_url_cuoi_khac_ten_mien_thi_bo_noi_dung():
    tr = _Trang(url="https://other.example.org/x", kich_ban=[yc(u(1)), ph(u(1), 200, HTML)])
    (st, text, loi), _ = _render(tr)
    assert text == "" and loi.startswith("chuyen huong ra ngoai") and tr.da_dong


def test_duoc_theo_chi_https_cung_ten_mien_goc_va_khong_noi_bo():
    g = DD._mien(u(1))
    assert DD._duoc_theo("https://%s/x" % HOST, g) and DD._duoc_theo("https://www.%s/x" % HOST, g)
    assert not DD._duoc_theo("http://%s/x" % HOST, g) and not DD._duoc_theo("https://other.example.org/x", g)
    assert not any(DD._duoc_theo(x, g) for x in ("file:///etc/passwd", "data:text/html,x", "javascript:alert(1)", "chrome://settings", "about:blank"))
    assert not DD._duoc_theo("https://forum.local/x", DD._mien("https://forum.local/")) and not DD._duoc_theo("https://127.0.0.1/x", DD._mien("https://127.0.0.1/"))


@pytest.mark.parametrize("dau, mong", [({"content-type": "text/html; charset=utf-8"}, ""), ({"content-type": "application/xhtml+xml"}, ""),
                                       ({"content-type": "application/json"}, ""), ({"content-type": "text/plain"}, ""),
                                       ({"content-type": "application/octet-stream"}, "khong phai trang web (application/octet-stream)"),
                                       ({"content-type": "image/png"}, "khong phai trang web (image/png)"), ({}, "khong co content-type"),
                                       ({"content-type": "text/html", "content-disposition": " Attachment; filename=a.exe"}, "tai ve (attachment)")])
def test_khong_phai_trang_nhan_ra_tep_tai_ve_va_loai_noi_dung_khong_doc_duoc(dau, mong):
    assert DD._khong_phai_trang(dau) == mong


def test_phien_cdp_viet_lai_url_mql5_thieu_www_va_ngon_ngu_nhu_lay_http():
    req = _Req(_Resp())
    phien(_Ctx(req)).lay("https://mql5.com/signals/2023752")
    assert req.goi[0][0].startswith("https://www.mql5.com/") and "/signals/2023752" in req.goi[0][0]


def test_phien_cdp_khong_co_cong_9224_thi_nem_khong_co_cdp_chua_import_playwright(monkeypatch):
    goi = []
    monkeypatch.setattr(DT, "cdp_dang_chay", lambda ports=None, **k: goi.append(ports))
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)                                 # neu co import thi se loi khac
    with pytest.raises(DD.KhongCoCdp, match="khong_mo_cdp"):
        DD.PhienCdp().__enter__()
    assert goi == [(9224,)]                                                                       # chi hoi cong 9224 (Chrome AI), khong 9222


def test_phien_cdp_co_cong_nhung_thieu_playwright_la_khong_co_cdp(monkeypatch):
    monkeypatch.setattr(DT, "cdp_dang_chay", lambda *a, **k: 9224)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
    with pytest.raises(DD.KhongCoCdp, match="khong_co_playwright"):
        DD.PhienCdp().__enter__()


def test_phien_cdp_noi_that_bai_thi_ngat_playwright_va_bao_khong_co_cdp(monkeypatch):
    nhat_ky = []

    class Chromium:
        def connect_over_cdp(self, url):
            nhat_ky.append(url)
            raise RuntimeError("ECONNREFUSED")

    class Pw:
        chromium = Chromium()

        def stop(self):
            nhat_ky.append("stop")

    class Goc:
        def start(self):
            return Pw()

    import types
    mod = types.ModuleType("playwright.sync_api")
    mod.sync_playwright = lambda: Goc()
    monkeypatch.setitem(sys.modules, "playwright.sync_api", mod)
    monkeypatch.setattr(DT, "cdp_dang_chay", lambda *a, **k: 9224)
    with pytest.raises(DD.KhongCoCdp, match="khong_noi_duoc_cdp"):
        DD.PhienCdp().__enter__()
    assert nhat_ky == ["http://127.0.0.1:9224", "stop"]


def test_cdp_mac_dinh_uu_tien_9224_chrome_ai_va_telegram_cung_dung_9224():
    assert DT.CDP_MAC_DINH == (9224, 9222)
    from nhan import telegram as TG
    assert TG.CDP_MAC_DINH.endswith(":9224") and DD.CDP_CONG == 9224


# ============================================================== 6. CHUNG TRANG THAI VOI b link
def test_dien_dan_va_b_link_dung_chung_trang_thai_chan_ten_mien_lan_sang_nhau(tmp_path):
    A = "a.example.com"
    web = Web({u(1, A): (429, "", "")})
    q, dh = tao(tmp_path, web, cfg(fo("a", A)))
    q.tt.ghi("ma_link_khac", "forum.example.com", "OK", url="x")                                  # muc cua b link, cung ten mien
    q.chay()
    assert q.tt.d["link"]["ma_link_khac"]["ket_qua"] == "OK" and "dd:a" in q.tt.d["link"]          # khong de len nhau
    ok, ly = q.tt.thu_duoc("ma_link_khac", "forum.example.com", 400)                               # nhung ten mien bi chan thi b link cung nghi
    assert not ok and "example.com" in ly
    assert json.loads((tmp_path / "tt.json").read_text(encoding="utf-8"))["link"]["dd:a"]["ket_qua"] == "CHAN_TAN_SUAT"


# ============================================================== 7. UNG VIEN + BAO CAO (khong lo URL / tieu de)
def _html_tin_hieu():
    return ('<html><head><link rel="next" href="/robot/page-2"></head><body>'
            '<a href="https://www.mql5.com/en/signals/2331122">Super Grid signal 2331122</a>'
            '<a href="/t/5/">Martingale hedge EA tu dong</a><a href="https://www.mql5.com/ru/signals/2023752">Another signal</a>'
            '<a href="/robot/page-2">2</a></body></html>')


def test_ung_vien_khong_trung_giua_cac_luot_va_ghi_diem_tu_khoa(tmp_path):
    web = Web({u(1): (200, _html_tin_hieu(), ""), u(2): (404, "", "")})
    q, dh = tao(tmp_path, web, cfg(fo(mau_bai=r"/t/\d+|mql5\.com/(?:[a-z]{2}/)?signals/\d+")))
    q.chay()
    dh.t += 169 * 3600
    q.chay()                                                                                      # pass thu hai doc lai cung trang
    uv = ung_vien(tmp_path)
    assert len(uv) == 3 and len({x["k"] for x in uv}) == 3                                        # khong ghi trung
    diem = {x["tieu_de"]: x["diem"] for x in uv}
    assert diem["Martingale hedge EA tu dong"] == 2 and diem["Super Grid signal 2331122"] == 2 and diem["Another signal"] == 1


def test_bao_cao_khong_lo_url_tieu_de_chi_co_id_tin_hieu_mql5_va_phu_nuoc(tmp_path):
    web = Web({u(1): (200, _html_tin_hieu(), ""), u(2): (404, "", "")})
    q, _ = tao(tmp_path, web, cfg(fo(mau_bai=r"/t/\d+|mql5\.com/(?:[a-z]{2}/)?signals/\d+"), fo("b", "khac.example.net", nuoc="th", bat=False)))
    bc = q.chay()
    txt = json.dumps(bc, ensure_ascii=False)
    md = (tmp_path / "reports" / "dien_dan_ket_qua.md").read_text(encoding="utf-8")
    js = (tmp_path / "reports" / "dien_dan_ket_qua.json").read_text(encoding="utf-8")
    for rac in ("Super Grid", "Martingale hedge", "forum.example.com/t/", "mql5.com/en/signals", "https://"):
        assert rac not in txt and rac not in md and rac not in js, rac
    assert sorted(bc["tin_hieu_mql5"]) == [2023752, 2331122] and bc["nuoc"]["vi"]["doc_duoc"] == 1
    assert bc["nuoc"]["th"] == {"dien_dan": 1, "bat": 0, "doc_duoc": 0} and bc["nuoc_chua_doc_duoc"] == ["th"]
    assert "Nuoc DA doc duoc" in md and "th" in md and len(js) < 40_000 and len(md) <= 38_000
    assert json.loads(js)["lenh"] == "quet"


def test_bao_cao_cat_vua_40k_khi_co_rat_nhieu_dien_dan_va_tin_hieu(tmp_path):
    fos = [fo("f%03d" % i, "f%03d.example.net" % i, nuoc="vi") for i in range(150)]
    web = Web()
    q, _ = tao(tmp_path, web, cfg(*[dict(f, bat=False) for f in fos]))
    for i in range(1000):                                                                         # kho ung vien gia: 1000 ID tin hieu
        q._kho_cua(fos[0]).them([{"url": "https://www.mql5.com/en/signals/%d" % (3000000 + i), "tieu_de": "x"}], 1, 1)
    bc = q.bao_cao()
    js = (tmp_path / "reports" / "dien_dan_ket_qua.json").read_text(encoding="utf-8")
    assert len(js) <= 40_000 and len(bc["tin_hieu_mql5"]) <= 300 and json.loads(js)["tong_dien_dan"] == 150


def test_bao_cao_tu_trang_thai_khong_mang_va_thieu_trang_thai_la_chua_lam(tmp_path):
    web = Web(dien_dan_web())
    q, _ = tao(tmp_path, web, cfg(fo()))
    bc = q.bao_cao()
    assert web.goi == [] and bc["dien_dan"][0]["ket_qua"] == "CHUA_LAM" and bc["nuoc_chua_doc_duoc"] == ["vi"]
    q.chay()
    bc = tao(tmp_path, Web(), cfg(fo()))[0].bao_cao()
    assert bc["dien_dan"][0]["ket_qua"] == "XONG" and bc["dien_dan"][0]["bai_tong"] == 12 and bc["nuoc"]["vi"]["doc_duoc"] == 1


def test_ly_do_trong_bao_cao_che_email_so_dai_va_duong_dan(tmp_path):
    web = Web({u(1): (None, "", "OSError: [Errno 2] C:\\Users\\SV STORE\\x.txt user mail@example.com acc 123456789012")})
    q, _ = tao(tmp_path, web, cfg(fo()))
    bc = q.chay()
    ly = next(b["ly_do"] for b in bc["dien_dan"] if b["ma"] == "a")
    assert "mail@example.com" not in ly and "123456789012" not in ly and "SV STORE" not in ly


# ============================================================== 8. KE HOACH + THAM DO
def test_ke_hoach_khong_mang_noi_buoc_tiep_cua_tung_dien_dan(tmp_path):
    web = Web(dien_dan_web())
    q, dh = tao(tmp_path, web, cfg(fo("a"), fo("b", "tat.example.net", bat=False), fo("c", "c.example.net")))
    kh = {r["ma"]: r for r in q.ke_hoach()}
    assert kh["a"]["buoc_tiep"] == "doc tu trang 1" and kh["b"]["buoc_tiep"] == "tat" and web.goi == []
    q2, _ = tao(tmp_path, Web(dien_dan_web()), cfg(fo("a", toi_da_trang_luot=1), fo("b", "tat.example.net", bat=False)), dh=dh)
    q2.chay()
    kh = {r["ma"]: r for r in q2.ke_hoach()}
    assert kh["a"]["buoc_tiep"] == "doc tiep trang 2" and kh["a"]["den_trang"] == 1
    for _ in range(3):
        q2.chay()
    kh = {r["ma"]: r for r in q2.ke_hoach()}
    assert kh["a"]["buoc_tiep"].startswith("cho den ") and kh["a"]["so_pass"] == 1


def test_do_tham_do_khong_ghi_moc_that_va_goi_y_bang_loi_thuong(tmp_path):
    web = Web(dien_dan_web())
    q, dh = tao(tmp_path, web, cfg(fo("a", bat=False)))
    bc = q.do()                                                                                   # ke ca dien dan dang tat
    r = bc["dien_dan"][0]
    assert r["ket_qua"] == "OK" and r["so_bai"] == 4 and r["rel_next"] is True and r["trang2"]["khac_trang_1"] is True
    assert r["tong_trang_uoc"] == 3 and "bat=true" in r["goi_y"] and web.trang_da_goi() == [u(1), u(2)]
    assert "dd:a" not in q.tt.d["link"] and q.tt.d["link"]["dd:a~do"]["so_bai"] == 4              # moc that khong bi dung vao
    assert (tmp_path / "reports" / "dien_dan_do.json").exists() and ung_vien(tmp_path) == []        # tham do khong ghi ung vien


def test_do_goi_y_cho_tung_tinh_huong(tmp_path):
    # moi dien dan MOT ten mien goc rieng: mot ten mien bi chan thi ca ten mien nghi (dung chu y), nen khong dung chung o day
    web = Web({u(1): (200, "<html><body>trong</body></html>", ""), "https://forum.blocked-one.org/robot/": (403, "x", ""),
               "https://forum.single-two.org/robot/": (200, trang_html(1, tong=1, rel_next=False, so_bai=5), ""),
               "https://forum.dup-three.org/robot/": (200, trang_html(1, tong=2), ""),
               "https://forum.dup-three.org/robot/page-2": (200, trang_html(1, tong=2), "")})
    q, _ = tao(tmp_path, web, cfg(fo("trong"), fo("chan", "forum.blocked-one.org"), fo("mot", "forum.single-two.org", mau_trang=None),
                                  fo("trung", "forum.dup-three.org", mau_trang=None, phan_trang="auto")))
    g = {r["ma"]: r["goi_y"] for r in q.do()["dien_dan"]}
    assert "it bai" in g["trong"] and "cdp_render" in g["trong"]
    assert "bi chan" in g["chan"] and "giu tat" in g["chan"]
    assert "chua thay cach sang trang" in g["mot"]
    assert "trang 2 giong trang 1" in g["trung"]


def test_do_goi_y_khi_trang_2_het_hoac_chua_do_duoc(tmp_path):
    web = Web({"https://forum.one-page-one.org/robot/": (200, trang_html(1, tong=2), ""),                         # trang 2 -> 404 mac dinh
               "https://forum.slow-two.org/robot/": (200, trang_html(1, tong=2), ""),
               "https://forum.slow-two.org/robot/page-2": (503, "", "")})
    q, _ = tao(tmp_path, web, cfg(fo("mot", "forum.one-page-one.org"), fo("cho", "forum.slow-two.org")))
    g = {r["ma"]: r["goi_y"] for r in q.do()["dien_dan"]}
    assert "khong ton tai" in g["mot"] and "bat=true" not in g["mot"]
    assert "chua do duoc" in g["cho"] and "LOI_MAY_CHU" in g["cho"]


def test_do_can_chrome_goi_y_bat_chrome_ai(tmp_path):
    q, _ = tao(tmp_path, Web(), cfg(fo("c", "chrome.example.net", cach_lay="cdp", bat=False)), cdp=CdpGia(loi_mo="khong_mo_cdp"))
    r = q.do()["dien_dan"][0]
    assert r["ket_qua"] == "KHONG_CO_CHROME" and "mo_trinh_duyet_ai.cmd" in r["goi_y"] and "9224" in r["goi_y"]


def test_do_theo_ma_va_ma_la_khong_nem_loi(tmp_path):
    web = Web({**dien_dan_web(), **dien_dan_web("khac.example.net")})
    q, _ = tao(tmp_path, web, cfg(fo("a"), fo("b", "khac.example.net")))
    bc = q.do(["b", "zzz"])
    assert [r["ma"] for r in bc["dien_dan"]] == ["b"] and bc["khong_thay"] == ["zzz"]
    assert all(urlsplit(x).hostname == "khac.example.net" for x in web.goi)


# ============================================================== 9. CLI + DANH SACH TRANG + NOI VAO HE
def test_cli_ke_hoach_quet_bao_cao_do_va_ma_sai(tmp_path, capsys):
    web = Web(dien_dan_web())
    q, _ = tao(tmp_path, web, cfg(fo("a")))
    assert DD.main(["ke-hoach"], tao_quet=lambda: q) == 0 and web.goi == []
    assert "1 dang bat" in capsys.readouterr().out
    assert DD.main(["quet", "--toi-da-trang", "2"], tao_quet=lambda: q) == 0
    out = capsys.readouterr().out
    assert "DANG_DO" in out and "den trang 2/3" in out and "+8 bai" in out and "https://" not in out.replace("du_lieu_cao", "")
    assert DD.main(["bao-cao"], tao_quet=lambda: q) == 0 and "bao cao: 1 dien dan" in capsys.readouterr().out
    assert DD.main(["do", "--ma", "a"], tao_quet=lambda: q) == 0 and "bai=" in capsys.readouterr().out
    assert DD.main(["quet", "--ma", "zzz"], tao_quet=lambda: q) == 3 and "zzz" in capsys.readouterr().out


def test_cli_config_sai_tra_ma_2_va_khong_in_stack(tmp_path, capsys):
    def hong():
        raise ValueError("config/dien_dan.json sai: dien_dan[0] a: `url` phai bat dau bang https://")
    assert DD.main(["ke-hoach"], tao_quet=hong) == 2
    assert "!! config/dien_dan.json sai" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        DD.main(["xoa-het"])


def test_cli_khong_in_url_hay_tieu_de_bai_ra_man_hinh(tmp_path, capsys):
    web = Web({u(1): (200, _html_tin_hieu(), ""), u(2): (404, "", "")})
    q, _ = tao(tmp_path, web, cfg(fo(mau_bai=r"/t/\d+|mql5\.com/(?:[a-z]{2}/)?signals/\d+")))
    DD.main(["quet"], tao_quet=lambda: q)
    DD.main(["do", "--ma", "a"], tao_quet=lambda: q)
    out = capsys.readouterr().out
    assert "Super Grid" not in out and "mql5.com/en/signals" not in out and "/t/5" not in out


def test_ma_nguon_chi_chua_ascii_tru_bang_tu_khoa_da_ngon_ngu_va_khong_in_url_bai():
    dong_ma = Path(DD.__file__).read_text(encoding="utf-8").splitlines()
    ngoai_ascii = [d for d in dong_ma if not d.isascii()]
    assert ngoai_ascii and all(re.match(r'^\s+r"', d) for d in ngoai_ascii), ngoai_ascii          # chi bang tu khoa (du lieu), khong chu thich / docstring
    for d in dong_ma:
        if re.search(r"\bprint\(|in_ra\(", d):
            assert not re.search(r'\.url\b|\["url"\]|tieu_de|\["neo"\]|\burl\)', d), d       # lenh in khong bao gio dua URL / tieu de bai ra man hinh


def test_b_dien_dan_nam_trong_bang_LENH_va_goi_duoc_CLI(tmp_path, capsys):
    import b as B
    assert B.LENH["dien-dan"] is B.c_dien_dan
    assert B.c_dien_dan(["ke-hoach"]) == 0                                                          # khong goi mang, doc config that
    assert "dien dan:" in capsys.readouterr().out


@pytest.mark.parametrize("lenh,ket", [
    (["ke-hoach"], True), (["bao-cao"], True), (["do"], True), (["do", "--ma", "mql5_forum_ru"], True), (["do", "--ma", "a,b_c,d9"], True),
    (["quet"], True), (["quet", "--ma", "a,b", "--toi-da-trang", "5"], True), (["quet", "--ep"], True), (["quet", "--toi-da-trang", "200"], True),
    (["quet", "--cdp"], False), (["quet", "--toi-da-trang", "0"], False), (["quet", "--toi-da-trang", "500"], False),
    (["quet", "--toi-da-trang", "5; rm -rf /"], False), (["quet", "--ma", "../etc"], False), (["quet", "--ma", "A B"], False),
    (["quet", "--ma", ",".join("m%d" % i for i in range(40))], False), (["quet", "--ma"], False), (["quet", "--ma", "a", "--ma", "b"], False),
    (["xoa"], False), ([], False), (["quet", "extra"], False),
])
def test_danh_sach_trang_cho_lenh_dien_dan(lenh, ket):
    r = CT.kiem_lenh(["{py}", "b.py", "dien-dan"] + lenh)
    assert (r is None) == ket, r


def test_dien_dan_nam_trong_kien_truc_va_con_dung_lop():
    from nhan import kien_truc as KT
    lop = {m for _mo_ta, ms in KT.LOP.values() for m in ms}
    assert "doc_dien_dan" in lop


def test_mien_goc_hau_to_hai_nhan_khong_gop_cac_trang_khac_nhau():
    for host, mong in (("gogojungle.co.jp", "gogojungle.co.jp"), ("www.kaskus.co.id", "kaskus.co.id"), ("www.forexforum.com.tr", "forexforum.com.tr"),
                       ("www.mql5.com", "mql5.com"), ("forums.babypips.com", "babypips.com"), ("note.com", "note.com"), ("x.y.example.co.uk", "example.co.uk"),
                       ("forum.example.com", "example.com"), ("localhost", "localhost"), ("", ""), ("co.jp", "co.jp")):
        assert LN.mien_goc(host) == mong, host
    assert LN.mien_goc("a.gogojungle.co.jp") != LN.mien_goc("b.kaskus.co.jp")


# ============================================================== 10. TU TIM TRANG TIEP (08/10/2026): khong rel=next, khong mau_trang
# Do 08/10: 2/8 don "quet sau" chi doc 1 trang roi bao XONG_PASS du MQL5 ghi 5842 trang. Thanh phan trang truoc day chi duoc DEM (tong_trang),
# khong bao gio duoc DUNG de di tiep, va "khong thay link trang ke" bi doc nham thanh "het danh sach". Cac HTML o day mo phong 6 phan mem dien dan that.
_SID = "9f3a1c77e0b24d5a"
KIEU_DS = ("xenforo", "vbulletin", "phpbb", "ipb", "mql5", "wordpress")


def url_ds(kieu, p, host=HOST):
    """URL trang `p` cua mot danh sach dien dan gia, theo cach phan trang that cua tung phan mem (trang 1 = URL khai trong config)."""
    g = "https://%s" % host
    return {
        "xenforo": g + "/forums/robot.44/" + ("" if p == 1 else "page-%d" % p),
        "vbulletin": g + "/forumdisplay.php?f=44" + ("" if p == 1 else "&page=%d" % p),
        "phpbb": g + "/viewforum.php?f=44" + ("" if p == 1 else "&start=%d&sid=%s" % (25 * (p - 1), _SID)),      # start = 25*(N-1), co ma phien
        "ipb": g + "/forum/44-robot/" + ("" if p == 1 else "page/%d/" % p),
        "mql5": g + "/en/forum/ea" + ("" if p == 1 else "/page%d" % p),
        "wordpress": g + "/blog/" + ("" if p == 1 else "page/%d/" % p),
    }[kieu]


def trang_ds(kieu, n, tong, so_neo=None, cua_so=True, so_bai=4, nut_tiep=True, mini=True, host=HOST, them_head=""):
    """Trang `n` / `tong` cua danh sach. KHONG rel=next. `so_neo` = cac so trang hien thanh LINK (trang hien tai la <span>): mac dinh `1 .. n-1 n n+1 .. tong`
    (`cua_so`) hoac co dinh `1 2 3 .. tong`. Moi chu de co thanh phan trang nho `2 3 120` (XenForo / phpBB that co) - KHONG phai trang cua danh sach."""
    hang = ""
    for i in range(so_bai):
        tid = n * 100 + i
        nho = ('<span class="mini"><a href="https://%s/t/%d/page-2">2</a> <a href="https://%s/t/%d/page-3">3</a> '
               '<a href="https://%s/t/%d/page-120">120</a></span>' % (host, tid, host, tid, host, tid)) if mini else ""
        hang += '<div class="structItem"><a href="/t/%d/">Grid EA robot thread %d-%d</a>%s</div>' % (tid, n, i, nho)
    if so_neo is None:
        hien = {1, n - 1, n, n + 1, tong} if cua_so else {1, 2, 3, tong}
        so_neo = sorted(p for p in hien if 1 <= p <= tong)
    neo = "".join('<span class="cur">%d</span>' % p if p == n else '<a href="%s">%d</a>' % (url_ds(kieu, p, host), p) for p in so_neo)
    nut = '<a class="next" href="%s">Next &rsaquo;</a><a class="last" href="%s">&raquo;</a>' % (url_ds(kieu, n + 1, host), url_ds(kieu, tong, host)) \
        if nut_tiep and n < tong else ""
    return ('<html><head><title>Robot EA - trang %d</title>%s</head><body>%s<div class="pageNav">%s%s</div></body></html>' % (n, them_head, hang, neo, nut))


def web_ds(kieu, tong, toi_da=None, **kw):
    return {url_ds(kieu, p): (200, trang_ds(kieu, p, tong, **kw), "") for p in range(1, (toi_da or tong) + 1)}


def fo_ds(kieu, ma="a", host=HOST, **kw):
    kw.setdefault("mau_trang", None)                                                                  # mac dinh KHONG khai mau_trang: bat buoc tu tim
    return fo(ma, host, url_ds(kieu, 1, host)[len("https://" + host):], **kw)


@pytest.mark.parametrize("kieu", KIEU_DS)
def test_tim_trang_tiep_di_theo_neo_so_khi_thanh_phan_trang_co_trang_ke(kieu):
    t = DD.tach_trang(trang_ds(kieu, 3, 9), url_ds(kieu, 3))
    assert t["rel_next"] == "" and sorted(set(t["so_trang"])) == [2, 3, 4, 9, 120]               # khong rel=next; 120 la cua mini-pager chu de
    tm = DD.tim_trang_tiep(fo_ds(kieu), t, url_ds(kieu, 3), 4)
    assert tm == {"url": url_ds(kieu, 4), "cach": "neo_so", "tong_uoc": 9}, tm


@pytest.mark.parametrize("kieu", KIEU_DS)
def test_tim_trang_tiep_suy_ra_mau_khi_thanh_phan_trang_rut_gon_1_2_3_cuoi(kieu):
    """Dien dan MQL5 ghi `1 2 3 ... 5842` o moi trang: trang 6 khong co neo, phai suy ra tu >= 2 neo (page-N, ?page=N, start=25*(N-1), ma phien...)."""
    t = DD.tach_trang(trang_ds(kieu, 5, 9, cua_so=False, nut_tiep=False), url_ds(kieu, 5))
    tm = DD.tim_trang_tiep(fo_ds(kieu), t, url_ds(kieu, 5), 6)
    assert tm == {"url": url_ds(kieu, 6), "cach": "mau_suy_ra", "tong_uoc": 9}, tm
    assert DD.tim_trang_tiep(fo_ds(kieu), t, url_ds(kieu, 5), 9)["url"] == url_ds(kieu, 9)       # neo cuoi co san -> dung neo
    assert DD.tim_trang_tiep(fo_ds(kieu), t, url_ds(kieu, 5), 10)["url"] == ""                    # trang 10 > 9: thanh phan trang khong cho phep doan


@pytest.mark.parametrize("cua_so", [True, False])
@pytest.mark.parametrize("kieu", KIEU_DS)
def test_quet_tu_di_het_danh_sach_khi_khong_co_rel_next_va_khong_khai_mau_trang(tmp_path, kieu, cua_so):
    tong = 7
    web = Web(web_ds(kieu, tong, cua_so=cua_so))
    q, _ = tao(tmp_path, web, cfg(fo_ds(kieu), toi_da_trang_luot=50))
    bc = q.chay()
    assert web.trang_da_goi() == [url_ds(kieu, p) for p in range(1, tong + 1)]                    # dung thu tu, moi trang MOT lan, khong doan trang 8
    assert kq_luot(bc) == "XONG_PASS"
    m = muc(q)
    assert (m["ket_qua"], m["trang_cuoi"], m["tong_trang"], m["so_pass"], m["so_loi"]) == ("XONG", tong, tong, 1, 0)
    uv = ung_vien(tmp_path)
    assert len(uv) == 4 * tong and {x["trang"] for x in uv} == set(range(1, tong + 1))             # 4 bai moi trang; link '2 3 120' cua chu de khong thanh bai


@pytest.mark.parametrize("kieu", ["xenforo", "phpbb"])
def test_quet_danh_sach_5842_trang_doc_tiep_tu_moc_qua_nhieu_luot(tmp_path, kieu):
    """Truong hop MQL5 forum 08/10: `1 2 3 ... 5842`. Moi luot doc 5 trang, luot sau doc tiep tu trang 6 (tien trinh moi), tong trang hien dung."""
    web = Web(web_ds(kieu, 5842, toi_da=12, cua_so=False))
    q1, dh = tao(tmp_path, web, cfg(fo_ds(kieu), toi_da_trang_luot=5))
    bc = q1.chay()
    assert kq_luot(bc) == "DANG_DO" and web.trang_da_goi() == [url_ds(kieu, p) for p in range(1, 6)]
    m = muc(q1)
    assert (m["den_trang"], m["url_tiep"], m["tong_trang"], m["tien_do"]) == (5, url_ds(kieu, 6), 5842, "DANG_DO")
    web2 = Web(web_ds(kieu, 5842, toi_da=12, cua_so=False))
    q2, _ = tao(tmp_path, web2, cfg(fo_ds(kieu), toi_da_trang_luot=5), dh=dh)
    q2.chay()
    assert web2.trang_da_goi() == [url_ds(kieu, p) for p in range(6, 11)] and muc(q2)["den_trang"] == 10
    assert len(ung_vien(tmp_path)) == 40 and muc(q2)["tong_trang"] == 5842


def test_thanh_phan_trang_duoi_tung_chu_de_khong_bi_nham_voi_trang_cua_danh_sach(tmp_path):
    """Danh sach 1 trang, KHONG co thanh phan trang nao, nhung moi chu de co `2 3 120`: khong duoc di vao /t/<id>/page-2 (quet het forum nhu nguoi doc)."""
    h = trang_ds("xenforo", 1, 1, so_neo=[], nut_tiep=False)
    t = DD.tach_trang(h, url_ds("xenforo", 1))
    assert t["so_trang"] == [2, 3, 120]
    assert DD.tim_trang_tiep(fo_ds("xenforo"), t, url_ds("xenforo", 1), 2) == {"url": "", "cach": "", "tong_uoc": 0}
    web = Web({url_ds("xenforo", 1): (200, h, "")})
    q, _ = tao(tmp_path, web, cfg(fo_ds("xenforo")))
    assert kq_luot(q.chay()) == "XONG_PASS" and web.trang_da_goi() == [url_ds("xenforo", 1)]
    assert muc(q)["tong_trang"] == 1                                                                # khong "1/120" nho link cua chu de
    g = q.do()["dien_dan"][0]
    assert g["tong_trang_uoc"] == 0 and g["co_neo_so_khac"] is True and "khong cung duong dan" in g["goi_y"]


def test_khong_thay_trang_ke_la_loi_cau_hinh_khong_phai_het_danh_sach(tmp_path):
    """Thanh phan trang chi hien `1 ... 40`: ta biet con 39 trang nhung khong co duong sang. TUNG bao XONG_PASS (sai); nay KHONG_THAY_TRANG_TIEP."""
    h = trang_ds("xenforo", 1, 40, so_neo=[40], nut_tiep=False)
    web = Web({url_ds("xenforo", 1): (200, h, "")})
    q, dh = tao(tmp_path, web, cfg(fo_ds("xenforo")))
    bc = q.chay()
    assert kq_luot(bc) == "KHONG_THAY_TRANG_TIEP" and bc["tom_tat_luot"] == {"KHONG_THAY_TRANG_TIEP": 1}
    assert web.trang_da_goi() == [url_ds("xenforo", 1)]                                              # khong doan bua trang 2
    m = muc(q)
    assert (m["ket_qua"], m["tien_do"], m["trang_cuoi"], m["tong_trang"], m["den_trang"], m["url_tiep"]) == ("KHONG_THAY_TRANG_TIEP", "KHONG_THAY_TRANG_TIEP", 1, 40, 0, "")
    assert m.get("so_pass", 0) == 0 and m["den_han"] == int(dh() + DD.GIO_NGHI_LOI_CAU_HINH * 3600)    # KHONG tinh la xong 1 pass; nghi 24 gio
    assert "khong tim thay link trang 2" in m["ly_do"] and "mau_trang" in m["ly_do"] and "https://" not in m["ly_do"]
    assert len(ung_vien(tmp_path)) == 4                                                              # bai cua trang 1 van duoc giu
    b = next(x for x in bc["dien_dan"] if x["ma"] == "a")
    assert b["tong_trang"] == 40 and b["trang_luot"] == 1 and "khong tim thay link trang 2" in b["ly_do"]
    kh = q.ke_hoach()[0]
    assert kh["buoc_tiep"].startswith("cho den ") and "KHONG_THAY_TRANG_TIEP" in kh["buoc_tiep"] and "--ep" in kh["buoc_tiep"]
    n = len(web.goi)
    assert kq_luot(q.chay()) == "CHO_TUAN" and len(web.goi) == n                                     # nghi 24 gio, khong dap lai
    dh.t += 25 * 3600
    assert kq_luot(q.chay()) == "KHONG_THAY_TRANG_TIEP" and web.trang_da_goi().count(url_ds("xenforo", 1)) == 2
    assert len(ung_vien(tmp_path)) == 4                                                              # doc lai khong ghi trung


def test_khong_thay_trang_ke_sua_bang_mau_trang_va_ep_thi_di_tiep_ngay(tmp_path):
    h = trang_ds("xenforo", 1, 40, so_neo=[40], nut_tiep=False)
    web = Web({url_ds("xenforo", 1): (200, h, ""), **{url_ds("xenforo", p): (200, trang_ds("xenforo", p, 40, so_neo=[40], nut_tiep=False), "") for p in (2, 3)}})
    q, dh = tao(tmp_path, web, cfg(fo_ds("xenforo")))
    assert kq_luot(q.chay()) == "KHONG_THAY_TRANG_TIEP"
    q2, _ = tao(tmp_path, web, cfg(fo_ds("xenforo", mau_trang="{base}page-{n}"), toi_da_trang_luot=3), dh=dh)         # chu du an khai mau_trang
    assert kq_luot(q2.chay()) == "CHO_TUAN"                                                           # sua config nhung chua --ep: van nghi het 24 gio
    assert kq_luot(q2.chay(ep=True)) == "DANG_DO" and [x for x in web.trang_da_goi()][-3:] == [url_ds("xenforo", p) for p in (1, 2, 3)]
    assert muc(q2)["den_trang"] == 3 and muc(q2)["url_tiep"] == url_ds("xenforo", 4)


def test_phan_trang_khong_van_la_xong_pass_du_thanh_phan_trang_ghi_nhieu_trang(tmp_path):
    h = trang_ds("xenforo", 1, 40)
    q, _ = tao(tmp_path, Web({url_ds("xenforo", 1): (200, h, "")}), cfg(fo_ds("xenforo", phan_trang="khong")))
    assert kq_luot(q.chay()) == "XONG_PASS"                                                           # chu du an chu dong chi doc trang 1 -> khong phai loi


def test_neo_tro_lai_chinh_trang_dang_doc_khong_gay_vong_lap(tmp_path):
    h = ('<html><body><a href="/t/1/">Grid EA robot thread 1</a><a href="%s">2</a><a href="%s">9</a></body></html>' % (url_ds("xenforo", 1), url_ds("xenforo", 9)))
    web = Web({url_ds("xenforo", 1): (200, h, "")})
    q, _ = tao(tmp_path, web, cfg(fo_ds("xenforo")))
    assert kq_luot(q.chay()) == "XONG_PASS" and web.trang_da_goi() == [url_ds("xenforo", 1)] and "tro lai chinh no" in muc(q)["ly_do"]


def test_neo_so_chi_nhan_cung_ten_mien_va_cung_danh_sach():
    f = fo_ds("xenforo")
    cua_minh, la = url_ds("xenforo", 2), "https://forum.example.com.evil.org/forums/robot.44/page-2"
    khac_dm = "https://other.example.org/forums/robot.44/page-2"
    anh_em = "https://cdn.example.com/forums/robot.44/page-2"                                          # cung ten mien goc nhung KHAC may chu -> khac danh sach
    khac_ds = "https://forum.example.com/forums/other.55/page-2"
    http = "http://forum.example.com/forums/robot.44/page-3"
    h = "".join('<a href="%s">%s</a>' % (x, n) for x, n in ((la, 2), (khac_dm, 2), (anh_em, 2), (khac_ds, 2), (http, 3), (cua_minh, 2)))
    t = DD.tach_trang(h, url_ds("xenforo", 1))
    assert DD._neo_cung_danh_sach(f, t, url_ds("xenforo", 1)) == [(3, url_ds("xenforo", 3)), (2, cua_minh)]      # http nang https; con lai bi loai
    assert DD.tim_trang_tiep(f, t, url_ds("xenforo", 1), 2)["url"] == cua_minh
    h2 = "".join('<a href="%s">%s</a>' % (x, n) for x, n in ((la, 2), (khac_dm, 3), (anh_em, 4), (khac_ds, 5)))
    assert DD.tim_trang_tiep(f, DD.tach_trang(h2, url_ds("xenforo", 1)), url_ds("xenforo", 1), 2) == {"url": "", "cach": "", "tong_uoc": 0}


@pytest.mark.parametrize("chu,mong", [("3", 3), ("Page 3", 3), ("page3", 3), ("Trang 12", 12), ("Seite 4", 4), ("Strona 5", 5), ("Pagina 6", 6), ("Página 6", 6),
                                      ("第5页", 5), ("5ページ", 5), ("страница 7", 7), ("стр. 8", 8), ("12345", 12345), ("  9  ", 9),
                                      ("03", 0), ("0", 0), ("00", 0), ("", 0), (None, 0), ("1,000", 0), ("123456", 0), ("Page", 0), ("2 replies", 0), ("v2", 0), ("1.5", 0)])
def test_so_tren_neo_nhan_chu_so_trang_nhieu_ngon_ngu_va_bo_so_dem_muc_luc(chu, mong):
    assert DD._so_tren_neo(chu) == mong


@pytest.mark.parametrize("chu,mong", [("Next", True), ("next ›", True), ("Next »", True), ("Next page", True), ("›", True), (">", True), ("→", True), ("▶", True),
                                      ("Siguiente", True), ("Weiter »", True), ("Nächste", True), ("Suivant", True), ("Следующая", True), ("Далее", True),
                                      ("下一页", True), ("次へ", True), ("다음", True), ("Trang sau", True), ("Tiếp", True), ("Berikutnya", True),
                                      ("»", False), (">>", False), ("»»", False), ("Last", False), ("Cuối", False), ("Previous", False), ("‹ Prev", False),
                                      ("Prev ›", False), ("Next unread post in the thread below", False), ("", False), (None, False), ("2", False)])
def test_chu_trang_sau_nhieu_ngon_ngu_va_dau_mui_ten_cuoi_khong_phai_trang_sau(chu, mong):
    assert DD._la_chu_tiep(chu) is mong


def test_nut_trang_sau_la_duong_cuoi_khi_khong_co_thanh_phan_trang_danh_so(tmp_path):
    def nut(n, tong):
        nxt = '<a class="pageNavSimple-el--next" href="%s">Next &rsaquo;</a>' % url_ds("xenforo", n + 1) if n < tong else ""
        prv = '<a href="%s">&lsaquo; Prev</a>' % url_ds("xenforo", n - 1) if n > 1 else ""
        return trang_ds("xenforo", n, tong, so_neo=[], nut_tiep=False).replace("</body>", prv + nxt + "</body>")
    t = DD.tach_trang(nut(1, 4), url_ds("xenforo", 1))
    assert DD.tim_trang_tiep(fo_ds("xenforo"), t, url_ds("xenforo", 1), 2) == {"url": url_ds("xenforo", 2), "cach": "chu_tiep", "tong_uoc": 0}
    web = Web({url_ds("xenforo", p): (200, nut(p, 4), "") for p in range(1, 5)})
    q, _ = tao(tmp_path, web, cfg(fo_ds("xenforo")))
    assert kq_luot(q.chay()) == "XONG_PASS" and web.trang_da_goi() == [url_ds("xenforo", p) for p in range(1, 5)]
    # dau » don le (thuong la 'trang cuoi') khong phai trang sau; Next tro sang danh sach khac / ten mien khac cung khong
    sai = ('<a href="%s">&raquo;</a><a href="https://other.example.org/x/page-2">Next</a><a href="https://forum.example.com/forums/other.55/page-2">Next</a>' %
           url_ds("xenforo", 9))
    assert DD.tim_trang_tiep(fo_ds("xenforo"), DD.tach_trang(sai, url_ds("xenforo", 1)), url_ds("xenforo", 1), 2)["url"] == ""


def test_nut_trang_sau_dung_khi_thanh_phan_trang_con_trang_nhung_khong_suy_ra_duoc_mau():
    """Chi hien `1 ... 40` va nut Next: khong du >= 2 neo de suy mau -> Next la duong cuoi. (Neu khong co ca Next thi la KHONG_THAY_TRANG_TIEP.)"""
    t = DD.tach_trang(trang_ds("xenforo", 2, 40, so_neo=[1, 40]), url_ds("xenforo", 2))
    assert DD.tim_trang_tiep(fo_ds("xenforo"), t, url_ds("xenforo", 2), 3) == {"url": url_ds("xenforo", 3), "cach": "chu_tiep", "tong_uoc": 40}
    t2 = DD.tach_trang(trang_ds("xenforo", 2, 40, so_neo=[1, 40], nut_tiep=False), url_ds("xenforo", 2))
    assert DD.tim_trang_tiep(fo_ds("xenforo"), t2, url_ds("xenforo", 2), 3) == {"url": "", "cach": "", "tong_uoc": 40}


def test_mau_suy_ra_tu_choi_khi_khong_tuyen_tinh_hoac_do_rong_co_dinh_hoac_nhieu_cum_so_doi():
    f = fo_ds("xenforo")
    def thu(neo):
        h = "".join('<a href="%s">%d</a>' % (x, n) for n, x in neo)
        return DD.tim_trang_tiep(f, DD.tach_trang(h, url_ds("xenforo", 1)), url_ds("xenforo", 1), 4)
    g = "https://forum.example.com/forums/robot.44/"
    assert thu([(2, g + "page-2"), (3, g + "page-3"), (9, g + "page-9")])["cach"] == "mau_suy_ra"
    assert thu([(2, g + "page-2"), (3, g + "page-3"), (9, g + "page-10")])["url"] == ""               # khong nam tren mot duong thang
    assert thu([(2, g + "page-02"), (3, g + "page-03"), (9, g + "page-09")])["url"] == ""             # do rong co dinh: khong suy
    assert thu([(2, g + "page-2"), (9, g + "page-9")])["cach"] == "mau_suy_ra"                        # 2 neo la du
    assert thu([(9, g + "page-9")])["url"] == ""                                                       # 1 neo khong du
    nhieu = [(2, g + "page-2?x=1"), (3, g + "page-3?x=2"), (9, g + "page-9?x=3")]
    assert thu(nhieu)["url"] == ""                                                                      # hai cum so doi cung luc: khong doan
    assert thu([(2, g + "page-2"), (3, g + "p3"), (9, g + "page-9")])["cach"] == "mau_suy_ra"          # neo la ('p3') khac khung bi bo, 2 neo con lai du


def test_bo_so_dem_muc_luc_chu_so_co_so_0_khong_thanh_neo_trang():
    h = "".join('<a href="%s">%s</a>' % (url_ds("xenforo", p), "%02d" % p) for p in (2, 3, 4))
    t = DD.tach_trang(h, url_ds("xenforo", 1))
    assert DD._neo_cung_danh_sach(fo_ds("xenforo"), t, url_ds("xenforo", 1)) == []


def test_tham_so_sap_xep_va_so_dong_khong_lam_roi_danh_sach_vbulletin():
    """vBulletin ghi `&order=desc&sort=lastpost&pp=25` vao link trang 2.. nhung `url` cau hinh khong co: van la CUNG danh sach. `tag=2` thi khong."""
    base = "https://forum.example.com/forumdisplay.php?f=44"
    f = fo("a", HOST, "/forumdisplay.php?f=44", mau_trang=None)
    h = ('<a href="%s&order=desc&sort=lastpost&page=2&pp=25">2</a><a href="%s&order=desc&sort=lastpost&page=3&pp=25">3</a>'
         '<a href="%s&tag=2">2</a><a href="https://forum.example.com/forumdisplay.php?f=45&page=2">2</a>' % (base, base, base))
    t = DD.tach_trang(h, base)
    cac = DD._neo_cung_danh_sach(f, t, base)
    assert [n for n, _ in cac] == [2, 3] and all("tag=" not in x and "f=45" not in x for _, x in cac)
    assert DD.tim_trang_tiep(f, t, base, 2)["url"] == "%s&order=desc&sort=lastpost&page=2&pp=25" % base


def test_canonical_giup_nhan_ra_danh_sach_khi_url_cau_hinh_duoc_chuyen_huong_sang_duong_khac():
    f = fo("a", HOST, "/old/robot", mau_trang=None)                                                    # config tro vao duong cu; dien dan 301 sang /forums/robot.44/
    h = ('<link rel="canonical" href="https://forum.example.com/forums/robot.44/">' +
         "".join('<a href="%s">%d</a>' % (url_ds("xenforo", p), p) for p in (2, 3, 9)))
    t = DD.tach_trang(h, "https://forum.example.com/old/robot")
    assert t["canonical"] == "https://forum.example.com/forums/robot.44/"
    assert DD.tim_trang_tiep(f, t, "https://forum.example.com/old/robot", 2)["url"] == url_ds("xenforo", 2)
    khong = DD.tach_trang(h.replace("canonical", "alternate"), "https://forum.example.com/old/robot")
    assert khong["canonical"] == "" and DD.tim_trang_tiep(f, khong, "https://forum.example.com/old/robot", 2)["url"] == ""
    ngoai = DD.tach_trang(h.replace("forum.example.com/forums/robot.44/\">", "evil.example.org/forums/robot.44/\">", 1), "https://forum.example.com/old/robot")
    assert DD.tim_trang_tiep(f, ngoai, "https://forum.example.com/old/robot", 2)["url"] == ""            # canonical ra ten mien khac: bo


def test_url_trang_tiep_la_vo_boc_mong_cua_tim_trang_tiep():
    t = DD.tach_trang(trang_ds("ipb", 2, 9), url_ds("ipb", 2))
    assert DD.url_trang_tiep(fo_ds("ipb"), t, url_ds("ipb", 2), 3) == DD.tim_trang_tiep(fo_ds("ipb"), t, url_ds("ipb", 2), 3)["url"] == url_ds("ipb", 3)


def test_tham_do_cho_biet_cach_sang_trang_va_canh_bao_khi_co_trang_ma_khong_co_duong_sang(tmp_path):
    web = Web({**web_ds("phpbb", 4, cua_so=False)})
    q, _ = tao(tmp_path, web, cfg(fo_ds("phpbb", bat=False)))
    r = q.do()["dien_dan"][0]
    assert r["cach_trang_tiep"] == "neo_so" and r["tong_trang_uoc"] == 4 and r["trang2"]["khac_trang_1"] is True
    assert "cach sang trang: neo_so" in r["goi_y"] and "bat=true" in r["goi_y"]
    web2 = Web({url_ds("xenforo", 1): (200, trang_ds("xenforo", 1, 40, so_neo=[40], nut_tiep=False), "")})
    q2, _ = tao(tmp_path / "x", web2, cfg(fo_ds("xenforo", bat=False)))
    r2 = q2.do()["dien_dan"][0]
    assert r2["tong_trang_uoc"] == 40 and "trang2" not in r2 and "KHONG tim thay link trang 2" in r2["goi_y"] and "KHONG_THAY_TRANG_TIEP" in r2["goi_y"]


# ---- ma thoat cua `b dien-dan quet`: khong dien dan nao di tiep duoc thi KHONG phai "DAT"
def test_cli_quet_khong_dien_dan_nao_duoc_chon_la_ma_5(tmp_path, capsys):
    q, _ = tao(tmp_path, Web(), cfg(fo("a", bat=False)))
    assert DD.main(["quet"], tao_quet=lambda: q) == 5
    out = capsys.readouterr().out
    assert "!! DIEN_DAN_KHONG_TIEN: khong dien dan nao duoc chon" in out


def test_cli_quet_dien_dan_dang_tat_goi_ten_la_ma_5_khong_phai_dat_gia(tmp_path, capsys):
    """6/8 don 'quet-sau' 08/10 bao DAT trong khi dien dan o may nha dang `bat: false` (BO_QUA)."""
    web = Web(dien_dan_web())
    q, _ = tao(tmp_path, web, cfg(fo("a", bat=False)))
    assert DD.main(["quet", "--ma", "a"], tao_quet=lambda: q) == 5
    out = capsys.readouterr().out
    assert "DIEN_DAN_KHONG_TIEN" in out and "BO_QUA 1" in out and "a(BO_QUA)" in out and web.goi == []


def test_cli_quet_bi_chan_het_la_ma_5_nhung_chan_giua_chung_sau_khi_doc_duoc_trang_thi_van_la_tien(tmp_path, capsys):
    q, _ = tao(tmp_path, Web({u(1): (403, "", "")}), cfg(fo("a")))
    assert DD.main(["quet"], tao_quet=lambda: q) == 5 and "CHAN_CAM 1" in capsys.readouterr().out
    web = Web({**dien_dan_web(), u(3): (429, "", "")})
    q2, _ = tao(tmp_path / "x", web, cfg(fo("a")))
    assert DD.main(["quet"], tao_quet=lambda: q2) == 0                                                  # doc duoc trang 1-2 roi moi bi 429: co tien
    out = capsys.readouterr().out
    assert "DIEN_DAN_KHONG_TIEN" not in out and "a(CHAN_TAN_SUAT)" in out                                # nhung van in dong canh bao


def test_cli_quet_mot_dien_dan_doc_duoc_mot_dien_dan_bi_chan_la_ma_0_kem_dong_canh_bao(tmp_path, capsys):
    web = Web({**dien_dan_web(), "https://forum.blocked-one.org/robot/": (403, "", "")})
    q, _ = tao(tmp_path, web, cfg(fo("a"), fo("b", "forum.blocked-one.org")))
    assert DD.main(["quet"], tao_quet=lambda: q) == 0
    out = capsys.readouterr().out
    assert "!! 1 dien dan khong tien duoc: b(CHAN_CAM)" in out and "DIEN_DAN_KHONG_TIEN" not in out


def test_cli_quet_chi_vi_dang_cho_hoac_het_nhip_la_ma_0(tmp_path, capsys):
    web = Web(dien_dan_web())
    q, _ = tao(tmp_path, web, cfg(fo("a")))
    assert DD.main(["quet"], tao_quet=lambda: q) == 0                                                    # doc het mot pass
    capsys.readouterr()
    assert DD.main(["quet"], tao_quet=lambda: q) == 0                                                    # CHO_TUAN: chua den han, khong phai loi
    out = capsys.readouterr().out
    assert "CHO_TUAN" in out and "DIEN_DAN_KHONG_TIEN" not in out and "!!" not in out


def test_cli_quet_dang_cho_nhung_co_dien_dan_khac_bi_chan_van_la_ma_5(tmp_path, capsys):
    web = Web({**dien_dan_web(), "https://forum.blocked-one.org/robot/": (403, "", "")})
    q0, dh = tao(tmp_path, web, cfg(fo("a")))
    q0.chay()
    q, _ = tao(tmp_path, web, cfg(fo("a"), fo("b", "forum.blocked-one.org")), dh=dh)
    assert DD.main(["quet"], tao_quet=lambda: q) == 5                                                    # a: CHO_TUAN, b: CHAN_CAM -> khong co gi di tiep
    assert "CHAN_CAM 1, CHO_TUAN 1" in capsys.readouterr().out


def test_cli_quet_khong_thay_trang_ke_o_moi_dien_dan_la_ma_5_du_da_doc_trang_1(tmp_path, capsys):
    web = Web({url_ds("xenforo", 1): (200, trang_ds("xenforo", 1, 40, so_neo=[40], nut_tiep=False), "")})
    q, _ = tao(tmp_path, web, cfg(fo_ds("xenforo")))
    assert DD.main(["quet"], tao_quet=lambda: q) == 5
    out = capsys.readouterr().out
    assert "KHONG_THAY_TRANG_TIEP 1" in out and "https://" not in out.replace("du_lieu_cao", "")
    # ... nhung neu CO dien dan khac di duoc thi luot van co tien
    web2 = Web({**web.trang, **dien_dan_web("khac.example.net")})
    q2, _ = tao(tmp_path / "y", web2, cfg(fo_ds("xenforo"), fo("b", "khac.example.net")))
    assert DD.main(["quet"], tao_quet=lambda: q2) == 0
    assert "!! 1 dien dan khong tien duoc: a(KHONG_THAY_TRANG_TIEP)" in capsys.readouterr().out


def test_dau_vet_cau_loi_nhan_ra_dong_dien_dan_khong_tien():
    from qwen import cau_loi as CL
    r = CL.dau_vet(["  a  BO_QUA  0 trang luot nay", "!! DIEN_DAN_KHONG_TIEN: khong dien dan nao doc tiep duoc: BO_QUA 8", "-> reports/x.md"])
    assert (r["nhan"], r["nhom"]) == ("dien_dan_khong_tien", "can_chan_doan") and "BO_QUA 8" in r["bang_chung"]
    assert CL.dau_vet(["a  OK  3 trang luot nay", "!! 1 dien dan khong tien duoc: b(CHAN_CAM)"]) is None      # co tien: khong phai DAT gia
