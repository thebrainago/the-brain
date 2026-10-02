# PHIEN HIEN TAI - doc DAU TIEN thay cho lich su chat / tai lieu dai

> Khoi AUTO do may lam moi (`b tiep --ghi`); khoi TAY do phien chi huy viet, cap nhat sau moi moc. Tai lieu day du: `b tiep --chi-muc`.

<!-- AUTO:BAT_DAU -->
## Trang thai (may do luc 2026-10-02 17:16 UTC) - `b tiep --ghi` de lam moi
- Nhanh claude/autonomous-trading-system-rzzt7h @ 2f310bd · 3 file sua/chua theo doi · so voi origin/claude/autonomous-trading-system-rzzt7h: +0/-0
- Commit gan day:
  · 2f310bd cau_thu: phien cloud REBASE khi nha day chen truoc (gui + doc thu), cay nha van ch
  · 777534a BAN GIAO PHIEN (b tiep) + so sanh model re (b so-sanh) + sua test Windows: phien m
  · ba78852 TOI UU TOKEN theo so do that + CLOUD CHI HUY: b token, cua so nen 300k, gop danh t
  · a17589a KHOI_PHUC_MAY_NHA: VPS het (V6_DONG_GOI + EA LuoiDoiXung khong con ban nao), MT5 c
  · e100fc6 BAT_DAU_O_NHA: truong hop da co lab, hop thu rieng (b cau cai), dang nhap GitHub m
- Thu: phien nay la `cloud`, chua doc 0 · 24h qua: cloud->nha 7, nha->cloud 4
  · moi nhat nha->cloud (gio may gui 2026-10-02T23:56:48): XONG bao cao dem
- May:
  · nha RANH ma=9429269+sua nhip 2026-10-02T23:30:26 (gio may)
- Don: cho 1 · dang 1 · xong 1 (DAT 1)
- Du lieu: kho gia /home/user/the-brain/data: 0 file .parquet · so_cai/doan.json CHUA CO (tao o lan nap() dau, PHAI commit+push ngay) · so_cai/nc 0 file 0 KB
- Cau hinh: config/cau.json khong co (phien cloud)
<!-- AUTO:HET -->

<!-- TAY:BAT_DAU -->
## Quyet dinh cua chu du an con hieu luc (ngay = ngay chot)
- 25/09 TIEU CHI DUYET: co lai sau phi + maxDD < 80%; martingale/DCA/luoi hop le; don bay chap nhan (CLAUDE.md LUAT SO 0).
- 25/09 AI la nha nghien cuu chinh, chu du an la nha tai tro (LUAT SO 1; `b nc` o dau phien).
- 02/10 LAM LAI TU DAU: V6, Ultima AUDCAD, SP500 chi la boi canh, khong phai bang chung. GitHub de PUBLIC (khong dua khoa/token/du lieu rieng vao repo, ke ca thu).
- 02/10 PHIEN CLOUD CHI HUY, phien NHA THUC THI ("toi phan quyen phien cloud cao hon"): nha phan doi 1 lan, cloud quyet. Viec khong khu hoi / di ra ngoai van hoi chu du an.
- 02/10 VPS cu da het -> V6_DONG_GOI/, LuoiDoiXung.mq5/.ex5, .set MAT HAN (chi con dac ta + ket qua). Chi dung MT5 DEMO.
- 02/10 DA DONG Y: `b cau cai`, tat defrag, XM demo (chu du an tu cai MT5 ngay 03/10). KHUYA 02/10 chu du an DUYET HET de xuat: lich schtasks 5 phut (runner khong-LLM, nha bat khi may len), subagent cho viec doc nang (model `haiku` cho viec co hoc), phien cloud MOI sau moc; duyet san moi de xuat tiep (CLAUDE.md VAN HANH).
- 02/10 Chu du an se cap API DeepSeek + Qwen ngay 03/10 de so sanh model re (`b so-sanh`) -> chon cho `b nc tho` / `q`.
- Phong cach chu du an: ngan gon, ghet phuc tap va ghet token vo ich, chi muon MOT kenh; "khong duoc dung lai o muc mo ta".

