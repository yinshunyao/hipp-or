# -*- coding: utf-8 -*-
"""小红书开放平台订单回调 Adapter（履约出短链 + 可选发货回写）。"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from application import settings
from apps.commerce import service as commerce


CHANNEL = "xhs"


def _app_secret() -> str:
    return (getattr(settings, "XHS_APP_SECRET", None) or "").strip()


def _skip_sign() -> bool:
    return bool(getattr(settings, "XHS_SKIP_SIGN", False))


def verify_sign(raw_body: bytes, signature: str | None) -> bool:
    if _skip_sign():
        return True
    secret = _app_secret()
    if not secret:
        # 未配置密钥时拒绝（联调请显式 HIPP_XHS_SKIP_SIGN=1）
        return False
    sig = (signature or "").strip()
    if not sig:
        return False
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, sig) or hmac.compare_digest(digest, sig.lower())


def _parse_events(payload: Any) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, dict) and payload.get("test") is True:
        return [{"_test": True}]
    items: list[Any]
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = [payload]
    else:
        return []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        data = it.get("data")
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {"raw": data}
        elif data is None:
            data = it
        if not isinstance(data, dict):
            data = {"raw": data}
        out.append(
            {
                "msg_tag": str(it.get("msgTag") or it.get("msg_tag") or ""),
                "seller_id": str(it.get("sellerId") or it.get("seller_id") or ""),
                "data": data,
                "raw": it,
            }
        )
    return out


def _extract_order_id(data: dict) -> str:
    for key in (
        "orderId",
        "order_id",
        "packageId",
        "package_id",
        "fulfillmentOrderId",
        "order_id_str",
    ):
        v = data.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    # 嵌套
    for nest in ("order", "package", "data"):
        nested = data.get(nest)
        if isinstance(nested, dict):
            found = _extract_order_id(nested)
            if found:
                return found
    return ""


def _is_refund_like(msg_tag: str, data: dict) -> bool:
    tag = (msg_tag or "").lower()
    if "refund" in tag or "after_sale" in tag or "aftersale" in tag:
        return True
    status = str(data.get("orderStatus") or data.get("status") or data.get("fulfillmentStatus") or "")
    if status in ("7", "closed", "refund", "REFUND", "取消", "关闭"):
        return True
    return False


def _is_fulfillable(msg_tag: str, data: dict) -> bool:
    if _is_refund_like(msg_tag, data):
        return False
    # 宽松：有订单号且非退款即尝试履约（幂等）
    return bool(_extract_order_id(data))


async def _try_deliver(short_url: str, order_id: str) -> tuple[bool, str]:
    url = (getattr(settings, "XHS_DELIVER_URL", None) or "").strip()
    if not url:
        return True, json.dumps(
            {"mode": "store_only", "short_url": short_url, "order_id": order_id},
            ensure_ascii=False,
        )
    body = {
        "order_id": order_id,
        "short_url": short_url,
        "content": f"请打开链接完成需求分析：{short_url}",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body)
        ok = 200 <= resp.status_code < 300
        return ok, (resp.text or "")[:2000]
    except Exception as exc:
        return False, str(exc)[:2000]


async def handle_notify(db: AsyncSession, payload: Any) -> dict:
    events = _parse_events(payload)
    if len(events) == 1 and events[0].get("_test"):
        return {"ok": True, "test": True}
    results = []
    for ev in events:
        data = ev.get("data") or {}
        msg_tag = ev.get("msg_tag") or ""
        order_id = _extract_order_id(data)
        if not order_id:
            results.append({"skipped": True, "reason": "no_order_id", "msg_tag": msg_tag})
            continue
        raw = commerce.dump_json(ev.get("raw") or ev)
        if _is_refund_like(msg_tag, data):
            voided = await commerce.void_by_channel_order(db, CHANNEL, order_id)
            results.append({"order_id": order_id, "action": "void", "voided": voided})
            continue
        if not _is_fulfillable(msg_tag, data):
            results.append({"order_id": order_id, "skipped": True, "reason": "not_fulfillable"})
            continue
        order, ent = await commerce.fulfill_channel_order(
            db,
            channel=CHANNEL,
            external_order_id=order_id,
            sku_code=str(data.get("skuId") or data.get("sku_id") or "") or None,
            raw_event=raw,
            remark="xhs_notify",
        )
        url = order.short_url or commerce.short_url_for(ent.token)
        ok, payload_text = await _try_deliver(url, order_id)
        await commerce.mark_order_delivered(db, order, deliver_ok=ok, payload=payload_text)
        results.append(
            {
                "order_id": order_id,
                "action": "fulfill",
                "token": ent.token,
                "short_url": url,
                "deliver_ok": ok,
            }
        )
    return {"ok": True, "results": results}
