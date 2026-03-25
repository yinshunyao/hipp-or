# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from apps.mp_chat import crud, schemas
from apps.vadmin.auth.utils.current import AllUserAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from utils.response import SuccessResponse

app = APIRouter()


@app.get(
    "/agents/{agent_id}/archived-topics",
    summary="按智能体分页查询已归档话题（场景页时间线）",
)
async def list_archived_topics_for_agent(
    agent_id: int,
    limit: int = Query(20, ge=1, le=50),
    before_update_ts: float | None = Query(None, description="当前列表最旧一条的 update_ts"),
    before_session_id: int | None = Query(None, ge=1, description="当前列表最旧一条的 session_id"),
    auth: Auth = Depends(AllUserAuth()),
):
    dal = crud.ChatSessionDal(auth.db)
    data = await dal.list_archived_topics_for_agent(
        auth.user.id,
        agent_id,
        limit=limit,
        before_update_ts=before_update_ts,
        before_session_id=before_session_id,
    )
    return SuccessResponse(data.model_dump())


@app.get("/scene-agent", summary="场景页解析可服务智能体（按类型随机 1 个）")
async def resolve_scene_agent(
    scene: str = Query(..., description="场景标识：requirement/business"),
    auth: Auth = Depends(AllUserAuth()),
):
    dal = crud.ChatSessionDal(auth.db)
    data = await dal.resolve_scene_agent(user_id=auth.user.id, scene=scene)
    return SuccessResponse(data.model_dump())


@app.get("/inbox", summary="对话收件箱")
async def get_inbox(
    q: str | None = Query(None, description="搜索关键词"),
    kind: str | None = Query(
        None,
        description="仅 `session`：仅返回已归档会话行（kind=session），不含智能体入口行（kind=agent）；省略则返回合并列表（智能体+会话）",
    ),
    auth: Auth = Depends(AllUserAuth()),
):
    if kind is not None and kind not in ("session", "staff"):
        raise HTTPException(status_code=422, detail="query kind 仅支持 session、staff 或省略")
    dal = crud.ChatSessionDal(auth.db)
    data = await dal.build_inbox(auth.user.id, q, kind=kind)
    return SuccessResponse(data.model_dump())


@app.post("/sessions", summary="创建会话")
async def create_session(
    body: schemas.CreateSessionIn,
    auth: Auth = Depends(AllUserAuth()),
):
    dal = crud.ChatSessionDal(auth.db)
    return SuccessResponse(await dal.create_session(auth.user.id, body.agent_id))


@app.post("/human-support/sessions", summary="从归档话题创建或进入人工客服会话")
async def create_human_support_session(
    body: schemas.CreateHumanSupportSessionIn,
    auth: Auth = Depends(AllUserAuth()),
):
    dal = crud.ChatSessionDal(auth.db)
    return SuccessResponse(await dal.create_or_get_human_support_session(auth.user.id, body.source_session_id))


@app.get("/sessions/{session_id}", summary="会话详情")
async def get_session(session_id: int, auth: Auth = Depends(AllUserAuth())):
    dal = crud.ChatSessionDal(auth.db)
    return SuccessResponse(await dal.session_detail(session_id, auth.user.id))


@app.patch("/sessions/{session_id}", summary="更新会话（标题、置顶）")
async def patch_session(
    session_id: int,
    body: schemas.PatchSessionIn,
    auth: Auth = Depends(AllUserAuth()),
):
    dal = crud.ChatSessionDal(auth.db)
    return SuccessResponse(await dal.patch_session(session_id, auth.user.id, body))


@app.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(session_id: int, auth: Auth = Depends(AllUserAuth())):
    dal = crud.ChatSessionDal(auth.db)
    await dal.delete_session(session_id, auth.user.id)
    return SuccessResponse("ok")


@app.get("/sessions/{session_id}/messages", summary="会话消息列表")
async def get_messages(
    session_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    auth: Auth = Depends(AllUserAuth()),
):
    dal_s = crud.ChatSessionDal(auth.db)
    await dal_s.get_session_for_participant(session_id, auth.user.id)
    dal_m = crud.ChatMessageDal(auth.db)
    datas, count = await dal_m.list_for_session(session_id, page, limit)
    return SuccessResponse(datas, count=count)


@app.post("/sessions/{session_id}/messages", summary="发送消息（智能体 Dify / 人工客服同步）")
async def post_message(
    session_id: int,
    body: schemas.SendMessageIn,
    auth: Auth = Depends(AllUserAuth()),
):
    dal_s = crud.ChatSessionDal(auth.db)
    sess = await dal_s.get_session_for_participant(session_id, auth.user.id)
    if getattr(sess, "session_kind", "dify") == "human_support":
        if sess.user_id == auth.user.id:
            role = "user"
        elif sess.assigned_human_user_id == auth.user.id:
            role = "assistant"
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
        dal_m = crud.ChatMessageDal(auth.db)
        result = await dal_m.send_human_text(auth.db, sess, role, body.query.strip())
        return SuccessResponse(result)
    agent = await dal_s.assert_session_agent_sendable(sess)
    dal_s.assert_session_topic_sendable(sess)
    dal_m = crud.ChatMessageDal(auth.db)
    result = await dal_m.send_user_and_bot(auth.db, sess, agent, auth.user.id, body.query)
    return SuccessResponse(result)


@app.post("/sessions/{session_id}/messages/stream", summary="发送消息（Dify SSE 流式）")
async def post_message_stream(
    session_id: int,
    body: schemas.SendMessageIn,
    auth: Auth = Depends(AllUserAuth()),
):
    dal_s = crud.ChatSessionDal(auth.db)
    sess = await dal_s.get_session_for_participant(session_id, auth.user.id)
    if getattr(sess, "session_kind", "dify") == "human_support":
        raise HTTPException(status_code=422, detail="人工客服会话不支持流式发送，请使用同步接口")
    agent = await dal_s.assert_session_agent_sendable(sess)
    dal_s.assert_session_topic_sendable(sess)
    dal_m = crud.ChatMessageDal(auth.db)
    # 必须在 return 之前从 ORM 读出标量：流式 body 在路由返回后才执行，届时 sess/agent 可能已分离
    gen = dal_m.stream_user_and_bot(
        session_id_val=sess.id,
        dify_conversation_id_initial=sess.dify_conversation_id,
        api_server=agent.api_server,
        app_key=agent.app_key,
        user_id=auth.user.id,
        query=body.query,
    )
    return StreamingResponse(
        gen,
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
