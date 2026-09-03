# -*- coding: utf-8 -*-
"""boc_llm.py - BOC CO CHE bang LLM, ban NANG SUAT.

Chu du an 03/09/2026: *"neu van de o co che boc thi hay tim cach khac phuc hoac
la xay dung bo doc hoac la goi api deepseek ma toi cho cau ket noi vao de luan"*
va truoc do: *"ty le chuyen doi phai xap xi hoac hon nguon dau vao"*.

DO DUOC HOM NAY, va do la ly do file nay ton tai:
  - 3.489 tai lieu -> 2.543 ban doc -> **4 ban tung duoc boc**. Day chuyen
    tai lieu->co che thuc te khong chay.
  - `doc_ma` chay 452 ban ma nguon trong DUOI 1 GIAY (1 ms/ban) va 444/452
    khong ra gi. Nut that KHONG phai toc do.
  - `seeker.boc_co_che` (ban LLM cu) chay 10 bai het 202 giay va ra **0 co che**.

VI SAO BAN CU RA 0. Loi nhac cua no kem danh sach 170 co che da co, cong cau:
  *"KHONG de xuat lai nhung cai tren, ke ca doi ten hay doi tham so. Mot bien
  the SMA/EMA cat nhau nua la lang phi mot suat ngan sach thong ke. Chi de
  xuat khi tai lieu cho mot co che THAT SU KHAC VE BAN CHAT."*
Voi menh lenh do va mot danh sach 170 ten, mo hinh gan nhu buoc phai im. Bo
loc nam ngay TRONG loi nhac, truoc ca khi co gi de loc.

BAN NAY DOI BA DIEU:
  1. **Lay HET luat doc duoc**, bien the duoc hoan nghenh. Chong trung KHONG
     lam bang menh lenh cho mo hinh ma lam bang `ngu_phap.van_tay_dieu_kien`
     - van tay tinh tren DIEU KIEN, nen doi ten khong qua duoc.
  2. **Chi dua tai lieu CO KHA NANG chua luat.** Bai hoc thuat ta PHUONG PHAP
     chu khong ta LUAT (suat do duoc: arxiv 0,8%, openalex 6%). Loc truoc bang
     tu khoa hanh dong thay vi dot mot luot goi cho mot bai khong co luat nao.
  3. **Goi SONG SONG.** API tra trong ~4 giay; chay tuan tu la tu bo 90% thong
     luong. Han muc chi phi van ton tai nhung la mot con so RIENG cua duong
     nay, khong dung chung voi phanh 40 luot/ngay cua `tri_tue`.

KHONG DOI: moi khai bao ra deu phai qua `kiem_khai_bao` + `kiem_khong_nhin_truoc`
truoc khi vao kho. Kien thuc moi chi vao he qua `ngu_phap.py` - khong `exec` ma
LLM sinh. Do la luat khong duoc pha.
"""
from __future__ import annotations

import concurrent.futures as _cf
import json
import re
import time

from nhan import ngu_phap as NP
from nhan import so as SO
from nhan import tri_tue as TT

#: Tai lieu phai co it nhat `DIEM_TOI_THIEU` dau hieu nay moi dang mot luot goi.
#:
#: BAN DAU CHI CO NHOM VAN XUOI, va do la mot loi do 03/09/2026: bo loc duoc
#: viet cho VAN XUOI roi dem ap len MA NGUON. Do that tren 300 ban doc github
#: (co that `class ThreeBarStrategy`, `strategy/indicators.py`): cham **0-1
#: diem, 0/300 qua nguong**. Code khong viet "buy when RSI crosses above 30";
#: no viet `if rsi < 30:`, `self.buy()`, `strategy.entry(...)`, `OrderSend(...)`.
DAU_HIEU_LUAT = [
    # --- van xuoi ---
    r"\b(buy|long|enter)\s+(when|if|signal|entry)", r"\b(sell|short|exit)\s+(when|if)",
    r"\bcross(es|ing)?\s+(above|below|over|under)\b", r"\bstop[\s-]?loss\b",
    r"\btake[\s-]?profit\b", r"\bif\s+.{0,40}\b(rsi|ema|sma|macd|atr|adx|stoch)",
    r"\b(rsi|stochastic|cci)\s*[<>]\s*\d", r"\bclose\s+(above|below)\b",
    r"\bentry\s+(rule|condition|signal)", r"\bexit\s+(rule|condition|signal)",
    r"\bkhi\s+(gia|rsi|ema|sma)\b", r"\b(vao|thoat)\s+lenh\b",
    # --- MA NGUON: Pine ---
    r"strategy\.(entry|close|exit|order)\s*\(", r"\bta\.(crossover|crossunder)\s*\(",
    r"\bplotshape\s*\(", r"//@version\s*=",
    # --- MA NGUON: MQL4/5 ---
    r"\b(OrderSend|PositionOpen|CTrade|trade\.(Buy|Sell))\s*\(",
    r"\bOnTick\s*\(", r"\biCustom\s*\(",
    r"\b(input|extern)\s+(double|int|bool)\s+\w*(SL|TP|Stop|Take|Period|Lot)",
    # --- MA NGUON: Python (backtrader / QuantConnect / vectorbt) ---
    r"self\.(buy|sell|order_target|close)\s*\(",
    r"\b(SetHoldings|MarketOrder|Liquidate)\s*\(",
    r"class\s+\w*Strateg\w*\s*[\(:]", r"def\s+(next|on_data|OnData|handle_data)\s*\(",
    # --- chung cho moi ngon ngu ---
    r"\b(rsi|ema|sma|macd|atr|adx|stoch|bollinger)\w*\s*[<>=]{1,2}\s*[\d\w]",
    r"\b(sl|tp|stop_?loss|take_?profit)\s*=\s*[\d\w]",
]

