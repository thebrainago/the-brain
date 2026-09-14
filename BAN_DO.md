# BAN DO HE THONG — sinh tu ma nguon

*2026-09-14 19:22 · 489 file .py · 163 tren duong chay · **7 MO COI THAT** · 3 ha tang · 14 kho cu `quant/` · 168 script chay tay*

Sinh boi `python -m nhan.ban_do --ghi`. **Dung sua tay** - ban viet
tay ngay 30/08 da loi thoi 13 ngay va bo sot 11 module, va mot ban do
loi thoi lam nguoi doc dung lai thu da co.

## Ba tru theo so do cua chu du an

- **SEEKER** `tru/seeker.py` — TRU SEEKER. Phong thu thap thong tin va kien thuc 24/7.
- **QUANTLAB** `tru/quantlab.py` — Quantlab V2: two isolated research lanes sharing only validated primitives.
- **EVO** `tru/evolution.py` — TRU EVOLUTION. Giam sat, nhin ra van de, tu cai tien.

## MODULE MO COI — khong duong chay nao goi toi

Luat L7: *cong cu khong nam tren duong chay thi bang khong co*.
Day la module trong goi (`nhan/`, `tru/`, `qwen/`), khong phai script
chay tay - nen moi dong o day hoac (a) can noi vao mot cua vao,
hoac (b) la ha tang cho thu chua xay xong.

- `nhan/dang_nhap_mt5.py` — TU DANG NHAP MT5, de tester chay duoc khi khong co nguoi.
- `nhan/doc_anh.py` — ANH -> VAN BAN, cho anh chup man hinh va PDF dang anh quet.
- `nhan/doc_pdf.py` — PDF -> van ban, co OCR cho trang la ANH.
- `nhan/ho_so_tai_san.py` — MOT CUA cho toan bo dac diem tai san da do duoc.
- `nhan/quant_plan.py` — Immutable preregistration contract for the two Quantlab research lanes.
- `nhan/suy_giam.py` — HE DANG CHAY CO CON GIONG CAI DA KIEM DINH KHONG.
- `nhan/tu_dang_nhap.py` — TU DANG NHAP cac site co san pass trong config/tai_khoan.json

## Kho cu `quant/` — 14 file

Tu 12-15/08/2026, truoc lan tai cau truc lab. Viec dung voi chung
la XEM CO GI DANG LAY roi don di, khong phai noi vao duong chay.

`auto_kham_pha` · `chay_tat_ca` · `co_che_A_cung_cau_engulfing` · `co_che_B_ichimoku_chikou_di` · `co_che_C_ema_rsi` · `co_che_D_premium_choch` · `du_lieu` · `ket_hop_hoc` · `kiem_dinh` · `metrics` · `run_ohlc_anomaly_hypothesis` · `ohlc_anomaly_hypothesis_tool` · `tim_ichimoku_cross` · `tin_hieu`

## Ha tang cho script chay tay — 3 module

Khong cua vao nao goi THANG, nhung mot script chay tay co goi. Do la
thu vien hop le, khong phai lo hong - de chung chung voi muc tren thi
lai che mat dung cai can doc.

- `nhan/cong_ra_tien.py` — CONG THU HAI. Hoi "co ra tien khong", khong hoi "co that khong".
- `nhan/doc_video_cuc_bo.py` — VIDEO TREN DIA -> VAN BAN. Khau con thieu cua Seeker.
- `nhan/luoi.py` — MO PHONG LUOI/DCA CO TRACH NHIEM, dung duoc lai cho moi cap.

## Script chay tay (`_*.py` va file goc lab) — 168 file

Mo coi la DUNG ban chat: moi cai tra loi mot cau hoi cu the mot lan.
Liet ke gon de khong che mat muc tren.

