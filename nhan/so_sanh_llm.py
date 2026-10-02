# -*- coding: utf-8 -*-
"""so_sanh_llm.py - SO SANH model re (DeepSeek, Qwen, ...) tren CHINH viec cua lab, cham bang MA khong bang y kien.

## Vi sao (02/10/2026)
Chu du an: *"mai toi se goi lai API cho cau so sanh giua deepseek va qwen"*. Model re (tang `tho` cua `nc_tho`, he `q`) lam viec doc/viet
co cau truc: khai bao co che bang JSON (`ngu_phap`), goi cong cu, trich so, tom tat, theo luat du an. Chon theo cam giac thi sai (lab da
tung do: LLM re dien `co_che` cho 48 khai bao, tham dinh bac 41) - nen o day moi task co HAM CHAM bang ma, chay cung mot bo task, cung mot
cach goi, ghi diem + token + do tre + chi phi.

Task (9, ~15k token / nha cung cap / lan; `--dai` them 1 task ngu canh dai ~12k token):
  json_ky_luat · spec_co_che (5 khai bao, cham bang `kiem_khai_bao` + `sinh_tu_spec` tren du lieu gia - khong exec ma LLM) · goi_cong_cu ·
  trich_bang_bao_cao · tinh_cagr_maxdd · luat_chan (tieu chi duyet cua chu du an) · tom_tat_trung_thuc (khong bia so) · tieng_viet_2_cau ·
  [needle_dai].
Cham THANG/HOA/THUA tung task, khong chi diem TB: mau nho thi chenh < 0,1 la nhieu. Ket luan: chenh diem >= 0,1 -> chon diem cao; con lai chon re hon.

Khoa KHONG nam trong repo/chat. Moi nha cung cap `P` (deepseek, qwen, hoac ten bat ky) lay theo thu tu:
  1. bien moi truong  SO_SANH_<P>_KHOA (hoac DEEPSEEK_API_KEY / DASHSCOPE_API_KEY) + SO_SANH_<P>_URL + SO_SANH_<P>_MO_HINH
  2. cc-switch (may nha): provider co ten chua `deepseek` / `aibox` (hoac SO_SANH_<P>_CC)
Tuy chon: SO_SANH_<P>_GIA_VAO / _GIA_RA (USD / 1 trieu token; khong khai thi chi phi ghi 'chua khai'), SO_SANH_<P>_THEM = JSON them vao than
yeu cau (vd {"enable_thinking": false} cho Qwen3).

    b so-sanh --khai                          in cach giai quyet tung nha cung cap (KHONG goi, KHONG in khoa)
    b so-sanh [--nha-cung-cap deepseek,qwen] [--task a,b] [--lan 2] [--dai] [--json]
"""
from __future__ import annotations

import json
import os
import random
import re
import statistics
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
MAC_DINH = {
    "deepseek": {"url": "https://api.deepseek.com", "cc": "deepseek", "khoa_env": ("DEEPSEEK_API_KEY",), "mo_hinh": "deepseek-chat"},
    "qwen": {"url": "", "cc": "aibox", "khoa_env": ("DASHSCOPE_API_KEY",), "mo_hinh": ""},
}
LAN_MAC_DINH = 2


class ThieuCauHinh(RuntimeError):
    pass


# ------------------------------------------------------------------ nha cung cap
def _cc_switch(ten: str) -> dict:
    try:
        from qwen import mo_hinh as QM
        return QM.tu_cc_switch(ten) or {}
    except Exception:                                       # noqa: BLE001
        return {}


def _so(env, k):
    try:
        return float(env[k]) if env.get(k) else None
    except ValueError:
        return None


