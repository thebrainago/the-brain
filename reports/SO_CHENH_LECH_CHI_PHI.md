# SO CHENH LECH CHI PHI TRIEN KHAI
*Do luc 2026-09-14 19:01:22 tren cac terminal MT5 dang cai.*

> **Day khong phai gia thuyet, day la phep tru.** Khong ton slot ngan sach
> thong ke nao. Khong can backtest, khong can placebo.

> **Cach doc:** so la phi giu vi the MUA, %/nam. Duong = ta TRA. Am = ta DUOC
> nhan (carry duong). Cot da neo vao GIA HIEN TAI - voi san thu swap bang so
> TUYET DOI, ty le nay GIAM khi gia tang, nen **dung ap cho ca lich su**
> (CLAUDE.md muc 13-14).

## Chenh lech dang ke (20 phoi nhiem >= 1 diem %/nam, do tin CAO)

| Phoi nhiem | Kenh re | %/nam | Kenh dat | %/nam | CHENH | Dieu kien de sai |
|---|---|---|---|---|---|---|
| `USDZAR` | FXCE | +0.00 | XM | +9.29 | **+9.29** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `XAGUSD` | FXCE | +3.00 | XM | +11.23 | **+8.23** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `USDMXN` | FXCE | +0.00 | XM | +7.18 | **+7.18** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `USDHUF` | FXCE | +0.00 | XM | +5.54 | **+5.54** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `ADP` | FXCE | +3.00 | XM | +7.18 | **+4.18** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `ING` | FXCE | +3.00 | XM | +7.18 | **+4.18** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `USDNOK` | FXCE | +0.00 | XM | +3.33 | **+3.33** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `USDPLN` | FXCE | +0.00 | XM | +2.87 | **+2.87** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `XAUUSD` | FXCE | +4.48 | XM | +7.12 | **+2.64** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `EURJPY` | FXCE | -0.86 | XM | +1.27 | **+2.13** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `CHFJPY` | FXCE | +1.27 | XM | +3.16 | **+1.89** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `AUDJPY` | FXCE | -3.22 | XM | -1.34 | **+1.88** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `GBPJPY` | FXCE | -2.26 | XM | -0.54 | **+1.72** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `USDJPY` | FXCE | -2.20 | XM | -0.50 | **+1.70** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `NZDJPY` | FXCE | -1.04 | XM | +0.62 | **+1.66** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `EURNZD` | FXCE | +0.96 | XM | +2.56 | **+1.60** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `USDHKD` | FXCE | +0.00 | XM | +1.41 | **+1.41** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `CADJPY` | FXCE | -1.00 | XM | +0.36 | **+1.36** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `AUDNZD` | FXCE | -1.27 | XM | +0.08 | **+1.35** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |
| `USDDKK` | FXCE | +0.00 | XM | +1.13 | **+1.13** | FXCE doi bieu phi; rui ro doi tac cua FXCE tang; hai symbol  |

## Canh bao doc so

- `MetaQuotes-Demo` **khong** nam trong bang: do la may chu demo cua chinh
  MetaQuotes, khong mo tai khoan that duoc. De no vao la tu lua - no luon re
  nhat vi khong ai phai kiem tien tren do.
- Chi lay dong `tin_cay=CAO` (swap_mode = POINTS hoac LAI SUAT). Cac mode
  tinh bang TIEN phai quy doi qua contract size + dong tien tai khoan nen
  con sai so; mode 9 (khong co trong tai lieu MT5) lai cang khong chac.
- Hai symbol cung ten chuan hoa **chua chac cung phoi nhiem**: phai doi chieu
  contract size va gio giao dich truoc khi chuyen tien that.

## Buoc tiep de bien thanh tien

1. Xac minh bang **sao ke tai khoan that** (mo mot lenh nho, giu qua dem,
   doc dung so tien bi tru) - so tu `symbol_info` la bang gia niem yet,
   khong phai bang chung.
2. Kiem rui ro doi tac + dieu kien rut tien cua
   kenh re truoc khi chuyen.
3. Dat lai lich do dinh ky: bieu phi doi thi
   ket luan doi.