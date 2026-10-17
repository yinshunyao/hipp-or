#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2022/8/8 11:02
# @File           : auth_util.py
# @IDE            : PyCharm
# @desc           : 简要说明

from datetime import datetime, timedelta

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from application import settings
from application.settings import DEFAULT_AUTH_ERROR_MAX_NUMBER, DEMO, REDIS_DB_ENABLE
from apps.vadmin.auth import crud, models, schemas
from core.database import redis_getter
from utils.count import Count
from utils.sms.code import CodeSMS
from .validation import LoginValidation, LoginForm, LoginResult


class LoginManage:
    """
    登录认证工具
    """

    @LoginValidation
    async def password_login(self, data: LoginForm, user: models.VadminUser, **kwargs) -> LoginResult:
        """
        验证用户密码。platform=1 且配置了 HIPP_MANAGER_BASE 时，口令以 manager 为准。
        platform=0（管理端）：优先校验 hipp-manager 平台管理员，失败再回落本地口令。
        """
        from utils import hipp_manager

        if getattr(data, "platform", "0") == "1" and hipp_manager.enabled():
            try:
                profile = hipp_manager.password_login(data.telephone, data.password)
            except hipp_manager.ManagerError as e:
                return LoginResult(status=False, msg=str(e) or "账号或密码错误")
            access = str(profile.get("token") or profile.get("access_token") or "").strip()
            if not access:
                return LoginResult(status=False, msg="用户系统登录失败")
            return LoginResult(status=True, msg="验证成功", manager_token=access)

        # 管理端：平台管理员（须本地仍有 is_staff 账号，用户名与 ops 一致）
        if getattr(data, "platform", "0") == "0" and hipp_manager.enabled():
            try:
                ops = hipp_manager.ops_login(data.telephone, data.password)
                ops_tok = str(ops.get("token") or ops.get("access_token") or "").strip()
                if ops_tok:
                    return LoginResult(status=True, msg="验证成功", manager_token=ops_tok)
            except hipp_manager.ManagerError:
                pass

        result = models.VadminUser.verify_password(data.password, user.password)
        if not result:
            return LoginResult(status=False, msg="账号或密码错误")
        # 配置了 manager 时：Web/管理端登录必须拿到 manager 令牌（在线权威）
        manager_token = None
        if hipp_manager.enabled():
            try:
                profile = hipp_manager.password_login(data.telephone, data.password)
                manager_token = str(profile.get("token") or profile.get("access_token") or "").strip() or None
            except hipp_manager.ManagerError as e:
                return LoginResult(status=False, msg=str(e) or "用户系统登录失败")
            if not manager_token:
                return LoginResult(status=False, msg="用户系统登录失败")
        return LoginResult(status=True, msg="验证成功", manager_token=manager_token)

    @LoginValidation
    async def sms_login(self, data: LoginForm, request: Request, **kwargs) -> LoginResult:
        """
        验证用户短信验证码
        """
        from utils import hipp_manager

        if hipp_manager.enabled():
            try:
                profile = hipp_manager.sms_login(data.telephone, data.password)
            except hipp_manager.ManagerError as e:
                return LoginResult(status=False, msg=str(e) or "验证码错误")
            access = str(profile.get("token") or profile.get("access_token") or "").strip()
            if not access:
                return LoginResult(status=False, msg="用户系统登录失败")
            return LoginResult(status=True, msg="验证成功", manager_token=access)
        rd = redis_getter(request)
        sms = CodeSMS(data.telephone, rd)
        result = await sms.check_sms_code(data.password)
        if result:
            return LoginResult(status=True, msg="验证成功")
        return LoginResult(status=False, msg="验证码错误")

    async def mp_sms_login_with_register(
        self, data: LoginForm, db: AsyncSession, request: Request
    ) -> LoginResult:
        """
        小程序（platform=1）短信登录：先验码（优先 hipp-manager），通过后再查库；无用户则自动注册。
        """
        from utils import hipp_manager

        manager_token = None
        if hipp_manager.enabled():
            try:
                profile = hipp_manager.sms_login(data.telephone, data.password)
            except hipp_manager.ManagerError as e:
                return LoginResult(status=False, msg=str(e) or "验证码错误")
            manager_token = str(profile.get("token") or profile.get("access_token") or "").strip() or None
            if not manager_token:
                return LoginResult(status=False, msg="用户系统登录失败")
        else:
            rd = redis_getter(request)
            sms = CodeSMS(data.telephone, rd)
            ok = await sms.check_sms_code(data.password)
            if not ok:
                user_existing = await crud.UserDal(db).get_user_for_login(data.telephone, "1")
                if user_existing and REDIS_DB_ENABLE and not DEMO:
                    count = Count(redis_getter(request), f"{data.telephone}_sms_auth")
                    number = await count.add(ex=86400)
                    if number >= DEFAULT_AUTH_ERROR_MAX_NUMBER:
                        await count.reset()
                        user_existing.is_active = False
                        await db.flush()
                return LoginResult(status=False, msg="验证码错误")

        dal = crud.UserDal(db)
        user = await dal.get_data(telephone=data.telephone, v_return_none=True)
        if not user:
            user = await dal.create_user_for_mp_sms_register(data.telephone)

        if getattr(user, "is_blocked", False):
            return LoginResult(status=False, msg="此账号已被拉黑")
        if not user.is_active:
            return LoginResult(status=False, msg="此账号已被冻结！")
        if not user.is_staff:
            return LoginResult(status=False, msg="此账号无权限！")

        if REDIS_DB_ENABLE and not DEMO:
            count = Count(redis_getter(request), f"{data.telephone}_sms_auth")
            await count.delete()

        await dal.update_login_info(user, request.client.host)
        await db.refresh(user)
        return LoginResult(
            status=True,
            msg="OK",
            user=schemas.UserPasswordOut.model_validate(user),
            manager_token=manager_token,
        )

    @staticmethod
    def create_token(payload: dict, expires: timedelta = None):
        """
        创建一个生成新的访问令牌的工具函数。

        pyjwt：https://github.com/jpadilla/pyjwt/blob/master/docs/usage.rst
        jwt 博客：https://geek-docs.com/python/python-tutorial/j_python-jwt.html

        #TODO 传入的时间为UTC时间datetime.datetime类型，但是在解码时获取到的是本机时间的时间戳
        """
        if expires:
            expire = datetime.utcnow() + expires
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload.update({"exp": expire})
        encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
