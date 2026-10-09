"""Endpoints de incidencias. Todos requieren un JWT válido."""

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, IssueServiceDep
from app.domain.models import IssueFilters, IssuePriority, IssueStatus
from app.schemas.error import ErrorResponse
from app.schemas.issue import (
    IssueCreate,
    IssueOut,
    IssueStatsOut,
    IssueSummaryOut,
    IssueUpdate,
)

router = APIRouter(
    prefix="/issues",
    tags=["Incidencias"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)


@router.get("", response_model=list[IssueOut], summary="Listar incidencias (con filtros)")
async def list_issues(
    _: CurrentUser,
    service: IssueServiceDep,
    status_filter: IssueStatus | None = Query(default=None, alias="status"),
    priority: IssuePriority | None = Query(default=None),
) -> list[IssueOut]:
    issues = await service.list(IssueFilters(status=status_filter, priority=priority))
    return [IssueOut.from_domain(i) for i in issues]


@router.post(
    "",
    response_model=IssueOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear incidencia",
)
async def create_issue(body: IssueCreate, user: CurrentUser, service: IssueServiceDep) -> IssueOut:
    issue = await service.create(
        title=body.title, description=body.description, priority=body.priority, author=user
    )
    return IssueOut.from_domain(issue)


# Debe declararse ANTES de "/{issue_id}" para que no se interprete como un id.
@router.get("/summary", response_model=IssueSummaryOut, summary="Resumen por estado")
async def summary(_: CurrentUser, service: IssueServiceDep) -> IssueSummaryOut:
    return IssueSummaryOut.from_domain(await service.summary())


@router.get(
    "/stats",
    response_model=IssueStatsOut,
    summary="Estadísticas por estado y prioridad (Administrador / Soporte)",
)
async def stats(user: CurrentUser, service: IssueServiceDep) -> IssueStatsOut:
    return IssueStatsOut.from_domain(await service.stats(actor=user))


@router.get(
    "/{issue_id}",
    response_model=IssueOut,
    summary="Detalle de una incidencia",
    responses={404: {"model": ErrorResponse}},
)
async def get_issue(issue_id: str, _: CurrentUser, service: IssueServiceDep) -> IssueOut:
    return IssueOut.from_domain(await service.get(issue_id))


@router.patch(
    "/{issue_id}",
    response_model=IssueOut,
    summary="Actualizar estado y/o prioridad",
    responses={404: {"model": ErrorResponse}},
)
async def update_issue(
    issue_id: str, body: IssueUpdate, user: CurrentUser, service: IssueServiceDep
) -> IssueOut:
    issue = await service.update(issue_id, actor=user, status=body.status, priority=body.priority)
    return IssueOut.from_domain(issue)


@router.post(
    "/{issue_id}/resolve",
    response_model=IssueOut,
    summary="Dar por resuelta (Administrador / Soporte)",
    responses={404: {"model": ErrorResponse}},
)
async def resolve_issue(issue_id: str, user: CurrentUser, service: IssueServiceDep) -> IssueOut:
    return IssueOut.from_domain(await service.resolve(issue_id, actor=user))


@router.delete(
    "/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar incidencia (Administrador / Soporte)",
    responses={404: {"model": ErrorResponse}},
)
async def delete_issue(issue_id: str, user: CurrentUser, service: IssueServiceDep) -> None:
    await service.delete(issue_id, actor=user)
