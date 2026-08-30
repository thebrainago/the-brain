# -*- coding: utf-8 -*-
"""nguon_youtube.py - Nguon YouTube cho SEEKNER: tim kien thuc / chien luoc /
backtest / edge tu cac kenh trading bang YouTube Data API v3, theo nhieu ngon ngu.
Ghi vao bang `muc` + tao task "scout" cho bo_nao (huong="seeker").

Chay:
  python nguon_youtube.py                 : quet thu 1 tu khoa, 2-3 ngon ngu
  python nguon_youtube.py --ngon-ngu en,vi,ru
"""
import sys, time, json, pathlib
import toc_do

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))
API_KEYS = LAB / "config" / "api_keys.json"

NGON_NGU = ("en", "vi", "ru", "es", "zh", "hi", "ar", "ja", "ko", "pt", "fr", "de", "tr")

# Tu khoa goc (en) cho cac chu de trading.
TU_KHOA = {
    "en": ["trading strategy", "top trader", "backtest", "forex edge", "legendary trader",
           "quant trading", "price action strategy"],
    "vi": ["chiến lược giao dịch", "trader giỏi", "backtest forex", "phương pháp trade"],
    "ru": ["торговая стратегия", "топ трейдер", "бэктест форекс", "торговая система"],
    "es": ["estrategia de trading", "top trader", "backtest forex"],
    "zh": ["交易策略", "顶级交易员", "回测", "外汇交易"],
    "hi": ["trading strategy", "top trader", "forex backtest"],
    "ar": ["استراتيجية تداول", "أفضل متداول", "فوركس"],
    "ja": ["トレーディング戦略", "トップトレーダー", "バックテスト"],
    "ko": ["트레이딩 전략", "최고의 트레이더", "백테스트"],
    "pt": ["estratégia de trading", "top trader", "backtest forex"],
    "fr": ["stratégie de trading", "top trader", "backtest forex"],
    "de": ["Trading-Strategie", "Top-Trader", "Backtest Forex"],
    "tr": ["trading stratejisi", "en iyi trader", "forex backtest"],
}


def _youtube_key():
    if API_KEYS.exists():
        try:
            return json.loads(API_KEYS.read_text(encoding="utf-8")).get("youtube", "")
        except Exception:
            return ""
    return ""


def _goi_youtube(params, retry=3):
    """Goi YouTube API qua toc_do.lay (to trong quota). Retry khi chap chon."""
    key = _youtube_key()
    for thu in range(retry):
        r = toc_do.lay("https://www.googleapis.com/youtube/v3/search",
                       nguon="youtube",
                       params={**params, "key": key, "part": "snippet",
                               "type": "video", "maxResults": 5},
                       timeout=40)
        if r is not None:
            return r.json()
        time.sleep(3)
    return None


def quet(tu_khoa_cac_ngon_ngu=None, gioi_han_goi=25):
    """Tim kiem YouTube theo tu dien {ngon_ngu: [tu_khoa,...]}. Tra ve danh
    sach dict: ten, url, ngon_ngu, tu_khoa, kenh. To trong quota (gioi_han_goi)."""
    tu_khoa_cac_ngon_ngu = tu_khoa_cac_ngon_ngu or TU_KHOA
    demo = 0
    ds = []
    seen = set()
    for ngon, tks in tu_khoa_cac_ngon_ngu.items():
        for kw in tks:
            if demo >= gioi_han_goi:
                break
            data = _goi_youtube({"q": kw, "relevanceLanguage": ngon})
            demo += 1
            if not data:
                continue
            for it in data.get("items", []):
                vid = (it.get("id") or {}).get("videoId")
                if not vid:
                    continue
                url = f"https://www.youtube.com/watch?v={vid}"
                if url in seen:
                    continue
                seen.add(url)
                sn = it.get("snippet", {})
                ds.append({"ten": (sn.get("title") or "")[:120],
                           "url": url,
                           "ngon_ngu": ngon,
                           "tu_khoa": kw,
                           "kenh": (sn.get("channelTitle") or ""),
                           "mo_ta": (sn.get("description") or "")[:200]})
        if demo >= gioi_han_goi:
            break
    return ds


def luu(con, ds):
    """Ghi cac video vao bang muc (bao trung qua bam(url)) + tao task scout.
    Tra ve so luong them moi."""
    import bo_nao
    them = 0
    for d in ds:
        mid = bo_nao.bam(d["url"])
        try:
            con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) "
                        "VALUES(?,?,?,?,?,0)",
                        (mid, "youtube", d["ten"], d["url"], time.time()))
            if con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()[0] == 0:
                # muc moi -> tao scout
                bo_nao.tao_task(con, "scout",
                                {"ten": d["ten"], "url": d["url"], "van_ban": "",
                                 "tu_khoa": d.get("tu_khoa", ""),
                                 "ngon_ngu": d.get("ngon_ngu", "")},
                                muc_id=mid, uu_tien=0, huong="seeker")
                them += 1
        except Exception:
            pass
    con.commit()
    return them


def main():
    ngn = None
    if "--ngon-ngu" in sys.argv:
        ngn = sys.argv[sys.argv.index("--ngon-ngu") + 1].split(",")
    chon = {k: TU_KHOA[k] for k in (ngn or ["en", "vi", "ru"])
            if k in TU_KHOA}
    if not chon:
        chon = {"en": TU_KHOA["en"]}
    ds = quet(chon)
    import bo_nao
    con = bo_nao.mo_db()
    n = luu(con, ds)
    print(f"YouTube: tim {len(ds)} video, them moi {n} vao muc + scout")
    for d in ds[:15]:
        print(f"  [{d['ngon_ngu']}] {d['ten'][:55]} | {d['url']}")


if __name__ == "__main__":
    main()
