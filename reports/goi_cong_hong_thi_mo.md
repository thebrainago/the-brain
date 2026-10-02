# GÓI: CỔNG CHẶN CỨNG **HỎNG THÌ MỞ**

Chỗ đắt nhất trong cả hệ — và nó đã ở đó suốt.

## LỖI

`nhan/cong.py`, điều kiện `11_khong_an_khe_dao_ngay`:

```python
dk["11_khong_an_khe_dao_ngay"] = True          # khởi tạo PASS
try:
    ...
    elif not _kh["do_duoc"]:
        ly_do.append("chua do duoc ... - KHONG ket luan la sach")   # ← văn
except Exception as _e:
    ly_do.append(f"khong do duoc khe dao ngay: ...")                # ← văn
```

Khởi tạo `True` rồi **giữ nguyên `True` ở mọi đường thất bại**: quá ít bar, chỉ
một ô thời gian, hay một ngoại lệ bất kỳ. Chính dòng `ly_do` ngay bên dưới viết
*"KHÔNG kết luận là sạch"* — **tác giả đã biết** — nhưng GIÁ TRỊ thì vẫn là
`True`, tức "sạch". **Văn nói một đằng, số nói một đằng**, và cái được dùng để
quyết định là số.

## VÌ SAO ĐÂY LÀ CHỖ ĐẮT NHẤT

`11_khong_an_khe_dao_ngay` nằm trong **`CHAN_CUNG`** — chặn cứng, không phải
nhãn mềm. Và docstring của chính nó ghi lý do nó ra đời:

> *"Một ứng viên (EURGBP.H4.mua_qua_dem) đạt `t_alpha = 14,52` và đi hết cổng
> rẻ nhờ đúng cái đó — **không một cổng nào trong 10 cổng cũ nhìn thấy**."*

Một cổng chặn cứng sinh ra để bắt đúng một kiểu gian lận, mà **hỏng thì mở**,
sẽ cho ứng viên tiếp theo cùng kiểu đi qua y hệt.

## SỬA

Ba trạng thái thay vì hai:

| tình huống | `dk[11]` | verdict |
|---|---|---|
| đo được, sạch | `True` | có thể PASS |
| đo được, bẩn | `False` | FAIL |
| **không đo được** | `True` + tên vào `cong_khong_do_duoc` | **trần ở `UNG_VIEN`** |

Không phải `FAIL` — *chưa đo được không phải là bẩn*. Không phải `PASS` — *chưa
chứng minh được là sạch*. Thêm trường `cong_khong_do_duoc` vào kết quả: rỗng
nghĩa là mọi cổng chặn đều đã được đo thật. **Đọc trường này TRƯỚC khi tin một
verdict.**

## BẰNG CHỨNG
- 3 bài mới trong `test_hong_im_lang.py::CongChanCungHongThiMo`, kế thừa khuôn
  `SoTam` (chuyển `SO.DB` sang thư mục tạm — `CONG.xet` **ghi** vào sổ `fdr`,
  và chính cái chắn đó của dự án đã bắt tôi khi tôi quên).
- **A/B: 2/3 bài đỏ trên bản cũ**, 3/3 xanh trên bản mới. Bài thứ ba chỉ kiểm
  khai báo `CHAN_CUNG` nên xanh cả hai bên — và nó nên như vậy.
- Kèm **hiệu chuẩn ngược**: chuỗi ĐO ĐƯỢC và thật sự sạch thì **vẫn PASS**. Nếu
  thiếu bài này thì một cổng chặn tất cả cũng "xanh".

## HAI FIXTURE PHẢI SỬA — VÀ VÌ SAO ĐÓ KHÔNG PHẢI NỚI TEST

`test_cong_do_phan_giai` và `test_phoi_nhiem_holdout` truyền `df=None`, nên cổng
mới chặn trần chúng ở `UNG_VIEN`.

