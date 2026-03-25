# -*- coding: utf-8 -*-
"""归档话题上下文纯文本（无 ORM 依赖，便于单测）。"""


def format_archive_topic_context(
    *,
    source_session_id: int,
    display_title: str,
    messages: list[tuple[str, str]],
) -> str:
    """
    与小程序「归档话题」提示语义一致：结构化文本，首行标题，后续为对话摘录。
    messages: (role, content) 按 id 升序
    """
    lines = [
        f"【归档话题】{display_title}",
        f"来源会话 ID：{source_session_id}",
        "",
        "—— 以下为归档对话摘录 ——",
    ]
    for role, content in messages:
        label = "用户" if role == "user" else ("智能体" if role == "assistant" else role)
        text = (content or "").strip()
        if text:
            lines.append(f"{label}：{text}")
    return "\n".join(lines).strip()
