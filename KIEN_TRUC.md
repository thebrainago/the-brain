# KIEN TRUC HE THONG — sinh tu ma nguon

*2026-09-18 18:35 · 535 file `.py` · 199 tren duong chay · 9 lop nhan · sinh boi `python -m nhan.kien_truc --ghi` (hoac `b kien-truc`)*

**Dung sua tay.** Vai tro o day doc tu docstring dong dau cua chinh
module; sua mo ta thi sua trong file `.py`, roi chay lai lenh tren.
Nguon cau truc goc van la `Desktop/hethong.txt` (LUAT SO 0) — file nay
khong thay the no, no chi cho thay CAI DA XAY toi dau so voi so do do.

## 0. Thu muc — cai gi nam o dau

So file va MB o day DO THAT tren dia luc chay; vai tro thi viet tay
(`THU_MUC_GOC` / `THU_MUC_LAB` trong `nhan/kien_truc.py`). Cache va
`.git` khong dem.

### `Research SP500/` — goc du an

| Thu muc | File | MB | Vai tro |
|---|---:|---:|---|
| `lab/` | 12898 | 3718 | **The Brain** — toan bo he 24/7 (tru + nhan + cua vao). Moi thu con lai o goc la Phase 1 (SP500), da dong. |
| `ds/` | 1418 | 62 | Ho so giao viec cho agent ngoai (DeepSeek). Git rieng, gop vao 30/08. |
| `nap_tay/` | 1040 | 8 | Kho NAP TAY: repo github + file chu du an tu tha vao. Nguyen lieu tho, Seeker doc tu day. |
| `reports/` | 1016 | 1465 | Bao cao Phase 1 SP500 (co truoc `lab/reports`). |
| `co_che_ds/` | 51 | 0 | Co che do DeepSeek viet ra, cho kiem dinh. |
| `V6_DONG_GOI/` | 22 | 1 | Ban dong goi he V6 de chay that (bat/ps1 + code). |
| `output_multi_indicator_us500cash/` | 20 | 1 | Ket qua quet indicator_master tren us500cash. |
| `so_do/` | 11 | 1 | So do he thong dang html/svg/png. |
| `data/` | 1 | 0 | Du lieu goc Phase 1 (co tuc do). |
| `ea/` | 1 | 0 | EA MQL5 xuat ra de chay MT5 (V7_SP500). |
| `output_multi_indicator/` | 0 | 0 | Ket qua quet indicator_master (rong). |

### `lab/` — The Brain

| Thu muc | File | MB | Vai tro |
|---|---:|---:|---|
| `.browser_darwinex/` | 10429 | 1918 | Ho so trinh duyet RIENG cua Seeker, dang chay. |
| `reports/` | 736 | 91 | **Dau ra chinh** — ket qua may sinh (json/csv) cua kiem dinh. |
| `nhat_ky/` | 501 | 1 | Ban giao song + log theo phien. |
| `downloaded_codes/` | 317 | 5 | File Seeker tai ve (github/mql5/myfxbook/tradingview/transcripts). |
| `nhan/` | 133 | 2 | **Lop nhan** — module thu vien, tang duoi cua moi tru. Xem muc 3. |
| `data/` | 113 | 75 | Du lieu gia da nap (csv). |
| `nghi_huu/` | 56 | 0 | Module DA NGHI HUU, giu lai de tra cuu — khong nam tren duong chay. |
| `quant/` | 37 | 15 | Lane nghien cuu Quantlab V2 (thu_vien/pseud + ket qua). |
| `config/` | 35 | 10 | Cau hinh: api_keys, chi_phi_do, co_che_dsl... |
| `archive/` | 23 | 0 | Script/anh chup cu cat di. |
| `_luu_tru/` | 20 | 0 | Script cu cat di. Phan lon muc 4.1 nam o day. |
| `browser_backup_20260821/` | 18 | 0 | Ban sao ho so trinh duyet Seeker (21/08). |
| `qwen/` | 16 | 0 | Bang viec + vong chay tu dong cua qwen — cua vao thu 4. |
| `tru/` | 7 | 0 | **Bay tru** — Seeker/Quantlab/Evolution/Banker/Finder/Nghi. Tang tren. |
| `roles/` | 4 | 0 | Mo ta vai tro cho agent (BANKER/CHUNG/QUANTLAB/SEEKER). |
| `tai_lieu/` | 3 | 0 | Dac ta viet tay (PMG, SLOT_TESTER). |
| `data_khung/` | 1 | 1 | Du lieu gia theo khung, dang parquet. |
| `prompts/` | 1 | 0 | Prompt cac vai. |
| `ma_tai_ve/` | 0 | 0 | Cho ma tai ve (rong). |

**Kho o goc `lab/`:** `nao.db` 1595 MB · `thu_vien.db` 2 MB

## 1. Cua vao — bon duong chay that

Module khong duoc goi tu mot trong cac duong nay thi *bang khong co*
(luat L7, `LUAT_GIAM_SAT.md`). Day la ly do phan lon cong cu bi bo quen.