`_audit_tru` · `_bo_doc_mu_o_dau` · `_boc_lai_toan_kho` · `_boc_lai_vung` · `_boc_video_khoa_hoc` · `_cao_mql5` · `_cao_mql5_sau` · `_chan_dd_holdout` · `_chay_go_html` · `_chien_dich_sp500` · `_cong_ra_tien_quet` · `_da_khung` · `_dang_ky_6_he` · `_dang_ky_github` · `_de_qt_ea_ngoai` · `_dien_co_che` · `_do_ma_mt5` · `_do_tap_trung_chang1` · `_do_thoi_gian_giu` · `_doc_boc_toan_luc` · `_doc_roi_boc` · `_ghep_h4` · `_ghep_he` · `_github_toan_luc` · `_gop_khong_chon` · `_hang_doi_toan_hang` · `_hieu_chuan_v6` · `_hinh_dang_audcad_rsi` · `_hinh_dang_song_sot` · `_kiem_cong_co_che` · `_kiem_tra_cuu` · `_lam_moi_mde` · `_linh_hoat` · `_luan_nguoc` · `_luoi_audcad` · `_luoi_audcad_chang2` · `_luoi_fx_song_bao_lau` · `_luong2_qwen` · `_ly_do_tu_choi` · `_ma_tran_ghep` · `_mo_xe_z5` · `_muc_tieu_20pc` · `_nap_viec_qwen` · `_nhap_bai_hoc` · `_noi_sinh_khop_rui_ro` · `_noi_sinh_xu_huong_chay` · `_placebo_da_ma` · `_placebo_ghep` · `_placebo_quan_tri` · `_placebo_tester` · `_placebo_xu_huong` · `_quay_quan_tri` · `_quet_chuoi_dai` · `_quet_nen_dat` · `_quet_quan_tri_python` · `_quet_rong_d1` · `_quet_signal_mql5` · `_quet_song_moc` · `_quet_song_song` · `_quet_tester_da_ma` · `_san_4_gia_thuyet` · `_san_he_pho_thong` · `_so_quan_tri` · `_so_sanh_chi_so` · `_so_voi_mua_giu` · `_sonic_r_don_bay` · `_sonic_r_kiem_chung` · `_sonic_r_placebo` · `_sonic_r_tpsl` · `_sua_ten_kho` · `_tai_chi_so_xm` · `_tester_holdout` · `_tham_dinh_co_che` · `_thu_chuoi_dai` · `_thu_day_chuyen_video` · `_thu_doi_khung` · `_thu_hai_cach` · `_thu_hoi_payload` · `_thu_mql5` · `_thu_quan_tri` · `_thu_tia` · `_tmp_chk` · `_tmp_chk2` · `_tmp_chk3` · `_tmp_dbg` · `_tmp_dbg2` · `_tmp_quet` · `_toan_luc` · `_tong_bench_qt` · `_trend_don_bay` · `_trend_theo_che_do` · `_truy_chang_4_5` · `_tv_toan_luc` · `_va_co_che_thieu` · `_va_duong_dan` · `_va_python_exe` · `_von_va_lot` · `_xac_minh_chenh_lech` · `_xao_toan_kho` · `_z5_chuoi_dai` · `_z5_don_bay` · `_z5_theo_nam` · `bao_cao_hen_gio` · `bo_nao` · `chay_backtest` · `chay_gop_vs_don` · `chay_tester_kho` · `chay_tester_z5` · `chien_luoc_mr` · `chien_luoc_mr_tf` · `chien_luoc_trend` · `chup_darwinex` · `conftest` · `cross_pair_quet` · `dang_ky_alphavantage` · `dang_nhap` · `darwinex_ocr` · `do_spread_hang_loat` · `doc_bang_trinh_duyet` · `doc_cdp` · `doc_email` · `doc_for_ds` · `doc_otp_gmail` · `doc_web_moi` · `ea_tu_dong` · `fl_cheo` · `gen_kiem_ke` · `hang_doi` · `ichimoku_cross` · `keywords_nguon` · `khao_sat_daily_zone` · `lab` · `lay_api_darwinex` · `lay_api_darwinex_v2` · `lay_du_lieu` · `lo_mot_gio` · `loc_chat_luong` · `mt5_chay_ichimoku` · `mt5_worker` · `nap_darwinex_api` · `nap_lai_ban_tho` · `nguon_code` · `nguon_dien_dan` · `nguon_kham_pha` · `nguon_reddit` · `nguon_reddit_sim` · `nguon_telegram` · `nguon_youtube` · `__init__` · `nhip_song` · `p_null_vs_ung_vien` · `placebo_d1` · `quant_sweep` · `quet_loi_ra` · `__init__` · `rem_via_tele` · `run_mt5_flag` · `seeker_cong_dong` · `seeker_deep` · `seeker_theo_doi` · `simulator_nguoi` · `tele_gate` · `telethon_ban` · `toc_do` · `tu_dang_ky` · `tu_follow_join` · `vao_web` · `xac_nhan_d1`

