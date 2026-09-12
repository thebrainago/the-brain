# LUẬT GIÁM SÁT — cho AI đọc kết quả của The Brain

Dòng cuối của `SO_DO_HE_THONG.txt`:

> *"Sau phần kết quả này cần viết luật cho AI giám sát tư duy để đúc rút và học
> hỏi được kiến thức và cần làm gì để cải thiện được hệ thống"*

Đây là bộ luật đó. Nó **không phải** hướng dẫn dùng lab — cái đó ở `CLAUDE.md`.
Nó là luật đọc **con số**: khi nào được tin, khi nào phải nghi, và nghi thì làm gì.

Mỗi luật dưới đây sinh ra từ một lỗi **đã xảy ra thật**, có số kèm theo. Không
luật nào là lý thuyết.

---

## PHẦN I — TRƯỚC KHI TIN MỘT CON SỐ

### L1. Một con số đẹp bất thường là một manh mối, không phải một phát hiện

> `GBPZAR chot_nhanh: CAGR 591%/năm, maxDD −99,38%` (12/09/2026)

Truy ngược ra: cột `high` của mã đó bị **nhân 10** suốt 4 tháng. Sau khi sửa,
Sharpe từ 0,763 xuống **−0,071**.

**Luật:** con số nằm ngoài khoảng hợp lý của lớp tài sản thì **dừng lại và truy
về dữ liệu gốc**, trước khi viết bất kỳ câu kết luận nào. Thứ tự truy:
dữ liệu → phép tính chi phí → phép quy đổi → mới đến "thị trường".

### L2. Kết luận ÂM chỉ có giá trị sau khi bộ đo đã chứng minh nó bắt được cái có thật

> `2.841 hệ qua holdout, 0 thắng mốc` (12/09/2026)

Suýt báo cáo. Cấy một edge **thật** 0,6 sigma vào chuỗi tổng hợp thì phễu
**trượt** — vì nó chạy `giu=60` cho 67% cơ chế khai `giu≤5`. Sau khi sửa: 7 hệ
qua. Con số 0 kia không nói gì về thị trường.

**Luật:** trước khi báo một kết luận âm rộng, chạy **hiệu chuẩn hai chiều** —
cấy edge thật (phải bắt được) và chuỗi ngẫu nhiên (không được bịa ra).

### L3. "Không đo được" không phải "âm"

Ba trạng thái, không phải hai: **TỐT · XẤU · CHƯA_ĐO**. Gộp `CHƯA_ĐO` vào `XẤU`
là cách một bộ giám sát tự bịa ra vấn đề. `nhan/evo.py` cưỡng chế luật này.

### L4. So sánh phải cùng đơn vị, cùng cỡ mẫu, cùng phép quy

Ba lần vi phạm trong một phiên:
- so *tốt nhất trong 40* với *từng lượt placebo lẻ* → p 0,0249 thay vì 0,5958
- so Sharpe trên **toàn chuỗi** với MDE tính trên **nửa holdout** → lệch 1,44 lần
- hệ dùng phép quy đòn bẩy đúng, **mốc** vẫn dùng phép nhân tuyến tính cũ

**Luật:** viết ra đơn vị và cỡ mẫu của **cả hai vế** trước khi so.

### L5. Một chỗ định nghĩa duy nhất cho mỗi tiêu chí

Siết tiêu chí holdout xong, bộ tổng kết vẫn in con số cũ (29 thay vì 19) vì nó
**tự suy lại** tiêu chí. Hai chỗ định nghĩa cùng một thứ là mầm sai lệch.

**Luật:** đánh dấu kết quả **ngay trên dòng dữ liệu**, người đọc không được suy lại.

---

## PHẦN II — TRƯỚC KHI XÂY

### L6. Nối dây trước khi xây thêm

Hai lần trong một phiên tôi ghi đè module đã có (`uu_tien.py`, `noi_sinh.py`).
Và bẫy "râu nến hỏng" **đã đếm được 154 bar hỏng của GBPZAR từ trước** — không
ai đọc nó.

**Luật:** trước khi viết file mới, `ls` + `git show HEAD:<đường dẫn>`. Trước khi
kết luận "thiếu X", tìm xem X đã có mà **chưa được nối vào đường chạy** không.

### L7. Công cụ không nằm trên đường chạy thì bằng không có

`du_lieu.kiem()` có đủ 5 bẫy, nhưng **không nơi nào trên đường chạy đọc
`dung_duoc`**. Nên phép sửa phải nằm trong `nap()` — cửa duy nhất mọi module đi qua.

**Luật:** mỗi bộ đo mới phải trả lời được: **ai gọi nó, và khi nào?** Không trả
lời được thì chưa xong.

### L8. Đường an toàn phải là đường mặc định

`anh_chup.hash_file` mặc định `dung_dem=True` — bộ đệm khoá theo mtime nên một
file bị sửa cùng giây **lọt**. Docstring của chính nó đã cảnh báo, mà mặc định
vẫn là đường nguy hiểm.

**Luật:** cái an toàn là mặc định; cái nhanh phải được **khai rõ**.

---

## PHẦN III — ĐỌC BẢNG XẾP HẠNG

### L9. Đọc cột TÀI SẢN trước cột ĐIỂM

200 ô sống sót của Q6 gần như chỉ nằm trên **TRYJPY · GBPTRY · USDARS** — ba
đồng tiền sụp đổ. Bảng đẹp, nhưng nó bắt một xu hướng một chiều **đã xảy ra rồi**.

**Luật:** nếu người thắng tập trung vào 1–3 mã cùng một tính chất, đó là tính
chất của **mã**, không phải của **cơ chế**.

