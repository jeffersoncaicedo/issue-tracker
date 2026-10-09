"""Traducción centralizada de excepciones a respuestas JSON homogéneas.

Formato: ``{"error": {"code": str, "message": str, "details": any}}``.
Los errores no controlados se registran con traza completa, pero al cliente
solo se le devuelve un mensaje genérico (no se filtran detalles internos).
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError, AuthenticationError, InvalidCredentialsError

logger = logging.getLogger(__name__)


def _error(status_code: int, code: str, message: str, details=None, headers=None) -> JSONResponse:  # noqa: ANN001
    body = {"error": {"code": code, "message": message, "details": details}}
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body), headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = (
            {"WWW-Authenticate": "Bearer"}
            if isinstance(exc, AuthenticationError | InvalidCredentialsError)
            else None
        )
        return _error(exc.status_code, exc.code, exc.message, exc.details or None, headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "Los datos enviados no son válidos.",
            details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return _error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "Ocurrió un error inesperado. Intente más tarde.",
        )
