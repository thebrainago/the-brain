import subprocess, os
cr = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(cr):
    cr = os.path.join(os.environ.get("LOCALAPPDATA",""), "Google","Chrome","Application","chrome.exe")
prof = r"C:\Users\SV STORE\Downloads\Research SP500\lab\.browser_darwinex"
p = subprocess.Popen([cr, "--remote-debugging-port=9224", "--user-data-dir=" + prof,
                      "--no-first-run", "https://web.telegram.org"],
                     creationflags=subprocess.CREATE_NO_WINDOW)
print("pid=", p.pid, "profile=darwinex port=9224")