- **`b.py`** — lenh nguoi go — ~80 lenh con
- **`dieu_phoi.py`** — nam tru chay 24/7
- **`day_viec.py`** — hang doi viec xay, chay tuan tu
- **`qwen/NHIEM_VU.json`** — bang viec qwen tu chay
- **`BAN_GIAO.py`** — chot phien, ghi ban giao

## 2. Tru — so do cua chu du an

### SEEKER

TRU SEEKER. Phong thu thap thong tin va kien thuc 24/7.

*2647 dong · goi thang 17 module nhan*

> `bien_dich_ung_vien` · `cau_browser` · `dns_vuot` · `doc_trinh_duyet` · `du_lieu` · `hop_dong` · `ma_nguon` · `mau` · `ngu_phap` · `nguon_bai_viet` · `san_cong_cu` · `so` · `thu_hoi_thanh_phan` · `toan_van` · `tri_tue` · `tu_khoa_da_ngon_ngu` · `vuon_nguon`

### QUANTLAB

Quantlab V2: two isolated research lanes sharing only validated primitives.

*1806 dong · goi thang 18 module nhan*

> `bai_hoc` · `canary` · `chi_phi` · `cong` · `danh_muc` · `do_luc` · `do_luong` · `du_lieu` · `gop_lop` · `mau` · `mo_phong` · `nen` · `ngu_phap` · `pham_vi` · `quant_plan` · `sang_loc` · `so` · `vuon_nguon`

### EVOLUTION

TRU EVOLUTION. Giam sat, nhin ra van de, tu cai tien.

*1393 dong · goi thang 8 module nhan*

> `bai_hoc` · `cong` · `do_tai_nguyen` · `ket_qua_hoat_dong` · `san_cong_cu` · `so` · `thu_hoi_thanh_phan` · `tri_tue`

### BANKER

TRU BANKER. Vi mo cap nhat lien tuc + phan tich sat sao.

*550 dong · goi thang 1 module nhan*

> `so`

### FINDER

TRU FINDER. Tim giai phap CONG NGHE de nang cap ha tang.

*442 dong · goi thang 2 module nhan*

> `san_cong_cu` · `so`

### NGHI

TRU NGHI. Bien thu doc duoc thanh thu kiem dinh duoc, roi HOC TU KET QUA.

*450 dong · goi thang 6 module nhan*

> `du_lieu` · `ket_qua_hoat_dong` · `mau` · `ngu_phap` · `so` · `tri_tue`

## 3. Lop nhan — 132 module thu vien

### SO & HOP DONG — 10 module

*Nguon su that chung. Moi tru doc va ghi qua day, khong tu giu so rieng.*

- **`anh_chup`** (203 dong, 3 noi goi) — GHIM BAN DU LIEU de mot ket qua tai lap duoc.
- **`bai_hoc`** (199 dong, 7 noi goi) — SO BAI HOC: he tu tra loi duoc "cai nay da thu chua".
- **`bang_he`** (331 dong, 4 noi goi) — BANG CAC HE DA QUA CONG. Mat xich cuoi cung, va no dang thieu.
- **`bi_mat`** (115 dong, 7 noi goi) — MOT CUA doc khoa. Khong module nao tu mo file khoa.
- **`duong_dan`** (159 dong, 7 noi goi) — MOT CHO duy nhat giai cac duong dan phu thuoc MAY.
- **`hop_dong`** (618 dong, 9 noi goi) — Versioned hand-off contract from SEEKER to downstream consumers.
- **`ket_qua_hoat_dong`** (79 dong, 4 noi goi) — Quy tac doc ket qua dang hoat dong cua THE BRAIN.
- **`pham_vi`** (305 dong, 13 noi goi) — Pham vi ap dung cua tung ho co che - va phep thu phan chung di kem.
- **`quant_plan`** (368 dong, 3 noi goi) — Immutable preregistration contract for the two Quantlab research lanes.
- **`so`** (925 dong, 114 noi goi) — SO CAI CUA THE BRAIN. Mot nguon su that duy nhat cho ca 4 tru.

### THU THAP — Seeker di lay ve — 19 module

*Di ra ngoai lay tai lieu ve. Do dau vao, khong do ket qua.*

