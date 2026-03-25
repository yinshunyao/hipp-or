# -*- coding: utf-8 -*-
"""归档话题分页：服务端对单页查询结果先按新→旧取 limit 条，再 reverse 为旧→新输出（与 crud.list_archived_topics_for_agent 一致）。"""


def test_archived_page_reverses_desc_slice_to_ascending():
    rows_desc = [("newest", 30), ("mid", 20), ("oldest", 10)]
    cap = 3
    chunk = rows_desc[:cap]
    chunk.reverse()
    assert [x[1] for x in chunk] == [10, 20, 30]


def test_has_more_when_extra_row_fetched():
    rows_desc = [("a", 4), ("b", 3), ("c", 2)]
    cap = 2
    has_more = len(rows_desc) > cap
    page = rows_desc[:cap]
    page.reverse()
    assert has_more is True
    assert [x[1] for x in page] == [3, 4]
