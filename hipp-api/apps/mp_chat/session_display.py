# -*- coding: utf-8 -*-
"""小程序会话 C 端展示标题（与 ORM 解耦，供单元测试直接引用）。"""


def mp_ui_session_title(session, agent) -> str:
    """
    若用户曾自定义标题（与创建时 agent_name_snapshot 不一致），保留 session.title；
    否则优先使用当前智能体名称（agent.name），以便管理端改智能体资料后展示即时更新。
    """
    snap = (getattr(session, "agent_name_snapshot", None) or "").strip()
    title = (getattr(session, "title", None) or "").strip()
    if snap and title != snap:
        return session.title
    if agent is not None:
        name = (getattr(agent, "name", None) or "").strip()
        if name:
            return name
    return session.title
