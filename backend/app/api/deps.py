"""Dependencias de FastAPI (inyección de servicios y usuario autenticado)."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import Container
from app.core.exceptions import AuthenticationError
from app.domain.models import User
from app.services.auth_service import AuthService
from app.services.issue_service import IssueService

_bearer = HTTPBearer(auto_error=False, description="JWT obtenido en /auth/login")


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_auth_service(container: Annotated[Container, Depends(get_container)]) -> AuthService:
    return container.auth_service


def get_issue_service(container: Annotated[Container, Depends(get_container)]) -> IssueService:
    return container.issue_service


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError()
    return credentials.credentials


async def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    return await auth_service.get_user_from_token(token)


CurrentUser = Annotated[User, Depends(get_current_user)]
BearerToken = Annotated[str, Depends(get_bearer_token)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
IssueServiceDep = Annotated[IssueService, Depends(get_issue_service)]
