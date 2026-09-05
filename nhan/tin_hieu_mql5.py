# -*- coding: utf-8 -*-
"""tin_hieu_mql5.py - DO NGUOC PHONG CACH DANH tu tai khoan CO LAI cong khai.

VI SAO NHANH NAY KHAC MOI NHANH KHAC.

Chu du an 04/09/2026: *"luc dau du an nay da tinh toi viec xem du lieu mql5
signal de ro nguoc lai luan ra phong cach danh => nhu ultima, nhanh do ts chua
he lam"*. Kiem lai thi dung: nguon `mql5_signals` co 36 tai lieu, va **gan het
la trang dieu huong** (Articles, CodeBase, danh sach tieng Bo Dao Nha). Dung
mot trang la signal that, va cung chi la trang tom tat.

Va day la lop nguon co tinh chat KHAC HAN 262 co che dang co. Chinh chu du an
da chi ra van de: *"o thi truong nay khong ai di share mieng banh minh co ca"*.
Dieu do dung voi **LUAT** - luat manh ma cong khai thi da bi an mat. Nhung
**HANH VI** thi khong giau duoc: mot tai khoan ban tin hieu buoc phai cong khai
duong von, muc tai, va MFE/MAE de nguoi ta dam mua. Ho giau duoc quy tac, khong
giau duoc DAU CHAN.

DUONG VAO - da do that 04/09, khong doan:

  1. `mql5.com/en/signals/<id>` - trang tom tat, 200, ~176 KB. **Trong trang co
     NHUNG SAN mot chuoi (timestamp, muc_tai)**: do that tren signal 2359404 la
     713 diem tu 17/02 den 03/09, trong do 328 diem co vi the, tai trung binh
     2,03%, tai dinh 12,54%.

  2. `mql5.com/signals/charts/risks/json?id=<id>` - **KHONG co tien to `/en`**
     (do la ly do lan do dau tien that bai: toi doan `/en/signals/charts/...`).
     Tra ve nhom 5 so mot ngay: (timestamp, loi, MFE, ?, MAE).

CAI CO THE SUY RA, va cai KHONG:

  SUY RA DUOC tu duong tai: bao lau giu mot vi the, co vao tang dan khong
  (tai tang theo bac hay nhay mot lan), tai dinh so voi tai thuong, co bao gio
  ve 0 giua chung khong. Tu MFE/MAE: chiu lo bao sau truoc khi cat, co de lai
  chay khong.

  KHONG SUY RA DUOC: dieu kien VAO LENH. Duong tai noi ho vao luc nao, khong
  noi VI SAO. Nen san pham cua file nay la mot **HO SO PHONG CACH**, khong phai
  mot co che. No thu hep khong gian tim kiem (vd "co che nay giu 3-5 ngay, vao
  tang dan 3 bac, chiu MAE toi 9%") roi de `noi_sinh` di tim co che khop ho so
  do - chu khong tu no sinh ra luat.

KHONG LAM: khong dang nhap bang tai khoan chu du an de lay du lieu sau hon.
Trang cong khai da du, va dang nhap se gan hoat dong nay vao tai khoan that.
"""
from __future__ import annotations

import re

from nhan import so as SO

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
GOC = "https://www.mql5.com"

#: Chuoi nhung trong trang: cap (timestamp, muc_tai) lien tiep, it nhat 20 cap.
_RX_CHUOI = re.compile(r"\[((?:\d{9,10},[-\d.]+,){20,}[^\]]*)\]")


def _lay(url: str, tham_so: dict | None = None, timeout: int = 30):
    import requests
    return requests.get(url, params=tham_so or {}, timeout=timeout,
                        headers={"User-Agent": UA, "Referer": GOC + "/en/signals",
                                 "X-Requested-With": "XMLHttpRequest"})


def duong_tai(html: str) -> list[tuple[int, float]]:
    """Chuoi (timestamp, muc_tai) nhung san trong trang signal."""
    m = _RX_CHUOI.search(html or "")
    if not m:
        return []
    so = [x for x in m.group(1).split(",") if x.strip()]
    ra = []
    for i in range(0, len(so) - 1, 2):
        try:
            ra.append((int(so[i]), float(so[i + 1])))
        except ValueError:
            continue
    return ra


