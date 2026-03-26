# -*- coding: utf-8 -*-
"""调用 Dify Chat 应用 chat-messages 接口（blocking / streaming）。"""

import json
import re
from collections.abc import AsyncIterator

import httpx

from core.exception import CustomException

_FINISH_STATUS_RE = re.compile(r"^结束状态\s*[:：]?\s*(true|false)\s*$", re.IGNORECASE)


def parse_topic_finished_from_raw_answer(raw: str) -> bool:
    """根据助手完整原文首行判断是否「结束状态 True」（归档条件之一）。"""
    lines = (raw or "").splitlines()
    if not lines:
        return False
    m = _FINISH_STATUS_RE.match(lines[0].strip())
    if not m:
        return False
    return m.group(1).lower() == "true"


def strip_finish_status_prefix(text: str) -> str:
    """去除回答首行的结束状态标记，避免混入用户可见正文。"""
    lines = (text or "").splitlines()
    if not lines:
        return text
    if _FINISH_STATUS_RE.match(lines[0].strip()):
        return "\n".join(lines[1:]).lstrip()
    return text


class StreamAnswerPrefixFilter:
    """
    流式 answer 增量过滤器：
    - 若首行是「结束状态 True/False（兼容 : / ：）」则仅过滤该首行；
    - 为避免误判，仅在能够确认首行后再输出首批内容。
    """

    _MAX_PENDING_NO_NEWLINE = 64

    def __init__(self) -> None:
        self._decided = False
        self._pending = ""

    def feed(self, chunk: str) -> str:
        if self._decided:
            return chunk
        if not chunk:
            return ""
        self._pending += chunk

        normalized = self._pending.replace("\r\n", "\n")
        has_newline = "\n" in normalized
        if not has_newline:
            # 首行尚未结束：若明显不是状态行则立即放行，避免阻塞正常首包显示。
            if not normalized.lstrip().startswith("结束状态"):
                self._decided = True
                out = normalized
                self._pending = ""
                return out
            if len(normalized) < self._MAX_PENDING_NO_NEWLINE:
                return ""

        self._decided = True
        if has_newline:
            first_line, rest = normalized.split("\n", 1)
            if _FINISH_STATUS_RE.match(first_line.strip()):
                self._pending = ""
                return rest.lstrip()
        out = normalized
        self._pending = ""
        return out

    def flush(self) -> str:
        if self._decided:
            return ""
        self._decided = True
        out = self._pending
        self._pending = ""
        return out


class DifyStreamAccumulator:
    """解析 Dify `text/event-stream` 行，累积回答与 conversation_id，识别 error 事件。"""

    def __init__(self) -> None:
        self.full_answer: str = ""
        self.conversation_id: str | None = None
        self.error: str | None = None

    def feed_line(self, line: str) -> None:
        s = line.strip("\r")
        if not s.startswith("data:"):
            return
        raw = s[5:].strip()
        if raw == "[DONE]":
            return
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return
        if not isinstance(obj, dict):
            return
        ev = obj.get("event")
        cid = obj.get("conversation_id")
        if isinstance(cid, str) and cid:
            self.conversation_id = cid
        if ev in ("message", "agent_message"):
            ans = obj.get("answer")
            if isinstance(ans, str) and ans:
                self.full_answer += ans
        elif ev == "message_end":
            pass
        elif ev == "error":
            msg = obj.get("message")
            self.error = str(msg) if msg is not None else "Dify 流式错误"


def rewrite_sse_answer_line(line: str, answer_filter: StreamAnswerPrefixFilter) -> str | None:
    """
    重写单行 SSE 中 message/agent_message 的 answer 字段。
    返回 None 表示当前增量仅用于前缀判断，不向客户端发送该行。
    """
    s = line.strip("\r")
    if not s.startswith("data:"):
        return line
    raw = s[5:].strip()
    if raw == "[DONE]":
        tail = answer_filter.flush()
        if tail:
            obj = {"event": "message", "answer": tail}
            return f"data: {json.dumps(obj, ensure_ascii=False)}"
        return line
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return line
    if not isinstance(obj, dict):
        return line
    if obj.get("event") not in ("message", "agent_message"):
        return line
    ans = obj.get("answer")
    if not isinstance(ans, str):
        return line
    filtered = answer_filter.feed(ans)
    if filtered == "":
        return None
    obj["answer"] = filtered
    return f"data: {json.dumps(obj, ensure_ascii=False)}"


def _api_v1_base(api_server: str) -> str:
    """
    兼容两种输入，返回 .../v1 根路径（无尾部斜杠）：
    - http(s)://host     -> http(s)://host/v1
    - http(s)://host/v1  -> http(s)://host/v1
    """
    base = (api_server or "").strip().rstrip("/")
    if not base:
        raise CustomException("Dify API 服务器地址为空")
    if not base.startswith(("http://", "https://")):
        base = "http://" + base
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


def _chat_messages_url(api_server: str) -> str:
    """POST .../v1/chat-messages"""
    return f"{_api_v1_base(api_server)}/chat-messages"


