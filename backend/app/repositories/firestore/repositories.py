"""Implementaciones sobre Google Cloud Firestore (modo nativo).

Notas de diseño:
* Se usa ``AsyncClient`` para no bloquear el *event loop* de FastAPI.
* Los filtros por igualdad (estado/prioridad) no requieren índices compuestos.
  El orden por fecha se aplica en memoria para no exigir índices adicionales;
  si el volumen crece, ver ``firestore.indexes.json`` y paginar con cursores.
* El resumen usa **agregaciones COUNT** del lado del servidor: no descarga
  documentos y su costo es mínimo.
* Cualquier error de Google API se encapsula en ``RepositoryError`` para no
  filtrar detalles de infraestructura al cliente.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from google.api_core.exceptions import GoogleAPIError
from google.cloud.firestore import AsyncClient
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.exceptions import RepositoryError
from app.domain.models import Issue, IssueFilters, IssuePriority, IssueStatus, Role, User
from app.repositories.base import IssueRepository, RevokedTokenRepository, UserRepository

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def _wrap_google_errors(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Decorador que traduce errores de Google Cloud a errores de dominio."""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return await func(*args, **kwargs)
        except GoogleAPIError as exc:
            logger.exception("Error de Firestore en %s", func.__qualname__)
            raise RepositoryError() from exc

    return wrapper


# ---------------------------------------------------------------- mapeadores
def _issue_to_doc(issue: Issue) -> dict[str, Any]:
    return {
        "title": issue.title,
        "description": issue.description,
        "priority": issue.priority.value,
        "status": issue.status.value,
        "created_by": issue.created_by,
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
    }


def _doc_to_issue(doc_id: str, data: dict[str, Any]) -> Issue:
    return Issue(
        id=doc_id,
        title=data["title"],
        description=data.get("description", ""),
        priority=IssuePriority(data["priority"]),
        status=IssueStatus(data["status"]),
        created_by=data["created_by"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _doc_to_user(doc_id: str, data: dict[str, Any]) -> User:
    return User(
        id=doc_id,
        username=data["username"],
        full_name=data.get("full_name", data["username"]),
        password_hash=data["password_hash"],
        role=Role(data.get("role", Role.USER.value)),
        is_active=data.get("is_active", True),
    )


# ------------------------------------------------------------- repositorios
class FirestoreUserRepository(UserRepository):
    def __init__(self, client: AsyncClient, collection: str) -> None:
        self._col = client.collection(collection)

    @_wrap_google_errors
    async def get_by_username(self, username: str) -> User | None:
        query = self._col.where(filter=FieldFilter("username", "==", username)).limit(1)
        async for doc in query.stream():
            return _doc_to_user(doc.id, doc.to_dict() or {})
        return None

    @_wrap_google_errors
    async def get_by_id(self, user_id: str) -> User | None:
        snapshot = await self._col.document(user_id).get()
        return _doc_to_user(snapshot.id, snapshot.to_dict() or {}) if snapshot.exists else None

    @_wrap_google_errors
    async def upsert(self, user: User) -> User:
        await self._col.document(user.id).set(
            {
                "username": user.username,
                "full_name": user.full_name,
                "password_hash": user.password_hash,
                "role": user.role.value,
                "is_active": user.is_active,
            }
        )
        return user


class FirestoreIssueRepository(IssueRepository):
    def __init__(self, client: AsyncClient, collection: str) -> None:
        self._col = client.collection(collection)

    @_wrap_google_errors
    async def add(self, issue: Issue) -> Issue:
        await self._col.document(issue.id).set(_issue_to_doc(issue))
        return issue

    @_wrap_google_errors
    async def get(self, issue_id: str) -> Issue | None:
        snapshot = await self._col.document(issue_id).get()
        return _doc_to_issue(snapshot.id, snapshot.to_dict() or {}) if snapshot.exists else None

    @_wrap_google_errors
    async def list(self, filters: IssueFilters) -> list[Issue]:
        query: Any = self._col
        if filters.status:
            query = query.where(filter=FieldFilter("status", "==", filters.status.value))
        if filters.priority:
            query = query.where(filter=FieldFilter("priority", "==", filters.priority.value))
        issues = [_doc_to_issue(doc.id, doc.to_dict() or {}) async for doc in query.stream()]
        return sorted(issues, key=lambda i: i.created_at, reverse=True)

    @_wrap_google_errors
    async def update(self, issue: Issue) -> Issue:
        await self._col.document(issue.id).update(
            {
                "status": issue.status.value,
                "priority": issue.priority.value,
                "updated_at": issue.updated_at,
            }
        )
        return issue

    @_wrap_google_errors
    async def delete(self, issue_id: str) -> None:
        await self._col.document(issue_id).delete()

    @_wrap_google_errors
    async def count_by_status(self) -> dict[IssueStatus, int]:
        results = await asyncio.gather(*(self._count(("status", s.value)) for s in IssueStatus))
        return dict(zip(IssueStatus, results, strict=True))

    @_wrap_google_errors
    async def count_by_status_and_priority(
        self,
    ) -> dict[tuple[IssueStatus, IssuePriority], int]:
        # 9 agregaciones COUNT en paralelo: no se descarga ningún documento.
        pairs = [(s, p) for s in IssueStatus for p in IssuePriority]
        results = await asyncio.gather(
            *(self._count(("status", s.value), ("priority", p.value)) for s, p in pairs)
        )
        return dict(zip(pairs, results, strict=True))

    async def _count(self, *equalities: tuple[str, str]) -> int:
        query: Any = self._col
        for field, value in equalities:
            query = query.where(filter=FieldFilter(field, "==", value))
        result = await query.count(alias="total").get()
        return int(result[0][0].value)


class FirestoreRevokedTokenRepository(RevokedTokenRepository):
    """Lista de revocación de JWT.

    Configurar una política TTL de Firestore sobre el campo ``expires_at`` para
    que los registros se eliminen solos cuando el token ya habría expirado.
    """

    def __init__(self, client: AsyncClient, collection: str) -> None:
        self._col = client.collection(collection)

    @_wrap_google_errors
    async def revoke(self, jti: str, expires_at: datetime) -> None:
        await self._col.document(jti).set({"expires_at": expires_at})

    @_wrap_google_errors
    async def is_revoked(self, jti: str) -> bool:
        snapshot = await self._col.document(jti).get()
        return bool(snapshot.exists)