def nha_cung_cap(ten: str, env=None, cc=None) -> dict:
    """-> {ten, url, khoa, mo_hinh, nguon, gia_vao, gia_ra, them}. Thieu khoa / url / mo hinh -> ThieuCauHinh (noi ro thieu gi, khong in khoa)."""
    env = os.environ if env is None else env
    P, md = ten.upper().replace("-", "_"), MAC_DINH.get(ten.lower(), {})
    khoa = env.get("SO_SANH_%s_KHOA" % P) or next((env[k] for k in md.get("khoa_env", ()) if env.get(k)), "")
    url, mo_hinh, nguon = env.get("SO_SANH_%s_URL" % P) or md.get("url", ""), env.get("SO_SANH_%s_MO_HINH" % P) or md.get("mo_hinh", ""), "env"
    if not khoa:
        d = (cc or _cc_switch)(env.get("SO_SANH_%s_CC" % P) or md.get("cc") or ten)
        if d.get("khoa"):
            khoa, url, mo_hinh, nguon = d["khoa"], env.get("SO_SANH_%s_URL" % P) or d.get("base_url") or url, \
                env.get("SO_SANH_%s_MO_HINH" % P) or d.get("model") or mo_hinh, "cc-switch:%s" % d.get("ten", "")
    thieu = [n for n, v in (("khoa", khoa), ("url", url), ("mo_hinh", mo_hinh)) if not v]
    if thieu:
        raise ThieuCauHinh("%s: thieu %s - dat SO_SANH_%s_KHOA/_URL/_MO_HINH (hoac them provider vao cc-switch o may nha)" % (ten, ", ".join(thieu), P))
    them = {}
    try:
        them = json.loads(env.get("SO_SANH_%s_THEM" % P) or "{}")
    except ValueError:
        pass
    return {"ten": ten, "url": url.rstrip("/") + "/chat/completions", "khoa": khoa, "mo_hinh": mo_hinh, "nguon": nguon,
            "gia_vao": _so(env, "SO_SANH_%s_GIA_VAO" % P), "gia_ra": _so(env, "SO_SANH_%s_GIA_RA" % P), "them": them if isinstance(them, dict) else {}}


def _post_that(d: dict, than: dict, timeout: int = 150) -> dict:
    from nhan import nc_tho as NT
    return NT._post(d, than, timeout)


# ------------------------------------------------------------------ ham cham
def _json_tu(text: str):
    """-> (obj, muc): 'sach' = ca tin nhan la JSON; 'rao' = phai gat hang rao ``` / chu thua; None = khong doc duoc."""
    t = (text or "").strip()
    try:
        return json.loads(t), "sach"
    except ValueError:
        pass
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    for c in ([m.group(1)] if m else []) + [t[t.find("{"):t.rfind("}") + 1], t[t.find("["):t.rfind("]") + 1]]:
        try:
            return json.loads(c), "rao"
        except ValueError:
            continue
    return None, None


def _co_so(x, dich, tol):
    try:
        return abs(float(x) - dich) <= tol
    except (TypeError, ValueError):
        return False


def cham_json_ky_luat(tra: dict) -> tuple:
    o, muc = _json_tu(tra["text"])
    if not isinstance(o, dict):
        return 0.0, "khong phai JSON object"
    d = 0.5 * (1.0 if muc == "sach" else 0.5) + 0.25 * _co_so(o.get("ngay_con_lai"), 29, 0) + 0.25 * (o.get("la_ngay_cuoi_tuan") is False)
    return d, "json %s; ngay_con_lai=%r; cuoi_tuan=%r" % (muc, o.get("ngay_con_lai"), o.get("la_ngay_cuoi_tuan"))


def _df_gia(n: int = 500):
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(7)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + abs(rng.normal(0, 0.003, n)))
    lo = np.minimum(o, c) * (1 - abs(rng.normal(0, 0.003, n)))
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "volume": rng.integers(100, 1000, n)},
                        index=pd.date_range("2020-01-01", periods=n, freq="D"))


