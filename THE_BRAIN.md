# THE BRAIN — He dieu hanh phong lab giao dich tu dong 24/7

## KIEN TRUC 2 TANG (chia tai de RE) — QUAN TRONG NHAT
Nguoi dung co MAY NHA 20 luong (bat 2-5h/ngay) + mot VPS RE nhat ($3/thang). Chia:

| viec | chay o dau | vi sao |
|---|---|---|
| **Bot that 24/7** (V6, EURCAD) | VPS | phai chay lien tuc ke ca khi may nha tat |
| **CAO nguon + DeepSeek rut co che** | VPS | nhe, chi goi API + luu text, chay 24/7 dot token |
| **Xep hang doi TEST** (sinh cau hinh .set) | VPS | nhe, ghi vao `hang_doi_test.jsonl` |
| **QUET MT5 tester 15 luong** | **MAY NHA** | nang, can 20 core — dung cai da co, khong thue lai |
| **JUDGE + kiem cheo + cap nhat moc** | MAY NHA (sau test) | can ket qua tester |

**Dong bo VPS <-> may nha**: mot thu muc dam may CHUNG (Google Drive Desktop / Dropbox,
mien phi) gan tren ca hai. VPS ghi `hang_doi_test.jsonl` (cac cau hinh cho test) +
`thu_vien.db`. May nha khi bat: doc hang doi, chay tester song song, ghi
`ket_qua_test.jsonl` tro lai. VPS doc ket qua -> JUDGE -> cap nhat thu vien. Khong can
SSH/server phuc tap — chi la file trong thu muc dong bo.

Nen VPS **KHONG can** nhieu core/RAM/disk. F.VPS 1 Sale ($2,97) hoac F.VPS 2 ($6) la du.
Quet nang van o may nha, mien phi, khi ban bat.

---

DeepSeek la LAO DONG GIA RE: rat nhieu tay, moi tay lam MOT viec nho, ro input/output.
The Brain (orchestrator Python) la QUAN DOC: chia viec, xep hang doi, chay MT5, quyet
dinh cai gi song cai gi chet. LLM khong bao gio "tu do lam" — no luon nhan mot the viec
(task card) co ngu canh day du va tra ve JSON dung schema.

Trai tim la mot BANG CONG VIEC (SQLite): moi dong la mot task o mot trang thai. Cac
VAI TRO DeepSeek rut task, lam, ghi ket qua, sinh task moi. The Brain khong bao gio
cho mot LLM — no bom viec lien tuc, dot token o muc cao nhat.

## 8 VAI TRO (moi vai = mot system-prompt rieng, mot viec nho)

| # | vai tro | input | output | goi khi |
|---|---|---|---|---|
| 1 | **SCOUT**    | 1 muc vua cao (tieu de + 3000 ky tu) | co lien quan? loai? co ma nguon? | moi muc moi cao ve |
| 2 | **EXTRACTOR**| van ban day du 1 muc | MANG co che (JSON) + diem 0-12 | muc SCOUT duyet |
| 3 | **REVERSER** | thong ke ro tu passview (buoc luoi, lot theo tang, TP, chi bao tai diem vao) | LUAT bot (JSON) | co du lieu passview |
| 4 | **SURVEYOR** | 1 luat/co che | tai san nao hop + phep do de xac minh (JSON) | co che diem>=8 chua co tai san |
| 5 | **MAPPER**   | 1 co che + danh sach input EA khung | anh xa thanh cau hinh .set, HOAC "can EA moi" + mo ta | truoc khi test |
| 6 | **JUDGE**    | bang ket qua tester + moc | THAT/AO/CHUA_RO + ly do (doc PF/DD) | sau moi lo test |
| 7 | **OPTIMIZER**| cau hinh + ket qua + chang playbook dang o | <=6 cau hinh tinh chinh de chay tiep | JUDGE = CHUA_RO |
| 8 | **CODER**    | mo ta co che khong anh xa duoc | ma .mq5 cho input/logic moi | MAPPER = "can EA moi" |

Moi vai co file prompt rieng trong `prompts/` (vd `prompts/scout.md`). The Brain nap
prompt theo vai khi goi. Tach vai giup: (a) prompt ngan, ro, it lan man; (b) doi/ tinh
chinh mot vai khong dung cac vai khac; (c) chay song song nhieu vai cung luc.

## BANG CONG VIEC (SQLite `thu_vien.db`, bang `task`)
    task(id, vai, trang_thai, uu_tien, input_json, output_json, co_che_id,
         tao_luc, xong_luc, so_lan_thu)
