# GIAO THUC DA TAC TU (05/10/2026) - Claude lam NAO, LLM re lam TAY CHAN

Chu du an (05/10): *"moi kho co cau hoi hay phien chat nao thi Claude nhan yeu cau, tu duy sau nhat de hieu y tuong, nhin nhu chuyen gia de dua tu y tuong toi he thong va thuc te voi kien thuc han lam, bo sung va sang tao ky cang va rong ... len so do thiet ke => giao viec cho llm, giam sat, doc ket qua, quan ly khau cuoi => tong ket va lap lai"*. Ap dung cho moi viec (khong chi The Brain). Voi The Brain: goi LLM nang cap moi module sau nhat co the; Claude giam sat bang kien thuc cao hon (CMT la vi du: dang le tu dau phai tu nghi toi, khong cho chu du an nhac).

## So do (nhan tu mau da co, giu cai hop, bo cai thua)
```
 chu du an --y tuong tho--> [1 HIEU]  Claude: y that su la gi, ai tra tien, thieu kien thuc gi (hoi lai chi khi KHONG tu quyet duoc)
                             [2 MO RONG] Claude voi tu cach chuyen gia: kien thuc han lam / thuc te, cach nguoi gioi lam, ruong sai thuong gap, phuong an thay the
                             [3 THIET KE] so do + tieu chi chap nhan + cai gi MAY cham duoc
                             [4 GIAO]   ke hoach = DAG viec (JSON) --> da_agent.chay
        +-------------------------+----------------------+
   [tay re qwen3.8-flash]   [tay nhanh ds-flash]   [tay manh qwen3.8-max / v4-pro] <- chi leo thang khi sai 2 vong
        |  moi viec: may cham (code) -> sua <= 2 vong -> phan bien CHEO (model khac) 
        +-------------------------+----------------------+
                             [5 GIAM SAT] Claude doc BAO_CAO.md, lay mau, tu kiem phat hien NANG (khong tin LLM)
                             [6 TONG KET] ghi bai hoc (reports/da_agent/BAI_HOC.md), cap nhat so ban giao, LAP LAI vong sau
```
Mau tham khao va cai ta lay: **Supervisor / hierarchical** (mot nao phan viec, noi phan cung duoc: dung) · **Planner-Executor + DAG** (ke hoach la du lieu, chay song song theo lop: `chay.py`) ·
**Reflexion / sua theo loi** (loi cu the cua may cham dua lai cho tay: <= 2 vong, vong cuoi leo thang) · **Critic / debate** (phan bien bang MODEL KHAC, khong tu cham minh) ·
**Blackboard** (moi ket qua vao `reports/da_agent/<chay>/ket_qua/`, viec sau doc ket qua viec truoc qua `dung`). Cai KHONG lay: swarm tu tri / agent tu goi agent khong gioi han (ton token, khong ai chiu trach nhiem).
Cai cua rieng The Brain thanh luat: **LLM khong tu cham diem; ba trang thai (DAT / HONG may cham = CHUA_DO_DUOC, khong phai AM); khong niem phong / sua `config/*` bang LLM.**

## Cach dung
1. Claude viet `da_agent/ke_hoach/<ten>.json`: `{"ten","muc_tieu","boi_canh","tasks":[{"id","vai":"re|nhanh|manh|pro","prompt","doc_tep":[...],"dung":[id...],"cham":{kieu...},"phan_bien":true|"nhanh","max_tokens","max_sua"}]}`.
2. `python3 -m da_agent chay da_agent/ke_hoach/<ten>.json` -> `reports/da_agent/<ten>_<gio>/` (ke_hoach, ket_qua/*.json, so_chi.jsonl, BAO_CAO.md).
3. Bo cham co san (`da_agent/cham.py`): `json` (khoa bat buoc), `khong_rong`, `py` (cu phap), `phat_hien_ma` (moi phat hien phai tro ham/lop CO THAT); them kieu `'module:ham'`.
4. Claude doc, lay mau, quyet. Chi cai Claude tu kiem moi duoc vao kho / ma.

## Chon che do cho Claude (tu chon, chu du an cho phep)
medium: giam sat thuong ngay (doc bao cao, lay mau, sua nho) - nhanh, du. max: buoc 1-3 (hieu y, mo rong chuyen gia, thiet ke kho), viec ma 1 sai lam doi huong ca du an, hoac khi LLM tra ket qua mau thuan nhau. LLM re: tat suy luan (bat = tran token + 502), `max_tokens` vua du.

## Bai hoc do that (cap nhat o `reports/da_agent/BAI_HOC.md`)
