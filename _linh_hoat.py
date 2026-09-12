# -*- coding: utf-8 -*-
"""BIEN "GIAO DICH LINH HOAT" THANH LUAT DO DUOC.

Chu du an: *"neu he ra tien ta se nhay ra truoc khi sap hoac dung lai da cashout
quay lai hoac bom tien ngoai vao cuu tai khoan"*.

Y do DUNG, nhung "nhay ra truoc khi sap" chi co nghia neu no la mot LUAT. Neu
ta biet luc nao sap thi chinh cai biet do la edge, va no phai nam trong he va
duoc backtest. Con "linh hoat" khong khai bao thi khong do duoc, va thu khong
do duoc thi khong biet no giup hay hai.

Ba phien ban DO DUOC cua "linh hoat":

  A. RUT LOI DINH KY - moi quy rut r% phan lai vuot von goc. Doi tien tu tai
     khoan ra tui, nen `sut giam tren VON CA NHAN` khac han `sut giam tren tai
     khoan`. Day la phien ban manh nhat cua y chu du an va no khong doi mot
     kha nang du bao nao.

  B. CHAN VON CHU SO HUU - thoat het khi tai khoan sut qua X% tu dinh, vao lai
     khi he cho tin hieu moi. Day la "nhay ra truoc khi sap" duoi dang luat.

  C. KHONG LAM GI - moc doi chieu.

KHONG lam: bom tien ngoai vao cuu tai khoan. Do khong phai mot luat giao dich,
do la chuyen mot khoan lo giao dich thanh mot khoan lo doi song. Kho ket qua
cua chinh du an nay co san mot vi du: DCA voi bom von cho -100,5% o MOI muc von.
"""
import sys, json, warnings
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np
from nhan import chi_phi as CP, da_thoi_dai as DT, du_lieu as DU
from nhan import mo_phong as MP, ngu_phap as NP

MA, KHUNG, L = "YH_NASDAQ", "D1", 2.0
TEN = "macd_stochastic_doub"

kho = [c for c in NP.doc_kho() if str(c.get("ten")).startswith(TEN)]
spec = kho[0]
cua = DT.cac_cua_so_sach(MA, KHUNG)
d = max(cua, key=lambda c: c["so_bar"])["df"]
tr, _ = DU.hai_nua(d, 0.6)
cp = CP.tu_du_lieu(MA, tr)
cp = cp[0] if isinstance(cp, tuple) else cp
vi_the = np.asarray(NP.sinh_tu_spec(spec, tr), float)
kq = MP.chay(tr, vi_the, cp, ma=MA, khung=KHUNG, don_bay=L, gop="so_hoc")
# `kq.loi` la loi suat LOG - phai doi ve so hoc bang expm1 truoc khi gop
# bang (1+r). Gop log truc tiep la loi da ghi trong bo nho du an
# ("don bay gop log la SAI"), va toi vua mac lai no.
r = np.expm1(np.nan_to_num(np.asarray(kq.loi, float)))
n = len(r)
nam = (tr.index[-1] - tr.index[0]).days / 365.25
print(f"{spec['ten'][:40]} | {MA} {KHUNG} L={L:.0f} | {n} bar, {nam:.1f} nam\n")


# 05/09: ban cai dat tay o day co loi DINH DAT LAI - no do sut giam ke tu lan
# dat lai gan nhat roi bao do la sut giam cua he, nen luat chan trong nhu cat
# DD tu -72% xuong -42% trong khi duong von khong doi. Da chuyen ca hai luat
# vao `bien_don_bay.ap_luat_von` (mot ban cai dat, dinh that va dinh lam viec
# tach nhau) va goi tu day. Ket qua dung: xem `_chan_dd_holdout.py`.
from nhan import bien_don_bay as B
from pathlib import Path


def chay(rut_quy=0.0, chan_dd=None):
    k = B.ap_luat_von(kq.loi, nam, chan_dd=chan_dd, rut_ky=rut_quy)
    if k.get("vo"):
        return {"vo": True}
    return {"tai_khoan_cuoi": k["tai_khoan_cuoi"], "da_rut": k["da_rut"],
            "tong_cuoi": k["tong_cuoi"], "cagr_tong": k["cagr"],
            "dd_tai_khoan": k["dd_tai_khoan"], "dd_tong": k["dd_von_ca_nhan"],
            "vo": False}


print(f"{'kich ban':<34}{'CAGR':>8}{'DD tai khoan':>14}{'DD tong':>10}{'da rut':>9}")
kb = [("C. khong lam gi", dict()),
      ("A. rut 50% lai moi quy", dict(rut_quy=0.5)),
      ("A. rut 100% lai moi quy", dict(rut_quy=1.0)),
      ("B. chan DD 30%", dict(chan_dd=0.30)),
      ("B. chan DD 40%", dict(chan_dd=0.40)),
      ("A+B rut 50% + chan 40%", dict(rut_quy=0.5, chan_dd=0.40))]
for ten, kw in kb:
    k = chay(**kw)
    if k.get("vo"):
        print(f"{ten:<34}  VO TAI KHOAN")
        continue
    print(f"{ten:<34}{k['cagr_tong']:>7.2%}{k['dd_tai_khoan']:>13.2%}"
          f"{k['dd_tong']:>10.2%}{k['da_rut']:>9.2f}")
