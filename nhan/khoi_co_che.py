# -*- coding: utf-8 -*-
"""khoi_co_che.py - KHO KHOI CO CHE cua cac con bot: moi bot = to hop cac KHOI; khoi dung chung de thu ap cheo.

Chu du an 04/10/2026: *"moi bot se co chien luoc va cach quan tri cung nhu tinh dac sac khac nhau. Muc tieu
cua the brain la boc tach duoc co che / chien luoc hoac yeu to dac sac cua cac con bot de thu ap dung cheo
hoac ket hop them vao cac he thong va ea sau nay."*

Mot KHOI la mot manh co che nho, ten rieng, co the do tu lich su lenh (dau van tay) va co the cai vao he luoi
cua ta (trang thai `engine`). Mot BOT la danh sach khoi + muc bang chung cua tung khoi:

    ma_nguon   chinh ta viet (he luoi cua ta)        deals   (CHI do `ho_so_bot` ghi - khong nam o day)
    knob       ten/gia tri tham so trong bo `.set`   video   loi tac gia / nguoi trinh bay trong video
    thong_bao  thong bao cua chu bot                 gia_thuyet  ta suy ra tu cac su kien khac (CHUA ai noi)

Day la KIEN THUC TRUOC KHI CO SO LIEU (bot la hop den .ex4/.ex5, khong co ma nguon). Bang chung that den tu
`nhan/ho_so_bot.py` (doc lich su lenh cua tester); no doi chieu voi `BOT[...]['khoi']` o day: xac nhan / bac bo /
khoi moi. Khong ghi nguoc vao file nay - de con thay duoc "tin gi truoc, do duoc gi sau".

Cac cau hoi file nay tra loi (khong phai tai lieu tay - `python -m nhan.khoi_co_che --viet` sinh lai
`tai_lieu/KHO_CO_CHE_BOT.md`, test so sanh de tai lieu khong bao gio cu):
  * `ma_tran()`            bot x khoi (muc bang chung)
  * `khoang_trong_engine()` khoi nao chua co trong engine luoi cua ta, xep theo so bot dung + co o bot song sot
  * `dac_sac_theo_bot()`   khoi it bot dung (<= 2) = yeu to DAC SAC cua tung bot
  * `de_xuat_ap_cheo()`    khoi nao nen thu ghep vao he luoi cua ta truoc (thu tu + ly do)
  * `loai_tu_ten_tham_so()` phan loai tham so `.set` theo TEN vao khoi (de doc bo .set)

Khong quyet dinh gi ve tien: day la ban do. Dat/Am van do `nhan/cham_diem` + so tay `nc.db`.
"""
from __future__ import annotations

import dataclasses
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PHIEN_BAN = "1"
LAB = Path(__file__).resolve().parent.parent
TAI_LIEU = LAB / "tai_lieu" / "KHO_CO_CHE_BOT.md"

# ============================================================== 1. NHOM VA TRANG THAI
NHOM = {
    "VAO": "VAO LENH DAU - khi nao mo chuoi",
    "TANG": "TANG VI THE / LUOI - them lenh the nao",
    "LOT": "LOT - lot moi lenh va tran",
    "THOAT": "THOAT / CHOT - dong chuoi bang cach nao",
    "BAO_VE": "BAO VE / CAT LO / HOA VON",
    "LOC": "BO LOC / LICH - luc nao khong choi",
}

#: Engine luoi cua ta (`nhan/luoi.py` + nhan C + `ea_LuoiDayDu.mq5`) co khoi nay khong.
ENGINE = {
    "co": "co (engine mo phong duoc, da co test)",
    "mot_phan": "mot phan (gan dung, chua dung y het)",
    "chua": "chua (can them vao luoi.py + nhan C + EA)",
    "ngoai": "ngoai (can nguoi / chi bao ngoai - khong mo phong tu lich su)",
}

#: Muc bang chung TINH (thu tu tin cay giam dan). `deals` do `ho_so_bot` ghi, khong nam trong du lieu tinh.
MUC = {
    "ma_nguon": "N",
    "knob": "K",
    "thong_bao": "T",
    "video": "V",
    "gia_thuyet": "G",
}
MUC_GIAI_THICH = {
    "ma_nguon": "N = ma nguon cua ta (he luoi.py)",
    "knob": "K = ten/gia tri tham so trong bo .set cua tac gia",
    "video": "V = loi tac gia / nguoi trinh bay trong video (phu de tu dong, co the nhan sai)",
    "thong_bao": "T = thong bao cua chu bot (nhom Telegram)",
    "gia_thuyet": "G = ta suy ra, chua ai noi (can lich su lenh moi chot)",
}


@dataclass(frozen=True)
class Khoi:
    ma: str                    # ten ngan snake_case
    nhom: str                  # khoa cua NHOM
    ten: str                   # ten ngan tieng Viet khong dau
    mo_ta: str                 # no la gi (1-2 cau)
    tham_so: tuple             # nui nao chinh (ten tham so cua bot / cua luoi.ThamSo)
    dau_van_tay: str           # no hien ra the nao trong lich su lenh
    kiem: str | None           # ten phep do trong `ho_so_bot.PHEP_DO` (None = khong do duoc tu lenh)
    engine: str                # khoa cua ENGINE
    engine_ghi_chu: str        # cu the: truong ThamSo nao / thieu gi
    ap_cheo: str               # ghep vao he khac the nao + dieu can do
    rui_ro: str                # cai gi co the sai
    truong_engine: tuple = ()  # truong `luoi.ThamSo` thuc hien khoi nay (engine co / mot_phan) hoac da khai bao chua cai dat


def _k(ma, nhom, ten, mo_ta, tham_so, dau_van_tay, kiem, engine, engine_ghi_chu, ap_cheo, rui_ro) -> Khoi:
    return Khoi(ma, nhom, ten, mo_ta, tuple(tham_so), dau_van_tay, kiem, engine, engine_ghi_chu, ap_cheo, rui_ro)