- **`cau_browser`** (232 dong, 2 noi goi) — CAU NOI: "The Eye of Seeker" (browser/) -> The Brain.
- **`chi_tieu`** (223 dong, 3 noi goi) — CHI TIEU NGAY va CHIA THOI LUONG THEO NEN TANG.
- **`dns_vuot`** (119 dong, 5 noi goi) — VUOT DNS BI DAU DOC, giu nguyen SNI va TLS that.
- **`doc_song_song`** (134 dong, 7 noi goi) — DOC TOAN VAN song song, uu tien nguon co SUAT CAO.
- **`doc_trinh_duyet`** (146 dong, 7 noi goi) — DOC BANG TRINH DUYET DANG MO (CDP) cho SEEKER.
- **`duyet_nguoi`** (147 dong, 5 noi goi) — DUYET NHU NGUOI: giu phien, co Referer, nhip khong deu.
- **`hang_doi`** (223 dong, 2 noi goi) — HANG DOI VIEC cua QUANTLAB. Chong nghen, chay song song duoc.
- **`kham_pha_nguon`** (228 dong, 4 noi goi) — SO DANG KY CAC KENH TU TIM NGUON MOI.
- **`nen_tang`** (278 dong, 1 noi goi) — MA NGUON CHIEN LUOC TU CAC NEN TANG GIAO DICH KHAC.
- **`nguon_bai_viet`** (634 dong, 4 noi goi) — NGUON VAN XUOI: bai viet chien luoc, lay qua RSS/Atom.
- **`nguon_tinix`** (209 dong, 2 noi goi) — repo.tinix.ai -> ung vien cong cu cho FINDER.
- **`san_cong_cu`** (1600 dong, 10 noi goi) — DI SAN CONG CU CO SAN, thay vi tu viet lai tu dau.
- **`telegram`** (669 dong, 3 noi goi) — TELEGRAM -> tai_lieu / noi_dung.
- **`theo_doi`** (261 dong, 2 noi goi) — THEO KENH DA CHON, doc lai theo LICH do duoc.
- **`tien_ich_xet`** (153 dong, 2 noi goi) — 58 FILE "TIEN ICH" DANG BI BO: CAI NAO DANG LAY VE?
- **`toan_van`** (499 dong, 7 noi goi) — TANG DOC. Lay NOI DUNG THAT chu khong phai dong tieu de.
- **`tu_dang_nhap`** (72 dong, 1 noi goi) — TU DANG NHAP cac site co san pass trong config/tai_khoan.json
- **`tu_khoa_da_ngon_ngu`** (264 dong, 3 noi goi) — MOT KHAI NIEM, MUOI BON THU TIENG.
- **`vuon_nguon`** (685 dong, 6 noi goi) — VUON NGUON: do suat, chia ngan sach, tu tim nguon moi.

### BOC TACH — tai lieu thanh co che — 19 module

*Khau hep nhat cua he: van xuoi/ma nguon/anh/video -> khai bao kiem dinh duoc.*

- **`bien_dich_ung_vien`** (483 dong, 5 noi goi) — Bien dich tai lieu da thu thap thanh CandidateArtifact co dan nguon.
- **`boc_llm`** (567 dong, 20 noi goi) — BOC CO CHE bang LLM, ban NANG SUAT.
- **`boc_ma_llm`** (651 dong, 8 noi goi) — BOC CO CHE tu ma nguon EA: regex khoanh vung, LLM dich.
- **`doc_anh`** (213 dong, 2 noi goi) — ANH -> VAN BAN, cho anh chup man hinh va PDF dang anh quet.
- **`doc_chi_bao`** (410 dong, 5 noi goi) — BOC CO CHE TU FILE CHI BAO (190 file, lop chua ai dong toi).
- **`doc_hieu`** (1151 dong, 12 noi goi) — DOC VAN XUOI THANH CO CHE KIEM DINH DUOC.
- **`doc_ma`** (1038 dong, 10 noi goi) — DOC MA NGUON THANH NHIEU KHAI BAO CO CHE.
- **`doc_pdf`** (258 dong, 2 noi goi) — PDF -> van ban, co OCR cho trang la ANH.
- **`doc_video`** (215 dong, 5 noi goi) — VIDEO -> VAN BAN, de video di chung mot duong voi van xuoi.
- **`doc_video_cuc_bo`** (199 dong, 3 noi goi ⚠MO COI) — VIDEO TREN DIA -> VAN BAN. Khau con thieu cua Seeker.
- **`go_html`** (219 dong, 5 noi goi) — KHAU CON THIEU giua THU THAP va BOC: go trang HTML ra van ban.
- **`ma_nguon`** (684 dong, 8 noi goi) — MA NGUON EA / CHI BAO -> CodeArtifact.
- **`mau`** (540 dong, 42 noi goi) — THU VIEN MAU CHIEN LUOC (template + tham so).
- **`mimic_cau_noi`** (186 dong, 3 noi goi) — NOI `ds/mimic` VAO DUONG CHAY CHINH.
- **`ngu_phap`** (2340 dong, 129 noi goi) — NGU PHAP CO CHE. Cach duy nhat kien thuc moi di vao day chuyen.
- **`phan_loai_ma`** (298 dong, 7 noi goi) — CHIA KHO MA NGUON THANH BON LAN, TRUOC KHI BOC.
- **`quan_tri`** (303 dong, 4 noi goi) — BOC CO CHE QUAN TRI VI THE tu ma nguon EA.
- **`quan_tri_llm`** (262 dong, 2 noi goi) — ANH XA INPUT -> NUT VAN khi bang REGEX khong doc noi ten.
- **`uu_tien`** (457 dong, 5 noi goi) — CUA MOT BUOC cho chu du an: mot link/file -> co che, ngay trong phien.

### DU LIEU & TAI SAN — 19 module

*Nap gia tu chinh cong cu se giao dich, va do dac tinh cua tung ma.*

