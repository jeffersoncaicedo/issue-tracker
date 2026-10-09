"""Pruebas de los repositorios Firestore contra un doble en memoria del SDK.

El doble imita solo la superficie de ``AsyncClient`` que usamos (collection,
document, where/FieldFilter, limit, stream, count). Valida el mapeo documento ↔
entidad, los filtros, los conteos y la traducción de errores sin acceder a GCP.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from google.api_core.exceptions import ServiceUnavailable

from app.core.exceptions import RepositoryError
from app.domain.models import Issue, IssueFilters, IssuePriority, IssueStatus, Role, User
from app.repositories.firestore.repositories import (
    FirestoreIssueRepository,
    FirestoreRevokedTokenRepository,
    FirestoreUserRepository,
)


# ----------------------------------------------------------------- doble del SDK
class _Snapshot:
    def __init__(self, doc_id: str, data: dict[str, Any] | None) -> None:
        self.id, self._data, self.exists = doc_id, data, data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return dict(self._data) if self._data else None


class _AggResult:
    def __init__(self, value: int) -> None:
        self.value = value


class _Doc:
    def __init__(self, store: dict, doc_id: str) -> None:
        self._store, self._id = store, doc_id

    async def get(self) -> _Snapshot:
        return _Snapshot(self._id, self._store.get(self._id))

    async def set(self, data: dict) -> None:
        self._store[self._id] = dict(data)

    async def update(self, data: dict) -> None:
        self._store[self._id].update(data)

    async def delete(self) -> None:
        self._store.pop(self._id, None)


class _Query:
    def __init__(self, store: dict, filters: tuple = (), limit: int | None = None) -> None:
        self._store, self._filters, self._limit = store, filters, limit

    def where(self, *, filter: Any) -> "_Query":  # noqa: A002 - firma del SDK
        return _Query(self._store, (*self._filters, (filter.field_path, filter.value)), self._limit)

    def limit(self, n: int) -> "_Query":
        return _Query(self._store, self._filters, n)

    def _matches(self) -> list[tuple[str, dict]]:
        rows = [
            (k, v)
            for k, v in self._store.items()
            if all(v.get(f) == val for f, val in self._filters)
        ]
        return rows[: self._limit] if self._limit else rows

    async def stream(self):  # noqa: ANN201
        for doc_id, data in self._matches():
            yield _Snapshot(doc_id, data)

    def count(self, alias: str) -> "_Query":
        return self

    async def get(self) -> list[list[_AggResult]]:
        return [[_AggResult(len(self._matches()))]]


class _Collection(_Query):
    def document(self, doc_id: str) -> _Doc:
        return _Doc(self._store, doc_id)


class FakeClient:
    def __init__(self) -> None:
        self.data: dict[str, dict] = {}

    def collection(self, name: str) -> _Collection:
        return _Collection(self.data.setdefault(name, {}))


def _issue(issue_id: str, status: IssueStatus, priority: IssuePriority, minutes: int) -> Issue:
    ts = datetime(2026, 10, 1, tzinfo=UTC) + timedelta(minutes=minutes)
    return Issue(
        id=issue_id,
        title=f"T{issue_id}",
        description="d",
        priority=priority,
        status=status,
        created_by="admin",
        created_at=ts,
        updated_at=ts,
    )


# ----------------------------------------------------------------- pruebas
@pytest.fixture
def client() -> FakeClient:
    return FakeClient()


async def test_user_roundtrip_and_lookup(client: FakeClient) -> None:
    repo = FirestoreUserRepository(client, "users")  # type: ignore[arg-type]
    user = User(id="u1", username="soporte", full_name="S", password_hash="h", role=Role.SUPPORT)
    await repo.upsert(user)

    assert client.data["users"]["u1"]["role"] == "support"
    assert "password" not in client.data["users"]["u1"]
    assert await repo.get_by_username("soporte") == user
    assert await repo.get_by_id("u1") == user
    assert await repo.get_by_username("nadie") is None
    assert await repo.get_by_id("nadie") is None


async def test_user_without_role_defaults_to_regular_user(client: FakeClient) -> None:
    client.data["users"] = {"u9": {"username": "legacy", "password_hash": "h"}}
    repo = FirestoreUserRepository(client, "users")  # type: ignore[arg-type]
    user = await repo.get_by_id("u9")
    assert user is not None and user.role is Role.USER and user.full_name == "legacy"


async def test_issue_crud_filters_and_order(client: FakeClient) -> None:
    repo = FirestoreIssueRepository(client, "issues")  # type: ignore[arg-type]
    await repo.add(_issue("a", IssueStatus.OPEN, IssuePriority.HIGH, 1))
    await repo.add(_issue("b", IssueStatus.OPEN, IssuePriority.LOW, 2))
    await repo.add(_issue("c", IssueStatus.COMPLETED, IssuePriority.HIGH, 3))

    assert [i.id for i in await repo.list(IssueFilters())] == ["c", "b", "a"]
    open_high = IssueFilters(status=IssueStatus.OPEN, priority=IssuePriority.HIGH)
    assert [i.id for i in await repo.list(open_high)] == ["a"]

    issue = await repo.get("a")
    assert issue is not None and issue.priority is IssuePriority.HIGH
    await repo.update(issue.with_changes(status=IssueStatus.IN_PROGRESS))
    assert client.data["issues"]["a"]["status"] == "in_progress"

    await repo.delete("b")
    assert await repo.get("b") is None


async def test_issue_counts(client: FakeClient) -> None:
    repo = FirestoreIssueRepository(client, "issues")  # type: ignore[arg-type]
    await repo.add(_issue("a", IssueStatus.OPEN, IssuePriority.HIGH, 1))
    await repo.add(_issue("b", IssueStatus.OPEN, IssuePriority.LOW, 2))
    await repo.add(_issue("c", IssueStatus.COMPLETED, IssuePriority.HIGH, 3))

    assert await repo.count_by_status() == {
        IssueStatus.OPEN: 2,
        IssueStatus.IN_PROGRESS: 0,
        IssueStatus.COMPLETED: 1,
    }
    matrix = await repo.count_by_status_and_priority()
    assert len(matrix) == 9
    assert matrix[(IssueStatus.OPEN, IssuePriority.LOW)] == 1
    assert matrix[(IssueStatus.COMPLETED, IssuePriority.HIGH)] == 1
    assert matrix[(IssueStatus.IN_PROGRESS, IssuePriority.MEDIUM)] == 0


async def test_revoked_tokens(client: FakeClient) -> None:
    repo = FirestoreRevokedTokenRepository(client, "revoked")  # type: ignore[arg-type]
    await repo.revoke("jti-1", datetime.now(UTC))
    assert await repo.is_revoked("jti-1") is True
    assert await repo.is_revoked("jti-2") is False


async def test_google_errors_are_translated(client: FakeClient, monkeypatch) -> None:  # noqa: ANN001
    repo = FirestoreIssueRepository(client, "issues")  # type: ignore[arg-type]

    async def boom(*_: Any, **__: Any) -> None:
        raise ServiceUnavailable("firestore caído")

    monkeypatch.setattr(_Doc, "get", boom)
    with pytest.raises(RepositoryError):
        await repo.get("x")
