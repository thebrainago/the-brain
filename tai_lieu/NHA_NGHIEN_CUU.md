# NHÀ NGHIÊN CỨU — thiết kế lại The Brain để AI nắm quyền nghiên cứu

*25/09/2026 · theo yêu cầu của chủ dự án · mã: `nhan/nc_*.py` · lệnh: `b nc` · sổ tay: `nc.db`*

> Chủ dự án: *"Cái tôi cần là 1 hệ thống — 1 bộ não — 1 người thay tôi mổ xẻ và nghiên cứu
> phương pháp, thử nghiệm đủ các tham số và kiểu kết hợp. The Brain là công cụ và các phương án
> cho cậu. Phần thực thi chính và suy luận chính phải do AI nắm quyền."*
>
> *"Tại sao có nhiều AI tự trade, tự học hỏi từ lệnh đúng lệnh sai mà còn ra được quy tắc vào
> lệnh, mà chúng ta có sẵn một bộ công cụ cực mạnh chỉ đi tìm kiếm những thứ sẵn có?"*

---

## 0. Trả lời ngắn

**Vì The Brain được xây như một cái PHỄU, không phải một NHÀ NGHIÊN CỨU.** Phễu đổ tài liệu vào,
bóc cơ chế, thử mỗi cơ chế một lần, loại 99,87% ngay chặng đầu — và **không có khâu nào hỏi
"lệnh thắng khác lệnh thua ở đâu"**. AI trong phễu chỉ là lao động bóc tách giá rẻ (qwen-flash),
còn việc "nghiên cứu cái gì tiếp theo" nằm ở chủ dự án và ở những bảng việc viết tay.

Những "AI tự học" ngoài kia có đúng hai thứ The Brain thiếu: **học từ KẾT QUẢ** (nhãn của từng
lệnh, lợi suất phía trước) thay vì từ tài liệu, và **vòng lặp kín có trí nhớ** (đặt giả thuyết →
thử → xem vì sao sai → sửa). The Brain lại có thứ họ thường thiếu — engine khớp MT5, chi phí đo
được, cổng hai chiều — nên thiết kế mới **giữ nguyên các cổng bằng code** và đặt một vòng
nghiên cứu do AI nắm quyền lên trên.

Và có một con số giải thích vì sao "quét nhiều hơn" không cứu được (mục 5.3): cùng một edge
yếu, cùng dữ liệu — **dò rộng ~3.000 điều kiện tìm ra 3/8 lần, một giả thuyết có chủ đích tìm ra
8/8 lần** (báo động giả của phép thử đó trên nhiễu: 0/8). Giá trị của một bộ não nằm ở việc đặt
ÍT câu hỏi đúng, không nằm ở việc quét thêm.

---

## 1. Hiện trạng: ai đang nắm quyền gì

Đọc từ mã nguồn, không phải từ tài liệu mô tả:

| Quyết định | Ai nắm | Chứng cứ |
|---|---|---|
| Nghiên cứu hướng nào tiếp theo | **chủ dự án** (qua chat), ghi thành `VIEC_MAI_*.md`, `TON_VIEC.md` | "tỉa lệnh tinh vi hơn", "nâng lot", "AUDCAD" đều do chủ dự án đề ra |
| Việc máy tự chạy 24/7 | **bảng viết tay** `qwen/NHIEM_VU.json` (43 việc cố định) | `qwen/tac_tu.py`: *"Không có vòng lặp 'qwen tự nghĩ tiếp theo làm gì'"* |
| Lịch chạy các trụ | **đồng hồ** trong `dieu_phoi.py` (5 trụ, chu kỳ cố định) | bảng `TRU` — mỗi trụ một kịch bản cố định |
| LLM chạy ở runtime | **qwen3.7-flash** (rẻ nhất), chỉ để BÓC TÁCH | `config/tri_tue.json`: *"Claude và Anthropic đã được loại khỏi cầu nối runtime"* |
| Suy luận tạo cơ chế | trụ **NGHI**: 6 đề xuất / 90 phút | `tru/nghi.py` — chỉ thấy **đếm PASS/FAIL theo họ**, không thấy một lệnh nào |
| Chấm đạt/âm | **code** (`cong.py`, `cong_ra_tien.py`) | giữ nguyên, đây là phần đúng — nhưng **`cong.xet` đã gãy từ 18/09**: hai điều kiện tầng 2 chưa được xếp loại nên ở chế độ `nhan` (đang bật) mọi lần gọi ném `KeyError`. Test sẵn có bắt được, chưa ai sửa. Đã sửa trong gói này |

