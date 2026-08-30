# -*- coding: utf-8 -*-
"""tai_khoan_nen_tang.py - MOT CHO BIET he dang co tai khoan nao, thieu cai gi.

VI SAO CO FILE NAY (30/08/2026). Ca ngay hom nay lap lai mot canh: mot duong
thu thap khong chay, va sau vai vong do dac moi lo ra nguyen nhan la **chua
dang nhap** — chu khong phai loi ma.

  - X thu ve 3 bai thay vi 65      -> hoa ra la loi bo loc, X DA dang nhap
  - TradingView follow 8/8 "thanh cong" -> that ra 0/8, vi CHUA dang nhap
  - reddit va tiktok doc duoc it   -> chua dang nhap

Lan cuoi toi kiem dang nhap thu cong cho sau nen tang va **bo sot dung
tradingview** - dung cai dang can. Mot danh sach trong dau thi lan nao cung sot
mot cai; nen no phai nam trong ma va chay duoc bang mot lenh.

HAI LOAI NEN TANG, va chung doi hai cach khac han nhau:

  `tu_dong`      Nha cung cap DU LIEU (AlphaVantage, TwelveData, CoinGecko...).
                 Ho MUON nguoi ta dang ky lay key, khong chan bot. Dang ky tu
                 dong chay duoc — `tu_dang_ky.py` da lam that, va OTP doc tu
                 Gmail bang `doc_otp_gmail.py`.

  `mot_lan_tay`  Nen tang nguoi dung (TradingView, X, Reddit, Discord, sàn).
                 Chan bot bang CAPTCHA, va dieu khoan cua ho CAM dang ky tu
                 dong. Ep lam thi tai khoan bi gan co hoac khoa — te hon la
                 khong co. San thi con them xac minh danh tinh.

                 Duong chay duoc: MOT lan thao tac tay ~30 giay cho MOI nen
                 tang, DUY NHAT mot lan. Sau do phien dang nhap nam trong ho so
                 `lab/.browser_darwinex` va moi thu ve sau tu dong. Do chinh la
                 co che dang cho du an 101 Pine script va Reddit hom nay.

File nay khong dang ky ho ai ca. No tra loi mot cau: **con thieu nhung gi, va
phai lam gi tiep.**

Chay:  b tai-khoan          xem trang thai moi nen tang
       b tai-khoan --mo x   mo trang dang nhap cua mot nen tang
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

EMAIL_CAU_HINH = LAB / "config" / "email_cong_tac.json"

#: Nen tang he can, kem CACH lay tai khoan va CACH biet la da co.
#:
#: `kiem`  : trang mo ra de doc trang thai dang nhap.
#:
#:           PHAI la trang DOI DANG NHAP, khong phai trang cong khai. Da nham
#:           that 30/08: ban dau dat `kiem` cua tradingview la trang HO SO
#:           CONG KHAI cua mot tac gia - trang do doc duoc ca khi chua dang
#:           nhap, nen phep kiem bao "DA DANG NHAP" trong khi that ra chua, va
#:           dung cai do da lam 8 lenh follow im lang that bai.
#:           `tradingview.com/u/` (ho so CUA MINH) thi chuyen thang sang
#:           `/accounts/signin/` khi chua dang nhap - do moi la tin hieu that.
#: `dau_hieu_chua`: cum chu chi xuat hien khi CHUA dang nhap
#: `dang_ky`: trang tao tai khoan (de mo san cho nguoi dung)
#: `vi_sao`: no mo khoa cai gi — de biet co dang bo cong ra lam khong
NEN_TANG = {
    "tradingview": {
        "loai": "mot_lan_tay",
        "kiem": "https://www.tradingview.com/u/",
        "dang_ky": "https://www.tradingview.com/pricing/?source=header_account",
        "dau_hieu_chua": r"\bsign in\b|\blog in\b",
        "vi_sao": "101 Pine Script da thu duoc; dang nhap them thi FOLLOW duoc "
                  "tac gia va doc duoc script rieng tu",
    },
    "x": {
        "loai": "mot_lan_tay", "kiem": "https://x.com/home",
        "dang_ky": "https://x.com/i/flow/signup",
        "dau_hieu_chua": r"\bsign in\b|\blog in\b|create your account",
        "vi_sao": "41 bai; theo tac gia thi lay duoc dong bai cua ho",
    },
    "reddit": {
        "loai": "mot_lan_tay", "kiem": "https://www.reddit.com/settings",
        "dang_ky": "https://www.reddit.com/register/",
        "dau_hieu_chua": r"\blog in\b|\bsign up\b",
        "vi_sao": "169 bai doc an danh duoc; dang nhap thi join duoc r/quant, "
                  "r/algotrading, r/options va doc duoc bai chi cho thanh vien",
    },
    "youtube": {
        "loai": "mot_lan_tay", "kiem": "https://www.youtube.com/feed/subscriptions",
        "dang_ky": "https://accounts.google.com/signup",
        "dau_hieu_chua": r"\bsign in\b|\bdang nhap\b",
        "vi_sao": "62 video, 25 da co phu de; dang nhap thi subscribe duoc kenh",
    },
    "facebook": {
        "loai": "mot_lan_tay", "kiem": "https://www.facebook.com/me",
        "dang_ky": "https://www.facebook.com/r.php",
        "dau_hieu_chua": r"\blog in\b|\bdang nhap\b",
        "vi_sao": "10 bai — trang tim kiem gan nhu khong tra link; nhom rieng "
                  "moi la cho co noi dung",
    },
    "tiktok": {
        "loai": "mot_lan_tay", "kiem": "https://www.tiktok.com/following",
        "dang_ky": "https://www.tiktok.com/signup",
        "dau_hieu_chua": r"\blog in\b|\bsign up\b",
        "vi_sao": "78 clip; nhung TikTok khong co phu de cong khai nen phai qua "
                  "tieng (yt-dlp + Whisper) moi doc duoc",
    },
    "mql5": {
        "loai": "mot_lan_tay", "kiem": "https://www.mql5.com/en/users",
        "dang_ky": "https://www.mql5.com/en/auth_register",
        "dau_hieu_chua": r"\blog in\b|\bsign in\b",
        "vi_sao": "185 file .mq5 va 30 tin hieu; dang nhap thi tai duoc ma nguon "
                  "day du va xem duoc lich su tin hieu",
    },
}


def cau_hinh_email() -> dict:
    try:
        return json.loads(EMAIL_CAU_HINH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _doc_trang(pg, url: str, cho_ms: int = 4000) -> str:
    pg.goto(url, timeout=30000, wait_until="domcontentloaded")
    pg.wait_for_timeout(cho_ms)
    return (pg.inner_text("body") or "")


def kiem_mot(pg, ten: str) -> dict:
    """Mot nen tang: da dang nhap chua? Tra `da_dang_nhap=None` khi khong biet."""
    c = NEN_TANG[ten]
    try:
        van = _doc_trang(pg, c["kiem"])
    except Exception as e:
        return {"ten": ten, "da_dang_nhap": None,
                "loi": f"{type(e).__name__}: {str(e)[:60]}"}
    url = pg.url.lower()
    chuyen_dang_nhap = any(k in url for k in ("login", "signin", "auth", "/i/flow"))
    thay_dau_hieu = bool(re.search(c["dau_hieu_chua"], van[:2500], re.I))
    if chuyen_dang_nhap:
        return {"ten": ten, "da_dang_nhap": False, "ly_do": "bi chuyen sang trang dang nhap"}
    if thay_dau_hieu and len(van) < 4000:
        return {"ten": ten, "da_dang_nhap": False, "ly_do": "trang co nut dang nhap"}
    if len(van) < 300:
        return {"ten": ten, "da_dang_nhap": None, "ly_do": "trang gan nhu rong - khong doc duoc"}
    return {"ten": ten, "da_dang_nhap": True, "so_ky_tu": len(van)}


def kiem_tat_ca(port: int = 9224) -> list[dict]:
    from playwright.sync_api import sync_playwright
    ra = []
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = b.contexts[0] if b.contexts else b.new_context()
        for ten in NEN_TANG:
            pg = ctx.new_page()
            try:
                ra.append(kiem_mot(pg, ten))
            finally:
                try:
                    pg.close()
                except Exception:
                    pass
    return ra


def mo_dang_ky(ten: str, port: int = 9224) -> dict:
    """Mo san trang tao tai khoan de nguoi dung lam MOT lan.

    Khong tu dien form, khong tu bam: nen tang nguoi dung chan bot va dieu khoan
    cua ho cam dang ky tu dong. Mo san trang + dua san email la het phan may lam
    duoc mot cach tu te.
    """
    if ten not in NEN_TANG:
        return {"loi": f"khong co nen tang '{ten}'"}
    from playwright.sync_api import sync_playwright
    em = cau_hinh_email()
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = b.contexts[0] if b.contexts else b.new_context()
        pg = ctx.new_page()
        pg.goto(NEN_TANG[ten]["dang_ky"], timeout=30000, wait_until="domcontentloaded")
        try:
            pg.bring_to_front()
        except Exception:
            pass
    return {"da_mo": NEN_TANG[ten]["dang_ky"], "email_dung": em.get("email", ""),
            "ghi_chu": "Chrome dang chay AN. Chay `python mo_chrome_cdp.py --hien` "
                       "de thay cua so ma thao tac."}


def bao_cao(port: int = 9224) -> int:
    print("=" * 74)
    print("TAI KHOAN NEN TANG")
    print("=" * 74)
    em = cau_hinh_email()
    print(f"email cong tac: {em.get('email') or '(chua khai)'}"
          f"   2FA: {em.get('da_2fa')}")
    print()
    try:
        ds = kiem_tat_ca(port)
    except Exception as e:
        print(f"khong ket noi duoc trinh duyet: {type(e).__name__}")
        print("chay `python mo_chrome_cdp.py` truoc.")
        return 1

    thieu = []
    for r in sorted(ds, key=lambda x: (x["da_dang_nhap"] is not False, x["ten"])):
        c = NEN_TANG[r["ten"]]
        if r["da_dang_nhap"] is True:
            dau = "DA DANG NHAP"
        elif r["da_dang_nhap"] is False:
            dau = "CHUA        "
            thieu.append(r["ten"])
        else:
            dau = "KHONG RO    "
        print(f"  [{dau}] {r['ten']:13s} {r.get('ly_do') or r.get('loi') or ''}")
        print(f"                   mo khoa: {c['vi_sao']}")

    if thieu:
        print("\n" + "-" * 74)
        print("CAN MOT LAN THAO TAC TAY (~30 giay moi cai, duy nhat mot lan):")
        for t in thieu:
            print(f"    {t:13s} {NEN_TANG[t]['dang_ky']}")
        print(f"\n  Dung email: {em.get('email')}")
        print("  Mo cua so:  python mo_chrome_cdp.py --hien")
        print("  Hoac:       b tai-khoan --mo <ten>")
        print("\n  Sau do phien nam trong ho so .browser_darwinex va moi thu ve"
              " sau tu dong.")
    return 0


if __name__ == "__main__":
    if "--mo" in sys.argv:
        i = sys.argv.index("--mo")
        print(json.dumps(mo_dang_ky(sys.argv[i + 1]), ensure_ascii=False, indent=1))
    else:
        raise SystemExit(bao_cao())