- **`chi_phi`** (985 dong, 62 noi goi) — MO HINH CHI PHI DO DUOC, khong phai go tay.
- **`dem_nen`** (171 dong, 4 noi goi) — BO DEM NEN: mot tai san co hinh dang nen nhu the nao.
- **`dia`** (87 dong, 5 noi goi) — CONG DIA DAY. Khong phai mot bao cao, mot CONG.
- **`doi_khung`** (347 dong, 5 noi goi) — CHUYEN MOT CO CHE SANG KHUNG KHAC MA NO VAN LA CHINH NO.
- **`du_lieu`** (1384 dong, 115 noi goi) — NAP DU LIEU TU CHINH CONG CU SE GIAO DICH.
- **`gop_wal`** (95 dong, 4 noi goi) — GOP `nao.db-wal` VAO DB. Cai phanh cho mot kieu day dia lang le.
- **`ho_so_mua_vu`** (373 dong, 5 noi goi) — TINH MUA VU va ENTRY-TIME cua mot tai san.
- **`ho_so_song`** (353 dong, 6 noi goi) — DAC TINH SONG va MOC MAGNETIC cua mot tai san.
- **`ho_so_symbol`** (189 dong, 11 noi goi) — HO SO TAI SAN: tra loi "co gia thuyet nay thi thu tren cai gi".
- **`ho_so_tai_san`** (880 dong, 3 noi goi) — MOT CUA cho toan bo dac diem tai san da do duoc.
- **`ho_so_tuong_quan`** (339 dong, 7 noi goi) — TUONG QUAN LIEN MA va DO ON DINH cua no.
- **`nen`** (115 dong, 3 noi goi) — DOI CACH DUNG NEN, NHUNG CHI CHO TIN HIEU.
- **`quy_doi_tham_so`** (171 dong, 3 noi goi) — DOI TAI SAN THI THAM SO PHAI DOI THEO.
- **`quy_luat_song`** (336 dong, 3 noi goi) — TU TIM QUY LUAT trong chuoi song, da khung.
- **`tai_tro`** (143 dong, 2 noi goi) — CARRY cua mot vi the chi so giu qua dem.
- **`ten_ma`** (238 dong, 5 noi goi) — MOT nguon su that cho cau hoi "ma nay CO tren terminal khong".
- **`thang_gia`** (358 dong, 4 noi goi) — NGUONG TINH BANG DON VI GIA la mot loi CAM LANG.
- **`tinh_cach`** (188 dong, 3 noi goi) — DO TINH CACH TAI SAN bang so hoc: hoi quy hay xu huong?
- **`tinh_cach_chieu`** (229 dong, 2 noi goi) — TINH CACH TAI SAN -> CHIEU DAT LUOI, BUOC, CHAN TROI.

### SINH GIA THUYET — 11 module

*Bon luong sinh: noi sinh, ngoai sinh, suy nguoc tu dau chan, to hop.*

- **`chuyen_he`** (210 dong, 2 noi goi) — MANG MOT HE SANG CHO KHAC MA NO VAN LA CHINH NO.
- **`da_thoi_dai`** (172 dong, 6 noi goi) — CHAY MOT CO CHE TREN MOI CUA SO DU LIEU SACH, khong chi mot.
- **`dau_chan`** (174 dong, 6 noi goi) — LUAN NGUOC KIEU CHIEN LUOC tu DAU CHAN CONG KHAI.
- **`gop_lop`** (635 dong, 3 noi goi) — GOP LOP - kiem dinh MOT co che tren CA MOT LOP TAI SAN, ton MOT suat FDR.
- **`luan_dau_chan`** (168 dong, 2 noi goi) — 400 HO SO SIGNAL -> KIEU CHIEN LUOC. Noi hai manh mo coi.
- **`ngoai_sinh`** (175 dong, 3 noi goi) — LUONG NGOAI SINH. Ke thua tu ben ngoai, roi CHINH cho tai san moi.
- **`noi_sinh`** (561 dong, 6 noi goi) — LUONG 3. Tu sinh co che tu CHINH LICH SU cua ma, khong doi nguon ngoai.
- **`suy_nguoc`** (416 dong, 5 noi goi) — SUY NGUOC: truoc mot cu di manh thi CO DAU HIEU GI.
- **`thu_hoi_thanh_phan`** (429 dong, 7 noi goi) — GIU LAI PHAN DUNG DUOC CUA MOT HE THONG BI LOAI.
- **`tin_hieu_mql5`** (292 dong, 3 noi goi) — DO NGUOC PHONG CACH DANH tu tai khoan CO LAI cong khai.
- **`to_hop`** (764 dong, 7 noi goi) — TO HOP DA CAP x DA KHUNG x DA QUAN LI x DA THONG SO.

### QUAN TRI VI THE — 12 module

*Ho co che THU HAI. 262 co che dau la tin hieu VAO; day la nua con lai.*

