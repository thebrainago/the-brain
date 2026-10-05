# BANG GIA AI BOX (chu du an chup tu home.ai-box.vn/pricing?tab=api, 05/10/2026)

Don vi: dong (d) / 1 trieu token. "-" = khong ho tro. Gia co the doi: so lai trang goc khi tinh tien that.

| Model | Input | Output | Cache read | Cache create |
|---|---|---|---|---|
| qwen3.6-flash | 1222 | 2444 | 24,18 | 1222 |
| qwen3.7-flash | 520 | 2080 | 104 | 520 |
| qwen3.7-plus | 1664 | 6890 | 332,8 | 1664 |
| qwen3.7-max | 6500 | 19500 | 1300 | 6500 |
| qwen3.8-flash | 832 | 2444 | 83,2 | 1040 |
| qwen3.8-max (= max-0902) | 10400 | 31200 | 650 | 10400 |
| glm-5.2 / ZHIPU GLM-5.2 | 7280 | 22880 | 1456 / 1352 | - |
| glm-5.3 / ZHIPU GLM-5.3 | 7280 | 22880 | 1352 | - |
| glm-5.2-fast-preview | 14560 | 45760 | 2912 | 14560 |
| glm-5.3-prime | 14560 | 45760 | 2912 | - |
| kimi-k2.7-code | 4940 | 20800 | 988 | 4940 |
| kimi-k3 | 15600 | 78000 | 1560 | - |
| ds/deepseek-flash | 2600 | 10400 | 52 | - |
| ds/deepseek-v4-pro | 11440 | 34320 | 379,6 | - |

## Doc bang nay
- **Output dat gap 3-4 lan input** o moi model; model "suy luan" tinh ca token nghi vao output -> dat `max_tokens` vua du.
- **`ds/deepseek-flash` cache read chi 52 d** (re hon input 50 lan): tien to lenh GIONG HET nhau giua cac lan goi (khuon + hang rao dat TRUOC, phan thay doi dat SAU) -> trung cache. Day la cach tiet kiem lon nhat khi goi hang loat.
- **`qwen3.8-flash` re nhat o ca input lan output** trong nhom co the dung: output 2444 d vs 10400 d cua deepseek-flash (re gan 4,3 lan), cache read 83 d.
- `qwen3.8-max`, `kimi-k3`, `glm-5.3-prime`, `ds/deepseek-v4-pro` dat gap 4-30 lan: chi leo thang khi model re sai 2 vong.

## Uoc tinh mot cuoc goi dien the (3.000 token vao, 1.500 ra, khong cache)
- qwen3.8-flash: ~5,2 d · ds/deepseek-flash: ~23 d · kimi-k2.7-code: ~46 d · ds/deepseek-v4-pro: ~86 d · qwen3.8-max: ~78 d.
- 35 the x (1 + 2 vong sua toi da) ~ 105 cuoc: ~550 d (qwen3.8-flash) toi ~2.400 d (deepseek-flash) - **duoi vai nghin dong**. Chi phi khong phai van de cua viec nay; van de la chat luong va thoi gian.
