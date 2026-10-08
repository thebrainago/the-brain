/* luoi_nhan.c - NHAN C cho `nhan/luoi.py` (mo phong MOT ro luoi, MOT chieu). HAI mo hinh bar, chon bang `p[P_MO_HINH]`:
 *   0 = `cuc_tri`  : dich nguyen van `_mot_ro`      (mo hinh cu: khop o cuc tri cua nen; lac quan voi tia lenh - xem luoi.py)
 *   1 = `duong_di` : dich nguyen van `_mot_ro_duong` (mo hinh mac dinh tu 08/10/2026: nen di theo duong O->x->y->C)
 *
 * Vi sao co file nay: `_mot_ro` la vong lap Python ~3-8 us/bar. Quet 1.000 to hop tham so tren 190.000 bar M15 ton ~20 phut
 * tren mot nhan. Ban C chay cung phep tinh nay nhanh hon hai bac do lon va (qua ctypes) NHA GIL, nen quet duoc da luong that.
 *
 * LUAT SAT: day la ban DICH NGUYEN VAN cua ban Python - cung thu tu phep tinh, cung thu tu cong don, cung gia tri
 * bar 0 (`lai_arr[0]` = tru spread lenh dau). Ban Python van la CHUAN: `nhan/luoi_nhan.py` tu kiem nhan nay
 * voi ban Python truoc khi cho dung, va `test_luoi_nhan.py` doi chieu tren hang tram kich ban ngau nhien. Muon doi hanh vi:
 * sua ban Python TRUOC, roi dich lai day. Bien dich KHONG duoc dung -ffast-math / -ffp-contract=fast (FMA doi lam tron).
 *
 * Hai chi tiet "giong het Python" de khong lech tung bit (CHI cho mo hinh `cuc_tri`; `duong_di` cong tuan tu moi noi):
 *  - `tong_lot = sum(l ...)` cua Python >= 3.12 la cong BU Neumaier (khi cac l la float thuan); cac tong chua gia
 *    (np.float64) van cong tuan tu. Co `P_KAHAN` de chon.
 *  - min(a, b) cua Python tra `b` chi khi b < a.
 *
 * ABI: tham so goi qua mang double `p` (xem enum P_*) de ABI don gian, khong phu thuoc layout struct cua compiler.
 */
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#define LUOI_API __declspec(dllexport)
#else
#define LUOI_API __attribute__((visibility("default")))
#endif

#define LUOI_NHAN_PHIEN_BAN 4

/* chi so trong mang tham so `p` - GIU KHOP voi `luoi_nhan.py::_TEN_P` */
enum {
    P_LOT = 0, P_HOP, P_PIP, P_BUOC, P_TP, P_TRAN, P_KIEU, P_HE_LOT, P_HE_BUOC, P_BUOC_TRAN,
    P_CHO_LUI, P_TIA, P_BIEN_CAP, P_CAP_MOI_BAR, P_CHOT_TIEN, P_TY_LE, P_KAHAN, P_MO_HINH, P_SO
};

/* chi so trong mang thong ke `stats` */
enum { S_LAI_GOP = 0, S_PHI_SPREAD, S_PHI_SWAP, S_SO_RO, S_SO_LENH, S_TANG_MAX, S_SO_CAP, S_CON_MO, S_SO };

/* mot dong su kien ghi lenh: 8 double. kind 0 = mo (bar, gia, lot, id, tang, ro); kind 1 = dong (bar, gia, id, ly_do:
 * 0 = tp, 1 = tia) */
#define GHI_COT 8

#define LOI_BO_NHO (-1)
#define LOI_DAU_VAO (-2)
#define LOI_VONG (-3)                  /* `duong_di`: qua TOI_DA_VONG lan chot / them tang trong MOT doan don dieu (tham so suy bien) */

/* GIU KHOP `luoi.TOI_DA_VONG_DOAN` (test_luoi_duong_di kiem hai so nay bang nhau) */
#define TOI_DA_VONG 1000000
/* Dung sai "gia cham moc" cua `duong_di`, tinh bang PIP. GIU KHOP `luoi.EPS_CHAM_PIP` (test_luoi_duong_di kiem hai so nay bang nhau). */
#define EPS_CHAM_PIP 1e-6

typedef struct { double g; double l; int64_t id; } Pos;

