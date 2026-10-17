# -*- coding: utf-8 -*-
"""话题结束后清理未出现在助手正文中的附件媒体（最佳努力）。"""

from __future__ import annotations

import logging
import re
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.mp_chat.attachments import loads_attachments
from apps.mp_chat import models
from utils import hipp_manager

logger = logging.getLogger(__name__)

# 助手正文中的平台媒体绝对/相对 URL
_MEDIA_URL_RE = re.compile(
    r"(?:https?://[^\s\"'<>\)]+)?/media/[^\s\"'<>\)]+",
    re.IGNORECASE,
)


def extract_media_urls_from_text(text: str | None) -> set[str]:
    found: set[str] = set()
    for m in _MEDIA_URL_RE.finditer(text or ""):
        raw = m.group(0).rstrip(".,;:)")
        if raw:
            found.add(raw)
    return found


def _normalize_keep_key(url: str) -> str:
    """用 /media/ 后缀作为比对键，兼容 http/https 基址差异。"""
    u = (url or "").strip()
    idx = u.find("/media/")
    if idx >= 0:
        return u[idx:].split("?", 1)[0]
    return u


async def collect_session_attachment_urls(db: AsyncSession, session_id: int) -> set[str]:
    result = await db.execute(
        select(models.VadminChatMessage.attachments).where(
            models.VadminChatMessage.session_id == session_id,
            models.VadminChatMessage.attachments.is_not(None),
        )
    )
    urls: set[str] = set()
    for (raw,) in result.all():
        for item in loads_attachments(raw) or []:
            u = str(item.get("url") or "").strip()
            if u.startswith(("http://", "https://")) and "/media/" in u:
                urls.add(u)
    return urls


async def collect_assistant_referenced_media(db: AsyncSession, session_id: int) -> set[str]:
    result = await db.execute(
        select(models.VadminChatMessage.content).where(
            models.VadminChatMessage.session_id == session_id,
            models.VadminChatMessage.role == "assistant",
        )
    )
    keep: set[str] = set()
    for (content,) in result.all():
        keep |= extract_media_urls_from_text(content)
    return keep


def urls_to_delete(attachment_urls: Iterable[str], keep_urls: Iterable[str]) -> list[str]:
    keep_keys = {_normalize_keep_key(u) for u in keep_urls}
    out: list[str] = []
    seen: set[str] = set()
    for u in attachment_urls:
        key = _normalize_keep_key(u)
        if key in keep_keys:
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


async def cleanup_session_media_after_topic_close(db: AsyncSession, session_id: int) -> None:
    """结题后媒体清理（保留会话历史）。

    已发送并写入消息 ``attachments`` 的 URL **一律保留**，供历史/分享页展示。
    待发取消仍走 ``DELETE /mp/chat/upload``；真正无引用落盘靠全站孤儿 GC。
    本函数保留调用点，避免结题路径再误删用户附图。
    """
    if not hipp_manager.s2s_enabled():
        logger.info("skip media cleanup: s2s not enabled session=%s", session_id)
        return
    try:
        attachment_urls = await collect_session_attachment_urls(db, session_id)
        # 历史气泡/分享依赖 attachments；不得因「未出现在助手正文」删盘
        keep = set(attachment_urls) | await collect_assistant_referenced_media(db, session_id)
        doomed = urls_to_delete(attachment_urls, keep)
        if doomed:
            # 理论上为空；若有则仍删（防御）
            hipp_manager.s2s_delete_media(product="or", urls=doomed)
        logger.info(
            "media cleanup session=%s keep_attachments=%s keep_asst=%s deleted=%s",
            session_id,
            len(attachment_urls),
            len(keep) - len(attachment_urls),
            len(doomed),
        )
    except Exception:
        logger.exception("media cleanup failed session=%s", session_id)


def schedule_topic_media_cleanup(session_id: int) -> None:
    """在独立短事务中执行清理，不阻塞结题响应。"""
    import asyncio

    async def _run() -> None:
        from core.database import session_factory

        try:
            async with session_factory() as db:
                async with db.begin():
                    await cleanup_session_media_after_topic_close(db, session_id)
        except Exception:
            logger.exception("schedule media cleanup failed session=%s", session_id)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_run())
    except RuntimeError:
        # 无事件循环时同步跑（少见）
        asyncio.run(_run())


async def collect_all_keep_media_urls(db: AsyncSession) -> list[str]:
    """全库 attachments + 助手正文中的 /media/ URL（孤儿 GC 保留集）。"""
    keep: set[str] = set()
    att_rows = await db.execute(
        select(models.VadminChatMessage.attachments).where(
            models.VadminChatMessage.attachments.is_not(None),
        )
    )
    for (raw,) in att_rows.all():
        for item in loads_attachments(raw) or []:
            u = str(item.get("url") or "").strip()
            if u.startswith(("http://", "https://")) and "/media/" in u:
                keep.add(u)
    asst_rows = await db.execute(
        select(models.VadminChatMessage.content).where(
            models.VadminChatMessage.role == "assistant",
            models.VadminChatMessage.content.is_not(None),
        )
    )
    for (content,) in asst_rows.all():
        keep |= extract_media_urls_from_text(content)
    return sorted(keep)


async def run_orphan_media_gc(*, min_age_hours: int = 24) -> dict:
    """收集保留 URL 并调 manager S2S gc。"""
    from core.database import session_factory

    if not hipp_manager.s2s_enabled():
        logger.info("skip orphan media gc: s2s not enabled")
        return {"ok": False, "reason": "s2s_disabled"}
    async with session_factory() as db:
        async with db.begin():
            keep_urls = await collect_all_keep_media_urls(db)
    result = hipp_manager.s2s_media_gc(
        product="or",
        prefix="chat",
        keep_urls=keep_urls,
        min_age_hours=min_age_hours,
    )
    logger.info(
        "orphan media gc keep=%s result=%s",
        len(keep_urls),
        result,
    )
    return result if isinstance(result, dict) else {"ok": True, "raw": result}
