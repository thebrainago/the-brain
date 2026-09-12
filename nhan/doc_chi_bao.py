# -*- coding: utf-8 -*-
"""doc_chi_bao.py - BOC CO CHE TU FILE CHI BAO (190 file, lop chua ai dong toi).

Chu du an 05/09/2026: *"Nang cao hieu suat tach"*.

## VI SAO LOP NAY BI BO QUA HOAN TOAN

`nhan/phan_loai_ma.py` do 05/09: trong 389 artifact ma, **190 file (49%) la chi
bao** - `#property indicator` hoac `OnCalculate` ma khong dat lenh. Khau boc
hien tai (`doc_ma` + `boc_ma_llm`) tim `strategy.entry` / `trade.Buy` /
`OrderSend`. **Khong file chi bao nao co mot dong nao trong so do.**

Nen 190 file khong "that bai o khau boc". Chung chua bao gio duoc dua vao khau
boc, va nam trong mau so nhu file khong ra co che. Do chinh la khoang cach giua
"70%" bao hom qua (70% cua 113 file co lenh vao) va **20% cua ca kho**.

## CHI BAO DINH NGHIA TIN HIEU O CHO KHAC

Mot EA noi tin hieu bang lenh: `if(rsi<30) trade.Buy(...)`. Mot chi bao noi
cung dieu do bang ba cach khac, do duoc tren 190 file:

    buffer trong `if`    37 file (19%)   `if(cond) BufferUp[i]=low[i]-10*_Point;`
    mui ten              34 file (18%)   `PLOT_ARROW` / `DRAW_ARROW` / arrow_code
    cat nhau             14 file ( 7%)   `cross`, `CrossUp`, cat len/xuong
    canh bao             79 file (42%)   `Alert("BUY signal")` / SendNotification
    ---
    co it nhat mot cach  ~ 60%

Cai duoc ve vao buffer mui ten CHINH LA tin hieu vao - tac gia chi bao va tac
gia EA dang noi cung mot cau, khac chi o cho dat lenh hay khong.

## CUNG KIEN TRUC VOI `boc_ma_llm`, KHAC MOI BO TIM VUNG

Bon lan va regex vao MQL5 tuy y da that bai (xem `boc_ma_llm`), va khong lam
lai o day. Kien truc giu nguyen: **regex khoanh VUNG, LLM dich vung do vao
schema co san**. Cai moi la bo tim vung - no tim cho GAN BUFFER / GOI ALERT
thay vi cho DAT LENH.

Rang buoc khong doi: moi khai bao phai qua `ngu_phap.kiem_khai_bao` +
`kiem_khong_nhin_truoc` truoc khi vao kho. **Khong `exec` ma LLM sinh.**

## MOT BAY RIENG CUA CHI BAO: NHIN TRUOC

Chi bao ve len bieu do co the ve LAI qua khu (repaint): `BufferUp[i]` duoc gan
o vong lap chay tu `rates_total` xuong, dung gia cua bar SAU. Dich sang DSL thi
dieu do thanh nhin truoc va se an mot edge gia. Nen o day `kiem_khong_nhin_truoc`
KHONG duoc bo qua - no la cong quan trong nhat cua duong nay, khong phai mot
buoc kiem hinh thuc.
"""
from __future__ import annotations

import concurrent.futures as _cf
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Chay thang `python nhan/doc_chi_bao.py` thi `nhan` chua nam tren duong nhap.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nhan import boc_ma_llm as BM

#: Tran ky tu mot vung gui cho LLM. Cung muc voi `boc_ma_llm.MAX_VUNG`.
MAX_VUNG = 16000
#: LUONG cao hon so nhan la DUNG o day: moi luong dung 8-10 giay CHO MANG
#: (goi LLM), khong an CPU. Do 12/09: 684 file x ~32s/file (hai tang x hai
#: lan thu) / 6 luong = 61 phut; 12 luong ha con ~30 phut ma CPU van ranh
#: cho pheu chay song song.
LUONG = 12

