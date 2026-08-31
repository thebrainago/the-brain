# -*- coding: utf-8 -*-
"""dieu_khien_xa.py - nghe lenh Telegram, KHONG ton mot token nao cua agent.

VI SAO CO FILE NAY (31/08/2026, chu du an giao)
  Yeu cau: "de lai mot luong token nho cho viec tat may tu xa". Cach dung khong
  phai de danh token - ma la **go bo phu thuoc**: neu viec tat may phai di qua
  agent thi no chet cung agent. Tien trinh nay chay rieng, dung `requests` va
  long-polling; agent het han muc, phien dong, no van nghe.

  `rem_via_tele.py` da co san cau noi nhung chi doc (/status, /bao_cao) va can
  telethon. File nay chi can `bot_token`, va them cac lenh HANH DONG.

LENH
  /trangthai   ba tru + tien trinh nen + o dia
  /bangiao     30 dong cuoi cua BAN_GIAO_SONG.md (dang lam gi, dang do gi)
  /dung        dat co DUNG_LAI - dieu phoi 24/7 nam im (khong tat may)
  /chay        go co DUNG_LAI
  /tat         hen tat may sau 60 giay
  /huy         huy lenh tat may
  /help        danh sach lenh

HAI CHOT AN TOAN
  1. `/tat` hen 60 giay chu khong tat ngay, va `/huy` go duoc - mot cu cham
     nham tren dien thoai khong duoc phep giet mot bo do dang chay 3 gio.
  2. Chi phuc vu `chat_id` da ghi trong cau hinh. Lan dau chua co thi no NHAN
     chat_id cua nguoi nhan tin dau tien roi ghi vao cau hinh (`b tele` in ra),
     tu do khoa lai.

Chay nen:
    python dieu_khien_xa.py            # vong lap nghe
    python dieu_khien_xa.py --thu      # kiem cau hinh + gui mot tin thu
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import requests

LAB = Path(__file__).resolve().parent
CAU_HINH = LAB / "config" / "tele_bridge.json"
DUNG_LAI = LAB / "DUNG_LAI.flag"
API = "https://api.telegram.org/bot{}/{}"
CHO = 25            # giay long-polling


def _ch() -> dict:
    return json.loads(CAU_HINH.read_text(encoding="utf-8-sig")) if CAU_HINH.exists() else {}


def _luu(c: dict) -> None:
    CAU_HINH.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")


def gui(text: str, chat_id=None) -> bool:
    c = _ch()
    tok, cid = c.get("bot_token"), chat_id or c.get("chat_id")
    if not tok or not cid:
        return False
    try:
        r = requests.post(API.format(tok, "sendMessage"),
                          data={"chat_id": cid, "text": text[:4000]}, timeout=20)
        return r.status_code == 200
    except Exception:
        return False


# ------------------------------------------------------------------ lenh

def _trang_thai() -> str:
    d = []
    try:
        cp = json.loads((LAB / "reports" / "control_plane.json").read_text(encoding="utf-8"))
        d.append(f"dieu phoi: {cp.get('status')} · {cp.get('health')} · "
                 f"cap nhat {cp.get('updated_at')}")
        d.append("dang chay: " + (", ".join(cp.get("workers", {}).get("running", {})) or "khong"))
    except Exception:
        d.append("dieu phoi: KHONG DOC DUOC control_plane.json")
    try:
        import shutil
        d.append(f"o dia trong: {shutil.disk_usage('C:/').free / 2**30:.1f} GB")
    except Exception:
        pass
    try:
        import ban_giao_song as BG
        tt = BG._tien_trinh_nen()
        d.append("tien trinh nen: " + (", ".join(tt) if tt else "khong co"))
    except Exception:
        pass
    d.append("co DUNG_LAI: " + ("CO" if DUNG_LAI.exists() else "khong"))
    return "\n".join(d)


def _ban_giao(n: int = 30) -> str:
    f = LAB / "BAN_GIAO_SONG.md"
    if not f.exists():
        return "chua co BAN_GIAO_SONG.md"
    return "\n".join(f.read_text(encoding="utf-8").splitlines()[-n:])


def _tat_may() -> str:
    subprocess.run(["shutdown", "/s", "/t", "60", "/c", "THE BRAIN: lenh tu Telegram"],
                   capture_output=True)
    return "Da hen TAT MAY sau 60 giay. Go /huy neu cham nham."


def _huy_tat() -> str:
    r = subprocess.run(["shutdown", "/a"], capture_output=True, text=True)
    return "Da huy lenh tat may." if r.returncode == 0 else "Khong co lenh tat nao dang cho."


def xu_ly(van: str) -> str:
    v = (van or "").strip().lower().split()[0] if van and van.strip() else ""
    if v in ("/trangthai", "/status"):
        return _trang_thai()
    if v == "/bangiao":
        return _ban_giao()
    if v == "/dung":
        DUNG_LAI.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        return "Da dat co DUNG_LAI - dieu phoi se nam im. /chay de go."
    if v == "/chay":
        DUNG_LAI.unlink(missing_ok=True)
        return "Da go co DUNG_LAI."
    if v == "/tat":
        return _tat_may()
    if v == "/huy":
        return _huy_tat()
    if v in ("/help", "/start"):
        return ("/trangthai  he dang the nao\n/bangiao  dang lam gi, dang do gi\n"
                "/dung /chay  dieu phoi 24/7\n/tat  tat may sau 60s · /huy  huy lai")
    return "Khong hieu. /help de xem lenh."


# ------------------------------------------------------------------ vong lap

def _mot_luot(offset: int | None) -> int | None:
    """Mot luot getUpdates. Tra offset moi (None neu khong doi)."""
    c = _ch()
    tok = c.get("bot_token")
    if not tok:
        return offset
    try:
        r = requests.get(API.format(tok, "getUpdates"),
                         params={"timeout": CHO, "offset": offset}, timeout=CHO + 10)
        kq = r.json()
    except Exception:
        time.sleep(5)
        return offset
    for up in kq.get("result", []):
        offset = up["update_id"] + 1
        tin = up.get("message") or up.get("edited_message") or {}
        cid = (tin.get("chat") or {}).get("id")
        van = tin.get("text") or ""
        if not cid:
            continue
        if not c.get("chat_id"):          # chot an toan 2: nhan chu lan dau
            c["chat_id"] = cid
            _luu(c)
        elif int(cid) != int(c["chat_id"]):
            continue                       # nguoi la - bo qua, khong tra loi
        gui(xu_ly(van), cid)
    return offset


def main(argv: list) -> int:
    c = _ch()
    if not c.get("bot_token"):
        print("THIEU bot_token trong config/tele_bridge.json")
        return 2
    if "--thu" in argv:
        print("chat_id:", c.get("chat_id") or "(chua co - hay nhan tin cho bot mot lan)")
        print("gui thu:", gui("THE BRAIN: dieu khien xa da san sang. /help"))
        return 0
    print("[dieu_khien_xa] dang nghe...", flush=True)
    off = None
    while True:
        off = _mot_luot(off)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