def cham_spec_co_che(tra: dict, k: int = 5) -> tuple:
    o, muc = _json_tu(tra["text"])
    ds = o.get("co_che") if isinstance(o, dict) else o
    if not isinstance(ds, list):
        return 0.0, "khong co danh sach khai bao"
    from nhan import ngu_phap as NP
    df, tot, thay, da_thay = _df_gia(), 0, [], set()
    for i, s in enumerate(ds[:k]):
        try:
            loi = NP.kiem_khai_bao(s)
            if loi:
                thay.append("#%d cu phap: %s" % (i, loi[0][:60]))
                continue
            NP.sinh_tu_spec(s, df)
            khoa = json.dumps(s.get("vao"), sort_keys=True)
            if khoa in da_thay:
                thay.append("#%d trung dieu kien vao" % i)
                continue
            da_thay.add(khoa)
            tot += 1
        except Exception as e:                              # noqa: BLE001 - mot khai bao hong khong duoc lam chet ca bo
            thay.append("#%d %s: %s" % (i, type(e).__name__, str(e)[:50]))
    return tot / float(k), "%d/%d hop le va khac nhau%s" % (tot, k, ("; " + "; ".join(thay[:3])) if thay else "")


def cham_goi_cong_cu(tra: dict) -> tuple:
    tc = tra.get("tool_calls") or []
    if not tc:
        return 0.0, "khong goi cong cu (tra loi bang chu)"
    f = (tc[0].get("function") or {})
    try:
        a = json.loads(f.get("arguments") or "{}")
    except ValueError:
        return 0.25 if f.get("name") == "tim_quy_luat" else 0.0, "arguments khong phai JSON"
    if f.get("name") != "tim_quy_luat":
        return 0.0, "goi nham cong cu %r" % f.get("name")
    d = 0.4 + 0.2 * (str(a.get("ma", "")).upper() == "AUDCAD") + 0.2 * (str(a.get("khung", "")).upper() == "H4") + 0.2 * _co_so(a.get("so_null"), 200, 0)
    return d, "args=%s" % json.dumps(a, ensure_ascii=False)[:80]


def cham_trich_bang(tra: dict) -> tuple:
    t = tra["text"].lower().replace(",", ".")
    ok = ("buoc30" in t.replace(" ", "") or "buoc 30" in t, "13.26" in t, "3.5" in t)
    return sum(ok) / 3.0, "cau hinh=%s hold=%s dd=%s" % ok


def cham_cagr_maxdd(tra: dict) -> tuple:
    o, _ = _json_tu(tra["text"])
    if not isinstance(o, dict):
        return 0.0, "khong phai JSON"
    ok = (_co_so(o.get("tong_loi_pct"), 50.0, 0.1), _co_so(abs(float(o["max_dd_pct"])) if _co_so(o.get("max_dd_pct"), 0, 1e9) else None, 25.0, 0.1),
          _co_so(o.get("cagr_pct"), 22.47, 0.15))
    return sum(ok) / 3.0, "tong_loi=%s maxdd=%s cagr=%s" % ok


def cham_luat_chan(tra: dict) -> tuple:
    o, _ = _json_tu(tra["text"])
    ds = o.get("chan") if isinstance(o, dict) else o
    if not isinstance(ds, list) or len(ds) != 4:
        return 0.0, "can danh sach 4 gia tri true/false"
    dung = [True, False, True, True]
    n = sum(1 for a, b in zip(ds, dung) if a is b)
    return n / 4.0, "dung %d/4 (tra %s, dap an %s)" % (n, ds, dung)


KHOA_TOM_TAT = ("108", "2642", "khop", "mai")


def cham_tom_tat(tra: dict) -> tuple:
    t = tra["text"]
    thieu = [k for k in KHOA_TOM_TAT if k not in t.lower().replace(".", "")]
    nguon = set(re.findall(r"\d+", NGUON_TOM_TAT))
    bia = [x for x in re.findall(r"\d+", t) if x not in nguon]
    tu = len(t.split())
    d = max(0.0, (4 - len(thieu)) / 4.0 - 0.25 * len(bia)) * (1.0 if tu <= 70 else 0.5)
    return d, "thieu %s; so bia %s; %d tu" % (thieu or "-", bia[:4] or "-", tu)


