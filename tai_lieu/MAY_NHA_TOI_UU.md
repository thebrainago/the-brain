# MAY NHA: QUET, DO, GIAM SAT, TOI UU

*Chu du an 03/10/2026: "lo toi uu khau giam sat may nha, phan claudecode tren may nha can quet may va biet bao cao gi cho hop ly.
May nha 10 nhan 20 luong nhung ram 32gb chi co 1 thanh nen khong dung het toc luc. Moi mua them 1 hdd 230gb de giai quyet phan nao
van de tran bo nho. Do dac va tinh toan ky toc do va nguong gioi han phan cung toi da co the khai thac (toi van cho hoat dong 75-80% cpu).
Can tao them tk mt5 de test thi bao toi can tao toi da bao nhieu."*

Ma: `nhan/may_nha.py` (`b may ...`) · Test: `test_may_nha.py` (168 ca, khong can may that: PowerShell duoc gia lap) ·
Tool **khong doi cai dat Windows nao**: moi de xuat in kem buoc, chu du an tu lam.

## 0. Ket luan truoc (cloud, CHUA do tren may that - doc muc 9 de biet con thieu gi)

1. Tool tra loi duoc bon cau: may GIOI HAN o dau (CPU / bang thong RAM / dung luong cam ket / dia) · o 75-80% CPU ta duoc bao nhieu %
   toc do toi da · moi loai viec chay toi da bao nhieu viec song song · tao toi da bao nhieu tai khoan MT5.
2. **RAM 1 thanh = 1 kenh.** Do 13/09: bai mang lon 1 luong 8,9 GB/s · 20 luong 9,4 GB/s (phang). Viec doc nhieu bo nho (quet M1 nhieu nam)
   KHONG chay nhanh hon khi them luong - day la tran cua 1 kenh, khong phai loi CPU. Viec nhe nam trong cache (quet D1, engine luoi chuoi ngan)
   van chay duoc het 10 nhan. Muon het nghen: them thanh RAM CUNG LOAI vao khe KHAC KENH (muc 5).
3. **HDD 230 GB khong lam may nhanh hon.** No chi lam may KHONG CHET khi tran bo nho (file trang co dinh, muc 5) va chua duoc du lieu nguoi.
4. Tai khoan MT5 demo can tao: **tam thoi 4** (uoc tu so lieu, con so RAM/agent va bang thong/agent la GIA DINH). So that chot sau `b may do`
   + phep thu tung buoc tren MT5 that (muc 4). Neu XM cho mot tai khoan dang nhap nhieu terminal thi KHONG can tao them.
5. Giu tran CPU 75-80% la dung neu `b may do` bao o ~78% may dat >= 85% toc do toi da (chay 100% chi them it ma may giat).

## 1. Phien nha lam gi khi MO PHIEN (khoang 30 giay)

```
git pull
b may                    # quet phan cung + lay mau + ket luan; ghi reports/may_nha_*.json|md (an danh); in them "24 GIO QUA"
```

Dong dau cua bao cao: `BAO CAO MAY NHA [XANH|VANG|DO]`. Phien nha doc roi lam theo bang nay:

| Den | Nghia | Phien nha lam |
|---|---|---|
| XANH | Chua co gi sap hong | **IM LANG** voi chu du an. Chi ghi so tay neu co so do moi (vd sau khi do co gian). |
| VANG | Se hong neu cu tiep tuc (cam ket bo nho con < 8 GB, RAM trong < 3 GB, o he thong < 20 GB, o du lieu < 2 GB, doc file trang > 1.000 trang/giay) | Mot dong cho chu du an o cau tra loi ke tiep: ly do + viec chu du an can lam (neu co). Khong ngat viec dang chay. Neu van VANG sau 2 lan mo phien: gui thu cloud (`b cau noi`). |
| DO | Dang/sap hong that (cam ket bo nho con < 3 GB, RAM trong < 1,5 GB, o he thong < 5 GB) - 13/09 het cam ket la `ENOMEM` du RAM con 17 GB | Bao NGAY (1-3 dong). KHONG khoi dong viec nang moi cho den khi het DO. Viec chu du an can lam dung dau. Gui thu cloud. |

**KHONG bao** (chu du an muon day CPU 75-80%): CPU cao (ke ca 100% van XANH), so tien trinh python, loi trang nho, RAM it tien trinh.
Den CHI do cai lam may chet, khong do cai ban.

