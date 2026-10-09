"""Carga los usuarios demo en Firestore (ejecutar una sola vez por entorno).

Uso:
    REPOSITORY_BACKEND=firestore GCP_PROJECT_ID=<proyecto> python -m scripts.seed_users

Las contraseñas se guardan como hash Argon2id, nunca en texto plano.
"""

import asyncio

from app.container import build_container, seed_demo_users
from app.core.config import RepositoryBackend, get_settings


async def main() -> None:
    settings = get_settings()
    if settings.repository_backend is not RepositoryBackend.FIRESTORE:
        raise SystemExit("Configure REPOSITORY_BACKEND=firestore para ejecutar este script.")
    container = build_container(settings)
    await seed_demo_users(container.users)
    print("Usuarios demo cargados en Firestore.")  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
