# TIEP TUC MAI — chot 12/09/2026 (toi)

## Trang thai luc tat may

    kho co che      2.741   (dau phien 2.554, +187 tu 684 file chi bao)
    mo coi that     5       (dau phien 26)
    tren duong chay 148     (dau phien 107)
    EVO             22/22 TOT
    o C             8,7 GB trong   (co luc chi con 177 MB)
    nao.db-wal      0 MB    (da gop truoc khi tat - DUNG bo qua buoc nay)
    git             dc4e038

## BON VIEC DAU PHIEN, THEO THU TU

**1. Chay lai pheu `to_hop` — no CHUA XONG.** Lan chay toi 12/09 moi den CHANG 1
(258.020 o) thi bi dung de tat may. Day la lan dau tien pheu chay tren du lieu
DA SUA, nen bang xep hang cu (`reports/TO_HOP.json`) van la bang BAN - 120/120
dong dau deu la EURMXN voi so lieu tu 68 bar hong.

    python -u -m nhan.to_hop --khung D1

Xong thi cham tien: `python -c "...V._cham_tien(print)"` hoac `b vong`.

**2. Xem hai bai test do.** Bo test chot phien chay den 94% thi bi cat. Truoc do
thay 2 chu `F` (o moc 59% va 63%) nhung chua kip biet la bai nao:

    python b.py test

**3. Boc not kho.** Duong LLM da thong (ghim thang AiBox, tran 20.000/ngay) va
684 file chi bao vua ra 93%. Con **97% kho chua boc**: 5.131 file ma nguon,
3.771 tai lieu hoc thuat. Hang doi da nap san:

    python day_viec.py        # xao_ma_llm, xao_hoc_thuat, noi_sinh_da_ma...

**4. Dua quan tri vi the ra tester.** 49/75 khai bao dich duoc sang MQL5 va chen
duoc vao EA ngoai. Buoc con thieu la DO that:

    b quan-tri --cap <EA.mq5> --khai-bao <i>   # sinh cap GOC / CO-QUAN-TRI
    # roi dua CA HAI vao `chay_tester_kho.py` va so ket qua

## CAN NGUOI (30 giay)

`b xa` roi nhan bot Telegram mot cau. `chat_id` van la 0 nen EVO KHONG gui duoc
canh bao nao ra ngoai - khi he cam VPS chay nhieu thang, do la duong duy nhat
de biet co chuyen.

## BA BAY MOI, DA CHAN NHUNG PHAI NHO

1. **Dia day khong hien ra nhu loi dia.** No hien ra nhu "boc 684 file -> 0 co
   che" va "viec XONG rc=0 ma kho khong doi". Thu pham 12/09 la `nao.db-wal`
   1,4 GB. Kiem `b don-dia` + `b evo` TRUOC khi tin bat ky ket qua rong nao.

2. **Bo do ket luan "khong co" phai chung minh no THAY DUOC cai co.** Ban do mu
   ba lan trong mot phien, moi lan deu bao mo coi cho thu dang chay hang ngay.
   Lay ba thu chac chan CO ra thu truoc khi tin mot danh sach rong.

3. **Du lieu hong bom ra ket qua dep.** EURMXN 68 bar lech x10 -> "942%/nam"
   tren mot cap di ngang 9 nam, va no chiem tron 120/120 dong dau bang. Da sua
   (neo truot) va da noi cong `dung_duoc` vao pheu, nhung con so nao qua dep
   thi van phai truy nguoc ve du lieu truoc.

## DUONG DAN DA DOI

`data/` va `data_khung/` gio nam o **F:\TheBrain_luu\**. Doi cho duoc bang bien
`BRAIN_DATA` / `BRAIN_CACHE`, hoac sua `nhan/duong_dan.py`. Neu o F khong gan
duoc thi hai ham do tu roi ve duong cu trong lab.
