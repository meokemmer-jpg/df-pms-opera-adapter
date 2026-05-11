"""df-pms-opera-adapter [CRUX-MK].

Welle-36 HeyLou-Mosaic-Adapter fuer Oracle Opera PMS (Premium-Segment).
"""

from __future__ import annotations

__version__ = "0.1.0-SKELETON"
__df_id__ = "df-pms-opera-adapter"
__welle__ = "welle-36"


def get_connector():
    from src.opera_adapter import OperaConnector
    return OperaConnector


def get_auth():
    from src.opera_auth import OperaAuth
    return OperaAuth


def get_orchestrator():
    from src.adapter_orchestrator import OperaAdapterOrchestrator
    return OperaAdapterOrchestrator


def get_audit_logger():
    from src.audit_logger import AuditLogger
    return AuditLogger


__all__ = ["__version__", "__df_id__", "__welle__", "get_connector", "get_auth", "get_orchestrator", "get_audit_logger"]
