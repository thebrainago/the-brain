#!/bin/bash
T="/c/Users/SV STORE/AppData/Roaming/MetaQuotes/Terminal/656C351524AFFE300FAFE576FA4C7845"
taskkill //F //IM terminal64.exe >/dev/null 2>&1; sleep 4
rm -f "$T/logs/"*.log 2>/dev/null
python - "$1" <<'PY'
import sys,io
sv=sys.argv[1]
p=r"C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal\656C351524AFFE300FAFE576FA4C7845\chi_dang_nhap.ini"
io.open(p,"w",encoding="utf-16").write(
  "[Common]\nLogin=342418441\nPassword=Vietanh1234$\nServer=%s\nEnableNews=false\n"%sv)
PY
"/c/Program Files/XM MT5/terminal64.exe" "/config:C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal\656C351524AFFE300FAFE576FA4C7845\chi_dang_nhap.ini" &
for i in $(seq 1 24); do
  sleep 5
  if iconv -f UTF-16LE -t UTF-8 "$T/logs/"*.log 2>/dev/null | grep -qiE "authorized on|previous successful"; then break; fi
done
echo "### $1 (sau $((i*5))s)"
iconv -f UTF-16LE -t UTF-8 "$T/logs/"*.log 2>/dev/null | grep -iE "network|authoriz|invalid|account|connect" | head -6
echo "--- history ---"; ls "$T/bases/XM.COM-MT5/history" 2>/dev/null | head -3
