# -*- coding: utf-8 -*-
"""Quy tac doc ket qua dang hoat dong cua THE BRAIN.

Ket qua va gia thuyet trong so la lich su chi-them. Vi vay mot dong ``PASS``
cu khong tu dong la bang chung hien hanh: no co the da bi supersede, bi
INVALIDATED, hoac gia thuyet cua no da bi quarantine. Cac man hinh va tru
phan tich phai dung module nay thay vi tu viet lai dieu kien SQL.
"""
from __future__ import annotations


TRANG_THAI_GIA_THUYET_KHONG_HOAT_DONG = (
    "QUARANTINED_V2",
    "INACTIVE",
    "SUPERSEDED",
)


def dieu_kien_gia_thuyet_hoat_dong(alias: str = "g") -> str:
    """Tra dieu kien SQL cho mot gia thuyet con hieu luc.

    ``UPPER`` giu tuong thich voi cac ban ghi cu viet thuong, trong khi danh
    sach trang thai van duoc khai bao mot cho de de audit.
    """
    trang_thai = ", ".join(f"'{x}'" for x in TRANG_THAI_GIA_THUYET_KHONG_HOAT_DONG)
    return f"UPPER(COALESCE({alias}.trang_thai, '')) NOT IN ({trang_thai})"


def dieu_kien_ket_qua_hoat_dong(k_alias: str = "k", gt_alias: str = "g") -> str:
    """Tra dieu kien SQL cho mot ket qua dang hoat dong."""
    return (
        f"{k_alias}.superseded_by IS NULL "
        f"AND UPPER(COALESCE({k_alias}.verdict, '')) <> 'INVALIDATED' "
        f"AND {dieu_kien_gia_thuyet_hoat_dong(gt_alias)}"
    )


def tu_ket_qua_hoat_dong(
    k_alias: str = "k", gt_alias: str = "g", *, join_them: str = ""
) -> str:
    """Tra ``FROM ... WHERE`` chung cho ket qua dang hoat dong.

    Dung ``JOIN`` (khong phai ``LEFT JOIN``) co chu y: ket qua khong con gia
    thuyet tuong ung khong du thong tin de duoc coi la bang chung hien hanh.
    ``join_them`` duoc chen truoc ``WHERE`` cho cac phep doi soat co bang phu.
    """
    return (
        f"FROM ket_qua {k_alias} "
        f"JOIN gia_thuyet {gt_alias} ON {gt_alias}.ma={k_alias}.gt_ma "
        f"{join_them} "
        f"WHERE {dieu_kien_ket_qua_hoat_dong(k_alias, gt_alias)}"
    )


def truy_van(
    cot: str,
    *,
    dieu_kien_them: str = "",
    nhom_theo: str = "",
    sap_xep: str = "",
    gioi_han: int | None = None,
) -> str:
    """Lap truy van SELECT tren tap ket qua dang hoat dong.

    Cac phan them la SQL noi bo, hang so trong ma nguon. Gia tri runtime van
    phai truyen bang placeholder qua ``SO.mot``/``SO.nhieu``.
    """
    sql = f"SELECT {cot} {tu_ket_qua_hoat_dong()}"
    if dieu_kien_them:
        sql += f" AND ({dieu_kien_them})"
    if nhom_theo:
        sql += f" GROUP BY {nhom_theo}"
    if sap_xep:
        sql += f" ORDER BY {sap_xep}"
    if gioi_han is not None:
        if gioi_han < 1:
            raise ValueError("gioi_han phai duong")
        sql += f" LIMIT {gioi_han}"
    return sql
