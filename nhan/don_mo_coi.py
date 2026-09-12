# -*- coding: utf-8 -*-
"""don_mo_coi.py - Tim va don TIEN TRINH MO COI dang an CPU.

## Chuyen da xay ra 12/09/2026

Toi phong vai ban quet nang bang `nohup ... &`. Tien trinh CHA thoat, nhung
`multiprocessing.Pool` cua no de lai **24 worker con** - va Pool tu SINH LAI
worker khi mot con chet, nen giet con khong giai quyet duoc gi.

Ket qua do duoc: **20 tien trinh x 85-92% CPU = 1.951% (19,5/20 loi)** trong
hon 20 phut, trong khi khong mot viec nao dang thuc su chay.

Va hau qua that su khong phai la "may cham". `qwen` co bo dieu toc: no do CPU
truoc khi phong viec, thay 100% thi **tu choi phong** - dung thiet ke. Nen he
nam im, bang viec day nhung `dang chay 0`, va nhat ky chi ghi mot dong
`con -1.0 loi` lap lai moi hai phut.

**Tren VPS chay nhieu thang khong nguoi truc, do la he tu te liet ma khong ai
biet.** Khong loi, khong canh bao, chi la khong co gi tien trien.

## Dau hieu nhan ra mot tien trinh MO COI

    1. la python
    2. KHONG thuoc cay cua mot tien trinh dieu phoi dang song (qwen / day_viec /
       dieu_phoi / phien Claude hien tai)
    3. cha cua no da chet, HOAC cha la mot Pool ma ong cua no da chet
    4. da song lau hon `TUOI_TOI_THIEU` (de khong giet nham viec vua phong)

Diem 3 la cho de sai: giet worker ma de Pool cha song thi Pool sinh lai ngay.
Phai giet **CA CAY** tu goc.

Chay:  python -m nhan.don_mo_coi          chi BAO, khong giet
       python -m nhan.don_mo_coi --don    giet that
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

#: Duoi tuoi nay thi khong dung toi - co the la viec vua duoc phong.
TUOI_TOI_THIEU = 300.0
#: Duoi muc CPU nay thi khong phai van de, du co mo coi.
CPU_DANG_KE = 5.0
#: Dau hieu mot tien trinh la DIEU PHOI - cay cua no duoc mien.
DIEU_PHOI = ("qwen.chay", "day_viec.py", "dieu_phoi.py", "pytest")


def _cmdline(p) -> str:
    try:
        return " ".join(p.cmdline())
    except Exception:
        return ""


def quet(tuoi_toi_thieu: float = TUOI_TOI_THIEU) -> dict:
    """-> {mien, mo_coi, cpu_mo_coi}. KHONG giet gi."""
    try:
        import psutil
    except ImportError:
        return {"loi": "khong co psutil"}

    song = {}
    for p in psutil.process_iter(["name", "ppid", "create_time"]):
        try:
            if "python" in (p.info.get("name") or "").lower():
                song[p.pid] = p
        except Exception:
            continue

    # 1) Cay duoc mien: dieu phoi + toan bo con chau cua no
    mien: set[int] = set()
    for pid, p in song.items():
        if any(d in _cmdline(p) for d in DIEU_PHOI):
            mien.add(pid)
            try:
                for c in p.children(recursive=True):
                    mien.add(c.pid)
            except Exception:
                pass
    # tien trinh cua CHINH phien nay
    mien.add(__import__("os").getpid())

    # 2) Mo coi: cha khong con trong bang tien trinh, hoac cha cung mo coi
    tat_ca = {q.pid for q in psutil.process_iter()}
    mo_coi = []
    for pid, p in song.items():
        if pid in mien:
            continue
        try:
            tuoi = time.time() - p.info["create_time"]
            if tuoi < tuoi_toi_thieu:
                continue
            ppid = p.info["ppid"]
            cha_song = ppid in tat_ca
            if cha_song and ppid in song and song[ppid].pid not in mien:
                # cha cung la python va cung khong duoc mien -> xet ONG
                try:
                    ong = song[ppid].ppid()
                except Exception:
                    ong = None
                if ong in tat_ca:
                    continue          # ca cay con cha that -> khong phai mo coi
            elif cha_song:
                continue
            mo_coi.append({"pid": pid, "ppid": ppid, "tuoi": int(tuoi),
                           "cpu": p.cpu_percent(None), "lenh": _cmdline(p)[:70]})
        except Exception:
            continue

    if mo_coi:
        time.sleep(1.0)
        for m in mo_coi:
            try:
                m["cpu"] = round(song[m["pid"]].cpu_percent(None), 1)
            except Exception:
                m["cpu"] = 0.0
    return {"mien": len(mien), "mo_coi": mo_coi,
            "cpu_mo_coi": round(sum(m["cpu"] for m in mo_coi), 1)}


def _goc_cay(mo_coi: list[dict]) -> list[int]:
    """Goc cua moi cay mo coi - giet goc chu khong giet la.

    Pool SINH LAI worker khi con chet. Giet 20 worker ma de Pool cha song thi
    sau 6 giay chung quay lai day du - do duoc 12/09/2026.
    """
    cha = {m["pid"]: m["ppid"] for m in mo_coi}
    goc = set()
    for pid in cha:
        # lan LEN trong khi cha cung la mo coi -> tim dinh cua chuoi
        dinh, tham = pid, 0
        while cha.get(dinh) in cha and tham < 64:
            dinh = cha[dinh]
            tham += 1
        # Dinh la mo coi cao nhat. Cha cua no la tien trinh CON SONG - neu do la
        # mot Pool thi phai giet ca no, khong thi no sinh lai worker sau vai
        # giay (do that 12/09: giet 20 worker, 6 giay sau chung quay lai du).
        goc.add(cha.get(dinh, dinh))
    return sorted(goc)


def don(tuoi_toi_thieu: float = TUOI_TOI_THIEU, in_ra=print) -> dict:
    k = quet(tuoi_toi_thieu)
    if k.get("loi") or not k["mo_coi"]:
        if in_ra:
            in_ra("khong co tien trinh mo coi (mien %s cay dieu phoi)"
                  % k.get("mien"))
        return k
    goc = _goc_cay(k["mo_coi"])
    if in_ra:
        in_ra("MO COI: %d tien trinh, %.0f%% CPU, %d cay"
              % (len(k["mo_coi"]), k["cpu_mo_coi"], len(goc)))
    n = 0
    for pid in goc:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           capture_output=True, timeout=30)
            n += 1
        except Exception as e:
            if in_ra:
                in_ra("  khong giet duoc %d: %s" % (pid, e))
    k["da_giet_cay"] = n
    if in_ra:
        in_ra("da giet %d cay" % n)
    return k


def main(argv: list[str]) -> int:
    if "--don" in argv:
        don()
        return 0
    k = quet()
    if k.get("loi"):
        print(k["loi"])
        return 1
    print("mien (cay dieu phoi): %d tien trinh" % k["mien"])
    print("MO COI: %d tien trinh, %.0f%% CPU" % (len(k["mo_coi"]), k["cpu_mo_coi"]))
    for m in sorted(k["mo_coi"], key=lambda x: -x["cpu"])[:12]:
        print("  pid %-7d cha %-7d %5.0f%%  %5ds  %s"
              % (m["pid"], m["ppid"], m["cpu"], m["tuoi"], m["lenh"]))
    if k["mo_coi"]:
        print("\nde don: python -m nhan.don_mo_coi --don")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