# ============================================================== 2. KHOI
KHOI_DS: list[Khoi] = [
    # ------------------------------------------------------------ VAO
    _k("vao_ngay_lap_tuc", "VAO", "Vao ngay, khong cho tin hieu",
       "Mo lenh dau ngay khi bat bot hoac ngay sau khi chuoi truoc dong (Buy, Sell hoac ca hai); khong dung chi bao.",
       ("chieu: mua | ban | hai chieu", "tre sau khi chuoi truoc dong"),
       "Chuoi moi bat dau cung phut / cung bar voi luc chuoi cu dong; gio vao khong theo mot chi bao nao.",
       "vao_lai", "co", "luoi.chay mo tang 1 o dau bar khi khong co ro dang song (cho_lui = 0).",
       "Khoi nen: moi he luoi cua ta dung no. Thay no bang diem vao co dieu kien (RSI, tam gia ngay...) de xem "
       "loc diem vao co them ky vong khong.",
       "Vao ngay luc thi truong dang chay manh mot chieu = chuoi sau ngay tu dau."),
    _k("vao_tay_roi_dca", "VAO", "Nguoi vao lenh dau, bot lo phan sau",
       "Lenh dau do nguoi dat (hoac che do manual / magic 0); bot chi lo them lenh, TP, trailing.",
       ("magic 0 = tay",),
       "Khong quan sat duoc tu lich su lenh: lenh dau khong theo quy luat nao; chi thay phan bot lam (luoi, TP).",
       None, "ngoai", "Can mot nguoi hoac mot luat vao; thay bang khoi VAO co dieu kien de mo phong.",
       "Thay 'nguoi' bang mot luat vao do duoc (vd 3 khung SSL cua HandDCA, hoac luat tim bang tim_quy_luat) roi thu "
       "phan quan ly cua bot nay.",
       "Bot khong co phan vao: ket qua phu thuoc hoan toan nguoi dung, khong the tu chay."),
    _k("vao_rsi_qua_ban", "VAO", "Vao khi RSI ngan han qua ban",
       "Mua khi RSI chu ky ngan (vd 4) tren khung nho (M5) xuong duoi nguong (vd 15); moi lan co tin hieu la them mot lenh.",
       ("rsi_chu_ky", "khung", "nguong_vao"),
       "Lenh mo o bar ngay sau khi RSI cat nguong; nhieu lenh cung chieu mo lien tiep khi RSI van thap; khoang cach "
       "gia giua cac lenh khong deu.",
       "dieu_kien_vao", "chua",
       "luoi.py khong co tin hieu vao; DSL ngu_phap co rsi nhung chi cho lenh don, khong cho chuoi nhoi.",
       "Thu lam cua vao cho he luoi cua ta: thay 'vao ngay' bang 'vao khi RSI(4) < 15' tren AUDCAD M15 va so voi vao ngay.",
       "Chi mua + nhoi: xu huong giam dai = ket ca chuoi, khong co SL (theo video)."),
    _k("vao_tam_gia_ngay", "VAO", "Vao theo 'tam gia' = gia mo cua ngay",
       "Lay gia mo cua ngay lam moc; Sell khi gia len qua tam X, Buy khi gia xuong duoi tam X (danh nguoc xu huong); "
       "triet ly 'choi SAU bao': doi gia lech 30-40 gia roi moi tha.",
       ("khoang lech vao (3-30 gia)", "buy_on / sell_on"),
       "Lenh dau cua ngay cach gia mo cua ngay mot khoang gan co dinh; Sell nam tren moc, Buy nam duoi moc.",
       "dieu_kien_vao", "chua", "Can gia mo cua ngay: luoi.py chua co dac trung nay.",
       "Khoang cach toi gia mo cua ngay la mot dac trung moi cho tim_quy_luat; thu lam dieu kien vao cua he luoi.",
       "Ngay co 'bao' (vang di 40-60 gia trong 5-10 phut khong hoi): chuoi ket."),
    _k("vao_chi_bao_ngoai", "VAO", "Doc tin hieu tu chi bao ben ngoai",
       "Bot doc buffer cua mot chi bao (so buffer cho Buy, so buffer cho Sell) hoac nguoi nhin chi bao roi vao tay "
       "(SSL ba khung cua HandDCA).",
       ("ten chi bao", "buffer buy", "buffer sell"),
       "Khong thay chi bao tu lich su lenh; chi thay lenh vao thua thot khong theo nhip luoi.",
       None, "ngoai", "Chi bao cu the khong co san.",
       "Ma 'SSL ba khung dong cung mau' co the viet thanh dac trung de thu bang tim_quy_luat.",
       "Chi bao ve lai (repaint): vao theo nen chua dong la sai (loi nguoi trinh bay)."),
    _k("vao_theo_ma", "VAO", "Vao theo duong trung binh (MA / EMA)",
       "Chon huong vao lenh theo vi tri gia so voi MA (vd EMA 46) hoac che do 'theo entry' / 'theo MA'.",
       ("chu_ky_ma", "khung"),
       "Chieu lenh dau khop dau cua (gia - MA) tai bar vao.",
       "dieu_kien_vao", "chua", "luoi.py khong co tin hieu vao.",
       "Dac trung (gia - MA) / ATR co the dung lam bo loc chieu cho che do mot_chieu.",
       "MA tre: vao muon khi thi truong dao chieu nhanh."),
    _k("vao_theo_xu_huong", "VAO", "Danh theo xu huong (trend-following)",
       "Vao cung chieu voi xu huong (khung H1 tro len), nhoi them khi xu huong tiep tuc; tac gia canh bao sideway la ke thu.",
       ("khung", "luat xu huong (khong noi)"),
       "Cac lenh cung chieu mo khi gia di CUNG chieu loi (Buy: lenh sau mo o gia cao hon), nguoc voi luoi gian cach.",
       "them_khi_hoi", "chua", "luoi.py chi co luoi nguoc xu huong.",
       "Khoi doi nghich voi luoi: 'luoi khi sideway, theo trend khi co trend' can bo loc che do (loc_adx_atr / loc_sideway_nen).",
       "Sideway: bi cuon lenh lien tiep."),
    _k("vao_lai_sau_cho_lui", "VAO", "Cho gia lui roi moi vao lai (khoi CUA TA)",
       "Sau khi mot ro chot TP khong mo lai ngay ma cho gia lui them N pip nguoc chieu roi moi vao.",
       ("cho_lui (pip)",),
       "Khoang cach thoi gian va gia giua chuoi vua dong va chuoi moi lon hon 0 va gan co dinh.",
       "vao_lai", "co", "luoi.ThamSo.cho_lui.",
       "Da do tren EURCAD (+7,9% -> +12,1%/nam, tester that). Thu tren moi ma khi ghep voi khoi cua bot khac.",
       "Bo lo nhip hoi nhanh sau chot neu cho_lui qua lon."),
    # ------------------------------------------------------------ TANG
    _k("hai_chieu_doc_lap", "TANG", "Hai chuoi Buy va Sell chay doc lap",
       "Chuoi Buy va chuoi Sell cung song, moi chuoi co luoi va TP rieng; lenh Sell khong cat lo lenh Buy.",
       ("kieu: hai chieu",),
       "Co luc nam ca Buy lan Sell cung mo (tai khoan hedging); nhieu luc chi mot chieu.",
       "huong", "co", "luoi.ThamSo.che_do = hai_chieu.",
       "Phan lon bot luoi chay hai chieu; so voi mot_chieu tren cung ma.",
       "Trend manh: chuoi nguoc trend am sau, chuoi thuan trend chot lai nho, am rong tang theo thoi gian."),
    _k("mot_chieu", "TANG", "Chi mot chieu (chi Buy hoac chi Sell)",
       "Chi danh mot chieu (thuong chi Buy vang theo y 'vang dai han tang'); xu ly xong chuoi roi moi sang chuoi khac.",
       ("chieu: mua | ban",),
       "Tu 95% lenh tro len cung mot chieu.",
       "huong", "co", "luoi.ThamSo.che_do = mua | ban.",
       "Chi nen thu tren tai san co xu huong dai han ro (vang, chi so); don bay thap hon vi khong co chuoi doi khang.",
       "Xu huong nguoc dai = ket ca chuoi (khong co ve phia doi dien)."),
    _k("luoi_gian_cach_deu", "TANG", "Luoi gian cach deu",
       "Moi lenh them cach lenh truoc dung mot buoc co dinh (pip hoac gia).",
       ("buoc", "tran so lenh"),
       "Khoang cach gia giua cac lenh lien tiep gan nhu hang so (CV nho).",
       "buoc_theo_bac", "co", "luoi.ThamSo.buoc.",
       "Khoi nen; so sanh voi buoc gian dan va buoc theo bac tren cung ma.",
       "Buoc nho + lot tang = lenh day, am sau rat nhanh."),
    _k("luoi_buoc_gian_dan", "TANG", "Buoc gian dan theo he so",
       "Buoc thu k = buoc * he_so^(k-1) co tran; he_so > 1 = song lau hon khi xu huong, < 1 = day dan.",
       ("buoc", "he_so_buoc", "buoc_tran"),
       "Khoang cach lien tiep tang theo ti le co dinh (1,05-1,2) cho den khi chay vao tran.",
       "buoc_theo_bac", "co", "luoi.ThamSo.he_so_buoc, buoc_tran.",
       "Black Dragon (x1,2) va CCBSN (InpDistanceMulti) deu dung: thu cung gia tri tren AUDCAD.",
       "Gian qua nhanh: luoi that thua nhieu khi gia hoi khong du xa de chot."),
    _k("luoi_buoc_theo_bac", "TANG", "Buoc theo bac (doi buoc o moc so lenh)",
       "Buoc doi theo so lenh: bac 1 cho lenh 2-9, bac 2 tu lenh 10, bac 3 ... (CCBSN Distance1-4, NuTi 'quang').",
       ("so_lenh_moc_k", "buoc_bac_k"),
       "Khoang cach gia giua cac lenh doi gia tri o nhung chi so lenh co dinh (vd lenh 10, 20, 30).",
       "buoc_theo_bac", "chua", "luoi.py chi co mot buoc + he so; chua co bang buoc theo tang.",
       "Khoi DE THU DAU: CCBSN la bot song sot duy nhat va dung 4 nac buoc; them vao luoi.py (+C +EA) la viec ro rang.",
       "Nhieu tham so = de khop nhieu: phai quet cao nguyen, khong cai gai."),
    _k("luoi_theo_nen_moi", "TANG", "Chi them lenh khi mo nen moi",
       "Mot nen chi duoc them toi da mot lenh (tranh don lenh khi gia chay nhanh trong mot nen); NuTi DCA theo nen.",
       ("khung nen",),
       "Thoi gian mo cac lenh them trung dau nen; khong co hai lenh them cung mot bar.",
       "nhip_them_lenh", "chua", "Engine them lenh theo gia trong bar; chua co rang 'toi da 1 lenh / bar'.",
       "De do: them tham so 'moi bar toi da 1 lenh'; xem co cat duoc DD luc tin manh khong.",
       "Them cham luc gia da di xa: gia trung binh kem hon."),
    _k("luoi_day_khi_gia_hoi", "TANG", "Gia hoi thi nhoi them lenh, keo TP lai gan",
       "Khi gia di nguoc roi hoi lai, bot van them lenh (luoi day them) va keo TP ve gan: ket thuc chuoi som hon (KawKaw).",
       ("buoc them khi hoi", "khoang TP keo lai"),
       "Co lenh them mo o gia TOT hon lenh them truoc (gia da hoi); TP chuoi gan gia trung binh.",
       "them_khi_hoi", "chua", "luoi.py chi them lenh khi gia di nguoc them.",
       "Giam thoi gian chuoi nhung tang lot trung binh; thu tren chuoi sau.",
       "Them lenh o gia hoi ma gia quay dau = lot nang them o gia xau."),
    _k("them_lenh_theo_tin_hieu", "TANG", "Moi lan co tin hieu la them mot lenh",
       "Khong co khoang cach co dinh: moi tin hieu vao (vd RSI < 15 tren M5) them mot lenh cung chieu, ke ca dang am "
       "(GoldHunter: hang tram lenh).",
       ("tin hieu", "tran lenh (khong noi)"),
       "Khoang cach gia giua lenh them khong deu, co the dao chieu (them o gia tot hon hoac xau hon).",
       "them_khi_hoi", "chua", "luoi.py them theo buoc gia, khong theo tin hieu.",
       "Neu tin hieu tot hon luoi co dinh thi lenh them nen nam o 'day nhip' chu khong o moi buoc; so tung thang.",
       "Tin hieu bam day nhieu lan: don lot o gia xau."),
    _k("nhoi_theo_loi", "TANG", "Nhoi them khi dang lai (pyramiding)",
       "Them lenh khi vi the dang lai de an xu huong (NewYear: 'nhoi theo trend', phu de mo ho).",
       (),
       "Lenh them mo o gia THEO huong loi (Buy: gia cao hon lenh truoc).",
       "them_khi_hoi", "chua", "luoi.py khong co nhoi thuan xu huong.",
       "Doi nghich cua luoi: chi hop khi xu huong chay xa.",
       "Dao chieu luc da nhoi nhieu: mat het lai cua chuoi."),
    _k("lenh_doi_ung_stop", "TANG", "Lenh stop doi ung (hedging bang lenh cho)",
       "Sau lenh dau, dat lenh STOP nguoc chieu cach gia mot khoang (350-360 point); khi stop khop thi dat tiep stop "
       "nguoc lai: tao thang bac hedging (Bigmouse).",
       ("khoang_cach_buy_sell", "he_so_lot_tong"),
       "Lenh mo bang BUY STOP / SELL STOP (cot Type trong bang Orders); chieu luan phien; khoang cach gia hang so.",
       "doi_ung", "chua", "luoi.py chi mo lenh thi truong.",
       "Chi dang thu neu do that cho thay lai; ghep voi lot_tong_gap_doi moi co nghia.",
       "36 lenh la 'tai khoan khong con' (loi tac gia trong video)."),
    _k("lenh_doi_ung_sau_n_lenh", "TANG", "Mo lenh doi ung sau N lenh (hedge khi sau)",
       "Khi mot chuoi co N lenh (CCBSN: 5-12), mo them lenh NGUOC chieu voi lot nho co dinh (0,01-0,05) de giam toc do am.",
       ("InpOrders2OpenOpp", "InpLotsOpp", "InpPerLotsOpp"),
       "Co lenh nguoc chieu xuat hien dung khi so lenh cua chuoi doi dien dat so co dinh; lot nho va khong tang.",
       "doi_ung", "chua", "luoi.py hai chuoi chay roi nhau, khong co lenh doi ung trong cung chuoi.",
       "Khoi nen thu SOM vi CCBSN song sot dung no; do bang quet_luoi sau khi them.",
       "Hedge khong dong: neu khong co luat dong, hai chieu cung ket."),
    _k("gong_duong_doi_ung", "TANG", "Gong lenh dang lai de can lenh am",
       "Khong chot lenh dang lai: giu no de bu cho cac lenh am (BNK), den khi chot ca chuoi; SemiHFT giu Buy khi Sell ket.",
       (),
       "Co lenh dang lai bi giu rat lau (lau hon trung vi nhieu lan), chi dong cung luc voi ca chuoi.",
       "gong_duong", "chua", "luoi.py chot theo ca chuoi, khong giu lenh duong rieng.",
       "Giam DD hien thi, khong giam rui ro that neu khong co luat dong; do bang 'lenh nao bi giu bao lau'.",
       "Lenh duong bi giu roi dao chieu: mat het lai da co."),
    # ------------------------------------------------------------ LOT
    _k("lot_phang", "LOT", "Lot phang",
       "Moi lenh trong chuoi cung lot.",
       ("lot",),
       "Lot lenh k = lot lenh 1 voi moi k.",
       "lot_theo_bac", "co", "luoi.ThamSo.kieu_lot = phang.",
       "Khoi an toan nhat; moc so sanh cho moi khoi lot khac.",
       "Phang khong cuu duoc chuoi dai (nhung DD tang cham)."),
    _k("lot_cong", "LOT", "Lot tang cong",
       "Lot lenh k = lot0 + (k-1) * buoc_lot (CCBSN InpPlus 0,01; KawKaw 'lot step add').",
       ("InpPlus", "lot step add"),
       "Lot tang deu cung mot luong moi lenh.",
       "lot_theo_bac", "co", "luoi.ThamSo.kieu_lot = cong.",
       "Hien hon nhan: so tren cung ma.",
       "Chuoi rat dai van phinh lot (tuyen tinh)."),
    _k("lot_nhan", "LOT", "Lot nhan theo he so",
       "Lot lenh k = lot0 * he_so^(k-1), he_so thuong 1,05-1,3 (BlackDragon, BNK 1,2, SemiHFT 1,08, NuTi 1,1, CCBSN 1,18-1,3).",
       ("InpMultiplier", "xlot"),
       "Ti le lot lien tiep gan hang so > 1.",
       "lot_theo_bac", "co", "luoi.ThamSo.kieu_lot = nhan, he_so_lot.",
       "Khoi trung tam cua DCA; do 'do sau toi da song duoc' theo he so.",
       "Luy thua: DD phinh o cuoi chuoi."),
    _k("lot_nhan_theo_bac", "LOT", "He so lot doi theo bac",
       "He so nhan lot thay doi o cac moc so lenh (CCBSN: lenh 10/20/30/40/50 -> he so moi 1,2/1,1/1,05/1,06/1,03; "
       "NuTi quang 2 lot lon tu lenh 10).",
       ("InpOrders2NewMultiplier1-5", "InpNewMultiplier1-5"),
       "Ti le lot lien tiep r_k = lot_k / lot_(k-1) doi gia tri o chi so lenh co dinh.",
       "lot_theo_bac", "chua", "luoi.py chi co mot he so; chua co bang moc -> he so.",
       "Khoi song sot: them vao luoi.py (kieu_lot = bac, bang moc -> he so) roi quet.",
       "Lot cuoi chuoi lon: DD phinh o day."),
    _k("lot_tong_gap_doi", "LOT", "Tong lot mot chieu gap doi chieu kia",
       "Tong lot chieu dang thua luon x2 tong lot chieu doi dien trong 4 lenh dau, tu lenh 5 con x1,6 (Bigmouse).",
       ("he_so_4_dau", "he_so_tu_lenh_5"),
       "Tai moi thoi diem tong lot Buy / tong lot Sell xap xi 2,0 roi 1,6.",
       "lot_theo_bac", "chua", "luoi.py khong co hai chieu noi voi nhau.",
       "Chi co nghia khi di cung lenh_doi_ung_stop.",
       "Tong lot tang rat nhanh (max lot 15 theo tac gia)."),
    _k("lot_fibo", "LOT", "Lot theo day Fibonacci",
       "Lot lenh k theo day Fibonacci (1,1,2,3,5,8...) thay cho nhan (Bigmouse, tac gia chua test).",
       (),
       "Ti le lot lien tiep gan 1,618 sau vai lenh dau.",
       "lot_theo_bac", "chua", "luoi.py khong co.",
       "Toc do tang nam giua nhan 1,3 va nhan doi: so voi nhan 1,6.",
       "Tang nhanh o dau chuoi."),
    _k("lot_nhan_sau_sl", "LOT", "Nhan lot sau moi lan cat lo (martingale lenh don)",
       "Sau moi lenh cat lo, lenh ke tiep nhan doi lot (0,01 -> 0,02 -> 0,04 -> ... 0,32 / 0,64); thang thi ve lot dau "
       "(NewYear, SignalX).",
       ("he so lot nhan 2", "lot toi da"),
       "Lot lenh moi = 2 x lot lenh vua cat lo; ve lot dau sau lenh thang.",
       "lot_theo_bac", "chua", "luoi.py la chuoi luoi, khong co lenh don nhan sau SL.",
       "Chu du an chap nhan martingale (tieu chi: co lai sau phi + maxDD < 80%); thu tren he co tin hieu ro.",
       "Chuoi thua 7 lenh = lot x64: chay tai khoan; win rate thap la tu sat."),
    _k("lot_tu_dong_theo_von", "LOT", "Lot tu dong theo von",
       "Lot lenh dau = so du / n (vd 0,01 cho moi 1000 von).",
       ("auto lot",),
       "Lot dau cua chuoi tang dan theo so du tai luc vao.",
       "lot_theo_von", "chua", "luoi.ThamSo.lot la hang so; lot chot ngoai engine (niem_phong_luoi).",
       "Ket hop voi tran_lot_tong thanh 'lai kep co kiem soat'.",
       "Lai kep cung la thua kep sau chuoi xau."),
    _k("tran_lot_tong", "LOT", "Tran lot",
       "Gioi han tong lot hoac lot lon nhat cua chuoi (Bigmouse 15, NuTi MT5 3, CCBSN InpMaxLots 0,02-2,3).",
       ("InpMaxLots", "max lot"),
       "Lot lon nhat cua cac chuoi dung o mot gia tri (cao nguyen) du chuoi sau.",
       "rui_ro", "chua", "luoi.py khong co tran lot.",
       "Tran lot la cach chan chay tai khoan: thu tran thap + tran so lenh.",
       "Cham tran ma gia van di nguoc: ket o lot lon."),
    _k("tran_so_lenh", "LOT", "Tran so lenh cua chuoi",
       "Ngung them lenh khi chuoi dat N lenh (Bigmouse 36, BlackDragon 99, NuTi 9 / 60 / 100, CCBSN InpMax*Orders 5-1000).",
       ("InpMaxBuyOrders", "InpMaxSellOrders", "max order"),
       "Do sau chuoi bi cat o mot gia tri co dinh (nhieu chuoi dung o N).",
       "chuoi_sau", "co", "luoi.ThamSo.tran_tang.",
       "Khoi nen; quet tran_tang voi cac khoi lot.",
       "Cham tran ma gia van di nguoc: ket o lot lon."),
    # ------------------------------------------------------------ THOAT
    _k("tp_chuoi_tu_gia_tb", "THOAT", "TP ca chuoi tu gia trung binh",
       "Dong ca chuoi khi gia cach gia trung binh X pip (CCBSN InpTPDCA; NuTi quang 2 'hoa von + 0,5 gia'; HandATMX 1 gia).",
       ("InpTPDCA", "tp pip"),
       "Gia dong cach gia trung binh cua chuoi mot khoang hang so (pip); cac lenh cua chuoi dong CUNG LUC.",
       "thoat", "co", "luoi.ThamSo.tp.",
       "Khoi nen cua luoi; thay bang chot theo tien / theo RSI de so.",
       "TP nho: chot thieu khi xu huong that."),
    _k("tp_chuoi_tien", "THOAT", "TP ca chuoi theo tien",
       "Dong ca chuoi khi tong lai (da tru phi) dat X USD, bat ke gia (Bigmouse 5 USD, HandATMX 10 USD, KawKaw, CCBSN).",
       ("tp usd", "chot_tien"),
       "Tien thu cua chuoi luc dong gan hang so trong khi khoang cach gia thay doi.",
       "thoat", "co", "luoi.ThamSo.chot_tien (don vi: tien tren 0,01 lot).",
       "Chuoi dai thi X USD = it pip: thu theo tien vs theo pip.",
       "Chuoi dai chot som: bo phan lai lon cua xu huong."),
    _k("tp_tung_lenh", "THOAT", "TP rieng tung lenh",
       "Moi lenh co TP rieng (CCBSN InpTP, NuTi quang 1 TP don 2 gia, SignalX TP 2 gia); lenh dong rieng khi gia cham.",
       ("InpTP", "tp don"),
       "Cot T/P trong bang Orders khac 0; lenh dong boi [tp] tai dung gia TP; khong dong cung luc ca chuoi.",
       "sl_tp_tung_lenh", "mot_phan", "luoi.py chot ca chuoi; chi co tia_cap (dau + cuoi) gan giong.",
       "TP tung lenh + khong SL = luoi 'ban dai' kieu NuTi quang 1; thu voi 60-100 lenh.",
       "Lenh sau cung ket lai het: khong co co che gom."),
    _k("tp_treo_len", "THOAT", "TP treo len (TP dich dan)",
       "Khi them lenh, TP cua chuoi duoc dich theo (BlackDragon 'TP trailing treo len').",
       (),
       "Cot T/P cua cac lenh trong chuoi doi gia tri moi khi them lenh (can bang Orders co lenh sua).",
       None, "chua", "luoi.py dat TP tu gia trung binh moi lan.",
       "Thuc chat giong tp_chuoi_tu_gia_tb khi TP tinh tu gia tb: co the da nam trong khoi nen.",
       "Kho tach khoi tp_chuoi_tu_gia_tb neu khong co bang lenh sua."),
    _k("thoat_rsi_va_tb_duong", "THOAT", "Thoat khi trung binh duong va RSI vuot nguong",
       "Dong ca chuoi khi gia trung binh cua chuoi dang lai va RSI(4) M5 > 50 (GoldHunter), khong dat TP pip / USD.",
       ("nguong thoat rsi",),
       "Tien thu khi dong khong co cum co dinh; lenh dong luc gia da qua gia trung binh.",
       "thoat", "chua", "luoi.py khong co chi bao.",
       "Thay TP co dinh bang 'thoat khi hoi nhe + RSI het qua ban': thu tren luoi AUDCAD, do chuoi ngan lai bao nhieu.",
       "Chi bao ve lai tre: thoat muon, nha lai."),
    _k("doi_tp_khi_lo", "THOAT", "Doi TP khi chuoi dang lo",
       "Khi lo cua chuoi vuot X% (CCBSN -5 .. -20%), bot ha muc TP xuong (chap nhan chot it hon de thoat som).",
       ("InpUseChangeTPDCA", "InpPerLoss2ChangeTP"),
       "Chuoi sau thoat voi lai nho hon chuoi nong cung loai; TP giam theo do sau cua chuoi.",
       "doi_tp", "chua", "luoi.py TP khong doi theo lo.",
       "Ke thua cho_lui va tia_cap: kieu 'thoat som khi sau'; thu bang quet_luoi.",
       "Chot it o dung luc co the hoi manh."),
    _k("tia_cap_sau_dau", "THOAT", "Tia cap: ghep lenh sau nhat voi lenh dau (khoi CUA TA)",
       "Ghep lenh sau nhat voi lenh dau tien, dong ca cap khi tong lai cua cap >= bien_cap pip (cat ngan thang bac ma "
       "khong cho ca chuoi ve).",
       ("bien_cap", "cap_moi_bar"),
       "Hai lenh (dau va cuoi) dong cung luc truoc phan con lai cua chuoi.",
       "thoat_tung_phan", "co", "luoi.ThamSo.tia_lenh, bien_cap, cap_moi_bar (tu LuoiDoiXung.mq5).",
       "Khoi cua ta; so voi tia_n_lenh_khi_chuoi_dai cua CCBSN / NuTi.",
       "Engine lac quan ~15% o tia lenh (viec #48): so tren tester that."),
    _k("tia_n_lenh_khi_chuoi_dai", "THOAT", "Tia N lenh khi chuoi dai",
       "Khi chuoi co >= N lenh, chot rieng M lenh (nang am hoac thap nhat) den khi lai sau tia >= X USD, phan con lai van "
       "chay (CCBSN Sniper, NuTi 'tia lenh' N=10 M=2 2,5 USD, SemiHFT Buy chot lenh thap nhat truoc).",
       ("InpUseSniper", "InpTPSniper", "InpMoneySniperFull", "InpFirstOrdersSniper", "InpLastOrdersSniper"),
       "Co dot dong CHI MOT PHAN chuoi (so lenh dong cung luc < so lenh dang mo), lap lai nhieu lan trong cung chuoi.",
       "thoat_tung_phan", "mot_phan", "tia_cap_sau_dau ghep 1 cap dau-cuoi; chua co tia M lenh theo N.",
       "Khoi nen thu SOM: CCBSN song sot dung no; mo rong tia_cap thanh tia M lenh khi chuoi >= N.",
       "Tia lenh tot, giu lenh xau: gia trung binh tien ve phia xau."),
    _k("all_sniper", "THOAT", "All Sniper: dong tat ca khi lai X USD sau N lenh",
       "Sau khi chuoi co N lenh (1-55), neu tong lai >= X USD (1-10) thi dong TAT CA: luat thoat an toan cho chuoi dai (CCBSN).",
       ("All Sniper: so lenh", "All Sniper: USD"),
       "Chuoi dai (>= N lenh) dong cung luc voi tong tien nho co dinh (1-10 USD).",
       "thoat", "chua", "luoi.py chot_tien khong doi theo so lenh.",
       "Mot chot_tien bac thang theo do sau chuoi: thu bang quet_luoi.",
       "Chot non voi tien nho: mat truong lai khi chuoi dai hoi manh."),
    # ------------------------------------------------------------ BAO VE
    _k("sl_cung", "BAO_VE", "SL co dinh tung lenh",
       "Moi lenh co cat lo co dinh (NewYear 2.1 SL ~7 gia, SignalX, Bigmouse SL theo RR 1,3).",
       ("sl pip",),
       "Cot S/L khac 0; nhieu lenh dong boi [sl] o khoang cach co dinh.",
       "sl_tp_tung_lenh", "chua", "luoi.py khong co SL tung lenh.",
       "Cong cu cho he lenh don (martingale); khong hop voi luoi khong SL.",
       "Cat lo lien tiep: lot nhan len roi cham SL."),
    _k("cat_lo_theo_tien", "BAO_VE", "Cat lo theo tien (chuoi / tai khoan)",
       "Dong het khi am X USD (Bigmouse 'cat am', NuTi 'shot tai khoan' -300 USD, de tat): bien 'khong cat lo' thanh "
       "'cat lo co tran'.",
       ("cat am USD", "shot tai khoan"),
       "Cum chuoi dong boi [ea] / stopout voi lo gan co dinh -X; hoac tai khoan ve 0.",
       "thoat", "chua", "ThamSo.dung_lo_tong da khai bao nhung KHONG cai dat (luoi.chay tu choi != 0).",
       "Dat tran DD tu truoc (vd 50%) la cach giu maxDD < 80% theo cong cua chu du an.",
       "Cat dung luc day: mat co hoi hoi phuc."),
    _k("thoat_hoa_von_khi_chuoi_dai", "BAO_VE", "Chap nhan hoa von khi chuoi dai",
       "Khi chuoi co N lenh (Bigmouse: 3), bo TP duong va chi dat SL o hoa von: chuoi thoat o 0 thay vi cho lai.",
       ("so lenh kich hoat", "kich hoat hoa von"),
       "Chuoi dai dong boi [sl] voi tien thu ~ 0 (am nho = phi), khong phai TP duong.",
       "hoa_von", "chua", "luoi.py chi thoat o TP duong.",
       "Luat 'cat DD': thu bien N nho / lon tren luoi - doi lai het lai cua chuoi dai.",
       "Cat het co hoi cua chinh chuoi nguy hiem nhat."),
    _k("keo_sl_hoa_von_khi_co_lai", "BAO_VE", "Keo SL ve hoa von khi da co lai",
       "Khi chuoi co >= N lenh va tong lai > X (USD / gia), keo SL ve hoa von cong them delta (HandATMX 3 lenh / 5 USD / "
       "1 gia; NewYear 2.1 lot 0,08 va lai 2 gia; SemiHFT, Bigmouse 2 gia).",
       ("so lenh toi thieu", "nguong lai", "delta"),
       "Chuoi dong boi [sl] voi tien thu duong NHO (xap xi delta) thay vi TP; xuat hien sau chuoi dai.",
       "hoa_von", "chua", "luoi.py khong co SL.",
       "Khoi lap lai o 5 bot: xay mot lan, thu cho moi he luoi.",
       "Quet sat ngay sau khi dat, mat lai tiem nang (tac gia noi)."),
    _k("trailing_stop_chuoi", "BAO_VE", "Trailing stop ca chuoi",
       "Thoat bang trailing stop tu hoa von (SemiHFT: khong co TP chuoi; lai 2 gia tu hoa von thi dich trailing).",
       ("trailing start", "trailing step"),
       "Tien thu khi dong bien thien rong (khong cum), dong boi [sl] o gia cao hon gia trung binh.",
       "hoa_von", "chua", "luoi.py khong co.",
       "Thay TP co dinh bang trailing: thu tren nhung chuoi hoi manh.",
       "Cat qua som neu trailing sat."),
    # ------------------------------------------------------------ LOC
    _k("loc_spread", "LOC", "Loc spread",
       "Khong vao / khong them lenh khi spread vuot X point (CCBSN InpMaxSpread 3-500).",
       ("InpMaxSpread",),
       "Khong thay duoc tu deal (bao cao khong co spread); gian tiep: khong co lenh vao o gio spread rong (qua dem).",
       None, "chua", "luoi.py dung chi phi spread theo mo hinh, khong loc.",
       "Chi phi that cua he luoi (spread rong luc roll-over) la bo loc nhay: thu cho luoi AUDCAD.",
       "Loc qua chat: bo qua nhip vao tot."),
    _k("loc_gio_giao_dich", "LOC", "Loc gio giao dich",
       "Chi cho mo lenh trong cac khung gio (BlackDragon, Bigmouse 'gio mo cua', NewYear 2.1 time trade 1-3, SemiHFT theo "
       "ngay, CCBSN lich ngay / gio).",
       ("gio bat dau", "gio ket thuc", "time trade 1-3 (NewYear 2.1)"),
       "Phan bo gio vao lenh dau khong deu: co gio khong bao gio co lenh.",
       "gio_ngay", "chua", "luoi.py khong loc gio.",
       "Thu loai gio xau (qua dem / tin) cho luoi: dac trung gio da co trong DSL, do bang quet_luoi sau khi them.",
       "Quet gio la cach de cai gai: can kiem tren doan xac nhan."),
    _k("loc_ngay_thu_lich", "LOC", "Loc ngay / thu / lich",
       "Tranh sang thu Hai, toi thu Sau, dau - cuoi thang, cuoi quy, nua cuoi thang 12, ngay le My (loi khuyen tac gia "
       "NuTi); CCBSN co lich.",
       ("lich ngay tranh", "bat / tat loc lich"),
       "Khoang lang (nhieu ngay khong co lenh vao) lap lai theo lich.",
       "gio_ngay", "chua", "luoi.py khong loc ngay.",
       "Gia thuyet kiem duoc bang so lieu dai: cac ngay 'tranh' co that su lam luoi lo? (xem LOI_KHUYEN_VAN_HANH).",
       "Mau nho theo ngay: de cai gai."),
    _k("loc_tin_tuc", "LOC", "Loc tin tuc",
       "Tat khi co tin manh (BlackDragon co nhung chua cau hinh; CCBSN v3.0.6 theo thong bao).",
       ("news filter",),
       "Khong thay duoc tu deal; gian tiep: lenh vao thua quanh gio tin.",
       None, "chua", "luoi.py khong co lich tin.",
       "Can lich tin that (nguon ngoai): chua co trong kho.",
       "Phu thuoc nguon lich."),
    _k("loc_adx_atr", "LOC", "Loc ADX / ATR (do manh xu huong, do bien dong)",
       "Dung ADX hoac ATR de khong vao / khong them lenh khi xu huong qua manh hoac bien dong qua lon (CCBSN v3.0.6 theo "
       "thong bao).",
       ("ADX", "ATR"),
       "Chi thay duoc khi co bar gia: lenh vao thua thot khi ADX cao.",
       None, "chua", "luoi.py khong co bo loc.",
       "Bo loc che do chinh cho luoi: ADX cao = khong luoi. Thu bang quet_luoi neu kho dac trung co adx.",
       "Loc qua chat bo lo moi luoi sau nhip manh (chinh la luc lai lon)."),
    _k("loc_sideway_nen", "LOC", "Loc sideway bang nen",
       "Nhan ra sideway khi 3-4 nen khong thoat duoc vung cua nhau thi tat bot (NewYear, van hanh tay).",
       (),
       "Chi thay duoc khi co bar gia.",
       None, "chua", "luoi.py khong co.",
       "Dung cho he theo xu huong (sideway la ke thu); voi luoi thi nguoc lai.",
       "Do bang mat: kho viet thanh luat."),
    _k("loc_bao_bien_dong", "LOC", "Loc bao bien dong",
       "Bao = di 40-60 gia trong 5-10 phut khong hoi (NuTi): chi tha bot SAU bao (gia da di 30-40 gia).",
       ("ngay thau", "khoang lech"),
       "Chi thay duoc khi co bar gia M1-M5.",
       None, "chua", "luoi.py khong co.",
       "Dac trung bien dong ngan (range 5-10 phut / ATR) lam bo loc vao / them lenh; xem DD co giam khong.",
       "Dinh nghia 'bao' theo cam tinh."),
    _k("loc_dca_tu_lenh_n", "LOC", "Loc DCA tu lenh thu N",
       "Tu lenh thu N tro di (1-25) moi them lenh neu bo loc (khong ro bo loc nao) cho phep (CCBSN InpUseFilterDCA).",
       ("InpUseFilterDCA",),
       "Sau lenh N, nhip them lenh kem deu hoac dai hon cac lenh dau.",
       "nhip_them_lenh", "chua", "luoi.py khong co.",
       "Chua biet bo loc la gi: dau van tay tren lich su lenh se goi y.",
       "Chua ro."),
]

