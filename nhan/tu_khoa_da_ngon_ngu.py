# -*- coding: utf-8 -*-
"""tu_khoa_da_ngon_ngu.py - MOT KHAI NIEM, MUOI BON THU TIENG.

## Cho nghen that

Chu du an, 15/09/2026: *"cai tu khoa kia moi search bang tieng anh va tieng viet
trong khi co hang tram quoc gia, cau bo di luong tai lieu khong lo."*

Dung, va voi MT5 thi no con nang hon binh thuong: **MetaQuotes la cong ty Nga**.
Kiem lai `tru/seeker.py`:

  - `GH_NGON_NGU = ["python","pine","mql5","mql4","cpp"]` -> ngon ngu LAP TRINH,
    khong phai ngon ngu nguoi. Ten bien gay hieu nham.
  - moi URL mql5 deu la `/en/...`, trong khi mql5.com co du `/ru /zh /ja /pt
    /es /de /tr /ko /ar /fr /it /id /th /vi` va **noi dung dien dan khac nhau
    theo tung ban**.
  - ca `tru/seeker.py` chi co mot nguon phi-Anh: `habr.com/ru`, va no la nguon
    duyet TRANG chu khong chay theo tu khoa.

## Vi sao khong phai chi dich may

Cai dat gia khong nam o ban dich. No nam o **khai niem chi ton tai trong mot thu
tieng**:

  - Nhat: `両建て` (ryodate) = giu dong thoi mua va ban tren cung cap. Tieng Anh
    goi la "hedging" nhung `両建て` la mot van hoa giao dich rieng cua ban le
    Nhat, voi ca kho bai viet rieng. Va `ナンピン` (nanpin) = nhoi lenh khi lo -
    tieng Anh chi co "averaging down" rat chung.
  - Nga: `усреднение` (trung binh gia) va `сеточник` (dan choi luoi) la tu long
    cua cong dong, khong ai viet "grid trader" trong bai tieng Nga.
  - Trung: `补仓` (bo cang) va `加仓` (gia cang) phan biet nhoi khi lo va nhoi
    khi lai - tieng Anh gop ca hai vao "adding to position".

Nen bang nay giu **ca tu long**, khong chi tu dien.

## Xep hang theo ky vong, khong theo so nguoi noi

Thu tu duoi day la theo *do day tai lieu ve bot forex*, khong theo dan so:
Nga dau bang vi MetaQuotes; Nhat tren Trung vi ban le Nhat giao dich FX tu dong
rat manh; Indonesia/Tho Nhi Ky tren Phap vi thi truong ban le forex lon hon.
"""
from __future__ import annotations

#: Ma ngon ngu -> (ten doc duoc, do uu tien 1 cao nhat). Do uu tien dung de cat
#: bot khi ngan sach mang hep - quet het 14 thu tieng ton gap 14 lan.
NGON_NGU = {
    "ru": ("Nga", 1),         # MetaQuotes la cong ty Nga - kho MQL lon nhat
    "ja": ("Nhat", 1),        # ban le FX tu dong rat manh, co tu vung rieng
    "zh": ("Trung", 1),       # cong dong luong hoa + EA lon
    "pt": ("Bo Dao Nha", 2),  # Brazil la thi truong MT5 lon
    "es": ("Tay Ban Nha", 2),
    "de": ("Duc", 2),
    "tr": ("Tho Nhi Ky", 2),  # ban le forex rat lon
    "id": ("Indonesia", 2),   # ban le MT5 rat lon
    "ko": ("Han", 3),
    "ar": ("A Rap", 3),
    "fr": ("Phap", 3),
    "it": ("Y", 3),
    "th": ("Thai", 3),
    "vi": ("Viet", 3),
}

