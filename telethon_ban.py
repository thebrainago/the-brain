# -*- coding: utf-8 -*-
"""telethon_ban.py - Nguon Telegram qua TAI KHOAN THAT (Telethon).
Dung api_id/api_hash/phone trong config/api_keys.json. Co the TU TIM KIEM + JOIN
nhom/kenh + doc tin nhan (khong bi gioi han nhu bot hay t.me/s).

Lan dau chay can nhap ma xac nhan tu Telegram (luu session vao config/telethon_thebrain.session,
lan sau khong can nhap lai).

Chay:
  python telethon_ban.py --dang-nhap <ma>   : hoan tat dang nhap (sau khi da nhan ma)
  python telethon_ban.py --gui-ma           : yeu cau gui ma xac nhan
  python telethon_ban.py --quet <tu_khoa>   : tim kiem + doc ket qua theo tu khoa
  python telethon_ban.py                    : quet theo keyword bank (gioi han)
"""
import sys, time, json, pathlib, asyncio

import telethon
from telethon import TelegramClient, functions
from telethon.tl.types import Channel, Chat, Message

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))
API_KEYS = LAB / "config" / "api_keys.json"
SESSION = LAB / "config" / "telethon_thebrain.session"
_HASH_FILE = LAB / "config" / "telethon_code_hash.txt"


def _thong_tin():
    if API_KEYS.exists():
        try:
            return json.loads(API_KEYS.read_text(encoding="utf-8")).get("telethon", {})
        except Exception:
            return {}
    return {}


from contextlib import asynccontextmanager


@asynccontextmanager
async def _ket_noi():
    """Mo ket noi khong goi start() de tranh hoi phone tuong tac."""
    cl = _client()
    await cl.connect()
    try:
        yield cl
    finally:
        try:
            await cl.disconnect()
        except Exception:
            pass


def _client():
    tt = _thong_tin()
    api_id = tt.get("api_id")
    api_hash = tt.get("api_hash")
    if not api_id or not api_hash:
        raise SystemExit("THIEU api_id/api_hash trong config/api_keys.json -> telethon")
    return TelegramClient(str(SESSION), int(api_id), api_hash)


async def _gui_ma():
    async with _ket_noi() as cl:
        if await cl.is_user_authorized():
            me = await cl.get_me()
            print(f"DA DANG NHAP roi: @{me.username} ({me.first_name})")
            return
        phone = _thong_tin().get("phone", "")
        res = await cl.send_code_request(phone)
        _HASH_FILE.write_text(str(getattr(res, "phone_code_hash", "")), encoding="utf-8")
        print(f"DA GUI MA xac nhan ve so {phone}. Hay chay: python telethon_ban.py --dang-nhap <ma>")


async def _dang_nhap(ma):
    async with _ket_noi() as cl:
        if await cl.is_user_authorized():
            print("DA DANG NHAP roi (session ton tai).")
            return
        phone = _thong_tin().get("phone", "")
        try:
            pch = _HASH_FILE.read_text(encoding="utf-8").strip() if _HASH_FILE.exists() else None
            if pch:
                await cl.sign_in(phone, code=ma, phone_code_hash=pch)
            else:
                await cl.sign_in(phone, code=ma)
            me = await cl.get_me()
            print(f"DANG NHAP OK: @{me.username} ({me.first_name})")
        except telethon.errors.SessionPasswordNeededError:
            print("Can 2FA password. Goi: python telethon_ban.py --mat-khau <pw>")
        except Exception as e:
            print("LOI dang nhap:", e)


async def _mat_khau(pw):
    async with _ket_noi() as cl:
        await cl.sign_in(password=pw)
        me = await cl.get_me()
        print(f"DANG NHAP OK (2FA): @{me.username}")