#: Khoi -> truong `luoi.ThamSo` thuc hien no. `kiem_tinh_nhat_quan` doi chieu voi `dataclasses.fields(luoi.ThamSo)` va
#: `luoi.CHUA_CAI_DAT`: khoi engine 'co' / 'mot_phan' phai co it nhat mot truong CO THAT va DUOC DOC; khoi 'chua' chi duoc tro
#: toi truong da khai bao nhung chua cai dat. Noi cach khac: kho nay khong the ghi "engine co" cho mot thu engine khong co.
_TRUONG_ENGINE = {
    "vao_ngay_lap_tuc": ("cho_lui",),
    "vao_lai_sau_cho_lui": ("cho_lui",),
    "hai_chieu_doc_lap": ("che_do",),
    "mot_chieu": ("che_do",),
    "luoi_gian_cach_deu": ("buoc",),
    "luoi_buoc_gian_dan": ("he_so_buoc", "buoc_tran"),
    "lot_phang": ("kieu_lot", "lot"),
    "lot_cong": ("kieu_lot", "he_so_lot"),
    "lot_nhan": ("kieu_lot", "he_so_lot"),
    "tran_so_lenh": ("tran_tang",),
    "tp_chuoi_tu_gia_tb": ("tp",),
    "tp_chuoi_tien": ("chot_tien",),
    "tp_tung_lenh": ("tia_lenh", "bien_cap"),
    "tia_cap_sau_dau": ("tia_lenh", "bien_cap", "cap_moi_bar"),
    "tia_n_lenh_khi_chuoi_dai": ("tia_lenh", "bien_cap", "cap_moi_bar"),
    "cat_lo_theo_tien": ("dung_lo_tong",),
}
KHOI_DS = [dataclasses.replace(k, truong_engine=_TRUONG_ENGINE.get(k.ma, ())) for k in KHOI_DS]
KHOI: dict[str, Khoi] = {k.ma: k for k in KHOI_DS}


