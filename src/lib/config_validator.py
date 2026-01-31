from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

class AppSettings(BaseSettings):
    """
    Application configuration and validation.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: str = Field(default="local", description="Deployment environment (local, dev, prod)")
    POLICY_PATH: str = Field(default="config/policy-workday.yaml", description="Path to the policy YAML file")
    
    # Add other potentially critical env vars here if needed
    # OKTA_ISSUER: str = ...
    # WORKDAY_API_URL: str = ...

    @field_validator("POLICY_PATH")
    @classmethod
    def validate_policy_path(cls, v: str) -> str:
        path = Path(v)
        if not path.exists():
            # In production, we might want to be strict. In local, we might warn.
            # But the current code raises FileNotFoundError, so we keep that behavior.
            raise FileNotFoundError(f"Policy file not found: {v}")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["local", "dev", "prod", "test"]
        if v.lower() not in allowed:
            raise ValueError(f"Invalid environment: {v}. Must be one of {allowed}")
        return v.lower()

# Create a global instance
try:
    settings = AppSettings()
except Exception as e:
    # Fail fast at startup
    print(f"CRITICAL: Configuration validation failed: {e}")
    raise