## Tren duong chay

### nhan/

- `nhan/anh_chup.py` — GHIM BAN DU LIEU de mot ket qua tai lap duoc.
- `nhan/bai_hoc.py` — SO BAI HOC: he tu tra loi duoc "cai nay da thu chua".
- `nhan/ban_do.py` — SINH ban do he thong TU CHINH MA NGUON.
- `nhan/bang_he.py` — BANG CAC HE DA QUA CONG. Mat xich cuoi cung, va no dang thieu.
- `nhan/bi_mat.py` — MOT CUA doc khoa. Khong module nao tu mo file khoa.
- `nhan/bien_dich_ung_vien.py` — Bien dich tai lieu da thu thap thanh CandidateArtifact co dan nguon.
- `nhan/bien_don_bay.py` — BIEN DON BAY. Don bay bao nhieu, va no tra ve duoc gi.
- `nhan/boc_llm.py` — BOC CO CHE bang LLM, ban NANG SUAT.
- `nhan/boc_ma_llm.py` — BOC CO CHE tu ma nguon EA: regex khoanh vung, LLM dich.
- `nhan/canary.py` — CHIM HOANG MAI. Gac chinh cai engine dang duoc dung.
- `nhan/cau_browser.py` — CAU NOI: "The Eye of Seeker" (browser/) -> The Brain.
- `nhan/cham_diem.py` — BANG DIEM THUC TE. Ra tien bao nhieu, rui ro the nao.
- `nhan/chi_phi.py` — MO HINH CHI PHI DO DUOC, khong phai go tay.
- `nhan/chi_tieu.py` — CHI TIEU NGAY va CHIA THOI LUONG THEO NEN TANG.
- `nhan/chuoi_quan_tri.py` — NOI BA MANH QUAN TRI VI THE THANH MOT DUONG CHAY.
- `nhan/chuyen_he.py` — MANG MOT HE SANG CHO KHAC MA NO VAN LA CHINH NO.
- `nhan/cong.py` — CONG PASS. Noi duy nhat mot gia thuyet duoc phep doi doi.
- `nhan/da_thoi_dai.py` — CHAY MOT CO CHE TREN MOI CUA SO DU LIEU SACH, khong chi mot.
- `nhan/danh_muc.py` — TANG 3 - tinh von va ket hop cac gia thuyet da qua cong.
- `nhan/dap_quan_tri.py` — DAP MOT BO LUAT QUAN TRI LEN MOT TIN HIEU VAO BAT KY.
- `nhan/dau_chan.py` — LUAN NGUOC KIEU CHIEN LUOC tu DAU CHAN CONG KHAI.
- `nhan/day_chuyen.py` — NOI CA DAY CHUYEN 03/09/2026 THANH MOT CHO GOI.
- `nhan/day_chuyen_quantlab.py` — QUY TRINH CHUAN: ma nguon -> co che -> he thong.
- `nhan/de_quan_tri.py` — CHEN bo quan tri cua ta vao MOT EA NGOAI, roi do bat/tat.
- `nhan/dia.py` — CONG DIA DAY. Khong phai mot bao cao, mot CONG.
- `nhan/dich_mq5.py` — DICH KHAI BAO DSL SANG MQL5 DE TESTER LAM TRONG TAI.
- `nhan/dich_mq5_ghep.py` — MOT EA CHAY NHIEU CO CHE CUNG LUC (ghep he thong).
- `nhan/dich_mq5_qtvt.py` — DICH KHAI BAO QUAN TRI VI THE SANG MQL5. Hai duong ra.
- `nhan/dich_mq5_quan_tri.py` — EA GHEP CO QUAN TRI VI THE.
- `nhan/dns_vuot.py` — VUOT DNS BI DAU DOC, giu nguyen SNI va TLS that.
- `nhan/do_im_lang.py` — TIM TANG NAO DANG CAM MA KHONG AI BIET.
- `nhan/do_luc.py` — Do LUC cua cong: edge nho nhat ma he con nhin thay duoc.
- `nhan/do_luong.py` — CHI SO + ALPHA SO VOI MUA-GIU.
- `nhan/do_tai_nguyen.py` — DO CHI PHI VAN HANH, khong phai chi phi giao dich.
- `nhan/doc_chi_bao.py` — BOC CO CHE TU FILE CHI BAO (190 file, lop chua ai dong toi).
- `nhan/doc_hieu.py` — DOC VAN XUOI THANH CO CHE KIEM DINH DUOC.
- `nhan/doc_lenh_tester.py` — Doc DANH SACH LENH tu bao cao MT5 Strategy Tester.
- `nhan/doc_ma.py` — DOC MA NGUON THANH NHIEU KHAI BAO CO CHE.
- `nhan/doc_song_song.py` — DOC TOAN VAN song song, uu tien nguon co SUAT CAO.
- `nhan/doc_trinh_duyet.py` — DOC BANG TRINH DUYET DANG MO (CDP) cho SEEKER.
- `nhan/doc_video.py` — VIDEO -> VAN BAN, de video di chung mot duong voi van xuoi.
- `nhan/doi_khung.py` — CHUYEN MOT CO CHE SANG KHUNG KHAC MA NO VAN LA CHINH NO.
- `nhan/don_mo_coi.py` — Tim va don TIEN TRINH MO COI dang an CPU.
- `nhan/du_lieu.py` — NAP DU LIEU TU CHINH CONG CU SE GIAO DICH.
- `nhan/duong_dan.py` — MOT CHO duy nhat giai cac duong dan phu thuoc MAY.
- `nhan/duyet_nguoi.py` — DUYET NHU NGUOI: giu phien, co Referer, nhip khong deu.
- `nhan/evo.py` — THE EVO: giam sat hieu suat tung module, cat nghia, de xuat.
- `nhan/go_html.py` — KHAU CON THIEU giua THU THAP va BOC: go trang HTML ra van ban.
- `nhan/gop_lop.py` — GOP LOP - kiem dinh MOT co che tren CA MOT LOP TAI SAN, ton MOT suat FDR.
- `nhan/gop_wal.py` — GOP `nao.db-wal` VAO DB. Cai phanh cho mot kieu day dia lang le.
- `nhan/han_muc.py` — KILL-SWITCH va TRAN. Cai phanh, khong phai cai ga.
- `nhan/hang_doi.py` — HANG DOI VIEC cua QUANTLAB. Chong nghen, chay song song duoc.
- `nhan/ho_so_mua_vu.py` — TINH MUA VU va ENTRY-TIME cua mot tai san.
- `nhan/ho_so_song.py` — DAC TINH SONG va MOC MAGNETIC cua mot tai san.
- `nhan/ho_so_symbol.py` — HO SO TAI SAN: tra loi "co gia thuyet nay thi thu tren cai gi".
- `nhan/ho_so_tuong_quan.py` — TUONG QUAN LIEN MA va DO ON DINH cua no.
- `nhan/hop_dong.py` — Versioned hand-off contract from SEEKER to downstream consumers.
- `nhan/ket_qua_hoat_dong.py` — Quy tac doc ket qua dang hoat dong cua THE BRAIN.
- `nhan/kham_pha_nguon.py` — SO DANG KY CAC KENH TU TIM NGUON MOI.
- `nhan/khoa_tester.py` — MOT CUA CO KHOA cho `terminal64.exe`.
- `nhan/loc_co_che.py` — BO LOC TINH, CHAY TRUOC PHEU V0-V3.
- `nhan/luan_dau_chan.py` — 400 HO SO SIGNAL -> KIEU CHIEN LUOC. Noi hai manh mo coi.
- `nhan/ma_nguon.py` — MA NGUON EA / CHI BAO -> CodeArtifact.
- `nhan/mach.py` — MACH DAP CUA DUONG ONG. Canary cho tung chang, khong chi cho engine.
- `nhan/mau.py` — THU VIEN MAU CHIEN LUOC (template + tham so).
- `nhan/mimic_cau_noi.py` — NOI `ds/mimic` VAO DUONG CHAY CHINH.
- `nhan/mo_phong.py` — ENGINE BACKTEST. Mot cua duy nhat de bien tin hieu thanh tien.
- `nhan/muc_tieu.py` — CHIEN DICH THEO MUC TIEU. Day moi la "The Brain + QUANTLAB".
- `nhan/nen.py` — DOI CACH DUNG NEN, NHUNG CHI CHO TIN HIEU.
- `nhan/nen_tang.py` — MA NGUON CHIEN LUOC TU CAC NEN TANG GIAO DICH KHAC.
- `nhan/ngan_sach.py` — SO NGAN SACH TAI NGUYEN. Cua vao chung cho moi viec nang.
- `nhan/ngoai_sinh.py` — LUONG NGOAI SINH. Ke thua tu ben ngoai, roi CHINH cho tai san moi.
- `nhan/ngu_phap.py` — NGU PHAP CO CHE. Cach duy nhat kien thuc moi di vao day chuyen.
- `nhan/nguon_bai_viet.py` — NGUON VAN XUOI: bai viet chien luoc, lay qua RSS/Atom.
- `nhan/nguon_tinix.py` — repo.tinix.ai -> ung vien cong cu cho FINDER.
- `nhan/nha_may_null.py` — 
- `nhan/noi_sinh.py` — LUONG 3. Tu sinh co che tu CHINH LICH SU cua ma, khong doi nguon ngoai.
- `nhan/pham_vi.py` — Pham vi ap dung cua tung ho co che - va phep thu phan chung di kem.
- `nhan/phan_loai_ma.py` — CHIA KHO MA NGUON THANH BON LAN, TRUOC KHI BOC.
- `nhan/pmg.py` — POSITION MANAGEMENT GRID ENGINE. Ho quan li lenh KHONG CO TIN HIEU VAO.
- `nhan/pmg_engine.py` — MO PHONG RO cua PMG tren bar. Cong G2 cua dac ta.
- `nhan/pmg_g0.py` — CONG G0 cua PMG. Do TINH CHAT QUA TRINH GIA truoc khi viet engine.
- `nhan/pmg_quet.py` — PHEU CUA PMG: G1 -> G2 -> G3, va SO DEM PHEP THU.
- `nhan/quan_tri.py` — BOC CO CHE QUAN TRI VI THE tu ma nguon EA.
- `nhan/quan_tri_dsl.py` — NGON NGU KHAI BAO CHO QUAN TRI VI THE.
- `nhan/quan_tri_llm.py` — ANH XA INPUT -> NUT VAN khi bang REGEX khong doc noi ten.
- `nhan/quy_doi_tham_so.py` — DOI TAI SAN THI THAM SO PHAI DOI THEO.
- `nhan/quy_luat_song.py` — TU TIM QUY LUAT trong chuoi song, da khung.
- `nhan/san_cong_cu.py` — DI SAN CONG CU CO SAN, thay vi tu viet lai tu dau.
- `nhan/san_sang_vps.py` — HE DA CHUYEN LEN VPS DUOC CHUA.
- `nhan/sang_loc.py` — PHEU BON VONG: V0 van tay -> V1 re -> V2 kinh te -> V3 phan chung.
- `nhan/so.py` — SO CAI CUA THE BRAIN. Mot nguon su that duy nhat cho ca 4 tru.
- `nhan/so_lenh.py` — SO LENH PAPER: cho mot he DA QUA CONG di tiep, khong dung o nhan.
- `nhan/suy_nguoc.py` — SUY NGUOC: truoc mot cu di manh thi CO DAU HIEU GI.
- `nhan/tai_khoan_nen_tang.py` — MOT CHO BIET he dang co tai khoan nao, thieu cai gi.
- `nhan/tai_tro.py` — CARRY cua mot vi the chi so giu qua dem.
- `nhan/telegram.py` — TELEGRAM -> tai_lieu / noi_dung.
- `nhan/theo_doi.py` — THEO KENH DA CHON, doc lai theo LICH do duoc.
- `nhan/thu_hoi_thanh_phan.py` — GIU LAI PHAN DUNG DUOC CUA MOT HE THONG BI LOAI.
- `nhan/tien_ich_xet.py` — 58 FILE "TIEN ICH" DANG BI BO: CAI NAO DANG LAY VE?
- `nhan/tin_hieu_mql5.py` — DO NGUOC PHONG CACH DANH tu tai khoan CO LAI cong khai.
- `nhan/tinh_cach.py` — DO TINH CACH TAI SAN bang so hoc: hoi quy hay xu huong?
- `nhan/to_hop.py` — TO HOP DA CAP x DA KHUNG x DA QUAN LI x DA THONG SO.
- `nhan/toan_van.py` — TANG DOC. Lay NOI DUNG THAT chu khong phai dong tieu de.
- `nhan/tri_tue.py` — Cau noi OpenAI tuy chon cho tien trinh nen 24/7.
- `nhan/uu_tien.py` — CUA MOT BUOC cho chu du an: mot link/file -> co che, ngay trong phien.
- `nhan/vao_lenh.py` — CAU TRUC VAO LENH nhieu chan. Nua con thieu cua module quan tri.
- `nhan/vong_day_du.py` — MOT LENH chay CA BA TRU theo dung so do cua chu du an.
- `nhan/vuon_nguon.py` — VUON NGUON: do suat, chia ngan sach, tu tim nguon moi.

