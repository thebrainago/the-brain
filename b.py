# -*- coding: utf-8 -*-
"""b — MOT cua vao cho moi viec hang ngay cua THE BRAIN.

Vi sao co file nay: lab co ~94 file .py o muc goc, ds/ co them 40 thu muc.
Nho ten file la viec cua may, khong phai cua nguoi. Go `b` de xem menu.

    b                 menu
    b vao             VAO PHIEN: trang thai song + ban giao hom qua
    b ket "tom tat"   KET PHIEN: chot git + sinh TIEP_TUC_MAI.md cho mai
    b test [tu-khoa]  chay test SONG SONG (8 tien trinh, ~1 phut thay vi 6)
    b test1 [tu-khoa] chay test MOT tien trinh (khi nghi song song lam sai)
    b toan-canh       MOT man hinh: dau vao + kho co che + tang kham pha
    b trang-thai      bang dieu khien (van hanh cua dieu phoi)
    b chay / b dung   bat / dung dieu phoi 24/7
    b canary          tu kiem engine (5 canary)
    b quet            quet_be_mat.py
    b mde             chay_bang_mde.py
    b mde-nap [khung] nap TRUOC bang MDE cho ca be mat (D1: ~4 phut, mot lan)
    b san             EVO di san cong cu/du an ngoai de tich hop
    b san-xem         xem kho cong cu da tim duoc
    b san-quet        nhat lai cong cu tu TOAN BO ban doc da co (khong tai gi moi)
    b trinh-duyet     mo Chrome bot + CDP 9224 (de doc nguon can dang nhap)
    b ds [args]       chay pytest ben ds/ (kho DeepSeek)
    b tim <tu>        tim trong MA NGUON (bo qua data/reports/backups)
    b luu "msg"       chot nhanh vao git (thay cho copy vao backups/)
    b lich [n]        n commit gan nhat
    b lui <file>      tra mot file ve ban da chot
    b ban-do          ban do thu muc + file nao lam gi
    b profile <file>  do cProfile mot script, in 25 dong ton nhat

Nguyen tac: file nay chi DIEU HUONG. Khong co logic nghien cuu nao o day.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
GOC = LAB.parent
DS = GOC / "ds"

PY = Path(r"C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe")
if not PY.exists():
    PY = Path(sys.executable)


def chay(cmd: list, cwd: Path = LAB) -> int:
    return subprocess.call([str(c) for c in cmd], cwd=str(cwd))


def _git(args: list, cwd: Path = GOC, im: bool = False):
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=im, text=True, encoding="utf-8", errors="ignore")
    return r


# ----------------------------------------------------------------- cac lenh
def c_vao(_):
    return chay([PY, LAB / "BAN_GIAO.py"])


def c_ket(a):
    return chay([PY, LAB / "KET_PHIEN.py", *a])


def c_test(a, song_song=True):
    cmd = [PY, "-m", "pytest", "-q"]
    if song_song:
        cmd += ["-n", "8", "--dist", "loadfile"]
    if a:
        cmd += ["-k", " or ".join(a)]
    return chay(cmd)


def c_toan_canh(_):
    return chay([PY, LAB / "toan_canh.py"])


def c_trang_thai(_):
    return chay([PY, LAB / "bang_dieu_khien.py"])


def c_chay(_):
    (LAB / "DUNG_LAI").unlink(missing_ok=True)
    return chay([PY, LAB / "dieu_phoi.py"])


def c_dung(_):
    (LAB / "DUNG_LAI").write_text("dung\n", encoding="utf-8")
    print("da dat co DUNG_LAI — dieu phoi se dung sau khi tru dang chay xong luot.")
    return 0


def c_canary(_):
    return chay([PY, LAB / "nhan" / "canary.py", "--tu-kiem"])


def c_quet(a):
    return chay([PY, LAB / "quet_be_mat.py", *a])


def c_mde(a):
    return chay([PY, LAB / "chay_bang_mde.py", *a])


def c_mde_nap(a):
    return chay([PY, LAB / "nap_truoc_mde.py", *a])


def c_san(a):
    return chay([PY, LAB / "nhan" / "san_cong_cu.py", *a])


def c_san_quet(_):
    return chay([PY, "-c",
                 "import sys;sys.path.insert(0,'.');"
                 "from nhan import san_cong_cu as S;S.quet_lai_thu_vien()"])


def c_san_xem(_):
    return chay([PY, LAB / "nhan" / "san_cong_cu.py", "--xem"])


def c_trinh_duyet(_):
    return chay([PY, LAB / "mo_chrome_cdp.py"])


def c_ds(a):
    if not DS.exists():
        print(f"khong thay {DS}")
        return 1
    return chay([PY, "-m", "pytest", "-q", *a], cwd=DS)


def c_tim(a):
    if not a:
        print("dung: b tim <tu khoa>")
        return 2
    loai = ["--glob=!data/**", "--glob=!data_khung/**", "--glob=!backups/**",
            "--glob=!reports/**", "--glob=!nghi_huu/**", "--glob=!__pycache__/**",
            "--glob=!.git/**", "--glob=!downloaded_codes/**", "--glob=!*.parquet"]
    for exe in ("rg", "rg.exe"):
        try:
            return subprocess.call([exe, "-n", "--color=never", *loai, a[0], str(GOC)])
        except FileNotFoundError:
            continue
    return subprocess.call(["grep", "-rn", "--include=*.py", "--include=*.md",
                            a[0], str(LAB)])


def c_luu(a):
    msg = a[0] if a else "chot nhanh"
    _git(["add", "-A"])
    r = _git(["commit", "-m", msg], im=True)
    print((r.stdout or "") + (r.stderr or ""), end="")
    return 0


def c_lich(a):
    n = a[0] if a else "15"
    return _git(["log", "--oneline", "--decorate", f"-{n}"]).returncode


def c_lui(a):
    if not a:
        print("dung: b lui <duong dan file>")
        return 2
    return _git(["restore", "--", *a]).returncode


def c_profile(a):
    if not a:
        print("dung: b profile <file.py> [args]")
        return 2
    ra = LAB / "reports" / "profile.prof"
    ra.parent.mkdir(exist_ok=True)
    rc = chay([PY, "-m", "cProfile", "-o", ra, a[0], *a[1:]])
    chay([PY, "-c",
          f"import pstats;pstats.Stats(r'{ra}').sort_stats('cumtime').print_stats(25)"])
    return rc


def c_ban_do(_):
    print((LAB / "BAN_DO.md").read_text(encoding="utf-8")
          if (LAB / "BAN_DO.md").exists() else "chua co BAN_DO.md")
    return 0


LENH = {
    "vao": c_vao, "ket": c_ket,
    "test": lambda a: c_test(a, True), "test1": lambda a: c_test(a, False),
    "toan-canh": c_toan_canh, "tc": c_toan_canh,
    "trang-thai": c_trang_thai, "tt": c_trang_thai,
    "chay": c_chay, "dung": c_dung, "canary": c_canary,
    "quet": c_quet, "mde": c_mde, "mde-nap": c_mde_nap,
    "san": c_san, "san-xem": c_san_xem, "san-quet": c_san_quet, "trinh-duyet": c_trinh_duyet,
    "ds": c_ds, "tim": c_tim,
    "luu": c_luu, "lich": c_lich, "lui": c_lui,
    "ban-do": c_ban_do, "profile": c_profile,
}


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "help", "?"):
        print(__doc__)
        return 0
    ten, *con = argv
    if ten not in LENH:
        gan = [k for k in LENH if k.startswith(ten[:2])]
        print(f"khong co lenh '{ten}'." + (f" Y ban la: {', '.join(gan)}?" if gan else ""))
        print("\nGo `b` de xem menu.")
        return 2
    return LENH[ten](con) or 0


if __name__ == "__main__":
    os.chdir(LAB)
    raise SystemExit(main(sys.argv[1:]))
