# -*- coding: utf-8 -*-
"""nghi.py - TRU NGHI. Bien thu doc duoc thanh thu kiem dinh duoc, roi HOC TU KET QUA.

Day la mat xich con thieu cua day chuyen. Truoc 16/08 no gay dung o day:

    SEEKER thu 303 tai lieu  ->  17 tai lieu HANG A mo ta co che chua co mau
                             ->  van de `can_mau_moi` mo tu 15/08, khong ai dong
                             ->  QUANTLAB tiep tuc quet dung 14 mau viet tay

Tuc phong lab DOC rat nhieu ma HOC duoc bang khong. Va chieu nguoc lai cung dut:
274 gia thuyet FAIL nhung khong co cho nao ghi lai *vi sao* de lan sau khong
lap lai - moi vong lai bat dau tu con so khong.

BON BUOC MOT VONG:
  1. DOI CHIEU  - doc ket qua cua chinh nhung co che minh de xuat vong truoc.
                  Ca cai bi TU CHOI truoc khi kiem dinh (sai cu phap, nhin
                  truoc, it lenh) lan cai da chay va FAIL.
  2. DOC        - lay tai lieu HANG A/B chua khai thac.
  3. NGHI       - de xuat co che moi bang NGU PHAP (`nhan/ngu_phap.py`), khong
                  phai bang ma. Kem theo `dieu_kien_sai`: cai gi neu quan sat
                  duoc thi co che nay sai.
  4. KIEM       - cu phap -> ty le kich hoat -> PHEP CAT chong nhin truoc.
                  Dat thi vao kho + xep viec cho QUANTLAB. Khong dat thi ghi
                  ly do vao so de vong sau doc lai.

NGUYEN TAC: tru nay KHONG duoc ket luan gi ve tien. No chi de xuat. Moi con so
di qua dung `nhan/cong.py` va dung ngan sach FDR nhu mau viet tay - khong co
duong tat nao cho co che tu de xuat.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import (du_lieu as DL, ket_qua_hoat_dong as KQHD, mau as MAU,
                  ngu_phap as NP, so as SO, tri_tue as TT)

TRU = "NGHI"
LAB = Path(__file__).resolve().parent.parent
REPORTS = LAB / "reports"
TAI_SAN_KIEM = ["EURCAD", "AUDNZD", "US500CASH", "XAUUSDM"]
KHUNG_KIEM = "H4"
SO_DE_XUAT_MOI_VONG = 6


HE_THONG = """Ban la tru NGHI cua mot phong lab dinh luong chay 24/7. Viec cua ban
la de xuat CO CHE co the kiem dinh duoc, khong phai de xuat "chien luoc thang".

Boi canh phai nho:
- Phong lab nay da chay hon 1.700 phep thu va ra 0 chien luoc dung duoc. "Khong
  tim thay" la ket qua binh thuong. De xuat cua ban gan nhu chac chan se FAIL,
  va do khong phai that bai - de xuat te la de xuat KHONG THE KIEM DINH.
- Hai thu duy nhat tung song sot o day deu co dang "A KHI B" (dieu kien kep),
  khong phai nhan to don: IBS bat day chi dung voi chi so chau My va chi sau
  2005; nghieng vi the theo thay doi loi suat 10 nam. Ghep CO DIEU KIEN la toan
  tu sinh loi nhat.
- Chi phi qua dem la chi phi quyet dinh, khong phai spread. Co che nao giu vi
  the nhieu ngay phai giai thich duoc vi sao no bu duoc 5-7%/nam phi giu.
- Co che phai noi duoc AI TRA TIEN va VI SAO ho tra. "Chi bao X cat chi bao Y"
  khong phai co che, do la mo ta hinh ve.

