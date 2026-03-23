#!/usr/bin/python
# -*- coding: utf-8 -*-
# @desc           : 智能客服管理 - 增删改查

import json
import httpx
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from application import settings
from core.crud import DalBase
from core.exception import CustomException
from . import models, schemas


def _dify_api_base(api_server: str) -> str:
    """
    用户填写 Dify「API 服务器」基准地址，须包含 /v1，例如 http://192.168.1.123/v1。
    实际请求路径为 {base}/info、{base}/site（勿再拼一层 /v1）。
    """
    s = (api_server or "").strip().rstrip("/")
    if not s:
        raise CustomException("API 服务器地址为空")
    if not s.startswith(("http://", "https://")):
        s = "http://" + s
    return s


def _request_error_detail(exc: httpx.RequestError) -> str:
    parts = [str(exc).strip(), repr(exc)]
    req = getattr(exc, "request", None)
    if req is not None:
        parts.append(f"request_url={req.url!s}")
    return " | ".join(p for p in parts if p)


class AgentDal(DalBase):

    def __init__(self, db: AsyncSession):
        super(AgentDal, self).__init__()
        self.db = db
        self.model = models.VadminAgent
        self.schema = schemas.AgentSimpleOut

    def add_filter_condition(self, sql, **kwargs):
        keyword = kwargs.pop("keyword", None)
        if keyword:
            sql = sql.where(
                or_(
                    self.model.name.like(f"%{keyword}%"),
                    self.model.description.like(f"%{keyword}%"),
                    self.model.tags.like(f"%{keyword}%"),
                )
            )
        return super().add_filter_condition(sql, **kwargs)

    async def _fetch_dify_and_apply(
        self,
        obj: models.VadminAgent,
        info_data: dict,
        site_data: dict,
    ) -> None:
        obj.name = info_data.get("name")
        obj.description = info_data.get("description")
        tags = info_data.get("tags")
        obj.tags = json.dumps(tags, ensure_ascii=False) if tags else None
        obj.mode = info_data.get("mode")

        obj.icon_type = site_data.get("icon_type")
        obj.icon = site_data.get("icon")
        obj.icon_background = site_data.get("icon_background")
        obj.icon_url = site_data.get("icon_url")
        obj.webapp_config = json.dumps(site_data, ensure_ascii=False)

        obj.is_tested = True

    async def _call_dify(self, api_server: str, app_key: str) -> tuple[dict, dict]:
        headers = {"Authorization": f"Bearer {app_key}"}
        timeout = httpx.Timeout(10.0)
        base = _dify_api_base(api_server)
        info_url = f"{base}/info"
        site_url = f"{base}/site"

        async with httpx.AsyncClient(
            timeout=timeout,
            verify=settings.DIFY_HTTPX_VERIFY,
            follow_redirects=True,
        ) as client:
            try:
                info_resp = await client.get(info_url, headers=headers)
                info_resp.raise_for_status()
                info_data = info_resp.json()

                site_resp = await client.get(site_url, headers=headers)
                site_resp.raise_for_status()
                site_data = site_resp.json()
            except httpx.HTTPStatusError as e:
                body = ""
                try:
                    body = (e.response.text or "")[:200]
                except Exception:
                    pass
                raise CustomException(
                    f"Dify API 返回错误: HTTP {e.response.status_code} url={e.request.url!s} {body}"
                )
            except httpx.RequestError as e:
                raise CustomException(
                    f"无法连接 Dify 服务器: {_request_error_detail(e)}"
                )
        return info_data, site_data

    async def test_connection(
        self,
        api_server: str,
        app_key: str,
        remark: str | None,
        data_id: int | None,
    ) -> dict:
        """
        使用请求体中的 api_server、app_key 调用 Dify；
        data_id 有值时先写入配置再同步并落库；无值时仅返回 Dify 同步结果（不落库）。
        """
        info_data, site_data = await self._call_dify(api_server, app_key)

        if data_id is not None:
            obj: models.VadminAgent = await self.get_data(data_id)
            obj.api_server = api_server
            obj.app_key = app_key
            obj.remark = remark
            await self._fetch_dify_and_apply(obj, info_data, site_data)
            await self.flush(obj)
            return self.schema.model_validate(obj).model_dump()

        tags = info_data.get("tags")
        tags_str = json.dumps(tags, ensure_ascii=False) if tags else None
        return {
            "id": None,
            "api_server": api_server,
            "app_key": app_key,
            "remark": remark,
            "name": info_data.get("name"),
            "description": info_data.get("description"),
            "tags": tags_str,
            "mode": info_data.get("mode"),
            "icon_type": site_data.get("icon_type"),
            "icon": site_data.get("icon"),
            "icon_background": site_data.get("icon_background"),
            "icon_url": site_data.get("icon_url"),
            "webapp_config": json.dumps(site_data, ensure_ascii=False),
            "status": "draft",
            "is_tested": True,
        }

    async def publish(self, data_id: int) -> dict:
        obj: models.VadminAgent = await self.get_data(data_id)
        if not obj.is_tested:
            raise CustomException("请先通过连通性测试后再上架")
        obj.status = "published"
        await self.flush(obj)
        return self.schema.model_validate(obj).model_dump()

    async def unpublish(self, data_id: int) -> dict:
        obj: models.VadminAgent = await self.get_data(data_id)
        obj.status = "draft"
        await self.flush(obj)
        return self.schema.model_validate(obj).model_dump()
