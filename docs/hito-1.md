# Hito 1: autenticación, perfil y dashboard

## Alcance implementado

Registro con rol mínimo, inicio/cierre de sesión, perfil, recuperación/cambio de contraseña y dashboard con datos persistentes. Diseño basado en las pantallas entregadas, adaptado a móvil.

La imagen del acceso es un fotograma del video `clase3.mp4` entregado por el usuario. No es una detección del sistema ni una imagen de una cámara conectada. La fuente Inter se distribuye con el frontend para no depender de solicitudes a Google Fonts.

## API

| Método | Ruta | Acceso |
| --- | --- | --- |
| GET | `/api/auth/csrf/` | Público; obtiene token CSRF |
| POST | `/api/auth/register/` | Público + CSRF; siempre rol consulta |
| POST | `/api/auth/login/` | Público + CSRF |
| POST | `/api/auth/logout/` | Sesión + CSRF |
| GET / PATCH | `/api/auth/me/` | Sesión; PATCH solo cambia nombre |
| POST | `/api/auth/password/recover/` | Público + CSRF |
| POST | `/api/auth/password/reset/` | Token válido + CSRF |
| POST | `/api/auth/password/change/` | Sesión, contraseña actual y CSRF |
| GET | `/api/auth/users/` | Administrador |
| GET | `/api/dashboard/` | Sesión |

Vite actúa como proxy local de `/api` hacia Django. Las cookies de sesión no se guardan en localStorage. Las rutas protegidas se validan también en el servidor.

## Definiciones del dashboard

- Aulas activas: espacios con `active=true`.
- Aulas analizadas: aulas distintas presentes en los registros de análisis.
- Conflictos abiertos: alertas no resueltas.
- Ocupación: promedio diario de `personas / capacidad × 100` en la semana local de lunes a domingo.
- Capacidad cero o desconocida: no entra en el promedio. Ausencia de muestras se representa con `null`, no con ocupación cero.
- Los modelos de análisis de este hito son resúmenes mínimos; todavía no reciben datos de un detector.

## Verificación

Resultado del hito: **16 pruebas backend aprobadas, 3 pruebas de navegador aprobadas y compilación TypeScript/Vite correcta**. También se revisaron capturas del acceso y del dashboard en escritorio/móvil. Las migraciones están sincronizadas con los modelos.

Pruebas backend cubren:

- CSRF, rutas anónimas y sesiones.
- Registro, correo duplicado, hash y contraseñas débiles.
- Intentos de elevar rol mediante registro/edición.
- Separación de permisos de consulta, coordinador y administrador.
- Credenciales incorrectas y cuenta inactiva.
- Recuperación uniforme para correos existentes/inexistentes.
- Tokens inválidos, caducados y reutilizados.
- Revocación de sesiones al cambiar/restablecer contraseña.
- Límites de intentos de acceso.
- Dashboard vacío y agregados a partir de registros persistidos.

Pruebas de navegador cubren registro, recarga con sesión, edición de perfil, cambio de contraseña, rechazo de contraseña antigua, acceso con la nueva, cierre de sesión, recuperación, enlace inválido y diseño móvil.

La ejecución está limitada a SQLite y Chromium. Chrome y Edge instalados, PostgreSQL, SMTP externo y AWS quedan pendientes de comprobación.

Las pruebas de navegador inician servicios separados y una base `e2e.sqlite3`; los límites de solicitudes permanecen activos y su caché se reinicia con cada servidor de pruebas.

## Documentación técnica consultada

- [Autenticación Django 5.2](https://docs.djangoproject.com/en/5.2/topics/auth/default/).
- [Autenticación por sesión en Django REST Framework](https://www.django-rest-framework.org/api-guide/authentication/).
- [Configuración de Vite](https://vite.dev/guide/).

## Continuación

El siguiente bloque es gestión de aulas y datos académicos. Luego se integrará el microservicio de visión con las muestras recibidas, sin dar por acreditado el requisito de precisión hasta disponer de conteos manuales.
