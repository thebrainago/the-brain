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


def rui_ro_json(sid: int) -> list[dict]:
    """MFE/MAE theo ngay. URL KHONG co tien to `/en` - do that 04/09."""
    try:
        r = _lay(f"{GOC}/signals/charts/risks/json", {"id": sid})
        if r.status_code != 200:
            return []
        so = [float(x) for x in r.text.strip().strip("[]").split(",") if x.strip()]
    except Exception:
        return []
    ra = []
    for i in range(0, len(so) - 4, 5):
        ra.append({"luc": int(so[i]), "loi": so[i + 1], "mfe": so[i + 2],
                   "mae": so[i + 4]})
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
