# Hinh dang co phan biet duoc voi ngau nhien khong?

> Cung mot luoi lan can, chay tren holdout THAT va tren chuoi NULL sinh
> tu chinh no. Cot `p` = ty le chuoi null dat toi hoac hon gia tri that
> (co +1 hieu chinh, nen p nho nhat la 1/(so_null+1)). Khong tieu suat
> FDR, khong cap phan quyet.

- do duoc: **76/108** ung vien

- **alpha o tam**: trung vi p = 0.222 · so ung vien p<=0,05: **0/76**
- **ty le o duong**: trung vi p = 0.222 · so ung vien p<=0,05: **0/76**
- **o tot nhat**: trung vi p = 0.278 · so ung vien p<=0,05: **0/76**

## Tung ung vien (xep theo p cua alpha o tam)

| ung vien | hinh dang that | alpha tam | p(alpha) | p(ty le duong) | p(boi dinh) | null p95 alpha |
|---|---|---:|---:|---:|---:|---:|
| `EURCAD.H4.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 3.2 lan trung vi lan can | 2.534 | 0.1111 | 0.1111 | 1.0 | 0.01 |
| `EURCAD.H4.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.3 lan | 2.308 | 0.1111 | 0.1111 | 0.6667 | 0.719 |
| `AUDNZD.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 3.7 lan trung vi lan can | 0.551 | 0.1111 | 0.2222 | 0.6667 | 0.398 |
| `EURGBP.D1.bollinger_ve.n50_k2.0` | SUON DOC - 100% duong, dinh gap 2.0 lan | 2.626 | 0.1111 | 0.2222 | 0.6667 | 1.343 |
| `AUDCAD.H1.rsi_dao_chieu.n14_vao25_ra_60` | SUON DOC - 100% duong, dinh gap 2.0 lan | 2.652 | 0.1111 | 0.3333 | 0.8889 | 1.508 |
| `AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.3 lan | 3.944 | 0.1111 | 0.4444 | 0.1111 | 2.723 |
| `AUDCAD.D1.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 3.4 lan trung vi lan can | 0.768 | 0.1111 | 0.1111 | 0.7778 | 0.108 |
| `AUDCAD.D1.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.3 lan | 3.561 | 0.1111 | 0.1111 | 1.0 | 0.147 |
| `AUDCHF.D1.cuoi_thang.truoc3_sau3` | SUON DOC - 88% duong, dinh gap 2.4 lan | 0.523 | 0.1111 | 0.1111 | 0.7778 | -0.043 |
| `AUDCHF.D1.bollinger_ve.n20_k2.0` | SUON DOC - 96% duong, dinh gap 2.2 lan | 3.447 | 0.1111 | 0.2222 | 0.4444 | 2.576 |
| `NZDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` | SUON DOC - 78% duong, dinh gap 2.3 lan | 1.661 | 0.1111 | 0.4444 | 0.6667 | 1.293 |
| `NZDCAD.H4.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 3.7 lan trung vi lan can | 2.568 | 0.1111 | 0.1111 | 0.7778 | 1.33 |
| `EURCAD.H1.ou_quay_ve.n100_z2.0` | CAI GAI - dinh cao gap 4.3 lan trung vi lan can | 0.645 | 0.1111 | 0.1111 | 1.0 | -0.018 |
| `EURCAD.H1.ou_quay_ve.n200_z2.0` | SUON DOC - 84% duong, dinh gap 2.7 lan | 1.471 | 0.1111 | 0.2222 | 0.6667 | 0.924 |
| `EURCAD.H4.ou_quay_ve.n50_z2.5` | CAI GAI - dinh cao gap 3.1 lan trung vi lan can | 1.46 | 0.1111 | 0.1111 | 0.7778 | 1.163 |
| `EURGBP.H4.ou_quay_ve.n100_z2.0` | CAI GAI - dinh cao gap 3.7 lan trung vi lan can | 2.313 | 0.1111 | 0.5556 | 1.0 | 2.095 |
| `EURGBP.H4.mua_qua_dem.gio_vao20_gio_ra14` | CAI GAI - dinh cao gap 330.5 lan trung vi lan can | 11.129 | 0.1111 | 0.2222 | 1.0 | -0.94 |
| `AUDCAD.H1.lap_gap.nguong0.001` | CAI GAI - da so lan can AM | 0.409 | 0.1111 | 0.1111 | 0.1111 | -1.548 |
| `AUDCAD.H1.lap_gap.nguong0.003` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 0.699 | 0.1111 | 0.1111 | 0.7778 | 0.283 |
| `AUDCAD.H1.ou_quay_ve.n100_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.3 lan | 4.091 | 0.1111 | 0.2222 | 0.6667 | 2.554 |
| `AUDCHF.H1.lap_gap.nguong0.005` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.5 lan | 0.337 | 0.1111 | 0.1111 | 1.0 | -0.07 |
| `NZDCAD.H1.lap_gap.nguong0.003` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.7 lan | 0.417 | 0.1111 | 0.2222 | 0.8889 | 0.104 |
| `AUDCHF.H4.ou_quay_ve.n200_z2.0` | SUON DOC - 96% duong, dinh gap 2.0 lan | 3.302 | 0.1111 | 0.1111 | 0.7778 | 1.895 |
| `NZDCAD.H1.lap_gap.nguong0.005` | SUON DOC - 100% duong, dinh gap 2.1 lan | 0.457 | 0.1111 | 0.2222 | 0.8889 | 0.166 |
| `NZDCAD.H1.ou_quay_ve.n200_z2.0` | CAI GAI - da so lan can AM | 1.401 | 0.1111 | 0.2222 | 0.1111 | 0.615 |
| `EURCAD.H4.rsi_dao_chieu.n14_vao25_ra_60` | SUON DOC - 67% duong, dinh gap 2.2 lan | 1.187 | 0.2222 | 0.5556 | 0.3333 | 0.985 |
| `EURCAD.H4.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - dinh cao gap 8.3 lan trung vi lan can | 0.356 | 0.2222 | 0.1111 | 1.0 | 0.378 |
| `EURCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` | CAI GAI - dinh cao gap 6.8 lan trung vi lan can | 0.655 | 0.2222 | 0.4444 | 0.8889 | 1.33 |
| `EURGBP.D1.cuoi_thang.truoc2_sau2` | CAI GAI - dinh cao gap 3.3 lan trung vi lan can | 1.151 | 0.2222 | 0.1111 | 0.7778 | 1.098 |
| `AUDCAD.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 0.967 | 0.2222 | 0.2222 | 0.2222 | 1.608 |
| `AUDCAD.D1.rsi_dao_chieu.n7_vao30_ra_55` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 0.813 | 0.2222 | 0.2222 | 1.0 | 1.085 |
| `AUDCAD.H4.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.5 lan | 3.444 | 0.2222 | 0.3333 | 0.8889 | 3.978 |
| `AUDCAD.D1.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 6.6 lan trung vi lan can | 0.482 | 0.2222 | 0.2222 | 0.8889 | 0.784 |
| `AUDCHF.D1.ibs_bat_day.nguong0.15_giu1` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.9 lan | 1.601 | 0.2222 | 0.1111 | 0.8889 | 2.002 |
| `AUDCHF.H4.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 6.0 lan trung vi lan can | 2.299 | 0.2222 | 0.2222 | 0.8889 | 3.291 |
| `AUDCHF.D1.ibs_bat_day.nguong0.2_giu1` | SUON DOC - 73% duong, dinh gap 1.9 lan | 1.891 | 0.2222 | 0.2222 | 0.8889 | 2.044 |
| `AUDCHF.D1.ibs_bat_day.nguong0.2_giu2` | SUON DOC - 80% duong, dinh gap 2.2 lan | 0.875 | 0.2222 | 0.2222 | 0.8889 | 1.286 |
| `EURNZD.H4.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - dinh cao gap 4.4 lan trung vi lan can | 0.884 | 0.2222 | 0.2222 | 1.0 | 1.226 |
| `NZDCAD.H1.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 6.0 lan trung vi lan can | 0.606 | 0.2222 | 0.2222 | 1.0 | 0.757 |
| `US500CASH.D1.ibs_bat_day.nguong0.2_giu2` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.8 lan | 4.782 | 0.2222 | 0.2222 | 0.5556 | 5.602 |
| `NZDCAD.D1.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 14.3 lan trung vi lan can | 1.309 | 0.2222 | 0.2222 | 1.0 | 0.931 |
| `EURGBP.H4.bollinger_ve.n50_k2.0` | CAO NGUYEN - 96% lan can duong, dinh chi gap 1.6 lan | 3.303 | 0.2222 | 0.3333 | 0.4444 | 3.917 |
| `EURCAD.H4.ou_quay_ve.n100_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.7 lan | 1.399 | 0.2222 | 0.2222 | 0.6667 | 2.465 |
| `GBPCAD.H4.lap_gap.nguong0.001` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 0.865 | 0.2222 | 0.1111 | 0.8889 | 1.163 |
| `EURGBP.H1.ou_quay_ve.n50_z2.5` | SUON DOC - 84% duong, dinh gap 3.0 lan | 0.727 | 0.2222 | 0.2222 | 0.8889 | 2.56 |
| `EURGBP.H4.ou_quay_ve.n200_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 3.028 | 0.2222 | 0.5556 | 0.3333 | 3.571 |
| `AUDCAD.H4.ou_quay_ve.n200_z2.0` | SUON DOC - 92% duong, dinh gap 2.4 lan | 2.904 | 0.2222 | 0.2222 | 0.4444 | 3.187 |
| `AUDCAD.H1.ou_quay_ve.n200_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.2 lan | 2.754 | 0.2222 | 0.2222 | 0.4444 | 2.85 |
| `AUDCHF.H4.ou_quay_ve.n100_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.6 lan | 3.194 | 0.2222 | 0.1111 | 0.6667 | 2.952 |
| `NZDCAD.H4.lap_gap.nguong0.005` | SUON DOC - 60% duong, dinh gap 2.0 lan | 0.098 | 0.2222 | 0.2222 | 0.8889 | 1.088 |
| `NZDCAD.H4.ou_quay_ve.n200_z2.0` | SUON DOC - 88% duong, dinh gap 2.3 lan | 1.614 | 0.2222 | 0.4444 | 0.5556 | 2.301 |
| `EURGBP.D1.cuoi_thang.truoc1_sau4` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.7 lan | 1.064 | 0.3333 | 0.1111 | 0.7778 | 1.144 |
| `US500CASH.D1.ibs_bat_day.nguong0.3_giu1` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.8 lan | 4.49 | 0.3333 | 0.1111 | 0.6667 | 7.91 |
| `NZDCAD.H4.bollinger_ve.n50_k2.0` | CAI GAI - da so lan can AM | 1.409 | 0.3333 | 0.3333 | 0.1111 | 2.218 |
| `EURNZD.D1.bollinger_ve.n50_k2.0` | CAI GAI - da so lan can AM | 0.424 | 0.3333 | 0.5556 | 0.1111 | 1.659 |
| `EURCAD.H4.ou_quay_ve.n200_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.6 lan | 1.916 | 0.3333 | 0.3333 | 0.6667 | 3.242 |
| `GBPCAD.H4.lap_gap.nguong0.003` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.0 lan | 0.604 | 0.3333 | 0.3333 | 0.7778 | 1.973 |
| `EURGBP.H1.lap_gap.nguong0.005` | CAO NGUYEN - 80% lan can duong, dinh chi gap 2.0 lan | 0.077 | 0.3333 | 0.3333 | 0.75 | 0.216 |
| `AUDCAD.H1.lap_gap.nguong0.005` | SUON DOC - 100% duong, dinh gap 2.1 lan | 0.328 | 0.3333 | 0.2222 | 1.0 | 0.424 |
| `AUDCAD.H4.ou_quay_ve.n50_z2.5` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 4.333 | 0.3333 | 0.3333 | 0.3333 | 5.429 |
| `EURNZD.H4.ou_quay_ve.n100_z2.0` | CAI GAI - da so lan can AM | 1.397 | 0.3333 | 0.3333 | 0.1111 | 1.815 |
| `EURCAD.D1.rsi_dao_chieu.n7_vao30_ra_55` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.2 lan | 1.084 | 0.4444 | 0.5556 | 0.3333 | 1.982 |
| `EURGBP.H4.rsi_dao_chieu.n14_vao25_ra_60` | SUON DOC - 100% duong, dinh gap 2.8 lan | 0.573 | 0.4444 | 0.3333 | 0.6667 | 1.347 |
| `GBPCAD.D1.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.6 lan | 1.665 | 0.4444 | 0.4444 | 0.7778 | 6.963 |
| `AUDCAD.D1.ichimoku_cheo.tenkan9_kijun26_chi_muaTrue` | CAI GAI - dinh cao gap 15.7 lan trung vi lan can | 0.457 | 0.4444 | 0.7778 | 0.8889 | 0.9 |
| `EURGBP.H4.rsi_dao_chieu.n14_vao30_ra_55` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.7 lan | 1.39 | 0.4444 | 0.4444 | 0.3333 | 2.186 |
| `AUDCHF.D1.bollinger_ve.n50_k2.0` | CAI GAI - dinh cao gap 5.6 lan trung vi lan can | 0.777 | 0.4444 | 0.6667 | 0.8889 | 1.949 |
| `EURGBP.H1.ou_quay_ve.n100_z2.0` | CAI GAI - dinh cao gap 3.1 lan trung vi lan can | 0.248 | 0.4444 | 0.4444 | 0.8889 | 2.228 |
| `EURGBP.H1.ou_quay_ve.n200_z2.0` | SUON DOC - 84% duong, dinh gap 2.3 lan | 1.22 | 0.4444 | 0.4444 | 0.8889 | 2.673 |
| `NZDCAD.H4.ou_quay_ve.n100_z2.0` | CAI GAI - dinh cao gap 81.4 lan trung vi lan can | 1.131 | 0.4444 | 0.3333 | 1.0 | 3.926 |
| `NZDCAD.H4.ou_quay_ve.n50_z2.5` | CAI GAI - dinh cao gap 11.7 lan trung vi lan can | 0.935 | 0.4444 | 0.4444 | 1.0 | 2.016 |
| `EURCAD.D1.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 3.5 lan trung vi lan can | 0.765 | 0.5556 | 0.3333 | 0.8889 | 3.091 |
| `EURGBP.D1.rsi_dao_chieu.n7_vao30_ra_55` | SUON DOC - 100% duong, dinh gap 2.0 lan | 1.264 | 0.5556 | 0.3333 | 0.6667 | 1.594 |
| `AUDCHF.H4.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 6.2 lan trung vi lan can | 0.606 | 0.5556 | 0.2222 | 0.8889 | 4.856 |
| `AUDCHF.D1.rsi_dao_chieu.n7_vao30_ra_55` | SUON DOC - 89% duong, dinh gap 2.5 lan | 0.899 | 0.5556 | 0.6667 | 0.8889 | 2.188 |
| `EURGBP.H4.ou_quay_ve.n50_z2.5` | CAI GAI - dinh cao gap 3.1 lan trung vi lan can | 1.476 | 0.5556 | 0.6667 | 0.8889 | 4.447 |

