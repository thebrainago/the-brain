# Tóm tắt cách dùng 15 bot EA (từ phụ đề tự động của video)

Nguồn: `C:\Research SP500\lab\du_lieu_cao\drive_trade_an_lac\_video_phu_de\*.txt` (phụ đề tự động, nhiều lỗi nhận dạng giọng nói).
Quy ước: chỉ ghi điều có trong phụ đề; "không nói" = video không đề cập; chỗ phụ đề mơ hồ ghi rõ là mơ hồ. Mọi số liệu lợi nhuận/drawdown là LỜI NGƯỜI TRÌNH BÀY, chưa kiểm chứng. Đơn vị "ph" trong phụ đề được hiểu là "phần trăm" (suy đoán). "Giá" = đơn vị giá của vàng (1 USD/oz), "BP" = point/pip theo cách nói trong video.

---

## 1. Bigmouse Hedging (T91 hedging v2.2) - file Bigmouse.txt

1. Chiến lược: dạng hedging bằng lệnh chờ. Mở một lệnh Buy hoặc Sell (tay, hoặc chế độ auto tự mở Buy đầu tiên khi bật bot); sau đó bot đặt lệnh stop ngược chiều cách giá một khoảng ("khoảng cách buy/sell", ví dụ 350-360 point = khoảng 3,6 giá). Chạy được mọi khung (demo test M15), cặp vàng. Tín hiệu vào lệnh: không dùng chỉ báo, chỉ là lệnh đầu (tay/auto) + chuỗi lệnh stop ngược.
2. Quản lý lệnh: có tăng lot kiểu "hệ số nhân" (người trình bày test nhiều hơn) hoặc kiểu Fibo (chưa test). Logic: tổng lot một chiều luôn gấp 2 lần tổng lot chiều ngược lại trong 4 lệnh đầu; từ lệnh thứ 5 hệ số giảm còn 1,6 (không phải nhân đôi lot lệnh trước mà tính theo tổng). Lot đầu 0,01; giới hạn lot tổng 15; tối đa 36 lệnh (nói "tới 36 lệnh thì tài khoản không còn").
3. Thoát lệnh: (a) Trailing stop hoặc SL theo tỷ lệ RR (ví dụ 1,3 khoảng cách buy/sell); (b) "chốt lãi theo tổng" khi tổng lãi trừ phí đạt 5 USD (có thể chỉnh 10/15/20); (c) "cắt âm" khi âm X USD; (d) "kích hoạt hòa vốn": khi chuỗi đã đủ N lệnh (ví dụ 3) bot bỏ TP dương, chỉ đặt SL ở hòa vốn (demo: 4 lệnh, thoát đúng hòa vốn, balance 2020 giữ nguyên); (e) trailing stop: khi giá về hòa vốn rồi đi thêm 2 giá thì kéo SL về hòa vốn.
4. Tham số: khoảng cách buy/sell, commission (nên điền theo sàn, ví dụ XM khoảng 4 USD/lot), kiểu tăng lot, hệ số 2 và 1,6, lot đầu 0,01, max lot 15, max lệnh 36, bật auto + mở lệnh Buy đầu, giờ mở cửa (giờ sàn + 7 = giờ VN, ví dụ mở từ 23h sàn). Test minh họa: XAU, M15, vốn demo 2000-2020 USD. "Red event" không biết là gì (người trình bày nói không hiểu). Sàn: nhắc XM. Loại tài khoản, đòn bẩy: không nói.
5. Cài đặt: file bot chia sẻ trên kênh Telegram; video hướng dẫn chạy Strategy Tester (Ctrl+R, Visual mode). Cách nạp MT4/MT5, AutoTrading, VPS: không nói.
6. Cảnh báo/số liệu (lời người trình bày): bot "về bờ nhanh hơn nhưng drawdown tăng rất nhanh (del load)"; gồng lâu thì mệt; 36 lệnh thì hầu như cháy tài khoản. Số liệu demo: chốt 5 USD hai lần được 10 USD; không có số liệu dài hạn.

Độ tin cậy nội dung: vừa (logic hệ số và các chế độ thoát rõ, nhưng nhiều tên input bị nhận dạng sai).

---

## 2. EA Black Dragon MT5 V13 (vàng) - file BlackDragon.txt

