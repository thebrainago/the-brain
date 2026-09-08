# -*- coding: utf-8 -*-
"""b — MOT cua vao cho moi viec hang ngay cua THE BRAIN.

Vi sao co file nay: lab co ~94 file .py o muc goc, ds/ co them 40 thu muc.
Nho ten file la viec cua may, khong phai cua nguoi. Go `b` de xem menu.

    b                 menu
    b vao             VAO PHIEN: trang thai song + ban giao hom qua
    b ket "tom tat"   KET PHIEN: chot git + sinh TIEP_TUC_MAI.md cho mai
    b bg ["dong"]     ghi BAN GIAO SONG (khong doi cuoi phien moi ban giao)
    b bg-xem          xem ban giao song hien tai
    b xa              bat DIEU KHIEN XA qua Telegram (tat may / dung he tu xa)
    b xa-thu          kiem cau hinh Telegram + gui mot tin thu
    b test [tu-khoa]  chay test SONG SONG (8 tien trinh, ~1 phut thay vi 6)
    b test1 [tu-khoa] chay test MOT tien trinh (khi nghi song song lam sai)
    b toan-canh       MOT man hinh: dau vao + kho co che + tang kham pha
    b trang-thai      bang dieu khien (van hanh cua dieu phoi)
    b chay / b dung   bat / dung dieu phoi 24/7
    b canary          tu kiem engine (5 canary)
    b phan-loai       389 file ma -> 4 lan + BANG SUAT BOC tung lan
    b chi-bao [N]     boc co che tu file CHI BAO (N = test me; --that = chay het)
    b loc [--khung K] loc TINH truoc pheu: suy bien / trung hanh vi / spec hong
    b quet            quet_be_mat.py  (da tu goi `b loc` truoc khi quet)
    b mde             chay_bang_mde.py
    b cham-lai        cham lai MOI gia thuyet duoi the he cong hien tai
    b on-dinh         edge la CAO NGUYEN hay CAI GAI (do vung lan can)
    b hinh-dang       hinh dang do co khac NGAU NHIEN khong (so voi chuoi null)
    b mde-nap [khung] nap TRUOC bang MDE cho ca be mat (D1: ~4 phut, mot lan)
    b thanh-phan      kho THANH PHAN thu hoi tu he bi loai + toan hang con thieu
    b san             EVO di san cong cu/du an ngoai de tich hop
    b san-xem         xem kho cong cu da tim duoc
    b san-quet        nhat lai cong cu tu TOAN BO ban doc da co (khong tai gi moi)
    b trinh-duyet     mo Chrome bot + CDP 9224 (de doc nguon can dang nhap)
    b tai-khoan       nen tang nao da dang nhap, thieu cai gi
    b tai-khoan --mo <ten>   mo san trang tao tai khoan
    b ds [args]       chay pytest ben ds/ (kho DeepSeek)
    b tim <tu>        tim trong MA NGUON (bo qua data/reports/backups)
    b luu "msg"       chot nhanh vao git (thay cho copy vao backups/)
    b lich [n]        n commit gan nhat
    b lui <file>      tra mot file ve ban da chot
    b qwen [lenh]     HE TU CHAY: qwen lam tiep bang viec (xem qwen/DOC_TRUOC.md)
                      `b qwen` = `q`. `b qwen trang-thai` xem bang. `b qwen kiem`.
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


def c_phan_loai(a):
    """b phan-loai - chia kho ma thanh 4 lan + bang suat boc tung lan."""
    return chay([PY, LAB / "nhan" / "phan_loai_ma.py",
                 *(a or ["--suat"])], cwd=LAB)


def c_chi_bao(a):
    """b chi-bao [N|--that] - boc co che tu 190 file CHI BAO."""
    return chay([PY, LAB / "nhan" / "doc_chi_bao.py", *a], cwd=LAB)


def c_loc(a):
    """b loc [--khung K] - bo loc TINH chay truoc pheu V0-V3."""
    return chay([PY, LAB / "nhan" / "loc_co_che.py", *a], cwd=LAB)


def c_mde(a):
    return chay([PY, LAB / "chay_bang_mde.py", *a])


def c_cham_lai(a):
    return chay([PY, LAB / "cham_lai_the_he.py", *a])


def c_on_dinh(a):
    return chay([PY, LAB / "do_on_dinh.py", *a])


def c_bg(a):
    return chay([PY, LAB / "ban_giao_song.py", *a])


def c_bg_xem(a):
    return chay([PY, LAB / "ban_giao_song.py", "--xem"])


def c_xa(a):
    return chay([PY, LAB / "dieu_khien_xa.py", *a])


def c_xa_thu(a):
    return chay([PY, LAB / "dieu_khien_xa.py", "--thu"])


def c_hinh_dang(a):
    return chay([PY, LAB / "hinh_dang_vs_null.py", *a])


def c_mde_nap(a):
    return chay([PY, LAB / "nap_truoc_mde.py", *a])


def c_thanh_phan(a):
    ma = [
        "import sys; sys.path.insert(0, r'%s')" % LAB,
        "from nhan import thu_hoi_thanh_phan as TH, so as SO",
        "print('KHO THANH PHAN: %d dong (%d viet ra duoc bang ngu phap)' % ("
        "SO.mot('SELECT COUNT(*) n FROM thanh_phan')['n'],"
        "SO.mot('SELECT COUNT(*) n FROM thanh_phan WHERE dien_dat_duoc=1')['n']))",
        "print()",
        "print('-- DUNG DUOC NGAY (top 20 theo so lan) --')",
        "[print('  %-14s %-14s cot=%-7s x%s' % (r['chi_bao'], r['tham_so'],"
        " r['cot'] or '-', r['so_lan'])) for r in TH.kho(True, 20)]",
        "print()",
        "print('-- TOAN HANG CON THIEU (do tu ma THAT, xep theo so lan dung) --')",
        "[print('  %-16s %5d lan · %2d bien the · %s' % (r['chi_bao'],"
        " r['tong_lan'], r['so_bien_the'], r['con_thieu']))"
        " for r in TH.toan_hang_con_thieu(20)]",
    ]
    return chay([PY, "-c", chr(10).join(ma)])


def c_san(a):
    return chay([PY, LAB / "nhan" / "san_cong_cu.py", *a])


def c_san_quet(_):
    return chay([PY, "-c",
                 "import sys;sys.path.insert(0,'.');"
                 "from nhan import san_cong_cu as S;S.quet_lai_thu_vien()"])


def c_san_xem(_):
    return chay([PY, LAB / "nhan" / "san_cong_cu.py", "--xem"])


def c_tai_khoan(a):
    return chay([PY, LAB / "nhan" / "tai_khoan_nen_tang.py", *a])


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



# ---- DAY CHUYEN 03/09/2026: san -> doc -> boc -----------------------------
def _nhan(a, i, mac_dinh):
    return a[i] if len(a) > i else mac_dinh


def c_day_chuyen(a):
    """b day-chuyen [MA] - ca day chuyen mot lenh."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import day_chuyen as D;"
                 f"D.mot_luot({_nhan(a, 0, 'US500CASH')!r})"], cwd=LAB)