Lý do AI bị tước quyền được ghi rõ và **đúng về số đo**: *"một LLM không bộ nhớ ngoài sẽ lặp lại
việc cũ và chọn việc dễ"*. Nhưng kết luận rút ra đi sai hướng: cái thiếu là **bộ nhớ ngoài**, không
phải quyền quyết định. Tước quyền thì hệ không còn ai nghĩ; cấp bộ nhớ thì AI nghĩ được mà không lặp.

---

## 2. Chẩn đoán — năm lỗi thiết kế, mỗi lỗi có số đo

**L1. Vòng MỞ thay vì vòng KÍN.** Tài liệu → cơ chế → một phép thử → loại. Đo 13/09: chặng 1 chạy
162.330 ô, giữ 200 = **0,13%**. Cái bị loại không bao giờ được hỏi *vì sao* — kể cả khi ý tưởng
đúng một nửa và chỉ thiếu một điều kiện chế độ.

**L2. Không học từ lệnh.** `dap_quan_tri.dap` trả về danh sách lệnh; không module nào so lệnh
thắng với lệnh thua. Trước 25/09 **không có một dòng code nào** trả lời "lúc vào lệnh, lệnh thắng
khác lệnh thua ở đâu" — đúng cái mà các "AI tự học" làm.

**L3. Trọng tâm đặt vào thứ có sẵn.** 19 module THU THẬP; 12.078 tài liệu → **18 mẫu** (0,15%); kho ×6
→ ứng viên chạm cổng vẫn 21. Kiến thức công khai là nơi edge đã bị khai thác hết — và đo ra rồi.

**L4. Dò rộng tự ghìm công suất.** Mỗi điều kiện thêm vào cuộc dò nâng ngưỡng cho mọi điều kiện
khác. Đo trên chuỗi có đáp án (mục 5.3): 3/8 so với 8/8. Phễu quét hàng trăm nghìn ô chỉ còn
nhìn thấy những edge rất mạnh — mà edge rất mạnh hiếm khi tồn tại trên thị trường thanh khoản.

**L5. Thứ thật sự ra tiền đến từ vòng nghiên cứu thủ công.** Kết quả tốt nhất của lab (AUDCAD lưới
có tỉa lệnh, holdout +13,26%/năm DD −3,5%) đến từ: chủ dự án phản biện → Claude đo sóng → đặt tham
số → thử → sửa. Tức đúng vòng khoa học — nhưng do người điều khiển, và chỉ chạy khi có phiên chat.

---

## 3. Những "AI tự học" thật sự làm gì — và phần nào là thật

| Họ làm | The Brain trước 25/09 | Sau thiết kế này |
|---|---|---|
| Nhãn từ **kết quả**: lệnh thắng/thua, lợi suất h bar tới | nhãn từ tài liệu (ai đó viết về chỉ báo X) | `mo_xe_lenh`, `tim_quy_luat` |
| Tìm **điều kiện tách** thắng/thua (meta-labeling, cây luật, ML) | không có | tìm điều kiện 1–2 đặc trưng, **có null hiệu chuẩn cả việc dò** |
| Vòng lặp nhanh, có **trí nhớ** | mỗi phiên bắt đầu lại, trí nhớ nằm trong file .md cho người đọc | sổ tay `nc.db` máy đọc được; mỗi chu kỳ mở đầu bằng hồ sơ nghiên cứu |
| Tự chọn việc tiếp theo | bảng viết tay | AI chọn, theo giá trị kỳ vọng |

**Phần không thật:** phần lớn "AI tự học ra quy tắc" công khai là quá khớp + sống sót — một mô hình
học đủ lâu trên một chuỗi thì luôn "học" được. Vì thế thiết kế này **không** cho AI tự chấm: mọi
con số đi qua engine + chi phí thật + cổng tiền; đoạn niêm phong mở một lần; mọi phép thử bị đếm.
Và chính bộ công cụ mới đã phải qua hiệu chuẩn hai chiều trước khi được tin (mục 5) — nó đã bắt
được một lỗi làm báo động giả gấp 2,7 lần.

