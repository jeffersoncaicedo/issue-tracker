"""DTOs de incidencias (contrato público del API)."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.models import Issue, IssuePriority, IssueStats, IssueStatus, IssueSummary


class IssueCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Error al exportar reporte",
                "description": "El botón Exportar devuelve un error 500.",
                "priority": "high",
            }
        },
    )

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2000)
    priority: IssuePriority


class IssueUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": "in_progress", "priority": "medium"}},
    )

    status: IssueStatus | None = None
    priority: IssuePriority | None = None

    @model_validator(mode="after")
    def _at_least_one_field(self) -> Self:
        if self.status is None and self.priority is None:
            raise ValueError("Debe indicar 'status' y/o 'priority'.")
        return self


class IssueOut(BaseModel):
    id: str
    title: str
    description: str
    priority: IssuePriority
    status: IssueStatus
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, issue: Issue) -> "IssueOut":
        return cls(
            id=issue.id,
            title=issue.title,
            description=issue.description,
            priority=issue.priority,
            status=issue.status,
            created_by=issue.created_by,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
        )


class IssueSummaryOut(BaseModel):
    total: int
    open: int
    in_progress: int
    completed: int

    @classmethod
    def from_domain(cls, summary: IssueSummary) -> "IssueSummaryOut":
        return cls(
            total=summary.total,
            open=summary.by_status[IssueStatus.OPEN],
            in_progress=summary.by_status[IssueStatus.IN_PROGRESS],
            completed=summary.by_status[IssueStatus.COMPLETED],
        )


class IssueStatsOut(BaseModel):
    total: int
    by_status: dict[IssueStatus, int]
    by_priority: dict[IssuePriority, int]
    matrix: dict[IssueStatus, dict[IssuePriority, int]] = Field(
        description="Conteo cruzado estado → prioridad"
    )

    @classmethod
    def from_domain(cls, stats: IssueStats) -> "IssueStatsOut":
        return cls(
            total=stats.total,
            by_status=stats.by_status,
            by_priority=stats.by_priority,
            matrix=stats.matrix,
        )
