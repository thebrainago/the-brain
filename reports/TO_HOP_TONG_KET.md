# TONG KET TO HOP

*2 o chang 2 / 1 ma / khung D1 / 1 giay*

Xep hang bang `cagr_dd20`: lai %/nam khi quy ca hai ve cung ngan sach
sut giam 20%. `hon_moc` = thang **max(mua-giu, ban-giu, tien mat)**.

## DOC BANG NAY NHU THE NAO

Chang 1 da CHON top 200 o theo chinh `cagr_dd20`, roi chang 2 mo rong
dung nhung o do. Nen con so `hon_moc` o day **bi thoi len boi chinh phep
chon** - no khong phai ti le thanh cong cua mot lan quet mu.

Cai bang nay tra loi duoc, va chi tra loi duoc, mot cau: *voi nhung o da
co ve co gi, thi doi CAU TRUC hay doi LUAT lam ket qua thay doi ra sao*.
Do la dung cau hoi chu du an dat ra cho module quan li lenh. Muon biet
ti le thanh cong THAT thi phai doc chang 1 (chua chon), hoac chay lai
tren holdout.

## Theo KHUNG

| khung | o | dd20 trung vi | tot nhat | ti le duong | hon moc |
|---|---:|---:|---:|---:|---:|
| D1 | 1 | -1.000 | -1.000 | 0% | 0 |
| H4 | 1 | -2.000 | -2.000 | 0% | 0 |

**NEN DI**: D1 (trung vi -1.000, 0/1 o duong)

**NEN TRANH**: H4 (trung vi -2.000, chi 0/1 o duong)

## Theo CAU TRUC VAO LENH

| cau truc vao lenh | o | dd20 trung vi | tot nhat | ti le duong | hon moc |
|---|---:|---:|---:|---:|---:|
| thi_truong | 1 | -1.000 | -1.000 | 0% | 0 |
| tt_hedge | 1 | -2.000 | -2.000 | 0% | 0 |

**NEN DI**: thi_truong (trung vi -1.000, 0/1 o duong)

**NEN TRANH**: tt_hedge (trung vi -2.000, chi 0/1 o duong)

## Cai duy nhat dang theo tiep

0/2 o thang duoc moc. 

**Khong o nao thang moc.** Do la mot ket qua, khong phai mot
loi: no noi rang tren khong gian nay, giu tai san con hon giao dich no.
