# GOI VIEC: TRAM MAY NHA + THO MODEL RE (29/09/2026)

Phien cloud [DOC], nhanh `claude/autonomous-trading-system-rzzt7h`. Chu du an duyet: "phan ro viec +
vua tinh tren cloud va may nha ... goi duoc model gia re de uu chi phi".

## 1. Da lam gi

- `nhan/tram.py` (`b tram`): may nha KEO viec qua GitHub (phien cloud khong voi toi may nha). Hop thu
  = ban clone rieng; cloud ghi `tram/viec/<id>.json`, tram chay trong thu muc lab THAT (du lieu, MT5,
  nao.db), ghi `tram/ket_qua/<id>.json` (trang thai, ma thoat, 200 dong cuoi log, file `reports/` moi,
  phien ban ma) roi day. DANH SACH TRANG trong MA: tram ping, nc so-tay/kiem/bot/tu-lai/tho/cc, test,
  vao, ban-do, kien-truc - doi so kiem tung o, khong shell. Khoa luot (Task Scheduler 5 phut khong
  chong nhau), het gio -> HET_GIO, dung khan tai may / tu xa.
- `nhan/nc_tho.py` (`b nc tho`): model re chuan OpenAI (DeepSeek mac dinh) chay vong KHAM PHA voi 12
  cong cu kham_pha + ghi so tay; `thu_luoi`/`ghep_danh_muc` bi ep ve kham_pha; gia thuyet/cau hoi mang
  nguon 'tho'. Khoa: cc-switch (may nha, dung chung `qwen/mo_hinh`) hoac bien moi truong (cloud).
  Tram dung `goi_re` nen ket qua thanh <= 12 dong cho Claude doc (log tho van giu).

## 2. Bang chung

`test_tram.py` + `test_nc_tho.py`: 26 qua - danh sach trang (9 lenh qua, 11 lenh la bi chan, ke ca
`AUDCAD;del *`), vong khu hoi cloud -> tram -> cloud qua git that (repo bare tam), viec la -> TU_CHOI,
het gio -> HET_GIO, dung khan + khoa, tho tu choi `niem_phong`, ep `doan` ve kham_pha, danh dau nguon.

## 3. Rui ro con lai

1. `nc cc` mo ca 16 cong cu (ke ca niem_phong) cho viec tu cloud - co y: ky luat nam TRONG cong cu
   (niem phong mot lan, dem phep thu). Ai co quyen ghi kho = giao duoc viec -> giu kho PRIVATE.
2. Het gio chi giet tien trinh con truc tiep; tien trinh chau (vd terminal64.exe) co the con song.
3. `tom_tat_re` co the chep sai so -> Claude doc tom tat truoc, nghi thi doc `duoi_log`.
4. Hop thu dang la nhanh cua phien nay. Muon mot nhanh CO DINH cho moi phien (vd `tram`) thi chu du an
   cho phep phien cloud day len nhanh do.

## 4. Viec chua lam

1. May nha: Git + `gh auth login`, them provider DeepSeek vao cc-switch, `b tram cai URL NHANH`, dat
   Task Scheduler (lenh in ra luc cai), giao thu `b tram giao tram ping`.
2. Lenh `b nc tester`: tieu hang doi `reports/nc_hang_doi_tester.jsonl` qua lan MT5 tester (roi them
   vao danh sach trang).
3. So sanh chi phi / chat luong: tho (DeepSeek) vs Claude tren CUNG cau hoi, cung so tay.
