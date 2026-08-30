# BAN DO — file nao lam gi  (`b ban-do`)

## Vao/ra phien
| file | viec |
|---|---|
| `b.py` / `b.cmd` | mot cua vao cho moi lenh. `b` de xem menu |
| `BAN_GIAO.py` | VAO phien: trang thai song + ban giao hom qua |
| `KET_PHIEN.py` | KET phien: git commit + sinh `TIEP_TUC_MAI.md` moi |
| `nhip_song.py` | mot phep dem duy nhat, dung chung cho ca hai file tren |
| `TIEP_TUC_MAI.md` | ban giao **dang hieu luc**. Ban cu o `nhat_ky/` |
| `NHAT_KY.md` | moi ngay mot dong |

## Hat nhan `nhan/` — dung chung, khong tru nao duoc lach
| file | viec |
|---|---|
| `so.py` | so cai chi-them + hang doi viec + van de + nhip tim |
| `du_lieu.py` | nap bar tu chinh cong cu se giao dich; chon ban theo do phu |
| `chi_phi.py` | spread DO tu cot spread cua bar; phi qua dem theo co che |
| `mo_phong.py` | engine backtest. Vao lenh `open[i+1]`, phi bat doi xung |
| `do_luong.py` | chi so + alpha Newey-West so voi mua-giu SAU PHI |
| `mau.py` | 15 template viet tay. Chien luoc = template + tham so |
| `ngu_phap.py` | cua duy nhat cho kien thuc moi vao he (khai bao JSON) |
| `cong.py` | cong PASS: cong re -> placebo -> FDR LORD theo ho x the he x quy |
| `canary.py` | 5 canary gac engine + mutation audit |
| `do_luc.py` | MDE — edge nho nhat con nhin thay duoc; cong KHA THI |
| `gop_lop.py` | mot co che tren CA LOP = MOT suat FDR |
| `pham_vi.py` | phep thu phan chung theo lop tai san |
| `danh_muc.py` | tang 3: von + ghep cac gia thuyet da qua cong |
| `sang_loc.py` | pheu 4 vong V0 van tay -> V1 re -> V2 kinh te -> V3 phan chung |
| `nha_may_null.py` | sinh chuoi null (block bootstrap / GARCH / hoan vi) |
| `hop_dong.py` | hop dong artifact SEEKER -> ha nguon |
| `quant_plan.py` | pre-registration bat bien (plan_hash) |
| `bien_dich_ung_vien.py` | tai lieu -> CandidateArtifact (khop theo van canh) |
| `doc_hieu.py` | doc van xuoi thanh co che, bang CU PHAP khong LLM |
| `nguon_bai_viet.py` | nguon RSS/Atom |
| `ma_nguon.py` | .mq5 -> CodeArtifact |
| `vuon_nguon.py` | do suat nguon, chia ngan sach, tu tim nguon moi |
| `chi_phi.py` `du_lieu.py` `cong.py` `so.py` | **4 file duoc test day nhat** |

## 5 tru `tru/`
| tru | viec | nhip cuoi |
|---|---|---|
| `seeker.py` | thu thap 24/7, dedup, provenance, ban giao artifact | 23/08 |
| `quantlab.py` | hai lane: xac nhan ung vien / kham pha tu chu. Hai duong: DON LE va GOP | 22/08 |
| `nghi.py` | sinh gia thuyet tu tai lieu, hoc tu ket qua | 16/08 (rc=1) |
| `banker.py` | vi mo point-in-time, che do thi truong | 16/08 |
| `evolution.py` | do SUC KHOE day chuyen, tu sua viec da khai bao | 16/08 |

`dieu_phoi.py` chay ca 5 nhu tien trinh con, ngan sach CPU, lease + mutex,
tu khoi dong lai. `bang_dieu_khien.py` la man hinh doc trong 60 giay.

## `ds/` — kho DeepSeek (git rieng)
`datalake_lib` (parquet -> npy mmap) · `primitives` (thu vien nguyen thuy nhan qua)
· `probes` (8 phep do cau truc thi truong) · `schemas` (card + may trang thai)
· `quantlab` gates G0-G7 · `mimic` (dung nguoc chien luoc tu so lenh)
· `orchestrator` · `ledgers` · `generators` · `forward`.

## Da nghi huu — DUNG CHAY
`nghi_huu/` 8 bo dieu phoi cu + tru cu · `nghi_huu/vun_20260830/` 26 script mot lan
· `archive/` log cu · `bo_nao.py`, `lab.py`, `hang_doi.py` la he TRUOC 15/08.
