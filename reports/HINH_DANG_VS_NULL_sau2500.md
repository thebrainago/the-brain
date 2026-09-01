# Hinh dang co phan biet duoc voi ngau nhien khong?

> Cung mot luoi lan can, chay tren holdout THAT va tren chuoi NULL sinh
> tu chinh no. Cot `p` = ty le chuoi null dat toi hoac hon gia tri that
> (co +1 hieu chinh, nen p nho nhat la 1/(so_null+1)). Khong tieu suat
> FDR, khong cap phan quyet.

- do duoc: **23/23** ung vien (alpha duong 23 · alpha am 0)

**Chi dem tren ung vien co ALPHA DUONG** — mot he lo tien deu hon null cua no thi khong phai phat hien:
- **alpha o tam**: trung vi p = 0.060 · p<=0,05: **9/23** (ky vong ngau nhien 1.2)
- **ty le o duong**: trung vi p = 0.068 · p<=0,05: **5/23** (ky vong ngau nhien 1.2)
- **o tot nhat**: trung vi p = 0.090 · p<=0,05: **3/23** (ky vong ngau nhien 1.2)

## Alpha DUONG (xep theo p cua alpha o tam)

| ung vien | hinh dang that | alpha tam | null p95 | p(alpha) | p(ty le duong) | p(boi dinh) |
|---|---|---:|---:|---:|---:|---:|
| `EURGBP.H4.mua_qua_dem.gio_vao20_gio_ra14` | CAI GAI - dinh cao gap 330.5 lan trung vi lan can | 11.129 | 0.235 | 0.0004 | 0.0532 | 0.9948 |
| `AUDCAD.D1.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.3 lan | 3.561 | 2.602 | 0.0128 | 0.1072 | 0.7197 |
| `AUDCAD.H1.lap_gap.nguong0.001` | CAI GAI - da so lan can AM | 0.409 | -0.759 | 0.0136 | 0.03 | 0.0092 |
| `AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` | SUON DOC - 95% duong, dinh gap 2.5 lan | 3.944 | 3.456 | 0.0208 | 0.0984 | 0.4124 |
| `NZDCAD.H1.lap_gap.nguong0.005` | SUON DOC - 100% duong, dinh gap 2.1 lan | 0.457 | 0.366 | 0.0276 | 0.058 | 0.8432 |
| `NZDCAD.H1.lap_gap.nguong0.003` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.7 lan | 0.417 | 0.265 | 0.0344 | 0.0324 | 0.948 |
| `AUDCAD.H1.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 3.2 lan trung vi lan can | 2.652 | 2.558 | 0.0428 | 0.0324 | 0.5722 |
| `GBPCAD.H1.lap_gap.nguong0.001` | CAI GAI - dinh cao gap 5.1 lan trung vi lan can | 0.102 | -0.08 | 0.044 | 0.04 | 0.994 |
| `AUDCAD.H1.lap_gap.nguong0.003` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 0.699 | 0.684 | 0.0488 | 0.0588 | 0.8108 |
| `EURGBP.D1.cuoi_thang.truoc2_sau2` | CAI GAI - dinh cao gap 3.3 lan trung vi lan can | 1.151 | 1.15 | 0.0504 | 0.0676 | 0.8289 |
| `AUDCAD.H1.ou_quay_ve.n100_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.3 lan | 4.091 | 4.253 | 0.0568 | 0.1547 | 0.6256 |
| `NZDCAD.H4.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 3.7 lan trung vi lan can | 2.568 | 2.737 | 0.06 | 0.0876 | 0.7914 |
| `EURGBP.H4.ou_quay_ve.n200_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 3.028 | 3.286 | 0.0696 | 0.2563 | 0.4956 |
| `GBPCAD.H4.lap_gap.nguong0.001` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 0.865 | 1.306 | 0.0712 | 0.06 | 0.9356 |
| `EURGBP.D1.cuoi_thang.truoc1_sau4` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.7 lan | 1.064 | 1.223 | 0.0728 | 0.058 | 0.6886 |
| `EURGBP.H4.bollinger_ve.n50_k2.0` | CAO NGUYEN - 96% lan can duong, dinh chi gap 1.6 lan | 3.303 | 3.826 | 0.0772 | 0.1839 | 0.5178 |
| `EURCAD.H4.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 3.2 lan trung vi lan can | 2.534 | 3.167 | 0.082 | 0.1004 | 0.8375 |
| `EURGBP.D1.bollinger_ve.n50_k2.0` | SUON DOC - 100% duong, dinh gap 2.0 lan | 2.626 | 3.216 | 0.1012 | 0.1603 | 0.6062 |
| `US500CASH.D1.ibs_bat_day.nguong0.2_giu2` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.8 lan | 4.782 | 6.35 | 0.106 | 0.0448 | 0.6389 |
| `AUDCHF.H4.ou_quay_ve.n100_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.6 lan | 3.194 | 4.417 | 0.1124 | 0.1379 | 0.615 |
| `US500CASH.D1.ibs_bat_day.nguong0.3_giu1` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.8 lan | 4.49 | 7.01 | 0.1196 | 0.052 | 0.6737 |
| `AUDCHF.H4.ou_quay_ve.n200_z2.0` | SUON DOC - 96% duong, dinh gap 2.0 lan | 3.302 | 4.607 | 0.1216 | 0.2219 | 0.694 |
| `AUDNZD.H4.lap_gap.nguong0.005` | CAI GAI - dinh cao gap 4.1 lan trung vi lan can | 0.054 | 0.268 | 0.1395 | 0.1415 | 0.956 |

## Alpha AM — p nho o day nghia la LO IT HON NULL, khong phai edge

| ung vien | alpha tam | null p95 | p(alpha) |
|---|---:|---:|---:|
