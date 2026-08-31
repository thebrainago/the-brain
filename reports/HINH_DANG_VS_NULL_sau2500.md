# Hinh dang co phan biet duoc voi ngau nhien khong?

> Cung mot luoi lan can, chay tren holdout THAT va tren chuoi NULL sinh
> tu chinh no. Cot `p` = ty le chuoi null dat toi hoac hon gia tri that
> (co +1 hieu chinh, nen p nho nhat la 1/(so_null+1)). Khong tieu suat
> FDR, khong cap phan quyet.

- do duoc: **2/2** ung vien (alpha duong 2 · alpha am 0)

**Chi dem tren ung vien co ALPHA DUONG** — mot he lo tien deu hon null cua no thi khong phai phat hien:
- **alpha o tam**: trung vi p = 0.062 · p<=0,05: **0/2** (ky vong ngau nhien 0.1)
- **ty le o duong**: trung vi p = 0.063 · p<=0,05: **0/2** (ky vong ngau nhien 0.1)
- **o tot nhat**: trung vi p = 0.098 · p<=0,05: **0/2** (ky vong ngau nhien 0.1)

## Alpha DUONG (xep theo p cua alpha o tam)

| ung vien | hinh dang that | alpha tam | null p95 | p(alpha) | p(ty le duong) | p(boi dinh) |
|---|---|---:|---:|---:|---:|---:|
| `EURGBP.D1.cuoi_thang.truoc2_sau2` | CAI GAI - dinh cao gap 3.3 lan trung vi lan can | 1.151 | 1.15 | 0.0504 | 0.0676 | 0.8289 |
| `EURGBP.D1.cuoi_thang.truoc1_sau4` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.7 lan | 1.064 | 1.223 | 0.0728 | 0.058 | 0.6886 |

## Alpha AM — p nho o day nghia la LO IT HON NULL, khong phai edge

| ung vien | alpha tam | null p95 | p(alpha) |
|---|---:|---:|---:|
