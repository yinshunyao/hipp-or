# -*- coding: utf-8 -*-
"""对话附件校验与预览（与 Dify file_upload 限额取更严）。"""

from __future__ import annotations

import json
import os
from typing import Any

from core.exception import CustomException
from utils import status

# 产品：单次合计 < 20MB；单图/单文档对齐 Dify 默认导出
MAX_TOTAL_BYTES = 20 * 1024 * 1024 - 1
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_BYTES = 15 * 1024 * 1024
MAX_AUDIO_STT_BYTES = 15 * 1024 * 1024
MAX_FILE_COUNT = 3

QUERY_PLACEHOLDER = "请结合附件内容回答"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
DOCUMENT_EXTS = {
    ".pdf",
    ".txt",
    ".md",
    ".markdown",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".html",
    ".htm",
}
AUDIO_STT_EXTS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

IMAGE_MIMES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}
DOCUMENT_MIMES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/html",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}
AUDIO_STT_MIMES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "video/mp4",
    "video/webm",
}


def use_dify_local_file() -> bool:
    raw = (os.environ.get("HIPP_OR_DIFY_CHAT_LOCAL_FILE") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _ext(filename: str | None) -> str:
    name = (filename or "").strip().lower()
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1]


def classify_chat_file(filename: str | None, mime: str | None) -> str:
    """返回 dify type: image | document；否则抛错。"""
    ext = _ext(filename)
    ct = (mime or "").strip().lower()
    if ext in IMAGE_EXTS or ct in IMAGE_MIMES:
        return "image"
    if ext in DOCUMENT_EXTS:
        return "document"
    if ct in DOCUMENT_MIMES and ct != "application/octet-stream":
        return "document"
    raise CustomException("不支持的附件类型，请上传图片或常见文档", code=status.HTTP_ERROR)


def max_bytes_for_type(file_type: str) -> int:
    if file_type == "image":
        return MAX_IMAGE_BYTES
    if file_type == "document":
        return MAX_DOCUMENT_BYTES
    raise CustomException("不支持的附件类型", code=status.HTTP_ERROR)


def assert_upload_size(file_type: str, size: int) -> None:
    limit = max_bytes_for_type(file_type)
    if size <= 0:
        raise CustomException("文件为空", code=status.HTTP_ERROR)
    if size > limit:
        mb = limit / 1024 / 1024
        raise CustomException(f"文件过大，{file_type} 不能超过 {mb:g}MB", code=status.HTTP_ERROR)


def normalize_attachment_dicts(raw: list[Any] | None) -> list[dict]:
    if not raw:
        return []
    if len(raw) > MAX_FILE_COUNT:
        raise CustomException(f"单次最多上传 {MAX_FILE_COUNT} 个附件", code=status.HTTP_ERROR)
    out: list[dict] = []
    total = 0
    for item in raw:
        if hasattr(item, "model_dump"):
            d = item.model_dump()
        elif isinstance(item, dict):
            d = dict(item)
        else:
            raise CustomException("附件格式错误", code=status.HTTP_ERROR)
        ftype = str(d.get("type") or "").strip()
        url = str(d.get("url") or "").strip()
        name = str(d.get("name") or "file").strip() or "file"
        mime = str(d.get("mime") or "").strip()
        try:
            size = int(d.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        if ftype not in ("image", "document"):
            raise CustomException("附件 type 仅支持 image / document", code=status.HTTP_ERROR)
        if not url.startswith(("http://", "https://")):
            raise CustomException("附件地址无效", code=status.HTTP_ERROR)
        assert_upload_size(ftype, size)
        total += size
        if total > MAX_TOTAL_BYTES:
            raise CustomException("附件总体积须小于 20MB", code=status.HTTP_ERROR)
        out.append({"type": ftype, "name": name, "size": size, "mime": mime, "url": url})
    return out


def dumps_attachments(items: list[dict] | None) -> str | None:
    if not items:
        return None
    return json.dumps(items, ensure_ascii=False)


def loads_attachments(raw: str | list | None) -> list[dict] | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, list):
        return raw or None
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, list) and data else None
    return None


def resolve_query_and_store(query: str | None, attachments: list[dict] | None) -> tuple[str, str]:
    """
    返回 (dify_query, store_content)。
    有附件且文本为空时，Dify 用占位句；落库 content 用占位句便于列表预览与重试。
    """
    text = (query or "").strip()
    has_files = bool(attachments)
    if not text and not has_files:
        raise CustomException("请输入内容或添加附件", code=status.HTTP_ERROR)
    if not text and has_files:
        return QUERY_PLACEHOLDER, QUERY_PLACEHOLDER
    return text, text


def preview_for_user(content: str, attachments: list[dict] | None) -> str:
    parts: list[str] = []
    for a in attachments or []:
        if a.get("type") == "image":
            parts.append("[图片]")
        else:
            name = str(a.get("name") or "文件")
            parts.append(f"[文件] {name}")
    text = (content or "").strip().replace("\n", " ")
    if text and text != QUERY_PLACEHOLDER:
        parts.append(text)
    joined = " ".join(parts).strip() or text or "[附件]"
    if len(joined) <= 80:
        return joined
    return joined[:79] + "…"


def to_dify_remote_files(attachments: list[dict] | None) -> list[dict]:
    files = []
    for a in attachments or []:
        files.append(
            {
                "type": a["type"],
                "transfer_method": "remote_url",
                "url": a["url"],
            }
        )
    return files


def is_audio_stt_file(filename: str | None, mime: str | None) -> bool:
    ext = _ext(filename)
    ct = (mime or "").strip().lower()
    return ext in AUDIO_STT_EXTS or ct in AUDIO_STT_MIMES
