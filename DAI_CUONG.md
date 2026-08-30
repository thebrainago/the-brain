# THE BRAIN - DAI CUONG & BAN GIAO
Ngay cap nhat: 2026-08-14  ~  Huong dan quy hoach + ban giao dan

## 1) Kien truc 24/7 (multi-agent)
- `brain_master.py` = SUPERVISOR: spawn NHIEU worker song song cho 4 tru, giam sat + tu khoi dong lai khi chet. Chay qua task `BrainThorn` (keeper 5`).
- `tru_worker.py` = worker chung: chay task cua tru roi nghi theo duty-cycle de giam CPU dung % (config).
- `config/tai_nguyen.json` = cau hinh tai nguyen PORTABLE: `cpu_pct` (do ban), `song_song` (so worker song song), `min_duty_sleep`, `task`. **Chuyen may chi can sua file nay.**

## 2) 4 tru - trach nhiem + file
| Tru | Nhiem vu | File task | %CPU mac dinh |
|---|---|---|---|
| SEEKER | tim chien luoc/nguon/EA co hieu suat that | `seeker_quy_tac.py` | 15 |
| QUANT | **backtest** tren data M1 local + placebo, quet param grid | `quant_offline.py` (dung `mo_phong_v2.py`,`ichimoku_cross.py`,`cross_pair_quet.py`,`quant/*`) | 60 |
| BANKER | vi mo (COT/Fed/news) | `banker.py` | 10 |
| EVO | giam sat + de xuat giai phap | `evo_giam_sat.py` | 10 |

Note: QUANT + MT5(20) + du phong(5) => duoi 100. Intense (800-100%) chi khi VPS.

## 3) Task Lich Windows
- `BrainThorn`  5`  : chay `brain_master.py` (keeper tu khoi dong lai neu chet/reboot).
- `BrainNudge`  5`  : chay `tiep_tuc.ps1` -> bơm ASCII "tiep tuc" vao console codex (chong mat ket noi).
- `BrainAuto`  20`  : `autopilot.py` - tu chon vice kha thi (quet cap/ichimoku/mt5/evolution).
- `BrainMT5`  (intensive, gan theo disk) : `run_mt5_flag.py` - tick-test that tren MT5 (chinh dang KHOA vi disk<15GB).
- `BrainSweep` (intensive, tam Disable) : `quant_sweep.py 12` - param grid da nhan, CHI BAN VPS.
- `BrainWatchdog` + `THE_BRAIN_daily` (8:00) : goc du an.

## 4) Giam sat
- `reports/EVO_BAO_CAO.md`  : trang thai 4 tru + de xuat giai phap (EVO tu viet moi chu ky).
- `reports/worker_<TRU>.txt` : nhip tim tung tru. `reports/brain_heartbeat.txt`, `brain_master.log`.
- `reports/worker_log.jsonl`  : su kien task tung tru. `reports/tiep_tuc.log` : nudge.
- `reports/QUANTLAB_ICHIMOKU.md`, `reports/quant_sweep.json`, `reports/cross_scan_M1.json` : ket qua backtest.
- CPU: `config/tai_nguyen.json` - giam `cpu_pct`/`song_song` neu nong; datasets trong `../data/*_M1_mq.parquet` (KHONG xoa).

## 5) Quy hoach thu muc DICH (ban giao dan, lam khi TAT brain)
```
lab/
  core/          brain_master.py, tru_worker.py, tiep_tuc.ps1, evolution.py
  tru/           seeker_quy_tac.py, banker.py, evo_giam_sat.py, quant_offline.py
  quant/         (da gom: mo_phong, kanh, metrics, du_lieu, tin_hieu, kiem_dinh)
  khai_pha/      ichimoku_cross.py, cross_pair_quet.py, quant_sweep.py
  config/        tai_nguyen.json  (PORTABLE)
  scripts/       run_mt5_flag.py, autopilot.py, mt5_worker.py
  reports/       (kiem ke - chọn giu moi nhat, archive con lai)
  archive/       (da tao: gom temp/scratch/log rac)
Suggest no: KHONG move file dang chay. (Tai lieu nay giu anh xa file->vi tri moi.)"

## 6) Trang thai hien tai
- 4 tru song song OK, CPU cap ~40% (muc vua); nudge 5` OK (INJECT rc=0).
- Backtest = Python tren M1 local (khong can MT5). MT5 tick-test dang KHOA (disk<15GB).
- Tam ngo: MT5 verify cần disk; param-grid full chi VPS; them M15/H1 + thanh lap candidates.