Mau bao cao 3-8 dong khi chu du an HOI tinh hinh may (khong tu bao khi XANH):

```
May nha: XANH. 24 gio qua CPU TB 77% (66% thoi gian trong dai 75-80%, 30% DUOI dai = may ranh, 4% tren dai).
Cai nghen: viec doc nhieu RAM chi chay hieu qua ~N viec cung luc (RAM 1 thanh). Viec nhe: ~M viec.
Toc do nghien cuu: ~X luot thu/gio (so voi hom qua Y).
Chu du an can lam: (chi neu CO) them RAM cung loai / dat file trang HDD / doi ke hoach dien.
```

Cac muc "CHU DU AN CAN LAM" va "PHIEN NHA / MAY TU LAM" trong bao cao la danh sach viec da phan loai san (`ai_lam`, `can_phep`). Muc nao `ai_lam=may`
(vd `b tran-cpu 78`, cai trinh bien dich C) thi phien nha lam ngay, KHONG hoi. Muc nao `chu_du_an` (mua RAM, doi Windows) thi khong tu lam.

## 2. Bon thu tool do (khong doan)

| Lenh | Lam gi | Mat bao lau | Khi nao |
|---|---|---|---|
| `b may quet` | Phan cung that: CPU, thanh RAM (loai/MT/s/ECC/khe trong/ma hang), o dia SSD/HDD, file trang, ke hoach dien, MT5 dang cai | ~3 giay | Moi phien, hoac truoc khi mua RAM |
| `b may mau [--nang]` | Mot mau: CPU, RAM trong, **dung luong cam ket** (RAM + file trang), dia, so tien trinh MT5/python. `--nang` them hieu nang WMI | ~1-3 giay | Chay tu dong moi 5 phut qua `b cau chay` |
| `b may do [--nhanh] [--ep] [--toi-da N]` | **Do co gian**: cung mot viec chay 1, 2, 4 ... N tien trinh -> toc do tong, 4 loai viec + dia | `--nhanh` ~1 phut · day du ~5 phut | Khi may RANH (CPU nen < 35%). Dang ban thi tu choi (`CHUA_DO_DUOC`); `--ep` do du ban nhung ket qua gan `nhieu_nen` va KHONG dung de chot so |
| `b may giam-sat [PHUT] [CHU_KY]` | Lay mau day (mac dinh 10 phut, 15 giay) -> bao nhieu % thoi gian CPU trong dai 75-80% | PHUT | Luc dang chay test that, de biet may co du ngua khong |

Bon loai viec cua `do` (moi loai tra loi mot cau hoi khac nhau):

- `cpu_nho` - vong lap Python gon trong cache (kieu quet D1). Tuyet doi doc lap. Cho biet gioi han CPU THUAN + loi ich hyperthreading.
- `luoi` - CHINH engine luoi (`luoi_nhan`: nhan C neu co) tren 60.000 nen (nam trong cache). Cho biet **luot thu / gio** o ~80% CPU.
- `luoi_dai` - cung engine tren **1 trieu nen** (40 MB moi tien trinh, lon hon cache): kieu quet M1 nhieu nam. Chi chay khi nhan C san sang.
- `bang_thong` - doc/ghi mang lon (STREAM): cham tran KENH RAM. Cho biet GB/s toi da va **bao nhieu viec thi het loi**.
- `dia` - ghi tuan tu + ghi ngau nhien 4 KiB co fsync tren tung o. Phan biet kieu HDD / vua / nhanh bang IOPS.

Cach tool ket luan (da co test, doc `ket_luan()` neu can):

- **Bao hoa** = n nho nhat ma them tien trinh nao nua cung chi them < 10% toc do. Chi xet n <= so luong (chay nhieu hon so luong chi chia thoi gian).
- **O ~78% CPU** = round(0,78 x so luong) viec song song; in "may dat X% toc do toi da". X >= 85 -> giu tran 75-80.
- **Nghen RAM** khi bao hoa cua viec doc-nhieu-RAM < 60% bao hoa cua viec nhe. Khi do moi noi "cai nghen thuc su" va moi de xuat them RAM.
- **Nang RAM co loi toi da bao nhieu**: min(ty le "chuoi trong cache nhanh hon chuoi o RAM bao nhieu lan", so kenh toi da cua nen tang / so kenh dang dung).
  So kenh toi da suy tu doi CPU (E5 v3/v4 = 4 kenh/o cam, Core/Ryzen thuong = 2, Xeon Gold = 6, EPYC = 8) - **la uoc, xem so tay bo mach**.