- **`bien_don_bay`** (192 dong, 22 noi goi) — BIEN DON BAY. Don bay bao nhieu, va no tra ve duoc gi.
- **`chuoi_quan_tri`** (248 dong, 4 noi goi) — NOI BA MANH QUAN TRI VI THE THANH MOT DUONG CHAY.
- **`dap_quan_tri`** (385 dong, 11 noi goi) — DAP MOT BO LUAT QUAN TRI LEN MOT TIN HIEU VAO BAT KY.
- **`de_quan_tri`** (204 dong, 4 noi goi) — CHEN bo quan tri cua ta vao MOT EA NGOAI, roi do bat/tat.
- **`luoi`** (351 dong, 2 noi goi ⚠MO COI) — MO PHONG LUOI/DCA CO TRACH NHIEM, dung duoc lai cho moi cap.
- **`pmg`** (345 dong, 5 noi goi) — POSITION MANAGEMENT GRID ENGINE. Ho quan li lenh KHONG CO TIN HIEU VAO.
- **`pmg_engine`** (688 dong, 4 noi goi) — MO PHONG RO cua PMG tren bar. Cong G2 cua dac ta.
- **`pmg_g0`** (448 dong, 4 noi goi) — CONG G0 cua PMG. Do TINH CHAT QUA TRINH GIA truoc khi viet engine.
- **`pmg_quet`** (419 dong, 4 noi goi) — PHEU CUA PMG: G1 -> G2 -> G3, va SO DEM PHEP THU.
- **`quan_tri_dsl`** (348 dong, 10 noi goi) — NGON NGU KHAI BAO CHO QUAN TRI VI THE.
- **`quan_tri_nhieu`** (446 dong, 4 noi goi) — QUAN TRI LENH voi NHIEU VI THE cung luc, chay bang Python.
- **`vao_lenh`** (562 dong, 9 noi goi) — CAU TRUC VAO LENH nhieu chan. Nua con thieu cua module quan tri.

### KIEM DINH & CONG — 11 module

*Noi mot gia thuyet duoc phep doi doi. Hai cong: co that khong, va co ra tien khong.*

- **`cham_diem`** (165 dong, 2 noi goi) — BANG DIEM THUC TE. Ra tien bao nhieu, rui ro the nao.
- **`cong`** (979 dong, 25 noi goi) — CONG PASS. Noi duy nhat mot gia thuyet duoc phep doi doi.
- **`cong_ra_tien`** (245 dong, 5 noi goi) — CONG THU HAI. Hoi "co ra tien khong", khong hoi "co that khong".
- **`danh_muc`** (343 dong, 3 noi goi) — TANG 3 - tinh von va ket hop cac gia thuyet da qua cong.
- **`do_luc`** (559 dong, 16 noi goi) — Do LUC cua cong: edge nho nhat ma he con nhin thay duoc.
- **`do_luong`** (145 dong, 13 noi goi) — CHI SO + ALPHA SO VOI MUA-GIU.
- **`loc_co_che`** (389 dong, 12 noi goi) — BO LOC TINH, CHAY TRUOC PHEU V0-V3.
- **`mo_phong`** (325 dong, 45 noi goi) — ENGINE BACKTEST. Mot cua duy nhat de bien tin hieu thanh tien.
- **`nha_may_null`** (336 dong, 6 noi goi) — NHA MAY NULL - sinh chuoi gia de hieu chuan cong.
- **`sang_loc`** (643 dong, 10 noi goi) — PHEU BON VONG: V0 van tay -> V1 re -> V2 kinh te -> V3 phan chung.
- **`suy_giam`** (116 dong, 2 noi goi) — HE DANG CHAY CO CON GIONG CAI DA KIEM DINH KHONG.

### MT5 / TESTER — do that — 12 module

*Quy tac cua chu du an: MT5 tester TRUOC, Python SAU.*

- **`chay_that`** (531 dong, 2 noi goi) — DUONG TU MOT HE DA QUA TESTER RA TAI KHOAN THAT.
- **`dang_nhap_mt5`** (269 dong, 2 noi goi) — TU DANG NHAP MT5, de tester chay duoc khi khong co nguoi.
- **`dich_mq5`** (1158 dong, 15 noi goi) — DICH KHAI BAO DSL SANG MQL5 DE TESTER LAM TRONG TAI.
- **`dich_mq5_ghep`** (291 dong, 8 noi goi) — MOT EA CHAY NHIEU CO CHE CUNG LUC (ghep he thong).
- **`dich_mq5_qtvt`** (625 dong, 6 noi goi) — DICH KHAI BAO QUAN TRI VI THE SANG MQL5. Hai duong ra.
- **`dich_mq5_quan_tri`** (482 dong, 2 noi goi) — EA GHEP CO QUAN TRI VI THE.
- **`doc_lenh_tester`** (240 dong, 2 noi goi) — Doc DANH SACH LENH tu bao cao MT5 Strategy Tester.
- **`khoa_tester`** (211 dong, 22 noi goi) — MOT CUA CO KHOA cho `terminal64.exe`.
- **`passview`** (311 dong, 2 noi goi) — TAI KHOAN XEM (investor password) -> LICH SU LENH THAT.
- **`san_sang_vps`** (284 dong, 2 noi goi) — HE DA CHUYEN LEN VPS DUOC CHUA.
- **`so_lenh`** (218 dong, 3 noi goi) — SO LENH PAPER: cho mot he DA QUA CONG di tiep, khong dung o nhan.
- **`tai_khoan_nen_tang`** (289 dong, 2 noi goi) — MOT CHO BIET he dang co tai khoan nao, thieu cai gi.

### DIEU HANH & GIAM SAT — 16 module

