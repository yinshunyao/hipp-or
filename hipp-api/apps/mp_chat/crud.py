# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import random
import re

from datetime import datetime

from sqlalchemy import Select, and_, exists, false, func, or_, select, true, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from apps.vadmin.agent_manager import models as agent_models
from apps.vadmin.auth.models import VadminUser
from core.database import session_factory
from core.crud import DalBase
from core.exception import CustomException

from . import models, schemas
from .inbox_order import order_archived_inbox_pairs, sort_session_pairs_by_recency_desc
from .session_display import mp_ui_session_title
from .archive_context import format_archive_topic_context
from .human_support import pick_random_human_staff_user_id
from .attachments import (
    dumps_attachments,
    normalize_attachment_dicts,
    preview_for_user,
    resolve_query_and_store,
    to_dify_remote_files,
    use_dify_local_file,
)
from .dify_client import (
    DifyStreamAccumulator,
    extract_conversation_name_from_chat_response,
    fetch_dify_conversation_name,
    generate_dify_conversation_name,
    iter_dify_chat_stream,
    parse_topic_finished_from_raw_answer,
    rewrite_sse_answer_line,
    send_chat_message_blocking,
    strip_finish_status_prefix,
    summarize_session_title,
    upload_file_to_dify,
    usage_total_tokens,
    StreamAnswerPrefixFilter,
)
import httpx

from apps.mp_chat.biz_codes import (
    AGENT_UNAVAILABLE_CODE,
    BALANCE_INSUFFICIENT_CODE,
    BALANCE_INSUFFICIENT_MSG,
    MP_GUEST_TRIAL_EXHAUSTED_CODE,
    MP_GUEST_TRIAL_EXHAUSTED_MSG,
    SCENE_AGENT_UNAVAILABLE_CODE,
    SESSION_FEE_CHECK_FAILED_CODE,
    SESSION_FEE_CHECK_FAILED_MSG,
    SESSION_FEE_NO_PHONE_MSG,
    TOPIC_CLOSED_CODE,
)

_TITLE_REPAIR_INFLIGHT: set[int] = set()
_TITLE_REPAIR_TASKS: set[asyncio.Task] = set()
# 访客在「需求分析」「商业评估」各自可完成的已归档话题上限（按 service_type 分别计数，非两场景合计）
GUEST_SCENE_TRIAL_ARCHIVES_MAX = 2
GUEST_QUOTA_SERVICE_TYPES = frozenset({"需求分析", "商业评估"})
MP_GUEST_USER_TYPE = "mp_guest"
ENTITLEMENT_USER_TYPE = "entitlement"


def _session_update_ts(sess: models.VadminChatSession) -> float:
    dt = sess.update_datetime
    if dt is None:
        return 0.0
    try:
        return float(dt.timestamp())
    except OSError:
        return 0.0


async def _first_user_content_map(db: AsyncSession, session_ids: list[int]) -> dict[int, str]:
    if not session_ids:
        return {}
    r = await db.execute(
        select(models.VadminChatMessage.session_id, models.VadminChatMessage.content)
        .where(
            models.VadminChatMessage.session_id.in_(session_ids),
            models.VadminChatMessage.is_delete == false(),
            models.VadminChatMessage.role == "user",
        )
        .order_by(models.VadminChatMessage.id.asc())
    )
    found: dict[int, str] = {}
    for sid, content in r.all():
        if sid not in found and content:
            found[int(sid)] = str(content)
    return found


async def _first_user_content(db: AsyncSession, session_id: int) -> str:
    r = await db.execute(
        select(models.VadminChatMessage.content)
        .where(
            models.VadminChatMessage.session_id == session_id,
            models.VadminChatMessage.is_delete == false(),
            models.VadminChatMessage.role == "user",
        )
        .order_by(models.VadminChatMessage.id.asc())
        .limit(1)
    )
    return str(r.scalar_one_or_none() or "")


def _preview(text: str, max_len: int = 80) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _is_default_session_title(session_title: str | None, agent_name_snapshot: str | None) -> bool:
    title = (session_title or "").strip()
    snap = (agent_name_snapshot or "").strip()
    if not title:
        return True
    return bool(snap) and title == snap


def _usable_generated_name(name: str | None, agent_name_snapshot: str | None, user_query: str) -> bool:
    text = (name or "").strip()
    if not text or len(text) > 40:
        return False
    low = text.lower()
    if low in {"new conversation", "new chat", "新对话"}:
        return False
    snap = (agent_name_snapshot or "").strip()
    if snap and text == snap:
        return False
    query = (user_query or "").strip()
    if query and text == query:
        return False
    return True


def _is_excerpt_title(title: str | None, user_query: str | None) -> bool:
    """标题只是用户原文的开头，而不是概括。"""
    text = (title or "").strip()
    query = re.sub(r"\s+", " ", (user_query or "").strip())
    if not text or not query:
        return False
    if text.startswith("#") or text.endswith("…"):
        return True
    bare = text.strip()
    if len(bare) >= 12 and (query.startswith(bare) or query.replace(" ", "").startswith(bare.replace(" ", ""))):
        return True
    return False


def _title_should_replace(title: str | None, agent_name_snapshot: str | None, user_query: str | None) -> bool:
    text = (title or "").strip()
    if _is_default_session_title(title, agent_name_snapshot):
        return True
    if text in {"新对话", "对话"}:
        return True
    return _is_excerpt_title(text, user_query)


def _cancel_task(task: asyncio.Task | None) -> None:
    if task is not None and not task.done():
        task.cancel()


def _title_for_archived_topic_fallback(session_title: str, agent_name_snapshot: str | None, user_query: str) -> str:
    """
    在无法从 Dify 取得会话 name 时的最后回退：短摘要，避免把整段用户首问写入标题。
    """
    preview = _preview(user_query, 36)
    default = (agent_name_snapshot or "").strip()
    if (session_title or "").strip() == default:
        return preview[:255]
    return (session_title or "")[:255]


