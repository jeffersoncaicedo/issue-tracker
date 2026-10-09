"""Contratos (puertos) de persistencia — patrón *Repository*.

Los servicios dependen de estas abstracciones, no de Firestore. Esto permite
cambiar de motor (SQL, NoSQL) o usar dobles en memoria para las pruebas sin
tocar la lógica de negocio (Inversión de Dependencias, SOLID).
"""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models import Issue, IssueFilters, IssuePriority, IssueStatus, User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def upsert(self, user: User) -> User: ...


class IssueRepository(ABC):
    @abstractmethod
    async def add(self, issue: Issue) -> Issue: ...

    @abstractmethod
    async def get(self, issue_id: str) -> Issue | None: ...

    @abstractmethod
    async def list(self, filters: IssueFilters) -> list[Issue]:
        """Devuelve incidencias ordenadas de la más reciente a la más antigua."""

    @abstractmethod
    async def update(self, issue: Issue) -> Issue: ...

    @abstractmethod
    async def delete(self, issue_id: str) -> None: ...

    @abstractmethod
    async def count_by_status(self) -> dict[IssueStatus, int]: ...

    @abstractmethod
    async def count_by_status_and_priority(
        self,
    ) -> dict[tuple[IssueStatus, IssuePriority], int]: ...


class RevokedTokenRepository(ABC):
    @abstractmethod
    async def revoke(self, jti: str, expires_at: datetime) -> None: ...

    @abstractmethod
    async def is_revoked(self, jti: str) -> bool: ...
