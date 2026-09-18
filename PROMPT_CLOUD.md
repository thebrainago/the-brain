# PROMPT CHO PHIEN CLOUD (Claude Code tren web)

> Copy tu dong `---` den het, dan vao khung "Describe a task" o claude.ai/code
> sau khi da chon repo `thebrainago/the-brain`.

---

Ban dang lam viec tren THE BRAIN — phong nghien cuu tu dong cho giao dich.

## Doc truoc khi go phim

1. `README.md` — he nay la gi, cai gi khong chay duoc tren cloud
2. `SO_DO_HE_THONG.txt` — so do goc cua chu du an (LUAT SO 0)
3. `CLAUDE.md` — luat lam viec va cac bay da dinh
4. `HO_SO_HE_THONG.md` — trang thai he, so lieu do ngay 18/09

## Rang buoc CUNG — doc ky, day khong phai loi khuyen

Repo nay KHONG co: `nao.db` (kho tri thuc 1,6 GB), MT5 terminal, du lieu gia,
ho so trinh duyet cua Seeker. 106/138 module trong `nhan/` va `tru/` can it
nhat mot trong so do, tuc **77% he khong chay duoc o day**.

Nghia la:
- **Dung chay** `b ban-do`, `b ho-so`, bat cu thu gi doc `nao.db` hay MT5.
- **Dung ket luan** mot co che "chay duoc" / "co lai" / "nen dung". Tren may
  chu du an, 1.284 ket qua da do chi giu lai duoc 60 khang dinh. Con so duy
  nhat dang tin la con so ra tu MT5 tester, va cho do khong o day.
- **Dung sinh them co che moi.** Kho dang don 705 ung vien chua do xong, ung
  vien moi nhat tu 01/09. Sinh them chi lam hang doi dai ra.

## VIEC CUA PHIEN NAY

Nut that that cua he: kho co **12.078 tai lieu** nhung chi boc ra duoc
**285 co che (2,4%)**. Bo doc ma nguon dang de rot phan lon.

Do bang mot lenh (chay duoc o cloud, khong can gi ngoai repo):

    python mau_thu/do_moc.py

Moc ngay 18/09/2026 tren 10 file `.mq5` mau trong `mau_thu/`:

    tim THAY diem vao lenh : 22
    RA duoc co che         : 0        <- con so phai nang

**Chan doan da co san, dung di tim lai:** bo doc THAY ca 22 diem vao lenh,
nhung dieu kien vao lenh nam trong BIEN TRUNG GIAN — vi du `downbreakout`,
`Tradesinfo.initup && current[0].close >= Tradesinfo.hedgeprice` — con
`nhan/ngu_phap.py` chi dien dat duoc bieu thuc truc tiep tren gia/chi bao.
Khong truy nguoc duoc bien ve bieu thuc goc thi khai bao roi het vao muc
`chua_dien_dat_duoc`.

**Viec:** nang so co che boc ra tu 0 len cang cao cang tot, bang cach cho
`nhan/doc_ma.py` truy nguoc duoc bien trung gian ve bieu thuc goc truoc khi
giao cho `nhan/ngu_phap.py`.

## Lam the nao cho khong hong thu dang chay

- Viet test TRUOC khi sua, theo dung kieu cac test dang co.
- Tang test phai xanh sau moi buoc:

      python -m pytest test_doc_ma.py test_ngu_phap_toan_hang.py \
                       test_ngu_phap_trung.py test_boc_va_doc.py -q

- `test_hien_phap.py` bat moi module trong `nhan/` va `tru/` phai co file test
  nhac den no. Them module moi ma quen test la bo test keu ngay.
- Bam sat giong van dang co: tieng Viet khong dau, docstring noi RO VI SAO chu
  khong chi noi lam gi.

## Bao cao lai

Commit theo tung buoc nho, moi commit mot y. Cuoi phien ghi vao
`BAO_CAO_CLOUD_<ngay>.md` o goc repo:

- so do duoc TRUOC va SAU (`python mau_thu/do_moc.py`)
- cai gi da sua, vi sao
- cai gi THU MA KHONG AN — phan nay quan trong khong kem phan thanh cong
- cai gi con lai chua lam duoc va vuong o dau

Neu ban ket luan khong nang duoc con so nay, hay noi thang va noi ro vi sao.
Mot ket luan am CO BANG CHUNG co gia tri hon mot cai sua vu vo.

---
