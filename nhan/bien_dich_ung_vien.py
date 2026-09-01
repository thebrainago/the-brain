# -*- coding: utf-8 -*-
"""Bien dich tai lieu da thu thap thanh CandidateArtifact co dan nguon.

Day la mat xich tung THIEU cua day chuyen: SEEKER gom duoc 156 DocumentArtifact,
QUANTLAB cho san o dau kia voi `kham_pha_theo_mau`, nhung khong co gi o giua nen
`candidate_queue` dung im o 0 dong.

BA RANG BUOC AN TOAN, khong duoc noi long:

1. **Chi anh xa vao mau CO SAN trong thu vien** (`nhan/mau.py`). Module nay
   khong bao gio sinh bieu thuc, khong bao gio sinh ma. Noi dung web chi duoc
   phep CHON mot mau da co, khong duoc dinh nghia mau moi. Do do khong co duong
   nao de van ban tren mang chen logic vao may.

2. **Khop theo RANH GIOI TU, va phai co van canh vao/ra lenh.** Khop chuoi tho
   la tham hoa da do that tren chinh kho nay:
       "rsi"  khop trong  Ve-rsi-on        -> 117/156 tai lieu "co RSI"
       "orb"  khop trong  col-orb-ar
       "ibs"  khop trong  ibserver
   Ba con so do se dot sach ngan sach FDR bang rac. Vi vay moi mau can:
   (a) tu khoa co ranh gioi tu, VA (b) mot tu van canh nam gan do.

3. **Moi ung vien phai kem trich dan that.** Hop dong CandidateArtifact bat
   buoc evidence khong rong va moi manh evidence phai tro ve mot artifact nguon
   da khai bao. Trich dan lay nguyen van tu tai lieu kem vi tri ky tu, nen mot
   khop sai nhin phat ra ngay thay vi trot lot thanh mot con so.

Bien dich xong KHONG co nghia la dung. No chi co nghia "dang xem xet, co nguon".
QUANTLAB moi la noi dong bang ke hoach, chay engine va phan quyet.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from nhan import hop_dong as HD
from nhan import so as SO

LAB = Path(__file__).resolve().parent.parent
CON_TRO = LAB / "reports" / "bien_dich_ung_vien_cursor.json"

#: Toi da bao nhieu ung vien moi mot luot. Hang doi day khong phai thanh tich:
#: moi ung vien qua duoc se an mot slot FDR o tang xac nhan.
TRAN_MOI_LUOT = 12
#: Mot tai lieu chi duoc de xuat toi da bay nhieu mau. Tai lieu nhac 9 chi bao
#: thuong la tai lieu liet ke thu vien, khong phai mot y tuong.
#: Bao nhieu MAU mot tai lieu duoc tro toi. Truoc 01/09 la 2, va do la mot tran
#: CUNG dat tuy y: chu du an noi mot bot hay mot chi bao tuong duong 1-5 kieu
#: danh, va do that cho thay phan bo bi cat dung o do (153 tai lieu ra 1 ung
#: vien, 79 ra 2, chi 4 ra 5 - vi 5 la so mau khop duoc chu khong phai so cho
#: phep). Nang len 6: du cho "1-5" ma van chan mot tai lieu tap hop nhac ten hai
#: chuc chi bao. Day KHONG phai noi long cong - moi ung vien van phai qua ty le
#: kich hoat, phep cat nhin truoc va FDR y nhu cu; no chi thoi ngung viec vut
#: bo thong tin TRUOC khi cong kip nhin.
TRAN_MOI_TAI_LIEU = 6
#: Tu khoa va van canh phai nam trong cung mot cua so bay nhieu ky tu.
CUA_SO_VAN_CANH = 600
#: Do dai trich dan luu lam bang chung.
DAI_TRICH_DAN = 240

#: Tu ngu cho thay dang mo ta mot QUY TAC VAO/RA LENH, khong phai ten bien trong
#: mot thu vien nao do.
#:
#: KHONG dua "strateg" vao day. No qua chung: cum "alignment strategy" trong mot
#: bai tin sinh hoc du bien "narrow range" thanh ung vien giao dich - da thu that
#: va no lot.
VAN_CANH = (
    r"\bentry\b|\bentries\b|\bsignals?\b|\bsetups?\b|\bbacktest"
    r"|\boversold\b|\boverbought\b|\bgo long\b|\bgo short\b"
    r"|long when|short when|buy when|sell when|buy if|sell if"
    r"|\bmean[- ]revers|\bbreakouts?\b|\btake profit\b|\bstop loss\b"
    r"|\bhold(?:ing)? (?:for )?\d+ (?:day|bar|hour)"
    r"|vao lenh|tin hieu|nguong vao|qua ban|qua mua|chot loi|cat lo"
)

#: Mau -> cac bieu thuc nhan dang. TAT CA deu co ranh gioi tu.
#: Chi liet ke mau ma van ban ngoai doi that co the goi ten duoc; mau nao khong
#: co cach goi pho bien thi de QUANTLAB tu quet o lane autonomous.
TU_KHOA: dict[str, tuple[str, ...]] = {
    "rsi_dao_chieu": (r"\brsi\b", r"\brelative strength index\b"),
    "bollinger_ve": (r"\bbollinger\b", r"\bbbands?\b", r"\bb-bands?\b"),
    "ibs_bat_day": (r"\binternal bar strength\b", r"\bibs\b(?!\s*erver)"),
    "donchian": (r"\bdonchian\b",),
    "momentum_ema": (r"\bema\b", r"\bexponential moving average\b"),
    "sma_cheo": (r"\bgolden cross\b", r"\bdeath cross\b",
                 r"\bmoving average cross(?:over)?\b", r"\bsma cross(?:over)?\b"),
    "ichimoku_cheo": (r"\bichimoku\b", r"\bkumo\b", r"\btenkan\b", r"\bkijun\b"),
    "orb_pha_vo": (r"\bopening range breakout\b", r"\bopening range\b",
                   r"\borb\b(?!\s*it)"),
    "cuoi_thang": (r"\bturn[- ]of[- ]the[- ]month\b", r"\bturn of month\b",
                   r"\bmonth[- ]end\b", r"\bend[- ]of[- ]month\b"),
    "gio_trong_ngay": (r"\bhour[- ]of[- ]day\b", r"\btime[- ]of[- ]day\b",
                       r"\bintraday season", r"\bsession hour\b"),
    "mua_qua_dem": (r"\bovernight (?:return|edge|drift|effect|anomaly)\b",
                    r"\bclose[- ]to[- ]open\b"),
    "ou_quay_ve": (r"\bornstein[- ]uhlenbeck\b", r"\bmean[- ]revert",
                   r"\bhalf[- ]life\b"),
    "lap_gap": (r"\bgap fill\b", r"\bfill(?:ing|s)? the gap\b", r"\bgap clos"),
    "bien_do_thu_hep": (r"\bnr7\b", r"\binside bar\b",
                        r"\b(?:volatility|bollinger) squeeze\b"),
    "phi_bao_hiem_cuoi_tuan": (r"\bweekend effect\b", r"\bweekend risk premi"),
    "moc_phien": (r"\bsession (?:high|low) break",),
}

#: Van canh cho MA NGUON - chi nhan GOI API DAT LENH THAT.
#:
#: Van xuoi noi "buy when RSI < 30"; ma nguon khong noi cau nao ca, no goi
#: `trade.Buy()`. Dung van canh cua van xuoi cho ma nguon thi moi EA that
#: deu truot.
#:
#: KHONG dua "buy signal"/"sell signal"/"entry signal" vao day. Do la cum
#: van xuoi va no nam trong CHU THICH cua chi bao thuan tuy. Do that 22/08:
#: `Fisher Transform Indicator` va `SuperTrend Indicator` deu chua dung mot
#: cum "sell signal" trong comment va khong he dat lenh - cum do bien mot
#: chi bao ve duong thanh "chien luoc RSI". Chi gu API dat lenh moi phan
#: biet duoc CHIEN LUOC voi CHI BAO.
VAN_CANH_MA = (
    r"\bOrderSend\b|\bOrderOpen\b|\bPositionOpen\b|\bCTrade\b"
    r"|\btrade\s*\.\s*(?:Buy|Sell)\b"
    r"|\bORDER_TYPE_(?:BUY|SELL)\b|\bTRADE_ACTION_DEAL\b"
)

_VAN_CANH_MA_RE = re.compile(VAN_CANH_MA, re.I)

#: MO mot vi the moi. Phan biet voi SUA/DONG vi the da co - do la ranh gioi
#: giua mot CHIEN LUOC va mot TIEN ICH quan ly lenh.
MO_LENH_MOI = (
    r"\btrade\s*\.\s*(?:Buy|Sell)\s*\(|\bOrderSend\b|\bPositionOpen\b"
)
#: Goi mot chi bao ky thuat. Khong bat buoc de la chien luoc (chien luoc gap /
#: phien chi doc gia tho), nhung co mat thi gan nhu chac chan la chien luoc.
CHI_BAO_MA = (
    r"\bi(?:MA|RSI|Stochastic|Bands|ATR|CCI|MACD|ADX|Momentum|Envelopes"
    r"|Ichimoku|Alligator|AO|SAR|Force|WPR|DeMarker|StdDev|OsMA|MFI|Custom)\b"
    r"|\bCopyBuffer\b"
)
_MO_LENH_RE = re.compile(MO_LENH_MOI, re.I)
_CHI_BAO_MA_RE = re.compile(CHI_BAO_MA, re.I)


def loai_ma_nguon(noi_dung: str) -> str:
    """`chien_luoc` | `tien_ich` | `chi_bao` - mot file .mq5 thuoc loai nao.

    Vi sao can (do 24/08 tren 40 file dau tien cua MQL5 Code Base muc `experts`):
    `_VAN_CANH_MA_RE` khop ca chu `CTrade`, ma **moi** tien ich quan ly lenh deu
    khai bao `CTrade trade;`. Ket qua la bo thu thap bao "24 chien luoc chua co
    mau" trong khi trong do co Quantora Margin Calculator, Break Even Manager,
    Trailing Stop Manager, Position Size Calculator, Trading Journal va vai cai
    panel - khong cai nao la chien luoc.

    Do lai bang ranh gioi MO VI THE MOI: 18/52 file mo vi the, 12/52 vua mo vi
    the vua goi chi bao. Con so dung de doc la 18, khong phai 24.

    Chinh docstring cua `ma_nguon._bao_mau_con_thieu` da canh bao dieu nay:
    "gop ba loai vao mot con so thi khong ai biet nen them template nao - va do
    dung la cach mot he thong hoc duoc bien thanh mot he thong ban ron".
    """
    if not noi_dung:
        return "chi_bao"
    if _MO_LENH_RE.search(noi_dung):
        return "chien_luoc"
    if _VAN_CANH_MA_RE.search(noi_dung):
        return "tien_ich"          # co goi giao dich nhung khong mo vi the moi
    return "chi_bao"


_VAN_CANH_RE = re.compile(VAN_CANH, re.I)
_TU_KHOA_RE = {mau: [re.compile(p, re.I) for p in ps] for mau, ps in TU_KHOA.items()}


# --------------------------------------------------------------- TRICH BANG CHUNG

def _cau_quanh(noi_dung: str, vi_tri: int) -> str:
    """Lay nguyen van doan quanh vi tri khop, de nguoi doc kiem duoc bang mat."""
    dau = max(0, vi_tri - DAI_TRICH_DAN // 2)
    cuoi = min(len(noi_dung), vi_tri + DAI_TRICH_DAN // 2)
    return " ".join(noi_dung[dau:cuoi].split())


def _tien_to_ma(tieu_de: str) -> str:
    """Tien to ten co che, rut tu tieu de tai lieu de con truy nguoc duoc.

    Ten di thang vao `gia_thuyet.ma` roi bi tim lai bang LIKE, nen chi giu chu
    va so - xem ghi chu o `ngu_phap.chuan_hoa_ten`.
    """
    import re as _re
    t = _re.sub(r"[^a-z0-9]+", "_", (tieu_de or "ma").lower()).strip("_")
    return (t[:24] or "ma")


def do_khop(noi_dung: str, che_do: str = "van_xuoi") -> list[dict]:
    """Cac mau ma tai lieu nay THUC SU noi den, kem trich dan va vi tri.

    Tra ve danh sach xep theo so lan nhac giam dan. Rong = tai lieu khong noi ve
    mau nao trong thu vien; do la ket qua BINH THUONG va pho bien.
    """
    if not noi_dung:
        return []
    ket_qua = []
    for mau, cac_re in _TU_KHOA_RE.items():
        for bieu_thuc in cac_re:
            khop = bieu_thuc.search(noi_dung)
            if khop is None:
                continue
            dau = max(0, khop.start() - CUA_SO_VAN_CANH)
            cuoi = min(len(noi_dung), khop.end() + CUA_SO_VAN_CANH)
            if che_do == "ma_nguon":
                # Van canh o muc CA FILE, khong phai cua so +-600 ky tu.
                #
                # Mot file ma nguon la MOT don vi mach lac: ten co che nam o
                # chu thich dau file, code dat lenh nam 10 KB ben duoi. Cua so
                # 600 ky tu duoc chinh cho VAN XUOI (mot doan van), va ap no
                # cho ma nguon thi tu choi dung nhung file dung nhat: do that
                # 22/08, `Session Opening Range Breakout EA` co du ca tu khoa
                # `orb_pha_vo` lan 14 diem dat lenh ma van bi loai, trong khi
                # mot chi bao tinh co nhac RSI gan chu "sell signal" thi lot.
                van_canh = _VAN_CANH_MA_RE.search(noi_dung)
            else:
                van_canh = _VAN_CANH_RE.search(noi_dung, dau, cuoi)
            if van_canh is None:
                continue        # co tu khoa nhung khong phai dang noi ve giao dich
            ket_qua.append({
                "mau": mau,
                "tu_khoa": khop.group(0),
                "vi_tri": khop.start(),
                "van_canh": van_canh.group(0),
                "trich_dan": _cau_quanh(noi_dung, khop.start()),
                "so_lan": len(bieu_thuc.findall(noi_dung)),
            })
            break               # moi mau chi lay khop dau tien
    ket_qua.sort(key=lambda x: (-x["so_lan"], x["mau"]))
    return ket_qua[:TRAN_MOI_TAI_LIEU]


def _tu_tin(khop: dict) -> float:
    """Do tu tin tho: nhac cang nhieu lan cang kho la trung ten bien."""
    return min(0.9, 0.3 + 0.1 * min(khop["so_lan"], 6))


# ------------------------------------------------------------------- BIEN DICH

def _mo_ta(tai_lieu) -> tuple[str, str, str]:
    """(tieu_de, url, che_do) cho ca DocumentArtifact lan CodeArtifact."""
    if isinstance(tai_lieu, HD.DocumentArtifact):
        return tai_lieu.title, tai_lieu.source_url, "van_xuoi"
    ten = (tai_lieu.metadata or {}).get("tieu_de") or tai_lieu.path
    return f"{ten} [{tai_lieu.path}]", tai_lieu.repository_url, "ma_nguon"


def bien_dich(tai_lieu, luc: str | None = None) -> list:
    """Mot DocumentArtifact HOAC CodeArtifact -> cac CandidateArtifact.

    Ma nguon duoc nhan tu 22/08. Rang buoc an toan KHONG doi mot ly nao: ma
    nguon o day la VAN BAN de doc va de CHON mot mau da co trong thu vien.
    Khong bao gio chay, khong bao gio bien dich, khong bao gio sinh mau moi.
    """
    if not isinstance(tai_lieu, (HD.DocumentArtifact, HD.CodeArtifact)):
        raise HD.ContractError(
            "bien_dich chi nhan DocumentArtifact hoac CodeArtifact")
    # Hop dong bat buoc ISO-8601 CO MUI GIO. `SO.bay_gio()` tra
    # "YYYY-MM-DD HH:MM:SS" gio may, khong co mui gio -> hop dong tu choi.
    tao_luc = luc or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    tieu_de, nguon_url, che_do = _mo_ta(tai_lieu)
    ra = []

    # ---- DUONG 2 (them 23/08): DOC HIEU van xuoi thanh MOT CO CHE CU THE ----
    # Duong 1 ben duoi chi tra loi duoc "tai lieu nay nhac den mau nao trong
    # thu vien" - no vut di CHINH cai dat gia nhat cua bai viet: chu ky, nguong
    # va so bar giu ma tac gia da viet ro. Duong 2 giu lai nhung con so do
    # duoi dang mot khai bao `nhan/ngu_phap.py`.
    #
    # An toan KHONG doi: van khong sinh ma. Khai bao la DU LIEU, va trinh thong
    # dich cua ngu phap khong co toan tu nao nhin ve tuong lai. Quyen nhan hay
    # tu choi van thuoc QUANTLAB, sau khi chay ty le kich hoat + phep cat.
    # DINH TUYEN THEO LOAI BAN DOC, khong theo doan mo. `DocumentArtifact` co
    # `metadata.content_kind` ghi ro ban doc nay la gi. Mot repo GitHub duoc
    # luu la `ma_nguon`, va bo doc VAN XUOI khong duoc cham vao no: do that
    # 23/08, hai co che sai (`mua_rsi30_tren_70`, `mua_rsi14_tren_30`) deu sinh
    # tu notebook/README cua repo - chu thich markdown pha loang mat do dau
    # hieu ma nen bo loc theo MAT DO khong bat duoc. Loai ban doc thi bat duoc.
    loai_ban_doc = str(((getattr(tai_lieu, "metadata", None) or {})
                        .get("content_kind") or "")).lower()
    if che_do == "van_xuoi" and loai_ban_doc not in ("ma_nguon", "khong_doc_duoc"):
        try:
            from nhan import doc_hieu as DH
            for r in DH.doc_bai(tai_lieu.content, tieu_de, nguon_url):
                spec = dict(r["spec"], nguon=nguon_url, van_tay=r["van_tay"])
                ra.append(HD.CandidateArtifact(
                    candidate_kind="method",
                    title=f"[DSL] {spec['ten']} - {tieu_de[:70]}",
                    summary=(
                        "Doc tu van xuoi thanh mot khai bao co che day du (chi bao, "
                        "nguong, so bar giu). QUANTLAB se kiem cu phap, ty le kich "
                        "hoat va phep cat nhin truoc TRUOC khi cho phep dang ky."),
                    source_artifact_fingerprints=[tai_lieu.fingerprint],
                    evidence=[dict(b, artifact_fingerprint=tai_lieu.fingerprint)
                              for b in r["bang_chung"]],
                    created_at=tao_luc,
                    tags=["tu_dong", "doc_hieu", "dsl"],
                    extractor="doc_hieu",
                    extractor_version="2",
                    confidence=0.5,
                    metadata={
                        "mau": spec["ten"],
                        "dsl": spec,
                        "van_tay_co_che": r["van_tay"],
                        "nguon_url": nguon_url,
                        "loai_nguon": "van_xuoi_dsl",
                    },
                ))
        except Exception:
            # Duong 2 hong KHONG duoc lam chet duong 1. Duong 1 la duong da
            # chay that tu 21/08.
            pass

    # DUONG 3 (them 01/09): DOC MA THANH NHIEU KHAI BAO CO CHE.
    #
    # Duong 2 o tren bi tat cho `ma_nguon` tu 23/08, va ly do do DUNG: bo doc
    # VAN XUOI ap len README/notebook trong repo de ra co che sai. Nhung cai bi
    # tat la bo doc van xuoi; chinh doan MA thi chua ai doc. Do phieu 01/09:
    # 247 ban doc ma nguon - EA MQL5 va Pine, suat ra ung vien cao nhat trong
    # moi loai (20,2%) - tu truoc toi nay chi duoc SO KHOP TU KHOA, tuc dong gop
    # dung mot cai nhan tro toi mot mau da co san.
    #
    # `nhan/doc_ma.py` doc KY HIEU chu khong doan nghia tu tieng nguoi, va tra
    # ve NHIEU khai bao cho MOT file - dung nhu chu du an noi: mot EA hay mot
    # Pine script tuong duong nhieu kieu danh. Do that tren `pineturtle.txt`
    # (Sonic R, 6 strategy): 12 khai bao, 10 qua cong ngu phap.
    if loai_ban_doc == "ma_nguon" or che_do == "ma_nguon":
        try:
            from nhan import doc_ma as DMA
            for spec in DMA.doc_ma(tai_lieu.content, nguon=nguon_url,
                                   tien_to=_tien_to_ma(tieu_de)):
                ra.append(HD.CandidateArtifact(
                    candidate_kind="method",
                    title=f"[MA] {spec['ten']} - {tieu_de[:70]}",
                    summary=(
                        "Doc tu MA NGUON that thanh mot khai bao co che day du. "
                        "Moi dieu kien so sanh doc lap trong file la mot kieu danh "
                        "rieng, de cong cham diem tung cai thay vi gop ca file "
                        "thanh mot nhan. QUANTLAB kiem cu phap, ty le kich hoat va "
                        "phep cat nhin truoc TRUOC khi cho dang ky."),
                    source_artifact_fingerprints=[tai_lieu.fingerprint],
                    evidence=[{"artifact_fingerprint": tai_lieu.fingerprint,
                               "quote": str(spec.get("co_che", ""))[:400],
                               "note": "dieu kien rut tu ma nguon"}],
                    created_at=tao_luc,
                    tags=["tu_dong", "doc_ma", "dsl"],
                    extractor="doc_ma",
                    extractor_version="1",
                    confidence=0.6,
                    metadata={
                        "mau": spec["ten"],
                        "dsl": spec,
                        "nguon_url": nguon_url,
                        "loai_nguon": "ma_nguon_dsl",
                    },
                ))
        except Exception:
            # Duong 3 hong KHONG duoc lam chet duong 1.
            pass

    for khop in do_khop(tai_lieu.content, che_do=che_do):
        ra.append(HD.CandidateArtifact(
            candidate_kind="method",
            title=f"{khop['mau']} - {tieu_de[:80]}",
            summary=(
                f"{'Ma nguon' if che_do == 'ma_nguon' else 'Tai lieu'} nhac den "
                f"co che '{khop['mau']}' {khop['so_lan']} lan "
                f"trong van canh vao/ra lenh ('{khop['van_canh']}'). Day la de xuat "
                f"XEM XET, chua phai ket luan: QUANTLAB se quet mau nay tren cac "
                f"tai san uu tien roi tu phan quyet."
            ),
            source_artifact_fingerprints=[tai_lieu.fingerprint],
            evidence=[{
                "artifact_fingerprint": tai_lieu.fingerprint,
                "quote": khop["trich_dan"],
                "locator": f"char {khop['vi_tri']}",
                "note": f"tu khoa khop: {khop['tu_khoa']}",
            }],
            created_at=tao_luc,
            tags=["tu_dong", "bien_dich_ung_vien", che_do],
            extractor="bien_dich_ung_vien",
            extractor_version="1",
            confidence=_tu_tin(khop),
            metadata={
                "mau": khop["mau"],
                "nguon_url": nguon_url,
                "loai_nguon": che_do,
                "so_lan_nhac": khop["so_lan"],
            },
        ))
    return ra


# ----------------------------------------------------------------- MOT LUOT

def _doc_con_tro() -> int:
    try:
        return int(json.loads(CON_TRO.read_text(encoding="utf-8"))["artifact_id"])
    except Exception:
        return 0


def _luu_con_tro(artifact_id: int) -> None:
    CON_TRO.parent.mkdir(parents=True, exist_ok=True)
    CON_TRO.write_text(json.dumps({"artifact_id": int(artifact_id)}), encoding="utf-8")


def mot_luot(gioi_han: int = TRAN_MOI_LUOT, tiep_tuc: bool = True) -> dict:
    """Quet cac DocumentArtifact chua bien dich, xep ung vien vao hang doi."""
    tu = _doc_con_tro() if tiep_tuc else 0
    rows = SO.nhieu(
        "SELECT id, payload FROM artifact "
        "WHERE artifact_type IN ('document','code') AND id>? "
        "ORDER BY id LIMIT 400", tu)

    bao = {"da_doc": 0, "xep_moi": 0, "trung": 0, "khong_khop": 0, "loi": 0,
           "mau": {}, "toi": tu, "cum_chua_hieu": {}}
    for row in rows:
        if bao["xep_moi"] >= gioi_han:
            break
        bao["da_doc"] += 1
        bao["toi"] = row["id"]
        try:
            tai_lieu = HD.artifact_from_json(row["payload"])
        except HD.ContractError:
            bao["loi"] += 1
            continue
        if not isinstance(tai_lieu, (HD.DocumentArtifact, HD.CodeArtifact)):
            bao["loi"] += 1
            continue

        # He tu noi ra thu no THIEU. Khong co dong nay thi "0 co che" doc nhu
        # "tai lieu khong co gi", trong khi that ra co the la "ngu phap chua co
        # chi bao do". Chi dem nhung cau DA chac chan la cau luat (co hanh dong
        # + phep so sanh + con so) ma ve trai khong doc duoc.
        if isinstance(tai_lieu, HD.DocumentArtifact):
            try:
                from nhan import doc_hieu as DH
                for x in DH.cum_chua_hieu(tai_lieu.content, toi_da=8):
                    bao["cum_chua_hieu"][x["cum"]] = \
                        bao["cum_chua_hieu"].get(x["cum"], 0) + 1
            except Exception:
                pass

        ung_vien = bien_dich(tai_lieu)
        if not ung_vien:
            bao["khong_khop"] += 1
            continue
        for uv in ung_vien:
            _, moi = SO.xep_candidate(uv, priority=5, route="QUANTLAB")
            if moi:
                bao["xep_moi"] += 1
                mau = uv.metadata.get("mau", "?")
                bao["mau"][mau] = bao["mau"].get(mau, 0) + 1
            else:
                bao["trung"] += 1

    _luu_con_tro(bao["toi"])
    top = sorted(bao["cum_chua_hieu"].items(), key=lambda kv: -kv[1])[:12]
    bao["cum_chua_hieu"] = dict(top)
    if top and top[0][1] >= 3:
        SO.bao_van_de(
            "ngu_phap_thieu_toan_hang", "VUA",
            "Cac cum tu dung o vi tri toan hang ma ngu phap chua co - day la "
            "danh sach viec cho nhan/ngu_phap.py, sinh tu tai lieu that",
            {"cum": top})
    SO.ghi_chi_so("ung_vien_xep_moi", bao["xep_moi"], bao)
    return bao


if __name__ == "__main__":
    import pprint
    pprint.pprint(mot_luot())
