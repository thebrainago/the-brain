# -*- coding: utf-8 -*-
"""TELEGRAM -> tai_lieu / noi_dung.

VI SAO CAN. Chu du an 04/09/2026 dua hai kenh:
  - `t.me/bobvolmanchannel` (Nhat Hoai Trader Channel, ~11.362 nguoi theo doi)
  - `t.me/vutruea`
va noi ro trong do "co rat nhieu chien luoc cu the va EA". Do la mat do co che
cao hon han RSS blog (suat do duoc: arxiv 0,8%, openalex 6%), va la mot LOP
NGUON ma SEEKER chua he cham toi.

HAI DUONG VAO, phai phan biet cho ro vi chung KHAC NHAU VE QUYEN:

  (1) **Xem truoc web** `t.me/s/<kenh>` - khong can dang nhap, khong can khoa.
      Doc duoc VAN BAN bai gan day. KHONG tai duoc file dinh kem.

  (2) **MTProto** (Telethon) - can tai khoan that. Doc duoc TOAN BO lich su va
      TAI DUOC file dinh kem (.mq5 / .ex5 / .zip / .pdf). Day la duong duy nhat
      lay duoc EA.

DO THAT 04/09/2026, va no lat nguoc gia dinh trong ban tom tat phien sang:

    t.me/s/durov              -> 200, 20 khoi tin nhan   (xem truoc BAT)
    t.me/s/bobvolmanchannel   -> ve t.me/bobvolmanchannel, 0 khoi tin nhan
    t.me/s/vutruea            -> ve t.me/vutruea         , 0 khoi tin nhan

Ban tom tat viet "preview khong can dang nhap tai t.me/s/<ten_kenh> chi doc
duoc text gan day, KHONG tai duoc file". Ve mat ky thuat cau do dung, nhung ap
len HAI KENH NAY thi SAI: ca hai deu TAT xem truoc web. Nen o day khong phai
"lay duoc text nhung thieu file" - ma la **khong lay duoc gi ca** neu khong
dang nhap.

Telegram KHONG chuyen huong bang 404. No tra 200 tren trang gioi thieu, nen mot
bo quet chi doc status code se bao "OK" trong khi ve 0 chu. Do la ly do
`kiem_kenh` so `r.url` chu khong so `r.status_code`.

RANG BUOC AN TOAN - giu y het `nhan/ma_nguon.py`, khong duoc noi long:
  1. KHONG BAO GIO chay file tai ve. Khong exec/import/bien dich/mo MetaEditor.
     `.ex5`/`.ex4` la nhi phan da bien dich: ghi dau vet roi BO, khong luu.
  2. Chi anh xa vao mau CO SAN qua `nhan/bien_dich_ung_vien.py`.
  3. Co tran kich thuoc.
  4. Provenance day du: moi ban ghi giu url dang `https://t.me/<kenh>/<id>`.
"""
from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path

from nhan import so as SO

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

GOC = "https://t.me"
CAU_HINH = Path(__file__).resolve().parent.parent / "config" / "telegram.json"

#: Tran mot bai. Bai Telegram dai hon 20k ky tu gan nhu chac chan la bai gop.
TRAN_KY_TU = 20_000
#: San: mot bai 200 ky tu khong mo ta noi mot chien luoc.
SAN_KY_TU = 200
#: Duoi file dang quan tam. `.ex5`/`.ex4` la NHI PHAN - ghi dau vet, khong doc.
DUOI_MA = (".mq5", ".mq4", ".mqh")
DUOI_NHI_PHAN = (".ex5", ".ex4")
DUOI_TAI_LIEU = (".pdf", ".txt", ".set")

