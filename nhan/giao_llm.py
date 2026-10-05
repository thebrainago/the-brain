# -*- coding: utf-8 -*-
"""giao_llm.py - goi model re qua AI Box tu phien cloud, ghi so chi, giu tran ngan sach (tai_lieu/PHUONG_AN_LLM.md).
Khong doc / in khoa (proxy gan san). Chi viet vao reports/deepseek/so_chi.jsonl. Khong niem phong, khong sua kho."""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

URL = "https://api.ai-box.vn/v1/chat/completions"
SO_CHI = Path(__file__).resolve().parent.parent / "reports" / "deepseek" / "so_chi.jsonl"
# tang -> (model, d/1M vao, d/1M ra, d/1M cache, tham so tat suy luan)
TANG = {
    "T1": ("qwen3.8-flash", 832, 2444, 83.2, {"enable_thinking": False}),
    "T2": ("ds/deepseek-flash", 2600, 10400, 52, {"thinking": {"type": "disabled"}}),
    "T3": ("kimi-k2.7-code", 4940, 20800, 988, {}),
    "T4": ("ds/deepseek-v4-pro", 11440, 34320, 379.6, {"thinking": {"type": "disabled"}}),
    "T4m": ("qwen3.8-max-0902", 10400, 31200, 650, {"enable_thinking": False}),
}


def da_chi_hom_nay() -> float:
    if not SO_CHI.exists():
        return 0.0
    ngay = time.strftime("%Y-%m-%d")
    return sum(j.get("dong", 0) for j in map(json.loads, SO_CHI.read_text("utf-8").splitlines()) if j.get("ngay") == ngay)


def goi(tang: str, prompt: str, max_tokens: int = 1500, viec: str = "", tran_ngay: float | None = None, he: str = "") -> dict:
    """Tra {'noi_dung','dong','vao','ra'}; vuot tran ngay -> nem RuntimeError (khong im lang)."""
    if tran_ngay is not None and da_chi_hom_nay() >= tran_ngay:
        raise RuntimeError("vuot tran chi ngay %.0f d" % tran_ngay)
    model, gv, gr, gc, them = TANG[tang]
    msgs = ([{"role": "system", "content": he}] if he else []) + [{"role": "user", "content": prompt}]
    body = {"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": 0.2, **them}
    t0 = time.time()
    r = requests.post(URL, json=body, timeout=120)
    r.raise_for_status()
    j = r.json()
    u = j.get("usage", {})
    vao, ra = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    cache = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    dong = ((vao - cache) * gv + cache * gc + ra * gr) / 1e6
    nd = (j["choices"][0]["message"].get("content") or "")
    SO_CHI.parent.mkdir(parents=True, exist_ok=True)
    with SO_CHI.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ngay": time.strftime("%Y-%m-%d"), "tang": tang, "model": model, "viec": viec, "vao": vao, "cache": cache,
                            "ra": ra, "dong": round(dong, 3), "giay": round(time.time() - t0, 1)}) + "\n")
    return {"noi_dung": nd, "dong": dong, "vao": vao, "ra": ra}


if __name__ == "__main__":
    print(goi("T1", "Tra loi dung 1 chu: OK", 20, "thu"))
