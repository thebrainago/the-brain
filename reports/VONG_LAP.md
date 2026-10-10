# VONG LAP KHEP KIN - bang diem theo chang

Sinh tu `viec/` (git) boi `python3 -m nhan.vong_lap`, 2026-10-10 02:01 UTC. Khong LLM, khong du lieu gia. Chu du an 10/10/2026: *muc tieu la VONG LAP tim -> boc -> kiem -> giu -> ap dung -> vong sau; cac module nho chi la phan cua vong*.

## Tom tat (loi thuong)

- Vong lap (tim -> boc -> kiem -> giu -> ap dung): da chay 1573 viec, 105.0 gio may. Gio may chia: quet trong mau 84%, kiem ngoai mau 0,0%, tim nguon 0,2%, boc co che 0,0%, giu lai 0,0%, ap dung 0,0%.
- Vung lai tim duoc: 698. Da kiem ngoai mau: 0, dang cho may: 698, chua ra don: 0.
- Co che giu lai de ap dung vong sau: 0. Don ap dung (chuyen thi truong / nho SEEKER / ghi so tay) da xong: 3.
- Dang ket o: thoi gian may lech: quet trong mau 84%, kiem ngoai mau 0,0% (de xuat tong chang KIEM 50%, trong do ngoai mau it nhat 1/3)

## Thoi gian may theo chang (tong 105.0 gio, 1573 viec da xong)

| Chang | Viec xong | DAT | AM | CHUA DO | Gio may | Ty le | De xuat | Cho: chay duoc / bi chan |
|---|---|---|---|---|---|---|---|---|
| TIM - tim nguon | 27 | 20 | 0 | 7 | 0.2 | 0,2% | 10% | 0 / 2 |
| BOC - boc tach co che | 12 | 12 | 0 | 0 | 0.0 | 0,0% | 10% | 0 / 0 |
| KIEM - kiem dinh | 1300 | 1289 | 0 | 11 | 87.9 | 84% | 50% | 1022 / 9 |
| &nbsp;&nbsp;trong mau (kham pha) | 1300 |  |  |  | 87.9 | 84% |  |  |
| GIU - giu lai & chon loc | 3 | 3 | 0 | 0 | 0.0 | 0,0% | 5,0% | 0 / 0 |
| &nbsp;&nbsp;ghi so tay | 3 |  |  |  | 0.0 | 0,0% |  |  |
| AP_DUNG - ap dung vao vong sau | 0 | 0 | 0 | 0 | 0.0 | 0,0% | 15% | 0 / 0 |
| HA_TANG - ha tang do luong | 231 | 195 | 0 | 36 | 16.9 | 16% | 10% | 0 / 159 |

DAT o cot nay chi nghia 'don chay xong, ma thoat 0' (xem `bang_chung.dong_cuoi` cua tung don). De xuat = muc tieu vong, chu du an sua duoc trong `nhan/vong_lap.DICH`.

## Diem nghen

- thoi gian may lech: quet trong mau 84%, kiem ngoai mau 0,0% (de xuat tong chang KIEM 50%, trong do ngoai mau it nhat 1/3)
- chang TIM moi dung 0,2% thoi gian may (de xuat 10%)
- chang BOC moi dung 0,0% thoi gian may (de xuat 10%)
- chang GIU moi dung 0,0% thoi gian may (de xuat 5,0%)
- chang AP_DUNG moi dung 0,0% thoi gian may (de xuat 15%)
- 170 don cho ma moi (dien-dan-v2, engine4, gia-v2, lenh-v1, ma-0810) nam im den khi may nha nap ma moi; 1022 don chay duoc ngay (~1.8 gio)
- TIM: doc duoc 3 dien dan (146 bai), 8 nguon bi chan/tat/can Chrome, 5 lan tham do link khong co link nao
- GIU: 0 co che giu lai (can >= 3 thi truong qua xac_nhan, >= 50% ung vien) -> chua co gi de AP DUNG vao vong sau

## San luong tung chang

- TIM: 27 lan chay; doc duoc 3 dien dan (146 bai moi), 8 nguon bi chan / tat / can Chrome, 5 lan tham do link khong co link.
- BOC: hepha do x1, hepha duc x1, ho_so_bot x1, ho_so_tai_san x9
- KIEM trong mau: CAI_GAI 85, CAO_NGUYEN 880, HON_HOP 138, KHONG_CO_LAI 9, KHONG_DOC_DUOC 134
- KIEM ngoai mau: vung lai 0 da kiem, 698 dang cho, 0 chua ra don; o ngau nhien da ra don 175
- GIU: 0 co che duoc giu lai
- AP DUNG: ghi 3

