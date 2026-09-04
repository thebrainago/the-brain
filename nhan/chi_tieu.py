# -*- coding: utf-8 -*-
"""chi_tieu.py - CHI TIEU NGAY va CHIA THOI LUONG THEO NEN TANG.

Chu du an 04/09/2026: *"xay bo quy dinh moi ngay can bao nhieu kenh moi, chien
luoc va code moi, phan chia ty le mang xa hoi, thoi luong uu tien"*.

CAI DA CO, KHONG VIET LAI. `nhan/vuon_nguon.chia_ngan_sach` da chia thoi luong
theo SUAT DO DUOC, co san tham do 15% va tran 75%, va da xu dung cai bay chuan
hoa (ap tran roi chia lai se day nguoc lan vua bi cat len tren tran). Module nay
KHONG dung vao phep chia do.

BA THU NO THIEU, va day la ba thu o file nay:

  1. **CHI TIEU NGAY.** `vuon_nguon` tra loi "dao o dau", khong tra loi "hom nay
     dao du chua". Khong co chi tieu thi khong phan biet duoc mot ngay yen tinh
     that voi mot ngay day chuyen chet - ca hai deu hien ra la "khong co gi
     moi".

  2. **NEN TANG, khong phai LAN.** `vuon_nguon.LAN` chi co hai ro: `hoc_thuat`
     va `xa_hoi`. Ro `xa_hoi` gom chung reddit + x + tiktok + youtube +
     telegram, nen khong tra loi duoc "telegram dang gap 10 lan tiktok" - ma do
     that 04/09 thi dung la vay.

  3. **UU TIEN THEO KHOANG THIEU.** Khoan nao dang thieu chi tieu thi duoc uu
     tien thoi luong. Do la mot vong dieu khien, khac han voi chia theo suat:
     chia theo suat lam giau cho ke dang thang, chia theo khoang thieu keo ke
     dang tut len.

NGUYEN TAC DAT CHI TIEU: **suy tu NANG LUC DO DUOC, khong tu mong muon.** Moi
con so duoi day deu kem phep do sinh ra no. Mot chi tieu bia ra chi tao them mot
cai bao dong sai moi ngay, va roi khong ai doc no nua.

CHI TIEU KHONG PHAI MOT LOI HUA. Khong dat chi tieu KHONG phai loi - no la mot
cau hoi: het nguon that, hay day chuyen dut? `bao_cao()` tra ve du so de phan
biet, khong tu ket luan.
"""
from __future__ import annotations

from nhan import so as SO

#: CHI TIEU NGAY. Moi muc: (chi so do duoc, muc tieu, vi sao la con so do).
#:
#: Cac con so duoi day suy tu ngay 04/09/2026 - ngay dau tien day chuyen chay
#: het cac chang. Dat o khoang **1/3 nang luc do duoc**, vi mot ngay binh
#: thuong khong co nguoi ngoi canh go lenh.
CHI_TIEU = {
    "nguon_moi": {
        "chi_so": "kham_pha_de_nghi",
        "muc_tieu": 5,
        "vi_sao": "Do 04/09: mot luot kham pha telegram ra 22 nguon ung vien "
                  "trong 13 giay. Nhung tim kiem BAO HOA nhanh - cung bo tu "
                  "khoa se tra ve cung cac kenh. Nen 5/ngay la muc doi hoi phai "
                  "co tu khoa moi hoac kenh kham pha moi, chu khong phai chay "
                  "lai cai cu.",
    },
    "tai_lieu": {
        "chi_so": "seeker_tai_lieu_moi|telegram_mtproto_ban_doc|"
                  "nguon_bai_viet_ban_doc_moi|doc_pdf_ban_doc",
        "muc_tieu": 150,
        "vi_sao": "Do 04/09: 432 tai lieu moi trong mot ngay co nguoi go lenh. "
                  "Mot ngay tu chay dat ~1/3 la hop ly.",
    },
    "co_che": {
        "chi_so": "boc_co_che_moi",
        "muc_tieu": 10,
        "vi_sao": "Do 04/09: kho 191 -> 227, tuc 36 co che trong mot ngay, o "
                  "suat 3,3-23,3 tren 100 ban doc tuy nguon. 10/ngay doi khoang "
                  "60-150 ban doc dung nguon - vua tam mot luot tu dong.",
    },
    "ma_nguon": {
        "chi_so": "boc_artifact|ma_nguon_ghi_moi",
        "muc_tieu": 20,
        "vi_sao": "Do 04/09: 99 artifact ma nguon duoc boc, va rieng @mqlfree "
                  "cho 39 file .mq4/.mq5 tho tren 300 tin. Ma nguon la lop "
                  "nguon co mat do luat cao nhat do duoc (23,3/100).",
    },
}