### tru/

- `tru/__init__.py` — 
- `tru/banker.py` — TRU BANKER. Vi mo cap nhat lien tuc + phan tich sat sao.
- `tru/evolution.py` — TRU EVOLUTION. Giam sat, nhin ra van de, tu cai tien.
- `tru/finder.py` — TRU FINDER. Tim giai phap CONG NGHE de nang cap ha tang.
- `tru/nghi.py` — TRU NGHI. Bien thu doc duoc thanh thu kiem dinh duoc, roi HOC TU KET QUA.
- `tru/quantlab.py` — Quantlab V2: two isolated research lanes sharing only validated primitives.
- `tru/seeker.py` — TRU SEEKER. Phong thu thap thong tin va kien thuc 24/7.

### qwen/

- `qwen/bang_viec.py` — Doc NHIEM_VU.json, giai phu thuoc, chon viec de phong.
- `qwen/cau_hinh.py` — MOT noi giu moi hang so cua he qwen.
- `qwen/chay.py` — VONG LAP DIEU PHOI. Mot lenh `q` la du de he chay tiep nhieu ngay.
- `qwen/cong.py` — CHAM KET QUA BANG CODE. Day la thu giu qwen khoi noi doi.
- `qwen/cong_cu.py` — Bo cong cu LangChain cho qwen. DANH SACH TRANG, khong co vo shell.
- `qwen/dieu_toc.py` — GIU MAY O ~85% CPU, do bang phep do chu khong bang gia dinh.
- `qwen/mo_hinh.py` — Duong LLM cho LangChain: khoa doc TAI CHO tu cc-switch.
- `qwen/so_tay.py` — Bo nho ben ngoai cua he: viec nao xong, cong cham gi, qwen viet gi.
- `qwen/tac_tu.py` — Tac tu LangGraph. qwen DOC ket qua va VIET, khong cham va khong chay.
- `qwen/tien_trinh.py` — Phong mot viec thanh mot TIEN TRINH RIENG, khong phai mot luong.

