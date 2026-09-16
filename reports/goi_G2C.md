# GOI G2-C — GHI CONFIG NGUYEN TU + LAN TAI NGUYEN · 16/09/2026

**Noi ngan:** hai lo hong, ca hai thuoc loai **khong bao loi**. Mot cai phai
xay moi; mot cai da co san 90% va chi thieu mot buoc — nhung buoc thieu do la
buoc quyet dinh.

## 1. `nhan/ghi_an_toan.py` (moi)

Doc-sua-ghi `config/*.json` truoc day khong co khoa nao. Hai phien cung sua:

```
A doc {"x":1} · B doc {"x":1} · A ghi {"x":2} · B ghi {"y":3}
-> thay doi cua A BIEN MAT, khong mot dong log nao
```

`sua_json(duong_dan, ham_sua)`: khoa lien tien trinh (`O_CREAT|O_EXCL`, nguyen
tu o muc he dieu hanh) cho CA khoang doc-sua-ghi -> ghi file tam -> `os.replace`
**co thu lai** -> **doc lai xac nhan**, lech thi nem `GhiHut`.

Khac `du_lieu._ghi_cache` co y nuot loi (cache hong thi tinh lai duoc), file
nay **nem**: mot cau hinh ghi hut la mot quyet dinh bi mat.

## 2. Cuoc dua trong `ngan_sach.xin()` — cai nguy nhat gap hom nay

Ban cu: **dem roi moi giu the**.

```python
if tran is None or _dang_giu(lop) < tran:
    the.write_text(...)          # <- khe cua so o giua
```

Hai tien trinh cung thay `_dang_giu < tran` roi **ca hai** cung ghi the. Voi
`SUC_CHUA["TESTER"] = 1` thi do la **hai luot tester cung luc** — dung cai hong
ma ca gioi han TESTER=1 sinh ra de chan, va no ghi de ket qua ma bang so doc y
het mot ket qua that.

Nay: **giu the truoc, dem sau**. `_duoc_o_lai()` xep the theo `(mtime, pid)` va
chi `tran` the cu nhat duoc o lai; ai den sau tu tra the roi cho. Khong con khe
cua so nao giua "thay con cho" va "chiem cho", va khong can trong tai vi moi
tien trinh deu suy ra cung mot thu tu.

**Cai da co san:** `ngan_sach` von da dem lan **toan may** bang the theo PID co
thu hoi the cua tien trinh chet. Yeu cau 3 cua bang ke hoach coi nhu da xong tu
truoc — chi thieu dung cho chong dua.

## 3. Test bat duoc mot loi trong chinh ma moi viet

Lan chay dau, bai 10 tien trinh **that bai** — khong phai o cho du doan:

```
FileNotFoundError: ... c.json.lock
  qua_han = time.time() - tep.stat().st_mtime > HAN_KHOA_GIAY
```

Giua luc `O_EXCL` that bai va luc `stat()` chay, chu khoa da **tra khoa xong**.
`stat` nem FileNotFoundError va no thoat ra ngoai nhu mot loi that. Da sua:
khoa bien mat nghia la den luot ta, quay lai vong ngay.

Day dung la ly do phai viet bai 10 tien trinh that thay vi tin vao lap luan.

## Rui ro con lai

- **Chua thay duong ghi config cu bang `sua_json`.** Quet duoc cac cho khai
  duong dan config: `chi_phi.CAU_HINH`, `tri_tue.CAU_HINH`, `tran_cpu.CAU_HINH`,
  `slot_tester.TEP`, `tai_khoan_nen_tang.EMAIL_CAU_HINH`,
  `dieu_khien_xa.CAU_HINH`, + vai script `credentials*.json`. Buoc sau: doi
  tung cho, chay test sau moi cho.
- `khoa_tester.json` co duong ghi rieng (khoa cua chinh no) — khong doi, doi se
  thanh khoa long khoa.
- `HAN_KHOA_GIAY = 120` la mot con so chon, chua do: chua biet lan sua config
  lau nhat la bao nhieu.

## Test

`test_ghi_an_toan.py` — 8 bai, pass het:
- **10 tien trinh x 20 lan sua mot file -> du 200, khong hut mot lan nao**
  (phep thu bang ke hoach doi)
- ham_sua nem loi thi **khong ghi gi** va khong de lai file tam
- khoa mo coi (pid da chet) duoc thu hoi
- khoa duoc tra sau khi xong
- `_duoc_o_lai` chi giu the cu nhat, the cua pid chet bi thu hoi

Hoi quy `-k "ngan_sach or tran_cpu or dia or so_sach or slot or bang_he or
ghi_an_toan or so_ghi_lo"` -> **96 passed**.
