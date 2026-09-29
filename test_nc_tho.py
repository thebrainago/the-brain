# -*- coding: utf-8 -*-
"""Tho (model re): chi co cong cu kham pha, doan bi ep ve kham_pha, moi thu ghi mang nguon 'tho'."""
from __future__ import annotations

import json

import pytest

from nhan import nc_so_tay as ST
from nhan import nc_tho as THO


@pytest.fixture(autouse=True)
def so_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    monkeypatch.setattr(THO, "LAB", tmp_path)
    yield


def test_tho_khong_co_cong_cu_tieu_doan_quy():
    ten = {t["function"]["name"] for t in THO.cong_cu_openai()}
    assert ten == set(THO.CONG_CU_THO)
    assert not ten & {"xac_nhan", "niem_phong", "xuat_mq5"}


def test_vong_tho_ep_kham_pha_tu_choi_niem_phong_va_danh_dau_nguon():
    cau = [{"choices": [{"message": {"content": "", "tool_calls": [
        {"id": "a", "type": "function", "function": {"name": "ghi_gia_thuyet", "arguments": json.dumps(
            {"cau": "EURGBP H4 hoi quy sau cu soc 1 bar khi bien dong cao",
             "vi_sao": "thanh khoan cheo cap mong"})}},
        {"id": "b", "type": "function", "function": {"name": "niem_phong", "arguments": "{}"}},
        {"id": "c", "type": "function", "function": {"name": "thu_luoi", "arguments": json.dumps(
            {"ma": "TONG_HOP_NHIEU_1", "khung": "H1", "doan": "xac_nhan",
             "tham_so": {"buoc": 40, "tp": 30, "tran_tang": 6}})}}]}}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 50}},
           {"choices": [{"message": {"content": "Da thu luoi tren nhieu: khong co gi."}}],
            "usage": {"prompt_tokens": 1200, "completion_tokens": 20}}]
    goi_cuoi = []

    def goi(than):
        goi_cuoi.append(than)
        return cau.pop(0)
    r = THO.chay_vong(goi=goi, so_cong_cu=10)
    assert r["so_cong_cu"] == 3 and r["token_vao"] == 2200 and "khong co gi" in r["ket_luan"]
    tool = {m["tool_call_id"]: m["content"] for m in goi_cuoi[-1]["messages"] if m["role"] == "tool"}
    assert "tho khong co cong cu" in tool["b"]
    assert '"doan":"kham_pha"' in tool["c"], tool["c"][:200]
    assert ST.mot("SELECT nguon FROM gia_thuyet ORDER BY id DESC LIMIT 1")["nguon"] == "tho"


def test_duong_tu_bien_moi_truong(monkeypatch):
    monkeypatch.setenv("THO_KHOA_ENV", "KHOA_GIA")
    monkeypatch.setenv("KHOA_GIA", "sk-khong-that")
    d = THO.duong()
    assert d["url"] == "https://api.deepseek.com/chat/completions" and d["mo_hinh"] == "deepseek-chat"
