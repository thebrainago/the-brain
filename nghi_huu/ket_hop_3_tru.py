# -*- coding: utf-8 -*-
r"""ket_hop_3_tru.py - BO DIEU PHOI DA NHIEM: chay SEEKER + QUANTLAB + BANKER
SONG SONG (ProcessPoolExecutor, 3 tien trinh), moi tru lam viec THAT, gop ve 1 state.
Chay:  python ket_hop_3_tru.py
Ghi:
  - lab/ket_hop_state.json        : ket qua 3 tru
  - lab/reports/TONG_HOP_3_TRU.md : 1 bao cao duy nhat
  - lab/BAN_GIAO.json             : ban giao / chuyen may
"""
import sys, json, io, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

THU_MUC = Path(__file__).resolve().parent
REPORTS = THU_MUC / "reports"
QUANT = THU_MUC / "quant"
sys.path.insert(0, str(THU_MUC))
sys.path.insert(0, str(QUANT))


def _task_seeker():
    import seeker_quy_tac as S
    t0 = time.time()
    r = S.chay_tru()
    r["giay"] = round(time.time() - t0, 1)
    return r


def _task_quantlab():
    t0 = time.time()
    try:
        import auto_kham_pha as ak
        kq = ak.chay(out="ket_qua_auto.json", n_perm=99)
        top = kq["dat"] or kq["da_quet"] or []
        top = sorted(top, key=lambda x: -x.get("edge", 0))[:8]
        return {"tru": "QUANTLAB", "giay": round(time.time() - t0, 1),
                "da_quet": len(kq["da_quet"]), "dat": len(kq["dat"]),
                "top": [{k: v for k, v in r.items()
                         if k in ("ten", "params", "symbol", "edge", "lai", "buy_hold",
                                  "pf", "sharpe", "so_lenh", "placebo_p", "era_edges", "dat")}
                        for r in top]}
    except Exception as e:
        return {"tru": "QUANTLAB", "giay": round(time.time() - t0, 1), "loi": str(e)}


def _task_banker():
    t0 = time.time()
    try:
        import bo_nao, banker
        con = bo_nao.mo_db()
        brief = banker.cap_nhat_macro_brief(con)
        return {"tru": "BANKER", "giay": round(time.time() - t0, 1), "brief": brief}
    except Exception as e:
        return {"tru": "BANKER", "giay": round(time.time() - t0, 1), "loi": str(e)}


def main():
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(_task_seeker), ex.submit(_task_quantlab), ex.submit(_task_banker)]
        ba = [ft.result() for ft in futs]
    tong = time.time() - t0
    kq = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "tong_giay": round(tong, 1),
          "timing": {b.get("tru", "?") + "_giay": b.get("giay", 0) for b in ba},
          "ba_tru": ba}
    (THU_MUC / "ket_hop_state.json").write_text(
        json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# TỔNG HỢP 3 TRỤ (chạy SONG SONG)", "> Lúc: " + kq["luc"] +
             " · tổng thời gian: " + str(round(tong, 1)) + "s (3 trụ chạy đồng thời)", ""]
    for b in ba:
        lines.append("## " + b.get("tru", "?"))
        lines.append("```"); lines.append(json.dumps(b, ensure_ascii=False, indent=1)); lines.append("```")
    (REPORTS / "TONG_HOP_3_TRU.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"=== DA NHIEM: tong {tong:.1f}s ===")
    for b in ba:
        print(f"  {b.get('tru')}: {b.get('giay')}s")
    print("thoi gian cac tru:", kq["timing"])
    print("(neu tong < tong cac tru con lai -> that su song song)")
    print("DA GHI:", THU_MUC / "ket_hop_state.json", "|", REPORTS / "TONG_HOP_3_TRU.md")


if __name__ == "__main__":
    main()
