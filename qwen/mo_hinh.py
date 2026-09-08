# -*- coding: utf-8 -*-
"""mo_hinh.py - Duong LLM cho LangChain: khoa doc TAI CHO tu cc-switch.

## Khoa nam o dau, va vi sao khong chep sang day

`~/.cc-switch/cc-switch.db`, bang `providers`, khop ten bang CHUOI CON. Mot khoa
API chi nen ton tai o MOT noi - chep di la tao them mot cho de ro ri va mot ban
co the lech khi chu du an doi khoa.

## Vi sao goi THANG api.ai-box.vn chu khong qua cau noi 8317

Cau noi `127.0.0.1:8317` dung cho **Codex CLI**, vi Codex doi `/v1/responses` ma
AI Box khong co. LangChain noi `/chat/completions` san - di qua cau noi la them
mot chang dich Responses<->Chat vo ich. Do 08/09: thang 2,1s, qua cau noi 3,2s.
Va cau noi la mot tien trinh rieng co the dang tat.

Neu muon ep di qua cau noi (vd de xem log tung loi goi): dat
`"qua_cau_noi": true` trong `config/qwen.json`.

## Bay da sap - kiem truoc khi tin mot ket qua boc AM

`max_tokens` thap lam mo hinh **bi cat giua chung** roi tra rong - doc y het
"mo hinh kem". Trong me do 05/09 co 4 mo hinh ra dung 1.019-1.200 token, tuc
cham tran. Luon kiem `completion_tokens` co sat tran khong.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from . import cau_hinh as CH

CC_SWITCH_DB = Path.home() / ".cc-switch" / "cc-switch.db"


def tu_cc_switch(ten: str = "aibox") -> dict:
    if not CC_SWITCH_DB.exists():
        return {}
    cn = None
    try:
        cn = sqlite3.connect("file:%s?mode=ro" % CC_SWITCH_DB, uri=True)
        cn.row_factory = sqlite3.Row
        for r in cn.execute("SELECT name, settings_config FROM providers"):
            if ten.lower() not in str(r["name"] or "").lower():
                continue
            cfg = json.loads(r["settings_config"] or "{}")
            khoa = (cfg.get("auth") or {}).get("OPENAI_API_KEY") or ""
            if not khoa:
                continue
            tho = str(cfg.get("config") or "")
            u = re.search(r'base_url\s*=\s*"([^"]+)"', tho)
            m = re.search(r'^model\s*=\s*"([^"]+)"', tho, re.M)
            return {"khoa": khoa, "ten": r["name"],
                    "base_url": (u.group(1) if u else "").rstrip("/"),
                    "model": m.group(1) if m else ""}
    except Exception:
        return {}
    finally:
        if cn is not None:
            try:
                cn.close()
            except Exception:
                pass
    return {}


def duong(c: dict | None = None) -> dict:
    """Tra {khoa, base_url, model} da giai quyet xong moi uu tien."""
    c = c or CH.nap()
    cc = tu_cc_switch(c["cc_switch_provider"])
    if not cc.get("khoa"):
        raise SystemExit(
            "!! khong tim thay provider chua '%s' trong %s.\n"
            "   Da tung mat ca duong LLM vi lech TEN provider (06/09): moi loi goi\n"
            "   tra 'thieu OPENAI_API_KEY' va khong ai bao. Mo cc-switch xem ten that,\n"
            "   roi sua `cc_switch_provider` trong config/qwen.json."
            % (c["cc_switch_provider"], CC_SWITCH_DB))
    base = cc["base_url"]
    if not c.get("qua_cau_noi") and ("127.0.0.1" in base or "localhost" in base):
        base = c["base_url"]        # thang, khong qua cau noi Codex
    return {"khoa": cc["khoa"], "base_url": base or c["base_url"],
            "model": c["model"] or cc.get("model") or "qwen3.7-flash",
            "provider": cc["ten"]}


def chat(c: dict | None = None, model: str | None = None, cong_cu=None):
    """Dung mot ChatOpenAI da tro dung duong. Goi la co the .bind_tools()."""
    from langchain_openai import ChatOpenAI
    c = c or CH.nap()
    d = duong(c)
    llm = ChatOpenAI(
        model=model or d["model"],
        api_key=d["khoa"],
        base_url=d["base_url"],
        temperature=float(c["temperature"]),
        max_tokens=int(c["max_tokens"]),
        timeout=float(c["timeout_giay"]),
        max_retries=int(c["so_lan_thu_lai"]),
    )
    return llm.bind_tools(cong_cu) if cong_cu else llm


def kiem() -> dict:
    """Kiem duong con song. Chay: python -m qwen.mo_hinh"""
    import time
    c = CH.nap()
    d = duong(c)
    ra = {"provider": d["provider"], "base_url": d["base_url"], "model": d["model"]}
    for m in (d["model"], c["model_du_phong"]):
        t = time.time()
        try:
            r = chat(c, model=m).invoke("Tra loi dung mot tu: OK")
            ok = (r.content or "").strip()[:20]
            sd = getattr(r, "usage_metadata", None) or {}
            ra[m] = {"tra": ok, "giay": round(time.time() - t, 1),
                     "token_ra": sd.get("output_tokens"),
                     "cham_tran": sd.get("output_tokens", 0) >= int(c["max_tokens"]) - 5}
        except Exception as e:
            ra[m] = {"loi": "%s: %s" % (type(e).__name__, str(e)[:200])}
    return ra


if __name__ == "__main__":
    print(json.dumps(kiem(), ensure_ascii=False, indent=1))
