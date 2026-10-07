# GIAO VIEC CHO DEEPSEEK - quy tac van hanh (chu du an duyet 05/10/2026)

Muc dich: DeepSeek GIAM TAI (token Claude + thoi gian) cho viec khoi luong lon co may cham tu dong. Khong de no quyet dinh, khong de no
cham diem, khong de no cham vao cau hinh / so tay that. Co so: `TOI_UU_TOKEN.md` muc 8.

## 1. Dieu kien de goi duoc (CHUA co o phien 05/10 sang)
Host `api.ai-box.vn` trong Network access + bien `AIBOX_API_KEY` o moi truong, phien MOI. Kiem: `python3 -m qwen.mo_hinh` (khong in khoa).
Chua goi duoc thi KHONG giao viec, KHONG lach (khong qua proxy la, khong dan khoa vao tep).

## 2. Hang rao (DeepSeek khong duoc lam)
- Khong ghi `nao.db` / `nc.db` / `config/*.json` / `kho_phuong_phap/` truc tiep: dau ra di vao `reports/deepseek/<viec>/` (ban NHAP); Claude hoac may cham moi chuyen vao kho.
- Khong sua `nhan/*.py` da co; chi tao tep moi trong thu muc nhap. Khong `exec` ma no sinh ra ngoai may cham.
- Khong duoc "cham diem" hay ket luan DAT / AM / xac nhan / niem phong. Nhan nguon cua moi thu no ra = `tho`.
- Moi tep ra phai ghi: ten viec, so lan sua, ma cham (hash may cham), de truy vet.
- Tran: 2 vong sua / viec (cham -> tra loi loi cu the cho no -> cham lai), sai tiep thi Claude lam tay hoac bo. Tran token moi lo.

## 3. Viec GIAO (moi viec phai co MAY CHAM viet TRUOC)
| Viec | May cham (ma, do Claude viet truoc) | Dau ra nhap |
|---|---|---|
| The phuong phap hang loat: 35 the con o `CHUA_PHAN_LOP` -> dien kieu + mien tu `ho_so_set` / `khoi_co_che` | `the_phuong_phap.kiem_the` + moi o co ten that trong `.set`/engine + mien chua cac gia tri bot da dung | `reports/deepseek/the/<ma>.json` |
| Test cho module nho chua co test (script assert, khong pytest) | chay duoc + >= 1 dot bien co y bi bat | `reports/deepseek/test/` |
| Tai lieu theo mau (bang tham so, vi du) | tieu de dung mau + khong co so khong nam trong nguon | `reports/deepseek/tai_lieu/` |
| Kham pha rong tren doan kham_pha (`b nc tho`) | cong san co (canary, chi phi do duoc) | so tay nhan `tho` |
| Doc log dai / tim rong | subagent `haiku`, chi tra ket luan 3-8 dong | - |

## 4. Viec GIU o Claude
Thiet ke, ke hoach dong bang + nguong, bo phep pha ma (phan kho nhat cua may cham), doc ket qua, xac nhan / niem phong, bao cao chu du an, viec nho.

## 5. Quy trinh mot viec
1. Claude viet to giao (<= 300 chu) + may cham, commit may cham TRUOC.
2. DeepSeek nhap -> may cham -> loi cu the -> sua (toi da 2 vong).
3. Dat: Claude doc MOT dong ket qua + lay mau 3 muc xem co loi tinh vi khong, roi chuyen vao kho. Khong dat: Claude lam tay hoac bo.
4. Ghi vao bang do (muc 8.4 TOI_UU_TOKEN): token cua Claude, so vong, diem may cham, loi lot qua phep pha ma. Nhan B cho mot loai viec chi khi
   diem may cham >= cach A va token Claude giam >= 30%.

## 6. Viec dau tien (khi goi duoc)
35 the con CHUA_PHAN_LOP trong `kho_phuong_phap/` (viec so 1 o bang tren) - day cung la 1 trong 3 viec cua phep thu 8.4.
