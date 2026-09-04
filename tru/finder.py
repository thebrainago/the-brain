# -*- coding: utf-8 -*-
"""finder.py - TRU FINDER. Tim giai phap CONG NGHE de nang cap ha tang.

VI SAO CO TRU NAY, va vi sao no KHONG phai mot bo quet moi.

Chu du an 04/09/2026 dua bon viec, trong do co: "ta bat dau hinh thanh finder -
seeker cua Evo chuyen di tim giai phap cong nghe de nang cap ha tang he thong".

Viec dau tien lam la DI TIM XEM NO DA CO CHUA, va no da co: `nhan/san_cong_cu.py`
(1.440 dong, 30-31/08/2026) da di san repo ngoai, da co so truy van xoay vong, da
loc giay phep, va da NOI VAO SO VAN DE qua `NHU_CAU_TU_VAN_DE` +
`VAN_DE_SANG_NHU_CAU`. Dung nguyen tac "noi day truoc khi xay them": khong viet
lai bo san, ma bo DUNG BA thu no thieu.

DO THAT 04/09/2026 tren `reports/cong_cu.json`:

    110 the, trang_thai = {MOI: 105, CHO_DOC: 5}

Tuc trong hon mot tuan, bo san tim duoc 110 ung vien va **khong mot cai nao di
tiep**. Day dung hinh dang nut that cua pheu boc: khau SAN chay tot, khau KET
LUAN khong ton tai. Mot bo san khong co buoc phan loai thi khong phai mot tru -
no la mot cai hom.

BA THU FINDER BO VAO:

1. **MUC KHOP** (`muc_khop`) - khac han `san_cong_cu.cham_diem`.
   `cham_diem` do SUC KHOE KHO MA: sao, lan day cuoi, giay phep, fork. Bon truc
   do noi repo co dang song khong; khong truc nao noi no co giai duoc van de
   CUA TA khong. Mot repo 5.000 sao con song hoan hao van co the vo dung o day.
   `muc_khop` do CHIEU CON LAI: the nay neo vao van de nao dang mo, bang chung
   khop la gi, ngon ngu co nhap duoc khong.

2. **CONG TICH HOP** (`cong_tich_hop`) - bo san chua bao gio uoc luong. Mot the
   khong kem gia thi khong so sanh duoc voi the khac, nen khong xep hang duoc,
   nen khong ai chon.

3. **RANG BUOC NEO** - dieu kien chu du an dat ra: *"1 repo chi vao the de xuat
   neu khop >=1 van de da biet cu the - khong luom tu do"*. Kiem tra thuc te:
   `NHU_CAU` TINH (viet tay, 01/09) khong he neo vao bang `van_de`; chi
   `NHU_CAU_TU_VAN_DE` co neo. Nen phan lon trong 110 the KHONG dat dieu kien
   do. Finder khong xoa chung - no danh dau `TAM_HOAN` kem ly do, vi "chua neo"
   khac "da bac bo".

RANH GIOI GIU NGUYEN tu `san_cong_cu`, khong duoc noi long:

    Cong cu ngoai duoc lam BAN THI NGHIEM (engine, bao cao, nap du lieu).
    Cong cu ngoai KHONG BAO GIO lam ONG TOA (cong PASS, FDR, dang ky truoc).

Va Finder KHONG tu tich hop gi ca. No chi bien mot dong repo thanh mot the co
du thong tin de NGUOI quyet dinh trong mot phut thay vi mot buoi.

FINDER vs SEEKER vs EVOLUTION:
    SEEKER     san TRI THUC tai chinh  -> co che -> gia thuyet
    EVOLUTION  do NOI BO, tu sua viec da khai bao, de ra `van_de`
    FINDER     san CONG NGHE ben ngoai -> the de xuat -> nguoi doc
Finder an dau vao tu so `van_de` cua Evolution va tra dau ra cho nguoi; no
khong tu do di lom cong cu "hay ho" khong ai can.
"""
from __future__ import annotations

import json
from pathlib import Path

from nhan import san_cong_cu as SCC
from nhan import so as SO

LAB = Path(__file__).resolve().parent.parent
THE = LAB / "reports" / "finder_the.json"

#: Diem suc khoe toi thieu de mot the da NEO duoc de xuat. Duoi muc nay thi kho
#: ma qua yeu (it nguoi dung / da bo / giay phep mo ho) de dang cong doc.
SAN_SUC_KHOE = 45.0

