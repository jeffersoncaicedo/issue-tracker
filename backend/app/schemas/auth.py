"""DTOs de autenticación (contrato público del API)."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import Role, User
from app.domain.permissions import Permission, permissions_of


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"example": {"username": "admin", "password": "Admin#2026"}},
    )

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: str
    username: str
    full_name: str
    role: Role
    permissions: list[Permission] = Field(
        description="Capacidades del usuario; el frontend las usa para mostrar u ocultar acciones."
    )

    @classmethod
    def from_domain(cls, user: User) -> "UserOut":
        return cls(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            permissions=sorted(permissions_of(user)),
        )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - tipo de token, no es una contraseña
    expires_in: int = Field(description="Vigencia del token en segundos")
    user: UserOut
