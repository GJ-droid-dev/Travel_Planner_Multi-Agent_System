from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    parallel_agent_execution: bool = True
    exchange_rate_usd_aed: float = 3.67
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global singleton
settings = Settings()