*Giu he chay 24/7 va tu thay duoc minh dang hong cho nao.*

- **`ban_do`** (409 dong, 7 noi goi) — SINH ban do he thong TU CHINH MA NGUON.
- **`canary`** (236 dong, 6 noi goi) — CHIM HOANG MAI. Gac chinh cai engine dang duoc dung.
- **`day_chuyen`** (157 dong, 4 noi goi) — NOI CA DAY CHUYEN 03/09/2026 THANH MOT CHO GOI.
- **`day_chuyen_quantlab`** (152 dong, 2 noi goi) — QUY TRINH CHUAN: ma nguon -> co che -> he thong.
- **`do_im_lang`** (207 dong, 3 noi goi) — TIM TANG NAO DANG CAM MA KHONG AI BIET.
- **`do_tai_nguyen`** (94 dong, 3 noi goi) — DO CHI PHI VAN HANH, khong phai chi phi giao dich.
- **`don_mo_coi`** (193 dong, 5 noi goi) — Tim va don TIEN TRINH MO COI dang an CPU.
- **`evo`** (773 dong, 7 noi goi) — THE EVO: giam sat hieu suat tung module, cat nghia, de xuat.
- **`han_muc`** (151 dong, 5 noi goi) — KILL-SWITCH va TRAN. Cai phanh, khong phai cai ga.
- **`kien_truc`** (468 dong, 3 noi goi) — SINH SO DO KIEN TRUC: module nao, VAI TRO gi, thuoc LOP nao.
- **`mach`** (385 dong, 2 noi goi) — MACH DAP CUA DUONG ONG. Canary cho tung chang, khong chi cho engine.
- **`muc_tieu`** (421 dong, 8 noi goi) — CHIEN DICH THEO MUC TIEU. Day moi la "The Brain + QUANTLAB".
- **`ngan_sach`** (464 dong, 15 noi goi) — SO NGAN SACH TAI NGUYEN. Cua vao chung cho moi viec nang.
- **`tran_cpu`** (159 dong, 5 noi goi) — MOT chO khai tran CPU, va moi viec nang deu tu ha theo no.
- **`tri_tue`** (380 dong, 14 noi goi) — Cau noi OpenAI tuy chon cho tien trinh nen 24/7.
- **`vong_day_du`** (476 dong, 3 noi goi) — MOT LENH chay CA BA TRU theo dung so do cua chu du an.

### CHUA XEP LOP — 3 module

Module moi chua ai xep vao tang nao. Day la muc **can doc truoc
khi lap ke hoach**: mot module khong co tang thi khong ai biet no
thuoc ve ai, va no se bi xay lai duoi mot cai ten khac.

- **`ghi_an_toan`** (178 dong, 5 noi goi) — SUA MOT FILE JSON MA KHONG MAT THAY DOI CUA NGUOI KHAC.
- **`ho_so_he`** (1156 dong, 1 noi goi) — MOT FILE DUY NHAT dua cho mot AI KHONG CO DIA.
- **`slot_tester`** (293 dong, 2 noi goi) — NHIEU LAN TESTER, moi lan mot terminal RIENG.

## 4. No kien truc — cho de lam ke hoach

### 4.1 Khong tu khai vai tro — 15 file

Khong co docstring dong dau, nen khong vao duoc ban do vai tro nao.
Sua mot dong docstring la het no.

- `_luu_tru/bao_cao_hen_gio.py` (46 dong)
- `_luu_tru/chien_luoc_mr_tf.py` (52 dong)
- `_luu_tru/chien_luoc_trend.py` (58 dong)
- `_luu_tru/dang_ky_alphavantage.py` (106 dong)
- `_luu_tru/doc_for_ds.py` (21 dong)
- `_luu_tru/gen_kiem_ke.py` (144 dong)
- `_luu_tru/lay_api_darwinex.py` (101 dong)
- `_luu_tru/nap_darwinex_api.py` (114 dong)
- `_luu_tru/placebo_d1.py` (53 dong)
- `_luu_tru/tele_gate.py` (83 dong)
- `_luu_tru/xac_nhan_d1.py` (53 dong)
- `_placebo_da_ma.py` (18 dong)
- `_quet_song_song.py` (51 dong)
- `_tmp_quet.py` (12 dong)
- `lay_du_lieu.py` (64 dong)

### 4.2 Goc `lab/` — 351 file roi

**Ba loai khac han nhau — tron chung lai thi con so vo nghia.** Ban sinh
dau tien cua chinh file nay bao "231 file phai don", trong khi 146 trong
so do la `test_*.py`: pytest TIM chung o goc, chung o dung cho roi.

| Loai | So | Phai lam gi |
|---|---|---|
| `test_*.py` + `conftest.py` | 155 | khong lam gi — dung cho |
| `_*.py` chay tay mot lan | 131 | mo coi la DUNG BAN CHAT — de yen hoac xoa |
| **con lai** | **65** | **day moi la no**: len `nhan/`, hoac doi ten `_*.py`, hoac xoa |

65 file thuoc nhom thu ba:

