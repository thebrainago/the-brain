# PHUONG AN BO TRI LLM THEO NGAN SACH (05/10/2026)

Nguon so: `SO_SANH_LLM.md` (do that 03/10: deepseek-flash 0,906 / qwen 0,854, tre 3,1s vs 15,9s; sai lech < 0,1 la nhieu),
`BANG_GIA_AIBOX.md` (gia d / 1 trieu token), do that 05/10 (35 the = 73 d, qwen3.8-flash, TAT che do suy luan).
Gia dinh: ngan sach la **moi thang** (neu chu du an hieu khac thi nhan/chia lai). Chi phi 1 cuoc goi mau (4k vao, 1,5k ra, khong cache):
qwen3.8-flash ~7 d · ds/deepseek-flash ~26 d (co cache ~12 d) · kimi-k2.7-code ~51 d · qwen3.8-max ~88 d · ds/deepseek-v4-pro ~97 d · kimi-k3 ~180 d.

## Vai tung model (moi viec CO MAY CHAM, sai 2 vong moi leo thang)
| Tang | Model | Lam gi |
|---|---|---|
| T1 tho | qwen3.8-flash (tat suy luan) | dien the, tom tat, trich bang, phan loai, soan nhap tai lieu |
| T2 nhanh | ds/deepseek-flash | goi cong cu, JSON ky luat, viec can tra nhanh + lap lai (cache 52 d) |
| T3 code | kimi-k2.7-code | viet / sua code nho co test chay duoc |
| T4 sau | ds/deepseek-v4-pro, qwen3.8-max | chi khi T1-T3 sai 2 vong; thiet ke kho |
| T5 | kimi-k3 | KHONG dung tru khi chu du an cho (178 d/cuoc) |
Claude (phien nay) giu: quyet dinh, doc mau 3 ket qua, xac nhan / niem phong. LLM khong bao gio niem phong.

## Bon muc ngan sach / thang (so cuoc goi toi da)
| Muc | T1 flash | T2 ds-flash | T3 kimi-code | T4 v4-pro / max | Ghi chu |
|---|---|---|---|---|---|
| 200k | 70% = ~20.000 | 20% = ~1.500 | - | 10% = ~230 (max) | du dien the + tom tat hang ngay; code do Claude viet |
| 300k | 60% = ~25.700 | 20% = ~2.300 | 10% = ~590 | 10% = ~340 (max) | them viec code nho |
| 400k | 50% = ~28.500 | 20% = ~3.000 | 15% = ~1.170 | 15% = ~620 (v4-pro) | khuyen nghi: can bang |
| 500k | 40% = ~28.500 | 20% = ~3.800 | 15% = ~1.470 | 25% = ~770 v4-pro + ~570 max | them du phong leo thang |
Quy tac chung: tien to lenh giong het (trung cache) · tat suy luan cho T1/T2 (bat la ton tien + rong noi dung) · `max_tokens` vua du ·
KHONG dat tran ngay / thang (chu du an tra truoc, 05/10: co bao nhieu dung bay nhieu); van ghi so chi `reports/deepseek/so_chi.jsonl` de biet con bao nhieu.
Khuyen nghi: **muc 300k** la du cho giai doan nay (viec that: ~100 d / 35 the; ca thang mau o muc 300k khong den het). Bat dau 300k, tang khi so chi that cho thay thieu.

## Cach dieu khien (khong tach phien)
`python3 -m nhan.giao_llm` (hoac import `goi(tang, prompt)`): goi thang AI Box tu phien nay (khoa do proxy gan, khong in khoa),
ghi so chi, chay may cham, tra ket qua. Claude goi - cham - doc mau - nhan; khong can phien phu.

## CAP NHAT 05/10 (so sanh 6 model tren cung 35 the, phien DeepSeek do, `reports/deepseek/so_sanh/_SO_SANH.md`)
Dat may cham / tien 35 the: qwen3.8-flash 35/35 · 73 d · 9,8s | ds/deepseek-flash 34/35 · 264 d · 3,1s (nhanh nhat) | qwen3.8-max 33/35 · 851 d |
ds/deepseek-v4-pro 30/35 · 1.079 d (THAP hon flash) | kimi-k2.7-code 13/35 (22 loi 502, khong tat duoc suy luan) | glm-5.3 0/35 (bat buoc suy luan).
=> **Sua bang chung (thay cho bang tren):** T1 qwen3.8-flash lam hang loat; T2 ds/deepseek-flash la vong sua cuoi + viec can nhanh;
**khong leo len v4-pro / max cho viec dien mau** (dat 4-12 lan, khong tot hon); T3 kimi, glm: KHONG dung goi hang loat qua AI Box.
Viec that su kho van do Claude lam. Loi hay gap cua model manh: thieu don_vi o NGUONG_CHI_BAO (them 1 dong vao prompt). 1 lan chay / 35 mau: chenh 1-2 the chua co nghia.
