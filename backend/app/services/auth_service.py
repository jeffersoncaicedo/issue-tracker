"""Casos de uso de autenticación: login, logout y resolución del usuario actual."""

import logging
from dataclasses import dataclass

from app.core.exceptions import AuthenticationError, InvalidCredentialsError
from app.core.security import TokenService, verify_password
from app.domain.models import User
from app.repositories.base import RevokedTokenRepository, UserRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AuthResult:
    access_token: str
    expires_in: int
    user: User


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        revoked_tokens: RevokedTokenRepository,
        tokens: TokenService,
    ) -> None:
        self._users = users
        self._revoked = revoked_tokens
        self._tokens = tokens

    async def login(self, username: str, password: str) -> AuthResult:
        user = await self._users.get_by_username(username.strip().lower())
        # verify_password se ejecuta SIEMPRE para no revelar si el usuario existe.
        password_ok = verify_password(password, user.password_hash if user else None)
        if user is None or not password_ok or not user.is_active:
            logger.warning("Intento de inicio de sesión fallido")
            raise InvalidCredentialsError()

        token = self._tokens.create_access_token(user.id, {"username": user.username})
        logger.info("Inicio de sesión exitoso user_id=%s", user.id)
        return AuthResult(token, self._tokens.expires_in_seconds, user)

    async def logout(self, token: str) -> None:
        payload = self._tokens.decode_access_token(token)
        await self._revoked.revoke(payload.jti, payload.expires_at)
        logger.info("Sesión cerrada user_id=%s", payload.subject)

    async def get_user_from_token(self, token: str) -> User:
        payload = self._tokens.decode_access_token(token)
        if await self._revoked.is_revoked(payload.jti):
            raise AuthenticationError("La sesión fue cerrada. Inicie sesión nuevamente.")
        user = await self._users.get_by_id(payload.subject)
        if user is None or not user.is_active:
            raise AuthenticationError()
        return user
