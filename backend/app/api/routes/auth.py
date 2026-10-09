"""Endpoints de autenticación."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, BearerToken, CurrentUser
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.schemas.error import ErrorResponse

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    responses={401: {"model": ErrorResponse}},
)
async def login(body: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    result = await auth_service.login(body.username, body.password)
    return TokenResponse(
        access_token=result.access_token,
        expires_in=result.expires_in,
        user=UserOut.from_domain(result.user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión (revoca el token actual)",
    responses={401: {"model": ErrorResponse}},
)
async def logout(token: BearerToken, _: CurrentUser, auth_service: AuthServiceDep) -> None:
    await auth_service.logout(token)


@router.get("/me", response_model=UserOut, summary="Usuario autenticado")
async def me(user: CurrentUser) -> UserOut:
    return UserOut.from_domain(user)
