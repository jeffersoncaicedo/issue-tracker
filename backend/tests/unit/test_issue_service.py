"""Pruebas unitarias del servicio de incidencias (incluidas las reglas de autorización)."""

import pytest

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.domain.models import IssueFilters, IssuePriority, IssueStatus, Role, User
from app.repositories.memory.repositories import InMemoryIssueRepository
from app.services.issue_service import IssueService

ADMIN = User(id="u1", username="admin", full_name="Admin", password_hash="x", role=Role.ADMIN)
SUPPORT = User(id="u2", username="soporte", full_name="S", password_hash="x", role=Role.SUPPORT)
USER = User(id="u3", username="analista", full_name="A", password_hash="x", role=Role.USER)


@pytest.fixture
def service() -> IssueService:
    return IssueService(InMemoryIssueRepository())


async def _create(service: IssueService, title: str = "Bug", priority=IssuePriority.HIGH):  # noqa: ANN001, ANN202
    return await service.create(title=title, description="desc", priority=priority, author=ADMIN)


# ------------------------------------------------------------------ creación
async def test_create_sets_defaults(service: IssueService) -> None:
    issue = await _create(service, "  Error en login  ")
    assert issue.title == "Error en login"
    assert issue.status is IssueStatus.OPEN
    assert issue.created_by == "admin"


async def test_create_rejects_blank_title(service: IssueService) -> None:
    with pytest.raises(BusinessRuleError):
        await _create(service, "   ")


async def test_get_unknown_issue_raises_not_found(service: IssueService) -> None:
    with pytest.raises(NotFoundError):
        await service.get("missing")


# ------------------------------------------------------------------ listado
async def test_list_returns_newest_first(service: IssueService) -> None:
    first = await _create(service, "Primera")
    second = await _create(service, "Segunda")
    assert [i.id for i in await service.list(IssueFilters())] == [second.id, first.id]


async def test_list_filters_by_status_and_priority(service: IssueService) -> None:
    high = await _create(service, "Alta", IssuePriority.HIGH)
    await _create(service, "Baja", IssuePriority.LOW)
    await service.update(high.id, actor=USER, status=IssueStatus.IN_PROGRESS)

    assert [i.title for i in await service.list(IssueFilters(priority=IssuePriority.LOW))] == [
        "Baja"
    ]
    assert [i.title for i in await service.list(IssueFilters(status=IssueStatus.IN_PROGRESS))] == [
        "Alta"
    ]
    combined = IssueFilters(status=IssueStatus.OPEN, priority=IssuePriority.HIGH)
    assert await service.list(combined) == []


# ------------------------------------------------------------------ actualización
@pytest.mark.parametrize("actor", [ADMIN, SUPPORT])
async def test_privileged_users_can_complete(service: IssueService, actor: User) -> None:
    issue = await _create(service)
    updated = await service.update(
        issue.id, actor=actor, status=IssueStatus.COMPLETED, priority=IssuePriority.LOW
    )
    assert updated.status is IssueStatus.COMPLETED
    assert updated.priority is IssuePriority.LOW
    assert updated.updated_at >= issue.updated_at


async def test_regular_user_can_move_to_in_progress_and_change_priority(
    service: IssueService,
) -> None:
    issue = await _create(service)
    updated = await service.update(
        issue.id, actor=USER, status=IssueStatus.IN_PROGRESS, priority=IssuePriority.MEDIUM
    )
    assert updated.status is IssueStatus.IN_PROGRESS
    assert updated.priority is IssuePriority.MEDIUM


async def test_regular_user_cannot_complete(service: IssueService) -> None:
    issue = await _create(service)
    with pytest.raises(ForbiddenError, match="resuelta"):
        await service.update(issue.id, actor=USER, status=IssueStatus.COMPLETED)
    assert (await service.get(issue.id)).status is IssueStatus.OPEN


async def test_regular_user_cannot_touch_completed_issue(service: IssueService) -> None:
    issue = await _create(service)
    await service.resolve(issue.id, actor=SUPPORT)
    with pytest.raises(ForbiddenError, match="completada"):
        await service.update(issue.id, actor=USER, status=IssueStatus.OPEN)
    with pytest.raises(ForbiddenError):
        await service.update(issue.id, actor=USER, priority=IssuePriority.LOW)


