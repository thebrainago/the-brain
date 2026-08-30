# -*- coding: utf-8 -*-
"""keywords_nguon.py - NGAN HANG TU KHOA dung chung cho Seeker.
Giup he thong TU SINH keyword de tim kiem / join kenh / join nhom tren moi
nen tang (Telegram, YouTube, X, TikTok, Facebook, web, Reddit, GitHub) theo
nhieu ngon ngu. Moi danh muc = chu de nguoi dung quan tam, co tu khoa theo lang.

Dung:
  from keywords_nguon import DANH_MUC, tao_truy_van, tao_ung_vien_username
  tao_truy_van("telegram", "cho_tin_hieu")
  tao_ung_vien_username("cho_tin_hieu", toi_da=20)
"""
import re

# Cac ngon ngu ho tro (ISO 639-1)
NGON_NGU = ("en", "vi", "ru", "es", "pt", "zh", "hi", "ar", "ja", "ko", "fr", "de", "tr")

# ------------------------------------------------------------------ DANH MUC
# Moi danh muc: ten tieng Viet (de hieu) + tu khoa theo [lang] -> [cac cum tu]
DANH_MUC = {
    "huyen_thoai": {
        "ten": "Trader huyền thoại",
        "tu_khoa": {
            "en": ["legendary trader", "top trader of all time", "best trader ever",
                   "warren buffett strategy", "george soros trading", "jesse livermore",
                   "ed seykota", "van tharp trading", "market wizards", "turtle trader"],
            "vi": ["trader huyền thoại", "trader giỏi nhất mọi thời đại", "warren buffett",
                   "george soros", "market wizards"],
            "ru": ["легендарный трейдер", "лучший трейдер", "джордж сорос", "уоррен баффет"],
            "es": ["trader legendario", "mejor trader de la historia", "george soros", "warren buffett"],
            "pt": ["trader lendário", "melhor trader", "george soros", "warren buffett"],
            "zh": ["传奇交易员", "最伟大交易员", "巴菲特", "索罗斯"],
            "hi": ["legendary trader", "sabse bada trader", "warren buffett"],
            "ar": ["متداول أسطوري", "أفضل متداول", "وارن بافيت"],
            "ja": ["伝説のトレーダー", "偉大なトレーダー", "ウォーレン・バフェット"],
            "ko": ["전설적인 트레이더", "위대한 트레이더", "워런 버핏"],
            "fr": ["trader légendaire", "meilleur trader", "warren buffett"],
            "de": ["legendärer Trader", "bester Trader", "warren buffett"],
            "tr": ["efsane trader", "en iyi trader", "warren buffett"],
        },
    },
    "dang_doi": {
        "ten": "Trader đương đại",
        "tu_khoa": {
            "en": ["top trader", "successful trader", "millionaire trader", "funded trader",
                   "trader interview", "pro trader", "institutional trader", "day trader lifestyle"],
            "vi": ["trader chuyên nghiệp", "trader thành công", "trader triệu phú", "trader giàu"],
            "ru": ["топ трейдер", "успешный трейдер", "трейдер миллионер", "про трейдер"],
            "es": ["trader exitoso", "trader millonario", "trader profesional"],
            "pt": ["trader de sucesso", "trader profissional", "trader milionário"],
            "zh": ["成功交易员", "专业交易员", "百万交易员"],
            "hi": ["successful trader", "top trader", "pro trader"],
            "ar": ["متداول ناجح", "متداول محترف"],
            "ja": ["成功したトレーダー", "プロトレーダー"],
            "ko": ["성공한 트레이더", "프로 트레이더"],
            "fr": ["trader à succès", "trader professionnel"],
            "de": ["erfolgreicher Trader", "Profi-Trader"],
            "tr": ["başarılı trader", "profesyonel trader"],
        },
    },
    "nguoi_thang": {
        "ten": "Top 1% / người chiến thắng",
        "tu_khoa": {
            "en": ["top 1% traders", "1% profit trader", "consistent winner", "winning trader",
                   "profitable trader", "trading edge", "only 1% traders win"],
            "vi": ["top 1% trader", "trader chiến thắng", "trader có lợi nhuận", "nhà giao dịch giỏi"],
            "ru": ["топ 1% трейдеров", "прибыльный трейдер", "выигрывающий трейдер"],
            "es": ["trader del 1%", "trader rentable", "trader ganador"],
            "pt": ["trader do 1%", "trader lucrativo", "trader vencedor"],
            "zh": ["1%交易员", "盈利交易员", "赢家交易员"],
            "hi": ["top 1% trader", "profitable trader", "winning trader"],
            "ar": ["متداول الربح", "متداول الفوز"],
            "ja": ["上位1%のトレーダー", "利益を出すトレーダー"],
            "ko": ["상위 1% 트레이더", "수익 트레이더"],
            "fr": ["trader du 1%", "trader rentable"],
            "de": ["Trader der Top 1%", "profitabler Trader"],
            "tr": ["ilk %1 trader", "kârlı trader"],
        },
    },
    "quy": {
        "ten": "Quỹ / prop firm",
        "tu_khoa": {
            "en": ["prop firm", "funded trader program", "hedge fund", "trading fund",
                   "ftmo", "fundednext", "myfundedfx", "prop trading challenge", "capital trader"],
            "vi": ["prop firm", "quỹ giao dịch", "funded trader", "vốn giao dịch"],
            "ru": ["проп фирма", "проп трейдинг", "хедж фонд", "funded trader"],
            "es": ["prop firm", "fondo de trading", "trader financiado"],
            "pt": ["prop firm", "fundo de trading", "trader financiado"],
            "zh": ["自营交易公司", "资金交易员", "对冲基金"],
            "hi": ["prop firm", "funded trader", "hedge fund"],
            "ar": ["شركة تداول خاص", "متداول ممول"],
            "ja": ["プロップファーム", "資金提供トレーダー"],
            "ko": ["프롭 펌", "자금 지원 트레이더"],
            "fr": ["prop firm", "trader financé"],
            "de": ["Prop-Firma", "funded Trader"],
            "tr": ["prop firm", "destekli trader"],
        },
    },
    "cho_tin_hieu": {
        "ten": "Chợ tín hiệu",
        "tu_khoa": {
            "en": ["forex signals", "trading signals", "copy trading", "signal provider",
                   "mql5 signals", "free forex signals", "crypto signals", "gold signals",
                   "stock signals", "signal service"],
            "vi": ["tín hiệu forex", "tín hiệu giao dịch", "copy trading", "nhà cung cấp tín hiệu"],
            "ru": ["форекс сигналы", "торговые сигналы", "копи трейдинг", "сигналы"],
            "es": ["señales forex", "señales de trading", "copy trading"],
            "pt": ["sinais forex", "sinais de trading", "copy trading"],
            "zh": ["外汇信号", "交易信号", "跟单交易"],
            "hi": ["forex signals", "trading signals", "copy trading"],
            "ar": ["إشارات فوركس", "إشارات التداول"],
            "ja": ["FXシグナル", "トレードシグナル"],
            "ko": ["외환 시그널", "거래 신호"],
            "fr": ["signaux forex", "signaux de trading"],
            "de": ["Forex Signale", "Trading Signale"],
            "tr": ["forex sinyalleri", "trading sinyalleri"],
        },
    },
    "cho_phuong_phap": {
        "ten": "Chợ phương pháp / khóa học",
        "tu_khoa": {
            "en": ["trading strategy", "trading system", "price action", "quant strategy",
                   "backtest", "trading course", "mentorship", "algorithmic trading",
                   "trading edge", "indicators"],
            "vi": ["chiến lược giao dịch", "hệ thống giao dịch", "price action", "khóa học trading",
                   "thuật toán giao dịch"],
            "ru": ["торговая стратегия", "торговая система", "price action", "курс трейдинга"],
            "es": ["estrategia de trading", "sistema de trading", "curso de trading"],
            "pt": ["estratégia de trading", "sistema de trading", "curso de trading"],
            "zh": ["交易策略", "交易系统", "交易课程"],
            "hi": ["trading strategy", "trading system", "trading course"],
            "ar": ["استراتيجية تداول", "نظام تداول", "دورة تداول"],
            "ja": ["取引戦略", "取引システム", "トレード講座"],
            "ko": ["거래 전략", "거래 시스템", "트레이딩 강좌"],
            "fr": ["stratégie de trading", "système de trading", "cours de trading"],
            "de": ["Trading-Strategie", "Trading-System", "Trading Kurs"],
            "tr": ["trading stratejisi", "trading sistemi", "trading kursu"],
        },
    },
    "cong_dong": {
        "ten": "Cộng đồng / diễn đàn",
        "tu_khoa": {
            "en": ["trading forum", "forex forum", "trading community", "trader chat",
                   "discord trading", "telegram trading", "trading subreddit", "trading group",
                   "investor community"],
            "vi": ["diễn đàn trading", "cộng đồng trader", "nhóm trading", "hội nhóm forex"],
            "ru": ["форум трейдеров", "сообщество трейдеров", "трейдер чат"],
            "es": ["foro de trading", "comunidad de trading", "grupo de traders"],
            "pt": ["fórum de trading", "comunidade de trading", "grupo de traders"],
            "zh": ["交易论坛", "交易社区", "交易群"],
            "hi": ["trading forum", "trading community", "trading group"],
            "ar": ["منتدى تداول", "مجتمع تداول", "مجموعة تداول"],
            "ja": ["トレードフォーラム", "トレードコミュニティ"],
            "ko": ["트레이딩 포럼", "트레이딩 커뮤니티"],
            "fr": ["forum de trading", "communauté de trading"],
            "de": ["Trading Forum", "Trading Community"],
            "tr": ["trading forumu", "trading topluluğu"],
        },
    },
    "vi_mo": {
        "ten": "Vĩ mô (cho Banker)",
        "tu_khoa": {
            "en": ["interest rate", "federal reserve", "fed", "cpi", "inflation",
                   "economic calendar", "cot report", "dollar index", "usd", "central bank",
                   "recession", "monetary policy"],
            "vi": ["lãi suất", "cục dự trữ liên bang", "lạm phát", "chỉ số đô la", "kinh tế vĩ mô"],
            "ru": ["процентная ставка", "инфляция", "индекс доллара", "центральный банк"],
            "es": ["tasa de interés", "inflación", "índice del dólar", "banco central"],
            "pt": ["taxa de juros", "inflação", "índice do dólar", "banco central"],
            "zh": ["利率", "通胀", "美元指数", "央行"],
            "hi": ["interest rate", "inflation", "dollar index", "central bank"],
            "ar": ["معدل الفائدة", "التضخم", "مؤشر الدولار"],
            "ja": ["金利", "インフレ", "ドル指数"],
            "ko": ["금리", "인플레이션", "달러 지수"],
            "fr": ["taux d'intérêt", "inflation", "indice du dollar"],
            "de": ["Zinssatz", "Inflation", "Dollar-Index"],
            "tr": ["faiz oranı", "enflasyon", "dolar endeksi"],
        },
    },
    "prop_firm": {
        "ten": "Prop firm / leaderboard funded trader",
        "tu_khoa": {
            "en": ["ftmo leaderboard", "topstep combine", "topstep trader", "apex trader funding",
                   "fundednext leaderboard", "the5ers leaderboard", "e8 funding", "funderpro",
                   "myfundedfx", "alphacapital group", "toptier trader", "earn2trade",
                   "bulenox", "fund your trading", "take profit trader", "surgetrader",
                   "funded trader leaderboard", "prop firm funded", "payout proof", "prop firm review",
                   "take profit trader", "true forex funds", "the fund trader", "the trading pit",
                   "instant funding", "alpha credit funding", "gowin funding", "cti funding",
                   "traders with edge", "aqua funded", "leveled equity", "theta funding",
                   "funded engineer", "elite anarchy", "polymer capital", "accelerator funding",
                   "prop firm payout", "funded trader payout"],
            "vi": ["prop firm", "trader được cấp vốn", "ftmo", "topstep", "apex", "fundednext",
                   "the5ers", "bảng xếp hạng prop", "nhận vốn trading"],
            "ru": ["проп трейдинг", "проп фирма", "фтмо", "топстеп", "финансируемый трейдер"],
            "es": ["prop firm", "trader financiado", "ftmo", "topstep", "apex"],
            "pt": ["prop firm", "trader financiado", "ftmo", "topstep"],
            "zh": ["自营交易", "资金交易员", "ftmo", "topstep"],
            "fr": ["prop firm", "trader financé", "ftmo", "topstep"],
            "de": ["Prop Firm", "finanzierter Trader", "ftmo", "topstep"],
        },
    },
    "copy_signal": {
        "ten": "Copy/signal có track record kiểm toán",
        "tu_khoa": {
            "en": ["collective2 strategy", "darwinex darwin", "darwinex d-live", "myfxbook autotrade",
                   "etoro popular investor", "zulutrade", "mql5 signals", "fxblue ranking",
                   "signal start", "peak index", "copyfx", "track record verified",
                   "audited trading performance", "third party verified trading",
                   "collective2 verified", "mql5 signal rankings", "zulutrade verified",
                   "darwinex audited", "performance chart audited"],
            "vi": ["copy trading", "tín hiệu có track record", "darwinex", "collective2", "myfxbook",
                   "etoro popular investor", "mql5 signals", "lịch sử giao dịch xác minh"],
            "ru": ["копи трейдинг", "дарвинекс", "коллектив2", "майфхбук", "проверенная история"],
            "es": ["copy trading", "darwinex", "collective2", "myfxbook"],
            "pt": ["copy trading", "darwinex", "collective2", "myfxbook"],
            "zh": ["跟单交易", "darwinex", "collective2", "myfxbook"],
            "fr": ["copy trading", "darwinex", "collective2", "myfxbook"],
            "de": ["Copy Trading", "darwinex", "collective2", "myfxbook"],
        },
    },
    "san_dau": {
        "ten": "Sàn đấu vô địch trading",
        "tu_khoa": {
            "en": ["world cup trading championship", "robbins world cup futures", "wccta",
                   "us investing championship", "usic champion", "trading cup",
                   "automated trading championship", "hungarian trading championship",
                   "trading competition winner", "trading championship results",
                   "tradingview house cup", "roboforex contest", "exness championship",
                   "alpari trading contest", "moneyshow top trader", "ftmo contest"],
            "vi": ["sàn đấu trading", "giải vô địch giao dịch", "world cup trading", "usic",
                   "nhà vô địch trading", "cuộc thi trading"],
            "ru": ["чемпионат по трейдингу", "world cup trading", "победитель трейдинг"],
            "es": ["campeonato de trading", "world cup trading"],
            "pt": ["campeonato de trading", "world cup trading"],
            "zh": ["交易大赛", "世界交易大赛", "交易冠军"],
            "fr": ["championnat de trading", "world cup trading"],
            "de": ["Trading-Meisterschaft", "world cup trading"],
        },
    },
    "chi_so_cta": {
        "ten": "Chỉ số quỹ CTA / managed futures",
        "tu_khoa": {
            "en": ["sg cta index", "sg trend index", "barclayhedge cta", "nilsson hedge",
                   "managed futures index", "cta fund performance", "hfri index",
                   "eurekahedge cta", "cta benchmark", "trend following index",
                   "solactive cta index", "uis managed futures index", "winton index"],
            "vi": ["chỉ số quỹ cta", "quỹ managed futures", "barclayhedge", "sg cta index",
                   "quỹ xu hướng", "hiệu suất quỹ cta"],
            "ru": ["индекс cta", "управляемые фьючерсы", "барклайхедж"],
            "es": ["índice cta", "futuros gestionados", "barclayhedge"],
            "pt": ["índice cta", "futuros gerenciados", "barclayhedge"],
            "zh": ["cta指数", "管理期货", "barclayhedge"],
            "fr": ["indice cta", "futures gérés", "barclayhedge"],
            "de": ["CTA-Index", "Managed Futures", "barclayhedge"],
        },
    },
    "hoc_thuat": {
        "ten": "Học thuật / nghiên cứu định lượng",
        "tu_khoa": {
            "en": ["arxiv q-fin", "ssrn quantitative finance", "quantconnect research",
                   "numerai tournament", "kaggle trading competition", "reddit algotrading",
                   "quantpedia", "quantocracy", "journal of financial economics",
                   "factor investing paper", "momentum anomaly", "trend following research",
                   "fama french data", "ken french data library", "time series momentum",
                   "cross sectional momentum", "jegadeesh titman", "quantstart", "quantocracy",
                   "factor investing", "seasonal trading research"],
            "vi": ["nghiên cứu định lượng", "bài báo quant", "arxiv q-fin", "ssrn",
                   "quantconnect", "numerai", "kaggle trading", "reddit algotrading"],
            "ru": ["количественные финансы", "arxiv q-fin", "соран", "квантик"],
            "es": ["finanzas cuantitativas", "arxiv q-fin", "ssrn", "quantconnect"],
            "pt": ["finanças quantitativas", "arxiv q-fin", "ssrn", "quantconnect"],
            "zh": ["量化金融", "arxiv q-fin", "ssrn", "quantconnect"],
            "fr": ["finance quantitative", "arxiv q-fin", "ssrn", "quantconnect"],
            "de": ["Quantitative Finanzen", "arxiv q-fin", "ssrn", "quantconnect"],
        },
    },
    "trader_he_thong": {
        "ten": "Trader hệ thống / CTA / quant nổi bật",
        "tu_khoa": {
            "en": ["turtle trading richard dennis", "larry hite", "bill dunn", "john w henry",
                   "andrea unger", "kevin davey", "andreas clenow", "ernest chan",
                   "robert carver", "michael dever", "mark minervini", "peter brandt",
                   "david ryan", "winton systematic", "ahl man group", "aqr asness",
                   "campbell and company", "systematica leda braga", "transtrend",
                   "ed seykota", "jesse livermore", "george soros", "richard dennis",
                   "jerry parker", "linda raschke", "jack schwager market wizards",
                   "john carter", "van tharp", "ed thorp", "jim simons renaissance",
                   "ray dalio", "howard marks", "quant trader interview"],
            "vi": ["trader hệ thống", "trader cta", "turtle trading", "andreas clenow",
                   "ernest chan", "mark minervini", "peter brandt", "trader định lượng"],
            "ru": ["системный трейдер", "квант трейдер", "андреас кленоу", "эрнест чан"],
            "es": ["trader sistemático", "trader cuantitativo", "andreas clenow", "mark minervini"],
            "pt": ["trader sistemático", "trader quantitativo", "andreas clenow", "mark minervini"],
            "zh": ["系统交易员", "量化交易员", "趋势跟踪"],
            "fr": ["trader systématique", "trader quantitatif", "andreas clenow"],
            "de": ["systematischer Trader", "quantitativer Trader", "andreas clenow"],
        },
    },
    "phuong_phap": {
        "ten": "Phương pháp / chiến lược giao dịch cụ thể",
        "tu_khoa": {
            "en": ["trend following donchian", "breakout strategy", "mean reversion",
                   "momentum strategy", "market structure liquidity", "smart money concepts",
                   "order flow", "volume profile", "supply and demand", "ict trading",
                   "wyckoff method", "elliot wave trading", "swing trading", "scalping strategy",
                   "grid trading", "carry trade", "gap trading", "range trading",
                   "price action trading", "vsa volume spread analysis"],
            "vi": ["phương pháp giao dịch", "chiến lược breakout", "mean reversion",
                   "smart money", "order flow", "volume profile", "price action",
                   "swing trading", "scalping", "ict"],
            "ru": ["торговая стратегия", "брэйкаут", "смарт мани", "прайс экшен"],
            "es": ["estrategia de trading", "breakout", "smart money", "price action"],
            "pt": ["estratégia de trading", "breakout", "smart money", "price action"],
            "zh": ["交易方法", "突破策略", "聪明钱", "价格行为"],
            "fr": ["stratégie de trading", "breakout", "smart money", "price action"],
            "de": ["Trading-Methode", "Breakout", "Smart Money", "Price Action"],
        },
    },
}
# ------------------------------------------------------------------ HAM TIM KIEM
def tong_hop():
    """Tra ve list (ten_danh_muc, ten_tieng_viet, so_ngon_ngu, tong_tu_khoa)."""
    return sorted(
        (ten, md["ten"], len(md["tu_khoa"]), sum(len(v) for v in md["tu_khoa"].values()))
        for ten, md in DANH_MUC.items()
    )


