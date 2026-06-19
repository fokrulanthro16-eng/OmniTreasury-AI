"""Application settings loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="OmniTreasury AI")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # AI / LLM
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")

    # UiPath Maestro
    uipath_org_id: str = Field(default="")
    uipath_tenant_name: str = Field(default="")
    uipath_client_id: str = Field(default="")
    uipath_client_secret: str = Field(default="")
    uipath_maestro_url: str = Field(default="https://cloud.uipath.com")
    uipath_folder_path: str = Field(default="Shared")

    # FX Data Feed
    fx_api_key: str = Field(default="")
    fx_api_url: str = Field(default="https://api.exchangerate-api.com/v4")

    # Decision thresholds
    auto_approve_max_amount: float = Field(default=500_000.0)
    risk_escalation_threshold: int = Field(default=60)
    high_risk_threshold: int = Field(default=80)
    compliance_fuzzy_match_threshold: int = Field(default=75)
    materiality_threshold: float = Field(default=1_000_000.0)

    # Mock flags
    use_mock_data: bool = Field(default=True)
    use_mock_fx: bool = Field(default=True)
    use_mock_banking: bool = Field(default=True)
    use_mock_maestro: bool = Field(default=True)

    @property
    def sample_data_dir(self) -> Path:
        return BASE_DIR / "sample_data"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()
