# -*- coding: utf-8 -*-
"""nguon_reddit.py - Nguon Reddit cho SEEKNER: quet cac subreddit trading
bang API JSON cong khai (khong can dang nhap) qua toc_do (khong spam).
Reddit chan User-Agent mac dinh -> dung UA trinh duyet. Ghi vao bang `muc`
+ tao task "scout" cho bo_nao (huong="seeker", nguon="reddit").

Chay:
  python nguon_reddit.py                : quet thu 2-3 sub roi luu
  python nguon_reddit.py --xem          : quet thu nhung KHONG luu (chi in)
  python nguon_reddit.py --sub Forex,algotrading
"""
import sys, time, json, pathlib
import requests
import toc_do

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

# User-Agent trinh duyet: Reddit chan UA mac dinh cua requests.
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"}

SUB_MAC_DINH = [
    "Forex", "algotrading", "options", "Daytrading", "swingtrading", "futures",
    "Trading", "TradingView", "LocalTrade", "ForexTrading", "quantitative",
    "Tradingpys", "CryptoCurrency", "stocks", "trading212",
]

CAC_DANG = ["new", "top_day", "top_week"]


def _ket_qua_sub(sub):
    """Lay danh sach bai cua 1 sub qua 3 dang (new, top day, top week).
    Tra ve (ds_bai, loi). loi la chuoi mo ta neu co (403/429/timeout)."""
    ds = []
    loi = ""
    bi_chan = False
    for dang in CAC_DANG:
        if dang == "new":
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=100"
        elif dang == "top_day":
            url = f"https://www.reddit.com/r/{sub}/top.json?t=day&limit=100"
        else:
            url = f"https://www.reddit.com/r/{sub}/top.json?t=week&limit=100"
        js = None
        for thu in range(3):  # 1 lan dau + retry 2 lan
            r = toc_do.lay(url, nguon="reddit", headers=UA, timeout=40)
            if r is not None:
                try:
                    js = r.json()
                except Exception:
                    js = None
                break
            # toc_do dat backoff khi gap 403/429 -> khong retry, bao loi ngay
            if toc_do.TOC_DO._doi_den.get("reddit", 0) > time.time():
                loi = f"{dang}: bi chan (403/429)"
                bi_chan = True
                break
            time.sleep(3)
        if bi_chan:
            break
        if js is None:
            if not loi:
                loi = f"{dang}: khong doc duoc (403/429/thoi gian)"
            continue
        for child in js.get("data", {}).get("children", []):
            dt = child.get("data", {})
            if not dt.get("name"):
                continue
            ten = (dt.get("title") or "")[:200]
            permalink = dt.get("permalink") or ""
            url_perma = "https://www.reddit.com" + permalink if permalink else ""
            if not url_perma:
                continue
            text = (dt.get("selftext") or "")[:400]
            ds.append({
                "ten": ten,
                "url": url_perma,
                "text": text,
                "nguon_y": sub,
                "tu_khoa": f"reddit:{dang}",
                "thoi_gian": dt.get("created_utc") or 0,
            })
    return ds, loi


def quet(sub_list=None, so=25):
    """Quet tung subreddit (new + top theo ngay/tuan). Tra ve list dict
    {ten, url, text, nguon_y, tu_khoa, thoi_gian} toi da `so` bai khong trung."""
    sub_list = sub_list or SUB_MAC_DINH
    out = []
    seen = set()
    thong_ke = {}   # sub -> {"bai": n, "loi": loi}
    for sub in sub_list:
        ds_sub, loi = _ket_qua_sub(sub)
        thong_ke[sub] = {"bai": len(ds_sub), "loi": loi}
        for d in ds_sub:
            if len(out) >= so:
                break
            if d["url"] in seen:
                continue
            seen.add(d["url"])
            out.append(d)
        # bi chan 403/429 -> dung quet cac sub con lai (tranh ngu backoff 600s)
        if loi and "bi chan" in loi:
            break
        if len(out) >= so:
            break
    return out, thong_ke


def luu(con, ds):
    """Ghi cac bai vao bang muc (bao trung qua bam(url)) + tao task scout.
    Tra ve so luong them moi."""
    import bo_nao
    them = 0
    for d in ds:
        mid = bo_nao.bam(d["url"])
        ten = d["ten"] or (d["text"] or d["url"])[:120]
        try:
            con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) "
                        "VALUES(?,?,?,?,?,0)",
                        (mid, "reddit", ten, d["url"], time.time()))
            if con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()[0] == 0:
                bo_nao.tao_task(con, "scout",
                                {"ten": ten, "url": d["url"],
                                 "van_ban": d.get("text", ""),
                                 "nguon_y": d.get("nguon_y", ""),
                                 "tu_khoa": d.get("tu_khoa", "")},
                                muc_id=mid, uu_tien=0, huong="seeker")
                them += 1
        except Exception:
            pass
    con.commit()
    return them


def main():
    args = sys.argv[1:]
    xem = "--xem" in args
    subs = SUB_MAC_DINH[:3]
    if "--sub" in args:
        subs = [s.strip() for s in args[args.index("--sub") + 1].split(",") if s.strip()]
    ds, thong_ke = quet(subs, so=25)
    print(f"=== REDDIT: quet {len(subs)} sub, lay {len(ds)} bai (xem={xem}) ===")
    for sub, st in thong_ke.items():
        loi = (" | loi: " + st["loi"]) if st["loi"] else ""
        print(f"  r/{sub}: {st['bai']} bai{loi}")
    if not xem:
        import bo_nao
        con = bo_nao.mo_db()
        n = luu(con, ds)
        print(f"THEM MOI: {n} vao muc + scout")
    for d in ds[:15]:
        print(f"  [{d['nguon_y']}] {d['ten'][:55]} | {d['url']}")


if __name__ == "__main__":
    main()
