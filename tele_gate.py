# -*- coding: utf-8 -*-
import json, sys, time
from pathlib import Path
import requests
L = Path(__file__).resolve().parent
C = L / "config" / "tele_bridge.json"
IN = L / "reports" / "tele_inbox.json"
DK = Path(r"C:\Users\SV STORE\Desktop")
API = "https://api.telegram.org/bot{}/{}/{}"
OW = None
def cg():
    return json.loads(C.read_text(encoding="utf-8-sig")) if C.exists() else {}
def sv(c):
    C.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
def send(t, cid=None):
    c = cg(); tok = c.get("bot_token")
    if not tok: return print("THIEU bot_token")
    cid = cid or c.get("chat_id") or 0
    if not cid: return print("chua co chat_id - chu nhan tin bot 1 lan")
    try:
        r = requests.post(API.format(tok, "sendMessage"), data={"chat_id": cid, "text": t[:4000]}, timeout=20)
        print("send", r.status_code)
    except Exception as e:
        print("send ERR", e)
def st():
    hb = [f.name.replace("worker_","").replace(".txt","")+"="+f.read_text(errors="ignore").strip()[-19:] for f in (L/"reports").glob("worker_*.txt")]
    g = "?"
    try: g = (L/"reports"/"cpu_gate.txt").read_text().strip()
    except Exception: pass
    return "TRU:\n" + "\n".join(hb) + "\ngate=" + g
def bao():
    f = L/"reports"/"EVO_BAO_CAO.md"
    return f.read_text(encoding="utf-8-sig")[:1400] if f.exists() else "chua co"
def kq():
    f = L/"reports"/"RANK_DARWIN.md"
    return f.read_text(encoding="utf-8-sig")[:800] if f.exists() else "chua co"
def act(t, cid):
    v = (t or "").strip()
    if v == "/status": return st()
    if v == "/bao_cao": return bao()
    if v == "/ket_qua": return kq()
    if v == "/help": return "/status /bao_cao /ket_qua\nfor ds: <y tuong> -> ghi Desktop/for ds.txt\nkhac -> inbox"
    if v.lower().startswith("for ds:"):
        try:
            with (DK/"for ds.txt").open("a", encoding="utf-8") as f:
                f.write("\n\n[" + time.strftime("%Y-%m-%d %H:%M") + " Tele]\n" + v[7:].strip() + "\n")
            return "Da ghi for ds (doc hang ngay)."
        except Exception as e:
            return "loi: " + str(e)[:80]
    lst = []
    if IN.exists():
        try: lst = json.loads(IN.read_text(encoding="utf-8-sig"))
        except Exception: lst = []
    lst.append({"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "chat": cid, "noi_dung": v})
    IN.write_text(json.dumps(lst, ensure_ascii=False, indent=1), encoding="utf-8")
    return "Da nhan (inbox). /help xem lenh."
def poll():
    c = cg(); tok = c.get("bot_token")
    if not tok: return print("THIEU bot_token")
    try:
        r = requests.post(API.format(tok, "getUpdates"), data={"timeout": 15}, timeout=22)
        j = r.json()
        if not j.get("ok"): return print("poll err", j)
        off = 0
        for u in j.get("result", []):
            m = u.get("message") or u.get("edited_message") or {}
            cid = m.get("chat", {}).get("id")
            txt = m.get("text") or ""
            off = max(off, u.get("update_id", 0))
            if not cid: continue
            if c.get("chat_id") in (None, 0):
                c["chat_id"] = cid; sv(c); print("chat_id =", cid)
            if cid != c.get("chat_id"): continue
            send(act(txt, cid), cid)
        if off:
            requests.post(API.format(tok, "getUpdates"), data={"offset": off + 1}, timeout=15)
    except Exception as e:
        print("poll ERR", e)
if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "poll"
    if a == "send" and len(sys.argv) > 2: send(sys.argv[2])
    elif a == "check": print(json.dumps(cg(), ensure_ascii=False))
    else: poll()
