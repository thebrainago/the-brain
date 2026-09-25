# GOI VIEC: NHA NGHIEN CUU — AI nam quyen nghien cuu (25/09/2026)

Phien cloud [DOC] tren nhanh `claude/autonomous-trading-system-rzzt7h`. Khong dung MT5
tester, khong ghi `nao.db` that, khong sua `config/*.json` co san. Phien [GHI] review roi gop.
Thiet ke day du: `tai_lieu/NHA_NGHIEN_CUU.md`.

## 1. Da lam gi

**Chan doan** (doc tu ma nguon): quyen "nghien cuu gi tiep theo" dang nam o chu du an +
`qwen/NHIEM_VU.json` viet tay + dong ho `dieu_phoi`; LLM runtime la qwen-flash chi de boc tach
(Claude bi loai khoi `tri_tue` tu 16/08); tru NGHI chi thay dem PASS/FAIL; **khong co khau nao
nhin vao tung lenh**. Pheu 162.330 o giu 0,13%, cai bi loai khong bao gio duoc hoi vi sao.

**Xay** (8 module `nhan/nc_*`, 16 cong cu, lenh `b nc`):

| Module | Viec |
|---|---|
| `nc_tac_tu` | vong tu chu Claude API (hien chuong, ngan sach cong cu/USD, tu choi, max_tokens, nhat ky chu ky) + driver Claude Code headless |
| `nc_cong_cu` | 16 cong cu, mot danh sach cho API / `b nc cc` / Python |
| `nc_so_tay` | `nc.db`: gia thuyet, thi nghiem (van tay), hieu biet (bang chung), cau hoi, vong, niem phong |
| `nc_thi_nghiem` | chay he (+ quan tri), tien o DD20 vs moc, quet + hinh dang, mo xe, xac nhan, niem phong 1 lan, danh muc, luoi AUDCAD, tang 2 kinh te |
| `nc_mo_xe` | tach lenh (phi thoat, lat chieu), HOC TU LENH, tim quy luat bar, MFE/MAE -> luat quan tri, null hieu chuan ca viec do tim |
| `nc_dac_trung` | 26 dac trung = toan hang ngu phap (luat tim ra chay thang, dich MQL5 duoc) |
| `nc_du_lieu` | 3 doan (kham pha / xac nhan / niem phong), 5 kich ban chuoi co dap an |
| `nc_tu_lai` | chuong trinh co dinh khong LLM + hieu chuan hai chieu + do cong suat |

**Noi vao he**: `b nc ...` (b.py), lop moi trong `nhan/kien_truc.LOP`, CLAUDE.md "LUAT SO 1",
bo sung `SO_DO_HE_THONG.txt` (danh dau ro la bo sung, khong sua so do goc), README.

**Sua mot loi co san** (commit rieng): `nhan/cong.py` tu 18/09 them dieu kien `12_rr_thuc_te`,
`13_edge_vuot_spread` ma khong xep vao `CHAN_CUNG`/`NHAN_MEM` -> o che do `"nhan"` (dang bat trong
`config/nguong.json`) MOI lan `cong.xet` nem KeyError. `test_cong_fdr_v2` bat duoc (3 do) nhung
chua ai sua. Xep ca hai vao `CHAN_CUNG` (dung chu thich "TANG 2 KINH TE: chan martingale tra
hinh"); sua fixture hai test FDR dung "he" loi 0 (nay truot tang 2 dung nhu thiet ke).

## 2. Bang chung (tat ca do trong phien, tai lap bang `b nc kiem 30`)

Hieu chuan HAI chieu tren chuoi co dap an (`reports/NC_HIEU_CHUAN.md`):

| Phep do | Ket qua |
|---|---|
| Tu lai tron ven, 7 chuoi | 6 dung · 1 chua ket luan (LOC: co che dung, 7 lenh o doan xac nhan -> CHUA_DO_DUOC) · **0 sai · 0 bao dong gia** |
| Hoc tu lenh (mo xe he goc "mua sau cu giam 3 bar") | LOC_1/LOC_2 tim dung `atr_pv < 0,39` (dap an 0,5), p = 0,005; he loc tren doan XAC NHAN: ky vong -62,7 -> **+16,0** bps, -15,8 -> **+10,6** bps, hon moc. Nhieu: p 0,64 / 0,82 -> khong tin. 4/4 dung |
| Bao dong gia `tim_quy_luat`, 30 hat nhieu | p <= 0,05: 6,7% · p <= 0,10: 13,3% (ky vong 5% / 10%) |
| Cong suat, edge yeu t ~ 2,3 sau phi, 8 hat | do tim rong **3/8** · gia thuyet co chu dich **8/8** (bao dong gia 0/8) |
| Bo test moi | 39 test (`test_nc_*`) + 41 test cong cu (`test_cong_*`) qua |

## 3. So truoc / sau

| | Truoc | Sau |
|---|---|---|
| Ai chon viec nghien cuu | nguoi + bang viet tay | AI (Claude) qua so tay; nguoi dat cau hoi uu tien |
| Khau hoc tu lenh thang/thua | 0 dong ma | `mo_xe_lenh` (bo loc + luat quan tri, null hieu chuan) |
| Bao dong gia bo tim quy luat (do tren 30 hat nhieu, p<=0,10) | 26,7% (ban dau, loi sd khong dieu kien) | 13,3% |
| `cong.xet` o che do `nhan` | KeyError moi lan goi (tu 18/09) | tra verdict; 41 test cong qua |
| Cong nha nghien cuu vs cong chinh thuc | (ban dau) cho DAT mot he truot tang 2 | dung chung `rr_thuc_te` + nguong `config/nguong.json` |

## 4. Rui ro con lai

1. Moi so o muc 2 tren chuoi TONG HOP. Chung chung minh cong cu khong noi doi tren chuoi biet dap
   an; KHONG chung minh thi truong that co edge. Chua chay tren du lieu that (o may chu du an).
2. Vong Claude API chua chay voi Claude that (khong co khoa tren cloud) - kiem bang client gia lap.
3. `thu_luoi` chi AUDCAD: `luoi.py` ghim phi qua dem AUDCAD va point 1e-5.
4. `xuat_mq5` chua dich luat quan tri (chi phan VAO).
5. Test cu do tren cloud KHONG do phien nay: `test_ma_nguon_sach` (seeker_deep.py dung f-string
   Python 3.12+, container 3.11), `test_kien_truc` (thu muc cha cua repo), `test_cua_vao` x2 (can
   `nao.db` da nap / tesseract). Deu ton tai truoc thay doi.

## 5. Viec chua lam (theo thu tu, chi tiet muc 8.2 cua thiet ke)

1. May chu du an: `b nc kiem` roi `b nc tu-lai AUDCAD H4` / `EURGBP H4` / `XAUUSDM H4` (du lieu +
   chi phi THAT).
2. `b nc claude --vong 3` voi cau hoi uu tien cua chu du an (tia lenh AUDCAD); so voi tu lai.
3. `luoi.py` nhan mo hinh chi phi -> `thu_luoi` cho moi ma.
4. Gan nha nghien cuu vao `dieu_phoi.py` (tru NHA_NGHIEN_CUU, thay NGHI) - can nhip tim `nao.db`.
5. Noi `reports/nc_yeu_cau_seeker.jsonl` vao `vuon_nguon`; `xuat_mq5` dich ca quan tri.