def c_san(a):
    """b san-nguon [MA] - LUONG 1: san theo tai san + ten he thong + MQL5."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import day_chuyen as D;"
                 f"D.san({_nhan(a, 0, 'US500CASH')!r})"], cwd=LAB)


def c_boc(a):
    """b boc [SO_DOC] [SO_BOC] - LUONG 2: doc song song + boc co che."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import day_chuyen as D;"
                 f"D.boc({int(_nhan(a, 0, 500))}, {int(_nhan(a, 1, 200))})"], cwd=LAB)


def c_noi_sinh(a):
    """b noi-sinh [MA] [KHUNG] - LUONG 3: sinh co che tu chinh lich su."""
    return chay([PY, LAB / "_noi_sinh_chay.py", "--ma", _nhan(a, 0, "US500CASH"),
                 "--khung", _nhan(a, 1, "H4")], cwd=LAB)


def c_pheu(a):
    """b pheu - do tung chang cua pheu nguon."""
    return chay([PY, LAB / "_pheu_nguon.py"], cwd=LAB)


def c_mang(a):
    """b mang - kiem duong ra cho cac nguon, bat WARP neu can."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import day_chuyen as D;"
                 "m=D.kiem_mang();"
                 "_=D.bat_warp() if m.get('mql5')!='OK' else None"], cwd=LAB)


def c_chi_tieu(a):
    """b chi-tieu [NGAY] - hom nay dat chi tieu nao, thieu cai nao."""
    n = repr(a[0]) if a else "None"
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import chi_tieu as CT;"
                 f"CT.in_bao_cao({n})"], cwd=LAB)


def c_kham_pha(a):
    """b kham-pha - chay het cac kenh TU TIM nguon moi (blog + telegram)."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import kham_pha_nguon as KP; KP.mot_luot()"], cwd=LAB)


