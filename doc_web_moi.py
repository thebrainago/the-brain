# -*- coding: utf-8 -*-
r"""doc_web_moi.py - DOC WEB BEN: thu requests truoc, neu loi hay noi dung rong
(intentionally-nhom) thi thu Playwright headless (render JS). Tra ve van ban + nguon.
Kem kiem TRA NOI DUNG (marker) chu khong tin moi check status code.

Dung (python co playwright - AppData\Local\Python\bin\python.exe):
  python doc_web_moi.py <url> --can-chua "Weekly Discussion" "algotrading"
"""
import sys, re, json
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
_TAG = re.compile(r"<[^>]+>")


def _doc_requests(url, timeout=20):
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    t = _TAG.sub(" ", r.text)
    return re.sub(r"\s+", " ", t)


def _doc_playwright(url, timeout=30):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        try:
            ctx = b.new_context(user_agent=UA["User-Agent"],
                                viewport={"width": 1280, "height": 900})
            page = ctx.new_page()
            page.goto(url, timeout=timeout * 1000)
            page.wait_for_timeout(4000)
            return page.evaluate("document.body.innerText"), "playwright"
        finally:
            b.close()


def doc(url, can_chua=(), toi_thieu=300):
    """Tra (van_ban, nguon). Thu requests, roi playwright. Kiem mark can_chua."""
    # 1) requests
    try:
        t = _doc_requests(url)
        if len(t) >= toi_thieu and all(m in t for m in can_chua):
            return t, "requests"
    except Exception:
        pass
    # 2) playwright
    try:
        t, nguon = _doc_playwright(url)
        if len(t) >= toi_thieu and all(m in t for m in can_chua):
            return t, nguon
    except Exception as e:
        return None, f"loi_playwright:{type(e).__name__}"
    return None, "khong_du"

def doc_reddit(duong_dan="/r/algotrading"):
    """Doc 1 trang reddit (dung Playwright vi reddit chan requests)."""
    t, nguon = doc("https://www.reddit.com" + duong_dan,
                   can_chua=("reddit",), toi_thieu=200)
    return t, nguon

if __name__ == "__main__":
    url = sys.argv[1]
    cc = sys.argv[sys.argv.index("--can-chua") + 1].split(",") if "--can-chua" in sys.argv else []
    t, nguon = doc(url, can_chua=cc)
    print("NGUON:", nguon)
    print("LEN:", len(t) if t else 0)
    if t:
        print(t[:600])
