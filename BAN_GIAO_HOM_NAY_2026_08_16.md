# BAN GIAO HOM NAY - 2026-08-16 (cuoi phien, da luu thanh qua)

## Da lam xong trong hom nay
1. SEEKER noi them nguon TRINH DUYET (12 nguon xa hoi + track-record) chay qua Chrome
   CDP dang mo: reddit, mql5_signals, myfxbook, collective2, fxblue, etoro, zulutrade,
   darwinex, x, tiktok, facebook, youtube. Ham `quet_trinh_duyet()` trong tru/seeker.py.
2. SEEKER noi nguon TELEGRAM follow (session that, khong can CDP): `quet_telegram_follow()`.
   Da chay duoc: 8 kenh, ~12 tin moi/vong vao thu vien.
3. Mo Chrome bot DUNG profile `.browser_darwinex` @ CDP 9224 (sua `mo_chrome_cdp.py`,
   truoc trỏ nham thebrain2/9222). Quet song song `_quet_song_song.py` mo 13 tab qua
   cac site, GUI TAB + bring_to_front de nhin thay tren man hinh.
4. Tu dang nhap bang pass luu: `nhan/tu_dang_nhap.py` (doc config/tai_khoan.json,
   form-detect nhu dang_nhap.py, khong can nguoi dung nhap lai).
5. LLM the he 2: tri_tue.py ho tro provider OpenAI-compatible (duong lui khi khong co
   Claude); loi ro "chua cau hinh LLM" thay vi treo.
6. nghi.py: co che truy nguyen nguon that, khong be mat lieu khi loi/toan van.
7. Ho so nho: `lab/GHI_NHO_LAM_VIEC.md` (tai khoan, port, lenh, trang thai, viec con)
   va chen ptr vao AGENTS.md de moi phien doc lai.

## Trang thai
- tai_lieu ~584+ (A=58, B=367+, C=159); toan van ~46 ban / ~337 trang A4.
- 12 nguon trinh duyet BAT, 11 nguon requests BAT, nguon telegram BAT.
- CDP 9224 dang mo. X/Facebook trong PROFILE BOT CHUA dang nhap (tai khoan xa hoi
  kha nang o profile Chrome "User Data").
- Vl nhap: khong con loi; neu can LLM thi can cau hinh CLAUDE/OPENAI.

## Khi mo phien moi (checklist de lam tiep khong loi)
1. `python mo_chrome_cdp.py`  -> mo Chrome bot da dang nhap + CDP 9224 (neu chua co).
2. `python -c "import tru.seeker as S; S.mot_luot(600)"` -> mot vong SEEKER.
3. Doc `lab/GHI_NHO_LAM_VIEC.md` muc 7 (việc con) + AGENTS.md.
4. Viec con: gan CDP vao profile co phien dang nhap X/FB; noi "tu mo tai khoan"
   (dang_ky_alphavantage/twelvedata) + "search da ngon ngu" vao vong SEEKER;
   mo rong NGUON_TRINH_DUYET neu can.