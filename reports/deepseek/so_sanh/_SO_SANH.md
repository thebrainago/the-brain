# SO SANH MODEL - cung 35 the "dien kieu + mien" (05/10/2026)

Cung prompt (tien to giong het + the), 1 lan / the, suy luan TAT, max_tokens 1500, 6 request song song, temperature 0,1.
Dau ra: `reports/deepseek/so_sanh/<model>/` (KHONG dung vao `reports/deepseek/the/`). Nhat ky: `_nhat_ky.jsonl`. Gia: `tai_lieu/BANG_GIA_AIBOX.md`.

| Model | Dat may cham | Token vao / ra (cache) | Tien (d, 35 the) | Giay / the | Ten o trung qwen3.8-flash | Lop trung o cung ten |
|---|---|---|---|---|---|---|
| qwen3.8-flash | 35/35 | 62.628 / 19.491 (35.840) | **73** | 9,8 | (chuan) | (chuan) |
| ds/deepseek-flash | 34/35 | 66.518 / 19.833 (45.184) | 264 | **3,1** | 0,36 | 0,88 |
| qwen3.8-max | 33/35 | 62.173 / 15.840 (29.696) | 851 | 8,5 | 0,45 | 0,96 |
| ds/deepseek-v4-pro | 30/35 | 66.518 / 22.577 (41.344) | 1.079 | 7,0 | 0,34 | 0,90 |
| kimi-k2.7-code | 13/35 (22 loi 502) | 24.621 / 20.320 (chi cac the thanh cong) | >= 460 (phan) | 28,5 | 0,42 | 0,92 |
| glm-5.3 | 0/35 | - | 0 | - | - | - |

## Doc ket qua
1. **qwen3.8-flash la lua chon mac dinh**: dat 35/35, re nhat (~2 d/the), ~10 giay/the. Cac model dat hon khong co.
2. **ds/deepseek-flash la du phong tot nhat** (3,6 lan dat hon qwen3.8-flash nhung van re): 34/35, nhanh nhat (3,1 giay/the). Leo thang len no truoc, KHONG leo thang len v4-pro.
3. **ds/deepseek-v4-pro khong dang tien o viec nay**: dat THAP hon deepseek-flash (30 vs 34) ma dat gap 4 lan. qwen3.8-max cung vay (12 lan gia qwen flash, khong hon).
4. **Moi loi cua model tot deu cung mot loai**: o `NGUONG_CHI_BAO` (nguong_adx, nguong_vao...) quen dien `don_vi` (6 trong 7 loi may cham cua deepseek-flash / v4-pro; qwen3.8-max con 1 loi doi khoa `ap_cheo` va 1 o thieu ten). Sua bang 1 dong trong prompt ("NGUONG_CHI_BAO cung can don_vi") hoac 1 vong sua - khong can doi model.
5. **Kimi va GLM-5.3 KHONG dung duoc cho goi hang loat qua cong AI Box nay**: khong tat duoc che do suy luan (GLM tra 400 "enable_thinking restricted to True"; Kimi bo qua tham so, chay lau ~28 giay va bi cong cat 502 o 22/35 the). Dung chung khi can suy luan sau voi viec NHO, khong dung de dien hang loat.
6. Do dong thuan thap: ten o chi trung 34-45% giua cac model (ten o la lua chon dat ten, khong co dap an duy nhat); lop o cung ten trung 88-96%. May cham KHONG do duoc "ten co dung y bot" - xem lai tay nhom the khong co tham so goc (xem `the/_BAO_CAO.md`).

## Gioi han cua phep so sanh
- 1 lan chay, 35 mau, temperature 0,1: hon kem 1-2 the (34 vs 35 vs 33) CHUA co y nghia thong ke. Chi chac: v4-pro / kimi / glm kem ro rang, flash re va du tot.
- Cham chi bang may cham (hinh thuc). Chua ai doc tay so sanh chat luong y nghia giua cac model.
- Tien tinh tu bang gia chup 05/10 va so token cua nhat ky; cache create khong tinh (nho).

## De xuat ke hoach chay (cho phien chi huy)
- Chay hang loat: `qwen3.8-flash`, suy luan TAT, 6 song song, tien to prompt co dinh, `max_tokens` 1500. Chi phi ~2 d / the.
- Vong sua 1: `qwen3.8-flash` kem loi cu the. Vong sua 2 (cuoi): `ds/deepseek-flash` (du phong re, nhanh), khong dung v4-pro / max / kimi / glm.
- Them vao tien to: "o NGUONG_CHI_BAO cung can don_vi" de tranh loi hay gap nhat.
- Ngan sach thang 300-500 nghin d: viec nay ~73 d / 35 the -> du dung cho hang chuc nghin the; ngan sach khong phai rang buoc, chat luong va thoi gian moi la.