- Do duoc `None` thi in "?" va ly do, khong bao gio thay bang 0.

## 3. Giam sat lien tuc (khong ton token)

- `b cau chay` (Task Scheduler moi 5 phut, khong dung LLM) **moi luot lay MOT mau nhe** -> `nhat_ky/may_nha_mau.jsonl` (cuc bo, gitignore, tu xoay vong o 12 MB).
- Nhip tim `viec/may/<ten>.json` chi ghi lai khi **DOI MAU DEN** hoac sau > 60 phut (de khong sinh 288 commit/ngay). Phien cloud thay dong
  `suc khoe may: VANG - ly do` trong `b cau lay` khi den khac XANH.
- `b may` (bao-cao) doc nhat ky 24 gio: CPU TB/p95, % thoi gian trong/duoi/tren dai 75-80, RAM trong va cam ket con lai THAP NHAT, % thoi gian MT5 chay.
  % thoi gian DUOI dai la "may ranh" - neu cao thi viec dang thieu, khong phai may yeu: day them viec (xem `b q trang-thai`).
- Giam sat KHONG bao gio giet viec: chi doc va bao. `dieu_toc` (tran CPU), `ngan_sach` (cho phep viec) van la thu quyet dinh chay hay khong.

## 4. TAO BAO NHIEU TAI KHOAN MT5 (cau tra loi cua tool + cach kiem tra that)

Tool dung `so_mt5_toi_da` = **MIN cua 4 tran**:

| Tran | Cach tinh | Do hay doan |
|---|---|---|
| CPU | ~78% x so luong (10 nhan / 20 luong -> 16) | do (so luong) |
| RAM | (min(RAM trong, RAM tong - 6 GB de danh) - 2 GB) / RAM moi agent | **GIA DINH 2,5 GB/agent** (Model 0/4); do that neu luc do co agent chay |
| Bang thong | dinh `bang_thong` do duoc / 2 GB/s moi agent | dinh do; **2 GB/s/agent la GIA DINH** |
| Dia | dung luong trong / ~8 GB moi terminal (du lieu tick + cache) | **GIA DINH 8 GB**; do that neu da cai terminal |

- 1 **tai khoan** = 1 terminal MT5 (moi terminal can thu muc du lieu rieng, ban portable - `SLOT_TESTER.md`).
  **Chua kiem:** XM co cho cung mot tai khoan dang nhap nhieu terminal cung luc khong. Neu co -> khong can them tai khoan.
- **Che do Optimization**: MOT terminal tu chia viec cho N agent tren cac nhan cua may (can 1 tai khoan). Dung de LOC (cuc dai chon tren cung du lieu =
  lua chon, khong phai phep do), roi chay lai don o Model=0/4 + doan xac_nhan. Day la cach de nhat de dung het nhan cho MT5.
- **Cap 'tam thoi 4'** la gia tri khi RAM 1 kenh (dinh ~9,4 GB/s / 2 GB/s ~ 4). Khi nang RAM len nhieu kenh, tran bang thong tang theo so kenh va
  tran CPU (~15-16) moi la cai chan.

**Kiem tra that tren MT5 (vi tool KHONG do duoc MT5 - day moi la so quyet dinh):**

```
Buoc 0  b may do --nhanh                          -> so UOC N (khong cai them gi)
Buoc 1  Cai terminal #1, chay MOT test chuan (EA tham chieu, 1 nam, Model 0/4) MOT MINH     -> T1 giay (cot `giay` cua ea_tho_quet)
Buoc 2  Cai terminal #2 (tai khoan rieng, hoac cung tai khoan neu XM cho). Chay HAI test cung luc -> T2 moi ben
        T2 <= 1,25 x T1  => hai terminal khong chen nhau, tiep tuc
Buoc 3  Them #3, #4 ... mot cai mot. Dung khi thoi gian moi lan > 1,25 x T1, HOAC CPU > 80%, HOAC `b may` bao VANG/DO.
        So terminal ngay truoc luc dung = TOI DA that
Buoc 4  Che do Optimization 1 terminal, N agent: thoi gian N agent / 1 agent -> co gian that cua MT5
Ghi:    Moi buoc ghi vao muc 9 duoi day (giay/lan, CPU %, RAM trong, den).
```

