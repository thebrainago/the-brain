# THE BRAIN V2 - KIEN TRUC CHUAN

*Chot theo y dinh cua chu he thong ngay 2026-08-16. Tai lieu nay co quyen uu tien
hon cac mo ta kien truc cu trong `lab/`.*

## 1. Muc tieu

The Brain la mot he thong nghien cuu va co van chay 24/7. He thong phai:

- thu du lieu va tai lieu co truy nguyen;
- bien dau vao thanh ung vien co hop dong may-doc-duoc;
- kiem dinh ung vien va tu tim edge tren hai lane doc lap;
- duy tri boi canh vi mo de co van chu he thong;
- tu do suc khoe, tu phuc hoi, sao luu va bao loi;
- khong danh dong "tien trinh dang chay" voi "ket qua dang tin".

Khong mot ket qua nao duoc phep tu dong giao dich tien that chi vi co nhan `PASS`.
Live execution la mot boundary rieng, chi duoc mo sau paper/live-shadow, tick test,
kill-switch va han muc von.

## 2. Nam tru va quyen so huu

### SEEKER - funnel

So huu: source registry, fetch, retry, raw immutable artifact, dedup, metadata,
license, relevance, provenance va hang doi ban giao.

Khong so huu: backtest, tinh chinh tham so, FDR, portfolio, allocation, live decay.

Dau ra duy nhat:

- `DocumentArtifact`
- `CodeArtifact`
- `TradeHistoryArtifact`
- `CandidateArtifact` neu chi la trich xuat co dan nguon, chua co verdict

### NGHI - theory generator tuy chon

NGHI tao `CandidateArtifact` tu tri thuc da truy nguyen hoac ly thuyet khai bao
truoc. NGHI khong duoc tu gan PASS va khong duoc cham holdout.

Neu khong co provider LLM rieng, NGHI o trang thai `DISABLED`, khong lap lai loi.

### QUANTLAB - hai lane

1. `candidate_validation`: nhan candidate tu Seeker/NGHI, kiem semantic tai san,
   dong bang analysis plan, tinh chinh tren train va xac nhan tren holdout sach.
2. `autonomous_discovery`: tu sinh gia thuyet bang template, thuat toan hoac ly
   thuyet; co ledger, universe, ngan sach FDR va holdout rieng.

Hai lane co queue/state/FDR rieng. Chung chi dung chung engine, cost model,
canary va schema ket qua. Khong duoc thu mot candidate hai lan duoi hai ten.

### BANKER - macro va advisory

So huu: du lieu vi mo point-in-time/as-of, freshness, revision/vintage, lich su
kien, regime co quy tac va bao cao co van tai chinh cho chu he thong.

Banker co the phat machine-readable regime cho Quantlab nghien cuu, nhung khong
tu dong bien mot nhan dinh vi mo thanh lenh giao dich.

### EVOLUTION - control va health

So huu: SLO, heartbeat, queue depth, stale data, drift, disk, backup/restore,
schema version, dead-letter, incident va de xuat sua. EVO khong duoc danh gia suc
khoe bang so PASS.

## 3. Hop dong va state machine

Moi artifact bat buoc co:

- `artifact_id`, `artifact_type`, `schema_version`;
- `source_uri`, `retrieved_at`, `published_at` neu co;
- `content_hash`, `producer`, `producer_version`;
- metadata JSON va chain provenance;
- raw payload bat bien hoac duong dan + hash den raw payload.

Candidate state:

`NEW -> TRIAGED -> PREREGISTERED -> TRAINED -> HOLDOUT_TESTED ->` 
`REJECTED | QUARANTINED | PAPER_CANDIDATE`

Khong co chuyen thang tu `NEW` sang `PASS`. Moi transition ghi append-only event.

## 4. Control plane 24/7

- Mot supervisor duy nhat, lock nguyen tu va PID/health check.
- Chay cac tru theo lane song song; moi tru toi da mot instance.
- CPU hard target: khong vuot 85% trong cua so do; chi launch job nang khi CPU
  duoi 75%. May hien tai 10 core/20 logical thread, giu it nhat 3 logical thread
  cho OS, SQLite, browser va recovery.
- Backpressure theo queue depth, disk free, DB latency va error rate.
- Process exit code va heartbeat payload deu la health signal. `rc=0` kem
  `chi_tiet.loi` van la failed run.
- Graceful shutdown, exponential cooldown, dead-letter va retry co gioi han.
- Tren Windows VPS: chay nhu service/Task Scheduler khong phu thuoc interactive
  login; restart-on-failure va log rotation.

## 5. Bao mat

- Secret khong nam trong Git; dung NTFS ACL/service account rieng tren Windows.
- Noi dung web la untrusted data. Moi model doc no phai khong co tool/file/shell
  permission, strict output schema va provenance validation.
- Khong bypass CAPTCHA/ToS, khong tu tao tai khoan ngoai khi chua co phe duyet.
- Khong tu dat lenh, rut/chuyen tien, doi credential hay gui thong diep ra ngoai.

## 6. Dieu kien san sang

### Research-ready

- artifact contract + provenance dat;
- hai Quantlab lane tach ledger/FDR/holdout;
- canary va mutation audit dat;
- backup/restore drill dat;
- supervisor dry-run 24h khong crash-loop, khong vuot CPU/disk guard.

### Paper-ready

- data snapshot bat bien;
- point-in-time macro va measured cost;
- walk-forward/purged validation phu hop;
- candidate qua tick test va khong co semantic mismatch;
- alert va kill-switch da dien tap.

### Live-ready

Chi sau paper period dinh truoc, capital cap, independent review va rollback.
Trang thai hien tai chua dat muc nay.

