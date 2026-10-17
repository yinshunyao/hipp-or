import pytest

from apps.vadmin.auth.utils.password_flags import user_must_set_password_without_old


class _U:
    pass


def _u(**kwargs):
    o = _U()
    for k, v in kwargs.items():
        setattr(o, k, v)
    return o


@pytest.mark.parametrize(
    "kw, expected",
    [
        ({"must_set_password_without_old": True}, True),
        ({"must_set_password_without_old": False, "is_system_created": True}, False),
        ({"must_set_password_without_old": False, "is_system_created": False, "is_reset_password": True, "user_type": "system"}, False),
        ({"must_set_password_without_old": False, "is_system_created": False, "is_reset_password": False, "user_type": "wechat"}, False),
        ({"must_set_password_without_old": False, "is_system_created": False, "is_reset_password": False, "user_type": "system"}, True),
    ],
)
def test_user_must_set_password_without_old(kw, expected):
    assert user_must_set_password_without_old(_u(**kw)) is expected
