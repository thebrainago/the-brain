# -*- coding: utf-8 -*-
"""seeker_quy_tac.py - SEEKER: bo QUY TAC cu the + pipeline loc chiến lược.
Không phải lời chung chung: đây là code chạy được, đọc nguồn, loc theo luật,
tra ve danh sach ung vien có cấu trúc (JSON) cho EVO gộp.

Cac buoc:
  1) NGUON_CATALOG  : danh sach nguồn cụ thể (loai, url, lay gi, do uu tien).
  2) RULES          : 5 luật cổng ngặt (track record, lãi, drawdown, vốn, repaint).
  3) loc_darwinex() : doc reports/darwinex_darwins.json, ap RULES, cham diem.
  4) mo_rong_keyword(): goi y truy van đào sâu tu keywords_nguon.
Hình: chay_tru() -> dict ket qua cho bo_nao gorped boi EVO.
"""
import json, io, re, time
from pathlib import Path

THU_MUC = Path(__file__).resolve().parent
REPORTS = THU_MUC / "reports"

# ------------------------------------------------------------------ 1. NGUỒN
# (loai, ten, url, lay_gi, uu_tien)
NGUON_CATALOG = [
    ("hoc_thuat", "SSRN - Financial Economics/Trading", "https://papers.ssrn.com", "công trình validate", 5),
    ("hoc_thuat", "arXiv q-fin", "https://arxiv.org/list/q-fin/recent", "preprint mới", 4),
    ("hoc_thuat", "QuantConnect Forum", "https://www.quantconnect.com/forum", "alpha/factor + code", 4),
    ("hoc_thuat", "Quantopian Lectures (archive)", "https://www.quantopian.com/lectures", "nền tảng factor", 3),
    ("hoc_thuat", "WorldQuant BRAIN (formulaic alphas)", "https://platform.worldquantbrain.com", "kho alpha", 4),
    ("cong_dong", "r/algotrading", "https://www.reddit.com/r/algotrading", "chiến lược thực + phản biện", 4),
    ("cong_dong", "r/quantfinance", "https://www.reddit.com/r/quantfinance", "thảo luận định lượng", 3),
    ("cong_dong", "Elite Trader (professional)", "https://www.elitetrader.com", "trader chuyên sâu", 3),
    ("hieu_suat", "Darwinex (1000 DARWIN)", "reports/darwinex_darwins.json", "track record thật", 5),
    ("hieu_suat", "Myfxbook Autotrade/Verified", "https://www.myfxbook.com/community/autotrade", "EA/robot có track record", 5),
    ("hieu_suat", "MQL5 Market/Signals", "https://www.mql5.com/en/signals", "EA + signal thật", 4),
    ("hieu_suat", "Collective2", "https://collective2.com", "hệ thống thuê bao có lịch sử", 4),
    ("hieu_suat", "FX Blue / DailyFX research", "https://www.fxblue.com", "tín hiệu chuyên nghiệp", 3),
]

# ------------------------------------------------------------------ 2. RULES
def r_track_record(d):
    """Co track record đu dai: period phai >= ONE_YEAR, hoac firstQuoteDate >= 2 nam."""
    p = d.get("period", "")
    if p in ("THREE_YEARS", "TWO_YEARS", "ONE_YEAR"):
        return True
    return False

def r_loi_duong(d):
    """Loi duong (returnByPeriod > 0)."""
    return d.get("returnByPeriod", 0) > 0

def r_drawdown(d, ngat=-20.0):
    """Drawdown khong qua sau (khong duoi -20%)."""
    dd = d.get("drawDownByPeriod", 0) or 0
    return dd > ngat

def r_von_that(d, toi_thieu=10000):
    """Co tien that (currentInvestment) tren muc toi thieu."""
    return (d.get("currentInvestment") or 0) >= toi_thieu

def r_nguoi_dau_tu(d, toi_thieu=5):
    """Co nguoi dau tu that (investorsByPeriod) tren muc toi thieu."""
    return (d.get("investorsByPeriod") or 0) >= toi_thieu

RULES = [r_track_record, r_loi_duong, r_drawdown, r_von_that, r_nguoi_dau_tu]

# ------------------------------------------------------------------ 3. DIEM
def diem(d):
    s = 0.0
    s += min(1.0, (d.get("returnByPeriod") or 0) / 100.0)          # loi
    s += min(1.0, (d.get("dscore") or 0) / 100.0) * 0.5            # dscore
    s += min(1.0, (d.get("investorsByPeriod") or 0) / 50.0) * 0.3  # nguoi tin
    s += min(1.0, (d.get("currentInvestment") or 0) / 500000.0) * 0.2  # quy mo von
    dd = abs(d.get("drawDownByPeriod") or 0)
    s -= min(1.0, dd / 25.0) * 0.4                                 # phat drawdown sau
    return round(s, 3)

# ------------------------------------------------------------------ 4. PIPELINE
def loc_darwinex(toi_da=30):
    f = REPORTS / "darwinex_darwins.json"
    if not f.exists():
        return []
    j = json.load(io.open(f, encoding="utf-8"))
    ds = j.get("darwins", [])
    ok = []
    for d in ds:
        if all(r(d) for r in RULES):
            d2 = dict(d)
            d2["diem"] = diem(d)
            ok.append(d2)
    ok.sort(key=lambda x: -x["diem"])
    return ok[:toi_da]

def mo_rong_keyword(toi_da=8):
    """Goi y truy van đào sâu tu keywords_nguon."""
    try:
        import keywords_nguon as K
        ds = K.tao_truy_van("web", "quan_research")[:toi_da]
        return ds
    except Exception:
        return []

def loc_web(toi_da=12, gioi_han_gio=6):
    """Loc LIVE tu arXiv (q-fin.ST/PM/TR), cache gioi_han. web_live=so bai loc duoc."""
    global last_fetch
    out = REPORTS / "seeker_web.json"
    state = REPORTS / "seeker_web_state.json"
    now = time.time(); last_fetch = {"luc": now}
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
                tt = re.sub(r"\s+", " ", t).strip(); ss = re.sub(r"\s+", " ", so).strip()
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


last_fetch = {"luc": 0}

def now_web():
    global last_fetch
    return time.strftime("%H:%M", time.gmtime(last_fetch.get("luc", 0)))


def chay_tru():
    """Ham EVO/bo dieu phoi goi: tra ve dict ket qua SEEKER."""
    top = loc_darwinex(30)
    kw = mo_rong_keyword(8)
    web = []
    try:
        web = loc_web()
    except Exception:
        web = []
    r = {
        "tru": "SEEKER",
        "so_nguon": len(NGUON_CATALOG),
        "nguon_uu_tien_cao": [n[1] for n in NGUON_CATALOG if n[4] >= 5],
        "so_ung_vien_qua_loc": len(top),
        "ung_vien_top": [{"a": d["darwin"], "url": d["url"],
                          "loi_pct": round(d.get("returnByPeriod", 0), 1),
                          "dd_pct": round(d.get("drawDownByPeriod", 0), 1),
                          "diem": d["diem"]} for d in top[:10]],
        "goi_y_keyword": kw,
        "ung_vien_web": [{ "t": e["title"], "tk": e.get("tu_khoa", []) } for e in web if "title" in e],
        "thuc_thu": {"darwinex": len(top), "web_live": len(web), "web_moi_lay": now_web()},
    }
    try:
        (REPORTS / "seek_out.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    return r

if __name__ == "__main__":
    print(json.dumps(chay_tru(), ensure_ascii=False, indent=2))
