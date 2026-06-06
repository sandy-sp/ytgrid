import pytest
from fastapi import HTTPException

from ytgrid.backend import auth


async def test_auth_disabled_when_no_key(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "")
    assert await auth.verify_api_key(header_key=None, query_key=None) is None


async def test_auth_missing_key_rejected(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "secret")
    with pytest.raises(HTTPException) as exc:
        await auth.verify_api_key(header_key=None, query_key=None)
    assert exc.value.status_code == 401


async def test_auth_bad_key_rejected(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "secret")
    with pytest.raises(HTTPException) as exc:
        await auth.verify_api_key(header_key="wrong", query_key=None)
    assert exc.value.status_code == 401


async def test_auth_valid_header_key(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "secret")
    assert await auth.verify_api_key(header_key="secret", query_key=None) == "secret"


async def test_auth_valid_query_key(monkeypatch):
    monkeypatch.setattr(auth.config, "API_KEY", "secret")
    assert await auth.verify_api_key(header_key=None, query_key="secret") == "secret"
