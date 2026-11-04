# Hito 8 - Configuración, reglas, administración y reportes detallados

Fecha: 2 de noviembre de 2026. Optimización de fluidez/GPU aplazada por solicitud del usuario.

## Funciones incorporadas

- Configuración general persistente: confianza predeterminada, guardado automático del resumen, descarga PDF al consultar el resultado, grabación local opcional, activación de alertas, umbral porcentual y formato de fecha.
- Opciones conservadas en cada análisis nuevo. Los anteriores mantienen los valores históricos/defaults: guardar manualmente y alertar cuando personas superan capacidad. Cambiar opciones no crea ni elimina alertas anteriores.
- Guardado automático en el trabajador para videos y al detener sesiones de cámara. Mantiene el guardado explícito para los demás casos.
- PDF automático al abrir un resultado completado con esa opción. Se solicita una vez por análisis/sesión de navegador; sigue disponible la descarga manual si falla o el navegador la bloquea. No constituye un archivo permanente de reportes en el servidor.
- Grabación local WebM optativa cuando está habilitada globalmente, hasta 100 MB, sin audio y sin subir la grabación al servidor. Se descarga desde la página de cámara; salir o recargar pierde el archivo que no se haya descargado. No se convierte a MP4 ni se muestra un enlace ficticio en el historial.
- Curso opcional en cámara y filtro de curso en historial/reportes.
- Reporte detallado con conteos máximos, ocupación media, análisis sobre capacidad, evolución diaria y horas con mayor máximo observado, tanto en pantalla como PDF. Se aplican los mismos filtros y límite de 500 registros. Las fechas/horas son de carga o inicio, no la fecha de grabación del archivo. No se suman detecciones como personas únicas.
- Administración de roles y activación de cuentas, con motivo y confirmación. No modifica contraseñas, `is_staff` ni `is_superuser`. El administrador no puede cambiar su propio acceso; las cuentas superusuario se gestionan con herramientas de Django. Desactivar una cuenta impide su autenticación por Django.
- Auditoría de configuración, reglas y cambios de acceso, con actor, fecha y antes/después. Consulta administrativa de los últimos 100 eventos.
- Reglas adicionales: puestos mínimos de reserva, matrícula máxima, un equipo obligatorio adicional y preferencia global de aula/laboratorio. Se admite una regla por tipo; se puede editar o desactivar, conservando auditoría. El tipo es inmutable. No es un intérprete arbitrario de reglas ni un optimizador global.
- Las reglas fundamentales de capacidad, disponibilidad, equipamiento y conflictos siempre se aplican. Las preferencias solo ordenan alternativas compatibles. Una regla que invalidaría asignaciones aceptadas futuras se rechaza dentro de la transacción.
- Accesos a historial/reporte desde el detalle del aula; accesos a reglas desde Horarios y Configuración.
- Control de versión para rechazar cambios de configuración/reglas basados en formularios desactualizados.

## Rutas

- `/configuracion`: configuración general y cuenta.
- `/administracion/reglas`, `/administracion/usuarios`, `/administracion/auditoria`.
- `/reportes`: resumen y detalle, filtros y PDF.
- `GET/PATCH /api/settings/` (PATCH requiere versión y administrador).
- `GET/POST /api/assignment-rules/`, `GET/PATCH /api/assignment-rules/{id}/` (PATCH requiere versión; escritura administrativa).
- `GET /api/administrative-events/` (administrador).
- `PATCH /api/auth/users/{id}/access/` (administrador; rol, activo y motivo).
- `GET /api/analysis-history/summary/`: mismos filtros que historial, solo completados.
- `GET /health/`: disponibilidad de la base sin revelar secretos.

## Preparación técnica

Migraciones `campus/0005` y `video_analysis/0003` aplicadas en la base local. No se crean datos académicos, roles ni reglas de demostración en ella. Las configuraciones de pruebas se preparan exclusivamente en `config.e2e`.

Incluidos Dockerfiles, `compose.deploy.yaml`, gateway HTTPS, volúmenes privados y guía de despliegue. Estructura YAML revisada; ejecución Docker, PostgreSQL y AWS pendientes en el entorno destino. También se incluye un flujo CI para Django y compilación frontend; no se ha ejecutado en GitHub.

Herramienta `services/vision/evaluate_counts.py` para comparar resultados con conteos humanos; no se han inventado etiquetas ni aprobado objetivos de precisión sin ellas.

## Verificación

- 73 pruebas Django aprobadas: regresiones previas más configuración, roles, instantáneas, guardado automático, umbral de alertas, reglas, protección de asignaciones y resumen de reportes.
- 10 pruebas del microservicio y evaluación aprobadas.
- Compilación TypeScript/Vite aprobada.
- Recorrido de navegador de administración aprobado tras corregir el proxy de `/admin`, que interceptaba indebidamente `/administracion`.
- Migraciones sin cambios pendientes detectados.

La evidencia adicional de navegador y revisión de PDFs se registra en `estado-y-entrega.md` al cerrar la verificación integral.