### goc lab

- `BAN_GIAO.py` — MOT LENH de vao phien: in ban ban giao + trang thai SONG cua he.
- `KET_PHIEN.py` — KET PHIEN — mot lenh chot ngay hom nay de mai vao lam ngay duoc.
- `_bo_ba.py` — GHEP BA CHAN, VA KHU TRUNG THEO DUONG VON.
- `_corpus_ngu_phap.py` — DO TRAN CUA NGU PHAP bang corpus van xuoi THAT.
- `_dem_ghep.py` — DAY CHUYEN TU CHAY: mo kho -> dao chan am -> ghep -> cong ra tien.
- `_do_suat_doc_ma.py` — DO SUAT THAT cua `doc_ma` tren 469 ban doc MA NGUON dang nam khong.
- `_ghep_da_tai_san.py` — GHEP CHAN TU CAC TAI SAN KHAC NHAU.
- `_ghep_holdout.py` — CHAM CAP TREN TRAIN, DO TREN HOLDOUT. Khong chay tester.
- `_khung_nho.py` — CHON CHAN TRUC TIEP TREN TUNG KHUNG (khong bung tu D1).
- `_noi_sinh_chay.py` — Chay LUONG 3 (noi sinh) tren mot ma + khung, dung quy trinh.
- `_pheu_nguon.py` — PHEU NGUON: tai lieu -> ban doc -> co che -> cau hinh. Ti le chuyen doi bao nhieu?
- `_quan_tri_ghep.py` — QUAN TRI VI THE DANG BAO NHIEU? Do o TICK, khong o nen.
- `_quet_bench_qt.py` — quet ban do quan tri tren DA TAI SAN x DA ENGINE VAO.
- `_quet_placebo_rong.py` — PLACEBO CHO TAT CA CO CHE QUA TRAIN/HOLDOUT, MOT LUOT.
- `_quet_quan_tri.py` — QUET CA HAI HO QUAN TRI tren nhieu tai san.
- `_qwen_het_cong_suat.py` — vong lap DOC -> BOC chay den khi het ton kho.
- `_stop_hai_dau.py` — HE THANG BANG QUAN LY LENH: dat stop hai dau, cai nao khop
- `_tinh_cach_tai_san.py` — Do TINH CACH tai san roi DOI CHIEU voi ket qua that de xem no co du bao khong.
- `b.py` — b — MOT cua vao cho moi viec hang ngay cua THE BRAIN.
- `ban_giao_song.py` — SO BAN GIAO SONG, ghi lien tuc chu khong doi cuoi phien.
- `bang_dieu_khien.py` — MOT MAN HINH DUY NHAT de biet he dang the nao.
- `cham_lai_the_he.py` — CHAM LAI moi gia thuyet da dang ky duoi THE HE CONG hien tai.
- `chay_bang_mde.py` — Chay ban NGHIEM THU cua nha may luc + nha may null, ra BANG MDE.
- `chay_bench_quan_tri.py` — DUA 11 HO QUAN TRI VI THE RA MT5 TESTER.
- `chay_test_tung_me.py` — chay CA bo test bang NHIEU tien trinh pytest ngan.
- `chuyen_giao.py` — Sao luu + ban giao THE BRAIN (chay cuoi moi phien lam viec).
- `day_viec.py` — HANG DOI VIEC XAY, chay TUAN TU va LIEN TUC.
- `dieu_khien_xa.py` — nghe lenh Telegram, KHONG ton mot token nao cua agent.
- `dieu_phoi.py` — Control plane 24/7 cho nam tru hien hanh cua THE BRAIN.
- `do_on_dinh.py` — CAO NGUYEN hay CAI GAI? Do HINH DANG cua mot edge.
- `giam_sat_dieu_phoi.py` — Watchdog ngoai tien trinh cho control plane.
- `hinh_dang_vs_null.py` — HINH DANG cua edge co phan biet duoc voi NGAU NHIEN khong?
- `mo_chrome_cdp.py` — Mo Chrome da dang nhap (.browser_darwinex) kem CDP 9224.
- `nap_truoc_mde.py` — Nap truoc BANG MDE cho ca be mat, thay vi do lazy giua vong quet.
- `quet_be_mat.py` — Quet TANG KHAM PHA tren toan be mat: moi co che x moi tai san, khung D1.
- `tinh_trang.py` — In tinh trang hien tai de biet dang lam viec toi dau.
- `toan_canh.py` — MOT MAN HINH cho biet he dang o dau — doc xong trong 30 giay.

