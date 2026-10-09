"""Pruebas unitarias del servicio de autenticación."""

import pytest

from app.container import Container, seed_demo_users
from app.core.exceptions import AuthenticationError, InvalidCredentialsError
from app.core.security import hash_password
from app.domain.models import User


@pytest.fixture
async def seeded(container: Container) -> Container:
    await seed_demo_users(container.users)
    return container


async def test_login_success_returns_token_and_user(seeded: Container) -> None:
    result = await seeded.auth_service.login("admin", "Admin#2026")
    assert result.access_token
    assert result.user.username == "admin"
    assert result.expires_in == 15 * 60


async def test_login_is_case_insensitive_on_username(seeded: Container) -> None:
    result = await seeded.auth_service.login("  ADMIN ", "Admin#2026")
    assert result.user.username == "admin"


async def test_login_fails_with_wrong_password(seeded: Container) -> None:
    with pytest.raises(InvalidCredentialsError):
        await seeded.auth_service.login("admin", "bad-password")


async def test_login_fails_with_unknown_user_with_same_error(seeded: Container) -> None:
    # Mismo error que contraseña incorrecta: no se revela si el usuario existe.
    with pytest.raises(InvalidCredentialsError):
        await seeded.auth_service.login("ghost", "Admin#2026")


async def test_login_fails_for_inactive_user(container: Container) -> None:
    await container.users.upsert(
        User(
            id="u-x",
            username="inactivo",
            full_name="Inactivo",
            password_hash=hash_password("Pass#123"),
            is_active=False,
        )
    )
    with pytest.raises(InvalidCredentialsError):
        await container.auth_service.login("inactivo", "Pass#123")


async def test_get_user_from_valid_token(seeded: Container) -> None:
    result = await seeded.auth_service.login("admin", "Admin#2026")
    user = await seeded.auth_service.get_user_from_token(result.access_token)
    assert user.id == result.user.id


async def test_logout_revokes_token(seeded: Container) -> None:
    result = await seeded.auth_service.login("admin", "Admin#2026")
    await seeded.auth_service.logout(result.access_token)
    with pytest.raises(AuthenticationError, match="cerrada"):
        await seeded.auth_service.get_user_from_token(result.access_token)


async def test_token_for_deleted_user_is_rejected(container: Container) -> None:
    token = container.tokens.create_access_token("non-existent-user")
    with pytest.raises(AuthenticationError):
        await container.auth_service.get_user_from_token(token)
