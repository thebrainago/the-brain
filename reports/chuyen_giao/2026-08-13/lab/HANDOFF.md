# HANDOFF — Ban giao trang thai de tiep dien cong viec (Claude/DeepSeek doc la lam duoc)

> Muc dich: bat ky ai (Claude Code tren VPS, DeepSeek, hoac chinh ban sau nay) mo file
> nay len la biet NGAY dang o dau, phai lam gi tiep, khong can doc lai ca lich su.
> Cap nhat 3 muc "TRANG THAI HIEN TAI" moi khi ket thuc mot phien lam viec.

## 0. DOC TRUOC (bat buoc, theo thu tu)
1. `THE_BRAIN.md`      — kien truc 2 tang + 8 vai tro + luong task
2. `PROMPT_DEEPSEEK.md`— system prompt DeepSeek: PLAYBOOK ULTIMA + thang diem + 8 BAY
3. `prompts/cac_vai.md`— 8 prompt vai tro chi tiet
4. `README_LAB.md`     — cai dat + nguon + cach chay
5. File nay (HANDOFF)  — trang thai hien tai + viec tiep

## 1. HE THONG DA CHOT (khong lam lai)
- **He EURCAD "Ultima"**: EA `LuoiDoiXung.mq5`, entry **lech EMA50-2ATR**, luoi buoc 30
  / TP 20 tu gia TB / chot cap bien 4 / dung lo 4.000 (per 0,01 lot). Da qua kiem cheo
  cap (NZDCAD/EURGBP duong) + walk-forward (duong ca 2 nua). MOC hien tai: **PF 1,71 ·
  DD 16% · ~17,5%/nam tren von-rui-ro** (cau hinh dung lo 4.000).
- **V6**: he chi so My (US500 CFD), 8,6%/nam, chay tren XM cent.
- **DongDongTV**: BAY — DCA Am Duong am 100%, Session V3 ky vong ~0. Khong phan bo.
- Con so tin duoc chi tu **MT5 tester THAT**; mo phong Python da nhieu lan sai (thuoc do
  von, do phan giai D1 thoi 11,7 lan). Xem memory `mt5-tester-truoc-python-sau`.

## 2. KIEN TRUC 2 TANG (chia tai de re)
- **VPS ($3, F.VPS 1 Sale hoac F.VPS 2 $6)**: bot 24/7 + cao + DeepSeek rut co che +
  xep hang doi test. GHI `hang_doi_test.jsonl`, DOC `ket_qua_test.jsonl`.
- **May nha (20 luong, bat 2-5h/ngay)**: quet MT5 tester song song. DOC hang doi, GHI
  ket qua. JUDGE + kiem cheo + cap nhat moc.
- **Dong bo**: thu muc Google Drive chung. Code: `hang_doi.py` (da test chay dung).
  Nguyen tac: moi may chi GHI file cua rieng no -> khong the conflict.

## 3. TRANG THAI HIEN TAI  << CAP NHAT MUC NAY MOI PHIEN >>
- **Ngay cap nhat**: 2026-08-02
- **Dang o chang nao**: da xong he EURCAD; dang DUNG PHONG LAB de tu dong hoa viec tim
  he TIEP THEO. Lab moi chay duoc che do `--kho` (cao 38 muc that). Chua noi DeepSeek
  (chua co API key). Chua tach lab.py thanh `--vps` / `--maynha`.
- **Viec dang do**:
  - [ ] cai DeepSeek API key tren may nha, chay thu `python lab.py --vong 1` (co goi API)
  - [ ] chay het 1 vong that tren may nha cho hoan thien quy trinh (cao->rut->test->judge)
  - [ ] tach lab.py: che do `--vps` (cao+rut+xep hang) va `--maynha` (doc hang+test+judge)
  - [ ] noi `hang_doi.py` vao lab.py (thay vi chay tester inline)
  - [ ] thue VPS, chay `setup_vps.ps1`, noi Google Drive chung
- **Ket qua vong gan nhat**: (dien sau khi chay vong dau tien co DeepSeek)


## 3b. KHUNG MOI (bo_nao.py) — cap nhat 2026-08-10
Da dung khung dieu phoi theo dung 8-vai + bang cong viec (xem KHUNG.md):
- **`lab/bo_nao.py`**: orchestrator moi. Bang `cong_viec` (CHO->DANG->XONG/LOI/BO),
  dieu phoi scout/extractor/reverser/surveyor/mapper/judge/optimizer/coder, vai `test`
  chay MT5 qua `lab/mt5_worker.py`. Doc prompt rieng tung vai tu `prompts/cac_vai.md`.
- **`lab/mt5_worker.py`**: tach cac ham tester tu lab.py (viet_set/chay_tester/doc_tester).
- **Tach 2 lop**: `bo_nao.py --vps` (cao->rut->mapper -> ghi `hang_doi_test.jsonl`),
  `bo_nao.py --maynha` (doc hang doi -> test -> ghi ket qua -> tao judge). Da noi `hang_doi.py`.
