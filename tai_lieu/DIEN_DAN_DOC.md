# DOC DIEN DAN NHIEU TRANG (`b dien-dan`) - 03/10/2026

Chu du an (thu nha 37ad / 5ce3): *"moi quoc gia can it nhat mot dien dan trader"*; *"danh sach nhieu trang: doc so trang roi di tung
trang, 3-5 giay / trang, nho 'da toi trang N' de lan sau doc tiep"*; *"quet lai 1 tuan / lan"*; *"cong cu cu ghi cung duong dan may cu +
cong 9222: doi sang trinh duyet AI cong 9224"*.

Day la buoc **TIM** cua day chuyen (TIM -> LAY lich su lenh -> HIEU luat -> LAM LAI -> THU -> CHINH): doc TRANG DANH SACH bai cua dien dan,
giu lai nhung bai co dau hieu luoi / DCA / EA / tin hieu (URL + tieu de + diem tu khoa, o `du_lieu_cao/dien_dan/<ma>.jsonl`, gitignore).
Mo tung bai va lay lich su lenh la buoc sau (`b link`, `b nc cc boc_lich_su`). Nguon moi chi vao day chuyen khi da co DAT o xac_nhan.

## Da lam / chua lam (noi that)

| Phan | Trang thai |
|---|---|
| Doc danh sach nhieu trang: tu dong tim trang ke (rel=next / so trang / mau URL), Referer = trang truoc, moc `den_trang` | xong, co test (`nhan/doc_dien_dan.py`) |
| Nhip / tran theo ten mien, robots.txt, 403-429-captcha-Cloudflare thi DUNG ten mien (nghi 15 phut x 2^n ... 24 gio), cong tuan 168 gio | xong, co test; dung CHUNG trang thai voi `b link` |
| 23 dien dan / 14 nuoc trong `config/dien_dan.json` (5 bat, 18 tat cho do that) | xong |
| Chrome AI 9224 (`cdp`, `cdp_render`): port sang cong 9224 + `.browser_thebrain`, khong con duong may cu | xong |
| **Thu voi Chrome that (Chrome 141 headless, dien dan gia HTTPS tren localhost)** | xong 03/10: tim ra + sua 2 loi an toan that (xem duoi) |
| **Chay tren dien dan THAT** | **CHUA**. Cloud khong toi duoc cac trang nay. `b dien-dan do` o may nha la lan do that dau tien |
| Nuoc chua co dien dan ung vien: pt, it, ko, ms, tl, bn | CHUA (can tim; xem `keywords_nguon.py`) |

## Cach dung o may nha

```
git pull
python b.py dien-dan ke-hoach                  khong mang: dien dan nao, se doc tu trang may, cho den bao gio
python b.py dien-dan do --ma traderviet_ea     tham do 1-2 trang (ke ca dien dan dang tat): co bai khong, co phan trang khong, goi y bat/tat
python b.py dien-dan quet                      doc tiep cac dien dan `bat: true` (ngan, xen ke; mac dinh toi da 10 trang / dien dan / luot)
python b.py dien-dan quet --ma a,b --toi-da-trang 3 --ep    thu ngan; --ep chi bo cong "1 tuan / lan"
python b.py dien-dan bao-cao                   dung lai bao cao tu trang thai (khong mang)
```

**Bat mot dien dan tat**: chay `do --ma <ma>` truoc; neu bao co bai va phan trang dung thi sua `"bat": true` trong `config/dien_dan.json`
(ghi chu o muc `kiem_tra`). Dien dan `cdp` / `cdp_render` can Chrome AI dang chay (`mo_trinh_duyet_ai.cmd`) - khong co thi duoc BO QUA
(`KHONG_CO_CHROME`), khong tinh la loi cua dien dan. Phien cloud chi ra don `ke-hoach | bao-cao | do | quet` (danh sach trang); dien dan `cdp`
chi chay duoc o may nha.

Quet lai 1 tuan / lan: moi luot xong thi `den_han = bay gio + 168 gio`; goi `quet` truoc han thi dien dan do duoc bo qua. Luot do (bi gioi han
trang / het tran ngay) ghi `den_trang`, lan sau noi tiep tu do, khong doc lai.

## Ba cach lay (chon TRUOC trong config, KHONG doi khi bi chan)

| `cach_lay` | La gi | Dung khi |
|---|---|---|
| `http` | yeu cau HTTP thang, khong cookie, UA trung thuc | dien dan cong khai, khong can dang nhap (mac dinh) |
| `cdp` | GET kem cookie cua Chrome AI, qua `context.request` cua Playwright (khong chay JS, khong phai ngan xep mang cua tab) | can dang nhap hoac cookie |
| `cdp_render` | mo TAB THAT trong Chrome AI, cho JS chay xong roi doc DOM | danh sach chi hien bang JS |

