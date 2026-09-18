# -*- coding: utf-8 -*-
"""QUET RONG - thu thap nguon cong khai (khong can tai khoan) cho THE BRAIN.

Chay:  python quet_rong.py                -> quet tat ca nguon
       python quet_rong.py --nguon arxiv github reddit
       python quet_rong.py --nguon youtube --so 5

Nguon: arXiv (API cong khai) · GitHub (API cong khai 60 req/h) · HuggingFace (API cong khai)
       Reddit (.json cong khai) · RSS (danh sach trong nguon_config.json) ·
       Darwinex (API cong khai) · Myfxbook (trang cong khai) · YouTube (can api_key, tu chon)

Chi dung thu vien chuan (urllib/xml) - khong can pandas. Ket qua ghi vao
reports/nguon_<ngay>.jsonl + reports/NGUON_QUET_RONG.md. Luon ton trong
may chu: timeout ngan, ngu nho giua cac request, bat loi tung nguon.
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
CONFIG = HERE / "nguon_config.json"
REPORTS = HERE / "reports"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TheBrainResearch/0.1"}

MAU_QUET = {
    "quet_rong": {
        "tu_khoa_arxiv": ["momentum", "mean reversion", "volatility", "machine learning trading",
                          "market microstructure", "technical analysis", "time series forecasting"],
        "tu_khoa_github": ["pine script strategy", "backtest trading", "quant strategy",
                           "forex ea mql5", "algorithmic trading"],
        "reddit_subs": ["algotrading", "quant", "Forex", "Trading"],
        "rss": [
            "https://www.investopedia.com/feedbuilder/index/getfeed?feedName=rss_quant",
            "https://feeds.feedburner.com/Quantocracy",
            "https://ssrn.com/feeds/top-downloads.cfm?fps=14787980",
        ],
        "darwinex": {"max_darwin": 20, "loai": "public"},
        "myfxbook": {"max_trang": 3, "loai": "public"},
        "youtube": {"tu_khoa": ["trading strategy backtest", "algorithmic trading"]},
    }
}


def _cfg():
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps(MAU_QUET, ensure_ascii=False, indent=2), encoding="utf-8")
    d = json.loads(CONFIG.read_text(encoding="utf-8"))
    d.setdefault("quet_rong", MAU_QUET["quet_rong"])
    CONFIG.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return d["quet_rong"]


def _get(url, timeout=12, headers=None):
    yc = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(yc, timeout=timeout) as r:
        return r.read()


def _ngu(n=1.0):
    time.sleep(n)


def _ghi(ra, nguon, khoa, ten, tac_gia="", ngay="", tom_tat="", link="", loai="", them=None):
    ra.append({"nguon": nguon, "khoa": khoa, "ten": ten[:300], "tac_gia": tac_gia[:100],
               "ngay": ngay, "tom_tat": tom_tat[:600], "link": link, "loai": loai,
               "them": them or {}, "luc": datetime.now(timezone.utc).isoformat()})


# ---------------------------------------------------------------- nguon
def quet_arxiv(q, ra, so=8):
    dem = 0
    for tk in q["tu_khoa_arxiv"][:6]:
        url = ("http://export.arxiv.org/api/query?search_query=" +
               urllib.parse.quote(f'all:"{tk}" AND cat:q-fin.PM') +
               f"&start=0&max_results={so}&sortBy=submittedDate&sortOrder=descending")
        try:
            x = _get(url)
        except Exception as e:
            print(f"  [LOI arxiv] {tk}: {str(e)[:60]}"); continue
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(x)
        for e in root.findall("a:entry", ns):
            t = e.find("a:title", ns).text.replace("\n", " ").strip()
            s = (e.find("a:summary", ns).text or "").replace("\n", " ").strip()
            d = (e.find("a:published", ns).text or "")[:10]
            a = ", ".join(x.find("a:name", ns).text for x in e.findall("a:author", ns)[:3])
            lk = e.find("a:id", ns).text
            _ghi(ra, "arXiv", tk, t, a, d, s, lk, "bai_bao")
            dem += 1
        _ngu(3)
    print(f"  arXiv: {dem} bai")


def quet_github(q, ra, so=8):
    dem = 0
    for tk in q["tu_khoa_github"][:4]:
        qq = urllib.parse.quote(f'"{tk}" in:name,description,readme license:mit,apache-2.0 pushed:>2025-01-01')
        url = f"https://api.github.com/search/repositories?q={qq}&sort=stars&order=desc&per_page={so}"
        try:
            j = json.loads(_get(url, headers={"Accept": "application/vnd.github+json"}))
        except Exception as e:
            print(f"  [LOI github] {tk}: {str(e)[:60]}"); continue
        for it in j.get("items", []):
            _ghi(ra, "GitHub", tk, it["full_name"], it.get("owner", {}).get("login", ""),
                 (it.get("pushed_at") or "")[:10], (it.get("description") or "")[:400],
                 it["html_url"], "repo", {"sao": it.get("stargazers_count"), "giay_phep": (it.get("license") or {}).get("spdx_id")})
            dem += 1
        _ngu(2)
    print(f"  GitHub: {dem} repo")


def quet_huggingface(q, ra, so=8):
    dem = 0
    for loai in ("models", "datasets", "papers"):
        url = f"https://huggingface.co/api/{loai}?search=financial+forecast&sort=lastModified&limit={so}"
        try:
            j = json.loads(_get(url))
        except Exception as e:
            print(f"  [LOI huggingface {loai}]: {str(e)[:60]}"); continue
        for it in j:
            _ghi(ra, "HuggingFace", loai, it.get("id") or it.get("title", ""), "",
                 (it.get("lastModified") or it.get("publishedAt") or "")[:10],
                 (it.get("description") or "")[:400], f"https://huggingface.co/{loai}/" + it.get("id", ""),
                 loai, {"luot_tai": it.get("downloads")})
            dem += 1
        _ngu(1)
    print(f"  HuggingFace: {dem} muc")


def quet_reddit(q, ra, so=8):
    dem = 0
    for sub in q["reddit_subs"]:
        url = f"https://www.reddit.com/r/{sub}/top.json?limit={so}&t=month"
        try:
            j = json.loads(_get(url, headers={"User-Agent": "TheBrainResearch/0.1 by research"}))
        except Exception as e:
            print(f"  [LOI reddit r/{sub}]: {str(e)[:60]}"); continue
        for ch in j.get("data", {}).get("children", []):
            d = ch["data"]
            _ghi(ra, "Reddit", f"r/{sub}", d.get("title", ""), d.get("author", ""),
                 datetime.utcfromtimestamp(d.get("created_utc", 0)).strftime("%Y-%m-%d"),
                 (d.get("selftext") or "")[:400], "https://www.reddit.com" + d.get("permalink", ""),
                 "bai_viet", {"diem": d.get("score"), "binh_luan": d.get("num_comments")})
            dem += 1
        _ngu(2)
    print(f"  Reddit: {dem} bai")


def quet_rss(q, ra, so=6):
    dem = 0
    for feed in q["rss"]:
        try:
            x = _get(feed)
        except Exception as e:
            print(f"  [LOI rss] {feed[:50]}: {str(e)[:50]}"); continue
        try:
            root = ET.fromstring(x)
            items = list(root.iter("item"))[:so]
        except Exception:
            print(f"  [LOI rss doc] {feed[:50]}"); continue
        for it in items:
            t = (it.findtext("title") or "").strip()
            lk = it.findtext("link") or ""
            d = (it.findtext("pubDate") or "")[:16]
            _ghi(ra, "RSS", feed[:40], t, "", d, (it.findtext("description") or "")[:400], lk, "bai_viet")
            dem += 1
        _ngu(2)
    print(f"  RSS: {dem} bai")


def quet_darwinex(q, ra, so=10):
    dem = 0
    so = q.get("darwinex", {}).get("max_darwin", so)
    url = "https://api.darwinex.com/public/v2/darwin"
    try:
        j = json.loads(_get(url))
    except Exception as e:
        print(f"  [LOI darwinex] (thu cong khi mang cho phep): {str(e)[:60]}"); return
    for it in (j if isinstance(j, list) else j.get("data", []))[:so]:
        _ghi(ra, "Darwinex", "track_record", it.get("name") or it.get("darwinName", ""),
             it.get("manager", ""), (it.get("inceptionDate") or "")[:10],
             f"Lo: {it.get('lowDD', '?')}% · Lo 12t: {it.get('lowDD12M', '?')}% · ROI: {it.get('roi', '?')}%",
             f"https://www.darwinex.com/darwin/" + it.get("url", ""), "track_record",
             {"lo12t": it.get("lowDD12M"), "roi": it.get("roi")})
        dem += 1
        _ngu(1)
    print(f"  Darwinex: {dem} track record")


def quet_myfxbook(q, ra, so=2):
    dem = 0
    so = q.get("myfxbook", {}).get("max_trang", so)
    for trang in ("https://www.myfxbook.com/systems", "https://www.myfxbook.com/community/outstanding"):
        try:
            h = _get(trang).decode("utf-8", "ignore")
        except Exception as e:
            print(f"  [LOI myfxbook] {str(e)[:60]}"); continue
        for m in re.finditer(r'href="(/members/[^"]+)"[^>]*>([^<]{3,60})<', h)[: so * 30]:
            _ghi(ra, "Myfxbook", "track_record", m.group(2).strip(), "", "",
                 "Track record cong khai - can loc fake/survivorship", "https://www.myfxbook.com" + m.group(1),
                 "track_record")
            dem += 1
        _ngu(3)
    print(f"  Myfxbook: {dem} track record (tho)")


def quet_youtube(q, ra, so=5):
    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    key = (c.get("youtube", {}).get("api_key") or "").strip()
    if not key:
        print("  YouTube: bo qua - chua co api_key trong nguon_config.json")
        return
    dem = 0
    for tk in q.get("youtube", {}).get("tu_khoa", [])[:3]:
        url = ("https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=" +
               f"{so}&q={urllib.parse.quote(tk)}&key={key}")
        try:
            j = json.loads(_get(url))
        except Exception as e:
            print(f"  [LOI youtube] {str(e)[:60]}"); continue
        for it in j.get("items", []):
            sn = it.get("snippet", {})
            _ghi(ra, "YouTube", tk, sn.get("title", ""), sn.get("channelTitle", ""),
                 (sn.get("publishedAt") or "")[:10], sn.get("description", "")[:400],
                 "https://www.youtube.com/watch?v=" + it.get("id", {}).get("videoId", ""), "video")
            dem += 1
        _ngu(2)
    print(f"  YouTube: {dem} video")


# ---------------------------------------------------------------- chay
NGUON = {"arxiv": quet_arxiv, "github": quet_github, "huggingface": quet_huggingface,
         "reddit": quet_reddit, "rss": quet_rss, "darwinex": quet_darwinex,
         "myfxbook": quet_myfxbook, "youtube": quet_youtube}


def main():
    p = argparse.ArgumentParser(description="Quet rong nguon cong khai cho THE BRAIN")
    p.add_argument("--nguon", nargs="*", default=list(NGUON), choices=list(NGUON),
                   help="nguon can quet (mac dinh: tat ca)")
    p.add_argument("--so", type=int, default=8, help="so muc moi nguon (mac dinh 8)")
    a = p.parse_args()

    q = _cfg()
    REPORTS.mkdir(exist_ok=True)
    ra = []
    ngay = datetime.now().strftime("%Y%m%d")
    print(f"=== QUET RONG {ngay} ===\n")
    for ten in a.nguon:
        print(f"[{ten}]")
        try:
            NGUON[ten](q, ra, a.so)
        except Exception as e:
            print(f"  [LOI {ten}]: {str(e)[:80]}")
        _ngu(1)

    if ra:
        f = REPORTS / f"nguon_{ngay}.jsonl"
        with f.open("w", encoding="utf-8") as fh:
            for r in ra:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        md = REPORTS / "NGUON_QUET_RONG.md"
        dem = {}
        for r in ra:
            dem[r["nguon"]] = dem.get(r["nguon"], 0) + 1
        md.write_text(
            "# NGUON QUET RONG - bao cao\n\n*Chay " + datetime.now().strftime("%Y-%m-%d %H:%M") +
            " · " + str(len(ra)) + " muc tu " + ", ".join(f"{k}: {v}" for k, v in dem.items()) + "*\n\n"
            "> Day la NGUON THO - chua phai gi thuyet. Chi viec duoc dua vao "
            "BRAIN_ung_vien / so khang dinh sau khi lo qua cong A (co che, bac bo duoc, khong trung KD).\n\n"
            "| nguon | so muc |\n|---|---|\n" +
            "".join(f"| {k} | {v} |\n" for k, v in sorted(dem.items(), key=lambda x: -x[1])) +
            "\nXem chi tiet: `reports/nguon_" + ngay + ".jsonl`\n",
            encoding="utf-8")
        print(f"\n== TONG: {len(ra)} muc -> {f.name} + NGUON_QUET_RONG.md")
    else:
        print("\n== KHONG thu duoc gi (kiem tra mang / nguon da chay tren may cua ban)")


if __name__ == "__main__":
    main()
