"""业务鉴权时向 hipp-manager 校验「用户是否在线」；服务端缓存 manager_token。"""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any

from redis.asyncio import Redis

from core.exception import CustomException
from utils import hipp_manager
from utils import status as http_status

_MGR_TOK_KEY = "or:mgr_tok:{user_id}"
# manager 会话默认 12h；缓存略短，刷新登录会重写
_MGR_TOK_TTL = 12 * 3600
_ME_OK_TTL = 30.0
_ME_FAIL_TTL = 5.0
_me_lock = threading.Lock()
_me_cache: dict[str, tuple[float, bool]] = {}


def _tok_key(user_id: int | str) -> str:
    return _MGR_TOK_KEY.format(user_id=user_id)


async def store_manager_token(rd: Redis | None, user_id: int | str, token: str) -> None:
    access = (token or "").strip()
    if not rd or not access or not user_id:
        return
    await rd.setex(_tok_key(user_id), _MGR_TOK_TTL, access)


async def get_manager_token(rd: Redis | None, user_id: int | str) -> str:
    if not rd or not user_id:
        return ""
    raw = await rd.get(_tok_key(user_id))
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace").strip()
    return str(raw).strip()


async def clear_manager_token(rd: Redis | None, user_id: int | str) -> None:
    if not rd or not user_id:
        return
    tok = await get_manager_token(rd, user_id)
    if tok:
        invalidate_me_cache(tok)
    await rd.delete(_tok_key(user_id))


def invalidate_me_cache(access_token: str = "") -> None:
    token = (access_token or "").strip()
    if not token:
        return
    key = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _me_lock:
        _me_cache.pop(key, None)


def ensure_manager_online(access_token: str) -> dict[str, Any]:
    """同步调用 manager /me；短缓存。失败抛 CustomException 401。"""
    token = (access_token or "").strip()
    if not token:
        raise CustomException(
            msg="请重新登录以同步账户",
            code=http_status.HTTP_401_UNAUTHORIZED,
            status_code=http_status.HTTP_401_UNAUTHORIZED,
        )
    key = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = time.monotonic()
    with _me_lock:
        hit = _me_cache.get(key)
        if hit and hit[0] > now:
            if hit[1]:
                return {}
            raise CustomException(
                msg="请重新登录",
                code=http_status.HTTP_401_UNAUTHORIZED,
                status_code=http_status.HTTP_401_UNAUTHORIZED,
            )
    try:
        profile = hipp_manager.me(token)
    except hipp_manager.ManagerError:
        # 管理端可能缓存的是平台管理员 ops 令牌
        try:
            profile = hipp_manager.ops_me(token)
        except hipp_manager.ManagerError as exc:
            with _me_lock:
                _me_cache[key] = (now + _ME_FAIL_TTL, False)
            raise CustomException(
                msg=str(exc) or "请重新登录",
                code=http_status.HTTP_401_UNAUTHORIZED,
                status_code=http_status.HTTP_401_UNAUTHORIZED,
            ) from exc
    with _me_lock:
        _me_cache[key] = (now + _ME_OK_TTL, True)
    return profile if isinstance(profile, dict) else {}


def should_skip_manager_check(user: Any) -> bool:
    """微信游客、电商次卡临时用户与未绑定 manager 的微信会话不二次校验。"""
    ut = str(getattr(user, "user_type", None) or "").strip()
    if ut in ("mp_guest", "entitlement"):
        return True
    return False


async def enforce_manager_online(rd: Redis | None, user: Any) -> None:
    """本地用户通过后：有 HIPP_MANAGER_BASE 则校验缓存的 manager 令牌。"""
    if not hipp_manager.enabled():
        return
    if should_skip_manager_check(user):
        return
    uid = getattr(user, "id", None)
    tok = await get_manager_token(rd, uid)
    if not tok:
        # 纯微信会话（从未拿到 manager 令牌）放行；其余须重登
        ut = str(getattr(user, "user_type", None) or "").strip()
        if ut == "wechat":
            return
        raise CustomException(
            msg="请重新登录以同步账户",
            code=http_status.HTTP_401_UNAUTHORIZED,
            status_code=http_status.HTTP_401_UNAUTHORIZED,
        )
    try:
        ensure_manager_online(tok)
    except CustomException:
        await clear_manager_token(rd, uid)
        raise