1. Chiến lược: bot DCA hai chiều, bán trên MQL5 market (người trình bày nói là bản bán đại trà, nhận được bản không giới hạn). Setup minh họa cho vàng. Có chế độ Manual (Magic 0 để đánh tay) và Auto (Magic khác 0). Setup này KHÔNG dùng chỉ báo: vào thẳng Buy/Sell; khi đang có Sell mà giá tăng thì mở Buy (và ngược lại) theo khoảng cách. Có tùy chọn dùng tín hiệu kiểu stochastic nhưng không bật.
2. Quản lý lệnh: DCA cả hai chiều, tối đa 99 Sell và 99 Buy; lot đầu 0,01; có chế độ auto-lot (khoảng cứ 1000 vốn thì 0,01 - không dùng); có hệ số nhân lot (thấy lot nhảy 0,01 -> 0,02, 0,03, 0,04, 0,05, 0,07...; sau 5 giá có hơn 10 lệnh); TP dạng trailing "treo lên" (TP dịch dần). Có lọc tin tức nhưng không cấu hình (cần thêm link).
3. Tham số: step distance 400 (với sàn XM 3 số = 0,4 giá); hệ số giãn bước 1,2 (bước càng sau càng xa); max order 99; lot đầu 0,01; khung giờ hoạt động có input. Vốn gợi ý (lời người trình bày): 10k cent hoặc 20k cent. Loại tài khoản: cent (gợi ý); sàn XM.
4. Cài đặt: lấy bot + file .set chia sẻ trong nhóm Zalo/Telegram; chạy test trong tester; MT5. DLL/WebRequest/VPS: không nói.
5. Cảnh báo/số liệu (lời người trình bày): tự gọi setup này là "setup sổ số", DCA vàng 0,4 giá + nhân lot thì lệnh rất dày, "âm cả nghìn" ngay trong phiên Âu; nên chơi phiên Á/Âu, tránh phiên Mỹ; tác giả không khuyến khích chơi bot DCA nhiều. Số liệu (lời họ): vốn 10k cent, một ngày lãi khoảng 2k-3k (nói "28%" và "thu hồi vốn trong 3-4 ngày"); ngày đầu test lãi khoảng 30%. Các con số lẫn lộn, không đáng tin.

Độ tin cậy nội dung: thấp-vừa (phụ đề nhiều lỗi, số liệu và thông số lẫn lộn).

---

## 3. BNK.HBot - file BNK.txt

1. Chiến lược: DCA có "gồng dương đối ứng": không chốt lệnh đơn; DCA, và giữ một lệnh đang dương để cân đối với các lệnh âm (ví dụ 1 Buy dương 25 USD, 2 Sell âm, tổng âm chỉ 12 USD). Khi chốt thì chốt cả chuỗi rồi mở chuỗi mới. Cặp EURUSD (test), không nói khung thời gian, không nói tín hiệu vào lệnh (nói họ không đặt nặng entry).
2. Quản lý lệnh: DCA/lưới có hệ số lot 1,2; lot khởi điểm trong phụ đề ghi "0,1" (mơ hồ, có thể 0,01); lot lớn nhất thấy khoảng 1,85, tối đa khoảng 19 lệnh; SL/trailing: không nói.
3. Tham số: min lot, hệ số lot 1,2. Vốn gợi ý 20k (có thể 15k) để chịu năm biến động mạnh (2020-2021-2022). Tài khoản cent: 200 USD thì ăn khoảng 100 USD/năm (lời họ). Sàn, đòn bẩy: không nói.
4. Cài đặt: lấy file trong group Telegram/Zalo; đề nghị treo VPS rẻ (khoảng 300.000 VND/năm) để test; không nói MT4/MT5, .set.
5. Cảnh báo/số liệu (lời người trình bày): backtest 2020-2024 EURUSD, vốn 20k, lãi khoảng 43k, drawdown lớn nhất khoảng 11k (năm 2021), trung bình khoảng 10k/năm, "khoảng 50%/năm", "5-10%/tháng". Nói "bot DCA chắc chắn sẽ cháy, chỉ không biết khi nào", chiến tranh/khủng bố/biến động lớn làm ảnh hưởng. EURUSD thường hồi sau khi đi khoảng 200 pip.

Độ tin cậy nội dung: vừa (nhiều số hợp lý nhưng lot khởi điểm mơ hồ, thiếu tên input).

---

## 4. Copy1 - bot copy trade EXP-COPYLOT (MT4 -> MT5) - file Copy1.txt