Ban khong duoc viet ma. Ban khai bao bang NGU PHAP JSON duoi day, va trinh
thong dich la thu duy nhat cham vao gia."""


NGU_PHAP_TOM_TAT = """
NGU PHAP (chi duoc dung dung nhung khoa nay):

  co_che = {
    "ten": "<chu_thuong_gach_duoi, duy nhat>",
    "co_che": "<MOT CAU: ai tra tien cho phoi nhiem nay va vi sao>",
    "ho": "quay_ve_trung_binh|xu_huong|pha_vo|lich|phien|bien_dong|dong_tien|vi_mo|khac",
    "chieu": 1 | -1,
    "giu": <so bar giu, 1..500>,
    "vao": [ dieu_kien, ... ],     // VA voi nhau
    "ra":  [ dieu_kien, ... ],     // HOAC; de rong thi ra sau `giu` bar
    "dieu_kien_sai": "<quan sat duoc gi thi co che nay SAI>",
    "nguon": "<url TRONG muc TAI LIEU ma y tuong xuat phat; de RONG neu khong>"
  }

  dieu_kien = {"trai": toan_hang, "phep": "<|<=|>|>=|cheo_len|cheo_xuong",
               "phai": toan_hang}

  toan_hang =
    {"hang": <so>}
    {"chi_bao": "gia", "cot": "open|high|low|close"}
    {"chi_bao": "rsi"|"atr"|"ema"|"sma", "n": <so>}
    {"chi_bao": "ibs"}                       // dong cua nam o dau trong bien do bar
    {"chi_bao": "bien_do"}                   // high - low
    {"chi_bao": "than_nen"}                  // close - open
    {"chi_bao": "khoi_luong"}
    {"chi_bao": "gio"|"ngay_trong_tuan"|"ngay_trong_thang"|"thang"}
    {"chi_bao": "tb"|"do_lech"|"zscore"|"phan_vi"|"doi"|"doi_pct"|"tre"|
                "cao_nhat"|"thap_nhat"|"tuyet_doi", "cua": toan_hang, "n": <so>}

  `phan_vi` = thu hang cua gia tri hien tai trong N bar gan nhat (0..1) - day la
  cach dung de noi "bien dong dang cao" ma khong phai go cung mot nguong tuyet doi.
  `n` LUON la so bar LUI VE QUA KHU. Khong co cach nao viet mot toan hang nhin
  ve tuong lai - dung thu.
