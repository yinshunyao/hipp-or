# -*- coding: utf-8 -*-
from apps.mp_chat.dify_client import parse_topic_finished_from_raw_answer, strip_finish_status_prefix
from apps.mp_chat.session_display import mp_ui_session_title


class _Sess:
    def __init__(self, title, agent_name_snapshot):
        self.title = title
        self.agent_name_snapshot = agent_name_snapshot


class _Ag:
    def __init__(self, name):
        self.name = name


def test_mp_ui_session_title_uses_live_agent_when_synced_with_snapshot():
    s = _Sess("OldName", "OldName")
    ag = _Ag("NewName")
    assert mp_ui_session_title(s, ag) == "NewName"


def test_mp_ui_session_title_keeps_custom_title():
    s = _Sess("MyTitle", "OldName")
    ag = _Ag("NewName")
    assert mp_ui_session_title(s, ag) == "MyTitle"


def test_mp_ui_session_title_deleted_agent_falls_back():
    s = _Sess("OnlyTitle", "Snap")
    assert mp_ui_session_title(s, None) == "OnlyTitle"


def test_strip_finish_status_prefix_true():
    text = "结束状态 True\n这是正文"
    assert strip_finish_status_prefix(text) == "这是正文"


def test_strip_finish_status_prefix_false():
    text = "结束状态 False\n第一行\n第二行"
    assert strip_finish_status_prefix(text) == "第一行\n第二行"


def test_strip_finish_status_prefix_keep_original():
    text = "普通回复"
    assert strip_finish_status_prefix(text) == "普通回复"


def test_strip_finish_status_prefix_colon_variants():
    assert strip_finish_status_prefix("结束状态: True\n内容") == "内容"
    assert strip_finish_status_prefix("结束状态：False\n内容") == "内容"


def test_parse_topic_finished_from_raw_answer():
    assert parse_topic_finished_from_raw_answer("结束状态 True\n正文") is True
    assert parse_topic_finished_from_raw_answer("结束状态: True\n正文") is True
    assert parse_topic_finished_from_raw_answer("结束状态：False\n正文") is False
    assert parse_topic_finished_from_raw_answer("正文") is False
    assert parse_topic_finished_from_raw_answer("") is False