async def _resolve_session_display_title(
    *,
    session_title: str,
    agent_name_snapshot: str | None,
    user_query: str,
    conversation_id: str | None,
    api_server: str,
    app_key: str,
    dify_user: str,
    topic_just_finished: bool,
    blocking_response: dict | None = None,
    pending_summary: asyncio.Task | None = None,
) -> str:
    """
    会话列表展示标题。用户已改过、或已经生成过的标题保持不变。
    仍是智能体默认名，或只是用户原文开头时，重新生成：
    1) blocking 响应体中的 name（若有，且不是原文开头）
    2) GET /v1/conversations 的 data[].name
    3) POST /conversations/{id}/name 自动起名
    4) 另请模型根据对话概括一个短标题
    """
    if not _title_should_replace(session_title, agent_name_snapshot, user_query):
        _cancel_task(pending_summary)
        return (session_title or "")[:255]

    def accept(name: str | None) -> str | None:
        if not _usable_generated_name(name, agent_name_snapshot, user_query):
            return None
        if _is_excerpt_title(name, user_query):
            return None
        return (name or "")[:255]

    already_excerpt = _is_excerpt_title(session_title, user_query)
    if not already_excerpt:
        if blocking_response:
            picked = accept(extract_conversation_name_from_chat_response(blocking_response))
            if picked:
                _cancel_task(pending_summary)
                return picked
        if conversation_id:
            picked = accept(await fetch_dify_conversation_name(api_server, app_key, conversation_id, dify_user))
            if picked:
                _cancel_task(pending_summary)
                return picked
            picked = accept(await generate_dify_conversation_name(api_server, app_key, conversation_id, dify_user))
            if picked:
                _cancel_task(pending_summary)
                return picked
    if pending_summary is not None:
        try:
            summarized = await pending_summary
        except Exception:
            summarized = None
        picked = accept(summarized if isinstance(summarized, str) else None)
        if picked:
            return picked
    elif (user_query or "").strip() and api_server and app_key:
        picked = accept(await summarize_session_title(api_server, app_key, dify_user, user_query))
        if picked:
            return picked
    current = (session_title or "").strip()
    if current and not _title_should_replace(current, agent_name_snapshot, user_query):
        return current[:255]
    if topic_just_finished:
        fallback = _title_for_archived_topic_fallback(session_title, agent_name_snapshot, user_query)
        if not _is_excerpt_title(fallback, user_query):
            return fallback[:255]
    return current[:255] or "新对话"