typedef struct { Pos *a; int64_t cap; int64_t head; int64_t n; } Vao;   /* cac tang dang mo = a[head .. head+n) */

typedef struct { double *out; int64_t cap; int64_t n; int bat; } Ghi;

static int vao_khoi_tao(Vao *v, int64_t cap0) {
    v->cap = cap0 < 16 ? 16 : cap0;
    v->a = (Pos *)malloc((size_t)v->cap * sizeof(Pos));
    v->head = 0;
    v->n = 0;
    return v->a ? 0 : LOI_BO_NHO;
}

static int vao_them(Vao *v, double g, double l, int64_t id) {
    if (v->head + v->n >= v->cap) {
        if (v->head > 0) {                                   /* don ve dau mang truoc, chi nho khi het cho */
            memmove(v->a, v->a + v->head, (size_t)v->n * sizeof(Pos));
            v->head = 0;
        } else {
            int64_t moi = v->cap * 2;
            Pos *p = (Pos *)realloc(v->a, (size_t)moi * sizeof(Pos));
            if (!p) return LOI_BO_NHO;
            v->a = p;
            v->cap = moi;
        }
    }
    v->a[v->head + v->n].g = g;
    v->a[v->head + v->n].l = l;
    v->a[v->head + v->n].id = id;
    v->n++;
    return 0;
}

static void vao_dat_mot(Vao *v, double g, double l, int64_t id) {
    v->head = 0;
    v->n = 1;
    v->a[0].g = g;
    v->a[0].l = l;
    v->a[0].id = id;
}

static void ghi_mo(Ghi *s, int64_t bar, double gia, double lot, int64_t id, int64_t tang, int64_t ro) {
    if (s->bat) {
        if (s->n < s->cap) {
            double *r = s->out + s->n * GHI_COT;
            r[0] = 0.0; r[1] = (double)bar; r[2] = gia; r[3] = lot; r[4] = (double)id; r[5] = (double)tang;
            r[6] = (double)ro; r[7] = 0.0;
        }
        s->n++;
    }
}

static void ghi_dong(Ghi *s, int64_t bar, double gia, int64_t id, int ly_do) {
    if (s->bat) {
        if (s->n < s->cap) {
            double *r = s->out + s->n * GHI_COT;
            r[0] = 1.0; r[1] = (double)bar; r[2] = gia; r[3] = 0.0; r[4] = (double)id; r[5] = 0.0;
            r[6] = 0.0; r[7] = (double)ly_do;
        }
        s->n++;
    }
}

/* lot cua tang thu k (0-based); y het `_lot`. Tra NaN khi pow() tran so: Python `float ** int` nem OverflowError o do, nen de
 * Python tu xu ly (nhan C chi bao loi, khong tu doan hanh vi). */
static double lot_k(int kieu, double lot, double he, int64_t k) {
    if (kieu == 1) {                                               /* nhan: lot * he^k */
        double w = pow(he, (double)k);
        if (!isfinite(w)) return NAN;
        return lot * w;
    }
    if (kieu == 2) return lot * (1.0 + he * (double)k);           /* cong: lot * (1 + he*k) */
    return lot;                                                    /* phang */
}

/* khoang cach tu tang k den k+1 (pip, k tu 0); y het `_buoc` (min(a, b) cua Python: tra b chi khi b < a). NaN khi pow() tran so
 * (xem `lot_k`). */
static double buoc_k(double buoc, double he, double tran, int64_t k) {
    if (he == 1.0) return buoc;
    double w = pow(he, (double)k);
    if (!isfinite(w)) return NAN;
    double v = buoc * w;
    return (tran < v) ? tran : v;
}

/* sum(l for ...) cua Python. kahan = 0: cong tuan tu (Python <= 3.11, hoac phan tu khong phai float thuan).
 * kahan = 1: CPython >= 3.12 tren float thuan = Kahan-Babuska-Neumaier; phan tu dau cong vao int 0 nen thanh gia tri khoi dau. */
