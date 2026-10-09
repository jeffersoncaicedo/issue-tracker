# Plan de Pruebas de Aceptación de Usuario (UAT)

Este documento define los criterios con los que un usuario de negocio valida que la
aplicación cumple los requisitos funcionales del examen. Cada historia tiene:

- **Validación automatizada**: `backend/tests/acceptance/test_user_acceptance.py`
  (8 historias; ejecutar con `pytest -m acceptance`), que recorre el flujo completo sobre el API.
- **Validación manual en la interfaz**: los casos de esta tabla, a ejecutar en la
  aplicación desplegada o local.

**Usuarios de prueba:**

| Usuario | Contraseña | Rol | Puede resolver, eliminar y ver el resumen detallado |
|---|---|---|---|
| `admin` | `Admin#2026` | Administrador | Sí |
| `soporte` | `Soporte#2026` | Soporte | Sí |
| `analista` | `Analista#2026` | Usuario | No |

## Trazabilidad requisito → historia → prueba

| Requisito del examen | Historia | Prueba automatizada |
|---|---|---|
| Iniciar sesión (usuario y contraseña), cerrar sesión | HU-01 | `test_hu01_iniciar_y_cerrar_sesion`, `test_hu01_credenciales_invalidas` |
| Crear incidencias (título, descripción, prioridad) | HU-02 | `test_hu02_hu03_crear_y_visualizar_incidencias` |
| Visualizar incidencias | HU-03 | `test_hu02_hu03_crear_y_visualizar_incidencias` |
| Actualizar estado y prioridad | HU-04 | `test_hu04_actualizar_estado_y_prioridad` |
| Filtrar por estado o prioridad | HU-05 | `test_hu05_filtrar_por_estado_o_prioridad` |
| Resumen con total y cantidad por estado | HU-06 | `test_hu06_resumen_por_estado` |
| Soporte/Administrador resuelven o eliminan tickets | HU-07 | `test_hu07_soporte_resuelve_y_elimina` |
| Vista de resumen con gráficos, solo para Soporte/Administrador | HU-08 | `test_hu08_vista_de_resumen_solo_para_privilegiados` |

## Casos de prueba manuales

### HU-01 — Iniciar y cerrar sesión
*Como usuario quiero iniciar y cerrar sesión para que solo personas autorizadas gestionen las incidencias.*

| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-01 | Abrir la aplicación sin sesión. | Se muestra la pantalla **Iniciar sesión**. | ☐ |
| UAT-02 | Pulsar **Iniciar sesión** con los campos vacíos. | Mensajes "Ingrese su usuario." e "Ingrese su contraseña."; no se envía la petición. | ☐ |
| UAT-03 | Ingresar `admin` y una contraseña incorrecta. | Mensaje "Usuario o contraseña incorrectos."; el campo contraseña se limpia. | ☐ |
| UAT-04 | Ingresar `admin / Admin#2026`. | Se abre el listado; la cabecera muestra "Adriana Mena" y el rol "Administrador". | ☐ |
| UAT-05 | Pulsar **Cerrar sesión**. | Vuelve al login. Al pulsar "Atrás" en el navegador no se puede ver el listado. | ☐ |
| UAT-06 | Sin sesión, abrir directamente `/issues/new`. | Redirige al login; tras autenticarse vuelve a `/issues/new`. | ☐ |

### HU-02 — Crear incidencias
*Como usuario quiero registrar una incidencia con título, descripción y prioridad para que se atienda.*

| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-07 | Pulsar **Nueva incidencia**. | Formulario con prioridad **Media** preseleccionada. | ☐ |
| UAT-08 | Pulsar **Registrar incidencia** sin título. | "Escriba un título para la incidencia."; no se registra. | ☐ |
| UAT-09 | Título `ab`. | "El título debe tener al menos 3 caracteres." | ☐ |
| UAT-10 | Título válido, descripción y prioridad **Alta**; registrar. | Vuelve al listado; la incidencia aparece primero, en estado **Abierto**, con su autor y fecha; el resumen suma 1. | ☐ |
| UAT-11 | Escribir en la descripción. | El contador "N de 2000 caracteres" se actualiza. | ☐ |

### HU-03 — Visualizar incidencias
| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-12 | Abrir el listado con datos. | Se ven título, descripción, autor, fecha, prioridad y estado; ordenadas de la más reciente a la más antigua. | ☐ |
| UAT-13 | Abrir el listado sin datos. | Mensaje "Aún no hay incidencias registradas." con acceso a registrar la primera. | ☐ |

### HU-04 — Actualizar estado y prioridad
| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-14 | (Cualquier usuario) Cambiar el **Estado** de una incidencia a **En progreso**. | Se guarda sin recargar la página; la franja lateral cambia a azul; el resumen se actualiza. | ☐ |
| UAT-15 | (Soporte/Administrador) Cambiarla a **Completado**. | Franja verde, título atenuado; el resumen se actualiza. | ☐ |
| UAT-16 | Cambiar la **Prioridad** a **Baja**. | El indicador de barras muestra 1 barra. | ☐ |
| UAT-17 | Recargar la página (F5). | Los cambios persisten. | ☐ |