"""


# ------------------------------------------------------------------ 1. DOI CHIEU
def doi_chieu() -> dict:
    """Doc ket qua cua chinh cac de xuat vong truoc. Day la du lieu day cua vong nay."""
    ds = SO.nhieu("SELECT * FROM de_xuat ORDER BY id DESC LIMIT 60")
    for d in ds:
        if not d["nhan"]:
            continue
        # co che da duoc nhan -> tim ket qua kiem dinh cua no trong so
        r = SO.nhieu(KQHD.truy_van(
            "k.verdict, COUNT(*) n",
            dieu_kien_them="k.gt_ma LIKE ?",
            nhom_theo="k.verdict",
        ), f"%.{d['ten']}.%")
        if r:
            tong = sum(x["n"] for x in r)
            v = {x["verdict"]: x["n"] for x in r}
            SO.chay("UPDATE de_xuat SET verdict=?, chi_tiet=?, trang_thai='DA_KIEM' "
                    "WHERE id=?", json.dumps(v, ensure_ascii=False),
                    f"{tong} phep thu", d["id"])
            d["verdict"] = json.dumps(v, ensure_ascii=False)
    tu_choi = [d for d in ds if not d["nhan"]]
    da_kiem = [d for d in ds if d["nhan"] and d.get("verdict")]
    cho = [d for d in ds if d["nhan"] and not d.get("verdict")]
    return {"tong": len(ds), "bi_tu_choi": len(tu_choi), "da_kiem": len(da_kiem),
            "dang_cho": len(cho),
            "_tu_choi": tu_choi[:10], "_da_kiem": da_kiem[:12]}


# ---------------------------------------------------------------------- 2. DOC
def doc_tai_lieu(n: int = 8) -> list[dict]:
    """Tai lieu HANG A/B con nong. Tra ca NOI DUNG THAT neu da keo ve - de NGHI
    doc duoc chu khong chi nhin tieu de/tom tat (neu chi nhin tom tat thi moi
    "co che" sinh ra la cua LLM, khong phai cua tai lieu)."""
    rows = SO.nhieu(
        "SELECT t.id, t.tieu_de, t.tom_tat, t.url, t.tu_khoa, t.diem, "
        "       nd.van_ban, nd.so_ky_tu "
        "FROM tai_lieu t "
        "LEFT JOIN noi_dung nd ON nd.tai_lieu_id = t.id "
        "WHERE t.tu_khoa IN('A','B') "
        "ORDER BY (nd.so_ky_tu IS NOT NULL AND t.da_khai_thac=0) DESC, "
        "t.da_khai_thac ASC, t.diem DESC, t.id DESC LIMIT ?", n)
    for r in rows:
        vb = r.pop("van_ban", None) or ""
        r["van_ban"] = vb[:12000]
        r["co_noi_dung"] = bool(vb)
    return rows


# --------------------------------------------------------------------- 3. NGHI
def _nhac(dc: dict, tl: list[dict]) -> str:
    da_co = sorted(set(list(MAU.MAU) + [c.get("ten") for c in NP.doc_kho()]))
    p = [NGU_PHAP_TOM_TAT, "",
         "== CO CHE DA CO (KHONG duoc de xuat lai, ke ca doi ten) ==",
         ", ".join(str(x) for x in da_co if x), ""]

    if dc["_tu_choi"]:
        p += ["== DE XUAT CUA CHINH BAN DA BI TU CHOI TRUOC KHI KIEM DINH ==",
              "(day la loi cu phap/thiet ke cua ban - dung lap lai)"]
        for d in dc["_tu_choi"]:
            p.append(f"- `{d['ten']}`: {str(d['ly_do_tu_choi'])[:200]}")
        p.append("")
    if dc["_da_kiem"]:
        p += ["== DE XUAT DA CHAY QUA DAY CHUYEN VA CO KET QUA ==",
              "(FAIL la binh thuong. Doc de biet HUONG nao da can, dung dao lai)"]
        for d in dc["_da_kiem"]:
            p.append(f"- `{d['ten']}` (ho {d['ho']}): {d['verdict']} | co che: "
                     f"{str(d['co_che'])[:120]}")
        p.append("")
    if tl:
        p += ["== TAI LIEU MOI THU DUOC (nguon y tuong, KHONG phai bang chung) ==",
              "(Neu de xuat xuat phat tu mot tai lieu, ghi `nguon` = DUNG url cua no)"]
        da_them_nd = 0
        for t in tl:
            p.append(f"- [{t['tu_khoa']}] {t['tieu_de'][:150]}")
            p.append(f"    url: {t.get('url') or '(khong co)'}")
            if t.get("tom_tat"):
                p.append(f"    tom_tat: {str(t['tom_tat'])[:320]}")
            vb = t.get("van_ban") or ""
            if vb and da_them_nd < 3:
                p.append(f"    NOI DUNG (doc ky truoc khi de xuat):\n    {vb[:6000]}")
                da_them_nd += 1
        p.append("")

    p += [
        f"== VIEC CUA BAN ==",
        f"De xuat toi da {SO_DE_XUAT_MOI_VONG} co che MOI. Tra ve JSON:",
        '  {"de_xuat": [ <co_che>, ... ], "ly_do_chon": "<mot doan ngan>"}',
        "",
        "Rang buoc - de xuat vi pham se bi may tu choi truoc khi den nguoi doc:",
        "  1. `co_che` phai noi AI TRA TIEN. 'RSI duoi 30 thi mua' bi tu choi.",
        "  2. Uu tien dang 'A KHI B' - it nhat 2 dieu kien trong `vao`, trong do",
        "     mot cai la DIEU KIEN CHE DO (dung `phan_vi` cua bien dong / khoi",
        "     luong / do dai xu huong) chu khong phai hai lan cung mot y.",
        "  3. Ty le kich hoat phai nam trong khoang 0,5% - 40% so bar. Duoi thi",
        "     khong bao gio du lenh de ket luan; tren thi la mua-giu tra hinh.",
        "  4. `giu` lon (> 20 bar) phai giai thich duoc phi qua dem trong `co_che`.",
        "  5. Khong dat nguong tuyet doi cho dai luong co don vi (gia, ATR, khoi",
        "     luong) - dung `phan_vi` hoac `zscore`.",
        "  6. Moi de xuat ghi `nguon`: neu y tuong xuat phat TU MOT TAI LIEU trong",
        "     danh sach ben tren, dat `nguon` = DUNG url cua tai lieu do. Neu la",
        "     y tuong cua rieng ban (khong tu tai lieu nao) thi de `nguon` RONG.",
        "     Dung bia URL - may se loai moi nguon khong khop danh sach.",
    ]
    return "\n".join(p)


def de_xuat_moi(dc: dict, tl: list[dict], ep: bool = False) -> dict:
    kq = TT.hoi_json(_nhac(dc, tl), HE_THONG, bo_qua_han_muc=ep, dung_cache=False)
    if kq.get("json"):
        (REPORTS / "nghi_de_xuat_tho.json").write_text(
            json.dumps(kq["json"], ensure_ascii=False, indent=1), encoding="utf-8")
    return kq


# --------------------------------------------------------------------- 4. KIEM
def _df_kiem():
    for ma in TAI_SAN_KIEM:
        try:
            df = DL.nap(ma, KHUNG_KIEM)
            if len(df) > 3000:
                return ma, df
        except Exception:
            continue
    return None, None


def kiem_va_nhan(ds: list[dict], tl: list[dict] | None = None) -> dict:
    """Cho tung de xuat di qua ba cua: cu phap -> ty le kich hoat -> phep cat."""
    # CHONG BIA NGUON: chi giu `nguon` khi no la mot url that trong danh sach
    # tai lieu da dua cho LLM. Nguon bia bi rong ve "tu kien thuc san co" - khong
    # bao gio lam gia thuoc do "hoc tu tai lieu".
    hop_le = {str(t.get("url") or "") for t in (tl or []) if t.get("url")}
    ma_kiem, df = _df_kiem()
    nhan, tu_choi = [], []
    for spec in ds[:SO_DE_XUAT_MOI_VONG * 2]:
        ten = str(spec.get("ten") or "").strip().lower().replace(" ", "_")
        if not ten:
            continue
        spec["ten"] = ten
        dks = spec.pop("dieu_kien_sai", "") or spec.get("dieu_kien_sai", "")
        nguon = str(spec.get("nguon") or "")
        spec["nguon"] = nguon if nguon in hop_le else ""
        r = NP.them_co_che(spec, df)
        ghi_de_xuat(spec, r, dks)
        if r["nhan"]:
            nhan.append(ten)
            # KHANG DINH: mot cau co the sai. Dieu kien sai duoc ghi TRUOC khi
            # chay, de sau nay khong ai dien giai lai ket qua cho vua y minh.
            SO.chay("INSERT INTO khang_dinh(gt_ma,hang,luc,dieu_kien_sai,trang_thai) "
                    "VALUES(?,?,?,?,'CHO_KIEM')",
                    ten, spec.get("ho", "khac"), SO.bay_gio(), dks[:600])
            SO.them_viec("QUANTLAB", "kham_pha_theo_mau",
                         {"mau": ten, "nguon_tai_lieu": spec.get("nguon", "tru NGHI")},
                         uu_tien=2)
        else:
            tu_choi.append({"ten": ten, "ly_do": r["ly_do"]})
    return {"tai_san_kiem": ma_kiem, "nhan": nhan, "tu_choi": tu_choi}


def ghi_de_xuat(spec: dict, r: dict, dieu_kien_sai: str = "") -> None:
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT OR IGNORE INTO de_xuat(luc,tru,ten,ho,co_che,dsl,nguon,nhan,"
            "ly_do_tu_choi,trang_thai) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (SO.bay_gio(), TRU, spec.get("ten"), spec.get("ho"),
             (spec.get("co_che") or "")[:600],
             json.dumps(spec, ensure_ascii=False)[:4000],
             spec.get("nguon", ""), int(bool(r.get("nhan"))),
             "; ".join(r.get("ly_do") or [])[:600],
             "DA_NHAN" if r.get("nhan") else "TU_CHOI"))


# ------------------------------------------------------------------ MOT LUOT
def mot_luot(ep: bool = False) -> dict:
    SO.nhip_tim(TRU, "chay")
    t0 = time.time()
    NP.nap_vao_mau()

    dc = doi_chieu()
    tl = doc_tai_lieu()
    kq = de_xuat_moi(dc, tl, ep=ep)

    ra = {"doi_chieu": {k: v for k, v in dc.items() if not k.startswith("_")},
          "tai_lieu_doc": len(tl), "duong": kq.get("duong")}
    if kq.get("bo_qua"):
        ra["bo_qua"] = kq["bo_qua"]
        SO.nhip_tim(TRU, "nghi", {"bo_qua": kq["bo_qua"], "cho_giay": 3600})
        return ra
    if not kq.get("json"):
        ra["loi"] = kq.get("loi") or kq.get("loi_phan_tich") or "khong co JSON"
        SO.nhip_tim(TRU, "nghi", {"loi": ra["loi"][:120], "cho_giay": 1800})
        return ra

    ds = kq["json"].get("de_xuat") or []
    kiem = kiem_va_nhan(ds, tl)
    ra.update({"de_xuat_nhan_duoc": len(ds), **kiem,
               "co_nguon_tu_tai_lieu": len([d for d in ds if d.get("nguon")]),
               "ly_do_chon": str(kq["json"].get("ly_do_chon", ""))[:400]})

    n_mau = NP.nap_vao_mau()
    ra["mau_dang_co"] = len(MAU.MAU)
    SO.ghi_chi_so("nghi_de_xuat", len(ds),
                  {"nhan": len(kiem["nhan"]), "tu_choi": len(kiem["tu_choi"])})
    SO.ghi_su_kien(TRU, "de_xuat_co_che",
                   {"nhan": kiem["nhan"], "tu_choi": [t["ten"] for t in kiem["tu_choi"]]})
    if kiem["nhan"]:
        SO.dong_van_de("can_mau_moi",
                       f"tru NGHI da bien {len(kiem['nhan'])} co che thanh mau kiem dinh duoc")

    viet_bao_cao(ra, dc, kiem)
    SO.nhip_tim(TRU, "nghi", {"nhan": len(kiem["nhan"]), "cho_giay": 5400,
                              "giay": round(time.time() - t0, 1)})
    return ra


def viet_bao_cao(ra: dict, dc: dict, kiem: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    d = ["# TRU NGHI - bien kien thuc thanh co che kiem dinh duoc",
         f"*{SO.bay_gio()}*", "",
         "> Tru nay KHONG ket luan gi ve tien. No chi de xuat. Moi con so van di",
         "> qua `nhan/cong.py` va van ton ngan sach FDR nhu mau viet tay.", "",
         "## 1. Doi chieu vong truoc",
         f"- De xuat da ghi so: **{dc['tong']}** "
         f"(bi tu choi truoc kiem dinh {dc['bi_tu_choi']}, "
         f"da co ket qua {dc['da_kiem']}, dang cho {dc['dang_cho']})"]
    if dc["_da_kiem"]:
        d += ["", "| Co che | Ho | Ket qua |", "|---|---|---|"]
        for x in dc["_da_kiem"]:
            d.append(f"| `{x['ten']}` | {x['ho']} | {x['verdict']} |")
    d += ["", "## 2. Vong nay",
          f"- Doc {ra.get('tai_lieu_doc', 0)} tai lieu hang A/B",
          f"- Nhan duoc {ra.get('de_xuat_nhan_duoc', 0)} de xuat, "
          f"**qua ba cua kiem: {len(kiem.get('nhan') or [])}**",
          f"- Trong do {ra.get('co_nguon_tu_tai_lieu', 0)} co nguon truy nguyen",
          f"  ve tai lieu (5-6 truoc day luon la 0 - moi co che la cua LLM).",
          f"- Tai san dung de kiem: {kiem.get('tai_san_kiem')}"]
    if kiem.get("nhan"):
        d += ["", "### Da nhan vao kho co che"] + [f"- `{t}`" for t in kiem["nhan"]]
    if kiem.get("tu_choi"):
        d += ["", "### Bi tu choi (va vi sao - vong sau se doc lai muc nay)"]
        for t in kiem["tu_choi"]:
            d.append(f"- `{t['ten']}`: {'; '.join(str(x) for x in t['ly_do'])[:300]}")
    d += ["", "## 3. Ba cua kiem moi de xuat phai qua", "",
          "1. **Cu phap** - dung ngu phap khai bao, khong co toan hang nhin truoc.",
          "2. **Ty le kich hoat** - trong khoang 0,5%..98% so bar. Duoi thi khong",
          "   bao gio du lenh; tren thi la mua-giu tra hinh.",
          "3. **Phep cat** - tin hieu tai bar t phai giong het du co biet cac bar",
          "   sau t hay khong, do tren 40 moc cat ngau nhien. Bai kiem nay da tu",
          "   chung minh la nhay (chen ro ri co y -> bat duoc)."]
    (REPORTS / "NGHI.md").write_text("\n".join(d), encoding="utf-8")


if __name__ == "__main__":
    SO.khoi_tao()
    print(json.dumps(mot_luot(ep="--ep" in sys.argv), ensure_ascii=False,
                     indent=1, default=str)[:6000])
