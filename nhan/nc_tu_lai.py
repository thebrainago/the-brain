# -*- coding: utf-8 -*-
"""nc_tu_lai.py - TU LAI: chuong trinh nghien cuu co dinh KHONG can LLM, dung chung cong cu va so tay.

Ba viec, khong viec nao la "thay nha nghien cuu AI":

1. **Duong nen.** Mot quy trinh tat dinh: ho so -> tim quy luat -> thu -> mo xe
   lenh -> bien the (bo loc / quan tri) -> quet hinh dang -> xac nhan -> niem
   phong. Neu AI (Claude) khong lam tot hon quy trinh nay tren cung du lieu thi
   AI chua dang dong tien nao - so sanh duoc vi ca hai ghi cung so tay.
2. **Bai kiem tich hop.** Chay het moi cong cu tu dau toi cuoi, tren may khong
   co LLM (cloud, test).
3. **HIEU CHUAN HAI CHIEU** (`hieu_chuan`). Chay tren chuoi `TONG_HOP_*` biet
   truoc dap an: phai TIM RA edge cai san (HOI_QUY, LOC) va KHONG tim ra gi tren
   NHIEU. Luat du an: *"mot cong tu choi TAT CA cho so lieu y het mot cong tot"*
   - nen phai do ca hai chieu, va ghi so do ra `reports/NC_HIEU_CHUAN.md`.

Khi het token Claude, `b nc tu-lai <MA> <KHUNG>` giu cho so tay van lon len.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import nc_so_tay as ST, nc_thi_nghiem as TN

LAB = Path(__file__).resolve().parent.parent
P_NGUONG = 0.10


def _hon(r: dict) -> float:
    """Diem xep bien the: tien tot nhat voi maxDD duoi tran chu du an (khong phai hon moc)."""
    t = (r or {}).get("tien") or {}
    v = t.get("cagr_duoi_tran_pct")
    return float(v) if v is not None and t.get("co_lai") else -1e9


def chay(ma: str, khung: str = "H4", so_null: int = 200, toi_da_luat: int = 3,
         mo_niem_phong: bool = True, vong_id: int | None = None, in_ra=print) -> dict:
    """Mot chuong trinh nghien cuu tron ven tren (ma, khung). Tra ve nhat ky tung buoc."""
    rieng = vong_id is None
    if rieng:
        vong_id = ST.bat_dau_vong("tu_lai", "khong_llm")
    t0 = time.time()
    ma, khung = str(ma).upper(), str(khung).upper()
    nk: list[dict] = []

    def _b(buoc, **kw):
        nk.append({"buoc": buoc, **kw})
        in_ra("  [%s] %s" % (buoc, json.dumps(kw, ensure_ascii=False, default=str)[:220]))

    hs = TN.ho_so(ma, khung, vong_id=vong_id)
    _b("ho_so", trang_thai=hs.get("trang_thai"), goi_y=hs.get("goi_y_huong"))
    ql = TN.tim_quy_luat(ma, khung, so_null=so_null, vong_id=vong_id)
    luat = [l for l in ql.get("luat", [])
            if (l.get("p_null") or 1.0) <= P_NGUONG and (l.get("tb_rong_bps") or 0) > 0]
    # moi (dieu kien, chieu) mot lan - nhieu chan troi cua cung mot dieu kien la MOT y
    da, chon = set(), []
    for l in luat:
        k = (l["dieu_kien"], l["chieu"])
        if k not in da:
            da.add(k)
            chon.append(l)
    chon = chon[:toi_da_luat]
    _b("tim_quy_luat", trang_thai=ql.get("trang_thai"), so_luat_qua_null=len(chon),
       null=ql.get("null"), tn=ql.get("tn_id"))
    ket = []
    if not chon:
        gt = ST.them_gia_thuyet(
            "%s/%s co quy luat 1-2 dac trung du bao loi suat 1-10 bar sau chi phi" % (ma, khung),
            "kiem tra noi sinh tong quat cua tu lai truoc khi AI dao sau", "quay_ve_trung_binh",
            {"ma": ma, "khung": khung}, nguon="tu_lai")
        ST.cap_nhat_gia_thuyet(gt, "BAC_BO", ket_luan="khong luat nao p_null <= %.2f (null trung vi %s)"
                               % (P_NGUONG, (ql.get("null") or {}).get("cuc_dai_trung_vi")))
        if ql.get("tn_id"):
            ST.them_hieu_biet("%s/%s: tren kham pha khong co quy luat 1-2 dac trung nao vuot cuc "
                              "dai cua nhieu (p_null <= %.2f) sau chi phi" % (ma, khung, P_NGUONG),
                              0.6, [ql["tn_id"]], {"ma": ma, "khung": khung})
    for l in chon:
        spec = l["spec"]
        gt = ST.them_gia_thuyet(
            "%s/%s: khi %s thi %s giu %d bar co lai sau chi phi"
            % (ma, khung, l["dieu_kien"], "mua" if l["chieu"] > 0 else "ban", l["giu"]),
            "quy luat noi sinh p_null %s, rong %.1f bps/lenh tren kham pha - tu lai chua giai thich "
            "duoc ai tra tien; AI/nguoi can dien" % (l["p_null"], l["tb_rong_bps"]),
            spec.get("ho", ""), {"ma": ma, "khung": khung}, nguon="tu_lai:tim_quy_luat")
        ST.cap_nhat_gia_thuyet(gt, "DANG_THU")
        ung = [("goc", spec, None, TN.danh_gia(ma, khung, spec, gt_id=gt, vong_id=vong_id))]
        mx = TN.mo_xe(ma, khung, spec, so_null=so_null, gt_id=gt, vong_id=vong_id)
        if mx.get("trang_thai") == "DAT" and mx.get("luat_loc"):
            s2 = mx["luat_loc"][0]["spec_de_xuat"]
            ung.append(("loc", s2, None, TN.danh_gia(ma, khung, s2, gt_id=gt, vong_id=vong_id)))
        for g in ((mx.get("thoat") or {}).get("goi_y_quan_tri") or [])[:2]:
            ung.append(("qt", spec, g["luat"],
                        TN.danh_gia(ma, khung, spec, g["luat"], gt_id=gt, vong_id=vong_id)))
        _b("bien_the", gt=gt, ket=[(u[0], u[2], u[3].get("trang_thai"), _hon(u[3])) for u in ung],
           mo_xe=mx.get("trang_thai"))
        dat = [u for u in ung if u[3].get("trang_thai") == "DAT"]
        if not dat:
            if all(u[3].get("trang_thai") == "CHUA_DO_DUOC" for u in ung):
                # it lenh / khai bao hong: KHONG phai bac bo (ba trang thai)
                ST.cap_nhat_gia_thuyet(gt, "DANG_THU", ket_luan="chua do duoc tren kham pha: %s"
                                       % ung[0][3].get("ly_do"))
                ket.append({"gt": gt, "ket": "CHUA_DO_DUOC_KHAM_PHA"})
                continue
            ST.cap_nhat_gia_thuyet(gt, "BAC_BO", ket_luan="khong bien the nao co lai tren kham pha "
                                   "sau chi phi (%s)" % "; ".join(str(u[3].get("ly_do"))[:80]
                                                                 for u in ung))
            ket.append({"gt": gt, "ket": "BAC_BO_KHAM_PHA"})
            continue
        ten, sb, qb, rb = max(dat, key=lambda u: _hon(u[3]))
        q = TN.quet(ma, khung, sb, quan_tri=qb, gt_id=gt, vong_id=vong_id, toi_da_o=60)
        _b("quet", gt=gt, bien_the=ten, hinh=q.get("hinh_dang"), ty_le=q.get("ty_le_o_co_lai"))
        if q.get("hinh_dang") != "CAO_NGUYEN":
            ST.cap_nhat_gia_thuyet(gt, "BAC_BO", ket_luan="quet ra %s (ty le o co lai %s) - khong "
                                   "phai cao nguyen" % (q.get("hinh_dang") or q.get("trang_thai"),
                                                        q.get("ty_le_o_co_lai")))
            ket.append({"gt": gt, "ket": "BAC_BO_HINH_DANG"})
            continue
        x = TN.danh_gia(ma, khung, sb, qb, "xac_nhan", gt, vong_id)
        _b("xac_nhan", gt=gt, trang_thai=x.get("trang_thai"), cagr_duoi_tran=_hon(x),
           lenh=(x.get("lenh") or {}).get("so_lenh"))
        if x.get("trang_thai") == "CHUA_DO_DUOC":
            ST.cap_nhat_gia_thuyet(gt, "DANG_THU", ket_luan="xac nhan CHUA DO DUOC (%s) - can them "
                                   "lenh: ghep ma/khung khac, khong phai bac bo" % x.get("ly_do"))
            ket.append({"gt": gt, "ket": "CHUA_DO_DUOC_XAC_NHAN"})
            continue
        if x.get("trang_thai") != "DAT":
            ST.cap_nhat_gia_thuyet(gt, "BAC_BO", ket_luan="truot xac nhan: %s" % x.get("ly_do"))
            ket.append({"gt": gt, "ket": "TRUOT_XAC_NHAN"})
            continue
        ST.cap_nhat_gia_thuyet(gt, "TRIEN_VONG", ket_luan="qua xac nhan: %s" % x.get("ly_do"))
        bang_chung = [i for i in (rb.get("tn_id"), q.get("tn_id"), x.get("tn_id")) if i]
        if mo_niem_phong:
            npk = TN.niem_phong(ma, khung, sb, qb, gt, vong_id)
            _b("niem_phong", gt=gt, trang_thai=npk.get("trang_thai"), ly_do=npk.get("ly_do"))
            if npk.get("tn_id"):
                bang_chung.append(npk["tn_id"])
            ket.append({"gt": gt, "ket": "NIEM_PHONG_" + str(npk.get("trang_thai")),
                        "spec": sb, "quan_tri": qb})
        else:
            ket.append({"gt": gt, "ket": "QUA_XAC_NHAN", "spec": sb, "quan_tri": qb})
        ST.them_hieu_biet("%s/%s: %s (%s) qua kham pha + quet cao nguyen + xac nhan"
                          % (ma, khung, sb["ten"], ten), 0.6 if mo_niem_phong else 0.5,
                          bang_chung, {"ma": ma, "khung": khung})
    tom = "tu lai %s/%s: %d luat qua null, ket: %s" % (
        ma, khung, len(chon), ", ".join("gt%s=%s" % (k["gt"], k["ket"]) for k in ket) or "khong")
    if rieng:
        so_tn = int(ST.mot("SELECT COUNT(*) n FROM thi_nghiem WHERE vong_id=?", vong_id).get("n") or 0)
        ST.ket_thuc_vong(vong_id, tom, so_tn)
    return {"ma": ma, "khung": khung, "vong_id": vong_id, "ket": ket, "nhat_ky": nk,
            "tom_tat": tom, "giay": round(time.time() - t0, 1)}


# ============================================================ HIEU CHUAN
KICH_BAN_HIEU_CHUAN = ("TONG_HOP_NHIEU_1", "TONG_HOP_NHIEU_2", "TONG_HOP_NHIEU_3",
                       "TONG_HOP_HOI_QUY_1", "TONG_HOP_HOI_QUY_2", "TONG_HOP_LOC_1",
                       "TONG_HOP_XU_HUONG_1")
#: He goc "mua sau cu giam 3 bar" cho bai kiem HOC TU LENH (mo xe) - y tuong dung
#: nua voi, dung loai he chu du an hay dua vao: can bo loc moi thanh he.
SPEC_GOC_HOC_LENH = {
    "ten": "mua_sau_cu_giam_3_bar", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 5,
    "co_che": "Ban thao sau cu giam 3 bar lon so voi binh thuong; nguoi mua cung cap thanh "
              "khoan duoc tra bang cu hoi.",
    "vao": [{"trai": {"chi_bao": "zscore", "cua": {"chi_bao": "doi_pct",
                                                   "cua": {"chi_bao": "gia", "cot": "close"}, "n": 3},
                      "n": 250}, "phep": "<", "phai": {"hang": -1.0}}]}


def _co_edge(ma: str) -> bool:
    from nhan import nc_du_lieu as NDL
    kb, _hat = NDL._tach_ten_tong_hop(ma)
    return bool(NDL.CO_EDGE_SAU_PHI[kb])


def _ket_cuc(ket: list[dict]) -> str:
    """DAT (tim + xac nhan + niem phong DAT) / CHUA_DO_DUOC (co ung vien nhung mau qua nho) / KHONG."""
    nhan = [k["ket"] for k in ket]
    if "NIEM_PHONG_DAT" in nhan:
        return "DAT"
    if any(n.startswith("CHUA_DO_DUOC") or n == "NIEM_PHONG_CHUA_DO_DUOC" for n in nhan):
        return "CHUA_DO_DUOC"
    return "KHONG"


def hoc_tu_lenh(cac_ma=("TONG_HOP_LOC_1", "TONG_HOP_LOC_2", "TONG_HOP_NHIEU_1", "TONG_HOP_NHIEU_2"),
                khung: str = "H4", so_null: int = 200) -> list[dict]:
    """Mo xe he goc, roi CHAY LAI he da loc tren xac_nhan. Co edge: phai tim bo loc (p<=0,05)
    va he loc thang he goc tren doan chua nhin. Nhieu: khong duoc tim ra bo loc p<=0,05."""
    ra = []
    for ma in cac_ma:
        mx = TN.mo_xe(ma, khung, SPEC_GOC_HOC_LENH, so_null=so_null)
        l = (mx.get("luat_loc") or [None])[0]
        tim = bool(l and (l.get("p_null") or 1) <= 0.05)
        d = {"ma": ma, "co_edge_that": _co_edge(ma), "bo_loc": l and l["dieu_kien"],
             "p_null": l and l["p_null"], "tim_ra": tim}
        if tim:
            g = TN.danh_gia(ma, khung, SPEC_GOC_HOC_LENH, doan="xac_nhan")
            v = TN.danh_gia(ma, khung, l["spec_de_xuat"], doan="xac_nhan")
            d.update(kv_goc_xn=(g.get("lenh") or {}).get("ky_vong_bps"),
                     kv_loc_xn=(v.get("lenh") or {}).get("ky_vong_bps"),
                     cagr_loc_xn=_hon(v), xn_loc=v.get("trang_thai"))
            d["dung"] = d["co_edge_that"] and v.get("trang_thai") == "DAT" and _hon(v) > _hon(g)
        else:
            d["dung"] = not d["co_edge_that"]
        ra.append(d)
    return ra


#: Gia thuyet CO CHU DICH cua bai do cong suat: dung co che da cai trong HOI_QUY_YEU,
#: phat bieu TRUOC khi nhin du lieu (nhu mot nha nghien cuu co kien thuc thi truong).
SPEC_CO_CHU_DICH = {
    "ten": "ibs_day_khi_bien_dong_cao", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
    "co_che": "Ban thao cuoi bar trong luc bien dong cao day gia qua sau; nguoi cung cap thanh "
              "khoan qua dem duoc tra bang cu hoi bar sau.",
    "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.15}},
            {"trai": {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
             "phep": ">", "phai": {"hang": 0.65}}]}


def do_cong_suat(so_hat: int = 8, khung: str = "H4", so_null: int = 200) -> dict:
    """DO TIM RONG vs GIA THUYET CO CHU DICH tren cung du lieu (edge yeu, t sau phi ~ 2,3).

    Do tim rong: `tim_quy_luat` (~3.000 dieu kien, p_null da tinh viec do tim).
    Co chu dich: MOT phep thu `thu_co_che` voi gia thuyet phat bieu truoc; phat hien khi
    t theo lenh > 1,645 (mot phia 5%). Doi chung: cung phep thu tren NHIEU cung hat.
    """
    from scipy import stats
    rong, dich, dich_nhieu = [], [], []
    for h in range(1, so_hat + 1):
        ma = "TONG_HOP_HOI_QUY_YEU_%d" % h
        r = TN.tim_quy_luat(ma, khung, so_null=so_null)
        l = (r.get("luat") or [None])[0]
        rong.append(bool(l and (l.get("p_null") or 1) <= 0.05))
        for ds, m in ((dich, ma), (dich_nhieu, "TONG_HOP_NHIEU_%d" % h)):
            g = TN.danh_gia(m, khung, SPEC_CO_CHU_DICH)
            t = (g.get("lenh") or {}).get("t_lenh")
            ds.append(bool(t is not None and t > stats.norm.ppf(0.95)))
    return {"so_hat": so_hat, "do_tim_rong_phat_hien": sum(rong),
            "co_chu_dich_phat_hien": sum(dich), "co_chu_dich_bao_dong_gia_tren_nhieu": sum(dich_nhieu),
            "chi_tiet": {"rong": rong, "dich": dich, "dich_nhieu": dich_nhieu}}


def do_bao_dong_gia(so_hat: int = 30, khung: str = "H4", so_null: int = 200) -> dict:
    """Ti le `tim_quy_luat` bao p_null <= 0,05 / 0,10 tren NHIEU THUAN - phai ~5% / ~10%."""
    p = []
    for h in range(1, so_hat + 1):
        r = TN.tim_quy_luat("TONG_HOP_NHIEU_%d" % h, khung, so_null=so_null)
        l = (r.get("luat") or [None])[0]
        p.append(float(l["p_null"]) if l and l.get("p_null") is not None else 1.0)
    p = sorted(p)
    return {"so_hat": so_hat, "p_tot_nhat": [round(x, 3) for x in p],
            "ty_le_p_le_0_05": round(sum(x <= 0.05 for x in p) / so_hat, 3),
            "ty_le_p_le_0_10": round(sum(x <= 0.10 for x in p) / so_hat, 3)}


def _ba_doan(ma: str, khung: str, spec: dict) -> tuple[str, dict]:
    """Giao thuc cua AI: kham_pha -> (chi khi DAT) xac_nhan -> (chi khi DAT) niem_phong.

    -> (doan XA NHAT ma he DAT: "" / "kham_pha" / "xac_nhan" / "niem_phong", ket qua niem phong).
    Kham pha CHUA_DO_DUOC -> "CHUA_DO_DUOC" (ba trang thai: khau do hong khong duoc lan vao AM).
    """
    gt = ST.them_gia_thuyet("kiem cong: %s tren %s/%s" % (spec["ten"], ma, khung),
                            "do ti le lot cua cong ba doan", spec.get("ho", ""),
                            {"ma": ma, "khung": khung}, nguon="hieu_chuan")
    tt = TN.danh_gia(ma, khung, spec, gt_id=gt).get("trang_thai")
    if tt == "CHUA_DO_DUOC":
        return "CHUA_DO_DUOC", {}
    if tt != "DAT":
        return "", {}
    if TN.danh_gia(ma, khung, spec, doan="xac_nhan", gt_id=gt).get("trang_thai") != "DAT":
        return "kham_pha", {}
    n = TN.niem_phong(ma, khung, spec, gt_id=gt, cong_that=False)
    return ("niem_phong" if n.get("trang_thai") == "DAT" else "xac_nhan"), n


def _dem_ba_doan(ket: list[tuple[str, dict]]) -> dict:
    den = [d for d, _ in ket]
    dat = [n for d, n in ket if d == "niem_phong"]
    ra = {"y_tuong": len(den), "chua_do_duoc": sum(d == "CHUA_DO_DUOC" for d in den),
          "qua_kham_pha": sum(d in ("kham_pha", "xac_nhan", "niem_phong") for d in den),
          "qua_xac_nhan": sum(d in ("xac_nhan", "niem_phong") for d in den),
          "dat_niem_phong": len(dat),
          "dat_mang_nhan_khong_hon_moc": sum(
              any("KHONG hon moc" in x for x in ((n.get("nhan") or {}).get("canh_bao") or []))
              for n in dat),
          "dat_mang_nhan_beta": sum(
              any("BETA" in x for x in ((n.get("nhan") or {}).get("canh_bao") or []))
              for n in dat),
          "dat_mang_nhan_beta_hoac_moc": sum(
              any(("BETA" in x or "KHONG hon moc" in x)
                  for x in ((n.get("nhan") or {}).get("canh_bao") or []))
              for n in dat)}
    ra["ty_le_dat_niem_phong"] = round(len(dat) / max(len(den), 1), 4)
    return ra


def y_tuong_ngau_nhien(ma: str, khung: str, so_y: int, rng) -> list[dict]:
    """`so_y` y tuong KHONG co co che: mot dieu kien dac trung lien tuc, nguong o phan vi
    10-30% (`<`) hoac 70-90% (`>=`) cua doan kham pha, chieu va thoi gian giu ngau nhien."""
    import numpy as np
    from nhan import nc_dac_trung as DT, nc_du_lieu as NDL
    pre, a = NDL.cat_doan(NDL.nap(ma, khung), "kham_pha")
    X = DT.tinh(pre).iloc[a:]
    ten = sorted(t for t in X.columns if X[t].nunique() > 30)
    ra = []
    for i in range(so_y):
        t = str(rng.choice(ten))
        phep = str(rng.choice(["<", ">="]))
        q = rng.uniform(0.1, 0.3) if phep == "<" else rng.uniform(0.7, 0.9)
        ra.append({"ten": "ngau_nhien_%s_%d" % (ma.lower()[-12:], i),
                   "ho": DT.HO_THEO_NHOM.get(DT.DAC_TRUNG[t][2], "xu_huong"),
                   "chieu": int(rng.choice([1, -1])), "giu": int(rng.choice([1, 3, 5, 10])),
                   "co_che": "Y tuong NGAU NHIEN de do ti le lot cua cong - khong co co che nao.",
                   "vao": [DT.dieu_kien(t, phep, float(np.nanquantile(X[t].dropna(), q)))]})
    return ra


def do_cong_ba_doan(so_hat: int = 10, so_y: int = 20, khung: str = "H4", hat: int = 0) -> dict:
    """Hieu chuan HAI chieu cua CHINH CONG ba doan (tieu chi chu du an 25/09).

    `hieu_chuan` do ca day chuyen, trong do bo tim quy luat (null da hieu chuan) chan nhieu
    TRUOC khi cong kip thay. Nhung AI cung dua THANG y tuong vao thu_co_che -> xac_nhan ->
    niem_phong, va cong "chi can co lai va maxdd duoi 80%" long hon cong cu. Nen do:
      * chieu NHIEU: y tuong ngau nhien tren NHIEU - bao nhieu lot tung doan va DAT niem phong.
        Day la ti le "may man" ma nhan so phep thu / Sharpe giam phat phai canh.
      * chieu CO EDGE: gia thuyet co chu dich tren HOI_QUY va HOI_QUY_YEU cung so hat.
    """
    import numpy as np
    rng = np.random.default_rng(hat)
    khong_edge = {}
    for kb in ("NHIEU", "BETA"):
        ket = []
        for h in range(1, so_hat + 1):
            ma = "TONG_HOP_%s_%d" % (kb, h)
            ket += [_ba_doan(ma, khung, s) for s in y_tuong_ngau_nhien(ma, khung, so_y, rng)]
        khong_edge[kb] = _dem_ba_doan(ket)
    edge = {}
    for kb in ("HOI_QUY", "HOI_QUY_YEU"):
        edge[kb] = _dem_ba_doan([_ba_doan("TONG_HOP_%s_%d" % (kb, h), khung,
                                          dict(SPEC_CO_CHU_DICH, ten="co_chu_dich_%s" % kb.lower()))
                                 for h in range(1, so_hat + 1)])
    return {"so_hat": so_hat, "so_y_moi_hat": so_y, "khong_edge": khong_edge, "co_edge": edge}


def hieu_chuan(cac_ma=KICH_BAN_HIEU_CHUAN, khung: str = "H4", so_null: int = 200,
               so_hat_bao_dong: int = 0, so_hat_cong_suat: int = 0, ghi_bao_cao: bool = True,
               in_ra=print) -> dict:
    """Chay tu lai + hoc tu lenh tren chuoi CO DAP AN, trong so tay TAM (khong dung so that).

    Ba ket cuc cho moi chuoi: DAT / CHUA_DO_DUOC / KHONG. Chuoi co edge ma ra CHUA_DO_DUOC
    la "chua ket luan" (vd he dung nhung qua thua de xac nhan tren 20% du lieu) - khong tinh
    la bo sot, cung khong tinh la dung.
    """
    db_cu = ST.DB
    ST.DB = Path(tempfile.mkdtemp(prefix="nc_hieu_chuan_")) / "nc.db"
    ket, hl, bd, cs, cg = [], [], None, None, None
    try:
        for ma in cac_ma:
            in_ra("== %s" % ma)
            r = chay(ma, khung, so_null=so_null, in_ra=in_ra)
            co_edge = _co_edge(ma)
            kc = _ket_cuc(r["ket"])
            dung = (kc == "DAT") if co_edge else (kc != "DAT")
            ket.append({"ma": ma, "co_edge_that": co_edge, "so_luat_qua_null":
                        next((b.get("so_luat_qua_null") for b in r["nhat_ky"]
                              if b["buoc"] == "tim_quy_luat"), None),
                        "ket_cuc": kc, "ket": [k["ket"] for k in r["ket"]],
                        "danh_gia": ("DUNG" if dung else
                                     "CHUA_KET_LUAN" if (co_edge and kc == "CHUA_DO_DUOC") else "SAI"),
                        "giay": r["giay"]})
        in_ra("== hoc tu lenh")
        hl = hoc_tu_lenh(so_null=so_null)
        if so_hat_bao_dong:
            in_ra("== do bao dong gia tren %d hat nhieu" % so_hat_bao_dong)
            bd = do_bao_dong_gia(so_hat_bao_dong, khung, so_null)
        if so_hat_cong_suat:
            in_ra("== do cong suat: do tim rong vs gia thuyet co chu dich (%d hat)" % so_hat_cong_suat)
            cs = do_cong_suat(so_hat_cong_suat, khung, so_null)
            in_ra("== do cong ba doan: y tuong ngau nhien tren nhieu/beta vs gia thuyet co edge")
            # D1 them vao vi la truong hop XAU NHAT cho cong: phi nho so voi nhieu cua mot nen.
            cg = {k: do_cong_ba_doan(10, 20, k) for k in dict.fromkeys((khung, "D1"))}
    finally:
        ST.DB = db_cu
    tom = {"so_kich_ban": len(ket),
           "dung": sum(k["danh_gia"] == "DUNG" for k in ket),
           "chua_ket_luan": sum(k["danh_gia"] == "CHUA_KET_LUAN" for k in ket),
           "sai": sum(k["danh_gia"] == "SAI" for k in ket),
           "bao_dong_gia": sum(1 for k in ket if not k["co_edge_that"] and k["ket_cuc"] == "DAT"),
           "hoc_tu_lenh_dung": "%d/%d" % (sum(d["dung"] for d in hl), len(hl)),
           "chi_tiet": ket, "hoc_tu_lenh": hl, "bao_dong_gia_tim_quy_luat": bd,
           "cong_suat": cs, "cong_ba_doan": cg}
    if ghi_bao_cao:
        L = ["# HIEU CHUAN NHA NGHIEN CUU - chuoi co dap an",
             "", "*%s · sinh boi `python b.py nc kiem` (nhan/nc_tu_lai.hieu_chuan)*" % ST.bay_gio(), "",
             "Quy trinh TU LAI (khong LLM) chay tron ven tren chuoi TONG_HOP biet truoc edge "
             "(`nhan/nc_du_lieu.KICH_BAN`). Hieu chuan HAI chieu: tim ra edge that, KHONG DAT gi "
             "tren nhieu va tren bay chi phi.", "",
             "## 1. Tu lai tron ven (tim quy luat -> mo xe -> quet -> xac nhan -> niem phong)", "",
             "| chuoi | edge sau phi | luat qua null | ket cuc | chi tiet | danh gia | giay |",
             "|---|---|---:|---|---|---|---:|"]
        for k in ket:
            L.append("| %s | %s | %s | %s | %s | %s | %.0f |" % (
                k["ma"], "co" if k["co_edge_that"] else "KHONG", k["so_luat_qua_null"],
                k["ket_cuc"], ", ".join(k["ket"]) or "-", k["danh_gia"], k["giay"]))
        L += ["", "**%d dung · %d chua ket luan · %d sai** · bao dong gia %d" % (
            tom["dung"], tom["chua_ket_luan"], tom["sai"], tom["bao_dong_gia"]), "",
            "## 2. Hoc tu lenh dung/sai (mo xe he goc -> chay lai he da loc tren xac_nhan)", "",
            "| chuoi | edge | bo loc tim ra | p_null | kv goc xn (bps) | kv loc xn (bps) | "
            "%/nam loc xn (DD<80%) | danh gia |", "|---|---|---|---:|---:|---:|---:|---|"]
        for d in hl:
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                d["ma"], "co" if d["co_edge_that"] else "KHONG", d.get("bo_loc") or "-",
                d.get("p_null"), d.get("kv_goc_xn", "-"), d.get("kv_loc_xn", "-"),
                d.get("cagr_loc_xn", "-"), "DUNG" if d["dung"] else "SAI"))
        if bd:
            L += ["", "## 3. Ti le bao dong gia cua tim_quy_luat tren %d hat NHIEU THUAN" % bd["so_hat"],
                  "", "p_null <= 0,05: **%.1f%%** (ky vong ~5%%) · p_null <= 0,10: **%.1f%%** (ky vong ~10%%)"
                  % (100 * bd["ty_le_p_le_0_05"], 100 * bd["ty_le_p_le_0_10"]), "",
                  "p tot nhat tung hat (sap xep): %s" % bd["p_tot_nhat"]]
        if cs:
            L += ["", "## 4. Cong suat: DO TIM RONG vs GIA THUYET CO CHU DICH (edge yeu, %d hat "
                  "HOI_QUY_YEU)" % cs["so_hat"], "",
                  "| cach | phat hien | bao dong gia tren NHIEU cung hat |", "|---|---:|---:|",
                  "| do tim rong (`tim_quy_luat`, ~3.000 dieu kien, p_null <= 0,05) | %d/%d | xem muc 3 |"
                  % (cs["do_tim_rong_phat_hien"], cs["so_hat"]),
                  "| mot gia thuyet co chu dich (1 phep thu, t > 1,645) | %d/%d | %d/%d |"
                  % (cs["co_chu_dich_phat_hien"], cs["so_hat"],
                     cs["co_chu_dich_bao_dong_gia_tren_nhieu"], cs["so_hat"]), "",
                  "Doc: cung mot edge, cung du lieu. Moi dieu kien them vao cuoc do tim nang NGUONG "
                  "cho moi dieu kien khac. Gia tri cua nha nghien cuu (AI hay nguoi) nam o viec dat "
                  "IT gia thuyet co co so - khong phai quet nhieu hon."]
        if cg:
            mot = next(iter(cg.values()))
            L += ["", "## 5. Cong ba doan theo tieu chi chu du an (co lai + maxDD < 80%)", "",
                  "Giao thuc cua AI: chi dua sang doan sau cai DAT o doan truoc. Chuoi KHONG edge: "
                  "y tuong NGAU NHIEN (%d hat x %d moi khung). Chuoi CO edge: mot gia thuyet co chu "
                  "dich moi hat (%d hat). D1 la truong hop XAU NHAT: phi nho so voi nhieu mot nen."
                  % (mot["so_hat"], mot["so_y_moi_hat"], mot["so_hat"]), "",
                  "| khung | chuoi | y tuong | chua do duoc | DAT kham pha | DAT xac nhan | DAT niem "
                  "phong | nhan KHONG hon moc | nhan BETA | mot trong hai |",
                  "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
            for kh, g in cg.items():
                for nhom in ("khong_edge", "co_edge"):
                    for kb, v in g[nhom].items():
                        L.append("| %s | %s (%s) | %d | %d | %d | %d | **%d (%.1f%%)** | %d | %d | %d |" % (
                            kh, kb, "khong edge" if nhom == "khong_edge" else "co edge", v["y_tuong"],
                            v["chua_do_duoc"], v["qua_kham_pha"], v["qua_xac_nhan"],
                            v["dat_niem_phong"], 100 * v["ty_le_dat_niem_phong"],
                            v["dat_mang_nhan_khong_hon_moc"], v["dat_mang_nhan_beta"],
                            v["dat_mang_nhan_beta_hoac_moc"]))
            L += ["", "Doc: cong nay chi hoi \"co lai khong\" - no KHONG loc may man, va KHONG loc "
                  "beta. Tren chuoi troi nhu chi so (BETA), he nghieng mua lot ba doan vi that su co "
                  "lai; cai canh la nhan KHONG hon moc / BETA (cot cuoi nen bang cot DAT). Tren nhieu "
                  "khong troi, phi chan gan het. AI thu N y tuong thi ky vong ~N x ti le o cot DAT "
                  "cai DAT gia - vi vay niem phong ghi so phep thu cua dong gia thuyet va Sharpe "
                  "giam phat: doc chung TRUOC khi tin mot DAT."]
        f = LAB / "reports" / "NC_HIEU_CHUAN.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("\n".join(L) + "\n", encoding="utf-8")
        tom["bao_cao"] = str(f.relative_to(LAB))
    return tom


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("python -m nhan.nc_tu_lai <MA> [KHUNG] [--khong-niem-phong]\n"
              "python -m nhan.nc_tu_lai kiem [SO_HAT]  # hieu chuan hai chieu tren chuoi co dap an;\n"
              "                                        # SO_HAT > 0: them do bao dong gia + cong suat")
        return 0
    if argv[0] == "kiem":
        so_hat = int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else 0
        r = hieu_chuan(so_hat_bao_dong=so_hat, so_hat_cong_suat=8 if so_hat else 0)
        print(json.dumps({k: v for k, v in r.items() if k not in ("chi_tiet", "hoc_tu_lenh")},
                         ensure_ascii=False, default=str))
        return 0 if r["sai"] == 0 else 1
    ma = argv[0]
    khung = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "H4"
    r = chay(ma, khung, mo_niem_phong="--khong-niem-phong" not in argv)
    print(r["tom_tat"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
