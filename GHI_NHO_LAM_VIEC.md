# GHI NHO LAM VIEC - THE BRAIN V2

Checkpoint: 2026-08-16 23:43 (Asia/Saigon).

Day la ho so bat buoc doc dau phien. Kien truc chuan nam trong
`../KIEN_TRUC_THE_BRAIN_V2.md`; tai lieu kien truc cu chi co gia tri lich su.

## 1. Trang thai an toan khi nghi

- `lab/DUNG_LAI` dang ton tai voi noi dung
  `THE_BRAIN_V2_MAINTENANCE_2026-08-16`.
- Khong co supervisor/watchdog The Brain dang chay.
- KHONG xoa `DUNG_LAI` va KHONG chay `BAT_DAU.bat` cho toi khi hoan tat cac muc
  Quant V2 o phan 5.
- Claude/Anthropic da nghi su dung. `config/tri_tue.json` dang `duong=tat`;
  `nhan/tri_tue.py` khong con fallback Claude/CLI. Neu sau nay bat AI ngoai, chi
  bat OpenAI bang cau hinh ro rang, schema chat, han muc chi phi va worker co lap.

## 2. Kien truc da chot

- SEEKER: funnel thu thap, raw artifact, dedup, metadata, provenance va ban giao.
  Khong backtest, khong tu xep PASS, khong goi LLM trong `mot_luot()`.
- NGHI: theory generator tuy chon; chi sinh candidate, khong cham holdout.
- QUANTLAB co hai lane doc lap:
  `candidate_validation` va `autonomous_discovery`.
- BANKER: vi mo point-in-time/freshness va co van tai chinh ca nhan; khong tu dat
  lenh giao dich.
- EVOLUTION: control + health; khong danh gia suc khoe bang so PASS.

### COT LOI CHUA HOAN TAT

Muc tieu dau-cuoi bat buoc cua he thong la:

`nguon web/trinh duyet -> raw artifact -> trich claim co dan nguon -> CandidateArtifact
-> DSL/template an toan -> QuantPlan dong bang -> train/backtest/confirmation -> bao cao`

Checkpoint hien tai CHUA chay tron vong nay. SEEKER moi tu thu thap duoc mot phan
nguon requests/Telegram/CDP va tao artifact; browser worker chua tu xu ly ben vung
toan bo nguon JS/login, 140 ban ghi van khong doc duoc. Tang bien kien thuc thanh
candidate/DSL va noi sang QuantPlan/backtest cung chua hoan tat.

SEEKER khong truc tiep viet ma tuy y hoac tu cham diem backtest. No van la dau vao
tu dong cua day chuyen; buoc bien claim thanh DSL/template thuoc candidate compiler
/NGHI, va QUANTLAB la noi dong bang ke hoach, chay engine va phan quyet. Tach nhu
vay de noi dung web khong the chen ma/prompt vao may va de cung mot tru khong vua
sinh gia thuyet vua tu cong nhan no.

## 3. Da hoan tat trong phien 16/08

- Them contract artifact bat bien va bang `artifact`, `candidate_queue`.
- SEEKER da backfill 156 `DocumentArtifact`; 140 ban `khong_doc_duoc` duoc bo qua
  dung nghia. Vong chinh khong con BOC/LLM/Quant bridge cu.
- Control plane 3 worker/3 lane, Windows Job Object hard cap 85%, CPU launch
  guard, named mutex, lease atomic, live/ready/health probe va watchdog restart.
- Ledger `ghi_su_kien` dung `BEGIN IMMEDIATE`; kiem hash mac dinh toan chuoi;
  trung `ma` nhung doi plan bi chan.
- Sua interval phi giu lenh, tang `CP.THE_HE=3` va regression test.
- Sua look-ahead extrema phien trong `mau.py` va regression test.
- BANKER da can as-of/freshness cho chuoi cap; vintage point-in-time that van la
  viec con.
- 8 gia thuyet cu da `QUARANTINED_V2` va co ket qua moi `INVALIDATED` de bao toan
  lich su.
