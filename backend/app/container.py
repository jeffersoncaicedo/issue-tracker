"""Composition Root: construye y conecta las dependencias de la aplicación.

Es el único lugar que conoce las implementaciones concretas. El resto del
código depende de abstracciones (patrón *Dependency Injection*).
"""

import logging
import uuid
from dataclasses import dataclass

from app.core.config import RepositoryBackend, Settings
from app.core.security import TokenService, hash_password
from app.core.seed_data import DEMO_USERS
from app.domain.models import User
from app.repositories.base import IssueRepository, RevokedTokenRepository, UserRepository
from app.services.auth_service import AuthService
from app.services.issue_service import IssueService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Container:
    settings: Settings
    users: UserRepository
    issues: IssueRepository
    revoked_tokens: RevokedTokenRepository
    tokens: TokenService
    auth_service: AuthService
    issue_service: IssueService


def _build_repositories(
    settings: Settings,
) -> tuple[UserRepository, IssueRepository, RevokedTokenRepository]:
    if settings.repository_backend is RepositoryBackend.FIRESTORE:
        # Import diferido: el SDK de GCP solo se carga cuando se necesita.
        from google.cloud.firestore import AsyncClient

        from app.repositories.firestore.repositories import (
            FirestoreIssueRepository,
            FirestoreRevokedTokenRepository,
            FirestoreUserRepository,
        )

        client = AsyncClient(project=settings.gcp_project_id, database=settings.firestore_database)
        return (
            FirestoreUserRepository(client, settings.users_collection),
            FirestoreIssueRepository(client, settings.issues_collection),
            FirestoreRevokedTokenRepository(client, settings.revoked_tokens_collection),
        )

    from app.repositories.memory.repositories import (
        InMemoryIssueRepository,
        InMemoryRevokedTokenRepository,
        InMemoryUserRepository,
    )

    return InMemoryUserRepository(), InMemoryIssueRepository(), InMemoryRevokedTokenRepository()


def build_container(settings: Settings) -> Container:
    users, issues, revoked = _build_repositories(settings)
    tokens = TokenService(settings)
    return Container(
        settings=settings,
        users=users,
        issues=issues,
        revoked_tokens=revoked,
        tokens=tokens,
        auth_service=AuthService(users, revoked, tokens),
        issue_service=IssueService(issues),
    )


async def seed_demo_users(users: UserRepository) -> None:
    """Crea (o actualiza) las cuentas demo con su contraseña hasheada."""
    for demo in DEMO_USERS:
        existing = await users.get_by_username(demo["username"])
        await users.upsert(
            User(
                id=existing.id if existing else uuid.uuid4().hex,
                username=demo["username"],
                full_name=demo["full_name"],
                password_hash=hash_password(demo["password"]),
                role=demo["role"],
            )
        )
    logger.info("Usuarios demo disponibles: %d", len(DEMO_USERS))
