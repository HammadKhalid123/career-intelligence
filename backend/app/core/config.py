from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urlsplit, urlunsplit


def get_async_database_url(url: str) -> str:
    """Normalize a Neon/libpq URL for SQLAlchemy's asyncpg dialect."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", parts.fragment))


class Settings(BaseSettings):
    APP_NAME: str = "CareerCopilot AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    CORS_ORIGINS: str = ""

    DATABASE_URL: str = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
    DATABASE_URL_DIRECT: str = ""

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: list[str] = [".pdf"]

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MAX_RETRIES: int = 2

    HF_TOKEN: str = ""
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    CHROMA_PERSIST_DIR: str = "chroma_store"
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 4

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()