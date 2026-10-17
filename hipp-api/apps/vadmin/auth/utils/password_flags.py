# -*- coding: utf-8 -*-
"""登录态与改密页：是否允许无「当前密码」首次设密（短信自助建号）。"""


def user_must_set_password_without_old(user) -> bool:
    """
    与 ORM / Pydantic 用户对象均可配合 getattr 使用。
    - 新库：must_set_password_without_old 由短信建号写入。
    - 兼容迁移前数据：短信自助用户 is_system_created=False、未设密、非微信来源。
    """
    if getattr(user, "must_set_password_without_old", False):
        return True
    if getattr(user, "is_system_created", True):
        return False
    if getattr(user, "is_reset_password", False):
        return False
    if getattr(user, "user_type", None) == "wechat":
        return False
    return True
