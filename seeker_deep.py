# -*- coding: utf-8 -*-
"""seeker_deep.py - SEEPER . sat: "bieu ten -> dao tai lieu cong khai da ngon ngu
-> rut ra chien luoc giao dich co cau truc". Khong chi list nguon be noi.

Voi 1 thuc the (ten/trader/quy/phuong phap), tu dong:
  1) tim_van_ban(): tim tai lieu tren Bing + Google + DuckDuckGo theo NHIEU NGON NGU.
  2) doc_van_ban(): cào noi dung, loc sach HTML -> van ban.
  3) rut_strategy(): bo RUT TRICH (deterministic, khong can LLM) ep van ban thanh
     cac truong co cau truc: nguyen_tac, entry, exit, risk, tai_san, khung, edge.
  4) luu JSON + day vao ket_hop_state cho EVO.

Chay:  python seeker_deep.py --ten "Warren Buffett"
       python seeker_deep.py               (chay danh sach goi y)
"""
import sys, re, json, io, time
from pathlib import Path
import requests

THU_MUC = Path(__file__).resolve().parent
REPORTS = THU_MUC / "reports"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Ngon ngu + query wrappers (test da ngon ngu)
LANGS = ["en", "vi", "ru", "es", "pt", "zh", "hi", "ar", "ja", "ko", "fr", "de", "tr"]
QUERY_MO = {
    "en": '"{N}" trading strategy rules entry exit risk management',
    "vi": '"{N}" chiến lược giao dịch quy tắc vào lệnh quản lý rủi ro',
    "ru": '"{N}" торговая стратегия правила вход выход управление рисками',
    "es": '"{N}" estrategia de trading reglas entrada salida gestión de riesgo',
    "pt": '"{N}" estratégia de trading regras entrada saída gestão de risco',
    "zh": '"{N}" 交易策略 规则 入场 出场 风险管理',
    "hi": '"{N}" ट्रेडिंग रणनीति नियम प्रवेश निकास जोखिम प्रबंधन',
    "ar": '"{N}" استراتيجية تداول قواعد دخول خروج إدارة المخاطر',
    "ja": '"{N}" トレード戦略 ルール エントリー エグジット リスク管理',
    "ko": '"{N}" 트레이딩 전략 규칙 진입 청산 리스크 관리',
    "fr": '"{N}" stratégie de trading règles entrée sortie gestion des risques',
    "de": '"{N}" Trading-Strategie Regeln Einstieg Ausstieg Risikomanagement',
    "tr": '"{N}" ticaret stratejisi kurallar giriş çıkış risk yönetimi',
}

# Goi y thuc the (tu khoa nguon: huyen_thoai, dang_doi, quy, trader_he_thong)
GOI_Y_TEN = [
    ("Warren Buffett", "huyen_thoai"),
    ("Ed Seykota", "huyen_thoai"),
    ("Turtle Traders trend following", "trader_he_thong"),
    ("Jesse Livermore", "huyen_thoai"),
    ("George Soros reflexivity strategy", "huyen_thoai"),
    ("Renaissance Technologies Medallion", "quy"),
    ("Ray Dalio All Weather", "quy"),
    ("CTA trend following system", "trader_he_thong"),
]

# ---------------------------------------------------------------- tim
def tim_van_ban(ten, ngon_ngu=("en", "vi", "ru"), toi_da=6):
    """Tim URL tren cac engine theo nhieu ngon ngu. Tra danh sach (url, nguon, ngon)."""
    kq = []
    def _bing(q):
        try:
            r = requests.get("https://www.bing.com/search", params={"q": q},
                             headers=UA, timeout=15)
            r.raise_for_status()
            return re.findall(r'<a href="(https?://[^"]+)"', r.text)[:toi_da]
        except Exception:
            return []
    def _ddg(q):
        try:
            r = requests.get("https://api.duckduckgo.com/", params={"q": q, "format": "json"},
                             headers=UA, timeout=15)
            j = r.json()
            urls = []
            for t in j.get("Results", []) + j.get("RelatedTopics", []):
                u = t.get("FirstURL") if isinstance(t, dict) else None
                if u and u.startswith("http"):
                    urls.append(u)
            return urls[:toi_da]
        except Exception:
            return []
    for lang in ngon_ngu:
        if lang not in QUERY_MO:
            continue
        q = QUERY_MO[lang].format(N=ten)
        for u in _bing(q):
            if u.startswith(("http",)) and "bing.com" not in u and "microsoft" not in u:
                kq.append((u, "bing", lang))
        for u in _ddg(q):
            kq.append((u, "ddg", lang))
    # bo trung, giu thu tu
    seen = set(); out = []
    for u, s, l in kq:
        if u in seen:
            continue
        seen.add(u); out.append((u, s, l))
    return out[:toi_da * 6]

