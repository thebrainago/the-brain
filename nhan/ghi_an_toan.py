# -*- coding: utf-8 -*-
"""ghi_an_toan.py - SUA MOT FILE JSON MA KHONG MAT THAY DOI CUA NGUOI KHAC.

## Van de

`b ho-so` muc 11.10 do duoc 8 tai nguyen dung chung khi chay nhieu phien. Thu
**khong bao loi** dung thu hai la `config/*.json`:

    phien A doc {..., "x": 1}
    phien B doc {..., "x": 1}
    phien A ghi {..., "x": 2}
    phien B ghi {..., "y": 3}      <- thay doi cua A BIEN MAT

Khong ai bao gi ca. Lan sau doc ra thi `x` van la 1, va khong co dau vet nao
cho thay da co mot lan ghi bi nuot.

## Vi sao khong dung os.replace khong

`os.replace` nguyen tu o buoc DOI TEN, nhung no khong khoa khoang doc-sua-ghi.
Va tren Windows no **NEM** khi dich dang bi tien trinh khac mo - bai hoc
`24-7-chet-vi-lease-windows`: lease bang file chet vi dung cho do, va trieu
chung doc duoc chi la rc=1 khong traceback.

Nen o day: khoa lien tien trinh cho ca khoang doc-sua-ghi, `os.replace` co thu
lai, roi **doc lai xac nhan**. Va khac `du_lieu._ghi_cache` (nuot loi la dung,
vi cache hong thi tinh lai duoc), file nay **nem loi** - mot cau hinh ghi hut
la mot quyet dinh bi mat.

Dung:

    from nhan import ghi_an_toan as GAT

    def bat_slot(d):
        d.setdefault("slots", []).append({"ten": "s2"})
        return d

    GAT.sua_json(TEP, bat_slot)
"""
from __future__ import annotations

import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

#: Khoa cu hon nguong nay coi nhu mo coi (chu da chet giua chung).
HAN_KHOA_GIAY = 120.0


class KhongLayDuocKhoa(RuntimeError):
    """Het gio cho khoa. La 'cho luot', khong phai loi cua du lieu."""


class GhiHut(RuntimeError):
    """Ghi xong doc lai KHONG khop. Loi nang - dung im lang di tiep."""


def _pid_song(pid: int) -> bool:
    if pid == os.getpid():
        return True
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        return True          # khong biet thi coi la CON SONG - an toan hon


@contextmanager
def khoa(duong_dan: Path, cho_giay: float = 30.0, nhip: float = 0.15):
    """Khoa lien tien trinh cho MOT file, bang `O_CREAT|O_EXCL`.

    `O_EXCL` la nguyen tu o muc he dieu hanh tren ca Windows lan POSIX - do la
    ly do dung no chu khong dung "kiem ton tai roi tao".
    """
    tep = Path(str(duong_dan) + ".lock")
    tep.parent.mkdir(parents=True, exist_ok=True)
    het = time.time() + cho_giay
    while True:
        try:
            fd = os.open(str(tep), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            # Thu hoi khoa mo coi: chu da chet, hoac khoa qua han.
            #
            # CA KHOI NAY PHAI CHIU DUOC VIEC KHOA BIEN MAT GIUA CHUNG. Test
            # 10 tien trinh bat duoc dung loi do: giua `O_EXCL` that bai va
            # `tep.stat()`, chu khoa da tra khoa xong - `stat` nem
            # FileNotFoundError va no thoat ra ngoai nhu mot loi that. Thay vi
            # vay: khoa bien mat nghia la den luot ta, quay lai vong ngay.
            try:
                chu = int(tep.read_text(encoding="utf-8").strip() or 0)
                qua_han = time.time() - tep.stat().st_mtime > HAN_KHOA_GIAY
            except (FileNotFoundError, ValueError):
                continue
            except OSError:
                chu, qua_han = 0, False
            if qua_han or not _pid_song(chu):
                tep.unlink(missing_ok=True)
                continue
            if time.time() >= het:
                raise KhongLayDuocKhoa(
                    "khong lay duoc khoa %s sau %.0fs (pid %s dang giu)"
                    % (tep.name, cho_giay, chu))
            time.sleep(nhip)
    try:
        yield
    finally:
        try:
            if tep.exists() and tep.read_text(encoding="utf-8").strip() \
                    == str(os.getpid()):
                tep.unlink(missing_ok=True)
        except Exception:
            pass


def _doi_ten(tam: Path, dich: Path, lan: int = 8) -> None:
    """`os.replace` co thu lai. Het lan thi NEM - khong nuot.

    Tren Windows buoc nay that bai khi dich dang bi tien trinh khac MO doc.
    Do la loi tam thoi nen thu lai la dung; nhung neu sau 8 lan van hong thi
    day la loi that, va nuot no chinh la cach 24/7 tung chet ma so "thoi gian
    song" van dep.
    """
    cho = 0.05
    for i in range(lan):
        try:
            os.replace(tam, dich)
            return
        except OSError:
            if i == lan - 1:
                raise
            time.sleep(cho)
            cho *= 2


def doc_json(duong_dan: Path, mac_dinh=None):
    p = Path(duong_dan)
    if not p.exists():
        return {} if mac_dinh is None else mac_dinh
    return json.loads(p.read_text(encoding="utf-8-sig"))


def sua_json(duong_dan, ham_sua, cho_giay: float = 30.0, mac_dinh=None):
    """doc -> `ham_sua(d)` -> ghi tam -> doi ten -> DOC LAI XAC NHAN.

    Ca khoang nam trong khoa lien tien trinh, nen hai tien trinh sua cung file
    khong the nuot thay doi cua nhau.

    `ham_sua` nhan dict va tra ve dict moi (tra `None` = giu nguyen ban da sua
    tai cho). Loi trong `ham_sua` thi khong ghi gi ca.
    """
    p = Path(duong_dan)
    with khoa(p, cho_giay=cho_giay):
        d = doc_json(p, mac_dinh)
        moi = ham_sua(d)
        if moi is None:
            moi = d
        vb = json.dumps(moi, ensure_ascii=False, indent=1)
        tam = p.with_suffix(p.suffix + ".%d.tmp" % os.getpid())
        tam.write_text(vb, encoding="utf-8")
        try:
            _doi_ten(tam, p)
        finally:
            tam.unlink(missing_ok=True)
        # DOC LAI. Mot lan ghi "thanh cong" ma doc ra khac la truong hop phai
        # bao ngay: dia day, quyen, hay antivirus giu file deu hien ra kieu do.
        lai = doc_json(p, mac_dinh)
        if lai != moi:
            raise GhiHut("ghi %s xong nhung doc lai khong khop" % p.name)
        return moi
