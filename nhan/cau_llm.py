# -*- coding: utf-8 -*-
"""cau_llm.py - CAU NOI LLM cho buoc BOC TACH / DICH cua ong dan (18/10/2026).

Dung lai cong AI Box cua `phong_hop/hop.py` (OpenAI-compatible, deepseek / glm / kimi / qwen). KHOA CHI DOC TU BIEN
MOI TRUONG, khong bao gio ghi vao git / file:
  AIBOX_API_KEY (bat buoc, tru khi proxy cloud tu chen), AIBOX_BASE_URL (mac dinh https://api.ai-box.vn/v1),
  BRAIN_LLM_MODEL (mac dinh ds/deepseek-v4-pro).
Khong co khoa -> moi ham tra {"trang_thai": "CHUA_CHAY_DUOC", ...} va KHONG goi mang (bo qua em). Ket qua cua LLM chi la
DU LIEU (spec JSON theo `nhan/ngu_phap.py` + vai tro co che) - khong bao gio exec ma LLM tra ve; spec phai qua
`kiem_spec` (co `vao`, chi bao biet) truoc khi dung.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request

MAC_DINH_MODEL = "ds/deepseek-v4-pro"
TRAN_MA = 16000

HE_THONG = (
    "Ban la ky su dich chien luoc giao dich. Doc MA NGUON (MQL4/MQL5/Pine/Python) va tra ve DUY NHAT mot JSON, khong giai "
    "thich. Khong bia: phan nao khong chac thi de trong va ghi vao 'chua_dich'.")

MAU_BOC = """Tra JSON dang:
{"loai": "he_hoan_thien|co_che|tien_ich|mo_ta",
 "spec": [ {"ten": str, "chieu": 1|-1, "vao": [{"trai": {...}, "phep": ">"|"<"|">="|"<=", "phai": {...}}]} ],
 "co_che": [ {"vai_tro": "nguon_lenh|bo_loc|moc_vung|quan_li|go_lenh", "ten": str, "mo_ta": str, "tham": {}} ],
 "quan_tri": {"tp": str, "sl": str, "dca": str, "hedge": str, "trailing": str, "chot_ro": str, "go_lenh": str},
 "tham_so": {"ten_input": [gia_tri_thap, mac_dinh, cao]},
 "chua_dich": [str]}
Toan hang trong 'vao' dung dang cua ngu phap The Brain, vi du {"chi_bao": "gia", "cot": "close"}, {"chi_bao": "sma", "n": 50},
{"chi_bao": "rsi", "n": 14}, {"chi_bao": "hang", "gia_tri": 30}. Tin hieu biet tai nen DA DONG.
MA NGUON (%s):
```
%s
```"""


def co_khoa() -> bool:
    return bool(os.environ.get("AIBOX_API_KEY") or os.environ.get("BRAIN_LLM_PROXY"))


def goi(nguoi_dung: str, he_thong: str = HE_THONG, model: str | None = None, max_tokens: int = 6000,
        han_giay: int = 180) -> dict:
    """-> {"trang_thai": "OK"|"CHUA_CHAY_DUOC"|"LOI", "van_ban": str, "ghi_chu": str}. Stream nhu phong_hop."""
    if not co_khoa():
        return {"trang_thai": "CHUA_CHAY_DUOC", "van_ban": "", "ghi_chu": "khong co AIBOX_API_KEY trong bien moi truong"}
    base = os.environ.get("AIBOX_BASE_URL", "https://api.ai-box.vn/v1").rstrip("/")
    body = json.dumps({"model": model or os.environ.get("BRAIN_LLM_MODEL", MAC_DINH_MODEL), "temperature": 0.1,
                       "max_tokens": max_tokens, "stream": True,
                       "messages": [{"role": "system", "content": he_thong}, {"role": "user", "content": nguoi_dung}]}).encode()
    h = {"Content-Type": "application/json"}
    if os.environ.get("AIBOX_API_KEY"):
        h["Authorization"] = "Bearer " + os.environ["AIBOX_API_KEY"]
    txt, t0 = "", time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(base + "/chat/completions", data=body, headers=h),
                                    timeout=han_giay) as r:
            for dong in r:
                dong = dong.decode("utf-8", "replace").strip()
                if not dong.startswith("data:") or dong.endswith("[DONE]"):
                    continue
                try:
                    ch = json.loads(dong[5:]).get("choices") or []
                except ValueError:
                    continue
                if ch:
                    txt += (ch[0].get("delta") or {}).get("content") or ""
    except Exception as e:  # noqa: BLE001
        return {"trang_thai": "LOI", "van_ban": txt, "ghi_chu": str(e)[:200]}
    return {"trang_thai": "OK" if txt.strip() else "LOI", "van_ban": txt.strip(),
            "ghi_chu": "%.0fs" % (time.time() - t0)}


def _json_trong(van_ban: str) -> dict | None:
    m = re.search(r"\{.*\}", van_ban or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None


def kiem_spec(sp: dict) -> list[str]:
    """Kiem toi thieu mot spec LLM tra ve truoc khi dung (khong exec gi)."""
    loi = []
    if not isinstance(sp, dict) or not sp.get("vao"):
        return ["spec khong co 'vao'"]
    for d in sp["vao"]:
        if not isinstance(d, dict) or d.get("phep") not in (">", "<", ">=", "<=", "cat_len", "cat_xuong"):
            loi.append("dieu kien hong: %s" % str(d)[:80])
    if int(sp.get("chieu", 1) or 1) not in (1, -1):
        loi.append("chieu khong phai 1/-1")
    return loi


def boc_tach(ma_nguon: str, ngon_ngu: str = "MQL5") -> dict:
    """Ma nguon -> {trang_thai, loai, spec[], co_che[], quan_tri{}, tham_so{}, chua_dich[]}. Khong khoa -> CHUA_CHAY_DUOC."""
    r = goi(MAU_BOC % (ngon_ngu, (ma_nguon or "")[:TRAN_MA]))
    if r["trang_thai"] != "OK":
        return {"trang_thai": r["trang_thai"], "ghi_chu": r["ghi_chu"]}
    d = _json_trong(r["van_ban"])
    if d is None:
        return {"trang_thai": "LOI", "ghi_chu": "LLM khong tra JSON"}
    spec_ok = []
    for sp in d.get("spec") or []:
        loi = kiem_spec(sp)
        if loi:
            d.setdefault("chua_dich", []).extend(loi)
        else:
            spec_ok.append(sp)
    d["spec"] = spec_ok
    d["trang_thai"] = "OK"
    d["nhan"] = "LLM (%s) - can MT5 xac nhan" % os.environ.get("BRAIN_LLM_MODEL", MAC_DINH_MODEL)
    return d
