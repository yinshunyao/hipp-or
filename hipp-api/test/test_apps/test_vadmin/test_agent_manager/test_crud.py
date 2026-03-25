# -*- coding: utf-8 -*-
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import httpx

from apps.vadmin.agent_manager.crud import AgentDal
from core.exception import CustomException


MOCK_INFO_RESPONSE = {
    "name": "测试客服",
    "description": "这是一个测试智能客服",
    "tags": ["客服", "AI"],
    "mode": "advanced-chat",
    "author_name": "Dify"
}

MOCK_SITE_RESPONSE = {
    "title": "测试客服",
    "chat_color_theme": "#ff4a4a",
    "chat_color_theme_inverted": False,
    "icon_type": "emoji",
    "icon": "😄",
    "icon_background": "#FFEAD5",
    "icon_url": None,
    "description": "这是一个测试智能客服",
    "copyright": "",
    "privacy_policy": "",
    "custom_disclaimer": "",
    "default_language": "zh-Hans",
    "show_workflow_steps": False,
    "use_icon_as_answer_icon": False
}

@pytest.mark.asyncio
async def test_test_connection_icon_url_wins_over_icon():
    mock_db = AsyncMock()
    dal = AgentDal(mock_db)
    agent_obj = _make_agent_obj()

    dal.get_data = AsyncMock(return_value=agent_obj)
    dal.flush = AsyncMock(return_value=agent_obj)

    info_resp = MagicMock()
    info_resp.json.return_value = MOCK_INFO_RESPONSE
    info_resp.raise_for_status = MagicMock()

    site_resp = MagicMock()
    site_data = dict(MOCK_SITE_RESPONSE)
    site_data["icon_url"] = "http://cdn.example.com/a.png"
    site_data["icon_type"] = "emoji"
    site_data["icon"] = "😄"
    site_data["icon_background"] = "#FFEAD5"
    site_resp.json.return_value = site_data
    site_resp.raise_for_status = MagicMock()

    async def mock_get(url, **kwargs):
        u = str(url)
        if "/v1/info" in u:
            return info_resp
        if "/v1/site" in u:
            return site_resp
        raise ValueError(f"Unexpected URL: {url}")

    with patch("apps.vadmin.agent_manager.crud.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get = mock_get
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        dal.schema = MagicMock()
        dal.schema.model_validate.return_value = MagicMock(
            model_dump=MagicMock(
                return_value={"id": 1, "icon_url": "http://cdn.example.com/a.png", "is_tested": True}
            )
        )

        await dal.test_connection(
            api_server="http://localhost/v1",
            app_key="test-key-123",
            remark="测试备注",
            data_id=1,
            service_type="需求分析",
        )

    assert agent_obj.icon_type == "image"
    assert agent_obj.icon_url == "http://cdn.example.com/a.png"
    assert agent_obj.icon is None
    assert agent_obj.icon_background is None


def _make_agent_obj(**overrides):
    defaults = dict(
        id=1,
        api_server="http://localhost/v1",
        app_key="test-key-123",
        service_type=None,
        remark="测试备注",
        name=None,
        description=None,
        tags=None,
        mode=None,
        icon_type=None,
        icon=None,
        icon_background=None,
        icon_url=None,
        webapp_config=None,
        status="draft",
        is_tested=False,
        create_user_id=1,
    )
    defaults.update(overrides)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


@pytest.mark.asyncio
async def test_test_connection_success():
    mock_db = AsyncMock()
    dal = AgentDal(mock_db)
    agent_obj = _make_agent_obj()

    dal.get_data = AsyncMock(return_value=agent_obj)
    dal.flush = AsyncMock(return_value=agent_obj)

    info_resp = MagicMock()
    info_resp.json.return_value = MOCK_INFO_RESPONSE
    info_resp.raise_for_status = MagicMock()

    site_resp = MagicMock()
    site_resp.json.return_value = MOCK_SITE_RESPONSE
    site_resp.raise_for_status = MagicMock()

    async def mock_get(url, **kwargs):
        u = str(url)
        if "/v1/info" in u:
            return info_resp
        if "/v1/site" in u:
            return site_resp
        raise ValueError(f"Unexpected URL: {url}")

    with patch("apps.vadmin.agent_manager.crud.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get = mock_get
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        dal.schema = MagicMock()
        dal.schema.model_validate.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": 1, "name": "测试客服", "is_tested": True})
        )

        result = await dal.test_connection(
            api_server="http://localhost/v1",
            app_key="test-key-123",
            remark="测试备注",
            data_id=1,
            service_type="需求分析",
        )

    assert agent_obj.name == "测试客服"
    assert agent_obj.description == "这是一个测试智能客服"
    assert agent_obj.tags == json.dumps(["客服", "AI"], ensure_ascii=False)
    assert agent_obj.mode == "advanced-chat"
    assert agent_obj.icon == "😄"
    assert agent_obj.icon_background == "#FFEAD5"
    assert agent_obj.is_tested is True
    assert agent_obj.service_type == "需求分析"


@pytest.mark.asyncio
async def test_test_connection_http_error():
    mock_db = AsyncMock()
    dal = AgentDal(mock_db)
    agent_obj = _make_agent_obj()

    dal.get_data = AsyncMock(return_value=agent_obj)

    with patch("apps.vadmin.agent_manager.crud.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()

        resp = MagicMock()
        resp.status_code = 401
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=resp
        )
        client_instance.get = AsyncMock(return_value=resp)
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        with pytest.raises(CustomException, match="Dify API 返回错误"):
            await dal.test_connection(
                api_server="http://localhost/v1",
                app_key="test-key-123",
                remark=None,
                data_id=1,
                service_type=None,
            )


@pytest.mark.asyncio
async def test_test_connection_network_error():
    mock_db = AsyncMock()
    dal = AgentDal(mock_db)
    agent_obj = _make_agent_obj()

    dal.get_data = AsyncMock(return_value=agent_obj)

    with patch("apps.vadmin.agent_manager.crud.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get = AsyncMock(
            side_effect=httpx.RequestError("Connection refused", request=MagicMock())
        )
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        with pytest.raises(CustomException, match="无法连接 Dify 服务器"):
            await dal.test_connection(
                api_server="http://localhost/v1",
                app_key="test-key-123",
                remark=None,
                data_id=1,
                service_type=None,
            )


@pytest.mark.asyncio
async def test_test_connection_no_id_echoes_service_type():
    mock_db = AsyncMock()
    dal = AgentDal(mock_db)

    info_resp = MagicMock()
    info_resp.json.return_value = MOCK_INFO_RESPONSE
    info_resp.raise_for_status = MagicMock()

    site_resp = MagicMock()
    site_resp.json.return_value = MOCK_SITE_RESPONSE
    site_resp.raise_for_status = MagicMock()

    async def mock_get(url, **kwargs):
        if "/v1/info" in str(url):
            return info_resp
        if "/v1/site" in str(url):
            return site_resp
        raise ValueError(f"Unexpected URL: {url}")

    with patch("apps.vadmin.agent_manager.crud.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get = mock_get
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        result = await dal.test_connection(
            api_server="http://localhost/v1",
            app_key="test-key-123",
            remark=None,
            data_id=None,
            service_type="  商业评估  ",
        )

    assert result["id"] is None
    assert result["service_type"] == "商业评估"
    assert result["is_tested"] is True


@pytest.mark.asyncio
async def test_publish_success():
    mock_db = AsyncMock()
    dal = AgentDal(mock_db)
    agent_obj = _make_agent_obj(is_tested=True)

    dal.get_data = AsyncMock(return_value=agent_obj)
    dal.flush = AsyncMock(return_value=agent_obj)
    dal.schema = MagicMock()
    dal.schema.model_validate.return_value = MagicMock(
        model_dump=MagicMock(return_value={"id": 1, "status": "published"})
    )

    result = await dal.publish(1)
    assert agent_obj.status == "published"


@pytest.mark.asyncio
async def test_publish_not_tested():
    mock_db = AsyncMock()
    dal = AgentDal(mock_db)
    agent_obj = _make_agent_obj(is_tested=False)

    dal.get_data = AsyncMock(return_value=agent_obj)

    with pytest.raises(CustomException, match="请先通过连通性测试"):
        await dal.publish(1)


@pytest.mark.asyncio
async def test_unpublish():
    mock_db = AsyncMock()
    dal = AgentDal(mock_db)
    agent_obj = _make_agent_obj(status="published")

    dal.get_data = AsyncMock(return_value=agent_obj)
    dal.flush = AsyncMock(return_value=agent_obj)
    dal.schema = MagicMock()
    dal.schema.model_validate.return_value = MagicMock(
        model_dump=MagicMock(return_value={"id": 1, "status": "draft"})
    )

    result = await dal.unpublish(1)
    assert agent_obj.status == "draft"
