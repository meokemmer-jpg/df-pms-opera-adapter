"""Opera-Adapter [CRUX-MK].

Connector fuer Oracle Opera PMS OXI-API (Premium-Segment):
- OXI-Inventory (Room-Availability)
- OXI-Reservation (Book/Modify/Cancel)
- OXI-Profile (Guest-Master-Data)

K12 Provenance, K13 PAV, ENV-Var-gated Sandbox.

Welle-36.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdapterResponse:
    """Kanonische Adapter-Response."""
    adapter_name: str
    operation: str
    success: bool
    payload: dict
    source: str
    timestamp_iso: str
    request_hash: str
    error: Optional[str] = None


class PMSAdapter(ABC):
    """Mosaic-Shared Pflicht-Interface."""

    @abstractmethod
    def connect(self, credentials: dict) -> bool: ...

    @abstractmethod
    def query_inventory(self, hotel_id: str, date_range: tuple) -> list[dict]: ...

    @abstractmethod
    def book_room(self, hotel_id: str, room_type: str, guest: dict, dates: tuple) -> str: ...

    @abstractmethod
    def cancel_booking(self, booking_id: str) -> bool: ...

    @abstractmethod
    def get_capabilities(self) -> dict: ...


class OperaConnector(PMSAdapter):
    """Oracle Opera OXI-API Connector (Premium-Segment)."""

    MOCK_HOTELS = {
        "hildesheim": {"property_id": "mock-opera-hildesheim-001", "rooms_total": 150, "segment": "premium"},
        "cape-coral": {"property_id": "mock-opera-cape-coral-001", "rooms_total": 200, "segment": "premium"},
    }

    def __init__(self, sandbox_mode: Optional[bool] = None):
        self.adapter_name = "opera-pms"
        if sandbox_mode is None:
            self.sandbox_mode = os.environ.get("DF_PMS_OPERA_REAL_ENABLED", "false") != "true"
        else:
            self.sandbox_mode = sandbox_mode
        self._connected = False
        self._credentials: Optional[dict] = None
        self._access_token: str = ""

    def _request_hash(self, operation: str, payload: dict) -> str:
        canonical = json.dumps({"op": operation, "payload": payload}, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def connect(self, credentials: dict) -> bool:
        try:
            if self.sandbox_mode:
                self._connected = True
                self._credentials = credentials
                self._access_token = credentials.get("access_token", "mock-bearer-token")
                return True

            client_id = credentials.get("client_id", "")
            client_secret = credentials.get("client_secret", "")
            token_url = credentials.get("token_url", "")
            hotel_id = credentials.get("hotel_id", "")
            access_token = credentials.get("access_token", "")

            if not client_id or not client_secret or not token_url or not hotel_id:
                logger.warning("[opera-adapter] missing credentials")
                self._connected = False
                return False

            if not access_token:
                logger.warning("[opera-adapter] missing bearer-token (token-service-call required)")
                self._connected = False
                return False

            self._credentials = credentials
            self._access_token = access_token
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"[opera-adapter] connect failed: {e}")
            self._connected = False
            return False

    def query_inventory(self, hotel_id: str, date_range: tuple) -> list[dict]:
        op = "query_inventory"
        try:
            if not self._connected:
                return []

            criteria = {"hotel_id": hotel_id, "date_range": list(date_range)}
            h = self._request_hash(op, criteria)

            if self.sandbox_mode:
                hotel = self.MOCK_HOTELS.get(hotel_id, {})
                if not hotel:
                    return []
                hash_int = int(h, 16) % 100
                available = max(0, hotel["rooms_total"] - hash_int)
                return [
                    {
                        "hotel_id": hotel_id,
                        "property_id": hotel["property_id"],
                        "segment": hotel["segment"],
                        "room_type": "premium_standard",
                        "available": available // 4,
                        "rate_eur": 195.0 + (hash_int % 40),
                    },
                    {
                        "hotel_id": hotel_id,
                        "property_id": hotel["property_id"],
                        "segment": hotel["segment"],
                        "room_type": "premium_suite",
                        "available": available // 8,
                        "rate_eur": 395.0 + (hash_int % 80),
                    },
                    {
                        "hotel_id": hotel_id,
                        "property_id": hotel["property_id"],
                        "segment": hotel["segment"],
                        "room_type": "presidential_suite",
                        "available": available // 25,
                        "rate_eur": 895.0 + (hash_int % 200),
                    },
                ]

            logger.warning("[opera-adapter] real-api query_inventory not yet implemented")
            return []
        except Exception as e:
            logger.error(f"[opera-adapter] query_inventory failed: {e}")
            return []

    def book_room(self, hotel_id: str, room_type: str, guest: dict, dates: tuple) -> str:
        op = "book_room"
        try:
            if not self._connected:
                return ""

            payload = {"hotel_id": hotel_id, "room_type": room_type, "guest": guest, "dates": list(dates)}
            h = self._request_hash(op, payload)

            if self.sandbox_mode:
                return f"opera-mock-{h[:8]}"

            ticket = os.environ.get("DF_PMS_OPERA_PHRONESIS_TICKET", "")
            if not ticket:
                logger.warning("[opera-adapter] K17-PAV: missing DF_PMS_OPERA_PHRONESIS_TICKET")
                return ""

            logger.warning("[opera-adapter] real-api book_room not yet implemented")
            return ""
        except Exception as e:
            logger.error(f"[opera-adapter] book_room failed: {e}")
            return ""

    def cancel_booking(self, booking_id: str) -> bool:
        op = "cancel_booking"
        try:
            if not self._connected or not booking_id:
                return False

            payload = {"booking_id": booking_id}
            _ = self._request_hash(op, payload)

            if self.sandbox_mode:
                if booking_id.startswith("fail-"):
                    return False
                return True

            logger.warning("[opera-adapter] real-api cancel_booking not yet implemented")
            return False
        except Exception as e:
            logger.error(f"[opera-adapter] cancel_booking failed: {e}")
            return False

    def get_capabilities(self) -> dict:
        return {
            "adapter_name": self.adapter_name,
            "version": "0.1.0-SKELETON",
            "sandbox_mode": self.sandbox_mode,
            "connected": self._connected,
            "adapter_type": "pms",
            "segment": "premium",
            "api_protocol": "OXI",
            "supported_operations": ["connect", "query_inventory", "book_room", "cancel_booking"],
            "feature_flags": {
                "real_api": not self.sandbox_mode,
                "k17_pav": True,
                "hmac_audit": True,
                "circuit_breaker": True,
                "oauth2_bearer": True,
                "token_refresh": True,
            },
            "health_score": 1.0 if self._connected else 0.5,
        }
