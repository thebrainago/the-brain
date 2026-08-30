# -*- coding: utf-8 -*-
r"""nguon_code.py - SEEKER: NGUON CODE (MQL5 + Pine) tu GitHub (API cong khai).
Tim repo chiến luoc/EA/indicator, lay cay file, loc file code (.mq5/.mqh/.pine/.py),
luu vao bang muc + tao task scout de Seeker nghien cuu code that.
Chay:  python nguon_code.py [--xem]
"""
import sys, time, json, pathlib
import requests

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

UA = {"User-Agent": "thebrain-seeker/1.0"}
API = "https://api.github.com"
DUOI_CODE = (".mq5", ".mqh", ".mq4", ".mql", ".pine", ".ps", ".py", ".cs", ".cpp", ".c")

TRUY_VAN = [
    "MQL5 EA trading robot",
    "MetaTrader 5 strategy",
    "Pine Script strategy tradingview",
    "tradingview pine indicator",
    "S&P 500 backtest strategy python",
]


def _get(url, params=None):
    r = requests.get(url, params=params, headers=UA, timeout=25)
    if r.status_code == 200:
        return r.json()
    return None


def tim_repo(truy_van, so=6):
    j = _get(API + "/search/repositories",
             {"q": truy_van, "sort": "stars", "order": "desc", "per_page": so})
    if not j:
        return []
    return [{"ten": it["full_name"], "url": it["html_url"],
             "mota": (it.get("description") or "")[:120],
             "ngon_ngu": it.get("language"), "sao": it["stargazers_count"],
             "ngay": it["updated_at"][:10]}
            for it in j.get("items", [])]


def cay_file(repo):
    """Lay danh sach file code trong repo (best-effort)."""
    j = _get(API + "/repos/" + repo + "/git/trees/HEAD", {"recursive": "1"})
    if not j:
        return []
    files = []
    for it in j.get("tree", []):
        if it["type"] == "blob" and it["path"].lower().endswith(DUOI_CODE):
            files.append(it["path"])
    return files[:40]


def chay_tru(so_repo=6):
    ds, thong_ke = [], {}
    for q in TRUY_VAN:
        repos = tim_repo(q, so=so_repo)
        for rp in repos:
            if rp["url"] in [d["url"] for d in ds]:
                continue
            files = cay_file(rp["ten"])
            if files:
                rp["file_code"] = files
                rp["so_file"] = len(files)
                rp["tu_khoa"] = "code:" + (rp["ngon_ngu"] or "?")
                rp["thoi_gian"] = time.time()
                ds.append(rp)
                thong_ke[rp["ten"]] = len(files)
    return ds, thong_ke


def luu(con, ds):
    import bo_nao
    them = 0
    for d in ds:
        for f_ in d.get("file_code", [])[:6]:
            url = d["url"] + "/blob/HEAD/" + f_
            mid = bo_nao.bam(url)
            ten = f"{d['ten']} :: {f_.split('/')[-1]}"
            try:
                con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) VALUES(?,?,?,?,?,0)",
                            (mid, "code", ten, url, time.time()))
                if con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()[0] == 0:
                    bo_nao.tao_task(con, "scout", {"ten": ten, "url": url, "van_ban": "",
                                                   "nguon_y": "github", "tu_khoa": d.get("tu_khoa", "")},
                                    muc_id=mid, uu_tien=0, huong="seeker")
                    them += 1
            except Exception:
                pass
    con.commit()
    return them


def main():
    xem = "--xem" in sys.argv
    ds, tk = chay_tru()
    print(f"=== NGUON CODE (GitHub): {len(ds)} repo co file code ===")
    for rp in ds[:15]:
        print(f"  {rp['sao']:>5}st | {rp['ngon_ngu']} | {rp['ten']} ({rp['so_file']} file)")
        for f_ in rp.get("file_code", [])[:4]:
            print(f"      - {f_}")
    if not xem:
        import bo_nao
        con = bo_nao.mo_db()
        n = luu(con, ds)
        print(f"THEM MOI: {n} file code -> muc + scout")
        ts = time.strftime("%Y%m%d_%H%M%S")
        (LAB / "reports" / f"nguon_code_{ts}.json").write_text(
            json.dumps(ds, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
