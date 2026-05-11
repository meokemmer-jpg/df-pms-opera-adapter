"""Tests fuer OperaConnector [CRUX-MK]."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.opera_adapter import OperaConnector, AdapterResponse, PMSAdapter


class TestOperaConnectorSandbox:

    def test_connector_initializes_in_sandbox_by_default(self):
        c = OperaConnector()
        assert c.sandbox_mode is True
        assert c.adapter_name == "opera-pms"

    def test_connect_sandbox(self):
        c = OperaConnector(sandbox_mode=True)
        result = c.connect({"access_token": "mock-token"})
        assert result is True
        assert c._connected is True
        assert c._access_token == "mock-token"

    def test_query_inventory_sandbox(self):
        c = OperaConnector(sandbox_mode=True)
        c.connect({})
        inv = c.query_inventory("hildesheim", ("2026-06-01", "2026-06-02"))
        assert isinstance(inv, list)
        assert len(inv) == 3  # premium_standard + premium_suite + presidential_suite
        for room in inv:
            assert "hotel_id" in room
            assert "segment" in room
            assert room["segment"] == "premium"
            assert "room_type" in room
            assert "rate_eur" in room

    def test_query_inventory_unknown_hotel(self):
        c = OperaConnector(sandbox_mode=True)
        c.connect({})
        inv = c.query_inventory("unknown", ("2026-06-01", "2026-06-02"))
        assert inv == []

    def test_book_room_sandbox(self):
        c = OperaConnector(sandbox_mode=True)
        c.connect({})
        bid = c.book_room("hildesheim", "premium_suite", {"name": "Test"}, ("2026-06-01", "2026-06-03"))
        assert bid.startswith("opera-mock-")

    def test_cancel_booking_sandbox(self):
        c = OperaConnector(sandbox_mode=True)
        c.connect({})
        assert c.cancel_booking("opera-mock-12345678") is True
        assert c.cancel_booking("fail-mock-12345678") is False

    def test_get_capabilities(self):
        c = OperaConnector(sandbox_mode=True)
        caps = c.get_capabilities()
        assert caps["adapter_name"] == "opera-pms"
        assert caps["segment"] == "premium"
        assert caps["api_protocol"] == "OXI"
        assert caps["feature_flags"]["oauth2_bearer"] is True


class TestOperaConnectorRealMode:

    def test_connect_real_mode_without_credentials_fails(self, monkeypatch):
        monkeypatch.setenv("DF_PMS_OPERA_REAL_ENABLED", "true")
        c = OperaConnector()
        result = c.connect({})
        assert result is False

    def test_connect_real_mode_without_bearer_token_fails(self, monkeypatch):
        monkeypatch.setenv("DF_PMS_OPERA_REAL_ENABLED", "true")
        c = OperaConnector(sandbox_mode=False)
        result = c.connect({
            "client_id": "cid",
            "client_secret": "secret",
            "token_url": "http://example.com/oauth",
            "hotel_id": "H1",
            "access_token": "",  # leer
        })
        assert result is False

    def test_book_room_real_mode_without_phronesis_fails(self, monkeypatch):
        monkeypatch.setenv("DF_PMS_OPERA_REAL_ENABLED", "true")
        monkeypatch.delenv("DF_PMS_OPERA_PHRONESIS_TICKET", raising=False)
        c = OperaConnector(sandbox_mode=False)
        c._connected = True
        bid = c.book_room("hildesheim", "premium_suite", {}, ("2026-06-01", "2026-06-03"))
        assert bid == ""


class TestPMSAdapterInterface:

    def test_opera_implements_pms_adapter(self):
        c = OperaConnector(sandbox_mode=True)
        assert isinstance(c, PMSAdapter)