#: Ha tu 2 xuong 1: mot file ma nguon co the chi lo dung MOT dau hieu (vd mot
#: dong `strategy.entry`) ma van chua tron mot chien luoc. Doi HAI dau hieu la
#: mot rao khong co co so, va no da giet 300 ban doc tot.
DIEM_TOI_THIEU = 1
_RX = [re.compile(p, re.I) for p in DAU_HIEU_LUAT]

HE_THONG = (
    "Ban la bo trich xuat LUAT GIAO DICH. Ban KHONG danh gia chien luoc tot hay "
    "xau, KHONG khuyen nghi. Ban chi doc tai lieu va viet lai cac luat vao dung "
    "mot ngu phap JSON cho truoc. Neu tai lieu khong co luat cu the nao thi tra "
    "mang rong - dung bia."
)


def _diem_luat(vb: str) -> int:
    return sum(1 for rx in _RX if rx.search(vb or ""))


def ung_vien(gioi_han: int = 200, diem_toi_thieu: int = 2,
             nguon_uu_tien=("tradingview_pine", "tradingview_scripts", "mql5_code",
                            "mql5_bai_viet", "github", "lean_algo", "blog",
                            "rss_tradingview_blog", "quantconnect")) -> list[dict]:
    """Ban doc CHUA duoc boc, co dau hieu chua luat, uu tien nguon suat cao."""
    ds = SO.nhieu(
        "SELECT n.id, n.van_ban, n.so_ky_tu, n.kieu, t.tieu_de, t.nguon, t.url "
        "FROM noi_dung n LEFT JOIN tai_lieu t ON t.id = n.tai_lieu_id "
        "WHERE n.da_boc = 0 AND n.so_ky_tu > 800 AND n.kieu != 'khong_doc_duoc' "
        "ORDER BY CASE WHEN t.nguon IN ({}) THEN 0 ELSE 1 END, n.so_ky_tu DESC "
        "LIMIT ?".format(",".join("?" for _ in nguon_uu_tien)),
        *nguon_uu_tien, gioi_han * 4) or []
    ra = []
    for r in ds:
        d = dict(r)
        if _diem_luat(d["van_ban"]) >= diem_toi_thieu:
            ra.append(d)
        if len(ra) >= gioi_han:
            break
    return ra


def ung_vien_artifact(gioi_han: int = 300, diem_toi_thieu: int | None = None) -> list[dict]:
    """Ma nguon nam trong bang `artifact` (type `code`) chu khong o `noi_dung`.

    MAT XICH DUT tim ra 03/09/2026: `ma_nguon.thu_thap` tai file `.mq5` THAT
    ve va ghi vao **`artifact`**; con `boc_llm.ung_vien` doc **`noi_dung`**.
    Ket qua: 290 file .mq5 vua cao ve nam ngoai tam voi cua bo boc, va bao cao
    hien ra la "0 co che" trong khi kho vua day len 377 artifact code.

    Danh dau da boc bang mot dong trong `chi_so_vh` (bang `artifact` la
    CHI-GHI-THEM, khong duoc UPDATE).
    """
    da = {str(r["chi_tiet"]) for r in (SO.nhieu(
        "SELECT chi_tiet FROM chi_so_vh WHERE ten='boc_artifact'") or [])}
    rows = SO.nhieu(
        "SELECT id, fingerprint, payload FROM artifact "
        "WHERE artifact_type='code' ORDER BY id DESC LIMIT ?", gioi_han * 3) or []
    nguong = DIEM_TOI_THIEU if diem_toi_thieu is None else diem_toi_thieu
    ra = []
    for r in rows:
        d = dict(r)
        if str(d["id"]) in da:
            continue
        try:
            pl = json.loads(d["payload"])
        except Exception:
            continue
        # Payload LONG mot tang: cot `payload` chua {artifact_type, fingerprint,
        # payload, schema_version}, va ma nguon nam o `payload["payload"]`.
        if isinstance(pl.get("payload"), dict):
            pl = pl["payload"]
        vb = pl.get("content") or pl.get("noi_dung") or ""
        if len(vb) < 800 or _diem_luat(vb) < nguong:
            continue
        ra.append({"id": f"art:{d['id']}", "artifact_id": d["id"],
                   "van_ban": vb, "so_ky_tu": len(vb),
                   "tieu_de": pl.get("title") or pl.get("ten_file") or "",
                   "nguon": "mql5_code",
                   "url": pl.get("source_url") or pl.get("url") or ""})
        if len(ra) >= gioi_han:
            break
    return ra