# ---------------------------------------------------------------- doc
_TAG = re.compile(r"<[^>]+>")
def doc_van_ban(url):
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        t = _TAG.sub(" ", r.text)
        t = re.sub(r"\s+", " ", t)
        return t[:4000]
    except Exception:
        return ""

# ---------------------------------------------------------------- rut trich
def _cau(chuoi, tu_khoa):
    """Tra cac cau co chua bat ky tu khoa nao."""
    cac_cau = re.split(r"(?<=[.!?])\s+", chuoi)
    tk = [k.lower() for k in tu_khoa]
    out = []
    for c in cac_cau:
        cl = c.lower()
        if any(k in cl for k in tk) and len(c) < 320:
            out.append(c.strip())
    return out[:6]

def rut_strategy(van_ban, ten):
    s = {}
    s["thuc_the"] = ten
    s["nguyen_tac"] = _cau(van_ban, ["rule", "principle", "never", "always", "quy luật", "nguyên tắc", "никогда", "правило"])
    s["entry"] = _cau(van_ban, ["buy when", "enter when", "go long", "long when", "vào lệnh", "вход", "comprar", "вы cuando"])
    s["exit"] = _cau(van_ban, ["sell when", "exit", "take profit", "take-profit", "chốt lời", "выход", "vender", "cerrar"])
    s["risk"] = _cau(van_ban, ["stop loss", "stop-loss", "risk", "position size", "1%", "2%", "cắt lỗ", "quản lý rủi ro", "стоп", "límite"])
    s["tai_san"] = _cau(van_ban, ["e-mini", "futures", "forex", "equities", "stocks", "options", "commodities", "chứng khoán", "фьючерс", "дериватив"])
    s["khung"] = _cau(van_ban, ["daily", "weekly", "intraday", "hourly", "ngày", "tuần", "внутридневной", "diario"])
    s["edge"] = _cau(van_ban, ["edge", "advantage", "expectancy", "correlation", "lợi thế", "преимущество", "ventaja"])
    # diem: co bao nhieu truong co noi dung
    s["do_day"] = sum(1 for v in s.values() if isinstance(v, list) and v)
    return s

# ---------------------------------------------------------------- chay
def chay_tru(ten, toi_da_doc=8):
    urls = tim_van_ban(ten, ngon_ngu=("en", "vi", "ru"), toi_da=6)
    vb = ""
    lap = 0
    for u, s, l in urls:
        if lap >= toi_da_doc:
            break
        t = doc_van_ban(u)
        if t:
            vb += " " + t
            lap += 1
    strat = rut_strategy(vb, ten)
    strat["nguon"] = [{"url": u, "nguon": s, "ngon": l} for u, s, l in urls[:20]]
    strat["so_tai_lieu_doc"] = lap
    f = REPORTS / f"seeker_deep_{re.sub(r'\\W+','_',ten)[:40]}.json"
    f.write_text(json.dumps(strat, ensure_ascii=False, indent=2), encoding="utf-8")
    return strat

def chay_nhieu(ten_li=GOI_Y_TEN, toi_da=20):
    kq = []
    for ten, loai in ten_li[:toi_da]:
        try:
            s = chay_tru(ten)
            kq.append(s)
            print(f"[OK] {ten}: do_day={s['do_day']} tai_lieu={s['so_tai_lieu_doc']}")
        except Exception as e:
            print(f"[LOI] {ten}: {e}")
    (REPORTS / "seeker_deep_results.json").write_text(
        json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")
    return kq

if __name__ == "__main__":
    if "--ten" in sys.argv:
        ten = sys.argv[sys.argv.index("--ten") + 1]
        print(json.dumps(chay_tru(ten), ensure_ascii=False, indent=2))
    else:
        chay_nhieu()
