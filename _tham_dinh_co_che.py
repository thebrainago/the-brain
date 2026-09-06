# -*- coding: utf-8 -*-
"""_tham_dinh_co_che.py - CONG `co_che` CHI CHAN DUOC SU VANG MAT, KHONG CHAN
DUOC SU RONG.

## VAN DE

06/09/2026, `_dien_co_che.py` hoi LLM lay cau "vi sao co nguoi tra tien" cho 129
muc thieu; 48 cau qua duoc `kiem_khai_bao` va vao kho. Doc lai thi vai cau la
dien lai chinh luat bang tu ngu ve nguoi:

    RSI Buy -> "Nha dau tu gia tri ... bi kich hoat lenh mua khi gia cham vung
                qua ban, buoc ho phai gom hang..."

Do khong phai ly do kinh te. Do la cau "mua khi RSI thap" viet dai ra. Cong
`kiem_khai_bao` chi do DO DAI (>= 25 ky tu) nen no cho qua het.

Neu de nguyen, cong `co_che` tro thanh san khau: moi co che deu co mot cau van
hoa, va ta mat chinh bo loc dang muon giu. Te hon nua: 48 cau nay do MAY viet,
nen tin vao chung la tin vao chinh minh mot vong.

## CACH THAM DINH: HOI LAI, VOI RUBRIC VA THIEN LECH VE PHIA BAC

Khong xay bo do cu phap - "co tu 'quy' va tu 'buoc'" thi ca 48 cau deu dat, do
dung la cach chung duoc viet ra. Thay vao do hoi mot luot DOC LAP: dua cau VA
luat, hoi *"cau nay noi mot ly do kinh te, hay chi dien lai luat?"*, kem rubric
va lenh **nghi ngo thi BAC**.

Day la cho LLM lam duoc that: phan biet "ai bi ep ban va vi sao" voi "gia thap
thi co nguoi mua" la viec doc hieu, khong phai viec dem tu.

Bien phap chong tu khen: luot tham dinh KHONG duoc thay ten co che va KHONG
duoc biet cau do tu dau ra. No chi thay (luat, cau).

Cau bi BAC thi truong `co_che` bi GO khoi kho - quay ve dung trang thai truoc
06/09, tuc co che do bi cong chan khoi be mat. Khong xoa co che: no van la bang
chung ve mot cho ngu phap con thieu.

Chay: python _tham_dinh_co_che.py [--that] [--lo 8]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import ngu_phap as NP     # noqa: E402
from nhan import tri_tue as TT      # noqa: E402

LAB = Path(__file__).resolve().parent
DAU_LLM = "llm_2026_09_06"

HE_THONG = ("Ban la nguoi phan bien mot phong nghien cuu dinh luong. Viec cua "
            "ban la BAC nhung ly do rong. Nghi ngo thi bac.")


def can_tham_dinh(kho: list[dict]) -> list[dict]:
    return [c for c in kho if c.get("co_che_nguon") == DAU_LLM]


def _tom_luat(spec: dict) -> str:
    """Luat, viet gon, KHONG kem ten co che - xem docstring."""
    def _th(t):
        if not isinstance(t, dict):
            return str(t)
        if "hang" in t:
            return str(t["hang"])
        cb = t.get("chi_bao", "?")
        p = [str(v) for k, v in t.items()
             if k not in ("chi_bao", "cua") and not isinstance(v, dict)]
        s = cb + ("(" + ",".join(p) + ")" if p else "")
        return s + ("[" + _th(t["cua"]) + "]" if isinstance(t.get("cua"), dict) else "")

    ve = [f"{_th(d.get('trai'))} {d.get('phep', '>')} {_th(d.get('phai'))}"
          for d in (spec.get("vao") or []) if isinstance(d, dict)]
    ra = [f"{_th(d.get('trai'))} {d.get('phep', '>')} {_th(d.get('phai'))}"
          for d in (spec.get("ra") or []) if isinstance(d, dict)]
    t = ("MUA" if int(spec.get("chieu", 1) or 1) > 0 else "BAN")
    s = f"{t} khi: " + " VA ".join(ve)
    if ra:
        s += " | thoat khi: " + " HOAC ".join(ra)
    s += f" | giu {spec.get('giu', 1)} nen"
    return s


def _nhac(lo: list[tuple[int, dict]]) -> str:
    muc = [json.dumps({"id": i, "luat": _tom_luat(c), "cau": c.get("co_che")},
                      ensure_ascii=False) for i, c in lo]
    return """Duoi day la %d cap (LUAT giao dich, CAU giai thich). Voi tung cap,
phan xu: cau do co noi mot LY DO KINH TE that su khong, hay no chi dien lai
chinh cai luat bang tu ngu ve con nguoi?