#: Cho phep mot `if(...)` dung TRUOC cho gan, tren CUNG MOT DONG.
#:
#: Do 05/09: `if(rsi[i] < 30.0) ExtUp[i] = close[i];` viet mot dong la cach viet
#: pho bien nhat cua chi bao mui ten. Ban dau bo tim doi cho gan phai o DAU DONG
#: (chi co khoang trang phia truoc) nen no truot sach lop nay - va truot dung
#: cai dong MANG dieu kien, tuc mat dung thu can tim.
_IF_MOT_DONG = r"^[ \t]*(?:if[ \t]*\([^)]{0,200}\)[ \t]*)?"

#: Gan mot buffer ve o trong THAN mot `if`. Day la cho chi bao "noi" tin hieu.
_RX_BUF = re.compile(_IF_MOT_DONG + r"(\w*[Bb]uf\w*|\w*[Aa]rrow\w*|\w*[Ss]ig\w*)"
                     r"\s*\[[^\]]{1,40}\]\s*=", re.M)
#: Canh bao / thong bao - hau het deu nam ngay sau dieu kien tin hieu.
_RX_ALERT = re.compile(r"^[ \t]*(Alert|SendNotification|SendMail|Print)\s*\("
                       r"[^)]{0,120}(?i:buy|sell|signal|long|short)", re.M)
#: Cho tinh cat nhau.
_RX_CROSS = re.compile(r"(?i)^[ \t]*(?:\w+\s+)?\w*(cross|cat)\w*\s*=", re.M)
#: Chi bao VE VAT THE thay vi ghi buffer: `indicator_buffers 0` + `ObjectCreate`.
#: Do 05/09: **97/190 file chi bao khong khai mot buffer nao**. Chung la lop
#: order block / FVG / liquidity map / session map - ve hop chu nhat len bieu do.
#: Bo qua ca lop nay la bo qua chinh nhom co che ma DSL hien chua dien duoc, va
#: khong bao gio biet minh dang thieu gi. LLM tra `khong_dien_dat_duoc` o day
#: la mot ket qua CO GIA TRI: no chi ra tu vung con thieu cua ngu phap.
_RX_VE = re.compile(r"^[ \t]*(?:ObjectCreate|ObjectSetInteger|ObjectSetString)"
                    r"\s*\(", re.M)


