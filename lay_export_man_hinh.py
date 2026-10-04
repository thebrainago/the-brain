# -*- coding: utf-8 -*-
r"""lay_export_man_hinh.py - lay export lich su lenh MQL5 bang THAO TAC MAN HINH tren Chrome THAT (Profile 3, da dang nhap).
Khong CDP, khong ban sao ho so (Chrome 154 gan cookie voi thu muc goc -> ban sao luon mat dang nhap).
Chay:  python lay_export_man_hinh.py ID [ID ...]      (>= 5,5 giay giua hai lan; dung khi gap HTML/403)
Chrome Profile 3 phai dang mo va dang o cua so truoc; tep CSV vao du_lieu_cao/mql5/ (gitignore, KHONG vao git)."""
import sys, time, shutil, pathlib, subprocess
import pyautogui, pyperclip
DL = pathlib.Path.home() / "Downloads"
OUT = pathlib.Path(__file__).parent / "du_lieu_cao" / "mql5"
CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

def chrome_truoc():
    subprocess.Popen([CHROME, '--profile-directory=Profile 3', 'about:blank'])   # dua cua so Profile 3 len truoc
    time.sleep(2.5)

def lay(sid):
    dich = OUT / f"mql5_{sid}_positions.csv"
    if dich.exists(): return "co_san"
    tep = DL / f"{sid}.positions.csv"
    if tep.exists(): tep.unlink()
    pyperclip.copy(f"https://www.mql5.com/en/signals/{sid}/export/positions")
    pyautogui.hotkey('ctrl', 'l'); time.sleep(0.4)
    pyautogui.hotkey('ctrl', 'v'); time.sleep(0.4)
    pyautogui.press('enter')
    for _ in range(40):
        time.sleep(1)
        if tep.exists() and not (DL / (tep.name + ".crdownload")).exists(): break
    else:
        return "khong_co_tep"
    time.sleep(0.5)
    dau = tep.read_bytes()[:40].decode("utf-8-sig", "ignore")
    if not dau.startswith("Time;Type"):
        tep.unlink(); return "khong_phai_csv"
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.move(str(tep), str(dich))
    return "ok"

if __name__ == "__main__":
    chrome_truoc()
    for i, sid in enumerate(sys.argv[1:]):
        if i: time.sleep(5.5)
        kq = lay(sid); print(sid, kq, flush=True)
        if kq not in ("ok", "co_san"): print("DUNG"); break