def cham_tieng_viet(tra: dict) -> tuple:
    t = tra["text"].strip()
    cau = [x for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]
    ok = (len(cau) == 2, "\n" not in t and not re.search(r"(^|\s)[*#\-]\s|\*\*", t), "cache" in t.lower(),
          len(re.findall(r"[ăâêôơưđáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ]", t.lower())) >= 5)
    return sum(ok) / 4.0, "2 cau=%s khong markdown=%s co 'cache'=%s tieng Viet=%s" % ok


def cham_needle(tra: dict) -> tuple:
    return (1.0, "dung") if NEEDLE["ma"] in tra["text"] else (0.0, "khong thay ma %s" % NEEDLE["ma"])


NEEDLE: dict = {}
NGUON_TOM_TAT = ("BAO CAO DEM 02/10. (1) b test: 108 fail / 2642 pass / 46 skip (23 phut); phan lon fail do thieu data/ds/nao.db/config. "
                 "(2) b nc kiem 30 KHOP het cloud: sai 0, dung 6/7, bao dong gia 0. (3) b token: 60 goi, ngu canh TB 86k. "
                 "MT5 XM da tai, chu du an cai ngay mai.")
BANG_BAO_CAO = """| Cau hinh | train %/nam | DD | hold %/nam | DD | lo treo dinh | lenh/nam |
| buoc30 hs1,0 tp60 tia | 17,11 | -4,8 | 13,26 | -3,5 | 11,0% von | 578 |
| buoc20 hs1,3 tp60 tia | 11,47 | -4,1 | 10,19 | -1,8 | 5,9% von | 485 |
| buoc20 hs1,0 tp45 tia | 20,60 | -5,5 | 12,01 | -4,9 | 14,6% von | 618 |"""
TOOLS = [{"type": "function", "function": {"name": "tim_quy_luat", "description": "Tim quy luat tren doan kham pha cua mot ma",
          "parameters": {"type": "object", "properties": {"ma": {"type": "string"}, "khung": {"type": "string"}, "so_null": {"type": "integer"}},
                         "required": ["ma", "khung", "so_null"]}}},
         {"type": "function", "function": {"name": "xem_so_tay", "description": "Doc so tay nghien cuu", "parameters": {"type": "object", "properties": {}}}}]


def _nhac_spec() -> str:
    return ("Dua ra DUNG 5 khai bao co che vao lenh KHAC NHAU, tra ve MOT JSON object {\"co_che\": [ ... 5 phan tu ... ]}, khong chu nao khac.\n"
            "Moi phan tu: {\"ten\": str, \"co_che\": \"MOT cau (>= 25 ky tu) giai thich vi sao co nguoi tra tien cho phoi nhiem nay\", "
            "\"ho\": \"quay_ve_trung_binh\"|\"xu_huong\"|\"pha_vo\", \"chieu\": 1|-1, \"giu\": so nguyen 1..20, \"vao\": [dieu kien, ...], \"ra\": []}.\n"
            "Dieu kien: {\"trai\": toan_hang, \"phep\": \"<\"|\">\", \"phai\": toan_hang}. Toan hang: {\"hang\": so} hoac {\"chi_bao\": TEN, \"n\": so nguyen} "
            "voi TEN thuoc {rsi, sma, atr} (n 2..200), hoac {\"chi_bao\": \"ibs\"}.\n"
            "Vi du: {\"ten\":\"v\",\"co_che\":\"Gia dong cua o day bien do ngay thuong hoi lai vi nguoi ban thao chay.\",\"ho\":\"quay_ve_trung_binh\",\"chieu\":1,"
            "\"giu\":1,\"vao\":[{\"trai\":{\"chi_bao\":\"ibs\"},\"phep\":\"<\",\"phai\":{\"hang\":0.2}}],\"ra\":[]}")


