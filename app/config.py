from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration for services and pipelines."""

    database_url: str = Field(
        default="sqlite:///./artifacts/app.db",
        description="SQLAlchemy-compatible database URL. Defaults to local SQLite for development.",
    )
    data_csv_path: Path = Field(
        default=Path("data/house_prices.csv"),
        description="Location of the raw house price CSV file.",
    )
    vector_store_path: Path = Field(
        default=Path("artifacts/vector_store"),
        description="Directory for persisting vector store snapshots.",
    )
    lm_studio_url: Optional[str] = Field(
        default=None,
        description="HTTP endpoint of the LM Studio server.",
    )
    lm_studio_api_key: Optional[str] = Field(
        default=None,
        description="Optional API key for LM Studio requests.",
    )
    lm_studio_model: str = Field(
        default="gpt-oss-20b",
        description="Identifier of the model served by LM Studio.",
    )
    max_results: int = Field(
        default=5,
        description="Default number of RAG retrieval results.",
    )
    embedding_dimension: int = Field(
        default=128,
        description="Length of generated embedding vectors.",
    )
    log_dir: Path = Field(
        default=Path("logs"),
        description="Root directory for application logs.",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        arbitrary_types_allowed=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance so all components share configuration."""

    settings = Settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_store_path.mkdir(parents=True, exist_ok=True)
    return settings
