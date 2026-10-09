"""Casos de uso de incidencias.

Las reglas de autorización viven aquí (y no solo en los routers) porque son
reglas de negocio: se cumplen sin importar desde dónde se invoque el caso de uso.
"""

import logging
import uuid

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.domain.models import (
    Issue,
    IssueFilters,
    IssuePriority,
    IssueStats,
    IssueStatus,
    IssueSummary,
    User,
)
from app.domain.permissions import Permission, has_permission
from app.repositories.base import IssueRepository

logger = logging.getLogger(__name__)


class IssueService:
    def __init__(self, issues: IssueRepository) -> None:
        self._issues = issues

    async def create(
        self, *, title: str, description: str, priority: IssuePriority, author: User
    ) -> Issue:
        clean_title = title.strip()
        if not clean_title:
            raise BusinessRuleError("El título no puede estar vacío.")

        issue = Issue(
            id=uuid.uuid4().hex,
            title=clean_title,
            description=description.strip(),
            priority=priority,
            created_by=author.username,
        )
        await self._issues.add(issue)
        logger.info("Incidencia creada id=%s por=%s", issue.id, author.username)
        return issue

    async def list(self, filters: IssueFilters) -> list[Issue]:
        return await self._issues.list(filters)

    async def get(self, issue_id: str) -> Issue:
        issue = await self._issues.get(issue_id)
        if issue is None:
            raise NotFoundError(f"La incidencia '{issue_id}' no existe.")
        return issue

    async def update(
        self,
        issue_id: str,
        *,
        actor: User,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
    ) -> Issue:
        if status is None and priority is None:
            raise BusinessRuleError("Indique al menos el estado o la prioridad a actualizar.")

        current = await self.get(issue_id)
        self._ensure_can_update(actor, current, status)

        updated = current.with_changes(status=status, priority=priority)
        await self._issues.update(updated)
        logger.info(
            "Incidencia actualizada id=%s estado=%s prioridad=%s por=%s",
            issue_id,
            updated.status,
            updated.priority,
            actor.username,
        )
        return updated

    async def resolve(self, issue_id: str, *, actor: User) -> Issue:
        """Atajo de negocio: dar la incidencia por resuelta (estado completado)."""
        return await self.update(issue_id, actor=actor, status=IssueStatus.COMPLETED)

    async def delete(self, issue_id: str, *, actor: User) -> None:
        if not has_permission(actor, Permission.DELETE_ISSUE):
            raise ForbiddenError("Solo Administrador o Soporte pueden eliminar incidencias.")
        await self.get(issue_id)  # 404 si no existe
        await self._issues.delete(issue_id)
        logger.warning("Incidencia eliminada id=%s por=%s", issue_id, actor.username)

    async def summary(self) -> IssueSummary:
        counts = await self._issues.count_by_status()
        by_status = {status: counts.get(status, 0) for status in IssueStatus}
        return IssueSummary(total=sum(by_status.values()), by_status=by_status)

    async def stats(self, *, actor: User) -> IssueStats:
        if not has_permission(actor, Permission.VIEW_STATS):
            raise ForbiddenError("Solo Administrador o Soporte pueden ver el resumen detallado.")
        counts = await self._issues.count_by_status_and_priority()
        matrix = {s: {p: counts.get((s, p), 0) for p in IssuePriority} for s in IssueStatus}
        by_status = {s: sum(matrix[s].values()) for s in IssueStatus}
        by_priority = {p: sum(matrix[s][p] for s in IssueStatus) for p in IssuePriority}
        return IssueStats(
            total=sum(by_status.values()),
            by_status=by_status,
            by_priority=by_priority,
            matrix=matrix,
        )

    @staticmethod
    def _ensure_can_update(actor: User, current: Issue, status: IssueStatus | None) -> None:
        """Un usuario sin permiso de resolución no puede cerrar ni tocar incidencias cerradas."""
        if has_permission(actor, Permission.RESOLVE_ISSUE):
            return
        if current.status is IssueStatus.COMPLETED:
            raise ForbiddenError(
                "Solo Administrador o Soporte pueden modificar una incidencia completada."
            )
        if status is IssueStatus.COMPLETED:
            raise ForbiddenError(
                "Solo Administrador o Soporte pueden dar por resuelta una incidencia."
            )
