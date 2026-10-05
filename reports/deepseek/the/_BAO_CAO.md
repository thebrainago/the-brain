# BAO CAO - dien kieu + mien cho 35 the phuong phap (05/10/2026)

Nhan nguon: `tho`. Bo chay: `reports/deepseek/chay_dien_the.py`. Nhat ky tung goi: `reports/deepseek/the/_nhat_ky.jsonl`.
Khong sua nhan/, kho_phuong_phap/, config/, nc.db. Chua ket luan dat/am; ban nhap CHUA vao kho.

## Ket qua
- 35/35 the DAT may cham `python3 -m nhan.kiem_the_nhap reports/deepseek/the` (0 hong, `_CON_HONG.txt` khong co).
- So vong sua: **0 vong cho ca 35 the** (dat ngay lan dau). Khong phai leo thang.
- Thoi gian: 3 the thu 13 giay + 32 the con lai 57 giay (6 request cung luc); trung binh 9,8 giay / cuoc goi.

## Model nao lam viec gi
| Model | Viec | So goi | Token vao | Token ra | Cache read (nam trong "vao") |
|---|---|---|---|---|---|
| qwen3.8-flash | dien 35 the, lan dau | 35 | 62.628 | 19.491 | 35.840 |
| (khong dung) ds/deepseek-v4-pro, kimi, deepseek-flash | khong can leo thang | 0 | - | - | - |

Gia tinh theo `tai_lieu/BANG_GIA_AIBOX.md` (qwen3.8-flash: vao 832, ra 2444, cache read 83,2 d/1M):
vao khong cache 26.788 x 832 + cache 35.840 x 83,2 + ra 19.491 x 2.444 ~ **73 dong** cho ca 35 the (~2 dong / the).

## THAT BAI TRUOC KHI CHAY DUOC (chi phi lang phi, tinh rieng)
Lan chay thu dau (che do suy luan bat mac dinh) hong het:
- qwen3.8-flash tra **HTTP 502 "upstream request failed" sau ~30 giay** o MOI cuoc goi (6 cuoc goi, khong co token tra ve).
- ds/deepseek-v4-pro dung het 2000 token ra vao suy luan, noi dung rong: 3 cuoc goi, ~6.200 vao + 6.000 ra ~ **280 dong**.
- 2 cuoc goi chan doan ds/deepseek-flash (~2.000 ra moi cai, ~50 dong) + vai cuoc qwen3.8-flash bi 502.
Cach sua (dung tu do): **tat che do suy luan** - qwen: `"enable_thinking": false`; deepseek: `"thinking": {"type": "disabled"}`.
Sau do: ~450-700 token ra / the, 7-13 giay, khong loi. Nho: `reasoning_effort: low` KHONG du (van het 2000 token).
Cac con so tren la uoc tinh tu nhat ky chan doan (lan thu bi xoa khoi `_nhat_ky.jsonl` vi la ban chay hong), khong phai hoa don.

## Chat luong - LUU Y (may cham khong do duoc y nghia)
Lay mau 6 the doc tay: ten snake_case hop ly, lop / don vi / mien dung kieu. NHUNG:
- `kiem_the_nhap` ep 1..8 o nen the nao khong co tham so trong the goc (vd `gong_duong_doi_ung`, `nhoi_theo_loi`, `loc_sideway_nen`)
  thi model **tu dat o moi** (tp, buoc, tran_tang, lot / buoc_nhoi, he_so_lot_nhoi / nguong_dao_hien...). Do la o DE XUAT theo mo ta, khong phai
  ten tham so that cua bot -> Claude nen xem lai nhom nay truoc khi chuyen vao kho.
- Ten o khong doi chieu duoc voi `luoi.ThamSo` / ho so `.set` bang may cham (chi kiem snake_case + lop + mien).
- Mien la khoang hop ly de rai luoi, chua doi chieu voi gia tri bot da dung.

## Loi hay gap
Khong co loi may cham o lan dau. Loi ha tang: 502 khi bat suy luan (xem tren); noi dung rong khi suy luan an het token.
