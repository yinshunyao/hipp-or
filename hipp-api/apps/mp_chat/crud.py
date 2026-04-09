# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import random

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
from .dify_client import (
    DifyStreamAccumulator,
    extract_conversation_name_from_chat_response,
    fetch_dify_conversation_name,
    iter_dify_chat_stream,
    parse_topic_finished_from_raw_answer,
    rewrite_sse_answer_line,
    send_chat_message_blocking,
    strip_finish_status_prefix,
    StreamAnswerPrefixFilter,
)

AGENT_UNAVAILABLE_CODE = 46001
TOPIC_CLOSED_CODE = 46002
SCENE_AGENT_UNAVAILABLE_CODE = 46003
MP_GUEST_TRIAL_EXHAUSTED_CODE = 46004
# 访客在「需求分析」「商业评估」各自可完成的已归档话题上限（按 service_type 分别计数，非两场景合计）
GUEST_SCENE_TRIAL_ARCHIVES_MAX = 2
GUEST_QUOTA_SERVICE_TYPES = frozenset({"需求分析", "商业评估"})
MP_GUEST_USER_TYPE = "mp_guest"


def _session_update_ts(sess: models.VadminChatSession) -> float:
    dt = sess.update_datetime
    if dt is None:
        return 0.0
    try:
        return float(dt.timestamp())
    except OSError:
        return 0.0


