"""Control de acceso basado en roles (RBAC).

Los roles se traducen a **permisos** y el código solo pregunta por permisos
(``user.can(Permission.DELETE_ISSUE)``), nunca por roles concretos. Así, dar o
quitar una capacidad a un rol es un cambio de una sola línea en ``ROLE_PERMISSIONS``.
"""

from enum import StrEnum

from app.domain.models import Role, User


class Permission(StrEnum):
    RESOLVE_ISSUE = "issues:resolve"  # Marcar como completada o reabrir una completada
    DELETE_ISSUE = "issues:delete"
    VIEW_STATS = "stats:view"  # Vista de resumen con gráficos


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.SUPPORT: frozenset(Permission),
    Role.USER: frozenset(),
}


def permissions_of(user: User) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get(user.role, frozenset())


def has_permission(user: User, permission: Permission) -> bool:
    return permission in permissions_of(user)