def _nhac(d: dict) -> str:
    return (
        NP.NP_TOM_TAT if hasattr(NP, "NP_TOM_TAT") else _ngu_phap_tom_tat()
    ) + (
        "\n\nNHIEM VU: doc tai lieu duoi day va viet lai MOI luat vao lenh / thoat "
        "lenh ma no mo ta, theo ngu phap tren.\n"
        "- Lay HET, ke ca bien the gan giong nhau (RSI<30 va RSI<25 la HAI luat).\n"
        "- Moi luat can mot cau `co_che` giai thich VI SAO co nguoi tra tien cho "
        "phoi nhiem do (it nhat 25 ky tu).\n"
        "- `ho` phai thuoc: xu_huong, quay_ve_trung_binh, pha_vo, bien_dong, "
        "dong_tien, phien, lich, vi_mo, khac.\n"
        "- Chi dung toan hang co trong ngu phap. Thieu thi bo luat do va ghi vao "
        "`khong_dien_dat_duoc`.\n"
        "- Neu tai lieu khong co luat cu the nao: tra `co_che` la mang RONG.\n\n"
        'Tra ve DUNG mot JSON: {"co_che": [...], "khong_dien_dat_duoc": "..."}\n\n'
        f"== TAI LIEU: {d.get('tieu_de') or ''} ==\n"
        f"nguon: {d.get('nguon')} | dia chi: {d.get('url')}\n\n"
        f"{(d.get('van_ban') or '')[:40000]}")


def _ngu_phap_tom_tat() -> str:
    from tru import seeker as SK
    return getattr(SK, "NP_TOM_TAT", "")



def chuan_hoa_spec(spec: dict) -> dict:
    """Sua nhung sai lech DINH DANG cua dau ra LLM, truoc khi qua cong ngu phap.

    Do that 03/09/2026 tren lo thu dau tien: 2/4 khai bao bi loai chi vi
    `'giu' phai la so nguyen 1..500` - mo hinh tra `giu` la so thuc, chuoi,
    hoac null. Do la loi DINH DANG, khong phai loi noi dung; de nguyen thi mat
    mot nua san luong ma khong hoc duoc gi.

    Chi sua KIEU va MIEN. KHONG dung vao dieu kien, khong doan gia tri thieu,
    khong bia toan hang. Cong ngu phap van la nguoi phan xu cuoi.
    """
    if not isinstance(spec, dict):
        return spec
    d = dict(spec)

    # giu: so nguyen 1..500
    g = d.get("giu", 1)
    try:
        g = int(float(g))
    except (TypeError, ValueError):
        g = 1
    d["giu"] = min(500, max(1, g))

    # chieu: 1 hoac -1
    c = d.get("chieu", 1)
    try:
        c = int(float(c))
    except (TypeError, ValueError):
        c = 1
    d["chieu"] = -1 if c < 0 else 1

    # ten: bat buoc, chuan hoa ve [a-z0-9_]
    ten = NP.chuan_hoa_ten(str(d.get("ten") or ""))
    if not ten:
        ten = "llm_" + (NP.chuan_hoa_ten(str(d.get("co_che") or ""))[:40] or "khong_ten")
    d["ten"] = ten

    # vao/ra phai la list
    for k in ("vao", "ra"):
        v = d.get(k)
        if v is None:
            d[k] = []
        elif isinstance(v, dict):
            d[k] = [v]
        elif not isinstance(v, list):
            d[k] = []

    # hang phai la so
    def _so_hoa(nut):
        if isinstance(nut, dict):
            if "hang" in nut:
                try:
                    nut["hang"] = float(nut["hang"])
                except (TypeError, ValueError):
                    return False
            if "n" in nut and nut["n"] is not None:
                try:
                    nut["n"] = int(float(nut["n"]))
                except (TypeError, ValueError):
                    nut.pop("n", None)
            for v in nut.values():
                if isinstance(v, (dict, list)) and _so_hoa(v) is False:
                    return False
        elif isinstance(nut, list):
            for v in nut:
                if _so_hoa(v) is False:
                    return False
        return True

    for k in ("vao", "ra"):
        _so_hoa(d[k])
    return d


