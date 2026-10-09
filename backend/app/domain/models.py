"""Entidades y enumeraciones del dominio (sin dependencias de frameworks)."""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum


def utc_now() -> datetime:
    return datetime.now(UTC)


class IssueStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Role(StrEnum):
    """Roles de usuario. Los permisos de cada rol se definen en ``permissions.py``."""

    ADMIN = "admin"
    SUPPORT = "support"
    USER = "user"


class IssuePriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class User:
    id: str
    username: str
    full_name: str
    password_hash: str
    role: Role = Role.USER
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class Issue:
    id: str
    title: str
    description: str
    priority: IssuePriority
    created_by: str
    status: IssueStatus = IssueStatus.OPEN
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def with_changes(
        self, *, status: IssueStatus | None = None, priority: IssuePriority | None = None
    ) -> "Issue":
        """Devuelve una copia inmutable con los cambios aplicados."""
        return replace(
            self,
            status=status or self.status,
            priority=priority or self.priority,
            updated_at=utc_now(),
        )


@dataclass(frozen=True, slots=True)
class IssueFilters:
    status: IssueStatus | None = None
    priority: IssuePriority | None = None


@dataclass(frozen=True, slots=True)
class IssueSummary:
    total: int
    by_status: dict[IssueStatus, int]


@dataclass(frozen=True, slots=True)
class IssueStats:
    """Estadísticas detalladas para la vista de resumen (estado x prioridad)."""

    total: int
    by_status: dict[IssueStatus, int]
    by_priority: dict[IssuePriority, int]
    matrix: dict[IssueStatus, dict[IssuePriority, int]]
