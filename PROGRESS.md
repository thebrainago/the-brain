# PROGRESS - may nha (cap nhat 07/10/2026 12:35, truoc khi chu du an restart may)

## Muc tieu
May nha keo don tu cloud qua git (`b cau`), chay het cong suat (chu du an cho 90-100% CPU, toan quyen cai dat), bao van de cho cloud.

## Da lam hom nay
- Chay song song: 14 bo CPU (hop thu `..\cau_hop_thu_p1..p14`, env CAU_HOP_THU/CAU_TEN/CAU_KHA_NANG) + bo chinh `nha` (Task Scheduler `TheBrainCauChay`, nhan don TESTER). Sau restart: task `TheBrainSongSong` (logon) chay `khoi_dong_song_song.ps1 -N 10` (go CAU_DUNG roi mo 10 bo).
- Cong dieu toc cloud (`qwen/dieu_toc.py`) + `config/dieu_toc.json` {tran_cpu 70, cach_giay 8, ram>=5GB, commit>=8GB}. cach_giay=20 la nut that khi don ngan.
- ziglang da cai (`b cai-goi ziglang`). Cache Tester chuyen sang D:\MT5cache (junction, C: tu 14 len 20GB trong).
- Sua `ea_tu_dong.bien_dich` (them /portable) va `_pid_cua` (psutil). Ban va luu o `ban_va_may_nha/ban_va_07102026.patch` (cau_git: CAU_TEN/CAU_KHA_NANG; ea_tu_dong). Khi `git pull` bi chan do cau_git.py: `git diff HEAD qwen/cau_git.py > p; git checkout HEAD -- qwen/cau_git.py; git pull --ff-only; git apply p`.
- Ket qua: hieu chuan luoi 100c/d/e (tn 186/190/192): engine lech tester chu yeu o swap (-3..-4%/nam vs 0) va von_quy_doi. CLMCA D_V1 Model 0 (tn 259): +9,54%/nam, maxDD 58,1%, 1551 lenh, PF 1,28 - Model 0, chi phi KHAI -> CHUA phai ket luan; T1 yeu cau xac_nhan dung MOT lan o Model 0 (chua lam). 24 EA kho deu TIEN_ICH.
- Tai 2 bot .ex5 (EA21 Samurai, EA36 Custom Hedge Grid) o `du_lieu_cao/drive_ea/` (khong vao git, khong dich nguoc; chua chay tester).

## Van de mo (da bao cloud)
1. SLOT PORTABLE s1-s3 HONG, da KHOA trong `config/slot_tester.json` (ban goc `.bak_0710`, `ban_va_may_nha/slot_tester.json.goc`). Co /portable -> agent khong len, test treo; khong /portable -> bao cao o AppData. Cloud huong dan: copy CA THU MUC cai MT5 (gom metatester64, Tester, MQL5, config) vao slot, port agent rieng (3000+10*i), Allow local agents. Chua thu.
2. Pagefile 48GB tren D: can quyen admin that (UAC bi huy vi khong ai bam) - lam khi chu du an bam.
3. Chan Windows tu restart (NoAutoRebootWithLoggedOnUsers) cung can admin.
4. ~10 don 20EUR*/20NZD* h2 bi ghi CHUA_DO_DUOC oan (het slot) - cloud giao lai.
5. 'DAT' ben ngoai = ma thoat 0; doc trang_thai ben trong.

## Viec tiep theo
- Sau restart: kiem `tasklist | find /c "python"`; `b cau lay`; neu CAU_DUNG con thi go. Doc `nhat_ky/chuyen_cache_D.log` neu junction hong (`dir C:\MT5slots\s1` phai la JUNCTION).
- Thu dung 1 slot portable theo huong dan cloud; neu ra bao cao thi nhan ra 3.
- Chay xac_nhan CLMCA D_V1 o Model 0 (EA_THO_CFG=config/ea_tho_model0.json).
- Ho so hanh vi EA21/EA36 bang tester mac dinh (vang/AUDCAD M15) khi co slot.

## Gia dinh
- Toc do don CPU phu thuoc don (quet_luoi 3000 o/don ~700 giay CPU, 3-4 luong); ~1120 don 22xxxx uoc ~11 gio.

## Cap nhat 07/10/2026 12:50 (sau restart, co ADMIN)
- Xong: High performance (CPU 100%, khong sleep); pagefile D 48GB + C 2-4GB (dat); chan auto-reboot Windows (NoAutoRebootWithLoggedOnUsers=1).
- Sua `TheBrainSongSong`: pwsh.exe (Store) loi 0x80070002 -> powershell.exe 5.1; 10 bo p1..p10 len, CAU_DUNG da go.
- Junction `C:\MT5slots\s1,s2\Tester` tao lai sang D:\MT5cache (truoc la thu muc thuong, cache vao C:). s3 van OK.
- Da gui bao cao cho cloud (b cau noi) + `reports/nen_may_nha.md` cuoi file. Cho cloud giao them don.
- Con lai: slot portable s1-s3 van khoa; xac_nhan CLMCA Model 0; ho so EA21/EA36.

