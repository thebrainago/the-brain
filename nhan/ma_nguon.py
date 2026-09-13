# -*- coding: utf-8 -*-
"""MA NGUON EA / CHI BAO -> CodeArtifact.

VI SAO CAN. Cho toi 22/08/2026 SEEKER chi thu duoc VAN BAN: tieu de + tom tat
cua bai bao, bai dien dan, bai blog. Van ban mo ta co che bang tieng nguoi, va
mot mo ta bang tieng nguoi thi mo ho o dung cho quan trong nhat - "mua khi RSI
thap" khong noi nguong bao nhieu, khung nao, giu bao lau, thoat bang gi.

MA NGUON thi khong mo ho. Mot file `.mq5` noi ro nguong, khung, dieu kien vao,
dieu kien ra, va no la thu DA CHAY THAT tren MT5 cua ai do. Day la nguon co mat
do co che cao nhat ma may nay lay duoc.

BON RANG BUOC AN TOAN - **khong duoc noi long**:

1. **KHONG BAO GIO chay ma tai ve.** Khong `exec`, khong `import`, khong bien
   dich, khong dua vao MetaEditor. Ma nguon o day la VAN BAN de doc, y het mot
   bai bao. Mot dong `.shift(-1)` du de che ra CAGR 115% (da sap that 15/08);
   mot file `.mq5` la tui do cua nguoi la va no con nguy hon nhieu.

2. **Chi anh xa vao mau CO SAN** trong `nhan/mau.py`, qua
   `nhan/bien_dich_ung_vien.py`. Ma nguon duoc phep CHON mot mau da kiem duyet,
   khong duoc dinh nghia mau moi. Do do khong co duong nao de ma tren mang chen
   logic vao may.

3. **Co tran kich thuoc.** Mot file 5 MB khong phai chien luoc, no la thu vien
   dinh kem hoac binary. Doc no vao so cai chi lam phinh CSDL.

4. **Provenance day du.** `CodeArtifact` doi repository_url + revision + path,
   va do la co y: mot doan ma khong biet den tu dau thi khong doi chieu lai duoc
   khi ket qua dang ngo.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import time
from html import unescape

from nhan import hop_dong as HD
from nhan import so as SO

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TheBrainResearch/0.1"

#: Tran kich thuoc mot file ma nguon (byte). Tren muc nay gan nhu chac chan la
#: thu vien dinh kem chu khong phai mot chien luoc doc duoc.
TRAN_BYTE = 400_000
#: Duoi kich thuoc nay thi file khong du de mo ta mot co che.
SAN_BYTE = 400
#: Duoi ma nguon chap nhan. `.mqh` la header - thuong la thu vien, bo qua.
DUOI_NHAN = (".mq5", ".mq4")

_CHU_DE = {"experts": "EA", "indicators": "chi bao"}

#: URL trang MOT BAI trong MQL5 Code Base (khong phai trang danh sach, khong
#: phai trang tai). Dinh nghia MOT LAN o day va dung chung voi
#: `tru/seeker._doc_dinh_tuyen` - truoc 13/09 hai noi giu hai ban regex rieng,
#: va do la dung mau bay "sua mot cho, quen cho kia" cua chinh du an nay.
#: CHUOI, khong phai regex da `re.compile` san: bo test an toan
#: `test_ma_nguon.KhongChayMaTaiVe` quet chuoi con `compile(` trong CA FILE de
#: khoa `compile()` builtin, va no bat nham chinh `re.compile(`.
RE_URL_CODE_MQL5 = r"https?://(www\.)?mql5\.com/[a-z]{2}/code/\d+"

#: Dau hieu ma nguon MQL THAT (dat lenh/quan ly vi the), doi lap voi trang
#: HTML cua landing page (dieu huong + mo ta + binh luan, khong mot dong ma).
#: Do tren `mql5.com/en/code/43355` (chu du an dua ra ngay 12/09): trang dai
#: 62.924 ky tu nhung **0 lan** xuat hien ca ba tu nay.
DAU_HIEU_MA_MQL = ("OnTick", "OrderSend", "CTrade", "OnCalculate", "OrderModify",
                   "PositionOpen", "OnInit")


def co_dau_hieu_ma_that(van_ban: str) -> bool:
    """True neu VAN_BAN co it nhat mot API dat-lenh/tinh-toan cua MQL that.

    Dung o hai cho: (1) `tai_ma_nguon` tu kiem lai chinh no truoc khi tra ve -
    phong khi trang tai bi doi cau truc va vo tinh tra ve mot trang loi thay
    vi file; (2) `thu_hoi_sai_loai` - phan biet ban ghi noi_dung nao THAT SU
    la ma (bo qua) voi ban nao chi la vo trang landing (thu tai lai).
    """
    return any(d in (van_ban or "") for d in DAU_HIEU_MA_MQL)


def _lay(url: str, timeout: int = 30, nhi_phan: bool = False):
    """Tai mot trang/file cua MQL5.

    DA THU va DA BO mot lop "duyet nhu nguoi" (phien giu cookie + Referer +
    nhip ngau nhien) ngay 03/09/2026. Do tach bach tren cung mot may, cung
    mot luc, cung 4 trang:
        `requests.get` tran   -> **4/4 HTTP 200**, 40 link ma moi trang
        `duyet_nguoi.Khach`   -> **4/4 HTTP 403**
    Tuc lop "giong nguoi" chinh la thu bi danh dau, khong phai thu duoc cho
    qua. Phien co cookie tu `/` roi mang Referer di khap noi la mot dau van
    RIENG, va no de nhan hon mot yeu cau tran.

    Cai that su can: (1) DNS khong bi dau doc - `nhan/dns_vuot.py` hoac mot
    duong VPN nhu Cloudflare WARP; (2) mot `User-Agent` that; (3) nghi giua
    cac lan goi. Khong can gi them.

    SUA 13/09/2026 - HAI TANG DNS, giong `tru/seeker._lay` (thieu cai nay la
    NGUYEN NHAN chinh cua "859 trang mql5.com bi luu thanh HTML tho"). Do
    duoc tren so cai: cot `cach='mql5_download'` (ham nay THANH CONG) chi co
    **25 dong, tat ca cung ngay 03/09** - trong khi `_doc_dinh_tuyen` (goi ham
    nay TRUOC TIEN cho moi URL `mql5.com/.../code/N` tu 03/09) van chay deu
    moi ngay va **813 dong moi** roi vao `kieu='khac'` (HTML trang, khong ma)
    trong ba lan quet 08-12/09. Tuc ham nay THAT BAI IM LANG dung luc DNS bi
    dau doc, va nguoi goi (`tru.seeker._doc_dinh_tuyen`) am tham ROT VE bo doc
    HTML chung - bo do co hai tang DNS (`tru.seeker._lay`) nen VAN lay duoc
    trang, chi la lay dung TRANG LANDING chu khong phai FILE MA. Ket qua duoc
    ghi nhu MOT LAN DOC THANH CONG binh thuong (khong phai `khong_doc_duoc`)
    nen khong bao gio duoc thu lai - xem `thu_hoi_sai_loai()` o duoi cho phan
    thu lai cac ban da lo o giai doan truoc khi co sua nay.
    """
    from nhan import duyet_nguoi as DN
    from nhan import dns_vuot as DV
    dau_trang = {"User-Agent": DN.UA, "Accept-Encoding": DN._MA_NEN}

    def _thu():
        import requests
        r = requests.get(url, timeout=timeout, headers=dau_trang)
        if r.status_code != 200:
            return None
        return r.content if nhi_phan else r.text

    can_vuot = any(t in url for t in DV.BAN_DO)
    try:
        kq = _thu()
        if kq is not None:
            return kq
    except Exception:
        pass
    if not can_vuot:
        return None
    # THAT BAI VOI DNS THAT -> thu lai VOI ban do IP tay (dns_vuot), y het
    # chien luoc da hieu chuan cua `tru/seeker._lay`. Khong lam vinh vien: chi
    # bat trong pham vi cua lan goi nay roi tra lai nguyen trang.
    try:
        with DV.Bat():
            return _thu()
    except Exception:
        return None


def _sach(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


CON_TRO = Path(__file__).resolve().parent.parent / "config" / "ma_nguon_con_tro.json"


def _con_tro() -> dict:
    try:
        return json.loads(CON_TRO.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _ghi_con_tro(d: dict) -> None:
    CON_TRO.parent.mkdir(parents=True, exist_ok=True)
    CON_TRO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def liet_ke_mql5(muc: str = "experts", trang: int = 1) -> list[dict]:
    """Danh sach bai trong MQL5 Code Base. Tra [{id, url, tieu_de}].

    HREF o day la TUONG DOI (`/en/code/76331`). Regex doi href tuyet doi la loi
    da lam `tru/seeker.py::n_mql5_code` tra ve rong suot ma khong bao gi.
    """
    u = f"https://www.mql5.com/en/code/mt5/{muc}"
    if trang > 1:
        u += f"/page{trang}"
    txt = _lay(u)
    if not txt:
        return []
    ra, da = [], set()
    for m in re.finditer(
            r'href="(?:https://www\.mql5\.com)?/en/code/(\d+)"[^>]*>(.*?)</a>',
            txt, re.S | re.I):
        ma_so, tt = m.group(1), _sach(m.group(2))
        if ma_so in da or len(tt) < 8:
            continue
        da.add(ma_so)
        ra.append({"id": ma_so, "url": f"https://www.mql5.com/en/code/{ma_so}",
                   "tieu_de": tt[:250], "muc": muc})
    return ra


def tai_ma_nguon(bai: dict) -> dict | None:
    """Trang bai -> file ma nguon dau tien. Tra dict co `noi_dung`, hoac None.

    Trang bai co hai loai link tai: `/en/code/download/<id>/<ten>.mq5` (file don)
    va `/en/code/download/<id>.zip` (goi). Chi lay file don: giai nen zip cua
    nguoi la la mot be mat tan cong khong can thiet, va phan lon bai deu co san
    file don.
    """
    txt = _lay(bai["url"])
    if not txt:
        return None
    link = re.findall(r'href="(/en/code/download/\d+/[^"]+)"', txt)
    lay = next((l for l in link if l.lower().endswith(DUOI_NHAN)), None)
    if not lay:
        return None
    ten = lay.rsplit("/", 1)[-1]
    noi_dung = _lay("https://www.mql5.com" + lay, timeout=40, nhi_phan=True)
    if noi_dung is None or not (SAN_BYTE <= len(noi_dung) <= TRAN_BYTE):
        return None
    try:
        vb = noi_dung.decode("utf-8")
    except UnicodeDecodeError:
        try:
            vb = noi_dung.decode("utf-16")     # MetaEditor hay luu UTF-16
        except UnicodeDecodeError:
            return None
    if not vb.strip():
        return None
    return {**bai, "ten_file": ten, "noi_dung": vb, "so_byte": len(noi_dung)}


def thanh_artifact(bai: dict) -> HD.CodeArtifact:
    """Mot bai da tai -> CodeArtifact voi provenance day du."""
    return HD.CodeArtifact(
        source_id=f"mql5_codebase:{bai['muc']}",
        repository_url=bai["url"],
        # MQL5 khong co commit hash; so bai la dinh danh ON DINH cua ban do -
        # bai duoc sua thi tac gia dang mot bai moi voi so khac.
        revision=f"mql5-code-{bai['id']}",
        path=bai["ten_file"],
        retrieved_at=SO.bay_gio().replace(" ", "T") + "Z",
        content=bai["noi_dung"],
        language="mql5" if bai["ten_file"].lower().endswith(".mq5") else "mql4",
        license="MQL5 Code Base (xem trang goc)",
        metadata={"tieu_de": bai["tieu_de"], "muc": bai["muc"],
                  "chu_de": _CHU_DE.get(bai["muc"], bai["muc"]),
                  "so_byte": bai["so_byte"]})


def thu_thap(muc_can: tuple = ("experts", "indicators"), so_bai: int = 10,
             nghi_giay: float = 1.5) -> dict:
    """Thu thap ma nguon va ghi CodeArtifact vao so cai. Tra bao cao dem duoc.

    Dem CA HAI dau: bao nhieu bai nhin thay, bao nhieu tai duoc, bao nhieu ghi
    moi. Mot ham thu thap chi bao "xong" ma khong bao ba con so do thi khong
    phan biet duoc "nguon rong" voi "bo phan tich hong" - va do dung la cach
    `n_mql5_code` chet im lang trong sau ngay.
    """
    bao = {"nhin_thay": 0, "tai_duoc": 0, "ghi_moi": 0, "trung": 0,
           "bo_qua": [], "bai": []}
    ct = _con_tro()
    trang_cua = ct.setdefault("trang", {})
    for muc in muc_can:
        # PHAN TRANG. Truoc 03/09/2026 cho nay goi `liet_ke_mql5(muc)` tran,
        # tuc LUON trang 1. Chay 4 vong lien tiep cho: vong 1 "moi 35", vong 2
        # va 3 deu "moi 0 | trung 60" - tai lai dung 60 file cu. `liet_ke_mql5`
        # co tham so `trang` tu dau, chi la khong ai truyen.
        n = int(trang_cua.get(muc, 1))
        ds = liet_ke_mql5(muc, n)
        if not ds and n > 1:
            # het trang (hoac hong) -> quay ve dau: muc MOI luon len dau bang
            n = 1
            ds = liet_ke_mql5(muc, n)
        trang_cua[muc] = n + 1 if ds else 1
        bao.setdefault("trang_da_lay", {})[muc] = n
        bao["nhin_thay"] += len(ds)
        for bai in ds[:so_bai]:
            time.sleep(nghi_giay)
            day_du = tai_ma_nguon(bai)
            if not day_du:
                bao["bo_qua"].append(f"{bai['id']}: khong co file don hop le")
                continue
            bao["tai_duoc"] += 1
            try:
                _id, moi = SO.them_artifact(thanh_artifact(day_du))
            except HD.ContractError as e:
                bao["bo_qua"].append(f"{bai['id']}: hop dong tu choi - {str(e)[:70]}")
                continue
            bao["ghi_moi"] += int(moi)
            bao["trung"] += int(not moi)
            bao["bai"].append({"id": bai["id"], "tieu_de": bai["tieu_de"][:70],
                               "url": bai["url"], "file": day_du["ten_file"],
                               "byte": day_du["so_byte"], "moi": bool(moi),
                               # giu tam de `_bao_mau_con_thieu` doc; bi loai
                               # khoi bao cao ghi so ngay sau do.
                               "_noi_dung": day_du["noi_dung"]})
    _ghi_con_tro(ct)
    _bao_mau_con_thieu(bao)
    for b in bao["bai"]:
        b.pop("_noi_dung", None)          # khong doc ca file ma nguon vao so cai
    SO.ghi_chi_so("ma_nguon_ghi_moi", float(bao["ghi_moi"]),
                  {k: v for k, v in bao.items() if k != "bai"})
    return bao


def _bao_mau_con_thieu(bao: dict) -> None:
    """File LA CHIEN LUOC that nhung khong mau nao trong thu vien goi ten duoc.

    Day la con so co gia tri nhat cua ca buoc thu thap, va no de bi nuot nhat:
    mot file bi bo qua vi "khong khop" tron lan ba truong hop khac han nhau -
    (a) tien ich, khong phai chien luoc; (b) chi bao ve duong, khong dat lenh;
    (c) **chien luoc that, dat lenh that, nhung co che cua no CHUA CO template**.

    Chi (c) la viec phai lam. Gop ba loai vao mot con so "22 file khong khop"
    thi khong ai biet nen them template nao - va do dung la cach mot he thong
    hoc duoc bien thanh mot he thong ban ron.
    """
    try:
        from nhan import bien_dich_ung_vien as BD
    except Exception:
        return
    chien_luoc_la = []
    dem = {"chien_luoc": 0, "tien_ich": 0, "chi_bao": 0, "da_co_mau": 0}
    for b in bao.get("bai", []):
        noi_dung = b.get("_noi_dung")
        if not noi_dung:
            continue
        # Ranh gioi la MO VI THE MOI, khong phai "co nhac den giao dich":
        # `CTrade trade;` co trong moi tien ich quan ly lenh (xem
        # `bien_dich_ung_vien.loai_ma_nguon`).
        loai = BD.loai_ma_nguon(noi_dung)
        b["loai_ma"] = loai
        dem[loai] += 1
        if loai != "chien_luoc":
            continue                      # (a) tien ich hoac (b) chi bao
        if BD.do_khop(noi_dung, che_do="ma_nguon"):
            dem["da_co_mau"] += 1
            continue                      # da co template
        chien_luoc_la.append({"tieu_de": b["tieu_de"], "url": b.get("url", ""),
                              "file": b["file"]})
    bao["theo_loai"] = dem
    bao["chien_luoc_chua_co_mau"] = [x["tieu_de"] for x in chien_luoc_la]
    if chien_luoc_la:
        SO.bao_van_de(
            "can_mau_moi_tu_ma_nguon", "VUA",
            f"{len(chien_luoc_la)} file .mq5 DAT LENH THAT nhung co che cua chung "
            "chua co template trong nhan/mau.py - QUANTLAB khong kiem dinh duoc "
            "cho toi khi them template",
            {"file": chien_luoc_la[:12]})
    else:
        SO.dong_van_de("can_mau_moi_tu_ma_nguon",
                       "moi chien luoc thu duoc deu co template tuong ung")


#: Sau bao nhieu lan thu lai khong thanh cong thi BO CUOC voi mot dia chi -
#: khong xoa, khong khoa vinh vien (van con la mot ban doc HTML dung duoc cho
#: tang BOC van xuoi), chi ngung goi mang lai cho no moi vong. Neu khong co
#: tran nay, mot URL bi chan vinh vien (vi du bai da bi go) se bi thu MOI VONG
#: `mot_luot()` chay - dung mau "406 URL chet chiem hang doi" da tung xay ra
#: o tang `khong_doc_duoc`.
TRAN_THU_LAI_SAI_LOAI = 3


def _duong_ra_song(chu: str = "https://www.mql5.com/en/code/", giay: int = 12) -> bool:
    """Duong ra toi mql5 con song khong - hoi THANG, khong suy tu so lan hong.

    Phan biet nay la thu duy nhat ngan mot su co mang tam thoi loai vinh vien
    ca mot lop nguon. Xem ghi chu trong `thu_hoi_sai_loai`.
    """
    import requests
    try:
        r = requests.get(chu + "43355", timeout=giay,
                         headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code == 200 and len(r.text) > 5000
    except Exception:
        return False


def go_bo_cuoc_do_mang(in_ra=print) -> int:
    """Xoa dau `sai_loai:N` cho cac URL bi loai trong mot dot MANG HONG.

    Chay sau khi da sua duong ra. Do 13/09: 29 URL bi loai oan vi WARP.
    """
    if not _duong_ra_song():
        in_ra("duong ra VAN HONG - chua go bo cuoc (go bay gio se loai lai)")
        return 0
    n = SO.chay("UPDATE noi_dung SET ket_boc=NULL WHERE ket_boc LIKE 'sai_loai:%'")
    in_ra("da go dau bo cuoc cho %d ban ghi" % n)
    return n


#: Giay nghi giua hai luot tai. Do 13/09: chay 0,3 giay/luot thi mql5 cho qua
#: ~50 luot roi chan ca IP; nghi 8 giay thi di duoc lau hon nhieu. Mot bo thu
#: thap chay hang gio KHONG duoc voi - voi la tu chan duong cua chinh minh.
NHIP_TAI_GIAY = 8.0


def thu_hoi_sai_loai(gioi_han: int = 30, ngan_sach_giay: float = 180.0,
                     nhip_giay: float | None = None) -> dict:
    """Thu tai lai PAYLOAD THAT cho cac `noi_dung` da bi luu SAI LOAI.

    VI SAO CAN HAM NAY (rieng voi `thu_hoi_khong_doc_duoc`, von lam viec voi
    dia chi hong HAN). O day dia chi KHONG hong - no da tra ve 200 va mot dong
    van ban that (trang landing), nen `kieu` cua no la 'khac'/'ma_nguon' chu
    khong phai 'khong_doc_duoc'. Truoc ham nay, mot ban ghi nhu the duoc coi
    la "da doc xong" VINH VIEN - khong con cong nao dua no tro lai hang doi.
    Do 13/09/2026: 983 ban ghi mql5.com/en/code/N dang o trang thai nay, 813
    ban trong so la SAU khi `_doc_dinh_tuyen` da duoc noi day (03/09) - tuc
    khong phai "chua noi day", ma la "noi day roi van that bai IM LANG" (xem
    chu thich o `_lay`, da sua tai chinh ham do).

    Chi quet URL khop `RE_URL_CODE_MQL5` VA thieu dau hieu ma that. Moi lan
    thu KHONG thanh cong duoc dem vao `ket_boc` (`sai_loai:N`) va dung lai o
    `TRAN_THU_LAI_SAI_LOAI` - xem `TRAN_THU_LAI_SAI_LOAI`.
    """
    t0 = time.time()
    ds = SO.nhieu(
        "SELECT id, van_tay, url, tai_lieu_id, van_ban, ket_boc FROM noi_dung "
        "WHERE url LIKE '%mql5.com/%/code/%' AND cach != 'mql5_download' "
        "ORDER BY id DESC LIMIT ?", max(int(gioi_han) * 4, 1))
    bao = {"xem": 0, "khop_mau": 0, "thu_lai": 0, "sua_duoc": 0,
          "bo_cuoc": 0, "van_sai": 0}
    # HOI DUONG RA MOT LAN MOI LUOT, khong phai moi lan that bai.
    #
    # Ban dau goi `_duong_ra_song()` ngay trong nhanh that bai. Hai cai gia:
    # mot luot 40 URL hong se ton them 40 luot HTTP, va - te hon - bai kiem
    # `test_bo_cuoc_sau_TRAN_lan_that_bai_lien_tiep` bong phu thuoc vao MANG
    # THAT, nen no do ngay khi mql5 dang bop toc do. Mot bai kiem don vi phai
    # xanh ke ca khi rut day mang.
    #
    # `None` = chua hoi. Chi hoi khi that su gap that bai dau tien.
    _song = None
    for r in ds:
        if bao["thu_lai"] >= gioi_han or time.time() - t0 > ngan_sach_giay:
            break
        url = r["url"] or ""
        if not re.match(RE_URL_CODE_MQL5, url):
            continue
        bao["xem"] += 1
        if co_dau_hieu_ma_that(r["van_ban"]):
            continue                       # da la ma that, khong co gi de sua
        bao["khop_mau"] += 1
        ket_boc = r["ket_boc"] or ""
        m = re.search(r"sai_loai:(\d+)", ket_boc)
        so_lan_truoc = int(m.group(1)) if m else 0
        if so_lan_truoc >= TRAN_THU_LAI_SAI_LOAI:
            continue                       # da bo cuoc voi dia chi nay
        bao["thu_lai"] += 1
        bai = tai_ma_nguon({"url": url, "tieu_de": ""})
        # KHONG doi hoi `co_dau_hieu_ma_that` o day: `tai_ma_nguon` da tu bao
        # dam noi dung la mot FILE .mq4/.mq5 THAT (theo dung link tai + kiem
        # kich thuoc + giai ma) - do la khac voi ban ghi CU dang xet (van_ban
        # cua landing page). Doi hoi ca marker se loai OAN cac script/tien
        # ich that su khong dat lenh (vi du 17996 "clear chart objects": ma
        # that 1.390 ky tu nhung 0/7 marker, vi no khong co OnTick/OrderSend -
        # phat hien khi do trong phien 13/09, ban dau ham nay tu choi nham no).
        if bai and bai.get("noi_dung"):
            with SO.ket_noi() as cn:
                cn.execute(
                    "UPDATE noi_dung SET kieu='ma_nguon', cach='mql5_download', "
                    "so_ky_tu=?, so_ky_tu_goc=?, van_ban=?, luc=?, da_boc=0, "
                    "ket_boc='sua_boi_thu_hoi_sai_loai' WHERE id=?",
                    (len(bai["noi_dung"]), len(bai["noi_dung"]), bai["noi_dung"],
                     SO.bay_gio(), r["id"]))
            bao["sua_duoc"] += 1
            # Nap lai vao artifact voi noi dung MOI - artifact cu (neu co) ung
            # voi van_tay CU se con lai nhu mot ban ghi rac, chap nhan duoc:
            # no la HTML that su tung doc duoc, khong phai du lieu bia dat.
            try:
                from tru import seeker as SK
                SK._noi_dung_artifact(r["van_tay"])
            except Exception:
                pass
        else:
            bao["van_sai"] += 1
            # MOT SU CO MANG KHONG DUOC DOT HAN MUC THU LAI.
            #
            # Do 13/09/2026, va no da lam mat viec that: Cloudflare WARP dang
            # BAT tren may nay, va mql5.com chan dai IP cua WARP. Suat thu hoi
            # tut 88% -> 24% -> 0/25 va **29 URL hoan toan tot bi day len
            # `sai_loai:3` roi loai VINH VIEN**. Tat WARP thi chinh trang do
            # tra 200 voi 62.851 ky tu.
            #
            # Nen dem lan that bai phai hoi "hong vi NOI DUNG hay vi DUONG
            # RA": chi noi dung moi tinh. Cung y voi `thu_hoi_github`, va cung
            # ho voi luat lon cua du an - khau do hong khong duoc doc thanh
            # ket qua am.
            if _song is None:
                _song = _duong_ra_song()
            if _song:
                moi = so_lan_truoc + 1
                with SO.ket_noi() as cn:
                    cn.execute("UPDATE noi_dung SET ket_boc=? WHERE id=?",
                               (f"sai_loai:{moi}", r["id"]))
                if moi >= TRAN_THU_LAI_SAI_LOAI:
                    bao["bo_cuoc"] += 1
            else:
                bao["mang_hong"] = bao.get("mang_hong", 0) + 1
                if bao["mang_hong"] >= 5:
                    bao["chan_mang"] = True
                    break
        # NHIP THEO HOST, khong phai sleep co dinh trong tien trinh nay.
        # Hai tien trinh cung cao mql5 ma moi cai tu dem nhip cua rieng minh
        # thi tong lai van nhanh gap doi va van bi chan - do 13/09.
        from nhan import ngan_sach as NS
        NS.cho_nhip("www.mql5.com")
    if bao["xem"]:
        SO.ghi_chi_so("ma_nguon_thu_hoi_sai_loai", float(bao["sua_duoc"]), bao)
    return bao


if __name__ == "__main__":
    import json
    SO.khoi_tao()
    r = thu_thap(so_bai=3)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:3000])


# ============================================ THU HOI PAYLOAD TU GITHUB
#
# Cung ho voi `thu_hoi_sai_loai` (mql5) nhung MOT LOP NGUON KHAC va, quan
# trong hon, mot lop DANG VOI TOI DUOC.
#
# Do 13/09/2026:
#   * `mql5.com` **bi chan**: `RemoteDisconnected` qua duong thuong, va **403**
#     qua `dns_vuot`. Cloudflare WARP da BAT SAN ma van chan - tuc ghi chu cu
#     "bat WARP la thong" khong con dung. Suat thu hoi tut 88% -> 24% -> 0/25
#     roi ton kho dung im. Do la `CHUA_DO_DUOC`, khong phai het viec.
#   * `raw.githubusercontent.com` **thong** (200, 0,3 giay), va `toan_van.
#     tu_github` keo ve 40.213 byte ma that tu `smart-money-concepts`.
#   * Trong kho co **2.998 ban ghi github** dang o dang README da go HTML,
#     khong mot dong ma nao.
#
# Nen khi mot duong bi chan, viec dung khong phai la quay vong tren no - la
# di duong con lai. Ham nay lam viec do.

#: Dau hieu MA CHIEN LUOC cho ngon ngu KHONG phai MQL (python/pine/c++).
#: `co_dau_hieu_ma_that` chi biet API cua MQL nen no bao "khong phai ma" cho
#: mot file `smc.py` 40 KB - dung cai bay bo do mu ma lab da gap ba lan.
DAU_HIEU_MA_CHUNG = (
    "def ", "class ", "import ", "strategy.entry", "ta.crossover",
    "self.buy", "SetHoldings", "OrderSend", "OnTick", "#include",
)


def co_dau_hieu_ma_bat_ky(van_ban: str) -> bool:
    vb = van_ban or ""
    return co_dau_hieu_ma_that(vb) or sum(d in vb for d in DAU_HIEU_MA_CHUNG) >= 2


TRAN_THU_LAI_GITHUB = 2

#: Tu khoa trong TEN repo/duong dan cho biet no co dinh den giao dich khong.
#: Chi doc TEN - khong ton mot luot API nao, trong khi tran la 60 luot/gio.
TU_KHOA_GIAO_DICH = (
    "trad", "forex", "mql", "metatrader", "strategy", "backtest", "quant",
    "indicator", "candle", "ohlc", "ticker", "stock", "crypto", "algo",
    "finance", "market", "invest", "signal", "-ea", "_ea", "bot", "price",
    "fx", "option", "future", "hedge", "portfolio", "trend", "scalp",
)


def _lien_quan_giao_dich(url: str) -> bool:
    u = (url or "").lower()
    return any(t in u for t in TU_KHOA_GIAO_DICH)


def han_muc_github() -> dict:
    """Con bao nhieu luot API GitHub.

    DO 13/09/2026: khong co token thi tran la **60 luot/GIO**. `tu_github`
    dung `api.github.com/.../git/trees` de liet ke file, nen moi repo an it
    nhat mot luot - 2.998 repo trong kho se can ~50 GIO cho rieng viec liet ke.

    Day la mot tran THAT, khong phai mot loi, va no phai duoc DOC RA chu khong
    de cho bo thu hoi cao den khi het luot roi that bai im lang (dung ho voi
    "het quota API -> me boc chay 2 giay -> bao 0/20 co che").

    Dat `GITHUB_TOKEN` thi tran len **5.000/gio** - hon 83 lan.
    """
    import os
    import requests
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    h = {"Authorization": "Bearer " + tok} if tok else {}
    try:
        r = requests.get("https://api.github.com/rate_limit", headers=h,
                         timeout=15).json()
        c = (r.get("resources") or {}).get("core") or {}
        return {"tran": c.get("limit"), "con_lai": c.get("remaining"),
                "co_token": bool(tok)}
    except Exception as e:
        return {"loi": repr(e)[:120], "co_token": bool(tok)}


def thu_hoi_github(gioi_han: int = 30, ngan_sach_giay: float = 240.0,
                   in_ra=print) -> dict:
    """Tai MA THAT cho cac ban ghi github dang chi co README.

    Tra bang dem. `chan_mang` = True nghia la duong ra hong chu khong phai het
    viec - cho goi biet de DUNG chu khong quay vong (bai hoc 406 URL chet).
    """
    import time as _t
    from nhan import toan_van as TV
    t0 = _t.time()

    # HAN MUC TRUOC, KHONG CAO MU. Het luot thi `tu_github` tra None cho MOI
    # repo, va bang dem se doc y het "kho github khong co ma nao" - mot ket
    # luan am tinh sinh ra tu mot cai tran.
    hm = han_muc_github()
    con = hm.get("con_lai")
    if isinstance(con, int) and con < 5:
        return {"xem": 0, "thu_lai": 0, "sua_duoc": 0, "het_han_muc": True,
                "han_muc": hm, "giay": 0.0,
                "ly_do": "con %s/%s luot API GitHub - dat GITHUB_TOKEN de len "
                         "5.000/gio" % (con, hm.get("tran"))}
    if isinstance(con, int):
        gioi_han = min(gioi_han, max(con - 2, 1))
    # XEP THEO DO LIEN QUAN, KHONG THEO id.
    #
    # Do 13/09/2026: trong 3.270 ban ghi github cua kho, **2.257 (69%) co ten
    # repo khong dinh dang gi den giao dich** (`ZenBerry/skydive`,
    # `shishutu-manager`, `static-web-apps-testing-org/...`). Voi tran API 60
    # luot/GIO, cao theo `id DESC` nghia la dot gan het ngan sach vao rac roi
    # ket luan "kho github khong co ma nao".
    #
    # Loc bang TEN URL chu khong bang noi dung: ten co san trong bang, khong
    # ton mot luot API nao de biet.
    ds = SO.nhieu(
        "SELECT id, url, van_ban, ket_boc FROM noi_dung "
        "WHERE url LIKE '%github.com/%' AND (cach IS NULL OR "
        "cach NOT LIKE 'github_payload%') ORDER BY id DESC LIMIT ?",
        max(int(gioi_han) * 40, 400)) or []
    ds.sort(key=lambda r: 0 if _lien_quan_giao_dich(r["url"]) else 1)
    ds = ds[:max(int(gioi_han) * 4, 1)]
    bao = {"xem": 0, "thu_lai": 0, "sua_duoc": 0, "da_co_ma": 0,
           "bo_cuoc": 0, "that_bai": 0, "chan_mang": False}
    lien_tiep_hong = 0
    for r in ds:
        if bao["thu_lai"] >= gioi_han or _t.time() - t0 > ngan_sach_giay:
            break
        bao["xem"] += 1
        if co_dau_hieu_ma_bat_ky(r["van_ban"] or ""):
            bao["da_co_ma"] += 1
            continue
        kb = str(r["ket_boc"] or "")
        m = re.search(r"github_payload:(\d+)", kb)
        if m and int(m.group(1)) >= TRAN_THU_LAI_GITHUB:
            bao["bo_cuoc"] += 1
            continue
        bao["thu_lai"] += 1
        from nhan import ngan_sach as NS
        NS.cho_nhip("api.github.com")     # 60 luot/GIO khi khong co token
        try:
            kq = TV.tu_github(r["url"], so_file=4)
        except Exception:
            kq = None
        vb = (kq or {}).get("van_ban") or ""
        if len(vb) > 500 and co_dau_hieu_ma_bat_ky(vb):
            with SO.ket_noi() as cn:
                cn.execute(
                    "UPDATE noi_dung SET van_ban=?, so_ky_tu=?, kieu='ma_nguon',"
                    " cach=?, da_boc=0 WHERE id=?",
                    (vb, len(vb), (kq.get("cach") or "github_payload")[:80],
                     r["id"]))
            bao["sua_duoc"] += 1
            lien_tiep_hong = 0
        else:
            bao["that_bai"] += 1
            lien_tiep_hong += 1
            n = int(m.group(1)) + 1 if m else 1
            with SO.ket_noi() as cn:
                cn.execute("UPDATE noi_dung SET ket_boc=? WHERE id=?",
                           ("github_payload:%d" % n, r["id"]))
            # DUONG RA HONG khac HET VIEC - nhung phai PHAN BIET duoc, khong
            # duoc suy tu so lan hong lien tiep.
            #
            # Ban dau o day viet `lien_tiep_hong >= 8 -> chan_mang = True`. Do
            # 13/09 ngay sau do: tam repo hong lien tiep la `ZenBerry/skydive`,
            # `Ren1116/shishutu-manager`, `static-web-apps-testing-org/...`,
            # `Devozitt/Schedule-` - tuc **repo khong lien quan giao dich**,
            # va `tu_github` tra None hoan toan DUNG. Bo do do bien mot ket qua
            # am tinh THAT thanh mot `CHUA_DO_DUOC` gia.
            #
            # Day la cai bay "hieu chuan cong hai chieu" nhin tu chieu con lai:
            # mot cong bao hong khi khong hong cung vo dung nhu mot cong khong
            # bao gio hong. Nen nay hoi THANG duong mang, khong suy dien.
            if lien_tiep_hong >= 8:
                hm2 = han_muc_github()
                con2 = hm2.get("con_lai")
                if hm2.get("loi") or (isinstance(con2, int) and con2 < 3):
                    bao["chan_mang"] = True
                    bao["han_muc"] = hm2
                    in_ra("  duong ra HONG that (%s) -> dung" % hm2)
                    break
                lien_tiep_hong = 0   # mang van tot: chi la repo khong lien quan
    bao["giay"] = round(_t.time() - t0, 1)
    bao["han_muc"] = hm
    return bao