- Them `nhan/ket_qua_hoat_dong.py`; dashboard, NGHI va EVOLUTION chi doc ket qua
  moi nhat con hieu luc. Trang thai DB doc gan nhat: 346 active, tat ca la FAIL.
- Backup truoc V2:
  `lab/backups/nao_pre_v2_20260816_231236.db` (quick_check OK).
- Backup dung phien:
  `lab/backups/nao_checkpoint_v2_20260816_2343.db` (16.355.328 byte,
  integrity_check OK). Chuoi ledger nguon: 1.699 dong lien mach.

## 4. Checkpoint code vua dung

Hai agent Quant/FDR bi dung theo yeu cau nghi may sau khi da ghi code:

- `nhan/quant_plan.py` va `tru/quantlab.py`: da co phan khung QuantPlan/hai lane.
  `py_compile` dat, nhung agent chua kip chot bao cao va chua co test QuantPlan
  rieng. BAT BUOC doc diff logic va bo sung test truoc khi coi la hoan tat.
- `nhan/cong.py` va `test_cong_fdr_v2.py`: da co FDR V2 dang phat trien. Test hien
  tai xanh, nhung BAT BUOC ra soat migration/tuong thich voi QuantPlan va DB that
  truoc khi mo scheduler.
- `nhan/tri_tue.py` va `config/tri_tue.json`: Claude da bi loai khoi runtime;
  external AI van tat.

Lenh kiem tra cuoi phien (chay tu thu muc `lab`) dat 31/31:

```powershell
& 'C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m unittest test_so_concurrency_v2 test_dieu_phoi_control test_hop_dong test_seeker_artifacts test_banker_v2 test_mau_v2 test_chi_phi_v2 test_ket_qua_hoat_dong test_cong_fdr_v2
```

Luu y: 31 test nay chua bao phu day du luong `quant_plan.py` moi.

## 5. Thu tu lam tiep ngay mai

1. Hoan thanh mot vertical slice that: SEEKER tu mo mot nguon trinh duyet, luu raw
   artifact/provenance, trich mot claim, tao CandidateArtifact, bien thanh
   DSL/template an toan, dong bang QuantPlan va chay backtest den verdict nghien cuu.
2. Rasoat `quant_plan.py` + `quantlab.py`, them test cho hai lane, scope/applicability
   va policy `NEEDS_SCOPE`/holdout da lo.
3. Rasoat `cong.py` FDR V2: moi frozen plan cham confirmation tieu mot slot;
   dedup theo economic plan; epoch co lane/family/data release/decision generation;
   khong reset theo quy.
4. Noi `candidate_queue` vao candidate lane; khong tu quet 6 FX khi candidate
   thieu asset/timeframe.
5. Chay full regression + `nhan/canary.py --tu-kiem`, integrity/hash chain va
   backup/restore drill.
6. Chay control plane dry-run khi van giu tien that va AI ngoai o trang thai tat.
7. Sau do moi xoa `DUNG_LAI`; muc tieu dau tien la research-ready, chua live-ready.

## 6. Blocker truoc production/VPS

- Holdout 60/40 cu da bi lo cho vong sinh gia thuyet; chi duoc coi exploratory.
- Hai lane Quant chua duoc chung minh tach state/FDR/data release end-to-end.
- Data/cost provenance con co nguy co tron venue va current swap voi lich su.
- BANKER chua co vintage store point-in-time day du.
- Secret van la plaintext trong `lab/config`; `.gitignore` da chan nhung can rotate
  khoa va chuyen sang secret store/service account truoc khi VPS production.
- Script Scheduled Task VPS da co (`CAI_CONTROL_PLANE_VPS.ps1`) nhung chua cai.
- Can dry-run 24 gio va paper/live-shadow truoc khi nghi den tien that.

## 7. Moi truong

- Repo: `C:\Users\SV STORE\Downloads\Research SP500`
- Python dung:
  `C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- Khong dung WindowsApps Python hoac `C:\Python314`.
- `git` khong co tren PATH trong phien nay; phai so sanh file bang cong cu khac
  neu can audit diff.
