# VONG LAP KHEP: tim -> boc -> kiem -> giu -> ap dung (chu du an 10/10/2026)

Chu du an nhac lai (10/10/2026): *"muc tieu cua the brain la VONG LAP lien tuc: tim nguon chien luoc / he thong chat luong => boc tach co che
=> kiem dinh => giu lai va chon loc co che hieu qua => ap dung va bo sung vao cac vong ve sau. Viec ta dang lam chi la nhung module nho."*

Nghia la: dung toi uu tung nhanh (gia lap, bo kiem luat backtest, mot con bot). Phai co MOT vong chay lien tuc, va moi chang cua vong
phai DO duoc. Truoc moi viec tu hoi: viec nay dua chang nao cua vong lai gan hon, hay chi lam dep mot nhanh?
(Khong nham voi `vong_lap.py` doi v1 da hu tri o `nghi_huu/`: day la module moi, o `nhan/vong_lap.py`.)

## 1. Bang diem (lam truoc moi phien)

```
python3 b.py vong-lap --in          # chi xem (alias: b vl --in)
python3 b.py vong-lap               # xem + ghi reports/VONG_LAP.md va reports/vong_lap/*
python3 b.py vong-lap --giao 240    # + ra toi da 240 don kiem ngoai mau / kiem lai engine moi / ap dung vao viec/cho (KHONG push)
python3 -m nhan.vong_lap --json     # day du dang JSON
```

Module khong trang thai: moi con so suy ra tu `viec/xong` + `viec/cho` + `viec/may` (git). Khong LLM, khong du lieu gia, khong ghi `nao.db`.
Nguoi goi `--giao` phai tu `git add viec/cho reports/vong_lap` + commit + push.

| chang | la gi | cong cu `nc cc` / don | de xuat ty le gio may |
|---|---|---|---|
| TIM | nguon chien luoc / he chat luong moi (dien dan, MQL5, link, SEEKER) | `yeu_cau_seeker`, `b dien-dan`, `b link` | 10% |
| BOC | boc co che tu nguon (ho so bot, ho so `.set`, ho so tai san) | `ho_so_bot`, `ho_so_set`, `ho_so_tai_san` | 10% |
| KIEM | kiem dinh: TRONG MAU (kham_pha) roi NGOAI MAU (xac_nhan) | `quet_luoi`, `thu_luoi`, `ea_tho_*` ... | 50% (it nhat 1/3 la ngoai mau) |
| GIU | giu lai + chon loc co che qua kiem o nhieu thi truong | `vl-gh-*`, `ghi_hieu_biet` | 5% |
| AP DUNG | nap nguoc: quet chuyen thi truong / khung lan can, yeu cau SEEKER nguon cung loai | `vl-tf-*`, `vl-sk-*` | 15% |
| HA TANG | hieu chuan, do engine, don dep (khong thuoc vong nhung an gio may) | `hieu_chuan_luoi` ... | 10% |

Ty le de xuat la `DICH` trong `nhan/vong_lap.py` (chu du an sua duoc).

## 2. Do 10/10/2026 (truoc khi co vong): vong KHONG khep

Tren 1.573 viec / 105 gio may cua may nha: 84% gio may la quet trong mau; 16% hieu chuan (HA TANG); TIM 0,2%; BOC ~0; GIU 3 viec vat;
AP DUNG 0; kiem NGOAI MAU = 0 viec. 698 vung lai (cao nguyen, 880 lan khai) chua lan nao duoc kiem ngoai mau. Moi luot quet dung engine
v3 (lac quan 15-55% so voi EA that). Dieu nay dung voi muc tieu cua chu du an: chi chay mot khuc cua vong, khuc de do ra con so dep.

## 3. Cach kiem (chang KIEM -> GIU) va vi sao co nhom doi chung

- Moi vung lai cua mot luot quet -> don `vl-xn-<id>`: `nc cc thu_luoi` tren doan `xac_nhan` (doan MO: khong tinh phep thu, khong tieu FDR).
  KHONG BAO GIO tao don `niem_phong` (niem phong la quyet dinh co chu dich cua cloud, mot lan cho moi khai bao dong bang).