static double suma_lot(const Vao *v, int kahan) {
    const Pos *a = v->a + v->head;
    int64_t n = v->n;
    double f = 0.0;
    if (!kahan) {
        for (int64_t k = 0; k < n; k++) f += a[k].l;
        return f;
    }
    double c = 0.0;
    f = a[0].l;
    for (int64_t k = 1; k < n; k++) {
        double x = a[k].l;
        double t = f + x;
        if (fabs(f) >= fabs(x)) c += (f - t) + x;
        else c += (x - t) + f;
        f = t;
    }
    if (c != 0.0 && isfinite(c)) f += c;
    return f;
}

LUOI_API int32_t luoi_nhan_phien_ban(void) { return LUOI_NHAN_PHIEN_BAN; }
LUOI_API int32_t luoi_nhan_so_tham_so(void) { return P_SO; }

/* ====================================================================================================================
 * MO HINH `cuc_tri` (cu) - dich nguyen van `luoi._mot_ro`. Tra 0 neu xong; <0 neu loi (LOI_BO_NHO, LOI_DAU_VAO).
 * `*ghi_n` = TONG so su kien (co the > ghi_cap: goi lai voi bo dem lon hon).
 * ==================================================================================================================== */
static int32_t mot_ro_cuc_tri(const double *hi, const double *lo, const double *cl, const double *spread,
                              const double *dem, int64_t n, int32_t chieu, const double *p, double *lai_arr,
                              double *treo_arr, double *stats, int32_t ghi_bat, double *ghi_out, int64_t ghi_cap,
                              int64_t *ghi_n) {
    *ghi_n = 0;
    if (n < 1 || chieu == 0) return LOI_DAU_VAO;
    const double lot = p[P_LOT], hop = p[P_HOP], pip = p[P_PIP], buoc = p[P_BUOC], tran = p[P_TRAN];
    const int kieu = (int)p[P_KIEU];
    const double he_lot = p[P_HE_LOT], he_buoc = p[P_HE_BUOC], buoc_tran = p[P_BUOC_TRAN];
    const double cho_lui = p[P_CHO_LUI], bien_cap = p[P_BIEN_CAP], cap_moi_bar = p[P_CAP_MOI_BAR];
    const double chot_tien = p[P_CHOT_TIEN], ty_le = p[P_TY_LE];
    const int tia = p[P_TIA] != 0.0;
    const int kahan = p[P_KAHAN] != 0.0;
    const double t = p[P_TP] * pip;
    const double c = (double)chieu;

    Vao v;
    if (vao_khoi_tao(&v, (int64_t)(tran > 0 && tran < 1e6 ? tran + 4 : 64)) != 0) return LOI_BO_NHO;
    Ghi g = {ghi_out, ghi_cap, 0, ghi_bat};
    int rc = 0;

    const double lot0 = lot_k(kieu, lot, he_lot, 0);
    int64_t n_id = 1, ro_hien = 0;
    vao_dat_mot(&v, cl[0], lot0, 0);
    ghi_mo(&g, 0, cl[0], lot0, 0, 0, 0);
    double cho = 0.0;                  /* != 0: dang CHO gia lui toi muc nay moi mo L1 */
    double lai = 0.0, phi_sp = 0.0, phi_sw = 0.0;
    int64_t so_ro = 0, so_lenh = 0, so_cap = 0;
    int64_t so_tang = 1, tang_max = 1;
    double tong_lot;
    phi_sp += spread[0] * lot * hop;   /* NB: `ts.lot`, khong phai lot cua tang 0 - y het Python */
    const double phi_sp_bar0 = phi_sp; /* chi phi DA PHAT SINH luc bar 0 (khong phai tong ca chuoi) */
    so_lenh += 1;
    tong_lot = lot;

    for (int64_t i = 1; i < n; i++) {
        /* ---- 0. dang CHO gia lui de mo L1 ---- */
        if (cho != 0.0) {
            int cham0 = chieu > 0 ? (lo[i] <= cho) : (hi[i] >= cho);
            if (cham0) {
                vao_dat_mot(&v, cho, lot0, n_id);
                ro_hien += 1;
                ghi_mo(&g, i, cho, lot0, n_id, 0, ro_hien);
                n_id += 1;
                so_lenh += 1;
                phi_sp += spread[i] * lot0 * hop;
                cho = 0.0;
            } else {
                lai_arr[i] = lai - phi_sp - phi_sw;
                treo_arr[i] = 0.0;
                continue;
            }
        }
        /* ---- 1. BAT LOI TRUOC: them tang ---- */
        if (v.n == 0) { rc = LOI_DAU_VAO; goto xong; }           /* Python se IndexError o day: de Python bao */
        if ((double)v.n < tran) {
            double b0 = buoc_k(buoc, he_buoc, buoc_tran, so_tang - 1);
            if (isnan(b0)) { rc = LOI_DAU_VAO; goto xong; }
            double moc = v.a[v.head + v.n - 1].g - c * b0 * pip;
            while (chieu > 0 ? (lo[i] <= moc) : (hi[i] >= moc)) {
                double lk = lot_k(kieu, lot, he_lot, so_tang);
                if (isnan(lk)) { rc = LOI_DAU_VAO; goto xong; }
                phi_sp += spread[i] * lk * hop;
                if ((rc = vao_them(&v, moc, lk, n_id)) != 0) goto xong;
                ghi_mo(&g, i, moc, lk, n_id, so_tang, ro_hien);
                n_id += 1;
                so_tang += 1;
                so_lenh += 1;
                if ((double)v.n >= tran) break;
                double b1 = buoc_k(buoc, he_buoc, buoc_tran, so_tang - 1);
                if (isnan(b1)) { rc = LOI_DAU_VAO; goto xong; }
                moc = moc - c * b1 * pip;
            }
        }
        if (v.n > tang_max) tang_max = v.n;
        /* ---- 2. phi qua dem cho cac tang dang mo ---- */
        tong_lot = suma_lot(&v, kahan);
        if (dem[i] != 0.0) phi_sw += tong_lot * hop * ty_le * dem[i] / 365.0 * cl[i];
        /* ---- 3. lo treo sau nhat trong bar ---- */
        {
            double xau = chieu > 0 ? lo[i] : hi[i];
            double treo = 0.0;
            for (int64_t k = 0; k < v.n; k++) {
                double d = c * (v.a[v.head + k].g - xau);
                if (d > 0) treo += d * v.a[v.head + k].l;
            }
            treo_arr[i] = treo * hop;
        }
        /* ---- 3b. TIA LENH: ghep tang SAU NHAT voi tang DAU TIEN ---- */
        if (tia && v.n >= 2) {
            double tot = chieu > 0 ? hi[i] : lo[i];
            double da = 0.0;
            while (v.n >= 2 && da < cap_moi_bar) {
                const Pos *pd = &v.a[v.head], *pc = &v.a[v.head + v.n - 1];
                double lai_cap = (c * (tot - pc->g) * pc->l + c * (tot - pd->g) * pd->l) * hop;
                if (lai_cap < bien_cap * pip * (pd->l + pc->l) * hop) break;
                lai += lai_cap;
                phi_sp += spread[i] * (pd->l + pc->l) * hop;
                so_cap += 1;
                da += 1.0;
                ghi_dong(&g, i, tot, pd->id, 1);
                ghi_dong(&g, i, tot, pc->id, 1);
                v.head += 1;
                v.n -= 2;
            }
            if (v.n == 0) {
                /* tia het ca ro -> mo lai mot lenh moi, ladder ve 0 */
                so_tang = 1;
                vao_dat_mot(&v, cl[i], lot0, n_id);
                ro_hien += 1;
                ghi_mo(&g, i, cl[i], lot0, n_id, 0, ro_hien);
                n_id += 1;
                so_lenh += 1;
                phi_sp += spread[i] * lot0 * hop;
            }
            tong_lot = suma_lot(&v, kahan);
        }
        /* gia trung binh CO TRONG SO LOT */
        {
            double s_lg = 0.0;
            for (int64_t k = 0; k < v.n; k++) s_lg += v.a[v.head + k].l * v.a[v.head + k].g;
            double tb = s_lg / tong_lot;
            double mtp, loi_chot;
            int cham;
            if (chot_tien > 0) {
                double tot = chieu > 0 ? hi[i] : lo[i];
                double s_ln = 0.0;
                for (int64_t k = 0; k < v.n; k++) s_ln += c * (tot - v.a[v.head + k].g) * v.a[v.head + k].l;
                double lai_noi = s_ln * hop;
                double nguong = chot_tien * (lot / 0.01);
                cham = lai_noi >= nguong;
                mtp = tot;
                loi_chot = lai_noi;
            } else {
                mtp = tb + c * t;
                cham = chieu > 0 ? (hi[i] >= mtp) : (lo[i] <= mtp);
                loi_chot = tong_lot * hop * t;
            }
            if (cham) {
                lai += loi_chot;
                so_ro += 1;
                for (int64_t k = 0; k < v.n; k++) ghi_dong(&g, i, mtp, v.a[v.head + k].id, 0);
                treo_arr[i] = 0.0;
                so_tang = 1;
                if (cho_lui > 0) {
                    cho = mtp - c * cho_lui * pip;          /* khong mo lai ngay: cho gia lui */
                    v.n = 0;
                    v.head = 0;
                } else {
                    vao_dat_mot(&v, mtp, lot0, n_id);
                    ro_hien += 1;
                    ghi_mo(&g, i, mtp, lot0, n_id, 0, ro_hien);
                    n_id += 1;
                    so_lenh += 1;
                    phi_sp += spread[i] * lot0 * hop;
                }
            }
        }
        lai_arr[i] = lai - phi_sp - phi_sw;
    }
    lai_arr[0] = -phi_sp_bar0;        /* y het Python: lai chot 0 tru spread lenh dau (sua 03/10/2026, truoc la tong ca chuoi) */
    treo_arr[0] = 0.0;
    stats[S_LAI_GOP] = lai;
    stats[S_PHI_SPREAD] = phi_sp;
    stats[S_PHI_SWAP] = phi_sw;
    stats[S_SO_RO] = (double)so_ro;
    stats[S_SO_LENH] = (double)so_lenh;
    stats[S_TANG_MAX] = (double)tang_max;
    stats[S_SO_CAP] = (double)so_cap;
    stats[S_CON_MO] = (double)v.n;
    *ghi_n = g.n;
xong:
    free(v.a);
    return rc;
}

