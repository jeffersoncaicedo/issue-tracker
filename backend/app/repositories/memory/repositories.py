"""Implementaciones en memoria (desarrollo local y pruebas automatizadas)."""

import asyncio
from datetime import UTC, datetime

from app.domain.models import Issue, IssueFilters, IssuePriority, IssueStatus, User
from app.repositories.base import IssueRepository, RevokedTokenRepository, UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}

    async def get_by_username(self, username: str) -> User | None:
        return next((u for u in self._by_id.values() if u.username == username), None)

    async def get_by_id(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)

    async def upsert(self, user: User) -> User:
        self._by_id[user.id] = user
        return user


class InMemoryIssueRepository(IssueRepository):
    def __init__(self) -> None:
        self._items: dict[str, Issue] = {}
        self._lock = asyncio.Lock()

    async def add(self, issue: Issue) -> Issue:
        async with self._lock:
            self._items[issue.id] = issue
        return issue

    async def get(self, issue_id: str) -> Issue | None:
        return self._items.get(issue_id)

    async def list(self, filters: IssueFilters) -> list[Issue]:
        result = [
            i
            for i in self._items.values()
            if (filters.status is None or i.status == filters.status)
            and (filters.priority is None or i.priority == filters.priority)
        ]
        return sorted(result, key=lambda i: i.created_at, reverse=True)

    async def update(self, issue: Issue) -> Issue:
        async with self._lock:
            self._items[issue.id] = issue
        return issue

    async def delete(self, issue_id: str) -> None:
        async with self._lock:
            self._items.pop(issue_id, None)

    async def count_by_status(self) -> dict[IssueStatus, int]:
        counts = dict.fromkeys(IssueStatus, 0)
        for issue in self._items.values():
            counts[issue.status] += 1
        return counts

    async def count_by_status_and_priority(
        self,
    ) -> dict[tuple[IssueStatus, IssuePriority], int]:
        counts = {(s, p): 0 for s in IssueStatus for p in IssuePriority}
        for issue in self._items.values():
            counts[(issue.status, issue.priority)] += 1
        return counts


class InMemoryRevokedTokenRepository(RevokedTokenRepository):
    def __init__(self) -> None:
        self._revoked: dict[str, datetime] = {}

    async def revoke(self, jti: str, expires_at: datetime) -> None:
        self._purge_expired()
        self._revoked[jti] = expires_at

    async def is_revoked(self, jti: str) -> bool:
        return jti in self._revoked

    def _purge_expired(self) -> None:
        now = datetime.now(UTC)
        self._revoked = {k: v for k, v in self._revoked.items() if v > now}