# ============================================================== 3. BOT
@dataclass(frozen=True)
class Bot:
    ma: str
    ten: str
    san: str                   # MT4 | MT5 | -
    tep: str                   # tep trong thu muc Drive (.ex4 / .ex5 / .set)
    nguon: str                 # lay thong tin tu dau
    ket_qua: str               # ket qua tester that (thu nha 04/10/2026) hoac '-'
    song_sot: bool             # qua xac nhan tren tester?
    dac_sac: str               # yeu to dac sac cua bot (1-2 cau)
    khoi: dict = field(default_factory=dict)   # ma_khoi -> (muc, ghi_chu)


def _b(ma, ten, san, tep, nguon, ket_qua, song_sot, dac_sac, khoi) -> Bot:
    return Bot(ma, ten, san, tep, nguon, ket_qua, song_sot, dac_sac, dict(khoi))


_T1 = "Model 1, GOLD.i# M15, kham_pha 2018-01-01..2021-10-11"
_KQ_AM = "tester (%s): am hoac chay het tai khoan trong doan kham_pha (thu nha 60fa)" % _T1

BOT_DS: list[Bot] = [
    _b("ccbsn", "CCBSN (Can Cu Bu Sieng Nang) v2.6 / v3.0.5", "MT5", ".ex5 + 10 bo .set",
       "224 tham so trong 10 bo .set; khong co video (hoi dap o nhom Telegram)",
       "tester (%s; thu nha 60fa, 6487): kham_pha lai: v3.0.5 Vamge10K +8623 DD 23,8%% PF 2,45, v2.6 CanCuBo10K27 +6482 "
       "DD 23%%; cac bo .set khac (min3000, CC304, onlybuy, H1_50usd, M15_10K_5KUT) am / chay het tai khoan. XAC NHAN "
       "2021-10-13..2024-04-07 (moi bo mot lan): CHI v2.6 + 'Can Cu Bo 10K 2.7 DD 3K.set' song: +4923, DD 25%% (~2,6k USD, "
       "lot co dinh), PF 1,89, 1467 lenh; von 5k DD 45,9%%, 20k DD 13,1%%. Vamge / Vange2 / 500_2 truot. Model 4: 0%% tick "
       "that (XM thieu) -> chua du dieu kien niem phong; v2.6 Model 4 kham_pha +5939 (equity DD 42,6%%)." % _T1,
       True,
       "DCA nang 5 tang: he so lot doi theo bac (moc 10/20/30/40/50 lenh), buoc 4 nac, lenh doi ung sau 5-12 lenh, doi TP "
       "khi lo, tia (Sniper) + All Sniper, loc DCA. Bo .set theo von (10K, 500, 50, 3000, US Tech, only-buy). "
       "Ten file 'DD 3K' = tuyen bo cua nguoi dung, khong phai bang chung. Tham so chua xep khoi: InpDCAMODE (0/1/5, chua biet "
       "nghia - co the la kieu DCA), InpMagicID.",
       {
           "hai_chieu_doc_lap": ("knob", "InpTypeBuySell = 0"),
           "mot_chieu": ("knob", "InpTypeBuySell = 2 (only-buy) o mot so bo"),
           "vao_ngay_lap_tuc": ("gia_thuyet", "khong thay tham so tin hieu vao trong bo .set"),
           "loc_spread": ("knob", "InpMaxSpread 3-500 point"),
           "tran_so_lenh": ("knob", "InpMaxBuyOrders / InpMaxSellOrders 5-1000"),
           "tran_lot_tong": ("knob", "InpMaxLots 0,02-2,3"),
           "lot_nhan": ("knob", "InpMultiplier 1,0-1,5 (mac dinh 1,18-1,3)"),
           "lot_cong": ("knob", "InpPlus 0,01"),
           "lot_nhan_theo_bac": ("knob", "InpOrders2NewMultiplier1-5 ~ 10/20/30/40/50 -> InpNewMultiplier1-5 ~ 1,2/1,1/1,05/1,06/1,03"),
           "luoi_gian_cach_deu": ("knob", "InpDistance0 9,8-200"),
           "luoi_buoc_theo_bac": ("knob", "InpDistance1-4 15-150"),
           "luoi_buoc_gian_dan": ("knob", "InpDistanceMulti 1,0-1,2"),
           "tp_tung_lenh": ("knob", "InpTP 3-500"),
           "tp_chuoi_tu_gia_tb": ("knob", "InpTPDCA 3-1200 (don vi chua chac: point?)"),
           "doi_tp_khi_lo": ("knob", "InpUseChangeTPDCA, InpPerLoss2ChangeTP -5..-20%"),
           "lenh_doi_ung_sau_n_lenh": ("knob", "InpOrders2OpenOpp 5-12, InpLotsOpp 0,01-0,05, InpPerLotsOpp 0-15"),
           "tia_n_lenh_khi_chuoi_dai": ("knob", "InpUseSniper, InpTPSniper 5-30, InpMoneySniperFull 1-10 USD, First/LastOrdersSniper, Sniper Partial khi lo -5..-30%"),
           "all_sniper": ("knob", "dong tat ca khi lai 1-10 USD sau 1-55 lenh"),
           "loc_dca_tu_lenh_n": ("knob", "InpUseFilterDCA, mo sau 1-25 lenh"),
           "loc_tin_tuc": ("thong_bao", "thong bao v3.0.6 o nhom"),
           "loc_adx_atr": ("thong_bao", "thong bao v3.0.6 o nhom"),
           "loc_gio_giao_dich": ("knob", "khao sat ghi co lich gio (ten tham so chua chep)"),
           "loc_ngay_thu_lich": ("knob", "khao sat ghi co lich ngay (ten tham so chua chep)"),
       }),
    _b("bigmouse", "Bigmouse Hedging (T91 hedging v2.2)", "MT5", ".ex5",
       "video Bigmouse -CO8sCuE31c", "tester: 0 lenh (khong vao duoc - can lenh dau tay hoac che do auto)", False,
       "Hedging bang lenh STOP doi ung voi tong lot x2 (4 lenh dau) roi x1,6; thoat theo tong tien, cat am, va "
       "KICH HOAT HOA VON sau N lenh (bo TP duong, chi dat SL o hoa von).",
       {
           "vao_tay_roi_dca": ("video", "lenh dau tay"),
           "vao_ngay_lap_tuc": ("video", "che do auto mo Buy dau khi bat bot"),
           "lenh_doi_ung_stop": ("video", "khoang cach buy/sell 350-360 point (~3,6 gia)"),
           "lot_tong_gap_doi": ("video", "tong lot x2 trong 4 lenh dau, tu lenh 5 con x1,6"),
           "lot_fibo": ("video", "tuy chon, tac gia chua test"),
           "tran_lot_tong": ("video", "15 lot"),
           "tran_so_lenh": ("video", "36 lenh"),
           "tp_chuoi_tien": ("video", "tong lai tru phi 5 USD (chinh duoc 10/15/20)"),
           "cat_lo_theo_tien": ("video", "cat am X USD"),
           "thoat_hoa_von_khi_chuoi_dai": ("video", "du N lenh (vd 3) bo TP duong, chi dat SL o hoa von"),
           "keo_sl_hoa_von_khi_co_lai": ("video", "ve hoa von roi di them 2 gia thi keo SL"),
           "sl_cung": ("video", "SL theo ti le RR ~1,3 khoang cach buy/sell"),
           "loc_gio_giao_dich": ("video", "gio mo cua (gio san + 7 = gio VN)"),
       }),
    _b("black_dragon", "EA Black Dragon MT5 V13 (vang)", "MT5", ".ex5 + .set vang 20k",
       "video Black Dragon IhdzG_Za3jg", _KQ_AM, False,
       "DCA hai chieu khong chi bao, buoc gian x1,2 (400 point), lot nhan, TP 'treo len', toi da 99 lenh moi chieu; "
       "che do manual (magic 0) va auto.",
       {
           "vao_ngay_lap_tuc": ("video", "setup khong dung chi bao: vao thang Buy/Sell"),
           "vao_tay_roi_dca": ("video", "che do Manual magic 0"),
           "hai_chieu_doc_lap": ("video", "mo Buy khi dang co Sell va gia tang (va nguoc lai)"),
           "tran_so_lenh": ("video", "99 Sell va 99 Buy"),
           "lot_nhan": ("video", "he so nhan lot (lot 0,01 -> 0,02, 0,03, 0,04, 0,05, 0,07 ...)"),
           "lot_tu_dong_theo_von": ("video", "co nhung khong dung (0,01 cho moi 1000 von)"),
           "luoi_buoc_gian_dan": ("video", "buoc 400 point, he so gian 1,2"),
           "tp_treo_len": ("video", "TP trailing 'treo len'"),
           "loc_gio_giao_dich": ("video", "co input khung gio"),
           "loc_tin_tuc": ("video", "co nhung chua cau hinh"),
       }),
    _b("bnk", "BNK.HBot", "MT4", ".ex4",
       "video BNK m-ECCVUrfh4", "-", False,
       "DCA co 'GONG DUONG DOI UNG': khong chot lenh dang lai, giu no de can bang cac lenh am, chot ca chuoi roi mo chuoi moi.",
       {
           "gong_duong_doi_ung": ("video", "vd 1 Buy +25 USD, 2 Sell am, tong am chi 12 USD"),
           "lot_nhan": ("video", "he so lot 1,2; lot lon nhat thay ~1,85"),
           "luoi_gian_cach_deu": ("gia_thuyet", "DCA/luoi, kieu buoc khong noi (EURUSD ~200 pip hoi)"),
           "tran_so_lenh": ("video", "quan sat ~19 lenh (chua ro tran)"),
       }),
    _b("copy_lot", "EXP-COPYLOT (Copy1 / Copy2)", "MT4+MT5", ".ex4 / .ex5 master + client",
       "2 video Copylot PKqS6XO1QTE + XA4Cm3E-oNE", "-", False,
       "KHONG phai bot giao dich: sao chep lenh tu tai khoan Master sang Client (ty le lot 1:1). Khong co khoi co che nao.",
       {}),
    _b("gold_hunter", "T91 Gold Hunter", "MT5", ".ex5 + 2 .set",
       "video Gold Hunter bnEMqsmJ5AI", "2 bo .set: " + _KQ_AM, False,
       "Chi BUY vang khi RSI(4) M5 < 15, nhoi hang tram lenh moi lan co tin hieu; thoat KHONG theo pip / USD ma khi "
       "gia trung binh duong va RSI > 50.",
       {
           "vao_rsi_qua_ban": ("video", "RSI chu ky 4 tren M5 duoi 15"),
           "vao_theo_ma": ("video", "phu de nhac Bollinger / MA4 (mo ho)"),
           "mot_chieu": ("video", "all buy"),
           "them_lenh_theo_tin_hieu": ("video", "nhoi Buy 'may tram lenh'"),
           "lot_phang": ("video", "~0,1 lot moi lenh (phu de mo ho)"),
           "thoat_rsi_va_tb_duong": ("video", "gia tb chuoi > 0 va RSI > 50 thi chot toan bo"),
       }),
    _b("hand_dca", "HandDCA.HBot (kem chi bao SSL)", "MT4", ".ex4",
       "video HandDCA zDxRwEiGvwE", "-", False,
       "'Danh tay + DCA tu dong': nguoi vao lenh dau bang SSL ba khung (M15 xanh da dong + M5 xanh + M1 doi mau), "
       "bot tu DCA nguoc lai va chinh TP de co lai duong nho.",
       {
           "vao_tay_roi_dca": ("video", "nguoi mo 1 lenh Buy / Sell"),
           "vao_chi_bao_ngoai": ("video", "SSL ba khung M1 / M5 / M15"),
           "tp_chuoi_tu_gia_tb": ("video", "bot chinh TP de co lai duong nho (muc: tuy chinh)"),
       }),
    _b("hand_atmx", "HandATMX.HBot (cap nhat trailing oneway)", "MT4", ".ex4",
       "video HandDCA QN5DUZC9wBM", "-", False,
       "DCA nhoi theo lenh tay + 'Trailing Oneway': khi chuoi mot chieu > N lenh va tong lai > X USD thi keo SL ve "
       "hoa von cong delta; che do hai chieu rieng khi tong Buy+Sell > 10.",
       {
           "vao_tay_roi_dca": ("video", "lenh tay"),
           "tp_chuoi_tien": ("video", "TP chuoi 10 USD"),
           "keo_sl_hoa_von_khi_co_lai": ("video", "Oneway number order 3, lai > 5 USD, SL = hoa von + 1 gia (10 BP)"),
       }),
    _b("kawkaw46", "KawKawKaw46 V2 (EMA46 XAU M1)", "MT4", ".ex4 + .set XAU M1",
       "video KawKaw w66ELN7cDPg", "-", False,
       "DCA mot chieu tren vang: luoi TU GIAN khi gia di nguoc, khi gia hoi thi nhoi them lenh lam luoi day va keo TP lai "
       "gan; lot cong deu.",
       {
           "vao_theo_ma": ("video", "che do mo lenh 'theo entry' / 'theo MA'"),
           "mot_chieu": ("video", "xu ly xong chuoi roi moi sang chuoi khac"),
           "luoi_buoc_gian_dan": ("video", "luoi tu gian khi gia di nguoc (cong thuc khong noi); step ~5 gia"),
           "luoi_day_khi_gia_hoi": ("video", "gia hoi 3-4 gia la TP chuoi sau khi nhoi them"),
           "lot_cong": ("video", "lot step add"),
           "tp_chuoi_tien": ("video", "dong tat ca khi dat USD"),
       }),
    _b("newyear", "NewYear.HBot (v1 va v2.1)", "MT5", ".ex5",
       "2 video NewYear uFomm1PqlFY + fbhWUKamAkg",
       "NewYear2.1 (%s): kham_pha +9666 DD 64%%, TRUOT xac nhan 2021-10..2024-04 (tai khoan chay het von); lan chay dau "
       "treo / log spam (thu nha 60fa)." % _T1, False,
       "Theo xu huong + MARTINGALE SAU SL (lot x2: 0,01 -> 0,32); v2.1 co TP / SL co dinh, keo SL ve hoa von khi lot 0,08 "
       "va lai 2 gia, chia lot, ba khung gio.",
       {
           "vao_theo_xu_huong": ("video", "khung H1 tro len; luat vao khong noi"),
           "nhoi_theo_loi": ("video", "'nhoi theo trend' (phu de mo ho)"),
           "lot_nhan_sau_sl": ("video", "he so nhan 2 sau moi SL, 0,01 -> 0,32 (co luc 0,36)"),
           "sl_cung": ("video", "v2.1: TP ~5 gia, SL ~7 gia (phu de mo ho)"),
           "tp_tung_lenh": ("video", "v2.1: TP co dinh"),
           "keo_sl_hoa_von_khi_co_lai": ("video", "v2.1: lot chuoi 0,08 va lai 2 gia thi SL ve hoa von"),
           "loc_gio_giao_dich": ("video", "v2.1: time trade 1 / 2 / 3"),
           "loc_sideway_nen": ("video", "nguoi trinh bay: sideway (3-4 nen khong thoat vung) la ke thu cua bot theo xu huong - NGUOI VAN HANH tat tay, khong phai tinh nang bot"),
       }),
    _b("nuti", "NuTi.HBot 1.3 (MT4 va MT5)", "MT4+MT5", ".ex4",
       "2 video NuTi S43_cKlP9y0 (MT5) + bYH9WFJ5rIg (MT4)", "-", False,
       "'TAM GIA' = gia mo cua ngay: tren Sell, duoi Buy (danh nguoc); ba 'QUANG' theo so lenh (lenh 1-9 TP don 2 gia, "
       "tu lenh 10 TP chuoi hoa von + 0,5 gia voi lot lon); DCA theo nen; tia lenh.",
       {
           "vao_tam_gia_ngay": ("video", "MT5: lech tam gia ~30 gia (20 duoc); MT4: +/- 3 gia"),
           "luoi_theo_nen_moi": ("video", "DCA mo theo nen (true = chi khi nen moi)"),
           "luoi_buoc_theo_bac": ("video", "MT4: quang 1 cach 2 gia (lenh 1-9), quang 2 cach 3 gia (lenh 10+); MT5: 1 gia"),
           "lot_nhan": ("video", "MT5: he so nhan 1,1, cong 0"),
           "lot_nhan_theo_bac": ("video", "MT4 quang 2: lot lon do tinh toan (vd 0,38)"),
           "tran_lot_tong": ("video", "MT5: max lot 3"),
           "tran_so_lenh": ("video", "MT5: 9 lenh; MT4: 60-100 co the chinh"),
           "tp_chuoi_tu_gia_tb": ("video", "MT5: TP chuoi 20 gia; MT4 quang 2: hoa von + 0,5 gia (khuyen 1-3)"),
           "tp_tung_lenh": ("video", "MT4 quang 1: TP don 2 gia / lenh, khong SL"),
           "tia_n_lenh_khi_chuoi_dai": ("video", "MT5: kich hoat 10 lenh, tia 2 lenh, lai sau tia 2,5 USD (de tat)"),
           "cat_lo_theo_tien": ("video", "'shot tai khoan' -300 USD (de tat)"),
           "mot_chieu": ("video", "che do 'only' khi test"),
           "hai_chieu_doc_lap": ("video", "MT4: quang 1 tang len 60-100 lenh = luoi hai chieu"),
           "loc_bao_bien_dong": ("video", "nguoi trinh bay: 'bao' = di 40-60 gia trong 5-10 phut khong hoi; chi tha bot SAU bao - NGUOI VAN HANH, khong phai tinh nang bot"),
           "loc_ngay_thu_lich": ("video", "nguoi trinh bay: tranh sang thu Hai, toi thu Sau, dau - cuoi thang / quy, nua cuoi thang 12, ngay le My - NGUOI VAN HANH"),
       }),
    _b("semi_hft", "SEMI HFT EA V3.3", "MT5", ".ex5",
       "video SEMI HFT aEVSlzjyhWs", "tester: treo / het gio (khong co ket qua)", False,
       "DCA hai chieu lot nhan 1,08, thoat bang trailing (khong TP chuoi); phia Buy TACH NHOM va chot lenh thap nhat "
       "truoc, phia Sell gong ca chuoi; khi Sell ket thi giu Buy duong lam dem.",
       {
           "hai_chieu_doc_lap": ("video", "mode Buy / Sell"),
           "luoi_gian_cach_deu": ("video", "DCA moi 2 gia (co the cach mot nen)"),
           "lot_nhan": ("video", "he so 1,08"),
           "trailing_stop_chuoi": ("video", "lai 2 gia tu hoa von thi dich trailing; khong TP chuoi"),
           "tia_n_lenh_khi_chuoi_dai": ("video", "Buy: chot tung phan lenh thap nhat truoc (nhu bot RTX)"),
           "gong_duong_doi_ung": ("video", "Sell ket -> giu Buy duong khong chot den khi Sell xong"),
           "loc_gio_giao_dich": ("video", "gio giao dich theo ngay"),
       }),
    _b("signalx", "SignalX.HBot (+ Atomic Analyst)", "MT4", ".ex4",
       "video SignalX YvfSeiSLqAM", "-", False,
       "Lenh don theo tin hieu CHI BAO NGOAI (doc buffer), MARTINGALE x2 sau moi SL (0,01 -> 0,64); khong luoi.",
       {
           "vao_chi_bao_ngoai": ("video", "ID buy / ID sell = so buffer (vd 22 / 23), M1 / M5 / M15"),
           "lot_nhan_sau_sl": ("video", "x2 sau SL den 0,64"),
           "sl_cung": ("video", "TP / SL co dinh (TP ~2 gia)"),
           "tp_tung_lenh": ("video", "TP co dinh moi lenh"),
       }),
    _b("black_wolf", "Black Wolf", "MT5", ".ex5 + .set",
       "chua co video / huong dan", "tester: treo / spam log (da chan log > 300 MB)", False,
       "Chua biet co che: chua co nguon mo ta.", {}),
    _b("goldminer", "GoldMiner MT5", "MT5", ".ex5",
       "chua co video / huong dan", "tester: treo / het gio", False,
       "Chua biet co che: chua co nguon mo ta.", {}),
    _b("trailing_hbot", "Trailing.HBot (2 ban)", "MT4", ".ex4",
       "chua co video / huong dan", "-", False,
       "Chua biet co che (ten goi y trailing).", {}),
    _b("unforgiven", "UNFORGIVEN", "MT4", ".ex4",
       "chua co video / huong dan", "-", False,
       "Chua biet co che: chua co nguon mo ta.", {}),
    # He luoi CUA TA: khong phai bot tai ve - de thay ta CO gi va THIEU gi so voi cac bot.
    _b("luoi_cua_ta", "He luoi cua ta (luoi.py + nhan C + ea_LuoiDayDu.mq5)", "MT5", "ma nguon",
       "ma nguon cua ta", "AUDCAD luoi co tia, holdout +13,26%/nam (mo phong, engine co the lac quan ~15% o tia lenh)", False,
       "Luoi hai chieu / mot chieu, buoc gian dan, lot phang / cong / nhan, tia cap dau-cuoi, chot theo tien, cho gia lui "
       "truoc khi vao lai.",
       {k.ma: ("ma_nguon", k.engine_ghi_chu) for k in KHOI_DS if k.engine == "co"}),
]
BOT: dict[str, Bot] = {b.ma: b for b in BOT_DS}
#: Bot tai ve (khong tinh he cua ta, khong tinh cong cu sao chep): dung de dem "bao nhieu bot dung khoi nay".
BOT_NGOAI = tuple(b.ma for b in BOT_DS if b.ma != "luoi_cua_ta")
CHU_BOT_CUA_TA = "luoi_cua_ta"


