# -*- coding: utf-8 -*-
"""_dien_co_che.py - 169/540 CO CHE TRONG KHO KHONG QUA NOI CONG CUA CHINH NO.

## PHAT HIEN (06/09/2026)

Chay `ngu_phap.kiem_khai_bao` len tung muc trong kho:

    thieu han truong `co_che`            148
    co `co_che` nhung ngan hon mot cau    16
    ve dieu kien hien nhien                5
    ----
    khong qua duoc cong                  169 / 540

`them_co_che` DOI truong `co_che` - mot cau noi ai la ben doi ung va vi sao ho
buoc phai giao dich o trang thai do. Dó khong phai trang tri: no la thu duy
nhat phan biet mot co che voi mot mau hinh tim thay trong du lieu. Ma 169 muc
nay chua bao gio bi hoi, vi chung vao kho qua **cua sau** - duong LLM ghi thang
vao file JSON, bo qua `them_co_che` (ban giao 05/09 da ke ten lo hong nay).

Va chung KHONG nam im: `nap_vao_mau` + `loc_co_che.loc` khong goi
`kiem_khai_bao`, nen ca 169 dang chay tren be mat nhu moi co che khac.

## VI SAO DUNG LLM O DAY, VA GIOI HAN CUA NO

Cau "vi sao co nguoi tra tien" khong suy ra duoc tu dieu kien bang luat - no
la kien thuc ve thi truong. Day dung la khau LLM lam duoc.

Nhung neu de LLM bia mot cau nghe hop ly cho MOI co che thi cong tro thanh san
khau: 148 cau van hoa se qua het, va ta mat chinh cai bo loc dang muon giu.
Nen loi nhac bat buoc mot loi thoat: **`CHUA_BIET_LY_DO`**. Cai nao LLM khong
biet thi giu nguyen trang thai chua co `co_che`, va bao ra - do la danh sach
co che dang cho **BO**, khong phai danh sach cho dien not.

Ty le `CHUA_BIET_LY_DO` la mot phep do co ich cua chinh kho: no noi bao nhieu
phan cua kho la co che that va bao nhieu la mau hinh nhat duoc.

Chay: python _dien_co_che.py [--that] [--lo 12] [--toi-da 200]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import ngu_phap as NP     # noqa: E402
from nhan import tri_tue as TT      # noqa: E402

LAB = Path(__file__).resolve().parent
KHONG_BIET = "CHUA_BIET_LY_DO"

HE_THONG = ("Ban la mot nha nghien cuu dinh luong hoai nghi. Ban khong bia ly "
            "do kinh te; khong biet thi ban noi la khong biet.")


def can_dien(kho: list[dict]) -> list[dict]:
    """Muc nao truot cong CHI vi truong `co_che`.

    Muc truot vi ly do KHAC (ve hien nhien, ho sai) khong thuoc viec nay - dien
    mot cau giai thich cho mot dieu kien vo nghia chi lam no kho phat hien hon.
    """
    ra = []
    for c in kho:
        loi = NP.kiem_khai_bao(c)
        if loi and all("co_che" in e for e in loi):
            ra.append(c)
    return ra


def _nhac(lo: list[dict]) -> str:
    muc = []
    for c in lo:
        muc.append(json.dumps(
            {"ten": c.get("ten"), "ho": c.get("ho"),
             "chieu": c.get("chieu", 1), "giu": c.get("giu", 1),
             "nguon": str(c.get("nguon") or "")[:80],
             "vao": c.get("vao"), "ra": c.get("ra") or []},
            ensure_ascii=False))
    return """Duoi day la %d co che giao dich viet bang mot ngon ngu khai bao.
Moi co che co dieu kien VAO (va co the co dieu kien RA) tinh tu gia.

Voi TUNG co che, viet MOT CAU tieng Viet (>= 30 ky tu) tra loi: **ai la ben
doi ung, va vi sao ho buoc phai giao dich o dung trang thai do** - tuc vi sao
co nguoi tra tien cho phoi nhiem nay.

QUY TAC BAT BUOC:
- KHONG dien lai chinh luat. "Mua khi RSI duoi 30" khong phai mot ly do.
- Ly do phai noi ve NGUOI: ai bi ep ban, ai phai mua lai, ai can thanh khoan
  gap, ai bi rang buoc bao cao/ky quy/chi so.