def _nhac_luat() -> str:
    return ("Luat duyet he giao dich cua du an: he CHI bi CHAN neu khong co lai sau phi, HOAC maxDD >= 80%, HOAC cua so do sai (phi chi duoc khai "
            "chu khong do duoc, qua it lenh, an khe dao ngay). Thua mua-giu o cung rui ro, hay kieu martingale/DCA/luoi chi la NHAN canh bao, KHONG chan.\n"
            "Cho 4 he: (a) lai +3%/nam sau phi, maxDD 85%, don bay 5. (b) lai +40%/nam sau phi, maxDD 60%, thua mua-giu o cung rui ro, kieu martingale. "
            "(c) lai -2%/nam sau phi, maxDD 10%. (d) lai +10%/nam, maxDD 30%, nhung phi chi do tin = KHAI (khong do duoc).\n"
            "Tra ve DUNG MOT JSON {\"chan\": [true|false, true|false, true|false, true|false]} theo thu tu a,b,c,d, khong chu nao khac.")


def tao_task(dai: bool = False) -> list[dict]:
    ts = [
        {"ten": "json_ky_luat", "cham": cham_json_ky_luat, "max_tokens": 200,
         "nhac": 'Hom nay la 02/10/2026 (nam khong nhuan). Tra ve DUNG MOT JSON object, khong markdown, khong chu nao khac: {"ngay_con_lai": <so ngay tu mai den het thang 10>, "la_ngay_cuoi_tuan": true|false}'},
        {"ten": "spec_co_che", "cham": cham_spec_co_che, "max_tokens": 1800, "nhac": _nhac_spec()},
        {"ten": "goi_cong_cu", "cham": cham_goi_cong_cu, "max_tokens": 300, "tools": TOOLS,
         "nhac": "Tim quy luat cho AUDCAD khung H4 voi 200 phep null."},
        {"ten": "trich_bang_bao_cao", "cham": cham_trich_bang, "max_tokens": 200,
         "nhac": "Bang ket qua luoi AUDCAD:\n%s\nCau hinh nao co 'hold %%/nam' cao nhat, va DD hold cua no la bao nhieu? Tra loi mot dong." % BANG_BAO_CAO},
        {"ten": "tinh_cagr_maxdd", "cham": cham_cagr_maxdd, "max_tokens": 300,
         "nhac": 'Von theo thoi gian (cach deu, tong 2 nam, 8 diem): [100, 110, 95, 120, 90, 130, 125, 150]. Tra ve DUNG MOT JSON: {"tong_loi_pct": ..., "max_dd_pct": ..., "cagr_pct": ...} (max_dd_pct la so duong).'},
        {"ten": "luat_chan", "cham": cham_luat_chan, "max_tokens": 200, "nhac": _nhac_luat()},
        {"ten": "tom_tat_trung_thuc", "cham": cham_tom_tat, "max_tokens": 250,
         "nhac": "Tom tat bao cao sau trong TOI DA 3 dong (<= 60 tu), chi dung so co trong bao cao, khong them suy dien:\n" + NGUON_TOM_TAT},
        {"ten": "tieng_viet_2_cau", "cham": cham_tieng_viet, "max_tokens": 200,
         "nhac": "Giai thich 'prompt cache' trong DUNG 2 cau tieng Viet co dau, khong markdown, khong xuong dong, phai chua tu 'cache'."},
    ]
    if dai:
        ma = "%08x" % random.Random(11).getrandbits(32)
        NEEDLE.clear()
        NEEDLE["ma"] = ma
        tl = []
        for p in sorted((LAB / "tai_lieu").glob("*.md"))[:6] + [LAB / "CLAUDE.md"]:
            try:
                tl.append(p.read_text(encoding="utf-8", errors="replace")[:9000])
            except OSError:
                pass
        van = "\n\n".join(tl) or ("lorem ipsum " * 2000)
        mid = len(van) // 2
        van = van[:mid] + "\n\n[MA_XAC_NHAN_DUY_NHAT = %s]\n\n" % ma + van[mid:]
        ts.append({"ten": "needle_dai", "cham": cham_needle, "max_tokens": 60,
                   "nhac": van + "\n\n---\nTrong van ban tren co dung mot dong MA_XAC_NHAN_DUY_NHAT. Chep lai DUNG gia tri cua no, khong gi khac."})
    return ts