async def _repair_titles_background(user_id: int, session_ids: list[int]) -> None:
    try:
        async with session_factory() as db:
            async with db.begin():
                r = await db.execute(
                    select(models.VadminChatSession, agent_models.VadminAgent)
                    .outerjoin(
                        agent_models.VadminAgent,
                        models.VadminChatSession.agent_id == agent_models.VadminAgent.id,
                    )
                    .where(
                        models.VadminChatSession.id.in_(session_ids),
                        models.VadminChatSession.user_id == user_id,
                        models.VadminChatSession.is_delete == false(),
                    )
                )
                first_map = await _first_user_content_map(db, session_ids)
                for sess, ag in r.all():
                    query = first_map.get(sess.id) or ""
                    if not ag or not query or not _title_should_replace(sess.title, sess.agent_name_snapshot, query):
                        continue
                    new_title = await _resolve_session_display_title(
                        session_title=sess.title,
                        agent_name_snapshot=sess.agent_name_snapshot,
                        user_query=query,
                        conversation_id=sess.dify_conversation_id,
                        api_server=ag.api_server,
                        app_key=ag.app_key,
                        dify_user=f"user-{user_id}",
                        topic_just_finished=False,
                    )
                    if new_title and not _title_should_replace(new_title, sess.agent_name_snapshot, query):
                        sess.title = new_title
    except Exception:
        return
    finally:
        for sid in session_ids:
            _TITLE_REPAIR_INFLIGHT.discard(sid)


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

    async def _count_guest_scene_archived_sessions(self, user_id: int, service_type: str) -> int:
        st = (service_type or "").strip()
        if st not in GUEST_QUOTA_SERVICE_TYPES:
            return 0
        sql = (
            select(func.count())
            .select_from(self.model)
            .join(
                agent_models.VadminAgent,
                self.model.agent_id == agent_models.VadminAgent.id,
            )
            .where(
                self.model.user_id == user_id,
                self.model.is_delete == false(),
                self.model.session_kind == "dify",
                self.model.is_topic_closed == true(),
                agent_models.VadminAgent.service_type == st,
            )
        )
        r = await self.db.execute(sql)
        return int(r.scalar_one() or 0)

    async def resolve_scene_agent(
        self,
        *,
        user_id: int,
        scene: str,
        user: VadminUser | None = None,
    ) -> schemas.SceneAgentOut:
        """
        场景页入口解析：按 scene 映射 service_type，从可服务智能体中挑选一个（同类型多候选时随机 1 个）。
        可选返回该智能体下用户当前进行中会话（is_topic_closed=false）。
        """

        scene_norm = (scene or "").strip().lower()
        if scene_norm == "requirement":
            service_type = "需求分析"
        elif scene_norm == "business":
            service_type = "商业评估"
        else:
            raise CustomException("scene 仅支持 requirement 或 business", code=422)

        sql = (
            select(agent_models.VadminAgent)
            .where(
                agent_models.VadminAgent.is_delete == false(),
                agent_models.VadminAgent.status == "published",
                agent_models.VadminAgent.service_type == service_type,
            )
            .order_by(agent_models.VadminAgent.id.asc())
        )
        r = await self.db.execute(sql)
        agents = list(r.scalars().all())
        if not agents:
            raise CustomException(
                "当前场景暂不可用，请稍后再试",
                code=SCENE_AGENT_UNAVAILABLE_CODE,
            )
        chosen = random.choice(agents)

        await self._retire_empty_prepaid_open_sessions(user_id, chosen.id)
        open_sess = await self._latest_reusable_open_session(user_id, chosen.id)

        guest_scene_archived_count = 0
        guest_need_login = False
        guest_scene_trial_limit = GUEST_SCENE_TRIAL_ARCHIVES_MAX
        if user and getattr(user, "user_type", "") == MP_GUEST_USER_TYPE:
            guest_scene_archived_count = await self._count_guest_scene_archived_sessions(user_id, service_type)
            guest_need_login = bool(
                guest_scene_archived_count >= guest_scene_trial_limit and open_sess is None
            )
        if user and getattr(user, "user_type", "") == ENTITLEMENT_USER_TYPE:
            from apps.commerce import service as commerce
            from apps.commerce.biz_codes import (
                ENTITLEMENT_SCENE_DENIED_CODE,
                ENTITLEMENT_SCENE_DENIED_MSG,
            )

            if service_type != commerce.SERVICE_TYPE_REQUIREMENT:
                raise CustomException(
                    ENTITLEMENT_SCENE_DENIED_MSG,
                    code=ENTITLEMENT_SCENE_DENIED_CODE,
                )
            await commerce.assert_entitlement_may_use_agent(self.db, user, service_type)

        return schemas.SceneAgentOut(
            service_type=service_type,
            agent=schemas.AgentSnippetOut.model_validate(chosen),
            session=(schemas.SessionListOut.model_validate(open_sess) if open_sess else None),
            guest_scene_archived_count=guest_scene_archived_count,
            guest_scene_trial_limit=guest_scene_trial_limit,
            guest_need_login=guest_need_login,
        )

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

    @staticmethod
    def assert_session_topic_sendable(session: models.VadminChatSession) -> None:
        if session.is_topic_closed:
            raise CustomException(
                "本话题已结束，无法继续发送。请返回列表新建对话，或在会话列表长按该会话选择「继续对话」。",
                code=TOPIC_CLOSED_CODE,
            )

    async def assert_mp_guest_scene_quota(self, user_id: int, agent: agent_models.VadminAgent) -> None:
        u = await self.db.get(VadminUser, user_id)
        if not u or getattr(u, "user_type", "") != MP_GUEST_USER_TYPE:
            return
        st = (agent.service_type or "").strip()
        if st not in GUEST_QUOTA_SERVICE_TYPES:
            return
        n = await self._count_guest_scene_archived_sessions(user_id, st)
        if n >= GUEST_SCENE_TRIAL_ARCHIVES_MAX:
            raise CustomException(
                MP_GUEST_TRIAL_EXHAUSTED_MSG,
                code=MP_GUEST_TRIAL_EXHAUSTED_CODE,
            )

    async def assert_entitlement_sendable(
        self, user: VadminUser, agent: agent_models.VadminAgent
    ) -> None:
        if getattr(user, "user_type", "") != ENTITLEMENT_USER_TYPE:
            return
        from apps.commerce import service as commerce

        await commerce.assert_entitlement_may_use_agent(
            self.db, user, (agent.service_type or "").strip()
        )

    async def get_session_for_participant(self, session_id: int, user_id: int) -> models.VadminChatSession:
        sess = await self.get_data(
            session_id,
            v_options=[joinedload(self.model.agent)],
            v_return_none=True,
        )
        if not sess or sess.is_delete:
            raise CustomException("会话不存在")
        sk = getattr(sess, "session_kind", None) or "dify"
        if sk == "human_support":
            if sess.user_id == user_id or sess.assigned_human_user_id == user_id:
                return sess
            raise CustomException("会话不存在")
        if sess.user_id != user_id:
            raise CustomException("会话不存在")
        return sess

    async def assert_session_owner_customer(self, session_id: int, user_id: int) -> models.VadminChatSession:
        sess = await self.get_data(
            session_id,
            v_where=[self.model.user_id == user_id],
            v_return_none=True,
        )
        if not sess:
            raise CustomException("会话不存在")
        return sess

    async def _human_cs_snippet(self, assigned_uid: int | None) -> schemas.AgentSnippetOut:
        if not assigned_uid:
            return schemas.AgentSnippetOut(
                id=0,
                name="人工客服",
                description=None,
                icon_type="emoji",
                icon="🗨️",
                icon_background="#4F9DFF",
                icon_url=None,
            )
        u = await self.db.get(VadminUser, assigned_uid)
        name = (u.name or "").strip() if u else "人工客服"
        return schemas.AgentSnippetOut(
            id=assigned_uid,
            name=name,
            description=None,
            icon_type="emoji",
            icon="🗨️",
            icon_background="#4F9DFF",
            icon_url=None,
        )

    async def _pair_to_inbox_item(
        self,
        sess: models.VadminChatSession,
        ag: agent_models.VadminAgent | None,
    ) -> schemas.InboxItem:
        if getattr(sess, "session_kind", "dify") == "human_support":
            cs_snip = await self._human_cs_snippet(sess.assigned_human_user_id)
            display = (sess.title or "").strip() or (cs_snip.name or "人工客服")
            session_out = schemas.SessionListOut.model_validate(sess).model_copy(
                update={
                    "agent_status": "active",
                    "display_title": display,
                    "assigned_human_name": cs_snip.name,
                }
            )
            return schemas.InboxItem(
                kind="session",
                session=session_out,
                agent=cs_snip,
            )
        status = self.resolve_agent_status(ag)
        session_out = schemas.SessionListOut.model_validate(sess).model_copy(
            update={
                "agent_status": status,
                "display_title": mp_ui_session_title(sess, ag),
            }
        )
        return schemas.InboxItem(
            kind="session",
            session=session_out,
            agent=self.build_agent_snippet(ag, sess),
        )

    def _pair_to_agent_item(
        self,
        sess: models.VadminChatSession | None,
        ag: agent_models.VadminAgent,
    ) -> schemas.InboxItem:
        session_out = None
        if sess is not None:
            session_out = schemas.SessionListOut.model_validate(sess).model_copy(
                update={
                    "agent_status": "active",
                    "display_title": mp_ui_session_title(sess, ag),
                }
            )
        return schemas.InboxItem(
            kind="agent",
            session=session_out,
            agent=schemas.AgentSnippetOut.model_validate(ag),
        )

    async def _build_inbox_merged(self, user_id: int, q: str | None) -> schemas.InboxOut:
        """默认收件箱：已上架智能体入口行 + 会话行（含归档等）。"""
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
        sess_sql = sess_sql.order_by(self.model.update_datetime.desc())
        r = await self.db.execute(sess_sql)
        pairs = r.all()

        open_active_pairs: list[tuple[models.VadminChatSession, agent_models.VadminAgent]] = []
        archived_pairs: list[tuple[models.VadminChatSession, agent_models.VadminAgent | None]] = []

        for sess, ag in pairs:
            if ag and self.resolve_agent_status(ag) == "active" and not sess.is_topic_closed:
                open_active_pairs.append((sess, ag))
            else:
                archived_pairs.append((sess, ag))

        open_active_pairs = sort_session_pairs_by_recency_desc(open_active_pairs)
        archived_pairs = sort_session_pairs_by_recency_desc(archived_pairs)

        open_session_by_agent_id: dict[int, models.VadminChatSession] = {}
        for sess, ag in open_active_pairs:
            if ag.id not in open_session_by_agent_id:
                open_session_by_agent_id[ag.id] = sess

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
        items: list[schemas.InboxItem] = []
        for ag in r2.scalars().all():
            items.append(self._pair_to_agent_item(open_session_by_agent_id.get(ag.id), ag))

        for sess, ag in archived_pairs:
            items.append(await self._pair_to_inbox_item(sess, ag))

        return schemas.InboxOut(items=items)

    async def _build_inbox_archived_session_only(
        self,
        user_id: int,
        q: str | None,
        *,
        include_open: bool = False,
    ) -> schemas.InboxOut:
        """
        对话 Tab：`kind=session`，无 kind=agent 行。
        默认仅已归档话题。`include_open` 时额外包含已有用户或助手消息、但尚未归档的会话。
        """
        kw = f"%{(q or '').strip()}%" if q and q.strip() else None
        dify_cond = and_(self.model.session_kind == "dify", self.model.is_topic_closed == true())
        if include_open:
            has_talk = exists(
                select(1).where(
                    models.VadminChatMessage.session_id == self.model.id,
                    models.VadminChatMessage.is_delete == false(),
                    models.VadminChatMessage.role.in_(("user", "assistant")),
                )
            )
            dify_cond = and_(
                self.model.session_kind == "dify",
                or_(self.model.is_topic_closed == true(), has_talk),
            )

        sess_sql: Select = (
            select(self.model, agent_models.VadminAgent)
            .outerjoin(agent_models.VadminAgent, self.model.agent_id == agent_models.VadminAgent.id)
            .where(
                self.model.user_id == user_id,
                self.model.is_delete == false(),
                or_(dify_cond, self.model.session_kind == "human_support"),
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
        r = await self.db.execute(sess_sql)
        pairs = list(r.all())
        ordered = order_archived_inbox_pairs(pairs)
        if include_open:
            await self._repair_session_titles(ordered, user_id)
        items: list[schemas.InboxItem] = []
        for sess, ag in ordered:
            items.append(await self._pair_to_inbox_item(sess, ag))
        return schemas.InboxOut(items=items)

    async def _repair_session_titles(self, pairs, user_id: int) -> None:
        """挑出仍需概括的标题，放到请求之外改写，避免列表接口等待模型。"""
        pending = [
            sess.id
            for sess, ag in pairs
            if getattr(sess, "session_kind", "dify") == "dify"
            and ag is not None
            and getattr(ag, "api_server", None)
            and getattr(ag, "app_key", None)
            and sess.id not in _TITLE_REPAIR_INFLIGHT
        ]
        if not pending:
            return
        first_map = await _first_user_content_map(self.db, pending)
        targets: list[int] = []
        for sess, _ag in pairs:
            if sess.id not in first_map:
                continue
            query = first_map.get(sess.id) or ""
            if not query or not _title_should_replace(sess.title, sess.agent_name_snapshot, query):
                continue
            if sess.id in _TITLE_REPAIR_INFLIGHT:
                continue
            targets.append(sess.id)
            if len(targets) >= 2:
                break
        if not targets:
            return
        _TITLE_REPAIR_INFLIGHT.update(targets)
        task = asyncio.create_task(_repair_titles_background(user_id, targets))
        _TITLE_REPAIR_TASKS.add(task)
        task.add_done_callback(_TITLE_REPAIR_TASKS.discard)

    async def _pair_to_staff_inbox_item(
        self,
        sess: models.VadminChatSession,
        end_user: VadminUser,
    ) -> schemas.InboxItem:
        end_name = (end_user.nickname or end_user.name or "").strip() or f"用户{end_user.id}"
        session_out = schemas.SessionListOut.model_validate(sess).model_copy(
            update={
                "agent_status": "active",
                "display_title": f"用户 {end_name}",
            }
        )
        peer = schemas.AgentSnippetOut(
            id=end_user.id,
            name=end_name,
            description=None,
            icon_type="emoji",
            icon="👤",
            icon_background="#C47F0A",
            icon_url=None,
        )
        return schemas.InboxItem(kind="session", session=session_out, agent=peer)

    async def _build_inbox_staff(self, staff_user_id: int, q: str | None) -> schemas.InboxOut:
        kw = f"%{(q or '').strip()}%" if q and q.strip() else None
        sess_sql = (
            select(self.model, VadminUser)
            .join(VadminUser, self.model.user_id == VadminUser.id)
            .where(
                self.model.assigned_human_user_id == staff_user_id,
                self.model.session_kind == "human_support",
                self.model.is_delete == false(),
            )
        )
        if kw:
            sess_sql = sess_sql.where(
                or_(
                    self.model.title.like(kw),
                    self.model.last_message_preview.like(kw),
                    VadminUser.name.like(kw),
                    VadminUser.nickname.like(kw),
                )
            )
        sess_sql = sess_sql.order_by(self.model.update_datetime.desc())
        r = await self.db.execute(sess_sql)
        rows = r.all()
        items: list[schemas.InboxItem] = []
        for sess, u in rows:
            items.append(await self._pair_to_staff_inbox_item(sess, u))
        return schemas.InboxOut(items=items)

    async def build_inbox(
        self,
        user_id: int,
        q: str | None,
        *,
        kind: str | None = None,
        include_open: bool = False,
    ) -> schemas.InboxOut:
        if kind == "session":
            return await self._build_inbox_archived_session_only(
                user_id, q, include_open=include_open
            )
        if kind == "staff":
            return await self._build_inbox_staff(user_id, q)
        return await self._build_inbox_merged(user_id, q)

    async def list_archived_topics_for_agent(
        self,
        user_id: int,
        agent_id: int,
        *,
        limit: int = 20,
        before_update_ts: float | None = None,
        before_session_id: int | None = None,
    ) -> schemas.ArchivedTopicsPageOut:
        """
        某智能体下已归档话题分页：面向场景页时间线。
        - 每页取「不早于游标」维度下最近的 limit 条（按 update 新→旧），再**逆序**输出为
          时间正序（旧→新），使数组末尾紧邻当前会话消息区（最新归档贴近消息）。
        - 游标 (before_update_ts, before_session_id) 表示「已展示的最旧一条」；下一页取比它更旧的记录。
        """
        cap = min(max(int(limit), 1), 50)
        if (before_update_ts is not None) ^ (before_session_id is not None):
            raise CustomException("分页参数不完整：before_update_ts 与 before_session_id 需成对传入")

        conds = [
            self.model.user_id == user_id,
            self.model.agent_id == agent_id,
            self.model.is_delete == false(),
            self.model.is_topic_closed == true(),
        ]
        if before_update_ts is not None and before_session_id is not None:
            cursor_dt = datetime.utcfromtimestamp(float(before_update_ts))
            conds.append(
                or_(
                    self.model.update_datetime < cursor_dt,
                    and_(
                        self.model.update_datetime == cursor_dt,
                        self.model.id < int(before_session_id),
                    ),
                )
            )
        sql = (
            select(self.model, agent_models.VadminAgent)
            .outerjoin(agent_models.VadminAgent, self.model.agent_id == agent_models.VadminAgent.id)
            .where(and_(*conds))
            .order_by(self.model.update_datetime.desc(), self.model.id.desc())
            .limit(cap + 1)
        )
        r = await self.db.execute(sql)
        rows = list(r.all())
        has_more = len(rows) > cap
        rows = rows[:cap]
        rows.reverse()

        items: list[schemas.ArchivedTopicItemOut] = []
        for sess, ag in rows:
            items.append(
                schemas.ArchivedTopicItemOut(
                    session_id=sess.id,
                    display_title=mp_ui_session_title(sess, ag),
                    update_ts=_session_update_ts(sess),
                )
            )
        return schemas.ArchivedTopicsPageOut(items=items, has_more=has_more)

    @staticmethod
    def _session_has_talk_exists():
        """未删除的用户/助手消息存在性子查询（关联当前会话行）。"""
        return exists(
            select(1).where(
                models.VadminChatMessage.session_id == models.VadminChatSession.id,
                models.VadminChatMessage.is_delete == false(),
                models.VadminChatMessage.role.in_(("user", "assistant")),
            )
        )

    async def _retire_empty_prepaid_open_sessions(self, user_id: int, agent_id: int) -> None:
        """
        旧版「创建即扣」遗留空壳：未结束、已扣费、无用户/助手消息。
        软删以免场景页 / 新会话路径再次捡起。
        """
        has_talk = self._session_has_talk_exists()
        sql = select(self.model.id).where(
            self.model.is_delete == false(),
            self.model.session_kind == "dify",
            self.model.user_id == user_id,
            self.model.agent_id == agent_id,
            self.model.is_topic_closed == false(),
            self.model.fee_charged == true(),
            ~has_talk,
        )
        r = await self.db.execute(sql)
        ids = [int(row[0]) for row in r.all()]
        if ids:
            await self.delete_datas(ids, v_soft=True)

    async def _latest_reusable_open_session(
        self, user_id: int, agent_id: int
    ) -> models.VadminChatSession | None:
        """进行中会话：有交互的优先；否则仅未扣费空草稿。"""
        has_talk = self._session_has_talk_exists()
        sql = (
            select(self.model)
            .where(
                self.model.is_delete == false(),
                self.model.session_kind == "dify",
                self.model.user_id == user_id,
                self.model.agent_id == agent_id,
                self.model.is_topic_closed == false(),
                or_(has_talk, self.model.fee_charged == false()),
            )
            .order_by(
                has_talk.desc(),
                self.model.update_datetime.desc(),
                self.model.id.desc(),
            )
            .limit(1)
        )
        rr = await self.db.execute(sql)
        return rr.scalar_one_or_none()

    async def create_session(self, user_id: int, agent_id: int) -> dict:
        ag = await self.get_published_agent(agent_id)
        u = await self.db.get(VadminUser, user_id)
        if u and getattr(u, "user_type", "") == MP_GUEST_USER_TYPE:
            st = (ag.service_type or "").strip()
            if st in GUEST_QUOTA_SERVICE_TYPES:
                n = await self._count_guest_scene_archived_sessions(user_id, st)
                if n >= GUEST_SCENE_TRIAL_ARCHIVES_MAX:
                    raise CustomException(
                        MP_GUEST_TRIAL_EXHAUSTED_MSG,
                        code=MP_GUEST_TRIAL_EXHAUSTED_CODE,
                    )
        if u and getattr(u, "user_type", "") == ENTITLEMENT_USER_TYPE:
            from apps.commerce import service as commerce

            ent = await commerce.assert_entitlement_may_use_agent(
                self.db, u, (ag.service_type or "").strip()
            )
            if ent.bound_session_id:
                existing = await self.get_data(
                    ent.bound_session_id,
                    v_where=[self.model.user_id == user_id, self.model.is_delete == false()],
                    v_return_none=True,
                )
                if existing and not bool(existing.is_topic_closed):
                    return await self.session_detail(existing.id, user_id)
        # 建空会话前即校验余额，避免用户写完长文再因 46005 失败
        await self.assert_user_session_fee_affordable(user_id, u)
        await self._retire_empty_prepaid_open_sessions(user_id, agent_id)
        title = ag.name or f"智能体 #{ag.id}"
        obj = self.model(
            user_id=user_id,
            agent_id=agent_id,
            session_kind="dify",
            title=title,
            agent_name_snapshot=ag.name,
            agent_avatar_snapshot=ag.icon_url,
            last_message_preview=None,
            is_pinned=False,
            dify_conversation_id=None,
            is_topic_closed=False,
            fee_charged=False,
        )
        await self.flush(obj)
        if u and getattr(u, "user_type", "") == ENTITLEMENT_USER_TYPE:
            from apps.commerce import service as commerce

            await commerce.bind_session(self.db, user_id, obj.id)
        return await self.session_detail(obj.id, user_id)

    async def assert_user_session_fee_affordable(
        self, user_id: int, user: VadminUser | None = None
    ) -> None:
        """校验用户余额足以支付一次会话咨询费（不预扣、不依赖具体 session）。"""
        u = user
        if u is None:
            u = await self.db.get(VadminUser, user_id)
        if u and getattr(u, "user_type", "") in (MP_GUEST_USER_TYPE, ENTITLEMENT_USER_TYPE):
            return
        from decimal import Decimal

        from apps.vadmin.billing import service as billing_service
        from utils import hipp_manager

        amount, _ = await billing_service.resolve_session_fee(self.db, user_id)
        if not amount or amount <= 0:
            return
        phone = str(getattr(u, "telephone", None) or "").strip() if u else ""
        if not phone:
            raise CustomException(
                SESSION_FEE_NO_PHONE_MSG,
                code=SESSION_FEE_CHECK_FAILED_CODE,
            )
        try:
            data = hipp_manager.s2s_balance(phone=phone)
            bal = Decimal(str((data or {}).get("balance") or "0"))
        except hipp_manager.ManagerError as exc:
            raise CustomException(
                str(exc) or SESSION_FEE_CHECK_FAILED_MSG,
                code=SESSION_FEE_CHECK_FAILED_CODE,
            ) from exc
        if bal < amount:
            raise CustomException(
                BALANCE_INSUFFICIENT_MSG,
                code=BALANCE_INSUFFICIENT_CODE,
            )

    async def assert_dify_session_fee_affordable(
        self, sess: models.VadminChatSession, user: VadminUser | None = None
    ) -> None:
        """发送前校验余额足以支付本话题结束后的咨询费（不预扣）。"""
        if getattr(sess, "session_kind", "dify") != "dify":
            return
        if bool(getattr(sess, "fee_charged", False)):
            return
        await self.assert_user_session_fee_affordable(sess.user_id, user)

    async def charge_dify_session_fee_on_topic_close(
        self, sess: models.VadminChatSession, user: VadminUser | None = None
    ) -> bool:
        """话题结束时扣一次咨询费。成功返回 True；失败不抛错，保持 fee_charged=false。"""
        if getattr(sess, "session_kind", "dify") != "dify":
            return True
        if bool(getattr(sess, "fee_charged", False)):
            return True
        if not bool(getattr(sess, "is_topic_closed", False)):
            return False
        u = user
        if u is None:
            u = await self.db.get(VadminUser, sess.user_id)
        if u and getattr(u, "user_type", "") == MP_GUEST_USER_TYPE:
            sess.fee_charged = True
            await self.flush(sess)
            return True
        if u and getattr(u, "user_type", "") == ENTITLEMENT_USER_TYPE:
            from apps.commerce import service as commerce

            await commerce.mark_used_on_topic_close(self.db, sess.id, sess.user_id)
            sess.fee_charged = True
            await self.flush(sess)
            return True
        from apps.vadmin.billing import service as billing_service
        from utils import hipp_manager

        amount, _ = await billing_service.resolve_session_fee(self.db, sess.user_id)
        if not amount or amount <= 0:
            sess.fee_charged = True
            await self.flush(sess)
            return True
        phone = str(getattr(u, "telephone", None) or "").strip() if u else ""
        if not phone:
            return False
        try:
            hipp_manager.s2s_deduct(
                phone=phone,
                amount=amount,
                ref_id=f"or_session_{sess.id}",
                remark=f"话题咨询结束 session={sess.id}",
                product="or",
                biz_type="consume_session",
            )
        except hipp_manager.ManagerError:
            return False
        sess.fee_charged = True
        await self.flush(sess)
        return True

    async def ensure_dify_session_fee(
        self, sess: models.VadminChatSession, user: VadminUser | None = None
    ) -> None:
        """兼容旧名：仅在话题已结束时尝试扣费。"""
        await self.charge_dify_session_fee_on_topic_close(sess, user)

    async def create_or_get_human_support_session(self, user_id: int, source_session_id: int) -> dict:
        u0 = await self.db.get(VadminUser, user_id)
        if u0 and getattr(u0, "user_type", "") == MP_GUEST_USER_TYPE:
            raise CustomException(
                "请先打开底部「我的」Tab 完成登录后再使用人工客服。",
                code=MP_GUEST_TRIAL_EXHAUSTED_CODE,
            )
        if u0 and getattr(u0, "user_type", "") == ENTITLEMENT_USER_TYPE:
            from apps.commerce.biz_codes import (
                ENTITLEMENT_SCENE_DENIED_CODE,
                ENTITLEMENT_SCENE_DENIED_MSG,
            )

            raise CustomException(
                ENTITLEMENT_SCENE_DENIED_MSG,
                code=ENTITLEMENT_SCENE_DENIED_CODE,
            )
        src = await self.get_data(
            source_session_id,
            v_where=[self.model.user_id == user_id, self.model.is_delete == false()],
            v_options=[joinedload(self.model.agent)],
            v_return_none=True,
        )
        if not src:
            raise CustomException("会话不存在")
        if getattr(src, "session_kind", "dify") != "dify":
            raise CustomException("仅支持从智能体归档话题发起人工客服")
        if not src.is_topic_closed:
            raise CustomException("仅已归档话题可发起人工客服")

        # 已有人工会话关联该归档：会话行上的 source 或历史里已有该来源的 system 提示（合并多归档后行上可能仍为首次来源 id）
        src_needle = f"来源会话 ID：{source_session_id}"
        r0 = await self.db.execute(
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.session_kind == "human_support",
                self.model.is_delete == false(),
                or_(
                    self.model.source_archive_session_id == source_session_id,
                    exists(
                        select(1).where(
                            models.VadminChatMessage.session_id == self.model.id,
                            models.VadminChatMessage.is_delete == false(),
                            models.VadminChatMessage.role == "system",
                            models.VadminChatMessage.content.like(f"%{src_needle}%"),
                        )
                    ),
                ),
            )
            .limit(1)
        )
        existing = r0.scalar_one_or_none()
        if existing:
            return await self.session_detail(existing.id, user_id)

        mr = await self.db.execute(
            select(models.VadminChatMessage.role, models.VadminChatMessage.content)
            .where(
                models.VadminChatMessage.session_id == source_session_id,
                models.VadminChatMessage.is_delete == false(),
            )
            .order_by(models.VadminChatMessage.id)
        )
        msgs = [(r[0], r[1]) for r in mr.all()]
        src_title = mp_ui_session_title(src, src.agent)
        system_text = format_archive_topic_context(
            source_session_id=source_session_id,
            display_title=src_title,
            messages=msgs,
        )

        # 同一用户与人工客服侧只保留一条进行中的会话：若已有未结束的人工会话，并入新归档提示，不新建会话、不重新分配客服
        r_open = await self.db.execute(
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.session_kind == "human_support",
                self.model.is_delete == false(),
                self.model.is_topic_closed == false(),
            )
            .order_by(self.model.update_datetime.desc())
            .limit(1)
        )
        open_existing = r_open.scalar_one_or_none()
        if open_existing:
            sys_msg = models.VadminChatMessage(session_id=open_existing.id, role="system", content=system_text)
            await ChatMessageDal(self.db).flush(sys_msg)
            open_existing.last_message_preview = _preview(system_text, 80)
            await self.flush(open_existing)
            return await self.session_detail(open_existing.id, user_id)

        staff_id = await pick_random_human_staff_user_id(self.db)
        if not staff_id:
            raise CustomException("暂无可用的客服，请稍后再试")

        staff_user = await self.db.get(VadminUser, staff_id)
        cs_name = (staff_user.name or "").strip() if staff_user else f"客服{staff_id}"
        if not cs_name:
            cs_name = f"客服{staff_id}"

        obj = self.model(
            user_id=user_id,
            agent_id=None,
            session_kind="human_support",
            assigned_human_user_id=staff_id,
            source_archive_session_id=source_session_id,
            title=cs_name,
            agent_name_snapshot=cs_name,
            agent_avatar_snapshot=None,
            last_message_preview=_preview(system_text, 80),
            is_pinned=False,
            dify_conversation_id=None,
            is_topic_closed=False,
        )
        await self.flush(obj)
        sys_msg = models.VadminChatMessage(session_id=obj.id, role="system", content=system_text)
        await ChatMessageDal(self.db).flush(sys_msg)
        return await self.session_detail(obj.id, user_id)

    async def session_detail(self, session_id: int, user_id: int) -> dict:
        sess = await self.get_session_for_participant(session_id, user_id)
        sk = getattr(sess, "session_kind", None) or "dify"
        if sk == "human_support":
            return await self._session_detail_human(sess, user_id)
        # 已结束未扣费：打开详情时补扣（覆盖流式路径抖动或历史话题）
        if bool(getattr(sess, "is_topic_closed", False)) and not bool(
            getattr(sess, "fee_charged", False)
        ):
            await self.charge_dify_session_fee_on_topic_close(sess)
        status = self.resolve_agent_status(sess.agent)
        out = schemas.SessionDetailOut.model_validate(sess, from_attributes=True).model_copy(
            update={
                "session_kind": "dify",
                "viewer_context": "owner",
                "agent_status": status,
                "agent": self.build_agent_snippet(sess.agent, sess),
                "display_title": mp_ui_session_title(sess, sess.agent),
                "assigned_human_user_id": None,
                "assigned_human_name": None,
                "end_user_display_name": None,
                "source_archive_session_id": None,
            }
        )
        return out.model_dump()

    async def _session_detail_human(self, sess: models.VadminChatSession, user_id: int) -> dict:
        vc = "assigned_staff" if user_id == sess.assigned_human_user_id else "owner"
        cs_user = await self.db.get(VadminUser, sess.assigned_human_user_id) if sess.assigned_human_user_id else None
        end_user = await self.db.get(VadminUser, sess.user_id) if sess.user_id else None
        cs_name = (cs_user.name or "").strip() if cs_user else (sess.title or "人工客服")
        if not cs_name:
            cs_name = "人工客服"
        end_name = (end_user.nickname or end_user.name or "").strip() if end_user else "用户"
        if not end_name:
            end_name = f"用户{sess.user_id}"
        if vc == "owner":
            display_title = cs_name
            agent_snip = schemas.AgentSnippetOut(
                id=cs_user.id if cs_user else (sess.assigned_human_user_id or 0),
                name=cs_name,
                description=None,
                icon_type="emoji",
                icon="🗨️",
                icon_background="#4F9DFF",
                icon_url=None,
            )
        else:
            display_title = f"用户 {end_name}"
            agent_snip = schemas.AgentSnippetOut(
                id=end_user.id if end_user else sess.user_id,
                name=end_name,
                description=None,
                icon_type="emoji",
                icon="👤",
                icon_background="#C47F0A",
                icon_url=None,
            )
        out = schemas.SessionDetailOut.model_validate(sess, from_attributes=True).model_copy(
            update={
                "session_kind": "human_support",
                "viewer_context": vc,
                "agent_status": "active",
                "agent": agent_snip,
                "display_title": display_title,
                "assigned_human_user_id": sess.assigned_human_user_id,
                "assigned_human_name": cs_name,
                "end_user_display_name": end_name,
            }
        )
        return out.model_dump()

    async def patch_session(self, session_id: int, user_id: int, data: schemas.PatchSessionIn) -> dict:
        sess = await self.assert_session_owner_customer(session_id, user_id)
        payload = data.model_dump(exclude_unset=True)
        if payload.pop("resume_topic", None) is True:
            sess.is_topic_closed = False
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
                "display_title": mp_ui_session_title(refreshed, refreshed.agent),
            }
        )
        return out.model_dump()

    async def ensure_share_token(self, session_id: int, user_id: int) -> str:
        import secrets

        sess = await self.assert_session_owner_customer(session_id, user_id)
        if not sess.is_topic_closed:
            raise CustomException("只有已完成的话题可以分享")
        if sess.share_token:
            return sess.share_token
        sess.share_token = secrets.token_urlsafe(18)
        await self.flush(sess)
        return sess.share_token

    async def clear_share_token(self, session_id: int, user_id: int) -> None:
        sess = await self.assert_session_owner_customer(session_id, user_id)
        sess.share_token = None
        await self.flush(sess)

    async def public_share(self, token: str) -> dict:
        sess = await self.get_data(
            v_where=[self.model.share_token == (token or "").strip()],
            v_return_none=True,
        )
        if not sess or sess.is_delete or not sess.is_topic_closed or not sess.share_token:
            raise CustomException("分享不存在或已失效", code=404)
        dal_m = ChatMessageDal(self.db)
        rows = []
        page = 1
        total = 0
        while len(rows) < 500:
            datas, count = await dal_m.list_for_session(sess.id, page, 200)
            total = count or 0
            if not datas:
                break
            rows.extend(datas)
            if len(rows) >= total:
                break
            page += 1
        messages = []
        for item in rows[:500]:
            if isinstance(item, dict):
                role = item.get("role") or ""
                content = item.get("content") or ""
                created = item.get("create_datetime")
            else:
                role = item.role
                content = item.content or ""
                created = item.create_datetime
            if isinstance(item, dict):
                atts = item.get("attachments")
            else:
                atts = getattr(item, "attachments", None)
            messages.append(
                schemas.ShareMessageOut(
                    role=role,
                    content=content,
                    attachments=atts,
                    create_datetime=created,
                )
            )
        title = (sess.title or "").strip() or "对话"
        return schemas.ShareOut(title=title, messages=messages).model_dump()

    async def delete_session(self, session_id: int, user_id: int) -> None:
        await self.assert_session_owner_customer(session_id, user_id)
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

    async def send_human_text(
        self,
        db: AsyncSession,
        session: models.VadminChatSession,
        from_role: str,
        content: str,
    ) -> dict:
        msg = models.VadminChatMessage(
            session_id=session.id,
            role=from_role,
            content=content,
        )
        await self.flush(msg)
        session.last_message_preview = _preview(content)
        await ChatSessionDal(db).flush(session)
        return {
            "answer": content,
            "topic_closed": False,
        }

    async def _build_dify_files(
        self,
        api_server: str,
        app_key: str,
        dify_user: str,
        attachments: list[dict] | None,
    ) -> list[dict] | None:
        if not attachments:
            return None
        if not use_dify_local_file():
            return to_dify_remote_files(attachments)
        out: list[dict] = []
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for item in attachments:
                url = item["url"]
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    content = resp.content
                except httpx.HTTPError as e:
                    raise CustomException(f"无法拉取附件: {e!s}") from e
                file_id = await upload_file_to_dify(
                    api_server,
                    app_key,
                    dify_user,
                    filename=item.get("name") or "file",
                    content=content,
                    content_type=item.get("mime") or None,
                )
                out.append(
                    {
                        "type": item["type"],
                        "transfer_method": "local_file",
                        "upload_file_id": file_id,
                    }
                )
        return out

    async def send_user_and_bot(
        self,
        db: AsyncSession,
        session: models.VadminChatSession,
        agent: agent_models.VadminAgent,
        user_id: int,
        query: str,
        files: list | None = None,
    ) -> dict:
        attachments = normalize_attachment_dicts(files)
        dify_query, store_content = resolve_query_and_store(query, attachments)
        att_json = dumps_attachments(attachments)
        user_msg = models.VadminChatMessage(
            session_id=session.id,
            role="user",
            content=store_content,
            attachments=att_json,
        )
        await ChatMessageDal(db).flush(user_msg)
        session.last_message_preview = preview_for_user(store_content, attachments)
        await ChatSessionDal(db).flush(session)

        dify_user = f"user-{user_id}"
        first_q = await _first_user_content(db, session.id)
        title_task = None
        title_seed = first_q or store_content
        if _title_should_replace(session.title, session.agent_name_snapshot, title_seed):
            title_task = asyncio.create_task(
                summarize_session_title(
                    agent.api_server,
                    agent.app_key,
                    dify_user,
                    title_seed,
                )
            )
        try:
            dify_files = await self._build_dify_files(
                agent.api_server, agent.app_key, dify_user, attachments
            )
            data = await send_chat_message_blocking(
                api_server=agent.api_server,
                app_key=agent.app_key,
                query=dify_query,
                dify_user=dify_user,
                conversation_id=session.dify_conversation_id,
                files=dify_files,
            )
        except Exception:
            _cancel_task(title_task)
            raise
        answer_raw = data.get("answer")
        if answer_raw is None or answer_raw == "":
            raise CustomException("Dify 未返回有效回答")
        topic_finished = parse_topic_finished_from_raw_answer(str(answer_raw))
        answer = strip_finish_status_prefix(str(answer_raw))
        if not (answer or "").strip():
            answer = "（无内容）"

        conv_id = data.get("conversation_id") or session.dify_conversation_id
        session.dify_conversation_id = conv_id
        session.last_message_preview = _preview(answer)
        if topic_finished:
            session.is_topic_closed = True
        session.token_usage = int(session.token_usage or 0) + usage_total_tokens(data)
        session.title = await _resolve_session_display_title(
            session_title=session.title,
            agent_name_snapshot=session.agent_name_snapshot,
            user_query=title_seed,
            conversation_id=conv_id,
            api_server=agent.api_server,
            app_key=agent.app_key,
            dify_user=dify_user,
            topic_just_finished=topic_finished,
            blocking_response=data,
            pending_summary=title_task,
        )
        dal_sess = ChatSessionDal(db)
        await dal_sess.flush(session)
        if topic_finished:
            await dal_sess.charge_dify_session_fee_on_topic_close(session)

        bot_msg = models.VadminChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
        )
        await ChatMessageDal(db).flush(bot_msg)

        if topic_finished:
            from apps.mp_chat.media_cleanup import cleanup_session_media_after_topic_close

            # 同事务可读刚 flush 的助手正文，避免异步会话看不到结题答案里的引用 URL
            await cleanup_session_media_after_topic_close(db, int(session.id))

        return {
            "answer": answer,
            "conversation_id": conv_id,
            "user_message_id": user_msg.id,
            "assistant_message_id": bot_msg.id,
            "topic_closed": topic_finished,
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
        files: list | None = None,
    ):
        """
        先写入 user 消息，再将 Dify SSE yield 给客户端；流正常结束后落库 assistant 并更新会话。
        流式响应体在路由 return 之后才执行，因此落库使用独立 session，避免请求依赖事务结束后写入丢失。
        """
        attachments = normalize_attachment_dicts(files)
        dify_query, store_content = resolve_query_and_store(query, attachments)
        att_json = dumps_attachments(attachments)
        async with session_factory() as stream_db:
            async with stream_db.begin():
                user_msg = models.VadminChatMessage(
                    session_id=session_id_val,
                    role="user",
                    content=store_content,
                    attachments=att_json,
                )
                stream_db.add(user_msg)
                await stream_db.execute(
                    update(models.VadminChatSession)
                    .where(models.VadminChatSession.id == session_id_val)
                    .values(last_message_preview=preview_for_user(store_content, attachments))
                )

        dify_user = f"user-{user_id}"
        title_task = None
        title_seed = store_content
        async with session_factory() as read_db:
            first_q = await _first_user_content(read_db, session_id_val)
            title_seed = first_q or store_content
            r0 = await read_db.execute(
                select(models.VadminChatSession).where(
                    models.VadminChatSession.id == session_id_val
                )
            )
            sess_for_title = r0.scalar_one()
            if _title_should_replace(sess_for_title.title, sess_for_title.agent_name_snapshot, title_seed):
                title_task = asyncio.create_task(
                    summarize_session_title(api_server, app_key, dify_user, title_seed)
                )
        try:
            dify_files = await self._build_dify_files(api_server, app_key, dify_user, attachments)
        except Exception:
            _cancel_task(title_task)
            raise
        acc = DifyStreamAccumulator()
        answer_filter = StreamAnswerPrefixFilter()
        stream_done = False
        try:
            async for line in iter_dify_chat_stream(
                api_server=api_server,
                app_key=app_key,
                query=dify_query,
                dify_user=dify_user,
                conversation_id=dify_conversation_id_initial,
                files=dify_files,
            ):
                acc.feed_line(line)
                out_line = rewrite_sse_answer_line(line, answer_filter)
                if out_line is None:
                    continue
                yield (out_line + "\n").encode("utf-8")
            stream_done = True
        except Exception:
            _cancel_task(title_task)
            raise
        if not stream_done or acc.error:
            _cancel_task(title_task)
            return
        raw_full = (acc.full_answer or "").strip()
        topic_finished = parse_topic_finished_from_raw_answer(raw_full)
        answer = strip_finish_status_prefix(raw_full)
        if not answer:
            answer = "（无内容）"
        conv_id = acc.conversation_id or dify_conversation_id_initial
        async with session_factory() as read_db:
            first_q = await _first_user_content(read_db, session_id_val)
            r0 = await read_db.execute(
                select(models.VadminChatSession).where(
                    models.VadminChatSession.id == session_id_val
                )
            )
            sess_for_title = r0.scalar_one()
            title_val = await _resolve_session_display_title(
                session_title=sess_for_title.title,
                agent_name_snapshot=sess_for_title.agent_name_snapshot,
                user_query=first_q or store_content,
                conversation_id=conv_id,
                api_server=api_server,
                app_key=app_key,
                dify_user=dify_user,
                topic_just_finished=topic_finished,
                blocking_response=None,
                pending_summary=title_task,
            )
            was_closed = bool(sess_for_title.is_topic_closed)
            was_fee_charged = bool(getattr(sess_for_title, "fee_charged", False))
            tokens = int(sess_for_title.token_usage or 0) + int(acc.total_tokens or 0)
        async with session_factory() as stream_db:
            async with stream_db.begin():
                is_closed = bool(was_closed or topic_finished)
                await stream_db.execute(
                    update(models.VadminChatSession)
                    .where(models.VadminChatSession.id == session_id_val)
                    .values(
                        dify_conversation_id=conv_id,
                        last_message_preview=_preview(answer),
                        is_topic_closed=is_closed,
                        title=title_val,
                        token_usage=tokens,
                    )
                )
                bot_msg = models.VadminChatMessage(
                    session_id=session_id_val,
                    role="assistant",
                    content=answer,
                )
                stream_db.add(bot_msg)
        if topic_finished and not was_closed and not was_fee_charged:
            async with session_factory() as fee_db:
                async with fee_db.begin():
                    r_fee = await fee_db.execute(
                        select(models.VadminChatSession).where(
                            models.VadminChatSession.id == session_id_val
                        )
                    )
                    sess_fee = r_fee.scalar_one()
                    await ChatSessionDal(fee_db).charge_dify_session_fee_on_topic_close(sess_fee)
        if topic_finished and not was_closed:
            from apps.mp_chat.media_cleanup import schedule_topic_media_cleanup

            schedule_topic_media_cleanup(int(session_id_val))
        meta = {"event": "mp_topic", "topic_closed": topic_finished}
        yield (f"data: {json.dumps(meta, ensure_ascii=False)}\n\n").encode("utf-8")
