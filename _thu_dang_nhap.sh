#!/bin/bash
T="/c/Users/SV STORE/AppData/Roaming/MetaQuotes/Terminal/656C351524AFFE300FAFE576FA4C7845"
taskkill //F //IM terminal64.exe >/dev/null 2>&1
sleep 5
rm -f "$T/logs/"*.log 2>/dev/null
"/c/Program Files/XM MT5/terminal64.exe" "/login:342418441" "/password:Vietanh1234\$" "/server:$1" &
sleep 75
echo "=== SERVER THU: $1 ==="
iconv -f UTF-16LE -t UTF-8 "$T/logs/"*.log 2>/dev/null | grep -iE "authoriz|invalid|network|login|account|connect" | head -8
taskkill //F //IM terminal64.exe >/dev/null 2>&1