trang_thai: CHO -> DANG -> XONG | LOI | BO
The Brain vong lap: lay task CHO uu_tien cao nhat -> goi vai tuong ung -> ghi output ->
sinh task con. Vd: EXTRACTOR xong -> sinh task SURVEYOR cho moi co che diem>=8.

## LUONG TASK (mot co che di tu tho den ket luan)
```
   [cao] --> SCOUT --> EXTRACTOR --+--> (co passview?) --> REVERSER --> SURVEYOR
                                   |                                       |
                                   +--> SURVEYOR <-------------------------+
                                             |
                                          MAPPER --(anh xa duoc)--> TEST(moc) --> JUDGE
                                             |                                      |
                                    (can EA moi)                          CHUA_RO --> OPTIMIZER
                                             |                                      |  (vong)
                                           CODER --> bien dich --> TEST             v
                                                                              THAT --> KIEM CHEO
                                                                                     (2 cap + walk-fwd)
                                                                                          |
                                                                                    cap nhat MOC
```

## CHIA NHO CONG VIEC TEST (The Brain lam, khong phai LLM)
- **song song hoa tester**: nhan ban thu muc du lieu MT5 thanh N ban (portable copies),
  moi core chay mot tester tren mot ban -> N config cung luc. Bai hoc: KHONG chay 2
  tester chung mot data-folder (de len nhau, hong bao cao).
- **hang doi test**: moi cau hinh MAPPER/OPTIMIZER sinh ra -> mot job test. The Brain
  rai job vao N slot core, thu ket qua, dua lai JUDGE theo lo.
- **don cache dinh ky**: sau moi K config, xoa `bases\*\history` cua cac cap khong dung
  trong 24h (bai hoc disk day 02/08). Giu parquet M1 goc trong `data/`.

## THANG DIEM CHI TIET (EXTRACTOR cham, 0-12)
| tieu chi | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **moi** | trung thu vien | bien the nho | co che khac | nguyen ly moi |
| **kiem duoc** | can tick/orderflow (CFD khong co) | can nhieu du lieu ngoai | can chi bao thuong | chi can OHLC+spread |
| **hop tai san** | khong ro tai san | tai san khong co M1 | co M1 nhung ngan | co M1 dai (>10 nam) |
| **bang chung song** | khong co | ly thuyet/blog | review/thoi gian ton tai | tai khoan that co lai |
Chi co che tong >= 8 vao hang doi. **Nhung phan quyet THAT (JUDGE) doc lap voi diem
nay** — diem cao chi de UU TIEN test, khong phai bang chung. Ket luan THAT can:
PF>=1,15 VA duong >=2 cap VA duong ca hai nua giai doan (CHANG 5 playbook).

## QUY TAC CUNG (nhung dieu The Brain khong bao gio pha)
1. Moi ket luan cuoi phai co so MT5 tester THAT tren M1 toan bo lich su. Python chi
   sang loc khi gia thuyet qua moi.
2. Doc PF va Sharpe TRUOC %/nam. PF<1,10 = nghi ngo don bay/ao.
3. Von = sut giam duong von, khong phai muc dung lo.
4. Khong nhan lot (martingale) tru khi backtest 13 nam THAT chung minh — mac dinh
   bac bo (Bigmouse pha san -19.970$).
5. Chong khop nhieu bat buoc: kiem cheo cap + walk-forward truoc moi ket luan THAT.
6. Chi nguon cong khai + passview tu nguyen. Khong truy cap trai phep.
7. Kiem disk truoc moi lo cao/test lon (Free_GB). Don cache khi < 20GB.

## NHIP DOT TOKEN (che do ultracode, tai nguyen vo tu)
The Brain giu **hang doi task luon day**: khi rong task, tu sinh task cao nguon moi +
task re-survey cac co che diem 6-7 chua test. Nhieu vai chay dong thoi (SCOUT +
EXTRACTOR + JUDGE cung luc tren cac task khac nhau). Muc tieu: khong bao gio de mot core
hoac mot khe API nhan roi. Gioi han duy nhat la ngan sach token/thang cua nguoi dung —
The Brain ghi so token da dot moi vong vao `nhat_ky_token`.

Xem `lab.py` (dang la ban 4-buoc, se nang thanh 8-vai + bang task), `PROMPT_DEEPSEEK.md`
(playbook + bay), `README_LAB.md` (cai VPS).
