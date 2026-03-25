# -*- coding: utf-8 -*-
"""收件箱列表分区排序（无 ORM 依赖，供 crud 与单测复用）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def recency_key_desc(sess: Any) -> tuple:
    """同一分区内：最近活跃优先；缺失时间则靠后；同时间以 id 大者优先。"""
    t = sess.update_datetime or sess.create_datetime
    return (t if t is not None else datetime.min, sess.id)


def sort_session_pairs_by_recency_desc(
    pairs: list[tuple[Any, Any]],
) -> list[tuple[Any, Any]]:
    return sorted(pairs, key=lambda p: recency_key_desc(p[0]), reverse=True)


def order_archived_inbox_pairs(pairs: list[tuple[Any, Any]]) -> list[tuple[Any, Any]]:
    """
    对话 Tab 收件箱：仅已归档会话。置顶分区整体在前（分区内最近活跃优先），其后非置顶分区（同样规则）。
    """
    pinned = [p for p in pairs if getattr(p[0], "is_pinned", False)]
    unpinned = [p for p in pairs if not getattr(p[0], "is_pinned", False)]
    return sort_session_pairs_by_recency_desc(pinned) + sort_session_pairs_by_recency_desc(unpinned)
