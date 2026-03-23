# -*- coding: utf-8 -*-
import asyncio

import pytest

from apps.mp_chat.dify_client import (
    DifyStreamAccumulator,
    StreamAnswerPrefixFilter,
    _chat_messages_url,
    rewrite_sse_answer_line,
    send_chat_message_blocking,
)


class _FakeResp:
    def __init__(self, payload: dict, status: int = 200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("err", request=None, response=None)

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response: _FakeResp):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, headers=None, json=None):
        assert "/v1/chat-messages" in url
        assert json["query"] == "hello"
        assert json["response_mode"] == "blocking"
        return self._response


def test_send_chat_message_blocking_success(monkeypatch):
    fake = _FakeClient(_FakeResp({"answer": "ok", "conversation_id": "c1"}))
    import apps.mp_chat.dify_client as mod

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda **kwargs: fake)

    async def _run():
        return await send_chat_message_blocking(
            "http://example.com/v1",
            "app-key",
            "hello",
            "user-1",
            None,
        )

    out = asyncio.run(_run())
    assert out["answer"] == "ok"
    assert out["conversation_id"] == "c1"


def test_send_chat_message_blocking_http_error(monkeypatch):
    import httpx

    class BadClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers=None, json=None):
            req = httpx.Request("POST", url)
            return httpx.Response(500, request=req, json={"message": "bad"})

    import apps.mp_chat.dify_client as mod

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda **kwargs: BadClient())
    from core.exception import CustomException

    async def _run():
        await send_chat_message_blocking("http://a/v1", "k", "q", "u", None)

    with pytest.raises(CustomException):
        asyncio.run(_run())


def test_dify_stream_accumulator_message_deltas():
    acc = DifyStreamAccumulator()
    acc.feed_line('data: {"event":"message","answer":"你"}')
    acc.feed_line('data: {"event":"message","answer":"好"}')
    assert acc.full_answer == "你好"
    assert acc.error is None


def test_dify_stream_accumulator_error_event():
    acc = DifyStreamAccumulator()
    acc.feed_line('data: {"event":"error","message":"bad"}')
    assert acc.error == "bad"


def test_rewrite_sse_answer_line_filters_finish_prefix():
    f = StreamAnswerPrefixFilter()
    # first chunk only contains prefix head, keep buffering
    assert rewrite_sse_answer_line('data: {"event":"message","answer":"结束状态 T"}', f) is None
    # second chunk closes status line and starts body, should emit only body
    line = rewrite_sse_answer_line('data: {"event":"message","answer":"rue\\n你好"}', f)
    assert line == 'data: {"event": "message", "answer": "你好"}'


def test_rewrite_sse_answer_line_keeps_normal_content():
    f = StreamAnswerPrefixFilter()
    line = rewrite_sse_answer_line('data: {"event":"message","answer":"正常内容"}', f)
    assert line == 'data: {"event": "message", "answer": "正常内容"}'


def test_chat_messages_url_with_and_without_v1():
    assert _chat_messages_url("https://dify.example.com") == "https://dify.example.com/v1/chat-messages"
    assert _chat_messages_url("https://dify.example.com/v1") == "https://dify.example.com/v1/chat-messages"