def vung_tin_hieu(src: str, so_vung: int = 6) -> list[str]:
    """Khoanh cac VUNG dinh nghia tin hieu trong mot file chi bao.

    Uu tien: buffer trong `if` > cat nhau > canh bao. Ly do: buffer la noi tac
    gia ghi tin hieu de MAY doc; canh bao la noi ghi de NGUOI doc, va thuong
    thieu dieu kien (`Alert("BUY")` sau mot bien `sig` da tinh o cho khac).
    """
    from nhan import doc_ma as DM
    vb = DM._chuan_hoa(src)
    L = vb.splitlines(keepends=True)
    dau, p = [], 0
    for l in L:
        dau.append(p)
        p += len(l)

    ra, da_lay = [], set()

    def _them(vi_tri: int, tren: int, duoi: int, tran: int,
              phai_co_if: bool = False) -> None:
        i = max(k for k, x in enumerate(dau) if x <= vi_tri)
        khoa = i // 6                      # gom cac cho sat nhau lam mot
        if khoa in da_lay:
            return
        doan = "".join(L[max(0, i - tren):min(len(L), i + duoi)])
        # Vung VE VAT THE chi dang doc khi co dieu kien o gan: mot
        # `ObjectCreate` de ve khung gio hay nhan chu khong noi gi ve tin hieu.
        if phai_co_if and "if" not in doan:
            return
        da_lay.add(khoa)
        ra.append(doan[:tran])

    # Ten buffer THAT cua file, hoc tu `SetIndexBuffer(0, TenBien)`. Bat theo
    # ten bien tu khai bao chinh xac hon bat theo chuoi "buf"/"arrow" trong ten:
    # do 05/09, 88/190 file khai buffer nhung nhieu file dat ten kieu `ExtUp`,
    # `HistogramValues`, `TrendLine` - khong khop mau chu nao ca.
    ten_buf = set(re.findall(r"SetIndexBuffer\s*\(\s*\d+\s*,\s*(\w+)", vb))
    dot = []
    if ten_buf:
        dot.append((re.compile(_IF_MOT_DONG + r"(?:%s)\s*\[[^\]]{1,40}\]\s*="
                               % "|".join(re.escape(t) for t in ten_buf), re.M),
                    14, 3, 1400, False))
    dot += [(_RX_BUF, 14, 3, 1400, False),
            (_RX_CROSS, 10, 4, 1000, False),
            (_RX_ALERT, 14, 2, 1200, False),
            (_RX_VE, 16, 2, 1400, True)]

    for rx, tren, duoi, tran, phai_if in dot:
        for m in rx.finditer(vb):
            _them(m.start(), tren, duoi, tran, phai_if)
            if len(ra) >= so_vung:
                break
        if len(ra) >= so_vung:
            break

    if not ra:
        return []
    # Bien cuc bo: LLM khong doan duoc `maFast`/`g_level` la gi neu khong thay
    # dong tinh no. Dung chinh bo cua `boc_ma_llm` de hai duong khong lech nhau.
    ra += BM._ngu_canh_bien("".join(ra), L, dau)
    return ra


def _nhac(ten: str, vung: list[str], ngu_phap_tom_tat: str) -> str:
    return f"""Day la vung DINH NGHIA TIN HIEU rut tu mot CHI BAO MQL5 (`{ten}`).
Chi bao khong dat lenh - no ve tin hieu vao buffer/mui ten hoac ban canh bao.
Nhiem vu: doc dieu kien lam tin hieu XUAT HIEN va dien vao schema JSON duoi.

{ngu_phap_tom_tat}

QUY TAC:
- Dieu kien can tim la dieu kien lam mot buffer mui ten duoc gan gia tri, hoac
  lam `Alert("BUY"/"SELL")` chay. Do la tin hieu VAO LENH.
- BO QUA: ve mau, dat do rong duong, kiem `rates_total`, vong lap khoi tao,
  `if(i>=rates_total)`, `ArraySetAsSeries`, dem bar.
- LAY HET dieu kien doc duoc; ca chieu MUA va chieu BAN neu ca hai co mat.
  Chong trung la viec cua he, khong phai viec cua ban.
- `chieu`: 1 neu buffer/canh bao do la MUA (arrow len, "BUY", "LONG"),
  -1 neu BAN.
- Chu ky chi bao phai la SO CU THE. Neu ma dung mot bien tham so
  (`InpPeriod`) thi lay gia tri mac dinh khai bao trong file.
- Neu mot bien nhu `maFast` la trung binh dong N chu ky thi dich thanh
  {{"chi_bao":"ema","n":N}}. Phan "CHO GAN BIEN" duoi cho biet cac bien do
  duoc tinh the nao.
- Ve nao that su khong dien duoc thi ghi vao "khong_dien_dat_duoc", VAN tra ve
  cac ve con lai.

VUNG MA (dau: cho gan buffer/canh bao · cuoi: CHO GAN BIEN):
```
{chr(10).join(vung)[:MAX_VUNG]}
```

- Moi muc PHAI co truong `co_che`: MOT CAU (>= 25 ky tu) noi VI SAO co nguoi
  tra tien cho phoi nhiem nay - ai la ben doi ung va vi sao ho buoc phai giao
  dich o trang thai do. **Khong dien lai chinh luat**. Neu ban khong biet ly do
  kinh te thi ghi dung chuoi "CHUA_BIET_LY_DO", dung bia mot cau nghe hop ly.

Tra ve DUNG mot JSON: {{"co_che": [{{"ten": "...", "ho": "...", "chieu": 1,
"giu": 1, "co_che": "...", "vao": [{{"trai": {{...}}, "phep": "<",
"phai": {{...}}}}]}}]}}"""


