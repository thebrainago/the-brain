# TIEP TUC MAI — chot 13/09/2026

Phien nay chu du an doi muc tieu giua chung: *"Muc tieu van chua phai la ra
nhieu co che hay kiem tien ma cai he thong phai tot da."* Nen ca ngay la SUA
HE. Bao cao day du: `../BAO_CAO_2026_09_13.md`.

## DANG CHAY KHI TAT MAY

**Boc 55 video khoa hoc** (`_boc_video_khoa_hoc.py`, 4 tien trinh, ~7,8 gio).
Chu du an giao: *"may khoa hoc do that ra toi da hoc roi nhung cho bro coi nhu
bai tap. Boc va test 14gb du lieu do di. Xong roi xoa."*

    xem tien do:  tail -1 nhat_ky/video_lat{0,1,2,3}.log
    chay tiep:    python _boc_video_khoa_hoc.py        (tu bo qua file da doc)
    dem duoc gi:  python -m nhan.doc_video_cuc_bo --xem

**Xong roi thi con HAI viec nua, dung quen:**
1. `python _xao_toan_kho.py 300 16` — boc co che tu 55 ban doc moi. **Day moi
   la phep thu that**: van xuoi tieng Viet noi -> co che. Chua ai do suat do.
2. Chi khi (1) xong moi **xoa `F:\TeraBoxDownload`** (14,2 GB).

## TRANG THAI LUC TAT MAY

    kho co che      3.033   (dau phien 2.741; da bi xoa 2 lan va khoi phuc du)
    o C trong       31,5 GB (dau phien 8,6 -> co luc 233 MB)
    o F trong       4,6 GB
    ung vien pheu   785 (truoc khi go HTML: 8)
    bo test         ~1.115 xanh / 4 do (dang truy, xem duoi)
    git             0547bd0

## BON VIEC DAU PHIEN, THEO THU TU

**1. Bon bai test DO.** Da biet nam trong me 2/6/7 cua `b test-me`, dang chay
lai de lay ten. Xem `nhat_ky/test_do.log`. **Dung chay `b test` (8 tien trinh)
khi may dang ban** — no chet giua chung 4 lan trong ngay 13/09. Dung:

    b test-me                  chia me, me nao chet thi biet la me nao
    b test-me --nhan 1 --me 8  khi van chet

**2. Quet ban do quan tri rong hon.** `b bench-qt --quet` moi chay 3 ma x 3
engine = 9 luot. Cot `tren deu_dan` (phep thu phan chung) chi co 3 quan sat
nen chua ket luan chac duoc ho nao that su qua.

    python _quet_bench_qt.py US500Cash,US100Cash,EURUSD,GBPUSD,USDJPY,GOLD,GER40Cash
    python _tong_bench_qt.py

**3. `dat_hue` la ung vien quan tri THUAN dang theo** — hon moc ca LAI lan SUT
GIAM o **9/9** luot, va no giu chieu (khac `stop_2_dau`). Nen thu ghep no vao
cac he DA PASS thay vi chi do tren ban do.

**4. Khau tai payload vua sua chua chay het.** `ma_nguon.thu_hoi_sai_loai()` do
duoc 31/40 URL sua duoc; con ~3.500 trang landing chua tai lai.

## BAY MOI, DA CHAN NHUNG PHAI NHO

1. **Mot lan DOC hong co the xoa sach kho.** `doc_kho()` tung nuot loi va tra
   `[]`, roi `luu_kho` lay `cu = 0` nen chot chong teo TAT. Nay `doc_kho` nem
   `KhoDocHong`, chot so voi MOC CAO NHAT, va co ban lui `.json.lui`. Khi thay
   so co che tut bat thuong: **dung ghi tiep bat cu thu gi**, kiem
   `git show HEAD:lab/config/co_che_dsl.json` va `config/co_che_dsl.json.lui`
   truoc. Vet goi cua moi lan ghi lam kho nho di o `nhat_ky/kho_co_che_ghi.log`.

2. **Het dia khong hien ra nhu loi dia.** Ca hai lan mat du lieu hom nay deu
   bat nguon tu o C con 233 MB. Nay co cong `nhan/dia.py` chan o `luu_kho`,
   `boc_llm.boc`, `go_html.go_kho`. Kiem nhanh: `python -m nhan.dia`.

3. **Tien trinh python mo coi tich lai lam may khong sinh duoc tien trinh moi.**
   Do 13/09: 34 tien trinh con sot -> `ENOMEM: uv_spawn`, pytest chet im lang.
   `taskkill /F /IM python.exe` truoc khi chay bo test lon.

4. **Mot ghi chu chua kiem cung la mot cai bay.** `doc_video.py` ghi
   *"faster_whisper can ffmpeg nen hien tai chua bat"* - SAI, no giai ma bang
   PyAV. Mot nang luc co san bi khai la khong co, va khong ai thu lai suot mot
   thang. Luat *"lay ba thu chac chan CO ra thu"* phai ap cho ca NANG LUC.

5. **Bai test khong duoc sua du lieu san xuat.** `test_chan_hang_so` tung
   doc-sua-ghi kho THAT. Nay co cong o `conftest.py` (theo tung bai khi mot
   nhan, theo ca phien duoi xdist).

## CONG CU MOI

    b go-html [N]     go trang HTML tho -> van ban  (khau TRUOC `b boc`)
    b bench-qt [MA]   ban do 11 ho quan tri vi the; `--quet` da tai san
    b test-me         chay bo test theo me (ben khi may nghet)
    python -m nhan.dia                 con bao nhieu GB truoc nguong chan ghi
    python -m nhan.doc_video_cuc_bo --xem   video tren dia da doc bao nhieu
    python _tong_bench_qt.py           tong hop ban do quan tri

## DIA — con can nguoi

    F:\Zalo Data          60,3 GB   don trong chinh Zalo, thuong lay lai 40-50
    F:\Riot Games         44,1 GB   game
    F:\Chuyen_tu_C\Apple_iTunes  5,7 GB  da chuyen tu C sang, xoa duoc neu khong can
