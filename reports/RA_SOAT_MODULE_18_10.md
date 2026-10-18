# Rà soát chủ động mọi module (18/10/2026)

> Chủ dự án, 18/10: *"Phần seeker được thay đổi tốt đấy, nhưng nếu tôi không hỏi thì bao giờ mới sửa được, mà nếu vậy thì các module khác cũng còn đấy lỗ hổng mà có thể tôi không kiểm soát hết."*

> **Bản trong the-brain:** mọi sửa lỗi đã port sang đây, trừ những gì the-brain chưa có module: A5 (phí qua đêm theo nửa đêm, P3), A7 phần spread theo năm, và D1–D3 (`mt5tools/`). the-brain không có `mt5tools/` và `vong_thu_nghiem.py`.

Bốn đợt rà soát chạy song song, mỗi đợt chỉ đọc code (và chạy thử khi cần): **(1) cổng và bộ lọc**, **(2) gom nguồn và đọc mã**, **(3) chi phí và mô phỏng**, **(4) công cụ MT5 và vận hành**. Mỗi lỗi dưới đây được kiểm lại trên code trước khi sửa. Thước đo vẫn là ba yếu tố cốt lõi (`BO_TIEU_CHI_MOI.md`): lãi sau phí và giãn, sụt giảm ≤ 80 %, lãi ≥ 10 %/năm.

Trạng thái: **ĐÃ SỬA** (có test, đã commit cả brain2 và the-brain) · **CHỜ** (đã xác nhận, chưa sửa) · **CẦN CHỦ DỰ ÁN** (phải anh quyết) · **MÁY NHÀ** (cần dữ liệu hoặc MT5 ở máy nhà).

## A. Lỗi làm kết quả ĐẸP HƠN THẬT (nguy hiểm nhất: nhìn như hệ có lãi)

| # | Lỗi | Chỗ | Đo được | Trạng thái |
|---|---|---|---|---|
| A1 | **Tài khoản cháy vẫn báo thắng.** Bar cháy được gán hệ số 1, nên log bằng 0 | `nhan/mo_phong.py` `chay` | Đòn bẩy 3x, tăng rồi gap −40 %: vốn về 0 nhưng chỉ số báo **+284 %, sụt giảm 0 %** | ĐÃ SỬA |
| A2 | **Lệnh BÁN được cộng lãi ảo.** Cộng dồn kiểu log khiến lệnh bán ăn 1/x − 1 thay vì 1 − x | `mo_phong.chay` (mặc định), `chay_tpsl`, `chay_dung_trong_bar`, `chay_he` | Chuỗi drift 0, biến động 17,5 %, luôn bán: **+3,41 %/năm** ảo (đúng là +0,18 %) | ĐÃ SỬA (cả 4 engine) |
| A3 | **SL bị gap vẫn khớp đúng giá SL** | `mo_phong.chay_tpsl` | SL 98, mở cửa 90: ghi lỗ 2 % thay vì 10 % | ĐÃ SỬA. Còn `vao_lenh.py:292`, `dap_quan_tri.py:174`: CHỜ |
| A4 | **Spread giờ rollover không bao giờ bị tính.** Giờ 23 và 0 bị loại khi đo rồi lấp bằng spread giờ thường | `nhan/chi_phi.py` `do_spread` | Rollover rộng 5–9 lần; mọi lệnh khớp lúc 00:00 (H1/H4) được giá rẻ | ĐÃ SỬA: đo cả giờ 23/0; bar ngày lấy spread của giờ khớp thật (2 giờ, như EA V24). Bộ đệm `config/chi_phi_do.json` phải đo lại: MÁY NHÀ |
| A5 | **Phí qua đêm tính sai kiểu.** Lệnh trong ngày vẫn trả phí; lệnh H1 qua đêm chỉ trả 2/24 đêm, không có ngày x3 | `chi_phi.MoHinhChiPhi.kieu_qua_dem` | | ĐÃ SỬA: mặc định "nửa đêm" như MT5 (`BRAIN_QUA_DEM=lien_tuc` để về bản cũ) |
| A6 | Swap hôm nay áp cho cả lịch sử | `chi_phi.tu_du_lieu` | Short US500 2011–21 được +0,67 %/năm, thật ra phải trả ~3 % | MÁY NHÀ: cần dữ liệu lãi suất lịch sử (trên cloud chỉ có EURUSD). `vong_thu_nghiem` đã có `ap_thoi_ky` |
| A7 | **Bài stress "phí x2" không làm gì.** Sai tên khoá nên bản x2 giống hệt bản gốc; spread theo năm triệt tiêu hệ số | `nhan/sang_loc.py` `_nhan_doi_chi_phi`, `chi_phi.bien_the` | Stress x2 ra x1 | ĐÃ SỬA |
| A8 | ATR nhìn trước (dùng `atr[i+1]`, gồm cả biên độ nến vào lệnh) để đặt SL/TP | `dap_quan_tri.py:113`, `vao_lenh.py:190` | ATR biết lúc tín hiệu 1,00, dùng 1,643 | ĐÃ SỬA |
| A9 | `mo_phong_v2.py` gắn cứng thông số EURCAD (pip, giá trị pip, swap) cho mọi mã | `mo_phong_v2.py:38-49` | Cặp JPY hoặc vàng ra lãi ảo ~100 lần | ĐÃ SỬA: `thong_so()` đọc point, hợp đồng, phí qua đêm hai chiều từ `config/chi_phi_do.json`, quy đổi sang USD; thiếu thì báo lỗi |
| A10 | Thông số symbol còn đoán ở nhiều nơi (USDCNH point 1e-5 thay vì 1e-4; JP225 trong `_diem_tu_gia`; hợp đồng 100.000 cho mọi mã trong `ro_mql.py`) | nhiều file | | CHỜ: cần một bảng symbol chung |
| A11 | 56 symbol đứng ở spread đúng 1,0 bps (giá trị dự phòng im lặng) | `chi_phi.py:837` | USDARS, TRYJPY, GBPTRY… | CHỜ |
| A13 | `dap_quan_tri.dap` không kiểm SL/TP trong chính nến vào lệnh (bắt đầu từ nến sau) và cộng lãi kiểu log cho lệnh bán | `nhan/dap_quan_tri.py:150-190` | | CHỜ (tìm thấy khi viết test A8) |
| A12 | Không mô phỏng ký quỹ / stop-out cho kiểu không SL, DCA, hedge (trừ `chay_he` có `tai_khoan`) | `mo_phong_v2`, `vao_lenh`, `dap` | | CHỜ, liên quan thiết kế (mục D) |

