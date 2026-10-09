"""Excepciones de dominio.

La capa de servicios lanza estas excepciones sin conocer HTTP; la capa API las
traduce a respuestas JSON homogéneas (ver ``app/api/error_handlers.py``).
"""


class AppError(Exception):
    """Error base de la aplicación."""

    status_code: int = 500
    code: str = "internal_error"
    message: str = "Ocurrió un error inesperado."

    def __init__(self, message: str | None = None, *, details: dict | None = None) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "El recurso solicitado no existe."


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "invalid_credentials"
    message = "Usuario o contraseña incorrectos."


class AuthenticationError(AppError):
    status_code = 401
    code = "not_authenticated"
    message = "Token inválido, expirado o ausente."


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    message = "No tiene permisos para realizar esta acción."


class BusinessRuleError(AppError):
    status_code = 422
    code = "business_rule_violation"
    message = "La operación no cumple las reglas de negocio."


class RepositoryError(AppError):
    status_code = 503
    code = "persistence_unavailable"
    message = "El servicio de persistencia no está disponible. Intente nuevamente."
