"""Opera-Adapter-Orchestrator [CRUX-MK]. Welle-36."""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LoopReport:
    loop_id: str
    df_id: str
    started_iso: str
    finished_iso: str
    sandbox_mode: bool
    final_status: str
    phases_passed: list = field(default_factory=list)
    phases_failed: list = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)
    error: Optional[str] = None


class OperaAdapterOrchestrator:
    DF_ID = "df-pms-opera-adapter"

    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id or os.environ.get("DF_PMS_OPERA_TENANT_ID", "hildesheim")
        self.sandbox_mode = os.environ.get("DF_PMS_OPERA_REAL_ENABLED", "false") != "true"

        from src.opera_auth import OperaAuth
        from src.opera_adapter import OperaConnector
        from src.audit_logger import AuditLogger

        self.auth = OperaAuth(sandbox_mode=self.sandbox_mode)
        self.connector = OperaConnector(sandbox_mode=self.sandbox_mode)
        self.audit = AuditLogger(df_id=self.DF_ID)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _persist_loop_report(self, report: LoopReport) -> Optional[Path]:
        try:
            reports_dir = Path("runs/loop-reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            file_path = reports_dir / f"loop-{report.loop_id}.json"
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2, default=str)
            return file_path
        except Exception as e:
            logger.error(f"loop-report persist failed: {e}")
            return None

    def run(self, hotel_id: Optional[str] = None, dry_run: bool = False) -> LoopReport:
        loop_id = str(uuid.uuid4())[:8]
        report = LoopReport(
            loop_id=loop_id,
            df_id=self.DF_ID,
            started_iso=self._now_iso(),
            finished_iso="",
            sandbox_mode=self.sandbox_mode,
            final_status="failed",
        )

        hotel_id = hotel_id or self.tenant_id

        try:
            creds = None
            try:
                creds = self.auth.get_credentials(self.tenant_id)
                if not self.auth.validate(creds):
                    report.phases_failed.append("auth")
                    self.audit.log("auth_failed", {"tenant_id": self.tenant_id, "loop_id": loop_id}, target="opera-auth")
                else:
                    report.phases_passed.append("auth")
                    self.audit.log("auth_ok", {"tenant_id": self.tenant_id, "source": creds.source, "loop_id": loop_id}, target="opera-auth")
            except Exception as e:
                report.phases_failed.append("auth")
                report.error = f"auth: {e}"

            if "auth" in report.phases_failed and not self.sandbox_mode:
                report.finished_iso = self._now_iso()
                self._persist_loop_report(report)
                return report

            try:
                creds_dict = {
                    "client_id": creds.client_id if creds else "",
                    "client_secret": creds.client_secret if creds else "",
                    "token_url": creds.token_url if creds else "",
                    "hotel_id": creds.hotel_id if creds else "",
                    "access_token": creds.access_token if creds else "",
                }
                connected = self.connector.connect(creds_dict)
                if connected:
                    report.phases_passed.append("connect")
                    self.audit.log("connect_ok", {"tenant_id": self.tenant_id, "loop_id": loop_id}, target="opera-operations")
                else:
                    report.phases_failed.append("connect")
            except Exception as e:
                report.phases_failed.append("connect")
                logger.error(f"[orchestrator] connect failed: {e}")

            try:
                caps = self.connector.get_capabilities()
                report.artifacts["capabilities"] = caps
                report.phases_passed.append("health_check")
            except Exception as e:
                report.phases_failed.append("health_check")

            if not dry_run and self.connector._connected:
                try:
                    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    tomorrow_iso = f"{today}T14:00:00Z"
                    inv = self.connector.query_inventory(hotel_id, (tomorrow_iso, tomorrow_iso))
                    report.artifacts["sample_inventory_count"] = len(inv)
                    report.phases_passed.append("sample_query")
                    self.audit.log("sample_query_ok", {"hotel_id": hotel_id, "rooms": len(inv), "loop_id": loop_id}, target="opera-operations")
                except Exception as e:
                    report.phases_failed.append("sample_query")

            try:
                self.audit.log(
                    "loop_complete",
                    {
                        "loop_id": loop_id,
                        "phases_passed": report.phases_passed,
                        "phases_failed": report.phases_failed,
                        "sandbox_mode": self.sandbox_mode,
                    },
                    target="opera-operations",
                )
                report.phases_passed.append("audit_persist")
            except Exception as e:
                report.phases_failed.append("audit_persist")

            if not report.phases_failed:
                report.final_status = "complete"
            elif len(report.phases_passed) >= 3:
                report.final_status = "partial"
            else:
                report.final_status = "failed"

        except Exception as e:
            report.error = f"orchestrator: {e}"
            report.final_status = "failed"
        finally:
            report.finished_iso = self._now_iso()
            self._persist_loop_report(report)

        return report


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    orch = OperaAdapterOrchestrator()
    report = orch.run()
    print(f"[df-pms-opera-adapter] loop_id={report.loop_id} status={report.final_status} sandbox={report.sandbox_mode}")
    sys.exit(0 if report.final_status in ("complete", "partial") else 1)


if __name__ == "__main__":
    main()
