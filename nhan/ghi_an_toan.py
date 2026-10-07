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
    """`True` khi KHONG CHAC. Cuop mot khoa cua nguoi con song la mat du lieu;
    cho them mot nhip thi chi mat mot nhip."""
    if pid <= 0:
        # `pid <= 0` KHONG phai mot tien trinh - no la "chua doc duoc pid".
        # `psutil.pid_exists(0)` tra `False` tren Linux, va do la duong dan
        # dan thang toi viec cuop khoa cua mot chu con song. Xem `khoa()`.
        return True
    if pid == os.getpid():
        return True
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        return True          # khong biet thi coi la CON SONG - an toan hon


try:
    import fcntl as _fcntl          # POSIX
except ImportError:                 # Windows
    _fcntl = None


@contextmanager
def _khoa_flock(duong_dan: Path, cho_giay: float, nhip: float):
    """Khoa bang `fcntl.flock` - khoa cua HE DIEU HANH.

    ## VI SAO DUONG NAY TON TAI (them 20/09/2026)

    So do `O_CREAT|O_EXCL` ben duoi phai tu quan li "khoa mo coi": chu chet
    giua chung thi ai do phai xoa khoa ho. Nhung `xoa roi tao lai` KHONG
    nguyen tu, nen hai nguoi cho cung ket luan "chu da chet" se cung xoa va
    cung tao - va mot lan ghi bien mat. Do duoc: **3 lan cuop tren 200 luot
    ghi**, va bai `test_muoi_tien_trinh_sua_mot_file` hong 3/3 tren `main`.

    `flock` khong co van de do vi **nhan tu tra khoa khi tien trinh chet**:
    khong con khai niem "khoa mo coi", nen khong con phep cuop de ma dua.

    Windows khong co `fcntl` - o do van di duong `O_EXCL`. Duong Windows
    KHONG doi, co chu dich: may chu du an chay Windows va toi khong kiem duoc
    nhanh do tu cloud. `msvcrt.locking` la thu tuong duong, va no dang cho mot
    phien co may that de doi chung.
    """
    tep = Path(str(duong_dan) + ".lock")
    tep.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(tep), os.O_CREAT | os.O_RDWR)
    het = time.time() + cho_giay
    try:
        while True:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
                break
            except OSError:
                if time.time() >= het:
                    raise KhongLayDuocKhoa(
                        "khong lay duoc khoa %s sau %.0fs" % (tep.name, cho_giay))
                time.sleep(nhip)
        try:
            os.ftruncate(fd, 0)
            os.write(fd, str(os.getpid()).encode())
        except OSError:
            pass
        try:
            yield
        finally:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_UN)
            except OSError:
                pass
    finally:
        os.close(fd)
        # KHONG `unlink`: mot file bi xoa trong khi nguoi khac dang cho khoa
        # tren chinh no se lam ho cho tren mot inode khong con ai dung toi.
        # File `.lock` con lai la rac VO HAI (0-2 byte), khong phai trang thai.


@contextmanager
def khoa(duong_dan: Path, cho_giay: float = 30.0, nhip: float = 0.15):
    """Khoa lien tien trinh cho MOT file.

    POSIX -> `fcntl.flock` (nhan giu, tu tra khi tien trinh chet).
    Windows -> `O_CREAT|O_EXCL` + tu quan li khoa mo coi, xem `_khoa_flock`
    de biet vi sao so do do co mot dua chua bit duoc.
    """
    if _fcntl is not None:
        with _khoa_flock(duong_dan, cho_giay, nhip):
            yield
        return
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
            # KHOA RONG KHAC KHOA CUA NGUOI CHET (sua 20/09/2026).
            #
            # `os.open(O_CREAT|O_EXCL)` va `os.write(fd, pid)` la HAI buoc.
            # Giua chung, file DA TON TAI nhung con RONG. Ban cu doc ra chuoi
            # rong roi `int("" or 0)` -> `chu = 0`, va `psutil.pid_exists(0)`
            # tra `False` tren Linux -> `not _pid_song(0)` la True -> **xoa
            # khoa cua mot chu dang song** roi di tiep. Hai tien trinh cung
            # vao vung toi han, va mot lan ghi bien mat.
            #
            # Do duoc: bai `test_muoi_tien_trinh_sua_mot_file` (10 tien trinh
            # x 20 lan) MAT 9/200 lan ghi, lap lai 3/3. Trong mot module ma
            # viec duy nhat cua no la khong de mat lan ghi nao.
            #
            # Khoa rong = chu VUA tao, chua kip ghi pid -> coi nhu CON SONG.
            # Neu chu chet dung giua hai buoc do thi khoa rong se qua han sau
            # `HAN_KHOA_GIAY` va duoc thu hoi o chinh nhanh `qua_han`.
            try:
                noi_dung = tep.read_text(encoding="utf-8").strip()
                qua_han = time.time() - tep.stat().st_mtime > HAN_KHOA_GIAY
            except (FileNotFoundError, ValueError):
                continue
            except OSError:
                noi_dung, qua_han = "", False
            try:
                chu = int(noi_dung) if noi_dung else -1
            except ValueError:
                chu = -1          # rac trong khoa -> khong ket luan la chet
            # CON MOT DUA CHUA BIT (ghi lai 20/09/2026, KHONG vui suot).
            #
            # `unlink` roi `O_EXCL` lai KHONG nguyen tu: hai nguoi cho cung
            # ket luan "chu da chet" thi ca hai cung xoa va ca hai cung tao
            # lai - nguoi sau xoa mat khoa cua nguoi truoc vua lay, va mot lan
            # ghi bien mat. Do duoc: **3 lan cuop tren 200 luot ghi**.
            #
            # Toi da thu bit bang `os.replace` sang mot ten duy nhat (phep
            # kiem-va-lay nguyen tu). No het mat luot ghi, NHUNG sinh ra DOI
            # KHOA: 1/12 lan chay treo het 60 giay. Doi mot loi lay mot loi
            # khac thi khong phai la sua.
            #
            # Duong dung la khoa cua HE DIEU HANH - `fcntl.flock` tren POSIX,
            # `msvcrt.locking` tren Windows - vi nhan tu tra khoa khi tien
            # trinh chet nen khong con logic "mo coi" de ma dua. May chu du an
            # chay Windows, va toi khong kiem duoc nhanh do tu day, nen KHONG
            # tu y doi. Da xep don `vet-khoa-flock`.
            #
            # Phan DA sua o tren (khoa RONG khong bi doc thanh "pid 0 da
            # chet") la phan chac chan dung va no da ha ty le hong tu 3/3
            # xuong ~1/12.
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
