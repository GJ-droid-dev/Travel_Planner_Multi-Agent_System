from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # Gemini — used by Orchestrator, Destination, Logistics, Budget agents
    gemini_api_key: SecretStr
    gemini_model: str = "gemini-3.6-flash"

    # Groq — used exclusively by the Review Agent
    groq_api_key: SecretStr
    groq_model: str = "llama-3.3-70b-versatile"

    llm_temperature: float = 0.7
    llm_max_tokens: int = 8192
    max_revision_loops: int = 2
    agent_timeout_seconds: int = 30
    request_timeout_seconds: int = 90
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    parallel_agent_execution: bool = True
    exchange_rate_usd_aed: float = 3.67
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/travel_planner"

    @field_validator("database_url")
    @classmethod
    def to_async_database_url(cls, url: str) -> str:
        url = url.replace("sslmode=require", "ssl=require")
        url = url.replace("&channel_binding=require", "").replace("?channel_binding=require", "")
        if url.startswith("postgresql+asyncpg://"):
            return url
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        raise ValueError("DATABASE_URL must be a PostgreSQL connection URL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global singleton
settings = Settings()