1. Chiến lược: không phải bot giao dịch. Copy lệnh từ tài khoản Master (MT4) sang tài khoản Client (MT5); phụ đề đặt tên "Copy Lot Master" (MT4) và "Copy Lot Lion/Client" (MT5). Dùng khi có bot chỉ chạy được trên MT4 (chạy demo MT4 rồi copy sang MT5).
2. Quản lý lệnh: mặc định copy tỷ lệ 1:1 volume. Các tùy chọn khác (lọc symbol, TP/SL, giới hạn lot, tỷ lệ theo balance): chỉ nói qua. Không DCA/trailing.
3. Tham số: nhãn/mật khẩu liên kết giữa hai terminal ("label for communication", mặc định "copy"; có thể đặt 1, 2... khi chạy nhiều cặp Master/Client; hai bên phải giống nhau); "copy original lot" (copy đúng lot của Master); tùy chọn chỉnh tỷ lệ lot. Thông tin Master hiển thị trên Client (balance 93 USD).
4. Cài đặt: copy file bot vào thư mục Experts (Open Data Folder, MQL4/Experts), kéo vào chart, bật Allow live trading/AutoTrading; bên Client MT5 làm tương tự với file bot Client; khi liên kết thì Client hiển thị balance của Master. Test: Master mở Buy 0,01, Client mở theo. Chiều MT5 -> MT4 làm ngược lại (file Master MT5, file Client MT4). Chia sẻ file qua Telegram/Zalo.
5. Cảnh báo/số liệu: không nói về rủi ro, không có số liệu lợi nhuận. Phần chỉnh tỷ lệ lot: người trình bày nói "chưa rõ, các bạn nghiên cứu thêm".

Độ tin cậy nội dung: vừa (quy trình cài rõ, tên input bị nhận dạng sai).

---

## 5. Copy2 - bot copy trade EXP-COPYLOT (MT4 -> MT4) - file Copy2.txt

1. Chiến lược: như Copy1; mục đích nêu: copy tài khoản người khác, copy từ demo sang real, hoặc nhiều người follow mình / quản lý quỹ. Demo MT4 -> MT4; nói MT5 -> MT5 cũng tương tự.
2. Quản lý lệnh: mặc định 1:1. Danh sách tính năng người trình bày liệt kê (chưa thử hết): lọc theo symbol, TP/SL, giới hạn max/min lot, lọc lệnh, copy theo tỷ lệ balance, hoặc tỷ lệ 1/10 so với Master. Thử đổi hệ số lên 2 nhưng demo vẫn ra lot như cũ (phụ đề mơ hồ).
3. Tham số: nhãn liên kết giữa hai bot (mặc định "copy", hoặc 1/2...) phải giống nhau giữa Master và Client; chế độ "master account" true/false.
4. Cài đặt: mỗi tài khoản một terminal MT4 riêng; copy file bot vào thư mục MT4 (Experts), kéo vào chart mới trùng cặp tiền; đặt chế độ Master cho bên gốc, Client (phụ đề "Lion") cho bên nhận; bật AutoTrading. Demo: Master mở Buy tại khoảng 6679, Client mở theo.
5. Cảnh báo: người trình bày nói ít dùng loại bot này, phải tự test, "không thể hướng dẫn quá sâu". Không có số liệu lợi nhuận.

Độ tin cậy nội dung: vừa (cùng nguồn với Copy1, ít chi tiết hơn).

---

## 6. T91 Gold Hunter - file GoldHunter.txt

1. Chiến lược: chỉ BUY (all buy) trên vàng. Vào lệnh khi RSI chu kỳ 4 trên M5 xuống dưới 15 (vùng quá mua 83 hầu như không sale). Phụ đề nói bot còn dùng Bollinger Band/MA4 (có đường biên trên-dưới) và một đường chưa xác định. Có đúng 1 lệnh Sell lẻ ở đầu test, người trình bày không giải thích được (nghi lỗi hoặc xu hướng lớn hơn).
2. Quản lý lệnh: nhồi Buy nhiều lần (thấy "mấy trăm lệnh"), mỗi lệnh khoảng 0,1 lot (phụ đề "0,1" mơ hồ); TP: khi giá trung bình của cả chuỗi dương (lớn hơn 0) và RSI trên 50 thì chốt toàn bộ, không đặt TP theo pip/USD. SL, giới hạn số lệnh: không nói.
3. Tham số: RSI(4) M5 ngưỡng 15; ngưỡng thoát RSI 50. Vốn test 10.000. Loại tài khoản, đòn bẩy, sàn: không nói. Năm test trong phụ đề ghi "2029" (rõ là lỗi, không biết năm thật).
4. Cài đặt: không nói (chỉ chạy Strategy Tester với Visual mode).
5. Cảnh báo/số liệu (lời người trình bày): ý tưởng "vàng dài hạn luôn tăng nên chỉ buy"; nói giá vàng 2000 -> 2004 trong test; balance từ 10.000 lên 16.000 trong 9 tháng, tính đến tháng 7 lãi khoảng 9000 (số mơ hồ). Người trình bày chưa hiểu hết bot, nói sẽ làm thêm video theo dõi. Rủi ro hiển nhiên (không được nói): chỉ buy + nhồi, gặp xu hướng giảm dài sẽ kẹt.

