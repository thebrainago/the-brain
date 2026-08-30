p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\seeker_quy_tac.py"
s = open(p, encoding="utf-8").read()
# 1) imports
s = s.replace("import json, io\n", "import json, io, re, time\n", 1)
# 2) them loc_web() truoc chay_tru
anchor = "def chay_tru():"
web = '''def loc_web(toi_da=12, gioi_han_gio=6):
    """Loc LIVE tu arXiv (q-fin.ST/PM/TR), cache gioi_han. web_live=so bai loc duoc."""
    out = REPORTS / "seeker_web.json"
    state = REPORTS / "seeker_web_state.json"
    now = time.time()
    try:
        st = json.load(io.open(state, encoding="utf-8"))
        if (now - st.get("luc", 0)) < gioi_han_gio * 3600 and out.exists():
            return json.load(io.open(out, encoding="utf-8")).get("entries", [])
    except Exception:
        pass
    kw = ["momentum", "mean reversion", "breakout", "factor", "alpha", "trend",
          "volatility", "macd", "rsi", "pair", "machine learning", "neural",
          "reinforcement", "statistical arbitrage", "signal"]
    entries = []
    try:
        import requests
        H = {"User-Agent": "Mozilla/5.0 ResearchBot/1.0"}
        for q in ["cat:q-fin.ST", "cat:q-fin.PM", "cat:q-fin.TR"]:
            u = f"http://export.arxiv.org/api/query?search_query={q}&start=0&max_results=20&sortBy=submittedDate&sortOrder=descending"
            r = requests.get(u, headers=H, timeout=25)
            for t, so in re.findall(r"<entry>.*?<title>(.*?)</title>.*?<summary>(.*?)</summary>", r.text, re.S):
                tt = re.sub(r"\\s+", " ", t).strip(); ss = re.sub(r"\\s+", " ", so).strip()
                low = (tt + " " + ss).lower()
                hit = [k for k in kw if k in low]
                if hit:
                    entries.append({"title": tt[:150], "summary": ss[:380], "nguon": "arxiv",
                                    "tu_khoa": hit[:4]})
            time.sleep(1.2)
            if len(entries) >= toi_da:
                break
    except Exception as e:
        entries.append({"loi": str(e)[:120]})
    entries = entries[:toi_da]
    try:
        out.write_text(json.dumps({"luc": now, "entries": entries}, ensure_ascii=False, indent=1), encoding="utf-8")
        state.write_text(json.dumps({"luc": now}), encoding="utf-8")
    except Exception:
        pass
    return entries


def chay_tru():'''
assert anchor in s
s = s.replace(anchor, web, 1)
# 3) goi loc_web trong chay_tru va cap nhat thuc_thu
s = s.replace('''    kw = mo_rong_keyword(8)
    return {''', '''    kw = mo_rong_keyword(8)
    web = []
    try:
        web = loc_web()
    except Exception:
        web = []
    return {''', 1)
s = s.replace('''        "goi_y_keyword": kw,
        "thuc_thu": {"darwinex": len(top), "web_live": 0},''', '''        "goi_y_keyword": kw,
        "ung_vien_web": [{ "t": e["title"], "tk": e.get("tu_khoa", []) } for e in web if "title" in e],
        "thuc_thu": {"darwinex": len(top), "web_live": len(web), "web_moi_lay": now_web()},''', 1)
# them ham now_web (de tranh dung bien) - gan thoi gian
s = s.replace('''def chay_tru():
    """Ham EVO/bo dieu phoi goi: tra ve dict ket qua SEEKER."""''',
'''last_fetch = {"luc": 0}

def now_web():
    global last_fetch
    return time.strftime("%H:%M", time.gmtime(last_fetch.get("luc", 0)))


def chay_tru():
    """Ham EVO/bo dieu phoi goi: tra ve dict ket qua SEEKER."""''', 1)
open(p, "w", encoding="utf-8").write(s)
print("seeker_quy_tac web patched ok")
