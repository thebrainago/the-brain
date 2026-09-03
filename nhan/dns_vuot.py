# -*- coding: utf-8 -*-
"""dns_vuot.py - VUOT DNS BI DAU DOC, giu nguyen SNI va TLS that.

Do 03/09/2026, sau khi chu du an chi ra *"mql5 dang la nguon thuc chien nhat,
hay thu moi cach de truy cap duoc nguon nay, mo phong thao tac tay nguoi dung
chu dung lam nhu bot"*.

CHAN DOAN (do tung tang, khong doan):
  1. `nslookup www.mql5.com` tren may nay tra ve DUY NHAT mot dia chi IPv6
     `2401:fce0:31:1::247` — dai cua ISP Viet Nam, khong phai cua MQL5. Va
     `DNS request timed out` tren may chu dau tien. **DNS bi dau doc.**
  2. Hau qua o moi tang: `requests` -> `RemoteDisconnected`, Chrome ->
     `ERR_HTTP2_PROTOCOL_ERROR`, `curl` -> HTTP 000 o ca http/1.0, 1.1 va 2.
     Ba trieu chung khac nhau cua CUNG mot nguyen nhan — va do la ly do ghi
     chu cu doan nham la "chan bot" hay "render bang JS".
  3. IP THAT lay qua DNS-over-HTTPS:
        Cloudflare -> 203.29.60.247
        Google     -> 36.255.76.151
     Noi thang vao 203.29.60.247 voi SNI dung + header trinh duyet that:
     **HTTP 200, Server: Caddy**, trang ve day du.

CACH LAM O DAY: va `socket.getaddrinfo` de chi rieng nhung ten trong `BAN_DO`
duoc phan giai sang IP that. Chon cach nay chu khong doi URL sang IP vi:
  - giu nguyen ten mien trong URL -> SNI va chung chi TLS van dung, khong phai
    tat xac thuc (`verify=False` la mo cua cho nguoi dung giua duong)
  - moi cho goi `requests`/`urllib` trong du an deu duoc huong, khong phai sua
    ~20 diem goi
  - Chrome dung `--host-resolver-rules` cho cung mot muc dich (xem
    `mo_chrome_cdp.MAP_TEN`)

KHONG phai de vuot chan cua CHU TRANG: mql5.com khong chan ta (no tra 200 khi
den duoc). Cai chan nam o giua duong, tren mang nay.
"""
from __future__ import annotations

import json
import socket
import urllib.request

#: ten mien -> IP that. Kiem lai dinh ky: MQL5 dung nhieu IP va chung co doi.
BAN_DO: dict[str, str] = {
    "www.mql5.com": "203.29.60.247",
    "mql5.com": "203.29.60.247",
}

_GOC = None


def tra_doh(ten: str, may_chu: str = "cloudflare") -> str | None:
    """Hoi IP that qua DNS-over-HTTPS. Dung de LAM MOI `BAN_DO` khi IP doi."""
    u = ({"cloudflare": f"https://cloudflare-dns.com/dns-query?name={ten}&type=A",
          "google": f"https://dns.google/resolve?name={ten}&type=A"}
         .get(may_chu))
    if not u:
        return None
    try:
        rq = urllib.request.Request(u, headers={"accept": "application/dns-json"})
        d = json.loads(urllib.request.urlopen(rq, timeout=15).read())
    except Exception:
        return None
    for x in (d.get("Answer") or []):
        if x.get("type") == 1 and x.get("data"):
            return str(x["data"])
    return None


def lam_moi(ten: str) -> str | None:
    """Hoi lai IP that va cap nhat `BAN_DO`. Tra IP moi, hoac None."""
    for may in ("cloudflare", "google"):
        ip = tra_doh(ten, may)
        if ip:
            BAN_DO[ten] = ip
            return ip
    return None


def bat() -> bool:
    """Bat va. Goi nhieu lan an toan. Tra True neu vua bat (khong phai da bat)."""
    global _GOC
    if _GOC is not None:
        return False
    _GOC = socket.getaddrinfo

    def _va(host, port, *a, **kw):
        ip = BAN_DO.get(str(host).lower())
        return _GOC(ip or host, port, *a, **kw)

    socket.getaddrinfo = _va
    return True


def tat() -> bool:
    """Tra `socket.getaddrinfo` ve nguyen trang."""
    global _GOC
    if _GOC is None:
        return False
    socket.getaddrinfo = _GOC
    _GOC = None
    return True


def dang_bat() -> bool:
    return _GOC is not None


class Bat:
    """`with dns_vuot.Bat():` — bat trong pham vi roi tra lai nguyen trang."""

    def __init__(self):
        self._da_bat_boi_toi = False

    def __enter__(self):
        self._da_bat_boi_toi = bat()
        return self

    def __exit__(self, *a):
        if self._da_bat_boi_toi:
            tat()
        return False