# ============================================================== 4. TRUY VAN
def khoi(ma: str) -> Khoi:
    return KHOI[ma]


def bot(ma: str) -> Bot:
    return BOT[ma]


def khoi_cua_bot(b: Bot) -> list[tuple[str, tuple]]:
    """(ma_khoi, (muc, ghi_chu)) cua bot theo THU TU CHUAN cua danh sach khoi (khong theo thu tu chen vao dict): tai lieu sinh ra
    phai xac dinh du dict cua bot bi sua / khoi phuc theo thu tu khac."""
    return [(k.ma, b.khoi[k.ma]) for k in KHOI_DS if k.ma in b.khoi]


def bot_dung_khoi(ma_khoi: str, gom_cua_ta: bool = False) -> list[str]:
    """Danh sach bot (theo thu tu khai bao) co khoi nay. Mac dinh khong dem he cua ta."""
    return [b.ma for b in BOT_DS if ma_khoi in b.khoi and (gom_cua_ta or b.ma != CHU_BOT_CUA_TA)]


def so_bot_dung(ma_khoi: str) -> int:
    return len(bot_dung_khoi(ma_khoi))


def ma_tran() -> dict[str, dict[str, str]]:
    """bot -> {khoi: muc}. Chi gom cac cap co khai bao."""
    return {b.ma: {m: v[0] for m, v in b.khoi.items()} for b in BOT_DS}


