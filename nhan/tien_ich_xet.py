# -*- coding: utf-8 -*-
"""tien_ich_xet.py - 58 FILE "TIEN ICH" DANG BI BO: CAI NAO DANG LAY VE?

Chu du an 05/09/2026: *"Boc tach ra se gom chien luoc va cac he thong ho tro.
Luc nay chien luoc thi phai kiem dinh con TIEN ICH THI CAN XEM XEM CAI NAO PHU
HOP DE LAY VE"*.

`nhan/phan_loai_ma.py` xep 58/389 file vao lan `tien_ich` va **bo chung co chu
dich** - chung khong dat lenh, khong co buffer chi bao, khong co lop quan tri.
Do la quyet dinh dung cho khau BOC CO CHE. Nhung "khong co co che" khong co
nghia la "khong dung duoc": dau hieu do duoc tren 58 file do la
`OnTick` 31 · giao dien 19 · `OnChartEvent` 17 - chung la cong cu van hanh.

Va trong so do co dung thu du an dang thieu nhat. Doc thang danh sach ten:

    RealCostSpreadP95LoggerMT5.mq5          ghi spread THAT theo phan vi 95
    Quantora_Spread_Monitor_MT5.mq5         theo doi spread
    spread_lister_current-min-max.mq5       liet ke spread min/max
    RiskPositionSizeCalculator.mq5          tinh khoi luong theo rui ro
    Quantora_Margin_Calculator_MT5.mq5      tinh ky quy

**Nut that lon nhat cua ca du an la CHI PHI DO DUOC**, khong phai thieu co che:
luat bat bien la `cp.do_tin == "KHAI"` thi **khong bao gio PASS**, va tinh den
05/09 chi rieng XM co spread do that. Mot EA ghi spread theo bar chinh la thu
nang `do_tin` tu KHAI len DO cho cac symbol con lai.

## CACH XET - KHONG DE LLM TU NGHI RA NHU CAU

Bang nhu cau lay THANG tu `san_cong_cu.NHU_CAU` (13 muc da viet tay, moi muc co
`vi_sao` / `cam_vao` / `khong_duoc_thay`). Ly do y het ly do o `san_cong_cu`:
*"tim truoc roi moi nghi ra ly do can no thi lan nao cung 'tim thay thu huu
ich', va do la mot dang tu lua minh"*. LLM chi duoc GAN mot file vao mot nhu cau
DA KHAI, hoac tra `null`.

Dau ra la UNG VIEN de nguoi doc, khong phai mot quyet dinh tich hop - cung ranh
gioi mot chieu ma `san_cong_cu` da dat: *"cong cu ngoai duoc lam BAN THI NGHIEM,
khong bao gio lam ONG TOA"*.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

#: Nhu cau THEM, rieng cho ma nguon MQL5 - `san_cong_cu.NHU_CAU` viet cho thu
#: vien Python chay canh day chuyen, khong phu het cai mot EA lam duoc.
NHU_CAU_MQL = {
    "do_chi_phi_that": (
        "Ghi spread / truot gia / phi qua dem THAT theo tung bar hoac tung lenh. "
        "Day la nut that lon nhat cua du an: `do_tin='KHAI'` thi khong bao gio "
        "PASS duoc cong, va den 05/09 chi rieng XM co so do that."),
    "tinh_khoi_luong": (
        "Tinh lot theo rui ro / ky quy / don vi tai khoan (cent vs chuan, "
        "contract size). Du an da sap bay don vi nhieu lan."),
    "xuat_du_lieu": (
        "Xuat bar / tick / bao cao ra file de doi chieu voi Python."),
    "quan_ly_phien_gio": (
        "Xu ly gio server, doi mui gio, moc phien - de co che theo PHIEN chay "
        "dung tren khung noi ngay."),
    "giam_sat_van_hanh": (
        "Theo doi tai khoan dang chay: sut giam, so lenh, canh bao ra ngoai."),
}


def _nhac(ten: str, src: str) -> str:
    nc = "\n".join("  %-20s %s" % (k, v) for k, v in NHU_CAU_MQL.items())
    return f"""Day la mot file ma nguon MQL5 (`{ten}`) da duoc xep loai TIEN ICH:
no khong dat lenh theo tin hieu va khong dinh nghia chi bao. Cau hoi KHONG phai
"no la chien luoc gi", ma: **no co lam duoc mot trong nhung viec duoi day khong?**

NHU CAU CUA DU AN (chi duoc chon trong danh sach nay, hoac null):
{nc}

MA NGUON (rut gon):
```
{src[:9000]}
```

QUY TAC:
- Chi gan khi file THAT SU lam viec do, doc duoc trong ma. Khong chac -> null.
- `muc_do`: "cao" neu no lam dung viec do va lam day du; "vua" neu lam mot phan.
- `lam_gi`: MOT CAU ta chinh xac no ghi/tinh cai gi, bang tieng Viet khong dau.
- `lay_ve_the_nao`: doc mot dong - vd "chay tren MT5 de sinh file CSV spread",
  hoac "doc lai cong thuc roi viet lai bang Python".

Tra ve DUNG mot JSON:
{{"nhu_cau": "do_chi_phi_that" hoac null, "muc_do": "cao",
  "lam_gi": "...", "lay_ve_the_nao": "..."}}"""


def xet_mot(src: str, ten: str = "", model: str = "") -> dict:
    from nhan import tri_tue as TT
    r = TT.hoi_json(_nhac(ten, src), bo_qua_han_muc=True, dung_cache=False,
                    model=model)
    if isinstance(r, dict) and (r.get("loi") or r.get("bo_qua")):
        return {"ten": ten, "chua_do": True,
                "vi_sao": str(r.get("loi") or r.get("bo_qua"))[:90]}
    j = (r or {}).get("json") or r or {}
    nc = j.get("nhu_cau")
    if nc not in NHU_CAU_MQL:
        nc = None                        # khong duoc tu nghi ra nhu cau moi
    return {"ten": ten, "nhu_cau": nc, "muc_do": str(j.get("muc_do") or "")[:8],
            "lam_gi": str(j.get("lam_gi") or "")[:220],
            "lay_ve_the_nao": str(j.get("lay_ve_the_nao") or "")[:220]}


def quet(gioi_han: int = 0, in_ra=print) -> dict:
    import concurrent.futures as cf
    from collections import Counter

    from nhan import phan_loai_ma as PL

    ds = []
    for d in PL._doc_kho_ma():
        if PL.phan_loai_mot(d["src"], d["ten"])["lan"] != PL.TIEN_ICH:
            continue
        ds.append(d)
        if gioi_han and len(ds) >= gioi_han:
            break
    in_ra("XET %d file lan `tien_ich` theo %d nhu cau da khai"
          % (len(ds), len(NHU_CAU_MQL)))
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        ket = list(ex.map(lambda d: xet_mot(d["src"], d["ten"]), ds))

    cd = [k for k in ket if k.get("chua_do")]
    if cd and len(cd) == len(ket):
        in_ra("  !! CA ME KHONG GOI DUOC: %s" % cd[0]["vi_sao"])
        return {"so_file": len(ds), "chua_do": len(cd), "hop": None, "ket": ket}
    hop = [k for k in ket if k.get("nhu_cau")]
    in_ra("  %d/%d file hop mot nhu cau (chua do: %d)"
          % (len(hop), len(ket) - len(cd), len(cd)))
    for k, v in Counter(k["nhu_cau"] for k in hop).most_common():
        in_ra("    %-20s %d" % (k, v))
    for k in sorted(hop, key=lambda z: z.get("muc_do") != "cao")[:12]:
        in_ra("  [%s] %-42s %s" % (k.get("muc_do", "?")[:4], k["ten"][:42],
                                   k["lam_gi"][:70]))
    return {"so_file": len(ds), "chua_do": len(cd), "hop": hop, "ket": ket}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    n = 0
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)
    r = quet(gioi_han=n)
    p = Path(__file__).resolve().parent.parent / "reports" / "tien_ich_xet.json"
    p.write_text(json.dumps(r.get("ket") or [], ensure_ascii=False, indent=1),
                 encoding="utf-8")
    print("-> %s" % p)