#: NEN TANG XA HOI - tach ro `vuon_nguon.LAN["xa_hoi"]` de do duoc tung cai.
#: `ty_le_san` la phan toi thieu cua thoi luong xa hoi, con lai chia theo suat.
#:
#: Con so `ty_le_san` KHONG phai uoc luong gia tri - no la GIA THAM DO. Nen tang
#: nao chua do duoc suat thi van phai duoc mot phan, neu khong no bi khoa vinh
#: vien o 0 va khong bao gio chung minh nguoc lai duoc (dung ly le cua
#: `vuon_nguon.SAN_THAM_DO`, ap o muc nen tang).
NEN_TANG = {
    "telegram": {"ty_le_san": 0.12, "chi_so": "telegram_mtproto_ban_doc",
                 "ghi_chu": "do 04/09: nen tang xa hoi duy nhat cho ra ma nguon "
                            "tho (@mqlfree 39 file/300 tin)"},
    "reddit": {"ty_le_san": 0.07, "chi_so": "reddit_ban_doc"},
    "youtube": {"ty_le_san": 0.05, "chi_so": "youtube_ban_doc",
                "ghi_chu": "chua co bo doc video - xem kham_pha_nguon.CHUA_LAM"},
    "x": {"ty_le_san": 0.05, "chi_so": "x_ban_doc"},
    "tiktok": {"ty_le_san": 0.03, "chi_so": "tiktok_ban_doc"},
    "dien_dan": {"ty_le_san": 0.07, "chi_so": "dien_dan_ban_doc"},
    "track_record": {"ty_le_san": 0.06, "chi_so": "track_record_ban_doc"},
}

#: TONG SAN phai o duoi 1 MOT KHOANG RONG, neu khong phan chia theo suat khong
#: bao gio co tac dung.
#:
#: DO THAT ngay trong lan chay dau 04/09: ban dau cac san la
#: 0,30+0,15+0,10+0,10+0,05+0,15+0,15 = **dung 1,00**, nen `con = 0` va nhanh
#: chia theo so ban doc do duoc khong chay lan nao. Bang chia ra trong y het
#: mot bang chia theo suat, nhung thuc chat la mot bang HANG SO - dung hinh dang
#: "cong tu choi tat ca cho so lieu y het cong hieu chuan tot".
#:
#: Nay tong san = 0,45, tuc 55% thoi luong THAT SU di theo do luong.
TONG_SAN_TOI_DA = 0.60


def _tong_chi_so(ten_gop: str, ngay: str | None = None) -> float | None:
    """Tong gia tri cua mot (hoac nhieu, ngan cach `|`) chi so trong NGAY.

    Tra `None` khi chi so CHUA TUNG duoc ghi - khac han voi 0. `None` nghia la
    "chua do", `0` nghia la "da do va bang khong". Lan lon hai cai nay la ho loi
    da sap nhieu lan trong du an nay.
    """
    ten = [t.strip() for t in ten_gop.split("|") if t.strip()]
    if not ten:
        return None
    cho = ",".join("?" for _ in ten)
    dieu = "luc >= date('now','localtime')" if ngay is None else "date(luc) = ?"
    args = list(ten) + ([] if ngay is None else [ngay])
    r = SO.nhieu(
        f"SELECT COUNT(*) n, COALESCE(SUM(gia_tri),0) tong FROM chi_so_vh "
        f"WHERE ten IN ({cho}) AND {dieu}", *args)
    d = dict(r[0]) if r else {"n": 0, "tong": 0}
    if not d["n"]:
        # Chi so nay da bao gio ton tai chua? Neu chua thi la CHUA DO.
        r2 = SO.nhieu(f"SELECT COUNT(*) n FROM chi_so_vh WHERE ten IN ({cho})",
                      *ten)
        if not dict(r2[0])["n"]:
            return None
    return float(d["tong"])


