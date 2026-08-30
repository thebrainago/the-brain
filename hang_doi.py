# -*- coding: utf-8 -*-
"""
hang_doi.py - Dong bo VPS <-> may nha qua THU MUC CHUNG, khong lan viec nhau
=============================================================================
Nguyen tac VANG: PHAN VAI THEO HUONG GHI. Moi may chi GHI file cua rieng no.
Khong bao gio hai may ghi chung mot file -> khong the conflict qua Google Drive.

  VPS      : chi GHI  hang_doi_test.jsonl   (append cau hinh can test)
             chi DOC  ket_qua_test.jsonl
  MAY NHA  : chi DOC  hang_doi_test.jsonl
             chi GHI  ket_qua_test.jsonl    (append ket qua)

File .jsonl = append-only, moi dong mot JSON. Append an toan hon ghi de qua Drive.
"Da lam chua" nhan biet bang `id` dong -> khong can khoa phan tan.

Chong trung TREN MAY NHA (neu chay nhieu tien trinh cung luc): file khoa CUC BO
(khong qua Drive) `<id>.dang` — atomic create, ai tao duoc thi lam.

Dat THU_MUC_CHUNG = duong dan thu muc Google Drive Desktop gan tren ca hai may.
"""
import json
import os
import socket
import time
from pathlib import Path

THU_MUC_CHUNG = Path(os.environ.get("LAB_CHUNG",
                     r"C:\Users\SV STORE\Google Drive\lab_chung"))
HANG_DOI = THU_MUC_CHUNG / "hang_doi_test.jsonl"
KET_QUA = THU_MUC_CHUNG / "ket_qua_test.jsonl"
KHOA_CUC_BO = Path(os.environ.get("LAB_KHOA", r"C:\lab\khoa"))
MAY = socket.gethostname()


def _bao_dam_thu_muc():
    THU_MUC_CHUNG.mkdir(parents=True, exist_ok=True)
    KHOA_CUC_BO.mkdir(parents=True, exist_ok=True)
    for f in (HANG_DOI, KET_QUA):
        if not f.exists():
            f.touch()


def _doc_jsonl(f):
    if not f.exists():
        return []
    ra = []
    for d in f.read_text(encoding="utf-8").splitlines():
        d = d.strip()
        if d:
            try:
                ra.append(json.loads(d))
            except Exception:
                pass
    return ra


def _append(f, obj):
    # append-only, flush ngay de Drive dong bo som
    with open(f, "a", encoding="utf-8") as h:
        h.write(json.dumps(obj, ensure_ascii=False) + "\n")
        h.flush()
        os.fsync(h.fileno())


# ================= VAI VPS: xep hang doi =================
def vps_xep(job_id, symbol, input_set, tu, den, ghi_chu=""):
    """VPS goi: dua mot cau hinh vao hang doi test. input_set = dict input EA."""
    _bao_dam_thu_muc()
    _append(HANG_DOI, {"id": job_id, "symbol": symbol, "input": input_set,
                       "tu": tu, "den": den, "ghi_chu": ghi_chu,
                       "luc": time.time(), "boi": MAY})


def vps_ket_qua_moi(da_doc_ids):
    """VPS goi dinh ky: lay ket qua MOI (id chua thay) tu may nha."""
    _bao_dam_thu_muc()
    return [r for r in _doc_jsonl(KET_QUA) if r.get("id") not in da_doc_ids]


# ================= VAI MAY NHA: chay test =================
def maynha_job_cho():
    """May nha goi: lay cac job CHUA co ket qua va CHUA bi may khac giu."""
    _bao_dam_thu_muc()
    xong = {r["id"] for r in _doc_jsonl(KET_QUA)}
    ra = []
    for j in _doc_jsonl(HANG_DOI):
        if j["id"] in xong:
            continue
        ra.append(j)
    return ra


def maynha_giu(job_id):
    """Khoa cuc bo (khong qua Drive): atomic create. True = giu duoc, lam di."""
    KHOA_CUC_BO.mkdir(parents=True, exist_ok=True)
    k = KHOA_CUC_BO / f"{job_id}.dang"
    try:
        fd = os.open(str(k), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(time.time()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        # neu khoa qua cu (>90 phut) coi nhu tien trinh kia chet -> cuop
        try:
            if time.time() - k.stat().st_mtime > 5400:
                k.unlink()
                return maynha_giu(job_id)
        except Exception:
            pass
        return False


def maynha_xong(job_id, ket):
    """May nha goi sau khi chay tester: ghi ket qua + nha khoa cuc bo."""
    ket = dict(ket)
    ket["id"] = job_id
    ket["luc"] = time.time()
    ket["boi"] = MAY
    _append(KET_QUA, ket)
    try:
        (KHOA_CUC_BO / f"{job_id}.dang").unlink()
    except Exception:
        pass


if __name__ == "__main__":
    # tu kiem: xep 1 job (vai VPS), lay ra (vai may nha), ghi ket qua
    _bao_dam_thu_muc()
    print("thu muc chung:", THU_MUC_CHUNG)
    vps_xep("thu_001", "EURCAD", {"LocEntry": 1, "LechATR": 2.0}, "2013.03.01",
            "2026.07.31", "test dong bo")
    cho = maynha_job_cho()
    print("may nha thay", len(cho), "job cho")
    if cho and maynha_giu(cho[0]["id"]):
        maynha_xong(cho[0]["id"], {"pf": 1.29, "loi": 3672, "dd": 1763})
        print("da ghi ket qua job", cho[0]["id"])
    print("con lai cho:", len(maynha_job_cho()))
