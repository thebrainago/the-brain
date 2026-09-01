# p cua UNG VIEN so voi p tren CHUOI NULL

Moc so sanh cho van de `vd_p_ung_vien_lech_null`. Chuoi null duoc QUET cung
mot luoi template/tham so da dang ky, roi goi `placebo()` thang - dung ngu
nghia CONG THE HE 1, vi 692/770 dong `ket_qua` mang p_placebo deu la cua
ngay 15/08 khi placebo con chay vo dieu kien.

| Quan the | n | trung vi p | p<0,05 |
|---|---:|---:|---:|
| CHUOI NULL, tat ca | 584 | 0.5 | 3.77% |
| UNG VIEN the he 1, tat ca | 692 | 0.340 | 13.44% |
| CHUOI NULL, alpha>0 | 138 | 0.125 | 13.77% |
| UNG VIEN the he 1, alpha>0 | 281 | 0.105 | 30.25% |

Du thua khong dieu kien: **3.6 lan**. Trong nhom alpha>0: **2.2 lan**.

## Doc ra sao

1. **p KHONG lech he thong.** Tren chuoi null, phan phoi khong dieu kien co
   trung vi 0.5 va 3.77% duoi 0,05 -
   dung chuan, va hoi bao thu so voi muc danh nghia 5%.
2. **Tien de cua chan doan sai o nhom alpha>0.** `placebo()` dem mot phia theo
   huong he thang null, nen ngay tren CHUOI NULL nhom alpha>0 cung cho trung vi
   0.125 va 13.77% duoi 0,05. So 30% cua ung
   vien khong duoc dem so voi 5%.
3. **Con du thua that, nhung nho hon nhieu so voi ve ban dau** - va no khong
   song sot qua hieu chuan hinh dang (368 gia thuyet x 100 null: 7 cai dat
   p<=0,05 trong khi ngau nhien thuan cho 5,8).

Quet 32 chuoi null, 584 o, 0 loi, 0 o khong toi placebo.