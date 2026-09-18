# -*- coding: utf-8 -*-
"""Ghi ket qua TANG SANG (09/08/2026) vao so khang dinh.

Day la buoc dong vong: 7 khang dinh CHUA_TEST tu 08/08 gio co so lieu. Ghi vao so
de lan sau tra 1 phut thay vi chay lai 1 ngay.

LUU Y VE MUC DO CHAC CHAN: day la ket qua TAP SANG (28 thi truong ngoai tap xac
nhan), tang 1, khong cong nao, khong ton slot FDR. "DA_DONG_SO" o day nghia la
"khong dang mang len tang xac nhan", KHONG phai "da chung minh la sai".
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brain_khang_dinh as bkd

NGAY = "2026-08-09"

# ma -> (trang_thai moi, ket qua)
KQ = {
    "KD_LUAN_PHIEN": ("DANG_SANG",
        "Sang 09/08: 6/7 nhom cung dau, z trung vi +0,83, p(dau theo nhom)=0,125. "
        "UNG HO luan phien nhung RAT YEU. Quan trong: do tho bang log(do doc) cho "
        "28/28 thi truong BAC BO Elliott - do la bien dong cum lai gia dang. Chia cho "
        "bien do duong nhien (ATR% x sqrt(thoi luong)) thi lat dau. Nong san (ngo, "
        "dautuong) nguoc han phan con lai (+0,38/+0,41 = KHONG luan phien)."),

    "KD_CHAN_GIUA_DAI_NHAT": ("DANG_SANG",
        "Sang 09/08: 7/7 nhom cung dau, p(dau theo nhom)=0,0156 - NHAT QUAN NHAT trong "
        "7 khang dinh. Nhung do lon ti hon: P(chan giua ngan nhat) lech khoang 1 diem "
        "phan tram so voi 1/3. Dung hieu la 'song 3 khong ngan nhat' dung theo huong "
        "nhung khong du bien de an chi phi. Muon giao dich phai co don bay thong tin "
        "khac di kem."),

    "KD_BAT_DOI_XUNG_5_3": ("CHUA_TEST",
        "Sang 09/08: KHONG DO DUOC o khung NGAY. Voi zigzag nguong 3xATR, so lan chuoi "
        "dat toi chan thu 5 duoi 15 lan o hau het thi truong -> duoi nguong mau toi "
        "thieu. Muon do phai ha nguong zigzag hoac xuong khung nho hon. Day la thieu "
        "DO PHAN GIAI, khong phai ket qua am tinh."),

    "KD_DON_CUM_LENH_DUNG": ("DA_DONG_SO",
        "Sang 09/08, do HAI LAN doc lap, cung ket luan: khong co hieu ung chung. "
        "(1) Ban cua Claude: 2/7 nhom, z trung vi +0,30, p=0,453. "
        "(2) Ban cua DeepSeek do TUONG TAC voi 4 che do (vol cao/thap, tren/duoi SMA200, "
        "xa/gan SMA200, bar quet rong/hep), phat da phep thu bang cach lay max|chenh| roi "
        "hoan vi nhan tung bien: 4/7 nhom, z trung vi +0,25, p=1,00. "
        "Tuc gia thuyet 'A khi B' cung KHONG cuu duoc no - DAX z=+2,6 chi la mot thi "
        "truong le, khong co cau chuyen che do nao dang sau. Luu y doc so: ban DeepSeek "
        "co nhin truoc (vao lenh tai close cua chinh bar tin hieu), ma nhin truoc thi "
        "THOI PHONG hieu ung - da thoi phong ma van khong thay gi thi ket luan am tinh "
        "cang chac."),

    "KD_LAP_KHOANG_TRONG": ("DA_DONG_SO",
        "Sang 09/08: BAC BO. Doi chung chi khop khoang cach cho z trung vi +1,89 (6/7 "
        "nhom) - trong nhu co suc hut that. Khop them CHE DO BIEN DONG (chia 5 tang ATR%, "
        "boc doi chung trong cung tang) thi sap con z trung vi -0,39, 4/7 nhom, p=1,00. "
        "Ty le lap 0,705 so voi 0,721 cua muc gia ngau nhien cung khoang cach cung tang "
        "vol - tuc THAP HON ngau nhien. Co che that: khoang trong chi sinh ra trong "
        "phien bien dong manh, ma phien bien dong manh thi gia quay lai bat ky muc nao "
        "cung de. Fair value gap khong co suc hut; cai nhin thay la volatility. "
        "(Kiem chung: ban vector hoa va ban vong lap cho ket qua trung khop tuyet doi.)"),

    "KD_KL_PHAN_KY_BIEN": ("DANG_SANG",
        "Sang 09/08: 5/6 nhom cung dau, z trung vi +0,37, p=0,219. Chi do duoc tren 11 "
        "thi truong co khoi luong that (Yahoo tra volume=0 cho chi so tong hop va FX). "
        "Huong dung voi Wyckoff/VSA nhung khong dat nguong, va mau it."),

    "KD_DOI_XUNG_THOI_GIAN": ("DA_DONG_SO",
        "Sang 09/08: 9/28 thi truong, chi 2/7 nhom, z trung vi -0,91, p=0,453. Khoang "
        "cach giua cac chan KHONG du bao duoc nhau - neu co gi thi nguoc dau (khoang "
        "dai theo sau khoang ngan). He so bien thien cua khoang cach quanh 0,6-0,8, "
        "dung nhu buoc di ngau nhien. Chu ky thoi gian kieu Gann: dong so o tang sang."),
}

# Khang dinh moi rut ra tu chinh phien nay - ap cho MOI phuong phap dem song
MOI = dict(
    ma="KD_DEM_SONG_VE_LAI",
    phat_bieu="Nhan song/cau truc gan bang zigzag thong thuong bi VE LAI tren phan lon bar",
    do_bang="cong repaint tong quat: ty le BAR tung bi doi nhan khi co du lieu moi",
    bac_bo_duoc_bang="neu ty le duoi 10% thi nhan la giao dich duoc",
    nhom="thong ke / hoc may",
    trang_thai="DA_DONG_SO",
    phuong_phap_dung_no="Elliott | ICT/SMC market structure | Wyckoff phase | ZigZag | Harmonic",
    ket_qua=("Sang 09/08: 28/28 thi truong, ty le bar bi ve lai TRUNG VI 93,9%. Ban "
             "nhan qua (chi cong bo nhan sau khi chan duoc xac nhan) ra 0,0%. Nghia la "
             "moi backtest dem song dung nhan kieu thuong deu la hu cau: luc backtest "
             "thay nhan CUOI CUNG, luc giao dich chi thay nhan TAM THOI. Cua nay mot "
             "minh dong ca chum phuong phap, va no re nhat trong tat ca cac cong."),
    ngay_cap_nhat=NGAY,
)


def main():
    so = bkd.doc_so()
    for ma, (tt, kq) in KQ.items():
        m = so["ma"] == ma
        if not m.any():
            print(f"  ! khong thay {ma} trong so")
            continue
        so.loc[m, "trang_thai"] = tt
        so.loc[m, "ket_qua"] = kq
        so.loc[m, "ngay_cap_nhat"] = NGAY
        print(f"  {ma:<26} -> {tt}")

    if not (so["ma"] == MOI["ma"]).any():
        import pandas as pd
        so = pd.concat([so, pd.DataFrame([MOI])], ignore_index=True)
        print(f"  + them khang dinh moi: {MOI['ma']}")

    bkd.ghi_so(so)
    bkd.bao_cao()


if __name__ == "__main__":
    main()
