# -*- coding: utf-8 -*-
r"""doc_bang_trinh_duyet.py - Doc trang bang TRINH DUYET THAT (Playwright/Chromium)
de vuot qua cac trang can JS va cac trang can dang nhap (X/TikTok/Facebook/Reddit...).

Hai che do:
  - headless: khong can dang nhap, doc trang cong khai.
  - profile: dung user-data-dir (thu muc Chrome da dang nhap) -> doc duoc trang can login.

Chay (python co playwright: AppData\Local\Python\bin\python.exe):
  python doc_bang_trinh_duyet.py <url> [--profile <dir>] [--anh reports/a.png]
"""
import sys, time, pathlib, re

LAB = pathlib.Path(__file__).parent


def _strip(html):
    import html as h
    txt = h.unescape(re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S))
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def doc(url, user_data_dir=None, cho_ms=8000, max_text=4000):
    """Mo trang, cho tai, trich title + text + link, co the chup anh. Tra dict."""
    from playwright.sync_api import sync_playwright
    kq = {"url": url, "title": "", "text": "", "links": [], "anh": None, "loi": ""}
    with sync_playwright() as p:
        try:
            if user_data_dir:
                ctx = p.chromium.launch_persistent_context(
                    user_data_dir, headless=False,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
            else:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
            page.goto(url, timeout=cho_ms + 2000, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=cho_ms)
            except Exception:
                pass
            time.sleep(1.0)
            kq["title"] = page.title()
            body = page.content()
            kq["text"] = _strip(body)[:max_text]
            kq["links"] = list(dict.fromkeys(page.eval_on_selector_all(
                "a", "els => els.map(e => e.href)")))[:40]
            if "--anh" in sys.argv:
                i = sys.argv[sys.argv.index("--anh") + 1]
                page.screenshot(path=i, full_page=True)
                kq["anh"] = i
            kq["url"] = page.url
            if user_data_dir:
                ctx.close()
            else:
                browser.close()
        except Exception as e:
            kq["loi"] = f"{type(e).__name__}: {e}"
            try:
                if user_data_dir:
                    ctx.close()
                else:
                    browser.close()
            except Exception:
                pass
    return kq


def main():
    if len(sys.argv) < 2:
        print("Thieu url. Dung: python doc_bang_trinh_duyet.py <url> [--profile dir] [--anh path]")
        return
    url = sys.argv[1]
    user_data_dir = None
    if "--profile" in sys.argv:
        user_data_dir = sys.argv[sys.argv.index("--profile") + 1]
    kq = doc(url, user_data_dir=user_data_dir)
    print("URL:", kq["url"])
    print("TITLE:", kq["title"])
    print("LOI:", kq["loi"] or "khong")
    print("ANH:", kq["anh"] or "khong")
    print("TEXT:", kq["text"][:400])
    print("LINKS:", len(kq["links"]))


if __name__ == "__main__":
    main()