Độ tin cậy nội dung: thấp-vừa (năm test, số liệu lợi nhuận mơ hồ; logic RSI và cách thoát rõ).

---

## 7. HandDCA.HBot (video 1, kèm chỉ báo SSL) - file HandDCA1.txt

1. Chiến lược: HandDCA là bot "đánh tay + DCA tự động": người dùng mở 1 lệnh Buy hoặc Sell, bot tự DCA ngược lại và điều chỉnh TP để có lãi dương. Phần lớn video nói cách vào lệnh tay bằng chỉ báo SSL (histogram xanh/đỏ), chơi scalping vàng: mở 3 chart M1, M5, M15; đợi M15 xanh (phải đóng đủ nến, ví dụ 2:30 xanh rồi 2:45 xanh đóng), M5 xanh, rồi canh M1 đổi từ đỏ sang xanh thì Buy (ngược lại với Sell). Có thể chơi 2 khung nhưng 3 khung đẹp hơn.
2. Quản lý lệnh: Chốt lãi 2-3 giá (scalp); nếu sai thì bot DCA. Mức DCA/lot/số lệnh: không nói. Chỉ báo SSL được nói là hợp để đánh theo DCA.
3. Tham số bot: không nói chi tiết (video chỉ nói TP "lãi dương bao nhiêu tùy chỉnh"). Sản phẩm: XAU; tài khoản demo.
4. Cài đặt: chỉ báo SSL lấy từ nhóm Telegram; add chỉ báo vào chart M1, M5, M15. Bot: không nói cách cài.
5. Cảnh báo (lời người trình bày): chỉ báo bị "repaint/reband" nếu nến chưa đóng, vào lệnh sớm là sai; M5 đảo liên tục thì khó; nên né giờ giao phiên; chơi từ 8h trở đi; khoảng 18h-21h (giờ VN) hay đi ngang/đảo chiều nên dễ dính chuỗi DCA dài. Phiên Mỹ biến động mạnh, hợp scalp. Số liệu: một lệnh chốt được khoảng 0,81 USD (demo).

Độ tin cậy nội dung: vừa (rõ về chỉ báo, rất ít về bot).

---

## 8. HandATMX.HBot (video 2, cập nhật trailing) - file HandDCA2.txt

1. Chiến lược: bot DCA nhồi lệnh theo lệnh tay (HandATMX); video chỉ cập nhật tính năng trailing mới "Trailing Oneway System" áp dụng khi chuỗi chỉ có MỘT chiều (ví dụ chỉ Buy). Khung M5 test; nói H1 dễ quan sát hơn.
2. Quản lý lệnh: TP tổng của chuỗi (ví dụ 10 USD). Trailing Oneway: khi số lệnh một chiều lớn hơn "Oneway number order" (ví dụ 3) VÀ tổng lãi các lệnh lớn hơn ngưỡng (ví dụ 5 USD), bot dịch SL về hòa vốn cộng thêm 1 giá (chỉnh được; ví dụ 10 BP). Có thể có on/off cho tính năng (nói sẽ thêm). Khi có cả Buy và Sell cùng lúc thì tính năng Oneway không bật; có nhóm input riêng "Trailing order setting" cho trường hợp hai chiều: khi tổng Buy+Sell lớn hơn 10 thì dịch SL về hòa vốn và chốt dương. Ví dụ demo: 6 lệnh Buy, lãi lớn hơn 5 thì SL dịch về trung bình; giá hồi thì cắn SL, chuỗi chốt dương.
3. Tham số: Oneway number order (3), ngưỡng lãi bật trailing (5 USD; gợi ý 5-8 và tránh 100, có thể 50), TP chuỗi (10 USD), khoảng cách SL so với hòa vốn (1 giá hoặc 10 BP). Cặp: vàng (giá khoảng 65-69 trong ví dụ, mơ hồ). Vốn, đòn bẩy: không nói.
4. Cài đặt: bot lấy ở Telegram/Zalo nhóm; hướng dẫn chi tiết ở video trước. Không nói chi tiết.
5. Cảnh báo (lời người trình bày): trailing sát có thể bị quét ngay sau khi đặt (giá giật xuống) và mất lợi nhuận tiềm năng, đổi lại an toàn nếu giá sập sau khi đã nhồi 6-7 lệnh Buy; tính năng phức tạp, phải test nhiều để hiểu hành vi modify.