---

## 4. Thiết kế mới: đảo quyền điều khiển

```
   CHỦ DỰ ÁN (nhà tài trợ)          đặt mục tiêu · gửi ý tưởng: `b nc hoi "..."` · đọc sổ tay
        │
        ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ NHÀ NGHIÊN CỨU (AI)   nhan/nc_tac_tu.py                                   │
 │   đọc sổ tay → chọn câu hỏi → đặt giả thuyết → thí nghiệm → đọc kết quả  │
 │   → ghi hiểu biết + câu hỏi mới → chu kỳ sau                             │
 │   Claude API  |  Claude Code (`claude -p` / phiên chat)  |  tự lái (không LLM)│
 └───────────────┬──────────────────────────────────────────────────────────┘
                 │ 16 công cụ, JSON  (nhan/nc_cong_cu.py)
 ┌───────────────▼──────────────────────────────────────────────────────────┐
 │ ĐO & CHẤM (code, AI không tự viết kết quả)                                │
 │   nc_thi_nghiem: chạy hệ · quét + hình dạng · mổ xẻ · xác nhận · niêm phong│
 │   nc_mo_xe: tách lệnh · học từ lệnh · tìm quy luật · MFE/MAE→quản trị     │
 │   nc_dac_trung: 26 đặc trưng ngữ cảnh = toán hạng ngữ pháp                │
 │   nc_du_lieu: 3 đoạn, niêm phong · chuỗi TỔNG HỢP có đáp án               │
 │   nc_so_tay: giả thuyết · thí nghiệm · hiểu biết · câu hỏi · vòng         │
 └───────────────┬──────────────────────────────────────────────────────────┘
                 │ dùng lại nguyên vẹn
 ┌───────────────▼──────────────────────────────────────────────────────────┐
 │ LÕI CŨ: ngu_phap · mo_phong · dap_quan_tri · vao_lenh · cham_diem (trần DD)│
 │ chi_phi · du_lieu · cong (nhãn) · dich_mq5 → MT5 tester                   │
 │ Trụ cũ thành DỊCH VỤ: SEEKER tìm theo yêu cầu (`yeu_cau_seeker`),         │
 │ qwen bóc tách, EVO giám sát                                               │
 └──────────────────────────────────────────────────────────────────────────┘
```

**Ranh giới** (giữ đúng tinh thần `qwen/DOC_TRUOC.md`, chỉ đổi người ngồi ghế quyết định):

| | AI | Code | Chủ dự án |
|---|---|---|---|
| chọn nghiên cứu gì | ✓ | | gợi ý qua câu hỏi ưu tiên |
| đặt giả thuyết + giải thích ai trả tiền | ✓ | kiểm cú pháp | |
| chạy thí nghiệm | gọi | ✓ thực thi | |
| chấm ĐẠT/ÂM/CHƯA ĐO ĐƯỢC | | ✓ | |
| mở niêm phong | yêu cầu | ✓ một lần, tối đa 3/dòng | |
| rút bài học, câu hỏi tiếp | ✓ (ghi kèm bằng chứng) | kẹp độ tin nếu không có bằng chứng | đọc |
| tiền thật | | | ✓ luôn luôn |

### 4.1 Tám module mới

