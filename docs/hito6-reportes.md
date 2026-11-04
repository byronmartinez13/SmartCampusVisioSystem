# Hito 6 - Reportes PDF

Implementado el 2 de noviembre de 2026.

- Reportes en `/reportes`: reutiliza los filtros y la consulta paginada del historial.
- PDF individual desde el historial y los resultados de un video completado.
- Consolidado con los filtros aplicados, todas las páginas y hasta 500 análisis completados. Si se supera el límite se solicita reducir los filtros; no se truncan resultados silenciosamente. Un filtro de estado diferente de completado produce un reporte sin análisis.
- Se incluyen también resultados cuyo resumen todavía no se ha guardado en el dashboard. El PDF individual indica ese estado.
- Acceso de lectura para cualquier usuario autenticado, según los permisos existentes del historial; acceso anónimo rechazado. Las descargas usan `private, no-store` y no exponen rutas de video ni claves internas.
- Capacidad de la instantánea al cargar, máximo de personas, ocupación y disponibilidad estimadas. Sin capacidad no se inventa un porcentaje. Los nombres de aula y curso son los actuales del catálogo y se identifican como tales.
- El PDF individual conserva la semántica del detector histórico, modelo, hash y umbral. Los monitores no sustituyen puestos utilizables ni capacidad validada.
- Se generan documentos al solicitar la descarga; no hay archivo permanente de reportes ni envío por correo.

## API

- `GET /api/video-analyses/{uuid}/report/`: PDF individual; 400 si el análisis no está completado con resultados.
- `GET /api/analysis-history/report/`: PDF consolidado; mismos filtros que el historial, sin paginación.

## Validación

- Las 58 pruebas previas Django pasaron durante la ejecución de la suite; cuatro pruebas nuevas de PDF aprobadas tras ajustar la comprobación del UUID cuando se divide en líneas.
- Cobertura nueva: autenticación, capacidad histórica, semántica de monitores, texto escapado, análisis pendiente, capacidad desconocida, filtros, fechas inválidas, salida vacía y límite de 500.
- TypeScript/Vite compilado correctamente.
- Playwright de historial aprobado con descarga PDF y navegación a Reportes, incluyendo comprobación de ancho móvil.
- PDFs de prueba individual y consolidado de 45 filas renderizados e inspeccionados visualmente. Datos sintéticos solo en pruebas y `tmp/pdfs/`, sin modificar la base local del usuario.

## Dependencias

ReportLab y dependencias fijadas en `backend/requirements.lock.txt`. Para ejecutar las pruebas que extraen texto PDF: `python -m pip install -r backend/requirements-dev.txt`.

Continúan pendientes análisis en vivo, configuración general, evaluación final del modelo, PostgreSQL verificado y AWS.