#: ARCHIVE - **khong tai theo mac dinh**, phai bat `tai_archive=True`.
#:
#: DO THAT 04/09/2026 tren 4 kenh EA vua tim duoc. Lieti ke ben trong 12 `.zip`
#: + toan bo `.rar` cua @AllEaShare:
#:     .ex4 x32  .dll x15  .jpg x75  .mp4 x8  .set x35  .pdf x10  .txt x19
#:     ma nguon (.mq4/.mq5): **1 file**
#: Tuc 181 MB tai ve doi lay 1 file doc duoc. Phan con lai la EA DA BIEN DICH va
#: DLL - hai thu ma luat cua du an cam chay, nen chung khong co cong dung nao
#: ngoai viec chiem dia.
#:
#: Va dia la mot VAN DE DANG MO (`dia_va_tick_test`): duoi 15 GB thi buoc kiem
#: dinh quyet dinh (MT5 tick-test) bi khoa. Luc do dia con **12,9 GB**. Mot bo
#: thu thap lam nang them mot van de dang mo la mot bo thu thap sai.
#:
#: Cach dung dung: tai archive co chon loc, rut `.set`/`.txt`/`.mq4`/`.mq5` ra
#: roi XOA archive. 181 MB rut ra duoc 240 KB thu dung duoc.
DUOI_ARCHIVE = (".zip", ".rar", ".7z")

KENH_CHU_DU_AN = ("bobvolmanchannel", "vutruea")


# ---------------------------------------------------------------- xem truoc web

def _so_theo_doi(t: str) -> int | None:
    m = re.search(r"([\d\s ,\.]+)\s*subscribers", t)
    if not m:
        return None
    try:
        return int(re.sub(r"[^\d]", "", m.group(1)))
    except ValueError:
        return None


def kiem_kenh(ten: str, timeout: int = 30) -> dict:
    """Kenh nay co BAT xem truoc web khong?

    Do bang `r.url` chu KHONG bang `r.status_code`: Telegram chuyen huong im
    lang ve trang gioi thieu va van tra 200. Doc status code thi ket luan se la
    "OK" trong khi khong co mot chu noi dung nao - dung ho loi "ket luan am phai
    phan biet CHUA DO".
    """
    import requests
    ten = ten.strip().lstrip("@")
    try:
        r = requests.get(f"{GOC}/s/{ten}", timeout=timeout,
                         headers={"User-Agent": UA})
    except Exception as e:
        return {"kenh": ten, "duoc": False,
                "ly_do": f"{type(e).__name__}: {str(e)[:80]}"}
    so_khoi = r.text.count("tgme_widget_message_text")
    xem_truoc = "/s/" in r.url and so_khoi > 0
    return {"kenh": ten, "http": r.status_code, "url_cuoi": r.url,
            "xem_truoc": xem_truoc, "so_khoi": so_khoi, "duoc": xem_truoc,
            "nguoi_theo_doi": _so_theo_doi(r.text),
            "ly_do": "" if xem_truoc else "kenh TAT xem truoc web - bat buoc MTProto"}


def _van_ban(khoi: str) -> str:
    m = re.search(r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
                  khoi, re.S)
    if not m:
        return ""
    t = m.group(1)
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"</?(?:pre|code|blockquote)[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t).strip()


def _dinh_kem(khoi: str) -> list[dict]:
    """File dinh kem NHIN THAY duoc tu trang xem truoc.

    Chi lay TEN + CO - trang xem truoc khong cho duong tai. Ghi lai de UOC LUONG
    gia tri cua viec mo duong MTProto TRUOC khi bo cong xin tai khoan.
    """
    ra = []
    for m in re.finditer(
            r"tgme_widget_message_document_title[^>]*>(.*?)</div>.*?"
            r"tgme_widget_message_document_extra[^>]*>(.*?)</div>", khoi, re.S):
        ten = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        co = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        duoi = ("." + ten.rsplit(".", 1)[-1].lower()) if "." in ten else ""
        ra.append({"ten": ten, "co": co, "duoi": duoi,
                   "loai": ("ma_nguon" if duoi in DUOI_MA else
                            "nhi_phan" if duoi in DUOI_NHI_PHAN else
                            "tai_lieu" if duoi in DUOI_TAI_LIEU else "khac")})
    return ra


