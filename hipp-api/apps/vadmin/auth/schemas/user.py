#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import annotations

# @version        : 1.0
# @Create Time    : 2021/10/18 22:19
# @File           : user.py
# @IDE            : PyCharm
# @desc           : pydantic 模型，用于数据库序列化操作


from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from core.data_types import Telephone, DatetimeStr, Email
from .role import RoleSimpleOut
from .dept import DeptSimpleOut


class User(BaseModel):
    name: str
    telephone: Telephone
    email: Email | None = None
    nickname: str | None = None
    avatar: str | None = None
    is_active: bool | None = True
    is_staff: bool | None = True
    gender: str | None = "0"
    is_wx_server_openid: bool | None = False
    user_type: str | None = "system"
    wx_nickname: str | None = None
    wx_avatar: str | None = None


class UserIn(User):
    """
    创建用户
    """
    role_ids: list[int] = []
    dept_ids: list[int] = []
    password: str | None = ""


class UserUpdateBaseInfo(BaseModel):
    """
    更新用户基本信息
    """
    name: str
    telephone: Telephone
    email: Email | None = None
    nickname: str | None = None
    gender: str | None = "0"


class UserUpdate(User):
    """
    更新用户详细信息
    """
    name: str | None = None
    telephone: Telephone
    email: Email | None = None
    nickname: str | None = None
    avatar: str | None = None
    is_active: bool | None = True
    is_staff: bool | None = False
    gender: str | None = "0"
    role_ids: list[int] = []
    dept_ids: list[int] = []


class UserSimpleOut(User):
    model_config = ConfigDict(from_attributes=True)

    id: int
    update_datetime: DatetimeStr
    create_datetime: DatetimeStr

    is_system_created: bool = True
    is_blocked: bool = False
    is_reset_password: bool | None = None
    last_login: DatetimeStr | None = None
    last_ip: str | None = None


class UserPasswordOut(UserSimpleOut):
    model_config = ConfigDict(from_attributes=True)

    password: str


def compute_user_tags(user: object) -> list[str]:
    """后台展示用多标签：系统创建 / 微信用户（与 OR 一致，不替代角色权限）。"""
    tags: list[str] = []
    if getattr(user, "is_system_created", True):
        tags.append("系统创建")
    ut = getattr(user, "user_type", None)
    if ut == "wechat" or getattr(user, "wx_nickname", None) or getattr(user, "wx_avatar", None):
        tags.append("微信用户")
    return tags


class UserBlockedIn(BaseModel):
    is_blocked: bool


class UserOut(UserSimpleOut):
    model_config = ConfigDict(from_attributes=True)

    roles: list[RoleSimpleOut] = []
    depts: list[DeptSimpleOut] = []
    user_tags: list[str] = Field(default_factory=list)


class ResetPwd(BaseModel):
    old_password: str
    password: str
    password_two: str

    @field_validator('password_two')
    def check_passwords_match(cls, v, info: FieldValidationInfo):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('两次密码不一致!')
        return v
