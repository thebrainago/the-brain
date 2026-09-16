# -*- coding: utf-8 -*-
"""bang_he.py - BANG CAC HE DA QUA CONG. Mat xich cuoi cung, va no dang thieu.

## VI SAO CO FILE NAY

Chu du an 13/09/2026: *"Tong the he thong dang chua lam duoc gi kia."*

Di dem thi khong dung han: he **co** san pham - 9 he rieng biet da qua cong,
trong do `XM_US100CASH.D1.mean_rev` cho CAGR 14,05% / Sharpe 1,16 / sut giam
13,5%. Nhung khong mot cho nao trong he tra loi duoc cau hoi **"hien co may
he da qua cong, moi cai dang bao nhieu"**. No nam rai trong `nao.db`, lan
giua 1.284 dong ket qua, co ca ban trung (15 dong = 9 he).

Mot phong nghien cuu ma khong ai doc duoc danh muc san pham cua no thi nhin
tu ngoai dung la "chua lam duoc gi" - va cai nhin do khong sai, vi khong ai
DUNG duoc thu khong thay.

## BA DIEU BANG NAY PHAI NOI, KHONG DUOC THIEU

  1. **So voi MUA-GIU**, khong chi so tuyet doi. Mot he 8,26%/nam nghe hay
     cho toi khi biet mua-giu cung ma cho 9,97%. Cot `hon_mua_giu` la cot
     quan trong nhat bang.
  2. **Cong nao TRUOT**. Do 13/09: 1/15 dong PASS duoc cap nhan trong khi
     `5_placebo` va `4_alpha_duong_co_y_nghia` deu `false`. Mot dong PASS co
     cong truot phai hien ra, khong duoc gop chung voi PASS sach.
  3. **Tuoi**. Mot he qua cong ba thang truoc, tren the he cong da doi, thi
     khong con la mot phat hien - no la mot ghi chep lich su.

## HAI NGUON, VA KHONG DUOC TRON

Do 13/09/2026: `to_hop` chay 110 phut, chang 4 (holdout) la phep thu duy nhat
co nghia trong ca pheu - va ket qua cua no **khong di dau ca**. No nam trong
`reports/TO_HOP.json`; `vong_day_du._cham_tien` doc ra, IN mot bang roi tra ve
mot cai dict dem. Khong dong nao vao `nao.db`, nen bang nay - cho duy nhat tra
loi "phong nghien cuu dang co gi" - khong bao gio thay chung.

Do la hinh dang that cua *"tong the he thong dang chua lam duoc gi"*: khong
phai khau nao hong, ma la khau cuoi khong noi vao dau nen **khong co gi tich
luy lai**.

Nen bang nay doc HAI nguon va in thanh HAI khoi rieng:

    A. `nao.db/ket_qua`      he da qua CONG THAT (`nhan/cong.py`)
    B. `reports/TO_HOP.json` he qua HOLDOUT CUA PHEU, chua qua cong that

Khong duoc cong hai con so lai. Qua holdout cua pheu la *"canh bac co ky vong
duong do duoc"* (chu cua `cham_diem`), chua phai phat hien. Va khoi B **khong
duoc ghi vao `ket_qua`**: lam vay la chiem suat FDR bang mot phep DO
(memory `do-dac-khong-duoc-chiem-suat-fdr`), va lan sau doc lai se tuong la
xac nhan.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

from nhan import so as SO  # noqa: E402


def _js(x):
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            return {}
    return x or {}


def thu_hoach(chi_pass: bool = True) -> list[dict]:
    """Moi he DA QUA CONG, khu trung, kem so tien va cong nao truot."""
    dk = "WHERE verdict LIKE '%PASS%'" if chi_pass else ""
    rs = SO.nhieu("SELECT id, gt_ma, luc, chi_so, cong, verdict, alpha, "
                  "t_alpha, p_placebo FROM ket_qua %s ORDER BY id DESC" % dk)
    theo_he: dict = {}
    for r in rs:
        ma = str(r["gt_ma"] or "")
        if ma in theo_he:          # da co ban MOI hon (ORDER BY id DESC)
            theo_he[ma]["so_lan_cham"] += 1
            continue
        ci = _js(r["chi_so"])
        he = ci.get("he") or {}
        mg = ci.get("mua_giu_net") or ci.get("mua_giu") or {}
        # SO LENH nam o nhanh `hoat_dong`, khong o `he`. Khong lay dung cho
        # thi cot nay toan `?`, va so lenh la con so quyet dinh mot he co
        # THAT khong: luat cua du an loai thang he duoi 2 lenh/tuan, va
        # `dap_quan_tri.so_luat` bo qua ban co duoi 15 lenh.
        hd = ci.get("hoat_dong") or {}
        cp = ci.get("chi_phi") or {}
        cong = _js(r["cong"])
        truot = sorted(k for k, v in cong.items() if v is False)
        theo_he[ma] = {
            "he": ma, "luc": r["luc"], "so_lan_cham": 1,
            "cagr_pct": he.get("cagr_pct"), "sharpe": he.get("sharpe"),
            "calmar": he.get("calmar"), "max_dd_pct": he.get("max_dd_pct"),
            "so_lenh": hd.get("so_lenh"), "so_nam": he.get("so_nam"),
            "lenh_moi_tuan": hd.get("lenh_moi_tuan"),
            "chi_phi_pct": cp.get("tong_pct"),
            "phi_qua_dem_ty_trong": cp.get("phi_qua_dem_ty_trong"),
            "phoi_nhiem": he.get("phoi_nhiem"),
            "mua_giu_cagr": mg.get("cagr_pct"),
            "mua_giu_sharpe": mg.get("sharpe"),
            "alpha": r["alpha"], "t_alpha": r["t_alpha"],
            "cong_truot": truot, "sach": not truot,
        }
    ra = list(theo_he.values())
    for d in ra:
        c, m = d.get("cagr_pct"), d.get("mua_giu_cagr")
        d["hon_mua_giu_cagr"] = (None if c is None or m is None
                                 else round(c - m, 3))
        s, sm = d.get("sharpe"), d.get("mua_giu_sharpe")
        d["hon_mua_giu_sharpe"] = (None if s is None or sm is None
                                   else round(s - sm, 3))
    _danh_ban_trung(ra)
    for d in ra:
        d["cong_tien"] = _cong_tien(d)
    ra.sort(key=_xep_theo_tien)
    return ra


# ---------------------------------------------------------------- G1 (16/09)
#: Nguong lay THANG tu `nhan/cong_ra_tien.py` - khong go lai o day. Do la
#: cach dua CONG THU HAI len duong chay: truoc 16/09 module do MO COI, va he
#: qua la bang nay xep theo Sharpe nen he 0,62%/nam dung dau.
def _nguong():
    from nhan import cong_ra_tien as CRT
    return CRT.MUC_CAGR, CRT.TRAN_DD, CRT.MIN_LENH, CRT.MIN_NAM


def _cong_tien(d: dict) -> dict:
    """Cham mot he bang CAU HOI TIEN, tren chinh so da do. Khong chay lai.

    Day la ban RE cua cong: no dung lai o bon nguong dem duoc. Ban DAY DU
    (`cong_ra_tien.xet`) con do don bay thap nhat dat muc CAGR trong tran sut
    giam, va viec do phai chay lai mo phong - xem `b he --do-lai`.
    """
    muc, tran, min_lenh, min_nam = _nguong()
    c, dd = d.get("cagr_pct"), d.get("max_dd_pct")
    n, nam = d.get("so_lenh"), d.get("so_nam")
    hon = d.get("hon_mua_giu_cagr")
    ly_do = []
    if c is None or c / 100.0 < muc:
        ly_do.append("lai %s < muc %.0f%%/nam" % (_n(c), muc * 100))
    if dd is not None and abs(dd) / 100.0 > tran:
        ly_do.append("sut giam %s vuot tran %.0f%%" % (_n(dd), tran * 100))
    if n is not None and n < min_lenh:
        ly_do.append("%d lenh < %d" % (n, min_lenh))
    if nam is not None and nam < min_nam:
        ly_do.append("%s nam < %.0f" % (_n(nam), min_nam))
    if hon is not None and hon <= 0:
        ly_do.append("KHONG hon mua-giu (%s diem)" % _n(hon))
    return {"dat": not ly_do, "ly_do": ly_do}


def _van_tay(d: dict) -> tuple:
    """Dau van tay RE: bo so da do, lam tron.

    Ban DUNG la hash cua CHUOI VI THE (hai co che khac ten ma vao/ra cung bar
    thi trung) - nhung chuoi do khong nam trong `ket_qua`, phai chay lai moi
    co. Ban nay bat duoc dung cai da thay 16/09: `mat_can_bang_lenh_dong_cua.`
    va `...mac_dinh` trung khit SAU con so tren cung mot ma. Xac suat hai co
    che KHAC nhau trung ca sau la khong dang ke.
    """
    r = lambda x, k=3: None if x is None else round(float(x), k)
    return (str(d.get("he", "")).split(".")[0],      # cung ma
            r(d.get("cagr_pct")), r(d.get("sharpe")), r(d.get("max_dd_pct")),
            r(d.get("calmar")), d.get("so_lenh"))


def _danh_ban_trung(ds: list[dict]) -> None:
    """Danh dau ban trung. KHONG xoa - ban trung la BI DANH cua ban goc."""
    dau: dict[tuple, str] = {}
    for d in sorted(ds, key=lambda x: len(str(x.get("he", "")))):
        vt = _van_tay(d)
        goc = dau.get(vt)
        if goc is None:
            dau[vt] = d["he"]
            d["ban_trung_cua"] = None
        else:
            d["ban_trung_cua"] = goc


def _xep_theo_tien(d: dict):
    """Xep hang theo CAU HOI TIEN, khong theo Sharpe.

    Thu tu: (1) ban trung xuong duoi - no khong phai mot he · (2) hon mua-giu
    bao nhieu DIEM CAGR · (3) Calmar = lai tren moi don vi sut giam. Sharpe bi
    bo khoi khoa xep hang han: no da tung cho he 0,62%/nam dung dau bang.
    """
    return (1 if d.get("ban_trung_cua") else 0,
            -(d.get("hon_mua_giu_cagr") if d.get("hon_mua_giu_cagr") is not None
              else -9),
            -(d.get("calmar") or -9))


def tu_pheu(tep: Path | None = None) -> list[dict]:
    """He QUA HOLDOUT CUA PHEU. Nguon B - xem docstring dau file.

    `dd20_*` = lai %/nam khi quy ca he lan moc ve CUNG ngan sach sut giam 20%.
    `moc_hold` = max(mua-giu, ban-giu, tien mat) tren chinh nua holdout. Nen
    `hon_moc = dd20_hold - moc_hold` la con so TIEN, doc duoc thang.
    """
    tep = tep or (GOC / "reports" / "TO_HOP.json")
    if not tep.exists():
        return []
    try:
        d = json.loads(tep.read_text(encoding="utf-8"))
    except Exception:
        return []
    ra = []
    for r in (d.get("holdout") or []):
        if not r.get("qua_holdout"):
            continue
        dh, mh = r.get("dd20_hold"), r.get("moc_hold")
        ra.append({
            "he": "%s.%s.%s" % (r.get("ma"), r.get("khung"), r.get("co_che")),
            "ma": r.get("ma"), "khung": r.get("khung"),
            "cau_truc": r.get("cau_truc"), "luat": r.get("luat"),
            "dd20_train": r.get("dd20_train"), "dd20_hold": dh,
            "moc_hold": mh, "chan_hold": r.get("chan_hold"),
            "ty_le_hai_nua": r.get("ty_le_hold_tren_train"),
            "hon_moc": (None if dh is None or mh is None
                        else round(dh - mh, 3)),
        })
    ra.sort(key=lambda x: -(x["hon_moc"] if x["hon_moc"] is not None else -9e9))
    return ra


def _khoi_pheu(in_ra, ds: list[dict]) -> None:
    in_ra("")
    in_ra("=" * 96)
    in_ra("QUA HOLDOUT CUA PHEU (chua qua cong that): %d he" % len(ds))
    in_ra("=" * 96)
    if not ds:
        in_ra("  (khong co - chay `python -m nhan.to_hop --khung D1`)")
        return
    in_ra("%-46s %9s %9s %9s %8s %6s"
          % ("he", "dd20 tr", "dd20 hd", "moc hd", "hon moc", "chan"))
    for d in ds[:25]:
        in_ra("  %-44s %9s %9s %9s %8s %6s"
              % (d["he"][:44], _n(d["dd20_train"]), _n(d["dd20_hold"]),
                 _n(d["moc_hold"]), _n(d["hon_moc"]),
                 d["chan_hold"] if d["chan_hold"] is not None else "?"))
    if len(ds) > 25:
        in_ra("  ... con %d dong nua trong reports/TO_HOP.json" % (len(ds) - 25))
    in_ra("")
    in_ra("`dd20` = lai %/nam khi quy ve cung ngan sach sut giam 20%. `tr`/`hd` "
          "= nua chon / nua kiem.")
    in_ra("`moc hd` = max(mua-giu, ban-giu, tien mat) tren CHINH nua kiem. "
          "`hon moc` am nghia la thua moc.")
    in_ra("CAC DONG NAY CHUA QUA `nhan/cong.py` - la canh bac co ky vong duong "
          "do duoc, chua phai phat hien.")


def bang(in_ra=print, chi_pass: bool = True) -> dict:
    ds = thu_hoach(chi_pass)
    sach = [d for d in ds if d["sach"]]
    trung = [d for d in ds if d.get("ban_trung_cua")]
    rieng = [d for d in ds if not d.get("ban_trung_cua")]
    tien = [d for d in rieng if d["cong_tien"]["dat"]]
    hon = [d for d in rieng if (d.get("hon_mua_giu_cagr") or -9) > 0]
    muc, tran, min_lenh, min_nam = _nguong()
    in_ra("=" * 100)
    in_ra("HE DA QUA CONG: %d dong = **%d he rieng** + %d ban trung  ·  "
          "%d sach  ·  %d hon mua-giu ve TIEN  ·  **%d qua CONG RA TIEN**"
          % (len(ds), len(rieng), len(trung), len(sach), len(hon), len(tien)))
    in_ra("=" * 100)
    in_ra("%-40s %7s %8s %7s %8s %7s %6s %7s  %s"
          % ("he", "CAGR%", "mua-giu", "hon%", "DD%", "Calmar", "lenh",
             "l/tuan", "cong tien"))
    for d in ds:
        if d.get("ban_trung_cua"):
            dau = "= "
        elif not d["sach"]:
            dau = "! "
        else:
            dau = "  "
        in_ra("%s%-38s %7s %8s %7s %8s %7s %6s %7s  %s"
              % (dau, d["he"][:38],
                 _n(d["cagr_pct"]), _n(d.get("mua_giu_cagr")),
                 _n(d.get("hon_mua_giu_cagr")), _n(d["max_dd_pct"]),
                 _n(d["calmar"]),
                 d["so_lenh"] if d["so_lenh"] is not None else "?",
                 _n(d.get("lenh_moi_tuan")),
                 "DAT" if d["cong_tien"]["dat"] else "-"))
        if d.get("ban_trung_cua"):
            in_ra("      = BAN TRUNG cua `%s` (sau con so trung khit)"
                  % d["ban_trung_cua"])
            continue
        if not d["sach"]:
            in_ra("      ! cong TRUOT: %s" % ", ".join(d["cong_truot"]))
        if not d["cong_tien"]["dat"]:
            in_ra("      - cong tien: %s" % " · ".join(d["cong_tien"]["ly_do"]))
    in_ra("")
    in_ra("XEP THEO TIEN, khong theo Sharpe (sua 16/09). Khoa xep hang:")
    in_ra("  (1) ban trung xuong duoi  (2) hon mua-giu bao nhieu DIEM CAGR")
    in_ra("  (3) Calmar = lai tren moi don vi sut giam")
    in_ra("dau `=` ban trung · `!` co cong that TRUOT")
    in_ra("cot `hon%` = CAGR he TRU CAGR mua-giu CUNG MA. Duong ma moc AM thi "
          "van chi la thang mot moc am.")
    in_ra("cot `cong tien` = 4 nguong cua `nhan/cong_ra_tien.py`: lai >= %.0f%%"
          "/nam · sut giam <= %.0f%% · >= %d lenh · >= %.0f nam · hon mua-giu."
          % (muc * 100, tran * 100, min_lenh, min_nam))
    if not tien:
        in_ra("")
        in_ra(">> KHONG HE NAO QUA CONG RA TIEN. Bang tren la bang cac PHEP DO, "
              "chua phai bang cac he kiem duoc tien.")
    ph = tu_pheu()
    _khoi_pheu(in_ra, ph)
    in_ra("")
    in_ra("TONG: %d he qua CONG THAT (%d sach) + %d he qua HOLDOUT CUA PHEU"
          % (len(ds), len(sach), len(ph)))
    ra = {"so_he": len(ds), "so_he_rieng": len(rieng), "so_ban_trung": len(trung),
          "so_sach": len(sach), "so_hon_mua_giu": len(hon),
          "so_qua_cong_tien": len(tien),
          "he": ds, "so_qua_pheu": len(ph), "qua_pheu": ph}
    (GOC / "reports" / "BANG_HE.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra


def _n(x, nd=2):
    return "?" if x is None else ("%.*f" % (nd, x))


if __name__ == "__main__":
    bang(chi_pass="--het" not in sys.argv)
