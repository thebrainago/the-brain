import subprocess, os
env = os.environ
cr = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(cr):
    cr = os.path.join(os.environ.get("LOCALAPPDATA",""), "Google","Chrome","Application","chrome.exe")
prof = r"C:\Users\SV STORE\Downloads\Research SP500\lab\.browser_thebrain2"
p = subprocess.Popen([cr, "--remote-debugging-port=9223", "--user-data-dir=" + prof,
                      "--profile-directory=Default", "https://web.telegram.org"],
                     creationflags=subprocess.CREATE_NO_WINDOW)
print("pid=", p.pid, "chrome=", cr)