#: Khai niem -> {ma ngon ngu: [cac cach noi]}. Tieng Anh nam o khoa "en".
#:
#: Quy tac dien bang: mot khai niem chi duoc dien neu no THAT SU co cach noi
#: rieng trong thu tieng do. De trong con hon dien mot ban dich may ma khong ai
#: go vao o tim kiem - tu do chi lam ton luot goi API.
KHAI_NIEM = {
    "hedge": {
        "en": ["hedging expert advisor forex", "locked position forex ea"],
        "ru": ["хеджирование советник форекс", "локирование позиций форекс"],
        "ja": ["両建て EA 自動売買", "両建て 手法 FX"],
        "zh": ["对冲 EA 外汇", "锁仓 外汇 智能交易"],
        "pt": ["hedge robô forex metatrader", "proteção de posição forex"],
        "es": ["cobertura forex asesor experto", "hedging robot forex"],
        "de": ["Hedging Expert Advisor Forex", "Absicherung Handelsroboter"],
        "tr": ["hedge uzman danışman forex", "riskten korunma forex robot"],
        "id": ["hedging robot forex ea", "lindung nilai forex"],
        "ko": ["헤지 자동매매 EA", "양방향 매매 외환"],
        "ar": ["التحوط المستشار الخبير فوركس"],
        "fr": ["couverture robot forex metatrader"],
        "it": ["copertura expert advisor forex"],
        "th": ["เฮดจ์ EA ฟอเร็กซ์"],
        "vi": ["hedge ea forex", "khoá lệnh hai chiều forex"],
    },
    "trailing": {
        "en": ["trailing stop expert advisor mql5", "break even stop ea forex"],
        "ru": ["трейлинг стоп советник mql5", "перевод в безубыток советник"],
        "ja": ["トレーリングストップ EA 自動売買", "建値 ストップ 移動 FX"],
        "zh": ["移动止损 EA 外汇", "追踪止损 智能交易系统"],
        "pt": ["stop móvel robô forex", "trailing stop expert advisor"],
        "es": ["stop dinámico asesor experto", "trailing stop robot forex"],
        "de": ["Trailing Stop Expert Advisor", "nachziehender Stopp Handelsroboter"],
        "tr": ["takip eden stop uzman danışman", "iz süren zarar durdur forex"],
        "id": ["trailing stop robot forex ea"],
        "ko": ["트레일링 스탑 자동매매"],
        "ar": ["وقف الخسارة المتحرك مستشار خبير"],
        "fr": ["stop suiveur robot forex"],
        "it": ["trailing stop expert advisor forex"],
        "th": ["trailing stop EA ฟอเร็กซ์"],
        "vi": ["trailing stop ea mt5", "dời stop về hoà vốn"],
    },
    "luoi": {
        "en": ["grid trading expert advisor no indicator", "grid ea forex"],
        "ru": ["сеточный советник форекс", "сетка ордеров советник mql5",
               "сеточник без индикаторов"],
        "ja": ["グリッドトレード EA 自動売買", "リピート系 自動売買 FX"],
        "zh": ["网格交易 EA 外汇", "网格策略 智能交易系统"],
        "pt": ["robô grid forex metatrader", "estratégia grade forex"],
        "es": ["robot rejilla forex", "estrategia grid forex metatrader"],
        "de": ["Grid Trading Expert Advisor", "Gitterhandel Forex Roboter"],
        "tr": ["grid uzman danışman forex", "ızgara stratejisi forex"],
        "id": ["robot grid forex ea", "strategi grid forex"],
        "ko": ["그리드 매매 자동매매 EA"],
        "ar": ["الشبكة تداول مستشار خبير فوركس"],
        "fr": ["robot grille forex metatrader"],
        "it": ["robot griglia forex metatrader"],
        "th": ["กริด EA ฟอเร็กซ์"],
        "vi": ["ea lưới forex", "chiến lược lưới mt5"],
    },
    "nhoi_lenh": {
        "en": ["martingale position sizing forex ea", "averaging down forex robot",
               "pyramiding add to winner"],
        # `усреднение` la tu cong dong Nga dung cho nhoi khi lo; khong ai viet
        # "averaging down" trong bai tieng Nga.
        "ru": ["мартингейл советник форекс", "усреднение позиций советник",
               "долив в прибыль советник"],
        # `ナンピン` = nhoi khi lo, tu rieng cua ban le Nhat.
        "ja": ["ナンピン EA 自動売買", "マーチンゲール FX 自動売買",
               "難平 手法 FX"],
        # `补仓` nhoi khi lo · `加仓` nhoi khi lai - tieng Anh gop lam mot.
        "zh": ["马丁格尔 EA 外汇", "补仓 策略 外汇", "加仓 策略 智能交易"],
        "pt": ["martingale robô forex", "média de preço forex robô"],
        "es": ["martingala robot forex", "promediar posiciones forex"],
        "de": ["Martingale Expert Advisor", "Nachkauf Strategie Forex Roboter"],
        "tr": ["martingale uzman danışman forex", "pozisyon büyütme forex"],
        "id": ["martingale robot forex", "averaging forex ea"],
        "ko": ["마틴게일 자동매매 EA", "물타기 매매 전략"],
        "ar": ["مارتينجال مستشار خبير فوركس"],
        "fr": ["martingale robot forex"],
        "it": ["martingala expert advisor forex"],
        "th": ["มาติงเกล EA ฟอเร็กซ์"],
        "vi": ["nhồi lệnh martingale ea", "trung bình giá forex"],
    },
    "cat_tung_phan": {
        "en": ["partial close take profit levels ea", "scale out position ea forex"],
        "ru": ["частичное закрытие позиции советник", "частичный тейк профит mql5"],
        "ja": ["分割決済 EA 自動売買", "一部決済 手法 FX"],
        "zh": ["部分平仓 EA 外汇", "分批止盈 策略"],
        "pt": ["fechamento parcial robô forex", "saída parcial forex"],
        "es": ["cierre parcial robot forex", "salida escalonada forex"],
        "de": ["Teilschließung Expert Advisor", "Teilgewinnmitnahme Forex Roboter"],
        "tr": ["kısmi kapatma uzman danışman forex"],
        "id": ["close sebagian robot forex"],
        "ko": ["분할청산 자동매매"],
        "ar": ["إغلاق جزئي مستشار خبير فوركس"],
        "fr": ["clôture partielle robot forex"],
        "it": ["chiusura parziale expert advisor"],
        "th": ["ปิดบางส่วน EA ฟอเร็กซ์"],
        "vi": ["cắt từng phần ea", "chốt lời từng phần mt5"],
    },
    "khong_tin_hieu_vao": {
        "en": ["no entry signal grid ea", "always in market position management",
               "zero indicator trading robot forex"],
        "ru": ["советник без индикаторов", "торговля без сигналов входа советник"],
        "ja": ["インジケーター不要 EA", "エントリー条件なし 自動売買"],
        "zh": ["无指标 EA 外汇", "不看信号 网格 策略"],
        "pt": ["robô forex sem indicador"],
        "es": ["robot forex sin indicadores"],
        "de": ["Expert Advisor ohne Indikator"],
        "tr": ["indikatörsüz forex robotu"],
        "id": ["robot forex tanpa indikator"],
        "ko": ["지표 없는 자동매매 EA"],
        "ar": ["روبوت فوركس بدون مؤشرات"],
        "fr": ["robot forex sans indicateur"],
        "it": ["expert advisor senza indicatori"],
        "th": ["EA ไม่ใช้อินดิเคเตอร์"],
        "vi": ["ea không cần tín hiệu vào", "bot đặt lệnh không điều kiện"],
    },
    "dong_ro": {
        "en": ["basket close total profit expert advisor", "close all in profit ea"],
        "ru": ["закрытие корзины по общей прибыли советник"],
        "ja": ["合計利益 一括決済 EA"],
        "zh": ["总盈利 一键平仓 EA", "篮子 平仓 策略"],
        "pt": ["fechar cesta lucro total robô forex"],
        "es": ["cerrar cesta beneficio total robot"],
        "de": ["Korb schließen Gesamtgewinn Expert Advisor"],
        "tr": ["sepet kapatma toplam kar forex"],
        "id": ["close all profit robot forex"],
        "ko": ["전체 청산 수익 자동매매"],
        "ar": ["إغلاق السلة الربح الإجمالي"],
        "fr": ["clôture panier profit total robot"],
        "it": ["chiusura paniere profitto totale"],
        "th": ["ปิดทั้งหมด กำไรรวม EA"],
        "vi": ["đóng cả rổ khi tổng lãi ea"],
    },
}