def _mot(d: dict, tom_tat: str, model: str = "") -> dict:
    from nhan import tri_tue as TT
    vung = vung_tin_hieu(d["src"])
    if not vung:
        return {"ten": d["ten"], "co_che": [], "vi_sao": "khong khoanh duoc vung"}
    try:
        # Duong BOC co han muc rieng - quen `bo_qua_han_muc` thi ca me tra
        # `{"bo_qua": ...}` va ra 0 (do that 05/09 tren duong `boc_ma_llm`).
        r = TT.hoi_json(_nhac(d["ten"], vung, tom_tat),
                        bo_qua_han_muc=True, dung_cache=False, model=model)
    except Exception as e:
        return {"ten": d["ten"], "co_che": [],
                "vi_sao": "%s: %s" % (type(e).__name__, str(e)[:60])}
    # `tri_tue.hoi_json` KHONG nem ngoai le khi goi hong - no tra `{"loi": ...}`.
    # Doc thang `.get("co_che")` tren dict do ra `[]`, va `[]` duoc bao cao la
    # "LLM tra ve rong". Do 05/09: quota API ve 0 d, ca me 20 file chay het 2
    # GIAY va bao 0/20 - doc nhu "bo doc khong hieu file chi bao nao" trong khi
    # KHONG MOT LOI GOI NAO xay ra. Day dung la ho benh
    # [[ket-luan-am-phai-phan-biet-chua-do]]: khong do duoc phai ra CHUA_DO chu
    # khong ra 0.
    if isinstance(r, dict) and r.get("loi"):
        return {"ten": d["ten"], "co_che": [], "chua_do": True,
                "vi_sao": "CHUA DO - %s" % str(r["loi"])[:90]}
    j = (r or {}).get("json") or r or {}
    cc = j.get("co_che") or []
    return {"ten": d["ten"], "co_che": cc, "chua_do": False,
            "vi_sao": "" if cc else "LLM tra ve rong"}


#: HAI TANG MODEL. Tang 1 chay ca me; tang 2 chi chay tren file tang 1 tra rong.
#:
#: Do 05/09 tren 6 file chi bao, dem khai bao QUA duoc cong ngu phap va quy ra
#: gia theo bang ratio cua san:
#:      qwen3.7-flash   5/6 file · 4.904 token ra · ratio 0,010/0,040 -> RE NHAT
#:      qwen3.6-flash   6/6 file · 6.155 token ra · ratio 0,0235/0,047
#: Chenh lech nam dung o nhung file kho, nen goi tang 2 CHI cho phan tra rong
#: se re hon nhieu so voi chay ca me bang model dat hon.
MODEL_TANG_1 = ""                 # rong = lay `model_openai` cua cau hinh
MODEL_TANG_2 = "qwen3.6-flash"


def mot_file(d: dict, tom_tat: str, so_lan: int = 2, hai_tang: bool = True) -> dict:
    """Boc MOT file. Thu lai khi tra rong (LLM khong tat dinh), roi doi MODEL.

    Khong thu lai khi `chua_do`: mot loi quota/mang khong tu khoi phuc trong
    3 giay, va thu lai chi lam me chay lau gap doi de ra cung mot con so 0.
    """
    cuoi = {"ten": d["ten"], "co_che": [], "vi_sao": "chua chay"}
    for _ in range(max(1, so_lan)):
        cuoi = _mot(d, tom_tat, MODEL_TANG_1)
        if cuoi["co_che"] or cuoi.get("chua_do"):
            return cuoi
    if hai_tang and MODEL_TANG_2:
        z = _mot(d, tom_tat, MODEL_TANG_2)
        if z["co_che"]:
            z["model_tang_2"] = MODEL_TANG_2
            return z
    return cuoi


