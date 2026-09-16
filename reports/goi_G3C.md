# GOI G3-C — KHAU BOC: DO TRUOC, ROI SUA CAI DO DUOC · 16/09/2026

**Noi ngan:** gia dinh cua ke hoach sai. Bo doc **khong hong** — suat boc
79-90%. Nut that that la 293 file CHIEN LUOC chua tung thu, va khi thu thi
**vao kho 0** vi cong tu choi het. Sua duoc mot phan: 4/19 -> 6/19.

## 1. Do truoc: suat boc theo lan

```
lan          file  da thu   ra   suat   duong
chi_bao       737     701   633   90%   doc_chi_bao -> LLM
chien_luoc    374      81    65   80%   boc_ma_llm
quan_tri      157     157   124   79%   quan_tri.boc_kho (tat dinh)
tien_ich      113       0     0    -    bo CO CHU DICH
```

Ke hoach viet: *"sua loi .mq5 bi cham 0 diem"*. Loi do **da duoc sua tu truoc**;
suat hien tai 79-90%, khong con gi de sua o do.

Nut that that: **`chien_luoc` moi thu 81/374 (22%)** — 293 file chua tung vao
khau boc, va do la lop gia tri cao nhat (mot file chien luoc la ca mot he, khong
phai mot chi bao le). Kho cung da lon hon so trong so tay: **1.381 file ma**,
khong phai 389.

## 2. Chay thu 12 file de do truoc khi chay 293

277 giay / 12 file = **~23 giay/file** -> 293 file ≈ **1,9 gio**.

```
file ra co che   : 9/12 (75%)
khai bao qua kiem: 11
them vao kho     : 0
```

**Vao kho 0.** Neu chay thang ca 293 file thi do la 1,9 gio doi lay khong gi.
Do la ly do phai chay me 12 truoc.

## 3. Doc ly do tu choi — 26/30 la HINH THUC

| so | ly do |
|---|---|
| 7 | `co_che` phai la MOT CAU giai thich vi sao co nguoi tra tien |
| 9 | `vao[i]` phai co `trai` va `phai` |
| 6 | ho `xu_hướng` / `quay_ve_trung_bình` / `pha_vào` khong thuoc bang |
| 4 | toan hang phai la dict · `n` phai la so nguyen |
| 4 | suy bien (hai ve giong het · `close > high` luon sai) |

**Sau muc la loi DAU TIENG VIET.** Mo hinh doc dung co che, goi dung ten ho, chi
go co dau. Bo mot khai bao dung vi mot dau sac la lang phi dat nhat ca day
chuyen: file da tai ve, da khoanh vung, da ton mot luot LLM.

Va chin muc `phai co 'trai' va 'phai'` hoa ra la mot HINH DANG khac: mo hinh
chen thang chuoi `khong_dien_dat_duoc` vao mang `vao` cho phan no khong doc noi.
Mot khai bao co **5 ve, 4 ve dau hoan chinh**, ve thu 5 la chuoi do — va ca
khai bao bi bo.

## 4. Da sua: `boc_ma_llm.sua_may_moc()`

Chay TRUOC cong, trong chinh `kiem_va_giu` nen nam tren duong chay:

1. **Ten ho**: khop lai theo ban da bo dau. `quay_ve_trung_bình` ->
   `quay_ve_trung_binh`. **Khong doan**: `pha_vào` bo dau ra `pha_vao`, khong
   co trong bang, giu nguyen de cong tu choi.
2. **`co_che`**: danh sach -> chuoi, nhieu cau -> giu cau dau.
3. **Ve khong doc duoc**: bo khoi `vao`, **nhung danh dau `khong_day_du` + so
   ve mat**. Bo im lang roi coi nhu day du la cach chac chan nhat de sinh ra
   mot "phat hien" ve mot co che chua ai tung viet.
4. **Toan hang**: `"close"` -> `{"chi_bao":"gia","cot":"close"}`, so -> `{"so":n}`,
   `n` thuc/chuoi -> so nguyen.

**Ranh gioi khong duoc pha: chi sua CACH VIET, khong sua NOI DUNG.** `cheo_len`
khong duoc doi thanh `cheo_xuong`; dieu kien suy bien khong duoc "sua" cho het
suy bien — co bai test rieng khoa dieu do.

## 5. Ket qua do duoc

**Qua cong: 4/19 -> 6/19.** That thi khiem ton: +2 khai bao.

Nhung con lai deu la loi **NGU NGHIA**, khong sua may moc duoc:
- 7 khai bao co `co_che` khong noi duoc ly do kinh te (mo hinh bia mot cau mo ta
  lai chinh luat)
- 7 khai bao co MOI ve deu `khong_dien_dat_duoc`
- 4 dieu kien suy bien

Khop voi phep do cu da ghi trong so: *LLM dien 48 khai bao, tham dinh bac 41,
rong cuu 3*.

## 6. Mot suy doan cua toi da SAI — ghi lai de khoi lap

Giua chung toi nghi cong co loi: mot khai bao bi bao `phai co 'trai' va 'phai'`
trong khi `vao[0]` cua no du ca hai truong. Kiem ky: loi noi ve **`vao[4]`**,
con toi in `vao[0]`. Cong dung, toi doc nham chi so. Khong co loi cong nao.

## Buoc sau (chua lam)

**Nap loi cong nguoc cho LLM.** `mot_file` hien chi thu lai khi ket qua **rong**
— no chua bao gio dua danh sach loi cua `kiem_khai_bao` ve cho mo hinh sua. Do
la don bay lon nhat con lai, va no ton luot LLM nen phai do trên me nho truoc.
Tien le da co ngay trong file (dong 203-205): me 05/09 bi `them vao kho: 0` cho
80/80 khai bao, sua bang cach **xin them mot truong trong loi nhac**.

## Test

`test_sua_may_moc.py` — 10 bai, pass het. Nua so bai la test cua RANH GIOI:
khong doan ten ho khac han · khong sua dieu kien suy bien · moi ve hong thi giu
nguyen cho cong tu choi · khong doi ban goc.
