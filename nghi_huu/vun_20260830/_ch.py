import subprocess, os, time
env = os.environ
cr = os.path.join(os.environ.get("LOCALAPPDATA",""), "Google", "Chrome", "Application", "chrome.exe")
prof = r"C:\Users\SV STORE\Downloads\Research SP500\lab\.browser_thebrain"
if not os.path.exists(cr):
    alt = [os.path.join(os.environ.get("ProgramFiles",""),"Google","Chrome","Application","chrome.exe"),
           os.path.join(os.environ.get("ProgramFiles(x86)",""),"Google","Chrome","Application","chrome.exe")]
    for a in alt:
        if os.path.exists(a): cr = a; break
print("chrome=", cr, "exits=", os.path.exists(cr))
p = subprocess.Popen([cr, "--remote-debugging-port=9222", "--user-data-dir=" + prof, "https://web.telegram.org"],
                     creationflags=subprocess.CREATE_NO_WINDOW)
print("pid=", p.pid)
time.sleep(4)
