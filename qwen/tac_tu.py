# -*- coding: utf-8 -*-
"""tac_tu.py - Tac tu LangGraph. qwen DOC ket qua va VIET, khong cham va khong chay.

## Ba luc no duoc goi

    mo_dau_ngay()      dau moi ngay - doc ban giao + bang, noi hom nay lam gi
    doc_ket_qua(ma)    ngay sau khi mot viec chay xong - doc so, viet nhat ky
    viet_bao_cao()     cuoi ngay - gop nhat ky thanh BAO_CAO_<ngay>.md nhap

Ba luc nay la CO DINH. Khong co vong lap "qwen tu nghi tiep theo lam gi" - da do
duoc rang mot LLM khong bo nho ngoai se lap lai viec cu va chon viec de.

## Cau he thong

Nguyen khoi "nap boi canh" trong PROMPT_QWEN.md, cong ranh gioi vai tro, cong
nam cau tu kiem. Viet lai o day chu khong doc file: neu ai sua PROMPT_QWEN.md
theo huong khac thi tac tu van phai giu dung luat cua no.
"""
from __future__ import annotations

import time

from . import cau_hinh as CH
from . import cong_cu as CC
from . import mo_hinh as MH

HE_THONG = """Ban la qwen, dang chay tiep du an nghien cuu dinh luong "The Brain"
tai C:\\Users\\SV STORE\\Downloads\\Research SP500\\lab, khi chu du an het token Claude.

MUC TIEU DU AN: tim he giao dich thang MUA-GIU o CUNG muc sut giam, kiem bang
MT5 Strategy Tester tren du lieu XM that.

VAI CUA BAN - doc ky, day la ranh gioi cung:
- Ban DOC ket qua va VIET nhat ky/bao cao. Ban DE XUAT viec.
- Ban KHONG cham dat/am - `qwen/cong.py` cham bang code, ban chi doc lai va giai thich.
- Ban KHONG tu phong lenh. Viec chay tu bang NHIEM_VU.json.
- Vi sao: da do duoc, LLM dien truong `co_che` cho 48 khai bao thi tham dinh bac
  41, rong cuu 3. Ti le do khong dung duoc cho mot cong.

BA TRANG THAI, KHONG PHAI HAI. Day la luat quan trong nhat cua du an:
    DAT           do duoc va vuot nguong
    AM            do duoc va khong vuot nguong
    CHUA_DO_DUOC  khau do bi hong, chua noi duoc gi
Lich su lab day nhung lan mot khau HONG doc y het ket qua am: hang doi bi 406 URL
chet chiem thi lan boc bao "het ton kho" khi kho con 4.560 tai lieu; het quota API
thi me boc chay 2 GIAY roi bao "0/20 co che". TUYET DOI khong viet "khong co edge"
cho mot khau chua chay duoc.

NAM CAU TU KIEM - tra loi duoc het thi moi duoc viet mot ket luan:
1. Cac dong trong bang co GIONG HET NHAU khong? Giong = tham so khong vao duoc he.
2. Con so nay trong mau hay ngoai mau? Tham so chon o dau?
3. Co moc mua-giu trong cung lan chay khong? O CUNG sut giam chu?
4. So LENH co du khong? Duoi 25 lenh moi doan = chua do duoc.
5. Neu am: am THAT hay CHUA CHAY DUOC? Bang chung dau?

BAY DA SAP THAT - kiem truoc khi tin so nao:
- Cot ket qua giong het nhau = tham so khong co tac dung (dau hieu chung cua 3 loi
  khac nhau trong mot phien).
- Model=1 che ra lai gia 12 lan khi TP < 2x bien do nen M1.
- Optimization=2 la thuat di truyen, bo sot co che. Luon dung =1.
- Phi qua dem 1,56 bps/dem DAT HON spread 0,98. Chan BAN duoc TRA +0,18.
- MT5 don bar NGAY vao khung nho khi thieu du lieu, khong bao loi. H1 chi co tu 2016.
- EA nhieu-slot co the lam lech so - CHUA TRUY RA.

CACH VIET: tieng Viet, ngan, di thang van de. Moi bang so phai co SO LENH.
Khong viet dai dong. Khong khen. Neu khong chac thi noi la khong chac."""


