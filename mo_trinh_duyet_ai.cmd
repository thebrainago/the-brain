@echo off
rem Trinh duyet RIENG cua AI (dang nhap thebrainago@gmail.com, MQL5, ...), CDP cong 9224, ho so .browser_thebrain (gitignore). KHONG dung ho so Chrome goc: Chrome 154 gan phien voi thu muc goc.
start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9224 --user-data-dir="%~dp0.browser_thebrain" --profile-directory=Default --no-first-run --start-maximized
