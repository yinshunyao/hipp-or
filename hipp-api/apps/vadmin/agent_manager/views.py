#!/usr/bin/python
# -*- coding: utf-8 -*-
# @desc           : 智能客服管理视图

from fastapi import APIRouter, Depends
from sqlalchemy.orm import joinedload
from core.dependencies import IdList
from utils.response import SuccessResponse, ErrorResponse
from . import schemas, crud, params, models
from apps.vadmin.auth.utils.current import FullAdminAuth
from apps.vadmin.auth.utils.validation.auth import Auth

app = APIRouter()


@app.get("/agents", summary="获取智能客服列表")
async def get_agents(p: params.AgentParams = Depends(), auth: Auth = Depends(FullAdminAuth())):
    model = models.VadminAgent
    options = [joinedload(model.create_user)]
    schema = schemas.AgentListOut
    datas, count = await crud.AgentDal(auth.db).get_datas(
        **p.dict(),
        v_options=options,
        v_schema=schema,
        v_return_count=True
    )
    return SuccessResponse(datas, count=count)


@app.post("/agents", summary="创建智能客服")
async def create_agent(data: schemas.Agent, auth: Auth = Depends(FullAdminAuth())):
    data.create_user_id = auth.user.id
    data.status = "draft"
    # 允许前端在「先测后存」场景传入 is_tested=True（未传则默认 False）
    if data.is_tested is None:
        data.is_tested = False
    return SuccessResponse(await crud.AgentDal(auth.db).create_data(data=data))


@app.put("/agents/{data_id}", summary="编辑智能客服")
async def put_agent(data_id: int, data: schemas.Agent, auth: Auth = Depends(FullAdminAuth())):
    """
    前端约定：请求体中字段为 null 表示不修改该字段（仅更新非 null 字段）。
    """
    patch = data.model_dump(exclude_unset=True, exclude_none=True)
    patch.pop("create_user_id", None)
    patch.pop("id", None)
    if not patch:
        return SuccessResponse(
            await crud.AgentDal(auth.db).get_data(data_id, v_schema=schemas.AgentSimpleOut)
        )
    return SuccessResponse(await crud.AgentDal(auth.db).put_data(data_id, patch))


@app.delete("/agents", summary="删除智能客服", description="软删除")
async def delete_agents(ids: IdList = Depends(), auth: Auth = Depends(FullAdminAuth())):
    await crud.AgentDal(auth.db).delete_datas(ids=ids.ids, v_soft=True)
    return SuccessResponse("删除成功")


@app.get("/agents/{data_id}", summary="获取智能客服详情")
async def get_agent(data_id: int, auth: Auth = Depends(FullAdminAuth())):
    schema = schemas.AgentSimpleOut
    return SuccessResponse(await crud.AgentDal(auth.db).get_data(data_id, v_schema=schema))


@app.post("/agents/test", summary="测试智能客服连通性（请求体须含当前表单的 api_server、app_key、remark；id 可空）")
async def test_agent(data: schemas.AgentTestIn, auth: Auth = Depends(FullAdminAuth())):
    try:
        result = await crud.AgentDal(auth.db).test_connection(
            api_server=data.api_server,
            app_key=data.app_key,
            remark=data.remark,
            data_id=data.id,
            service_type=data.service_type,
        )
        return SuccessResponse(result, msg="测试成功")
    except Exception as e:
        return ErrorResponse(msg=str(e))


@app.put("/agents/{data_id}/publish", summary="上架智能客服")
async def publish_agent(data_id: int, auth: Auth = Depends(FullAdminAuth())):
    try:
        result = await crud.AgentDal(auth.db).publish(data_id)
        return SuccessResponse(result, msg="上架成功")
    except Exception as e:
        return ErrorResponse(msg=str(e))


@app.put("/agents/{data_id}/unpublish", summary="下架智能客服")
async def unpublish_agent(data_id: int, auth: Auth = Depends(FullAdminAuth())):
    result = await crud.AgentDal(auth.db).unpublish(data_id)
    return SuccessResponse(result, msg="下架成功")