Độ tin cậy nội dung: vừa (cơ chế rõ, đơn vị USD/giá/BP hơi lẫn).

---

## 9. KawKawKaw46 V2 (EMA46 XAU M1) - file KawKaw.txt

1. Chiến lược: bot DCA một chiều trên vàng, MT4, có tên "Kawa Kawa/KWA" trong phụ đề. Phụ đề không nhắc rõ EMA46 hay M1; chỉ nói có chế độ mở lệnh "theo entry" và "theo MA", Buy/Sell mode bật được. Đánh một chiều, xử lý xong chuỗi rồi mới sang chuỗi khác (khác Semi HFT là bot ưu tiên cứu Sell và TP từng phần Buy).
2. Quản lý lệnh: lưới tự giãn ra khi giá đi ngược; khi giá hồi lại thì bot nhồi thêm lệnh làm lưới dày, kéo điểm TP lại gần (ví dụ đi 20 giá, âm khoảng 400, giá hồi 3-4 giá là TP chuỗi). Lot giữ ổn định (mặc định kiểu lot cộng "lot step add", không tăng lot nhanh). Step margin open khoảng 5 giá. Có TP tổng theo USD. SL, max lệnh: không nói.
3. Tham số: các input chính: mở lệnh theo entry/MA, Buy/Sell mode, lot step add (lot cộng), step ~5 giá, đóng tất cả khi đạt USD; nhiều input khác người trình bày nói "chưa hiểu lắm". Sàn: có thể chơi trên XM (phụ đề ghi "xnet"). Vốn: không nói.
4. Cài đặt: file bot chia sẻ ở nhóm Zalo; đặt tên "KWA"; chạy trên MT4. Không nói gì thêm.
5. Cảnh báo/số liệu (lời người trình bày): bot DCA gặp trend mạnh thì âm cao; test demo từ 3/7 lãi 14 USD, chưa tính spread.

Độ tin cậy nội dung: vừa (cơ chế lưới rõ, thiếu tên và giá trị input).

---

## 10. NewYear.HBot (video 1, ý tưởng vận hành) - file NewYear1.txt

1. Chiến lược: bot đánh theo xu hướng (trend-following), nhồi theo trend; sợ sideway. Mọi khung được, tốt nhất từ M5 trở lên (có thể D1/W1). Vàng là sản phẩm hợp nhất; Bitcoin khó vì sideway không có quy luật; forex chưa thử. Khuyến nghị chạy đúng cặp mà tác giả bot đã test.
2. Quản lý lệnh: sau mỗi lệnh SL thì nhân lot lên tiếp (ví dụ chuỗi lot 0,01 -> 0,02 -> 0,04 -> 0,08 -> 0,16 -> 0,32; có lúc đánh tới 0,36), kiểu martingale. Số lệnh tối đa, SL, TP: không nói.
3. Tham số: không đi vào input. Vốn: demo tài khoản cent; ví dụ mua quỹ (prop) 5000 USD với SL tối đa 500 USD và 250 USD/ngày (người trình bày nói bot "đánh quỹ được" nhưng phải lái). Bản "V2 / FVG V2" là bot khác (nói thêm ở cuối video).
4. Cài đặt: file bot chia sẻ miễn phí trong group; không nói cách cài.
5. Cảnh báo/số liệu (lời người trình bày): "từ Tết tới giờ lãi khoảng 50%" trên tài khoản cent; bot nào cũng phải "lái" (tắt bật theo thị trường), không có bot bất tử. Cách nhận diện sideway: 3-4 cây nến không thoát được vùng của nhau thì tắt bot, đợi phá vùng; nên tắt bot trong phiên khuya (khoảng 23h-1h/2h sáng giờ VN) và khi có tin mạnh (ví dụ tin Iran). Với FVG V2 (không phải NewYear): lời họ nói một tháng lãi 10-30% khi đánh vàng, một số người vốn 5000-10.000 cent; có hôm kẹt khoảng 76 giá, âm khoảng 10%. Khuyên dùng tài khoản nhỏ khi mới chơi.

Độ tin cậy nội dung: vừa (cách vận hành rõ; không có tham số).

---

## 11. NewYear.HBot 2.1 (video 2) - file NewYear2.txt

