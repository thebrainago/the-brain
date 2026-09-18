# -*- coding: utf-8 -*-
"""Kiem tra file nguon_config.json - bao cao khoa nao san sang, khoa nao con thieu.
Chay: python kiem_tra_ma_khoa.py"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
CONFIG = HERE / "nguon_config.json"


def danh_dau(ok, noi_dung):
    ky = "[OK]  " if ok else "[THIEU]"
    print(f"  {ky} {noi_dung}")


def main():
    if not CONFIG.exists():
        print("KHONG THAY nguon_config.json - chay python brain_nguon_moi.py --imap de tao mau.")
        sys.exit(1)

    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    print("=== KIEM TRA MA KHOA ===")
    print(f"File: {CONFIG}\n")

    # 1. IMAP Gmail
    imap = c.get("imap", {})
    email = (imap.get("email") or "").strip()
    mk = (imap.get("mat_khau_ung_dung") or "").strip()
    print("1) GMAIL (IMAP)")
    ok_email = bool(re.match(r"^[^@\s]+@gmail\.com$", email)) and "example.com" not in email
    danh_dau(ok_email, f"email: {email or '(trong)'}")
    mk_chuan = bool(re.fullmatch(r"[a-z]{4} [a-z]{4} [a-z]{4} [a-z]{4}", mk)) or bool(re.fullmatch(r"[a-zA-Z0-9]{16}", mk.replace(" ", "")))
    danh_dau(bool(mk) and mk_chuan, "mat_khau_ung_dung: " + ("(da dien, dung dang)" if mk and mk_chuan else ("(da dien, SAi dang - phai la 16 ky tu kieu xxxx xxxx xxxx xxxx)" if mk else "(trong)")))

    # 2. YouTube
    yt = (c.get("youtube", {}).get("api_key") or "").strip()
    print("2) YOUTUBE API KEY")
    if not yt:
        danh_dau(False, "api_key: (trong - tu chon, co the bo qua)")
    elif yt.startswith("AIza"):
        danh_dau(True, "api_key: (da dien, dung dang)")
    else:
        danh_dau(False, "api_key: (dien nhung khong bat dau bang AIza - kiem tra lai)")

    # 3. Myfxbook
    mf = c.get("myfxbook", {})
    mf_email = (mf.get("email") or "").strip()
    print("3) MYFXBOOK")
    if not mf_email:
        danh_dau(False, "email: (trong - tu chon, track record cong khai khong can)")
    else:
        danh_dau(True, "email: (da dien)")

    # 4. Thu ket noi IMAP (chi khi co day du)
    print("4) THU KET NOI IMAP")
    if ok_email and mk:
        try:
            import imaplib
            M = imaplib.IMAP4_SSL(imap.get("may_chu", "imap.gmail.com"), int(imap.get("cong", 993)), timeout=20)
            M.login(email, mk.replace(" ", ""))
            M.logout()
            danh_dau(True, f"Dang nhap IMAP thanh cong: {email}")
        except Exception as e:
            danh_dau(False, f"Khong dang nhap duoc: {str(e)[:120]}")
    else:
        danh_dau(False, "(bo qua - chua dien email/mat khau)")

    print("\n=== KET LUAN ===")
    if ok_email and mk:
        print("  San sang chay: python brain_nguon_moi.py --imap")
    else:
        print("  Lam buoc 1 trong TAI_KHOAN_VA_MA_KHOA.txt roi chay lai.")


if __name__ == "__main__":
    main()