#: Ngon ngu nhap duoc thang vao `lab`. Ngoai danh sach nay thi cong tich hop
#: nhay mot bac: phai doc de HIEU roi VIET LAI bang Python, khong import duoc.
NGON_NGU_NHAP_DUOC = {"Python", "Jupyter Notebook"}

#: Loai the -> cong tich hop CO SO (bac 1..4). Mot thu vien don la re nhat; mot
#: khung tron doi doi kien truc la dat nhat.
CONG_CO_SO = {"thu_vien": 1, "cong_cu": 2, "khung": 4, "bai_bao": 2, "khac": 3}
TEN_BAC = {1: "THAP", 2: "VUA", 3: "CAO", 4: "RAT_CAO"}


#: TU KHOA -> NHU CAU. Dung de gan `nhu_cau` cho ung vien den tu mot dong chay
#: qua (tinix) - nhung ban ghi khong sinh ra tu mot truy van nen khong mang san
#: nhu cau nao.
#:
#: DAY LA KHAI BAO, khong phai suy dien: nguyen tac "kien thuc moi chi vao he
#: bang khai bao" (`nhan/ngu_phap.py`) ap ca o day. Khong LLM nao duoc gan nhu
#: cau, vi mot the gan sai se NEO gia vao mot van de that va lam hong dung cai
#: rang buoc ma chu du an dat ra.
#:
#: Khong khop = `nhu_cau` van la None = the o TAM_HOAN. Do la cau tra loi dung:
#: "chua biet no giai van de nao cua ta", khong phai "no vo dung".
#: MOI mau deu phai chan bien tu. Do that 04/09/2026 ngay trong lan chay dau:
#: ban dau nhanh `doc_ma_thanh_chien_luoc` co mot lua chon tran la `ast` (y dinh
#: la "abstract syntax tree"). Khong chan bien tu thi no khop vao **l**ast,
#: contr**ast**, f**ast** - va ket qua la 11 the neo duoc, ca 11 deu la BAI BAO
#: arXiv khong lien quan ("Kinetic modelling of the CO2 capture", "Real-Time
#: Structural Detection for Indoor..."), neo vao van de that
#: `can_mau_moi_tu_ma_nguon`.
#:
#: Do dung la cai hai ma chinh ghi chu tren canh bao: mot neo GIA lam hong dung
#: cai rang buoc chu du an dat ra. Nen quy tac o day la `\b...\b` cho MOI muc,
#: khong co ngoai le, va cum ngan hon 4 ky tu thi khong duoc dung mot minh.
TU_KHOA_NHU_CAU: list[tuple[str, str]] = [
    (r"\b(crawl\w*|scrap(e|er|ing)|spider|firecrawl|bot[- ]detection|"
     r"anti-?detect\w*|telegram|headless|playwright|puppeteer|"
     r"session[- ]reuse|scraping)\b", "thu_thap_nguon_rong"),
    (r"\b(pine[- ]?script|mql[45]?|metatrader|mt[45]|expert[- ]advisor|"
     r"strategy[- ]pars\w*|transpil\w*|abstract[- ]syntax[- ]tree)\b",
     "doc_ma_thanh_chien_luoc"),
    (r"\b(indicator[s]?|supertrend|zigzag|fractal[s]?|"
     r"technical[- ]analysis|ta-lib)\b", "toan_tu_co_nho"),
    (r"\b(bootstrap\w*|surrogate|monte[- ]?carlo|permutation[- ]test\w*)\b",
     "nha_may_null_qua_nho"),
    (r"\b(deflated[- ]sharpe|haircut|multiple[- ]testing|false[- ]discovery|"
     r"track[- ]record)\b", "do_luc_cong"),
    (r"\b(newey[- ]west|hodrick|overlapping[- ]returns?|autocorrelat\w*)\b",
     "p_value_chuoi_chong_lan"),
    (r"\b(langextract|structured[- ]output|instructor|"
     r"information[- ]extraction)\b", "doc_ma_thanh_chien_luoc"),
    (r"\b(ocr|tesseract|paddleocr|easyocr|rapidocr|document[- ]ai|scanned[- ]pdf|pdf[- ]to[- ](markdown|text))\b",
     "ocr_nhanh_tieng_viet"),
]


