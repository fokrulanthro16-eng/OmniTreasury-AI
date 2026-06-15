"""Custom exception hierarchy for OmniTreasury AI."""

from __future__ import annotations


class OmniTreasuryError(Exception):
    """Base exception. All application errors inherit from this."""


class ParseError(OmniTreasuryError):
    """Raised when a document (e.g. SWIFT MT103) cannot be parsed."""


class ComplianceError(OmniTreasuryError):
    """Raised on unrecoverable compliance engine failures."""


class FXEngineError(OmniTreasuryError):
    """Raised when FX rate data is unavailable or routing fails."""


class LiquidityError(OmniTreasuryError):
    """Raised when cash position data cannot be retrieved."""


class RiskEngineError(OmniTreasuryError):
    """Raised when the risk scoring engine encounters a fatal error."""


class DecisionEngineError(OmniTreasuryError):
    """Raised when the decision engine cannot produce a result."""


class MaestroIntegrationError(OmniTreasuryError):
    """Raised on UiPath Maestro API failures."""


class AgentExecutionError(OmniTreasuryError):
    """Raised when a CrewAI agent fails to complete its task."""


class DataNotFoundError(OmniTreasuryError):
    """Raised when required reference data (entity, account) is missing."""