def _mot_ban(d: dict) -> dict:
    t0 = time.time()
    try:
        kq = TT.hoi_json(_nhac(d), HE_THONG, bo_qua_han_muc=True, dung_cache=False)
    except Exception as e:
        return {"id": d["id"], "loi": f"{type(e).__name__}: {str(e)[:80]}",
                "giay": time.time() - t0}
    j = kq.get("json") or {}
    return {"id": d["id"], "url": d.get("url"), "nguon": d.get("nguon"),
            "co_che": j.get("co_che") or [],
            "thieu": j.get("khong_dien_dat_duoc") or "",
            "giay": time.time() - t0}


def boc(gioi_han: int = 50, luong: int = 6, ghi_kho: bool = True,
        df_kiem=None, in_ra=print) -> dict:
    """Boc `gioi_han` ban doc, goi SONG SONG `luong` luot."""
    ds = ung_vien(gioi_han)
    con = gioi_han - len(ds)
    if con > 0:
        them = ung_vien_artifact(con)
        ds += them
        in_ra(f"  + {len(them)} ma nguon tu bang `artifact` (file .mq5 that)")
    in_ra(f"  {len(ds)} ban doc co dau hieu chua luat (tren tong chua boc)")
    if not ds:
        return {"ban": 0, "co_che_moi": 0}

    t0 = time.time()
    ket = []
    with _cf.ThreadPoolExecutor(max_workers=luong) as ex:
        for i, r in enumerate(ex.map(_mot_ban, ds), 1):
            ket.append(r)
            if i % 10 == 0:
                in_ra(f"  ... {i}/{len(ds)}  ({time.time()-t0:.0f}s)")

    da_co = {NP.van_tay_dieu_kien(c) for c in NP.doc_kho()}
    moi, tu_choi, loi = 0, 0, 0
    ly_do = {}
    for r in ket:
        if r.get("loi"):
            loi += 1
            continue
        for spec in r["co_che"]:
            if not isinstance(spec, dict):
                continue
            spec = chuan_hoa_spec(spec)
            spec.setdefault("nguon", r.get("url") or r.get("nguon") or "boc_llm")
            v = NP.kiem_khai_bao(spec)
            if v:
                tu_choi += 1
                ly_do[v[0][:60]] = ly_do.get(v[0][:60], 0) + 1
                continue
            try:
                vt = NP.van_tay_dieu_kien(spec)
            except Exception:
                tu_choi += 1
                continue
            if vt in da_co:
                tu_choi += 1
                ly_do["trung dieu kien"] = ly_do.get("trung dieu kien", 0) + 1
                continue
            if ghi_kho:
                try:
                    kq = NP.them_co_che(spec, df_kiem)
                    if not kq.get("nhan"):
                        tu_choi += 1
                        ly_do[str(kq.get("ly_do"))[:60]] = \
                            ly_do.get(str(kq.get("ly_do"))[:60], 0) + 1
                        continue
                except Exception as e:
                    tu_choi += 1
                    ly_do[f"them_co_che: {type(e).__name__}"] = \
                        ly_do.get(f"them_co_che: {type(e).__name__}", 0) + 1
                    continue
            da_co.add(vt)
            moi += 1

    with SO.ket_noi() as cn:
        for r in ket:
            if r.get("loi"):
                continue
            i = r["id"]
            if isinstance(i, str) and i.startswith("art:"):
                # `artifact` la CHI-GHI-THEM: danh dau o `chi_so_vh`.
                cn.execute("INSERT INTO chi_so_vh(ten,gia_tri,chi_tiet,luc) "
                           "VALUES('boc_artifact',1,?,?)",
                           (i.split(":", 1)[1], SO.bay_gio()))
            else:
                cn.execute("UPDATE noi_dung SET da_boc=1 WHERE id=?", (i,))

    giay = time.time() - t0
    return {"ban": len(ds), "co_che_moi": moi, "tu_choi": tu_choi, "loi": loi,
            "giay": round(giay, 1), "giay_moi_ban": round(giay / max(len(ds), 1), 1),
            "suat_tren_100_ban": round(moi / max(len(ds), 1) * 100, 1),
            "ly_do_tu_choi": dict(sorted(ly_do.items(), key=lambda x: -x[1])[:8])}
