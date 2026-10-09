"""Configuración centralizada de la aplicación.

Todos los valores se leen de variables de entorno (o de un archivo ``.env`` en
desarrollo) siguiendo el principio *12-factor*. Ningún secreto se versiona.
"""

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RepositoryBackend(StrEnum):
    """Implementaciones de persistencia disponibles."""

    MEMORY = "memory"
    FIRESTORE = "firestore"


class Settings(BaseSettings):
    """Parámetros de configuración tipados y validados al arrancar."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Issue Tracker API"
    app_version: str = "1.0.0"
    app_env: str = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # Persistencia
    repository_backend: RepositoryBackend = RepositoryBackend.MEMORY
    gcp_project_id: str | None = None
    firestore_database: str = "(default)"
    users_collection: str = "users"
    issues_collection: str = "issues"
    revoked_tokens_collection: str = "revoked_tokens"

    # Seguridad / JWT
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "issue-tracker-api"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)

    # CORS
    cors_origins: list[str] = ["http://localhost:4200"]

    # Datos demo (solo backend en memoria)
    seed_demo_users: bool = True

    @field_validator("jwt_algorithm")
    @classmethod
    def _only_hmac_algorithms(cls, value: str) -> str:
        allowed = {"HS256", "HS384", "HS512"}
        if value not in allowed:
            raise ValueError(f"JWT_ALGORITHM debe ser uno de {sorted(allowed)}")
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia única (cacheada) de la configuración."""
    return Settings()  # type: ignore[call-arg]