def bot_song_sot() -> list[str]:
    return [b.ma for b in BOT_DS if b.song_sot]


def khoang_trong_engine() -> list[dict]:
    """Khoi chua (hoac moi mot phan) co trong engine luoi, xep: so bot dung giam dan, co o bot song sot truoc, roi ten.

    `uu_tien` la thu tu goi y XAY, khong phai du bao ket qua: khoi nhieu bot dung = it nhat nhieu nguoi tin no; khoi o bot
    song sot = bot DUY NHAT qua xac nhan dung no."""
    song = set(bot_song_sot())
    hang = []
    for k in KHOI_DS:
        if k.engine not in ("chua", "mot_phan"):
            continue
        bd = bot_dung_khoi(k.ma)
        hang.append({"ma": k.ma, "ten": k.ten, "engine": k.engine, "so_bot": len(bd), "bot": bd,
                     "o_bot_song_sot": sorted(song.intersection(bd)), "ghi_chu": k.engine_ghi_chu})
    hang.sort(key=lambda r: (-(1 if r["o_bot_song_sot"] else 0), -r["so_bot"], r["ma"]))
    for i, r in enumerate(hang, 1):
        r["uu_tien"] = i
    return hang


def dac_sac_theo_bot(tran: int = 2) -> dict[str, list[str]]:
    """Voi moi bot: cac khoi chi <= `tran` bot dung (yeu to dac sac). Khong tinh he cua ta."""
    kq = {}
    for b in BOT_DS:
        if b.ma == CHU_BOT_CUA_TA:
            continue
        kq[b.ma] = [m for m, _ in khoi_cua_bot(b) if so_bot_dung(m) <= tran]
    return kq


#: Cac nhom khoi thay the nhau trong MOT he (chon mot): ghep khoi thu hai thi THAY CHO khoi dang co.
LOAI_TRU = (
    ("lot_phang", "lot_cong", "lot_nhan", "lot_nhan_theo_bac", "lot_tong_gap_doi", "lot_fibo", "lot_nhan_sau_sl"),
    ("luoi_gian_cach_deu", "luoi_buoc_gian_dan", "luoi_buoc_theo_bac"),
    ("hai_chieu_doc_lap", "mot_chieu"),
    ("vao_ngay_lap_tuc", "vao_tay_roi_dca", "vao_rsi_qua_ban", "vao_tam_gia_ngay", "vao_chi_bao_ngoai", "vao_theo_ma",
     "vao_theo_xu_huong"),
    ("tp_chuoi_tu_gia_tb", "tp_chuoi_tien", "tp_tung_lenh", "thoat_rsi_va_tb_duong"),
)


