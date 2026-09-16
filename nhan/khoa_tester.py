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


def _tep(ten: str | None) -> Path:
    """File khoa cua MOT slot. `None` -> khoa cu (mot slot, ten cu, tuong thich).

    Them 16/09 cho goi G2-A: khoa phai theo SLOT chu khong toan cuc, neu khong
    thi hai slot tester van doi nhau du chung ghi vao hai thu muc du lieu khac
    hau. Giu nguyen ten file cu cho slot mac dinh de khong bo roi khoa dang giu
    luc nang cap.
    """
    return KHOA if not ten else LAB / "config" / ("khoa_tester_%s.json" % ten)

#: Khoa cu hon nguong nay ma chu giu khong con song -> thu hoi. Mot lan chay
#: tester day du (8.241 phep thu) do duoc la 82 giay; mot lan chay nang nhat tu
#: truoc den nay khoang 20 phut. 45 phut la bien an toan.
HAN_GIAY = 45 * 60


class TesterDangBan(RuntimeError):
    """Nem ra khi khong lay duoc khoa. TEN loai co y: no khong phai mot loi cua
    phep thu, no la 'cho luot'."""


def _con_song(pid: int) -> bool:
    if not pid or pid == os.getpid():
        return pid == os.getpid()
    try:
        import psutil
        return psutil.pid_exists(int(pid))
    except Exception:
        return True          # khong biet thi coi nhu CON SONG - an toan hon


def dang_giu(ten: str | None = None) -> dict | None:
    """-> {pid, viec, luc} hoac None. Tu thu hoi khoa mo coi."""
    tep = _tep(ten)
    if not tep.exists():
        return None
    try:
        d = json.loads(tep.read_text(encoding="utf-8"))
    except Exception:
        tep.unlink(missing_ok=True)
        return None
    qua_han = time.time() - float(d.get("luc") or 0) > HAN_GIAY
    if qua_han or not _con_song(int(d.get("pid") or 0)):
        tep.unlink(missing_ok=True)
        return None
    return d


def thu_lay(viec: str, ten: str | None = None) -> dict:
    """Lay khoa, KHONG cho. -> {duoc, ly_do, chu}"""
    cu = dang_giu(ten)
    if cu and int(cu.get("pid") or 0) != os.getpid():
        return {"duoc": False, "chu": cu, "ly_do": (
            f"tester dang bi giu boi pid {cu.get('pid')} ({cu.get('viec')}) "
            f"tu {cu.get('luc_doc')}. Hai viec tester cung luc se ghi de ket qua "
            f"cua nhau VA khong ai bao loi.")}
    tep = _tep(ten)
    tep.parent.mkdir(exist_ok=True)
    tep.write_text(json.dumps(
        {"pid": os.getpid(), "viec": viec, "slot": ten, "luc": time.time(),
         "luc_doc": time.strftime("%Y-%m-%d %H:%M:%S")},
        ensure_ascii=False), encoding="utf-8")
    return {"duoc": True, "ly_do": "", "chu": None}


def tra(ten: str | None = None) -> None:
    d = dang_giu(ten)
    if d and int(d.get("pid") or 0) == os.getpid():
        _tep(ten).unlink(missing_ok=True)


@contextmanager
def giu(viec: str, cho_giay: float = 0.0, nhip: float = 5.0,
        ten: str | None = None):
    """Giu khoa trong mot khoi `with`. `cho_giay > 0` thi CHO den khi lay duoc.

    Mac dinh KHONG cho: mot viec tester bi tu choi thi nen bao ngay de bo dieu
    phoi xep lai, chu khong nen dung do chiem mot slot CPU.
    """
    het = time.time() + cho_giay
    while True:
        r = thu_lay(viec, ten)
        if r["duoc"]:
            break
        if time.time() >= het:
            raise TesterDangBan(r["ly_do"])
        time.sleep(nhip)
    try:
        yield r
    finally:
        tra(ten)


def phong(exe, ini, tran: int = 3600, nhip: float = 6.0,
          dong_truoc=None, viec: str = "", cho_giay: float = 0.0,
          ten: str | None = None) -> float:
    """PHONG terminal64 TRONG KHOA roi cho no thoat. -> so giay da chay.

    Mot cua duy nhat cho moi script. Truoc 11/09 moi script tu `Popen` lay, va
    quet ma nguon thay 9 file lam vay - tuc cai khoa co viet cung khong an gi.
    """
    import subprocess
    with giu(viec or f"phong {Path(ini).name}", cho_giay=cho_giay, ten=ten):
        if dong_truoc:
            dong_truoc()
        t0 = time.time()
        p = subprocess.Popen([str(exe), "/config:%s" % ini])
        # CHO DUNG TIEN TRINH MINH DE RA, khong quet `tasklist` theo TEN ANH.
        #
        # Sua 16/09 (goi G2-A): ban cu doi den khi KHONG CON terminal64.exe nao
        # tren may. Voi mot slot thi dung; voi hai slot thi slot nay "xong" ngay
        # khi slot kia con dang chay, hoac ngoi doi ca luot cua slot kia. Ca hai
        # deu sai va **khong cai nao bao loi**.
        while time.time() - t0 < tran:
            if p.poll() is not None:
                break
            time.sleep(nhip)
        else:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                               capture_output=True)
            except Exception:
                pass
        return round(time.time() - t0, 1)


def dong_terminal(viec: str = "") -> bool:
    """`taskkill /F /IM terminal64.exe` NHUNG chi khi khong ai khac dang giu khoa.

    Do 12/09/2026: bon script (`mt5_worker.py`, `lab.py`, `mt5_chay_ichimoku.py`,
    `chay_tester_z5.py`) goi thang `taskkill /F /IM terminal64.exe` de don duong
    truoc khi chay. Lenh do giet MOI terminal, ke ca luot tester ma nguoi/tien
    trinh khac dang chay - roi ben kia doc file ket qua CU hoac RONG **va khong
    ai bao loi**. Dung dang hong ma `khoa_tester` sinh ra de chan, nhung khoa chi
    chan duong PHONG chu khong chan duong GIET.

    Ham nay la cua duy nhat de giet terminal. Tra True neu da giet.
    Nem `TesterDangBan` neu tien trinh KHAC dang giu khoa - luc do giet la pha
    viec cua ho.
    """
    import subprocess
    # Nhin MOI khoa slot, khong chi khoa mac dinh. Voi nhieu slot thi
    # `taskkill /IM terminal64.exe` giet luon terminal cua slot khac - dung cai
    # hong ma chinh ham nay sinh ra de chan, chi khac la o quy mo slot.
    cu = dang_giu()
    for q in sorted((LAB / "config").glob("khoa_tester_*.json")):
        k = dang_giu(q.stem.replace("khoa_tester_", ""))
        if k and int(k.get("pid") or 0) != os.getpid():
            cu = k
            break
    if cu and int(cu.get("pid") or 0) != os.getpid():
        raise TesterDangBan(
            f"KHONG giet terminal64: pid {cu.get('pid')} ({cu.get('viec')}) dang "
            f"chay tester tu {cu.get('luc_doc')}. Giet bay gio la pha ket qua cua "
            f"ho, va ho se khong bao loi. Viec dang cho: {viec or '?'}")
    subprocess.run(["taskkill", "/F", "/IM", "terminal64.exe"], capture_output=True)
    time.sleep(2)
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tha":
        KHOA.unlink(missing_ok=True)
        print("da xoa khoa")
    else:
        d = dang_giu()
        print(json.dumps(d or {"trong": True}, ensure_ascii=False, indent=1))