## Khong do duoc

- `EURGBP.H4.dong_luong_dau_thang_khi_gia_giam.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCAD.D1.dong_luong_dau_thang_khi_gia_giam.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCAD.D1.dong_luong_dau_thang_khi_gia_giam.`: khong co tham so -> khong co lan can de do
- `EURCAD.H1.ban_lo_cuoi_nam_thue.mac_dinh`: khong co tham so -> khong co lan can de do
- `EURCAD.D1.ghim_gia_tuan_dao_han.mac_dinh`: khong co tham so -> khong co lan can de do
- `GBPCAD.D1.ghim_gia_tuan_dao_han.mac_dinh`: khong co tham so -> khong co lan can de do
- `EURGBP.H4.ghim_gia_tuan_dao_han.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCHF.H4.pha_day_hut_quet_stop.mac_dinh`: khong co tham so -> khong co lan can de do
- `EURCAD.H4.mat_can_bang_lenh_dong_cua.mac_dinh`: khong co tham so -> khong co lan can de do
- `EURGBP.H4.mat_can_bang_lenh_dong_cua.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCAD.H4.mat_can_bang_lenh_dong_cua.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCAD.H4.mua_lai_co_phieu_quy_theo_ngan_sach.mac_dinh`: khong co tham so -> khong co lan can de do
- `EURCAD.H1.ban_lo_cuoi_nam_thue.`: khong co tham so -> khong co lan can de do
- `EURCAD.H4.mat_can_bang_lenh_dong_cua.`: khong co tham so -> khong co lan can de do
- `EURCAD.D1.ghim_gia_tuan_dao_han.`: khong co tham so -> khong co lan can de do
- `GBPCAD.D1.ghim_gia_tuan_dao_han.`: khong co tham so -> khong co lan can de do
- `EURGBP.H4.mat_can_bang_lenh_dong_cua.`: khong co tham so -> khong co lan can de do
- `AUDCAD.H4.mat_can_bang_lenh_dong_cua.`: khong co tham so -> khong co lan can de do
- `EURNZD.H1.ban_lo_cuoi_nam_thue.`: khong co tham so -> khong co lan can de do
- `GBPCAD.D1.phi_bao_hiem_bien_dong_gian_no.mac_dinh`: khong co tham so -> khong co lan can de do
- `EURGBP.H4.phi_bao_hiem_bien_dong_gian_no.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCAD.D1.phi_bao_hiem_bien_dong_gian_no.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCHF.D1.phi_bao_hiem_bien_dong_gian_no.mac_dinh`: khong co tham so -> khong co lan can de do
- `GBPCAD.D1.bu_rui_ro_truoc_cong_bo_vi_mo.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCAD.D1.gamma_duong_keo_ve.mac_dinh`: khong co tham so -> khong co lan can de do
- `EURCAD.H4.rut_von_quy_tuong_ho.mac_dinh`: khong co tham so -> khong co lan can de do
- `AUDCAD.H4.rut_von_quy_tuong_ho.mac_dinh`: khong co tham so -> khong co lan can de do
- `GBPCAD.D1.phi_bao_hiem_bien_dong_gian_no.`: khong co tham so -> khong co lan can de do
- `GBPCAD.D1.bu_rui_ro_truoc_cong_bo_vi_mo.`: khong co tham so -> khong co lan can de do
- `AUDCAD.D1.phi_bao_hiem_bien_dong_gian_no.`: khong co tham so -> khong co lan can de do
- `AUDCHF.D1.phi_bao_hiem_bien_dong_gian_no.`: khong co tham so -> khong co lan can de do
- `GOP.ichimoku_cheo.D1.chi_so_my+vang.tenkan9_kijun26_chi_muaTrue`: FileNotFoundError: khong co du lieu cho RO:CHI_SO_MY+VANG. Co: AUDCAD, AUDCHF, AUDDKK, AUDHKD, AUDHUF, AUDJPY, AUDNOK, AUDNZD, AUDPLN, AUDSEK, AUDSGD, AUDTHB, 