### L10. Mốc bằng 0 thì "thắng mốc" chỉ có nghĩa "dương"

`moc_hold = 0,00` nghĩa là mua-giữ **và** bán-giữ đều âm, mốc tụt về tiền mặt.
Ghi rõ giá trị mốc cạnh mỗi dòng, đừng chỉ ghi cờ `hon_moc`.

### L11. Hai nửa phải CÙNG CỠ, không chỉ cùng dấu

`train 1,67 → hold 48,86` gấp 30 lần **không phải** bền — đó là nửa sau tình cờ
có xu hướng. Đòi tỉ lệ `hold/train` nằm trong `[0,33 · 3,0]`.

### L12. Lực của một bảng đa tài sản nằm ở SỰ LẶP LẠI, không ở từng ô

Suy ngược: tốt nhất chỉ **54/154** mã đạt ý nghĩa riêng lẻ → nhìn cột đó thì kết
luận "không có gì". Nhưng **126/154 mã cùng dấu** là phép thử nhị thức rất mạnh.

**Luật:** với bảng đa tài sản, chạy phép thử **gộp trên dấu**, và ghi kèm số mã
**độc lập** ước lượng được (ở đây ~79/154) vì p gộp là chặn dưới lạc quan.

---

## PHẦN IV — ĐÚC RÚT

### L13. Mỗi lỗi đo được sinh ra một lưới chặn, không phải một ghi chú

Ghi chú không chặn được lần sau. Bài kiểm thì có. Hôm nay: 8 lỗi → 8 nhóm bài
kiểm (`test_sua_bar_hong`, `test_hieu_chuan_to_hop`, `test_mau_nen`, …).

### L14. Cái gì phải nhớ thì viết vào memory, cái gì phải chặn thì viết thành test

- **memory** — sự thật không đọc được từ mã (vì sao một quyết định được đưa ra)
- **test** — ràng buộc đọc được từ mã
- **`bai_hoc`** — hướng đã đi và kết cục, để không đi lại

### L15. Không được sửa ngưỡng để kết quả đẹp lên

Sửa ngưỡng **chỉ được phép** khi có bằng chứng ngưỡng cũ sai về nguyên tắc, và
phải ghi lại bằng chứng đó. Hôm nay: `giu_toi_da` 60→theo cơ chế có bằng chứng
(edge 1 bar chết khi giữ 20 bar); còn tiêu chí holdout thì **siết vào** chứ
không nới ra.

### L16. Một bộ dò kết luận "không có" phải chứng minh nó THẤY ĐƯỢC cái có

Bản đồ hệ thống sinh ngày 12/09 báo cả gói `qwen/` là MỒ CÔI — trong khi `q.cmd`
chạy nó mỗi ngày. Nguyên nhân: bộ dò chỉ đọc `from nhan import X`, mù với
`from . import X` và mù với cửa vào `.cmd`. Đó là **âm tính giả**, không phải
thực tế âm — và một bản đồ báo nhầm còn tệ hơn bản đồ cũ, vì nó khiến người đọc
xoá thứ đang chạy.

Cùng họ bệnh với `cong-pass-phai-hieu-chuan-hai-chieu` và
`bo-do-nhin-truoc-mu-voi-co-che-thua`. Quy tắc: trước khi tin một danh sách
"không tìm thấy", lấy **ba thứ chắc chắn CÓ** ra kiểm. Nếu bộ dò không thấy
chúng thì con số 0 kia không nói gì về thế giới, nó chỉ nói về bộ dò.

### L17. Ba bậc, không phải hai: "mồ côi" phải phân biệt được với "hạ tầng"

Lần sinh đầu ra **211 mồ côi** trên 433 file — không ai đọc nổi. Nhưng 151 là
script `_*.py` chạy tay một lần (mồ côi là đúng bản chất), 11 là thư viện được
script tay gọi (hạ tầng hợp lệ). Số thật là **31**.

Một danh sách cảnh báo mà 85% là nhiễu thì không phải cảnh báo, nó là tiếng ồn —
và tiếng ồn dạy người đọc bỏ qua cả những dòng thật. Chia bậc cho tới khi mỗi
dòng còn lại đều đáng hành động.

### L18. Thiếu một trường thì bộ chấm BỎ QUA, không được đoán

`to_hop` không ghi `so_nam` vào từng dòng. Nếu `cham_diem` lấy mặc định 0 thì
`so_lenh_nam` = TỔNG số lệnh, và mọi dòng đều vượt ngưỡng 20 lệnh/năm **một
cách giả**. Cùng họ với `h.get("so_lenh")` trả None→0 rồi gắn nhãn
`KHONG_KICH_HOAT` cho 10/10 hôm nay.

Sửa ở NGUỒN (ghi `so_nam` vào dòng), và ở chỗ dùng thì đếm rồi nói ra:
*"120/120 dòng thiếu `so_nam` — bỏ qua"*. Một con số bị bỏ qua mà có báo thì
sửa được; một con số bị đoán thì không ai biết để sửa.

---

## CHẠY GÌ MỖI PHIÊN

```
b vao          trạng thái sống + bàn giao + EVO một dòng
b evo          sức khoẻ từng module + cắt nghĩa + đề xuất chạy được
b xay --xem    hàng đợi việc xây
b test         1.493 bài kiểm — phải xanh trước khi chốt phiên
```

Và **LUẬT SỐ 0** trong `CLAUDE.md`: đối chiếu `Desktop/hethong.txt` — nguồn cấu
trúc là sơ đồ của chủ dự án, không phải tài liệu trong lab.