async def _tim(ket_qua, gioi_han=10):
    """Tim kiem channel/group theo tu khoa qua SearchGlobal. Tra list (entity, text)."""
    ds = []
    async with _ket_noi() as cl:
        try:
            res = await cl(functions.messages.SearchGlobalRequest(
                q=ket_qua, filter=None, min_date=None, max_date=None,
                offset_rate=0, offset_peer=telethon.tl.types.InputPeerEmpty(),
                offset_id=0, limit=gioi_han))
            for m in res.messages:
                if not getattr(m, "message", None):
                    continue
                try:
                    ent = await cl.get_entity(m.peer_id)
                except Exception:
                    continue
                ten = getattr(ent, "title", None) or getattr(ent, "username", None) or ""
                ds.append((ent, m.message[:300]))
        except Exception as e:
            print("LOI tim kiem:", e)
    return ds


async def _doc_kenh(ref, so=15):
    """Doc so tin moi nhat cua 1 kenh/nhom (ref: username/@/link)."""
    out = []
    async with _ket_noi() as cl:
        try:
            ent = await cl.get_entity(ref)
        except Exception as e:
            return out, f"LOI get_entity({ref}): {e}"
        try:
            async for msg in cl.iter_messages(ent, limit=so):
                if not getattr(msg, "message", None):
                    continue
                out.append({"text": msg.message[:400],
                            "time": msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "",
                            "url": f"https://t.me/{getattr(ent,'username','')}/{msg.id}" if getattr(ent,'username','') else ""})
        except Exception as e:
            return out, f"LOI doc kenh: {e}"
        return out, ""


SEED_KENH = [
    "forexsignals", "tradingview", "fxstreetnews", "investingcom", "trading212",
    "forexfactory", "metatrader", "octafx", "fxtm", "pipmailer", "forextime",
    "earnforex", "dailyforex", "tradingideas", "gold_signals", "thinkingtrader",
    "babypips", "exness", "icmarkets", "pepperstone", "tradersunion",
    "fxempire", "dailyfx", "forexfactory", "myfxbook", "tradingtips",
    "forexmagnates", "cryptosignals", "btcusdsignals", "xauusdsignals",
    "goldpricesignals", "forexbeginner", "tradertalk", "forexnews",
]


QUY_KENH = [
    "ftmo", "fundednext", "myfundedfx", "the5ers", "apexpropfirm", "topstepprop",
    "tfpforex", "fundedtrading", "propfirmguy", "fundedpass", "cta", "managedfutures",
    "hedgefund", "quantfund", "winton", "man_group", "milestone", "citadelsecurities",
    "twosigma", "renaissance", "nanex", "point72", "d.e.shaw", "guggli", "quantconnect",
    "avatrade_prop", "tradersfund", "fundedtradingacademy",
]


async def quet_quy(so_kenh=12, so_bai=6):
    """Doc rieng cac kenh QUY / prop firm / hedge fund. Tra ds bai."""
    ds = []
    async with _ket_noi() as cl:
        if not await cl.is_user_authorized():
            print("CHUA DANG NHAP.")
            return ds
        da = set()
        for u in QUY_KENH:
            if len(da) >= so_kenh:
                break
            try:
                ent = await cl.get_entity(u)
            except Exception:
                continue
            key = getattr(ent, "id", u)
            if key in da:
                continue
            da.add(key)
            ten = getattr(ent, "title", None) or u
            un = getattr(ent, "username", "") or ""
            dem = 0
            try:
                async for msg in cl.iter_messages(ent, limit=so_bai):
                    if not getattr(msg, "message", None):
                        continue
                    url = f"https://t.me/{un}/{msg.id}" if un else ""
                    ds.append({"ten": (ten or u)[:120], "url": url, "kenh": un or u,
                               "text": msg.message[:400], "ngon_ngu": "",
                               "tu_khoa": "quy_fund",
                               "nguon": "quy",
                               "thoi_gian": msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""})
                    dem += 1
            except Exception:
                pass
            if dem < 1 and un:
                ds.append({"ten": (ten or u)[:120], "url": f"https://t.me/{un}", "kenh": un or u,
                           "text": "", "ngon_ngu": "", "tu_khoa": "quy_fund", "thoi_gian": ""})
    return ds