- Neu ban khong biet ly do kinh te that su, ghi DUNG chuoi "%s".
  Mot cau nghe hop ly ma ban tu nghi ra thi TE HON la khong co cau nao: no se
  lot qua bo loc va lam hong ca kho. Tha bo con hon bia.

CO CHE:
%s

Tra ve JSON: {"ly_do": {"<ten co che>": "<mot cau, hoac %s>", ...}}""" % (
        len(lo), KHONG_BIET, "\n".join(muc), KHONG_BIET)


def chay(lo_size: int = 12, toi_da: int = 200, that: bool = False) -> dict:
    kho = NP.doc_kho()
    can = can_dien(kho)[:toi_da]
    print("kho %d co che, %d muc thieu 'co_che'" % (len(kho), len(can)))
    if not can:
        return {"can": 0}

    ly_do: dict = {}
    so_goi = 0
    for i in range(0, len(can), lo_size):
        lo = can[i:i + lo_size]
        # `bo_qua_han_muc=True`: day la duong BOC HANG LOAT, cung lop voi
        # `boc_ma_llm` / `doc_chi_bao`. Phanh 600 giay/luot cua `tri_tue` danh
        # cho cau hoi le; ap no o day thi 13 lo thanh hon hai gio cho.
        kq = TT.hoi_json(_nhac(lo), HE_THONG, bo_qua_han_muc=True)
        so_goi += 1
        if kq.get("bo_qua"):
            print("  dung o lo %d: %s" % (i // lo_size + 1, kq["bo_qua"]))
            break
        d = (kq.get("json") or {}).get("ly_do") or {}
        if not d:
            print("  lo %d: khong doc duoc JSON (%s)"
                  % (i // lo_size + 1, kq.get("loi") or kq.get("loi_phan_tich")))
            continue
        ly_do.update({str(k): str(v) for k, v in d.items()})
        print("  lo %d/%d: %d cau" % (i // lo_size + 1,
                                      (len(can) + lo_size - 1) // lo_size, len(d)))

    dien, khong_biet, hong = [], [], []
    theo_ten = {c["ten"]: c for c in kho}
    for c in can:
        v = (ly_do.get(c["ten"]) or "").strip()
        if not v:
            hong.append(c["ten"])
        elif KHONG_BIET in v or len(v) < 25:
            khong_biet.append(c["ten"])
        else:
            thu = dict(c, co_che=v)
            # Cau moi phai lam spec QUA duoc cong that, khong phai dai la duoc.
            if NP.kiem_khai_bao(thu):
                hong.append(c["ten"])
            else:
                theo_ten[c["ten"]]["co_che"] = v
                # XUAT XU, khong phai trang tri. Mot cau do LLM viet co the la
                # ly do kinh te that, cung co the chi la dien lai luat bang tu
                # ngu ve nguoi ("quy X bi kich hoat lenh khi RSI qua ban"). Cong
                # cu phap khong phan biet duoc hai thu do. Danh dau de sau nay
                # con truy nguoc duoc, va de khong ai nham mot cau may viet voi
                # mot cau doc ra tu nguon.
                theo_ten[c["ten"]]["co_che_nguon"] = "llm_2026_09_06"
                dien.append((c["ten"], v))

    print("\n%d goi LLM -> dien %d · khong biet %d · khong nhan duoc %d"
          % (so_goi, len(dien), len(khong_biet), len(hong)))
    for t, v in dien[:8]:
        print("  %-34s %s" % (t[:34], v[:90]))
    if khong_biet:
        print("\nCHUA_BIET_LY_DO (ung vien BO, khong phai cho dien not):")
        for t in khong_biet[:20]:
            print("  ", t)

    if that and dien:
        NP.luu_kho(kho)
        print("\nda ghi %d cau vao kho" % len(dien))
    elif not that:
        print("\n(chua ghi - them --that)")
    ra = {"can": len(can), "dien": len(dien), "khong_biet": len(khong_biet),
          "hong": len(hong), "so_goi": so_goi,
          "ten_khong_biet": khong_biet, "ten_hong": hong}
    (LAB / "reports" / "DIEN_CO_CHE.json").write_text(
        json.dumps({**ra, "cau": dict(dien)}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return ra


def main() -> int:
    lo = 12
    if "--lo" in sys.argv:
        lo = int(sys.argv[sys.argv.index("--lo") + 1])
    td = 200
    if "--toi-da" in sys.argv:
        td = int(sys.argv[sys.argv.index("--toi-da") + 1])
    chay(lo, td, "--that" in sys.argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