1. Chiến lược: đánh theo trend ("follow trend", nhồi theo xu hướng, không ngược trend), vàng; test trên MT5. Khung H1 trở lên (M15 cũng được). Vào lệnh: không nói rõ tín hiệu.
2. Quản lý lệnh: sau SL thì nhân lot lên ("hệ số lot nhân 2": 0,01 -> 0,02 -> 0,04 -> 0,08 -> 0,16 -> 0,32), nên lot đầu 0,01; TP/SL cố định (demo TP khoảng 5 giá, SL khoảng 7 giá, phụ đề mơ hồ); trailing: khi lot chuỗi đạt 0,08 và lãi 2 giá thì dịch SL về hòa vốn. Có chia lot (divot, 1 = không dùng). Đánh theo ba khung giờ giao dịch (time trade 2, 3; mặc định không dùng).
3. Tham số: Magic, lot, TP/SL, hệ số lot nhân 2, trailing (lot 0,08 và 2 giá), time trade 1/2/3 (khung giờ), divot (chia lot). Vốn gợi ý: tài khoản cent nhỏ khoảng 100 USD, không cần đánh lên 0,32 lot. Đòn bẩy, sàn: không nói.
4. Cài đặt: lấy bot ở nhóm Zalo; chạy test Strategy Tester ở chế độ Visual. MT5.
5. Cảnh báo/số liệu (lời người trình bày): 10 ngày đầu tháng 1/2025 lãi khoảng 100 USD, âm tối đa 20-25; từ 1 đến 13/1/2025 lãi 126 USD, max âm khoảng 28; "một tháng 10-20%". Sideway thì bot "ngáo" và bị cuốn lệnh. Nhắc không có bot nào thần thánh, đừng tin win rate 90-99% và "không cháy"; DCA, lệnh dương, lệnh đơn đều có rủi ro; nến cuối tháng/quý hay điều chỉnh mạnh; "ăn đủ thì nghỉ". Họ nói họ bán bot (không còn chia sẻ miễn phí).

Độ tin cậy nội dung: vừa.

---

## 12. NuTi.HBot 1.3 (video 1, bản MT5, DCA theo tâm giá) - file Nuti1.txt

1. Chiến lược: DCA theo "tâm giá" (giá mở cửa ngày); ý tưởng giống con NuTi MT4 nhưng bản MT5 mới, ít tính năng hơn (chủ yếu DCA và khoảng cách giá). Tên trong phụ đề "fory haa" (không chắc). Vàng. Mở lệnh đầu khi giá lệch tâm giá khoảng 30 giá (có thể chỉnh 20). Triết lý (lời họ): vàng luôn có "bão" không báo trước nên chơi SAU bão (vàng sập 30-40 giá rồi mới vào).
2. Quản lý lệnh: DCA mở theo nến (true = chỉ DCA khi mở nến mới); khoảng cách DCA khoảng 1 giá; lot đầu 0,01; hệ số nhân 1,1 (hệ số cộng 0); lot tối đa 3; tối đa 9 lệnh; TP tổng chuỗi 20 giá; SL: giá trị ghi "2000" (mơ hồ); "tỉa lệnh": kích hoạt khi chuỗi có 10 lệnh, tỉa 2 lệnh, lãi sau tỉa 2,5 USD (người trình bày chỉnh false, không dùng). Có tùy chọn support (không bật).
3. Tham số: tâm giá 30 giá, DCA theo nến, khoảng cách 1 giá, hệ số 1,1, max lot 3, max lệnh 9, TP chuỗi 20 giá, tỉa (tắt).
4. Cài đặt: lấy bot ở nhóm Zalo (chủ yếu) hoặc Telegram; chạy song song MT4 và MT5. Không nói gì thêm.
5. Cảnh báo (lời người trình bày): không nên backtest nhiều tháng rồi cắm thật; bot DCA phải "lái": chọn ngày thả. Tránh: sáng thứ Hai, tối thứ Sáu, đầu và cuối tháng, cuối quý (30/6, 30/9, 31/12), nửa cuối tháng 12 (nghỉ Noel), ngày lễ Mỹ, tháng 3 từng có "bão" ~200 giá làm mọi bot cháy. Định nghĩa "bão": đi khoảng 40-60 giá trong 5-10 phút không hồi (nhìn nến H1/M15). Tránh gồng chuỗi lâu. Số liệu lợi nhuận tổng hợp: không nêu rõ (có nói TP khoảng 100 giá/đợt trong demo, mơ hồ). Cộng đồng Zalo ~160, có khóa học code bot.

Độ tin cậy nội dung: vừa (nhiều tham số nhận dạng được; một số giá trị mơ hồ).

---

## 13. NuTi.HBot 1.3 (video 2, bản MT4) - file Nuti2.txt

