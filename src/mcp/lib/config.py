from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class MCPServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    CAPABILITY_API_BASE_URL: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"
    AUDIT_LOG_PATH: str = "logs/mcp-audit.jsonl"
    
    # Optional: for direct testing or specific overrides
    ENVIRONMENT: str = "local"
    
    # Auth settings
    OKTA_ISSUER: str = "http://localhost:9000/oauth2/default"
    CAPABILITY_API_AUDIENCE: str = "api://hr-ai-platform"

settings = MCPServerSettings()