/* ====================================================================================================================
 * MO HINH `duong_di` - dich nguyen van `luoi._mot_ro_duong` (doc docstring cua ham do truoc khi sua day).
 * Moi bar (i >= 1) di tren duong o -> x -> y -> cl[i]; moi doan la mot nhat cat thang, moi su kien khop o GIA NGUONG cua no.
 * KHAC `cuc_tri`: MOI tong deu cong TUAN TU tung phan tu (khong Neumaier) nen khong co P_KAHAN; spread chi tru luc mo lenh.
 * ==================================================================================================================== */
typedef struct {
    Vao v;                                                   /* cac tang dang mo cua ro hien tai */
    Ghi g;
    const double *sp;                                        /* spread theo GIA, theo bar */
    double lot, hop, pip, buoc, tran, he_lot, he_buoc, buoc_tran, cho_lui, bien_cap, cap_moi_bar, chot_tien, nguong_tien, t;
    double eps;                                              /* dung sai "cham moc" = EPS_CHAM_PIP * pip */
    int kieu, tia;
    double s;                                                /* chieu: +1.0 / -1.0 (Python: s = int +-1; phep nhan voi +-1 chinh xac) */
    double cho;                                              /* != 0: dang CHO gia lui toi muc nay moi mo L1 */
    double lai, phi_sp, phi_sw;
    int64_t so_ro, so_lenh, so_cap, so_tang, tang_max, n_id, ro_hien, da_bar;
} Duong;