1. Chiến lược: bot scalping vàng kết hợp DCA, theo "tâm giá" = giá mở cửa ngày; "trên Sell, dưới Buy": ví dụ mở 2000, giá lên 2003 thì Sell, xuống 1997 thì Buy. Có bật/tắt Buy/Sell on. Mở theo nến (true: một nến một lệnh nếu đủ khoảng giá; false: chỉ cần đủ khoảng giá). Khung M5 trong test. Giữ ở chế độ "only" (một chiều) khi test.
2. Quản lý lệnh: ba "quãng": Quãng 1 = lệnh 1-9: lot 0,01, cách nhau 2 giá, TP đơn 2 giá mỗi lệnh, không SL; Quãng 2 = lệnh 10 trở đi (ví dụ chỉnh đến 15): lot lớn hơn do tính toán (ví dụ 0,38), cách nhau 3 giá, TP chuỗi (hòa vốn cộng 0,5 giá; khuyên chỉnh lên 1-3 giá vì 0,5 hay bị stress); Quãng 3: lệnh tiếp theo. Có thể chỉnh quãng 1 lên 60-100 lệnh để chỉ đánh lệnh đơn (kiểu lưới cả hai chiều, không TP chuỗi) -> rất bền nhưng hay bị treo lệnh chéo. Max order có thể chỉnh lên 30/50/60/100. "Shot tài khoản" (cắt khi âm X USD, ví dụ 300) có nhưng để false.
3. Tham số: Magic, lot đầu 0,01, TP đơn 2 giá, khoảng cách 2/3 giá, mốc lệnh 9-10 chuyển sang TP chuỗi, TP chuỗi (hòa vốn + 0,5 giá), max order 60 (có thể 100), shot tài khoản (tắt). Vốn gợi ý (lời họ): khoảng 50k, 40k hoặc 30k cũng được và đủ chịu "khoảng 80 giá"; có thể 100k (đơn vị 50k/100k không nói rõ, có thể cent). Sàn: không nói.
4. Cài đặt: lấy bot ở nhóm Zalo/Telegram; setup do một bạn (tên phụ đề "Nguyễn Thi") yêu cầu, dựa trên cách chơi trong group; không nói về VPS, AutoTrading.
5. Cảnh báo/số liệu (lời người trình bày): backtest XAU 2024 (9 tháng) lãi 44k, max drawdown 35k; setup mặc định "gồng khá nhiều"; không biết khi nào cháy; chơi 100k cũng được. Kiểu 60 lệnh đơn "bền nhưng hay bị kẹt".

Độ tin cậy nội dung: vừa (cơ chế quãng và tham số rõ; đơn vị vốn mơ hồ).

---

## 14. SEMI HFT EA V3.3 - file SemiHFT.txt

1. Chiến lược: bot DCA/lưới trên vàng, không rõ khung. Mở lệnh đầu theo "signal" nào đó (không rõ), hai chiều Buy/Sell. Tên trong phụ đề "Simi HFT"; người trình bày giải thích "HFT" = giao dịch tần số cao (suy đoán).
2. Quản lý lệnh: DCA mỗi 2 giá (có thể cách một nến); hệ số lot 1,08 mỗi lệnh (lot nhỏ); thoát bằng trailing stop (không có TP chuỗi). Chiều Buy: tách nhóm, TP từng phần lệnh Buy thấp nhất trước (giống bot RTX), và treo lên; chiều Sell: không tách, gồng cả chuỗi tới khi thoát. Khi Sell kẹt nhiều, bot gồng giữ Buy dương (giảm drawdown, không TP) cho tới khi chuỗi Sell xong. Có thể là lỗi vì Buy dương không chốt.
3. Tham số: mode Buy/Sell, signal, vào lệnh market, mode DCA (mode 3), Xlot 1,08, khoảng cách 2 giá, trailing: lãi 2 giá tính từ hòa vốn thì dịch trailing; đóng khi đạt USD (không dùng); giờ giao dịch theo ngày. Vốn, sàn: không nói.
4. Cài đặt: bot chia sẻ trong nhóm Zalo; test chậm. Bản chưa thấy bản quyền ("allow to install" trong chart).
5. Cảnh báo (lời người trình bày): chưa chắc cơ chế; lợi nhuận không cao nhưng drawdown thấp; nếu giá tăng mạnh mà Sell kẹt nhiều thì "chắc chắn" đau; bot DCA cần kế hoạch vốn; cần test thêm. Không có số liệu USD tổng hợp.

Độ tin cậy nội dung: vừa (hành vi quan sát khá chi tiết, tham số mơ hồ).

---

## 15. SignalX.HBot - file SignalX.txt

