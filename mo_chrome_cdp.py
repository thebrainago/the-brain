# -*- coding: utf-8 -*-
r"""mo_chrome_cdp.py - Mo Chrome da dang nhap (.browser_darwinex) kem CDP 9224.

Theo INVENTORY_THE_BRAIN.md: "BROWSER DUNG: .browser_darwinex (darwin) - KHONG mo
thebrain2/9222."  Cong 9224 la diet doc_cdp/doc_trinh_duyet/SEEKER vao duoc cac
nguon can dang nhap (Reddit, MQL5 Signals, Myfxbook, track-record, X/FB/TikTok).

Chay:  python mo_chrome_cdp.py [port] [profile_dir]
  python mo_chrome_cdp.py                : darwin @ 9224
  python mo_chrome_cdp.py 9224 .browser_darwinex
"""
import subprocess, time, sys, pathlib
import urllib.request

LAB = pathlib.Path(__file__).parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROF = str(LAB / ".browser_darwinex")      # profile DA DANG NHAP
PORT = "9224"

def cdp_song(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%s/json/version" % port, timeout=4) as r:
            return r.status == 200
    except Exception:
        return False

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else PORT
    prof = sys.argv[2] if len(sys.argv) > 2 else PROF
    if cdp_song(port):
        print("CDP %s DA MO san roi - khong lam gi" % port)
        return
    args = [CHROME, "--remote-debugging-port=" + port,
            "--user-data-dir=" + prof,
            "--no-first-run", "--no-default-browser-check", "about:blank"]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    p = subprocess.Popen(args, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Da phong Chrome pid=%s profile=%s, cho CDP %s bat..." % (p.pid, prof, port))
    for _ in range(20):
        time.sleep(2)
        if cdp_song(port):
            print("CDP %s OPEN - doc_cdp/doc_trinh_duyet ket noi duoc" % port)
            return
    print("KHONG thay CDP sau 40s (co the profile dang bi Chrome khac giu khoa -> dong no roi chay lai)")

if __name__ == "__main__":
    main()