#: mql5.com co ban dia phuong hoa day du, va **dien dan tung ban khac nhau**.
#: Day la loi lon nhat cua ban seeker cu: moi URL deu ghim `/en/`.
MQL5_BAN = ["en", "ru", "zh", "ja", "pt", "es", "de", "tr", "ko", "ar", "fr",
            "it", "th", "vi", "id"]


def tu_khoa(khai_niem: list[str] | None = None,
            ngon_ngu: list[str] | None = None,
            uu_tien_toi_da: int = 3) -> list[str]:
    """Danh sach tu khoa phang, da khu trung, giu thu tu uu tien ngon ngu.

    `uu_tien_toi_da=1` chi lay Nga/Nhat/Trung (+ Anh) - dung khi ngan sach mang
    hep. `=3` la tat ca 14 thu tieng.
    """
    kn = khai_niem or list(KHAI_NIEM)
    if ngon_ngu:
        cho_phep = set(ngon_ngu)
    else:
        cho_phep = {"en"} | {m for m, (_, u) in NGON_NGU.items()
                             if u <= uu_tien_toi_da}
    ra, thay = [], set()
    # Duyet theo do uu tien truoc, roi moi theo khai niem: neu bi cat ngan sach
    # giua chung thi cai con lai van la lop manh nhat.
    thu_tu = ["en"] + [m for m, _ in sorted(
        NGON_NGU.items(), key=lambda kv: (kv[1][1], kv[0]))]
    for m in thu_tu:
        if m not in cho_phep:
            continue
        for k in kn:
            for t in KHAI_NIEM.get(k, {}).get(m, []):
                if t not in thay:
                    thay.add(t)
                    ra.append(t)
    return ra


