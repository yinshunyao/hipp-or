# -*- coding: utf-8 -*-
import pytest

from application import database_url as du


def test_get_url_direct(monkeypatch):
    monkeypatch.setenv("HIPP_DATABASE_URL", "mysql+pymysql://u:p@h:3306/db")
    monkeypatch.delenv("HIPP_DATABASE_HOST", raising=False)
    assert du.get_database_url_raw() == "mysql+pymysql://u:p@h:3306/db"


def test_compose_password_with_at(monkeypatch):
    monkeypatch.delenv("HIPP_DATABASE_URL", raising=False)
    monkeypatch.setenv("HIPP_DATABASE_HOST", "8.137.33.38")
    monkeypatch.setenv("HIPP_DATABASE_PORT", "33306")
    monkeypatch.setenv("HIPP_DATABASE_NAME", "hipp")
    monkeypatch.setenv("HIPP_DATABASE_USER", "root")
    monkeypatch.setenv("HIPP_DATABASE_PASSWORD", "Luoaiai@")
    raw = du.get_database_url_raw()
    assert raw.startswith("mysql+pymysql://")
    assert "8.137.33.38:33306/hipp" in raw
    from sqlalchemy.engine.url import make_url

    u = make_url(du.resolve_sqlalchemy_async_url())
    assert u.username == "root"
    assert u.password == "Luoaiai@"


def test_compose_missing_returns_error(monkeypatch):
    monkeypatch.delenv("HIPP_DATABASE_URL", raising=False)
    monkeypatch.delenv("HIPP_DATABASE_HOST", raising=False)
    with pytest.raises(RuntimeError, match="未配置数据库"):
        du.get_database_url_raw()
