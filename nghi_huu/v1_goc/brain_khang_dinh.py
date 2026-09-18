# -*- coding: utf-8 -*-
"""
brain_khang_dinh.py - SO KHANG DINH + CONG REPAINT TONG QUAT
=====================================================================================
Doc `PROMPT_DEEPSEEK_TU_DUY.md` truoc. File nay la ban cai dat cua no.

NGUYEN LY: so bien the cua mot phuong phap la con so VO NGHIA. So KHANG DINH NGUYEN TU
moi la thu phai tra tien. Elliott ~1.000 bien the nhung chi ~6 khang dinh. Harmonic ~50
bien the nhung 1 khang dinh - VA NO TRUNG VOI ELLIOTT. Test 1 lan, biet ca hai.

Da do tren chinh du an: 40 phep thu -> nguong t~2,73; 306 phep thu -> t~3,48.
Moi gia thuyet nap them lam KHO HON cho tat ca nhung cai da co.

SO NAY LA TAI SAN TICH LUY LON NHAT. Sau vai thang, danh gia mot phuong phap moi
chuyen tu "vai ngay backtest" thanh "vai phut tra cuu".

CLI:
  python brain_khang_dinh.py gieo              # gieo cac khang dinh da rut san
  python brain_khang_dinh.py tra "fib"         # tra so truoc khi test bat cu thu gi
  python brain_khang_dinh.py nap <file.json>   # nap ho so phuong phap moi
  python brain_khang_dinh.py bao-cao
  python brain_khang_dinh.py demo-repaint      # chay thu cong repaint
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
REPORTS.mkdir(exist_ok=True)
SO = REPORTS / "BRAIN_khang_dinh.parquet"
RA_MD = REPORTS / "BRAIN_KHANG_DINH.md"

# 9 nhom co che - dung y het brain_nap_kho.py de tra cheo duoc
NHOM_HOP_LE = {
    "bien dong / phong ho", "dao chieu / qua ban", "xu huong / momentum",
    "khoi luong / dong tien", "moc gia / cau truc", "mua vu / lich",
    "vi cau truc / thanh khoan", "quan tri von / lenh", "thong ke / hoc may",
}
# Hai nhom du an da dot 35.932 + 12,17 trieu to hop -> 0 song sot
DA_DONG_SO = {"xu huong / momentum", "moc gia / cau truc"}


# ---------------------------------------------------------------------------
# CONG REPAINT TONG QUAT - phan dung duoc cho MOI phuong phap
# ---------------------------------------------------------------------------

def cong_repaint(df, ham_gan_nhan, buoc=1, toi_da_bar=None, nguong=0.10):
    """Do ty le nhan bi VE LAI. Day la cong re nhat va giet nhieu phuong phap nhat.

    Y tuong: mot phuong phap chi giao dich duoc neu nhan cua bar qua khu KHONG DOI khi
    co them du lieu moi. Neu no doi (dem lai song, ve lai vung, "xac nhan sau") thi
    moi backtest cua no la hu cau - vi luc backtest ban thay nhan CUOI CUNG, con luc
    giao dich that ban chi thay nhan TAM THOI.

    Tham so
    -------
    df            : DataFrame OHLC day du
    ham_gan_nhan  : f(df_cat) -> array/Series cung do dai df_cat.
                    Tra ve nhan cho TUNG bar (vd: -1/0/+1, hoac so hieu song).
                    KHONG duoc dung du lieu ngoai df_cat.
    buoc          : moi lan tien bao nhieu bar (1 = nghiem ngat nhat, cham nhat)
    toi_da_bar    : chi kiem `toi_da_bar` bar cuoi cho nhanh (None = het)
    nguong        : ty le doi nhan bi coi la repaint

    Tra ve dict: ty_le_nhan_doi, so_bar_kiem, so_lan_doi, ket_luan
    """
    n = len(df)
    bat_dau = max(50, n - toi_da_bar) if toi_da_bar else 50
    if bat_dau >= n:
        return {"loi": "khong du bar"}

    nhan_dau_tien = {}     # vi tri bar -> nhan LAN DAU duoc gan (cai ban THAY LUC DO)
    bar_da_doi = set()     # bar nao TUNG bi ve lai - day moi la thu can dem
    so_lan_doi = 0
    so_lan_kiem = 0

    for cuoi in range(bat_dau, n + 1, buoc):
        cat = df.iloc[:cuoi]
        try:
            nhan = np.asarray(ham_gan_nhan(cat))
        except Exception as e:
            return {"loi": f"ham_gan_nhan hong o bar {cuoi}: {str(e)[:80]}"}
        if len(nhan) != len(cat):
            return {"loi": f"ham_gan_nhan tra ve {len(nhan)} nhan cho {len(cat)} bar"}

        # chi kiem cac bar da tung duoc gan nhan truoc do
        for i in range(len(cat)):
            if i in nhan_dau_tien:
                so_lan_kiem += 1
                cu, moi = nhan_dau_tien[i], nhan[i]
                # so sanh chiu duoc NaN
                doi = not ((cu != cu and moi != moi) or cu == moi)
                if doi:
                    so_lan_doi += 1
                    bar_da_doi.add(i)
                    nhan_dau_tien[i] = moi
            else:
                nhan_dau_tien[i] = nhan[i]

    # Ty le DUNG = bao nhieu phan tram BAR tung bi ve lai.
    # KHONG phai so_lan_doi/so_lan_kiem - cach do pha loang ghe gom vi da so bar on dinh
    # o da so lan chup, nen mot phuong phap repaint nang van ra ty le be xiu. Da mac loi
    # nay khi viet lan dau: zigzag ve lai ca doan ma chi ra 1,21%.
    # Cau hoi dung la: trong so nhan toi THAY LUC GIAO DICH THAT, bao nhieu cai sau do sai?
    ty_le = len(bar_da_doi) / len(nhan_dau_tien) if nhan_dau_tien else 0.0
    return {
        "ty_le_nhan_doi": round(float(ty_le), 4),
        "so_bar_kiem": len(nhan_dau_tien),
        "so_bar_bi_ve_lai": len(bar_da_doi),
        "so_lan_doi": so_lan_doi,
        "nguong": nguong,
        "ket_luan": "REPAINT - DUNG LAI" if ty_le > nguong else "khong repaint - di tiep",
    }


# ---------------------------------------------------------------------------
# SO KHANG DINH
# ---------------------------------------------------------------------------

COT = ["ma", "phat_bieu", "do_bang", "bac_bo_duoc_bang", "nhom", "trang_thai",
       "phuong_phap_dung_no", "ket_qua", "ngay_cap_nhat"]


def doc_so():
    if SO.exists():
        try:
            return pd.read_parquet(SO)
        except Exception:
            pass
    return pd.DataFrame(columns=COT)


def ghi_so(df):
    tam = Path(str(SO) + ".tam")
    df.to_parquet(tam, index=False)
    import os
    os.replace(tam, SO)


def them_khang_dinh(kd):
    """Them 1 khang dinh. Neu ma da co -> chi gop them ten phuong phap, KHONG tao dong moi.
    Do chinh la co che khu trung lap giup tiet kiem ngan sach FDR."""
    so = doc_so()
    ma = kd["ma"]
    if len(so) and (so["ma"] == ma).any():
        i = so.index[so["ma"] == ma][0]
        cu = set(str(so.at[i, "phuong_phap_dung_no"]).split(" | ")) - {"", "nan"}
        moi = cu | set(kd.get("phuong_phap_dung_no", "").split(" | ")) - {""}
        so.at[i, "phuong_phap_dung_no"] = " | ".join(sorted(moi))
        so.at[i, "ngay_cap_nhat"] = datetime.now().date().isoformat()
        ghi_so(so)
        return "gop", so.at[i, "trang_thai"]
    kd = {**{c: "" for c in COT}, **kd, "ngay_cap_nhat": datetime.now().date().isoformat()}
    ghi_so(pd.concat([so, pd.DataFrame([kd])], ignore_index=True))
    return "moi", kd.get("trang_thai", "CHUA_TEST")


def tra(tu_khoa):
    """TRA SO TRUOC KHI TEST BAT CU THU GI. Day la buoc tiet kiem tien nhat ca he thong."""
    so = doc_so()
    if so.empty:
        print("  so rong - chay `python brain_khang_dinh.py gieo` truoc")
        return so
    tk = tu_khoa.lower()
    m = so.apply(lambda r: tk in " ".join(str(v).lower() for v in r.values), axis=1)
    kq = so[m]
    if kq.empty:
        print(f"  khong thay '{tu_khoa}' trong so -> co the la khang dinh MOI")
        return kq
    print(f"  thay {len(kq)} khang dinh khop '{tu_khoa}':\n")
    for _, r in kq.iterrows():
        print(f"  [{r['trang_thai']:12}] {r['ma']}")
        print(f"     {r['phat_bieu']}")
        print(f"     nhom: {r['nhom']}")
        print(f"     dung boi: {r['phuong_phap_dung_no']}")
        if str(r["ket_qua"]).strip():
            print(f"     KET QUA: {r['ket_qua']}")
        print()
    return kq


def nap_ho_so(duong_dan):
    """Nap ho so phuong phap moi (JSON theo mau trong PROMPT_DEEPSEEK_TU_DUY.md).
    In ra con so DUY NHAT dang quan tam: bao nhieu khang dinh THAT SU moi."""
    hs = json.loads(Path(duong_dan).read_text(encoding="utf-8"))
    ten = hs.get("phuong_phap", "?")
    print(f"\n=== NAP: {ten} ===")
    print(f"  bien the uoc tinh: {hs.get('so_bien_the_uoc_tinh', '?')}")

    moi = 0
    for kd in hs.get("khang_dinh", []):
        kd = dict(kd)
        kd["phuong_phap_dung_no"] = ten
        if kd.get("nhom") in DA_DONG_SO and not kd.get("trang_thai"):
            kd["trang_thai"] = "DA_DONG_SO"
            kd["ket_qua"] = "nhom da dong so: 35.932 + 12,17 trieu to hop -> 0 song sot"
        trang, tt = them_khang_dinh(kd)
        dau = "MOI " if trang == "moi" else "trung"
        if trang == "moi" and tt == "CHUA_TEST":
            moi += 1
        print(f"  [{dau}] {kd['ma']:22} {tt:12} {kd.get('phat_bieu','')[:60]}")

    print(f"\n  >>> KHANG DINH THAT SU MOI: {moi}")
    if moi == 0:
        print("      Ton 0 slot ngan sach. Day la THANH CONG, khong phai that bai.")
        print("      Tra so ra cau tra loi ma khong phai chay backtest nao.")
    else:
        print(f"      Se ton {moi} slot NEU duoc nguoi ky. Ban chi lap ho so, khong duoc ky.")
    return moi


# ---------------------------------------------------------------------------
# GIEO: cac khang dinh da rut san tu 6 phuong phap (xem bang trong PROMPT)
# ---------------------------------------------------------------------------

GIEO = [
    # --- moc gia: DA DONG SO. Bay phuong phap, hai khang dinh. ---
    dict(ma="KD_FIB_HUT", nhom="moc gia / cau truc", trang_thai="DA_DONG_SO",
         phat_bieu="Sau chan song lon, gia dao chieu gan muc thoai lui Fib nhieu hon ngau nhien",
         do_bang="mat do phan bo do sau thoai lui vs null giu nguyen bien dong",
         bac_bo_duoc_bang="mat do tai 0.618 khong khac phan con lai",
         phuong_phap_dung_no="Elliott Wave | Harmonic | Fibonacci retracement",
         ket_qua="nhom da dong so: 12,17 trieu to hop moc gia -> 0 song sot"),
    dict(ma="KD_GIA_CO_TRI_NHO", nhom="moc gia / cau truc", trang_thai="DA_DONG_SO",
         phat_bieu="Muc gia da giao dich nhieu trong qua khu co suc hut/day khi gia quay lai",
         do_bang="loi suat K bar sau khi cham lai muc, so voi muc ngau nhien cung khoang cach",
         bac_bo_duoc_bang="loi suat khong khac muc ngau nhien",
         phuong_phap_dung_no="Order Block (ICT/SMC) | Ho tro-Khang cu | Supply-Demand | Volume Profile POC",
         ket_qua="magnetic_master: 90/169 moc la bien the trung lap, xep hang chi la cuc tri ngau nhien"),
    dict(ma="KD_FIB_MO_RONG", nhom="moc gia / cau truc", trang_thai="DA_DONG_SO",
         phat_bieu="Chan song ke tiep ket thuc gan muc mo rong Fib 1.618 hon ngau nhien",
         do_bang="mat do diem ket thuc chan vs null",
         bac_bo_duoc_bang="khong co cum tai 1.618",
         phuong_phap_dung_no="Elliott Wave | Harmonic"),

    # --- QUAN HE giua cac chan: CHUA AI CHAM. Day la khe ho that. ---
    dict(ma="KD_LUAN_PHIEN", nhom="thong ke / hoc may", trang_thai="CHUA_TEST",
         phat_bieu="Hai dot dieu chinh lien tiep co hinh dang doi lap (nhon <-> phang)",
         do_bang="tuong quan giua chi so 'do nhon' cua hai dot dieu chinh ke nhau",
         bac_bo_duoc_bang="tuong quan ~ 0",
         phuong_phap_dung_no="Elliott Wave"),
    dict(ma="KD_CHAN_GIUA_DAI_NHAT", nhom="thong ke / hoc may", trang_thai="CHUA_TEST",
         phat_bieu="Trong 3 chan cung chieu lien tiep, chan giua co phan phoi do dai khac hai chan kia",
         do_bang="so sanh phan phoi do dai chan 1/2/3, kiem dinh khong tham so",
         bac_bo_duoc_bang="ba phan phoi khong khac nhau",
         phuong_phap_dung_no="Elliott Wave"),
    dict(ma="KD_BAT_DOI_XUNG_5_3", nhom="thong ke / hoc may", trang_thai="CHUA_TEST",
         phat_bieu="Chuoi 5 chan co tinh chat thong ke khac chuoi 3 chan (bien dong, thoi luong, di tiep)",
         do_bang="phan loai chuoi roi so sanh loi suat K bar sau khi chuoi ket thuc",
         bac_bo_duoc_bang="hai loai chuoi cho phan phoi giong nhau",
         phuong_phap_dung_no="Elliott Wave"),

    # --- thanh khoan / vi cau truc: co CO CHE that, dang uu tien ---
    dict(ma="KD_DON_CUM_LENH_DUNG", nhom="vi cau truc / thanh khoan", trang_thai="CHUA_TEST",
         phat_bieu="Lenh dung don cum ngay tren dinh/duoi day ro rang, gia quet qua roi dao chieu",
         do_bang="ty le 'pha bien roi dong cua nguoc lai trong K bar' vs bien ngau nhien",
         bac_bo_duoc_bang="ty le khong khac bien ngau nhien",
         phuong_phap_dung_no="ICT/SMC quet thanh khoan | Wyckoff spring | stop hunt"),
    dict(ma="KD_LAP_KHOANG_TRONG", nhom="vi cau truc / thanh khoan", trang_thai="CHUA_TEST",
         phat_bieu="Gia quay lai lap khoang trong (fair value gap) voi xac suat cao hon ngau nhien",
         do_bang="ty le lap trong K bar vs null",
         bac_bo_duoc_bang="ty le lap = ty le cham muc ngau nhien cung khoang cach",
         phuong_phap_dung_no="ICT/SMC fair value gap | gap fill"),

    # --- khoi luong ---
    dict(ma="KD_KL_PHAN_KY_BIEN", nhom="khoi luong / dong tien", trang_thai="CHUA_TEST",
         phat_bieu="Khoi luong giam dan khi gia cham bien vung bao hieu dao chieu",
         do_bang="loi suat sau khi cham bien, chia theo xu huong khoi luong",
         bac_bo_duoc_bang="hai nhom khoi luong cho loi suat nhu nhau",
         phuong_phap_dung_no="Wyckoff | Volume Spread Analysis",
         ket_qua="LUU Y: CFD co volume=0, chi lam duoc tren futures/co phieu that"),

    # --- thoi gian ---
    dict(ma="KD_DOI_XUNG_THOI_GIAN", nhom="mua vu / lich", trang_thai="CHUA_TEST",
         phat_bieu="Khoang thoi gian giua cac diem xoay co cau truc lap lai (khong ngau nhien)",
         do_bang="pho Fourier / kiem dinh chu ky tren chuoi khoang cach diem xoay",
         bac_bo_duoc_bang="pho phang, khong dinh troi",
         phuong_phap_dung_no="Gann | chu ky thoi gian"),
]


def gieo():
    print("=== GIEO SO KHANG DINH ===\n")
    moi = trung = 0
    for kd in GIEO:
        trang, _ = them_khang_dinh(kd)
        moi += trang == "moi"
        trung += trang == "gop"
    so = doc_so()
    print(f"  {moi} moi, {trung} gop vao dong da co")
    print(f"  tong: {len(so)} khang dinh\n")
    n_pp = len({p for r in so["phuong_phap_dung_no"] for p in str(r).split(" | ") if p})
    print(f"  >>> {n_pp} phuong phap rut ve {len(so)} khang dinh")
    print(f"  >>> trong do {int((so['trang_thai']=='DA_DONG_SO').sum())} da co cau tra loi, "
          f"{int((so['trang_thai']=='CHUA_TEST').sum())} that su can test")
    bao_cao()


def bao_cao():
    so = doc_so()
    if so.empty:
        return
    md = ["# THE BRAIN - so khang dinh", "",
          f"*Cap nhat {datetime.now():%Y-%m-%d %H:%M}. {len(so)} khang dinh.*", "",
          "> **Tra so nay TRUOC khi test bat cu phuong phap nao.** So bien the la con so vo nghia;",
          "> so khang dinh nguyen tu moi la thu phai tra tien. Nhieu phuong phap khac ten rut ve",
          "> cung mot khang dinh - test 1 lan la biet ca chum.", ""]
    for tt in ("CHUA_TEST", "DANG_SANG", "DA_DONG_SO", "DA_KY"):
        nhom = so[so["trang_thai"] == tt]
        if nhom.empty:
            continue
        md += [f"## {tt} ({len(nhom)})", "",
               "| ma | phat bieu | nhom | phuong phap dung no |", "|---|---|---|---|"]
        for _, r in nhom.iterrows():
            md.append(f"| `{r['ma']}` | {r['phat_bieu']} | {r['nhom']} | {r['phuong_phap_dung_no']} |")
        md.append("")
    RA_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"  -> {RA_MD}")


# ---------------------------------------------------------------------------
# DEMO cong repaint: hai ham gan nhan, mot cai sach mot cai repaint
# ---------------------------------------------------------------------------

def demo_repaint():
    rng = np.random.default_rng(7)
    n = 600
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    df = pd.DataFrame({"open": gia, "high": gia * 1.003, "low": gia * 0.997, "close": gia})

    def nhan_sach(d):
        """SACH: chi dung du lieu den bar hien tai, khong bao gio nhin lai."""
        return np.sign(d["close"].diff(20).fillna(0).to_numpy())

    def nhan_repaint(d):
        """REPAINT: zigzag dinh lai diem xoay moi khi co dinh/day moi - dung nhu
        cach Elliott 'dem lai song'. Nhan cua bar qua khu DOI khi co du lieu moi."""
        c = d["close"].to_numpy()
        nhan = np.zeros(len(c))
        moc = 0
        for i in range(1, len(c)):
            if abs(c[i] - c[moc]) / c[moc] > 0.05:
                nhan[moc:i] = np.sign(c[i] - c[moc])   # <-- ve lai ca doan da qua
                moc = i
        return nhan

    print("=== DEMO CONG REPAINT ===\n")
    for ten, fn in [("nhan_sach   ", nhan_sach), ("nhan_repaint", nhan_repaint)]:
        kq = cong_repaint(df, fn, buoc=5, toi_da_bar=300)
        print(f"  {ten}: ty le nhan doi {kq.get('ty_le_nhan_doi', '?'):>7} "
              f"-> {kq.get('ket_luan', kq.get('loi'))}")
    print("\n  Day la cong RE NHAT va giet NHIEU phuong phap nhat. Luon chay truoc.")


if __name__ == "__main__":
    lenh = sys.argv[1] if len(sys.argv) > 1 else "help"
    if lenh == "gieo":
        gieo()
    elif lenh == "tra":
        tra(sys.argv[2] if len(sys.argv) > 2 else "")
    elif lenh == "nap":
        nap_ho_so(sys.argv[2])
    elif lenh == "bao-cao":
        bao_cao()
    elif lenh == "demo-repaint":
        demo_repaint()
    else:
        print(__doc__)