def la_bai_bao(v: dict) -> bool:
    """Ban ghi nay la BAI BAO chu khong phai kho ma?

    Dau nhan la `loai == "bai_bao"` (do `san_cong_cu` dat khi lay tu arxiv/
    openalex), phu tro bang ten mien. KHONG dung `full_name` de doan: bai bao
    trong kho VAN co `full_name` - do la TIEU DE bai, khong phai `owner/repo`.
    Do la ly do lan sua dau tien khong an: dieu kien `not full_name` chua bao
    gio dung cho mot ban ghi nao.
    """
    if str(v.get("loai") or "") == "bai_bao":
        return True
    u = str(v.get("url") or "")
    return "arxiv.org" in u or "openalex.org" in u or "doi.org" in u


def doan_nhu_cau(v: dict) -> tuple[str | None, str]:
    """Gan nhu cau cho mot the CHUA co, kem BANG CHUNG la cum tu nao khop.

    KHONG gan cho BAI BAO. Bai bao vao kho tu mot truy van da mang san nhu cau
    cua no; gan them bang tu khoa chi tao ra neo gia (do that: 11/11 the neo
    duoc trong lan chay dau la bai bao bi gan nham). Bai bao thieu nhu cau thi
    de thieu - do la cau tra loi dung.

    Tra `(None, "")` khi khong cum nao khop, va do cung la ket qua hop le.
    """
    import re as _re
    if la_bai_bao(v):
        return None, ""
    van = " ".join([str(v.get("full_name") or ""), str(v.get("mo_ta") or ""),
                    " ".join(v.get("chu_de") or [])])
    for mau, nc in TU_KHOA_NHU_CAU:
        m = _re.search(mau, van, _re.I)
        if m:
            i = max(0, m.start() - 60)
            return nc, van[i:m.end() + 60]
    return None, ""


def _nhu_cau_co_neo(van_de_mo: list[dict]) -> dict[str, list[str]]:
    """nhu_cau -> danh sach ma van de DANG MO da kich hoat no.

    Chi tinh van de dang MO: mot the neo vao van de da dong thi khong con ly do
    ton tai, va do la cach the tu het han ma khong can ai don.
    """
    ra: dict[str, list[str]] = {}
    for v in van_de_mo or []:
        khoa = SCC.VAN_DE_SANG_NHU_CAU.get(v.get("ma") or "")
        if khoa:
            ra.setdefault(khoa, []).append(v["ma"])
    return ra


def cong_tich_hop(the: dict) -> dict:
    """Uoc tinh cong tich hop. Ordinal, khong phai gio - dung de XEP THU TU.

    Khong tra ve "3 ngay": mot con so gio bia ra trong se duoc doc nhu mot cam
    ket. Tra bac + ly do de nguoi tu quy ra thoi gian cua ho.
    """
    bac = CONG_CO_SO.get(str(the.get("loai") or "khac"), 3)
    ly_do = [f"loai={the.get('loai') or 'khac'}"]
    ng = the.get("ngon_ngu")
    if ng and ng not in NGON_NGU_NHAP_DUOC:
        bac += 1
        ly_do.append(f"ngon ngu {ng}: phai doc roi viet lai, khong import duoc")
    gp = the.get("giay_phep")
    if gp in SCC.GIAY_PHEP_LAY_NHIEM:
        bac += 1
        ly_do.append(f"giay phep {gp} lay nhiem: chi doc de doi chieu, khong nhap ma")
    if the.get("doi_chieu_voi"):
        ly_do.append(f"da biet cham vao dau: {the['doi_chieu_voi']}")
    else:
        bac += 1
        ly_do.append("chua biet no cham vao file nao cua he")
    bac = max(1, min(4, bac))
    return {"bac": bac, "muc": TEN_BAC[bac], "ly_do": ly_do}


def muc_khop(the: dict, neo: list[str]) -> dict:
    """0-100: the nay khop van de CUA TA den dau. KHONG do suc khoe kho ma.

    Bon truc, moi truc 25:
      - NEO   : co van de dang mo nao doi thu nay khong (truc quan trong nhat;
                khong neo thi ba truc con lai khong cuu duoc).
      - BANG CHUNG: bo san co trich duoc cau van noi ro no lam gi khong.
      - NHAP  : ngon ngu co dung vao `lab` duoc khong.
      - DICH  : co biet no cham vao file nao cua he khong.
    """
    d_neo = 25.0 if neo else 0.0
    # `mo_ta` la bang chung hop le: voi ban ghi tu tinix do la mo ta tu tac gia
    # repo viet, khong phai suy dien cua ta. Chi xep sau trich dan/cum khop vi
    # hai cai kia la cau van BO SAN da doi chieu duoc voi nhu cau.
    bc = the.get("trich_dan") or the.get("cum_khop") or the.get("mo_ta") or ""
    d_bc = 25.0 if len(str(bc)) > 120 else 15.0 if bc else 0.0
    d_nhap = 25.0 if the.get("ngon_ngu") in NGON_NGU_NHAP_DUOC else \
        10.0 if the.get("ngon_ngu") else 5.0
    d_dich = 25.0 if the.get("doi_chieu_voi") else 0.0
    return {"muc_khop": round(d_neo + d_bc + d_nhap + d_dich, 1),
            "truc": {"neo": d_neo, "bang_chung": d_bc, "nhap": d_nhap,
                     "dich": d_dich}}


