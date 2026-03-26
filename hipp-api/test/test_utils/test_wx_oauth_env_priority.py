# -*- coding: utf-8 -*-
import pytest

from utils.wx.oauth import WXOAuth


@pytest.mark.asyncio
async def test_get_settings_prefers_env(monkeypatch):
    class DummyCache:
        def __init__(self, rd):
            pass

        async def get_tab_name(self, tab_name, retry):
            raise AssertionError("should not read settings tab when env is configured")

    monkeypatch.setattr("utils.wx.oauth.Cache", DummyCache)
    monkeypatch.setattr("utils.wx.oauth.settings.WECHAT_APPID", "wx-env-appid")
    monkeypatch.setattr("utils.wx.oauth.settings.WECHAT_KEY", "wx-env-key")

    oauth = WXOAuth(rd=None, index=0)
    await oauth._WXOAuth__get_settings()

    assert oauth.appid == "wx-env-appid"
    assert oauth.secret == "wx-env-key"
