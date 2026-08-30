# THIẾT KẾ QUY TRÌNH BACKTEST 24/7 (ENGINE)

> Ngày: 2026-08-12 · Quyết định kiến trúc khâu giữa (sau khâu đầu vào của Seeker/EVO).

## A. Phân chia + tần suất 24/7
| Tầng | Kích hoạt | Tài nguyên |
|---|---|---|
| Thu thập (Seeker/EVO) | lịch cố định 2h-12h theo nguồn | nhẹ, 1 tiến trình |
| Sàng nhanh Vòng 1 | event-driven (có chiến lược mới) | song song 19 nhân |
| Vòng sâu + MT5 | queue (chỉ chiến lược qua V1) | 2-3 tune MT5 song song, còn lại chờ |

## B. Nền tảng code
- Python = nguồn sự thật (sàng nhanh + kiểm định + đa cặp).
- Port sang MQL5 CHỈ khi qua hết cổng kiểm định (MT5 tick + demo).
- Pine/TradingView: chỉ để đọc/trích chiến lược.

## C. Cặp tiền đại diện
- Chiến lược cụ thể (EUR/vàng) -> dùng đúng cặp.
- Chiến lược tổng quát -> bộ 5 đại diện:
  SP500 (chỉ số) · XAU (kim loại) · EURUSD (major FX) · GBPUSD (cross) · BTC-USD (crypto).
- Yêu cầu: edge trên >=3/5 mới coi là tổng quát.

## D. Khung + thời lượng
| Vòng | Khung | Thời lượng | Lý do |
|---|---|---|---|
| V1 sàng nhanh | H4 hoặc D1 | 3 năm | đủ bull+bear+1 chu kỳ lãi suất, ~780 nến, mili-giây |
| V2 xác nhận | H1 | 5 năm | walk-forward, tham số ổn định |
| V3 MT5 tick | tick | 3-5 năm | khớp lệnh/trượt giá/swap thật |

## E. MT5 đa nhiệm
- Nhiều terminal /portable -> backtest song song, nhưng giới hạn RAM/ổ cứng.
- Máy 32GB: chạy 2-3 tune song song, còn lại queue theo ưu tiên.
- Python = song song 19 nhân; MT5 = queue 2-3 tune/đợt.

## F. Cổng ra (gate)
- C0 Seeker: lọc ngôn ngữ + 5 rules.
- C1 Python H4/D1 3n, 5cặp: chống lookahead + placebo(p<0.05) + era.
- C2 Python H1 5n: walk-forward, tham số ổn định, đủ mẫu (>=30 lệnh).
- C3 MT5 tick: khớp lệnh/trượt giá/swap thật, giữ edge sau chi phí.
- C4 Demo: tài khoản demo thật 4-8 tuần.
- C5 Live: chỉ khi chủ quyết định.

## G. Cần dựng tiếp
- Gate runner (bo_kiem_dinh): tự đưa chiến lược qua C0->C4, xếp hàng MT5.
- Queue chiến lược (SQLite) + ưu tiên theo điểm.
- Trình điều khiển nhiều terminal MT5 /portable (2-3 tune song song).


## H. HUONG QUANT SÂU (2026-08-12, theo ý chủ): TÌM QUY LUẬT CƠ
Mục tiêu KHÔNG phải "test vài cơ chế xem edge". Mà: MỔ XẺ mọi loại tài sản x mọi giai đoạn
để tìm QUY LUẬT CƠ (primitive/structural law) lặp lại xuyên tài sản và xuyên thời đại.

### H1. Vũ trụ tài sản x giai đoạn
- Nhiều lớp tài sản: FX major/cross, chỉ số, hàng hóa (vàng/vàng), crypto, trái phiếu/lãi suất,
  volatility (VIX), carry.
- Nhiều timeframe: M1-M5-H1-H4-D1-W1.
- Nhiều regime/giai đoạn: bull/bear/sideways, low/high-vol, QE/tightening, khủng hoảng,
  chia theo decade (2000/2010/2020) để test độ ổn định theo thời đại.

### H2. Bộ quy luật cơ (primitive laws) cần đo
- Momentum/trend persistence theo độ trễ k (tự tương quan tại k; độ dốc giá).
- Mean-reversion tại cực trị + volatility clustering (GARCH).
- Phản ứng thừa/thiếu bất đối xứng (over/under-reaction).
- Seasonality: ngày trong tuần, tháng, dịp lễ, phiên giao dịch.
- Lead-lag xuyên tài sản: lãi suất->FX, USD->hàng hóa, VIX->risk.
- Phụ thuộc regime: cùng tín hiệu ĐẢO DẤU theo regime (quan trọng nhất).
- Chuỗi tự tương quan, kurtosis, phân bố lợi nhuận.

### H3. Đo "quy luật" chứ không phải "chiến lược"
Với mỗi quy luật x asset x timeframe x regime:
  - đo effect size, mức ý nghĩa (placebo), 
  - CONSISTENCY: quy luật hiện diện trên bao nhiêu asset (%),
  - ERA-STABILITY: còn đúng ở 2000 vs 2010 vs 2020 không.
=> Output: BẢN ĐỒ QUY LUẬT (law map): quy luật nào là cấu trúc bền, đúng ở đâu (asset x regime).
Chiến lược = tổ hợp các quy luật ĐÃ XÁC NHẬN (không phải cơ chế tự chế).

### H4. Điều kiện regime
- Dùng BANKER (macro regime) + volatility regime để biết QUY LUẬT ĐANG HOẠT ĐỘNG khi nào.
- Cùng 1 quy luật có thể ĐÚNG ở regime này, SAI ở regime khác -> gated theo regime.

### H5. Hệ quả kiến trúc
- Cần DỮ LIỆU RỘNG: nhiều asset/tf -> nối với auto-registration nhiều provider + IBKR/Dukascopy tick.
- Module mới: quant/khao_quy_luat.py (pattern-mining engine) tách khỏi auto_kham_pha.
- auto_kham_pha (=test cơ chế) chỉ là lớp STRATEGY, KHÔNG phải lớp khám phá quy luật.
- Ensemble (ket_hop_hoc) hoạt động trên QUY LUẬT đã xác nhận, không phải trên cơ chế ad-hoc.