## Kiem ngoai mau: cao nguyen co du bao duoc gi khong?

| Nhom | Da kiem | QUA (co lai) | RUOT | Khong do duoc | Ty le qua |
|---|---|---|---|---|---|
| vung lai (o tot nhat cua luot quet CAO NGUYEN) | 0 | 0 | 0 | 0 | - |
| doi chung: o tot nhat cua luot quet khac | 0 | 0 | 0 | 0 | - |
| doi chung: o ngau nhien cung luoi | 0 | 0 | 0 | 0 | - |

QUA = co lai tren doan xac_nhan (mo, khong tinh phep thu) bang ENGINE MO PHONG. Ben trong mau luon dep hon ngoai mau (chon o tot nhat trong 3.000 o); so sanh voi nhom doi chung moi cho biet cao nguyen co hon ngau nhien hay khong.

## Phep so sanh voi doi chung (ke hoach dong bang 10/10/2026 - nguong dat TRUOC khi co ket qua)

Hai cau hoi khac nhau. HON = chenh >= 10 diem va p < 0.05 (mot phia, chinh xac); KEM = nguoc lai; CHUA_DU = it hon 20 cap / 20 phep moi ben; con lai NGANG (kem MDE: chenh nho nhat phep thu thay duoc voi luc 80%). Ca hai dung ket luan cua lan kiem DAU (cung engine) cho moi o; khong hieu chinh da phep thu vi day la NHAN canh bao, khong phai cong chan.

| Phep thu | So cap | Ca hai qua | Cao qua / ngau ruot | Cao ruot / ngau qua | Ca hai ruot | Ty le cao | Ty le ngau | Chenh | p (hon) | MDE | Ket luan |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. chon o TOT NHAT trong luoi co hon chon BUA mot o cung luoi? (ghep cap, McNemar) | 0 | 0 | 0 | 0 | 0 | - | - | - | - | - | CHUA_DU |

| Phep thu | Cao: da kiem | Cao: qua | Doi: da kiem | Doi: qua | Ty le cao | Ty le doi | Chenh | p (hon) | MDE | Ket luan |
|---|---|---|---|---|---|---|---|---|---|---|
| 2. luoi xep CAO NGUYEN co ben hon luoi khac? (hai nhom, Fisher) | 0 | 0 | 0 | 0 | - | - | - | - | - | CHUA_DU |

| Nhom (ty le tuyet doi) | Da kiem | QUA | Ty le qua | Khoang tin cay 95% (Wilson) |
|---|---|---|---|---|
| vung lai | 0 | 0 | - | - |
| doi chung: o tot nhat luot quet khac | 0 | 0 | - | - |
| doi chung: o ngau nhien | 0 | 0 | - | - |

## Co che (che_do | kieu_lot | cho_lui)

(chua co ket qua ngoai mau)

GIU = qua xac_nhan o >= 3 thi truong va >= 50% so ung vien co ket luan (NHAN, khong phai cong chan; niem phong la quyet dinh rieng).

## Co che giu lai (dau vao vong sau)

- (chua co co che nao du dieu kien giu lai)

## Viec cho may nha

- 1192 don dang cho: 1022 chay duoc ngay (uoc ~1.8 gio), 170 nam im vi cho ma moi (engine4 x139, ma-0810 x24, so-ea-v1 x5, gia-v2 x4, dien-dan-v2 x2, swap-v1 x1).
- May nha tung khai kha nang: data, mt5, windows.
- MOT LAN, chu du an dan dong sau vao phien Claude Code o may nha de nap ma moi (khong lam gi them):

      Doc thu cloud: chay `b cau lay && b cau thu`, commit phan sua tay cua ban o qwen/cau_git.py roi `git pull --ff-only`, khoi dong lai bo chay `b cau chay --lien-tuc --nghi 20`, va bao ket qua bang `b cau noi`.

## Khuyen nghi cho phien cloud / `giam_sat_may_nha`

- (vong dang chay deu)

## Don vua ra lan nay

- kiem ngoai mau: 0; kiem lai engine moi: 0; ap dung: 0; loi: 0