## B. Lỗi LOẠI NHẦM hệ có lãi (trái ba yếu tố cốt lõi)

| # | Lỗi | Chỗ | Trạng thái |
|---|---|---|---|
| B1 | Hệ đạt cốt lõi trên chuỗi nghiên cứu nhận `UNG_VIEN`, mà không bước nào phía sau nhận `UNG_VIEN` → kẹt vĩnh viễn (lỗi của tôi ngày 17/10) | `nhan/cong.py` | ĐÃ SỬA → `CO_CO_CHE` (đi tiếp sang CFD của sàn) |
| B2 | Nhìn lại holdout và `t_alpha > 5` vẫn hạ PASS ở chế độ lợi nhuận | `cong.py` | ĐÃ SỬA: thành nhãn, MT5 tester phân xử |
| B3 | **Sàng thô của quantlab** vẫn đòi thắng mua-giữ cả tổng lãi lẫn Sharpe, bỏ cặp "không đo được MDE" (80/233 cặp), bỏ ứng viên Sharpe < MDE, giữ 3 cái theo Sharpe | `tru/quantlab.py` `kham_pha`, `kham_pha_theo_mau` | ĐÃ SỬA: chế độ lợi nhuận chỉ hỏi cốt lõi trên train, xếp theo lãi/sụt giảm, giữ 10; MDE thành nhãn |
| B4 | Phép thử "phạm vi lớp tài sản" bỏ cả mẫu chạy đều trên cả lớp | `quantlab.py:713` | ĐÃ SỬA ở quantlab (thành nhãn). `sang_loc.py:410`, `gop_lop.py:440`: CHỜ |
| B5 | **Hệ luôn có lệnh nhưng đảo mua/bán bị coi là "mua-giữ trá hình"** (đo bằng `|tín hiệu|`, không phân biệt chiều) | `sang_loc.py:246`, `loc_co_che.py:88/277`, `to_hop.KICH_HOAT` trần 0,60 | ĐÃ SỬA: đo tỉ lệ ở CÙNG MỘT CHIỀU; `loc_co_che` đếm cả lật chiều; trần `to_hop` 0,98 |
| B6 | `quan_tri.loc` bỏ spec chỉ có lưới / DCA / martingale | `nhan/quan_tri.py` | ĐÃ SỬA |
| B7 | `to_hop`: mỗi chân phải thắng mua/bán-giữ và tiền mặt ở CẢ HAI NỬA; mọi luật phải có SL; chân DCA bị gắn SL 2 ATR; thoát cưỡng bức theo `giu` | `nhan/to_hop.py` | CẦN CHỦ DỰ ÁN + Grok: đây chính là kiểu giao dịch của anh (không SL, DCA, giữ), phải thiết kế lại cùng mô phỏng kiểu chủ dự án |
| B8 | `chon_ung_vien` đòi ≥ 8 năm dữ liệu, chi phí đo được, ≤ 8 bps từ D1 | `nhan/ho_so_symbol.py` | CHỜ |
| B9 | `noi_sinh` mặc định chỉ sinh hệ MUA (`chieu=1`) | `nhan/noi_sinh.py` | CHỜ |
| B10 | Ngữ pháp từ chối khai báo có `co_che` < 25 ký tự, `sltp` bắt buộc SL, `giu` ≤ 500 | `nhan/ngu_phap.kiem_khai_bao` | CHỜ (SL bắt buộc: thuộc mục D) |
| B11 | Báo động "> 5 PASS/ngày" và hiệu chuẩn null sẽ kêu khi cổng nới | `tru/evolution.py`, `hieu_chuan_null` | CHỜ: đổi thành nhãn ở chế độ lợi nhuận |

