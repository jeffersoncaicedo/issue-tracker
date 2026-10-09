# Issue Tracker API (backend)

API REST con **FastAPI** sobre **Python 3.12**, persistencia en **Google Firestore**, autenticación
**JWT** y contraseñas con hash **Argon2id**. Se despliega como contenedor en **Cloud Run**.

## Estructura

```
backend/
├── app/
│   ├── main.py                 # Application factory: middlewares, CORS, routers, lifespan
│   ├── container.py            # Composition root (inyección de dependencias) + carga de usuarios demo
│   ├── core/
│   │   ├── config.py           # Configuración tipada desde variables de entorno (pydantic-settings)
│   │   ├── security.py         # Argon2id + TokenService (JWT)
│   │   ├── exceptions.py       # Excepciones de dominio (sin dependencia de HTTP)
│   │   ├── logging.py          # Logs JSON compatibles con Cloud Logging
│   │   └── seed_data.py        # Usuarios demo
│   ├── domain/
│   │   ├── models.py           # Entidades inmutables y enums (incluye Role)
│   │   └── permissions.py      # RBAC: permisos por rol
│   ├── repositories/
│   │   ├── base.py             # Interfaces (puertos)
│   │   ├── memory/             # Implementación en memoria (local y pruebas)
│   │   └── firestore/          # Implementación Firestore (producción)
│   ├── services/               # Casos de uso y reglas de autorización: AuthService, IssueService
│   ├── schemas/                # DTOs de entrada/salida y formato de error
│   └── api/                    # Routers, dependencias, manejadores de error, middleware
├── scripts/seed_users.py       # Carga los usuarios demo en Firestore
├── tests/
│   ├── unit/                   # Seguridad, permisos, servicios, repositorios (memoria y Firestore)
│   ├── integration/            # Endpoints vía TestClient, incluida la autorización por rol
│   └── acceptance/             # UAT automatizadas (historias de usuario)
├── Dockerfile                  # Imagen multi-etapa, usuario sin privilegios
├── .env.example                # Plantilla de configuración
├── requirements.txt / requirements-dev.txt
└── pyproject.toml              # Configuración de pytest, coverage y ruff
```

## Ejecución local

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"   # pegar en JWT_SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs · ReDoc: http://localhost:8000/redoc
- Con `REPOSITORY_BACKEND=memory` los datos viven en memoria y los usuarios demo se cargan al iniciar.
- Para usar Firestore en local: `REPOSITORY_BACKEND=firestore`, `GCP_PROJECT_ID=<proyecto>` y
  credenciales de aplicación (`gcloud auth application-default login`). Cargar los usuarios una vez con
  `python -m scripts.seed_users`.

### Con Docker

```bash
docker build -t issue-tracker-api .
docker run --rm -p 8080:8080 --env-file .env issue-tracker-api
```

## Configuración

| Variable | Por defecto | Descripción |
|---|---|---|
| `APP_ENV` | `local` | Con `production` se desactivan `/docs`, `/redoc` y `/openapi.json`. |
| `LOG_LEVEL` | `INFO` | Nivel de logs. |
| `REPOSITORY_BACKEND` | `memory` | `memory` o `firestore`. |
| `GCP_PROJECT_ID` | — | Proyecto de GCP (requerido con Firestore fuera de GCP). |
| `FIRESTORE_DATABASE` | `(default)` | Base de datos de Firestore. |
| `JWT_SECRET_KEY` | — | **Obligatoria**, mínimo 32 caracteres. En GCP se inyecta desde Secret Manager. |
| `JWT_ALGORITHM` | `HS256` | Solo se aceptan HS256, HS384 o HS512. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Vigencia del token (5 a 1440). |
| `CORS_ORIGINS` | `["http://localhost:4200"]` | Orígenes permitidos (lista JSON). |
| `SEED_DEMO_USERS` | `true` | Carga los usuarios demo al iniciar (solo backend `memory`). |

## Endpoints

Prefijo: `/api/v1`. Todos los de `/issues` y `/auth/me`, `/auth/logout` requieren `Authorization: Bearer <token>`.
La columna **Permiso** indica las operaciones reservadas a Administrador y Soporte.