def theo_ngon_ngu(khai_niem: list[str] | None = None) -> dict[str, list[str]]:
    """Gom tu khoa theo ngon ngu - de bao cao va de chia me quet."""
    kn = khai_niem or list(KHAI_NIEM)
    ra: dict[str, list[str]] = {}
    for m in ["en"] + list(NGON_NGU):
        ds = [t for k in kn for t in KHAI_NIEM.get(k, {}).get(m, [])]
        if ds:
            ra[m] = ds
    return ra


def bang() -> str:
    """Bang do phu: khai niem x ngon ngu, de thay cho nao con trong."""
    ma = ["en"] + [m for m, _ in sorted(NGON_NGU.items(),
                                        key=lambda kv: (kv[1][1], kv[0]))]
    d = ["%-20s" % "khai niem" + "".join("%4s" % m for m in ma)]
    for k in KHAI_NIEM:
        d.append("%-20s" % k + "".join(
            "%4s" % (len(KHAI_NIEM[k].get(m, [])) or ".") for m in ma))
    tong = sum(len(v) for kn in KHAI_NIEM.values() for v in kn.values())
    d.append("%-20s" % "TONG" + "".join(
        "%4d" % sum(len(KHAI_NIEM[k].get(m, [])) for k in KHAI_NIEM) for m in ma))
    d.append("")
    d.append("tong %d tu khoa / %d khai niem / %d thu tieng"
             % (tong, len(KHAI_NIEM), len(ma)))
    return "\n".join(d)


if __name__ == "__main__":
    print(bang())