def c_nguon_cho(a):
    """b nguon-cho - liet ke nguon ung vien dang cho nguoi gat."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import kham_pha_nguon as KP;"
                 "[print(f\"{str(d.get('nguoi')):>8}  {d['khoa'][:36]:36s} "
                 "{str(d.get('ten'))[:44]}\") for d in KP.dang_cho_duyet()]"],
                cwd=LAB)


def c_finder(a):
    """b finder [--khong-san] - san cong cu ngoai + phan loai the de xuat."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from tru import finder as F;"
                 f"F.mot_luot(san={'--khong-san' not in a})"], cwd=LAB)


def c_tinix(a):
    """b tinix - nap chi muc du an tu repo.tinix.ai vao kho cong cu."""
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import nguon_tinix as T; T.nap_vao_kho()"], cwd=LAB)


def c_tele(a):
    """b tele [KENH] - quet kenh Telegram (web, hoac MTProto neu co khoa)."""
    if a:
        return chay([PY, "-c",
                     "import sys; sys.path.insert(0,'.');"
                     "from nhan import telegram as TG;"
                     f"print(TG.quet_tat_ca(kenh=({a[0]!r},)))"], cwd=LAB)
    return chay([PY, "-c",
                 "import sys; sys.path.insert(0,'.');"
                 "from nhan import telegram as TG; print(TG.quet_tat_ca())"], cwd=LAB)


def c_qwen(a):
    """b qwen [...] - he tu chay bang qwen. Cua vao ngan hon la `q` o cung thu muc.

    Vi sao co ca hai: `q` la lenh chu du an go hang ngay; `b qwen` de nguoi doc
    menu `b` biet la he do TON TAI.
    """
    return chay([PY, "-X", "utf8", "-m", "qwen.chay", *a], cwd=LAB)


LENH = {
    "vao": c_vao, "ket": c_ket,
    "qwen": c_qwen, "q": c_qwen,
    "test": lambda a: c_test(a, True), "test1": lambda a: c_test(a, False),
    "toan-canh": c_toan_canh, "tc": c_toan_canh,
    "trang-thai": c_trang_thai, "tt": c_trang_thai,
    "chay": c_chay, "dung": c_dung, "canary": c_canary,
    "quet": c_quet, "mde": c_mde, "mde-nap": c_mde_nap,
    # --- 05/09/2026: khau boc tach + bo loc truoc pheu ---
    "phan-loai": c_phan_loai, "chi-bao": c_chi_bao, "loc": c_loc,
    "cham-lai": c_cham_lai, "on-dinh": c_on_dinh,
    "hinh-dang": c_hinh_dang,
    "bg": c_bg, "bg-xem": c_bg_xem, "xa": c_xa, "xa-thu": c_xa_thu,
    "thanh-phan": c_thanh_phan, "san": c_san, "san-xem": c_san_xem, "san-quet": c_san_quet,
    "tai-khoan": c_tai_khoan, "trinh-duyet": c_trinh_duyet,
    "ds": c_ds, "tim": c_tim,
    "luu": c_luu, "lich": c_lich, "lui": c_lui,
    "ban-do": c_ban_do, "profile": c_profile,
    # --- day chuyen 03/09/2026 ---
    "day-chuyen": c_day_chuyen, "dc": c_day_chuyen,
    "san-nguon": c_san, "boc": c_boc,
    "noi-sinh": c_noi_sinh, "pheu": c_pheu, "mang": c_mang,
    # --- 04/09/2026 ---
    "finder": c_finder, "tinix": c_tinix, "tele": c_tele,
    "kham-pha": c_kham_pha, "nguon-cho": c_nguon_cho,
    "chi-tieu": c_chi_tieu, "ct": c_chi_tieu,
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
