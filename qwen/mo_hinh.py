# -*- coding: utf-8 -*-
"""mo_hinh.py - Duong LLM cho LangChain: khoa doc TAI CHO tu cc-switch.

## Khoa nam o dau, va vi sao khong chep sang day

(1) bien moi truong `AIBOX_API_KEY` (may nha: bien User; phien cloud / may khong co
cc-switch: cai dat moi truong), roi (2) `~/.cc-switch/cc-switch.db`, bang
`providers`, khop ten bang CHUOI CON. Khoa KHONG bao gio nam trong repo / thu / log:
chep di la tao them mot cho de ro ri va mot ban co the lech khi chu du an doi khoa.

## Model mac dinh + du phong (thu nha c91d, 03/10/2026)

`config/qwen.json`: `model` = `ds/deepseek-flash` (viec khoi luong lon: nhanh, it token),
`model_du_phong` = `qwen3.8-max-0902` (suy luan sau: cham, nhieu token hon).
`ke_hoach_thu()`: model dau thu `leo_thang_sau_lan_sai` (2) lan, KHONG duoc thi moi toi
model du phong - mot loi le te khong dang tra gia model dat hon. `sau=True` = viec can
suy luan sau, di thang model du phong.

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
import os
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
    """Tra {khoa, base_url, model, provider, nguon} da giai quyet xong moi uu tien (env truoc, cc-switch sau)."""
    c = c or CH.nap()
    khoa_env = (os.environ.get("AIBOX_API_KEY") or "").strip()
    if khoa_env:
        cc = {"khoa": khoa_env, "ten": "env:AIBOX_API_KEY", "base_url": "", "model": ""}
        nguon = "env:AIBOX_API_KEY"
    else:
        cc = tu_cc_switch(c["cc_switch_provider"])
        nguon = "cc-switch:%s" % cc.get("ten", "")
    if not cc.get("khoa"):
        raise SystemExit(
            "!! khong co khoa AI Box: bien moi truong AIBOX_API_KEY trong, va khong tim thay\n"
            "   provider chua '%s' trong %s.\n"
            "   Da tung mat ca duong LLM vi lech TEN provider (06/09): moi loi goi\n"
            "   tra 'thieu OPENAI_API_KEY' va khong ai bao. Mo cc-switch xem ten that,\n"
            "   roi sua `cc_switch_provider` trong config/qwen.json (hoac dat AIBOX_API_KEY)."
            % (c["cc_switch_provider"], CC_SWITCH_DB))
    base = cc["base_url"]
    if not c.get("qua_cau_noi") and ("127.0.0.1" in base or "localhost" in base):
        base = c["base_url"]        # thang, khong qua cau noi Codex
    return {"khoa": cc["khoa"], "base_url": base or c["base_url"],
            "model": c["model"] or cc.get("model") or CH.MAC_DINH["model"],
            "provider": cc["ten"], "nguon": nguon}


def thu_tu_model(c: dict | None = None, sau: bool = False) -> list[str]:
    """[mac dinh, du phong], bo ten rong va ten trung; `sau=True` dao thu tu (viec can suy luan sau)."""
    c = c or CH.nap()
    ds = []
    for m in (c.get("model"), c.get("model_du_phong")):
        m = str(m or "").strip()
        if m and m not in ds:
            ds.append(m)
    return ds[::-1] if sau else ds


def ke_hoach_thu(c: dict | None = None, sau: bool = False) -> list[str]:
    """Cac model THU LAN LUOT cho MOT viec: model dau `leo_thang_sau_lan_sai` lan, moi model sau 1 lan.

    Vi sao hai lan roi moi doi (thu nha c91d): mot loi le te (mang chap chon, mot lan tra rong)
    khong dang tra gia model manh - cham hon ~5 lan va ra nhieu token hon (do 03/10: 15,9 s
    vs 3,1 s); hai lan lien tiep la model nay khong lam duoc viec nay.
    """
    c = c or CH.nap()
    ds = thu_tu_model(c, sau)
    if not ds:
        return []
    return [ds[0]] * max(1, int(c.get("leo_thang_sau_lan_sai") or 2)) + ds[1:]


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
    for m in thu_tu_model(c):
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
