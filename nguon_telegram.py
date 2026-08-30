# -*- coding: utf-8 -*-
"""nguon_telegram.py - Nguon Telegram cho SEEKNER: doc tin tu cac kenh/channel
cong khai lien quan trading. Luu y: bot chi doc duoc kenh ma bot da duoc them vao
(lam admin/member). Voi kenh cong khai, thu doc qua getChat + getUpdates.

Chay:
  python nguon_telegram.py                : doc cac kenh cau hinh + tin nhan
  python nguon_telegram.py --them @ten    : thu getChat 1 kenh
"""
import sys, time, json, pathlib
import requests
import toc_do

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))
API_KEYS = LAB / "config" / "api_keys.json"

# Cac kenh/channel cong khai lien quan trading can thu doc. Bot phai duoc them
# vao kenh thi moi doc duoc; neu chua, getChat tra loi ro can them bot.
KENH_MAC_DINH = [
    "forexsignals", "tradingpro", "babypips_signals", "forex_trading_news",
    "quant_trading", "crypto_signals_daily",
]

TG_API = "https://api.telegram.org/bot{token}/{method}"


def _bot_token():
    if API_KEYS.exists():
        try:
            return json.loads(API_KEYS.read_text(encoding="utf-8")).get(
                "telegram_bot_token", "")
        except Exception:
            return ""
    return ""


def _goi_telegram(method, params=None):
    """Goi Telegram Bot API qua toc_do (khong spam). Tra ve (json_hoac_None, code)."""
    token = _bot_token()
    if not token:
        return None, None
    toc_do.TOC_DO.cho("telegram")
    try:
        r = requests.get(TG_API.format(token=token, method=method),
                         params=params, timeout=30)
        if r.status_code in (429, 403):
            toc_do.TOC_DO.doi_429("telegram")
            return None, r.status_code
        try:
            return r.json(), r.status_code
        except Exception:
            return None, r.status_code
    except Exception:
        return None, None


def kiem_tra_bot():
    """getMe de xac nhan token bot hoat dong."""
    js, code = _goi_telegram("getMe")
    if js and js.get("ok"):
        u = js["result"]
        return f"@{(u.get('username') or '?')} (id={u.get('id')})"
    return f"LOI getMe code={code}"

def _kiem_tra_kenh(ten):
    """getChat tung kenh -> (trang_thai, ten_day_du)."""
    js, code = _goi_telegram("getChat", {"chat_id": ten})
    if js and js.get("ok"):
        ch = js["result"]
        return ("CO_QUYEN", ch.get("title") or ch.get("username") or ten)
    mo_ta = ""
    if js and js.get("description"):
        mo_ta = js["description"][:80]
    return ("CAN_THEM_BOT", ten + ((" (" + mo_ta + ")") if mo_ta else ""))


def doc_kenh_cong_khai(kenh_list=None):
    """Doc cac kenh cong khai:
      - getChat tung kenh: xac nhan bot co quyen doc hay can them.
      - getUpdates: trong --khong -- doc cac tin nhan gan day bot nhan duoc.
    Tra ve (ds, thong_bao). ds la cac dict {ten,url,kenh,text} cho luu."""
    kenh_list = kenh_list or KENH_MAC_DINH
    ds = []
    notes = []
    # 1) getMe xac nhan bot
    note = kiem_tra_bot()
    notes.append("BOT: " + note)
    # 2) kiem tra tung kenh
    for ten in kenh_list:
        trang, chi_tiet = _kiem_tra_kenh(ten)
        if trang == "CO_QUYEN":
            notes.append(f"CO_QUYEN: {chi_tiet}")
            url = f"https://t.me/{ten.lstrip('@')}"
            ds.append({"ten": chi_tiet, "url": url, "kenh": ten, "text": "",
                       "ngon_ngu": "", "tu_khoa": "telegram_channel"})
        else:
            notes.append(f"CAN_THEM_BOT: {chi_tiet}")
    # 3) getUpdates: doc tin nhan gan day (bot phai trong kenh moi nhan channel_post)
    js, code = _goi_telegram("getUpdates", {"limit": 50, "timeout": 0})
    if js and js.get("ok"):
        for up in js.get("result", []):
            msg = up.get("channel_post") or up.get("message") or {}
            ch = msg.get("chat") or {}
            if not ch.get("id"):
                continue
            text = (msg.get("text") or msg.get("caption") or "")[:400]
            if not text:
                continue
            un = ch.get("username") or f"chat{ch.get('id')}"
            mid = msg.get("message_id")
            url = f"https://t.me/{un}/{mid}" if mid else f"https://t.me/{un}"
            ds.append({"ten": (msg.get("channel_title") or ch.get("title") or un)[:120],
                       "url": url, "kenh": un, "text": text,
                       "ngon_ngu": "", "tu_khoa": "telegram_post"})
    else:
        notes.append(f"getUpdates: khong doc duoc (code={code})")
    # bo trung url
    seen, out = set(), []
    for d in ds:
        if d["url"] in seen:
            continue
        seen.add(d["url"]); out.append(d)
    thong_bao = "\n".join(notes)
    return out, thong_bao


def luu(con, ds):
    """Ghi cac bai dang vao bang muc (bao trung qua bam(url)) + tao task scout.
    Tra ve so luong them moi."""
    import bo_nao
    them = 0
    for d in ds:
        mid = bo_nao.bam(d["url"])
        ten = d["ten"] or (d["text"] or d["url"])[:120]
        try:
            con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) "
                        "VALUES(?,?,?,?,?,0)",
                        (mid, "telegram", ten, d["url"], time.time()))
            if con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()[0] == 0:
                bo_nao.tao_task(con, "scout",
                                {"ten": ten, "url": d["url"],
                                 "van_ban": d.get("text", ""),
                                 "kenh": d.get("kenh", ""),
                                 "tu_khoa": d.get("tu_khoa", "")},
                                muc_id=mid, uu_tien=0, huong="seeker")
                them += 1
        except Exception:
            pass
    con.commit()
    return them


def main():
    args = sys.argv[1:]
    ds, tb = doc_kenh_cong_khai()
    print("=== THONG BAO KENH ===")
    print(tb)
    import bo_nao
    con = bo_nao.mo_db()
    n = luu(con, ds)
    print(f"\nTelegram: doc {len(ds)} bai, them moi {n} vao muc + scout")
    for d in ds[:15]:
        print(f"  [{d.get('kenh')}] {d['ten'][:55]}")


if __name__ == "__main__":
    main()
