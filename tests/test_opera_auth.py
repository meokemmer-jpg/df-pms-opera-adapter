"""Tests fuer OperaAuth [CRUX-MK]."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.opera_auth import OperaAuth, OperaCredentials


class TestOperaAuthSandbox:

    def test_auth_sandbox_returns_mock_credentials(self):
        auth = OperaAuth(sandbox_mode=True)
        creds = auth.get_credentials("hildesheim")
        assert creds is not None
        assert creds.client_id == OperaAuth.MOCK_CLIENT_ID
        assert creds.client_secret == OperaAuth.MOCK_CLIENT_SECRET
        assert creds.access_token == OperaAuth.MOCK_ACCESS_TOKEN
        assert creds.source == "mock"

    def test_validate_mock(self):
        auth = OperaAuth(sandbox_mode=True)
        creds = auth.get_credentials("hildesheim")
        assert auth.validate(creds) is True

    def test_validate_none(self):
        auth = OperaAuth(sandbox_mode=True)
        assert auth.validate(None) is False

    def test_default_sandbox(self, monkeypatch):
        monkeypatch.delenv("DF_PMS_OPERA_REAL_ENABLED", raising=False)
        auth = OperaAuth()
        assert auth.sandbox_mode is True


class TestOperaAuthRealMode:

    def test_real_mode_without_env_returns_none(self, monkeypatch):
        monkeypatch.setenv("DF_PMS_OPERA_REAL_ENABLED", "true")
        for v in ("OPERA_CLIENT_ID", "OPERA_CLIENT_SECRET", "OPERA_TOKEN_URL", "OPERA_HOTEL_ID"):
            monkeypatch.delenv(v, raising=False)
        auth = OperaAuth()
        assert auth.get_credentials("hildesheim") is None

    def test_real_mode_with_env_returns_creds_no_token(self, monkeypatch):
        # ohne tatsaechlichen Token-Service-Call: access_token bleibt leer im Placeholder
        monkeypatch.setenv("DF_PMS_OPERA_REAL_ENABLED", "true")
        monkeypatch.setenv("OPERA_CLIENT_ID", "cid")
        monkeypatch.setenv("OPERA_CLIENT_SECRET", "secret")
        monkeypatch.setenv("OPERA_TOKEN_URL", "http://example.com/oauth")
        monkeypatch.setenv("OPERA_HOTEL_ID", "H1")
        auth = OperaAuth()
        creds = auth.get_credentials("hildesheim")
        # Strukturell zurueck, aber token leer (placeholder)
        assert creds is not None
        assert creds.client_id == "cid"
        assert creds.source == "env"
        # Validate scheitert da access_token leer im Real-Mode
        assert auth.validate(creds) is False

    def test_is_real_mode(self, monkeypatch):
        monkeypatch.setenv("DF_PMS_OPERA_REAL_ENABLED", "true")
        auth = OperaAuth()
        assert auth.is_real_mode() is True
