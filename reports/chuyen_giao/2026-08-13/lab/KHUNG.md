# KHUNG — đặc tả quy trình vận hành THE BRAIN (bản code theo đuổi)

> File này là CHUẨN DUY NHẤT cho code điều phối (`bo_nao.py`) và mọi pha sau.
> Đọc kèm: `THE_BRAIN.md` (thư mục cha) · `prompts/cac_vai.md` (8 vai + schema) ·
> `PROMPT_DEEPSEEK.md` (playbook + 8 bẫy) · `hang_doi.py` (lớp đồng bộ 2 máy).
> CAP NHAT khi quy trình đổi; code phải bám đúng file này, không bám file cũ.

## 1. MÔ HÌNH LÕI: BẢNG CÔNG VIỆC (task queue)
Mọi hoạt động của The Brain là một dòng trong bảng `cong_viec` (SQLite, `thu_vien.db`).
Orchestrator KHÔNG "chạy một vòng linear" — nó bơm task, các vai rút task tương ứng,
làm, ghi kết quả, và SINH task con. Không bao giờ chờ một LLM; queue luôn đầy.

### Bảng `cong_viec`
| cột | ý nghĩa |
|---|---|
| id | TEXT khóa chính (bam của nội dung đầu vào) |
| vai | scout / extractor / reverser / surveyor / mapper / judge / optimizer / coder / test |
| muc_id / co_che_id | nối tới bảng `muc` / `co_che` |
| trang_thai | CHO -> DANG -> XONG \| LOI \| BO |
| uu_tien | số nguyên, cao chạy trước |
| input_json | một chuỗi JSON (đầu vào của vai) |
| output_json | một chuỗi JSON (kết quả, đúng schema vai) |
| loi | chuỗi lỗi cuối (nếu LOI) |
| tao_luc / xong_luc | timestamp REAL |
| so_lan_thu | số lần thử (tối đa 3 rồi BO) |

### Vòng đời trạng thái
```
         tao           rút về        thành công
        ┌─────┐  lấy  ┌──────┐  ghi ┌──────┐
        │ CHO ├──────►│ DANG ├─────►│ XONG │
        └─────┘       └──────┘      └──────┘
             ▲            │LOI (thử ≤3)   SINH task con ở đây
             │            ▼
             │        ┌──────┐  
             └────────│ LOI  │──quá 3 lần / vô nghĩa──► BO
                      └──────┘
```
Quy tắc: mỗi task gắn với MỘT vai, MỘT đầu vào. Task con sinh ra khi task cha XONG.

## 2. CÁC VAI (điều phối bởi bo_nao.py)
Prompt đầy đủ từng vai nằm trong `prompts/cac_vai.md`, schema JSON ở đó là BẮT BUỘC.
`test` là vai PYTHON (không phải LLM): chạy MT5 tester rồi tự ghi kết quả.

| vai | LLM? | đầu vào | đầu ra (luôn JSON) | sinh task con khi |
|---|---|---|---|---|
| scout | có | 1 mục vừa cạo | lien_quan, loai, uu_tien | XONG → extractor (nếu lien_quan) |
| extractor | có | toàn văn 1 mục | MẢNG co_che (mỗi cái có diem) | mỗi cơ chế diem≥8 → surveyor |
| reverser | có | thống kê passview | MẢNG luật | luật → surveyor |
| surveyor | có | 1 luật/cơ chế | phep_do, tai_san_ung_vien | python chạy phép đo → mapper |
| mapper | có | cơ chế + input EA | anh_xa_duoc, cau_hinh[] | test (nếu anh_xa_duoc) / coder (nếu không) |
| test | KHÔNG | 1+ cấu hình .set | PF, loi, dd, sharpe, lenh | judge |
| judge | có | bảng kết quả + mốc | THAT/AO/CHUA_RO + ly_do | CHUA_RO→optimizer; THAT→kiểm chéo |
| optimizer | có | cấu hình + kết quả + chang | ≤6 cấu hình tinh chỉnh | test (vòng tiếp) |
| coder | có | mô tả cơ chế không ánh xạ | mã MQL5 + chỗ chèn | (bàn giao viết EA) |

## 3. LUỒNG CHÍNH (một cơ chế từ nguồn thô → kết luận)
```
 [cao] nguồn --> scout --> extractor --+--> (passview?) --> reverser --> surveyor
                                       +--> surveyor <-------------------------+
                                                 mapper --(ánh xạ được)--> test(mốc) --> judge
                                                          (cần EA mới)                    | (vòng)
                                                       coder --> biên dịch --> test      CHUA_RO --> optimizer
                                                                                          v
                                                                                    THAT --> KIỂM CHÉO (2 cặp + walk-fwd)
                                                                                             --> cập nhật MỐC
```
- `test(mốc)`: mọi cụm test phải kèm 1 cấu hình MỐC để đối chiếu (JUDGE so với mốc).
- Mốc hiện tại: `moc` id=1 (EURCAD ema50-2atr dl4000, PF 1.71, dd 3194, 559$/năm).

## 4. HAI LỚP: VPS vs MÁY NHÀ (đồng bộ qua thư mục chung)
Xem `hang_doi.py` — đây là lớp đồng bộ, KHÔNG tách riêng 2 phiên DB.
- **VPS** (`--vps`): cao nguồn → scout → extractor → surveyor → mapper → xếp `hang_doi_test.jsonl`.
- **MÁY NHÀ** (`--maynha`): đọc `hang_doi_test.jsonl` → test MT5 → JUDGE → optimizer →
  kiểm chéo → cập nhật MỐC → ghi `ket_qua_test.jsonl`.
