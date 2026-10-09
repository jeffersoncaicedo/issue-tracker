"""Fixtures compartidas.

Las pruebas usan los repositorios en memoria: son rápidas, deterministas y no
requieren credenciales de GCP.
"""

import os

# Variables mínimas ANTES de importar la app (app.main crea la instancia al importarse).
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough-for-hmac-256")
os.environ.setdefault("REPOSITORY_BACKEND", "memory")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.container import Container, build_container  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.core.seed_data import DEMO_USERS  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-that-is-long-enough-for-hmac-256",
        repository_backend="memory",
        access_token_expire_minutes=15,
        seed_demo_users=True,
        log_level="WARNING",
    )


@pytest.fixture
def container(settings: Settings) -> Container:
    return build_container(settings)


@pytest.fixture
def client(settings: Settings, container: Container) -> Iterator[TestClient]:
    app = create_app(settings, container)
    with TestClient(app) as test_client:  # ejecuta el lifespan (carga usuarios demo)
        yield test_client


@pytest.fixture
def demo_user() -> dict[str, str]:
    return dict(DEMO_USERS[0])


@pytest.fixture
def auth_headers(client: TestClient, demo_user: dict[str, str]) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": demo_user["username"], "password": demo_user["password"]},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