- **Nhip token**: ghi `reports/nhat_ky_token.json` moi lan goi API.
- **Trai thai**: DB co 1 task scout CHO (muc MQL5 that, qua `--them`), `co_che` rong,
  chua co `DEEPSEEK_API_KEY` nen chua chay tron 1 chuoi 8 vai that.
- **Chay**: `python bo_nao.py --xem` | `--them <url>` | `--nhip 1` (can key) | `--vps` | `--maynha`.
- **Luu y**: dung python co du `requests` (venv `sp500_env` hoac `pythoncore-3.14-64`),
  KHONG dung `C:\Python314` (thieu requests/pandas/certifi).

## 3c. PHIEN 2026-08-10 (bo_nao.py noi DeepSeek + tu dong hoa) << DOC MOI NHAT
- **DeepSeek qua box API cong ty da noi**: `_cau_hinh_deepseek()` doc tu
  `C:\Users\SV STORE\.codex\config.toml` (provider `aibox`, `wire_api=responses`,
  model `deepseek-v4-flash`). `goi_llm` ho tro ca `responses` lan `chat/completions`.
  KHONG hardcode token vao code. Chay duoc: `bo_nao.py --lien-tuc` (daemon 24/7).
- **Khoa don phien**: `_giu_khoa()` dung file `bo_nao.lock` (O_EXCL chua PID),
  tu cuop lock chet. Tranh 2 daemon chay song song.
- **Cache noi dung**: bang `noi_dung` (muc_id,url,van_ban). `cao_url()` lay content
  MQL5 (mo ta that) va GitHub (API: README + file .mq5/.py/.set). scout/extractor
  dung chung cache -> khong cao lai.
- **Trang thai truc tiep**: `reports/trang_thai.json` (cong_viec/co_che/cache/hanh_dong
  cuoi). Xem: `bo_nao.py --trang-thai`.
- **Watchdog**: `lab/watchdog_brain.ps1` + scheduled task `BrainWatchdog` (moi 3 phut)
  tu khoi dong lai daemon neu chet. (Copy tai `C:\lab\watchdog_brain.ps1`.)
- **KET QUA PIPELINE THUC** (da chay that, co_che sinh ra):
  - co_che 1&2 tu EA "Daily Zone Recovery EA mql5/code/75922": Daily Zone breakout-
    return (diem 10), Test-lui-pha vung (8) -> mapper noi can EA survey rieng -> coder
    stub ghi KHONG_ANH_XA. co_che 3 ATR band filter (7). co_che 4 Regime Score Gate
    (ER/ADX/MA) tu "Trend Execution Planner" (8).
  - `reports/khao_sat_daily_zone.json` = survey Python co che #1 tren 6 tai san (M1/M5->M15/D1,
    recovery + MAE/ATR): xep hang EURCAD top (74 sig/nam, hoi 100%, MAE_p90 0.17 ATR);
    XAUUSD/GOLD 162 sig/nam nhung MAE sau hon; AUDNZD/EURGBP loai vi tan suat <30/nam.
    Script: `lab/khao_sat_daily_zone.py` (nhan ca M5).
- **Luu y**: daemon chay bang venv `sp500_env` (du requests/sqlite). Survey Python chay
  bang `pythoncore-3.14-64` (co pyarrow). Muon chay tham: `python bo_nao.py --them <url>`.

## 4. LAM GI TIEP
 (uu tien tu tren xuong)
1. Mai: cai DeepSeek + chay thu quy trinh tren MAY NHA cho tron mot vong. Sua bug
   (schema, JSON parse, tester path) cho den khi `--vong 1` chay het khong loi.
2. Khi may nha chay muot: tach 2 che do + noi hang_doi.py.
3. Thue VPS re, cai bot + lab-cao, noi Drive chung. Tu day he tu chay.
4. Moi co che THAT tim duoc -> viet vao muc "HE THONG DA CHOT" o tren + memory.

## 5. LENH NHANH
```
# kiem duong ong (khong ton API)
python lab.py --kho --vong 1
# chay that mot vong (can DEEPSEEK_API_KEY)
python lab.py --vong 1
# 24/7
python lab.py --lien-tuc --nghi 1800
# test co che dong bo 2 may
python hang_doi.py
# xem thu vien
python -c "import sqlite3;c=sqlite3.connect('thu_vien.db');[print(r) for r in c.execute('select ten,diem,phan_quyet,pf from co_che order by diem desc limit 20')]"
```

## 6. QUY TAC BAT BIEN (khong pha, o bat ky may nao)
- MT5 tester THAT truoc, Python chi sang loc khi gia thuyet qua moi.
- Doc PF/Sharpe truoc %/nam. PF<1,10 = nghi ngo ao.
- THAT chi khi PF>=1,15 + duong >=2 cap + duong ca 2 nua giai doan.
- Kiem disk truoc lo cao/test lon; don cache MT5 khi Free < 20GB.
- Chi nguon cong khai + passview tu nguyen.
- Chay lien tuc, khong hoi duyet (xem memory `lam-lien-mach-khong-cho-duyet`).