def _norm_conversation_id(s: str | None) -> str:
    """比较 Dify 会话 id 时忽略大小写与连字符差异。"""
    if s is None:
        return ""
    return str(s).strip().lower().replace("-", "")


def extract_conversation_name_from_chat_response(data: dict | None) -> str | None:
    """
    从 POST /v1/chat-messages（blocking）响应中解析会话展示名。
    Dify 可能在顶层或嵌套对象中返回 `name`（与 GET /conversations 的 data[].name 同源语义）。
    """
    if not isinstance(data, dict):
        return None
    n = data.get("name")
    if isinstance(n, str) and n.strip():
        return n.strip()[:255]
    conv = data.get("conversation")
    if isinstance(conv, dict):
        cn = conv.get("name")
        if isinstance(cn, str) and cn.strip():
            return cn.strip()[:255]
    meta = data.get("metadata")
    if isinstance(meta, dict):
        for key in ("conversation_name", "name", "title"):
            v = meta.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()[:255]
    return None


async def fetch_dify_conversation_name(
    api_server: str,
    app_key: str,
    conversation_id: str,
    dify_user: str,
    *,
    max_pages: int = 15,
    page_limit: int = 100,
) -> str | None:
    """
    调用 Dify GET /v1/conversations，按 user 分页查找 conversation_id 对应的会话名称（name）。
    见官方文档「获取会话列表」：data[].id、data[].name。
    请求失败或未找到时返回 None，不抛异常，由业务层回退标题策略。
    """
    if not (conversation_id or "").strip():
        return None
    url = f"{_api_v1_base(api_server)}/conversations"
    headers = {"Authorization": f"Bearer {app_key}"}
    last_id: str | None = None
    timeout = httpx.Timeout(60.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            for _ in range(max_pages):
                params: dict[str, str | int] = {
                    "user": dify_user,
                    "limit": page_limit,
                }
                if last_id:
                    params["last_id"] = last_id
                try:
                    resp = await client.get(url, headers=headers, params=params)
                except httpx.RequestError:
                    return None
                if resp.status_code >= 400:
                    return None
                try:
                    payload = resp.json()
                except ValueError:
                    return None
                if not isinstance(payload, dict):
                    return None
                rows = payload.get("data") or []
                for item in rows:
                    if not isinstance(item, dict):
                        continue
                    if _norm_conversation_id(item.get("id")) != _norm_conversation_id(conversation_id):
                        continue
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        return name.strip()[:255]
                    return None
                if not payload.get("has_more") or not rows:
                    break
                last_id = rows[-1].get("id")
                if not last_id:
                    break
    except Exception:
        return None
    return None


async def iter_dify_chat_stream(
    api_server: str,
    app_key: str,
    query: str,
    dify_user: str,
    conversation_id: str | None = None,
) -> AsyncIterator[str]:
    """
    POST {api_server}/v1/chat-messages，response_mode=streaming。
    逐行产出 Dify 返回的 SSE 文本行（不含换行符）。
    """
    url = _chat_messages_url(api_server)
    headers = {
        "Authorization": f"Bearer {app_key}",
        "Content-Type": "application/json",
    }
    body: dict = {
        "inputs": {},
        "query": query,
        "user": dify_user,
        "response_mode": "streaming",
    }
    if conversation_id:
        body["conversation_id"] = conversation_id

    timeout = httpx.Timeout(120.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                if resp.status_code >= 400:
                    err_text = (await resp.aread())[:500].decode("utf-8", errors="replace")
                    raise CustomException(f"Dify 请求失败: HTTP {resp.status_code} {err_text}")
                async for line in resp.aiter_lines():
                    yield line
        except httpx.HTTPStatusError as e:
            text = e.response.text[:500] if e.response is not None else ""
            raise CustomException(f"Dify 请求失败: HTTP {e.response.status_code} {text}")
        except httpx.RequestError as e:
            raise CustomException(f"无法连接 Dify: {e!s}")


async def send_chat_message_blocking(
    api_server: str,
    app_key: str,
    query: str,
    dify_user: str,
    conversation_id: str | None = None,
) -> dict:
    """
    POST {api_server}/v1/chat-messages
    返回解析后的 JSON dict，至少包含 answer、conversation_id（若 Dify 返回）。
    """
    url = _chat_messages_url(api_server)
    headers = {
        "Authorization": f"Bearer {app_key}",
        "Content-Type": "application/json",
    }
    body: dict = {
        "inputs": {},
        "query": query,
        "user": dify_user,
        "response_mode": "blocking",
    }
    if conversation_id:
        body["conversation_id"] = conversation_id

    timeout = httpx.Timeout(120.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            text = e.response.text[:500] if e.response is not None else ""
            raise CustomException(f"Dify 请求失败: HTTP {e.response.status_code} {text}")
        except httpx.RequestError as e:
            raise CustomException(f"无法连接 Dify: {e!s}")

    try:
        data = resp.json()
    except ValueError:
        raise CustomException("Dify 返回非 JSON 响应")

    return data