DAT ("that") khi cau chi ra duoc mot ben doi ung CU THE va mot RANG BUOC ep ho
giao dich o trang thai do - rang buoc ton tai doc lap voi cai luat:
  vi du dat: "quy chi so phai mua lai co phieu vao ngay tai can bang du gia da
  cao, vi ho bi rang buoc bam sat chi so chu khong duoc chon gia"
  vi du dat: "nguoi ban quyen chon phai phong ve dong khi gia vuot diem hoa
  von, va ho mua bang moi gia vi lo cua ho khong co tran"

BAC ("rong") khi cau chi la chinh luat mac ao:
  - "nha dau tu bi kich hoat lenh mua khi gia cham vung qua ban" -> BAC, day la
    "mua khi RSI thap" viet dai ra.
  - "cac quy theo xu huong buoc phai mua khi gia pha dinh" -> BAC, day la dinh
    nghia cua chinh tin hieu.
  - "nguoi ban can thanh khoan gap" ma khong noi VI SAO ho can gap o dung trang
    thai do -> BAC.
  - Ly do dung cho MOI luat (ai cung so mat tien, ai cung tham) -> BAC.

Phep thu nhanh: **xoa cau di, doc luat, roi doc lai cau. Cau co them thong tin
nao ma luat khong co khong?** Khong co thi BAC.

Nghi ngo thi BAC. Ty le bac cao la ket qua binh thuong va co ich.

CAP:
%s

Tra ve JSON: {"phan_xu": {"<id>": {"ket": "that"|"rong", "vi_sao": "<toi da 15 tu>"}}}""" % (
        len(lo), "\n".join(muc))


def chay(lo_size: int = 8, that: bool = False) -> dict:
    kho = NP.doc_kho()
    can = can_tham_dinh(kho)
    print("kho %d co che, %d cau do LLM viet can tham dinh" % (len(kho), len(can)))
    if not can:
        return {"can": 0}

    xu: dict = {}
    danh_so = list(enumerate(can))
    so_goi = 0
    for i in range(0, len(danh_so), lo_size):
        lo = danh_so[i:i + lo_size]
        kq = TT.hoi_json(_nhac(lo), HE_THONG, bo_qua_han_muc=True)
        so_goi += 1
        if kq.get("bo_qua"):
            print("  dung o lo %d: %s" % (i // lo_size + 1, kq["bo_qua"]))
            break
        d = (kq.get("json") or {}).get("phan_xu") or {}
        if not d:
            print("  lo %d: khong doc duoc JSON (%s)"
                  % (i // lo_size + 1, kq.get("loi") or kq.get("loi_phan_tich")))
            continue
        xu.update({str(k): v for k, v in d.items()})
        print("  lo %d/%d: %d phan xu" % (i // lo_size + 1,
                                          (len(danh_so) + lo_size - 1) // lo_size,
                                          len(d)))

    theo_ten = {c["ten"]: c for c in kho}
    giu, bac, chua = [], [], []
    for i, c in danh_so:
        v = xu.get(str(i)) or {}
        ket = str(v.get("ket", "")).lower()
        if ket == "that":
            giu.append((c["ten"], v.get("vi_sao", "")))
        elif ket == "rong":
            bac.append((c["ten"], v.get("vi_sao", ""), c.get("co_che", "")))
            # GO cau, khong xoa co che: no van la bang chung ve cho ngu phap
            # con thieu, va cong se chan no khoi be mat nhu truoc 06/09.
            theo_ten[c["ten"]].pop("co_che", None)
            theo_ten[c["ten"]].pop("co_che_nguon", None)
        else:
            chua.append(c["ten"])

    print("\n%d goi -> GIU %d · BAC %d · chua phan xu %d"
          % (so_goi, len(giu), len(bac), len(chua)))
    print("\nGIU:")
    for t, v in giu[:12]:
        print("  %-34s %s" % (t[:34], str(v)[:70]))
    print("\nBAC:")
    for t, v, _ in bac[:12]:
        print("  %-34s %s" % (t[:34], str(v)[:70]))

    if that and bac:
        NP.luu_kho(kho)
        print("\nda go %d cau khoi kho" % len(bac))
    elif not that:
        print("\n(chua ghi - them --that)")

    ra = {"can": len(can), "giu": len(giu), "bac": len(bac), "chua": len(chua),
          "so_goi": so_goi,
          "ten_giu": [t for t, _ in giu],
          "ten_bac": [{"ten": t, "vi_sao": v, "cau": c} for t, v, c in bac]}
    (LAB / "reports" / "THAM_DINH_CO_CHE.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    return ra


def main() -> int:
    lo = 8
    if "--lo" in sys.argv:
        lo = int(sys.argv[sys.argv.index("--lo") + 1])
    chay(lo, "--that" in sys.argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
