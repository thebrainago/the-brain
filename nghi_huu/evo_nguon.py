# -*- coding: utf-8 -*-
r"""evo_nguon.py - EVOLUTION: LIEN TUC TIM THEM NGUON (da tu khoa, da ngon ngu, cham diem).
Bo sung vao bo loc nguon (reports/nguon_moi.json) mot cach lien tuc, va day nguon moi
cho SEEKER (tao scout + them muc).
Nguon phat hien: GitHub search (repo MQL5/Pine) + X search (CDP, doc-x).
Cham diem: do lien quan vs tu khoa chinh, sao/followers, moi (ngay), co code.
Chay:  python evo_nguon.py [--xem]
"""
import sys, time, json, pathlib, re
import requests

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))
BO_LOC = LAB / "reports" / "nguon_moi.json"
UA = {"User-Agent": "thebrain-evo/1.0"}
API = "https://api.github.com"

# 1) DA TU KHOAS + DA NGON NGU
TRUY_VAN_GITHUB = [
    "MQL5 EA trend following", "Pine Script strategy",
    "MetaTrader 5 backtest", "quant strategy python",
]
TRUY_VAN_X = [
    "trend following strategy", "turtle trading system",
    "chiến lược giao dịch xu hướng",  # VN
    "торговая стратегия тренд",        # RU
    "趋势跟踪策略",                     # CN
    "estrategia de trading de tendencia", # ES
]
TU_KHOA_CHINH = ["trend", "momentum", "breakout", "backtest", "ea", "mql5", "pine",
                 "strategy", "chiến lược", "стратегия", "策略", "trading"]

def _get(url, params=None):
    r = requests.get(url, params=params, headers=UA, timeout=25)
    return r.json() if r.status_code == 200 else None

def _doc_bang():
    if BO_LOC.exists():
        try:
            return json.loads(BO_LOC.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"ngay": time.strftime("%Y-%m-%d"), "nguon": []}

def _ghi_bang(b):
    BO_LOC.write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")

def cham_diem(ten, mo_ta, ngon_ngu=None, sao=0, ngay="", moi=0):
    s = 0.0
    tl = (ten + " " + (mo_ta or "")).lower()
    for k in TU_KHOA_CHINH:
        if k.lower() in tl:
            s += 1.5
    s += min(1.0, sao / 500.0) * 2.0
    if ngon_ngu in ("MQL5", "MQL4", "Python", "Pine"):
        s += 1.0
    if ngay and ngay >= time.strftime("%Y-")[0:7]:
        s += 0.5
    return round(s, 2)

def tim_github():
    ds = []
    for q in TRUY_VAN_GITHUB:
        j = _get(API + "/search/repositories", {"q": q, "sort": "stars", "per_page": 6})
        if not j:
            continue
        for it in j.get("items", []):
            ds.append({"loai": "github", "ten": it["full_name"], "url": it["html_url"],
                       "mo_ta": (it.get("description") or "")[:100], "ngon_ngu": it.get("language"),
                       "sao": it["stargazers_count"], "ngay": (it.get("updated_at") or "")[:10],
                       "diem": 0})
    return ds

def tim_x():
    ds = []
    try:
        import tu_follow_join as tf
        p = tf.sync_playwright().start()
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        pg = b.contexts[0].pages[0]
        seen = set()
        for q in TRUY_VAN_X[:4]:
            try:
                pg.bring_to_front()
                pg.goto("https://x.com/search?q=" + q.replace(" ", "%20") + "&f=live",
                        timeout=30000, wait_until="domcontentloaded")
                pg.wait_for_timeout(4000)
                for el in pg.query_selector_all("a[href]"):
                    href = el.get_attribute("href") or ""
                    m = re.match(r"^/([A-Za-z0-9_]{3,20})$", href)
                    if m:
                        u = m.group(1)
                        if u not in seen:
                            seen.add(u)
                            ds.append({"loai": "x", "ten": "@" + u, "url": "https://x.com/" + u,
                                       "mo_ta": "tai khoan tu ket qua X", "ngon_ngu": None,
                                       "sao": 0, "ngay": "", "diem": 0})
            except Exception:
                continue
        b.close(); p.stop()
    except Exception:
        pass
    return ds

def feed_seeker(ds):
    """Bo sung nguon dat diem vao DB cho SEEKER (muc + scout)."""
    n = 0
    try:
        import bo_nao
        con = bo_nao.mo_db()
        for d in ds:
            mid = bo_nao.bam(d["url"])
            try:
                con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) VALUES(?,?,?,?,?,0)",
                            (mid, "evo", d["ten"], d["url"], time.time()))
                if con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()[0] == 0:
                    bo_nao.tao_task(con, "scout", {"ten": d["ten"], "url": d["url"], "van_ban": "",
                                                   "nguon_y": d["loai"], "tu_khoa": "evo_nguon"},
                                    muc_id=mid, uu_tien=0, huong="seeker")
                    n += 1
            except Exception:
                pass
        con.commit()
    except Exception:
        pass
    return n


def chay_main():
    ds = tim_github() + tim_x()
    for d in ds:
        d["diem"] = cham_diem(d["ten"], d["mo_ta"], d["ngon_ngu"], d["sao"], d["ngay"])
    ds.sort(key=lambda x: -x["diem"])
    b = _doc_bang()
    cu = {x["url"] for x in b["nguon"]}
    b["ngay"] = time.strftime("%Y-%m-%d")
    them = 0
    for d in ds:
        if d["url"] not in cu:
            b["nguon"].append(d)
            them += 1
    b["nguon"] = sorted(b["nguon"], key=lambda x: -x["diem"])[:200]
    _ghi_bang(b)
    feed_seeker([d for d in ds if d["diem"] >= 5.0])
    print(f"=== EVO NGUON: phat hien {len(ds)}, them moi {them}, tong bo loc {len(b['nguon'])} ===")
    for d in ds[:12]:
        print(f"  {d['diem']:>5} | {d['loai']:6} | {d['ten'][:38]} | {str(d.get('ngon_ngu') or ''):10} | {d['url'][:45]}")
    return b

if __name__ == "__main__":
    chay_main()