| Método | Ruta | Descripción | Permiso | Respuestas |
|---|---|---|---|---|
| GET | `/health` | Disponibilidad del servicio (sin prefijo, sin token) | — | 200 |
| POST | `/auth/login` | `{username, password}` → JWT + usuario con `role` y `permissions` | — | 200, 401, 422 |
| POST | `/auth/logout` | Revoca el token actual | — | 204, 401 |
| GET | `/auth/me` | Usuario autenticado (con rol y permisos) | — | 200, 401 |
| GET | `/issues?status=&priority=` | Listado (filtros opcionales) | — | 200, 401, 422 |
| POST | `/issues` | Crea `{title, description?, priority}` | — | 201, 401, 422 |
| GET | `/issues/summary` | `{total, open, in_progress, completed}` | — | 200, 401 |
| GET | `/issues/stats` | `{total, by_status, by_priority, matrix}` (estado × prioridad) | `stats:view` | 200, 401, 403 |
| GET | `/issues/{id}` | Detalle | — | 200, 401, 404 |
| PATCH | `/issues/{id}` | Actualiza `{status?, priority?}` (al menos uno) | `issues:resolve` para pasar a `completed` o tocar una completada | 200, 401, 403, 404, 422 |
| POST | `/issues/{id}/resolve` | Da la incidencia por resuelta (`completed`) | `issues:resolve` | 200, 401, 403, 404 |
| DELETE | `/issues/{id}` | Elimina la incidencia | `issues:delete` | 204, 401, 403, 404 |

### Roles y permisos

| Rol | Permisos |
|---|---|
| `admin` | `issues:resolve`, `issues:delete`, `stats:view` |
| `support` | `issues:resolve`, `issues:delete`, `stats:view` |
| `user` | — |

La matriz está en `app/domain/permissions.py`; las reglas se aplican en `IssueService`, de modo que se
cumplen sin importar el punto de entrada. Usuarios demo: `admin` (admin), `soporte` (support),
`analista` (user).

Valores válidos — `status`: `open`, `in_progress`, `completed` · `priority`: `high`, `medium`, `low`.
Reglas: título de 3 a 120 caracteres; descripción hasta 2000; campos desconocidos se rechazan.

### Formato de error

Todas las respuestas de error comparten la misma forma:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Los datos enviados no son válidos.",
    "details": [{ "field": "title", "message": "String should have at least 3 characters" }]
  }
}
```

| Código | HTTP | Cuándo |
|---|---|---|
| `invalid_credentials` | 401 | Usuario o contraseña incorrectos (mismo mensaje en ambos casos). |
| `not_authenticated` | 401 | Token ausente, inválido, expirado o revocado. |
| `forbidden` | 403 | El rol del usuario no tiene el permiso requerido. |
| `validation_error` | 422 | Datos de entrada inválidos. |
| `business_rule_violation` | 422 | Regla de negocio incumplida. |
| `not_found` | 404 | La incidencia no existe. |
| `persistence_unavailable` | 503 | Firestore no disponible (el detalle queda solo en logs). |
| `internal_error` | 500 | Error no controlado; mensaje genérico, traza solo en logs. |

## Modelo de datos (Firestore)

| Colección | Documento | Campos |
|---|---|---|
| `users` | id aleatorio | `username`, `full_name`, `password_hash` (Argon2id), `role` (`admin`, `support`, `user`), `is_active` |
| `issues` | id aleatorio | `title`, `description`, `priority`, `status`, `created_by`, `created_at`, `updated_at` |
| `revoked_tokens` | `jti` del token | `expires_at` — se recomienda una política TTL sobre este campo para la limpieza automática |

## Pruebas

```bash
pytest                       # toda la suite
pytest --cov                 # con cobertura (101 pruebas, 99 %)
pytest tests/unit            # solo unitarias
pytest -m acceptance -v      # solo pruebas de aceptación de usuario
ruff check . && ruff format --check .
```

Las pruebas usan los repositorios en memoria: son deterministas y no requieren credenciales de GCP.
La implementación Firestore se prueba contra un doble en memoria del SDK
(`tests/unit/test_firestore_repositories.py`), que valida el mapeo documento ↔ entidad, los filtros,
las agregaciones `COUNT` y la traducción de errores de Google Cloud.