def rui_ro(the: dict, neo: list[str]) -> list[str]:
    """Gop canh bao cua bo san + rui ro rieng cua viec TICH HOP."""
    r = list(the.get("canh_bao") or [])
    if not neo:
        r.append("CHUA NEO: khong van de dang mo nao doi thu nay - "
                 "tich hop bay gio la mo rong pham vi khong ai yeu cau")
    if the.get("giay_phep") in SCC.GIAY_PHEP_LAY_NHIEM:
        r.append("chi duoc DOC de doi chieu, khong duoc nhap ma vao du an")
    nc = SCC.NHU_CAU.get(the.get("nhu_cau")) or \
        SCC.NHU_CAU_TU_VAN_DE.get(the.get("nhu_cau")) or {}
    if nc.get("khong_duoc_thay"):
        r.append("RANG BUOC: " + str(nc["khong_duoc_thay"])[:200])
    return r


def lam_the(khoa: str, v: dict, co_neo: dict) -> dict:
    """Mot ban ghi kho cong cu -> mot THE DE XUAT dung schema chu du an dua."""
    neo = co_neo.get(v.get("nhu_cau"), [])
    mk = muc_khop(v, neo)
    ct = cong_tich_hop(v)
    suc_khoe = v.get("diem")
    tam = bool(v.get("nhu_cau_gan_boi"))

    if la_bai_bao(v):
        # Mot BAI BAO khong phai thu tich hop duoc. Chu du an dinh nghia Finder
        # 04/09: "di tim nhung du an nay => tich hop vao he thong chung ta co".
        # Bai bao van co gia tri - nhung no thuoc hang doi DOC, khong phai hang
        # doi TICH HOP, va tron hai thu lam hong ca hai.
        #
        # Do that: lan chay dau ra 10 DE_XUAT thi 8 la bai bao arXiv khong lien
        # quan ("Kinetic modelling of the CO2 capture...", "Real-Time Structural
        # Detection for Indoor Navigation..."). Chung mang san `nhu_cau` tu
        # khau san bai bao cua `san_cong_cu`, nen NEO that nhung VO NGHIA.
        tt = "DOC_THAM_KHAO"
    elif not neo:
        tt = "TAM_HOAN"
    elif suc_khoe is not None and suc_khoe < SAN_SUC_KHOE:
        tt = "LOAI"
    elif tam:
        # Neo do `doan_nhu_cau` gan bang TU KHOA la neo TAM. Do that 04/09: hai
        # the duy nhat qua duoc deu khop nham - `mt5-headless` (chay MT5 khong
        # giao dien) trung tu "headless" cua nhom quet web, va `anti-mage` la bo
        # PHAT HIEN trinh duyet chong-nhan-dang chu khong giup ta vao nguon nao.
        # Ca hai deu hop ly khi nhin tu xa va sai khi doc ky.
        #
        # Nen tu khoa KHONG duoc tu minh phong mot the len DE_XUAT. No dua the
        # den truoc mat nguoi, va nguoi xac nhan. Giu duoc rang buoc "chi de
        # xuat khi khop mot van de that" ma khong de mot regex gia mao cai khop
        # do.
        tt = "CHO_XAC_NHAN"
    elif mk["muc_khop"] >= 50:
        tt = "DE_XUAT"
    else:
        tt = "TAM_HOAN"
    return {
        "id": v.get("full_name") or khoa,
        "nguon": v.get("nguon") or v.get("nguon_phat_hien") or "?",
        "loai": v.get("loai") or "khac",
        "van_de_giai_quyet": neo,
        "nhu_cau": v.get("nhu_cau"),
        "tom_tat": (v.get("mo_ta") or v.get("tieu_de") or "")[:400],
        "muc_khop": mk["muc_khop"],
        "truc_khop": mk["truc"],
        "suc_khoe_kho_ma": suc_khoe,
        "rui_ro": rui_ro(v, neo),
        "cong_tich_hop": ct,
        "trang_thai": tt,
        "neo_tam": tam,
        "neo_bang_chung": v.get("nhu_cau_bang_chung"),
        "url": v.get("url"),
        "doi_chieu_voi": v.get("doi_chieu_voi"),
    }


