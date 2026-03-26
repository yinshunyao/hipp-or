from pydantic import ValidationError

from apps.vadmin.auth.schemas.user import ResetPwd


def test_reset_pwd_requires_old_password():
    try:
        ResetPwd(password="new-password-123", password_two="new-password-123")
        assert False, "old_password should be required"
    except ValidationError as exc:
        assert "old_password" in str(exc)


def test_reset_pwd_password_two_must_match():
    try:
        ResetPwd(old_password="old-password-123", password="new-password-123", password_two="different-password")
        assert False, "password_two should match password"
    except ValidationError as exc:
        assert "两次密码不一致" in str(exc)


def test_reset_pwd_valid_payload():
    data = ResetPwd(
        old_password="old-password-123",
        password="new-password-123",
        password_two="new-password-123",
    )
    assert data.old_password == "old-password-123"
