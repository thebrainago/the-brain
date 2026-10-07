# -*- coding: utf-8 -*-
"""link_nguon: link chu du an dua -> phan loai -> ke hoach -> nhip lich su -> tom tat cau truc trang.

Khong goi mang that: robots / dong ho / ham ngu deu duoc tiem. Hieu chuan hai chieu: moi kiem tra "link nay la RIENG" co mot kiem tra
"link cong khai gan giong khong bi nham la rieng"; moi kiem tra "bi chan thi nghi" co mot kiem tra "OK thi khong nghi".
Dieu quan trong nhat cua file nay: **bi mat khong lot ra bao cao / trang thai gui di** (repo la PUBLIC).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from nhan import link_nguon as LN

MOI_NHOM = "https://t.me/+Zq9XkLmN0pQrStUv"
MAT_KHAU = "Xk93mQ7pLz"


@pytest.fixture(autouse=True)
def _khong_cham_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(LN, "FILE_LINK_RIENG", (tmp_path / "link_rieng.txt", tmp_path / "config" / "link_rieng.txt"))
    monkeypatch.setattr(LN, "TRANG_THAI", tmp_path / "du_lieu_cao" / "trang_thai.json")
    monkeypatch.setattr(LN, "BAO_CAO_JSON", tmp_path / "reports" / "kh.json")
    monkeypatch.setattr(LN, "BAO_CAO_MD", tmp_path / "reports" / "kh.md")


class DongHo:
    """Dong ho gia: ngu() chi day kim len, khong cho that."""

    def __init__(self, t=1000.0):
        self.t, self.da_ngu = t, []

    def __call__(self):
        return self.t

    def ngu(self, s):
        self.da_ngu.append(s)
        self.t += s


# ------------------------------------------------------------------ TIM LINK
class TestTimLink:
    def test_cat_dau_cau_va_ngoac_thua(self):
        vb = ("xem (https://www.mql5.com/en/signals/123), roi https://www.myfxbook.com/members/a/b/9. "
              "va \"https://github.com/o/r\"; ket thuc https://t.me/kenhabc!")
        assert LN.tim_link(vb) == ["https://www.mql5.com/en/signals/123", "https://www.myfxbook.com/members/a/b/9",
                                   "https://github.com/o/r", "https://t.me/kenhabc"]

    def test_giu_ngoac_dong_khi_link_co_ngoac_mo(self):
        assert LN.tim_link("https://vi.wikipedia.org/wiki/Foo_(bar)") == ["https://vi.wikipedia.org/wiki/Foo_(bar)"]

    def test_khong_co_scheme_va_dau_cau_toan_goc(self):
        got = LN.tim_link("vao t.me/goldbot123， hoac www.fxblue.com/users/ab。")
        assert got == ["https://t.me/goldbot123", "https://www.fxblue.com/users/ab"]

    def test_khu_trung_va_khong_bat_email(self):
        assert LN.tim_link("a@t.me/x https://t.me/kenh1 https://t.me/kenh1") == ["https://t.me/kenh1"]

    def test_van_ban_rong_hoac_khong_phai_chuoi(self):
        assert LN.tim_link("") == [] and LN.tim_link(None) == []


# ------------------------------------------------------------------ CHUAN HOA
class TestChuanHoa:
    def test_cung_mot_trang_khac_vo(self):
        a = "https://www.mql5.com/en/signals/2196457?source=Site+Signals+Subscriptions#!tab=history"
        b = "http://mql5.com/vi/signals/2196457/"
        c = "https://www.mql5.com/signals/2196457?utm_source=x&fbclid=y"
        assert LN.ma_link(a) == LN.ma_link(b) == LN.ma_link(c)

    def test_khac_tai_nguyen_thi_khac_ma(self):
        assert LN.ma_link("https://www.mql5.com/en/signals/1") != LN.ma_link("https://www.mql5.com/en/signals/2")
        assert LN.ma_link("https://mql5.com/en/signals/1") != LN.ma_link("https://mql5.com/en/market/product/1")

    def test_telegram_xem_truoc_bang_ten_goc_va_khong_phan_biet_hoa(self):
        assert LN.ma_link("https://t.me/s/GoldReaper") == LN.ma_link("t.me/goldreaper") == LN.ma_link("https://telegram.me/GOLDREAPER")

    def test_ma_moi_nhom_giu_nguyen_chu_hoa(self):
        assert LN.chuan_hoa_url("https://t.me/+AbCdEf").endswith("/+AbCdEf")
        assert LN.ma_link("https://t.me/+AbCdEf") != LN.ma_link("https://t.me/+abcdef")

    def test_facebook_chi_giu_tham_so_dinh_danh(self):
        u = LN.chuan_hoa_url("https://www.facebook.com/groups/botfx/?mibextid=abc&ref=share&__cft__[0]=zz")
        assert u == "https://facebook.com/groups/botfx"
        assert "id=7" in LN.chuan_hoa_url("https://facebook.com/profile.php?id=7&mibextid=1")


# ------------------------------------------------------------------ PHAN LOAI
BANG = [
    # url, nen_tang, loai, rieng, cach_lay
    ("https://www.mql5.com/en/signals/2196457", "mql5", "tin_hieu", False, "http"),
    ("https://www.mql5.com/en/market/product/12345", "mql5", "san_pham_market", False, "http"),
    ("https://www.mql5.com/en/code/9876", "mql5", "ma_nguon", False, "http"),
    ("https://www.mql5.com/en/users/someone/signals", "mql5", "nguoi_dung", False, "http"),
    ("https://www.myfxbook.com/members/user/system-x/1234567", "myfxbook", "tai_khoan_cong_khai", False, "cdp"),
    ("https://www.myfxbook.com/portfolio/grid-bot/777", "myfxbook", "portfolio", False, "cdp"),
    ("https://www.fxblue.com/users/trader1", "fxblue", "tai_khoan_cong_khai", False, "http"),
    ("https://www.tradingview.com/script/AbC123-ten-script/", "tradingview", "pine_script", False, "http"),
    ("https://ctrader.com/algos/cbots/show/1234", "ctrader", "thuat_toan", False, "http"),
    ("https://github.com/owner/ea-grid", "github", "kho_ma", False, "http"),
    ("https://raw.githubusercontent.com/o/r/main/a.mq5", "github_raw", "tep_tho", False, "http"),
    ("https://t.me/GoldReaperEA", "telegram", "kenh_cong_khai", False, "telethon"),
    ("https://t.me/GoldReaperEA/4821", "telegram", "tin_nhan_cong_khai", False, "telethon"),
    ("https://t.me/somebot", "telegram", "bot", False, "telethon"),
    (MOI_NHOM, "telegram", "moi_vao_nhom", True, "telethon"),
    ("https://t.me/joinchat/AAAAAEabcdef", "telegram", "moi_vao_nhom", True, "telethon"),
    ("https://t.me/c/1234567890/55", "telegram", "tin_nhan_rieng", True, "telethon"),
    ("https://www.facebook.com/groups/botfxvn", "facebook", "nhom", True, "thu_cong"),
    ("https://www.facebook.com/share/p/1AbCdE/", "facebook", "bai_dang", True, "thu_cong"),
    ("https://www.facebook.com/SomePublicPage", "facebook", "trang", False, "thu_cong"),
    ("https://zalo.me/g/abcxyz", "zalo", "nhom", True, "thu_cong"),
    ("https://discord.gg/abc123", "discord", "moi_vao_may_chu", True, "thu_cong"),
    ("https://chat.whatsapp.com/Ab12Cd34", "whatsapp", "moi_vao_nhom_hoac_so", True, "thu_cong"),
    ("https://drive.google.com/file/d/1AbC/view?usp=sharing", "kho_tep", "kho_tep", True, "thu_cong"),
    ("https://mega.nz/file/abc#key", "kho_tep", "kho_tep", True, "thu_cong"),
    ("https://youtu.be/dQw4w9WgXcQ", "youtube", "video", False, "khong_ho_tro"),
    ("https://bit.ly/3abcDEF", "rut_gon", "chuyen_huong", False, "giai_ma"),
    ("https://www.forexfactory.com/thread/123-grid-ea", "dien_dan", "dien_dan", False, "cdp"),
    ("https://example.org/trang-bat-ky", "khac", "khac", False, "http"),
]


class TestPhanLoai:
    @pytest.mark.parametrize("url,nen,loai,rieng,cach", BANG)
    def test_bang(self, url, nen, loai, rieng, cach):
        m = LN.phan_loai(url)
        assert (m["nen_tang"], m["loai"], m["rieng"], m["cach_lay"]) == (nen, loai, rieng, cach), m

    def test_id_va_tab_cua_tin_hieu(self):
        m = LN.phan_loai("https://www.mql5.com/vi/signals/2196457?source=x#!tab=history")
        assert m["id"] == "2196457" and m["tab"] == "history"
        assert LN.phan_loai("https://github.com/o/r")["id"] == "o/r"

    def test_rieng_khi_co_credential_trong_link(self):
        a = LN.phan_loai("https://example.org/x?token=abc123")
        b = LN.phan_loai("https://user:pw@example.org/x")
        c = LN.phan_loai("https://example.org/x?page=2&sort=asc")             # chieu im lang: tham so thuong KHONG rieng
        assert a["rieng"] and "token" in a["ly_do_rieng"] and b["rieng"] and not c["rieng"]

    def test_dia_chi_noi_bo_khong_bao_gio_duoc_tham_do(self):
        for u in ("http://localhost:8000/x", "http://127.0.0.1/a", "http://192.168.1.10/admin", "http://[::1]/x",
                  "http://8.8.8.8/x", "http://may-nha.local/x"):
            m = LN.phan_loai(u)
            assert m["nen_tang"] == "noi_bo" and m["rieng"] and m["cach_lay"] == "khong_ho_tro", u

    def test_tep_thuc_thi_bi_danh_dau_nguy_hiem_va_khong_tu_tai(self):
        m = LN.phan_loai("https://files.example.org/dl/robot.zip")
        assert m["loai"] == "tep_truc_tiep" and m["nguy_hiem"] and m["cach_lay"] == "thu_cong"
        m2 = LN.phan_loai("https://files.example.org/dl/report.html")
        assert m2["loai"] == "tep_truc_tiep" and not m2.get("nguy_hiem")

    def test_can_gi(self):
        assert LN.phan_loai(MOI_NHOM)["can"] == ["telegram_dang_nhap_o_may_nha"]       # nhom kin: http khong thay
        assert LN.phan_loai("https://t.me/GoldReaperEA")["can"] == ["telegram_dang_nhap_o_may_nha", "mang"]
        assert "chrome_cdp_da_dang_nhap" in LN.phan_loai("https://www.myfxbook.com/portfolio/a/1")["can"]

    def test_ma_on_dinh(self):
        a = LN.phan_loai("https://www.mql5.com/en/signals/5")
        assert a["ma"] == LN.phan_loai("https://mql5.com/vi/signals/5?utm_medium=z")["ma"] and len(a["ma"]) == 10


class TestLoaiTep:
    @pytest.mark.parametrize("ten,loai", [
        ("ReportHistory-123456.html", "bao_cao"), ("statement.csv", "bao_cao"), ("EA_Grid.mq5", "ea_nguon"),
        ("EA_Grid.ex5", "ea_bien_dich"), ("EURUSD_best.set", "tham_so"), ("mix.zip", "nen"), ("anh.PNG", "anh"),
        ("bangtinh.xlsx", "bao_cao_co_the"), ("loi.bin", "khac")])
    def test_loai(self, ten, loai):
        assert LN.loai_tep(ten) == loai

    def test_khong_tai_tep_thuc_thi_hay_nen_hay_qua_lon(self):
        assert LN.tai_duoc("a.exe")[0] is False and LN.tai_duoc("robot.zip")[0] is False and LN.tai_duoc("x.dll")[0] is False
        assert LN.tai_duoc("ea.ex5") == (True, "") and LN.tai_duoc("report.html")[0] is True       # chieu im lang
        assert LN.tai_duoc("report.html", kich_thuoc=9_000_000)[0] is False
        assert LN.tai_duoc("hinh.png")[0] is False


# ------------------------------------------------------------------ link_rieng.txt
class TestLinkRieng:
    def test_doc_tin_nhan_dan_nguyen_van(self, tmp_path):
        f = tmp_path / "ln.txt"
        f.write_text("# ghi chu bo qua https://mql5.com/signals/999\n"
                     "Gold Reaper EA 300%%/nam - https://www.mql5.com/en/signals/2204998\n"
                     "nhom VIP: %s\n"
                     "lai lan nua https://mql5.com/vi/signals/2204998?utm_source=z\n" % MOI_NHOM, encoding="utf-8")
        muc = LN.doc_link_rieng(f)
        assert [m["nen_tang"] for m in muc] == ["mql5", "telegram"]               # dong # bo qua, trung khu
        assert muc[0]["nhan"].startswith("Gold Reaper EA") and muc[1]["rieng"]

    def test_khong_co_tep_thi_rong(self):
        assert LN.doc_link_rieng() == []

    def test_them_link_khong_trung(self, tmp_path):
        f = tmp_path / "x" / "lr.txt"
        moi = LN.them_link_rieng("xem https://www.mql5.com/en/signals/5 va t.me/kenhabc", duong=f)
        assert len(moi) == 2
        assert LN.them_link_rieng("https://mql5.com/vi/signals/5 // them t.me/kenhabc", duong=f) == []
        assert len(f.read_text(encoding="utf-8").splitlines()) == 2

    def test_them_vao_tep_mac_dinh(self, tmp_path):
        LN.them_link_rieng("https://github.com/o/r")
        assert len(LN.doc_link_rieng()) == 1


# ------------------------------------------------------------------ TRICH TU VAN BAN
TIN_NHAN = """Chao ca nha, bot nay chay luoi DCA martingale, khong SL, 14 thang ra tien:
Signal: https://www.mql5.com/en/signals/2196457 va https://www.mql5.com/en/signals/884935
Kenh: https://t.me/GoldReaperEA (telegram: @vip_bot_fx) nhom kin %s
Account xem (investor): Login: 12345678  Investor password: %s  Server: XMGlobal-MT5 7
File: ReportHistory-12345678.html, EA_Grid.set, robot.zip
Lien he test@example.com""" % (MOI_NHOM, MAT_KHAU)


class TestTrichVanBan:
    def test_manh_dung_duoc(self):
        kq = LN.trich_tu_van_ban(TIN_NHAN)
        assert kq["mql5_tin_hieu"] == [884935, 2196457]
        assert kq["telegram_cong_khai"] == ["goldreaperea"] and "vip_bot_fx" in kq["telegram_goi_y"]
        assert {t["loai"] for t in kq["tep"]} >= {"bao_cao", "tham_so", "nen"}
        assert kq["tu_khoa"]["dca"] >= 1 and kq["tu_khoa"]["martingale"] == 1 and kq["tu_khoa"]["khong_sl"] == 1

    def test_tai_khoan_xem_khong_lo_mat_khau_hay_login(self):
        kq = LN.trich_tu_van_ban(TIN_NHAN)
        assert len(kq["tai_khoan_xem"]) == 1
        a = kq["tai_khoan_xem"][0]
        assert a["server"].startswith("XMGlobal-MT5") and a["co_mat_khau"] is True and len(a["ma"]) == 8
        dump = json.dumps(kq, ensure_ascii=False)
        assert MAT_KHAU not in dump and "12345678" not in dump and "tai_khoan_xem_tho" not in kq

    def test_giu_bi_mat_chi_khi_duoc_yeu_cau(self):
        kq = LN.trich_tu_van_ban(TIN_NHAN, giu_bi_mat=True)
        assert kq["tai_khoan_xem_tho"][0]["mat_khau"] == MAT_KHAU and kq["tai_khoan_xem_tho"][0]["login"] == 12345678

    def test_van_ban_tro_trai_khong_co_gi(self):
        kq = LN.trich_tu_van_ban("hom nay troi dep, khong co link, khong co tai khoan")
        assert kq["link"] == [] and kq["tai_khoan_xem"] == [] and kq["tu_khoa"] == {} and kq["mql5_tin_hieu"] == []

    def test_telegram_goi_y_chi_khi_van_ban_nhac_telegram(self):
        assert LN.trich_tu_van_ban("lien he @nguoi_dung_abc nhe")["telegram_goi_y"] == []        # co the la mang khac
        assert LN.trich_tu_van_ban("telegram @nguoi_dung_abc")["telegram_goi_y"] == ["nguoi_dung_abc"]


# ------------------------------------------------------------------ KE HOACH
def _muc():
    return [LN.phan_loai(u, nhan=n) for u, n in [
        ("https://www.facebook.com/groups/botfxvn", "nhom FB bot vang"),
        (MOI_NHOM, "VIP Gold"),
        ("https://www.myfxbook.com/members/u/sys/1234567", ""),
        ("https://www.mql5.com/en/signals/2196457", "X117"),
        ("https://github.com/o/ea-grid", ""),
        ("https://drive.google.com/file/d/SECRETFILE123/view", "ban EA"),
        ("https://www.mql5.com/en/code/9876", ""),
    ]]


class TestKeHoach:
    def test_thu_tu_cach_lay_roi_nguon_co_lenh_that(self):
        kh = LN.ke_hoach(_muc())
        cach = [e["cach_lay"] for e in kh]
        assert cach == sorted(cach, key=lambda c: LN._THU_TU_CACH[c])             # http -> cdp -> telethon -> thu cong
        http = [e for e in kh if e["cach_lay"] == "http"]
        assert http[0]["loai"] == "tin_hieu"                                      # co lenh that len dau, truoc ma nguon
        assert all(e["buoc"] for e in kh) and kh[0]["nhip_giay"] == 8

    def test_ban_an_toan_khong_lo_link_rieng_hay_nhan(self):
        kh = LN.ke_hoach(_muc())
        dump = json.dumps(LN.bao_cao_an_toan(kh), ensure_ascii=False)
        for bi_mat in ("Zq9XkLmN0pQrStUv", "SECRETFILE123", "botfxvn", "nhom FB bot vang", "VIP Gold", "ban EA"):
            assert bi_mat not in dump, bi_mat
        assert "mql5.com/signals/2196457" in dump                                 # chieu im lang: link CONG KHAI van co url
        assert LN.bao_cao_an_toan(kh)["rieng"] == 3

    def test_ghi_bao_cao_khong_lo_va_trong_gioi_han(self, tmp_path):
        muc = _muc() + [LN.phan_loai("https://www.mql5.com/en/signals/%d" % (100000 + i)) for i in range(1500)]
        LN.ghi_bao_cao(LN.ke_hoach(muc))
        j, md = (tmp_path / "reports" / "kh.json"), (tmp_path / "reports" / "kh.md")
        assert len(j.read_text(encoding="utf-8")) <= 38_000 and len(md.read_text(encoding="utf-8")) <= 38_000
        assert json.loads(j.read_text(encoding="utf-8"))["bi_cat"] > 0
        for f in (j, md):
            t = f.read_text(encoding="utf-8")
            assert "Zq9XkLmN0pQrStUv" not in t and "SECRETFILE123" not in t

    def test_bao_cao_van_ban_noi_ro_can_gi(self):
        vb = LN.bao_cao_van_ban(LN.ke_hoach(_muc()))
        assert "7 link" in vb and "3 link RIENG TU" in vb
        assert "Telegram" in vb and "Chrome" in vb and "tha_vao" in vb
        assert all(ord(c) < 128 for c in vb)                                      # ASCII (tai lieu repo)

    def test_chua_co_link_thi_chi_cach_dan(self):
        vb = LN.bao_cao_van_ban([])
        assert "link_rieng.txt" in vb and "GitHub" in vb


# ------------------------------------------------------------------ NHIP
class TestNhip:
    def test_cung_ten_mien_phai_cho_ten_mien_khac_thi_khong(self):
        dh = DongHo()
        n = LN.Nhip(dong_ho=dh, ngu=dh.ngu)
        assert n.doi("www.mql5.com") == 0.0                                       # lan dau khong cho
        assert n.doi("mql5.com") == 8.0                                           # cung ten mien goc
        assert n.doi("www.myfxbook.com") == 0.0                                   # chieu im lang: ten mien khac khong bi cham
        dh.t += 100
        assert n.doi("mql5.com") == 0.0                                           # da qua nhip
        assert dh.da_ngu == [8.0]

    def test_nhip_mac_dinh_theo_ten_mien(self):
        assert LN.nhip_cho("www.myfxbook.com") == 10 and LN.nhip_cho("gist.github.com") == 2
        assert LN.nhip_cho("example.org") == LN.NHIP_MIEN["*"]

    def test_crawl_delay_lon_hon_nhip_thi_theo_robots(self):
        dh = DongHo()
        n = LN.Nhip(dong_ho=dh, ngu=dh.ngu)
        n.doi("github.com")
        assert n.doi("github.com", toi_thieu=20) == 20.0
        n.doi("github.com")
        assert dh.da_ngu[-1] == 2.0                                               # robots khong con thi quay lai nhip mac dinh

    def test_het_tran_moi_luot_thi_dung_ten_mien_do(self):
        dh = DongHo()
        n = LN.Nhip(dong_ho=dh, ngu=dh.ngu, tran_luot=3)
        for _ in range(3):
            n.doi("t.me")
        with pytest.raises(LN.HetNhip):
            n.doi("t.me")
        n.doi("mql5.com")                                                          # ten mien khac van chay


# ------------------------------------------------------------------ ROBOTS
ROBOTS = "User-agent: *\nDisallow: /private/\nDisallow: /en/signals/*/trade\nCrawl-delay: 15\n"


def _lay_robots(status, text="", dem=None):
    def lay(url):
        if dem is not None:
            dem.append(url)
        return status, text, ""
    return lay


class TestRobots:
    def test_theo_tep(self):
        r = LN.Robots(_lay_robots(200, ROBOTS))
        assert r.cho_phep("https://x.org/public/page") == (True, "")
        ok, ly = r.cho_phep("https://x.org/private/a")
        assert not ok and "robots" in ly
        assert r.crawl_delay("https://x.org/a") == 15.0

    def test_khong_co_robots_thi_duoc(self):
        r = LN.Robots(_lay_robots(404))
        assert r.cho_phep("https://x.org/private/a") == (True, "") and r.crawl_delay("https://x.org/") is None

    def test_loi_may_chu_hay_mang_thi_khong_cao_luot_nay(self):
        assert LN.Robots(_lay_robots(503)).cho_phep("https://x.org/a")[0] is False
        r = LN.Robots(lambda u: (None, "", "ConnectionError: x"))
        ok, ly = r.cho_phep("https://x.org/a")
        assert not ok and "robots.txt" in ly

    def test_nho_theo_ten_mien_va_het_han(self):
        dem, t = [], [0.0]
        r = LN.Robots(_lay_robots(200, ROBOTS, dem), ttl=100, dong_ho=lambda: t[0])
        r.cho_phep("https://x.org/a")
        r.cho_phep("https://x.org/b")
        r.cho_phep("https://y.org/b")
        assert dem == ["https://x.org/robots.txt", "https://y.org/robots.txt"]
        t[0] = 101
        r.cho_phep("https://x.org/c")
        assert dem.count("https://x.org/robots.txt") == 2


# ------------------------------------------------------------------ LOI + LUI
class TestLoi:
    @pytest.mark.parametrize("status,text,loi,kq", [
        (200, "<html>binh thuong</html>", "", "OK"), (301, "", "", "OK"), (429, "", "", "CHAN_TAN_SUAT"),
        (403, "", "", "CHAN_CAM"), (401, "", "", "CHAN_CAM"), (404, "", "", "HET_TRANG"), (410, "", "", "HET_TRANG"),
        (503, "", "", "LOI_MAY_CHU"), (None, "", "Timeout", "LOI_MANG"), (200, "", "reset", "LOI_MANG"),
        (200, "<title>Just a moment...</title> cf-chl-bypass", "", "CHAN_CAM"),
        (200, "Please verify you are human (captcha)", "", "CHAN_CAM"),
    ])
    def test_phan_loai(self, status, text, loi, kq):
        assert LN.phan_loai_loi(status, text, loi) == kq

    def test_trang_binh_thuong_nhac_tu_captcha_o_cuoi_trang_khong_bi_chan(self):
        # chieu im lang: chi doc 6000 ky tu dau, bai viet dai nhac "captcha" o cuoi khong phai man chan
        assert LN.phan_loai_loi(200, "x" * 7000 + " captcha") == "OK"

    def test_lui_cap_so_nhan_co_tran(self):
        assert [LN.nghi_sau_loi("CHAN_TAN_SUAT", n) for n in (1, 2, 3, 4, 5, 6)] == [900, 1800, 3600, 7200, 14400, 21600]
        assert LN.nghi_sau_loi("CHAN_TAN_SUAT", 20) == 6 * 3600
        assert LN.nghi_sau_loi("LOI_MANG", 1) == 300 and LN.nghi_sau_loi("LOI_MANG", 30) == 2 * 3600
        assert LN.nghi_sau_loi("CHAN_CAM", 1) == LN.nghi_sau_loi("CHAN_CAM", 9) == 24 * 3600
        assert LN.nghi_sau_loi("OK", 1) == 0.0


# ------------------------------------------------------------------ TRANG THAI
class TestTrangThai:
    def test_chan_tan_suat_lam_ca_ten_mien_nghi(self, tmp_path):
        dh = DongHo(5000.0)
        tt = LN.TrangThai(tmp_path / "t.json", dong_ho=dh)
        a, b = LN.ma_link("https://mql5.com/signals/1"), LN.ma_link("https://mql5.com/signals/2")
        tt.ghi(a, "www.mql5.com", "CHAN_TAN_SUAT")
        ok, ly = tt.thu_duoc(b, "mql5.com")                                       # link KHAC cung ten mien cung phai doi
        assert not ok and "mql5.com" in ly
        assert tt.thu_duoc(b, "www.myfxbook.com")[0] is True                      # chieu im lang: ten mien khac van chay
        dh.t += 899
        assert not tt.thu_duoc(b, "mql5.com")[0]
        dh.t += 2
        assert tt.thu_duoc(b, "mql5.com")[0] is True

    def test_lien_tiep_chan_thi_nghi_dai_hon_va_thanh_cong_thi_xoa(self, tmp_path):
        dh = DongHo(0.0)
        tt = LN.TrangThai(tmp_path / "t.json", dong_ho=dh)
        tt.ghi("a1", "t.me", "CHAN_TAN_SUAT")
        assert tt.d["link"]["a1"]["thu_lai_sau"] == 900
        dh.t = 1000
        tt.ghi("a1", "t.me", "CHAN_TAN_SUAT")
        assert tt.d["link"]["a1"]["thu_lai_sau"] == 1000 + 1800 and tt.d["link"]["a1"]["so_loi"] == 2
        dh.t = 10_000
        tt.ghi("a1", "t.me", "OK")
        assert tt.d["link"]["a1"]["so_loi"] == 0 and tt.d["mien"]["t.me"]["so_loi_lien_tiep"] == 0
        assert tt.thu_duoc("a1", "t.me")[0] is True

    def test_chan_cam_nghi_24_gio_va_bao_ro(self, tmp_path):
        dh = DongHo(0.0)
        tt = LN.TrangThai(tmp_path / "t.json", dong_ho=dh)
        tt.ghi("x", "www.myfxbook.com", "CHAN_CAM")
        ok, ly = tt.thu_duoc("khac", "myfxbook.com")
        assert not ok and "CHAN_CAM" in ly
        dh.t = 24 * 3600 + 1
        assert tt.thu_duoc("khac", "myfxbook.com")[0] is True

    def test_het_trang_khong_lam_ten_mien_nghi(self, tmp_path):
        tt = LN.TrangThai(tmp_path / "t.json", dong_ho=DongHo(0.0))
        tt.ghi("x", "mql5.com", "HET_TRANG")
        assert tt.thu_duoc("y", "mql5.com")[0] is True                            # trang chet khong phai tin hieu chan
        assert not tt.thu_duoc("x", "mql5.com")[0]

    def test_tran_ngay(self, tmp_path):
        tt = LN.TrangThai(tmp_path / "t.json", dong_ho=DongHo(0.0))
        for _ in range(3):
            tt.tinh_yeu_cau("mql5.com")
        assert tt.so_hom_nay("www.mql5.com") == 3
        assert not tt.thu_duoc("z", "mql5.com", tran_ngay=3)[0]
        assert tt.thu_duoc("z", "mql5.com", tran_ngay=4)[0]
        tt.dh = DongHo(2 * 86400.0)                                                # sang ngay moi dem lai tu 0
        assert tt.so_hom_nay("mql5.com") == 0

    def test_ben_qua_lan_chay_va_file_hong_thi_bat_dau_lai(self, tmp_path):
        d = tmp_path / "t.json"
        LN.TrangThai(d, dong_ho=DongHo(1.0)).ghi("a", "t.me", "OK", so_ban_ghi=7)
        tt2 = LN.TrangThai(d, dong_ho=DongHo(2.0))
        assert tt2.trang_thai("a") == "OK" and tt2.d["link"]["a"]["so_ban_ghi"] == 7
        assert tt2.trang_thai("chua_co") == "CHUA_LAM"
        d.write_text("{hong", encoding="utf-8")
        assert LN.TrangThai(d).d == {"phien_ban": 1, "link": {}, "mien": {}}
        assert not list(tmp_path.glob("*.tmp"))                                    # ghi nguyen tu: khong de tep tam


# ------------------------------------------------------------------ TOM TAT CAU TRUC
HTML = """<!doctype html><html><head><title>Signal X117 | MQL5</title>
<meta name="description" content="Gold grid, contact test@example.com 0912345678"><meta property="og:type" content="website">
<meta name="csrf-token" content="SECRET-CSRF-VALUE"><script src="https://cdn.example.org/lib.js?v=123&key=SECRETKEY"></script>
<script type="application/json" id="__NEXT_DATA__">{"props": {"token": "SECRET-JSON-VALUE"}, "page": "/x", "buildId": "abc"}</script>
<script>var cfg = {tok: "SECRET-INLINE"}; $.get('/en/signals/2196457/history?page=1&session=SECRETSESS', function(d){});
fetch("/api/v2/trades?id=5&token=SECRETTOKEN2"); $.ajax({url: '/ajax/stats.php'});</script></head>
<body><h1>X117 EA</h1><h2>Trading history</h2>
<ul><li><a href="#!tab=overview" class="tab">Overview</a></li><li><a href="#!tab=history" class="tab active">History</a></li>
<li><a href="/en/users/ab">profile</a></li></ul>
<table><tr><th>Time</th><th>Type</th><th>Volume</th><th>Symbol</th><th>Price</th><th>Profit</th></tr>
<tr><td>2026.09.01 10:00</td><td>buy</td><td>0.10</td><td>AUDCAD</td><td>0.9051</td><td>12.5</td></tr>
<tr><td>2026.09.01 11:00</td><td>sell</td><td>0.20</td><td>AUDCAD</td><td>0.9060</td><td>-3.1</td></tr>
<tr><td>2026.09.01 12:00</td><td>buy</td><td>0.30</td><td>AUDCAD</td><td>0.9049</td><td>1.0</td></tr></table>
<form action="/en/search?q=SECRETQ" method="post"><input name="q" value="SECRET-FORM-VALUE"><input type="hidden" name="_csrf" value="SECRET-HIDDEN">
<button name="go">Go</button></form>
<a href="https://t.me/SignalChannelPub">tele</a> <a href="https://t.me/+HiddenInvite999">vip</a> <a href="https://github.com/o/r">code</a>
</body></html>"""


class TestTomTat:
    def test_cau_truc_chinh(self):
        kq = LN.tom_tat_cau_truc(HTML, url="https://www.mql5.com/en/signals/2196457?token=XYZ")
        assert kq["tieu_de"] == "Signal X117 | MQL5"
        assert [t["chu"] for t in kq["tab"]] == ["Overview", "History"]
        b = kq["bang"][0]
        assert b["tieu_de"] == ["Time", "Type", "Volume", "Symbol", "Price", "Profit"] and b["so_hang"] == 3 and len(b["mau"]) == 2
        assert {"cap": "h2", "chu": "Trading history"} in kq["muc"]
        dc = " ".join(kq["diem_cuoi"])
        assert "/en/signals/2196457/history?page=&session=" in dc and "/api/v2/trades?id=&token=" in dc and "/ajax/stats.php" in dc
        assert kq["form"][0]["duong"] == "/en/search?q=" and {"ten": "q", "loai": "text"} in kq["form"][0]["o"]
        assert kq["json_nhung"][0]["khoa"] == ["buildId", "page", "props"]
        assert kq["link_ra_theo_nen_tang"] == {"telegram": 1, "github": 1}       # link moi RIENG khong tinh vao bao cao

    def test_khong_lo_gia_tri_bi_mat(self):
        dump = json.dumps(LN.tom_tat_cau_truc(HTML, url="https://www.mql5.com/x?token=SECRETURL"), ensure_ascii=False)
        for bi_mat in ("SECRET-CSRF-VALUE", "SECRETKEY", "SECRET-JSON-VALUE", "SECRET-INLINE", "SECRETSESS", "SECRETTOKEN2",
                       "SECRETQ", "SECRET-FORM-VALUE", "SECRET-HIDDEN", "HiddenInvite999", "SECRETURL", "test@example.com",
                       "0912345678"):
            assert bi_mat not in dump, bi_mat

    def test_trang_trong_va_html_hong_khong_nem_loi(self):
        assert LN.tom_tat_cau_truc("")["bang"] == []
        kq = LN.tom_tat_cau_truc("<table><tr><td>a<h1><form><script>fetch('/api/x'", url="")
        assert isinstance(kq["tieu_de"], str)

    def test_gioi_han_kich_thuoc(self):
        nang = "<html><body>" + "".join("<h2>muc %d</h2><table><tr><th>a</th></tr><tr><td>%s</td></tr></table>" % (i, "x" * 50)
                                        for i in range(300)) + "".join("<a class='tab' href='/t%d'>t</a>" % i for i in range(200)) + "</body>"
        kq = LN.tom_tat_cau_truc(nang, toi_da=4000)
        assert len(json.dumps(kq, ensure_ascii=False)) <= 4000 + 800 and kq["da_cat"] is True
        assert len(LN.tom_tat_cau_truc(HTML)["bang"]) == 1 and LN.tom_tat_cau_truc(HTML)["da_cat"] is False


class TestChoThamDo:
    @pytest.mark.parametrize("url,ok", [
        ("https://www.mql5.com/en/signals/2196457", True), ("https://github.com/o/r", True), ("https://t.me/GoldReaperEA", True),
        ("http://www.mql5.com/en/signals/1", False),                              # khong https
        (MOI_NHOM, False), ("https://www.facebook.com/groups/x", False), ("https://drive.google.com/file/d/1/view", False),
        ("https://www.mql5.com/x?token=abc", False), ("https://user:pw@www.mql5.com/x", False),
        ("https://www.mql5.com:8443/x", False), ("https://127.0.0.1/x", False), ("https://evil.example.org/x", False),
        ("https://mql5.com.evil.org/x", False)])                                  # ten mien gia mao
    def test_bang(self, url, ok):
        assert LN.cho_tham_do(url)[0] is ok, LN.cho_tham_do(url)


# ============================================================== PHAN BO SYMBOL (bang Distribution cua trang tin hieu MQL5)
_DIST = [{"so_hang": 3, "tieu_de": ["Symbol", "", "Deals", "Sell", "Buy"], "mau": [["GOLD#", "1549", "", "", ""], ["USDCHF#", "2", "", "", ""]]},
         {"so_hang": 3, "tieu_de": ["Symbol", "", "Gross Profit, USD", "Loss, USD", "Profit, USD"],
          "mau": [["GOLD#", "9.8K", "", "", ""], ["USDCHF#", "24", "", "", ""]]},
         {"so_hang": 3, "tieu_de": ["Symbol", "", "Gross Profit, pips", "Loss, pips", "Profit, pips"],
          "mau": [["GOLD#", "410K", "", "", ""], ["USDCHF#", "134", "", "", ""]]}]          # y het trang that cua 2196457 (do o may nha 03/10)


class TestPhanBoSymbol:
    @pytest.mark.parametrize("tho,chuan", [
        ("GOLD#", "XAUUSD"), ("Gold", "XAUUSD"), ("GOLDm", "XAUUSD"), ("XAUUSDm", "XAUUSD"), ("XAUUSD.a", "XAUUSD"),
        ("SILVER", "XAGUSD"), ("EURUSD.pro", "EURUSD"), ("EURUSD_i", "EURUSD"), ("EURUSDm", "EURUSD"), ("AUDCAD+", "AUDCAD"),
        ("USDCHF#", "USDCHF"), ("US30m", "US30"), ("NAS100", "NAS100"), ("BTCUSD", "BTCUSD"), ("", "")])
    def test_chuan_symbol(self, tho, chuan):
        assert LN.chuan_symbol(tho) == chuan

    @pytest.mark.parametrize("t,v", [("1549", 1549.0), ("9.8K", 9800.0), ("410K", 410000.0), ("1,549", 1549.0), ("-3.4K", -3400.0),
                                     ("1.2M", 1.2e6), ("", None), ("abc", None), (None, None)])
    def test_so_ngan(self, t, v):
        assert LN._so_ngan(t) == v

    def test_con_vang_2196457_la_vang_khong_phai_usdchf(self):
        ps = LN.phan_bo_symbol(_DIST)
        assert ps["symbol_chinh"] == "XAUUSD" and ps["ty_le_lenh"] == 0.999
        assert ps["symbol"][0] == {"tho": "GOLD#", "chuan": "XAUUSD", "lenh": 1549, "usd": 9800.0, "pip": 410000.0}
        assert ps["symbol"][1]["chuan"] == "USDCHF" and ps["symbol"][1]["lenh"] == 2
        assert ps["day_du"] is False                                  # trang bao 3 hang, bang mau moi chi cho 2

    def test_hai_ten_san_cua_cung_mot_cap_duoc_gop(self):
        b = [{"so_hang": 3, "tieu_de": ["Symbol", "", "Deals"], "mau": [["EURUSD", "10", ""], ["EURUSDm", "15", ""], ["GBPUSD", "20", ""]]}]
        ps = LN.phan_bo_symbol(b)
        assert ps["symbol_chinh"] == "EURUSD" and ps["ty_le_lenh"] == round(25 / 45, 3) and ps["day_du"] is True

    @pytest.mark.parametrize("bang", [None, [], [{"so_hang": 2, "tieu_de": ["Time", "Type"], "mau": [["a", "1"]]}],
                                      [{"so_hang": 1, "tieu_de": ["Symbol", "", "Gross Profit, USD"], "mau": [["GOLD#", "9.8K"]]}],     # thieu bang so lenh
                                      [{"so_hang": 1, "tieu_de": ["Symbol", "", "Deals"], "mau": [["GOLD#", "n/a"]]}]])
    def test_khong_co_bang_symbol_thi_none(self, bang):
        assert LN.phan_bo_symbol(bang) is None

    def test_bang_symbol_lay_toi_10_hang_mau_bang_khac_chi_2(self):
        def bang(cot0):
            return "<table><tr><th>%s</th><th>n</th></tr>" % cot0 + "".join("<tr><td>S%d</td><td>%d</td></tr>" % (i, i) for i in range(1, 8)) + "</table>"
        d = LN.tom_tat_cau_truc("<html><body>%s%s</body></html>" % (bang("Symbol"), bang("Month")))
        assert len(d["bang"][0]["mau"]) == 7 and len(d["bang"][1]["mau"]) == 2 and d["bang"][0]["so_hang"] == 7