### HU-05 — Filtrar
| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-18 | Seleccionar Estado = **Abierto**. | Solo se listan incidencias abiertas; aparece "Quitar filtros". | ☐ |
| UAT-19 | Seleccionar además Prioridad = **Alta**. | Solo abiertas de prioridad alta. | ☐ |
| UAT-20 | Pulsar **En progreso** en la leyenda del resumen. | Se aplica el filtro y el selector Estado muestra "En progreso"; el resto de la barra se atenúa. | ☐ |
| UAT-21 | Filtro sin coincidencias. | "Ninguna incidencia coincide con los filtros seleccionados." con botón para quitarlos. | ☐ |
| UAT-22 | Con filtro "Abierto", cambiar una incidencia a "Completado". | La incidencia sale del listado filtrado. | ☐ |

### HU-06 — Resumen por estado
| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-23 | Observar el resumen del listado. | Total y, por cada estado, **primero la cantidad**, luego el nombre y al final el porcentaje (p. ej. "**2** Abierto │ 29 %"); la suma coincide con el total. | ☐ |
| UAT-24 | Aplicar un filtro. | El resumen sigue mostrando los totales globales (no cambia con el filtro). | ☐ |

### HU-07 — Resolver y eliminar (Soporte / Administrador)
*Como Soporte o Administrador quiero dar por resuelto o eliminar un ticket para mantener el tablero al día.*

| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-28 | Iniciar sesión como `analista`. | Ninguna fila muestra **Resolver** ni **Eliminar**; no aparece la pestaña **Resumen**. | ☐ |
| UAT-29 | Como `analista`, abrir el selector de estado de una incidencia abierta. | La opción **Completado** aparece deshabilitada. | ☐ |
| UAT-30 | Como `analista`, observar una incidencia completada. | Sus selectores están bloqueados; al pasar el cursor se indica que solo Soporte o Administrador pueden modificarla. | ☐ |
| UAT-31 | Iniciar sesión como `soporte`. | Las incidencias no completadas muestran **Resolver**; todas muestran **Eliminar**. | ☐ |
| UAT-32 | Pulsar **Resolver**. | La incidencia pasa a **Completado** (franja verde) y el resumen se actualiza sin recargar. | ☐ |
| UAT-33 | Pulsar **Eliminar** y luego **Cancelar** (o la tecla Esc). | Se abre un diálogo con el título de la incidencia; al cancelar no se elimina nada. | ☐ |
| UAT-34 | Pulsar **Eliminar** y confirmar. | La incidencia desaparece del listado y el resumen se actualiza. | ☐ |
| UAT-35 | Recargar la página (F5). | La incidencia eliminada no reaparece. | ☐ |

### HU-08 — Vista de resumen (Soporte / Administrador)
*Como Administrador quiero ver gráficamente cómo se distribuyen las incidencias para priorizar el trabajo.*

| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-36 | Como `admin`, abrir la pestaña **Resumen**. | Se muestran el anillo por estado, el diagrama de Pareto, la carga por prioridad y la tabla cruzada. | ☐ |
| UAT-37 | Comparar el total del anillo con la tabla. | El total del centro del anillo coincide con la celda Total/Total de la tabla. | ☐ |
| UAT-38 | Revisar el Pareto. | Las barras están ordenadas de mayor a menor y la línea acumulada termina en 100 %. | ☐ |
| UAT-39 | Leer la frase bajo el título. | Indica cuántas incidencias están sin resolver y cuántas de ellas son de prioridad alta, con concordancia correcta (singular o plural). | ☐ |
| UAT-40 | Resolver una incidencia en el listado, volver a **Resumen** y pulsar **Actualizar**. | Las cifras reflejan el cambio. | ☐ |
| UAT-41 | Como `analista`, escribir `/dashboard` en la barra de direcciones. | Se redirige al listado; el resumen detallado no se muestra. | ☐ |

### Casos no funcionales
| ID | Pasos | Resultado esperado | ✔ |
|---|---|---|---|
| UAT-25 | Detener el API y recargar el listado. | Mensaje claro de conexión con opción **Reintentar**; la app no se rompe. | ☐ |
| UAT-26 | Usar la aplicación en un teléfono (≈390 px), incluida la vista **Resumen**. | Todo es legible y operable sin desplazamiento horizontal de la página (la tabla cruzada se desplaza dentro de su propio contenedor). | ☐ |
| UAT-27 | Navegar solo con teclado (Tab/Enter/flechas). | Todos los controles son alcanzables y con foco visible; el diálogo de eliminación atrapa el foco y se cierra con Esc. | ☐ |
| UAT-42 | Ver la pestaña del navegador en tema claro y oscuro. | El ícono (anillo con check) es visible en ambos temas. | ☐ |

## Registro de ejecución

| Fecha | Entorno (local / Cloud) | Ejecutado por | Resultado | Observaciones |
|---|---|---|---|---|
| | | | | |