# ------------------------------------------------------------------ chay
def goi_mot(ncc: dict, task: dict, post=None, timeout: int = 150) -> dict:
    than = {"model": ncc["mo_hinh"], "max_tokens": task.get("max_tokens", 400), "temperature": 0.2,
            "messages": [{"role": "user", "content": task["nhac"]}]}
    if task.get("tools"):
        than["tools"] = task["tools"]
    than.update(ncc.get("them") or {})
    t0 = time.time()
    try:
        r = (post or _post_that)(ncc, than, timeout)
    except Exception as e:                                  # noqa: BLE001
        return {"loi": "%s: %s" % (type(e).__name__, str(e)[:160]), "giay": round(time.time() - t0, 2), "tok_vao": 0, "tok_ra": 0}
    m = ((r.get("choices") or [{}])[0].get("message") or {})
    u = r.get("usage") or {}
    return {"text": (m.get("content") or ""), "tool_calls": m.get("tool_calls") or [], "giay": round(time.time() - t0, 2),
            "tok_vao": int(u.get("prompt_tokens") or 0), "tok_ra": int(u.get("completion_tokens") or 0)}


def so_sanh(ds_ncc: list[dict], ds_task: list[dict], lan: int = LAN_MAC_DINH, post=None) -> dict:
    kq: dict = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "lan": lan, "task": [t["ten"] for t in ds_task], "ncc": {}}
    for ncc in ds_ncc:
        ra = {"mo_hinh": ncc["mo_hinh"], "nguon": ncc["nguon"], "task": {}, "tok_vao": 0, "tok_ra": 0, "loi": 0, "giay": []}
        for t in ds_task:
            diem, ghi = [], []
            for _ in range(lan):
                tra = goi_mot(ncc, t, post)
                ra["tok_vao"] += tra["tok_vao"]
                ra["tok_ra"] += tra["tok_ra"]
                ra["giay"].append(tra["giay"])
                if tra.get("loi"):
                    ra["loi"] += 1
                    diem.append(0.0)
                    ghi.append("LOI " + tra["loi"])
                    continue
                d, g = t["cham"](tra)
                diem.append(round(d, 3))
                ghi.append(g)
            ra["task"][t["ten"]] = {"diem": diem, "tb": round(sum(diem) / len(diem), 3), "ghi": ghi}
        ra["tb"] = round(statistics.mean(v["tb"] for v in ra["task"].values()), 3)
        ra["giay_trung_vi"] = round(statistics.median(ra["giay"]), 2) if ra["giay"] else 0.0
        gv, gr = ncc.get("gia_vao"), ncc.get("gia_ra")
        ra["chi_phi_usd"] = round(ra["tok_vao"] * gv / 1e6 + ra["tok_ra"] * gr / 1e6, 5) if gv is not None and gr is not None else None
        kq["ncc"][ncc["ten"]] = ra
    kq["ket_luan"] = ket_luan(kq)
    return kq


def ket_luan(kq: dict) -> str:
    t = list(kq["ncc"].items())
    if len(t) < 2:
        return "Chi co 1 nha cung cap: khong co gi de so sanh."
    (a, ra), (b, rb) = t[0], t[1]
    thang = sum(1 for k in kq["task"] if ra["task"][k]["tb"] > rb["task"][k]["tb"] + 0.05)
    thua = sum(1 for k in kq["task"] if rb["task"][k]["tb"] > ra["task"][k]["tb"] + 0.05)
    hoa = len(kq["task"]) - thang - thua
    chenh = ra["tb"] - rb["tb"]
    ban = "%s thang %d / hoa %d / thua %d tren %d task; diem TB %s %.3f vs %s %.3f." % (a, thang, hoa, thua, len(kq["task"]), a, ra["tb"], b, rb["tb"])
    if abs(chenh) >= 0.1:
        return ban + " CHON %s (chenh >= 0,1)." % (a if chenh > 0 else b)
    ca, cb = ra.get("chi_phi_usd"), rb.get("chi_phi_usd")
    if ca is not None and cb is not None:
        return ban + " Diem GAN NHU NHAU (chenh < 0,1, mau nho): chon RE HON = %s (%.5f vs %.5f USD)." % (a if ca <= cb else b, ca, cb)
    return ban + " Diem gan nhu nhau; chua khai gia (SO_SANH_<P>_GIA_VAO/_GIA_RA) nen chua chon duoc theo chi phi (token ra: %s %d, %s %d)." % (a, ra["tok_ra"], b, rb["tok_ra"])