- **Nhom doi chung** (de do xem buoc loc "cao nguyen" co hon boc tham khong - tranh *winner's curse*):
  `doi` = o tot nhat cua luot quet KHONG phai cao nguyen (~12% don); `ngau` = mot o ngau nhien cung luoi voi moi vung lai (cu 4 vung lai 1 o).
  Chon ngau nhien theo hat giong co dinh (cung dau vao -> cung o), nen co the tai lap.
- Ket qua moi don duoc doc tu 25 dong cuoi cua `viec/xong` (`TOM_TAT {json}` la dong cuoi moi; dong cuoi cu van doc duoc, bi cat thi
  danh dau KHONG_DO_DUOC). **KHONG_DO_DUOC khong bao gio tinh la QUA hay RUOT.** QUA = co lai sau phi, khong chay tai khoan,
  >= 10 lenh o tai lot da thu; RUOT = ket luan duoc va khong dat.
- Co che = `che_do|kieu_lot|lui/-`. **Nhan GIU**: qua xac_nhan o >= 3 thi truong VA >= 50% trong >= 5 ket qua ket luan duoc. Day la NHAN,
  khong phai cong chan. `so_voi_nen` = HON_NEN / NGANG_NEN / CHUA_BIET (so voi nhom doi chung). `san_sang_niem_phong` chi bat khi co ket qua
  tu engine >= 4 (engine v3 lac quan).

### Cach doc ket qua: ke hoach DONG BANG truoc khi co ket qua nao (10/10/2026)

Khi 1.022 don kiem ngoai mau tra ve, `nhan/vong_lap.so_sanh_nhom` tra loi HAI cau hoi (nguong la hang `SO_SANH_*`, khong doi sau khi nhin so):

1. **Chon o TOT NHAT trong luoi co hon chon BUA mot o cung luoi khong?** (`cao_vs_ngau`, ghep cap, McNemar chinh xac mot phia.) Neu KHONG hon:
   3.000 o quet khong them gi so voi thu vai o -> dem gio may sang chieu rong (them thi truong, co che), khong quet sau.
2. **Luot quet duoc xep CAO NGUYEN co ben hon luot quet khac khong?** (`cao_vs_doi`, hai nhom doc lap, Fisher chinh xac mot phia, chi so sanh o tot nhat
   cua moi ben.) Neu KHONG: cach xep cao nguyen khong du bao gi, dung dung no lam bo loc duy nhat.

- Ket luan: **HON** = chenh >= 10 diem va p < 0,05 (mot phia); **KEM** = nguoc lai; **CHUA_DU** = it hon 20 cap / 20 phep moi ben; con lai **NGANG** va
  luon di kem **MDE** (chenh nho nhat phep thu thay duoc voi luc 80%): "khong thay" co the chi la "khong du mau de thay" (CLAUDE.md: ket luan am tinh kem MDE).
  Chenh be khong bao gio thanh HON du mau lon. Hai phep thu cung luc, khong hieu chinh: day la NHAN canh bao, khong phai cong chan.
- **Cung mot thuoc do** (`kq_cung_thuoc_do`): moi o lay ket luan cua LAN KIEM DAU (engine thap nhat). Don kiem lai engine moi chi ra cho co che da GIU,
  nen neu dung no de so sanh thi nhom cao bi do bang thuoc kho hon. Nhan GIU van dung ket qua tot nhat.
- KHONG_DO_DUOC (don chet, thieu so lieu) bi bo khoi ca hai phep thu - khong bao gio tinh la RUOT. Ca ty le tuyet doi (khoang tin cay Wilson) lan ty le theo
  DO MANH cua cao nguyen (ba nhom, khi >= 30 ket luan) nam trong `reports/VONG_LAP.md`.
- Dong tom tat bang loi thuong nam trong `tom_tat_cho_chu` (nen ra ca trong dong `VONG:` cua `giam_sat_may_nha`); diem nghen tu dong doi huong gio may khi ket qua la NGANG/KEM.

## 4. Chang AP DUNG (nap nguoc vao vong sau)

Co che duoc GIU -> `ke_hoach_ap_dung`: (a) quet chuyen sang thi truong chua quet / khung ke ben (chi vao o TRONG, co du lieu trong
`so_cai/doan.json`); (b) `ke_hoach_nho_lai`: don `vl-sk-*` nho SEEKER tim nguon cung loai co che va `vl-gh-*` ghi vao so tay nghien cuu.
Don chi sinh khi co co che GIU; idempotent (chay lai khong ra don trung).

## 5. Gioi han hien tai (nho ro)

- May nha dang chay ma cu (`44b3b23d+sua`): chi nhan don khong the `can`. 170 don cu khai `can` (engine4, ma-0810, dien-dan-v2, gia-v2, lenh-v1...) nam im
  cho toi khi may nha nap ma moi. Don `vl-xn-*` khong the, nen chay duoc ngay (moi don vai giay). Khi may nha da nap ma moi, `vl-xn4-*` kiem lai bang engine v4.
- Mot lan nap ma moi cho may nha (chu du an dan vao phien Claude Code o may nha): `b cau lay && b cau thu`, commit phan sua tay o `qwen/cau_git.py`
  roi `git pull --ff-only`, khoi dong lai `b cau chay --lien-tuc --nghi 20`, bao lai bang `b cau noi`.
- Tren Linux (cloud) khong co du lieu gia va khong ra mang: cloud chi lam NHAC TRUONG (bang diem, chon dot, ra don, doc ket qua); cac chang can du lieu
  (TIM, BOC tu ma nguon, KIEM) chay o may nha.

## 6. Van hanh moi gio (phien cloud)

Dieu phoi dinh ky `Giam sat may nha moi gio`: `python3 -m nhan.giam_sat_may_nha` (in 4 dong `VONG:` + `HANH_DONG`) -> lam theo khuyen nghi
(thuong la `python3 -m nhan.vong_lap --giao 240`) -> commit `viec/cho` + `reports/vong_lap` + push. Hang doi chia theo chang, khong don het vao quet.

## 7. Viec ke tiep (dung thu tu)

1. May nha chay het cac don `vl-xn-*` -> doc tong ket: ty le qua cua vung lai so voi nhom doi chung (pheu co hon boc tham khong? muc 3, phan "Cach doc ket qua").
2. Co che dau tien qua nhan GIU -> kiem do ben: thu cac o lan can cua nguoi qua (khong chi mot o), roi `vl-xn4-*` (engine v4).
3. Co che GIU -> AP DUNG: HEPHAESTUS rai luoi tham so quanh co che, SEEKER di tim nguon cung loai (TIM co muc tieu).
4. Khi du ket qua: chu du an/cloud quyet NIEM PHONG theo luat (mot lan, doan dong bang). Khong tu dong.