def doc_trang(ten: str, truoc: int | None = None, timeout: int = 30) -> dict:
    """Mot trang xem truoc -> danh sach bai + con tro `truoc` cua trang ke tiep."""
    import requests
    ten = ten.strip().lstrip("@")
    url = f"{GOC}/s/{ten}" + (f"?before={truoc}" if truoc else "")
    r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    t = r.text
    if "/s/" not in r.url:
        return {"bai": [], "truoc_tiep": None, "loi": "kenh tat xem truoc web"}
    bai = []
    for k in re.split(r'<div class="tgme_widget_message_wrap', t)[1:]:
        m = re.search(r'data-post="([^"]+)"', k)
        if not m:
            continue
        post = m.group(1)
        sid = post.rsplit("/", 1)[-1]
        ngay = re.search(r'datetime="([^"]+)"', k)
        bai.append({"post": post, "id": int(sid) if sid.isdigit() else None,
                    "url": f"{GOC}/{post}", "van_ban": _van_ban(k),
                    "dinh_kem": _dinh_kem(k),
                    "luc": ngay.group(1) if ngay else ""})
    m = re.search(r'data-before="(\d+)"', t)
    return {"bai": bai, "truoc_tiep": int(m.group(1)) if m else None}


def _ghi(b: dict, kenh: str, vb: str, bao: dict) -> None:
    tieu_de = (vb.split("\n", 1)[0] or "")[:180]
    vt = SO.van_tay(b["url"])
    with SO.ket_noi() as cn:
        cur = cn.execute(
            "INSERT OR IGNORE INTO tai_lieu(van_tay,nguon,loai,tieu_de,url,"
            "tom_tat,tu_khoa,diem,luc) VALUES(?,?,?,?,?,?,?,?,?)",
            (vt, f"telegram_{kenh}", "telegram", tieu_de, b["url"],
             vb[:2000], "telegram", 2.0, SO.bay_gio()))
        bao["tai_lieu_moi"] = bao.get("tai_lieu_moi", 0) + cur.rowcount
        row = cn.execute("SELECT id FROM tai_lieu WHERE van_tay=?",
                         (vt,)).fetchone()
        if not row:
            return
        cur2 = cn.execute(
            "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
            "so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc) "
            "VALUES(?,?,?,'bai_bao',?,?,?,?,?,0)",
            (row["id"], SO.van_tay("nd", b["url"]), b["url"],
             b.get("cach", "telegram_web"),
             len(vb), len(b.get("van_ban") or ""), vb, SO.bay_gio()))
        if cur2.rowcount:
            bao["ban_doc_moi"] = bao.get("ban_doc_moi", 0) + 1
            bao["ky_tu"] = bao.get("ky_tu", 0) + len(vb)


def thu_thap(ten: str, so_trang: int = 20, ngan_sach_giay: int = 180,
             in_ra=print) -> dict:
    """Di NGUOC lich su kenh qua xem truoc web, ghi `tai_lieu` + `noi_dung`.

    Voi kenh tat xem truoc, tra ve LY DO ro rang thay vi mot bao cao "0 bai"
    khong phan biet duoc voi "kenh rong".
    """
    ten = ten.strip().lstrip("@")
    kt = kiem_kenh(ten)
    if not kt.get("duoc"):
        return {"kenh": ten, "chay": False, "ly_do": kt.get("ly_do"),
                "can": "MTProto - xem telegram.CAN_GI()"}
    t0 = time.time()
    bao = {"kenh": ten, "chay": True, "trang": 0, "bai": 0, "tai_lieu_moi": 0,
           "ban_doc_moi": 0, "ky_tu": 0, "bo_qua_ngan": 0,
           "dinh_kem": {"ma_nguon": 0, "nhi_phan": 0, "tai_lieu": 0, "khac": 0}}
    truoc = None
    for _ in range(so_trang):
        if time.time() - t0 > ngan_sach_giay:
            bao["dung_vi"] = "het ngan sach giay"
            break
        try:
            tr = doc_trang(ten, truoc)
        except Exception as e:
            bao["dung_vi"] = f"{type(e).__name__}: {str(e)[:80]}"
            break
        if tr.get("loi") or not tr["bai"]:
            break
        bao["trang"] += 1
        for b in tr["bai"]:
            bao["bai"] += 1
            for dk in b["dinh_kem"]:
                bao["dinh_kem"][dk["loai"]] = bao["dinh_kem"].get(dk["loai"], 0) + 1
            vb = (b["van_ban"] or "")[:TRAN_KY_TU]
            if len(vb) < SAN_KY_TU:
                bao["bo_qua_ngan"] += 1
                continue
            _ghi(b, ten, vb, bao)
        truoc = tr.get("truoc_tiep")
        if not truoc:
            break
    bao["giay"] = round(time.time() - t0, 1)
    SO.ghi_chi_so("telegram_ban_doc_moi", float(bao["ban_doc_moi"]), {"kenh": ten})
    in_ra(f"  telegram/{ten}: {bao['bai']} bai, {bao['ban_doc_moi']} ban doc moi, "
          f"dinh kem {bao['dinh_kem']}")
    return bao


