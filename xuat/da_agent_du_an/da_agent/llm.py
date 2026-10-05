# -*- coding: utf-8 -*-
"""llm.py - goi model qua AI Box (kieu OpenAI). Khoa do proxy cua moi truong gan san: KHONG doc / in khoa. Moi cuoc goi ghi so chi."""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import requests

URL = "https://api.ai-box.vn/v1/chat/completions"
# ten -> (model, d vao, d ra, d cache, tham so tat suy luan). Gia: tai_lieu/BANG_GIA_AIBOX.md (d / 1 trieu token)
MODEL = {
    "re": ("qwen3.8-flash", 832, 2444, 83.2, {"enable_thinking": False}),
    "nhanh": ("ds/deepseek-flash", 2600, 10400, 52, {"thinking": {"type": "disabled"}}),
    "manh": ("qwen3.8-max-0902", 10400, 31200, 650, {"enable_thinking": False}),
    "pro": ("ds/deepseek-v4-pro", 11440, 34320, 379.6, {"thinking": {"type": "disabled"}}),
}
_khoa = threading.Lock()


def _dau() -> dict:
    """Trong cloud Claude Code, proxy tu gan khoa. Ngoai do dat bien moi truong AIBOX_API_KEY (khong bao gio ghi vao tep)."""
    k = os.environ.get("AIBOX_API_KEY")
    return {"Authorization": "Bearer " + k} if k else {}


def goi(ten_model: str, he: str, nguoi: str, max_tokens: int = 1500, so_chi: Path | None = None, nhan: str = "", temperature: float = 0.2) -> dict:
    model, gv, gr, gc, them = MODEL[ten_model]
    body = {"model": model, "messages": [{"role": "system", "content": he}, {"role": "user", "content": nguoi}],
            "max_tokens": max_tokens, "temperature": temperature, **them}
    t0 = time.time()
    last = None
    for lan in range(3):                       # loi mang / 5xx: thu lai toi da 3 lan, khong im lang
        try:
            r = requests.post(URL, json=body, timeout=180, headers=_dau())
            if r.status_code >= 500:
                raise RuntimeError("HTTP %d" % r.status_code)
            r.raise_for_status()
            break
        except Exception as e:                  # noqa: BLE001
            last = e
            time.sleep(2 * (lan + 1))
    else:
        raise RuntimeError("goi %s hong 3 lan: %s" % (model, last))
    j = r.json()
    u = j.get("usage", {})
    vao, ra = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    cache = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    dong = ((vao - cache) * gv + cache * gc + ra * gr) / 1e6
    nd = j["choices"][0]["message"].get("content") or ""
    if so_chi:
        with _khoa:
            so_chi.parent.mkdir(parents=True, exist_ok=True)
            with so_chi.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"luc": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": model, "nhan": nhan, "vao": vao, "cache": cache,
                                    "ra": ra, "dong": round(dong, 3), "giay": round(time.time() - t0, 1)}) + "\n")
    return {"noi_dung": nd, "dong": dong, "vao": vao, "ra": ra, "ket_thuc": j["choices"][0].get("finish_reason")}
