---
name: da-agent
description: Chay he multi-agent (Claude lam bo nao, LLM re qua AI Box lam tay chan) cho BAT KY tac vu/du an nao: chia ke hoach DAG, giao LLM re, may cham, sua toi da 2 vong, phan bien cheo, Claude duyet cuoi. Dung khi viec co the chia thanh nhieu phan doc lap kiem duoc bang may (viet test, sinh the, dich, tom tat, quet).
---
# da-agent
1. Doc `da_agent/GIAO_THUC_CLAUDE.md` (6 pha) va `reports/da_agent/BAI_HOC.md` (cai gi LLM re lam tot / dung giao).
2. Viet ke hoach JSON o `da_agent/ke_hoach/<ten>.json` (mau: `viet_test_thu_1.json`): moi task co `id`, `vai` (re|nhanh|manh|pro), `prompt`, `cham` (json|khong_rong|py|phat_hien_ma|test_chay|module:ham), `phu_thuoc`.
3. `python3 -m da_agent chay da_agent/ke_hoach/<ten>.json` -> `reports/da_agent/<ten>_<gio>/` (BAO_CAO.md, ket_qua/, so_chi.jsonl).
4. Claude TU DOC ket qua, chay lai, roi moi nhan vao repo. Chi viec co may cham chay that moi dang tin; kiem toan bang doc = nhieu rac.
5. Khoa AI Box lay tu moi truong (khong bao gio ghi ra file). Tach thanh du an rieng: `python3 da_agent/dong_goi.py` -> `xuat/da_agent_du_an.zip`.