## Cap nhat 07/10/2026 16:27 - SLOT PORTABLE DA SUA, 4 SLOT TESTER DUOC NANG
- NGUYEN NHAN that: MT5 /portable tach sai tham so /config khi duong dan co dau cach (log: cannot load config "...ini""). KHONG phai thieu metatester64. Sua a_tu_dong.py (chep ini sang C:\MT5slots\ini truoc khi chay slot portable).
- Kiem chung (reports/slot_kiem_chung.json): (a) cung ini AUDCAD# M15 2018H2 Model 0 -> s1 = s2 (net 808.07, 609 lenh, PF 1.43, DD 7.65%, 8.59M tick); (b) AUDCAD@s1 + EURCAD@s2 chay CUNG LUC = chay rieng EURCAD@s3 (net 791.84, 862 lenh, PF 1.28, DD 12.06%). Khop tung chi so.  slot kiem => DUOC NANG.
- Bat lai s1-s3 trong config/slot_tester.json (4 slot gom mac_dinh). Khoi dong lai bo 
ha (TheBrainCauChay) de nap code moi. 
han/ngan_sach.SUC_CHUA['TESTER'] GIU 1 (khong ai dung khoa do; test coi la rang buoc co dinh).
- Con lai: don hieu chuan 20*-h3 (12 don) cho 
ha tuan tu; xac_nhan CLMCA Model 0; ho so EA21/EA36; p11/p12 treo ~3h (kiem).

## Cap nhat 07/10/2026 18:05 - 4 TESTER SONG SONG
- Doc 3 thu cloud (09:09/09:27/10:21 gio cloud): lam du. Go .khoa_tester cu (nha,m1,m2; pid chet) -> 63 don TESTER hoi lai duoc nhan. Bat m1-m3 (TESTER-only) + p13,p14. 4 terminal64 chay song song luc 18:00 (mac_dinh,s1,s2,s3). Da bao cloud (push can thu lai nhieu lan vi ~19 bo cung day mot nhanh).
- 
ha + m1-m3 CHI nhan TESTER: env CAU_CHI_LAN=TESTER (va qwen/cau_git.py chay_mot_don_dang_cho). Task TheBrainCauChay da boc env; khoi_dong_song_song.ps1 mo m1-m3 + p1..p14 (-N 14). Ban va: ban_va_may_nha/ban_va_07102026b.patch (cau_git + ea_tu_dong + slot_tester.json).
- LUU Y: khi git pull bi chan do cau_git.py: dung quy trinh o muc 'Da lam hom nay' (diff -> checkout -> pull -> apply).
- Viec tiep: theo doi 4 tester ra bao cao; p11/p12 treo (kiem); xac_nhan CLMCA Model 0; ho so EA21/EA36.

## 07/10/2026 18:55 - TAT MAY HA NHIET (chu du an: chay 12 tieng roi)
- Da dat CAU_DUNG, doi het don dang chay (4 tester + CPU) xong, day het hop thu len remote (khong con 'ahead'). Ket qua tong: 1036 (DAT 988, CHUA_DO_DUOC 48), con cho 452.
- Tat may bang shutdown. Khi bat lai: TheBrainSongSong (logon) go CAU_DUNG, go khoa tester cu, mo m1-m3 (TESTER-only) + p1..p14; TheBrainCauChay mo 'nha' (TESTER-only). Viec dau phien sau: kiem 	asklist | find /c "python",  cau lay, dir C:\MT5slots\s1 Tester phai la JUNCTION, doc thu cloud (b cau lay roi b cau thu).
- Con lai: p11/p12 treo (kiem); xac_nhan CLMCA Model 0; ho so EA21/EA36.

## 07/10/2026 23:05 - CHI PHI THEO TK XM MICRO TRANG
- Chu du an: tk XM micro (XMGlobal-MT5 10, login/mat khau o E:\api.txt) la tk TRANG khong nap tien, dung xem spread/swap/phi -> chi phi phai tinh theo tk nay. Chi doc, khong dat lenh.
- Da do lai swap/phi 380 ma XM (thay ban MT5 17; 13 ma hop dong thang giu so cu) va spread bar H1 80 ma (EURCAD 1,74 bps; AUDCAD 3,28; NZDCAD 4,84; EURGBP 2,54; vang 0,71; US500 1,0). Backup: config/chi_phi_do.json.bak_xm10. Sua TERMINAL['XM'] -> "XM Global MT5". Terminal XM gio dang nhap san tk trang (demo cu 345930355 khong con mac dinh).
- GPU may nha GT 730 2GB -> reports/gpu_may_nha.md (da bao cloud).
- Viec tiep: chay lai CLMCA Model 0 + hieu chuan voi chi phi moi; p11/p12 treo.

## 07/10/2026 23:35 - DIA RAM + DEFENDER + 18 BO
- Defender loai tru xong; dia RAM R: 4GB (OSFMount) co data + cache MT5 s2,s3; script `ramdisk_khoi_dong.ps1` (tasks TheBrainRamdisk luc boot, TheBrainRamdiskDongBo 10 phut). lab\data = junction R:\data, goc lab\data_goc. s1 se doi sang R: lan khoi dong sau (dang chay tester).
- 18 bo CPU (p15-p18 moi clone), TheBrainSongSong -N 18. CPU 100%, RAM trong >=15 GB. Chi tiet: reports/dung_tai_day.md.
- Doc tuan tu khong nhanh hon (nut that la CPU). Chua lam: cat som mo phong khi lo>=70% von (muc 4 chi thi cloud 12:30).
