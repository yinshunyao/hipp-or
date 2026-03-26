# -*- coding: utf-8 -*-
from apps.vadmin.auth.schemas.user import compute_user_tags


class _U:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_compute_user_tags_wechat_only():
    u = _U(is_system_created=False, user_type="wechat", wx_nickname=None, wx_avatar=None)
    assert compute_user_tags(u) == ["微信用户"]


def test_compute_user_tags_system_only():
    u = _U(is_system_created=True, user_type="system", wx_nickname=None, wx_avatar=None)
    assert compute_user_tags(u) == ["系统创建"]


def test_compute_user_tags_merged_system_and_wechat():
    u = _U(is_system_created=True, user_type="wechat", wx_nickname="n", wx_avatar=None)
    assert compute_user_tags(u) == ["系统创建", "微信用户"]


def test_compute_user_tags_wechat_by_profile_without_type():
    u = _U(is_system_created=False, user_type="system", wx_nickname="x", wx_avatar=None)
    assert compute_user_tags(u) == ["微信用户"]