def _ds_chi_bao(gioi_han: int = 0) -> list[dict]:
    """File thuoc lan `chi_bao` VA khoanh duoc vung tin hieu."""
    from nhan import phan_loai_ma as PL
    ds = []
    for d in PL._doc_kho_ma():
        z = PL.phan_loai_mot(d["src"], d["ten"])
        if z["lan"] != PL.CHI_BAO:
            continue
        if not vung_tin_hieu(d["src"]):
            continue                       # khong co gi de doc -> khong goi LLM
        ds.append(d)
        if gioi_han and len(ds) >= gioi_han:
            break
    return ds


def _chay(ds: list[dict], so_lan: int, in_ra, tom_tat: str = "") -> list[dict]:
    from nhan import boc_llm as BL
    import time
    # `tom_tat` truyen vao la diem chen CHI DAN RIENG cho tung lop file. Do 06/09:
    # ban tom tat ngu phap co lieu ke nguyen thuy `vung`, nhung VI DU tra ve
    # trong loi nhac chi cho dang so-sanh-tung-nen, va LLM bam vi du chu khong
    # bam ban tham chieu - 0/9 khai bao dung `vung` o luot dau.
    tom_tat = tom_tat or BL._ngu_phap_tom_tat()
    t0 = time.time()
    ket = []
    with _cf.ThreadPoolExecutor(max_workers=LUONG) as ex:
        for i, z in enumerate(ex.map(lambda d: mot_file(d, tom_tat, so_lan), ds), 1):
            ket.append(z)
            if i % 20 == 0:
                in_ra("  ... %d/%d (%.0fs)" % (i, len(ds), time.time() - t0))
    return ket


def moi(so_file: int = 20, in_ra=print) -> dict:
    """TEST ME: do suat tren mau nho TRUOC khi chay het.

    Chu du an: *"test nen co test moi truoc khi test that de do ton thoi gian"*.
    """
    ds = _ds_chi_bao(gioi_han=so_file)
    in_ra("TEST ME tren %d file chi bao co vung tin hieu" % len(ds))
    ket = _chay(ds, 2, in_ra)
    cd = [k for k in ket if k.get("chua_do")]
    if cd:
        in_ra("  !! %d/%d file CHUA DO duoc (khong phai ket qua am):"
              % (len(cd), len(ds)))
        in_ra("     %s" % cd[0]["vi_sao"])
        if len(cd) == len(ds):
            in_ra("  -> ca me khong goi duoc. KHONG co suat de bao cao.")
            return {"so_file": len(ds), "chua_do": len(cd), "ra_co_che": None,
                    "khai_bao": None, "qua_kiem": None, "ket": ket}
    co = [k for k in ket if k["co_che"]]
    tong = sum(len(k["co_che"]) for k in ket)
    in_ra("  LLM tra ve co che : %d/%d file (%.0f%%), %d khai bao"
          % (len(co), len(ds) - len(cd),
             100 * len(co) / max(len(ds) - len(cd), 1), tong))
    giu, ho = [], []
    for k in ket:
        g, h = BM.kiem_va_giu(k["co_che"], nguon=k["ten"])
        giu += g
        ho += h
    in_ra("  qua KIEM KHAI BAO : %d/%d khai bao" % (len(giu), tong))
    if ho:
        in_ra("  bi loai: " + "; ".join(ho[:4]))
    for k, v in Counter(k["vi_sao"] for k in ket if not k["co_che"]).most_common(4):
        in_ra("  khong ra: %-40s %d" % (k[:40], v))
    return {"so_file": len(ds), "ra_co_che": len(co), "khai_bao": tong,
            "qua_kiem": len(giu), "ket": ket}