- `BAN_GIAO.py` — MOT LENH de vao phien: in ban ban giao + trang thai SONG cua he.
- `KET_PHIEN.py` — KET PHIEN — mot lenh chot ngay hom nay de mai vao lam ngay duoc.
- `b.py` — MOT cua vao cho moi viec hang ngay cua THE BRAIN.
- `ban_giao_song.py` — SO BAN GIAO SONG, ghi lien tuc chu khong doi cuoi phien.
- `bang_dieu_khien.py` — MOT MAN HINH DUY NHAT de biet he dang the nao.
- `bo_nao.py` — Orchestrator THE BRAIN: bang cong viec + dieu phoi 8 vai.
- `cham_lai_the_he.py` — CHAM LAI moi gia thuyet da dang ky duoi THE HE CONG hien tai.
- `chay_bang_mde.py` — Chay ban NGHIEM THU cua nha may luc + nha may null, ra BANG MDE.
- `chay_bench_quan_tri.py` — DUA 11 HO QUAN TRI VI THE RA MT5 TESTER.
- `chay_test_tung_me.py` — chay CA bo test bang NHIEU tien trinh pytest ngan.
- `chay_tester_kho.py` — DUA CA KHO CO CHE RA MT5 TESTER.
- `chay_tester_z5.py` — DUA HE DA PASS RA TICK THAT.
- `chien_luoc_mr.py` ⚠MO COI — CHIEN LUOC HOI QUY ban tho (thang 8) - giu lam moc doi chieu.
- `chup_darwinex.py` ⚠MO COI — Chup man hinh trang Darwinex bang profile da dang nhap (dung cho screen-read).
- `chuyen_giao.py` — Sao luu + ban giao THE BRAIN (chay cuoi moi phien lam viec).
- `cross_pair_quet.py` ⚠MO COI — QUET M1 local: mo phong he grid LuoiDoiXung/mo_phong_v2
- `dang_nhap.py` — AUTO-LOGIN: dang nhap site/san tu dong qua Chrome CDP.
- `darwinex_ocr.py` ⚠MO COI — LUỒNG A - NGUỒN DARWINEX (module mới, chỉ tạo file).
- `day_viec.py` — HANG DOI VIEC XAY, chay TUAN TU va LIEN TUC.
- `dieu_khien_xa.py` — nghe lenh Telegram, KHONG ton mot token nao cua agent.
- `dieu_phoi.py` — Control plane 24/7 cho nam tru hien hanh cua THE BRAIN.
- `do_on_dinh.py` — CAO NGUYEN hay CAI GAI? Do HINH DANG cua mot edge.
- `doc_bang_trinh_duyet.py` ⚠MO COI — Doc trang bang TRINH DUYET THAT (Playwright/Chromium)
- `doc_cdp.py` ⚠MO COI — Doc X/TikTok/Facebook qua CDP tren TRINH DUYET DA DANG NHAP
- `doc_email.py` ⚠MO COI — DOC EMAIL qua IMAP: lay ma xac minh / thu tu nguon da dang ky.
- `doc_web_moi.py` ⚠MO COI — DOC WEB BEN: thu requests truoc, neu loi hay noi dung rong
- `ea_tu_dong.py` ⚠MO COI — TAI EA THAT -> BIEN DICH -> CHAY STRATEGY TESTER.
- `fl_cheo.py` ⚠MO COI — FOLLOW CHEO (cross-follow): tu 1 nguon / tai khoan chat luong,
- `giam_sat_dieu_phoi.py` — Watchdog ngoai tien trinh cho control plane.
- `hang_doi.py` — Dong bo VPS <-> may nha qua THU MUC CHUNG, khong lan viec nhau
- `hinh_dang_vs_null.py` — HINH DANG cua edge co phan biet duoc voi NGAU NHIEN khong?
- `ichimoku_cross.py` ⚠MO COI — QUANTLAB: Ichimoku cross tren du lieu M1 local (khong can mang).
- `keywords_nguon.py` — NGAN HANG TU KHOA dung chung cho Seeker.
- `khao_sat_daily_zone.py` ⚠MO COI — Quet tham so TP cho co che #1, do PF + Drawdown.
- `lab.py` ⚠MO COI — Phong lab quet he thong giao dich 24/7, DeepSeek lam bo nao
- `lay_du_lieu.py` ⚠MO COI — _(chua tu khai vai tro)_
- `loc_chat_luong.py` — SEEKER: BO LOC CHAT LUONG noi dung.
- `mo_chrome_cdp.py` — Mo Chrome da dang nhap (.browser_darwinex) kem CDP 9224.
- `mt5_chay_ichimoku.py` ⚠MO COI — Chay EA_IchimokuCross tren MT5 Strategy Tester.
- `mt5_worker.py` — Chay MT5 Strategy Tester THAT (worker chung cho moi vai 'test').
- `nap_truoc_mde.py` — Nap truoc BANG MDE cho ca be mat, thay vi do lazy giua vong quet.
- `nguon_code.py` ⚠MO COI — SEEKER: NGUON CODE (MQL5 + Pine) tu GitHub (API cong khai).
- `nguon_dien_dan.py` ⚠MO COI — NGUON DIEN DAN (khong can dang nhap): futures.io, Trade2Win,
- `nguon_kham_pha.py` ⚠MO COI — TU KHAM PHA NGUON (SEENER): tu sinh keyword, tu do
- `nguon_reddit.py` ⚠MO COI — Nguon Reddit cho SEEKNER: quet cac subreddit trading
- `nguon_reddit_sim.py` ⚠MO COI — REDDIT qua trinh duyet that (Playwright), vi JSON API
- `nguon_telegram.py` ⚠MO COI — Nguon Telegram cho SEEKNER: doc tin tu cac kenh/channel
- `nguon_youtube.py` ⚠MO COI — Nguon YouTube cho SEEKNER: tim kien thuc / chien luoc /
- `nhip_song.py` — Mot cho duy nhat doc TRANG THAI SONG cua he — dung chung cho vao/ket phien.
- `quant_sweep.py` ⚠MO COI — QUANTLAB PARAM GRID da nhan (ProcessPoolExecutor).
- `quet_be_mat.py` — Quet TANG KHAM PHA tren toan be mat: moi co che x moi tai san, khung D1.
- `quet_loi_ra.py` ⚠MO COI — MOT TIN HIEU CHUA PHAI MOT CHIEN LUOC.
- `rem_via_tele.py` ⚠MO COI — Cau noi THE BRAIN qua Telegram.
- `run_mt5_flag.py` ⚠MO COI — tick-test MT5 that cho he flagship LuoiDoiXung (EURCAD, MOC).
- `seeker_cong_dong.py` ⚠MO COI — Tang cong dong cua SEEKNER: tim CO NHOM nguoi chia se,
- `seeker_deep.py` ⚠MO COI — SEEPER . sat: "bieu ten -> dao tai lieu cong khai da ngon ngu
- `seeker_theo_doi.py` ⚠MO COI — SEEKER: theo doi ca nhan / nhom chat luong.
- `simulator_nguoi.py` ⚠MO COI — BO MO PHONG NGUOI DUNG TREN WEB.
- `telethon_ban.py` — Nguon Telegram qua TAI KHOAN THAT (Telethon).
- `tinh_trang.py` — In tinh trang hien tai de biet dang lam viec toi dau.
- `toan_canh.py` — MOT MAN HINH cho biet he dang o dau — doc xong trong 30 giay.
- `toc_do.py` — Bo dem tan so quet (rate limiter) chong spam/block tung nguon.
- `tu_dang_ky.py` ⚠MO COI — QUY TRINH TAO TAI KHOAN TU DONG de lay du lieu.
- `tu_follow_join.py` ⚠MO COI — SEEKER TU FOLLOW + JOIN GROUP (kiem soat spam).
- `vao_web.py` ⚠MO COI — VAO WEB bang trinh duyet that (dang nhap, giu phien).

