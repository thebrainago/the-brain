# -*- coding: utf-8 -*-
"""Do hinh dang lan can cho hai ung vien song sot holdout (03/09/2026)."""
import sys, warnings
sys.path.insert(0, '.')
warnings.filterwarnings('ignore')
from nhan import ngu_phap as NP, mau as M
import do_on_dinh as OD

def main():
    NP.nap_vao_mau()
    for khung, ten in (('H4', 'macd_sma_200_strateg_close_duoi_sma12'),
                       ('D1', 'rsi_dao_chieu')):
        tam = M.MAU[ten].get('tham_so_tam') or (M.MAU[ten]['luoi'] or [{}])[0]
        print(f"\n=== {ten} @ US500CASH.{khung} ===", flush=True)
        print(f"    tam: {tam}", flush=True)
        r = OD.do_hinh_dang(ten, tam, 'US500CASH', khung, luong=1)
        if not r.get('do_duoc'):
            print(f"    KHONG DO DUOC: {r.get('ly_do')} "
                  f"(so_o={r.get('so_o')}, chay={r.get('chay_duoc')})", flush=True)
            continue
        print(f"    HINH DANG: {r['hinh_dang']}", flush=True)
        print(f"    so o {r['so_o']} / chay {r['chay_duoc']} / KHAC NHAU {r.get('so_o_khac_nhau')}", flush=True)
        print(f"    alpha tam {r['alpha_tam']}% | trung vi lan can {r['trung_vi_lan_can']}% "
              f"| tot nhat {r['o_tot_nhat']}%", flush=True)
        print(f"    o duong {r['ty_le_duong']}% | boi dinh {r['boi_dinh']} "
              f"| do doc mot buoc {r['do_doc_mot_buoc_pct']}%", flush=True)
        print(f"    tam la dinh: {r['tam_co_phai_dinh']}  ({r['giay']}s)", flush=True)

if __name__ == "__main__":
    main()