def phan_loai(ghi: bool = True, in_ra=print) -> dict:
    """Bien toan bo kho cong cu thanh the de xuat + phan loai.

    KHONG xoa gi, KHONG tich hop gi. Chi tra loi duoc cau: "trong 110 cai nay,
    cai nao dang doc hom nay va vi sao".
    """
    kho = SCC.doc_kho()
    vd = SO.van_de_mo() or []
    co_neo = _nhu_cau_co_neo(vd)

    # The den tu mot dong chay qua (tinix) khong mang nhu cau nao. Gan bang
    # KHAI BAO truoc khi cham, va ghi lai bang chung de kiem lai duoc bang mat.
    da_gan = 0
    for v in kho.values():
        cu_nc = v.get("nhu_cau")
        # Gan cho the CHUA co nhu cau, VA gan lai cho the mang mot nhu cau ma
        # khong con van de nao dang doi.
        #
        # VI SAO can nhanh thu hai. Do that 04/09/2026: `hoainama8/convertOCR`
        # - dung cong cu chu du an chi tu 30/08 - nam yen o TAM_HOAN vi no mang
        # nhan `doc_pdf`, ma `doc_pdf` khong co van de nao dang mo. Cung luc do
        # van de `ocr_anh_chan_nguon` vua duoc ghi va dang tim dung mot thu nhu
        # the. Mot kho cong cu ma cai dung nhat nam im vi mot cai nhan cu la
        # mot kho hong.
        #
        # Nhu cau cu duoc giu o `nhu_cau_goc` - khong xoa dau vet, va van la
        # neo TAM nen chi len toi CHO_XAC_NHAN.
        if cu_nc and cu_nc in co_neo:
            continue
        nc, bc = doan_nhu_cau(v)
        if nc and nc != cu_nc and (not cu_nc or nc in co_neo):
            if cu_nc:
                v["nhu_cau_goc"] = cu_nc
            v["nhu_cau"] = nc
            v["nhu_cau_bang_chung"] = bc
            v["nhu_cau_gan_boi"] = "finder.doan_nhu_cau"
            da_gan += 1
    if da_gan and ghi:
        SCC.luu_kho(kho)

    the = [lam_the(k, v, co_neo) for k, v in kho.items()]
    the.sort(key=lambda t: (-(t["muc_khop"]), t["cong_tich_hop"]["bac"]))

    dem: dict[str, int] = {}
    for t in the:
        dem[t["trang_thai"]] = dem.get(t["trang_thai"], 0) + 1

    bao = {"the": len(the), "trang_thai": dem, "nhu_cau_vua_gan": da_gan,
           "van_de_mo": len(vd), "nhu_cau_co_neo": sorted(co_neo),
           "de_xuat": [t for t in the if t["trang_thai"] == "DE_XUAT"][:10]}

    if ghi:
        THE.write_text(json.dumps({"luc": SO.bay_gio(), "bao": bao, "the": the},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
        SO.ghi_chi_so("finder_de_xuat", float(dem.get("DE_XUAT", 0)),
                      {"tong": len(the)})

    in_ra(f"FINDER: {len(the)} the | {dem}")
    in_ra(f"  van de dang mo: {len(vd)}, trong do co nhu cau neo: "
          f"{sorted(co_neo) or 'KHONG CAI NAO'}")
    for t in bao["de_xuat"]:
        in_ra(f"  [{t['muc_khop']:5.1f}] {t['id']}  "
              f"cong={t['cong_tich_hop']['muc']}  neo={t['van_de_giai_quyet']}")
    if not bao["de_xuat"]:
        in_ra("  KHONG the nao dat nguong de xuat. Doc `nhu_cau_co_neo`: neu "
              "rong thi nguyen nhan la KHONG van de NANG nao dang mo co anh xa "
              "trong san_cong_cu.VAN_DE_SANG_NHU_CAU - do la thieu ANH XA, "
              "khong phai thieu cong cu.")
    return bao


def vuong(ma: str, mo_ta: str, bang_chung: dict | None = None,
          muc: str = "NANG", san_luon: bool = True, in_ra=print) -> dict:
    """MOT LOI GOI cho ca vong lap: gap chan -> ghi van de -> Finder di san.

    Chu du an 04/09/2026: *"finder va evo va claude lam viec cac cau di, vuong
    khau nao ta tim giai phap va tien ich cho van de do"*. Truoc ham nay, vong
    do phai lam bang TAY bon buoc (ghi van de, khai nhu cau, them anh xa, chay
    san) va vi vay no khong bao gio duoc lam - mot cai chan gap luc dang ban thi
    nguoi ta chiu dung no chu khong dung lai lam bon buoc.

    CAI HAM NAY KHONG TU KHAI BAO NHU CAU, va do la co y. Mot muc trong
    `NHU_CAU_TU_VAN_DE` phai kem `cam_vao` + `khong_duoc_thay` - hai loi khai
    ranh gioi noi cong cu ngoai duoc cham vao dau va tuyet doi khong duoc doi
    gi. De may tu sinh hai dong do la bo dung cai hang rao. Nen khi chua co anh
    xa, ham tra ve `can_khai_bao` kem doan ma san de dan vao `san_cong_cu.py`.

    Tra ve dict co `van_de_id`, `da_co_anh_xa`, va `san` (neu da san).
    """
    vid = SO.bao_van_de(ma, muc, mo_ta, bang_chung or {})
    nc = SCC.VAN_DE_SANG_NHU_CAU.get(ma)
    co = bool(nc) and nc in SCC.NHU_CAU_TU_VAN_DE
    ra = {"van_de_id": vid, "ma": ma, "muc": muc, "nhu_cau": nc,
          "da_co_anh_xa": co}
    if not co:
        ra["can_khai_bao"] = (
            f'Them vao nhan/san_cong_cu.NHU_CAU_TU_VAN_DE mot muc mo ta cai '
            f'CAN, kem "cam_vao" + "khong_duoc_thay" + "truy_van", roi them '
            f'VAN_DE_SANG_NHU_CAU["{ma}"] = "<ten nhu cau>".')
        in_ra(f"FINDER vuong: da ghi van de '{ma}' (id {vid}) nhung CHUA co "
              f"anh xa nhu cau -> chua san duoc.\n  {ra['can_khai_bao']}")
        return ra
    in_ra(f"FINDER vuong: '{ma}' (id {vid}) -> nhu cau '{nc}'")
    if san_luon and muc in SCC.MUC_SINH_NHU_CAU:
        ra["san"] = mot_luot(san=True, in_ra=in_ra)
    else:
        ra["san"] = {"bo_qua": f"muc {muc} khong sinh truy van san"}
    return ra


def mot_luot(san: bool = True, gioi_han_truy_van: int = 5, in_ra=print) -> dict:
    """Mot vong Finder: san (uy quyen cho san_cong_cu) roi PHAN LOAI.

    `san=False` de chi phan loai lai kho da co - khong ton mot luot mang nao.
    """
    bao = {}
    if san:
        try:
            # PHAI truyen `van_de_mo`, neu khong `nhu_cau_tu_van_de(None)`
            # tra `{}` va nhanh "nhu cau DONG di truoc nhu cau TINH" khong bao
            # gio chay - bo san chi lap lai danh sach tinh cua thang truoc.
            #
            # Do that 04/09/2026: vua dang ky van de NANG `video_khong_co_phu_de`
            # xong, goi ngay `vuong()` -> bo san di hoi "duckdb parquet time
            # series", "supervise long running python process". Khong mot truy
            # van nao ve video. Van de moi xep hang sau mot so truy van xoay
            # vong, dung ra phai di dau tien.
            bao["san"] = SCC.mot_luot(gioi_han_truy_van=gioi_han_truy_van,
                                      van_de_mo=SO.van_de_mo())
        except Exception as e:
            bao["san"] = {"loi": f"{type(e).__name__}: {str(e)[:120]}"}
            in_ra(f"  san loi: {bao['san']['loi']}")
    bao["phan_loai"] = phan_loai(in_ra=in_ra)
    SO.nhip_tim("FINDER", "song", {"de_xuat": bao["phan_loai"]["trang_thai"]})
    return bao


if __name__ == "__main__":
    import sys
    mot_luot(san="--khong-san" not in sys.argv)
