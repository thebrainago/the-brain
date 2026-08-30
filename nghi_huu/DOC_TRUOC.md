# NGHI HUU — 2026-08-15

Cac file trong thu muc nay **da bi thay the**, khong con duoc goi nua.
Chung duoc GIU LAI (khong xoa) de doi chieu lich su va de lay lai neu can.

## Vi sao nghi huu

Bao cao `BAO_CAO_2026_08_15.md` do duoc: **tam bo dieu phoi chong len nhau**, moi
cai co state rieng, log rieng, lich rieng, va chung **da lech nhau that**:

- `brain_master.py` dinh nghia tru QUANT = `quant_offline.py`
- `the_thorn.py`    dinh nghia tru QUANT = `quant/auto_kham_pha.py`

Hai dinh nghia khac nhau cho cung mot tru — tuy cai nao duoc bat ma lab lam viec khac.

Ngoai ra `seeker_quy_tac.py` + `evo_giam_sat.py` chay **8.719 va 8.413 lan trong
5,3 gio**, moi lan 0,2-0,3 giay, doc lai mot file tinh roi ghi de mot bao cao —
tuc 63/64 luot CPU la vong lap rong.

## Thay bang cai gi

| Cu | Moi |
|---|---|
| brain_master.py + tru_worker.py + the_thorn.py + autopilot.py + vong_lap.py + quan_li_quet.py + brain_24h.py + watchdog_brain.ps1 | **`lab/dieu_phoi.py`** (mot dau moi, lich theo su kien) |
| seeker_quy_tac.py | **`lab/tru/seeker.py`** |
| quant_offline.py + quant/auto_kham_pha.py | **`lab/tru/quantlab.py`** |
| banker.py | **`lab/tru/banker.py`** |
| evo_giam_sat.py + evolution.py + evo_theo_doi.py | **`lab/tru/evolution.py`** |
| thu_vien.db + cac file `*_state.json` | **`lab/nao.db`** qua `lab/nhan/so.py` |
| quant/kiem_dinh.py + quant/metrics.py | **`lab/nhan/cong.py`** + `lab/nhan/do_luong.py` + `lab/nhan/chi_phi.py` |

## Canh bao

**Dung chay lai bat ky file nao trong day song song voi `dieu_phoi.py`.**
Chung ghi vao state cu, khong biet gi ve `nao.db`, va se lam sai lech so lieu
van hanh ma EVO dang do.

Cac task Windows cu (`BrainThorn`, `BrainWatchdog`, `BrainAuto`, `BrainSweep`,
`BrainMT5`, `BrainNudge`, `BrainTheoDoi`, `THE_BRAIN_daily`, `BrainBaoCao`,
`BrainDocForDs`) **da bi xoa** ngay 15/08 de chung khong tu thuc day.