def bao_cao(ngay: str | None = None) -> dict:
    """Hom nay dat chi tieu nao, thieu cai nao, va thieu bao nhieu."""
    ra = {"ngay": ngay or "hom nay", "muc": {}, "dat": 0, "thieu": 0,
          "chua_do": 0}
    for ten, c in CHI_TIEU.items():
        thuc = _tong_chi_so(c["chi_so"], ngay)
        if thuc is None:
            trang_thai, khoang = "CHUA_DO", None
        elif thuc >= c["muc_tieu"]:
            trang_thai, khoang = "DAT", 0.0
        else:
            trang_thai, khoang = "THIEU", c["muc_tieu"] - thuc
        ra["muc"][ten] = {"muc_tieu": c["muc_tieu"], "thuc": thuc,
                          "trang_thai": trang_thai, "thieu": khoang}
        ra[{"DAT": "dat", "THIEU": "thieu", "CHUA_DO": "chua_do"}[trang_thai]] += 1
    return ra


def uu_tien(ngay: str | None = None) -> dict[str, float]:
    """Trong so uu tien theo KHOANG THIEU, chuan hoa ve tong 1.

    Khoan dang thieu nhieu nhat duoc nhieu thoi luong nhat. Khoan da dat nhan 0
    - khong phai de phat no, ma vi thoi luong con lai co cho tot hon de di.

    Muc `CHUA_DO` duoc tinh nhu THIEU TOAN BO: mot chi so chua bao gio duoc ghi
    thuong nghia la khau do CHUA CHAY LAN NAO, va do la thu can uu tien nhat.
    """
    bc = bao_cao(ngay)
    tho = {}
    for ten, m in bc["muc"].items():
        if m["trang_thai"] == "CHUA_DO":
            tho[ten] = float(m["muc_tieu"])
        elif m["trang_thai"] == "THIEU":
            tho[ten] = float(m["thieu"])
        else:
            tho[ten] = 0.0
    tong = sum(tho.values())
    if tong <= 0:
        # Dat het: chia deu, vi khong con tin hieu nao de nghieng.
        n = max(len(tho), 1)
        return {t: 1.0 / n for t in tho}
    return {t: v / tong for t, v in tho.items()}


def chia_nen_tang(tong_giay: float, ngay: str | None = None) -> dict[str, float]:
    """Chia thoi luong XA HOI cho tung nen tang: san khai bao + phan theo suat.

    Moi nen tang nhan `ty_le_san` cua no truoc (gia tham do), phan con lai chia
    theo SO BAN DOC do duoc hom nay. Nen tang chua do duoc gi chi nhan san -
    dung, vi ta chua co co so nao de cho no hon.
    """
    san = {t: c["ty_le_san"] for t, c in NEN_TANG.items()}
    tong_san = sum(san.values())
    if tong_san > TONG_SAN_TOI_DA:           # san khai qua tay -> co lai
        san = {t: v * TONG_SAN_TOI_DA / tong_san for t, v in san.items()}
        tong_san = TONG_SAN_TOI_DA
    con = 1.0 - tong_san

    do = {}
    for t, c in NEN_TANG.items():
        v = _tong_chi_so(c["chi_so"], ngay)
        do[t] = 0.0 if v is None else float(v)
    tong_do = sum(do.values())

    phan = dict(san)
    if con > 1e-9 and tong_do > 0:
        for t in phan:
            phan[t] += con * do[t] / tong_do
    elif con > 1e-9:
        for t in phan:
            phan[t] += con / max(len(phan), 1)
    return {t: round(tong_giay * v, 1) for t, v in phan.items()}


def in_bao_cao(ngay: str | None = None, in_ra=print) -> dict:
    bc = bao_cao(ngay)
    in_ra(f"CHI TIEU {bc['ngay']}: {bc['dat']} dat / {bc['thieu']} thieu / "
          f"{bc['chua_do']} chua do")
    for ten, m in bc["muc"].items():
        thuc = "chua do" if m["thuc"] is None else f"{m['thuc']:.0f}"
        in_ra(f"  {ten:<12} {thuc:>8} / {m['muc_tieu']:<5} {m['trang_thai']}")
    ut = uu_tien(ngay)
    in_ra("  uu tien thoi luong: " +
          ", ".join(f"{t} {v*100:.0f}%" for t, v in
                    sorted(ut.items(), key=lambda x: -x[1]) if v > 0))
    return bc
