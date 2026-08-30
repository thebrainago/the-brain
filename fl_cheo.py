# -*- coding: utf-8 -*-
r"""fl_cheo.py - FOLLOW CHEO (cross-follow): tu 1 nguon / tai khoan chat luong,
trich cac link sang nen tang khac cua ho (YouTube/Telegram/GitHub/Instagram/
TradingView/Discord/Patreon/Substack...) roi follow/join tung cai (kiem soat spam).

Chay:
  python fl_cheo.py --trich https://x.com/<tk>   : chi trich lien ket cheo
  python fl_cheo.py --fl-cheo https://x.com/<tk> : trich + follow/join cac lien ket
"""
import sys, time, random, json, pathlib, re
from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"
LAB = pathlib.Path(__file__).parent
import tu_follow_join as tf
import requests as _req

SHORT = ("t.co", "bit.ly", "tinyurl", "rb.gy")

NEN_TANG = {
    "x.com": "X", "twitter.com": "X",
    "youtube.com": "YouTube", "youtu.be": "YouTube",
    "t.me": "Telegram", "telegram.org": "Telegram", "web.telegram.org": "Telegram",
    "github.com": "GitHub", "gist.github.com": "GitHub",
    "instagram.com": "Instagram",
    "tradingview.com": "TradingView", "tvc.com": "TradingView",
    "discord": "Discord", "discord.gg": "Discord",
    "facebook.com": "Facebook", "fb.com": "Facebook",
    "linkedin.com": "LinkedIn",
    "patreon.com": "Patreon", "substack.com": "Substack", "medium.com": "Medium",
    "tiktok.com": "TikTok", "twitch.tv": "Twitch", "reddit.com": "Reddit",
    "pinterest.com": "Pinterest", "trendspider.com": "TradingPlatform",
    "blog.": "Blog",
}


def _phan_tich(link):
    for k, ten in NEN_TANG.items():
        if k in link:
            return ten, link
    return None, link

def _giai_redirect(link):
    """Giai link rut gon (t.co, bit.ly...) ve URL that."""
    if any(sh in link for sh in SHORT):
        try:
            r = _req.get(link, allow_redirects=True, timeout=20,
                         headers={"User-Agent": "Mozilla/5.0"})
            if r.url and r.url != link:
                return r.url
        except Exception:
            pass
    return link

def trich_lien_ket_cheo(profile_url):
    p = sync_playwright().start()
    b = p.chromium.connect_over_cdp(CDP)
    try:
        pg = b.contexts[0].pages[0]
        pg.bring_to_front()
        pg.goto(profile_url, timeout=30000, wait_until="domcontentloaded")
        pg.wait_for_timeout(5000)
        links = set()
        for el in pg.query_selector_all("a[href]"):
            try:
                href = el.get_attribute("href") or ""
            except Exception:
                continue
            if href.startswith("http") and not href.startswith(("https://x.com", "https://twitter.com")):
                links.add(href)
        # trong bio X, link co the nam trong span href
        kq = []
        NHIEU = ("support.", "help.", "business.", "status.", "/about", "/terms",
                "/privacy", "/policy", "help/", "support/")
        for l in links:
            l = _giai_redirect(l)
            if any(n in l.split("//")[-1].lower() for n in NHIEU):
                continue
            ten, _ = _phan_tich(l)
            if ten:
                kq.append({"nen": ten, "url": l})
        # dedupe theo nen
        thay = {}
        for x in kq:
            thay.setdefault(x["nen"], x["url"])
        return [{"nen": n, "url": u} for n, u in thay.items()]
    finally:
        b.close(); p.stop()

def fl_cheo(profile_url):
    links = trich_lien_ket_cheo(profile_url)
    print(f"=== FOLLOW CHEO tu {profile_url} ===")
    print(f"Truc lien ket cheo ({len(links)}):")
    lich = []
    for x in links:
        print(f"  - {x['nen']}: {x['url'][:70]}")
        # xac dinh handle cho nen tang co the follow
        h = tf.theo_doi_x  # placeholder - mo rong theo nen tang
        lich.append(x)
    return lich

if __name__ == "__main__":
    if "--trich" in sys.argv:
        print(json.dumps(trich_lien_ket_cheo(sys.argv[sys.argv.index("--trich")+1]), ensure_ascii=False, indent=2))
    elif "--fl-cheo" in sys.argv:
        fl_cheo(sys.argv[sys.argv.index("--fl-cheo")+1])
