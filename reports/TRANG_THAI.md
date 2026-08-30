# TRANG THAI THE BRAIN (tu cap nhat)
Ngay: 2026-08-14 ~ 18:30

## Dang chay (24/7, Task Scheduler, doc lap chat)
- brain_master.py (supervisor) + GOVERNOR CPU (tu do CPU -> giu ~83%).
- 5 worker SONG SONG: SEEKER, QUANT(scan M1), BANKER, EVO(giam sat), COMPUTE(param grid qua nhieu nhan).
- worker heartbeats: reports/worker_<TRU>.txt ; governor: reports/brain_master.log, cpu_gate.txt.
- EVO report moi chu ky: reports/EVO_BAO_CAO.md (trang thai tru + van de + de xuat + da thuc thi).

## CPU & tai nguyen
- CPU do = ~33-77% tuy pha (muc truoc luc cap nhat nay ~12-25%). Governor target 83%.
- Goc quan trong: may nay (10 nhuan/20 threads) co xu huong `rc3221225786` (process init flaky) khi chay qua nhieu process. Do do config on dinh: COMPUTE(6 nhan)+QUANTx1+SEEKERx1. Muon cham 80-85% ben vung hon: ong config/tai_nguyen.json COMPUTE "10"->"12" + sUA khi may manh (VPS).

## Man hinh / cua so
- Da the CREATE_NO_WINDOW vao subprocess de het cua so cmd chup (sua 18:20).
- NUDGE da TAT (BrainNudge Disabled): trong TUI codex nay chi go duoc khong send duoc, nen bo de khoi lam ract het.

## Vi du / kiem tra khi quay lai
- Mo reports/EVO_BAO_CAO.md: co gi moi + de xuat.
- Xem worker_*.txt: tru nao con song.
- reports/brain_master.log: governor cpu/gate.
- data/*_M1_mq.parquet: 8 cap M1 (KHONG xoa). results: reports/quantlab_*, reports/quant_sweep.json.

## Chinh cau hinh khi can
- config/tai_nguyen.json: cpu_pct (duty), song_song (so worker), task, min_duty_sleep.
- GOVERNOR: brain_master.py --target 80-85.
