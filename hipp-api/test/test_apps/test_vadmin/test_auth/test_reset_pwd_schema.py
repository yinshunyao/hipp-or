from pydantic import ValidationError

from apps.vadmin.auth.schemas.user import ResetPwd


def test_reset_pwd_old_password_optional_for_first_time_flow():
    data = ResetPwd(password="new-password-123", password_two="new-password-123")
    assert data.old_password is None


def test_reset_pwd_password_two_must_match():
    try:
        ResetPwd(old_password="old-password-123", password="new-password-123", password_two="different-password")
        assert False, "password_two should match password"
    except ValidationError as exc:
        assert "两次密码不一致" in str(exc)


def test_reset_pwd_valid_payload_with_old():
    data = ResetPwd(
        old_password="old-password-123",
        password="new-password-123",
        password_two="new-password-123",
    )
    assert data.old_password == "old-password-123"
