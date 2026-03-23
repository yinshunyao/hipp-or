# -*- coding: utf-8 -*-
from apps.mp_chat.dify_client import strip_finish_status_prefix


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
