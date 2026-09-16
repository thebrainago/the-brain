# GOI G3-B — KEO CAC HE RA TIEN VAO SO · 16/09/2026

**Noi ngan:** Sonic R **qua duoc cong ra tien** — he DAU TIEN lam duoc dieu do
(bang `b he` hien tai la 0/7). Nhung con so 26%/nam trong so tay khong tai lap
nguyen xi, va cau hinh do la mot **cuc dai luoi** nen chua duoc goi la phat hien.

## 1. Sonic R H4 US500CASH — TP 5% / SL 1%

Tin hieu: `_sonic_r_tpsl.tin_hieu_sonic_r` (hoi ve dai Dragon EMA34 trong xu
huong EMA89). Du lieu 15.689 bar H4, **10,5 nam** (2016-01 -> 2026-07).

### Qua `cong_ra_tien.xet()` — cong chinh thuc

```
verdict        : RA_TIEN
truot          : []           (khong nguong nao truot)
he             : L=3 · CAGR 24,36% · maxDD -46,58% · Calmar 0,523
                 Sharpe 0,842 · 182 lenh · phoi nhiem 2,06
mua-giu CUNG DD: L=1,41 · CAGR 9,00% · maxDD -46,58% · Sharpe 0,467
cach biet      : +15,36 diem CAGR o CUNG SUT GIAM
```

**Day la cau hoi tien, va cau tra loi la co.** O cung muc sut giam, he cho
24,36%/nam so voi 9,00%/nam cua mua-giu co don bay tuong duong.

### Hang don bay (lai kep SO HOC, khong gop log)

| L | CAGR | maxDD | chay tai khoan |
|---|---|---|---|
| 1,0 | +8,78% | −18,21% | khong |
| 1,5 | +12,97% | −26,25% | khong |
| 2,0 | +16,98% | −33,63% | khong |
| **3,0** | **+24,36%** | **−46,58%** | khong |
| 4,0 | +30,68% | −57,35% | khong |
| 5,0 | +35,72% | −66,24% | khong |

`xet` chon L thap nhat dat muc CAGR trong tran sut giam — khong toi uu L theo
ket qua, de khong bien viec chon don bay thanh mot vong quet tham so.

### So voi con so trong so tay

| | So tay | Do lai 16/09 |
|---|---|---|
| CAGR @ L=3 | 26%/nam | **24,36%** |
| Calmar tang theo don bay | co | co, nhung **rat it**: 0,37 -> 0,39 -> 0,40 |

Gan dung. Khac biet con lai gan nhu chac chan la do cua so du lieu va cach gop.

### Doi chieu tren XM_US500CASH (cung co che, khac nguon gia)

TP5/SL1: CAGR 8,47% · maxDD −19,3% · Calmar 0,44 — **hon moc mua-giu**.
Thap hon US500CASH mot chut nhung cung huong. Khong phai hien tuong cua mot
nguon gia.

## 2. Ba dieu KHONG duoc bo qua

1. **TP5%/SL1% la mot CUC DAI LUOI.** Luoi trong `_sonic_r_tpsl.py` quet
   7 TP x 7 SL x 4 moc gio = 196 cau hinh, va dinh nam o **MEP luoi** (TP toi
   da da thu la 3,0%) — chinh docstring cua `_sonic_r_don_bay.py` ghi dieu do.
   Theo luat cua du an, "tot nhat trong N" phai so voi ban gia cung co mau
   truoc khi goi la phat hien.
2. **`cong_ra_tien` KHONG tra loi "co that khong".** Chinh docstring cua no ghi
   vay. Con phai qua `nhan/cong.py`: placebo (hoan vi chuoi VI THE), FDR, alpha
   co y nghia.
3. **Sut giam 46,58% o L=3.** Cong cho qua vi tran la 70%, nhung do la muc mot
   nguoi that phai ngoi nhin. L=2 cho 16,98% o −33,63% — gan bang mua-giu ve
   sut giam ma gap 2,4 lan ve lai.

## 3. Chua lam

- **Chua ghi vao `nao.db`.** Ghi thang vao `ket_qua` ma khong co
  pre-registration (`plan_hash`) la chiem suat FDR bang mot phep DO, va lan sau
  doc lai se tuong la mot xac nhan. Phai dang ky gia thuyet TRUOC roi chay.
- **Luoi Bigmouse AUDCAD** va **trailing x4,8**: chua do. Ca hai nam o duong
  khac (`.set` that chay trong MT5 tester, va ho quan tri) nen can luot tester
  rieng — tester dang la LAN = 1 va me boc 293 file dang chiem may.
- **Chua qua MT5 tester.** Moi so tren la ban Python. Quy tac cua du an la
  tester TRUOC, Python SAU — o day nguoc lai vi tester dang ban, nen phai ghi
  ro: **day la ket qua Python, chua xac nhan tren tester**.

## 4. Y nghia

`b he` hom nay: **0/7 he qua cong ra tien**. Sonic R la cai dau tien qua duoc,
va no khong nam trong kho — no nam trong mot script `_*.py` chay tay. Do dung
la van de V7 trong ho so: *thu TUNG ra tien nam ngoai duong chay*.
