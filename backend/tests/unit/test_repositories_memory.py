"""Pruebas del repositorio de tokens revocados en memoria."""

from datetime import UTC, datetime, timedelta

from app.repositories.memory.repositories import InMemoryRevokedTokenRepository


async def test_revoke_and_check() -> None:
    repo = InMemoryRevokedTokenRepository()
    await repo.revoke("abc", datetime.now(UTC) + timedelta(minutes=5))
    assert await repo.is_revoked("abc") is True
    assert await repo.is_revoked("other") is False


async def test_expired_entries_are_purged() -> None:
    repo = InMemoryRevokedTokenRepository()
    await repo.revoke("old", datetime.now(UTC) - timedelta(minutes=1))
    await repo.revoke("new", datetime.now(UTC) + timedelta(minutes=5))  # dispara la purga
    assert await repo.is_revoked("old") is False
    assert await repo.is_revoked("new") is True
