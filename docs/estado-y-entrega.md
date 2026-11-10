# Estado verificable y entrega al grupo

Actualizado: 10 de noviembre de 2026. Este documento distingue funciones implementadas de validación pendiente. No se certifica el sistema completo para producción.

## Actualización para la presentación

- Despliegue Linux realizado en AWS Lightsail con Docker, PostgreSQL 17, HTTPS y volúmenes persistentes. Login confirmado por el usuario; salud pública y `check --deploy` aprobados.
- 73 pruebas Django pasaron sobre PostgreSQL antes de las últimas mejoras; después se verificaron adicionalmente cinco pruebas de cámara/monitor y cuatro de eliminación sobre PostgreSQL. No se presenta esa ejecución por grupos como una nueva suite completa.
- Revisión previa a GitHub: suite completa de 78 pruebas Django aprobada localmente con SQLite y sin migraciones pendientes. Once pruebas de visión y las compilaciones frontend pasaron durante los cambios; los recorridos específicos de video/eliminación, cámara y monitor fueron verificados. El workflow comprobará SQLite y PostgreSQL al subir el código; su resultado remoto sigue pendiente.
- Cámara trasera/frontal seleccionable; monitor de video entre navegadores en la misma red y con la misma cuenta. El usuario confirmó iVCam como webcam. Las pruebas automatizadas usan cámara sintética, no certifican el equipo físico.
- Captura secuencial con ciclo objetivo mínimo de 200 ms, token CSRF reutilizado durante la sesión y tiempo de muestra visible. Hasta 5 muestras/s como objetivo, sin garantía de FPS y sin acumular solicitudes. Siguen separados el video continuo y la muestra analizada.
- Eliminación definitiva por administrador con confirmación individual: retira archivos, resultado, resumen y alertas; no permite borrar trabajos activos ni ejecuta una limpieza masiva automática.
- Candidato entrenado en Roboflow descargado y cargado correctamente, clases `person`/`monitor`. En siete imágenes de test a confianza 0,50, el error medio de conteo de personas fue 1,00 con el original y 5,57 con el candidato. Se conserva el original. La muestra pequeña y las etiquetas no acreditan precisión general.

| Requisito | Estado y ubicación |
| --- | --- |
| RF-01 Cargar videos | Implementado; validación MP4/AVI, cola y errores. Hito 3. |
| RF-02 Detectar personas | Detector real y muestras persistidas, sin certificación de precisión. Hitos 3 y 7. |
| RF-03 Contar puestos | Parcial: se detectan objetos de referencia (monitores), no puestos utilizables. Falta definición/dataset/modelo validado. |
| RF-04 Capacidad y ocupación | Implementado respecto a capacidad humana validada. Capacidad física automática no acreditada. |
| RF-05/06 Aulas | Registro, consulta, edición y validación de capacidad. Hito 2. |
| RF-07 Datos académicos | Docentes, asignaturas, cursos, matrícula y franjas. Hito 2. |
| RF-08/09 Alternativas y propuestas | Compatibilidad explicada y propuestas persistidas. Hito 5. |
| RF-10 Conflictos | Aula, docente y curso; revalidación al aceptar y al modificar catálogos. Hito 5. |
| RF-11 Cámara | Cámara local, preferencia trasera/frontal y monitor entre navegadores. iVCam confirmado por el usuario. Muestreo optimizado; sin GPU ni entrada RTSP directa. Hito 7. |
| RF-12 Reglas | Reglas adicionales editables y preferencias; restricciones fundamentales siempre activas. Hito 8. |
| RF-13 Validar capacidad | Valor humano, responsable, fecha e historial. Hito 2. |
| RF-14 Alertas | Creación según opciones del análisis; estados y auditoría. Hitos 4 y 8. |
| RF-15/16 Propuestas/decisiones | Consulta, aceptación/modificación/rechazo/cancelación, motivo y auditoría. Hito 5. |
| RF-17 Historial | Análisis filtrables; eventos de alertas y decisiones en sus detalles; auditoría administrativa. Hitos 4, 5 y 8. |
| RF-18 Reportes | PDF individual/consolidado, filtros y resumen detallado reproducible. Hitos 6 y 8. |
| RF-19/20 Cuentas | Registro, sesiones y cambio/recuperación. Correo local probado; SMTP externo pendiente. Hito 1. |
| RF-21 Roles | Autorización de backend y gestión administrativa de acceso. Hito 8. |
| RF-22 Dashboard | Indicadores y ocupación a partir de resúmenes guardados. Hito 1. |

