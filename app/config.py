from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    gateway_api_key: str = "gate-dev-key-123"
    cheap_model: str = "groq/openai/gpt-oss-20b"
    strong_model: str = "groq/openai/gpt-oss-120b"
    db_path: str = "gatellm.db"
    rate_limit_per_min: int = 30
    request_timeout: float = 30.0
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"


settings = Settings()