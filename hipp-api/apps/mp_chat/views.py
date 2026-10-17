# -*- coding: utf-8 -*-
import asyncio
import json
import logging

import jwt
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, WebSocket
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from apps.mp_chat import crud, schemas
from apps.mp_chat.attachments import (
    MAX_AUDIO_STT_BYTES,
    assert_upload_size,
    classify_chat_file,
    is_audio_stt_file,
)
from apps.mp_chat.dify_client import audio_to_text
from apps.vadmin.auth.crud import UserDal
from apps.vadmin.auth.utils.current import AllUserAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from application import settings
from core.database import db_getter, redis_getter, session_factory
from core.exception import CustomException
from utils import hipp_manager
from utils.manager_session import get_manager_token
from utils.response import ErrorResponse, SuccessResponse

app = APIRouter()
logger = logging.getLogger(__name__)


async def _ws_auth_user(token_raw: str, redis=None):
    token = (token_raw or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise CustomException("请您先登录！", code=403)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError as e:
        raise CustomException("无效认证，请您重新登录", code=403) from e
    telephone = payload.get("sub")
    is_refresh = payload.get("is_refresh")
    password = payload.get("password")
    if not telephone or is_refresh or not password:
        raise CustomException("未认证，请您重新登录", code=403)
    async with session_factory() as db:
        user = await UserDal(db).get_data(telephone=telephone, password=password, v_return_none=True)
        if not user:
            raise CustomException("未认证，请您重新登录", code=401)
        if getattr(user, "is_blocked", False):
            raise CustomException("账号已被拉黑", code=401)
        if not user.is_active:
            raise CustomException("用户已被冻结！", code=401)
        from utils.manager_session import enforce_manager_online

        await enforce_manager_online(redis, user)
        return user


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
    data = await dal.resolve_scene_agent(user_id=auth.user.id, scene=scene, user=auth.user)
    return SuccessResponse(data.model_dump())


@app.get("/inbox", summary="对话收件箱")
async def get_inbox(
    q: str | None = Query(None, description="搜索关键词"),
    kind: str | None = Query(
        None,
        description="仅 `session`：仅返回已归档会话行（kind=session），不含智能体入口行（kind=agent）；省略则返回合并列表（智能体+会话）",
    ),
    include_open: bool = Query(
        False,
        description="kind=session 时是否包含已有交互、尚未归档的会话。小程序不传。",
    ),
    auth: Auth = Depends(AllUserAuth()),
):
    if kind is not None and kind not in ("session", "staff"):
        raise HTTPException(status_code=422, detail="query kind 仅支持 session、staff 或省略")
    dal = crud.ChatSessionDal(auth.db)
    data = await dal.build_inbox(auth.user.id, q, kind=kind, include_open=include_open)
    return SuccessResponse(data.model_dump())


@app.get("/session-fee-precheck", summary="建会话/进入空草稿前校验余额是否够付咨询费")
async def session_fee_precheck(auth: Auth = Depends(AllUserAuth())):
    """与创建会话、发消息同一套 46005/46006；不预扣、不落库。"""
    dal = crud.ChatSessionDal(auth.db)
    await dal.assert_user_session_fee_affordable(auth.user.id, auth.user)
    return SuccessResponse({"ok": True})


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


@app.post("/sessions/{session_id}/share", summary="为已完成话题生成或取回分享令牌")
async def create_share(session_id: int, auth: Auth = Depends(AllUserAuth())):
    dal = crud.ChatSessionDal(auth.db)
    token = await dal.ensure_share_token(session_id, auth.user.id)
    return SuccessResponse({"share_token": token})


@app.delete("/sessions/{session_id}/share", summary="停止分享已完成话题")
async def delete_share(session_id: int, auth: Auth = Depends(AllUserAuth())):
    dal = crud.ChatSessionDal(auth.db)
    await dal.clear_share_token(session_id, auth.user.id)
    return SuccessResponse()


@app.get("/share/{token}", summary="免登录查看已完成话题分享")
async def get_share(token: str, db: AsyncSession = Depends(db_getter)):
    dal = crud.ChatSessionDal(db)
    return SuccessResponse(await dal.public_share(token))


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


@app.post("/upload", summary="上传对话附件（经 hipp-manager 公共媒体）")
async def upload_chat_file(
    request: Request,
    file: UploadFile = File(...),
    session_id: int | None = Form(None),
    auth: Auth = Depends(AllUserAuth()),
):
    if session_id is not None:
        dal_s = crud.ChatSessionDal(auth.db)
        sess = await dal_s.get_session_for_participant(session_id, auth.user.id)
        if getattr(sess, "session_kind", "dify") != "dify":
            raise HTTPException(status_code=422, detail="人工客服会话不支持附件")
        await dal_s.assert_session_agent_sendable(sess)
    raw = await file.read()
    ftype = classify_chat_file(file.filename, file.content_type)
    assert_upload_size(ftype, len(raw))
    if not hipp_manager.enabled():
        return ErrorResponse(msg="未配置平台媒体服务", code=503)
    try:
        rd: Redis = redis_getter(request)
    except Exception:
        return ErrorResponse(msg="请重新登录以同步账户", code=401)
    tok = await get_manager_token(rd, auth.user.id)
    if not tok:
        return ErrorResponse(msg="请重新登录以同步账户", code=401)
    try:
        uploaded = hipp_manager.upload_media(
            tok,
            file_bytes=raw,
            filename=file.filename or "file",
            content_type=(file.content_type or "").strip(),
            product="or",
            prefix="chat",
        )
    except hipp_manager.ManagerError as exc:
        code = int(exc.status or 400)
        if code < 400:
            code = 400
        return ErrorResponse(msg=str(exc) or "媒体上传失败", code=code)
    url = str(uploaded.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return ErrorResponse(msg="媒体服务未返回有效地址", code=502)
    return SuccessResponse(
        {
            "type": ftype,
            "name": str(uploaded.get("name") or file.filename or "file"),
            "size": int(uploaded.get("size") or len(raw)),
            "mime": str(uploaded.get("mime") or (file.content_type or "")).strip(),
            "url": url,
        }
    )


@app.delete("/upload", summary="删除未发送的对话附件（平台媒体）")
async def delete_chat_upload(
    request: Request,
    body: schemas.DeleteChatUploadIn,
    auth: Auth = Depends(AllUserAuth()),
):
    url = (body.url or "").strip()
    if not url.startswith(("http://", "https://")) or "/media/" not in url:
        return ErrorResponse(msg="附件地址无效", code=400)
    if not hipp_manager.enabled():
        return ErrorResponse(msg="未配置平台媒体服务", code=503)
    try:
        rd: Redis = redis_getter(request)
    except Exception:
        return ErrorResponse(msg="请重新登录以同步账户", code=401)
    tok = await get_manager_token(rd, auth.user.id)
    if not tok:
        return ErrorResponse(msg="请重新登录以同步账户", code=401)
    try:
        data = hipp_manager.delete_media(tok, url=url)
    except hipp_manager.ManagerError as exc:
        code = int(exc.status or 400)
        if code < 400:
            code = 400
        return ErrorResponse(msg=str(exc) or "媒体删除失败", code=code)
    return SuccessResponse(data if isinstance(data, dict) else {"ok": True})


@app.post("/audio-to-text", summary="语音转文字（Dify）")
async def chat_audio_to_text(
    file: UploadFile = File(...),
    session_id: int = Form(...),
    auth: Auth = Depends(AllUserAuth()),
):
    dal_s = crud.ChatSessionDal(auth.db)
    sess = await dal_s.get_session_for_participant(session_id, auth.user.id)
    if getattr(sess, "session_kind", "dify") != "dify":
        raise HTTPException(status_code=422, detail="人工客服会话不支持语音转写")
    agent = await dal_s.assert_session_agent_sendable(sess)
    raw = await file.read()
    if len(raw) > MAX_AUDIO_STT_BYTES:
        raise CustomException("语音文件过大，不能超过 15MB")
    if not is_audio_stt_file(file.filename, file.content_type):
        raise CustomException("不支持的语音格式")
    text = await audio_to_text(
        agent.api_server,
        agent.app_key,
        f"user-{auth.user.id}",
        filename=file.filename or "audio.webm",
        content=raw,
        content_type=file.content_type,
    )
    return SuccessResponse({"text": text})


@app.post("/sessions/{session_id}/messages", summary="发送消息（智能体 Dify / 人工客服同步）")
async def post_message(
    session_id: int,
    body: schemas.SendMessageIn,
    auth: Auth = Depends(AllUserAuth()),
):
    dal_s = crud.ChatSessionDal(auth.db)
    sess = await dal_s.get_session_for_participant(session_id, auth.user.id)
    if getattr(sess, "session_kind", "dify") == "human_support":
        if body.files:
            raise HTTPException(status_code=422, detail="人工客服会话不支持附件")
        if sess.user_id == auth.user.id:
            role = "user"
        elif sess.assigned_human_user_id == auth.user.id:
            role = "assistant"
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
        dal_m = crud.ChatMessageDal(auth.db)
        result = await dal_m.send_human_text(auth.db, sess, role, (body.query or "").strip())
        return SuccessResponse(result)
    agent = await dal_s.assert_session_agent_sendable(sess)
    dal_s.assert_session_topic_sendable(sess)
    await dal_s.assert_mp_guest_scene_quota(auth.user.id, agent)
    await dal_s.assert_entitlement_sendable(auth.user, agent)
    await dal_s.assert_dify_session_fee_affordable(sess, auth.user)
    dal_m = crud.ChatMessageDal(auth.db)
    result = await dal_m.send_user_and_bot(
        auth.db, sess, agent, auth.user.id, body.query or "", files=body.files
    )
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
    await dal_s.assert_mp_guest_scene_quota(auth.user.id, agent)
    await dal_s.assert_entitlement_sendable(auth.user, agent)
    await dal_s.assert_dify_session_fee_affordable(sess, auth.user)
    dal_m = crud.ChatMessageDal(auth.db)
    files_payload = [f.model_dump() for f in (body.files or [])] or None
    # 必须在 return 之前从 ORM 读出标量：流式 body 在路由返回后才执行，届时 sess/agent 可能已分离
    gen = dal_m.stream_user_and_bot(
        session_id_val=sess.id,
        dify_conversation_id_initial=sess.dify_conversation_id,
        api_server=agent.api_server,
        app_key=agent.app_key,
        user_id=auth.user.id,
        query=body.query or "",
        files=files_payload,
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


@app.websocket("/sessions/{session_id}/messages/ws")
async def post_message_stream_ws(websocket: WebSocket, session_id: int):
    await websocket.accept()
    try:
        await websocket.send_json({"event": "ready"})
        token = websocket.query_params.get("token", "")
        rd = getattr(websocket.app.state, "redis", None)
        user = await _ws_auth_user(token, redis=rd)

        # 兼容两种调用：1) query string 直接传 query；2) 首条 WS 文本消息传 JSON（可含 files）
        query = str(websocket.query_params.get("query") or "").strip()
        files_payload = None
        if not query:
            try:
                payload_text = await asyncio.wait_for(websocket.receive_text(), timeout=60)
            except asyncio.TimeoutError as e:
                raise CustomException("等待消息超时，请重试") from e
            try:
                payload = json.loads(payload_text or "{}")
            except json.JSONDecodeError as e:
                raise CustomException("消息格式错误") from e
            query = str(payload.get("query") or payload.get("message") or "").strip()
            raw_files = payload.get("files")
            if isinstance(raw_files, list) and raw_files:
                files_payload = raw_files
        if not query and not files_payload:
            raise CustomException("请输入内容或添加附件")

        async with session_factory() as db:
            dal_s = crud.ChatSessionDal(db)
            sess = await dal_s.get_session_for_participant(session_id, user.id)
            if getattr(sess, "session_kind", "dify") == "human_support":
                raise CustomException("人工客服会话不支持流式发送，请使用同步接口")
            agent = await dal_s.assert_session_agent_sendable(sess)
            dal_s.assert_session_topic_sendable(sess)
            await dal_s.assert_mp_guest_scene_quota(user.id, agent)
            await dal_s.assert_entitlement_sendable(user, agent)
            await dal_s.assert_dify_session_fee_affordable(sess, user)
            dal_m = crud.ChatMessageDal(db)
            full = ""
            topic_closed = False
            async for chunk in dal_m.stream_user_and_bot(
                session_id_val=sess.id,
                dify_conversation_id_initial=sess.dify_conversation_id,
                api_server=agent.api_server,
                app_key=agent.app_key,
                user_id=user.id,
                query=query,
                files=files_payload,
            ):
                line = chunk.decode("utf-8", errors="ignore").strip()
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if not raw:
                    continue
                try:
                    evt = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if evt.get("event") in ("message", "agent_message"):
                    answer = evt.get("answer")
                    if isinstance(answer, str) and answer:
                        full += answer
                        await websocket.send_json({"event": "delta", "answer": answer, "full_text": full})
                elif evt.get("event") == "mp_topic":
                    topic_closed = bool(evt.get("topic_closed"))
                    await websocket.send_json({"event": "done", "topic_closed": topic_closed})
            if not topic_closed:
                await websocket.send_json({"event": "done", "topic_closed": False})
    except CustomException as e:
        await websocket.send_json(
            {
                "event": "error",
                "code": int(getattr(e, "code", 400) or 400),
                "message": str(getattr(e, "msg", "") or e),
            }
        )
    except Exception as e:
        detail = str(e).strip() or e.__class__.__name__
        logger.exception("mp_chat ws stream failed: session_id=%s", session_id)
        await websocket.send_json({"event": "error", "code": 500, "message": detail})
    finally:
        await websocket.close()