- `test_che_do_giao_dich_van_ra_PASS_duoc` là **bài kiểm LỰC** (*"nếu không còn
  đường nào ra PASS thì cả hệ vô nghĩa"*). Nó **phải** chạy trên chuỗi ĐO ĐƯỢC,
  nếu không nó đang đo thứ khác. Đã cấp 420 bar ngày (~60 mẫu mỗi THỨ, ngưỡng
  của `khe_gio_bat_thuong` là 30) với `open[i] = close[i-1]` → khe bằng 0 ở mọi
  ô: một chuỗi sạch **thật sự**.
- `test_placebo_truot_thi_tieu_suat_voi_p_bang_1` cố ý dùng `df=None` để kiểm sổ
  sách FDR. Khẳng định `verdict == PASS` chỉ là phụ. Nay nó khẳng định
  `UNG_VIEN` **và** `"11_..." in cong_khong_do_duoc` — một khẳng định **có
  nghĩa** thay cho một khẳng định tình cờ.
- `test_ha_xuong_UNG_VIEN_chu_KHONG_phai_FAIL` đòi `all(dieu_kien.values())` —
  **rộng hơn ý nó**, nên nó vỡ khi một NHÃN MỀM bất kỳ lật (`12_rr_thuc_te`,
  `5_placebo` — cả hai đều không chặn). Nay xét đúng các cổng `CHAN_CUNG`.

Ba thay đổi này đều **siết** bài kiểm cho đúng ý nó, không nới.

## TỔNG
**246 passed, 3 skipped, 2 failed** trên 14 file. Hai bài đỏ là
`test_chuoi_fdr_chi_nhan_p_alpha_lien_tuc` và
`test_che_do_nghien_cuu_tra_loi_duoc_cau_co_che` — đã đối chiếu
`reports/do_main.txt`: **đỏ sẵn trên `main`**.

---

## CỔNG THỨ HAI, CÙNG HÌNH DẠNG: `13_edge_vuot_spread`

```python
except Exception:
    _lai_rong = _phi_sp = 0.0
dk["13_edge_vuot_spread"] = (_phi_sp <= 0) or (...)    # ← _phi_sp = 0 ⇒ MỞ
```

Đo hỏng → `_phi_sp = 0` → `(_phi_sp <= 0)` là `True` → **cổng mở**. Một cổng
CHẶN CỨNG hỏi *"edge có dày hơn chi phí không"* lại đi qua **đúng lúc không đọc
được chi phí**. Cùng tầng, cùng hình dạng với cổng 11.

## PHẠM VI HẸP CÓ CHỦ ĐÍCH — VÀ MỘT THỨ TÔI ĐÃ BỎ

Tôi đã thử bắt cả *"đã có lệnh mà phí = 0"* — đúng về lý lẽ (giao dịch thì phải
trả spread). **Đã bỏ.** Hai lý do:

1. Nó chặn cả các chuỗi **nghiên cứu hợp lệ**, nơi chi phí là KHAI BÁO chứ không
   đo được — và `7_chi_phi_do_duoc` đã chặn sẵn đúng trường hợp đó.
2. Nó buộc tôi phải bịa số vào 5 fixture, và mỗi con số bịa lại làm trượt một
   điều kiện khác. Đó là dấu hiệu tôi đang **đánh nhau với fixture thay vì sửa
   lỗi**.

Một chốt chặn chặn nhầm tăng thì không phải là chặt hơn. Nay chỉ đánh dấu khi
phép ĐỌC thật sự thất bại; `0.0` khai tường minh vẫn đi qua như cũ.

## BẰNG CHỨNG
- 2 bài mới, gồm **hiệu chuẩn ngược** (`0.0` khai tường minh **vẫn PASS**).
- A/B: bài `cong_13` **đỏ trên bản cũ**, xanh trên bản mới.
- **197 passed, 3 skipped, 6 failed** trên 13 file. Cả 6 bài đỏ đã đối chiếu
  `reports/do_main.txt`: **đỏ sẵn** (2 ở `cong_fdr_v2`/`cong_do_phan_giai`,
  4 ở `test_chay_that`).
