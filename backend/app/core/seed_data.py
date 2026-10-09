"""Usuarios de demostración.

El examen no exige alta/baja de usuarios, por lo que se proveen cuentas
predefinidas. Las contraseñas se **hashean con Argon2id antes de persistirse**;
el texto plano solo existe aquí para poder documentarlas en el README.
"""

from typing import TypedDict

from app.domain.models import Role


class DemoUser(TypedDict):
    username: str
    full_name: str
    password: str
    role: Role


DEMO_USERS: list[DemoUser] = [
    {
        "username": "admin",
        "full_name": "Jefferson Caicedo",
        "password": "Admin#2026",
        "role": Role.ADMIN,
    },
    {
        "username": "soporte",
        "full_name": "Servicio Soporte",
        "password": "Soporte#2026",
        "role": Role.SUPPORT,
    },
    {
        "username": "analista",
        "full_name": "Usuario Analista",
        "password": "Analista#2026",
        "role": Role.USER,
    },
]