async def test_privileged_user_can_reopen(service: IssueService) -> None:
    issue = await _create(service)
    await service.resolve(issue.id, actor=ADMIN)
    reopened = await service.update(issue.id, actor=SUPPORT, status=IssueStatus.OPEN)
    assert reopened.status is IssueStatus.OPEN


async def test_update_only_priority_keeps_status(service: IssueService) -> None:
    issue = await _create(service)
    updated = await service.update(issue.id, actor=USER, priority=IssuePriority.MEDIUM)
    assert updated.status is IssueStatus.OPEN


async def test_update_without_fields_raises(service: IssueService) -> None:
    issue = await _create(service)
    with pytest.raises(BusinessRuleError):
        await service.update(issue.id, actor=ADMIN)


async def test_update_unknown_issue_raises_not_found(service: IssueService) -> None:
    with pytest.raises(NotFoundError):
        await service.update("missing", actor=ADMIN, status=IssueStatus.COMPLETED)


# ------------------------------------------------------------------ resolver / eliminar
async def test_resolve_marks_completed(service: IssueService) -> None:
    issue = await _create(service)
    assert (await service.resolve(issue.id, actor=SUPPORT)).status is IssueStatus.COMPLETED


async def test_regular_user_cannot_resolve(service: IssueService) -> None:
    issue = await _create(service)
    with pytest.raises(ForbiddenError):
        await service.resolve(issue.id, actor=USER)


@pytest.mark.parametrize("actor", [ADMIN, SUPPORT])
async def test_privileged_users_can_delete(service: IssueService, actor: User) -> None:
    issue = await _create(service)
    await service.delete(issue.id, actor=actor)
    with pytest.raises(NotFoundError):
        await service.get(issue.id)


async def test_regular_user_cannot_delete(service: IssueService) -> None:
    issue = await _create(service)
    with pytest.raises(ForbiddenError):
        await service.delete(issue.id, actor=USER)
    assert await service.get(issue.id)


async def test_delete_unknown_issue_raises_not_found(service: IssueService) -> None:
    with pytest.raises(NotFoundError):
        await service.delete("missing", actor=ADMIN)


# ------------------------------------------------------------------ resumen y estadísticas
async def test_summary_counts_by_status(service: IssueService) -> None:
    a = await _create(service)
    b = await _create(service)
    await _create(service)
    await service.update(a.id, actor=ADMIN, status=IssueStatus.IN_PROGRESS)
    await service.resolve(b.id, actor=ADMIN)

    summary = await service.summary()
    assert summary.total == 3
    assert summary.by_status == {
        IssueStatus.OPEN: 1,
        IssueStatus.IN_PROGRESS: 1,
        IssueStatus.COMPLETED: 1,
    }


async def test_summary_empty(service: IssueService) -> None:
    summary = await service.summary()
    assert summary.total == 0
    assert all(v == 0 for v in summary.by_status.values())


async def test_stats_cross_counts(service: IssueService) -> None:
    a = await _create(service, "A", IssuePriority.HIGH)
    await _create(service, "B", IssuePriority.HIGH)
    await _create(service, "C", IssuePriority.LOW)
    await service.resolve(a.id, actor=ADMIN)

    stats = await service.stats(actor=SUPPORT)
    assert stats.total == 3
    assert stats.by_status[IssueStatus.OPEN] == 2
    assert stats.by_priority == {
        IssuePriority.HIGH: 2,
        IssuePriority.MEDIUM: 0,
        IssuePriority.LOW: 1,
    }
    assert stats.matrix[IssueStatus.COMPLETED][IssuePriority.HIGH] == 1
    assert stats.matrix[IssueStatus.OPEN][IssuePriority.LOW] == 1


async def test_regular_user_cannot_view_stats(service: IssueService) -> None:
    with pytest.raises(ForbiddenError):
        await service.stats(actor=USER)
