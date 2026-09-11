# -*- coding: utf-8 -*-
"""khoa_tester.py - MOT CUA CO KHOA cho `terminal64.exe`.

## Rang buoc VAT LY, khong phai lua chon

`chay_tester_kho` ghi de **cung mot** `MQL5/Experts/<TEN_EA>.mq5`, **cung mot**
`.ini`, **cung mot** `.xml` ket qua - va may chi co MOT `terminal64.exe`. Hai
viec tester chay cung luc thi:

  - ghi de ket qua cua nhau,
  - **va khong ai bao loi**.

Bang so ra doc y het mot ket qua that. Day la dang hong dat nhat trong ca du an:
no khong lam gi sap, no chi lam moi con so sai.

Truoc 11/09/2026 rang buoc do duoc giu bang KY LUAT CON NGUOI: mot dong trong
`qwen/NHIEM_VU.json` ghi "lan TESTER toi da 1 viec", va mot dong trong CLAUDE.md
nhac lai. Ky luat con nguoi hong im lang - nhat la khi co ca Claude, qwen va chu
du an cung ngoi tren mot may.

## Cach khoa

Khoa theo FILE + PID, khong theo bien trong tien trinh: ba tien trinh khac nhau
khong nhin thay bien cua nhau.

    with khoa_tester.giu("chay_tester_kho US500Cash"):
        ...chay tester...

Khoa CU (chu giu da chet) duoc thu hoi tu dong - neu khong thi mot lan Ctrl-C se
khoa cung ca day chuyen cho toi khi co nguoi vao xoa file.
"""
from __future__ import annotations

import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
KHOA = LAB / "config" / "khoa_tester.json"

#: Khoa cu hon nguong nay ma chu giu khong con song -> thu hoi. Mot lan chay
#: tester day du (8.241 phep thu) do duoc la 82 giay; mot lan chay nang nhat tu
#: truoc den nay khoang 20 phut. 45 phut la bien an toan.
HAN_GIAY = 45 * 60


def _con_song(pid: int) -> bool:
    if not pid or pid == os.getpid():
        return pid == os.getpid()
    try:
        import psutil
        return psutil.pid_exists(int(pid))
    except Exception:
        return True          # khong biet thi coi nhu CON SONG - an toan hon


def dang_giu() -> dict | None:
    """-> {pid, viec, luc} hoac None. Tu thu hoi khoa mo coi."""
    if not KHOA.exists():
        return None
    try:
        d = json.loads(KHOA.read_text(encoding="utf-8"))
    except Exception:
        KHOA.unlink(missing_ok=True)
        return None
    qua_han = time.time() - float(d.get("luc") or 0) > HAN_GIAY
    if qua_han or not _con_song(int(d.get("pid") or 0)):
        KHOA.unlink(missing_ok=True)
        return None
    return d


def thu_lay(viec: str) -> dict:
    """Lay khoa, KHONG cho. -> {duoc, ly_do, chu}"""
    cu = dang_giu()
    if cu and int(cu.get("pid") or 0) != os.getpid():
        return {"duoc": False, "chu": cu, "ly_do": (
            f"tester dang bi giu boi pid {cu.get('pid')} ({cu.get('viec')}) "
            f"tu {cu.get('luc_doc')}. Hai viec tester cung luc se ghi de ket qua "
            f"cua nhau VA khong ai bao loi.")}
    KHOA.parent.mkdir(exist_ok=True)
    KHOA.write_text(json.dumps(
        {"pid": os.getpid(), "viec": viec, "luc": time.time(),
         "luc_doc": time.strftime("%Y-%m-%d %H:%M:%S")},
        ensure_ascii=False), encoding="utf-8")
    return {"duoc": True, "ly_do": "", "chu": None}


def tra() -> None:
    d = dang_giu()
    if d and int(d.get("pid") or 0) == os.getpid():
        KHOA.unlink(missing_ok=True)


@contextmanager
def giu(viec: str, cho_giay: float = 0.0, nhip: float = 5.0):
    """Giu khoa trong mot khoi `with`. `cho_giay > 0` thi CHO den khi lay duoc.

    Mac dinh KHONG cho: mot viec tester bi tu choi thi nen bao ngay de bo dieu
    phoi xep lai, chu khong nen dung do chiem mot slot CPU.
    """
    het = time.time() + cho_giay
    while True:
        r = thu_lay(viec)
        if r["duoc"]:
            break
        if time.time() >= het:
            raise TesterDangBan(r["ly_do"])
        time.sleep(nhip)
    try:
        yield r
    finally:
        tra()


def phong(exe, ini, tran: int = 3600, nhip: float = 6.0,
          dong_truoc=None, viec: str = "", cho_giay: float = 0.0) -> float:
    """PHONG terminal64 TRONG KHOA roi cho no thoat. -> so giay da chay.

    Mot cua duy nhat cho moi script. Truoc 11/09 moi script tu `Popen` lay, va
    quet ma nguon thay 9 file lam vay - tuc cai khoa co viet cung khong an gi.
    """
    import subprocess
    with giu(viec or f"phong {Path(ini).name}", cho_giay=cho_giay):
        if dong_truoc:
            dong_truoc()
        t0 = time.time()
        subprocess.Popen([str(exe), "/config:%s" % ini])
        while time.time() - t0 < tran:
            time.sleep(nhip)
            r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                               capture_output=True, text=True)
            if "terminal64.exe" not in r.stdout:
                break
        else:
            if dong_truoc:
                dong_truoc()
        return round(time.time() - t0, 1)


class TesterDangBan(RuntimeError):
    """Nem ra khi khong lay duoc khoa. TEN loai co y: no khong phai mot loi cua
    phep thu, no la 'cho luot'."""


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tha":
        KHOA.unlink(missing_ok=True)
        print("da xoa khoa")
    else:
        d = dang_giu()
        print(json.dumps(d or {"trong": True}, ensure_ascii=False, indent=1))