## Lo que el grupo aún debe validar

1. Precisión con personas y puestos reales (RNF-01/RF-03): completar etiquetas humanas y ejecutar la evaluación, según `evaluacion-modelo.md`. No basta que el video funcione.
2. Fluidez y rendimiento en la computadora de presentación: comparar muestras/segundo, retraso, resolución y recursos con la nueva captura; no se prometen 30 FPS.
3. PostgreSQL, Linux y HTTPS ya fueron verificados. Ampliar validación de concurrencia y ensayar restauración de backups y SMTP externo. Guía en `despliegue-aws.md`.
4. Completar el ensayo manual de los flujos desde la web pública, con los equipos y red de presentación. El servidor AWS ya existe y consume recursos/créditos.
5. Medir objetivos de tiempos de recomendaciones/dashboard con un conjunto y hardware documentados; aprobar una política institucional de conservación de videos.

## Para otra computadora

Leer primero README y usar entornos separados para backend y visión. Instalar dependencias fijadas, configurar `.env` local y transferir pesos del modelo. No compartir el `.env` actual, correos locales ni bases con cuentas personales como parte del código.

Desde la raíz, aplicar migraciones y usar la tarea de VS Code **Iniciar Smart Campus Vision**, que inicia Django, Vite, visión y el trabajador de videos. La aplicación se abre por el frontend en el puerto 5173. Para datos nuevos, registrar cuentas y crear catálogos reales; no hay contraseña administrativa predeterminada.

## Entrega de la mejora de video

- `frontend/src/LiveAnalysis.tsx`: cámara, captura JPEG y visualización con un máximo objetivo de cinco muestras por segundo, sujeto a red y procesamiento. La cámara local y la última muestra son vistas separadas.
- `backend/video_analysis/live.py`: sesión, envío al detector y agregación; los conteos se calculan en el servidor.
- `backend/video_analysis/client.py`: petición interna; timeout de primera carga de 120 segundos.
- `services/vision/app/main.py`: endpoint `/v1/frame`, validación JPEG y exclusión de inferencias de cámara simultáneas.
- `services/vision/app/detector.py`: YOLO en CPU a tamaño 640.

Si se cambia el detector o la visualización, conservar la semántica histórica, autorización y liberación de cámara; evitar acumular fotogramas atrasados. Validar precisión además de velocidad. Los tests de cámara usan un dispositivo sintético y no activan la cámara física.

## Evidencia del cierre anterior (2 de noviembre)

- 73 pruebas Django y 10 de visión/evaluación aprobadas.
- Compilación frontend y consistencia de migraciones aprobadas.
- Estructura de Compose y aislamiento de puertos revisados estáticamente; construcción y despliegue no verificados.
- 11 recorridos completos Chromium aprobados, incluidos cámara simulada con YOLO real, grabación WebM, guardado automático y PDF automático.
- PDF individual y consolidado con resumen/evolución renderizados e inspeccionados visualmente; encabezados de tabla repetidos y notas agrupadas para evitar párrafos aislados.
- Cinco recorridos Edge aprobados: registro/perfil/contraseña, recuperación, acceso móvil, historial/alertas/PDF y administración. El recorrido administrativo se repitió satisfactoriamente después de un timeout previo al login. No se ha probado la cámara física en Edge.