/* Mo MOT lenh tang k o gia `gia` (moi_ro: lenh dau cua ro moi). Y het `mo_lenh` Python. */
static int d_mo_lenh(Duong *D, int64_t i, double gia, int64_t k, int moi_ro) {
    double lk = lot_k(D->kieu, D->lot, D->he_lot, k);
    if (isnan(lk)) return LOI_DAU_VAO;                       /* pow() tran so: Python nem OverflowError - de Python bao */
    D->phi_sp += D->sp[i] * lk * D->hop;
    D->so_lenh += 1;
    if (moi_ro) {
        D->ro_hien += 1;
        vao_dat_mot(&D->v, gia, lk, D->n_id);
    } else {
        int rc = vao_them(&D->v, gia, lk, D->n_id);
        if (rc != 0) return rc;
    }
    ghi_mo(&D->g, i, gia, lk, D->n_id, k, D->ro_hien);
    D->n_id += 1;
    return 0;
}

/* Doan NGUOC chieu ro tu a den b (a == b: nhay gia luc mo nen). Y het `lui` Python. */
static int d_lui(Duong *D, int64_t i, double a, double b) {
    const double s = D->s;
    int rc;
    if (D->cho != 0.0) {
        if (s * (D->cho - b) < -D->eps) return 0;            /* chua lui toi muc cho */
        double gg = (s * (D->cho - a) <= 0) ? D->cho : a;
        if ((rc = d_mo_lenh(D, i, gg, 0, 1)) != 0) return rc;
        D->so_tang = 1;
        D->cho = 0.0;
        a = gg;
    }
    if (D->v.n == 0) return LOI_DAU_VAO;                     /* Python se IndexError o vao[-1]: de Python bao */
    if ((double)D->v.n < D->tran) {
        double b0 = buoc_k(D->buoc, D->he_buoc, D->buoc_tran, D->so_tang - 1);
        if (isnan(b0)) return LOI_DAU_VAO;
        double moc = D->v.a[D->v.head + D->v.n - 1].g - s * b0 * D->pip;
        int64_t vong = 0;
        while (s * (moc - b) >= -D->eps) {
            if (++vong > TOI_DA_VONG) return LOI_VONG;
            double gg = (s * (moc - a) <= 0) ? moc : a;      /* nhay gia vuot moc: khop o gia dau doan */
            if ((rc = d_mo_lenh(D, i, gg, D->so_tang, 0)) != 0) return rc;
            D->so_tang += 1;
            if ((double)D->v.n >= D->tran) break;
            double b1 = buoc_k(D->buoc, D->he_buoc, D->buoc_tran, D->so_tang - 1);
            if (isnan(b1)) return LOI_DAU_VAO;
            moc = gg - s * b1 * D->pip;                      /* moc ke tiep tinh tu GIA KHOP THAT (EA: tu BID mo cua tang sau cung) */
        }
    }
    if (D->v.n > D->tang_max) D->tang_max = D->v.n;
    return 0;
}

