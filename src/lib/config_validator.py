from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import TYPE_CHECKING
import os

if TYPE_CHECKING:
    from typing import Self

class AppSettings(BaseSettings):
    """
    Application configuration and validation.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: str = Field(default="local", description="Deployment environment (local, dev, prod)")
    POLICY_PATH: str = Field(default="config/policy-workday.yaml", description="Path to the policy YAML file")
    CAPABILITY_REGISTRY_PATH: str = Field(default="config/capabilities/index.yaml", description="Path to the capability registry")
    AUDIT_LOG_PATH: str = Field(default="logs/audit.jsonl", description="Path to the audit log file")
    MOCK_OKTA_TEST_SECRET: str = Field(description="Secret key for Mock Okta test endpoints")
    MCP_CLIENT_ID: str = Field(default="mcp-server-client", description="Authorized Client ID for MCP server")
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30, description="Request timeout in seconds")

    @field_validator("POLICY_PATH", "CAPABILITY_REGISTRY_PATH")
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        path = Path(v)
        if not path.is_absolute():
            # Resolve relative to project root (parent of 'src')
            project_root = Path(__file__).resolve().parent.parent.parent
            path = project_root / v
        
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {v} (resolved to: {path.absolute()})")
        return str(path)

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["local", "dev", "prod", "test"]
        if v.lower() not in allowed:
            raise ValueError(f"Invalid environment: {v}. Must be one of {allowed}")
        return v.lower()

    @model_validator(mode='after')
    def validate_policy_against_registry(self) -> 'AppSettings':
        """
        Cross-validate policy references against the capability registry at startup.
        Note: We import here to avoid circular dependencies during initialization.
        """
        from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
        from src.domain.services.capability_registry import reset_capability_registry
        
        try:
            # Ensure we aren't using a stale registry instance from a previous validation run
            reset_capability_registry()
            
            loader = FilePolicyLoaderAdapter(
                policy_path=self.POLICY_PATH, 
                registry_path=self.CAPABILITY_REGISTRY_PATH
            )
            # This will raise ValueError if validation fails
            loader.load_policy()
        except Exception as e:

            if isinstance(e, FileNotFoundError):
                raise e
            raise ValueError(f"Policy validation against registry failed: {e}")
            
        return self

# Create a global instance
try:
    settings = AppSettings()
except Exception as e:
    # Fail fast at startup
    raise