## C. Lỗi GOM NGUỒN (mất phần quý nhất: xử lí lệnh)

| # | Lỗi | Chỗ | Trạng thái |
|---|---|---|---|
| C1 | Seeker đào ở nguồn học thuật; không tìm KHO; đọc repo chỉ 6 file | `tru/seeker.py` | ĐÃ SỬA 17–18/10 (`san-kho`, `tai-kho`, `kiem-ke`, ký hiệu mã) |
| C2 | Xếp hạng tải: EA quản trị −40, chỉ báo −50 → xếp cuối | `nhan/xep_hang_ung_vien.py` | ĐÃ SỬA: +30 khi mã có ký hiệu xử lí lệnh |
| C3 | Đọc toàn văn bỏ qua `backtest/`, `StrategyTester/`, không đọc `.mqh`/`.cs` | `nhan/toan_van.py` | ĐÃ SỬA |
| C4 | Truy vấn coi "manager", "indicator" là công cụ (hạ ưu tiên) | `nhan/truy_van_seeker.py` | ĐÃ SỬA |
| C5 | **Thông tin xử lí lệnh không bao giờ vào kho cơ chế**: 0/4.049 cơ chế có trường quản trị; khoá trùng (`ngu_phap.py:2604-2613`) bỏ qua phần quản trị; lời nhắc `boc_llm` chỉ hỏi vào/ra; `doc_ma` cắt EA thành mảnh mua-giữ-1-nến; mới dịch 85/2.378 EA (3,57 %) | `ngu_phap`, `boc_llm`, `doc_ma` | CẦN CHỦ DỰ ÁN + Grok: cần một khối "quản trị" trong DSL (thiết kế) |
| C6 | `quan_tri.boc_kho` chỉ đọc bảng `artifact`, khớp input đầu tiên (`bool UseTrailingStop` thắng), nhầm đơn vị (SL tiền thành pip, point thành pip) | `nhan/quan_tri.py` | CHỜ |
| C7 | `goi_github` giới hạn 16 EA/repo và chỉ giữ file có `OnTick` → bỏ hết chỉ báo; `bo_nao._cao_github` chỉ đọc nhánh master/main và đệm vĩnh viễn | `nhan/goi_github.py`, `bo_nao.py` | CHỜ |
| C8 | Giải mã dự phòng sang UTF-16 làm rác file cp1252/cp1251 | bộ đọc mã | CHỜ |
| C9 | `ma_nguon.thu_thap` lỗi TypeError khi một trang danh sách hỏng; `tai_mql5_goi` báo ok khi hỏng hết | `nhan/ma_nguon.py` | CHỜ |
| C10 | `seeker_quet_nguon`: con trỏ/đóng dấu 168 giờ; 271 repo GitHub và 69 kênh Telegram chưa đọc | | MÁY NHÀ |
| C11 | `boc_llm` chỉ nhìn 3×N artifact mới nhất, bỏ mã < 800 ký tự | `boc_llm` | CHỜ |

