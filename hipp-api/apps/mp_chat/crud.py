# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import Select, false, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from apps.vadmin.agent_manager import models as agent_models
from core.database import session_factory
from core.crud import DalBase
from core.exception import CustomException

from . import models, schemas
from .dify_client import (
    DifyStreamAccumulator,
    iter_dify_chat_stream,
    rewrite_sse_answer_line,
    send_chat_message_blocking,
    strip_finish_status_prefix,
    StreamAnswerPrefixFilter,
)

AGENT_UNAVAILABLE_CODE = 46001


def _preview(text: str, max_len: int = 80) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


class ChatSessionDal(DalBase):
    def __init__(self, db: AsyncSession):
        super().__init__(db=db, model=models.VadminChatSession, schema=schemas.SessionListOut)

    async def get_published_agent(self, agent_id: int) -> agent_models.VadminAgent:
        sql = (
            select(agent_models.VadminAgent)
            .where(
                agent_models.VadminAgent.id == agent_id,
                agent_models.VadminAgent.is_delete == false(),
                agent_models.VadminAgent.status == "published",
            )
        )
        r = await self.db.execute(sql)
        agent = r.scalar_one_or_none()
        if not agent:
            raise CustomException("智能体不存在或未上架")
        return agent

    @staticmethod
    def resolve_agent_status(agent: agent_models.VadminAgent | None) -> str:
        if agent is None:
            return "deleted"
        if bool(agent.is_delete):
            return "deleted"
        if agent.status != "published":
            return "offline"
        return "active"

    @staticmethod
    def build_agent_snippet(
        agent: agent_models.VadminAgent | None,
        session: models.VadminChatSession | None = None,
    ) -> schemas.AgentSnippetOut:
        if agent is not None:
            return schemas.AgentSnippetOut.model_validate(agent)
        name = None
        icon_url = None
        if session is not None:
            name = session.agent_name_snapshot
            icon_url = session.agent_avatar_snapshot
        return schemas.AgentSnippetOut(
            id=(session.agent_id if session else 0),
            name=name or "已删除智能体",
            description=None,
            icon_type="image" if icon_url else "emoji",
            icon="🗂️" if not icon_url else None,
            icon_background="#D9D9D9",
            icon_url=icon_url,
        )

    async def assert_session_agent_sendable(
        self,
        session: models.VadminChatSession,
    ) -> agent_models.VadminAgent:
        sql = select(agent_models.VadminAgent).where(agent_models.VadminAgent.id == session.agent_id)
        r = await self.db.execute(sql)
        agent = r.scalar_one_or_none()
        status = self.resolve_agent_status(agent)
        if status != "active":
            msg = "智能体已删除，暂不支持继续对话" if status == "deleted" else "智能体已下架，暂不支持继续对话"
            raise CustomException(msg, code=AGENT_UNAVAILABLE_CODE)
        return agent

    async def assert_session_owner(self, session_id: int, user_id: int) -> models.VadminChatSession:
        sess = await self.get_data(
            session_id,
            v_where=[self.model.user_id == user_id],
            v_return_none=True,
        )
        if not sess:
            raise CustomException("会话不存在")
        return sess

    async def build_inbox(self, user_id: int, q: str | None) -> schemas.InboxOut:
        kw = f"%{(q or '').strip()}%" if q and q.strip() else None

        sess_sql: Select = (
            select(self.model, agent_models.VadminAgent)
            .outerjoin(agent_models.VadminAgent, self.model.agent_id == agent_models.VadminAgent.id)
            .where(
                self.model.user_id == user_id,
                self.model.is_delete == false(),
            )
        )
        if kw:
            sess_sql = sess_sql.where(
                or_(
                    self.model.title.like(kw),
                    self.model.last_message_preview.like(kw),
                    self.model.agent_name_snapshot.like(kw),
                    agent_models.VadminAgent.name.like(kw),
                )
            )
        sess_sql = sess_sql.order_by(self.model.is_pinned.desc(), self.model.update_datetime.desc())
        r = await self.db.execute(sess_sql)
        pairs = r.all()

        session_agent_ids: set[int] = set()
        items: list[schemas.InboxItem] = []
        for sess, ag in pairs:
            if ag and self.resolve_agent_status(ag) == "active":
                session_agent_ids.add(ag.id)
            status = self.resolve_agent_status(ag)
            session_out = schemas.SessionListOut.model_validate(sess).model_copy(
                update={"agent_status": status}
            )
            items.append(
                schemas.InboxItem(
                    kind="session",
                    session=session_out,
                    agent=self.build_agent_snippet(ag, sess),
                )
            )

        ag_sql = (
            select(agent_models.VadminAgent)
            .where(
                agent_models.VadminAgent.is_delete == false(),
                agent_models.VadminAgent.status == "published",
            )
            .order_by(agent_models.VadminAgent.name.asc())
        )
        if kw:
            ag_sql = ag_sql.where(
                or_(
                    agent_models.VadminAgent.name.like(kw),
                    agent_models.VadminAgent.description.like(kw),
                )
            )
        r2 = await self.db.execute(ag_sql)
        for ag in r2.scalars().all():
            if ag.id in session_agent_ids:
                continue
            items.append(
                schemas.InboxItem(
                    kind="agent",
                    session=None,
                    agent=schemas.AgentSnippetOut.model_validate(ag),
                )
            )

        return schemas.InboxOut(items=items)

    async def create_session(self, user_id: int, agent_id: int) -> dict:
        ag = await self.get_published_agent(agent_id)
        title = ag.name or f"智能体 #{ag.id}"
        obj = self.model(
            user_id=user_id,
            agent_id=agent_id,
            title=title,
            agent_name_snapshot=ag.name,
            agent_avatar_snapshot=ag.icon_url,
            last_message_preview=None,
            is_pinned=False,
            dify_conversation_id=None,
        )
        await self.flush(obj)
        return await self.session_detail(obj.id, user_id)

    async def session_detail(self, session_id: int, user_id: int) -> dict:
        sess = await self.get_data(
            session_id,
            v_where=[self.model.user_id == user_id],
            v_options=[joinedload(self.model.agent)],
        )
        if not sess:
            raise CustomException("会话不存在")
        status = self.resolve_agent_status(sess.agent)
        out = schemas.SessionDetailOut.model_validate(sess, from_attributes=True).model_copy(
            update={
                "agent_status": status,
                "agent": self.build_agent_snippet(sess.agent, sess),
            }
        )
        return out.model_dump()

    async def patch_session(self, session_id: int, user_id: int, data: schemas.PatchSessionIn) -> dict:
        sess = await self.assert_session_owner(session_id, user_id)
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            setattr(sess, k, v)
        await self.flush(sess)
        refreshed = await self.get_data(
            sess.id,
            v_where=[self.model.user_id == user_id],
            v_options=[joinedload(self.model.agent)],
        )
        status = self.resolve_agent_status(refreshed.agent)
        out = schemas.SessionDetailOut.model_validate(refreshed, from_attributes=True).model_copy(
            update={
                "agent_status": status,
                "agent": self.build_agent_snippet(refreshed.agent, refreshed),
            }
        )
        return out.model_dump()

    async def delete_session(self, session_id: int, user_id: int) -> None:
        await self.assert_session_owner(session_id, user_id)
        await self.delete_datas([session_id], v_soft=True)