| Module | Vai trò |
|---|---|
| `nhan/nc_tac_tu.py` | Vòng tự chủ: hiến chương nghiên cứu (system prompt), vòng gọi công cụ, ngân sách công cụ/USD, nhật ký chu kỳ; driver Claude API và Claude Code headless |
| `nhan/nc_cong_cu.py` | 16 công cụ = một danh sách, ba cách gọi (API, `b nc cc`, Python) |
| `nhan/nc_so_tay.py` | Bộ nhớ dài hạn: 6 bảng, vân tay thí nghiệm (chạy y hệt = trả kết quả cũ, không tính phép thử), đếm phép thử theo DÒNG giả thuyết |
| `nhan/nc_thi_nghiem.py` | Chạy hệ + quản trị; **có lãi sau phí?** + CAGR tốt nhất với maxDD < 80% (mốc mua-giữ/bán-giữ chỉ là nhãn); quét + hình dạng; mổ xẻ; xác nhận; niêm phong với đòn bẩy chốt trước; danh mục |
| `nhan/nc_mo_xe.py` | Tách lệnh (kể cả phí thoát, lật chiều); học bộ lọc từ lệnh thắng/thua; tìm quy luật trên bar; MFE/MAE → luật quản trị; null hiệu chuẩn cả việc dò |
| `nhan/nc_dac_trung.py` | 26 đặc trưng ngữ cảnh viết bằng CHÍNH toán hạng ngữ pháp → luật tìm ra chạy thẳng trong engine, dịch được sang MQL5 |
| `nhan/nc_du_lieu.py` | 3 đoạn (khám phá 60% · xác nhận 20% · niêm phong 20%); 5 kịch bản chuỗi tổng hợp có đáp án |
| `nhan/nc_tu_lai.py` | Chương trình cố định không LLM: đường nền, bài kiểm tích hợp, hiệu chuẩn hai chiều |

### 4.2 Một chu kỳ nghiên cứu

1. **Đọc hồ sơ** (`tom_tat_md`): câu hỏi mở (của chủ dự án xếp trước), giả thuyết đang sống, thí
   nghiệm tốt nhất, hiểu biết có bằng chứng, phép thử đã tiêu theo mã.
2. **Chọn** 1–2 câu hỏi theo giá trị kỳ vọng (~70% đào sâu hướng có dấu hiệu, ~30% hướng mới).
3. **Giả thuyết** (`ghi_gia_thuyet`) + vì sao có người trả tiền cho phơi nhiễm đó.
4. **Thí nghiệm**: `ho_so_tai_san` → `tim_quy_luat` hoặc `thu_co_che` → `mo_xe_lenh` → biến thể
   (bộ lọc / quản trị) → `quet_tham_so` (hình dạng) → `xac_nhan` → `niem_phong` → `xuat_mq5`.
   Họ quản trị không cần tín hiệu vào (lưới, tỉa lệnh, nâng lot): `thu_luoi`.
5. **Ghi**: hiểu biết kèm id thí nghiệm, câu hỏi mới, trạng thái giả thuyết.
6. **Tóm tắt** 5–10 dòng → bảng `vong` + `reports/nc_vong/vong_NNNNN.md`.

### 4.3 Kỷ luật do code ép (AI không cần tự giác)

- **Ba đoạn.** `niem_phong` không đọc được bằng cửa thường (`DoanNiemPhong`). Một khai báo mở một
  lần; một dòng giả thuyết tối đa 3 lần.
- **Vân tay.** Đổi TÊN không phải phép thử mới; chạy lại y hệt không tính thêm phép thử.
- **Đếm phép thử theo dòng** (gốc + mọi hậu duệ) → nhãn Sharpe giảm phát ở niêm phong.
- **Ba trạng thái.** Ít lệnh / khai báo sai / chi phí KHAI → `CHUA_DO_DUOC`, không bao giờ `AM`.
- **Cổng = tiêu chí chủ dự án 25/09/2026**, nguyên văn: *"tôi không quan tâm martingale hay dca
  hay là phương pháp gì. Tôi trade đòn bẩy tôi chấp nhận rủi ro, chỉ cần có lãi và maxdd dưới 80%
  là ok"*. CHẶN chỉ còn: **có lãi sau mọi phí** (kỳ vọng lệnh > 0) và **maxDD < 80%** — ở niêm phong
  là maxDD ở **đòn bẩy chốt trên khám phá + xác nhận TRƯỚC khi mở** (chọn đòn bẩy trên chính đoạn
  niêm phong là nhìn trước) — cộng tính đúng của số (chi phí đo được, đủ lệnh). Trần 80% đọc từ MỘT
  nguồn `cham_diem.TRAN_SUT_GIAM`, dùng chung với `cong.py` (điều kiện 15), `cong_ra_tien`, `bang_he`.