def tao_truy_van(nen_tang, danh_muc):
    """Tao cac chuoi tim kiem cho mot nen tang + mot danh muc.
    nen_tang: "google"|"telegram"|"x"|"tiktok"|"facebook"|"youtube"|"github"|"reddit"|"tat_ca"
    Tra ve list chuoi tim kiem rieng biet."""
    if danh_muc not in DANH_MUC:
        return []
    md = DANH_MUC[danh_muc]
    cac = []
    tm = {
        "telegram": lambda k: [f"site:t.me {k}", f"telegram channel {k}", f"telegram group {k}"],
        "x":        lambda k: [f"site:x.com {k}", f"twitter {k} trader"],
        "tiktok":   lambda k: [f"site:tiktok.com {k}"],
        "facebook": lambda k: [f"site:facebook.com {k}"],
        "youtube":  lambda k: [k],
        "github":   lambda k: [f"site:github.com {k}"],
        "reddit":   lambda k: [f"site:reddit.com {k}"],
        "google":   lambda k: [k],
    }
    builder = tm.get(nen_tang)
    if danh_muc == "tat_ca":
        builder = tm.get(nen_tang, tm["google"])
        for _ten, _md in DANH_MUC.items():
            for k in _md["tu_khoa"].get("en", [])[:3]:
                cac += builder(k)
        return list(dict.fromkeys(cac))
    if builder is None:
        return []
    for k in md["tu_khoa"].get("en", [])[:6]:
        cac += builder(k)
    return list(dict.fromkeys(cac))


