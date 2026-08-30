# -*- coding: utf-8 -*-
"""doc_trinh_duyet.py - DOC BANG TRINH DUYET DANG MO (CDP) cho SEEKER.

Nguon co gia tri nhung requests/HTML tho khong hien duoc (403, render bang JS, can
dang nhap): Reddit, MQL5 Signals, Myfxbook, SSRN, CFTC/COT, X/TikTok/Facebook...
`_in.py` ghi ro: "Social chua chay that qua BROWSER DARWIN - can mo .browser_darwinex
+ CDP". May nay co profile da dang nhap (.browser_darwinex) va Playwright san.

Modun nay KHONG tu mo trinh duyet moi (de khoa profile / sinh OTP). No chi NOI
vao con Chrome da bat CDP san - neu khong co con nao, no bao `khong_mo_cdp`.
"""
from __future__ import annotations

import urllib.request

CDP_MAC_DINH = (9222, 9224)   # 9224 = darwin (.browser_darwinex), 9222 = thebrain2


def cdp_dang_chay(ports=CDP_MAC_DINH):
    """Tra ve cong CDP dau tien dang bat (127.0.0.1), hoac None."""
    for p in ports:
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % p,
                                        timeout=1.5) as r:
                if r.status == 200 and r.read():
                    return p
        except Exception:
            continue
    return None


def doc_gan(url, port=None, cho_ms=14000, toi_da_text=20000):
    """Doc mot trang qua con Chrome CDP dang mo. Tra {url,title,text,links,loi}."""
    from playwright.sync_api import sync_playwright
    port = port or cdp_dang_chay()
    if not port:
        return {"loi": "khong_mo_cdp"}
    kq = {"url": url, "title": "", "text": "", "links": [], "anchor": [], "loi": ""}
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp("http://127.0.0.1:%d" % port)
            ctx = b.contexts[0] if b.contexts else b.new_context()
            # MO TAB MOI moi lan va GIU LAI: cac nguon hien song song nhieu tab
            # tren man hinh trinh duyet, nguoi dung thay duoc ca qua trinh quet.
            pg = ctx.new_page()
            try:
                pg.bring_to_front()
            except Exception:
                pass
            try:
                pg.goto(url, timeout=min(cho_ms + 3000, 40000), wait_until="domcontentloaded")
                try:
                    pg.wait_for_load_state("networkidle", timeout=cho_ms)
                except Exception:
                    pass
                pg.wait_for_timeout(1200)
                kq["url"] = pg.url
                kq["title"] = (pg.title() or "")[:300]
                kq["text"] = (pg.inner_text("body") or "")[:toi_da_text]
                kq["links"] = list(dict.fromkeys(
                    pg.eval_on_selector_all("a", "els => els.map(e => e.href)")))[:120]
                kq["anchor"] = pg.eval_on_selector_all(
                    "a", "els => els.map(e => [e.innerText.trim(), e.href])")
            except Exception as e:
                kq["loi"] = "%s: %s" % (type(e).__name__, str(e)[:120])
            # KHONG `pg.close()`: giu tab lai de nguoi dung quan sat + tai su dung
    except Exception as e:
        kq["loi"] = "%s: %s" % (type(e).__name__, str(e)[:120])
    return kq


def lot_hang_het(url, port=None):
    """Doc trang lien ket (chau ngay), lay tu khoa/nganh khong le."""


if __name__ == "__main__":
    import sys
    print("cdp dang chay:", cdp_dang_chay())
    if len(sys.argv) > 1:
        k = doc_gan(sys.argv[1])
        print({kk: (str(v)[:200] if isinstance(v, str) else len(v)) for kk, v in k.items()})