# Hinh dang co phan biet duoc voi ngau nhien khong?

> Cung mot luoi lan can, chay tren holdout THAT va tren chuoi NULL sinh
> tu chinh no. Cot `p` = ty le chuoi null dat toi hoac hon gia tri that
> (co +1 hieu chinh, nen p nho nhat la 1/(so_null+1)). Khong tieu suat
> FDR, khong cap phan quyet.

- do duoc: **3/3** ung vien

- **alpha o tam**: trung vi p = 0.119 · so ung vien p<=0,05: **0/3**
- **ty le o duong**: trung vi p = 0.129 · so ung vien p<=0,05: **0/3**
- **o tot nhat**: trung vi p = 0.257 · so ung vien p<=0,05: **0/3**

## Tung ung vien (xep theo p cua alpha o tam)

| ung vien | hinh dang that | alpha tam | p(alpha) | p(ty le duong) | p(boi dinh) | null p95 alpha |
|---|---|---:|---:|---:|---:|---:|
| `EURCAD.H4.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 3.2 lan trung vi lan can | 2.534 | 0.0594 | 0.0792 | 0.8713 | 2.411 |
| `EURCAD.H4.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.3 lan | 2.308 | 0.1188 | 0.1287 | 0.7525 | 3.259 |
| `EURCAD.D1.ibs_bat_day.nguong0.2_giu2` | CAI GAI - da so lan can AM | -0.59 | 0.2178 | 0.6535 | 0.4851 | 0.934 |
