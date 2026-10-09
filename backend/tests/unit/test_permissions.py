"""Pruebas de la matriz de roles y permisos (RBAC)."""

import pytest

from app.domain.models import Role, User
from app.domain.permissions import Permission, has_permission, permissions_of


def _user(role: Role) -> User:
    return User(id="x", username="x", full_name="x", password_hash="x", role=role)


@pytest.mark.parametrize("role", [Role.ADMIN, Role.SUPPORT])
def test_admin_and_support_have_every_permission(role: Role) -> None:
    assert permissions_of(_user(role)) == frozenset(Permission)


@pytest.mark.parametrize("permission", list(Permission))
def test_regular_user_has_no_elevated_permission(permission: Permission) -> None:
    assert has_permission(_user(Role.USER), permission) is False


def test_user_role_defaults_to_regular_user() -> None:
    assert User(id="x", username="x", full_name="x", password_hash="x").role is Role.USER
