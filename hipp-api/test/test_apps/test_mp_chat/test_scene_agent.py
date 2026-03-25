# -*- coding: utf-8 -*-
import types

import pytest

from apps.mp_chat.crud import ChatSessionDal, SCENE_AGENT_UNAVAILABLE_CODE
from core.exception import CustomException


class _FakeExecuteResult:
    def __init__(self, *, agents=None, open_session=None):
        self._agents = agents
        self._open_session = open_session

    def scalars(self):
        return types.SimpleNamespace(all=lambda: list(self._agents or []))

    def scalar_one_or_none(self):
        return self._open_session


class _FakeDb:
    def __init__(self, *, agents=None, open_session=None):
        self._agents = agents or []
        self._open_session = open_session
        self._calls = 0

    async def execute(self, _sql):
        # 第一次 execute：查询候选 agents；第二次：查询 open session
        self._calls += 1
        if self._calls == 1:
            return _FakeExecuteResult(agents=self._agents)
        return _FakeExecuteResult(open_session=self._open_session)


class _Ag:
    def __init__(self, *, id, service_type):
        self.id = id
        self.service_type = service_type
        self.name = f"ag-{id}"
        self.description = None
        self.icon_type = None
        self.icon = None
        self.icon_background = None
        self.icon_url = None


class _Sess:
    def __init__(self, *, id, user_id, agent_id):
        self.id = id
        self.user_id = user_id
        self.agent_id = agent_id
        self.session_kind = "dify"
        self.title = "t"
        self.display_title = "t"
        self.agent_name_snapshot = None
        self.agent_avatar_snapshot = None
        self.agent_status = "active"
        self.last_message_preview = None
        self.is_pinned = False
        self.is_topic_closed = False
        self.update_datetime = None
        self.assigned_human_user_id = None
        self.assigned_human_name = None
        self.source_archive_session_id = None


@pytest.mark.asyncio
async def test_resolve_scene_agent_requirement_picks_from_candidates(monkeypatch):
    agents = [_Ag(id=1, service_type="需求分析"), _Ag(id=2, service_type="需求分析")]
    db = _FakeDb(agents=agents, open_session=None)
    dal = ChatSessionDal(db)

    monkeypatch.setattr("apps.mp_chat.crud.random.choice", lambda xs: xs[0])

    out = await dal.resolve_scene_agent(user_id=10, scene="requirement")
    assert out.service_type == "需求分析"
    assert out.agent.id == 1
    assert out.session is None


@pytest.mark.asyncio
async def test_resolve_scene_agent_returns_open_session(monkeypatch):
    agents = [_Ag(id=9, service_type="商业评估")]
    open_sess = _Sess(id=100, user_id=10, agent_id=9)
    db = _FakeDb(agents=agents, open_session=open_sess)
    dal = ChatSessionDal(db)

    monkeypatch.setattr("apps.mp_chat.crud.random.choice", lambda xs: xs[0])

    out = await dal.resolve_scene_agent(user_id=10, scene="business")
    assert out.service_type == "商业评估"
    assert out.agent.id == 9
    assert out.session is not None
    assert out.session.id == 100


@pytest.mark.asyncio
async def test_resolve_scene_agent_no_candidates_raises():
    db = _FakeDb(agents=[], open_session=None)
    dal = ChatSessionDal(db)
    with pytest.raises(CustomException) as e:
        await dal.resolve_scene_agent(user_id=10, scene="requirement")
    assert e.value.code == SCENE_AGENT_UNAVAILABLE_CODE


@pytest.mark.asyncio
async def test_resolve_scene_agent_invalid_scene_raises():
    db = _FakeDb(agents=[], open_session=None)
    dal = ChatSessionDal(db)
    with pytest.raises(CustomException) as e:
        await dal.resolve_scene_agent(user_id=10, scene="other")
    assert e.value.code == 422