Cam: hai viec MT5 tester cung luc tren CUNG MOT terminal (ghi de ket qua nhau, khong ai bao loi - `khoa_tester`). Moi terminal mot lan chay.

## 5. RAM 1 thanh + HDD 230 GB: lam gi, khong lam gi

**RAM (cai that su lam may nhanh):**
- Them thanh CUNG LOAI voi thanh dang co (tool in loai/MT/s/ECC/RDIMM + **ma hang** o bao cao `b may`). Neu thanh hien tai la ECC RDIMM thi them ECC RDIMM;
  **khong tron RDIMM voi LRDIMM**; khong tron non-ECC voi ECC. Chua chac -> chup anh nhan thanh dang co gui phien cloud de chon dung ma.
- Cam vao khe **KHAC KENH** (khe vi tri 1 cua moi kenh; xem so tay bo mach). Them 1 thanh: 1 -> 2 kenh, bang thong ly thuyet gap 2 lan. Du bo: gap 4 lan (neu nen tang 4 kenh).
- Gia tri: chi lam nhanh **viec doc nhieu RAM** (quet M1 nhieu nam, agent MT5 nang). Viec nhe nam trong cache khong nhanh hon. Tool in "loi toi da ~xN" sau khi do.

**HDD 230 GB:**
- **Dung de:** (1) file trang CO DINH lam luoi an toan; (2) du lieu NGUOI: luu tru `data/` cu, ban sao luu, log tester, dump CSV M1 da xuat, `reports/` cu.
- **KHONG dung de:** bo nho lam viec (cham ~100 lan SSD: neu may phai doc/ghi file trang LIEN TUC thi dung hinh), `nao.db`, `bases/` cua MT5, parquet nong, repo.
- **File trang tren HDD** (chu du an lam tay, khong bat buoc khoi dong lai de dung nhung nen):
  `Win+R` -> `sysdm.cpl` -> **Advanced** -> Performance **Settings** -> **Advanced** -> Virtual memory **Change** -> bo "Automatically manage" -> chon o HDD
  -> **Custom size**: Initial = Maximum = ~58.000 MB (goi y ~25% HDD, 32-64 GB) -> **Set** -> OK. Giu o `C:` o che do tu quan ly hoac dat 8-16 GB co dinh.
  Tong cam ket = RAM + moi file trang. 13/09: o C con 233 MB, file trang khong gian ra duoc, `ENOMEM` du RAM con 17 GB. File co dinh tren HDD ngan dung loi nay.
- Windows tu chon ghi vao file trang nao; ta khong ep duoc. Dau hieu RAM that su thieu: `b may` bao "doc file trang > 1.000/giay" (VANG). Luc do **giam so viec**,
  dung them HDD.
- Tool KHONG tu lam: ke hoach dien (`powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c` = High performance, khong ha xung / khong ngu nhan), file trang, mua RAM.
  Tat ca nam trong "CHU DU AN CAN LAM" cua bao cao.

**Phan mem (hai viec KHONG can mua gi):**
- `b tran-cpu 78` (mac dinh trong code la 85; `config/qwen.json` `muc_tieu_cpu_ultra` 95): dua tran ve giua dai 75-80.
- `ngan_sach.xin` nay kiem them **cam ket bo nho con lai (Windows)** truoc khi nhan viec nang (truoc chi nhin RAM trong + so tien trinh python:
  khong thay loi 13/09). Xem `test_ngan_sach*.py`.

## 6. Lenh qua kenh cau (danh sach trang)

Cloud giao viec: `b cau giao -- may quet` · `-- may mau --nang` · `-- may bao-cao` · `-- may do --nhanh [--ep] [--toi-da N]` · `-- may giam-sat [PHUT 1-180] [CHU_KY 5-300]`.
`do` va `giam-sat` di lan **TESTER** (doc quyen: khong co viec khac chay cung, vi do luc ban cho so SAI); `quet`/`mau`/`bao-cao` di lan CPU.
Khong co lenh nao DOI cai dat may: `may ap-dung`, `powercfg`... bi tu choi o cong (`test_may_nha.py::TestDanhSachTrangMay`).
Ket qua tu ve cloud qua `reports/may_nha_*.json|md` (nho, an danh: ten nguoi dung/ten may thay bang `<user>`, bo khoa kieu serial; repo PUBLIC).

## 7. Neu lan chay dau o may nha bao loi (ket qua cloud khong thay the duoc phan Windows)