def ho_so_phong_cach(cap: list[tuple[int, float]]) -> dict:
    """Duong tai -> ho so phong cach. Khong suy ra dieu kien vao lenh."""
    if len(cap) < 10:
        return {"du_lieu": "qua ngan"}
    import numpy as np
    t = np.array([c[0] for c in cap], dtype=float)
    v = np.array([c[1] for c in cap], dtype=float)
    co = v > 0

    # Doan GIU LIEN TUC: chuoi diem lien tiep deu co vi the.
    doan, dai = [], 0
    for x in co:
        if x:
            dai += 1
        elif dai:
            doan.append(dai)
            dai = 0
    if dai:
        doan.append(dai)

    # Vao TANG DAN: muc tai tang lien tiep bao nhieu buoc truoc khi ve 0.
    bac, cao_nhat = 0, 0
    for i in range(1, len(v)):
        if v[i] > v[i - 1] > 0:
            bac += 1
            cao_nhat = max(cao_nhat, bac)
        elif v[i] == 0:
            bac = 0

    gio = [int((x % 86400) // 3600) for x, y in zip(t, v) if y > 0]
    return {
        "so_diem": len(cap),
        "ty_le_thoi_gian_co_vi_the": round(float(co.mean()), 4),
        "tai_trung_binh": round(float(v[co].mean()) if co.any() else 0.0, 4),
        "tai_dinh": round(float(v.max()), 4),
        "so_doan_giu": len(doan),
        "doan_giu_dai_nhat": int(max(doan)) if doan else 0,
        "bac_tang_dan_cao_nhat": int(cao_nhat),
        "vao_tang_dan": cao_nhat >= 2,
        "gio_vao_hay_gap": (max(set(gio), key=gio.count) if gio else None),
    }


#: Mang so dai nhung trong trang signal, theo THU TU xuat hien:
#: 0 = growth %% theo so lenh, 1 = balance theo so lenh,
#: 2 = (luc, balance, equity), 3 = (luc, muc_tai).
_RX_MANG = re.compile(r"\[((?:[-\d.]+,){40,}[-\d.]+)\]")


def mang_trong_trang(html: str) -> list:
    """Cac mang so dai nhung trong trang signal, giu nguyen thu tu."""
    import numpy as np
    return [np.array([float(x) for x in m.group(1).split(",")])
            for m in _RX_MANG.finditer(html or "")]


def phan_loai_mang(html: str) -> dict:
    """Nhan dang tung mang theo HINH DANG, khong theo vi tri.

    Lan dau (04/09) code lay `mang[0]` la growth va `mang[3]` la muc tai. Do
    la dung tren #2359404 va SAI tren nhieu signal khac: co trang khong co du
    bon mang, co trang chen them mang khac vao giua. Quet 288 signal thi no no
    o cai thu 3 (`cannot reshape array of size 7575 into shape (2)`).

    Bon dang phan biet duoc chac chan:
      `von`     bo BA so, so dau > 1e9  -> (timestamp, balance, equity)
      `tai`     bo HAI so, so dau > 1e9, so sau trong [0, 1] -> (timestamp, tai)
      `growth`  bo HAI so, so dau la 0,2,4,... va gia tri dau = 0 -> (lenh, %)
      `balance` bo HAI so, so dau la 0,2,4,... va gia tri dau != 0 -> (lenh, tien)
    """
    import numpy as np
    ra: dict = {}
    for a in mang_trong_trang(html):
        n = len(a)
        if n % 3 == 0 and n >= 6 and (a[0::3] > 1e9).all():
            ra.setdefault("von", a.reshape(-1, 3))
            continue
        if n % 2:
            continue
        x, y = a[0::2], a[1::2]
        if (x > 1e9).all():
            if ((y >= 0) & (y <= 1)).all():
                ra.setdefault("tai", a.reshape(-1, 2))
            continue
        if len(x) > 2 and x[0] == 0 and (np.diff(x) > 0).all():
            ra.setdefault("growth" if abs(y[0]) < 1e-9 else "balance",
                          a.reshape(-1, 2))
    return ra


def duong_von(html: str):
    """(loi_suat_theo_lenh, tang_truong_cuoi_pct) tu chuoi `growth`.

    DAY la chuoi dung de tinh hieu suat, khong phai chuoi balance/equity:
    growth DA HIEU CHINH nap/rut, con balance thi khong (do that tren #2359404:
    mot buoc -398,59 USD la lenh rut, neu tinh la lo thi ra -35,8% mot ngay).
    Truc x la SO LENH chu khong phai ngay - dung no lam "loi suat ngay" se
    thoi moi thu len theo so lenh moi ngay.
    """
    import numpy as np
    g = phan_loai_mang(html).get("growth")
    if g is None or len(g) < 3:
        return np.array([]), None
    v = 1.0 + g[:, 1] / 100.0
    return np.diff(v) / v[:-1], float(g[-1, 1])


def rui_ro_json(sid: int) -> list[dict]:
    """Nhom 5 so mot ngay tu bieu do rui ro. URL KHONG co tien to `/en`.

    Thu tu la (luc, LAI, MFE, LO, MAE) - do 05/09 tren #2359404:
    LAI >= 0 va MFE >= LAI luon dung; LO <= 0 va MAE <= LO luon dung.

    HAI CAI BAY, ca hai da sap that ngay 04/09:

      1. `so[i+1]` KHONG phai loi suat cua ngay - no chi la NHANH LAI, luon
         khong am. Lay no lam loi suat cho 0/118 ngay am va +5,4%/ngay.
         Net cua ngay la `lai + lo` (o day tra san trong khoa `net`).
      2. Don vi KHONG phai % von. Ngay MAE -71,22% (14/07/2026) doi chieu
         chuoi equity thi lo treo that chi 7,6% von. Dung cac so nay de XEP
         HANG / so sanh giua cac ngay thi duoc; dung de tinh tien thi sai.
    """
    try:
        r = _lay(f"{GOC}/signals/charts/risks/json", {"id": sid})
        if r.status_code != 200:
            return []
        so = [float(x) for x in r.text.strip().strip("[]").split(",") if x.strip()]
    except Exception:
        return []
    ra = []
    for i in range(0, len(so) - 4, 5):
        lai, lo = so[i + 1], so[i + 3]
        ra.append({"luc": int(so[i]), "lai": lai, "mfe": so[i + 2],
                   "lo": lo, "mae": so[i + 4], "net": lai + lo})
    return ra


def mot_tin_hieu(sid: int, in_ra=None) -> dict:
    """Mot signal -> ho so phong cach + chiu lo. KHONG dang nhap."""
    try:
        r = _lay(f"{GOC}/en/signals/{sid}")
        if r.status_code != 200:
            return {"id": sid, "loi": f"HTTP {r.status_code}"}
        html = r.text
    except Exception as e:
        return {"id": sid, "loi": f"{type(e).__name__}: {str(e)[:80]}"}

    ten = re.search(r"<title>([^<]+)</title>", html)
    tang = re.search(r"Growth:\s*</?[^>]*>?\s*([-\d.,]+)\s*%", html)
    ho = ho_so_phong_cach(duong_tai(html))
    rr = rui_ro_json(sid)
    if rr:
        mae = [x["mae"] for x in rr if x["mae"] < 0]
        mfe = [x["mfe"] for x in rr if x["mfe"] > 0]
        ho["mae_sau_nhat"] = round(min(mae), 3) if mae else None
        ho["mae_trung_binh"] = round(sum(mae) / len(mae), 3) if mae else None
        ho["mfe_trung_binh"] = round(sum(mfe) / len(mfe), 3) if mfe else None
        ho["so_ngay_co_rui_ro"] = len(rr)
    ra = {"id": sid, "url": f"{GOC}/en/signals/{sid}",
          "ten": (ten.group(1)[:120] if ten else None),
          "tang_truong_pct": (tang.group(1) if tang else None), "ho_so": ho}
    if in_ra:
        in_ra(f"  #{sid} {str(ra['ten'])[:44]:44s} tang={ra['tang_truong_pct']} "
              f"giu={ho.get('doan_giu_dai_nhat')} bac={ho.get('bac_tang_dan_cao_nhat')} "
              f"MAE={ho.get('mae_sau_nhat')}")
    return ra


def danh_sach_id(trang: int = 1) -> list[int]:
    """ID cac signal tren mot trang danh sach cong khai."""
    try:
        r = _lay(f"{GOC}/en/signals/mt5/page{trang}")
        if r.status_code != 200:
            return []
    except Exception:
        return []
    return sorted({int(x) for x in re.findall(r"/signals/(\d{6,8})", r.text)})


def thu_thap(so_tin_hieu: int = 12, trang: int = 1, in_ra=print) -> dict:
    """Quet nhieu signal -> ghi ho so vao `tai_lieu`/`noi_dung` de sau doi chieu."""
    import json
    ids = danh_sach_id(trang)[:so_tin_hieu]
    bao = {"thay": len(ids), "doc_duoc": 0, "ghi": 0, "loi": 0}
    for sid in ids:
        r = mot_tin_hieu(sid, in_ra=in_ra)
        if r.get("loi") or not (r.get("ho_so") or {}).get("so_diem"):
            bao["loi"] += 1
            continue
        bao["doc_duoc"] += 1
        vb = json.dumps(r, ensure_ascii=False, indent=1)
        vt = SO.van_tay(r["url"])
        with SO.ket_noi() as cn:
            cn.execute(
                "INSERT OR IGNORE INTO tai_lieu(van_tay,nguon,loai,tieu_de,url,"
                "tom_tat,tu_khoa,diem,luc) VALUES(?,?,?,?,?,?,?,?,?)",
                (vt, "mql5_signals_hoso", "hieu_suat", str(r["ten"])[:180],
                 r["url"], vb[:2000], "ho_so_phong_cach", 2.5, SO.bay_gio()))
            row = cn.execute("SELECT id FROM tai_lieu WHERE van_tay=?",
                             (vt,)).fetchone()
            if row:
                c2 = cn.execute(
                    "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,"
                    "cach,so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc) "
                    "VALUES(?,?,?,'ho_so','mql5_signal',?,?,?,?,0)",
                    (row["id"], SO.van_tay("nd", r["url"]), r["url"],
                     len(vb), len(vb), vb, SO.bay_gio()))
                bao["ghi"] += c2.rowcount
    SO.ghi_chi_so("tin_hieu_ho_so", float(bao["ghi"]), {"trang": trang})
    in_ra(f"mql5 signals: {bao}")
    return bao