def de_xuat_ap_cheo(host: tuple | list | None = None, top: int = 15) -> list[dict]:
    """Khoi nao nen thu GHEP vao `host` (mac dinh: cac khoi engine da co) - thu tu thu va ly do.

    Moi dong: khoi, `kieu` ('them' = khong dung hang voi gi dang co | 'thay <khoi>' = cung loai tru nhau), so bot dung,
    co o bot song sot khong, trang thai engine, ly do ngan. Khoi can nguoi / chi bao ngoai ('ngoai') khong de xuat.
    Day la MENU de AI chon thi nghiem (qua `b nc cc ...`), khong phai ket luan."""
    host = tuple(host) if host is not None else tuple(k.ma for k in KHOI_DS if k.engine == "co")
    song = set(bot_song_sot())
    hang = []
    for k in KHOI_DS:
        if k.ma in host or k.engine == "ngoai":
            continue
        bd = bot_dung_khoi(k.ma)
        if not bd:
            continue
        thay = [h for nh in LOAI_TRU if k.ma in nh for h in host if h in nh]
        lo_song = sorted(song.intersection(bd))
        ly_do = ["%d bot dung (%s)" % (len(bd), ", ".join(bd))]
        if lo_song:
            ly_do.append("co o bot SONG SOT (%s)" % ", ".join(lo_song))
        ly_do.append("engine: " + ENGINE[k.engine].split(" (")[0])
        hang.append({"ma": k.ma, "ten": k.ten, "kieu": ("thay " + "/".join(thay)) if thay else "them",
                     "so_bot": len(bd), "o_bot_song_sot": lo_song, "engine": k.engine, "ly_do": ly_do,
                     "ap_cheo": k.ap_cheo})
    rank = {"co": 0, "mot_phan": 1, "chua": 2}
    hang.sort(key=lambda r: (-(1 if r["o_bot_song_sot"] else 0), -r["so_bot"], rank[r["engine"]], r["ma"]))
    return hang[:top]


# ---------------------------------------------------- phan loai tham so .set theo TEN
#: Thu tu quan trong: dong dau khop thang. Khop theo TEN nen co the SAI - ket qua chi la goi y de doc bo .set.
#: Hai rang buoc thu tu da bi bay: (1) cac luat 'max...' (tran lot / so lenh) phai dung TRUOC luat lot_nhan vi 'MaxLots' chua
#: 'xLot'; (2) luat cu the (All Sniper, Sniper, Opp, ChangeTP, News, ATR) dung truoc luat chung (TP, Multiplier). Test
#: `test_loai_ten_that_ccbsn` / `test_loai_ten_bay_va_duong_bien` giu ca hai.
_REGLA_THAM_SO: list[tuple[str, tuple]] = [
    (r"(?i)all.?sniper|sniper.?all", ("all_sniper",)),
    (r"(?i)sniper|trim", ("tia_n_lenh_khi_chuoi_dai",)),
    (r"(?i)opp(?![a-z])|opposite|hedg", ("lenh_doi_ung_sau_n_lenh",)),         # 'PerLoss2Hedging' la nguong hedge, khong phai doi TP
    (r"(?i)change.?tp|per.?loss", ("doi_tp_khi_lo",)),
    (r"(?i)news", ("loc_tin_tuc",)),
    (r"(?-i:ATR|ADX|Atr|Adx|(?<![A-Za-z])atr|(?<![A-Za-z])adx)", ("loc_adx_atr",)),
    (r"(?i)new.?multi|orders?2new", ("lot_nhan_theo_bac",)),
    (r"(?i)dist(ance)?.?multi|step.?(multi|factor)|dist.?factor|grid.?multi", ("luoi_buoc_gian_dan",)),
    (r"(?i)dist(ance)?[1-9]$|step[1-9]$|level[1-9]$", ("luoi_buoc_theo_bac",)),
    (r"(?i)dist(ance)?0?$|step$|grid.?step|grid.?size", ("luoi_gian_cach_deu",)),
    (r"(?i)max.?lots?$|lot.?max|max.?volume|max.?lot", ("tran_lot_tong",)),
    (r"(?i)max.?(buy|sell)?.?orders?|max.?trades|orders?.?max|max.?positions?|max.?levels?", ("tran_so_lenh",)),
    (r"(?i)multiplier|multi.?lot|xlot|lot.?multi|lot.?factor|coef.?lot", ("lot_nhan",)),
    (r"(?i)plus$|lot.?step.?add|add.?lot|lot.?add", ("lot_cong",)),
    (r"(?i)max.?spread|spread.?max|spread.?limit", ("loc_spread",)),
    (r"(?i)filter.?dca|dca.?filter", ("loc_dca_tu_lenh_n",)),
    (r"(?i)tp.?dca|tp.?basket|tp.?all|basket.?tp|total.?tp|tp.?chuoi", ("tp_chuoi_tu_gia_tb",)),
    (r"(?i)(take.?profit|tp)$", ("tp_tung_lenh",)),
    (r"(?i)(stop.?loss|sl)$", ("sl_cung",)),
    (r"(?i)break.?even|be.?(start|step|profit)", ("keo_sl_hoa_von_khi_co_lai",)),
    (r"(?i)trail", ("trailing_stop_chuoi",)),
    (r"(?i)hour|session|time.?(start|end|trade|filter|from|to)|start.?time|end.?time|use.?time|trad(e|ing).?time", ("loc_gio_giao_dich",)),
    (r"(?i)calendar|holiday|monday|friday|weekday|day.?filter", ("loc_ngay_thu_lich",)),
    (r"(?i)rsi", ("vao_rsi_qua_ban",)),
    (r"(?-i:(?<![A-Za-z])E?MA(?![a-z]))", ("vao_theo_ma",)),
    (r"(?i)type.?buy.?sell|buy.?sell.?(mode|type)|only.?(buy|sell)|trade.?(mode|direction)", ("hai_chieu_doc_lap", "mot_chieu")),
    (r"(?i)auto.?lot|lot.?auto|risk.?percent|percent.?risk", ("lot_tu_dong_theo_von",)),
    (r"(?i)new.?day|delay.?day", ("loc_ngay_thu_lich",)),
    (r"(?i)indi.?mode|signal", ("vao_chi_bao_ngoai",)),
]


def loai_tu_ten_tham_so(ten: str) -> tuple:
    """Khoi co the nam sau mot tham so cua `.set`, doan theo TEN (rong neu khong biet). Chi la goi y, co the sai."""
    ten = (ten or "").strip()
    for mau, khois in _REGLA_THAM_SO:
        if re.search(mau, ten):
            return khois
    return ()


# ---------------------------------------------------- loi khuyen van hanh -> gia thuyet kiem duoc
#: Loi nguoi trinh bay noi lai nhieu lan: bot phai 'lai' (chon ngay tha, tat khi ...). Bien thanh GIA THUYET do duoc bang so
#: lieu dai, khong phai su that. (loi khuyen, bot noi, khoi loc, cach kiem)
LOI_KHUYEN_VAN_HANH: list[tuple[str, str, str, str]] = [
    ("Tranh sang thu Hai va toi thu Sau", "nuti", "loc_ngay_thu_lich",
     "Chia ket qua luoi theo (thu, gio vao chuoi): nhom 'thu Hai gio dau' / 'thu Sau gio cuoi' co ky vong am hon khong?"),
    ("Tranh dau - cuoi thang, cuoi quy (30/6, 30/9, 31/12) va nua cuoi thang 12", "nuti", "loc_ngay_thu_lich",
     "Chia theo ngay trong thang / quy; so chuoi mo trong cac ngay 'tranh' voi cac ngay con lai tren doan kham_pha, "
     "kiem lai tren xac_nhan."),
    ("Tranh ngay le My", "nuti", "loc_ngay_thu_lich",
     "Dung lich ngay le My (du lieu ngoai); so ket qua chuoi mo trong tuan le voi tuan thuong."),
    ("Tat khi co 'bao': di 40-60 gia trong 5-10 phut khong hoi", "nuti", "loc_bao_bien_dong",
     "Dac trung bien dong ngan (range 5-10 phut chia ATR) lam bo loc vao / them lenh; xem DD luoi co giam khi bo cac bar bao."),
    ("Sideway: 3-4 nen khong thoat vung cua nhau thi tat bot (voi he theo xu huong)", "newyear", "loc_sideway_nen",
     "Chi hop he theo xu huong; voi luoi thi dao nguoc: luoi tot hon khi sideway - do ca hai."),
    ("Khong tha phien khuya (23h - 2h gio VN) va luc co tin manh", "newyear", "loc_gio_giao_dich",
     "Voi luoi AUDCAD: gio vao nao co ky vong am? (loc_gio_giao_dich; do tren kham_pha, kiem tren xac_nhan)."),
    ("Choi phien A / Au, tranh phien My cho DCA vang (BlackDragon) - nhung phien My hop scalp (HandDCA)", "black_dragon",
     "loc_gio_giao_dich", "Hai loi nguoc nhau: do ket qua luoi theo phien de xem phien nao hop he nao."),
    ("18h - 21h gio VN hay di ngang / dao chieu nen de dinh chuoi DCA dai", "hand_dca", "loc_gio_giao_dich",
     "Do do dai chuoi theo gio vao chuoi."),
]


# ============================================================== 5. KIEM TINH NHAT QUAN
def kiem_tinh_nhat_quan() -> list[str]:
    """Tra danh sach loi du lieu (rong = on). Test goi ham nay; chay tay: `python -m nhan.khoi_co_che --kiem`."""
    loi = []
    if len(KHOI) != len(KHOI_DS):
        loi.append("trung ma khoi")
    if len(BOT) != len(BOT_DS):
        loi.append("trung ma bot")
    for k in KHOI_DS:
        if k.nhom not in NHOM:
            loi.append("khoi %s: nhom la %r" % (k.ma, k.nhom))
        if k.engine not in ENGINE:
            loi.append("khoi %s: engine la %r" % (k.ma, k.engine))
        for ten in ("ten", "mo_ta", "dau_van_tay", "engine_ghi_chu", "ap_cheo", "rui_ro"):
            if not getattr(k, ten).strip():
                loi.append("khoi %s: thieu %s" % (k.ma, ten))
        if not re.fullmatch(r"[a-z][a-z0-9_]*", k.ma):
            loi.append("khoi %s: ma khong dung dang snake_case" % k.ma)
    for b in BOT_DS:
        for m, (muc, ghi) in b.khoi.items():
            if m not in KHOI:
                loi.append("bot %s: khoi la %r" % (b.ma, m))
            if muc not in MUC:
                loi.append("bot %s / %s: muc la %r" % (b.ma, m, muc))
            if b.ma == CHU_BOT_CUA_TA and muc != "ma_nguon":
                loi.append("he cua ta chi duoc co muc ma_nguon (%s)" % m)
            if b.ma != CHU_BOT_CUA_TA and muc == "ma_nguon":
                loi.append("bot ngoai %s khong the co muc ma_nguon (%s)" % (b.ma, m))
    ta = set(BOT[CHU_BOT_CUA_TA].khoi)
    co = {k.ma for k in KHOI_DS if k.engine == "co"}
    if ta != co:
        loi.append("he cua ta khong khop khoi engine=co: thua %s, thieu %s" % (sorted(ta - co), sorted(co - ta)))
    for k in KHOI_DS:
        if not bot_dung_khoi(k.ma) and k.engine != "co":
            loi.append("khoi %s mo coi: khong bot nao dung va engine khong co" % k.ma)
    for ma_loai in LOAI_TRU:
        for m in ma_loai:
            if m not in KHOI:
                loi.append("LOAI_TRU: khoi la %r" % m)
    for ma in _TRUONG_ENGINE:
        if ma not in KHOI:
            loi.append("_TRUONG_ENGINE: khoi la %r" % ma)
    try:
        from nhan import luoi as _luoi
        co_that = {f.name for f in dataclasses.fields(_luoi.ThamSo)}
        chua_cai = set(_luoi.CHUA_CAI_DAT)
    except Exception as e:      # pragma: no cover - luoi khong nap duoc la loi moi truong, khong phai loi du lieu
        loi.append("khong nap duoc nhan.luoi de doi chieu truong engine: %r" % (e,))
    else:
        for k in KHOI_DS:
            ngoai_ts = [t for t in k.truong_engine if t not in co_that]
            if ngoai_ts:
                loi.append("khoi %s: truong_engine khong co trong luoi.ThamSo: %s" % (k.ma, ngoai_ts))
            if k.engine in ("co", "mot_phan"):
                if not k.truong_engine:
                    loi.append("khoi %s: engine=%s nhung khong chi ra truong luoi.ThamSo nao" % (k.ma, k.engine))
                chua_doc = [t for t in k.truong_engine if t in chua_cai]
                if chua_doc:
                    loi.append("khoi %s: engine=%s nhung truong %s CHUA cai dat (luoi.CHUA_CAI_DAT)" % (k.ma, k.engine, chua_doc))
            else:
                da_chay = [t for t in k.truong_engine if t not in chua_cai]
                if da_chay:
                    loi.append("khoi %s: engine=%s nhung truong %s da duoc engine doc" % (k.ma, k.engine, da_chay))
    for _loi_khuyen, bo, kh, _c in LOI_KHUYEN_VAN_HANH:
        if bo not in BOT:
            loi.append("LOI_KHUYEN: bot la %r" % bo)
        if kh not in KHOI:
            loi.append("LOI_KHUYEN: khoi la %r" % kh)
    return loi