def tao_ung_vien_username(danh_muc, toi_da=20):
    """Tu keyword cua mot danh muc (chu yeu en) sinh ra username Telegram tien nang."""
    if danh_muc not in DANH_MUC:
        return []
    tu = DANH_MUC[danh_muc]["tu_khoa"].get("en", [])
    out, seen = [], set()
    for k in tu[:5]:
        base = re.sub(r"[^a-z0-9]", "", k.lower())
        for cand in (base, base + "signals", base + "trading", base + "fx",
                     base + "group", base + "channel", base + "official"):
            if cand and cand not in seen and len(cand) <= 30:
                seen.add(cand); out.append(cand)
            if len(out) >= toi_da:
                return out
    return out


# ------------------------------------------------------------------ EVOLUTION
# Keyword bank TU BO SUNG lien tuc: cac tu khoa/ten moi phat hien tu du lieu quet
# duoc luu vao config/keyword_bo_sung.json va gop dong vao DANH_MUC. Ham bo_sung()
# dung de them (Evolution se goi). Nhu vay bank khong dung yen ma tu lon.

import pathlib as _pl
import json as _json

_BO_SUNG_FILE = _pl.Path(__file__).parent / "config" / "keyword_bo_sung.json"
BO_SUNG = {}


def _tai_bo_sung():
    global BO_SUNG
    try:
        if _BO_SUNG_FILE.exists():
            BO_SUNG = _json.loads(_BO_SUNG_FILE.read_text(encoding="utf-8"))
    except Exception:
        BO_SUNG = {}
    # gop vao DANH_MUC
    for dm, du_lieu in BO_SUNG.items():
        if dm not in DANH_MUC:
            DANH_MUC[dm] = {"ten": dm, "tu_khoa": {}}
        for lang, cac_tu in du_lieu.items():
            if lang not in DANH_MUC[dm]["tu_khoa"]:
                DANH_MUC[dm]["tu_khoa"][lang] = []
            for t in cac_tu:
                if t not in DANH_MUC[dm]["tu_khoa"][lang]:
                    DANH_MUC[dm]["tu_khoa"][lang].append(t)
    return len(BO_SUNG)