def bao_cao(kq: dict) -> str:
    ten = list(kq["ncc"])
    dong = ["SO SANH MODEL RE - %d nha cung cap, %d task, %d lan (%s)" % (len(ten), len(kq["task"]), kq["lan"], kq["luc"]),
            "%-22s" % "task" + "".join("%12s" % n[:11] for n in ten)]
    for k in kq["task"]:
        dong.append("%-22s" % k + "".join("%12.2f" % kq["ncc"][n]["task"][k]["tb"] for n in ten))
    dong.append("%-22s" % "DIEM TB" + "".join("%12.3f" % kq["ncc"][n]["tb"] for n in ten))
    dong.append("%-22s" % "token vao/ra" + "".join("%12s" % ("%dk/%dk" % (kq["ncc"][n]["tok_vao"] // 1000, kq["ncc"][n]["tok_ra"] // 1000)) for n in ten))
    dong.append("%-22s" % "giay trung vi/goi" + "".join("%12.1f" % kq["ncc"][n]["giay_trung_vi"] for n in ten))
    dong.append("%-22s" % "chi phi USD" + "".join("%12s" % ("chua khai" if kq["ncc"][n]["chi_phi_usd"] is None else "%.4f" % kq["ncc"][n]["chi_phi_usd"]) for n in ten))
    dong.append("%-22s" % "loi goi" + "".join("%12d" % kq["ncc"][n]["loi"] for n in ten))
    dong.append("mo hinh: " + " · ".join("%s=%s (%s)" % (n, kq["ncc"][n]["mo_hinh"], kq["ncc"][n]["nguon"]) for n in ten))
    dong.append("KET LUAN: " + kq["ket_luan"])
    return "\n".join(dong)


def _khai() -> int:
    for ten in ("deepseek", "qwen"):
        try:
            d = nha_cung_cap(ten)
            print("%-9s OK  mo_hinh=%s nguon=%s url=%s gia=%s/%s" % (ten, d["mo_hinh"], d["nguon"], d["url"], d["gia_vao"], d["gia_ra"]))
        except ThieuCauHinh as e:
            print("%-9s THIEU  %s" % (ten, e))
    return 0


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    if "--khai" in argv:
        return _khai()

    def co(ten, mac_dinh=None):
        return argv[argv.index(ten) + 1] if ten in argv and argv.index(ten) + 1 < len(argv) else mac_dinh
    ten = [x for x in (co("--nha-cung-cap", "deepseek,qwen") or "").split(",") if x]
    try:
        ds_ncc = [nha_cung_cap(x) for x in ten]
    except ThieuCauHinh as e:
        print("THIEU CAU HINH:", e)
        print("Xem cach giai quyet: b so-sanh --khai")
        return 2
    ds_task = tao_task(dai="--dai" in argv)
    loc = [x for x in (co("--task") or "").split(",") if x]
    if loc:
        ds_task = [t for t in ds_task if t["ten"] in loc]
    kq = so_sanh(ds_ncc, ds_task, lan=int(co("--lan", LAN_MAC_DINH)))
    f = LAB / "reports" / ("SO_SANH_LLM_%s.json" % time.strftime("%Y%m%d_%H%M"))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(kq, ensure_ascii=False, indent=1) if "--json" in argv else bao_cao(kq))
    print("chi tiet: %s" % f.relative_to(LAB))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