def _ung_vien():
    """Ung vien username kenh: seed + sinh tu keyword bank."""
    cac = list(SEED_KENH)
    try:
        import keywords_nguon as kw
        for dm in ("cho_tin_hieu", "dang_doi", "cong_dong", "quy"):
            cac += kw.tao_ung_vien_username(dm, toi_da=10)
    except Exception:
        for w in ("forex", "trading", "signals", "gold", "crypto"):
            cac += [w, w + "signals", w + "trading", w + "fx"]
    return [c for c in dict.fromkeys(cac) if len(c) <= 32]


async def quet(so_kenh=16, so_bai=8):
    """Do username ung vien -> doc kenh/nhom ton tai qua tai khoan that. Tra ds bai."""
    ds = []
    async with _ket_noi() as cl:
        if not await cl.is_user_authorized():
            print("CHUA DANG NHAP (chay --gui-ma roi --dang-nhap).")
            return ds
        da = set()
        so_kenh = max(so_kenh, 1)
        for u in _ung_vien():
            if len(da) >= so_kenh:
                break
            try:
                ent = await cl.get_entity(u)
            except Exception:
                continue
            key = getattr(ent, "id", u)
            if key in da:
                continue
            da.add(key)
            ten = getattr(ent, "title", None) or getattr(ent, "username", None) or u
            un = getattr(ent, "username", "") or ""
            dem = 0
            try:
                async for msg in cl.iter_messages(ent, limit=so_bai):
                    if not getattr(msg, "message", None):
                        continue
                    url = f"https://t.me/{un}/{msg.id}" if un else ""
                    ds.append({"ten": (ten or u)[:120], "url": url, "kenh": un or u,
                               "text": msg.message[:400], "ngon_ngu": "",
                               "tu_khoa": "telethon_channel",
                               "thoi_gian": msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""})
                    dem += 1
            except Exception:
                pass
            if dem < 1:
                url = f"https://t.me/{un}" if un else ""
                ds.append({"ten": (ten or u)[:120], "url": url, "kenh": un or u,
                           "text": "", "ngon_ngu": "", "tu_khoa": "telethon_channel",
                           "thoi_gian": ""})
    return ds


def luu(con, ds):
    import bo_nao
    them = 0
    for d in ds:
        mid = bo_nao.bam(d["url"])
        ten = d["ten"] or (d["text"] or d["url"])[:120]
        try:
            nguon_ = d.get("nguon", "telethon")
            con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) "
                        "VALUES(?,?,?,?,?,0)", (mid, nguon_, ten, d["url"], time.time()))
            row = con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()
            if row and row[0] == 0:
                bo_nao.tao_task(con, "scout",
                                {"ten": ten, "url": d["url"], "van_ban": d.get("text", ""),
                                 "kenh": d.get("kenh", ""), "tu_khoa": d.get("tu_khoa", "")},
                                muc_id=mid, uu_tien=0, huong="seeker")
                them += 1
        except Exception:
            pass
    con.commit()
    return them


async def main():
    args = sys.argv
    if "--gui-ma" in args:
        await _gui_ma(); return
    if "--dang-nhap" in args:
        await _dang_nhap(args[args.index("--dang-nhap") + 1]); return
    if "--mat-khau" in args:
        await _mat_khau(args[args.index("--mat-khau") + 1]); return
    if "--quet" in args:
        tk = args[args.index("--quet") + 1]
        ds = await quet(so_kenh=12, so_bai=8)
    else:
        ds = await quet(so_kenh=16, so_bai=8)
    print(f"QUET duoc {len(ds)} bai")
    for d in ds[:15]:
        print(f"  [{d['kenh']}] {d['ten'][:45]} :: {(d['text'] or '')[:50]}")
    if "--xem" not in args:
        import bo_nao
        con = bo_nao.mo_db()
        n = luu(con, ds)
        print(f"LUU them {n} vao muc + scout")


if __name__ == "__main__":
    asyncio.run(main())