1. Chiến lược: bot đánh lệnh đơn + x lot, bắt tín hiệu Buy/Sell từ chỉ báo bên ngoài (đọc buffer). Khung M1/M5/M15 (test M1); sản phẩm nói qua XAU/MT4. Chỉ báo ví dụ có tên "Atom" (phụ đề).
2. Quản lý lệnh: mỗi lệnh có TP/SL cố định (ví dụ TP 2 giá); khi chạm SL thì lệnh kế tiếp (khi có tín hiệu mới) nhân đôi lot (0,01 -> 0,02 -> 0,04 -> 0,08 -> 0,16 -> 0,32 -> 0,64). Giống martingale. Không có DCA lưới.
3. Tham số: Magic; volume đầu; TP/SL; "ID buy" và "ID sell" (số buffer của chỉ báo; thường 0/1 hoặc 1/0; chỉ báo ví dụ Buy = 22, Sell = 23); tên chỉ báo phải copy chính xác tên trong MT4. Thường bắt được 70-80% chỉ báo, một số thì không.
4. Cài đặt: file bot trong Drive/Zalo; MT4; gắn chỉ báo cùng bot và điền ID.
5. Cảnh báo (lời người trình bày): chỉ báo nhiễu, winrate thấp thì x lot liên tục dẫn đến cháy tài khoản; phải lọc nhiễu/trend lớn (ví dụ chỉ theo Buy); bot x lot "sợ sideway" còn DCA "sợ trend mạnh"; nên đánh ít lot, một ngày quản lý một hai lần, không treo 24/24. Thắng demo vài lệnh, không có số liệu tổng hợp. Chủ bot nhắc con bot khác tên "Vahala" (đang nâng cấp từ New Year).

Độ tin cậy nội dung: vừa (cách cấu hình rõ; chi tiết quản lý vốn thiếu).

---

## Điểm chung

- Hầu hết là bot DCA/lưới/martingale trên vàng (XAU) với lot nhân hệ số nhỏ (1,08-1,2) hoặc nhân đôi sau SL (NewYear, SignalX); chỉ Bigmouse dùng hedging bằng lệnh stop ngược với tổng lot gấp 2 lần phía đối diện, và Black Dragon/NuTi chạy hai chiều.
- Cơ chế thoát lặp lại: TP chuỗi tại hòa vốn cộng một khoảng nhỏ (Nuti 0,5 giá, HandATMX 1 giá), TP theo tổng USD (Bigmouse 5 USD), hoặc chốt khi trung bình giá dương và RSI trên 50 (GoldHunter).
- Trailing/hòa vốn lặp lại ở Bigmouse, HandATMX (Oneway), NewYear 2.1 (lot 0,08, lãi 2 giá), Semi HFT (2 giá), Black Dragon (TP treo lên); tất cả đều "kéo SL về hòa vốn" khi chuỗi đủ lớn, đổi lại bị quét sớm và mất lợi nhuận tiềm năng.
- Kiểu tách nhóm/chốt từng phần xuất hiện ở Semi HFT (Buy thấp nhất trước) và "tỉa lệnh" ở NuTi; ý tưởng giảm kẹt chuỗi mà không phải chờ về hòa vốn toàn chuỗi.
- Nhiều bot lấy giá mở cửa ngày (NuTi) hoặc nến M5-H1 làm mốc, đánh một chiều rồi giãn lưới khi giá đi ngược (KawKaw, Black Dragon hệ số giãn 1,2).
- Người trình bày lặp lại: bot phải "lái" (chọn ngày/phiên thả, tắt khi sideway, tin mạnh, đầu/cuối tháng/quý, giữa tháng 12), không có bot nào bất tử; DCA sợ trend mạnh, x lot sợ sideway.
- Thiếu sót/rủi ro hay gặp: gần như không có giới hạn drawdown tuyệt đối (SL tài khoản thường tắt/false), không nêu spread/phí/trượt giá trong số liệu, số liệu lợi nhuận là từ test/demo ngắn hoặc lời kể (BNK 43k/20k, NuTi 44k/35k DD, Black Dragon "28%/ngày" là bất thường và không đáng tin), thường không nêu tham số vốn/đòn bẩy/sàn đủ rõ.
- Hầu hết là bot không rõ nguồn gốc/bản quyền (bot "nhặt từ group", EA bán chợ MQL5, EA free "allow to install"), file chia sẻ qua Telegram/Zalo; không nói về chống rò rỉ look-ahead hay chất lượng dữ liệu tick của backtest.
- Việc cài đặt hầu như không được mô tả (không nhắc DLL/WebRequest, VPS chỉ nhắc ở BNK); phần copy trade (Copy1/Copy2) là tiện ích ngoài, không phải chiến lược.