/* Doan THUAN chieu ro tu a den b: tia cap + chot ro, moi cai o gia nguong cua no. Y het `len_` Python. */
static int d_len(Duong *D, int64_t i, double a, double b) {
    const double s = D->s;
    double p = a;
    int64_t vong = 0;
    int rc;
    while (D->v.n > 0) {
        if (++vong > TOI_DA_VONG) return LOI_VONG;
        const Pos *va = D->v.a + D->v.head;
        double tong = 0.0, sw = 0.0;
        for (int64_t k = 0; k < D->v.n; k++) { tong += va[k].l; sw += va[k].l * va[k].g; }
        double tb = sw / tong;
        double mtp;
        if (D->chot_tien > 0) mtp = tb + s * D->nguong_tien / (D->hop * tong);
        else mtp = tb + s * D->t;
        int la_tia = 0;
        double ps = 0.0;
        if (D->tia && D->v.n >= 2 && (double)D->da_bar < D->cap_moi_bar) {
            const Pos *pd = &va[0], *pc = &va[D->v.n - 1];
            ps = (pc->g * pc->l + pd->g * pd->l) / (pc->l + pd->l) + s * D->bien_cap * D->pip;
            la_tia = (s * ps <= s * mtp);                    /* bang nhau: tia truoc TP */
        }
        double g_ev = la_tia ? ps : mtp;
        if (s * (g_ev - b) > D->eps) break;                  /* chua toi trong doan nay */
        double e = (s * (g_ev - p) >= 0) ? g_ev : p;         /* nguong da bi vuot luc dau doan -> khop o gia hien tai */
        p = e;
        if (la_tia) {
            const Pos *pd = &va[0], *pc = &va[D->v.n - 1];
            D->lai += (s * (e - pc->g) * pc->l + s * (e - pd->g) * pd->l) * D->hop;
            D->so_cap += 1;
            D->da_bar += 1;
            ghi_dong(&D->g, i, e, pd->id, 1);
            ghi_dong(&D->g, i, e, pc->id, 1);
            D->v.head += 1;
            D->v.n -= 2;
            if (D->v.n == 0) {                               /* tia het ca ro -> mo lai mot lenh moi, ladder ve 0 */
                D->so_tang = 1;
                if ((rc = d_mo_lenh(D, i, e, 0, 1)) != 0) return rc;
            }
        } else {
            double acc = 0.0;
            for (int64_t k = 0; k < D->v.n; k++) acc += s * (e - va[k].g) * va[k].l;
            D->lai += acc * D->hop;
            D->so_ro += 1;
            for (int64_t k = 0; k < D->v.n; k++) ghi_dong(&D->g, i, e, va[k].id, 0);
            D->so_tang = 1;
            if (D->cho_lui > 0) {
                D->cho = e - s * D->cho_lui * D->pip;        /* khong mo lai ngay: cho gia lui */
                D->v.n = 0;
                D->v.head = 0;
            } else {
                if ((rc = d_mo_lenh(D, i, e, 0, 1)) != 0) return rc;
            }
        }
    }
    return 0;
}

