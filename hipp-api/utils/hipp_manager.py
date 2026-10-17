"""hipp-manager 身份与钱包客户端（用户 Bearer + S2S）。"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from application import settings


class ManagerError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def enabled() -> bool:
    base = str(getattr(settings, "HIPP_MANAGER_BASE", "") or "").strip()
    return bool(base)


def s2s_enabled() -> bool:
    return enabled() and bool(str(getattr(settings, "HIPP_MANAGER_KEY", "") or "").strip())


def _base() -> str:
    return str(getattr(settings, "HIPP_MANAGER_BASE", "") or "").strip().rstrip("/")


def _s2s_key() -> str:
    return str(getattr(settings, "HIPP_MANAGER_KEY", "") or "").strip()


def _call(
    method: str,
    path: str,
    body: dict | None = None,
    access_token: str = "",
    query: dict | None = None,
    *,
    s2s: bool = False,
) -> dict:
    if not enabled():
        raise ManagerError("未配置 HIPP_MANAGER_BASE", status=503)
    if s2s and not _s2s_key():
        raise ManagerError("未配置 HIPP_MANAGER_KEY", status=503)
    url = _base() + path
    if query:
        qs = urllib.parse.urlencode(
            {k: v for k, v in query.items() if v is not None and v != ""}
        )
        if qs:
            url = url + ("&" if "?" in url else "?") + qs
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if s2s:
        req.add_header("X-Manager-Key", _s2s_key())
    if access_token:
        req.add_header("Authorization", "Bearer " + access_token)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except OSError as e:
        raise ManagerError("hipp-manager 不可达", status=502) from e
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError as e:
        raise ManagerError("hipp-manager 返回无法识别", status=502) from e
    if status >= 400:
        detail = ""
        if isinstance(payload, dict):
            detail = str(payload.get("detail") or payload.get("message") or "")
        raise ManagerError(detail or "hipp-manager 请求失败", status=status)
    return payload if isinstance(payload, dict) else {}


def sms_send(telephone: str) -> None:
    _call("POST", "/api/auth/sms/send", {"phone": telephone})


def sms_login(telephone: str, code: str) -> dict:
    return _call(
        "POST",
        "/api/auth/sms/login",
        {"phone": telephone, "code": code, "product": "or"},
    )


def password_login(telephone: str, password: str) -> dict:
    return _call("POST", "/api/auth/login", {"phone": telephone, "password": password})


def ops_login(username: str, password: str) -> dict:
    return _call(
        "POST",
        "/api/ops/auth/login",
        {"username": username, "password": password},
    )


def ops_verify(username: str, password: str) -> dict:
    return _call(
        "POST",
        "/api/ops/auth/verify",
        {"username": username, "password": password},
    )


def ops_me(access_token: str) -> dict:
    return _call("GET", "/api/ops/auth/me", None, access_token=access_token)


def me(access_token: str) -> dict:
    return _call("GET", "/api/auth/me", None, access_token=access_token)


def wallet_balance(access_token: str) -> dict:
    return _call("GET", "/api/wallet/balance", access_token=access_token)


def wallet_presets(access_token: str) -> dict:
    return _call("GET", "/api/wallet/presets", access_token=access_token)


def wallet_pay_channels(access_token: str) -> dict:
    return _call("GET", "/api/wallet/pay-channels", access_token=access_token)


def wallet_recharge(access_token: str, amount, channel: str = "") -> dict:
    body: dict = {"amount": amount, "product": "or"}
    if channel:
        body["channel"] = channel
    return _call("POST", "/api/wallet/recharge", body, access_token=access_token)


def wallet_recharge_detail(access_token: str, order_id: str) -> dict:
    return _call("GET", f"/api/wallet/recharge/{order_id}", access_token=access_token)


def wallet_recharge_orders(
    access_token: str,
    page: int = 1,
    page_size: int = 20,
    status: str = "",
    product: str = "",
) -> dict:
    return _call(
        "GET",
        "/api/wallet/recharge/orders",
        access_token=access_token,
        query={
            "page": page,
            "page_size": page_size,
            "status": status,
            "product": product,
        },
    )


def wallet_dev_pay(access_token: str, order_id: str) -> dict:
    return _call(
        "POST",
        f"/api/wallet/recharge/{order_id}/dev-pay",
        {},
        access_token=access_token,
    )


def wallet_transactions(
    access_token: str,
    page: int = 1,
    page_size: int = 20,
    product: str = "",
) -> dict:
    return _call(
        "GET",
        "/api/wallet/transactions",
        access_token=access_token,
        query={"page": page, "page_size": page_size, "product": product},
    )


def wallet_bills(access_token: str) -> dict:
    return _call("GET", "/api/wallet/bills", access_token=access_token)


def s2s_balance(*, phone: str = "", user_id: str = "") -> dict:
    return _call(
        "GET",
        "/api/s2s/wallet/balance",
        query={"phone": phone, "user_id": user_id},
        s2s=True,
    )


def s2s_deduct(
    *,
    phone: str = "",
    user_id: str = "",
    amount,
    ref_id: str = "",
    remark: str = "",
    product: str = "or",
    biz_type: str = "consume_session",
) -> dict:
    return _call(
        "POST",
        "/api/s2s/wallet/deduct",
        {
            "phone": phone,
            "user_id": user_id,
            "amount": float(amount),
            "product": product,
            "biz_type": biz_type,
            "ref_id": ref_id,
            "remark": remark,
        },
        s2s=True,
    )


def upload_media(
    access_token: str,
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str = "",
    product: str = "or",
    prefix: str = "file",
) -> dict:
    """上传文件到 hipp-manager 公共媒体；返回 {path,url,name,size,mime}。"""
    import httpx

    if not enabled():
        raise ManagerError("未配置 HIPP_MANAGER_BASE", status=503)
    token = (access_token or "").strip()
    if not token:
        raise ManagerError("请重新登录以同步账户", status=401)
    url = _base() + "/api/media/upload"
    files = {
        "file": (
            filename or "file.bin",
            file_bytes,
            (content_type or "application/octet-stream").strip() or "application/octet-stream",
        )
    }
    data = {"product": product, "prefix": prefix}
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, data=data, files=files, headers=headers)
    except httpx.HTTPError as e:
        raise ManagerError("hipp-manager 不可达", status=502) from e
    raw = resp.text or ""
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError as e:
        raise ManagerError("hipp-manager 返回无法识别", status=502) from e
    if resp.status_code >= 400:
        detail = ""
        if isinstance(payload, dict):
            detail = str(payload.get("detail") or payload.get("message") or "")
        raise ManagerError(detail or "媒体上传失败", status=resp.status_code)
    return payload if isinstance(payload, dict) else {}


def delete_media(access_token: str, *, url: str = "", path: str = "") -> dict:
    """用户删除本人媒体。"""
    import httpx

    if not enabled():
        raise ManagerError("未配置 HIPP_MANAGER_BASE", status=503)
    token = (access_token or "").strip()
    if not token:
        raise ManagerError("请重新登录以同步账户", status=401)
    body: dict = {}
    if path:
        body["path"] = path
    if url:
        body["url"] = url
    if not body:
        raise ManagerError("缺少 url 或 path", status=400)
    endpoint = _base() + "/api/media"
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.request("DELETE", endpoint, json=body, headers=headers)
    except httpx.HTTPError as e:
        raise ManagerError("hipp-manager 不可达", status=502) from e
    raw = resp.text or ""
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError as e:
        raise ManagerError("hipp-manager 返回无法识别", status=502) from e
    if resp.status_code >= 400:
        detail = ""
        if isinstance(payload, dict):
            detail = str(payload.get("detail") or payload.get("message") or "")
        raise ManagerError(detail or "媒体删除失败", status=resp.status_code)
    return payload if isinstance(payload, dict) else {}


def s2s_delete_media(*, product: str = "or", urls: list | None = None, paths: list | None = None) -> dict:
    """S2S 批量删除媒体。"""
    if not s2s_enabled():
        raise ManagerError("未配置 HIPP_MANAGER_KEY", status=503)
    body = {
        "product": product,
        "urls": list(urls or []),
        "paths": list(paths or []),
    }
    if not body["urls"] and not body["paths"]:
        return {"ok": True, "deleted": 0, "skipped": 0}
    return _call("POST", "/api/s2s/media/delete", body, s2s=True)


def s2s_media_gc(
    *,
    product: str = "or",
    prefix: str = "chat",
    keep_urls: list | None = None,
    min_age_hours: int = 24,
) -> dict:
    """S2S 孤儿扫盘：删掉不在 keep 且超过宽限期的文件。"""
    if not s2s_enabled():
        raise ManagerError("未配置 HIPP_MANAGER_KEY", status=503)
    return _call(
        "POST",
        "/api/s2s/media/gc",
        {
            "product": product,
            "prefix": prefix,
            "keep_urls": list(keep_urls or []),
            "min_age_hours": int(min_age_hours),
        },
        s2s=True,
    )
