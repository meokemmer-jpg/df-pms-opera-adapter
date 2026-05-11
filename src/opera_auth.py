"""Opera-Auth-Manager [CRUX-MK].

Opera verwendet OAuth2 Token-Service-Pattern:
- Client-Credentials Grant (Client-ID + Client-Secret)
- Token-Service-Endpoint liefert Bearer-Token
- Token-Lifetime ~1h, Refresh per 55min Re-Fetch

ENV-Var-gated: ohne OPERA_CLIENT_ID -> Mock.

Welle-36.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OperaCredentials:
    """Kanonische Opera-Credentials.

    source ∈ {"env", "mock", "vault"}
    """
    client_id: str
    client_secret: str
    token_url: str
    hotel_id: str
    access_token: str            # Bearer-Token
    source: str
    fetched_iso: str
    expires_iso: str             # Token-Expiry


class OperaAuth:
    """Manager fuer Opera OAuth2 Token-Service-Auth."""

    MOCK_CLIENT_ID = "mock-opera-client-id"
    MOCK_CLIENT_SECRET = "mock-opera-client-secret"
    MOCK_TOKEN_URL = "https://mock.opera.example.com/oauth/token"
    MOCK_HOTEL_ID = "MOCK-HEYLOU-HILD"
    MOCK_ACCESS_TOKEN = "mock-bearer-token-xyz-2026"

    TOKEN_LIFETIME_MIN = 55  # tatsaechlich 60min, wir refreshen nach 55min

    def __init__(self, sandbox_mode: Optional[bool] = None):
        if sandbox_mode is None:
            self.sandbox_mode = os.environ.get("DF_PMS_OPERA_REAL_ENABLED", "false") != "true"
        else:
            self.sandbox_mode = sandbox_mode

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _expiry_iso(self) -> str:
        return (datetime.now(timezone.utc) + timedelta(minutes=self.TOKEN_LIFETIME_MIN)).isoformat()

    def get_credentials(self, tenant_id: str = "hildesheim") -> Optional[OperaCredentials]:
        """Holt Credentials. Im Real-Mode wird Token-Service-Call simuliert (Placeholder)."""
        if self.sandbox_mode:
            return OperaCredentials(
                client_id=self.MOCK_CLIENT_ID,
                client_secret=self.MOCK_CLIENT_SECRET,
                token_url=self.MOCK_TOKEN_URL,
                hotel_id=self.MOCK_HOTEL_ID,
                access_token=self.MOCK_ACCESS_TOKEN,
                source="mock",
                fetched_iso=self._now_iso(),
                expires_iso=self._expiry_iso(),
            )

        client_id = os.environ.get("OPERA_CLIENT_ID", "")
        client_secret = os.environ.get("OPERA_CLIENT_SECRET", "")
        token_url = os.environ.get("OPERA_TOKEN_URL", "")
        hotel_id = os.environ.get("OPERA_HOTEL_ID", "")

        if not client_id or not client_secret or not token_url or not hotel_id:
            logger.warning(
                f"[opera-auth] missing credentials for tenant={tenant_id} "
                f"(CLIENT_ID={'set' if client_id else 'EMPTY'}, "
                f"CLIENT_SECRET={'set' if client_secret else 'EMPTY'}, "
                f"TOKEN_URL={'set' if token_url else 'EMPTY'}, "
                f"HOTEL_ID={'set' if hotel_id else 'EMPTY'})"
            )
            return None

        # Real Token-Service Call (Welle-37 Live-Implementation)
        # Placeholder: token wird hier echt von OPERA_TOKEN_URL geholt
        access_token = ""  # placeholder

        return OperaCredentials(
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            hotel_id=hotel_id,
            access_token=access_token,
            source="env",
            fetched_iso=self._now_iso(),
            expires_iso=self._expiry_iso(),
        )

    def validate(self, creds: Optional[OperaCredentials]) -> bool:
        """Strukturelle Validierung + Expiry-Check."""
        if creds is None:
            return False
        if not creds.client_id or not creds.client_secret or not creds.token_url:
            return False
        if not creds.hotel_id:
            return False
        if creds.source not in ("env", "mock", "vault"):
            return False
        # Mock-token is OK without expiry check
        if creds.source == "mock":
            return True
        # Real-mode: token must be present
        if not creds.access_token:
            return False
        return True

    def refresh_if_expired(self, creds: Optional[OperaCredentials]) -> Optional[OperaCredentials]:
        """Re-fetch token wenn expired."""
        if not self.validate(creds):
            return self.get_credentials()
        try:
            expires = datetime.fromisoformat(creds.expires_iso)
            now = datetime.now(timezone.utc)
            if now >= expires:
                logger.info("[opera-auth] token expired, re-fetching")
                return self.get_credentials()
        except (ValueError, TypeError):
            return self.get_credentials()
        return creds

    def is_real_mode(self) -> bool:
        return not self.sandbox_mode
