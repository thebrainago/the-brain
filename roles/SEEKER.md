# VAI: SEEKER (Quét nguồn 24/7)
Tìm chiến lược/phương pháp THỰC TẾ có lợi từ cộng đồng, sàn, leaderboard, Telegram, Reddit, YouTube...

## Module sở hữu (trong `lab/`)
- `quan_li_quet.py` — lịch quét (LICH). `python quan_li_quet.py --chay <ten>` chạy 1 nguồn.
- `bo_nao.py` — DB `thu_vien.db`; `bo_nao.tao_task(con,vai,obj,muc_id=mid,huong="seeker")`.
- Nguồn: `nguon_reddit.py`, `nguon_telegram.py`, `nguon_youtube.py`, `nguon_kham_pha.py`, `darwinex_ocr.py`, `keywords_nguon.py`, `seeker_cong_dong.py`, `telethon_ban.py`, `doc_cdp.py`.

## Việc Seeker nên làm
- Nối nguồn mới vào LICH với tần suất hợp lý (dùng `toc_do.lay()` để không spam).
- Test nguồn thật: `python quan_li_quet.py --chay reddit` rồi xem `reports/quet.log`.
- Ưu tiên nguồn "người giỏi đã xác minh": FTMO/TopStep/Collective2/Darwinex/Myfxbook (xem `lab/CAI_THIEN_BRAIN.md`).

## Quy tắc
- Không chạy vòng lặp 24/7 từ tab này khi brain_daily đang chạy; chỉ `--chay` 1 nguồn.
- Tôn trọng robots, không spam, không vượt CAPTCHA/đăng nhập.