### 4.3 File tren 600 dong — 34 file

Khong phai loi, nhung la cho mot module dang lam nhieu hon mot viec.

- `tru/seeker.py` — 2647 dong
- `nhan/ngu_phap.py` — 2340 dong
- `tru/quantlab.py` — 1806 dong
- `nhan/san_cong_cu.py` — 1600 dong
- `tru/evolution.py` — 1393 dong
- `nhan/du_lieu.py` — 1384 dong
- `nhan/dich_mq5.py` — 1158 dong
- `nhan/ho_so_he.py` — 1156 dong
- `nhan/doc_hieu.py` — 1151 dong
- `dieu_phoi.py` — 1092 dong
- `nhan/doc_ma.py` — 1038 dong
- `b.py` — 1027 dong
- `nhan/chi_phi.py` — 985 dong
- `nhan/cong.py` — 979 dong
- `bo_nao.py` — 940 dong
- `nhan/so.py` — 925 dong
- `nhan/ho_so_tai_san.py` — 880 dong
- `test_san_cong_cu.py` — 830 dong
- `quant/thu_vien/pseud/tools/ohlc_anomaly_hypothesis_tool.py` — 782 dong
- `nhan/evo.py` — 773 dong
- `nhan/to_hop.py` — 764 dong
- `chay_tester_kho.py` — 689 dong
- `nhan/pmg_engine.py` — 688 dong
- `nhan/vuon_nguon.py` — 685 dong
- `nhan/ma_nguon.py` — 684 dong

### 4.4 Module trong goi nhung MO COI — 2

- `nhan/doc_video_cuc_bo.py` — VIDEO TREN DIA -> VAN BAN. Khau con thieu cua Seeker.
- `nhan/luoi.py` — MO PHONG LUOI/DCA CO TRACH NHIEM, dung duoc lai cho moi cap.

## 5. So tong

| Muc | So |
|---|---|
| File `.py` (bo `nhat_ky/ backups/ __pycache__/ ...`) | 535 |
| Tren duong chay | 199 |
| Module thu vien `nhan/` | 132 |
| — da xep lop | 129 |
| — chua xep lop | 3 |
| Tru `tru/` | 7 |
| File roi o goc `lab/` | 351 |
| — `test_*.py` (dung cho) | 155 |
| — script `_*.py` chay tay | 131 |
| — **con lai, la no that** | **65** |
| Khong tu khai vai tro | 15 |