Cloud chi chay duoc **nhanh Linux du phong** + gia lap PowerShell (168 test). Cac duong Windows (PowerShell/CIM, ctypes cam ket bo nho, ke hoach dien) CHUA chay tren Windows that.
Neu `b may quet` ra `do_duoc_bang_powershell: false`, hoac cam ket/khe RAM la `None` -> gui cloud (`b cau noi`) **noi dung `loi_powershell`** va cac truong `None`,
kem phien ban Windows/PowerShell (`$PSVersionTable`). Muc tieu: sua tai cloud, khong sua mo tren may nha.
Sua ket luan sai (vd dem nham kenh RAM) = sua `_kenh_tu_ten_khe` / `_doc_ram` + them ca test voi ten khe that cua bo mach.

## 8. Cac viec KHONG lam (da can nhac)

- Khong ep Windows ghi vao file trang nao, khong tat file trang, khong "toi uu RAM" bang phan mem dong; khong RAM disk tren HDD; khong ReadyBoost.
- Khong chay `do` khi may dang ban roi bao la "so cua may" (so se dep nhung sai) - tool tu choi.
- Khong dung con so 2 GB/s va 2,5 GB cua agent MT5 nhu su that: la gia dinh duoc dan ra trong bao cao cho den khi co agent chay that.
- Khong mua them gi ma chua `b may do`: viec dau tien la do, khong phai cai them.

## 9. SO DO THAT (phien nha dien sau lan `b may do` dau tien)

```
Ngay do / CPU / RAM / HDD/SSD:        ...
Bang thong RAM do duoc (dinh, GB/s):   ...   (% muc ly thuyet ...)   bao hoa tu n = ...
Viec nhe (cpu_nho): o ~78% CPU duoc ... % dinh; hyperthreading cho them ...%
Engine luoi: luot/gio o 80% CPU ... (cache) / ... (chuoi dai)
Cai nghen thuc su: ...
MT5: UOC N = ... | Buoc 1 T1 = ... giay | Buoc 2 T2 = ... | TOI DA that = ...
Dia: o ..: ghi ... MB/s, ... IOPS (kieu ...)
```

## 10. CO CAN THUE VPS KHONG (03/10/2026, tra loi chu du an - chua do, chua thue)

**Ket luan: CHUA thue ngay.** Thue khi da co it nhat MOT EA qua cong that (`DAT` o xac_nhan) de chay demo / forward 24/7. Luc do VPS la de GIU EA SONG, khong phai de test nhanh hon.

- **VPS KHONG giup:** (a) quet / backtest nhanh hon - vCPU thue yeu, it nhan, it RAM hon may nha 10 nhan/20 luong; viec dang lam hon la them thanh RAM thu hai CUNG LOAI de chay 2 kenh (muc 5).
  (b) cao web - IP datacenter hay bi MQL5 / Myfxbook chan hon IP nha; viec cao giu o may nha (`b link`, `LINK_NGUON.md`).
- **VPS CO giup:** (1) demo / forward-test chay lien tuc khi may nha tat, mat dien, cai lai Windows; (2) mot ban SAO LUU NGOAI MAY (bai hoc 02/10: cai lai Windows mat het `nao.db`, `data/`, file bot);
  (3) la "may thu hai" cho `b cau chay` (kenh cau da ho tro: `b cau cai URL NHANH --ten T --kha-nang ...`) - nhung van chi MOT may la [GHI] (tester, `nao.db`).
- **Sao luu ngay bay gio KHONG ton tien:** o HDD 230 GB la o VAT LY RIENG nen song sot khi cai lai Windows tren o C - dua `data/`, `nao.db`, `du_lieu_cao/`, `config/passview.json`, file `.set/.ex5/.mq5` da co vao do (dinh ky), va 1 ban nua ra ngoai may (o USB / kho luu tru rieng tu). KHONG dua vao git (repo PUBLIC).
- **Khi den luc thue:** can Windows VPS (MT5 chay tren Windows), khoang 2-4 vCPU / 4-8 GB RAM, gia xap xi 10-30 USD/thang (CON SO XAP XI, kiem lai luc thue); VPS cua chinh MetaQuotes (khoang 15 USD/thang, kiem lai) chi chay EA, khong chay duoc he thong Python cua ta.
  Dieu kien: chu du an dong y chi phi · tai khoan MT5 DEMO rieng cho VPS · khong dua khoa / mat khau vao repo · ket qua demo van chi tinh la GIA THUYET cho den khi co `DAT`.
