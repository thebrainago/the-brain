@echo off
rem ============================================================
rem  THE BRAIN - CAI MAY NHA TU NHAN DON (chay MOT LAN, chu du an mo bang tay)
rem  Tao hai tac vu Windows (tai khoan hien tai, khong can quyen admin):
rem    TheBrainCauChay      moi 5 phut: `b cau chay` (keo don -> chay -> day ket qua). Khoa trong code (`DANG_BAN`)
rem                         nen luot sau thoat ngay neu luot truoc dang chay - khong chay trung.
rem    TheBrainCauChayBoot  luc dang nhap Windows: chay ngay (sau khi may khoi dong lai khong phai go tay).
rem  Dang choi LoL (League of Legends.exe / LeagueClient.exe): ha uu tien, gioi han nhan, bo don TESTER + don tuong tac
rem  (qwen/che_do_choi.py; them game khac o config\che_do_choi.json).
rem  Go bo:  schtasks /Delete /TN TheBrainCauChay /F  &  schtasks /Delete /TN TheBrainCauChayBoot /F
rem  Dung khan: tao tep CAU_DUNG o thu muc lab (hoac b cau dung tu cloud).
rem ============================================================
cd /d "%~dp0"
set RUN=%~dp0b.cmd cau chay
schtasks /Create /F /SC MINUTE /MO 5 /TN "TheBrainCauChay" /TR "cmd /c \"%RUN% >> %~dp0reports\cau_chay_nen.log 2>&1\""
schtasks /Create /F /SC ONLOGON /TN "TheBrainCauChayBoot" /TR "cmd /c \"%RUN% >> %~dp0reports\cau_chay_nen.log 2>&1\""
echo.
schtasks /Query /TN "TheBrainCauChay" | findstr /i "TheBrain"
schtasks /Query /TN "TheBrainCauChayBoot" | findstr /i "TheBrain"
pause