class ChatMessageDal(DalBase):
    def __init__(self, db: AsyncSession):
        super().__init__(db=db, model=models.VadminChatMessage, schema=schemas.ChatMessageOut)

    def add_filter_condition(self, sql, **kwargs):
        session_id = kwargs.pop("session_id", None)
        if session_id is not None:
            sql = sql.where(self.model.session_id == session_id)
        return super().add_filter_condition(sql, **kwargs)

    async def list_for_session(self, session_id: int, page: int, limit: int):
        return await self.get_datas(
            page=page,
            limit=limit,
            v_order_field="id",
            session_id=session_id,
            v_schema=schemas.ChatMessageOut,
            v_return_count=True,
        )

    async def send_user_and_bot(
        self,
        db: AsyncSession,
        session: models.VadminChatSession,
        agent: agent_models.VadminAgent,
        user_id: int,
        query: str,
    ) -> dict:
        user_msg = models.VadminChatMessage(
            session_id=session.id,
            role="user",
            content=query,
        )
        await ChatMessageDal(db).flush(user_msg)

        dify_user = f"user-{user_id}"
        data = await send_chat_message_blocking(
            api_server=agent.api_server,
            app_key=agent.app_key,
            query=query,
            dify_user=dify_user,
            conversation_id=session.dify_conversation_id,
        )
        answer = data.get("answer")
        if answer is None or answer == "":
            raise CustomException("Dify 未返回有效回答")
        answer = strip_finish_status_prefix(answer)

        conv_id = data.get("conversation_id") or session.dify_conversation_id
        session.dify_conversation_id = conv_id
        session.last_message_preview = _preview(answer)
        await ChatSessionDal(db).flush(session)

        bot_msg = models.VadminChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
        )
        await ChatMessageDal(db).flush(bot_msg)

        return {
            "answer": answer,
            "conversation_id": conv_id,
            "user_message_id": user_msg.id,
            "assistant_message_id": bot_msg.id,
        }

    async def stream_user_and_bot(
        self,
        *,
        session_id_val: int,
        dify_conversation_id_initial: str | None,
        api_server: str,
        app_key: str,
        user_id: int,
        query: str,
    ):
        """
        先写入 user 消息，再将 Dify SSE yield 给客户端；流正常结束后落库 assistant 并更新会话。
        流式响应体在路由 return 之后才执行，因此落库使用独立 session，避免请求依赖事务结束后写入丢失。
        """
        async with session_factory() as stream_db:
            async with stream_db.begin():
                user_msg = models.VadminChatMessage(
                    session_id=session_id_val,
                    role="user",
                    content=query,
                )
                stream_db.add(user_msg)

        dify_user = f"user-{user_id}"
        acc = DifyStreamAccumulator()
        answer_filter = StreamAnswerPrefixFilter()
        stream_done = False
        try:
            async for line in iter_dify_chat_stream(
                api_server=api_server,
                app_key=app_key,
                query=query,
                dify_user=dify_user,
                conversation_id=dify_conversation_id_initial,
            ):
                acc.feed_line(line)
                out_line = rewrite_sse_answer_line(line, answer_filter)
                if out_line is None:
                    continue
                yield (out_line + "\n").encode("utf-8")
            stream_done = True
        finally:
            if not stream_done:
                return
            if acc.error:
                return
            answer = (acc.full_answer or "").strip()
            answer = strip_finish_status_prefix(answer)
            if not answer:
                answer = "（无内容）"
            conv_id = acc.conversation_id or dify_conversation_id_initial
            async with session_factory() as stream_db:
                async with stream_db.begin():
                    await stream_db.execute(
                        update(models.VadminChatSession)
                        .where(models.VadminChatSession.id == session_id_val)
                        .values(
                            dify_conversation_id=conv_id,
                            last_message_preview=_preview(answer),
                        )
                    )
                    bot_msg = models.VadminChatMessage(
                        session_id=session_id_val,
                        role="assistant",
                        content=answer,
                    )
                    stream_db.add(bot_msg)