## D. Công cụ MT5 (thẩm phán cuối cùng phải đáng tin)

| # | Lỗi | Chỗ | Trạng thái |
|---|---|---|---|
| D1 | **Đòn bẩy bị bỏ qua**: viết `Leverage=30`, tester cần `1:30` → cả 58 báo cáo thật đều 1:100 | `mt5tools/chay_lien_tuc.py`, `chay_lai_tren_san.py`, `chay_xu_li_lenh.py`, hai `.ps1` | ĐÃ SỬA + đọc lại đòn bẩy trong báo cáo |
| D2 | **Lần chạy hỏng bị đánh dấu "đã thử" vĩnh viễn**; không có hạn thời gian mỗi việc (terminal treo thì không bao giờ commit sổ cái); 0 lệnh trong 20 giây được ghi như kết quả thật | `chay_lien_tuc.py`, `sinh_viec.py` | ĐÃ SỬA: thử lại tối đa 2 lần, hạn 1.800 s, `CHUA_DO_DUOC` |
| D3 | **Đọc báo cáo CŨ và .ex5 CŨ như kết quả mới** (tên báo cáo cố định, không xoá; kiểm "có .ex5" chứ không kiểm "mới hơn"); sửa `.mqh` không bao giờ tới slot | `chay_xu_li_lenh.py`, `chay_lai_tren_san.py` | ĐÃ SỬA. Khoá sổ cái chưa có phiên bản EA: CHỜ |
| D4 | Sổ XM không có swap (tài khoản `#` tắt swap FX/kim loại) và pha IS 0 % tick thật | `reports/mt5_lien_tuc/so_cai.jsonl` | CẦN CHỦ DỰ ÁN: chạy lại trên sàn của anh (`chay_lai_tren_san.py`) trước khi gọi là "đạt" |
| D5 | D1 trong `chay_tester_kho` (Period=D1, Model=2): chỉ số CFD không khớp được lệnh | `chay_tester_kho.py:133` | CHỜ |
| D6 | Log agent trỏ thư mục dữ liệu CŨ (656C3515) → "cannot generate history data" lọt qua như 0 lệnh | `chay_tester_z5.py:199` | ĐÃ SỬA: theo thư mục dữ liệu đo được, quét mọi agent, chỉ đọc log sau lúc bắt đầu chạy |
| D7 | `taskkill /IM terminal64.exe` giết cả terminal đang giao dịch và 4 slot; khoá không nguyên tử, hết hạn 45 phút < 3.600 s | `nhan/khoa_tester.py` | CHỜ |
| D8 | Exness giờ máy chủ GMT+0, code giả định giờ XM (rollover 00:00) | `BRAIN_XuLiLenh.mq5`, `do_phi_san.py` | CHỜ |
| D9 | Lỗi logic `BRAIN_XuLiLenh` (rổ theo comment, tài khoản netting chỉ cảnh báo, chờ sau khi đóng rổ) | `ea_demo/BRAIN_XuLiLenh.mq5` | CHỜ (EA là đích cuối, chưa làm tiếp) |
| D10 | Trailing V24 có thể không thoát khi stop mới vượt giá | `BRAIN_V24_Chung.mqh:160` | CHỜ |

## E. Pháp lý: mã của người khác đang nằm trong git công khai

`reports/_ea_mau.json` (24 EA), `reports/ea/kho.json`, `reports/quan_tri_cap/*_GOC.mq5`, `reports/DE_QT_EA Snippets_*.mq5`, `mau_thu/EA Snippets_*.mq5`, `mau_thu/mql5-pro_assets_EA_Template.mq5`. `.gitignore` không chặn `.mq4/.mq5/.mqh` trong `reports/`, và `b luu` / `b ket` dùng `git add -A`. **CẦN CHỦ DỰ ÁN**: bỏ theo dõi các file này thì lần `git pull` ở máy nhà sẽ xoá chúng khỏi ổ (lịch sử git vẫn còn). Tôi chưa làm gì.
