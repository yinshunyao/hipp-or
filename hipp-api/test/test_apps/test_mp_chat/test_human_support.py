# -*- coding: utf-8 -*-
from apps.mp_chat.archive_context import format_archive_topic_context


def test_format_archive_topic_context_includes_title_and_roles():
    text = format_archive_topic_context(
        source_session_id=42,
        display_title="测试话题",
        messages=[("user", "你好"), ("assistant", "您好")],
    )
    assert "【归档话题】测试话题" in text
    assert "来源会话 ID：42" in text
    assert "用户：你好" in text
    assert "智能体：您好" in text


def test_format_archive_topic_context_needle_for_session_dedup():
    """与 crud.create_or_get_human_support_session 中按「来源会话 ID：{id}」去重一致。"""
    text = format_archive_topic_context(
        source_session_id=100,
        display_title="T",
        messages=[("user", "x")],
    )
    assert "来源会话 ID：100" in text