Chuyen huong chi duoc theo khi **cung ten mien goc + https**, toi da 3 buoc, moi buoc qua nhip; sang ten mien khac / ha xuong http / dia chi
noi bo / IP -> KHONG toi dich, ghi `CHUYEN_HUONG` (sua `url` trong config, khong tu theo). Phan hoi la tep tai ve (`attachment`) hoac khong doc duoc
nhu trang (exe, zip, pdf, octet-stream, thieu Content-Type) -> chan, Chrome khong luu gi ve may.

## KHONG lam

- Khong tu dang ky, dang nhap, tham gia nhom, follow, dang bai: module nay chi DOC trang danh sach. Tao tai khoan / join / follow la viec khong
  khu hoi, chu du an duyet truoc (CLAUDE.md), va co kiem soat spam o `tu_follow_join.py` (chua port).
- Khong giai captcha, khong gia nguoi: man chan -> dung ten mien do, ghi ma loi, het.
- Khong mo ho so Chrome goc (Profile 3), khong dung cong 9222; chi cong 9224 (`mo_trinh_duyet_ai.cmd`).
- Khong dua URL / tieu de bai / ten may vao bao cao gui ve cloud (repo PUBLIC): bao cao chi co ma dien dan, nuoc, so dem, ma loi, ID tin hieu MQL5.
- Khong chay `b dien-dan` va `b link chay` cung luc (chung mot file trang thai, chi co mot nguoi ghi).

## Ket qua thu voi Chrome that (03/10, Chrome 141 + Playwright 1.63, cong CDP rieng 19224, KHONG phai 9224)

Dien dan gia HTTPS tu ky tren localhost (ten mien gia qua `/etc/hosts` trong sandbox cloud, da hoan nguyen), nhat ky yeu cau o phia may chu:

1. `ctx.request.get(max_redirects>0)` **tu theo ca sang ten mien KHAC** -> dat `max_redirects=0` va tu theo tung buoc (da sua, da kiem).
2. Loi Playwright co "Call log: GET https://..." -> lo URL vao trang thai / bao cao -> da cao sach (`_khong_url`, `_loi_ngan`), mot dong, <= 100 ky tu.
3. **`page.route` cua Playwright KHONG duoc goi cho cac buoc chuyen huong** (ke ca khi buoc dau dung `route.fetch(max_redirects=0)` +
   `route.fulfill`), nen Chrome van cham ten mien khac. Lop **Fetch cua CDP** (qua `new_cdp_session`) o CA hai giai doan Request + Response
   chan dung: may chu dich khong nhan gi. `cdp_render` dung cach nay, chi tren KHUNG CHINH.
4. Tai nguyen phu (anh, CDN) o ten mien khac van tai nhu trinh duyet thuong - **co y**: chi chan DIEU HUONG khung chinh, khong chan trang tai anh.
5. Chrome tu dung vong chuyen huong sau ~20 hop; ta dung o hop thu 4 (`qua nhieu lan chuyen huong`).
6. Popup do script tu mo (`window.open` khong co thao tac nguoi dung): Chrome mac dinh CHAN, tab khong tang. Chua kiem voi co dong lenh khac
   cua Chrome AI that: neu `mo_trinh_duyet_ai.cmd` tat chan popup thi cua so moi KHONG nam trong bo loc nay (gioi han da biet).

Neu Chrome cua chu du an (ban 154) doi cach danh so khung nen su kien Fetch dau tien khong khop khung chinh, bo loc DONG (loi
`khung_chinh_khong_khop`) thay vi am tham tat; ket qua se hien o bao cao va duoc xem la CHUA_DO_DUOC, khong phai ket qua am.

## Dem tran ngay

Tran `yeu cau / ngay / ten mien` (`tran_ngay_mien` 120, mql5.com 60) dem moi yeu cau TRANG (ke ca moi buoc chuyen huong, moi trang con do script tu mo
cung ten mien o che do render). Khong dem yeu cau phu (anh, script, XHR) cua mot trang vi do khong qua bo loc tai lieu; nhip van la nhip cua ten mien.

## Doi chieu

- `LINK_NGUON.md` (b link: tham do + lich su lenh), `KIEM_KE_NGUON.md` (71 nguon + 19 ung vien dien dan quoc gia da dang ky trong code),
  `NGUON_NGUOI_THANG.md` (thu tu khai thac), CLAUDE.md muc "TRINH DUYET AI + NGUON DIEN DAN DA NGON NGU".
- Test: `test_doc_dien_dan.py` (khong mang that; Chrome gia bang doi tuong CDP gia). Bai thu Chrome that nam o scratchpad cua phien cloud, khong vao git.
