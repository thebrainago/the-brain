# TRU NGHI - bien kien thuc thanh co che kiem dinh duoc
*2026-09-01 16:04:32*

> Tru nay KHONG ket luan gi ve tien. No chi de xuat. Moi con so van di
> qua `nhan/cong.py` va van ton ngan sach FDR nhu mau viet tay.

## 1. Doi chieu vong truoc
- De xuat da ghi so: **21** (bi tu choi truoc kiem dinh 1, da co ket qua 15, dang cho 5)

| Co che | Ho | Ket qua |
|---|---|---|
| `ep_mua_lai_ban_khong_thanh_khoan_can` | pha_vo | {"FAIL": 1} |
| `rut_von_quy_tuong_ho` | dong_tien | {"FAIL": 7} |
| `gamma_duong_keo_ve` | quay_ve_trung_binh | {"FAIL": 1} |
| `bu_rui_ro_truoc_cong_bo_vi_mo` | vi_mo | {"FAIL": 8} |
| `phi_bao_hiem_bien_dong_gian_no` | bien_dong | {"FAIL": 10} |
| `mua_lai_co_phieu_quy_theo_ngan_sach` | dong_tien | {"FAIL": 4} |
| `mat_can_bang_lenh_dong_cua` | phien | {"FAIL": 5} |
| `pha_day_hut_quet_stop` | quay_ve_trung_binh | {"FAIL": 4} |
| `ghim_gia_tuan_dao_han` | lich | {"FAIL": 9} |
| `ban_lo_cuoi_nam_thue` | lich | {"FAIL": 7} |
| `hap_thu_khoi_luong` | quay_ve_trung_binh | {"FAIL": 2} |
| `phi_bao_hiem_cuoi_tuan` | phien | {"FAIL": 1} |

## 2. Vong nay
- Doc 8 tai lieu hang A/B
- Nhan duoc 6 de xuat, **qua ba cua kiem: 0**
- Trong do 1 co nguon truy nguyen
  ve tai lieu (5-6 truoc day luon la 0 - moi co che la cua LLM).
- Tai san dung de kiem: EURCAD

### Bi tu choi (va vi sao - vong sau se doc lai muc nay)
- `mua_bien_dong_thap_ibs_thap`: vao[0] phep 'phu_vi' khong hop le
- `ban_bien_dong_cao_ibs_cao`: vao[0] phep 'phu_vi' khong hop le
- `mua_tich_luy_khoi_luong_gia_thap`: vao[0] phep 'phu_vi' khong hop le
- `ban_phan_phoi_khoi_luong_gia_cao`: vao[0] phep 'phu_vi' khong hop le
- `mua_vol_gian_no_sau_lang`: vao[0] phep 'phu_vi' khong hop le
- `ban_sau_vol_gian_no_nghich`: vao[0] phep 'phu_vi' khong hop le

## 3. Ba cua kiem moi de xuat phai qua

1. **Cu phap** - dung ngu phap khai bao, khong co toan hang nhin truoc.
2. **Ty le kich hoat** - trong khoang 0,5%..98% so bar. Duoi thi khong
   bao gio du lenh; tren thi la mua-giu tra hinh.
3. **Phep cat** - tin hieu tai bar t phai giong het du co biet cac bar
   sau t hay khong, do tren 40 moc cat ngau nhien. Bai kiem nay da tu
   chung minh la nhay (chen ro ri co y -> bat duoc).