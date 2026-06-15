"""UiPath Maestro Case integration client.

In mock mode (USE_MOCK_MAESTRO=true), cases are stored in-memory and logged.
In live mode, communicates with UiPath Cloud via REST/OAuth2.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx

from src.core.config import settings
from src.core.exceptions import MaestroIntegrationError
from src.core.logging_config import get_logger
from src.models.decision import CasePayload, EscalationLevel

logger = get_logger("uipath_maestro")

# In-memory case store for mock mode
_MOCK_CASES: dict[str, dict[str, Any]] = {}


class MaestroClient:
    """Creates and manages UiPath Maestro Cases for treasury payment exceptions."""

    def __init__(self) -> None:
        self._mock = settings.use_mock_maestro
        self._token: Optional[str] = None
        self._base_url = settings.uipath_maestro_url

    # ── Public interface ──────────────────────────────────────────────────────

    def create_case(self, payload: CasePayload) -> str:
        """Create a Maestro Case and return the case ID."""
        if self._mock:
            return self._mock_create_case(payload)
        return self._live_create_case(payload)

    def get_case_status(self, case_id: str) -> dict[str, Any]:
        """Retrieve current status of an existing case."""
        if self._mock:
            return self._mock_get_case(case_id)
        return self._live_get_case(case_id)

    def close_case(
        self,
        case_id: str,
        decision: str,
        approver: str,
        notes: str = "",
    ) -> bool:
        """Close a Maestro Case with a human decision."""
        if self._mock:
            return self._mock_close_case(case_id, decision, approver, notes)
        return self._live_close_case(case_id, decision, approver, notes)

    # ── Mock implementation ───────────────────────────────────────────────────

    def _mock_create_case(self, payload: CasePayload) -> str:
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        _MOCK_CASES[case_id] = {
            "case_id": case_id,
            "title": payload.case_title,
            "type": payload.case_type,
            "priority": payload.priority,
            "assigned_role": payload.assigned_role.value,
            "sla_minutes": payload.sla_minutes,
            "status": "OPEN",
            "created_at": datetime.utcnow().isoformat(),
            "payload": payload.model_dump(),
        }
        logger.info(
            "[MOCK] Maestro Case created",
            case_id=case_id,
            title=payload.case_title,
            assigned_role=payload.assigned_role.value,
            sla_minutes=payload.sla_minutes,
        )
        self._print_case_summary(case_id, payload)
        return case_id

    def _mock_get_case(self, case_id: str) -> dict[str, Any]:
        case = _MOCK_CASES.get(case_id)
        if not case:
            raise MaestroIntegrationError(f"Case {case_id} not found in mock store.")
        return case

    def _mock_close_case(
        self, case_id: str, decision: str, approver: str, notes: str
    ) -> bool:
        case = _MOCK_CASES.get(case_id)
        if not case:
            raise MaestroIntegrationError(f"Case {case_id} not found.")
        case["status"] = "CLOSED"
        case["human_decision"] = decision
        case["approver"] = approver
        case["human_notes"] = notes
        case["closed_at"] = datetime.utcnow().isoformat()
        logger.info(
            "[MOCK] Maestro Case closed",
            case_id=case_id,
            decision=decision,
            approver=approver,
        )
        return True

    # ── Live implementation ───────────────────────────────────────────────────

    def _live_create_case(self, payload: CasePayload) -> str:
        token = self._get_token()
        url = (
            f"{self._base_url}/{settings.uipath_org_id}/"
            f"{settings.uipath_tenant_name}/orchestrator_/odata/Cases"
        )
        body = {
            "Name": payload.case_title,
            "Description": json.dumps(payload.model_dump()),
            "Priority": payload.priority,
            "CatalogName": "TreasuryPaymentException",
            "AssignedRoleName": payload.assigned_role.value,
        }
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    url,
                    json=body,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                data = response.json()
                return str(data.get("Id", "UNKNOWN"))
        except httpx.HTTPError as exc:
            raise MaestroIntegrationError(f"Failed to create Maestro Case: {exc}") from exc

    def _live_get_case(self, case_id: str) -> dict[str, Any]:
        token = self._get_token()
        url = (
            f"{self._base_url}/{settings.uipath_org_id}/"
            f"{settings.uipath_tenant_name}/orchestrator_/odata/Cases({case_id})"
        )
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(url, headers={"Authorization": f"Bearer {token}"})
                response.raise_for_status()
                return dict(response.json())
        except httpx.HTTPError as exc:
            raise MaestroIntegrationError(f"Failed to get case {case_id}: {exc}") from exc

    def _live_close_case(
        self, case_id: str, decision: str, approver: str, notes: str
    ) -> bool:
        token = self._get_token()
        url = (
            f"{self._base_url}/{settings.uipath_org_id}/"
            f"{settings.uipath_tenant_name}/orchestrator_/odata/Cases({case_id})/Close"
        )
        body = {"Resolution": decision, "Comment": f"{approver}: {notes}"}
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, json=body, headers={"Authorization": f"Bearer {token}"})
                response.raise_for_status()
                return True
        except httpx.HTTPError as exc:
            raise MaestroIntegrationError(f"Failed to close case {case_id}: {exc}") from exc

    def _get_token(self) -> str:
        if self._token:
            return self._token
        url = f"{self._base_url}/identity_/connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.uipath_client_id,
            "client_secret": settings.uipath_client_secret,
            "scope": "OR.Cases OR.Tasks",
        }
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, data=data)
                response.raise_for_status()
                self._token = response.json()["access_token"]
                return self._token
        except httpx.HTTPError as exc:
            raise MaestroIntegrationError(f"OAuth2 token request failed: {exc}") from exc

    # ── Display helper ────────────────────────────────────────────────────────

    @staticmethod
    def _print_case_summary(case_id: str, payload: CasePayload) -> None:
        print(f"\n{'='*60}")
        print(f"  MAESTRO CASE CREATED: {case_id}")
        print(f"{'='*60}")
        print(f"  Title    : {payload.case_title}")
        print(f"  Priority : {payload.priority}")
        print(f"  Assigned : {payload.assigned_role.value}")
        print(f"  SLA      : {payload.sla_minutes} minutes")
        print(f"  Triggers : {'; '.join(payload.agent_recommendations[:2])}")
        print(f"{'='*60}\n")
