"""Primitivas de seguridad: hash de contraseñas y emisión/validación de JWT.

* Contraseñas: **Argon2id** (recomendado por OWASP). Nunca se almacenan en texto
  plano; solo se persiste el hash con su sal y parámetros embebidos.
* Tokens: JWT firmados con HMAC, con ``exp``, ``iat``, ``iss`` y ``jti`` (este
  último permite revocar el token en el logout).
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings
from app.core.exceptions import AuthenticationError

_password_hasher = PasswordHasher()  # Argon2id con parámetros por defecto seguros

# Hash "señuelo" para igualar tiempos cuando el usuario no existe y así
# evitar enumeración de usuarios por ataque de tiempo (timing attack).
_DUMMY_HASH = _password_hasher.hash("dummy-password-for-constant-time")


def hash_password(plain_password: str) -> str:
    """Genera el hash Argon2id de una contraseña."""
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """Verifica una contraseña en tiempo aproximadamente constante."""
    try:
        return _password_hasher.verify(password_hash or _DUMMY_HASH, plain_password) and (
            password_hash is not None
        )
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


@dataclass(frozen=True, slots=True)
class TokenPayload:
    """Claims relevantes extraídos de un JWT válido."""

    subject: str
    jti: str
    expires_at: datetime


class TokenService:
    """Encapsula la creación y validación de JWT (patrón *Service*)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def expires_in_seconds(self) -> int:
        return self._settings.access_token_expire_minutes * 60

    def create_access_token(self, subject: str, extra_claims: dict | None = None) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=self._settings.access_token_expire_minutes),
            "iss": self._settings.jwt_issuer,
            "jti": uuid.uuid4().hex,
            **(extra_claims or {}),
        }
        return jwt.encode(
            payload, self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm
        )

    def decode_access_token(self, token: str) -> TokenPayload:
        try:
            claims = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],  # lista explícita: evita "alg=none"
                issuer=self._settings.jwt_issuer,
                options={"require": ["exp", "iat", "sub", "jti", "iss"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError("La sesión expiró. Inicie sesión nuevamente.") from exc
        except jwt.PyJWTError as exc:
            raise AuthenticationError() from exc

        return TokenPayload(
            subject=claims["sub"],
            jti=claims["jti"],
            expires_at=datetime.fromtimestamp(claims["exp"], tz=UTC),
        )
