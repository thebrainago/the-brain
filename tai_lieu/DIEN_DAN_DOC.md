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
| Doc danh sach nhieu trang: tu dong tim trang ke (rel=next -> `mau_trang` -> link so trang -> suy mau tu >= 2 link -> nut "trang sau"), Referer = trang truoc, moc `den_trang` | xong, co test (`nhan/doc_dien_dan.py`). **Sua 08/10**: ban 03/10 chi DEM so tren thanh phan trang, khong di theo, va coi "khong thay trang ke" la "het" -> xem muc ngay duoi |
| Nhip / tran theo ten mien, robots.txt, 403-429-captcha-Cloudflare thi DUNG ten mien (nghi 15 phut x 2^n ... 24 gio), cong tuan 168 gio | xong, co test; dung CHUNG trang thai voi `b link` |
| 23 dien dan / 14 nuoc trong `config/dien_dan.json` (5 bat, 18 tat cho do that) | xong |
| Chrome AI 9224 (`cdp`, `cdp_render`): port sang cong 9224 + `.browser_thebrain`, khong con duong may cu | xong |
| **Thu voi Chrome that (Chrome 141 headless, dien dan gia HTTPS tren localhost)** | xong 03/10: tim ra + sua 2 loi an toan that (xem duoi) |
| **Chay tren dien dan THAT** | **CHUA**. Cloud khong toi duoc cac trang nay. `b dien-dan do` o may nha la lan do that dau tien |
| Nuoc chua co dien dan ung vien: pt, it, ko, ms, tl, bn | CHUA (can tim; xem `keywords_nguon.py`) |

## Tim trang ke + trang thai trung thuc (08/10/2026)

Chu du an hoi vi sao "hon 70 nguon" ma quet duoc co mot chut. Do that (8 don `quet-sau` o may nha, ma cu + config cu): 6/8 don **BO_QUA** vi dien dan dang tat trong
config cu cua may nha, 2/8 doc dung 1 trang roi bao XONG, ma thoat 0 -> don ghi **DAT**. Hai loi trong ma:

1. Ban cu chi dem so ghi tren link ("1 2 3 ... 5842") roi bo; neu dien dan khong co `rel=next` va config khong khai `mau_trang` thi "khong co URL trang ke" bi hieu la **het
   danh sach** (XONG_PASS, nghi 168 gio) du con 5842 trang.
2. `b dien-dan quet` thoat 0 ke ca khi moi dien dan deu bi tat / bi chan / khong di tiep duoc -> `cong chay_duoc` ghi DAT.

Nay (`nhan/doc_dien_dan.py::tim_trang_tiep`), theo thu tu, dung o cach dau tien cho ra URL (`phan_trang: auto`):

| # | `cach` | Cai gi |
|---|---|---|
| 1 | `rel_next` | `<link rel=next>` / `<a rel=next>` cung ten mien, khac trang dang doc |
| 2 | `mau_trang` | mau URL khai trong `config/dien_dan.json` (`{base}` = url cua dien dan, `{n}` = so trang) |
| 3 | `neo_so` | link CHINH XAC ghi so trang ke (thanh phan trang `1 .. 4 5 6 .. 120` co `6`) |
| 4 | `mau_suy_ra` | thanh phan trang rut gon `1 2 3 .. 5842` khong co link trang ke: suy URL tu >= 2 link so >= 2 cung danh sach, CHI khi cum so doi la ham tuyen tinh NGUYEN cua so tren link (`page-N`; phpBB `start = 25*(N-1)`) va khong vuot so lon nhat thanh phan ghi |
| 5 | `chu_tiep` | nut "Next ›", "Trang sau", "下一页", "Следующая"... (da ngon ngu). Chi mui ten DON ›; « » >> bi bo vi nhieu giao dien dung cho "TRANG CUOI" |

Link chi duoc nhan khi thuoc **chinh danh sach dang doc** (cung ten mien + cung duong dan sau khi bo vi tri trang / ma phien / tham so sap xep, hoac cung duong dan voi
`<link rel=canonical>`): "2 3 .. 120" duoi tung chu de (`/threads/x.1/page-2`) khong bi nham voi phan trang cua danh sach. `phan_trang: mau` = chi `mau_trang`, `khong` = chi doc trang 1.

**Khong tim duoc duong sang trang trong khi thanh phan trang bao con trang** -> ket qua `KHONG_THAY_TRANG_TIEP`: loi CAU HINH, **khong phai XONG** (nghi 24 gio, giu moc
`den_trang`, khong tang `so_pass`, hien o bao cao). Cach sua: khai `mau_trang` cho dien dan do (doc 2 URL trang 2, trang 3 bang tay roi suy mau), hoac dat `phan_trang: khong`
neu chi can trang 1. `b dien-dan do --ma <ma>` nay in `tong_trang_uoc` + `cach_trang_tiep` + goi y dung cau ("bao co N trang nhung KHONG tim thay link trang 2", hoac
"co link danh so trang nhung khong cung duong dan voi `url` - dien dan chuyen huong? dat `url` la dia chi cuoi cung").

**Ma thoat `b dien-dan quet`**: `0` = co tien (it nhat mot dien dan doc them trang / xong mot pass) hoac chi dang cho (nhip, tran ngay, chua den han 1 tuan) · `3` = ma khong co trong
config · `5` = **khong dien dan nao tien duoc** (khong dien dan nao duoc chon / tat het, BO_QUA, KHONG_THAY_TRANG_TIEP, CHUYEN_HUONG, bi chan...): in `!! DIEN_DAN_KHONG_TIEN: ...`,
`qwen/cau_loi.py` xep vao `can_chan_doan`, don **khong** ghi DAT. Hong mot phan (mot dien dan loi, cac dien dan khac tien): in `!! N dien dan khong tien duoc: ma(KET_QUA)`, thoat 0.

Gioi han da biet: thanh phan trang tro sang duong dan KHAC `url` trong config va canonical (dien dan chuyen huong ten mien / doi duong dan) thi khong tim duoc trang ke
-> sua `url` thanh dia chi cuoi cung, hoac khai `mau_trang`. Test: `test_doc_dien_dan.py` muc 10 (6 kieu phan mem dien dan, danh sach 5842 trang doc 5 trang / luot noi tiep o
trang 6 trong tien trinh moi, link chu de, ma thoat) - 42 ca hong khi chay lai hanh vi cu.

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
