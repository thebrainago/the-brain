# GOI G2-A — SLOT TESTER · 16/09/2026

**Noi ngan:** "TESTER = 1 la rang buoc VAT LY" — sai mot nua. May co 6 ban cai
MT5 va 8 thu muc du lieu; rang buoc nam o MA NGUON. Da go duoc 2/4 cho ghim
cung. **Tran van giu 1**, vi may chi co MOT thu muc du lieu co lich su that.

## Da lam gi

1. **`nhan/slot_tester.py` (moi)** — mot SLOT = `(exe, thu_muc_du_lieu, hau_to)`.
   `cap()` cap slot ranh, giu khoa cua no, va dat `BRAIN_MT5` / `BRAIN_MT5_DATA`
   de tien trinh con doc dung ban cua slot.
2. **`khoa_tester` khoa THEO SLOT** — `khoa_tester_<ten>.json`. Slot dau giu
   nguyen ten file cu de khong bo roi khoa dang giu luc nang cap.
3. **Sua mot cai bay that trong `phong()`** — ban cu doi den khi `tasklist`
   khong con `terminal64.exe` NAO. Voi hai slot thi no bao "xong" trong khi slot
   kia con chay, hoac ngoi doi ca luot cua slot kia. Nay cho dung tien trinh
   minh de ra (`p.poll()`).
4. **`dong_terminal()` nhin MOI khoa slot** — truoc chi nhin khoa mac dinh, nen
   `taskkill /IM terminal64.exe` se giet terminal cua slot khac.
5. **`b slot` / `b slot kiem`** + `tai_lieu/SLOT_TESTER.md`.

## Do duoc: vi sao van giu TESTER = 1

| Thu muc du lieu | Ban cai | Ma co lich su | Dung luong |
|---|---|---|---|
| `BB16F565…` | **XM Global MT5** | **32** | **2,42 GB** |
| `53785E09…` | MetaTrader 5 EXNESS | 14 | 0,06 |
| `D0E8209F…` | MetaTrader 5 | 4 | 0,10 |
| `1A842330…` | FXCE MT5 | 4 | 0,04 |
| `43A9BD89…` | Ultima Markets | 4 | 0,04 |
| `656C3515…` | XM MT5 | 0 | 0 |

Nam thu muc kia khong lam slot duoc, va **ly do khong phai dung luong**: khac
broker la khac symbol, khac spread, khac lich su. Hai slot khac broker cho hai
ket qua khong so duoc — ma van in ra mot bang trong nhu so duoc.

Slot 2 phai la **ban sao portable cua chinh XM Global MT5**, va viec do can
dang nhap -> chu du an lam tay, 5 buoc trong `tai_lieu/SLOT_TESTER.md`.

## Cai PHANH

`nen_nang_tran()` doi DU BA dieu kien, thieu mot la tu choi:
1. >= 2 slot san sang (co lich su gia that)
2. khong slot nao dung chung `(thu_muc, hau_to)`
3. `reports/slot_kiem_chung.json` ghi `giong_nhau` VA `song_song_khop` deu true

Dieu kien 3 la hai phep thu bat buoc: **cung cau hinh hai slot ra ket qua y
het**, va **hai cau hinh chay cung luc moi cai khop voi lan chay rieng**.

## Rui ro con lai

- **Chua go cho ghim cung thu (1)**: `chay_tester_kho` van ghi de cung mot
  `.mq5`/`.ini`/`.xml`. Voi hai slot co thu muc RIENG thi khong dung nhau;
  `trung_thu_muc()` chan truong hop khai chung. Buoc sau: cho `chay_tester_kho`
  nhan `slot` de dat ten dau ra qua `slot.ten_ea()` / `slot.tep()`.
- **`kiem()` CO Y khong tu chay hai luot tester de so.** Viet mot bo so sanh
  chua bao gio chay duoc tren may nay thi vi pham chinh luat cua du an: do phai
  do TREN DUONG CHAY THAT. Khi co slot 2 that thi chay hai phep thu roi ghi
  bang chung.
- So slot nen bat dau o **2**, khong lay theo so nhan CPU: MT5 tester tu chia
  nhieu agent moi lan toi uu.

## Test

`test_slot_tester.py` — 9 bai, pass het. Sau bai la test cua cai PHANH:
khong nang khi 1 slot · khong nang khi chua co bang chung · khong nang khi
kiem chung TRUOT · chi nang khi du ca ba · bat slot chung thu muc · slot thieu
lich su thi khong san sang. Cong them: hai slot khoa doc lap (tra khoa slot nay
khong xoa khoa slot kia), va `cap()` dat dung bien moi truong.

`-k "khoa_tester or tester or bang_he"`: 39 passed.