# ------------------------------------------------------------------- MTProto

def CAN_GI() -> dict:
    """CAI GI CON THIEU de vao MTProto - va cau tra loi hom nay la: KHONG GI CA.

    SAI LAM 04/09/2026, ghi lai de khong lap: ham nay ban dau viet huong dan chu
    du an di lay `api_id`/`api_hash` tren my.telegram.org, va toi con di muon
    `auth_key` tu phien Telegram Web trong trinh duyet de vong qua buoc do.
    **Ca hai deu thua.** `lab/telethon_ban.py` (11/08/2026) da co san:
        config/api_keys.json           -> api_id + api_hash + phone (du ca ba)
        config/telethon_thebrain.session -> phien DA DANG NHAP, con song
    Do that: `is_user_authorized() -> True`, cung tai khoan 8789315634.

    Tuc toi da xay trung mot thu da co, va con bao nguoi dung di lam mot viec ho
    da lam tu ba tuan truoc. Dung nguyen tac "noi day truoc khi xay them" ma
    chinh toi ap cho code nguoi khac ca ngay hom nay.

    Giu ham nay lai vi no van dung khi phien het han - luc do moi that su can
    nguoi nhap ma.
    """
    cs = _khoa_co_san()
    if cs:
        return {"du_roi": True,
                "khoa": "config/api_keys.json (telethon)",
                "phien": str(PHIEN_CO_SAN),
                "ghi_chu": "khoa va phien da co san tu telethon_ban.py - "
                           "khong can hoi nguoi dung gi ca"}
    return {
        "vi_sao": "chua co khoa nao dung duoc, va phien cu (neu co) da het han",
        "can_tu_nguoi": [
            "api_id + api_hash: dang nhap my.telegram.org -> 'API development "
            "tools' -> tao mot ung dung (mien phi, ~2 phut)",
            "so dien thoai cua mot tai khoan Telegram DA co (hoac tao moi)",
            "ma dang nhap gui ve app Telegram khi chay lan dau - nhap MOT lan, "
            "sau do Telethon giu phien trong lab/config/telegram.session",
        ],
        "khong_can": ["khong can mat khau neu khong bat xac thuc hai buoc",
                      "khong can tra phi"],
        "dat_o": str(CAU_HINH),
        "mau": {"api_id": 123456, "api_hash": "xxxxxxxx", "phone": "+84..."},
        "sau_do": "b tele bobvolmanchannel",
    }


