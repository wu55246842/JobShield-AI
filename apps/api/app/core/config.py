from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JobShield API"
    env: str = "dev"
    api_prefix: str = ""

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/jobshield"
    web_origin: str = "http://localhost:3000"

    onet_base_url: str = "https://services.onetcenter.org/ws"
    onet_username: str | None = None
    onet_password: str | None = None

    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"

    ingest_api_key: str = "change-me"
    request_timeout_s: float = 20.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
