# -*- coding: utf-8 -*-
"""对话 Tab 收件箱：归档会话排序（置顶分区在前，分区内最近活跃优先）。"""
from datetime import datetime
from types import SimpleNamespace

from apps.mp_chat.inbox_order import (
    order_archived_inbox_pairs,
    recency_key_desc,
    sort_session_pairs_by_recency_desc,
)


def test_recency_key_prefers_update_datetime():
    t = datetime(2024, 6, 1)
    s = SimpleNamespace(id=5, update_datetime=t, create_datetime=datetime(2020, 1, 1))
    assert recency_key_desc(s)[0] == t


def test_sort_session_pairs_newer_first():
    t_old = datetime(2024, 1, 1)
    t_new = datetime(2024, 1, 10)
    a = SimpleNamespace(id=1, update_datetime=t_old, create_datetime=t_old)
    b = SimpleNamespace(id=2, update_datetime=t_new, create_datetime=t_new)
    out = sort_session_pairs_by_recency_desc([(a, None), (b, None)])
    assert [x[0].id for x in out] == [2, 1]


def test_sort_session_pairs_tiebreaker_by_id_desc():
    t = datetime(2024, 1, 1)
    a = SimpleNamespace(id=1, update_datetime=t, create_datetime=t)
    b = SimpleNamespace(id=2, update_datetime=t, create_datetime=t)
    out = sort_session_pairs_by_recency_desc([(a, None), (b, None)])
    assert [x[0].id for x in out] == [2, 1]


def _sess(sid, *, pinned=False, when=None):
    t = when or datetime(2024, 1, 1)
    return SimpleNamespace(
        id=sid,
        is_pinned=pinned,
        update_datetime=t,
        create_datetime=t,
    )


def test_order_archived_inbox_pairs_pinned_before_unpinned():
    older = datetime(2024, 1, 1)
    newer = datetime(2024, 1, 20)
    u_new = _sess(1, pinned=False, when=newer)
    u_old = _sess(2, pinned=False, when=older)
    p_old = _sess(3, pinned=True, when=older)
    out = order_archived_inbox_pairs([(u_new, None), (u_old, None), (p_old, None)])
    assert [x[0].id for x in out] == [3, 1, 2]


def test_order_archived_inbox_pairs_recency_within_pin_group():
    t1 = datetime(2024, 1, 5)
    t2 = datetime(2024, 1, 10)
    a = _sess(1, pinned=True, when=t1)
    b = _sess(2, pinned=True, when=t2)
    out = order_archived_inbox_pairs([(a, None), (b, None)])
    assert [x[0].id for x in out] == [2, 1]
