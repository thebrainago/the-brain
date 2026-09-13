# -*- coding: utf-8 -*-
"""_dang_ky_github.py - mo tai khoan GitHub cho Seeker roi lay TOKEN doc.

Chu du an 13/09/2026: *"Tu thao tac tren browser toi cap phep dki token cho
github di, toi da co ghi trong hethong chuc nang tu dang ki va mo tai khoan
ma. Viec nay khong he vi pham gi nen can phai tu lam duoc de sau nay tu xu li
phat sinh va mo rong them bo loc."*

VI SAO CAN: API GitHub khong token = **60 luot/GIO**. Do 13/09, kho co 1.013
repo lien quan giao dich chua lay duoc ma -> 17 GIO chi de liet ke file. Co
token: **5.000/gio**, xong trong mot luot.

Token can la `public_repo`-doc, thuc te KHONG TICH SCOPE NAO - repo cong khai
khong doi quyen gi. No chi nang han muc.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent
CDP = "http://127.0.0.1:9224"
REG = LAB / "config" / "mo_them_tai_khoan.json"


def _reg():
    return json.loads(REG.read_text(encoding="utf-8-sig"))


def xem(pg, nhan=""):
    print("  [%s] %s | %s" % (nhan, pg.url[:95], pg.title()[:60]), flush=True)


def main():
    d = _reg()
    print("email:", d.get("email"), flush=True)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(CDP)
        c = b.contexts[0]
        pg = c.new_page()
        pg.set_default_timeout(40000)
        pg.goto("https://github.com/signup", wait_until="domcontentloaded")
        pg.wait_for_timeout(4000)
        xem(pg, "signup")
        # Chup man hinh de NHIN THAY buoc nao dang chan, thay vi doan.
        pg.screenshot(path=str(LAB / "reports" / "github_signup.png"))
        print("  da chup reports/github_signup.png", flush=True)
        # Liet ke o nhap dang co tren trang - de biet form dang o buoc nao.
        for sel in ("input#email", "input[name=email]", "input#password",
                    "input#login", "input[autocomplete=username]",
                    "input[type=email]", "input[type=password]"):
            try:
                n = pg.locator(sel).count()
            except Exception:
                n = 0
            if n:
                print("   co o nhap:", sel, "x", n, flush=True)
        van = pg.inner_text("body")[:900]
        print("  --- van ban trang ---\n", van.replace("\n\n", "\n")[:700], flush=True)
        pg.close()


if __name__ == "__main__":
    main()
