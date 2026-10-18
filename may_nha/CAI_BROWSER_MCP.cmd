@echo off
rem CAI BROWSER MCP (browsermcp.io) cho agent tren may nha - 18/10/2026. Xem tai_lieu/BROWSER_MCP.md
rem Agent (Claude Code / Grok) dieu khien Chrome THAT qua giao thuc MCP: dung phien dang nhap + cookie co san,
rem van tay trinh duyet that -> doc duoc trang sau Cloudflare ma headless bi chan.
rem Cai vao TRINH DUYET RIENG CUA AI (.browser_thebrain, CDP 9224) - KHONG cai vao Chrome ca nhan cua anh.
setlocal
set "CHROME=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe"

where node >nul 2>nul || (echo [LOI] Chua co Node.js 18+. Cai tu https://nodejs.org roi chay lai. & pause & exit /b 1)
where claude >nul 2>nul || (echo [LOI] Chua co lenh "claude" ^(Claude Code^). Bo qua buoc dang ky, xem tai_lieu/BROWSER_MCP.md muc 3. & goto MO_CHROME)

echo [1/2] Dang ky may chu MCP "browsermcp" cho Claude Code (pham vi user, ghim ban 0.1.3)...
claude mcp remove browsermcp --scope user >nul 2>nul
claude mcp add browsermcp --scope user -- cmd /c npx -y @browsermcp/mcp@0.1.3
claude mcp list

:MO_CHROME
echo.
echo [2/2] Mo trinh duyet RIENG cua AI tai trang tien ich Browser MCP.
echo       Bam "Add to Chrome" MOT LAN. Sau do moi khi agent can: bam bieu tuong Browser MCP tren tab can dung ^> "Connect".
start "" "%CHROME%" --remote-debugging-port=9224 --user-data-dir="%~dp0.browser_thebrain" --profile-directory=Default --no-first-run "https://chromewebstore.google.com/detail/browser-mcp-automate-your/bjfgambnhccakkhmkepdoekmckoijdlc"
echo.
echo Xong. Kiem tra: mo Claude Code trong thu muc repo, go /mcp - phai thay "browsermcp" connected.
pause