def _preview(text: str, max_len: int = 80) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


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
) -> str:
    """
    会话列表展示标题：始终优先 Dify 会话 `name`。
    1) blocking 响应体中的 name（若有）
    2) GET /v1/conversations 分页匹配 id 后的 data[].name
    3) 话题刚结束仍无时：短回退（非长文用户 query）
    4) 否则保持原 session_title（例如仍为智能体默认名，待下轮同步）
    """
    if blocking_response:
        n = extract_conversation_name_from_chat_response(blocking_response)
        if n:
            return n[:255]
    if conversation_id:
        dify_name = await fetch_dify_conversation_name(
            api_server, app_key, conversation_id, dify_user
        )
        if dify_name:
            return dify_name[:255]
    if topic_just_finished:
        return _title_for_archived_topic_fallback(session_title, agent_name_snapshot, user_query)
    return (session_title or "")[:255]


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

        open_sess_sql = (
            select(self.model)
            .where(
                self.model.is_delete == false(),
                self.model.session_kind == "dify",
                self.model.user_id == user_id,
                self.model.agent_id == chosen.id,
                self.model.is_topic_closed == false(),
            )
            .order_by(self.model.update_datetime.desc(), self.model.id.desc())
            .limit(1)
        )
        rr = await self.db.execute(open_sess_sql)
        open_sess = rr.scalar_one_or_none()

        guest_scene_archived_count = 0
        guest_need_login = False
        guest_scene_trial_limit = GUEST_SCENE_TRIAL_ARCHIVES_MAX
        if user and getattr(user, "user_type", "") == MP_GUEST_USER_TYPE:
            guest_scene_archived_count = await self._count_guest_scene_archived_sessions(user_id, service_type)
            guest_need_login = bool(
                guest_scene_archived_count >= guest_scene_trial_limit and open_sess is None
            )

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
                "本场景免费体验次数已用完。请打开底部「我的」Tab，进入登录页完成登录后再继续使用。",
                code=MP_GUEST_TRIAL_EXHAUSTED_CODE,
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

    async def _build_inbox_archived_session_only(self, user_id: int, q: str | None) -> schemas.InboxOut:
        """对话 Tab：`kind=session`，仅已归档话题（is_topic_closed=true），无 kind=agent 行。"""
        kw = f"%{(q or '').strip()}%" if q and q.strip() else None

        sess_sql: Select = (
            select(self.model, agent_models.VadminAgent)
            .outerjoin(agent_models.VadminAgent, self.model.agent_id == agent_models.VadminAgent.id)
            .where(
                self.model.user_id == user_id,
                self.model.is_delete == false(),
                or_(
                    and_(self.model.session_kind == "dify", self.model.is_topic_closed == true()),
                    self.model.session_kind == "human_support",
                ),
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
        items: list[schemas.InboxItem] = []
        for sess, ag in ordered:
            items.append(await self._pair_to_inbox_item(sess, ag))
        return schemas.InboxOut(items=items)

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

    async def build_inbox(self, user_id: int, q: str | None, *, kind: str | None = None) -> schemas.InboxOut:
        if kind == "session":
            return await self._build_inbox_archived_session_only(user_id, q)
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

    async def create_session(self, user_id: int, agent_id: int) -> dict:
        ag = await self.get_published_agent(agent_id)
        u = await self.db.get(VadminUser, user_id)
        if u and getattr(u, "user_type", "") == MP_GUEST_USER_TYPE:
            st = (ag.service_type or "").strip()
            if st in GUEST_QUOTA_SERVICE_TYPES:
                n = await self._count_guest_scene_archived_sessions(user_id, st)
                if n >= GUEST_SCENE_TRIAL_ARCHIVES_MAX:
                    raise CustomException(
                        "本场景免费体验次数已用完。请打开底部「我的」Tab，进入登录页完成登录后再继续使用。",
                        code=MP_GUEST_TRIAL_EXHAUSTED_CODE,
                    )
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
        )
        await self.flush(obj)
        return await self.session_detail(obj.id, user_id)

    async def create_or_get_human_support_session(self, user_id: int, source_session_id: int) -> dict:
        u0 = await self.db.get(VadminUser, user_id)
        if u0 and getattr(u0, "user_type", "") == MP_GUEST_USER_TYPE:
            raise CustomException(
                "请先打开底部「我的」Tab 完成登录后再使用人工客服。",
                code=MP_GUEST_TRIAL_EXHAUSTED_CODE,
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
        session.title = await _resolve_session_display_title(
            session_title=session.title,
            agent_name_snapshot=session.agent_name_snapshot,
            user_query=query,
            conversation_id=conv_id,
            api_server=agent.api_server,
            app_key=agent.app_key,
            dify_user=dify_user,
            topic_just_finished=topic_finished,
            blocking_response=data,
        )
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
        except Exception:
            raise
        if not stream_done:
            return
        if acc.error:
            return
        raw_full = (acc.full_answer or "").strip()
        topic_finished = parse_topic_finished_from_raw_answer(raw_full)
        answer = strip_finish_status_prefix(raw_full)
        if not answer:
            answer = "（无内容）"
        conv_id = acc.conversation_id or dify_conversation_id_initial
        async with session_factory() as stream_db:
            async with stream_db.begin():
                r = await stream_db.execute(
                    select(models.VadminChatSession).where(
                        models.VadminChatSession.id == session_id_val
                    )
                )
                sess_row = r.scalar_one()
                title_val = await _resolve_session_display_title(
                    session_title=sess_row.title,
                    agent_name_snapshot=sess_row.agent_name_snapshot,
                    user_query=query,
                    conversation_id=conv_id,
                    api_server=api_server,
                    app_key=app_key,
                    dify_user=dify_user,
                    topic_just_finished=topic_finished,
                    blocking_response=None,
                )
                is_closed = bool(sess_row.is_topic_closed or topic_finished)
                await stream_db.execute(
                    update(models.VadminChatSession)
                    .where(models.VadminChatSession.id == session_id_val)
                    .values(
                        dify_conversation_id=conv_id,
                        last_message_preview=_preview(answer),
                        is_topic_closed=is_closed,
                        title=title_val,
                    )
                )
                bot_msg = models.VadminChatMessage(
                    session_id=session_id_val,
                    role="assistant",
                    content=answer,
                )
                stream_db.add(bot_msg)
        meta = {"event": "mp_topic", "topic_closed": topic_finished}
        yield (f"data: {json.dumps(meta, ensure_ascii=False)}\n\n").encode("utf-8")
