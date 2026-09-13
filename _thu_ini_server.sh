#!/bin/bash
T="/c/Users/SV STORE/AppData/Roaming/MetaQuotes/Terminal/656C351524AFFE300FAFE576FA4C7845"
for SV in "XMGlobal-MT5 17" "XMGlobal-MT5 10" "XMGlobal-MT5"; do
  taskkill //F //IM terminal64.exe >/dev/null 2>&1; sleep 4
  rm -f "$T/logs/"*.log "$T/thu.xml" 2>/dev/null
  python - "$SV" <<'PY'
import sys,io
sv=sys.argv[1]
p=r"C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal\656C351524AFFE300FAFE576FA4C7845\thu.ini"
txt="[Common]\nLogin=342418441\nPassword=Vietanh1234$\nServer=%s\n\n[Tester]\nExpert=QuanTriBench.ex5\nSymbol=US500Cash\nPeriod=H1\nModel=2\nOptimization=0\nFromDate=2024.01.01\nToDate=2024.03.01\nDeposit=10000\nCurrency=USD\nLeverage=1:500\nReport=thu\nReplaceReport=1\nShutdownTerminal=1\n"%sv
io.open(p,"w",encoding="utf-16").write(txt)
PY
  "/c/Program Files/XM MT5/terminal64.exe" "/config:C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal\656C351524AFFE300FAFE576FA4C7845\thu.ini" &
  sleep 70
  echo "### $SV"
  iconv -f UTF-16LE -t UTF-8 "$T/logs/"*.log 2>/dev/null | grep -iE "network|authoriz|invalid|tester" | head -4
  ls "$T/thu.xml" "$T/thu.htm" 2>/dev/null && echo "  -> CO BANG KET QUA"
done
taskkill //F //IM terminal64.exe >/dev/null 2>&1
