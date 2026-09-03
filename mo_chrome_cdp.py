# -*- coding: utf-8 -*-
r"""mo_chrome_cdp.py - Mo Chrome da dang nhap (.browser_darwinex) kem CDP 9224.

Theo INVENTORY_THE_BRAIN.md: "BROWSER DUNG: .browser_darwinex (darwin) - KHONG mo
thebrain2/9222."  Cong 9224 la diet doc_cdp/doc_trinh_duyet/SEEKER vao duoc cac
nguon can dang nhap (Reddit, MQL5 Signals, Myfxbook, track-record, X/FB/TikTok).

Chay:  python mo_chrome_cdp.py [port] [profile_dir] [--hien]
  python mo_chrome_cdp.py                : darwin @ 9224, CHAY AN
  python mo_chrome_cdp.py --hien         : hien cua so (de xem may dang lam gi)

CHAY AN LA MAC DINH tu 30/08/2026. Ho so `.browser_darwinex` giu nguyen phien
dang nhap that, nen chay an KHONG mat quyen vao cac trang can dang nhap - no chi
bo phan ve len man hinh.

Do that hom do voi 19 tien trinh Chrome: **2,93 GB**. Phan lon la GPU + do hoa
+ nen trang, deu vo ich khi khong ai nhin. Muon nhin lai thi `--hien`.
"""
import subprocess, time, sys, pathlib
import urllib.request

LAB = pathlib.Path(__file__).parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

#: Ten mien -> IP THAT, cho nhung ten bi DNS dau doc tren mang nay.
#: Lay bang: curl -H "accept: application/dns-json" \n#:   "https://cloudflare-dns.com/dns-query?name=<ten>&type=A"
#: Kiem lai dinh ky - MQL5 dung nhieu IP va chung co doi.
MAP_TEN = {
    "www.mql5.com": "203.29.60.247",
    "mql5.com": "203.29.60.247",
}
PROF = str(LAB / ".browser_darwinex")      # profile DA DANG NHAP
PORT = "9224"

#: User-agent cua Chrome co man hinh tren chinh may nay. Phai cap nhat khi
#: Chrome len doi lon - UA lech qua xa ban that cung la mot dau vet.
UA_THAT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

def cdp_song(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%s/json/version" % port, timeout=4) as r:
            return r.status == 200
    except Exception:
        return False

def main():
    # Bo CO (`--hien`...) ra khoi doi so vi tri. Truoc 30/08 khong loc, nen
    # `mo_chrome_cdp.py --hien` chay thanh `--remote-debugging-port=--hien`:
    # Chrome mo len nhung khong co CDP nao, va thong bao la "KHONG thay CDP sau
    # 40s (profile bi Chrome khac giu khoa)" - mot chan doan HOAN TOAN SAI.
    vi_tri = [a for a in sys.argv[1:] if not a.startswith("-")]
    port = vi_tri[0] if len(vi_tri) > 0 else PORT
    prof = vi_tri[1] if len(vi_tri) > 1 else PROF
    if cdp_song(port):
        print("CDP %s DA MO san roi - khong lam gi" % port)
        return
    an = "--hien" not in sys.argv
    args = [CHROME, "--remote-debugging-port=" + port,
            "--user-data-dir=" + prof,
            "--no-first-run", "--no-default-browser-check"]
    # --- VUOT DNS BI DAU DOC ---------------------------------------------
    # Do that 03/09/2026: `nslookup www.mql5.com` tren may nay tra ve DUY NHAT
    # mot dia chi IPv6 `2401:fce0:31:1::247` (dai cua ISP Viet Nam), va moi
    # ket noi deu rot: `requests` -> RemoteDisconnected, Chrome -> ERR_HTTP2_
    # PROTOCOL_ERROR, curl -> HTTP 000 o ca http1.0/1.1/2. DNS bi dau doc.
    # IP THAT lay qua DNS-over-HTTPS (Cloudflare 1.1.1.1): noi thang vao do
    # thi may chu tra 403 - tuc DEN DUOC, chi con bi chan vi trong nhu bot.
    # Nen phai la CHROME THAT di vao (dau van TLS that, JS that, cookie that),
    # chi ep rieng phan phan giai ten.
    if MAP_TEN:
        args.append("--host-resolver-rules=" +
                    ",".join(f"MAP {t} {ip}" for t, ip in MAP_TEN.items()))
    if an:
        # `--headless=new` la ban headless DUNG CHUNG engine voi Chrome thuong
        # (khac ban cu, von la mot trinh duyet khac han va bi nhieu trang chan).
        # Ho so van la ho so cu -> cookie va phien dang nhap giu nguyen.
        args += ["--headless=new", "--disable-gpu",
                 # Bo nhung thu chi phuc vu man hinh:
                 "--disable-software-rasterizer",
                 "--mute-audio", "--disable-background-timer-throttling",
                 "--disable-renderer-backgrounding",
                 "--window-size=1440,2400",
                 # --- che dau vet tu dong hoa ---
                 # Chrome headless tu khai `HeadlessChrome/152.0.0.0` NGAY TRONG
                 # user-agent. Reddit doc dung chuoi do va tra ve
                 # "You've been blocked by network security" - do that 30/08.
                 # Dat lai UA cho giong ban co man hinh.
                 "--user-agent=" + UA_THAT,
                 "--disable-blink-features=AutomationControlled"]
    args.append("about:blank")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    p = subprocess.Popen(args, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Da phong Chrome %s pid=%s profile=%s, cho CDP %s bat..."
          % ("AN" if an else "HIEN", p.pid, prof, port))
    for _ in range(20):
        time.sleep(2)
        if cdp_song(port):
            print("CDP %s OPEN - doc_cdp/doc_trinh_duyet ket noi duoc" % port)
            return
    print("KHONG thay CDP sau 40s (co the profile dang bi Chrome khac giu khoa -> dong no roi chay lai)")

if __name__ == "__main__":
    main()
