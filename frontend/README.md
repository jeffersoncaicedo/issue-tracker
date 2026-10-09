# Issue Tracker Web (frontend)

Aplicación **Angular 20** (TypeScript 5.9, SCSS) para gestionar incidencias. Se despliega en
**Firebase Hosting** y consume el API FastAPI.

## Requisitos técnicos cubiertos

| Requisito | Implementación |
|---|---|
| Standalone Components | Todos los componentes son standalone; no hay `NgModule`. |
| Routing | `app.routes.ts` + `features/issues/issues.routes.ts`, con guards `authGuard`, `guestGuard` y `permissionGuard`. |
| Reactive Forms | Login, alta de incidencia y filtros, con formularios **tipados** (`NonNullableFormBuilder`, `FormGroup<…>`). |
| HttpClient | `provideHttpClient(withFetch(), withInterceptors([...]))`, interceptores funcionales. |
| Lazy loading | Cada página (`login`, `shell`, `issue-list`, `issue-create`, `dashboard`) se carga bajo demanda. |
| Strict typing | `strict`, `strictTemplates`, `noImplicitOverride`, `noPropertyAccessFromIndexSignature`; modelos con tipos literales. |

Además: **signals** para el estado, **zoneless change detection**, `OnPush` en todos los componentes,
control flow (`@if`, `@for`) y `inject()`.

## Estructura

```
src/app/
├── app.config.ts / app.routes.ts       # Providers globales y rutas raíz (lazy)
├── core/                               # Singleton, sin UI
│   ├── auth/                           # AuthService (signals, can()), SessionStorageService, guards
│   ├── http/                           # authInterceptor, errorInterceptor
│   ├── issues/issue-api.service.ts     # Cliente HTTP de /issues
│   ├── config/api.config.ts            # Token API_BASE_URL
│   └── models/                         # Interfaces y tipos del dominio
├── features/
│   ├── auth/login/                     # Página de inicio de sesión
│   ├── dashboard/                      # Vista Resumen (anillo, Pareto, carga por prioridad)
│   │   └── chart-geometry.ts           # Cálculo de los gráficos (funciones puras)
│   └── issues/
│       ├── issues.routes.ts            # Rutas hijas + IssueStore con alcance de ruta
│       ├── data/issue.store.ts         # Estado de la funcionalidad (signals)
│       ├── pages/issue-list/           # Resumen + filtros + listado editable
│       ├── pages/issue-create/         # Alta de incidencia
│       └── components/                 # SummaryBar, IssueFiltersBar
├── shared/                             # Shell (cabecera y navegación), ConfirmDialog, PriorityMeter, etiquetas
└── testing/test-data.ts                # Datos de prueba reutilizables
```

## Vistas y permisos

| Ruta | Vista | Acceso |
|---|---|---|
| `/login` | Inicio de sesión | Sin sesión |
| `/issues` | Resumen por estado, filtros y listado editable | Todos los usuarios |
| `/issues/new` | Alta de incidencia | Todos los usuarios |
| `/dashboard` | Resumen con gráficos y tabla cruzada | `stats:view` (Administrador, Soporte) |

El backend devuelve los permisos del usuario al iniciar sesión y `AuthService.can(permiso)` decide qué
se muestra: los botones **Resolver** y **Eliminar**, la opción "Completado", la edición de incidencias
completadas y la pestaña **Resumen**. Es solo presentación: la autorización real la aplica el API.

## Ejecución local

```bash
npm ci
npm start                 # http://localhost:4200 (usa environment.development.ts → http://localhost:8000/api/v1)
```

El backend debe estar en `http://localhost:8000` con `CORS_ORIGINS=["http://localhost:4200"]`.

## Configuración por entorno

| Archivo | Uso | `apiUrl` |
|---|---|---|
| `src/environments/environment.development.ts` | `ng serve`, `npm run build:dev` | `http://localhost:8000/api/v1` |
| `src/environments/environment.ts` | `ng build` (producción) | URL del servicio Cloud Run + `/api/v1` |

## Scripts

| Comando | Descripción |
|---|---|
| `npm start` | Servidor de desarrollo. |
| `npm run build` | Build de producción en `dist/frontend/browser`. |
| `npm test` | Pruebas en modo observación (Chrome). |
| `npm run test:ci` | Pruebas una vez, Chrome headless, con cobertura (umbral mínimo 80 %). |
| `npm run typecheck` | Verificación de tipos de la app y de las pruebas. |

## Pruebas

87 pruebas unitarias (Karma + Jasmine), **96 % de cobertura**:

| Archivo | Qué valida |
|---|---|
| `auth.service.spec.ts` | Login, persistencia de sesión, expiración, logout (incluso con el servidor caído). |
| `session-storage.service.spec.ts` | Lectura/escritura y descarte de datos corruptos. |
| `auth.guards.spec.ts` | Redirección al login conservando `returnUrl`; acceso por permiso. |
| `interceptors.spec.ts` | El token solo viaja al API propio; normalización de errores; 401 → cierre de sesión. |
| `issue-api.service.spec.ts` | Verbos, rutas y query params de filtros. |
| `issue.store.spec.ts` | Carga, filtros, actualización, resolver, eliminar, errores (incluido 403) y estado pendiente. |
| `issue-list.page.spec.ts` | Botones y restricciones según permisos; eliminación solo tras confirmar. |
| `confirm-dialog.spec.ts` | Apertura modal, confirmar, cancelar y cierre con Esc. |
| `chart-geometry.spec.ts` | Arcos del anillo, orden y acumulado del Pareto, escalas por prioridad, casos sin datos. |
| `dashboard.page.spec.ts` | Gráficos, tabla con totales, concordancia singular/plural, error y reintento. |
| `login.page.spec.ts` | Validaciones, navegación, protección contra *open redirect*, mensajes de error. |
| `issue-create.page.spec.ts` | Validación del título, valores por defecto, envío y errores del API. |
| `summary-bar.spec.ts` / `issue-filters.spec.ts` | Cálculo de porcentajes, emisión y sincronización de filtros. |

Los casos de aceptación de usuario sobre la interfaz están en [`../docs/UAT.md`](../docs/UAT.md).

## Diseño de la interfaz

- El color se reserva para comunicar **estado** (abierto ámbar, en progreso índigo, completado verde):
  aparece en la barra del resumen, en la franja lateral de cada incidencia y en la marca.
- La **prioridad** se representa con un indicador de barras (3 = alta) además del texto, para no
  depender solo del color.
- El resumen es interactivo: pulsar un estado filtra el listado y queda sincronizado con los selectores.
  La cantidad va **antes** del nombre del estado y el porcentaje al final, separado, para no confundirlos.
- Ícono "Ciclo" (anillo de estados con check) en SVG adaptable a tema oscuro.
- Los gráficos son SVG propios (sin librería): ligeros, con colores del sistema de diseño y texto alternativo.
- Accesible: etiquetas asociadas, `aria-invalid`, `role="alert"`, foco visible, `prefers-reduced-motion`
  y diseño responsivo hasta 360 px.
