# -*- coding: utf-8 -*-
"""test_bo_nao.py - Mo phong LLM de kiem tra wiring ca chuoi 8 vai (khong can key/MT5).

Chay bang pytest:   python -m pytest test_bo_nao.py
Chay tay:           python test_bo_nao.py

Dung DB tam + gia lap goi_llm / _chay_test. KHONG dong cham DB that.

Luu y: ban truoc dat toan bo doan nay o MUC MODULE va ket thuc bang sys.exit().
Pytest import file ten test_*.py de thu thap test, nen sys.exit o muc module nem
SystemExit ngay trong luc thu thap va lam do CA PHIEN pytest cua thu muc lab
(INTERNALERROR) - khong bo test nao khac chay duoc.
"""
import sys, tempfile
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

TRA = {
    "scout":     '{"lien_quan": true, "loai": "chien luoc", "uu_tien": 2}',
    "extractor": '[{"ten":"co_che_A","loai":"luoi","diem":9,"vao_lenh":"EMA entry","quan_ly":"dca","thoat":"tp","moi_so_voi_thu_vien":"moi"}]',
    "surveyor":  '{"phep_do":"MAE","tai_san_ung_vien":["EURCAD"],"tieu_chi_xep_hang":"dd"}',
    "mapper":    '{"anh_xa_duoc": true, "cau_hinh":[{"ten":"moc","input":{"LocEntry":1}},{"ten":"v2","input":{"LocEntry":2}}]}',
    "judge":     '{"phan_quyet":"CHUA_RO","ly_do":"can kiem cheo","buoc_tiep":[],"canh_bao":""}',
    "optimizer": '{"buoc_tiep":[{"ten":"o1","input":{"LocEntry":3}}]}',
    "coder":     '{"input_them":"","logic":"","diem_chen":"","kiem_thu":""}',
}

VAI_BAT_BUOC = {"scout", "extractor", "surveyor", "mapper", "test", "judge", "optimizer"}


def chay_mo_phong():
    """Chay het chuoi vai tren DB tam, tra ve (cac vai da XONG, bang co_che)."""
    import bo_nao as bn

    bn.DB = Path(tempfile.mkdtemp(prefix="bn_test_")) / "thu_vien.db"

    def fake_llm(vai, noi_dung):
        if vai not in TRA:
            raise RuntimeError("chua co mock cho vai " + vai)
        return TRA[vai]

    def fake_test(inp):
        ch = inp.get("cau_hinh") or [{}]
        return [{"pf": 1.4, "loi": 700, "dd": 300, "sharpe": 1.2, "lenh": 50,
                 "ten": ch[0].get("ten", "t"), "nam": 13.42}]

    bn.goi_llm = fake_llm
    bn._chay_test = fake_test

    con = bn.mo_db()
    mid = bn.bam("https://mock.example/a")
    con.execute("INSERT OR IGNORE INTO muc VALUES(?,?,?,?,?,0)",
                (mid, "mock", "mock A", "https://mock.example/a", 0))
    # van_ban dai de chay_vai khong goi fetch mang
    bn.tao_task(con, "scout", {"ten": "mock A", "url": "https://mock.example/a",
                               "van_ban": "x" * 900}, muc_id=mid, uu_tien=0)

    for _ in range(14):
        if not bn.chay_mot_nhip(con):
            break

    roles_done = {r[0] for r in con.execute(
        "select vai from cong_viec where trang_thai='XONG'")}
    co_che = con.execute("select id,ten,diem from co_che").fetchall()
    return roles_done, co_che


def test_wiring_chuoi_8_vai():
    """Ca chuoi vai phai chay het va de lai co_che dung diem."""
    roles_done, co_che = chay_mo_phong()
    thieu = VAI_BAT_BUOC - roles_done
    assert not thieu, f"vai chua chay: {sorted(thieu)}"
    assert co_che, "khong sinh duoc co_che nao"
    assert co_che[0][2] == 9, f"diem co_che = {co_che[0][2]}, cho 9"


def main() -> int:
    roles_done, co_che = chay_mo_phong()
    ok = bool(co_che) and co_che[0][2] == 9 and VAI_BAT_BUOC <= roles_done
    print("=== test_bo_nao ===")
    print("  XONG:", sorted(roles_done))
    print("  co_che:", co_che)
    print("  KET LUAN:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