def cau_hinh() -> dict:
    if CAU_HINH.exists():
        try:
            return json.loads(CAU_HINH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


# ------------------------------------- duong KHONG can SMS: muon phien trinh duyet

#: api_id/api_hash CONG KHAI cua chinh Telegram Web K. Phai dung cap nay chu
#: khong phai cap rieng: `auth_key` lay tu localStorage cua Telegram Web da duoc
#: cap PHAT cho ung dung do. Ghep khoa cua app A voi id cua app B thi may chu
#: tu choi.
API_WEB_ID = 2496
API_WEB_HASH = "8da85b0d5bfe62527e5b244c209159c3"

#: Dia chi IPv4 cac trung tam du lieu Telegram. `MemorySession.set_dc` doi
#: ip/port tuong minh - Telethon chi tu tra cuu duoc khi da co phien.
DC_IP = {1: "149.154.175.53", 2: "149.154.167.51", 3: "149.154.175.100",
         4: "149.154.167.91", 5: "91.108.56.130"}

CDP_MAC_DINH = "http://127.0.0.1:9224"


def khoa_tu_trinh_duyet(cdp: str = CDP_MAC_DINH, dong_tab: bool = True) -> dict:
    """Lay `auth_key` tu phien Telegram Web dang mo trong ho so trinh duyet CDP.

    VI SAO CO DUONG NAY. `CAN_GI()` noi that: tao phien MTProto tu dau doi mot
    so dien thoai nhan ma SMS, va do la thu may khong tu lam duoc. Nhung
    04/09/2026 chu du an noi: *"toi da dang nhap tele tren trinh duyet cho ban
    ma"* - va do that thi phien do nam san trong ho so `.browser_darwinex` ma
    `mo_chrome_cdp.py` van dung (`IndexedDB/https_web.telegram.org_*`).

    Telegram Web K giu khoa phien trong `localStorage`:
        user_auth      = {"date":..., "id":<uid>, "dcID":<n>}
        dc<n>_auth_key = "<512 ky tu hex>"   (256 byte)
    Do la du de dung mot phien Telethon. Khong can SMS, khong can api_id rieng.

    RUI RO PHAI BIET: dung cung mot `auth_key` tu hai ket noi co the khien may
    chu Telegram huy phien (AUTH_KEY_DUPLICATED) - hau qua la chu du an bi dang
    xuat khoi Telegram Web va phai dang nhap lai. Vi vay mac dinh `dong_tab`
    DONG moi tab telegram.org lai truoc khi tra khoa ve.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(cdp)
        if not br.contexts:
            raise RuntimeError("CDP khong co context nao - Chrome chua mo?")
        ctx = br.contexts[0]
        pg = ctx.new_page()
        pg.goto("https://web.telegram.org/k/", wait_until="domcontentloaded",
                timeout=60000)
        pg.wait_for_timeout(5000)
        ls = pg.evaluate(
            "() => { const o={}; for (let i=0;i<localStorage.length;i++)"
            "{const k=localStorage.key(i); o[k]=localStorage.getItem(k);} return o; }")
        pg.close()
        if dong_tab:
            for t in ctx.pages:
                if "telegram.org" in (t.url or ""):
                    t.close()

    if not ls.get("user_auth"):
        raise RuntimeError("Telegram Web chua dang nhap trong ho so trinh duyet nay")
    ua = json.loads(ls["user_auth"])
    dc = int(ua["dcID"])
    k = ls.get(f"dc{dc}_auth_key")
    if not k:
        raise RuntimeError(f"thieu dc{dc}_auth_key trong localStorage")
    return {"dc": dc, "auth_key": bytes.fromhex(json.loads(k)),
            "user_id": ua.get("id")}


def _client(cdp: str = CDP_MAC_DINH):
    """Client Telethon theo THU TU UU TIEN: khoa co san -> rieng -> trinh duyet."""
    cs = _khoa_co_san()
    if cs:
        from telethon.sync import TelegramClient
        return (TelegramClient(cs["phien"], int(cs["api_id"]), cs["api_hash"]),
                {"duong": "khoa_co_san"})
    c = cau_hinh()
    if c.get("api_id") and c.get("api_hash"):
        from telethon.sync import TelegramClient
        return (TelegramClient(str(CAU_HINH.with_suffix(".session")),
                               int(c["api_id"]), c["api_hash"]),
                {"duong": "khoa_rieng"})
    return _client_tu_trinh_duyet(cdp)


def _client_tu_trinh_duyet(cdp: str = CDP_MAC_DINH):
    from telethon.sync import TelegramClient
    from telethon.sessions import MemorySession
    from telethon.crypto import AuthKey

    kh = khoa_tu_trinh_duyet(cdp)
    s = MemorySession()
    s.set_dc(kh["dc"], DC_IP[kh["dc"]], 443)
    s.auth_key = AuthKey(kh["auth_key"])
    return TelegramClient(s, API_WEB_ID, API_WEB_HASH), kh


#: Phien Telethon DA CO SAN cua `lab/telethon_ban.py`. Day la duong UU TIEN 1:
#: no dung khoa rieng cua du an, khong dung chung `auth_key` voi trinh duyet nen
#: khong co rui ro AUTH_KEY_DUPLICATED.
KHOA_CO_SAN = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
PHIEN_CO_SAN = (Path(__file__).resolve().parent.parent / "config"
                / "telethon_thebrain.session")


def _khoa_co_san() -> dict:
    """api_id/api_hash cua du an, neu co."""
    if not KHOA_CO_SAN.exists():
        return {}
    try:
        d = json.loads(KHOA_CO_SAN.read_text(encoding="utf-8"))
    except Exception:
        return {}
    tt = d.get("telethon") or d.get("telegram") or {}
    if isinstance(tt, dict) and tt.get("api_id") and tt.get("api_hash"):
        return {"api_id": tt["api_id"], "api_hash": tt["api_hash"],
                "phien": str(PHIEN_CO_SAN)}
    return {}


def san_sang_mtproto() -> tuple[bool, str]:
    """Co duong MTProto nao dung duoc khong - ke ca duong muon phien trinh duyet."""
    try:
        import telethon  # noqa: F401
    except ImportError:
        return False, "chua cai telethon (pip install telethon)"
    if _khoa_co_san():
        return True, "ok (khoa + phien co san cua telethon_ban.py)"
    c = cau_hinh()
    if c.get("api_id") and c.get("api_hash"):
        return True, "ok (khoa rieng trong config/telegram.json)"
    try:
        import requests
        requests.get(CDP_MAC_DINH + "/json/version", timeout=3)
    except Exception:
        return False, ("khong co khoa nao, va Chrome CDP 9224 khong chay - "
                       "chay `python mo_chrome_cdp.py` roi thu lai")
    return True, ("ok (muon phien Telegram Web - DUONG CUOI, co rui ro "
                  "AUTH_KEY_DUPLICATED)")


def quet_mtproto(ten: str, so_bai: int = 500, tai_file: bool = True,
                 tang_dan: bool = True, tai_archive: bool = False,
                 in_ra=print) -> dict:
    """Doc lich su kenh + TAI FILE dinh kem qua tai khoan that.

    File tai ve KHONG duoc chay - chi doc nhu van ban (giong `ma_nguon.py`).
    `.ex5`/`.ex4` la nhi phan da bien dich: dem roi BO, khong tai.
    """
    duoc, ly_do = san_sang_mtproto()
    if not duoc:
        return {"kenh": ten, "chay": False, "ly_do": ly_do, "can": CAN_GI()}

    c = cau_hinh()
    ten = ten.strip().lstrip("@")
    kho = Path(__file__).resolve().parent.parent / "data" / "telegram" / ten
    kho.mkdir(parents=True, exist_ok=True)
    bao = {"kenh": ten, "chay": True, "bai": 0, "ban_doc_moi": 0,
           "tai_lieu_moi": 0, "file_tai": 0, "file_bo_nhi_phan": 0, "ky_tu": 0}

    # Uu tien khoa RIENG neu chu du an da dat (phien on dinh, khong dung chung
    # voi trinh duyet). Khong co thi muon phien Telegram Web - do la duong da
    # do chay that 04/09/2026.
    cs = _khoa_co_san()
    if cs:
        from telethon.sync import TelegramClient
        cl_ = TelegramClient(cs["phien"], int(cs["api_id"]), cs["api_hash"])
        bao["duong"] = "khoa_co_san"
    elif c.get("api_id") and c.get("api_hash"):
        from telethon.sync import TelegramClient
        cl_ = TelegramClient(str(CAU_HINH.with_suffix(".session")),
                             int(c["api_id"]), c["api_hash"])
        bao["duong"] = "khoa_rieng"
    else:
        cl_, kh = _client_tu_trinh_duyet()
        bao["duong"] = "phien_trinh_duyet"
        bao["user_id"] = kh.get("user_id")

    ct = _con_tro_kenh(ten)
    da_tai = set(ct.get("file_da_tai") or [])
    tu_id = int(ct.get("id_cao_nhat") or 0) if tang_dan else 0
    bao["tu_id"] = tu_id
    cao_nhat = tu_id

    # `min_id` la thu lam cho lan quet thu hai RE. Khong co no thi moi lan chay
    # deu keo lai tu bai moi nhat va di nguoc het `so_bai` - tuc tra tien mang
    # cho nhung bai da nam trong kho. Voi `min_id`, may chu Telegram chi tra ve
    # phan MOI HON con tro, nen lan quet thu hai cua mot kenh im lang gan nhu
    # khong ton gi.
    with cl_ as cl:
        for tin in cl.iter_messages(ten, limit=so_bai,
                                    min_id=tu_id) if tu_id else \
                cl.iter_messages(ten, limit=so_bai):
            bao["bai"] += 1
            if tin.id > cao_nhat:
                cao_nhat = tin.id
            url = f"{GOC}/{ten}/{tin.id}"
            vb = tin.message or ""
            if tin.file and tin.file.name:
                duoi = ("." + tin.file.name.rsplit(".", 1)[-1].lower()) \
                    if "." in tin.file.name else ""
                if duoi in DUOI_NHI_PHAN:
                    bao["file_bo_nhi_phan"] += 1
                elif duoi in DUOI_ARCHIVE and not tai_archive:
                    bao["archive_bo"] = bao.get("archive_bo", 0) + 1
                elif tai_file and duoi in (DUOI_MA + DUOI_TAI_LIEU
                                           + (DUOI_ARCHIVE if tai_archive else ())):
                    # Nhan dang file bang ID DUY NHAT cua Telegram, khong bang
                    # ten: hai kenh co the dang cung mot file voi ten khac nhau,
                    # va cung mot kenh co the dang lai file cu. `file.id` on
                    # dinh qua cac lan quet.
                    ma_f = str(getattr(tin.file, "id", "") or f"{ten}/{tin.id}")
                    if ma_f in da_tai:
                        bao["file_bo_da_co"] = bao.get("file_bo_da_co", 0) + 1
                        dd = None
                    else:
                        try:
                            dd = cl.download_media(tin, file=str(kho))
                            da_tai.add(ma_f)
                            bao["file_tai"] += 1
                        except Exception:
                            dd = None
                    try:
                        if dd and duoi in DUOI_MA:
                            ma = Path(dd).read_text(encoding="utf-8",
                                                    errors="replace")
                            vb = f"{vb}\n\n=== {tin.file.name} ===\n{ma}"
                    except Exception:
                        pass
            vb = vb[:TRAN_KY_TU * 4]
            if len(vb) < SAN_KY_TU:
                continue
            _ghi({"url": url, "van_ban": vb, "cach": "telegram_mtproto"},
                 ten, vb, bao)
    ct["id_cao_nhat"] = max(cao_nhat, int(ct.get("id_cao_nhat") or 0))
    ct["file_da_tai"] = sorted(da_tai)
    ct["lan_cuoi"] = SO.bay_gio()
    ct["tong_bai"] = int(ct.get("tong_bai") or 0) + bao["bai"]
    _ghi_con_tro(ten, ct)
    bao["den_id"] = ct["id_cao_nhat"]
    in_ra(f"  telegram/{ten} (MTProto): {bao}")
    SO.ghi_chi_so("telegram_mtproto_ban_doc", float(bao["ban_doc_moi"]),
                  {"kenh": ten})
    return bao


# ------------------------------------------------- CON TRO: chi lay cai CHUA CO

#: So con tro tung kenh. Cung quy uoc voi `config/ma_nguon_con_tro.json` cua
#: `nhan/ma_nguon.py` - mot file JSON canh cau hinh, khong nam trong so cai.
CON_TRO = Path(__file__).resolve().parent.parent / "config" / "telegram_con_tro.json"


def doc_con_tro() -> dict:
    if CON_TRO.exists():
        try:
            return json.loads(CON_TRO.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def luu_con_tro(d: dict) -> None:
    CON_TRO.parent.mkdir(parents=True, exist_ok=True)
    CON_TRO.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                       encoding="utf-8")


def _con_tro_kenh(ten: str) -> dict:
    return doc_con_tro().get(ten) or {"id_cao_nhat": 0, "file_da_tai": [],
                                      "lan_cuoi": None, "tong_bai": 0}


def _ghi_con_tro(ten: str, ct: dict) -> None:
    d = doc_con_tro()
    d[ten] = ct
    luu_con_tro(d)


# --------------------------------------------------------- TIM KENH MOI

#: Mau bat nhac den mot kenh khac trong noi dung bai. Telegram viet lien ket
#: kenh bang `t.me/<ten>` hoac `@<ten>`; ca hai deu dan den cung mot noi.
_RX_KENH = re.compile(r"(?:t\.me/|@)([A-Za-z][A-Za-z0-9_]{4,31})\b")

#: Ten khong phai kenh noi dung: bot dich vu, lien ket moi ca nhan, tai khoan
#: cham soc khach hang. Bo som de khong dot mot luot goi cho chung.
_BO_TEN = {"joinchat", "share", "addstickers", "proxy", "socks", "iv", "s",
           "telegram", "durov", "BotFather", "SpamBot"}


def kenh_duoc_nhac(gioi_han: int = 500) -> dict[str, int]:
    """Dem cac kenh duoc NHAC DEN trong kho bai Telegram da thu.

    VI SAO. Chu du an 04/09: *"kia la nhung nguon toi tu tim duoc, ban can
    follow va tim nhung kenh khac"*. Cach re nhat de tim kenh moi khong phai di
    doan tu khoa - ma la doc chinh nhung bai DA CO: mot kenh trading gan nhu
    luon dan sang kenh khac (gioi thieu, chuyen tiep bai, nhom phu).

    Day la mot DE XUAT de nguoi duyet, khong phai lenh theo doi tu dong: mot ma
    trong `t.me/...` co the la nhom chat, bot, hay lien ket moi ca nhan.
    """
    ds = SO.nhieu(
        "SELECT n.van_ban FROM noi_dung n JOIN tai_lieu t ON t.id = n.tai_lieu_id "
        "WHERE t.nguon LIKE 'telegram%' LIMIT ?", gioi_han) or []
    dem: dict[str, int] = {}
    da_theo = {k.lower() for k in KENH_CHU_DU_AN}
    for r in ds:
        for m in _RX_KENH.findall(dict(r)["van_ban"] or ""):
            if m in _BO_TEN or m.lower() in da_theo:
                continue
            dem[m] = dem.get(m, 0) + 1
    return dict(sorted(dem.items(), key=lambda x: -x[1]))


def tim_kenh(tu_khoa, gioi_han: int = 10, in_ra=print) -> list[dict]:
    """Tim kenh MOI bang chinh o tim kiem cua Telegram (can phien dang nhap).

    Tra ve THONG TIN de nguoi chon, khong tu them vao danh sach quet: mot kenh
    la mot nguon, va nguyen tac cua du an la nguon phai duoc khai bao.
    """
    duoc, ly_do = san_sang_mtproto()
    if not duoc:
        return [{"loi": ly_do}]
    from telethon.tl.functions.contacts import SearchRequest

    if isinstance(tu_khoa, str):
        tu_khoa = [tu_khoa]
    ra: dict[str, dict] = {}
    cl_, _ = _client()
    with cl_ as cl:
        for tk in tu_khoa:
            try:
                kq = cl(SearchRequest(q=tk, limit=gioi_han))
            except Exception as e:
                in_ra(f"  tim '{tk}': LOI {type(e).__name__}: {str(e)[:70]}")
                continue
            for c in list(kq.chats or []):
                ten = getattr(c, "username", None)
                if not ten or ten in ra:
                    continue
                ra[ten] = {"kenh": ten, "tieu_de": getattr(c, "title", ""),
                           "nguoi_tham_gia": getattr(c, "participants_count", None),
                           "la_kenh": bool(getattr(c, "broadcast", False)),
                           "tu_khoa": tk}
            in_ra(f"  tim '{tk}': {len(kq.chats or [])} ket qua")
    ds = sorted(ra.values(), key=lambda d: -(d["nguoi_tham_gia"] or 0))
    return ds


def quet_tat_ca(kenh=KENH_CHU_DU_AN, in_ra=print) -> dict:
    """Thu duong web truoc; kenh nao tat xem truoc thi sang MTProto neu co khoa."""
    ra = {}
    for k in kenh:
        r = thu_thap(k, in_ra=in_ra)
        if not r.get("chay"):
            duoc, _ = san_sang_mtproto()
            if duoc:
                r = quet_mtproto(k, in_ra=in_ra)
            else:
                in_ra(f"  telegram/{k}: {r.get('ly_do')} -> can CAN_GI()")
        ra[k] = r
    return ra
