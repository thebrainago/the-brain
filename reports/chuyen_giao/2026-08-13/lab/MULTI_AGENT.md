# THE BRAIN — MULTI-AGENT (4 vai / 4 tab)

> Cập nhật 2026-08-12. Cách vận hành hệ "The Brain" như 4 sub-agent song song:
> **CHUNG · SEEKER · QUANTLAB · BANKER**. Mỗi vai là 1 tab/tiến trình riêng, giao
> việc từng tab, chạy đồng thời để tăng tốc và dùng hết tài nguyên máy.

## 4 VAI & TRÁCH NHIỆM

| Vai | Vai trò | Sở hữu (ghi được) |
|---|---|---|
| **CHUNG** | Điều phối, tích hợp, giữ hệ sống, evolution | `roles/CHUNG.md`, `MULTI_AGENT.md`, `ke_hoach_mai.md`, tích hợp báo cáo |
| **SEEKER** | Quét nguồn 24/7, tìm chiến lược thực tế có lợi | `quan_li_quet.py`, `nguon_reddit.py`, `darwinex_ocr.py`, `nguon_telegram.py`, `nguon_youtube.py`, `nguon_kham_pha.py`, `keywords_nguon.py`, `seeker_cong_dong.py`, `telethon_ban.py`, `doc_cdp.py` |
| **QUANTLAB** | Nghiên cứu + backtest cơ chế (Python sàng lọc → MT5 sau) | `quant/` (script + `KET_QUA.md`) |
| **BANKER** | Vĩ mô (FRED, USD, VIX, COT), regime, brief | `banker.py`, `reports/banker_brief.md` |

## BẬT 4 TAB
Mỗi tab = 1 cửa sổ cmd chạy `codex` với prompt vai trò:
- `lab\TAB_CHUNG.cmd`
- `lab\TAB_SEEKER.cmd`
- `lab\TAB_QUANTLAB.cmd`
- `lab\TAB_BANKER.cmd`

Mỗi `codex` sẽ mở session riêng; dán nhiệm vụ vào tab tương ứng. Các tab độc lập — giao
việc khác nhau vào từng tab, rồi CHUNG gom kết quả.

## NGUYÊN TẮC PHỐI HỢP (không đụng nhau)
1. **Ranh giới quyền**: mỗi vai chỉ ghi file mình sở hữu (bảng trên). File chung (`bo_nao.py`,
   `thu_vien.db`, `brain_*.py`) thì đọc-only trừ khi CHUNG chỉ định.
2. **Không đụng DB lâu**: ghi `thu_vien.db` ngắn, commit ngay — `brain_daily.py --processes 10`
   có thể đang chạy.
3. **2 cổng ngặt duy nhất**: repaint + dòng mua-giữ. Rigorous ở cổng ra (nơi mất tiền),
   thoải mái ở cổng vào (khám phá).
4. **Không tự tinh chỉnh tham số đã đăng ký** (nguyên tắc khoá FDR trong `brain_daily.py`).
5. **Backtest phải có chi phí thật** (spread + swap) và so với buy&hold; đừng tin survey PF
   trước khi qua MT5 tick.

## TRẠNG THÁI HIỆN TẠI (2026-08-12)
- Pipeline `brain_daily.py --processes 10` đang chạy định kỳ (fetch dữ liệu → thu thập nguồn → chạy cơ chế CHƯA test → báo cáo).
- `quan_li_quet.py` đã có lịch: github, mql5, cong_dong, wccta, kham_pha, telethon, quy, social, youtube, telegram, banker, evolution.
- Đang nối thêm: reddit, darwinex (Seeker). Quantlab đang backtest 4 cơ chế. Banker đang test FRED + thêm COT.

## BACKLOG HÔM QUA (ke_hoach_mai.md + CAI_THIEN_BRAIN.md) — theo dõi
- [ ] Test MT5 thật Daily Zone gold TP=50 (ưu tiên 1 — cần vai CODER/MT5).
- [x] Quét backtest 4 cơ chế đáng giá (Quantlab) — kết quả `quant/KET_QUA.md`.
- [x] Nối + test nguồn mới reddit/darwinex (Seeker) — darwinex OK, reddit 403 phía server.
- [x] Hoàn thiện Banker FRED + COT (Banker) — `reports/banker_brief.md`.
- [ ] Pipeline --maynha / --vps (folder Drive chung lab_chung + MT5 tester thật).

## KẾT QUẢ 2026-08-12 (3 sub-agent song song)
- **SEEKER**: nối `reddit` (6h) + `darwinex` (12h) vào `LICH`. Test thật: darwinex lấy 1000 DARWIN (`reports/darwinex_darwins.json`); reddit bị 403 phía server (đã sửa code chống treo, chờ Reddit nới chặn).
- **QUANTLAB**: 4 cơ chế × 3 tài sản, trừ chi phí thật. Nổi bật: **Ichimoku Chikou+DI trên EURUSD vượt buy&hold** (27.8% vs 3.6%) → đưa lên MT5 tick trước. Đã phát hiện + sửa lỗi lookahead bias cơ chế B. Xem `quant/KET_QUA.md`.
- **BANKER**: FRED (DGS10/DFF/USD/VIX) + COT (CFTC) chạy thật, ghi `macro_brief` + `reports/banker_brief.md`. Regime hiện tại: neutural, spec S&P lệch SHORT nhẹ.

## VIỆC TIẾP THEO (đề xuất CHUNG)
1. Đưa Ichimoku Chikou+DI EURUSD lên MT5 tick (vai CODER viết EA / dùng EA khung).
2. Test MT5 thật Daily Zone gold TP=50 (ưu tiên số 1 còn nợ).
3. Theo dõi reddit khi server nới chặn; nếu cần thì thêm proxy/old.reddit.
4. Pipeline --maynha / --vps (folder Drive chung lab_chung + MT5 tester thật).