- **Nhãn, không chặn** (`nhan_canh_bao`): không hơn mốc mua-giữ/bán-giữ ở cùng trần DD ("beta, chưa
  phải hệ"); tầng 2 kinh tế (RR thực tế < 0,2 = kiểu martingale/DCA; lãi ròng < 3× phí spread);
  **đuôi lỗ** (hệ lãi nhỏ nhiều lần lỗ lớn ít lần cần ≥ 3/q* lệnh, q* = RR/(1+RR), mới thấy được cú
  thua — thiếu thì ghi số lệnh cần, để AI đo trên đoạn dài hơn chứ không cấm); `cong.xet` (placebo,
  alpha) với `ghi_so=False`; Sharpe giảm phát.
- **Tiền đo thế nào**: `tien_duoi_tran` — tăng trưởng G(L) = Σ log(1 + L·x) lõm theo đòn bẩy L, nên
  "có lãi ở một mức đòn bẩy nào đó" ⇔ Σx > 0, và mức tốt nhất là min(Kelly, đòn bẩy chạm DD 80%,
  10). Không bao giờ báo CAGR ở đòn bẩy quá Kelly. Lưới: hệ số lot chạm trần tính CHÍNH XÁC trên
  đường equity (lãi lỗ tuyến tính theo lot).
- **Chuỗi tổng hợp** không bao giờ xuất MQL5; chỉ khai báo ĐẠT niêm phong trên mã thật mới xuất.

---

## 5. Bằng chứng — hiệu chuẩn hai chiều trên chuỗi có đáp án

`b nc kiem 30` → `reports/NC_HIEU_CHUAN.md`. Năm kịch bản, đáp án biết trước (`nc_du_lieu.KICH_BAN`):

| Kịch bản | Cài gì | Đáp án đúng |
|---|---|---|
| NHIEU | không có gì | không ĐẠT |
| HOI_QUY | IBS < 0,15 **và** biến động cao → bar sau trôi +0,5σ (đối xứng chiều bán) | ĐẠT |
| HOI_QUY_YEU | như trên, 0,3σ — sau phí t ≈ 2,3 | dùng đo công suất |
| LOC | sau cú đi 3 bar: biến động thấp → hồi, cao → đi tiếp | hệ gốc thua; mổ xẻ phải tìm bộ lọc |
| XU_HUONG | quán tính thật nhưng nhỏ hơn chi phí (**bẫy chi phí**) | không ĐẠT |

### 5.1 Học từ lệnh đúng/sai — câu hỏi của chủ dự án, trả lời bằng số

Hệ gốc "mua sau cú giảm 3 bar" (ý đúng một nửa). Mổ xẻ trên đoạn khám phá, rồi **chạy lại** hệ đã
lọc trên đoạn xác nhận chưa từng nhìn:

| Chuỗi | Bộ lọc tìm ra (đáp án: `atr_pv < 0,5`) | p_null | Kỳ vọng hệ gốc (xác nhận) | Kỳ vọng hệ lọc (xác nhận) |
|---|---|---:|---:|---:|
| LOC_1 | `atr_pv < 0,392` | 0,005 | −62,7 bps | **+16,0 bps**, hơn mốc |
| LOC_2 | `atr_pv < 0,392` | 0,005 | −15,8 bps | **+10,6 bps**, hơn mốc |
| NHIEU_1 | (tốt nhất `rsi2 < 9 và r5_z < −0,7`) | 0,64 | — | không tin |
| NHIEU_2 | (tốt nhất `kl_pv ≥ 0,79`) | 0,82 | — | không tin |

### 5.2 Công cụ đã bắt được lỗi của CHÍNH NÓ

Lần đo đầu trên 30 hạt nhiễu thuần: tỉ lệ `tim_quy_luat` báo p_null ≤ 0,10 là **26,7%** (phải ~10%).
Nguyên nhân: điểm số chia cho độ lệch chuẩn KHÔNG điều kiện, trong khi đặc trưng biến động dự báo
ĐỘ LỚN lợi suất (cụm GARCH) — tập con biến động cao có trung bình dao động rộng hơn, còn null xoay
vòng phá mất sự khớp đó nên null hẹp hơn thật. Sửa: chia cho độ lệch chuẩn của chính tập con.
Sau sửa: **p ≤ 0,05: 6,7% · p ≤ 0,10: 13,3%** (kỳ vọng 5% / 10%, trong sai số của 30 hạt).
Không có hiệu chuẩn hai chiều thì lỗi này sẽ sinh ra "phát hiện" biến động cao mãi mãi.

### 5.3 Vì sao "quét nhiều hơn" không phải lời giải — công suất

Cùng edge yếu (HOI_QUY_YEU, t ≈ 2,3 sau phí), cùng 8 hạt:

| Cách | Phát hiện | Báo động giả trên nhiễu cùng hạt |
|---|---:|---:|
| dò rộng `tim_quy_luat` (~3.000 điều kiện) | **3/8** | ~5% (mục 5.2) |
| **một giả thuyết có chủ đích** (1 phép thử) | **8/8** | **0/8** |

Edge mạnh (HOI_QUY 0,5σ): dò rộng tìm ra 4/4 với p = 0,005. Tức dò rộng chỉ thấy edge mạnh; edge
vừa phải — loại edge có thật trên thị trường thanh khoản — cần một người đặt ĐÚNG câu hỏi. Đó là
chỗ của một bộ não, và cũng giải thích vì sao phễu 162.330 ô ra rất ít.

*(Giả thuyết có chủ đích ở đây là đáp án đúng — AI không phải lúc nào cũng đoán đúng. Điểm rút ra
không phải "AI biết đáp án", mà là: mỗi giả thuyết tiêu công suất, nên giả thuyết phải ít và sắc.
Sổ tay đếm phép thử để con số này luôn nhìn thấy được.)*

---

## 6. Vận hành

```
b nc                          hồ sơ nghiên cứu — đọc TRƯỚC mỗi phiên
b nc hoi "ý tưởng / câu hỏi"  LUỒNG ƯU TIÊN của chủ dự án → đầu chương trình
b nc cc                       liệt kê 16 công cụ
b nc cc <tên> '<json>'        gọi một công cụ (hoặc @file.json)
b nc chay [--vong N]          chu kỳ bằng Claude API (0 = liên tục tới DUNG_LAI / hết ngân sách ngày)
b nc claude [--vong N]        chu kỳ bằng Claude Code headless (`claude -p`, chỉ mở quyền `b nc`)
b nc tu-lai AUDCAD H4         chương trình cố định không LLM
b nc kiem [30]                hiệu chuẩn hai chiều (30 = thêm đo báo động giả + công suất)
```

**Chọn driver:**
- Có gói Claude Code (đang dùng hằng ngày): `b nc claude --vong 0` — không tốn API riêng. Lệnh
  chỉ cấp `Bash(python b.py nc:*)`, `Read`, `Grep`, `Glob`: AI nghiên cứu được, không sửa mã.
- Có API key (`ANTHROPIC_API_KEY` hoặc `ant auth login`): `pip install anthropic` rồi `b nc chay`.
  Mặc định `claude-opus-5`, effort `high`, thinking adaptive, bật `fallbacks: "default"`
  (beta `server-side-fallback-2026-07-01`) để một lần từ chối nhầm không làm đứt chu kỳ.
- Không có gì: `b nc tu-lai MA KHUNG` — sổ tay vẫn lớn lên.
- Phiên Claude Code đang chat: CLAUDE.md "LUẬT SỐ 1" bảo phiên đó LÀ nhà nghiên cứu.

**Cấu hình** (tuỳ chọn, file mới `config/nha_nghien_cuu.json`, hoặc biến môi trường):

```json
{"mo_hinh": "claude-opus-5", "effort": "high", "cong_cu_moi_vong": 40,
 "usd_moi_vong": 6.0, "usd_moi_ngay": 30.0, "nghi_giua_vong_giay": 120}
```
`NC_MO_HINH`, `NC_EFFORT`, `NC_USD_NGAY`, `NC_CONG_CU_MOI_VONG`. Chi phí được tính từ `usage` của
từng request và cộng vào bảng `vong`; hết ngân sách ngày thì chu kỳ không khởi động.

---

## 7. Hệ cũ đổi vai thế nào

| Thành phần | Trước | Sau |
|---|---|---|
| SEEKER | quét mọi nguồn, 24/7 | **đóng băng quy mô**; tìm THEO YÊU CẦU của nhà nghiên cứu (`reports/nc_yeu_cau_seeker.jsonl` — cần nối vào `vuon_nguon`) |
| trụ NGHI | qwen, 6 đề xuất / 90 phút, mù lệnh | **được thay** bởi nhà nghiên cứu; giữ để tham chiếu |
| qwen `q` | chạy bảng viết tay | lao động bóc tách + việc MT5 dài; bảng việc có thể do nhà nghiên cứu xếp |
| `dieu_phoi.py` | 5 trụ theo đồng hồ | giữ nguyên trong gói này (xem 8.2) |
| cổng `cong.py` / `cong_ra_tien.py` | chặn thắng mua-giữ + tầng 2 | **thế hệ cổng 6**: chặn = có lãi sau phí + maxDD < 80% + tính đúng của số; thắng mua-giữ, tầng 2 → NHÃN; `cong.xet` làm nhãn ở niêm phong (`ghi_so=False`) |
| MT5 tester | đo thật | vẫn là trọng tài cuối: `xuat_mq5` → `reports/nc_hang_doi_tester.jsonl` |

---

## 8. Việc tiếp theo — và rủi ro còn lại

### 8.1 Rủi ro nói trước

1. **Hiệu chuẩn chạy trên chuỗi tổng hợp.** Nó chứng minh công cụ không nói dối trên chuỗi biết đáp
   án; nó KHÔNG chứng minh thị trường thật có edge. Chưa chạy một chu kỳ nào trên dữ liệu thật
   (dữ liệu và `nao.db` ở máy chủ dự án, không lên cloud).
2. **Một chu kỳ API chưa từng chạy với Claude thật** (không có khoá trên cloud). Vòng được kiểm bằng
   client giả lập (`test_nc_tac_tu.py`): gọi công cụ, trả đúng id, ngân sách, từ chối, cắt max_tokens.
3. **Luật quản trị chưa có đường dịch MQL5 trong `xuat_mq5`** — xuất phần VÀO, ghi quản trị vào hàng
   đợi. Nối `dich_mq5_qtvt` là việc riêng.
4. **Hệ quá thưa không xác nhận được trên 20% dữ liệu** (LOC: đúng cơ chế, 7 lệnh ở đoạn xác nhận →
   `CHUA_DO_DUOC`). Lời giải đúng theo LUẬT SỐ 0 là ghép nhiều mã/khung, không phải hạ ngưỡng lệnh.
5. **Chi phí API.** Opus 5 ~$0,5–2/chu kỳ ước tính; trần ngày mặc định $30. Claude Code headless
   dùng gói có sẵn.

### 8.2 Thứ tự làm (mỗi bước có tiêu chí xong)

| # | Việc | Xong khi |
|---|---|---|
| 1 | Trên máy chủ dự án: `b nc kiem` rồi `b nc tu-lai AUDCAD H4`, `EURGBP H4`, `XAUUSDM H4` | sổ tay có hồ sơ + quy luật + kết luận ba mã, dùng dữ liệu và chi phí THẬT |
| 2 | `b nc claude --vong 3` với câu hỏi ưu tiên của chủ dự án (tỉa lệnh AUDCAD) | ba chu kỳ có hiểu biết kèm bằng chứng; so với tự lái trên cùng mã |
| 3 | `thu_luoi` (bọc `nhan/luoi.py`) **đã có cho AUDCAD**. Còn: `luoi.py` nhận mô hình chi phí (đang ghim phí qua đêm AUDCAD) để mở cho mọi mã | AI tự tái lập +13,26%/năm AUDCAD trong sổ tay rồi thử bản tỉa tinh vi hơn; `thu_luoi` chạy được trên EURGBP |
| 4 | Gắn nhà nghiên cứu vào `dieu_phoi.py` như trụ `NHA_NGHIEN_CUU` (lane external), thay trụ NGHI | chạy 24/7 không người, nhịp tim trong `nao.db` |
| 5 | Nối `reports/nc_yeu_cau_seeker.jsonl` vào `vuon_nguon` | một yêu cầu của AI dẫn tới tài liệu mới |
| 6 | `xuat_mq5` dịch cả luật quản trị (`dich_mq5_qtvt`) | EA từ nhà nghiên cứu chạy tester Model=4 |
