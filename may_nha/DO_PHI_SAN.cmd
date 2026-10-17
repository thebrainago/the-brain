@echo off
rem DO PHI THAT tren tai khoan cua chu du an (17/10/2026). Moi san mot terminal DANG DANG NHAP.
rem   DO_PHI_SAN.cmd "D:\mt5_tester\exness_cent\terminal64.exe"
rem   DO_PHI_SAN.cmd "D:\mt5_tester\xm_micro\terminal64.exe"
rem Ra: reports\phi_san\<server>\ (tai_khoan.json, ma.csv, spread_gio.csv, ma_san.json, lich_su_tom_tat.csv, lenh_cua_anh.csv)
rem Sau do (MT5 tester, cung terminal):  python mt5tools\chay_lai_tren_san.py chay --slot <thu muc terminal> --ma-san reports\phi_san\<server>\ma_san.json --tien USC
chcp 65001 >nul
cd /d "%~dp0.."
set PY=C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python
if "%~1"=="" (
  echo Thieu duong dan terminal64.exe. Vi du: DO_PHI_SAN.cmd "D:\mt5_tester\exness_cent\terminal64.exe"
  exit /b 1
)
"%PY%" mt5tools\do_phi_san.py "%~1" --ngay-tick 14 --tp-gia 5 --ngay-lich-su 365