/* Lo noi (duong) cua cac tang dang mo neu gia hien tai la `gia`. Y het `treo_tai` Python. */
static double d_treo_tai(const Duong *D, double gia) {
    const Pos *va = D->v.a + D->v.head;
    double acc = 0.0;
    for (int64_t k = 0; k < D->v.n; k++) {
        double d = D->s * (va[k].g - gia);
        if (d > 0) acc += d * va[k].l;
    }
    return acc * D->hop;
}

static int32_t mot_ro_duong(const double *hi, const double *lo, const double *cl, const double *spread,
                            const double *dem, int64_t n, int32_t chieu, const double *p, double *lai_arr,
                            double *treo_arr, double *stats, int32_t ghi_bat, double *ghi_out, int64_t ghi_cap,
                            int64_t *ghi_n) {
    *ghi_n = 0;
    if (n < 1 || (chieu != 1 && chieu != -1)) return LOI_DAU_VAO;
    /* Mien cua `duong_di` (GIU KHOP `luoi.mien_duong_di`): du lieu va tham so huu han; Python nem ValueError cho cung nhung ca nay */
    for (int64_t i = 0; i < n; i++)
        if (!(isfinite(hi[i]) && isfinite(lo[i]) && isfinite(cl[i]) && isfinite(spread[i]) && isfinite(dem[i]))) return LOI_DAU_VAO;
    for (int k = 0; k < P_SO; k++)
        if (!isfinite(p[k])) return LOI_DAU_VAO;
    if (!(p[P_LOT] > 0 && p[P_BUOC] > 0 && p[P_TP] > 0 && p[P_TRAN] >= 1 && p[P_PIP] > 0 && p[P_HOP] > 0 && p[P_HE_BUOC] > 0 &&
          p[P_CHO_LUI] >= 0 && p[P_BUOC_TRAN] >= 0 && p[P_HE_LOT] >= 0 && p[P_CHOT_TIEN] >= 0))
        return LOI_DAU_VAO;

    Duong D;
    memset(&D, 0, sizeof D);
    D.sp = spread;
    D.lot = p[P_LOT]; D.hop = p[P_HOP]; D.pip = p[P_PIP]; D.buoc = p[P_BUOC]; D.tran = p[P_TRAN];
    D.kieu = (int)p[P_KIEU];
    D.he_lot = p[P_HE_LOT]; D.he_buoc = p[P_HE_BUOC]; D.buoc_tran = p[P_BUOC_TRAN];
    D.cho_lui = p[P_CHO_LUI]; D.bien_cap = p[P_BIEN_CAP]; D.cap_moi_bar = p[P_CAP_MOI_BAR]; D.chot_tien = p[P_CHOT_TIEN];
    D.tia = p[P_TIA] != 0.0;
    D.s = (double)chieu;
    D.t = p[P_TP] * D.pip;
    D.eps = EPS_CHAM_PIP * D.pip;                            /* dung sai "cham moc" (y het Python: EPS_CHAM_PIP * pip) */
    D.nguong_tien = D.chot_tien * (D.lot / 0.01);            /* chot theo tien: quy ve 0,01 lot goc (y het Python) */
    const double ty_le = p[P_TY_LE];

    if (vao_khoi_tao(&D.v, (int64_t)(D.tran < 1e6 ? D.tran + 4 : 64)) != 0) return LOI_BO_NHO;
    D.g.out = ghi_out; D.g.cap = ghi_cap; D.g.n = 0; D.g.bat = ghi_bat;
    int rc = 0;

    const double lot0 = lot_k(D.kieu, D.lot, D.he_lot, 0);
    if (isnan(lot0)) { rc = LOI_DAU_VAO; goto xong; }
    D.n_id = 1; D.ro_hien = 0;
    vao_dat_mot(&D.v, cl[0], lot0, 0);
    ghi_mo(&D.g, 0, cl[0], lot0, 0, 0, 0);
    D.so_lenh = 1; D.so_tang = 1; D.tang_max = 1;
    D.phi_sp += spread[0] * D.lot * D.hop;                   /* NB: `ts.lot`, khong phai lot cua tang 0 - y het Python */
    const double phi_sp_bar0 = D.phi_sp;

    for (int64_t i = 1; i < n; i++) {
        double hi_i = hi[i], lo_i = lo[i], cl_i = cl[i];
        double o = cl[i - 1];                                /* gia mo ~ dong bar truoc (chua co cot open), kep vao [low, high] */
        if (o < lo_i) o = lo_i;
        if (o > hi_i) o = hi_i;
        double pts[3];
        if (cl_i >= o) { pts[0] = lo_i; pts[1] = hi_i; }     /* nen xanh: xuong low truoc */
        else           { pts[0] = hi_i; pts[1] = lo_i; }     /* nen do: len high truoc */
        pts[2] = cl_i;
        D.da_bar = 0;
        if ((rc = d_lui(&D, i, o, o)) != 0) goto xong;       /* nhay gia luc mo nen */
        double treo_bar = d_treo_tai(&D, o);
        double a = o;
        for (int j = 0; j < 3; j++) {
            double b = pts[j];
            double d = D.s * (b - a);
            if (d < 0) { if ((rc = d_lui(&D, i, a, b)) != 0) goto xong; }
            else if (d > 0) { if ((rc = d_len(&D, i, a, b)) != 0) goto xong; }
            double f = d_treo_tai(&D, b);
            if (f > treo_bar) treo_bar = f;
            a = b;
        }
        if (D.v.n > 0 && dem[i] != 0.0) {
            double tl = 0.0;
            for (int64_t k = 0; k < D.v.n; k++) tl += D.v.a[D.v.head + k].l;
            D.phi_sw += tl * D.hop * ty_le * dem[i] / 365.0 * cl_i;
        }
        lai_arr[i] = D.lai - D.phi_sp - D.phi_sw;
        treo_arr[i] = treo_bar;
    }
    lai_arr[0] = -phi_sp_bar0;
    treo_arr[0] = 0.0;
    stats[S_LAI_GOP] = D.lai;
    stats[S_PHI_SPREAD] = D.phi_sp;
    stats[S_PHI_SWAP] = D.phi_sw;
    stats[S_SO_RO] = (double)D.so_ro;
    stats[S_SO_LENH] = (double)D.so_lenh;
    stats[S_TANG_MAX] = (double)D.tang_max;
    stats[S_SO_CAP] = (double)D.so_cap;
    stats[S_CON_MO] = (double)D.v.n;
    *ghi_n = D.g.n;
xong:
    free(D.v.a);
    return rc;
}

/* ---- Diem vao duy nhat cho ctypes: chon mo hinh theo p[P_MO_HINH] (0 = cuc_tri, 1 = duong_di; gia tri khac -> LOI_DAU_VAO) ---- */
LUOI_API int32_t luoi_mot_ro(const double *hi, const double *lo, const double *cl, const double *spread,
                             const double *dem, int64_t n, int32_t chieu, const double *p, double *lai_arr,
                             double *treo_arr, double *stats, int32_t ghi_bat, double *ghi_out, int64_t ghi_cap,
                             int64_t *ghi_n) {
    const double mh = p[P_MO_HINH];
    if (mh == 0.0)
        return mot_ro_cuc_tri(hi, lo, cl, spread, dem, n, chieu, p, lai_arr, treo_arr, stats, ghi_bat, ghi_out, ghi_cap, ghi_n);
    if (mh == 1.0)
        return mot_ro_duong(hi, lo, cl, spread, dem, n, chieu, p, lai_arr, treo_arr, stats, ghi_bat, ghi_out, ghi_cap, ghi_n);
    *ghi_n = 0;
    return LOI_DAU_VAO;
}