## Dang o dau (02/10 toi)
- Kenh cloud<->nha THONG hai chieu (ping->pong ~2 phut; nha chay `cho`, runner 1 lan DAT, hop thu rieng `C:\Research SP500\cau_hop_thu`). Nha da: pull, venv, hook, tat defrag, tai MT5 XM (chua cai).
- Nha bao cao dem 02/10 (xong, da dung, chu du an hen gio tat may; KHONG chay `cho` qua dem): `b test` 108 fail / 2642 pass / 46 skip (23 phut); `b nc kiem 30` KHOP cloud tung con so (xac dinh xuyen nen tang); `b token` nha: 60 goi, ngu canh TB 86k (cloud 443k -> ~5x re moi goi). Cloud da sua test `khoa_tien_trinh` (pid 1 khong co tren Windows) + them beautifulsoup4 vao requirements.
- Cloud da lam 02/10: so cai nghien cuu trong git + doan du lieu dong bang theo ngay; kenh `b cau` (thu, cho 55 phut, runner, cau chi 8 thu/30 phut, gop danh thuc 15 phut); `b token`; cua so nen 300k; `b tiep`; `b so-sanh`; tai_lieu BAT_DAU_O_NHA / TOI_UU_TOKEN / SO_SANH_LLM.
- `b so-sanh` (nhan/so_sanh_llm.py, 8 task cham bang ma, tai_lieu/SO_SANH_LLM.md) da viet + 17 test bang nha cung cap gia, CHUA chay that (can API; chay o NHA, `b so-sanh --khai` truoc).

## Viec ke tiep (thu tu)
1. Nha: `git pull`, `pip install -r requirements.txt`, chay lai `b test` luu danh sach fail (node id + loai loi, <= 110 dong, `pytest -q -n 8 --dist loadfile -rfE --tb=no`) vao `reports/test_fail_nha.txt`, push -> cloud diff voi baseline Linux de tim loi CHI-CO-TREN-WINDOWS (da biet 1, da sua). Thieu data/ds/nao.db/config/ffmpeg la moi truong, khong phai loi.
2. 03/10 chu du an cai MT5 XM demo -> nha viet bo xuat M1 (`copy_rates_range`; doc `_tai_chi_so_xm.py` truoc: moc RAT xa, thu lai 4 lan, dem bar moi nam, D1 spread=0) cho AUDCAD, EURCAD, NZDCAD, EURGBP, XAUUSD, US500Cash -> ho chieu du lieu (`reports/ho_chieu_du_lieu.json`) + do chi phi that -> lan `nap()` dau dong bang doan: COMMIT+PUSH `so_cai/doan.json` NGAY -> `b nc kiem 30` + `b test` xanh tren may moi -> roi moi tin phat hien nao.
3. 03/10 `b so-sanh` DeepSeek vs Qwen (tai_lieu/SO_SANH_LLM.md); khoa qua cc-switch (may nha) hoac bien moi truong; KHONG dan khoa vao chat.
4. Cloud viet tiep (chua lam, DA DUYET, lam o phien MOI cho re ~5x moi luot): `b nc tien-len` (giai doan tien len, 7.4), ho chieu du lieu (7.5), tran phep thu (7.6) - tai_lieu/KHOI_PHUC_MAY_NHA.md muc 7.
5. DA DUYET: nha bat lich 5 phut (schtasks) khi may len; subagent cho viec doc nang; mo phien cloud MOI (phien cu ~450k ngu canh): phien moi vao bang `b tiep` roi gui nha thu `b cau dat-session <session_id moi>` (id: `get_session`).

## Dung lam lai (da thu / da quyet)
- Khong tim V6_DONG_GOI / EA tren VPS (het). Khong khoi phuc o E: (chua co dau vet bang file cu, can Admin) - ha uu tien, chi lam neu chu du an muon.
- Khong cat CLAUDE.md (toan luat da sap that). Khong poll bang LLM: cho bang lenh khong-LLM hoac `send_later` MOT lan.
- Khong chay `b ket` (KET_PHIEN.py) o container cloud: no `git add -A` va doc `nhip_song` cua the gioi cu; dung `b tiep --ghi`.
- Ket qua cu (SP500 / V6 / Ultima AUDCAD) khong phai bang chung; thu lai y tuong cu = dang ky gia thuyet MOI.
- Baseline test: Linux cloud 77 fail + 4 error, nha Windows 108 fail (chua phan loai het) - DO MOI TRUONG phan lon; chi so luong / diff danh sach, dung sua tung cai.
<!-- TAY:HET -->