def _luu_bo_sung():
    try:
        _BO_SUNG_FILE.parent.mkdir(exist_ok=True)
        _BO_SUNG_FILE.write_text(_json.dumps(BO_SUNG, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
        return True
    except Exception:
        return False


def bo_sung(danh_muc, lang, cac_tu):
    """Them cac tu khoa moi vao bank (trong bo nho + luu file). Tra so luong them."""
    if isinstance(cac_tu, str):
        cac_tu = [cac_tu]
    cac_tu = [t.strip() for t in cac_tu if t and t.strip()]
    if not cac_tu:
        return 0
    BO_SUNG.setdefault(danh_muc, {}).setdefault(lang, [])
    them = 0
    for t in cac_tu:
        if t not in BO_SUNG[danh_muc][lang]:
            BO_SUNG[danh_muc][lang].append(t)
            them += 1
    # gop truc tiep vao DANH_MUC (khong goi _tai_bo_sung de tranh xoa bo nho)
    dm = DANH_MUC.setdefault(danh_muc, {"ten": danh_muc, "tu_khoa": {}})
    dm["tu_khoa"].setdefault(lang, [])
    for t in cac_tu:
        if t not in dm["tu_khoa"][lang]:
            dm["tu_khoa"][lang].append(t)
    _luu_bo_sung()
    return them


def thong_ke_bo_sung():
    return {dm: sum(len(v) for v in lang_map.values())
            for dm, lang_map in BO_SUNG.items()}


_tai_bo_sung()

if __name__ == "__main__":
    print("GENERAL: so danh muc:", len(DANH_MUC))
    for ten, ten_vn, sl, n in tong_hop():
        print(f"  - {ten:<15} {ten_vn:<28} lang={sl} keyword={n}")
    print("TONG keyword:", sum(td[3] for td in tong_hop()))
    print("\nVI DU: tao_truy_van('telegram','cho_tin_hieu'):")
    for q in tao_truy_van("telegram", "cho_tin_hieu")[:8]:
        print("   ", q)
    print("\nVI DU: tao_ung_vien_username('cho_tin_hieu')[:10]:")
    print("   ", tao_ung_vien_username("cho_tin_hieu", toi_da=10))