def chay_that(gioi_han: int = 0, so_lan: int = 2, ghi_kho: bool = True,
              in_ra=print) -> dict:
    """Chay tren TOAN BO file chi bao co vung tin hieu, ghi khai bao dat vao kho."""
    import pathlib
    from nhan import ngu_phap as NP

    ds = _ds_chi_bao(gioi_han)
    in_ra("CHAY THAT tren %d file chi bao (thu lai %d lan)" % (len(ds), so_lan))
    ket = _chay(ds, so_lan, in_ra)
    cd = [k for k in ket if k.get("chua_do")]
    if len(cd) == len(ds) and ds:
        in_ra("  !! CA ME KHONG GOI DUOC: %s" % cd[0]["vi_sao"])
        in_ra("  -> khong ghi kho, khong bao suat. Nap lai quota roi chay lai.")
        return {"so_file": len(ds), "chua_do": len(cd), "ra_co_che": None,
                "qua_kiem": None, "them_kho": 0, "ket": ket}
    if cd:
        in_ra("  !! %d/%d file chua do duoc: %s"
              % (len(cd), len(ds), cd[0]["vi_sao"][:70]))
    try:
        pathlib.Path("reports/doc_chi_bao_tho.json").write_text(
            json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
        in_ra("  da ghi tho -> reports/doc_chi_bao_tho.json")
    except Exception as e:
        in_ra("  khong ghi duoc ban tho: %s" % str(e)[:60])

    co = [k for k in ket if k["co_che"]]
    giu, ho = [], []
    for k in ket:
        g, h = BM.kiem_va_giu(k["co_che"], nguon=k["ten"])
        giu += g
        ho += h
    in_ra("")
    in_ra("  file ra co che   : %d/%d (%.0f%%)"
          % (len(co), len(ds), 100 * len(co) / max(len(ds), 1)))
    in_ra("  khai bao qua kiem: %d" % len(giu))
    them, tu_choi = 0, Counter()
    if ghi_kho and giu:
        # VAO KHO BANG CUA CHINH, KHONG PHAI CUA SAU.
        #
        # Ban dau duong nay (va `boc_ma_llm`) tu goi `NP.doc_kho()` +
        # `NP.luu_kho()`, tuc bo qua `ngu_phap.them_co_che` - "cua duy nhat cho
        # kien thuc moi vao he". Gia phai tra do duoc 05/09: **20 spec trong kho
        # khong CHAY duoc** (`vao: ["khong_dien_dat_duoc"]`, thieu khoa `trai`,
        # toan hang la chuoi, doi cot `bid`/`ask` khong ton tai). Chung qua
        # `kiem_khai_bao` - bai kiem TINH - roi no o buoc sinh tin hieu.
        #
        # `them_co_che(spec, df)` chay THU spec tren du lieu that, nen no bat
        # duoc ca ba thu ma bai kiem tinh khong thay: chay loi, ty le kich hoat
        # suy bien, va nhin truoc.
        from nhan import loc_co_che as LCC
        df_kiem = LCC.df_kiem_chuan()
        if df_kiem is None:
            in_ra("  !! khong nap duoc chuoi kiem - KHONG ghi kho (khong ha cong)")
        else:
            for c in giu:
                c["nguon_lan"] = "chi_bao"
                r = NP.them_co_che(c, df_kiem)
                if r.get("nhan"):
                    them += 1
                else:
                    tu_choi[str((r.get("ly_do") or ["?"])[0])[:46]] += 1
            for k, v in tu_choi.most_common(5):
                in_ra("  cong tu choi %3d : %s" % (v, k))
    in_ra("  them vao kho     : %d" % them)
    return {"so_file": len(ds), "ra_co_che": len(co), "qua_kiem": len(giu),
            "them_kho": them, "ket": ket}


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    sys.stdout.reconfigure(encoding="utf-8")
    if "--that" in sys.argv:
        chay_that()
    else:
        n = 20
        for a in sys.argv[1:]:
            if a.isdigit():
                n = int(a)
        moi(n)
