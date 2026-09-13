# -*- coding: utf-8 -*-
"""_do_ma_mt5.py - DO khoang cach giua KHO GIA CUA LAB va SO MA SAN THUC CO.

Chu du an 13/09/2026: *"Mt5 co rat nhieu ma o xm nen neu thieu ma la co van
de."* Dung: `du_lieu.kho()` co 194 bang, con MT5 liet ke ca tram ma. Neu kho
gia la mot anh chup cu thi moi ket luan "quet 194 ma" thuc ra la "quet phan
con sot lai cua mot lan tai nam ngoai".
"""
import collections
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

import MetaTrader5 as mt5          # noqa: E402
from chay_tester_z5 import XM_EXE  # noqa: E402
from nhan import du_lieu as DU     # noqa: E402

NGAN = "\\"

ok = mt5.initialize(path=str(XM_EXE), timeout=60000)
print("mt5.initialize:", ok, "" if ok else mt5.last_error())
if not ok:
    raise SystemExit(1)

a = mt5.account_info()
print("tai khoan:", a.login, "|", a.server, "|", a.company)

s = mt5.symbols_get()
print("TONG SO MA SAN CUNG CAP:", len(s))
c = collections.Counter((x.path.split(NGAN)[0] if x.path else "?") for x in s)
for k, v in c.most_common(12):
    print("   %-30s %d" % (k, v))

# Ma dang duoc CHON trong Market Watch (chi nhung ma nay tai duoc lich su
# ngay; ma chua chon phai `symbol_select` truoc).
chon = [x for x in s if x.visible]
print("dang chon trong Market Watch:", len(chon))

kho = {(k[0] if isinstance(k, tuple) else str(k).split("|")[0]) for k in DU.kho()}
ten_san = {x.name for x in s}
print()
print("kho gia cua lab :", len(kho), "ma")
print("san cung cap    :", len(ten_san), "ma")
print("lab CO ma san khong co :", len(kho - ten_san))
print("san CO ma lab khong co :", len(ten_san - kho))
print()
print("vi du ma san co ma lab THIEU:")
for m in sorted(ten_san - kho)[:20]:
    print("   ", m)
mt5.shutdown()