def _tac_tu(cong_cu=None):
    from langchain.agents import create_agent
    c = CH.nap()
    return create_agent(model=MH.chat(c), tools=cong_cu or CC.BO_CONG_CU,
                        system_prompt=HE_THONG)


def hoi(nhac: str, so_vong: int = 12) -> str:
    """Chay tac tu mot luot. Tra ve van ban cuoi cung."""
    try:
        g = _tac_tu()
        r = g.invoke({"messages": [{"role": "user", "content": nhac}]},
                     {"recursion_limit": so_vong * 2})
        tin = r["messages"][-1]
        return (getattr(tin, "content", "") or "").strip()
    except Exception as e:
        return "!! tac tu loi: %s: %s" % (type(e).__name__, str(e)[:300])


# ------------------------------------------------------------------ ba luc
def mo_dau_ngay(ngay: int) -> str:
    return hoi(
        "Hom nay la ngay %d cua dot chay. Goi `xem_bang_viec` va `doc_ban_giao`, "
        "roi viet 4-6 dong: hom nay se do duoc cai gi, va viec nao dang la nut that. "
        "Neu thay viec nao trong bang da thua (vi ket qua truoc da tra loi no roi) "
        "thi noi ro. Khong goi qua 5 cong cu." % ngay)


def doc_ket_qua_viec(ma: str, viec: dict, ket_cong: dict) -> str:
    return hoi(
        "Viec `%s` (%s) vua chay xong. Cong cua he da cham: **%s** - ly do: %s. "
        "So do duoc: %s.\n\n"
        "Hay: (1) goi `doc_ket_qua('%s')` de xem log va con so; (2) neu co file ra "
        "thi goi `doc_file_bao_cao` doc no; (3) goi `ghi_nhat_ky('%s', ...)` viet "
        "2-4 cau: con so nay sinh ra tu bao nhieu phep thu, no co dinh bay nao khong, "
        "va no doi gi trong buc tranh chung. (4) Neu ket qua nay mo ra mot viec ro "
        "rang tiep theo thi goi `de_xuat_viec` MOT lan. Khong goi qua 6 cong cu."
        % (ma, viec.get("ten", ""), ket_cong.get("ket"), ket_cong.get("vi_sao"),
           ket_cong.get("so"), ma, ma))


def viet_bao_cao(nhat_ky: list, bang_chu: str) -> str:
    muc = "\n".join("- [%s] %s: %s" % (d["luc"][5:16], d["ma"], d["van"])
                    for d in nhat_ky[-40:])
    return hoi(
        "Viet BAO CAO cho hom nay bang Markdown tieng Viet. Day la nhat ky cac viec "
        "da chay:\n\n%s\n\nVa day la bang viec:\n\n%s\n\n"
        "Bo cuc bat buoc:\n"
        "## Mot doan doc la hieu ca ngay  (5-10 dong: phat hien lon nhat, va cai gi "
        "lat nguoc ket luan cu)\n"
        "## Bang so  (moi dong PHAI co so lenh; ghi ro DAT / AM / CHUA DO DUOC)\n"
        "## Viec tiep theo  (xep theo gia tri tren moi gio may)\n"
        "## Vuong mac con lai  (cai gi biet la chua dung nhung chua sua)\n\n"
        "Chi tra ve Markdown, khong goi cong cu nao." % (muc or "(chua co)", bang_chu),
        so_vong=3)


def kiem() -> str:
    """Tu kiem tac tu goi duoc cong cu khong. Chay: python -m qwen.tac_tu"""
    t = time.time()
    r = hoi("Goi `xem_bang_viec` mot lan roi noi cho toi biet co bao nhieu viec "
            "chua chay. Tra loi mot cau.")
    return "%s\n(%.1fs)" % (r, time.time() - t)


if __name__ == "__main__":
    import sys
    from . import bang_viec as BV
    from . import so_tay as ST
    CC.NGU_CANH["so_tay"] = ST.SoTay()
    CC.NGU_CANH["bang"] = BV.BangViec()
    print(kiem())
    sys.exit(0)
