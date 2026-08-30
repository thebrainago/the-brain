# -*- coding: utf-8 -*-
r"""rem_via_tele.py - Cau noi THE BRAIN qua Telegram.
Ban nhan tin Telegram -> bot -> xu ly lenh -> tra loi. Lenh thuong duoc ghi vao
inbox (reports/tele_inbox.json) cho agent xu ly khi chay.
Lenh:
  /status  : trang thai he thong (3 tru + heartbeat).
  /bao_cao : tom tat bao cao moi nhat.
  /ket_qua : ket qua quantlab moi nhat.
  /help    : danh sach lenh.
Cau hinh: lab/config/tele_bridge.json
  { "bot_token": "...", "api_id": 123456, "api_hash": "...", "chat_id": 123456789 }
Lay: bot_token tu @BotFather; api_id/api_hash tu https://my.telegram.org; chat_id = id ban.
Chay:  python rem_via_tele.py
"""
import sys, json, os, time, pathlib
from pathlib import Path

LAB = pathlib.Path(__file__).parent
CFG = LAB / "config" / "tele_bridge.json"
INBOX = LAB / "reports" / "tele_inbox.json"

def _doc_cau_hinh():
    if CFG.exists():
        try:
            return json.loads(CFG.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {}

def _ghi_inbox(noi_dung):
    lst = []
    if INBOX.exists():
        try:
            lst = json.loads(INBOX.read_text(encoding="utf-8-sig"))
        except Exception:
            lst = []
    lst.append({"luc": time.time(), "luc_s": time.strftime("%Y-%m-%d %H:%M:%S"),
                "noi_dung": noi_dung})
    INBOX.write_text(json.dumps(lst, ensure_ascii=False, indent=1), encoding="utf-8")

def _status():
    lines = []
    hb = LAB / "reports" / "seek_heartbeat.txt"
    lines.append("HEARTBEAT: " + (hb.read_text(encoding="utf-8-sig").strip() if hb.exists() else "KHONG RUNNING"))
    st = LAB / "ket_hop_state.json"
    if st.exists():
        try:
            j = json.loads(st.read_text(encoding="utf-8-sig"))
            lines.append("3 TRU (lan chay gan nhat %s):" % j.get("luc", "?"))
            for t, v in j.get("tru", {}).items():
                lines.append(f"  {t}: {v.get('thoi_gian')} rc={v.get('rc')}")
        except Exception:
            pass
    return "\n".join(lines)

def _bao_cao():
    f = LAB / "reports" / "TONG_HOP_3_TRU.md"
    if f.exists():
        return f.read_text(encoding="utf-8-sig")[:1000]
    return "chua co bao cao"

def _ket_qua():
    f = LAB / "quant" / "ket_hop_hoc.json"
    if f.exists():
        try:
            j = json.loads(f.read_text(encoding="utf-8-sig"))
            return json.dumps(j, ensure_ascii=False)[:800]
        except Exception:
            pass
    return "chua co ket qua quant"

def xu_ly(van_ban):
    v = (van_ban or "").strip()
    if v == "/status": return _status()
    if v == "/bao_cao": return _bao_cao()
    if v == "/ket_qua": return _ket_qua()
    if v == "/help": return "/status /bao_cao /ket_qua\nTin nhan thuong -> ghi vao inbox cho agent."
    _ghi_inbox(v)
    return "Da nhan, ghi vao viec cho THE BRAIN xu ly. (ban co the /status, /bao_cao, /ket_qua)"

def main():
    cfg = _doc_cau_hinh()
    if not cfg.get("bot_token"):
        print("THIEU bot_token. Tao bot qua @BotFather, dien vao " + str(CFG))
        print("Mau: " + json.dumps({"bot_token": "...", "api_id": 0, "api_hash": "...", "chat_id": 0}))
        return
    from telethon import TelegramClient, events
    api_id = cfg.get("api_id"); api_hash = cfg.get("api_hash")
    if not api_id or not api_hash:
        print("THIEU api_id/api_hash (my.telegram.org)"); return
    client = TelegramClient("config/tele_bridge_session", api_id, api_hash)
    @client.on(events.NewMessage)
    async def handler(e):
        uid = (e.sender_id or 0)
        if cfg.get("chat_id") and uid != cfg.get("chat_id"):
            return
        try:
            await e.reply(xu_ly(e.raw_text))
        except Exception as ex:
            await e.reply("loi: " + str(ex)[:120])
    client.start(bot_token=cfg["bot_token"])
    print("REM VIA TELE chay... (bot dang lang nghe)")
    client.run_until_disconnected()

if __name__ == "__main__":
    main()