# ============================================================== 6. TAI LIEU SINH TU MA
def _cell(bot_ma: str, ma_khoi: str) -> str:
    v = BOT[bot_ma].khoi.get(ma_khoi)
    return MUC[v[0]] if v else "."


def _bang(hang: list[list[str]], dau: list[str]) -> list[str]:
    out = ["| " + " | ".join(dau) + " |", "|" + "|".join(["---"] * len(dau)) + "|"]
    for h in hang:
        out.append("| " + " | ".join(str(x).replace("|", "/") for x in h) + " |")
    return out


def viet_tai_lieu() -> str:
    """Noi dung `tai_lieu/KHO_CO_CHE_BOT.md` (xac dinh, khong co ngay gio: test so sanh voi tep da commit)."""
    L: list[str] = []
    ngoai = [b for b in BOT_DS if b.ma != CHU_BOT_CUA_TA]
    co_mo_ta = [b for b in ngoai if b.khoi]
    L += ["# KHO KHOI CO CHE CUA CAC CON BOT",
          "",
          "**Tep nay SINH TU MA (`python -m nhan.khoi_co_che --viet`), KHONG sua tay** - sua `nhan/khoi_co_che.py` roi sinh lai.",
          "Test `test_khoi_co_che.py` so sanh tep nay voi ban sinh ra, nen no khong bao gio cu.",
          "",
          "Chu du an 04/10/2026: *\"moi bot se co chien luoc va cach quan tri cung nhu tinh dac sac khac nhau. Muc tieu cua the "
          "brain la boc tach duoc co che / chien luoc hoac yeu to dac sac cua cac con bot de thu ap dung cheo hoac ket hop "
          "them vao cac he thong va ea sau nay.\"*",
          "",
          "## 1. Y TUONG MOT DONG",
          "",
          "Mot con bot = **to hop cac KHOI co che** (vao lenh, them lenh, lot, thoat, bao ve, bo loc). Khoi dung chung giua nhieu "
          "bot la khoi 'chuan'; khoi chi mot hai bot dung la **yeu to dac sac**. Muon ap dung cheo: lay khoi cua bot A, cai "
          "vao he luoi cua ta (hoac bot B), do lai bang `b nc cc ...`. Bot la HOP DEN (.ex4/.ex5, khong co ma nguon) nen "
          "khoi chi co hai nguon: (1) loi tac gia / bo `.set` = **kien thuc truoc so lieu** (tep nay), (2) lich su lenh cua "
          "tester = **bang chung** (`nhan/ho_so_bot.py`, doi chieu: xac nhan / bac bo / khoi moi).",
          "",
          "- %d khoi, %d bot (%d bot co mo ta khoi + he cua ta; %d bot chua co nguon mo ta)." % (
              len(KHOI_DS), len(ngoai), len(co_mo_ta), len(ngoai) - len(co_mo_ta)),
          "- Dong chay: tester -> `lenh_tester.vi_the_tu_tep` -> `ho_so_bot` -> doi chieu voi bang nay -> them khoi con thieu vao "
          "engine -> nhan ban bot -> so lenh voi hop den.",
          "- Muc bang chung: " + "; ".join(MUC_GIAI_THICH[m] for m in MUC) + ". (D = lich su lenh tester: `ho_so_bot` ghi, "
          "khong nam trong bang tinh.)",
          "- Trang thai engine: " + "; ".join("**%s** = %s" % (k, v) for k, v in ENGINE.items()) + ".",
          ""]

    L += ["## 2. BOT: AI LA AI, DAC SAC O DAU", ""]
    for b in BOT_DS:
        L.append("### %s - %s" % (b.ma, b.ten))
        L.append("- San: %s; tep: %s; nguon thong tin: %s." % (b.san, b.tep, b.nguon))
        if b.ket_qua != "-":
            L.append("- Ket qua tester that: %s%s" % (b.ket_qua, " **[SONG SOT xac nhan]**" if b.song_sot else ""))
        L.append("- Dac sac: %s" % b.dac_sac)
        if b.khoi:
            L.append("- Khoi: " + "; ".join("`%s`[%s]" % (m, MUC[v[0]]) for m, v in khoi_cua_bot(b)))
            ds = [m for m, _ in khoi_cua_bot(b) if so_bot_dung(m) <= 2] if b.ma != CHU_BOT_CUA_TA else []
            if ds:
                L.append("- Khoi it bot dung (yeu to dac sac): " + ", ".join("`%s`" % m for m in ds))
        L.append("")

    L += ["## 3. MA TRAN BOT x KHOI", "",
          "Ky hieu: " + ", ".join(MUC_GIAI_THICH[m] for m in MUC) + "; `.` = khong co. Cot dau: so bot ngoai dung.",
          ""]
    cot = [b.ma for b in BOT_DS if b.khoi]
    dau = ["khoi", "so bot"] + cot
    for ma_nhom, ten_nhom in NHOM.items():
        L.append("**%s**" % ten_nhom)
        L.append("")
        hang = [[k.ma, so_bot_dung(k.ma)] + [_cell(c, k.ma) for c in cot] for k in KHOI_DS if k.nhom == ma_nhom]
        L += _bang(hang, dau)
        L.append("")

    L += ["## 4. TUNG KHOI", ""]
    for ma_nhom, ten_nhom in NHOM.items():
        L += ["### %s" % ten_nhom, ""]
        for k in KHOI_DS:
            if k.nhom != ma_nhom:
                continue
            bd = bot_dung_khoi(k.ma)
            L.append("**`%s`** - %s (engine: %s; %d bot ngoai dung%s)" % (
                k.ma, k.ten, k.engine, len(bd), ": " + ", ".join(bd) if bd else ""))
            L.append("- Mo ta: %s" % k.mo_ta)
            if k.tham_so:
                L.append("- Tham so: " + ", ".join(k.tham_so))
            L.append("- Dau van tay trong lich su lenh: %s%s" % (
                k.dau_van_tay, " (phep do `%s`)" % k.kiem if k.kiem else " (khong do duoc tu lenh)"))
            L.append("- Engine: %s%s" % (k.engine_ghi_chu, (" [truong luoi.ThamSo: %s]" % ", ".join(k.truong_engine))
                                          if k.truong_engine else ""))
            L.append("- Ap cheo: %s" % k.ap_cheo)
            L.append("- Rui ro: %s" % k.rui_ro)
            L.append("")

    L += ["## 5. KHOANG TRONG ENGINE - XAY GI TRUOC", "",
          "Khoi chua (hoac moi mot phan) co trong `luoi.py`. Thu tu = **o bot song sot truoc**, roi so bot dung. "
          "Bot song sot hien nay: %s (tester that, xem muc 2); thu tu nay la GOI Y XAY, khong phai du bao khoi nao ra tien." %
          (", ".join(bot_song_sot()) or "chua co"), ""]
    hang = [[r["uu_tien"], r["ma"], r["engine"], r["so_bot"], ", ".join(r["o_bot_song_sot"]) or "-", r["ghi_chu"]]
            for r in khoang_trong_engine()]
    L += _bang(hang, ["#", "khoi", "engine", "so bot", "bot song sot", "thieu gi"])
    L.append("")

    L += ["## 6. DE XUAT AP CHEO VAO HE LUOI CUA TA", "",
          "Menu thi nghiem (khong phai ket luan): khoi nao nen ghep vao he luoi cua ta truoc. `them` = khong dung hang voi khoi dang co; "
          "`thay X` = cung loai tru nhau (chon mot).", ""]
    hang = [[i, r["ma"], r["kieu"], r["so_bot"], r["engine"], "; ".join(r["ly_do"])] for i, r in
            enumerate(de_xuat_ap_cheo(top=20), 1)]
    L += _bang(hang, ["#", "khoi", "kieu", "so bot", "engine", "ly do"])
    L.append("")

    L += ["## 7. LOI KHUYEN VAN HANH -> GIA THUYET DO DUOC", "",
          "Nguoi trinh bay lap lai: bot phai 'lai' (chon ngay tha, tat khi sideway / tin manh / dau cuoi thang). Day la LOI KE, chua "
          "phai su that; nhung nhieu y kiem duoc bang so lieu dai cua ta (chia ket qua luoi theo gio / thu / ngay trong thang).", ""]
    hang = [[i, a, c, d, e] for i, (a, c, d, e) in enumerate(LOI_KHUYEN_VAN_HANH, 1)]
    L += _bang(hang, ["#", "loi khuyen", "bot noi", "khoi loc", "cach kiem"])
    L += ["",
          "## 8. PHAN LOAI THAM SO .SET THEO TEN", "",
          "`loai_tu_ten_tham_so(ten)` doan khoi tu TEN tham so (CCBSN `Inp*` va ten pho bien). Chi la goi y de doc bo `.set`; "
          "tham so khong xep duoc duoc ghi 'chua xep' de AI doc tay.", "",
          "## 9. KHONG PHAI GI",
          "",
          "- Khong phai danh gia bot: dat / am van do bang `cham_diem` va so tay `nc.db`.",
          "- Khong phai ban sao bot: nhan ban bot = viec #53 (can lich su lenh that + bo `.set` that).",
          "- Bot cu / bot crack co the co ma doc (BAT_DAU_O_NHA.md): chi chay tren tester hoac demo, tat DLL, **khong dua file "
          "bot vao git**.",
          ""]
    return "\n".join(L) + "\n"


def ghi_tai_lieu(duong: Path | None = None) -> Path:
    duong = Path(duong) if duong else TAI_LIEU
    duong.parent.mkdir(parents=True, exist_ok=True)
    with open(duong, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(viet_tai_lieu())
    return duong


def main(argv: list[str]) -> int:
    """`--viet` sinh lai tai lieu; `--kiem` kiem tinh nhat quan; `--loai TEN` phan loai mot ten tham so; khong doi so = tom tat."""
    if "--kiem" in argv:
        loi = kiem_tinh_nhat_quan()
        print("\n".join(loi) if loi else "OK: %d khoi, %d bot" % (len(KHOI_DS), len(BOT_DS)))
        return 1 if loi else 0
    if "--viet" in argv:
        print("da ghi", ghi_tai_lieu())
        return 0
    if "--loai" in argv:
        for ten in argv[argv.index("--loai") + 1:]:
            print(ten, "->", ", ".join(loai_tu_ten_tham_so(ten)) or "chua xep")
        return 0
    print("%d khoi, %d bot (song sot: %s)" % (len(KHOI_DS), len(BOT_DS), ", ".join(bot_song_sot()) or "-"))
    print("Xay truoc (engine chua co):")
    for r in khoang_trong_engine()[:8]:
        print("  %2d. %-28s %d bot%s" % (r["uu_tien"], r["ma"], r["so_bot"],
                                         "  [SONG SOT]" if r["o_bot_song_sot"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
