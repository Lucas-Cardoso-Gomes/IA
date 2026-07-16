from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_API_KEY: str = "ollama"
    DB_CONNECTION: str = "sqlite:///./pmlogistica.db"
    VECTOR_DB_PATH: str = "./chroma_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    OPENAI_TELEMETRY: str = "false"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
