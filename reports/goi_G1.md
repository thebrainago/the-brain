# GOI G1 — CONG RA TIEN + KHU TRUNG · 16/09/2026

**Noi ngan:** bang `b he` truoc day xep theo Sharpe, nen he lam ra 0,62%/nam
dung dau. Nay no xep theo TIEN, va no noi mot cau khac han: **khong he nao
trong kho qua duoc cong ra tien.**

## Da lam gi

1. **Noi `cong_ra_tien` len duong chay.** `bang_he._nguong()` doc THANG bon
   nguong tu `nhan/cong_ra_tien.py` (lai >=20%/nam · sut giam <=70% · >=20 lenh
   · >=8 nam) thay vi go lai. Ai doi nguong trong cong thi bang doi theo — co
   test khoa dieu do.
2. **Doi khoa xep hang.** Sharpe bi bo khoi khoa. Thu tu moi: ban trung xuong
   duoi · hon mua-giu bao nhieu DIEM CAGR · Calmar (lai tren moi don vi sut giam).
3. **Bat ban trung.** Dau van tay = (ma, cagr, sharpe, dd, calmar, so_lenh).
   Ban trung duoc danh `=` va ghi ro no la bi danh cua ai — **khong xoa**.
4. **Cot moi**: `mua-giu%`, `hon%`, `cong tien` kem ly do tung he truot.

## So truoc / sau

| | Truoc | Sau |
|---|---|---|
| Dong trong bang | 9 | 9 (khong xoa gi) |
| **He rieng biet** | khong dem | **7** (+2 ban trung) |
| Dung dau bang | EURGBP 0,62%/nam (Sharpe 1,47) | EURGBP `ou_quay_ve` **+6,39 diem** |
| Qua cong ra tien | khong hoi | **0/7** |

## Bang chung — vi sao 0/7

| He | CAGR% | mua-giu% | hon% | Vi sao truot |
|---|---|---|---|---|
| EURGBP.H4.ou_quay_ve.n200_z2.0 | 3,55 | -2,84 | +6,39 | lai < 20% · 5,37 nam < 8 |
| AUDCAD.H4.ou_quay_ve.n50_z2.5 | 4,46 | 0,60 | +3,86 | lai < 20% · 5,37 nam < 8 |
| AUDCAD.H4.rsi_dao_chieu | 4,16 | 0,60 | +3,55 | lai < 20% · 5,37 nam < 8 |
| EURGBP.H4.mat_can_bang | 0,62 | -2,84 | +3,47 | lai < 20% · 5,37 nam < 8 |
| XM_US100CASH.D1.z5 | 14,05 | 12,22 | +1,83 | lai < 20% · 6,17 nam < 8 |
| AUDCAD.H4.mat_can_bang | 0,69 | 0,60 | +0,09 | lai < 20% · 5,37 nam < 8 |
| US500CASH.D1.z5 | 8,26 | 9,97 | **-1,71** | **THUA mua-giu** + 2 cong that truot |

Hai ly do truot lap lai o moi he: **lai duoi 20%/nam** va **chuoi ngan hon 8 nam**.
Do khong phai loi cua cong — do la hinh dang that cua kho hien tai.

## Rui ro con lai

- **Dau van tay la ban RE.** No so SAU con so da do, khong so chuoi vi the.
  Hai co che that su khac nhau ma trung ca sau con so tren cung mot ma thi
  gan nhu chac chan la mot — nhung ban DUNG (hash chuoi vi the) can chay lai
  mo phong moi co. Chua lam.
- **Cham bang so da do, khong chay lai.** `cong_ra_tien.xet()` con do don bay
  thap nhat dat muc CAGR trong tran sut giam; ban nay chua goi den do.
- **Chua ap cho 592 he cua pheu** va 169/540 co che trong kho.
- Nguong `MIN_NAM = 8` loai gan het kho (du lieu H4 chi 5,37 nam). Day la cau
  hoi cho chu du an: ha nguong hay chap nhan chi do tren D1 dai hon.

## Viec chua lam (chuyen sang sau)

- Hash chuoi vi the tai NOI SINH, truoc khi tieu suat FDR (phan A day du cua G1).
- Chay lai toan kho qua cong moi (phan C).
- `b he --do-lai` goi `cong_ra_tien.xet()` that.

## Test

`test_bang_he_g1.py` — 6 bai, tat ca pass:
he Sharpe cao ma khong ra tien khong duoc dung dau · thua mua-giu thi xuong duoi
· bat ban trung · lech mot lenh thi KHONG phai ban trung · nguong lay tu
`cong_ra_tien` · he it lenh bi tu choi.


---

## SUA 16/09 (toi) — toi da noi sai ve FDR

Trong bao cao nay va o vai cho khac toi viet "ban trung tieu mot suat FDR" va
"chay pheu se tieu suat FDR". **Sai.**

`config/nguong.json` ghi ro:

```json
"bat_fdr": false,
"_ghi_chu_bat_fdr": "TAT 04/09/2026 theo quyet dinh chu du an.
                     Do truoc khi tat: 703 ket qua cham cong FDR,
                     0 cai truot CHI vi FDR. Doi thanh true de bat lai."
```

Va `nhan/cong.py` dong 868: `_bat_fdr = bool(nguong().get("bat_fdr", False))`
- khong bat thi `10_qua_fdr_online` **khong vao dieu kien PASS**.

So FDR van duoc GHI (`lord_v2` van chay, 1.811 dong) de con doi chieu neu sau
nay muon danh gia lai - nhung **no khong chan ai ca**. Quyet dinh cua chu du an
da duoc thuc hien va van dang co hieu luc.

Ly do THAT de mot ban trung dat gia van con nguyen, chi la khac: no **ngon mot
luot chay tester**, ma lan tester la 1.

Ly do THAT de dang ky gia thuyet truoc khi chay cung van con: do la
**pre-registration** (`plan_hash`, dong bang ke hoach truoc khi cham holdout) -
mot luat RIENG, khong lien quan gi den FDR.
