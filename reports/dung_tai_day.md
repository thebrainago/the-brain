# Dung tai day (07/10/2026 23:30) - dia RAM + Defender + 16-18 bo

- Defender: loai tru thu muc C:\Research SP500, C:\MT5slots, D:\MT5cache, C:\Program Files\XM Global MT5, AppData\Roaming\MetaQuotes; tien trinh terminal64/metatester64/python/powershell; duoi parquet/tkc/hcc/hc.
- Dia RAM R: 4 GB (OSFMount, NTFS). Cong thuc cloud min(nong+2GB,12GB) = min(1,15+2;12) ~ 3,2 -> chon 4 GB. data/ 1,15 GB (lab\data = junction R:\data, ban goc lab\data_goc) + cache MT5 s2,s3 (junction R:\MT5cache\*, goc D:\MT5cache; s1 dang chay se doi lan khoi dong sau). R: dung 1,54 GB. Ket qua van ghi dia that: dong bo R->goc 10 phut/lan (task TheBrainRamdiskDongBo), tao lai dia khi khoi dong (task TheBrainRamdisk + dau khoi_dong_song_song.ps1).
- Toc do doc truoc/sau: 1,15 GB parquet doc tuan tu 0,19 GB/s ca dia that lan dia RAM (6,1 s) - nut that la CPU (100% tai), khong phai o dia; dia SSD + cache Windows da du nhanh. Loi ich dia RAM chu yeu: bot ghi/doc nho cua tester, khong nang toc doc tuan tu.
- Bo chay: 18 bo CPU p1..p18 + m1..m3 + nha (22). Task TheBrainSongSong da doi -N 18.
- Do luc 16 bo: CPU 100% (tb va max), disk 4%, RAM trong min 15,4 GB. Luc 18 bo: CPU 100%, disk 1%, RAM trong min 16,1 GB, commit 41,7/81,9 GB, 101 tien trinh python, 3 terminal64. => 16 da bao hoa CPU; 18 khong lam hong nhung cung khong them CPU. Dieu toc tran_cpu 70 van de nguyen.
- Cat som mo phong (tk lo >=70% von): chua lam, can doc cau_hinh mo phong; ghi so o bi cat de cloud doi chieu khi lam.
- Choi LoL: che_do_choi chi tam dung runner, KHONG go dia RAM; RAM trong luc chay day >= 15 GB, tam dung runner thi tra lai >= 18 GB.