- Mỗi máy CHỈ GHI file của riêng nó (append-only); máy kia chỉ đọc. Không conflict.
- DB `thu_vien.db` có thể ở cả hai máy; bên nào xử lý vai nào thì ghi bảng tương ứng.
  (Đơn giản nhất: VPS chỉ phụ trách `muc`+`co_che`+task sinh; máy nhà tự cập nhật kết quả test.)

## 5. ĐỊNH NGHĨA "XONG" (definition of done — không đổi)
1. Mọi kết luận cuối đều có số MT5 tester THẬT trên M1 toàn bộ lịch sử.
2. Đọc PF/Sharpe TRƯỚC %/năm. PF < 1,10 = nghi ngờ đòn bẩy/ảo.
3. Vốn = sụt giảm đường vốn, không phải mức dừng lỗ.
4. Không nhận lot (martingale) trừ khi backtest 13 năm THẬT chứng minh.
5. Chống khớp nhiều bắt buộc: kiểm chéo cặp + walk-forward trước kết luận THAT.
6. Chỉ nguồn công khai + passview tự nguyện.
7. Kiểm disk trước mỗi loạt test lớn; dọn cache khi Free < 20GB.

## 6. NGÂN SÁCH TOKEN
- Mỗi lần gọi LLM, `bo_nao.py` đọc `usage` từ API và cộng dồn vào `nhat_ky_token` (JSON).
- Ghi mỗi vòng: `{ngay, vong, token_vao, token_ra, tong}`.
- Không để vai nào chạy mù — nếu một vai trả lỗi JSON 3 lần liên tiếp → BO và ghi lý do.

## 7. THỨ TỰ TRIỂN KHAI (khung này được dựng theo thứ tự)
1. ✅ `KHUNG.md` (file này) — quy trình chuẩn.
2. ✅ Nâng DB: bảng `cong_viec` + handler nhan/tra task (trong `bo_nao.py`).
3. ✅ `bo_nao.py`: điều phối 8 vai theo task, đọc prompt từ `prompts/cac_vai.md`, parse JSON, sinh task con.
4. ✅ Tách `--vps` / `--maynha` và nối `hang_doi.py` (mapper ở VPS ghi vào `hang_doi_test.jsonl`; máy nhà test + tạo judge).
5. ✅ Nhật ký token (`reports/nhat_ky_token.json`) + chế độ `--kho` không API.

> CẬP NHẬT 2026-08-10: đã nối DeepSeek qua box API (`config.toml`), chạy trọn chuỗi thật sinh `co_che`
> (xem `HANDOFF.md` mục 3c). Đã dựng phép đo SURVEYOR bằng Python (`khao_sat_daily_zone.py`),
> thêm cache `noi_dung` + khoá đơn phiên `bo_nao.lock` + watchdog `BrainWatchdog`.
> Còn lại: nối survey Python tự vào pipeline (hiện chạy tách) và tích hợp CODER tự biên dịch EA.


## 8. CÁCH CHẠY KHUNG (bo_nao.py)
```
python bo_nao.py --xem                 # xem hang doi + thong ke
python bo_nao.py --them <url>          # cao 1 url -> task scout
python bo_nao.py --dan --so 24         # cao nguon (mql5+github) -> them scout tasks
python bo_nao.py --nhip 3              # chay 3 nhip (can DEEPSEEK_API_KEY)
python bo_nao.py --vps --lien-tuc      # may VPS: cao->rut->mapper -> hang_doi_test.jsonl
python bo_nao.py --maynha --lien-tuc   # may nha: hang_doi -> test -> judge -> moc
python bo_nao.py --kho                 # liet ke task LLM dang cho (khong ton API)
python bo_nao.py --trang-thai            # trang thai truc tiep (reports/trang_thai.json)
python khao_sat_daily_zone.py            # survey Python co che #1 (can pythoncore-3.14-64)
python test_bo_nao.py                  # mo phong LLM: kiem tra ca chuoi 8 vai (PASS)
```
Luu y moi truong: dung python co `requests` (venv `sp500_env` hoac `pythoncore-3.14-64`);
KHONG dung `C:\Python314` (thieu requests/pandas/certifi).

## 9. NGUỒN + CÁCH TEST (quyết định 2026-08-10)
- **Nguồn**: tuân theo `NGUON.md` (5 bậc ưu tiên). Bậc 1 = người giỏi đã xác minh;
  bậc 2 = nơi thấy hiệu quả thật (sàn đấu/xếp hạng/prop leaderboard/copy-signal/chỉ số quỹ);
  bậc 3 = thư viện code; bậc 4 = quan điểm; bậc 5 = passview lung tung (không ưu tiên).
- **SOURCE LOOP**: định kỳ tự tìm "người giỏi mới" (top trader năm, champion, prop mới,
  CTA/quant mới), xác minh năng lực trước rồi mới vào pipeline; ghi `reports/NGUOI_GIOI.md`.
- **PHẠM VI TEST**: không giới hạn vài tên/indicator — quét rộng variants × tham số
  (mọi kiểu EMA, BB cải tiến, ...). NHƯNG **bắt buộc lọc tự động**:
  mỗi lô quét kèm walk-forward (nửa đầu/nửa sau) + kiểm chéo ≥2 cặp; tổ hợp overfit
  bị loại bằng code (`loc_tu_dong`), không đưa vào thư viện. Chạy 24/7 không giới hạn ngân sách.
- Không "chạy mù tất cả không lọc" — chi phí thật là OVERFIT, không phải token.
