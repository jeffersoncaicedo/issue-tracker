"""Punto de entrada de la aplicación FastAPI (patrón *Application Factory*)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_error_handlers
from app.api.middleware import SecurityHeadersMiddleware
from app.api.routes import auth, issues
from app.container import Container, build_container, seed_demo_users
from app.core.config import RepositoryBackend, Settings, get_settings
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    container = container or build_container(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # En memoria los datos se pierden al reiniciar: se recargan los usuarios demo.
        # En Firestore los usuarios se cargan una sola vez con scripts/seed_users.py.
        if settings.seed_demo_users and settings.repository_backend is RepositoryBackend.MEMORY:
            await seed_demo_users(container.users)
        yield

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API REST para la gestión de incidencias (Issue Tracker).",
        lifespan=lifespan,
        # La documentación interactiva no se expone en producción.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.state.container = container

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,  # el JWT viaja en la cabecera Authorization, no en cookies
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )
    register_error_handlers(app)

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(issues.router, prefix=settings.api_prefix)

    @app.get("/health", tags=["Salud"], summary="Verificación de disponibilidad")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
