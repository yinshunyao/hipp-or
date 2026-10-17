# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2021/10/19 15:47
# @File           : urls.py
# @IDE            : PyCharm
# @desc           : 路由文件

from apps.vadmin.auth.utils.login import app as auth_app
from apps.vadmin.auth.views import app as vadmin_auth_app
from apps.vadmin.system.views import app as vadmin_system_app
from apps.vadmin.record.views import app as vadmin_record_app
from apps.vadmin.workplace.views import app as vadmin_workplace_app
from apps.vadmin.analysis.views import app as vadmin_analysis_app
from apps.vadmin.help.views import app as vadmin_help_app
from apps.vadmin.resource.views import app as vadmin_resource_app
from apps.vadmin.agent_manager.views import app as vadmin_agent_app
from apps.mp_chat.views import app as mp_chat_app
from apps.wallet.views import app as wallet_app
from apps.vadmin.billing.views import app as billing_app
from apps.commerce.views import app as commerce_app
from apps.commerce.views import admin_app as commerce_admin_app


# 引入应用中的路由
urlpatterns = [
    {"ApiRouter": auth_app, "prefix": "/auth", "tags": ["系统认证"]},
    {"ApiRouter": vadmin_auth_app, "prefix": "/vadmin/auth", "tags": ["权限管理"]},
    {"ApiRouter": vadmin_system_app, "prefix": "/vadmin/system", "tags": ["系统管理"]},
    {"ApiRouter": vadmin_record_app, "prefix": "/vadmin/record", "tags": ["记录管理"]},
    {"ApiRouter": vadmin_workplace_app, "prefix": "/vadmin/workplace", "tags": ["工作区管理"]},
    {"ApiRouter": vadmin_analysis_app, "prefix": "/vadmin/analysis", "tags": ["数据分析管理"]},
    {"ApiRouter": vadmin_help_app, "prefix": "/vadmin/help", "tags": ["帮助中心管理"]},
    {"ApiRouter": vadmin_resource_app, "prefix": "/vadmin/resource", "tags": ["资源管理"]},
    {"ApiRouter": vadmin_agent_app, "prefix": "/vadmin/agent", "tags": ["智能客服管理"]},
    {"ApiRouter": billing_app, "prefix": "/vadmin/billing", "tags": ["会话计费配置"]},
    {"ApiRouter": commerce_admin_app, "prefix": "/vadmin/commerce", "tags": ["电商次卡履约"]},
    {"ApiRouter": commerce_app, "prefix": "/commerce", "tags": ["电商短链核销"]},
    {"ApiRouter": mp_chat_app, "prefix": "/mp/chat", "tags": ["小程序对话"]},
    {"ApiRouter": wallet_app, "prefix": "/wallet", "tags": ["个人资金账户"]},
]
