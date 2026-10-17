# -*- coding: utf-8 -*-
"""mp_chat 业务错误码与默认提示（前后端约定；变更须同步设计码表与前端）。"""

from __future__ import annotations

# 智能体不可发送（下架/删除）
AGENT_UNAVAILABLE_CODE = 46001
AGENT_UNAVAILABLE_MSG = "智能体已下架或删除，暂不支持继续对话"

# 话题已结束，当前会话不可再发
TOPIC_CLOSED_CODE = 46002
TOPIC_CLOSED_MSG = "话题已结束，请开启新话题后再发送"

# 场景暂无可用智能体
SCENE_AGENT_UNAVAILABLE_CODE = 46003
SCENE_AGENT_UNAVAILABLE_MSG = "当前场景暂不可用"

# 游客免费体验次数用尽
MP_GUEST_TRIAL_EXHAUSTED_CODE = 46004
MP_GUEST_TRIAL_EXHAUSTED_MSG = (
    "本场景免费体验次数已用完。请打开底部「我的」Tab，进入登录页完成登录后再继续使用。"
)

# 余额不足以支付本话题咨询费
BALANCE_INSUFFICIENT_CODE = 46005
BALANCE_INSUFFICIENT_MSG = "余额不足，请先前往账户充值后再发起咨询"

# 发消息前无法完成扣费预检（未绑手机、manager 余额查询失败等）
SESSION_FEE_CHECK_FAILED_CODE = 46006
SESSION_FEE_CHECK_FAILED_MSG = "无法校验余额，请稍后重试"
SESSION_FEE_NO_PHONE_MSG = "账号未绑定手机号，无法扣费，请先完成登录绑定"

# 兼容旧名：历史上费用相关失败曾统一为 46005
SESSION_FEE_FAILED_CODE = BALANCE_INSUFFICIENT_CODE
