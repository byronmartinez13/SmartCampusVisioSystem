# Estado verificable y entrega al grupo

Actualizado: 2 de noviembre de 2026. Este documento distingue funciones implementadas de validación pendiente. No se certifica el sistema completo para producción.

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
| RF-11 Cámara | Cámara local funcional, confirmada también por el usuario. La mejora de fluidez/GPU queda aplazada. Hito 7. |
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
2. Fluidez y rendimiento en la computadora de presentación: comparar muestras/segundo, retraso, resolución y recursos; no se prometen 30 FPS. No se cambió la pausa de muestreo en este cierre.
3. Ejecutar y comprobar PostgreSQL y pila de despliegue Linux. Después validar concurrencia, persistencia, HTTPS, envío SMTP y restauración de backup. Guía en `despliegue-aws.md`.
4. Despliegue real en la cuenta AWS del grupo y prueba de las funciones desde ese dominio. No se han creado recursos ni utilizado credenciales externas.
5. Medir objetivos de tiempos de recomendaciones/dashboard con un conjunto y hardware documentados; aprobar una política institucional de conservación de videos.

## Para otra computadora

Leer primero README y usar entornos separados para backend y visión. Instalar dependencias fijadas, configurar `.env` local y transferir pesos del modelo. No compartir el `.env` actual, correos locales ni bases con cuentas personales como parte del código.

Desde la raíz, aplicar migraciones y usar la tarea de VS Code **Iniciar Smart Campus Vision**, que inicia Django, Vite, visión y el trabajador de videos. La aplicación se abre por el frontend en el puerto 5173. Para datos nuevos, registrar cuentas y crear catálogos reales; no hay contraseña administrativa predeterminada.

## Entrega de la mejora de video

- `frontend/src/LiveAnalysis.tsx`: cámara, captura JPEG, visualización y pausa de un segundo entre respuestas. La cámara local y la última muestra son vistas separadas.
- `backend/video_analysis/live.py`: sesión, envío al detector y agregación; los conteos se calculan en el servidor.
- `backend/video_analysis/client.py`: petición interna; timeout de primera carga de 120 segundos.
- `services/vision/app/main.py`: endpoint `/v1/frame`, validación JPEG y exclusión de inferencias de cámara simultáneas.
- `services/vision/app/detector.py`: YOLO en CPU a tamaño 640.

Si se cambia el detector o la visualización, conservar la semántica histórica, autorización y liberación de cámara; evitar acumular fotogramas atrasados. Validar precisión además de velocidad. Los tests de cámara usan un dispositivo sintético y no activan la cámara física.

## Evidencia de este cierre

- 73 pruebas Django y 10 de visión/evaluación aprobadas.
- Compilación frontend y consistencia de migraciones aprobadas.
- Estructura de Compose y aislamiento de puertos revisados estáticamente; construcción y despliegue no verificados.
- 11 recorridos completos Chromium aprobados, incluidos cámara simulada con YOLO real, grabación WebM, guardado automático y PDF automático.
- PDF individual y consolidado con resumen/evolución renderizados e inspeccionados visualmente; encabezados de tabla repetidos y notas agrupadas para evitar párrafos aislados.
- Cinco recorridos Edge aprobados: registro/perfil/contraseña, recuperación, acceso móvil, historial/alertas/PDF y administración. El recorrido administrativo se repitió satisfactoriamente después de un timeout previo al login. No se ha probado la cámara física en Edge.
